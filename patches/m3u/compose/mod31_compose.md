# M3U bridge completion and module 31 extension composition

> Current build correction: the 7,114-byte measurements below describe an
> earlier compiler and parser revision. The current reviewed composition is
> 7,168 bytes, SHA-256 `84b82518bfb02105cb4166914021b0e56a2ba16ea1cbd19ecc88abe70dbbfe28`.
> Its lock routine is at `0x030808B0` and patch 0033 is `02f007b8`;
> patch 0040 remains `00f095bf`. With Arm GNU GCC 14.2.1, binutils 2.44,
> Python and Capstone, run:
>
> `python3 patches/m3u/compose/build_payload.py --out-dir /tmp/fosi-m3u-build`
>
> The script audits branch targets and rejects unreviewed payloads and hook
> bytes. It writes to the chosen scratch directory. Pair this payload with
> the tail resolver and patches 0041/0042: a grown overlay alone does not
> implement playlist playback. The hardware and filesystem gates remain open.

**Verdict: complete for FAT volumes, with two named incompletions.** The M3U bridge is finished against the bridge_completion pins, composed with the parser, the 0040 trampoline and the lock-screen routine into one module 31 extension payload of 7,114 bytes against 7,436 bytes of room (322 bytes spare), and proven in a scratch grown build: validate_grown passes and segment isolation holds across all 82 modules. The two incompletions are the FS type 3 volume path, which declines because its enumeration contract is not pinned anywhere in the project documents, and the parser's stage 3 library match, which is disabled. Both are stated in full under "Deviations and incompletions" below. Nothing here is stacked in the live framework, nothing was pushed, and the stock image still hashes to fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef.

## The completed bridge

The bridge source is src/m3u_bridge.c with src/m3u_bridge.h, superseding the pre-pin draft at work/m3u_bridge/bridge/. The old draft's contracts were wrong in three ways the completion pins corrected: file primitives take descriptor handles rather than paths, there is no path string anywhere on device, and the descriptor table stride is 638 rather than 384 (the bridge never touches the table directly, so the stride matters only as provenance for the size field the registrar fills). Entry point **m3u_bridge_node_action** (node, state, ctx), called by the trampoline with the node-action function's registers.

The import path, in order:

1. If the volume type byte at 0x0307A024 is 3, return 0 (decline) before touching any state. Otherwise clear the staging flag byte, so a stale import can never be live while a new one is being built.
2. Read the browser's current directory cluster from the level record (state + 56 times the level byte at state + 0x1CC, cluster at record + 0x14).
3. Acquire the filesystem (0x030611E0) and register the playlist file itself through the resident registrar 0x0305C514 with (current directory cluster, the node's 11-byte name at node + 0x4F, the node's attribute byte at node + 0x5A). A negative return declines. The slot is never filled directly.
4. Run m3u_import over the handle. The parser's read requests are (buffer, length, position) shaped exactly like the stock read primitive 0x030693EA, so bridge_read passes them through; the size comes from 0x030545D4. This is module 37's whole-file model (registrar, size query, positional reads) with no bridge-side file buffer, which is what makes playlist size unbounded by bridge RAM. There is no close call: no stock close primitive is pinned, the descriptor slots are the device manager's fixed pool, and module 37's model never closes.
5. Write the staging and set the flag byte last. Any failure or cap overflow before that point returns 0 with the flag still clear, and the node opens with stock behaviour: the import is all-or-nothing per file, per the tail_build design.

### The path namespace and stat

The parser speaks in paths; the device speaks in clusters. The bridge defines the namespace it serves: the playlist path is "/" + a one-byte sentinel component (0x01) + "/" + the playlist's text name, so the parser's folder for stage 1 is the sentinel directory. In **stat**, a leading sentinel component starts the walk at the browser's current directory cluster; any other absolute path starts at the volume root cluster, read from the cell at 0x0307BF58 (the same cell the resolver's stack reset reads). Components "." and ".." are handled inside the walk with an ancestor stack of up to 16 clusters; ".." above the start directory fails that stat, and the parser's stage 2 then retries the entry root-relative, which rescues the common "../OtherFolder/track" playlist shape.

stat walks directories with the raw dirent reader 0x03057F8E, the same reader the stock counter 0x0305AB0A counts with in card mode, applying that counter's skip rules: end at a zero first byte, skip deleted entries (0xE5), hidden entries (attribute 0x02) and volume labels (attribute 0x08). A file counts toward the ordinal only when the stock classifier 0x0305A15C accepts its extension against the volume accept table at 0x03005714 (MP1 MP2 MP3 WMA WAV APE FLA AAC M4A OGG MP4 3GP DFF DSF, read from the stock image during this work; CUE is not in the volume table). A name that matches a file the classifier rejects does not resolve. The returned pair is (parent directory cluster, accepted-file ordinal), the resolver's playback identity; the reasoning is recorded in the header of src/m3u_bridge.h. m3u.h's wording calls the pair the file's starting cluster plus ordinal; the bridge deliberately narrows that to the pair the tail hooks serve, and the parser itself never interprets the values.

Long names are matched from the on-disk format, not from a stock contract: LFN dirent groups (attribute 0x0F) preceding an entry are reassembled, checksum-verified against the short entry, and compared case-folded alongside the 8.3 form the component is also reduced to. A refinement the disassembly forced during this work: the 42-byte context copied into every directory-stack element, and therefore into every staging run, is the standing context at **0x0307BF5C**, captured verbatim at import time; it is not per-directory state.

### Resolution logging and staging

The parser's M3uTrack is 272 bytes (two 128-byte text fields), so out[] cannot be the bridge's record for 144 tracks. It does not need to be: stat_path in m3u.c issues exactly one fs->stat call per resolution attempt and accepts exactly when stat returns 0 for a non-directory, so stat appends each resolved file's (parent cluster, ordinal) to a compact log (576 + 288 bytes) in resolution order, and the parser writes into a single dummy track. The bridge cross-checks the log length against stats.resolved + stats.overflow and declines on any mismatch, so a drift in the stat contract fails safe instead of staging a wrong table. Entries past the 144 cap set an overflow flag inside stat and decline the whole import.

The staging writer groups the log into runs in first-use order, calls the stock counters for each new run's countA (0x0305AB0A) and countB (0x0305965C), writes the 50-byte run records (cluster, countA, countB, the 42-byte context), the 4-byte entries (within-directory index, run id, flags 0), then the header (entry count, position 0xFFFF, residual 0, run count), and sets the flag byte at +0 last. Counts are captured in card mode 6, the scan's own mode: module 33 recomputes totals at playback against the scan database in mode 1, and for an unchanged card the two agree; the card is the only side an import can measure.

## Payload layout

One payload for the module 31 code extension, built by build_payload.py (layout record in build/layout.json). The extension room is exec 0x0307EE48 to 0x03080B54.

| Offset | Address | Bytes | Component |
|-------:|--------:|------:|-----------|
| 0 | 0x0307EE48 | 64 | 0040 hook trampoline (fills its slot exactly at this placement) |
| 64 | 0x0307EE88 | 6,644 | bridge + parser blob, m3u_bridge_node_action first |
| 6,708 | 0x0308087C | 406 | lock-screen routine, ui_lockscreen_paint at its base |
| | | 7,114 | total, 322 bytes spare of 7,436 |

The bridge + parser blob is one link of src/m3u.c and src/m3u_bridge.c (-Os, cortex-m3, freestanding): 5,469 bytes of text and read-only data plus 1,172 bytes of .data, 6,644 bytes as a flat binary. m3u_import lands at 0x0307F6B0; the parser's contribution matches its standalone target build (3,601 bytes at -Os per parser_build/TARGET_BUILD.md, the difference being link sharing). The link asserts zero undefined symbols, the entry symbol exactly at the blob base, and zero .bss: the payload is a plain byte copy with no loader, so every writable byte rides in the image as .data, which the bridge sources arrange with nonzero initializers on their statics (the build fails loudly if any .bss appears; -fno-zero-initialized-in-bss alone did not move them, so the initializers are the mechanism, and both are in place).

The trampoline is the audited instruction sequence from the earlier workstream, re-assembled at the new base with rz-asm and re-audited against its Capstone decode in the build: name test on node + 0x57, bridge call to 0x0307EE88, displaced call 0x0307D1F8 reproduced on no-match, resume at 0x0307DF1E, handled exit through 0x0307E0C8 with r0 = 1. The lock routine is byte-identical logic to its standalone build (366 bytes of code, 40 bytes of .data), relinked from 0x0307EE48 to its payload offset.

## Updated scratch patches

In patches/, not stacked:

* **0040-m3u-browser-hook.patch**: same site (module 31 code 0x0307DF1A, expect fff76df9), replacement regenerated for the new trampoline base: **00f095bf** = B.W 0x0307EE48. The gate text now names the module 31 extension build instead of the withdrawn module 0 placement.
* **0033-ui-lockscreen-title.patch**: same site (0x0307E89E, expect e4f72fbf); the routine moved, so the replacement is regenerated: **01f0edbf** = B.W 0x0308087C (the standalone scratch build had 00f0d3ba to 0x0307EE48). The composition build emits these bytes as build/site33.bin and build/site40.bin so a future layout change regenerates both mechanically.

## Scratch build and isolation

The scratch framework is a copy of work/patches/framework/ at framework/, with the two scratch patches added and a scratch manifest (patches/manifest_composed.txt: the default 32 patches plus 0033 and 0040). The transplant tree is copied alongside it because the build resolves transplants relative to the framework's parent. Two builds, both offline:

* Ungrown equivalent (default manifest + transplants): out/ungrown.img, SHA-256 1cf609559048a02686585a159dab06fa4856954aa647283a50a8b47da33e3c99, identical to the shipped default unified image, which pins the scratch copy's provenance.
* Grown (scratch manifest + --grow 31:code:payload.bin): out/grown.img, SHA-256 23a188c889823c8e78bd01101beb4eac42130a83a29c23f1ebd37ecf9807d7f5, byte length 13,638,606 = stock 13,631,492 + 7,114. **validate_grown passes**, both inside the build's finalize step and standalone on the result.

Isolation (tests/check_isolation.py, modelled on verify.py check 9): every segment of all 82 modules is byte-identical between the two images except module 31 code, which is exactly the ungrown code with the payload appended and the two hook sites patched (7 of the 8 site bytes differ; patch 0033's last byte equals stock's). The build report's positional diff against stock (5,065,174 bytes) is dominated by the insertion shift and is not the meaningful comparison; the segment comparison above is.

## Host-side exercise

Three layers, all in tests/:

* The parser's existing suite, run unmodified against the composed sources: **26 checks, 0 failures**, including the ASan/UBSan build.
* The bridge end-to-end against a mock firmware layer (tests/host_bridge_test.c, the target source compiled with HOST_TEST and its stock bindings rebound): a fake FAT tree with LFN dirent groups, a deleted entry, a hidden file, a volume label and an unaccepted extension. Scenario 1 imports a nine-entry playlist (seven resolve, including an LFN-named file at the root, a duplicate, a lowercase entry, and a "../" entry rescued by stage 2; two do not: a missing file and the hidden file) and checks the staging **field by field against the tail_build layout**: header flag, count 7, position 0xFFFF, residual 0, run count 4; runs in first-use order with hand-derived counts (MUSIC cluster 0x1001 countA 2 countB 1, LIVE 0x1003 2/0, root 0x0002 2/2, PODCAST 0x1002 1/0) and the 42-byte context verbatim; all seven entries' (index, run, flags). The registrar mock also verifies the B1 call shape: one call, directory cluster 0x1001, name "TEST    M3U", attribute 0x20. Scenarios 2 to 4 verify the declines: FS type 3 leaves the staging buffer byte-for-byte untouched, a 13-run playlist returns 0 with the flag clear, and a playlist with no resolvable entries returns 0. The suite also passes under ASan/UBSan. **All host checks pass.**
* The trampoline audit described above, run on every payload build.

One defect was found and fixed by the host test: stat's start-component scan did not skip the path's leading separator, so stage 1 walks started at the root instead of the playlist's folder. The fix is in src/m3u_bridge.c and the payload was rebuilt and re-verified after it.

## Deviations and incompletions

* **FS type 3 volumes decline.** Under type 3 the stock counters and the resolver take context-based paths (0x0305AC92 for totals, 0x03059746 behind countB) whose per-directory enumeration contract is pinned nowhere: how a type 3 directory is keyed to those functions and how its entries are enumerated by name through the 0x03057E46 context-source mechanism is exactly the missing pin. Rather than invent it, bridge entry checks the type byte at 0x0307A024 and returns "not handled" for type 3, leaving all state untouched. The FAT path is complete. This is the one piece of the brief stopped for an insufficient pin.
* **Parser stage 3 is disabled.** lib_count reports an empty library, so entries that fail stages 1 and 2 stay unresolved even when a suffix match exists somewhere on the card. No library enumeration order or node-chain path reconstruction is pinned, and stage 3's value depends on the long-name forms it compares. This matches the prior bridge draft's stated degradation, now documented in the source header.
* **M3uFileInfo.clus carries the parent directory cluster**, not the file's own first cluster. The parser copies the pair through uninterpreted, staging needs the parent, and the file's own cluster is not part of the resolver format. Recorded here because m3u.h's comment describes the pair the other way; the narrowing is deliberate and confined to the bridge's stat.
* **Counter capture mode.** Staged countA and countB are card-mode (mode 6) values, captured by calling the stock counters at import. Playback recomputes its totals in database mode 1; the sentinel logic in the tail hooks consumes the staged counts, so end-of-playlist behaviour rests on the scan database mirroring the card, the design's standing assumption. Unverifiable offline.
* **Exactly-at-cap ambiguity is resolved conservatively.** A resolution that would be the 145th entry sets the overflow flag and declines the whole import, because a log that ends exactly full cannot be distinguished from a truncated one after the fact.

## What remains Phase E

* **Window-cycle soak on the grown module 31 build**: the insertion shifts module 31's data segment and every later module; that the device loader accepts the grown code_len and cycles windows against the shifted layout is proven structurally only (validate_grown, insertion-rebuild gates), not on hardware.
* **Real card import**: a physical card, the registrar against the real descriptor pool, real dirent streams (including multi-cluster directories and fragmented LFN sets), and playback through the tail hooks end to end, including the end-of-playlist sentinel.
* **Stack depth**: the import runs the parser (about 2 KB of line and path buffers) plus the bridge's walk (512-byte LFN assembly) on module 31's task stack, whose size is not pinned. The code is built to keep large buffers out of the payload, not out of the stack.
* **FS type 3 support**, if a pin for its enumeration contract is ever established.

## Files

* src/m3u_bridge.c, src/m3u_bridge.h: the completed bridge. src/m3u.c, src/m3u.h: the parser, byte-identical copies of work/patches/m3u/src/. src/lockscreen.c: verbatim copy of the lock-screen source. src/asm_trampoline_ext.py: the trampoline generator for this placement. src/asm_trampoline.py and src/site33.S.orig: the earlier workstream's originals, kept for provenance.
* build_payload.py: the composition build; payload.bin: the composed payload; build/: intermediates, the layout record and the generated site bytes.
* patches/0040-m3u-browser-hook.patch, patches/0033-ui-lockscreen-title.patch: the re-pinned scratch patches.
* framework/, vorbis_swap/: the scratch framework copy and its transplant sibling; out/grown.img and out/ungrown.img with their build reports.
* tests/host_bridge_test.c, tests/check_isolation.py, tests/test_m3u.c with its Makefile: the host exercise.
