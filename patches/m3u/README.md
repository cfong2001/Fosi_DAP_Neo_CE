# M3U playlists

Shipped in the Standard image, composed by the full build
([`../full/README.md`](../full/README.md)): selecting an `.m3u` file in the
browser plays it, and next, previous and shuffle stay inside the playlist (up
to 150 tracks from up to 32 folders). A `.m3u8` file is reached through its
8.3 alias, whose extension is `M3U`, so it imports the same way. The shipped
pieces:

- Patch 0040 (browser hook) and the parser and bridge in the module 31
  extension, built by
  [`../full/build/build_compose.py`](../full/build/build_compose.py) from
  [`../full/build/src/`](../full/build/src/).
- Patches 0041 to 0044 (resolver, count and forward-step hook sites) and
  patch 0047, which places the resolver hooks in unused module 0 code. The
  playlist staging sits at the start of the merged gap tail
  ([`../full/build/build_tail.py`](../full/build/build_tail.py)); its
  packed layout is described in
  [`../full/README.md`](../full/README.md#playlist-staging).
- Patches 0060 to 0062, which leave the playlist when folder, file or tag
  playback starts ([`../navigation/README.md`](../navigation/README.md)).

## Playlist format

- Encoding: UTF-8, with or without a BOM; any invalid UTF-8 switches the
  file to Windows-1252.
- Lines end in LF, CR or CRLF. Blank lines and `#` comments are skipped;
  `#EXTINF` is parsed but not shown on the device. URLs are skipped.
- Each entry is tried relative to the playlist's folder, then from the
  card root with any drive letter (`D:\`) and leading separators dropped
  and `..` steps that would climb above the root ignored. The device does not know the path above the playlist's
  folder, so `../Album/track.flac` resolves only when `Album` sits at the
  card root. Playlists exported on Windows with absolute paths work when
  the card mirrors the library's layout. Backslashes and forward slashes
  are both accepted.
- Names match the file's long name, case-insensitively (ASCII and
  Latin-1 letters), or its 8.3 name.
- Only files the player can play count. Missing, hidden and unplayable
  entries are skipped; the rest of the playlist still plays. Duplicates
  are kept in order.
- Limits: 150 entries from at most 32 folders, and a file must be within
  the first 2,048 playable files of its folder. A playlist past any limit
  does not import, and the file opens as it would on stock firmware.
- The library-wide filename search (the parser's third resolution stage)
  stays off on the device.

Playlists work on FAT volumes; on FS type 3 volumes the import declines,
because that enumeration contract is not pinned
([`compose/mod31_compose.md`](compose/mod31_compose.md)).

The design documents record the path to that composition. Their status lines
describe the state when each was written: [`m3u_design.md`](m3u_design.md)
(resolution rules and the parser core), [`m3u_bridge.md`](m3u_bridge.md) and
[`bridge_completion.md`](bridge_completion.md) (the browser bridge, before the
compose build replaced its staging design), and
[`resolver_design.md`](resolver_design.md) (the track resolver).
