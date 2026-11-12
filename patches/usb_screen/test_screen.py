"""Execute the USB paint path and keep DAC/file metadata strictly separate."""
import struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'patches/framework')]
from rknano_image import Image
from build import parse_patch
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import *
END=0x030EF000
class USBScreen(unittest.TestCase):
    def test_usb_transport_card_and_data_screen(self):
        raw=(ROOT/'DP3_V137.img').read_bytes();im=Image(raw)
        for audio in (0,1):
            u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(0x03000000,0x100000)
            for mod in (0,9):
                for kind in ('code','data'):
                    off,n=im.module_region(mod,kind)
                    u.mem_write(im.modules[mod][kind+'_exec'],raw[off:off+n])
            for p in Path(__file__).parent.glob('*.patch'):
                r=parse_patch(p);u.mem_write(r['address'],r['replace'])
            u.mem_write(0x030232A0+0x2f2,bytes([audio]))
            labels=[];texts=[]
            def hook(uc,addr,n,_):
                if addr==0x03063242:
                    labels.append(struct.unpack('<I',uc.mem_read(uc.reg_read(UC_ARM_REG_SP)+4,4))[0])
                elif addr==0x03062CEE:
                    ptr=uc.reg_read(UC_ARM_REG_R2)
                    texts.append((struct.unpack('<4h',uc.mem_read(uc.reg_read(UC_ARM_REG_R0),8)),bytes(uc.mem_read(ptr,48)).decode('utf-16le').split('\0')[0]))
                elif addr not in (0x0306316E,0x0306314A,0x03067258,0x03063700,0x030632FA,0x0306723C):return
                uc.reg_write(UC_ARM_REG_R0,1 if addr==0x03067258 else 0)
                uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
            u.hook_add(UC_HOOK_CODE,hook);u.reg_write(UC_ARM_REG_SP,0x030ED000);u.reg_write(UC_ARM_REG_LR,END|1)
            u.emu_start(0x030806CD,END,count=10000)
            self.assertEqual(u.reg_read(UC_ARM_REG_PC),END)
            self.assertEqual(u.reg_read(UC_ARM_REG_SP),0x030ED000)
            self.assertNotIn(133,labels)
            texts=[(r,t) for r,t in texts if r[1]<200]
            self.assertEqual([t for r,t in texts],['USB Audio','16-bit / 48 kHz','PCM: 1536 kbps stereo'] if audio else [])
            self.assertTrue(all(132<=r[1]<=r[3]<200 for r,t in texts))
    def test_advertised_format_matches_card(self):
        # Pin the descriptor bytes, including channel count, subframe size,
        # bit depth and 48,000 Hz. 48000 * 2 * 16 / 1000 = 1536 kbps PCM.
        im=Image((ROOT/'DP3_V137.img').read_bytes())
        self.assertIn(bytes.fromhex('0b2402010202100180bb00'),im.raw[0x8113c:0x811cc])
if __name__=='__main__':unittest.main()
