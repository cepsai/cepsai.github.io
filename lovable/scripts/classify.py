#!/usr/bin/env python3
"""Classify discovered Lovable apps to ESCO occupations using Ollama + ESCO API.

Pipeline (per app):
  1. Extract text (title + description + og_* + MWL project slug).
  2. Query ESCO search API with the title — retrieve top-N occupation candidates.
  3. Build a schema-constrained prompt with candidates + app text → Ollama → JSON.
  4. Parse LLM output into per-app record; attach placeholder for exposure score.

Output: data/apps_classified.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
IN_FILE = DATA / "discovered_apps.json"
OUT_FILE = DATA / "apps_classified.json"

OLLAMA_URL = "http://localhost:11434/api/chat"
ESCO_SEARCH = "https://ec.europa.eu/esco/api/search"
ESCO_RESOURCE = "https://ec.europa.eu/esco/api/resource/occupation"
UA = "Mozilla/5.0 (compatible; CEPS-DST-AtlasBot/0.2; research; +https://www.ceps.eu/)"

DEFAULT_MODEL = "nemotron-3-nano:4b"
ESCO_CAND_LIMIT = 5
REQ_TIMEOUT = 45
OLLAMA_TIMEOUT = 120

SYSTEM_PROMPT = """Classify an app to one of the given ESCO occupations. Pick the single best match whose work the app augments or automates. Choose only from the candidate list. Return JSON:
{"primary_occupation_id":"<id>","primary_occupation_label":"<label>","primary_task_free_text":"<short task>","automation_vs_augmentation":"automation|augmentation|mixed","confidence":0.0,"rationale":"<brief>"}
If no candidate fits, use "primary_occupation_id":null."""


def esco_search_occupations(query: str, limit: int = ESCO_CAND_LIMIT) -> list[dict]:
    """Search ESCO for occupation candidates matching the query."""
    if not query or not query.strip():
        return []
    params = {"text": query[:200], "type": "occupation", "limit": limit, "language": "en"}
    try:
        r = requests.get(ESCO_SEARCH, params=params, headers={"User-Agent": UA}, timeout=REQ_TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  [esco search] '{query[:50]}' failed: {e}", file=sys.stderr)
        return []
    results = data.get("_embedded", {}).get("results", [])
    out = []
    for r_ in results:
        uri = r_.get("uri", "")
        uuid = uri.rsplit("/", 1)[-1] if uri else ""
        label = r_.get("title") or (r_.get("preferredLabel") or {}).get("en") or ""
        out.append({"uuid": uuid, "uri": uri, "label": label, "search_hit": r_.get("searchHit", "")})
    return out


def esco_fetch_description(uri: str) -> str:
    """Fetch occupation description (short). Caches in-process via closure below."""
    try:
        r = requests.get(ESCO_RESOURCE, params={"uris": uri, "language": "en"}, headers={"User-Agent": UA}, timeout=REQ_TIMEOUT)
        r.raise_for_status()
        d = r.json()
        # Response shape: { "_embedded": { "<uri>": { "description": { "en": { "literal": "..." } }, ... } } }
        emb = d.get("_embedded", {}).get(uri) or {}
        desc = (emb.get("description") or {}).get("en", {}).get("literal") or ""
        return desc[:400]
    except Exception:
        return ""


def ollama_chat(model: str, messages: list[dict], format_json: bool = True) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.1, "num_ctx": 4096, "num_predict": 400},
    }
    if format_json:
        payload["format"] = "json"
    r = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
    r.raise_for_status()
    return r.json()["message"]["content"]


def extract_app_text(app: dict) -> str:
    """Combine title + og_title + description + og_description + MWL slug hints."""
    parts = []
    for k in ("title", "og_title"):
        v = app.get(k)
        if v:
            parts.append(v.strip())
    for k in ("description", "og_description"):
        v = app.get(k)
        if v:
            parts.append(v.strip())
    slug = app.get("mwl_project_slug")
    if slug:
        parts.append(f"(project slug: {slug.replace('-', ' ')})")
    return " — ".join(parts)[:1200]


def classify_app(app: dict, model: str) -> dict:
    text = extract_app_text(app)
    out: dict = {
        "url": app["url"],
        "platform": app.get("platform"),
        "title": app.get("title"),
        "description": app.get("description"),
        "esco_candidates": [],
        "classification": None,
        "error": None,
        "classifier_version": "v0.1",
    }
    if not text:
        out["error"] = "no_text"
        return out

    # ESCO candidate retrieval — use title as primary query, fall back to first keywords
    query = (app.get("title") or "").strip()
    if not query or len(query) < 3:
        query = text[:80]
    candidates = esco_search_occupations(query)
    # Enrich with short description (throttled, just for top 3 to limit API calls)
    for c in candidates[:3]:
        c["description"] = esco_fetch_description(c["uri"])
    out["esco_candidates"] = candidates
    if not candidates:
        out["error"] = "no_esco_candidates"
        return out

    # Build prompt
    cand_lines = []
    for c in candidates:
        line = f'- id: {c["uuid"]}\n  label: "{c["label"]}"'
        if c.get("description"):
            line += f'\n  description: "{c["description"][:240]}"'
        cand_lines.append(line)
    cand_block = "\n".join(cand_lines)

    user_prompt = (
        f"App URL: {app['url']}\n"
        f"App text (title + description): {text}\n\n"
        f"Candidate ESCO occupations:\n{cand_block}\n"
    )

    try:
        raw = ollama_chat(
            model,
            [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}],
            format_json=True,
        )
    except Exception as e:
        out["error"] = f"ollama_error:{type(e).__name__}:{str(e)[:200]}"
        return out

    # Parse JSON response
    try:
        parsed = json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            out["error"] = f"json_parse_failed: {raw[:300]}"
            return out
        try:
            parsed = json.loads(m.group(0))
        except Exception as e:
            out["error"] = f"json_parse_failed:{e}: {raw[:300]}"
            return out

    # Validate: primary_occupation_id must be in candidate set (or null)
    valid_ids = {c["uuid"] for c in candidates} | {None}
    pid = parsed.get("primary_occupation_id")
    if pid not in valid_ids:
        out["error"] = f"llm_hallucinated_id:{pid}"
        return out
    # Secondary IDs kept optional; filter to valid
    secs = parsed.get("secondary_occupation_ids") or []
    parsed["secondary_occupation_ids"] = [s for s in secs if s in {c["uuid"] for c in candidates}]
    # Enrich with labels for chosen IDs (primary + secondary)
    label_by_id = {c["uuid"]: c["label"] for c in candidates}
    if pid and not parsed.get("primary_occupation_label"):
        parsed["primary_occupation_label"] = label_by_id.get(pid, "?")
    parsed["secondary_occupation_labels"] = [label_by_id.get(s, "?") for s in parsed["secondary_occupation_ids"]]

    out["classification"] = parsed
    out["validation_status"] = "unvalidated"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model tag (e.g. qwen3.5:9b, gemma4:31b)")
    ap.add_argument("--limit", type=int, default=100, help="Max apps to classify this run")
    ap.add_argument("--workers", type=int, default=4, help="Parallel workers (keep modest for local Ollama)")
    ap.add_argument("--platform", choices=["any", "lovable.app", "lovable.dev", "custom_domain"], default="any")
    ap.add_argument("--min-text-chars", type=int, default=30, help="Skip apps with less text than this")
    args = ap.parse_args()

    if not IN_FILE.exists():
        print(f"missing {IN_FILE} — run discover.py first", file=sys.stderr)
        return 1

    in_data = json.loads(IN_FILE.read_text())
    apps = in_data["apps"]

    # Filter: live 2xx, has usable text, matches platform
    def live(a: dict) -> bool:
        s = a.get("status")
        return isinstance(s, int) and 200 <= s < 300

    def usable(a: dict) -> bool:
        txt = extract_app_text(a)
        return len(txt) >= args.min_text_chars

    candidates = [a for a in apps if live(a) and usable(a) and (args.platform == "any" or a.get("platform") == args.platform)]
    print(f"{len(candidates)} apps meet filter (live, has text, platform={args.platform})")
    candidates = candidates[: args.limit]
    print(f"classifying first {len(candidates)} with model {args.model} ({args.workers} workers)...\n")

    results: list[dict] = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(classify_app, a, args.model): a for a in candidates}
        for i, f in enumerate(as_completed(futs), 1):
            rec = f.result()
            results.append(rec)
            status = "OK" if rec.get("classification") else f"ERR:{rec.get('error', '?')[:60]}"
            label = (rec.get("classification") or {}).get("primary_occupation_label") or "—"
            print(f"[{i}/{len(candidates)}] {rec['url'][:70]:72s} {status:22s} → {str(label)[:50]}", flush=True)

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "summary": {
            "classified_ok": sum(1 for r in results if r.get("classification")),
            "errors": sum(1 for r in results if r.get("error")),
            "total": len(results),
            "runtime_seconds": round(time.time() - t0, 1),
        },
        "results": sorted(results, key=lambda r: r["url"]),
    }
    OUT_FILE.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nwrote {OUT_FILE}")
    print(json.dumps(out["summary"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
