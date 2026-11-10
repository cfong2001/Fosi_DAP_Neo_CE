/* Lock-screen blob layout, linked at the module 31 segment extension
 * base. Module 31's stock code segment ends at 0x0307EE48; the
 * extension room runs to 0x03080B54 (resident-home census), so the
 * entry symbol must sit exactly at 0x0307EE48 for patch 0033's branch.
 * The blob carries no .bss: the extension payload is a plain byte
 * copy, so writable state lives in .data inside the image. */
SECTIONS
{
    . = 0x0307EE48;
    .text : {
        *(.text.entry)
        *(.text)
        *(.text.*)
    }
    .rodata : { *(.rodata) *(.rodata.*) }
    .data : { *(.data) *(.data.*) }
    .bss : { *(.bss) *(.bss.*) *(COMMON) }
    /DISCARD/ : { *(.comment) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }
    ASSERT(ADDR(.text) == 0x0307EE48, "lock-screen entry must sit at the extension base")
    ASSERT(SIZEOF(.bss) == 0, "lock-screen blob cannot contain uninitialised storage")
    ASSERT(. <= 0x03080B54, "lock-screen blob exceeds module 31 extension room")
}
