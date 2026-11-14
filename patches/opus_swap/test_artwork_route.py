"""Execute native picture extraction, JPEG decode and theater drawing end to end."""
import argparse
import ast
import base64
import io
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / 'tools'), str(ROOT / 'patches/theater/build')]
from artwork_harness import extract
from build_artwork_route import edits
from rknano_image import Image
from repair_metrics import ogg
from PIL import Image as PillowImage


def port_derived(rows, light):
    count = sum(map(len, rows))
    avg = [sum(((pixel >> shift) & maximum) * 255 // maximum
               for row in rows for pixel in row) for shift, maximum in ((11, 31), (5, 63), (0, 31))]
    rgb = [(total + count // 2) // count for total in avg]
    mixed = [(value * 45 + 50) // 100 for value in rgb]
    return ((((mixed[0] * 31 + 127) // 255) << 11)
            | (((mixed[1] * 63 + 127) // 255) << 5)
            | ((mixed[2] * 31 + 127) // 255), rgb, mixed)


def fixture_jpeg():
    tree = ast.parse((ROOT / 'patches/theater/research/probe_jpeg.py').read_text())
    node = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == 'JPEG' for t in n.targets))
    return base64.b64decode(ast.literal_eval(node.args[0]))


def picture(jpeg):
    mime = b'image/jpeg'
    return (struct.pack('>II', 3, len(mime)) + mime
            + struct.pack('>6I', 0, 30, 18, 24, 0, len(jpeg)) + jpeg)


def stream(value, vorbis=False):
    comments = [] if value is None else [b'METADATA_BLOCK_PICTURE=' + value]
    tags = struct.pack('<II', 0, len(comments)) + b''.join(struct.pack('<I', len(c)) + c for c in comments)
    head = b'\x01vorbis' + bytes(23) if vorbis else b'OpusHead' + bytes([1, 2]) + bytes(9)
    return ogg([head, (b'\x03vorbis' if vorbis else b'OpusTags') + tags])


def check(raw):
    image = Image(raw)
    legacy = bytearray(raw)
    stock = (ROOT / 'DP3_V137.img').read_bytes()
    original = Image(stock)
    for mod, addr, code in edits():
        at = image.module_region(mod, 'code')[0] + addr - image.modules[mod]['code_exec']
        before = original.module_region(mod, 'code')[0] + addr - original.modules[mod]['code_exec']
        assert raw[at:at + len(code)] == code, 'candidate lacks artwork repair'
        legacy[at:at + len(code)] = stock[before:before + len(code)]
    jpeg = fixture_jpeg()
    block = picture(jpeg)
    media = stream(base64.b64encode(block))
    assert extract(bytes(legacy), media)[0] == 0, 'negative control did not reproduce missing Opus cover'
    copied = 0
    for payload in (block, picture(jpeg + bytes(80000))):
        result, kind, actual, calls = extract(raw, stream(base64.b64encode(payload)))
        assert result == len(payload) and actual == payload and kind == 0
        assert 0x030611E0 in calls, 'watchdog service absent'
        copied += len(actual)
    vorbis = stream(base64.b64encode(block), vorbis=True)
    assert extract(raw, vorbis)[:3] == extract(bytes(legacy), vorbis)[:3]
    assert extract(raw, vorbis)[2] == block
    malformed = [None, b'not base64!', b'', base64.b64encode(b'bad')]
    for value in malformed:
        assert extract(raw, stream(value))[0] == 0
    assert extract(raw, media[:80])[0] == 0
    decoded = 0
    for encoded in (jpeg,):
        rows, ground = extract(raw, stream(base64.b64encode(picture(encoded))), decode=True)
        assert len(rows) == 18
        assert ground == port_derived(rows[:6], False)[0] == 0x7000
        decoded += len(rows)
    # White and green covers distinguish an unchanged black ground from a
    # legitimately dark image without depending on external music fixtures.
    for color in ('white', 'green'):
        out = io.BytesIO()
        PillowImage.new('RGB', (30, 18), color).save(out, 'JPEG', quality=95)
        rows, ground = extract(raw, stream(base64.b64encode(picture(out.getvalue()))), decode=True)
        assert len(rows) == 18
        assert ground == port_derived(rows[:6], False)[0] and ground != 0
        decoded += len(rows)
    return dict(extraction_bytes_matched=copied, extraction_fixtures=2,
                malformed_or_missing_returns=5, native_decoded_rows=decoded,
                theater_reference_matches=3, vorbis_parity=True,
                legacy_opus_artwork_missing=True)


def corpus(raw, directory):
    from mutagen.oggopus import OggOpus
    result = dict(files=0, with_picture=0, without_picture=0, exact_picture_blocks=0)
    for path in directory.rglob('*'):
        if not path.is_file() or path.suffix.lower() not in ('.opus', '.opu'):
            continue
        result['files'] += 1
        values = OggOpus(path).get('metadata_block_picture', [])
        if not values:
            result['without_picture'] += 1
            continue
        result['with_picture'] += 1
        expected = base64.b64decode(values[0], validate=True)
        returned, kind, actual, _ = extract(raw, path.read_bytes())
        assert returned == len(expected) and kind == 0 and actual == expected, 'corpus picture mismatch'
        result['exact_picture_blocks'] += 1
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, default=ROOT / 'release/DP3_V137_CE.img')
    parser.add_argument('--media-dir', type=Path)
    args = parser.parse_args()
    raw = args.candidate.read_bytes()
    print(json.dumps(corpus(raw, args.media_dir) if args.media_dir else check(raw), indent=2))
