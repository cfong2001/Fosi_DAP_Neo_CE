#!/usr/bin/env python3
"""Render media/dac_filters.png from the CS43198 datasheet (DS1156F2,
Table 3-7, single-speed mode) at Fs = 44.1 kHz. Every number is the
datasheet's, scaled by Fs; nothing is measured on a device.

Usage: python3 render_figure.py OUTPUT.png   (needs matplotlib)
"""
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

FS = 44.1  # kHz
# name, group delay (x/Fs), -0.01 dB passband edge (x Fs), stopband attenuation dB
ROWS = [
    ('Fast, low latency (stock)', 6.3, 0.4535, 110),
    ('Fast, linear phase', 39.5, 0.4535, 110),
    ('Slow, low latency', 5.6, 0.417, 64),
    ('Slow, linear phase', 34.5, 0.417, 64),
    ('NOS', 2.7, 0.026, None),
]
BLUE, INK, INK2, GRID, SURF = '#2a78d6', '#0b0b0b', '#52514e', '#e6e5e1', '#fcfcfb'
panels = [
    ('Group delay (ms)', [r[1] / FS for r in ROWS], lambda v: f'{v:.2f}', 1.15),
    ('Flat to within 0.01 dB (kHz)', [r[2] * FS for r in ROWS], lambda v: f'{v:.1f}', 24),
    ('Rejection above the band (dB)', [r[3] or 0 for r in ROWS], lambda v: f'{v:.0f}', 135),
]
fig, axes = plt.subplots(1, 3, figsize=(11, 3.2), sharey=True, facecolor=SURF)
y = list(range(len(ROWS)))[::-1]
for ax, (title, vals, fmt, xmax) in zip(axes, panels):
    ax.set_facecolor(SURF)
    for yi, v, row in zip(y, vals, ROWS):
        if v:
            ax.add_patch(FancyBboxPatch((0, yi - 0.17), v, 0.34,
                         boxstyle='round,pad=0,rounding_size=0.06',
                         mutation_aspect=xmax / 5, fc=BLUE, ec='none'))
            ax.text(v + xmax * 0.02, yi, fmt(v), va='center', fontsize=9, color=INK)
        else:
            ax.text(xmax * 0.02, yi, 'not specified: no interpolation filter', va='center',
                    fontsize=9, color=INK2)
    ax.set_xlim(0, xmax)
    ax.set_ylim(-0.6, len(ROWS) - 0.4)
    ax.set_title(title, fontsize=10, color=INK, loc='left')
    ax.grid(axis='x', color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8, length=0)
axes[0].set_yticks(y)
axes[0].set_yticklabels([r[0] for r in ROWS], fontsize=9, color=INK)
axes[1].text(0.026 * FS + 24 * 0.12, 0, 'then falls gradually,\n3.2 dB down at 20 kHz',
             va='center', fontsize=8, color=INK2)
fig.text(0.01, 0.01, 'CS43198 datasheet DS1156F2, Table 3-7, single-speed mode, scaled to 44.1 kHz.',
         fontsize=8, color=INK2)
fig.tight_layout(rect=(0, 0.05, 1, 1))
fig.savefig(sys.argv[1], dpi=200, facecolor=SURF)
