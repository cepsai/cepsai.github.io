#!/usr/bin/env python3
"""Discover live Lovable-deployed apps from public sources.

Sources:
  1. Certificate Transparency logs via crt.sh (*.lovable.app, *.lovable.dev)
  2. madewithlovable.com sitemap → each project page → all outbound non-social links
     (yields both lovable.app URLs and custom-domain apps invisible to CT logs)
  3. Liveness check on the union

Writes data/discovered_apps.json with per-app URL, liveness, title, description,
sources (which discovery channels surfaced it), and summary stats.
"""
from __future__ import annotations

import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "discovered_apps.json"

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
}
FETCH_TIMEOUT = 30
MWL_TIMEOUT = 60
CRT_TIMEOUT = 180
LIVE_WORKERS = 16
MWL_WORKERS = 4  # MWL seems rate-sensitive

KNOWN_INFRA_LABELS = {
    "www", "app", "api", "docs", "blog", "dashboard", "admin", "auth",
    "preview", "staging", "dev", "status", "help", "support", "mail",
    "email", "cdn", "static", "assets", "launched", "editor", "cloud",
    "supabase", "github", "ceo",
}
# Hosts we treat as "not an app URL" when parsing MWL project pages
EXCLUDED_DOMAINS = {
    "madewithlovable.com", "twitter.com", "x.com", "linkedin.com", "github.com",
    "facebook.com", "instagram.com", "youtube.com", "youtu.be", "tiktok.com",
    "producthunt.com", "discord.gg", "discord.com", "reddit.com", "medium.com",
    "substack.com", "notion.so", "notion.site", "mailchi.mp", "calendly.com",
    "apple.com", "apps.apple.com", "play.google.com", "chrome.google.com",
    "t.me", "threads.net", "bsky.app", "mastodon.social",
}
# lovable.dev refs that aren't apps (marketing, auth, referral)
LOVABLE_NON_APP_PATHS = re.compile(r"^/($|login|signup|pricing|blog|solutions|videos|company|examples|terms|privacy|changelog|affiliate|learn|\?via=)", re.I)


def crt_sh(domain: str) -> list[str]:
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    r = requests.get(url, headers=HEADERS, timeout=CRT_TIMEOUT)
    r.raise_for_status()
    entries = r.json()
    subs: set[str] = set()
    for e in entries:
        for name in ((e.get("name_value") or "") + "\n" + (e.get("common_name") or "")).split("\n"):
            name = name.strip().lower().lstrip("*.")
            if name.endswith("." + domain) and name != domain:
                subs.add(name)
    return sorted(subs)


def mwl_project_urls() -> list[str]:
    url = "https://madewithlovable.com/sitemap_projects.xml"
    r = requests.get(url, headers=HEADERS, timeout=CRT_TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "xml")
    return [loc.get_text(strip=True) for loc in soup.find_all("loc")]


def _normalize_host(u: str) -> str:
    try:
        return urlparse(u).netloc.lower().lstrip("www.")
    except Exception:
        return ""


def _is_app_link(u: str) -> bool:
    try:
        p = urlparse(u)
    except Exception:
        return False
    if p.scheme not in ("http", "https"):
        return False
    host = p.netloc.lower()
    if not host:
        return False
    if host.startswith("www."):
        host = host[4:]
    if host in EXCLUDED_DOMAINS:
        return False
    for excl in EXCLUDED_DOMAINS:
        if host.endswith("." + excl):
            return False
    # Non-app lovable.dev marketing paths
    if host == "lovable.dev":
        if LOVABLE_NON_APP_PATHS.search(p.path or "/"):
            return False
    return True


def parse_mwl_page(url: str) -> dict:
    """Fetch one MWL project page, extract outbound app links + project metadata."""
    rec: dict = {"mwl_url": url, "project_slug": url.rstrip("/").split("/")[-1], "app_urls": [], "project_title": None, "fetch_status": None}
    try:
        r = requests.get(url, headers=HEADERS, timeout=MWL_TIMEOUT, allow_redirects=True)
        rec["fetch_status"] = r.status_code
        if r.status_code != 200:
            return rec
        soup = BeautifulSoup(r.text, "html.parser")
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            # strip " | Made with Lovable" suffix if present
            title = re.sub(r"\s*[|\-]\s*Made with Lovable\s*$", "", title, flags=re.I)
            rec["project_title"] = title[:180]
        # All outbound links
        links: set[str] = set()
        for a in soup.find_all("a", href=True):
            h = a["href"].strip()
            if h.startswith("//"):
                h = "https:" + h
            if _is_app_link(h):
                # Normalize: strip query strings that are just tracking
                p = urlparse(h)
                clean_query = p.query if not re.search(r"(via|ref|utm_)=", p.query or "", re.I) else ""
                clean = f"{p.scheme}://{p.netloc}{p.path}"
                if clean_query:
                    clean += "?" + clean_query
                links.add(clean.rstrip("/"))
        rec["app_urls"] = sorted(links)
    except requests.exceptions.Timeout:
        rec["fetch_status"] = "timeout"
    except requests.exceptions.RequestException as e:
        rec["fetch_status"] = f"error:{type(e).__name__}"
    return rec


def fetch_app_page(url: str) -> dict:
    rec: dict = {"url": url, "final_url": None, "status": None, "title": None, "description": None, "og_title": None, "og_description": None}
    try:
        r = requests.get(url, headers=HEADERS, timeout=FETCH_TIMEOUT, allow_redirects=True)
        rec["status"] = r.status_code
        rec["final_url"] = r.url
        ctype = r.headers.get("content-type", "").lower()
        if r.status_code < 400 and "text/html" in ctype:
            soup = BeautifulSoup(r.text[:300_000], "html.parser")
            if soup.title and soup.title.string:
                rec["title"] = soup.title.string.strip()[:240]
            md = soup.find("meta", attrs={"name": "description"})
            if md and md.get("content"):
                rec["description"] = md["content"].strip()[:600]
            og = soup.find("meta", attrs={"property": "og:title"})
            if og and og.get("content"):
                rec["og_title"] = og["content"].strip()[:240]
            ogd = soup.find("meta", attrs={"property": "og:description"})
            if ogd and ogd.get("content"):
                rec["og_description"] = ogd["content"].strip()[:600]
    except requests.exceptions.Timeout:
        rec["status"] = "timeout"
    except requests.exceptions.RequestException as e:
        rec["status"] = f"error:{type(e).__name__}"
    return rec


def is_infra_subdomain(sub: str) -> bool:
    # sub like foo.lovable.app
    parts = sub.split(".")
    if len(parts) < 3:
        return True
    label = parts[0]
    return label in KNOWN_INFRA_LABELS


def canonical_url(url: str) -> str:
    p = urlparse(url)
    host = p.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = p.path.rstrip("/") or "/"
    return f"{p.scheme}://{host}{path}"


def main() -> int:
    DATA.mkdir(exist_ok=True)

    # -------- Source 1: CT logs --------
    ct_subs: dict[str, list[str]] = {}
    for domain in ("lovable.app", "lovable.dev"):
        print(f"[crt.sh] querying *.{domain} (timeout {CRT_TIMEOUT}s)...", flush=True)
        try:
            subs = crt_sh(domain)
            for s in subs:
                ct_subs.setdefault(s, []).append(f"crt_sh:{domain}")
            print(f"  got {len(subs)} unique subdomains for {domain}")
        except Exception as e:
            print(f"  [crt.sh] {domain} failed: {e}", file=sys.stderr)

    # -------- Source 2: MWL project pages --------
    print("[mwl] fetching project sitemap...", flush=True)
    mwl_urls: list[str] = []
    try:
        mwl_urls = mwl_project_urls()
        print(f"  got {len(mwl_urls)} project page URLs")
    except Exception as e:
        print(f"  [mwl] sitemap failed: {e}", file=sys.stderr)

    print(f"[mwl] fetching {len(mwl_urls)} project pages (workers={MWL_WORKERS}, slow to respect rate limits)...", flush=True)
    mwl_records: list[dict] = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=MWL_WORKERS) as ex:
        futs = {ex.submit(parse_mwl_page, u): u for u in mwl_urls}
        for i, f in enumerate(as_completed(futs), 1):
            mwl_records.append(f.result())
            if i % 10 == 0:
                nonempty = sum(1 for m in mwl_records if m["app_urls"])
                print(f"  [mwl] {i}/{len(mwl_urls)} pages, {nonempty} with outbound links ({time.time()-t0:.0f}s elapsed)", flush=True)

    # Build URL -> sources map from MWL
    mwl_url_sources: dict[str, list[str]] = {}
    mwl_url_project: dict[str, str] = {}  # map app URL → MWL slug for enrichment
    for mrec in mwl_records:
        for appu in mrec["app_urls"]:
            c = canonical_url(appu)
            mwl_url_sources.setdefault(c, []).append(f"mwl:{mrec['project_slug']}")
            mwl_url_project[c] = mrec["project_slug"]

    # -------- Union: combine CT subs (as https://sub) and MWL app URLs --------
    combined: dict[str, list[str]] = {}
    # CT subs — drop infra
    for sub, sources in ct_subs.items():
        if is_infra_subdomain(sub):
            continue
        url = f"https://{sub}"
        c = canonical_url(url)
        combined.setdefault(c, []).extend(sources)
    # MWL URLs
    for u, sources in mwl_url_sources.items():
        combined.setdefault(u, []).extend(sources)

    # Dedup sources per URL
    for u in combined:
        combined[u] = sorted(set(combined[u]))

    print(f"\n[union] {len(combined)} unique app-URL candidates (CT + MWL)")

    # -------- Liveness check --------
    print(f"[liveness] fetching {len(combined)} URLs (workers={LIVE_WORKERS})...", flush=True)
    records: list[dict] = []
    t1 = time.time()
    with ThreadPoolExecutor(max_workers=LIVE_WORKERS) as ex:
        futs = {ex.submit(fetch_app_page, u): u for u in combined}
        for i, f in enumerate(as_completed(futs), 1):
            u = futs[f]
            rec = f.result()
            rec["sources"] = combined[u]
            if u in mwl_url_project:
                rec["mwl_project_slug"] = mwl_url_project[u]
            records.append(rec)
            if i % 50 == 0:
                live = sum(1 for r in records if isinstance(r.get("status"), int) and 200 <= r["status"] < 300)
                print(f"  [liveness] {i}/{len(combined)} checked, {live} live-2xx ({time.time()-t1:.0f}s)", flush=True)

    # Partition by host for stats
    def host_of(u: str) -> str:
        try:
            h = urlparse(u).netloc.lower()
            return h.lstrip("www.")
        except Exception:
            return ""

    def platform(u: str) -> str:
        h = host_of(u)
        if h.endswith("lovable.app"):
            return "lovable.app"
        if h.endswith("lovable.dev"):
            return "lovable.dev"
        return "custom_domain"

    for r in records:
        r["platform"] = platform(r["url"])

    def status_bucket(r: dict) -> str:
        s = r["status"]
        if isinstance(s, int):
            if 200 <= s < 300:
                return "live_2xx"
            if 300 <= s < 400:
                return "redirect_3xx"
            if 400 <= s < 500:
                return "dead_4xx"
            return "error_5xx"
        return "timeout_or_error"

    buckets: dict[str, int] = {}
    by_platform: dict[str, int] = {}
    live_by_platform: dict[str, int] = {}
    for r in records:
        b = status_bucket(r)
        buckets[b] = buckets.get(b, 0) + 1
        by_platform[r["platform"]] = by_platform.get(r["platform"], 0) + 1
        if b == "live_2xx":
            live_by_platform[r["platform"]] = live_by_platform.get(r["platform"], 0) + 1

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "crt_sh_lovable_app_count": sum(1 for s in ct_subs if s.endswith(".lovable.app")),
        "crt_sh_lovable_dev_count": sum(1 for s in ct_subs if s.endswith(".lovable.dev")),
        "mwl_project_pages_total": len(mwl_urls),
        "mwl_project_pages_parsed_ok": sum(1 for m in mwl_records if m["fetch_status"] == 200),
        "mwl_unique_app_urls_extracted": len(mwl_url_sources),
        "unique_app_url_candidates_total": len(combined),
        "status_buckets": buckets,
        "candidates_by_platform": by_platform,
        "live_2xx_by_platform": live_by_platform,
    }

    out = {
        "summary": summary,
        "apps": sorted(records, key=lambda r: r["url"]),
        "mwl_projects": sorted(mwl_records, key=lambda r: r["project_slug"]),
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nwrote {OUT}")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
