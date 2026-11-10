#!/usr/bin/env python3
"""TBB-aware per-module disassembler for the 0x0308c694 stub family.
Decodes TBB tables, disassembles each case block linearly from its entry,
resolves PC-relative literals against module code/data + module 0.
Usage: tbbdis.py MODULE_INDEX [START LENGTH]"""
import sys, struct, json, glob
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS

ROOT = '/home/hatch/workspace/fosi-dap-neo'
man = json.load(open(f'{ROOT}/extracted/manifest.json'))
mods = {m['index']: m for m in man['modules']}

def load(idx, kind):
    f = glob.glob(f'{ROOT}/extracted/module_{idx:02d}_{kind}_*.bin')
    return open(f[0], 'rb').read() if f else b''

def make_reader(idx):
    m = mods[idx]
    code, base = load(idx, 'code'), m['code_exec']
    data, dbase = load(idx, 'data'), m['data_exec']
    m0 = mods[0]
    segs = [(code, base), (data, dbase),
            (load(0, 'code'), m0['code_exec']), (load(0, 'data'), m0['data_exec'])]
    def read(addr, n):
        for buf, b in segs:
            if b <= addr < b + len(buf):
                return buf[addr - b: addr - b + n]
        return None
    return read, code, base

def main():
    idx = int(sys.argv[1])
    read, code, base = make_reader(idx)
    start = int(sys.argv[2], 0) if len(sys.argv) > 2 else base
    length = int(sys.argv[3], 0) if len(sys.argv) > 3 else len(code)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
    md.detail = False
    off = start - base
    chunk = code[off:off + length]
    addr = start
    end = start + len(chunk)
    while addr < end:
        o = addr - base
        got = list(md.disasm(chunk[o:o + 16], addr, count=1))
        if not got:
            print(f'{addr:08x}  {code[o]:02x} {code[o+1]:02x}        .byte?')
            addr += 2
            continue
        ins = got[0]
        note = ''
        if ins.mnemonic.startswith('ldr') and '[pc' in ins.op_str:
            try:
                imm = int(ins.op_str.split('#')[1].rstrip(']'), 0)
                litaddr = (ins.address + 4 & ~3) + imm
                val = read(litaddr, 4)
                if val:
                    note = f'  ; [{litaddr:#x}] = {struct.unpack("<I", val)[0]:#010x}'
            except Exception:
                pass
        print(f'{ins.address:08x}  {ins.bytes.hex(" "):<14} {ins.mnemonic:<8} {ins.op_str}{note}')
        if ins.mnemonic in ('tbb', 'tbh'):
            # table follows immediately; size unknown -- scan callsites hint
            tbl = ins.address + ins.size
            n = 16
            bytes_ = code[tbl - base: tbl - base + n]
            print(f'  TBB table at {tbl:#x}: {bytes_.hex()}')
            pc = ins.address + 4
            for i, b in enumerate(bytes_):
                print(f'    case {i}: -> {pc + 2*b:#010x}')
            addr = tbl + n
            continue
        addr += ins.size

if __name__ == '__main__':
    main()
