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
    movne r0, #191
    strh r0, [sp, #16]
    movw r0, #240
    strh r0, [sp, #18]
    cmp r4, #0
    ite eq
    moveq r0, #72
    movne r0, #239
    strh r0, [sp, #20]
    movw r0, #253
    strh r0, [sp, #22]
    add r0, sp, #16
    mov r1, r0
    mov r2, sp
    movs r3, #0
    ldr ip, =0x030513C1
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

/* Clear the text rectangle before rendering tabular digits. Main-font ink
 * occupies rows 2..12; the 14-row line ends before the bar at y=254. */
.section .text.draw,"ax",%progbits
.global time_draw
.thumb_func
time_draw:
    push {r0, r1, r2, lr}
    sub sp, #8
    ldr r3, =0x03004400
    ldrh r3, [r3]
    str r3, [sp]
    ldrh r3, [r0, #6]
    ldrh r2, [r0, #4]
    ldrh r1, [r0, #2]
    ldrh r0, [r0]
    ldr ip, =0x030632FB
    blx ip
    add sp, #8
    pop.w {r0, r1, r2, lr}
    movs r3, #0
    ldr ip, =0x03062CEF
    bx ip
.ltorg
