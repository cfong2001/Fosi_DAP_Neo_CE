#!/usr/bin/env python3
"""Export stock RKnano RGB565 image resources as PNG without extra dependencies.

Pixel byte order and channel arrangement follow the 16-bit little-endian
RGB565 interpretation. No transparency or compositor behavior is inferred.
"""
import argparse
from pathlib import Path
import struct
import zlib
from rknano_image import Image


def _chunk(typ, data):
    body = typ + data
    return (struct.pack('>I', len(data)) + body +
            struct.pack('>I', zlib.crc32(body) & 0xffffffff))


def to_png(data, width, height):
    if len(data) != 2 * width * height or width == 0 or height == 0:
        raise ValueError('invalid RGB565 pixel dimensions')
    scan = bytearray()
    for y in range(height):
        scan.append(0)  # PNG filter: None
        for (v,) in struct.iter_unpack('<H', data[y*width*2:(y+1)*width*2]):
            r = ((v >> 11) & 31) * 255 // 31
            g = ((v >> 5) & 63) * 255 // 63
            b = (v & 31) * 255 // 31
            scan.extend((r, g, b))
    return (b'\x89PNG\r\n\x1a\n' +
            _chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) +
            _chunk(b'IDAT', zlib.compress(scan, 9)) +
            _chunk(b'IEND', b''))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('image', type=Path)
    p.add_argument('output', type=Path, help='PNG filename with --id, or output directory with --all')
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--id', type=int, help='resource index 0..455')
    group.add_argument('--all', action='store_true')
    a = p.parse_args()
    im = Image(a.image.read_bytes())
    images = list(im.images())
    if a.id is not None and not 0 <= a.id < len(images):
        p.error('image resource ID out of range')
    selected = images if a.all else [images[a.id]]
    for entry in selected:
        off, size = entry['data_offset'], entry['size']
        if not entry['rgb565_bytes']:
            raise ValueError(f"unrecognized resource format {entry['id']}")
        png = to_png(im.raw[off:off+size], entry['width'], entry['height'])
        out = a.output / f"asset_{entry['id']:03d}.png" if a.all else a.output
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(png)
        print(out)


if __name__ == '__main__':
    main()
