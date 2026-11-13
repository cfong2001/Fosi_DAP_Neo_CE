"""The backup helper cannot select write/reset commands or hide bad reads."""
import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import backup_stock as b
class FakeUSB:
    def __init__(self,change=False,short=False):self.calls=[];self.change=change;self.short=short;self.reads=0
    def command(self,op,n,address=0,sectors=0):
        self.calls.append((op,n,address,sectors))
        if op==0x1A:return bytes(n)
        if op==0x1B:return bytes(16)
        self.reads+=1
        v=(address+(1 if self.change and self.reads>2 else 0))&255
        return bytes([v])*(n-1 if self.short else n)
class BackupStock(unittest.TestCase):
    def test_reads_twice_with_bounded_chunks(self):
        raw=FakeUSB()
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'backup';r=b.backup(b.ReadOnly(raw),19,out)
            self.assertTrue(r['two_independent_reads_match']);self.assertFalse(r['whole_device_capacity_verified'])
            self.assertEqual((out/'stock-read-1.bin').read_bytes(),(out/'stock-read-2.bin').read_bytes())
            self.assertEqual(r,json.loads((out/'BACKUP.json').read_text()))
            self.assertEqual([c[3] for c in raw.calls if c[0]==0x14],[16,3,16,3])
            self.assertTrue(all(c[0] in (0x14,0x1A,0x1B) for c in raw.calls))
    def test_non_read_opcodes_are_rejected_before_transport(self):
        raw=FakeUSB();usb=b.ReadOnly(raw)
        for op in (0x15,0xFF,0x0B,0x16):
            with self.assertRaises(ValueError):usb.command(op,512,0,1)
        self.assertFalse(raw.calls)
    def test_disagreement_is_recorded_and_not_qualified(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'backup'
            with self.assertRaisesRegex(ValueError,'disagree'):b.backup(b.ReadOnly(FakeUSB(change=True)),19,out)
            r=json.loads((out/'BACKUP.json').read_text());self.assertFalse(r['two_independent_reads_match']);self.assertEqual(r['status'],'INCOMPLETE')
    def test_short_read_fails_and_keeps_incomplete_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'backup'
            with self.assertRaisesRegex(ValueError,'short'):b.backup(b.ReadOnly(FakeUSB(short=True)),19,out)
            self.assertEqual(json.loads((out/'BACKUP.json').read_text())['status'],'INCOMPLETE')
    def test_existing_path_and_unknown_transport_are_preserved(self):
        raw=FakeUSB()
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);sentinel=out/'sentinel';sentinel.write_text('keep')
            with self.assertRaisesRegex(ValueError,'exists'):b.backup(b.ReadOnly(raw),19,out)
            self.assertFalse(raw.calls);self.assertEqual(sentinel.read_text(),'keep')
            with self.assertRaisesRegex(ValueError,'reviewed'):b.load_transport(sentinel)
    def test_bad_ranges_are_refused(self):
        raw=FakeUSB();usb=b.ReadOnly(raw)
        for args in ((0x14,512,-1,1),(0x14,1024,0xffffffff,2),(0x14,512,0,17),(0x14,1024,0,1),(0x1A,512,0,0)):
            with self.assertRaises(ValueError):usb.command(*args)
        self.assertFalse(raw.calls)
if __name__=='__main__':unittest.main()
