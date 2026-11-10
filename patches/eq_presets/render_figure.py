#!/usr/bin/env python3
"""Render media/eq_presets.png. Left: the curve each stock menu item
applies (arrays chosen by the stock selector under Unicorn, responses from
the firmware's own band filters at 48 kHz). Right: the AutoEQ Sennheiser
HD 600 target and what the fitted gains produce on the same filters.

Usage: python3 render_figure.py OUTPUT.png   (matplotlib, unicorn)
"""
import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import eqfit  # noqa: E402
from test_eq_presets import selected_array  # noqa: E402

raw = (eqfit.REPO / 'DP3_V137.img').read_bytes()
R = eqfit.band_table(raw)
realised = lambda g: [sum(R[b][g[b] + 12][i] for b in range(31)) for i in range(len(eqfit.GRID))]  # noqa: E731
COLORS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#6250d6']
INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#e6e5e1', '#fcfcfb'
fig, (a, b) = plt.subplots(1, 2, figsize=(11, 3.6), facecolor=SURF, sharey=True)
for n in range(1, 7):
    g = selected_array(raw, n)
    a.plot(eqfit.GRID, realised(g), color=COLORS[n - 1], lw=2,
           ls='--' if n in (4, 5) else '-', label=eqfit.SLOTS[n] + (' (= Pop)' if n == 4 else ' (= Jazz)' if n == 5 else ' (flat)' if n == 6 else ''))
a.set_title('Stock: what each menu item applies', loc='left', fontsize=10, color=INK)
a.legend(fontsize=8, frameon=False, ncol=2, loc='lower left')
pts = eqfit.parse_curve((HERE / 'fixtures' / 'Sennheiser_HD_600_GraphicEQ.txt').read_text())
gains, rms, _ = eqfit.fit(pts, R)
b.plot(eqfit.GRID, [eqfit.target_at(pts, f) for f in eqfit.GRID], color='#9b9a94', lw=3, label='AutoEQ target')
b.axvline(eqfit.TREBLE_HOLD, color=GRID, lw=1.5, ls=':')
b.text(eqfit.TREBLE_HOLD * 0.93, 1.5, 'held above\n16 kHz', fontsize=8, color=INK2, ha='right')
b.plot(eqfit.GRID, realised(gains), color=COLORS[0], lw=2, label=f'Fitted 31-band gains ({rms:.1f} dB rms)')
b.set_title('AutoEQ Sennheiser HD 600, fitted to the firmware EQ', loc='left', fontsize=10, color=INK)
b.legend(fontsize=8, frameon=False, loc='lower left')
for ax in (a, b):
    ax.set_facecolor(SURF)
    ax.set_xscale('log')
    ax.set_xlim(20, 20000)
    ax.set_xticks([20, 100, 1000, 10000])
    ax.set_xticklabels(['20 Hz', '100 Hz', '1 kHz', '10 kHz'])
    ax.grid(color=GRID, lw=0.8)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8, length=0)
a.set_ylabel('dB', color=INK2, fontsize=9)
fig.text(0.01, 0.01, 'Responses computed from the firmware coefficient tables (module 35, 48 kHz set); AutoEQ data (c) Jaakko Pasanen, MIT.',
         fontsize=8, color=INK2)
fig.tight_layout(rect=(0, 0.05, 1, 1))
fig.savefig(sys.argv[1], dpi=200, facecolor=SURF)
