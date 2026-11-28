"""Wheel acceleration for the file browser list (module 31).

Writes the four patch files of this directory. The code lives in two
dead module 0 functions (see README.md for the reference scan) and is
entered from the browser Key callback's two wheel-step calls.

Each wheel step stamps the 100 Hz OS clock. A step that follows the
previous one in the same direction within FAST_TICKS extends a streak;
a slower step or a reversal resets it. The streak picks the rows per
step from ROWS, STEPS_PER_LEVEL steps per level. A one-row step tail
calls the stock step function with nothing changed. A larger step puts
the selection one row short of the target (and, when the target is off
the seven visible rows, moves the top row so that the stock scroll
lands the target on the edge row), runs the stock step function for
the last row, and swaps the stock two-row repaint (0x144) it posted
for the stock full-list repaint (0x143).
"""
from pathlib import Path
import hashlib
import sys
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'patches/full/build')]
from rknano_image import Image  # noqa: E402
from build_tail import branch  # noqa: E402

STOCK_SHA = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
# Two dead stock functions with no branch, call or literal reference
# left in any module of the stock or Standard image.
HOME_A, HOME_A_END = 0x03052728, 0x030527A0   # GPIO pull read/write helpers
HOME_B, HOME_B_END = 0x0305DDD8, 0x0305DE20   # unreferenced lookup leaf
DOWN_SITE, UP_SITE = 0x0307E6D4, 0x0307E6FA   # bl 0x0307E474 / bl 0x0307E3BA
STOCK_DOWN, STOCK_UP = 0x0307E474, 0x0307E3BA
CTX, CLOCK, POST, CLEAR = 0x030228A8, 0x03023298, 0x0306723C, 0x0306727E
# The painter walks one node pointer through its two-row pass and then
# its full pass, so the two must never be pending together.
TWO_ROW_REPAINT, FULL_REPAINT = 0x144, 0x143

FAST_TICKS = 10          # 100 ms: a step closer than this to the last is fast
STEPS_PER_LEVEL = 4      # fast steps spent at each level
ROWS = (1, 2, 4, 8)      # rows per step at levels 0 to 3
STREAK_CAP = STEPS_PER_LEVEL * (len(ROWS) - 1)
# The code computes rows = 1 << (streak >> 2), which is this table.
assert all(ROWS[s // STEPS_PER_LEVEL] == 1 << (s >> 2) for s in range(STREAK_CAP + 1))


def assemble():
    """Return (home A bytes, home B bytes, layout dict)."""
    ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
    # r3 = direction (1 down, 0 up); r4 = browser context; r5 = old
    # selection; r6 = rows - 1, negated for up; r1 = count - 2;
    # r2 = context + 2 * level (top row at +0x1CE); ip = top row.
    # State byte = streak << 1 | direction of the last step.
    a_src = f'''
    down:   movs r3, #1
            b common
    up:     movs r3, #0
    common: push {{r4, r5, r6, lr}}
            ldr r4, ={CTX:#x}
            adr r2, state
            ldr.w r1, [r4, #{CLOCK - CTX:#x}]
            ldr r0, [r2]
            str r1, [r2]
            subs r0, r1, r0
            ldrb r1, [r2, #4]
            cmp r0, #{FAST_TICKS}
            bhs reset
            eor.w r0, r1, r3
            lsls r0, r0, #31
            bne reset
            cmp r1, #{2 * STREAK_CAP}
            it lo
            addlo r1, #2
            b keep
    reset:  mov r1, r3
    keep:   strb r1, [r2, #4]
            lsrs r1, r1, #3
            movs r6, #1
            lsls r6, r1
            subs r6, #1
            beq plain
            ldrh.w r5, [r4, #0x1ee]
            ldrh.w r1, [r4, #0x1cc]
            add.w r2, r4, r1, lsl #1
            movs r0, #56
            mla r1, r1, r0, r4
            ldrh r1, [r1, #0xc]
            subs r1, #2
            ble plain
            ldrh.w ip, [r2, #0x1ce]
            cbnz r3, signed
            negs r6, r6
    signed: b.w {HOME_B:#x}
    plain:  pop.w {{r4, r5, r6, lr}}
    tail:   cbz r3, upstock
            b.w {STOCK_DOWN:#x}
    upstock: b.w {STOCK_UP:#x}
            .ltorg
            .balign 4
    state:
    '''
    a = bytes(ks.asm(a_src, HOME_A)[0])
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
    plain = [i.address for i in md.disasm(a, HOME_A) if i.mnemonic == 'pop.w'][0]
    tail = plain + 4
    state = HOME_A + len(a)
    if state + 8 > HOME_A_END:
        raise SystemExit(f'home A needs {len(a) + 8} bytes; {HOME_A_END - HOME_A} available')
    b_src = f'''
            adds r0, r5, r6
            cmp r0, #1
            it lt
            movlt r0, #1
            cmp r0, r1
            it gt
            movgt r0, r1
            subs r1, r0, r5
            eors r1, r6
            bpl move
            b.w {plain:#x}
    move:   strh.w r0, [r4, #0x1ee]
            sub.w r1, r0, ip
            cbz r3, upwin
            subs r1, #6
            blt call
            subs r0, #6
            b settop
    upwin:  cmp r1, #0
            bgt call
    settop: strh.w r0, [r2, #0x1ce]
    call:   bl {tail:#x}
            movw r0, #{TWO_ROW_REPAINT:#x}
            bl {CLEAR:#x}
            movw r0, #{FULL_REPAINT:#x}
            bl {POST:#x}
            pop {{r4, r5, r6, pc}}
    '''
    b = bytes(ks.asm(b_src, HOME_B)[0])
    if len(b) > HOME_B_END - HOME_B:
        raise SystemExit(f'home B needs {len(b)} bytes; {HOME_B_END - HOME_B} available')
    layout = {'down': HOME_A, 'up': HOME_A + 4, 'plain': plain, 'state': state,
              'a_used': len(a) + 8, 'b_used': len(b)}
    a += bytes(HOME_A_END - HOME_A - len(a))
    b += bytes(HOME_B_END - HOME_B - len(b))
    return a, b, layout


def patches():
    """(number, label, module, address, replacement) for every patch."""
    a, b, lay = assemble()
    return [(330, 'wheel-accel-home-a', 0, HOME_A, a),
            (331, 'wheel-accel-home-b', 0, HOME_B, b),
            (332, 'wheel-accel-down-hook', 31, DOWN_SITE, branch(DOWN_SITE, lay['down'], True)),
            (333, 'wheel-accel-up-hook', 31, UP_SITE, branch(UP_SITE, lay['up'], True))]


def main():
    raw = (ROOT / 'DP3_V137.img').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == STOCK_SHA
    image = Image(raw)
    rationale = ('Wheel acceleration in the file browser. Steps under '
                 f'{FAST_TICKS * 10} ms apart in one direction build a streak that '
                 'moves 1, 2, 4, then 8 rows per step, four steps per level; a slower '
                 'step or a reversal returns to one row. A one-row step is the stock '
                 'step unchanged. A larger step reuses the stock step for its last row '
                 'and posts the stock full-list repaint.')
    gate = ('stock bytes; real module 31 Key callback and painter under emulation: '
            'slow steps match stock, bursts follow the table, ends clamp as stock')
    for number, label, module, address, code in patches():
        offset, size = image.module_region(module, 'code')
        base = image.modules[module]['code_exec']
        assert base <= address and address + len(code) <= base + size
        expected = raw[offset + address - base:offset + address - base + len(code)]
        name = f'{number:04d}-{label}'
        (HERE / (name + '.patch')).write_text(
            '# Generated by build_wheel_accel.py.\n'
            f'name: {name}\nkind: module\nmodule: {module}\nregion: code\n'
            f'address: {address:#x}\nexpect: {expected.hex()}\nreplace: {code.hex()}\n'
            f'gate: {gate}\nrationale: {rationale}\n')
    lay = assemble()[2]
    print(f"Wheel acceleration: home A {lay['a_used']} of {HOME_A_END - HOME_A} bytes, "
          f"home B {lay['b_used']} of {HOME_B_END - HOME_B}, state {lay['state']:#x}")


if __name__ == '__main__':
    main()
