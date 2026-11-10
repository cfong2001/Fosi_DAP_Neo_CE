"""Full-build CLI must reject destructive targets before generating anything."""
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INPUT = ROOT / 'DP3_V137.img'
SCRIPT = HERE / 'build_full.py'


class OutputGuardTest(unittest.TestCase):
    def test_existing_output_and_report_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / 'existing.img'
            report = root / 'existing.img.report.json'
            for existing in (output, report):
                existing.write_bytes(b'keep me')
                result = subprocess.run([sys.executable, str(SCRIPT),
                                         '--ecpatch-dir', tmp,
                                         '--output', str(output)],
                                        capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('already exists', result.stderr)
                self.assertEqual(existing.read_bytes(), b'keep me')
                existing.unlink()

    def test_stock_image_cannot_be_selected_as_output(self):
        before = hashlib.sha256(INPUT.read_bytes()).digest() if INPUT.exists() else None
        result = subprocess.run([sys.executable, str(SCRIPT),
                                 '--ecpatch-dir', str(HERE),
                                 '--output', str(INPUT)],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('resolves to the input image', result.stderr)
        if before is not None:
            self.assertEqual(hashlib.sha256(INPUT.read_bytes()).digest(), before)
        else:
            self.assertFalse(INPUT.exists())


if __name__ == '__main__':
    unittest.main()
