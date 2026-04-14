/**
 * @OnlyCurrentDoc
 *
 * Funding tracker web app — Google Apps Script source.
 *
 * Backs the Sheet that powers the dashboard. One tab, named "funding", with
 * this header row:
 *
 *   source_tracker | source_id | title | funder | category | amount_raw |
 *   deadline | rolling | status | url | description | thematic_fit |
 *   archived | archived_at | actor | note | date_added | last_seen
 *
 * Behavior:
 *   - GET  ?fmt=json
 *       Returns { rows: [ {col: value, ...}, ... ] }.
 *   - POST { action: "insert_rows", rows: [...] }
 *       For each row, append it only if no existing row has the same
 *       (source_tracker, source_id) pair. Existing rows are NEVER touched —
 *       user edits in the Sheet win. Returns { ok, inserted, skipped }.
 *   - POST { action: "archive" | "unarchive", key, actor?, note? }
 *       key = "<source_tracker>::<source_id>". Flips the `archived` cell on
 *       the matching row. Creates a stub row if the row doesn't exist (rare —
 *       only happens if the dashboard has a key the Sheet hasn't seen).
 *
 * Deploy: Extensions → Apps Script, paste, Deploy → Web app,
 *   Execute as: Me, Who has access: Anyone. Copy the /exec URL into
 *   docs/config.json as `scriptUrl`.
 *
 * The dashboard POSTs with `Content-Type: text/plain` to avoid CORS preflight.
 */

const SHEET_NAME = "funding";
const HEADERS = [
  "source_tracker", "source_id", "title", "funder", "category", "amount_raw",
  "deadline", "rolling", "status", "url", "description", "thematic_fit",
  "archived", "archived_at", "actor", "note", "date_added", "last_seen",
];
const KEY_COLS = ["source_tracker", "source_id"];

function _sheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) {
    sh = ss.insertSheet(SHEET_NAME);
    sh.appendRow(HEADERS);
    sh.setFrozenRows(1);
    return sh;
  }
  // Backfill any missing columns at the right edge so the script keeps working
  // if someone adds headers manually.
  const existing = sh.getRange(1, 1, 1, Math.max(sh.getLastColumn(), 1)).getValues()[0];
  const missing = HEADERS.filter(h => !existing.includes(h));
  if (missing.length) {
    sh.getRange(1, existing.length + 1, 1, missing.length).setValues([missing]);
  }
  return sh;
}

function _headerMap(sh) {
  const row = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  const m = {};
  row.forEach((h, i) => { if (h) m[String(h)] = i; });
  return m;
}

function _allRows(sh, hmap) {
  const last = sh.getLastRow();
  if (last < 2) return [];
  const width = sh.getLastColumn();
  const values = sh.getRange(2, 1, last - 1, width).getValues();
  return values.map((r, i) => {
    const obj = { _rowIndex: i + 2 };
    for (const k in hmap) obj[k] = r[hmap[k]];
    return obj;
  });
}

function _keyOf(row) {
  return String(row.source_tracker || "") + "::" + String(row.source_id || "");
}

function _json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function _toIso(v) {
  if (v instanceof Date) return v.toISOString();
  return v == null ? "" : String(v);
}

function doGet(e) {
  const sh = _sheet();
  const hmap = _headerMap(sh);
  const rows = _allRows(sh, hmap).map(r => {
    const o = {};
    for (const h of HEADERS) o[h] = _toIso(r[h]);
    return o;
  });
  return _json({ rows });
}

function doPost(e) {
  let body;
  try { body = JSON.parse(e.postData.contents || "{}"); }
  catch (err) { return _json({ ok: false, error: "invalid JSON" }); }

  const sh = _sheet();
  const hmap = _headerMap(sh);
  const action = body.action;

  if (action === "insert_rows") {
    const existing = new Set(_allRows(sh, hmap).map(_keyOf));
    const incoming = Array.isArray(body.rows) ? body.rows : [];
    let inserted = 0, skipped = 0;
    const toAppend = [];
    for (const row of incoming) {
      const k = _keyOf(row);
      if (!row.source_tracker || !row.source_id || existing.has(k)) { skipped++; continue; }
      const values = HEADERS.map(h => row[h] == null ? "" : row[h]);
      toAppend.push(values);
      existing.add(k);
      inserted++;
    }
    if (toAppend.length) {
      sh.getRange(sh.getLastRow() + 1, 1, toAppend.length, HEADERS.length).setValues(toAppend);
    }
    return _json({ ok: true, inserted, skipped });
  }

  if (action === "archive" || action === "unarchive") {
    const key = body.key;
    if (!key) return _json({ ok: false, error: "missing key" });
    const rows = _allRows(sh, hmap);
    let target = rows.find(r => _keyOf(r) === key);
    const ts = new Date().toISOString();
    const archived = action === "archive";
    if (!target) {
      // Stub row so the state is captured even if the opportunity hasn't been
      // synced yet.
      const [tracker, sid] = String(key).split("::");
      const stub = HEADERS.map(h => {
        if (h === "source_tracker") return tracker || "";
        if (h === "source_id") return sid || "";
        if (h === "archived") return archived;
        if (h === "archived_at") return archived ? ts : "";
        if (h === "actor") return body.actor || "";
        if (h === "note") return body.note || "";
        if (h === "date_added") return ts;
        if (h === "last_seen") return ts;
        return "";
      });
      sh.appendRow(stub);
      return _json({ ok: true, action, key, created_stub: true });
    }
    const row = target._rowIndex;
    sh.getRange(row, hmap.archived + 1).setValue(archived);
    sh.getRange(row, hmap.archived_at + 1).setValue(archived ? ts : "");
    if (body.actor) sh.getRange(row, hmap.actor + 1).setValue(body.actor);
    if (body.note != null) sh.getRange(row, hmap.note + 1).setValue(body.note);
    return _json({ ok: true, action, key });
  }

  return _json({ ok: false, error: "unknown action: " + action });
}
