#!/usr/bin/env python3
"""Draw the player's status bar on the current ground.

Three stock status items carry a fixed background in their pixels, so with
a theater ground they show as dark boxes: the Bluetooth icon, a blank cell
after the track counter, and the speaker icon before the volume.

Bluetooth icon
--------------

The resident status routine at 0x03063642 draws the Bluetooth icon at
(176, 5), 18 by 18. In the music window (window byte 3) with flag 0x1A8
clear it picks resources 284 (off) and 285 (on), light 450 and 451, whose
surround is the stock player ground (0x10A2 dark, 0xFFFF light). It draws
them through the opaque DrawImageAt (0x0306354A), so with a theater ground
the icon shows as a dark (or white) 18 by 18 box, even with Bluetooth off.
Other windows use 282 and 283 (black surround) on their black ground and
are left unchanged.

Track counter
-------------
The player draws the counter (module 27, call at 0x0307E458) through the
sprite-string routine 0x030639A8: characters map to resource
(char - 0x30 + 249), 9 pixels apart, at y = 8, drawn keyed. The total is
formatted as four digits; each stripped leading zero becomes a trailing
':' whose resource (259, light 425) is a solid 9 by 12 tile (0x10A2 dark,
0x2945 light) used as an eraser. The field always ends at x = 170. The
wrapper fills the whole field (90, 8)..(170, 19) with the background cell,
ends the string at its first ':' (the blanks only ever trail the digits;
the slash is ';'), then calls the stock routine with the stock arguments.
Resource 259 is left unchanged, because other windows still use it.

Volume speaker
--------------
The speaker (resource 133, light 299; 8 by 14 at (10, 7)) has one image
for every window, with a black (light: white) surround, drawn opaque by the
player (module 27, 0x0307F024) and by the shared status routine (module 0,
0x03063ACC). With the surround keyed, the player's call draws through the
keyed helper directly: it runs only in straight line after the player's
full-screen ground fill (0x0307EFB8), so the rectangle already holds the
ground. The shared routine's call goes through a wrapper: in the music
window (window byte 3) it fills the icon rectangle with the background
cell, elsewhere with the stock surround colour, then draws keyed. Other
windows therefore stay pixel for pixel stock.

Artefacts
---------

  0279-bt-status-ground.patch   a 38-byte wrapper in the census pocket at
                                0x03063C4A (stock's unreferenced format-2
                                silhouette helper): fill the 18 by 18
                                rectangle with the background cell
                                0x03004400, then tail-call the keyed helper
                                0x03063A08 (skips 0xF800).
  0280-bt-status-keyed-hook.patch
                                the music-window branch of the routine
                                (22 bytes at 0x030636B8) rebuilt to call the
                                wrapper with the same id, x and y, then
                                store the drawn state and return as stock.
  0281-counter-ground.patch     a 52-byte wrapper in the census pocket at
                                0x03062EB8 (68 bytes): fill the counter
                                field with the background cell, cut the
                                trailing blanks, call 0x030639A8.
  0282-counter-ground-hook.patch
                                the player's counter call (module 27,
                                0x0307E458) retargeted to that wrapper.
  0283-volume-icon-ground.patch a 72-byte wrapper in the census pocket at
                                0x0306944E (72 bytes, stock's unreferenced
                                leaf routine) for the speaker, as above.
  0284-volume-icon-player-hook.patch
                                the player's speaker draw (module 27,
                                0x0307F024) retargeted to the keyed helper.
  0285-volume-icon-status-hook.patch
                                the shared status routine's speaker draw
                                (module 0, 0x03063ACC) retargeted to it.
  status-key.json               six resource runs at stock offsets: every
                                surround-coloured pixel of 284, 285, 450
                                and 451, and the border-connected surround
                                of 133 and 299, become the key 0xF800.

Both fills keep stock's whole-rectangle replacement, so a glyph or digit
that is no longer drawn is still erased. Outside theater mode the cell
holds the theme default, so the Bluetooth icon equals stock pixel for
pixel; the counter field matches stock in the dark theme, and in the light
theme it no longer shows stock's dark grey blank cell.

Usage (repository root): python3 patches/status_bar/build_status_bar.py
Needs keystone-engine. Output is deterministic; CI rebuilds and diffs it.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image  # noqa: E402

STOCK_SHA = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
WRAPPER = 0x03063C4A        # census tier-1 pocket, 42 bytes (0x03063C4A..0x03063C74)
POCKET_END = 0x03063C74
BRANCH = 0x030636B8         # music-window branch, 22 bytes (0x030636B8..0x030636CE)
BRANCH_END = 0x030636CE
HELPER = 0x03063A08         # keyed draw (id, x, y), format 1: skips 0xF800
FILL = 0x030632FA           # fill (x0, y0, x1, y1), colour on the stack
GROUND = 0x03004400         # player background cell
ICON = 18                   # resources 282..285 and 448..451 are 18 by 18
IDS = {284: 0x10A2, 285: 0x10A2, 450: 0xFFFF, 451: 0xFFFF}   # id: surround
KEY = 0xF800
COUNTER = 0x03062EB8        # census tier-1 pocket, 68 bytes (0x03062EB8..0x03062EFC)
COUNTER_END = 0x03062EFC
COUNTER_SITE = 0x0307E458   # module 27: bl 0x030639A8 (the track counter)
STRINGS = 0x030639A8        # sprite string (base id, text, step, x), y on stack
FIELD = (90, 8, 170, 19)    # x0, y0, x1, y1: nine 9 by 12 cells from x = 0x5A
VOLUME = 0x0306944E         # census tier-2 pocket, 72 bytes (0x0306944E..0x03069496)
VOLUME_END = 0x03069496
VOLUME_SITES = ((27, 0x0307F024, '0284-volume-icon-player-hook', 'player', HELPER,
                 'keyed helper. The call runs only in straight line after the\n'
                 '  player\'s full-screen ground fill (0x0307EFB8), so the icon\n'
                 '  rectangle already holds the ground.'),
                (0, 0x03063ACC, '0285-volume-icon-status-hook', 'shared status routine',
                 VOLUME, 'volume ground wrapper.'))
WINDOW = 0x030057E0         # current window index byte (3: music)
SAVEINFO = 0x030232A0       # +0x2D8: theme (0 dark, 1 light)
SPEAKER = {133: 0x0000, 299: 0xFFFF}   # id: stock surround (border-connected)
SPEAKER_W, SPEAKER_H = 8, 14

WRAPPER_ASM = f'''
    push {{r0, r1, r2, lr}}
    sub sp, #8
    ldr r3, ={GROUND:#x}
    ldrh r3, [r3]
    str r3, [sp]
    mov r0, r1
    mov r1, r2
    adds r2, r0, #{ICON - 1}
    adds r3, r1, #{ICON - 1}
    bl {FILL:#x}
    add sp, #8
    pop.w {{r0, r1, r2, lr}}
    b.w {HELPER:#x}
    .balign 4, 0
    .ltorg
'''

BRANCH_ASM = f'''
    movs r1, #0xb0
    movs r2, #5
    movw r0, #0x11c
    cmp r4, #0
    it ne
    addne r0, #1
    bl {WRAPPER:#x}
    strb r4, [r5]
    pop {{r4, r5, r6, pc}}
'''

COUNTER_ASM = f'''
    push {{r0, r1, r2, r3, r4, lr}}
    sub sp, #8
scan:
    ldrh r4, [r1], #2
    cbz r4, fill
    cmp r4, #0x3a
    bne scan
    movs r4, #0
    strh r4, [r1, #-2]
fill:
    ldr r3, ={GROUND:#x}
    ldrh r3, [r3]
    str r3, [sp]
    movs r0, #{FIELD[0]}
    movs r1, #{FIELD[1]}
    movs r2, #{FIELD[2]}
    movs r3, #{FIELD[3]}
    bl {FILL:#x}
    add sp, #8
    pop.w {{r0, r1, r2, r3, r4, lr}}
    b.w {STRINGS:#x}
    .balign 4, 0
    .ltorg
'''

VOLUME_ASM = f'''
    push {{r0, r1, r2, lr}}
    sub sp, #8
    ldr r3, ={WINDOW:#x}
    ldrb r3, [r3]
    cmp r3, #3
    bne surround
    ldr r3, ={GROUND:#x}
    ldrh r3, [r3]
    b store
surround:
    ldr r3, ={SAVEINFO:#x}
    ldrb.w r3, [r3, #0x2d8]
    cbz r3, store
    movw r3, #0xffff
store:
    str r3, [sp]
    mov r0, r1
    mov r1, r2
    adds r2, r0, #{SPEAKER_W - 1}
    adds r3, r1, #{SPEAKER_H - 1}
    bl {FILL:#x}
    add sp, #8
    pop.w {{r0, r1, r2, lr}}
    b.w {HELPER:#x}
    .balign 4, 0
    .ltorg
'''

# Stock bytes of the music-window branch, decoded, for the record:
#   030636b8 cmp r4, #0 ; mov.w r2, #5 ; mov.w r1, #0xb0 ; ite ne
#   030636c4 movwne r0, #0x11d ; moveq.w r0, #0x11c ; b 0x030636b0
# 0x030636B0 is `bl 0x0306354A ; strb r4, [r5] ; pop {r4, r5, r6, pc}`.


def assemble(source, address):
    code = bytes(Ks(KS_ARCH_ARM, KS_MODE_THUMB).asm(source, address)[0])
    return code


def stock_bytes(raw, image, address, length, module=0):
    offset, size = image.module_region(module, 'code')
    base = image.modules[module]['code_exec']
    assert base <= address and address + length <= base + size
    return raw[offset + address - base:offset + address - base + length]


def patch_text(name, address, expect, replace, rationale, module=0):
    return ('# Generated by patches/status_bar/build_status_bar.py.\n'
            f'name: {name}\nkind: module\nmodule: {module}\nregion: code\n'
            f'address: {address:#x}\n'
            'gate: build refuses unless the stock bytes at the target equal\n'
            '  `expect`; test_status_bar.py runs the routines under emulation.\n'
            f'expect: {expect.hex()}\nreplace: {replace.hex()}\n'
            f'rationale: {rationale}\n')


def border_connected(px, w, h, colour):
    seen, stack = set(), [(x, y) for x in range(w) for y in (0, h - 1)] + \
        [(x, y) for y in range(h) for x in (0, w - 1)]
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h) or px[y * w + x] != colour:
            continue
        seen.add((x, y))
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return seen


def resource_runs(raw):
    entries = {e['id']: e for e in Image(raw).images()}
    runs = []
    for rid, surround in IDS.items():
        e = entries[rid]
        assert (e['width'], e['height']) == (ICON, ICON), rid
        old = raw[e['data_offset']:e['data_offset'] + e['size']]
        px = [v for (v,) in struct.iter_unpack('>H', old)]   # panel order
        assert KEY not in px, f'resource {rid} already uses the key colour'
        new = [KEY if v == surround else v for v in px]
        keyed = sum(1 for v in px if v == surround)
        runs.append({'offset': hex(e['data_offset']), 'expect': old.hex(),
                     'replace': struct.pack(f'>{len(new)}H', *new).hex()})
        print(f'resource {rid}: {keyed} of {ICON * ICON} surround pixels keyed')
    for rid, surround in SPEAKER.items():
        e = entries[rid]
        w, h = e['width'], e['height']
        assert (w, h) == (SPEAKER_W, SPEAKER_H), rid
        old = raw[e['data_offset']:e['data_offset'] + e['size']]
        px = [v for (v,) in struct.iter_unpack('>H', old)]
        assert KEY not in px, f'resource {rid} already uses the key colour'
        keyed = border_connected(px, w, h, surround)
        new = list(px)
        for x, y in keyed:
            new[y * w + x] = KEY
        runs.append({'offset': hex(e['data_offset']), 'expect': old.hex(),
                     'replace': struct.pack(f'>{len(new)}H', *new).hex()})
        print(f'resource {rid}: {len(keyed)} of {w * h} border-connected surround pixels keyed')
    return runs


def main():
    raw = (ROOT / 'DP3_V137.img').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == STOCK_SHA, 'stock SHA gate'
    image = Image(raw)

    wrapper = assemble(WRAPPER_ASM, WRAPPER)
    assert len(wrapper) <= POCKET_END - WRAPPER, len(wrapper)
    hook = assemble(BRANCH_ASM, BRANCH)
    assert len(hook) == BRANCH_END - BRANCH, len(hook)

    (HERE / '0279-bt-status-ground.patch').write_text(patch_text(
        '0279-bt-status-ground', WRAPPER,
        stock_bytes(raw, image, WRAPPER, len(wrapper)), wrapper,
        'Fill the Bluetooth icon rectangle (18 by 18) with the background\n'
        '  cell 0x03004400, then tail-call the keyed helper 0x03063A08 with\n'
        '  the caller\'s (id, x, y). Lives in the census pocket at 0x03063C4A,\n'
        '  stock\'s unreferenced format-2 silhouette helper (42 bytes).'))
    (HERE / '0280-bt-status-keyed-hook.patch').write_text(patch_text(
        '0280-bt-status-keyed-hook', BRANCH,
        stock_bytes(raw, image, BRANCH, len(hook)), hook,
        'The music-window branch of the status routine drew 284/285\n'
        '  (light 450/451) through the opaque DrawImageAt, so their 0x10A2\n'
        '  surround showed as a box on a theater ground. Same id, x and y,\n'
        '  now through the ground wrapper; the state store and return are\n'
        '  stock. The other windows\' branch (282/283) is unchanged.'))
    (HERE / 'status-key.json').write_text(json.dumps(
        {'version': 1, 'literal_sites': [], 'runs': resource_runs(raw)},
        indent=1) + '\n')
    counter = assemble(COUNTER_ASM, COUNTER)
    assert len(counter) <= COUNTER_END - COUNTER, len(counter)
    site = assemble(f'bl {COUNTER:#x}', COUNTER_SITE)
    stock_site = stock_bytes(raw, image, COUNTER_SITE, 4, module=27)
    assert stock_site == assemble(f'bl {STRINGS:#x}', COUNTER_SITE), 'counter site drift'
    (HERE / '0281-counter-ground.patch').write_text(patch_text(
        '0281-counter-ground', COUNTER,
        stock_bytes(raw, image, COUNTER, len(counter)), counter,
        'Fill the track counter field (90, 8)..(170, 19) with the\n'
        '  background cell 0x03004400, end the string at its first \':\'\n'
        '  (the trailing blank cells, resource 259, a solid 0x10A2 tile),\n'
        '  then call the sprite string routine 0x030639A8 with the stock\n'
        '  arguments. Lives in the census pocket at 0x03062EB8 (68 bytes).'))
    (HERE / '0282-counter-ground-hook.patch').write_text(patch_text(
        '0282-counter-ground-hook', COUNTER_SITE, stock_site, site,
        'The player\'s track counter call, retargeted from the sprite\n'
        '  string routine to the ground wrapper. Other windows keep\n'
        '  drawing their blank cells as stock.', module=27))
    volume = assemble(VOLUME_ASM, VOLUME)
    assert len(volume) <= VOLUME_END - VOLUME, len(volume)
    (HERE / '0283-volume-icon-ground.patch').write_text(patch_text(
        '0283-volume-icon-ground', VOLUME,
        stock_bytes(raw, image, VOLUME, len(volume)), volume,
        'Fill the speaker icon rectangle (8 by 14) with the background\n'
        '  cell 0x03004400 in the music window (window byte 3), else with\n'
        '  the stock surround (black dark, white light), then tail-call the\n'
        '  keyed helper 0x03063A08 with the caller\'s (id, x, y). Lives in\n'
        '  the census pocket at 0x0306944E (72 bytes).'))
    for module, site, name, who, target, why in VOLUME_SITES:
        stock_site = stock_bytes(raw, image, site, 4, module=module)
        assert stock_site == assemble('bl 0x0306354a', site), f'{name} drift'
        (HERE / f'{name}.patch').write_text(patch_text(
            name, site, stock_site, assemble(f'bl {target:#x}', site),
            f'The {who}\'s speaker draw (resource 133 at (10, 7)),\n'
            '  retargeted from the opaque DrawImageAt to the ' + why,
            module=module))
    print(f'volume wrapper {len(volume)} bytes at {VOLUME:#x}')
    print(f'bluetooth wrapper {len(wrapper)} bytes at {WRAPPER:#x}; '
          f'branch {len(hook)} bytes at {BRANCH:#x}; '
          f'counter wrapper {len(counter)} bytes at {COUNTER:#x}')


if __name__ == '__main__':
    main()
