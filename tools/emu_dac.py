#!/usr/bin/env python3
"""Execute the stock firmware's original dac_write/dac_read (module 0,
0x03060c4c / 0x03060d28) under Unicorn and capture the exact I2C frames
the original code builds for the CS43198.

Only the three bus-layer callees are stubbed (bus select/pinmux 0x0306021c,
I2C transfer 0x03060622, I2C read-phase 0x030608d0, bus release 0x0306043a);
each stub records its arguments and returns success. Everything else —
frame layout, the volume-register transform, the 0x05000a/b special cases,
the mute sentinel handling — is the original Thumb code executing.
"""
import sys, struct
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rknano_image import Image
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC

_img_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / 'DP3_V137.img'
IMG = Image(_img_path.read_bytes())
M0 = IMG.modules[0]
CODE_OFF, _ = IMG.module_region(0, 'code')
DATA_OFF, _ = IMG.module_region(0, 'data')
CODE = IMG.raw[CODE_OFF:CODE_OFF+M0['code_len']]
DATA = IMG.raw[DATA_OFF:DATA_OFF+M0['data_len']]

SENTINEL = 0x03050000  # first byte of module 0 code; returning here stops the run
STUBS = {0x0306021c: 'i2c_bus_select', 0x03060622: 'i2c_transfer',
         0x030608d0: 'i2c_read_phase', 0x0306043a: 'i2c_bus_release',
         0x0306d8f0: 'log_call'}
STATE_BYTE_ADDR = 0x030232a0 + 0x2e8   # volume/gain state read by dac_write
ERRBYTE_ADDR = 0x0300411d + 1          # dac_write/read error counter (<2 gate)

def make_uc(state_byte=0):
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
    uc.mem_map(0x03003000, 0x1000)                       # stack below SP
    uc.mem_map(0x03004000, 0x8000)                       # module 0 data + BSS start
    uc.mem_write(0x03004000, DATA)
    uc.mem_map(0x03020000, 0x8000)                       # persistent state region (zeroed)
    uc.mem_map(0x03050000, 0x2C000)                      # module 0 code
    uc.mem_write(0x03050000, CODE)
    uc.mem_write(STATE_BYTE_ADDR, bytes([state_byte]))
    uc.mem_write(ERRBYTE_ADDR, b'\0')
    return uc

def run(fn, r0, r1, state_byte=0):
    uc = make_uc(state_byte)
    calls = []
    def hook(uc, address, size, user):
        if address == SENTINEL:
            uc.emu_stop(); return
        name = STUBS.get(address)
        if name:
            a = [uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]
            rec = {'fn': name, 'r0': a[0], 'r1': a[1], 'r2': a[2], 'r3': a[3]}
            if name == 'i2c_transfer':
                n = 5 if a[3] == 5 else 4
                rec['frame'] = uc.mem_read(a[2], n).hex()
            calls.append(rec)
            uc.reg_write(UC_ARM_REG_R0, 0)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    uc.hook_add(UC_HOOK_CODE, hook)
    uc.reg_write(UC_ARM_REG_SP, 0x03004000)
    uc.reg_write(UC_ARM_REG_R0, r0)
    if isinstance(r1, int):
        uc.reg_write(UC_ARM_REG_R1, r1)
        outbuf = None
    else:
        outbuf = 0x03021000
        uc.mem_write(outbuf, b'\xAA')
        uc.reg_write(UC_ARM_REG_R1, outbuf)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL | 1)
    uc.emu_start(fn | 1, SENTINEL, count=200000)
    res = {'ret': uc.reg_read(UC_ARM_REG_R0), 'calls': calls}
    if outbuf:
        res['out_byte'] = uc.mem_read(outbuf, 1)[0]
    return res

def frames(res):
    return [c['frame'] for c in res['calls'] if c['fn'] == 'i2c_transfer']

if __name__ == '__main__':
    print('== plain register writes (state byte 0) ==')
    for mp, val in [(0x00020000, 0xF6), (0x000F0010, 0xE7), (0x00010010, 0x99), (0x00080032, 0x20)]:
        r = run(0x03060c4c, mp, val)
        print(f'dac_write(map={mp:#08x}, value={val:#04x}) -> frame {frames(r)} ret={r["ret"]:#x}')
    print('== channel config registers with mute sentinel 0xff ==')
    for mp in (0x0005000a, 0x0005000b):
        r = run(0x03060c4c, mp, 0xFF)
        print(f'dac_write(map={mp:#08x}, value=0xff) -> frame {frames(r)}')
    print('== PCM volume registers: value transform vs state byte ==')
    for st in (0, 6, 12):
        for mp, val in [(0x00090001, 0x78), (0x00090002, 0x78), (0x00090001, 0xFF)]:
            r = run(0x03060c4c, mp, val, state_byte=st)
            print(f'state={st:2d} dac_write(map={mp:#08x}, value={val:#04x}) -> frame {frames(r)}')
    print('== read path ==')
    r = run(0x03060d28, 0x000F0000, None)
    print(f'dac_read(map=0x000f0000) -> calls {[(c["fn"], c.get("frame")) for c in r["calls"]]} out={r.get("out_byte"):#04x}')
