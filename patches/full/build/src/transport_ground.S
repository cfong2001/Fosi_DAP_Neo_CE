/*
 * Design refresh v4 transport glyphs without ghosting.
 *
 * The v4 set repoints eight player transport draws from the opaque
 * DrawImageAt (0x0306354A) to the keyed helper (0x03063A08), so the glyph
 * surround (key colour 0xF800) shows the ground instead of a tile. The
 * opaque draw used to replace its whole rectangle; the keyed draw only
 * writes ink, so a segment-only repaint left the previous glyph's ink where
 * the new glyph does not cover it (34 to 58 pixels measured in
 * patches/design_refresh_v4/design_v4.md, gate c).
 *
 * transport_keyed_draw takes the helper's (id, x, y) arguments, fills the
 * glyph's rectangle with the ground colour from the background cell
 * 0x03004400 (the colour the painter's full repaint fills the screen with),
 * then tail-calls the keyed helper. Composites 155 and 156 are 240 by 32;
 * every other transport id is 32 by 32. The helper applies the light theme
 * remap itself, so the call sites pass dark ids in both themes.
 *
 * The result equals the stock opaque draw with the surround in the ground
 * colour, so any repaint leaves no ink from the previous state.
 */
    .syntax unified
    .thumb

    .equ HELPER, 0x03063A08        /* keyed draw (id, x, y) */
    .equ FILL, 0x030632FA          /* fill (x0, y0, x1, y1), colour on stack */
    .equ GROUND, 0x03004400        /* background cell */

    .text

    .global transport_keyed_draw
    .type transport_keyed_draw, %function
transport_keyed_draw:
    /* In B>=2 the first painter call uses 157 at x=0 for the base left
       arrow, while the computed focus call uses the same id at x=4. Keep
       the base draw bare by substituting its identical bare resource 162;
       resource 157 can then carry the orange focused-glyph treatment. */
    cmp     r0, #157
    bne     2f
    cmp     r1, #0
    bne     1f
    movs    r0, #162
    b       1f
2:
    /* The second page's focused left arrow shares the bare resource ID.
       Only the computed draw passes it here, so reuse selected arrow 157. */
    cmp     r0, #162
    it      eq
    moveq   r0, #157
1:
    push    {r0, r1, r2, lr}
    sub     sp, #8
    ldr     r3, =GROUND
    ldrh    r3, [r3]
    str     r3, [sp]               /* fill colour */
    subs    r3, r0, #155
    cmp     r3, #1
    ite     ls
    movls   r3, #239               /* composite: 240 wide */
    movhi   r3, #31                /* icon: 32 wide */
    add     r3, r3, r1
    mov     r0, r1                 /* x0 */
    mov     r1, r2                 /* y0 */
    mov     r2, r3                 /* x1 */
    adds    r3, r1, #31            /* y1 */
    bl      FILL
    add     sp, #8
    pop.w   {r0, r1, r2, lr}
    b.w     HELPER
    .size transport_keyed_draw, . - transport_keyed_draw

    .ltorg
