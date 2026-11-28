#!/usr/bin/env python3
"""The glyph-width table answers exactly what the stock routine computes.

Runs 0x030627BE from the composed image under Unicorn, through the patched
entry and through the cave's resume of the stock prologue, with flash
reads served from the image. Checks:

- for every table code, the table entry equals the stock routine's result;
- for random codes, font classes, base cells and state bytes, the patched
  entry returns the stock result, and reads flash only when it must;
- the table agrees with the advance model in patches/antialias, which
  wrote the redrawn records and passed device acceptance.

Usage: test_glyph_width.py [IMAGE]   (default release/DP3_V137_CE.img)
"""
import random
import struct
import sys
import unittest
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_SP

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(HERE))
from rknano_image import Image  # noqa: E402
import build_glyph_width as G  # noqa: E402

IMAGE = Path(sys.argv.pop(1)) if len(sys.argv) > 1 and not sys.argv[1].startswith('-') \
    else ROOT / 'release/DP3_V137_CE.img'
RET = 0x030FFF00


class Width:
    def __init__(self, raw):
        image = Image(raw)
        m = image.modules[0]
        self.raw, self.reads = raw, 0
        self.uc = uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        uc.mem_map(0x03000000, 0x100000)
        for kind, at in (('code', m['code_exec']), ('data', m['data_exec'])):
            offset, size = image.module_region(0, kind)
            uc.mem_write(at, raw[offset:offset + size])
        uc.mem_write(RET, b'\xfe\xe7')
        offset, _ = image.module_region(0, 'code')
        cave = raw[offset + G.HOME - m['code_exec']:offset + G.HOME_END - m['code_exec']]
        self.slow = G.HOME + cave.index(bytes.fromhex('70b50546'))
        uc.hook_add(UC_HOOK_CODE, self._hook)

    def _hook(self, u, address, size, _):
        if address == RET:
            u.emu_stop()
        elif address in (G.COPY, 0x030642FE):
            self.reads += 1
            src, dst, n = (u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2))
            u.mem_write(dst, self.raw[src:src + n] if src + n <= len(self.raw) else bytes(n))
            u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR))

    def __call__(self, code, cls=0, base=None, state=0, slow=False):
        uc = self.uc
        uc.mem_write(G.CTX + 0x24, struct.pack('<H', cls))
        uc.mem_write(G.FONT_CELL, struct.pack('<I', G.font_base(self.raw) if base is None else base))
        uc.mem_write(G.STATE + 0x10, bytes([state]))
        uc.reg_write(UC_ARM_REG_R0, code)
        uc.reg_write(UC_ARM_REG_SP, 0x030F0000)
        uc.reg_write(UC_ARM_REG_LR, RET | 1)
        uc.emu_start((self.slow if slow else G.WIDTH) | 1, RET, count=20000)
        return uc.reg_read(UC_ARM_REG_R0)


class GlyphWidth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = IMAGE.read_bytes()
        cls.w = Width(cls.raw)

    def test_hook_is_installed(self):
        image = Image(self.raw)
        offset, _ = image.module_region(0, 'code')
        at = offset + G.WIDTH - image.modules[0]['code_exec']
        self.assertEqual(self.raw[at:at + 4], G.entry_patch())

    def test_table_matches_the_stock_routine(self):
        for cls in (0, 2):
            for code in range(G.CODES):
                self.w.reads = 0
                fast = self.w(code, cls=cls)
                self.assertEqual(self.w.reads, 0, (cls, hex(code)))
                self.assertEqual(fast, self.w(code, cls=cls, slow=True), (cls, hex(code)))

    def test_every_other_case_runs_the_stock_routine(self):
        rng = random.Random(5)
        base = G.font_base(self.raw)
        for _ in range(3000):
            case = dict(code=rng.choice((rng.randrange(G.CODES), rng.randrange(G.CODES, 0x3000))),
                        cls=rng.choice((0, 0, 1, 2)),
                        base=rng.choice((base, base, base + 1, base - 0x1000)),
                        state=rng.choice((0, 0, 1, 8, 10, 0x20)))
            self.assertEqual(self.w(**case), self.w(**case, slow=True), case)

    def test_table_agrees_with_the_font_generator(self):
        sys.path.insert(0, str(ROOT / 'patches/antialias'))
        import generate_font as GF
        records = G.font_base(self.raw) + 1
        for code in range(0x20, G.CODES):
            rec = self.raw[records + 33 * code:records + 33 * (code + 1)]
            self.assertEqual(self.w(code), GF.advance(rec, code), hex(code))


if __name__ == '__main__':
    unittest.main()
