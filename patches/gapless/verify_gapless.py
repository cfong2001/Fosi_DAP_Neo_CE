#!/usr/bin/env python3
"""Verify the gapless patch set (0010-0015, plus the unstacked ARM patch
0016) against the framework build, stacked on the DAC set (0000-0002).

Checks:
  1. Input is the pinned stock image; the stock file is byte-identical
     after the run (the build never modifies its input).
  2. Three builds succeed and pass firmware_patch.validate():
       A = 0000-0002 (DAC baseline)
       B = A + gapless 0010-0015 (the shipped, DISARMED set)
       C = B + 0016 (ARMED variant)
  3. The whole-file diff B-vs-A is confined to exactly the six named
     gapless sites (module/region/address/length), nothing else.
  4. The whole-file diff C-vs-B is confined to the single ARM byte pair
     at 0x03051674.
  5. The full production manifest (0000-0018, clock set included) also
     accepts the gapless set stacked after it (scratch-renumbered
     0020-0025; contents unchanged) and validates.
  6. Before/after disassembly of every patched site (A vs B, and the
     ARM site in C).

Run:  ~/workspace/fosi-dap-neo/venv/bin/python verify_gapless.py
Exit code 0 = all checks passed.
"""
import hashlib
import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

WS = Path(__file__).resolve().parents[3]          # ~/workspace/fosi-dap-neo
HERE = Path(__file__).resolve().parent
FW = WS / 'work' / 'patches' / 'framework'
STOCK = WS / 'DP3_V137.img'
sys.path.insert(0, str(WS / 'repo' / 'tools'))
import firmware_patch as fp                       # noqa: E402
from rknano_image import Image                    # noqa: E402

spec = importlib.util.spec_from_file_location('fwbuild', FW / 'build.py')
fwbuild = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fwbuild)

DATE = '20261023'
fails = []


def check(name, ok, detail=''):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ''))
    if not ok:
        fails.append(name)


def parse(d, names):
    return [fwbuild.parse_patch(d / n) for n in names]


BASE_NAMES = ['0000-noop-selftest.patch', '0001-dac-fix-branch.patch',
              '0002-dac-fix-cave.patch']
GAP_NAMES = ['0010-gapless-state-pair.patch', '0011-gapless-gate-hook.patch',
             '0012-gapless-gate-cave.patch', '0013-gapless-delay-cave.patch',
             '0014-gapless-delay-hook.patch', '0015-gapless-delay-pool.patch']

SITES = [  # (module, region, exec address, length) -- the named gapless sites
    (0, 'code', 0x030515B0, 8),    # 0010 state pair
    (0, 'code', 0x0306CB2C, 4),    # 0011 gate hook
    (0, 'code', 0x03051664, 32),   # 0012 gate cave
    (0, 'code', 0x030514FE, 26),   # 0013 delay cave
    (33, 'code', 0x03088FEA, 4),   # 0014 delay hook
    (0, 'code', 0x03051684, 4),    # 0015 delay pool
]
ARM_SITE = (0, 'code', 0x03051674, 2)

stock = STOCK.read_bytes()
sha0 = hashlib.sha256(stock).hexdigest()
check('input is pinned stock', sha0 == fp.STOCK_SHA256, sha0[:16])

base = parse(FW / 'patches', BASE_NAMES)
gap = parse(HERE, GAP_NAMES)
arm = parse(HERE, ['0016-gapless-arm.patch'])

outA, _ = fwbuild.build_image(stock, base, DATE)
outB, _ = fwbuild.build_image(stock, base + gap, DATE)
outC, _ = fwbuild.build_image(stock, base + gap + arm, DATE)
for nm, out in [('A (DAC baseline)', outA), ('B (gapless disarmed)', outB),
                ('C (gapless armed)', outC)]:
    fp.validate(out)
    check(f'build {nm} validates', True, hashlib.sha256(out).hexdigest()[:16])


def site_file_ranges(img_bytes, sites):
    im = Image(img_bytes)
    out = []
    for mod, region, addr, ln in sites:
        m = im.modules[mod]
        base_off, _ = im.module_region(mod, region)
        out.append((base_off + (addr - m[region + '_exec']), ln))
    return sorted(out)


def diff_runs(a, b):
    """Differing byte runs between equal-length images (chunk-skipping)."""
    runs = []
    n = len(a)
    CH = 1 << 20
    open_run = None
    for cs in range(0, n, CH):
        ce = min(n, cs + CH)
        if a[cs:ce] == b[cs:ce]:
            if open_run is not None:
                runs.append(open_run)
                open_run = None
            continue
        for i in range(cs, ce):
            if a[i] != b[i]:
                if open_run is None:
                    open_run = [i, 1]
                else:
                    open_run[1] = i - open_run[0] + 1
            elif open_run is not None:
                runs.append(tuple(open_run))
                open_run = None
    if open_run is not None:
        runs.append(tuple(open_run))
    return runs


def runs_within(runs, allowed):
    """Every diff run must be covered by the union of allowed ranges."""
    for off, ln in runs:
        cur = off
        for aoff, aln in allowed:
            if aoff <= cur < aoff + aln:
                cur = min(off + ln, aoff + aln)
        if cur < off + ln:
            return False
    return True


CRC_RANGE = [(len(outA) - 4, 4)]  # finalize() rewrites the trailer CRC
allowedB = site_file_ranges(outA, SITES)
runsB = diff_runs(outA, outB)
check('diff B-vs-A confined to the 6 named sites + trailer CRC',
      runs_within(runsB, allowedB + CRC_RANGE) and
      sum(ln for _, ln in runsB) <= sum(s[3] for s in SITES) + 4,
      f'{len(runsB)} runs, {sum(ln for _, ln in runsB)} bytes '
      f'(sites hold {sum(s[3] for s in SITES)} patch bytes; bytes that '
      f'coincidentally equal the stock stub bytes do not diff)')
changed = set()
for off, ln in runsB:
    for aoff, aln in allowedB:
        if off < aoff + aln and aoff < off + ln:   # overlap
            changed.add(aoff)
check('every named site changed', len(changed) == len(SITES),
      f'{len(changed)}/{len(SITES)} sites')

allowedC = site_file_ranges(outB, [ARM_SITE])
runsC = diff_runs(outB, outC)
check('diff C-vs-B confined to the ARM site + trailer CRC',
      runs_within(runsC, allowedC + CRC_RANGE) and
      any(off < allowedC[0][0] + 2 and allowedC[0][0] < off + ln
          for off, ln in runsC),
      f'{runsC} vs site {allowedC} + CRC {CRC_RANGE}')

# ---- full production manifest stacking (clock set included) ----
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    pdir = td / 'patches'
    pdir.mkdir()
    manifest = []
    for n in (FW / 'patches' / 'manifest.txt').read_text().splitlines():
        n = n.split('#', 1)[0].strip()
        if n:
            shutil.copy(FW / 'patches' / n, pdir / n)
            manifest.append(n)
    for i, n in enumerate(GAP_NAMES):
        nn = f'{20 + i:04d}-' + n.split('-', 1)[1]
        shutil.copy(HERE / n, pdir / nn)
        manifest.append(nn)
    (pdir / 'manifest.txt').write_text('\n'.join(manifest) + '\n')
    patches = fwbuild.load_manifest(pdir / 'manifest.txt')
    outF, _ = fwbuild.build_image(stock, patches, DATE)
    fp.validate(outF)
    check('full manifest 0000-0018 + gapless (as 0020-0025) builds + validates',
          True, hashlib.sha256(outF).hexdigest()[:16])

# ---- before/after disassembly ----
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS  # noqa: E402
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)


def region_bytes(img_bytes, mod, region, addr, ln):
    im = Image(img_bytes)
    m = im.modules[mod]
    base_off, _ = im.module_region(mod, region)
    off = base_off + (addr - m[region + '_exec'])
    return img_bytes[off:off + ln]


print('\n--- before/after disassembly (A -> B) ---')
for mod, region, addr, ln in SITES:
    print(f'site mod{mod} {region} @{addr:#010x} ({ln} B):')
    for tag, img in [('before', outA), ('after ', outB)]:
        blob = region_bytes(img, mod, region, addr, ln)
        txt = '; '.join(f'{i.mnemonic} {i.op_str}' for i in md.disasm(blob, addr))
        print(f'  {tag}: {blob.hex()}')
        if txt:
            print(f'         {txt}')
print('ARM site @0x03051674 (B -> C):')
for tag, img in [('disarmed', outB), ('armed   ', outC)]:
    blob = region_bytes(img, *ARM_SITE)
    ins = next(md.disasm(blob, ARM_SITE[2]))
    print(f'  {tag}: {blob.hex()}  {ins.mnemonic} {ins.op_str}')

check('stock file untouched',
      hashlib.sha256(STOCK.read_bytes()).hexdigest() == sha0)

print(f"\n{'ALL CHECKS PASSED' if not fails else 'FAILURES: ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
