"""Measure a metadata ASCII fast path in emulator scratch space only.

The scratch placement is not a qualified firmware code home. This is a
performance experiment; it emits no image and changes no release patches.
"""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'patches/opus_swap'),str(ROOT/'patches/full/build')]
from test_tags import parse
from repair_metrics import opus,ogg
from build_tail import branch
from build_tags import run

SCRATCH=0x030c0000
BASELINE='08054971d2a5ef837c5186a8b31e20f720bedbc1ddb41978885b0f4e32d105c9'

def prototype():
    assert '22.1.3' in run('clang','--version'), 'use the pinned LLVM reference compiler'
    here=ROOT/'patches/opus_swap'
    layout=json.loads((here/'tags-layout.json').read_text())
    layout=dict(sorted(layout.items(),key=lambda row: SCRATCH if row[0]=='.text.utf16' else row[1]['address']))
    source=(here/'opus_tags.c').read_text()
    needle='        u32 used,c=codepoint(p+i,n-i,&used);'
    assert source.count(needle)==1
    source=source.replace(needle,"        if(p[i]<128) { if(!p[i])break;out[j++]=p[i++];continue; }\n"+needle)
    with tempfile.TemporaryDirectory() as td:
        b=Path(td);(b/'tags.c').write_text(source)
        run('clang','--target=arm-none-eabi','-mcpu=cortex-m3','-mthumb','-Oz','-ffreestanding','-fno-builtin','-ffunction-sections','-fdata-sections','-c',str(b/'tags.c'),'-o',str(b/'tags.o'))
        sections=[]
        for i,(name,entry) in enumerate(layout.items()):
            addr=SCRATCH if name=='.text.utf16' else entry['address']
            sections.append(f'.p{i} {addr:#x} : {{ *({name}) }}')
        (b/'tags.ld').write_text('SECTIONS {\n'+'\n'.join(sections)+'\n/DISCARD/ : { *(.ARM*) *(.comment) *(.note*) }\n}')
        run('ld.lld','-T',str(b/'tags.ld'),str(b/'tags.o'),'-o',str(b/'tags.elf'))
        overrides=[];size=0
        for i,(name,entry) in enumerate(layout.items()):
            out=b/f'{i}.bin';run('llvm-objcopy','-O','binary','-j',f'.p{i}',str(b/'tags.elf'),str(out))
            code=out.read_bytes()
            if name=='.text.utf16':size=len(code);addr=SCRATCH
            else:
                assert len(code)==entry['bytes'],(name,len(code),entry['bytes'])
                addr=entry['address']
            overrides.append((addr,code))
        # Retain every original caller and redirect the former function entry.
        overrides.append((layout['.text.utf16']['address'],branch(layout['.text.utf16']['address'],SCRATCH)))
        return overrides,size

def check(raw):
    assert hashlib.sha256(raw).hexdigest()==BASELINE
    overrides,size=prototype()
    fixtures=[('ascii',opus([('TITLE','A long ASCII title '*12),('ARTIST','Artist'),('ALBUM','Album'),('GENRE','Genre')])),
              ('unicode',opus([('TITLE','Title 音楽 🎵'),('ARTIST','Beyonce\u0301'),('ALBUM','Album'),('GENRE','Genre')])),
              ('unicode-only',opus([('TITLE','\u97f3\u697d'*60)])),
              ('boundary-surrogate',opus([('TITLE','x'*125+'\U0001f3b5')])),
              ('embedded-nul',opus([('TITLE','Before\0After')])),
              ('long',opus([('TITLE','x'*600)])),
              ('large-art',opus([('TITLE','Title'),('METADATA_BLOCK_PICTURE','x'*70000),('ARTIST','Artist')]))]
    # Invalid UTF-8 and packet truncation use raw comment bytes.
    import struct
    head=b'OpusHead'+bytes([1,2])+bytes(9)
    for name,value in [('invalid',b'\xff\xc0\xaf\xe2x'),('truncated-utf8',b'\xf0\x9f')]:
        comment=b'TITLE='+value
        fixtures.append((name,ogg([head,b'OpusTags'+struct.pack('<III',0,1,len(comment))+comment])))
    fixtures += [('truncated-page',fixtures[1][1][:-1]),('empty',opus([]))]
    rows=[]
    for name,data in fixtures:
        before={};after={}
        a=parse(data,raw=raw,apply_patches=False,native_fs=True,metrics=before)
        b=parse(data,raw=raw,apply_patches=False,native_fs=True,metrics=after,code_overrides=overrides)
        assert a==b and before['record_sha256']==after['record_sha256'],name
        assert before['file_read_calls']==after['file_read_calls'] and before['sector_read_calls']==after['sector_read_calls'],name
        rows.append(dict(case=name,baseline_instructions=before['instructions'],prototype_instructions=after['instructions'],record_identical=True,file_reads=after['file_read_calls'],sector_reads=after['sector_read_calls']))
    assert rows[0]['prototype_instructions']<rows[0]['baseline_instructions']
    return dict(cases=len(rows),record_bytes_per_case=0x556,utf16_code_bytes=size,qualified_code_home=False,release_image_modified=False,results=rows)

if __name__=='__main__':
    print(json.dumps(check((ROOT/'release/DP3_V137_CE.img').read_bytes()),indent=2))
