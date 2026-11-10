#!/usr/bin/env python3
"""Thumb-2 disassembly of module 72 code (0-based core-1 view) with literal
resolution against code + data images. Usage: dis72.py <start_hex> <len_hex> [...]"""
import struct, sys
from pathlib import Path
WS = Path.home() / 'workspace/fosi-dap-neo'
code = open(WS / 'extracted/module_72_code_01000000.bin', 'rb').read()
data = open(WS / 'extracted/module_72_data_01020000.bin', 'rb').read()
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
from capstone.arm import ARM_REG_PC
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
md.detail = True
md.skipdata = True

def rd32va(va):
    if 0 <= va < len(code) - 3: return struct.unpack('<I', code[va:va+4])[0]
    if 0x01020000 <= va < 0x01020000 + len(data) - 3:
        return struct.unpack('<I', data[va-0x01020000:va-0x01020000+4])[0]
    return None

args = sys.argv[1:]
for i in range(0, len(args), 2):
    start, ln = int(args[i], 16), int(args[i+1], 16)
    print(f'===== m72 code @{start:#06x} len {ln:#x} =====')
    for ins in md.disasm(code[start:start+ln], start):
        note = ''
        if ins.mnemonic.startswith(('ldr',)) and len(ins.operands) == 2 \
                and ins.operands[1].type == 3 and ins.operands[1].mem.base == ARM_REG_PC:
            la = ((ins.address + 4) & ~3) + ins.operands[1].mem.disp
            val = rd32va(la)
            if val is not None: note = f'   ; [{la:#x}] = {val:#010x}'
        print(f'{ins.address:#08x}:  {ins.bytes.hex(" "):<14} {ins.mnemonic:8s} {ins.op_str}{note}')
    print()
