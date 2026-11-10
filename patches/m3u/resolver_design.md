# M3U bridge: SRAM map, descriptor registrar pin, and resolver hook design

Scope: the last two open items from bridge_completion.md (B2 staging arena, B1b descriptor registrar) and the replacement playback mechanism that bridge_completion.md's refutation of the source-6 fill design calls for. Method: disassembly of the extracted stock modules (capstone listings under completion/), a literal census over every module's code and data, and the package manifest extents. Design and pins only. No bridge code changes, no patches emitted.

Two corrections to bridge_completion.md come out of this pass and are flagged where they apply:

1. The descriptor table element stride is 638 bytes, not 384. The registrar's index math (63 times the index plus 256 times the index, then doubled) gives 638, module 0's dedup loops advance elements by 0x27E (638), and 8 elements of 638 bytes from 0x0307AB68 end exactly at the root cluster global 0x0307BF58. Three independent checks agree.
2. The resolver's table argument is the address of the volume table pointer cell (0x03005714 itself), passed through to the counter functions. Callers load the literal 0x03005714; nobody dereferences it first.

## Job 1: SRAM map and the B2 arena verdict

### How the map was built

Code, data, and BSS extents come from extracted/manifest.json. The package gap between module 0's code end (0x03079C14) and the lowest overlay base (0x0307C7B0) is declared by no module, so its contents were attributed by a literal census: every word in every module's code and data was scanned for values inside the gap, and each hit was traced to its use. Ranges with no literal reference anywhere are marked as having no evidence of use, which is weaker than proof of freeness: a computed pointer could still reach them, and only runtime observation can settle that.

The loader itself is the SoC ROM bootloader working from the package records; module 0 is loaded code, not the loader. Two things the brief asked for are therefore not in the package at all: the initial stack pointer (set by ROM boot code) and the RTOS task stacks. Tasks are registered through per-module data tables (module 33's table at 0x03036990 holds three entry pointers, 0x03089E2F, 0x0308A1CB, 0x0308A927, with no stack fields), and the kernel in module 0 assigns stacks at runtime. Stack extents live somewhere inside module 0's BSS or the shared overlay BSS window and cannot be proven from the image. No heap arena is declared in the manifest, and no allocator was identified among the module 0 exports that overlays call (the exported veneers are event and service calls). Every allocation traced in the filesystem and playback paths is static: the descriptor table, the directory stack, and fixed BSS buffers. A heap may exist, but its existence and extent are both unproven, so it cannot serve as a proven arena either.

### The map

Core 0 SRAM, in address order. Status is A (attributed) or U (unknown or unproven).

| Range | Size | Contents | Status |
|---|---|---|---|
| 0x03000000..0x03004000 | 16,384 | Declared by no module. Boot, vector, and low SRAM territory. | U |
| 0x03004000..0x030059A9 | 6,537 | Module 0 data. Holds the FS ops table at 0x03004438 and the volume table pointer cell at 0x03005714. | A |
| 0x030059AC..0x030247C0 | 126,484 | Module 0 BSS. Named residents include the browser state struct 0x030228A8, DSP runtime state 0x03022AC0 and 0x03022E10, SAVEINFO at 0x030232A0, the PCM ring pointer cells 0x03023928 and 0x03023938, the play context at 0x03023980, and the event bitmap 0x03023CF8. Task stacks and any heap also live in this span or the overlay BSS window, extents unknown. | A with U subranges |
| 0x030247C0..0x03048D68 | ~148,000 | Shared overlay data and BSS window. Overlay groups take turns: module 31 data and BSS from 0x030247C4, module 7 BSS 0x030247EC..0x030347EC (64 KiB), module 38 BSS 0x03024E34..0x03045DDE, module 19 BSS to 0x030368C8, module 33 data 0x030368C8..0x03048D68, module 39 BSS to 0x03048D08, module 36 BSS 0x0304B604..0x0304DE32. Module 35's data declaration overlaps module 0's code range on paper. | A, overlapping declarations |
| 0x0304DE34..0x0304FE34 | 8,192 | Module 40 BSS and codec stub data. | A |
| 0x0304FE34..0x03050000 | 460 | Declared by no module. | U |
| 0x03050000..0x03079C14 | 171,028 | Module 0 code (resident). | A |
| 0x03079C14..0x0307C7B0 | 11,164 | Package gap, pure runtime SRAM in stock. Attributed by census below. | Mixed |
| 0x0307C7B0..0x0309F4AC | ~158,000 | Overlay code windows, bases 0x0307C7B0 through 0x03094604. | A |
| 0x0309F4AC..top | Unknown | Above the highest overlay code end. SRAM top is not proven from the package. | U |

The gap at 0x03079C14..0x0307C7B0, by census:

| Range | Contents | Status |
|---|---|---|
| 0x03079C14..~0x0307A024 | Module 0 workspace head. Five literal sites in module 0 reference the base; one decoded use reads a byte at 0x03079E14 and a word at 0x03079E18. Full extent of the head fields is not pinned. | A, extent partial |
| 0x0307A024..~0x0307A8DC | FAT driver workspace. FS type byte at 0x0307A024 (36 references, modules 0 and 7), volume parameter struct at 0x0307A030 (root cluster word at +0x0D), cluster allocation bitmap cache base at 0x0307A6D8, plus cells at 0x0307A060..0x0307A068, 0x0307A268, 0x0307A277, 0x0307A4D8. | A |
| 0x0307A8DC..0x0307AB1C | Directory stack: header (depth byte at 0x0307A8DC, cumulative count at 0x0307A8E0) plus elements 0..7 at 0x0307A8E4, 71 bytes each. Depth is capped at 7 by the descend function, so 8 elements is the maximum used. | A |
| 0x0307AB1C..0x0307AB64 | 72 bytes. Room for exactly one more stack element, never used given the depth cap. No identified role. | U, bounded |
| 0x0307AB64 | Current directory cluster cell (u32). | A |
| 0x0307AB68..0x0307BF58 | Descriptor table, 8 elements of 638 bytes. See job 2. | A |
| 0x0307BF58 | Current and root directory cluster global (u32), referenced by modules 0, 18, 21, 22, 30, 31, 34, 38. | A |
| 0x0307BF5C..0x0307BF86 | Standing 42-byte current directory FS context. Its first word doubles as the FS type 3 cluster cell; a flag byte sits at +0x0C. | A |
| 0x0307BF86..0x0307BFB0 | Second context cell area (0x0307BF86 referenced by modules 0, 31, 38) and a word at 0x0307BFB0 referenced once from module 0's counter code. Boundary inside this span is not pinned. | A, boundary partial |
| 0x0307BFB0..0x0307C7B0 | About 2,048 bytes. No literal reference in any module's code or data. | No evidence of use |

Core 1 and shared windows:

| Range | Contents | Status |
|---|---|---|
| 0x01000000..0x010162C0 | Decoder code window (modules 70 to 80). | A |
| 0x01020000..~0x0105E9D4 | Decoder data and BSS. The parameter page is the first 144 bytes at 0x01020000. | A |
| 0x40110000 | Message unit peripheral, not SRAM. | A |
| Modules 63 to 69 | Codepage and font data declared at 0-based addresses, loaded elsewhere. Not part of the SRAM map. | A |

### Arena verdict

No range of 6,152 bytes is provably free. The packed staging from bridge_completion.md (512 records plus the bridge's own 2,056 bytes of buffer and statics) fits nowhere that this pass can prove, and no larger unreferenced range exists anywhere in the map: module 0's BSS is large but its unallocated subranges cannot be proven, the overlay window is shared and resident-dependent, and the gap is fully attributed except for one tail.

The largest candidate is 0x0307BFB0..0x0307C7B0, about 2,048 bytes: no literal reference in any of the 82 modules, inside the extension load window (below the lowest overlay base), above the descriptor table and both context cells. The design must shrink to fit it, and its freeness must be proven on hardware in Phase E (canary writes plus a playback soak) before the feature is trusted. If the canary fails, playlist mode degrades to off; there is no fallback arena.

One risk this census raises for the already-merged parser pass, stated here because it belongs on the Phase E list: the composed extension blob (3,729 bytes at 0x03079C14..0x0307AAA5) overlaps runtime workspace the census attributes to stock, including the FAT fields from 0x0307A024, the bitmap cache at 0x0307A6D8, and the head fields at 0x03079E14 and 0x03079E18 that module 0 reads as data. Whether the stock runtime rewrites those fields after load, which would corrupt resident blob code, is not observable offline. The staging area chosen below sits above every attributed range, but the blob itself does not.

## Job 2: B1b, the descriptor registrar is pinned

The resident registrar is module 0 function 0x0305C514.

Contract:

- r0: directory cluster of the file to register.
- r1: pointer to the 11-byte 8.3 name.
- r2: attribute byte (stored into the search dirent at +0x0B before lookup).
- Returns r0: the handle (slot index 0..7), or -1 on failure. Failure cases: table full, the directory resolution at 0x03058638 returning 0xFFFFFFF7 or above, or the entry not found by the lookup at 0x0305BCDC.

Free slot rule: the first slot i in 0..7 whose state byte at 0x0307AB68 + i times 638 is 0. The registrar claims it (state becomes 3 on the FAT path) and fills the element itself, including the directory lookup:

- +0x00: state byte.
- +0x01..+0x0B: the 11-byte name.
- +0x0C: canonical directory key, the output of 0x03058638 on the directory cluster. This is the match key module 0's open path dedups on, together with the name.
- +0x10: file size (bounds-checked by the read engine).
- +0x14, +0x18: cluster pair.
- +0x1C: output word from the 0x0305BCDC dirent lookup.
- +0x20: current position.
- +0x24: cluster.
- +0x254: current cluster cache. +0x258: field. +0x260: flag byte. The FS type 3 path also uses the element's LFN area at +0x22A and fields at +0x26E, +0x272, +0x276.

Design consequence: anything that needs a descriptor calls 0x0305C514; nothing fills a slot directly. The registrar does its own lookup from (directory cluster, name), so a caller never supplies size or cluster fields.

Two boundaries, stated for the record. First, a caller census over every module's BL and B.W immediates finds no direct callers of 0x0305C514: it is reached by a table-driven or wrapped route not identified in this pass. That does not block the design, since the bridge would call it by address with the contract above. Second, module 38's registrar at 0x0307E43C is a different function: it scans the same table for a state byte of 0, sets state 1 (3 if the name starts with "WW"), and fills name, size, and cluster from caller-passed values. It is an overlay variant and is not resident while module 31 is up, so it is not a substitute.

For context, the FS ops table at 0x03004438 holds six thumb entries: 0x030589B7, 0x03058FA9, 0x030594A1, 0x0305CA1D, 0x03058E8F, 0x0305947F. The position and read engine is 0x0305CA1C (thumb 0x0305CA1D): it takes the handle in r3, computes the element with the same 638 math, and tests state bit 1, so state 3 (the registrar's FAT value) takes the cluster chain position path. Consumers reach the table indirectly; its only literal reference in the image is the population site at 0x030545F8.

The resolver hook in job 3 does not call the registrar. It writes the play context descriptor, and module 33's own open machinery performs registration through its stock path. The registrar pin closes B1b and serves any future direct-open design.

## Job 3: resolver hook design

### The stock resolver contract, pinned

Resolver 0x03059DAC(module 0, resident). Arguments: r0 is the flat index, r1 is the out descriptor pointer, r2 is the address of the volume table pointer cell (0x03005714), r3 is the mode (1 for source 6 folder play, 3 for source 0x63).

Behaviour, from the disassembly:

1. It resets the directory stack through 0x03059C76: depth becomes 0, the current cluster cell at 0x0307AB64 and the cell at 0x0307BF86 take the root cluster from the global at 0x0307BF58, and element 0 is initialised for that directory.
2. It walks: while the top element's countA (offset +0x00, a u16 file count from counter 0x0305AB0A) is less than or equal to the remaining index, it subtracts countA and descends through 0x03059B10. Descend refuses to push past depth 7 and pops instead when a directory has no subdirectories.
3. On resolution it writes the out descriptor and returns the residual index, the index within the resolved directory:
   - out+0x00: u32, the resolved directory's cluster (element +0x15).
   - out+0x08: u32, countA + countB of the resolved directory (countB at element +0x02, from counter 0x0305965C, or the FS type 3 pair 0x0305AC92 and 0x03059746).
   - out+0x1C..+0x45: the 42-byte FS context, copied verbatim from element +0x1D.
4. Clamping: an out-of-range flat index does not signal an error. When the walk exhausts the subtree at depth 0, the resolver forces the index to 0 and resolves element 0 (sites 0x03059E00 and 0x03059E52..0x03059E56). Past-the-end wraps to the first entry, silently.

Directory stack element layout, for the staged context format below: +0x00 countA (u16), +0x02 countB (u16), +0x04 cursor (u16), +0x11 parent cumulative count (u32), +0x15 directory cluster (u32), +0x19 a u32 zeroed at init, +0x1D the 42-byte context.

Caller census for 0x03059DAC: module 0 at 0x0305D0A6, 0x0305D41E, 0x0305D458, 0x0305D532, 0x0305D57A, 0x0305D5D8, 0x0305D61C (its own file manager APIs, passing caller-owned structs); module 31 at 0x0307D556 (folder play setup, passing a stack buffer as the out pointer); module 33 at 0x0308A5DE (source 0x63, mode 3) and 0x0308A68C (source 6, mode 1). Only the module 33 source 6 call passes the live play context descriptor: r1 = 0x03023980 + 0x34 = 0x030239B4, r3 = 1.

### What module 33 does with the result

On the source 6 play start path (the event handler block at 0x0308A574), module 33 dispatches on a byte at +0x61 of its session struct. Values 0, 1, 2 take the single-directory fetch 0x0305B2C2 with the current ctx+0x34 cluster (call site 0x0308A6C6, mode 1); other values take the resolver (call site 0x0308A68C). Either way, afterwards:

- The returned index is stored to [ctx+2] and [ctx+6].
- [ctx+0], the total, is recomputed: on the resolver path it becomes countA of the resolved directory (0x0305AB0A on the resolved cluster, or 0x0305AC92 on the copied context at ctx+0x50 for FS type 3); on the single-directory path it becomes the subtree total from 0x03059D58.
- The open machinery materialises the entry from (cluster at ctx+0x34, returned index, context at ctx+0x50). That triple is the complete currency downstream.

End of list is module 33's decision, not the resolver's. The auto-advance (event 0x56 path at 0x0308A4DC) increments the index and, when it reaches [ctx+0], stops playback through 0x03089AD6 and the 0xEC event, which resets the index to 0. The resolver itself never reports end of list.

### Hook sites

Primary hook, at the resolver entry. Stock bytes at 0x03059DAC are 2D E9 F0 47 (push.w {r4, r5, r6, r7, r8, sb, sl, lr}, 4 bytes). Replace with a B.W to the hook entry in the extension (displacement about 0x1FE68, well inside the B.W range). The hook:

1. Tests the playlist flag first (one LDRB and one CBZ). If clear, it executes the displaced push.w and branches back to 0x03059DB0. Non-playlist cost is one branch pair and one byte load.
2. If the flag is set, it tests the discriminator: r1 equals 0x030239B4 and r3 equals 1. Any mismatch takes the same stock fallback. This excludes module 31's setup call (stack out buffer), module 0's internal calls (caller-owned structs), and module 33's source 0x63 call (mode 3), each by a property observed at its call site.
3. On a match it performs the substitution below and returns directly with BX LR, using only caller-saved registers (r0..r3, ip). It never ran the stock prologue, so it owes no stack cleanup.

Companion hook, at the single-directory fetch 0x0305B2C2, whose entry bytes are also 2D E9 F0 47 (fallback returns to 0x0305B2C6). This hook exists because module 33's path B cannot change directories: it fetches within the cluster already at ctx+0x34. In playlist mode the next entry may live in another directory, so path B must be intercepted too. Discriminator: flag set, r3 equals 1, and r1 equals the cluster of the run containing the last served entry. On a match it runs the same substitution, writing ctx+0x34, ctx+0x3C, and ctx+0x50 in the play context directly (the context address 0x03023980 is a constant), and returns the target entry's within-directory index, which is what path B's callers store. On any mismatch it falls back to stock.

### The playlist flag

The flag is a byte in the extension's own state area: staging header offset +0, at 0x0307BFB0. Two candidate homes were considered:

- A SAVEINFO verbatim byte (+0x1C7..+0x2D5). Rejected. SAVEINFO persists to flash when settings save, so a stale flag could survive a power cycle and make the first stock folder resolution after reboot substitute against an empty staging table. The verbatim range is also copied and restored by settings paths whose writers are not fully traced, so the flag could desync from the staging table it describes.
- The extension state byte. Chosen. It is package-loaded with its initial value 0 at every boot, so playlist mode always starts off and is armed only by an import in the current session. It is written by one writer (the bridge) and read by both hooks at a fixed address. The cost is that the flag does not persist across reboot, which matches the design: playlists are imported per session when the .m3u file is opened.

### Substitution semantics

The hook keeps the playlist position itself, in the staging header: p, the index of the entry most recently served, plus the residual it returned. This is necessary because stock overwrites [ctx+2] with the within-directory residual after every resolution, so the incoming index on later calls is a residual, not a playlist index. The hook maps the incoming index i against the last served residual j:

- i equals j + 1: serve entry p + 1 (auto-advance or next).
- i equals j - 1: serve entry p - 1 (previous).
- i equals j: serve entry p again (resume, repeat one, seek restart).
- Anything else: treat i as a playlist index directly (a fresh selection, for example from the UI) and clamp it into [0, count - 1].

The first call after import is a special case of the last rule: the bridge sets [ctx+2] to 0 and p to none, so the hook serves entry 0.

Serving entry p means writing the out descriptor in exactly the stock format and returning the entry's within-directory index:

- out+0x00: the entry's directory cluster (its run's cluster).
- out+0x08: the run's countA + countB, captured at import.
- out+0x1C..+0x45: the run's 42-byte context, captured at import from the enumeration block the bridge already holds for that directory (the same bytes the stock initialiser copies into stack elements).
- Return value: the entry's within-directory index.

Index clamping mirrors stock where stock has a rule and stops where stock stops. A fresh selection clamps into range. Forward motion past the last entry must not wrap silently the way the stock resolver wraps a flat index, because module 33 has its own stop logic and a wrapped serve would loop the playlist without the user's repeat setting asking for it. The hook therefore serves a past-the-end sentinel for p + 1 equal to count: the last run's cluster and context, with the returned residual set to that directory's countA (one past its last file). Module 33's advance comparison and its fetch failure path then end playback. Which of the two fires first, and whether the result reads as a clean stop or an error stop, is not distinguishable offline; it is a named Phase E check below.

Previous direction needs no separate mechanism. Module 33 presents a decremented index to the same two fetch points, and the j - 1 rule serves it. Both directions and the auto-advance all pass through the two hooks, and no other fetch point consumes (cluster, index) for source 6: the completion pass pinned the full set (resolver 0x03059DAC, single-directory fetch 0x0305B2C2, total counter 0x03059D58, which reads no per-entry data and is safe to leave stock).

Inertness for non-playlist playback is structural, not incidental. With the flag clear, both hooks are a byte test and a branch back. With the flag set, the discriminators still exclude every observed non-source-6 caller. Source 6 folder play with the flag set but no import in progress cannot occur, because the bridge sets the flag only after staging is complete and clears it when the playlist is dismissed.

### Staged record layout, against the arena verdict

The arena is 2,048 bytes at 0x0307BFB0..0x0307C7B0 (extension offset 0x239C). The layout spends 1,976 of them:

| Part | Layout | Bytes |
|---|---|---|
| Header | +0 flag byte, +1 entry count (u8), +2 current position p (u16, 0xFFFF = none), +4 last served residual (u16), +6 run count (u8), +7 reserved, +8..+15 reserved zero | 16 |
| Run table | Up to 20 runs, 50 bytes each: u32 cluster, u16 countA, u16 countB, 42-byte context | 1,000 |
| Entry array | Up to 240 entries, 4 bytes each: u16 within-directory index, u8 run id, u8 flags (bit 0: FS type 3 directory) | 960 |

Entries stay in playlist order; runs group entries by directory, since a playlist's entries usually span few directories and the 42-byte context is per directory, not per entry. The caps are a reduction forced by the verdict: 240 entries and 20 directories, down from the 512 records in bridge_completion.md. Import behaviour at the caps: entries or directories beyond the caps are not staged, the flag stays clear, and the .m3u opens with stock behaviour (the browser hook treats it as an unsupported file). A partial playlist that silently drops tracks is worse than no playlist mode, so the rule is all or nothing per file.

The 2 KB playlist text buffer in the bridge's own accounting is not part of this resident staging. It is needed only during import, inside the browser window; where it lives is a bridge-side decision for the build pass and does not change the arena math here.

## Open risks and Phase E checks

1. Arena freeness. 0x0307BFB0..0x0307C7B0 has no evidence of use, not proof. Gate: canary the full 2,048 bytes across a boot, a folder play session, and a settings save, and confirm the bytes survive untouched before trusting staging there.
2. Extension and workspace overlap. The resident blob already overlaps attributed FAT workspace (see job 1). Gate: confirm on hardware that the blob's code survives a mount and a long playback session; if the runtime rewrites those fields, the extension base or the workspace users need rework before any of this design ships.
3. Stop behaviour at end of playlist. The past-the-end sentinel relies on module 33 treating a one-past-the-last residual as end of list. Gate: on hardware, play a two-entry playlist to completion and confirm a clean stop with no error state and no wrap.
4. Index bookkeeping sequence. The exact order in which module 33's advance mutates the index across its session struct and the play context was traced at the fetch points but not as one continuous sequence. The state machine's +1, -1, and equal rules cover every presentation the stock code can make at either hook, but a full traversal (next across a directory boundary, previous, end) must be exercised on hardware before the design is called proven.
5. Registrar call route. 0x0305C514 has no direct callers in the image, so its contract is read from its own code alone. It is not on the resolver hook's path; this matters only for a future direct-open design.

## Correction from the tail build (2026-10-31)

The companion hook's discriminator above originally named r0 as the
cluster argument. The tail build (patches/m3u/tail_build.md) proved
from the module 33 call site at 0x0308A6BA that the single-directory
fetch receives r0 = [ctx+2] (the index) and r1 = [ctx+0x34] (the
cluster), and the fetch's own body reads the cluster from r1. The
discriminator in the companion paragraph is corrected to r1, and the
built hook implements r1. The build also exercised the traversal in
risk 4 end to end in emulation (next across a directory boundary,
previous, end-of-playlist sentinel on both hooks), which narrows that
risk to the hardware confirmation; risks 1 to 3 stand as written.
