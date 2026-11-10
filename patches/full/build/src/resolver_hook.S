/*
 * Playlist hooks for source 6 playback, full build.
 *
 * Stock source 6 plays the folder tree as one flat list. The play context
 * at 0x03023980 holds the list length at ctx+0 and a 1-based position at
 * ctx+2. Stock maps a position to a folder and a 1-based ordinal inside it
 * with the resolver at 0x03059DAC, then resets the folder iterator and
 * advances (ordinal - 1) times (0x0305D048, and the backward and shuffle
 * steps of 0x0305D124).
 *
 * While a playlist is armed these hooks make the flat list the playlist:
 *
 *   count_hook      0x03059D58, mode 1: returns the staged entry count,
 *                   so ctx+0 is the playlist length and stock wraps and
 *                   shuffles inside the playlist.
 *   primary         0x03059DAC, mode 1, out == ctx+0x34: position i maps
 *                   to entry i - 1. Writes that entry's folder into the
 *                   out descriptor and returns its 1-based ordinal.
 *   companion       0x0305B2C2, mode 1, called from the playlist start
 *                   (module 31, return 0x0307E065) or the play-mode
 *                   switch (module 33, return 0x0308A6CB): returns the
 *                   index unchanged, so a position stays a playlist
 *                   position. The start call passes 1, so playback
 *                   begins at the first entry.
 *   advance_hook    called by BL from 0x0305D598 in the source 6 step.
 *                   Replaces "ldrh r0, [r4, #0xc]; cmp r0, #1" and sets
 *                   Z when the playlist is armed, so a forward step
 *                   takes stock's resolver, reset and advance path
 *                   instead of the folder iterator's next file.
 *
 * Staging at STAGE (written by the bridge, see m3u_bridge.h):
 *   +0 flag (u8), +1 entry count (u8), +2 last position served (u16),
 *   +4 last ordinal served (u16), +6 run count (u8). Runs at +16, 50
 *   bytes each (u32 cluster, u16 countA, u16 countB, 42-byte context).
 *   Entries at +316, 4 bytes each (u16 0-based ordinal among the folder's
 *   accepted files, u8 run id, u8 flags). The bridge arms the flag only
 *   after a complete import, so the count is at least 1 when it is set.
 *
 * The three entry hooks are reached by B.W from the stock entry, whose
 * displaced first instruction is a push.w. A declined call restores r2,
 * the only register the test uses, executes that push with every register
 * and the stack as at entry, and continues at entry + 4. A served call
 * returns to the caller directly and may change r1-r3 and ip, which are
 * caller-saved.
 */
    .syntax unified
    .thumb

    .equ STAGE, 0x0307BFB4
    .equ CTXDESC, 0x030239B4       /* play context + 0x34 */
    .equ RESUME_P, 0x03059DB0      /* resolver entry + 4 */
    .equ RESUME_C, 0x0305B2C6      /* fetch entry + 4 */
    .equ RESUME_N, 0x03059D5C      /* count entry + 4 */
    .equ RET_START, 0x0307E065     /* module 31 playlist start */
    .equ RET_MODE, 0x0308A6CB      /* module 33 play-mode switch */
    .equ RUNS_OFF, 16
    .equ ENTRIES_OFF, 316          /* 16 + 6 * 50, full build caps */

    .text

/* Primary: resolver 0x03059DAC. r0 = position, r1 = out, r3 = mode. */
    .global resolver_hook_primary
    .type resolver_hook_primary, %function
resolver_hook_primary:
    push    {r2}
    ldr     r2, =STAGE
    ldrb    r2, [r2]
    cbz     r2, 1f
    cmp     r3, #1
    bne     1f
    ldr     r2, =CTXDESC
    cmp     r1, r2
    bne     1f
    pop     {r2}
    b       serve
1:  pop     {r2}
    push.w  {r4, r5, r6, r7, r8, sb, sl, lr}
    b.w     RESUME_P
    .size resolver_hook_primary, . - resolver_hook_primary

/* Companion: fetch 0x0305B2C2. r0 = index, r1 = folder, r3 = mode. */
    .global resolver_hook_companion
    .type resolver_hook_companion, %function
resolver_hook_companion:
    push    {r2}
    ldr     r2, =STAGE
    ldrb    r2, [r2]
    cbz     r2, 1f
    cmp     r3, #1
    bne     1f
    ldr     r2, =RET_START
    cmp     lr, r2
    beq     2f
    ldr     r2, =RET_MODE
    cmp     lr, r2
    bne     1f
2:  pop     {r2}
    bx      lr                     /* r0 unchanged: a playlist position */
1:  pop     {r2}
    push.w  {r4, r5, r6, r7, r8, sb, sl, lr}
    b.w     RESUME_C
    .size resolver_hook_companion, . - resolver_hook_companion

/* Count: 0x03059D58. r0 = table, r1 = mode. */
    .global resolver_hook_count
    .type resolver_hook_count, %function
resolver_hook_count:
    push    {r2}
    ldr     r2, =STAGE
    ldrb    r2, [r2]
    cbz     r2, 1f
    cmp     r1, #1
    bne     1f
    ldr     r2, =STAGE
    ldrb    r0, [r2, #1]           /* staged entry count */
    pop     {r2}
    bx      lr
1:  pop     {r2}
    push.w  {r4, r5, r6, r7, r8, lr}
    b.w     RESUME_N
    .size resolver_hook_count, . - resolver_hook_count

/* Forward step: BL from 0x0305D598. r4 = play context; r1 is dead. */
    .global resolver_hook_advance
    .type resolver_hook_advance, %function
resolver_hook_advance:
    ldrh    r0, [r4, #0xc]         /* displaced: shuffle flag */
    ldr     r1, =STAGE
    ldrb    r1, [r1]
    cbz     r1, 1f
    movs    r0, #1                 /* armed: take the resolver path */
1:  cmp     r0, #1                 /* displaced compare */
    bx      lr
    .size resolver_hook_advance, . - resolver_hook_advance

/*
 * serve: r0 = 1-based position, r1 = out descriptor. Clamps the position
 * to [1, count], records it, writes the entry's folder in the stock out
 * format (out+0x00 cluster, out+0x08 countA + countB, out+0x1C..+0x45
 * the 42-byte context) and returns the entry's 1-based ordinal.
 */
    .type serve, %function
serve:
    ldr     ip, =STAGE
    uxth    r0, r0
    cbz     r0, 1f
    subs    r0, r0, #1             /* entry index t = position - 1 */
1:  ldrb    r3, [ip, #1]
    cmp     r0, r3
    blo     2f
    subs    r0, r3, #1             /* past the end: last entry */
2:  strh    r0, [ip, #2]
    add     r2, ip, #ENTRIES_OFF
    add     r2, r2, r0, lsl #2     /* entry pointer */
    ldrh    r0, [r2]
    adds    r0, r0, #1             /* 1-based ordinal for stock */
    strh    r0, [ip, #4]
    ldrb    r2, [r2, #2]           /* run id */
    movs    r3, #50
    mla     r2, r2, r3, ip
    adds    r2, r2, #RUNS_OFF      /* run pointer */
    ldr     r3, [r2]
    str     r3, [r1]               /* cluster */
    ldrh    r3, [r2, #4]
    ldrh    ip, [r2, #6]
    add     r3, r3, ip
    str     r3, [r1, #8]           /* countA + countB */
    adds    r2, r2, #8
    adds    r1, r1, #0x1C
    movs    r3, #42
3:  ldrb    ip, [r2], #1
    strb    ip, [r1], #1
    subs    r3, r3, #1
    bne     3b
    bx      lr
    .size serve, . - serve

    .ltorg
