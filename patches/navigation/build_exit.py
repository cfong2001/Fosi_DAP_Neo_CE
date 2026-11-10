#!/usr/bin/env python3
"""Build a candidate playlist-disarm extension, for research only.

The candidate is linked immediately after the current 7,168-byte M3U
module-31 payload. It is NOT installed by the shipped configurator. Hook
site selection and playback behavior require end-to-end/hardware review.
"""
import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
BASE = 0x03080A48
END = 0x03080B54


def branch(site, target, link=False):
    delta = target - (site + 4)
    if delta & 1 or not -(1 << 24) <= delta < 1 << 24:
        raise ValueError('invalid branch displacement')
    s, i1, i2 = (delta >> 24) & 1, (delta >> 23) & 1, (delta >> 22) & 1
    j1, j2 = (~(i1 ^ s)) & 1, (~(i2 ^ s)) & 1
    return struct.pack('<HH', 0xf000 | (s << 10) | ((delta >> 12) & 0x3ff),
                       (0xd000 if link else 0x9000) | (j1 << 13) | (j2 << 11) | ((delta >> 1) & 0x7ff))


def run(*cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def build(prefix):
    with tempfile.TemporaryDirectory(prefix='navigation-') as td:
        d = Path(td)
        obj, elf, blob, linker = [d / n for n in ('nav.o', 'nav.elf', 'nav.bin', 'nav.ld')]
        linker.write_text(f'SECTIONS {{ . = {BASE:#x}; .text : {{ *(.text*) }} }}\n')
        run(prefix + 'as', '-mcpu=cortex-m3', '-mthumb', '-o', str(obj), str(HERE / 'playlist_exit.S'))
        run(prefix + 'ld', '-T', str(linker), '-o', str(elf), str(obj))
        run(prefix + 'objcopy', '-O', 'binary', str(elf), str(blob))
        symbols = {}
        for line in run(prefix + 'nm', '-n', str(elf)).splitlines():
            cols = line.split()
            if len(cols) == 3:
                symbols[cols[2]] = int(cols[0], 16)
        data = bytearray(blob.read_bytes())
        for label, dest, link in [('folder_continue', 0x0307E052, False),
                                  ('file_call', 0x030570A4, True),
                                  ('file_continue', 0x0307E1D2, False)]:
            at = symbols[label]
            data[at-BASE:at-BASE+4] = branch(at, dest, link)
        if BASE + len(data) > END:
            raise ValueError('candidate exceeds module 31 extension budget')
        sites = {'folder': branch(0x0307E04E, symbols['folder_start']),
                 'file': branch(0x0307E1CC, symbols['file_start']) + b'\x00\xbf'}
        return bytes(data), symbols, sites


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prefix', default='arm-none-eabi-')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    data, syms, sites = build(a.prefix)
    a.output.write_bytes(data)
    print(f'{len(data)} bytes; SHA-256 {hashlib.sha256(data).hexdigest()}')
    for name in ('folder', 'file'):
        print(f'{name}: {sites[name].hex()}')
    for name in ('folder_start', 'file_start'):
        print(f'{name}: 0x{syms[name]:08x}')


if __name__ == '__main__':
    main()
