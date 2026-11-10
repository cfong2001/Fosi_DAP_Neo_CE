/* Extension blob layout, linked at the module-0 extension base.
 * .text.hook must start exactly at the base: patch 0032 branches to it.
 * The lock-screen entry is pinned at +0x400 so patch 0033 can name a
 * fixed target before final link composition. */
SECTIONS
{
    . = 0x03079C14;
    .text.hook : { *(.text.hook) }
    .text : { *(.text) *(.text.*) }
    .rodata : { *(.rodata) *(.rodata.*) }
    .data : { *(.data) *(.data.*) }
    . = 0x03079C14 + 0x400;
    .text.lock : { *(.text.lock) }
    /DISCARD/ : { *(.comment) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }
    ASSERT(SIZEOF(.text.hook) + SIZEOF(.text) + SIZEOF(.rodata) + SIZEOF(.data) <= 0x400,
           "BT region overruns the lock-screen entry at +0x400")
}
