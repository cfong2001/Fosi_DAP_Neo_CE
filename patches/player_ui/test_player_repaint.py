"""Native framebuffer coverage, display-context parity and repaint work counts."""
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(Path(__file__).resolve().parent), str(ROOT / 'tools')]
from rknano_image import Image
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *

TOP, LOWER, CTX, TEXT, SP, END = 0x030065A8, 0x0306F224, 0x030238B8, 0x0302385C, 0x030ED000, 0x030EF000
SURFACES = ((TOP, 115200), (LOWER, 38400))
KEPT = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)


def draw(raw, entry, args, *, band=False, rotation=0, count=False):
    image = Image(raw)
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x03000000, 0x100000)
    offset, size = image.module_region(0, 'code')
    u.mem_write(image.modules[0]['code_exec'], raw[offset:offset + size])
    for address, size in SURFACES:
        u.mem_write(address, struct.pack('<H', 0x1234) * (size // 2))
    if band:
        u.mem_write(LOWER, bytes(240 * 35 * 2))
        for y in range(14):
            for x0, width in ((7, 66), (191, 49)):
                u.mem_write(LOWER + 480 * y + 2 * x0, b'\xef\xbe' * width)
    context = bytearray(40)
    struct.pack_into('<4H', context, 0, 0, 0, 319, 0)
    struct.pack_into('<I', context, 20, rotation)
    u.mem_write(CTX, bytes(context))
    u.mem_write(TEXT, struct.pack('<6H', 0xFFFF, 0x10A2, 1, 0, 240, 320))
    u.mem_write(0x03004400, struct.pack('<H', args[4]))
    instructions = 0
    def instruction(uc, address, size, _):
        nonlocal instructions
        instructions += 1
    if count:
        u.hook_add(UC_HOOK_CODE, instruction)
    def write(uc, access, address, size, value, _):
        allowed = SURFACES + ((CTX, 40), (SP - 4096, 4096), (0x03024904, 48))
        assert any(start <= address and address + size <= start + length for start, length in allowed), 'repaint wrote outside its buffers'
    u.hook_add(UC_HOOK_MEM_WRITE, write)
    for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3), args):
        u.reg_write(reg, value)
    u.mem_write(SP, struct.pack('<I', args[4]))
    for reg in KEPT:
        u.reg_write(reg, 0x12345678)
    u.reg_write(UC_ARM_REG_SP, SP)
    u.reg_write(UC_ARM_REG_LR, END | 1)
    u.emu_start(entry | 1, END, count=10000000)
    assert u.reg_read(UC_ARM_REG_PC) == END and u.reg_read(UC_ARM_REG_SP) == SP
    assert all(u.reg_read(reg) == 0x12345678 for reg in KEPT)
    return (b''.join(bytes(u.mem_read(address, size)) for address, size in SURFACES),
            bytes(u.mem_read(CTX, 40)), instructions)


def check(raw):
    image = Image(raw)
    offset, _ = image.module_region(0, 'code')
    base = image.modules[0]['code_exec']
    from build_player_repaint import payloads, branch, GAPS, FULL
    gap, full = payloads()
    for address, code in ((GAPS, gap), (FULL, full)):
        assert raw[offset + address - base:offset + address - base + len(code)] == code
    legacy = bytearray(raw)
    from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
    ks=Ks(KS_ARCH_ARM, KS_MODE_THUMB)
    old=bytes(ks.asm('push {r0-r4,lr};ldr r0,=0x03004400;ldrh r0,[r0];bl 0x0305DE30;pop.w {r0-r4,lr};ldr ip,=0x030632FB;bx ip;.ltorg',0x03053EF4)[0])
    at=offset+0x03053EF4-base
    legacy[at:at+len(old)]=old
    args = (40, 254, 201, 268, 0x7222)
    old = draw(bytes(legacy), 0x03053EF4, args, band=True)[0]
    new = draw(raw, 0x03053EF4, args, band=True)[0]
    restored = 0
    for y in range(240, 275):
        for x in range(240):
            index = y * 240 + x
            value = struct.unpack_from('<H', new, index * 2)[0]
            is_time = y <= 253 and (7 <= x <= 72 or 191 <= x <= 239)
            assert value == (0xBEEF if is_time else 0x7222)
            is_bar = 254 <= y <= 268 and 40 <= x <= 201
            if not is_time and not is_bar:
                assert struct.unpack_from('<H', old, index * 2)[0] == 0
                restored += 1
    assert restored == 4360
    assert new[:240*240*2] == struct.pack('<H',0x1234)*(240*240)
    assert new[275*240*2:] == struct.pack('<H',0x1234)*(45*240)
    args = (0, 0, 239, 319, 0x39C7)
    normal = draw(raw, 0x030632FA, args, count=True)
    fast = draw(raw, FULL, args, count=True)
    assert fast[:2] == normal[:2], 'full fill changed framebuffer or display context'
    assert fast[0] == struct.pack('<H', args[4]) * 76800
    assert fast[2] < normal[2] // 4
    # The same hook must retain the original rotated display behavior.
    rotated = draw(raw, FULL, args, rotation=1)
    assert rotated[:2] == draw(raw, 0x030632FA, args, rotation=1)[:2]
    return dict(progress_gap_pixels_restored=restored, time_label_pixels_preserved=1610,
                full_fill_pixels=76800, normal_fill_instructions=normal[2],
                burst_fill_instructions=fast[2], instruction_ratio=round(fast[2] / normal[2], 4),
                framebuffer_context_abi_parity=True, rotation_fallback_parity=True)


if __name__ == '__main__':
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'release/DP3_V137_CE.img'
    print(json.dumps(check(path.read_bytes()), indent=2))
