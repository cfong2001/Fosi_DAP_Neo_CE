"""Offline recovery preparation must preserve firmware and refuse unsafe inputs."""
import datetime as dt
import hashlib,json,os,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import prepare_flash as pf
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
if __name__=='__main__':unittest.main()
