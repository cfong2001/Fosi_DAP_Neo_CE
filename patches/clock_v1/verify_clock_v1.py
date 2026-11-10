#!/usr/bin/env python3
"""Independent verification of clock_v1 against DP3_V137 stock.

Does not reuse the build script's assembly: it loads clock_v1.patch.json,
applies the specs byte-wise to a fresh copy of the stock image with
expect-byte preconditions, refixes mirror+CRC the way firmware_patch.py
does, and checks:

  solver replica self-check : FREQSetFreq model (sum over active rows,
      then per-field out = max(row1 floor, min(sum, row35 cap))) must
      reproduce clock_table.md section 6 stock outputs for every codec row
  (a) every in-scope codec-alone state hits its target B-core/B-bus output
  (b) A-core/A-stclk/A-pclk solver outputs sit at the row-1 floor (96 MHz)
      for every in-scope codec-alone state (PLL reported, not asserted:
      v1 deliberately preserves stock PLL requests)
  (c) bytes outside the table are identical to stock, except the 4-byte
      trailer CRC (inherent to the package format) which must equal
      rk_crc32 of the patched body; header mirror region identical
  (d) word 0 (id/counter) of all 36 rows untouched
  (e) firmware_patch.validate() passes on the patched image, and the
      image rebuilt here is byte-identical to the build script's image

Writes verify_clock_v1_output.txt and exits non-zero on any failure.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

WS = Path.home() / 'workspace/fosi-dap-neo'
sys.path.insert(0, str(WS / 'repo/tools'))
import firmware_patch
from rknano_image import rk_crc32

HERE = Path(__file__).resolve().parent
STOCK = WS / 'DP3_V137.img'
TABLE_OFF = 0x52ED0
ROW = 0x1C
NROWS = 36
FIELDS = ('pll', 'a_core', 'a_stclk', 'a_pclk', 'b_core', 'b_bus')
MHZ = 1_000_000

# clock_table.md section 6: stock solver outputs, codec row alone (MHz).
DOC_SOLVER_STOCK_MHZ = {
    5: (96, 96, 96, 96, 96, 96), 6: (200, 100, 100, 96, 200, 200),
    7: (200, 150, 150, 96, 300, 300), 8: (200, 150, 150, 96, 300, 300),
    9: (450, 200, 200, 96, 450, 450), 10: (200, 150, 150, 96, 300, 300),
    11: (200, 150, 150, 96, 300, 300), 14: (300, 96, 96, 96, 400, 400),
    15: (300, 96, 96, 96, 400, 400), 16: (300, 96, 96, 96, 400, 400),
    17: (480, 200, 200, 96, 480, 480), 18: (480, 200, 200, 96, 480, 480),
    19: (480, 200, 200, 96, 480, 480), 20: (480, 200, 200, 96, 480, 480),
    21: (480, 200, 200, 96, 480, 480), 22: (480, 200, 200, 96, 480, 480),
}

failures = []
log = []


def say(s=''):
    log.append(s)
    print(s)


def check(ok, msg):
    say(('PASS  ' if ok else 'FAIL  ') + msg)
    if not ok:
        failures.append(msg)


def decode_rows(raw, off=TABLE_OFF):
    rows = {}
    for r in range(NROWS):
        vals = struct.unpack_from('<7I', raw, off + r * ROW)
        rows[r] = {'id_word': vals[0], **dict(zip(FIELDS, vals[1:]))}
    return rows


def solver(rows, active):
    """FREQSetFreq per clock_table.md S3/S6: sum fields over active rows,
    then out = max(row-1 floor, min(sum, row-35 cap)) per field."""
    floor = rows[1]
    cap = rows[35]
    out = {}
    for f in FIELDS:
        s = sum(rows[r][f] for r in active)
        out[f] = max(floor[f], min(s, cap[f]))
    return out


def fmt(vals_hz):
    return ' '.join(f'{vals_hz[f] // MHZ:>4}' for f in FIELDS)


def main():
    raw = STOCK.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == firmware_patch.STOCK_SHA256
    spec_doc = json.loads((HERE / 'clock_v1.patch.json').read_text())
    specs = spec_doc['patches']
    in_scope = {s['row']: s for s in specs}

    stock_rows = decode_rows(raw)
    say('== solver replica self-check against clock_table.md S6 (stock) ==')
    ok = True
    for r, doc in DOC_SOLVER_STOCK_MHZ.items():
        got = solver(stock_rows, [r])
        if tuple(got[f] // MHZ for f in FIELDS) != doc:
            ok = False
            say(f'  row {r}: replica {tuple(got[f] // MHZ for f in FIELDS)} != doc {doc}')
    check(ok, 'solver replica reproduces all 16 published stock outputs')

    # Apply specs to a fresh copy, byte-wise, with preconditions.
    out = bytearray(raw)
    for s in specs:
        o = TABLE_OFF + s['row'] * ROW + 4
        expect = bytes.fromhex(s['expect_hex'])
        replace = bytes.fromhex(s['replace_hex'])
        assert bytes(out[o:o + 24]) == expect, f"row {s['row']} expect mismatch"
        out[o:o + 24] = replace
    out[0xC94000:0xC94200] = out[:0x200]
    struct.pack_into('<I', out, len(out) - 4, rk_crc32(out[:-4]))
    out = bytes(out)
    new_rows = decode_rows(out)

    say()
    say('== solver outputs, codec row alone (MHz) ==')
    say(f"{'row':>3} {'format':<22} {'':9} {'pll':>4} {'Acor':>4} {'Astk':>4} "
        f"{'Apck':>4} {'Bcor':>4} {'Bbus':>4}")
    for r in sorted(DOC_SOLVER_STOCK_MHZ):
        s = in_scope[r]
        st = solver(stock_rows, [r])
        nw = solver(new_rows, [r])
        say(f"{r:>3} {s['format']:<22} {'stock':9} {fmt(st)}")
        say(f"{'':>3} {'':<22} {'v1':9} {fmt(nw)}")

    say()
    say('== assertions ==')
    # (a) B-core/B-bus targets
    bad = [r for r, s in in_scope.items()
           if solver(new_rows, [r])['b_core'] != s['target_b_core_mhz'] * MHZ
           or solver(new_rows, [r])['b_bus'] != s['target_b_core_mhz'] * MHZ]
    check(not bad, f'(a) all {len(in_scope)} in-scope codec states hit target '
                   f'B core/B bus (violations: {bad})')
    # (b) A fields at floor
    floor = stock_rows[1]
    bad = []
    for r in in_scope:
        o = solver(new_rows, [r])
        for f in ('a_core', 'a_stclk', 'a_pclk'):
            if o[f] != floor[f]:
                bad.append((r, f, o[f] // MHZ))
    check(not bad, f'(b) A core/stclk/pclk at 96 MHz floor for all codec-alone '
                   f'states (violations: {bad})')
    # (c) byte identity outside the table
    t0, t1 = TABLE_OFF, TABLE_OFF + NROWS * ROW
    diffs = [i for i in range(len(raw)) if raw[i] != out[i]]
    outside = [i for i in diffs if not (t0 <= i < t1)]
    crc_bytes = set(range(len(raw) - 4, len(raw)))
    check(set(outside) <= crc_bytes,
          f'(c) no byte outside the table differs except trailer CRC '
          f'(outside diffs: {[hex(i) for i in outside if i not in crc_bytes]})')
    check(struct.unpack_from('<I', out, len(out) - 4)[0] == rk_crc32(out[:-4]),
          '(c) trailer CRC equals rk_crc32 of patched body')
    check(out[0xC94000:0xC94200] == raw[0xC94000:0xC94200],
          '(c) header mirror region byte-identical to stock')
    say(f'      ({len(diffs)} bytes differ in total, '
        f'{sum(1 for i in diffs if t0 <= i < t1)} inside the table)')
    # (d) word 0 untouched
    bad = [r for r in range(NROWS)
           if struct.unpack_from('<I', out, TABLE_OFF + r * ROW)[0]
           != struct.unpack_from('<I', raw, TABLE_OFF + r * ROW)[0]]
    check(not bad, f'(d) word 0 of all 36 rows untouched (violations: {bad})')
    # untouched rows fully identical
    bad = [r for r in range(NROWS) if r not in in_scope
           and out[TABLE_OFF + r * ROW: TABLE_OFF + (r + 1) * ROW]
           != raw[TABLE_OFF + r * ROW: TABLE_OFF + (r + 1) * ROW]]
    check(not bad, f'(d) all {NROWS - len(in_scope)} out-of-scope rows '
                   f'byte-identical (violations: {bad})')
    # (e) validate + build reproducibility
    try:
        firmware_patch.validate(out)
        check(True, '(e) firmware_patch.validate() passes on patched image')
    except Exception as e:  # noqa: BLE001
        check(False, f'(e) firmware_patch.validate() raised: {e}')
    built = (HERE / 'DP3_V137_clock_v1.img').read_bytes()
    check(built == out, '(e) verify-rebuilt image byte-identical to build output')
    say(f'      patched sha256 = {hashlib.sha256(out).hexdigest()}')

    # Sensitivity note (not an assertion): row 4 held concurrently, as
    # nanitecfw reported for the Nano music service (+48 MHz all fields).
    say()
    say('== sensitivity: solver B core if row 4 (audio init, +48) is also held ==')
    for r in sorted(in_scope):
        s = in_scope[r]
        b = solver(new_rows, [4, r])['b_core'] // MHZ
        say(f"  row {r:>2} {s['format']:<22} B core {b} MHz "
            f"(target {s['target_b_core_mhz']} codec-alone)")

    say()
    say('RESULT: ' + ('ALL CHECKS PASSED' if not failures
                      else f'{len(failures)} FAILURE(S)'))
    (HERE / 'verify_clock_v1_output.txt').write_text('\n'.join(log) + '\n')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
