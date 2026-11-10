# Playlist-to-library navigation: lifecycle audit

The browser can select an M3U playlist, a normal music file, or a
folder. The experimental M3U bridge arms the staging flag at
`0x0307BFB4`; its resident resolver hooks use that flag to substitute
playlist entries. The current bridge clears the flag on a new M3U
import, but no code in the checked-in bridge or trampoline clears it
when the listener selects a normal music file or starts folder playback.
The design note's claim that dismissal clears it is not established.

## Evidence

- A successful import currently arms staging but does not start playback.
  The bridge ignores its play-context argument and returns after writing
  staging. Its trampoline then jumps directly to the common return at
  `0x0307E0C8`, skipping the stock source selection, event `0x14D` and
  message 3. The lifecycle audit executes the actual trampoline and stock
  epilogue with a modeled successful bridge return and confirms the two
  calls are skipped. It does not emulate the parser or playback task. The
  statement in the resolver design that the bridge initializes the index
  at `ctx+2` does not match the composed bridge source. The unified
  build in `patches/full/` implements the start by entering this stock
  sequence at `0x0307E052` from the trampoline's handled exit, gated
  by an extended audit there; the composition audited here is
  unchanged.
- Stock folder playback performs the classifier and directory fetch at
  `0x0307E052` and `0x0307E060`, writes the result at `sp+4`, selects
  source 6, updates the current directory global, clears events, then
  posts `0x14D` and sends message 3 using `sp+4` as its argument. A
  playlist start needs a validated equivalent of this sequence and the
  receiver's context initialization; merely setting source or count is
  not established to work.
- Module 31's node-action routine branches at `0x0307DF16` directly to
  `0x0307DF4E` for a class-zero directory. This bypasses the M3U hook
  at `0x0307DF1A`. Routine directory traversal continues through
  `0x0307DF72`; it should not disarm an active playlist merely because
  the user browses.
- A class-one file takes the non-M3U trampoline path. Running the
  current 64-byte trampoline with an `MP3` node and staging flag set
  leaves the flag set and resumes the original classifier path. The
  `audit_playlist_lifecycle.py` script reproduces this instruction-level
  finding against an independently generated trampoline.
- The validated music-file action reaches `0x0307E1CC` and may call the
  stock directory fetch at `0x0307E1EE` or `0x0307E20C`. The experimental
  companion resolver at that entry substitutes playlist records when
  its flag, mode and matching-cluster tests pass. Thus a stale flag is
  a plausible cause of the wrong file being selected when leaving a
  playlist; the full user interaction is not yet emulated or tested on
  a device.
- The class-zero folder-play path begins at `0x0307E04E` and calls the
  same fetch before setting source 6 at `0x0307E088`. Ordinary folder
  traversal branches elsewhere and does not need to disarm playback.
- Module 24 constructs the play context for a selected library list.
  At `0x0307EC72` it stores the category from `0x030235C0` into play
  context `+0xF2`. A same-track branch returns through `0x0307EA78`
  without reaching this context-commit site. Module 33 checks the
  category at `0x0308A584` and routes 6 to its folder resolver and
  `0x63` separately; observed tag-library categories 1–5, 7–9 and 100
  use the remaining path. The old flag can therefore remain stale
  across tag playback even if those categories don't immediately use
  the source-6 resolver.

## Candidate, not installed

`playlist_exit.S` provides two small stubs, one at each play-start site.
Each clears the flag and reproduces the displaced instructions. The
file stub also reproduces the displaced call, restores its original
return address, and resumes at `0x0307E1D2`. The folder stub resumes at
`0x0307E052`, before the original classifier call. The candidate is
linked at `0x03080A48`, immediately after the current 7,168-byte
module-31 composition; it is 68 bytes and fits in its 268-byte remaining
window. Any payload layout change requires relinking and re-auditing
both hooks. **It is not included in the configurator or any firmware
build.** The unified build in `patches/full/` does include it,
relinked after that build's own module 31 composition, together
with the playback-start sequence its audit pairs it with.

To reproduce on a local machine with GNU Arm binutils, Capstone, Unicorn
and the pinned stock image:

```sh
python3 patches/navigation/build_exit.py --output /tmp/playlist-exit.bin
python3 patches/navigation/test_exit.py
python3 patches/navigation/build_tag_exit.py --output /tmp/playlist-tag-exit.bin
python3 patches/navigation/test_tag_exit.py
python3 patches/navigation/audit_residency.py
python3 patches/navigation/audit_playlist_lifecycle.py --trampoline /path/to/generated/trampoline.bin
```

The instruction-level emulator compares the two hooks with the stock
instructions, including register and flag state, return address, stack
pointer and a modeled stock callee. It verifies that a clear flag stays
clear and an armed flag is cleared at either playback start. It also
executes the stock child-directory traversal up to its directory-loader
call with both candidate hooks installed and confirms that traversal
leaves an active playlist flag set. It does not
prove the full browser, library, playlist and playback lifecycle. Before
shipping, audit other source-6 entry paths and transitions from the tag
library, integrate the extension and preconditioned hooks with the M3U
payload, test normal playback and playlist resumption end to end, and
perform the existing module-window and gap-tail hardware gates.

The separate `tag_exit.S` candidate clears the flag when module 24
commits a new library context, replaying the displaced `strh.w` before
returning to `0x0307EC76`. It adds 26 bytes at `0x0307EDEC`, the end
of stock module 24, and requires `--grow 24:code:` as well as the
module-31 growth above. `test_tag_exit.py` checks register and flag
equivalence for ten category values and both initial flag states, and
executes the stock same-track early-return branch to confirm that the
candidate does not clear the flag on that path. These are synthetic
instruction tests: module-24's grown-overlay memory residency, the
complete selection flow and hardware behavior remain unverified. The
candidate is not in the build or configurator. The unified build in
`patches/full/` includes this stub as its module 24 growth.

The address census lists every stock code/data/BSS span intersecting
the two candidate regions. The module-24 candidate intersects module
11, 27, 30, 31, 32, 38 and 39 code; the module-31 candidate intersects
module 27 and 39 code. Neither candidate intersects stock module 0,
18–20, 23–26 or 33 ranges. Module 23 loads module 24 at `0x0307E0D8`
and `0x0307E4B4`; its own code ends at the start of module 24's code,
below the proposed stub. Existing analysis identifies the other overlaps
as window or scan overlays, but it does not prove every runtime schedule
or all possible simultaneous occupants. In particular module 27 is the
playback window and overlaps both proposed regions. A module-window
cycle and runtime loading trace are required before treating either
placement as safe.
