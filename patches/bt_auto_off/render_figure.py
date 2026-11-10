#!/usr/bin/env python3
"""Render media/bt_auto_off.png: how long Bluetooth stays on without a
connection in stock and each option. The on/off spans are measured by
running the firmware's supervisor under Unicorn (emu_supervisor.py) on
images built by build.py; the first tick that switches off is found
by bisection.

Usage: python3 render_figure.py OUTPUT.png [STOCK_IMAGE]  (matplotlib, unicorn)
"""
import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / 'patches' / 'framework'))
sys.path.insert(0, str(HERE))
import build as fw  # noqa: E402
from emu_supervisor import auto_off  # noqa: E402

stock = (Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / 'DP3_V137.img').read_bytes()
base = fw.load_manifest(REPO / 'patches' / 'framework' / 'patches' / 'manifest.txt')
rows = [('Stock', stock)]
for name, label in (('10min', '--bt-auto-off 10min'), ('never', '--bt-auto-off never')):
    img, _ = fw.build_image(stock, base + [fw.bt_auto_off_patch(name)], fw.DEFAULT_BUILD_DATE)
    rows.append((label, img))
HORIZON = 90000                      # 15 minutes of 10 ms ticks
BLUE, INK, INK2, GRID, SURF, OFF = '#2a78d6', '#0b0b0b', '#52514e', '#e6e5e1', '#fcfcfb', '#d9d8d3'
fig, ax = plt.subplots(figsize=(9, 2.4), facecolor=SURF)
ax.set_facecolor(SURF)
for y, (label, img) in enumerate(reversed(rows)):
    off_at = None
    if not auto_off(img, HORIZON)[0]:
        lo, hi = 0, HORIZON                  # bisect the first tick that switches off
        while hi - lo > 1:
            mid = (lo + hi) // 2
            lo, hi = (mid, hi) if auto_off(img, mid)[0] else (lo, mid)
        off_at = hi
    end = (off_at if off_at is not None else HORIZON) / 6000
    ax.barh(y, end, height=0.38, color=BLUE)
    if off_at is not None:
        ax.barh(y, 15 - end, left=end, height=0.38, color=OFF)
        ax.text(end + 0.15, y, f'off at tick {off_at:,} ({end:.0f} min), saved as Off',
                va='center', fontsize=9, color=INK)
    else:
        ax.text(15.1, y, 'stays on', va='center', fontsize=9, color=INK)
ax.set_yticks(range(len(rows)))
ax.set_yticklabels([r[0] for r in reversed(rows)], fontsize=9, color=INK)
ax.set_xlim(0, 18)
ax.set_xticks(range(0, 16, 5))
ax.set_xlabel('Minutes with Bluetooth on and no device connected', fontsize=9, color=INK2)
ax.grid(axis='x', color=GRID, lw=0.8)
ax.set_axisbelow(True)
for s in ('top', 'right', 'left'):
    ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(GRID)
ax.tick_params(colors=INK2, labelsize=8, length=0)
fig.text(0.01, 0.01, "Firmware supervisor run under Unicorn on each build; the switch-off tick found by bisection.",
         fontsize=8, color=INK2)
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig(sys.argv[1], dpi=200, facecolor=SURF)
