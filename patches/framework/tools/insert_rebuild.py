#!/usr/bin/env python3
"""Insertion rebuild for RKnano firmware update packages (DP3_V137 layout).

Grows one module segment (code or data) by appending a payload at the end of
that segment's storage range, inserting bytes into the package file and
shifting every later byte. All dependent offsets are recomputed:

  * the grown module record's code_len / data_len grows by the payload size;
  * every module record code_load / data_load at or after the insertion
    address (storage space) grows by the payload size, including the grown
    module's other segment and zero-length records that alias moved content;
  * header section offset fields (0x70, 0x78, 0x80, 0xCC, 0xF8, 0x14C) at or
    after the insertion file position grow by the payload size (section
    lengths are unchanged; sysdefault's length word at 0x74 is a sector
    count, not a byte length, and is unchanged);
  * the firmware-length / duplicate-header offset at 0x1F4 grows by the
    payload size, and the 0x200-byte header copy at that offset is re-synced
    from the updated header;
  * the trailer CRC (Rockchip CRC-32, poly 0x04C10DB7, MSB-first, init 0,
    no final XOR) is regenerated over the whole rebuilt image.

The header BCD date bytes are never touched: stamping a build date is the
patch framework's job, not this tool's. Exec and BSS record fields never
change: appended bytes land at exec address (old exec + old len) of the
grown segment, and every pre-existing byte keeps its exec address.

A zero-length payload reproduces the input byte for byte (the header copy
re-sync and CRC regeneration are identities on a well-formed input).

Offline only. Never communicates with a device. Standard library only.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

TABLE_OFF = 0x200            # u32 load_base at 0x200, u32 count at 0x204
RECORD_BASE = 0x208          # first 32-byte module record
FIELDS = ('code_load', 'code_exec', 'code_len', 'data_load', 'data_exec',
          'data_len', 'bss_exec', 'bss_len')
# Header (offset, length) field pairs for the resource sections. Only the
# offset word is ever adjusted; lengths describe content that does not move
# relative to its section start.
SECTION_OFFSET_FIELDS = (0x70, 0x78, 0x80, 0xCC, 0xF8, 0x14C)
FW_LEN_OFF = 0x1F4           # offset of the duplicate 0x200-byte header
HEADER_LEN = 0x200


def _crc_table():
    table = []
    for n in range(256):
        v = n << 24
        for _ in range(8):
            v = ((v << 1) ^ (0x04C10DB7 if v & 0x80000000 else 0)) & 0xFFFFFFFF
        table.append(v)
    return table


_CRC_TABLE = _crc_table()


def rk_crc32(data):
    """MSB-first non-reflected Rockchip CRC-32, poly 0x04C10DB7, init 0."""
    crc = 0
    for b in data:
        crc = ((crc << 8) & 0xFFFFFFFF) ^ _CRC_TABLE[((crc >> 24) ^ b) & 0xFF]
    return crc


def parse(raw):
    """Return (load_base, records) with records as lists of 8 ints."""
    if len(raw) < 0x400 or raw[0x10:0x18] != b'Rockchip' \
            or raw[0x1F8:0x200] != b'RKnanoFW':
        raise ValueError('not an RKnanoFW image')
    base = struct.unpack_from('<I', raw, TABLE_OFF)[0]
    count = struct.unpack_from('<I', raw, TABLE_OFF + 4)[0]
    if count > 4096 or RECORD_BASE + count * 32 > len(raw):
        raise ValueError('invalid module table size')
    records = [list(struct.unpack_from('<8I', raw, RECORD_BASE + i * 32))
               for i in range(count)]
    return base, records


def file_offset(base, load_addr):
    return load_addr - base + TABLE_OFF


def insert_once(raw, module, kind, payload):
    """Return a rebuilt image with payload appended to one segment."""
    base, records = parse(raw)
    if not 0 <= module < len(records):
        raise ValueError(f'module {module} out of range')
    if kind not in ('code', 'data'):
        raise ValueError("segment must be 'code' or 'data'")
    load_i = FIELDS.index(kind + '_load')
    len_i = FIELDS.index(kind + '_len')
    rec = records[module]
    seg_load, seg_len = rec[load_i], rec[len_i]
    if seg_load == 0:
        raise ValueError(
            f'module {module} {kind} has no storage position (load = 0)')
    ins_addr = seg_load + seg_len            # storage-space insertion point
    pos = file_offset(base, ins_addr)        # file-space insertion point
    if not (RECORD_BASE + len(records) * 32 <= pos <= len(raw) - 4):
        raise ValueError(f'insertion position {pos:#x} outside payload area')
    n = len(payload)

    out = bytearray(raw[:pos])
    out += payload
    out += raw[pos:]

    if n:
        # Module records: grow the target length; shift every load field at
        # or after the insertion address, except the grown segment's own
        # start. Zero-length records aliasing moved content shift with it.
        for j, r in enumerate(records):
            for k2 in ('code', 'data'):
                lj = FIELDS.index(k2 + '_load')
                if j == module and k2 == kind:
                    continue
                if r[lj] >= ins_addr:
                    r[lj] += n
        records[module][len_i] += n
        for j, r in enumerate(records):
            struct.pack_into('<8I', out, RECORD_BASE + j * 32, *r)
        # Header section offsets at or after the insertion position shift.
        for off in SECTION_OFFSET_FIELDS:
            value = struct.unpack_from('<I', out, off)[0]
            if value >= pos:
                struct.pack_into('<I', out, off, value + n)
        # Duplicate-header offset (always after the payload area).
        fw_len = struct.unpack_from('<I', out, FW_LEN_OFF)[0]
        if fw_len >= pos:
            struct.pack_into('<I', out, FW_LEN_OFF, fw_len + n)

    # Re-sync the duplicate header from the (possibly updated) first 0x200
    # bytes, then regenerate the trailer CRC. Both are identities when the
    # input is well formed and n == 0.
    fw_len = struct.unpack_from('<I', out, FW_LEN_OFF)[0]
    if fw_len + HEADER_LEN > len(out) - 4:
        raise ValueError('duplicate header offset outside image')
    out[fw_len:fw_len + HEADER_LEN] = out[:HEADER_LEN]
    struct.pack_into('<I', out, len(out) - 4, rk_crc32(out[:-4]))
    return bytes(out)


def apply_insertions(raw, insertions):
    """Apply (module, kind, payload) insertions sequentially.

    Each insertion is computed against the layout produced by the previous
    one, so a list of insertions equals the same insertions applied one
    image at a time.
    """
    out = raw
    for module, kind, payload in insertions:
        out = insert_once(out, module, kind, payload)
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('image', type=Path)
    p.add_argument('--output', type=Path, required=True,
                   help='must not exist; never overwrite the source')
    p.add_argument('--module', type=int, required=True)
    p.add_argument('--segment', choices=('code', 'data'), default='code')
    p.add_argument('--payload', type=Path, required=True,
                   help='file whose bytes are appended to the segment')
    a = p.parse_args()
    raw = a.image.read_bytes()
    payload = a.payload.read_bytes()
    out = apply_insertions(raw, [(a.module, a.segment, payload)])
    if a.output.resolve() == a.image.resolve():
        p.error('refusing to overwrite the source image')
    with a.output.open('xb') as f:
        f.write(out)
    base, records = parse(out)
    rec = records[a.module]
    len_i = FIELDS.index(a.segment + '_len')
    print(json.dumps({
        'input_sha256': hashlib.sha256(raw).hexdigest(),
        'output_sha256': hashlib.sha256(out).hexdigest(),
        'input_length': len(raw),
        'output_length': len(out),
        'module': a.module,
        'segment': a.segment,
        'payload_bytes': len(payload),
        'new_segment_len': rec[len_i],
        'header_date_bytes': out[:4].hex(),
        'stored_crc32': hex(struct.unpack_from('<I', out, len(out) - 4)[0]),
        'computed_crc32': hex(rk_crc32(out[:-4])),
    }, indent=2))


if __name__ == '__main__':
    sys.exit(main())
