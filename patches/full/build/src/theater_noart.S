/*
 * Theater mode: restore the theme background when a track has no artwork.
 *
 * The theater reset stub runs inside artwork setup (module 18, 0x0308389E),
 * so it restores the theme default only when setup is called. The player's
 * artwork loader in module 27 skips setup on two exits:
 *
 *   0x0307E96C  the audio file did not open
 *   0x0307E972  the locator found no picture, or setup returned 0
 *
 * On those exits the background cell kept the previous track's color.
 * Patches 0045 and 0046 send both exits here. Each entry restores the
 * displaced instructions around a call to theater_default, which disarms
 * sampling, writes the theme default to the background cell and, when the
 * cell changed, posts the same repaint event bit the trampoline's finalize
 * posts (0x03023CFC, bit 0x02000000).
 *
 * The theme default rule is the reset stub's: 0x10A2 for the dark theme
 * (SAVEINFO+0x2D8 == 0), else palette cell 0 at 0x030235B4.
 */
    .syntax unified
    .thumb

    .equ THEATER_STATE, 0x03023468
    .equ SAVEINFO, 0x030232A0
    .equ PALCELL, 0x030235B4
    .equ BGCELL, 0x03004400
    .equ EVWORD, 0x03023CFC
    .equ EVMASK, 0x02000000
    .equ RESUME_NA, 0x0307E978     /* sxtb r0, r0 before closing the file */

    .text

/* B.W from 0x0307E972, replacing "str r4, [r6]; ldrb.w r0, [r8]".
 * r4 = 0, r6 = the art-present cell, r8 = the file handle cell. */
    .global theater_noart_close
    .type theater_noart_close, %function
theater_noart_close:
    str     r4, [r6]
    push    {r3, lr}
    bl      theater_default
    pop.w   {r3, lr}
    ldrb.w  r0, [r8]
    b.w     RESUME_NA
    .size theater_noart_close, . - theater_noart_close

/* B.W from 0x0307E96C, replacing "str r4, [r6]" and the first half of the
 * loader's exit pop. The loader's frame is still on the stack. */
    .global theater_noart_open
    .type theater_noart_open, %function
theater_noart_open:
    str     r4, [r6]
    bl      theater_default
    pop.w   {r3, r4, r5, r6, r7, r8, sb, pc}
    .size theater_noart_open, . - theater_noart_open

/* Preserves every register and the flags' consumers (callers do not test
 * flags after the call). */
    .type theater_default, %function
theater_default:
    push    {r0, r1, r2, r3, r4, lr}
    ldr     r1, =THEATER_STATE
    movs    r0, #0
    strb    r0, [r1, #25]          /* flags: not armed */
    ldr     r1, =SAVEINFO
    ldrb.w  r0, [r1, #0x2d8]       /* theme selector */
    cbnz    r0, 1f
    movw    r0, #0x10a2            /* dark default */
    b       2f
1:  ldr     r1, =PALCELL
    ldrh    r0, [r1]               /* light: palette cell 0 */
2:  ldr     r1, =BGCELL
    ldrh    r2, [r1]
    cmp     r2, r0
    beq     3f
    strh    r0, [r1]
    ldr     r1, =EVWORD
    ldr     r2, [r1]
    orr     r2, r2, #EVMASK
    str     r2, [r1]               /* repaint request */
3:  bl      ART_PLACEHOLDER
    pop     {r0, r1, r2, r3, r4, pc}
    .size theater_default, . - theater_default

    .ltorg
