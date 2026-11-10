/*
 * Resolver hooks for playlist (source 6) playback.
 * Design: work/m3u_bridge/resolver_design.md (job 3), with one register
 * correction proven from the module 33 call site at 0x0308A6BA: the
 * companion fetch 0x0305B2C2 takes the index in r0 and the directory
 * cluster in r1 (r2 = volume table cell 0x03005714, r3 = mode). The
 * design text says "r0 equals the cluster"; the call site loads r0
 * from [ctx+2] (the index) and r1 from [ctx+0x34] (the cluster), and
 * the stock fetch itself keeps r1 in r5 and compares it against the
 * current-directory cell at 0x0307AB64. The companion discriminator
 * below therefore tests r1.
 *
 * Placement: linked in the tail of the module 0 package gap,
 * immediately after the staging area. Staging header at STAGE:
 *   +0 flag (u8), +1 entry count (u8), +2 position p (u16, 0xFFFF =
 *   none), +4 last served residual (u16), +6 run count (u8), +7..15
 *   reserved zero. Runs at STAGE+16, 50 bytes each (u32 cluster,
 *   u16 countA, u16 countB, 42-byte context). Entries at STAGE+616,
 *   4 bytes each (u16 within-directory index, u8 run id, u8 flags).
 * Layout caps: 12 runs, 144 entries, staging = 16 + 600 + 576 =
 * 1,192 bytes.
 *
 * Both hooks are entered by B.W from the stock entry point, whose
 * first instruction (push.w {r4-r8, sb, sl, lr}, bytes 2D E9 F0 47)
 * they displace. Register contract on entry is the stock function's:
 * the fallback path executes the displaced push with every register
 * and the stack exactly as at entry, then continues at entry+4.
 * The substitution path uses only caller-saved registers (r0-r3, ip)
 * plus balanced stack saves of lr, and returns to the original
 * caller without ever running the stock prologue. APSR flags are
 * not live at either stock entry (the displaced push does not read
 * them and the next stock instruction is a MOV), so the tests may
 * clobber them.
 *
 * Call discipline: serve_common is a normal function (push {lr} at
 * entry, pop {pc} at exit) because it calls run_ptr_from_id. The
 * entry stubs save the caller's lr before their bl and restore it
 * into pc afterwards. The companion stub saves lr at entry because
 * its discriminator itself calls run_ptr_from_id.
 */
    .syntax unified
    .thumb

    .equ STAGE_LO, 0xBFB4          /* STAGE = 0x0307BFB4 */
    .equ STAGE_HI, 0x0307
    .equ CTXDESC_LO, 0x39B4        /* play context descriptor 0x030239B4 */
    .equ CTXDESC_HI, 0x0302
    .equ RESUME_P, 0x03059DB0      /* resolver entry + 4 */
    .equ RESUME_C, 0x0305B2C6      /* fetch entry + 4 */
    .equ RUNS_OFF, 16
    .equ ENTRIES_OFF, 616          /* 16 + 12*50 */

    .text

/* ------------------------------------------------------------------ */
/* Primary hook: resolver 0x03059DAC entry.                            */
/* r0 = flat index, r1 = out descriptor, r2 = table cell, r3 = mode.   */
/* Discriminator: flag set, r1 == 0x030239B4, r3 == 1.                 */
/* ------------------------------------------------------------------ */
    .global resolver_hook_primary
    .type resolver_hook_primary, %function
resolver_hook_primary:
    push    {ip, lr}               /* the tests clobber ip; save it and lr */
    movw    ip, #STAGE_LO
    movt    ip, #STAGE_HI
    ldrb    ip, [ip, #0]           /* playlist flag */
    cmp     ip, #0
    beq     .Lp_fail
    movw    ip, #CTXDESC_LO
    movt    ip, #CTXDESC_HI
    cmp     r1, ip
    bne     .Lp_fail
    cmp     r3, #1
    bne     .Lp_fail
    bl      serve_common           /* r0 = index, r1 = out descriptor */
    pop     {ip, pc}               /* caller lr into pc, ip restored */
.Lp_fail:
    pop     {ip, lr}
.Lp_fallback:
    push.w  {r4, r5, r6, r7, r8, sb, sl, lr}
    b.w     RESUME_P
    .size resolver_hook_primary, . - resolver_hook_primary

/* ------------------------------------------------------------------ */
/* Companion hook: single-directory fetch 0x0305B2C2 entry.            */
/* r0 = index, r1 = directory cluster, r2 = table cell, r3 = mode.     */
/* Discriminator: flag set, r3 == 1, r1 == cluster of the run          */
/* containing the last served entry. On a match the substitution       */
/* writes the play context descriptor at its fixed address             */
/* (ctx+0x34 = cluster, ctx+0x3C = countA+countB, ctx+0x50 = the       */
/* 42-byte context), which is serve_common with r1 = 0x030239B4.       */
/* r2 is borrowed as scratch, lr is saved, and r0 is saved because    */
/* run_ptr_from_id clobbers it during the cluster check while          */
/* serve_common still needs the caller's index. All under balanced     */
/* stack operations, so the fallback path sees the entry state         */
/* exactly.                                                            */
/* ------------------------------------------------------------------ */
    .global resolver_hook_companion
    .type resolver_hook_companion, %function
resolver_hook_companion:
    push    {r0, r2, ip, lr}      /* index, scratch, ip, return address */
    movw    ip, #STAGE_LO
    movt    ip, #STAGE_HI
    ldrb    ip, [ip, #0]           /* playlist flag */
    cmp     ip, #0
    beq     .Lc_fail
    cmp     r3, #1
    bne     .Lc_fail
    movw    ip, #STAGE_LO
    movt    ip, #STAGE_HI
    ldrh    r2, [ip, #2]           /* position p */
    adds    r2, r2, #1
    lsrs    r2, r2, #16
    cmp     r2, #0
    bne     .Lc_fail               /* p == 0xFFFF: nothing served yet */
    ldrh    r2, [ip, #2]           /* p again */
    ldrb    ip, [ip, #1]           /* entry count */
    cmp     ip, #0
    beq     .Lc_fail               /* empty staging cannot serve */
    cmp     r2, ip
    blo     .Lc_have_idx           /* p < count: entry p */
    subs    r2, ip, #1             /* past-end state: last entry */
.Lc_have_idx:
    movw    ip, #STAGE_LO
    movt    ip, #STAGE_HI
    add     ip, ip, #ENTRIES_OFF
    lsls    r2, r2, #2
    add     ip, ip, r2             /* entry pointer */
    ldrb    r2, [ip, #2]           /* run id */
    movw    ip, #STAGE_LO
    movt    ip, #STAGE_HI
    bl      run_ptr_from_id        /* r2 = run pointer (clobbers r0) */
    ldr     r2, [r2, #0]           /* run cluster */
    cmp     r1, r2
    bne     .Lc_fail
    pop     {r0, r2, ip}           /* sp now at the saved lr */
    movw    r1, #CTXDESC_LO
    movt    r1, #CTXDESC_HI
    bl      serve_common           /* r0 = index, r1 = descriptor */
    pop     {pc}                   /* the saved caller lr */
.Lc_fail:
    pop     {r0, r2, ip, lr}
.Lc_fallback:
    push.w  {r4, r5, r6, r7, r8, sb, sl, lr}
    b.w     RESUME_C
    .size resolver_hook_companion, . - resolver_hook_companion

/* ------------------------------------------------------------------ */
/* run_ptr_from_id: ip = STAGE, r2 = run id.                           */
/* Returns r2 = STAGE + 16 + runid*50. Clobbers r0. Leaf.              */
/* ------------------------------------------------------------------ */
    .type run_ptr_from_id, %function
run_ptr_from_id:
    mov     r0, r2                 /* run id */
    lsls    r2, r2, #5             /* runid * 32 */
    add     r2, r2, r0, lsl #4     /* + runid * 16 */
    add     r2, r2, r0, lsl #1     /* + runid * 2  = runid * 50 */
    add     r2, r2, ip
    add     r2, r2, #RUNS_OFF
    bx      lr
    .size run_ptr_from_id, . - run_ptr_from_id

/* ------------------------------------------------------------------ */
/* serve_common: r0 = incoming index i, r1 = out descriptor pointer.   */
/* Maps i against the header state and serves one entry (or the        */
/* past-the-end sentinel), in exactly the stock out format:            */
/*   out+0x00 = run cluster, out+0x08 = run countA + countB,           */
/*   out+0x1C..+0x45 = the run's 42-byte context.                      */
/* Returns the within-directory index (or the sentinel residual)       */
/* in r0, and stores it in the header residual cell, from which        */
/* the return value is loaded. Updates header position.                */
/* Uses r0-r3, ip. Assumes the staging is valid when the flag is       */
/* set (count >= 1), per the design: the bridge arms the flag only     */
/* after a complete import.                                            */
/* ------------------------------------------------------------------ */
    .type serve_common, %function
serve_common:
    push    {lr}
    movw    ip, #STAGE_LO
    movt    ip, #STAGE_HI          /* ip = STAGE for the mapping */
    uxth    r0, r0                 /* i is a u16-domain value */
    ldrh    r2, [ip, #2]           /* position p */
    adds    r3, r2, #1
    lsrs    r3, r3, #16
    cbnz    r3, .Ls_fresh          /* p == 0xFFFF: fresh selection */
    ldrh    r3, [ip, #4]           /* last residual j */
    adds    r3, r3, #1
    uxth    r3, r3                 /* j + 1 (u16) */
    cmp     r0, r3
    beq     .Ls_plus1
    ldrh    r3, [ip, #4]
    subs    r3, r3, #1
    uxth    r3, r3                 /* j - 1 (u16) */
    cmp     r0, r3
    beq     .Ls_minus1
    ldrh    r3, [ip, #4]
    cmp     r0, r3
    beq     .Ls_equal
.Ls_fresh:                         /* t = clamp(i, 0, count-1); t in r0 */
    ldrb    r3, [ip, #1]           /* count */
    cmp     r0, r3
    blo     .Ls_serve_t
    subs    r0, r3, #1
    b       .Ls_serve_t
.Ls_plus1:                         /* t = p + 1; may reach count */
    adds    r0, r2, #1
    ldrb    r3, [ip, #1]           /* count */
    cmp     r0, r3
    bhs     .Ls_sentinel
    b       .Ls_serve_t
.Ls_minus1:                        /* t = p - 1, clamped at 0 */
    cmp     r2, #0
    beq     .Ls_t_zero
    subs    r0, r2, #1
    b       .Ls_serve_t
.Ls_t_zero:
    movs    r0, #0
    b       .Ls_serve_t
.Ls_equal:                         /* t = p; p == count is the sentinel state */
    mov     r0, r2
    ldrb    r3, [ip, #1]
    cmp     r0, r3
    bhs     .Ls_sentinel
    /* fall through */
.Ls_serve_t:                       /* r0 = t in [0, count), r1 = out, ip = STAGE */
    strh    r0, [ip, #2]           /* header position = t */
    add     r2, ip, #ENTRIES_OFF
    lsls    r3, r0, #2
    add     r2, r2, r3             /* entry pointer */
    ldrh    r3, [r2, #0]           /* within-directory index */
    strh    r3, [ip, #4]           /* header residual = within */
    ldrb    r2, [r2, #2]           /* run id */
    bl      run_ptr_from_id        /* r2 = run pointer (clobbers r0) */
    b       .Ls_write_out
.Ls_sentinel:                      /* serve past-the-end on the last run */
    ldrb    r3, [ip, #1]           /* count */
    strh    r3, [ip, #2]           /* header position = count */
    subs    r3, r3, #1             /* last entry index */
    add     r2, ip, #ENTRIES_OFF
    lsls    r3, r3, #2
    add     r2, r2, r3             /* last entry pointer */
    ldrb    r2, [r2, #2]           /* its run id */
    bl      run_ptr_from_id        /* r2 = run pointer (clobbers r0) */
    ldrh    r3, [r2, #4]           /* that run's countA */
    /* ip still holds STAGE: run_ptr_from_id preserves it */
    strh    r3, [ip, #4]           /* header residual = countA (sentinel) */
    /* fall through */
.Ls_write_out:                     /* r1 = out, r2 = run pointer */
    ldr     r3, [r2, #0]
    str     r3, [r1, #0]           /* out+0x00 = cluster */
    ldrh    r3, [r2, #4]
    ldrh    r0, [r2, #6]
    add     r3, r3, r0
    str     r3, [r1, #8]           /* out+0x08 = countA + countB */
    add     r2, r2, #8             /* run context source */
    add     r0, r1, #0x1C          /* out context destination */
    movs    r3, #42
.Ls_copy:
    ldrb    r1, [r2], #1
    strb    r1, [r0], #1
    subs    r3, r3, #1
    bne     .Ls_copy
    /* ip still holds STAGE: the copy loop and write-out preserve it */
    ldrh    r0, [ip, #4]           /* return the header residual */
    pop     {pc}
    .size serve_common, . - serve_common
