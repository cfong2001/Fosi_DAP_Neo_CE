"""An update is successful only after both the slot copy and file cleanup."""
import datetime
import unittest

from boot_recovery_support import ROOT, STOCK, STOP, machine, run, stub, word
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import (
    UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R6, UC_ARM_REG_SL,
)

from prepare_flash import apply_boot_patches, prepare, redated

INSTALLER = 0x0307E64C
SAVEINFO = 0x030232A0
CLEANUP_FAILURE = 0x12


class UpdateCleanup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock = STOCK.read_bytes()
        cls.patched, _ = apply_boot_patches(cls.stock, ('update-cleanup',))

    def install(self, raw, version, delete_result, copy_result=0, found=True):
        cpu = machine(raw, 8)
        cpu.mem_write(SAVEINFO + 0x2DB, version.to_bytes(2, 'little'))
        cpu.mem_write(0x03024340, word(0x7800))
        calls = []

        def read(cpu):
            size = cpu.reg_read(UC_ARM_REG_R1)
            cpu.mem_write(cpu.reg_read(UC_ARM_REG_R0),
                          raw[:512] if size == 512 else bytes(size))
            return size

        def copy(cpu):
            calls.append('copy')
            return copy_result

        def delete(cpu):
            calls.append('delete')
            return delete_result

        stub(cpu, {
            0x030611E0: lambda cpu: 0,
            0x03058CC6: lambda cpu: 1 if found else -1,
            0x03058FA8: read,
            0x030594A0: lambda cpu: 0,
            0x0307E53C: lambda cpu: 0,
            0x0307E880: copy,
            0x03058E8E: lambda cpu: 0,
            0x0305C86A: delete,
        })
        run(cpu, INSTALLER)
        self.assertEqual(cpu.reg_read(UC_ARM_REG_PC), STOP)
        return cpu.reg_read(UC_ARM_REG_R0), calls

    def test_generic_and_numbered_files_propagate_cleanup_failure(self):
        for version in (0xFFFF, 137):
            with self.subTest(version=version):
                self.assertEqual(self.install(self.stock, version, CLEANUP_FAILURE),
                                 (0, ['copy', 'delete']))
                failure, calls = self.install(self.patched, version, CLEANUP_FAILURE)
                self.assertEqual((failure, calls), (CLEANUP_FAILURE, ['copy', 'delete']))
                self.assertEqual(self.install(self.patched, version, 0),
                                 (0, ['copy', 'delete']))

    def test_failed_copy_or_missing_file_still_fails(self):
        self.assertEqual(self.install(self.patched, 137, 0, copy_result=-1),
                         (0xFFFFFFFF, ['copy', 'delete']))
        self.assertEqual(self.install(self.patched, 137, 0, found=False),
                         (0xFFFFFFFF, []))

    def test_cleanup_failure_bypasses_update_success_wait(self):
        for result, expected in ((0, 0x0307D434), (CLEANUP_FAILURE, 0x0307D3B4)):
            with self.subTest(result=result):
                cpu = machine(self.stock, 21)
                cpu.reg_write(UC_ARM_REG_R0, result)
                cpu.reg_write(UC_ARM_REG_R6, 1)
                cpu.reg_write(UC_ARM_REG_SL, SAVEINFO)

                def stop_at_disposition(cpu, address, size, data):
                    if address in (0x0307D434, 0x0307D3B4):
                        cpu.emu_stop()

                cpu.hook_add(UC_HOOK_CODE, stop_at_disposition)
                run(cpu, 0x0307D388)
                self.assertEqual(cpu.reg_read(UC_ARM_REG_PC), expected)

    def test_prepared_pair_keeps_recovery_stock(self):
        original = (ROOT / 'release' / 'DP3_V137_CE.img').read_bytes()
        date = datetime.date(2026, 11, 21)
        ce, recovery, report = prepare(original, self.stock, date, boot_patches=('update-cleanup',))
        baseline = redated(original, date)
        edit, = report['boot_patches']
        offset = int(edit['file_offset'], 16)
        self.assertEqual(ce[:offset], baseline[:offset])
        self.assertEqual(ce[offset:offset + 2].hex(), '2043')
        self.assertEqual(ce[offset + 2:-4], baseline[offset + 2:-4])
        self.assertEqual(recovery, redated(self.stock, date + datetime.timedelta(days=1)))
        self.assertTrue(report['modified_code_or_resources'])

    def test_unrecognized_or_already_patched_input_fails(self):
        with self.assertRaisesRegex(ValueError, 'unknown boot patch'):
            apply_boot_patches(self.stock, ('../update-cleanup',))
        with self.assertRaisesRegex(ValueError, 'precondition mismatch'):
            apply_boot_patches(self.patched, ('update-cleanup',))
