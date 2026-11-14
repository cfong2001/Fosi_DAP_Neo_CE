# Opus album art and theater background

The content-routing repair is merged and Opus music playback is confirmed on
hardware. The latest playback test displayed neither the album cover nor a
derived theater background. This follow-up does not change the working image
until the missing artwork path is reproduced and repaired.

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

The initial PR supplies the inventory and scope. Firmware extraction and
native artwork handoff remain to be implemented and tested.
