"""Count embedded Opus pictures without publishing paths or tag values.

Host-side inventory only: this does not establish firmware JPEG compatibility.
Requires Mutagen. Files are opened read-only; output contains aggregate counts.
"""
import argparse
import base64
import binascii
import json
from pathlib import Path

from mutagen.flac import Picture
from mutagen.oggopus import OggOpus

MAX_ENCODED = 16 * 1024 * 1024


def picture_kind(value):
    if len(value) > MAX_ENCODED:
        return 'oversize'
    try:
        raw = base64.b64decode(value, validate=True)
        picture = Picture(raw)
    except (ValueError, TypeError, binascii.Error):
        return 'invalid'
    except Exception:
        # Mutagen's parser errors vary by version. No input text is emitted.
        return 'invalid'
    if not picture.data:
        return 'empty'
    if picture.data.startswith(b'\xff\xd8\xff'):
        return 'jpeg'
    if picture.data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    return 'other'


def inventory(root):
    result = dict(files=0, unreadable=0, without_picture=0, with_picture=0,
                  picture_blocks=0, jpeg=0, png=0, other=0, empty=0,
                  invalid=0, oversize=0)
    for path in root.rglob('*'):
        if not path.is_file() or path.suffix.lower() not in ('.opus', '.opu'):
            continue
        result['files'] += 1
        try:
            tags = OggOpus(path)
            values = tags.get('metadata_block_picture', [])
        except Exception:
            result['unreadable'] += 1
            continue
        result['with_picture' if values else 'without_picture'] += 1
        for value in values:
            result['picture_blocks'] += 1
            result[picture_kind(value)] += 1
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('media_dir', type=Path)
    args = parser.parse_args()
    if not args.media_dir.is_dir():
        parser.error('media directory is unavailable')
    print(json.dumps(inventory(args.media_dir), indent=2))
