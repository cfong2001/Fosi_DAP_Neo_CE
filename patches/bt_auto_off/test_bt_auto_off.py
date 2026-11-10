#!/usr/bin/env python3
"""Build each --bt-auto-off option and run the firmware's Bluetooth
supervisor on it under Unicorn (emu_supervisor.py).

Expected, with Bluetooth on:
  stock  off after 30,000 ticks (5 min) without a connection
  10min  off after 60,000 ticks (10 min) without a connection
  never  never off for lack of a connection
and in every image Bluetooth stays on while a device is connected.

Usage: python3 test_bt_auto_off.py [STOCK_IMAGE]   (needs unicorn)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / 'patches' / 'framework'))
sys.path.insert(0, str(HERE))
import build as fw  # noqa: E402
from emu_supervisor import auto_off  # noqa: E402

ELAPSED = (0, 29999, 30001, 59999, 60001, 10_000_000)
LIMIT = {'stock': 30000, '10min': 60000, 'never': None}


def main():
    stock = (Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / 'DP3_V137.img').read_bytes()
    base = fw.load_manifest(REPO / 'patches' / 'framework' / 'patches' / 'manifest.txt')
    images = {'stock': stock}
    for name in fw.BT_AUTO_OFF:
        images[name], _ = fw.build_image(stock, base + [fw.bt_auto_off_patch(name)],
                                         fw.DEFAULT_BUILD_DATE)
    print(f'{"ticks without a connection":<28}' + ''.join(f'{n:>8}' for n in images))
    failures = 0
    for elapsed in ELAPSED:
        row = []
        for name, raw in images.items():
            on, _, _ = auto_off(raw, elapsed, connected=0)
            limit = LIMIT[name]
            want_on = limit is None or elapsed <= limit
            failures += bool(on) != want_on
            row.append(('on' if on else 'OFF') + ('' if bool(on) == want_on else '!'))
        print(f'{elapsed:>9} ({elapsed / 6000:6.1f} min)        ' + ''.join(f'{r:>8}' for r in row))
    for name, raw in images.items():
        on, _, _ = auto_off(raw, 10_000_000, connected=1)
        failures += not on
    if failures:
        raise SystemExit(f'FAIL: {failures} case(s)')
    print('OK: stock 5 min, 10min option 10 min, never option never; connected always stays on')


if __name__ == '__main__':
    main()
