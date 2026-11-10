.syntax unified
.thumb
.section .text,"ax"
.global tag_start, tag_continue
.thumb_func
tag_start:
    push {r0, r1}
    movw r0, #0xbfb4
    movt r0, #0x0307
    mov.w r1, #0
    strb r1, [r0]
    pop {r0, r1}
    strh.w ip, [r5, #0xf2]      /* displaced category commit */
tag_continue:
    b.w .                       /* patched to 0x0307EC76 */
