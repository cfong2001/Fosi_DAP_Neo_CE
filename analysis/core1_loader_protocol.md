# Core-1 loader and inter-core protocol: Fosi DAP Neo (DP3_V137)

All addresses are execution addresses. "Proven" = read directly from the
disassembly cited. "Likely" = inference from proven pieces, labelled as such.

## 0. Headline verdict: the loader

**The decoder image is fully re-copied (code + data, BSS zeroed) and core 1 is
reset on EVERY codec-open invocation, including same-codec track changes.
There is no loaded-codec cache check anywhere in the chain.** (Proven, §1–§2.)

Chain, all in module 33 unless noted:

```
framework vtable open 0x03089e2e (codec open)
  → self-dispatch msg 0xe5 via dispatcher 0x03089c86 (case at 0x03089cd2)
  → load-and-start fn 0x03088d9c        (5 callers in mod 33, all open paths)
  → per-codec dispatcher 0x0308886e     (TBB on codec id at [0x0304b4d4], ids 0–9)
  → loader 0x03067870(module, 7)        (module 0; flags 7 = code+data+BSS)
  → reset/wait fn 0x0306cb2c(decoder module no.)
```

In fn 0x03088d9c the call to 0x0308886e at 0x03088e64 is unconditional: the
only earlier exit is an error path (0x0308bfbc()+1 == 0 → post event 0x56,
return 4). No instruction in 0x03088d9c, 0x0308886e, or codec open 0x03089e2e
compares the requested codec id against a stored "currently loaded" value.
The codec id is re-read from [0x0304b4d4] on every call (0x0308886e). The one
per-open state byte, [0x03023151], is *written* 0xff at 0x03088da4, never
compared. Consequence for gapless: a same-codec advance pays the full
image copy (32,888–117,376 bytes from internal storage) + core-1 reset +
boot handshake every track, not just on codec change.

## 1. The generic module loader (module 0)

0x03067870(module_index, flags) → tail-calls 0x0306777a. (Proven)

0x0306777a(module r6, flags r4):

1. Takes semaphore via 0x0306660a.
2. `fp = [0x0302327c]`, runtime pointer to the firmware image base on
   device 3 (the slot base; set at boot, not a static literal).
3. Reads the 512-byte package header from device selector 0x00030000 via
   block-read 0x03067510 into a stack buffer (0x03067794–0x0306779c).
   r5 = first word of the header buffer.
4. Computes the record address `header + 4 + module_index*32` and reads the
   32-byte module record the same way (0x030677a6–0x030677b6).
5. Record fields (same layout as the package table): +0 code_load,
   +4 code_exec, +8 code_len, +0xc data_load, +0x10 data_exec,
   +0x14 data_len, +0x18 bss_exec, +0x1c bss_len, loaded by the two `ldm`
   at 0x030677bc/0x030677c0.
6. flags bit 0 (1): copy code, `0x0306771e(src = image_base + (code_load − r5),
   dst = code_exec, len = code_len)` (0x030677ca–0x030677d2). This is the
   package formula `file_offset = load − load_base + 0x200` in device units;
   0x0306771e is the chunked storage→RAM copy loop.
7. flags bit 1 (2): copy data the same way (data_load/data_exec/data_len)
   (0x030677dc–0x030677ea).
8. flags bit 2 (4): zero BSS, `0x03054e66(bss_exec, …, bss_len)`
   (0x030677f4–0x030677f8). (The decoder also zeroes its own BSS at boot;
   both happen.)
9. Releases the semaphore (0x03066662).

A twin at 0x0306780a performs the same operation against the other slot
base (argument packing differs; same header cell 0x0302327c is read;
which slot each variant addresses is **unproven**).

This one loader serves everything: system overlays (e.g. module 34 loaded
at every codec start, 0x03088db4: `0x03067870(0x22, 7)`), per-codec
interface overlays, and the decoder images.

## 2. Per-codec load sequence (module 33)

Codec-id dispatcher 0x0308886e: reads codec id from [0x0304b4d4];
if ≥ 10, returns; else TBB with 10 cases (ids 0–9). Each case (proven for
id 0, sampled for the rest):

1. Loads a small per-codec interface overlay via 0x03067870(stub, 7)
   (stub modules are in the 41–52 range; the 0x0308c694 stub family).
2. Semaphore/GPIO conditioning (0x030525ac / 0x0305261c calls).
3. Calls 0x0306cb2c(decoder_module), the reset-and-start fn (§3),
   which itself first calls 0x03067870(decoder_module, 7).

Sampled (stub → decoder) pairs from the case bodies: id 0: 41 → 71 (MP3)
(0x0308888c / 0x030888b2); → 72 (WMA) (reset arg at 0x0308890e);
51 → 74 (WAV) (0x030889da / 0x030889e0); 50 → 73 (AAC)
(0x03088a2e / 0x03088a34); 52 → 75 (OGG) (reset arg at 0x03088ac2).
Case layout order in the binary is scrambled relative to TBB order.
**Likely:** ids 0–9 map 1:1 onto decoder modules 71–80 in catalog order
(MP3, WMA, AAC, WAV, OGG, FLAC, ALAC, APE, DSD-DFF, DSD-DSF); the full
10-row table was not extracted case-by-case.

Load-and-start fn 0x03088d9c (called from dispatcher msg 0xe5 and four
other module-33 open paths: 0x0308914c, 0x030891aa, 0x030892b6, 0x03089346):

- [0x03023151] ← 0xff (0x03088da4); event-flag op 0x030670e0(4, 0xc8).
- 0x03067870(0x22, 7) loads module 34 (0x03088db4).
- Calls 0x0308c284; configures MU logical channels 0x1a/0x1b is done later
  in codec open; here it configures channel 0x0e helpers
  (0x03056d8e/0x03056c44/0x030664e8/0x03056c88 at 0x03088dfc–0x03088e12).
- File-info fixups (fileinfo 0x03023980 +0x34/+0x44), post event 0xf0
  (0x03088e60), then bl 0x0308886e (0x03088e64), the load itself.
- Logs via 0x0306d8f0 with the format string at ≈0x03089234
  ('audio codec open success.'), clears state halfword [0x03023926],
  calls helpers 0x0308875a / 0x030886b8 / 0x03088588, copies the volume
  byte (SAVEINFO +0x12) into the audio state struct at 0x0304af10+0x10,
  runs DAC-side calls 0x0305168a / 0x03060d9c / 0x03060d98, and sets up
  the PCM ring via 0x0308abe4([0x03023928], [0x03023938]).

## 3. Reset-and-start, and the boot handshake (module 0)

0x0306cb2c(arg = decoder module number) (0x0306cb2c–0x0306cb8c, proven):

1. `0x030525ac(2, 1)`; `0x0305261c(0x32, 1)`, assert control line 0x32.
2. `0x03067870(arg, 7)`, load the decoder image (§1).
3. `delay_ms(5)` (0x03064944).
4. `memcpy(0x03054e34)(dst = 0x01020000, src = 0x030064e0, len = 0x90)`,
   writes a 144-byte runtime-built parameter page at the base of the
   decoder data window. Source 0x030064e0 is beyond module 0's data_len:
   a BSS buffer filled at runtime (contents not decoded).
5. [0x03004138] ← 0 (the decoder-ready word).
6. `0x0305261c(0x32, 0)`, deassert line 0x32. Steps 1+6 form a pulse on
   line 0x32 around the copy; **likely** the core-1 reset/clock-gate line.
7. Poll [0x03004138] until nonzero, timeout 0x30d40 (200,000) iterations;
   each iteration calls 0x030611e0 (clock helper), 0x030531f6 (**likely**
   the MU message pump that lets the ready message land), delay
   0x03064920(1).

Ready signal: the decoder, once booted, sends MU channel-0 cmd 1;
module 0's channel-0 receiver 0x0306cb8e acks (mask 1), reads the cmd
via 0x0306cfa0(0,0): cmd 1 → [0x03004138] = 1; cmd 3 → [0x0300413c] = 1.

Second handshake: 0x03066b80. If [0x03004138] ≠ 0: clears
[0x0300413c], sends system→decoder channel-0 cmd 2, param 0
(0x0306d0d8 / 0x0306d0ac), waits for [0x0300413c] (the decoder's cmd-3
reply; decoder side fn 0x01000820 sends it), timeout 0xc350 (50,000),
then calls 0x030600f2(0..4) (five enables, **likely** DMA/audio-path
starts). 0x03066bee: sends channel-0 cmd 4 (no wait), then
0x03060130(0..5), the counterpart stops. Cmd 2's semantics beyond the
handshake and cmd 4's exact meaning are **unproven** (4 sits on the stop
path by symmetry).

Decoder boot (from prior verified work, FLAC): two vector tables;
table-1 reset trampoline zeroes registers, disables interrupts, sets
VTOR = 0x01022000, branches to table-2 reset; C startup zeroes
0x23550 bytes of BSS from 0x010224bc, configures logical channels
0x1a/0x1b on the message unit, then the main loop dispatches on the
command word at 0x0102221c. Core 1 executes its code window in a local
0-based offset view; data addresses 0x0102xxxx are identical for both
cores.

## 4. Shared memory and the message unit

Message unit (MU): base 0x40110000 in both cores' views, per-unit
stride 0x50. The same driver library is compiled into module 0
(0x0306cf28–0x0306d110) and every decoder (FLAC copy 0x01004e80–0x0100505e).
Register groups per unit (ch = 0..3, stride 8 within a group):

| Offset | Direction | Accessors (system / decoder) |
|---|---|---|
| +0x00, +0x28 | control/status A/B (RMW bit set/clear) | 0x0306cf28… / 0x01004ec4 |
| +0x08+8·ch | sys→dec **cmd** | write 0x0306d0d8 / read 0x01004f80 |
| +0x0c+8·ch | sys→dec **param** | write 0x0306d0ac / read 0x01004f54 |
| +0x2c | interrupt/status clear (ack) | write 0x0306cf90 / 0x01004eec; mask = 1<<ch |
| +0x30+8·ch | dec→sys **cmd** | read 0x0306cfa0 / write 0x01004fb0 |
| +0x34+8·ch | dec→sys **param** | read 0x0306cfcc / write 0x01004fdc |

Channel allocation (proven from the receivers): ch 0 = boot/handshake
(module 0), ch 1 = decoder status/info → module 33 (receiver
0x03089416) and module 61 (0x03081522), ch 2 = HifiFile RPC
(module 33 server 0x030895da; module 61 notification reader 0x0308158e),
ch 3 = a value-query service in module 0 (receiver 0x0306cbb4:
cmd 5 → returns the param).

Shared SRAM: the decoder data window 0x01020000–0x01042000 is the
shared region. The system writes it directly (parameter page at
0x01020000, §3; the image data copy lands at 0x01022000+), the decoder's
own data/BSS live there (command word 0x0102221c, control struct
0x01022290, HifiFile cells §5), and the system dereferences
decoder-supplied pointers into it (info-struct case, §6). The system-side
control block 0x0304ad70 is system-private: no decoder contains
0x0304xxxx literals; its core-1-visible counterpart is the decoder's own
control struct at 0x01022290 + command word 0x0102221c. The 0x60082xxx
base from the brief is the decoders' audio/control MMIO view, not the
mailbox; the mailbox is 0x40110000.

## 5. HifiFile RPC

Transport: MU channel 2, unit 0. Request = cmd in the cmd register +
request-block pointer in the param register. Blocks live in decoder
SRAM; the server dereferences the pointer directly (no system module
contains literals for the block addresses; proven by scan).

### Client side (module 76 FLAC; module 74 WAV identical layout, strings
at the same offsets)

Shared cells (decoder data): flag/status base 0x0102222c (+0 =
request-complete flag, +1 = RPC-initialised flag), handle table
0x01022234 (word per handle), result-status byte 0x01022298.

Stub pattern (Seek stub 0x010002f4 read in full; others identical):
store args into the block; clear flag [0x0102222c]; send cmd
(0x01004fb0(cmd, 0, 2)); send block pointer (0x01004fdc(block, 0, 2));
poll the flag with timeout 0x002dc6c0 iterations, delay
0x01000b54(1) each; on timeout print the op's timeout string via
0x0100095e and fall through; return the byte at [0x01022298].

| Op | Client fn | Cmd | Request block | Block layout | Post-completion |
|---|---|---|---|---|---|
| Seek | 0x010002f4 | 0x69 | 0x01022254 | +0 arg0 (u32), +4 arg1 (u32), +8 handle (byte) | handle_table[handle] = block+0 |
| Read | 0x01000350 | 0x6b | 0x01022260 | same shape; first requires flag [0x0102222d] = 1 | handle_table[handle] = block+4 |
| Write | 0x010003b6 | 0x6d | 0x0102226c | +0/+4/+8 u32 args, +0xc byte arg | none |
| Close | 0x0100040e | 0x73 | none, param = handle value | none | returns status byte |

Timeout strings: Open 0x010004ec, Seek 0x0100510, Read 0x010052c,
Write 0x0100548, Close 0x0100564 ('HifiFileXxx: timeout!!').
A 7-pointer file-ops vtable is installed at 0x010220f4 by fn
0x01000456, which also sets the initialised flag [0x0102222d] = 1. The
stubs are reached through it (no direct BL callers for Open/Write/Close).

Open's send half was not located. The wait half is fn 0x010002a8
(polls the flag; 'HifiFileOpen' string). Two fire-and-forget ch2 sends in
the decoder's open-path code are candidates by position: cmd 0x66
at 0x0100184c (after buffer setup with size 0x15c00) and cmd 0x68
at 0x010018a2 (right after the vtable install call). On the server both
0x66 and 0x68 are real cases (§5.1), so one of them is very likely the
Open request; which one is **unproven**.

### 5.1 Server side (module 33, fn 0x030895da)

Reads cmd (0x0306cfa0(0,2)) and param = block pointer (0x0306cfcc(0,2)),
acks with mask 4, dispatches TBB on (cmd − 0x66), valid 0x66–0x75
(table parsed at 0x03089606). Each request case stores the block pointer
in the control block (+0x74/+0x78/+0x7c slots), performs the FS call,
writes the result word back into the block, and replies on ch2 with
cmd = request + 1 (send 0x0306d0d8, param 0x0306d0ac):

| Cmd | Case | FS primitive called | Result written | Reply |
|---|---|---|---|---|
| 0x69 Seek | 0x03089616 | 0x030594a0([blk+0], byte[blk+4], sbyte[blk+8]) | [blk+0] = folder table 0x0307ab68[handle·0x180]+0x20 | 0x6a |
| 0x6b Read | 0x03089656 | 0x03058fa8 (file-read primitive; same fn the updater uses) | [blk+4] = folder-derived word | 0x6c |
| 0x6d Write | 0x03089696 | 0x0305ca1c | none | 0x6e |
| 0x6f | 0x0308971c | reads folder table [idx]+0x20 | none | 0x70 |
| 0x71 | 0x03089744 | reads folder table [idx]+0x10 | none | 0x72 |
| 0x73 Close | 0x0308976c | 0x03058e8e (close-class) | none | 0x74 |
| 0x66 / 0x75 | 0x0308978c | notification sink: records a value at [ctlblk+0x70], calls state helper 0x0308b724 twice with 0x030531f6/0x030611e0 polling | none | none |

0x6f/0x71 are info queries distinguished by which folder-record field
(+0x20 vs +0x10) they return, field semantics **unproven** (candidates:
file size / start cluster). The reply presumably triggers the decoder's
own ch2 receive path, which sets the completion flag [0x0102222c] and
the status byte [0x01022298]; that decoder-side handler was not
isolated (labelled likely, §7).

Module 61 also reads ch2 (fn 0x0308158e) but only for the notification
cmds 0x68/0xd3, which set byte [0x03025994] = 1; it is not the file
server. (0x68 therefore appears both as a decoder→system notification
consumed by module 61 and in the HifiFile command range. The two
readers coexist on the channel; which one services a given 0x68 is
**unproven**.)

## 6. Decoder control command set

### System → decoder
- MU ch0: cmd 2 = readiness query (expects cmd-3 reply, §3);
  cmd 4 = stop-class command on the 0x03066bee path (no handshake).
- MU ch2: cmd 0x65 = "report info", sent by fn 0x03088824 with
  param = 0x0304b4ac (ctlblk +0x73c); completion is polled on word
  [ctlblk +0x70], timeout 0x004c4b40. The decoder's answer path is the
  0x66 notification case (§5.1), **likely** the same handshake.
- Shared-memory command word at 0x0102221c + control struct at
  0x01022290 (+0 = flag byte, +0xc = one-shot notify field): the
  decoder main loop (FLAC, from 0x0100156c) sleeps in WFI while both are
  zero, then dispatches the command word via TBB at 0x0100159a,
  values 0–14 (15 commands). Who writes the command word (system
  core directly through the shared window vs an MU side path) is
  **unproven**; the per-case names are **unproven** (see §7).

### Decoder → system
- MU ch0: cmd 1 = booted/ready; cmd 3 = reply to cmd 2.
- MU ch1 status messages (sent from decoder main-loop cases):
  cmd 2 (0x010015c8, 0x01001604), 3 (0x01001720), 6 + param
  (0x0100174e), 5 + param (0x01001776), 0xc (0x010017a8), 1
  (0x010017b4), 0xe + param (0x010017cc).
- Module 33 ch1 receiver 0x03089416: reads cmd/param, stores the pair
  at [ctlblk +0x4c], acks mask 2, TBB-dispatches ids 2–0x12 (17
  cases). Case cmd 2: sets [ctlblk +0x6c] = 1 and [ctlblk +0x5c] = 1.
  The info case (0x03089460) copies a decoder-supplied struct (param =
  pointer into the shared window) into 0x0304b170+0x30c / the
  0x0304b47c area and sets [0x0304b47c+0x24] = 1. This is the
  stream-info return path (the FreqChange-adjacent flow).

### FreqChange
No discrete message named or identifiable as "FreqChange" was isolated
on either side (**unproven**). Proven facts around it: codec open sets
the I2S to a fixed 48000 (0x03055dcc(1, 2, 0xbb80) at 0x03089f06); the
decoder-info struct at 0x030368d8 is rebuilt at every codec open
from SAVEINFO bytes +0x61, +0x63 and the EQ coefficient table indexed
by (SAVEINFO+0x68 − 8) at 0x0304aef4 (0x0308a01a–0x0308a036); the actual
per-stream rate travels back through the ch1 info exchange above.
**Likely:** rate change is effected decoder-internally from the opened
file's parameters and only *reported* to the system, not commanded by a
dedicated FreqChange message.

### Shared fields at codec open (proven, module 33 0x03089e2e)
- Control block 0x0304ad70: +2 ← 0 (halfword), +0x30 ← 0, +8 ← pointer
  to the 0x030368d8 info struct, +0x44 ← target position
  ([0x03023298] mod fileinfo+0), +0x48 ← 1 = play-enable (0x0308a126).
- Position: the open path polls the decoder-reported position word at
  SAVEINFO +0x64 against the target (delay_ms(15), ≤ 200 iterations,
  0x0308a0ee–0x0308a118), then writes SAVEINFO+0x64 = target.
- File-info struct 0x03023980: +0xf2 = codec/source code (0x63 / 6
  special-cased), +0xc/+0x10 filled for native codecs.
- After setup: logical channels 0x1a/0x1b are re-registered with the MU
  helpers (0x030664e8 / 0x03056d8e / ack / 0x0306cf54 / 0x03056c88),
  then codec open re-enters its own dispatcher with msg 0xe5.

## 7. What remains unproven

1. The exact per-case names of the decoder command-word TBB (values
   0–14 at 0x0100159a), play/pause/seek/EQ assignments not decoded.
2. Which ch2 cmd (0x66 or 0x68) is HifiFileOpen's send; Open has no
   located client stub, only the wait fn 0x010002a8.
3. The decoder-side ch2 receive handler that sets the HifiFile
   completion flag [0x0102222c] and status byte [0x01022298] on reply.
4. Who writes the decoder command word 0x0102221c (direct shared-memory
   write by the system core is likely but not instruction-proven).
5. Semantics of MU ch0 cmd 4, and of the 0x030600f2/0x03060130 enable/
   stop groups (0..4 / 0..5).
6. Contents of the 144-byte parameter page copied to 0x01020000
   (source BSS buffer at 0x030064e0 is runtime-built).
7. Folder-record field semantics behind server cmds 0x6f/0x71
   (table 0x0307ab68, fields +0x10/+0x20) and the result words the Seek/
   Read cases write back.
8. The full 10-row codec-id → (stub, decoder) mapping (5 rows sampled).
9. Which slot variant the twin loader 0x0306780a serves.
10. Whether cmd 0x68 on ch2 is serviced by module 61, module 33, or
    both (two readers exist).
11. FreqChange as a discrete message: not found; the rate path in §6 is
    the current best model.
12. The 0x030531f6 poll helper called in every wait loop (modelled as
    the MU message pump; body not read).

## Helper scripts (this folder)

- `mdis2.py`: per-module disassembler (skipdata + module-0 literal
  fallback); `work/core1/mdis2.py MODULE START LENGTH`.
- `blrange.py` / `blsites.py`: raw-halfword BL target scans (reliable;
  capstone-independent).
- `litscan.py`: literal-word scan across all extracted modules.
- `adrscan.py`: LDR-literal/ADR references within one module.
- `movscan.py`: movt high-half construction scan.
- `callsites.py`: capstone call-site finder (unreliable negatives;
  superseded by blrange/blsites).
