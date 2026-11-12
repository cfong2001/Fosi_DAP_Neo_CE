"""Compare executed stock and CE routines, framebuffer bytes, context and ABI."""
import random,struct,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'patches/framework')]
from rknano_image import Image
from build import parse_patch
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
END=0x030EF000;SP=0x030ED000;SOURCE=0x030A0000
CTX=0x030238B8;TEXT=0x0302385C
BUFFERS=((0x030065A8,240*240*2),(0x0306F224,240*80*2))
REGS=(UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)
KEPT=(UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11)
ENTRIES={'fill':0x030632FA,'fg':0x030632B4,'bitmap':0x0306333E,'keyed':0x0306373C,'flash':0x03063444,'clear':0x03063F92}
class Rows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.im=Image((ROOT/'DP3_V137.img').read_bytes())
        r=random.Random(777);cls.background=r.randbytes(240*320*2)
        cls.pixels=[r.choice((0,0xF800,r.randrange(65536))) for _ in range(240*320)]
        cls.source=struct.pack('<%dH'%len(cls.pixels),*cls.pixels)
        cls.flash=struct.pack('>%dH'%len(cls.pixels),*cls.pixels)
    def run_case(self,kind,args,fast,*,rotation=0,mode=0,count=False,bank=0):
        u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(0x03000000,0x100000)
        off,n=self.im.module_region(0,'code');u.mem_write(0x03050000,self.im.raw[off:off+n])
        if fast:
            for p in HERE.glob('*.patch'):
                a=parse_patch(p);u.mem_write(a['address'],a['replace'])
        pos=0
        for addr,n in BUFFERS:u.mem_write(addr,self.background[pos:pos+n]);pos+=n
        u.mem_write(SOURCE,self.source)
        context=bytearray(40);struct.pack_into('<HHHH',context,0,bank,0,319,0);struct.pack_into('<I',context,20,rotation)
        u.mem_write(CTX,bytes(context));u.mem_write(TEXT,struct.pack('<6H',0xFFFF,0x10A2,mode,0,240,320))
        u.mem_write(0x030235B6,b'\xff\xff');u.mem_write(0x0302328C,struct.pack('<I',0x10000000))
        trace={'pixel':0,'instructions':0,'flash':[],'fallback':False,'writes':[]}
        def hook(uc,addr,size,_):
            if count:trace['instructions']+=1
            if addr==0x03063E60:trace['pixel']+=1
            if addr==ENTRIES[kind]+(8 if kind=='flash' else 4):trace['fallback']=True
            if addr==0x03053F5E:
                source,dest,n=(uc.reg_read(r) for r in REGS[:3]);start=source-0x10000000-0x800
                self.assertGreaterEqual(start,0);self.assertLessEqual(start+n,len(self.flash))
                trace['flash'].append((dest,n));uc.mem_write(dest,self.flash[start:start+n]);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
        u.hook_add(UC_HOOK_CODE,hook)
        def write_hook(uc,access,addr,size,value,_):
            if not fast or trace['fallback']:return
            allowed=BUFFERS+((CTX,40),(SP-0x1000,0x1000))
            self.assertTrue(any(a<=addr and addr+size<=a+n for a,n in allowed),(hex(addr),size))
        u.hook_add(UC_HOOK_MEM_WRITE,write_hook)
        for reg,v in zip(REGS,args):u.reg_write(reg,v&0xffffffff)
        if len(args)>4:u.mem_write(SP,struct.pack('<'+'I'*(len(args)-4),*args[4:]))
        for reg in KEPT:u.reg_write(reg,0x12345678)
        u.reg_write(UC_ARM_REG_SP,SP);u.reg_write(UC_ARM_REG_LR,END|1)
        u.emu_start(ENTRIES[kind]|1,END,count=10000000)
        self.assertEqual(u.reg_read(UC_ARM_REG_PC),END)
        self.assertEqual(u.reg_read(UC_ARM_REG_SP),SP)
        self.assertEqual([u.reg_read(r) for r in KEPT],[0x12345678]*len(KEPT))
        self.assertEqual(bytes(u.mem_read(SOURCE,len(self.source))),self.source)
        return b''.join(bytes(u.mem_read(a,n)) for a,n in BUFFERS),bytes(u.mem_read(CTX,40)),trace
    def compare(self,kind,args,**kw):
        stock=self.run_case(kind,args,False,**kw);fast=self.run_case(kind,args,True,**kw)
        self.assertEqual(fast[:2],stock[:2],(kind,args,kw))
        return stock[2],fast[2]
    def test_fills_and_clear_across_split(self):
        for kind in ('fill','fg'):
            for box in ((0,0,239,319),(8,230,18,250),(239,319,239,319),(0,0,0,0)):
                s,f=self.compare(kind,box+((0xABCD,) if kind=='fill' else ()))
                self.assertEqual(f['pixel'],0);self.assertFalse(f['fallback'])
        s,f=self.compare('clear',(0xABCD,));self.assertEqual(f['pixel'],0)
    def test_opaque_images(self):
        for x,y,w,h in ((0,0,240,320),(4,235,19,12),(239,319,1,1),(50,12,80,70)):
            s,f=self.compare('bitmap',(x,y,w,h,16,SOURCE));self.assertEqual(f['pixel'],0)
    def test_keyed_images_and_keys(self):
        for key in (0,1,2,255):
            for box in ((2,235,17,245),(80,12,96,20),(0,0,0,0)):
                s,f=self.compare('keyed',box+(16,SOURCE,key));self.assertEqual(f['pixel'],0)
    def test_monochrome_glyphs_and_modes(self):
        for mode in range(4):
            for w in (1,6,12,16):
                s,f=self.compare('bitmap',(7,235,w,12,1,SOURCE),mode=mode);self.assertEqual(f['pixel'],0)
    def test_stock_fallback_for_rotation_clipping_and_modes(self):
        cases=(('fill',(4,2,15,8,0x1234)),('fg',(4,2,15,8)),('bitmap',(4,2,12,7,16,SOURCE)),('keyed',(4,2,15,8,16,SOURCE,0)),('flash',(0,0,240,320,0x800)),('clear',(0x1234,)))
        for rotation in (1,2,3):
            for kind,args in cases:
                s,f=self.compare(kind,args,rotation=rotation);self.assertTrue(f['fallback'])
        for kind,args in (('fill',(238,318,241,321,0x1234)),('bitmap',(238,318,4,4,16,SOURCE)),('bitmap',(7,4,20,2,1,SOURCE)),('keyed',(238,318,241,321,16,SOURCE,0)),('bitmap',(0,0,4,4,8,SOURCE))):
            s,f=self.compare(kind,args);self.assertTrue(f['fallback'])
    def test_full_screen_flash_reads_directly_into_both_banks(self):
        s,f=self.compare('flash',(0,0,240,320,0x800));self.assertEqual(f['pixel'],0)
        self.assertEqual(f['flash'],list(BUFFERS));self.assertGreater(len(s['flash']),2)
    def test_random_rectangles_preserve_framebuffer_and_context(self):
        rng=random.Random(9123)
        for _ in range(24):
            x=rng.randrange(220);y=rng.randrange(300);w=rng.randrange(1,20);h=rng.randrange(1,20)
            for kind,args in (('fill',(x,y,x+w-1,y+h-1,rng.randrange(65536))),
                              ('bitmap',(x,y,w,h,16,SOURCE)),
                              ('keyed',(x,y,x+w-1,y+h-1,16,SOURCE,rng.choice((0,1,2,255))))):
                self.compare(kind,args)

    def test_instruction_reduction(self):
        for kind,args in (('fill',(3,3,66,66,0xABCD)),('bitmap',(3,3,64,64,16,SOURCE)),('keyed',(3,3,66,66,16,SOURCE,1)),('bitmap',(3,3,16,16,1,SOURCE))):
            s,f=self.compare(kind,args,count=True)
            self.assertLess(f['instructions'],s['instructions']//2,(kind,s['instructions'],f['instructions']))
            print(f'{kind}: {s["instructions"]} -> {f["instructions"]} instructions')
if __name__=='__main__':unittest.main()
