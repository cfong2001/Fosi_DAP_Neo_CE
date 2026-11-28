#!/usr/bin/env python3
"""Find stock code that still reaches bytes a CE patch overwrites.

PR #41 fixed a patch that put a trampoline in a `bx lr` stub that
shutdown still called. This tool checks every byte patch in a build report
for the same mistake. It indexes every way stock code can reach an address:

- Thumb branch and call targets (B, B<cond>, B.W, BL, BLX, CBZ, CBNZ),
  disassembled from every module at both halfword phases;
- PC-relative literal loads and ADR, which read data inside code;
- 32-bit words in every module's code and data that point into code
  (function pointers and jump tables, Thumb bit ignored).

A patched range covers only the bytes a patch changes. A reference is
reported when its target lies inside a patched range, its source lies
outside every patched range, and the source module can be loaded at the
same time as the patched module. Overlays that share an execution range
replace each other, so their references cannot meet. Core-1 decoder
modules run in their own address space and are skipped as sources.

A branch to the first byte of a hook is the hook's normal entry, so
`--interior-only` hides it. The exception is a range whose stock bytes
were stubs or padding, marked FILLER: a call into overwritten filler is
the PR #41 bug.

Linear sweeps decode some data as code, so treat a hit as a lead and
confirm it in context. tests/test_patch_xref_audit.py lists each lead
that has been read and why it is harmless.

Usage:
  tools/patch_xref_audit.py [--stock DP3_V137.img]
      [--report release/DP3_V137_CE.img.report.json] [--interior-only]
"""
import argparse
import functools
import json
import struct
import sys
from bisect import bisect_right
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs
from capstone.arm import ARM_OP_IMM, ARM_OP_MEM, ARM_REG_PC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image  # noqa: E402

BRANCHES = {'b', 'bl', 'blx', 'cbz', 'cbnz', 'b.w'}


def is_branch(mnemonic):
    m = mnemonic.split('.')[0]
    return m in BRANCHES or (m.startswith('b') and len(m) == 3
                             and m[1:] in {'eq', 'ne', 'cs', 'hs', 'cc', 'lo', 'mi', 'pl',
                                           'vs', 'vc', 'hi', 'ls', 'ge', 'lt', 'gt', 'le'})


def code_regions(image):
    for m in image.modules:
        if not m['code_len'] or not m['code_exec']:
            continue
        off, size = image.module_region(m['index'], 'code')
        yield m['index'], m['code_exec'], image.raw[off:off + size]


def data_regions(image):
    for m in image.modules:
        if not m['data_len']:
            continue
        try:
            off, size = image.module_region(m['index'], 'data')
        except Exception:
            continue
        yield m['index'], m['data_exec'], image.raw[off:off + size]


def references(image, in_target):
    """Yield (kind, module, source address, target) for targets that in_target accepts."""
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    md.skipdata = True
    for index, base, blob in code_regions(image):
        for phase in (0, 2):
            for ins in md.disasm(blob[phase:], base + phase):
                if ins.id == 0 or not ins.operands:   # id 0: skipped data
                    continue
                if is_branch(ins.mnemonic):
                    op = ins.operands[-1]
                    if op.type == ARM_OP_IMM and in_target(op.imm):
                        yield 'branch:' + ins.mnemonic, index, ins.address, op.imm
                elif ins.mnemonic.startswith(('ldr', 'adr', 'vldr')):
                    for op in ins.operands:
                        if op.type == ARM_OP_MEM and op.mem.base == ARM_REG_PC:
                            t = ((ins.address + 4) & ~3) + op.mem.disp
                            if in_target(t):
                                yield 'literal:' + ins.mnemonic, index, ins.address, t
                        elif ins.mnemonic.startswith('adr') and op.type == ARM_OP_IMM:
                            t = ((ins.address + 4) & ~3) + op.imm
                            if in_target(t):
                                yield 'adr', index, ins.address, t
    for kind, regions in (('word:code', code_regions(image)), ('word:data', data_regions(image))):
        for index, base, blob in regions:
            for i in range(0, len(blob) - 3, 2):
                w = struct.unpack_from('<I', blob, i)[0] & ~1
                if in_target(w):
                    yield kind, index, base + i, w


def patched_ranges(report):
    out = []
    for p in report['patches_applied']:
        if p.get('kind') != 'module' or p.get('region') != 'code' or 'cpu_address' not in p:
            continue
        old, new = bytes.fromhex(p['old_hex']), bytes.fromhex(p['new_hex'])
        changed = [i for i in range(len(new)) if old[i] != new[i]]
        if not changed:
            continue   # a no-op patch, such as the self-test
        lo, hi = changed[0] & ~1, (changed[-1] | 1) + 1   # whole halfwords
        start = int(p['cpu_address'], 16)
        out.append((start + lo, start + hi, p['patch'], p['module'], old[lo:hi].hex()))
    return sorted(out)


FILLER = {'7047', '0000', '00bf', 'ffff'}   # bx lr, zero, nop, erased


def is_filler(old_hex):
    """True when the stock bytes are stubs or padding, which a cave patch overwrites."""
    return all(old_hex[i:i + 4] in FILLER for i in range(0, len(old_hex), 4))


def exclusive(image, a, b):
    """True when modules a and b are overlays with overlapping code ranges."""
    if a == b:
        return False
    ma, mb = image.modules[a], image.modules[b]
    return (ma['code_exec'] < mb['code_exec'] + mb['code_len']
            and mb['code_exec'] < ma['code_exec'] + ma['code_len'])


@functools.lru_cache(maxsize=2)
def core0_references(stock):
    """Every reference in stock whose target is core-0 code (0x03050000 and up)."""
    image = Image(stock)
    return image, tuple(references(image, lambda a: 0x03050000 <= a < 0x030B0000))


def audit(stock, report, interior_only=False):
    """Return the references from stock code into the ranges the report's patches change."""
    image, index = core0_references(stock)
    ranges = patched_ranges(report)
    starts = [r[0] for r in ranges]

    def owner(address):
        i = bisect_right(starts, address) - 1
        return ranges[i] if i >= 0 and ranges[i][0] <= address < ranges[i][1] else None

    findings, seen = [], set()
    for kind, module, source, target in index:
        if owner(target) is None or owner(source) is not None:
            continue   # reference from bytes a patch replaces anyway
        start, end, name, pmod, old_hex = owner(target)
        core1 = image.modules[module]['code_exec'] < 0x03000000   # decoder core, own address space
        if core1 or exclusive(image, module, pmod) or (kind, source, target) in seen:
            continue
        seen.add((kind, source, target))
        if interior_only and target == start and not is_filler(old_hex):
            continue
        findings.append(dict(patch=name, patch_module=pmod, range=[hex(start), hex(end)],
                             target=hex(target), at_start=target == start,
                             filler=is_filler(old_hex), kind=kind,
                             source_module=module, source=hex(source)))
    findings.sort(key=lambda f: (f['range'][0], f['target'], f['source']))
    return findings, len(ranges)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--stock', default=str(ROOT / 'DP3_V137.img'))
    ap.add_argument('--report', default=str(ROOT / 'release/DP3_V137_CE.img.report.json'))
    ap.add_argument('--interior-only', action='store_true',
                    help='hide references to the first byte of a patched range')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    findings, count = audit(Path(args.stock).read_bytes(),
                            json.loads(Path(args.report).read_text()), args.interior_only)
    if args.json:
        print(json.dumps(findings, indent=1))
    else:
        for f in findings:
            tags = ('start ' if f['at_start'] else '') + ('FILLER' if f['filler'] else '')
            print(f"{f['patch']:40s} {f['range'][0]}..{f['range'][1]} target {f['target']}"
                  f" [{tags.strip()}]  <- {f['kind']} m{f['source_module']} {f['source']}")
        print(f'{len(findings)} references into {count} patched code ranges', file=sys.stderr)


if __name__ == '__main__':
    main()
