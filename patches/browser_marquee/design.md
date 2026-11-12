# Browser dwell-scroll metadata display: design and evidence

Experimental variant. When an entry in the music browser stays
selected, the row text starts scrolling after a one second dwell and
shows the entry's metadata, the way a long title scrolls in the
player. Built and validated entirely under emulation; nothing has
been flashed. The default build is unchanged (verified byte
identical, SHA-256 `92c44606...`).

Second version: the scroll string for a file with usable tags is
now the tag string (ARTIST - TITLE, plus - ALBUM when present),
parsed on the selecting paint by the firmware's own tag dispatcher.
Everything else keeps the first version's composed dirent string.
The v2 investigation, design, accounting and gates are in the
section "Tag extension (v2)" below; the v1 sections stand as the
record of the base feature, with one correction: research item 4's
conclusion that tags are not reachable from the browser window was
wrong about the parser's home, as the v2 section documents.

## Verdict first

Stock already scrolls a wide selected name in the browser, through
the same marquee engine the player uses. What stock does not have
is a dwell (the scroll starts one step interval after the paint
that registers it) and the scroll string is the bare name, never
metadata. This variant adds the dwell and swaps the scroll string
for a composed name / format / size string built from fields the
browser node already carries. The stepper, the erase and the text
draw stay stock, byte for byte.

## Stock marquee mechanism (research item 1)

The text engine in module 0 owns a single global marquee context
at 0x03023888. Two entry points matter:

| Piece | Address | Behaviour |
|---|---|---|
| Registrar | 0x0306302A | Stores the rect (arg 1 descriptor copied to ctx+0), the packed position and size (args 2 and 3 to ctx+0x18), the string's character count (wcslen 0x03056B80, to ctx+0x24), the width of the prefix that fits the rect (ctx+0x10), the cell unit (ctx+0x16: 12 if the font class cell at 0x03023880 is 1, else 16), state byte ctx+8 = 0xFF, char offset ctx+0xA = 0, the current tick (cell 0x03023298, 100 Hz) at ctx+0x28, and the step interval (arg 6) at ctx+0x2C. Draws nothing. |
| Stepper | 0x03062F54 | Called with the registered string. Returns at once unless the tick gate passes (elapsed since ctx+0x28 at least ctx+0x2C). Advances the char offset by one character per interval, ping-pong: forward while the state byte is 0xFF, back down at 0, flipping at both ends. Before drawing it erases the text rect, then draws the string plus offset through the text renderer 0x03062CEE. |

The state machine has one quirk, measured in the gates below: the
forward flip happens only once the offset exceeds the maximum
(chars minus rect width / cell unit), so the stored offset peaks
at max + 2 and two frames draw past the nominal end, showing a
shortening string. That is stock behaviour for the player's title
scroll as well, and this variant inherits it unchanged.

Erase path: window registrations pass arg 4 with a zero low
halfword, which the registrar stores at ctx+0x14; the stepper then
erases with the rect fill 0x030632FA whose colour argument is read
from the palette accent cell 0x030235B8 itself. So a scroll step
repaints the text rect in the band colour, then draws. No stale
glyph residue is possible inside the rect, and nothing outside the
rect is written.

Callers: the player (module 27) registers its title and artist the
same way (setup sites 0x0307DFD2, 0x0307FA2A, 0x0307FF4A; stepper
calls at 0x0307FB10 and 0x0307FE34, the latter gated by
test-noclear(0x148) in its painter). Every window caller passes
interval 30: one character per 30 ticks (300 ms), first step one
interval after registration. There is no stock dwell anywhere.

The browser (module 31) wires the same idiom for the selected row.
Its painter (0x0307E8F2) measures the selected node's name with
0x0306295A; when the width exceeds 0xDC (220 px, the text rect
width) it stores the name pointer at the window local context
0x03025928 + 0xC, registers it with the row rect
(11, 53 + 40i)..(231, 68 + 40i) and interval 30, and posts event
bit 0x148. The painter's tail (test site at 0x0307ECA0) then calls
the stepper with that pointer on every paint while bit 0x148
tests set. Both list modes (bits 0x144 and 0x143) share the row
geometry, the registration and the tail.

## Idle cadence (research item 2)

The dwell and the steps ride on paints, not keys. Bit 0x148 is the
framework's persistent repaint request for this window: painters
post it after a registration and clear it on list repaints, chrome
repaints, narrow selections and window exit (the exit callback at
0x0307D776 is a dedicated clear(0x148)). While it pends, paints
keep being dispatched, which is exactly the cadence the stock
player title scroll runs on. The window-manager dispatch loop
itself was not located in module 0's message dispatcher or module
1's runtime, so the dispatch half of this idiom is a Phase E
confirmation item; the set / test / clear half is fully traced,
and the gate below is written so it behaves correctly under any
dispatch that delivers paints while the bit pends. The gate also
re-posts the bit during the dwell, so the cadence cannot stall
before the first registration exists.

## Text geometry (research item 3)

The renderer 0x03062CEE clips against the descriptor it is handed
(the descriptor words land in the draw state at 0x03023868 and
0x0302386C, the clip the glyph rasterizer works against). The
stock scroll never needs left clipping: it advances the string
pointer by whole characters and draws the remainder at the rect's
left edge, so no negative pen offset ever arises. This design
mirrors that technique exactly, which is why no negative-offset
drawing had to be proven. A rendered-width path exists and is the
one the painter itself uses: 0x0306295A (per-character advances
from 0x030627BE). The gate calls it on the composed string and
scrolls only above the painter's own 0xDC threshold.

## Node census and metadata reachability (research item 4)

The browser node is 0x270 bytes. Fields used or considered:

| Offset | Contents | Source |
|---|---|---|
| +0x04 | Next node pointer | painter chain walk |
| +0x0C | Enumeration ordinal | bridge documentation |
| +0x4E | Class byte (category classifier 0x0307D1D0) | painter / bridge docs |
| +0x4F | Embedded FAT dirent copy: 8.3 name at +0x4F (11 bytes), extension at +0x57 (3 bytes, space padded, uppercase), attr at +0x5A (bit 0x10 = directory), first cluster at +0x63/+0x69, file size at +0x6B (u32) | enumeration fill 0x0307D254; the M3U bridge already tests +0x57..+0x59 for an extension |
| +0x70 | UTF-16 display name (long name when present, else converted 8.3), capacity 256 units | fill path 0x0305B004 (0x0305A1A4 on FS type 3) |

Tags (title, artist, album) are not reachable from the browser
window, on this evidence: no tag fields exist in the node; the
only tag parser runs on the playback open path (modules 33 and
24) for the loaded track; module 18's metadata path serves the
player overlay and its residency and callability from the browser
window are not established; the name buffer at 0x030235CE is the
playing track's snapshot and must not be overwritten while
browsing. (Superseded by v2: the parser is module 0's dispatcher
and is reachable; see "Tag extension (v2)". The v1 string below
remains the fallback for files without usable tags.) The
composed string is therefore:

- Files: NAME + " - " + EXT + " - " + SIZE, with EXT omitted when
  the dirent extension is blank. Separator is " - " (basic ASCII,
  guaranteed font coverage).
- Folders (attr bit 0x10): NAME only.
- SIZE from the dirent size: "N B" below 1 KiB, "N KB" (rounded)
  below 1 MiB, "N.N MB" below 1 GiB, else "N.N GB" (one decimal).
- Names longer than 48 UTF-16 units are not composed; the feature
  falls back to the stock name scroll for that entry (no
  truncation). Buffer worst case is 48 + 19 = 67 units plus the
  terminator, inside the 68-unit buffer.

Selection state comes from the browser context at 0x030228A8:
first visible node pointer at +0x00, current level at +0x1CC
(u16), first visible index at +0x1CE + level x 2 (u16), selected
index at +0x1EE (u16). The selected node is the chain walk from
the first visible node by (selected minus first), exactly as the
painter computes it.

## Design

Three hooks, all in module 31 code, plus a growth payload.

| Patch | Site | Change |
|---|---|---|
| 0300 | 0x0307ECA0, the painter tail's test-noclear(0x148) call | BL to mq_gate. The gate returns the value the displaced test would have returned, so the stock tail steps only when the gate allows. |
| 0301 | 0x0307E5B8, the Key callback entry | B.W to mq_key, which resets the dwell state, performs the displaced push.w, and resumes the stock handler at site + 4. |
| 0302 | 0x0307D776, the exit callback | B.W to mq_exit, which zeroes the marquee state, then performs the displaced mov.w r0, #0x148 and tail-branches to the stock clear helper, as stock does. |

mq_gate runs on every painter tail. It resolves the selected
node, then:

- Selection changed: record the node, stamp the tick, phase =
  DWELL.
- DWELL: return 0 (no step this paint, including a step of a stock
  name registration the row loop just made). Keep bit 0x148 posted
  so paints keep coming. At expiry: if the name exceeds the
  compose cap, register the stock name and go PASS; else compose,
  measure, and if the composed width exceeds 0xDC register the
  composed string (stock registrar, row rect, interval 30) and go
  SCROLL; if it fits, clear bit 0x148 (paints stop) and go PASS.
- SCROLL: if a list or chrome paint re-registered the stock name
  (the string pointer at LCTX+0xC is no longer the buffer),
  re-register the composed string preserving the stepper's char
  offset, direction and tick stamp around the registrar call.
  Return the stock test result so the tail steps.
- PASS: pure stock. If a key press flagged a reset, re-register
  the stock name once (registrar resets the offset to 0) so the
  stock name scroll restarts from the beginning.

mq_key runs on any key press: phase back to DWELL, stamp = now,
and the dirty flag set (the PASS re-registration above). In
SCROLL the restart needs no flag: the dwell expiry re-registers
the composed string, which resets the offset by construction.

State and buffer live inside the payload (module 31's own growth,
resident exactly while the window is). Nothing goes to SAVEINFO:
this is transient UI state. Layout: 32 bytes of state (node
pointer, dwell stamp, phase, dirty flag, three saved stepper
fields for the re-registration path), then the 68-unit (136 byte)
compose buffer.

### Parameters

| Parameter | Value | Origin |
|---|---|---|
| Step interval | 30 ticks (300 ms), one character per step | Stock-mirrored: every window registration passes 30 |
| End behaviour | Ping-pong, offset range per the stock state machine (peak max + 2, see the quirk above) | Stock: the stepper is unmodified |
| Erase | Rect fill with the accent cell colour, then draw | Stock stepper path for window registrations |
| Wide threshold | 220 px (measure above 0xDC) | Stock-mirrored: the painter's own comparison |
| Dwell | 100 ticks (1.0 s) | Chosen. Stock has no dwell; the brief suggested about one second |
| Compose name cap | 48 UTF-16 units | Chosen: buffer bound; longer names keep the stock name scroll |
| Size format | B / KB rounded / MB / GB with one decimal | Chosen |

### Payload accounting

| Part | Bytes |
|---|---|
| mq_gate | 352 |
| mq_node (selected-node walk) | 68 |
| mq_units (name length) | 30 |
| mq_compose (compose + size formatting + decimal printer) | 404 |
| mq_register (stock-mirroring registration) | 84 |
| mq_key stub | 36 |
| mq_exit stub | 32 |
| State | 32 |
| Compose buffer | 136 |
| Total payload | 1,172 |

(Routine sizes are code plus each routine's literal pool; the
build's assembled code total is 1,004 bytes. The payload is
marquee_payload.bin, placed by build.py as the module 31 code
growth at 0x0307EE48. Build note: build_marquee.py forces wide
branch encodings for label branches and verifies every branch
target after assembly, because Keystone mis-sizes short
conditional branches between its passes and corrupts later
absolute BL displacements by +2; the verification is part of the
build, not a comment.)

Variant: default 32 patches + the 3 hooks + vorbis75 transplant +
the growth. Length 13,632,664 bytes (stock + 1,172). SHA-256
`e8839fa77258e41eabea2347185880500e9fdc5224baeff4aed81069558d514d`.

## Gates

All gates run under Unicorn against the built variant
(test_browser_marquee.py): the real painter, the real registrar,
the real stepper and the payload routines execute; text is
modelled at its painter-facing entries (the string measure and
the per-character advance return a deterministic width model, the
renderer records its descriptor and string, fills record and
apply), the same boundary the focus suite uses, because the font
is compression-wrapped and its decode callbacks are
boot-initialised on hardware. Both list modes are exercised.

| Gate | Result |
|---|---|
| Compose units (file with extension in each size class: 500 B, 1023 B, 1 KB, 822 KB, 1.0 MB, 24.5 MB, 1.5 GB; extensionless file; folder) | 9 of 9 exact strings |
| 1. No offset movement before the dwell elapses | Pass: offset 0 and no scroll draw across the 100-tick dwell |
| 2. Cadence and end behaviour | Pass: first step exactly at registration + 30 ticks; one character per step; stored peak 35 for the 46-unit fixture string (46 - 220/16 + 2, cell unit 16 in the tail context); ping-pong back to 0 |
| 3. Selection change resets | Pass: phase returns to DWELL, offset frozen through the new dwell |
| 3. Key press resets | Pass: phase returns to DWELL, no step during the post-key dwell, offset 0 at re-registration |
| 4. Fitting name never scrolls | Pass: zero scroll steps over 3,000 ticks; bit 0x148 released; phase settles to PASS |
| 5. Pixel cleanliness | Pass: the step's only draw is in the row text rect (11, 133, 231, 148); the erase fill is exactly that rect in the band colour 0xF220 and precedes the draw; every other fill in the paint is the band colour |
| 6. Rows above and below | Pass: no fill or erase touches any other row's band during a step |
| Fallback (60-unit name) | Pass: phase PASS, the stock name pointer is registered |
| Folder | Pass: composes the bare name, scrolls when wide |
| Mode B list | Pass: registers after the dwell, steps at the same cadence |
| Exit callback | Pass: state zeroed, bit 0x148 cleared as stock |

A demo GIF rendered from the emulation trace (dwell, then the
composed string stepping) is in the work directory:
work/browser_marquee/demo/marquee_scroll.gif.

## Integration into the full build: does not fit

(This section is the v1 record; the v2 numbers are in "Tag
extension (v2)" below, under the same heading.)

The full build's module 31 window is 7,436 bytes with a 6,800
byte payload (patches/full/README.md, module 31 window ledger),
leaving 636 spare bytes at window offsets 6800..7436. The marquee
payload is 1,172 bytes: a shortfall of 536 bytes. The code alone
(1,004 bytes) exceeds the spare, so no relocation of state or
buffer closes the gap. Trimming inside this feature does not
close it either: dropping the size formatter entirely (the single
largest discretionary block, roughly 230 bytes of mq_compose)
still leaves a shortfall of about 300 bytes, and dropping the
extension as well (roughly 40 bytes) leaves about 260. The
remaining window occupants (M3U bridge and parser 6,260 bytes,
hook trampoline 64, lock routine 406, navigation stubs 68) cannot
shrink without changing their behaviour, and moving an occupant
would change existing stub offsets, which the integration
conditions forbid. patches/full/ is therefore untouched, and this
variant ships standalone. What would change the verdict: about
540 bytes freed inside the module 31 window, or a second proven
resident home of about 1,180 bytes reachable from the browser
window (the focus census found none).

## Tag extension (v2)

### Route investigation

The working assumption going in was that module 18 is the
firmware's text tag parser. It is not. Every substantial function
in module 18 was decompiled: its ID3, FLAC, APE and MP4 machinery
locates embedded pictures only (APIC frame scanners at 0x03081AD0
and 0x03082362, the FLAC picture extractor at 0x03082CD2, the
picture locator dispatcher at 0x03083276 that the player calls
from 0x0307DA24 immediately before artwork setup). The two packed
frame-id tables in its code are picture-scan vocabularies, not a
text parser's. Route A as literally specified (call module 18 for
text tags) therefore fails on the evidence: there is no text
parser there to call.

The text parser is in module 0, which is resident at all times.
Module 0 embeds the Vorbis field names ("Title", "Artist",
"Album", "Album Artist", "Track", "Discnumber", "Genre"), the
RIFF INFO names and the ID3 marker, and one dispatcher,
FUN_0306C51C, routes by extension to per-format parsers that all
stay inside module 0. Routes B (library records) and C (a
self-contained reader in the payload) were not needed: the
dispatcher is callable from the browser window, with two stock
callers proving the pattern (below). The route taken is the
dispatcher, reached exactly the way stock reaches it.

### Parser pins

| Piece | Address | Contract |
|---|---|---|
| Dispatcher | 0x0306C51C | (handle, out struct, extension). The extension is three bytes, compared verbatim against a table in module 0 data at 0x03005714: MP1 MP2 MP3 WMA WAV APE FLA AAC M4A OGG MP4 3GP DFF DSF. DFF has no case and returns an untouched struct. Returns 0 always; success is read off the fields, as both stock callers do. |
| Output struct | 0x556 bytes | Zeroed by the caller before the call (FUN_03054E66 is bzero(dst, len); module 33 zeroes 0x556 at 0x03088D0C, module 38 zeroes 0x558 at 0x0307EE5E). Fields are UTF-16, each 127 units plus terminator: disc number +0x000, track number +0x008, title +0x060, artist +0x15E, album +0x25C, genre +0x35A, album artist +0x458. |
| ID3 family (MP1/MP2/MP3/AAC) | FUN_03069564 + FUN_03068876 | The first parses ID3v2.2/2.3/2.4 through a 0x400-byte header read; the second fills still-empty fields from an ID3v1 trailer (title, artist, album, genre from the ID3v1 table) and trims trailing spaces itself. TPE2 lands in album artist. |
| WAV | FUN_03069BA6 | RIFF INFO (INAM, ITRK, IART, IPRD, IGNR). |
| APE | FUN_03069D3E | APE items. |
| FLAC | FUN_0306A66A | Skips an ID3 header when present, walks metadata blocks to the Vorbis comment block, hands it to the comment parser. |
| OGG | FUN_0306A514 | Walks Ogg pages to the type 3 comment packet, hands it to the comment parser. |
| Vorbis comment parser | FUN_0306A282 | Matches TITLE, ARTIST, ALBUM, ALBUMARTIST, DISCNUMBER, TRACKNUMBER, GENRE case-insensitively; values are converted from UTF-8 to UTF-16 by FUN_03068664. |
| MP4 family (M4A/MP4/3GP) | FUN_0306C08C | Walks moov/udta/meta/ilst and the ID32 box. |
| DSF | FUN_0306A812 | DSF metadata. |
| Open | FUN_030589B6 | (name-out buffer, directory cluster, entry index, mode, mode-string pointer) returns a handle 0..7 or -1. The name-out receives the 11-byte 8.3 name. The index is the raw entry slot within the directory: the fetch below computes the dirent offset as index x 32. The payload passes mode 3 (module 33's value; 1 and 2 are the only values with distinct behaviour in the body, both database fixups) and the stock "R" string at 0x0306E828 that module 33 passes (read mode is selected by the absence of 'W' in the string's first two bytes). |
| Dirent fetch | FUN_03057F8E (FAT), FUN_03057E46 (FS type 3) | Called by the open to materialise the entry from (directory cluster, index). On FS type 3 the open reads the type byte itself and takes the database path. |
| Stream leaves | 0x03058FA8 read, 0x030594A0 seek, 0x030545D4 size, 0x0305943E and 0x0305945E tell, 0x03058E8E close | All take the handle (read/seek as the third argument, size/tell/close as the first). Seek whence 2 positions from end minus the offset, measured with the ID3v1 reader. |

The browser-side identity comes from the same pins the M3U bridge
uses (patches/m3u/bridge_completion.md): the directory cluster is
the browser context's per-level record at 0x030228A8 + 56 x level
+ 0x14 (the +0x18 word is the FS type 3 twin and doubles as that
mode's cluster cell), and the node's ordinal at +0x0C is the
enumeration index the fill at 0x0307D254 stores as walker cursor
minus 1, that is, the entry's slot within its directory. The
node's file cluster (dirent halves at +0x63 and +0x69) completes
the cache key. The dispatcher's extension argument is the node's
own dirent extension at +0x57, three uppercase bytes, the same
format the dispatcher table stores.

Both stock callers confirm the contract. Module 38 (the scan)
zeroes a stack struct, opens each enumerated file with
FUN_030589B6, calls the dispatcher at 0x0307EE70, reads fields at
+0x15E and +0x458, closes. Module 33 (playback open) does the same
at 0x03088D42 into a static struct, then applies the rule this
build mirrors: when artist is empty and album artist is not, copy
album artist over artist.

### Residency verdict

No residency question arises for the parser itself: module 0 is
the permanent system module, and the dispatcher plus every
non-WMA parser execute entirely inside it (callee census over all
six parser bodies: no call leaves module 0's code span). The open
is likewise module 0, and window overlays call it in stock:
module 27 (the player window) at 0x0307DDD2 and 0x0307E8F8,
module 30 at 0x0307D49C and 0x0307DFB2. Module 38, which shares
the window overlay family with the browser, calls the dispatcher
itself. The handle the open allocates comes from the eight-slot
descriptor table at 0x0307AB68; the payload opens and closes
inside one gate call, so it holds a slot only for the duration of
a parse, exactly as the scan does per file.

One format is excluded. For WMA the dispatcher delegates outside
module 0: when the mode byte at 0x03023151 is 0 it calls
0x0307E134, an address inside the shared window span (the ASF
parser overlay, whose data holds the WM field map), and otherwise
0x0308B560 inside module 33's span. Neither residency is
guaranteed while the browser window is active, and the
window-span variant would execute the browser's own bytes at
that address. The payload's extension gate therefore admits
every dispatcher format except WMA (and DFF, which has no case):
MP1, MP2, MP3, AAC, WAV, APE, FLA, OGG, M4A, MP4, 3GP, DSF. WMA
files keep the v1 string.

### Design additions

The three v1 hooks and the gate's phase machine are unchanged in
shape. Two routines and three payload data areas are added.

mq_tags runs on the selecting paint, inside the node-change
branch of mq_gate, so the bounded parse cost lands at the start
of the dwell and never on the scroll path. It returns at once for
folders (the dirent attr bit: a folder never triggers a file
read) and for names over the 48-unit compose cap (those keep the
stock name scroll, as in v1). Otherwise it keys the tag cache:
four entries, direct-mapped by node pointer, each holding the
node pointer, directory cluster, file cluster and ordinal, a
flags byte, and a 68-unit string buffer. A hit sets
state.cur_entry and ends. A miss claims the entry, checks the
extension against the admitted list, opens the file, zeroes the
struct, calls the dispatcher, closes, and composes the tag
string into the entry buffer in place. A parse that yields no
usable tag leaves the entry valid with has_tags clear, so
reselection does not re-read an untagged file either. The exit
hook also clears the cache valid bits (the node array is
rebuilt on re-entry). Key presses do not invalidate.

mq_tagstr composes: artist, then title, then album, joined by
" - ", a field appearing only when it survives hygiene. Artist
falls back to album artist when empty (the playback rule above).
Album is appended only when a lead field exists; album alone is
not a usable tag and the file keeps its v1 string. Hygiene: each
field is trimmed of leading and trailing units at or below 0x20,
whitespace-only counts as absent, and each field is capped
(artist 24, title 24, album 13 units), so the worst case is
24 + 3 + 24 + 3 + 13 = 67 units, inside the 68-unit buffer
discipline v1 established. Truncation is at a unit boundary.

At dwell expiry the gate checks state.cur_entry first: with
has_tags set, it measures and registers the entry buffer instead
of composing the dirent string; the SCROLL phase's
re-registration guard now compares against the active string
pointer held in state, so the tag string is what gets restored
after a list or chrome repaint. Every other path (fitting tag
string, no tags, fallback, PASS behaviour, key handling) is the
v1 flow unchanged.

### Payload accounting (v2)

| Part | Bytes |
|---|---|
| mq_gate (v1 352, tag branch added) | 428 |
| mq_node | 68 |
| mq_units | 30 |
| mq_compose | 402 |
| mq_register | 84 |
| mq_key stub | 36 |
| mq_exit stub (v1 32, cache clear added) | 60 |
| mq_tags | 324 |
| mq_tagstr (with field helpers) | 276 |
| Code total | 1,708 |
| State (v1 32, entry and string pointers added) | 48 |
| Compose buffer | 136 |
| Extension table (12 x 3) | 36 |
| Tag struct | 1,366 |
| Tag cache (4 x 156) | 624 |
| Alignment padding | 2 |
| Total payload | 3,920 |

Variant: default 32 patches + the 3 hooks + vorbis75 transplant +
the growth. Length 13,635,412 bytes (stock + 3,920). SHA-256
`1a0c385704e4b7c39bbc7d81bae70881f0d8ec04b4f899c95d1bf31bc3d12f28`.

### Gates (v2)

Parser proof (development harness, stock image): the real
dispatcher was called the way the payload calls it, with only the
stream leaves modelled, over eleven fixtures. ID3v2.3 MP3, FLAC
and OGG fixtures returned the exact title, artist and album;
TPE2 landed in album artist; an ID3v1-only MP3 returned its
fields and genre; untagged and malformed fixtures returned an
empty struct without hanging (four reads for the malformed
FLAC); 40-unit fields arrived intact. Observed read volumes:
1152 bytes in 2 reads for the MP3, 78 bytes in 29 reads for the
FLAC, 90 bytes in 35 reads for the OGG, trivially inside the
one-second dwell.

The v1 suite (test_browser_marquee.py) re-runs unchanged against
the v2 build and passes in full: its fixtures carry no modelled
filesystem, the stock open fails soft on the zeroed card state,
and every v1 assertion (compose strings, dwell, cadence, resets,
fitting, fallback, folder, mode B, exit) holds.

The v2 suite (test_browser_marquee_tags.py) drives the real
painter, gate, open, dispatcher, parsers and close, modelling
only the dirent fetch, the stream leaves, the raw sector read
(failed soft; the proof showed the parse completes without it)
and the v1 text model:

| Gate | Result |
|---|---|
| Tagged MP3, FLAC, OGG scroll the exact tag string | Pass: one dirent fetch each for (directory cluster, ordinal), entry buffer registered, string exact, scroll advances |
| Untagged MP3 falls back | Pass: parse attempted, v1 string "Plain Tune - MP3 - 2 KB" composed, no tag string registered |
| Malformed FLAC falls back | Pass: v1 string, no hang |
| Folder | Pass: zero dirent fetches across the dwell |
| Cache | Pass: A parsed once, B parsed once, reselecting A is a hit (no third fetch), key reset does not re-read |
| Directory change | Pass: same nodes under a new directory cluster re-parse (fetch under the new key) |
| Field rules | Pass: title alone, artist alone, whitespace artist treated as absent, album artist fallback, caps produce exactly 24 + 3 + 24 + 3 + 13 units |
| WMA | Pass: no fetch, v1 string (extension gate) |
| FS type 3 argument | Pass: the open is attempted with the +0x18 cluster (fetch records cluster 7, not the sentinel at +0x14); the modelled fetch refuses and the v1 string results |
| Parse timing | Pass: the fetch is already done on the selecting paint; no step before the dwell expires |

A demo GIF rendered from the emulation trace (dwell on the node
name, then the tag string stepping) is in the work directory:
work/browser_marquee2/demo/marquee_tags.gif.

### Integration into the full build: still does not fit

The v1 payload missed the full build's 636-byte module 31 spare
by 536 bytes. The v2 payload is 3,920 bytes, so the shortfall is
now 3,284 bytes. Nothing else about the integration picture
changed: the window occupants cannot shrink without changing
behaviour, and patches/full/ is untouched. What would change the
verdict: about 3,300 bytes freed inside the module 31 window, or
a proven resident home elsewhere. The tag struct and cache are
payload-resident scratch by design (transient UI state), so a
future home would need roughly 2,000 bytes of writable RAM with
no other owner plus the 1,708 bytes of code in the window; the
focus census found no such home.

## v3: full tag string, view toggle, thumbnail verdict

### Change 1: the uncapped tag string

The v2 field caps (artist 24, title 24, album 13) are gone. The
field-length helper now receives the dispatcher struct's own
bound, 127 units, for every field, so the tag view carries the
full title, artist and album exactly as the parser left them in
the struct. The worst case string is 127 + 3 + 127 + 3 + 127 =
387 units, 388 with the terminator; a cache entry is 20 + 776 =
796 bytes and the four-entry cache is 3,184 bytes (v2: 624). The
file view string is unchanged (the v1 composition, 68-unit
buffer, 48-unit name cap and stock fallback above it).

One stock parser quirk surfaced while building the gate fixture,
recorded because it bounds what "full" can mean at the struct
level: the ID3 parser terminates each field in place, and a full
127-unit title's terminator lands on artist unit 0 (title at
struct +0x60, +0x60 + 2 x 127 = +0x15E, the artist field). When a
long title frame precedes the artist frame in the file, the
artist is read back empty from the struct; when the artist frame
is written after the title, it wins the shared byte. The payload
composes from the struct contents either way, the same struct
the library scan and the playback path read, so the scroll shows
what the firmware itself holds. The gate fixture orders its
frames title, artist, album so all three fields survive at 127.

### Change 2: long-press view toggle

Census method: the Key handler's dispatch is a compare tree over
the event word in r4 (region 0x0307E5DC to 0x0307E662). The tree
was executed under emulation for every event word of types 1 to
5 across all sixteen single-bit masks, recording the leaf each
word reaches; the leaves were then read against the handler
disassembly. GetKeyMask produces only masks 0x0001 (Power),
0x4000 (OK), 0x0010 (Vol+) and 0x0020 (Vol-); the wheel adds
0x0004 and 0x0008 at types 3 and 4. Type 1 (press) and type 5
(long release) reach the default exit for every mask. The type 2
(long press) outcomes:

| Event | Leaf | Stock action in this window |
|---|---|---|
| 0x20004000 (OK) | 0x0307E700 | Assigned: tests event flag 1; if set, posts 0x2F and clears flag 1; if clear, calls 0x0307E354 unless the context halfword at [sb+4] is 1 |
| 0x20000040 (ESC mask) | 0x0307E77C | Assigned on paper (clears flag 1, sends a message), but no producer on this device emits mask 0x0040 |
| 0x20000001 (Power) | 0x0307E7FC | None in the handler; it is the shared epilogue |
| 0x20000010 (Vol+) | 0x0307E7FC | None |
| 0x20000020 (Vol-) | 0x0307E7FC | None |

Chosen: **long press Vol+ (0x20000010)**. Long OK was rejected
because it is assigned. Long Power was rejected because the key
state machine independently posts the system power-off event
past 100 ticks, so a held toggle would become a power-off. The
ESC long press cannot be produced at all.

Documented conflict: a Vol+ hold keeps emitting type 3 repeats
after the 20-tick point, and stock maps those to volume steps in
this window (leaf 0x0307E688). The toggle does not consume or
alter them, so a volume ramp hold in the browser flips the view
once at the 200 ms mark and then ramps as stock. Volume
behaviour itself is unchanged; releasing and re-holding toggles
back.

Mechanism: hook 0303 is a BL at 0x0307E5E6 inside the Key
handler, displacing the ldr.w that loads the local context
pointer into sb. At that point r4 holds the final event word:
the handler has already fetched it through FUN_03061B16 and
applied its own 0x131 override, which can only substitute the
OK release word, never a type 2 word, so an exact compare
against 0x20000010 cannot be spoofed. The stub preserves r0 to
r3 (r2 carries a cell pointer the volume paths use), flips the
mode byte at state +0x18, clears state.node so the next paint
re-runs the gate's selection path under the new mode, performs
the displaced load, and returns. Hook 0301 (mq_key) runs earlier
in the same callback and has already reset the dwell stamp and
phase, so the scroll restarts from the dwell in the new view; an
in-progress scroll is reset, nothing more. The mode is payload
state only and mq_exit clears it, so every browser session
starts in the tag view.

In the file view the gate skips the parse on the selecting
paint (the file view needs none) and always composes the dirent
string at dwell expiry. In the tag view nothing changed. The
cache is mode-independent: toggling tag to file to tag on one
file performs no second read in either direction, which the v3
gates assert from the fetch log.

### Change 3: cover thumbnail feasibility

Verdict: **not built; blocked on placement (question c)**.
Questions (a) and (b) came back clean by a route that avoids
the locator, and their evidence is recorded so the feature can
be picked up if a placement is ever approved.

(a) Driving the pipeline at thumbnail size. The locator
(FUN_03083276) is not handle-self-contained: its format
identifier (FUN_03067F50) reads the file header through
callback cells at 0x0300443C and 0x03004440 (module 0 data,
zero until bound) and a stream type pointer at 0x0304B4D4
(module 33 BSS). In emulation, calling the locator with those
cells at their power-on value jumps to address 0. Binding them
to the plain stream leaves, whose signatures match the
callbacks exactly, makes the identifier work (it wrote "MP3"
for the fixture), but the cells belong to whichever stream the
media core currently has bound; rebinding them from a browser
dwell hook, even with save and restore, reaches into another
stream's state.

The direct route avoids the question. The locator's own MP3
case body, the picture scan FUN_03082BF6, works from the handle
alone through the stream leaves, the same leaves the tag path
already uses. Driven that way (open, rewind, scan, the two
descriptor setters, setup, the painter consumer in a loop,
close), all under emulation with an MP3 carrying the theater
probe JPEG (30x18) in an APIC frame:

| Box | Scaled | Blits | Instructions, whole sequence |
|---|---|---|---|
| 36x36 | 36x21 | 21 rows of 36x1 at the requested dest, mode 0x10 | 981,765 |
| 16x16 | 16x9 | 9 | 326,735 |
| 144x144 | 144x86 | 60 of 86 shown (probe loop cap) | 9,077,935 |

The target size is caller-supplied through the request globals
at 0x0302598C to 0x03025998 (the player writes 144, the focus
variant 190, this probe 36 and 16). Setup's only size gate is
box width at most 320; no floor appeared down to 16. The first
blit row of the 36-wide decode is pure red (mean red channel
31 of 31), matching the fixture's red top band. Decode buffers
are the pipeline's own: the 640-byte row buffer at 0x03026A20
and the work buffer at 0x03025A20. A one-entry pixel cache at
the full 36x36 box would cost 2,592 bytes (the fixture's
produced size, 36x21, is 1,512 bytes). The demonstrated route
covers ID3; the FLAC picture extractor (FUN_03082CD2) is
likewise handle-based in the locator's dispatch, but was not
probed separately.

(b) Shared state. After a 36x36 browser sequence, a fresh
player-size sequence (144x144 at the player's dest) leaves the
artwork context at 0x03026CA0 (0x40 bytes) and the request
descriptor at 0x030259D4 (0x10 bytes) byte-identical to a clean
player-only run in the same emulation. What a browser session
leaves behind, item by item: the four request globals and the
descriptor fields (the player's request function rewrites all
of them per track), the artwork context (setup reinitialises
it, starting from the previous-picture reset at 0x03080B98),
module 19 resident in its overlay (the player's own setup
reloads it through the loader), the picture work buffer
(scratch by design), and the scan's stream position (the
payload's handle is closed at the end of the sequence). A file
without a picture returns scan 0, setup never runs, and there
are no blits. Nothing in the direct route touches the bound
stream cells named in (a).

(c) Placement. The selection band and text geometry, measured
from the real painter in the v1 harness: band (0, 40 + 40j) to
(239, 78 + 40j); text rect (11, 53 + 40j) to (231, 68 + 40j).
The painter builds the row text rect on its stack inside the
per-row path shared by every row and both list modes, and uses
that one struct for the text render (call site 0x0307EB36) and,
copied with its height set to 15, for the marquee registration
(0x0307EB0E); the 220 px over-wide test is applied to the same
geometry (0x0307EAB2). The payload's own registrar mirror
(mq_register) hardcodes the same 11 and 231. No parameter,
template rect or selected-row branch isolates the selected
row's x origin, so shifting the text right only while a
thumbnail is shown needs coordinated conditional changes at
the rect construction, the width test and mq_register, inside
machinery the v1 and v2 gates cover. The fallback named in the
brief, thumbnail over the band's left margin with the text
rect unchanged, requires the name text to start at x = 48 or
later; it starts at x = 11, so a 36-wide thumbnail would cover
the name's first 25 px. Neither placement survives the
geometry. Space was not the blocker, though it was tight: with
the pixel cache and capture code the payload would have
exceeded the 7,436-byte window unless the tag cache dropped to
two entries.

### Payload accounting (v3)

| Part | Bytes |
|---|---|
| mq_gate (v2 428, mode checks added) | 444 |
| mq_node | 68 |
| mq_units | 30 |
| mq_compose | 402 |
| mq_register | 84 |
| mq_key stub | 36 |
| mq_toggle stub (new) | 44 |
| mq_exit stub (v2 60, mode clear added) | 64 |
| mq_tags | 324 |
| mq_tagstr (with field helpers) | 276 |
| Code total | 1,772 |
| State (mode byte at +0x18, inside the v2 size) | 48 |
| Compose buffer (file view) | 136 |
| Extension table (12 x 3) | 36 |
| Tag struct | 1,366 |
| Tag cache (4 x 796, entry buffer 776) | 3,184 |
| Alignment padding | 2 |
| Total payload | 6,544 |

Variant: default 32 patches + the 4 hooks + vorbis75 transplant
+ the growth. Length 13,638,036 bytes (stock + 6,544). SHA-256
`c00e51ec20fe3ec0e9c70ad02a8c5ff6b701cf63ce49b8b520172cfb99d13807`.

### Gates (v3)

The v1 suite passes unchanged. The v2 suite passes with one
expectation updated by design: the field-rules case that
asserted the 24/24/13 caps in v2 now asserts the same fixture's
fields in full (40 units each), and says so in a comment.

The v3 suite (test_browser_marquee_v3.py) drives the real
painter, gate, Key callback, open, dispatcher, parsers and
close, with the v2 harness's modelled leaves:

| Gate | Result |
|---|---|
| Uncapped string | Pass: fixture fields all at the 127-unit struct bound register exactly the struct-derived 387-unit string (expectation composed from the struct bytes in memory, not from the fixture text); the terminator lands inside the 776-byte entry buffer and the halfword past it is untouched; scroll offset reaches 113 |
| Toggle stub contract | Pass: only event 0x20000010 flips the mode, both ways; state.node cleared; r0 to r4 preserved; sb left holding the local context pointer (displaced instruction performed); short press, repeat, release, long release, long Vol-, long Power, long OK and OK release are all inert |
| Toggle through the real Key callback | Pass: the event delivered through the key state cell and the stock fetch flips the mode; the volume byte is unchanged (no stock action); phase is back to DWELL |
| Views alternate | Pass: tag view scrolls the tags; after the toggle the file view scrolls "A Rather Long Fixture Song Name - MP3 - 2 KB"; after the second toggle the tag string is back; the fetch log shows exactly one fetch across the whole sequence (no re-read in either direction) |
| Short press | Pass: a type 1 Vol+ event through the full handler does not toggle |
| Exit reset | Pass: the exit hook returns the mode to tag view (and clears the cache, as in v2) |

A demo GIF rendered from the emulation trace (tag view dwell
and scroll of a 345-unit tag string, the long press, file view
dwell and scroll) is in the work directory:
work/browser_marquee3/demo/marquee_v3.gif.

The thumbnail gates are not applicable: the feature was not
built, for the placement reason above. The feasibility probes
behind the verdict are work/browser_marquee3/thumbprobe.py
(locator route) and thumbprobe2.py (direct route, restoration
and the no-picture case).

### Integration into the full build: updated shortfall

The v3 payload is 6,544 bytes against the full build's
636-byte module 31 spare: shortfall 5,908 bytes (v2: 3,284).
patches/full/ is untouched, and the default build is
unaffected: a framework build with the default manifest
reproduces the pinned unified image
`92c446066e715d74a719671d3ee643ed4b7587c94801eb6dc3893f2271ed944d`
byte for byte.

## v4: cover thumbnail with the text shift

### The placement decision

The v3 section left the placement open. The owner chose the
three-site text shift: while the selected file's thumbnail is
shown, the selected row's text rect moves right, left edge from
11 to 48 (the thumbnail occupies x=4..39, plus margin), right
edge unchanged at 231. Unselected rows and every other window
behaviour are untouched.

### The shift at the three consumers

The rect is a stack struct the painter builds per row at
[sp+8] (x0), [sp+0xA] (y0), [sp+0xC] (x1), [sp+0xE] (y1), and it
feeds two of the three consumers directly: the text render call
and the stock marquee registration both read it after the
per-row selected check. Two new hooks sit exactly on that
check, one per list mode: patch 0304 replaces the mode A
instruction at 0x0307EA98 (`ldrh.w r0, [r8, #0x1ee]`) and patch
0305 the mode B one at 0x0307EBBA (`ldrh.w r0, [r0, #0x1ee]`).
Each stub performs the displaced load (the mode A stub returns
the index in r0 because stock re-compares it), and, when the
row being painted is the selected row and the payload's
thumb-active byte is set, rewrites the struct's x0 field to 48.
One rewrite propagates to both the render and the
registration, because both consume the struct afterwards. The
stubs also verify that the thumbnail's tracked node is the
current selection (through mq_node): on a selection-change
paint the row loop runs before the gate clears thumb-active,
and the old row must still paint unshifted.

The third consumer is the width test, a constant compare
(`cmp r0, #0xdc`) fed by the measure calls at 0x0307EAAE (mode
A) and 0x0307EBE4 (mode B). Patches 0306 and 0307 hook those
two calls with one stub that returns the measured width plus
37 while thumb-active, so the stock 220 px compare acts as a
183 px test against the shifted rect (231 - 48); unshifted, it
returns the width unchanged. The payload's own mq_register
follows the same condition for its hardcoded geometry: x0 is
48 while thumb-active, 11 otherwise, for both the rect it
registers and the packed position it writes.

The condition is a single payload state, the thumb-active
byte in the gate state (which stays 48 bytes; the thumbnail
fields take its previously spare tail). It is set exactly when
a thumbnail becomes visible at dwell expiry, and cleared on
selection change (the gate's node-change branch), on the view
toggle, and on window exit. A scroll wrap is not a clear.

### Thumbnail lifecycle and the raster cache

At dwell expiry the gate calls mq_thumb before deciding the
string, so every measure and registration in that paint sees
the final geometry. mq_thumb:

- Skips folders, files already keyed in the raster cache, and
  extensions without a picture route (see the probe table).
- Resolves the file identity through mq_ident (the same key
  discipline as the string cache: node, directory cluster,
  file cluster, ordinal).
- Opens the file by (directory cluster, ordinal), rewinds it,
  zeroes the picture descriptor's located cell (the rule the
  locator's MP3 case follows; a stale value from an earlier
  picture makes later scans fail, proven in the probes), and
  locates the picture. The descriptor setters and the request
  globals are written only after a successful locate, before
  setup: the scan bodies need no descriptor setup, and setup
  is the consumer of those fields.
- Runs setup at the 36x36 target with destination
  (4, band top + 2), then consumes the painter consumer,
  copying each produced row out of the artwork row buffer
  into the raster cache. A row is captured only on the calls
  that return 1 (a new row decoded); its index is the context
  cursor minus the descriptor's mode cell, the flag path the
  v3 census found. The recorded width is the scaled width
  clamped to 36; the reservation is the full 36x36, 2,592
  bytes of halfwords.
- Publishes the cache key with the produced height (0 for a
  picture-less file, which suppresses re-opens on later
  dwells), and sets thumb-active and thumb-fresh when a
  picture was produced.

One entry is enough: the thumbnail is only ever shown for the
selected node, so the cache holds exactly the entry the
display can use, keyed like the string cache's selected
entry. Switching between two pictured files re-decodes on
each switch; the two-entry string cache still holds both
files' strings. The tag cache drops from four entries to two
to pay for the raster (the string fixtures' two files still
map to distinct slots).

The raster shares the tag struct's reservation (a union of
2,592 bytes; the struct is 0x556). The struct is scratch at
the selecting paint (the dispatcher's output) and as a
decode's open name-out; the raster is live between decodes.
The discipline: mq_tags clears the raster key after its open
succeeds, before the struct is zeroed and parsed; mq_thumb
clears it before its own decode. A failed open never touches
the span (proven with a sentinel-filled struct: the buffer is
byte-identical after a refused open), so a failed parse
attempt on another file leaves a cached raster intact. The
decode's locator out cell sits in the compose buffer, idle at
expiry, never in the raster.

Repaints: the setup call's own consumer blits paint the
thumbnail at the requested destination during the transition
paint. At every gate exit, mq_show then re-blits the cached
raster through the same bitmap path; on the fresh paint it
first fills the old unshifted text rect with the band colour
and renders the active string into the shifted rect,
mirroring the painter's own row render. On later paints it
blits only: the list repaint has just repainted the band over
the raster, and the stepper's erase covers only the shifted
text rect (x >= 48), so it never overlaps the raster and no
ordering hazard exists between the erase and the blit. No
paint after the transition touches the picture pipeline: the
gate suite asserts the open, setup and consumer counts are
flat across scroll paints and across a second dwell.

### Format probe results

Each route was probed end to end under emulation with the
theater probe's 30x18 JPEG embedded per format (work
directory: work/browser_marquee4/). Admitted routes are in
the payload's route table (PIC_ROUTES); anything not proven
clean stays thumbnail-less with its v1 or v2 string.

| Format | Entry | Located | Setup | Scaled | Verdict |
|---|---|---|---|---|---|
| MP3 (ID3 APIC) | scan body 0x03082BF6 | 868 | 1 | 36x21, 21 rows | in |
| FLAC (PICTURE block) | case head 0x0308364E | 907 | 1 | 36x21, 21 rows | in |
| APE (Cover Art item) | case head 0x030834DA | 865 | 1 | 36x21, 21 rows | in |
| WAV (id3 chunk) | case head 0x0308337C | 868 | 1 | 36x21, 21 rows | in |
| OGG (block picture) | case head 0x03083750 | extractor matches, then exits through a media-core temp-file path and closes the picture handle | n/a | n/a | out |
| DSF | case entry entangled with the dispatch's metadata-pointer seek; not probed clean as a head | n/a | n/a | n/a | out |
| DFF, M4A/MP4/3GP, AAC | no handle-direct picture entry found | n/a | n/a | n/a | out |
| WMA, OPUS | gated out since v2 (parser residency) | n/a | n/a | n/a | out |

The FLAC, APE and WAV entries are case bodies inside the
locator dispatch: they share the dispatch's stack frame (the
register push set plus a 0x224-byte frame, r5 = handle,
r6 = out cell) and exit through its shared epilogue at
0x03083712. mq_loccase rebuilds exactly that state, with the
epilogue's pc slot holding a return trampoline, and jumps in
(thumb bit set). The dispatch itself is never called: its
format identifier dereferences the media core's binding
cells and faults cold, as established in v3. OGG's case walks
the fixture correctly and its extractor's key compare
matches, but the extractor then exits through its temp-file
path (the "PICTURE OGG" strings and file helpers), which is
not handle-direct to the end; documenting the gap, not
working around it.

### Payload accounting (v4)

| Part | Bytes |
|---|---|
| mq_gate (v3 444, thumbnail call and shifted thresholds) | 500 |
| mq_node | 68 |
| mq_units | 30 |
| mq_compose | 402 |
| mq_register (conditional geometry) | 100 |
| mq_key stub | 36 |
| mq_toggle stub (v3 44, thumbnail clear added) | 48 |
| mq_exit stub (v3 64, thumbnail clears added) | 76 |
| mq_tags (identity factored out, invalidation moved) | 288 |
| mq_tagstr | 276 |
| mq_ident (new, shared by tags and thumb) | 64 |
| mq_thumb (new) | 500 |
| mq_loccase (new) | 38 |
| mq_blit (new) | 74 |
| mq_show (new) | 164 |
| mq_shifta stub (new) | 52 |
| mq_shiftb stub (new) | 52 |
| mq_measa stub (new, both measure sites) | 48 |
| Code total | 2,816 |
| State (thumbnail fields in the tail) | 48 |
| Compose buffer (file view; locator out cell at +0x80) | 136 |
| Extension table (12 x 3) | 36 |
| Tag struct / raster cache union | 2,592 |
| Tag cache (2 x 796, entry buffer 776) | 1,592 |
| Picture route table (4 x 8) | 32 |
| Total payload | 7,252 |

Eight hooks (0300 to 0307). Variant: default 32 patches + the
8 hooks + vorbis75 transplant + the growth. Length 13,638,744
bytes (stock + 7,252). SHA-256
`99e1dcc3fec2f59ed35ccba0a0990926b65fd93bd9766c6e8fd292d3f7a4ba2a`.

### Gates (v4)

The v1, v2 and v3 suites pass against the v4 payload. Two
harness changes came with v4, both recorded here because they
touch the older suites: their machines now load modules 18
and 19 and model the loader and bitmap leaves (module 18 is
resident on hardware; the v1 to v3 payloads never called it),
and the suites' node pool moved from 0x03030000 to
0x030A0000, because the old address lies inside module 19's
BSS (0x03026DA8 + 0xFB20), which the loader zeroes when the
picture setup loads the decoder. The v2 and v3 fetch
expectations now count the thumbnail probe's one open per
picture-route file per cache miss; the behaviours they gate
(the string cache's hit discipline) are unchanged, and the
counts say so in comments.

The v4 suite (test_browser_marquee_v4.py) adds a framebuffer
fed by the same leaf records, and gates:

| Gate | Result |
|---|---|
| Activation and raster | Pass: after the dwell, thumb-active is set, the cached raster is 36x21, and its rows equal a reference decode run through the stock pipeline directly |
| Shift at the painter | Pass: the selecting paint renders the row at x=11; the expiry and scroll paints render it only at x>=48, and the tag string is drawn at the shifted rect on the transition paint |
| Shift at the registration | Pass: the marquee context's packed position reads x=48 while active |
| Width test | Pass: a 206 px string (in (183, 220]) scrolls while shifted and never scrolls on a picture-less twin of the same name and size |
| Blit geometry and pixels | Pass: 21 blits of 36x1, mode 0x10, at (4, band top + 2 + k), pixels equal to the reference decode, from both the decode consumer and the cached re-blit; the framebuffer's red pixels sit exactly at the thumbnail rect |
| Cost discipline | Pass: open, setup and consumer counts are flat across scroll paints; the second dwell of the same node (after a one-paint detour whose parse fails) re-decodes nothing and blits the cached raster |
| Erase completeness | Pass: selection change, toggle and exit each clear thumb-active; after the painter's next repaint of the band no raster pixel survives in the framebuffer; the post-toggle paint renders at x=11 and blits nothing |
| Format coverage | Pass: FLAC, APE and WAV fixtures activate with rasters equal to the reference; the OGG picture fixture, a picture-less MP3 and a WMA stay unshifted (WMA is never even opened) |
| Scroll persistence | Pass: thumb-active survives the full scroll cycle (offsets rise and wrap) with no re-open |
| Trace parity | Pass: every paint before activation is record-identical to a picture-less twin (same name, size and tags); unselected rows render identically on the expiry paint |
| Player restoration | Pass: with a thumbnail session in between, a player-size sequence leaves the artwork context (0x40 bytes) and the request descriptor (0x10 bytes) byte-identical to a clean player-only run |

A demo GIF rendered from the emulation trace and the
framebuffer (dwell at the stock rect, the thumbnail appearing
at expiry with the text shifted, then the scroll) is in the
work directory: work/browser_marquee4/demo/marquee_v4.gif.

### Integration into the full build: updated shortfall

The v4 payload is 7,252 bytes against the full build's
636-byte module 31 spare: shortfall 6,616 bytes (v3: 5,908).
patches/full/ is untouched, and the default build is
unaffected: a framework build with the default manifest
reproduces the pinned unified image
`92c446066e715d74a719671d3ee643ed4b7587c94801eb6dc3893f2271ed944d`
byte for byte (re-verified for v4).

## Phase E notes

- Confirm the window manager keeps dispatching paints while bit
  0x148 pends in the browser (the dispatch loop was not located
  offline; the idiom is proven for the player).
- Confirm the cell unit the registrar computes on hardware in the
  browser tail context (16 under emulation with the fixture font
  class state).
- Watch the two overshoot frames at the turn (stock quirk,
  inherited).
- BMP and non-square names, FS type 3 volumes (the name fill path
  differs), and names near the 48-unit cap on real cards.
- v2: watch the selecting paint's latency on a real card (the
  parse reads a bounded head, up to about 1.2 KB across a few
  dozen reads in the fixtures) and confirm no visible stall.
- v2: confirm the (directory cluster, ordinal) identity on real
  cards whose directories contain deleted or long-name entries:
  the ordinal is the enumeration slot the browser's own walker
  assigned, and the open's fetch addresses slots directly, but
  the pair was only ever exercised against modelled fetches
  offline.
- v2: FS type 3 end to end (the open's exFAT entry handling is
  stock machinery shared with the scan, but the browser path was
  gated only at the argument level offline).
- v2: non-ASCII tag text. The fixtures were ASCII; the
  dispatcher's converters handle UTF-8 and UTF-16 in module 0,
  while Latin-1 beyond ASCII goes through the on-demand codepage
  modules (63 to 69) that the loader supplies, the same path the
  stock scan takes. Confirm with a Latin-1 fixture with high
  characters on hardware.
- v2: browsing while a track plays. The parse takes a descriptor
  slot for its duration (the scan does the same); confirm no
  audible or visible interaction when the selected file is the
  playing track, whose descriptor module 33 holds separately.
- v2: WMA stays on the v1 string unless the ASF overlay's
  residency during browsing is proven otherwise on hardware.
- v3: confirm the toggle's feel on hardware (the flip lands at
  the 200 ms mark of the hold) and that the volume ramp
  following it reads as intended; the census says the T2 event
  is delivered in the browser, but the live key path is the
  proof.
- v3: exercise very long tag fields on real cards, including
  Latin-1 high characters through the on-demand codepage
  modules, against the uncapped string.
- v3: the thumbnail placement stays an open owner decision. If
  a placement outside the row is ever wanted, the pipeline
  evidence in the v3 section is the starting point: the direct
  scan route is drivable at 36x36 for about 1M instructions and
  leaves the player's state clean.
- v4: hardware decode timing at 36x36. The full route is
  about 1M instructions under emulation; the dwell absorbs
  the wait before expiry, but the decode itself lands inside
  the expiry paint, so watch for a one-frame stall when the
  thumbnail appears, and for the transition paint's double
  draw (the decode consumer paints the thumbnail, then
  mq_show re-blits it from the cache in the same paint)
  reading as a flicker.
- v4: the gate's stack depth on the real window stack. The
  locator case helper rebuilds a 0x224-byte frame under the
  gate, inside the painter; emulation stacks are roomy, the
  hardware window stack is the proof.
- v4: the payload loads module 19 (through setup's own loader
  call) while the browser window is active, a state the stock
  code never enters: the loader zeroes module 19's BSS, which
  is module 19's by the firmware's own memory discipline, but
  confirm on hardware that nothing else parks in that range
  while browsing (the harness node pool originally did, which
  is how the collision was found).
- v4: the shifted row at native size: the thumbnail's look
  at 36x21 scaled from real covers (the fixture is a test
  pattern), the 2 px band margin, and text starting at x=48.
## v5: title-led label and full-screen background

Two changes, one of which replaced the other mid-build. The
label change was specified first and is built as specified. The
visual change went through three specified forms; the first
two were built, gated, and then cancelled by the owner before
anything shipped:

- Always-on selected-row thumbnail (built as the first v5
  form, gated, then superseded by the windowed model).
- Windowed per-row thumbnails with a deduplicated,
  half-resolution RGB332 raster store in the gap tail (built
  and gated as the second form; its census, codec study and
  traces remain the evidence base the final model reuses).
- Per-row text shift (hooks 0304 to 0309 in the v4 and
  windowed builds): cancelled; row text is stock everywhere
  in the final model.

The final visual model is one full-screen background, below.
Nothing of the cancelled forms ships: no per-row thumbnails,
no windowed cache, no deduplication, no storage codec, no
text shift.

### The label: title first, installed at selection

The selected row's displayed string is one metadata-enriched
label from the selecting paint onward: title first, then
artist, then album, joined with " - ", under the v2 field
hygiene (trim; whitespace-only counts as absent; album
artist only as the artist fallback). Lead-field rule: if the
title is absent, the file name leads and artist and album
are appended when present; the artist never leads. If
neither title nor artist exists, the label is the v1 file
string. The long-press Vol+ file view works on the same
basis: its label (name, type, size) is the row's string from
the toggle paint onward.

There is no content swap on dwell. The gate installs the
label at the selecting paint (the tag parse already runs
there); the row renders it statically when it fits, and the
1.0 s dwell governs only the scroll start when it overflows.
Unselected rows are untouched.

Composition-order change, recorded because the v2 suite's
expectations encoded the old order: v2 to v4 composed the
scroll string artist-led (artist, title, album). v5 composes
title-led because the label is now the row's standing
display string, not a dwell bonus: the field a reader looks
for first is the track title, and an artist-led string reads
as a different track when titles repeat across artists. The
v2-era assertions that changed are exactly the string-order
ones (the composed scroll strings in the tag suite, and the
artist-only fallback, which now leads with the file name and
appends the artist). The field hygiene, coverage, cache and
timing assertions all survive unchanged.

### The background model

While browsing, the selected file's album art renders
behind the whole browser menu, darkened so the list text
stays legible. Scrolling to another file swaps the
background to that file's art. One render at a time, for the
current selection only; nothing is drawn in the rows.

Acquisition reuses what the cancelled forms proved: the
direct-route picture decode (MP3, FLAC, APE, WAV in; OGG,
DSF, DFF, the M4A family, AAC, WMA, OPUS out, unchanged),
run inside the paint that resolves the selection, alongside
the tag parse, and a single key entry keyed by the selected
node's identity (node, directory cluster, file cluster,
ordinal; a negative entry suppresses re-opens). Reselecting
the same node is free; moving away and back re-decodes,
because the store holds exactly one picture. Cross-file
deduplication is out of scope by decision: album tracks
share a cover, but each selection change re-decodes it,
which the cost section prices.

The decode drives the pipeline at a 56x56 request box with
its destination at the client area's top left, so the
consumer's own blits land inside the art area during the
selecting paint and are then covered by the install draw in
the same paint (see paint integration). Capture samples the
produced rows as they arrive: the produced image is centre
cropped to the store's aspect, and each store row takes the
produced row its centre maps to, darkened per pixel at
capture (below). Rows the sampler skips (the pipeline can
end early) are filled by replicating the previous store
row.

### Store format, size, and the cache-home census

The background area is the browser client area, (0, 40) to
(239, 319): 240x280, aspect 6:7. The store is raw RGB565 at
30x35 (exact 6:7), 1,050 pixels, 2,100 bytes, darkened at
capture so no per-blit colour work remains. Expansion at
draw time is pixel replication: output pixel (px, py) is
store[(py - 40) * 35 / 280][px * 30 / 240].

The census behind the size, in the order it was run. The
brief's example sizes (80x106 at about 17 KB, 120x160 at
about 38 KB) have no proven home; the chosen store is the
largest the proven homes hold alongside the payload's code:

- Module 31 data segment append: 0 usable bytes (the append
  lands at the module's own BSS start, and BSS ends hard at
  module 18 and 61 data).
- The module 31 payload window (7,436 B, code and data
  shared): holds the store, as a union with the tag parse
  struct (the 0x556 struct reservation becomes
  max(0x556, 2,100) = 2,100 B). The union is safe by the
  gate's ordering: the parse and the decode both run inside
  the gate, the store overwrite happens there, and mq_show
  repaints at the gate exit before any other paint can read
  either tenant.
- The package-gap tail (2,044 B proven): carries the slice
  line buffer (480 B at its base); the rest is unused. It is
  scratch, rewritten per drawn row, never a store.
- Refuted again for this build, with neighbours named:
  module 19's BSS span (64,288 B) is the picture pipeline's
  own and is zeroed on its load; the 4,848 B span after
  module 18's data is picture-subsystem workspace (the
  request, descriptor and context cells live there); the
  spans after modules 12 and 9 data are player and other
  BSS soup with no provable owner; the 11,164 B package gap
  is live runtime workspace except its proven top 2,044 B;
  the decoder-space gaps at 0x01000000 are the decoder
  core's RAM. SAVEINFO's spare bytes were never a candidate.

Payload arithmetic: code 3,808 B plus data 3,184 B (state
52, string buffer 136, extension table 36, the 2,100 B
struct span, the one-entry key table 20, the two-entry tag
cache 808, picture routes 32) totals 6,992 B, leaving 444 B
spare in the window. A 36x42 store (3,024 B) was measured
first and does not fit (7,848 B total); 30x35 is the largest
exact-6:7 store the window holds with working spare.

### Darkening and legibility

Darkening is per pixel at capture, integer math, starting
from the theater finalize mixes. Dark theme: each channel
keeps 45 percent (channel * 45 / 100), the theater 55
percent mix toward black, unchanged. Light theme: each
channel keeps 25 percent and takes 75 percent of the paper
colour [242, 237, 230] (the theater light mix), because
light-theme text is black.

Worst-case contrast of the theme text colour over the
stored pixels, measured on the brightest and darkest covers
constructible (solid near-white and near-black JPEGs through
the real decode), computed with WCAG relative luminance:

| cover | theme | text | worst contrast |
| --- | --- | --- | --- |
| bright (248, 246, 242) | dark | white | 4.98 |
| bright | light | black | 19.30 |
| dark (6, 6, 9) | dark | white | 12.91 |
| dark | light | black | 10.09 |

The floor the gates assert is 4.0 (dark theme) and 7.0
(light theme); every measured case clears it. The pinch
case is a bright cover under the dark theme, as expected:
the 45 percent keep is what holds it at 4.98.

### Paint integration

The substitution point is the fill helper's call sites, not
the helper: the harness (and the panel) model the leaf
0x030632FA, so the payload hooks the six call sites whose
fills land in the client area during browser paints, and
one stub (mq_fillsub) serves all six:

| hook | site | fill it carries |
| --- | --- | --- |
| 0310 | 0x0307EA30 (module 31) | mode A row band (ground) |
| 0311 | 0x0307EA72 (module 31) | mode A selected band (accent) |
| 0312 | 0x0307EA94 (module 31) | mode A separator |
| 0313 | 0x0307EBDC (module 31) | mode B selected band (accent) |
| 0314 | 0x0306358C (module 0) | window ground (full paints) |
| 0315 | 0x03063024 (module 0) | marquee stepper text erase (accent) |

The census behind the set: mode A has exactly three fill
call sites in its row loop; mode B has one (it relies on the
window ground fill for the rest); the paint framework's
window ground fill is one call covering the whole client
area; the stepper's erase is one call with the accent over
the text rect. The status area at the top (y 0..39) is never
filled by the browser painter at all: it is window chrome,
accounted here rather than substituted, and the art area
starts at y 40 for that reason.

The stub's contract is the fill's own (rect in r0..r3,
colour at [sp]). While a background is installed, it clips
the rect to the client area and classifies the colour: the
accent (palette cell at 0x030235B8) draws the slice mixed
halfway toward the accent; the ground (0x0000), the
separator (the halfword at the browser context) and the
palette ground cell draw the plain slice; anything else,
and everything while no background is installed, tail
branches to the stock fill with its arguments restored
untouched. The module 0 sites serve every window and the
player's marquee too; the guard is the payload's
background-active byte, set only inside the browser gate
and cleared on exit, so no other window's fills change.

The selection band treatment is the accent-tinted slice:
the stored pixel mixed halfway toward the accent per
channel. It keeps the band's shape and position identical
to stock, keeps art visible inside it, and stays
distinguishable from the plain art around it; the demo
renders it for review. The stepper's erase uses the same
tint, so a scrolling label erases to the band's own
background, not to flat accent.

Two ordering facts make the model exact rather than
approximate. First, on the selecting paint the row loop
runs before the gate resolves the new selection, so its
fills substitute (or flat-fill) under the previous
selection; the gate then decodes, and mq_show at the gate
exit makes the install the paint's final word: the whole
client area drawn from the new store, plain except the
selected band, which is drawn tinted. Every paint that
changes the background therefore ends in the same state.
Second, when the new selection has no picture, mq_show
repaints the client area with the theme's flat ground
(black, or the palette ground cell in the light theme), so
the fallback is the exact stock ground, not a faded
remnant.

Steady paints do no full redraws: paints that change
nothing cost the flag checks only, and the background
maintains itself because every later fill inside the area
substitutes its slice. The creep gate (below) samples panel
points after selection moves, scroll steps in both
directions, marquee runs and view toggles, and asserts the
stored expansion everywhere, with the tint inside the
selected band.

### Lifecycle

Selecting a pictured file installs its background in that
same paint. Selecting a folder, a picture-less file or an
unsupported file restores the exact stock ground in that
paint and records the negative entry. Leaving the window
zeroes the payload state and the key entry (exit hook, as
in every version), so nothing survives; returning re-renders
from the current selection on its selecting paint. The
player-restoration proof passes: the picture pipeline's
context and descriptor bytes after a browser decode match
the pre-decode snapshot byte for byte.

### Costs, measured

Instruction counts on the variant image, whole paint
(painter plus gate):

| paint | instructions |
| --- | --- |
| pictured selecting paint (parse, decode at the 56 box, capture, install slices) | 3,274,505 |
| picture-less selecting paint | 26,232 |
| steady paint, background installed | 334 |
| dwell-expiry paint | 1,601 |

Against the recorded baselines: the v4 selecting paint
(parse only) was 20,394 and its dwell-expiry decode paint
991,258 at a 36x36 target; the cancelled windowed build's
pictured selecting paint was 1,537,463. The background
model's selecting paint is the expensive one of the three
by design: the decode box is larger (56x56 against 36x36)
and the install draw writes 240x280 output pixels through
per-pixel address division.

Fast-scrolling implication, stated plainly: every selection
stop on a pictured file costs one paint of about 3.27M
instructions, most of it the install slice. Scrolling
rapidly through a pictured folder pays that per stop. No
settle delay is implemented; it is flagged as a tunable in
the Phase E list with this number beside it, because
whether 3.27M instructions is a hitch or a pause is a
hardware question the emulator cannot settle. The obvious
optimisation (a per-row slice address table in place of
per-pixel division) is likewise left to Phase E evidence.

### Gates, and the expectations that changed by design

Suites: test_browser_marquee.py (v1), _tags (v2), _v3 and
_v5 pass. test_browser_marquee_v4.py gated the frozen v4
variant (05db1334) and could not run against this builder,
so it was retired; commit 05db1334 keeps it as the v4 record.

Expectations updated by design, listed explicitly:

- Tag suite fetch expectations: the selecting paint fetches
  the parse plus one background probe of the selected file
  (picture routes only). The windowed build's per-row probes
  of every visible file are gone; folder and WMA selections
  fetch nothing at all.
- Tag suite cache test: reselecting A after B costs one
  background re-probe (the store holds one entry), where the
  windowed build held every visible row's entry and
  re-probed nothing. The string cache behaviour is
  unchanged.
- v3 toggle test: the same fetch update (parse plus probe).
  Toggle behaviour itself is unchanged, and the background
  follows the selection across view toggles because its key
  does not involve the view.
- The v5 suite is rewritten for this model: store equality
  against the reference pipeline capture (crop, sample, mix),
  framebuffer equality against the store's expansion (plain
  slices, tinted selected band), per-theme darkening and the
  contrast floors above, stock-ground fallback exactness for
  folder and picture-less selections, the creep session,
  single-entry discipline (same node free, A to B to A
  re-decodes), exit cleanliness and return re-render, mode B
  substitution, and the player-restoration proof.

Two harness corrections from the windowed build carry
forward: the tag suite's _bind fix (the file key is tracked
across close and reopen) and its per-call instruction
budget of 16,000,000, both still needed and unchanged.
One fallback nuance the gates pin down: the paint that
removes a background ends all-ground, because the restore
fill is that paint's final word and the row loop ran before
it under the old background; the v5 gate asserts the whole
written client area is the ground colour or a text marker
on that paint, and stock layout parity from then on rests
on the v1 suite (with no background installed the fill stub
is a pure pass-through).

Build defects found by the gates and fixed in this build,
recorded because they are the kind that pass review: the
background's produced-row origin halfword (state +0x2A)
spans the byte the label-fresh flag occupied (+0x2B), so
every decode silently cleared the flag and the label never
rendered on the selecting paint; the flag moved to +0x0A.
And the slice's tint path used its own flag register as a
channel scratch, so only the first pixel of each tinted row
was tinted; the flag is now restored at the end of the tint
path. The accent cell is 0x030235B8 (the mode A literal at
0x0307EE28); an earlier reading of 0x030235BA was an
off-by-four in the literal pool and is corrected wherever
it appeared.

### Accounting

Payload 6,992 B in the module 31 growth window (3,808 code
+ 3,184 data), 444 B spare. Variant image 13,638,484 B,
SHA-256
7d955caaf32e0a731ec08ba38f90e1063f16a70e2a5f6c14f1d577508915a8f3. Hooks: the four standing hooks (0300
gate, 0301 key, 0302 exit, 0303 toggle) plus 0310 to 0315
above; hooks 0304 to 0309 do not exist in this variant. The
gap tail ships as 2,044 zero bytes and carries the slice
line buffer at runtime. Full-build composition: against the
full build's module 31 growth, the shortfall is 6,192 B on
the same basis as the v4 note (payload minus the 800 B the
full build's growth leaves), so the variant remains
standalone.

Demo: work/browser_marquee5/demo/marquee_v5_background.gif
and marquee_v5_background_sheet.png, composited from the
emulation framebuffer after real paints: album A selected
(art installed, darkened), the label scrolling while the
art holds, the next track of the same album (same picture,
band moved), and a different, bright album (background
swapped, worst contrast 4.98). The fixture cover is the
theater probe JPEG (an abstract test image), so the demo
shows geometry and legibility rather than photography.

### Phase E items

- Hardware decode timing at the 56x56 request inside the
  selecting paint, and the panel cost of 280 slice rows per
  background change.
- The settle-delay tunable: if per-stop cost is a visible
  hitch on hardware, gate the decode on the selection
  resting (the dwell constant is the natural knob) at the
  measured 3,274,505 instructions per pictured stop. Not
  implemented; needs the hardware number first.
- Panel behaviour of slice-substituted fills: the
  substitution redraws through the row blitter; banding or
  tearing at band boundaries is a hardware observation.
- The light theme's ground colour for the fallback repaint
  is the palette ground cell, read live; the gates run under
  the dark harness palette, so the light fallback is proven
  in arithmetic (the mix and contrast gates run in both
  themes) but its panel colour is a hardware check.
- Browsing while a track plays: decode contention with the
  player's own picture pipeline is untested by construction
  (the restoration proof covers state, not timing).
## v6 study: a higher-resolution background, two routes measured

Owner's question after v5 shipped: the 30x35 store reads as
a soft wash; can the background be shown at full resolution
instead? Two routes were investigated with measurements
before anything was built. Neither clears its gate, so v6
does not exist as a variant: v5 stands unchanged. The
measurements, the census and the decision are recorded here
because they close the question rather than leave it open.
Scripts and logs: work/browser_marquee6/ (route_a_stream.py,
route_a_rowcost.py, route_a_rowcost2.py,
route_a_fillorder.py, route_a_residency.py, route_a_mix.py,
route_b_datagrow.py, census_segments_rerun.txt). Comparison
render: route_ab_sheet.png in the same directory: one
cover's real produced rows shown as the v5 store holds
them, as a 120x160 store would hold them (simulated by the
same capture rule, since no home exists to build), and as
the Route A stream delivers them.

### Why resolution is expensive here

The panel is write-only for the payload's purposes: there
is no framebuffer to re-read, so every repaint demand (row
band fills, the selection band, the marquee stepper's erase
every 300 ms) needs its art slice again from somewhere.
v5's answer is the store. The two routes are the two ways
to not have a small store: re-derive the slice on demand
(Route A, streaming), or hold a bigger store (Route B).

### Route A: streaming, no store

Model: no raster is kept. The background paints by
streaming the picture pipeline at a full-width request
(cover-fit to the client area: box 240x280, destination
(0, 40); produced geometry is fit-inside, so square art
produces 240x240 and the tall 6:7 fixture produces exactly
240x280). A repaint slice is restored by re-acquiring the
picture (stock open, locate, setup) and streaming from the
top: the consumers pull rows in order and the cursor
advances monotonically, so a slice at depth d is priced by
the stream down to its last row. Darkening applies per row
between the consumer's decode and the row's draw.

The pipeline's cost profile is the finding. Per produced
row at 240 wide, steady state, by fixture (acquisition is
fixture-independent at about 85,000 instructions; the first
row carries a warm-up premium of about 2x):

| source | per-row | per pixel | full pass |
| --- | --- | --- | --- |
| probe JPEG 30x18 | 239,682 | 999 | 57.6M (240 rows) |
| photo-like 500x500 | 323,841 | 1,349 | 77.8M |
| photo-like 1000x1000 | 384,939 | 1,604 | 92.5M |
| photo-like 480x560 (6:7) | 316,142 | 1,317 | 88.6M (280 rows) |

The pipeline's scaler costs on the order of 1,000
instructions per output pixel regardless of source (the
player's own 144x144 geometry measures 1,028 per pixel, so
this is the stock pipeline's normal behaviour, not a
harness artefact); the entropy term adds on top for real
photographs. That is also why v5 is cheap: it decodes at a
56-wide box, about 2.0M of its 3,274,505-instruction
selecting paint.

Fill order within one paint, traced on the v5 variant
(route_a_fillorder.py, the six fill sites v5 hooks):

- A stepper paint makes exactly one demand, the selected
  row's text rect, and it recurs every 300 ms for as long
  as a label scrolls.
- A selection-move paint is monotone when the selection
  moves down (old band, separators, new band: one pass to
  the deeper band). When the selected row itself is drawn
  by the row loop, the painter demands its band twice in
  one paint, ground fill then accent fill over the same
  rect (observed in the selecting paint, the move-up paint
  and the full repaint): a sequential stream has passed
  those rows by the second demand, so the paint needs two
  passes even before the gate's install is counted.
- A full repaint on hardware adds the paint framework's
  window-ground fill (whole client area, one rect) ahead
  of the row loop (its position is from the framework's
  structure; the harness enters at the window's Paint
  callback and does not drive it). Served by a stream, the
  loop's later demands sit above the stream head and
  restart it, the selected row's double demand twice
  more.

Repaint prices that follow (photo-like 500x500 curve;
restore = acquisition + stream to the slice's last
produced row):

| repaint | price |
| --- | --- |
| stepper erase, selected band 0 | 9.9M |
| stepper erase, selected band 2 | 35.8M |
| stepper erase, selected band 5 | 74.6M |
| stepper erase, selected band 6 (6:7 art) | 85.5M |
| selection move 0 to 2 | 39.6M |
| selection move 2 to 0 (two passes) | 26.8M |
| selecting paint (one install pass) | 77.8M |
| full repaint (ground pass + selected-row restarts) | 97.6M and up |

Budget and verdict. The defended budget is the selecting
paint v5 already pays once per pictured selection,
3,274,505 instructions: a repaint kind that recurs may not
cost more than the design's most expensive one-off event,
and the stepper erase recurs every 300 ms for the whole
scroll, so even meeting that budget would mean about
10.9M instructions per second sustained. Measured against
it, the cheapest recurring repaint (band 0 erase, 9.9M)
is 3.0x over; a mid-list erase is 10.9x over; the worst
is 26.1x over and recurs at about 249M instructions per
second of scrolling. Selection moves cost 8x to 27x the
selecting paint each. Route A fails on cost at every band
depth, by one to two orders of magnitude. The darkening
mix is not a factor in this: assembled and counted, it is
5,762 instructions per 240-pixel row (1.61M per pass,
about 1.8 percent of one decode row).

Residency, for the record (route_a_residency.py):

- The picture context is single-owner. In the harness, a
  player setup for one file followed by a browser setup
  for another leaves the player's next consumer call
  emitting the browser's stream (a 240-wide row at the
  browser's destination, where the player's geometry was
  144 wide at (23, 36)). A session-long open stream is
  therefore not ownable; the workable shape is
  re-acquisition per repaint under v5's snapshot and
  restore discipline, which is what the prices above
  assume.
- The loader evicts without bookkeeping: loading module
  20 overwrites module 19's code at their shared base
  0x03085A4C, loading module 61 overwrites module 18's
  code at 0x03080B54, and loading module 19 zeroes its
  whole 64,288 B BSS. Module 18 itself loads worker 20
  from inside its own flows (at 0x03080C80), so a held
  stream's code can be replaced by the picture
  subsystem's own format alternation.
- What remains Phase E under the re-acquisition shape is
  the same class as v5's existing note (track changes
  while browsing, window flows on hardware), but at erase
  frequency instead of selection frequency. The route is
  already dead on cost, so these were not pursued.

### Route B: a bigger store

The census, settled with the segment records and the
framework's own insert tool (route_b_datagrow.py,
census_segments_rerun.txt):

- Module 31's data segment: exec 0x030247C4, 80 B, in the
  shared window-data arena. Its BSS follows at 0x03024814,
  4,400 B, ending at 0x03025944, where module 18's data
  (180 B) and module 61's data (79 B) sit, then module
  18's BSS to 0x03026CE5, modules 19 and 20's data at
  0x03026CE8, and module 19's 64,288 B BSS.
- The insert tool does support data growth mechanically
  (segment kind 'data'; records, section offsets and the
  CRC are recomputed). It never moves BSS fields: appended
  bytes land at exec (data exec + data len), which for
  module 31 is 0x03024814, its own BSS start. A 120x160
  store grown there spans 0x03024814..0x0302DE14: through
  the browser's own BSS, module 18's data and BSS, the
  picture request and context cells, and the decoder
  workers' BSS. The loader copies the data segment and
  zeroes the declared BSS on the same activation, so the
  store would be erased by the browser's own load even
  before the overlap with live workspace is counted. A
  data growth buys exactly zero usable bytes, as the v5
  census said, now with the mechanism shown.
- Every proven arena is smaller than the smallest priced
  store (80x106, 16,960 B): module 31's whole BSS is
  4,400 B and is live browser workspace; the module 31
  payload window totals 7,436 B (444 B spare in v5); the
  package-gap tail is 2,044 B; the span after module 18's
  data is 4,848 B of picture-subsystem workspace. The
  shortfall against the most generous candidate is at
  least 9,524 B.
- Module 19's BSS (64,288 B) has the capacity and fails
  residency twice over: it is zeroed at every module 19
  load, and a sentinel study shows the decoder writes
  across effectively the whole span during one ordinary
  decode (after a 56-box decode of a 500x500 cover, 17
  of 64,288 sentinel bytes survive, with no untouched
  run of 256 B). It is the decode worker's scratch in
  fact, not only in declaration.
- The one capacity-shaped remainder is append past
  module 39's code end at 0x0309F4AC, the highest exec
  end of any segment in the image (a 120x160 store would
  span 0x0309F4AC..0x030A8AAC). It is not a proven home:
  no artefact in the image establishes that RAM exists
  past that address (the harness maps 5 MB from
  0x03000000 as a modelling convenience), and growing
  module 39's record makes its own loader copy, run by
  the library scan and sort flows, land on the store at
  every activation. The hardware test that would settle
  the first point is a Rockusb pattern write and
  read-back across 0x0309F4AC..0x030A8AAC after boot,
  scan, sort and playback; the second point stands
  regardless, and the decision rule for this route
  required a proven home with no residency conflicts.

Verdict: Route B fails. No proven home reaches even the
80x106 store, and the 120x160 bar is not met by any
candidate.

### Decision

Neither route clears its gate, so nothing is built and
v5's 30x35 store remains the design. The comparison
sheet (route_ab_sheet.png) shows what is being given up:
the full-res stream and the 120x160 store are visibly
better, and both are priced out by the platform, one by
the scaler's per-pixel cost on a write-only panel, the
other by the RAM map. If Phase E ever proves RAM past
0x0309F4AC (the canary above) the Route B question can be
reopened for the module 39 append with the residency
conflict stated; if a future pipeline path decodes
cheaper per pixel, Route A's erase price is the number
to re-measure first.
