# HTML dashboards — what each page shows

Five HTMLs in this folder, all driven by the same embedded `DATA` JSON (one country → one nested object). The v3.1 ensemble 4-way labels (`digital_governance_and_rights`, `digital_human_development`, `hard_infrastructure`, `non_digital`) are collapsed into the three existing UI slots: **gov** (governance + rights), **inc** (human development, keeping the old variable name), **inf** (hard infrastructure). Every page carries a yellow banner at the top linking back to the v1 (3-way Nemotron) dashboard.

Colour key used throughout: **blue = gov**, **green = inc/human development**, **orange = inf/hard infra**.

---

## Shared data schema (per country)

The HTMLs all read one entry per country with these keys:

| key | meaning |
|---|---|
| `region` | Europe / Africa / Asia / Central Asia / Pacific |
| `type` | "Most Interested" or "Diplomatic" (Taiwan-ICDF relationship label, carried over from v1) |
| `total` | dedup digital row count (after 8-col exact dedup) |
| `gov / inc / inf` | counts per category |
| `n_distinct` | same as `total` (legacy duplicate field) |
| `total_commit / total_disb` | USD millions, summed over digital dedup rows |
| `year_min / year_max` | earliest / latest digital entry for the country |
| `donors[]` | top 8 donors by digital row count: `{name, gov, inc, inf, total}` |
| `sectors[]` | top 8 CRS sectors by digital row count: `{name, n}` |
| `trend[]` | year → `{year, gov, inc, inf}` counts |
| `themes{}` | 16-keyword substring match on tech_reason + descriptions → hit counts |
| `projects[]` | dedup groups keyed on (title × category). Each entry has title / cat / donor / n_donors / desc / long / sector / reason / conf_bin / conf_tech / total_commit / total_disb / n_entries / year_range / members[] |
| `projects[].members[]` | raw CRS rows inside the group: `{year, donor, sector, uc, ud, cb, ct}` |

All counts are on the 12,440 deduplicated digital rows across the 12 priority-target recipients.

---

## 1. `tech_overview.html` — integrated overview dashboard

**Layout:** left sidebar (country list) + right main panel with two inner tabs ("General" / "Projects").

### Sidebar
- Countries listed grouped by region, with a region-colour chip.
- Each row shows `total` digital count and gov/inc/inf mini-bar.
- Click a country → main panel re-renders for that country.
- Deep-linked via URL hash `#CountryName/tab/yearRange`.

### Main panel — General tab
- **Header KPI strip**: total projects · pledged USD · disbursed USD · year range · region · type.
- **Category breakdown bar**: horizontal stacked bar showing gov / inc / inf split of the country's digital rows.
- **Trend chart** (`buildTrendChart`): stacked area or stacked bar by year, three series (gov/inc/inf). Hover shows year-level counts.
- **Donors panel**: top 8 donors, each row showing gov/inc/inf split as a mini stacked bar + row total.
- **Sectors panel**: top 8 OECD CRS sector names + project counts.
- **Themes panel**: 16-keyword matches sorted by frequency (e-government, digital skills, capacity building, media & journalism, connectivity, …).

### Main panel — Projects tab
- Scrollable list of **project cards**, one per dedup group (title × category).
- Each card:
  - Left: pledged USD (big) + disbursed USD (smaller) + "N entries" pill (if the group spans >1 CRS row).
  - Right: category badge (GOV/INC/INF) + top donor ("+N more" if group has more) + year range.
  - Fields: Title / Subtitle / Description / **Sector (bold)** / "Why Digital Governance & Rights" (= the model's `tech_reason`).
  - Two confidence pills: "Confidence as tech: X%" (binary is_digital) and "Confidence in <category>: X%" (4-way primary weight).
- Hovering a card's "N entries" pill pops a tooltip with the year-by-year member breakdown (what values went into the group).

**Good for:** answering "what is the digital ODA story for country X?" in one page.

---

## 2. `all_country_profiles_v2.html` — full-size single-country deep dive

Same sidebar + URL-hash navigation as `tech_overview.html`, but the main panel is taller and the project cards are bigger. Adds:

- **Year range slider** in the toolbar — filters all charts, aggregates, and project cards live. Implementation: `computeAggregates` re-reduces `trend[]` and `projects[].members[]` to the selected range on every slider change.
- **Tabs**: "General" (charts) and "Projects" (cards). On the Projects tab, cards show only members with `year` inside the selected range; the pledged/disbursed totals and "N entries" pill update accordingly.
- **Export CSV** button on the Projects tab — dumps the currently-filtered project cards as CSV via `exportProjectsCSV`.
- Everything else matches `tech_overview.html` but rendered at larger sizes (KPI cards take a full row instead of a strip).

**Good for:** drilling into one country's full project list with year filtering.

---

## 3. `all_country_profiles_v2a.html` — v2 with compact KPI row

Identical to `v2.html` except the six KPI cards at the top (total / pledged / disbursed / year range / region / type) are compressed into a single horizontal row instead of a 3×2 grid. Everything else — tabs, filters, charts, cards — is the same. Useful when you want the charts + cards closer to the top of the viewport.

---

## 4. `all_country_profiles_v3.html` — single-scroll, no tabs

Merges the General and Projects views into one continuous scroll, with charts at the top and project cards below. Charts are compacted (smaller, side-by-side). No inner tabs — just scroll. Same year range slider and sidebar as v2/v2a.

**Good for:** presentations where you want everything for a country visible without clicking.

---

## 5. `country_comparison_v2.html` — cross-country dashboard

This one is fundamentally different — no sidebar, no per-country drill-down. All 12 countries are visible simultaneously across every section.

### Global toolbar (top)
- **Tech filter**: `All / Gov / Inc / Inf` — restricts all counts, bars, rankings, and projects to the chosen category (or all three combined).
- **Metric toggle**: `Pledged / Disbursed / Entries / Distinct`
  - Pledged = sum of `usd_commitment` over filtered members
  - Disbursed = sum of `usd_disbursement`
  - Entries = raw CRS row count (before dedup)
  - Distinct = dedup row count (`n_distinct`)
- **Region filter**: `All / EU / AF / AS / CA / PA` — chops the country list to one region. EU pulls from the `Europe` region key; AF/AS/CA/PA map to Africa / Asia / Central Asia / Pacific.
- **Year range slider**: 1990 → 2024, filters all sections live.

### Sections (top to bottom)

1. **Country rankings** — three side-by-side columns: Governance / Inclusion / Infrastructure. Each is a horizontal bar list of all countries ranked by the selected metric within that category. Bars are tinted with the region colour; hovering shows a tooltip with the exact number.

2. **Trends over time** — single multi-line SVG chart: one line per country, y-axis = selected metric, x-axis = year. The legend below is clickable to toggle countries on/off. A small "Trends sub" selector lets you switch between totals and per-category trends.

3. **Top 5 donors per country — USD millions pledged in selected period** — grid (`donor-grid`): one card per country, listing its top 5 donors with a mini horizontal stacked bar (gov/inc/inf) and total pledged $ inside the selected years. Useful for quickly seeing "who funds what in Uganda vs. Viet Nam".

4. **Tech category share — within each country's digital ODA** — horizontal 100%-stacked bars, one per country, showing the gov/inc/inf composition as a percentage. Two callouts underneath the chart:
   - **Most governance-heavy**: the country with the highest gov share
   - **Most inclusion-heavy**: the country with the highest inc share
   
   (These update as the year slider moves.)

5. **Summary table** — sortable columns: country / region / type / total / gov / inc / inf / pledged / disbursed / year range / top donor. "↓ Export CSV" button dumps the table as-is.

6. **Largest projects (top 60)** — ranked card grid of the single largest projects across all 12 countries, filtered by the selected tech / year / region. Each card has: rank, country badge, category pill, pledged $, donor, title, year range. Clicking a card scrolls to the owning country in the rankings.

**Good for:** answering "how do the 12 countries compare on digital ODA?" — rankings, composition, and cross-cutting largest-projects view.

---

## Interaction behaviours common to all pages

- **Tooltips**: `showTip` / `hideTip` drive a floating div; hovering any bar / pill / table row shows contextual numbers.
- **URL hash deep linking**: in the sidebar-driven pages (`tech_overview`, `all_country_profiles_*`) the URL updates to `#CountryName/tab/yearMin-yearMax`. Sharing a link lands the recipient on the same view.
- **Projects tab entries tooltip**: hovering "N entries" on a project card pops `positionEntriesTooltip` with the year-by-year member breakdown (year, donor, sector, pledged, disbursed, binary confidence, tech confidence).

---

## What the stats actually mean (glossary)

| label in UI | value in data | interpretation |
|---|---|---|
| "total" / "digital projects" | `n_distinct` | distinct digital rows after 8-column exact dedup |
| "pledged" | `total_commit` | sum of `usd_commitment` (USD millions) across digital rows |
| "disbursed" | `total_disb` | sum of `usd_disbursement` (USD millions) |
| "N entries" pill | `n_entries` | raw CRS rows that collapsed into a single project-card group (title × category) |
| "+N more" (donors) | `n_donors` − 1 | distinct donors in the project group beyond the top one |
| "Confidence as tech: X%" | `conf_bin` / `cb` | binary is_digital probability from the ensemble binary classifier (higher = more sure it's digital) |
| "Confidence in <Category>: X%" | `conf_tech` / `ct` | primary-label weight from the 3-model soft ensemble (= `primary_weight` in the source CSV) |
| "e-government" etc. theme count | `themes[name]` | naive substring match: rows whose `tech_reason` + `short_description` + `description` contain any of a fixed keyword list |

Neither confidence field is calibrated — treat them as ordinal signals, not probabilities. The theme counter is a substring match, not a topic model — "mobile" matches "automobile"; use it for directional reading, not precise counts.

---

## Known limitations

- **12 countries only.** v3.1 ensemble ran on the "priority target" subset; the v1 dashboards in `../` have all 32.
- **3-way UI, 4-way data.** The v3.1 label `digital_human_development` merged v1's `digital_inclusion` + `other_digital`; it now renders in the "inc" / green slot. A proper 4-way UI (stacked soft-weight bars) is a follow-up.
- **Dedup is exact-row.** Two near-duplicate CRS rows differing only in whitespace or a trailing char will produce two separate cards.
- **`type` metadata** (Most Interested / Diplomatic) is inherited from the v1 dataset and never re-derived.
