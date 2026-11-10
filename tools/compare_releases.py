#!/usr/bin/env python3
"""Compare RKnano firmware releases by logical modules, UI strings and image assets.

Read-only. Changed modules are leads, not proof of what a user-facing feature does.
"""
import argparse
import hashlib
import json
from pathlib import Path
from rknano_image import Image


def digest(data):
    return hashlib.sha256(data).hexdigest()


def spans(a, b, limit=80):
    if len(a)!=len(b):
        raise ValueError('same length required')
    runs=[];start=None
    for i,(x,y) in enumerate(zip(a,b)):
        if x!=y and start is None:start=i
        elif x==y and start is not None:
            runs.append((start,i));start=None
    if start is not None:runs.append((start,len(a)))
    return runs[:limit],sum(j-i for i,j in runs),max(0,len(runs)-limit),len(runs)


def modules(a,b):
    out=[]
    for idx in range(max(len(a.modules),len(b.modules))):
        if idx>=len(a.modules) or idx>=len(b.modules):
            out.append({'module':idx,'status':'added' if idx>=len(a.modules) else 'removed'})
            continue
        x,y=a.modules[idx],b.modules[idx];regions={}
        for kind in ('code','data'):
            o,n=a.module_region(idx,kind);p,t=b.module_region(idx,kind)
            xbytes=a.raw[o:o+n];ybytes=b.raw[p:p+t]
            addr=x[kind+'_exec'];newaddr=y[kind+'_exec']
            if xbytes==ybytes and addr==newaddr:continue
            rec={'old_size':n,'new_size':t,'old_exec':hex(addr),'new_exec':hex(newaddr),
                 'old_sha256':digest(xbytes),'new_sha256':digest(ybytes)}
            if n==t and addr==newaddr and addr:
                diffs,changed,truncated,nspans=spans(xbytes,ybytes)
                rec.update(changed_bytes=changed,span_count=nspans,truncated_spans=truncated,
                           spans=[{'cpu_start':hex(addr+i),'cpu_end_exclusive':hex(addr+j),
                                   'old_file_offset':hex(o+i),'new_file_offset':hex(p+i),
                                   'length':j-i} for i,j in diffs])
            else:rec['note']='relocated or resized: addresses cannot be paired by byte offset'
            regions[kind]=rec
        for key in ('bss_exec','bss_len'):
            if x[key]!=y[key]:regions[key]={'old':x[key],'new':y[key]}
        if regions:out.append({'module':idx,'status':'changed','regions':regions})
    return out


def languages(a,b):
    def count(im):
        off=im.sections['lang']['offset']
        return int.from_bytes(im.raw[off:off+2],'little')
    oldcount,newcount=count(a),count(b)
    changed=[]
    for idx in range(min(oldcount,newcount)):
        try:
            x={r['id']:r['text'] for r in a.lang(idx)}
            y={r['id']:r['text'] for r in b.lang(idx)}
        except ValueError as ex:
            changed.append({'language':idx,'error':str(ex)})
            continue
        for id_ in sorted(x.keys()|y.keys()):
            if x.get(id_)!=y.get(id_):
                changed.append({'language':idx,'string_id':id_,'old':x.get(id_),'new':y.get(id_)})
    return {'old_count':oldcount,'new_count':newcount,'changes':changed}


def assets(a,b):
    x=list(a.images());y=list(b.images());changed=[]
    for idx in range(max(len(x),len(y))):
        if idx>=len(x) or idx>=len(y):
            changed.append({'id':idx,'status':'added' if idx>=len(x) else 'removed'})
            continue
        old,new=x[idx],y[idx]
        dx=digest(a.raw[old['data_offset']:old['data_offset']+old['size']])
        dy=digest(b.raw[new['data_offset']:new['data_offset']+new['size']])
        dims=('width','height','x','y')
        if dx!=dy or any(old[k]!=new[k] for k in dims):
            changed.append({'id':idx,'old_geometry':{k:old[k] for k in dims},
                            'new_geometry':{k:new[k] for k in dims},
                            'old_sha256':dx,'new_sha256':dy})
    return {'old_count':len(x),'new_count':len(y),'changes':changed}


def compare(a,b):
    x=a.summary();y=b.summary()
    keys=('sha256','file_length','build_date_bcd','header_mirror_valid','crc_valid','module_count')
    return {'old':{k:x[k] for k in keys},'new':{k:y[k] for k in keys},
            'modules':modules(a,b),'languages':languages(a,b),'images':assets(a,b),
            'sections':{s:{'old_start':a.sections[s]['offset'],'new_start':b.sections[s]['offset'],
                            'old_size':a.sections[s]['length'],'new_size':b.sections[s]['length'],
                            'unchanged':a.raw[a.sections[s]['offset']:a.sections[s]['offset']+a.sections[s]['length']]==b.raw[b.sections[s]['offset']:b.sections[s]['offset']+b.sections[s]['length']]}
                        for s in a.sections}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('old_image',type=Path)
    p.add_argument('new_image',type=Path)
    p.add_argument('--output',type=Path)
    args=p.parse_args()
    result=compare(Image(args.old_image.read_bytes()),Image(args.new_image.read_bytes()))
    data=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
    if args.output:args.output.write_text(data)
    else:print(data,end='')


if __name__=='__main__':
    main()
