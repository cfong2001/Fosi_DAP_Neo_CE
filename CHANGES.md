# Changelog

## 2026-11-12: EQ preset names

- Each EQ preset slot takes an optional `name` (`--eq-presets` config and
  the builder's name fields). It replaces that item's menu string, records
  175 to 180, in all 21 languages, so the EQ menu and the settings value
  show it. A slot can carry a name without a curve.
- The browser builder now applies string patches (build.py's `string`
  kind), checked against each language's stock text and byte-identical to
  build.py. The example config names slot 6 "HD 600"; its builder pin is
  d247ed21….

## 2026-11-12: power profiles

- System Settings gains a Power Profile item (Standard image) with three
  options: High, Balanced and Battery Saver. Each sets brightness, auto
  screen off and auto power off through the settings window's own setters.
  Labels in all 21 menu languages.
- The settings menu tree is data: each string record starts with the SDK's
  `MENU_TEXT_INFO_STRUCT`. The new item and options are ids 266 to 269,
  past the stock table, so no stock string is touched. The two routines
  that look up records send those ids to a table in the padding after the
  image resources. Hooks in the settings window's value switch and commit
  handler mark the matching profile and apply the chosen one.
- 240 bytes of code in three dead module 0 routines (patches 0140 to 0146),
  64 theme runs. `test_profiles.py` runs the real lookups and settings
  code: stock text and headers are unchanged for all 266 ids in all 21
  languages.
- The first battery-profile design (clock caps, wheel timer, SAVEINFO area)
  stays unstacked: its clock caps went below Rockchip's figures and it had
  no settings item.

## 2026-11-12: theme code colours

- Themes can now change the accent and divider-line colours, which the
  firmware sets in code rather than in resources. A config's
  `code_colours` takes any of `accent_light`, `line_light`,
  `accent_dark` and `line_dark`. Each is a `movw r0` immediate in module 0
  loaded by both the palette routine and the clock painter; the build
  rewrites both, after decoding each site and checking it holds the stock
  value. The page builder applies it byte for byte the same (new test case
  b2), and the theme studio has controls for it.
- `verify.py` check 10 confines the example's diff to the eight sites and
  refuses an unknown role.

## 2026-11-12: focus mode in the standard image

- Focus mode joins the standard image: after five seconds without input
  the player hides its controls and enlarges the cover; the first key or
  wheel turn only wakes it.
- To make room, the playlist resolver hooks (216 B), the theater no-art
  exits (100 B) and the transport ground wrapper (52 B) moved out of the
  gap tail into module 0, into stock routines the census found nothing
  can reach (patches 0047 to 0049). The 340-byte focus payload takes
  their place at 0x0307C1DC; its twelve hooks are patches 0120 to 0131.
- Every full-build emulation suite passes with the hooks in their new
  homes, and `test_focus_mode.py` runs all four focus gates on the full
  image (new CI step).

## 2026-11-12: Font A redrawn

- Font A, the 6 x 12 font for status and small text, is redrawn from
  Barlow SemiBold at 11 px, matching the list font. Same generator
  (`generate_font.py a`), same firmware rules (letters measured over rows
  0 to 7, explicit tails for everything else). 314 theme runs; the merged
  theme has 1,583.

## 2026-11-12: gapless v3, warm start

- Stock zeroes the first three decoded buffers of every track and
  restores the volume on the fourth (the playback monitor at
  `0x03064F7E`, counter `0x0304AD84`; Rockchip's `AudioErrorFrameNum` in
  the SDK's `Service.c`), to hide a cold decoder's start-up output. That
  silence, about 78 ms for MP3 and up to about 279 ms for FLAC, was most
  of the audible gap. When the gate retains the decoder it is warm, so
  new patch 0034 has the gate's retained path set the counter to 3: the
  first buffer plays and the volume is restored at once.
- The transition rig now runs the real monitor after each transition: stock
  and every cold start zero three buffers, a warm start zeroes none
  (FLAC, MP3, APE). Skips and codec changes keep the stock behaviour.
- The SDK's decoder-core program (`Main2.c`) cycles file and decode
  open/close per file without a core restart, which is the design the
  fast path relies on; every decoder takes it cleanly in the rig.

## 2026-11-12: clock table v1 corrected against Rockchip's SDK

- Rows 18 and 19 were mislabelled. Running the firmware's own extension
  classifier under emulation makes `.APE` codec 5 and `.FLA` codec 6, and
  the module 33 switch sends 5 to row 18 and 6 to row 19. v1 had been
  running APE at 288 MHz while calling it FLAC.
  `analysis/clock_table.md` and `core1_loader_protocol.md` carry the
  corrected mapping.
- No decoder now runs below Rockchip's figure for its class
  (`PowerManager.c` in the RKNanoD SDK): APE, ALAC and DSD (400 MHz there)
  and the top Vorbis tier (260 MHz there, and CE runs a heavier
  full-precision decoder) keep stock's 480 MHz until their loads are
  measured. FLAC stays at 288 MHz, above the SDK's 220. Every other
  lowered row is above the SDK's figure too, and all rows sit inside the
  SDK solver's divider and bus limits.

## 2026-11-12: list and menu font, resident-space census

- Font B's Latin glyphs (lists, menus, titles; 314 records) are redrawn
  from Barlow SemiBold. They are still 1-bit, but with 2-pixel stems,
  even spacing and tabular digits. The redraw also fixes a stock layout
  bug: stock `L` advanced 2 px and overlapped the next letter.
  `patches/antialias/generate_font.py`, checked by `test_font.py`.
- `patches/space/`: a reachability census of module 0 finds 8,508 bytes
  of stock code in 150 pockets that nothing can reach. An emulation
  coverage gate over the Unicorn suites (now in CI) confirms that none
  of it executes. That is enough resident room for focus mode and text
  smoothing, pending a hardware tripwire build. The marquee still does
  not fit.
- The merged theme has 1,269 runs. New Standard pin `148446d9…`. Minimal
  and recovery are unchanged.

## 2026-11-11: sector-aligned header mirror (Standard image)

- Fixes a likely boot failure in the Standard image. The boot validator
  (module 1, `0x0307E2CA`) reads the header mirror at sector
  `(u32 @ 0x1F4) >> 9` and compares the whole sector with the primary
  header. The module 31 and 24 growths (6,962 bytes) had left the mirror
  at `0xC95B32`, 0x132 bytes into a sector, so that compare would fail
  on both slots. Byte-offset checks, ours and the updater's file read,
  passed, which is why nothing caught it.
- The insertion step (`insert_rebuild.align_mirror`, and `alignMirror`
  in the browser builder) now pads zeros before the mirror up to the
  next sector. The Standard image gains 206 bytes and its mirror moves
  to `0xC95C00`. The rounded transfer stays 13 MiB.
- `validate_grown` and the browser validator refuse an unaligned mirror
  or one past `0xCFBE00`, the last offset that keeps the 13 MiB transfer.
- New Standard pin `e72449d7…` (13,638,660 bytes). Minimal and recovery
  are stock length and were never affected.

## 2026-11-11: antialiased screens, dialogs and progress bar

- Baked antialiasing extends to the stored screen art
  (`patches/antialias/generate_screens.py`):
  - dialog card corners
  - the low-battery icon
  - "Powering off…" text
  - the CE splash mark (now generated)
  - the progress bar columns and knob
- Patch 0118 (full build) draws the progress knob through the keyed
  helper. Over a theater ground the stock knob sat in a dark square.
- The README renders and the site simulator draw the progress bar from
  the image's own resources at module 27's coordinates.
- `test_screens.py` checks the art in the Standard image and runs the
  keyed knob draw in emulation. Verify's CE mark check now derives its
  byte count from the runs.
- Baked text uses Barlow, the site's typeface (vendored in `docs/fonts`),
  so the output is the same on every machine.
- New Standard pin `db0a11d2…`. Minimal and recovery are unchanged. The
  merged theme has 955 runs.

## 2026-11-11: antialiased status and browser icons

- The status and browser icon set (lock, play state, battery levels and
  charging frames, headphones, file, clock) now has baked antialiasing.
  These are drawn opaque, so edges blend exactly into each icon's own
  ground. Battery shells and terminals are rounded.
- Five stock two-colour keyed sprites are redrawn inside their stock
  footprints with antialiased edges: the black mini pause/play (189,
  190, 355, 356) and the light-theme speaker 298.
- Stock art that already had smooth edges is unchanged (large clock
  digits, Bluetooth, headphones 116, checkmarks, spinner, arrows,
  dots). So are the 7x9 pixel digits, which read best crisp.
- New Standard pin `7f496fae…`. The merged theme has 550 runs (browser
  300). The browser icon tests run without an unpacked tree.

## 2026-11-11: antialiased transport sprites

- The v4 transport sprites carry baked antialiasing. Edge pixels are
  pre-blended toward a neutral grey as bright as the theme ground, and
  fully outside pixels stay the transparent key. No draw code changed.
  The keyed-transport gates now check each sprite's own pixels.
- Mockups for antialiased text (`patches/antialias/`). Not built.
- New Standard pin `57d920af…`. Minimal and recovery are unchanged. The
  merged theme config has 494 runs.

## 2026-11-11: gapless v2 and the transition rig

- New transition rig (`patches/gapless/rig/`) runs the system core's real
  end-of-track and user-skip code under Unicorn with a virtual clock. It
  models the decoder core, CRU reset and clock state, module loads and DAC
  I2C. `test_transition.py` checks stock, the CE image and two mutants in
  about a second, and runs in the firmware workflow.
- The rig found that the first armed gapless release (Standard `9cc86655…`,
  Minimal `62321437…`) stalled for about 27 s on every same-format track
  change. The stock stop path holds core 1 in reset and gates its clock,
  and the v1 gate then skipped the reboot.
- Gapless v2: the decoder shutdown no longer halts core 1 on a natural end
  of track (0024). The gate also requires the core-1 running flag (0022,
  0023, 0025), so user skips, codec changes and other halts fall back to
  the full reload. The 80 ms delay cut is retired, because that delay runs
  after the I2S restart.
- 0019: the DAC bus I2C controller reset hold drops from 1 ms to 50 µs.
  Each track change makes seven DAC writes.
- Measured in the rig, from the end-of-track event to the I2S restart:
  stock 20.5 ms, CE 4.7 ms (FLAC to FLAC). Decoder-side open and decode are
  not included. Claims now say "shorter track changes", not "gapless".
- New release pins: Standard `63050146…`, Minimal `92c44606…`. Recovery is
  unchanged.

## 2026-11-10: site redesign with Stageshow

- The Pages site takes the look of Stageshow (github.com/benjitaylor/skills,
  MIT): the kit's neutral surfaces, three inks, one accent, its radii and
  shadows, in light and dark (`docs/theme.css`). Every existing function is
  unchanged: install flow, simulator, theme studio and builder.
- New pictures built with the Stageshow kit in `site/` (vendored in
  `site/src/kit/`, brand marks left out) and committed as `docs/stage/`:
  a hero demo of the install (the update file copied to the player and its
  SHA-256 read back) and a "What CE changes" bento of theater mode, the
  Vorbis gain, a fitted EQ curve, natural sort and the Bluetooth key. Each
  passes Stageshow's rehearsal gate at 1280 and 390, light and dark.
- CI rebuilds `docs/stage/` from `site/` and fails on any difference; a
  browser test mounts every picture in both color schemes. The page no
  longer widens when resized while scrolled away from the hero.

## 2026-11-10: builder without local scripts

- The builder page no longer asks for locally generated files. The
  Opus decoder data (`docs/builder-opus-data.mjs`, loaded only when a
  build needs it) and the Bluetooth-shortcut and lock-screen routines
  (`docs/builder-payloads.mjs`) are generated by
  `docs/generate_builder_data.py` and pinned by SHA-256. Section 1 can
  fetch the stock image from the repository.
- The lock-screen routine is now the reference-toolchain (GCC 13.2.1)
  build: 406 bytes, SHA-256 `9610d8d7…`, which passes every
  `emu_lock.py` gate. Framework reference for the standalone build:
  `53905b2e…`.
- Section 4 reorganised: sound settings (DAC filter, EQ presets,
  Bluetooth auto-off) first, then **All CE features** (reproduces the
  Standard image) or **Pick features**, a grouped checklist that starts
  as the Minimal image and disables combinations a picked build cannot
  make, with the reason. The disabled standalone playlist inputs are
  gone; playlists come with All CE features.
- `tests/builder.test.mjs` runs the Opus, everything, Bluetooth and
  lock-screen cases unconditionally (25 cases);
  `tests/site-comparison.test.cjs` builds the Standard and Minimal
  images in Chromium from the page.

## 2026-11-10: light play-mode icons keyed; theme colours in panel order

- Fixed: on CE with theater mode in the light theme, the play-mode
  icon showed as a white box. The light icons (resources 452 to 455)
  carried a white surround where the dark ones (286 to 289) carry the
  0xF800 key. `patches/design_refresh_v4/play_mode_light/` keys the
  border-connected white of each light icon (1,172 pixels; every white
  pixel in these icons is surround, so no glyph pixel changes). Both
  draw sites use the keyed helper, as the dark icons already require.
  The merged theme grows from 497 to 501 runs.
- New standard image `DP3_V137_CE.img`, SHA-256
  `9cc86655ddf23bddf72903b828e58f6b0a978836825e74c0f2a1a5056bdc98a3`
  (2,348 bytes differ from the previous one: the four icons and the
  CRC). The minimal and recovery images are unchanged. The browser
  everything build reproduces it byte for byte.
- Fixed: theme colours were written little-endian, so the panel, which
  shows stored bytes big-endian, would have shown them byte-swapped.
  `build.py` and the builder page now write the replacement colour
  big-endian; rule sources keep the studio's little-endian naming, so
  saved themes and presets keep their counts. The studio's previews
  now show pixels in panel order. Example-theme reference build:
  `5786e0db52ecd4b120f0035ed31c8454bae42b563c23d77418add6999591e17c`.

## 2026-11-10: simulator from real firmware pixels

- The site's screen comparison now draws real pixels: resources come
  from the stock image and the CE standard image (each resource section
  fetched by byte range and checked against a pinned SHA-256), and the
  status icon and transport row replay what each image's player painter
  draws, recorded under emulation by `tools/gen_sim_data.py`.
  `tests/sim-core.test.mjs` reproduces all 24 emulated framebuffers
  (both images, both themes, four transport states, default and
  theater grounds) word for word.
- Theater mode uses the firmware port's integer rule (top-third average,
  55% toward black or 75% toward paper, RGB565), checked against the
  Python port on synthetic art. Dark and light themes, the transport
  pages, no-media and boot-splash screens are selectable. Cover, text
  and progress bar remain approximations.
- Found by the simulator: in the light theme with theater on, the CE
  status icon (resource 452) keeps its white surround, because only
  0xF800 is keyed. The emulated painter shows the same.
- CI: `firmware.yml` regenerates the simulator data and fails on any
  difference; `ci.yml` runs the replay test.

## 2026-11-10: install flow on the site

- The Pages site (`docs/`) now opens on a three-step install: choose
  Standard, Minimal or Back to stock; copy it to the player or download
  it; run the update on the device. Copy to player (Chrome and Edge)
  writes the image to the player's USB storage as `RKNANOFWIMG` and reads
  it back. Every image is fetched from `release/` and refused unless its
  length and SHA-256 match the pins in `docs/install-data.mjs`. Nothing
  writes to the player's flash; the player's own installer does that.
- The theme studio and builder moved, unchanged, into a collapsed
  Advanced section. A build made there becomes a fourth install choice.
- `tests/install-data.test.mjs` (in CI) checks the pins against
  `release/SHA256SUMS` and the images. `tests/site-comparison.test.cjs`
  covers copy, download, a tampered image and the no-picker fallback.

## 2026-11-08: research record and README pass

- `research/external_sources_2026-11.md`: the second source survey with
  difficulty and reward scores, and an outcome table recording what each
  item became (#73 to #78) and why the rest were not done.
- README: the new build options in Building and the documentation index,
  quick device checks under Hardware status, and the open-items list
  brought up to date (the Bluetooth UART baud and the EQ machinery are
  closed).

## 2026-11-08: EQ presets (AutoEQ and custom)

- Decoded the stock EQ: a 31-band ISO third-octave graphic EQ, ±12 dB in
  1 dB steps, coefficients in module 35 for five sample rates, set up by
  module 36, presets in module 33. Stock presets use five bands, and the
  selector gives Classical, Bass Boost and Heavy Metal the Pop, Jazz and
  flat arrays.
- New `--eq-presets CONFIG.json` (`patches/eq_presets/`) fixes the
  selector and loads AutoEQ `GraphicEQ` files or custom curves into any
  of the six presets, fitted to the firmware's own band responses.
  Unconfigured presets keep exactly the curve stock applied. Published
  images are unchanged.
- The browser builder takes the same curves and gives byte-identical
  images. Not tested on a device.
## 2026-11-08: Bluetooth auto-off option

- Found why Bluetooth does not stay on: module 0's supervisor turns it
  off after 30,000 ticks (5 minutes at the 10 ms tick) with no device
  connected, and clears the saved setting. New `--bt-auto-off 10min`
  and `--bt-auto-off never` (`patches/bt_auto_off/`) lengthen or remove
  the limit; four bytes each. Published images are unchanged.
- The browser builder offers the choice, for the everything build too.
- `emu_supervisor.py` and `test_bt_auto_off.py` run the supervisor under
  Unicorn on every build; `verify.py` gains check 15. Not tested on a
  device.

## 2026-11-08: headphone unplug in stock

- `analysis/ui_controls.md` §1.7: GPIO0.13 is the headphone-jack sense
  line. Module 0 debounces it (0.5 s) and sets event flag `0x2B` on
  unplug; module 33 consumes the flag, sends playback command `0xE6` and
  redraws the play/pause glyph. So stock very likely pauses on unplug
  already, and the "pause on unplug" patch candidate is shelved until a
  device test says otherwise. Whether `0xE6` is pause is not decoded.
## 2026-11-08: Bluetooth UART settings verified in stock

- Closed the open "Bluetooth UART baud" item. Stock's Bluetooth power-on
  path configures UART1 (`0x400B0000`, pin group A, GPIO2.16/2.17) at
  115200 baud with divisor 13, the same controller and register sequence
  NeoPod v1.7.0 uses for Bluetooth audio on the Neo.
- New `tools/emu_bt_uart.py` runs the stock configure routine under
  Unicorn and checks the divisor latch and pin-group writes; CI runs it.
## 2026-11-08: RKNanoD reference manual

- New `analysis/rknanod_trm.md` records what Rockchip's public RKNanoD
  Technical Reference Manual (rev 1.0) settles for CE, with chapter
  references: the decoder core, HIFIACC and HIGHRAM share a power domain
  that only software turns off; SRAM clocks gate per 32 KB; the decoder
  code's low-address alias; the HIFIACC feature list, including a 300 MHz
  vendor figure for 192/24 APE; CRU divider, UART and I2C formulas; and
  the SAR-ADC's limits. Figure `media/rknanod_power_domains.png`.
- Cross-references added to the platform, power, clock-table, clock v1
  and harness documents. No code or image changes.
## 2026-11-08: DAC filter option

- New build option `--dac-filter` (`patches/dac_filter/`) selects one of
  the CS43198's four non-default interpolation filters. Stock's DAC init
  already chooses between all five from a settings byte that no menu
  sets; the option changes the default branch's immediate at
  `0x03051814`. One byte. Published images are unchanged.
- The browser builder offers the same choice as a menu, for the
  everything build too, and matches `build.py` byte for byte.
- `test_dac_filter.py` runs the firmware's filter selection under
  Unicorn for every build and settings value; `verify.py` gains check
  14. Not tested on a device.

## 2026-11-06: README lead and figures

- The README opens with what CE is, its hardware status and the three
  downloads, then shows each feature against stock before explaining it.
  A patch table marks which image carries each patch.
- `tools/render_readme.py` renders the figures in `media/` from the stock
  and standard images. Resource pixels are decoded from the images, the
  transport row and status icon come from the real player painter run
  under emulation, and theater grounds come from the ported firmware
  algorithm. Cover art and text are drawn and labelled as such.
- The outdated "Built but not enabled", "Design refresh" and "The CE
  interface" sections are replaced by "Variants and prototypes" and
  "Design history".

## 2026-11-06: everything build as the standard download

- `release/DP3_V137_CE.img` is now the everything build (`4d993e89…`).
  The former default ships as `release/DP3_V137_CE_minimal.img`
  (`62321437…`), the stock-length option. The recovery image is unchanged.
- `ci/build_release.sh` builds all three images by default
  (`--minimal-only` skips the compiler-dependent standard image), and
  `firmware.yml` checks all three against `release/` and attaches them to
  tagged releases. The standard image's published report summarises its
  byte ranges instead of listing about 11 MB of them.
- Repaired 48 Markdown files damaged by the curly-quote step of the unslop
  pass: a byte-level `sed` in a non-UTF-8 locale had broken characters such
  as "…", "→", "–" and "×", and turned each curly quote into three straight
  quotes. Each repaired file was checked against its pre-pass version.
- Space priorities recorded: the browser marquee ranks above focus mode,
  and playlists and the lock screen stay in the standard image.

## 2026-11-06: playlist, theater and transport fixes

Closed the defects the #57 review left open in the everything image, which
is now SHA-256 `4d993e89…` (64 patches).

- **Playlists.** The resolver hook now maps stock source 6's 1-based
  position to staged entry `position - 1` and returns a 1-based ordinal,
  with no hidden state. New hook sites make the count the playlist length
  (0043), route forward steps through stock's resolve-reset-advance path
  (0044), and keep the start and play-mode fetches in playlist positions
  (companion hook, whitelisted by return address). The five documented
  defects are fixed. `test_playlist_lifecycle.py` replaces the two audits
  that reproduced them.
- **Theater.** The player's two no-art exits restore the theme background
  (0045, 0046, `test_theater_noart.py`). The 676-byte portrait-sampling
  payload from #68 now fits in the tail at 0x0307C354.
- **Transport.** The eight v4 transport draws fill their rectangle with the
  ground before the keyed draw (0110 to 0117). Segment-only repaints leave
  no ghost pixels (`test_transport_ground.py`).
- **Focus mode** moved after the 676-byte standalone theater payload, to
  0x0307C258; its four gates pass.
- `firmware.yml` runs the new suites and rebuilds the standalone theater and
  focus variants. `tests/builder.test.mjs` derives the everything build's
  patch list from its manifest.
- `ci/feature-evidence.json`, `patches/full/README.md`, the release guide
  and the top-level README describe the new state. Focus mode and the
  browser marquee still need space a shipped feature would give up; the
  options are in `patches/full/README.md`.

No image has been tested on hardware.

## 2026-11-06: integration and release workflow

Merged the three open pull requests into one tree and made the release
images reproducible from CI.

- **#57** (CE player, navigation and theater workstream), with the stacked
  work already merged into it (#60 to #62, #64 to #67): merged unchanged.
- **#63** (playlist filename hardening): the hardened bridge is now built
  into the everything image. The module 31 payload grew from 6,800 to 6,936
  bytes (`010197e6…`); patches 0033, 0060 and 0061 were regenerated, and the
  image pin moved from `58f19e5d…` to `c7b8c490…`. The old pin was rebuilt
  from its own branch first and reproduced exactly. The lifecycle defects
  #63 documents are still open.
- **#68** (theater portrait sampling): landed in the standalone theater
  variant (payload 642 to 676 bytes, `96931a93…`). Focus mode, which sits
  after theater in the tail, was rebased to 0x0307C258 and passes its four
  gates. The everything build keeps the 642-byte payload because its tail
  has 4 bytes spare; see `patches/full/README.md`.
- The committed `patches/full/out/theme-full*.json` were stale (241 runs);
  they now match the build (497 runs).
- New `release/` directory with the recommended image (`62321437…`), the
  recovery image (`aff851b3…`), the build report, checksums and an install
  and recovery guide.
- New `ci/fetch_decoder_inputs.sh` and `ci/build_release.sh`, and the
  `firmware.yml` workflow: full `verify.py` (13 of 13), pinned release
  builds, a byte comparison against `release/`, the everything build's
  emulation suites, artifacts, and prereleases on `v*` tags.
- Added `.gitignore` for bytecode and generated build outputs.

No image has been tested on hardware.

## 2026-10-31: CE documentation redraft

Prepared 2026-10-31 against main at 9d810e90. Files written as complete
replacements; nothing in the live tree was modified and nothing was
pushed. Sources read at that revision: `README.md`,
`patches/framework/README.md`, `patches/framework/patches/manifest.txt`,
`patches/framework/patches/transplants.txt` (via the patches directory
listing and the framework README), `patches/framework/space_budget.md`,
`patches/theme_editor/README.md`, `patches/power/power.md`, the
`patches/` and `research/` directory listings, and the feature build
documents under `patches/m3u/`, `patches/ui_features/`, and
`patches/power/build/` as staged for their merge PRs.

### README.md (repository root)

- Title and opening rewritten around the name CE (Community Edition):
  what CE is (the stock image plus a defined patch set, produced by the
  framework), what it is not (not a from-scratch firmware), the base
  image name, size, and SHA-256, and the not-affiliated line, all in
  the first screen.
- New **Hardware status** section near the top: no image has been
  flashed, all results are offline, and the five hardware-phase checks
  are named in queue order (Rockusb slot read-back, the APE and DSD128
  clock gate, the gap tail canary, the module 31 window-cycle soak,
  system-side gapless observation).
- "What is in the build" became **What CE changes**: the same table,
  updated to current evidence. The Vorbis row now carries the corpus
  numbers (stock 38.1 to 42.1 dB; transplant 79.1 to 91.4 dB, median
  81.2 dB; arithmetic 102 to 123 dB; the 16-bit ceiling 85.1 to 97.4 dB)
  alongside the single-file figures (45.1 and 85.5 dB), and the
  rounding fix has its own row. The gapless row states that patch 0026
  arms the path and gives the fixed saving (85 ms per transition plus
  the unmeasured copy and reset time). The default image's SHA-256,
  length, and diff accounting are stated above the table, and the
  manifest count (32, including the no-op fixture 0000) is stated
  plainly.
- "Built but not in the image yet" became **Built but not enabled** and
  was rewritten to current status: the Bluetooth shortcut, M3U support,
  the lock-screen routine, and battery profiles are built and
  offline-tested, held out of the default build by named gates (tail
  canary, window-cycle soak, the unauthored settings item record with
  item id 0xC5 as a working value). The previous text described the
  M3U bridge and both UI features as design-stage, which later merges
  superseded. Theme configuration and the CE splash mark are listed
  here as in progress, with the theme's build-time-only decision and
  its space reason stated.
- **Safety and recovery** kept, with the validator rule, the slot
  layout, the stock update flow prohibition, and the recovery image
  behaviour each stated in one place and cited to `analysis/boot_slots.md`
  and `analysis/flash_security_and_port.md` and the framework README's
  date discipline section.
- **Building** shortened to the framework's mechanics (SHA gate,
  manifest order, transplant disjointness, date stamp, report, the
  `--grow` and `--tail` steps, `--recovery`, the nine verify checks)
  with the pointer to `patches/framework/README.md` for commands. The
  withdrawn gap-base warning is kept, shortened.
- **Documentation** index kept with the same structure; entries added
  for `analysis/resident_home/resident_home.md`, the M3U bridge
  completion document, `patches/power/power.md` and its build folder,
  `patches/ui_features/ui_features.md`, `patches/theme_editor/README.md`,
  the harness milestone 2 document, and `tools/ui_theme.py` in the
  Tools paragraph. One-line descriptions for the M3U and UI entries
  were updated to built status.
- **Project status and open questions** rewritten to match: armed
  gapless instead of disarmed, the built-but-not-enabled set named,
  theme and splash listed as open items, and the documentation damage
  paragraph retained unchanged in substance.
- The not-affiliated line also appears under **Credits and licenses**.
  License content is unchanged: Tremor BSD-style, the transplant
  surgery BSD-3-Clause, nanitecfw MIT as the technique source, the
  SDK proprietary and reference-only.

### patches__framework__README.md (for patches/framework/README.md)

- Opening now names CE once ("every Fosi DAP Neo CE (Community
  Edition) patch"). The rest of the document was already a technical
  build manual and is carried over with two factual corrections:
  the unified-build paragraph called the gapless fast path "disarmed"
  and omitted the wheel timer patch; it now says armed and lists all
  six components including the 0000 fixture, with the manifest count
  stated as 32.
- Typographic normalizations inside carried-over text: an em dash
  in the patch-format example became a colon, an en dash in a CRC
  offset range became "to", and a Unicode minus sign in the diff
  accounting was spelled out. No technical content changed by these.

### patches__theme_editor__README.md (for patches/theme_editor/README.md)

- Rewritten around the verified state. The editor page (`docs/`),
  the catalog tool (`tools/ui_theme.py`), the export format, the
  456-record resource census, the blocked color values, and the
  empty `APPROVED_LITERAL_SITES` registry are all stated as before.
- The build section was replaced: the previous text presented
  `build.py --theme-config` and a verify.py theme check as existing.
  They do not exist at this revision (see disagreements). The new
  section states what the missing build step has to do and that, until
  it lands, the exported theme JSON has no consumer in the framework.
- The Pages hosting paragraph was rewritten to what the tree proves:
  `.github/workflows/pages.yml` is a real `Publish theme studio`
  workflow that deploys `docs/` on pushes to main and skips if the
  page is absent (contents read in this pass). Whether it has ever
  completed a deployment is not recorded in the tree, and the
  paragraph no longer claims a live site.
- The original's line that the theme stage runs after the "disarmed
  gapless hooks" was removed with the rest of that paragraph; the
  gapless path is armed in the current manifest.

### Checked and left untouched

- `research/README.md`: its first screen describes the research folder
  and its method, not the project as a whole. No CE framing change
  needed.
- All deep analysis and feature documents: out of scope per the brief.
  Several carry stale status lines of their own (for example
  `patches/power/power.md` still says the battery apply routine is
  "designed here, not built" and that patch 0050 "is not stacked";
  the PR 31 build document and the manifest supersede both). Flagged
  here rather than edited.

### Disagreements found between sources

1. **Theme build integration.** `patches/theme_editor/README.md`
   describes `build.py --theme-config`, overlap refusal for theme
   rules, and an extra color-patch check in `verify.py`. The shipped
   `patches/framework/build.py` at 9d810e90 contains no theme code at
   all (full-text read), and `verify.py` contains no theme or color
   check. The framework README is also silent on any theme step. The
   redrafts follow `build.py` and `verify.py`: the editor exists, the
   build integration does not. This is also the gap behind the user's
   "you removed the theme generator" report; from the documents alone
   it cannot be determined whether the integration was removed or
   never landed.
2. **Gapless arming.** `patches/framework/README.md` ("the disarmed
   gapless fast path") and `patches/theme_editor/README.md`
   ("disarmed gapless hooks") disagree with `manifest.txt`, which
   lists `0026-gapless-arm.patch`, and with the root README's table.
   The redrafts follow the manifest: armed.
3. **Default build contents.** The framework README's component list
   omitted patch 0050 (wheel timer period), which the manifest lists.
   The redraft lists it.
4. **Stock image distribution.** The previous root README said "The
   stock image is not distributed here." The repository root at
   9d810e90 contains `DP3_V137.img` at 13,631,492 bytes. The redraft
   states that a copy is in the repository root.
5. **Built-but-not-enabled status in the previous root README.** It
   described the M3U bridge as "designed, not built", the lock-screen
   and Bluetooth work as "fully designed, neither built yet", and the
   M3U placement question as open. The later merge documents
   (`space_budget.md`, the module 31 composition document, the tail
   build document, the power build document) show all four built.
   The redraft follows the later documents.
6. **Two live copies of patch 0040.** `patches/framework/patches/0040-m3u-browser-hook.patch`
   is the earlier variant: its gate text targets the module 0
   extension at exec 0x03079C14 (the placement the census withdrew)
   and its replace bytes are `fbf77bbe`. The current variant, in
   `patches/m3u/compose/patches/`, targets the module 31 extension
   trampoline at 0x0307EE48. Same patch name and site, different
   bytes and gate. The root README redraft warns about the stale copy
   in one sentence. Which copy a future stacking should use is a
   coordinator decision; this note flags it and does not resolve it.
7. **Battery profiles design vs build.** `patches/power/power.md`
   (the design document) says the apply routine is not built and
   recommends stacking 0050 with the feature; 0050 is already in the
   manifest, and the build document records the blob built and
   emulation at 32 of 32. The redraft follows the build document.

### Facts not verified in this pass

- `.github/workflows/pages.yml` contents were read in this pass: it
  deploys `docs/` to GitHub Pages on pushes to main touching `docs/`
  and skips cleanly when `docs/index.html` is absent. Whether it has
  ever completed a deployment is not recorded in the tree, and the
  redrafts do not claim a live Pages site. `ci.yml` was not read.
- The theme editor page's runtime behaviour (SHA check in the browser,
  record reading, mock screens) is stated from
  `patches/theme_editor/README.md` and the presence of `docs/index.html`,
  `docs/theme.js`, `docs/theme.css`, `docs/theme-core.mjs`,
  `tools/ui_theme.py`, `patches/theme_editor/test_theme.py`, and
  `patches/theme_editor/test_browser.mjs`. The page was not executed.
- The example theme counts in `theme.example.json` (6,060, 4,668,
  3,276, 1,884, 492) are carried from the theme editor README; they
  were not recomputed against the image in this pass.
- Rockusb read-back sector numbers appear in project working notes
  but were not re-verified against a repository document in this
  pass, so the redrafts name the read-back task without sector
  numbers.
- No `research/feature_matrix.md` or other roadmap file exists in the
  tree (the `research/` folder holds five documents, listed in the
  README index). Status and roadmap statements were taken from the
  root README, the framework documents, and the feature build
  documents instead.
- The CE splash mark's target resource and byte cost are not stated
  anywhere in the tree yet (the census is in progress in a parallel
  workstream), so the redrafts describe the mark only as in progress,
  with no format or size claims.

### Addendum at merge (2026-11-01)

This redraft was merged after three further changes landed, and the
merged files were reconciled against them:

- The theme build step the redraft recorded as missing has landed
  (the `--theme-config` consumer and verify check 10), and the CE
  splash mark ships as `patches/theme_editor/ce-mark.json`. The
  theme sections of the merged READMEs describe the landed state;
  the colour census is complete, and its open endianness question
  is recorded in the theme editor README.
- The opt-in Opus variant build has merged (verify check 11); the
  root README names it as merged but not in the default build.
- verify.py runs eleven checks; the counts in the merged READMEs
  say so.

The sections above remain the record of the redraft as prepared
against 9d810e90.

### Addendum: documentation sync (2026-11-01)

This sync reconciles the README set with the merges that landed
after the redraft:

- The CE builder page has merged: the `docs/` theme studio now
  carries feature toggles, theme application, a CE mark toggle,
  and a gated-features list, and patches a user's own stock image
  client-side under the SHA gate. The root README's Building
  section names it as a browser front end to the same build, with
  the byte-equality proof in `tests/builder.test.mjs` and the
  unverified Pages deployment stated plainly. Project status
  moves the builder from the open list to the merged list; the
  theme follow-through item keeps only the literal-site registry
  decision.
- The stale framework copy of patch 0040 has been deleted. The
  root README's M3U note no longer warns about two copies; it
  states that the current variant lives in
  `patches/m3u/compose/patches/`.
- The design refresh v2 and v3 document sets have merged and are
  now in the root README's Documentation index, with the
  opus_swap README indexed beside them. Project status records
  both design sets as merged; the open list records theater mode
  as designed but not built, with its two named pre-build steps
  (the module 19 cover-handler emulation and the RAM census for
  the 3-byte placement), and records that the v2 and v3 icon
  binaries are local-only with the release-zip route.
- The CE splash mark wording is reconciled: the mark is landed
  as a theme-config runs config, applied on request, and is not
  part of the default build.
- The root README gains a short bullet list of the main patches
  in What CE changes, and a Design refresh section embedding the
  four design sheets (stock against v2, v2 against v3, theater
  mode, the v3 set at native size). The images are hosted on the
  design-refresh-v3 release, which also carries the v3 icon
  binaries; the repository push path cannot carry binaries.
- The theme editor README's opening Status paragraph is
  corrected to the landed state: the `--theme-config` consumer
  and verify check 10 exist, the CE mark ships as a runs config,
  literal sites remain refused, and the endianness question
  stays open for the hardware phase. The paragraph previously
  said the build step was not landed, contradicting the same
  file's build consumer section.
