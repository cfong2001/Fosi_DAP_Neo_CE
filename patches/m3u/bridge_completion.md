# M3U bridge completion pass

> Current status: superseded. The bridge was completed and composed with the
> parser and the lock-screen routine into the module 31 extension
> ([`compose/mod31_compose.md`](compose/mod31_compose.md)), which ships in the
> Standard image. The verdict below records the state when this was written.

Scope: close blockers B1, B3, B5 and the B2 staging arena choice with instruction-level evidence, and complete the bridge build only if every pin reaches proof. Method: Capstone disassembly of the extracted modules (listings in completion/), traced from the hook site in module 31 through module 0's walker, counters, directory stack and file engine, and module 33's playback advance. Stock image verified unchanged at the end of the pass: SHA-256 fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef.

Verdict summary: B1 pinned with a design correction, B5 pinned, B3 pinned as a mechanism and the pin refutes the staged-record design in the current bridge source, B2 still blocked. The build was not attempted, because the brief conditions it on all pins reaching proof and two do not. No bytes were composed, the live manifest was not touched, and the bridge source was not edited.

## B1: current directory identity

**Pinned, and the representation is a cluster, not a path.** No path string exists anywhere in the browser flow. The browser state is a fixed struct at 0x030228A8 (module 31 loads the literal directly; it is not a pointer chase). Fields used here:

- +0x000: display node list head.
- +0x1CC: u16 current level (depth).
- +0x1CE: per-level u16 array A, 8 entries.
- +0x1DE: per-level u16 array B, 8 entries.
- +0x1EE: u16 selected index within the current level.
- +0x1F4: pointer to the current volume descriptor entry (entry layout at module 31 data 0x030247C4: u8 code, u32 extension-table pointer at +4; lookup fn 0x0307D1F8).
- +0x1F8: u16 volume code.

Per-level directory records sit at state + 56 * level (the arithmetic `rsb r0, r2, r2, lsl #3; add r0, r7, r0, lsl #3` is 56 * level), about 8 levels before +0x1CC. Record fields:

- +0x0C: u16 entry count of that level's directory.
- +0x0E: u16 sub-count A.
- +0x10: u16 sub-count B, also used as an index base by the node-action code.
- +0x14: u32 directory cluster (the FAT-path field).
- +0x18: u32 the byte-swapped twin of the same cluster pair (the FS-type-3 field).
- +0x24: u8 flag, set to 1 on descend and at init.

Write on directory entry, in module 31's node-action function: at 0x0307DF96..0x0307DFB2 the new level's rec+0x14 is stored as `[node+0x69] | ([node+0x63] << 16)`, and at 0x0307DFB4..0x0307DFCC rec+0x18 is stored as `[node+0x63] | ([node+0x69] << 16)`. The node fields are the selected folder node's embedded dirent halves: node+0x63 is dirent+0x14 (cluster high u16, since the dirent copy starts at node+0x4F) and node+0x69 is dirent+0x1A (cluster low u16), so rec+0x14 is the full FAT32 cluster, low half first. The counts are then filled by 0x0307D410 and the level is enumerated by 0x0307D254.

Write at level 0, in browser init 0x0307D456: rec+0x14 and rec+0x18 both receive the return of 0x0305A022(mode byte at [0x03025928+4]), the root-cluster getter (mode 1 or 2 returns 0; otherwise it returns the word at [0x0307A030 + 0xD]).

Read on enumeration, in 0x0307D254: the walker parameter block is built on the stack with block+0x00 = [rec+0x14] at 0x0307D29A..0x0307D29E, block+0x04 = 0, block+0x08 = [rec+0x0C], and block+0x1C = a 42-byte copy from rec+0x18 at 0x0307D28E..0x0307D296. The wrapper 0x0305A970 is then called with ctx = sp+0x48, table = [[state+0x1F4]+4], mode = the byte at [0x03025928+4].

So the bridge reads the current directory cluster as `*(uint32_t *)(0x030228A8 + 56 * *(uint16_t *)(0x030228A8 + 0x1CC) + 0x14)`, with +0x18 as the FS-type-3 twin. The playlist file's own identity comes from its node: cluster = `[node+0x69] | ([node+0x63] << 16)`, ordinal = the u32 at node+0x0C (written by the enumerator as the walker cursor minus 1, that is, the entry's enumeration index).

### Design correction forced by B1

The bridge source models file access on paths: `stock_file_size(path)`, `stock_file_read(path, ...)`, and `bridge_playlist_path()` building an absolute path string. The instruction evidence says both primitives take a descriptor handle, not a path:

- 0x030545D4(handle): element = 0x0307AB68 + handle * 384; returns [element+0x10], the file size. The sibling getter at 0x030545E6 returns [element+0x20].

**Erratum (2026-10-31, resolver-design workstream, coordinator-confirmed from the registrar disassembly): the descriptor stride is 638 bytes, not 384.** Three independent checks agree: the registrar's index math at 0x0305C526 (r7 times 319, then times 2), module 0's dedup loops advancing by 0x27E, and 8 slots of 638 from 0x0307AB68 ending exactly at the root-cluster global 0x0307BF58. Every "384" in this document should read 638.
- 0x030693EA(handle, buf, len, pos): reads through the FS position engine (seek helper 0x030594A0, read helper 0x03058FA8) in chunks of at most 0x400, returns bytes read or -1.

Module 37's CUE parse entry 0x0307D73A receives the handle as its r0 argument; its caller, module 38's scan at 0x0307EAAC, passes the return of the registrar 0x0307E43C. The descriptor element layout, from the registrar's stores and the engine's reads: +0x00 state byte (1 = in use, 3 = the "WW" special case), +0x01..+0x0B the 11-byte name, +0x10 size, +0x14/+0x18 cluster pair, +0x20 current position, +0x24 cluster.

**Remaining sub-pin (B1b):** no registrar that is resident while the browser window is up has been pinned. Module 38's registrar 0x0307E43C is overlay code in module 38's exec window and is not resident while module 31 is up. The exact missing trace is which module 0 function registers a descriptor from a dirent (the FS operations table at 0x03004438 is populated at 0x030545F8 with entries 0x030589B7, 0x03058FA9, 0x030594A1, 0x0305CA1D, 0x03058E8F, 0x0305947F, and one of its call paths is the likely registrar), or a proof that the bridge may fill a free descriptor slot directly (state byte 0) with the pinned fields and have the position engine accept it. Until one of those is traced, the bridge cannot obtain a handle for the playlist file, and `pl_open` cannot be completed honestly.

## B5: walker block +0x08 producer and the ctx name field

**Pinned.** The producer of block+0x08 is the walker's caller, writing the block before the wrapper call. In module 31's enumerator the store is at 0x0307D2A4..0x0307D2A8: block+0x08 = [rec+0x0C], the level record's u16 count. That count is itself produced by 0x0307D410 over the directory cluster: [rec+0x0E] = 0x0305AB0A(cluster, table), [rec+0x10] = 0x0305965C(cluster, mode), [rec+0x0C] = the sum when the FS-type byte at 0x0307A024 is not 3; when it is 3, the pair is 0x0305AC92 and 0x03059746 over rec+0x18 instead.

Semantics: the walker reads block+0x08 at exactly two sites, 0x0305A356 and 0x0305A58A, both in its database modes (mode argument 1 and 2), where it bounds the cursor against the record count of the database list. A full read-site scan of the walker (0x0305A2F0..0x0305A944) shows no other load of [block+0x08]. In the FAT and FS-type-3 enumeration paths, the bridge's case, block+0x08 is never read; enumeration terminates on a dirent whose first byte is 0. Module 38's stack block likewise leaves the field unwritten. The bridge's stat() may therefore leave block+0x08 = 0. The bridge header's guess that the count is established by 0x03059F58 is wrong; that function initialises the directory-stack elements (see B3), a different structure.

The ctx name field: in the FAT enumeration path the walker leaves the raw dirent in the ctx record. The dirent reader 0x03057F8E writes it there, and the match path at 0x0305A84C..0x0305A938 tests the fields in place (first byte 0 = end, 0x2E = dot entry, 0xE5 = deleted, attr tests) and returns with the ctx untouched. Layout: name at ctx+0x00 (11 bytes), attribute at ctx+0x0B, cluster high u16 at ctx+0x14, cluster low u16 at ctx+0x1A, size u32 at ctx+0x1C. In the FS-type-3 path the walker also writes parsed fields into the ctx (offsets +0x00, +0x04, +0x08, +0x0A, +0x0B, plus ctx+0x0D and the cluster/size stores at 0x0305A786..0x0305A792 landing at +0x14, +0x1A, +0x1C), and the entry name then lives in the LFN out-buffer built by 0x0305A1A4, not in the ctx. That case is the B4 LFN exclusion and stays a documented fall-through for v1.

Two corrections to the bridge header fall out of this trace. The walker returns 0 when an entry is found (epilogue at 0x0305A7A0) and 0x13 when none is (exit at 0x0305A93A); the header's "nonzero = entry found" is inverted. The block fields the header lists at +0x0C, +0x10, +0x14, +0x18 are outputs of the database modes, not of enumeration; in enumeration the outputs are the cursor at block+0x04 (advanced past the found entry) and the ctx record itself.

One erratum to the completion brief and to m3u_bridge.md: the array at 0x0307A8E4 has 71-byte elements, not 56-byte. 0x0307A8DC is its depth byte. The 56-byte stride belongs to module 31's level records at 0x030228A8. The brief's phrase "node array 0x0307A8DC, 56-byte stride" conflates the two arrays.

## B3: module 33's source-6 fetch chain

**Pinned as a mechanism. The pin refutes the staged-record consumption model in the current bridge source.**

The advance for source code 6 (play ctx +0xF2 == 6) is the branch at 0x0308A642 in module 33's playback task. Its fetch calls are 0x03059DAC(index = [ctx+2], out descriptor = ctx+0x34, table = the pointer at [0x03005714], mode = 1) at 0x0308A68C, and in the alternate sub-case 0x0305B2C2(cluster = [ctx+0x34], table, mode = 1, index) at 0x0308A6C6. The total at [ctx+0] is refreshed from 0x0305AB0A([ctx+0x34]) when the FS-type byte is not 3, or 0x0305AC92(ctx+0x50) when it is 3. The resolved index returned by 0x03059DAC is stored back to [ctx+2] and [ctx+6] at 0x0308A6DE..0x0308A6E2.

0x03059DAC resolves the flat index against the directory stack, a module 0 structure the scan and the folder-play setup maintain:

- Base 0x0307A8E4, element stride 71 bytes, depth byte at 0x0307A8DC, cumulative count word at 0x0307A8E0.
- Element fields: +0x00 u16 countA (from 0x0305AB0A), +0x02 u16 countB (from 0x0305965C), +0x04 u16 cursor, +0x11 u32 parent cumulative count, +0x15 u32 directory cluster, +0x1D the 42-byte FS context (the same 42 bytes the walker block carries at +0x1C).
- Builders: 0x03059C76 resets the stack to the directory whose cluster is in the global at 0x0307BF58 (module 31's folder-play fill stores it there from the selected record) and fills element 0; it is called at the head of both 0x03059D58 and 0x03059DAC. 0x03059F58 initialises an element's counts (called by module 38's scan at 0x0307E618 and by 0x0305B2C2). 0x03059B10 descends one level, pushing an element for the subdirectory at the cursor.
- 0x03059DAC walks the elements accumulating counts until the element whose range contains the index, re-descends via 0x03059B10 as needed, then writes the element back into the caller's descriptor: [out+0x00] = element cluster, [out+0x08] = element total, and the 42-byte context copied to [out+0x1C]. In the play ctx that out descriptor is ctx+0x34, so after the call [ctx+0x34] is the resolved directory's cluster and [ctx+0x50] its context.

Entry materialisation for the decoder goes through the descriptor table at 0x0307AB68 (see B1): module 33's HifiFile server at 0x030895DA serves the descriptor named by the current-handle byte at [0x03004458], and the FS position engine (0x030594A0 seek, 0x03058FA8 read) walks that descriptor's cluster chain.

There is no array of (cluster, index) records anywhere in this chain, and no consumer reads one. Source 6 always enumerates the real subtree rooted at the [0x0307BF58] directory, in the scan's depth-first order, resolving each flat index through the element stack. The fetch module 24 performs at 0x0306C7AC, which the bridge source's StageRec comment cites, belongs to the database sources; it is never called for source 6 (a call census over module 33 shows its only fetch-helper calls are the ones above).

Consequence: the fill at the end of `m3u_bridge_node_action` as written (source code 6, total = playlist length, index = 0) would make the player iterate the playlist folder's subtree in scan order, not the staged playlist. Completing the bridge on this design is not possible. A working design needs one of: a consumer hook inside the source-6 fetch (for example inside 0x03059DAC's index resolution) that substitutes the bridge's staged records; or a different playback source whose fetch the bridge can supply. Both are design changes with new patch surface, outside a pinning pass. The staged-record staging loop and the context fill in m3u_bridge.c should not ship as written.

## B2: staging arena

**Still blocked.** The bridge as designed needs 512 staged records at 0x1C bytes = 14,336 B, plus its own .bss of 2,056 B (the 2 KB playlist buffer and statics; the parser has no .bss), 16,392 B total. A packed staging of (cluster, index) pairs at 8 B per record would cut the record part to 4,096 B, 6,152 B total, but no range is proven free at either size. The records must survive from the browser window, where the import runs, into playback, where the consumer reads them, so the proof has to cover both windows and everything that runs during playback.

Survey results, from a literal-reference census over all 82 modules plus the manifest's data and BSS extents:

- Module 31 BSS tail: does not exist. Module 31's BSS is 0x030247F4..0x03025924, and the display-node pool at 0x03024814 is 7 nodes of 0x270 B = 0x1110 B, ending exactly at 0x03025924.
- SAVEINFO verbatim tail: the block at SAVEINFO +0x1C7..+0x2D5 is about 270 B. Two orders of magnitude too small.
- The shared overlay window 0x03025924..0x030368C8: this is the data and BSS window of overlays 17, 18, 19, 20, 27, 29, 38 and 61, all of which hold literal references into it. Modules 18, 19 and 20 are the tag and cover workers and run during playback. Modules 38 and 39 hold the scan and sort arenas in the same span (module 38 BSS 0x03024E34..0x03045D98, module 39 BSS 0x030247EC..0x03048D40). Any address in this window can be overwritten by a window change or a cover load after the import, so it fails the survival proof.
- Above module 33's BSS end (0x0304B624): claimed. Module 36 references 0x0304B624 and 0x0304CAA8, and the codec stub family's data sits at 0x0304DE34..0x0304DE48.

The exact missing pin is the loader's complete allocation map for the system SRAM, including task stacks and runtime-only allocations that no module manifest declares. Without it, no range of 6 KB or more can be positively proven unwritten across the browse-to-playback lifecycle. A smaller staging design would narrow the search but not remove the need for that map.

## Build outcome

Not built. B1b and B2 remain open, and the B3 pin removes the consumer the current bridge source was written against, so composing a blob would mean putting speculative bytes into the extension region, which the brief forbids. Patch 0040 and its trampoline are unaffected: the trampoline declines cleanly whenever the bridge entry returns 0, and the stub already composes to stock behaviour. The scratch build from the parser pass (image SHA f2a6f34a0dbf206325f26759cf0417ee6062edb6f0f0eb2a399f7a9abe1dc466) remains the last composed state.

Recommended next steps, in order: trace the descriptor registrar through the FS operations table at 0x03004438 (closes B1b); take the design decision B3 forces, a consumer hook in the source-6 fetch versus a different playback source, before any more bridge code is written; and obtain or derive the SRAM allocation map (closes B2), possibly alongside a packed 8-byte staging record.

## Evidence

Disassembly listings produced in this pass, all under completion/: mod31_full.txt (module 31, full), mod33_full.txt (module 33, full), mod0_full.txt (module 0, full), mod0_walker.txt (walker 0x0305A2F0..0x0305A944), mod0_ctxinit.txt (0x03059F58 region). Prior evidence in evidence/ (walker region, classifier, module 37, module 38 scan) was rechecked against the new listings where the two overlap and agrees.
