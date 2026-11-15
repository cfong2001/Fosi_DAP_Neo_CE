**Standard CE is running on physical hardware.** A DAP Neo completed two
matching full-range backups, a full Rockusb write/readback of both 13 MiB
firmware regions, normal boot and custom-settings display. The current
Standard image also passed full-card scanning, Opus playback, embedded
covers, theater color, progress-gap and continuous dial acceptance.
Restoring that player's own stock firmware passed readback and boot. The
copy-a-file stock update path has not yet been run with CE on hardware.
Read the install and recovery guide in `release/README.md` before using any
file; remaining format, USB-mode and endurance checks are listed there.

| File | Use |
|---|---|
| `DP3_V137_CE.img` | Standard CE image: the framework fixes and full-precision Vorbis, plus Opus in place of WMA, the design refresh, theater mode, M3U playlists, the lock-screen track info, the Bluetooth shortcut, baked antialiasing in the icons and screen art, and a redrawn list and menu font. 8,192 bytes longer than stock, with the header mirror sector-aligned; both written slots matched in full and booted on the qualified unit. |
| `DP3_V137_CE_minimal.img` | Minimal option at stock length: DAC error-counter fix, clock table v1, full-precision Vorbis, shorter same-format track changes, natural sort, wheel timer period. Use it if the standard image does not install, or if you need WMA. |
| `DP3_V137_CE_recovery.img` | Stock code dated one day after the CE images, for returning to stock through the installer. |
| `*.report.json` | Build reports for the two CE images. |
| `SHA256SUMS` | Check these before installing. |

Every file is rebuilt from source by CI and must match its pinned hash.
