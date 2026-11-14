"""Run real sort-buffer initialization before executing CE natural sorting."""
import sys
import struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path[:0]=[str(ROOT/'tools'),str(HERE.parent)]
from rknano_image import Image
from build_sort_extension import assemble,BASE,OLD
from build_tail import branch
sys.path.insert(0,str(ROOT/'patches/framework'))
from build import parse_patch
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import *
END=0x030EE000
SP=0x030ED000

def machine(path=None):
    raw=(path or ROOT/'release/DP3_V137_CE.img').read_bytes();im=Image(raw)
    u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(0x03000000,0x100000)
    for idx in (0,39):
        for kind in ('code','data'):
            off,n=im.module_region(idx,kind)
            if n:u.mem_write(im.modules[idx][kind+'_exec'],raw[off:off+n])
    return u

def call(u,entry,r0=0,r1=0):
    for reg,val in ((UC_ARM_REG_R0,r0),(UC_ARM_REG_R1,r1),
                    (UC_ARM_REG_SP,SP),(UC_ARM_REG_LR,END|1)):
        u.reg_write(reg,val)
    u.emu_start(entry|1,END,count=3000000)
    assert u.reg_read(UC_ARM_REG_PC)==END
    assert u.reg_read(UC_ARM_REG_SP)==SP
    return u.reg_read(UC_ARM_REG_R0)

def main():
    u=machine();old=parse_patch(ROOT/'patches/framework/patches/0031-sortkeys-cave.patch')['replace']
    u.mem_write(OLD,old)
    call(u,0x0307D75E,0x0308F48C)
    assert bytes(u.mem_read(OLD,1052))==bytes(1052)
    print('PASS negative control: stock buffer initialization erases the former CE code home')
    path=Path(sys.argv[1]) if len(sys.argv)>1 else None
    u=machine(path);payload=assemble()
    if path:assert bytes(u.mem_read(BASE,len(payload)))==payload
    else:
        u.mem_write(BASE,payload)
        u.mem_write(0x0307D620,branch(0x0307D620,BASE))
    for buffer in (0x0307F48C,0x0308F48C):call(u,0x0307D75E,buffer)
    assert bytes(u.mem_read(BASE,len(payload)))==payload
    print('PASS: both real 64 KiB buffer clears preserve every byte of the extension')
    # Execute the existing database-read ABI, then the relocated prefix and
    # full comparator paths after initialization (the former missing gate).
    names=['Track 10','Track 2'];records=[0x030A0000,0x030A0020]
    def hook(uc,addr,size,user):
        if addr!=0x03067510:return
        dev,source,n,dst=[uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
        assert dev==0x30001 and n==256
        idx=source//2048;assert idx in (0,1),source
        uc.mem_write(dst,(names[idx]+'\0').encode('utf-16-le').ljust(256,b'\0'))
        uc.reg_write(UC_ARM_REG_R0,0);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
    u.hook_add(UC_HOOK_CODE,hook)
    u.mem_write(0x0302329c,bytes(4));u.mem_write(0x030247ec,bytes(8))
    for i,record in enumerate(records):
        u.mem_write(record,bytes(32));u.mem_write(record+12,struct.pack('<H',i))
        call(u,BASE+0xb6,record)
    assert call(u,0x0307D620,records[0]+4,records[1]+4)==2
    assert call(u,0x0307D620,records[1]+4,records[0]+4)==0
    assert bytes(u.mem_read(BASE,len(payload)))==payload
    print('PASS: relocated prefix builder and comparator execute after buffer initialization, including database reads and numeric ordering')
if __name__=='__main__':main()
