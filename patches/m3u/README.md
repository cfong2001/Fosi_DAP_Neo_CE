# M3U playlists

Shipped in the Standard image, composed by the full build
([`../full/README.md`](../full/README.md)): selecting an `.m3u` file in the
browser plays it, and next, previous and shuffle stay inside the playlist (up
to 59 tracks from up to 6 folders). The shipped pieces:

- Patch 0040 (browser hook) and the parser and bridge in the module 31
  extension, built by [`compose/`](compose/) (`build_payload.py`).
- Patches 0041 to 0044 (resolver, count and forward-step hooks) with the
  resolver in the shared gap tail ([`tail_build/`](tail_build/tail_build.md)).
- Patches 0060 to 0062, which leave the playlist when folder, file or tag
  playback starts ([`../navigation/README.md`](../navigation/README.md)).

Playlists work on FAT volumes; on FS type 3 volumes the import declines,
because that enumeration contract is not pinned
([`compose/mod31_compose.md`](compose/mod31_compose.md)).

The design documents record the path to that composition. Their status lines
describe the state when each was written: [`m3u_design.md`](m3u_design.md)
(resolution rules and the parser core), [`m3u_bridge.md`](m3u_bridge.md) and
[`bridge_completion.md`](bridge_completion.md) (the browser bridge, before the
compose build replaced its staging design), and
[`resolver_design.md`](resolver_design.md) (the track resolver).
