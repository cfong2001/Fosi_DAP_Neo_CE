# NeoPod / EchoPod as reference code for patching the Fosi DAP Neo stock firmware

Research date: 2026-10-31. Purpose: determine, per target feature, how the existing
custom-firmware ecosystem implements it, how portable that implementation is to a
binary patch of the stock firmware (DP3_V137.img), and the easiest path to each
goal, including work that already exists outside the two main repos.

Sources read directly (local clones):

- `refs/NeoPod-Fosi-DAP-Neo-Custom-Firmware/`: danielNZ27/NeoPod, v1.5.2, commit
  `b40ee16` (single squashed commit), GPL-3.0. Remote:
  `https://github.com/danielNZ27/NeoPod-Fosi-DAP-Neo-Custom-Firmware.git`
- `refs/echopod-upstream/`: BasilSkyWalk/echopod, HEAD `8b0bad5` "release: EchoPod
  0.6.0", 238 commits, branches `main`, `bluetooth-audio`, `test/0.2-candidate`.
- Also in `refs/`: `nanitecfw` (maaraneasi), `intelarc/echo-mini-fw`,
  `Fosi-Dap-Neo-firmware-restore-tool` (danielNZ27), `rknanod-sdk` (leaked 2016
  Rockchip RKnanoD MP3 SDK).
- GitHub API (unauthenticated reads, 2026-10-31): repo metadata, branches, issues,
  forks, compare, and repository search for both projects and the wider scene.
- Web: Fosi Audio EU product FAQ; RECHO project page (recho.atzkey.workers.dev);
  berettavexee/echo-mini-opus README; Head-Fi Echo Mini thread (vendor statements).

Stock patch points referenced below are from our completed RE of DP3_V137.img
(stage/ and stage2/ analysis): lock hook = module 31 Display `0x0307ED40` / shared
status painter in module 0 ≈`0x03055A5A`, snapshot buffer `0x030235CE`; BT power
routine `0x0307D1A8` (module 81), state SAVEINFO+0x2D4; gapless = module 33 chain
(open `0x03089E2E`), decoder image re-copied per open via loader `0x0306777A`; M3U
model = stock CUE parser (module 37), tracks referenced by (cluster, index);
sort keys built at `0x0307D80A`/`0x0307D8C4` (module 39); persistent patch config
can only live in the SAVEINFO verbatim block +0x1C7..+0x2D5.

Easiest-path verdict key (per the expanded brief):

- **(a)** already exists in reference code and is portable to the stock-patch route
- **(b)** exists in some form and needs adaptation
- **(c)** must be built

---

## 1. Lineage: is NeoPod derived from EchoPod?

What the repos claim. NeoPod's README states: "NeoPod is a direct hardware port
of EchoPod by BasilSkyWalk." Its license section says GPL-3.0, "inheriting the
open-source license of the upstream EchoPod project." NeoPod's CREDITS.md credits:
EchoPod (GPL-3.0-or-later) as the base; hardware knowledge largely from ReChord
(brnomt/ReChord, GPL-3.0) and the livetrack.club debrick guide; EchoPod Enhanced
(qurolates/echopod-enchanced) as the source of the AAC/Opus integrations and
audio-settings work adapted into NeoPod.

Verification against the upstream repo. Confirmed derived, by content:

- NeoPod's git history is a single squashed commit (`b40ee16`). There is no
  shared git history with upstream, so lineage rests on file content, and the
  content is decisive: the two `src/` trees have identical layout (app, codec, core,
  fonts, gfx, hal, image, library, playback, settings, ui) and most files differ
  only in board-specific or feature-specific hunks. `CMakePresets.json` is
  byte-identical between the repos.
- NeoPod's `ROADMAP.md` is EchoPod's roadmap at its 0.3.0 state, unedited
  (it still says "EchoPod roadmap" and lists Bluetooth audio as in-progress).
  Upstream's current roadmap has since shipped Bluetooth audio, a charge screen,
  a Random album tile, and album grouping across featured artists.
- Settings file format version is a direct continuation: upstream `settings.c`
  has `VERSION = 4`; NeoPod's has `VERSION = 6` with decode branches for every
  earlier version.
- Upstream git history (238 commits) contains the original feature commits NeoPod
  inherits, e.g. `12358c8` "feat: play music with a queue, shuffle, repeat, gapless
  hand-over and resume" and `4fa758c` "feat: gapless MP3 from the LAME tag's
  encoder delay and padding".

What NeoPod added on top of upstream 0.6.0 (full-tree diff; "Only in NeoPod"):

- `src/core/eq.c`, `src/core/replay_gain.c` (+ headers), the entire EQ/ReplayGain
  DSP layer. Upstream has neither file; upstream's roadmap still lists both as
  todo. NeoPod leapfrogged its own upstream on exactly this feature area.
- Screens: `custom_eq_screen.c`, `equalizer_screen.c`, `save_preset_screen.c`.
- Core-1 decoder programs `aac_main.c`, `opus_main.c` (+ `core1_aac.ld`,
  `core1_opus.ld`) and logic `aac_decoder.c`, `opus_decoder.c`, `core1_aac.c`,
  `core1_opus.c`, `aac_probe.c`, `opus_probe.c`, `replay_gain_probe.c`,
  `boot_power.c`, adapted from EchoPod Enhanced per CREDITS.
- `KEY_WHEEL_UP`/`KEY_WHEEL_DOWN` added to `src/core/include/core/key.h`
  (upstream has 6 keys, NeoPod 8), the Neo's scroll wheel.
- `platform/neo_diag/`: a diagnostic image target (see §2).

What upstream has that NeoPod does not (yet): `src/app/bluetooth_link.c`,
`bluetooth_store.c` (Bluetooth audio, shipped in upstream 0.6.0), `charge_screen.c`,
`src/gfx/font_pack.c` + `src/fonts/packs` (downloadable CJK font packs),
`src/library/library_builder_albums.c`, board `glyphs.c`.

Timeline. Both projects are days old: EchoPod repo created 2026-10-24,
NeoPod repo created 2026-10-30, NeoPod v1.5.2 released 2026-10-31. NeoPod has
0 forks, 1 star, no PRs, exactly 2 issues (both closed; see §4). This is a
two-author ecosystem (BasilSkyWalk, danielNZ27) plus the EchoPod Enhanced author
(qurolates).

---

## 2. Build system, toolchain, image packaging, code structure

Build. CMake ≥ 3.25 + Ninja, presets in `CMakePresets.json` (dev / device /
release / sim). Compiler: `arm-none-eabi-gcc`, C11, freestanding, no heap
anywhere in `src/`. All state is static or caller-provided buffers. Each layer
is a static library (`src/*/CMakeLists.txt`). Targets in
`platform/device/CMakeLists.txt`: `echo_device` (main firmware), `echo_core1`
plus one core-1 program per codec (`echo_core1_mp3`, FLAC, and in NeoPod AAC and
Opus), each with its own linker script (`core1/core1*.ld`, board
`echo_device.ld`), and a rescan overlay. A desktop SDL simulator
(`platform/sim`) runs the same `src/` code, and there is a large host test suite:
29,228 lines of tests; NeoPod's CHANGELOG reports the Neo-configured host run
passes 109 of 117 suites (the 8 failures are named in the changelog; the
suite is not claimed fully green).

Sizes. `src/` = 32,254 lines of C/H; `platform/device/` = 18,599 lines. Per
the architecture doc, the device code window is `0x2666C` (157,292) bytes and
the firmware nearly fills it, a useful bound on how much code a stock patch
could ever add. Default static app RAM budget `ECHO_APP_RAM_BUDGET_BYTES` =
131,072.

Packaging. `tools/make_image.py` writes the Rockchip RKnano update container:
magic `RKnanoFW` at 0x1F8, CRC-32 polynomial `0x04C10DB7`, table at 0x208 with
capacity 91 rows (stock DP3_V137 has 82 module records, same format family,
same CRC polynomial and same 0x03050000 code base our RE established
independently; the tool is a cross-check on our container findings). Output
names: `DP3_V152.IMG` (Neo), `HIFIEC90.IMG` (Echo Mini).

Install route. Copy the .IMG to the root of internal storage; the stock
bootloader performs the flash (the same route as a stock update, no exploit
involved). The core-1 decoder programs and library scanner are *not* in the
image: they ship as files on the microSD card: `/.echo/neo_flac.bin`,
`neo_mp3.bin`, `neo_aac.bin`, `neo_opus.bin`, `neo_scan.bin`, loaded from SD at
runtime (consistent with our Phase 1 xref finding that NeoPod does not use eMMC
for decoders on the Neo). Recovery: Rockusb mode (hold VOL+/VOL−/OK, plug
USB-C; VID 0x2207 PID 0x262D) with `flash-neo.py` from danielNZ27's separate
restore-tool repo, which flashes both slots.

Direct link to the stock-patch route. NeoPod's own `tools/build_neo_image.py`
builds the author's diagnostic image by taking stock DP3_V137.img as a
template, substituting module 0, fixing metadata and CRC, and it imports the
`rknano_fw` library from `investigation/nanitecfw/tools` (maaraneasi's
stock-patching project for the sibling Echo Nano). I.e., even the full-firmware
project's Neo tooling is built on the stock-image patching toolchain, and its
diagnostic flow is the same module-substitution our offline patcher performs.

---

## 3. Licenses, per component

Overall project license (both repos): GPL-3.0-or-later. Components vary, per
NeoPod's CREDITS.md and `third_party/`:

| Component | License | Notes |
|---|---|---|
| EchoPod/NeoPod code (incl. own FLAC decoder in `src/codec`) | GPL-3.0-or-later | |
| libmad 0.16.4 (MP3 decoder, core-1) | **GPL-2.0-or-later** | `third_party/libmad` |
| Helix AAC decoder (NeoPod AAC) | **RealNetworks RPSL / RCSL, not GPL** | `third_party/helix_aac` ships `RPSL.txt`/`RCSL.txt`; sourced via arduino-libhelix. Source-available with its own terms; do not lift into a distributed patch without reading both licenses. |
| libopus 1.5.2 (NeoPod Opus) | BSD-style (Xiph) | `third_party/libopus/COPYING` |
| dr_libs (simulator-only FLAC/MP3/WAV) | Public domain or MIT-0 | Not in device builds |
| Inter font | SIL OFL 1.1 | Noto Sans CJK font packs (upstream) also OFL 1.1 |
| rkdeveloptool | GPL-2.0 | Host tool, not shipped in firmware |
| USB VID 1209 | pid.codes assignment (upstream) | |

Community precedent for comparison: berettavexee/echo-mini-opus is BSD-3-Clause
(libopus and Tremor also BSD-3), the most license-permissive code in the scene.
GPL-3.0 reference code can be studied freely; distributing a patched stock image
that *contains* adapted GPL code carries the usual source-availability
obligations, and the stock image itself is Fosi's proprietary binary. Both are
flagged as facts for the project, not legal advice.

---

## 4. Community landscape beyond the two repos

GitHub repository search (2026-10-31): "fosi dap neo" returns exactly 2
repos: danielNZ27's NeoPod and his restore tool. No other DAP Neo firmware
work exists. The reference pool is the sibling Echo Mini scene (same RKnanoD
SoC, same stock firmware family):

- berettavexee/echo-mini-opus: the key precedent for this project: a
  binary patch of the official stock Echo Mini V3.9.0 firmware
  (`HIFIEC39.IMG`), validated on hardware. It replaces the stock WMA decoder
  module with libopus, replaces the stock Tremor Vorbis decoder with a
  full-precision build (the stock one runs at reduced precision, ~7 effective
  bits per their RE), and lowers the audio-core clock for Ogg playback.
  Delivered as `.ecpatch` files applied by `patch/apply_patch.py` to the stock
  image; installed by copying the patched IMG to internal storage. Ships
  `docs/OPUS_PORTING.md` / `docs/TREMOR_PORTING.md` with porting checklists
  "for other players" and a full RE report. BSD-3-Clause. This proves the
  module-swap patch technique end-to-end on this firmware family.
- RECHO (atzkey, recho.atzkey.workers.dev): from-scratch Echo Mini
  firmware, currently closed source ("source code will be published after
  the project matures"). Claims gapless across FLAC/WAV/MP3 *including across
  sample-rate changes*, a 10-band EQ, ReplayGain (track/album/auto, preamp,
  clipping prevention), and settings in an editable text file `RECHO.CFG`.
  Design reference only. No code available.
- BlackVllad/Echo-Mini-Customizer (28 stars) and Parche-Firmware-Echo-Mini:
  PyQt5 tooling that patches stock Echo Mini images at the resource level
  (themes, animations). Precedent for resource-level stock patches (relevant to
  feature 2's artwork/text side).
- maaraneasi/nanitecfw: patches the Echo Nano's stock firmware and boots
  it; its Python `rknano_fw` image library is the one NeoPod's own build tools
  import (§2).
- intelarc/echo-mini-fw, Losses/flame-ocean: Echo Mini firmware RE
  toolkits/notes.
- Forks of EchoPod: `invis-z/echopod` is a pure mirror (18 commits behind,
  0 ahead). `pedrox86lopes/echopod` diverged at the 0.2.0 era; its "ahead"
  commits are old EchoPod history, not new feature work. No feature-bearing
  forks exist. `gongchunru/echopod-release` is a release mirror.

Issues as evidence (attempted / solved / abandoned):

- NeoPod #1 "FLAC songs at over 200kbps sound distorted" (2026-10-30) → closed
  same day; root cause was the tiny-block decoder handoff fixed in v1.5.2
  (CHANGELOG, feature 1 below).
- NeoPod #2 "All songs menu is 1/2 cut off visually" → closed with v1.5.2.
- EchoPod #3 (open): requests for long-press-volume fast-forward, M4A, Opus,
  lyrics. M4A/Opus were in fact solved by EchoPod Enhanced, then ported into
  NeoPod (§1). Lyrics remain todo in both roadmaps. Nobody has attempted them
  in this ecosystem beyond the request.
- EchoPod #1 (open, 14 comments): a user cannot revert; the player rejects
  stock and alternative images as invalid; the workaround that emerged (also in
  issue #4) is to install official firmware 3.8 first. Evidence that the
  file-copy install route is fragile in the field, relevant to any patch
  project's install/rollback story.
- EchoPod #4 (open): "Consumes battery while off": 98%→85% overnight fully
  powered off, plus ~3% per song. A caution against importing the replacement
  firmware's power behaviour uncritically (feature 7).
- Vendor claims: Fosi's EU FAQ states plainly "Gapless playback is not
  available on DAP Neo" (stock), matching our binary RE. A FiiO representative
  told Head-Fi that M3U support "isn't possible on this hardware" (Echo Mini);
  two independent firmwares on the same SoC implement it. Vendor impossibility
  claims in this product family should be treated as product decisions, not
  technical facts. (AI-generated content-farm pages about the DAP Neo claim
  conditional M3U support on stock; they contradict the binary evidence and
  were disregarded.)

---

## 5. Feature 1: Gapless playback / track transitions

How NeoPod/EchoPod implement it (all in the portable + device-logic layers;
this is an EchoPod-original feature, upstream commits `12358c8`, `4fa758c`):

- `src/app/player.c`: when a track starts, `queue_upcoming()` resolves the next
  track (Up Next queue → play queue with shuffle/repeat) and immediately calls
  `hal_audio_queue_next(path, next_token)`. Tracks carry monotonically
  increasing tokens; `player_update()` watches the HAL status token flip to
  `next_token` to advance its own state.
- `platform/device/logic/audio_engine.c` (496 lines, host-testable): a single
  24-bit stereo ring buffer plus up to 4 `AudioSegment`s (token, ring
  start offset, base_ms, sample rate, track info, path), so two tracks' PCM
  coexists in one ring. `audio_engine_queue_next(path, token)` just records the
  next path. Decoding runs ahead of consumption (`audio_engine_pump`);
  when the decoder source returns end-of-stream, `finish_decoding()` opens
  the queued next track on the same decoder source and keeps appending to the
  same ring. No ring reset, no DAC re-init, position/token reporting rolls
  over segment boundaries (`drop_finished_segments`, `audio_engine_status`).
- Rate changes are the one non-seamless case: the engine marks `rate_pending`,
  lets the ring drain, then `board/audio.c:change_rate()` stops the DMA
  transfer, reconfigures the DAC path (`ensure_path(rate)`, a no-op if the
  path is already up at that rate, which is the common same-rate transition)
  and calls `audio_engine_restart()`. DAC fades wrap play/pause/seek/skip/
  rate-change (fade service in `board/audio.c:serve_fade`, ramp math in
  `logic/dac_sequence.c:dac_ramp_next`).
- Codec-exact trimming: `platform/device/logic/mp3_probe.c` parses the LAME
  header's encoder delay/padding and converts them to head/tail sample trims
  (net of the decoder's own delay) so MP3 transitions are sample-exact. FLAC
  runs on core 1 behind `logic/core1_stream.c`: a shared-memory `StreamControl`
  with two PCM slots and generation counters.
- Board glue (`platform/device/board/audio.c`, 943 lines): DMA ring of
  7 × 4000 words (112,000 B engine ring ≈ 14,000 stereo frames); on start it
  prefills rate/4 frames (capped at ¾ ring) before unmuting; 3 s after stop it
  powers down the DAC path and core 1 (`shut_down_when_idle`, IDLE_SHUTDOWN_MS
  = 3000).
- v1.5.2 CHANGELOG documents a real-world gapless-adjacent fix: FLAC files with
  47-sample blocks starved the two-slot core-1 handoff (~2.13 ms queued);
  short blocks are now batched to ≥2,048 samples/slot (~93.8 ms queued), with
  the full track verified sample-identical to FFmpeg. Any reimplementation on
  this hardware will hit the same handoff-granularity issue.

Portability to a stock patch. The engine itself is a different playback
architecture from stock's (stock: module 33 opens one track at a time and the
loader at `0x0306777A` re-copies the decoder image on *every* open, ours
included). No part of `audio_engine.c` can be dropped into the stock binary.
What transfers: (1) the decomposition (pre-open the next track, keep the DAC
path configured across the boundary, trim codec delay/padding); (2) the LAME
trim math in `mp3_probe.c`, which is small and self-contained; (3) the segment
bookkeeping idea if a patch injects code into module 33's open chain
(`0x03089E2E`). RECHO independently proves gapless, including across rate
changes, is achievable on this SoC by a third party, but its code is closed.

**Easiest path: (b)**: exists in proven form on this hardware (twice: EchoPod
lineage and RECHO) and the design + trim math are reusable, but the stock-side
integration (hooking module 33's chain, suppressing per-open decoder reload and
teardown at the boundary) must be built. Not (a): no Neo-stock patch for
gapless exists anywhere (GitHub search: the Neo has exactly two repos, both by
NeoPod's author). Not (c): the hard design questions are answered and
host-testable reference code exists.

## 6. Feature 2: Lock / hold screen content

Finding: neither firmware has a lock screen, and the Neo has no hold switch.
The "locked" state is *display off*, governed by `src/core/power_policy.c`:

- Power tap toggles the display; with the display off, Play and volume keys are
  returned as background keys (`power_policy_key` → `background = true`):
  tap volume = volume, hold volume = skip, Play = pause. Playback control
  without waking the screen (app.c swaps the volume keys to
  `KEY_BEHAVIOR_TAP_HOLD_REPEAT` whenever the display is off).
- On wake, the app returns to Now Playing unless the current screen sets
  `stays_on_wake`.

So the content question reduces to what Now Playing draws, in
`src/app/screens/now_playing_screen.c` (935 lines): album cover (112×112,
from `covers.bin`), then title / artist / album as three text lines with
marquee scrolling for overflow (`draw_track_text`), a progress bar computed by
`now_playing_progress_width(position_ms, duration_ms, width)`, position and
duration, shuffle/repeat mode indicators, a transient volume-feedback overlay,
and the shared status bar (battery, etc.) from `src/ui/status_bar.c`.

Portability to a stock patch. Stock already *has* a locked-state painter.
Our RE found the shared status painter (module 0 ≈`0x03055A5A`, module 31 copy
at Display `0x0307ED40`) drawing hold icons (stock images 38/39, selected by
bit 2 of `0x030230EC`) into the snapshot buffer at `0x030235CE`. The patch task
is therefore augmentation of an existing painter, not a new screen. NeoPod's
contribution is the content model and layout (cover + 3 tag lines + progress)
and the background-keys behaviour; Fosi's own FAQ documents that stock's
locked state already has a control scheme (center button: 1 press =
play/pause, 2 = next, 3 = previous), i.e. stock and reference agree that
screen-off is a control mode, not a dead state. Theme/resource-level patching
of stock images also has a working precedent (Echo-Mini-Customizer, §4).

**Easiest path: (b)**: the screen to extend exists in stock with known hook
points; the reference supplies the what-to-draw design. The drawing code itself
is not reusable (different gfx stack), so not (a).

## 7. Feature 3: Physical control mapping and shortcuts

Architecture (four layers, no user-facing remapping UI anywhere; mapping
is code, in exactly one function):

1. Hardware scan: `platform/device/board/input.c`: SARADC channel 1 reads the
   resistor ladder; battery shares the ADC (1 of every 20 scans). Neo-specific:
   OK key on GPIO2.14, power on GPIO2.5, and a quadrature wheel on
   GPIO2.12/2.13 decoded by a 16-entry step table into synthetic
   `KEY_WHEEL_UP`/`KEY_WHEEL_DOWN` press+release transitions.
2. Ladder decode: `platform/device/logic/key_ladder.c`: a band table. Neo
   bands: {0–50 → VOLUME_UP, 80–180 → VOLUME_DOWN}. (Caution: our stock RE
   measured stock's decode bands as <50 and 100–199. NeoPod's VolDown band
   starts at 80 where stock's starts at 100. Do not copy these constants into
   a stock patch.)
   `logic/key_scanner.c` debounces (two consistent samples) into a transition
   queue.
3. Gestures: `src/core/key_tracker.c/.h`: per-key `KeyBehavior`
   (TAP_OR_HOLD / REPEAT / TAP_HOLD_REPEAT) and per-key long-press overrides;
   produces PRESS / LONG_PRESS / REPEAT events. Defaults in `src/app/app.c`
   (`KEY_CONFIG`): long-press 600 ms, repeat delay 400 ms / interval 120 ms;
   volume long-press 1,000 ms, power long-press 2,000 ms (shutdown).
4. The mapping table: `src/ui/navigation.c:navigation_from_key()`, a
   single switch from (key, gesture) to intent: WheelDown/VolUp = NEXT,
   WheelUp/VolDown = PREVIOUS, Play tap = SELECT, Play long = OPTIONS,
   Back tap = BACK, Back long = HOME. Screens then reinterpret intents, and
   contexts re-bind keys: Now Playing and the display-off state set
   `hold_volume_keys`, turning volume holds into skips; audiobook shelves turn
   volume holds into ±30 s/−15 s jumps; shortcuts like "hold Play on an album
   = favorite it" live in the individual screens.

Portability to a stock patch. Stock has no key-map table (our RE:
`GetKeyMask` at `0x030617A0`, behaviour compiled into each applet), so there is
no table to edit. A patch must intercept at the mask/gesture level in
module 0/31 code. What the reference gives the patch project is the *shape* to
imitate: a per-key behaviour table + gesture layer + one dispatch switch, and
concrete timings that are known to work well on this exact hardware (wheel
included).

**Easiest path: (b)**: the gesture model and timings exist and are proven on
the Neo's own controls; the interception point in stock must still be built.
No community project offers a remapping patch for stock on either device.

## 8. Feature 4: Playlist support (M3U)

Implementation (EchoPod-original, device status in the roadmap):

- Parser: `src/library/playlist_reader.c/.h`: streaming line parser over a
  `ByteSource` (512 B chunks, entries up to 1,024 B). It sniffs the whole file
  for valid UTF-8 and otherwise falls back to Windows-1252 mapping, skips a
  UTF-8 BOM, and treats blank lines and `#` lines as skips. Extended M3U
  directives (`#EXTINF` etc.) are simply comments to it. URLs are ignored.
- Resolution: `src/library/library_builder_paths.c:builder_resolve_entry()`:
  three-stage fallback: (1) exact path relative to the playlist's own folder
  (backslashes converted to `/` first, so Windows paths work), (2) exact path
  relative to the music root, (3) case-folded suffix match on trailing path
  parts (this is what makes MusicBee's absolute `D:\Music\...` exports match;
  a tie counts as not found). `\` → `/` and case-folding use generated Unicode
  fold tables (`tools/fold_table.py`).
- Storage/browsing: resolved playlists become rows in `library.db`
  (docs/library-format.md): a name row plus link rows of u16 track indices,
  browsed in the Playlists view. The builder runs in the scan overlay on device
  (`neo_scan.bin`) or on PC via `tools/library_index.py` / echo-sync, and the
  two implementations are tested to agree byte-for-byte on fixtures
  (`scan_music/`, `builder_random/with_playlists`: 30 playlists, 379 entries).

Portability to a stock patch. Stock has no playlist format at all (our RE
negative proof). The parser and resolver are small, self-contained,
host-testable C, the most liftable code in this entire study. The stock patch
design already identified (module 37 CUE parser as the structural template;
entries ultimately referenced by (cluster, index), not path) needs: a place
for the parser to live, a scan-time or open-time hook, and a bridge from
resolved FAT paths to stock's (cluster, index) track references. That bridge
is the real work; the parsing/resolution logic is not.

**Easiest path: (b)**, with the parser+resolver component itself at (a)-level
reusability as logic. Not (a) overall because the stock integration (hook +
reference bridge + a browse surface) does not exist in any project.


## 9. Feature 5: Library browsing and sorting

Implementation. A real tag database, not folder browsing:
`docs/library-format.md` specifies `/.echo/library.db` (format v3): magic
`EMDB`, 128-byte header with a 10-section directory; fixed-size records
(track 24 B, album 16 B, group 12 B, folder 16 B) plus a deduplicated UTF-8
string pool; u16 indices throughout (≤65,535 tracks). Views: Artists, Album
Artists, Albums, Genres, Folders, All Songs, Playlists, Favorites, plus
Cover Flow. Sort keys are case-insensitive and accent-insensitive (NFKD with
combining marks stripped, via generated fold tables) with a leading "The "
ignored ("The Beatles" → "beatles", "Björk" → "bjork"). Albums group by
album artist; artist album lists order by year then title. The DB is built by
an external merge sort on the card inside the scan overlay (20,000 tracks
tested in 360 KB RAM) or identically on PC by echo-sync. Favorites survive
rescans because they key albums by FNV-1a hash of (album artist, title), not
by index (`/.echo/favorites.bin`, magic `EMFV`). Covers live in a separate
`covers.bin` keyed by the same album hash. Audiobooks/Podcasts folders are
segregated into shelves with their own bookmarks file (`EMBK`).

Portability to a stock patch. The database architecture is not portable to
a binary patch. Stock's library is its own (cluster, index) world. What *is*
in scope for patching, and where the reference helps: stock builds its sort
keys at `0x0307D80A`/`0x0307D8C4` (module 39). The reference's sort-key rules
(the fold-table approach, "The " stripping, and natural ordering) are a
complete, tested specification for what those two functions should produce,
and `tools/fold_table.py` + `src/library/sort_key.c` show the data layout.
Cover Flow / tag-DB views are out of reach of patching and should be scoped
out explicitly.

**Easiest path: (b)** for sort-order improvement (rules and generator exist;
the two stock hook points are known). The full tag database would be (c) and
is not a patch-class change at all.

## 10. Feature 6: EQ / ReplayGain / DSP

Lineage first, because it decides where to read: these are NeoPod-side
additions (shipped in the v1.5.x line, per its CHANGELOG). Upstream EchoPod's
roadmap lists "Parametric EQ" and "ReplayGain" as todo to this day, and
upstream has no `eq.c`/`replay_gain.c`. NeoPod built them; RECHO independently
ships a 10-band EQ + ReplayGain on the same SoC (closed source).

EQ (`src/core/eq.c` / `eq.h`): fixed-point 5-band peaking biquads at
100 / 300 / 1k / 3k / 10k Hz, ±12 dB per band, int32 coefficients with int64
per-channel state. 17 named presets (table in `eq.c`: Flat, Acoustic, Bass
Boost, Deep Bass, Pop, Rock, …) plus a Custom slot and 8 named user
presets persisted in settings. Gains *step* toward targets (`eq_step_gains`)
so changes don't click. Screens: `equalizer_screen.c`,
`custom_eq_screen.c` (v1.5.2 replaced the Echo Mini landscape layout with a
portrait one derived from the Neo's 240×320 screen; wheel selects band, OK
toggles adjust), `save_preset_screen.c`.

ReplayGain (`src/core/replay_gain.c` / `.h`): parses tag text to centibels
(`replay_gain_parse_gain`) and peaks to Q16 (`replay_gain_parse_peak`);
`replay_gain_calculate_multiplier` applies track/album gain with peak-based
anti-clipping. Modes: Off / Track / Album. Device-side tag probing at track
open lives in `platform/device/logic/replay_gain_probe.c` (ID3v2, Vorbis
comment, MP4). Application point: the audio engine's `copy_pending` (feature 1)
multiplies each frame by a gain that ramps toward its target in /64 steps,
then runs `eq_process_frame`, so track-to-track loudness changes are
click-free. A `dsp_bypass` flag skips volume/EQ/RG entirely for bit-perfect
output.

Portability to a stock patch. The two core units are small, portable,
host-tested C. As *algorithms* they are the most directly reusable DSP code
available. The open problem is stock-side: where in the stock chain PCM can be
scaled/filtered. Our RE found stock already has DSP/EQ coefficient machinery
(modules 35/36, module 36 expanding into runtime DSP state) and an EQ selector
at SAVEINFO+0x68. Stock has *an* EQ; a patch would more likely extend/replace
its coefficient sets or insert RG gain than add a new DSP stage. NeoPod's
preset gain tables and RG math drop straight into whichever of those routes
proves open. Settings space is the binding constraint (feature 8): five int8
gains + mode + preset id fit the SAVEINFO verbatim block easily; 8 *named*
user presets do not.

**Easiest path: (b)**: DSP units and preset tables exist and are liftable;
locating/building the stock insertion point is the work. Not (c): nobody has
to design or validate the DSP itself.

## 11. Feature 7: Power / battery behaviour

Implementation: `src/core/power_policy.c` (read in full) + settings tables
in `src/settings/settings.c`:

- Screen timeout options {10, 20, 30, 60, 120, 300 s, never}; sleep timer
  options {off, 15, 30, 45, 60, 90, 120 min}; auto-off options
  {off, 1, 5, 10 min}, default 5 min. Auto-off counts only while not playing
  and not on USB (the app refreshes `stay_awake` during playback).
- Power key: tap = display on/off, long-press (2 s) = shutdown. Screen-off
  background keys per feature 2/3.
- Low battery: `src/core/low_battery.c`: below 3450 mV for 2 s without USB
  → shutdown, checked every 250 ms. The architecture doc states this rule (and
  the CPU rule below) was *copied from the stock firmware's observed
  behaviour*.
- Battery gauge: `platform/device/logic/battery_gauge.c`: average of the last
  64 SARADC readings converted through stock's voltage→percent curve, with
  a −50 mV offset while charging.
- CPU clock follows stock's rule per the doc: 200 MHz with screen on / audio
  active, 96 MHz floor only when screen off and audio idle. The DAC path and
  core 1 are powered down 3 s after playback stops (feature 1).
- No profile concept exists in either firmware: one settings set, one
  timeout, one auto-off. "Battery profiles" appear nowhere in the ecosystem.

Community signal: upstream issue #4 reports the replacement firmware
draining 98%→85% *overnight while powered off*. The reference firmware's
off-state power behaviour is worse than stock's, so its power design should be
read as a spec of *features* (timers, thresholds), not of *efficiency*.

Portability to a stock patch. Stock already implements equivalents of most
of this (that's where the rules were copied from); a patch would adjust option
tables, defaults, and thresholds, constants in known structures (several live
in SAVEINFO: brightness at +0x14, etc.). A multi-profile feature would be new
design on both sides.

**Easiest path: (b)** for behaviour tweaks (policy is one small file; every
knob is a named constant or option table). **(c)** for battery *profiles*:
they exist nowhere in the reference code.

## 12. Feature 8: Settings persistence design

Implementation: `src/settings/settings.c/.h`, `src/app/settings_store.c`:

- One file, `/.echo/settings.bin`, fixed 256-byte layout: magic `EMST`,
  version byte at offset 4 (NeoPod v6; upstream v4), an FNV-style hash
  checksum (`core/hash`), then packed fields. Decode accepts versions 1–6 and
  fills defaults for fields newer than the file (v2: auto-off, v3: USB mode,
  v4: DAC volume, then the EQ and ReplayGain fields; the CHANGELOG notes
  "persistent EQ/ReplayGain settings, backward decoding of legacy settings").
  A legacy 24-byte size is still readable.
- contents: brightness (1–10), screen-timeout index, gain level, output jack,
  start screen, shuffle/repeat, volume, auto-off index, USB mode, DAC volume,
  EQ enabled/preset/5 gains, up to 8 named EQ user presets, ReplayGain mode.
- `settings_store.c` loads at boot and writes only when the encoded bytes
  differ; the app saves when the screen goes off. Sibling files follow the
  same pattern (magic + version + FNV checksum, hash keys instead of indices):
  `favorites.bin` (`EMFV`), `bookmarks.bin` (`EMBK`), `resume.bin` (queue plan
  + cursor + position; rejected if the library fingerprint changed).

Portability to a stock patch. The mechanism (a private file on the card)
is not portable: stock code knows nothing of `/.echo/`, and patched-in code
would have to bring its own file handling. Our Phase 2 SAVEINFO work is the
binding constraint: patch-persistent data must live in the verbatim block
+0x1C7..+0x2D5 (~270 bytes) because fields in the checksummed gaps do not
survive stock's save/load. What transfers from the reference is the *design
discipline*: version byte + checksum + defaults-on-upgrade + write-on-change,
compressed into that block (a mini header of magic/version/checksum inside
+0x1C7.. costs a few bytes and buys the same migration behaviour). Capacity
forces scope choices: EQ gains + RG mode + timeout indices fit trivially;
named user presets do not.

**Easiest path: (b)**: the design exists and is proven; the storage location
is dictated by stock, and the layout must be re-cut to fit ~270 bytes.

---

## 13. Roadmap: planned features (both copies)

NeoPod's `ROADMAP.md` is EchoPod's at 0.3.0 (see §1). Its "Later" list:
Bluetooth audio (in progress at 0.3.0: "the module powers up, scans and
pairs; no audio yet"), parametric EQ (todo), ReplayGain (todo),
lyrics `.lrc` (todo), ALAC and APE playback (todo). Its "Next" list:
pid.codes USB PID, refuse to start on a near-empty battery, faster cover
decoding (~0.5 s/album), browse while covers build, playback speed for
audiobooks/podcasts, firmware images in GitHub releases, more hardware
testing. Also "configurable start screen" is marked sim-only.

Since that snapshot, upstream 0.6.0 shipped Bluetooth audio, the charge
screen, a Random album tile, and featured-artist album grouping. EQ and
ReplayGain are *still* todo upstream. NeoPod shipped both on its own (§10).
Lyrics, ALAC/APE, playback speed, and browse-during-cover-build remain
unimplemented everywhere in the ecosystem. For our patch project the roadmap
matters mainly as a negative map: nothing there is a shortcut for stock
patching, and Bluetooth audio in particular should not be expected from the
reference code for the Neo (NeoPod has no `bluetooth_link.c` at all; stock,
separately, already has its BT window in module 81 with the callable power
routine at `0x0307D1A8`).

## 14. Cross-cutting caveats for the patch project

- Echo-derived constants are not Neo facts. NeoPod inherited Echo Mini
  documentation and some numbers; our Phase 1 xref already caught EchoPod-line
  claims that fail on the Neo (eMMC usage: NeoPod uses no eMMC on Neo; the
  slot-2 sector figure 69632 is an Echo number). Verify every constant against
  the stock image before use. The key-ladder band discrepancy (feature 3) is
  the same class of trap, found this time in NeoPod's own device code.
- The two codebases are a week old and single-tester deep. NeoPod's
  changelog is candid that its full host suite passes 109/117 and that several
  features are "tested on a computer, not yet heard on the player" (the
  roadmap's own words for LAME-trimmed gapless MP3). Treat reference behaviour
  as well-tested-on-host, lightly-tested-on-Neo-hardware.
- Nothing in the ecosystem patches the Neo's stock firmware. The only
  stock-patch precedent is for the Echo Mini (echo-mini-opus, nanitecfw for
  Echo Nano). Their techniques (module swap, resource patch, .ecpatch-style
  delivery) transfer; their binaries and offsets do not.

## 15. Summary: easiest path per feature

| # | Feature | Easiest path | Basis |
|---|---|---|---|
| 1 | Gapless | **(b)** | Engine design + LAME trim proven on this SoC (EchoPod lineage; RECHO independently); stock module-33 integration must be built |
| 2 | Lock/hold screen | **(b)** | No lock screen exists in the reference: the model is display-off + Now Playing content; stock already has the painter to extend (`0x0307ED40`) |
| 3 | Control mapping / shortcuts | **(b)** | Gesture model, per-key behaviour table and one-switch dispatch exist with Neo-proven timings; stock has no table, so interception must be built |
| 4 | M3U playlists | **(b)** (parser/resolver logic itself (a)-grade) | `playlist_reader.c` + `builder_resolve_entry()` are small and host-tested; stock hook + (cluster,index) bridge must be built |
| 5 | Library / sorting | **(b)** for sort orders; tag DB not patch-portable | Fold-table/"The " sort rules fully specified; stock key builders at `0x0307D80A`/`0x0307D8C4` are the hook |
| 6 | EQ / ReplayGain | **(b)** | NeoPod-only additions; `eq.c`/`replay_gain.c` are liftable fixed-point units with preset tables; stock DSP insertion point (modules 35/36) is the open RE item |
| 7 | Power / battery | **(b)** for tweaks; **(c)** for profiles | One-file policy with named constants, rules copied *from* stock; profiles exist nowhere; reference firmware has a known off-state drain issue |
| 8 | Settings persistence | **(b)** | Versioned magic+checksum design proven; must be re-cut into the SAVEINFO verbatim block +0x1C7..+0x2D5 (~270 B) |

No feature rated (a) end-to-end: in every case *some* stock-side integration is
unbuilt, because no project has ever patched this device's stock firmware.
The reference code's real value is that it removes the design risk. Every
feature above has a working, host-tested specification running on this exact
SoC, and two of them (EQ/ReplayGain, playlists) have implementations small
enough to adapt almost mechanically once their stock hook points are opened.

*Not pushed to GitHub, per instructions. Local clones used:
`refs/NeoPod-Fosi-DAP-Neo-Custom-Firmware` (b40ee16) and
`refs/echopod-upstream` (8b0bad5, cloned for this task).*
