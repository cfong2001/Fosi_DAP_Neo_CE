# How the V137 update maps to further firmware changes

Studied image: `DP3_V137.img`, SHA-256 `fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`. This is a reconstruction of the **delivery and runtime layers** of the stock update, not a source-code diff. We have V137, but no authenticated pre-V137 DAP Neo image. Therefore we cannot yet say which original instructions Fosi changed for each release-note item.

The [October 24, 2026 V137 announcement](https://www.reddit.com/r/DigitalAudioPlayer/comments/1xe7cal/a_firmware_update_for_the_fosi_dap_neo_is_now/) lists four changes: disable lock screen through System Settings > Lock Screen Wallpaper, repair Repeat Folder, show total tracks on the now-playing screen, and fix display issues. It does not claim a battery improvement. The [manufacturer's support page](https://support.fosiaudio.com/products/dapneo) is the named distribution endpoint; it was not accessible for direct inspection in this research environment.

## Firmware delivery reconstructed from the machine code

The released file is a **whole RKnano update package**, not an incremental binary patch and not a complete raw flash dump. It contains 82 module records, executable code and initialized data with distinct load/execute addresses, a BCD build date (2026-10-22), 21 fixed-record language tables, 456 RGB565 images, a duplicated 512-byte header and a non-cryptographic CRC trailer. This establishes what the update *ships*, but does not reveal Fosi's internal source tree, compiler commands or QA process.

The on-device updater (module 8, entry `0x0307e64c`) reads the first header, checks `RKnanoFW` at `+0x1f8`, obtains the mirror offset from `+0x1f4`, checks that second header against the first, and copies logical 512-byte sectors using the device-3 storage dispatch. The helper at `0x0307e53c` writes, reads back and compares up to 16 sectors per call. The module-1 installed-slot validator at `0x0307e26c` checks candidate headers and mirrors and compares BCD version dates. For V137 it derives a secondary candidate at logical sector `0x6800`, with 1 MiB search steps. It does **not** establish the physical flash geometry, actual update destination, inactive-slot safety or complete first-stage boot policy.

These are the steps in a **proposed equivalent engineering workflow**:

1. Modify the relevant application overlay or system/decoder component; update resource strings and image IDs only if the UI needs them.
2. Reassemble module payloads and their load/execute/BSS records. Preserve overlay collision rules, vector tables, memory limits and cross-module pointers. An in-place same-length patch is simpler than re-linking an overlay.
3. Rebuild the RKnano container, including the mirrored header, internal lengths/layout and outer CRC. This satisfies *known offline checks*. It does not prove bootloader acceptance.
4. Validate the image without hardware. Compare every changed module and resource, disassemble changed sites, execute unit-level code with modeled hardware, and inspect the ROM/update trust boundaries.
5. Before any real installation, establish full-flash **read-only** backup and tested recovery. Run a controlled device trial only after the location and behavior of both installed firmware slots are known.

We cannot establish that Fosi followed this exact source/build process. The package and on-device code support these technical steps.

## How the four V137 changes relate to the binary

| Published change | V137 evidence | Where to investigate next | Our analogous modification |
| --- | --- | --- | --- |
| Disable lock screen | English resource 184 is `Lock Screen Wallpaper`. **Separately**, module 32 sets event bit 184 at `0x0307fda8` and tests-and-clears it at `0x030800b6` through module-0 event functions; equality of the event number and resource ID does not prove they are the same menu control | Trace callers into lock-entry state and persistent settings, and identify the consumer of event 184 before associating it with the release change | Show title/artist on lock screen, selectable lock behavior, customizable wake shortcut |
| Fix Repeat Folder | Resource 151 `Play Mode`, 154 `Repeat Folder`; module 32 compares an immediate `0x97` at `0x0307d22c`, but the meaning of this comparison is **not proven**; module 31 contains `HoldOnplay : %d` | Locate repeat-mode state, folder iterator, next-track event and end-of-stream transition; establish boundaries before touching the audio decoder | Correct all queue transitions, then implement gapless playback via preload and continuous PCM |
| Display playlist total | Resource 80 `Now Playing`, 85 `Playlists`; module 27 has `CurrentFileNum `, module 23 `TotalFiles is --- %d ---` | Find ownership of current-list count, playback screen formatter and redraw routine; confirm whether the counter is queue length or library size | Show track X of Y, queue duration and playlist position |
| Display fixes | Module 32 contains `MenuKeyPro - SelItemID` and multiple drawing calls; assets are 456 indexed RGB565 images, and module 18 handles `METADATA_BLOCK_PICTURE` | Trace dirty rectangles, overlapping text, glyph width, background restore, album-art bounds and frame updates | Legible fonts, better artwork layout, lock-screen metadata and fewer redundant LCD writes |

The Fosi release demonstrates that changes at these *classes* of software can be shipped. The precise modules changed in V137 cannot be proved without an earlier image.

Module 0 supplies a shared bit-indexed event mechanism: `0x0306723c` sets, `0x03067258` tests-and-clears, `0x0306727e` clears, and `0x0306729c` tests flags in RAM beginning at `0x03023cf8`. This is directly established by Thumb instructions. It matters for both UI changes and power notifications, but does not map event IDs to menu labels. See [the event-bit trace](event_flags.md).

## Map the same mechanism to planned enhancements

| Target | Existing stock facility / proposed change | Required reconstruction | Major dependency |
| --- | --- | --- | --- |
| Battery: backlight-off playback | Existing Auto Screen Off text is resource 188, brightness 196, Auto Power Off 202. Module 32 separately *consumes event 188* at `0x0307d820`, passes `196` to a drawing path at `0x0307d4dc`, and passes `202` into routine `0x0306354a` at `0x0307d5e0`; these are **not yet identified as the settings handlers** | Track settings dispatch into actual backlight PWM/GPIO, LCD clock and screen wake path; ensure screen-off is real power-off, not a black picture | Locate physical backlight controller and wake events; current measurement |
| Battery: pause/idle standby | Module 0 has `WFI; BX LR` at `0x03055b70`; shutdown path begins `0x03067c1c`; DAC is manufacturer-specified CS43198 | Resolve RTOS idle task, system tick, audio state changes, I2C control writes, DAC power sequencing, radio standby | Prove clock/data ownership and wake/restore logic; measured current |
| Battery: fewer redraws | Module 32 UI calls, module 18 album art decoder, indexed RGB565 graphics | Mark dirty areas and avoid drawing on every tick while playback continues | Reliable display-controller/DMA activity trace |
| Better controls and Bluetooth shortcut | Module 32 menu/event logic, existing Bluetooth labels 167-169 | Trace key/wheel event map, debounce, mode persistence, Bluetooth module control event | Verify physical input scan and wireless lifecycle |
| Playback controls and gapless | Module 31 playback state, module 27 iterator, module 33 codec setup, calculation-core modules 71-80 | Pre-open next file, decode to a separate buffer, identify format-specific delay/padding, eliminate unnecessary DAC stop/restart | Second-core IPC, decoder state, PCM/DMA buffer memory |
| M3U playlists | Module 23 folder/file enumeration; module 27 current-file index; module 31 playback/queue | Add bounded UTF-8/UTF-16 line parsing, path resolution, list indexing, format filtering and persistence | RAM budget, filesystem semantics, queue object ownership |
| Lock-screen metadata and now-playing extras | Module 32 UI; metadata from module 18 and core 0 | Identify metadata state and draw paths; ensure screen updates do not wake the backlight without user input | Font and screen redraw ownership |
| Battery-saving preset | Existing timeout and brightness options plus potential DAC standby | Build a reversible combination of verified controls, not guessed MMIO writes | Independent measurements and no audio regression |

**Do first:** lock-screen or now-playing text changes, a resource-level font or artwork proof, and screen timeout behavior tracing. These reuse the same UI/runtime surfaces that Fosi's V137 update visibly changed. **Do later:** gapless and clock/power changes. They cross decoder cores and hardware state, where a malformed patch can silence audio or cause unstable power behavior.

## How to verify what Fosi changed when an earlier image is available

`tools/compare_releases.py` compares two complete RKnano images by module ID, original code/data execution address, SHA-256 and changed byte spans. It also compares text by (language, string ID) and images by resource ID, dimensions and decoded-pixel payload hash. When code length or execute base changes, it deliberately reports a layout mismatch rather than guessing that bytes still map to the same instructions.

```sh
python3 tools/compare_releases.py DP3_OLD.img DP3_V137.img --output old_to_v137.json
python3 tools/feature_landmarks.py DP3_V137.img --output v137_landmarks.json
```

The tools were checked offline against the original uploaded V137. Comparing V137 to itself reports zero module, language and image changes. A synthetic, size-preserving string modification was detected as **one English string change (ID 184)**, with no false code/asset changes; a separate synthetic module-32 one-byte change was found at the correct original execution address `0x0307fda8`. Those are tool-validation fixtures, not claims about Fosi's update and **not firmware for installation**.

A legitimate old image should be hashed and kept unchanged, then the diff should be mapped to disassembly and function-level control flow. Changed UI strings alone will not prove a new feature; corresponding code, state transitions and persistence must be established.

## Test criteria for each planned change

- **Screen/battery:** measure average supply current and drain duration with the same media, card, headphones, volume, brightness and battery state. Confirm playback/wake, alarm/USB handling, no clicks, and no underruns. A changed battery icon is not a measured endurance improvement.
- **Repeat/gapless:** one-track folder, first/last track, repeat one/all/folder, shuffle, pause/resume, codec changes, trailing encoder padding and sample continuity at the boundary.
- **Playlist counts/M3U:** empty queue, mixed folders, unsupported file, removal during playback, Unicode paths, long filenames, thousands of tracks, and resuming after reboot.
- **Lock/display:** persistence after full power-off, unlock controls, variable-length Unicode titles, album-art changes, dimming, screen refresh and USB charging screens.
- **Release safety:** exact original-byte patch preconditions, valid package mirror/CRC, module/RAM collision audit, full-flash backup and verified recovery before any install.

## What is still missing

The earlier firmware image; proof of the physical update-slot mapping and ROM signature policy; function-level UI and playback state graphs; CS43198 bus and power sequencing; LCD/backlight controller and clock ownership; decoder IPC and memory budgets; and battery-current measurements. Until those exist, this is a grounded modification plan with verified landmarks, **not a claim that Fosi's original source changes have been reconstructed**.
