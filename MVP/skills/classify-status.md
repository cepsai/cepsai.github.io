---
name: classify-status
description: Check classification job status — count completed vs remaining items across chunks, surface failed chunks, estimate completion. Built for the Taiwan gov procurement classification pipeline.
---

# Classification Status

Check the current status of a running or completed batch classification job.

## Step 0 — Locate the job

```bash
# Find classification output directories
find ~ -maxdepth 6 -type d \( -name "classified*" -o -name "output*" -o -name "chunks*" -o -name "results*" \) 2>/dev/null | head -20
```

Ask user to confirm the correct directory if ambiguous.

## Step 1 — Count completed vs remaining

```python
import os, glob, pandas as pd

output_dir = "<output_dir>"
input_file = "<input_file>"  # original dataset

# Count total items
total = len(pd.read_csv(input_file)) if input_file.endswith('.csv') else len(pd.read_parquet(input_file))

# Count classified items across all output chunks
output_files = glob.glob(f"{output_dir}/**/*.csv", recursive=True) + \
               glob.glob(f"{output_dir}/**/*.parquet", recursive=True)

completed = 0
for f in output_files:
    try:
        df = pd.read_csv(f) if f.endswith('.csv') else pd.read_parquet(f)
        completed += len(df)
    except Exception as e:
        print(f"Error reading {f}: {e}")

print(f"Total items:     {total:,}")
print(f"Completed:       {completed:,} ({completed/total*100:.1f}%)")
print(f"Remaining:       {total - completed:,}")
print(f"Output files:    {len(output_files)}")
```

## Step 2 — Check for failures

```bash
# Check logs for errors
grep -r "Error\|error\|failed\|FAILED\|exception" logs/ 2>/dev/null | tail -30

# Check if any background processes still running
jobs -l 2>/dev/null || ps aux | grep -i "classify\|python" | grep -v grep
```

## Step 3 — Chunk-level status

If processing was split into chunks, show per-chunk status:

```python
import glob, os

chunk_outputs = sorted(glob.glob(f"{output_dir}/chunk_*.csv"))  # adjust pattern
print(f"\nChunk status ({len(chunk_outputs)} chunks found):")
for f in chunk_outputs:
    size = os.path.getsize(f)
    rows = len(open(f).readlines()) - 1  # rough count
    status = "OK" if rows > 0 else "EMPTY"
    print(f"  {os.path.basename(f)}: {rows:,} rows ({size/1024:.1f} KB) [{status}]")
```

## Step 4 — Summary

Output a clean summary:
```
Classification Status
=====================
Total items:    156,432
Completed:      154,891 (99.0%)
Remaining:        1,541
Failed chunks:       0
Est. completion: [in progress / complete]

Next step: [run remaining items / merge outputs / done]
```

If any chunks failed or are empty, identify them and suggest the recovery command.
