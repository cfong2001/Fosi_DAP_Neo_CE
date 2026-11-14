# Library scan and responsiveness validation

Standard CE keeps natural-sort code in an explicit 1,052-byte extension of
module 39, beyond its two live 64 KiB scratch arrays. Stock initialization
erased the former code location. The lifecycle regression executes those real
clears before running the relocated prefix builder and comparator through the
database-read interface.

Opus metadata uses an original streaming OpusTags reader with bounded UTF-16
title, artist, album and genre fields. Unknown comments, including large
artwork, are skipped across page boundaries without allocating their lengths.
The reader services the stock watchdog and leaves adjacent M4A/AAC, FLAC,
APE, Ogg and other metadata dispatch code intact. Allocation is limited to the
ASF-specific case and censused resident pockets. The protected dispatch bytes
are checked independently of the payload hash.

The native content probe is also part of the playback route. Stock
`0x03067F50` changed any OggS stream to OGG after the extension lookup,
so the second lookup selected Vorbis even for an admitted Opus file.
The repair recognizes a bounded BOS OpusHead packet, selects OPU and
retains the original final seek reset. The regression initializes the
real file-API registration and models its reads, reproducing codec 4
and module 75 without the repair, then codec 1 and module 72 with it.

## Short gate

With Unicorn, Capstone and Keystone installed:

```sh
python tools/repair_metrics.py --output repair-metrics.json
```

The gate takes about four seconds on the development host. It uses generated
fixtures, the real tag dispatcher and the real FileRead/FileSeek routines;
only storage-sector access, contiguous FAT-chain lookup and interrupt gates
are modeled. Its output contains no media paths or device identifiers.

| Metric | Required result |
| --- | --- |
| Non-ASF dispatch bytes preserved | 130 / 130 |
| Metadata fields matched across four fixtures | 16 / 16 |
| Truncated-input cases returning without corruption | 9 / 9 |
| Sort code surviving both scratch clears | 1,052 / 1,052 bytes |
| Stack restoration and record guards | Pass for every fixture |
| Opus watchdog servicing | Real reload-register writes observed |
| Hidden wheel wake | 1 / 1 at the next player service pass |
| Visible wheel steps accounted | 20 / 20, without artwork re-requests |
| Selected glyph variants with orange fill, contrast and antialiasing | 30 / 30 |
| Browser admission / codec selection for generated Opus | Audio kind 1 / module 72 |
| Generated silence: initial PCM frames, 48 kHz stereo | 3,840 / 3,840 |
| Native content-probe negative control / repair | Vorbis 4 / Opus 1 |
| Malformed/non-BOS header controls retaining native Ogg routing | 6 / 6 |
| Header-buffer boundary positions and callee-register guards | 7 / 7 |
| Opus picture extraction, small and multipage fixtures | 81,814 exact bytes |
| Native JPEG rows / independent theater color matches | 54 / 3 |
| Missing or malformed artwork returns | 5 / 5 |
| Selected-control instruction ratio vs stock | At most 1.0 (currently 0.4914) |
| Selected-control resource reads vs stock | No increase (currently 14 vs 14) |

An optional corpus check compares all Opus text metadata with a host parser:

```sh
python patches/opus_swap/test_tags.py --native-fs \
  --image release/DP3_V137_CE.img --media-dir /path/to/local/media
```

The corpus check requires Mutagen. Results are counts; filenames and metadata
values are not written to the repository.

The short gate also exercises the real browser classifier, system codec
loader and transplanted decoder on a generated 200 ms silence file. Its
core-1 mailbox and file RPC use the existing harness model. Passing this
gate establishes that the image contains a working modeled route; it does
not prove that live filesystem state, boot initialization, mailbox timing
or physical playback match that model.

## Wheel latency: diagnosis in progress

The reported visible delay remains an acceptance blocker. The short gate
counts instructions, resource reads and framebuffer stores for the same
selected-control states in stock and CE. Current CE counts are about 49% of
stock's instructions, with 14 resource reads in each image. These are emulator
work counts, not measured device milliseconds; CPU frequency, scheduler
cadence, artwork decoding and physical display transfer remain separate costs.

The wheel timer changes from 400 to 1,000 microseconds. The decoded
three-sample confirmation adds at most 1.2 milliseconds in that stage. Focus
mode previously checked wheel activity only on the progress cadence
(more than 40 ticks at 100 Hz), and skipped that check once hidden. The
repaired service-entry poll wakes hidden controls in 44 emulated instructions
on the next service pass, preserves volatile inputs and the stock prologue,
and accounts for 20 successive visible wheel changes without requesting
artwork. The progress cadence remains unchanged. Scheduler and physical
display latency still require device measurement, especially for continuous
movement while the controls are already visible.

On 2026-11-14, hardware testing confirmed the repaired image boots and plays
Opus music after full readback of both written slots. Full-card scanning and
file listing had also passed. Album art and the theater background were absent
on the latest playback test and are tracked separately. Continuous wheel
latency still needs device measurement. These remaining checks do not negate
the confirmed scan and playback repair; emulator counts are not device timing.

The optional [live diagnostic utility](RUNTIME_DIAGNOSTICS.md) exposes
runtime classifier and codec state at a format-error popup without changing
the playback policy.
