# Opus album art and theater background

The content-routing repair is merged and Opus music playback is confirmed on
hardware. The latest playback test displayed neither the album cover nor a
derived theater background. The repaired image passes extraction and native drawing tests; device visual
acceptance remains pending.

## Established source behavior

`patches/opus_swap/opus_tags.c` maps only TITLE, ARTIST, ALBUM and GENRE.
`comment()` passes unknown keys to `value()` without a destination, which
streams past their contents. This includes METADATA_BLOCK_PICTURE. This is
a confirmed omission in that parser; it does not establish whether a separate
playback artwork loader also needs repair.

The theater lifecycle test supplies decoded rows and verifies the derived
RGB565 color. It therefore cannot establish that embedded Opus picture bytes
reach the native JPEG loader. Missing art and an unchanged background must be
measured at separate stages before changing color computation.

## Short measurements

Run `python tools/audit_opus_artwork.py /path/to/local/media` with Mutagen
installed. It opens files read-only and emits only aggregate picture counts,
including JPEG/PNG signatures, malformed blocks and missing pictures. It does
not validate JPEG decoding or the device path. No music or private tag data
is committed. Synthetic classifier tests run with:

```sh
python -m unittest discover -s tests -p test_opus_artwork_inventory.py
```

The initial local inventory found 204 readable Opus files: 201 carried picture
blocks with JPEG signatures, three had no picture, and none had malformed or
oversized picture blocks. Thus absent source artwork cannot explain the whole
corpus. These are signature checks, not a claim that all JPEGs decode on device.

The repair gates are:

| Stage | Measurement | Success |
|---|---|---|
| Extraction | Generated Opus picture payload vs original bytes | Exact match, including multipage comments |
| Bounds | Invalid base64, truncated picture lengths, oversized values | Bounded rejection, intact guards and stack |
| Native drawing | Extracted supported JPEG reaches native loader and row consumer | Nonzero decoded rows; no placeholder fallback |
| Theater | White, colored and no-art fixtures | Independent RGB565 reference match and no stale previous-track color |
| Regression | Existing scan, text metadata and playback gate | All current checks still pass |
| Hardware | Same track through browser and library | Audible playback, visible cover and derived background |

## Diagnosed repair and results

Module 18's format dispatch still sent OPU (the former WMA slot) to the
ASF picture reader. The new entry routes it to the native Ogg picture loader.
That loader expects the seven-byte `03 vorbis` comment header; the Opus shim
recognizes all eight bytes of `OpusTags` and adjusts the packet length without
changing the lacing table. Non-comment packets retain the native skip offset.

Large covers exposed a second defect: the loader used the page granule value
as a continuation signal. The tested Opus header pages use zero even when
all 255 laces are 255. The repair follows the last lace instead, on both the
initial and subsequent comment pages. Native base64 decoding, temporary-file
creation, JPEG decoding, row drawing and theater accumulation remain in use.
The text parser still skips picture values; artwork has its own playback path.

`patches/opus_swap/test_artwork_route.py` executes those native paths with
modeled filesystem and LCD leaves. The short gate checks 81,814 exact copied
bytes across two fixtures (including a multipage cover), five missing/malformed
returns, 54 actual decoded JPEG rows and three independent theater-color
matches. The old image reproduces missing Opus art; native Vorbis output
remains identical. Stack, output guards and callee-saved registers are checked.

The full local corpus check extracted all 201 picture blocks byte-for-byte
from 204 files; three files had no picture. All 201 source images are readable
baseline JPEGs. No filenames or media are included in these results.

Run the short gate with:

```sh
python patches/opus_swap/test_artwork_route.py --candidate release/DP3_V137_CE.img
```

The integrated repair gate also includes these checks. Hardware must still
confirm the cover and derived background while music plays before merging.
