# Community landscape: what already exists for the DAP Neo and sibling RKnano devices

Survey date: 2026-10-31. Method: GitHub repository/issue search API
(queries: "DAP Neo", "DP3 firmware", "Fosi", "NeoPod", "Echo Mini
firmware", "Echo Nano firmware", "Snowsky", "RKnano", "ReChord"), plus
web search (RECHO, Rockbox/RK27xx, DAP Neo coverage, Reddit). Every
entry is marked **[verified]** (repo/site opened and read during this
survey) or **[mentioned]** (search snippet only). Stars and dates are
as reported by the GitHub API on the survey date. The purpose is
routing: for each of our goals (gapless, lock-screen info, Bluetooth
shortcut, M3U playlists, library sorting/navigation, battery profiles,
control remapping, standalone firmware), name the best existing work to
build on, or state plainly that none exists.

The DAP Neo itself has exactly one public modifier
(danielNZ27). The surrounding Snowsky Echo Mini community (same
RKnanoD SoC, same Rockchip SDK family) is large, active, and has
already solved several of our goals in public, including two
from-scratch firmwares with working gapless and one validated
stock-firmware codec-replacement patch. The easiest path to most goals
runs through Echo Mini work, not Neo work.

---

## 1. The DAP Neo itself

- danielNZ27/NeoPod-Fosi-DAP-Neo-Custom-Firmware [verified,
  prior local study]: the only custom firmware for the Neo. GPL-3.0,
  1 star, 0 forks, v1.5.2, actively pushed (2026-10-31). An EchoPod
  port: replaces the stock image wholesale via the stock update route
  for the player core, loads its decoders as `.echo/neo_*.bin` files
  from the microSD card. Its two GitHub issues are its own bugs, both
  closed: a visually cut-off "All songs" menu, and "FLAC songs at over
  200 kbps sound distorted" (the 1.5.2 changelog's tiny-block FLAC fix
  addresses that class).
- danielNZ27/Fosi-Dap-Neo-firmware-restore-tool [verified, prior
  local study]: Rockusb recovery flasher for the Neo (VID 0x2207 /
  PID 0x262D), flashes both slots, no open issues.
- Nothing else exists in public. GitHub repository search under
  "DAP Neo", "DP3", "Fosi", and "NeoPod" returns no other Neo project,
  no forks under other names, and no gists surfaced. Web coverage of
  the Neo (launched 2026-10-10) is press reviews and SEO explainers
  only; no Reddit or forum modding threads were found. One SEO blog
  (trendingalone.blogspot.com) claims .m3u files work on the Neo with
  relative paths and UTF-8. **[mentioned] and contradicted by our own
  binary evidence**: Phase 1 proved no playlist file format exists in
  the stock image. Do not cite it.
- Consequence: for Neo-specific work there is no community to mine,
  and no duplication either. Everything reusable comes from the
  sibling devices below.

## 2. Sibling RKnano devices: the Echo Mini ecosystem is the centre of gravity

The Snowsky Echo Mini (FiiO sub-brand) uses the same RKnanoD and the
same SDK lineage as the Neo (dual CS43131 DACs and a 320×170 panel are
the board-level differences). Its community is roughly a year ahead of
the Neo's.

### 2.1 From-scratch firmwares (standalone route: three independent existence proofs)

- RECHO: https://recho.atzkey.workers.dev/ [verified, site read
  in full]. From-scratch Echo Mini firmware by "miauk", v0.10.1
  (2026-10-23), closed source for now ("source code will be published
  after the project matures"), free binary, tested "on hundreds of
  devices". Feature list reads like our goal list: gapless across
  FLAC/WAV/MP3 including across sample-rate changes (with a published
  gapless test set), 10-band EQ + ReplayGain, logical file
  sorting with a filesystem driver "a couple of times faster than
  the official one", play-screen tags (title/artist/album/track),
  pocket controls (screen off: hold play = next track, hold back =
  previous; headphone unplug pauses), battery-aware CPU clock
  scaling with idle-core sleep (claims 20+ h playback), settings in
  an editable text file (`RECHO.CFG`), resume, exFAT, and .m3u
  support already implemented "for internal use", UX pending. The
  site also documents the recovery fact we rely on: the updater and
  USB disk mode live in the firmware's first module, so reverting to
  stock is always the same file copy. Relevance: the strongest proof
  that every one of our feature goals is achievable on this silicon.
  With source unpublished, it is a behavioural reference and a
  benchmark, not code we can build on.
- berettavexee/echo-mini-newfw:
  https://github.com/berettavexee/echo-mini-newfw [verified, README
  read]. From-scratch Echo Mini firmware, MIT, created
  2026-10-23, pushed 2026-10-30, 0 stars (new and unpublicised). Own
  decoders on the HiFi core ("core B") for WAV/AIFF/FLAC/MP3/Vorbis/
  Opus/AAC/ALAC/Musepack at 8–192 kHz, gapless + ReplayGain,
  folder browser with long names on internal + microSD (FAT32/exFAT),
  settings for brightness, screen timeout, sleep timer, idle
  power-off (the components of our battery profiles, already
  implemented), resume/seek/clock/USB disk, and a USB sound-card mode
  (16/24-bit, 44.1/48 kHz, asynchronous). No EQ or tag library yet.
  Includes `ETUDE.md`, a full study (in French) of the hardware, boot,
  both cores, and codecs, and per-decoder core-load measurements.
  Relevance: the single best code reference for a standalone on
  RKnanoD. MIT-licensed, architecturally identical to the Neo's
  stock split (system core + decoder core), written from a study of
  stock V3.9.0 with no stock/SDK code. It also states the conclusion
  our own analysis reached independently: gapless "could not be added
  by patching the stock firmware" was the author's reason for going
  from scratch (on the Echo Mini's stock build, at least).
- brnomt/ReChord: https://github.com/brnomt/ReChord [verified,
  README read]. A third from-source Echo Mini CFW, GPL-3.0,
  23 stars, pushed 2026-10-25. Boots standalone (own reset/Main, stock
  AP layer gone), UI/library working, Core B decodes while the AP
  drives the CS43131, audio 16/44.1 to 24/96. Gapless works within
  one format (same rate/channels/depth); a format change is a hard
  boundary by design (DAC re-lock). Open items it names: the 192 kHz
  FLAC edge case (max_block 16384 needs a ~143 KB decode window, a
  concrete SRAM budget data point for our ~960 KiB wall) and the DSP
  chain. Relevance: second open-source standalone reference; its
  within-format gapless design and stated limits are directly
  comparable to our gapless design.
- BasilSkyWalk/echopod: https://github.com/BasilSkyWalk/echopod
  [verified via API + local clone]. The Echo Mini replacement
  firmware NeoPod was ported from. GPL-3.0, 29 stars, pushed
  2026-10-30, at "EchoPod 0.6.0". Cover Flow UI is its signature.
  Relevance: NeoPod's upstream. When NeoPod lacks a feature or a
  fix, this is the first place to look.

### 2.2 Stock-firmware patching on RKnano (the technique references)

- berettavexee/echo-mini-opus:
  https://github.com/berettavexee/echo-mini-opus [verified, README
  read]. The most transferable single artifact in this survey.
  A binary patch for the official Echo Mini V3.9.0 firmware
  (`HIFIEC39.IMG`, 8 GB model), BSD-3-Clause, validated on device
  October 2026. It replaces the WMA decoder module with an Opus
  decoder and replaces the stock Vorbis decoder with a
  full-precision Tremor build, distributed as `.ecpatch` files
  applied by a Python `apply_patch.py`; ready-made patched images are
  release artifacts. Its porting docs (`OPUS_PORTING.md`,
  `TREMOR_PORTING.md`) explicitly include "checklists for other
  players". Two findings transfer to the Neo almost verbatim:
  (a) decoder-module replacement inside a stock RKnano image is a
  proven, device-validated operation, the same module-slot mechanics
  our Phase 2 loader trace documented on the Neo; (b) a stock
  edge-case bug in this SDK family: the stock Vorbis decoder is built
  in a low-accuracy mode with roughly 7 effective bits of output,
  audible in quiet passages and fade-outs. Whether the Neo's Vorbis
  module (module 75, "likely OGG Vorbis" in our catalog) is the same
  low-precision build is unverified. Checking it is now a named,
  cheap test (decode a known file under emulation and measure), and
  if it holds, this project's patch is the fix template. The project
  also documents running the audio core at reduced clock for Ogg
  (300 MHz vs 400–480 MHz) once the efficient decoder made it
  possible, a battery-relevant technique. Limits: 8 GB model only;
  its MaskROM recovery pointer (livetrack.club/debrick) is community
  documentation it did not itself test.
- maaraneasi/nanitecfw (NaniteCFW):
  https://github.com/maaraneasi/nanitecfw [verified, README read
  locally]. Patches (no firmware included; you supply the official
  image) for the FiiO Echo Nano stock V1.7.0, tested on device.
  Headline features are library features: ~5× faster library
  refresh (148 s → 28 s for 2,000 FLAC-heavy songs), a Recent Albums
  view (newest first, by folder creation date), and a main-menu
  Shuffle item. Relevance: proof that stock SDK-family firmware takes
  library-speed and library-navigation patches of exactly the class
  our goals need, shipped in the same patches-only distribution model
  our patcher uses. Extended by pkronstrom/echo-nano-audiobooks
  [verified via API] (MIT, 2026-10-27), audiobook/meditation features
  layered on NaniteCFW, patches only.
- BlackVllad/Parche-Firmware-Echo-Mini:
  https://github.com/BlackVllad/Parche-Firmware-Echo-Mini [verified,
  README read]. Standalone patch scripts for the Echo Mini .IMG:
  per-theme boot/shutdown animations via resource-table expansion
  (ROCK26 table 1602 → 1870 entries, metadata duplication, four
  instruction patches, header/integrity fix in `fix_img_echo_mini.py`).
  No license stated. Notes the Echo Mini does not verify the image
  CRC32 trailer during flashing (**device-specific; do not transfer
  to the Neo**), whose validator does check header mirror and CRC per
  our Phase 2 trace. Relevance: a worked example of growing the
  resource section of an RKnano image, the same resource system
  (ROCK26IMAGERES) the Neo uses, useful for any UI/lock-screen
  artwork changes.
- Losses/flame-ocean: https://github.com/Losses/flame-ocean
  [verified, tree + write-up]. Echo Mini firmware RE toolkit and
  story: breaker/fixer/bitmap/font Python scripts (MIT, Jan 2026)
  plus a long blog post, "The Story Behind Reverse Engineering the
  Snowsky Echo Mini Firmware" (https://im.not.ci/echo-mini-rse/),
  covering resource extraction and text-rendering internals.
  Relevance: resource-format groundwork from the same image family.

### 2.3 Playlists: solved sideways, not in firmware

- purpleturtle21/echo-list (EchoList):
  https://github.com/purpleturtle21/echo-list [verified, README read].
  GPL-3.0, 15 stars, pushed 2026-09-12. A desktop app that gives the
  Echo Mini "real playlists" by copying tracks into device folders
  with playlist metadata, because, in its words, the Echo Mini
  "doesn't support .m3u playlists" and its SoC "simply ignores them."
  Relevance: independent confirmation that the stock SDK firmware has
  no M3U support (matching our proven negative on the Neo), and a
  working metadata-based workaround pattern. It is a workaround,
  not the in-firmware parser our plan specifies. No in-firmware M3U
  patch for any stock RKnano firmware was found anywhere in this
  survey; RECHO's internal-use .m3u support (§2.1) is in a
  from-scratch firmware, not a patch.

### 2.4 Other RKnano devices

- ekelly95/walkman-firmware:
  https://github.com/ekelly95/walkman-firmware [verified via API].
  Firmware modding tools for Sony's NW-E390-series Walkman, which is
  also Rockchip RKnano. GPL-2.0, created 2026-10-13. Relevance: a
  second, unrelated RKnano device family with active modding tools,
  evidence the package format and tooling generalise; no feature work
  relevant to our goals found in it.
- Snowsky Disc (a different, larger FiiO player, not RKnanoD):
  b0hemia/diskOS (89 stars) and zmd22/diskos-disco are custom
  firmware/UI projects [mentioned via search]. Different platform;
  listed only to prevent confusion; nothing transfers directly.

### 2.5 Community-documented stock bugs (SDK family)

- Low-precision stock Vorbis decode (~7 effective bits): proven
  and fixed by echo-mini-opus (§2.2). The highest-value bug lead for
  the Neo; status on the Neo unverified.
- Library corruption/freeze after an official update: head-fi
  user reports on Echo Mini firmware 3.3.0 (skips, freeze on rewind,
  corrupted media library) [mentioned, forum posts, not reproduced
  here]. Anecdotal, but the failure mode (library DB corruption) is
  the same raw-sector database design we mapped on the Neo.
- NeoPod's own FLAC distortion bug (§1) is a custom-firmware bug,
  not a stock one; noted so it is not misattributed.
- No community write-ups were found documenting the Neo's stock DAC
  error-counter flaw or any other Neo stock bug. The Neo is too new
  and too sparsely owned in public. **[explicit negative]**

## 3. Whole ports: Rockbox and others

- Rockbox on RKnano/RKNanoD: does not exist. Rockbox's target
  lists (stable/unstable/unusable) contain no RKnano or RKNanoD
  target, and no porting thread or code was found. **[verified
  negative, target lists + source tree checked]**
- Closest Rockbox relative: the RK27xx port. Rockbox does carry a
  `firmware/target/arm/rk27xx` tree [verified via API], classed an
  *unusable* port (boots, displays text; never became a usable
  player). The RK27xx is a different world from the RKnanoD:
  ARM7EJ-S application core + a proprietary Rockchip DSP, tens of KB
  of internal SRAM, PMP-era peripherals. It shares with the RKnanoD
  only the vendor, a dual-core shape, and the no-MMU constraint. Its
  code would not carry over; at most its porting notes are of
  historical interest.
- Other Rockbox Rockchip ports are hosted, not bare-metal: the
  AGPTEK Rocker (Benjie T6) port runs Rockbox as an application on a
  Linux system, a different SoC class entirely (application
  processor with MMU and megabytes-to-gigabytes of RAM). Rockbox's
  own architecture notes put its targets at 1–64 MB of RAM; the
  RKnanoD's ~960 KiB total SRAM sits at/below that floor, and its
  split-core decoder model doesn't match Rockbox's unified codec
  model. This corroborates our Phase 2 assessment from the outside:
  a Rockbox port to the Neo is a research project, not an existing
  path.
- Other open DAP firmwares on RKnanoD: the three from-scratch
  firmwares in §2.1 (RECHO, echo-mini-newfw, ReChord) *are* the
  whole-port options for this SoC. All three are Echo Mini targets;
  none targets the Neo. A Neo standalone would be a port of one of
  these (echo-mini-newfw under MIT, ReChord/EchoPod under GPL-3.0) or
  a sibling effort, not a port of Rockbox.

## 4. Tooling the community uses

- rockchip-linux/rkdeveloptool:
  https://github.com/rockchip-linux/rkdeveloptool [verified via API].
  The standard open-source Rockusb/MaskROM flashing tool
  (GPL-2.0, 463 stars, maintained). Already the basis of the Neo
  restore route; the community debrick procedure
  (https://livetrack.club/debrick, referenced by echo-mini-opus;
  TheMVS/snowsky-echo-mini-recovery packages it for the Echo Mini)
  is built on it.
- BlackVllad/Echo-Mini-Customizer:
  https://github.com/BlackVllad/Echo-Mini-Customizer [verified via
  API]. PyQt5 theme/resource customizer for Echo Mini .IMG files
  (MIT, 28 stars, pushed 2026-09-09): reads/writes the same
  ROCK26IMAGERES resource system the Neo image uses. The closest
  existing tool to a general RKnano image editor.
- Patch frameworks: echo-mini-opus's `.ecpatch` + `apply_patch.py`
  (§2.2), BlackVllad's patch/fix scripts (§2.2), nanitecfw's
  patches-and-tools distribution (§2.2), matteorisso/snowsky-echo-py
  [verified via API] (Python analysis toolkit for Snowsky firmware),
  and intelarc/echo-mini-fw's resource toolkit round out the
  ecosystem. Nothing here displaces our own rknano tooling for the
  Neo package (ours is the only one that models the Neo's validator
  and dual-slot rules), but the `.ecpatch` format is a proven
  distribution format worth matching.
- Desktop-side helpers (library prep, not firmware):
  silent-sphinx/snowsky-echo-mini-toolbox (30 stars), ntr0n/
  echo-mini-file-processor (24 stars), unitreign/calliope sync
  manager, subirats345/echo-shelf control panel. Useful patterns for
  a companion tool; none affect the firmware goals.

## 5. Explicit negatives (searched, not found)

- No Neo forks, gists, patches, or modding threads beyond danielNZ27.
- No in-firmware gapless patch for any *stock* RKnano firmware.
  Gapless exists only in from-scratch firmwares (RECHO, newfw,
  ReChord) and in NeoPod. Every public attempt concluded, as we did,
  that stock's per-open decoder reload blocks it; nobody has published
  a stock fast-path patch. **[gapless-on-stock: build it ourselves]**
- No Bluetooth feature work anywhere in this ecosystem: no BT
  shortcut, toggle fix, or BT stack work in any repo surveyed. The
  Neo's BT window finding stands alone. **[build it ourselves]**
- No lock-screen patch for stock firmware. The nearest prior art
  is presentational: RECHO shows full tags on its play screen and
  EchoPod/NeoPod draw their own now-playing screens, design
  references inside standalone firmwares, not patches.
- No battery-profile feature in any stock patch. The components
  exist in echo-mini-newfw's settings (brightness/timeout/sleep/
  idle-off) and RECHO's load-following CPU clock, as standalone
  firmware features.
- No control-remapping patch for stock. RECHO's pocket controls
  are again a standalone-firmware behaviour.
- No Rockbox (or other external OS) port to RKnanoD, at any maturity.

## 6. Easiest known path per goal

| Goal | Easiest known path | Build on | Evidence |
|---|---|---|---|
| Gapless | On stock: build the module-33 fast path ourselves: no prior art exists. On a standalone: adopt an existing gapless pipeline design. | Our Phase 2 design; RECHO/newfw/ReChord as design references | §2.1, §5 |
| Lock-screen info | Patch stock per our design (hook points already pinned); use RECHO/NeoPod play screens as the layout reference. | Our saveinfo_and_lock.md hook points | §2.1, §5 |
| Bluetooth shortcut | Build it ourselves on the Phase 2 BT-window finding, zero community prior art. | Module 81 routine, SAVEINFO +0x2D4 | §5 |
| M3U playlists | Build the CUE-modelled parser overlay ourselves; EchoList's metadata playlists are a stopgap, RECHO's internal .m3u a design reference. | Our library_m3u.md design | §2.3 |
| Library sorting / navigation | Adapt nanitecfw's proven stock-patch approach (library speed + views) and our sort-key-builder patch; RECHO's faster FS + logical sorting as the standalone benchmark. | nanitecfw; our module 39 patch points | §2.2 |
| Battery profiles | Bundle the already-pinned SAVEINFO fields ourselves; echo-mini-newfw's settings set and RECHO's clock scaling define the feature shape. | Our feasibility §6; newfw/RECHO designs | §2.1 |
| Control remapping | Producer-side patch ourselves; RECHO's pocket-control bindings are the behaviour reference. | Our GetKeyMask patch point | §2.1, §5 |
| Standalone firmware | Port an existing RKnanoD standalone to the Neo (echo-mini-newfw, MIT, cleanest license and newest study; or ReChord/EchoPod, GPL-3.0) rather than starting from Rockbox or from zero. NeoPod already proves the Neo side of this route. | berettavexee/echo-mini-newfw; brnomt/ReChord | §2.1, §3 |
| Bonus: audio quality bug | Test whether the Neo's stock Vorbis module is the SDK's low-precision build; if so, port echo-mini-opus's full-precision Tremor replacement, a validated patch on the sibling device. | berettavexee/echo-mini-opus | §2.2, §2.5 |

*Survey compiled from GitHub API metadata and READMEs, the RECHO
site, Rockbox target lists/source tree, and web search, 2026-10-31.
"Verified" means the artifact itself was opened during the survey;
activity dates are last-push dates from the GitHub API.*
