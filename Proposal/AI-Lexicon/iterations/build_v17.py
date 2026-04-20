"""build_v17.py — Digital AI Lexicon v17

Use the DAL v18.5 reference file (reference_style_v16.html) as the SHELL
for layout, colouring, typography. Replace its embedded CONCEPTS data
with v16's fixed data (per-sub-concept notes, no orphan rows, TX fix).

Strategy:
    1. Run build_v16.main() to get a clean digital_lexicon_v16.html.
    2. Extract v16's CONCEPTS (list of 6 concept families with sub_concepts
       that carry ceps_notes_rich = [{title, body_runs, dim_label}, ...]).
    3. Transform each sub_concept so its ceps_notes matches the reference
       shape: {summary: "...", themes: [{title, body}, ...]}.
    4. Load reference_style_v16.html, replace its `const CONCEPTS = ...`
       literal with the transformed data.
    5. Write digital_lexicon_v17.html.

Entry point:
    python3 build_v17.py
Writes:
    digital_lexicon_v17.html
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
HTML_V16 = HERE / "digital_lexicon_v16.html"
HTML_V17 = HERE / "digital_lexicon_v17.html"
REF_HTML = HERE / "reference_style_v16.html"


def _find_json_literal(src: str, var_name: str) -> tuple[int, int] | None:
    """Return (start, end) for `const <var_name> = <literal>;`. Bracket-
    aware — handles strings with embedded brackets/quotes."""
    key = f"const {var_name}"
    start = src.find(key)
    if start < 0:
        return None
    i = src.index("=", start) + 1
    while i < len(src) and src[i] not in "[{":
        i += 1
    if i >= len(src):
        return None
    opener = src[i]
    closer = "]" if opener == "[" else "}"
    depth = 0
    in_str = False
    esc = False
    j = i
    while j < len(src):
        c = src[j]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == opener:
                depth += 1
            elif c == closer:
                depth -= 1
                if depth == 0:
                    return (i, j + 1)
        j += 1
    return None


def _runs_to_plain(runs: list) -> str:
    """Concatenate rich-text runs into plain text (drops bold styling)."""
    return "".join(r.get("t", "") for r in (runs or []))


def _runs_to_html(runs: list) -> str:
    """Convert rich-text runs to simple HTML with <strong> for bold runs,
    <br> for newlines. Matches the runsToHtml helper the v15 IIFE uses."""
    def esc(s: str) -> str:
        return (
            s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
        )
    out = []
    for r in runs or []:
        txt = esc(r.get("t", "")).replace("\n", "<br>")
        if r.get("b"):
            out.append(f"<strong>{txt}</strong>")
        else:
            out.append(txt)
    return "".join(out)


def _convert_notes(rich_notes: list) -> dict:
    """Translate v16's ceps_notes_rich (list of {title, body_runs, dim_label})
    into the reference's ceps_notes shape: {summary, themes:[{title, body}]}.

    Strategy:
      - If there's exactly 1 rich note, the first paragraph becomes `summary`
        and any subsequent bold-prefixed sections become themes.
      - With >=2 rich notes, each becomes a theme.
    """
    if not rich_notes:
        return {"summary": "", "themes": []}

    def _split_into_themes(runs: list) -> tuple[str, list]:
        """Split a single rich-text cell into (summary, themes).
        Bold runs longer than a few words act as theme delimiters (headings
        like `- Scope of high-risk` that break the rest into sections)."""
        themes: list = []
        summary_runs: list = []
        current_title = ""
        current_body_runs: list = []

        def flush():
            if current_title and (current_body_runs or True):
                themes.append({
                    "title": current_title,
                    "body": _runs_to_html(current_body_runs).strip(),
                })

        for r in runs:
            text = r.get("t", "")
            if r.get("b") and text.strip() and len(text.strip()) < 120:
                heading = text.strip().lstrip("- \t").rstrip(":")
                if current_title or current_body_runs:
                    flush()
                current_title = heading
                current_body_runs = []
            else:
                if current_title:
                    current_body_runs.append(r)
                else:
                    summary_runs.append(r)
        if current_title:
            flush()

        return (
            _runs_to_plain(summary_runs).strip(),
            themes,
        )

    if len(rich_notes) == 1:
        summary, themes = _split_into_themes(rich_notes[0].get("body_runs") or [])
        if not themes:
            # No bold headings inside the cell — keep it all as summary.
            return {"summary": summary, "themes": []}
        # If summary is empty but first theme's title is generic, promote its
        # body to the summary so the UI has something to show before the
        # collapsible themes.
        return {"summary": summary, "themes": themes}

    themes = []
    for n in rich_notes:
        themes.append({
            "title": n.get("title") or n.get("dim_label") or "Note",
            "body":  _runs_to_html(n.get("body_runs") or []).strip(),
        })
    return {"summary": "", "themes": themes}


def _v17_cluster_matrix_js() -> str:
    """Override the reference's renderMatrix so the Concepts page uses
    v16's cluster_summary layout: EU canonical term spans continuation
    rows, each jurisdiction shows its own variant pills per row, and
    pills are colour-coded by jurisdiction + bill code."""
    return r"""
<style>
/* v17 cluster-matrix overrides */
.v17-cluster-wrap{overflow-x:auto;border-radius:var(--r-xl);border:1px solid var(--bd);background:var(--card)}
.v17-cluster-table{width:100%;border-collapse:collapse;font-size:13px}
.v17-cluster-table thead th{font-family:var(--mono);font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-h);padding:10px 14px;background:var(--surf);border-bottom:1px solid var(--bd);text-align:left;white-space:nowrap}
.v17-cluster-table thead th.th-eu{border-top:4px solid var(--eu-active)}
.v17-cluster-table thead th.th-ca{border-top:4px solid var(--ca-active)}
.v17-cluster-table thead th.th-co{border-top:4px solid var(--co-active)}
.v17-cluster-table thead th.th-ny{border-top:4px solid var(--ny-active)}
.v17-cluster-table thead th.th-tx{border-top:4px solid var(--tx-active)}
.v17-cluster-table thead th.th-ut{border-top:4px solid var(--ut-active)}
.v17-cluster-table tbody td{padding:14px;border-top:1px solid var(--bd-s);vertical-align:middle;line-height:1.45}
.v17-cluster-table tbody tr.family-first td{border-top:2px solid var(--bd)}
.v17-cluster-table tbody tr:first-child td{border-top:none}
.v17-cluster-table .concept-cell{vertical-align:top;padding:18px 16px;background:var(--bg2);min-width:180px}
.v17-cluster-table .concept-title{font-family:var(--serif);font-weight:600;font-size:15px;color:var(--ink);margin-bottom:6px;letter-spacing:-.01em}
.v17-cluster-table .concept-cluster{font-family:var(--mono);font-size:9px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-h);background:var(--bd-s);padding:2px 7px;border-radius:3px;display:inline-block}
.v17-cluster-table .term-cell{vertical-align:middle}
.v17-cluster-table .pill-stack{display:flex;flex-direction:column;gap:6px}
.v17-cluster-table .v-pill{display:inline-block;padding:5px 12px;border-radius:var(--r-md,8px);font-family:var(--serif);font-size:13px;line-height:1.35;cursor:pointer;transition:filter .12s,transform .08s;text-align:center;border:none}
.v17-cluster-table .v-pill:hover{filter:brightness(.95);transform:translateY(-1px)}
.v17-cluster-table .v-pill.eu{background:var(--eu-bg);color:var(--eu-tx)}
.v17-cluster-table .v-pill.ca{background:var(--ca-bg);color:var(--ca-tx)}
.v17-cluster-table .v-pill.co{background:var(--co-bg);color:var(--co-tx)}
.v17-cluster-table .v-pill.ny{background:var(--ny-bg);color:var(--ny-tx)}
.v17-cluster-table .v-pill.tx{background:var(--tx-bg);color:var(--tx-tx)}
.v17-cluster-table .v-pill.ut{background:var(--ut-bg);color:var(--ut-tx)}
.v17-cluster-table .v-empty{color:var(--bd);font-size:13px}
</style>
<script>
(function(){
  function _escape(s){
    return String(s||'').replace(/[&<>]/g, function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c];});
  }

  // Parse "[SB53] Frontier developer" → {name: 'Frontier developer', bill: 'SB53'}.
  function _parseVariant(v){
    if (v && typeof v === 'object' && v.name) {
      return {name: v.name, bill: v.bill || '', sub_id: v.sub_id || ''};
    }
    var s = String(v || '').trim();
    var m = s.match(/^\[([^\]]+)\]\s*(.*)$/);
    if (m) return {name: m[2].trim(), bill: m[1].trim(), sub_id: ''};
    return {name: s, bill: '', sub_id: ''};
  }

  function _renderClusterMatrix(concepts, activeJuris){
    var JO = (typeof JURIS_ORDER !== 'undefined') ? JURIS_ORDER : ['eu','ca','co','ny','tx','ut'];
    var allJ = (activeJuris && activeJuris.length) ? JO.filter(function(j){ return activeJuris.indexOf(j) !== -1; }) : JO;
    var header = '<tr><th scope="col">Concept</th>';
    allJ.forEach(function(j){
      var label = (typeof JURIS_LABELS !== 'undefined' && JURIS_LABELS[j]) ? JURIS_LABELS[j] : j.toUpperCase();
      if (j === 'eu') label = 'EU (AIA)';
      header += '<th scope="col" class="th-' + j + '">' + _escape(label) + '</th>';
    });
    header += '</tr>';

    var bodyParts = [];
    concepts.forEach(function(c){
      var cs = c.cluster_summary || {};
      var rows = (cs.rows || []).filter(function(r){ return r.term_rowspan !== 0 || true; });
      if (!rows.length){
        // fall back: one row per sub_concept
        rows = (c.sub_concepts || []).map(function(sc){
          var cells = {};
          allJ.forEach(function(j){
            var jd = sc.jurisdictions[j];
            cells[j] = {rowspan: 1, variants: jd ? [{name: jd.term || '', bill: jd.bills || '', sub_id: sc.id}] : []};
          });
          return {term_label: sc.title, term_rowspan: 1, sub_id: sc.id, cells: cells};
        });
      }
      var totalRows = 0;
      rows.forEach(function(r){ if (r.term_rowspan && r.term_rowspan > 0) totalRows += r.term_rowspan; });
      if (totalRows === 0) totalRows = rows.length;

      rows.forEach(function(row, rIdx){
        var trClass = rIdx === 0 ? 'family-first' : '';
        bodyParts.push('<tr class="' + trClass + '">');
        if (rIdx === 0) {
          // Concept family cell spans all rows of this family.
          bodyParts.push(
            '<td class="concept-cell" rowspan="' + totalRows + '">' +
              '<button class="matrix-title-btn" onclick="go(\'concept\',\'' + c.id + '\')" style="background:none;border:none;padding:0;text-align:left;cursor:pointer;width:100%">' +
                '<div class="concept-title">' + _escape(c.title) + '</div>' +
                '<span class="concept-cluster">' + _escape(c.cluster) + '</span>' +
              '</button>' +
            '</td>'
          );
        }
        // Term-label column — v16's cluster_summary stores this separately,
        // but the user's screenshot shows the EU column IS the term cell.
        // We merge the two: render EU's variants as the term label stack.
        allJ.forEach(function(j){
          var cell = (row.cells || {})[j];
          if (!cell) cell = {rowspan: 1, variants: []};
          if (cell.rowspan === 0) return;  // covered by a previous row's rowspan
          var rsAttr = (cell.rowspan && cell.rowspan > 1) ? (' rowspan="' + cell.rowspan + '"') : '';
          var variants = cell.variants || [];
          if (!variants.length){
            bodyParts.push('<td class="col-' + j + '"' + rsAttr + '><span class="v-empty">\u2014</span></td>');
            return;
          }
          var parsed = variants.map(_parseVariant);
          var pills = parsed.map(function(v){
            var label = v.name;
            if (v.bill) label += ' (' + v.bill + ')';
            var onclick = '';
            if (v.sub_id) {
              onclick = ' onclick="go(\'concept\',\'' + c.id + '\',' + _subIdxOf(c, v.sub_id) + ')"';
            } else {
              onclick = ' onclick="go(\'concept\',\'' + c.id + '\')"';
            }
            return '<button class="v-pill ' + j + '"' + onclick + '>' + _escape(label) + '</button>';
          }).join('');
          bodyParts.push('<td class="col-' + j + '"' + rsAttr + '><div class="pill-stack">' + pills + '</div></td>');
        });
        bodyParts.push('</tr>');
      });
    });

    return '<div class="v17-cluster-wrap"><table class="v17-cluster-table"><thead>' + header + '</thead><tbody>' + bodyParts.join('') + '</tbody></table></div>';
  }

  function _subIdxOf(c, subId){
    var arr = c.sub_concepts || [];
    for (var i = 0; i < arr.length; i++) if (arr[i].id === subId) return i;
    return 0;
  }

  // Wait for the reference's renderMatrix to be defined, then replace it.
  function _install(){
    if (typeof window.renderMatrix !== 'function' || window.__v17_rm_patched) return;
    window.__v17_rm_patched = true;
    window.renderMatrix = function(filtered, activeJuris){
      try {
        var mv = document.getElementById('matrix-view');
        if (!mv) return;
        mv.innerHTML = _renderClusterMatrix(filtered, activeJuris || []);
      } catch(e){ console.error('v17 renderMatrix:', e); }
    };
    // The "Expand sub-concepts" checkbox is no longer meaningful — hide it.
    var wrap = document.getElementById('show-subconcepts-wrap');
    if (wrap) wrap.style.display = 'none';
    // Re-render in case Concepts page is already showing.
    if (typeof filterConcepts === 'function') filterConcepts();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', _install);
  else _install();
})();
</script>
"""


def _v17_home_cards_css() -> str:
    """Three-card home-page layout: Browse concepts / Methodology / Source laws."""
    return """
<style>
.v17-home-cards{margin:28px 0 20px}
.v17-home-card-grid{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:16px;max-width:860px}
.v17-home-card{display:flex;flex-direction:column;gap:10px;padding:28px 28px 24px;background:var(--card);border:1px solid var(--bd-s);border-radius:var(--r-xl);cursor:pointer;text-decoration:none;transition:border-color .15s,transform .15s,box-shadow .15s;min-height:170px}
.v17-home-card:hover{border-color:var(--accent);box-shadow:0 2px 12px rgba(0,51,153,.1);transform:translateY(-1px)}
.v17-home-card-primary{background:var(--accent);border-color:var(--accent);color:#fff}
.v17-home-card-primary:hover{background:var(--accent-d);border-color:var(--accent-d)}
.v17-home-card-primary .v17-home-card-title,
.v17-home-card-primary .v17-home-card-desc{color:#fff}
.v17-home-card-title{font-family:var(--serif);font-size:22px;font-weight:600;color:var(--ink);letter-spacing:-.02em;line-height:1.2;display:flex;align-items:center;gap:8px}
.v17-home-card-desc{font-family:var(--serif);font-size:14px;color:var(--ink-s);line-height:1.55;flex:1}
.v17-home-card-primary .v17-home-card-desc{color:rgba(255,255,255,.85)}
.v17-home-card-cta{margin-top:auto;font-size:18px;color:var(--ink-s)}
@media (max-width:720px){.v17-home-card-grid{grid-template-columns:1fr}}
</style>
"""


def _v17_law_drawer_js() -> str:
    """JS injected at end of <body> that (a) decodes the inline law blobs
    on first use, (b) wraps updateDrawerContent to append an
    "Explore in full law" button whose click expands the matching article
    text below the verbatim citation."""
    return r"""
<style>
.v17-explore-wrap{margin-top:18px;padding-top:16px;border-top:1px dashed var(--bd-s)}
.v17-explore-btn{font-family:var(--sans);font-size:12px;font-weight:500;color:var(--accent);background:var(--accent-l);border:1px solid transparent;padding:7px 14px;border-radius:var(--r-md,8px);cursor:pointer;display:inline-flex;align-items:center;gap:6px}
.v17-explore-btn:hover{background:var(--accent);color:#fff}
.v17-full-article{margin-top:14px;padding:14px 16px;background:var(--surf);border-left:3px solid var(--accent);border-radius:0 var(--r-md,8px) var(--r-md,8px) 0;font-family:var(--serif);font-size:14px;line-height:1.75;color:var(--ink);white-space:pre-wrap}
.v17-full-article-title{font-family:var(--mono);font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-h);margin-bottom:8px}
.v17-missing-anchor{margin:0 0 14px;padding:10px 14px;border-left:3px solid #c08a00;background:#fff8e6;font-size:13px;color:#5a4200;border-radius:3px}
</style>
<script>
(function(){
  var _lawCache = {};
  function _lawBlob(lawId){
    if (lawId in _lawCache) return _lawCache[lawId];
    var el = document.getElementById('law-blob-' + lawId);
    if (!el) { _lawCache[lawId] = null; return null; }
    try { _lawCache[lawId] = JSON.parse(el.textContent); }
    catch(e) { _lawCache[lawId] = null; }
    return _lawCache[lawId];
  }
  function _resolveRef(refStr){
    if (!refStr || !window.REF_MAP) return null;
    var s = String(refStr).trim();
    var hit = window.REF_MAP[s];
    if (hit && hit.law) return hit;
    // Cell references are often a ;-joined list of REF_MAP keys.
    var parts = s.split(/\s*;\s*/);
    for (var i = 0; i < parts.length; i++) {
      hit = window.REF_MAP[parts[i].trim()];
      if (hit && hit.law) return hit;
    }
    return null;
  }
  function _findArticle(blob, anchor){
    if (!blob || !anchor) return null;
    var items = blob.articles || blob.sections || [];
    var a = String(anchor);
    // Try exact, then first segment (e.g. '6-1' → '6').
    var match = items.find(function(x){ return String(x.id) === a; });
    if (match) return match;
    var short = a.split('-')[0];
    match = items.find(function(x){ return String(x.id) === short; });
    return match || null;
  }
  function _appendFullArticle(info){
    var body = document.getElementById('drawer-verbatim');
    if (!body) return;
    // Clear any previous wrap before adding a new one.
    var prev = body.parentNode.querySelector('.v17-explore-wrap');
    if (prev) prev.parentNode.removeChild(prev);
    var blob = _lawBlob(info.law);
    var anchor = info.anchor;
    // EU AI Act article ids are bare numbers; REF_MAP stores them as e.g. '3-1'.
    if (anchor && info.law === 'eu-ai-act' && info.kind === 'article') {
      anchor = anchor.split('-')[0];
    }
    var art = _findArticle(blob, anchor);
    var wrap = document.createElement('div');
    wrap.className = 'v17-explore-wrap';
    if (!blob) {
      wrap.innerHTML = '<div class="v17-full-article"><div class="v17-full-article-title">Full article</div>Law text is not embedded for this source.</div>';
    } else if (!art) {
      var banner = '<div class="v17-missing-anchor">Section "' + (anchor || '') + '" is not separately parsed in this law blob. Showing the full scraped text below — use browser find to locate the section.</div>';
      var raw = blob.raw_text ? String(blob.raw_text).slice(0, 20000) : 'No section text available.';
      wrap.innerHTML = banner + '<div class="v17-full-article"><div class="v17-full-article-title">Full bill text (truncated)</div>' + _escape(raw) + '</div>';
    } else {
      var title = art.title ? art.title : ('Section ' + art.id);
      wrap.innerHTML = '<div class="v17-full-article"><div class="v17-full-article-title">' + _escape(title) + '</div>' + _escape(String(art.text || '')) + '</div>';
    }
    body.parentNode.insertBefore(wrap, body.nextSibling);
  }
  function _escape(s){
    return String(s).replace(/[&<>]/g, function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c];});
  }
  function _installExploreButton(refStr){
    // Drop any existing button/wrap from a previous open.
    var body = document.getElementById('drawer-verbatim');
    if (!body) return;
    var old = body.parentNode.querySelector('.v17-explore-wrap');
    if (old) old.parentNode.removeChild(old);
    var actions = document.querySelector('.drawer-actions');
    if (!actions) return;
    Array.prototype.forEach.call(
      actions.querySelectorAll('.v17-explore-btn'),
      function(n){ n.parentNode.removeChild(n); }
    );
    var info = _resolveRef(refStr);
    if (!info || !info.law) return;
    var btn = document.createElement('button');
    btn.className = 'drawer-action-btn v17-explore-btn';
    btn.textContent = 'Explore in full law \u2192';
    btn.addEventListener('click', function(){ _appendFullArticle(info); });
    actions.insertBefore(btn, actions.firstChild);
  }
  // Wrap updateDrawerContent once renderConceptPage / drawer code is ready.
  function _installWrapper(){
    if (typeof window.updateDrawerContent !== 'function' || window.__v17_udc_patched) return;
    window.__v17_udc_patched = true;
    var orig = window.updateDrawerContent;
    window.updateDrawerContent = function(dim, juris, sc, c){
      orig.apply(this, arguments);
      try {
        var cell = dim && dim.cells && dim.cells[juris];
        _installExploreButton(cell && cell.reference);
      } catch(e){ console.error('v17 explore-btn:', e); }
    };
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _installWrapper);
  } else {
    _installWrapper();
  }
})();
</script>
"""


def _transform_concepts(concepts: list) -> list:
    """Return a deep-copied CONCEPTS list where each sub_concept has
    ceps_notes (reference shape) in place of v16's ceps_notes_rich.
    cluster_summary is preserved so v17's overridden renderMatrix can
    reuse v16's rowspan/variant layout."""
    out: list = []
    for c in concepts:
        sub_concepts: list = []
        for sc in c.get("sub_concepts") or []:
            new_sc = {
                "id":             sc.get("id"),
                "title":          sc.get("title"),
                "jurisdictions":  sc.get("jurisdictions") or {},
                "dimensions":     sc.get("dimensions") or [],
                "ceps_notes":     _convert_notes(sc.get("ceps_notes_rich") or []),
            }
            sub_concepts.append(new_sc)
        out.append({
            "id":             c.get("id"),
            "cluster":        c.get("cluster"),
            "title":          c.get("title"),
            "ceps_framing":   c.get("ceps_framing") or "",
            "cluster_summary": c.get("cluster_summary") or {"headers": [], "rows": []},
            "sub_concepts":   sub_concepts,
        })
    return out


def main() -> None:
    import build_v16

    print("== v17 build ==")
    # 1. Ensure v16 is up to date.
    if not HTML_V16.exists():
        build_v16.main()

    v16_html = HTML_V16.read_text(encoding="utf-8")
    span = _find_json_literal(v16_html, "CONCEPTS")
    if not span:
        raise SystemExit("v16 HTML: `const CONCEPTS` literal not found")
    v16_concepts = json.loads(v16_html[span[0]:span[1]])
    print(f"  loaded {len(v16_concepts)} concepts from v16")

    # 2. Transform to reference shape.
    transformed = _transform_concepts(v16_concepts)
    n_notes = sum(
        bool(sc["ceps_notes"].get("summary") or sc["ceps_notes"].get("themes"))
        for c in transformed for sc in c["sub_concepts"]
    )
    print(f"  transformed notes:   {n_notes} sub_concepts have notes")

    # 3. Load reference shell.
    if not REF_HTML.exists():
        raise SystemExit(f"reference shell not found at {REF_HTML}")
    html = REF_HTML.read_text(encoding="utf-8")

    # 4. Replace reference's CONCEPTS with transformed data.
    span = _find_json_literal(html, "CONCEPTS")
    if not span:
        raise SystemExit("reference shell: `const CONCEPTS` not found")
    new_blob = json.dumps(transformed, ensure_ascii=False, separators=(",", ":"))
    html = html[: span[0]] + new_blob + html[span[1] :]
    print("  CONCEPTS replaced with v16's data")

    # 5. The reference renderer expects jurisdictions keyed by {'eu','ca',...}
    #    but v16 emits lane-suffixed keys like 'ca-0-covered-provider' when a
    #    state has multiple bills applicable to the same sub_concept. Without
    #    help, JURIS_LABELS['ca-0-covered-provider'] is undefined and the
    #    column header renders as literal "undefined".
    #
    #    Patch the inline template strings in renderAnalysisTable and
    #    renderMatrix so every `JURIS_LABELS[j]` falls back to the parent
    #    jurisdiction's label, and every `th-${j}` / `j-pill ${j}` CSS class
    #    uses the parent jid (so the colour theming still works).
    # 4b. Front page: replace the "Two ways to consult" two-card section
    #     with a three-card layout (Browse concepts / Methodology / Source laws).
    new_modes = '''<section class="v17-home-cards" aria-label="Explore the lexicon">
      <div class="v17-home-card-grid">
        <a class="v17-home-card v17-home-card-primary"
           onclick="go('concepts');return false"
           href="#/concepts"
           aria-label="Browse concepts">
          <span class="v17-home-card-title">Browse concepts <span aria-hidden="true">\u2192</span></span>
          <span class="v17-home-card-desc">Explore 6 concept families across EU and US AI legislation with CEPS comparative analysis</span>
        </a>
        <a class="v17-home-card"
           onclick="go('methodology');return false"
           href="#/methodology"
           aria-label="Methodology">
          <span class="v17-home-card-title">Methodology</span>
          <span class="v17-home-card-desc">Scope, sources, and approach</span>
          <span class="v17-home-card-cta" aria-hidden="true">\u2192</span>
        </a>
        <a class="v17-home-card"
           onclick="go('laws');return false"
           href="#/laws"
           aria-label="Source laws">
          <span class="v17-home-card-title">Source laws</span>
          <span class="v17-home-card-desc">11 regulatory frameworks</span>
          <span class="v17-home-card-cta" aria-hidden="true">\u2192</span>
        </a>
      </div>
    </section>'''
    consult_start = html.find('<section class="consult-modes"')
    consult_end_anchor = "</section>"
    if consult_start != -1:
        # find matching </section>
        consult_end = html.find(consult_end_anchor, consult_start)
        if consult_end != -1:
            end_idx = consult_end + len(consult_end_anchor)
            html = html[:consult_start] + new_modes + html[end_idx:]
            print("  home cards:          swapped for 3-card layout")

    # 4c. Always expand sub-concept rows on the matrix (each variant on its
    #     own row), and default the "Expand sub-concepts" checkbox to
    #     checked since users want that level of detail by default.
    html = html.replace(
        '<input type="checkbox" id="show-subconcepts" onchange="filterConcepts()">',
        '<input type="checkbox" id="show-subconcepts" onchange="filterConcepts()" checked>',
        1,
    )
    print("  show-subconcepts:    default-checked")

    # Replace every `${JURIS_LABELS[j]}` template interpolation with a
    # lane-key-aware fallback, and every `${j}` used in a CSS class context
    # with `${j.split('-')[0]}`.
    label_expr = "${JURIS_LABELS[j] || JURIS_LABELS[j.split('-')[0]] || j}"
    replacements = [
        # Column label template interpolations — everywhere.
        ("${JURIS_LABELS[j]}", label_expr),
        # CSS class hooks — these pair the key with a styled variant.
        ('class="th-${j}"',   'class="th-${j.split(\'-\')[0]}"'),
        ('class="col-${j}"',  'class="col-${j.split(\'-\')[0]}"'),
        ('class="j-pill ${j}"', 'class="j-pill ${j.split(\'-\')[0]}"'),
        ('class="j-dot ${j}"', 'class="j-dot ${j.split(\'-\')[0]}"'),
    ]
    for old, new in replacements:
        count_before = html.count(old)
        if count_before == 0:
            continue
        html = html.replace(old, new)
        print(f"  patched {count_before}x: {old!r}")
    print("  renderer patches:    done")

    # 4d. Research cutoff date.
    if "<strong>28 Mar 2026</strong>" in html:
        html = html.replace(
            "<strong>28 Mar 2026</strong>",
            "<strong>20 Apr 2026</strong>",
            1,
        )
        print("  research cutoff:     20 Apr 2026")

    # 6. Port v16's law-blob infrastructure so the drawer can show the
    #    full statute text for any cell whose `reference` resolves in
    #    REF_MAP (e.g. "EU AI Act, Article 6"). The reference shell only
    #    shows the cell's verbatim extract — we attach a collapsible
    #    "Full article from source law" section beneath it.
    v16_law_blobs = re.findall(
        r'<script type="application/json" id="law-blob-[^"]+">[\s\S]*?</script>',
        v16_html,
    )
    ref_span = _find_json_literal(v16_html, "REF_MAP")
    if ref_span:
        ref_map_blob = v16_html[ref_span[0] : ref_span[1]]
    else:
        ref_map_blob = "{}"
    stubs_span = _find_json_literal(v16_html, "LAW_STUBS")
    if stubs_span:
        stubs_blob = v16_html[stubs_span[0] : stubs_span[1]]
    else:
        stubs_blob = "{}"
    law_infra = (
        "\n<!-- v16 law infrastructure (inline, lazy-parsed) -->\n"
        + "\n".join(v16_law_blobs)
        + f'\n<script>window.REF_MAP = {ref_map_blob};window.LAW_STUBS = {stubs_blob};</script>\n'
    )
    html = html.replace(
        "</body>",
        _v17_home_cards_css()
        + _v17_cluster_matrix_js()
        + law_infra
        + _v17_law_drawer_js()
        + "\n</body>",
        1,
    )
    print(f"  law blobs injected:  {len(v16_law_blobs)}")

    # 7. Tag the version for clarity.
    html = html.replace(
        "<!-- DAL v18.5 -->",
        "<!-- DAL v17 (v16 data + v18.5 reference shell) -->",
        1,
    )
    html = html.replace(
        "<title>Digital AI Lexicon — CEPS</title>",
        "<title>Digital AI Lexicon v17 — CEPS</title>",
        1,
    )

    HTML_V17.write_text(html, encoding="utf-8")
    final = len(html)
    ref_size = REF_HTML.stat().st_size
    v16_size = HTML_V16.stat().st_size
    print(f"\nWrote {HTML_V17}  ({final:,} bytes)")
    print(f"  vs reference: {final - ref_size:+,}")
    print(f"  vs v16:       {final - v16_size:+,}")

    # Run the v17 smoke test. Any regression fails the build.
    import subprocess, sys
    test_path = HERE / "test_lexicon_v17.py"
    if test_path.exists():
        print("\n[v17 smoke test]")
        rc = subprocess.run([sys.executable, str(test_path)], cwd=HERE).returncode
        if rc != 0:
            raise SystemExit(
                f"v17 smoke test failed (rc={rc}). Build artifact is "
                f"still written, but review the failures before shipping."
            )


if __name__ == "__main__":
    main()
