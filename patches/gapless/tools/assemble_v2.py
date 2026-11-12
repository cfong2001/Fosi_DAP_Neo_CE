#!/usr/bin/env python3
"""Assemble the gapless v2 patch bytes at their final addresses (keystone)
and check each against a capstone re-disassembly in place.

Prints the expect/replace pairs for patches 0022-0026. Run from the repo
root; needs keystone-engine and capstone.
"""
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image  # noqa: E402

ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)

STATE = 0x030515B0          # retained-module word (patch 0020)
FLAG_LIT = 0x03051500       # literal: address of the core-1 running flag
RUNNING = 0x03004138        # cleared by halt 0x0306CB0C, set by core-1 boot
GATE = 0x03051664           # gate cave, 32 B (0022) + 4 B tail (0025)
BODY = 0x0306CB30           # stock reset-and-start after its prologue
SHUT = 0x030893C4           # module 33 decoder shutdown, 82 B
CLOSE = 0x0308936E          # 0x74 close on the HifiFile channel, waits
HALT = 0x0306CB0C           # hold core-1 reset, gate its clock
RESET, CLKGATE = 0x0305261C, 0x030525AC
I2C_PULSE = 0x03060338      # bus 0-2 controller reset hold: delay_ms(1)
DELAY_US = 0x03064920


def asm(seq, base):
    out = b''
    for line in seq:
        if isinstance(line, bytes):
            out += line
            continue
        enc, _ = ks.asm(line, base + len(out))
        out += bytes(enc)
    return out


def show(code, base):
    for ins in cs.disasm(code, base):
        print(f'    {ins.address:08x}  {ins.bytes.hex():<10} {ins.mnemonic} {ins.op_str}')


def ldr_lit_back(rt, here, lit):
    """LDR.W rt, [pc, #-imm12] (T2, U=0); keystone rejects the form."""
    imm = (here + 4 & ~3) - lit
    assert 0 < imm < 4096
    return struct.pack('<HH', 0xF85F, rt << 12 | imm)


def sub_pc(rd, here, target):
    """SUB.W rd, pc, #imm8 (T3, plain 8-bit immediate)."""
    imm = (here + 4 & ~3) - target
    assert 0 < imm < 256
    return struct.pack('<HH', 0xF1AF, rd << 8 | imm)


def gate(armed):
    miss = GATE + 0x1A
    code = asm([
        ldr_lit_back(2, GATE, FLAG_LIT),    # r2 = &running
        'ldr r2, [r2]',
        sub_pc(1, GATE + 6, STATE),         # r1 = state word
        f'cbz r2, #{miss}',                 # core 1 halted: full load
        'ldr r3, [r1]',
        'eors r3, r0',
        'lsls r3, r3, #25',                 # Z = same decoder module
        f'bne #{miss}' if armed else f'b #{miss}',
        'adds r0, #0x80',                   # retained: module | 0x80
        'str r0, [r1]',
        'bx lr',
        'str r0, [r1]',                     # miss: remember the module
        'push {r4, r5, r6, lr}',            # stock prologue, then body
        'mov r5, r0',
        f'b.w #{BODY}',
    ], GATE)
    assert len(code) == 36, len(code)
    return code


def shutdown():
    done = SHUT + 0x3A
    code = asm([
        b'\xcf\x48',                        # ldr r0, [pc, #0x33c] (stock)
        'push {r4, lr}',
        'ldr r0, [r0]',
        'cmp r0, #10',
        'it hs; pophs {r4, pc}',
        'mov r4, r0',
        f'bl #{CLOSE}',                     # close the decoder's file
        f'cbz r5, #{SHUT + 0x18}',          # natural advance: keep core 1
        f'bl #{HALT}',
        f'cbnz r4, #{done}',                # codec 0 also parks its blocks
        'movs r1, #1', 'movs r0, #0xe', f'bl #{RESET}',
        'movs r1, #1', 'movs r0, #0xf', f'bl #{RESET}',
        'movs r1, #0', 'movs r0, #0x6e', f'bl #{CLKGATE}',
        'movs r1, #0', 'movs r0, #0x7e', f'bl #{CLKGATE}',
        'pop {r4, pc}',
    ], SHUT)
    assert len(code) == 0x3C, hex(len(code))
    return code + b'\x00\xbf' * ((0x52 - len(code)) // 2)   # nop to 0x03089416


def main():
    raw = (ROOT / 'DP3_V137.img').read_bytes()
    im = Image(raw)

    def stock(mod, addr, n):
        m = im.modules[mod]
        off, _ = im.module_region(mod, 'code')
        return raw[off + addr - m['code_exec']:off + addr - m['code_exec'] + n]

    pulse = asm(['movs r0, #50', f'bl #{DELAY_US}'], I2C_PULSE)
    g0, g1 = gate(False), gate(True)
    sd = shutdown()
    lit = struct.pack('<I', RUNNING)
    arm_at = GATE + 0x12
    rows = [
        ('0022 gate cave', 0, GATE, stock(0, GATE, 32), g0[:32]),
        ('0025 gate tail', 0, GATE + 32, stock(0, GATE + 32, 4), g0[32:]),
        ('0023 flag literal', 0, FLAG_LIT, stock(0, FLAG_LIT, 4), lit),
        ('0024 keep decoder', 33, SHUT, stock(33, SHUT, 0x52), sd),
        ('0026 arm', 0, arm_at, g0[0x12:0x14], g1[0x12:0x14]),
        ('0019 i2c reset pulse', 0, I2C_PULSE, stock(0, I2C_PULSE, 6), pulse),
    ]
    for name, mod, addr, exp, rep in rows:
        print(f'{name}: module {mod} @ {addr:#010x} ({len(rep)} B)')
        print(f'  expect:  {exp.hex()}')
        print(f'  replace: {rep.hex()}')
    print('gate (armed):'); show(g1, GATE)
    print('shutdown:'); show(sd[:0x3C], SHUT)


if __name__ == '__main__':
    main()
