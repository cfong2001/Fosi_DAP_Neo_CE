/*
 * Patch-site stubs. Each section is linked at its patch site address
 * so the linker computes the B.W displacement to the cave stub in
 * the module 32 extension. Six bytes per site: the 4-byte B.W plus
 * a NOP, matching the 6 displaced stock bytes (cmp, beq, b).
 */

.syntax unified
.thumb

.section .site_a, "ax"
.global site_a
.thumb_func
site_a:
    b.w     hook_dispatch_a
    nop

.section .site_b, "ax"
.global site_b
.thumb_func
site_b:
    b.w     hook_dispatch_b
    nop
