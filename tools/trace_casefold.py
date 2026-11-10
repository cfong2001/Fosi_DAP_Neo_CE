#!/usr/bin/env python3
"""Execute two original Thumb-2 leaf routines from module 39 in a strict CPU subset.

No source reimplementation is used to produce the result: instructions are
fetched from the stock image and decoded one by one. Unknown opcodes abort.
Hardware/RTOS behavior is intentionally out of scope for this emulator.
"""
import argparse
import struct
from rknano_image import Image

# Addresses are valid only for the SHA256-identified DP3_V137.img release.
SHA256 = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
ENTRY_UPPER = 0x0307d5fc
ENTRY_CMP = 0x0307d608
MASK = 0xffffffff


def signed(v):
    v &= MASK
    return v-0x100000000 if v & 0x80000000 else v


def execute(img, address, a, b=0, trace=False):
    m = img.modules[39]
    if not m['code_exec'] <= address < m['code_exec']+m['code_len']:
        raise ValueError('entry outside module 39')
    file_start, _ = img.module_region(39, 'code')
    regs=[0]*16
    regs[0],regs[1],regs[14]=a&MASK,b&MASK,0xffffffff
    pc=address
    carry=zero=False
    it_condition=None
    lines=[]
    for _ in range(40):
        off=file_start+(pc-m['code_exec'])
        hw=struct.unpack_from('<H',img.raw,off)[0]
        cond = (not carry or zero) if it_condition == 'ls' else True
        in_it=it_condition is not None
        it_condition=None
        before=pc
        pc+=2
        if (hw & 0xfff0)==0xf1a0:  # SUB.W Rd,Rn,#imm12
            hw2=struct.unpack_from('<H',img.raw,off+2)[0]
            rd=(hw2>>8)&15;rn=hw&15
            imm=((hw>>10)&1)<<11 | ((hw2>>12)&7)<<8 | (hw2&255)
            if cond:regs[rd]=(regs[rn]-imm)&MASK
            pc+=2
            op=f'sub.w r{rd},r{rn},#{imm}'
        elif hw&0xf800==0x2800:  # CMP immediate
            rn=(hw>>8)&7;imm=hw&255
            if cond:
                zero=regs[rn]==imm
                carry=regs[rn]>=imm
            op=f'cmp r{rn},#{imm}'
        elif hw==0xbf98:  # IT LS (only supported IT encoding)
            it_condition='ls'
            op='it ls'
        elif hw&0xf800==0x3800:  # SUB immediate (does not set flags in IT)
            rd=(hw>>8)&7;imm=hw&255
            if cond:
                lhs=regs[rd]
                regs[rd]=(lhs-imm)&MASK
                if not in_it:
                    zero=regs[rd]==0
                    carry=lhs>=imm
            op=f'sub r{rd},#{imm}'
        elif hw&0xfe00==0x1a00:  # SUBS register
            rm=(hw>>6)&7;rn=(hw>>3)&7;rd=hw&7
            if cond:
                lhs=regs[rn];rhs=regs[rm]
                regs[rd]=(lhs-rhs)&MASK
                zero=regs[rd]==0
                carry=lhs>=rhs
            op=f'subs r{rd},r{rn},r{rm}'
        elif hw==0x4770:  # BX LR
            op='bx lr'
            if trace:lines.append(f'{before:08x} {hw:04x} {op:22s} r0={signed(regs[0]):+d} r1={signed(regs[1]):+d} C={int(carry)} Z={int(zero)}')
            return signed(regs[0]),lines
        else:
            raise ValueError(f'unimplemented Thumb opcode 0x{hw:04x} at 0x{before:08x}')
        if trace:lines.append(f'{before:08x} {hw:04x} {op:22s} r0={signed(regs[0]):+d} r1={signed(regs[1]):+d} C={int(carry)} Z={int(zero)}')
    raise RuntimeError('execution step limit reached')


def selfcheck(img):
    upper=lambda c: c-32 if 97<=c<=122 else c
    for x in range(128):
        v,_=execute(img,ENTRY_UPPER,x)
        assert v==upper(x),(x,v)
        for y in range(128):
            v,_=execute(img,ENTRY_CMP,x,y)
            assert v==upper(x)-upper(y),(x,y,v)
    return 128+128*128


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('image')
    ap.add_argument('--verify',action='store_true',help='exhaustively test ASCII 0..127')
    ap.add_argument('--upper',type=lambda s:int(s,0),default=None)
    ap.add_argument('--compare',nargs=2,type=lambda s:int(s,0))
    ap.add_argument('--trace',action='store_true')
    a=ap.parse_args();img=Image(open(a.image,'rb').read())
    if img.summary()['sha256'] != SHA256:
        ap.error('release hash mismatch; code offsets are not safe for this build')
    if a.verify:print('PASS:',selfcheck(img),'machine-code executions')
    if a.upper is not None:
        v,t=execute(img,ENTRY_UPPER,a.upper,trace=a.trace)
        print(*t,sep='\n'); print('return:',v)
    if a.compare is not None:
        v,t=execute(img,ENTRY_CMP,*a.compare,trace=a.trace)
        print(*t,sep='\n'); print('return:',v)


if __name__=='__main__':main()
