# Feature feasibility: what it would take to extend the DAP Neo

Verdicts for the six requested features, each grounded in the traced stock
architecture of DP3_V137. Detail lives in the linked analysis documents;
this page is the summary a porter (custom patch or Rockbox) should read
first. Difficulty scale: **string/resource patch** (data only) <
**code patch** (modify an existing overlay/module-0 function) <
**new overlay logic** (new code in a free overlay window) <
**new subsystem** (structural additions).

## 1. Gapless playback: code patch, well-scoped

Full trace: `gapless.md`.

- The DAC is not the per-track problem: its power/configure sequence
  (181 ms of staged delays + ~50 I2C writes) is guarded by the byte at
  `[0x03023125]` and runs once per playback session. It re-runs only after
  a full stop/close, which the natural track-advance path never calls.
  **Proven.**
- The gap is structural: nothing pre-opens the next track. End-of-track
  (event `0xec` in module 33's playback task) starts a fully sequential
  pipeline (type probe, file open + metadata preparse on the decoder
  core, decoder (re)initialisation) plus per-open fixed costs that run
  even on the fast path: a fixed `delay_ms(100)` in codec open and a
  position-sync polling loop (15 ms polls, up to 200 iterations).
- A same-codec fast path is the biggest single win, and Phase 2 proved
  it does not exist in stock: the decoder image is fully re-copied
  (code + data, BSS zeroed) and core 1 reset on every codec open,
  including same-codec track changes. There is no loaded-codec cache
  check anywhere in the chain (`core1_loader_protocol.md` §0–§2; the
  loader is `0x0306777A`, flags 7 = code+data+BSS). Every transition
  pays the 33-117 KB copy plus the boot handshake. The fast path must
  be added by the patch: retain the requested codec id and skip the
  load/reset when it matches the resident one.
- Design that fits: precompute the next index during playback
  (repeat/mode logic is cheap state reads), pre-open/pre-parse the next
  file into a shadow file-info struct in the current track's last
  seconds, flip it in at the EOF event, re-arm DMA channel 5. Crossfade
  is not achievable in this architecture (one decoder window, one
  DMA feed, no mixer).

## 2. Better lock-screen information: code patch (moderate)

Full analysis: `ui_controls.md`.

- Hold state is SAVEINFO byte +0x60 at `0x030232A0`; unlock is a wheel
  gesture ('Rotate to Unlock', string 121). The stock "lock screen" is
  not a separate window: each applet overlays a small lock badge on its
  own screen, plus the unlock hint. No title/artist/time is drawn today.
- The key discovery: when hold engages during playback, the
  now-playing applet already snapshots the current track. The
  256-byte track name buffer and the track index are copied to shared
  globals (`0x030235CE` / `0x030235C0`) precisely so something else can
  display them. A lock display that reads those globals needs no new
  plumbing for the title.
- Playback position is available from resident module-0 getters
  (`0x0306316E` / `0x0306314A`) that applets already call from their
  paint code; a lock display can call them the same way.
- The one real gap is artist: it is not in the snapshot. Extending
  the snapshot copy in module 31 (an ~8-instruction loop) or reading the
  player's ID3 state at draw time closes it. Phase 2 closed the
  Display-isolation question: there is no dedicated lock window.
  The locked UI is a shared status painter linked into module 0 and
  each overlay, and its hold segment (or module 31's Display at
  `0x0307ED40`) is the hook point (`saveinfo_and_lock.md` §2).

## 3. Customizable physical controls: new overlay logic (hard); one cheap subset

Full analysis: `ui_controls.md`.

- Input production is fully mapped. `GetKeyMask` (`0x030617A0`) yields:
  power = GPIO2.5 (mask 0x0001), OK/center = GPIO2.14 (mask 0x4000),
  Vol+ = ADC ladder < 50 (mask 0x0010), Vol- = ADC ladder 100-199
  (mask 0x0020). A state machine builds event words
  `(type << 28) | mask` with types for debounced press, long-press
  (20 ticks), repeat (every 4 ticks), short release, long release. The
  wheel (GPIO2.12/2.13 quadrature) produces polled counters, not
  events. Holding power > 100 ticks posts the power-off request.
- There is no key-map table. Each window's Key callback is a
  hand-written switch over raw event words; delivery is direct. A data
  patch cannot remap anything.
- Cheap subset (code patch): translate masks in the producer
  (`GetKeyMask` or the state machine) before any window sees them.
  Small and global, but it remaps everywhere including menus, and
  cannot express per-screen or new long-press bindings.
- Full remapping (new logic): a persistent table. Phase 2 traced the
  SAVEINFO save path end-to-end (`saveinfo_and_lock.md` §1) and the
  answer is restrictive: fields in the record's unchecked gaps are
  not restored at boot, so a table placed there dies on the first
  save/load cycle. The home that works is the verbatim block
  +0x1C7..+0x2D5 (copied buffer→struct untouched at load), or a
  one-time patch to module 1's load pass. Still needed: an interception
  point in key delivery (not located) and a settings UI (module 32's
  string-ID-keyed item system can host one in principle).
- The Bluetooth shortcut is unblocked (Phase 2 correction). Round 1
  reported no callable BT toggle; that was wrong. The Bluetooth window
  is module 81; the power routine is window-linked (callable at
  `0x0307D1A8` with module 81 resident, `0x0307D1B6` with module 21
  resident; the settings window, module 32, carries its own copies).
  It drives GPIO2.7, runs the 'CV1' banner handshake, and records state
  in SAVEINFO +0x2D4, which sits inside the round-tripping block
  above, so BT state persists correctly. A shortcut must have the
  owning window loaded (or load it via `0x03067870`) and keep +0x2D4
  consistent; power-off is the GPIO-low sequence in module 21's 0x1BD
  handler. See `modules_round2.md` §3.
  **Scoping correction (2026-10-31, UI features workstream):** "callable"
  holds only inside the settings and Bluetooth window family. From the
  playback window the routine is not callable at all: its addresses are
  overlay addresses occupied by module 31's own bytes while playing,
  modules 21/81 are not resident, and loading one evicts the player. The
  workable design hooks module 0's resident key dispatcher
  (`0x03061B16`) and runs an inline replica of the toggle built from
  module-0-resident helpers. See `patches/ui_features/ui_features.md`
  section 1.6 and the Bluetooth design section.

## 4. M3U playlist support: new overlay logic, with a proven template

Full analysis: `library_m3u.md`.

- No playlist file format exists in stock firmware. Reproducible
  negative across ASCII/UTF-16LE/UTF-16BE searches of the whole image and
  all 21 language tables. No M3U/M3U8/PLS/XSPF/PLA parser, no extension
  entry, no string. "Playlists" are four fixed internal lists (A-D) plus
  one favourites list, stored as records in a raw-sector database on
  internal storage (device selector `0x00030001`), not as files.
- The hard constraint: playback does not reference tracks by path.
  The play context resolves a library record to a `(clus, index)` pair,
  starting cluster + directory-entry ordinal on the file's volume. An M3U
  entry is playable only after being resolved to a scanned file's pair.
- The extension gate is the first blocker and the easiest fix: `.m3u` is
  rejected by the dotless 3-char extension tables (module 0 data
  `0x030056be` + duplicates, module 31 `0x0307e110`, module 38
  `0x0307e6cc`). Adding `M3U` is a data patch at known addresses.
- Best implementation shape: a parser overlay modelled on the CUE
  parser (module 37), the one existing precedent for "text file →
  ordered sub-track list". Parse on open, resolve entries against the
  playlist's own folder/volume via the directory walk, load the play
  context directly. Preserves file order (the library lists would not;
  module 39 insertion-sorts everything by key) and needs no database
  writes.
- Open risks: cross-volume playlists (which record field disambiguates
  internal vs TF is unproven), UTF-8 names (no UTF-8 decoder identified;
  the firmware's conversion tables are legacy codepages feeding UTF-16),
  and unresolvable lines (file not in the library) having no
  representation.

## 5. Improved library navigation: code patch at known points

Full analysis: `library_m3u.md`.

- Sorting is insertion-at-scan-time in module 39. The record is 14 bytes:
  two u16 category fields, the first 4 sort-key chars inline (UTF-16,
  ASCII-uppercased when built), and an index to the full key string in
  the sector database. The comparator (`0x0307d620`) compares the two
  category fields, then the inline chars, then, on ties, reads both
  full strings from flash and compares up to 128 UTF-16 code units, raw.
  No natural sort ("Track 2" vs "Track 10"), no multi-key sort beyond
  the two category fields.
- "Better sorting" therefore means changing the key the scan builds.
  The builders at `0x0307d80a`/`0x0307d8c4` and the string-area writer
  are the patch points; the comparator can stay.
- "Faster browsing" is bounded by scan cost and per-tie flash reads, not
  by the UI; the lists are already indexed by the database.
- The database is stale by design: it rebuilds only on a manual *Update
  media library*. Files added to the card are invisible to library views
  (but visible in Folder browse) until then.
- "Clearer titles" is a tag-parse/display issue (modules 0 and 18),
  independent of the sort machinery. Redraw is bitmap blitting at fixed
  coordinates baked into resource names. Richer rows mean new bitmaps
  and new blit code, not a layout change.

## 6. Battery-saving profiles: code patch for a settings bundle; two components blocked/unproven

Evidence: `ui_controls.md` (settings record), `dac_audio_path.md` (DAC
power states), `power_and_features.md` (shutdown/WFI anchors).

What a profile could switch today, with proven mechanisms:

- Screen behavior: the settings already exist individually:
  Auto Screen Off (10 s-10 min / Always On, strings 188-195), Screen
  Brightness in 5 steps (20-100%, strings 196-201), Auto Power Off
  (Off / 5-20 min, strings 202-207), Sleep Timer (strings 208-214).
  All are SAVEINFO-backed menu settings. A profile is a bundle that
  writes several fields at once. Phase 2 pinned two more offsets via
  module 32's apply dispatch: brightness = +0x14 and the EQ
  selector = +0x68 (volume +0x12 and Channel Balance +0x2E8 were
  already proven); the screen-off offset is still among the record's
  unpinned enum fields.
- Backlight: GPIO2.4 is the backlight line (driven low = off in
  boot init, stock-verified). NeoPod's 10-step PWM duty table is
  not in the stock image (byte search: no match even for its first
  five values), so stock's exact duty mapping is unrecovered; the
  5-step UI above is the stock surface.
- DAC/headphone path: real power gates exist: the stop/close path
  runs a DAC power-down script (`0x03051736`) plus GPIO sequencing for
  mute/amp/reset/enable, and the CS43198 power register (map 0x020000)
  has individually releasable serial-port (0x40) and headphone (0x10)
  bits, exercised in that order by the stock release sequence. A
  profile that powers the DAC down when idle-with-no-playback is a
  policy change on existing machinery.
- Settings persistence: SAVEINFO is a 0x300-byte record in a raw
  partition of the internal store (device 3), dual-copy with SAVE/INFO
  magics and a checksum, loaded and clamped at boot by module 1. The
  save path is fully traced (`saveinfo_and_lock.md` §1): a profile
  field has a home only in the verbatim block +0x1C7..+0x2D5 (or
  via a load-pass patch); unchecked gaps do not survive.

What is blocked or unproven:

- Bluetooth: no longer blocked: the toggle routine and its state
  byte are identified (see §3), so a profile can switch BT by the same
  call a shortcut would use.
- CPU clocks / background activity: a WFI stub exists
  (`0x03055b70`) but its only traced caller is a peripheral-transfer
  wait, not an idle loop; no stock clock-scaling behavior was
  established from the binary. NeoPod's "96 MHz floor / 200 MHz
  screen-on" rule is uncited in its docs and unverified in stock.
  Battery claims for a profile should not include CPU savings until
  the scheduler/clock path is traced.
- Battery gauge: NeoPod's voltage-to-percent curve and its
  3450 mV shutdown figure are Echo-attributed and unverified in stock
  (`neopod_xref.md` B16/C11). The stock shutdown path is anchored
  (`0x03067c1c`), but its voltage thresholds were not recovered.

## Cross-cutting facts for any port

- Memory is the hard wall (datasheet figures, unverified on this
  board): ~960 KiB total SRAM across both cores. Any new subsystem,
  including a Rockbox port, shares that with the existing buffers
  (module 39 alone declares a 148,756-byte BSS arena for sorting;
  module 11's USB PCM ring is 36 KiB).
- Updates are unsigned (see `flash_security_and_port.md`): the
  traced installer/validator paths check magic, a header mirror, an
  unkeyed CRC-32 (polynomial `0x04c10db7`, init 0, no final XOR), and a
  user-editable BCD date. The offline patcher
  (`tools/firmware_patch.py`) already produces valid patched images.
  Boot ROM policy is not in this image and remains unproven either way.
- NeoPod already runs on this device and its board support is
  largely verified against stock bytes (`neopod_xref.md`: 8 of 10
  stock-cited claims full match, 1 match with a documented variance,
  1 partial; plus a list of Echo-Mini-inherited values that must not be
  trusted for the Neo). It is the fastest starting point for feature
  work; its gaps are equally documented there (notably: it does not use
  the internal eMMC at all, loading decoders from SD files instead).
- Storage is fully mapped (`storage_stack.md`): logical devices
  resolve through two dispatch layers to DW-MMC controllers at
  0x60020000 (drive 0) and 0x60030000 (drive 1, internal, holding the
  NANO partition info, firmware slots, the library database's device,
  and the user volume).
- The DAC path is fully mapped and executed (`dac_audio_path.md`,
  `tools/emu_dac.py`): CS43198 at I2C address byte 0x66 on I2C0
  (0x40040000, GPIO2.10/2.11), MAP frame format, a 73-entry static
  register table, and a hidden balance-style L/R trim inside the stock
  volume-write function that any reimplementation must reproduce or
  deliberately drop.
