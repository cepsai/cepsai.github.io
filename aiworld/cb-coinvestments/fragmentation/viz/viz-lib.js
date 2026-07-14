/* Shared chart helpers for the fragmentation viz set.
   file://-safe, vanilla JS + SVG, no external deps. Reads window.METRICS
   (loaded from ../data/data.js). Charts scale to their container width. */
(function (global) {
  const NS = 'http://www.w3.org/2000/svg';
  const M = global.METRICS;

  // ---- URL-driven chrome hiding: ?buttons=0&source=0&legend=0&logo=0&chrome=0 (see body.hide-* in viz.css)
  const _q = new URLSearchParams(location.search);
  [['buttons', 'hide-buttons'], ['source', 'hide-source'], ['legend', 'hide-legend'], ['logo', 'hide-logo'], ['chrome', 'hide-chrome']]
    .forEach(([p, c]) => { const v = (_q.get(p) || '').toLowerCase(); if (v === '0' || v === 'false' || v === 'no') document.body.classList.add(c); });

  // ---- tooltip (create once)
  let tip = document.getElementById('tip');
  if (!tip) { tip = document.createElement('div'); tip.className = 'tip'; tip.id = 'tip'; document.body.appendChild(tip); }
  function showTip(html, ev) { tip.innerHTML = html; tip.style.opacity = 1; moveTip(ev); }
  function moveTip(ev) { let x = ev.clientX + 14, y = ev.clientY + 14; if (x > window.innerWidth - 270) x = window.innerWidth - 270; tip.style.left = x + 'px'; tip.style.top = y + 'px'; }
  function hideTip() { tip.style.opacity = 0; }
  function hoverable(node, html) { node.addEventListener('mousemove', e => showTip(html, e)); node.addEventListener('mouseleave', hideTip); }

  // ---- formatting
  const fmtPct = v => (v * 100).toFixed(0) + '%';
  const fmtPct1 = v => (v * 100).toFixed(1) + '%';
  const money = v => { const a = Math.abs(v);
    if (a >= 1e9) return '$' + (v / 1e9).toFixed(1) + 'B';
    if (a >= 1e6) return '$' + (v / 1e6).toFixed(0) + 'M';
    if (a >= 1e3) return '$' + (v / 1e3).toFixed(0) + 'K'; return '$' + v.toFixed(0); };

  // ---- svg primitives
  function el(tag, attrs, txt) { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (txt != null) e.textContent = txt; return e; }
  function svg(w, h) { const s = el('svg', { viewBox: `0 0 ${w} ${h}`, preserveAspectRatio: 'xMidYMid meet' }); return s; }

  // ---- line chart (multi-series, x=year, y=share 0..1)
  function lineChart(id, seriesList, opts) {
    opts = opts || {};
    const box = document.getElementById(id); box.innerHTML = '';
    const W = opts.W || 520, H = opts.H || 250, pad = { l: 44, r: 14, t: 14, b: 28 };
    const s = svg(W, H);
    const allx = seriesList.flatMap(se => se.pts.map(p => p.x));
    const xmin = Math.min(...allx), xmax = Math.max(...allx);
    const ymax = opts.ymax || Math.max(0.01, ...seriesList.flatMap(se => se.pts.map(p => p.y))) * 1.12;
    const X = x => pad.l + (xmax === xmin ? 0.5 : (x - xmin) / (xmax - xmin)) * (W - pad.l - pad.r);
    const Y = y => H - pad.b - (y / ymax) * (H - pad.t - pad.b);
    const ticks = opts.yticks || 5;
    for (let i = 0; i <= ticks; i++) { const yv = ymax * i / ticks, yy = Y(yv);
      s.appendChild(el('line', { x1: pad.l, y1: yy, x2: W - pad.r, y2: yy, class: 'gl' }));
      s.appendChild(el('text', { x: pad.l - 6, y: yy + 3, 'text-anchor': 'end', class: 'axis' }, fmtPct(yv))); }
    const step = (xmax - xmin > 12 ? 3 : (xmax - xmin > 6 ? 2 : 1));
    for (let x = xmin; x <= xmax; x += step) {
      s.appendChild(el('text', { x: X(x), y: H - 8, 'text-anchor': 'middle', class: 'axis' }, "'" + String(x).slice(2))); }
    const loN = opts.loN || 0;
    seriesList.forEach(se => {
      let d = ''; se.pts.forEach((p, i) => { d += (i ? 'L' : 'M') + X(p.x) + ' ' + Y(p.y); });
      s.appendChild(el('path', { d, fill: 'none', stroke: se.color, 'stroke-width': opts.thin ? 1.8 : 2.4, 'stroke-linejoin': 'round' }));
      se.pts.forEach(p => {
        const lo = loN && p.n != null && p.n < loN;              // low-data year → hollow marker
        const r = opts.thin ? 2.6 : 3.4;
        const c = lo
          ? el('circle', { cx: X(p.x), cy: Y(p.y), r, fill: '#fff', stroke: se.color, 'stroke-width': 1.6 })
          : el('circle', { cx: X(p.x), cy: Y(p.y), r, fill: se.color });
        hoverable(c, `<b>${se.label}</b> · ${p.x}<br><span class="d">${opts.tipLabel || 'Share'}:</span> ${fmtPct1(p.y)}`
          + (p.n != null ? `<br><span class="d">rounds:</span> ${p.n.toLocaleString()}` + (lo ? ' <span class="d">(low data)</span>' : '') : ''));
        s.appendChild(c); });
    });
    box.appendChild(s);
  }

  // ---- sankey (weight = 'rounds' | 'usd'); node sets/colors/labels overridable via opts
  function sankey(id, links, opts) {
    opts = opts || {}; const weight = opts.weight || 'rounds';
    const box = document.getElementById(id); box.innerHTML = '';
    const W = 460, H = 380, nodeW = 15, padY = 34;
    const s = svg(W, H);
    const srcNames = opts.srcNames || ['Single-jurisdiction syndicate', 'Multi-jurisdiction syndicate'];
    const tgtNames = opts.tgtNames || ['Invests domestically', 'Invests cross-border'];
    const val = l => l[weight];
    const total = links.reduce((a, l) => a + val(l), 0) || 1;
    const gap = 16;
    function colTotals(key) { const m = {}; links.forEach(l => { m[l[key]] = (m[l[key]] || 0) + val(l); }); return m; }
    const srcTot = colTotals('source'), tgtTot = colTotals('target');
    const nGaps = names => Math.max(names.filter(n => srcTot[n] || tgtTot[n]).length - 1, 1);
    const availH = H - padY * 2 - gap * Math.max(nGaps(srcNames), nGaps(tgtNames));
    function layout(names, tot) { let y = padY; const pos = {}; names.forEach(n => { const h = (tot[n] || 0) / total * availH; pos[n] = { y0: y, h }; y += h + (h ? gap : 0); }); return pos; }
    const L = layout(srcNames, srcTot), R = layout(tgtNames, tgtTot);
    const colFor = opts.colorFor || (t => t === 'Invests domestically' ? 'var(--dom)' : 'var(--ib)');
    const srcColor = opts.srcColor || (() => '#3d4753');
    const lbl = opts.label || (n => n.replace(' syndicate', '').replace('Invests ', ''));
    const srcOff = {}, tgtOff = {};
    links.sort((a, b) => srcNames.indexOf(a.source) - srcNames.indexOf(b.source) || tgtNames.indexOf(a.target) - tgtNames.indexOf(b.target));
    links.forEach(l => {
      const h = val(l) / total * availH;
      const sy = (srcOff[l.source] = (srcOff[l.source] || L[l.source].y0)) + 0;
      const ty = (tgtOff[l.target] = (tgtOff[l.target] || R[l.target].y0)) + 0;
      const x0 = nodeW, x1 = W - nodeW, xm = (x0 + x1) / 2;
      const y0a = sy, y0b = sy + h, y1a = ty, y1b = ty + h;
      const d = `M${x0} ${y0a} C${xm} ${y0a} ${xm} ${y1a} ${x1} ${y1a} L${x1} ${y1b} C${xm} ${y1b} ${xm} ${y0b} ${x0} ${y0b} Z`;
      const p = el('path', { d, fill: opts.linkColor ? opts.linkColor(l) : colFor(l.target), opacity: .42 });
      hoverable(p, `<b>${l.source}</b><br>→ ${l.target}<br><span class="d">Rounds:</span> ${l.rounds.toLocaleString()} (${fmtPct1(l.rounds / links.reduce((a, x) => a + x.rounds, 0))})<br><span class="d">$:</span> ${money(l.usd)} (${fmtPct1(l.usd / links.reduce((a, x) => a + x.usd, 0))})`);
      p.addEventListener('mouseenter', () => p.setAttribute('opacity', .68));
      p.addEventListener('mouseleave', () => p.setAttribute('opacity', .42));
      s.appendChild(p);
      // flow-share labels: left = share of the source node's outflow, right = share of the target node's inflow
      const flowLabel = (x, y, anchor, txt) => { const t = el('text', { x, y, 'text-anchor': anchor, 'font-weight': 600, fill: 'var(--ink)' }, txt); t.style.fontSize = '10.5px'; s.appendChild(t); };
      const nudge = (y, mid, lo, hi) => { if (Math.abs(y - mid) < 30) y = mid + (y >= mid ? 30 : -30); return Math.max(lo, Math.min(hi, y)); };
      if (h > 13) {
        const lMid = L[l.source].y0 + L[l.source].h / 2 + 4, rMid = R[l.target].y0 + R[l.target].h / 2 + 4;
        flowLabel(nodeW + 6, nudge(y0a + h / 2 + 3.5, lMid, y0a + 10, y0b - 3), 'start', fmtPct(val(l) / srcTot[l.source]));
        // with a single source node every target's inflow share is 100% — skip the noise
        if (!opts.noInflowLabels) flowLabel(W - nodeW - 6, nudge(y1a + h / 2 + 3.5, rMid, y1a + 10, y1b - 3), 'end', fmtPct(val(l) / tgtTot[l.target]));
      }
      srcOff[l.source] = sy + h; tgtOff[l.target] = ty + h;
    });
    const unit = weight === 'usd' ? ' of $' : ' of rounds';
    // node share shown outside the chart (above for the top node, below for the bottom one) with a leader line to the node
    function nodeShare(o, top, cx, tx, anchor, pct) {
      const t = el('text', { x: tx, y: top ? 12 : H - 3, 'text-anchor': anchor, class: 'axis', 'font-weight': 700, fill: 'var(--ink)' }, pct + unit);
      t.style.fontSize = '11px'; s.appendChild(t);
      const y1 = top ? 16 : o.y0 + o.h + 2, y2 = top ? o.y0 - 2 : H - 14;
      s.appendChild(el('line', { x1: cx, y1, x2: cx, y2, stroke: 'var(--muted)', 'stroke-width': 1 }));
    }
    const srcAct = srcNames.filter(n => L[n].h), tgtAct = tgtNames.filter(n => R[n].h);
    srcNames.forEach(n => { const o = L[n]; if (!o.h) return;
      const ai = srcAct.indexOf(n), pct = fmtPct(srcTot[n] / total);
      s.appendChild(el('rect', { x: 0, y: o.y0, width: nodeW, height: o.h, fill: srcColor(n), rx: 2 }));
      const t = el('text', { x: nodeW + 6, y: o.y0 + o.h / 2 + 4, 'font-weight': 600, fill: 'var(--ink)' });
      t.textContent = lbl(n); t.style.fontSize = '10.5px'; s.appendChild(t);
      if (ai === 0 || ai === srcAct.length - 1) nodeShare(o, ai === 0, nodeW / 2, 0, 'start', pct);
      else { const ts = el('tspan', { fill: 'var(--muted)' }, ' ' + pct); t.appendChild(ts); } });
    tgtNames.forEach(n => { const o = R[n]; if (!o.h) return;
      const ai = tgtAct.indexOf(n), pct = fmtPct(tgtTot[n] / total);
      s.appendChild(el('rect', { x: W - nodeW, y: o.y0, width: nodeW, height: o.h, fill: colFor(n), rx: 2 }));
      const t = el('text', { x: W - nodeW - 6, y: o.y0 + o.h / 2 + 4, 'text-anchor': 'end', 'font-weight': 600, fill: 'var(--ink)' });
      t.textContent = lbl(n); t.style.fontSize = '10.5px'; s.appendChild(t);
      if (ai === 0 || ai === tgtAct.length - 1) nodeShare(o, ai === 0, W - nodeW / 2, W, 'end', pct);
      else { const ts = el('tspan', { fill: 'var(--muted)' }, pct + ' '); t.insertBefore(ts, t.firstChild); } });
    box.appendChild(s);
  }

  // ---- grouped bars (categories x series)
  function groupedBar(id, cats, series, opts) {
    opts = opts || {};
    const box = document.getElementById(id); box.innerHTML = '';
    const W = 760, H = 290, pad = { l: 44, r: 12, t: 12, b: 56 };
    const s = svg(W, H);
    const ymax = Math.max(0.01, ...series.flatMap(se => se.values)) * 1.12;
    const iw = (W - pad.l - pad.r) / cats.length, bw = Math.min(26, iw / 3);
    const Y = y => H - pad.b - (y / ymax) * (H - pad.t - pad.b);
    for (let i = 0; i <= 4; i++) { const yv = ymax * i / 4, yy = Y(yv);
      s.appendChild(el('line', { x1: pad.l, y1: yy, x2: W - pad.r, y2: yy, class: 'gl' }));
      s.appendChild(el('text', { x: pad.l - 6, y: yy + 3, 'text-anchor': 'end', class: 'axis' }, fmtPct(yv))); }
    cats.forEach((c, i) => {
      const cx = pad.l + iw * i + iw / 2;
      series.forEach((se, j) => {
        const v = se.values[i]; const bx = cx - bw - 1 + j * (bw + 2);
        const h = (v / ymax) * (H - pad.t - pad.b);
        const rect = el('rect', { x: bx, y: H - pad.b - h, width: bw, height: h, fill: se.color, rx: 2 });
        hoverable(rect, `<b>${se.label} — ${c}</b><br><span class="d">${opts.tipLabel || 'Share'}:</span> ${fmtPct1(v)}`);
        s.appendChild(rect);
      });
      const t = el('text', { x: cx, y: H - pad.b + 16, 'text-anchor': 'end', class: 'axis', transform: `rotate(-32 ${cx} ${H - pad.b + 16})` }, c);
      t.style.fontSize = '11px'; s.appendChild(t);
    });
    box.appendChild(s);
  }

  // ---- composition stacked bars (rows: [label, colorKey('us'|'eu'), summaryObj])
  function compositionBars(id, rows) {
    const box = document.getElementById(id); box.innerHTML = '';
    const W = 760, H = 150, pad = { l: 90, r: 80, t: 10, b: 10 }, bh = 42, gap = 26;
    const s = svg(W, H);
    const bw = W - pad.l - pad.r;
    rows.forEach((r, i) => {
      const d = r[2], y = pad.t + i * (bh + gap);
      const segs = [['Domestic', d.dom_share_usd, 'var(--dom)'], ['Internal cross-border', d.ib_share_usd, 'var(--ib)'], ['International', d.intl_share_usd, 'var(--intl)']];
      let x = pad.l;
      s.appendChild(el('text', { x: pad.l - 10, y: y + bh / 2 + 5, 'text-anchor': 'end', 'font-weight': 700, fill: r[1] === 'us' ? 'var(--us)' : 'var(--eu)' }, r[0]));
      segs.forEach(sg => { const w = sg[1] * bw; if (w <= 0) return;
        const rect = el('rect', { x, y, width: w, height: bh, fill: sg[2] });
        hoverable(rect, `<b>${r[0]} — ${sg[0]}</b><br>${fmtPct1(sg[1])} of funding $`);
        s.appendChild(rect);
        if (w > 44) s.appendChild(el('text', { x: x + w / 2, y: y + bh / 2 + 5, 'text-anchor': 'middle', fill: '#fff', 'font-weight': 700, 'font-size': '13px' }, fmtPct(sg[1])));
        x += w; });
    });
    box.appendChild(s);
  }

  // ---- segmented-control wiring
  function seg(id, onPick) {
    const node = document.getElementById(id); if (!node) return;
    node.addEventListener('click', e => {
      const b = e.target.closest('button'); if (!b) return;
      [...node.children].forEach(c => c.classList.remove('active')); b.classList.add('active');
      onPick(b.dataset[Object.keys(b.dataset)[0]]);
    });
  }

  // ---- color helpers
  function hex2rgb(h) { h = h.replace('#', ''); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)); }
  function lerpColor(c1, c2, t) { const a = hex2rgb(c1), b = hex2rgb(c2); return 'rgb(' + a.map((v, i) => Math.round(v + (b[i] - v) * t)).join(',') + ')'; }

  // ---- chord diagram (co-investment among a set of jurisdictions)
  function chord(id, links, nodes, opts) {
    opts = opts || {}; const wf = opts.weight || 'rounds';
    const box = document.getElementById(id); box.innerHTML = '';
    const S = new Set(nodes);
    const L = links.filter(l => S.has(l.a) && S.has(l.b) && l[wf] > 0);
    const tot = {}; nodes.forEach(n => tot[n] = 0);
    L.forEach(l => { tot[l.a] += l[wf]; tot[l.b] += l[wf]; });
    const ns = nodes.filter(n => tot[n] > 0);
    const grand = ns.reduce((a, n) => a + tot[n], 0) || 1;
    const W = 540, H = 540, cx = W / 2, cy = H / 2, R = 190;
    const s = svg(W, H);
    const gap = 0.03, avail = 2 * Math.PI - gap * ns.length;
    const span = {}; let ang = -Math.PI / 2;
    ns.forEach(n => { const a0 = ang, a1 = ang + (tot[n] / grand) * avail; span[n] = [a0, a1]; ang = a1 + gap; });
    // allocate a sub-arc for each link at each of its endpoints
    const linkArc = {};
    ns.forEach(n => {
      let c = span[n][0];
      const mine = L.map((l, i) => ({ l, i })).filter(o => o.l.a === n || o.l.b === n);
      mine.sort((x, y) => { const ox = x.l.a === n ? x.l.b : x.l.a, oy = y.l.a === n ? y.l.b : y.l.a; return ns.indexOf(ox) - ns.indexOf(oy); });
      mine.forEach(o => { const w = (o.l[wf] / grand) * avail; linkArc[o.i + '@' + n] = [c, c + w]; c += w; });
    });
    const P = (a, r) => [cx + r * Math.cos(a), cy + r * Math.sin(a)];
    const arcPts = (a0, a1, r) => { const st = Math.max(2, Math.ceil(Math.abs(a1 - a0) / 0.15)), out = []; for (let i = 0; i <= st; i++) out.push(P(a0 + (a1 - a0) * i / st, r)); return out; };
    const totRounds = L.reduce((a, l) => a + l.rounds, 0), totUsd = L.reduce((a, l) => a + l.usd, 0);
    // ribbons
    L.forEach((l, i) => {
      const aA = linkArc[i + '@' + l.a], aB = linkArc[i + '@' + l.b];
      if (!aA || !aB) return;
      const A = arcPts(aA[0], aA[1], R), B = arcPts(aB[1], aB[0], R);
      let d = 'M' + A[0][0].toFixed(1) + ' ' + A[0][1].toFixed(1);
      A.slice(1).forEach(p => d += 'L' + p[0].toFixed(1) + ' ' + p[1].toFixed(1));
      d += 'Q' + cx + ' ' + cy + ' ' + B[0][0].toFixed(1) + ' ' + B[0][1].toFixed(1);
      B.slice(1).forEach(p => d += 'L' + p[0].toFixed(1) + ' ' + p[1].toFixed(1));
      d += 'Q' + cx + ' ' + cy + ' ' + A[0][0].toFixed(1) + ' ' + A[0][1].toFixed(1) + 'Z';
      const p = el('path', { d, fill: 'var(--ib)', opacity: .32, stroke: 'none' });
      hoverable(p, `<b>${l.a} ↔ ${l.b}</b><br><span class="d">Co-invested rounds:</span> ${l.rounds.toLocaleString()} (${fmtPct1(l.rounds / totRounds)})<br><span class="d">$:</span> ${money(l.usd)}`);
      p.addEventListener('mouseenter', () => p.setAttribute('opacity', .7));
      p.addEventListener('mouseleave', () => p.setAttribute('opacity', .32));
      s.appendChild(p);
    });
    // node arcs + labels
    ns.forEach(n => {
      const [a0, a1] = span[n], pts = arcPts(a0, a1, R);
      let d = 'M' + pts[0][0].toFixed(1) + ' ' + pts[0][1].toFixed(1);
      pts.slice(1).forEach(p => d += 'L' + p[0].toFixed(1) + ' ' + p[1].toFixed(1));
      s.appendChild(el('path', { d, fill: 'none', stroke: '#3d4753', 'stroke-width': 9, 'stroke-linecap': 'butt' }));
      const mid = (a0 + a1) / 2, lp = P(mid, R + 16), right = Math.cos(mid) >= 0;
      const t = el('text', { x: lp[0].toFixed(1), y: lp[1].toFixed(1), 'text-anchor': right ? 'start' : 'end', 'dominant-baseline': 'middle', fill: 'var(--ink)' });
      t.textContent = n.length > 16 ? n.slice(0, 15) + '…' : n; t.style.fontSize = '12px'; t.style.fontWeight = 600;
      s.appendChild(t);
    });
    box.appendChild(s);
  }

  // ---- Lorenz curves + Gini (concentration across jurisdictions)
  function lorenz(id, seriesList, opts) {
    opts = opts || {};
    const box = document.getElementById(id); box.innerHTML = '';
    const W = 520, H = 460, pad = { l: 52, r: 18, t: 16, b: 44 };
    const s = svg(W, H);
    const X = x => pad.l + x * (W - pad.l - pad.r);
    const Y = y => H - pad.b - y * (H - pad.t - pad.b);
    for (let k = 0; k <= 4; k++) {
      const yy = Y(k / 4), xx = X(k / 4);
      s.appendChild(el('line', { x1: pad.l, y1: yy, x2: W - pad.r, y2: yy, class: 'gl' }));
      s.appendChild(el('text', { x: pad.l - 8, y: yy + 3, 'text-anchor': 'end', class: 'axis' }, (k * 25) + '%'));
      s.appendChild(el('text', { x: xx, y: H - pad.b + 16, 'text-anchor': 'middle', class: 'axis' }, (k * 25) + '%'));
    }
    // equality diagonal
    s.appendChild(el('line', { x1: X(0), y1: Y(0), x2: X(1), y2: Y(1), stroke: '#b6bfca', 'stroke-width': 1.4, 'stroke-dasharray': '5 4' }));
    s.appendChild(el('text', { x: (X(0) + 8), y: (Y(0) - 8), class: 'axis' }, 'jurisdictions →'));
    const ginis = [];
    seriesList.forEach(se => {
      const v = se.values.filter(x => x > 0).slice().sort((a, b) => a - b);
      const n = v.length, sum = v.reduce((a, b) => a + b, 0) || 1;
      const pts = [[0, 0]]; let c = 0;
      v.forEach((x, i) => { c += x; pts.push([(i + 1) / n, c / sum]); });
      // Gini via trapezoid area under Lorenz
      let area = 0; for (let i = 1; i < pts.length; i++) area += (pts[i][0] - pts[i - 1][0]) * (pts[i][1] + pts[i - 1][1]) / 2;
      const gini = 1 - 2 * area; ginis.push({ label: se.label, gini, color: se.color });
      let d = ''; pts.forEach((p, i) => d += (i ? 'L' : 'M') + X(p[0]).toFixed(1) + ' ' + Y(p[1]).toFixed(1));
      s.appendChild(el('path', { d, fill: 'none', stroke: se.color, 'stroke-width': 2.6, 'stroke-linejoin': 'round' }));
      // hoverable dots (every ~10%)
      pts.forEach((p, i) => { if (i % Math.max(1, Math.round(n / 10)) === 0 || i === pts.length - 1) {
        const dot = el('circle', { cx: X(p[0]), cy: Y(p[1]), r: 2.6, fill: se.color });
        hoverable(dot, `<b>${se.label}</b><br><span class="d">top ${fmtPct(p[0])} of jurisdictions</span><br>hold ${fmtPct1(p[1])} of ${opts.unit || 'total'}`);
        s.appendChild(dot); } });
    });
    // gini annotations
    ginis.forEach((g, i) => {
      const gy = pad.t + 6 + i * 20;
      s.appendChild(el('rect', { x: W - pad.r - 150, y: gy - 10, width: 12, height: 12, rx: 3, fill: g.color }));
      s.appendChild(el('text', { x: W - pad.r - 132, y: gy, fill: 'var(--ink)', 'font-weight': 700 }, `${g.label}: Gini ${g.gini.toFixed(2)}`));
    });
    box.appendChild(s);
    return ginis;
  }

  // ---- geographic choropleth (lon/lat rings, equirectangular fit)
  function geoMap(id, geo, values, opts) {
    opts = opts || {};
    const box = document.getElementById(id); box.innerHTML = '';
    const names = Object.keys(geo);
    let minx = 1e9, maxx = -1e9, miny = 1e9, maxy = -1e9;
    names.forEach(n => geo[n].forEach(r => r.forEach(p => { if (p[0] < minx) minx = p[0]; if (p[0] > maxx) maxx = p[0]; if (p[1] < miny) miny = p[1]; if (p[1] > maxy) maxy = p[1]; })));
    const kx = Math.cos((miny + maxy) / 2 * Math.PI / 180);
    const W = opts.W || 460, H = opts.H || 380, pad = 10;
    const gw = (maxx - minx) * kx, gh = (maxy - miny), sc = Math.min((W - 2 * pad) / gw, (H - 2 * pad) / gh);
    const ox = (W - gw * sc) / 2, oy = (H - gh * sc) / 2;
    const X = lon => ox + (lon - minx) * kx * sc, Y = lat => oy + (maxy - lat) * sc;
    const s = svg(W, H);
    const dmin = opts.domain ? opts.domain[0] : 0, dmax = opts.domain ? opts.domain[1] : 1;
    const c0 = opts.colorLo || '#eef2f7', c1 = opts.colorHi || '#2756d3';
    names.forEach(n => {
      let d = '';
      geo[n].forEach(r => { r.forEach((p, i) => d += (i ? 'L' : 'M') + X(p[0]).toFixed(1) + ' ' + Y(p[1]).toFixed(1)); d += 'Z'; });
      const v = values[n];
      const t = (v == null || dmax === dmin) ? null : Math.max(0, Math.min(1, (v - dmin) / (dmax - dmin)));
      const path = el('path', { d, fill: t == null ? '#e6e9ee' : lerpColor(c0, c1, t), stroke: '#fff', 'stroke-width': .6 });
      hoverable(path, v == null ? `<b>${n}</b><br><span class="d">no data</span>` : `<b>${n}</b><br><span class="d">${opts.tipLabel || 'Value'}:</span> ${opts.fmt ? opts.fmt(v) : v}`);
      s.appendChild(path);
    });
    box.appendChild(s);
  }

  // ---- 100%-stacked area over time
  function stackShare(id, xs, bands, opts) {
    opts = opts || {};
    const box = document.getElementById(id); box.innerHTML = '';
    const W = opts.W || 960, H = opts.H || 380, pad = { l: 42, r: 14, t: 12, b: 28 };
    const s = svg(W, H);
    const n = xs.length, totals = xs.map((_, i) => bands.reduce((a, b) => a + (b.vals[i] || 0), 0) || 1);
    const X = i => pad.l + (n <= 1 ? 0.5 : i / (n - 1)) * (W - pad.l - pad.r);
    const Y = v => H - pad.b - v * (H - pad.t - pad.b);
    for (let k = 0; k <= 4; k++) { const yy = Y(k / 4); s.appendChild(el('line', { x1: pad.l, y1: yy, x2: W - pad.r, y2: yy, class: 'gl' })); s.appendChild(el('text', { x: pad.l - 6, y: yy + 3, 'text-anchor': 'end', class: 'axis' }, (k * 25) + '%')); }
    let cum = xs.map(() => 0);
    bands.forEach(b => {
      const lower = cum.slice(), upper = xs.map((_, i) => lower[i] + (b.vals[i] || 0) / totals[i]);
      let d = ''; upper.forEach((v, i) => d += (i ? 'L' : 'M') + X(i).toFixed(1) + ' ' + Y(v).toFixed(1));
      for (let i = n - 1; i >= 0; i--) d += 'L' + X(i).toFixed(1) + ' ' + Y(lower[i]).toFixed(1);
      s.appendChild(el('path', { d: d + 'Z', fill: b.color, opacity: .92 })); cum = upper;
    });
    const step = n > 12 ? 3 : (n > 6 ? 2 : 1);
    xs.forEach((x, i) => { if (i % step === 0 || i === n - 1) s.appendChild(el('text', { x: X(i), y: H - 8, 'text-anchor': 'middle', class: 'axis' }, "'" + String(x).slice(2))); });
    xs.forEach((x, i) => {
      const bw = (W - pad.l - pad.r) / Math.max(1, n - 1);
      const rect = el('rect', { x: (X(i) - bw / 2).toFixed(1), y: pad.t, width: bw.toFixed(1), height: H - pad.t - pad.b, fill: 'transparent' });
      const parts = bands.map(b => `<span class="d">${b.label}:</span> ${fmtPct1((b.vals[i] || 0) / totals[i])}`).reverse().join('<br>');
      const tot = opts.unit === '$' ? money(totals[i]) : totals[i].toLocaleString() + ' rounds';
      hoverable(rect, `<b>${x}</b> · ${tot}<br>${parts}`);
      s.appendChild(rect);
    });
    box.appendChild(s);
  }

  // ---- pill toggle group (template .top-filter style)
  function pills(id, onPick) {
    const node = document.getElementById(id); if (!node) return;
    node.addEventListener('click', e => {
      const b = e.target.closest('button'); if (!b || b.classList.contains('active')) return;
      [...node.querySelectorAll('button')].forEach(c => c.classList.remove('active')); b.classList.add('active');
      onPick(b.dataset[Object.keys(b.dataset)[0]]);
    });
  }

  // ---- year multi-select dropdown. opts:{years:[int], initial:[int], onChange(years[])}
  function yearDropdown(wrapId, opts) {
    const wrap = document.getElementById(wrapId); if (!wrap) return;
    const years = opts.years.slice().sort((a, b) => a - b);
    let sel = new Set(opts.initial && opts.initial.length ? opts.initial : years);
    wrap.classList.add('yr-wrap');
    const toggle = el2('div', 'top-filter'); const btn = document.createElement('button');
    btn.type = 'button'; btn.className = 'yr-toggle'; toggle.appendChild(btn);
    const panel = el2('div', 'yr-panel');
    years.forEach(y => {
      const lab = document.createElement('label'); const cb = document.createElement('input');
      cb.type = 'checkbox'; cb.value = y; cb.checked = sel.has(y);
      cb.addEventListener('change', () => { cb.checked ? sel.add(y) : sel.delete(y); commit(); });
      lab.appendChild(cb); lab.appendChild(document.createTextNode(y)); panel.appendChild(lab);
    });
    const acts = el2('div', 'yr-actions');
    const mkAct = (label, fn) => { const b = document.createElement('button'); b.type = 'button'; b.textContent = label; b.addEventListener('click', e => { e.stopPropagation(); fn(); syncBoxes(); commit(); }); acts.appendChild(b); };
    mkAct('All', () => { sel = new Set(years); });
    if (opts.recent) mkAct(opts.recent[0] + '–' + ('' + opts.recent[1]).slice(2), () => { sel = new Set(years.filter(y => y >= opts.recent[0] && y <= opts.recent[1])); });
    panel.appendChild(acts);
    wrap.appendChild(toggle); wrap.appendChild(panel);
    function el2(tag, cls) { const e = document.createElement(tag); e.className = cls; return e; }
    function syncBoxes() { [...panel.querySelectorAll('input')].forEach(cb => cb.checked = sel.has(+cb.value)); }
    function label() {
      const a = years.filter(y => sel.has(y));
      if (!a.length) return 'No years ▾';
      if (a.length === 1) return a[0] + ' ▾';
      if (a.length === years.length) return 'All years ▾';
      const contiguous = a[a.length - 1] - a[0] === a.length - 1;
      return (contiguous ? a[0] + '–' + a[a.length - 1] : a.length + ' years') + ' ▾';
    }
    function commit() { btn.textContent = label(); opts.onChange(years.filter(y => sel.has(y))); }
    btn.addEventListener('click', e => { e.stopPropagation(); panel.classList.toggle('show'); });
    document.addEventListener('click', e => { if (!wrap.contains(e.target)) panel.classList.remove('show'); });
    commit();
  }

  // ---- generic multi-select dropdown. opts:{items:[{value,label}], initial:[value], noun, cols, onChange(values[])}
  function multiSelect(wrapId, opts) {
    const wrap = document.getElementById(wrapId); if (!wrap) return;
    const items = opts.items, noun = opts.noun || 'items';
    let sel = new Set(opts.initial && opts.initial.length ? opts.initial : items.map(i => i.value));
    wrap.classList.add('yr-wrap');
    const toggle = document.createElement('div'); toggle.className = 'top-filter';
    const btn = document.createElement('button'); btn.type = 'button'; btn.className = 'yr-toggle'; toggle.appendChild(btn);
    const panel = document.createElement('div'); panel.className = 'yr-panel';
    if (opts.cols) panel.style.gridTemplateColumns = 'repeat(' + opts.cols + ',auto)';
    items.forEach(it => {
      const lab = document.createElement('label'); const cb = document.createElement('input');
      cb.type = 'checkbox'; cb.value = it.value; cb.checked = sel.has(it.value);
      cb.addEventListener('change', () => { cb.checked ? sel.add(it.value) : sel.delete(it.value); commit(); });
      lab.appendChild(cb); lab.appendChild(document.createTextNode(it.label)); panel.appendChild(lab);
    });
    const acts = document.createElement('div'); acts.className = 'yr-actions';
    const mkAct = (label, fn) => { const b = document.createElement('button'); b.type = 'button'; b.textContent = label; b.addEventListener('click', e => { e.stopPropagation(); fn(); sync(); commit(); }); acts.appendChild(b); };
    mkAct('All', () => { sel = new Set(items.map(i => i.value)); });
    panel.appendChild(acts);
    wrap.appendChild(toggle); wrap.appendChild(panel);
    function sync() { [...panel.querySelectorAll('input')].forEach(cb => cb.checked = sel.has(cb.value)); }
    function label() {
      const a = items.filter(i => sel.has(i.value));
      if (!a.length) return 'No ' + noun + ' ▾';
      if (a.length === 1) return a[0].label + ' ▾';
      if (a.length === items.length) return 'All ' + noun + ' ▾';
      return a.length + ' ' + noun + ' ▾';
    }
    function commit() { btn.textContent = label(); opts.onChange(items.filter(i => sel.has(i.value)).map(i => i.value)); }
    btn.addEventListener('click', e => { e.stopPropagation(); panel.classList.toggle('show'); });
    document.addEventListener('click', e => { if (!wrap.contains(e.target)) panel.classList.remove('show'); });
    commit();
  }

  global.VL = { M, el, svg, lineChart, sankey, groupedBar, compositionBars, chord, lorenz, geoMap, stackShare, seg, pills, yearDropdown, multiSelect,
    fmtPct, fmtPct1, money, hoverable, lerpColor, euLabel: k => k === 'EU27' ? 'EU-27' : 'EU+UK+EFTA' };
})(window);
