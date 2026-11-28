# Official firmware V155 to V162: review and port disposition

Sources: Fosi's support page (https://support.fosiaudio.com/products/dapneo),
read 2026-11-28, and the four official images it links. Each image passes
its header mirror and Rockchip CRC check. Pins are in
`tools/official_images.py`. The images are not stored in this repository.

| Version | File | Header date | SHA-256 |
|---|---|---|---|
| V137 | `DP3_V137.IMG` | 2026-10-22 | `fcc1cd3e…6deef` |
| V155 | `DP3_V155.IMG` | 2026-11-02 | `4713a2eb…e1332` |
| V161 | `DAP Neo FW_V161.rar` holding `DP3_V161.IMG` | 2026-11-12 | `96e9216a…724ed` |
| V162 | `DAP Neo FW_V162.rar` holding `DP3_V162.IMG` | 2026-11-17 | `ff201296…77aa0` |

The RAR archives use RAR5 compression. `unar` extracts them; the 7-Zip
build in Ubuntu's `7zip` package does not.

## What Fosi changed

Release notes, with what the images show.

**V155.** Better FLAC compatibility, three media library slots for up to
20,000 tracks, a prompt before a library update, a manual Update Media
Library item, 60 or 120 volume steps, a power saving mode and a jog wheel
speed setting. Decoder modules 76, 77 and 78 changed. `v155_port_review.md`
traces the settings fields.

**V161.** A 12/24-hour time option, gapless playback for FLAC files at the
same sample rate, faster file reading, separate Bluetooth volume and other
fixes. The language tables gain a Gapless Playback item with On and Off
(Simplified Chinese string 181 onward) and a Time Format item with 12-hour
and 24-hour (strings 264 to 266). Every later string ID shifts. Module 33,
the decoder dispatcher, grows from 0x3b94 to 0x4b74 bytes.

**V162.** Fosi lists stability, memory card compatibility and other fixes.
The image differs from V161 in 28 bytes. Apart from the version, date and
CRC, the only change is three rows of the clock request table
(`clock_table.md`):

| Row | Use | Field | V161 | V162 |
|---|---|---|---:|---:|
| 1 | solver floor | A pclk | 96 MHz | 48 MHz |
| 3 | boot and init | PLL | 200 MHz | 240 MHz |
| 3 | boot and init | A core, A hclk | 96 MHz | 100 MHz |
| 3 | boot and init | B core, B bus | 0 | 240 MHz |
| 30 | library update | A pclk | 75 MHz | 100 MHz |

All 456 image resources, Font A, the codepage and the system defaults are
byte-identical from V137 to V162. Font B and the language tables differ.

## Installation path

Fosi's procedure for V155, V161 and V162 is the same. Copy the file to the
root of the internal **DAP Sys** drive, eject, power off with the orange side
button, and power on. The update screen starts by itself. All three images
keep the installer name templates `DP3_V100IMG` and `RKNANOFWIMG`, so CE's
`RKNANOFW.IMG` is still found. Because the versioned name is searched first,
the install steps now say to remove other `.IMG` files from DAP Sys.

## Disposition

Porting each Fosi feature into V137 would need a separate trace of
settings fields, menu layout and persistence (`v155_port_review.md`). This
review instead re-derives CE's patches against the newer images with
`tools/port_patches.py`, so a CE build on V162 keeps every Fosi change.
`patches/ported/<VERSION>/README.md` lists the evidence for each patch.

| CE change | V155 | V161 | V162 | Why |
|---|---|---|---|---|
| DAC error counter (0001, 0002) | ported | ported | ported | the newer `dac_write` changes only an unrelated SAVEINFO offset |
| I2C reset pulse (0019) | ported | ported | ported | delay routine unchanged, call relocated |
| Natural sort (0027 to 0031) | ported | ported | ported | the newer key builder adds a 0x2000-record cap after the hooked loop, which the hooks do not feed |
| Wheel timer period (0050) | ported | ported | ported | key init and timer setter unchanged |
| Full-precision Vorbis (module 75) | ported | ported | ported | module 75 is byte-identical |
| Clock table v1 (0003 to 0018) | conflict | ported | conflict | V155 grew the table to 37 rows; V162 changed the solver floor clock_v1 assumes |
| Gapless fast path (0020 to 0026, 0034) | conflict | conflict | conflict | V155 renumbered playback events; V161 rewrote the decoder start, stop and shutdown paths for its own FLAC gapless |

`build.py --base V162` builds the ported set: 10 patches plus the Vorbis
transplant, SHA-256 `27744c5fad59df0f4e613934ce8b7b7f8d608e9594b6d6ed330230dd15c04c7f`.
It passes `validate_grown()`. It is not in `release/` and has not run on
hardware.

## Open work

- Re-derive the clock table rows against V162's table, keeping Fosi's new
  row 3 and row 30 values. Measure decoder load before lowering any row.
- Decide whether CE's gapless fast path is still needed beside Fosi's FLAC
  gapless. CE covers every same-format change; Fosi covers FLAC at one
  sample rate. Porting it means re-tracing the V161 playback monitor.
- The standard image's theme runs target unchanged resources and may port
  with only a section-offset check. Its code patches, module growth and
  string patches (Power Profile) need the same evidence the porter
  collects, plus new string IDs from V161.
- A V162-based image needs a hardware boot, playback, library and recovery
  test before release.
