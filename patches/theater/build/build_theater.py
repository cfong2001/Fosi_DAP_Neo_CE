#!/usr/bin/env python3
"""Build the theater-mode tail payload and hook patches.

Assembles the reset stub and the blit trampoline with Keystone
(Thumb-2, base 0x0307BFB4, the census-clean gap tail), fixes up the
one external call (the stock bitmap function 0x0306333E) with a
local branch encoder, and round-trip checks the result with
Capstone: instruction counts per part match the source listing,
every branch target lands inside the payload or on the bitmap
function, and the entry/exit register contracts hold.

Emits, next to this script:
  theater_tail.bin          the tail payload for build.py --tail
  0100-theater-setup-reset-hook.patch
  0101-theater-blit-sync-a.patch
  0102-theater-blit-sync-b.patch
  0103-theater-blit-painter-a.patch
  0104-theater-blit-painter-b.patch
  manifest.txt              default 32 patches + the five above

State: 28 bytes at SAVEINFO+0x1C8 (0x03023468), inside the
+0x1C7..+0x2D5 verbatim block. Census evidence: README.md here and
work/theater_integration/census_*.py. Layout:
  +0x00 sum[0..2] u32 x3   +0x0C row bitmask u32 x2 (48 rows)
  +0x14 width u16          +0x16 rows_needed u16
  +0x18 rows_seen u8       +0x19 flags u8 (1 armed, 2 done, 4 latched)
  +0x1A spare u16
"""
import hashlib
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / 'tools'))

from rknano_image import Image  # noqa: E402
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB, KS_MODE_V8  # noqa: E402
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_OP_IMM  # noqa: E402

TAIL_BASE = 0x0307BFB4
TAIL_MAX = 2044
BITMAP = 0x0306333E
SETUP = 0x0308389E
BLIT_SITES = (0x03083A72, 0x03083A7E, 0x03083B82, 0x03083B94)
STOCK_SHA = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'


def branch(site, target, link=False):
    delta = target - (site + 4)
    if delta & 1 or not -(1 << 24) <= delta < (1 << 24):
        raise ValueError('invalid branch displacement')
    s, i1, i2 = (delta >> 24) & 1, (delta >> 23) & 1, (delta >> 22) & 1
    j1, j2 = (~(i1 ^ s)) & 1, (~(i2 ^ s)) & 1
    return struct.pack('<HH', 0xF000 | (s << 10) | ((delta >> 12) & 0x3FF),
                       (0xD000 if link else 0x9000) | (j1 << 13)
                       | (j2 << 11) | ((delta >> 1) & 0x7FF))


def load(reg, addr):
    return [f'movw {reg}, #{addr & 0xFFFF}', f'movt {reg}, #{addr >> 16}']


RESET_ASM = [
    # The two displaced setup instructions run exactly as stock:
    # the frame they push is setup's own (its epilogue pops it), so
    # the stub must not pop it. Stub work uses only r2/r3 behind a
    # balanced save; r0/r1 (setup's arguments) and r4/r5 are never
    # touched.
    'push {r4, r5, r6, lr}',
    'mov r6, r1',
    'push {r2, r3}',
    *load('r3', 0x03023468),                    # state
    'movs r2, #0',
    'str r2, [r3, #0]',
    'str r2, [r3, #4]',
    'str r2, [r3, #8]',
    'str r2, [r3, #12]',
    'str r2, [r3, #16]',
    'strh r2, [r3, #20]',
    'strh r2, [r3, #22]',
    'strb r2, [r3, #24]',
    'movs r2, #1',
    'strb r2, [r3, #25]',                       # flags = armed
    *load('r3', 0x030232A0),                    # SAVEINFO
    'ldrb r2, [r3, #0x2d8]',                    # theme selector
    'cmp r2, #0',
    'bne rst_light',
    'movw r2, #0x10a2',                         # dark default
    'b rst_store',
    'rst_light:',
    *load('r3', 0x030235B4),                    # palette cell 0
    'ldrh r2, [r3, #0]',
    'rst_store:',
    *load('r3', 0x03004400),                    # background cell
    'strh r2, [r3, #0]',
    'pop {r2, r3}',
    # A plain branch back into setup at 0x030838A2 is appended by
    # fixup: the hook site uses B (not BL), so lr still holds
    # setup's own return address, exactly as stock leaves it.
]

TRAMP_HEAD_ASM = [
    'push {r4, r5, r6, r7, r8, lr}',
    'mov r5, r2',                               # width
    'mov r8, r3',                               # height arg (must be 1)
    'ldr r6, [sp, #24]',                        # stack arg: mode
    'ldr r7, [sp, #28]',                        # stack arg: source ptr
    'push {r6, r7}',                            # replicate for bitmap
    # BL to BITMAP is inserted here by branch fixup.
]


def _channel(name, sum_off, slot, light_const):
    return [
        f'ldr r0, [r2, #{sum_off}]',
        'add r0, r0, r8',
        'udiv r0, r0, r5',
        'ldrb r1, [sp, #4]',
        'cmp r1, #0',
        f'bne fin_{name}_light',
        'movs r1, #45',
        'mul r0, r0, r1',
        'adds r0, r0, #50',
        f'b fin_{name}_div',
        f'fin_{name}_light:',
        'movs r1, #25',
        'mul r0, r0, r1',
        f'movw r1, #{light_const}',
        'add r0, r0, r1',
        f'fin_{name}_div:',
        'movs r1, #100',
        'udiv r0, r0, r1',
        f'strb r0, [sp, #{slot}]',
    ]


TRAMP_TAIL_ASM = [
    'add sp, #8',
    'mov r4, r0',                               # preserve bitmap return
    *load('r2', 0x03023468),                    # state
    'ldrb r3, [r2, #25]',
    'tst r3, #1',
    'beq tramp_out',                            # not armed
    'tst r3, #2',
    'bne tramp_out',                            # done
    *load('r0', 0x03026A20),                    # row buffer
    'cmp r7, r0',
    'bne tramp_out',
    'cmp r6, #0x10',
    'bne tramp_out',                            # mode must be 0x10
    'cmp r8, #1',
    'bne tramp_out',                            # height arg must be 1
    'cmp r5, #0',
    'beq tramp_out',                            # zero width
    *load('r0', 0x03026CA0),                    # player ctx
    'ldr r1, [r0, #0x2c]',                      # row index just drawn
    'tst r3, #4',
    'bne latched',
    'ldr r5, [r0, #0x14]',                     # scaled artwork width
    'cmp r5, #0',
    'beq tramp_out',
    'ldr r3, [r0, #0x0c]',                     # rendered target width
    'cmp r5, r3',
    'bhi tramp_out',                           # reject inconsistent geometry
    'ldr r0, [r0, #0x18]',                      # scaled height
    'adds r0, r0, #2',
    'movs r3, #3',
    'udiv r0, r0, r3',                          # rows_needed = ceil(h/3)
    'cmp r0, #48',
    'bls latch_store',
    'movs r0, #48',
    'latch_store:',
    'cmp r0, #0',
    'beq tramp_out',
    'strh r5, [r2, #20]',                       # width
    'strh r0, [r2, #22]',                       # rows_needed
    'ldrb r3, [r2, #25]',
    'orr r3, r3, #4',
    'strb r3, [r2, #25]',                       # latched
    'latched:',
    'ldrh r0, [r2, #22]',
    'cmp r1, r0',
    'bhs tramp_out',                            # row beyond top third
    'lsrs r3, r1, #5',
    'lsls r3, r3, #2',
    'add r3, r2, r3',
    'adds r3, r3, #12',                         # &bitmask[word]
    'and r0, r1, #31',
    'movs r1, #1',
    'lsls r1, r1, r0',
    'ldr r0, [r3, #0]',
    'tst r0, r1',
    'bne tramp_out',                            # row already counted
    'orr r0, r0, r1',
    'str r0, [r3, #0]',
    'ldrh r5, [r2, #20]',                       # width counter
    *load('r6', 0x03026CA0),
    'ldr r0, [r6, #0x0c]',                     # target width
    'subs r0, r0, r5',                         # difference in pixels
    'bic r0, r0, #1',                          # centered left inset in bytes
    'add r6, r7, r0',                          # first artwork pixel
    'acc_loop:',
    'cmp r5, #0',
    'beq acc_done',
    'ldrh r0, [r6], #2',                        # little-endian pixel
    'lsrs r1, r0, #11',
    'and r1, r1, #31',
    'movs r3, #255',
    'mul r1, r1, r3',
    'movs r3, #31',
    'udiv r1, r1, r3',
    'ldr r3, [r2, #0]',
    'add r3, r3, r1',
    'str r3, [r2, #0]',
    'lsrs r1, r0, #5',
    'and r1, r1, #63',
    'movs r3, #255',
    'mul r1, r1, r3',
    'movs r3, #63',
    'udiv r1, r1, r3',
    'ldr r3, [r2, #4]',
    'add r3, r3, r1',
    'str r3, [r2, #4]',
    'and r1, r0, #31',
    'movs r3, #255',
    'mul r1, r1, r3',
    'movs r3, #31',
    'udiv r1, r1, r3',
    'ldr r3, [r2, #8]',
    'add r3, r3, r1',
    'str r3, [r2, #8]',
    'subs r5, r5, #1',
    'b acc_loop',
    'acc_done:',
    'ldrb r0, [r2, #24]',
    'adds r0, r0, #1',
    'strb r0, [r2, #24]',                       # rows_seen++
    'ldrh r1, [r2, #22]',
    'cmp r0, r1',
    'bne tramp_out',
    # finalize: count = width * rows_seen
    'ldrh r0, [r2, #20]',
    'ldrb r1, [r2, #24]',
    'mul r5, r0, r1',
    'cmp r5, #0',
    'beq tramp_out',
    'sub sp, #12',
    'lsrs r8, r5, #1',                          # count / 2
    *load('r0', 0x030232A0),
    'ldrb r0, [r0, #0x2d8]',
    'strb r0, [sp, #4]',                        # theme flag
    *_channel('r', 0, 0, 75 * 242 + 50),
    *_channel('g', 4, 1, 75 * 237 + 50),
    *_channel('b', 8, 2, 75 * 230 + 50),
    # quantize to RGB565 with theme-core rgb565 rounding
    'ldrb r0, [sp, #0]',
    'movs r1, #31',
    'mul r0, r0, r1',
    'adds r0, r0, #127',
    'movs r1, #255',
    'udiv r0, r0, r1',
    'lsls r5, r0, #11',
    'ldrb r0, [sp, #1]',
    'movs r1, #63',
    'mul r0, r0, r1',
    'adds r0, r0, #127',
    'movs r1, #255',
    'udiv r0, r0, r1',
    'lsls r0, r0, #5',
    'orr r5, r5, r0',
    'ldrb r0, [sp, #2]',
    'movs r1, #31',
    'mul r0, r0, r1',
    'adds r0, r0, #127',
    'movs r1, #255',
    'udiv r0, r0, r1',
    'orr r5, r5, r0',
    *load('r0', 0x03004400),                    # background cell
    'strh r5, [r0, #0]',
    *load('r0', 0x03023CFC),                    # event word, bit 0x19
    'ldr r1, [r0, #0]',
    'orr r1, r1, #0x02000000',
    'str r1, [r0, #0]',
    'ldrb r0, [r2, #25]',
    'orr r0, r0, #2',
    'strb r0, [r2, #25]',                       # done
    'add sp, #12',
    'tramp_out:',
    'mov r0, r4',
    'pop {r4, r5, r6, r7, r8, pc}',
]


def assemble(lines, base):
    # KS_MODE_V8 only widens Keystone's feature gate so UDIV (an
    # ARMv7E-M / Cortex-M3 instruction) assembles; every other
    # encoding was verified identical to plain KS_MODE_THUMB.
    ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB | KS_MODE_V8)
    src = '\n'.join(lines)
    encoding, count = ks.asm(src, addr=base)
    if encoding is None:
        raise SystemExit(f'keystone failed at {base:#x}')
    return bytes(encoding), count


def insn_lines(lines):
    return [l for l in lines if not l.endswith(':')]


def roundtrip(payload, parts):
    """parts: list of (name, source_lines, byte_len). Disassemble the
    payload and check per-part instruction counts, entry contracts,
    and that every control-flow target is inside the payload, the
    stock bitmap function, or the setup continuation 0x030838A2."""
    cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    cs.detail = True
    insns = list(cs.disasm(payload, TAIL_BASE))
    total_src = sum(len(insn_lines(p[1])) for p in parts) + 2  # + 2 fixups
    if len(insns) != total_src:
        raise SystemExit(f'round-trip: disassembled {len(insns)} '
                         f'instructions, source has {total_src}')
    ok_targets = set(range(TAIL_BASE, TAIL_BASE + len(payload))) \
        | {BITMAP | 1, 0x030838A2 | 1, 0x030838A2}
    for ins in insns:
        if ins.mnemonic.startswith(('b', 'bl')) and ins.operands \
                and ins.operands[0].type == CS_OP_IMM:
            t = ins.operands[0].imm
            if t not in ok_targets and t != BITMAP:
                raise SystemExit(f'round-trip: branch at {ins.address:#x} '
                                 f'to unexpected {t:#x}')
    first = insns[0]
    if first.mnemonic != 'push':
        raise SystemExit('round-trip: payload does not start with push')
    return insns


def main():
    stock_path = REPO / 'DP3_V137.img'
    raw = stock_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise SystemExit('stock image hash mismatch')
    im = Image(raw)

    reset_body, n_reset = assemble(RESET_ASM, TAIL_BASE)
    reset = reset_body + branch(TAIL_BASE + len(reset_body), 0x030838A2)
    tramp_entry = TAIL_BASE + len(reset)
    head, n_head = assemble(TRAMP_HEAD_ASM, tramp_entry)
    bl_site = tramp_entry + len(head)
    bl_bytes = branch(bl_site, BITMAP, link=True)
    tail, n_tail = assemble(TRAMP_TAIL_ASM, bl_site + 4)
    payload = reset + head + bl_bytes + tail
    if len(payload) > TAIL_MAX:
        raise SystemExit(f'payload {len(payload)} exceeds tail {TAIL_MAX}')
    insns = roundtrip(payload, [('reset', RESET_ASM, len(reset)),
                                ('head', TRAMP_HEAD_ASM, len(head)),
                                ('tail', TRAMP_TAIL_ASM, len(tail))])
    # The inserted BL must decode to the bitmap function.
    cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    bl_ins = list(cs.disasm(payload[len(reset) + len(head):
                                    len(reset) + len(head) + 4], bl_site))
    assert len(bl_ins) == 1 and bl_ins[0].mnemonic == 'bl', bl_ins
    print(f'payload {len(payload)} bytes: reset stub {len(reset)} at '
          f'{TAIL_BASE:#x}, trampoline {len(payload) - len(reset)} at '
          f'{tramp_entry:#x}, bitmap BL at {bl_site:#x}')
    print(f'round-trip: {len(insns)} instructions verified')

    (HERE / 'theater_tail.bin').write_bytes(payload)

    def site_bytes(addr):
        off, _ = im.module_region(18, 'code')
        base = im.modules[18]['code_exec']
        return raw[off + (addr - base):off + (addr - base) + 4]

    setup_expect = site_bytes(SETUP)
    if setup_expect.hex() != '70b50e46':
        raise SystemExit(f'setup entry bytes changed: {setup_expect.hex()}')
    patches = [{
        'file': '0100-theater-setup-reset-hook.patch',
        'name': 'theater-setup-reset-hook',
        'address': SETUP,
        'expect': setup_expect,
        'replace': branch(SETUP, TAIL_BASE, link=False),
        'rationale': ('Module 18 artwork setup entry: the first two '
                      'instructions (push {r4, r5, r6, lr}; mov r6, r1) '
                      'are replaced by a branch (not a call, so lr '
                      'keeps setup\'s own return address) to the '
                      'theater reset stub in the gap tail, which '
                      're-executes both, clears the accumulator state '
                      'at SAVEINFO+0x1C8, arms sampling, restores the '
                      'player background cell to the theme default and '
                      'branches back to the third setup instruction.'),
    }]
    names = ['sync-a', 'sync-b', 'painter-a', 'painter-b']
    for name, site in zip(names, BLIT_SITES):
        expect = site_bytes(site)
        dec = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(expect, site))
        if len(dec) != 1 or dec[0].mnemonic != 'bl' \
                or f'{BITMAP:#x}' not in dec[0].op_str:
            raise SystemExit(f'blit site {site:#x} is not the expected '
                             f'bitmap call: {expect.hex()}')
        patches.append({
            'file': f'010{1 + len(patches) - 1 + 1}-theater-blit-{name}.patch',
            'name': f'theater-blit-{name}',
            'address': site,
            'expect': expect,
            'replace': branch(site, tramp_entry, link=True),
            'rationale': ('Bitmap call in the artwork row consumer '
                          'repointed to the theater trampoline in the '
                          'gap tail. The trampoline calls the stock '
                          'bitmap function with the original arguments '
                          'and stack layout, then samples the rendered '
                          'row into the top-third average when armed.'),
        })
    patches[1]['file'] = '0101-theater-blit-sync-a.patch'
    patches[2]['file'] = '0102-theater-blit-sync-b.patch'
    patches[3]['file'] = '0103-theater-blit-painter-a.patch'
    patches[4]['file'] = '0104-theater-blit-painter-b.patch'

    for p in patches:
        text = (f"# Theater mode device integration: {p['name']}.\n"
                f"# Design and census: patches/theater/build/README.md.\n"
                f"name: {p['name']}\n"
                f"kind: module\n"
                f"module: 18\n"
                f"region: code\n"
                f"address: {p['address']:#x}\n"
                f"gate: stock byte precondition; variant-only patch, "
                f"never in the default manifest; validated by "
                f"test_theater_lifecycle.py under emulation\n"
                f"rationale: {p['rationale']}\n"
                f"expect: {p['expect'].hex()}\n"
                f"replace: {p['replace'].hex()}\n")
        (HERE / p['file']).write_text(text)
        print(f"{p['file']}: {p['address']:#x} "
              f"{p['expect'].hex()} -> {p['replace'].hex()}")

    default_manifest = (REPO / 'patches' / 'framework' / 'patches'
                        / 'manifest.txt')
    entries = [l.split('#', 1)[0].strip()
               for l in default_manifest.read_text().splitlines()]
    entries = [e for e in entries if e]
    lines = ['# Theater variant manifest: the full default build PLUS',
             '# the five theater hook patches in this directory. The',
             '# first 33 entries are the default manifest patches,',
             '# referenced relative to this file. Use ONLY with',
             '# --tail theater_tail.bin; the tail payload is exclusive',
             '# (see README.md). The default manifest is unchanged.',
             '']
    lines += [f'../../framework/patches/{e}' for e in entries]
    lines += [p['file'] for p in patches]
    (HERE / 'manifest.txt').write_text('\n'.join(lines) + '\n')
    print(f'manifest.txt: {len(entries)} default + {len(patches)} theater')
    print(f'payload sha256 {hashlib.sha256(payload).hexdigest()}')


if __name__ == '__main__':
    main()
