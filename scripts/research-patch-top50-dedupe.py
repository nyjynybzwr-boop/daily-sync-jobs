from pathlib import Path

p = Path('scripts/backfill-release-year-sales-top50.mjs')
s = p.read_text()

old = """  const items = [];
  const audit = [];
  let stoppedReason = null;
"""
new = """  const items = [];
  const audit = [];
  const selectedLanguageEditionIds = new Set();
  let stoppedReason = null;
"""
if old not in s and 'selectedLanguageEditionIds' not in s:
    raise SystemExit('collector anchor 1 not found')
if old in s:
    s = s.replace(old, new, 1)

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
        const duplicateLanguageEditionOf =
          [...languageEditionIds].find((id) => selectedLanguageEditionIds.has(id)) || null;

        if (duplicateLanguageEditionOf) {
          audit.push({
            product_id: candidate.product_id,
            source_ranking_rank: candidate.source_ranking_rank,
            decision: 'excluded_language_edition_duplicate',
            detail_fetch_attempts: attempts,
            duplicate_of_product_id: duplicateLanguageEditionOf,
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
if old not in s and 'duplicateLanguageEditionOf' not in s:
    raise SystemExit('collector anchor 2 not found')
if old in s:
    s = s.replace(old, new, 1)

old = """          release_year_rank: releaseYearRank,
        });
        audit.push({
"""
new = """          release_year_rank: releaseYearRank,
        });
        for (const id of languageEditionIds) selectedLanguageEditionIds.add(id);
        audit.push({
"""
if old not in s and 'selectedLanguageEditionIds.add' not in s:
    raise SystemExit('collector anchor 3 not found')
if old in s:
    s = s.replace(old, new, 1)

s = s.replace('schema_version: 2,', 'schema_version: 3,', 1)
s = s.replace(
    "definition: 'DLsite yearly sales ranking traversed from the top; only works released in the same calendar year are retained, preserving the source ranking order.',",
    "definition: 'DLsite yearly sales ranking traversed from the top; only works released in the same calendar year are retained, preserving source ranking order; language editions of the same underlying work are counted once.',",
    1,
)
p.write_text(s)
