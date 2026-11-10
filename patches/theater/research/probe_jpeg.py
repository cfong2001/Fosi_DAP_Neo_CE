#!/usr/bin/env python3
"""Decode a generated 30x18 JPEG using stock module 19 under Unicorn.

The fixture has six red rows above twelve blue rows. Only the file-read
callback is modeled; code, metadata helper and decoder are stock bytes.
This is a bounded regression fixture, not evidence of real-card I/O.
"""
import base64
import hashlib
import os
from pathlib import Path
import struct
import sys
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
    UC_ARM_REG_R3, UC_ARM_REG_PC, UC_ARM_REG_SP, UC_ARM_REG_LR)

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image

# Original generated fixture, quality 100, 4:4:4, red top six rows.
JPEG = base64.b64decode("/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAASAB4DAREAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD8Af8AhfPwo/6Gr/yh+JP/AJT1n/xRL/adf9Izf+dm+j7/APTXP+tD/ir3+zt/6SF/85N44/8A0sw/4Xz8KP8Aoav/ACh+JP8A5T0f8US/2nX/AEjN/wCdm+j7/wDTXD/ir3+zt/6SF/8AOTeOP/0sw/4Xz8KP+hq/8ofiT/5T0f8AFEv9p1/0jN/52b6Pv/01w/4q9/s7f+khf/OTeOP/ANLMP+F8/Cj/AKGr/wAofiT/AOU9H/FEv9p1/wBIzf8AnZvo+/8A01w/4q9/s7f+khf/ADk3jj/9LM/OWv8Av8P+IcKACgAoAKACgAoAKAP/2Q==")
EXPECTED = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
raw = Path(os.environ.get('FOSI_STOCK_IMAGE', ROOT / 'DP3_V137.img')).read_bytes()
assert hashlib.sha256(raw).hexdigest() == EXPECTED
im = Image(raw)
u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
u.mem_map(0x03000000, 0x100000)
for module in (0, 18, 19):
    m = im.modules[module]
    for kind in ('code', 'data'):
        off, size = im.module_region(module, kind)
        if size:
            u.mem_write(m[kind + '_exec'], raw[off:off + size])

def w32(addr, value):
    u.mem_write(addr, struct.pack('<I', value))

def r32(addr):
    return struct.unpack('<I', u.mem_read(addr, 4))[0]

ctx, row, callback, end = 0x030282A8, 0x03027DA8, 0x030E0000, 0x030EF000
w32(0x03025944, 1)       # fake file handle
w32(0x0302598C, 30)      # desired display dimensions
w32(0x03025990, 18)
w32(0x03025948, callback | 1)
cursor = 0
reads = []
writes = []
def intercept(uc, addr, size, user):
    global cursor
    if addr == callback:
        dest, count, handle = (uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2))
        assert handle == 1 and count <= 4096
        block = JPEG[cursor:cursor + count]
        cursor += len(block)
        if block:
            uc.mem_write(dest, block)
        reads.append((count, len(block)))
        uc.reg_write(UC_ARM_REG_R0, len(block))
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    elif addr == 0x030878AC:
        # Store base and index; capture the location before the STRH.
        writes.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R11)))

# r11 is Thumb fp in the output store.
from unicorn.arm_const import UC_ARM_REG_R11
u.hook_add(UC_HOOK_CODE, intercept)
def call(command):
    for reg, val in ((UC_ARM_REG_R0, command), (UC_ARM_REG_R1, 0),
                     (UC_ARM_REG_R2, 0), (UC_ARM_REG_R3, 0),
                     (UC_ARM_REG_SP, 0x030F0000), (UC_ARM_REG_LR, end | 1)):
        u.reg_write(reg, val)
    u.emu_start(0x03085A4D, end, count=5000000)
    assert u.reg_read(UC_ARM_REG_PC) == end, 'instruction limit or unexpected return'
    return u.reg_read(UC_ARM_REG_R0)

assert call(9) == 1
assert reads and cursor == len(JPEG)
assert (r32(ctx + 0x0C), r32(ctx + 0x10)) == (30, 18)
rows = []
for y in range(18):
    assert call(11) == (1 if y < 17 else 0)
    assert r32(ctx + 0x24) == y + 1
    rows.append(struct.unpack('<30H', u.mem_read(row, 60)))
assert writes == [(row, x) for x in range(30)] * 18

def sum_red_blue(group):
    red = sum(((w >> 11) & 31) for line in group for w in line)
    blue = sum((w & 31) for line in group for w in line)
    return red, blue
red, top_blue = sum_red_blue(rows[:6])
bottom_red, blue = sum_red_blue(rows[6:])
assert red > 4 * top_blue, (red, top_blue)
assert blue > 4 * bottom_red, (bottom_red, blue)
print('PASS: stock JPEG decode, non-square dimensions, row reuse, upper-third color and completion')

# Repeat the same fixture with a square target. The context carries both
# target and scaled-art dimensions; all target-height calls reach STRH.
u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
u.mem_map(0x03000000, 0x100000)
for module in (0, 18, 19):
    m = im.modules[module]
    for kind in ('code', 'data'):
        off, size = im.module_region(module, kind)
        if size:
            u.mem_write(m[kind + '_exec'], raw[off:off + size])
cursor = 0
reads.clear(); writes.clear()
w32(0x03025944, 1)
w32(0x0302598C, 16)
w32(0x03025990, 16)
w32(0x03025948, callback | 1)
u.hook_add(UC_HOOK_CODE, intercept)
assert call(9) == 1
assert tuple(r32(ctx + i) for i in (0x0C, 0x10, 0x14, 0x18, 0x2C)) == (16, 16, 16, 9, 3)
for y in range(16):
    assert call(11) == (1 if y < 15 else 0)
    assert r32(ctx + 0x24) == y + 1
assert writes == [(row, x) for x in range(16)] * 16
print('PASS: scaled target exposes distinct geometry and writes each target row')
