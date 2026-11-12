#!/usr/bin/env python3
"""Merge the full build's theme config: design refresh v4 glyph
runs (182), the browser icon extension runs (300), the CE
splash mark runs (40), the light play-mode key runs (4) and the
antialiased screens, dialogs, progress bar and knob runs (429) and the
redrawn Font B Latin glyphs (314), Font A Latin glyphs (314) and the
power profile menu records (64), 1,647 runs total.

The eight source configs are disjoint (the theme consumer refuses
overlaps; the merge asserts it). Two outputs:

  theme-full.json        run offsets shifted by the full build's
                         total growth (both insertions sit in
                         the module area, far before the image
                         resources the runs edit, so one uniform
                         delta applies; asserted per run). This is
                         the config build.py takes.
  theme-full-stock.json  the same runs at stock offsets, for the
                         builder page, whose engine applies runs
                         before insertion.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FULL = HERE.parent
OUT = FULL / 'out'
REPO = FULL.parents[1]

# First section offset in the stock image (sysdefault): every
# insertion point is in the module area before it, and every source
# run lands in the images section far after it.
SECTION_FLOOR = 1505568


def load_runs(path):
    cfg = json.loads(path.read_text())
    assert cfg.get('version') == 1, path
    assert set(cfg) <= {'version', 'resources', 'runs', 'literal_sites'}, \
        (path, set(cfg))
    assert not cfg.get('resources'), f'{path}: unexpected resource rules'
    assert not cfg.get('literal_sites'), \
        f'{path}: literal_sites not accepted by the build'
    return cfg['runs']


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    v4 = load_runs(REPO / 'patches' / 'design_refresh_v4' / 'v4-glyphs.json')
    browser = load_runs(REPO / 'patches' / 'design_refresh_v4'
                        / 'browser_icons' / 'browser-glyphs.json')
    mark = load_runs(REPO / 'patches' / 'theme_editor' / 'ce-mark.json')
    play_mode = load_runs(REPO / 'patches' / 'design_refresh_v4'
                          / 'play_mode_light' / 'play-mode-light.json')
    screens = load_runs(REPO / 'patches' / 'antialias' / 'screens-glyphs.json')
    font = load_runs(REPO / 'patches' / 'antialias' / 'font-glyphs.json')
    font_a = load_runs(REPO / 'patches' / 'antialias' / 'font-a-glyphs.json')
    menu = load_runs(REPO / 'patches' / 'power' / 'profiles' / 'profile-menu.json')
    print(f'v4 glyph runs: {len(v4)}; browser runs: {len(browser)}; '
          f'ce mark runs: {len(mark)}; light play-mode runs: {len(play_mode)}; '
          f'screens runs: {len(screens)}; font runs: {len(font)}; '
          f'font A runs: {len(font_a)}; profile menu runs: {len(menu)}')
    labels = load_runs(REPO / 'patches/player_ui/labels.json')
    artwork = load_runs(REPO / 'patches/player_ui/artwork-resources.json')
    runs = v4 + browser + mark + play_mode + screens + font + font_a + menu + labels + artwork
    seen = []
    for r in runs:
        off = int(r['offset'], 16) if isinstance(r['offset'], str) \
            else r['offset']
        n = len(bytes.fromhex(r['expect']))
        assert off >= SECTION_FLOOR, f'run at {off:#x} below section floor'
        seen.append((off, off + n))
    seen.sort()
    for (s1, e1), (s2, e2) in zip(seen, seen[1:]):
        assert e1 <= s2, f'runs overlap: {s1:#x}..{e1:#x} vs {s2:#x}..{e2:#x}'
    growth = (len((OUT / 'payload31.bin').read_bytes())
              + len((OUT / 'tag24.bin').read_bytes()))
    print(f'growth delta: {growth} bytes')

    def shifted(delta):
        out = []
        for r in runs:
            off = int(r['offset'], 16) if isinstance(r['offset'], str) \
                else r['offset']
            out.append({'offset': off + delta,
                        'expect': r['expect'], 'replace': r['replace']})
        return {'version': 1, 'runs': out}

    stock_cfg = shifted(0)
    grown_cfg = shifted(growth)
    (OUT / 'theme-full-stock.json').write_text(
        json.dumps(stock_cfg, indent=1) + '\n')
    (OUT / 'theme-full.json').write_text(
        json.dumps(grown_cfg, indent=1) + '\n')
    for name, cfg in (('theme-full-stock.json', stock_cfg),
                      ('theme-full.json', grown_cfg)):
        data = json.dumps(cfg, indent=1).encode()
        print(f'{name}: {len(cfg["runs"])} runs, '
              f'sha256 {hashlib.sha256(data).hexdigest()}')


if __name__ == '__main__':
    main()
