#!/usr/bin/env python3
"""Assemble the M3U hook trampoline with rz-asm (two-pass, labels),
then verify the blob by Capstone-decoding it against the source.

Layout in the module 0 extension (exec 0x03079C14):
  +0x00  m3u_hook          this trampoline
  +0x80  m3u_bridge_node_action   bridge entry (stub for now)
Everything between trampoline end and +0x80 is zero padding.
"""
import subprocess
import sys
from pathlib import Path

RZASM = '/home/hatch/workspace/fosi-dap-neo/tools-local/bin/rz-asm'
BASE = 0x03079C14
BRIDGE_OFF = 0x80

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


def rz(addr, text):
    r = subprocess.run([RZASM, '-a', 'arm', '-b', '16', '-o', hex(addr), text],
                       capture_output=True, text=True)
    hx = r.stdout.strip()
    if r.returncode != 0 or not hx or len(hx) % 2:
        raise RuntimeError(f'rz-asm failed at {addr:#x}: {text!r} -> {r.stdout} {r.stderr}')
    return bytes.fromhex(hx)


def assemble():
    # pass 1: sizes with every label resolved to BASE as a dummy target
    # (sizes are target-stable for every form used here)
    labels = {}
    addr = BASE
    items = []
    names = [lbl.rstrip(':') for lbl, _ in SRC if lbl] + ['m3u_bridge_node_action']
    for label, text in SRC:
        if label:
            labels[label.rstrip(':')] = addr
        if text:
            items.append((addr, text))
            dummy = text
            for nm in names:
                dummy = dummy.replace(nm, hex(BASE))
            addr += len(rz(addr, dummy))
    labels['m3u_bridge_node_action'] = BASE + BRIDGE_OFF
    # pass 2: real targets
    blob = bytearray()
    for addr, text in items:
        for name, la in labels.items():
            text = text.replace(name, hex(la))
        enc = rz(addr, text)
        assert addr - BASE == len(blob)
        blob += enc
    return bytes(blob), labels


def main():
    blob, labels = assemble()
    assert len(blob) <= BRIDGE_OFF, f'trampoline {len(blob)}B overruns bridge offset'
    nop = bytes.fromhex('00bf')  # Thumb NOP (0xBF00), exec-safe padding
    pad = nop * ((BRIDGE_OFF - len(blob)) // 2)
    # stub at BRIDGE_OFF: movs r0, #0 (0x2000); bx lr (0x4770)
    full = blob + pad + bytes.fromhex('00207047')
    out = Path(__file__).with_name('extension_blob.bin')
    out.write_bytes(full)
    print(f'trampoline {len(blob)} bytes; blob {len(full)} bytes; labels {labels}')
    # verify: capstone decode of the whole blob at BASE
    sys.path.insert(0, '/home/hatch/workspace/fosi-dap-neo/venv/lib/python3.12/site-packages')
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    for insn in md.disasm(full, BASE):
        print(f'{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}')
    # verify patch 0040's replacement: B.W at the hook site to m3u_hook
    enc = rz(0x0307DF1A, f'b.w {hex(BASE)}')
    dec = list(md.disasm(enc, 0x0307DF1A))
    print('patch 0040 replace bytes:', enc.hex(), '(expect stock fff76df9)',
          '-> decodes as:', [(i.mnemonic, i.op_str) for i in dec])
    assert len(dec) == 1 and dec[0].mnemonic in ('b', 'b.w') and dec[0].op_str == '#0x3079c14'
    stub = full[BRIDGE_OFF:BRIDGE_OFF + 4]
    sdec = [(i.mnemonic, i.op_str) for i in md.disasm(stub, BASE + BRIDGE_OFF)]
    print('bridge stub decodes as:', sdec)
    assert sdec == [('movs', 'r0, #0'), ('bx', 'lr')]
    Path(__file__).with_name('hook_replace.bin').write_bytes(enc)


if __name__ == '__main__':
    main()
