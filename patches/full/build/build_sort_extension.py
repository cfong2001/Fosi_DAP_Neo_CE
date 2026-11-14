"""Relocate the pinned natural sorter beyond module 39's live scratch arrays.

The former 0x0309F000 home lies within the 64 KiB scratch array at
0x0308F48C. Stock SortPageBufferInit clears that whole array. The new
home is an explicit code-segment extension after every stock byte.
"""
import hashlib
import json
import sys
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
from keystone import Ks,KS_ARCH_ARM,KS_MODE_THUMB
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'patches/framework'))
from build import parse_patch
sys.path.insert(0,str(HERE))
from build_tail import branch
OLD=0x0309F000
BASE=0x0309F4AC

def assemble():
    patch=parse_patch(ROOT/'patches/framework/patches/0031-sortkeys-cave.patch')
    original=patch['replace'];assert len(original)==1052
    code_end=len(original)-128
    out=bytearray(original);ks=Ks(KS_ARCH_ARM,KS_MODE_THUMB)
    decoder=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
    fold_old=OLD+code_end;fold_new=BASE+code_end;fixes=0;externals=0
    for ins in decoder.disasm(original[:code_end],OLD):
        offset=ins.address-OLD
        if ins.mnemonic in ('bl','b.w') and ins.op_str.startswith('#'):
            target=int(ins.op_str[1:],16)
            if not OLD<=target<OLD+len(original):
                out[offset:offset+4]=branch(BASE+offset,target,ins.mnemonic=='bl');externals+=1
        if ins.mnemonic=='movw' and ins.op_str==f'r3, #{fold_old&65535:#x}':
            encoded=bytes(ks.asm(f'movw r3, #{fold_new&65535}',BASE+offset)[0]);assert len(encoded)==4
            out[offset:offset+4]=encoded;fixes+=1
        if ins.mnemonic.startswith('ldr') and '[pc' in ins.op_str:raise ValueError('unhandled PC-relative literal')
    assert fixes==1 and externals==3,(fixes,externals)
    # Re-decode every branch and require the exact original destination,
    # relocated only for targets within the payload itself.
    before=list(decoder.disasm(original[:code_end],OLD))
    after=list(decoder.disasm(bytes(out[:code_end]),BASE))
    assert len(before)==len(after)
    for a,b in zip(before,after):
        assert a.size==b.size and a.mnemonic==b.mnemonic
        if a.mnemonic.startswith('b') and a.op_str.startswith('#'):
            target=int(a.op_str[1:],16)
            if OLD<=target<OLD+len(original):target+=BASE-OLD
            assert int(b.op_str[1:],16)==target,(a,b)
    return bytes(out)

def main():
    payload=assemble();out=HERE.parent/'out';out.mkdir(exist_ok=True)
    (out/'sort39.bin').write_bytes(payload)
    (out/'layout_sort39.json').write_text(json.dumps({'base':hex(BASE),'bytes':len(payload),
        'sha256':hashlib.sha256(payload).hexdigest(),'stock_scratch_end':hex(BASE),
        'comparator':hex(BASE),'prefix_builder':hex(BASE+0xb6)},indent=2)+'\n')
    for number,label,site,reg,exit_addr in (
            (27,'comparator',0x0307D620,None,None),
            (28,'builder-a',0x0307D87E,'r5',0x0307D8AE),
            (29,'builder-bmain',0x0307D954,'r4',0x0307D984),
            (30,'builder-balt',0x0307D9F2,'r4',0x0307DA22)):
        stock=(ROOT/'DP3_V137.img').read_bytes()
        from rknano_image import Image
        im=Image(stock);offset,_=im.module_region(39,'code')
        length=4 if reg is None else 48
        expected=stock[offset+site-im.modules[39]['code_exec']:offset+site-im.modules[39]['code_exec']+length]
        if reg is None:replacement=branch(site,BASE)
        else:
            mov=bytes.fromhex('2846' if reg=='r5' else '2046')
            replacement=mov+branch(site+2,BASE+0xb6,True)+branch(site+6,exit_addr)+bytes.fromhex('00bf')*19
        assert len(replacement)==length
        name=f'{number:04d}-sort-extension-{label}'
        (HERE.parent/'patches'/f'{name}.patch').write_text(
            f'# Natural-sort hook into explicit module 39 extension.\nname: {name}\nkind: module\nmodule: 39\nregion: code\naddress: {site:#x}\nexpect: {expected.hex()}\nreplace: {replacement.hex()}\ngate: stock-byte precondition; sort-buffer lifecycle regression\nrationale: Keep natural-sort code beyond all live scratch buffers, which are cleared during every library rebuild. Requires the module 39 code extension.\n')
    print(f'Sort extension: {len(payload)} bytes at {BASE:#x}, SHA-256 {hashlib.sha256(payload).hexdigest()}')
if __name__=='__main__':main()
