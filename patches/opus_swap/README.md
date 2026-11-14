# Opus decoder transplant (module 72)

Standard CE includes this transplant, the five classifier renames,
the bounded OpusTags reader and the content-routing repair. The
framework's default/Minimal build retains WMA. The older standalone
variant below is a component build and does not include all Standard
metadata and routing repairs. Do not enable the decoder and renames
by halves; they remain a matched set.

## What it does

The stock firmware's module 72 is a WMA decoder. This transplant
replaces the WMA library inside module 72 with berettavexee's
Opus plug-in (fixed-point libopus 1.5.2 plus a minimal Ogg
demuxer), keeping the module's own runtime byte for byte. The
splice works because Neo module 72 and the Echo Mini's WMA
module 74 are the same SDK build of the decoder program:
identical geometry (code 0x162C0, data 0x67C0, 117,376 bytes
total), and every runtime address the plug-in depends on sits at
the same offset in both (CodecFunc table and slot, FILE_OPS
table, BSS base and clear length, info block, runtime
event-flag array). The plug-in's decoder entry is linked at the
same address as the WMA entry, so the stock CodecFunc[1] word
needs no change. The transplant is size-neutral: the image
keeps its stock length.

The five rename patches change the extension `WMA` to `OPU` in
every copy of the classifier string
`MP1MP2MP3WMAWAVAPEFLAAACM4AOGGMP43GPDFFDSF`: three in module 0
data, one in module 31 code, one in module 38 code. Slot 3 of
the classifier then matches `OPU`, which is the extension the
FAT layer's 8.3 alias carries for `.opus` files, so files keep
their `.opus` names and reach module 72 through the stock
selection path. This admission check is not the final codec decision:
stock content detector `0x03067F50` reads the file and overwrites the
extension before the second codec lookup in module 34. Its original
OggS case changed Opus to OGG, selecting Vorbis. Standard's patches
0263–0265 recognize a bounded BOS `OpusHead` packet and retain OPU;
Vorbis stays on OGG, and the original final seek-to-zero is preserved.
The per-codec stub family and parameter page remain codec-generic,
and Opus inherits the WMA clock rows. The donor's measured cost for this plug-in build
(about 33 million instructions per second of audio for typical
music, at most 56 million for the worst case) fits the clock v1
rows with headroom.

## Build the variant

From the repo root, with the stock image at DP3_V137.img and
the .ecpatch inputs in a directory of their own (see
DEPENDENCY.md):

```sh
python3 patches/framework/build.py \
    --input DP3_V137.img \
    --manifest patches/opus_swap/manifest.txt \
    --transplants patches/opus_swap/transplants.txt \
    --ecpatch-dir /path/to/echo-mini-opus/patch \
    --output DP3_V137_opus.img
```

`FOSI_ECPATCH_DIR` can replace `--ecpatch-dir`, and
`FOSI_STOCK_IMAGE` can replace `--input`. The build refuses if
a rename patch's stock bytes do not match, if the .ecpatch
input's hash differs from the pin in DEPENDENCY.md, or if a
transplant's claimed ranges overlap any byte patch.

## What changes when it is enabled

- `.opus` files play: the library scan, the browser and
  playback all route them to module 72.
- **WMA playback is removed.** `.wma` files stop matching every
  classifier copy, so they disappear from the library scan and
  the browser.
- Standard's streaming reader stores title, artist, album and genre
  in bounded UTF-16 fields. Large artwork comments are skipped;
  playback artwork uses the separately repaired native Ogg picture loader.
  See [artwork qualification](../../release/ALBUM_ART_FOLLOWUP.md).

## Gates before this can become the default

- Harness decode validation: the transplanted module booted
  under the Phase D harness rig, driven through the stock open
  exchange, decoding reference Opus files frame-exact against
  ffmpeg/libopus, with the efficiency measurement (instructions
  per second of audio, transplanted Opus versus stock WMA)
  recorded.
- The system-open regression must initialize the real file API and
  execute its content probe. The old extension-only harness missed
  this probe and incorrectly selected Opus while hardware selected
  Vorbis. The negative control now loads module 75; the repaired
  case loads module 72 from the same generated file.
- Phase E (hardware): successful playback, metadata and the
  worst-case underrun gate (2.5 ms frames at 256 kbps) remain
  separate device acceptance requirements.

`patches/framework/verify.py` pins the transplanted module
hash and proves the variant's diff stays confined to module
72, the five rename sites and the derived trailer CRC, with
the default build bit-identical to before.
