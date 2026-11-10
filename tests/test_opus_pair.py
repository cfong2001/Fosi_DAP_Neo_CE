"""The WMA classifier and decoder must never be changed independently."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('firmware_build', ROOT / 'patches/framework/build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class OpusPairTest(unittest.TestCase):
    def test_rejects_incomplete_pair_before_building(self):
        manifest = build.load_manifest(ROOT / 'patches/opus_swap/manifest.txt')
        renames = manifest[-5:]
        for patches, transplants in (([], ['opus72']), (renames, []),
                                     (renames[:-1], ['opus72'])):
            with self.subTest(patches=len(patches), transplants=transplants):
                with self.assertRaisesRegex(ValueError, 'must be used together'):
                    build.build_image(b'', patches, '20261023', transplants)


if __name__ == '__main__':
    unittest.main()
