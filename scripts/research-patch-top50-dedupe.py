from pathlib import Path

p = Path('scripts/backfill-release-year-sales-top50.mjs')
s = p.read_text()

old = """  const items = [];
  const audit = [];
  let stoppedReason = null;
"""
new = """  const items = [];
  const audit = [];
  const selectedLanguageEditionOwner = new Map();
  let stoppedReason = null;
"""
if old in s:
    s = s.replace(old, new, 1)
else:
    s = s.replace(
        '  const selectedLanguageEditionIds = new Set();',
        '  const selectedLanguageEditionOwner = new Map();',
        1,
    )

old = """      } else {
        const releaseYearRank = items.length + 1;
        items.push({
"""
new = """      } else {
        const languageEditionIds = new Set([
          candidate.product_id,
          ...(detail.language_editions || [])
            .map((entry) => String(entry?.workno || '').toUpperCase())
            .filter(Boolean),
        ]);
        const duplicateLanguageEditionId =
          [...languageEditionIds].find((id) => selectedLanguageEditionOwner.has(id)) || null;
        const duplicateLanguageEditionOf = duplicateLanguageEditionId
          ? selectedLanguageEditionOwner.get(duplicateLanguageEditionId)
          : null;

        if (duplicateLanguageEditionOf) {
          audit.push({
            product_id: candidate.product_id,
            source_ranking_rank: candidate.source_ranking_rank,
            decision: 'excluded_language_edition_duplicate',
            detail_fetch_attempts: attempts,
            duplicate_of_product_id: duplicateLanguageEditionOf,
            duplicate_via_language_edition_id: duplicateLanguageEditionId,
            language_edition_ids: [...languageEditionIds].sort(),
            release_year: releaseYear,
            release_date_text: detail.release_date_text || null,
          });
          console.log(
            `[${year}] excluded language-edition duplicate: source rank ${candidate.source_ranking_rank} ${candidate.product_id} -> ${duplicateLanguageEditionOf}`,
          );
          await sleep(detailDelayMs);
          continue;
        }

        const releaseYearRank = items.length + 1;
        items.push({
"""
if old in s:
    s = s.replace(old, new, 1)
else:
    old_lookup = """        const duplicateLanguageEditionOf =
          [...languageEditionIds].find((id) => selectedLanguageEditionIds.has(id)) || null;
"""
    new_lookup = """        const duplicateLanguageEditionId =
          [...languageEditionIds].find((id) => selectedLanguageEditionOwner.has(id)) || null;
        const duplicateLanguageEditionOf = duplicateLanguageEditionId
          ? selectedLanguageEditionOwner.get(duplicateLanguageEditionId)
          : null;
"""
    if old_lookup not in s:
        raise SystemExit('collector duplicate lookup anchor not found')
    s = s.replace(old_lookup, new_lookup, 1)
    s = s.replace(
        "            duplicate_of_product_id: duplicateLanguageEditionOf,\n",
        "            duplicate_of_product_id: duplicateLanguageEditionOf,\n            duplicate_via_language_edition_id: duplicateLanguageEditionId,\n",
        1,
    )

old = """          release_year_rank: releaseYearRank,
        });
        audit.push({
"""
new = """          release_year_rank: releaseYearRank,
        });
        for (const id of languageEditionIds) selectedLanguageEditionOwner.set(id, candidate.product_id);
        audit.push({
"""
if old in s:
    s = s.replace(old, new, 1)
else:
    old_owner = '        for (const id of languageEditionIds) selectedLanguageEditionIds.add(id);'
    new_owner = '        for (const id of languageEditionIds) selectedLanguageEditionOwner.set(id, candidate.product_id);'
    if old_owner not in s and new_owner not in s:
        raise SystemExit('collector owner registration anchor not found')
    s = s.replace(old_owner, new_owner, 1)

s = s.replace('schema_version: 2,', 'schema_version: 3,', 1)
s = s.replace(
    "definition: 'DLsite yearly sales ranking traversed from the top; only works released in the same calendar year are retained, preserving the source ranking order.',",
    "definition: 'DLsite yearly sales ranking traversed from the top; only works released in the same calendar year are retained, preserving source ranking order; language editions of the same underlying work are counted once.',",
    1,
)

required = [
    'selectedLanguageEditionOwner = new Map()',
    'duplicate_via_language_edition_id',
    'selectedLanguageEditionOwner.set(id, candidate.product_id)',
]
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit(f'missing dedupe patch components: {missing}')

p.write_text(s)
