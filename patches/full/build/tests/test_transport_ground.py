#!/usr/bin/env python3
"""Transport glyph repaints in the composed image leave no ghost pixels.

Reuses the machine from patches/design_refresh_v4/test_keyed_transport.py
(real module 0, 18 and 27 code, real pixel store, framebuffer readback) on
patches/full/out/DP3_V137_CE_full.img, where the eight transport draws go
through transport_keyed_draw: fill the glyph rectangle with the ground
cell, then draw keyed.

Gates, each over a screen pre-filled with a theater-derived ground:
  c1  B = 0, play to pause at the centre, segment-only repaint.
  c2  B = 2, chevron to pause at the computed slot, segment-only repaint.
  A ghost is a pixel where the repaint differs from painting the second
  state alone on a clean ground; both gates require none.
  b   Every keyed transport draw is preceded by a fill of exactly its rectangle in
      the ground colour, and no pixel store carries the key colour 0xF800.
The same c1 and c2 sequences on the standalone v4 build (no wrapper)
leave 58 and 34 ghost pixels; that build is run as the negative control.
"""
import importlib.util
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
IMAGE = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    REPO / 'patches' / 'full' / 'out' / 'DP3_V137_CE_full.img'

spec = importlib.util.spec_from_file_location(
    'keyed', REPO / 'patches' / 'design_refresh_v4' / 'test_keyed_transport.py')
kt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kt)

GROUND = kt.GROUND
KEY = kt.KEY
IDS = [155, 156] + list(range(157, 182)) + list(range(286, 290))
CENTRE = (104, 275, 32, 32)
SLOT = (4, 275, 32, 32)


def paint(image, states):
    """Run the painter for each (A, B, play) state over a ground screen."""
    m = kt.Machine(image, real_store=True)
    m.stage(IDS)
    kt.fb_fill(m, GROUND)
    for a, b, play in states:
        m.painter(state_a=a, state_b=b, play=play, ground=GROUND)
    return m


def ghosts(image, first, second, rect):
    """Pixels where repainting `second` over `first` differs from painting
    `second` alone on a clean ground: ink the repaint failed to remove."""
    m = paint(image, [first, second])
    fresh = paint(image, [second])
    got, want = kt.fb_read(m, *rect), kt.fb_read(fresh, *rect)
    return m, {p: (got[p], want[p]) for p in want if got[p] != want[p]}


def c1(image):
    return ghosts(image, (0, 0, 1), (0, 0, 0), CENTRE)


def c2(image):
    return ghosts(image, (1, 2, 1), (11, 2, 1), SLOT)


def main():
    image = IMAGE.read_bytes()
    print(f'image sha256 {hashlib.sha256(image).hexdigest()}')

    m, g = c1(image)
    assert not g, f'c1: {len(g)} ghost pixels, e.g. {sorted(g.items())[:4]}'
    print('PASS c1: B=0 play to pause, segment-only repaint, 0 ghost pixels')

    # b: each keyed draw follows a ground fill of its own rectangle
    log = m.drawlog
    # transport row draws only; the stock play-mode indicator also uses
    # the keyed helper, after its own fill, at (53, 5)
    draws = [i for i, e in enumerate(log)
             if e[0] == 'draw' and e[1] == kt.HELPER and e[4] == 275]
    assert draws, 'no keyed draws'
    for i in draws:
        _, _, rid, x, y = log[i]
        prev = log[i - 1]
        width = 240 if rid in (155, 156) else 32
        assert prev[0] == 'fill' and prev[1:] == (
            x, y, x + width - 1, y + 31, GROUND), (prev, log[i])
    assert all(v != KEY for _, _, v in m.stores), 'key colour stored'
    print(f'PASS b: all {len(draws)} keyed draws follow a ground fill of '
          f'their own rectangle; no key-colour stores')

    m, g = c2(image)
    assert not g, f'c2: {len(g)} ghost pixels, e.g. {sorted(g.items())[:4]}'
    print('PASS c2: B=2 chevron to pause, segment-only repaint, 0 ghost pixels')

    # Negative control: the standalone v4 build keeps the direct repoints.
    v4, _ = kt.build_v4_image()
    _, g1 = c1(v4)
    _, g2 = c2(v4)
    assert g1 and g2, (len(g1), len(g2))
    print(f'PASS control: the standalone v4 build leaves {len(g1)} and '
          f'{len(g2)} ghost pixels in the same sequences')
    print('ALL PASS: transport repaints in the composed image')


if __name__ == '__main__':
    main()
