#!/usr/bin/env python3
"""Execute the stock player artwork setup and row consumer with a JPEG fixture."""
from pathlib import Path
import runpy
import struct
import ctypes
import subprocess
import tempfile
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_PC, UC_ARM_REG_SP, UC_ARM_REG_LR

fixture = runpy.run_path(str(Path(__file__).resolve().parent / 'probe_jpeg.py'))
im, raw, jpeg = fixture['im'], fixture['raw'], fixture['JPEG']
class Average(ctypes.Structure):
    _fields_ = [('sum', ctypes.c_uint64 * 3), ('width', ctypes.c_uint32),
                ('rows_needed', ctypes.c_uint32), ('rows_seen', ctypes.c_uint32),
                ('big_endian', ctypes.c_int)]

tmp = tempfile.TemporaryDirectory()
source = Path(__file__).resolve().parent.parent / 'frame_average.c'
subprocess.run(['cc', '-shared', '-fPIC', '-o', str(Path(tmp.name) / 'avg.so'), str(source)], check=True)
avg = ctypes.CDLL(str(Path(tmp.name) / 'avg.so'))
avg.theater_top_init.argtypes = [ctypes.POINTER(Average), ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int]
avg.theater_top_row.argtypes = [ctypes.POINTER(Average), ctypes.c_void_p, ctypes.c_size_t]
avg.theater_top_finish.argtypes = [ctypes.POINTER(Average), ctypes.POINTER(ctypes.c_uint8)]
ctx, end = 0x03026CA0, 0x030EF000


def exercise(width, height, expected_height):
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x03000000, 0x100000)
    for module in (0, 18, 19):
        m = im.modules[module]
        for kind in ('code', 'data'):
            off, size = im.module_region(module, kind)
            if size:
                u.mem_write(m[kind + '_exec'], raw[off:off + size])
    def w32(addr, val): u.mem_write(addr, struct.pack('<I', val))
    def r32(addr): return struct.unpack('<I', u.mem_read(addr, 4))[0]
    for addr, val in ((0x0302598C, width), (0x03025990, height),
                      (0x03025994, 23), (0x03025998, 36), (0x030259DC, 1)):
        w32(addr, val)
    cursor, blits = 0, []
    def hook(uc, addr, size, user):
        nonlocal cursor
        if addr == 0x03058FA8:
            dest, count, handle = (uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2))
            assert handle == 1 and count <= 4096
            block = jpeg[cursor:cursor + count]
            cursor += len(block)
            if block: uc.mem_write(dest, block)
            uc.reg_write(UC_ARM_REG_R0, len(block))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif addr == 0x03067870:
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif addr == 0x0306333E:
            args = [uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]
            mode, ptr = struct.unpack('<II', uc.mem_read(uc.reg_read(UC_ARM_REG_SP), 8))
            blits.append((args, mode, ptr, struct.unpack('<%dH' % width, uc.mem_read(ptr, width * 2))))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    u.hook_add(UC_HOOK_CODE, hook)
    def call(addr, r0=0, r1=0):
        for reg, value in ((UC_ARM_REG_R0, r0), (UC_ARM_REG_R1, r1), (UC_ARM_REG_R2, 0), (UC_ARM_REG_R3, 0), (UC_ARM_REG_SP, 0x030F0000), (UC_ARM_REG_LR, end | 1)):
            u.reg_write(reg, value)
        u.emu_start(addr | 1, end, count=5000000)
        assert u.reg_read(UC_ARM_REG_PC) == end, 'instruction limit or unexpected return'
        return u.reg_read(UC_ARM_REG_R0)
    assert call(0x0308389E, 1, 0) == 1
    assert r32(ctx + 0x28) == 0x03026A20
    assert r32(ctx + 0x18) == expected_height
    assert r32(ctx + 0x2c) == 0
    returns = [call(0x03083B36) for _ in range(expected_height)]
    assert len(blits) == expected_height, (returns, len(blits))
    assert all(a == [23, 36 + y, width, 1] and mode == 0x10 and ptr == 0x03026A20 for y, (a, mode, ptr, _) in enumerate(blits)), blits
    top = [p for _, _, _, row in blits[:expected_height // 3] for p in row]
    red = sum((p >> 11) & 31 for p in top)
    blue = sum(p & 31 for p in top)
    assert red > 4 * blue, (red, blue)
    state = Average()
    assert avg.theater_top_init(ctypes.byref(state), width, expected_height, 0)
    for _, _, _, pixels in blits[:state.rows_needed]:
        data = struct.pack('<%dH' % width, *pixels)
        assert avg.theater_top_row(ctypes.byref(state), data, len(data))
    rgb = (ctypes.c_uint8 * 3)()
    assert avg.theater_top_finish(ctypes.byref(state), rgb)
    assert rgb[0] > 4 * rgb[2], tuple(rgb)
    print('host accumulator RGB:', tuple(rgb))
    before = len(blits)
    extra = call(0x03083B36)
    assert (extra, len(blits) - before) == ((1, 1) if height == 18 else (0, 0))
    print('extra call:', extra, 'additional blits:', len(blits) - before, 'cursor:', r32(ctx + 0x2c))
    print('PASS player', width, height, 'scaled rows', expected_height, 'returns', returns, 'top RGB565 red/blue sums', red, blue, 'cursor', r32(ctx + 0x2c))

exercise(30, 18, 18)
exercise(16, 16, 9)
