"""Measure the real player repaint's pixel coverage, not just its ground cell."""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_SP

SITE = 0x0307EFA6


def repaint(raw, view, color, event=True, hidden=False, light=False):
    image = Image(raw)
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x03000000, 0x100000)
    for module in (0, 27):
        for kind in ('code', 'data'):
            offset, size = image.module_region(module, kind)
            u.mem_write(image.modules[module][kind + '_exec'], raw[offset:offset + size])
    if event:
        u.mem_write(0x03023CFC, struct.pack('<I', 1 << (0x39 % 32)))
    u.mem_write(0x030232BA, bytes([view]))
    u.mem_write(0x0302348C, bytes([hidden]))
    u.mem_write(0x03023578, bytes([light]))
    u.mem_write(0x03004400, struct.pack('<H', color))
    u.reg_write(UC_ARM_REG_SP, 0x030F0000)
    pixels = [0] * (240 * 320)
    fills, resources = [], []
    def hook(machine, address, size, _):
        args = [machine.reg_read(reg) for reg in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]
        if address == 0x030632FA:
            x0, y0, x1, y1 = args
            ink = struct.unpack('<I', machine.mem_read(machine.reg_read(UC_ARM_REG_SP), 4))[0]
            assert (x0, y0, x1, y1) == (0, 0, 239, 319)
            fills.append(ink)
            pixels[:] = [ink] * len(pixels)
        elif address == 0x03063700:
            resources.append(args[0])
            # Both committed backgrounds are solid; the control's resource
            # selection is real, and its pixels are independently checked below.
            pixels[:] = [0xFFFF if light else 0x10A2] * len(pixels)
        machine.reg_write(UC_ARM_REG_PC, machine.reg_read(UC_ARM_REG_LR))
    for address in (0x030632FA, 0x03063700, 0x0306354A, 0x03063642):
        u.hook_add(UC_HOOK_CODE, hook, begin=address, end=address)
    u.emu_start(0x0307EF7B, 0x0307F084, count=20000)
    assert u.reg_read(UC_ARM_REG_PC) == 0x0307F084
    title = struct.unpack('<I', u.mem_read(0x03023D00, 4))[0] & (1 << (0x4A % 32))
    return pixels, fills, resources, bool(title)


def check(raw):
    image = Image(raw)
    offset = image.module_region(27, 'code')[0] + SITE - image.modules[27]['code_exec']
    assert raw[offset:offset + 2] == b'\x00\xbf', 'missing full-ground repair'
    for rid, ink in ((138, 0x10A2), (304, 0xFFFF)):
        entry = next(entry for entry in image.images() if entry['id'] == rid)
        data = raw[entry['data_offset']:entry['data_offset'] + entry['size']]
        assert data == struct.pack('>H', ink) * (240 * 320), 'background resource is no longer a solid fill'
    legacy = bytearray(raw)
    legacy[offset:offset + 2] = b'\x50\xb1'
    before, fills, resources, title = repaint(bytes(legacy), 0, 0x7000)
    assert before.count(0x7000) == 0 and resources == [138] and not fills and title
    cases = 0
    for view in (0, 1):
        for hidden in (False, True):
            for light in (False, True):
                for color in (0x7000, 0x39C7):
                    pixels, fills, resources, title = repaint(raw, view, color, hidden=hidden, light=light)
                    assert pixels.count(color) == 76800 and fills == [color] and not resources and title
                    cases += 1
    pixels, fills, resources, title = repaint(raw, 0, 0x7000, event=False)
    assert not fills and not resources and not title and pixels == [0] * 76800
    return dict(full_screen_pixels=76800, repaint_cases=cases,
                legacy_art_view_derived_pixels=0, repaired_art_view_derived_pixels=76800,
                no_event_draws=0, title_repaint_preserved=True)


if __name__ == '__main__':
    import json
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'release/DP3_V137_CE.img'
    print(json.dumps(check(path.read_bytes()), indent=2))
