# Lock-screen unknowns: evidence (DP3_V137, offline RE)

Scope: four open questions for the planned lock-screen info patch, resolved
from the extracted module binaries in `extracted/`. Every claim carries an
address. Negative results state what was scanned. Nothing outside this file
was modified.

Method / scans performed:

- Raw Thumb BL/B.W encoding scan over **all** extracted `module_*_code_*.bin`
  files for targets `0x0306723C` (post), `0x03067258` (test-clear),
  `0x0306729C` (test-noclear), `0x0306727E` (clear), `0x030632FA`,
  `0x0306316E`, `0x0306314A`, `0x030630C2`. (BL targets computed with
  unaligned `PC = addr+4`; an aligned-PC variant missed known sites and was
  discarded.)
- Capstone linear-sweep and skipdata censuses of the same targets
  (647 post-call sites total under skipdata).
- Raw dword searches across all extracted bins for `0x03023CF8`,
  `0x03023CFC`, `0x030235CE`, `0x030235B4`, `0x03023980`, `0x0302309C`.
- Capstone scan for `movw/movt` immediates `#0x3CF8/#0x3CFC/#0x3D00`
  (computed bitmap-address construction).
- Direct range disassembly (`work/ui_features/build/disx.py`) of every
  function cited below.

Flag API confirmation (module 0, `0x0306723C–0x030672D0`): post
`0x0306723C`, test-clear `0x03067258`, clear `0x0306727E`, test-noclear
`0x0306729C` all load the bitmap base from the literal at `0x030672B8` =
`0x03023CF8` and index `word[r0>>5]`, bit `r0&31`. Matches the brief.

---

## Item 1: painter flag cadence

**Verdict: EVENT-ONLY. No periodic poster of flag `0x2E` (or `0x27`) exists
in any scanned module. During steady playback nothing reposts the painter's
flags, on a per-second basis or otherwise.**

### The painter is a shared template

The status painter exists as byte-parallel copies in module 0
`0x03055A26`, module 5 `0x0307D2EE`, module 22 `0x0307D8B2`, module 23
~`0x0307E528`, module 27 ~`0x0307E7C4`, **module 31 `0x0307E804`**, module 32
`0x0307FFB0`. Structure (module 31 addresses):

- Entry `0x0307E804`: `cmp r0,#1`; if equal, it re-posts its own flags
  (post `0x27` @`0x0307E818`, `0x28` @`0x0307E81E`, `0x2C` @`0x0307E824`,
  `0x2D` @`0x0307E82A`) and returns without drawing.
- Tail entry `0x0307E832`: `movs r0,#0x2E; b.w 0x0306723C`, a standalone
  post-`0x2E` stub.
- Else path: test-clear `0x27` @`0x0307E80E`, `0x28` @`0x0307E846`, `0x2C`
  @`0x0307E85C`, `0x2D` @`0x0307E870`, `0x2E` @`0x0307E886`; each set flag
  draws one icon via DrawImage `0x03063700` (byte offsets `+0x107`, `+0x105`,
  `+0x8F`, `+0x109` of a state struct); the `0x2E` segment loads the byte at
  `0x030230EC` @`0x0307E892`, `ubfx r0,r0,#2,#1; adds r0,#0x26; b.w
  DrawImage` @`0x0307E898` (hold icon 38/39).

Invocation: no direct BL/B.W caller of `0x0307E804`/`0x0307E832` exists in
any code bin, and no dword pointer to either (`0x0307E804/05`,
`0x0307E832/33`) exists in any extracted bin or in `DP3_V137.img`. Module
31's data bin (`module_31_data_030247c4.bin`) lists callback pointers
`0x0307DA8B, 0x0307E5B9 (Key), 0x0307ED41 (Display), 0x0307D6A1, 0x0307D777`
at offsets `0x34–0x4C`; the painter entries are not among them. Module 0's
generic service dispatch at `0x03067302` walks runtime lists calling
callbacks at node `+0x14` (blx @`0x0306731E`), `+8`, `+0xC`. The painter is
reached through runtime-registered callbacks, i.e. on window/display events.

### Every poster of flags `0x27–0x2E`

| Poster | Sites | Trigger |
|---|---|---|
| Painter template, arg==1 path (7 copies) | e.g. mod31 posts @`0x0307E818/E81E/E824/E82A`; tail post-`0x2E` stub @`0x0307E832` (mod0 tail @`0x03055A54`, mod5 @`0x0307D31C`, mod22 @`0x0307D8E0`, mod32 @`0x0307FFE0`) | The painter re-flagging itself when invoked with arg 1 (a window/display event), not a timer |
| Module 0 "invalidate" helper `0x03063A32` with arg 1 | posts `0x27` @`0x03063A44`, `0x28` @`0x03063A4A`, `0x2C` @`0x03063A50`, `0x2D` @`0x03063A56`, `0x2E` @`0x03063A5C` (also `0x1F`, `0x19A`) | Called with r0=1 and r0=0 bracketing draws (e.g. module 31 Display @`0x0307E96C`/`0x0307E972`); callers in modules 5, 9, 21, 23, 27, 31, 32, 81, on window/draw transitions |
| Module 0 state-change handler (fn containing @`0x03065386`, @`0x03065426`) | posts `0x27` on two parallel paths gated on flag `0x12`; also `0x13`, `0x188`, `0x18`; writes SAVEINFO `+0x3E` | Playback/file state change |
| Module 0 change detector `0x030656EE` | posts `0x2C` @`0x0306571E`, `0x28` @`0x0306572E`, `0x2D` @`0x03065742`; never `0x27` or `0x2E` | Change-only: compares three state bytes against caches at `0x0302312E`, `0x0302312D`, `0x0302312F` (the third is the boolean of SAVEINFO `+0x17`, read @`0x0306570A`) and posts only when a value differs, updating the cache. None of the three is a time or position counter |
| Module 30 | post `0x2C` @`0x0307EDAE`, in a cluster gated by test-clear of flag `0x12C` @`0x0307EDCE` | Event (flag `0x12C` consumption) |

Flags `0x29/0x2A/0x2B` are not painter flags (the painter tests only `0x27,
0x28, 0x2C, 0x2D, 0x2E`). Posts of `0x29` occur at module 33 @`0x03089D36`
and @`0x0308A360`, module 81 @`0x0307DE0E` and @`0x0307DEA4`; module 33
test-clears `0x2B` @`0x0308A232`; no poster of `0x2A` was found. Module 33
posts nothing in `0x27–0x2E` except the `0x29` sites above.

Non-immediate-r0 post sites (647 total under skipdata) were spot-checked in
module 31 (@`0x0307E470`, @`0x0307E52A`, @`0x0307E550`, @`0x0307EB16`,
@`0x0307EC50`, @`0x0307D6CC`, @`0x0307D6E0`): all are `mov.w` immediates
`0x144`, `0x148`, `0x14B`, `0x14D`, outside the painter range.

### The periodic paths, examined and excluded

- **Clock/status service `0x03065FD4`** (module 0): its only caller is the
  service dispatch @`0x03067320` (inside `0x03067302`), so it is polled once
  per service cycle. @`0x030660C0` it derives a value from a free-running
  timer via reciprocal `0x51EB851F` (literal @`0x030662C0`, ≈ timer/100) and
  compares it with a stored counter at struct `0x03023918 +0x14`; on change
  it advances a seconds counter (cmp `0x3C` @`0x03066100`), minutes byte
  (cmp `0x3B` @`0x0306610C`), hours byte (cmp `0x17` @`0x03066120`) and a
  date struct. It posts no flag itself; it calls the change detector
  `0x030656EE` @`0x03066186` on every invocation, which posts only on state
  change (above) and never `0x2E`.
- **Dispatcher region `0x03061C10–0x03061CA0`** (module 0): entry test-noclear
  flag `0x15` @`0x03061C10`; calls tick fn `0x03061E78` @`0x03061C1A`.
  Countdown halfword is `[0x0302309C + 0xA]` (base via literal pool
  @`0x03061918`/`0x03061D60`). If countdown < 6 (cmp @`0x03061C48`): post
  flag `0x95` @`0x03061C70` only. If countdown ≥ 6: clear flag `0x25`
  @`0x03061C4E`, post flag `0x24` @`0x03061C54`, reset countdown to 0
  @`0x03061C58`. Delta path @`0x03061C76`: `delta = [r7] − [r4]`; if
  `delta ≤ 0x50`, exit; if `delta > 0x50` and countdown ≠ 0 (cbz
  @`0x03061C82`): post `0x95` @`0x03061C86` and decrement the countdown
  @`0x03061C8C–0x03061C98`; if countdown == 0, no post. This path posts
  only `0x95` (plus `0x24` on the ≥6 branch), no painter flag, and the
  painter consumes neither `0x95` nor `0x24`. (Module 31 Display bodies
  test-noclear `0x24` @`0x0307E93E` for an unrelated purpose.) The wider
  dispatcher also posts `0x1A4`/`0x24` @`0x03061B34`/`0x03061B44`, `0x1A2`,
  `0x1A3`, `0x1C4`, `0x19A`, `0x1C5`, `0x18`, `0x16`. None is in `0x27–0x2E`.
- **Module 31 Service dumps** (`mod31_svc_a/b/mid.txt`, function
  `0x0307DEB8`): contain no test-clear/test-noclear calls at all. They contain only
  posts, all track/action events: `0x19A` @`0x0307DCAC`/`0x0307DD30`,
  `0x143` @`0x0307E040`, `0x14D` @`0x0307E0BA`/`0x0307E27E`/`0x0307E302`/
  `0x0307E344`, `0x14C` @`0x0307E150`, `0x141` (several), `0x144`
  @`0x0307E6F0`, with clears of `0x148`/`0x17B`/`0x17D`. The adjacent
  Service function (@`0x0307DA9A–0x0307DC7C`) tests flags `0x14A`
  (test-clear @`0x0307DB74`), `0x149` (test-noclear @`0x0307DBAC`), `0xD9`
  (test-noclear @`0x0307DBB4`, test-clear @`0x0307DBC4`), `0xDA`
  (test-noclear @`0x0307DBBC`), `0x14E` (test-clear @`0x0307DC12`). None is in
  `0x27–0x2E`. Module 31's repaint triggers are its callers' actions
  (track context established/changed), not flag tests on painter flags.

### Direct bitmap writes: negative

- Raw dword search for `0x03023CFC` (bitmap word covering flags `0x20–0x3F`)
  across all extracted code bins: 0 hits.
- Raw dword search for the bitmap base `0x03023CF8`: exactly 1 hit, the
  flag functions' own literal pool at module 0 `0x030672B8`.
- Capstone scan for `movw/movt` building `#0x3CF8/#0x3CFC/#0x3D00` in any
  code bin: no hits. No computed direct bitmap writes exist outside the
  flag API.

### Patch implication

A position readout hooked into the `0x2E` segment will go stale between
track/state changes. The patch must supply its own repost/timer; no stock
periodic repaint of the painter exists to ride on.

---

## Item 2: "text draw" `0x030632FA` stack argument

**Verdict: VALUE, not POINTER, and not an ID either. The stack argument is
a by-value 16-bit pixel (color) value. `0x030632FA` is a rectangle fill,
not a text draw. This refutes the "text draw" label in
`ui_features.md` §1.7 and `saveinfo_lock.md` §2.8.**

### The function itself (`0x030632FA–0x0306333A`, module 0)

- Pushes 8 registers; copies `r7=r3, r6=r2, r5=r1, r8=r0`, `uxth` on all
  four; loads the stack argument `sb = [sp,#0x20]` @`0x0306330E` (first
  caller stack slot after the 8-register push).
- Calls clip/setup fn `0x03063F10(r0..r3)` @`0x03063312` (clamps coordinates
  against `0xEF`/`0x13F` screen bounds).
- Nested loops: outer over `y = r1..r3`, inner over `x = r0..r2`; body is
  `mov r0, sb; bl 0x03063E60` @`0x03063324–0x03063326`, once per pixel cell.
  The stack argument is never dereferenced, never incremented, never used
  as an index. It is passed by value, unchanged, every iteration.
- Callee `0x03063E60` stores its `r0` argument as a halfword into the
  framebuffer, `strh.w r0,[r2, r1, lsl #1]` @`0x03063EA0` / `strh
  r0,[r2]` @`0x03063EC2`, at a cursor taken from the display struct, then
  advances the cursor. So the stack argument of `0x030632FA` is the 16-bit
  pixel value written to every cell of the rectangle:
  `0x030632FA(x0, y0, x1, y1, [sp] = pixel)`.

The neighbouring function at `0x0306333E` is the actual halfword-string
renderer: it loads a stack-arg pointer pair via `ldrd r0,r5,[sp,#0x28]`,
steps `ldrh r0,[r5],#2` @`0x03063390`, and calls `0x03063E60` per glyph.

### Call-site census

Raw BL scan of all extracted code bins: **87 call sites**. Validation: 86
of 87 are reached on an instruction boundary when disassembling a 64-byte
window ending at the call, and show a preceding `str …,[sp]` stack store
and an `ldrh` in that window; the two exceptions are genuine sites whose
stack store lies >64 B earlier (module 31 @`0x0307EA30`, store
@`0x0307E9C0`; module 32 @`0x0307D6B0`, store @`0x0307D662`). Per module:
mod0 5, mod5 2, mod9 15, mod21 10, mod22 1, mod23 5, mod27 11, mod30 6,
mod31 4, mod32 22, mod81 5. Full list:

- mod0: `0x03063024, 0x0306358C, 0x030635EC, 0x03063ADE, 0x03063C10`
- mod5: `0x0307D1F0, 0x0307D3D2`
- mod9: `0x03080026, 0x03080038, 0x0308005C, 0x030800AA, 0x030801CA,
  0x030801E6, 0x03080202, 0x03080220, 0x0308023C, 0x03080258, 0x03080272,
  0x0308028E, 0x030802AA, 0x030807EA`
- mod21: `0x0307DE58, 0x0307DF4A, 0x0307DFD0, 0x0307E002, 0x0307E062,
  0x0307E114, 0x0307E206, 0x0307E22E, 0x0307E240, 0x0307E372`
- mod22: `0x0307DB98`
- mod23: `0x0307E6A6, 0x0307E7AA, 0x0307E7C4, 0x0307E7EA, 0x0307E804`
- mod27: `0x0307EFB8, 0x0307F27A, 0x0307F31C, 0x0307F542, 0x0307F6AE,
  0x0307F7E6, 0x0307F90E, 0x0307FC46, 0x0307FC6E, 0x0307FC80, 0x0307FE9C`
- mod30: `0x0307EDE6, 0x0307EE14, 0x0307EE32, 0x0307EE5E, 0x0307EE9A,
  0x0307EF90`
- mod31: `0x0307EA30, 0x0307EA72, 0x0307EA94, 0x0307EBDC`
- mod32: `0x0307D37A, 0x0307D580, 0x0307D5A6, 0x0307D5B2, 0x0307D5FE,
  0x0307D66E, 0x0307D6B0, 0x0307F17A, 0x0307F2FE, 0x0307F310, 0x0307F3D0,
  0x0307F3E2, 0x0307F3F2, 0x0307F42A, 0x0307F5D6, 0x0307F5E8, 0x0307F5FA,
  0x0307F60A, 0x0307F61C, 0x0307F8C8, 0x0307F8DA, 0x030800F8`
- mod81: `0x0307D566, 0x0307D662, 0x0307D71A, 0x0307D798, 0x0307D810`

At essentially every validated site the stack slot is written with a
halfword loaded from a cell, pattern `ldrh r0,[<cell>]; str r0,[sp]`,
never with an address.

### Fully traced site

Module 5 @`0x0307D1E0–0x0307D1F0`: `ldr r0,[pc,#0x3A4]` → literal
@`0x0307D588` = `0x030235B4`; `ldrh r0,[r0]` @`0x0307D1E8`; `str r0,[sp]`
@`0x0307D1EA`; then `r1=0xB9 (185)`, `r2=0xEF (239)`, `r3=0x13F (319)`,
`r0=0`; `bl 0x030632FA` @`0x0307D1F0`. Stack arg provenance: the contents
of halfword cell `0x030235B4`, a global color cell beside the name
buffer, not a buffer address.

Corroborating traced sites: module 5 painter @`0x0307D3C2–0x0307D3D2`
(stack = `ldrh` from the same `0x030235B4` cell; `r0=0, r1=0, r2=0xEF,
r3=0x13F`, a full-screen 240×320 fill); module 31 @`0x0307EA30` (stack
loaded from literal @`0x0307EA2C` = `0x030235B4` @`0x0307E9B8`, stored
@`0x0307E9C0`; `r0=0, r1=0x28+row*40, r2=0xEF, r3=0x4E+row*40`); module 32
@`0x0307D6B0` (stack = `ldrh r1,[r1]` @`0x0307D660` from a cell, `str
r1,[sp]` @`0x0307D662`); module 27 @`0x0307F27A` (stack = `ldrh.w
r0,[r8,#4]` @`0x0307F26C`; `r0=0, r1=0, r2=0xEF, r3=0x27`); module 30
@`0x0307EDE6` (stack = `ldrh r0,[r4]` @`0x0307EDD8`; full-screen geometry);
module 0 @`0x03063ADE` (`r0=0x14, r1=8, r2=0x32, r3=0x14`, stack = `ldrh`
from a cell @`0x03063AD6–0x03063AD8`); module 21 @`0x0307DE58` (stack =
`ldrh` from a cell @`0x0307DE46–0x0307DE48`).

### Patch implication

The planned patch cannot draw the track name with `0x030632FA`. It needs
the halfword-string renderer at `0x0306333E` or the text routine
`0x03062CEE` (Item 3), whose signatures were only partially read here.

---

## Item 3: name buffer `0x030235CE` encoding

**Verdict: UTF-16-style wide string. One code unit per halfword,
NUL-halfword terminated. ASCII text appears as its code value in the low
halfword (e.g. newline is the halfword `0x000A`), not as two ASCII bytes
packed per halfword.**

### References (raw dword search, all extracted bins)

Exactly 6 literal-pool hits: module 22 @`0x0307D710`, module 24
@`0x0307EDE8`, module 31 @`0x0307DCFC`, @`0x0307E144`, @`0x0307E570`,
module 34 @`0x0308C664`. The module 34 hit is a literal-pool coincidence
(the bytes decode as `adds r5,#0xce` inside unrelated code @`0x0308C664`);
no instruction in module 34 loads it. The module 22 hit @`0x0307D710` is
the destination pointer of module 22's snapshot loop (below).

### Who writes it

1. **Snapshot copy loop, module 31 Service** @`0x0307DC3C–0x0307DC4C`,
   inside the flag-`0x14E` branch (test-clear @`0x0307DC12`), gated on
   SAVEINFO `+0x60` == 1 (@`0x0307DC24–0x0307DC28`):
   `ldr r1,[pc]` → literal @`0x0307DCFC` = `0x030235CE` @`0x0307DC38`;
   loop `i = 0..0x7F`: `add r2, r5, i, lsl #1` @`0x0307DC3C`; `ldrh
   r2,[r2,#0x87]` @`0x0307DC40`; `strh r2,[r1, i, lsl #1]` @`0x0307DC44`.
   Source: halfwords at `[r5 + 0x87 + 2i]`, where `r5` is the SAVEINFO
   struct base `0x030232A0` (same base as the `+0x60` gate and the `+0x85`
   index halfword copied @`0x0307DC2E–0x0307DC36` to `0x030235C0` and
   `[0x03023980+0xF2]`). So the source is the track-name field inside
   SAVEINFO at `+0x87`, 0x80 halfwords. The prior-work claim "copied from
   a browser struct" is wrong; the immediate source is SAVEINFO.
2. **Identical snapshot loop, module 22** @`0x0307D4BA–0x0307D4CC`, gated on
   `[sb+0x60]` @`0x0307D4A4`: `ldrh r3,[sb + 0x87 + 2i]` @`0x0307D4BE`;
   `strh r3,[r1, i, lsl #1]` @`0x0307D4C2`, with `r1` loaded @`0x0307D4B0`
   from the literal @`0x0307D710` = `0x030235CE`.
3. **Copy-helper fills, module 31**: `0x030630C2(r0=4, r1=0x030235CE,
   r2=0x80)` @`0x0307E06E` (literal @`0x0307E144`) and @`0x0307E21A`
   (literal @`0x0307E570`), both in node-action flows, the first preceded
   by `0x0305B2C2(r0=1, r1=[r4+8], r2=sp+0x20, r3=[sl+4])` @`0x0307E060`
   whose halfword result is stored @`0x0307E064`. `0x030630C2` (module 0,
   `0x030630C2–0x03063106`) computes a source address from its `r0` index
   (table base `*[0x03023288]`, terms scaled by SAVEINFO bytes `+0x10`/
   `+0x1F` read @`0x030630CE–0x030630D6`, entry stride 258 = 0x80 halfwords
   + 2) and tail-branches @`0x03063102` via `0x0306432A` → `0x03053F5E` to
   the copy engine `0x03067510` with `r2 = count<<1` (bytes). The same
   helper fills local buffers that are then drawn as strings (in
   `0x03063106` @`0x0306311C` with count `0x40`, in `0x03063242`
   @`0x03063258` with count `0x64`). That fixes the direction. `r1` is the
   destination. **Named gap:** the identity of the `*[0x03023288]` source
   table (which record index 4 selects) was not pinned; this affects only
   the completeness of the writer list, not the encoding verdict.
   The same helper is called with `r0=0x45` / `r0=0x47` and `r1 = node+0x70`
   @`0x0307ED86` / @`0x0307EDA4` (module 31), i.e. it also fills the
   browser-node name field.

### Who reads it

- Module 24 @`0x0307ECE4`: `ldr r0,[pc,#0x100]` → literal @`0x0307EDE8` =
  `0x030235CE`; with `r1,r2 = ldrd [fp,#0x10]`, `r3 = [fp,#0x18]`; `bl
  0x0307DCE4`. **Named gap:** the callee at `0x0307DCE4` lives in the
  co-loaded window segment and its body is not present in module 24's or
  module 31's extracted code bin, so this consumer's per-halfword handling
  could not be read directly.
- The two `0x030630C2` sites above are writes (destination), per the
  direction argument.

### Why UTF-16 (consumer semantics, module 0 text routine `0x03062CEE`)

`0x03062CEE` is the firmware's string measure/draw routine (called by
module 31 Display with the string at node `+0x70`, @`0x0307EB36` and
@`0x0307EC7A`). It consumes its string one halfword per character:

- `ldrh r0,[r5]` @`0x03062D52` (r5 = string), terminator test `cmp r0,#0`
  @`0x03062D58`;
- per-unit width via `bl 0x030627BE` @`0x03062D6A` and @`0x03062DAA`;
- advance `ldrh r0,[r4,#2]!` @`0x03062D90`, `ldrh r0,[r7],#2`
  @`0x03062DA6`;
- line-break test compares the **whole halfword** against `0x0A` and `0x0D`
  @`0x03062D78–0x03062D80`;
- per-unit draw via `bl 0x03062582` @`0x03062DF4`, pointer advanced by 2
  @`0x03062DF8`.

A byte-pair packing would make the `0x0A`/`0x0D` whole-halfword comparisons
and the +2 advance meaningless. The sibling renderer `0x0306333E` likewise
steps `ldrh r0,[r5],#2` @`0x03063390`. Browser node names are compared
halfword-by-halfword against this same format (module 31 name matcher:
`ldrh` from `[sb + 2i]` vs `ldrh` from `[r5+0x70 + 2i]`, in the function at
`0x0307DEB8`'s caller region @`0x0307E2C–…`; node name field at `+0x70` is
filled by the same `0x030630C2` helper, @`0x0307ED86`).

---

## Item 4: "getters" `0x0306316E` / `0x0306314A`

**Verdict: unit = N/A for both. Neither function returns a playback
position in any unit. They are a get-and-set pair for two small-integer
display-mode fields of struct `0x0302385C`. The premise that they are
elapsed/total position getters is refuted.**

### `0x0306316E` (module 0, `0x0306316E–0x03063184`, full body)

- `cmp r0,#2; it eq; moveq r0,#0`; `cmp r0,#0; it eq; moveq r0,#2`, an input
  remap 2→0, 0→2, other values unchanged.
- `ldr r2,[pc,#0x114]` → literal @`0x03063294` = `0x0302385C`;
  `ldrh r1,[r2,#0x20]`; `strh r0,[r2,#0x20]`; `mov r0,r1; bx lr`.
- Returns the previous value of halfword field `+0x20` of struct
  `0x0302385C`, after storing the (remapped) argument there. No other
  memory access, no arithmetic.

### `0x0306314A` (module 0, `0x0306314A–0x0306316C`, full body)

- `ldr r2,[pc,#0x148]` → literal @`0x03063294` = same struct
  `0x0302385C`; `ldrh r0,[r2,#0x24]`; if the stored `+0x24` halfword
  equals the argument, return it immediately (`bxeq lr` @`0x03063154`);
  else `strh r1,[r2,#0x24]` and copy a word into struct offset 0 from a
  dereferenced pointer, with source pointer at literal `0x030632A8` =
  `0x03023270` (arg ≠ 2, @`0x0306315E–0x03063164`) or `0x030632AC` =
  `0x03023274` (arg == 2, @`0x03063166–0x0306316C`), via cell `0x03023280`
  (literal @`0x030632A4`).
- Returns the previous value of halfword field `+0x24`. A get-and-set
  with a mode-dependent pointer swap at struct offset 0.

### Negative arithmetic evidence

Neither function references the file-info struct `0x03023980` (both use
only struct `0x0302385C`), reads any codec/DMA counter, or contains any
division, modulo, or the constants 1000, 75, 44100, or any sample rate.
(Raw dword census of `0x03023980`: 31 literal hits across the bins, none in
these two functions.) Call-site census: `0x0306316E` 78 raw / 46
linear-sweep sites; `0x0306314A` 68 raw / 32 linear-sweep sites.

### Caller usage: save/set/restore, never mm:ss

- **Module 5 progress painter** @`0x0307D38C`: `movs r0,#1; bl 0x0306316E`
  @`0x0307D39A` → result kept in `sb`; `movs r0,#2; bl 0x0306314A`
  @`0x0307D3A2` → result in `r8`; … draws …; at exit `mov r0,sb; bl
  0x0306316E` @`0x0307D3E2` and `mov r0,r8; b.w 0x0306314A` @`0x0307D3F0`.
  The returned values are stored verbatim and restored, never divided
  by 60 or compared against a total. Same pair pattern in module 5
  @`0x0307D1C4`/`0x0307D1D2` (results reloaded from `[sp+8]`/`[sp+0xC]` and
  fed back).
- **Module 31 Display body** @`0x0307E8F2`: `movs r0,#1; bl 0x0306316E`
  @`0x0307E91A` → stored `[sp,#0x18]`; `movs r0,#2; bl 0x0306314A`
  @`0x0307E922` → stored `[sp,#0x1C]`; restored from those slots at the end
  @`0x0307ECCE–0x0307ECE0`. Second copy @`0x0307ECEA`: set
  @`0x0307ECF6`/`0x0307ECFE`, restore @`0x0307ED2E`/`0x0307ED3C`. Also used
  to bracket the text helper `0x03062CEE` @`0x0307EB24–0x0307EB3C` (set
  mode 1, draw, restore), which is mode bracketing around text rendering.
- **Module 0 shutdown painter** @`0x03067C4C`: `movs r0,#1; bl 0x0306316E`
  @`0x03067C4C` and `movs r0,#2; bl 0x0306314A` @`0x03067C52`, and both
  return values are discarded (r0 overwritten @`0x03067C56`) before
  drawing via `0x03063242` @`0x03067C7A`. Pure mode-set.
- **Module 0 painter** @`0x03055AC4`: `movs r0,#2; bl 0x0306314A`
  @`0x03055AD2` → previous value in `r7`; restored `mov r0,r7; b.w
  0x0306314A` @`0x03055B3E–0x03055B44`. It does not call `0x0306316E`.
- **Module 31 Service** @`0x0307DB6C`: `mov r0, sl; bl 0x0306316E`, result
  discarded, a restore of a saved mode value.

### Patch implication

Playback position must come from another source; this pair cannot supply
it. **Named missing fact:** the true elapsed/total source was not traced
in this pass. Unexamined candidates: file-info struct `0x03023980` fields
(`+0x44/+0x48/+0x4C`) as used by module 33 in the region @`0x030886B8+`.

---

## Verdict summary

1. **Cadence: EVENT-ONLY.** No periodic poster of `0x2E` (or `0x27`) during
   steady playback. Posters are the painter template's arg==1 self-repost,
   the `0x03063A32(1)` invalidate helper on draw/window transitions,
   state-change handlers, and the change-only detector `0x030656EE` (never
   posts `0x2E`). The dispatcher's countdown path posts only `0x95`/`0x24`,
   which the painter does not consume.
2. **Text-draw stack arg: VALUE (16-bit pixel/color), not POINTER, not ID.**
   `0x030632FA` is a rectangle fill; its stack argument is passed by value
   into framebuffer store `0x03063E60` @`0x03063EA0`. Traced provenance:
   contents of halfword cell `0x030235B4`, module 5 @`0x0307D1E0–0x0307D1F0`.
3. **Encoding: UTF-16-style wide string** (one code unit per halfword,
   NUL-halfword terminated). Writers: snapshot loops module 31
   @`0x0307DC3C` and module 22 @`0x0307D4BA`, source SAVEINFO `+0x87`;
   consumer semantics from text routine `0x03062CEE` @`0x03062D52–
   0x03062DF8`. Two named gaps (the `*[0x03023288]` table identity; module
   24's callee `0x0307DCE4`) do not affect the encoding verdict.
4. **Getter units: N/A for both.** `0x0306316E` and `0x0306314A` are a
   get-and-set display-mode pair on struct `0x0302385C` fields `+0x20` /
   `+0x24`, returning previous small-integer mode values (0/1/2 class). No
   file-info access, no division, no time unit.
