#!/usr/bin/env python3
"""Build the clock table v1 patch for DP3_V137 (Fosi DAP Neo), offline.

Reads the stock image read-only, decodes the 36-row clock table at
module 0 exec 0x03079824 (image offset 0x52ED0), cross-checks every row
against the values published in work/perf/clock_table.md section 5,
then emits:

  clock_v1.patch.json   patch specs consumable by repo/tools/firmware_patch.py
  clock_v1.patch        the same edits in nanitecfw grammar (MOD:ADDR:hex)
  DP3_V137_clock_v1.img combined patched copy (all specs applied, mirror+CRC
                        refixed exactly as firmware_patch.patch does)

Design (see clock_v1.md for the full rationale and flags):
  per in-scope codec row, one 24-byte spec over fields +4..+27:
    PLL (+4)      : stock bytes preserved (evidence doc section 7 caution)
    A fields (+8..+19): 0  -> solver floor (row 1) parks A outputs at 96 MHz
    B core (+20), B bus (+24): class target 144 / 240 / 288 MHz, written
      directly so the codec-row-alone solver output (clock_table.md
      section 6 model) equals the performance plan section 3.4 target.
  Word 0 of every row is never touched. No header date change: the
  stock+1 date discipline belongs to framework image assembly, and this
  artifact is verified byte-identical to stock outside the table.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

WS = Path.home() / 'workspace/fosi-dap-neo'
sys.path.insert(0, str(WS / 'repo/tools'))
import firmware_patch
from rknano_image import Image, rk_crc32

OUT = Path(__file__).resolve().parent
STOCK = WS / 'DP3_V137.img'
TABLE_EXEC = 0x03079824
TABLE_FILE_OFF = 0x52ED0
ROW = 0x1C
NROWS = 36
FIELDS = ('pll', 'a_core', 'a_stclk', 'a_pclk', 'b_core', 'b_bus')
MHZ = 1_000_000

# work/perf/clock_table.md section 5, MHz: (pll, a_core, a_stclk, a_pclk, b_core, b_bus)
DOC_TABLE_MHZ = {
    0: (0, 0, 0, 0, 0, 0), 1: (96, 96, 96, 96, 0, 0),
    2: (96, 96, 96, 48, 0, 0), 3: (200, 96, 96, 48, 0, 0),
    4: (48, 48, 48, 48, 48, 48), 5: (96, 48, 48, 48, 96, 96),
    6: (200, 100, 100, 75, 200, 200), 7: (200, 150, 150, 75, 300, 300),
    8: (200, 150, 150, 75, 300, 300), 9: (450, 200, 200, 75, 450, 450),
    10: (200, 150, 150, 75, 300, 300), 11: (200, 150, 150, 75, 300, 300),
    12: (200, 150, 150, 75, 300, 300), 13: (200, 150, 150, 75, 300, 300),
    14: (300, 80, 80, 80, 400, 400), 15: (300, 80, 80, 80, 400, 400),
    16: (300, 80, 80, 80, 400, 400), 17: (480, 200, 200, 80, 480, 480),
    18: (480, 200, 200, 80, 480, 480), 19: (480, 200, 200, 80, 480, 480),
    20: (480, 200, 200, 80, 480, 480), 21: (480, 200, 200, 80, 480, 480),
    22: (480, 200, 200, 80, 480, 480), 23: (36, 36, 36, 36, 36, 36),
    24: (72, 72, 72, 72, 72, 72), 25: (140, 140, 140, 140, 140, 140),
    26: (450, 200, 200, 75, 0, 0), 27: (24, 24, 24, 24, 0, 0),
    28: (300, 200, 200, 75, 400, 400), 29: (24, 24, 24, 24, 0, 0),
    30: (400, 200, 200, 75, 0, 0), 31: (400, 200, 200, 75, 400, 400),
    32: (24, 24, 24, 24, 0, 0), 33: (100, 100, 100, 75, 0, 0),
    34: (400, 120, 120, 75, 0, 0), 35: (480, 200, 200, 80, 480, 480),
}

# In-scope codec rows: row -> (format label, B-core target MHz).
# Targets are the performance plan section 3.4 solver outputs.
IN_SCOPE = {
    5: ('MP3 <=128k, <=44.1k', 144), 6: ('MP3 high', 144),
    7: ('WMA tier A', 144), 8: ('WMA tier B', 144),
    9: ('WAV', 144),
    10: ('AAC high', 144), 11: ('AAC low', 144),
    14: ('OGG tier 1', 240), 15: ('OGG tier 2', 240),
    16: ('OGG tier 3', 240), 17: ('OGG top tier', 240),
    18: ('FLAC', 288), 19: ('ALAC', 288), 20: ('APE', 288),
    21: ('DSD-DFF', 288), 22: ('DSD-DSF', 288),
}


def decode_rows(raw, off):
    rows = {}
    for r in range(NROWS):
        vals = struct.unpack_from('<7I', raw, off + r * ROW)
        rows[r] = {'id_word': vals[0], **dict(zip(FIELDS, vals[1:]))}
    return rows


def main():
    raw = STOCK.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    assert sha == firmware_patch.STOCK_SHA256, f'stock SHA mismatch: {sha}'

    im = Image(raw)
    m0 = im.modules[0]
    base, _ = im.module_region(0, 'code')
    off = base + (TABLE_EXEC - m0['code_exec'])
    assert off == TABLE_FILE_OFF, f'table offset {off:#x} != {TABLE_FILE_OFF:#x}'

    rows = decode_rows(raw, off)
    for r in range(NROWS):
        got = tuple(rows[r][f] // MHZ for f in FIELDS)
        assert rows[r]['id_word'] == r, f'row {r} id word {rows[r]["id_word"]}'
        assert got == DOC_TABLE_MHZ[r], f'row {r}: image {got} != doc {DOC_TABLE_MHZ[r]}'
    print(f'table decoded at file offset {off:#x}; all 36 rows match clock_table.md S5')

    specs = []
    proofs = []
    for r, (label, target_mhz) in sorted(IN_SCOPE.items()):
        row_off = off + r * ROW
        expect = bytes(raw[row_off + 4: row_off + ROW])
        stock = rows[r]
        replace = struct.pack('<6I',
                              stock['pll'],            # preserved, see header
                              0, 0, 0,                 # A fields -> solver floor
                              target_mhz * MHZ,        # B core
                              target_mhz * MHZ)        # B bus
        assert len(expect) == len(replace) == 24
        address = TABLE_EXEC + r * ROW + 4
        # Prove this spec is consumable by firmware_patch.py as-is:
        _, proof = firmware_patch.patch(raw, module=0, region='code',
                                        address=address, expect=expect,
                                        replace=replace)
        assert int(proof['edit']['file_offset'], 16) == row_off + 4
        proofs.append({'row': r, 'format': label,
                       'single_patch_output_sha256': proof['output_sha256']})
        specs.append({'module': 0, 'region': 'code',
                      'address': hex(address), 'address_int': address,
                      'row': r, 'format': label, 'target_b_core_mhz': target_mhz,
                      'expect_hex': expect.hex(), 'replace_hex': replace.hex()})
    print(f'{len(specs)} specs each verified consumable by firmware_patch.patch()')

    # Combined image: apply every edit, then the same mirror+CRC fixup
    # firmware_patch.patch performs (header untouched, so mirror is a no-op).
    out = bytearray(raw)
    for s in specs:
        o = off + s['row'] * ROW + 4
        assert bytes(out[o:o + 24]) == bytes.fromhex(s['expect_hex'])
        out[o:o + 24] = bytes.fromhex(s['replace_hex'])
    out[0xC94000:0xC94200] = out[:0x200]
    struct.pack_into('<I', out, len(out) - 4, rk_crc32(out[:-4]))
    out = bytes(out)
    firmware_patch.validate(out)
    img_path = OUT / 'DP3_V137_clock_v1.img'
    if img_path.exists():
        img_path.unlink()
    img_path.write_bytes(out)
    print(f'combined image written: {img_path.name} '
          f'sha256={hashlib.sha256(out).hexdigest()} (validate() passed)')

    doc = {'name': 'clock_v1', 'target': 'Fosi Audio DAP Neo DP3_V137',
           'stock_sha256': firmware_patch.STOCK_SHA256,
           'patched_sha256': hashlib.sha256(out).hexdigest(),
           'table': {'module': 0, 'region': 'code', 'exec': hex(TABLE_EXEC),
                     'file_offset': hex(TABLE_FILE_OFF),
                     'rows': NROWS, 'row_bytes': ROW},
           'policy': 'per spec: 24 bytes over row fields +4..+27; PLL word '
                     'carried over unchanged; A fields zeroed (solver floor '
                     'row 1 applies); B core/B bus set to the class target; '
                     'word 0 never edited; no header date change',
           'patches': specs,
           'single_patch_proofs': proofs}
    (OUT / 'clock_v1.patch.json').write_text(json.dumps(doc, indent=2) + '\n')
    lines = ['# clock_v1 in nanitecfw patch grammar (module:execaddr:hexbytes),',
             '# generated from clock_v1.patch.json; fields +4..+27 of each row.']
    for s in specs:
        lines.append(f"0:{s['address']}:{s['replace_hex']}  "
                     f"# row {s['row']:2d} {s['format']}: B core/bus -> "
                     f"{s['target_b_core_mhz']} MHz, A fields 0 (floor), PLL kept")
    (OUT / 'clock_v1.patch').write_text('\n'.join(lines) + '\n')
    print('wrote clock_v1.patch.json and clock_v1.patch')


if __name__ == '__main__':
    main()
