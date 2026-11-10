# Tail build: resolver hook and Bluetooth blob composed in the gap tail

> Current build correction: `build_tail.py` now emits a resolver-only
> **tail payload** for `build.py --tail`, not the old full-gap blob or the
> withdrawn `--extension` option. With Arm GNU GCC 14.2.1, binutils 2.44,
> Python and Capstone, run `python3 patches/m3u/tail_build/build_tail.py
> --output /tmp/resolver-tail.bin`. The 1,602-byte output has SHA-256
> `43f5867abaee882171466438e0a8fa0efa3f930b70339064759b993dc9a0dab4`.
> For Bluetooth as well, append two zero alignment bytes and the independently
> generated 436-byte Bluetooth routine at offset 1,604; include patch 0032-tail.
> Include patches 0041/0042 and the module 31 bridge composition with either
> variant. The results below are historical measurements, not device tests.

**Verdict: the full tail composition builds, fits, and passes all three emulation suites.** The resolver hook (410 bytes, both entry points plus the shared serve routine) is written and linked at 0x0307C45C, the trimmed staging layout (1,192 bytes) sits at 0x0307BFB4, and the Bluetooth blob (436 bytes) is relinked at 0x0307C5F8. Total tail use is 2,040 of the 2,044 usable bytes, with 4 bytes spare. The scratch image (live manifest plus patches 0032-tail, 0041, 0042 plus the extension blob) passes `firmware_patch.validate()`, and its diff against the plain live-manifest build is confined to the three patch sites, the extension span, the code length record, and the trailer CRC. Nothing was stacked into the live manifest and nothing was pushed.

Scratch image SHA-256: `fddcc52bfcc9963c4780221159e52474b1ef2e1b035570110dc41bc04147f8c0`.
Baseline (live manifest, same pipeline run) SHA-256: `623214370755053ed69dc53f0c7ae5ec0504bcb3e9ca6f2766cc9e9049101090`. The baseline is not the older pinned unified image: the live tree has moved since that pin (the Vorbis transplant gained its rounding post-step), so the baseline was rebuilt fresh and the confinement measurement is taken against it.
Stock image SHA-256 verified unchanged at the end: `fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`.

## Tail layout

Tail window: 0x0307BFB4..0x0307C7B0 (2,044 usable bytes; 0x0307BFB0 is a live counter word and is not touched). Delivery is the existing extension mechanism: one blob of 11,160 bytes at file offset 0x532C0 (exec 0x03079C14), zeros across the workspace zone, occupants at their tail offsets. Module 0 code length grows 0x29C14 to 0x2C7AC.

| Occupant | Exec range | Bytes | Blob offset |
| --- | --- | --- | --- |
| Staging header | 0x0307BFB4..0x0307BFC3 | 16 | 0x23A0 |
| Staging runs (12 x 50) | 0x0307BFC4..0x0307C21B | 600 | 0x23B0 |
| Staging entries (144 x 4) | 0x0307C21C..0x0307C45B | 576 | 0x2408 |
| Resolver hook code | 0x0307C45C..0x0307C5F5 | 410 | 0x2848 |
| Alignment padding | 0x0307C5F6..0x0307C5F7 | 2 | 0x29E2 |
| Bluetooth blob | 0x0307C5F8..0x0307C7AB | 436 | 0x29E4 |
| Spare | 0x0307C7AC..0x0307C7AF | 4 | 0x2B98 |

The staging area is zeros in the composed blob, so the playlist flag is clear at package load, as the design requires. Header layout is the resolver design's, at the moved base: +0 flag, +1 entry count, +2 position (0xFFFF = none), +4 last served residual, +6 run count, +7..+15 reserved. Caps are the census trim: 12 runs, 144 entries (16 + 600 + 576 = 1,192 bytes).

Hook code, by symbol (source: `src/resolver_hook.S`, GNU as via arm-none-eabi-gcc 13.2.1):

| Symbol | Address | Bytes | Role |
| --- | --- | --- | --- |
| `resolver_hook_primary` | 0x0307C45C | 58 | flag test, discriminator, fallback to 0x03059DB0 |
| `resolver_hook_companion` | 0x0307C496 | 136 | flag, mode and last-run-cluster tests, fallback to 0x0305B2C6 |
| `run_ptr_from_id` | 0x0307C51E | 20 | run id to run pointer (id x 50 + runs base) |
| `serve_common` | 0x0307C532 | 196 | position mapping, descriptor write-out, sentinel |

Budget arithmetic: 1,192 + 410 + 2 + 436 = 2,040 of 2,044. No overflow, and no silent trim was needed: the staging trim to 12 runs and 144 entries is the census decision from `resident_home.md` section 4, applied as specified. One build iteration is worth recording: the first hook build measured 414 bytes and fit with zero spare, but its fallback path left the scratch register ip holding a test constant where stock passes the entry value through. The shipped build saves and restores ip on both hooks (free on the companion, whose stack frame already existed; +4 net on the primary) and removes two redundant staging-base reloads that `run_ptr_from_id` and the write-out path make unnecessary (both preserve ip), landing at 410 bytes.

## The hook, as built

Implementation follows `resolver_design.md` job 3, with one correction proven from the stock code, flagged here because it changes a design sentence:

- **Companion discriminator register.** The design text says the cluster test is on r0. The module 33 call site at 0x0308A6BA loads r0 from [ctx+2] (the index) and r1 from [ctx+0x34] (the cluster), and the stock fetch at 0x0305B2C2 keeps r1 in r5 and compares it against the current-directory cell at 0x0307AB64. The companion hook therefore tests **r1** against the last served run's cluster. Its other arguments are r2 = 0x03005714 (table cell) and r3 = mode, and its entry bytes are also `2D E9 F0 47`. The design's intent (flag + mode 1 + cluster equals last served run's cluster) is unchanged.

Behaviour, both hooks:

- Flag test first. Clear flag, or any discriminator mismatch, re-executes the displaced `push.w {r4-r8, sb, sl, lr}` with every register (including ip, which the tests clobber) and the stack exactly as at entry, then continues at entry+4. APSR is not live at either stock entry (the displaced push ignores it and the next stock instruction is a MOV).
- Primary discriminator: out descriptor pointer r1 == 0x030239B4 and mode r3 == 1. This is exactly module 33's source 6 call; it excludes the module 31 setup call, module 0's internal callers, and the source 0x63 call, per the design's caller census.
- Companion discriminator: flag set, r3 == 1, r1 == cluster of the run containing the last served entry (past-end state uses the last entry's run). On a match the substitution writes the play context descriptor at its fixed address: 0x030239B4 (ctx+0x34, cluster), 0x030239BC (ctx+0x3C, countA+countB), 0x030239D0 (ctx+0x50, the 42-byte context), and returns the within-directory index.
- Serve mapping (shared): the incoming index is compared in the u16 domain against the header's last residual: +1 serves the next entry, -1 the previous (clamped at entry 0), equal re-serves, anything else is a fresh selection clamped into range. Position and residual live in the header, because stock overwrites [ctx+2] with the residual after every serve.
- Past-the-end: serving position == count writes the last run's cluster and context and returns that run's countA as the residual, the sentinel shape the design specifies so module 33's own stop logic fires.
- One stated assumption, inherited from the design: when the flag is set the staging is valid (count >= 1). The bridge arms the flag only after a complete import; the hooks do not re-validate the table.

## Patch files

In `patches/` (scratch copies of the live patch files and manifest are there too; the live tree was not modified). Each file parses with the framework's own `parse_patch`, and each branch was disassembly-verified against its target.

| File | Site | Expect | Replace | Target |
| --- | --- | --- | --- | --- |
| 0041-resolver-primary-hook.patch | 0x03059DAC | `2de9f047` | `22f056bb` | B.W 0x0307C45C (`resolver_hook_primary`) |
| 0042-resolver-companion-hook.patch | 0x0305B2C2 | `2de9f047` | `21f0e8b8` | B.W 0x0307C496 (`resolver_hook_companion`) |
| 0032-ui-bt-dispatcher-hook-tail.patch | 0x03061E5E | `2046bde8f09f` | `1af0cbbb00bf` | B.W 0x0307C5F8 (`ui_dispatcher_hook`) + NOP |

Patch 0032-tail is the UI build's patch 0032 with the branch target regenerated for the tail base. A result worth stating plainly: **the relinked Bluetooth blob is byte-identical to the UI build's original `ext.bin`** (436 bytes, same compiler version). The blob's interior held no self-absolute references, so the relink changed nothing inside it; only the dispatcher branch in the patch moved.

## Scratch build

`build_tail.py` runs the pipeline: assemble and link the hook, relink the Bluetooth blob, generate the three patches (Python B.W encoder, asserted against the UI build's known 0032 encoding), compose the blob, then invoke the framework `build.py` twice with the full transplant set.

- Baseline: live manifest (32 patches) plus the vorbis75 transplant, no extension. SHA above.
- Tail image: scratch manifest (the same 32 plus 0032-tail, 0041, 0042 = 35 patches) plus the transplant plus the extension blob. `firmware_patch.validate()` passed (header mirror, trailer CRC, V137 layout), both by the build's finalization and by a direct re-check.
- Diff, tail vs baseline: **818 bytes in 54 ranges, all inside the allowed set**: the code length record (file 0x210, 2 of its 4 bytes), the 0041 site (0x33458, 4 bytes), the 0042 site (0x3496E, 4 bytes), the 0032 site (0x3B50A, 6 bytes), the nonzero occupant bytes inside the extension span (file 0x532C0..0x55E57), and the trailer CRC (0xD00000, 4 bytes). Nothing else moved.

## Emulation

Harnesses in `emu/`, full output in `scratch/emu_bt_tail_output.txt` and `scratch/emu_resolver_output.txt`. All runs map module 0 code and data from the built tail image, so the hooks execute at their real addresses through the real patch branches.

### (a) Bluetooth six-case suite at the tail base

The UI build's suite (`emu_bt_tail.py`, cases and checks unchanged), entered at the patched dispatcher site 0x03061E5E as before. All six cases pass, matching the original run at the old base:

| Case | Result |
| --- | --- |
| Long-press Power, BT off to on (banner CV15) | Pass: event swallowed (r0 = 0), SAVEINFO +0x2D4 = 1, result byte 5, GPIO port 2 bit 7 set, flags 0x123 and 0x1B8 posted, tick copy written, delays 100 + 10 + 1 |
| Long-press Power, BT on to off | Pass: +0x2D4 and +0x2D3 cleared, port 2 bits 7/17/16 all 0, one 200 ms delay, no 0x123 post |
| Long-press Power, banner never arrives | Pass: full 5000 ms poll, timeout powers back down, status byte 7, +0x2D4 back to 0, no post-on writes |
| T1 Power short press | Pass: pass-through, r0 = event word, no MMIO writes, no delays |
| T2 other key | Pass: pass-through, same checks |
| T4 OK release | Pass: pass-through, same checks |

The saved register frame was restored exactly in every case.

### (b) Resolver fallback equivalence

Method: the stock resolver and fetch call three stack-managing callees (reset 0x03059C76, stack init 0x03059F58, descend 0x03059B10) whose real bodies walk card structures that do not exist offline. Those three are intercepted and replaced by a deterministic model of the directory stack over a fixed tree (root with countA 2 / countB 1, subdirectories A with 3 / 0 and B with 1 / 2, distinct 42-byte contexts), mirrored into emulated memory at the real stack addresses. The resolver and fetch code itself, including its 42-byte memcpy, runs for real. The model is identical between the stock run and the hooked run, so any divergence is attributable to the hooks. Descend is modelled as a depth-first advance with a per-element child cursor; the resolver's own post-descend checks then behave as traced (including the depth-0 wrap to index 0).

Compared per scenario: return value, registers r0 to r12 (with ip seeded to a sentinel value 0x12C0FFEE at entry, so the comparison proves the hooks return it untouched), stack pointer, the out descriptor bytes, the directory stack area bytes, and the model call log. **All 12 scenarios byte-identical:**

| Scenario | Shape | Stock result |
| --- | --- | --- |
| P1 | primary, flag clear, disc-passing, i=0 | ret 0, root |
| P2 | primary, flag clear, disc-passing, i=3 | ret 1, directory A after one descend |
| P3 | primary, flag set, excluded out pointer (module 31 shape), i=1 | ret 1 |
| P4 | primary, flag set, excluded mode 3 (source 0x63), i=4 | ret 2, directory A |
| P5 | primary, flag set, excluded out pointer (module 0 internal), i=5 | ret 3, directory A |
| P6 | primary, flag clear, disc-passing, i=7 | ret 0, exhaustion wrap to root |
| P7 | primary, flag clear, disc-passing, i=6 | ret 1, directory B |
| C1 | companion, flag clear, cluster A, idx 1 | ret 3 |
| C2 | companion, flag set, excluded mode 3, cluster A, idx 1 | ret 3 |
| C3 | companion, flag set, staged, cluster B != last run A, idx 0 | ret 5 (full stock walk) |
| C4 | companion, flag set, staged, sentinel cluster argument 0x0FFFFFF7, idx 0 | ret 0, no callees |
| C5 | companion, flag clear, cluster == root, idx 2 | ret 2 |

Control: with the flag set and discriminator-passing arguments, the primary hook engages (serves the staged entry 0, cluster 0x2001, no stock callees run), proving the equivalence above is not vacuous.

### (c) Staged traversal

Synthetic playlist in the tail layout: run 0 = directory A (cluster 0x2001, countA 3, countB 0), run 1 = directory B (cluster 0x2002, countA 1, countB 2); entries (within 0, run 0), (within 2, run 0), (within 0, run 1). Driven with module 33's index presentation (stored residual, +1 next, 0xFFFF for previous). Every step matched the expected cluster, total, 42-byte context, header position and residual:

| Step | Presentation | Served | Return |
| --- | --- | --- | --- |
| First track | i = 0, position none | entry 0, run A | 0 |
| Next within run | i = residual + 1 = 1 | entry 1, run A | 2 |
| Next across boundary | i = 3 | entry 2, run B | 0 |
| Previous | i = 0xFFFF (residual - 1) | entry 1, run A | 2 |
| Next again | i = 3 | entry 2, run B | 0 |
| Past the end | i = 1 | sentinel on run B | **1 = countA of the last run**, position = count = 3 |

Companion path, after two primary serves left position 1 in run A: a path B call (idx 3, cluster argument A) crossed into run B and rewrote the descriptor (cluster 0x2002, total 3, run B context, return 0); a following path B call (idx 1, cluster argument B) served the sentinel (return 1 = countA of run B, position = count). No stock callee ran in any substitution step of either sequence. The remaining hardware question is the design's own named one: whether module 33 reads this sentinel as a clean stop or an error stop is not distinguishable offline.

## Risks and open items

- The tail is still a Phase E canary candidate, not a proven home. This build does not change that: the census standard is met offline, and the hardware canary in `resident_home.md` (pattern write, mount, playback, scan, settings save, Bluetooth cycling, Rockusb read-back) remains the settling test. If the canary fails, the composition falls back cleanly because the flag ships clear and the hooks are inert without it.
- End-of-playlist stop behaviour (clean stop vs error stop on the sentinel) is a hardware check, as the resolver design states.
- The traversal was exercised at the two fetch points with module 33's index presentation as traced at those points, not as one continuous session on hardware; the design's Phase E full-traversal check stands.
- Tail spare is 4 bytes. Any future hook growth must come out of the staging caps (4 bytes per entry, 50 per run), per the census arithmetic.

## Files

- `src/resolver_hook.S`: hook source (primary, companion, serve routine).
- `bt/hooks.S`, `bt/bt_toggle.c`, `bt/ext_tail.ld`: Bluetooth blob sources copied from the UI build, with the linker script base regenerated.
- `patches/`: the three new patch files, scratch copies of the live patches, and `manifest_scratch.txt` (35 entries).
- `build_tail.py`: the whole pipeline, including the budget refusal and the diff-confinement check.
- `emu/emu_bt_tail.py`, `emu/emu_resolver.py`: the two harnesses.
- `scratch/`: hook and Bluetooth objects, ELFs and maps, `tail_blob.bin`, `baseline.img`, `out_tail.img` with its build report, `summary.json`, and both emulation outputs.
