"""
Fetch Hugging Face hub-stats for datasets, classify each dataset by a primary
task category, aggregate by month, and write `datasets_monthly.csv`.

Source: https://huggingface.co/datasets/cfahlgren1/hub-stats (datasets.parquet)

Output columns: month, nlp, cv, audio, multimodal, rl, tabular, other, all_total
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
PARQUET_URL = "https://huggingface.co/datasets/cfahlgren1/hub-stats/resolve/main/datasets.parquet"
PARQUET_PATH = HERE / ".hub-stats-datasets.parquet"
OUTPUT_CSV = HERE / "datasets_monthly.csv"

# Primary-category resolution. The order here matters: the first matching
# bucket wins (so e.g. a dataset tagged both "image-classification" and
# "visual-question-answering" is counted as Multimodal, not CV).
# Mirrors Hugging Face's published task taxonomy (Tasks sidebar on the dataset
# search UI). Order is irrelevant since each task belongs to exactly one bucket;
# we only iterate in this order for the explicit-tag pass.
CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("multimodal", [
        "image-text-to-text",
        "image-text-to-image",
        "image-text-to-video",
        "visual-question-answering",
        "video-text-to-text",
        "visual-document-retrieval",
        "any-to-any",
    ]),
    ("cv", [
        "depth-estimation",
        "image-classification",
        "object-detection",
        "image-segmentation",
        "text-to-image",
        "image-to-text",
        "image-to-image",
        "image-to-video",
        "unconditional-image-generation",
        "video-classification",
        "text-to-video",
        "zero-shot-image-classification",
        "mask-generation",
        "zero-shot-object-detection",
        "text-to-3d",
        "image-to-3d",
        "image-feature-extraction",
        "keypoint-detection",
    ]),
    ("nlp", [
        "text-classification",
        "token-classification",
        "table-question-answering",
        "question-answering",
        "zero-shot-classification",
        "translation",
        "summarization",
        "feature-extraction",
        "text-generation",
        "text2text-generation",
        "fill-mask",
        "sentence-similarity",
        "table-to-text",
        "multiple-choice",
        "text-ranking",
        "text-retrieval",
        "conversational",
    ]),
    ("audio", [
        "text-to-speech",
        "text-to-audio",
        "automatic-speech-recognition",
        "audio-to-audio",
        "audio-classification",
        "voice-activity-detection",
    ]),
    ("tabular", [
        "tabular-classification",
        "tabular-regression",
        "tabular-to-text",
        "time-series-forecasting",
    ]),
    ("rl", [
        "reinforcement-learning",
        "robotics",
    ]),
    # "Other" bucket on HF: graph-ml. Everything else falls through to other.
]


def download_parquet(force: bool = False) -> None:
    if PARQUET_PATH.exists() and not force:
        size = PARQUET_PATH.stat().st_size
        # A truncated/corrupted file won't end with the parquet `PAR1` magic.
        with PARQUET_PATH.open("rb") as f:
            f.seek(-4, os.SEEK_END)
            tail = f.read(4)
        if size > 1_000_000 and tail == b"PAR1":
            return
        print(f"[get_datasets] cached parquet looks corrupted (size={size}, "
              f"tail={tail!r}); re-downloading", file=sys.stderr)

    print(f"[get_datasets] downloading {PARQUET_URL} → {PARQUET_PATH}", file=sys.stderr)
    tmp = PARQUET_PATH.with_suffix(PARQUET_PATH.suffix + ".tmp")
    with requests.get(PARQUET_URL, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with tmp.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                if chunk:
                    f.write(chunk)
    tmp.replace(PARQUET_PATH)


def classify(tags: list[str] | None) -> str:
    if not tags:
        return "other"
    tagset = {t.lower() for t in tags if isinstance(t, str)}

    # 1) Explicit task_categories on the dataset card.
    for bucket, candidates in CATEGORY_RULES:
        for c in candidates:
            if c in tagset or f"task_categories:{c}" in tagset:
                return bucket

    # 2) Free-form thematic tags (people don't always file task_categories).
    if "reinforcement-learning" in tagset or "robotics" in tagset:
        return "rl"

    # 3) Modality fallback — covers the ~86% of datasets that publish only
    #    modality: tags. Multimodal is only inferred from explicit
    #    task_categories above; here, modality combos collapse to a single
    #    dominant bucket (tabular > image/video > audio > text).
    modalities = {t.split(":", 1)[1] for t in tagset if t.startswith("modality:")}
    if "tabular" in modalities or "timeseries" in modalities or "time-series" in modalities:
        return "tabular"
    if "image" in modalities or "video" in modalities:
        return "cv"
    if "audio" in modalities:
        return "audio"
    if "text" in modalities:
        return "nlp"

    return "other"


def main() -> None:
    download_parquet()

    print(f"[get_datasets] reading {PARQUET_PATH}", file=sys.stderr)
    df = pd.read_parquet(PARQUET_PATH)

    if "createdAt" not in df.columns:
        raise SystemExit(f"unexpected schema, columns: {list(df.columns)[:30]}")

    created = pd.to_datetime(df["createdAt"], utc=True, errors="coerce")
    df = df.assign(_created=created).dropna(subset=["_created"])

    # `tags` is typically a list of strings. Some hub-stats snapshots stash
    # task categories there; in others there's a dedicated `task_categories`
    # column. Be tolerant of both.
    def row_tags(r):
        out: list[str] = []
        for col in ("tags", "task_categories", "task_ids"):
            if col not in r:
                continue
            v = r[col]
            if v is None:
                continue
            if isinstance(v, str):
                out.append(v)
            else:
                try:
                    out.extend(str(x) for x in v)
                except TypeError:
                    pass
        return out

    df["_category"] = df.apply(row_tags, axis=1).map(classify)

    df["_month"] = df["_created"].dt.to_period("M").dt.to_timestamp()

    pivot = (
        df.groupby(["_month", "_category"], dropna=False)
        .size()
        .unstack(fill_value=0)
        .sort_index()
    )

    for col in ("nlp", "cv", "audio", "multimodal", "rl", "tabular", "other"):
        if col not in pivot.columns:
            pivot[col] = 0

    pivot = pivot[["nlp", "cv", "audio", "multimodal", "rl", "tabular", "other"]]
    pivot["all_total"] = pivot.sum(axis=1)

    out = pivot.reset_index().rename(columns={"_month": "month"})
    out["month"] = out["month"].dt.strftime("%Y-%m-%d")

    out.to_csv(OUTPUT_CSV, index=False)
    print(f"[get_datasets] wrote {OUTPUT_CSV} ({len(out)} rows, "
          f"{out['all_total'].sum():,} datasets total)", file=sys.stderr)


if __name__ == "__main__":
    main()
