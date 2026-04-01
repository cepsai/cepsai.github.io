"""
merge_reviews.py — Combine CSV exports from multiple reviewers.

Usage:
    python3 merge_reviews.py *.csv
    python3 merge_reviews.py reviewer_alice.csv reviewer_bob.csv

Output:
    reviews_merged.csv      — all rows stacked, one row per (reviewer, item)
    reviews_agreement.csv   — one row per item, columns per reviewer + majority vote
"""

import sys, glob, pandas as pd
from pathlib import Path

# ── Load files ──────────────────────────────────────────────────────────────
files = sys.argv[1:] if len(sys.argv) > 1 else sorted(glob.glob('*.csv'))
files = [f for f in files if f != 'reviews_merged.csv' and f != 'reviews_agreement.csv']

if not files:
    print("No CSV files found. Pass filenames as arguments or run in the folder with the exports.")
    sys.exit(1)

dfs = []
for f in files:
    df = pd.read_csv(f)
    if 'reviewer' not in df.columns:
        df['reviewer'] = Path(f).stem  # use filename as fallback reviewer name
    dfs.append(df)
    print(f"  {f}: {len(df)} rows, reviewer(s): {df['reviewer'].unique().tolist()}")

merged = pd.concat(dfs, ignore_index=True)
print(f"\nTotal rows merged: {len(merged):,}")
print(f"Reviewers: {sorted(merged['reviewer'].dropna().unique().tolist())}")
print(f"Modes: {merged['mode'].value_counts().to_dict()}")

# ── Save merged ──────────────────────────────────────────────────────────────
merged.to_csv('reviews_merged.csv', index=False)
print("\nSaved: reviews_merged.csv")

# ── Agreement table — one row per item, side-by-side verdicts ────────────────
key_cols = ['mode', 'orig_idx']
reviewers = sorted(merged['reviewer'].dropna().unique())

pivot = merged.pivot_table(
    index=key_cols,
    columns='reviewer',
    values='verdict_label',
    aggfunc='first'
).reset_index()

# Add metadata from first reviewer's entry for each item
meta_cols = ['year', 'donor', 'recipient', 'is_digital', 'tech_category']
meta = merged.groupby(key_cols)[meta_cols].first().reset_index()
pivot = pivot.merge(meta, on=key_cols, how='left')

# Majority vote (most common verdict, ties → 'tie')
def majority(row):
    votes = [row.get(r) for r in reviewers if pd.notna(row.get(r))]
    if not votes:
        return ''
    counts = pd.Series(votes).value_counts()
    if len(counts) == 1 or counts.iloc[0] > counts.iloc[1]:
        return counts.index[0]
    return 'tie'

pivot['majority_vote'] = pivot.apply(majority, axis=1)

# Agreement flag
pivot['full_agreement'] = pivot.apply(
    lambda r: len({r.get(rv) for rv in reviewers if pd.notna(r.get(rv))}) == 1, axis=1
)

# Reorder columns
first_cols = key_cols + meta_cols + reviewers + ['majority_vote', 'full_agreement']
pivot = pivot[[c for c in first_cols if c in pivot.columns]]

pivot.to_csv('reviews_agreement.csv', index=False)
print("Saved: reviews_agreement.csv")

# ── Summary ──────────────────────────────────────────────────────────────────
print("\n── Agreement summary ──")
total = len(pivot)
agreed = pivot['full_agreement'].sum()
print(f"Items reviewed by 2+ people: {total}")
print(f"Full agreement: {agreed} ({agreed/total*100:.1f}%)" if total else "No overlapping reviews.")

print("\n── Verdict distribution (merged) ──")
print(merged['verdict_label'].value_counts().to_string())
