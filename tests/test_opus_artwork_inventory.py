"""Aggregate artwork classification, with no media fixtures or identifiers."""
import base64
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mutagen.flac import Picture

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import audit_opus_artwork as audit


def block(data):
    picture = Picture()
    picture.type = 3
    picture.data = data
    return base64.b64encode(picture.write()).decode('ascii')


class ArtworkInventory(unittest.TestCase):
    def test_picture_classification(self):
        cases = [(b'\xff\xd8\xfftest', 'jpeg'),
                 (b'\x89PNG\r\n\x1a\ntest', 'png'),
                 (b'unknown', 'other'), (b'', 'empty')]
        for data, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(audit.picture_kind(block(data)), expected)
        self.assertEqual(audit.picture_kind('not base64!'), 'invalid')
        self.assertEqual(audit.picture_kind(base64.b64encode(b'bad').decode()), 'invalid')
        with patch.object(audit, 'MAX_ENCODED', 3):
            self.assertEqual(audit.picture_kind('AAAA'), 'oversize')

    def test_aggregate_counts_do_not_contain_input_values(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('a.OPU', 'b.opus', 'c.opus', 'ignored.mp3'):
                (root / name).write_bytes(b'unchanged')
            def tags(path):
                if path.stem == 'c':
                    raise ValueError('private error text')
                return {'metadata_block_picture': [block(b'\xff\xd8\xfftest')]} if path.stem == 'a' else {}
            with patch.object(audit, 'OggOpus', side_effect=tags):
                result = audit.inventory(root)
            self.assertEqual((result['files'], result['unreadable'], result['with_picture'],
                              result['without_picture'], result['jpeg']), (3, 1, 1, 1, 1))
            self.assertTrue(all(type(value) is int for value in result.values()))
            self.assertTrue(all(path.read_bytes() == b'unchanged' for path in root.iterdir()))


if __name__ == '__main__':
    unittest.main()
