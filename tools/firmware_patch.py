#!/usr/bin/env python3
"""Offline, size-preserving V137 firmware patcher. Never communicates with a DAP.

A successful offline CRC/mirror check DOES NOT establish that retail devices
will install or boot modified firmware. No device writes are implemented.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from rknano_image import Image, rk_crc32

STOCK_SHA256 = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'


def validate(raw):
    im = Image(raw)
    info = im.summary()
    if not info['header_mirror_valid'] or not info['crc_valid']:
        raise ValueError('header mirror or trailer CRC failed')
    if len(raw) != 0xd00004 or im.u32(0x1f4) != 0xc94000 or len(im.modules) != 82:
        raise ValueError('input is not a V137-layout update package')
    return im


def bcd_date(date):
    import datetime
    if len(date) != 8 or not date.isdigit():
        raise ValueError('date must be YYYYMMDD')
    datetime.date(int(date[:4]), int(date[4:6]), int(date[6:8]))
    return struct.pack('<HH',int(date[:4],16),int(date[4:],16))


def patch(raw, *, module=None, region='code', address=None, expect=None,
          replace=None, language=None, string_id=None, expect_text=None,
          replace_text=None, date=None):
    raw=bytearray(raw)
    im=validate(bytes(raw))
    if hashlib.sha256(raw).hexdigest()!=STOCK_SHA256:
        raise ValueError('firmware SHA-256 does not match unmodified V137')
    if (module is not None) == (string_id is not None):
        raise ValueError('select exactly one patch target: module OR language string')
    if module is not None:
        if region not in ('code','data') or not 0<=module<len(im.modules):
            raise ValueError('invalid module/region')
        if address is None or expect is None or replace is None:
            raise ValueError('module patch requires address, expect, replace')
        if len(expect)<1 or len(expect)!=len(replace):
            raise ValueError('replacement must preserve byte length')
        m=im.modules[module]
        rel=address-m[region+'_exec']
        if rel<0 or rel+len(replace)>m[region+'_len']:
            raise ValueError('patch crosses selected module boundary')
        base,_=im.module_region(module,region)
        off=base+rel
        if raw[off:off+len(expect)]!=expect:
            raise ValueError('stock code/data byte precondition mismatch')
        raw[off:off+len(replace)]=replace
        edit={'kind':'module','module':module,'region':region,
              'cpu_address':hex(address),'file_offset':hex(off),
              'old_hex':expect.hex(),'new_hex':replace.hex()}
    else:
        if language is None or expect_text is None or replace_text is None:
            raise ValueError('string patch needs language, expected and replacement text')
        s=im.sections['lang'];start=s['offset']
        n=struct.unpack_from('<H',raw,start)[0]
        if not 0<=language<n or not 0<=string_id<266:
            raise ValueError('language/string ID out of bounds')
        lang_offset=im.u32(start+2+language*4)
        rec=start+lang_offset+string_id*258
        if struct.unpack_from('<H',raw,rec)[0]!=string_id:
            raise ValueError('string resource record ID mismatch')
        off=rec+58
        original=raw[off:off+200].decode('utf-16le').split('\0',1)[0]
        if original!=expect_text:
            raise ValueError('stock UI text precondition mismatch')
        value=replace_text.encode('utf-16le')+b'\0\0'
        if len(value)>200:
            raise ValueError('string too long for fixed field')
        raw[off:off+200]=value.ljust(200,b'\0')
        edit={'kind':'string','language':language,'string_id':string_id,
              'file_offset':hex(off),'old_text':original,'new_text':replace_text}
    if date is not None:
        raw[:4]=bcd_date(date)
    raw[0xc94000:0xc94200]=raw[:0x200]
    struct.pack_into('<I',raw,len(raw)-4,rk_crc32(raw[:-4]))
    after=validate(bytes(raw))
    return bytes(raw),{'input_sha256':STOCK_SHA256,
                       'output_sha256':hashlib.sha256(raw).hexdigest(),
                       'byte_length':len(raw),
                       'header_mirror_valid':after.summary()['header_mirror_valid'],
                       'crc_valid':after.summary()['crc_valid'],
                       'stored_crc32':hex(after.u32(len(raw)-4)),
                       'date_bcd':raw[:4].hex(),
                       'edit':edit,
                       'scope':'offline package integrity only; actual device acceptance unverified'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('image',type=Path)
    p.add_argument('--output',type=Path,help='must not exist; never overwrite source')
    p.add_argument('--module',type=int)
    p.add_argument('--region',choices=('code','data'),default='code')
    p.add_argument('--address',type=lambda x:int(x,0))
    p.add_argument('--expect',help='expected code/data bytes as hex')
    p.add_argument('--replace',help='same-length replacement as hex')
    p.add_argument('--language',type=int)
    p.add_argument('--string-id',type=int)
    p.add_argument('--expect-text')
    p.add_argument('--replace-text')
    p.add_argument('--date',help='YYYYMMDD; use only with understood recovery/slot policy')
    a=p.parse_args()
    try:
        old=bytes.fromhex(a.expect) if a.expect is not None else None
        new=bytes.fromhex(a.replace) if a.replace is not None else None
    except ValueError as e:
        p.error(str(e))
    out,proof=patch(a.image.read_bytes(),module=a.module,region=a.region,
                    address=a.address,expect=old,replace=new,
                    language=a.language,string_id=a.string_id,
                    expect_text=a.expect_text,replace_text=a.replace_text,date=a.date)
    if a.output:
        if a.output.resolve()==a.image.resolve():
            p.error('refusing to overwrite stock firmware')
        with a.output.open('xb') as f:
            f.write(out)
        proof['output_file']=str(a.output)
    else:
        proof['output_file']=None
        proof['note']='modified bytes discarded after offline validation'
    print(json.dumps(proof,indent=2))

if __name__=='__main__':
    main()
