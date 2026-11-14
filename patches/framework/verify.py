#!/usr/bin/env python3
"""Round-trip + tamper verification for the patch framework.

Proves, against the real stock image:
  1. A zero-patch build differs from stock ONLY in the header date and
     the mirror/CRC fields that the date change implies.
  2. The shipped manifest (no-op self-test + DAC fix + clock v1,
     framework-only) applies all 31 patches and reproduces the known
     1,400-byte stacked diff, with a consistent report.
  3. A tampered input image (one flipped byte at the self-test patch's
     target) makes the build refuse (stock SHA gate).
  4. The patch's expected-bytes precondition itself fails loudly when
     the apply step is run against that tampered image directly.
  5. Feeding a build output back in as input is refused (not stock).
  6. A recovery build (zero patches, build date + 1) validates and
     stays inside the same allowed diff regions.
  7. The UNIFIED build (byte patches + the vorbis75 transplant)
     combines correctly: outside module 75 it is byte-identical to
     the framework-only build, module 75 matches the pinned
     transplant hash from patches/vorbis_swap/DEPENDENCY.md, its
     total diff is confined to the union of its parts' diffs, and
     two runs produce byte-identical output. Skipped (not failed)
     when the .ecpatch inputs are not locatable — see
     tools/fosi_paths.py for FOSI_ECPATCH_DIR.
  10. The theme step (--theme-config, check 10 below): the default
      unified build still reproduces its pinned whole-image hash;
      the studio's example theme recolours exactly the counted
      pixels of resources 6 to 10, its diff against the default
      build confined to those resources' pixel ranges; the
      runs-only CE mark config changes exactly the bytes its runs change
      (and only inside them); and a tampered expected count, a guard-word source,
      a run with wrong expected bytes, and --theme-config with
      --recovery are all refused. Skipped on the same condition
      as check 7.
  11. The OPUS variant build (patches/opus_swap/, check 11
      below): the opus72 transplant plus the five WMA-to-OPU
      classifier rename patches is checked the same way
      against the default build: its module 72 matches the
      pinned transplant hash from
      patches/opus_swap/DEPENDENCY.md, its diff vs the unified
      build is confined to module 72, the five rename sites
      and the trailer CRC, and the default unified build still
      reproduces its pinned whole-image hash. Skipped on the
      same condition as check 7.
  12. The THEATER variant build (patches/theater/build/,
      check 12 below): the default build plus five module 18
      hook patches and a tail payload; its diff vs the unified
      build is confined to the hook sites, the gap tail span,
      the module 0 code_len record and the trailer CRC, and
      the default unified build still reproduces its pinned
      whole-image hash. Skipped on the same condition as
      check 7.
  13. The FULL build (patches/full/, check 13 below): every
      feature composed in one pass (143 patches, both
      transplants, two growth insertions, the merged gap
      tail, the merged theme config). Its whole-image hash and
      length are pinned; every segment of the composed image
      is byte-identical to the default unified build except
      inside the union of its parts (patch sites, growth
      payloads, the tail span, module 72's transplant scope,
      the theme runs, header bookkeeping and the CRCs); and
      the default unified build still reproduces its pinned
      whole-image hash. Skipped on the same condition as
      check 7.
  14. The DAC filter option (--dac-filter, patches/dac_filter/):
      each of the four filter builds differs from the framework-only
      default build in exactly one byte, the movs immediate at exec
      0x03051814 (file 0x2AEC0), set to that filter's register
      value, plus the trailer CRC; the report names the filter; and
      --dac-filter with --recovery is refused. Needs no transplant
      inputs, so it never skips.
  15. The Bluetooth auto-off option (--bt-auto-off,
      patches/bt_auto_off/): the 10min build differs from the
      framework-only default only in the supervisor's movw immediate
      (file 0x3F88C..0x3F88F), the never build only in its bls.w
      (file 0x3F892..0x3F895), each plus the trailer CRC; the report
      names the option; --bt-auto-off with --recovery is refused.

Run:  python verify.py     (paths resolve via tools/fosi_paths.py)
Exit code 0 = all checks passed. Build artifacts land in a temp dir.
"""
import hashlib
import importlib.util
import json
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path


def _tools_dir():
    here = Path(__file__).resolve()
    roots = [Path(os.environ['FOSI_REPO_ROOT'])] if os.environ.get('FOSI_REPO_ROOT') else []
    roots += [here.parent, *here.parents]
    for r in roots:
        for cand in (r / 'tools', r / 'repo' / 'tools'):
            if (cand / 'firmware_patch.py').exists():
                return cand
    raise SystemExit('cannot locate repo tools/ (set FOSI_REPO_ROOT)')


HERE = Path(__file__).resolve().parent
TOOLS = _tools_dir()
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(HERE / 'tools'))
REPO = TOOLS.parent
BUILD = HERE / 'build.py'

import fosi_paths  # noqa: E402
import firmware_patch as fp  # noqa: E402

STOCK = fosi_paths.stock_image_path(REPO)

spec = importlib.util.spec_from_file_location('fwbuild', BUILD)
fwbuild = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fwbuild)

MIRROR_OFF = 0xC94000
results = []


def check(name, ok, detail=''):
    results.append((name, ok))
    tag = 'PASS' if ok else ('SKIP' if ok is None else 'FAIL')
    print(f'{tag}  {name}' + (f' — {detail}' if detail else ''))


def diff_offsets(a, b):
    return {i for i in range(len(a)) if a[i] != b[i]}


def allowed_offsets(n):
    return set(range(0, 4)) | set(range(MIRROR_OFF, MIRROR_OFF + 4)) | set(range(n - 4, n))


def run_build(args):
    return subprocess.run([sys.executable, str(BUILD), *args],
                          capture_output=True, text=True)


def main():
    stock = STOCK.read_bytes()
    n = len(stock)
    allowed = allowed_offsets(n)
    tmp = Path(tempfile.mkdtemp(prefix='neo-fw-verify-'))
    print(f'verify artifacts: {tmp}')

    # -- 1. zero-patch build -------------------------------------------
    empty_manifest = tmp / 'empty-manifest.txt'
    empty_manifest.write_text('# no patches enabled\n')
    out1 = tmp / 'zero.img'
    r = run_build(['--input', str(STOCK), '--output', str(out1),
                   '--manifest', str(empty_manifest), '--no-transplants'])
    ok = r.returncode == 0 and out1.exists()
    detail = r.stderr.strip()
    if ok:
        img1 = out1.read_bytes()
        extra = diff_offsets(stock, img1) - allowed
        fp.validate(img1)
        ok = not extra and img1[:4] == fp.bcd_date('20261023')
        detail = (f'diff offsets {sorted(hex(x) for x in diff_offsets(stock, img1))}, '
                  f'date 20261023, validate() passed')
    check('zero-patch build: diff confined to date + mirror + CRC', ok, detail)

    # -- 2. shipped manifest, framework-only (no transplants) -----------
    # The manifest carries the no-op self-test, the DAC fix, the
    # 16 clock-v1 patches, the DAC-bus I2C reset patch (0019), the
    # gapless v2 set 0020-0025 with its ARM patch 0026 (whose 2 bytes
    # land inside the 0022 cave), the 5 sort-key patches and the wheel
    # power patch: 34 patches (with the gapless warm start 0034), a known
    # 1,400-byte diff vs stock.
    out2 = tmp / 'manifest.img'
    r = run_build(['--input', str(STOCK), '--output', str(out2),
                   '--no-transplants'])
    ok = r.returncode == 0 and out2.exists()
    detail = r.stderr.strip()
    if ok:
        img2 = out2.read_bytes()
        report = json.loads(Path(str(out2) + '.report.json').read_text())
        applied = report['patches_applied']
        ok = (len(applied) == 34
              and applied[0]['patch'] == 'noop-selftest'
              and applied[0]['old_hex'] == applied[0]['new_hex']
              and report['diff_vs_stock']['bytes_changed'] ==
              len(diff_offsets(stock, img2)) == 1400
              and report['transplants_applied'] == [])
        detail = (f"patches applied: {len(applied)} "
                  f"({applied[0]['patch']} … {applied[-1]['patch']}), "
                  f"bytes changed: {report['diff_vs_stock']['bytes_changed']}")
    check('shipped manifest build: 34 patches, known 1,400-byte diff, '
          'report consistent', ok, detail)

    # -- 3. tampered input refused by the SHA gate -----------------------
    tampered = bytearray(stock)
    tampered[0x296AC] ^= 0xFF          # first byte of the self-test target
    bad_in = tmp / 'tampered.img'
    bad_in.write_bytes(bytes(tampered))
    r = run_build(['--input', str(bad_in), '--output', str(tmp / 'never.img')])
    check('tampered input: build refuses (SHA gate)',
          r.returncode != 0 and 'BUILD REFUSED' in r.stderr
          and not (tmp / 'never.img').exists(),
          r.stderr.strip().split('\n')[0][:120])

    # -- 4. expect-bytes precondition fails loudly -----------------------
    noop = fwbuild.load_manifest(HERE / 'patches' / 'manifest.txt')
    try:
        fwbuild.apply_patches(bytes(tampered), noop)
        check('tampered target: expect-bytes precondition fails loudly',
              False, 'apply_patches returned without raising')
    except ValueError as e:
        check('tampered target: expect-bytes precondition fails loudly',
              'precondition mismatch' in str(e), str(e)[:120])

    # -- 5. build output is not accepted as input ------------------------
    r = run_build(['--input', str(out1), '--output', str(tmp / 'never2.img')])
    check('feedback of build output as input: refused',
          r.returncode != 0 and 'BUILD REFUSED' in r.stderr,
          r.stderr.strip().split('\n')[0][:120])

    # -- 6. recovery build ------------------------------------------------
    out6 = tmp / 'recovery.img'
    r = run_build(['--input', str(STOCK), '--output', str(out6), '--recovery'])
    ok = r.returncode == 0 and out6.exists()
    detail = r.stderr.strip()
    if ok:
        img6 = out6.read_bytes()
        extra = diff_offsets(stock, img6) - allowed
        fp.validate(img6)
        ok = not extra and img6[:4] == fp.bcd_date('20261024')
        detail = 'date 20261024 (build+1), validate() passed, diff in allowed regions'
    check('recovery build: stock bytes, later date, validates', ok, detail)

    # -- 7. unified build: combined effects of patches + transplant -----
    ecp = fosi_paths.ecpatch_dir(REPO)
    if ecp is None:
        check('unified build: combined effects verified', None,
              'ecpatch inputs not found — set FOSI_ECPATCH_DIR '
              '(see patches/vorbis_swap/DEPENDENCY.md)')
    else:
        u1, u2, fo = tmp / 'unified1.img', tmp / 'unified2.img', tmp / 'framework-only.img'
        r1 = run_build(['--input', str(STOCK), '--output', str(u1),
                        '--ecpatch-dir', str(ecp)])
        r2 = run_build(['--input', str(STOCK), '--output', str(u2),
                        '--ecpatch-dir', str(ecp)])
        r3 = run_build(['--input', str(STOCK), '--output', str(fo),
                        '--no-transplants'])
        ok = all(r.returncode == 0 for r in (r1, r2, r3)) \
            and all(p.exists() for p in (u1, u2, fo))
        detail = (r1.stderr + r3.stderr).strip()[:160]
        if ok:
            u, f = u1.read_bytes(), fo.read_bytes()
            fp.validate(u)
            im = fwbuild.Image(stock)
            co, cl = im.module_region(75, 'code')
            do, dl = im.module_region(75, 'data')
            regions = set(range(co, co + cl)) | set(range(do, do + dl))
            # The trailer CRC (last 4 bytes) is derived from the whole
            # image, so it legitimately differs between the two builds;
            # date + mirror carry identical values in both.
            outside_same = all(u[i] == f[i] for i in range(n - 4)
                               if i not in regions)
            mod_ok = hashlib.sha256(u[co:co + cl] + u[do:do + dl]).hexdigest() == \
                'dd8f772fb5c7fa128ed5bdfde99401cff66798847eb6c993feea89a0997ab695'
            du, df = diff_offsets(stock, u), diff_offsets(stock, f)
            confined = du <= (df | regions | allowed)
            repro = u1.read_bytes() == u2.read_bytes()
            ok = outside_same and mod_ok and confined and repro
            detail = (f'outside module 75 == framework-only build: {outside_same}; '
                      f'module 75 == pinned transplant hash: {mod_ok}; '
                      f'diff confined to union of parts: {confined}; '
                      f'two builds byte-identical: {repro}; '
                      f'unified diff {len(du)} bytes, '
                      f'sha {hashlib.sha256(u).hexdigest()[:16]}…')
        check('unified build: combined effects verified', ok, detail)

    # -- 8. gap tail build ----------------------------------------------
    # A tail build must equal the default framework-only build
    # (check 2's image) at every byte outside the gap span, the
    # module 0 code_len record field, and the trailer CRC (a derived
    # field). The span's workspace zone (everything before the tail
    # payload) must be all zero in the output: that is the safety
    # property replacing the removed raw extension step, which let a
    # caller place code at the gap base inside live FAT workspace.
    # Oversize payloads, range overlaps and a non-zero gap must all
    # be refused.
    payload = bytes((i * 37 + 11) & 0xFF for i in range(2000))
    payload_path = tmp / 'tail-payload.bin'
    payload_path.write_bytes(payload)
    out8 = tmp / 'tail.img'
    r = run_build(['--input', str(STOCK), '--output', str(out8),
                   '--no-transplants', '--tail', str(payload_path)])
    ok = r.returncode == 0 and out8.exists()
    detail = r.stderr.strip()[:160]
    span = 0x2B9C                       # gap span, exec 0x03079C14..0x0307C7B0
    tail_file = 0x532C0 + 0x23A0        # tail payload file offset
    if ok:
        b = out8.read_bytes()
        fp.validate(b)
        ext_allowed = (set(range(0x532C0, 0x532C0 + span))
                       | set(range(0x210, 0x214)) | set(range(n - 4, n)))
        extra = diff_offsets(img2, b) - ext_allowed
        base, ln = fwbuild.Image(b).module_region(0, 'code')
        rep8 = json.loads(Path(str(out8) + '.report.json').read_text())
        ok = (not extra and base == 0x296AC and ln == 0x29C14 + span
              and b[tail_file:tail_file + len(payload)] == payload
              and not any(b[0x532C0:tail_file])
              and rep8['tail']['code_len_new'] == hex(0x29C14 + span)
              and rep8['tail']['payload_bytes'] == len(payload)
              and rep8['tail']['workspace_zone_zero_bytes'] == 0x23A0)
        detail = (f'outside-diff vs default build: {len(extra)} bytes; '
                  f'module 0 code region {hex(base)} len {hex(ln)}; '
                  f'workspace zone all zero; validate() passed')
    big_path = tmp / 'tail-big.bin'
    big_path.write_bytes(bytes(fwbuild.TAIL_MAX + 1))
    r = run_build(['--input', str(STOCK), '--output', str(tmp / 'never8.img'),
                   '--no-transplants', '--tail', str(big_path)])
    ok_big = (r.returncode != 0 and 'BUILD REFUSED' in r.stderr
              and 'tail' in r.stderr
              and not (tmp / 'never8.img').exists())
    unit_ok, unit_detail = True, ''
    try:
        fwbuild.apply_tail(stock, payload, [[0x532C0, 0x532FF]])
        unit_ok, unit_detail = False, 'overlap not refused'
    except ValueError as e:
        unit_detail = f'overlap refused ({str(e)[:60]}…)'
    if unit_ok:
        dirty = bytearray(stock)
        dirty[0x532C0 + 10] = 1
        try:
            fwbuild.apply_tail(bytes(dirty), payload, [])
            unit_ok, unit_detail = False, 'non-zero gap not refused'
        except ValueError:
            pass
    check('tail build: confined diff + workspace zone zero + '
          'validate; oversize/overlap/dirty-gap refused',
          bool(ok and ok_big and unit_ok),
          f'{detail}; oversize refused: {ok_big}; {unit_detail}')
    # -- 9. grown build: segment-insertion isolation. A 1,000-byte
    # patterned growth of module 31 code must leave every other
    # module's extracted segments byte-identical, grow module 31's
    # code by exactly the pattern at its tail, and compose with the
    # full shipped build (manifest + transplant) unchanged.
    from validate_grown import validate_grown
    pattern = bytes((i * 31 + 7) & 0xFF for i in range(1000))
    pat_path = tmp / 'grow-pattern.bin'
    pat_path.write_bytes(pattern)
    empty_manifest = tmp / 'empty-manifest.txt'
    empty_manifest.write_text('# empty: growth isolation\n')
    gout = tmp / 'grown.img'
    r = run_build(['--input', str(STOCK), '--output', str(gout),
                   '--manifest', str(empty_manifest),
                   '--no-transplants', '--grow', f'31:code:{pat_path}'])
    ok = r.returncode == 0 and gout.exists()
    detail = r.stderr.strip()[:160]
    if ok:
        g = gout.read_bytes()
        validate_grown(g)
        sim, gim = fwbuild.Image(stock), fwbuild.Image(g)
        iso = True
        for m in sim.modules:
            i = m['index']
            for kind in ('code', 'data'):
                so, sl = sim.module_region(i, kind)
                go, gl = gim.module_region(i, kind)
                sb, gb = stock[so:so + sl], g[go:go + gl]
                if i == 31 and kind == 'code':
                    iso &= (gl == sl + len(pattern)
                            and gb == sb + pattern)
                else:
                    iso &= (gb == sb)
        grep = json.loads(Path(str(gout) + '.report.json').read_text())
        ok = (iso and len(g) == n + 1024     # 1,000 B + 24 B sector pad
              and grep['growth'] and grep['growth'][0]['module'] == 31
              and grep['growth'][0]['payload_bytes'] == len(pattern))
        detail = (f'all non-grown segments identical: {iso}; '
                  f'length {n} -> {len(g)}; validate_grown passed')
    r2 = run_build(['--input', str(STOCK), '--output', str(tmp / 'grown-full.img'),
                    '--grow', f'31:code:{pat_path}'])
    ok_full = r2.returncode == 0 and (tmp / 'grown-full.img').exists()
    if ok_full:
        frep = json.loads(
            Path(str(tmp / 'grown-full.img') + '.report.json').read_text())
        ok_full = (len(frep['growth']) == 1
                   and len(frep['patches_applied']) == 34
                   and len(frep['transplants_applied']) == 1)
    check('grown build: segment isolation + full-build composition',
          bool(ok and ok_full),
          f'{detail}; full build with growth: {ok_full}')

    # -- 10. theme build: --theme-config consumer ----------------------
    # The default unified build must still reproduce its pinned
    # whole-image hash, proving the theme step changes nothing when
    # no config is given. The studio's example theme must recolour
    # exactly the counted pixels of resources 6 to 10: the diff vs
    # the default build stays inside those resources' pixel ranges
    # and changes exactly twice the summed expected counts (the
    # trailer CRC is derived from the whole image and is exempt,
    # as in check 7). The runs-only CE mark config must change
    # exactly the bytes its runs change and nothing else. A tampered
    # expected count, a guard-word source, a run whose expected
    # bytes are wrong, and --theme-config with --recovery refuse.
    THEME_DIR = HERE.parent / 'theme_editor'
    if ecp is None:
        check('theme build: pinned default, confined example and CE '
              'mark diffs, refusals hold', None,
              'ecpatch inputs not found; set FOSI_ECPATCH_DIR '
              '(see patches/vorbis_swap/DEPENDENCY.md)')
    else:
        dflt = tmp / 'theme-default.img'
        rd = run_build(['--input', str(STOCK), '--output', str(dflt),
                        '--ecpatch-dir', str(ecp)])
        ok = rd.returncode == 0 and dflt.exists()
        detail = rd.stderr.strip()[:160]
        if ok:
            dimg = dflt.read_bytes()
            fp.validate(dimg)
            default_ok = hashlib.sha256(dimg).hexdigest() == \
                '0dfd10e23749f9b6c65499266f1a7a2ec038160b089ba0fc2ca68dcf2b24c986'
            entries = {e['id']: e
                       for e in fwbuild._rock26_resources(stock)}
            crc = set(range(n - 4, n))
            example = json.loads(
                (THEME_DIR / 'theme.example.json').read_text())
            ex_allowed = set()
            for rule in example['resources']:
                ent = entries[rule['id']]
                ex_allowed |= set(range(
                    ent['data_offset'], ent['data_offset'] + ent['size']))
            ex_total = sum(rule['expected_count']
                           for rule in example['resources'])
            tex = tmp / 'theme-example.img'
            r = run_build(['--input', str(STOCK), '--output', str(tex),
                           '--ecpatch-dir', str(ecp),
                           '--theme-config',
                           str(THEME_DIR / 'theme.example.json')])
            ex_ok = r.returncode == 0 and tex.exists()
            if ex_ok:
                timg = tex.read_bytes()
                fp.validate(timg)
                content = diff_offsets(dimg, timg) - crc
                trep = json.loads(
                    Path(str(tex) + '.report.json').read_text())
                ex_ok = (content <= ex_allowed
                         and len(content) == 2 * ex_total
                         and trep['theme']['pixels_changed'] == ex_total
                         and len(trep['theme']['resources']) == 5)
            ce = json.loads((THEME_DIR / 'ce-mark.json').read_text())
            ce_allowed = set()
            ce_changed = 0          # bytes the runs actually change
            ce_written = 0          # bytes the runs write (the report's count)
            for run in ce['runs']:
                o = int(run['offset'], 16)
                ce_written += len(bytes.fromhex(run['expect']))
                ce_allowed |= set(range(
                    o, o + len(bytes.fromhex(run['expect']))))
                ce_changed += sum(a != b for a, b in zip(
                    bytes.fromhex(run['expect']), bytes.fromhex(run['replace'])))
            tce = tmp / 'theme-ce.img'
            r = run_build(['--input', str(STOCK), '--output', str(tce),
                           '--ecpatch-dir', str(ecp),
                           '--theme-config', str(THEME_DIR / 'ce-mark.json')])
            ce_ok = r.returncode == 0 and tce.exists()
            if ce_ok:
                cimg = tce.read_bytes()
                fp.validate(cimg)
                content = diff_offsets(dimg, cimg) - crc
                crep = json.loads(
                    Path(str(tce) + '.report.json').read_text())
                ce_ok = (content <= ce_allowed and len(content) == ce_changed
                         and crep['theme']['bytes_changed'] == ce_written
                         and len(crep['theme']['runs']) == len(ce['runs']))

            # Code colours: the four accent/line roles rewrite exactly
            # their eight movw sites in module 0 and nothing else.
            cc = json.loads(
                (THEME_DIR / 'code-colours.example.json').read_text())
            mimg = fwbuild.Image(dimg)
            moff, _ = mimg.module_region(0, 'code')
            mexec = mimg.modules[0]['code_exec']
            cc_sites = {}
            for role, (stock_w, sites) in fwbuild.CODE_COLOUR_SITES.items():
                for a in sites:
                    cc_sites[moff + a - mexec] = fwbuild._theme_rgb565(
                        cc['code_colours'][role])
            tcc = tmp / 'theme-code.img'
            r = run_build(['--input', str(STOCK), '--output', str(tcc),
                           '--ecpatch-dir', str(ecp),
                           '--theme-config',
                           str(THEME_DIR / 'code-colours.example.json')])
            cc_ok = r.returncode == 0 and tcc.exists()
            if cc_ok:
                ximg = tcc.read_bytes()
                fp.validate(ximg)
                content = diff_offsets(dimg, ximg) - crc
                allowed = {o + i for o in cc_sites for i in range(4)}
                cc_ok = (content <= allowed and len(cc_sites) == 8
                         and all(fwbuild._movw_r0_imm(ximg[o:o + 4]) == w
                                 for o, w in cc_sites.items()))

            def refuse(cfg, name):
                p = tmp / f'theme-bad-{name}.json'
                p.write_text(json.dumps(cfg))
                out = tmp / f'theme-never-{name}.img'
                rr = run_build(['--input', str(STOCK), '--output', str(out),
                                '--ecpatch-dir', str(ecp),
                                '--theme-config', str(p)])
                return (rr.returncode != 0 and not out.exists()
                        and 'BUILD REFUSED' in rr.stderr)

            bad = json.loads((THEME_DIR / 'theme.example.json').read_text())
            bad['resources'][0]['expected_count'] += 1
            ref_ok = refuse(bad, 'count')
            bad = json.loads((THEME_DIR / 'theme.example.json').read_text())
            bad['resources'][0]['source'] = '0x0000'
            ref_ok = refuse(bad, 'guard') and ref_ok
            bad = json.loads((THEME_DIR / 'ce-mark.json').read_text())
            e0 = bad['runs'][0]['expect']
            bad['runs'][0]['expect'] = ('0' if e0[0] != '0' else '1') + e0[1:]
            ref_ok = refuse(bad, 'run') and ref_ok
            ref_ok = refuse({'version': 1, 'code_colours':
                             {'background': '#000000'}}, 'code') and ref_ok
            out = tmp / 'theme-never-recovery.img'
            rr = run_build(['--input', str(STOCK), '--output', str(out),
                            '--theme-config',
                            str(THEME_DIR / 'theme.example.json'),
                            '--recovery'])
            ref_ok = (rr.returncode != 0 and not out.exists()) and ref_ok
            ok = default_ok and ex_ok and ce_ok and cc_ok and ref_ok
            detail = (f'default build == pinned unified hash: '
                      f'{default_ok}; example diff confined to '
                      f'resources 6-10, {2 * ex_total} bytes: {ex_ok}; '
                      f'CE mark diff == its {ce_changed} changed bytes, inside its runs: {ce_ok}; '
                      f'code colours confined to their 8 movw sites: {cc_ok}; '
                      f'refusals hold: {ref_ok}')
        check('theme build: pinned default, confined example and CE '
              'mark diffs, refusals hold', bool(ok), detail)

    # -- 11. opus variant build (opt-in, patches/opus_swap/) ------------
    # The variant is the default build plus two things: the opus72
    # transplant and the five 3-byte WMA->OPU classifier renames.
    # It must differ from the unified build ONLY inside module 72's
    # two regions, at the five rename sites, and in the trailer CRC
    # (a derived field); its module 72 must equal the pinned
    # transplant hash; and the default unified build must still
    # reproduce its pinned whole-image hash, proving the opt-in
    # wiring left the default untouched.
    OPUS_MANIFEST = HERE.parent / 'opus_swap' / 'manifest.txt'
    OPUS_TRANSPLANTS = HERE.parent / 'opus_swap' / 'transplants.txt'
    RENAME_SITES = (0x58987, 0x589B2, 0x589DD, 0x90AF5, 0x7E4D5)
    if ecp is None:
        check('opus variant: module 72 pinned, diff confined, '
              'default build unchanged', None,
              'ecpatch inputs not found; set FOSI_ECPATCH_DIR '
              '(see patches/opus_swap/DEPENDENCY.md)')
    else:
        vout, uout = tmp / 'opus-variant.img', tmp / 'unified3.img'
        rv = run_build(['--input', str(STOCK), '--output', str(vout),
                        '--manifest', str(OPUS_MANIFEST),
                        '--transplants', str(OPUS_TRANSPLANTS),
                        '--ecpatch-dir', str(ecp)])
        ru = run_build(['--input', str(STOCK), '--output', str(uout),
                        '--ecpatch-dir', str(ecp)])
        ok = rv.returncode == 0 and ru.returncode == 0 \
            and vout.exists() and uout.exists()
        detail = (rv.stderr + ru.stderr).strip()[:160]
        if ok:
            v, u = vout.read_bytes(), uout.read_bytes()
            fp.validate(v)
            im = fwbuild.Image(stock)
            co, cl = im.module_region(72, 'code')
            do, dl = im.module_region(72, 'data')
            regions = set(range(co, co + cl)) | set(range(do, do + dl))
            sites = set()
            for s in RENAME_SITES:
                sites |= set(range(s, s + 3))
            mod_ok = hashlib.sha256(
                v[co:co + cl] + v[do:do + dl]).hexdigest() == \
                '6a7d50d2647c6623181e3cbbc16a13d2bd9a8724559d62c84f25b83ae8cbb07d'
            renames_ok = all(v[s:s + 3] == b'OPU' and u[s:s + 3] == b'WMA'
                             for s in RENAME_SITES)
            confined = diff_offsets(u, v) <= \
                (regions | sites | set(range(n - 4, n)))
            default_ok = hashlib.sha256(u).hexdigest() == \
                '0dfd10e23749f9b6c65499266f1a7a2ec038160b089ba0fc2ca68dcf2b24c986'
            vrep = json.loads(Path(str(vout) + '.report.json').read_text())
            counts_ok = (len(vrep['patches_applied']) == 39
                         and len(vrep['transplants_applied']) == 2)
            ok = (mod_ok and renames_ok and confined and default_ok
                  and counts_ok and len(v) == n)
            detail = (f'module 72 == pinned transplant hash: {mod_ok}; '
                      f'renames OPU in variant / WMA in default: '
                      f'{renames_ok}; variant-vs-default diff confined: '
                      f'{confined}; default build == pinned unified hash: '
                      f'{default_ok}; 39 patches + 2 transplants: '
                      f'{counts_ok}; variant diff vs stock '
                      f'{len(diff_offsets(stock, v))} bytes, '
                      f'sha {hashlib.sha256(v).hexdigest()[:16]}…')
        check('opus variant: module 72 pinned, diff confined, '
              'default build unchanged', ok, detail)

    # -- 12. theater variant build (opt-in, patches/theater/build/) -----
    # The variant is the default build plus five module 18 hook
    # patches and a 676-byte tail payload (reset stub + blit
    # trampoline). It must differ from the unified build ONLY at the
    # five hook sites, inside the gap tail span, at the module 0
    # code_len record, and in the trailer CRC; the hook sites must
    # carry the assembled branch bytes; and the default unified
    # build must still reproduce its pinned whole-image hash.
    THEATER_DIR = HERE.parent / 'theater' / 'build'
    HOOK_SITES = (0x97EC2, 0x98096, 0x980A2, 0x981A6, 0x981B8)
    if ecp is None:
        check('theater variant: hooks and tail confined, '
              'default build unchanged', None,
              'ecpatch inputs not found; set FOSI_ECPATCH_DIR '
              '(see patches/vorbis_swap/DEPENDENCY.md)')
    else:
        if not (THEATER_DIR / 'theater_tail.bin').exists():
            # The payload is a generated artifact (build_theater.py
            # regenerates it deterministically); build it if absent.
            subprocess.run([sys.executable,
                            str(THEATER_DIR / 'build_theater.py')],
                           check=True, capture_output=True)
        tout, uout = tmp / 'theater-variant.img', tmp / 'unified12.img'
        rv = run_build(['--input', str(STOCK), '--output', str(tout),
                        '--manifest', str(THEATER_DIR / 'manifest.txt'),
                        '--ecpatch-dir', str(ecp),
                        '--tail', str(THEATER_DIR / 'theater_tail.bin')])
        ru = run_build(['--input', str(STOCK), '--output', str(uout),
                        '--ecpatch-dir', str(ecp)])
        ok = rv.returncode == 0 and ru.returncode == 0 \
            and tout.exists() and uout.exists()
        detail = (rv.stderr + ru.stderr).strip()[:160]
        if ok:
            v, u = tout.read_bytes(), uout.read_bytes()
            fp.validate(v)
            payload = (THEATER_DIR / 'theater_tail.bin').read_bytes()
            tail_file = 0x532C0 + 0x23A0
            span = set(range(0x532C0, 0x532C0 + 0x2B9C))
            sites = set()
            for s in HOOK_SITES:
                sites |= set(range(s, s + 4))
            allowed = span | sites | set(range(0x210, 0x214)) \
                | set(range(n - 4, n))
            confined = diff_offsets(u, v) <= allowed
            payload_ok = v[tail_file:tail_file + len(payload)] == payload \
                and not any(v[0x532C0:tail_file])
            trep = json.loads(Path(str(tout) + '.report.json').read_text())
            counts_ok = (len(trep['patches_applied']) == 39
                         and len(trep['transplants_applied']) == 1
                         and trep['tail']['payload_bytes'] == len(payload))
            default_ok = hashlib.sha256(u).hexdigest() == \
                '0dfd10e23749f9b6c65499266f1a7a2ec038160b089ba0fc2ca68dcf2b24c986'
            ok = confined and payload_ok and counts_ok and default_ok
            detail = (f'variant-vs-default diff confined to hooks + '
                      f'tail span + record + CRC: {confined}; payload '
                      f'at tail with zero workspace zone: {payload_ok}; '
                      f'39 patches + 1 transplant + tail record: '
                      f'{counts_ok}; default build == pinned unified '
                      f'hash: {default_ok}; variant sha '
                      f'{hashlib.sha256(v).hexdigest()[:16]}…')
        check('theater variant: hooks and tail confined, '
              'default build unchanged', ok, detail)

    # -- 13. full build (patches/full/) --------------------------------
    # One build.py pass composing every feature: 143 patches, the
    # vorbis75 and opus72 transplants, two growth insertions
    # (module 31 +6,616, module 24 +26), the merged
    # 2,040-byte gap tail and the merged 938-run theme config. The
    # ebook reader (module 30) is not shrunk, so the image is
    # exactly the growth total longer than stock. Confinement is
    # proven per segment against the default unified build: a
    # segment may differ only inside the union of its parts (the
    # manifest's patch sites in that segment, a growth payload
    # appended at its stock end, the module 0 tail span, module
    # 72's transplant scope), and the post-segment region may
    # differ only at the theme runs, the mirrored header and
    # the trailer CRC once the growth shift is accounted for.
    FULL_DIR = HERE.parent / 'full'
    FULL_SHA = '6b6c9b503e9538a0199f67b06ffab2347a46b00493be01ff3101d14e1380079a'
    PAYLOAD_GROWTH = 7694       # module 31 + module 24 + module 39 payloads
    GROWTH_TOTAL = 8192         # sector-aligned mirror
    if ecp is None:
        check('full build: composed image pinned, diff confined '
              'to the union of its parts, default unchanged', None,
              'ecpatch inputs not found; set FOSI_ECPATCH_DIR '
              '(see patches/vorbis_swap/DEPENDENCY.md)')
    else:
        import rknano_image as rk
        fout, uout = tmp / 'full.img', tmp / 'unified13.img'
        rf = subprocess.run(
            [sys.executable, str(FULL_DIR / 'build' / 'build_full.py'),
             '--output', str(fout), '--ecpatch-dir', str(ecp)],
            capture_output=True, text=True)
        ru = run_build(['--input', str(STOCK), '--output', str(uout),
                        '--ecpatch-dir', str(ecp)])
        ok = rf.returncode == 0 and ru.returncode == 0 \
            and fout.exists() and uout.exists()
        detail = (rf.stderr + ru.stderr).strip()[-4000:]
        if ok:
            f, u = fout.read_bytes(), uout.read_bytes()
            from validate_grown import validate_grown
            validate_grown(f)
            stock = STOCK.read_bytes()
            pin_ok = hashlib.sha256(f).hexdigest() == FULL_SHA \
                and len(f) == len(stock) + GROWTH_TOTAL \
                and struct.unpack_from('<I', f, 0x1F4)[0] == MIRROR_OFF + GROWTH_TOTAL \
                and not any(f[MIRROR_OFF + PAYLOAD_GROWTH:MIRROR_OFF + GROWTH_TOTAL])
            rep = json.loads(Path(str(fout) + '.report.json').read_text())
            rep_ok = len(rep["patches_applied"]) == 184 \
                and [t['module75_sha256'] if 'module75_sha256' in t
                     else t['module72_sha256']
                     for t in rep['transplants_applied']] == [
                    'dd8f772fb5c7fa128ed5bdfde99401cff66798847eb6c993feea89a0997ab695',
                    '6a7d50d2647c6623181e3cbbc16a13d2bd9a8724559d62c84f25b83ae8cbb07d'] \
                and [(g['module'], g['payload_bytes'])
                     for g in rep['growth']] == [(31, 6616),
                                                  (24, 26), (39, 1052)] \
                and rep['tail']['payload_bytes'] == 2040 \
                and rep['tail']['payload_sha256'] == \
                'a0bccfe19ecc842afbe1a57ba05d26ef56ab71a4632791c36523cf67c5708e55'
            imgf, imgu = rk.Image(f), rk.Image(u)

            def segs(img, raw):
                out = {}
                for idx, m in enumerate(img.modules):
                    for kind in ('code', 'data'):
                        off, ln = img.module_region(idx, kind)
                        out[(idx, kind)] = (off, m[kind + '_exec'],
                                            raw[off:off + ln])
                return out

            sf, su = segs(imgf, f), segs(imgu, u)
            allowed = {}

            def allow(key, lo, hi):
                allowed.setdefault(key, []).append((lo, hi))

            for p in fwbuild.load_manifest(FULL_DIR / 'manifest.txt'):
                if p.get('kind') == 'module':
                    key = (p['module'], p['region'])
                    base = sf[key][1]
                    allow(key, p['address'] - base,
                          p['address'] - base + len(p['replace']))
            payloads = {(31, 'code'): FULL_DIR / 'out' / 'payload31.bin',
                        (24, 'code'): FULL_DIR / 'out' / 'tag24.bin',
                        (39, 'code'): FULL_DIR / 'out' / 'sort39.bin'}
            # The legacy reference used live sort scratch as code. Standard
            # restores the stock zeros there and uses its explicit extension.
            sort_base = sf[(39, 'code')][1]
            allow((39, 'code'), 0x0309F000-sort_base, 0x0309F000-sort_base+1052)
            for key, path in payloads.items():
                allow(key, len(su[key][2]),
                      len(su[key][2]) + path.stat().st_size)
            allow((0, 'code'), len(su[(0, 'code')][2]),
                  len(su[(0, 'code')][2]) + 0x2B9C)
            confined = True
            for key in sf:
                if key[0] == 72:
                    continue
                a, b = sf[key][2], su[key][2]
                if len(a) != len(b) and key not in payloads \
                        and key != (0, 'code'):
                    confined = False
                for i in range(min(len(a), len(b))):
                    if a[i] != b[i] and not any(
                            lo <= i < hi for lo, hi in
                            allowed.get(key, [])):
                        confined = False
                if key in payloads:
                    want = payloads[key].read_bytes()
                    if a[len(b):len(b) + len(want)] != want:
                        confined = False
            ext = sf[(0, 'code')][2][len(su[(0, 'code')][2]):]
            tail = (FULL_DIR / 'out' / 'tail-full.bin').read_bytes()
            ext_ok = len(ext) == 0x2B9C \
                and not any(ext[:0x23A0]) \
                and ext[0x23A0:0x23A0 + len(tail)] == tail \
                and not any(ext[0x23A0 + len(tail):])
            post_end = max(off + len(seg) for off, _, seg in su.values())
            runs = json.loads((FULL_DIR / 'out' /
                               'theme-full.json').read_text())['runs']
            run_ranges = [(r['offset'], r['offset'] +
                           len(bytes.fromhex(r['replace'])))
                          for r in runs]
            post_ok = True
            for i in range(post_end, len(u) - 4):
                j = i + (PAYLOAD_GROWTH if i < MIRROR_OFF else GROWTH_TOTAL)
                if u[i] != f[j]:
                    if not any(lo <= j < hi for lo, hi in run_ranges) \
                            and not (MIRROR_OFF + GROWTH_TOTAL <= j
                                     < MIRROR_OFF + GROWTH_TOTAL + 0x200):
                        post_ok = False
            default_ok = hashlib.sha256(u).hexdigest() == \
                '0dfd10e23749f9b6c65499266f1a7a2ec038160b089ba0fc2ca68dcf2b24c986'
            ok = pin_ok and rep_ok and confined and ext_ok \
                and post_ok and default_ok
            detail = (f'whole-image pin and length (+{GROWTH_TOTAL}): '
                      f'{pin_ok}; report pins (184 patches, both '
                      f'transplant hashes, growths, tail): {rep_ok}; '
                      f'segment diff confined to the union of parts: '
                      f'{confined}; module 0 tail span (zero workspace '
                      f'zone + payload): {ext_ok}; post-segment diff '
                      f'confined to theme runs + mirror + CRC: '
                      f'{post_ok}; default build == pinned unified '
                      f'hash: {default_ok}')
        check('full build: composed image pinned, diff confined '
              'to the union of its parts, default unchanged', ok, detail)

    # -- 14. DAC filter option (patches/dac_filter/) ---------------------
    # Each variant changes one immediate in the DAC init's filter
    # selection (movs r1, #0x02 at exec 0x03051814, file 0x2AEC0).
    # Compared against the framework-only build so the check needs no
    # transplant inputs.
    FILTER_FILE = 0x2AEC0
    filter_values = {'fast-linear-phase': 0x42, 'slow-low-latency': 0x82,
                     'slow-linear-phase': 0xC2, 'nos': 0x22}
    base_out = tmp / 'framework14.img'
    rb = run_build(['--input', str(STOCK), '--output', str(base_out),
                    '--no-transplants'])
    ok = rb.returncode == 0 and base_out.exists()
    detail = rb.stderr.strip()[:160]
    if ok:
        base_img = base_out.read_bytes()
        ok = base_img[FILTER_FILE:FILTER_FILE + 2] == bytes([0x02, 0x21])
        notes = [f'default immediate 0x02: {ok}']
        for name, value in filter_values.items():
            out = tmp / f'filter-{name}.img'
            r = run_build(['--input', str(STOCK), '--output', str(out),
                           '--no-transplants', '--dac-filter', name])
            if r.returncode != 0 or not out.exists():
                ok = False
                notes.append(f'{name}: build failed {r.stderr.strip()[:80]}')
                continue
            v = out.read_bytes()
            fp.validate(v)
            rep = json.loads(Path(str(out) + '.report.json').read_text())
            one = (diff_offsets(base_img, v) - set(range(n - 4, n))
                   == {FILTER_FILE}) and v[FILTER_FILE] == value
            named = rep.get('dac_filter') == name
            ok = ok and one and named
            notes.append(f'{name}: one byte = 0x{value:02X}: {one}, '
                         f'reported: {named}')
        rr = run_build(['--input', str(STOCK),
                        '--output', str(tmp / 'filter-recovery.img'),
                        '--recovery', '--dac-filter', 'nos'])
        refused = rr.returncode != 0 and not (tmp / 'filter-recovery.img').exists()
        ok = ok and refused
        notes.append(f'--recovery refused: {refused}')
        detail = '; '.join(notes)
    check('dac filter: each option changes exactly the filter immediate',
          ok, detail)

    # -- 15. Bluetooth auto-off option (patches/bt_auto_off/) ------------
    auto_sites = {'10min': (0x3F88C, bytes.fromhex('4ef66021')),
                  'never': (0x3F892, bytes.fromhex('fff76bbf'))}
    ok = base_out.exists()
    notes = []
    if ok:
        base_img = base_out.read_bytes()
        for name, (site, replace) in auto_sites.items():
            out = tmp / f'autooff-{name}.img'
            r = run_build(['--input', str(STOCK), '--output', str(out),
                           '--no-transplants', '--bt-auto-off', name])
            if r.returncode != 0 or not out.exists():
                ok = False
                notes.append(f'{name}: build failed {r.stderr.strip()[:80]}')
                continue
            v = out.read_bytes()
            fp.validate(v)
            rep = json.loads(Path(str(out) + '.report.json').read_text())
            confined = (diff_offsets(base_img, v) - set(range(n - 4, n))
                        <= set(range(site, site + 4)))
            placed = v[site:site + 4] == replace
            named = rep.get('bt_auto_off') == name
            ok = ok and confined and placed and named
            notes.append(f'{name}: confined {confined}, bytes {placed}, '
                         f'reported {named}')
        rr = run_build(['--input', str(STOCK),
                        '--output', str(tmp / 'autooff-recovery.img'),
                        '--recovery', '--bt-auto-off', 'never'])
        refused = rr.returncode != 0
        ok = ok and refused
        notes.append(f'--recovery refused: {refused}')
    check('bt auto-off: each option changes only the supervisor limit check',
          ok, '; '.join(notes))

    failed = [name for name, ok in results if ok is False]
    skipped = [name for name, ok in results if ok is None]
    passed = len(results) - len(failed) - len(skipped)
    print(f'\n{passed}/{len(results) - len(skipped)} checks passed'
          + (f' ({len(skipped)} skipped)' if skipped else ''))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
