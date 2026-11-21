"""Exercise the startup battery cutoff with real Thumb code and synthetic ADC."""
import unittest

from boot_recovery_support import STOCK, STOP, machine, run, stub, word
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_R0

from prepare_flash import apply_boot_patches

ADC = 0x400D0000
STARTUP_BATTERY = 0x0307D978
BELOW_CUTOFF, AT_CUTOFF, ABOVE_CUTOFF = 675, 676, 800


class StartupBattery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock = STOCK.read_bytes()
        cls.patched, _ = apply_boot_patches(cls.stock, ('startup-battery',))

    def measure(self, raw, samples, usb=False):
        cpu = machine(raw, 1)
        cpu.mem_map(ADC, 0x1000)
        readings = iter(samples)
        delays = []
        cuts = []

        def delay(cpu):
            interval = cpu.reg_read(UC_ARM_REG_R0)
            delays.append(interval)
            if interval == 1:
                cpu.mem_write(ADC, word(next(readings)))

        def cut_power(cpu):
            cuts.append(cpu.reg_read(UC_ARM_REG_R0))
            cpu.emu_stop()

        stub(cpu, {
            0x030535BC: lambda cpu: int(usb),
            0x03064944: delay,
            0x030613BE: cut_power,
        })
        run(cpu, STARTUP_BATTERY)
        self.assertEqual(delays, [1] * 18 + ([200] if cuts else []))
        self.assertEqual(cuts, [0] if cuts else [])
        self.assertEqual(cpu.reg_read(UC_ARM_REG_PC), 0x030613BE if cuts else STOP)
        battery = bytes(cpu.mem_read(0x03023904, 8))
        adc_control = bytes(cpu.mem_read(ADC + 8, 4))
        return bool(cuts), battery, adc_control

    def test_lone_final_dip_is_ignored(self):
        samples = [ABOVE_CUTOFF] * 17 + [BELOW_CUTOFF]
        self.assertTrue(self.measure(self.stock, samples)[0])
        self.assertFalse(self.measure(self.patched, samples)[0])

    def test_cutoff_and_usb_exception(self):
        for low_count, should_cut in ((0, False), (8, False), (9, True), (18, True)):
            with self.subTest(low_count=low_count):
                samples = [BELOW_CUTOFF] * low_count + [AT_CUTOFF] * (18 - low_count)
                self.assertEqual(self.measure(self.patched, samples)[0], should_cut)
                self.assertFalse(self.measure(self.patched, samples, usb=True)[0])

    def test_displayed_level_and_adc_restoration_follow_stock(self):
        for final_sample in (BELOW_CUTOFF, AT_CUTOFF, ABOVE_CUTOFF):
            with self.subTest(final_sample=final_sample):
                samples = [AT_CUTOFF] * 17 + [final_sample]
                self.assertEqual(self.measure(self.patched, samples, usb=True),
                                 self.measure(self.stock, samples, usb=True))
