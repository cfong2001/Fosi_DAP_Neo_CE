# DAC error-counter fix: reset on success

Patch spec: `dac_fix.patch.json` (two edits, module 0, code region).
Framework form: `dac_fix_1_branch.patch` + `dac_fix_2_cave.patch`.
Verification: `verify_dac_fix.py`; patched copy `DP3_V137_dacfix.img`.
All work offline against stock `DP3_V137.img` (SHA-256
`fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`);
the stock image is never modified.

## 1. The bug, traced

The DAC register API is `dac_write(map, value)` at `0x03060c4c` and
`dac_read(map, &out)` at `0x03060d28` (Phase 1: `analysis/dac_audio_path.md`).
Both consult a small state block based at `0x0300411d` (module 0
initialized data, offset `0x11d`; the whole block is zero at boot).
The byte at **`0x0300411e`** (`[base + 1]`) is the error counter.

Complete access map for that byte. Provenance: an image-wide scan finds
the word `0x0300411d` exactly three times in the entire image, all of
them literal pools in module 0 (`0x030519a4`, `0x03051ab0`,
`0x03060fac`); a movw/movt pair-construction scan over all 82 modules
finds zero hits, so no other code can hold the address. Every use:

| Access | Site | Evidence |
|---|---|---|
| Gate (read) | `dac_write` `0x03060cf0`: `ldrb r0, [r5, #1]; cmp r0, #2; bhs 0x03060d22` | §2 listing |
| Gate (read) | `dac_read` `0x03060d48`: `ldrb r0, [r0, #1]; cmp r0, #2; bhs 0x03060d88` | §2 listing |
| Increment (write) | `dac_write` `0x03060d16..0x03060d1a`, only when the transfer function `0x03060622` returns nonzero | §2 listing |
| Reset (write 0) | DAC start `0x03051a4e`: `strb r0, [r1, #1]` with `r0 = 0` (also zeroes +2, +3) | below |
| none | The clock-config function at `0x030515c2` loads the same base but touches only `[+4]`/`[+5]` (a last-rate cache); the function at `0x03060d9c` writes `[+3]` (mode state). Neither touches `+1`. | scan output |

The DAC-start reset, for reference. `0x03051a46` is the common DAC
start that codec open calls (`0x03089ef0`), guarded by the per-session
byte at `[0x03023125]`:

```
03051a46: ldr      r1, [pc, #0x68]   ; r1 = 0x0300411d
03051a48: push     {r4, lr}
03051a4a: movs     r0, #0
03051a4c: strb     r0, [r1, #3]
03051a4e: strb     r0, [r1, #1]      ; counter = 0
03051a50: strb     r0, [r1, #2]
03051a52: movs     r1, #0x1f
03051a54: mov.w    r0, #0xb0000
03051a58: bl       #0x3060c4c       ; dac_write(0x0B0000, 0x1F)
...
03051a80: bl       #0x305175e       ; full CS43198 init
```

### Counter semantics (exact)

- **Unit:** one count per failed `dac_write` *transaction* (the 5-byte
  I2C write), regardless of which register it targeted. `dac_read`
  never increments. Its disassembly ignores both transfer return
  values; it only obeys the gate.
- **Not saturating, never decremented:** `adds r0, r0, #1; strb`
  (byte arithmetic; the gate trips at 2, long before wrap matters).
- **Reset only at DAC start**, which runs once per playback session
  (guard byte; track changes do not re-run it; see
  `analysis/gapless.md` §2).

So the Phase 1 wording stands with one refinement: the counter is not
lifetime-per-boot, it is **lifetime-per-playback-session**, and within
a session it only ever goes up. Two transient I2C errors at any point
in a session (a volume change is a `dac_write`; sessions are long)
push it to 2, and from then on *every* `dac_write` and `dac_read` is
silently skipped: volume, balance, and any later DAC configuration
are frozen until the user fully stops playback (or reboots). On the
disabled path `dac_write` also returns whatever `r4` held at
entry (the function never sets it there), so callers cannot even
detect the failure from the return value.

## 2. Stock disassembly (the tail of `dac_write`)

```
03060cee: ldr      r5, [pc, #0x2bc]   ; r5 = 0x0300411d
03060cf0: ldrb     r0, [r5, #1]       ; counter
03060cf2: cmp      r0, #2
03060cf4: bhs      #0x3060d22         ; >= 2: skip everything, return
...
03060cfe: bl       #0x306021c         ; bus select (0, 0x66, 400)
03060d0e: bl       #0x3060622         ; transfer; result in r0 (0 = ok)
03060d12: movs     r4, r0             ; r4 = result (also sets Z)
03060d14: beq      #0x3060d1c         ; success -> tail
03060d16: ldrb     r0, [r5, #1]       ; failure:
03060d18: adds     r0, r0, #1         ;   counter++
03060d1a: strb     r0, [r5, #1]       ;
03060d1c: movs     r0, #0             ; both paths join:
03060d1e: bl       #0x306043a         ; bus release (r0 = bus index!)
03060d22: add      sp, #0x14
03060d24: uxtb     r0, r4
03060d26: pop      {r4, r5, pc}
```

## 3. Fix design

**Chosen shape (a): reset the counter on a successful `dac_write`.**
The counter then counts *consecutive* failures. Two consecutive
failures still disable DAC control (the stock protection against a
genuinely dead DAC is preserved), but any success re-arms it, so
isolated transients can never accumulate into a lockout.

Two simpler-looking placements were considered and rejected on
evidence:

1. **Replace `movs r0, #0` at `0x03060d1c` with `strb r0, [r5, #1]`.**
   Unsafe: the failure path *falls through* into `0x03060d1c` with
   `r0` = the just-incremented counter, and the next instruction is
   `bl 0x0306043a`, the bus-release function, whose `r0` is a bus
   index (`cmp r0, #9; bhs; tbb [pc, r0]`, a per-bus switch; case 0
   is the I2C0/GPIO2.10-11 release). On a failure the stock `movs`
   is what guarantees `release(0)`. The replacement would call it
   with 1 or 2 and release the wrong bus.
2. **Re-lay the tail in place.** Success needs a store plus a branch
   around the 6-byte failure block; failure needs load/add/store;
   both need `r0 = 0` at the `bl`. Minimum 18 bytes against the 16
   available before the `bl`. Does not fit.

**Construction (2 edits, 6 bytes of patch space, 5 bytes change):**

1. `0x03060d14`: `beq 0x03060d1c` (`02 d0`) → `beq 0x03060d8e`
   (`3b d0`). Same condition (Z set by the stock `movs r4, r0`),
   same fall-through; only the success target moves. (The second
   byte is unchanged, so the file diff here is 1 byte.)
2. Trampoline at `0x03060d8e`, in the alignment padding after
   `dac_read`:

   ```
   03060d8e: strb     r0, [r5, #1]     ; r0 == 0 here -> counter = 0
   03060d90: b        #0x3060d1c       ; rejoin stock tail
   ```

   Entry invariants come from stock itself: the branch is taken only
   when the transfer returned 0 (`r0` is still that 0; `movs r4, r0`
   does not modify it), and `r5` still holds `0x0300411d`, loaded at
   `0x03060cee` and preserved across both bus calls. The stock
   increment block at `0x03060d16` relies on exactly that invariant.
   The trampoline modifies no register and no flags; the rejoined
   `movs r0, #0` restores the stock flag state before the release
   call, so the failure path, the gate path, and the return value
   (`r4`) are bit-for-bit stock behaviour.

**Cave safety.** `0x03060d8e` lies in a 14-byte run of `bx lr`
filler (`0x03060d8e..0x03060d9b`) between `dac_read`'s epilogue and
the next function. An exhaustive reference scan of all 82 modules
(every BL/B.W target and every literal word) shows **zero references
to `0x03060d8e..0x03060d96`**, and no fall-through reaches it
(`dac_read` ends in `pop {r4, r5, r6, pc}`). The run's last two
stubs, `0x03060d98` and `0x03060d9a`, are referenced as no-op
return targets by modules 11 and 61; they are left byte-identical
(verified in §5). This is the nanitecfw code-cave technique, with
the reference scan as the safety case.

**`dac_read` is deliberately untouched.** It never increments the
counter, so it cannot trip the gate on its own; once any write
succeeds, its gate is re-armed by this patch.

Encodings were hand-derived and independently reproduced by
`rz-asm` assembled at the target addresses:
`beq 0x03060d8e` @`0x03060d14` = `3bd0`;
`strb r0, [r5, #1]` = `6870`; `b 0x03060d1c` @`0x03060d90` = `c4e7`.
(Control check: `rz-asm` decodes the stock `02d0` at `0x03060d14`
as `beq 0x3060d1c`, as expected.)

## 4. Patched disassembly

`dac_write` tail, patched (Capstone on the combined image):

```
03060d0e: fff788fc   bl       #0x3060622
03060d12: 0400       movs     r4, r0
03060d14: 3bd0       beq      #0x3060d8e     ; success -> trampoline
03060d16: 6878       ldrb     r0, [r5, #1]   ; failure path: unchanged
03060d18: 401c       adds     r0, r0, #1
03060d1a: 6870       strb     r0, [r5, #1]
03060d1c: 0020       movs     r0, #0         ; tail: unchanged
03060d1e: fff78cfb   bl       #0x306043a
03060d22: 05b0       add      sp, #0x14
03060d24: e0b2       uxtb     r0, r4
03060d26: 30bd       pop      {r4, r5, pc}
```

Trampoline and its neighbourhood, patched:

```
03060d88: 2878       ldrb     r0, [r5]       ; dac_read epilogue
03060d8a: 04b0       add      sp, #0x10
03060d8c: 70bd       pop      {r4, r5, r6, pc}
03060d8e: 6870       strb     r0, [r5, #1]   ; NEW: counter = 0
03060d90: c4e7       b        #0x3060d1c     ; NEW: rejoin tail
03060d92: 7047       bx       lr             ; filler, unchanged
03060d94: 7047       bx       lr
03060d96: 7047       bx       lr
03060d98: 7047       bx       lr             ; referenced stub, unchanged
03060d9a: 7047       bx       lr             ; referenced stub, unchanged
03060d9c: 70b5       push     {r4, r5, r6, lr}  ; next function
```

## 5. Verification (offline, `verify_dac_fix.py`)

- Each edit applied **alone** through `firmware_patch.patch()` from
  pristine stock: expect precondition, module boundary check, and
  `validate()` all pass (file offsets `0x3a3c0` and `0x3a43a`).
- Combined image (edit 1 via the patcher; edit 2 via the patcher's
  own offset resolution, then its mirror-sync + trailer-CRC
  finalization): passes `firmware_patch.validate()`.
- Byte diff vs stock is exactly **9 bytes**: `0x3a3c0` (branch byte),
  `0x3a43a..0x3a43d` (trampoline), `0xd00000..0xd00003` (trailer
  CRC). The header-mirror region is untouched (no date change in
  this isolated build; the framework stamps stock+1 on integration).
- Patched-copy disassembly asserts: branch target `0x03060d8e`;
  trampoline decodes as designed; filler stubs `0x03060d92..`
  `0x03060d9a` still `bx lr`.
- Patched copy: `DP3_V137_dacfix.img`, SHA-256
  `6682961a51bd390fa1d1a4c2d24740bc2b84b55500ee41b586d819fd632e4af0`.

## 6. Risk note

- **Return-convention inversion** (0 = failure) would invert the
  fix's effect. Ruled out by stock's own structure: the stock code
  skips its increment block on the zero result. The patch rides the
  same success signal stock already trusts.
- **`r5` liveness** is the patch's one real assumption, and it is
  stock's own: the increment block at `0x03060d16` dereferences
  `r5` after the identical calls. If a bus callee violated the
  callee-saved convention, stock would already corrupt the counter.
- **Hidden cave entry:** a computed jump into `0x03060d8e` from
  outside the static scan's view would now execute a store through
  an arbitrary `r5`. The scan covered all branch targets and
  literals in all 82 modules; residual risk is the standard cave
  risk of this patch technique, accepted framework-wide.
- **Phase E catch:** on hardware, the success path is
  instruction-identical except one added store of 0, so the
  regression test is behavioural identity (full DAC init, volume
  and balance sweeps, `dac_read` log read-backs), plus the targeted
  check that DAC control survives long sessions with heavy volume
  activity (the stock lockout scenario). The dual-slot discipline
  keeps stock one header-corruption away throughout.
