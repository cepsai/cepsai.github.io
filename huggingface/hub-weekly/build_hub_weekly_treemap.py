#!/usr/bin/env python3
"""Build the data JSON for the Hugging Face Hub "weekly new releases" treemap.

Pulls the freshest weekly Hub snapshot from the dataset
`hfmlsoc/hub_weekly_snapshots` (the HF ML & Society Team's weekly Hub metadata
snapshots), finds the models and datasets created in the last 30 days of that
snapshot, and writes a compact JSON consumed by the treemap HTML.

What it does, step by step:
  1. Resolves the LATEST snapshot date dynamically via the HF tree API (the
     lexicographically max date dir under `models/`), and locates the single
     `.parquet` file inside the matching `models/<date>/` and `datasets/<date>/`
     directories. The snapshot date from the models dir is used as the single
     "as-of" anchor for BOTH item types.
  2. Runs ONE duckdb query per item type over the REMOTE parquet (via httpfs;
     no full files are downloaded to disk) filtering to items created in the
     30 days ending at the snapshot midnight.
  3. Caps each item type to the UNION of top-N rows across all four toggle
     states the HTML exposes (7d vs 30d window x dl/day vs likes/day metric),
     deduped by id, so no toggle view is ever truncated.
  4. Prints a validation report, fails loudly if either type is empty, then
     writes `hub_weekly_data.json` next to this script.

The client (HTML) recomputes per-day metrics and the 7d filter from
`createdAt` + `snapshot_date`, so per-day values are NOT baked into the JSON.

Run it (e.g. every Monday):
    python3 build_hub_weekly_treemap.py
"""

import json
import os
import sys
from datetime import datetime, timezone

import duckdb
import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Configurable constants
# ---------------------------------------------------------------------------
REPO = "hfmlsoc/hub_weekly_snapshots"
N = 250                # top-N kept per (window, metric) ranking
WINDOW_DAYS = 30       # creation lookback window (the full pulled window)
SHORT_WINDOW_DAYS = 7  # the "7d" toggle threshold (age_days <= 7)

API_TREE = "https://huggingface.co/api/datasets/{repo}/tree/main/{path}"
RESOLVE_URL = "https://huggingface.co/datasets/{repo}/resolve/main/{path}"

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hub_weekly_data.json")

# Only these fields are emitted per row (client recomputes the rest).
OUTPUT_FIELDS = ["id", "author", "task", "likes", "downloadsAllTime", "createdAt"]


# ---------------------------------------------------------------------------
# Snapshot resolution (HF tree API)
# ---------------------------------------------------------------------------
def _tree(path):
    """Return the list of tree entries (dicts with 'type' and 'path') for a dir."""
    url = API_TREE.format(repo=REPO, path=path) + "?recursive=false"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.json()


def latest_snapshot_date():
    """Lexicographically-max date dir under models/ -> the snapshot date string."""
    entries = _tree("models")
    date_dirs = [e["path"] for e in entries if e.get("type") == "directory"]
    if not date_dirs:
        raise SystemExit("ERROR: no model snapshot date directories found under models/ "
                         "(upstream layout may have changed).")
    latest = max(date_dirs)            # e.g. "models/2026-06-24"
    return latest.rsplit("/", 1)[-1]   # -> "2026-06-24"


def find_parquet(kind, date_str):
    """Return the parquet path inside <kind>/<date>/ (exactly one expected)."""
    dir_path = f"{kind}/{date_str}"
    entries = _tree(dir_path)
    parquets = [e["path"] for e in entries
                if e.get("type") == "file" and e["path"].endswith(".parquet")]
    if not parquets:
        raise SystemExit(f"ERROR: no .parquet file found in {dir_path} "
                         "(upstream layout may have changed).")
    return parquets[0]


def resolve_url(path):
    return RESOLVE_URL.format(repo=REPO, path=path)


# ---------------------------------------------------------------------------
# Per-type query over the remote parquet
# ---------------------------------------------------------------------------
def task_expr(kind):
    """The SQL expression that derives the grouping key 'task' per item type."""
    if kind == "models":
        return "COALESCE(NULLIF(pipeline_tag, ''), 'other')"
    # datasets: derive from the tags VARCHAR[]; strip the prefixes in SQL.
    return (
        "COALESCE("
        "  replace(list_filter(tags, x -> starts_with(x, 'task_categories:'))[1], 'task_categories:', ''),"
        "  replace(list_filter(tags, x -> starts_with(x, 'modality:'))[1], 'modality:', ''),"
        "  'other')"
    )


def query_type(con, kind, parquet_url, date_str):
    """Run the single 30-day query for one item type, return a pandas DataFrame."""
    anchor = f"TIMESTAMP '{date_str} 00:00:00'"
    sql = f"""
    WITH base AS (
      SELECT id, author, likes, downloadsAllTime, createdAt, tags,
             {task_expr(kind)} AS task,
             GREATEST(1.0, date_diff('second', createdAt, {anchor}) / 86400.0) AS age_days
      FROM read_parquet('{parquet_url}')
      WHERE createdAt >  {anchor} - INTERVAL {WINDOW_DAYS} DAY
        AND createdAt <= {anchor}
        AND COALESCE(author, '') <> ''
    )
    SELECT id, author, task, likes, downloadsAllTime, createdAt,
           downloadsAllTime / age_days AS dl_per_day,
           likes / age_days            AS likes_per_day,
           date_diff('second', createdAt, {anchor}) / 86400.0 AS age_days
    FROM base
    """
    return con.execute(sql).fetch_df()


# ---------------------------------------------------------------------------
# Top-N union capping (across all four toggle states)
# ---------------------------------------------------------------------------
def cap_union(df):
    """Keep the dedup'd union of top-N rows across the 4 toggle states.

    Toggle states: window in {7d, 30d} x metric in {dl_per_day, likes_per_day}.
    "within 7d" means age_days <= SHORT_WINDOW_DAYS.
    """
    df30 = df
    df7 = df[df["age_days"] <= SHORT_WINDOW_DAYS]

    keep_ids = set()
    for sub in (df30, df7):
        if sub.empty:
            continue
        keep_ids.update(sub.nlargest(N, "dl_per_day")["id"])
        keep_ids.update(sub.nlargest(N, "likes_per_day")["id"])

    kept = df[df["id"].isin(keep_ids)].drop_duplicates(subset="id")
    return kept, df7


# ---------------------------------------------------------------------------
# Row serialization
# ---------------------------------------------------------------------------
def to_records(df):
    """Emit only the 6 contract fields; createdAt as ISO8601, ints as ints."""
    records = []
    for _, r in df.iterrows():
        created = r["createdAt"]
        if isinstance(created, pd.Timestamp):
            created = created.isoformat()
        else:
            created = str(created)
        records.append({
            "id": r["id"],
            "author": r["author"],
            "task": r["task"],
            "likes": int(r["likes"]) if pd.notna(r["likes"]) else 0,
            "downloadsAllTime": int(r["downloadsAllTime"]) if pd.notna(r["downloadsAllTime"]) else 0,
            "createdAt": created,
        })
    return records


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    date_str = latest_snapshot_date()
    models_pq = find_parquet("models", date_str)
    datasets_pq = find_parquet("datasets", date_str)
    models_url = resolve_url(models_pq)
    datasets_url = resolve_url(datasets_pq)

    print("=" * 72)
    print("HF Hub weekly treemap — validation report")
    print("=" * 72)
    print(f"Resolved snapshot date : {date_str}")
    print(f"Models parquet URL     : {models_url}")
    print(f"Datasets parquet URL   : {datasets_url}")
    print(f"Window                 : last {WINDOW_DAYS} days (anchor = {date_str} 00:00:00)")
    print(f"Top-N per ranking      : {N}")
    print("-" * 72)

    con = duckdb.connect()
    con.execute("INSTALL httpfs;")
    con.execute("LOAD httpfs;")

    out = {
        "snapshot_date": date_str,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    for kind, url in (("models", models_url), ("datasets", datasets_url)):
        print(f"[{kind}] querying remote parquet (this can take ~30s)...")
        df = query_type(con, kind, url, date_str)
        total_30d = len(df)
        n_7d = int((df["age_days"] <= SHORT_WINDOW_DAYS).sum()) if total_30d else 0

        if total_30d == 0:
            raise SystemExit(
                f"ERROR: 0 rows in the {WINDOW_DAYS}d window for {kind}. "
                "This likely signals an upstream schema/snapshot change — aborting."
            )

        kept, _ = cap_union(df)
        n_kept = len(kept)
        n_dropped = total_30d - n_kept

        print(f"[{kind}] total rows (30d)      : {total_30d}")
        print(f"[{kind}] rows with age<=7 (7d) : {n_7d}")
        print(f"[{kind}] rows kept after cap   : {n_kept}")
        print(f"[{kind}] rows dropped          : {n_dropped}")

        if kind == "models":
            print(f"[{kind}] top-10 by dl_per_day:")
            for _, r in df.nlargest(10, "dl_per_day").iterrows():
                print(f"    {r['id']:<55} {r['dl_per_day']:,.1f} dl/day")
            print(f"[{kind}] top-5 by likes_per_day:")
            for _, r in df.nlargest(5, "likes_per_day").iterrows():
                print(f"    {r['id']:<55} {r['likes_per_day']:,.2f} likes/day")
        print("-" * 72)

        out[kind] = to_records(kept)

    if not out["models"] or not out["datasets"]:
        raise SystemExit("ERROR: one of the item types is empty after capping — aborting.")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

    size = os.path.getsize(OUTPUT_PATH)
    print(f"Wrote: {OUTPUT_PATH}")
    print(f"Size : {size:,} bytes ({size / 1024:.1f} KiB)")
    print(f"Counts: models={len(out['models'])}, datasets={len(out['datasets'])}")


if __name__ == "__main__":
    main()
