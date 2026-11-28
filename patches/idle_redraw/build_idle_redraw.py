"""Skip the once-a-second progress-bar and transport repaint when nothing moved.

Each time the displayed elapsed second changes, the player's 0x40 segment
posts 0x4D. The 0x4D segment redraws the progress bar and then posts 0x43,
which redraws the whole transport row and the play-mode indicator. When the
bar position and the transport state are what the last 0x4D run drew, both
repaints write the pixels already on screen.

- tick_gate replaces that one post (BL at 0x0307F5BC). It posts 0x4D as
  stock unless the bar position it computes (the 0x4D segment's own formula
  and divide) equals the last stored one and the fingerprint (play state,
  transport state A and B) equals the one stored with it. It always posts
  in the two modes where the 0x4D segment computes differently or has side
  effects: seek preview (halfword 0x030247EA == 6) and the sub-track timebase
  (word 0x030239C4 == 1).
- fp_store replaces the 0x4D segment's second store of the position
  (0x0307F696, `str.w r0, [sb, #0x10]`). The word 0x030247F4 is written there
  and read nowhere else; it now holds the fingerprint of what was drawn.

Every other 0x4D and 0x43 poster (full repaint, seek, track change, keys,
playback engine) is unchanged.
"""
import hashlib
import sys
from pathlib import Path

from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'patches/full/build')]
from rknano_image import Image  # noqa: E402
from build_tail import branch  # noqa: E402

STOCK_SHA = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
# Unreached stock code (patches/space/census_dead.py). 0x03052F66..0x03052F8F
# holds patch 0276's rectangle table, so the first pocket starts after it.
# The other two are unreached stock functions: 0x030645B6 (census tier 2, a
# whole 42-byte function) and the head of 0x0305C9CE (tier 1).
FP, FP_END = 0x03052F90, 0x03052FB8
HEAD, HEAD_END = 0x030645B6, 0x030645E0
TAIL, TAIL_END = 0x0305C9CE, 0x0305C9FC
TICK_SITE, STORE_SITE = 0x0307F5BC, 0x0307F696
EVENT_SET, UDIV64 = 0x0306723C, 0x03054D90


def payloads():
    ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
    fp = bytes(ks.asm('''
    fingerprint:
        ldr r2, =0x03023924
        ldrh r1, [r2]
        ldr r3, =0x0302314A
        ldrh r3, [r3]
        orr.w r1, r1, r3, lsl #16
        ldr r3, =0x030247E4
        bx lr
    fp_store:
        push {r0, lr}
        bl fingerprint
        str r1, [r3, #0x10]
        pop {r0, pc}
        .ltorg
    ''', FP)[0])
    store = FP + 16                  # fp_store follows the 16-byte fingerprint
    assert fp[16:18] == b'\x01\xb5', fp[16:18].hex()   # push {r0, lr}
    # tick_gate, first half: the fingerprint and the two always-post modes.
    head = bytes(ks.asm(f'''
        push {{r4, lr}}
        bl {FP:#x}
        mov r4, r3
        ldr r0, [r4, #0x10]
        cmp r0, r1
        bne post
        ldrh r1, [r4, #6]
        cmp r1, #6
        beq post
        ldr.w r1, [r2, #0xA0]
        cmp r1, #1
        beq post
        b.w {TAIL:#x}
    post:
        movs r0, #0x4D
        pop.w {{r4, lr}}
        b.w {EVENT_SET:#x}
    ''', HEAD)[0])
    # Second half: the bar position, as the 0x4D segment computes it.
    tail = bytes(ks.asm(f'''
        ldr r1, =0x0304AD78
        ldr r1, [r1]
        ldrd r2, r0, [r1]
        movs r1, #0x93
        umull r0, r1, r0, r1
        movs r3, #0
        bl {UDIV64:#x}
        ldr r1, [r4, #0xC]
        cmp r0, r1
        it eq
        popeq {{r4, pc}}
        movs r0, #0x4D
        pop.w {{r4, lr}}
        b.w {EVENT_SET:#x}
        .ltorg
    ''', TAIL)[0])
    assert FP + len(fp) <= FP_END, len(fp)
    assert HEAD + len(head) <= HEAD_END, len(head)
    assert TAIL + len(tail) <= TAIL_END, len(tail)
    return fp, store, head, tail


def patches(raw):
    image = Image(raw)
    fp, store, head, tail = payloads()
    rows = (
        (350, 'idle-redraw-fingerprint', 0, FP, fp,
         'Fingerprint of the drawn transport state (play state, state A and B) and the store hook that keeps it beside the bar position.'),
        (351, 'idle-redraw-tick-gate', 0, HEAD, head,
         'First half of the gate on the per-second 0x4D: post when the transport fingerprint changed, or in seek preview or the sub-track timebase.'),
        (352, 'idle-redraw-tick-gate-position', 0, TAIL, tail,
         'Second half of the gate: post when the bar position computed as the 0x4D segment does differs from the stored one.'),
        (353, 'idle-redraw-tick-hook', 27, TICK_SITE, branch(TICK_SITE, HEAD, True),
         'The 0x40 segment posts the per-second 0x4D through tick_gate.'),
        (354, 'idle-redraw-store-hook', 27, STORE_SITE, branch(STORE_SITE, store, True),
         'The 0x4D segment stores the transport fingerprint in the otherwise unread word 0x030247F4.'),
    )
    out = []
    for number, label, module, address, code, why in rows:
        offset, size = image.module_region(module, 'code')
        base = image.modules[module]['code_exec']
        assert base <= address and address + len(code) <= base + size
        expect = raw[offset + address - base:offset + address - base + len(code)]
        name = f'{number:04d}-{label}'
        out.append((name, (
            '# Generated by build_idle_redraw.py.\n'
            f'name: {name}\nkind: module\nmodule: {module}\nregion: code\naddress: {address:#x}\n'
            f'expect: {expect.hex()}\nreplace: {code.hex()}\n'
            'gate: stock bytes; idle-tick framebuffer, display-context and panel parity against the unpatched image (test_idle_redraw.py)\n'
            f'rationale: {why} Skipped repaints would rewrite identical pixels. No new RAM.\n')))
    return out


def main():
    raw = (ROOT / 'DP3_V137.img').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == STOCK_SHA
    for old in HERE.glob('035*.patch'):
        old.unlink()
    for name, text in patches(raw):
        (HERE / f'{name}.patch').write_text(text)
    fp, _, head, tail = payloads()
    print(f'fingerprint + store: {len(fp)} of {FP_END - FP} B; gate: {len(head)} of {HEAD_END - HEAD} B '
          f'and {len(tail)} of {TAIL_END - TAIL} B')


if __name__ == '__main__':
    main()
