#!/usr/bin/env python3
"""Read-only RKnano module, resource and firmware integrity inspector.

Only uses the Python standard library. ELF output contains original code and
load addresses; it does not implement the device's loader or flash updater.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

FIELDS = ('code_load', 'code_exec', 'code_len', 'data_load', 'data_exec',
          'data_len', 'bss_exec', 'bss_len')
SECTIONS = {'sysdefault': (0x70, None), 'font_a': (0x78, 0x7c),
            'font_b': (0x80, 0x84), 'codepage': (0xcc, 0xd0),
            'lang': (0xf8, 0xfc), 'images': (0x14c, 0x150)}


def rk_crc32(data):
    """MSB-first non-reflected Rockchip CRC32, polynomial 0x04c10db7, init 0."""
    table = []
    for n in range(256):
        v = n << 24
        for _ in range(8):
            v = ((v << 1) ^ (0x04c10db7 if v & 0x80000000 else 0)) & 0xffffffff
        table.append(v)
    crc = 0
    for b in data:
        crc = ((crc << 8) & 0xffffffff) ^ table[((crc >> 24) ^ b) & 255]
    return crc


class Image:
    def __init__(self, raw):
        self.raw = raw
        if len(raw) < 0x400 or raw[0x10:0x18] != b'Rockchip' or raw[0x1f8:0x200] != b'RKnanoFW':
            raise ValueError('not an RKnanoFW image')
        self.base = self.u32(0x200)
        count = self.u32(0x204)
        if count > 4096 or 0x208 + count * 32 > len(raw):
            raise ValueError('invalid module table size')
        self.modules = [dict(index=i, **dict(zip(FIELDS,
                        struct.unpack_from('<8I', raw, 0x208 + i*32))))
                        for i in range(count)]
        self.sections = {}
        for name, (off_pos, len_pos) in SECTIONS.items():
            start = self.u32(off_pos)
            length = (self.u32(0x78) - start) if len_pos is None else self.u32(len_pos)
            if start + length > len(raw):
                raise ValueError(f'{name} section outside image')
            self.sections[name] = {'offset': start, 'length': length}

    def u32(self, offset):
        return struct.unpack_from('<I', self.raw, offset)[0]

    def file_offset(self, load_addr):
        return load_addr - self.base + 0x200

    def module_region(self, index, kind):
        m = self.modules[index]
        length = m[kind + '_len']
        off = self.file_offset(m[kind + '_load'])
        if length and (off < 0 or off + length > len(self.raw)):
            raise ValueError(f'module {index} {kind} outside image')
        return off, length

    def summary(self):
        fw_len = self.u32(0x1f4)
        trailer = self.u32(len(self.raw)-4)
        crc = rk_crc32(self.raw[:-4])
        return {'file_length': len(self.raw), 'sha256': hashlib.sha256(self.raw).hexdigest(),
                'build_date_bcd': self.raw[:4].hex(),
                'image_length_field': fw_len, 'header_mirror_valid':
                self.raw[:0x200] == self.raw[fw_len:fw_len+0x200],
                'stored_crc32': f'{trailer:08x}', 'computed_crc32': f'{crc:08x}',
                'crc_valid': trailer == crc, 'module_load_base': self.base,
                'module_count': len(self.modules), 'sections': self.sections}

    def images(self):
        s = self.sections['images']
        start = s['offset']
        if self.raw[start:start+16] != b'ROCK26IMAGERES  ':
            raise ValueError('invalid image resource signature')
        n = self.u32(start+16)
        if 0x20 + n*16 > s['length']:
            raise ValueError('invalid image resource count')
        for i in range(n):
            w,h,x,y,size,offset = struct.unpack_from('<4H2I',self.raw,start+0x20+i*16)
            if offset+size > s['length']:
                raise ValueError(f'image #{i} outside section')
            yield {'id': i, 'width': w, 'height': h, 'x': x, 'y': y,
                   'data_offset': start+offset, 'size': size,
                   'rgb565_bytes': w*h*2 == size}

    def lang(self, language):
        s=self.sections['lang']; start=s['offset']
        n=struct.unpack_from('<H',self.raw,start)[0]
        if not 0 <= language < n:
            raise ValueError(f'language must be from 0 to {n-1}')
        offsets=[self.u32(start+2+i*4) for i in range(n)]
        end=offsets[language+1] if language<n-1 else s['length']
        stride=258
        if (end-offsets[language]) % stride:
            raise ValueError('unknown language slot stride')
        for i in range((end-offsets[language])//stride):
            off=start+offsets[language]+i*stride
            sid=struct.unpack_from('<H',self.raw,off)[0]
            if sid != i:
                raise ValueError(f'language {language} id mismatch in slot {i}')
            txt=self.raw[off+58:off+stride].decode('utf-16le',errors='replace').split('\0',1)[0]
            yield {'id':sid,'text':txt,'file_offset':off+58}

    def extract(self, root):
        root.mkdir(parents=True,exist_ok=True)
        manifest={'source': self.summary(), 'modules': [], 'images': list(self.images())}
        for m in self.modules:
            entry=m.copy()
            for kind in ('code','data'):
                off, size=self.module_region(m['index'],kind)
                if size:
                    dest=f'module_{m["index"]:02}_{kind}_{m[kind+"_exec"]:08x}.bin'
                    (root/dest).write_bytes(self.raw[off:off+size])
                    entry[kind+'_file']=dest
                    entry[kind+'_file_offset']=off
            manifest['modules'].append(entry)
        (root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


def _align(value, boundary=4):
    return (value+boundary-1)//boundary*boundary


def module_elf(image, index, dest):
    """Emit ELF32/ARM LE segments and a Thumb mapping symbol for Ghidra/LLVM."""
    m=image.modules[index]
    co,cl=image.module_region(index,'code')
    da,dl=image.module_region(index,'data')
    if not cl or not m['code_exec']:
        raise ValueError('module has no executable region with known load address')
    code=image.raw[co:co+cl]
    data=image.raw[da:da+dl] if dl else b''
    names=['', '.text']
    if dl:names.append('.data')
    if m['bss_len']:names.append('.bss')
    names += ['.symtab','.strtab','.shstrtab']
    ids={x:i for i,x in enumerate(names)}
    shstr=b'\0';names_off={}
    for name in names[1:]: names_off[name]=len(shstr);shstr+=name.encode()+b'\0'
    strtab=b'\0$t\0_start\0'
    symbols=[bytes(16), struct.pack('<IIIBBH',1,m['code_exec'],0,0,0,ids['.text']),
             struct.pack('<IIIBBH',4,m['code_exec']|1,cl,0x12,0,ids['.text'])]
    symtab=b''.join(symbols)
    chunks={'.text':code,'.strtab':strtab,'.symtab':symtab,'.shstrtab':shstr}
    if dl:chunks['.data']=data
    # File structure: ELF header, PT_LOADs, sections, section headers.
    nph=1+bool(dl)+bool(m['bss_len'])
    payload=bytearray(b'\0'*(52+32*nph)); offsets={}
    for name in names[1:]:
        if name=='.bss':continue
        payload.extend(b'\0'*(_align(len(payload))-len(payload)))
        offsets[name]=len(payload)
        payload.extend(chunks[name])
    payload.extend(b'\0'*(_align(len(payload))-len(payload)))
    shoff=len(payload)
    payload.extend(bytes(40))
    for name in names[1:]:
        typ=8 if name=='.bss' else (2 if name=='.symtab' else 3 if name in ('.strtab','.shstrtab') else 1)
        flags=6 if name=='.text' else (3 if name in ('.data','.bss') else 0)
        addr=(m['code_exec'] if name=='.text' else m['data_exec'] if name=='.data' else m['bss_exec'] if name=='.bss' else 0)
        size=(m['bss_len'] if name=='.bss' else len(chunks[name]))
        link=ids['.strtab'] if name=='.symtab' else 0
        info=2 if name=='.symtab' else 0
        entsize=16 if name=='.symtab' else 0
        payload.extend(struct.pack('<IIIIIIIIII',names_off[name],typ,flags,addr,offsets.get(name,0),size,link,info,4 if name not in ('.strtab','.shstrtab') else 1,entsize))
    # ELF header and program headers, including zero-filled BSS.
    vector=struct.unpack_from('<I',code,4)[0] if cl>=8 else m['code_exec']|1
    entry=(vector if m['code_exec'] <= (vector&~1) < m['code_exec']+cl else m['code_exec']|1)
    payload[:52]=struct.pack('<16sHHIIIIIHHHHHH',b'\x7fELF\x01\x01\x01'+bytes(9),2,40,1,entry,52,shoff,0x5000000,52,32,nph,40,len(names),ids['.shstrtab'])
    segs=[('.text',m['code_exec'],cl,cl,5)]
    if dl:segs.append(('.data',m['data_exec'],dl,dl,6))
    if m['bss_len']:segs.append(('.bss',m['bss_exec'],0,m['bss_len'],6))
    for j,(name,vma,filesz,memsz,flags) in enumerate(segs):
        p_offset=offsets.get(name,0)
        struct.pack_into('<IIIIIIII',payload,52+32*j,1,p_offset,vma,vma,filesz,memsz,flags,4)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(payload)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('image',type=Path)
    sub=ap.add_subparsers(dest='action',required=True)
    sub.add_parser('info')
    p=sub.add_parser('unpack');p.add_argument('directory',type=Path)
    p=sub.add_parser('elf');p.add_argument('module',type=int);p.add_argument('output',type=Path)
    p=sub.add_parser('lang');p.add_argument('language',type=int)
    sub.add_parser('images')
    a=ap.parse_args();im=Image(a.image.read_bytes())
    if a.action=='info': print(json.dumps(im.summary(),indent=2))
    if a.action=='unpack': im.extract(a.directory)
    if a.action=='elf':module_elf(im,a.module,a.output)
    if a.action=='lang':print(json.dumps(list(im.lang(a.language)),ensure_ascii=False,indent=2))
    if a.action=='images':print(json.dumps(list(im.images()),indent=2))


if __name__=='__main__':main()
