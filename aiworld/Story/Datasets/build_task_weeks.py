#!/usr/bin/env python3
"""Build weekly task aggregates from datasets/hf_boss.csv."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def load_and_prepare(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df.rename(columns={"id": "dataset_id", "task": "id"})
    df = df.drop(columns=[col for col in ["Unnamed: 0"] if col in df.columns])
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
    df = df.dropna(subset=["id", "created_at"])

    df["week_date"] = df["created_at"].dt.to_period("W-WED").dt.end_time.dt.normalize()
    df["week"] = df["week_date"].dt.isocalendar().week.astype(int)
    df["year"] = df["week_date"].dt.isocalendar().year.astype(int)
    df["month"] = df["week_date"].dt.month.astype(int)
    df["month_date"] = df["week_date"].dt.to_period("M").dt.start_time.dt.normalize()

    week_order = {date: idx + 1 for idx, date in enumerate(sorted(df["week_date"].unique()))}
    df["week_count"] = df["week_date"].map(week_order)
    return df


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby(
        ["id", "week_date", "week", "year", "month", "month_date", "week_count"],
        as_index=False,
    ).agg(
        datasets_week=("dataset_id", "size"),
        downloads_week=("downloads", "sum"),
        likes_week=("likes", "sum"),
    )

    grouped["downloads_week"] = grouped["downloads_week"].fillna(0).astype(int)
    grouped["likes_week"] = grouped["likes_week"].fillna(0).astype(int)

    grouped = grouped.sort_values(["id", "week_date"])
    for base, col in [("datasets", "datasets_week"), ("downloads", "downloads_week"), ("likes", "likes_week")]:
        grouped[f"{base}_total"] = grouped.groupby("id")[col].cumsum().astype(int)
    
    grouped["rank_week"] = (
        grouped.groupby("week_date")["datasets_total"]
        .rank(method="dense", ascending=False)
        .astype(int)
    )
    
    grouped["week_date"] = grouped["week_date"].dt.strftime("%Y-%m-%d")
    grouped["month_date"] = grouped["month_date"].dt.strftime("%Y-%m-%d")

    for zero_col in [""]:
        grouped[zero_col] = 0

    cols = [
        "id",
        "week",
        "year",
        "week_count",
        "week_date",
        "month",
        "month_date",
        "datasets_week",
        "datasets_total",
        "likes_week",
        "likes_total",
        "downloads_week",
        "downloads_total",
        "rank_week",
    ]
    return grouped[cols]


def main() -> None:
    csv_path = Path("datasets/hf_boss.csv")
    out_path = Path("task_weeks.json")

    df = load_and_prepare(csv_path)
    result = aggregate(df)
    out_path.write_text(json.dumps(result.to_dict(orient="records"), indent=2))
    print(f"Wrote {len(result)} records to {out_path}")


if __name__ == "__main__":
    main()
