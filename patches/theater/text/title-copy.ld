SECTIONS {
 .text.loop 0x0307f9d0 : { *(.text.loop) }
 .text.finish 0x0307fa3a : { *(.text.finish) }
 /DISCARD/ : { *(.ARM.attributes) }
 ASSERT(SIZEOF(.text.loop) == 30, "title loop must occupy 30 bytes")
 ASSERT(SIZEOF(.text.finish) == 36, "title suffix must occupy 36 bytes")
}
