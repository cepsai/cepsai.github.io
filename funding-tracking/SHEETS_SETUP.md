# Google Sheets backend — setup (~5 minutes)

The Sheet is the source of truth for both **current and archived** funding
opportunities. The aggregator only ever *appends* new rows (keyed on
`source_tracker` + `source_id`), so your hand edits in the Sheet stick.

## 1. Create the Sheet

1. Open <https://sheets.new>. Name it e.g. **funding-tracker**.
2. Rename the first tab to **`funding`**.
3. Paste this header row into row 1 (the Apps Script will also self-heal any
   missing headers on first run):

   ```
   source_tracker  source_id  title  funder  category  amount_raw  deadline  rolling  status  url  description  thematic_fit  archived  archived_at  actor  note  date_added  last_seen
   ```

## 2. Add the Apps Script

1. In the Sheet: **Extensions → Apps Script**.
2. Replace the default `Code.gs` with [`scripts/archive_sync.gs`](scripts/archive_sync.gs).
3. Save, then **Deploy → New deployment → Web app**:
   - Execute as: **Me**
   - Who has access: **Anyone** *(or "Anyone with the link")*
4. Copy the `/exec` URL.

## 3. Publish the funding tab as CSV

1. **File → Share → Publish to web**.
2. Choose the **`funding`** tab and format **CSV**, click **Publish**.
3. Copy the `…/pub?...&output=csv` URL.

## 4. Wire the dashboard

Edit [`docs/config.json`](docs/config.json):

```json
{
  "fundingCsvUrl": "https://docs.google.com/spreadsheets/.../pub?...&output=csv",
  "scriptUrl":     "https://script.google.com/macros/s/XXXXXXXX/exec",
  "actor":         "robert"
}
```

Commit + push. The dashboard now:

- Reads opportunity rows from the published CSV on every page load, cached in
  localStorage so it renders instantly next time.
- Falls back to the static `docs/data.json` if the CSV fetch fails.
- Archive/Unarchive clicks POST to the script (optimistic UI; failed writes
  are retried on next load).

## 5. Wire the aggregator

In the scheduled task's environment, set:

```
FUNDING_SCRIPT_URL=<same /exec URL as step 2>
FUNDING_CSV_URL=<same CSV URL as step 3>
```

On each daily run the aggregator:

- POSTs the full opportunity list with `action: insert_rows`. The script only
  appends rows whose `(source_tracker, source_id)` is new — existing rows
  (and any hand edits) are untouched.
- Pulls the CSV and mirrors the archived keys back into
  `central/archived.json` so the static fallback stays in sync.

## Rules of thumb

- **Never rename** `source_tracker` or `source_id` columns — they're the key.
- **User edits win** on every other column. If a tracker updates a deadline,
  you won't see it unless you delete that row from the Sheet so the aggregator
  can re-insert it on the next run.
- The Apps Script uses `Content-Type: text/plain` POSTs so the browser skips
  the CORS preflight Apps Script can't answer.
