# SAVEINFO save path + lock display, Fosi DAP Neo V137

Workstream deliverable. Offline static analysis of `DP3_V137.img` (SHA-256
`fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`), extracted modules in
the extracted module set. Labels: **[P]** proven from disassembly read in this
workstream, **[I]** inference from that evidence. Helper scripts in this folder:
`mdis.py` (per-module disassembler), `scan2.py` (BL/literal scan), `xref.py`
(register-tracked literal xref), `flagscan.py` (flag-API call sites by immediate id),
`drawscan.py` (DrawImage call sites by immediate id, see caveat in §2.4).

---

## 1. SAVEINFO save path, FOUND [P]

### 1.1 Storage plumbing under the record

- SAVEINFO live struct: 0x300 bytes at `0x030232A0`. Stored image: 0x800 bytes.
- Raw-area helpers in module 0: **read `0x0306C960(a, b, dst, len)`**,
  **write `0x0306C9B4(a, b, src, len)`**. Both query geometry through
  `0x0306795A(0x30001, &info)`; the device-3 info method at `0x0305E008` fills
  `[info+4]=0x400`, `[info+6]=0x10`, `[info+0]` = subdevice offset (from `0x0305DF72`).
  Logical sector = `a*0x400 + b*0x10` (device-3 subdevice-1 sectors). [P]
- Read count = ceil(len/512) sectors. Write count = ceil(len/0x2000)*0x10 sectors,
  the write helper's unit is 0x2000, an observed quirk; net effect for the 0x800-byte
  SAVEINFO image is one 0x2000-unit write at the target sector. Semantics not fully
  resolved beyond that. [P for the arithmetic, I for the interpretation]
- Device read/write wrappers: `0x030678CA` (read) / `0x03067912` (write), record
  methods +0x04/+0x08 via dispatcher `0x030678B0`, table base `0x0306E958`. The
  block-read `0x03067510` used by the boot path is a cached reader over selector
  `0x00030001`; the save path does **not** use it. It uses the raw helpers above. [P]
- **Checksum `0x0306CAA6(ptr, len)`: `len` is in BITS.** Save and load both pass
  `0x17E0` → covers `0x2FC` bytes = struct bytes `[0, +0x2FC)`, i.e. everything except
  the checksum word itself at +0x2FC. Table-driven byte checksum, table at
  `0x030058A9`, initial value `0xF`. [P]

### 1.2 The saver: module 0 function `0x0306CA10(arg)` [P]

1. Zero-fills an 0x800-byte stack buffer with `0xFF` (memset `0x03054E58`).
2. Commit marker: `arg != 0` → `[struct+0x2F4] = 0x55AA`; `arg == 0` →
   `[struct+0x2F4] = 0`. (+0x2F4 is inside the checksummed range.)
3. Recomputes checksum over the live struct (`0x0306CAA6(0x030232A0, 0x17E0)`)
   → stores at `[struct+0x2FC]`.
4. `memcpy(buf, struct, 0x300)` (`0x03054E34`), the stored image's first 0x300 bytes
   are the live struct verbatim; bytes 0x300–0x7FF of the image remain `0xFF`.
5. Area-select `0x03067870(2, 7)`.
6. **Primary write: `0x0306C9B4(0, 1, buf, 0x800)` → sector 0x10.**
7. **Mirror write of the same image: `(0, 4)` → sector 0x40 if mode byte
   `[struct+0xE] == 2`, else `(0, 12)` → sector 0xC0.**

Companion load helper `0x0306CA8C` reads only `(0, 1)` via `0x0306C960`. [P]

There is **no 'FWUP' header construction on the SAVEINFO write path**. The image
written is the raw struct block starting with the 'SAVE' magic at +0. The 'FWUP'
check in the boot path belongs to the separate firmware-descriptor read through
`0x03067510` on handle `0x30000`. [P]

### 1.3 Second writer: module 1 boot load+normalize+write-back [P]

Module 1's boot function (ends `0x0307E25C`) reads the image via
`0x0306C960(0, 1, buf, 0x800)` @ `0x0307DBF6`, verifies checksum + SAVE/INFO magics,
then copies buffer → live struct **field by field with per-field clamps**
(~`0x0307DD06`–`0x0307E228`). It then:

- clears `[struct+0x2F4] = 0` @ `0x0307E22C`,
- recomputes the checksum over the live struct @ `0x0307E236`,
- `memcpy(struct → buf, 0x300)` @ `0x0307E246`,
- writes back **only the primary** `(0, 1)` via `0x0306C9B4` @ `0x0307E254`,
  after area-select `0x03067870(2, 7)` @ `0x0307E228`.

Interlock @ `0x0307E1D0`–`0x0307E1E0`: the stored +0x2F4 is copied into the struct;
if it is not `0x55AA`, `[struct+0x3E]` is forced to 1. [P]

### 1.4 Save triggers, every caller of `0x0306CA10` [P]

| Caller | Arg | Context |
|---|---|---|
| Module 32 (settings menu) ×5: `0x0307D8E8`, `0x0307D8FE`, `0x0307D988`, `0x0307D9F0`, `0x0307FD36` | 1 | Settings apply paths. `0x0307D988`/`0x0307D9F0` run right after `strh r6, [struct+0x3E]` in printf-accompanied apply paths; `0x0307FD36` is a field-setter dispatch (writes struct +0x1B/+0x1C by index, audio apply `0x030570E8`, saves if it returns 0); `0x0307D8E8` follows GPIO(2,16) config + stubs `0x0307FD60/62/64`. |
| Module 0 power-off handler @ `0x03065682` | 1 | Entered on flag 0x1A test+clear @ `0x03065606` / flag 0x1A0 test @ `0x03065610`. Preceded by struct +0xF→+0x29 copy and +0x17 clear; followed by shutdown fn `0x03067C1C`. |
| Module 0 init @ `0x030536D0` | 1 | Conditional on the enclosing function's entry-arg bit 0. |
| Module 5 @ `0x0307D2AE` | 0 | Mode applet, inside the mode-load function `0x0307D208` (see §1.5). |
| Module 21 @ `0x0307D43C` | 0 | Pre-reset save: immediately before writing reset register `0x40120004` and spinning. |
| Module 23 @ `0x0307D32C` | 1 | After a DB write via `0x03067912` + invalidating the 3-entry cache at `0x03005878` + decrementing struct halfword +0x36. [I: scan-completion save] |
| Module 61 @ `0x03081974` | 1 | Same DB-write/cache-invalidate pattern as module 23. |

Related, not the saver: module 21 calls the load helper `0x0306CA8C` @ `0x0307D372`
after rewriting mode fields +0x29/+0x3E/+0xF/+0xE when +0x29 ≠ 2. Module 5's
mode-load function reads a mirror image directly, `0x0306C960(0, 0xC, …, 0x1000)` @
`0x0307D252` or `(0, 4, …)` @ `0x0307D2E6`, branch-selected by the mode byte, i.e.
the mode applet loads the *target mode's* settings image on a mode switch. [P,
interpretation I]

### 1.5 Event flag 0x189 is NOT the save trigger [P]

Flag 0x189 is posted only by module 1: @ `0x0307DC2C` (checksum/magic failure, after
0xFF-filling the buffer) and @ `0x0307DC62`–`0x0307DC66` (header halfword-pair
mismatch with 0). It is test+cleared only by module 1 @ `0x0307D5E0`, inside a
mode/init routine (sets +0xE=2, clears +0x60 @ `0x0307D612`, writes +0x3E=1,
posts/tests flag 0x18C) that does **not** call the saver. Conclusion: 0x189 is a
module-1-internal "settings were reset" notification; persistence happens only
through the direct `0x0306CA10` callers in §1.4. (Tooling caveat: `flagscan.py`
only detects an immediate id loaded within ~40 bytes before the flag-API call.)

### 1.6 SURVIVAL VERDICT, a patched-in field in an unchecked gap does NOT survive [P]

- **Save side is lossless:** both writers (§1.2, §1.3) memcpy the whole 0x300-byte
  live struct into the image, and the checksum covers the gaps, so gap bytes reach
  storage intact.
- **Load side is selective:** module 1's boot pass copies back **only individually
  listed fields**. Its only bulk operations are @ `0x0307DC24` (memset),
  @ `0x0307E15C` (the block copy below), @ `0x0307E246` (write-back). There is **no
  bulk buffer→struct copy**. A gap byte is therefore never restored into RAM at
  boot, and the first subsequent save overwrites storage with whatever the
  (default/zero) RAM value is. The field is lost on the first save/load cycle.

**Exceptions that DO round-trip verbatim** [P]:

- `+0x11` (single byte copy in the load pass).
- **Block `+0x1C7 .. +0x2D5`**: `memcpy(buffer+0x1C7 → struct+0x1C7, 0x10E)` @
  `0x0307E15C`. (An alternate branch of the same code uses the strncpy-like
  `0x03054E66` over this region, because the block is the record's string and large-field
  area, so a patch must check which branch a given boot takes.)
- `+0x2E9` and `+0x2ED` as words, with only a `0xFFFFFFFF`-sentinel check,
  mirrored to module-0 globals `0x030041EC` / `0x030041E0` @
  `0x0307E204`–`0x0307E212`. (Module 5 also writes those globals into
  +0x2E9/+0x2ED @ `0x0307D4C4`–`0x0307D4F0`.)

**Patch guidance** [I]: to add a persistent custom field, either (a) place it
inside the +0x1C7..+0x2D5 verbatim block if a free sub-range can be confirmed, or
(b) patch module 1's load pass (one site, ~`0x0307E15C` neighbourhood) to also
restore the chosen gap offset, and every boot goes through that pass. Patching only
the savers is useless; the loss happens at load.

---

## 2. Lock / hold display

### 2.1 There is no dedicated lock window [P]

WIN structs (entries are Thumb addresses; entry = stored−1; layout +0x08 Service,
+0x0C Key, +0x10 Display, +0x14 Init, +0x18 DeInit) were decoded for modules
5, 6, 10, 17, 21, 25, 26, 27, 29, 30, 31, 32. None is a lock applet:

- Module 5 (mode applet): Service `0x0307D3F6`, Key `0x0307D5F6` (stub, returns 0),
  **Display `0x0307D5FA` = `bx lr` stub**, Init `0x0307D38C`, DeInit `0x0307D3F4`.
- Module 31 (player): WIN at its data+0x38, Service `0x0307DA8A`, Key
  `0x0307E5B8`, Display `0x0307ED40`, Init `0x0307D6A0`, DeInit `0x0307D776`.
  Its Display's first 0x300 bytes contain no DrawImage call and no +0x60 read
  (dump: `mod31_display.txt`); it delegates to helper painters
  `0x0307D456`/`0x0307D410` (not fully traced).
- Module 21 Display `0x0307E524`, module 27 Display `0x0308002C`, identified,
  not yet read for lock content.

The only reader of SAVEINFO +0x60 outside the player/mode applets is module 33
(codec service) @ `0x030886C2`. The locked UI is therefore the stock design from
the prior workstream: per-screen badges drawn by a shared status painter (§2.2),
plus the 'Rotate to Unlock' string (language id 121).

### 2.2 The status painter, where the badges are drawn [P]

A framework status-icon painter is linked into module 0 and into each overlay
(same source, per-module addresses). Copies located: **module 0 @ ~`0x03055A5A`**
(first DrawImage @ `0x03055A62`), module 5 @ `0x0307D2EE`, module 23 @
~`0x0307E52x`, module 27 @ ~`0x0307E7Cx`, **module 31 @ `0x0307E804`**.

Behaviour (module 31 copy, read in full):

- Called with arg == 1 → posts flags `0x27, 0x28, 0x2C, 0x2D` (invalidate all).
- Otherwise, per set flag (test+clear `0x03067258`), it calls
  DrawImage `0x03063700` with a computed id:
  flag 0x27 → `byte[0x0302312C] + 0x107`; flag 0x28 → `byte[0x0302312D] + 0x105`;
  flag 0x2C → `byte[0x0302312E] + 0x8F`; flag 0x2D → `byte[0x0302312F] + 0x109`.
  The four bytes at `0x0302312C`–`0x0302312F` are framework icon-state bytes
  (read by every painter copy; their writers use base-register addressing and
  were not isolated).
- Final segment (flag 0x2E): loads the framework state byte at `0x030230EC` and
  tail-calls the hold-icon painter (§2.3).

The module-0 copy also draws image ids `0xCC`/`0xCD` selected by a
halfword pair. The same painter serves the non-overlay screens.

### 2.3 The list-screen hold icon [P]

Tail painter, module 5 copy @ `0x0307D382`, module 31 copy @ `0x0307E898`:

```
r0 = (byte[0x030230EC] >> 2) & 1
DrawImage(0x26 + r0)          ; 38 or 39
```

Image records 38 and 39 were verified against the resource table: both
15×17 at (135,4), exactly `A_LIST_NOHOLD_(135,4)` / `A_LIST_HOLD_(135,4)`.
So **DrawImage ids equal resource-manifest ordinals in this range**, and
**bit 2 of the framework state byte at `0x030230EC` is the hold indicator** for
list screens. Who writes that byte/bit was not isolated (only readers found:
the painter copies in modules 5, 23, 27, 31 and module 18 @ `0x030839B2`).

### 2.4 Image-id correlation caveat [P]

The resource manifest holds 469 named entries vs 456 image records (two themes,
`A_`/`B_`); the two lists drift against each other. Ordinal == id is verified at
38/39 (and consistent at 2–5: 240×320 full-screen records matching
`A_LOCKOFF1..4_(0,0)`, and at 143). But manifest entries 43/44
(`A_BROWSER_SMALLLOCK(_BACK)`) and 183/184 (`A_MUSIC_SMALLLOCK(_BACK)`) land on
1×1 placeholder records, so **the SMALLLOCK badge ids cannot be read off the
manifest ordinal**; the painter's computed ids (state byte + base, §2.2) are the
reliable route, and the badge for a given screen is whichever base+state pair
its painter uses. (`drawscan.py` also produces false positives here: it reports
the flag constant 0x2C = 44 as an "image id" at painter sites.)

### 2.5 Hold engage path [P, with one gap]

1. Something posts **event flag 0x14E**. Poster not isolated: no applet loads
   the immediate 0x14E before a flag-API call; the input task in module 0 is the
   remaining candidate [I].
2. Module 31 Service, flag-0x14E branch @ `0x0307DC0E`–`0x0307DC7C` (test+clear
   @ `0x0307DC12`): if `[struct+0x60] == 1` (@ `0x0307DC24`; note the branch
   reads +0x60 twice, @ `0x0307DC1A` for a debug print via `0x0306D8F0`), it
   snapshots the current track. All offsets are on the same base register as
   +0x60, i.e. the shared state struct at `0x030232A0`:
   - index halfword `[+0x85]` → `0x030235C0` and → `[0x03023980+0xF2]`;
   - name: 0x80 halfwords from `+0x87` → buffer at `0x030235CE` (copy loop
     @ `0x0307DC3C`–`0x0307DC4C`);
   - word `[+0x193]` → pointer cell `0x0307BF58`; halfword `[+0x5A]` →
     `[0x03023980+6]`.
3. It then sends **message type 3** via SendMessage `0x03067452` @
   `0x0307DC76`, payload `{halfword = [+0x5A], halfword = 4}`.
   The receiver of message type 3 was **not** isolated. Module 0's message
   dispatch remains to be traced for it. [open]

Correction to the prior doc: the snapshot globals are **not** hold-specific.
`0x030235C0` is a general category selector (read/written by modules 5, 21, 22,
23, 24, 25, 27, 29, 31) and `0x030235CE` is also written by module 22 @
`0x0307D4B0` and read by module 24 @ `0x0307ECE4` and module 31 @ `0x0307E06A`
(via copy fn `0x030630C2`, count 0x80). "Find the snapshot reader" is therefore
not a viable route to the lock display on its own.

### 2.6 Who writes SAVEINFO +0x60, engage writer is NOT in the applets [P]

Register-tracked xref over all 82 modules found these byte writers of
`[0x030232A0+0x60]`, and **every resolved value is 0 (clear)**:

| Site | Value | Context |
|---|---|---|
| Module 5 Service @ `0x0307D40C` | 0 (r5, set @ `0x0307D404`) | Mode-context reset; also clears halfword +0x3E, then calls the mode-load fn `0x0307D208` and posts flag 0x186. (Module 5's only other +0x60 access is the read @ `0x0307D518` for the message-0x0B substitution, the prior doc's "module 5 writes it" refers to this clear.) |
| Module 31 @ `0x0307D7F6` | 0 (r4) | Stop/exit path, after `0x0305791A([struct+0xE])`. |
| Module 31 @ `0x0307E0A2` | 0 (sb, set @ `0x0307DF12`) | Track/list change path: sets `[0x03023980+0xF2] = 6` @ `0x0307E08A`, updates current-track pointer `0x0307BF58`, clears flags 0x17D/0x17B. |
| Module 26 Key @ `0x0307EA78` | 0 (r6, set @ `0x0307E9F0`) | `strbeq`, executes only when play-context halfword `[0x03023980+0xF2] == 7`. |
| Module 12 @ `0x0307F0B8` | r0, unresolved | Written alongside +0x3E/+0xE in the USB MSC applet's state-reset cluster; almost certainly also a clear [I]. |

**No applet sets +0x60 to 1.** The engage write must live in resident module 0,
the input/key region `0x03061936`–`0x03061E58`, which owns the wheel counters
(`0x03023178`, `0x03023179`, total `0x0302317C`), the key-state merge
`0x03061686`, and the big event dispatcher (function ~`0x03061B40`+, which among
other things special-cases event word `0x40004000`). That region was partially
read (`mod0_input.txt`) but the +0x60 gate / engage write inside it was not
isolated. Method limitation: the xref tracks bases loaded from literals within
a window; a writer holding the struct base in a long-lived register across a
large function could be missed. [P for the applet exhaustiveness within that
method; I for the module-0 conclusion]

### 2.7 Unlock check, not isolated [open]

'Rotate to Unlock' implies wheel input is compared while +0x60 == 1. The wheel
decoder post-processing @ `0x03061A00`–`0x03061AAE` increments the counters and
writes sentinel 5s into a phase buffer; no +0x60 test appears in the input-task
range read. The threshold/compare site (counter delta vs a constant, gated on
+0x60) remains to be found, most likely inside the module-0 dispatcher
(~`0x03061B40`–`0x03061E58`) or in the applet Key handlers' locked branch
(module 31 Key @ `0x0307E5B8` not yet read).

### 2.8 Patch points for a richer lock screen [I, addresses P]

- **Hook:** the status painter's flag-0x2E segment (§2.2) or module 31's
  Display `0x0307ED40`. Both run while the badge is shown.
- **Data already snapshotted at engage:** track name at `0x030235CE`, index at
  `0x030235C0` / `[0x03023980+0xF2]` (§2.5).
- **Primitives available:** DrawImage `0x03063700`; text draw `0x030632FA`
  (used by module 5's progress painter @ `0x0307D1F0`/`0x0307D3D2` with a
  halfword string pointer + geometry args); playback position getters
  `0x0306316E(1)` / `0x0306314A(2)` (used by the module-0 shutdown painter @
  `0x03067C4C`/`0x03067C52` and module 5's painters).

---

## 3. Lock-disable switch (module 32 menu item for string 184), NOT pinned

What was established [P]:

- Module 32's Key handler (`0x0307DDA6`) works on the runtime menu struct at
  `0x03024834`, **which is module 32's BSS** (data file is only the 112-byte
  WIN struct at `0x030247C4`; bss_exec `0x03024834`, len 681). Item records are
  12 bytes at struct+0x10, current index at struct+0xC; the handler computes
  `record = struct + 0x10 + index*12` @ `0x0307DDB0`–`0x0307DDBA`. Record
  layout: value byte at **record+5**, descriptor pointer at **record+8**.
  Descriptor: string id = halfword `[desc+0]`, option count = halfword
  `[desc+0xE]`. The table is built at runtime by Init (`0x0307D164`, helper
  `0x0307D1B8` builds record 0 and a descriptor area from a byte table at
  `0x030237D7`), so no static record for id 184 exists in the image to read.
- Only two items are special-cased in the Key handler's apply dispatch
  (@ `0x0307DEE4`–`0x0307DEF0`), and neither is 184:
  - **id 173 (0xAD, EQ)** → branch `0x0307DF6C`: value ↔ **SAVEINFO +0x68**
    (compare @ `0x0307DF6C`, write @ `0x0307DF7E`; posts flag 0xFB if changed).
  - **id 196 (0xC4, brightness)** → branch `0x0307DF84`: writes value →
    **SAVEINFO +0x14** @ `0x0307DF86`, then backlight apply `0x03064964`.
  - All other ids → `0x0307DF8C`: post flag 0xC6 (the generic settings-changed
    flag; module 32's Service posts/tests 0xC6 and 0xC3 and does the saves in
    §1.4) and exit. The generic value↔SAVEINFO-offset binding lives in the
    runtime-built descriptor fields (+0x2/+0x4 area), which were not decoded.
- Saver-adjacent field setter in module 32 @ `0x0307FD36` writes SAVEINFO
  +0x1B/+0x1C by index. A different dispatch, not the 184 item.

Candidates +0x13/+0x1A/+0x1C/+0x2E7 remain untested; +0x2E4 is excluded (gain
byte, per the integration addendum). Next step for whoever picks this up:
decode descriptor fields +0x2/+0x4 in module 32's Service apply loop, or
Unicorn-run module 32 Init + one generic apply cycle and watch which struct
offset takes the value.

---

## 4. Open items (explicitly not done)

1. Poster of flag 0x14E; receiver of message type 3 (§2.5).
2. The +0x60 = 1 engage write and the wheel-unlock threshold check, both
   believed to be in module 0's input/dispatch region (§2.6, §2.7).
   Module 31 Key @ `0x0307E5B8` and module 31 Display's helper painters
   `0x0307D456`/`0x0307D410` also unread.
3. Writers of the icon-state bytes `0x0302312C`–`0x0302312F` and of bit 2 of
   `0x030230EC` (§2.2, §2.3).
4. SMALLLOCK badge image ids for the music/browser screens (§2.4).
5. Lock-disable SAVEINFO offset (§3).
6. Write helper `0x0306C9B4`'s 0x2000-unit count quirk (§1.1). Arithmetic
   proven, device-level semantics inferred.
7. Module 12's r0 value at its +0x60 write @ `0x0307F0B8` (§2.6).
