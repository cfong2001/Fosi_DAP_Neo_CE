# DAP Neo CE release images

This directory holds the current CE images, rebuilt from source and checked
against their pins by `.github/workflows/firmware.yml` on every change.

| File | What it is | Length | SHA-256 |
|---|---|---|---|
| `DP3_V137_CE.img` | **Standard.** Every composed CE feature (list below). Header date 2026-10-23. | 13,638,148 bytes (6,656 more than stock) | `69ee512a082338fb656e2730dcaa15c206e25ad47faf2d97bc64f2e5090d2140` |
| `DP3_V137_CE_minimal.img` | **Minimal option.** The default framework set and full-precision Vorbis only. Header date 2026-10-23. | 13,631,492 bytes (same as stock) | `0dfd10e23749f9b6c65499266f1a7a2ec038160b089ba0fc2ca68dcf2b24c986` |
| `DP3_V137_CE_recovery.img` | Unmodified stock bytes dated 2026-10-24, one day after either CE image, so the boot validator prefers it. | 13,631,492 bytes | `aff851b31d6eee55cbd4bb3fc0464ac79f0039ee86ae6723225ac036a157d223` |
| `*.report.json` | Build reports: every patch with its address and old and new bytes, transplant hashes, validation results. The standard report summarises its byte ranges. | | |
| `SHA256SUMS` | Hashes of the three images. | | |

## Not yet tested on hardware

No CE image has been flashed to a device. The images pass every offline
check this project has: SHA-gated builds, structural validation, the
15-check framework verifier, and Unicorn emulation of each changed code
path. None of that proves a device accepts, boots or plays them. You are
the first hardware test. Proceed only if you accept the risk of needing a
Rockusb (USB) recovery.

## Which image

Start with the standard image unless one of these applies, then use the
minimal one:

- **The standard image is 6,656 bytes longer than stock.** The installer
  computes a 13 MiB transfer from the header, and whether a longer image
  installs and boots correctly has not been tested
  ([`analysis/slot_reclamation/report.md`](../analysis/slot_reclamation/report.md)).
  Its header mirror is padded onto a 512-byte sector boundary, which the
  boot validator requires. Standard images built before 2026-11-11 (pin
  `db0a11d2…` and earlier longer-than-stock pins) lacked that padding
  and should not be flashed.
  The minimal image is exactly stock length, so it avoids that question.
  If the standard image does not install or boot, try the minimal one.
- **You play WMA files.** The standard image replaces the WMA decoder with
  Opus.

## What each image changes

Both images carry the default framework set:

- DAC error counter: counts consecutive I2C failures, so two transient
  errors no longer freeze volume and DAC control for the session.
- Clock table v1: decoder clocks lowered for MP3, WMA, AAC, WAV, FLAC and
  the lower Vorbis tiers. APE, ALAC, DSD and the top Vorbis tier keep
  stock clocks, at or above what Rockchip's SDK uses for them.
- Full-precision Vorbis with round-to-nearest output (about 40 dB better
  SNR than stock in emulation).
- Shorter track changes between files of the same format (decoder stays
  loaded; see patches/gapless/).
- Natural sort: case and accent folding, a leading "The " ignored,
  numbers compared as numbers.
- Wheel timer period 400 to 1000 µs, fewer wakeups.

The standard image adds:

- Opus playback in place of WMA.
- The CE design refresh: bare transport glyphs drawn over the background,
  redrawn browser status icons, and the CE splash mark.
- Baked antialiasing in the icons, dialog cards, low-battery and power-off
  screens and the progress bar; the progress knob sits on the theater
  background without a square.
- The list and menu font's Latin glyphs redrawn from Barlow SemiBold
  (still 1-bit), which also fixes stock `L` overlapping the next letter.
- Theater mode: the player background derives from the album art.
- M3U playlists: select an `.m3u` or `.m3u8` file in the browser to play
  it. Up to 150 entries from up to 32 folders; next, previous, wrap and
  shuffle stay in the playlist.
- Lock-screen track title and elapsed and total time.
- A long press of Power toggles Bluetooth.
- Safer track-title handling.

Details and evidence: [`patches/full/README.md`](../patches/full/README.md)
and the [README](../README.md#features). Focus mode and the browser
marquee remain separate variants. Focus mode could use the module 0 pockets
the dead-code census found ([`patches/space/`](../patches/space/README.md))
once a hardware tripwire build clears them; the marquee does not fit
without removing playlists and the lock screen.

## Before you install

1. **Check the hash.** `sha256sum -c SHA256SUMS` in this directory.
   Never install an image whose hash does not match.
2. **Back up your card.** Copy your music somewhere safe.
3. **Know your way back.** Keep `DP3_V137_CE_recovery.img` and the stock
   `DP3_V137.img` with you, and read the recovery section below first.

## How the stock installer finds an update

From the traced installer (module 8, [`analysis/boot_slots.md`](../analysis/boot_slots.md)):

- It looks for a file in storage named `DP3_Vnnn` + `IMG` (nnn taken from
  the running firmware's version) first, then the generic name
  `RKNANOFWIMG`. Both names have **no dot and no extension**.
- It checks the `RKnanoFW` marker and that the mirrored header matches,
  writes the image to firmware slot 2, then copies slot 2 over slot 1.
  **After a stock-path install both slots hold CE**; no stock copy remains
  on the device.

What opens the update screen (a menu item, or detection of the file at
boot) has not been traced. Use the same procedure Fosi provides for
official updates, with the CE file in place of the official one.

## Install (stock update path)

1. Rename `DP3_V137_CE.img` (or `DP3_V137_CE_minimal.img`) to
   `RKNANOFWIMG` and copy it to the root of the storage the device updates
   from.
2. Run the update the way you would for an official Fosi update.
3. After the device restarts, **delete `RKNANOFWIMG`** from the card.
   Leaving an update file in place can rerun the installer.
4. Test, in this order: boot to the menu, play an MP3, then a FLAC file.
   Then try APE and DSD128 if you have them (the unmeasured clock gate), an
   Ogg Vorbis file, two same-format tracks in a row (the next must start promptly), a
   track skip within one format, and a
   library rescan (natural sort). On the standard image also try an Opus
   file, a track with album art and one without (theater), an `.m3u`
   playlist with next and previous, the hold switch (lock screen), and a
   long press of Power (Bluetooth).

Please report results, good or bad, as a GitHub issue with the image hash
and what you tested.

## Recovery

- **If the device still boots and can run an update:** install
  `DP3_V137_CE_recovery.img` the same way (renamed to `RKNANOFWIMG`). It is
  stock code dated 2026-10-24, newer than either CE image, so the validator
  selects it. Plain `DP3_V137.img` is dated 2026-10-22; it is older than CE
  and the validator would keep booting CE.
- **If the device does not boot:** recovery needs the Rockchip USB
  (Rockusb) path. The mapping between Rockusb addresses and the validator's
  slot sectors is **not yet proven** (README, Safety and recovery). Read
  back before you write anything.

The planned dual-slot layout, with stock kept in slot 1 as a software
fallback, needs Rockusb writes to slot 2 only. That procedure is not ready:
it depends on the same unproven sector mapping.

## Rebuild it yourself

```sh
python3 -m venv .venv
.venv/bin/pip install capstone==5.0.7 keystone-engine==0.9.2 unicorn==2.1.4
bash ci/install_reference_toolchain.sh "$PWD/.ce-arm"
PATH="$PWD/.ce-arm/usr/bin:$PATH" PYTHON=.venv/bin/python \
  bash ci/build_release.sh /path/to/new-dir
```

The script fetches the two hash-pinned decoder inputs, builds all three
images and refuses any output whose hash differs from its pin. The standard
image compiles CE payloads with the reference toolchain
([`ci/REFERENCE_BUILD.md`](../ci/REFERENCE_BUILD.md)). Without it, pass
`--minimal-only` to build the minimal and recovery images.
