    .syntax unified
    .thumb
    .section .patch, "ax"
    .org 0
    /* B.W from 0x0307E89E to the standalone entry at 0x0307EE48.
       Absolute .equ branch relocations are rejected by newer binutils. */
    .hword 0xf000, 0xbad3
