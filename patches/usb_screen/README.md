# USB screen

The data screen no longer draws string 133 (“USB Connected”). USB Audio
shows its actual fixed transport: 16-bit / 48 kHz, stereo PCM at 1536 kbps.
The existing charging-power labels, volume display, keys, USB descriptors
and audio handlers are unchanged.

This is the **USB PCM rate**, not the original MP3/FLAC bitrate. Module 11
advertises only one UAC1 audio alternate setting: two 16-bit channels at
48,000 Hz (`analysis/usb_audio.md`). USB Audio transports decoded samples;
its consumer-control HID report has no track-title or artist fields. The
firmware cannot recover those tags or the source-file bitrate from PCM.
Host track metadata would need an opt-in host companion and a new device
protocol. No invented title, playing/paused state, or source bitrate is
shown. SET_INTERFACE state alone is also not proof that audible audio is
playing.

Original CE code, informed by SDK display semantics. The 72-byte card and
144-byte strings use previously unreferenced resident pockets at
0x0305DE20 and 0x03054404. Exact stock-byte gates protect their placement;
Unicorn runs the real USB window painter in both USB personalities and
checks that connection text is absent and transport text fits above the
existing power controls. No persistent RAM or overlay growth is added.
