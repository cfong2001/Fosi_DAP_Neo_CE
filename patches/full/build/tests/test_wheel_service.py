"""Quantify hidden-wheel wake and uninterrupted visible wheel accounting."""
import sys
import struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path[:0]=[str(ROOT/'tools'),str(HERE.parent)]
from rknano_image import Image
from build_focus_wheel import assemble,POLL,WRAP,SERVICE,STATE
from build_tail import branch
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import *
SP=0x030ED000
END=0x030EE000
TOTAL=0x0302317C

def probe(raw,fix):
    im=Image(raw);u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(0x03000000,0x100000)
    for idx in (0,27):
        for kind in ('code','data'):
            off,n=im.module_region(idx,kind)
            if n:u.mem_write(im.modules[idx][kind+'_exec'],raw[off:off+n])
    if fix:
        poll,wrap=assemble()
        if fix=='embedded':
            assert bytes(u.mem_read(POLL,len(poll)))==poll
            assert bytes(u.mem_read(WRAP,len(wrap)))==wrap
            assert bytes(u.mem_read(SERVICE,4))==branch(SERVICE,WRAP)
        else:
            u.mem_write(POLL,poll);u.mem_write(WRAP,wrap);u.mem_write(SERVICE,branch(SERVICE,WRAP))
    posts=[];count=[0]
    def hook(uc,addr,size,user):
        count[0]+=1
        if addr==0x0306672E:
            uc.reg_write(UC_ARM_REG_R0,1000);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
        elif addr==0x0306723C:posts.append(uc.reg_read(UC_ARM_REG_R0))
    u.hook_add(UC_HOOK_CODE,hook)
    u.mem_write(STATE,struct.pack('<II',0,0)+b'\x01\0\0\0')
    u.mem_write(TOTAL,struct.pack('<I',1))
    if not fix:
        # Actual legacy tick path posts progress but never checks a wheel
        # change after hidden is set.
        u.reg_write(UC_ARM_REG_SP,SP);u.reg_write(UC_ARM_REG_LR,END|1);u.reg_write(UC_ARM_REG_R0,0x40)
        u.emu_start(0x0307C201,END,count=10000)
        assert bytes(u.mem_read(STATE+8,1))==b'\x01'
        assert 0x39 not in posts and 0x3b not in posts
        return {'hidden_wake_events':0,'instructions':count[0]}
    def service():
        kept=(UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R12)
        values=[0x100+i for i in range(len(kept))]
        for reg,val in zip(kept,values):u.reg_write(reg,val)
        u.reg_write(UC_ARM_REG_SP,SP);u.reg_write(UC_ARM_REG_LR,END|1)
        u.emu_start(SERVICE|1,SERVICE+4,count=10000)
        assert u.reg_read(UC_ARM_REG_PC)==SERVICE+4
        assert u.reg_read(UC_ARM_REG_SP)==SP-28
        assert [u.reg_read(r) for r in kept]==values
    service();wake_cost=count[0]
    assert bytes(u.mem_read(STATE+8,1))==b'\0'
    assert posts.count(0x39)==1 and posts.count(0x3b)==1
    assert struct.unpack('<I',u.mem_read(STATE+4,4))[0]==1
    posts.clear()
    for step in range(2,22):
        u.mem_write(TOTAL,struct.pack('<I',step));service()
        assert struct.unpack('<I',u.mem_read(STATE+4,4))[0]==step
    assert not posts,'visible wheel movement must not request artwork or full repaint'
    assert wake_cost<200
    return {'hidden_wake_events':1,'required':1,'wake_instructions':wake_cost,
            'visible_steps_accounted':20,'visible_artwork_requests':0,
            'volatile_inputs_preserved':True,'stock_prologue_replayed':True}

def main():
    raw=(ROOT/'release/DP3_V137_CE.img').read_bytes()
    print('Legacy:',probe(raw,False));print('Repaired:',probe(raw,True))
if __name__=='__main__':main()
