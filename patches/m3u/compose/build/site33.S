    .syntax unified
    .thumb
    .section .patch, "ax"
    .org 0
    b.w ui_lockscreen_paint
    .equ ui_lockscreen_paint, 0x308087c
