#!/usr/bin/env python3
"""Thumb-2 disassembly of the transplant candidate's code segment
(first 0x162C0 bytes of work/opus_transplant/module72_opus.bin), with
literal resolution. Usage: dis72t.py <start_hex> <len_hex> [...]"""
import struct, sys
from pathlib import Path
WS = Path.home() / 'workspace/fosi-dap-neo'
blob = open(WS / 'work/opus_transplant/module72_opus.bin', 'rb').read()
code = blob[:0x162C0]
data = blob[0x162C0:]
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
from capstone.arm import ARM_REG_PC
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
md.detail = True

for i in range(1, len(sys.argv) - 1, 2):
    start, ln = int(sys.argv[i], 16), int(sys.argv[i + 1], 16)
    print(f'===== transplant code @0x{start:x} len 0x{ln:x} =====')
    for ins in md.disasm(code[start:start + ln], start):
        extra = ''
        if ins.mnemonic == 'ldr' and ins.operands and ins.operands[-1].type == 2:
            mem = ins.operands[-1].mem
            if mem.base == ARM_REG_PC:
                lit = (ins.address + 4 & ~3) + mem.disp
                if 0 <= lit < len(code):
                    v = struct.unpack_from('<I', code, lit)[0]
                    extra = f'  ; [{lit:#x}] code = {v:#010x}'
                elif 0x01020000 <= lit < 0x01020000 + len(data):
                    v = struct.unpack_from('<I', data, lit - 0x01020000)[0]
                    extra = f'  ; [{lit:#x}] data = {v:#010x}'
        print(f'0x{ins.address:06x}:  {ins.bytes.hex(" "):<14} {ins.mnemonic:<8} {ins.op_str}{extra}')
