/* Belgium slice — aggregation layer over window.METRICS (data/belgium.js).
   All aggregation is client-side from round-level records, so every page can
   switch direction / geo level / weight / round type / years without a rebuild.
   file://-safe, no deps. Pairs with viz-lib.js (charts) and viz.css (layout). */
(function (global) {
  const M = global.METRICS;

  // record layouts (kept in sync with build_belgium.py)
  const R_Y = 0, R_B = 1, R_O = 2, R_USD = 3, R_INV = 4, R_F = 5;
  const I_NAME = 0, I_PERM = 1, I_CC = 2, I_JUR = 3, I_PROV = 4;
  const O_SLUG = 0, O_NAME = 1, O_CC = 2, O_JUR = 3, O_PROV = 4;
  const FLAG_IN = 1, FLAG_OUT = 2, FLAG_AI = 4;

  /* ---- sector domain -----------------------------------------------------
     'ai'  : only rounds whose funded company carries a Crunchbase AI category
             (house definition, see build_ai_flags.py) — THE DEFAULT
     'all' : every equity round, all sectors
     Held module-level so a page switches domain with one call and every
     aggregation below picks it up; select() is the single choke point.      */
  let DOMAIN = 'ai';
  const setDomain = d => { DOMAIN = (d === 'all' ? 'all' : 'ai'); return DOMAIN; };
  const getDomain = () => DOMAIN;
  const inDomain = r => DOMAIN === 'all' || (r[R_F] & FLAG_AI);
  const DOMAIN_LABEL = { ai: 'AI companies', all: 'all sectors' };
  const N_AI = M.rounds.reduce((a, r) => a + ((r[R_F] & FLAG_AI) ? 1 : 0), 0);

  /* ---- EU institutions registered in Brussels ----------------------------
     EIC, EIC Accelerator, EISMEA, Horizon 2020, the European Commission, the
     ERC, the ESF and the EIT bodies all carry a Belgian location record in
     Crunchbase, so by construction they count as BELGIAN investors — ~13% of
     all Belgian-investor dollars, almost all deployed abroad and booked to
     Brussels. `?eubodies=excl` (the default) reclassifies them into their own
     bloc, 'EU institutions': they stop being Belgian money, but the dollars
     are conserved — EU-body money into a Belgian company becomes foreign
     INFLOW rather than domestic. `?eubodies=incl` restores the raw Crunchbase
     treatment. The index list is baked by build_belgium.py, so there is one
     definition for every page.                                             */
  const EU_INST = 'EU institutions';
  const EU_BODY = new Set(M.eu_bodies || []);
  let EXCL_EU = true;
  const setEUB = m => { EXCL_EU = (m !== 'incl'); return EXCL_EU; };
  const getEUB = () => (EXCL_EU ? 'excl' : 'incl');
  const isEUBody = i => EU_BODY.has(i);
  // effective country of an investor under the current mode; the single place
  // the reclassification happens, so every aggregation below follows.
  const invCC = i => (EXCL_EU && EU_BODY.has(i)) ? EU_INST : M.inv[i][I_CC];
  const isBEinv = i => invCC(i) === 'Belgium';

  const EU27 = new Set(M.eu27), EFTA = new Set(M.efta), UK = new Set(M.uk);

  function bloc(cc) {
    if (cc === 'Belgium') return 'Belgium';
    if (cc === EU_INST) return EU_INST;
    if (EU27.has(cc)) return 'EU-27 (excl. BE)';
    if (UK.has(cc) || EFTA.has(cc)) return 'UK + EFTA';
    if (cc === 'United States') return 'United States';
    if (cc === 'Unknown' || !cc) return 'Unknown';
    return 'Rest of world';
  }

  // ---- colours ------------------------------------------------------------
  const BLOC_COL = {
    'Belgium': '#8a97a6',
    'EU institutions': '#c9a227',
    'EU-27 (excl. BE)': '#2756d3',
    'UK + EFTA': '#3f9c76',
    'United States': '#E1701A',
    'Rest of world': '#8e5fb5',
    'Unknown': '#c3cad3',
  };
  const NUTS1_COL = {
    'Flanders': '#E1701A', 'Brussels': '#2756d3',
    'Wallonia': '#3f9c76', 'Region n/a': '#c3cad3',
  };
  // provinces: shaded variants of their NUTS-1 colour
  const PROV_COL = (function () {
    const out = {}, seen = {};
    M.prov_order.forEach(code => {
      const p = M.prov[code], base = NUTS1_COL[p.nuts1] || '#8a97a6';
      const k = (seen[p.nuts1] = (seen[p.nuts1] || 0) + 1);
      out[p.name] = VL.lerpColor(base, '#ffffff', Math.min(0.42, (k - 1) * 0.14));
    });
    return out;
  })();

  // the single non-Belgian target node on intra_be.html (kept distinct from
  // flows.html's "Other", which means "countries beyond top-N")
  const OUTSIDE = 'Outside Belgium';

  function nodeColor(name, level) {
    if (name === OUTSIDE) return '#8e5fb5';
    if (BLOC_COL[name]) return BLOC_COL[name];
    if (NUTS1_COL[name]) return NUTS1_COL[name];
    if (PROV_COL[name]) return PROV_COL[name];
    if (name === 'Other') return '#b9c2cc';
    return BLOC_COL[bloc(name)] || '#8a97a6';
  }

  // country name -> ISO-2 tag; 'Unknown'/missing render as no tag
  const CC2 = M.cc2 || {};
  // 'EU' rather than the muted '?' — an EU institution is located, just not in a
  // country; '?' means Crunchbase has no location at all and would read as an error
  const cc2 = name => (name === EU_INST ? 'EU' : (CC2[name] || null));

  // bloc order with the EU-institutions band slotted in after Belgium. Not in
  // M.bloc_order: that stays exactly as the build emits it.
  const BLOC_ORDER = M.bloc_order.includes(EU_INST) ? M.bloc_order.slice()
    : (function () {
        const o = M.bloc_order.slice(), at = o.indexOf('Belgium');
        o.splice(at < 0 ? 0 : at + 1, 0, EU_INST);
        return o;
      })();

  // ---- geo level ----------------------------------------------------------
  // level: 'country' | 'nuts1' | 'nuts2'
  function beNode(provCode, level) {
    if (level === 'country') return 'Belgium';
    const p = M.prov[provCode] || M.prov.BEZZ;
    return level === 'nuts1' ? p.nuts1 : p.name;
  }
  function beNodeOrder(level) {
    if (level === 'country') return ['Belgium'];
    if (level === 'nuts1') return ['Brussels', 'Flanders', 'Wallonia', 'Region n/a'];
    return M.prov_order.map(c => M.prov[c].name);
  }
  const LEVEL_LABEL = { country: 'Belgium', nuts1: 'Region', nuts2: 'Province' };

  // ---- filtering ----------------------------------------------------------
  // f: {dir:'in'|'out', years:[int]|null, buckets:[label]|null}
  function select(f) {
    const flag = f.dir === 'out' ? FLAG_OUT : FLAG_IN;
    const ys = f.years && f.years.length ? new Set(f.years) : null;
    const bs = f.buckets && f.buckets.length
      ? new Set(f.buckets.map(b => M.bucket_order.indexOf(b))) : null;
    // FLAG_OUT is baked at build time with EU bodies counted as Belgian, so a
    // round whose ONLY Belgian investor is an EU body has to drop out of the
    // outbound universe under 'excl'. Inbound is company-based and unaffected.
    const dropEU = EXCL_EU && flag === FLAG_OUT && EU_BODY.size;
    return M.rounds.filter(r => (r[R_F] & flag)
      && inDomain(r)
      && (!ys || ys.has(r[R_Y]))
      && (!bs || bs.has(r[R_B]))
      && (!dropEU || r[R_INV].some(isBEinv)));
  }

  /* ---- how many distinct Belgian entities are in the current domain ------
     M.meta.n_be_orgs / n_be_investors are whole-corpus constants, so they are
     wrong the moment the AI filter is on. Pages should use this instead.    */
  function counts() {
    const orgs = new Set(), invs = new Set();
    M.rounds.forEach(r => {
      if (!inDomain(r)) return;
      if ((r[R_F] & FLAG_IN) && M.org[r[R_O]][O_CC] === 'Belgium') orgs.add(r[R_O]);
      if (r[R_F] & FLAG_OUT) r[R_INV].forEach(i => {
        if (isBEinv(i)) invs.add(i);
      });
    });
    return { beOrgs: orgs.size, beInvestors: invs.size };
  }

  /* ---- the AI / all-sectors toggle, rendered identically on every page --- */
  function domainPills(id, onChange) {
    const box = document.getElementById(id);
    if (!box) return;
    box.classList.add('top-filter');
    box.innerHTML =
      `<button data-dom="ai"${DOMAIN === 'ai' ? ' class="active"' : ''}>AI</button>` +
      `<button data-dom="all"${DOMAIN === 'all' ? ' class="active"' : ''}>All sectors</button>`;
    VL.pills(id, v => { setDomain(v); onChange(v); });
  }

  /* ---- the EU-institutions toggle, rendered identically on every page --- */
  function eubPills(id, onChange) {
    const box = document.getElementById(id);
    if (!box) return;
    box.classList.add('top-filter');
    box.innerHTML =
      `<button data-eub="excl"${EXCL_EU ? ' class="active"' : ''} title="EU institutions HQ'd in Brussels are treated as EU money, not Belgian">EU bodies out</button>` +
      `<button data-eub="incl"${EXCL_EU ? '' : ' class="active"'} title="Raw Crunchbase treatment: EU institutions count as Belgian investors">in</button>`;
    VL.pills(id, v => { setEUB(v); onChange(v); });
  }

  /* ---- how big is the EU-institution correction? ------------------------
     Membership comes from M.eu_bodies (baked by build_belgium.py); the share
     differs sharply by domain, so it is computed live.                     */
  /* Share of Belgian-investor dollars that are really EU-institution money.
     Always computed on the RAW Crunchbase treatment (EU bodies counted as
     Belgian), whatever the current mode — it is the size of the correction,
     so it must not go to zero the moment the correction is applied.        */
  function euBodyShare() {
    let all = 0, eu = 0;
    M.rounds.forEach(r => {
      if (!(r[R_F] & FLAG_OUT) || !inDomain(r)) return;
      const n = r[R_INV].length; if (!n) return;
      const share = r[R_USD] / n;
      r[R_INV].forEach(i => {
        if (M.inv[i][I_CC] !== 'Belgium') return;
        all += share;
        if (EU_BODY.has(i)) eu += share;
      });
    });
    return { usd: eu, pct: all ? eu / all * 100 : 0 };
  }

  // round counts for the current domain, for footnotes that used to hardcode them
  function roundCounts() {
    const out = select({ dir: 'out' });
    const dom = out.filter(r => M.org[r[R_O]][O_CC] === 'Belgium');
    return { outbound: out.length, domestic: dom.length, abroad: out.length - dom.length,
             inbound: select({ dir: 'in' }).length };
  }

  // one sentence for footnotes, so every page states its scope the same way
  const scopeNote = () => DOMAIN === 'ai'
    ? ' Scope: AI companies only — rounds raised by a company carrying a Crunchbase'
      + ' AI category (Artificial Intelligence, Generative AI, Machine Learning, NLP,'
      + ' Agentic AI, AI Infrastructure, Foundational AI, Intelligent Systems).'
      + ` That is ${N_AI.toLocaleString()} of ${M.rounds.length.toLocaleString()} rounds,`
      + ' so single-year and province-level cells are thin — compare periods and regions,'
      + ' not years and provinces.'
    : ' Scope: all sectors, equity rounds only.';

  // one sentence describing the EU-institution treatment, for the same footnotes
  const eubNote = () => {
    const e = euBodyShare();
    return EXCL_EU
      ? ` EU institutions registered in Brussels (EIC, EIC Accelerator, EISMEA, Horizon 2020,`
        + ` the European Commission, ERC, ESF, EIT Food, EIT Digital Accelerator) are EXCLUDED from`
        + ` the Belgian side and shown as their own “EU institutions” origin — they carry a Belgian`
        + ` location record in Crunchbase and would otherwise be ${e.pct.toFixed(0)}% of Belgian-investor`
        + ` dollars (${VL.money(e.usd)}), almost all of it deployed abroad and booked to Brussels.`
        + ` Add them back with ?eubodies=incl.`
      : ` EU institutions registered in Brussels (EIC, EIC Accelerator, EISMEA…) are INCLUDED as`
        + ` Belgian investors here, the raw Crunchbase treatment: ${e.pct.toFixed(0)}% of Belgian-investor`
        + ` dollars (${VL.money(e.usd)}), nearly all deployed abroad and booked to Brussels.`
        + ` ?eubodies=excl removes them.`;
  };

  // counterparty node for one investor/company, at country granularity
  const invNode = i => invCC(i);
  const orgNode = o => M.org[o][O_CC] === 'Belgium' ? 'Belgium' : M.org[o][O_CC];

  /* ---- sankey links -------------------------------------------------------
     dir 'in'  : funder origin (country)  ->  Belgian recipient (geo level)
     dir 'out' : Belgian funder (geo level) -> recipient destination (country)
     USD: round total split equally across ALL investors in the round.
     Rounds: each round counted once per distinct (source,target) pair.        */
  function flows(f) {
    const level = f.level || 'country', topN = f.topN == null ? 8 : f.topN;
    const rows = select(f), acc = {}, foreignTot = {};
    rows.forEach(r => {
      const n = r[R_INV].length; if (!n) return;
      const share = r[R_USD] / n;
      const pairs = {};                                   // dedup rounds per pair
      if (f.dir === 'out') {
        const tgt = orgNode(r[R_O]);
        r[R_INV].forEach(i => {
          if (!isBEinv(i)) return;
          const src = beNode(M.inv[i][I_PROV], level);
          const k = src + ' ' + tgt;
          (pairs[k] = pairs[k] || { source: src, target: tgt, usd: 0 }).usd += share;
        });
      } else {
        const tgt = beNode(M.org[r[R_O]][O_PROV], level);
        r[R_INV].forEach(i => {
          const src = invNode(i);
          const k = src + ' ' + tgt;
          (pairs[k] = pairs[k] || { source: src, target: tgt, usd: 0 }).usd += share;
        });
      }
      Object.values(pairs).forEach(p => {
        const k = p.source + ' ' + p.target;
        const a = (acc[k] = acc[k] || { source: p.source, target: p.target, rounds: 0, usd: 0 });
        a.rounds += 1; a.usd += p.usd;
        const foreign = f.dir === 'out' ? p.target : p.source;
        foreignTot[foreign] = (foreignTot[foreign] || 0)
          + (f.weight === 'usd' ? p.usd : 1);
      });
    });

    // keep Belgium + Unknown always; top-N of the rest collapses into "Other"
    const ranked = Object.keys(foreignTot)
      .filter(k => k !== 'Belgium' && k !== 'Unknown')
      .sort((a, b) => foreignTot[b] - foreignTot[a]);
    const keep = new Set(ranked.slice(0, topN));
    const collapse = name => (name === 'Belgium' || name === 'Unknown' || keep.has(name))
      ? name : 'Other';

    const out = {};
    Object.values(acc).forEach(l => {
      const src = f.dir === 'out' ? l.source : collapse(l.source);
      const tgt = f.dir === 'out' ? collapse(l.target) : l.target;
      const k = src + ' ' + tgt;
      const a = (out[k] = out[k] || { source: src, target: tgt, rounds: 0, usd: 0 });
      a.rounds += l.rounds; a.usd += l.usd;
    });
    const links = Object.values(out);

    const foreignOrder = ['Belgium', ...ranked.slice(0, topN), 'Other', 'Unknown']
      .filter((v, i, a) => a.indexOf(v) === i);
    const beOrder = beNodeOrder(level).filter(n =>
      links.some(l => (f.dir === 'out' ? l.source : l.target) === n));
    return f.dir === 'out'
      ? { links, srcNames: beOrder, tgtNames: foreignOrder.filter(n => links.some(l => l.target === n)) }
      : { links, srcNames: foreignOrder.filter(n => links.some(l => l.source === n)), tgtNames: beOrder };
  }

  /* ---- per-year bloc composition (stacked share) ------------------------- */
  function trend(f) {
    const rows = select({ dir: f.dir, buckets: f.buckets });
    const years = M.meta.years.filter(y => y >= (f.from || 2010) && y <= (f.to || 9999));
    const idx = {}; years.forEach((y, i) => idx[y] = i);
    const bands = {}; BLOC_ORDER.forEach(b => bands[b] = years.map(() => 0));
    const counts = years.map(() => 0);
    rows.forEach(r => {
      const i = idx[r[R_Y]]; if (i == null) return;
      const n = r[R_INV].length; if (!n) return;
      counts[i] += 1;
      const share = r[R_USD] / n;
      if (f.dir === 'out') {
        const b = bloc(M.org[r[R_O]][O_CC]);
        const nbe = r[R_INV].reduce((a, x) => a + (isBEinv(x) ? 1 : 0), 0);
        bands[b][i] += f.weight === 'usd' ? share * nbe : nbe / n;
      } else {
        r[R_INV].forEach(x => {
          const b = bloc(invCC(x));
          bands[b][i] += f.weight === 'usd' ? share : 1 / n;
        });
      }
    });
    return {
      years,
      counts,
      bands: BLOC_ORDER
        .filter(b => bands[b].some(v => v > 0))
        .map(b => ({ label: b, color: BLOC_COL[b], vals: bands[b] })),
    };
  }

  /* ---- by round-type bucket: domestic vs foreign ------------------------- */
  function byBucket(f) {
    const rows = select({ dir: f.dir, years: f.years });
    const acc = {}; M.bucket_order.forEach(b => acc[b] = { dom: 0, foreign: 0, n: 0 });
    rows.forEach(r => {
      const b = M.bucket_order[r[R_B]], n = r[R_INV].length; if (!n) return;
      const a = acc[b]; a.n += 1;
      const share = r[R_USD] / n;
      if (f.dir === 'out') {
        const nbe = r[R_INV].reduce((x, i) => x + (isBEinv(i) ? 1 : 0), 0);
        const dom = M.org[r[R_O]][O_CC] === 'Belgium';
        const v = f.weight === 'usd' ? share * nbe : 1;
        a[dom ? 'dom' : 'foreign'] += v;
      } else {
        r[R_INV].forEach(i => {
          const v = f.weight === 'usd' ? share : 1 / n;
          a[isBEinv(i) ? 'dom' : 'foreign'] += v;
        });
      }
    });
    return M.bucket_order.filter(b => acc[b].n > 0).map(b => ({ bucket: b, ...acc[b] }));
  }

  /* ---- named entities ----------------------------------------------------
     dir 'in'  : Belgian companies, with the bloc mix of their funders
     dir 'out' : Belgian investors, with the bloc mix of their destinations
     `partners` is keyed by counterparty INDEX (not name) so same-named
     entities in different countries stay distinct; each value carries the
     counterparty's own country for the tags on entities.html.              */
  function entities(f) {
    const rows = select(f), acc = {};
    const addPartner = (e, k, name, country) => {
      const p = (e.partners[k] = e.partners[k]
        || { name, country, cc: cc2(country), bloc: bloc(country), usd: 0, rounds: 0 });
      p.rounds += 1;
      return p;
    };
    rows.forEach(r => {
      const n = r[R_INV].length; if (!n) return;
      const share = r[R_USD] / n;
      if (f.dir === 'out') {
        const o = r[R_O], oCC = M.org[o][O_CC], dest = bloc(oCC);
        r[R_INV].forEach(i => {
          if (!isBEinv(i)) return;
          const e = (acc[i] = acc[i] || {
            key: i, name: M.inv[i][I_NAME], sub: (M.prov[M.inv[i][I_PROV]] || M.prov.BEZZ).name,
            perm: M.inv[i][I_PERM], rounds: 0, usd: 0, mix: {}, partners: {},
          });
          e.rounds += 1; e.usd += share; e.mix[dest] = (e.mix[dest] || 0) + share;
          addPartner(e, o, M.org[o][O_NAME], oCC).usd += share;
        });
      } else {
        const o = r[R_O];
        const e = (acc[o] = acc[o] || {
          key: o, name: M.org[o][O_NAME], sub: (M.prov[M.org[o][O_PROV]] || M.prov.BEZZ).name,
          perm: M.org[o][O_SLUG], rounds: 0, usd: 0, mix: {}, partners: {},
        });
        e.rounds += 1; e.usd += r[R_USD];
        r[R_INV].forEach(i => {
          const cc = invCC(i), b = bloc(cc);
          e.mix[b] = (e.mix[b] || 0) + share;
          addPartner(e, i, M.inv[i][I_NAME], cc).usd += share;
        });
      }
    });
    const list = Object.values(acc);
    const key = f.weight === 'usd' ? 'usd' : 'rounds';
    list.sort((a, b) => b[key] - a[key]);
    return list;
  }

  /* ---- intra-Belgian flows: BE investor node -> BE company node ----------
     f.other=true adds a single "Outside Belgium" target, so each Belgian
     region can be compared on how much it funds at home vs abroad. Selection
     then switches to dir 'out' (rounds with >=1 Belgian investor), which is a
     strict superset: every outbound round with a Belgian recipient also
     carries FLAG_IN, so the Belgian->Belgian links are identical either way
     and "Outside Belgium" is purely additive.                              */
  function intra(f) {
    const level = f.level === 'country' ? 'nuts1' : (f.level || 'nuts1');
    const other = !!f.other;
    const rows = select({ dir: other ? 'out' : 'in', years: f.years, buckets: f.buckets });
    const acc = {};
    rows.forEach(r => {
      const n = r[R_INV].length; if (!n) return;
      const share = r[R_USD] / n;
      const isBE = M.org[r[R_O]][O_CC] === 'Belgium';
      if (!isBE && !other) return;
      const tgt = isBE ? beNode(M.org[r[R_O]][O_PROV], level) : OUTSIDE;
      const pairs = {};
      r[R_INV].forEach(i => {
        if (!isBEinv(i)) return;
        const src = beNode(M.inv[i][I_PROV], level);
        const k = src + ' ' + tgt;
        (pairs[k] = pairs[k] || { source: src, target: tgt, usd: 0 }).usd += share;
      });
      Object.values(pairs).forEach(p => {
        const k = p.source + ' ' + p.target;
        const a = (acc[k] = acc[k] || { source: p.source, target: p.target, rounds: 0, usd: 0 });
        a.rounds += 1; a.usd += p.usd;
      });
    });
    const links = Object.values(acc);
    const order = beNodeOrder(level);
    const tgtOrder = other ? [...order, OUTSIDE] : order;
    return {
      links,
      srcNames: order.filter(n => links.some(l => l.source === n)),
      tgtNames: tgtOrder.filter(n => links.some(l => l.target === n)),
    };
  }

  /* ---- headline numbers for a filter ------------------------------------ */
  function stats(f) {
    const rows = select(f);
    let usd = 0, dom = 0, domRounds = 0;
    rows.forEach(r => {
      const n = r[R_INV].length; if (!n) return;
      const share = r[R_USD] / n;
      if (f.dir === 'out') {
        const nbe = r[R_INV].reduce((a, i) => a + (isBEinv(i) ? 1 : 0), 0);
        usd += share * nbe;
        if (M.org[r[R_O]][O_CC] === 'Belgium') { dom += share * nbe; domRounds += 1; }
      } else {
        usd += r[R_USD];
        const be = r[R_INV].reduce((a, i) => a + (isBEinv(i) ? 1 : 0), 0);
        dom += share * be;
        if (be) domRounds += 1;
      }
    });
    return { rounds: rows.length, usd, domesticUsd: dom, domesticRounds: domRounds };
  }

  // ---- shared URL/state helpers -------------------------------------------
  const Q = new URLSearchParams(location.search);
  // ?domain=all opts out of the AI default; anything else (or nothing) stays AI
  setDomain((Q.get('domain') || '').toLowerCase().trim() === 'all' ? 'all' : 'ai');
  // ?eubodies=incl opts back into the raw Crunchbase treatment; default is 'excl'
  setEUB((Q.get('eubodies') || '').toLowerCase().trim() === 'incl' ? 'incl' : 'excl');
  function qs(name, allowed, dflt) {
    const v = (Q.get(name) || '').toLowerCase().trim();
    return allowed.includes(v) ? v : dflt;
  }
  function parseYears(str, avail) {
    if (!str) return null;
    if (str.toLowerCase() === 'all') return avail.slice();
    const out = new Set();
    str.split(',').forEach(t => {
      t = t.trim();
      const m = t.match(/^(\d{4})\s*[-–]\s*(\d{4})$/);
      if (m) { for (let y = +m[1]; y <= +m[2]; y++) if (avail.includes(y)) out.add(y); }
      else if (/^\d{4}$/.test(t) && avail.includes(+t)) out.add(+t);
    });
    return out.size ? [...out].sort((a, b) => a - b) : null;
  }
  /* Carry the two global modes across in-site links, so a page opened from
     index.html keeps the toggles the user set there.                       */
  function decorateLinks(sel) {
    const keep = { domain: getDomain(), eubodies: getEUB() };
    document.querySelectorAll(sel || 'a[href]').forEach(a => {
      const href = a.getAttribute('href') || '';
      if (/^(https?:|mailto:|#)/i.test(href) || !/\.html(\?|#|$)/i.test(href)) return;
      const [base, hash] = href.split('#');
      const [path, qs] = base.split('?');
      const u = new URLSearchParams(qs || '');
      Object.entries(keep).forEach(([k, v]) => u.set(k, v));
      a.setAttribute('href', path + '?' + u.toString() + (hash ? '#' + hash : ''));
    });
  }

  function legend(id, items) {
    const box = document.getElementById(id); if (!box) return;
    box.innerHTML = items.map(([label, color]) =>
      `<span class="legend-item"><span class="legend-square" style="background:${color}"></span>${label}</span>`
    ).join('');
  }

  // the org/{year}.csv inputs were generated 2026-07-01, so the last year is partial
  const PARTIAL = ' Coverage is 2000–2026 from Crunchbase bulk exports (org CSVs built 2026-07-01);'
    + ' 2026 is a partial year and is not comparable to full years.';

  global.BE = {
    M, PARTIAL, bloc, BLOC_COL, NUTS1_COL, PROV_COL, nodeColor, cc2, OUTSIDE,
    beNode, beNodeOrder, LEVEL_LABEL,
    select, flows, trend, byBucket, entities, intra, stats, counts,
    setDomain, getDomain, domainPills, scopeNote, DOMAIN_LABEL,
    setEUB, getEUB, eubPills, eubNote, isEUBody, isBEinv, invCC, EU_INST, BLOC_ORDER,
    euBodyShare, roundCounts, decorateLinks,
    Q, qs, parseYears, legend,
    R: { Y: R_Y, B: R_B, O: R_O, USD: R_USD, INV: R_INV, F: R_F },
    I: { NAME: I_NAME, PERM: I_PERM, CC: I_CC, JUR: I_JUR, PROV: I_PROV },
    O: { SLUG: O_SLUG, NAME: O_NAME, CC: O_CC, JUR: O_JUR, PROV: O_PROV },
  };
})(window);
