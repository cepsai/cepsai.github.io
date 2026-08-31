#!/usr/bin/env python3
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import date, timedelta

API = "https://openrouter.ai/api/v1/datasets/rankings-daily"
START = "2025-01-01"

OPEN_ORGS = {
    "meta-llama", "deepseek", "qwen", "z-ai", "thudm", "moonshotai", "nvidia",
    "microsoft", "mistralai", "nousresearch", "gryphe", "sao10k", "thedrummer",
    "undi95", "neversleep", "cognitivecomputations", "sophosympatheia",
    "alpindale", "eva-unit-01", "allenai", "ai21", "liquid", "minimax", "01-ai",
    "opengvlab", "baidu", "tencent", "tngtech", "agentica-org", "arcee-ai",
    "rekaai", "eleutherai", "huggingfaceh4", "cohere", "anthracite-org",
    "latitudegames", "scb10x", "shisa-ai", "aion-labs", "bytedance-research",
    "xiaomi", "stepfun", "inclusionai", "openchat",
}
PROP_ORGS = {
    "openai", "anthropic", "google", "x-ai", "perplexity", "amazon",
    "inflection", "inception", "morph", "poolside",
}
CLOAKED_ORGS = {"openrouter", "stealth"}
CLOAKED_REVEALED_PROP = (
    "quasar-alpha", "optimus-alpha", "horizon-alpha", "horizon-beta",
    "sonoma-sky-alpha", "sonoma-dusk-alpha", "polaris-alpha",
    "sherlock-think-alpha", "sherlock-dash-alpha",
)
OPEN_SLUG_OVERRIDES = ("gpt-oss", "gemma")
PROP_SLUG_OVERRIDES = (
    "mistral-large", "mistral-medium", "magistral-medium", "codestral",
    "mistral-saba", "pixtral-large", "devstral-medium",
)
SKIP_SLUGS = {"other", "openrouter/auto"}


def classify(slug):
    s = slug.lower()
    if s in SKIP_SLUGS:
        return "other"
    for frag in OPEN_SLUG_OVERRIDES:
        if frag in s:
            return "open"
    for frag in PROP_SLUG_OVERRIDES:
        if frag in s:
            return "prop"
    org = s.split("/")[0]
    if org in CLOAKED_ORGS:
        name = s.split("/", 1)[-1]
        return "prop" if name in CLOAKED_REVEALED_PROP else "excluded"
    if org in OPEN_ORGS:
        return "open"
    if org in PROP_ORGS:
        return "prop"
    return "unclassified"


def fetch_range(key, start, end, tries=4):
    url = f"{API}?start_date={start}&end_date={end}&period=month"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                payload = json.load(r)
            break
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            code = getattr(e, "code", None)
            body = e.read().decode("utf-8", "replace")[:500] if hasattr(e, "read") else str(e)
            retryable = code is None or code >= 500 or code == 429
            if retryable and attempt < tries - 1:
                wait = 5 * (attempt + 1)
                print(f"HTTP {code or 'error'} for {start}..{end}, retrying in {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            raise RuntimeError(f"HTTP {code} for {start}..{end}: {body}") from None
    rows = payload.get("data", payload)
    if isinstance(rows, dict):
        rows = rows.get("rows", [])
    return rows


def main():
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("Set OPENROUTER_API_KEY (any OpenRouter inference key works).")

    end = date.today() - timedelta(days=1)
    start = date.fromisoformat(START)
    if (end - start).days <= 366:
        rows = fetch_range(key, start, end)
    else:
        rows = []
        for y in range(start.year, end.year + 1):
            s = max(date(y, 1, 1), start)
            e2 = min(date(y, 12, 31), end)
            rows += fetch_range(key, s, e2)

    monthly = defaultdict(lambda: defaultdict(int))
    unknown = defaultdict(int)
    excluded_tokens = 0
    for r in rows:
        month = str(r["date"])[:7] + "-01"
        tokens = int(float(r["total_tokens"]))
        cat = classify(r["model_permaslug"])
        if cat == "excluded":
            excluded_tokens += tokens
            continue
        if cat == "unclassified":
            unknown[r["model_permaslug"]] += tokens
            cat = "other"
        monthly[month][cat] += tokens

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "openrouter_share.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["month", "open_tokens", "prop_tokens", "other_tokens", "total_tokens"])
        for month in sorted(monthly):
            m = monthly[month]
            total = m["open"] + m["prop"] + m["other"]
            w.writerow([month, m["open"], m["prop"], m["other"], total])
    print(f"wrote {out} ({len(monthly)} months)")
    kept = sum(m["open"] + m["prop"] + m["other"] for m in monthly.values())
    if excluded_tokens:
        print(f"excluded {excluded_tokens:,} tokens from still-anonymous stealth models "
              f"({excluded_tokens / max(1, kept + excluded_tokens):.1%} of the pull)")

    if unknown:
        rep = os.path.join(os.path.dirname(out), "unclassified_models.txt")
        with open(rep, "w") as f:
            for slug, tok in sorted(unknown.items(), key=lambda x: -x[1]):
                f.write(f"{tok:>20,}  {slug}\n")
        share = sum(unknown.values()) / max(1, sum(
            m["open"] + m["prop"] + m["other"] for m in monthly.values()))
        print(f"{len(unknown)} unclassified slugs ({share:.1%} of tokens) -> {rep}")
        print("Extend OPEN_ORGS/PROP_ORGS and re-run; they count as 'other' until then.")


if __name__ == "__main__":
    main()
