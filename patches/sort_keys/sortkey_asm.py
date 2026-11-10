#!/usr/bin/env python3
"""Assemble the sort-key cave routines for module 39 (DAP Neo DP3_V137).

Two-pass mini-assembler driving tools-local/bin/rz-asm instruction by
instruction (no arm-none-eabi toolchain exists in this environment).
Branch forms are width-fixed by construction (b.w / bl = 4 bytes,
conditional branches = 2 bytes), so label addresses converge.

Exports: build() -> (blob_bytes, symbols dict, listing text).
The Latin-1 fold table bytes come from host_ref.FOLD_TABLE_BYTES so the
host reference and the device code share one source of truth.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from host_ref import FOLD_TABLE_BYTES  # noqa: E402

RZASM = str(HERE.parents[2] / 'tools-local' / 'bin' / 'rz-asm')
BASE = 0x0309F000

SOURCE = r"""
; ================= cave_cmp : patched comparator body =================
; in: r0 = &recA_key (record+4), r1 = &recB_key ; out: r0 = 0 less,1 eq,2 gt
; ABI mirrors stock 0x0307d620 (called with bl, returns in r0).
cave_cmp:
    push {r4, r5, r6, r7, r8, lr}
    mov r4, r0
    mov r5, r1
    movs r6, #0
cc_pfx:
    ldrh r0, [r4, r6]
    ldrh r1, [r5, r6]
    cmp r0, #1
    beq cc_full
    cmp r1, #1
    beq cc_full
    cmp r0, r1
    bhi cc_gt
    bcc cc_lt
    cmp r0, #0
    beq cc_eq
    adds r6, r6, #2
    cmp r6, #8
    bcc cc_pfx
cc_full:
    ldrh r0, [r4, #8]
    bl sk_str_addr
    mov r6, r0
    ldrh r0, [r5, #8]
    bl sk_str_addr
    mov r7, r0
    movw r8, #0xe1ec
    movt r8, #0x0307
    ldr r0, [r8, #8]
    cmp r0, r6
    beq cc_b
    mov r1, r6
    movw r0, #0x0001
    movt r0, #0x0003
    movw r2, #0x0100
    movw r3, #0xf28c
    movt r3, #0x0307
    bl 0x03067510
    str r6, [r8, #8]
cc_b:
    ldr r0, [r8, #12]
    cmp r0, r7
    beq cc_go
    mov r1, r7
    movw r0, #0x0001
    movt r0, #0x0003
    movw r2, #0x0100
    movw r3, #0xf38c
    movt r3, #0x0307
    bl 0x03067510
    str r7, [r8, #12]
cc_go:
    movw r0, #0xf28c
    movt r0, #0x0307
    movw r1, #0xf38c
    movt r1, #0x0307
    bl sk_tcmp
    cmp r0, #0
    blt cc_lt
    bgt cc_gt
cc_eq:
    movs r0, #1
    pop {r4, r5, r6, r7, r8, pc}
cc_lt:
    movs r0, #0
    pop {r4, r5, r6, r7, r8, pc}
cc_gt:
    movs r0, #2
    pop {r4, r5, r6, r7, r8, pc}

; ================= cave_pfx : patched builder key writer =================
; in: r0 = record (14-byte sort record, index already stored at +0xc)
; reads the full name by index and stores T's first 4 units at record+4.
cave_pfx:
    push {r4, r5, r6, r7, r8, r9, r10, r11, lr}
    mov r4, r0
    ldrh r0, [r4, #12]
    bl sk_str_addr
    mov r1, r0
    movw r0, #0x0001
    movt r0, #0x0003
    movw r2, #0x0100
    movw r3, #0xf28c
    movt r3, #0x0307
    bl 0x03067510
    movw r8, #0xe1ec
    movt r8, #0x0307
    mvn r0, #0
    str r0, [r8, #8]
    str r0, [r8, #12]
    mov r0, r4
    movw r1, #0xf28c
    movt r1, #0x0307
    bl sk_pfx4
    pop {r4, r5, r6, r7, r8, r9, r10, r11, pc}

; ================= sk_str_addr : string DB address from index =================
; in: r0 = string index ; out: r0 = device address ; clobbers r0-r2, r12
sk_str_addr:
    movw r1, #0x329c
    movt r1, #0x0302
    ldr r1, [r1]
    movw r2, #0x47ec
    movt r2, #0x0302
    ldr r12, [r2, #4]
    add r1, r1, r12
    lsl r1, r1, #9
    ldr r2, [r2]
    add r1, r1, r2
    add r0, r1, r0, lsl #11
    bx lr

; ================= sk_tcmp : full transformed compare =================
; in: r0 = bufA, r1 = bufB (0x100-byte UTF-16 buffers) ; out: r0 = -1|0|1
sk_tcmp:
    push {r4, r5, r6, lr}
    sub sp, #56
    mov r4, sp
    add r5, sp, #28
    mov r6, r1
    mov r1, r0
    mov r0, r4
    bl gen_init
    mov r0, r5
    mov r1, r6
    bl gen_init
tc_loop:
    mov r0, r4
    bl gen_next
    mov r6, r0
    mov r0, r5
    bl gen_next
    cmn r6, #1
    bne tc_n1
    movs r6, #0
tc_n1:
    cmn r0, #1
    bne tc_n2
    movs r0, #0
tc_n2:
    cmp r6, r0
    bhi tc_gt
    bcc tc_lt
    cmp r6, #0
    bne tc_loop
    movs r0, #0
    b.w tc_out
tc_gt:
    movs r0, #1
    b.w tc_out
tc_lt:
    mvn r0, #0
tc_out:
    add sp, #56
    pop {r4, r5, r6, pc}

; ================= sk_pfx4 : first 4 T units into a record =================
; in: r0 = record, r1 = name buffer
sk_pfx4:
    push {r4, r5, lr}
    sub sp, #28
    mov r4, r0
    mov r0, sp
    bl gen_init
    adds r4, r4, #4
    movs r5, #4
pf_loop:
    mov r0, sp
    bl gen_next
    cmn r0, #1
    bne pf_st
    movs r0, #0
pf_st:
    strh r0, [r4]
    adds r4, r4, #2
    subs r5, r5, #1
    bne pf_loop
    add sp, #28
    pop {r4, r5, pc}

; ================= gen_init : state init + space trim + article =================
; in: r0 = state (28 bytes), r1 = buffer (0x100 bytes)
; state: +0 CUR, +4 END, +8 PEND(-1), +12 TSTAGE, +16 TN, +20 TDPTR, +24 TDLEFT
gen_init:
    push {lr}
    str r1, [r0]
    adds r2, r1, #0x100
    str r2, [r0, #4]
    mvn r2, #0
    str r2, [r0, #8]
    movs r2, #0
    str r2, [r0, #12]
    mov r2, r1
    mov r3, r1
gi_trim:
    ldr r12, [r0, #4]
    cmp r2, r12
    bcs gi_trimdone
    ldrh r12, [r2]
    cmp.w r12, #0
    beq gi_trimdone
    adds r2, r2, #2
    cmp.w r12, #0x20
    beq gi_trim
    mov r3, r2
    b.w gi_trim
gi_trimdone:
    str r3, [r0, #4]
    ldr r1, [r0]
    ldr r2, [r0, #4]
gi_lead:
    cmp r1, r2
    bcs gi_art
    ldrh r3, [r1]
    cmp r3, #0x20
    bne gi_art
    adds r1, r1, #2
    b.w gi_lead
gi_art:
    str r1, [r0]
    mov r12, r1
    ldr r2, [r0, #4]
    subs r2, r2, r1
    cmp r2, #10
    bcc gi_done
    ldrh r3, [r12]
    bl sk_fold
    cmp r1, #0x54
    bne gi_done
    ldr r12, [r0]
    ldrh r3, [r12, #2]
    bl sk_fold
    cmp r1, #0x48
    bne gi_done
    ldr r12, [r0]
    ldrh r3, [r12, #4]
    bl sk_fold
    cmp r1, #0x45
    bne gi_done
    ldr r12, [r0]
    ldrh r3, [r12, #6]
    cmp r3, #0x20
    bne gi_done
    ldr r12, [r0]
    add r2, r12, #8
    ldr r3, [r0, #4]
gi_artskip:
    cmp r2, r3
    bcs gi_done
    ldrh r12, [r2]
    cmp.w r12, #0x20
    bne gi_strip
    adds r2, r2, #2
    b.w gi_artskip
gi_strip:
    str r2, [r0]
gi_done:
    pop {pc}

; ================= gen_next : next T unit from a state =================
; in: r0 = state ; out: r0 = unit, or -1 at end ; clobbers r0-r3, r12
gen_next:
    push {lr}
    ldr r1, [r0, #8]
    cmn r1, #1
    beq gn_stage
    mvn r2, #0
    str r2, [r0, #8]
    mov r0, r1
    b.w gn_ret
gn_stage:
    ldr r1, [r0, #12]
    cmp r1, #1
    beq gn_count
    cmp r1, #2
    beq gn_digits
    b.w gn_fetch
gn_count:
    movs r1, #2
    str r1, [r0, #12]
    ldr r0, [r0, #16]
    b.w gn_ret
gn_digits:
    ldr r1, [r0, #24]
    cmp r1, #0
    beq gn_digdone
    subs r1, r1, #1
    str r1, [r0, #24]
    ldr r1, [r0, #20]
    ldrh r2, [r1]
    adds r1, r1, #2
    str r1, [r0, #20]
    mov r0, r2
    b.w gn_ret
gn_digdone:
    movs r1, #0
    str r1, [r0, #12]
gn_fetch:
    ldr r1, [r0]
    ldr r2, [r0, #4]
    cmp r1, r2
    bcs gn_end
    ldrh r3, [r1]
    cmp r3, #0
    beq gn_end
    subs r2, r3, #0x30
    cmp r2, #9
    bls gn_run
    bl sk_fold
    cmp r3, #1
    beq gn_drop
    ldr r3, [r0]
    adds r3, r3, #2
    str r3, [r0]
    str r2, [r0, #8]
    mov r0, r1
    b.w gn_ret
gn_drop:
    ldr r3, [r0]
    adds r3, r3, #2
    str r3, [r0]
    b.w gn_fetch
gn_end:
    mvn r0, #0
    b.w gn_ret
gn_run:
    mov r2, r1
gr_scan:
    ldr r3, [r0, #4]
    cmp r2, r3
    bcs gr_scanned
    ldrh r3, [r2]
    subs r3, r3, #0x30
    cmp r3, #9
    bhi gr_scanned
    adds r2, r2, #2
    b.w gr_scan
gr_scanned:
    mov r3, r1
gr_sig:
    ldrh r12, [r3]
    cmp.w r12, #0x30
    bne gr_set
    adds r12, r3, #2
    cmp r12, r2
    bcs gr_set
    mov r3, r12
    b.w gr_sig
gr_set:
    subs r1, r2, r3
    lsrs r1, r1, #1
    str r1, [r0, #16]
    str r1, [r0, #24]
    str r3, [r0, #20]
    str r2, [r0]
    movs r2, #1
    str r2, [r0, #12]
    movs r0, #1
    b.w gn_ret
gn_ret:
    pop {pc}

; ================= sk_fold : fold one unit =================
; in: r3 = c ; out: r1 = first, r2 = second|-1, r3 = 1 if dropped else 0
; clobbers r1, r2, r3, r12 ; preserves r0
sk_fold:
    mov r1, r3
    mvn r2, #0
    movs r3, #0
    subs r12, r1, #0x61
    cmp.w r12, #0x19
    bhi sf_comb
    subs r1, r1, #0x20
    bx lr
sf_comb:
    subs r12, r1, #0x300
    cmp.w r12, #0x6f
    bhi sf_oe
    movs r3, #1
    bx lr
sf_oe:
    movw r12, #0x0152
    cmp r1, r12
    beq sf_oe2
    movw r12, #0x0153
    cmp r1, r12
    bne sf_tab
sf_oe2:
    movs r1, #0x4f
    movs r2, #0x45
    bx lr
sf_tab:
    subs r12, r1, #0xc0
    cmp.w r12, #0x3f
    bhi sf_ret
    movw r3, #L16(fold_table)
    movt r3, #H16(fold_table)
    lsls r12, r12, #1
    add r3, r3, r12
    ldrb r2, [r3]
    cmp r2, #0
    beq sf_tabid
    mov r1, r2
    ldrb r2, [r3, #1]
    cmp r2, #0
    bne sf_tabdone
    mvn r2, #0
sf_tabdone:
    movs r3, #0
    bx lr
sf_tabid:
    mvn r2, #0
    movs r3, #0
    bx lr
sf_ret:
    bx lr

fold_table:
    .foldtable
"""


def _parse():
    items = []          # ('label', name) | ('insn', text) | ('table', None)
    for raw in SOURCE.splitlines():
        line = raw.split(';', 1)[0].strip()
        if not line:
            continue
        if line.endswith(':'):
            items.append(('label', line[:-1].strip()))
        elif line == '.foldtable':
            items.append(('table', None))
        else:
            items.append(('insn', line))
    return items


def _assemble_one(addr, text, labels):
    # resolve label operands + L16/H16 immediates
    out = []
    for tok in text.replace(',', ' , ').split():
        if tok in labels:
            out.append(hex(labels[tok]))
        elif tok.startswith('#L16(') and tok.endswith(')'):
            out.append('#' + hex(labels[tok[5:-1]] & 0xFFFF))
        elif tok.startswith('#H16(') and tok.endswith(')'):
            out.append('#' + hex((labels[tok[5:-1]] >> 16) & 0xFFFF))
        else:
            out.append(tok)
    text2 = ' '.join(out).replace(' , ', ', ')
    r = subprocess.run([RZASM, '-a', 'arm', '-b', '16', '-o', hex(addr), text2],
                       capture_output=True, text=True)
    hx = r.stdout.strip()
    if r.returncode != 0 or not hx or len(hx) % 2:
        raise RuntimeError(f'rz-asm failed at {addr:#x}: {text!r} -> {text2!r}: '
                           f'{r.stdout} {r.stderr}')
    return bytes.fromhex(hx)


def build():
    items = _parse()
    labels = {name: BASE for kind, name in items if kind == 'label'}
    blob = b''
    for _ in range(8):
        addr = BASE
        labels_new = {}
        chunks = []
        for kind, val in items:
            if kind == 'label':
                labels_new[val] = addr
            elif kind == 'table':
                chunks.append(FOLD_TABLE_BYTES)
                addr += len(FOLD_TABLE_BYTES)
            else:
                b = _assemble_one(addr, val, labels)
                chunks.append(b)
                addr += len(b)
        blob = b''.join(chunks)
        if labels_new == labels:
            break
        labels = labels_new
    else:
        raise RuntimeError('label addresses did not converge')
    # listing
    lines = []
    addr = BASE
    li = 0
    listing = []
    for kind, val in items:
        if kind == 'label':
            listing.append(f'{val}:')
        elif kind == 'table':
            listing.append(f'    <fold table {len(FOLD_TABLE_BYTES)} bytes>')
            addr += len(FOLD_TABLE_BYTES)
        else:
            n = 0
            # recompute this instruction's bytes from the final blob
            # (walk sizes again with final labels)
            b = _assemble_one(addr, val, labels)
            listing.append(f'{addr:08x}  {b.hex(" "):<12} {val}')
            addr += len(b)
    return blob, labels, '\n'.join(listing)


if __name__ == '__main__':
    blob, labels, listing = build()
    print(f'blob: {len(blob)} bytes at {BASE:#x}..{BASE + len(blob):#x} '
          f'(cave budget {0x0309F4AC - BASE:#x})')
    for k, v in labels.items():
        print(f'  {k:14s} {v:#x}')
    (HERE / 'cave.bin').write_bytes(blob)
    (HERE / 'cave_listing.txt').write_text(listing + '\n')
    print('wrote cave.bin + cave_listing.txt')
