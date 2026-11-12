#!/usr/bin/env python3
"""Emulation gate for census_dead.py: run the repository's Unicorn suites
with a coverage hook and check that no candidate byte ever executes.

Each suite runs as in CI; covhook/sitecustomize.py records the module 0
addresses executed. A candidate any suite executes is a census false
positive and is dropped. Writes coverage.json (executed address count per
suite, and the surviving candidates).

Usage: run_coverage.py [--json OUT]
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import census_dead  # noqa: E402

SUITES = [
    ['tools/emu_bt_uart.py'],
    ['patches/dac_filter/test_dac_filter.py'],
    ['patches/bt_auto_off/test_bt_auto_off.py'],
    ['patches/eq_presets/test_eq_presets.py'],
    ['patches/gapless/rig/test_transition.py'],
    ['patches/antialias/test_screens.py'],
    ['patches/design_refresh_v4/test_keyed_transport.py'],
]


def main():
    r = census_dead.census(ROOT / 'release' / 'DP3_V137_CE.img')
    cands = [c for c in r['candidates'] if c['tier']]
    per, allhits = {}, set()
    for suite in SUITES:
        with tempfile.NamedTemporaryFile('r', suffix='.cov', delete=False) as t:
            path = t.name
        env = dict(os.environ, FOSI_COV_OUT=path,
                   PYTHONPATH=str(HERE / 'covhook') + os.pathsep + os.environ.get('PYTHONPATH', ''))
        p = subprocess.run([sys.executable, str(ROOT / suite[0])] + suite[1:], cwd=ROOT,
                           env=env, capture_output=True, text=True)
        hits = {int(x, 16) for x in Path(path).read_text().split()}
        os.unlink(path)
        per[suite[0]] = {'exit': p.returncode, 'module0_addresses': len(hits)}
        allhits |= hits
        print(f'{suite[0]}: exit {p.returncode}, {len(hits)} module 0 addresses')
    killed = [c for c in cands if any(c['start'] <= a < c['end'] for a in allhits)]
    survive = [c for c in cands if c not in killed]
    print(f'executed module 0 addresses (union): {len(allhits)}')
    print(f'candidates executed (census false positives): {len(killed)}')
    for c in killed:
        print(f"  {c['start']:#010x}..{c['end']:#010x}")
    print(f'surviving: {len(survive)}, {sum(c["bytes"] for c in survive)} B')
    if '--json' in sys.argv:
        Path(sys.argv[sys.argv.index('--json') + 1]).write_text(json.dumps(
            {'suites': per, 'executed_union': len(allhits),
             'false_positives': killed, 'surviving': survive}, indent=1) + '\n')
    return 1 if killed or any(v['exit'] for v in per.values()) else 0


if __name__ == '__main__':
    sys.exit(main())
