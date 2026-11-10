# BT power-cycle side effects: evidence

Scope: the five side effects of module 21's flag-0x1BD handler
(`module_21_code_0307d164.bin`, handler at 0x0307D574, side-effect block
0x0307D5E8–0x0307D61E), plus the producer of flag 0x1B2. All addresses are
exec addresses. Scan methods are stated per item so negatives are checkable.

Register facts used throughout (module 21 Service prologue,
0x0307D2C4–0x0307D2E4): `sl` = SAVEINFO base 0x030232A0, `r5` = 0, `r6` = 1,
`fp` = 2. So in the handler `strb r6` writes 1 and `strb r5` writes 0.

Key resident structures (module 0):

- BT poll state struct at **0x03004168**, used as a base register (`sl`/`r5`)
  by module 0's BT poll 0x030657AC and its supervisor 0x03065FD4. Fields:
  +0x4 = 0x0300416C, +0x6 = 0x0300416E, +0x7 = 0x0300416F, +0x8 = 0x03004170,
  +0xC = 0x03004174, +0x10 = 0x03004178, +0x14 = 0x0300417C.
- UART channel state at **0x03004104**: +0 = TX byte count (halfword),
  +8 = 0x0300410C = RX buffer pointer. The module-0 data image
  (`module_00_data_03004000.bin`, offset 0x10C) initialises [0x0300410C] to
  0x0300642C.
- BT TX packet buffer at **0x030064AC**, its length byte at **0x03004116**;
  BT RX buffer at **0x0300642C**; BT status byte at **0x0300411C**;
  TX/RX gate byte at **0x03023124** (set by the power-on banner check,
  0x0307D27E–0x0307D28A in module 21: 5 if RX buffer[3] == 0x35, else 0).

---

## 1. Flag 0x123: NEEDED

### Poster / consumers found

Byte-pattern scan of every `*_code_*.bin` for the `movw r0,#0x123`
encoding (40 F2 23 10) finds exactly five sites:

| Site | Op | Context |
|---|---|---|
| mod21 0x0307D5E8 | post (bl 0x0306723C at 0x0307D5EC) | the power cycle itself |
| mod0 0x030657B0 | test-noclear (bl 0x0306729C at 0x030657B4) | entry of BT poll 0x030657AC |
| mod0 0x030658C2 | test-noclear (bl at 0x030658C8) | BT poll, periodic-query gate |
| mod0 0x03065840 | clear (bl 0x0306727E at 0x03065844) | BT poll, after acting on the flag |
| mod0 0x030661D2 | clear (via tail branch to 0x030660A2) | supervisor 0x03065FD4, state-byte==0xE path |

Plus one clear in module 81 at 0x0307DD1A (bl 0x0306727E at 0x0307DD1E),
in a teardown function at 0x0307DD02 that also posts 0x1B4 and clears
0xD9/0xDA. That is window-exit cleanup, not a semantic consumer.

No other poster exists. Direct bitmap access is excluded: a literal-word
search for 0x03023D1C (word 9 of the bitmap at 0x03023CF8, bit 3 =
flag 0x123) over all extracted `.bin` files (code and data) found zero
occurrences.

### What the consumer does (BT poll 0x030657AC)

The poll is resident and runs constantly: supervisor 0x03065FD4 calls it
at 0x03066022 whenever SAVEINFO+0x2D4 == 1, and the supervisor itself is
called from module 0's main dispatch loop at 0x03067320.

Flag-set path (0x030657D4–0x03065852):

1. If tick [0x03023298] minus [0x03004174] ≤ 0x12C (300), do nothing yet.
2. Stores tick into [0x03004174]; if SAVEINFO+0x2D3 != 0 or [0x0300416C]
   == 0, skip to the clear at step 4.
3. Otherwise builds a TX frame in 0x030064AC: `'C','L'`, then 6 bytes
   copied from SAVEINFO+0x1C7..+0x1CC into frame bytes [4..9]
   (loop 0x030657FE–0x03065812), frame[2] = 0x30, frame[3] = 0x36,
   sets SAVEINFO+0x2D2 = 1 (0x03065816), TX length [0x03004116] = 0x0A,
   posts flag 0x1B8 (TX pending, 0x0306582E), posts flag 0x1B4
   (0x03065836), and writes BT status byte [0x0300411C] = 2 (0x0306583E).
4. Clears flag 0x123 (0x03065844), stores tick into [0x03004174] again,
   writes [0x0300416C] = 0.

Flag-clear path (0x03065854–0x0306587C and 0x030658A8–0x030658FC): the
flag is also the gate for the poll's idle behaviour. The 0x1BD re-post
countdown (item 3, +0x6 byte) only runs in the flag-clear branch, and the
periodic `"CQ00"` query frame (built inline at 0x030658CE–0x030658EC,
TX length 5, post 0x1B8) is sent only when test-noclear(0x123) returns 0
at 0x030658C8 and the [0x03004118] timestamp is stale (>0x64 ticks, or
>0x1F4 when SAVEINFO+0x2D3 != 0).

### Verdict

**NEEDED.** Flag 0x123 is a private handshake from the power cycle to the
resident BT poll. Posting it (with items 3a and 5, its enabling
conditions) makes the poll emit the `"CL" + 6-byte SAVEINFO name/code`
frame to the BT module over the UART, set status [0x0300411C] = 2, set
SAVEINFO+0x2D2, and post 0x1B4. No overlay module consumes it. Omitting
the post leaves the poll in its idle-query mode and the CL frame is never
sent after power returns.

---

## 2. Function 0x03053242: NEEDED (UART3 re-initialisation)

Full disassembly (module 0, 0x03053242–0x03053264):

```
03053242  push {r3, lr}
03053244  ldr  r1, [pc]        ; literal [0x03053268] = 0x03004144
03053246  movs r0, #0
0305324a  str  r0, [r1, #4]    ; [0x03004148] = 0
0305324c  movs r0, #2
0305324e  str  r0, [sp]        ; stack arg = 2
03053250  movs r2, #8
03053252  mov.w r1, #0x1C200   ; 115200
03053256  movs r0, #3          ; channel 3
03053258  bl   0x0305654E      ; generic UART configure
0305325c  movs r1, #1
03053262  mov  r0, r1
03053264  b.w  0x03056392      ; tail: enable
```

- 0x0305654E is the generic per-channel UART configure routine: it
  dispatches on the channel index (tbb at 0x0305656C), programs the
  channel's GPIO mux/dir/level helpers, calls the hardware init
  0x0305134C (baud divisor from 0x16E360 / baud, control-register setup),
  and finishes by registering and enabling that channel's RX IRQ
  (see item 6).
- The tail call 0x03056392 looks the channel up in the peripheral table
  at 0x0306DD94 and ORs r1 (= 1) into [peripheral+4], the channel
  enable bit.
- The state struct at 0x03004144 belongs to the UART driver. The TX helper
  0x03052FB8 reads its byte 0 as a busy flag and 0x03052FE0 uses byte 1;
  the neighbouring helpers 0x03053230 (sets [0x03004148] = arg and a
  word 1 at +4) and 0x0305323A (clears +4) operate on the same struct.
  0x03053242 clears +4 before reconfiguring.

Callers (exhaustive per-offset BL scan of all extracted code bins with
base != 0 and != 0x01000000, targets 0x03053242 / 0x0305654E):

- module 1, 0x0307D55C (its BT/media init sequence, after clearing
  [0x03023160] and calling 0x0305328C)
- module 21, 0x0307D5F0 (the power cycle)
- module 81, 0x0307D30A and 0x0307DC60 (both power-on sequences; each is
  followed, after a delay, by 0x03065772('S') / banner handling)
- module 81's Init at 0x0307D192 calls 0x0305654E directly with the
  identical argument set (r0=3, r1=0x1C200, r2=8, r3=0, stack=2) and the
  same enable tail, i.e. it inlines 0x03053242.
- No caller inside module 0 (per-offset BL scan of
  module_00_code_03050000.bin: the only call to 0x0305654E is at
  0x03053258, inside 0x03053242 itself).

### Verdict

**NEEDED.** It is not generic housekeeping. It is the BT UART's
(re)initialisation: channel 3 at 115200, driver state reset, peripheral
enabled, RX IRQ (re)registered and enabled (item 6). Every stock BT
power-on path calls it (or its inline twin in module 81's Init). A
replica that skips it relies on UART/IRQ state that, on a cold path, was
never set up.

---

## 3. Bytes 0x0300416C / 0x0300416E / 0x0300416F: MIXED (one needed, two bookkeeping)

These are fields +0x4 / +0x6 / +0x7 of the BT poll state struct at
0x03004168 (see header). Literal-word searches over all extracted bins:
0x0300416C and 0x0300416E occur only in module 21's literal pool
(0x0307D70C / 0x0307D710); 0x0300416F occurs there (0x0307D714) and in
module 81's pools (0x0307D5DC, 0x0307DEF8, both in module 81 code that
mirrors the poll/supervisor logic for its own window). All other
accesses are base+offset from a register holding 0x03004168 (module 0
poll/supervisor). The complete access list below is from disassembling
those two functions and the two writers.

### 3a. 0x0300416C (struct+4): NEEDED (as part of item 1)

- Writer: module 21 cycle, = 1 at 0x0307D602.
- Reader/writer, module 0 poll: tested at 0x030657EC (`cbz`; if 0, the
  CL frame of item 1 is skipped); cleared at 0x0306584E after the CL
  send, and at 0x03065854 on the flag-clear path.

It is the one-shot enable for the CL frame: the cycle arms it, the poll
consumes and clears it. Without it, posting 0x123 alone does nothing.

### 3b. 0x0300416E (struct+6): BOOKKEEPING

- Writers: module 21 cycle, = 0 at 0x0307D604; supervisor = 0 at
  0x030661D0 (state-byte==0xE path); poll decrements it at
  0x03065872–0x03065874 and zeroes it at 0x03065886 when
  SAVEINFO+0x2D3 != 0.
- Reader: poll flag-clear path, 0x0306586C. If SAVEINFO+0x2D3 == 0 and
  this byte is nonzero, each >400-tick interval (item 5 timestamp)
  decrements it and re-posts flag 0x1BD at 0x0306587C, i.e. it is a
  "re-run the power cycle N more times" countdown.
- No writer of a nonzero value was found in any module (literal scans
  above; base+offset scan of the only two module-0 functions that hold
  the struct base). As far as the extracted firmware shows, the
  countdown is inert: it starts at 0 (BSS; data image word at
  0x0300416C is 0) and the cycle resets it to 0.

The cycle's write is a reset of a counter that is already 0 in every
reachable state found. Safe to omit; harmless to keep.

### 3c. 0x0300416F (struct+7): BOOKKEEPING

- Writers: module 21 cycle, = 0 at 0x0307D616 (immediately after writing
  SAVEINFO+0x2D3 = 0 at 0x0307D612); supervisor: = 0 at 0x0306601C when
  SAVEINFO+0x2D4 == 0, and = SAVEINFO+0x2D3 at 0x03066040 whenever it
  changes.
- Reader: supervisor at 0x0306602A–0x03066040. It is the supervisor's
  shadow copy of SAVEINFO+0x2D3, used purely for edge detection (on a
  falling edge it clears flag 0x1CB at 0x03066034–0x03066038; the new
  value is then copied into the shadow anyway).

Because the supervisor re-synchronises the shadow on the first tick
after any change, the cycle's write is redundant. A replica that writes
SAVEINFO+0x2D3 = 0 (as the stock cycle does) but leaves 0x0300416F stale
produces one edge detection, one clear of 0x1CB, and the same final
state. Safe to omit.

---

## 4. Function 0x03065772 with r0 = 0x53 ('S'): NEEDED

Disassembly (module 0, 0x03065772–0x030657A0), literals resolved:

```
03065772  ldr  r1, [pc]        ; [0x030659EC] = 0x03023124 (gate byte)
03065774  ldrb r1, [r1]
03065776  cmp  r1, #5
03065778  beq  0x03065782      ; gate == 5: send unconditionally
0306577a  cmp  r0, #0x87       ; else commands 0x87 / 0x86 are suppressed
0306577e  cmpne r0, #0x86
03065780  bxeq lr
03065782  movs r2, #0x43       ; 'C'
03065784  ldr  r1, [pc]        ; [0x030659E4] = 0x030064AC (TX buffer)
03065786  strb r2, [r1]        ; frame[0] = 'C'
03065788  strb r0, [r1, #1]    ; frame[1] = command letter
0306578a  movs r0, #0x30
0306578c  strb r0, [r1, #2]    ; frame[2] = '0'
0306578e  strb r0, [r1, #3]    ; frame[3] = '0'
03065790  movs r0, #0
03065792  strb r0, [r1, #4]    ; frame[4] = 0
03065794  strb r0, [r1, #5]    ; frame[5] = 0
03065796  ldr  r1, [pc]        ; [0x030659E8] = 0x03004116 (TX length)
03065798  movs r0, #5
0306579a  strb r0, [r1]        ; length = 5
0306579c  mov.w r0, #0x1B8
030657a0  b.w  0x0306723C      ; post flag 0x1B8 (TX pending)
```

So 0x03065772 is the BT command-frame sender: it formats
`"C" <cmd> "00"` into the TX buffer and queues it by posting 0x1B8.
The actual UART drain happens in the BT poll: test-and-clear 0x1B8 at
0x03065892, then the TX drain helper 0x0305126C at 0x030658A2 with the
count from [0x03004116] (same pattern at 0x030657A8, in the one-shot
flush helper 0x030657A4, and at supervisor 0x0306607C / 0x0306609C).
'S' (0x53) is simply the command letter for this call; the gate byte
0x03023124 is the banner-result byte (item header). 'S' is not one of
the suppressed commands (0x86/0x87), so it is sent regardless of the
gate.

Its sibling 0x03065756 is the two-argument variant (r0 = command,
r1 = frame[3] digit) building the same frame at 0x03065756–0x03065770
without the gate check and without posting 0x1B8 (callers post it).

All callers of 0x03065772 (per-offset BL scan, all bins) and their
command letters:

- module 21: 0x0307D608, 'S' (the power cycle)
- module 81: 0x0307D402 'S', 0x0307DC7A 'S', 0x0307DF98 'S',
  0x0307E042 'P', 0x0307E05C 'T', 0x0307E0C0 'Q', 0x0307E420 'H',
  0x0307E5AC 'T', 0x0307E6CE 'T'
- module 0: none (module 0 builds its `"CQ00"` query inline at
  0x030658CE instead of calling it)
- 0x03065756 callers: module 81 0x0307DECE / 0x0307DF14 (r0 = 'Y'),
  supervisor 0x0306606E and 0x0306608E (r0 = 'Y', r1 = 0x1E / 0)

In module 81, 'S' is sent in its power-on sequences (0x0307DC7A right
after its second 0x03053242 call at 0x0307DC60; 0x0307DF98 when its
state byte == 1, followed by post 0x1B4). That is the same position the
cycle's 'S' occupies, immediately after power is restored and the UART is
re-initialised.

### Verdict

**NEEDED.** This is a real command to the BT module on the UART
(`"CS00"`), sent by every stock power-on path at exactly this point in
the sequence. It is not window bookkeeping. The frame leaves the device.
Omitting it leaves the module powered but never issued the start
command the stock firmware sends after every power restore.

---

## 5. Copy [0x03023298] -> [0x03004174]: NEEDED (timing gate for item 1)

0x03004174 is field +0xC of the BT poll struct (item 3 header): the
poll's timestamp. Complete access list:

Writers:
- module 21 cycle, 0x0307D61C–0x0307D61E (literals at 0x0307D718 =
  0x03023298, 0x0307D71C = 0x03004174)
- poll itself: 0x030657E2 (on entering the flag-set action path) and
  0x03065848 (after clearing flag 0x123)

Readers (all in the poll; no other module holds the struct base with
this offset, see item 3 scan):
- 0x030657D6: `elapsed = tick - [0x03004174]`; the flag-set (CL) action
  is deferred until elapsed > 0x12C (300 ticks)
- 0x0306585A: same subtraction on the flag-clear path; the 0x1BD
  re-post countdown (item 3b) and related housekeeping run only when
  elapsed > 0x190 (400 ticks)

(The supervisor's other timestamps are different fields: [struct+0x10]
= 0x03004178, written at 0x030660BE and compared against 0x7530 at
0x030661D8–0x030661E6 for a power timeout; [struct+0x14] = 0x0300417C
at 0x030660CE–0x030660E4 for a once-per-second counter. Neither is
0x03004174.)

### Verdict

**NEEDED for stock-identical behaviour, as part of the item-1
mechanism.** The copy stamps "power was restored now" into the poll's
timestamp, which starts both of the poll's debounce intervals (300
ticks before the CL frame, 400 ticks before any countdown action). It
is one word copy from resident code, and the poll overwrites the field
itself on every action, so there is no stale-state risk in replicating
it. Skipping it leaves a pre-power-loss timestamp in place. The CL
frame would then fire on the first supervisor tick after the flag is
posted instead of after the 300-tick settle interval the stock cycle
creates.

---

## 6. Flag 0x1B2 producer: WINDOW-ARMED

### The producer

Byte-pattern scan for `mov.w r0,#0x1B2` (4F F4 D9 70) over all code bins
finds five sites: module 0 0x03051328 (post), module 0 0x03065900
(test-and-clear, poll RX parser), module 21 0x0307D1EC (test-and-clear,
power-on banner poll), module 81 0x0307D1E2 and 0x0307E0CC
(test-and-clear). **The only post site in the firmware is module 0
0x03051328–0x03051330.** A literal search for the flag's bitmap word
0x03023D2C (word 13, bit 18) over all bins found zero occurrences, so
there is no direct-bitmap producer either.

The post sits at the end of the common UART receive handler
0x030512C4 (module 0):

- Entry stubs at 0x03051334–0x0305134A load r0 = 5,4,3,2,1,0 and branch
  to 0x030512C4, one stub per UART channel. Channel 3's stub is at
  0x0305133C (r0 = 3).
- The handler reads the channel's peripheral from the table at
  0x0306DD94, extracts error/status bits from [periph+8] into the
  per-channel status byte at 0x03004110+channel (0x030512EA–0x030512F0),
  and if data is present, zeroes [0x03004108], calls the FIFO drain
  0x030563B0 with r2 = 0x64 (100) and r1 = [0x0300410C] (the buffer
  pointer, initially 0x0300642C per the data image), stores 0x0300642C
  back into [0x0300410C] (0x0305131E–0x03051320), and if the drained
  count is nonzero posts flag 0x1B2 (0x03051328–0x03051330).
- So the buffer at 0x0300642C is filled only here, by this handler,
  from the UART FIFO. Its readers are the power-on banner checks
  (module 21 0x0307D1E0–0x0307D204, module 81 0x0307D1E2 onward), the
  poll's RX parser (0x03065910 onward, sb = 0x0300642C), and module 81's
  Service parser (0x0307E0CC onward).

### How the handler gets invoked: IRQ registration inside UART configure

The handler is reached through the RAM vector table at 0x03004000
(the module-0 data image starts with that table: word 0 = 0x03004000,
word 1 = 0x030556B1, the rest initially the default handler
0x030663AF). Registration happens at the end of the generic UART
configure routine 0x0305654E (the routine item 2 calls):

- 0x030567D4: calls the hardware init 0x0305134C for the channel.
- 0x030567DA–0x030567E0: clears the channel status byte at
  [0x03004110 + channel].
- Per-channel tail (tbb at 0x030567E2): for channel 3, at
  0x03056822–0x03056832 it loads the stub address 0x0305133D from the
  literal at 0x03056874 and calls 0x030664E8 with r0 = 0x27 (IRQ
  number), then 0x03056D8E (r0 = 0x27), then falls into 0x03056C88.
  (Channels 0–5 map to IRQs 0x2A, 0x29, 0x28, 0x27, 0x26, 0x25 with
  stubs 0x03051349, 0x03051345, 0x03051341, 0x0305133D, 0x03051339,
  0x03051335 respectively, same block, 0x030567EC–0x03056856.)
- 0x030664E8 is the vector-install function: if SCB VTOR
  ([0xE000ED08]) does not already point at 0x03004000 it copies the
  default vectors there and sets VTOR = 0x03004000
  (0x0306650E–0x03066530), then stores the handler at
  [0x03004000 + IRQn*4] (0x03066532).
- 0x03056D8E sets the IRQ's bit in the NVIC enable registers
  (0x03056DB0–0x03056DC8 region, base derived from 0xE000E100 range);
  0x03056C88 clears the pending bit (base 0xE000ED24 / NVIC ICPR
  region).

The handler is therefore interrupt-driven, but it is armed only when
0x0305654E runs for channel 3. 0x0305654E's callers (item 2) are:
0x03053242 (called only by modules 1, 21, 81) and module 81's Init
inline copy at 0x0307D184–0x0307D19A. No resident module-0 code path
calls either at boot. The per-offset BL scan of
module_00_code_03050000.bin for targets 0x03053242 / 0x0305654E returns
exactly one hit, 0x03053258, inside 0x03053242 itself. Other IRQ
registrations that do happen in resident code (e.g. at 0x03054412,
0x0305466E, 0x030603FC) are for other peripherals/IRQs, not the UART
stubs.

No disarm path was found: nothing calls a UART-disable or NVIC-disable
for IRQ 0x27, and module 81's teardown at 0x0307DD02 only clears event
flags. Once any BT-family overlay has run, the IRQ stays armed for the
rest of the boot.

### The surrounding family (module 0, 0x03065700–0x03065900)

- 0x03065756 / 0x03065772: TX command-frame builders (item 4).
- 0x030657A4: one-shot TX flush (stores a length halfword at
  [0x03004104], tail-calls the drain 0x0305126C).
- 0x030657AC: the BT poll (items 1, 3, 5). Its sections, in order:
  (a) flag-0x123 / CL handshake (0x030657B0–0x03065852, posts 0x1B8 and
  0x1B4 at 0x0306582E / 0x03065836, sets [0x0300411C] = 2);
  (b) flag-clear housekeeping: 0x1BD re-post countdown (posts 0x1BD at
  0x0306587C);
  (c) TX drain: test-and-clear 0x1B8 at 0x03065892, on success calls
  0x0305126C at 0x030658A2;
  (d) periodic `"CQ00"` query when flag 0x123 is clear (0x030658C2–
  0x030658FC, posts 0x1B8 twice);
  (e) RX parser: test-and-clear 0x1B2 at 0x03065904; returns if unset.
  If set, it scans 0x0300642C for a `'C'` frame (0x0306591E–0x03065944,
  clearing flag 0x10E at 0x0306594C), dispatches on frame[1]:
  'P' (0x03065970, counts banner-like replies, may post 0x1A4),
  'C' (0x03065A16, may post 0x1C3 / 0x1A4), 'A' -> 0x1A3
  (0x03065A70), 'B' -> 0x1A2 (0x03065A8C), 'T' (0x03065A50),
  'Q' (0x03065AA8, parses the name response into SAVEINFO+0x2B1 /
  +0x1C7 and sets/clears SAVEINFO+0x2D3 at 0x03065AC2 / 0x03065B4C);
  finally re-tests 0x10E at 0x03065B54 and loops or returns.
  The function above the poll (ending 0x03065748) is a state-change
  reporter that posts flags 0x2C / 0x28 / 0x2D when three state bytes
  change, unrelated plumbing in the same page.

### Verdict

**WINDOW-ARMED.** The 0x1B2 producer is an interrupt handler, but the
interrupt is registered and NVIC-enabled only inside the UART
configure routine, which resident code never calls on its own. It is
reached from module 81's Init, module 81's / 21's power-on paths (via
0x03053242), and module 1's init. A replica running in a context where
no BT-family overlay has run since boot must arm the receiver first,
which is exactly what item 2 (call 0x03053242) does. Note the stock
cycle's own ordering confirms this dependency. It calls 0x03053242 at
0x0307D5F0, delays 100 ticks (0x0307D5F4–0x0307D5F6), and only then
calls the power-on/banner-poll routine at 0x0307D5FA. Once armed, the
registration persists (RAM vector table + NVIC enable; no disarm path
found), so in a session where the BT window was already visited the
replica's banner poll would work even without re-arming, but it
cannot rely on that.

---

## Summary

| # | Item | Verdict |
|---|---|---|
| 1 | post flag 0x123 | NEEDED: triggers resident poll's CL frame + status/1B4 |
| 2 | call 0x03053242 | NEEDED: UART3 115200 re-init + enable + RX IRQ arm |
| 3a | write 0x0300416C = 1 | NEEDED: one-shot enable for item 1's CL frame |
| 3b | write 0x0300416E = 0 | BOOKKEEPING: reset of a countdown no nonzero writer was found for |
| 3c | write 0x0300416F = 0 | BOOKKEEPING: supervisor re-syncs this SAVEINFO+0x2D3 shadow itself |
| 4 | call 0x03065772('S') | NEEDED: sends "CS00" command frame to the BT module |
| 5 | copy tick -> 0x03004174 | NEEDED: poll timestamp; starts the 300/400-tick debounce intervals |
| 6 | flag 0x1B2 producer | WINDOW-ARMED: IRQ handler registered only via UART configure, called only by BT-family overlays (81 Init / 21 / 81 / 1); persists once armed |
