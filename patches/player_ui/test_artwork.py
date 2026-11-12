"""Execute generated artwork rows and no-art drawings with LCD leaves modeled."""
import random
import struct
import unittest
from test_typography import Typography, HERE, END
from build import parse_patch
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *

class Artwork(unittest.TestCase):
    def machine(self):
        u=Typography().machine()
        for pattern in ('016*.patch','017*.patch'):
            for p in HERE.glob(pattern):
                r=parse_patch(p);u.mem_write(r['address'],r['replace'])
        return u
    def put(self,u,addr,value):u.mem_write(addr,struct.pack('<I',value))
    @staticmethod
    def contrast(v):
        def gain(n,m):return max(0,min(m,(118*n-9*m+50)//100))
        return gain(v>>11,31)<<11|gain(v>>5&63,63)<<5|gain(v&31,31)
    def row(self,*,target=144,top=36,left=48,width=144,art_width=144,h=144,r=0,mode=16,height=1,codec=6):
        u=self.machine();buf=0x03026A20
        rng=random.Random(123);pixels=[rng.randrange(65536) for _ in range(width)]
        source=struct.pack('<%dH'%width,*pixels);u.mem_write(buf,source)
        for addr,v in ((0x0302598c,target),(0x03025998,top),(0x03025994,left),(0x03026cb8,h),(0x03026cb4,art_width),(0x0304b4d4,codec)):self.put(u,addr,v)
        u.mem_write(0x03004400,b'\xa2\x10');u.mem_write(0x030235b4,b'\xa2\x10');u.mem_write(0x030235b6,b'\xff\xff')
        blits=[];texts=[]
        def hook(uc,addr,n,data):
            if addr==0x0306333E:
                args=[uc.reg_read(reg) for reg in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
                mode_,ptr=struct.unpack('<II',uc.mem_read(uc.reg_read(UC_ARM_REG_SP),8))
                blits.append((args,mode_,ptr,list(struct.unpack('<%dH'%args[2],uc.mem_read(ptr,args[2]*2)))))
            elif addr==0x03062CEE:
                ptr=uc.reg_read(UC_ARM_REG_R2);texts.append(bytes(uc.mem_read(ptr,10)).decode('utf-16le').split('\0')[0])
            elif addr!=0x030632FA:return
            uc.reg_write(UC_ARM_REG_R0,0x1234)
            uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
        u.hook_add(UC_HOOK_CODE,hook)
        for reg,val in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),(left,top+r,width,height)):u.reg_write(reg,val)
        u.mem_write(0x030ED000,struct.pack('<II',mode,buf));u.reg_write(UC_ARM_REG_LR,END|1)
        for reg in (UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11):u.reg_write(reg,0x345678)
        u.emu_start(0x0306D13D,END,count=200000)
        self.assertEqual(u.reg_read(UC_ARM_REG_PC),END)
        self.assertEqual(u.reg_read(UC_ARM_REG_R0),0x1234)
        self.assertEqual(u.reg_read(UC_ARM_REG_SP),0x030ED000)
        for reg in (UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11):self.assertEqual(u.reg_read(reg),0x345678)
        self.assertEqual(bytes(u.mem_read(buf,len(source))),source)
        return blits,texts,pixels
    def test_center_contrast_rounding_and_aspect_padding(self):
        edge=(7,5,4,3,2,2,1,1,0,0)
        for target,top,left,w,h in ((144,36,48,144,144),(144,36,48,80,144),(190,8,25,190,114)):
            for row in (0,1,9,10,h//2,h-1):
                b,text,source=self.row(target=target,top=top,left=left,width=target,art_width=w,h=h,r=row)
                args,mode,ptr,out=b[0];self.assertEqual(args,[(240-target)//2,top+(target-h)//2+row,target,1]);self.assertEqual(mode,16)
                dy=min(row,h-1-row);skip=edge[dy] if dy<10 else 0;pad=(target-w)//2
                expected=[0x10a2 if x<pad+skip or x>=pad+w-skip else self.contrast(v) for x,v in enumerate(source)]
                self.assertEqual(out,expected)
                self.assertEqual(text,['FLAC'] if row==h-1 else [])
    def test_fallback_leaves_pixels_and_placement_unchanged(self):
        for kwargs in ({'left':23},{'target':30,'width':30,'art_width':30,'h':18},{'mode':0},{'height':2},{'h':0},{'art_width':145}):
            b,text,source=self.row(**kwargs);args,mode,ptr,out=b[0]
            self.assertEqual(out,source);self.assertEqual(ptr,0x03026A20);self.assertEqual(text,[])
    def test_duplicate_last_row_is_not_double_contrasted(self):
        a=self.row(r=143)[0][0][3];b=self.row(r=143)[0][0][3];self.assertEqual(a,b)
    def test_placeholder_is_bounded_and_draws_codec_badge(self):
        u=self.machine();self.put(u,0x0304b4d4,6);fills=[];text=[]
        def hook(uc,addr,n,data):
            if addr==0x030632FA:fills.append(tuple(uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)))
            elif addr==0x03062CEE:text.append(bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_R2),10)).decode('utf-16le').split('\0')[0])
            else:return
            uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
        u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x0307EBA9,END,count=100000)
        self.assertTrue(fills);self.assertTrue(all(48<=x0<=x1<=191 and 36<=y0<=y1<=179 for x0,y0,x1,y1 in fills));self.assertEqual(text,['FLAC'])

if __name__=='__main__':unittest.main()
