from pathlib import Path
import json

core = Path('scripts/lib/analysis-core.mjs')
s = core.read_text()

old_export = "export const DERIVED_ACTOR_TARGET_LABEL = /(?:男性|女性|攻め|受け)\\)$/;"
new_export = "const ACTOR_TARGET_SUFFIX_RE = /\\((?:男性|女性|性別不明|攻め|受け|受け攻め不明)\\)$/;\nexport const DERIVED_ACTOR_TARGET_LABEL = ACTOR_TARGET_SUFFIX_RE;\nconst canonicalPlayLabel = (label = '') => String(label).replace(ACTOR_TARGET_SUFFIX_RE, '');"
if old_export in s:
    s = s.replace(old_export, new_export, 1)
elif 'const ACTOR_TARGET_SUFFIX_RE' not in s:
    raise SystemExit('actor-target suffix anchor not found')

new_role_block = r'''const BL_ROLE_TARGET_RULES = {
  'アナル責め': {
    defaultTarget: '受け',
    ukeTarget: [
      /受け(?:の)?(?:アナル|尻|ケツ)/,
      /受け(?:を|に)[^。！？\n]{0,16}(?:アナル責め|アナル開発|アナル拡張)/,
      /(?:アナル責め|アナル開発|アナル拡張)[^。！？\n]{0,16}受け/,
    ],
    semeTarget: [
      /攻め(?:の)?(?:アナル|尻|ケツ)/,
      /攻め(?:を|に)[^。！？\n]{0,16}(?:アナル責め|アナル開発|アナル拡張)/,
      /(?:アナル責め|アナル開発|アナル拡張)[^。！？\n]{0,16}攻め/,
      /逆アナル/,
    ],
  },
  '乳首責め': {
    defaultTarget: '受け',
    ukeTarget: [
      /受け(?:の)?乳首/,
      /受け(?:を|に)[^。！？\n]{0,16}乳首(?:責め|攻め|弄り|いじり|舐め)/,
      /乳首(?:責め|攻め|弄り|いじり|舐め)[^。！？\n]{0,16}受け/,
    ],
    semeTarget: [
      /攻め(?:の)?乳首/,
      /攻め(?:を|に)[^。！？\n]{0,16}乳首(?:責め|攻め|弄り|いじり|舐め)/,
      /乳首(?:責め|攻め|弄り|いじり|舐め)[^。！？\n]{0,16}攻め/,
    ],
  },
  'フェラ': {
    defaultTarget: '攻め',
    ukeTarget: [
      /攻めフェラ/,
      /攻め(?:が|は)[^。！？\n]{0,12}フェラ/,
      /受け(?:に|へ)[^。！？\n]{0,8}フェラ/,
    ],
    semeTarget: [
      /受けフェラ/,
      /受け(?:が|は)[^。！？\n]{0,12}フェラ/,
      /攻め(?:に|へ)[^。！？\n]{0,8}フェラ/,
    ],
  },
};
const BL_ROLE_RIBA_RE = /(?:^|[^ぁ-んァ-ヶ一-龠])リバ(?:$|[^ぁ-んァ-ヶ一-龠]|プレイ|設定|要素)/;
const BL_ROLE_GENERIC_REVERSAL_RE = /逆レ|逆NTR|リバース|攻め受け交代|受け攻め交代|攻め受け入れ替|受け攻め入れ替|攻め受け兼任|受け攻め兼任/;
const BL_ROLE_NO_REVERSAL_RE = /逆転無し|反転無し|逆転(?:は)?(?:あり)?ません/;
const matchesAny = (text, patterns = []) => patterns.some((pattern) => pattern.test(text));

function detectBLRoleTarget(item, rawCorpus, matched) {
  const results = [];
  for (const [label, cfg] of Object.entries(BL_ROLE_TARGET_RULES)) {
    if (!matched.some((m) => m.label === label)) continue;
    const explicitUke = matchesAny(rawCorpus, cfg.ukeTarget);
    const explicitSeme = matchesAny(rawCorpus, cfg.semeTarget);
    const ambiguousRoleSystem = BL_ROLE_RIBA_RE.test(rawCorpus) || BL_ROLE_GENERIC_REVERSAL_RE.test(rawCorpus);
    const confirmedNoReversal = BL_ROLE_NO_REVERSAL_RE.test(rawCorpus);

    let target = '受け攻め不明';
    let evidence = 'no label-specific BL role evidence';
    if (explicitUke !== explicitSeme) {
      target = explicitUke ? '受け' : '攻め';
      evidence = `explicit ${target} target evidence`;
    } else if (!explicitUke && !explicitSeme && confirmedNoReversal && !ambiguousRoleSystem) {
      target = cfg.defaultTarget;
      evidence = `explicit no-reversal marker -> conventional ${target} target`;
    } else if (explicitUke && explicitSeme) {
      evidence = 'both uke and seme target evidence';
    } else if (ambiguousRoleSystem) {
      evidence = 'generic reversal/riba marker without label-specific target evidence';
    }

    results.push({
      label: `${label}(${target})`,
      category: labelToCategory.get(label) || 'play',
      matched_keywords: [`derived from ${label}: ${evidence}`],
    });
  }
  return results;
}

'''
start_marker = "const BL_ROLE_TARGET_RULES = {"
end_marker = "function detectActorTarget"
start = s.index(start_marker)
end = s.index(end_marker, start)
current_block = s[start:end]
if '受け攻め不明' not in current_block or 'BL_ROLE_GENERIC_REVERSAL_RE' not in current_block:
    s = s[:start] + new_role_block + s[end:]

old_bl = """  if (isBL) {\n    matched.push(...detectBLRoleTarget(item, rawCorpus, matched));\n  } else if (!isMangaItem(item)) {"""
new_bl = """  if (isBL) {\n    const blRoleTargets = detectBLRoleTarget(item, rawCorpus, matched);\n    matched.push(...blRoleTargets);\n    const splitBases = new Set(Object.keys(BL_ROLE_TARGET_RULES));\n    matched = matched.filter((m) => !splitBases.has(m.label));\n  } else if (!isMangaItem(item)) {"""
if old_bl in s:
    s = s.replace(old_bl, new_bl, 1)
elif 'const blRoleTargets = detectBLRoleTarget' not in s:
    raise SystemExit('BL detectLabels fold anchor not found')

old_score = "const playLabelRows = labelDetails.filter((row) => row.category === 'play' && !DERIVED_ACTOR_TARGET_LABEL.test(row.label));\n  const playLabelCount = playLabelRows.length;"
new_score = """const playLabelMap = new Map();\n  for (const row of labelDetails.filter((entry) => entry.category === 'play')) {\n    const baseLabel = canonicalPlayLabel(row.label);\n    if (!playLabelMap.has(baseLabel)) playLabelMap.set(baseLabel, { ...row, label: baseLabel });\n  }\n  const playLabelRows = [...playLabelMap.values()];\n  const playLabelCount = playLabelRows.length;"""
if old_score in s:
    s = s.replace(old_score, new_score, 1)
elif 'const playLabelMap = new Map();' not in s:
    raise SystemExit('play fallback canonicalization anchor not found')

old_intensity = "const labels = new Set(labelDetails.map((row) => row.label));"
new_intensity = "const labels = new Set(labelDetails.flatMap((row) => [row.label, canonicalPlayLabel(row.label)]));"
if old_intensity in s:
    s = s.replace(old_intensity, new_intensity, 1)
elif 'canonicalPlayLabel(row.label)' not in s:
    raise SystemExit('play intensity canonicalization anchor not found')

core.write_text(s)

taxp = Path('config/label-taxonomy.json')
tax = json.loads(taxp.read_text())
play = tax['categories']['play']
for after, label in [
    ('乳首責め(攻め)', '乳首責め(受け攻め不明)'),
    ('フェラ(受け)', 'フェラ(受け攻め不明)'),
    ('アナル責め(攻め)', 'アナル責め(受け攻め不明)'),
]:
    if label not in play:
        play.insert(play.index(after) + 1, label)
tax['version'] = max(int(tax.get('version', 0)), 19)
taxp.write_text(json.dumps(tax, ensure_ascii=False, indent=2) + '\n')

tp = Path('scripts/test-label-regression.mjs')
t = tp.read_text()
start = t.index('  // --- BL role-target')
end = t.index("  {\n    name: 'manga: unresolved-gender", start)
new_tests = r'''  // --- BL role-target: evidence-first, mutually exclusive 受け/攻め/不明 ---
  {
    name: 'BL no role evidence -> アナル責め/フェラ are 受け攻め不明 and bare labels disappear (RJ01378017)',
    run: () => {
      const l = labelsOf(fixtures.RJ01378017);
      return l.has('アナル責め(受け攻め不明)') && l.has('フェラ(受け攻め不明)')
        && !l.has('アナル責め') && !l.has('フェラ')
        && !l.has('アナル責め(受け)') && !l.has('アナル責め(攻め)');
    },
  },
  {
    name: 'BL generic 逆レ alone does not guess a specific target (RJ01397684)',
    run: () => {
      const l = labelsOf(fixtures.RJ01397684);
      return l.has('アナル責め(受け攻め不明)') && !l.has('アナル責め')
        && !l.has('アナル責め(受け)') && !l.has('アナル責め(攻め)');
    },
  },
  {
    name: 'BL explicit 逆転無し keeps conventional targets (RJ01661916)',
    run: () => {
      const l = labelsOf(fixtures.RJ01661916);
      return l.has('アナル責め(受け)') && l.has('フェラ(攻め)')
        && !l.has('アナル責め') && !l.has('フェラ')
        && !l.has('アナル責め(受け攻め不明)') && !l.has('フェラ(受け攻め不明)');
    },
  },
  {
    name: 'BL explicit 攻めフェラ -> フェラ(受け) only (RJ01394225)',
    run: () => {
      const l = labelsOf(fixtures.RJ01394225);
      return l.has('フェラ(受け)') && !l.has('フェラ')
        && !l.has('フェラ(攻め)') && !l.has('フェラ(受け攻め不明)');
    },
  },
  {
    name: 'BL 逆転無し explicitly confirms conventional target (RJ01363178)',
    run: () => {
      const l = labelsOf(fixtures.RJ01363178);
      return l.has('アナル責め(受け)') && !l.has('アナル責め')
        && !l.has('アナル責め(攻め)') && !l.has('アナル責め(受け攻め不明)');
    },
  },
  {
    name: 'otome actor/target labels never fire on a BL item (url-gated)',
    run: () => {
      const l = labelsOf(fixtures.RJ01378017);
      return !l.has('乳首責め(男性)') && !l.has('乳首責め(女性)') && !l.has('オナニー(男性)') && !l.has('オナニー(女性)');
    },
  },
'''
if 'BL explicit 逆転無し keeps conventional targets (RJ01661916)' not in t or '受け攻め不明 and bare labels disappear' not in t:
    t = t[:start] + new_tests + t[end:]
tp.write_text(t)
