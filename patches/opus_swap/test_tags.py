"""Execute the real resident tag dispatcher and OpusTags reader under Unicorn."""
import argparse
import json
import struct
import sys
import os
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(ROOT/'patches/framework'))
from rknano_image import Image
from build import parse_patch
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE,UC_HOOK_MEM_WRITE,UC_HOOK_MEM_INVALID
from unicorn.arm_const import *
END=0x030EF000
RECORD=0x030D0000

def parse(data,watchdog=True,raw=None,apply_patches=True,native_fs=False,extension=b'OPU',metrics=None):
    if raw is None:raw=(ROOT/'release/DP3_V137_CE.img').read_bytes()
    im=Image(raw)
    u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(0x03000000,0x100000)
    u.mem_map(0x40120000,0x1000)
    for kind in ('code','data'):
        off,n=im.module_region(0,kind);u.mem_write(im.modules[0][kind+'_exec'],raw[off:off+n])
    for name in (HERE/'tags-manifest.txt').read_text().splitlines() if apply_patches else ():
        row=parse_patch(HERE/name);u.mem_write(row['address'],row['replace'])
    u.mem_write(RECORD-8,b'Z'*8);u.mem_write(RECORD+0x556,b'Z'*8)
    assert len(extension)==3
    u.mem_write(0x030D1000,extension)
    if native_fs:
        # Actual FileRead/FileSeek descriptor and FAT32 geometry. Only the
        # sector-device leaf, FAT-chain lookup, and IRQ gate are modeled.
        fd=0x0307AB68+638*7
        u.mem_write(fd,bytes(638));u.mem_write(fd,b'\x01')
        for off,value in ((16,len(data)),(20,2),(24,2),(32,0)):
            u.mem_write(fd+off,struct.pack('<I',value))
        u.mem_write(0x0307A024,b'\x00')
        u.mem_write(0x0307A026,struct.pack('<HH',6,9))
        u.mem_write(0x0307A02C,struct.pack('<I',0x30001))
        u.mem_write(0x0307A030,struct.pack('<II',512,64))
        u.mem_write(0x0307A04F,struct.pack('<I',100))
    pos=0;calls=0;elapsed=0;kicks=0;pending=[];instructions=0;sectors=0;read_calls=0
    def watchdog_write(uc,access,addr,size,value,user):
        nonlocal elapsed,kicks
        assert addr==0x4012000c and size==4 and value==0x76
        elapsed=0;kicks+=1
    u.hook_add(UC_HOOK_MEM_WRITE,watchdog_write,begin=0x40120000,end=0x40120fff)
    def hook(uc,addr,size,user):
        nonlocal pos,calls,elapsed,instructions,sectors,read_calls
        if metrics is not None:instructions+=1
        if addr==0x03058FA8:read_calls+=1
        if native_fs and os.environ.get('CE_TRACE_FS'):
            if pending and addr==pending[-1][0]:
                lr,dst,n=pending.pop();print('FileRead result',uc.reg_read(UC_ARM_REG_R0),bytes(uc.mem_read(dst,min(n,28))).hex())
            if addr==0x03058FA8:pending.append((uc.reg_read(UC_ARM_REG_LR)&~1,uc.reg_read(UC_ARM_REG_R0),uc.reg_read(UC_ARM_REG_R1)))
        if addr in (0x03058FA8,0x030594A0,0x030545D4,0x030545F8):
            elapsed+=20
            if watchdog:assert elapsed<=80,'simulated slow storage exceeded watchdog service interval'
        if native_fs and addr in (0x0306660A,0x03066662):
            uc.reg_write(UC_ARM_REG_R0,0)
        elif native_fs and addr==0x0305715C:
            uc.reg_write(UC_ARM_REG_R0,uc.reg_read(UC_ARM_REG_R0)+uc.reg_read(UC_ARM_REG_R1))
        elif native_fs and addr==0x030678CA:
            sectors+=1
            dev,sector,n,dst=[uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
            assert dev==0x30001 and sector>=100 and 0<n<=128,(dev,sector,n)
            offset=(sector-100)*512;block=data[offset:offset+n*512].ljust(n*512,b'\0')
            if os.environ.get('CE_TRACE_FS'):print('sector',sector,n,'offset',offset,'prefix',block[:8].hex())
            uc.mem_write(dst,block);uc.reg_write(UC_ARM_REG_R0,0)
        elif native_fs and addr in (0x03058FA8,0x030594A0,0x030545D4,0x030545F8):return
        elif addr==0x03058FA8:
            dst,n,h=[uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
            assert h==7 and n<=508,(h,n)
            block=data[pos:pos+n];pos+=len(block)
            if block:uc.mem_write(dst,block)
            uc.reg_write(UC_ARM_REG_R0,len(block));calls+=1
        elif addr==0x030594A0:
            offset,whence,h=[uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
            assert h==7 and whence==0 and offset<=len(data),(offset,whence,h,len(data),hex(uc.reg_read(UC_ARM_REG_LR)))
            pos=offset;uc.reg_write(UC_ARM_REG_R0,0)
        elif addr==0x030545D4:uc.reg_write(UC_ARM_REG_R0,len(data))
        elif addr==0x030545F8:pos=0;uc.reg_write(UC_ARM_REG_R0,0)
        elif addr in (0x0307E134,0x0308B560):raise AssertionError('obsolete ASF reader executed')
        else:return
        uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
    u.hook_add(UC_HOOK_CODE,hook)
    def invalid(uc,access,address,size,value,user):
        raise AssertionError(f'invalid memory access at PC {uc.reg_read(UC_ARM_REG_PC):#x}, address {address:#x}, size {size}')
    u.hook_add(UC_HOOK_MEM_INVALID,invalid)
    for r,v in ((UC_ARM_REG_R0,7),(UC_ARM_REG_R1,RECORD),(UC_ARM_REG_R2,0x030D1000),
                (UC_ARM_REG_SP,0x030ED000),(UC_ARM_REG_LR,END|1)):
        u.reg_write(r,v)
    try:u.emu_start(0x0306C51D,END,count=10000000)
    except Exception as exc:
        raise RuntimeError(f'{exc}; PC={u.reg_read(UC_ARM_REG_PC):#x}, LR={u.reg_read(UC_ARM_REG_LR):#x}, R0..3={[hex(u.reg_read(r)) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]}') from exc
    assert u.reg_read(UC_ARM_REG_PC)==END
    assert u.reg_read(UC_ARM_REG_SP)==0x030ED000
    assert bytes(u.mem_read(RECORD-8,8))==b'Z'*8
    assert bytes(u.mem_read(RECORD+0x556,8))==b'Z'*8
    if len(data)>1000 and extension==b'OPU':assert kicks>0,'reader did not service the hardware watchdog'
    if metrics is not None:metrics.update(instructions=instructions,sector_read_calls=sectors,
                                        file_read_calls=read_calls,watchdog_reloads=kicks,
                                        stack_restored=True,record_guards_intact=True)
    def text(off):return bytes(u.mem_read(RECORD+off,254)).decode('utf-16-le').split('\0')[0]
    return {key:text(off) for key,off in [('title',0x60),('artist',0x15e),('album',0x25c),('genre',0x35a)]}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--media-dir',type=Path)
    ap.add_argument('--image',type=Path);ap.add_argument('--native-fs',action='store_true');a=ap.parse_args()
    raw=a.image.read_bytes() if a.image else None
    if a.media_dir:
        from mutagen.oggopus import OggOpus
    count=0
    for p in a.media_dir.rglob('*.opus') if a.media_dir else ():
        want=OggOpus(p);got=parse(p.read_bytes(),raw=raw,apply_patches=raw is None,native_fs=a.native_fs)
        for key,value in got.items():
            expected=want.get(key,[''])[0]
            # Reader reserves room for a two-unit supplementary character.
            if len(expected.encode('utf-16-le'))<=252:assert value==expected,(key,repr(value),repr(expected))
        count+=1
        if count%25==0:print(f'Validated {count} Opus files',flush=True)
    if a.media_dir:
        assert count
        print(f'PASS: {count} Opus files through the real tag dispatcher; title, artist, album, genre match host parser; ASF path never entered; stack and record guards intact')

    def pages(packets):
        result=b'';seq=0
        for packet in packets:
            laces=[255]*(len(packet)//255)+[len(packet)%255];offset=0;continued=False
            while laces:
                part,laces=laces[:255],laces[255:];n=sum(part)
                flags=(2 if seq==0 else 0)|(1 if continued else 0)
                h=b'OggS'+bytes([0,flags])+bytes(8)+struct.pack('<III',123,seq,0)+bytes([len(part)])
                result+=h+bytes(part)+packet[offset:offset+n];offset+=n;seq+=1;continued=True
        return result
    head=b'OpusHead'+bytes([1,2])+bytes(9)
    values=[b'TITLE='+('Unicode 音楽 🎵').encode(),b'METADATA_BLOCK_PICTURE='+b'x'*445020,
            b'ARTIST=Artist',b'ALBUM=Album',b'GENRE=Genre']
    tags=b'OpusTags'+struct.pack('<II',0,len(values))+b''.join(struct.pack('<I',len(v))+v for v in values)
    sample=pages([head,tags])
    assert parse(sample)==dict(title='Unicode 音楽 🎵',artist='Artist',album='Album',genre='Genre')
    for n in (0,1,26,27,28,45,46,60,len(sample)-1):parse(sample[:n])
    bad=b'OpusTags'+struct.pack('<II',0,0xffffffff)
    parse(pages([head,bad]))
    bad=b'OpusTags'+struct.pack('<III',0,1,0xffffffff)
    parse(pages([head,bad]))
    print('PASS: multi-page large artwork skip, Unicode, truncated pages/packets, excessive counts and lengths return without stack/record corruption; simulated slow I/O stays within watchdog interval and executes real hardware reload writes')
if __name__=='__main__':main()
