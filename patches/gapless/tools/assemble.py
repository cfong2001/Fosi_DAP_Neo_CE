#!/usr/bin/env python3
"""Assemble the gapless caves with rz-asm at their final addresses and
verify every instruction by re-disassembling with capstone in place."""
import subprocess, os, sys
os.chdir(os.path.expanduser('~/workspace/fosi-dap-neo'))
RZ = 'tools-local/bin/rz-asm'

def asm(addr, text):
    out = subprocess.run([RZ, '-a', 'arm', '-b', '16', '-o', hex(addr), text],
                         capture_output=True, text=True)
    h = out.stdout.strip()
    if out.returncode != 0 or not h or 'ERROR' in h:
        raise SystemExit(f"ASM FAIL @{addr:#x}: {text!r} -> {out.stdout} {out.stderr}")
    return bytes.fromhex(h)

# ---------------- gate cave @ 0x03051664 (32 B) ----------------
G = 0x03051664
gate = b''
for addr, text in [
    (G+0x00, 'push {r4, r5, r6, lr}'),
    (G+0x02, 'mov r5, r0'),
    (G+0x04, 'sub.w r6, pc, 188'),        # r6 = 0x030515B0 (state pair)
    (G+0x08, 'ldr r0, [r6]'),
    (G+0x0A, 'lsls r0, r0, 25'),          # mask state to 7 bits (drop fast-path flag)
    (G+0x0C, 'lsrs r0, r0, 25'),
    (G+0x0E, 'cmp r0, r5'),
    (G+0x10, 'b 0x03051676'),             # DISARMED: ignore compare, always stock
    (G+0x12, 'str r5, [r6]'),             # state = arg (stock load follows)
    (G+0x14, 'b.w 0x0306cb30'),           # stock continuation of reset-and-start
    (G+0x18, 'movs r4, 128'),
    (G+0x1A, 'orrs r5, r4'),          # state value = arg | 0x80
    (G+0x1C, 'str r5, [r6]'),
    (G+0x1E, 'pop {r4, r5, r6, pc}'),     # skip path: return to codec case
]:
    b = asm(addr, text)
    assert addr - G + len(b) <= 32, (hex(addr), text, len(b))
    gate += b
assert len(gate) == 32, len(gate)
armed_branch = asm(G+0x10, 'beq 0x0305167c')   # ARM patch (0016) replace bytes
assert len(armed_branch) == 2

# ---------------- delay cave @ 0x030514FE (26 B) ----------------
D = 0x030514FE
delay = b''
for addr, text in [
    (D+0x00, 'adr r1, 176'),              # r1 = 0x030515B0 (state pair)
    (D+0x02, 'ldr r3, [pc, 384]'),        # literal pool @ 0x03051684 -> 0x030368D8
    (D+0x04, 'ldr r3, [r3, 8]'),          # new sample rate [info+8]
    (D+0x06, 'ldr r2, [r1, 4]'),          # prev rate
    (D+0x08, 'str r3, [r1, 4]'),          # prev = new (every invocation)
    (D+0x0A, 'cmp r3, r2'),
    (D+0x0C, 'bne 0x03051514'),
    (D+0x0E, 'ldr r2, [r1]'),             # state
    (D+0x10, 'cmp r2, 128'),
    (D+0x12, 'bcc 0x03051514'),
    (D+0x14, 'bx lr'),                    # SKIP: return to load-start tail
    (D+0x16, 'b.w 0x03064944'),           # stock: tail-call delay_ms (r0, lr intact)
]:
    b = asm(addr, text)
    assert addr - D + len(b) <= 26, (hex(addr), text, len(b))
    delay += b
assert len(delay) == 26, len(delay)

# ---------------- hooks ----------------
gate_hook = asm(0x0306CB2C, 'b.w 0x03051664')
delay_hook = asm(0x03088FEA, 'bl 0x030514fe')

print('gate cave   :', gate.hex())
print('gate armed branch @+0x10:', armed_branch.hex(), '(disarmed:', gate[0x10:0x12].hex() + ')')
print('delay cave  :', delay.hex())
print('gate hook   :', gate_hook.hex())
print('delay hook  :', delay_hook.hex())

# ---------------- verify by disassembly in place ----------------
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
for name, blob, base in [('GATE CAVE', gate, G), ('DELAY CAVE', delay, D)]:
    print(f'--- {name} @{base:#x}')
    for ins in md.disasm(blob, base):
        print(f'  {ins.address:08x}  {ins.bytes.hex():<10} {ins.mnemonic:<8} {ins.op_str}')
for name, blob, base in [('GATE HOOK', gate_hook, 0x0306CB2C), ('DELAY HOOK', delay_hook, 0x03088FEA),
                          ('ARMED BRANCH', armed_branch, G+0x10)]:
    ins = next(md.disasm(blob, base))
    print(f'{name}: {ins.mnemonic} {ins.op_str}  [{blob.hex()}]')
