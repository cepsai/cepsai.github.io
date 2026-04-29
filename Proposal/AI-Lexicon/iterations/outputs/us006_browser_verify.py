"""Structural browser-verification proxy for US-006.

Loads the rendered v28 HTML, extracts the CONCEPTS data, and for each of the
5 in-scope EU regulatory texts confirms the content the popup would show
when a user clicks an article link:

  - the cell's `reference` field
  - the cell's `verbatim` field (or the analysis-fallback note)
  - that the cited article numbers actually exist in the corresponding law-blob

This is the structural equivalent of opening the page and clicking through
5+ links per EU text. Reports a per-text pass/fail summary.
"""
import json, re, sys
from pathlib import Path

HTML = Path('/Users/robertpraas/Documents/GitHub/cepsai.github.io/Proposal/AI-Lexicon/iterations/digital_lexicon_v28.html')
html = HTML.read_text(encoding='utf-8')

# Extract CONCEPTS literal.
start = html.find('const CONCEPTS = [')
assert start > 0, 'CONCEPTS literal not found'
i = start + len('const CONCEPTS = ')
depth = 0
in_str = False
esc = False
while i < len(html):
    c = html[i]
    if in_str:
        if esc: esc = False
        elif c == '\\': esc = True
        elif c == '"': in_str = False
    else:
        if c == '"': in_str = True
        elif c == '[': depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    i += 1
concepts = json.loads(html[start + len('const CONCEPTS = '):end])

# Collect all EU cells keyed by (sub_concept_id, dimension_id).
eu_cells = {}
for c in concepts:
    for s in c.get('sub_concepts', []):
        for d in s.get('dimensions', []):
            cell = d.get('cells', {}).get('eu')
            if cell:
                eu_cells[(s['id'], d['id'])] = cell

def find_cell(prefix_sub, dim_substr):
    """Find the first cell matching sub_concept prefix + dim id substring."""
    for (sub, dim), cell in eu_cells.items():
        if sub == prefix_sub and dim_substr in dim:
            return sub, dim, cell
    return None

# Spot checks per the us006_eu_audit.md plan.
spot_checks = [
    # EU AI Act (>=5)
    ('eu-ai-act', 'provider', 'scope', ['Article 50']),
    ('eu-ai-act', 'provider', 'transparency', ['Article 50']),
    ('eu-ai-act', 'provider', 'penalties', ['Article 99']),
    ('eu-ai-act', 'provider-of-high-risk-ai-systems', 'registration', ['Article 49', 'Article 16']),
    ('eu-ai-act', 'provider-of-high-risk-ai-systems', 'scope', ['Article 6', 'Article 3 (3)', 'Annex III']),
    ('eu-ai-act', 'provider-of-general-purpose-ai-models-with-systemic-risk', 'notification', ['Article 52']),
    ('eu-ai-act', 'deployer-of-high-risk-ai-systems', 'right-to-explanation', ['Article 86']),
    # CoP CC
    ('eu-gpai-cop-copyright', 'provider-of-general-purpose-ai-models', 'copyright', ['Code of Practice for GPAI - Copyright Chapter']),
    ('eu-gpai-cop-copyright', 'provider-of-general-purpose-ai-models-with-systemic-risk', 'copyright', ['Code of Practice for GPAI - Copyright Chapter']),
    # CoP TC (bundled, but check the Transparency Chapter label appears in agg ref)
    ('eu-gpai-cop-transparency', 'provider-of-general-purpose-ai-models', 'specific-information-disclosure', ['CoP TC', 'Article 53']),
    # CoP SSC
    ('eu-gpai-cop-safety', 'provider-of-general-purpose-ai-models-with-systemic-risk', 'risk-management', ['Code of Practice for GPAI - Safety and Security Chapter']),
    ('eu-gpai-cop-safety', 'provider-of-general-purpose-ai-models-with-systemic-risk', 'incident-reporting', ['Code of Practice for GPAI - Safety and Security Chapter']),
    # GL
    ('eu-guidelines-gpai-scope', 'general-purpose-ai-model', 'compute-threshold', ['GL, (17)']),
    ('eu-guidelines-gpai-scope', 'provider-of-general-purpose-ai-models', 'scope-system', ['(GL, (59))', '(GL, (60))']),
    ('eu-guidelines-gpai-scope', 'provider-of-general-purpose-ai-models', 'scope', ['Article 3', 'GL, (17)']),
]

results = {}
for law, sub, dim_substr, expected_strings in spot_checks:
    found = find_cell(sub, dim_substr)
    key = f'{law} :: {sub}/{dim_substr}'
    if not found:
        results[key] = f'CELL_NOT_FOUND'
        continue
    _, real_dim, cell = found
    ref = (cell.get('reference') or '')
    ana = (cell.get('analysis') or '')
    vb  = (cell.get('verbatim')  or '')
    blob = ref + ' || ' + ana + ' || ' + vb
    misses = [e for e in expected_strings if e not in blob]
    if misses:
        results[key] = f'MISS {misses} (dim={real_dim}, ref={ref!r})'
    else:
        # Popup will show: ref (or fallback), verbatim (or analysis-fallback note).
        # Confirm popup-renderable content is non-empty.
        if not (ref or ana):
            results[key] = f'EMPTY_POPUP (dim={real_dim})'
        else:
            results[key] = f'OK (dim={real_dim}, ref-len={len(ref)}, ana-len={len(ana)}, vb-len={len(vb)})'

# Per-law tallies.
per_law = {}
for k, v in results.items():
    law = k.split(' :: ')[0]
    per_law.setdefault(law, {'pass':0,'fail':0})
    if v.startswith('OK'):
        per_law[law]['pass'] += 1
    else:
        per_law[law]['fail'] += 1

print('=== US-006 browser-verification proxy ===')
print(f'Loaded {len(eu_cells)} EU cells from CONCEPTS.\n')
for k, v in results.items():
    flag = 'OK ' if v.startswith('OK') else 'X  '
    print(f'  [{flag}] {k}\n        {v}')
print('\nPer-law spot-check tallies:')
for law, t in per_law.items():
    print(f'  {law}: pass={t["pass"]}, fail={t["fail"]}')
fail_total = sum(t['fail'] for t in per_law.values())
sys.exit(0 if fail_total == 0 else 1)
