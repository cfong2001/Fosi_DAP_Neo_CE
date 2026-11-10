/* Assembled at the two stock module-27 addresses by title-copy.ld.
 * r0 = title buffer, r3 = input, r7 = 0 (established by the painter).
 * The painter does not read its old [sp+0xc] loop counter after this path.
 * Both sites must be patched together; see the paired .patch files. */
.syntax unified
.cpu cortex-m3
.thumb
.section .text.loop,"ax",%progbits
.global title_copy
.thumb_func
title_copy:
 movs r1, #0
.Lcopy:
 ldrh.w r2, [r3, r1, lsl #1]
 cbz r2, .Lshort
 cmp r1, #127
 bhs .Llong
 strh.w r2, [r0, r1, lsl #1]
 adds r1, #1
 b.n .Lcopy
.Llong:
 strh.w r7, [r0, r1, lsl #1]
 b.n 0x0307f9ee
.Lshort:
 b.n 0x0307fa3a
 nop
.section .text.finish,"ax",%progbits
.global title_finish
.thumb_func
title_finish:
 strh.w r7, [r0, r1, lsl #1]
 cmp r1, #5
 blo .Ldone
 add.w r0, r0, r1, lsl #1
 subs r0, #10
 ldrh r1, [r0, #2]
 cmp r1, #46
 it eq
 strheq r7, [r0, #2]
 ldrh r1, [r0]
 cmp r1, #46
 it eq
 strheq r7, [r0]
.Ldone:
 b.n 0x0307f9ee
 nop
 nop
