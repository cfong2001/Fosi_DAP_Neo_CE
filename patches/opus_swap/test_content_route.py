"""Execute the stock content probe, including its real file-read callback.

The previous extension-only harness left these callbacks uninitialized;
it therefore missed the second, content-based overwrite from OPU to OGG.
"""
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'tests/opus_harness'), str(HERE)]
from rknano_image import Image
from test_open_path import silence, system_route
from build_content_route import PREFIX, SIGNATURE, HOOK, RESET_SEEK, STOCK_OGG, assemble
from build_tail import branch
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE, UC_HOOK_MEM_READ
from unicorn.arm_const import *

EXT, STACK, STOP, READ, SEEK = 0x030D0000, 0x030E0000, 0x030EF000, 0x030EF100, 0x030EF104


def detect(raw, data):
    image = Image(raw)
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    uc.mem_map(0x03000000, 0x100000)
    for region in ('code', 'data'):
        offset, size = image.module_region(0, region)
        uc.mem_write(image.modules[0][region + '_exec'], raw[offset:offset + size])
    uc.mem_write(0x0300443C, struct.pack('<I', READ | 1))
    uc.mem_write(0x03004440, struct.pack('<I', SEEK | 1))
    uc.mem_write(0x0304B4D4, struct.pack('<I', 1))
    uc.mem_write(EXT - 8, b'Z' * 8 + b'OPU\0' + b'Z' * 8)
    position = 0
    calls = []
    def callback(u, address, size, _):
        nonlocal position
        if address == READ:
            target, count, handle = [u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2)]
            assert handle == 7
            block = data[position:position + count]
            u.mem_write(target, block)
            position += len(block)
            result = len(block)
            calls.append(('read', result))
        elif address == SEEK:
            offset, whence, handle = [u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2)]
            assert handle == 7
            position = offset if whence == 0 else position + offset
            result = position
            calls.append(('seek', position))
        else:
            return
        u.reg_write(UC_ARM_REG_R0, result)
        u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR))
    uc.hook_add(UC_HOOK_CODE, callback)
    for reg, value in ((UC_ARM_REG_R0, EXT), (UC_ARM_REG_R1, 7),
                       (UC_ARM_REG_SP, STACK), (UC_ARM_REG_LR, STOP | 1)):
        uc.reg_write(reg, value)
    try:
        uc.emu_start(0x03067F51, STOP, count=100000)
    except Exception as exc:
        raise AssertionError(f'content probe fault at {uc.reg_read(UC_ARM_REG_PC):#x}; r5={uc.reg_read(UC_ARM_REG_R5):#x}') from exc
    assert uc.reg_read(UC_ARM_REG_PC) == STOP, 'content probe did not return'
    assert uc.reg_read(UC_ARM_REG_SP) == STACK
    assert bytes(uc.mem_read(EXT - 8, 8)) == b'Z' * 8
    assert bytes(uc.mem_read(EXT + 3, 9)) == b'\0' + b'Z' * 8
    assert position == 0 and calls[-1] == ('seek', 0), 'native seek reset lost'
    return bytes(uc.mem_read(EXT, 3)), calls


def check(raw):
    image = Image(raw)
    offset, _ = image.module_region(0, 'code')
    base = image.modules[0]['code_exec']
    prefix, signature = assemble()
    for address, code in ((PREFIX, prefix), (SIGNATURE, signature), (HOOK, branch(HOOK, PREFIX))):
        assert raw[offset + address - base:offset + address - base + len(code)] == code, 'candidate lacks content-route repair'
    stock = (ROOT / 'DP3_V137.img').read_bytes()
    data = silence()
    assert detect(stock, data)[0] == b'OGG', 'negative control no longer reproduces Opus misrouting'
    legacy = bytearray(raw)
    stock_image = Image(stock)
    stock_offset, _ = stock_image.module_region(0, 'code')
    for address, size in ((PREFIX, len(prefix)), (SIGNATURE, len(signature)), (HOOK, 4)):
        at = offset + address - base
        before = stock_offset + address - stock_image.modules[0]['code_exec']
        legacy[at:at + size] = stock[before:before + size]
    legacy_codec, legacy_loads = system_route(bytes(legacy), data)
    assert legacy_codec == 4 and 75 in legacy_loads, 'negative system control did not load Vorbis'
    codec, loads = system_route(raw, data)
    assert codec == 1 and 72 in loads, 'repaired system route did not load Opus'
    assert detect(raw, data)[0] == b'OPU'
    cases = []
    for label, index, value in (('ogg-version', 4, 1), ('not-bos', 5, 0),
                                ('continued', 5, 3), ('no-segments', 26, 0),
                                ('short-first-packet', 27, 18), ('not-opus', 28, 1)):
        broken = bytearray(data)
        broken[index] = value
        assert detect(raw, bytes(broken))[0] == b'OGG', label
        cases.append(label)
    # A Vorbis identification signature remains on the native Ogg route.
    vorbis = bytearray(data)
    vorbis[28:36] = b'\x01vorbis\0'
    assert detect(raw, bytes(vorbis))[0] == b'OGG'
    guarded = 0
    for start, segments in ((0, 1), (485, 1), (486, 1), (508, 1),
                            (0, 255), (180, 255), (212, 255)):
        u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        u.mem_map(0x03000000, 0x100000)
        u.mem_write(base, raw[offset:offset + image.modules[0]['code_len']])
        buffer = 0x030D1000
        body = bytearray(512)
        for relative, value in ((4, 0), (5, 2), (26, segments), (27, 19)):
            if start + relative < 512:
                body[start + relative] = value
        payload = start + 27 + segments
        if payload + 8 <= 512:
            body[payload:payload + 8] = b'OpusHead'
        u.mem_write(buffer - 16, b'Z' * 16 + bytes(body) + b'Z' * 16)
        u.mem_write(EXT - 8, b'Z' * 8 + b'OPU\0' + b'Z' * 8)
        u.reg_write(UC_ARM_REG_R4, buffer + start)
        u.reg_write(UC_ARM_REG_R5, EXT)
        u.reg_write(UC_ARM_REG_R8, start)
        u.reg_write(UC_ARM_REG_SP, STACK)
        kept = (UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)
        for reg in kept:
            u.reg_write(reg, 0x12345678)
        exits = []
        def stop(machine, address, size, _):
            if address in (RESET_SEEK, STOCK_OGG):
                exits.append(address)
                machine.emu_stop()
        def read_guard(machine, access, address, size, value, _):
            if buffer - 16 <= address < buffer + 528:
                assert buffer <= address and address + size <= buffer + 512, 'header read outside buffer'
        u.hook_add(UC_HOOK_CODE, stop)
        u.hook_add(UC_HOOK_MEM_READ, read_guard)
        u.emu_start(HOOK | 1, STOP, count=1000)
        expected = RESET_SEEK if payload + 19 <= 512 else STOCK_OGG
        assert exits == [expected], (start, segments, exits)
        assert u.reg_read(UC_ARM_REG_SP) == STACK
        assert all(u.reg_read(reg) == 0x12345678 for reg in kept)
        assert bytes(u.mem_read(EXT - 8, 8)) == b'Z' * 8
        assert bytes(u.mem_read(EXT + 3, 9)) == b'\0' + b'Z' * 8
        guarded += 1
    return {'legacy_opus_detection': 'OGG', 'repaired_opus_detection': 'OPU',
            'legacy_system_codec': legacy_codec, 'repaired_system_codec': codec,
            'vorbis_detection': 'OGG', 'malformed_or_non_bos_controls': len(cases),
            'guarded_buffer_positions': guarded, 'callee_registers_preserved': True,
            'file_read_callback_executed': True, 'native_seek_reset': True}


if __name__ == '__main__':
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'release/DP3_V137_CE.img'
    print(json.dumps(check(path.read_bytes()), indent=2))
