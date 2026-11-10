#!/usr/bin/env python3
"""Unicorn emulation for the resolver hooks (patches 0041/0042) and
the staging layout, against the scratch tail image.

Method for the flag-clear / excluded-caller equivalence tests (part
b): the stock resolver and fetch call three stack-managing callees
(reset 0x03059C76, stack init 0x03059F58, descend 0x03059B10) whose
real bodies walk card structures that do not exist offline. Those
three are intercepted and replaced by a small deterministic model of
the directory stack (a fixed three-directory tree, mirrored into
emulated memory at the real stack addresses). The resolver/fetch
code itself, including its memcpy, runs for real in both runs, and
the model is byte-for-byte identical between the stock run and the
hooked run, so any divergence in the captured state is attributable
to the hooks alone. The model's descend is a depth-first advance
with a per-element child cursor, matching the resolver design's
reading of the walk; the resolver's own post-descend checks
(top countA == 0, depth == 0 forces index 0) then behave as traced.

Part (c) drives the primary and companion hooks with the flag set
and a synthetic two-run playlist staged in the tail header layout,
following the index sequence module 33 presents ([ctx+2] stored
residual, +1 for next, -1 in the u16 domain for previous).
"""
import struct
import sys
import argparse
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_LITTLE_ENDIAN, UC_HOOK_CODE
from unicorn.arm_const import *

HERE = Path(__file__).resolve().parent
TB = HERE.parent
WS = TB.parents[2]
STOCK_IMG = WS / 'DP3_V137.img'

RAM_BASE, RAM_SIZE = 0x03000000, 0x100000
RET_ADDR = 0x030F8000
STACK_TOP = 0x030E0000

RESOLVER = 0x03059DAC
FETCH = 0x0305B2C2
RESET, INIT, DESCEND = 0x03059C76, 0x03059F58, 0x03059B10

DEPTH_ADDR = 0x0307A8DC
ELEM_BASE = 0x0307A8E4
CUR_CELL = 0x0307AB64
ROOT_CELL = 0x0307BF58
TABLE_CELL = 0x03005714
CTXDESC = 0x030239B4
STAGE = 0x0307BFB4

ROOT = 0x2000
DIR_A, DIR_B = 0x2001, 0x2002
TREE = {
    ROOT:  {'countA': 2, 'countB': 1, 'children': [DIR_A, DIR_B]},
    DIR_A: {'countA': 3, 'countB': 0, 'children': []},
    DIR_B: {'countA': 1, 'countB': 2, 'children': []},
}


def ctx_bytes(cluster):
    return bytes(((cluster + k) & 0xFF) for k in range(42))


def module0_regions(img_path):
    sys.path.insert(0, str(WS / 'tools'))
    import rknano_image as rk
    img = rk.Image(open(img_path, 'rb').read())
    m = img.modules[0]
    regions = {}
    for kind in ('code', 'data'):
        off, size = img.module_region(0, kind)
        regions[kind] = (m[kind + '_exec'], img.raw[off:off + size])
    return regions


class Model:
    """Directory stack model, mirrored into emulated memory."""

    def __init__(self, uc):
        self.uc = uc
        self.stack = []
        self.log = []

    def _write_elem(self, idx):
        e = self.stack[idx]
        node = TREE[e['cluster']]
        base = ELEM_BASE + idx * 71
        self.uc.mem_write(base + 0x00, struct.pack('<H', node['countA']))
        self.uc.mem_write(base + 0x02, struct.pack('<H', node['countB']))
        self.uc.mem_write(base + 0x15, struct.pack('<I', e['cluster']))
        self.uc.mem_write(base + 0x1D, ctx_bytes(e['cluster']))
        self.uc.mem_write(DEPTH_ADDR, bytes([idx]))
        self.uc.mem_write(CUR_CELL, struct.pack('<I', e['cluster']))

    def reset(self):
        self.stack = [{'cluster': ROOT, 'next': 0}]
        self._write_elem(0)
        self.log.append(('reset', ROOT))

    def init(self):
        self.stack = [{'cluster': ROOT, 'next': 0}]
        self._write_elem(0)
        self.log.append(('init', ROOT))

    def descend(self):
        while True:
            top = self.stack[-1]
            node = TREE[top['cluster']]
            if top['next'] < len(node['children']) and len(self.stack) <= 7:
                child = node['children'][top['next']]
                top['next'] += 1
                self.stack.append({'cluster': child, 'next': 0})
                self._write_elem(len(self.stack) - 1)
                self.log.append(('descend->push', child))
                return
            if len(self.stack) == 1:
                self.log.append(('descend->exhausted', ROOT))
                return
            popped = self.stack.pop()
            self._write_elem(len(self.stack) - 1)
            self.log.append(('descend->pop', popped['cluster']))


class Run:
    def __init__(self, regions):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_LITTLE_ENDIAN)
        uc = self.uc
        uc.mem_map(RAM_BASE, RAM_SIZE)
        for base, blob in regions.values():
            uc.mem_write(base, blob)
        uc.mem_write(RET_ADDR, bytes.fromhex('fee7'))
        uc.mem_write(ROOT_CELL, struct.pack('<I', ROOT))
        self.model = Model(uc)
        self.reached = False
        uc.hook_add(UC_HOOK_CODE, self._code)

    def _code(self, uc, address, size, _):
        if address == RESET:
            self.model.reset()
            uc.reg_write(UC_ARM_REG_R0, 0)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif address == INIT:
            self.model.init()
            uc.reg_write(UC_ARM_REG_R0, 0)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif address == DESCEND:
            self.model.descend()
            uc.reg_write(UC_ARM_REG_R0, 0)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif address == RET_ADDR:
            self.reached = True
            uc.emu_stop()

    def call(self, entry, r0, r1, r2, r3):
        uc = self.uc
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_R0, r0)
        uc.reg_write(UC_ARM_REG_R1, r1)
        uc.reg_write(UC_ARM_REG_R2, r2)
        uc.reg_write(UC_ARM_REG_R3, r3)
        for r in (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
                  UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11):
            uc.reg_write(r, 0x5EED0000 + r)
        uc.reg_write(UC_ARM_REG_R12, 0x12C0FFEE)   # ip sentinel: the hooks
        # must return it untouched on every fallback path
        uc.reg_write(UC_ARM_REG_LR, RET_ADDR | 1)
        self.reached = False
        uc.emu_start(entry | 1, RET_ADDR, count=4_000_000)
        self.reached = self.reached or (uc.reg_read(UC_ARM_REG_PC) & ~1) == RET_ADDR
        return self.capture(r1 if entry == RESOLVER else CTXDESC)

    def capture(self, desc_addr):
        uc = self.uc
        regs = {f'r{i}': uc.reg_read(globals()[f'UC_ARM_REG_R{i}'])
                for i in range(0, 13)}
        return {
            'reached': self.reached,
            'regs': regs,
            'sp': uc.reg_read(UC_ARM_REG_SP),
            'desc': uc.mem_read(desc_addr, 0x30).hex(),
            'ctxdesc': uc.mem_read(CTXDESC, 0x60).hex(),
            'stack_area': uc.mem_read(DEPTH_ADDR, CUR_CELL + 4 - DEPTH_ADDR).hex(),
            'log': list(self.model.log),
        }


def stage_playlist(uc, pos=0xFFFF, resid=0):
    """The synthetic two-run playlist from the brief, in tail layout."""
    hdr = bytearray(16)
    hdr[0] = 1                      # flag
    hdr[1] = 3                      # entry count
    struct.pack_into('<H', hdr, 2, pos)
    struct.pack_into('<H', hdr, 4, resid)
    hdr[6] = 2                      # run count
    uc.mem_write(STAGE, bytes(hdr))
    for i, (cluster, ca, cb) in enumerate([(DIR_A, 3, 0), (DIR_B, 1, 2)]):
        run = bytearray(50)
        struct.pack_into('<I', run, 0, cluster)
        struct.pack_into('<H', run, 4, ca)
        struct.pack_into('<H', run, 6, cb)
        run[8:50] = ctx_bytes(cluster)
        uc.mem_write(STAGE + 16 + i * 50, bytes(run))
    for i, (within, runid) in enumerate([(0, 0), (2, 0), (0, 1)]):
        ent = bytearray(4)
        struct.pack_into('<H', ent, 0, within)
        ent[2] = runid
        uc.mem_write(STAGE + 616 + i * 4, bytes(ent))


def header_state(uc):
    pos, resid = struct.unpack('<HH', uc.mem_read(STAGE + 2, 4))
    return pos, resid


def desc_fields(uc, addr=CTXDESC):
    cluster = struct.unpack('<I', uc.mem_read(addr, 4))[0]
    total = struct.unpack('<I', uc.mem_read(addr + 8, 4))[0]
    ctx = bytes(uc.mem_read(addr + 0x1C, 42))
    return cluster, total, ctx


# ------------------------------------------------------------- part (b)

def part_b(stock_regions, tail_regions):
    print('== Part (b): flag-clear / excluded-caller equivalence ==')
    ok_all = True

    def scenario(name, entry, args, stage):
        nonlocal ok_all
        results = {}
        for label, regions in (('stock', stock_regions), ('tail', tail_regions)):
            run = Run(regions)
            if stage is not None and label == 'tail':
                stage(run.uc)
            results[label] = run.call(entry, *args)
        same = results['stock'] == results['tail']
        ok_all = ok_all and same and results['tail']['reached']
        print(f'  [{"PASS" if same else "FAIL"}] {name}: '
              f'stock == tail byte-identical '
              f'(ret {results["tail"]["regs"]["r0"]:#x}, '
              f'log {[e[0] for e in results["tail"]["log"]]})')
        if not same:
            for k in results['stock']:
                if results['stock'][k] != results['tail'][k]:
                    print(f'      differs: {k}')
        return results

    def flag_only(uc):
        uc.mem_write(STAGE, b'\x01')

    def staged_pos1(uc):
        stage_playlist(uc, pos=1, resid=2)

    R, F = RESOLVER, FETCH
    scenario('P1 primary, flag clear, disc-passing, i=0', R,
             (0, CTXDESC, TABLE_CELL, 1), None)
    scenario('P2 primary, flag clear, disc-passing, i=3 (descend)', R,
             (3, CTXDESC, TABLE_CELL, 1), None)
    scenario('P3 primary, flag SET, excluded out ptr (module 31 shape), i=1', R,
             (1, 0x0307D000, TABLE_CELL, 1), flag_only)
    scenario('P4 primary, flag SET, excluded mode 3 (source 0x63), i=4', R,
             (4, CTXDESC, TABLE_CELL, 3), flag_only)
    scenario('P5 primary, flag SET, excluded out ptr (module 0 internal), i=5', R,
             (5, 0x03024000, TABLE_CELL, 1), flag_only)
    scenario('P6 primary, flag clear, disc-passing, i=7 (exhaustion wrap)', R,
             (7, CTXDESC, TABLE_CELL, 1), None)
    scenario('P7 primary, flag clear, disc-passing, i=6 (second subdir)', R,
             (6, CTXDESC, TABLE_CELL, 1), None)
    scenario('C1 companion, flag clear, cluster A, idx 1', F,
             (1, DIR_A, TABLE_CELL, 1), None)
    scenario('C2 companion, flag SET, excluded mode 3, cluster A, idx 1', F,
             (1, DIR_A, TABLE_CELL, 3), flag_only)
    scenario('C3 companion, flag SET, staged, cluster B != last run A, idx 0', F,
             (0, DIR_B, TABLE_CELL, 1), staged_pos1)
    scenario('C4 companion, flag SET, staged, sentinel cluster arg, idx 0', F,
             (0, 0x0FFFFFF7, TABLE_CELL, 1), staged_pos1)
    scenario('C5 companion, flag clear, cluster == root, idx 2', F,
             (2, ROOT, TABLE_CELL, 1), None)

    # Control: with the flag set and discriminator-passing arguments
    # the hook MUST engage (results differ from stock), proving the
    # equivalence above is not vacuous.
    run = Run(tail_regions)
    stage_playlist(run.uc)
    got = run.call(R, 0, CTXDESC, TABLE_CELL, 1)
    cl, tot, ctx = desc_fields(run.uc)
    engaged = (got['regs']['r0'] == 0 and cl == DIR_A and ctx == ctx_bytes(DIR_A)
               and run.model.log == [])
    ok_all = ok_all and engaged
    print(f'  [{"PASS" if engaged else "FAIL"}] control: flag set + '
          f'discriminator-passing call engages the substitution '
          f'(served cluster {cl:#x}, no stock callees ran)')
    print(f'  part (b): {"ALL PASS" if ok_all else "FAILURES"}')
    return ok_all


# ------------------------------------------------------------- part (c)

def part_c(tail_regions):
    print('== Part (c): staged traversal, flag set ==')
    ok = True

    def check(desc, cond):
        nonlocal ok
        print(f'    [{"PASS" if cond else "FAIL"}] {desc}')
        ok = ok and cond

    run = Run(tail_regions)
    stage_playlist(run.uc)

    def primary(i):
        out = run.call(RESOLVER, i, CTXDESC, TABLE_CELL, 1)
        cl, tot, ctx = desc_fields(run.uc)
        pos, resid = header_state(run.uc)
        return out['regs']['r0'], cl, tot, ctx, pos, resid

    print('  primary-hook sequence (module 33 index presentation):')
    r = primary(0)
    print(f'    first track: i=0 -> ret {r[0]}, cluster {r[1]:#x}, total {r[2]}, pos {r[4]}, resid {r[5]}')
    check('serves entry 0: ret 0, run A cluster, run A total 3, run A context',
          r[0] == 0 and r[1] == DIR_A and r[2] == 3 and r[3] == ctx_bytes(DIR_A)
          and r[4] == 0 and r[5] == 0)
    r = primary(1)
    print(f'    next in run: i=1 -> ret {r[0]}, cluster {r[1]:#x}, pos {r[4]}, resid {r[5]}')
    check('next within run: entry 1 (within 2), same cluster and context',
          r[0] == 2 and r[1] == DIR_A and r[3] == ctx_bytes(DIR_A)
          and r[4] == 1 and r[5] == 2)
    r = primary(3)
    print(f'    next across boundary: i=3 -> ret {r[0]}, cluster {r[1]:#x}, total {r[2]}, pos {r[4]}, resid {r[5]}')
    check('next across the run boundary: entry 2, run B cluster, total 1+2=3, run B context',
          r[0] == 0 and r[1] == DIR_B and r[2] == 3 and r[3] == ctx_bytes(DIR_B)
          and r[4] == 2 and r[5] == 0)
    r = primary(0xFFFF)
    print(f'    previous: i=0xFFFF (resid-1) -> ret {r[0]}, cluster {r[1]:#x}, pos {r[4]}, resid {r[5]}')
    check('previous back across the boundary: entry 1 in run A',
          r[0] == 2 and r[1] == DIR_A and r[3] == ctx_bytes(DIR_A)
          and r[4] == 1 and r[5] == 2)
    r = primary(3)
    check('next again: entry 2 in run B',
          r[0] == 0 and r[1] == DIR_B and r[4] == 2 and r[5] == 0)
    r = primary(1)
    print(f'    past the end: i=1 -> ret {r[0]}, cluster {r[1]:#x}, pos {r[4]}, resid {r[5]}')
    check('past-the-end sentinel: last run cluster/context, residual == countA of last run (1), position == count (3)',
          r[0] == 1 and r[1] == DIR_B and r[3] == ctx_bytes(DIR_B)
          and r[4] == 3 and r[5] == 1)
    check('no stock callees ran during the primary traversal',
          run.model.log == [])

    print('  companion-hook sequence (path B presentation):')
    run2 = Run(tail_regions)
    stage_playlist(run2.uc)
    run2.call(RESOLVER, 0, CTXDESC, TABLE_CELL, 1)
    run2.call(RESOLVER, 1, CTXDESC, TABLE_CELL, 1)   # pos 1, resid 2, run A
    r = companion_c(run2, 3, DIR_A)
    print(f'    path B next: idx 3, cluster arg A -> ret {r[0]}, descriptor cluster {r[1]:#x}, pos {r[4]}, resid {r[5]}')
    check('companion crosses the directory boundary: descriptor now run B, ret 0',
          r[0] == 0 and r[1] == DIR_B and r[3] == ctx_bytes(DIR_B)
          and r[4] == 2 and r[5] == 0)
    r = companion_c(run2, 1, DIR_B)
    print(f'    path B past end: idx 1, cluster arg B -> ret {r[0]}, descriptor cluster {r[1]:#x}, pos {r[4]}, resid {r[5]}')
    check('companion sentinel: residual == countA of last run (1), position == count (3)',
          r[0] == 1 and r[1] == DIR_B and r[4] == 3 and r[5] == 1)
    check('no stock callees ran during the companion sequence',
          run2.model.log == [])
    print(f'  part (c): {"ALL PASS" if ok else "FAILURES"}')
    return ok


def companion_c(run, i, cluster):
    out = run.call(FETCH, i, cluster, TABLE_CELL, 1)
    cl, tot, ctx = desc_fields(run.uc)
    pos, resid = header_state(run.uc)
    return out['regs']['r0'], cl, tot, ctx, pos, resid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, default=STOCK_IMG)
    parser.add_argument('--image', type=Path, required=True)
    args = parser.parse_args()
    stock_regions = module0_regions(args.stock)
    tail_regions = module0_regions(args.image)
    ok_b = part_b(stock_regions, tail_regions)
    ok_c = part_c(tail_regions)
    print()
    print('ALL PASS' if ok_b and ok_c else 'SOME CASES FAILED')
    return 0 if ok_b and ok_c else 1


if __name__ == '__main__':
    raise SystemExit(main())
