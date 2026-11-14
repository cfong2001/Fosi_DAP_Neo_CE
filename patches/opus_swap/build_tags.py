"""Build original OpusTags reader into pinned resident pockets (LLVM)."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import shutil
import tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from rknano_image import Image
sys.path.insert(0,str(ROOT/'patches/full/build'))
from build_tail import branch

def run(*args):
    command=shutil.which(args[0]) or shutil.which(args[0]+'.exe') or args[0]
    r=subprocess.run((command,*args[1:]),text=True,capture_output=True)
    if r.returncode:raise RuntimeError(r.stderr)
    return r.stdout

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--census',type=Path)
    args=ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        b=Path(tmp);obj=b/'tags.o'
        run('clang','--target=arm-none-eabi','-mcpu=cortex-m3','-mthumb',
            '-Oz','-ffreestanding','-fno-builtin','-ffunction-sections',
            '-fdata-sections','-c',str(HERE/'opus_tags.c'),'-o',str(obj))
        sections={}
        for line in run('llvm-objdump','-h',str(obj)).splitlines():
            m=re.match(r'\s*\d+ (\S+)\s+([0-9a-f]+) ',line)
            if m and (m[1].startswith('.text.') or m[1].startswith('.rodata')):
                sections[m[1]]=int(m[2],16)
        layout_path=HERE/'tags-layout.json'
        if args.census:
            pockets=[(p['start'],p['end']) for p in json.loads(args.census.read_text())['candidates'] if p['tier'] in (1,2)]
            # Only the ASF-specific case is available. M4A/AAC and other
            # live format cases begin at C61A; they are never allocator space.
            pockets.append((0x0306C5B0,0x0306C61A))
            layout={}
            # The large sequence validator occupies the now-unused ASF case.
            order=sorted(sections,key=lambda s:(s!='.text.page_sequence',-sections[s]))
            for section in order:
                size=sections[section];choices=[]
                for i,(start,end) in enumerate(pockets):
                    addr=(start+3)&~3
                    if addr+size<=end:choices.append((end-addr-size,i,addr))
                if not choices:raise RuntimeError(f'no pocket for {section}: {size}')
                _,i,addr=min(choices);start,end=pockets[i]
                layout[section]={'address':addr,'bytes':size}
                pockets[i]=((addr+size+3)&~3,end)
            layout_path.write_text(json.dumps(layout,indent=2)+'\n')
        layout=json.loads(layout_path.read_text())
        for section,size in sections.items():assert layout[section]['bytes']==size,(section,size)
        ordered=sorted(layout,key=lambda s:layout[s]['address'])
        ld=b/'tags.ld';elf=b/'tags.elf'
        ld.write_text('SECTIONS {\n'+''.join(f'.p{i} {layout[s]["address"]:#x} : {{ *({s}) }}\n' for i,s in enumerate(ordered))+
                      '/DISCARD/ : { *(.ARM*) *(.comment) *(.note*) }\n}')
        run('ld.lld','-T',str(ld),str(obj),'-o',str(elf))
        assert not run('llvm-nm','-u',str(elf)).strip()
        symbols={p[2]:int(p[0],16) for line in run('llvm-nm',str(elf)).splitlines() if len(p:=line.split())==3}
        stock=(ROOT/'DP3_V137.img').read_bytes();im=Image(stock);off,_=im.module_region(0,'code');base=im.modules[0]['code_exec']
        edits=[]
        for i,s in enumerate(ordered):
            dest=b/f'p{i}.bin';run('llvm-objcopy','-O','binary','-j',f'.p{i}',str(elf),str(dest))
            edits.append((layout[s]['address'],dest.read_bytes(),s))
        edits.append((0x0306C5A6,bytes.fromhex('48463146')+branch(0x0306C5AA,symbols['opus_tags']&~1,True)+bytes.fromhex('52e0'),'dispatch'))
        names=[]
        for i,(addr,code,label) in enumerate(edits):
            assert not (addr<0x0306C66C and addr+len(code)>0x0306C61A),label
            assert not (addr<0x0306C5A6 and addr+len(code)>0x0306C576),label
            name=f'{230+i:04d}-opus-tags-{label.replace(".text.","").replace(".","-")}'
            expect=stock[off+addr-base:off+addr-base+len(code)]
            path=HERE/(name+'.patch');names.append('../opus_swap/'+path.name)
            path.write_text(f'# Original CE streaming OpusTags reader: {label}.\nname: {name}\nkind: module\nmodule: 0\nregion: code\naddress: {addr:#x}\nexpect: {expect.hex()}\nreplace: {code.hex()}\ngate: stock bytes, resident census, real-card parser regression\nrationale: Parse OpusTags with bounded reads and UTF-16 output instead of entering the obsolete ASF tag reader.\n')
        (HERE/'tags-manifest.txt').write_text('\n'.join(names)+'\n')
        print('OpusTags:',sum(len(x[1]) for x in edits),'bytes;',len(edits),'patches')
if __name__=='__main__':main()
