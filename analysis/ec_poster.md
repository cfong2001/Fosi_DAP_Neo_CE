# Who posts event 0xEC: RESOLVED

**Verdict (proven):** Event `0xEC` (the decode-finished event consumed by
module 33's playback task) is posted by a playback monitor function in
module 0 at `0x03064F7E`, from exactly two call sites:
`0x0306500C` and `0x03065032`. The monitor is not called directly by
anyone: module 33 registers it as the callback for message-unit
channel `0xE` (14) during the codec open/start chain, so it runs when
the decoder core signals on channel 14. It cross-checks the resident
codec's playback status and, when it confirms end-of-stream, finalizes
playback state and posts `0xEC`. It is the only producer: every post
mechanism in the image was exhaustively scanned (§5).

All addresses are system-core exec addresses unless marked core-1.
Labels: **proven** = instruction bytes cited; **likely** = strong
structural inference.

---

## 1. The event mechanism (proven)

Events are bits in a bitmap at `0x03023CF8` (reset-preserved SRAM,
the same bitmap that holds flags 0x18B/0x18C). Three primitives in
module 0, all reading the base from the shared literal at `0x030672B8`:

```
; post-event  0x0306723C(r0 = id):  bitmap[id>>5] |= 1 << (id & 0x1F)
0306723c  ldr      r2, [pc, #0x78]   ; = 0x03023cf8
0306723e  lsrs     r1, r0, #5
03067240  and      r0, r0, #0x1f
03067244  ldr.w    r3, [r2, r1, lsl #2]
03067248  mov.w    ip, #1
0306724c  lsl.w    r0, ip, r0
03067250  orrs     r0, r3
03067252  str.w    r0, [r2, r1, lsl #2]
03067256  bx       lr
; test-event  0x03067258(r0 = id):  returns 1 and CLEARS the bit if set, else 0
; clear-event 0x0306727E(r0 = id):  clears the bit
```

Event `0xEC` = 236 → word 7 (at `0x03023D14`), bit 12, mask 0x1000.

## 2. The consumer (proven)

Module 33 playback task `0x0308A1CA`, in its poll loop:

```
0308a504  movs     r0, #0xec
0308a506  bl       #0x3067258        ; test-and-clear(0xEC)
0308a50a  cbz      r0, #0x308a562    ; not set -> keep polling
          ... repeat-one test via [0x0304b47c+0x2c], folder bounds,
              fall through to open-prep 0x03089da6 / post 0xeb ...
```

This is the only test of `0xEC` in the image (scan of all
`0x03067258` call sites with r0 provenance: the only r0=0xEC test is
this one).

## 3. The producer: module 0 monitor `0x03064F7E` (proven)

### 3.1 How it is invoked: registered MU channel-0xE callback

No instruction anywhere BLs to `0x03064F7E` (all-module BL scan: zero
callers). Its address (with Thumb bit, `0x03064F7F`) appears as a
literal exactly twice in the image, both in module 33, both in the
registration idiom `0x030664E8(channel, fnptr)`, the same helper
Phase 2 saw registering logical channels 0x1A/0x1B at codec open:

```
; site 1, module 33 open chain, preceding function
03088d84  movs     r0, #0xe
03088d86  bl       #0x3056c44        ; channel-14 op
03088d8a  ldr      r1, [pc, #0x68]   ; = 0x03064f7f
03088d8c  movs     r0, #0xe
03088d8e  bl       #0x30664e8        ; register callback(14, monitor)

; site 2, inside fn 0x03088D9C (the per-open loader chain fn)
03088e00  movs     r1, #0xe0
03088e02  movs     r0, #0xe
03088e04  bl       #0x3056c44
03088e08  ldr      r1, [pc, #0x3f8]  ; = 0x03064f7f
03088e0a  movs     r0, #0xe
03088e0c  bl       #0x30664e8        ; register callback(14, monitor)
03088e10  movs     r0, #0xe
03088e12  bl       #0x3056c88        ; channel-14 op
```

So on every codec open/start, module 33 (re)registers the module-0
monitor as the handler for channel 14, flanked by channel-14
open/enable operations (`0x03056C44` / `0x03056C88`).

### 3.2 What the monitor works on

On entry it takes no meaningful arguments; it reads global state:

- `r6 = 0x03023918`, playback state struct: `+0xA` state halfword
  `[0x03023922]`, `+0xE` play-state/end flag halfword `[0x03023926]`
  (the flag the UI polls), `+0x10` PCM ring pointer `[0x03023928]`,
  `+0x14` position word `[0x0302392C]`, `+0x1C` arm flag
  `[0x03023934]`, `+0x20` ring length `[0x03023938]`, `+0x24`
  invocation counter (incremented on every entry).
- `r7 = 0x0304AD78`, decoder control block +8, i.e. a pointer to the
  decoder-info struct at `0x030368D8`.

### 3.3 Trigger logic (proven flow; semantic labels noted)

```
03064f7e  push.w   {r4, r5, r6, r7, r8, lr}
03064f82  ldr      r6, [pc]          ; = 0x03023918
03064f88  ldr      r0, [r6, #0x24]   ; counter++
03064f8e  str      r0, [r6, #0x24]
03064f90  ldrh     r0, [r6, #0xa]    ; state [0x03023922]
03064f94  cmp      r0, #0
03064f96  bne      #0x306507e        ; state != 0 -> tail processing, NO post
```

1. State gate. If `[0x03023922] != 0`, the monitor only does its
   tail work (PCM sample-width processing of the ring via the
   `0x03064E48`/`0x03064EC0` converter family, at `0x030650B6`+) and
   returns. End-of-stream is evaluated only in state 0.
2. End-flag pre-post. If the play-state halfword `[0x03023926]`
   is nonzero: state ← 4 and it posts `0x56` at `0x03064FA6`
   (the advance event the playback task also consumes), then falls
   through to the evaluation below anyway.
3. Codec status query. It calls module 33's stub dispatcher
   `0x0308ABE4` with the PCM ring descriptor (`r0 = 0x03023928`,
   `r1 = 0x03023938`):

   ```
   03064faa  ldr      r1, [pc]        ; = 0x03023938
   03064fac  sub.w    r0, r1, #0x10   ; = 0x03023928
   03064fb0  bl       #0x308abe4
   ; 0x0308abe4: ip = table 0x030489a4[ CurrentCodec [0x0304b4d4] ];
   ;             tail-jump to per-codec stub (0x0308c694 family)
   ;             with r0 = 10 (command 10); returns -1 if codec==0xff
   ```

   Stub command 10's body (TBB case at `0x0308C6FE`, module 41 family)
   is a status query over the codec struct `0x0304B47C`: it reads
   fields `+0x24/+0x28/+0x2C`, can write the ring-length word through
   the caller's pointer, and returns small status codes, including
   an immediate `return 2` when `[struct+0x28] == 1`
   (`0x0308C716`). (This refines Phase 2's tentative "cmd 10 = DMA
   playback start" label: the body reached from the monitor is a
   status getter; the DMA-start profile sits in a different case,
   cmd 8 at `0x0308C6B8`.)
4. End path E1: post at `0x0306500C` (stub query returned 0):

   ```
   03064fc0  folder-table test (table 0x0307ab68, index [0x03004458],
             entry fields +0x10/+0x20, the same table and compare
             module 33's own end handler uses)
   03064fd6  cmp.w    r1, r0, lsr #1
   03064fda  bhi      #0x3064ffc      ; [entry+0x20] > [entry+0x10]/2 -> E1
   03064fdc  ldrb     r0, [0x030232a0+0x61]   ; SAVEINFO+0x61
   03064fe2  cmp      r0, #2 / cmpne r0, #4
   03064fe8  beq      #0x3064ffc      ; SAVEINFO+0x61 in {2,4} -> E1
   ; otherwise -> 0x03064fea variant: same finalize, but posts 0x56
   03064ffc  strh.w   r8, [r6, #0xa]  ; state <- 4
   03065000  ldr      r0, [r6, #0x20] ; ring length
   03065002  lsls     r1, r0, #2
   03065004  ldr      r0, [r6, #0x10] ; ring pointer
   03065006  bl       #0x3054e66      ; fill/silence ring (value 0)
   0306500a  movs     r0, #0xec
   0306500c  bl       #0x306723c      ; POST 0xEC
   03065010  str      r4, [r6, #0x14] ; position [0x0302392c] <- 0
   03065014  pop.w    {r4, r5, r6, r7, r8, pc}
   ```

   So with the stub reporting 0, the monitor posts `0xEC` if the
   folder-table position test passes or the per-stream config
   byte SAVEINFO+0x61 is 2 or 4; in the remaining sub-case it runs the
   same finalize sequence but posts `0x56` instead (shared BL tail at
   `0x0306500C`).
5. End path E2: post at `0x03065032` (stub query returned
   nonzero):

   ```
   03064fb6  ldr      r1, [pc]        ; = 0x03023980 (file-info struct)
   03064fb8  ldr      r2, [r1, #0x44]
   03064fba  cmp      r2, #1
   03064fbc  beq      #0x3065018      ; fileinfo+0x44 == 1 required
   03065018  ldr      r2, [r7]        ; decoder-info struct ptr
   0306501a  ldr      r1, [r1, #0x4c] ; fileinfo+0x4c
   0306501c  ldr      r2, [r2, #4]    ; [infostruct+4]
   0306501e  cmp      r2, r1
   03065020  blo      #0x306503e      ; not reached -> not end
   03065022  strh.w   r8, [r6, #0xa]  ; state <- 4
   03065026  ... bl #0x3054e66        ; silence ring
   03065030  movs     r0, #0xec
   03065032  bl       #0x306723c      ; POST 0xEC
   03065036  str      r4, [r6, #0x14] ; position <- 0
   ```

   I.e. with a nonzero stub status, end is confirmed when the
   file-info mode word `+0x44` equals 1 and the decoder-info struct's
   `+4` word has reached the file-info struct's `+0x4C` word (a
   length/position pair; exact field names unproven).
6. Not-end outcomes. If the stub returned 2, the monitor sets
   the arm flag `[0x03023934] ← 1` and returns without posting
   (`0x0306503E`), a deferred state: end is finalized on a later
   invocation, so the poster is stateful across calls. Otherwise it
   does position bookkeeping (converter `0x03064EC0` against the info
   struct's bits-per-sample word `[info+0x9C]`) and runs a stall
   watchdog: a counter at control-block `+0x14` (`[0x0304AD84]`)
   increments per invocation; when it reaches 4 the monitor posts
   `0x5A` (`0x03065074`) and clears `[0x0304AD8C]`.

Net trigger condition, in one sentence: the monitor runs on a
channel-14 decoder signal; when the playback state halfword is 0 and
the resident codec's status query plus the position/folder checks
agree the stream is exhausted, it sets state 4, silences the PCM
ring, zeroes the position word, and posts 0xEC.

## 4. The decoder-side signal (proven send; routing identity likely)

The decoder programs raise the channel-14 signal from their main
loop. Example: FLAC (module 76), in the shared handler for
command-word values 3/6/7/14 (the stop/finish-class commands; exact
per-value names remain unproven per `core1_loader_protocol.md` §7):

```
010017c0  str      r4, [r6]          ; update decoder control struct
010017c2  bl       #0x1004e0c        ; helper (file/flush class)
010017c6  movs     r2, #1
010017c8  movs     r1, #0
010017ca  movs     r0, #0xe          ; message 0xE = 14
010017cc  bl       #0x1004fb0        ; MU send helper
```

The identity between this decoder-side `0xE` and the system-side
logical channel `0xE` the monitor is registered under is **likely**
(same number, same registration idiom Phase 2 established for
channels 0x1A/0x1B, and the monitor's behaviour is exactly the
consumer such a signal needs), not byte-proven end to end. The MU
demux that routes a decoder message to a registered callback was not
itself reversed in this pass.

## 5. Exhaustiveness: how the space was closed

Scans run over all 82 modules' code and data (scripts:
`work/perf/scan_ec.py`, `resolve_unresolved.py`, `resolve_bw.py`,
`branch_to.py`):

| Mechanism | Result |
|---|---|
| BL → `0x0306723C` (post), r0 provenance resolved for **every** site | Exactly two sites with r0=0xEC: `0x0306500C`, `0x03065032` (both §3). All other sites resolved to other ids (window-local events, 0x27-service idiom, key events, BT 0x1B2/0x1B4/0x1BD, etc.). ~45 initially ambiguous sites were individually resolved (conditional movs, shared tails, branch-source tracing, byte-level `movs` checks). |
| B.W tail-call → post (66 sites) | All resolved; none carries 0xEC. |
| Literal word `0x0306723C` / `0x0306723D` in any code/data | **None**: no function-pointer table, BLX, or veneer path to the post routine exists in the image. |
| Literal word `0x03023CF8` (bitmap base) | Occurs **once** in the image: the primitives' own pool at `0x030672B8`. |
| Literal word `0x03023D14` (bitmap word 7) | **None**: nobody addresses 0xEC's bit directly. |
| Data words == 0xEC in module data segments | None (no message-map table carries it). |
| BL callers of the monitor `0x03064F7E` | None; only the two registration literals (§3.1). |
| Test sites for 0xEC | Only the consumer, §2. |

Residual corners a pattern scan cannot formally exclude, a producer
that *computes* the bitmap base or the post address arithmetically,
or a multi-hop computed dispatch, have no supporting evidence
anywhere in the image, and the identified producer fully accounts
for the event (right semantics, right registration point in the open
chain, right state machine). The core-1 decoders cannot be direct
producers at all: they execute in the `0x01000000` window, cannot
reach the system-core bitmap, and their only path to the system core
is the message unit, whose channel-14 endpoint is the monitor.

Note the contrast with flags 0x18B/0x18C (Phase 2): those genuinely
have no producer in the image. 0xEC looked similar only because its
producer is reached by callback registration rather than by a call,
and because the post sits inside a module-0 monitor rather than in
module 33 near the consumer.

## 6. Consequence for the gapless design

From `analysis/gapless.md` §5: the end event no longer needs a
hypothetical producer. The chain is

```
decoder EOF -> MU ch 14 -> monitor 0x03064F7E (finalize + post)
            -> playback task 0x0308A1CA (repeat/advance) -> open chain
```

Two patch-relevant facts: (1) the monitor silences the PCM ring and
zeroes the position word before posting, so a pre-staged next track
must survive or bypass this finalize step; (2) end confirmation is
*polled through the stub status query inside the monitor*, not
signalled sample-accurately by the DMA, so even with pre-open, the
transition granularity is bounded by when channel 14 fires and the
monitor runs, which is where a gapless patch should hook first
(the monitor's finalize block at `0x03064FFC`/`0x03065022`, or the
registration at `0x03088D8A`/`0x03088E08`).
