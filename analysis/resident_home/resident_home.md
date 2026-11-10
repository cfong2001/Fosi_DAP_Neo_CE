# Resident code home hunt

Stock image `DP3_V137.img`, SHA-256 `fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`, re-verified after all work below. Offline only. No patches emitted, no build files touched.

Question: after the module 0 package-gap extension premise was refuted (the gap at exec 0x03079C14..0x0307C7B0 is live FAT/filesystem workspace), where can the five feature code pieces provably live?

The five needs:

| Need | Size | Required context |
| --- | --- | --- |
| M3U parser (`m3u_import`) | 3,601 B | callable from the browser (module 31 up) |
| M3U bridge | ~936 B code + const | browser context, module 31 up |
| Resolver hook code | under ~300 B | module 0 (resident) context |
| Bluetooth toggle replica | 436 B as built (28 B dispatcher hook + 408 B toggle, `work/ui_features/build/scratch/ext.bin` and its map) | module 0 dispatcher context |
| Lock-screen painter addition | part of the ~5–6 KB overlay total | module 31 painter context |

## Bottom line

**No need has a fully proven home today.** Each surviving candidate is missing exactly one proof, and the missing proof is a hardware test in every case. Ranked by how much proof is already in hand:

1. **Resolver hook + Bluetooth toggle: one strong candidate.** The tail at **0x0307BFB4..0x0307C7B0 (2,044 B)** inside the refuted gap is clean under the full disassembly-level census and clear of every documented struct extent in the gap. It is RAM workspace territory with no package backing, so it stays a Phase E canary candidate, not a proven home. It fits only after a forced trim: the staging as designed (1,976 B) plus the measured 436 B Bluetooth blob plus the ~300 B hook estimate totals ~2,712 B against 2,044 B, so the staging must come down to ≤ ~1,308 B (a 12-run, 144-entry layout at 1,192 B works, ~116 B spare). Full arithmetic in §4.
2. **Parser + bridge + lock painter: one strong candidate.** A **module 31 segment extension** has 7,436 B of RAM room (0x0307EE48..0x03080B54) in the right context, resident exactly when its hooks are. It needs two things that do not exist yet: a package rebuild that inserts payload bytes (the framework only patches bytes in place and extends module 0 into its file gap), and a hardware co-residency soak. Proof standard today: strong inference, not proof.
3. **Module 0 dead pockets: exhausted.** The gapless workstream took the only proven-dead space. What remains in the stub farm is 8 bytes in three scraps. The large zero areas elsewhere in module 0 are data tables and runtime workspace, not caves.
4. **Ebook slot (module 30): available, not the best home.** The ebook reader exists and is pinned below (§6). It is a leaf window and safe to remove, but its slot is the shared window VMA (base 0x0307D164, the same base as the browser and player). Code hosted there is evicted by, and evicts, the very contexts that need to call it. It is a good home only for a feature that is itself a window.
5. **Module 7 and the empty records rank below the ebook slot** (§6). The codepage modules 63–69 are not code homes at all.

## Census method

All claims below come from `work/resident_home/census.py`, run over the extracted segments in `extracted/` (file names carry the true exec addresses; `extracted/manifest.json` gives the lengths). Re-run any range with:

```sh
./venv/bin/python work/resident_home/census.py LO HI [--detail]
```

For each queried address, four reference classes are collected:

- **Raw branch decode.** Every code segment is scanned at every halfword offset for BL/B.W encodings (first halfword `(hw & 0xF800) == 0xF000`, second-halfword class in {0x8000, 0x9000, 0xD000}), short B (`0xE000` mask), Bcond (`0xD000` mask, cond not 0xE/0xF), and CBZ/CBNZ (`0xB100` pattern). This decode cannot desync, because it does not depend on instruction boundaries.
- **Literal pools.** A capstone pass (used only for non-branch facts, because a linear sweep desyncs after data pools) resolves LDR-literal pool addresses PC-relative and records the word stored there.
- **ADR targets and MOVW/MOVT pairs** formed to one register, from the same capstone pass.
- **Byte-find.** Every 4-byte little-endian occurrence of the address and of its Thumb form (address | 1), at any offset, in any code or data segment.

Cross-check: the gapless workstream's `work/patches/gapless/tools/refscan.py` (raw halfword branch decode plus byte-find) was run on the contested addresses. The two tools initially disagreed twice, and both disagreements were resolved before any claim was made:

- The first capstone-based census missed the branch references to 0x0305168A (from module 33 at 0x03088EAE and module 61 at 0x03081D76 and 0x03082024). Capstone's linear sweep had desynced in those modules. The final census.py uses raw decode for branches; its farm output now matches refscan and the gapless document exactly, including the live guards at 0x030515BA (branches from module 0 at 0x03050858, 0x0305086A, 0x0305087C) and 0x030515AC (unreferenced in both).
- Byte-find hits inside the core-1 decoder segments (modules 71–80, exec base 0x01000000) are coincidental data words, not references to core-0 SRAM; a decoder cannot address core-0 memory. Where a zone39 hit came only from a decoder segment, it is discarded in the text below and the discard is stated.

A "direct-unreferenced" result is never treated as proof of deadness on its own. Two residuals are handled explicitly per candidate: fall-through reachability (code reached only by sequential execution has no reason to be referenced) and base+offset reach (an address inside a documented struct extent can be reached without ever being named). Jump tables (TBB/TBH) and register-indirect calls cannot be resolved statically in general; no candidate below depends on denying them except where stated.

Census outputs are saved next to this document: `census_farm.txt`, `census_candE.txt`, `census_gapfull.txt`, `census_mod0tail.txt`, `census_zone39.txt`, `census_zone61.txt`, `census_ext31.txt`.

## Candidate 1: module 0 dead space

Range censused: the whole module 0 code segment, 0x03050000..0x03079C14.

### The stub farm is exhausted

The farm at 0x030514F0..0x0305168C is not uniformly stubs. Content inspection of the hex shows real code from 0x03051520 onward and again at 0x03051614..0x03051663, with live branch targets inside both stretches (0x03051544, 0x0305155E, 0x03051584, 0x030515A0..0x030515AA, 0x03051612, and the function entry at 0x0305168A). The census runs that look like pockets at 0x03051520 (36 B), 0x03051546 (24 B), 0x03051560 (36 B), 0x03051586 (26 B), 0x030515BC (40 B), and 0x03051614 (118 B) are interiors of those live functions, reached by fall-through. They fail the proof standard and are excluded.

The genuine stub stretches are the two ends. The gapless patches already occupy 70 B of them (delay cave 0x030514FE..0x03051517, state pair 0x030515B0..0x030515B7, gate cave and pool 0x03051664..0x03051687). What is left, at the same proof standard the gapless workstream used (stub-pattern content, no direct reference under the reconciled census, no fall-through entry because the preceding slot is itself a `bx lr` stub):

| Pocket | Size | Note |
| --- | --- | --- |
| 0x030514FA..0x030514FD | 4 B | contains the return-0 stub at 0x030514FA |
| 0x03051518..0x03051519 | 2 B | one stub slot |
| 0x03051688..0x03051689 | 2 B | one stub slot, adjacent to the live function at 0x0305168A |

Total: **8 bytes.** No feature piece fits. Candidate 1 is closed.

### The other zero areas in module 0 are tables and workspace

- The zero runs at 0x0306E9A7 (338 B) and 0x0306EDD4 (720 B) sit inside a dense rodata table area (59 direct references in 0x0306E900..0x0306F1E8 alone; the bytes immediately before and after both runs are table words such as 0x030542A3 and patterned data). They are zero fields inside tables, not code pockets.
- The 42,584-byte zero run at 0x0306F1E8..~0x03079840 has 53 direct references under the census, including the SAVEINFO mirror buffer at 0x03078824 (4,096 B), a near-periodic series of referenced entries at ~194-byte stride starting at 0x0306F224 (a record array reached by computed index), and the clock table at 0x03079824, whose 36 × 28 B = 1,008 B end exactly at the segment end 0x03079C14. The largest direct-unreferenced holes (10,476 B at 0x03075EFE, 8,424 B at 0x03073E14, 6,922 B at 0x03072308) sit between named bases whose struct extents are unknown. This is the same failure shape as the package gap: a workspace arena with computed addressing. No subrange is proven dead, and the named-base density makes it a worse canary candidate than the §4 tail.

## Candidate 4 first, because it decides the resident needs: the gap tail at 0x0307BFB0

The full-gap census (0x03079C14..0x0307C7B0) finds 24 direct-referenced addresses. Every attributed structure from the resolver census is confirmed referenced: the workspace head (0x03079C14, 0x03079DC8..0x03079DD0), the FAT fields (0x0307A024..0x0307A030, 0x0307A060..0x0307A068, 0x0307A268, 0x0307A276, 0x0307A4D8), the bitmap cache base 0x0307A6D8, the directory stack (0x0307A8DC, 0x0307A8E4), the descriptor table (0x0307AB64, 0x0307AB68), the root cluster global 0x0307BF58, and the standing FS context at 0x0307BF5C. The refutation stands everywhere except the tail.

In **0x0307BFB0..0x0307C7B0 (2,048 B)** the census finds exactly one direct reference in all 82 modules: the word at **0x0307BFB0 itself** (byte-find in module 0 code, the counter-code literal the resolver agent reported). The remaining **0x0307BFB2..0x0307C7B0 (2,046 B)** is direct-unreferenced under all four reference classes.

Documented extents close off the base+offset residual from below:

- The standing FS context at 0x0307BF5C is 42 bytes and ends at 0x0307BF86.
- The second context cell area starts at 0x0307BF86; at the same 42-byte size it ends exactly at 0x0307BFB0.
- The word at 0x0307BFB0 is therefore the next cell, the counter word. Code placed from **0x0307BFB4** starts 4 bytes past it, outside every documented extent in the gap.
- Task stacks and any heap live in module 0 BSS or the overlay BSS window per the resolver census; this range is neither.

Two consequences:

- **The resolver staging header must move.** The resolver design placed its header at 0x0307BFB0 with the playlist flag at header +0. That byte is the live counter word. The header must start at 0x0307BFB4 at the earliest.
- **The range is too small for staging plus both code pieces at full size; the staging must shrink.** Three occupants need the tail: the resolver staging area, the resolver hook code, and the Bluetooth blob. The Bluetooth size is no longer an estimate: the built blob (`work/ui_features/build/scratch/ext.bin`, map in the same directory) is **436 B** total, .text.hook 28 B + .text 408 B, linked back to back with no internal padding, so a relink cannot meaningfully shrink it. The arithmetic against the 2,044 B usable from 0x0307BFB4:

  | Occupant | Size |
  | --- | --- |
  | Staging as designed (16 B header, 20 runs × 50 B, 240 entries × 4 B) | 1,976 B |
  | Bluetooth blob, measured | 436 B |
  | Resolver hook code (design estimate, unbuilt) | ~300 B |
  | **Total as designed** | **~2,712 B, over the 2,044 B by ~668 B** |

  Even staging plus the Bluetooth blob alone (2,412 B) overflows by 368 B, so the trim is forced by measured code, not by the hook estimate. The binding constraint is staging ≤ 2,044 − 436 − ~300 = **~1,308 B**. A layout of 12 runs and 144 entries (16 + 600 + 576 = 1,192 B) satisfies it and leaves ~116 B spare after all three occupants; the entry count is the flexible term if the hook lands larger than its estimate (each entry is 4 B, each run 50 B). The caps are a design choice, and import is all-or-nothing per file, so a smaller cap only rejects more oversized playlists; it does not corrupt behaviour. There is no second arena to move staging to (the resolver census's B2 bounded negative stands), so this trim is the resolution, not one option among several.
- **Placement mechanics for the Bluetooth blob.** The blob as built is linked at the refuted extension base 0x03079C14, and its dispatcher patch (the UI build's scratch patch 0032, a B.W at module 0 0x03061E5E) targets that base. Placing the blob in the tail means relinking it at its tail offset and regenerating that branch target. The UI build's own report states this regeneration is mechanical (its site-patch snippets do it), and the blob's interior is position-relative except for the entry points. The same applies to the resolver hook's two B.W patch sites at 0x03059DAC and 0x0305B2C2 once its code is placed in the tail.

Delivery is the already-built mechanism: the module 0 code-length extension carries a blob across the gap, zeros over the workspace zone (matching the stock don't-care state, since every attributed field in the gap is written before it is read) and code at the tail. The framework's extension step does exactly this mechanically (verify check 8); its previous blob placed code at 0x03079C94, inside the workspace, which is what was refuted. Relocating the same blob's code to the tail is the fix.

**Verdict: best candidate for the two resident needs, proof standard = full direct census plus documented-extent exclusion, still a Phase E canary candidate.** The range is RAM that no module record backs, in a window already shown to be workspace. A clean offline census cannot exclude a computed reach that no document records. The hardware test that settles it is the resolver design's canary, restated for this range: build the tail with a distinctive pattern, boot, exercise card mount, folder playback, a library scan, a settings save, and Bluetooth on/off, then read the range back over Rockusb and confirm the pattern is intact and the one live word at 0x0307BFB0 is the only changed cell.

## Candidate 2: overlay segment extension

### Loader mechanics (what a length change actually does)

The generic loader at 0x0306777A, reached through the wrapper 0x03067870(id, flags), reads the module's 32-byte record (record fetch at 0x03067786..0x030677B6: a 0x200-byte header read, then the record at header + 4 + id × 32), then, per flag bit: bit 0 copies exactly `code_len` bytes from the record's storage offset to `code_exec` (copy call at 0x030677CA..0x030677D2), bit 1 copies the data segment the same way, bit 2 zeroes exactly the declared BSS via the memset at 0x03054E66. There is no overlap check, no eviction bookkeeping, and no unload. Loading is a destructive copy. Growing a record's `code_len` is therefore mechanically safe for the loader: it copies more bytes and touches nothing else. BSS clearing never reaches code space.

The blocker is the file side. Every module payload in the package sits back to back; the sorted payload map shows a gap after exactly one module (module 0, 16,384 B of file space, which is what the existing extension step uses). Module 31's code payload is followed immediately by its own data payload, then the next module's. Extending any overlay therefore requires inserting bytes into the package and shifting every later payload, recomputing each record's storage offset (the manifest shows storage offset = file offset + a constant 50,658,816 across modules), the section offsets after the payload area, and the CRC. The ecosystem tooling in `refs/` performs this class of rebuild; this project's framework does not. That machinery is unproven here, and it is the first of the two missing proofs.

### Module 31's room

Module 31 spans 0x0307D164..0x0307EE48 (7,396 B). Growing it upward, the next bases are module 11 at 0x0307E3C8 (already inside the span's shadow), module 12 at 0x0307F018, module 9 at 0x0307FFDC, and the first base that belongs to a different co-residency class, modules 18/61 at 0x03080B54. Raw room to 0x03080B54: **7,436 B**, against a combined parser + bridge + painter need of ~5–6 KB. It fits, with roughly 1.4–2.4 KB to spare.

Co-residency evidence for that room:

- Every module whose code span intersects 0x0307EE48..0x03080B54 is a window-family module: the window applets at base 0x0307D164 (21, 22, 23, 27, 30, 32, 81 family), module 9's USB window at 0x0307FFDC, and module 9's sub-overlays 11 and 12. Windows are mutually exclusive: the window manager at 0x0306742E loads one window module per activation (module id read from the table at module 0 data 0x030057E0, +0x40 + index × 4, loader called at 0x0306743E), and sub-overlays are loaded by the active window itself. Module 31's only sub-load is the empty module 2.
- The one proven co-resident with the player, module 33 (the playback service), starts at 0x0308837C, well above the room. Modules 34/36 and the codec stubs sit higher still.
- The installer, module 8 at 0x0307E53C..0x0307E954, lies inside the grown span. It is loaded only by module 21 during the update flow, never while browsing or playing. Growing module 31 over it is safe in the browser/player context and irrelevant elsewhere, since the extension bytes are only ever copied when module 31 loads.

Residual risks, stated plainly: the window manager loads by computed id, so the mutual-exclusion argument rests on the window table and the loader-call graph, not on an exhaustive trace of every activation path (a popup-style second window loaded by the manager would break it; none is known, and the known popup family, modules 24–26, is loaded by module 23, not the manager). A grown module 31 also destroys whatever window was resident each time the browser opens, which is already true of every window switch in stock.

**Verdict: best candidate for the parser, the bridge, and the lock painter.** The context match is exact: the extension is resident in exactly the loads where the browser hook, the import path, and the module 31 painter run, with no persistence assumption. Missing proofs: the insertion rebuild, and one hardware soak (build with the extension filled by a known pattern plus a trivial hook; cycle every window including USB and settings, play a track with cover art so modules 18/19/20 load, visit the record window so 29/61 load, return to the browser, and verify the extension bytes and the import path).

### Module 39's tail is not a second home

Module 39's span (0x0307D5FC..0x0309F4AC) has one exclusive subrange: above module 61's end at 0x03094604, no other module's code span reaches. That exclusivity is not enough:

- Module 0 holds computed array bases inside it: 0x03099206 (literal in module 0 code at 0x030547FD and in module 27 at 0x0307D5B3) and 0x0309C024 (literal in module 0 at 0x0306D112, used as an indexed array base by the parameter-setter functions around 0x0306D104). Their extents are unknown.
- Module 39 itself loads pointers 0x0309F48C and 0x0309F49C at seven sites (for example 0x0307DDC6, which reads a word table at 0x0309F48C + index × 4). The top 32 bytes of the span are module 39's own live cells.
- Module 39's sort arena is its BSS (148,756 B at 0x030247F4), not this span, but the span's zero tail beyond its real code end at 0x0307E1EC has no proven non-use between the array bases.

The only subrange with exercised evidence is the sort-keys cave itself, 0x0309F000..0x0309F48C (1,192 B, of which the sort blob uses 1,052 B and ~140 B is free). That is too small for the parser and is already committed. Module 61's exclusive zone (0x0308C978..0x03094604) has 34 direct references under the census and sits in the recording context only; it is dismissed.

## Candidate 3: a dedicated feature module

### The ebook reader, pinned

The reader exists as its own window module. Evidence chain:

- Module 0's code holds a packed window-name table at 0x03067490: MediaLib, MediaBro, Music, Video, Radio, Picture, Record, **Ebook** (at +64, exec 0x030674D0), Browser, Systemset, USB, Charge, MDB, NO THIS TASK.
- The window manager's table (module 0 data at 0x030057E0) holds 15 window module ids at +0x40: [21, 22, 23, 27, 13, 28, 17, 29, 30, 31, 32, 9, 6, 5, 81]. Aligning the names to the ids shifted by one (module 21, the installer/Bluetooth service window, has no menu name) is consistent at every checkable anchor: Browser = 31, Systemset = 32, USB = 9, MDB = 5 (which loads the scan/sort pair 38/39), Record = 29 (which loads module 61), Music = 27 (which loads the playback service 33), and Video = 13 and Radio = 28, both empty records, matching a build with no video or radio function. By that alignment, **Ebook = module 30**.
- Module 30 independently fits: code 8,288 B at 0x0307D164..0x0307F1C4, data 56 B, BSS 2,492 B, a WIN struct whose Service/Key/Paint pointers (0x0307D193, 0x0307D731, 0x0307DB1D) sit inside its own code. It references the extension-table address 0x03005743, the "TXT" entry in module 0's category tables (the only window module besides the browser's own data to do so). It calls the resident text draw 0x030632FA six times and the text position getters 0x0306314A/0x0306316E nineteen times, reads files through the read engine at 0x03058FA8, and its only loader calls are the empty-slot idiom (module 2, five times). It is a leaf text window.

### What reclaiming module 30 would and would not buy

Module 30's slot is the shared window VMA. Every window module loads at base 0x0307D164 or a neighbouring slot base, and loading one destroys the previous. Feature code hosted in module 30's place would exist only while that slot is the active window, and loading it would evict the browser (module 31, same base) that needs to call the parser and the bridge. For the five needs as specified, the slot fails on context, the same failure as every window slot. It would be the right home for a feature that is itself a window (a playlist manager page, for instance), at a generous 8,288 B.

Removal itself is low-risk and buys nothing resident:

- Nothing loads module 30 except the window manager; nothing else calls into its span (its span is shared window space, so inbound references are the manager's table entries, not addresses).
- What a removal must also touch: the menu (name table entry "Ebook" and id slot 30 in the manager's table), and the browser's classification of .txt (module 0's category tables list TXT under the group that activates this window; leaving TXT classified while the window is gone gives .txt files a dead destination). SAVEINFO's last-window state could also name window index 8 and would need the same treatment as any removed window.
- What removal does not free: the codepage modules 63–69 and the text machinery in module 0 are shared. Lyrics, ID3 tags, and file names all render through the same text draw and codepage tables (module 69 carries the GBK table). Deleting the reader frees neither the tables nor the 0x030247C4 data arena, which every window shares. Module 30's BSS (2,492 B at 0x030247FC) overlaps module 23's BSS in the same arena.

**Verdict: merely available, not the best home.** Chase's constraint was that removal is acceptable if space is needed. Space is not what this slot provides; the binding constraint for the feature code is co-residency with the browser and the resident core, and a window slot cannot provide it.

### The rest of the candidate 3 field

- **Module 7** (664 B at 0x0307D5FC, 64 KB BSS at 0x030247EC): role still unknown. It calls only the device-read wrapper 0x030678CA and works through a pointer table inside the FAT workspace (0x0307A024..0x0307A060), which makes it a storage-side worker by behaviour. Repurposing it risks the storage stack to gain a slot in the scanner family's VMA (base shared with modules 37/39), the wrong context for every need. Ranked below the ebook slot on both safety and context.
- **Empty records** (2, 13–16, 28, 43–49, 58–60, 62, 70): no payload, no storage space, and no loader caller except the manager for the two window empties (13, 28). Using one still needs the insertion rebuild and a VMA, and every candidate VMA is a shared slot with the same eviction problem. Module 2 is also the stock "clear slot" idiom and must not be touched.
- **Codepage modules 63–69**: exec address 0, no code/data/BSS split, loaded as data tables to a working buffer by the text path. There is no loader contract that places their bytes at an executable address. Not code homes without a new load path, which is a larger change than any candidate above.

## Per-feature verdicts

| Need | Home | Size vs need | Proof standard met | Residual risk |
| --- | --- | --- | --- | --- |
| Resolver hook | Gap tail 0x0307BFB4.., delivered by the module 0 extension with zeros over the workspace zone | ~300 B (estimate, unbuilt); fits only with staging trimmed to ≤ ~1,308 B (see §4) | full direct census (4 reference classes, reconciled between two tools) + documented-extent exclusion | computed reach no document records; Phase E canary required |
| Bluetooth toggle replica | Same tail, same delivery | 436 B measured (28 B hook + 408 B toggle); inside the same trimmed-staging residue; needs a base relink and regeneration of its dispatcher branch patch | same census | same canary; the dispatcher hook site itself (module 0, patch site 0x03061E5E in the UI build) is in resident code and is not a placement risk |
| M3U parser | Module 31 segment extension (package rebuild) | 3,601 B of 7,436 B room | loader mechanics proven from disassembly; window mutual exclusion from the manager table + loader-call graph | insertion rebuild unbuilt; manager computed-id loads not exhaustively traced; Phase E window-cycle soak required |
| M3U bridge | Same module 31 extension | ~936 B, cumulative ~4.5 KB with the parser | same as parser | same soak; bridge's own blockers (B4 FS-type-3 path) are unchanged by placement |
| Lock-screen painter addition | Same module 31 extension (the painter it extends is module 31's own copy) | remainder of the 7,436 B after parser + bridge, ~2.9 KB | same as parser | same soak; the module 0 painter copy is not extended, so any screen painted outside module 31 keeps the stock lock display |

## What would close the remaining proofs

1. Phase E canary for 0x0307BFB4..0x0307C7B0 (pattern write via the extension build, exercise mount/playback/scan/settings/Bluetooth, Rockusb read-back). Settles the resolver hook and Bluetooth toggle placements.
2. An insertion-rebuild tool for overlay payloads, validated by rebuilding stock with a zero-length change and reproducing the stock image byte for byte outside the CRC. Settles the delivery half of the module 31 extension.
3. Phase E window-cycle soak on an extended module 31 build. Settles the co-residency half for the parser, bridge, and painter.

Nothing in this report requires the ebook removal. If a future feature wants its own window, module 30's slot is the place, and the removal checklist in §6 is the work it needs.
