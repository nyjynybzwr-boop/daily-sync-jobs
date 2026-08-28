import json
import os
from pathlib import Path

p = Path(os.environ['CORRECTED'])
d = json.loads(p.read_text())
assert d['complete'] is True
assert d['item_count'] == 50
assert d['period_status'] == 'current_ytd'
assert d['as_of_date'] == '2026-08-29'

seen = set()
for i, x in enumerate(d['items'], 1):
    assert x['release_year'] == 2026
    assert x['release_year_rank'] == i
    group = {x['product_id']}
    group.update(
        str(e.get('workno', '')).upper()
        for e in (x.get('language_editions') or [])
        if e.get('workno')
    )
    overlap = seen & group
    assert not overlap, (i, x['product_id'], sorted(overlap))
    seen.update(group)

audits = [a for a in d['selection_audit'] if a.get('decision') == 'excluded_language_edition_duplicate']
assert any(
    a.get('product_id') == 'RJ01618847'
    and a.get('duplicate_of_product_id') == 'RJ01622357'
    for a in audits
), audits

print('corrected cutoff', d['items'][-1]['source_ranking_rank'], d['items'][-1]['product_id'])
print('language-edition exclusions', len(audits))
