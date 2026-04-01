---
name: llm-benchmark
description: Benchmark LLM/embedding/OCR models — structured comparison across accuracy, latency (p50/p95), throughput, and cost per 1K items. Supports Ollama, llama.cpp, and API backends.
---

# LLM Benchmark

Benchmark one or more models and produce a structured comparison table. Run models in parallel as background processes.

## Step 0 — Identify models and test set

Ask (or infer from context):
- Which models to benchmark (Ollama tags, llama.cpp model files, or API model IDs)
- Test dataset location and size
- Task type: classification, embedding, OCR, or generation
- Metric of interest: accuracy, latency, cost, or all three

## Step 1 — Detect available backends

```bash
# Check what's available
ollama list 2>/dev/null && echo "ollama: OK" || echo "ollama: not running"
which llama-cli 2>/dev/null || which llama.cpp 2>/dev/null || echo "llama.cpp: not found"
echo "ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:+set}"
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:+set}"
```

## Step 2 — Sample the test set

Before running full benchmark, run each model on 5 samples to verify it works:

```python
import pandas as pd, time, json

df = pd.read_csv("<test_file>")  # or read_parquet
sample = df.sample(5, random_state=42)
print(f"Test set: {len(df):,} items")
print(f"Sample:\n{sample.head()}")
```

## Step 3 — Run benchmarks in parallel (background processes)

For each model, write a benchmark script then launch in background:

```bash
mkdir -p results/benchmark logs/benchmark

# Launch each model as a background job
nohup python scripts/benchmark_<model_name>.py \
  --input <test_file> \
  --output results/benchmark/<model_name>.json \
  > logs/benchmark/<model_name>.log 2>&1 &
echo "<model_name> PID: $!"
```

Each benchmark script should output a JSON file with:
```json
{
  "model": "<name>",
  "n_items": 1000,
  "accuracy": 0.92,
  "latency_p50_ms": 145,
  "latency_p95_ms": 380,
  "throughput_per_min": 412,
  "cost_per_1k_items": 0.043,
  "errors": 3,
  "notes": ""
}
```

Monitor progress:
```bash
tail -f logs/benchmark/*.log
```

## Step 4 — Aggregate results

Once all jobs complete, merge result JSONs into a comparison table:

```python
import json, glob, pandas as pd

results = [json.load(open(f)) for f in glob.glob("results/benchmark/*.json")]
df = pd.DataFrame(results).sort_values("accuracy", ascending=False)

print(df[["model", "accuracy", "latency_p50_ms", "latency_p95_ms",
          "throughput_per_min", "cost_per_1k_items", "errors"]].to_markdown(index=False))
```

Save as `results/benchmark_comparison_<date>.md` and `results/benchmark_comparison_<date>.csv`.

## Step 5 — Recommend

Based on the results, recommend:
- **Best accuracy**: [model]
- **Best cost/performance**: [model] — [X]% accuracy at $[Y]/1K items
- **Fastest**: [model] at p50=[X]ms

Flag any model with >1% error rate as unreliable.
