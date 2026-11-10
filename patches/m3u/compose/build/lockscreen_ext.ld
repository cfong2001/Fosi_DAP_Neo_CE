SECTIONS
{
    . = 0x308087c;
    .text : {
        *(.text.entry)
        *(.text)
        *(.text.*)
    }
    .rodata : { *(.rodata) *(.rodata.*) }
    .data : { *(.data) *(.data.*) }
    /DISCARD/ : { *(.comment) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }
    ASSERT(ADDR(.text) == 0x308087c, "lock-screen entry must sit at its link base")
}
