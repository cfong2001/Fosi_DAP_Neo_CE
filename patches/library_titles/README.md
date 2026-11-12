# Library lists retain title tags

V137's scanner parses the title, artist, album and genre into a temporary
record, then unconditionally copies the filename over the title. At
module 38 `0x0307EF52..0x0307EF5C` it calls the resident memcpy with a
256-byte title destination at `r4+0x100` and the filename at `r4`.
The database writer then stores that title at record offset `0x400`.
The library's display configuration already selects that field.

Patch 0181 redirects only the memcpy call to a 16-byte helper in the
unused resident pocket `0x0305318C..0x030531A0`. If the first title unit
is nonzero and the file opened successfully it returns; otherwise it tail-calls the original memcpy with
its original arguments. The scanner retains the open result at `[sp]` through this call. A failed
open can leave stale temporary tags; that case always uses the filename.
No file opens, parsing, allocation or additional
storage reads are added while browsing. Filename and playback-path fields
stay unchanged. FAT and FS-type-3 paths meet before this copy; CUE entries
keep their existing separate title handling.

**Refresh the music library after installing Standard CE.** Existing
database entries still contain the old filename until they are rescanned.

The SDK reference confirms the distinction between the long filename and
ID3-title fields and documents a conditional filename fallback. Its code
is not included here. The Neo offsets and the unconditional-copy defect
are established from the pinned V137 instructions.

```
python patches/library_titles/build_titles.py
python patches/library_titles/test_titles.py
```

The regression executes the original scanner instructions around the call
and the real resident memcpy under Unicorn. It checks tagged and untagged
tracks, a 127-unit title, Unicode and empty names, neighboring fields,
registers and stack. It does not emulate a full card scan or validate a
physical device. The patch is composed into Standard CE only.
