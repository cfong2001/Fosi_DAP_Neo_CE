"""Offline recovery preparation must preserve firmware and refuse unsafe inputs."""
import datetime as dt
import hashlib,json,os,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import prepare_flash as pf
from unicorn import Uc, UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1

class PrepareFlash(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock=(ROOT/'DP3_V137.img').read_bytes()
        cls.ce=(ROOT/'release/DP3_V137_CE.img').read_bytes()
    def test_pair_date_order_and_only_date_crc_changes(self):
        ce,recovery,r=pf.prepare(self.ce,self.stock,dt.date(2026,11,13))
        self.assertEqual(pf.image_date(ce),dt.date(2026,11,13))
        self.assertEqual(pf.image_date(recovery),dt.date(2026,11,14))
        for before,after in ((self.ce,ce),(self.stock,recovery)):
            mirror=struct.unpack_from('<I',before,0x1f4)[0]
            for lo,hi in ((4,mirror),(mirror+4,len(before)-4)):
                self.assertEqual(before[lo:hi],after[lo:hi])
            self.assertEqual(before[:2],after[:2]) # year unchanged
            self.assertEqual(len(before),len(after))
        self.assertFalse(r['modified_code_or_resources'])
        self.assertFalse(r['official_source_matches_device_verified'])
        self.assertFalse(r['full_device_backup_verified'])
        self.assertFalse(r['prepared_candidate']['hardware_boot_verified'])
        self.assertIn('DEVICE QUALIFICATION REQUIRED',r['status'])
    def test_refuses_unknown_candidate_and_official(self):
        for candidate,official,message in ((self.stock,self.stock,'candidate'),(self.ce,self.ce,'official')):
            with self.assertRaisesRegex(ValueError,message):pf.prepare(candidate,official)
    def test_refuses_non_newer_date(self):
        with self.assertRaisesRegex(ValueError,'newer'):pf.prepare(self.ce,self.stock,pf.image_date(self.ce))
    def test_crc_and_mirror_tampering(self):
        for position in (0x1000,0x1f8):
            bad=bytearray(self.ce);bad[position]^=1
            with self.assertRaises(ValueError):pf.audit(bytes(bad))
    def test_cli_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'existing';out.mkdir();(out/'sentinel').write_text('keep')
            r=subprocess.run([sys.executable,str(ROOT/'tools/prepare_flash.py'),'--official',str(ROOT/'DP3_V137.img'),'--output',str(out)],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0);self.assertEqual((out/'sentinel').read_text(),'keep')
            self.assertEqual([p.name for p in out.iterdir()],['sentinel'])
    @unittest.skipUnless(os.environ.get('FOSI_V155_IMAGE'),'optional verified user-supplied V155 input')
    def test_v155_matching_recovery(self):
        official=Path(os.environ['FOSI_V155_IMAGE']).read_bytes()
        ce,recovery,r=pf.prepare(self.ce,official,dt.date(2026,11,13))
        self.assertEqual(r['source_official']['version'],'V155')
        self.assertTrue(r['source_candidate_not_newer_than_official'])
        im=pf.Image(official);mirror=im.u32(0x1f4)
        self.assertEqual(recovery[4:mirror],official[4:mirror])
        self.assertEqual(recovery[mirror+4:-4],official[mirror+4:-4])


class PowerOnDebounce(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock = (ROOT / 'DP3_V137.img').read_bytes()
        cls.standard = (ROOT / 'release/DP3_V137_CE.img').read_bytes()
        cls.patched = pf.debounce_power_restart(cls.standard)

    def run_shutdown_poll(self, raw, high_periods):
        image = pf.Image(raw)
        offset, size = image.module_region(0, 'code')
        uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        uc.mem_map(0x03050000, 0x30000)
        uc.mem_write(image.modules[0]['code_exec'], raw[offset:offset + size])
        delay, read_button, reset = 0x03064944, 0x03061630, 0x030536A6
        for address in (delay, read_button):
            uc.mem_write(address, bytes.fromhex('7047'))  # bx lr

        now = 0
        restarted = None

        def observe(machine, address, size, data):
            nonlocal now, restarted
            if address == delay:
                self.assertEqual(machine.reg_read(UC_ARM_REG_R0), 10)
                now += 10_000
            elif address == read_button:
                if now >= 350_000:
                    machine.emu_stop()
                pressed = any(start <= now < end for start, end in high_periods)
                machine.reg_write(UC_ARM_REG_R0, int(pressed))
                now += 25  # A burst of stock reads fits inside a brief pulse.
            elif address == reset:
                self.assertEqual(machine.reg_read(UC_ARM_REG_R0), 0)
                self.assertEqual(machine.reg_read(UC_ARM_REG_R1), 0)
                restarted = now
                machine.emu_stop()

        uc.hook_add(UC_HOOK_CODE, observe)
        uc.emu_start(pf.POWER_RESTART_POLL | 1, 0x03067D1A, count=250_000)
        self.assertTrue(restarted is not None or now >= 350_000)
        return restarted

    def test_stock_restarts_on_a_brief_pulse_but_patch_rejects_it(self):
        pulse = [(20_000, 21_000)]
        self.assertIsNotNone(self.run_shutdown_poll(self.standard, pulse))
        self.assertIsNone(self.run_shutdown_poll(self.patched, pulse))

    def test_no_restart_without_release_and_fresh_press(self):
        for periods in ([], [(0, 400_000)], [(0, 50_000)]):
            with self.subTest(periods=periods):
                self.assertIsNone(self.run_shutdown_poll(self.patched, periods))

    def test_release_resets_the_count_and_a_deliberate_press_restarts(self):
        periods = [(0, 50_000), (70_000, 170_000), (180_000, 400_000)]
        self.assertEqual(self.run_shutdown_poll(self.patched, periods), 280_700)

    def test_candidate_changes_are_confined_to_power_poll_and_package_metadata(self):
        for name in ('DP3_V137_CE.img', 'DP3_V137_CE_minimal.img'):
            with self.subTest(image=name):
                original = (ROOT / 'release' / name).read_bytes()
                ce, recovery, report = pf.prepare(
                    original, self.stock, debounce_power_on=True)
                im = pf.Image(original)
                code_offset, _ = im.module_region(0, 'code')
                start = code_offset + pf.POWER_RESTART_POLL - im.modules[0]['code_exec']
                end = start + len(pf.POWER_RESTART_STOCK)
                mirror = im.u32(0x1f4)
                self.assertEqual(len(ce), len(original))
                self.assertEqual(ce[4:start], original[4:start])
                self.assertEqual(ce[start:end], pf.POWER_RESTART_DEBOUNCED)
                self.assertEqual(ce[end:mirror], original[end:mirror])
                self.assertEqual(ce[mirror+4:-4], original[mirror+4:-4])
                self.assertEqual(recovery, pf.redated(self.stock, pf.image_date(recovery)))
                self.assertTrue(report['modified_code_or_resources'])

    def test_patch_refuses_an_already_modified_poll(self):
        with self.assertRaisesRegex(ValueError, 'unexpected shutdown'):
            pf.debounce_power_restart(self.patched)


if __name__=='__main__':unittest.main()
