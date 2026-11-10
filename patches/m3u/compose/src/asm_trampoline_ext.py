#!/usr/bin/env python3
"""Assemble the M3U hook trampoline for the module 31 segment
extension placement, with the GNU Arm assembler, then verify the
blob by Capstone-decoding it against the source.

Adapted from work/m3u_bridge/scratch/asm_trampoline.py (the module 0
extension version); the instruction sequence is unchanged. Only the
placement constants differ, and they are arguments here:

  --base     exec address of the trampoline (payload offset 0)
  --bridge   exec address of m3u_bridge_node_action
  --slot     bytes reserved for the trampoline in the payload
             (code is padded with Thumb NOPs to the slot size)
  --out      output binary (exactly --slot bytes)
  --site-out output file for patch 0040's replacement bytes: the
             B.W encoding at the hook site 0x0307DF1A to --base

The trampoline contract (work/m3u_bridge/m3u_bridge.md job 4): at the
hook site r4 = node, r5 = class byte, r7 = browser state, r8 = play
context, lr = the node-action caller's return address. No match (or
bridge decline): reproduce the displaced BL 0x0307D1F8 with r0 = r5
and resume at 0x0307DF1E with lr restored. Handled: leave through
the stock common exit at 0x0307E0C8 with r0 = 1.
"""
import argparse
import subprocess
import tempfile
import struct
from pathlib import Path

HOOK_SITE = 0x0307DF1A

SRC = [
    ('m3u_hook:', None),
    (None, 'push {lr}'),
    (None, 'ldrb.w r1, [r4, 0x57]'),      # node name ext char 0 (SFN +0x4F+8)
    (None, 'cmp r1, 0x4d'),               # 'M'
    (None, 'bne nomatch'),
    (None, 'ldrb.w r1, [r4, 0x58]'),
    (None, 'cmp r1, 0x33'),               # '3'
    (None, 'bne nomatch'),
    (None, 'ldrb.w r1, [r4, 0x59]'),
    (None, 'cmp r1, 0x55'),               # 'U'
    (None, 'bne nomatch'),
    (None, 'mov r0, r4'),                 # bridge(node, state, ctx)
    (None, 'mov r1, r7'),
    (None, 'mov r2, r8'),
    (None, 'bl m3u_bridge_node_action'),
    (None, 'cmp r0, 0'),
    (None, 'bne handled'),
    ('nomatch:', None),
    (None, 'mov r0, r5'),                 # displaced call's argument: class
    (None, 'bl 0x0307d1f8'),              # the displaced BL, reproduced
    (None, 'pop {lr}'),
    (None, 'b.w 0x0307df1e'),             # resume stock flow after hook site
    ('handled:', None),
    (None, 'pop {lr}'),
    (None, 'movs r0, 1'),                 # stock folder-play success code
    (None, 'b.w 0x0307e0c8'),             # stock common exit (add sp,#0x4c; pop.w)
]


def assemble_at(base, source):
    """Assemble and link at the execution address, using the target toolchain."""
    with tempfile.TemporaryDirectory(prefix="fosi-trampoline-") as td:
        root = Path(td)
        asm, obj, elf, binary, script = (root / n for n in
                                          ("code.S", "code.o", "code.elf", "code.bin", "link.ld"))
        asm.write_text(".syntax unified\n.thumb\n.section .text, \"ax\"\n" + source + "\n")
        script.write_text(f"SECTIONS {{ . = {base:#x}; .text : {{ *(.text*) }} }}\n")
        subprocess.run(["arm-none-eabi-gcc", "-mcpu=cortex-m3", "-mthumb", "-c", str(asm), "-o", str(obj)], check=True)
        subprocess.run(["arm-none-eabi-gcc", "-mcpu=cortex-m3", "-mthumb", "-nostdlib", "-T", str(script), str(obj), "-o", str(elf)], check=True)
        subprocess.run(["arm-none-eabi-objcopy", "-O", "binary", str(elf), str(binary)], check=True)
        return binary.read_bytes()


def branch(site, target, link=False):
    off = target - (site + 4)
    if off & 1 or not -(1 << 24) <= off < (1 << 24):
        raise ValueError("Thumb branch target out of range")
    sign, i1, i2 = (off >> 24) & 1, (off >> 23) & 1, (off >> 22) & 1
    j1, j2 = (~(i1 ^ sign)) & 1, (~(i2 ^ sign)) & 1
    return struct.pack("<HH", 0xf000 | (sign << 10) | ((off >> 12) & 0x3ff),
                       (0xd000 if link else 0x9000) | (j1 << 13) | (j2 << 11) | ((off >> 1) & 0x7ff))


def assemble(base, bridge):
    # Resolve local labels with GNU as; replace self-branch placeholders
    # for external absolute addresses with audited Thumb-2 encodings.
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    external = {"bl m3u_bridge_node_action": (bridge, True),
                "bl 0x0307d1f8": (0x0307d1f8, True),
                "b.w 0x0307df1e": (0x0307df1e, False),
                "b.w 0x0307e0c8": (0x0307e0c8, False)}
    lines, targets = [], []
    for label, text in SRC:
        if label:
            lines.append(label)
        if text:
            if text in external:
                target, link = external[text]
                targets.append((target, link))
                text = "bl ." if link else "b.w ."
            lines.append("    " + text)
    blob = bytearray(assemble_at(base, "\n".join(lines)))
    insns = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(bytes(blob), base))
    placeholders = [i for i in insns if i.mnemonic in ("bl", "b.w") and
                    i.op_str == f"#0x{i.address:x}"]
    if len(placeholders) != len(targets):
        raise ValueError("unexpected trampoline branch placeholders")
    for insn, (target, link) in zip(placeholders, targets):
        off = insn.address - base
        blob[off:off + 4] = branch(insn.address, target, link)
    return bytes(blob)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', type=lambda x: int(x, 0), required=True)
    ap.add_argument('--bridge', type=lambda x: int(x, 0), required=True)
    ap.add_argument('--slot', type=int, default=64)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--site-out', type=Path, required=True)
    a = ap.parse_args()

    blob = assemble(a.base, a.bridge)
    if len(blob) > a.slot:
        raise SystemExit(f'trampoline code {len(blob)} bytes overruns '
                         f'the {a.slot}-byte slot')
    if (a.slot - len(blob)) % 2:
        raise SystemExit('slot padding is not a whole number of NOPs')
    nop = bytes.fromhex('00bf')  # Thumb NOP (0xBF00), exec-safe padding
    full = blob + nop * ((a.slot - len(blob)) // 2)
    a.out.write_bytes(full)
    print(f'trampoline code {len(blob)} bytes, slot {a.slot}')

    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    insns = list(md.disasm(full, a.base))
    for insn in insns:
        print(f'{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}')
    # audit: the four control transfers must land where the design says
    targets = {}
    for insn in insns:
        if insn.mnemonic in ('bl', 'b.w', 'b', 'bne'):
            targets.setdefault(insn.op_str, []).append(insn.address)
    expect = {
        f'#0x{a.bridge:x}': 'bridge call',
        '#0x307d1f8': 'displaced call',
        '#0x307df1e': 'resume',
        '#0x307e0c8': 'common exit',
    }
    for tgt, what in expect.items():
        assert tgt in targets, f'missing {what} transfer to {tgt}'
    print('trampoline audit: all four transfers present')

    enc = branch(HOOK_SITE, a.base)
    dec = list(md.disasm(enc, HOOK_SITE))
    assert len(dec) == 1 and dec[0].op_str == f'#0x{a.base:x}', dec
    a.site_out.write_bytes(enc)
    print(f'patch 0040 replace bytes at {HOOK_SITE:#x}: {enc.hex()}')


if __name__ == '__main__':
    main()
