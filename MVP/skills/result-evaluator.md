---
name: result-evaluator
description: Turn any classification or analysis result into a self-contained HTML evaluator with localStorage database and CSV export. Use when the user wants to manually audit, validate, or annotate a dataset — LLM classifications, model outputs, ranked lists, anything with rows that need human judgment.
---

# Result Evaluator

Build a self-contained HTML evaluation tool from any tabular result. No server needed — opens directly from the filesystem. Ratings and notes persist in `localStorage` and export to CSV.

## Step 0 — Understand the data

Read the result file(s) and identify:

```python
import pandas as pd

df = pd.read_csv("<result_file>", low_memory=False)
print("Shape:", df.shape)
print("Columns:", df.columns.tolist())
print("Sample:")
print(df.head(3).to_dict('records'))
```

Determine:
- **What is being evaluated?** (rows = items, one human judgment per row)
- **What are the classification dimensions?** (binary labels, multi-class labels, scores, ranks)
- **What text should be shown per card?** (description, title, content field)
- **What metadata is useful context?** (year, donor, category, source, etc.)
- **Are there special sub-groups that need different judgment options?** (e.g. ambiguous/borderline rows)

## Step 1 — Define evaluation modes

Design one tab per major judgment question. Common patterns:

| Mode | When to use | Default verdicts |
|---|---|---|
| **Binary** | One yes/no label to validate | Agree / Disagree / Unsure |
| **Multi-way** | A categorical label to validate | Agree / Disagree / Unsure + definitions panel |
| **Borderline / special group** | A flagged subset needing finer judgment | Custom verdicts specific to the ambiguity |
| **Ranking / score** | Ordered results to spot-check | Correct / Too high / Too low / Unsure |

For **borderline/special groups**, define verdicts that name the actual decision:
- e.g. for reclassified rows: `original_correct | correct_reclassification | different_needed | unsure`
- e.g. for low-confidence items: `clearly_correct | probably_correct | wrong | unsure`

Ask the user to confirm modes and verdicts before building if unclear.

## Step 2 — Build the JSON dataset

Sample strategically — the tool should be usable in a single session:

```python
import pandas as pd, json, random
random.seed(42)

df = pd.read_csv("<result_file>", low_memory=False)

def make_record(row, text_fields, meta_fields, label_fields):
    """Build a card record from a dataframe row."""
    # Pick longest non-empty text field as primary display text
    text = max([str(row.get(f, '') or '') for f in text_fields], key=len)
    record = {
        'text': text[:900].strip(),
        **{f: str(row.get(f, '') or '') for f in meta_fields},
        **{f: (float(row[f]) if pd.notna(row.get(f)) else None)
           if df[f].dtype in ['float64','int64'] else str(row.get(f,'') or '')
           for f in label_fields},
        '_orig_idx': int(row.name),
    }
    return record

# --- Mode 1: Binary --- ~500 positive + ~300 negative
pos = df[df['<label_col>'] == '<positive_value>'].sample(min(500, ...), random_state=42)
neg = df[df['<label_col>'] == '<negative_value>'].sample(min(300, ...), random_state=42)
binary_data = [make_record(r, ...) for _, r in pd.concat([pos, neg]).sample(frac=1).iterrows()]

# --- Mode 2: Multi-way --- ~150 per category
multiway_data = []
for cat in df['<category_col>'].dropna().unique():
    sub = df[df['<category_col>'] == cat].sample(min(150, len(...)), random_state=42)
    multiway_data += [make_record(r, ...) for _, r in sub.iterrows()]

# --- Mode 3: Special group --- all rows (if manageable) or large sample
special = df[df['<flag_col>'] == True]
special_data = [make_record(r, ...) for _, r in special.iterrows()]

dataset = {'binary': binary_data, 'multiway': multiway_data, 'special': special_data}
print({k: len(v) for k, v in dataset.items()})
```

## Step 3 — Build the HTML evaluator

Generate a single self-contained `.html` file with all data embedded inline. Follow this architecture:

### Required UI elements

**Top bar**
- App title (dataset name)
- Mode tabs (one per evaluation question)
- Random jump button
- Export CSV button

**Stats bar** (updates live)
- Current mode label
- Item position (`N of M`)
- Verdict tally per mode (e.g. `✓ 42  ✗ 8  ? 3`)
- Reviewed count (`53 / 500`)

**Sidebar**
- Filter dropdowns (by category, source, label value, etc.)
- Progress bar + position
- Prev / Next navigation buttons
- Keyboard shortcut reference

**Card (main area)**
- Item metadata (year, source, category, etc.) as small header
- Primary text in a readable box (pre-wrap, scrollable if long)
- Classification badges with confidence scores
- Model reasoning if available (in a highlighted aside box)
- For multi-way mode: **definitions panel on the right** showing all category definitions, with the active one highlighted
- Rating buttons (mode-specific verdicts, full-width grid when 4+ options)
- Notes textarea (auto-saves on blur, `has-note` style when non-empty)

### CSS conventions

```css
/* Category color system */
.badge-cat-A  { background: #dbeafe; color: #1e3a5f; }   /* blue   */
.badge-cat-B  { background: #fef3c7; color: #78350f; }   /* amber  */
.badge-cat-C  { background: #ede9fe; color: #3b0764; }   /* purple */
.badge-positive { background: #d1fae5; color: #065f46; } /* green  */
.badge-negative { background: #fee2e2; color: #7f1d1d; } /* red    */

/* Verdict buttons — use a 4-column grid for 4 options so they fit on one line */
.rating-row { display: flex; gap: 10px; flex-wrap: wrap; }
.rating-row.grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 7px; }
.rating-row.grid-4 .rate-btn { padding: 8px 6px; font-size: 0.8rem; justify-content: center; }

/* Notes */
.notes-wrap textarea { width: 100%; min-height: 64px; padding: 9px 12px;
  border: 1px solid #e0e0e8; border-radius: 8px; font-family: inherit; font-size: 0.85rem; resize: vertical; }
.notes-wrap textarea.has-note { border-color: #6366f1; background: #fafafe; }
```

### JS architecture

```javascript
// State
const RAW = /* embedded JSON */;
let mode = '<first_mode>';
let allItems = {};   // mode → full item array (with _origIdx)
let filtered = [];   // current filtered view
let ratings = {};    // key: "mode:origIdx" → verdict string
let notes = {};      // key: "mode:origIdx" → note string
let currentIdx = 0;

// Persistence
try { ratings = JSON.parse(localStorage.getItem('<app_key>_ratings') || '{}'); } catch(e) {}
try { notes   = JSON.parse(localStorage.getItem('<app_key>_notes')   || '{}'); } catch(e) {}

function ratingKey(item) { return mode + ':' + item._origIdx; }

// Save note before navigating
function saveNote() {
  const ta = document.getElementById('noteArea');
  if (!ta || !filtered.length) return;
  const key = ratingKey(filtered[currentIdx]);
  const val = ta.value.trim();
  if (val) { notes[key] = val; ta.classList.add('has-note'); }
  else     { delete notes[key]; ta.classList.remove('has-note'); }
  localStorage.setItem('<app_key>_notes', JSON.stringify(notes));
}

function rate(verdict) {
  if (!filtered.length) return;
  const key = ratingKey(filtered[currentIdx]);
  ratings[key] = ratings[key] === verdict ? undefined : verdict;  // toggle
  if (ratings[key]) {
    localStorage.setItem('<app_key>_ratings', JSON.stringify(ratings));
    if (currentIdx < filtered.length - 1) { setTimeout(() => { currentIdx++; renderCard(); }, 220); return; }
  }
  renderCard();
}

function navigate(dir) {
  saveNote();
  currentIdx = Math.max(0, Math.min(filtered.length - 1, currentIdx + dir));
  renderCard();
}
```

### Keyboard shortcuts (always include)

| Key | Action |
|---|---|
| `←` / `→` | Navigate |
| `Y` / `N` | Agree / Disagree (binary & multiway modes) |
| `U` | Unsure (all modes) |
| `1`–`4` | Named verdicts in special modes |
| `R` | Random jump |
| `1`–`3` (mode switch) | Only when not in a special mode using number keys |

### CSV export

Always export rows that have **either** a rating **or** a note. Include:
- `mode`, `orig_idx`, relevant metadata columns (year, source, category, etc.)
- `rating` (raw key), `verdict_label` (human-readable), `notes`

```javascript
function exportCSV() {
  const esc = s => '"' + String(s||'').replace(/"/g,'""') + '"';
  let csv = 'mode,orig_idx,...,rating,verdict_label,notes\n';
  Object.keys(allItems).forEach(m => {
    allItems[m].forEach(item => {
      const key = m + ':' + item._origIdx;
      if (ratings[key] || notes[key]) {
        const label = VERDICT_LABELS[ratings[key]] || ratings[key] || '';
        csv += [...fields, esc(ratings[key]||''), esc(label), esc(notes[key]||'')].join(',') + '\n';
      }
    });
  });
  // trigger download
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], {type:'text/csv'}));
  a.download = '<output_name>_reviewed.csv';
  a.click();
}
```

## Step 4 — Output

Save the HTML file **next to the source data file**, named `<source_name>_review.html`.

Open it immediately:
```bash
open <path_to_file>.html
```

Then tell the user:
- Total items per mode
- Keyboard shortcuts summary
- That ratings/notes persist in localStorage keyed to the file path (don't move/rename the file during review)
- To Export CSV when done for a durable save

## Design rules

1. **Self-contained** — all data embedded inline; no fetch(), no server required
2. **localStorage keyed to app name** — survives reloads; warn user not to rename file mid-review
3. **Auto-advance after rating** — 220ms delay then move to next item
4. **Save note on navigate** — call `saveNote()` in navigate() and jumpRandom()
5. **Mode-specific verdicts** — don't force agree/disagree when the question has natural named answers
6. **Definitions panel for multi-way modes** — show category definitions on the right, highlight active one
7. **4+ verdicts → grid layout** — use `grid-template-columns: repeat(N, 1fr)` so buttons stay on one line
8. **Export includes notes-only rows** — a note without a rating is still useful data
9. **No inline event handlers** — use `addEventListener` or named functions only
10. **No native `title` tooltips** — use styled elements for any hover info
