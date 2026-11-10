#!/usr/bin/env python3
"""Disassembly-level reference census for the DAP Neo resident-home hunt.

Method (re-runnable, no linear-sweep disassembly is trusted for branches):
  Segments and true exec bases come from extracted/manifest.json and the
  extracted/module_NN_{code,data}_*.bin files.
  For every code segment, references are collected by RAW halfword decode
  (alignment-proof, the gapless workstream's refscan discipline):
    * BL / B.W targets: first halfword (hw & 0xF800) == 0xF000 and second
      halfword class in {0x8000, 0x9000, 0xD000} (B.W/BL encoding space).
    * B (short): (hw & 0xF800) == 0xE000, imm11 sign-extended.
    * Bcond: (hw & 0xF000) == 0xD000, cond not 0xE/0xF, imm8.
    * CBZ/CBNZ: (hw & 0xF500) == 0xB100 pattern space (0xB1xx/0xB9xx).
  Plus, from a capstone pass used ONLY for non-branch facts (capstone can
  desync after data pools, so its branch output is ignored):
    * ADR targets, LDR-literal pool values (the word stored in the pool is
      the referenced address), MOVW/MOVT pairs formed to one register.
  Plus byte-find: every 4-byte LE occurrence of the queried address or its
  Thumb form at ANY offset in ANY code or data segment (literal pools and
  data tables wherever they sit).
  A queried address with no hit in any class is "direct-unreferenced".
  That is NOT proof of deadness. Three residuals are handled separately in
  the report, not by this script:
    * fall-through: code reached only by sequential execution has no
      reason to be referenced; candidate pockets must be shown to be
      non-fall-through (preceding instruction is a return/unconditional
      branch, or the pocket is a run of identical stub returns).
    * base+offset: an address inside [named_base, named_base+extent) of a
      documented struct can be reached without ever being named; the
      report checks documented struct extents explicitly.
    * jump tables (TBB/TBH byte/halfword offsets) and register-indirect
      calls (BX/BLX) cannot be resolved statically in general.

Usage: census.py LO HI [--detail]
"""
import glob, json, os, struct, sys
os.chdir(os.path.expanduser('~/workspace/fosi-dap-neo'))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS

man = json.load(open('extracted/manifest.json'))
mods = {m['index']: m for m in man['modules']}
regions = []
for idx in range(82):
    for kind in ('code', 'data'):
        f = glob.glob(f'extracted/module_{idx:02d}_{kind}_*.bin')
        if not f: continue
        b = open(f[0], 'rb').read()
        if b: regions.append((idx, kind, mods[idx][kind + '_exec'], b))

branch_tgts, adr_tgts, ldr_values, formed = {}, {}, {}, {}

def note(d, a, item):
    d.setdefault(a, []).append(item)
    d.setdefault(a & ~1, []).append(item)

# raw branch decode
for idx, kind, base, code in regions:
    if kind != 'code': continue
    for i in range(0, len(code) - 4, 2):
        hw1, hw2 = struct.unpack_from('<HH', code, i)
        site = base + i
        if (hw1 & 0xf800) == 0xf000 and (hw2 & 0xd000) in (0xd000, 0x8000, 0x9000):
            s = (hw1 >> 10) & 1; imm10 = hw1 & 0x3ff
            j1 = (hw2 >> 13) & 1; j2 = (hw2 >> 11) & 1; imm11 = hw2 & 0x7ff
            i1 = (~(j1 ^ s)) & 1; i2 = (~(j2 ^ s)) & 1
            imm = (s << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
            if imm & (1 << 24): imm -= (1 << 25)
            note(branch_tgts, site + 4 + imm, (idx, site))
        if (hw1 & 0xf800) == 0xe000:
            imm = hw1 & 0x7ff
            if imm & 0x400: imm -= 0x800
            note(branch_tgts, site + 4 + (imm << 1), (idx, site))
        if (hw1 & 0xf000) == 0xd000 and ((hw1 >> 8) & 0xf) not in (0xe, 0xf):
            imm = hw1 & 0xff
            if imm & 0x80: imm -= 0x100
            note(branch_tgts, site + 4 + (imm << 1), (idx, site))
        if (hw1 & 0xf500) == 0xb100:
            imm = (((hw1 >> 9) & 1) << 6) | (((hw1 >> 3) & 0x1f) << 1)
            note(branch_tgts, site + 4 + imm, (idx, site))

# capstone pass for ADR / LDR-literal / MOVW-MOVT only
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB + CS_MODE_MCLASS)
md.detail = True
for idx, kind, base, code in regions:
    if kind != 'code': continue
    pending = {}
    for ins in md.disasm(code, base):
        m, ops = ins.mnemonic, ins.operands
        if m == 'adr':
            for op in ops:
                if op.type == 2: note(adr_tgts, op.imm, (idx, ins.address))
        if m.startswith('ldr') and len(ops) >= 2 and ops[1].type == 3:
            mem = ops[1].mem
            if ins.reg_name(mem.base) == 'pc':
                pool = (ins.address & ~3) + 4 + mem.disp
                off = pool - base
                if 0 <= off + 4 <= len(code):
                    v = struct.unpack_from('<I', code, off)[0]
                    note(ldr_values, v, (idx, ins.address, pool))
        if m == 'movw' and len(ops) == 2 and ops[1].type == 2:
            pending[ins.reg_name(ops[0].reg)] = (ops[1].imm, ins.address)
        elif m == 'movt' and len(ops) == 2 and ops[1].type == 2:
            r = ins.reg_name(ops[0].reg)
            if r in pending:
                lo, site = pending.pop(r)
                note(formed, (ops[1].imm << 16) | lo, (idx, site))

def byte_find(target):
    hits = []
    pat = struct.pack('<I', target)
    for idx, kind, base, buf in regions:
        start = 0
        while True:
            j = buf.find(pat, start)
            if j < 0: break
            hits.append((idx, kind, base + j)); start = j + 1
    return hits

def main():
    lo, hi = int(sys.argv[1], 0), int(sys.argv[2], 0)
    detail = '--detail' in sys.argv
    unref_runs, run_start, referenced = [], None, []
    for a in range(lo, hi, 2):
        refs = []
        bf = byte_find(a) + byte_find(a | 1)
        if bf: refs.append(f"BYTEFIND n={len(bf)} {bf[:4]}")
        for name, d in (('BRANCH', branch_tgts), ('ADR', adr_tgts), ('LDRLIT', ldr_values), ('MOVPAIR', formed)):
            s = d.get(a, []) + (d.get(a | 1, []) if a | 1 != a else [])
            # de-dup: note() already mirrored a and a&~1
            s = d.get(a, [])
            if s: refs.append(f"{name} n={len(s)} {[(i, hex(x) if isinstance(x, int) else x) for i, x, *r in [tuple(t) if isinstance(t, tuple) else (0, t) for t in s[:4]]]}")
        if refs:
            referenced.append(a)
            if run_start is not None:
                unref_runs.append((run_start, a - run_start)); run_start = None
            if detail: print(f"{a:#010x}: " + " ; ".join(refs))
        else:
            if run_start is None: run_start = a
    if run_start is not None: unref_runs.append((run_start, hi - run_start))
    print(f"RANGE {lo:#010x}..{hi:#010x}: {len(referenced)} direct-referenced addrs, "
          f"{(hi - lo) // 2 - len(referenced)} direct-unreferenced")
    print("Direct-unreferenced runs (>=16 B):")
    for s, n in sorted([r for r in unref_runs if r[1] >= 16], key=lambda r: -r[1]):
        print(f"  {s:#010x}  {n} bytes")
    if not detail:
        print("Direct-referenced addresses:")
        for a in referenced: print(f"  {a:#010x}")

if __name__ == '__main__':
    main()
