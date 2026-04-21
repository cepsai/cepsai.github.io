"""build_v21.py — Digital AI Lexicon v21

Reshapes v20's Legal-text view to show ONE dim/sub row at a time with
the full verbatim text (no line-clamp), driven by two filter dropdowns
(Dimension + Sub-dimension) and prev/next navigation.

Rationale: v20's Legal-text view showed every row at once with
6-line-clamped cells. For legal text that's often multi-paragraph, the
clamp hid most of the content and the table felt overwhelming. v21
swaps that for a focused single-row comparison across jurisdictions
with the full text expanded in each cell.

Build chain: v13 -> v15 -> v16 -> v17 -> v18 -> v20 -> v21.

Changes over v20:
    * Inside each concept page, when the Legal-text mode tab is active:
        - a filter bar appears directly above the table with
          Dimension + Sub-dimension dropdowns and prev/next buttons.
        - the table renders only the ONE (dim, sub) row chosen by the
          filter. No rowspan is needed for a single row — col 1 carries
          the dim label, col 2 the sub-dim, columns 3+ carry each
          jurisdiction's full verbatim.
        - verbatim cells are unclamped (no -webkit-line-clamp).
        - Analysis mode is unchanged.
    * Filter selection persists in state (per session) and survives
      sub-concept switches when the stored (dim, sub) still exists in
      the new sub-concept's row set; otherwise it resets to index 0.

Predecessors (v13..v20) untouched.

Note: downstream HTML files cache aggressively. If xlsx or law JSON
changed, wipe before rebuild:
    rm -f digital_lexicon_v1{6,7,8}.html digital_lexicon_v2*.html
    python3 build_v21.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE      = Path(__file__).parent
HTML_V20  = HERE / "digital_lexicon_v20.html"
HTML_V21  = HERE / "digital_lexicon_v21.html"


# --------------------------------------------------------------------------- #
# v21 overrides — single-row filter UI + full-text cells.                     #
# --------------------------------------------------------------------------- #

def _v21_overrides_css_js() -> str:
    return r"""
<style>
/* ── v21 filter bar, directly above the one-row Legal-text table ─────── */
.v21-filter-bar{
  display:flex;
  flex-wrap:wrap;
  align-items:end;
  gap:16px 22px;
  padding:14px 16px;
  margin:0 0 16px 0;
  background:var(--bg2);
  border:1px solid var(--bd-s);
  border-radius:var(--r-md,8px);
}
.v21-filter-group{
  display:flex;
  flex-direction:column;
  gap:4px;
  min-width:200px;
  flex:1 1 220px;
}
.v21-filter-group label{
  font-family:var(--mono);
  font-size:10px;
  text-transform:uppercase;
  letter-spacing:.06em;
  color:var(--ink-h);
  font-weight:600;
}
.v21-filter-group select{
  font-family:var(--sans);
  font-size:13px;
  color:var(--ink);
  background:var(--card);
  border:1px solid var(--bd);
  border-radius:var(--r-sm,5px);
  padding:8px 10px;
  cursor:pointer;
  width:100%;
}
.v21-filter-group select:focus{
  outline:none;
  border-color:var(--accent);
  box-shadow:0 0 0 2px var(--accent-l);
}
.v21-filter-nav{
  display:flex;
  gap:6px;
  align-items:center;
  margin-left:auto;
}
.v21-filter-btn{
  font-family:var(--sans);
  font-size:13px;
  font-weight:500;
  color:var(--ink);
  background:var(--card);
  border:1px solid var(--bd);
  border-radius:var(--r-sm,5px);
  padding:8px 14px;
  cursor:pointer;
  display:inline-flex;
  align-items:center;
  gap:4px;
  line-height:1;
  transition:background-color .12s, border-color .12s;
}
.v21-filter-btn:hover:not(:disabled){
  background:var(--accent-l);
  border-color:var(--accent);
  color:var(--accent);
}
.v21-filter-btn:disabled{ opacity:.4; cursor:not-allowed; }
.v21-filter-count{
  font-family:var(--mono);
  font-size:11px;
  color:var(--ink-s);
  margin:0 8px;
  white-space:nowrap;
}

/* Full-text verbatim cells (no clamp). Vertical alignment stays on top
   so multi-paragraph cells align with shorter ones. */
.v21-verbatim-cell{
  cursor:pointer;
  font-family:var(--serif);
  font-size:13px;
  line-height:1.6;
  color:var(--ink);
  padding:6px 8px;
  border-radius:var(--r-sm,4px);
  transition:background-color .12s;
  white-space:pre-wrap;
  word-break:break-word;
}
.v21-verbatim-cell:hover,
.v21-verbatim-cell:focus{ background:var(--accent-l); outline:none; }

/* Cells on the single-row layout should top-align and sit roomily. */
.analysis-table.v21-one-row tbody td{
  vertical-align:top;
  padding-top:14px;
  padding-bottom:14px;
}
.analysis-table.v21-one-row .v21-analysis-only{
  color:var(--ink-s);
  font-style:italic;
}
</style>
<script>
(function(){
  if (typeof state === 'undefined') return;

  // Fields persisted in state (written via saveState()):
  //   state.verbatimDim : string    — selected parent label
  //   state.verbatimSub : string    — selected sub-dim label (unique within dim)

  function _escH(s){
    return String(s==null?'':s).replace(/[&<>"']/g, function(c){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
    });
  }

  function _dimParent(c, dim){
    if (dim && dim.parent_label) return dim.parent_label;
    var key = (dim && (dim.label || '')).toLowerCase().trim();
    var m = window.V20_DIM_PARENTS || {};
    var cm = m[c && c.id] || {};
    if (cm[key]) return cm[key];
    var g = window.V20_DIM_PARENTS_GLOBAL || {};
    if (g[key]) return g[key];
    return (dim && (dim.label || '')) || '';
  }
  function _dimSub(dim){ return (dim && (dim.sub_label || dim.label || '')) || ''; }

  function _buildRowsPlan(c, sc){
    return (sc.dimensions || []).map(function(dim){
      return {dim: dim, parent: _dimParent(c, dim), sub: _dimSub(dim)};
    });
  }

  function _uniqueDims(rowsPlan){
    var seen = {};
    var out = [];
    rowsPlan.forEach(function(r){
      if (!seen[r.parent]) { seen[r.parent] = true; out.push(r.parent); }
    });
    return out;
  }

  function _subsForDim(rowsPlan, dim){
    // Preserve sheet order and allow duplicates (e.g. Incident has two
    // Scope/(High-risk, GPAI...) entries that need to stay distinct).
    return rowsPlan
      .map(function(r, i){ return r.parent === dim ? {sub: r.sub, idx: i} : null; })
      .filter(function(x){ return x; });
  }

  function _findRowIdx(rowsPlan, dim, sub){
    for (var i = 0; i < rowsPlan.length; i++){
      if (rowsPlan[i].parent === dim && rowsPlan[i].sub === sub) return i;
    }
    return -1;
  }

  function _ensureFilterBar(){
    var pc = document.getElementById('p-concept');
    if (!pc) return null;
    var bar = document.getElementById('v21-filter-bar');
    if (bar) return bar;
    bar = document.createElement('div');
    bar.id = 'v21-filter-bar';
    bar.className = 'v21-filter-bar';
    bar.innerHTML =
      '<div class="v21-filter-group">' +
      '  <label for="v21-dim-select">Dimension</label>' +
      '  <select id="v21-dim-select"></select>' +
      '</div>' +
      '<div class="v21-filter-group">' +
      '  <label for="v21-sub-select">Sub-dimension</label>' +
      '  <select id="v21-sub-select"></select>' +
      '</div>' +
      '<div class="v21-filter-nav">' +
      '  <button type="button" class="v21-filter-btn" id="v21-prev-btn" aria-label="Previous row">\u2039 Prev</button>' +
      '  <span class="v21-filter-count" id="v21-row-count"></span>' +
      '  <button type="button" class="v21-filter-btn" id="v21-next-btn" aria-label="Next row">Next \u203a</button>' +
      '</div>';
    // Insert just ABOVE the analysis-wrap that contains the table.
    var wrap = document.querySelector('#p-concept .analysis-wrap');
    if (wrap && wrap.parentNode) {
      wrap.parentNode.insertBefore(bar, wrap);
    } else {
      pc.appendChild(bar);
    }
    // Wire events once.
    bar.querySelector('#v21-dim-select').addEventListener('change', _onDimChange);
    bar.querySelector('#v21-sub-select').addEventListener('change', _onSubChange);
    bar.querySelector('#v21-prev-btn').addEventListener('click', function(){ _stepRow(-1); });
    bar.querySelector('#v21-next-btn').addEventListener('click', function(){ _stepRow(1); });
    return bar;
  }

  function _showFilterBar(show){
    var bar = document.getElementById('v21-filter-bar');
    if (!bar) return;
    bar.style.display = show ? '' : 'none';
  }

  function _currentRowsPlan(){
    var c  = getConcept(state.conceptId);
    var sc = c && c.sub_concepts && (c.sub_concepts[state.subConceptIdx] || c.sub_concepts[0]);
    if (!sc) return {c: null, sc: null, rowsPlan: []};
    return {c: c, sc: sc, rowsPlan: _buildRowsPlan(c, sc)};
  }

  function _resolveSelection(rowsPlan){
    if (!rowsPlan.length) return 0;
    var idx = _findRowIdx(rowsPlan, state.verbatimDim, state.verbatimSub);
    if (idx < 0) idx = 0;
    var r = rowsPlan[idx];
    // Snap state to the canonical values.
    state.verbatimDim = r.parent;
    state.verbatimSub = r.sub;
    return idx;
  }

  function _populateDimSelect(rowsPlan, selectedDim){
    var sel = document.getElementById('v21-dim-select');
    if (!sel) return;
    var dims = _uniqueDims(rowsPlan);
    sel.innerHTML = dims.map(function(d){
      return '<option value="' + _escH(d) + '"' + (d === selectedDim ? ' selected' : '') + '>' +
             _escH(d) + '</option>';
    }).join('');
  }

  function _populateSubSelect(rowsPlan, selectedDim, selectedSub){
    var sel = document.getElementById('v21-sub-select');
    if (!sel) return;
    var subs = _subsForDim(rowsPlan, selectedDim);
    // Use a JSON-encoded {sub, idx} as the value to support duplicate
    // sub labels within the same dim (rare but present on Incident).
    sel.innerHTML = subs.map(function(s){
      var val = JSON.stringify({sub: s.sub, idx: s.idx});
      var sel_ = (s.sub === selectedSub) ? ' selected' : '';
      return '<option value="' + _escH(val) + '"' + sel_ + '>' + _escH(s.sub) + '</option>';
    }).join('');
  }

  function _updateNav(rowsPlan, idx){
    var prev = document.getElementById('v21-prev-btn');
    var next = document.getElementById('v21-next-btn');
    var count = document.getElementById('v21-row-count');
    if (prev) prev.disabled = (idx <= 0);
    if (next) next.disabled = (idx >= rowsPlan.length - 1);
    if (count) count.textContent = (idx + 1) + ' of ' + rowsPlan.length;
  }

  function _onDimChange(){
    var dimSel = document.getElementById('v21-dim-select');
    if (!dimSel) return;
    var newDim = dimSel.value;
    var ctx = _currentRowsPlan();
    var subs = _subsForDim(ctx.rowsPlan, newDim);
    state.verbatimDim = newDim;
    state.verbatimSub = subs.length ? subs[0].sub : '';
    try { if (typeof saveState === 'function') saveState(); } catch(e){}
    _rerender();
  }

  function _onSubChange(){
    var subSel = document.getElementById('v21-sub-select');
    if (!subSel) return;
    try {
      var parsed = JSON.parse(subSel.value);
      state.verbatimSub = parsed.sub;
      try { if (typeof saveState === 'function') saveState(); } catch(e){}
      _rerender();
    } catch(e){}
  }

  function _stepRow(delta){
    var ctx = _currentRowsPlan();
    if (!ctx.rowsPlan.length) return;
    var idx = _resolveSelection(ctx.rowsPlan);
    var newIdx = Math.max(0, Math.min(ctx.rowsPlan.length - 1, idx + delta));
    if (newIdx === idx) return;
    var r = ctx.rowsPlan[newIdx];
    state.verbatimDim = r.parent;
    state.verbatimSub = r.sub;
    try { if (typeof saveState === 'function') saveState(); } catch(e){}
    _rerender();
  }

  function _rerender(){
    if (typeof renderAnalysisTable === 'function') renderAnalysisTable();
  }

  function _renderV21VerbatimTable(){
    var ctx = _currentRowsPlan();
    if (!ctx.sc) return;
    var thead = document.getElementById('analysis-thead');
    var tbody = document.getElementById('analysis-tbody');
    if (!thead || !tbody) return;

    var table = thead.closest('table');
    if (table) table.classList.add('v21-one-row');

    var rowsPlan = ctx.rowsPlan;
    var idx = _resolveSelection(rowsPlan);
    _ensureFilterBar();
    _populateDimSelect(rowsPlan, state.verbatimDim);
    _populateSubSelect(rowsPlan, state.verbatimDim, state.verbatimSub);
    _updateNav(rowsPlan, idx);
    _showFilterBar(true);

    var sc = ctx.sc, c = ctx.c;
    var juris = Object.keys(sc.jurisdictions);
    var JL = (typeof JURIS_LABELS !== 'undefined') ? JURIS_LABELS : {};

    // Header: Dimension | Sub-dimension | ...jurisdictions
    var head = '<tr>';
    head += '<th scope="col" class="analysis-dim-cell v20-dim-col">Dimension</th>';
    head += '<th scope="col" class="v20-subdim-cell">Sub-dimension</th>';
    juris.forEach(function(j){
      var jid = String(j).split('-')[0];
      var jd = sc.jurisdictions[j];
      head += '<th scope="col" class="th-' + jid + '">' + _escH(JL[j] || JL[jid] || j) +
              '<span class="j-law">' + _escH((jd && jd.law) || '') + '</span></th>';
    });
    head += '</tr>';
    thead.innerHTML = head;

    // Body: single row.
    if (!rowsPlan.length) {
      tbody.innerHTML = '<tr><td colspan="' + (2 + juris.length) + '" style="padding:24px;text-align:center;color:var(--ink-s);font-style:italic">No dimensions on this sub-concept.</td></tr>';
      return;
    }
    var r = rowsPlan[idx];
    var tr = '<tr>';
    tr += '<td class="v20-dim-cell">' + _escH(r.parent) + '</td>';
    tr += '<td class="v20-subdim-cell">' + _escH(r.sub) + '</td>';
    juris.forEach(function(j){
      var cell = r.dim.cells[j];
      if (cell && cell.verbatim) {
        tr += '<td><span class="v21-verbatim-cell addressed" tabindex="0" role="button" ' +
              'data-dimid="' + _escH(r.dim.id) + '" data-juris="' + _escH(j) + '" ' +
              'aria-label="Open full law: ' + _escH(JL[j] || j) + ' on ' + _escH(r.dim.label) + '">' +
              _escH(cell.verbatim) + '</span></td>';
      } else if (cell && cell.analysis) {
        tr += '<td><span class="cell-null v21-analysis-only" ' +
              'title="Analysis only \u2014 no verbatim quote in source law">\u2014</span></td>';
      } else {
        tr += '<td><span class="cell-null" aria-label="Not addressed">\u2014</span></td>';
      }
    });
    tr += '</tr>';
    tbody.innerHTML = tr;

    tbody.addEventListener('click', _verbatimCellClick);
    tbody.addEventListener('keydown', function(e){
      if (e.key !== 'Enter' && e.key !== ' ') return;
      var t = e.target && e.target.closest && e.target.closest('.v21-verbatim-cell');
      if (!t) return;
      e.preventDefault();
      _verbatimCellClick({target: t});
    });
  }

  function _verbatimCellClick(ev){
    var el = ev && ev.target && (ev.target.closest ? ev.target.closest('.v21-verbatim-cell') : null);
    if (!el) return;
    var dimId = el.getAttribute('data-dimid');
    var j     = el.getAttribute('data-juris');
    var c  = getConcept(state.conceptId);
    var sc = c && c.sub_concepts && (c.sub_concepts[state.subConceptIdx] || c.sub_concepts[0]);
    var dim = sc && (sc.dimensions || []).find(function(d){ return d.id === dimId; });
    if (!dim) return;
    _openFullLawForCell(dim, j);
  }

  function _openFullLawForCell(dim, juris){
    if (typeof openDrawer !== 'function') return;
    openDrawer(dim.id, juris);
    requestAnimationFrame(function(){
      var btn = document.querySelector('.drawer-actions .v17-explore-btn');
      if (btn) btn.click();
    });
  }

  // ── Wrap renderAnalysisTable ─────────────────────────────────────────
  function _installHooks(){
    if (window.__v21_installed) return;
    window.__v21_installed = true;

    if (typeof window.renderAnalysisTable === 'function') {
      var origRAT = window.renderAnalysisTable;  // already v20-wrapped
      window.renderAnalysisTable = function(){
        if (state.mode === 'verbatim') {
          // Run the v20-wrapped render first so it also fires any v18 /
          // v20 side-effects (CEPS notes area, mode-bar update). Then
          // immediately replace its output with our single-row layout.
          origRAT.apply(this, arguments);
          _renderV21VerbatimTable();
          return;
        }
        // Analysis mode: hide the filter bar, drop one-row class.
        _showFilterBar(false);
        var thead = document.getElementById('analysis-thead');
        var table = thead && thead.closest('table');
        if (table) table.classList.remove('v21-one-row');
        return origRAT.apply(this, arguments);
      };
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _installHooks);
  } else {
    _installHooks();
  }
})();
</script>
"""


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #

def main() -> None:
    import build_v20

    print("== v21 build ==")
    if not HTML_V20.exists():
        build_v20.main()
    html = HTML_V20.read_text(encoding="utf-8")

    html = html.replace("</body>", _v21_overrides_css_js() + "\n</body>", 1)
    print("  overrides:           CSS + JS appended (filter bar + single-row)")

    html = html.replace(
        "<!-- DAL v20 (in-page Analysis/Verbatim mode tabs) -->",
        "<!-- DAL v21 (single-row Legal-text view with dim/sub filters) -->",
        1,
    )
    html = html.replace(
        "<title>Digital AI Lexicon v20 \u2014 CEPS</title>",
        "<title>Digital AI Lexicon v21 \u2014 CEPS</title>",
        1,
    )

    HTML_V21.write_text(html, encoding="utf-8")
    print(f"\nWrote {HTML_V21}  ({len(html):,} bytes)")

    test_path = HERE / "test_lexicon_v21.py"
    if test_path.exists():
        print("\n[v21 smoke test]")
        rc = subprocess.run([sys.executable, str(test_path)], cwd=HERE).returncode
        if rc != 0:
            raise SystemExit(f"v21 smoke test failed (rc={rc})")


if __name__ == "__main__":
    main()
