"""Compact non-rendering baseline: native metadata I/O, sort and wheel service."""
import json
import runpy
import struct
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools')]
from repair_metrics import opus
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_PC,UC_ARM_REG_LR

def sort_metrics():
    h=runpy.run_path(str(ROOT/'patches/full/build/tests/test_sort_lifecycle.py'))
    rows=[]
    for names in (['Alpha','Beta'],['Track 10','Track 2']):
        u=h['machine'](); counts=dict(instructions=0,database_reads=0)
        def hook(uc,addr,size,user):
            counts['instructions']+=1
            if addr!=0x03067510:return
            dev,source,n,dst=[uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
            assert dev==0x30001 and n==256
            counts['database_reads']+=1
            uc.mem_write(dst,(names[source//2048]+'\0').encode('utf-16-le').ljust(256,b'\0'))
            uc.reg_write(UC_ARM_REG_R0,0);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
        u.hook_add(UC_HOOK_CODE,hook)
        for buffer in (0x0307f48c,0x0308f48c):h['call'](u,0x0307d75e,buffer)
        u.mem_write(0x0302329c,bytes(4));u.mem_write(0x030247ec,bytes(8))
        records=[0x030a0000,0x030a0020]
        for i,record in enumerate(records):
            u.mem_write(record,bytes(32));u.mem_write(record+12,struct.pack('<H',i))
            h['call'](u,h['BASE']+0xb6,record)
        u.mem_write(0x0307e1f4,b'\xff'*8)
        for state in ('cold','warm'):
            counts.update(instructions=0,database_reads=0)
            result=h['call'](u,0x0307d620,records[0]+4,records[1]+4)
            assert result==(0 if names[0]=='Alpha' else 2)
            rows.append(dict(case='prefix' if names[0]=='Alpha' else 'numeric',cache=state,result=result,**counts))
    return rows

def check():
    raw=(ROOT/'release/DP3_V137_CE.img').read_bytes()
    tags=runpy.run_path(str(ROOT/'patches/opus_swap/test_tags.py'))
    rows=[]
    for n in (5,12,24,48):
        metrics={}
        got=tags['parse'](opus([('X'*n,'ignored'),('TITLE','Title')]),raw=raw,apply_patches=False,native_fs=True,metrics=metrics)
        assert got['title']=='Title'
        rows.append(dict(unknown_key_bytes=n,**metrics))
    wheel=runpy.run_path(str(ROOT/'patches/full/build/tests/test_wheel_service.py'))
    return dict(metadata_unknown_key=rows,sorting=sort_metrics(),wheel_service=wheel['probe'](raw,'embedded'),
                timing_units='emulator instructions and modeled I/O calls; not device milliseconds')

if __name__=='__main__':print(json.dumps(check(),indent=2))
