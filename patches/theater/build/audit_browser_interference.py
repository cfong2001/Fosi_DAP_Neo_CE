#!/usr/bin/env python3
"""Demonstrate current setup-hook interference on a browser-style decode.

This is a known-defect reproducer, not a passing isolation regression.
It calls the shared stock artwork setup entry with a browser-sized request;
the window manager and browser driver are not emulated here.
"""
import struct
import tempfile

from test_theater_lifecycle import BGCELL, Player, build_variant


def main():
    with tempfile.TemporaryDirectory(prefix='theater-browser-') as tmp:
        raw = build_variant(tmp)
        p = Player(raw, 30, 18)
        assert p.setup() == 1
        p.call(0x03083B36)
        before = p.state()
        assert before['flags'] & 1 and before['seen'] == 1
        p.u.mem_write(BGCELL, struct.pack('<H', 0x4567))
        p.w32(0x0302598C, 36)
        p.w32(0x03025990, 36)
        p.cursor = 0
        assert p.setup() == 1
        after = p.state()
        assert p.r16(BGCELL) == 0x10a2
        assert after['seen'] == 0 and after['flags'] == 1
        print('KNOWN GAP: shared browser-size setup resets player theater state and background')


if __name__ == '__main__':
    main()
