// Computes the leaderboard "ALL" score for every model with the repo's own JS,
// fed exactly as index.html feeds it. Reads the live data saved by fetch-data.sh.
// Usage: node compute-scores.js <rawDir> <outCsv>
const path = require('path');
const fs = require('fs');
const REPO = path.join(process.env.HOME, 'Documents/GitHub/ai-model-leaderboard');
const rawDir = process.argv[2] || path.join(__dirname, 'raw');
const outCsv = process.argv[3] || path.join(__dirname, '..', 'scores.csv');

require(path.join(REPO, 'scripts/util.js'));
require(path.join(REPO, 'scripts/aggregation.js'));
require(path.join(REPO, 'scripts/tooltip.js'));
require(path.join(REPO, 'scripts/data-loader.js'));

// d3.json shim: map the URLs loadData builds onto the files fetched from the live sources.
const FILES = {
  'processed.json': 'processed.json', 'history.json': 'history.json', 'sources.json': 'sources.json',
  'models.json': 'models.json', 'tracking.json': 'tracking.json'
};
global.d3 = {
  json: async url => {
    const f = FILES[path.basename(url)];
    if (!f) throw new Error('unexpected url ' + url);
    return JSON.parse(fs.readFileSync(path.join(rawDir, f), 'utf8'));
  }
};

(async () => {
  const state = await LB.loadData({ dataMode: 'rtdb', dataBase: 'RTDB', configBase: 'SITE', snapshotParam: null });
  const rows = LB.aggregate({
    rawData: state.rawData,
    lastTrackedScores: state.lastTrackedScores,
    modelToGeo: state.modelToGeo,
    modelToOs: state.modelToOs,
    modelToDeactivated: state.modelToDeactivated,
    modelToLogo: state.modelToLogo,
    active: { question: 'ALL' },
    hiddenGeos: [],
    activeOsFilter: null,
    modeParam: 0,
    includeSegments: true,
    sourceData: state.sourceData,
    snapshotMode: false,
    ignoreModelFilter: true,
    onMissingBaseline: () => { throw new Error('GPT-5 baseline missing'); }
  });
  const byModel = {};
  state.rawData.forEach(d => { byModel[String(d.model).trim()] = d; });
  const parseNum = LB.util.parseNum;
  const srcState = (d, k) => {
    if (parseNum(d[k]) > 0) return 'live';
    const l = state.lastTrackedScores[d.model] && state.lastTrackedScores[d.model][k];
    return l && l.value > 0 ? `stale(${l.date})` : 'missing';
  };
  const out = rows.map(r => {
    const d = byModel[r.model] || {};
    const st = {};
    ['lma', 'aa', 'lb'].forEach(k => {
      let s = srcState(d, k);
      if (r.estimates && r.estimates[k] != null) s = 'estimated';
      st[k] = s;
    });
    return {
      model_id: r.model, name: r.name, logo: state.modelToLogo[r.model] || '',
      org: state.modelToOrg[r.model] || '', geo: state.modelToGeo[r.model] || '',
      deactivated: r.deactivated ? 1 : 0, score: r.score,
      lma: d.lma ?? '', aa: d.aa ?? '', aa_version: d.aa_version ?? '', aa_estimated_by_AA: Number(d.aa_estimated) === 1 ? 1 : 0, lb: d.lb ?? '',
      lma_state: st.lma, aa_state: st.aa, lb_state: st.lb
    };
  }).sort((a, b) => b.score - a.score);
  out.forEach((r, i) => { r.rank = i + 1; });
  const cols = ['rank', 'model_id', 'name', 'logo', 'org', 'geo', 'deactivated', 'score', 'lma', 'aa', 'aa_version', 'aa_estimated_by_AA', 'lb', 'lma_state', 'aa_state', 'lb_state'];
  const esc = v => { const s = String(v); return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };
  fs.writeFileSync(outCsv, [cols.join(',')].concat(out.map(r => cols.map(c => esc(c === 'score' ? r.score.toFixed(6) : r[c])).join(','))).join('\n') + '\n');
  console.log(JSON.stringify({ aaIndex: { v5Start: LB.aaIndex.v5Start, v5Ratio: LB.aaIndex.v5Ratio, gpt5V5: LB.aaIndex.gpt5V5 }, n: out.length }));
  // top per lab, active only
  const best = {};
  out.filter(r => !r.deactivated && r.score > 0).forEach(r => { if (r.logo && !best[r.logo]) best[r.logo] = r; });
  Object.values(best).sort((a, b) => b.score - a.score).forEach((r, i) =>
    console.log([i + 1, r.logo, r.org, r.name, r.model_id, r.score.toFixed(3), r.lma_state, r.aa_state, r.lb_state].join(' | ')));
  console.log('no-logo active rows:', out.filter(r => !r.deactivated && !r.logo).map(r => r.model_id).join(', '));
})().catch(e => { console.error(e); process.exit(1); });
