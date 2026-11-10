/*
 * Selector cave stubs for module 32's settings apply dispatch.
 *
 * The dispatch (disassembly in power_build.md) tests the item id
 * (descriptor halfword at [record + 8]) twice, once after the value
 * editor's decrement path and once after its increment path:
 *
 *   dispatch A, exec 0x0307DEE4: cmp 173 -> EQ path 0x0307DF6C
 *                                cmp 196 -> brightness 0x0307DF84
 *                                else    -> generic 0x0307DF8C
 *   dispatch B, exec 0x0307DFE0: cmp 173 -> EQ path 0x0307DFF8
 *                                cmp 196 -> brightness 0x0307E010
 *                                else    -> exit 0x0307E198
 *
 * Each patch replaces the second compare, its branch, and the
 * fall-through branch (6 bytes) with a B.W to the matching stub here
 * plus a NOP. The stub re-executes the displaced compare and branch
 * first, then tests the profile item id, then takes the same exit
 * the site's own special cases take: dispatch A's special cases fall
 * into the generic settings-changed post at 0x0307DF8C, dispatch B's
 * exit directly at 0x0307E198. Register state at entry, from the
 * dispatch disassembly: r0 = item id, r4 = item record (value byte
 * at +5, already updated by the stock editor), r6 = SAVEINFO base.
 * Only r0 and the caller-saved set are touched; the stubs' one call
 * is to profile_select, an ordinary AAPCS function, and the enclosing
 * function's prologue has already saved lr (its own code calls
 * through bl on these very paths, e.g. exec 0x0307DEDA).
 *
 * PROFILE_ITEM_ID is the settings item id the profile selector item
 * carries. The item record itself is UI workstream work (design
 * job 3: a 12-byte record with three options); the id must be
 * confirmed free against the firmware's string table when that
 * record is authored. 0xC5 (197) is the working value: it is not
 * 173 or 196, the only ids this dispatch special-cases, and no other
 * settings item id is compared anywhere in module 32. Reassignment
 * is a one-constant change here.
 */

.syntax unified
.thumb

.equ PROFILE_ITEM_ID, 0xC5
/* The stock continuations are Thumb entry points, not ARM code. */
.type brightness_a, %function
.type generic_a, %function
.type brightness_b, %function
.type exit_b, %function

.section .text.hooks, "ax"

.global hook_dispatch_a
.thumb_func
hook_dispatch_a:
    cmp     r0, #196
    bne     .La_profile
    b.w     brightness_a        @ displaced brightness branch
.La_profile:
    cmp     r0, #PROFILE_ITEM_ID
    bne     .La_done
    ldrb    r0, [r4, #5]        @ chosen option = record value byte
    bl      profile_select
.La_done:
    b.w     generic_a           @ generic exit, as items 173/196 take

.global hook_dispatch_b
.thumb_func
hook_dispatch_b:
    cmp     r0, #196
    bne     .Lb_profile
    b.w     brightness_b        @ displaced brightness branch
.Lb_profile:
    cmp     r0, #PROFILE_ITEM_ID
    bne     .Lb_done
    ldrb    r0, [r4, #5]
    bl      profile_select
.Lb_done:
    b.w     exit_b              @ function exit, as items 173/196 take
