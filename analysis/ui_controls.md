# Fosi DAP Neo (DP3_V137): input dispatch, lock screen, settings storage, Bluetooth

Analyst workstream: UI / controls / lock screen / settings.
Evidence base: `DP3_V137.img` (SHA-256 `fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`),
extracted modules in `~/workspace/fosi-dap-neo/extracted/`, disassembly via Capstone (Thumb-2)
with the module-pinned disassembler in this folder (`mdisasm.py`).
Framework naming cross-checked against the leaked RKNanoD SDK
(`EACHAN-YIN/RKNanoD_MP3_V1.3_20161102`, headers only). Every SDK constant below was
verified against stock code before use; where stock and SDK disagree, stock wins and the
disagreement is noted.

Conventions: **[P]** = proven from stock machine code. **[I]** = inference, with basis stated.
Addresses are execution addresses. Module 0 = resident image at 0x03050000. GUI applets are
overlays loaded at code 0x0307d164 / data window 0x030247c4 (a second overlay family sits at
0x0307e9c0, codecs at 0x0308837c+).

---

## 1. Input path: how keys and the wheel are produced

### 1.1 Hardware producers (module 0, all [P])

Input is polled, not interrupt-driven, except for the ADC conversion-complete ISR.

| Source | Hardware | Stock evidence |
|---|---|---|
| Power button | GPIO port 2, pin 5 | `GetKeyMask` 0x030617A0 reads GPIO(2,5) first via GPIO read helper 0x030560F2 |
| OK / center button | GPIO port 2, pin 14 | `GetKeyMask` reads GPIO(2,14) second |
| Vol+ / Vol− | SARADC channel 1 resistor ladder | SARADC base 0x400D0000, control reg +0x08 (channel mask [2:0], power 0x08, start 0x10, IRQ 0x40) |
| Scroll wheel | GPIO port 2, pins 12 (A) and 13 (B), quadrature | decoder at 0x03061936 reads both pins via 0x030560F2 |
| (also configured as inputs at key init) | GPIO(2,5), GPIO(2,14), GPIO(0,13), GPIO(2,13), GPIO(2,12) | key-init routine in the shared overlay runtime (module 1 copy at 0x0307D1CC) |

GPIO(0,13) is configured as an input by key init but is not read by `GetKeyMask`;
GPIO(0,11) is read by the mode applet (module 5, at 0x0307D442) in a state-transition
path. [I] One of these is a jack/USB-detect line; neither is a user key in stock code.
**Update (2026-11-08):** GPIO(0,13) is the headphone-jack sense line; see §1.7.

SARADC driver (module 0, [P]): state struct at 0x030040E4; channel scan order table at
0x03005684 = {1, 1, 2, 0} (written by init 0x0305FDBC); per-channel results (uint16) at
0x030059AC; request ring 0x030059BC–0x030059DC. Functions: init 0x0305FDBC, start/stop
0x0305FD98/0x0305FD2C, periodic scan tick 0x0305FE0E, ADC ISR 0x0305FE92 (stores result to
0x030059AC + ch×2, sets done bit), `ReadADC(channel)` 0x0305FF28, test-and-clear-done
0x0305FF12. Device-name strings in module 0: 'ADCDevice' 0x0306E929, 'KeyDevice' 0x0306E93E.

A periodic input task at 0x03061AB2 calls the key state machine (0x030617FE), the ADC scan
tick 0x0305FE0E(1), and a merge routine 0x03061686. Key init registers this task as a
periodic callback (timer id 0x23) via 0x030664E8/0x03056D8E/0x03056C88. The tick period is
not established from the binary; all durations below are in ticks.

### 1.2 Key mask construction: `GetKeyMask` 0x030617A0 [P]

Returns a bitmask (or −1 if the ADC sample is not ready):

| Condition | Mask | Physical key [P source; name = I] |
|---|---|---|
| GPIO(2,5) active | `0x0001` | Power button |
| GPIO(2,14) active | `0x4000` | OK / center button |
| ADC ch1 value < 50 | `0x0010` | ladder key A (Vol+ on the Neo) |
| ADC ch1 value 100–199 | `0x0020` | ladder key B (Vol− on the Neo) |
| ADC ch1 value 50–99 or ≥ 200 | `0x0000` | dead zone / no key |

Only one source is reported per scan: GPIO(2,5) wins over GPIO(2,14), which wins over the
ladder. The ladder bands are taken from the stock compare constants (50, 100, 200).
NeoPod's published bands for the sibling platform (Vol− = 80–180) do not match stock;
the stock 100–200 band governs. The SDK's 7-key ladder table (SysConfig.h ADKEY2..7) also
does not apply. The Neo ladder has exactly two decoded bands.

Framework naming (SDK SysConfig.h, verified where bits coincide): mask bit 0x0001 =
`KEY_VAL_PLAY`/`KEY_VAL_POWER`, 0x0010 = `KEY_VAL_UP`, 0x0020 = `KEY_VAL_DOWN`,
0x0040 = `KEY_VAL_ESC`, 0x0100 = `KEY_VAL_UNHOLD`, `KEY_VAL_HOLD` = PLAY|MENU combo.
The Neo's 0x4000 bit (GPIO2.14) has no counterpart in the SDK's 7-key map; [I] it is the
OK/center key (NeoPod lead + it is the only other GPIO button).

### 1.3 Event word: key state machine at 0x030617FE / 0x03061800 [P]

State struct at 0x0302309C: +0x38 current mask, +0x3C previous mask, +0x44 state word,
+0x48 hold counter (ticks), +0x34 event word. A pending flag byte lives at 0x030230EC
(bit 0 = scan inhibit, bits set on event production; applets poll this byte, with references
found in overlays 1, 5, 18, 22, 23, 27, 31, 32).

Event word format: `event = (type << 28) | mask`, matching the SDK's
`KEY_VAL_UNMASK = 0xF0000000` / `KEY_VAL_MASK = 0x0FFFFFFF`. Types decoded from the
state-machine branches:

| Type (high nibble) | Meaning [P] | Condition |
|---|---|---|
| 0x1 | Press (debounced) | same nonzero mask stable for 2 ticks |
| 0x2 | Long-press trigger | hold counter reaches 20 ticks |
| 0x3 | Key repeat | every 4 ticks while held past 20 ticks |
| 0x4 | Release after short press | mask → 0 with hold counter ≥ 2 and < 20 |
| 0x5 | Release after long press | mask → 0 with hold counter ≥ 20 |

Special case [P]: while mask 0x0001 (power) is held past 100 ticks, the state machine
posts system event flag 0x1A via the flag-post function 0x0306723C, [I] the power-off
request; the shutdown path in module 0 is anchored at 0x03067C1C ("system powerdown!").

### 1.4 Wheel decoder: 0x03061936 [P]

Quadrature decoder over GPIO(2,12)/(2,13). It keeps a 3-deep phase-sequence buffer at
0x03023110 (phase values 0–3, sentinel 5 = consumed/idle), previous pin levels at
0x03023170/0x03023175, a sample counter at 0x03023174, and only accepts a step when a
consistent 3-sample phase sequence completes. Debounce is by sequence validation,
not by time. Outputs are counters, not events: direction-A count (byte) 0x03023178,
direction-B count (byte) 0x03023179, total steps (word) 0x0302317C. [I] Applets poll
these counters (and derived delta bytes in the same state page, e.g. 0x0302312C–0x0302312F
are read by the paint code of modules 5 and 31 to offset image indices). No wheel
*message* is posted by the producer. Which counter is clockwise was not established.

### 1.5 Dispatch to applets [P structure, I slot names]

Applets are framework "windows" (SDK `WIN` struct, verified on module 32 whose data at
0x030247C4 reads {link, link, 0x0307D807, 0x0307DDA7, 0x0307D7B9, 0x0307D165, 0x0307D1AB}):

| WIN offset | Stock module-32 value | Role (SDK field order) |
|---|---|---|
| +0x08 | 0x0307D807 | Service (system event/message consumer) |
| +0x0C | 0x0307DDA7 | Key (receives the event word in r0) |
| +0x10 | 0x0307D7B9 | Display (paint) |
| +0x14 | 0x0307D165 | Init, the common entry stub shared by overlays (initialises ADC state 0x030040E4, posts flags 0x0A/0x93) |
| +0x18 | 0x0307D1AB | DeInit |

Coordination between windows is by an OS event-flag bitmap at 0x03023CF8 with API
[P]: post 0x0306723C(id), test-and-clear 0x03067258(id), clear 0x0306727E(id),
test 0x0306729C(id); plus a message send 0x03067452(payload-struct). Key events are
delivered to the active window's Key callback as the raw event word of §1.3. There is
no (screen, key) → action table anywhere; each window's Key function is a hand-written
switch over the event word. That is the single most important structural fact for the
remapping goal (§5).

### 1.6 Key → action table

Producer codes (proven, §1.2/§1.3) × consumer behaviour. Module 32 (settings menu) Key
handler 0x0307DDA6 decoded in detail [P]; module 31 (now playing) shares the volume code
(identical sequence at 0x0307DC84) [P]; other module-31 actions are [I] as marked.

Event notation: `T4·0x0010` = type 4 (short release), mask 0x0010.

| Event | Stock action | Where |
|---|---|---|
| `T4·0x0010` or `T3·0x0010` | Volume +1 (field +0x12 of settings struct, clamp 120; applies via audio fns 0x030570E8/0x03057040; posts flag 0x19A) | mod 32 @ 0x0307DEA0 / 0x0307DE32→0x0307DE84 region; same code mod 31 @ 0x0307DC84 [P] |
| `T4·0x0020` or `T3·0x0020` | Volume −1 (same path) | mod 32 @ 0x0307DE84 [P] |
| `T4·(item keys)` in menu | Adjust selected item: item record (12-byte records at menu struct 0x03024834 +0x10, index at +0x0C) byte +2 = value index (decrement path at 0x0307DEC0), byte +5 = state; posts flag 0xC8; items whose sub-struct halfword +0xE == 1 are inert; item IDs 0xAD (173) and 0xC4 (196) get special handling branches (0x0307DF6C / 0x0307DF84), these IDs equal the first EQ string ID (173) and first brightness string ID (196), so menu items are keyed by language-string ID [P IDs, I meaning] |
| `T2·0x0040` (long ESC) | branch to 0x0307E01A in menu key handler [P branch, I "exit/back"] | mod 32 |
| `T2·0x0004`, `T2·0x0008` (long FFD/FFW) | branches to 0x0307DF96 / item-action 0x0307DEC0 [P branches, actions I] | mod 32 |
| any · 0x0001 held > 100 ticks | system event 0x1A posted (power-off request) [P post, I purpose] | key SM 0x03061900s |
| wheel steps | menu/now-playing navigation + the "Rotate to Unlock" gesture; consumed by polling counters 0x03023178/0x03023179 [P counters, I per-screen use] | §1.4 |
| `T*·0x4000` (OK), `T*·0x0010/0x0020` in now-playing | [I] play/pause and track/level actions, module 31's Key callback was not fully decoded in this pass; its Service callback (below) and the shared volume code are proven, the rest is inference from the framework layout and NeoPod's control map | mod 31 |

What is proven absent: no remapping indirection exists, meaning no key-map table and no
per-key action pointers. Every consumer hard-codes mask constants in its switch.

---

### 1.7 Headphone unplug: stock already reacts [P path, I meaning]

Stock debounces the headphone jack and acts on unplug. This settles the
"pause on unplug" candidate from the 2026-11-08 source survey: a patch
for it is probably unnecessary.

1. **Debounce, module 0 `0x03064D9E`.** Reads GPIO(0,13) through the
   read helper `0x030560F2` (`gpio_read(0, 13)`). A change starts a timer
   from the 10 ms tick `0x03023298`; once the level holds for more than
   50 ticks (0.5 s), the routine acts:
   - level high (jack occupied): clear event flag `0x2B` and mark
     "plugged" (state byte `+6` = 1);
   - level low after having been plugged: **set flag `0x2B`** and mark
     "unplugged".
   It returns the plugged byte. NeoPod reads the same pin the same way
   (high = 3.5 mm plug present; `neopod_xref.md` B11).
2. **Consumer, module 33 `0x0308A230`.** The playback service
   test-and-clears flag `0x2B`. When it was set, the halfword at
   `0x03023924` is 0, and flag `0x19B` is not set, it calls the playback
   command entry `0x03088540` with command `0xE6` and sets flag `0x43`,
   which redraws the transport row (the play/pause glyph;
   `patches/design_refresh_v4/design_v4.md`).

Flag helper roles are from `analysis/event_flags.md` (`0x0306723C` set,
`0x0306727E` clear, `0x03067258` test-and-clear).

**What is not proven:** that command `0xE6` means pause. The player
window (module 27) sends `0xE6` and `0xE7` from its key handler
(`0x030804E4`, `0x030804A0`) and module 33 sends `0xE6` on two other
paths, which fits a play/pause pair, but the command table in module 33
was not decoded. Nor is the meaning of `0x03023924` (it gates both this
path and a Bluetooth path at `0x0308A312`, with values 0 and 3 seen).
The cheapest proof is a device test: unplug headphones during playback
and see whether playback stops. Until then, treat stock as likely
pausing on unplug.

## 2. Lock screen ("Hold")

### 2.1 Lock state [P]

The lock/hold state is byte +0x60 of the system settings/state struct at 0x030232A0
(see §3). Evidence: module 31's Service handler, on consuming event flag 0x14E, executes
`printf("HoldOnplay : %d", [0x030232A0+0x60])` (ADR xref at 0x0307DC1E, call to printf
wrapper 0x0306D8F0 at 0x0307DC20). The boot validator clamps +0x60 to ≤ 1. It is a
persistent boolean. Module 5's handler also reads/writes +0x60 (at 0x0307D518: if +0x60==1
it substitutes halfword 0x0B in an outgoing message). The mode applet participates in
hold behaviour. SDK name for this feature is "Hold" (dialog window `DialogHold`,
`HoldState`, `HOLD_STATE_ON=0/OFF=1` in the SDK's inverted convention; do not import the
SDK's polarity; stock semantics of the byte are "nonzero = hold engaged" per the
'HoldOnplay' print and the module-31 snapshot path below).

The lock *gesture*: language string 121 = 'Rotate to Unlock' [P, `lang 2` dump].
Combined with the wheel-counter design (§1.4), [I] unlock = rotate the wheel while held;
engage is via the settings switch / key combination. The exact engage gesture was not
isolated in stock code (SDK uses a PLAY+MENU key combo, `KEY_VAL_HOLD`; the Neo lacks a
MENU bit in its producer, so the combo cannot be stock behaviour as-is).

### 2.2 What happens when hold engages during playback [P]

In module 31's Service handler (flag 0x14E branch, 0x0307DC0E–0x0307DC7C), if +0x60 ≠ 0
the now-playing applet snapshots the current track into shared display globals:

- halfword [struct +0x85] → stored to 0x03023980+0xF2 and to 0x030235C0
- 128 halfwords from struct +0x87 (a 256-byte buffer at struct +0x87…+0x186, the current
  track name/path buffer) → copied to 0x030235CE
- format-string pointer 0x030056E9 (the 'MP1MP2…' extension table) → 0x03023980+0x10
- halfword [struct +0x5A] → 0x03023980+6; word [struct +0x193] → 0x0307BF58
- calls 0x030544A8, then sends message type 3 via 0x03067452 with payload
  {halfword = [struct +0x5A], halfword = 4}

So the firmware already stages track identity (name buffer + index + format) into
globals that outlive the now-playing window when hold engages. [I] The consumer is the
hold/locked display path (the message type 3 is its notification).

### 2.3 What the locked screen draws today [P assets, I composition]

Lock-related bitmaps in the image section [P, image-name manifest near file 0xC86D9A]:
`A_LOCKOFF1..4_(0,0)`, `A_SYSTEM_LOCKON_(0,0)`, `A_SYSTEM_LOCKOFF_(0,0)`,
`A_MUSIC_SMALLLOCK_(0,0)`, `A_MUSIC_SMALLLOCK_BACK_(0,0)`,
`A_BROWSER_SMALLLOCK_(0,0)`, `A_BROWSER_SMALLLOCK_BACK_(0,0)`,
`A_LIST_HOLD_(135,4)` / `A_LIST_NOHOLD_(135,4)`.
The per-screen SMALLLOCK variants (music, browser, list) indicate the stock "lock screen"
is not a separate full-screen window: each applet overlays a small lock badge on its
own screen while hold is on, and text is limited to the unlock hint (string 121).
No lock-screen-specific window module was isolated; consistent with the SDK, hold is a
framework-level dialog (`DialogHoldDisplay/Key/Service`) whose Display is minimal.
[I] The locked display therefore shows: the underlying screen (or a dimmed variant), a
small lock icon, and 'Rotate to Unlock'. It does not draw title/artist/time today.
No text-draw calls with the metadata fields were found in a lock path.

### 2.4 Is track metadata available to a lock-screen draw?

- Title/name: yes. Already snapshotted to 0x030235CE (256 B) with index at
  0x030235C0 / 0x03023980+0xF2 by the now-playing applet itself (§2.2) [P]. [I] The buffer
  at struct +0x87 is the current file's name/path as loaded by the player; whether it
  contains parsed ID3 artist separately was not established. The player keeps ID3 fields
  elsewhere (module 31 draws `A_MUSIC_ID3` background on its own screen).
- Playback position: the audio engine exposes current/total time through the same
  getters the applets already call for their own UI. Module 5's and module 31's paint
  code call 0x0306316E(1) and 0x0306314A(2) (argument selects the value; [I] elapsed/total)
  [P calls, I semantics]. These are resident module-0 functions, callable from any
  overlay, including a patched lock Display.
- Artist: not in the snapshot. [I] It would have to be read from the player's ID3
  state (module 31's data) at draw time, or added to the snapshot copy in §2.2 (the copy
  loop is 8 instructions, so extending it is a small, well-localised patch).

### 2.5 The V137 "disable lock screen" switch

V137's release notes add a lock-screen disable switch. No dedicated language string for
it exists among the 266 English strings (nearest: 184 'Lock Screen Wallpaper',
121 'Rotate to Unlock') [P]. [I] The switch therefore reuses an existing label/on-off
submenu in the settings menu. Its settings flag was not isolated in this pass:
candidates are the boolean fields of the settings struct that the boot validator clamps
to ≤ 1 (+0x13, +0x1A, +0x1C, +0x2E4, +0x2E7; §3), distinct from +0x60, which is the
live hold state itself. Pinning it down needs one more pass over module 32's item table
(item records keyed by string ID; the lock item would sit near ID 184).

---

## 3. Settings storage: the SAVEINFO record

### 3.1 The record [P]

There is one persistent settings/state record: a 0x300-byte (768-byte) struct,
live in RAM at 0x030232A0, identified by magic 'SAVE' (0x45564153) at +0x00 and
'INFO' (0x4F464E49) at +0x2F8, with a checksum at +0x2FC (computed by 0x0306CAA6 over
0x17E0 bytes of the source buffer; the stored image is larger than the live struct; the
read buffer in boot code is 0x800 bytes on the stack).

Boot load (module 1, ~0x0307DB60–0x0307DD06) [P]:
1. Opens device 1 (0x0305D908(1, 2, buf)) and reads blocks from device handle 0x30000
   (device 3 = the firmware/settings store) via block-read 0x03067510. The settings live
   in a raw partition of the internal store, not in a filesystem file.
2. Verifies a header block magic 'FWUP' (bytes 'F','W','U','P'), the SAVE/INFO magics,
   and the checksum; the block index is computed from a slot byte (dual-copy layout:
   index = slot×32 + 8 blocks).
3. On any mismatch it rebuilds defaults field-by-field and posts event flag 0x189
   ([I] "settings dirty: save defaults back").
4. Valid fields are copied into the live struct with per-field range clamps. This
   clamp pass is what makes the field map below provable.

### 3.2 Field map (offsets into 0x030232A0; all [P] as to offset/range/default)

Defaults are the values written by the rebuild path at 0x0307DCB4+ when the stored record
is invalid. Semantics are [I] unless tied to a proven consumer.

| Offset | Size | Range (clamp) | Default | Meaning |
|---|---|---|---|---|
| +0x00 | 4 | none | 'SAVE' | magic |
| +0x0E | 1 | 0–4 | 2 | system/device mode byte, written with 2 or 4 by the mode applet (module 5, with calls to 0x0305791A(mode)); [I] not play mode |
| +0x10 | 1 | 0–20 | 2 | index remapped at load through a 21-entry table (loop at 0x0307DE00 builds map at 0x030237D7, count 0x15), [I] volume level index for UI |
| +0x11 | 1 | none | none | copied verbatim; replaced from a defaults table if nonzero-check fails |
| +0x12 | 1 | 0–120 (0x78) | 50 | **volume** [P: incremented/decremented by the vol± key actions §1.6, applied via 0x030570E8] |
| +0x13 | 1 | 0–1 | from defaults table | boolean (candidate: resume-playback switch, strings 154/155) [I] |
| +0x14 | 1 | 0–5 | from defaults table | enum [I] |
| +0x15 | 1 | 0–6 | from defaults table | enum [I] |
| +0x17 | 1 | 0–5 | none | enum [I] |
| +0x18 | 1 | 0–4 | 2 | enum [I] |
| +0x19 | 1 | 0–3 | 3 | enum [I] |
| +0x1A | 1 | 0–1 | none | boolean [I] |
| +0x1B | 1 | 0–2 | 1 | enum; gates the +0x5C resume word (zeroed when +0x1B==0) [P gate, I meaning] |
| +0x1C | 1 | 0–1 | none | boolean; selects whether +0x12 takes flash +0x12 or +0x1D at load [P], [I] "restore last volume" style flag |
| +0x1D | 1 | 0–120 | 50 | second volume-range byte (see +0x1C) [P range, I meaning] |
| +0x1E–0x20 | 1×3 | none | from header bytes | copied from the FWUP header (slot/version bytes) [P] |
| +0x29 | 1 | 0–4 | 2 | enum [I] |
| +0x2A | 2 | none | none | halfword read by module 5's handler [P use, ? meaning] |
| +0x3E | 2 | none | none | halfword cleared/set by module 5 [P use, ? meaning] |
| +0x5A | 2 | if 0 → 1 | none | [I] current track index (sent in messages, copied for hold snapshot) |
| +0x5C | 4 | none | none | [I] resume position/file word (gated by +0x1B) |
| +0x60 | 1 | 0–1 | none | **hold/lock state** [P, §2.1] |
| +0x85 | 2 | none | none | halfword copied into the hold snapshot [P] |
| +0x87 | 256 B | none | none | current track name/path buffer (snapshot source) [P copy, I content] |
| +0x193 | 4 | none | none | word copied into the hold snapshot (→ 0x0307BF58) [P copy, ? meaning] |
| +0x2D5 | 1 | 0–3 | 1 | enum [I] |
| +0x2D9 | 2 | < 500 | none | halfword [I] |
| +0x2E2 | 1 | 0 or 0x55 only | 0 | sentinel-style byte [P validation] |
| +0x2E4 | 1 | 0–1 | none | boolean [I] |
| +0x2E5 | 1 | 0–2 | 2 | enum [I] |
| +0x2E7 | 1 | 0–1 | none | boolean [I] |
| +0x2E8 | 1 | 0–24 (0x18) | 12 (0x0C) | [I] brightness level or screen-off minutes, the 0–24 range fits neither string table exactly; unresolved |
| +0x2F1 | 1 | 0–3 | none | enum [I] |
| +0x2F8 | 4 | none | 'INFO' | magic |
| +0x2FC | 4 | none | none | checksum |

### 3.3 What is *not* the settings record [P]

The 512-byte `sysdefault` section at file offset 0x16F920 (header count field = 2 at
0x74) is audio DSP parameter defaults, not user settings: its content is fixed-point
coefficient tables (repeated 0x3FF8 unity-gain words, band values 0x88/0x90/0xB8/0x48…)
with no booleans, no volume, no strings. The tasking lead was checked and rejected on
content. Consequence: there are no "spare bytes in sysdefault" for a remap table.
See §3.4 for where remap data could actually live.

### 3.4 Room for a key-remap table

- The live record is mostly dense in +0x00–+0x2F1, but the validator only *checks* the
  fields listed above. Regions of the 0x300-byte struct never referenced by the clamp
  pass (e.g. +0x21–+0x28, +0x30–+0x3D, +0x62–+0x84, +0x187–+0x192, +0x2DA–+0x2E1,
  +0x2E9–+0x2F0) are [I] unused or runtime-only. But the record is checksummed and
  dual-slot, so repurposing bytes is only safe if the save path writes the whole struct
  back unchanged in size. The save path itself (who calls the block-write counterpart of
  0x03067510, and when; flag 0x189 is the [I] trigger) was not fully traced; a remap
  implementation must verify save/restore of any borrowed bytes on real boot cycles.
- A safer home [I]: append remap entries in the settings-menu applet's own persisted
  item state, or store the table in the record's unchecked gaps above after the save
  path is verified. The struct is shared by every applet (0x030232A0 is referenced from
  modules 1, 5, 21–24, 27, 31, 32…), so any new field is globally visible for free.

### 3.5 Settings the owner asked about: status

| Setting | Field | Status |
|---|---|---|
| Lock (hold) state | +0x60 | [P] |
| Lock-screen disable switch (V137) | one of +0x13/+0x1A/+0x1C/+0x2E4/+0x2E7 | not isolated [I candidates] |
| Volume / default volume | +0x12 (live), +0x1D (stored) | [P] |
| Screen-off time / brightness | +0x2E8 is the only wide-range tail byte (0–24, default 12) | [I], unresolved |
| Gain (strings 181–183: Low/High) | a 0–1 or 0–2 byte among +0x13/+0x1A/+0x2E4/+0x2E7/+0x2E5 | not isolated |
| EQ type | handled inside module 32's own item state ('MenuKeyPro - SelItemID=%d, SetEqType=%d' debug print) + DSP coefficients from `sysdefault` | [P print], EQ selection may not live in SAVEINFO at all |
| Bluetooth switch | not found in SAVEINFO clamps | see §4 |

---

## 4. Bluetooth: toggle callability verdict

**Verdict: welded to the settings window's state machine. No global BT on/off function
was found that a shortcut could call.** Evidence:

1. No Bluetooth stack or driver strings exist in any of the 82 modules [P, full
   per-module ASCII scan]: no 'Bluetooth', 'A2DP', 'AVRCP', 'HCI', 'AT+' strings outside
   coincidental byte fragments. BT appears only as language strings 10, 130–132, 166–171
   ('Bluetooth', 'Please turn on Bluetooth!', 'Bluetooth Settings', 'Bluetooth Switch',
   'On'/'Off', 'Search Device', 'Paired Devices').
2. The framework this firmware is built on implements Bluetooth as a settings-window
   state machine, not a service API: the SDK's SetBluetooth.h defines window states
   `BT_WIN_STATUS_IDLE/SCAN/CONNECTING/…/BT_OFF_ING/BT_GO_TO_OFF`. Power transitions are
   states of the Bluetooth settings window itself, driven through its Service/Key
   callbacks and system messages [P for the SDK design; the stock firmware uses the same
   window framework, §1.5].
3. In stock code, Bluetooth UI ownership sits in module 32 (settings menu). The
   menu items for strings 166–171 are its item records; the BT *switch* field was not
   found among the SAVEINFO clamp fields (§3.2), consistent with BT state being held by
   the BT window/driver rather than the settings record [P absence in clamps, I conclusion].
4. No overlay contains a small exported "BT on/off" routine: the only cross-module
   callable surface found in this firmware is module-0 resident functions; none of the
   module-0 functions traced in this workstream (audio, ADC, GUI, flags, block I/O)
   touches Bluetooth, and no module-0 function is referenced by module 32 in a
   BT-item context that was isolated. [P within the traced scope]

What a Bluetooth shortcut would actually require [I]: either (a) synthesise the same
window/message sequence the settings menu produces when its BT switch item is toggled,
i.e. drive the BT window's state machine from outside, which needs the BT window module
and its message IDs identified first (not done here; the BT window is likely one of the
unexamined 0x0307E9C0-family overlays, modules 24–26/30, or in the base-0x00000000 blobs
63–69, none of which yielded BT strings); or (b) find the underlying radio power/driver
call inside that window's toggle handler and call it directly, accepting that the
window's state and the settings record may desynchronise. Both are new-logic efforts,
not a call-this-function shortcut.

---

## 5. Difficulty verdicts

### 5.1 Lock screen showing track + artist + position

**Verdict: code patch in overlay (moderate). Not a string/resource patch; not new
overlay logic from scratch.**

Reasons, tied to the structures above:
- The data is already staged: when hold engages, the now-playing applet itself copies
  track name (256 B) + index into shared globals 0x030235CE / 0x030235C0 (§2.2) [P].
  A lock Display that reads those globals needs no new plumbing for the title.
- Position is available from resident getters (0x0306316E / 0x0306314A) that applets
  already call [P calls exist]; the lock Display can call them the same way.
- The draw primitives are resident and shared (image draw 0x03063700, text via the GUI
  helpers used by every applet's Display callback) [P usage across modules].
- What is missing: (a) artist is not in the snapshot. Extend the §2.2 copy (a
  ~8-instruction loop in module 31) or read the player's ID3 state at draw time;
  (b) the lock Display today draws only a badge + hint, so the patch adds text draws to
  that Display function, and the function itself was not isolated to an address in this
  pass, which is the first task of the patch work; (c) the periodic repaint while locked
  (for the position readout) depends on the window Service cadence, and the framework
  already ticks windows via Service callbacks [I].
- No resource/string changes are needed except optionally new layout bitmaps; the
  320×240 RGB565 asset set already includes a full now-playing theme to reuse.

### 5.2 Remappable physical controls (incl. a Bluetooth shortcut)

**Verdict: new overlay logic (hard). A limited subset is a code patch; full remapping
is not.**

Reasons:
- Dispatch is hard-coded per window (§1.5/§1.6): each applet's Key callback switches on
  raw event words. There is no key-map table to edit. A "resource patch" cannot exist.
- A *producer-side* remap is the cheapest real option [I]: patch `GetKeyMask`
  (0x030617A0, module 0, ~5 compare/store sites) or the state machine's event-word
  construction to translate physical keys before any window sees them. That remaps
  globally with a tiny patch, but: it cannot distinguish screens (Vol± would swap
  everywhere, including menus), it cannot express "long-press OK = X" style bindings
  beyond what the type nibble already encodes, and module 0 is the resident image.
  Patching it touches the one component every overlay depends on (update-package CRC is
  recomputable per prior analysis; no signature check was found by the parent workstream,
  but module 0 is still the highest-blast-radius target).
- A *consumer-side* remap (the flexible design) requires: a remap table in persistent
  storage (§3.4; feasible, bytes exist, but the save path must be verified), an
  interception point in the window manager's key delivery (not located; delivery may be
  direct callback invocation by the framework), and a settings UI to edit bindings
  (module 32's item system could host it; items are string-ID-keyed 12-byte records,
  so new items are addable in principle). Each piece is real work; together they are a
  new feature, not a patch.
- The Bluetooth shortcut specifically stacks §4 on top: even with remapping solved,
  the *action* "toggle Bluetooth" has no callable target today. The shortcut is blocked
  on the BT-window reverse engineering described in §4, independent of the key side.

### 5.3 Suggested order of work [I]

1. Lock-screen info display (§5.1): self-contained, data already staged.
2. Producer-side fixed remaps (e.g. swap two keys globally) if the owner wants a quick
   win (§5.2, module-0 patch, small).
3. BT window identification → only then judge whether a BT toggle action can be exposed.
4. Full consumer-side remapping last. It is a feature build, and it can reuse (3)'s
   action registry if one is created.

---

## 6. Open items / not established in this pass

- Module 31's Key callback not fully decoded (now-playing per-key actions partly [I]).
- The lock Display function's module/address not isolated; engage gesture not isolated.
- V137 lock-disable switch's exact settings offset not isolated (candidates in §2.5).
- SAVEINFO save path (writer, trigger timing) not traced end-to-end; +0x2E8 semantics
  unresolved; several enum fields (§3.2) lack proven meanings.
- Wheel direction sign (which counter = clockwise) not established; input tick period
  not established (all thresholds are in ticks).
- Modules 24–26, 30 (0x0307E9C0 family) and 63–69 (base 0) not catalogued here. The
  Bluetooth window may live there (sibling workstream covers the module catalog).

## Appendix: key addresses

| Address | What |
|---|---|
| 0x030560F2 | GPIO read (port, pin) |
| 0x0305FDBC | SARADC init; scan order {1,1,2,0} @ 0x03005684 |
| 0x0305FE92 | SARADC ISR; results @ 0x030059AC |
| 0x0305FF28 | ReadADC(channel) |
| 0x030617A0 | GetKeyMask (producer) |
| 0x030617FE | Key state machine wrapper; flag @ 0x030230EC |
| 0x03061936 | Wheel quadrature decoder; counters @ 0x03023178/79/7C |
| 0x03061AB2 | Periodic input task |
| 0x0306723C / 258 / 27E / 29C | Event flags: post / test+clear / clear / test; bitmap @ 0x03023CF8 |
| 0x03067452 | SendMessage |
| 0x03067510 | Block read (device 3 store) |
| 0x03063700 | DrawImage(id) |
| 0x0306316E / 0x0306314A | Playback info getters (used by paint code) |
| 0x030232A0 | SAVEINFO settings/state struct (0x300 B) |
| 0x0302309C | Key state machine struct; event word @ +0x34 |
| 0x030235CE / 0x030235C0 | Hold snapshot: track name buffer / index |
| module 1 @ 0x0307DB60+ | SAVEINFO load/validate/defaults |
| module 31 @ 0x0307DC0E | Hold-engage snapshot ('HoldOnplay') |
| module 32 @ 0x0307DDA6 | Settings menu Key handler |
| module 32 WIN @ data 0x030247C4 | Service 0x0307D807, Key 0x0307DDA7, Display 0x0307D7B9, Init 0x0307D165, DeInit 0x0307D1AB |

*Scripts/data in this folder: `mdisasm.py` (module-pinned disassembler), `blscan.py`,
`scan_strings.py`, `modstrings.py`, `lang2.json` (266 English strings), `modstrings.json`
(per-module ASCII strings).*
