SECTIONS
{
    . = 0x307ee88;
    .text : { *(.text.entry) *(.text) *(.text.*) }
    .rodata : { *(.rodata) *(.rodata.*) }
    .data : { *(.data) *(.data.*) }
    /DISCARD/ : { *(.comment) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }
    ASSERT(ADDR(.text) == 0x307ee88, "bridge entry must sit at the blob base")
}
