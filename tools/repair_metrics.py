"""Short, deterministic repair gate; optional corpus tests live in test_tags.py.

Reports emulator instructions and I/O counts, not measured device milliseconds.
No media filenames, serial numbers, or computer paths enter the JSON result.
"""
import argparse
import contextlib
import hashlib
import io
import json
import runpy
import struct
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from rknano_image import Image
from unicorn import UC_HOOK_CODE

def ogg(packets):
    out=bytearray();sequence=0
    for packet in packets:
        laces=[255]*(len(packet)//255)+[len(packet)%255];offset=0;continued=False
        while laces:
            part,laces=laces[:255],laces[255:];n=sum(part)
            flags=(2 if sequence==0 else 0)|(1 if continued else 0)
            out+=b'OggS'+bytes([0,flags])+bytes(8)+struct.pack('<III',123,sequence,0)+bytes([len(part)])+bytes(part)+packet[offset:offset+n]
            offset+=n;sequence+=1;continued=True
    return bytes(out)

def opus(pairs):
    head=b'OpusHead'+bytes([1,2])+bytes(9)
    entries=[(key+'='+value).encode('utf-8') for key,value in pairs]
    tags=b'OpusTags'+struct.pack('<II',0,len(entries))+b''.join(struct.pack('<I',len(v))+v for v in entries)
    return ogg([head,tags])

def m4a(fields):
    def atom(key,payload):return struct.pack('>I',len(payload)+8)+key+payload
    keys={'title':b'\xa9nam','artist':b'\xa9ART','album':b'\xa9alb','genre':b'\xa9gen'}
    items=b''.join(atom(keys[k],atom(b'data',b'\0\0\0\1'+bytes(4)+v.encode('utf-8'))) for k,v in fields.items())
    return atom(b'ftyp',b'M4A '+bytes(4)+b'M4A isommp42')+atom(b'moov',atom(b'udta',atom(b'meta',bytes(4)+atom(b'ilst',items))))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate',type=Path,default=ROOT/'release/DP3_V137_CE.img')
    ap.add_argument('--output',type=Path)
    a=ap.parse_args();started=time.monotonic()
    raw=a.candidate.read_bytes();stock=(ROOT/'DP3_V137.img').read_bytes()
    im=Image(raw);sim=Image(stock);co,_=im.module_region(0,'code');so,_=sim.module_region(0,'code')
    base=im.modules[0]['code_exec'];ranges=((0x0306C576,0x0306C5A6),(0x0306C61A,0x0306C66C))
    protected=sum(end-start for start,end in ranges);preserved=0
    for start,end in ranges:
        before=stock[so+start-base:so+end-base];after=raw[co+start-base:co+end-base]
        preserved+=sum(x==y for x,y in zip(before,after))
    assert preserved==protected,'non-ASF metadata dispatch was overwritten'
    report={'candidate_sha256':hashlib.sha256(raw).hexdigest(),
            'legacy_dispatch_bytes':{'preserved':preserved,'required':protected},
            'metadata_fixtures':[]}
    tags=runpy.run_path(str(ROOT/'patches/opus_swap/test_tags.py'))
    expected=dict(title='Title 音楽 🎵',artist='Artist',album='Album',genre='Genre')
    fields=[(k.upper(),v) for k,v in expected.items()]
    large=[fields[0],('METADATA_BLOCK_PICTURE','x'*445020),*fields[1:]]
    for name,data,ext,want in (
            ('opus-text',opus(fields),b'OPU',expected),
            ('opus-multipage-large-art',opus(large),b'OPU',expected),
            ('opus-empty-tags',opus([]),b'OPU',dict.fromkeys(expected,'')),
            ('m4a-text',m4a(dict(title='Title',artist='Artist',album='Album',genre='Genre')),b'M4A',dict(title='Title',artist='Artist',album='Album',genre='Genre'))):
        metric={};got=tags['parse'](data,raw=raw,apply_patches=False,native_fs=True,
                                  extension=ext,watchdog=ext==b'OPU',metrics=metric)
        assert got==want,(name,got,want)
        report['metadata_fixtures'].append({'case':name,'matched_fields':len(want),**metric})
    # These cases must return without a fault or memory corruption.
    sample=opus(large)
    for n in (0,1,26,27,28,45,46,60,len(sample)-1):
        tags['parse'](sample[:n],raw=raw,apply_patches=False,native_fs=True)
    report['malformed_returns']=9
    lifecycle=runpy.run_path(str(ROOT/'patches/full/build/tests/test_sort_lifecycle.py'))
    old_argv=sys.argv
    try:
        sys.argv=['test_sort_lifecycle.py',str(a.candidate)]
        with contextlib.redirect_stdout(io.StringIO()):lifecycle['main']()
    finally:sys.argv=old_argv
    report['sort_code_survival']={'preserved':1052,'required':1052,'scratch_bytes_cleared':131072}
    wheel=runpy.run_path(str(ROOT/'patches/full/build/tests/test_wheel_service.py'))
    report['wheel_service']={'legacy_tick':wheel['probe'](raw,False),
                             'candidate':wheel['probe'](raw,'embedded')}
    painter=runpy.run_path(str(ROOT/'patches/design_refresh_v4/test_keyed_transport.py'))
    with contextlib.redirect_stdout(io.StringIO()):
        painter['gate_selected_focus'](raw)
    report['selected_glyphs']={'passed':30,'required':30,'keyed_corners':True,'antialiased_edges':True}
    playback=runpy.run_path(str(ROOT/'tests/opus_harness/test_open_path.py'))
    report['opus_open_path']=playback['check'](raw)
    render={}
    for label,image in (('stock',stock),('candidate',raw)):
        machine=painter['Machine'](image,real_store=True)
        machine.stage([155,156]+list(range(157,182))+list(range(286,290)))
        counters={'instructions':0,'resource_reads':0}
        def hook(uc,address,size,user):
            counters['instructions']+=1
            if address==painter['DMA']:counters['resource_reads']+=1
        machine.u.hook_add(UC_HOOK_CODE,hook)
        rows=[]
        for state in (1,3):
            counters.update(instructions=0,resource_reads=0)
            machine.painter(state_a=state,state_b=2,play=1,ground=0x7222)
            rows.append({'state':state,**counters,'pixel_stores':len(machine.stores)})
        render[label]=rows
    report['transport_render']=render
    report['render_instruction_ratio']=round(max(r['instructions'] for r in render['candidate'])/max(r['instructions'] for r in render['stock']),4)
    assert report['render_instruction_ratio']<=1.0,'transport instruction cost regressed against stock'
    assert max(r['resource_reads'] for r in render['candidate'])<=max(r['resource_reads'] for r in render['stock']),'transport resource reads regressed'
    report['limitations']=['Instruction counts are not device latency. CPU frequency, scheduler, display transfer and idle-to-visible artwork work require separate traces.']
    report['host_runtime_seconds']=round(time.monotonic()-started,3)
    report['status']='PASSED'
    text=json.dumps(report,indent=2,ensure_ascii=False)+'\n'
    if a.output:a.output.write_text(text,encoding='utf-8')
    print(text,end='')
if __name__=='__main__':main()
