# Fosi DAP Neo (DP3_V137): library / scan / sort machinery and M3U feasibility

Scope: stock firmware update image `DP3_V137.img` (13,631,492 bytes, SHA-256
`fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`), RKnano package,
82 overlay modules. All analysis offline, static (capstone disassembly + string/byte
search). Addresses are execution addresses in the image's load map;
`file_offset = load_addr − 0x03050000 + 0x200` for module code/data.
Evidence is marked **[proven]** (bytes/instructions observed) or **[inference]**.

Companion scripts in this directory: `search_terms.py` (+ `search_terms_output.txt`),
`strings_module.py`, `disasm_module.py` (disassemble one module by index; the shared
`work/main/disasm.py` picks the *first* module matching an address and is wrong for
the shared `0x0307d164` overlay window).

---

## 0. Verdict summary

- **M3U verdict: no playlist file format exists in this firmware.** No M3U/M3U8/PLS/
  XSPF/PLA parser, extension entry, or string anywhere in the image (reproducible
  negative, §1). "Playlists" in the UI are four fixed internal lists (Playlist A–D)
  plus one favourites list, stored as records in a raw-sector database on the
  internal system flash, not as files. An M3U importer is therefore new code, but
  it has three concrete targets to write into (§4).
- Track-list record: the library is a sector-addressed database. The sortable
  record is 14 bytes: two leading u16 fields the comparator never reads,
  the first 4 characters of the sort key stored inline as uppercased UTF-16,
  and a u16 index of the full key string in the database (§2.3). Correction
  (from the sort-keys work, patches/sort_keys/sort_keys.md): the comparator
  compares no category fields anywhere; what an earlier draft called
  category fields at comparator offsets +0/+2 are key units 0 and 1. Playback resolves a record to a file via a
  `(clus, index)` pair (§3.2).
- Sort routine and key: module 39 is the sort engine. Sorting is by *insertion
  into linked lists* with comparator `0x0307d620`: compare u16 fields at +0, +2,
  then the inline key characters at +4, +6; on a tie past the second character it
  reads both full key strings (up to 128 UTF-16 chars) from the flash database and
  compares them raw. Case folding (ASCII a–z → A–Z) is applied when keys are
  built, not in the comparator; non-ASCII keys pass through a pinyin/collation
  table (§2.4).
- Scan modules: enumeration/filter in modules 31 and 38; metadata/cover parser in
  module 18; sort-key builders + comparator in module 39; database address bookkeeping
  ("SortInfo") in module 23; play-context builder in module 24; browsers in modules
  27, 31, 34; CUE parser in module 37.

---

## 1. Task 1: M3U / playlist-format search (reproducible negative)

### Method

`search_terms.py` lowercases both haystack and needle and searches the raw bytes
of the whole image and of each module's code+data separately in three
encodings: ASCII, UTF-16LE, UTF-16BE. (The UTF-16BE hits it reports for UI words are
+1-byte-offset aliases of the UTF-16LE strings; an artifact, not independent
evidence.) Separately, all 21 language tables were dumped with
`rknano_image.py … lang <0..20>` (266 strings each, fixed IDs across languages) and
searched for playlist/favourite/recent/history concepts, and all printable strings
in the trailing resource-name table (file `0xc86d9a`…) were extracted.

### Results

| term | ASCII | UTF-16LE | UTF-16BE | notes |
|---|---|---|---|---|
| `m3u` | 1 | 0 | 0 | the single ASCII hit is at file `0x2ea3`, inside module 65's CJK conversion **data** table, high-entropy bytes, not a string or code reference |
| `m3u8`, `#EXTM3U`, `.pla`, `.pls`, `xspf` | 0 | 0 | 0 | none |
| `.mp3` `.flac` `.ape` `.dsd` `.m4a` `.wav` `.lrc` `*.mp3` | 0 | 0 | 0 | extensions are stored **dotless** as 3-char codes (§2.1), so dotted searches are the wrong probe, the negative holds via the extension tables, not via these searches |
| `playlist` | 0 | 36 | (aliases) | **all** hits are language-resource UI strings (IDs 85, 94–97, 99–106 and translations) |
| `favorite` / `favourite` | 0 / 0 | 19 / 0 | (aliases) | all UI strings (IDs 88, 98, 107 + translations) |
| `recent` | 0 | 0 | 0 | no recently-played concept in any language |
| `history` | 2 | 0 | 0 | module 77 (second-core ALAC-family decoder), file `0x1554ed`/`0x155501`: `rice_initial_history =%d`, `rice_history_mult = %d`, codec internals, unrelated |
| `medialib` | 1 | 8 | (aliases) | ASCII hit in module 0 code, file `0x40b3c`: UI element name `MediaLib` among `MainMenu`, `MediaBro`, `Music`, `Video` |

**Conclusion [proven]:** no M3U/M3U8/PLS/XSPF/PLA file support exists. The playlist
concept exists only as internal lists (§3). There is also no "recently played" list
anywhere, with no string and no UI entry in any of the 21 languages.

### UI surface (English = language 2; IDs are fixed across all 21 tables)

Media library menu (IDs 78–108): 78 `MediaLib Update？`, 79 `medialib`,
80 `Now Playing`, 81 `All Songs`, 82 `Select Artist`, 83 `Play Album`, 84 `Genres`,
85 `Playlists`, 86 `Folder`, 87 `RECORE FILE` [record files], 88 `My Favorite`,
89 `Update media library`, 92 `Breakpoint player`, 93 `Title`,
94–97 `Playlist A/B/C/D`, 98 `Add to favorite`, 99–102 `Added to list A/B/C/D`,
103–106 `Removed from list A/B/C/D`, 107 `Clear favorite list`, 108/116/141
`Updating Library` / `Update media library`, 122 `Scanning…`, 142 `Media library updated`.
Play modes (151–156): `Order`, `Repeat All`, `Repeat Folder`, `Repeat One`, `Shuffle`
(+ one blank). Resume modes (157–160): `Song`, `Position`, `off`.
Volume labels (69–72): `C:FLASH`, `D:FLASH`, `D:SD CARD`, `E:SD CARD`.

Resource-name table (file ≈`0xc86d9a`–`0xc92da2`, names of the `ROCK26IMAGERES`
bitmaps; `(x,y)` in the name is the fixed blit position) confirms the same menu and
the redraw model (§5): `A_ALLMUSIC_(12,30).BMP` (file `0xc88906`), `A_SINGER_`,
`A_ABLUM_` [sic], `A_GENRE_`, `A_LIST_`, `A_MEDIA_RECORDFILE_`, `A_MYFAVO_`
(`0xc88b8e`), `A_MEDIAUPDATA_`, `A_BREAKPOINT_PLAY_`, `A_NOWPLAY_`, each in plain /
`_RED` / `_Y` variants over `A_MEDIA_ITEMBARBACK_(20,29)`. Browser rows use
`A_BROWSER_FILETYPE_{FOLDER,MUSIC,VIDEO,TEXT,PICTURE,OTHER}` icons.
`A_MEIDASORTBAK0..8_(40,64).BMP` (nine sort-dialog backgrounds, `0xc8c5c6`…) show a
sort-selection screen exists in the stock UI.

---

## 2. Task 2: the library scan

### 2.1 Extension filter [proven]

Module 0 data at exec `0x030056be` (file offset `0x16be`; duplicate copies at data
offsets `0x16e9`, `0x1714`), 14 dotless 3-char codes:

```
MP1 MP2 MP3 WMA WAV APE FLA AAC M4A OGG MP4 3GP DFF DSF
```

Note `FLA`, not `FLAC`. The same table sits in module 31 code at `0x0307e110` and in
module 38 code at `0x0307e6cc`. Module 38's copy has `CUE` appended (15 codes).
Module 0 data also has `JPGJPEBMP` (pictures). Module 31's browser function at
`0x0307deb8` copies the table to its stack frame (44 bytes from `0x0307e110`) before
filtering. This is the scan/browser accept-list. Anything not in this table is
invisible to both the file browser and the library scan; `.m3u` fails here first.

### 2.2 Who does what [proven strings/code; role labels are inference from them]

| module | exec window | evidence | role |
|---|---|---|---|
| 0 | `0x03050000` | FS (module-0 `0x030611e0` is called by every overlay to acquire the FS context), UI element names, ext table, ID3 genre table | resident kernel: FAT FS, GUI, drivers |
| 31 | `0x0307d164` | ext table at `0x0307e110`; `xxxxxxxxxx From File: AudioFileNum = %d` (ADR ref `0x0307e2b8`); walks a node list rooted at `0x030228a8`, compares **11 bytes** at node `+0x4f` (an 8.3 name); writes play-source codes 6 / `0x63` into play context `+0xf2` | file browser + "play from file/folder" |
| 38 | `0x0307e290` | ext table + `CUE` at `0x0307e6cc`; data strings `U:\RECORD \VOICE`, `U:\RECORD ` | media-file enumeration (scan walk) |
| 18 | none | `ID3`/`TDAT`, `APETAGEX`, `OggS`, `fLaC`, Vorbis comment fields, `image/bmp`, `PICTURE OGG` | metadata + cover-art parser (ID3v2, APE, Vorbis/FLAC) |
| 37 | `0x0307d5fc` | `CUE Can't read content\n` (`0x0307db18`), `CUE end i = %d \n`, `cue_info->m_total_Song == %d\n` (`0x0307db48`); its data (320 B at `0x030247ec`) holds UTF-16LE ASF field names `WM/Title`, `WM/Author`, `WM/AlbumTitle`, `WM/Genre`, `WM/Track`, `WM/TrackNumber`, `WM/PartOfSet`, `WM/TitleSortOrder`, `WM/ArtistSortOrder`, `WM/AlbumSortOrder` | CUE-sheet parser; also the WMA/ASF tag field map |
| 23 | `0x0307d164` | `SortInfoAddr.ulFileSortInfoSectorAddr = %d` (`0x0307dfac`), ` totalFmfile = %d`, `Play All Album`, ` TotalFiles is --- %d ---`; data `U:\RECORD \FM` | SortInfo address bookkeeping; FM/record counts |
| 24 | `0x0307e9c0` | §3.2 | builds the play context for a chosen library list |
| 27 | none | ` TotalFiles is --- %d ---`, ` CurrentFileNum == %d `, `.LRC` string | browser/list overlay (also lyrics) |
| 34 | `0x0308bed4` | ` SysFileInfo->CurrentFileNum == %d `, `ERROR!!! CurrentCodec == 0x%02x` | browser overlay; a `SysFileInfo` struct exists |
| 39 | `0x0307d5fc` | §2.4 | **sort engine** (key builders + comparator + sorted insert) |
| 63–69 | data only | BIG5/GBK/SJIS/KOI8/ISO-8859 conversion tables | codepage conversion for names/tags |

Module 0 code embeds tag field names at `0x1a33c`+ (`Artist`, `Album`,
`Album Artist`, `Genre`, uppercase duplicates at `0x1a770`+), `id3 ` at `0x19e4c`,
`ID32` at `0x1c084`. Tag parsing is split between module 0 and module 18.

### 2.3 Where the list lives: a raw-sector database, not a file [proven]

No database filename exists (no `.db`/`.dat` medialib name in any string search).
Module 23's function at `0x0307de14` builds a `SortInfoAddr` struct in RAM at
`0x03024808` from a base sector stored at `[0x0302329c]` and a category selector
halfword at `[0x030235c0]` (values 1–7): struct `+0` = base; `+4…` = halfword
capacities (`0x400`/`0x500`/`0x600`/`0x700`); `+0xc…` = u32 sector addresses of the
form base + `0x14000` + {0x20, 0x40, 0x80, 0x160, 0x4a0, …}. That is one sector
region per library list (All Songs, Artist, Album, Genre, Playlists, Favourites;
the exact selector→list mapping is [inference] from the UI order).

All database I/O goes through module-0 function `0x03067510` with device selector
`0x00030001`, the same device-3 channel the firmware updater (module 8) writes
through. [Inference]: device 3 is the internal system/NAND area, so the library
database lives in raw sectors outside the FAT volumes, persists across boots, and
is rebuilt only when the user runs *Update media library* (IDs 78/89; progress
strings 108/122/141, completion 142). Nothing found suggests an incremental or
boot-time rescan.

RAM-side, a list header lives at `0x03024f78` (halfwords: `+0` total, `+0xa`
category count, per-category counts at `+0x2+i*2` and `+0xc+i*2`), and the sort
working set is an array of 14-byte records at `0x03024d08` inside module 39's large
BSS arena (`0x030247f4`, 148,756 bytes declared).

### 2.4 The sort: module 39 [proven from disassembly]

Module 39's header claims 138,928 code bytes; the last nonzero byte is at
+0xbf0. That is 3,056 bytes of real code; the rest is zero padding.

Functions:

- `0x0307d5fc`: ASCII uppercase of one char (`c−'a' ≤ 0x19 → c−0x20`).
- `0x0307d608`: case-folded char difference using the same fold (used elsewhere;
  the record comparator below does not call it).
- `0x0307d620`: record comparator, returns 0/1/2 (less/equal/greater):
  1. compare u16 at record `+0`, then `+2`, then `+4`, then `+6`;
  2. if the `+6` field is 0, records are equal (return 1);
  3. otherwise compute both full-string addresses
     `((base + data[1]) << 9) + (record[+8] << 11) + data[0]`
     (base = `[0x0302329c]`, data = module 39's 8-byte data at `0x030247ec`),
     read `0x100` units of each via `0x03067510` (device `0x00030001`) into cached
     buffers at `0x0307f28c` / `0x0307f38c` (cache state at `0x0307e1ec`), and
     compare up to 128 UTF-16 code units, raw, with no case folding at compare time.
- `0x0307d6ea`: sorted insertion of a record into one of two linked lists whose
  heads live in the state struct at `0x0307e1ec` (+0, +4), ordered by `0x0307d620`.
  Sorting is therefore insertion sort at scan time, not a post-pass.
- `0x0307d786`: builds the non-ASCII collation table at `0x0307e1fc`: `'A'…'Z'`,
  then `0x4dff`, then a generated CJK range starting at `0x4e00`, a pinyin-style
  first-character bucketing for Chinese titles.
- `0x0307d80a` / `0x0307d8c4`: sort-key builders. They walk the 14-byte record
  array at `0x03024d08` (stride `0xe`), read 8 bytes (4 UTF-16 chars) of each
  record's name string from the database (builder B reads a 16-byte name entry at
  16-byte stride first, mode 1 bases {0x10000, 0}, mode 2 bases {0x14000,
  0x10000}, the same `0x14000` region offset as in SortInfo), uppercase ASCII
  letters inline, and store into the record.

Sort record layout (14 bytes) [proven fields; two roles flagged]:

| offset | type | meaning |
|---|---|---|
| +0x0 | u16 | leading field 1: not read by the comparator (the comparator is called with record+4, so its units start at +0x4); role unproven |
| +0x2 | u16 | leading field 2: not read by the comparator; role unproven |
| +0x4 | u16[4] | first 4 chars of the sort key, UTF-16, ASCII-uppercased at build time (only +4/+6 are used by the comparator's fast path) |
| +0x8 | u16 | also read by the comparator as the **full-string index** into the database string area (address arithmetic above). Whether +8 does double duty as key char 3 in the builder layout or the two layouts differ is **unresolved** |
| +0xc | u16 | index stored by the builders (from a side table / caller argument) |

Sort key [proven]: *(field+0, field+2, key string)* where the key string is
whatever name the scan stored for that list: tag title for songs, artist name for
the artist list, etc. [inference: which tag feeds which list was not traced to the
scan writer]. Case-insensitivity is by pre-folding at build time plus the
collation table for CJK; the comparator itself is case-sensitive on the folded
data. Numbers are compared as raw UTF-16 code points. There is no natural-sort
("Track 2" vs "Track 10") handling anywhere in the comparator.

Callers of `0x0307d620`/`0x0307d6ea`: none of the browser overlays (23, 27, 31,
34, 38) contain a direct branch or literal reference to these addresses [proven by
grep over their disassemblies]. Cross-overlay calls can't be direct branches (the
windows overlap), so the sort engine is driven through the overlay manager during
the scan, most plausibly by module 0 / the scan coordinator [inference].

### 2.5 Scan flow (synthesis; steps individually evidenced above)

1. Enumerate both volumes; accept files whose dotless 3-char extension is in the
   table (modules 31/38; 8.3 directory nodes carry an 11-byte name at node +0x4f).
2. Parse tags (modules 0/18; module 37's ASF map for WMA).
3. Write per-list records + key strings into the sector database (SortInfo regions).
4. Build folded 4-char key prefixes and insertion-sort each list (module 39).
5. Persist; UI counts come from the RAM list header at `0x03024f78`
   (`TotalFiles`, `AudioFileNum`, `SysFileInfo->CurrentFileNum` diagnostics in
   modules 21/23/27/31/34).

---

## 3. Task 3: existing sequential-play structures (M3U targets)

### 3.1 What exists [proven]

- Playlist A–D (UI 85, 94–97): four user lists, add/remove with confirmations
  (IDs 99–106). My Favorite (88, 98, 107): one favourites list, clearable.
  Both are database lists like the category lists (§2.3), with the same SortInfo
  machinery and the same record format; they are the natural target for an importer.
- Folder play / Play All Album: module 23 string `Play All Album`; module 31
  plays from the browser by writing a source code into the play context
  (`+0xf2` = 6, or `0x63` when a mode halfword at `[0x03025928+4]` equals 3).
- Play modes (UI 151–156): Order / Repeat All / Repeat Folder / Repeat One /
  Shuffle. Sequencing is a mode over whatever list is loaded, not a queue object.
- Breakpoint resume (UI 92, 157–160): resume by Song or by Position.
- CUE sub-tracks: module 37 parses a `.cue` file into a `cue_info` struct with
  `m_total_Song`. That is the one existing precedent for "text file → ordered
  sub-track list", and the closest model for an M3U parser.
- A–B repeat: present as now-playing bitmaps (`A_MUSIC_A_B_MODE_…`). It is a
  time-range state in the player, not a list; not a useful importer target.
- No play queue, no recent-played list (§1).

### 3.2 The play context and the per-track playback record [proven]

Module 24 (`0x0307e9c0`, single function, frame `0x23c`) builds the play context at
`0x03023980` for the category in `[0x030235c0]` (values seen: 1,2,3,4,5,7,8,9,
100):

- per-category counts are fetched by calling `0x0307dda8` (co-resident overlay)
  with a sector address from `SortInfoAddr + idx*4 + 0x10`, an index, and mode 1/2;
  it logs `All Album TotalNum = %d`;
- the selected track's record is fetched by module-0 `0x0306c7ac` (buffer
  `0x03024f98`, `[SortInfo+0]`, `[SortInfo+0xc]`) and logged as
  `st.clus = %d, st.index = %d` (string at `0x0307edb4`);
- final context fields: `+0` = total (u16), `+2` = current index within category,
  `+6` = same, `+0x10` = constant from `[0x03005714]`, `+0x44/+0x48/+0x4c` = record
  fields `+0x10/+0x14/+0x18`, `+0xf2` = category/source code, `+0xf8` = SortInfo
  base, `+0xfc` = `[SortInfo+0xc]`, `+0x100…` and `+0x110…` = two parallel
  per-category u16 arrays copied from the list header.

Playback record layout (partial, from the fetch in module 24):

| offset | type | meaning |
|---|---|---|
| +0x00 | u32 | `clus`, starting cluster of the file on its volume |
| +0x04 | u32 | `index`, index (directory-entry ordinal) |
| +0x10 | u32 | copied to play context +0x44 (unproven semantics) |
| +0x14 | u32 | copied to +0x48 |
| +0x18 | u32 | copied to +0x4c |

This is the key constraint for any importer. The firmware does not reference
tracks by path at play time. It references them by (cluster, index) into the
filesystem. A playlist entry is only playable once resolved to a scanned file's
(clus, index) pair (categories 8/9 in module 24 take an extra validation path
through `0x030570e8`/`0x03057040` with buffer `0x03036988`; category 8 also
loops `0x0305aa18` per entry; exact roles unproven).

---

## 4. Task 4: M3U feasibility

### What breaks

1. Extension gate. `.m3u` is rejected by the dotless 3-char filter before any
   parser could see it (§2.1). Fix surface is small and known: add `M3U` to the
   tables at module 0 data `0x030056be` (+ its two duplicate copies), module 31
   `0x0307e110`, module 38 `0x0307e6cc`.
2. Path model mismatch. Internal structures use drive-prefixed UI labels
   (`C:FLASH`, `D:FLASH`, `D:SD CARD`, `E:SD CARD`) and internal paths like
   `U:\RECORD \FM`, with backslash separators and 8.3 space-padded components
   (`RECORD` + 5 spaces = 11 chars, matching the 11-byte node names in module 31),
   while the database stores display names as UTF-16 (up to 128 chars compared).
   A computer-made M3U uses `/` or `\`, long names, and usually relative paths.
   The importer must resolve each line against the .m3u's own folder and volume,
   then match it to a scanned file to obtain its (clus, index). Unresolvable lines
   (file not in the library, wrong volume) have no representation.
3. Two volumes. One SortInfo base pointer (`[0x0302329c]`) is visible in the
   sort code; which record field disambiguates internal vs TF storage is unproven
   (candidates: sort record +0/+2). Cross-volume playlists are the risky case.
4. Encoding. M3U is conventionally ANSI/UTF-8, M3U8 is UTF-8. The firmware's
   conversion tables (modules 63–69) are legacy codepages (BIG5, GBK, SJIS, KOI8,
   ISO-8859 family) feeding UTF-16; no UTF-8 decoder was identified [negative:
   no UTF-8 table among the data modules; not exhaustively proven]. Non-ASCII
   track names in a UTF-8 playlist would need a new converter, and the resulting
   UTF-16 keys must then pass the same fold/collation path as scanned names.
5. Ordering. Imported order is *not* preserved by the library lists: module 39
   insertion-sorts everything by key. An importer that writes into Playlist A–D
   gets alphabetical playback unless it also controls the sequencing (below).

### Where a parser could hook: three options, ranked

1. Browser-open hook (best fit). Treat `.m3u` like `.cue`: module 37 already
   parses a text file into an ordered sub-track list (`cue_info.m_total_Song`).
   A sibling parser overlay could parse the M3U on open, resolve entries to
   (clus, index) via the same directory walk module 31 uses, and load the play
   context (`0x03023980`) directly, preserving file order and requiring no
   database writes. Cost: entries must resolve at open time; no persistence.
2. Import into Playlist A–D / Favourites. Write database records in the
   existing format during a scan or an "import" action. Persists and reuses all
   UI, but order is lost to the sort (§2.4) and the write path into the sector
   database (the scan writer) is the least-understood code in this track.
3. Scan-time sidecar. During MediaLib Update, treat each `.m3u` as a virtual
   album/folder whose tracks are its entries. Most integrated, most new code in
   the scan path.

Option 1 mirrors an existing, proven pattern (CUE) and avoids the database
entirely; it is the recommended first implementation.

---

## 5. Task 5: navigation limits, proven vs guessed

Proven limits

- Sort key is a pre-folded prefix + raw string compare. Only the first 4 chars
  are inline; ties fall back to reading both full strings from flash (cached, one
  sector each). That is fine for correctness, but the key is a *single* name string
  per list. There is no multi-key sort (e.g. artist→album→track): the
  comparator compares key units only, no category fields, and there is no
  numeric awareness.
- Lists are fixed and precomputed. Seven-ish category regions with fixed
  sector capacities (`0x400`–`0x700` halfword counts in SortInfo); new list types
  mean new regions, not a query.
- Stale by design. The database changes only on manual *Update media library*;
  files added to the card are invisible to library views (but visible in Folder
  browse) until then.
- Redraw is bitmap blitting at fixed coordinates. Every screen element is a
  named bitmap with its `(x,y)` baked into the resource name; list rows are an
  item-bar bitmap plus drawn text. There is no layout engine to extend. Richer
  rows (e.g. two-line title+artist) mean new bitmaps and new blit code.
- Titles come from tags when parsed (modules 0/18 handle ID3/APE/Vorbis/ASF);
  the sort/display string area holds one string per record per list.

Guesses (labelled, not established)

- Which tag (title vs filename) feeds the All Songs key string; whether untagged
  files fall back to filename in the same string area.
- Exact semantics of sort-record fields +0/+2 and playback-record fields
  +0x10/+0x14/+0x18; the category-number→UI-list mapping (1–9, 100) is inferred
  from UI order, not traced.
- Whether the TF card gets a second database or shares the one at
  `[0x0302329c]`.
- What the nine `A_MEIDASORTBAK0..8` sort-dialog options actually change.

Practical consequences for the owner's goals

- "Better sorting" (e.g. natural track-number order, album-artist grouping) means
  changing the key the scan stores. The builders at `0x0307d80a`/`0x0307d8c4` and
  the string-area writer are the patch points; the comparator can stay.
- "Faster browsing" is bounded by insertion-sort scan cost and per-tie flash
  reads, not by the UI; the lists themselves are already indexed by the database.
- "Clearer titles" is a tag-parse/display-string issue (module 18 / module 0),
  independent of the sort machinery.

---

## Appendix: key addresses

| what | where |
|---|---|
| extension table (14 codes) | mod 0 data `0x030056be`; mod 31 code `0x0307e110`; mod 38 code `0x0307e6cc` (+`CUE`) |
| DB read/write primitive | mod 0 `0x03067510`, device selector `0x00030001` |
| record fetch for playback | mod 0 `0x0306c7ac` |
| SortInfo struct (RAM) | `0x03024808`; base sector ptr `[0x0302329c]`; builder mod 23 `0x0307de14` |
| category selector | halfword `[0x030235c0]` |
| list header (RAM) | `0x03024f78` |
| sort record array (RAM) | `0x03024d08`, stride 14 |
| sort engine | mod 39: uppercase `0x0307d5fc`, char cmp `0x0307d608`, record cmp `0x0307d620`, sorted insert `0x0307d6ea`, collation table build `0x0307d786`, key builders `0x0307d80a`/`0x0307d8c4`, string buffers `0x0307f28c`/`0x0307f38c`, state `0x0307e1ec`, collation table `0x0307e1fc` |
| play context | `0x03023980` (category at +0xf2); builder mod 24 `0x0307e9c0`; per-category count fn `0x0307dda8` |
| CUE parser | mod 37 at `0x0307d5fc` window; strings `0x0307db18`, `0x0307db48` |
| browser state / node list | `0x030228a8` (mod 31); 11-byte name at node +0x4f |
| resource-name table | file `0xc86d9a`… (`A_ALLMUSIC_` at `0xc88906`) |
