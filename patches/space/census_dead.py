#!/usr/bin/env python3
"""Reachability census of module 0 code: which stock routines can never run.

Resident code space is the binding constraint on new features (see
patches/framework/space_budget.md), and module 0 is the resident image.
This finds module 0 code that nothing can reach.

Method, on a built image (default: the Standard CE image, so CE's own hooks
count as callers):

  Roots (deliberately liberal; a false root only hides dead code):
    * every word in module 0's vector table that points into module 0;
    * every BL / B.W / B / Bcond / CBZ target decoded RAW at every halfword
      of every core-0 code segment (modules 0..70, 81), at its exec base;
    * every 32-bit value, at any 2-byte offset of any core-0 segment, that
      lands in module 0 code (literal pools, function-pointer tables,
      window structs, callback registrations);
    * every MOVW/MOVT pair formed into one register, and every ADR target.
  Coverage: recursive descent with capstone from each root, following
  branches, stopping at returns and unconditional transfers, walking
  TBB/TBH tables (bounded by the preceding CMP), and marking LDR-literal
  pool words as covered data.
  Candidates: maximal uncovered runs inside module 0's stock code with
  no reference to any address inside them. Tier 1 begins with a
  PUSH {.., lr} prologue (after any alignment pad). Tier 2 decodes
  cleanly to the end, contains a return, and is not mostly printable
  bytes (leaf routines). Other uncovered runs are reported as data.

Static unreachability is evidence, not proof (register-computed targets
with no literal anywhere would be missed). emulate_poison.py is the second
gate: it overwrites every candidate with UDF and reruns the emulation
suites.

Usage: census_dead.py [IMAGE] [--json OUT]
"""
import json
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
from capstone.arm import ARM_OP_IMM, ARM_OP_MEM, ARM_REG_PC

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image  # noqa: E402

STOCK_CODE_END = 0x03079C14          # module 0 stock code_len 0x29C14
CORE1 = range(71, 81)


def load(path):
    raw = Path(path).read_bytes()
    im = Image(raw)
    segs = []
    for m in im.modules:
        if m['index'] in CORE1:
            continue
        for kind in ('code', 'data'):
            off, ln = im.module_region(m['index'], kind)
            if ln:
                segs.append((m['index'], kind, m[kind + '_exec'], raw[off:off + ln]))
    return raw, im, segs


def branch_targets(code, base):
    out = set()
    for i in range(0, len(code) - 3, 2):
        h1, h2 = struct.unpack_from('<HH', code, i)
        pc = base + i + 4
        if (h1 & 0xF800) == 0xF000 and (h2 & 0xC000) == 0xC000 or \
                (h1 & 0xF800) == 0xF000 and (h2 & 0xD000) == 0x9000:
            s = (h1 >> 10) & 1
            j1 = (~((h2 >> 13) & 1 ^ s)) & 1
            j2 = (~((h2 >> 11) & 1 ^ s)) & 1
            imm = s << 24 | j1 << 23 | j2 << 22 | (h1 & 0x3FF) << 12 | (h2 & 0x7FF) << 1
            if s:
                imm -= 1 << 25
            out.add(pc + imm)
        elif (h1 & 0xF800) == 0xF000 and (h2 & 0xD000) == 0x8000:   # B<c>.W
            s = (h1 >> 10) & 1
            imm = s << 20 | ((h2 >> 11) & 1) << 19 | ((h2 >> 13) & 1) << 18 | \
                (h1 & 0x3F) << 12 | (h2 & 0x7FF) << 1
            if s:
                imm -= 1 << 21
            out.add(pc + imm)
    for i in range(0, len(code) - 1, 2):
        h = struct.unpack_from('<H', code, i)[0]
        pc = base + i + 4
        if (h & 0xF800) == 0xE000:
            imm = (h & 0x7FF) << 1
            out.add(pc + (imm - 0x1000 if imm & 0x800 else imm))
        elif (h & 0xF000) == 0xD000 and (h >> 8) & 0xF < 0xE:
            imm = (h & 0xFF) << 1
            out.add(pc + (imm - 0x200 if imm & 0x100 else imm))
        elif (h & 0xF500) == 0xB100:
            out.add(pc + (((h >> 9) & 1) << 6 | ((h >> 3) & 0x1F) << 1))
    return out


def census(path):
    raw, im, segs = load(path)
    m0 = im.modules[0]
    off0, len0 = im.module_region(0, 'code')
    base0 = m0['code_exec']
    code0 = raw[off0:off0 + len0]
    end0 = base0 + len0
    inside = lambda a: base0 <= a < end0

    roots, words = set(), set()
    for idx, kind, base, b in segs:
        if kind == 'code':
            roots |= {t for t in branch_targets(b, base) if inside(t)}
        for i in range(0, len(b) - 3, 2):
            v = struct.unpack_from('<I', b, i)[0]
            words.add(v)
            if inside(v & ~1):
                roots.add(v & ~1)
    for i in range(0, 0x200, 4):                      # vector table
        v = struct.unpack_from('<I', code0, i)[0]
        if inside(v & ~1) and v & 1:
            roots.add(v & ~1)

    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
    md.detail = True
    # MOVW/MOVT and ADR across core-0 code (linear sweep is fine for
    # non-branch facts; a desync only adds roots).
    for idx, kind, base, b in segs:
        if kind != 'code':
            continue
        lo = {}
        for ins in md.disasm(b, base):
            if ins.mnemonic == 'movw' and ins.operands[1].type == ARM_OP_IMM:
                lo[ins.operands[0].reg] = ins.operands[1].imm
            elif ins.mnemonic == 'movt' and ins.operands[0].reg in lo:
                v = (ins.operands[1].imm << 16) | lo.pop(ins.operands[0].reg)
                if inside(v & ~1):
                    roots.add(v & ~1)
            elif ins.mnemonic == 'adr':
                t = ((ins.address + 4) & ~3) + ins.operands[1].imm
                if inside(t):
                    roots.add(t)

    covered = bytearray(len0)
    seen = set()
    work = sorted(roots)
    ends = {'bx', 'b', 'b.w'}
    while work:
        a = work.pop()
        if a in seen or not inside(a):
            continue
        seen.add(a)
        last_cmp = None
        it_left = 0          # instructions left in the current IT block
        pc = a
        while inside(pc):
            o = pc - base0
            if covered[o] and pc != a:
                break
            ins = next(md.disasm(code0[o:o + 4], pc), None)
            if ins is None:
                break
            for k in range(ins.size):
                covered[o + k] = 1
            mn = ins.mnemonic.split('.')[0]
            ops = ins.operands
            # Decoding one instruction at a time loses IT context, so a
            # conditional 'bxeq lr' decodes as 'bx lr'. Track IT blocks:
            # nothing inside one terminates the walk.
            in_it = it_left > 0
            if in_it:
                it_left -= 1
            if mn.startswith('it') and mn.strip('ite') == '':
                it_left = len(mn) - 1
            if mn == 'cmp' and len(ops) == 2 and ops[1].type == ARM_OP_IMM:
                last_cmp = ops[1].imm
            if mn in ('b', 'bl', 'cbz', 'cbnz') or (mn.startswith('b') and len(mn) == 3
                                                    and ops and ops[-1].type == ARM_OP_IMM):
                t = ops[-1].imm
                if ops[-1].type == ARM_OP_IMM and inside(t):
                    work.append(t)
            if mn.startswith('ldr') and len(ops) == 2 and ops[1].type == ARM_OP_MEM \
                    and ops[1].mem.base == ARM_REG_PC:
                p = ((pc + 4) & ~3) + ops[1].mem.disp
                if inside(p):
                    for k in range(8 if mn == 'ldrd' else 4):
                        if inside(p + k):
                            covered[p + k - base0] = 1
            if mn in ('tbb', 'tbh'):
                n = (last_cmp or 0) + 1
                tbl = pc + 4
                step = 1 if mn == 'tbb' else 2
                for k in range(n):
                    e = code0[tbl - base0 + k * step] if step == 1 else \
                        struct.unpack_from('<H', code0, tbl - base0 + 2 * k)[0]
                    work.append(tbl + 2 * e)
                for k in range(n * step):
                    covered[tbl - base0 + k] = 1
                break
            if in_it:
                pc += ins.size
                continue
            if mn == 'b' and ins.mnemonic in ('b', 'b.w'):
                break
            if mn in ('bx',) or (mn == 'pop' and 'pc' in ins.op_str) or \
                    (mn.startswith('ldr') and ins.op_str.startswith('pc')) or \
                    mn in ('udf', 'bkpt') or (mn == 'mov' and ins.op_str.startswith('pc')):
                break
            pc += ins.size

    # candidate runs in the stock part of module 0
    cands = []
    lim = STOCK_CODE_END - base0
    i = 0x200
    while i < lim:
        if covered[i]:
            i += 1
            continue
        j = i
        while j < lim and not covered[j]:
            j += 1
        run = code0[i:j]
        if any(run) and j - i >= 8:
            k = i
            while k + 2 <= j and code0[k:k + 2] == b'\0\0':     # alignment pad
                k += 2
            hw = struct.unpack_from('<H', code0, k)[0] if k + 2 <= j else 0
            h2 = struct.unpack_from('<H', code0, k + 2)[0] if k + 4 <= j else 0
            prologue = ((hw & 0xFE00) == 0xB400 and hw & 0x100) or \
                (hw == 0xE92D and h2 & 0x4000)
            ins = list(md.disasm(run, base0 + i))
            clean = sum(x.size for x in ins) == len(run)
            rets = any(x.mnemonic in ('bx', 'pop') and ('lr' in x.op_str or 'pc' in x.op_str)
                       for x in ins)
            text = sum(32 <= ch < 127 for ch in run) / len(run)
            refs = [a for a in range(base0 + i, base0 + j) if a in words or (a | 1) in words]
            tier = 1 if prologue else 2 if (clean and rets and text < 0.6) else 0
            cands.append({'start': base0 + i, 'end': base0 + j, 'bytes': j - i,
                          'tier': tier if not refs else 0, 'interior_refs': len(refs)})
        i = j
    return {'image': str(path), 'module0_code': [hex(base0), hex(end0)],
            'roots': len(roots), 'covered_bytes': sum(covered[:lim]),
            'stock_code_bytes': lim, 'candidates': cands}


def main():
    argv = sys.argv[1:]
    if '--json' in argv:
        k = argv.index('--json')
        argv = argv[:k] + argv[k + 2:]
    args = argv
    path = args[0] if args else ROOT / 'release' / 'DP3_V137_CE.img'
    r = census(path)
    c = r['candidates']
    print(f"roots {r['roots']}; covered {r['covered_bytes']} of "
          f"{r['stock_code_bytes']} stock module 0 code bytes")
    print(f"uncovered nonzero runs: {len(c)}, {sum(x['bytes'] for x in c)} B")
    for t, name in ((1, 'tier 1 (prologue)'), (2, 'tier 2 (leaf code)'),
                    (0, 'data or referenced')):
        xs = [x for x in c if x['tier'] == t]
        print(f"{name}: {len(xs)} runs, {sum(x['bytes'] for x in xs)} B")
    strict = [x for x in c if x['tier']]
    for x in sorted(strict, key=lambda x: -x['bytes'])[:20]:
        print(f"  {x['start']:#010x}..{x['end']:#010x} {x['bytes']:6d}  tier {x['tier']}")
    if '--json' in sys.argv:
        out = Path(sys.argv[sys.argv.index('--json') + 1])
        out.write_text(json.dumps(r, indent=1) + '\n')


if __name__ == '__main__':
    main()
