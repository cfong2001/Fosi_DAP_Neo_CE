# DAP Neo CE release images

This directory holds the current CE images, rebuilt from source and checked
against their pins by `.github/workflows/firmware.yml` on every change.

| File | What it is | Length | SHA-256 |
|---|---|---|---|
| `DP3_V137_CE.img` | **Standard.** Every composed CE feature (list below). Header date 2026-10-23. | 13,639,684 bytes (8,192 more than stock) | `8f710fd19975e2e2ddfc43e0624e9247a349ff4810c9aa3f00aadc2662bacc19` |
| `DP3_V137_CE_minimal.img` | **Minimal option.** The default framework set and full-precision Vorbis only. Header date 2026-10-23. | 13,631,492 bytes (same as stock) | `43476a08ace9e4fbf942bfcab2bbd5eea2e3554ac7a7c7cf60f9770d29700565` |
| `DP3_V137_CE_recovery.img` | Unmodified stock bytes dated 2026-10-24, one day after either CE image, so the boot validator prefers it. | 13,631,492 bytes | `aff851b31d6eee55cbd4bb3fc0464ac79f0039ee86ae6723225ac036a157d223` |
| `*.report.json` | Build reports: every patch with its address and old and new bytes, transplant hashes, validation results. The standard report summarises its byte ranges. | | |
| `SHA256SUMS` | Hashes of the three images. | | |
| `DP3_V132_device_recovery.img` | Stock V1.3.2 rebuilt from the qualified unit's own slots (header date 2026-09-20). Restored over Rockusb on that unit; older than CE, so the stock installer would not select it. Not in `SHA256SUMS`; details in [`FIRST_DEVICE_QUALIFICATION.md`](FIRST_DEVICE_QUALIFICATION.md#sanitized-device-derived-recovery-image). | 13,631,492 bytes | `2e8167df18c6c49d0e734647f7169d986a373f97d4d77de66d649b10650db6af` |

See [FLASH_REVIEW.md](FLASH_REVIEW.md) for the current major-flaw review,
version-aware recovery preparation and device qualification procedure. The
bundled V137 recovery must not be assumed to supersede official V155.

## Hardware status

Standard CE has been flashed to a physical DAP Neo. Both measured 13 MiB
firmware regions matched a complete Rockusb readback before reset; the player
then booted, exposed its custom settings, displayed embedded album artwork and
played an MP3. Restoring the player's own stock firmware over Rockusb also
passed full readback and booted. Remaining format, USB-mode and endurance
checks are tracked in [`FIRST_DEVICE_QUALIFICATION.md`](FIRST_DEVICE_QUALIFICATION.md).

All of these hardware installs used Rockusb. The stock update path below
(copy `RKNANOFW.IMG`, run the update on the player) follows the traced
installer but has not yet been run with CE on hardware.

The content-route repaired Standard code also booted and played Opus music
on hardware on 2026-11-14. That test used the optional diagnostic readout
and a newer header date; both written slots passed full readback. On 2026-11-15, the current Standard code also passed embedded artwork, full-screen
theater color, progress-gap and continuous dial acceptance. Small black boxes in
the top status bar and residual background-fill staging remain follow-ups.

## Which image

Start with the standard image unless one of these applies, then use the
minimal one:

- **The standard image is 8,192 bytes longer than stock.** Its complete
  13 MiB transfer has been written to both measured slots, read back and
  booted on the qualified unit
  ([`analysis/slot_reclamation/report.md`](../analysis/slot_reclamation/report.md)).
  Its header mirror is padded onto a 512-byte sector boundary, which the
  boot validator requires. Standard images built before 2026-11-11 (pin
  `db0a11d2…` and earlier longer-than-stock pins) lacked that padding
  and should not be flashed.
  The minimal image is exactly stock length and remains available as the
  smaller feature set.
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
2. **Check the installed version.** The bundled recovery is V137 dated
   2026-10-24. If the player runs newer official firmware (V155 is dated
   2026-11-02), that recovery cannot replace it; prepare a matched pair with
   `tools/prepare_flash.py` first ([FLASH_REVIEW.md](FLASH_REVIEW.md#prepare-a-dated-pair-offline)).
3. **Back up your card.** Copy your music somewhere safe.
4. **Know your way back.** Keep `DP3_V137_CE_recovery.img` and the stock
   `DP3_V137.img` with you, and read the recovery section below first. If
   you may need Rockusb recovery, take a two-pass full backup with
   `tools/backup_stock.py` before installing; an update image is not a
   backup of your player.

## How the stock installer finds an update

From the traced installer (module 8, [`analysis/boot_slots.md`](../analysis/boot_slots.md)):

- It looks for `DP3_Vnnn.IMG` (nnn taken from the running firmware's
  version) first, then `RKNANOFW.IMG`. These are visible FAT 8.3 names;
  the firmware compares their raw directory forms without the dot.
  Keep the `.IMG` extension when saving or renaming the file.
- It checks the `RKnanoFW` marker and that the mirrored header matches,
  writes the image to firmware slot 2, then copies slot 2 over slot 1.
  **After a stock-path install both slots hold CE**; no stock copy remains
  on the device.

What opens the update screen (a menu item, or detection of the file at
boot) has not been traced. Use the same procedure Fosi provides for
official updates, with the CE file in place of the official one.

## Install (stock update path)

1. Rename `DP3_V137_CE.img` (or `DP3_V137_CE_minimal.img`) to
   `RKNANOFW.IMG` and copy it to the root of the storage the device updates
   from.
2. Run the update the way you would for an official Fosi update.
3. After the device restarts, **delete `RKNANOFW.IMG`** from the card.
   Leaving an update file in place can rerun the installer.
4. Test, in this order: boot to the menu, play an MP3, then a FLAC file.
   Then try APE and DSD128 if you have them (the unmeasured clock gate), an
   Ogg Vorbis file, two same-format tracks in a row (the next must start promptly), a
   track skip within one format, and a
   library rescan (natural sort). On the standard image also try an Opus
   file, a track with album art and one without (theater), the progress bar
   and continuous dial movement, an `.m3u` playlist with next and previous,
   the hold switch (lock screen), and a long press of Power (Bluetooth).

## Install (Rockusb, hardware-tested path)

This is how CE was installed on the qualified unit. Follow
[Repeating the qualified Rockusb procedure](FLASH_REVIEW.md#repeating-the-qualified-rockusb-procedure)
step by step. In short: take and compare a two-pass full backup, remove the
card, enter recovery (physical reset, then hold Vol+ + Vol- + OK while
reconnecting USB), write only the 13 MiB updater region of each slot,
compare a full readback of both slots, then unplug and use the physical
reset button. The slot addresses (LBA 0 and 30720) were measured on one
unit; confirm them against your own backup before writing.

Please report results, good or bad, as a GitHub issue with the image hash
and what you tested.

## Recovery

- **If the device still boots and can run an update:** install
  `DP3_V137_CE_recovery.img` the same way (renamed to `RKNANOFW.IMG`). It is
  stock code dated 2026-10-24, newer than either CE image, so the validator
  selects it. Plain `DP3_V137.img` is dated 2026-10-22; it is older than CE
  and the validator would keep booting CE.
- **If the device does not boot:** use the measured Rockusb procedure in
  [FLASH_REVIEW.md](FLASH_REVIEW.md#repeating-the-qualified-rockusb-procedure).
  Recovery entry on the qualified unit uses reset, then Vol+ + Vol- + OK while
  reconnecting USB and holding through verification. Both 13 MiB payloads were
  written and fully read back; the trailing slot-local data was preserved.
  Restoring the device-derived stock firmware also passed readback and boot.
  Another unit still requires its own backup and map verification.

After verification, unplug USB and use the physical reset button to start;
software reset alone was unreliable. If a dated candidate is newer than the
bundled recovery, prepare a matching recovery newer than that candidate first.
The stock installer replaces both slots; a separately retained stock fallback
slot is not part of this qualified procedure.

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
