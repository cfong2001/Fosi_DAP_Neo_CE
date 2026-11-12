#!/usr/bin/env python3
"""Checks for the EQ preset option (needs unicorn).

1. Stock's selector, run under Unicorn, maps menu items Classical,
   Bass Boost and Heavy Metal onto Pop's array, Jazz's array and a flat
   array. After the fix every item 1..6 reads its own array.
2. With no curves configured, every menu item applies exactly the gains
   stock applied.
3. The example config's AutoEQ curve (Sennheiser HD 600) lands in slot 6
   with a realised error under 1.0 dB rms, computed with the firmware's
   own band filters.
4. The example's slot 6 name replaces that menu item's text in all 21
   languages and leaves every other EQ name as stock; bad names are
   refused.
"""
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / 'patches' / 'framework'))
sys.path.insert(0, str(HERE))
import build as fw  # noqa: E402
import eqfit  # noqa: E402
from rknano_image import Image  # noqa: E402
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_CODE  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_R1, UC_ARM_REG_R4, UC_ARM_REG_SP  # noqa: E402


def selected_array(raw, mode):
    """Run module 33's selector (0x0308ACF8) for an EQ mode byte; return the
    gain array passed to the EQ setup call (0x0308C22E), or None."""
    img = Image(raw)
    m = img.modules[33]
    off, _ = img.module_region(33, 'code')
    doff, _ = img.module_region(33, 'data')
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
    uc.mem_map(0x03000000, 0x90000)
    uc.mem_write(m['code_exec'], raw[off:off + m['code_len']])
    uc.mem_write(m['data_exec'], raw[doff:doff + m['data_len']])
    uc.mem_write(0x03001000, bytes([mode]))
    uc.reg_write(UC_ARM_REG_R4, 0x03001000)
    uc.reg_write(UC_ARM_REG_SP, 0x03003000)
    got = []

    def hook(uc, a, size, _):
        if a == 0x0308C22E:
            p = uc.reg_read(UC_ARM_REG_R1)
            got.append(list(struct.unpack('<31H', bytes(uc.mem_read(p, 62)))))
            uc.emu_stop()
        elif a == 0x0308AD74:
            uc.emu_stop()
    uc.hook_add(UC_HOOK_CODE, hook)
    uc.emu_start(0x0308ACF8 | 1, 0, count=200)
    return [g - 12 for g in got[0]] if got else None


def build(stock, slots, names=None):
    base = fw.load_manifest(REPO / 'patches' / 'framework' / 'patches' / 'manifest.txt')
    extra = eqfit.slot_patches(stock, slots) + eqfit.name_patches(stock, names or {})
    out, _ = fw.build_image(stock, base + extra, fw.DEFAULT_BUILD_DATE)
    return out


def main():
    stock = (REPO / 'DP3_V137.img').read_bytes()
    fails = 0
    stock_sel = {n: selected_array(stock, n) for n in range(1, 7)}
    print('stock menu item -> applied gains (dB)')
    for n in range(1, 7):
        print(f'  {eqfit.SLOTS[n]:<12} {stock_sel[n]}')
    dup = stock_sel[4] == stock_sel[1] and stock_sel[5] == stock_sel[2] and stock_sel[6] == [0] * 31
    print('stock duplicates Classical=Pop, Bass Boost=Jazz, Heavy Metal=flat:', dup)
    fails += not dup

    plain = build(stock, {})
    same = all(selected_array(plain, n) == stock_sel[n] for n in range(1, 7))
    print('no curves configured: every item applies stock gains:', same)
    fails += not same

    slots, names, report = eqfit.load_config(HERE / 'example.json', stock)
    img = build(stock, slots, names)
    sel = {n: selected_array(img, n) for n in range(1, 7)}
    ok = sel[5] == slots[5] and sel[6] == slots[6] and all(sel[n] == stock_sel[n] for n in (1, 2, 3, 4))
    print('example config reaches slots 5 and 6, others unchanged:', ok, report)
    fails += not ok
    fails += report[6]['rms_error_db'] >= 1.0

    def eq_names(raw):
        im = Image(raw)
        return [[r['text'] for r in list(im.lang(lang))[175:181]] for lang in range(21)]
    before, after = eq_names(stock), eq_names(img)
    named = (all(a[5] == names[6] for a in after)
             and all(a[:5] == b[:5] for a, b in zip(after, before)))
    print(f'slot 6 named {names[6]!r} in 21 languages, other names stock:', named)
    fails += not named
    for bad in ('', ' Warm', 'x' * 25, 'a\nb'):
        try:
            eqfit.name_patches(stock, {1: bad})
            print('accepted a bad name:', repr(bad))
            fails += 1
        except ValueError:
            pass
    if fails:
        raise SystemExit(f'FAIL: {fails}')
    print('OK')


if __name__ == '__main__':
    main()
