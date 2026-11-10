#!/usr/bin/env python3
"""Compare stock and patched module-27 title copy paths in Unicorn.

Runs only the original/modified copy and suffix blocks up to the next
stock instruction, not the whole player. Seeded adjacent bytes detect
out-of-bounds writes; a nonzero sentinel detects a missing terminator.
"""
from pathlib import Path
import hashlib
import os
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R3, UC_ARM_REG_R7, UC_ARM_REG_SP

HERE = Path(__file__).resolve().parent
raw = Path(os.environ.get('FOSI_STOCK_IMAGE', ROOT / 'DP3_V137.img')).read_bytes()
if hashlib.sha256(raw).hexdigest() != 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef':
    raise ValueError('stock image SHA-256 mismatch')
im = Image(raw)
m = im.modules[27]
off, size = im.module_region(27, 'code')
code = bytearray(raw[off:off + size])


def patch_code():
    out = bytearray(code)
    for path in (HERE / 'title-copy.patch', HERE / 'title-suffix.patch'):
        fields = {}
        for line in path.read_text().splitlines():
            if line and not line.startswith(('#', ' ', '\t')) and ':' in line:
                key, value = line.split(':', 1)
                fields[key] = value.strip()
        addr = int(fields['address'], 0) - m['code_exec']
        expect, replace = bytes.fromhex(fields['expect']), bytes.fromhex(fields['replace'])
        if len(expect) != len(replace) or out[addr:addr + len(expect)] != expect:
            raise ValueError(f'{path.name}: patch precondition failed')
        out[addr:addr + len(expect)] = replace
    return out


def execute(text, patched):
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x03000000, 0x100000)
    u.mem_write(m['code_exec'], bytes(patch_code() if patched else code))
    src, dst = 0x0304adf4, 0x03024804
    u.mem_write(src, text.encode('utf-16le') + b'\0\0')
    u.mem_write(dst - 10, b'\x2e\0\x2e\0' + b'\x5a' * 6)
    u.mem_write(dst, b'\xff' * 258)
    u.reg_write(UC_ARM_REG_SP, 0x030f0000)
    u.reg_write(UC_ARM_REG_R0, dst)
    u.reg_write(UC_ARM_REG_R3, src)
    u.reg_write(UC_ARM_REG_R7, 0)
    writes = []
    def trace(_uc, _access, addr, width, value, _user):
        if dst - 10 <= addr < dst + 258:
            writes.append((addr, width, value))
    u.hook_add(UC_HOOK_MEM_WRITE, trace)
    u.emu_start(0x0307f9d1, 0x0307f9ee, count=5000)
    data = bytes(u.mem_read(dst, 258))
    units = list(struct.unpack('<129H', data))
    return units, writes


def main():
    _, writes = execute('', False)
    assert {a for a, _, _ in writes if a < 0x03024804} == {0x030247fa, 0x030247fc}
    old, _ = execute('X' * 128, False)
    assert 0 not in old[:128]
    for source, expected in [('', ''), ('A', 'A'), ('ABCD', 'ABCD'),
                             ('A.mp3', 'A'), ('Song.flac', 'Song'),
                             ('X' * 127, 'X' * 127), ('X' * 128, 'X' * 127),
                             ('X' * 123 + '.mp3' + 'Z', 'X' * 123 + '.mp3')]:
        out, writes = execute(source, True)
        end = out.index(0)
        assert ''.join(chr(c) for c in out[:end]) == expected, (source, end)
        assert all(0x03024804 <= a and a + width <= 0x03024904
                   for a, width, _ in writes), source
        assert end <= 127 and out[128] == 0xffff, source
    for source in ('A.mp3', 'Song.flac', 'ordinary', 'X' * 126):
        old, _ = execute(source, False)
        new, _ = execute(source, True)
        assert old[:old.index(0) + 1] == new[:new.index(0) + 1], source
    print('PASS: stock defects reproduced; patched short, suffix, boundary, truncation and stock-equivalence cases')


if __name__ == '__main__':
    main()
