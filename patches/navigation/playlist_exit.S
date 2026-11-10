.syntax unified
.thumb
.section .text,"ax"
.global folder_start, file_start, folder_continue, file_call, file_continue
.thumb_func
folder_start:
    push {r1, r2}
    movw r1, #0xbfb4
    movt r1, #0x0307
    mov.w r2, #0
    strb r2, [r1]
    pop {r1, r2}
    movs r5, #1                 /* displaced */
    mov r0, r5                 /* displaced */
folder_continue:
    b.w .                       /* patched to 0x0307E052 */
.thumb_func
file_start:
    push {r1, r2}
    movw r1, #0xbfb4
    movt r1, #0x0307
    mov.w r2, #0
    strb r2, [r1]
    pop {r1, r2}
    ldr r0, stock_cell          /* displaced PC-relative load */
file_call:
    bl .                        /* displaced call to 0x030570A4 */
    ldr.w lr, original_lr       /* original return address after BL */
file_continue:
    b.w .                       /* patched to 0x0307E1D2 */
.align 2
stock_cell:
    .word 0x03023d38
original_lr:
    .word 0x0307e1d3
