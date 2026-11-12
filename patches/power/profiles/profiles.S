/*
 * Power profiles: a "Power Profile" item in System Settings with three
 * options that set brightness, auto screen off and auto power off
 * together. Every value is a stock setting written through the stock
 * code that the settings window itself uses, so the profile needs no
 * storage of its own and nothing beyond what stock already restores at
 * boot. No clock, timer or radio state is touched.
 *
 * Three parts, all in module 0 pockets that the reachability census
 * found dead (patches/space/), so they are resident in every window:
 *
 *  1. Menu records 266..269. The menu tree is data: every string record
 *     (258 bytes, 266 per language) starts with the SDK's
 *     MENU_TEXT_INFO_STRUCT (self, parent, index, first child, siblings,
 *     function index, child count, child ids; Common/Display/LcdChar.h).
 *     GetResourceStr (0x030630C2) and GetMenuTextInfoWithIDNum
 *     (0x03063206) find a record at base + language * 266 * 258 +
 *     id * 258. The new ids live past the end of the image resources
 *     instead, so these two hooks send ids 266 and up to that table and
 *     leave every stock id on the stock path.
 *
 *  2. The value hook in module 32's settings window (0x0307DBCE). When
 *     a submenu opens, the window loads the selected option from
 *     SAVEINFO with a switch on the item id. For item 266 the selected
 *     option is the profile whose three values match the current
 *     settings, or none.
 *
 *  3. The commit hook (0x0307FA80). Choosing an option calls module 32's
 *     handler with the option's id; ids past 265 take its default exit.
 *     The hook catches 267..269 there and applies the profile.
 */

.syntax unified
.thumb

.equ SAVEINFO,      0x030232A0  @ live settings struct
.equ MENU_BASE_PTR, 0x03023288  @ holds the language section's address
.equ FIRST_NEW_ID,  266
.equ PROFILE_ITEM,  266
.equ FIRST_OPTION,  267
.equ HEADER,        58          @ sizeof(MENU_TEXT_INFO_STRUCT)
.equ LABEL,         48          @ bytes per label slot (23 UTF-16 + NUL)
.equ LABELS_PER_LANGUAGE, 4

/* TABLE_DELTA: distance from the language section's start to the
 * table, which sits right after the image resources. Every module
 * growth shifts both by the same amount (they are all past the module
 * area), so the distance is a constant of the stock layout:
 * 0x00C92E10 - 0x0074D676. build_profiles.py checks it. */
.equ TABLE_DELTA,   0x0054579A

/* ------------------------------------------------------------------ */
.section .text.lookup, "ax"

/* Entered from GetResourceStr's first instruction: r0 = string id,
 * r1 = buffer, r2 = length in halfwords. */
.global str_hook
.thumb_func
str_hook:
    cmp.w   r0, #FIRST_NEW_ID
    bhs     1f
    push    {r4, r5, r6, r7}        @ displaced
    ldr     r5, =SAVEINFO           @ displaced: ldr r5, [pc, #468]
    b.w     getresourcestr_body
1:  ldr     r3, =SAVEINFO
    ldrb    r3, [r3, #16]           @ current language
    sub.w   r0, r0, #FIRST_NEW_ID
    add.w   r0, r0, r3, lsl #2      @ language * 4 + label
    movs    r3, #LABEL
    muls    r0, r3
    ldr     r3, =MENU_BASE_PTR
    ldr     r3, [r3]
    add     r0, r3
    ldr     r3, =TABLE_DELTA + LABELS_PER_LANGUAGE * HEADER
    add     r0, r3
    movw    r3, #0xFFFF             @ the stock tail: bytes = len * 2
    and.w   r2, r3, r2, lsl #1
    b.w     resource_read

/* Entered from GetMenuTextInfoWithIDNum's first instruction: r0 = id,
 * r1 = destination for the 58-byte header. Headers do not depend on
 * the language, so the table holds one copy. */
.global menu_hook
.thumb_func
menu_hook:
    cmp.w   r0, #FIRST_NEW_ID
    bhs     1f
    push    {r4, r5}                @ displaced
    ldr     r4, =SAVEINFO           @ displaced: ldr r4, [pc, #144]
    b.w     getmenutextinfo_body
1:  sub.w   r0, r0, #FIRST_NEW_ID
    movs    r2, #HEADER
    muls    r0, r2
    ldr     r3, =MENU_BASE_PTR
    ldr     r3, [r3]
    add     r0, r3
    ldr     r3, =TABLE_DELTA
    add     r0, r3
    b.w     resource_read
.ltorg

/* ------------------------------------------------------------------ */
.section .text.profiles, "ax"

/* Option index -> brightness (+0x14), auto screen off (+0x15) and auto
 * power off (+0x18), each the index of the stock option:
 *   brightness      20% 40% 60% 80% 100%                (0..4)
 *   screen off      10 s 20 s 30 s 1 min 5 min 10 min always (0..6)
 *   power off       off 5 10 15 20 min                  (0..4)
 */
.global profile_table
profile_table:
    .byte 4, 3, 0       @ High: 100 %, 1 minute, never
    .byte 2, 2, 2       @ Balanced: 60 %, 30 seconds, 10 minutes
    .byte 0, 0, 1       @ Battery Saver: 20 %, 10 seconds, 5 minutes
    .byte 0             @ pad

/* Entered from the settings window's value switch in place of
 * `cmp r5, #188; it eq` (r5 = item id, r7 = SAVEINFO, r4 = the menu
 * level record). r0..r3 are free here: the switch's cases set r0 and
 * nothing reads r1..r3 before writing them. */
.global value_hook
.thumb_func
value_hook:
    cmp     r5, #188
    bne     1f
    ldrb    r0, [r7, #21]           @ displaced case: Auto Screen Off
    b.w     value_store
1:  cmp.w   r5, #PROFILE_ITEM
    bne     3f
    adr     r1, profile_table
    movs    r0, #0
2:  ldrb    r2, [r1]
    ldrb    r3, [r7, #0x14]
    cmp     r2, r3
    bne     4f
    ldrb    r2, [r1, #1]
    ldrb    r3, [r7, #0x15]
    cmp     r2, r3
    bne     4f
    ldrb    r2, [r1, #2]
    ldrb    r3, [r7, #0x18]
    cmp     r2, r3
    beq.w   value_store             @ r0 = matching profile
4:  adds    r1, #3
    adds    r0, #1
    cmp     r0, #3
    bne     2b
    b.w     value_none              @ no match: no option marked
3:  cmp     r5, #188                @ restore the flags the next case tests
    b.w     value_next

/* ------------------------------------------------------------------ */
.section .text.commit, "ax"

/* Entered from the commit handler's range check in place of
 * `bcs.w exit` (r0 = option id - 152, r1 = argument, r4 = 0). The
 * handler saved lr, r4 and r5 in its prologue. */
.global commit_hook
.thumb_func
commit_hook:
    subs    r0, #(FIRST_OPTION - 152)
    cmp     r0, #3
    bhs     1f
    ldr     r1, =profile_table
    add     r0, r0, r0, lsl #1
    add     r1, r0
    push    {r1, r2}            @ keep sp 8-byte aligned
    ldrb    r0, [r1]
    ldr     r2, =SAVEINFO
    strb    r0, [r2, #0x14]
    bl      backlight_apply         @ as module 32's brightness case does
    ldr     r1, [sp]
    ldrb    r0, [r1, #1]
    bl      set_screen_off          @ module 32's own setter
    pop     {r1, r2}
    ldrb    r0, [r1, #2]
    bl      set_power_off           @ module 32's own setter (re-arms)
    movs    r0, #1
    bl      saveinfo_save
1:  b.w     commit_exit
.ltorg
