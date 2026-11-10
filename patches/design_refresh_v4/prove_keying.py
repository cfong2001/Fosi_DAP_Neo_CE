#!/usr/bin/env python3
"""Emulation proof: which pixels does each stock draw path emit?

Runs the real module 0 draw code from the stock image under Unicorn.
The framebuffer store 0x03063E60 is intercepted at entry: the value in
r0 is recorded (that is the pixel the real code decided to write, in
raster order) and the call is skipped. Everything upstream of the
store (clip setup, staging copy, byte swap, blitter loops, key
compares) executes unmodified.

Paths exercised:
  A  blitter 0x0306333E mode 0x10 (the icon pipeline's leaf)
  B  blitter 0x0306333E mode 1, flags(+4) = 1 (text-style mask)
  C  blitter 0x0306333E mode 1, flags(+4) = 0
  D  blitter 0x0306333E mode 1, flags(+4) = 2
  E  keyblit 0x0306373C mode 0x10 format 0
  F  keyblit 0x0306373C mode 0x10 format 1
  G  keyblit 0x0306373C mode 0x10 format 2 (silhouette)
  H  DrawImage 0x03063700 on a synthetic resource (opaque pipeline)
  I  keyed helper 0x03063A08 on the same synthetic resource
  J  keyed helper 0x03063A08 on the real stock resource 286
  K  DrawImageAt 0x0306354A on the real stock resource 159
"""
import hashlib
import struct
import sys
from pathlib import Path

ROOT = Path('/home/hatch/workspace/fosi-dap-neo/repo-pr57')
WORK = Path('/home/hatch/workspace/fosi-dap-neo')
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image  # noqa: E402
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE  # noqa: E402
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,  # noqa: E402
                               UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR,
                               UC_ARM_REG_PC)

raw = (ROOT / 'DP3_V137.img').read_bytes()
assert hashlib.sha256(raw).hexdigest() == \
    'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
im = Image(raw)
EXT = WORK / 'extracted'
CODE = (EXT / 'module_00_code_03050000.bin').read_bytes()
DATA = (EXT / 'module_00_data_03004000.bin').read_bytes()
END = 0x030EF000
STORE = 0x03063E60
CTX = 0x0302385C          # display context: pens +0/+2, flags +4
RES_CELL = 0x0302328C     # resource section base pointer cell
SAVEINFO = 0x030232A0
PAL_FG = 0x030235B6       # palette cell 1 (foreground)

BITMAP = [0x0000, 0xF800, 0xFFFF, 0x1234, 0x07E0, 0x001F, 0xF81F, 0x8000]
SRC = 0x03090000
STACK = 0x030F0000


def make_uc():
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x03000000, 0x500000)
    # The firmware's copy helpers touch NVIC registers (critical
    # sections); give them a harmless scratch page.
    u.mem_map(0xE000E000, 0x1000)
    u.mem_write(0x03050000, CODE)
    u.mem_write(0x03004000, DATA)
    emitted = []

    def hook(uc, addr, size, user):
        if addr == STORE:
            emitted.append(uc.reg_read(UC_ARM_REG_R0) & 0xFFFF)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif addr == 0x03053F5E:
            # The firmware's copy primitive programs a DMA controller
            # (writes at 0x40180098); model its data effect, a plain
            # byte copy (src=r0, dst=r1, n=r2). All draw code runs
            # unmodified.
            src = uc.reg_read(UC_ARM_REG_R0)
            dst = uc.reg_read(UC_ARM_REG_R1)
            n = uc.reg_read(UC_ARM_REG_R2)
            if n:
                uc.mem_write(dst, bytes(uc.mem_read(src, n)))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    u.hook_add(UC_HOOK_CODE, hook)
    return u, emitted


def call(u, addr, r0=0, r1=0, r2=0, r3=0, stack=()):
    sp = STACK - 0x100
    for i, v in enumerate(stack):
        u.mem_write(sp + 4 * i, struct.pack('<I', v))
    for reg, val in ((UC_ARM_REG_R0, r0), (UC_ARM_REG_R1, r1),
                     (UC_ARM_REG_R2, r2), (UC_ARM_REG_R3, r3),
                     (UC_ARM_REG_SP, sp), (UC_ARM_REG_LR, END | 1)):
        u.reg_write(reg, val)
    u.emu_start(addr | 1, END, count=20000000)
    assert u.reg_read(UC_ARM_REG_PC) == END, \
        f'call to {addr:#x} did not return (pc={u.reg_read(UC_ARM_REG_PC):#x})'


def put_bitmap(u, values, addr=SRC):
    u.mem_write(addr, struct.pack(f'<{len(values)}H', *values))


def fmt(vals):
    return '[' + ', '.join(f'{v:#06x}' for v in vals) + ']'


results = []

# --- A: blitter mode 0x10 -------------------------------------------------
u, em = make_uc()
put_bitmap(u, BITMAP)
call(u, 0x0306333E, 10, 20, 4, 2, stack=(0x10, SRC))
ok = em == BITMAP
results.append(('A blitter mode 0x10', ok, f'emitted {fmt(em)}'))

# --- B/C/D: blitter mode 1 with flags 1 / 0 / 2 ---------------------------
for flags, want, name in (
        (1, [0xAAAA] * 3, 'B blitter mode 1 flags=1'),
        (0, [0xAAAA, 0x5555, 0xAAAA, 0xAAAA, 0x5555, 0x5555, 0x5555, 0x5555],
         'C blitter mode 1 flags=0'),
        (2, [0x5555, 0xAAAA, 0x5555, 0x5555, 0xAAAA, 0xAAAA, 0xAAAA, 0xAAAA],
         'D blitter mode 1 flags=2')):
    u, em = make_uc()
    u.mem_write(CTX + 0, struct.pack('<H', 0xAAAA))
    u.mem_write(CTX + 2, struct.pack('<H', 0x5555))
    u.mem_write(CTX + 4, struct.pack('<H', flags))
    put_bitmap(u, [0xB000])          # bits 1011 0000 in the top byte
    call(u, 0x0306333E, 10, 20, 8, 1, stack=(1, SRC))
    results.append((name, em == want, f'emitted {fmt(em)}'))

# --- E/F: keyblit formats 0 and 1 -----------------------------------------
# NOTE: the keyblit register convention is (x, y, x_end, y_end),
# inclusive, unlike the 0x0306333E blitter's (x, y, width, height).
# Format 0 keys on {0x0000, 0xF800}; format 1 keys on {0xF800} only
# (its pixel==0 test branches TO the store call at 0x030637EE).
for fmt_id, keys in ((0, (0x0000, 0xF800)), (1, (0xF800,))):
    u, em = make_uc()
    put_bitmap(u, BITMAP)
    call(u, 0x0306373C, 10, 20, 13, 21, stack=(0x10, SRC, fmt_id))
    want = [v for v in BITMAP if v not in keys]
    results.append((f'{"E" if fmt_id == 0 else "F"} keyblit format {fmt_id}',
                    em == want, f'emitted {fmt(em)}'))

# --- G: keyblit format 2 (silhouette) -------------------------------------
u, em = make_uc()
u.mem_write(PAL_FG, struct.pack('<H', 0xC618))
put_bitmap(u, [0x0000, 0xF800, 0x1234, 0xFFFF])
call(u, 0x0306373C, 10, 20, 13, 20, stack=(0x10, SRC, 2))
want = [0xC618, 0xC618, 0xC618]
results.append(('G keyblit format 2', em == want, f'emitted {fmt(em)}'))

# --- H/I: synthetic resource through DrawImage and the keyed helper -------
RES = 0x03080000


def build_resource(u):
    u.mem_write(RES_CELL, struct.pack('<I', RES))
    # descriptor for id 3: w, h, x, y, size, offset
    desc = struct.pack('<4H2I', 4, 2, 10, 20, 16, 0x2000)
    u.mem_write(RES + 0x20 + 3 * 16, desc)
    # pixel bytes stored big-endian, as in the stock resource section
    u.mem_write(RES + 0x2000, struct.pack(f'>{len(BITMAP)}H', *BITMAP))
    u.mem_write(SAVEINFO + 0x2D8, b'\x00')   # dark theme: no id remap


u, em = make_uc()
build_resource(u)
call(u, 0x03063700, 3)
results.append(('H DrawImage id 3 (synthetic)', em == BITMAP,
                f'emitted {fmt(em)}'))

u, em = make_uc()
build_resource(u)
call(u, 0x03063A08, 3, 10, 20)
want = [v for v in BITMAP if v != 0xF800]   # helper passes format 1
results.append(('I keyed helper id 3 (synthetic)', em == want,
                f'emitted {fmt(em)}'))

# --- J: real stock resource 286 (mode-repeat) via the keyed helper --------
sec = im.sections['images']
imgs = {e['id']: e for e in im.images()}


def stage_real_section(u):
    """Copy the descriptor table and the needed resources' pixels into
    RAM at RES (the full section is 4 MB; only the parts the draw code
    reads are staged)."""
    n = struct.unpack_from('<I', raw, sec['offset'] + 16)[0]
    u.mem_write(RES, raw[sec['offset']:sec['offset'] + 0x20 + n * 16])
    for e in imgs.values():
        if e['id'] in (159, 286):
            rel = e['data_offset'] - sec['offset']
            u.mem_write(RES + rel, raw[e['data_offset']:
                                       e['data_offset'] + e['size']])
e286 = imgs[286]
px286 = struct.unpack_from(f"<{e286['width'] * e286['height']}H",
                           raw, e286['data_offset'])
# colour-domain values are the byte swaps of the file's LE-read values
px286_col = [((v & 0xFF) << 8) | (v >> 8) for v in px286]
want286 = [v for v in px286_col if v != 0xF800]  # format 1 key
u, em = make_uc()
u.mem_write(RES_CELL, struct.pack('<I', RES))
stage_real_section(u)
u.mem_write(SAVEINFO + 0x2D8, b'\x00')
call(u, 0x03063A08, 286, 53, 5)
results.append(('J keyed helper, real resource 286', em == want286,
                f'{len(em)} of {len(px286_col)} pixels emitted; '
                f'{px286_col.count(0xF800)} key-red pixels skipped; '
                f'the art holds no 0x0000 pixels'))

# --- K: real stock resource 159 (play keycap) via DrawImageAt -------------
e159 = imgs[159]
px159 = struct.unpack_from(f"<{e159['width'] * e159['height']}H",
                           raw, e159['data_offset'])
px159_col = [((v & 0xFF) << 8) | (v >> 8) for v in px159]
u, em = make_uc()
u.mem_write(RES_CELL, struct.pack('<I', RES))
stage_real_section(u)
u.mem_write(SAVEINFO + 0x2D8, b'\x00')
call(u, 0x0306354A, 159, 4, 275)
results.append(('K DrawImageAt, real resource 159', em == px159_col,
                f'{len(em)} of {len(px159_col)} pixels emitted, '
                f'including all {px159_col.count(0x10A2)} surround pixels '
                f'of colour 0x10a2'))

print()
failed = 0
for name, ok, detail in results:
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
    failed += 0 if ok else 1
print(f'\n{len(results) - failed}/{len(results)} cases as expected')
sys.exit(1 if failed else 0)
