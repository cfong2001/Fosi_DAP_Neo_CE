/*
 * Link layout for the battery-profile build.
 *
 * The blob (.text + .rodata) links at 0x030804AC, the first byte past
 * module 32's stock code segment (exec 0x0307D164, length 0x3348):
 * the start of its segment extension room, which the residency
 * argument in power_build.md bounds at 0x03080B54. The payload is a
 * plain byte copy (code and constants, no .data, no .bss), exactly
 * what the framework --grow step appends to the module 32 segment.
 *
 * The two .site sections link at the patch sites in module 32's own
 * code so their B.W displacements resolve against the blob address.
 * They are extracted separately and are not part of the payload.
 */

ENTRY(profiles_apply)
brightness_a = 0x0307DF85;
generic_a = 0x0307DF8D;
brightness_b = 0x0307E011;
exit_b = 0x0307E199;

SECTIONS
{
    .text 0x030804AC :
    {
        *(.text.entry)
        *(.text .text.*)
    }

    .rodata :
    {
        *(.rodata .rodata.*)
    }

    .site_a 0x0307DEEC :
    {
        *(.site_a)
    }

    .site_b 0x0307DFE8 :
    {
        *(.site_b)
    }

    /DISCARD/ :
    {
        *(.comment)
        *(.note .note.*)
        *(.ARM.exidx .ARM.exidx.*)
        *(.ARM.extab .ARM.extab.*)
    }
}
