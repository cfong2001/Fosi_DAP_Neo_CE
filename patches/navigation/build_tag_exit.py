#!/usr/bin/env python3
"""Build a tag-library disarm candidate; it is not installed in firmware."""
import argparse
from pathlib import Path
import subprocess
import tempfile
from build_exit import branch

HERE = Path(__file__).resolve().parent
BASE = 0x0307EDEC  # end of stock module 24 code
LIMIT = 0x0307EE48 # module 31's original code end, not a proven RAM boundary


def run(*args):
    return subprocess.run(args, check=True, text=True, capture_output=True).stdout


def build(prefix):
    with tempfile.TemporaryDirectory(prefix='navigation-tag-') as tmp:
        d = Path(tmp)
        obj, elf, binary, linker = [d / n for n in ('nav.o', 'nav.elf', 'nav.bin', 'nav.ld')]
        linker.write_text(f'SECTIONS {{ . = {BASE:#x}; .text : {{ *(.text*) }} }}\n')
        run(prefix + 'as', '-mcpu=cortex-m3', '-mthumb', '-o', str(obj), str(HERE / 'tag_exit.S'))
        run(prefix + 'ld', '-T', str(linker), '-o', str(elf), str(obj))
        run(prefix + 'objcopy', '-O', 'binary', str(elf), str(binary))
        symbols = {}
        for line in run(prefix + 'nm', '-n', str(elf)).splitlines():
            cols = line.split()
            if len(cols) == 3:
                symbols[cols[2]] = int(cols[0], 16)
        blob = bytearray(binary.read_bytes())
        at = symbols['tag_continue']
        blob[at-BASE:at-BASE+4] = branch(at, 0x0307EC76)
        if BASE + len(blob) > LIMIT:
            raise ValueError('candidate crosses comparison boundary')
        return bytes(blob), branch(0x0307EC72, symbols['tag_start'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prefix', default='arm-none-eabi-')
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    blob, patch = build(a.prefix)
    a.output.write_bytes(blob)
    print(f'{len(blob)} bytes at 0x{BASE:08x}; site replacement {patch.hex()}')


if __name__ == '__main__':
    main()
