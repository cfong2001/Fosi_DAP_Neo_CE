#!/usr/bin/env python3
"""Run the stock and patched block reader (0x03067510) against a fake disk.

The module 0 code under test is real. The sector driver MDRead
(0x030678CA), the interrupt mask pair and the write wrapper's device
record are replaced by Python models: a dictionary of sectors per device
that records every sector read, and can fail chosen reads once.

Checks:
- every read returns the disk's current bytes and the stock return value,
  for random mixes of system-disk, data-disk and other-device reads and
  writes, aligned and unaligned, shorter and longer than a sector;
- a failed system-disk sector read is retried once, as in stock;
- a write through 0x03067912 is never followed by a stale cached sector;
- on the glyph and row reads of one browser wheel step and of one Now
  Playing screen, the patched reader issues fewer sector reads.
"""
import random
import re
import struct
import sys
import unittest
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1,
                               UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image  # noqa: E402

READER, WRITER, MDREAD = 0x03067510, 0x03067912, 0x030678CA
DISPATCH, ISR_OFF, ISR_ON = 0x030678B0, 0x0306660A, 0x03066662
FLASH_SEC = 0x03005878
SYS, DATA, OTHER = 0x00030000, 0x00030001, 0x00030003
RET, BUF, STACK = 0x030FFF00, 0x030E0000, 0x030F0000
RECORD, WRITE_FN = 0x030D0000, 0x030D0100
SECTORS = 64


def patch_list():
    out = []
    for path in sorted(HERE.glob('029*.patch')):
        text = path.read_text()
        out.append((int(re.search(r'^address: (0x[0-9a-f]+)', text, re.M)[1], 16),
                    bytes.fromhex(re.search(r'^expect: ([0-9a-f]+)', text, re.M)[1]),
                    bytes.fromhex(re.search(r'^replace: ([0-9a-f]+)', text, re.M)[1])))
    return out


def module0(patched):
    raw = (ROOT / 'DP3_V137.img').read_bytes()
    image = Image(raw)
    m = image.modules[0]
    offset, size = image.module_region(0, 'code')
    code = bytearray(raw[offset:offset + size])
    doff, dsize = image.module_region(0, 'data')
    if patched:
        for address, expect, replace in patch_list():
            at = address - m['code_exec']
            assert code[at:at + len(expect)] == expect, hex(address)
            code[at:at + len(replace)] = replace
    return m['code_exec'], bytes(code), m['data_exec'], raw[doff:doff + dsize]


class Machine:
    def __init__(self, patched, seed=1):
        self.uc = uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        uc.mem_map(0x03000000, 0x00100000)
        base, code, dbase, data = module0(patched)
        uc.mem_write(base, code)
        uc.mem_write(dbase, data)
        uc.mem_write(RET, b'\xfe\xe7')
        uc.mem_write(RECORD + 8, struct.pack('<I', WRITE_FN | 1))
        rng = random.Random(seed)
        self.disk = {dev: [bytes(rng.getrandbits(8) for _ in range(512)) for _ in range(SECTORS)]
                     for dev in (SYS, DATA, OTHER)}
        self.reads, self.failures = [], {}
        uc.hook_add(UC_HOOK_CODE, self._hook)

    def _return(self, value):
        self.uc.reg_write(UC_ARM_REG_R0, value & 0xFFFFFFFF)
        self.uc.reg_write(UC_ARM_REG_PC, self.uc.reg_read(UC_ARM_REG_LR))

    def _hook(self, uc, address, size, _):
        if address == RET:
            uc.emu_stop()
        elif address in (ISR_OFF, ISR_ON):
            self._return(0)
        elif address == MDREAD:
            dev, sector, count, dst = (uc.reg_read(r) for r in
                                       (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
            self.reads.append((dev, sector, count))
            if self.failures.get((dev, sector)) or sector + count > SECTORS:
                self.failures[(dev, sector)] = self.failures.get((dev, sector), 1) - 1
                return self._return(-1)
            uc.mem_write(dst, b''.join(self.disk[dev][sector:sector + count]))
            self._return(0)
        elif address == DISPATCH:
            self._return(RECORD)
        elif address == WRITE_FN:
            # Device record write method: (subdevice byte, sector, count, source).
            sub, sector, count, src = (uc.reg_read(r) for r in
                                       (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
            blob = bytes(uc.mem_read(src, count * 512))
            dev = 0x00030000 | sub
            for i in range(count):
                self.disk[dev][sector + i] = blob[i * 512:(i + 1) * 512]
            self._return(0)

    def call(self, entry, *args):
        uc = self.uc
        for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3), args):
            uc.reg_write(reg, value)
        uc.reg_write(UC_ARM_REG_SP, STACK)
        uc.reg_write(UC_ARM_REG_LR, RET | 1)
        uc.emu_start(entry | 1, RET, count=2_000_000)
        return uc.reg_read(UC_ARM_REG_R0)

    def read(self, dev, offset, length):
        self.uc.mem_write(BUF, b'\xcc' * length)
        result = self.call(READER, dev, offset, length, BUF)
        return result, bytes(self.uc.mem_read(BUF, length))

    def write(self, dev, sector, blob):
        self.uc.mem_write(BUF + 0x8000, blob)
        return self.call(WRITER, dev, sector, len(blob) // 512, BUF + 0x8000)

    def truth(self, dev, offset, length):
        return b''.join(self.disk[dev])[offset:offset + length]


def random_ops(seed, count):
    rng = random.Random(seed)
    ops = []
    for _ in range(count):
        dev = rng.choice((SYS, SYS, SYS, DATA, DATA, OTHER))
        if rng.random() < 0.1:
            ops.append(('write', dev, rng.randrange(SECTORS - 2), rng.randrange(1, 3), rng.getrandbits(32)))
            continue
        length = rng.choice((2, 34, 33, 480, 511, 512, 700, 1024, 1500))
        offset = rng.randrange(SECTORS * 512 - length)
        if rng.random() < 0.2:
            offset -= offset % 512
        ops.append(('read', dev, offset, length))
    return ops


class SysdiskCache(unittest.TestCase):
    def run_ops(self, patched, ops):
        m = Machine(patched)
        results = []
        for op in ops:
            if op[0] == 'write':
                _, dev, sector, n, seed = op
                blob = random.Random(seed).randbytes(n * 512)
                results.append(('w', m.write(dev, sector, blob)))
                continue
            _, dev, offset, length = op
            result, got = m.read(dev, offset, length)
            self.assertEqual(got, m.truth(dev, offset, length), op)
            results.append(('r', result))
        return results, m.reads

    def test_random_reads_and_writes_return_disk_bytes(self):
        for seed in range(6):
            with self.subTest(seed=seed):
                ops = random_ops(seed, 300)
                stock, stock_reads = self.run_ops(False, ops)
                fast, fast_reads = self.run_ops(True, ops)
                self.assertEqual(fast, stock)
                sys_stock = sum(1 for d, *_ in stock_reads if d == SYS)
                sys_fast = sum(1 for d, *_ in fast_reads if d == SYS)
                self.assertLess(sys_fast, sys_stock)
                # Other devices keep the stock uncached path exactly.
                self.assertEqual([r for r in fast_reads if r[0] == OTHER],
                                 [r for r in stock_reads if r[0] == OTHER])

    def test_failed_system_read_is_retried_once(self):
        for patched in (False, True):
            with self.subTest(patched=patched):
                m = Machine(patched)
                m.failures[(SYS, 5)] = 1
                result, got = m.read(SYS, 5 * 512 + 40, 34)
                self.assertEqual(result, 0)
                self.assertEqual(got, m.truth(SYS, 5 * 512 + 40, 34))
                self.assertEqual(m.reads, [(SYS, 5, 1), (SYS, 5, 1)])

    def test_successful_retry_is_cached(self):
        m = Machine(True)
        m.failures[(SYS, 7)] = 1
        self.assertEqual(m.read(SYS, 7 * 512, 34)[0], 0)
        m.reads.clear()
        m.read(SYS, 7 * 512 + 100, 34)
        self.assertEqual(m.reads, [])

    def test_failed_read_is_not_cached(self):
        for patched in (False, True):
            with self.subTest(patched=patched):
                m = Machine(patched)
                m.failures[(SYS, 7)] = 2
                self.assertEqual(m.read(SYS, 7 * 512, 34)[0], 0xFFFFFFFF)
                m.reads.clear()
                self.assertEqual(m.read(SYS, 7 * 512, 34), (0, m.truth(SYS, 7 * 512, 34)))
                self.assertEqual(m.reads, [(SYS, 7, 1)])

    def test_cache_hit_skips_the_sector_read(self):
        m = Machine(True)
        m.read(SYS, 3 * 512 + 10, 34)
        m.reads.clear()
        result, got = m.read(SYS, 3 * 512 + 200, 34)
        self.assertEqual((result, got, m.reads), (0, m.truth(SYS, 3 * 512 + 200, 34), []))

    def test_write_invalidates_a_cached_system_sector(self):
        m = Machine(True)
        m.read(SYS, 9 * 512, 34)
        self.assertEqual(m.write(SYS, 9, b'\x5a' * 512), 0)
        self.assertEqual(m.read(SYS, 9 * 512, 34)[1], b'\x5a' * 34)

    def test_system_and_data_tags_never_alias(self):
        m = Machine(True)
        m.read(SYS, 4 * 512, 34)
        m.reads.clear()
        self.assertEqual(m.read(DATA, 4 * 512, 34)[1], m.truth(DATA, 4 * 512, 34))
        self.assertEqual(m.reads, [(DATA, 4, 1)])
        tags = struct.unpack('<3I', m.uc.mem_read(FLASH_SEC, 12))
        self.assertIn(0x80000004, tags)
        self.assertIn(4, tags)

    def test_unaligned_read_into_whole_sectors(self):
        m = Machine(True)
        result, got = m.read(SYS, 2 * 512 + 300, 212 + 1024 + 50)
        self.assertEqual((result, got), (0, m.truth(SYS, 2 * 512 + 300, 212 + 1024 + 50)))
        self.assertIn((SYS, 3, 2), m.reads)   # the whole-sector read used an untagged sector

    def test_ui_traces_need_fewer_sector_reads(self):
        """Glyph records are 33 bytes from the font base; a 34-byte read each."""
        image = Image((ROOT / 'DP3_V137.img').read_bytes())
        font = image.sections['font_a']['offset']
        rows = ['02 - Another Track Name.flac', '03 - A Much Longer Title That Will Need To Scroll']
        now_playing = ['A Much Longer Title That Will Need To Scroll', 'Artist Name', 'Album Name',
                       '01:23', '04:56']
        for name, strings in (('wheel step', rows), ('now playing', now_playing)):
            glyphs = [(font + ord(ch) * 33) for s in strings for ch in s] * 2   # measure, then draw
            counts = {}
            for patched in (False, True):
                m = Machine(patched)
                m.disk[SYS] = [bytes(512)] * ((font + 0x10000) // 512 + 2)
                globals()['SECTORS'] = len(m.disk[SYS])
                for offset in glyphs:
                    m.read(SYS, offset, 34)
                counts[patched] = len(m.reads)
            globals()['SECTORS'] = 64
            print(f'{name}: {len(glyphs)} glyph reads, sector reads {counts[False]} -> {counts[True]}')
            self.assertLess(counts[True] * 2, counts[False])


if __name__ == '__main__':
    unittest.main()
