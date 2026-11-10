"""Reject a partial player title repair before building any image."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('firmware_build', ROOT / 'patches/framework/build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class TitlePairTest(unittest.TestCase):
    def test_incomplete_or_modified_pair_refused(self):
        directory = ROOT / 'patches/theater/text'
        copy = build.parse_patch(directory / 'title-copy.patch')
        suffix = build.parse_patch(directory / 'title-suffix.patch')
        modified = dict(suffix, replace=b'\x00' * len(suffix['replace']))
        for patches in ([copy], [suffix], [copy, modified], [copy, copy]):
            with self.subTest(patches=len(patches)):
                with self.assertRaisesRegex(ValueError, 'must be used together'):
                    build.build_image(b'', patches, '20261023')
        # A complete pair reaches the ordinary stock-image gate.
        with self.assertRaisesRegex(ValueError, 'input SHA-256'):
            build.build_image(b'', [copy, suffix], '20261023')


if __name__ == '__main__':
    unittest.main()
