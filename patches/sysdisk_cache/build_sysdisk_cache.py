#!/usr/bin/env python3
"""Cache system-disk sector reads in the block reader's existing buffers.

The block reader at 0x03067510 is the SDK's MDReadData. For the data disk
(device 0x00030001) it keeps three 512-byte sectors in FlashBuf
(0x03023D3C) tagged by FlashSec (0x03005878). For the system disk
(device 0x00030000), which holds the fonts and image resources, it reads a
whole sector for every request shorter than 512 bytes, copies the part
asked for and discards the sector. Every glyph, glyph width and partial
image row therefore costs one eMMC sector read with interrupts disabled.

These patches send system-disk partial reads through the same three-slot
cache. A system-disk sector's tag is its sector number with bit 31 set,
so it never equals a data-disk tag, a free slot (-1) or a real sector.

- 0290 is the code below.
- 0291 routes device 0x00030000 into the cached path with a tagged r4.
- 0292 clears bit 31 before the cached path calls MDRead, and keeps the
  stock system-disk retry of a failed read (stock retries once, at
  sector - RawOffset, where RawOffset is the zero word at [sp]).
- 0293 clears bit 31 before the multi-sector path, which a read reaches
  after an unaligned first sector.
- 0294 clears all three tags at the start of every device write
  (0x03067912), so a firmware update or database write is never served
  from a stale sector. Stock data-disk writers already clear them after
  writing.

The code lives in the unreached stock routine at 0x0306D450 (tier 1 in
patches/space/census.json, 740 bytes). No new RAM.
"""
from pathlib import Path
import hashlib
import sys

from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image  # noqa: E402

STOCK_SHA = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
HOME, HOME_END = 0x0306D450, 0x0306D734
MDREAD, ISR_OFF = 0x030678CA, 0x0306660A
CACHED, UNCACHED = 0x0306756A, 0x03067604
FLASH_SEC = 0x03005878

SITE_ROUTE = 0x03067562    # ldr r1,=0x30001 ; ldr r0,[sp,#0xc]
SITE_READ = 0x030675E0     # mov r1,r4 ; ldr r0,[sp,#0xc] ; bl MDRead
SITE_MULTI = 0x0306767A    # lsrs r5,r6,#9 ; cmp r5,r7
SITE_WRITE = 0x0306792E    # bl UserIsrDisable

PIECES = {
    'route': f"""
    ldr r0, [sp, #0xc]
    ldr r1, =0x00030001
    cmp r0, r1
    beq cached
    cmp.w r0, #0x30000
    beq tag
    b.w {UNCACHED:#x}
tag:
    orr r4, r4, #0x80000000
cached:
    b.w {CACHED:#x}
    .ltorg
""",
    'read': f"""
    push {{r2, r3, lr}}
    bic r1, r4, #0x80000000
    ldr r0, [sp, #0x18]
    bl {MDREAD:#x}
    cbz r0, done
    ldr r0, [sp, #0x18]
    cmp.w r0, #0x30000
    bne done
    ldr r0, [sp, #0xc]
    bic r1, r4, #0x80000000
    subs r1, r1, r0
    ldm sp, {{r2, r3}}
    ldr r0, [sp, #0x18]
    bl {MDREAD:#x}
done:
    pop {{r2, r3, pc}}
""",
    'multi': """
    bic r4, r4, #0x80000000
    lsrs r5, r6, #9
    cmp r5, r7
    bx lr
""",
    'write': f"""
    ldr r0, ={FLASH_SEC:#x}
    mov.w r1, #-1
    str r1, [r0]
    str r1, [r0, #4]
    str r1, [r0, #8]
    b.w {ISR_OFF:#x}
    .ltorg
""",
}


def assemble(source, address):
    code, _ = Ks(KS_ARCH_ARM, KS_MODE_THUMB).asm(source, address)
    return bytes(code)


def cave():
    """Lay the pieces out from HOME, each 4-byte aligned; return the bytes and each entry."""
    code, at = b'', {}
    for name, source in PIECES.items():
        code += b'\x00\xbf' * ((-len(code) % 4) // 2)
        at[name] = HOME + len(code)
        code += assemble(source, at[name])
    return code, at


def patches():
    code, at = cave()
    assert HOME + len(code) <= HOME_END, len(code)
    nop = b'\x00\xbf'
    return [
        ('0290-sysdisk-cache-code', HOME, code),
        ('0291-sysdisk-cache-route', SITE_ROUTE, assemble(f"b.w {at['route']:#x}", SITE_ROUTE)),
        ('0292-sysdisk-cache-read', SITE_READ, assemble(f"bl {at['read']:#x}", SITE_READ) + nop + nop),
        ('0293-sysdisk-cache-multi', SITE_MULTI, assemble(f"bl {at['multi']:#x}", SITE_MULTI)),
        ('0294-sysdisk-cache-write', SITE_WRITE, assemble(f"bl {at['write']:#x}", SITE_WRITE)),
    ]


RATIONALE = {
    '0290-sysdisk-cache-code': 'Cache code in the unreached stock routine at 0x0306D450 (census tier 1).',
    '0291-sysdisk-cache-route': 'Send system-disk partial reads into the stock three-slot cache with a bit-31 tag.',
    '0292-sysdisk-cache-read': 'Strip the tag before MDRead and keep the stock system-disk single retry.',
    '0293-sysdisk-cache-multi': 'Strip the tag before the multi-sector path.',
    '0294-sysdisk-cache-write': 'Clear every cache tag at the start of each device write.',
}


def main():
    raw = (ROOT / 'DP3_V137.img').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == STOCK_SHA, 'stock SHA drift'
    image = Image(raw)
    offset, size = image.module_region(0, 'code')
    base = image.modules[0]['code_exec']
    for name, address, code in patches():
        assert base <= address and address + len(code) <= base + size
        expect = raw[offset + address - base:offset + address - base + len(code)]
        (HERE / (name + '.patch')).write_text(
            '# Generated by build_sysdisk_cache.py.\n'
            f'name: {name}\nkind: module\nmodule: 0\nregion: code\naddress: {address:#x}\n'
            'gate: pinned stock bytes; block reader emulation in test_sysdisk_cache.py\n'
            f'expect: {expect.hex()}\nreplace: {code.hex()}\n'
            f'rationale: {RATIONALE[name]}\n')
        print(f'{name}: {len(code)} bytes at {address:#x}')


if __name__ == '__main__':
    main()
