"""Small stock-control gate for browser admission, codec routing and PCM.

Uses a generated 200 ms stereo silence stream, not external media. The
browser classifier and system loader execute real candidate instructions.
Core-1 mailbox delivery and file RPC are modeled by the existing harness;
these checks cannot establish that the physical playback path works.
"""
import contextlib
import io
import json
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'patches/gapless/rig'),
               str(Path(__file__).resolve().parent)]
from rknano_image import Image
from scenario import Scenario, CODEC, LOAD_START
from machine import RET
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_SP, UC_ARM_REG_LR,
                               UC_ARM_REG_PC)


def silence():
    def page(packet, sequence, granule, flags):
        data = bytearray(b'OggS' + bytes([0, flags]) +
                         struct.pack('<QIII', granule, 123, sequence, 0) +
                         b'\x01' + bytes([len(packet)]) + packet)
        crc = 0
        for byte in data:
            crc ^= byte << 24
            for _ in range(8):
                crc = ((crc << 1) ^ (0x04C11DB7 if crc & 0x80000000 else 0)) & 0xFFFFFFFF
        struct.pack_into('<I', data, 22, crc)
        return data
    head = b'OpusHead' + bytes([1, 2]) + struct.pack('<HIhB', 0, 48000, 0, 0)
    tags = b'OpusTags' + struct.pack('<II', 0, 0)
    result = page(head, 0, 0, 2) + page(tags, 1, 0, 0)
    for i in range(10):
        result += page(b'\xf8\xff\xfe', i + 2, (i + 1) * 960, 4 if i == 9 else 0)
    return bytes(result)


def browser_kind(raw):
    image = Image(raw)
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    uc.mem_map(0x03000000, 0x100000)
    for module in (0, 31):
        for region in ('code', 'data'):
            offset, size = image.module_region(module, region)
            if size:
                uc.mem_write(image.modules[module][region + '_exec'], raw[offset:offset + size])
    entry = bytearray(32)
    entry[:11] = b'SILENCE OPU'
    entry[11] = 0x20
    uc.mem_write(0x030D0000, bytes(entry))
    for reg, value in ((UC_ARM_REG_R0, 0x030D0000),
                       (UC_ARM_REG_SP, 0x030E0000), (UC_ARM_REG_LR, 0x030EF001)):
        uc.reg_write(reg, value)
    uc.emu_start(0x0307D1D1, 0x030EF000, count=10000)
    assert uc.reg_read(UC_ARM_REG_PC) == 0x030EF000, 'browser classifier did not return'
    return uc.mem_read(uc.reg_read(UC_ARM_REG_R0), 1)[0]


def check(raw):
    stock = (ROOT / 'DP3_V137.img').read_bytes()
    assert browser_kind(stock) == 6, 'stock negative control must reject OPU'
    assert browser_kind(raw) == 1, 'candidate browser must admit OPU as audio'
    system = Scenario(raw, ext=b'OPU', rate=48000)
    system.set_next_file()
    system.m.call(LOAD_START, limit=2_000_000)
    assert system.m.u.reg_read(UC_ARM_REG_PC) == RET, 'system open did not return'
    assert system.m.r32(CODEC) == 1
    assert 72 in [load[0] for load in system.m.loads], 'Opus module was not loaded'
    import harness72 as decoder
    previous = decoder.H.WS
    with tempfile.TemporaryDirectory(prefix='ce-opus-open-') as tmp:
        workspace = Path(tmp)
        extracted = workspace / 'extracted'
        extracted.mkdir()
        image = Image(raw)
        (extracted / 'manifest.json').write_text(json.dumps({'modules': [image.modules[72]]}))
        for region in ('code', 'data'):
            offset, size = image.module_region(72, region)
            address = image.modules[72][region + '_exec']
            (extracted / f'module_72_{region}_{address:08x}.bin').write_bytes(raw[offset:offset + size])
        media = workspace / 'silence.opus'
        media.write_bytes(silence())
        machine = None
        try:
            decoder.H.WS = workspace
            with contextlib.redirect_stdout(io.StringIO()):
                machine = decoder.H72(media=media, trace_path=str(workspace / 'trace.log'))
                assert machine.boot(), 'decoder did not become ready'
                info = machine.open_current(max_slices=50)
                assert info and not machine.open_failed, 'decoder rejected generated Opus'
                assert machine.poll_decode(max_slices=50), 'decoder did not produce another buffer'
            assert (info['rate'], info['channels'], info['bps'], info['length_ms']) == (48000, 2, 16, 200)
            frames = len(machine.pcm) // 4
            assert frames == 3840 and not any(machine.pcm), 'unexpected silence PCM'
        finally:
            decoder.H.WS = previous
            if machine is not None:
                machine.tr.f.close()
    return {'stock_browser_kind': 6, 'candidate_browser_kind': 1, 'codec_id': 1,
            'module72_loaded': True, 'sample_rate': 48000, 'channels': 2,
            'initial_pcm_frames': frames, 'expected_pcm_frames': 3840,
            'hardware_playback_verified': False}


if __name__ == '__main__':
    candidate = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'release/DP3_V137_CE.img'
    print(json.dumps(check(candidate.read_bytes()), indent=2))
