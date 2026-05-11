import pandas as pd

df = pd.read_csv("/Users/robertpraas/Documents/GitHub/cepsai.github.io/aiworld/gtc/260228/temp_data_2026-02-28.csv", low_memory=False)
nv = df[df["org_name"] == "NVIDIA"].copy()
nv["created_at"] = pd.to_datetime(nv["created_at"], utc=True)
nv = nv.sort_values("created_at", ascending=False)

cols = ["id", "type", "created_at", "likes", "downloads", "pipeline_tag"]
print(nv[cols].head(20).to_string(index=False))
