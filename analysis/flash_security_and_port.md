# Flashing, trust checks and Rockbox feasibility (DP3_V137)

Analysis target: `DP3_V137.img`, 13,631,492 bytes, SHA-256 `fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`.

## Main result

**There is no cryptographic authenticity check in the two update and installed-slot validation routines traced so far.** Both use RKnano magic, a duplicate 512-byte header and comparisons of raw data. The package has a reconstructible, non-keyed CRC-32. This makes offline size-preserving code and resource edits feasible without a signing key. It does not prove that the device's boot ROM, secondary loader, or production settings will accept such an edit.

Additional file-layout evidence: The updater's calculated 13 MiB transfer length ends at file `0xD00000`, exactly where the four-byte outer CRC begins. The CRC trailer therefore lies outside that calculated main copy. All 441,856 bytes at `0xC94200..0xCFFFFF` (after the header mirror) are zero in V137, providing unused *package capacity*. Those zeros are not an executable code cave by themselves; using them for code would also require verified module-loader mapping and runtime RAM space.

The separate [FiiO Echo Nano firmware patching project](https://github.com/maaraneasi/nanitecfw) demonstrates stock firmware modification, CRC regeneration and booting of customized code on a sibling RKnano-based player. It does not independently verify the Fosi DAP Neo.

## What the machine code actually checks

### Update-file installer: module 8

Entry at `0x0307e64c`, verified against code bytes at file `0x84264`:

1. `0x0307e6fa` reads one 512-byte header into the local stack buffer using `0x03058fa8`.
2. `0x0307e70a` to `0x0307e716` compares eight bytes at header `+0x1f8` with the embedded `RKnanoFW` constant by calling `0x03054ebe`.
3. `0x0307e718` reads the user-supplied 32-bit header field at `+0x1f4`. `0x0307e71c` adds `0x104000`; `0x0307e720` clears the bottom 20 bits of the result. With `0x00c94000` this produces `0x00d00000` (13 MiB), the rounded image length.
4. `0x0307e730` reads a second 512-byte header from the file position indicated by `+0x1f4`. `0x0307e73e` compares the second header to the first. This path does **not check the return value of the mirror read before comparing buffers**. The impact of a short read needs to be established from the file I/O implementation.
5. `0x0307e75c` enters the sector writer; `0x0307e53c` calls the device-3 write callback at `0x0305fc08`, read callback at `0x0305e020`, and a byte comparison on the readback. Writes/readbacks use up to 16 sectors per helper call (512 bytes per sector).

No RSA/ECDSA/Ed25519 verification, digest-comparison step, public key or signature-field validation was identified in this traced installer path. This is a **scope-limited negative finding**. We have not dumped the boot ROM or proven that nothing else can authenticate the update.

### Installed-flash slot validator: module 1

This is a separate, newly traced function at `0x0307e26c` (the module's code executes from `0x0307d164`).

- `0x0307e292` reads sector zero of logical device `0x00030000`. `0x0307e29e` compares the eight-byte marker at `+0x1f8` to `RKnanoFW`, using `0x03054ebe`. Failure logs `fw1 Sign error!`: **"Sign" here is the firmware magic**, not evidence of a cryptographic signature.
- `0x0307e2c6` obtains the `+0x1f4` length and reads the header mirror from `(length >> 9)` sectors after the first slot's start. `0x0307e2da` compares all 512 bytes. Failure logs `fw1 compare error!`.
- `0x0307e2ec` computes an aligned candidate second-slot base: `((length+0x104000)>>9) & 0xfffff800`. For V137 this is `0x6800` sectors, or `0xD00000` bytes (13 MiB). This is an observed logical slot stride, not a proven physical flash offset.
- `0x0307e2fe` scans candidate secondary headers. The code compares the magic at `0x0307e30c`, steps the candidate by `0x800` sectors (1 MiB) on a mismatch at `0x0307e320`, and uses the same mirror comparison at `0x0307e34c`. The retry counter is compared with `0x14` at `0x0307e32e`. It logs `fw2 compare error!`, `No find fw2!` and related messages in the same code block.
- If both headers pass, `0x0307e3e4` through `0x0307e400` compares the two four-byte BCD dates and favors the newer candidate. A flag is written at `0x0307e402`. This is not cryptographic anti-rollback: the date is editable and included in the duplicated header.
- The validator also maintains a slot/size state in data through `r10`. Boot ROM startup policy, actual flash geometry, and failover after a bad code image remain unverified.

No CRC or public-key verification call appears in this specific validator path, which does not mean the rest of the boot sequence is equally permissive.

## Issues and confidence

| Issue | Evidence | Consequence | Confidence |
| --- | --- | --- | --- |
| Unkeyed update CRC | Outer CRC-32 (polynomial `0x04c11db7`, init zero); exact recomputation tested | Package integrity is not authentication | Proven |
| User-editable mirrored metadata | File `0x1f4` length, marker `0x1f8`, matching copy at file `0xc94000` | Contents can be edited while preserving known checks | Proven offline |
| No signature verification in traced installer/slot-validator paths | Thumb control flow in modules 8 and 1 | Custom code is plausible on retail hardware | Proven for paths, unverified for full boot |
| Date-based slot precedence | Module 1 comparisons at `0x0307e3e4`-`0x0307e400` | A newer date can change preference; may complicate downgrade/recovery | Proven code, unverified production behavior |
| Header-length trust boundary | Module 8 uses `+0x1f4` for seek and rounded copy size | Malformed length could trigger excessive I/O or rejected reads; exploitability is unknown | Potential |
| Mirror read return ignored | Module 8 `0x0307e730`-`0x0307e742` | A short mirror read may be mishandled | Proven omission; effect unknown |
| Missing complete boot ROM/loader | Not present in supplied update package | Cannot demonstrate complete secure-boot bypass or safe modified flashing | Proven limitation |

The device-3 block callbacks apply a logical `0x2000` sector offset. Consequently, the dual-slot logical addresses above must not be interpreted as raw eMMC/flash-sector write instructions. No destructive flash access is implemented here.

## Offline modification proof

Run `python3 tools/firmware_patch.py DP3_V137.img --language 2 --string-id 136 --expect-text "USB Audio" --replace-text "USB Audo" --date 20261031`.

With no `--output`, the tool edits an in-memory copy only, refreshes the header mirror and CRC, and independently re-parses the result. Actual result on the uploaded stock file:

- Original SHA-256 `fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`.
- Modified in-memory SHA-256 `ae1f31a111e57c2408ed5d0c61ab9ff64a1b968fd012ee30a44358049aaed007`.
- Preserved length, 13,631,492 bytes; duplicate header matches; CRC valid (`0xddc29ba6`).
- Actual English UI string ID 136 reads `USB Audo` after modification.
- This proves offline editability and packaging, not installability.

A separate no-output opcode edit at module 39, address `0x0307d5fc`, successfully changed the original Thumb halfwords `a0 f1 61 01` to `a0 f1 62 01` in RAM, leaving the known package checks valid. Do not deploy that deliberately behavior-altering example.

## Practical porting choice

The near-term route is a **stock-kernel extension/custom UI overlay**, modeled on the working sibling-project approach. Keep Rockchip's kernel, flash driver, audio codecs, the two-core messaging interface, and external DAC control. Replace a targeted UI function or inject small Thumb code into an appropriately sized overlay, using exact original-address patch preconditions.

A clean Rockbox port would require replacing the scheduler/filesystem/device-driver layer, dual-core audio/decoder and shared memory IPC, LCD/input/backlight/power management, and CS43198 I2C/I2S control. The SoC family offers much less RAM than an ordinary Linux-class audio player. Even if the kernel is replaceable, a full Rockbox codec and plugin system may not fit without overlays, selective features, or reusing proprietary decoding. No mainline Rockbox RKNanoD port has been demonstrated by this analysis. Rockbox lists an earlier generic rk27xx port as unusable; that is a different platform.

## Safe next hardware checks

Preserve the full original flash before experiments. Establish the actual USB RockUSB identity and whether a read-only full backup is available. Determine storage type and block geometry, identify both installed slots and the active slot by read-only comparison, and confirm a reversible recovery path. A vendor recovery mode on a related RKnanoD device cannot be assumed identical on the Fosi model. Only after independent backup/recovery and exact-board identification should an on-device update trial be considered.
