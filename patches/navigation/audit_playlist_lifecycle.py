#!/usr/bin/env python3
"""Read-only audit of the playlist-to-browser transition.

Usage: python3 patches/navigation/audit_playlist_lifecycle.py --trampoline PATH

Pass trampoline.bin emitted by patches/m3u/compose/build_payload.py for the
current source tree. This is an offline instruction/branch check, not a
hardware or end-to-end playback test. It never modifies the firmware image.
"""
import argparse
import hashlib
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_SP

STOCK_HASH = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
TRAMP = 0x0307EE48
RESUME = 0x0307DF1E
STOCK_CLASSIFY = 0x0307D1F8
STAGE = 0x0307BFB4
NODE = 0x03018000


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--trampoline', type=Path, required=True)
    p.add_argument('--stock', type=Path, default=ROOT / 'DP3_V137.img')
    a = p.parse_args()
    raw = a.stock.read_bytes()
    if hashlib.sha256(raw).hexdigest() != STOCK_HASH:
        raise ValueError('stock image SHA-256 mismatch')
    image = Image(raw)
    m = image.modules[31]
    off, length = image.module_region(31, 'code')
    code = raw[off:off + length]
    def read(addr, n):
        pos = addr - m['code_exec']
        if pos < 0 or pos + n > len(code):
            raise ValueError('address outside module 31')
        return code[pos:pos+n]
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
    branch = list(md.disasm(read(0x0307DF16, 2), 0x0307DF16))
    if len(branch) != 1 or branch[0].mnemonic != 'cbz' or branch[0].op_str != 'r5, #0x307df4e':
        raise ValueError('stock directory branch changed; reassess audit')
    if read(0x0307DF1A, 4) != bytes.fromhex('fff76df9'):
        raise ValueError('stock node classifier site changed; reassess audit')
    patch = (ROOT / 'patches/m3u/compose/patches/0040-m3u-browser-hook.patch').read_text()
    if 'replace: 00f095bf' not in patch:
        raise ValueError('browser hook changed; reassess audit')
    blob = a.trampoline.read_bytes()
    if len(blob) != 64 or hashlib.sha256(blob).hexdigest() != 'f719932358ee1601539c6c5e5e58231e1723b6ac9a1672cb7df4315bccef5b55':
        raise ValueError('trampoline is not the audited 64-byte build')

    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x03000000, 0x100000)
    u.mem_write(TRAMP, blob)
    u.mem_write(NODE + 0x57, b'MP3')
    u.mem_write(STAGE, b'\x01')
    u.reg_write(UC_ARM_REG_R4, NODE)
    u.reg_write(UC_ARM_REG_R5, 1)
    u.reg_write(UC_ARM_REG_SP, 0x030f0000)
    u.reg_write(UC_ARM_REG_LR, 0x030ef001)
    calls = []
    def on_code(uc, address, size, user):
        if address == STOCK_CLASSIFY:
            calls.append(address)
            uc.reg_write(UC_ARM_REG_R0, 1)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    u.hook_add(UC_HOOK_CODE, on_code)
    u.emu_start(TRAMP | 1, RESUME, count=100)
    if calls != [STOCK_CLASSIFY] or bytes(u.mem_read(STAGE, 1)) != b'\x01':
        raise AssertionError('normal-file trampoline behavior changed; reassess audit')
    print('PASS: directory class bypasses the M3U hook')
    print('PASS: selecting a non-M3U node leaves an armed playlist flag set')

    # Model a successful bridge return, then execute the actual trampoline and
    # stock epilogue. The bridge itself is not emulated here; its source shows
    # it writes staging and ignores the play-context argument.
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x03000000, 0x100000)
    u.mem_write(m['code_exec'], code)
    u.mem_write(TRAMP, blob)
    u.mem_write(NODE + 0x57, b'M3U')
    sp = 0x030d0000
    u.mem_write(sp + 0x4c, struct.pack('<9I', *([0] * 8), 0x030ef001))
    u.reg_write(UC_ARM_REG_R4, NODE)
    u.reg_write(UC_ARM_REG_SP, sp)
    u.reg_write(UC_ARM_REG_LR, 0x030ef001)
    calls = []
    def success_bridge(uc, address, size, user):
        if address == TRAMP + 64:
            calls.append('bridge')
            uc.mem_write(STAGE, b'\x01')
            uc.reg_write(UC_ARM_REG_R0, 1)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif address in (0x0306723c, 0x03067452):
            calls.append(hex(address))
    u.hook_add(UC_HOOK_CODE, success_bridge)
    u.emu_start(TRAMP | 1, 0x030ef000, count=100)
    if calls != ['bridge'] or bytes(u.mem_read(STAGE, 1)) != b'\x01' or u.reg_read(UC_ARM_REG_R0) != 1:
        raise AssertionError('successful import path changed; reassess audit')
    print('PASS: modeled successful import returns via stock epilogue without event or playback message')
    print('LIMIT: bridge import, event loop, and hardware playback are not emulated')


if __name__ == '__main__':
    main()
