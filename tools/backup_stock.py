#!/usr/bin/env python3
"""Read-only DP3 Rockusb information/range backup using a pinned Windows transport.

No flash-write, erase, reset or loader-download command is issued. Hardware
compatibility and capacity remain unverified until checked on the real unit.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import types
TRANSPORT_BLOB='ae5627283a2f80c445b8f15155cf12c6a38c283d'
ALLOWED_READS=frozenset((0x14,0x1A,0x1B))
SECTOR=512

def load_transport(path):
    raw=path.read_bytes().replace(b'\r\n',b'\n')
    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    if blob!=TRANSPORT_BLOB:raise ValueError('transport is not the reviewed restore-stock.py Git blob; refusing to import')
    if sys.platform!='win32':raise ValueError('the reviewed transport requires Windows; no USB commands were sent')
    module=types.ModuleType('reviewed_dp3_read_transport');module.__file__=str(path.resolve())
    # The reviewed source defines its driver/class at import and puts every
    # restore/write operation behind its __main__ guard. Pin before executing.
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module

class ReadOnly:
    """Restrict the unexposed transport to the three reviewed read commands."""
    def __init__(self,usb):self._usb=usb
    def command(self,opcode,length,address=0,sectors=0):
        if opcode not in ALLOWED_READS:raise ValueError('non-read Rockusb command refused')
        if opcode==0x14:
            if not 0<=address<=0xffffffff or not 1<=sectors<=16 or length!=sectors*SECTOR:
                raise ValueError('invalid bounded LBA read')
        elif (opcode,length,address,sectors) not in ((0x1A,11,0,0),(0x1B,16,0,0)):
            raise ValueError('invalid information read')
        raw=self._usb.command(opcode,length,address,sectors)
        expected=512 if opcode==0x1A else length
        if len(raw)!=expected:raise ValueError(f'short information/data read: {len(raw)} / {expected}')
        return raw

def information(usb):
    return {'chip_info_hex':usb.command(0x1B,16).hex(),
            'flash_info_raw_hex':usb.command(0x1A,11).hex(),
            'capacity_interpreted':False,'flash_write_commands_issued':False}

def backup(usb,sectors,output):
    if not isinstance(sectors,int) or not 1<=sectors<=0x100000000:
        raise ValueError('sector count must be within the 32-bit LBA address space')
    if output.exists() or output.is_symlink():raise ValueError('output already exists')
    # Query before creating output; do not infer units/capacity from an
    # undocumented flash-info layout or silently choose a presumed slot map.
    info=information(usb)
    output.mkdir(parents=True,exist_ok=False)
    report={**info,'start_lba':0,'sectors_requested':sectors,'bytes_requested':sectors*SECTOR,
            'sector_bytes':SECTOR,'whole_device_capacity_verified':False,
            'two_independent_reads_match':False,'restore_verified_on_device':False,
            'files':[],'status':'INCOMPLETE'}
    manifest=output/'BACKUP.json'
    try:
        for passno in (1,2):
            name=f'stock-read-{passno}.bin';h=hashlib.sha256();count=0
            with (output/name).open('xb') as f:
                for lba in range(0,sectors,16):
                    n=min(16,sectors-lba);data=usb.command(0x14,n*SECTOR,lba,n)
                    if len(data)!=n*SECTOR:raise ValueError('short LBA read')
                    f.write(data);h.update(data);count+=len(data)
            report['files'].append({'name':name,'bytes':count,'sha256':h.hexdigest()})
        if report['files'][0]['sha256']!=report['files'][1]['sha256']:
            raise ValueError('independent backup reads disagree; do not flash')
        report['two_independent_reads_match']=True
        report['status']='READ RANGE VERIFIED; DEVICE CAPACITY AND RESTORE STILL REQUIRE QUALIFICATION'
        return report
    except Exception as exc:
        report['error']=str(exc);raise
    finally:
        with manifest.open('x') as f:json.dump(report,f,indent=2);f.write('\n')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--transport',type=Path,required=True,help='reviewed community restore-stock.py, imported after blob verification; never run it directly for backup')
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--info',action='store_true',help='read chip/flash information only; does not interpret flash capacity')
    g.add_argument('--sectors',type=int,help='entire device capacity in 512-byte sectors, independently confirmed; never guess a slot size')
    p.add_argument('--output',type=Path,help='new directory for two independent reads and BACKUP.json')
    a=p.parse_args()
    if a.sectors is not None and (a.output is None or a.output.exists() or a.output.is_symlink()):
        p.error('backup needs a new --output directory')
    if a.info and a.output is not None:p.error('--output is only used for backup')
    if a.sectors is not None and not 1<=a.sectors<=0x100000000:p.error('invalid sector count')
    transport=load_transport(a.transport);raw_usb=transport.Rockusb(transport.device_path())
    try:
        usb=ReadOnly(raw_usb)
        report=information(usb) if a.info else backup(usb,a.sectors,a.output)
        print(json.dumps(report,indent=2))
    finally:raw_usb.close()
if __name__=='__main__':main()
