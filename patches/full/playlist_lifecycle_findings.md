# Playlist lifecycle: source 6 integration

Playlist playback in the everything build now runs through stock source 6
with the playlist as the flat list. `build/tests/test_playlist_lifecycle.py`
runs the composed image's module 0 (and module 33 for the start message)
under Unicorn and checks the folder and file the iterator ends on for
start, next across folders, wrap at the end, previous at the start, and the
unarmed folder-play path. No device playback has been performed.

## How stock source 6 works

The play context at 0x03023980 holds the list length at ctx+0 and a
**1-based** position at ctx+2. The resolver at 0x03059DAC maps a position
to a folder (written to ctx+0x34) and returns a **1-based** ordinal inside
that folder. The initializer at 0x0305D048 and the backward and shuffle
steps of 0x0305D124 then reset the folder iterator (0x0305AA44) and advance
it ordinal - 1 times (0x0305AA18). The list length comes from the count
function at 0x03059D58.

## The five defects and their fixes

The original hook kept its own position and guessed the direction of each
call. Review found five ways that went wrong. The fix replaces it with a
stateless mapping plus two small hooks (`build/src/resolver_hook.S`,
patches 0041 to 0044).

1. **First fetch.** The start path in module 31 calls the fetch at
   0x0305B2C2 with index 1 and the M3U file's own folder, and the old hook
   declined it, so stock returned a folder position. The companion hook
   now answers the two mode 1 callers that convert positions (return
   addresses 0x0307E065 and 0x0308A6CB) by returning the index unchanged.
   The start call passes 1, so playback starts at playlist position 1.
2. **One-based start index.** Module 33 normalizes the start payload to
   1, and the old hook treated it as a 0-based entry, selecting the second
   entry. The resolver hook now serves entry `position - 1`.
3. **Ordinal base.** The bridge stores 0-based ordinals among a folder's
   accepted files; stock advances `ordinal - 1` times, so ordinals 0 and 1
   both reached the first file. The hook now returns `ordinal + 1`.
4. **Forward step ignored the playlist.** For source 6, a forward step
   called the folder iterator's next file directly. Patch 0044 replaces
   `ldrh r0, [r4, #0xc]; cmp r0, #1` at 0x0305D598 with a call that runs
   both instructions and forces the shuffle-path condition while a playlist
   is armed. Every forward step then resolves the new position and
   advances to its ordinal, the path backward steps already took.
5. **Folder-boundary reset.** At the end of a folder, stock reset the
   iterator to the first file of the next folder without advancing to the
   returned ordinal. With patch 0044 an armed playlist never takes that
   path.

The count hook (patch 0043) makes the list length the playlist length, so
stock wraps from the last entry to the first and back, and shuffle picks
positions inside the playlist.

## Verification

| Test | What it runs | Result |
|---|---|---|
| `test_playlist_lifecycle.py` | Composed image: companion start fetch, module 33 start message, initializer, five steps (next, next, wrap, previous wrap, previous), unarmed start and next, a non-whitelisted fetch | All pass |
| The same test against the previous image (`c7b8c490…`) | Negative control | Fails at the first list-length check, as expected |
| `emu_resolver_full.py` part (b) | Twelve declined calls (flag clear, wrong mode, wrong descriptor, wrong caller) compared with stock, registers included | All byte-identical |
| `emu_resolver_full.py` part (c) | Position to entry mapping, including position 0 and past the end | All pass |
| `audit_playlist_start.py` | Start trampoline and the three disarm stubs, S1 to S6 | All pass |
| Host bridge and filename tests | Parser, staging layout, short-name and long-name bounds, ASan and UBSan | All pass |

## Remaining limits

- **Repeat-folder mode.** With repeat mode 2 (ctx+0xa), stock bypasses the
  resolver and repeats the current folder. During a playlist that repeats
  the folder of the current entry, not the playlist.
- **Changing play mode mid-playlist.** Module 33's switch into
  repeat-folder converts the position with the resolver, so the same
  folder-repeat behavior applies.
- **Capacity.** Staging holds 59 entries in at most 6 folder runs. Larger
  playlists decline wholesale and the M3U file is not opened as a list.
- **Hardware.** Real iterator behavior on a card, the decoder start and
  timing, and the FS type 3 decline are unobserved.
