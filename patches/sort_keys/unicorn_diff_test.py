#!/usr/bin/env python3
"""Differential test: device Thumb-2 routines (under Unicorn) vs host_ref.

Emulates sk_tcmp and sk_pfx4 from cave.bin — the two pure subroutines at
the heart of the patch (the wrappers cave_cmp/cave_pfx additionally do a
database read via 0x03067510, which is not emulated; they are verified by
disassembly + the framework build).

Checks:
  * sk_tcmp(bufA, bufB) == host tcmp for the vector suite and a large
    randomized corpus (buffers filled with garbage past the NUL, like the
    real flash slots).
  * sk_pfx4(record, buf) writes exactly host pfx4's units at record+4.
  * full device_cmp model (prefix phase over the emulated pfx4 output +
    emulated sk_tcmp) == host device_cmp.

Run after sortkey_asm.py: venv/bin/python unicorn_diff_test.py
"""
import random
import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_SP

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from host_ref import device_cmp, gen_units, pfx4, tcmp  # noqa: E402
from sortkey_asm import BASE, build  # noqa: E402

RAM = 0x02000000
RAM_SIZE = 0x100000
STACK_TOP = RAM + RAM_SIZE - 0x1000
BUFA = RAM + 0x1000
BUFB = RAM + 0x2000
REC = RAM + 0x3000
SENTINEL = RAM + 0x800          # mapped return trampoline address


def make_uc(symbols):
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    uc.mem_map(RAM, RAM_SIZE)
    cave_addr = BASE & ~0xFFFFF
    uc.mem_map(cave_addr, 0x100000)
    blob, _, _ = build()
    uc.mem_write(BASE, blob)
    return uc


def call(uc, addr, r0=0, r1=0):
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_R0, r0)
    uc.reg_write(UC_ARM_REG_R1, r1)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL | 1)
    uc.emu_start(addr | 1, SENTINEL, count=200000)
    return uc.reg_read(UC_ARM_REG_R0)


def name_buffer(rng, name):
    """0x100-byte flash-slot image: UTF-16LE units, NUL, garbage tail."""
    units = [ord(c) for c in name] if isinstance(name, str) else list(name)
    buf = bytearray(rng.randrange(256) for _ in range(0x100))
    for i, u in enumerate(units[:127]):
        struct.pack_into('<H', buf, i * 2, u)
    if len(units) < 128:
        struct.pack_into('<H', buf, len(units) * 2, 0)
    return bytes(buf)


def main():
    blob, symbols, _ = build()
    print(f'cave blob {len(blob)} bytes; symbols: ' +
          ', '.join(f'{k}={v:#x}' for k, v in symbols.items() if not k.startswith('c') or k in ('cave_cmp', 'cave_pfx')))
    uc = make_uc(symbols)
    rng = random.Random(424242)
    fails = 0

    def check(cond, msg):
        nonlocal fails
        if not cond:
            fails += 1
            print('FAIL:', msg)

    corpus = ['The Beatles', 'Beach House', 'track 2', 'Track 10', 'Émile',
              'Emma', 'Beyoncé', 'Beyonce', 'Björk', 'Track 02', 'Track 2',
              '2Pac', '10cc', 'Weiß', 'Weiss', 'Æsop', 'Aesop', 'Café',
              'Café', 'The 39 Steps', '39 Steps', 'ab12', 'ab123',
              'ab9x', 'Song 007', 'Song 7', 'The', 'Theodore', '中文歌',
              '', '   ', 'A', 'a01', 'a1', 'Ñandú', 'Nana', 'Vol 2', 'Vol 10',
              '123', '1234', 'x1y2', 'x1y10', 'Song 07a', 'The The',
              '  The   Beatles  ', 'Œuvre', 'Oeuvre', 'ZZ Top', '9 Songs']
    alphabet = (list('aAbBzZtThHeE ') + list('0123456789') +
                ['é', 'É', 'ö', 'ß', 'Æ', 'ñ', '́', '中', 'x', 'X', '.'])
    words = ['the', 'The', 'THE', 'track', 'Track', 'Beach', 'Beatles', '']
    for _ in range(300):
        n = ''.join(rng.choice(alphabet) for _ in range(rng.randrange(0, 12)))
        if rng.random() < 0.4:
            n = rng.choice(words) + ' ' + n
        corpus.append(n)

    # --- sk_tcmp vs tcmp, and device model (emulated pfx4 + tcmp) ---
    for i, a in enumerate(corpus):
        for b in corpus[max(0, i - 3):i + 4]:
            uc.mem_write(BUFA, name_buffer(rng, a))
            uc.mem_write(BUFB, name_buffer(rng, b))
            got = call(uc, symbols['sk_tcmp'], BUFA, BUFB)
            got = got - 0x100000000 if got >= 0x80000000 else got
            want = tcmp(a, b)
            check(got == want, f'sk_tcmp {a!r} vs {b!r}: device {got} != host {want}')
            # emulated pfx4 for both, then host prefix phase on the results
            uc.mem_write(REC, bytes(14))
            call(uc, symbols['sk_pfx4'], REC, BUFA)
            pa = list(struct.unpack_from('<4H', uc.mem_read(REC + 4, 8)))
            uc.mem_write(REC, bytes(14))
            call(uc, symbols['sk_pfx4'], REC, BUFB)
            pb = list(struct.unpack_from('<4H', uc.mem_read(REC + 4, 8)))
            check(pa == pfx4(a), f'sk_pfx4 {a!r}: device {pa} != host {pfx4(a)}')
            check(pb == pfx4(b), f'sk_pfx4 {b!r}: device {pb} != host {pfx4(b)}')
            # device model on emulated prefixes
            d = None
            for j in range(4):
                ua, ub = pa[j], pb[j]
                if ua == 1 or ub == 1:
                    d = want
                    break
                if ua != ub:
                    d = -1 if ua < ub else 1
                    break
                if ua == 0:
                    d = 0
                    break
            if d is None:
                d = want
            check(d == device_cmp(a, b) == want,
                  f'device model {a!r} vs {b!r}: {d} != {device_cmp(a, b)}')
    print(f'{fails} failure(s) over {len(corpus)} names')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
