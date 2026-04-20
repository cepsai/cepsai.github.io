#!/usr/bin/env python3
"""
fetch_laws.py — download and parse the law texts referenced by the Digital
AI Lexicon into structured JSON files in this directory.

Output files (one per law):
    eu-ai-act.json            (fetched from artificialintelligenceact.eu)
    co-sb24-205.json          (fetched from leg.colorado.gov)
    ca-sb53.json              (fetched from leginfo.legislature.ca.gov)
    ca-sb942.json             (fetched from leginfo.legislature.ca.gov)
    ca-ab2013.json            (fetched from leginfo.legislature.ca.gov)
    ny-s8828.json             (fetched from nysenate.gov)
    ny-a6453.json             (fetched from nysenate.gov)
    tx-hb149.json             (fetched from capitol.texas.gov)
    ut-sb226.json             (fetched from le.utah.gov)

JSON schema:
{
  "id": "eu-ai-act",
  "title": "Regulation (EU) 2024/1689 (AI Act)",
  "url":   "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
  "articles": [
     {"id": "3", "title": "Definitions", "text": "...", "paras": {"1": "...", "2": "..."}},
     ...
  ],
  "annexes": {"III": {"text": "..."}},
  "recitals": {"12": "..."},
}

Only one law per run, to keep noise manageable:
    python3 fetch_laws.py eu-ai-act
    python3 fetch_laws.py all
"""
from __future__ import annotations

import concurrent.futures as futures
import json
import re
import ssl
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) "
      "Version/17.0 Safari/605.1.15")


def http_get(url: str, timeout: int = 30) -> str:
    """Fetch URL with a browser UA; return decoded text.

    Writes curl's output to a tempfile (not `capture_output=True` pipe) because
    subprocess pipes truncate responses above ~150 KB for archive.org's
    gzip-heavy payloads. Retries transient failures (archive.org sometimes
    returns an empty body on first attempt, then succeeds)."""
    import tempfile, os, time
    last_err = None
    for attempt in range(3):
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".html") as tf:
            tmp_path = tf.name
        try:
            res = subprocess.run(
                ["curl", "-sL", "--max-time", str(timeout),
                 "-A", UA,
                 "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                 "-H", "Accept-Language: en-US,en;q=0.9",
                 "-o", tmp_path, url],
                capture_output=True, timeout=timeout + 5,
            )
            if res.returncode != 0:
                last_err = f"curl rc={res.returncode}: {res.stderr.decode(errors='replace').strip()}"
            else:
                size = os.path.getsize(tmp_path)
                if size < 1024:  # plausibly an error page / 404 stub
                    last_err = f"short response: {size} bytes"
                else:
                    with open(tmp_path, "rb") as f:
                        data = f.read()
                    try:
                        return data.decode("utf-8")
                    except UnicodeDecodeError:
                        return data.decode("latin-1", errors="replace")
        finally:
            try: os.unlink(tmp_path)
            except OSError: pass
        if attempt < 2:
            time.sleep(1 + attempt)  # simple linear backoff
    raise RuntimeError(f"curl {url}: {last_err}")


def strip_html(raw: str) -> str:
    """Drop scripts/styles and tags, decode entities, collapse whitespace."""
    import html as _html
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<br\s*/?>", "\n", raw, flags=re.I)
    raw = re.sub(r"</?(p|div|li|h\d)[^>]*>", "\n", raw, flags=re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    # Decode all HTML entities (named + numeric, incl. &#xA0; used by TX bills).
    raw = _html.unescape(raw)
    raw = raw.replace("\u00a0", " ")
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip()


# ============================================================================
# EU AI Act — fetched article-by-article from artificialintelligenceact.eu
# ============================================================================

AIA_SITE = "https://artificialintelligenceact.eu"


def fetch_aia_one(kind: str, ident: str) -> dict | None:
    """kind in {'article','recital','annex'}."""
    url = f"{AIA_SITE}/{kind}/{ident}/"
    try:
        html = http_get(url, timeout=20)
    except Exception as e:
        print(f"  fail {kind} {ident}: {e}", flush=True)
        return None
    if "404" in html[:400]:
        return None

    # Title: <h1 class="et_pb_module_header"> or <h1> near top
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S | re.I)
    title = strip_html(m.group(1)) if m else f"{kind.title()} {ident}"

    # Body: look for an <article> element or a main content div.
    body_html = html
    m2 = re.search(r'<div class="[^"]*post-content[^"]*">(.*?)</div>\s*<!--\s*.entry-content', html, re.S)
    if not m2:
        m2 = re.search(r'<div class="[^"]*entry-content[^"]*">(.*?)</div>', html, re.S)
    if m2:
        body_html = m2.group(1)

    text = strip_html(body_html)
    # Trim common footer junk / "Related content" etc.
    text = re.split(r"\n\s*(?:Previous|Next|Related\s+content|Suitable\s+Recitals|Related:|Connect\s+with\s+us)",
                    text, maxsplit=1)[0].strip()

    return {"id": str(ident), "title": title, "text": text}


def parse_paragraphs(text: str) -> dict[str, str]:
    """Split an article body into paragraphs keyed by their label.

    Handles the typical EU style:
        1.   <sentence>
        (a)  <sentence>
        (i)  <sentence>
    Paragraph labels are treated as top-level keys; nested letters are folded
    into their parent.
    """
    paras: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for ln in text.split("\n"):
        ln = ln.strip()
        if not ln:
            continue
        # matches "1." or "(1)" at start
        m = re.match(r"^\(?(\d+)\)?\.?\s+(.*)$", ln)
        if m:
            if current is not None and buf:
                paras[current] = " ".join(buf).strip()
            current = m.group(1)
            buf = [m.group(2)]
        else:
            buf.append(ln)
    if current is not None and buf:
        paras[current] = " ".join(buf).strip()
    return paras


def fetch_eu_ai_act() -> dict:
    print("== EU AI Act (artificialintelligenceact.eu)")
    articles: list[dict] = []
    recitals: dict[str, str] = {}
    annexes: dict[str, dict] = {}

    # Articles 1..113. Parallelize with a thread pool.
    def fetch_article(n: int):
        res = fetch_aia_one("article", str(n))
        if res:
            res["paras"] = parse_paragraphs(res["text"])
        return (n, res)

    with futures.ThreadPoolExecutor(max_workers=6) as ex:
        for n, res in ex.map(fetch_article, range(1, 114)):
            if res:
                articles.append(res)
                print(f"  art {n}: {res['title'][:60]!r}  paras={len(res.get('paras',{}))}", flush=True)
            else:
                print(f"  art {n}: (skipped)", flush=True)
            time.sleep(0.05)

    # Recitals 1..180 (parallel, we only embed a subset cited by the lexicon to
    # keep the JSON size in check — but fetch them all and filter later.)
    CITED_RECITALS = {12, 13, 128, 177}
    def fetch_recital(n: int):
        if n not in CITED_RECITALS:
            return (n, None)
        return (n, fetch_aia_one("recital", str(n)))

    with futures.ThreadPoolExecutor(max_workers=4) as ex:
        for n, res in ex.map(fetch_recital, range(1, 181)):
            if res:
                recitals[str(n)] = res["text"]
                print(f"  recital {n}: ok", flush=True)

    # Annexes I..XIII (Roman numerals). We want III, IV, XI, XII at minimum.
    for roman in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII"]:
        res = fetch_aia_one("annex", roman)
        if res:
            annexes[roman] = {"text": res["text"], "title": res["title"]}
            print(f"  annex {roman}: ok", flush=True)

    return {
        "id": "eu-ai-act",
        "title": "Regulation (EU) 2024/1689 (AI Act)",
        "url":   "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
        "articles": articles,
        "annexes":  annexes,
        "recitals": recitals,
    }


# ============================================================================
# US state laws — each fetched in a single request (bill text page)
# ============================================================================

def parse_section_sequence(text: str, label_re: str) -> list[dict]:
    """Generic splitter: given law text and a section-label regex (matches the
    beginning of each section), return [{id, text}] split on those boundaries."""
    lines = text.split("\n")
    sections: list[dict] = []
    current_id: str | None = None
    buf: list[str] = []
    label_pat = re.compile(label_re)
    for ln in lines:
        s = ln.strip()
        m = label_pat.match(s)
        if m:
            if current_id is not None:
                sections.append({"id": current_id, "text": "\n".join(buf).strip()})
            current_id = m.group(1)
            buf = [s]
        else:
            buf.append(ln)
    if current_id is not None:
        sections.append({"id": current_id, "text": "\n".join(buf).strip()})
    return sections


def fetch_co_sb24205() -> dict:
    print("== Colorado SB24-205")
    # Final Act text URL at leg.colorado.gov
    url = "https://leg.colorado.gov/sites/default/files/2024a_205_signed.pdf"
    # PDF fetch is awkward without parsing. Fallback to the bill text HTML view:
    url_html = "https://leg.colorado.gov/bills/sb24-205"
    html = http_get(url_html, timeout=30)
    text = strip_html(html)
    # Split by "6-1-17xx" anchors (Colorado section numbering used in xlsx refs)
    sections = parse_section_sequence(text, r"^§?\s*6-1-(1\d{3})\b")
    return {"id": "co-sb24-205", "title": "Colorado SB 24-205 (Colorado AI Act)", "url": url_html,
            "sections": sections, "raw_text": text[:200000]}


def fetch_ca_bill(bill_code: str, bill_id: str, name: str) -> dict:
    """Fetch California leginfo bill text page."""
    print(f"== California {bill_code}")
    url = f"https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id={bill_id}"
    try:
        html = http_get(url, timeout=30)
        text = strip_html(html)
    except Exception as e:
        print(f"  fetch failed: {e}")
        text = ""
    sections = parse_section_sequence(text, r"^§?\s*(\d{4,5}(?:\.\d+)?)\s*\.")
    return {"id": f"ca-{bill_code.lower().replace(' ','')}", "title": f"California {bill_code} ({name})",
            "url": url, "sections": sections, "raw_text": text[:300000]}


def _strip_wayback(html: str) -> str:
    """Remove Internet Archive's injected banner/toolbar so we get clean source HTML."""
    html = re.sub(r"<!-- BEGIN WAYBACK TOOLBAR INSERT -->.*?<!-- END WAYBACK TOOLBAR INSERT -->",
                  " ", html, flags=re.S)
    html = re.sub(r'<div id="wm-ipp[^"]*"[^>]*>.*?</div>', " ", html, flags=re.S)
    html = re.sub(r"<iframe[^>]*src=[^>]*web\.archive[^>]*></iframe>", " ", html, flags=re.I)
    return html


def fetch_ny_bill(wayback_url: str, display_code: str, name: str, law_id: str) -> dict:
    """Fetch a New York bill. nysenate.gov is behind Cloudflare's JS challenge,
    so we pull the Internet-Archive mirror instead. The toolbar needs stripping."""
    print(f"== {display_code} ({law_id}) via Wayback")
    try:
        html = http_get(wayback_url, timeout=30)
        html = _strip_wayback(html)
        text = strip_html(html)
    except Exception as e:
        print(f"  fetch failed: {e}")
        text = ""
    # NY RAISE-Act section labels look like "§ 1420." / "§ 1421-A." on the
    # first column of each paragraph. Accept both plain and dashed forms.
    sections = parse_section_sequence(text, r"^§\s*(1[34]\d{2}(?:[-A-Z]+)?)\.")
    # Fallback: if the strict pattern didn't match (the text may be wrapped),
    # split on occurrences of "§ 14xx." anywhere in the text.
    if not sections and "§" in text:
        parts = re.split(r"(§\s*1[34]\d{2}(?:[-A-Z]+)?\s*\.)", text)
        # parts = [pre, label, body, label, body, ...]
        for i in range(1, len(parts), 2):
            label = re.search(r"(1[34]\d{2}(?:[-A-Z]+)?)", parts[i]).group(1)
            sections.append({"id": label, "text": (parts[i] + parts[i+1] if i+1<len(parts) else parts[i]).strip()})
    return {
        "id": law_id,
        "title": f"New York {display_code} ({name})",
        "url": wayback_url,
        "sections": sections,
        "raw_text": text[:400000],
    }


def fetch_tx_hb149() -> dict:
    print("== Texas HB149")
    url = "https://capitol.texas.gov/tlodocs/89R/billtext/html/HB00149F.HTM"
    try:
        html = http_get(url, timeout=30)
        text = strip_html(html)
    except Exception as e:
        print(f"  fetch failed: {e}")
        text = ""
    # TX section labels look like "Sec. 552.104. SHORT TITLE." — line-anchored
    # splitting rarely matches after entity decode, so split anywhere in text.
    sections: list[dict] = []
    parts = re.split(r"(Sec\.?\s+(?:552|503)\.\d{3}\s*\.?)", text)
    if len(parts) >= 3:
        # parts = [pre, label, body, label, body, ...]
        for i in range(1, len(parts), 2):
            m = re.search(r"((?:552|503)\.\d{3})", parts[i])
            if not m:
                continue
            sid = m.group(1)
            body = (parts[i] + (parts[i+1] if i+1 < len(parts) else "")).strip()
            sections.append({"id": sid, "text": body})
    if not sections:
        sections = parse_section_sequence(
            text, r"^(?:Sec\.?\s*)?§?\s*((?:552|503)\.\d{3})")
    print(f"  tx sections parsed: {len(sections)} ids={[s['id'] for s in sections]}")
    return {"id": "tx-hb149", "title": "Texas HB 149 (TRAIGA)", "url": url,
            "sections": sections, "raw_text": text[:300000]}


def fetch_ut_sb226() -> dict:
    """Utah's 2025 SB 226 (AI Consumer Protection Amendments) — enrolled bill
    lives in Utah's legislative XML feed. The 2024 SB 226 with the same code
    number is an unrelated School of General Education Act; the AI chapter
    13-75 was originally enacted by SB 0149 (2024) and amended by this 2025
    SB 226. We pull the XML and extract each <section>…</section> block,
    keyed by the 13-75-N identifier embedded in the body."""
    print("== Utah SB 226 (2025 enrolled XML)")
    url = "https://le.utah.gov/Session/2025/bills/enrolled/SB0226.xml"
    try:
        xml = http_get(url, timeout=30)
    except Exception as e:
        print(f"  fetch failed: {e}")
        return {"id": "ut-sb226", "title": "Utah SB 226 (2025)", "url": url,
                "sections": [], "raw_text": ""}
    # Each enrolled section has the form
    #   <section>Section N, Section 13-75-XXX is enacted to read: 13-75-XXX
    #    <effect><date>...</date></effect> . Definitions. As used in this chapter: ...</section>
    sections: list[dict] = []
    for m in re.finditer(r"<section[^>]*>(.*?)</section>", xml, re.S):
        body_xml = m.group(1)
        # Extract the 13-75-xxx id (the target section being enacted).
        id_m = re.search(r"(13-75-\d{3})", body_xml)
        if not id_m:
            continue
        sid = id_m.group(1)
        txt = strip_html(body_xml)
        sections.append({"id": sid, "text": txt})
    return {
        "id": "ut-sb226",
        "title": "Utah SB 226 (Artificial Intelligence Consumer Protection Amendments, 2025)",
        "url": url,
        "sections": sections,
        "raw_text": strip_html(xml)[:200000],
    }


# ============================================================================
# Driver
# ============================================================================

JOBS = {
    "eu-ai-act":   fetch_eu_ai_act,
    "co-sb24-205": fetch_co_sb24205,
    "ca-sb53":     lambda: fetch_ca_bill("SB 53",  "202520260SB53",  "TFAI"),
    "ca-sb942":    lambda: fetch_ca_bill("SB 942", "202320240SB942", "California AI Transparency Act"),
    "ca-ab2013":   lambda: fetch_ca_bill("AB 2013","202320240AB2013","Generative AI Training Data Transparency"),
    # NB: the xlsx cites "NY S8828" but the RAISE Act (Senate) is actually
    # S6953 (2025). nysenate.gov is Cloudflare-protected for curl; we use
    # the Internet-Archive mirror to get clean HTML. We keep the law_id as
    # "ny-s8828" to match the REF_MAP built from the xlsx — the content
    # behind that id is the RAISE Act text regardless of bill-number drift.
    # Specific Wayback timestamps that have the full bill body (later
    # snapshots sometimes return an nysenate.gov error page under ~8 KB).
    # id_ suffix = Wayback's "raw capture" mode (skips the toolbar/iframe wrapper
    # and returns the exact bytes as captured). More stable than the live
    # snapshots, which sometimes serve an error stub.
    "ny-s8828":    lambda: fetch_ny_bill(
        "https://web.archive.org/web/20250512114728id_/https://www.nysenate.gov/legislation/bills/2025/S6953",
        "S6953", "RAISE Act", "ny-s8828",
    ),
    "ny-a6453":    lambda: fetch_ny_bill(
        "https://web.archive.org/web/20251218183710id_/https://www.nysenate.gov/legislation/bills/2025/A6453",
        "A6453", "RAISE Act (Assembly)", "ny-a6453",
    ),
    "tx-hb149":    fetch_tx_hb149,
    "ut-sb226":    fetch_ut_sb226,
}


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    jobs = list(JOBS.items()) if target == "all" else [(target, JOBS[target])]
    for jid, fn in jobs:
        out = HERE / f"{jid}.json"
        if out.exists() and "--force" not in sys.argv:
            print(f"skip {jid} (use --force to refetch)")
            continue
        t0 = time.time()
        data = fn()
        with out.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=None)
        print(f"wrote {out.name}  ({out.stat().st_size:,} bytes, {time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()
