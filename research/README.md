# Research, existing code and community work for adding features to the DAP Neo

Compiled 2026-10-31, after the Phase 1/2 reverse engineering in
`../analysis/`. The question: what already exists that we can build on,
and what is the easiest honest path, for each of these goals? Gapless,
lock-screen info, Bluetooth shortcut, M3U playlists, library sorting and
navigation, battery profiles, control remapping, standalone firmware.

Method: three passes. A deep read of NeoPod and its EchoPod upstream
(`neopod_echopod.md`), a deep read of the RKnano patch-technique
references and the leaked SDK (`patch_technique_and_sdk.md`), and a
community-wide landscape survey (`community_landscape.md`). Findings
below are attributed to the pass that established them; "verified"
there means the artifact itself was opened.

## The landscape in one paragraph

The Neo has exactly **one** public modifier (danielNZ27, NeoPod plus
the restore tool; zero forks, no other projects, no forum scene). The
reusable work lives in the **Snowsky Echo Mini** ecosystem, same
RKnanoD SoC, same SDK family, about a year ahead: three from-scratch
firmwares (RECHO, echo-mini-newfw, ReChord), a validated stock-firmware
decoder-swap patch (echo-mini-opus), a complete stock-patch framework
for the sibling Echo Nano (nanitecfw), and NeoPod's own upstream
EchoPod. Rockbox has **no** RKnanoD target and its nearest Rockchip
relative (RK27xx) is a different, abandoned architecture. A verified
negative, corroborating the Phase 2 assessment from the outside.

## The documents

- **`neopod_echopod.md`**. NeoPod is a content-verified port of
  BasilSkyWalk's EchoPod (squashed single commit; identical tree and
  build files; settings format continues upstream's versioning).
  NeoPod's own additions are the EQ + ReplayGain layer, AAC/Opus
  decoder programs, and wheel keys; upstream has Bluetooth audio,
  which NeoPod dropped. Per-feature: implementation evidence
  (files/functions), portability verdicts, license table. Headline:
  **nothing rates "exists and portable" end-to-end**. Nobody has ever
  patched the Neo's stock firmware, so every feature needs stock-side
  integration built by us, but every feature's *design and most of
  its logic* already exists somewhere in this pool.
- **`patch_technique_and_sdk.md`**. Nanitecfw (MIT) is a complete
  patch-authoring system for Echo Nano stock: patch grammar, Thumb-2
  patches assembled at their target address, code caves in dead stock
  code, a hooks manifest with a wrap mode, typed pointers into stock
  functions, and the date-bump discipline our validator findings
  predict (their loader boots the newest-dated slot). Its library
  rewrite (148 s → 28 s refresh) and its two power patches
  (clock-table data edit; idle/WFI instruction patch) are finished
  models for two of our goals. The leaked RKnanoD SDK (proprietary,
  reference only) **confirms our binary RE from source**: loader flag
  values, the settings saver's exact behaviour, the checksum, the WIN
  struct, and a `BtConfig.btOpened` field matching our BT state byte.
  Corrections logged there: intelarc's echo-mini-fw targets the
  full-size Snowsky ECHO, not the Mini, and is unlicensed. Its facts are
  usable; its code is not.
- **`community_landscape.md`**. The survey: RECHO (closed source;
  behavioural benchmark for nearly every goal, incl. gapless across
  sample-rate changes and load-following CPU clock), echo-mini-newfw
  (MIT, from scratch, with a full hardware study, the cleanest
  standalone porting base), ReChord (GPL; gapless within a format; a
  concrete SRAM data point: 192 kHz FLAC needs a ~143 KB decode
  window), echo-mini-opus (BSD-3; the decoder-swap patch), tooling,
  and the explicit negatives per goal.
- **`performance_maximization.md`**. The follow-on test round and
  plan: the Vorbis low-precision bug **proven** on the Neo's module
  75 (`../analysis/vorbis_precision_test.md`); the clock table found
  and decoded, stock runs the decode core at its 480 MHz cap for
  everything hi-res, and 450 MHz for WAV
  (`../analysis/clock_table.md`); the 0xEC poster identified, moving
  the gapless hooks earlier, to the playback monitor's finalize
  blocks (`../analysis/ec_poster.md`). Finish lines per axis
  (fidelity in effective bits, transition offset in samples, latency
  budgets, headroom, tuned clocks), a claims register treating every
  "impossible" as a hypothesis, and the phased implementation plan
  (framework + data patches → Vorbis swap → gapless/M3U → core-1
  harness → hardware).

- **`external_sources_2026-11.md`** (2026-11-08). A second pass over
  external sources, with each candidate scored for difficulty and reward.
  The best ratio by far: the CS43198 datasheet shows stock's five
  `0x090000` values are the chip's five digital filters, a selector stock
  never wires to a menu, so a one-byte patch can offer the other four.
  Also new: the RKNanoD TRM is publicly hosted, echo-mini-newfw (MIT)
  documents the decode accelerators with emulator models and measured
  loads, NeoPod v1.7.0 runs Bluetooth audio on the Neo, and FiiO added
  M3U to SDK-family stock firmware.

## Easiest path per goal (synthesis)

| Goal | Route | Build on | What remains ours |
|---|---|---|---|
| Gapless | Patch stock per the Phase 1 design; **no stock-patch prior art exists anywhere** (two independent passes confirm; echo-mini-newfw's author reached the same "can't patch it" conclusion about Echo stock and went from scratch) | Phase 1/2 module-33 design; NeoPod's segment/trim engine and RECHO as design references | The module-33 fast path + pre-open; finding the 0xEC poster |
| Lock-screen info | Patch stock at the pinned hooks | Stock status painter / module 31 Display; NeoPod/RECHO play screens as the content model | The hook + artist snapshot extension |
| Bluetooth shortcut | Build it, **zero community prior art** | Our module 81 routine + SAVEINFO +0x2D4; nanitecfw's key-cave technique as the trigger mechanism | Everything except the technique |
| M3U playlists | Port the reference parser/resolver logic (the one "(a)-grade" component found) into a CUE-modelled overlay | NeoPod/EchoPod `playlist_reader.c` (UTF-8 sniff, 3-stage path resolution) | The stock hook and the path → (cluster, index) bridge |
| Library sorting | Port nanitecfw's measured design to our addresses | Walk-hook keys + FNV hashes, replaced comparator, spare-sector tables; sort-key *rules* (casefold, accent-strip, ignore leading "The ") from EchoPod's library spec for our key builders at 0x0307D80A/0x0307D8C4 | Address re-derivation on the Neo image |
| Battery profiles | Patch, the easiest goal | nanitecfw's `power_clocks` (data-only clock-table edit) + `power_idle` (WFI + poll constants), retargeted to resident module 0; profile state in SAVEINFO +0x1C7..+0x2D5 | Retargeting; the profile bundle UI |
| Control remapping | Cave-sized patches for fixed remaps (producer-side); full remap UI stays hard | nanitecfw's shuffle-key cave (intercept fetched key, rewrite, let stock dispatch proceed); NeoPod's `navigation_from_key()` as the mapping-table design | The interception on Neo stock |
| EQ / ReplayGain (bonus) | Lift NeoPod's small fixed-point units | `eq.c` / `replay_gain.c` (NeoPod-only work, GPL-3.0) | The stock insertion point, modules 35/36 DSP machinery is the open RE item |
| Standalone firmware | **Fork/port an existing RKnanoD firmware**, echo-mini-newfw (MIT) or NeoPod (GPL-3.0, already on this device, but no Bluetooth), under the dual-slot arrangement | newfw's ETUDE hardware study; our `dual_slot_and_standalone_plan.md` | The Neo port + (for NeoPod) re-adding BT |
| Audio-quality bug (bonus) | Test, then port a validated fix | echo-mini-opus's full-precision Tremor Vorbis replacement (.ecpatch, BSD-3) | One emulation test (below) |

## Cross-cutting lessons

- **Adopt nanitecfw's authoring layer wholesale** (it is MIT): patch
  grammar, per-change files, hooks manifest, SHA gate, date+1 build
  discipline, a same-build recovery image. Our patcher already does
  the container half (CRC, mirror); this adds the code half.
- **Distribution format:** `.ecpatch` (echo-mini-opus) and
  patches-only releases (nanitecfw) are both proven on this family;
  either beats shipping full images.
- **Licensing discipline:** the SDK is proprietary (dictionary, never
  donor); intelarc's tool is unlicensed (facts only); NeoPod/EchoPod/
  ReChord are GPL-3.0; nanitecfw and echo-mini-newfw are MIT;
  echo-mini-opus is BSD-3. **Flag:** NeoPod's Helix AAC is RealNetworks
  RPSL/RCSL, not GPL. Do not lift it into anything distributed
  without reading those terms.
- **NeoPod trades away Bluetooth.** Any plan that adopts it wholesale
  loses a stock feature the shortcut goal depends on; the patch route
  keeps it. This is the strongest argument for patch-first.
- **A FiiO representative's claim that M3U "isn't possible on this
  hardware" is disproven** by two firmwares on the same SoC; Fosi's
  own FAQ confirms stock has no gapless.

## Named follow-ups this research produced

1. **Vorbis precision test: DONE** (2026-10-31). Module 75 is
   proven to be the `_LOW_ACCURACY_` build
   (`../analysis/vorbis_precision_test.md`); the Tremor swap is a
   validated fix. Remaining: measuring the module's own PCM output,
   which needs the core-1 harness (item 5).
2. **EQ insertion point:** finish characterizing modules 35/36 (the
   DSP coefficient machinery) as the host for lifted EQ/ReplayGain
   code.
3. **0xEC poster: DONE** (2026-10-31). The producer is module 0's
   playback monitor; the gapless hooks move to its finalize blocks
   (`../analysis/ec_poster.md`).
4. **Clock-table location: DONE** (2026-10-31). The table is 36 rows × 0x1C at
   module 0 `0x03079824`, decoded in
   `../analysis/clock_table.md`; stock clocks and the tuned-table
   targets are in `performance_maximization.md`.
5. **Core-1 emulation harness:** stand up the message-unit/HifiFile
   server (spec in `../analysis/vorbis_precision_test.md` §6) to
   unlock PCM-level measurement for every codec, Phase D of the
   implementation plan in `performance_maximization.md`.
