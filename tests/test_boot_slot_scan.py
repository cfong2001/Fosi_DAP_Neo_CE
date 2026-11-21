"""Check secondary scan limits and fallback by executing the V137 validator."""
import unittest

from boot_recovery_support import ROOT, STOCK, STOP, Image, machine, run, stub, word
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_R1, UC_ARM_REG_R3

from prepare_flash import apply_boot_patches

VALIDATOR = 0x0307E26C
FIRST_CANDIDATE = 0x6800
SECONDARY = 0x7800


class SlotScan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock = STOCK.read_bytes()
        cls.patched, _ = apply_boot_patches(cls.stock, ('slot-scan',))

    def validate(self, raw, *, primary=True, secondary=False, bad_mirror=False,
                 read_fails=False, false_header=False):
        cpu = machine(raw, 1)
        header = raw[:512]
        mirror = Image(raw).u32(0x1F4) >> 9
        newer = header[:2] + bytes.fromhex('2111') + header[4:]
        sectors = {0: header, mirror: header} if primary else {}
        if secondary:
            sectors.update({SECONDARY: newer, SECONDARY + mirror: newer})
        if bad_mirror:
            sectors.update({FIRST_CANDIDATE: newer, FIRST_CANDIDATE + mirror: b'\xFE' * 512})
        if false_header:
            zero_mirror = newer[:0x1F4] + word(0) + newer[0x1F8:]
            sectors[FIRST_CANDIDATE] = zero_mirror
        reads = []

        def read(cpu):
            sector = cpu.reg_read(UC_ARM_REG_R1)
            reads.append(sector)
            if len(reads) == 34:
                cpu.emu_stop()
            if read_fails and sector == FIRST_CANDIDATE:
                return -1  # Leave the previous primary mirror in the buffer.
            cpu.mem_write(cpu.reg_read(UC_ARM_REG_R3), sectors.get(sector, bytes(512)))
            return 0

        cpu.mem_write(0x03024340, word(SECONDARY))
        stub(cpu, {0x030678CA: read, 0x0306D8F0: lambda cpu: 0})
        run(cpu, VALIDATOR)
        done = cpu.reg_read(UC_ARM_REG_PC) == STOP
        selected = cpu.mem_read(0x03024354, 1)[0]
        base = int.from_bytes(cpu.mem_read(0x03024340, 4), 'little')
        return done, selected, base, reads

    def test_absent_secondary_has_exactly_twenty_probes(self):
        self.assertFalse(self.validate(self.stock)[0])
        for raw in (self.patched, apply_boot_patches(
                (ROOT / 'release' / 'DP3_V137_CE.img').read_bytes(), ('slot-scan',))[0]):
            done, selected, base, reads = self.validate(raw)
            self.assertTrue(done)
            self.assertEqual((selected, base), (0, FIRST_CANDIDATE))
            self.assertEqual(reads[2:], [FIRST_CANDIDATE + i * 0x800 for i in range(20)])

    def test_broken_first_candidate_does_not_hide_valid_later_slot(self):
        self.assertEqual(self.validate(self.stock, secondary=True, bad_mirror=True)[1], 0)
        for case in ('bad_mirror', 'read_fails', 'false_header'):
            with self.subTest(case=case):
                self.assertEqual(self.validate(self.patched, secondary=True, **{case: True})[:3],
                                 (True, 1, SECONDARY))

    def test_bad_mirror_preserves_original_fallback_sector(self):
        self.assertEqual(self.validate(self.patched, bad_mirror=True)[:3],
                         (True, 0, FIRST_CANDIDATE))

    def test_valid_secondary_still_works_without_primary(self):
        for raw in (self.stock, self.patched):
            self.assertEqual(self.validate(raw, primary=False, secondary=True)[:3],
                             (True, 1, SECONDARY))
            self.assertEqual(self.validate(raw, secondary=True)[:3], (True, 1, SECONDARY))
