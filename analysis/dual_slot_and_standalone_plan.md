# Dual-slot operation and the road to standalone firmware, Fosi DAP Neo (DP3_V137)

> **Correction:** Later instruction-level review found errors in the slot-scan, updater mirror-seek, and device-3 subdevice-offset descriptions. See [the slot capacity investigation](slot_reclamation/report.md) before relying on this document. Physical slot geometry and recovery behavior remain unverified.

Plan built on the Phase 2 mechanics in `boot_slots.md`,
`core1_loader_protocol.md`, `modules_round2.md`, and
`saveinfo_and_lock.md`. Everything labelled proven there is proven from
the image; this document's job is procedure and sequencing. Nothing here
has been run on hardware. No unit is available yet, and nothing has
ever been flashed.

---

## 1. Dual-slot operation (stock in slot 1, custom in slot 2)

### 1.1 Proposed selection behavior

The boot validator (module 1) selects the package to run by these rules
(proven, `boot_slots.md` §validator):

- Both slots hold **complete, independent firmware packages**. Every
  overlay load at runtime reads from the selected package (via the
  active-package pointer), so the slots never mix.
- Slot 1 (fw1) boots by default. Slot 2 (fw2) boots only if it
  validates (header magic + mirrored-header compare) **and** its packed
  BCD build date (header +0x000) is **strictly newer** than slot 1's,
  or if slot 1 is broken.
- The traced validator compares a plain date field; the outer CRC is
  unkeyed. Earlier-stage signature and anti-rollback behavior is unknown.

This suggests a possible dual-image arrangement, but does not establish
physical layout, early boot behavior, safe flashing or reliable fallback.

### 1.2 Fallback behaviour

- Fallback after an invalid slot-2 header is not established: the
  magic-mismatch scan bypasses the apparent iteration limit. Do not
  treat header corruption as a recovery procedure.
- A restore tool reports sector addresses 0 and 30720, but the mapping
  to the firmware device layer and recovery on this unit remain unproven.

### 1.3 The one hard rule

**Never let the stock update flow run on a dual-boot unit.** The
installer (module 8, reached only through the module 21 applet) writes
the new image to slot 2 and then copies it over slot 1; the slot-sync
function mirrors the booted image over the other slot. Either action
collapses the pair into two identical images and destroys the fallback.
Concretely:

- Keep `DP3_VnnnIMG` / `RKNANOFWIMG` update files off the user volume.
- Preferably, patch the update applet out of the custom image (or make
  its entry unreachable) so the flow cannot be triggered by accident.

### 1.4 Unproven geometry, resolve this first on real hardware

The restore tool's Rockusb addresses (slot 2 at LBA 30720) and the
validator's device-3-relative scan candidates (fw2 found around sector
0x6800 + n·0x800 for V137-sized images) are consistent **if** device-3
sector 0 in the firmware area equals Rockusb LBA 0, 30720 is exactly
the third scan candidate under that assumption. This is arithmetic
consistency, not proof: the image alone cannot show how Rockusb LBAs
map to the firmware's internal subdevice sectors.

**First hardware session, before writing anything:** read back sectors
0, 0x6800, 0x7000, and 0x7800 over Rockusb and compare the 512-byte
headers. That settles which LBA holds which slot's header on the real
unit.

---

## 2. Augment-first roadmap (patching the stock firmware)

Ordered by the Phase 1/2 feasibility verdicts, cheapest sound change
first. All patch production goes through `tools/firmware_patch.py`
(SHA-pinned input, mirrored header, CRC regenerated); every patch is
offline until a unit exists.

1. **Lock-screen information** (code patch in an overlay; moderate).
   There is no lock window to rewrite: hook the shared status painter's
   hold segment, or module 31's Display (0x0307ED40). Track name is
   already snapshotted at hold-engage (buffer 0x030235CE); position
   getters are resident (0x0306316E / 0x0306314A); artist requires
   extending module 31's snapshot copy loop. See
   `saveinfo_and_lock.md` §2.8.
2. **Persistent custom settings, placement rule.** A new field patched
   into SAVEINFO's unchecked gaps does **not** survive: the boot load
   restores only individually listed fields. Fields placed in the
   verbatim block **+0x1C7..+0x2D5** round-trip untouched (the Bluetooth
   state byte +0x2D4 already lives there). The alternative is a one-time
   patch to module 1's load pass. Any remap table or feature config
   should live in that block. See `saveinfo_and_lock.md` §1.6.
3. **Bluetooth shortcut** (unblocked in Phase 2). The power routine is
   window-linked, not resident: 0x0307D1A8 with module 81 resident,
   0x0307D1B6 with module 21 resident; the settings window (module 32)
   carries its own linked copies. A shortcut patch either loads the
   owning window via the segment loader (0x03067870) before calling, or
   reuses module 32's copy. State to keep consistent: SAVEINFO +0x2D4
   (1 = on; persists, per item 2). Power-off is the GPIO-low sequence in
   module 21's 0x1BD handler. See `modules_round2.md` §3.
4. **Fixed key remaps** (tiny patch, highest blast radius). Patch the
   producer, GetKeyMask at 0x030617A0 in module 0, global effect, no
   per-screen bindings. A configurable table belongs in the SAVEINFO
   verbatim block (item 2); full per-window remapping is new overlay
   logic and stays last.
5. **Gapless playback** (code patch; scope now closed). Phase 2 proved
   the per-track cost includes a **full decoder image re-copy and
   core-1 reset on every codec open, same codec included; there is no
   cache**. The patch set: (a) a same-codec fast path in module 33's
   load chain that skips the re-copy when the requested codec already
   resident (requires adding the retained-loaded-id state the stock
   code lacks); (b) pre-open of the next track into a shadow file-info
   struct during the current track's last seconds, flipped at the
   decode-finished event; (c) transitions must never route through
   stop/close, the DAC power sequence is per-session (proven), so a
   transition that avoids stop pays none of its ~181 ms; (d) true
   crossfade is not achievable (one decoder window, one DMA feed, no
   mixer). See `core1_loader_protocol.md` §0–§2 and `gapless.md`.
6. **M3U playlists** (new overlay logic on a proven template). Model
   the parser on the CUE parser (module 37); patch the audio-extension
   gate at its three copies to admit the playlist extension; resolve
   entries to the firmware's native (cluster, index) track references,
   it never references tracks by path. See `library_m3u.md`.
7. **Library sorting** (small patch). Natural-sort / case handling goes
   in the sort-key builders at 0x0307D80A / 0x0307D8C4 (module 39).

## 3. Standalone firmware, what stock proves a replacement must provide

A from-scratch image (Rockbox-class goal) has to satisfy contracts that
are now mapped end-to-end:

- **Package format:** `RKnanoFW` magic at +0x1F8, mirrored 512-byte
  header at the sector named by +0x1F4, module records at +0x208,
  load base 0x03050000, unkeyed CRC-32 (poly 0x04C10DB7, init 0)
  regenerated over the package. Tooling exists and is tested offline.
- **Storage:** internal storage on the DesignWare MMC controller at
  0x60030000 (channel 1), card-side controller at 0x60020000; the
  device-manager/vtable contracts and the NANO subdevice layout are in
  `storage_stack.md` and `boot_slots.md`.
- **Audio:** CS43198 on I2C0 (wire address 0x66), init tables dumped in
  `dac_init_table.txt`; PCM reaches the DAC via DMA channel 5 to the
  I2S TX register 0x40030024; the init/power sequences are in
  `dac_audio_path.md`.
- **Second core:** decoder programs load to 0x01000000 and talk to the
  system over the message unit at 0x40110000 (channel map, handshake,
  and the HifiFile RPC are in `core1_loader_protocol.md`). A standalone
  system can keep the stock decoder modules and the RPC contract, or
  replace both sides, it cannot replace one side silently.
- **Settings compatibility (optional):** SAVEINFO is a raw 0x300-byte
  struct at subdevice-1 sector 0x10 with mirrors at 0x40/0xC0, layout
  and save/load semantics in `saveinfo_and_lock.md`.

**Still unknown:** the boot ROM / first-stage contract before module 1
runs (who loads the validator, and from where). NeoPod, the open
custom firmware already running on this hardware via the Rockusb route
is the existence proof that a complete replacement image boots; its
approach is the reference when this stage starts.

**Development loop:** retain both images and do not rely on slot
fallback or a restore procedure until the exact device geometry and
recovery path have been independently tested.

## 4. Open items carried forward

- Slot geometry proof on hardware (§1.4) and the drive-0 = TF-card
  confirmation (inferred, not proven, in `storage_stack.md`).
- Boot ROM / first-stage behaviour before module 1.
- Who posts event flags 0x18B/0x18C (proven: no immediate-call poster
  exists in the image; setters likely in an earlier boot stage or a
  previous session, the flag bitmap lives in reset-preserved SRAM).
- The hold-engage write (SAVEINFO +0x60 = 1) and the wheel-unlock
  threshold check, both believed to be in module 0's input/dispatch
  region (0x03061936–0x03061E58); every applet writer only clears it.
- Decoder command-word case names (values 0–14), the HifiFileOpen send
  command (0x66 vs 0x68), and module 7's role.
