import pandas as pd
import numpy as np
import os
import json

base_path = '/Users/robertpraas/CEPS-DST Dropbox/Robert Praas/Code/DST/IL_VIZ/FW'

# ---------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------
df = pd.read_csv(os.path.join(base_path, 'occ_exposure_db.csv'), na_values=['NA'])

# ---------------------------------------------------------------------------
# 2. Define column groupings (matching the image layout)
# ---------------------------------------------------------------------------
ai_g1  = ['2017_Frey_autom', '2018_Brynjolfsson_mSML', '2020_Webb_AI']
ai_g2  = ['2021_Tolan_AI', '2021_Felten_AIOE', '2024_Engberg_DAIOE']
ai_g3  = ['2024_Loaiza_augm', '2024_Loaiza_autom']
genai  = ['2023_Felten_genAIOE', '2023_Gmyrek_LLM', '2024_Eloundou_GPT']
wt_g1  = ['2020_Webb_robot', '2020_Webb_software']
wt_g2  = ['2024_Autor_augm', '2024_Autor_autom', '2024_Prytkova_digital']

all_cols = ai_g1 + ai_g2 + ai_g3 + genai + wt_g1 + wt_g2

# Human-readable x-axis labels (year / author / measure, multiline)
col_labels = {
    '2017_Frey_autom':          ['2017', 'Frey', 'autom'],
    '2018_Brynjolfsson_mSML':   ['2018', 'Brynjolfsson', 'mSML'],
    '2020_Webb_AI':             ['2020', 'Webb', 'AI'],
    '2021_Tolan_AI':            ['2021', 'Tolan', 'AI'],
    '2021_Felten_AIOE':         ['2021/3', 'Felten', 'AIOE'],
    '2024_Engberg_DAIOE':       ['2024', 'Engberg', 'DAIOE'],
    '2024_Loaiza_augm':         ['2024', 'Loaiza', 'augm'],
    '2024_Loaiza_autom':        ['2024', 'Loaiza', 'autom'],
    '2023_Felten_genAIOE':      ['2021/3', 'Felten', 'genAIOE'],
    '2023_Gmyrek_LLM':          ['2023', 'Gmyrek', 'LLM'],
    '2024_Eloundou_GPT':        ['2024', 'Eloundou', 'GPT'],
    '2020_Webb_robot':          ['2020', 'Webb', 'robot'],
    '2020_Webb_software':       ['2020', 'Webb', 'software'],
    '2024_Autor_augm':          ['2024', 'Autor', 'augm'],
    '2024_Autor_autom':         ['2024', 'Autor', 'autom'],
    '2024_Prytkova_digital':    ['2024', 'Prytkova', 'digital'],
}

# ---------------------------------------------------------------------------
# 3. Aggregate to ISCO 1-digit level (exclude armed forces, ISCO1D = 0)
# ---------------------------------------------------------------------------
df_f = df[df['ISCO1D'].isin(range(1, 10))].copy()
df_g = (df_f
        .groupby(['ISCO1D', 'ISCO1Dname'])[all_cols]
        .mean()
        .reset_index()
        .sort_values('ISCO1D'))

# ---------------------------------------------------------------------------
# 4. Compute percentile ranks (per column, across ISCO1D rows)
# ---------------------------------------------------------------------------
pct_cols = []
for col in all_cols:
    pct_col = f'{col}_pct'
    df_g[pct_col] = df_g[col].rank(pct=True)
    pct_cols.append(pct_col)

# ---------------------------------------------------------------------------
# 5. Save CSV (means + percentile ranks)
# ---------------------------------------------------------------------------
csv_out = df_g[['ISCO1D', 'ISCO1Dname'] + all_cols + pct_cols]
csv_out.to_csv(os.path.join(base_path, 'occ_exposure_pct_rank.csv'), index=False)
print("Saved: occ_exposure_pct_rank.csv")
print(df_g[['ISCO1Dname'] + pct_cols].to_string(index=False))

# ---------------------------------------------------------------------------
# 6. Build HTML heatmap
# ---------------------------------------------------------------------------

# Convert percentile-rank matrix to list of dicts for JSON embedding
rows = []
for _, row in df_g.iterrows():
    rows.append({
        'label': f"{int(row['ISCO1D'])} {row['ISCO1Dname']}",
        'values': {col: (None if pd.isna(row[f'{col}_pct']) else round(float(row[f'{col}_pct']), 4))
                   for col in all_cols}
    })

# Section structure for the HTML layout
sections = [
    {
        'title': 'AI',
        'groups': [ai_g1, ai_g2, ai_g3]
    },
    {
        'title': 'GenAI',
        'groups': [genai]
    },
    {
        'title': 'wider-tech',
        'groups': [wt_g1, wt_g2]
    },
]

rows_json    = json.dumps(rows)
labels_json  = json.dumps(col_labels)
sections_json = json.dumps(sections)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Occupational AI Exposure Heatmap</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    background: #fff;
    padding: 30px 20px 40px 20px;
    color: #222;
  }}
  h2 {{
    text-align: center;
    font-size: 14px;
    font-weight: normal;
    margin-bottom: 20px;
    color: #333;
  }}

  /* Legend */
  #legend {{
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 30px;
  }}
  #legend-title {{
    font-size: 12px;
    margin-bottom: 6px;
    text-align: center;
    line-height: 1.4;
  }}
  #legend-bar-row {{
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  #legend-bar {{
    width: 200px;
    height: 14px;
    background: linear-gradient(to right, #FFFFFF, #9B89C4, #2D1B8E);
    border: 1px solid #ccc;
  }}
  .legend-tick {{
    font-size: 10px;
    color: #444;
  }}

  /* Main grid wrapper */
  #heatmap-wrapper {{
    display: flex;
    align-items: flex-start;
    gap: 0;
  }}

  /* Y-axis labels */
  #y-axis {{
    display: flex;
    flex-direction: column;
    justify-content: space-around;
    flex-shrink: 0;
    padding-top: 28px;   /* align with section title row */
    padding-bottom: 60px; /* space for x-axis labels */
  }}
  .y-label {{
    font-size: 11px;
    text-align: right;
    padding-right: 10px;
    line-height: 1.25;
    color: #333;
  }}

  /* Sections wrapper */
  #sections {{
    display: flex;
    gap: 16px;
    align-items: flex-start;
  }}

  .section {{
    display: flex;
    flex-direction: column;
    align-items: center;
  }}
  .section-title {{
    font-size: 13px;
    text-align: center;
    margin-bottom: 6px;
    color: #111;
  }}
  .section-grid {{
    display: flex;
    gap: 0;
    align-items: flex-end;
  }}
  /* sub-group: columns separated by black vertical bar */
  .group-block {{
    display: flex;
    gap: 0;
    position: relative;
  }}
  .group-separator {{
    width: 2px;
    background: #000;
    align-self: stretch;
    margin: 0 1px;
  }}

  .col-block {{
    display: flex;
    flex-direction: column;
    align-items: center;
  }}

  .cell {{
    width: 36px;
    height: 36px;
    border: 0.5px solid rgba(255,255,255,0.3);
  }}

  .x-label {{
    font-size: 9.5px;
    text-align: center;
    color: #333;
    line-height: 1.3;
    margin-top: 5px;
    width: 36px;
  }}
</style>
</head>
<body>

<div id="legend">
  <div id="legend-title">Exposure<br>(percentile rank)</div>
  <div id="legend-bar-row">
    <div id="legend-bar"></div>
  </div>
  <div id="legend-bar-row" style="width:212px; display:flex; justify-content:space-between; margin-top:3px;">
    <span class="legend-tick">0</span>
    <span class="legend-tick">0.25</span>
    <span class="legend-tick">0.50</span>
    <span class="legend-tick">0.75</span>
    <span class="legend-tick">1</span>
  </div>
</div>

<div id="heatmap-wrapper">
  <div id="y-axis"></div>
  <div id="sections"></div>
</div>

<script>
const rows     = {rows_json};
const labels   = {labels_json};
const sections = {sections_json};

// Color interpolation: white -> medium purple -> dark indigo
function valToColor(v) {{
  if (v === null || v === undefined) return '#e0e0e0'; // grey for missing
  // stops: 0→#FFFFFF, 0.5→#9B89C4, 1→#2D1B8E
  let r, g, b;
  if (v <= 0.5) {{
    const t = v / 0.5;
    r = Math.round(255 + (155 - 255) * t);
    g = Math.round(255 + (137 - 255) * t);
    b = Math.round(255 + (196 - 255) * t);
  }} else {{
    const t = (v - 0.5) / 0.5;
    r = Math.round(155 + (45 - 155) * t);
    g = Math.round(137 + (27 - 137) * t);
    b = Math.round(196 + (142 - 196) * t);
  }}
  return `rgb(${{r}},${{g}},${{b}})`;
}}

// Build Y-axis
const yAxis = document.getElementById('y-axis');
const cellH = 36; // px per row
rows.forEach(row => {{
  const div = document.createElement('div');
  div.className = 'y-label';
  div.style.height = cellH + 'px';
  div.style.display = 'flex';
  div.style.alignItems = 'center';
  div.style.justifyContent = 'flex-end';
  // Format: "1 Managers" → "1 Managers" with number bold
  const parts = row.label.match(/^(\\d+)\\s+(.+)$/);
  if (parts) {{
    div.innerHTML = `${{parts[1]}} ${{parts[2]}}`;
  }} else {{
    div.textContent = row.label;
  }}
  yAxis.appendChild(div);
}});

// Build sections
const sectionsEl = document.getElementById('sections');

sections.forEach(sec => {{
  const secDiv = document.createElement('div');
  secDiv.className = 'section';

  const titleDiv = document.createElement('div');
  titleDiv.className = 'section-title';
  titleDiv.textContent = sec.title;
  secDiv.appendChild(titleDiv);

  const gridDiv = document.createElement('div');
  gridDiv.className = 'section-grid';
  gridDiv.style.alignItems = 'flex-start';

  sec.groups.forEach((group, gi) => {{
    // Separator before groups after the first
    if (gi > 0) {{
      const sep = document.createElement('div');
      sep.className = 'group-separator';
      sep.style.height = (rows.length * cellH) + 'px';
      gridDiv.appendChild(sep);
    }}

    const groupDiv = document.createElement('div');
    groupDiv.className = 'group-block';

    group.forEach(colKey => {{
      const colDiv = document.createElement('div');
      colDiv.className = 'col-block';

      // Cells
      rows.forEach(row => {{
        const cell = document.createElement('div');
        cell.className = 'cell';
        const v = row.values[colKey];
        cell.style.backgroundColor = valToColor(v);
        if (v !== null && v !== undefined) {{
          cell.title = `${{row.label}}: ${{v.toFixed(3)}}`;
        }} else {{
          cell.title = `${{row.label}}: N/A`;
        }}
        colDiv.appendChild(cell);
      }});

      // X-axis label
      const xl = document.createElement('div');
      xl.className = 'x-label';
      const parts = labels[colKey] || [colKey];
      xl.innerHTML = parts.join('<br>');
      colDiv.appendChild(xl);

      groupDiv.appendChild(colDiv);
    }});

    gridDiv.appendChild(groupDiv);
  }});

  secDiv.appendChild(gridDiv);
  sectionsEl.appendChild(secDiv);
}});
</script>
</body>
</html>
"""

html_path = os.path.join(base_path, 'occ_exposure_heatmap.html')
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Saved: occ_exposure_heatmap.html")
