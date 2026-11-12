/* Original CE drawing code; SDK consulted for API semantics only. */
.syntax unified
.thumb
.section .text.time,"ax",%progbits
.global player_time
.thumb_func
player_time:
    push {r4, lr}
    sub sp, #32
    mov r4, r3
    /* Stock time layout displays minutes and seconds; cap at 99:59. */
    cmp r0, #0
    it ne
    movne r1, #99
    movs r3, #10
    udiv r0, r1, r3
    mls r1, r0, r3, r1
    adds r0, #48
    adds r1, #48
    strh r0, [sp, #0]
    strh r1, [sp, #2]
    movs r0, #58
    strh r0, [sp, #4]
    udiv r0, r2, r3
    mls r2, r0, r3, r2
    adds r0, #48
    adds r2, #48
    strh r0, [sp, #6]
    strh r2, [sp, #8]
    movs r0, #0
    strh r0, [sp, #10]
    cmp r4, #0
    ite eq
    moveq r0, #7
    movne r0, #167
    strh r0, [sp, #16]
    movw r0, #256
    strh r0, [sp, #18]
    cmp r4, #0
    ite eq
    moveq r0, #72
    movne r0, #232
    strh r0, [sp, #20]
    movw r0, #271
    strh r0, [sp, #22]
    add r0, sp, #16
    mov r1, r0
    mov r2, sp
    movs r3, #0
    ldr ip, =0x03062CEF
    blx ip
    cmp r4, #0
    beq 1f
    ldr r0, =0x030247E4
    movs r1, #0
    strb r1, [r0]
1:  add sp, #32
    pop {r4, pc}
.ltorg

.section .text.marquee,"ax",%progbits
.global marquee_stamp
.thumb_func
marquee_stamp:
    ldr r0, [r6]
    str r0, [r5, #0x28]
    movs r0, #50
    strh r0, [r5, #0x2C]
    bx lr
