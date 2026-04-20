"""build_v16.py — Digital AI Lexicon v16

Builds on top of v15 with:
  1. Lighter output (deduped shadow consts, merged rich-text runs, minified CSS).
  2. "Explore in full law" button on verbatim drawers.
  3. Wider concept-page dimension table (no horizontal scroll on desktop).
  4. Matrix pill click → concept page + matching sub-tab (no drawer detour).

Entry point:
    python3 build_v16.py
Writes:
    digital_lexicon_v16.html
Leaves v14/v15 untouched.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import build_v13
import build_v15

HERE = Path(__file__).parent
HTML_V16 = HERE / "digital_lexicon_v16.html"


# --------------------------------------------------------------------------- #
# Task 1a — Merge adjacent rich-text runs with identical bold state.          #
# Applied as a build-time patch to cell_runs().                               #
# --------------------------------------------------------------------------- #

def _install_runs_merge_patch() -> None:
    orig = build_v13.cell_runs

    def patched(cell):
        runs = orig(cell)
        if not runs:
            return runs
        out = [{"t": runs[0].get("t", ""), "b": bool(runs[0].get("b"))}]
        for r in runs[1:]:
            b = bool(r.get("b"))
            t = r.get("t", "")
            if out[-1]["b"] == b:
                out[-1]["t"] += t
            else:
                out.append({"t": t, "b": b})
        return out

    build_v13.cell_runs = patched
    build_v15.cell_runs = patched


# --------------------------------------------------------------------------- #
# Task 1b — Minify inline <style> blocks (comments + whitespace).             #
# Conservative: no color shortening, no selector rewrites, no JS minify.      #
# --------------------------------------------------------------------------- #

def _minify_css(css: str) -> str:
    css = re.sub(r"/\*[\s\S]*?\*/", "", css)
    lines = [ln.strip() for ln in css.splitlines()]
    css = " ".join(ln for ln in lines if ln)
    css = re.sub(r" +", " ", css)
    css = re.sub(r"\s*([{};,])\s*", r"\1", css)
    css = css.replace(";}", "}")
    return css.strip()


def _minify_style_blocks(html: str) -> str:
    def sub(m: "re.Match[str]") -> str:
        return m.group(1) + _minify_css(m.group(2)) + "</style>"

    return re.sub(r"(<style[^>]*>)([\s\S]*?)</style>", sub, html)


# --------------------------------------------------------------------------- #
# Task 4b — Rebuild cluster_summary.row[*].sub_id via a smarter matcher       #
# (GPAI ↔ general-purpose AI normalization, forward-fill continuation rows).  #
# v15's cluster_summary_from_matrix uses exact-title matching, which fails    #
# for:                                                                        #
#   matrix "Provider of GPAI models with systemic risk"  →                    #
#   sub_concept "Provider of general-purpose AI models with systemic risk"    #
# and blank-term continuation rows (e.g. NY "Large developer (A6453B)")       #
# silently fall back to sub_concepts[0] = "Provider".                         #
# --------------------------------------------------------------------------- #

_ABBREVIATIONS = [
    (r"\bgpai\b",  "general purpose ai"),
    (r"\bg\.p\.a\.i\.\b", "general purpose ai"),
    (r"\bgeneral[- ]purpose\s+ai\b", "general purpose ai"),
    (r"\bai\s+models?\b", "ai model"),
    (r"\bai\s+systems?\b", "ai system"),
]


def _norm_concept_name(s: str) -> str:
    s = (s or "").lower()
    for pat, repl in _ABBREVIATIONS:
        s = re.sub(pat, repl, s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _find_best_sub_id(term_label: str, sub_concepts: list) -> str:
    if not term_label or not sub_concepts:
        return ""
    want = _norm_concept_name(term_label)
    if not want:
        return ""
    norms = [(sc["id"], _norm_concept_name(sc.get("title") or "")) for sc in sub_concepts]
    for sid, n in norms:
        if n == want:
            return sid
    # Prefer the *longest* substring match so
    # "provider of general purpose ai model with systemic risk" beats
    # the looser prefix "provider of general purpose ai model".
    best = ("", -1)
    for sid, n in norms:
        if not n:
            continue
        if n in want or want in n:
            score = len(n) if n in want else len(want)
            if score > best[1]:
                best = (sid, score)
    return best[0]


def _find_json_literal(src: str, var_name: str) -> tuple[int, int] | None:
    """Return (start, end) indices of the JSON literal assigned to `const var_name`.
    Bracket-aware: handles strings containing `[`/`]`/`{`/`}`."""
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


def _row_is_redundant(row: dict) -> bool:
    """A continuation row with no own content in any jurisdiction — drops
    without changing what the user sees. These appear when the xlsx layout
    has multiple matrix rows that all spell out the same term across
    jurisdictions: every column's cell is either covered by a rowspan from
    above (rowspan == 0) or genuinely empty (no variants)."""
    if (row.get("term_label") or "").strip():
        return False
    for cell in (row.get("cells") or {}).values():
        rs = cell.get("rowspan", 1)
        variants = cell.get("variants") or []
        if rs != 0 and variants:
            return False
    return True


def _drop_orphan_continuation_rows(rows: list) -> tuple[list, int]:
    """Return (kept_rows, dropped_count). Adjusts term_rowspan and per-column
    rowspan so the DOM still merges cells that were covered before a dropped
    row was removed."""
    # A "group" starts at a row with term_rowspan > 0 (non-zero) and spans
    # as many rows as that value. We work group-by-group so we don't cross
    # concepts' first-column merges.
    dropped = 0
    out: list = []
    i = 0
    n = len(rows)
    while i < n:
        head = rows[i]
        group_size = head.get("term_rowspan") or 1
        group = rows[i : i + group_size]
        i += group_size
        # Walk the group and mark which rows to keep.
        keep_flags = []
        for idx, row in enumerate(group):
            if idx == 0:
                keep_flags.append(True)  # always keep the group head
            else:
                keep_flags.append(not _row_is_redundant(row))
        kept = [r for r, k in zip(group, keep_flags) if k]
        dropped += len(group) - len(kept)
        if not kept:
            continue
        # Recompute term_rowspan on the head and rebuild per-column rowspans
        # so rendered cells merge correctly across the new row set.
        kept[0]["term_rowspan"] = len(kept)
        for k in range(1, len(kept)):
            kept[k]["term_rowspan"] = 0
        jids = list(kept[0].get("cells", {}).keys())
        for jid in jids:
            anchor = None
            for idx, row in enumerate(kept):
                cell = (row.get("cells") or {}).get(jid) or {"rowspan": 1, "variants": []}
                variants = cell.get("variants") or []
                if variants:
                    cell["rowspan"] = 1
                    anchor = idx
                else:
                    if anchor is not None:
                        kept[anchor]["cells"][jid]["rowspan"] = (
                            kept[anchor]["cells"][jid].get("rowspan", 1) + 1
                        )
                        cell["rowspan"] = 0
                    else:
                        cell["rowspan"] = 1
                row["cells"][jid] = cell
        out.extend(kept)
    return out, dropped


def _rewrite_concepts_const(html: str) -> tuple[str, int, int]:
    """Load CONCEPTS JSON, rebuild each cluster_summary row's sub_id, drop
    orphan continuation rows, re-emit. Also blanks out `ceps_framing` so it
    doesn't duplicate the rich notes (v15 populated framing with the
    plain-text version of the first note, which then renders as a paragraph
    above the dim table — the same content the rich-notes box shows below).
    Returns (html, subid_fixed, rows_dropped)."""
    span = _find_json_literal(html, "CONCEPTS")
    if not span:
        raise SystemExit(
            "_rewrite_concepts_const: `const CONCEPTS` literal not found. "
            "The v15 output shape has changed — v16 cannot post-process it."
        )
    start, end = span
    concepts = json.loads(html[start:end])
    fixed = 0
    dropped_total = 0
    for c in concepts:
        # Drop the duplicate plain-text framing; the rich notes below the
        # table already carry this content with formatting preserved.
        if c.get("ceps_framing"):
            c["ceps_framing"] = ""
        subs = c.get("sub_concepts") or []
        cs = c.get("cluster_summary") or {}
        rows = cs.get("rows") or []
        last_sub_id = ""
        for row in rows:
            tlabel = (row.get("term_label") or "").strip()
            if tlabel:
                sid = _find_best_sub_id(tlabel, subs)
                if not sid and subs:
                    sid = subs[0]["id"]
                last_sub_id = sid
            else:
                sid = last_sub_id  # continuation: inherit
            if row.get("sub_id") != sid:
                fixed += 1
                row["sub_id"] = sid
            # Also patch the variant pills inside each cell (they carry their own copy).
            for jid, cell in (row.get("cells") or {}).items():
                for v in cell.get("variants", []):
                    if v.get("sub_id") != sid:
                        v["sub_id"] = sid
        kept_rows, dropped = _drop_orphan_continuation_rows(rows)
        dropped_total += dropped
        cs["rows"] = kept_rows
    new_blob = json.dumps(concepts, ensure_ascii=False, separators=(",", ":"))
    html = html[:start] + new_blob + html[end:]
    return html, fixed, dropped_total


# --------------------------------------------------------------------------- #
# Task 1c — Replace coverage-only shadow consts with a flat string corpus.    #
# DATA / ANALYSIS_DATA / MATRIX exist solely so the coverage test can         #
# substring-match xlsx cells. Their JSON keys ("tabId", "rowLabel", ...) are  #
# dead bytes in production. Flatten every string value into one dedup'd       #
# JSON-array blob — the coverage test already walks all                       #
# <script type="application/json"> blobs.                                     #
# --------------------------------------------------------------------------- #

def _collect_strings(obj, sink: list[str]) -> None:
    if isinstance(obj, str):
        if len(obj) > 2:
            sink.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _collect_strings(v, sink)
    elif isinstance(obj, list):
        for v in obj:
            _collect_strings(v, sink)


# --------------------------------------------------------------------------- #
# Task 3 — Clean up law-blob raw_text so the drawer doesn't render a wall of  #
# blank-line boilerplate for laws whose sections didn't parse (Colorado).     #
# --------------------------------------------------------------------------- #

_LAW_BLOB_BOILERPLATE_LINES = {
    "hide", "skip to main content", "share:", "contact us", "privacy policy",
    "ethics tutorial", "social calendar", "it login",
    "policy on member requests for csp protection", "house and senate rules",
    "for legislators  staff", "for legislators & staff",
    "schedule", "visit  learn", "visit & learn", "find my legislator",
    "watch  listen", "watch & listen", "menu", "search", "bills", "committees",
    "senate", "house", "related documents", "status", "became law",
    "introduced", "passed", "signed", "enacted",
    "colorado general assembly", "200 e colfax avenue", "denver co 80203",
    "colorado general assembly", "committees", "judiciary",
    "state civic military  veterans affairs", "state, civic, military, & veterans affairs",
    "second regular session  75th general assembly",
    "sb24205 consumer protections for artificial intelligence  colorado general assembly",
    "searchclearinput", "datasearchtargetclearbutton",
}


def _clean_law_raw_text(txt: str) -> str:
    if not txt:
        return txt
    raw_lines = txt.split("\n")
    kept: list[str] = []
    for ln in raw_lines:
        s = ln.strip()
        if not s:
            if kept and kept[-1] == "":
                continue  # collapse blank runs to a single blank
            kept.append("")
            continue
        # Drop likely-navigation lines: very short, or matching known boilerplate.
        key = re.sub(r"[^a-z&: ]+", "", s.lower()).strip()
        if key in _LAW_BLOB_BOILERPLATE_LINES:
            continue
        # Drop raw HTML/JS attribute fragments (scraping leftovers).
        if re.match(r'^[a-z\-]+(=|#)', s) and '"' in s:
            continue
        kept.append(s)
    while kept and kept[0] == "":
        kept.pop(0)
    while kept and kept[-1] == "":
        kept.pop()
    return "\n".join(kept)


_SHALL_RE = re.compile(r"\bshall\b", re.I)
_SECTION_SYM_RE = re.compile(r"§|Section\s+\d|\b\d{4,5}\.\d+\b|\b\d-\d-\d{3,}\b")


def _raw_text_is_mostly_boilerplate(txt: str) -> bool:
    """Real legislative text is dense with "shall" and section markers. If the
    raw_text has neither in proportion to its length, it's navigation scraped
    from the landing page, not bill content."""
    if not txt:
        return True
    length = len(txt)
    shall_hits = len(_SHALL_RE.findall(txt))
    sect_hits = len(_SECTION_SYM_RE.findall(txt))
    # Bills use "shall" ≥ ~1 per 700 chars, and have plenty of section anchors.
    if length >= 2000 and shall_hits < length // 1500 and sect_hits < 3:
        return True
    return False


def _clean_law_blobs(html: str) -> tuple[str, int]:
    """Rewrite each law blob's raw_text to collapse whitespace + strip boilerplate.
    Only touches blobs whose `sections` and `articles` are both empty — those are
    the ones the drawer would render as a <pre> of raw_text."""
    saved = 0

    def repl(m: "re.Match[str]") -> str:
        nonlocal saved
        head, body, tail = m.group(1), m.group(2), m.group(3)
        try:
            blob = json.loads(body)
        except json.JSONDecodeError:
            return m.group(0)
        if blob.get("articles") or blob.get("sections"):
            return m.group(0)
        rt = blob.get("raw_text")
        if not rt:
            return m.group(0)
        cleaned = _clean_law_raw_text(rt)
        # If the remaining text is still mostly navigation boilerplate
        # (Colorado bill page is the known offender), swap in a short
        # fallback message so the drawer doesn't render pages of junk.
        if _raw_text_is_mostly_boilerplate(cleaned):
            cleaned = (
                "Full law text is not embedded inline for this source. "
                "Use the official link above to read the bill as enacted."
            )
        if cleaned == rt:
            return m.group(0)
        blob["raw_text"] = cleaned
        new_body = json.dumps(blob, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        saved += len(body) - len(new_body)
        return head + new_body + tail

    html = re.sub(
        r'(<script type="application/json" id="law-blob-[^"]+">)([\s\S]*?)(</script>)',
        repl, html,
    )
    return html, saved


def _replace_shadow_consts(html: str) -> tuple[str, int]:
    names = ("DATA", "ANALYSIS_DATA", "MATRIX")
    collected: list[str] = []
    orig_len = len(html)

    for name in names:
        pat = re.compile(rf"^const {name}\s*=\s*(.+);\s*$", re.M)
        m = pat.search(html)
        if not m:
            continue
        try:
            obj = json.loads(m.group(1))
        except json.JSONDecodeError as e:
            print(f"  warn: could not parse const {name}: {e}")
            continue
        _collect_strings(obj, collected)
        html = pat.sub("", html, count=1)

    if collected:
        seen: set[str] = set()
        uniq: list[str] = []
        for s in collected:
            if s not in seen:
                seen.add(s)
                uniq.append(s)
        blob = json.dumps(uniq, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        tag = f'<script type="application/json" id="__v16_coverage__">{blob}</script>'
        html = html.replace("</body>", tag + "\n</body>", 1)

    return html, orig_len - len(html)


# --------------------------------------------------------------------------- #
# Tasks 2, 3, 4 — CSS + JS overrides injected before </body>.                 #
# --------------------------------------------------------------------------- #

def _v16_overrides() -> str:
    return r"""
<style>
/* v16 — widen concept page; drop unnecessary nowrap on dim table headers */
.concept-page{max-width:min(1760px,calc(100vw - 64px))}
.analysis-table th{white-space:normal;line-height:1.35}
.analysis-table th:first-child{min-width:100px}
.analysis-table td:first-child{white-space:normal;min-width:100px}
@media (min-width:901px){.analysis-wrap{overflow-x:visible}}
/* Explore-in-full-law button */
.drawer-action-btn.explore-law-btn{border-color:var(--accent);color:var(--accent);font-weight:500}
.drawer-action-btn.explore-law-btn:hover{background:var(--accent-l)}
/* Brief column-focus highlight after matrix-pill navigation */
.analysis-table th.v16-focus-flash{background:var(--accent-l)!important;transition:background-color .4s}
/* Compact home page — fit in one viewport at ~900px tall */
.landing{padding:32px 40px 40px!important}
.landing h1{font-size:42px;margin-bottom:12px}
.landing-sub{margin-bottom:24px}
.landing-stats{padding:12px 20px;margin-bottom:20px}
.prose-section h1.prose-title{font-size:26px;margin-bottom:10px}
.prose-section .prose-paragraph{margin-bottom:10px}
/* Collapse the notes panel when it has no content (e.g. Overview tab,
   or sub-concepts without any attached interpretative notes). */
.ceps-notes:empty{display:none}
/* Tighten the law-drawer body: raw_text from scraped pages has huge runs
   of blank lines that we collapse in JS; this also caps the vertical
   stretch of any stray empty lines. */
.drawer-verbatim pre{white-space:pre-wrap;margin:0;font-family:var(--serif);font-size:14px;line-height:1.7}
.drawer-body{padding:16px 20px}
/* Leave a little room above the sub-tab bar when scrolled into view from
   a pill click or a deep link (#sub_id in the URL). */
#sub-tabs{scroll-margin-top:20px}
/* Make the per-jurisdiction term name in dim-table headers more legible.
   v15 set it too pale (ink-s italic); legal pros read these headers. */
.analysis-table th .j-term{color:var(--ink)!important;font-weight:500;font-size:13px}
</style>
<script>
(function(){
  /* ---- Task 2: "Explore in full law" button in verbatim drawer ---- */
  function _prettyLaneLabel(jd, laneKey){
    // Lane keys like "ca-0-substantial-modification" are not in JURIS_LABELS.
    // Fall back to the parent jurisdiction + bill code so the switcher pill
    // isn't labeled literally "undefined".
    var parent = (jd && jd._parent_jid) || (laneKey ? String(laneKey).split('-')[0] : '');
    var base = (typeof JURIS_LABELS !== 'undefined' ? JURIS_LABELS[parent] : null) || parent.toUpperCase();
    var bill = (jd && (jd.bills || '')).trim();
    if (!bill && jd && jd.law && jd.law !== base) bill = jd.law;
    return bill ? (base + ' (' + bill + ')') : base;
  }

  function installExploreLawButton(){
    if (typeof window.updateDrawerContent !== 'function' || window.__v16_udc_patched) return;
    window.__v16_udc_patched = true;
    var orig = window.updateDrawerContent;
    window.updateDrawerContent = function(dim, juris, sc){
      orig(dim, juris, sc);
      // Replace any literal "undefined" labels on the jurisdiction switcher.
      try {
        var nav = document.getElementById('drawer-nav');
        if (nav && sc && sc.jurisdictions) {
          nav.querySelectorAll('button').forEach(function(b){
            if (b.textContent.trim() !== 'undefined') return;
            var m = (b.getAttribute('onclick') || '').match(/switchDrawerJuris\([^,]+,\s*'([^']+)'\)/);
            if (!m) return;
            var key = m[1];
            var jd = sc.jurisdictions[key];
            if (jd) b.textContent = _prettyLaneLabel(jd, key);
          });
        }
      } catch(e) {}
      // Add the "Explore in full law" button (Task 2).
      var bar = document.querySelector('.drawer-actions');
      if (!bar) return;
      bar.querySelectorAll('.explore-law-btn').forEach(function(b){ b.remove(); });
      var cell = dim && dim.cells && dim.cells[juris];
      var refStr = (cell && cell.reference) ? String(cell.reference).trim() : '';
      if (!refStr) return;
      var info = (typeof REF_MAP !== 'undefined') ? REF_MAP[refStr] : null;
      if (!info || !info.law){
        // Cell references are often a ;-joined list of full REF_MAP keys
        // (REF_MAP keys themselves contain commas, e.g. "EU AI Act, Article 3").
        var parts = refStr.split(/\s*;\s*/);
        for (var i = 0; i < parts.length; i++){
          var p = parts[i].trim();
          var hit = (typeof REF_MAP !== 'undefined') ? REF_MAP[p] : null;
          if (hit && hit.law){ info = hit; break; }
        }
      }
      if (!info || !info.law) return;
      var btn = document.createElement('button');
      btn.className = 'drawer-action-btn explore-law-btn';
      btn.textContent = 'Explore in full law \u2192';
      btn.addEventListener('click', function(){
        var aid = info.anchor || undefined;
        // EU AI Act uses 'article-paragraph' anchors like '3-1'; its article
        // list indexes by article number only. Every other law's anchor is a
        // section identifier that contains its own dashes (e.g. '6-1-1701').
        if (aid && info.law === 'eu-ai-act' && info.kind === 'article') {
          aid = aid.split('-')[0];
        }
        if (typeof openLawDrawerById === 'function') openLawDrawerById(info.law, aid);
      });
      bar.insertBefore(btn, bar.firstChild);
    };
  }

  /* ---- Remove the dead "Matrix options → Show sub-concepts" checkbox.
     v15 overrode renderMatrix to render from the curated cluster-summary
     sheet, so the original v14 checkbox is no longer wired to anything. ---- */
  function removeDeadMatrixOptions(){
    var cb = document.getElementById('show-subconcepts');
    if (!cb) return;
    var section = cb.closest('.sidebar-section');
    if (section && section.parentNode) section.parentNode.removeChild(section);
  }

  /* ---- Task 4: Matrix pill click → concept page + matching sub-tab ---- */
  function _scrollToSubTabs(){
    // Scroll the sub-tab bar into view (with scroll-margin-top from CSS)
    // instead of landing at the very top of the page. Runs on the next
    // frame so v15's go() scrollTo(0,0) runs first.
    requestAnimationFrame(function(){
      var el = document.getElementById('sub-tabs');
      if (el) el.scrollIntoView({block:'start', behavior:'smooth'});
    });
  }

  function _resolveSubIdToConcept(subId){
    if (typeof CONCEPTS === 'undefined' || !subId) return null;
    var c = CONCEPTS.find(function(cc){
      return (cc.sub_concepts || []).some(function(s){ return s.id === subId; });
    });
    if (!c) return null;
    var i = c.sub_concepts.findIndex(function(s){ return s.id === subId; });
    return {concept: c, subIdx: i >= 0 ? i : 0};
  }

  function installVariantPillNav(){
    // Replace v15's drawer-opening pill handler on the concept Overview tab.
    window.__openVariantDrawer = function(subId, jid, bill){
      try {
        var resolved = _resolveSubIdToConcept(subId);
        if (!resolved) return;
        if (typeof state !== 'undefined') state.focusJid = jid || '';
        if (typeof go === 'function') go('concept', resolved.concept.id, resolved.subIdx);
        if (location.hash !== '#' + subId) {
          try { history.replaceState(null, '', '#' + subId); } catch(e) {}
        }
        _scrollToSubTabs();
      } catch(e) { console.error('v16 pill nav:', e); }
    };

    // Also rewire the Concepts-landing matrix (window.renderMatrix from v15):
    // pills there currently call go('concept', c.id) without a sub-tab. Wrap
    // renderMatrix so after it renders, each cell's pill is re-pointed to the
    // matching sub-concept + jurisdiction.
    if (typeof window.renderMatrix !== 'function' || window.__v16_rm_patched) return;
    window.__v16_rm_patched = true;
    var origRM = window.renderMatrix;
    window.renderMatrix = function(filtered, activeJuris){
      origRM(filtered, activeJuris);
      try {
        if (typeof JURIS_ORDER === 'undefined') return;
        var view = document.getElementById('matrix-view');
        if (!view) return;
        var tbody = view.querySelector('tbody');
        if (!tbody) return;
        var allJ = (activeJuris && activeJuris.length)
          ? JURIS_ORDER.filter(function(j){ return activeJuris.includes(j); })
          : JURIS_ORDER.slice();
        var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));
        // Walk concept-by-concept; v15's renderMatrix emits one <tr> per
        // cluster_summary row (or a single placeholder row).
        var rIdx = 0;
        filtered.forEach(function(c){
          var cs = c.cluster_summary;
          var conceptRows = (cs && cs.rows && cs.rows.length) ? cs.rows
                           : [{sub_id: (c.sub_concepts[0] || {}).id || '', cells: {}}];
          conceptRows.forEach(function(row){
            var tr = rows[rIdx++];
            if (!tr) return;
            var tds = tr.querySelectorAll('td');
            // First <td> on family-first rows is the concept-name cell (rowspan).
            var dataCells = [];
            for (var i = 0; i < tds.length; i++){
              var td = tds[i];
              if (td.classList && td.classList.contains('matrix-family-cell')) continue;
              dataCells.push(td);
            }
            // Match each visible data cell to its jurisdiction column,
            // respecting rowspan=0 skips in row.cells.
            var jIdx = 0;
            allJ.forEach(function(j){
              var cell = row.cells && row.cells[j];
              if (cell && cell.rowspan === 0) return; // covered by previous row
              var td = dataCells[jIdx++];
              if (!td) return;
              var pill = td.querySelector('.j-pill');
              if (!pill || !cell || !(cell.variants || []).length) return;
              var v = cell.variants[0];
              pill.setAttribute('onclick', '');
              pill.addEventListener('click', (function(subId, jj, bill){
                return function(ev){
                  ev.preventDefault();
                  window.__openVariantDrawer(subId, jj, bill);
                };
              })(row.sub_id, j, v.bill || ''));
            });
          });
        });
      } catch(e) { console.error('v16 renderMatrix wrap:', e); }
    };
  }

  /* ---- Task 4 polish: scroll + flash the clicked jurisdiction column ---- */
  function installFocusJurisFlash(){
    if (typeof window.renderAnalysisTable !== 'function' || window.__v16_rat_patched) return;
    window.__v16_rat_patched = true;
    var orig = window.renderAnalysisTable;
    window.renderAnalysisTable = function(){
      orig.apply(this, arguments);
      try {
        if (typeof state === 'undefined' || !state.focusJid) return;
        var jid = state.focusJid;
        state.focusJid = '';
        if (typeof saveState === 'function') saveState();
        var thead = document.getElementById('analysis-thead');
        if (!thead) return;
        var ths = Array.prototype.slice.call(thead.querySelectorAll('th'));
        var target = ths.find(function(th){
          return (th.className || '').indexOf('th-' + jid) !== -1;
        });
        if (!target) return;
        if (target.scrollIntoView) {
          target.scrollIntoView({inline:'center', block:'nearest', behavior:'smooth'});
        }
        target.classList.add('v16-focus-flash');
        setTimeout(function(){ target.classList.remove('v16-focus-flash'); }, 1200);
      } catch(e){}
    };
  }

  /* ---- URL hash → sub-concept deep link (shareable links) ---- */
  function _applyHashRoute(){
    var raw = (location.hash || '').replace(/^#/, '').trim();
    if (!raw) return false;
    var resolved = _resolveSubIdToConcept(raw);
    if (!resolved) return false;
    if (typeof go === 'function') go('concept', resolved.concept.id, resolved.subIdx);
    _scrollToSubTabs();
    return true;
  }
  function installHashRouter(){
    if (!_applyHashRoute()) return;
    window.addEventListener('hashchange', _applyHashRoute);
  }

  /* Notes scoping is done at build time via regex patch of the v15
     IIFE — see _patch_notes_scope() in build_v16.py. No JS wrapper
     needed here (renderRichNotes lives inside the v15 IIFE and isn't
     on window, so we can't wrap it from outside). */
  function installNotesOnSubTabsOnly(){ /* handled at build time */ }

  /* ---- Warn the user when a law anchor doesn't exist in its parsed blob
     (e.g. an older scrape of TX HB 149 only captured one section).
     Wrap openLawDrawerById to detect the silent items[0] fallback and
     prepend a banner to #drawer-verbatim.

     `lawBlob` is IIFE-scoped so we re-parse the inline JSON blob
     directly from its <script type="application/json" id="law-blob-X">. ---- */
  function _v16LookupBlob(lawId){
    var el = document.getElementById('law-blob-' + lawId);
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch(e) { return null; }
  }
  function installMissingAnchorBanner(){
    if (typeof window.openLawDrawerById !== 'function' || window.__v16_oldb_patched) return;
    window.__v16_oldb_patched = true;
    var orig = window.openLawDrawerById;
    window.openLawDrawerById = function(lawId, articleId){
      // Decide up-front whether we expect to hit a real section.
      var blob = _v16LookupBlob(lawId);
      var items = (blob && (blob.articles || blob.sections)) || [];
      var missed = !!articleId && items.length > 0 && !items.find(function(x){
        return String(x.id) === String(articleId);
      });
      orig.call(this, lawId, articleId);
      if (!missed) return;
      try {
        var body = document.getElementById('drawer-verbatim');
        if (!body) return;
        // Remove any previous banner from an earlier call.
        Array.prototype.forEach.call(
          body.querySelectorAll('.v16-missing-anchor'),
          function(n){ n.parentNode.removeChild(n); }
        );
        var banner = document.createElement('div');
        banner.className = 'v16-missing-anchor';
        banner.style.cssText = 'margin:0 0 14px;padding:10px 14px;border-left:3px solid #c08a00;background:#fff8e6;font-size:13px;color:#5a4200;border-radius:3px;';
        banner.textContent = 'Section "' + articleId + '" is not separately parsed in this law blob. Showing the full law text below — use your browser\u2019s find (\u2318F / Ctrl+F) to jump to the section.';
        body.insertBefore(banner, body.firstChild);
      } catch(e){}
    };
  }

  function init(){
    // Install all renderConceptPage / renderAnalysisTable / openLawDrawerById
    // wrappers BEFORE invoking the hash router — otherwise the first render
    // triggered by a deep-link (e.g. ...#provider-of-general-purpose-ai-models)
    // uses the un-wrapped renderer and leaves the notes panel blank until
    // the user clicks something to force a re-render.
    installExploreLawButton();
    installVariantPillNav();
    installFocusJurisFlash();
    installNotesOnSubTabsOnly();
    installMissingAnchorBanner();
    removeDeadMatrixOptions();
    installHashRouter();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
</script>
"""


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #

def main() -> None:
    _install_runs_merge_patch()

    tmp_out = HERE / ".v16_tmp.html"
    orig_out = build_v15.HTML_OUT
    build_v15.HTML_OUT = tmp_out
    try:
        build_v15.main()
    finally:
        build_v15.HTML_OUT = orig_out

    html = tmp_out.read_text(encoding="utf-8")
    tmp_out.unlink(missing_ok=True)

    stage_size = len(html)
    print(f"\n[v16 post-processing]")
    print(f"  intermediate size:   {stage_size:,} bytes")

    html, fixed_subs, dropped_rows = _rewrite_concepts_const(html)
    print(f"  sub_id remappings:   {fixed_subs} rows fixed")
    print(f"  orphan rows dropped: {dropped_rows}")

    # Patch the v15-era renderConceptPage so the notes panel renders the
    # CURRENT sub_concept's notes on a sub-tab (c.sub_concepts[idx]),
    # rather than the family concept's (now-empty) notes pool. Keep the
    # Overview branch on the family pool so it still honours
    # c.ceps_notes_rich = [] → empty → hidden by the :empty CSS rule.
    old_line = "      renderAnalysisTable();\n      notesEl.innerHTML = renderRichNotes(c);\n    }"
    new_line = "      renderAnalysisTable();\n      notesEl.innerHTML = renderRichNotes((c.sub_concepts && c.sub_concepts[idx]) || c);\n    }"
    if old_line not in html:
        raise SystemExit(
            "notes-scoping patch: source line not found in v15 IIFE. The "
            "regex anchor has drifted — update build_v16.py's `old_line` to "
            "match the current v15 renderConceptPage. Build aborted to avoid "
            "shipping a broken notes panel."
        )
    html = html.replace(old_line, new_line, 1)
    print("  notes-scoping patch:  applied")

    html, law_clean_saved = _clean_law_blobs(html)
    after_law = len(html)
    print(f"  after law cleanup:   {after_law:,} bytes  (raw_text trim: -{law_clean_saved:,})")

    html, shadow_saved = _replace_shadow_consts(html)
    after_shadow = len(html)
    print(f"  after shadow-dedupe: {after_shadow:,} bytes  (shadow: -{shadow_saved:,})")

    html = _minify_style_blocks(html)
    after_min = len(html)
    print(f"  after CSS minify:    {after_min:,} bytes  ({after_min - after_shadow:+,})")

    if "</body>" not in html:
        raise SystemExit(
            "_v16_overrides: no `</body>` tag found — cannot inject v16 JS."
        )
    html = html.replace("</body>", _v16_overrides() + "\n</body>", 1)
    final = len(html)
    print(f"  after v16 overrides: {final:,} bytes ({final - after_min:+,})")

    HTML_V16.write_text(html, encoding="utf-8")

    v15_path = HERE / "digital_lexicon_v15.html"
    v14_path = HERE / "digital_lexicon_v14.html"
    v15_size = v15_path.stat().st_size if v15_path.exists() else 0
    v14_size = v14_path.stat().st_size if v14_path.exists() else 0
    print(f"\nWrote {HTML_V16}  ({final:,} bytes)")
    if v15_size:
        print(f"  vs v15: {final - v15_size:+,} bytes ({(final - v15_size) / v15_size * 100:+.1f}%)")
    if v14_size:
        print(f"  vs v14: {final - v14_size:+,} bytes ({(final - v14_size) / v14_size * 100:+.1f}%)")

    # Run correspondence + rendering tests. A regression in any of them
    # fails the build.
    import subprocess, sys
    for label, fname in [
        ("correspondence tests", "test_lexicon_correspondence.py"),
        ("rendering tests (headless)", "test_lexicon_rendering.py"),
    ]:
        path = HERE / fname
        if not path.exists():
            continue
        print(f"\n[{label}]")
        rc = subprocess.run([sys.executable, str(path)], cwd=HERE).returncode
        if rc != 0:
            raise SystemExit(
                f"{label} failed (rc={rc}). Build artifact is still "
                f"written, but review the failures before shipping."
            )


if __name__ == "__main__":
    main()
