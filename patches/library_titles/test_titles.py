"""Run the real scanner copy site and its hooked memcpy on UTF-16 records."""
import struct
import sys
import unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
sys.path.insert(0,str(REPO/'tools'))
sys.path.insert(0,str(REPO/'patches/framework'))
from rknano_image import Image
from build import parse_patch
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_MEM_WRITE
from unicorn.arm_const import *

class Titles(unittest.TestCase):
    def test_actual_scanner_copy_preserves_tags_and_bounds(self):
        raw=(REPO/'DP3_V137.img').read_bytes();im=Image(raw)
        for title,name,want in [('Tagged.flac','01_filename.flac','Tagged.flac'),('','01_filename.flac','01_filename.flac'),('T'*127,'fallback.flac','T'*127),('音楽 🎵','file.mp3','音楽 🎵'),('','','')]:
            u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(0x03000000,0x100000)
            for mod in (0,38):
                off,n=im.module_region(mod,'code');u.mem_write(im.modules[mod]['code_exec'],raw[off:off+n])
            for p in HERE.glob('018*.patch'):
                row=parse_patch(p);u.mem_write(row['address'],row['replace'])
            record=0x030D0000
            u.mem_write(record,b'Z'*0x600)
            for off,text in ((0,name),(0x100,title)):
                u.mem_write(record+off,(text+'\0').encode('utf-16le'))
            before=bytes(u.mem_read(record,0x600));writes=[]
            def hook(uc,access,a,n,v,data):
                if record<=a<record+0x600:writes.append((a,n))
            u.hook_add(UC_HOOK_MEM_WRITE,hook)
            u.reg_write(UC_ARM_REG_R4,record);u.reg_write(UC_ARM_REG_SP,0x030EF000)
            u.emu_start(0x0307EF53,0x0307EF60,count=10000)
            got=bytes(u.mem_read(record+0x100,256)).decode('utf-16le').split('\0')[0]
            self.assertEqual(got,want)
            self.assertTrue(all(record+0x100<=a and a+n<=record+0x200 for a,n in writes))
            if title:self.assertEqual(writes,[])
            self.assertEqual(bytes(u.mem_read(record,256)),before[:256])
            self.assertEqual(bytes(u.mem_read(record+0x200,0x400)),before[0x200:])
            self.assertEqual(u.reg_read(UC_ARM_REG_R4),record)
            self.assertEqual(u.reg_read(UC_ARM_REG_SP),0x030EF000)

if __name__=='__main__':unittest.main()
