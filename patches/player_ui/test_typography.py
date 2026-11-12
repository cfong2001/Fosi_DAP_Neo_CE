"""Execute real patched Thumb code; mock only the LCD text draw."""
import struct
import sys
import unittest
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import *
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0,str(REPO/'tools'))
sys.path.insert(0,str(REPO/'patches/framework'))
from rknano_image import Image
from build import parse_patch

END=0x030EF000
class Typography(unittest.TestCase):
    def machine(self):
        raw=(REPO/'DP3_V137.img').read_bytes(); im=Image(raw)
        u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(0x03000000,0x100000)
        for mod in (0,27):
            off,n=im.module_region(mod,'code');u.mem_write(im.modules[mod]['code_exec'],raw[off:off+n])
        for p in HERE.glob('015*.patch'):
            row=parse_patch(p)
            if row['module'] in (0,27):u.mem_write(row['address'],row['replace'])
        u.reg_write(UC_ARM_REG_SP,0x030ED000);u.reg_write(UC_ARM_REG_LR,END|1)
        return u
    def test_time_draws_main_font(self):
        for args,expected,x in [((0,3,9,0),'03:09',7),((0,59,59,1),'59:59',191),((1,0,0,0),'99:00',7)]:
            u=self.machine(); seen=[]; fills=[]
            u.mem_write(0x030247E4,b'\x55')
            def hook(uc,addr,size,data):
                if addr==0x030632FA:
                    fills.append(tuple(uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)))
                    for reg in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3):uc.reg_write(reg,0xBAD)
                    uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
                elif addr==0x03062CEE:
                    rect=uc.reg_read(UC_ARM_REG_R0);text=uc.reg_read(UC_ARM_REG_R2)
                    seen.append((struct.unpack('<4H',uc.mem_read(rect,8)),uc.mem_read(text,12).decode('utf-16le').split('\0')[0]))
                    uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
            u.hook_add(UC_HOOK_CODE,hook)
            for reg,val in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),args):u.reg_write(reg,val)
            for reg in (UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7):u.reg_write(reg,0x12345678)
            u.emu_start(0x0307E72D,END,count=1000)
            right=72 if x==7 else 239
            self.assertEqual(seen,[((x,240,right,253),expected)])
            self.assertEqual(fills,[(x,240,right,253)])
            self.assertLess(seen[0][0][3],254) # Stock progress erase starts here.
            self.assertEqual(u.reg_read(UC_ARM_REG_SP),0x030ED000)
            for reg in (UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7):self.assertEqual(u.reg_read(reg),0x12345678)
            self.assertEqual(u.mem_read(0x030247E4,1),b'\0' if args[3] else b'\x55')
    def test_time_digits_fit_the_line(self):
        im=Image((REPO/'release/DP3_V137_CE.img').read_bytes())
        base=im.sections['font_b']['offset']
        for ch in '0123456789:':
            rec=im.raw[base+ord(ch)*33:base+(ord(ch)+1)*33]
            rows=[y for y in range(16) if int.from_bytes(rec[y*2:y*2+2],'big')]
            self.assertLess(max(rows),14)

    def test_marquee_stamp_wrap(self):
        for tick in (0,50,65535,65536,0xFFFFFFFF):
            u=self.machine();u.reg_write(UC_ARM_REG_R5,0x03023888);u.reg_write(UC_ARM_REG_R6,0x03023298)
            u.mem_write(0x03023298,struct.pack('<I',tick));u.emu_start(0x03053115,END,count=100)
            self.assertEqual(struct.unpack('<I',u.mem_read(0x030238B0,4))[0],tick)
            self.assertEqual(struct.unpack('<H',u.mem_read(0x030238B4,2))[0],50)
    def test_first_step_waits_and_later_steps_slow_down(self):
        u=self.machine();ctx=0x03023888;draws=[]
        # Ten-character title in a two-cell clip, matching the stock context.
        u.mem_write(ctx,struct.pack('<4h',0,10,32,25))
        u.mem_write(ctx+8,struct.pack('<HH',255,0))
        u.mem_write(ctx+0x16,struct.pack('<H',16))
        u.mem_write(ctx+0x24,struct.pack('<H',10))
        u.mem_write(ctx+0x2c,struct.pack('<H',150))
        def hook(uc,addr,size,data):
            if addr in (0x03056910,0x03062CEE,0x030632FA):
                if addr==0x03062CEE:draws.append(tick)
                uc.reg_write(UC_ARM_REG_R0,0)
                uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
        u.hook_add(UC_HOOK_CODE,hook)
        for tick in (0,30,50,149,150,180,199,200,249,250):
            u.mem_write(0x03023298,struct.pack('<I',tick))
            u.reg_write(UC_ARM_REG_R0,0x03024804)
            u.reg_write(UC_ARM_REG_LR,END|1)
            u.emu_start(0x03062F55,END,count=1000)
        self.assertEqual(draws,[150,200,250])

    def test_dwell_and_labels(self):
        u=self.machine();u.reg_write(UC_ARM_REG_R0,0x03023888)
        u.emu_start(0x030630BB,0x030630BE,count=2)
        self.assertEqual(struct.unpack('<H',u.mem_read(0x030238B4,2))[0],150)
        im=Image((REPO/'DP3_V137.img').read_bytes());raw=bytearray(im.raw)
        import json
        for r in json.loads((HERE/'labels.json').read_text())['runs']:
            off=r['offset'];v=bytes.fromhex(r['replace']);raw[off:off+len(v)]=v
        self.assertEqual([r['text'] for r in Image(bytes(raw)).lang(2) if r['id'] in (82,83)],['Artists','Albums'])

if __name__=='__main__':unittest.main()
