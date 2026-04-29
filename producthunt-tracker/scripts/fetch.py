#!/usr/bin/env python3
"""
Fetches Product Hunt's public Atom feed, normalizes each entry, and merges into
a rolling history at ../data/history.json. Writes a dashboard payload to
../docs/data.json containing today, yesterday, and the last 7 days bucketed
by launch date.

The Atom feed is unauthenticated and contains the latest ~50 launches with
title, tagline, maker, product URL, and the original publish timestamp. That
is enough for a morning digest. If a Product Hunt developer token is later
added (env PH_API_TOKEN), the GraphQL enrichment block in `enrich_via_api`
will fill in vote counts and topic tags.
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"
HISTORY_FILE = DATA_DIR / "history.json"
DASHBOARD_FILE = DOCS_DIR / "data.json"

FEED_URL = "https://www.producthunt.com/feed"
ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}

# Brussels-friendly default. The tracker is hosted on cepsai.github.io and the
# user is at CEPS in Brussels — Europe/Brussels is UTC+1 in winter, UTC+2 in
# summer. We bucket products by *Brussels* date so "today" matches the user's
# morning.
DISPLAY_TZ_OFFSET_HOURS = 2  # CEST (Apr-Oct). Good enough; not load-bearing.


USER_AGENT = "cepsai-producthunt-tracker/1.0 (+https://cepsai.github.io)"


def _http_get(url: str, headers: dict | None = None, data: bytes | None = None, timeout: int = 30) -> str:
    """GET (or POST if data) a URL. Falls back to curl when the stdlib SSL store
    can't verify the chain — common on python.org Python on macOS."""
    headers = {"User-Agent": USER_AGENT, **(headers or {})}
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.URLError as e:
        if not isinstance(e.reason, ssl.SSLError):
            raise
        if not shutil.which("curl"):
            raise
        cmd = ["curl", "-sSL", "--max-time", str(timeout), "-A", USER_AGENT]
        for k, v in headers.items():
            cmd += ["-H", f"{k}: {v}"]
        if data is not None:
            cmd += ["--data-binary", "@-"]
        cmd.append(url)
        result = subprocess.run(
            cmd, input=data, capture_output=True, check=True, timeout=timeout + 5,
        )
        return result.stdout.decode("utf-8")


def fetch_feed() -> str:
    return _http_get(FEED_URL)


def strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def parse_entry(entry: ET.Element) -> dict | None:
    def text(tag: str) -> str:
        el = entry.find(f"a:{tag}", ATOM_NS)
        return (el.text or "").strip() if el is not None and el.text else ""

    raw_id = text("id")  # e.g. tag:www.producthunt.com,2005:Post/1124845
    m = re.search(r"Post/(\d+)", raw_id)
    if not m:
        return None
    post_id = m.group(1)

    title = text("title")
    published = text("published")
    updated = text("updated")

    link_el = entry.find("a:link[@rel='alternate']", ATOM_NS)
    url = link_el.get("href") if link_el is not None else ""

    author_el = entry.find("a:author/a:name", ATOM_NS)
    maker = (author_el.text or "").strip() if author_el is not None and author_el.text else ""

    content_el = entry.find("a:content", ATOM_NS)
    content_raw = content_el.text or "" if content_el is not None else ""
    # Tagline is the first <p> block. The second <p> is just "Discussion | Link".
    paragraphs = re.findall(r"<p>(.*?)</p>", content_raw, re.DOTALL)
    tagline = strip_html(paragraphs[0]) if paragraphs else ""
    discussion_url = url
    external_url = ""
    if len(paragraphs) > 1:
        link_match = re.search(r'href="([^"]*r/p/\d+[^"]*)"', paragraphs[1])
        if link_match:
            external_url = html.unescape(link_match.group(1))

    return {
        "id": post_id,
        "title": title,
        "tagline": tagline,
        "maker": maker,
        "url": url,
        "discussion_url": discussion_url,
        "external_url": external_url,
        "published": published,
        "updated": updated,
    }


def to_display_date(iso_ts: str) -> str:
    """Convert an ISO timestamp to a Brussels-local YYYY-MM-DD bucket."""
    if not iso_ts:
        return ""
    try:
        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    except ValueError:
        return ""
    local = dt.astimezone(timezone(timedelta(hours=DISPLAY_TZ_OFFSET_HOURS)))
    return local.date().isoformat()


def load_history() -> dict:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {"products": {}}


def save_history(history: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, indent=2, sort_keys=True))


def merge(history: dict, new_entries: list[dict], fetched_at: str) -> dict:
    products = history.setdefault("products", {})
    for entry in new_entries:
        existing = products.get(entry["id"], {})
        first_seen = existing.get("first_seen", fetched_at)
        # Preserve any enrichment fields we may have added later (votes, topics).
        merged = {**existing, **entry, "first_seen": first_seen, "last_seen": fetched_at}
        products[entry["id"]] = merged
    history["last_fetched_at"] = fetched_at
    return history


def build_dashboard_payload(history: dict) -> dict:
    products = list(history.get("products", {}).values())
    for p in products:
        p["display_date"] = to_display_date(p.get("published", ""))

    by_date: dict[str, list[dict]] = {}
    for p in products:
        d = p["display_date"]
        if not d:
            continue
        by_date.setdefault(d, []).append(p)

    # Within a bucket: most-recently-published first.
    for d in by_date:
        by_date[d].sort(key=lambda x: x.get("published", ""), reverse=True)

    today = datetime.now(timezone(timedelta(hours=DISPLAY_TZ_OFFSET_HOURS))).date()
    days = [(today - timedelta(days=i)).isoformat() for i in range(7)]

    return {
        "generated_at": history.get("last_fetched_at"),
        "tz": f"UTC+{DISPLAY_TZ_OFFSET_HOURS}",
        "days": [{"date": d, "products": by_date.get(d, [])} for d in days],
        "total_tracked": len(products),
    }


def enrich_via_api(entries: list[dict]) -> None:
    """Optional: enrich entries with votes/topics via Product Hunt GraphQL.

    No-op unless PH_API_TOKEN is set. Kept here so the workflow can switch on
    enrichment by adding a secret without code changes.
    """
    token = os.environ.get("PH_API_TOKEN")
    if not token:
        return
    url = "https://api.producthunt.com/v2/api/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "cepsai-producthunt-tracker/1.0",
    }
    for e in entries:
        slug_match = re.search(r"/products/([^/?#]+)", e.get("url", ""))
        if not slug_match:
            continue
        slug = slug_match.group(1)
        query = {
            "query": (
                "query($slug:String!){post(slug:$slug){votesCount commentsCount "
                "thumbnail{url} topics(first:5){edges{node{name slug}}}}}"
            ),
            "variables": {"slug": slug},
        }
        body = json.dumps(query).encode("utf-8")
        try:
            payload = json.loads(_http_get(url, headers=headers, data=body, timeout=15))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, subprocess.SubprocessError):
            continue
        post = (payload.get("data") or {}).get("post") or {}
        if not post:
            continue
        e["votes"] = post.get("votesCount")
        e["comments"] = post.get("commentsCount")
        thumb = post.get("thumbnail") or {}
        e["thumbnail"] = thumb.get("url")
        topics = post.get("topics", {}).get("edges", [])
        e["topics"] = [t["node"]["name"] for t in topics if t.get("node")]


def main() -> int:
    feed_xml = fetch_feed()
    root = ET.fromstring(feed_xml)
    entries: list[dict] = []
    for entry_el in root.findall("a:entry", ATOM_NS):
        parsed = parse_entry(entry_el)
        if parsed:
            entries.append(parsed)

    if not entries:
        print("no entries parsed from feed", file=sys.stderr)
        return 1

    enrich_via_api(entries)

    fetched_at = datetime.now(timezone.utc).isoformat()
    history = merge(load_history(), entries, fetched_at)
    save_history(history)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_dashboard_payload(history)
    DASHBOARD_FILE.write_text(json.dumps(payload, indent=2))

    today_count = len(payload["days"][0]["products"])
    print(f"fetched {len(entries)} entries, {today_count} for today, {payload['total_tracked']} tracked total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
