#!/usr/bin/env python3
"""Read-only checks of V137 package geometry and cited Thumb byte ranges."""
import hashlib
import json
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tools'))
from rknano_image import Image
from fosi_paths import stock_image_path

SHA = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
PINS = {
    (0, 0x0305e038): '8db1012d0bd0022d05d0032d22d10220fff793ff04440120fff78fff04440020fff78bff04440120fff788feb0f5005f8cbfa0f500500020e11988420ad343463a4604f500510120',
    (0, 0x0305ec6e): 'bdf802021849c002206040080860',
    (1, 0x0307e380): '4349daf800000a68b2eb400f04d24ff4005202eb40000860',
    (1, 0x0307e2ec): '7d98012500f582100bea50244ff00008bcb180ab012221464ff44030e9f7dffa08220df5806107f5fc70d6f7d2fd68b1012d0cbf04f50064a4f5006408f10108e6e7b8f1140f1ad2e4b918e0',
    (1, 0x0307e338): 'd7f8f4016b4604eb502101224ff44030e9f7bffa4ff40072694680a8d6f7b3fd002808bf0126e6d0214640a0eff7c4fae1e745a0eff7c0fa55ea060017d0002e18bfcaf8004016d0',
    (8, 0x0307e718): '7d985a4600f582166ff313060021daf7bbfe5a464ff400718098daf739fc4ff4007268468099d6f7befb002854d1',
    (8, 0x0307e764): '3868b6eb402f88bf750a5a4600214ff40050daf7',
    (8, 0x0307e5b0): '70b5dd480178dd480129026807bf0020114610460021520200f05af9',
}


def main():
    raw = stock_image_path(REPO).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA:
        raise ValueError('stock image SHA-256 mismatch')
    im = Image(raw)
    for (module, address), expected_hex in PINS.items():
        off, length = im.module_region(module, 'code')
        start = address - im.modules[module]['code_exec']
        expected = bytes.fromhex(expected_hex)
        if start < 0 or start + len(expected) > length or raw[off + start:off + start + len(expected)] != expected:
            raise ValueError(f'module {module} code at {address:#x} differs from the pin')
    mirror = struct.unpack_from('<I', raw, 0x1f4)[0]
    if raw[:512] != raw[mirror:mirror + 512]:
        raise ValueError('header mirror mismatch')
    boundary = (mirror + 0x104000) & ~0xfffff
    image_end = im.sections['images']['offset'] + im.sections['images']['length']
    if any(raw[image_end:mirror]) or any(raw[mirror + 512:boundary]):
        raise ValueError('expected package padding is not zero')
    max_same_stride_mirror = (boundary + 0x100000 - 1 - 0x104000) & ~511
    print(json.dumps({'sha256': SHA, 'file_bytes': len(raw),
                      'mirror_offset': hex(mirror),
                      'images_end': hex(image_end),
                      'zero_bytes_before_mirror': mirror - image_end,
                      'zero_bytes_after_mirror_before_transfer_end': boundary - mirror - 512,
                      'stock_transfer_bytes': boundary,
                      'maximum_aligned_mirror_at_same_transfer_length': hex(max_same_stride_mirror),
                      'conditional_max_mirror_growth_bytes': max_same_stride_mirror - mirror,
                      'outer_crc_bytes_beyond_transfer': len(raw) - boundary,
                      'instruction_pins_checked': len(PINS)}, indent=2))


if __name__ == '__main__':
    main()
