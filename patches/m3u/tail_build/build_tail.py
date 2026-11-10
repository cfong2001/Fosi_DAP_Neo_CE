#!/usr/bin/env python3
"""Build the resolver-only gap-tail payload for the experimental M3U bridge.

The output is passed to build.py --tail (not the withdrawn --extension).
Its 1,192-byte zero staging area precedes resolver code linked at 0x0307c45c.
The optional Bluetooth routine starts at 0x0307c5f8 and can be appended
separately after two alignment bytes. This does not flash a device.
"""
import argparse
import hashlib
import os
import struct
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = 0x0307C45C
STAGING = 1192
HOOK_LIMIT = 0x0307C5F8 - BASE


def run(*args):
    return subprocess.run(args, check=True, text=True, capture_output=True).stdout


def bw(site, target):
    off = target - (site + 4)
    if off & 1 or not -(1 << 24) <= off < (1 << 24):
        raise ValueError('branch out of range')
    sign, i1, i2 = (off >> 24) & 1, (off >> 23) & 1, (off >> 22) & 1
    j1, j2 = (~(i1 ^ sign)) & 1, (~(i2 ^ sign)) & 1
    return struct.pack('<HH', 0xf000 | (sign << 10) | ((off >> 12) & 0x3ff),
                       0x9000 | (j1 << 13) | (j2 << 11) | ((off >> 1) & 0x7ff))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--prefix', default=os.environ.get('CROSS_COMPILE', 'arm-none-eabi-'))
    args = ap.parse_args()
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    with tempfile.TemporaryDirectory(prefix='fosi-resolver-') as tmp:
        tmp = Path(tmp)
        source = (HERE / 'src/resolver_hook.S').read_text()
        for target in ('RESUME_P', 'RESUME_C'):
            needle = 'b.w     ' + target
            if source.count(needle) != 1:
                raise ValueError(f'unexpected {target} branch count')
            source = source.replace(needle, 'b.w     .')
        asm, obj, elf, raw, ld = [tmp / f for f in ('hook.S','hook.o','hook.elf','hook.bin','hook.ld')]
        asm.write_text(source)
        ld.write_text(f'''SECTIONS {{
 . = {BASE:#x};
 .text : {{ *(.text) *(.text.*) }}
 .data : {{ *(.data) *(.data.*) }}
 .bss : {{ *(.bss) *(.bss.*) *(COMMON) }}
 /DISCARD/ : {{ *(.comment) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }}
 ASSERT(SIZEOF(.bss) == 0, "resolver requires BSS")
 ASSERT(. <= 0x0307C5F8, "resolver overlaps Bluetooth")
}}\n''')
        flags = ['-mcpu=cortex-m3','-mthumb','-Os','-ffreestanding','-fno-builtin','-nostdlib','-Wall','-Wextra','-Werror']
        cc = args.prefix + 'gcc'
        run(cc, *flags, '-c', str(asm), '-o', str(obj))
        run(cc, *flags, '-T', str(ld), str(obj), '-o', str(elf))
        symbols = run(args.prefix + 'nm', '-n', str(elf))
        for addr, name in ((BASE, 'resolver_hook_primary'), (0x0307C496, 'resolver_hook_companion')):
            if not any(line.split() == [f'{addr:08x}', 'T', name] for line in symbols.splitlines()):
                raise ValueError(f'{name} changed address')
        if run(args.prefix + 'nm', '-u', str(elf)).strip():
            raise ValueError('resolver has undefined symbols')
        run(args.prefix + 'objcopy','-O','binary',str(elf),str(raw))
        hook = bytearray(raw.read_bytes())
        instructions = list(decoder.disasm(bytes(hook), BASE))
        placeholders = [i for i in instructions if i.mnemonic == 'b.w' and i.op_str == f'#0x{i.address:x}']
        if len(placeholders) != 2:
            raise ValueError('expected two external-branch placeholders')
        for insn, target in zip(placeholders, (0x03059DB0, 0x0305B2C6)):
            offset = insn.address - BASE
            hook[offset:offset + 4] = bw(insn.address, target)
            decoded = list(decoder.disasm(hook[offset:offset + 4], insn.address))
            if len(decoded) != 1 or decoded[0].op_str != f'#0x{target:x}':
                raise ValueError('resolver branch audit failed')
        if len(hook) != 410 or len(hook) > HOOK_LIMIT:
            raise ValueError(f'resolver length changed: {len(hook)}')
        payload = bytes(STAGING) + bytes(hook)
        digest = hashlib.sha256(payload).hexdigest()
        if digest != '43f5867abaee882171466438e0a8fa0efa3f930b70339064759b993dc9a0dab4':
            raise ValueError(f'resolver tail sha256 {digest} does not match the audited build')
        args.output.write_bytes(payload)
        print(f'resolver tail {len(payload)} bytes, sha256 {digest}')


if __name__ == '__main__':
    main()
