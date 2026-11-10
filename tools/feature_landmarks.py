#!/usr/bin/env python3
"""Check feature-related V137 instruction/data landmarks against original bytes.

Numeric event IDs and localized string IDs are different namespaces.
Equal numbers do not establish a matching setting handler.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from rknano_image import Image

SHA256='fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
UI_SITES=[
 ('raw_compare_0x97',32,0x0307d22c,0x2897,151,'comparison (not mapped to Play Mode)'),
 ('event_184_set',32,0x0307fda8,0x20b8,184,'set event via 0x0306723c'),
 ('event_184_consume',32,0x030800b6,0x20b8,184,'test and clear via 0x03067258'),
 ('event_188_consume',32,0x0307d820,0x20bc,188,'test and clear via 0x03067258'),
 ('draw_operand_196',32,0x0307d4dc,0x20c4,196,'branch to drawing path 0x0307d408'),
 ('call_operand_202',32,0x0307d5e0,0x20ca,202,'call 0x0306354a'),
]
STRINGS=[
 ('menu_event_debug',32,'MenuKeyPro - SelItemID'),
 ('playback_debug',31,'HoldOnplay : %d'),
 ('playlist_index_debug',27,'CurrentFileNum '),
 ('filesystem_total_debug',23,'TotalFiles is --- %d ---'),
 ('album_art_metadata',18,'METADATA_BLOCK_PICTURE'),
 ('shutdown_debug',0,'system powerdown!'),
 ('i2c_debug',0,'i2c write error happen '),
]
UI_IDS=(80,85,151,154,157,184,188,196,202,208)


def evidence(image):
    if hashlib.sha256(image.raw).hexdigest()!=SHA256:
        raise ValueError('addresses are pinned to the uploaded V137 image')
    english={x['id']:x for x in image.lang(2)}
    out={'firmware_sha256':SHA256,'ui_resources':[],'instruction_sites':[],'module_strings':[]}
    for id_ in UI_IDS:
        rec=english[id_]
        out['ui_resources'].append({'id':id_,'text':rec['text'],
                     'file_offset':hex(rec['file_offset']),'status':'resource only'})
    for name,idx,address,opcode,operand,interpretation in UI_SITES:
        m=image.modules[idx];start,n=image.module_region(idx,'code')
        offset=start+address-m['code_exec']
        if not start<=offset<=start+n-2:
            raise ValueError(f'{name} falls outside module')
        actual=struct.unpack_from('<H',image.raw,offset)[0]
        if actual!=opcode:
            raise ValueError(f'{name} mismatch at {address:#x}: {actual:#x}')
        out['instruction_sites'].append({'name':name,'module':idx,'cpu_address':hex(address),
                     'file_offset':hex(offset),'opcode_halfword':hex(actual),
                     'operand':operand,'interpretation':interpretation,
                     'status':'raw instruction verified; feature linkage unproved'})
    for name,idx,string in STRINGS:
        m=image.modules[idx];start,n=image.module_region(idx,'code')
        pos=image.raw[start:start+n].find(string.encode())
        if pos<0:raise ValueError(f'module {idx} missing {name}')
        out['module_strings'].append({'name':name,'module':idx,'cpu_address':hex(m['code_exec']+pos),
                                       'file_offset':hex(start+pos),'string':string,
                                       'status':'bytes present; caller and semantics not proven'})
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('image',type=Path)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    result=evidence(Image(a.image.read_bytes()))
    data=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
    if a.output:a.output.write_text(data)
    else:print(data,end='')


if __name__=='__main__':
    main()
