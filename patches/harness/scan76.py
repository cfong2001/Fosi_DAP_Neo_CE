#!/usr/bin/env python3
"""Full-code reference scan of module 76: call graph + literal-load resolution.
Prints: BL/BLX-immediate callers per target; literal values loaded per address."""
import struct
import sys
from collections import defaultdict
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

WS = Path(__file__).resolve().parents[2]
code = open(WS / 'extracted/module_76_code_01000000.bin', 'rb').read()

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True
md.skipdata = True

callers = defaultdict(list)      # target -> [insn addr]
litrefs = defaultdict(list)      # literal VALUE loaded -> [insn addr]
adrrefs = defaultdict(list)      # adr target -> [insn addr]

for ins in md.disasm(code, 0):
    if ins.mnemonic in ('bl', 'blx') and ins.operands and ins.operands[0].type == 2:  # IMM
        callers[ins.operands[0].imm].append(ins.address)
    if ins.mnemonic == 'ldr' and len(ins.operands) == 2 and ins.operands[1].type == 3:  # MEM
        m = ins.operands[1].mem
        if m.base != 0:
            from capstone.arm import ARM_REG_PC
            if m.base == ARM_REG_PC:
                la = ((ins.address + 4) & ~3) + m.disp
                if 0 <= la < len(code) - 3:
                    val = struct.unpack('<I', code[la:la + 4])[0]
                    litrefs[val].append(ins.address)
    if ins.mnemonic == 'adr' and len(ins.operands) == 2 and ins.operands[1].type == 2:
        tgt = ((ins.address + 4) & ~3) + ins.operands[1].imm
        adrrefs[tgt].append(ins.address)

if __name__ == '__main__':
    q = sys.argv[1]
    if q == 'callers':
        for t in sorted(callers):
            print(f'{t:#08x} <- called from ' + ', '.join(f'{a:#x}' for a in callers[t]))
    elif q == 'lit':
        for v in sys.argv[2:]:
            v = int(v, 16)
            print(f'literal {v:#010x} loaded at: ' + ', '.join(f'{a:#x}' for a in litrefs.get(v, [])))
    elif q == 'adr':
        for v in sys.argv[2:]:
            v = int(v, 16)
            print(f'adr {v:#08x} at: ' + ', '.join(f'{a:#x}' for a in adrrefs.get(v, [])))
