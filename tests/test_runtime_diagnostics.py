"""Runtime readouts must preserve calls, bound writes and protect inputs."""
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import runtime_diagnostics as diagnostic
from rknano_image import Image
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import *

BUFFER, NODE, STACK, STOP = 0x030D0000, 0x030D1000, 0x030E0000, 0x030EF000


class Diagnostics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / 'release/DP3_V137_CE.img').read_bytes()
        cls.result, cls.report = diagnostic.build(cls.source, (ROOT / 'DP3_V137.img').read_bytes())

    def machine(self):
        image = Image(self.result)
        uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        uc.mem_map(0x03000000, 0x100000)
        for module in (0, 31):
            for region in ('code', 'data'):
                offset, size = image.module_region(module, region)
                if size:
                    uc.mem_write(image.modules[module][region + '_exec'], self.result[offset:offset + size])
        uc.reg_write(UC_ARM_REG_SP, STACK)
        uc.reg_write(UC_ARM_REG_LR, STOP | 1)
        return uc

    def test_browser_capture_and_displaced_instruction(self):
        for kind in (1, 6):
            with self.subTest(kind=kind):
                uc = self.machine()
                uc.mem_write(NODE + 0x4E, bytes([kind]))
                uc.mem_write(NODE + 0x57, b'OPU')
                uc.mem_write(diagnostic.TRACE - 4, b'Z' * 12)
                uc.reg_write(UC_ARM_REG_R4, NODE)
                kept = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2)
                for i, reg in enumerate(kept):
                    uc.reg_write(reg, 0x100 + i)
                uc.emu_start(diagnostic.NODE_SITE | 1, diagnostic.NODE_SITE + 4, count=1000)
                self.assertEqual(bytes(uc.mem_read(diagnostic.TRACE - 4, 12)), b'ZZZZOPU' + bytes([kind]) + b'ZZZZ')
                self.assertEqual(uc.reg_read(UC_ARM_REG_R5), kind)
                self.assertEqual([uc.reg_read(r) for r in kept], [0x100, 0x101, 0x102])
                self.assertEqual(uc.reg_read(UC_ARM_REG_SP), STACK)
                self.assertEqual(uc.reg_read(UC_ARM_REG_LR), STOP | 1)

    def test_live_popup_and_guards(self):
        uc = self.machine()
        uc.mem_write(0x030056F2, b'OPU')
        uc.mem_write(diagnostic.TRACE, b'OPU\x06')
        uc.mem_write(0x0304B4D4, b'\xD4')
        uc.mem_write(0x03023151, b'\xFF')
        uc.mem_write(BUFFER - 8, b'Z' * 72)
        for reg, value in ((UC_ARM_REG_R0, 60), (UC_ARM_REG_R1, BUFFER), (UC_ARM_REG_R2, 32)):
            uc.reg_write(reg, value)
        for reg in (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6):
            uc.reg_write(reg, 0x12345678)
        uc.emu_start(diagnostic.RESOURCE | 1, STOP, count=1000)
        expected = 'CE:OPU OPU 06 D4 FF 4F \0'.encode('utf-16le')
        self.assertEqual(bytes(uc.mem_read(BUFFER, len(expected))), expected)
        self.assertEqual(bytes(uc.mem_read(BUFFER - 8, 8)), b'Z' * 8)
        self.assertEqual(bytes(uc.mem_read(BUFFER + len(expected), 64 - len(expected))), b'Z' * (64 - len(expected)))
        self.assertEqual(uc.reg_read(UC_ARM_REG_SP), STACK)
        self.assertTrue(all(uc.reg_read(r) == 0x12345678 for r in (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6)))

    def test_other_labels_and_short_buffers_use_original_lookup(self):
        for sid, size in ((61, 32), (60, 31)):
            uc = self.machine()
            uc.mem_write(BUFFER, b'Z' * 64)
            for reg, value in ((UC_ARM_REG_R0, sid), (UC_ARM_REG_R1, BUFFER), (UC_ARM_REG_R2, size)):
                uc.reg_write(reg, value)
            uc.emu_start(diagnostic.RESOURCE | 1, diagnostic.PROFILE, count=1000)
            self.assertEqual(uc.reg_read(UC_ARM_REG_PC), diagnostic.PROFILE)
            self.assertEqual([uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2)], [sid, BUFFER, size])
            self.assertEqual(bytes(uc.mem_read(BUFFER, 64)), b'Z' * 64)

    def test_prepatched_input_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'occupied or unexpected'):
            diagnostic.build(self.result, (ROOT / 'DP3_V137.img').read_bytes())

    def test_existing_outputs_are_refused_before_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'candidate.img'
            for target in (output, Path(str(output) + '.diagnostics.json')):
                target.write_bytes(b'keep')
                with patch.object(sys, 'argv', ['runtime_diagnostics.py', '--output', str(output)]), \
                        patch.object(diagnostic, 'build', side_effect=AssertionError('must not build')), \
                        self.assertRaises(SystemExit):
                    diagnostic.main()
                self.assertEqual(target.read_bytes(), b'keep')
                target.unlink()


if __name__ == '__main__':
    unittest.main()
