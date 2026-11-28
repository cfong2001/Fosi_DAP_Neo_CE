# Main-font width table

`0x030627BE` returns a character's advance. For the 16 x 16 main font it
reads the 34-byte record at cell + 33 × code from the system disk and
derives the width from the record's last byte. Measuring a string calls
it once per character and drawing calls it again, so it accounted for
188 of 247 glyph reads in one emulated browser wheel step.

| Patch | Site | Change |
|---|---|---|
| 0295 | `0x0306D4BC` | Check and 384-entry width table, after patch 0290 in the same unreached routine |
| 0296 | `0x030627BE` | Enter the check; every other call resumes the stock prologue |

The table answers when all of these hold, and the stock routine runs
otherwise:

- the code is below 0x180;
- the font class (context +0x24) is not 1, the 12-pixel font;
- the font base cell `0x03023280` holds Font B's header offset minus 1,
  the value both glyph routines imply by reading rows from bytes 1 to 32
  and the tail from byte 33;
- the byte at `0x030232B0` is not 8 or 10, the two values the stock
  routine special-cases.

`build_glyph_width.py IMAGE` generates the table by running the routine
from IMAGE (an image without these two patches) in emulation.
`test_glyph_width.py IMAGE` checks the composed image: every table entry
equals the stock routine, 3,000 randomized calls outside the table's
conditions equal it too, and the table matches the advance model in
`patches/antialias/generate_font.py`.

If a future change edits Font B or the width rules, regenerate the table
from an image built without 0295 and 0296.
