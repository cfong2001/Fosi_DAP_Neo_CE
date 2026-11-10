#!/usr/bin/env python3
"""DAC error-counter fix: apply + verify against a COPY of stock DP3_V137.img.
Offline only; the stock image is never modified. Each edit is first proven
individually through repo/tools/firmware_patch.py (stock SHA gate, module
boundary check, expect precondition, validate()). The combined image then
applies both edits and replicates the patcher's own finalization
(header-mirror sync + trailer CRC) before a final validate()."""
import hashlib, json, struct, sys
from pathlib import Path
WS = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WS / 'repo' / 'tools'))
import firmware_patch as fp
from rknano_image import Image, rk_crc32

OUT = Path(__file__).resolve().parent / 'DP3_V137_dacfix.img'
EDITS = [
    dict(name='branch', address=0x03060d14,
         expect=bytes.fromhex('02d0'), replace=bytes.fromhex('3bd0')),
    dict(name='cave', address=0x03060d8e,
         expect=bytes.fromhex('70477047'), replace=bytes.fromhex('6870c4e7')),
]
stock = (WS / 'DP3_V137.img').read_bytes()
assert hashlib.sha256(stock).hexdigest() == fp.STOCK_SHA256, 'stock SHA drift'

# 1) each edit individually through the official patcher, from pristine stock
for e in EDITS:
    out, proof = fp.patch(stock, module=0, region='code', address=e['address'],
                          expect=e['expect'], replace=e['replace'])
    assert proof['crc_valid'] and proof['header_mirror_valid']
    print(f"[ok] patcher applies edit '{e['name']}' alone: "
          f"file_offset={proof['edit']['file_offset']} crc_valid=True")

# 2) combined: edit 1 via patcher, edit 2 via the patcher's own mechanics
combined, _ = fp.patch(stock, module=0, region='code', address=EDITS[0]['address'],
                       expect=EDITS[0]['expect'], replace=EDITS[0]['replace'])
combined = bytearray(combined)
im = Image(bytes(combined))
base, _ = im.module_region(0, 'code')
e2 = EDITS[1]
off = base + (e2['address'] - im.modules[0]['code_exec'])
assert bytes(combined[off:off+4]) == e2['expect'], 'edit 2 expect mismatch in combined image'
combined[off:off+4] = e2['replace']
combined[0xc94000:0xc94200] = combined[:0x200]                      # mirror sync (as patch())
struct.pack_into('<I', combined, len(combined)-4, rk_crc32(bytes(combined[:-4])))
combined = bytes(combined)
fp.validate(combined)
print('[ok] combined image passes firmware_patch.validate() (mirror + CRC)')

# 3) byte diff vs stock must be exactly: edit1 (2B) + edit2 (4B) + CRC trailer (4B)
diffs = [i for i in range(len(stock)) if stock[i] != combined[i]]
regions = []
for i in diffs:
    if regions and i == regions[-1][1] + 1:
        regions[-1][1] = i
    else:
        regions.append([i, i])
print('[ok] differing regions (file offsets):',
      [(hex(a), hex(b), b-a+1) for a, b in regions])
assert len(diffs) <= 10 and all(not (0xc94000 <= i < 0xc94200) for i in diffs), \
    'unexpected diff (mirror region must be untouched: header unchanged)'

# 4) disassemble the patched module 0 code and assert the new semantics
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
code_off, _ = Image(combined).module_region(0, 'code')
code = combined[code_off:code_off + Image(combined).modules[0]['code_len']]
BASE = 0x03050000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
def dis(a, b):
    return {i.address: f'{i.mnemonic} {i.op_str}' for i in md.disasm(code[a-BASE:b-BASE], a)}
tail = dis(0x03060d12, 0x03060d22)
assert tail[0x03060d14] == 'beq #0x3060d8e', tail[0x03060d14]
cave = dis(0x03060d8e, 0x03060d9c)
assert cave[0x03060d8e] == 'strb r0, [r5, #1]', cave[0x03060d8e]
assert cave[0x03060d90] == 'b #0x3060d1c', cave[0x03060d90]
for a in (0x03060d92, 0x03060d94, 0x03060d96, 0x03060d98, 0x03060d9a):
    assert cave[a] == 'bx lr', (a, cave[a])   # remaining stubs untouched, incl. the referenced pair d98/d9a
print('[ok] disassembly: beq -> cave; cave = strb r0,[r5,#1] ; b 0x03060d1c; stubs d92..d9a intact')

OUT.write_bytes(combined)
print(f'[ok] wrote {OUT} sha256={hashlib.sha256(combined).hexdigest()}')
print('ALL CHECKS PASSED')
