"""Distinguish OpusHead from Vorbis in the stock Ogg content detector.

The first extension lookup is not final: 0x03067F50 reads the file and
rewrites every OggS stream to OGG before the second codec lookup. Standard
CE's removed ASF tag case provides the bounded prefix-check home. The
signature loop uses a separately censused resident pocket.
"""
import sys
from pathlib import Path
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'patches/full/build')]
from rknano_image import Image
from build_tail import branch

PREFIX, SIGNATURE, HOOK = 0x0306C5B0, 0x03065534, 0x03068452
RESET_SEEK, STOCK_OGG = 0x030684C6, 0x030684A6


def assemble():
    ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
    prefix = bytes(ks.asm(f'''
        mov r0,r8;adds r0,#27;cmp r0,#512;bhi fallback;
        ldrb r1,[r4,#26];cbz r1,fallback;
        mov r2,r4;adds r2,#27;add r2,r1;
        add r0,r1;adds r0,#19;cmp r0,#512;bhi fallback;
        ldrb r0,[r4,#4];cbnz r0,fallback;
        ldrb r0,[r4,#5];and r0,r0,#3;cmp r0,#2;bne fallback;
        ldrb r0,[r4,#27];cmp r0,#19;blo fallback;
        b.w {SIGNATURE};
    fallback:
        movs r0,#79;strb r0,[r5];movs r0,#71;strb r0,[r5,#1];
        b.w {STOCK_OGG}
    ''', PREFIX)[0])
    fallback = PREFIX + len(prefix) - 12
    signature = bytes(ks.asm(f'''
        adr r3,magic;movs r1,#8;
    again:
        ldrb r0,[r2],#1;ldrb r12,[r3],#1;cmp r0,r12;
        beq equal_byte;b.w {fallback};
    equal_byte:
        subs r1,#1;bne again;
        movs r0,#79;strb r0,[r5];movs r0,#80;strb r0,[r5,#1];
        movs r0,#85;strb r0,[r5,#2];b.w {RESET_SEEK};
        .balign 4,0;
    magic:
        .ascii "OpusHead"
    ''', SIGNATURE)[0])
    assert len(prefix) <= 106 and len(signature) <= 68
    assert prefix[-12:-10] == b'\x4f\x20', 'fallback offset changed'
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    externals = {SIGNATURE, fallback, STOCK_OGG, RESET_SEEK}
    for base, code in ((PREFIX, prefix), (SIGNATURE, signature[:-8])):
        for insn in decoder.disasm(code, base):
            if insn.mnemonic.startswith('b') and insn.op_str.startswith('#'):
                target = int(insn.op_str[1:], 16)
                assert base <= target < base + len(code) or target in externals, (insn, target)
    return prefix, signature


def main():
    raw = (ROOT / 'DP3_V137.img').read_bytes()
    image = Image(raw)
    offset, _ = image.module_region(0, 'code')
    base = image.modules[0]['code_exec']
    prefix, signature = assemble()
    for number, label, address, code in (
            (263, 'prefix', PREFIX, prefix), (264, 'signature', SIGNATURE, signature),
            (265, 'hook', HOOK, branch(HOOK, PREFIX))):
        name = f'{number:04d}-opus-content-{label}'
        expected = raw[offset + address - base:offset + address - base + len(code)]
        (HERE / (name + '.patch')).write_text(
            f'# Opus content routing: {label}.\nname: {name}\nkind: module\nmodule: 0\nregion: code\naddress: {address:#x}\n'
            f'expect: {expected.hex()}\nreplace: {code.hex()}\n'
            'gate: stock bytes; content-detector Opus/Vorbis negative control, read bounds and codec-loader regression\n'
            'rationale: The stock file-content probe overwrites OPU with OGG for every OggS stream. Recognize a bounded BOS OpusHead packet before that overwrite; retain native Vorbis detection and the original final seek reset. Requires Standard CE OpusTags routing, which releases the ASF-specific tag case.\n')
    print(f'Opus content routing: prefix {len(prefix)} bytes; signature {len(signature)} bytes')


if __name__ == '__main__':
    main()
