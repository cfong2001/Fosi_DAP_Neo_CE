"""The generator must not overwrite an image or a pre-existing output."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'docs' / 'generate_builder_data.py'


class OpusOutputGuardTest(unittest.TestCase):
    def invoke(self, stock, output, only=True):
        args = [sys.executable, str(SCRIPT), '--stock', str(stock),
                '--ecpatch-dir', str(stock.parent), '--opus-data', str(output)]
        if only:
            args.append('--opus-data-only')
        return subprocess.run(args, capture_output=True, text=True)

    def test_same_input_path_rejected_even_if_input_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            stock = Path(tmp) / 'stock.img'
            result = self.invoke(stock, stock)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('resolves to the stock image', result.stderr)
            self.assertFalse(stock.exists())

    def test_existing_outputs_preserved_in_both_modes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / 'output.json'
            output.write_bytes(b'existing output')
            for only in (True, False):
                result = self.invoke(root / 'missing-stock.img', output, only)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('output already exists', result.stderr)
                self.assertEqual(output.read_bytes(), b'existing output')

    def test_symlink_and_hardlink_aliases_preserve_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stock = root / 'stock.img'
            stock.write_bytes(b'keep image')
            for alias, kind in ((root / 'symlink', 'sym'), (root / 'hardlink', 'hard')):
                if kind == 'sym':
                    alias.symlink_to(stock)
                else:
                    os.link(stock, alias)
                result = self.invoke(stock, alias)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(stock.read_bytes(), b'keep image')
                self.assertEqual(alias.read_bytes(), b'keep image')

    def test_dangling_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / 'output.json'
            output.symlink_to(root / 'missing-target')
            result = self.invoke(root / 'missing-stock', output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('output already exists', result.stderr)
            self.assertTrue(output.is_symlink())


if __name__ == '__main__':
    unittest.main()
