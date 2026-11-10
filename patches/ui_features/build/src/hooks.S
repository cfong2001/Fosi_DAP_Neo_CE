/*
 * Hook stubs for the UI extension blob.
 * Linked at the extension base 0x03079C14 (see ext.ld).
 */
    .syntax unified
    .thumb

/* ------------------------------------------------------------------ */
/* Dispatcher hook, entered by B.W from module 0 code 0x03061E5E,     */
/* replacing the stock `mov r0, r4` + `pop.w {r4-r11, ip, pc}` tail.  */
/* Register/stack state on entry is exactly the state at the stock    */
/* return: r4 = processed event word (or 0), the dispatcher's saved   */
/* register frame on the stack. The stub performs the identical       */
/* epilogue on every path; only the long-press Power word             */
/* (type 2, mask 0x1 = 0x20000001) diverts into bt_toggle and is      */
/* swallowed (return 0).                                              */
/* ------------------------------------------------------------------ */
    .section .text.hook, "ax"
    .global ui_dispatcher_hook
    .type ui_dispatcher_hook, %function
ui_dispatcher_hook:
    movw    r12, #0x0001
    movt    r12, #0x2000
    cmp     r4, r12
    bne     .Lhook_pass
    bl      bt_toggle
    movs    r0, #0
    pop.w   {r4, r5, r6, r7, r8, r9, r10, r11, r12, pc}
.Lhook_pass:
    mov     r0, r4
    pop.w   {r4, r5, r6, r7, r8, r9, r10, r11, r12, pc}
    .size ui_dispatcher_hook, . - ui_dispatcher_hook
