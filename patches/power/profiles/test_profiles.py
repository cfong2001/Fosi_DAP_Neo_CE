#!/usr/bin/env python3
"""Emulation checks for the power profile item.

Applies the seven profile patches and the menu runs to the stock image
(or, with PROFILES_FULL_IMAGE, takes a built image that carries them),
then runs the real firmware code under Unicorn:

  1. GetResourceStr and GetMenuTextInfoWithIDNum (module 0) return the
     stock text and headers for every stock id in every language, and
     the new labels and headers for ids 266..269.
  2. The settings tree: item 164 lists 266 as its 17th child, 243's
     next sibling is 266, and 266 lists 267..269.
  3. Module 32's value switch: item 266 selects the profile whose three
     values match SAVEINFO (none when nothing matches); items 188 and
     196 still load their stock bytes.
  4. Module 32's commit handler: options 267..269 write the three
     settings through the stock setters, apply the backlight and save;
     a stock option (197) never enters the hook; an id past the range
     changes nothing.

The flash read (0x0306432A) is replaced by a reader over the image
file, which is what the stock routine does on hardware.
"""
import json
import os
import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                               UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5,
                               UC_ARM_REG_R7, UC_ARM_REG_SP, UC_ARM_REG_LR,
                               UC_ARM_REG_PC)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / 'tools'))
sys.path.insert(0, str(REPO / 'patches' / 'framework'))
from rknano_image import Image  # noqa: E402
import build_profiles as bp  # noqa: E402

SAVEINFO = 0x030232A0
MENU_BASE_PTR = 0x03023288
LOGICAL = 0x10000000          # arbitrary logical address of the language section
STOP = 0x02000000
STACK = 0x02100000
BUF = 0x02200000
PATCHES = sorted((REPO / 'patches' / 'full' / 'patches').glob('014[0-6]-*.patch'))

failures = 0


def check(ok, what):
    global failures
    print(('PASS ' if ok else 'FAIL ') + what)
    if not ok:
        failures += 1


def load_image():
    path = os.environ.get('PROFILES_FULL_IMAGE')
    if path:
        return Path(path).read_bytes()
    sys.path.insert(0, str(REPO / 'patches' / 'framework'))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'fwbuild', REPO / 'patches' / 'framework' / 'build.py')
    fw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fw)
    raw = (REPO / 'DP3_V137.img').read_bytes()
    raw, _ = fw.apply_patches(raw, [fw.parse_patch(p) for p in PATCHES])
    raw = bytearray(raw)
    for r in json.loads((HERE / 'profile-menu.json').read_text())['runs']:
        o = int(r['offset'], 16)
        e, n = bytes.fromhex(r['expect']), bytes.fromhex(r['replace'])
        assert raw[o:o + len(e)] == e
        raw[o:o + len(n)] = n
    return bytes(raw)


class Rig:
    def __init__(self, raw):
        self.raw = raw
        self.img = Image(raw)
        self.lang_off = self.img.sections['lang']['offset']
        self.uc = uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        uc.mem_map(0x03000000, 0x00100000)
        uc.mem_map(STOP, 0x1000)
        uc.mem_map(STACK - 0x10000, 0x10000)
        uc.mem_map(BUF, 0x1000)
        for idx in (0, 32):
            for kind in ('code', 'data'):
                off, n = self.img.module_region(idx, kind)
                if n:
                    uc.mem_write(self.img.modules[idx][kind + '_exec'], raw[off:off + n])
        uc.mem_write(MENU_BASE_PTR, struct.pack('<I', LOGICAL))
        # SAVEINFO +0x1F is the SDK's FMEnable, copied from the firmware
        # header at boot. With it zero the stock lookups use a 257-record
        # stride that the image does not have, so every unit that shows
        # its languages correctly runs with it set.
        uc.mem_write(SAVEINFO + 0x1F, b'\x01')
        self.stubs = {}
        self.calls = []
        self.trace = set()
        uc.hook_add(UC_HOOK_CODE, self._hook)

    def _hook(self, uc, addr, size, _):
        self.trace.add(addr)
        if addr == 0x0306432A:          # flash read: (address, buffer, bytes)
            a, b, n = (uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2))
            off = a - LOGICAL + self.lang_off
            uc.mem_write(b, self.raw[off:off + n])
            self._ret(0)
        elif addr in self.stubs:
            args = [uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1)]
            self.calls.append((self.stubs[addr], args[0]))
            self._ret(0 if self.stubs[addr] != 'changed?' else 1)

    def _ret(self, value):
        self.uc.reg_write(UC_ARM_REG_R0, value)
        self.uc.reg_write(UC_ARM_REG_PC, self.uc.reg_read(UC_ARM_REG_LR))

    def call(self, addr, regs, until=STOP):
        uc = self.uc
        uc.reg_write(UC_ARM_REG_SP, STACK)
        uc.reg_write(UC_ARM_REG_LR, STOP | 1)
        for r, v in regs.items():
            uc.reg_write(r, v)
        uc.emu_start(addr | 1, until, count=200000)
        return uc.reg_read(UC_ARM_REG_R0)

    def u8(self, off):
        return self.uc.mem_read(SAVEINFO + off, 1)[0]

    def set8(self, off, v):
        self.uc.mem_write(SAVEINFO + off, bytes([v]))


def stock_record(raw, lang, rid):
    img = Image(raw)
    start = img.sections['lang']['offset']
    o = start + 0x56 + lang * 266 * 258 + rid * 258
    return raw[o:o + 258]


def main():
    raw = load_image()
    stock = (REPO / 'DP3_V137.img').read_bytes()
    rig = Rig(raw)

    # 1. lookups, every stock id and language, plus the new ids
    bad = []
    for lang in range(21):
        rig.set8(0x10, lang)
        for rid in range(266):
            rec = stock_record(stock, lang, rid)
            rig.call(0x030630C2, {UC_ARM_REG_R0: rid, UC_ARM_REG_R1: BUF, UC_ARM_REG_R2: 100})
            expected = bytearray(rec[58:258])
            # Standard CE intentionally renames these categories. Standalone
            # profile builds retain stock text; validate the exact edited bytes.
            if os.environ.get('PROFILES_FULL_IMAGE') and lang == 2 and rid in (82, 83):
                label = ('Artists' if rid == 82 else 'Albums') + '\0'
                encoded = label.encode('utf-16le')
                expected[:len(encoded)] = encoded
            if bytes(rig.uc.mem_read(BUF, 200)) != expected:
                bad.append(('str', lang, rid))
            if rid in (164, 243):
                continue                  # edited below
            rig.call(0x03063206, {UC_ARM_REG_R0: rid, UC_ARM_REG_R1: BUF})
            if bytes(rig.uc.mem_read(BUF, 58)) != rec[:58]:
                bad.append(('menu', lang, rid))
    check(not bad, f'stock headers and expected text for 266 ids x 21 languages ({bad[:3]})')

    bad = []
    for lang, (_, labels) in enumerate(bp.LABELS):
        rig.set8(0x10, lang)
        for k, text in enumerate(labels):
            rig.uc.mem_write(BUF, bytes(200))
            rig.call(0x030630C2, {UC_ARM_REG_R0: 266 + k, UC_ARM_REG_R1: BUF, UC_ARM_REG_R2: 100})
            got = bytes(rig.uc.mem_read(BUF, 200)).decode('utf-16le').split('\0')[0]
            if got != text:
                bad.append((lang, k, got))
    check(not bad, f'labels for ids 266..269 in all 21 languages ({bad[:2]})')

    # 2. the tree
    def header(rid, lang=2):
        rig.set8(0x10, lang)
        rig.call(0x03063206, {UC_ARM_REG_R0: rid, UC_ARM_REG_R1: BUF})
        return struct.unpack('<29H', bytes(rig.uc.mem_read(BUF, 58)))
    ok = True
    for lang in range(21):
        h = header(164, lang)
        ok &= h[7] == 17 and h[8 + 16] == 266 and h[:7] == struct.unpack('<7H', stock_record(stock, lang, 164)[:14])
        ok &= header(243, lang)[5] == 266
    check(ok, 'settings (164) has 17 children ending in 266; 243 links to 266, in every language')
    h = header(266)
    check(h[:8] == (266, 164, 16, 267, 243, 0xFFFF, 0xFFFF, 3) and h[8:11] == (267, 268, 269),
          f'item 266 header: parent 164, index 16, children 267..269 ({h[:11]})')
    ok = all(header(267 + k)[:3] == (267 + k, 266, k) and header(267 + k)[7] == 0 for k in range(3))
    check(ok, 'options 267..269: parent 266, indices 0..2, no children')

    # 3. value switch (module 32, entered at the patched site)
    rec = BUF + 0x400
    def value(item):
        rig.uc.mem_write(rec, bytes(16))
        regs = {UC_ARM_REG_R5: item, UC_ARM_REG_R7: SAVEINFO, UC_ARM_REG_R4: rec}
        rig.uc.reg_write(UC_ARM_REG_R0, 0xEE)
        for r, v in regs.items():
            rig.uc.reg_write(r, v)
        rig.uc.reg_write(UC_ARM_REG_SP, STACK)
        rig.uc.emu_start(0x0307DBCE | 1, 0x0307DC50, count=1000)
        return rig.uc.reg_read(UC_ARM_REG_R0), rig.uc.reg_read(UC_ARM_REG_PC)
    table = [(4, 3, 0), (2, 2, 2), (0, 0, 1)]
    ok = True
    for i, (b, s, p) in enumerate(table):
        rig.set8(0x14, b); rig.set8(0x15, s); rig.set8(0x18, p)
        r0, _ = value(266)
        ok &= r0 == i
    check(ok, 'item 266 marks the profile matching brightness, screen off and power off')
    rig.set8(0x14, 3); rig.set8(0x15, 3); rig.set8(0x18, 0)
    rig.uc.reg_write(UC_ARM_REG_R0, 0xEE)
    rig.trace.clear()
    r0, pc = value(266)
    check(0x0307DC4E not in rig.trace and pc == 0x0307DC50,
          'item 266 with no matching profile leaves the stock "none" marker')
    rig.set8(0x15, 5)
    r0, _ = value(188)
    check(r0 == 5, 'item 188 still loads Auto Screen Off (+0x15)')
    rig.set8(0x14, 1)
    r0, _ = value(196)
    check(r0 == 1, 'item 196 still loads brightness (+0x14) through the re-entered switch')
    rig.set8(0x18, 4)
    r0, _ = value(202)
    check(r0 == 4, 'item 202 still loads Auto Power Off (+0x18)')

    # 4. commit
    rig.stubs = {0x03064964: 'backlight', 0x0306CA10: 'save', 0x03065188: 'arm',
                 0x030651CC: 'disarm', 0x030570E8: 'changed?'}
    for i, (b, s, p) in enumerate(table):
        rig.set8(0x14, 9); rig.set8(0x15, 9); rig.set8(0x18, 9)
        rig.calls.clear()
        rig.call(0x0307FA74, {UC_ARM_REG_R0: 267 + i, UC_ARM_REG_R1: 0})
        got = (rig.u8(0x14), rig.u8(0x15), rig.u8(0x18))
        names = [c[0] for c in rig.calls]
        check(got == (b, s, p) and ('backlight', b) in rig.calls and names.count('save') == 1,
              f'option {267 + i} sets {got} (want {(b, s, p)}), backlight {b}, one save: {names}')
    rig.trace.clear()
    rig.set8(0x14, 2)
    rig.call(0x0307FA74, {UC_ARM_REG_R0: 197, UC_ARM_REG_R1: 0})
    pockets = range(0x03067064, 0x030670E0)
    check(not any(a in pockets for a in rig.trace), 'stock option 197 never enters the commit hook')
    before = bytes(rig.uc.mem_read(SAVEINFO, 0x300))
    rig.calls.clear()
    rig.call(0x0307FA74, {UC_ARM_REG_R0: 270, UC_ARM_REG_R1: 0})
    check(bytes(rig.uc.mem_read(SAVEINFO, 0x300)) == before and
          not [c for c in rig.calls if c[0] in ('backlight', 'save')],
          'an id past the options changes nothing')

    print(f'{failures} failure(s)' if failures else 'ALL PROFILE CHECKS PASS')
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
