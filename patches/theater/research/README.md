# Artwork row trace (stock V137)

This is research, not an installable patch. `probe_jpeg.py` and
`probe_cover_rows.py` read the stock image after verifying SHA-256
`fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`.
They require Unicorn and accept `FOSI_STOCK_IMAGE` when it is not at the
repository root:

```sh
python3 patches/theater/research/probe_jpeg.py
python3 patches/theater/research/probe_cover_rows.py
python3 patches/theater/research/probe_player.py
```

## What runs

The JPEG probe loads stock modules 0, 18 and 19 and executes module 19's
entry at `0x03085A4C`. The fixture is an original generated JPEG with
30 × 18 pixels: its top six rows are red and the rest are blue. Only the
file-read callback is modeled; the stock parser, decoder, scaling code,
module-18 size helper and RGB565 writer execute. This tests a single
baseline JPEG, not all JPEG encodings, file systems, or actual device I/O.

In the matching 30 × 18 target, dispatcher command 9 succeeds and writes
30 and 18 at context `+0x0C` and `+0x10`. Eighteen calls to command 11
advance context `+0x24` from 0 to 18, returning 1 for the first 17 and 0
for the last. The routine writes the same row buffer, `0x03027DA8`, on
every call. Its 30 halfwords are little-endian RGB565; the top six decoded
rows are predominantly red and the bottom twelve predominantly blue.
The actual `STRH` at `0x030878AC` is observed for each pixel.

The same source with a 16 × 16 target yields context fields `+0x0C=16`,
`+0x10=16`, `+0x14=16`, `+0x18=9`, and `+0x2C=3`. All sixteen calls
still execute sixteen pixel stores. These fields cannot be substituted for
each other: the player-consumer probe below establishes the row count for this fixture.
The row pointer comes from context `+0x28` plus an even byte offset
computed from `+0x0C` and `+0x14` at `0x030874F6–0x0308750A`.

The synthetic row probe separately seeds the interpolation source and
runs the real command 11 for solid red, green and blue. It checks output
word order, row reuse, completion and non-square output sizes. It is not a
replacement for real decode coverage.

## Lifecycle and proposed integration

Command 9 resets `ctx+0x24` before it tests the file handle. With a
missing file it returns failure but leaves old output bytes and the cursor
at `ctx+0x2C` untouched; the same holds for an injected header-setup
failure. An accumulator or cached color must therefore be invalidated on
all relevant start, failure, close and track-change paths. Stale row bytes
must not be used as proof that a new cover was decoded.

The current user request is the average over the **top third of the
rendered artwork**, not its border. A verified streaming implementation
could accumulate pixels as rows are produced and avoid retaining a full
bitmap. It must first establish exactly which rows and columns represent
the visible artwork when aspect ratio or orientation differs, and which
row callback gives a reliable boundary. The player-consumer probe establishes this relationship for one JPEG and two geometries; rotated images, horizontal letterboxing, and the BMP worker in module 20 remain unproven.

The existing player background cell at `0x03004400` belongs to the
resident module-0 data, but the module-27 constructor writes it again at
`0x0307D1CA`. The player painter at `0x0307EF7A–0x0307EFA8` fills the
background only in response to selected flags (`0x24`, `0x39`, `0x2F`)
and then reads that cell. We have not established a safe, persistent
valid flag or accumulator range, a complete invalidation path, or that a
repaint reliably occurs after artwork decoding. The player row buffer is reusable module-18 storage and cannot itself serve as persistent state.
Do not patch firmware on the strength of these fixtures alone.

Next: trace centered and rotated artwork and the complete real player event lifecycle; identify non-overlaid
state with bounded lifetime; prove update and no-art/error reset on every
track transition; test the module-20 path; then check repaint and clipping
under emulation and on device. The isolated top-third accumulator is not
called by firmware and does not settle which emitted rows to feed it.


## Player artwork path and executable consumer proof

The now-playing code in module 27 at `0x0307E8A4` sets requested size
144 × 144 and destination (23, 36), then calls module 18 setup
`0x0308389E`. It also invokes `0x0308399C`, which can synchronously decode
and blit rows. The player painter at `0x0307F1C4` calls the other consumer,
`0x03083B36`. Both paths call the renderer at `0x0308745E`; an integration
that observes only the painter will miss the synchronous path. Earlier
guesses that `0x030640BC` or `0x0306411A` were cover blitters were wrong:
these routines search and update banks of word pairs. The actual final
bitmap call in this path is `0x0306333E`.

`probe_player.py` runs stock `0x0308389E` and `0x03083B36` with the
30 × 18 JPEG above. The file reader, overlay load, and LCD bitmap call are
modeled, while JPEG initialization, rendering and player consumption execute
unaltered. It does not emulate the window scheduler or prove a complete
track transition. The setup initializes a separate context at `0x03026CA0`
and a reusable 640-byte row buffer at `0x03026A20`; the latter is the
actual LCD call's source in both fixtures. With a 30 × 18 target, 18 rows
are blitted at y=36..53. With a 16 × 16 target, scaled artwork height
`ctx+0x18` is 9 and nine rows are blitted at y=36..44; the first three
rows yield red RGB565 sums 1488 and blue 0. The probe compiles the isolated
`frame_average.c` as a host library and feeds it the observed blits; it
returns RGB (255, 0, 0) in both geometries. This confirms that the top
third for this player geometry is based on scaled artwork height rather
than target height. The fixture sets the player flag at `0x030259DC`,
which makes the initial row cursor zero; other flag modes need testing.

Completion has a subtle distinction: in the 30 × 18 fixture the final
row call returns zero but leaves the cursor at 17, and a manually forced
extra call draws another row. In the scaled fixture the first nine calls
return one, cursor reaches nine, and the next call returns zero without a
blit. These observations do not establish whether the real scheduler makes
either extra call. A production hook must use explicit lifecycle and row
count, not assume that the renderer return value alone signals that all
visible art rows have been captured.

Module 19's code allocation ends at `0x0308837C`, exactly where module 33
starts; growing it unconditionally could overwrite that module. Module 18
likewise ends at the module-19 start. No safe persistent accumulator
storage, insertion space, error/track-change invalidation, or repaint
trigger has yet been established, so these probes do not justify a
shipping firmware hook.
