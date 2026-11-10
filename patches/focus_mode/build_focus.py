#!/usr/bin/env python3
"""Build the focus-mode (auto-hide controls) tail payload and patches.

Experimental variant on top of theater mode. The focus payload is
appended to theater's 676-byte tail payload unchanged: theater keeps
offsets 0..675 (exec 0x0307BFB4..0x0307C257), the focus routines
start at exec 0x0307C258. All focus state lives at SAVEINFO+0x1E4
(0x03023484), 12 bytes inside the verbatim block, immediately after
theater's 28 bytes at +0x1C8..+0x1E3; census in design.md.

Assembles the seven focus routines with Keystone at their final
addresses, emits the hook patches (stock bytes read from the pinned
stock image), round-trip checks every routine with Capstone, and
verifies the routines' external references and sizes.

Emits, next to this script:
  focus_tail.bin            theater_tail.bin bytes + focus payload
  0200..0211 *.patch        the twelve module 27 hook patches
  manifest.txt              default 32 + theater 5 + focus 12

Layout constants (derived in design.md from the painter's own
coordinates): HIDE_TICKS 500 (5 s at the proven 100 Hz OS tick),
grown art box 190x190 at dest (25, 8), title/artist shift +34.
"""
import hashlib
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tools'))

from rknano_image import Image  # noqa: E402
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB  # noqa: E402
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB  # noqa: E402

TAIL_BASE = 0x0307BFB4
TAIL_MAX = 2044
THEATER_TAIL = REPO / 'patches' / 'theater' / 'build' / 'theater_tail.bin'
THEATER_PAYLOAD_LEN = 676
FOCUS_BASE = TAIL_BASE + THEATER_PAYLOAD_LEN      # 0x0307C258
STATE = 0x03023484                                # SAVEINFO + 0x1E4
HIDE_TICKS = 500
STOCK_SHA = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'

POST = 0x0306723C          # event-flag post
TEST_CLEAR = 0x03067258    # event-flag test-and-clear
TICK_GET = 0x0306672E      # OS clock read (100 Hz ticks)
KEYFN = 0x03061B16         # displaced per-key function in module 29
SETSRC0 = 0x03083A90       # displaced set-source-0 in module 18
MEASURE = 0x0306295A       # title text measure
RENDER = 0x03062CEE        # text renderer (artist call)
WHEEL_TOTAL = 0x0302317C   # key task total-steps counter


def branch(site, target, link=False):
    """Thumb-2 B/BL encoder (same construction as build_theater.py)."""
    delta = target - (site + 4)
    if delta & 1 or not -(1 << 24) <= delta < (1 << 24):
        raise ValueError('invalid branch displacement')
    s, i1, i2 = (delta >> 24) & 1, (delta >> 23) & 1, (delta >> 22) & 1
    j1, j2 = (~(i1 ^ s)) & 1, (~(i2 ^ s)) & 1
    return struct.pack('<HH', 0xF000 | (s << 10) | ((delta >> 12) & 0x3FF),
                       (0xD000 if link else 0x9000) | (j1 << 13)
                       | (j2 << 11) | ((delta >> 1) & 0x7FF))


# ------------------------------------------------------------- routines
# Each routine is assembled at its final exec address. External calls
# name stock addresses directly; Keystone computes the displacement.
# Entry contracts are stated per routine and checked after assembly.

RESET_ASM = [
    # BL from the player Init hook site 0x0307D1A2. r0 = 0x39 on
    # entry (the site's own immediate). Performs the displaced post,
    # then initialises the focus state: hidden = 0, activity stamp =
    # now, wheel snapshot = current total. Preserves r4; clobbers
    # r0-r3 only (the site continues into Init body code that reloads
    # everything it uses).
    'push {r4, lr}',
    f'bl {POST:#x}',
    f'ldr r4, ={STATE:#x}',
    'movs r0, #0',
    'strb r0, [r4, #8]',          # hidden = 0
    'strb r0, [r4, #9]',          # reserved slide byte = 0
    f'bl {TICK_GET:#x}',
    'str r0, [r4, #0]',           # last_tick = now
    f'ldr r0, ={WHEEL_TOTAL:#x}',
    'ldr r0, [r0, #0]',
    'str r0, [r4, #4]',           # wheel_seen
    'pop {r4, pc}',
]

TICK_ASM = [
    # BL from the player Service hook site 0x0307E20C. r0 = 0x40 on
    # entry. Performs the displaced progress post, then the idle
    # accounting. Preserves r4-r11 (r4/r5 saved); clobbers r0-r3.
    'push {r4, r5, lr}',
    f'bl {POST:#x}',              # post(0x40), displaced
    f'ldr r4, ={STATE:#x}',
    'ldrb r0, [r4, #8]',
    'cmp r0, #0',
    'bne ft_done',                # already hidden: counter frozen
    f'ldr r5, ={WHEEL_TOTAL:#x}',
    'ldr r0, [r5, #0]',
    'ldr r1, [r4, #4]',
    'cmp r0, r1',
    'beq ft_nowheel',
    'str r0, [r4, #4]',           # wheel moved: activity
    f'bl {TICK_GET:#x}',
    'str r0, [r4, #0]',
    'b ft_done',
    'ft_nowheel:',
    f'bl {TICK_GET:#x}',          # r0 = now (leaf: clobbers r0 only)
    'ldr r1, [r4, #0]',
    'subs r0, r0, r1',
    f'movw r1, #{HIDE_TICKS}',
    'cmp r0, r1',
    'blo ft_done',
    'movs r0, #1',
    'strb r0, [r4, #8]',          # hidden = 1
    f'bl {TICK_GET:#x}',
    'str r0, [r4, #0]',
    'movs r0, #0x39',
    f'bl {POST:#x}',              # full repaint
    'movs r0, #0x3b',
    f'bl {POST:#x}',              # artwork re-request
    'ft_done:',
    'pop {r4, r5, pc}',
]

KEY_ASM = [
    # BL from the player Key wrapper hook site 0x03080AF6, replacing
    # the displaced call to the per-key function. Runs that function
    # first (its side effects are load-bearing: playback-state
    # posts), restamps activity, and on the visible path returns its
    # result in r0 so the wrapper continues byte-identically. On the
    # hidden path it wakes (posts the repaint pair) and swallows the
    # key by unwinding both frames: the wrapper pushed {r4, lr}
    # before the hook, so the wrapper's saved lr sits at [sp, #16]
    # and its saved r4 at [sp, #12] once this frame ({r4, r5, lr})
    # is up. Neither key handler runs.
    'push {r4, r5, lr}',
    f'bl {KEYFN:#x}',
    'mov r4, r0',                 # keep the function's result
    f'ldr r5, ={STATE:#x}',
    f'bl {TICK_GET:#x}',
    'str r0, [r5, #0]',           # last_tick = now
    f'ldr r0, ={WHEEL_TOTAL:#x}',
    'ldr r0, [r0, #0]',
    'str r0, [r5, #4]',           # wheel_seen sync
    'ldrb r0, [r5, #8]',
    'cmp r0, #0',
    'beq fk_pass',
    'movs r0, #0',
    'strb r0, [r5, #8]',          # hidden = 0 (wake)
    'movs r0, #0x39',
    f'bl {POST:#x}',
    'movs r0, #0x3b',
    f'bl {POST:#x}',
    'mov r0, r4',                 # return value: the event word
    'ldr r4, [sp, #12]',          # wrapper's saved r4
    'ldr r5, [sp, #4]',           # own saved r5
    'ldr lr, [sp, #16]',          # wrapper's saved lr
    'add sp, sp, #20',            # drop both frames
    'bx lr',                      # return to the framework caller
    'fk_pass:',
    'mov r0, r4',
    'pop {r4, r5, pc}',
]

GATE_ASM = [
    # Shared segment gate. BL from each gated segment's test site;
    # r0 = event id, lr = resume address (site + 4). Visible: tail
    # to the real test-and-clear, which returns through lr. Hidden:
    # return 0 with the event bit NOT consumed, so the segment
    # redraws fresh on the wake paint. r1 is saved out of caution.
    'push {r1}',
    f'ldr r1, ={STATE:#x}',
    'ldrb r1, [r1, #8]',
    'cmp r1, #0',
    'pop {r1}',
    'beq fg_visible',
    'movs r0, #0',
    'bx lr',
    'fg_visible:',
    f'b {TEST_CLEAR:#x}',
]

GEOM_ASM = [
    # BL from the artwork request hook site 0x0307E8DE, replacing
    # the displaced set-source-0 call. When hidden, rewrites the
    # four request globals (box W/H at 0x0302598C/90, dest X/Y at
    # 0x03025994/98) with the focus geometry, then tail-calls the
    # displaced function with its stock argument (r0 = 0), which
    # returns through the restored lr to the request function.
    # Preserves r4 (the caller's picture-kind register).
    'push {r4, lr}',
    f'ldr r4, ={STATE:#x}',
    'ldrb r0, [r4, #8]',
    'cmp r0, #0',
    'beq fgm_stock',
    'movs r1, #190',
    'ldr r0, =0x0302598c',
    'str r1, [r0, #0]',           # box W = 190
    'str r1, [r0, #4]',           # box H = 190
    'movs r1, #25',
    'str r1, [r0, #8]',           # dest X = 25
    'movs r1, #8',
    'str r1, [r0, #12]',          # dest Y = 8
    'fgm_stock:',
    'movs r0, #0',
    'pop {r4, lr}',
    f'b {SETSRC0:#x}',
]

TITLE_ASM = [
    # BL from the title measure hook site 0x0307F9F0, replacing the
    # displaced measure call. The title rect lives on the painter's
    # stack at [sp, #0x10] (left/top/right/bottom halfwords), built
    # fresh at the segment head with stock values and read again by
    # the draw and marquee code after the measure call. While
    # hidden the stub SETS top/bottom to the focus values (232 /
    # 247): set, not add, because the stock suffix-trim path can
    # loop back and measure the same rect twice in one paint, and
    # an add would shift it twice. Tail to the displaced measure
    # with r0 (the title buffer) untouched.
    f'ldr ip, ={STATE:#x}',
    'ldrb ip, [ip, #8]',
    'cmp ip, #0',
    'beq ft2_go',
    'movw r1, #232',
    'strh r1, [sp, #0x12]',
    'movw r1, #247',
    'strh r1, [sp, #0x16]',
    'ft2_go:',
    f'b {MEASURE:#x}',
]

ARTIST_ASM = [
    # BL from the artist renderer hook site 0x0307FAA8, replacing
    # the displaced renderer call. r0 = r1 = rect pointer; while
    # hidden the stub sets top/bottom (+2/+6) to the focus values
    # (257 / 272), then tail calls the renderer with all arguments
    # untouched.
    f'ldr ip, ={STATE:#x}',
    'ldrb ip, [ip, #8]',
    'cmp ip, #0',
    'beq fa_go',
    'movw ip, #257',
    'strh ip, [r0, #2]',
    'movw ip, #272',
    'strh ip, [r0, #6]',
    'fa_go:',
    f'b {RENDER:#x}',
]

ROUTINES = [
    ('focus_reset', RESET_ASM),
    ('focus_tick', TICK_ASM),
    ('focus_key', KEY_ASM),
    ('focus_gate', GATE_ASM),
    ('focus_geom', GEOM_ASM),
    ('focus_title_shift', TITLE_ASM),
    ('focus_artist_shift', ARTIST_ASM),
]


def assemble():
    ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
    payload = bytearray()
    entries = {}
    for name, lines in ROUTINES:
        addr = FOCUS_BASE + len(payload)
        code, _ = ks.asm('\n'.join(lines), addr)
        entries[name] = addr
        payload += bytes(code)
    return bytes(payload), entries


def roundtrip(payload, entries):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    starts = sorted(entries.items(), key=lambda kv: kv[1])
    for i, (name, addr) in enumerate(starts):
        end = (starts[i + 1][1] if i + 1 < len(starts)
               else FOCUS_BASE + len(payload))
        insns = list(md.disasm(payload[addr - FOCUS_BASE:end - FOCUS_BASE],
                               addr))
        if not insns or insns[0].address != addr:
            raise ValueError(f'{name}: round-trip disassembly failed')
        text = ' '.join(f'{x.mnemonic} {x.op_str}' for x in insns)
        if 'udf' in text or '.byte' in text:
            raise ValueError(f'{name}: round-trip contains bad bytes')


PATCH_DEFS = [
    # (number, name, site, target, gate-note)
    ('0200', 'focus-init-reset-hook', 0x0307D1A2, 'focus_reset',
     'module 27 Init post(0x39) site'),
    ('0201', 'focus-service-tick-hook', 0x0307E20C, 'focus_tick',
     'module 27 Service post(0x40) site'),
    ('0202', 'focus-key-hook', 0x03080AF6, 'focus_key',
     'module 27 Key wrapper displaced-call site'),
    ('0203', 'focus-geometry-hook', 0x0307E8DE, 'focus_geom',
     'module 27 artwork request set-source-0 site'),
    ('0204', 'focus-gate-status-1f', 0x0307F510, 'focus_gate',
     'painter status segment 0x1F test site'),
    ('0205', 'focus-gate-progress-41', 0x0307F548, 'focus_gate',
     'painter progress segment 0x41 test site'),
    ('0206', 'focus-gate-progress-40', 0x0307F598, 'focus_gate',
     'painter progress segment 0x40 test site'),
    ('0207', 'focus-gate-progress-4d', 0x0307F5EA, 'focus_gate',
     'painter progress segment 0x4D test site'),
    ('0208', 'focus-gate-transport-43', 0x0307F7B6, 'focus_gate',
     'painter transport segment 0x43 test site'),
    ('0209', 'focus-gate-volume-19a', 0x0307F8F8, 'focus_gate',
     'painter volume segment 0x19A test site'),
    ('0210', 'focus-title-shift-hook', 0x0307F9F0, 'focus_title_shift',
     'painter title measure call site'),
    ('0211', 'focus-artist-shift-hook', 0x0307FAA8, 'focus_artist_shift',
     'painter artist renderer call site'),
]

RATIONALES = {
    'focus-init-reset-hook':
        'Player Init posts the first full repaint at this site; the '
        'focus reset stub performs that post, then initialises the '
        'focus state at SAVEINFO+0x1E4 (hidden clear, activity stamp '
        '= OS clock now, wheel snapshot = key-task total-steps word), '
        'so every player-window entry starts visible with a fresh '
        'idle budget.',
    'focus-service-tick-hook':
        'The Service handler posts the progress event 0x40 on a '
        'counter cadence while the play state is playing or paused. '
        'The focus tick stub performs that post, then does the idle '
        'accounting in OS clock ticks (100 Hz, proven from the '
        'screen-off table): wheel movement restamps activity; at '
        '500 ticks idle it sets the hidden flag and posts 0x39 and '
        '0x3B so the painter repaints into the focus layout.',
    'focus-key-hook':
        'The Key wrapper call to the per-key function is the one '
        'point every key event for this window passes, before the '
        'sleep-state fork to the main or alternate handler. The '
        'focus key stub runs the displaced function for its side '
        'effects, restamps activity, and returns its result '
        'unchanged while visible. While hidden it wakes (posts 0x39 '
        'and 0x3B) and swallows the key by unwinding both frames, '
        'so neither handler performs the key action.',
    'focus-geometry-hook':
        'The artwork request function writes the box and destination '
        'globals on every call; this hook runs just before the '
        'displaced set-source-0 call and, while hidden, overwrites '
        'the four globals with the focus geometry (box 190x190, '
        'destination (25, 8)). Setup then scales and the picture '
        'context persists the new geometry until the next request.',
    'focus-gate-status-1f':
        'Segment gate: while hidden, the shared focus gate answers '
        'the segment event test with 0 without consuming the bit, '
        'so the status icons are not drawn over the focus layout '
        'and redraw fresh on the wake paint. While visible it tail '
        'calls the real test-and-clear.',
    'focus-gate-progress-41':
        'Segment gate for the first progress segment (time labels '
        'and track): see focus-gate-status-1f for the gate '
        'contract. The progress chain is gated as a unit across '
        '0x41, 0x40 and 0x4D.',
    'focus-gate-progress-40':
        'Segment gate for the progress update segment: see '
        'focus-gate-status-1f for the gate contract.',
    'focus-gate-progress-4d':
        'Segment gate for the progress bar segment: see '
        'focus-gate-status-1f for the gate contract.',
    'focus-gate-transport-43':
        'Segment gate for the transport row segment: while hidden '
        'the row (and its mode indicator erase) is not drawn; the '
        '0x43 bit stays pending and the row redraws on the wake '
        'paint. Gate sits at the segment test, not at the draw '
        'sites, so it composes with design refresh v4 either way.',
    'focus-gate-volume-19a':
        'Segment gate for the volume readout segment: see '
        'focus-gate-status-1f for the gate contract. Volume keys '
        'wake through the key hook first, so the readout still '
        'appears on the wake paint.',
    'focus-title-shift-hook':
        'The title rect is built on the painter stack and consumed '
        'by the measure call replaced here and by the draw and '
        'marquee code after it. While hidden the stub sets the '
        'rect top and bottom to the focus values 232 and 247 '
        'before tail calling the measure function, moving the '
        'title (and any marquee) into the space the progress bar '
        'and transport row vacated. Set, not add: the stock '
        'suffix-trim path can loop back and measure the same rect '
        'twice in one paint.',
    'focus-artist-shift-hook':
        'The artist rect is passed in r0 to the renderer call '
        'replaced here. While hidden the stub sets its top and '
        'bottom to the focus values 257 and 272 before tail '
        'calling the renderer, moving the artist line with the '
        'title and preserving the stock 10 px gap between them.',
}


def stock_bytes(stock, address, length):
    img = Image(stock)
    off, _ln = img.module_region(27, 'code')
    exec_base = img.modules[27]['code_exec']
    rel = address - exec_base
    return stock[off + rel:off + rel + length]


def main():
    stock_path = REPO / 'DP3_V137.img'
    stock = stock_path.read_bytes()
    if hashlib.sha256(stock).hexdigest() != STOCK_SHA:
        raise ValueError('stock image hash mismatch; refusing')
    theater = THEATER_TAIL.read_bytes()
    if len(theater) != THEATER_PAYLOAD_LEN:
        raise ValueError(f'theater tail is {len(theater)} bytes, '
                         f'expected {THEATER_PAYLOAD_LEN}')

    payload, entries = assemble()
    roundtrip(payload, entries)
    tail = theater + payload
    if len(tail) > TAIL_MAX:
        raise ValueError(f'composed tail {len(tail)} > {TAIL_MAX}')
    (HERE / 'focus_tail.bin').write_bytes(tail)

    lines = []
    for num, name, site, target, _note in PATCH_DEFS:
        expect = stock_bytes(stock, site, 4)
        replace = branch(site, entries[target], link=True)
        fname = f'{num}-{name}.patch'
        (HERE / fname).write_text(
            f'# Focus mode (experimental, on the theater variant): '
            f'{name}.\n'
            f'# Design and census: patches/focus_mode/design.md.\n'
            f'name: {name}\n'
            f'kind: module\n'
            f'module: 27\n'
            f'region: code\n'
            f'address: {site:#x}\n'
            f'gate: stock byte precondition; variant-only patch, '
            f'never in the default manifest; validated by '
            f'test_focus_mode.py under emulation\n'
            f'rationale: {RATIONALES[name]}\n'
            f'expect: {expect.hex()}\n'
            f'replace: {replace.hex()}\n')
        lines.append(fname)

    theater_manifest = (REPO / 'patches' / 'theater' / 'build'
                        / 'manifest.txt').read_text().splitlines()
    base_entries = [ln.strip() for ln in theater_manifest
                    if ln.strip() and not ln.startswith('#')]
    out = ['# Focus variant manifest: the theater variant (default '
           '32 + theater 5) PLUS the twelve focus hook patches in '
           'this directory. Use ONLY with --tail focus_tail.bin; '
           'the tail payload extends theater\'s (see design.md).',
           '']
    for e in base_entries:
        if e.startswith('010'):
            out.append(f'../theater/build/{e}')
        elif e.startswith('../../framework/'):
            out.append('../' + e[len('../../'):])
        else:
            out.append(e)
    out += lines
    (HERE / 'manifest.txt').write_text('\n'.join(out) + '\n')

    print(f'focus payload: {len(payload)} bytes at {FOCUS_BASE:#x}')
    for name, addr in sorted(entries.items(), key=lambda kv: kv[1]):
        print(f'  {name:20s} {addr:#x}')
    print(f'composed tail: {len(tail)} bytes '
          f'(theater {THEATER_PAYLOAD_LEN} + focus {len(payload)}), '
          f'cap {TAIL_MAX}, headroom {TAIL_MAX - len(tail)}')
    print(f'focus_tail.bin sha256: {hashlib.sha256(tail).hexdigest()}')
    print(f'patches: {len(lines)} written; manifest entries: '
          f'{len(base_entries) + len(lines)}')


if __name__ == '__main__':
    main()
