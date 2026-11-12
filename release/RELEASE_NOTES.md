**Not yet tested on hardware.** Every image here passes the project's
offline checks (SHA-gated build, the 15-check framework verifier, Unicorn
emulation of the changed code paths). None has been flashed. Read the
install and recovery guide in `release/README.md` before using any file.

| File | Use |
|---|---|
| `DP3_V137_CE.img` | Standard CE image: the framework fixes and full-precision Vorbis, plus Opus in place of WMA, the design refresh, theater mode, M3U playlists, the lock-screen track info, the Bluetooth shortcut, baked antialiasing in the icons and screen art, and a redrawn list and menu font. 7,168 bytes longer than stock, with the header mirror sector-aligned; slot acceptance of a longer image is untested. |
| `DP3_V137_CE_minimal.img` | Minimal option at stock length: DAC error-counter fix, clock table v1, full-precision Vorbis, shorter FLAC-to-FLAC track changes, natural sort, wheel timer period. Use it if the standard image does not install, or if you need WMA. |
| `DP3_V137_CE_recovery.img` | Stock code dated one day after the CE images, for returning to stock through the installer. |
| `*.report.json` | Build reports for the two CE images. |
| `SHA256SUMS` | Check these before installing. |

Every file is rebuilt from source by CI and must match its pinned hash.
