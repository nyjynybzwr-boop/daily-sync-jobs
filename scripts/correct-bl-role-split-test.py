from pathlib import Path

p = Path('scripts/fix-bl-role-target-split.sh')
s = p.read_text()
old = """  {
    name: 'BL no marker stays unknown instead of convention-defaulting (RJ01661916)',
    run: () => {
      const l = labelsOf(fixtures.RJ01661916);
      return l.has('アナル責め(受け攻め不明)') && l.has('フェラ(受け攻め不明)')
        && !l.has('アナル責め') && !l.has('フェラ');
    },
  },"""
new = """  {
    name: 'BL explicit 逆転無し keeps conventional targets (RJ01661916)',
    run: () => {
      const l = labelsOf(fixtures.RJ01661916);
      return l.has('アナル責め(受け)') && l.has('フェラ(攻め)')
        && !l.has('アナル責め') && !l.has('フェラ')
        && !l.has('アナル責め(受け攻め不明)') && !l.has('フェラ(受け攻め不明)');
    },
  },"""
if old not in s:
    raise SystemExit('fixture expectation anchor not found')
p.write_text(s.replace(old, new, 1))
