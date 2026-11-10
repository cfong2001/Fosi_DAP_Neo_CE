/* M3U parser core placed inside the module 0 code-region extension.
 * Extension base (exec) 0x03079C14; trampoline occupies +0x00..+0x7F;
 * this image is linked at +0x80 -> 0x03079C94.
 * The parser has no .data/.bss (verified in the objects), so the flat
 * binary is exactly .text followed by .rodata. */
SECTIONS
{
  . = 0x03079C94;
  .text : { *(.text) *(.text.*) }
  .rodata : { *(.rodata) *(.rodata.*) }
  /DISCARD/ : { *(.comment) *(.ARM.attributes) *(.note*) }
}
