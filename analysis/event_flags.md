# Event flags and UI handlers in V137 (original Thumb instructions)

The resident module-0 firmware implements a **bit-indexed event flag array** in RAM. This is an important correction to treating every small immediate in the menu overlay as a localized string ID. V137's event IDs and language string IDs can share the same number but belong to **different namespaces**. No direct relationship has been established between them.

The word literal at CPU `0x030672b8` contains the pointer `0x03023cf8`. Four nearby leaf routines index this address with `r0 >> 5` (32 flags per word) and use the bit `1 << (r0 & 31)`. Each operation has been reconstructed from the exact original Thumb instructions.

| Module 0 function | ARM behavior | Instruction evidence |
| --- | --- | --- |
| `0x0306723c` | Set a flag (bitwise OR into word) | `LSRS r1,r0,#5`; `AND r0,#31`; `LDR`; shift one; `ORRS`; `STR`; `BX LR` |
| `0x03067258` | Test-and-clear a flag, returning 0 if absent or 1 if set | `TST`, conditional return 0, `BIC` and `STR`, return 1 |
| `0x0306727e` | Clear a flag unconditionally | indexed `LDR`, `BIC`, `STR`, return |
| `0x0306729c` | Test without clearing, returning a Boolean | indexed `LDR`, `AND`, normalize result to 1 |

This demonstrates a shared event/state notification facility. It is **not** itself a message queue, and the producer/consumer pairing for each application event remains to be reconstructed.

Concrete module-32 callers:

- `0x0307fd9c`: loads event index `0xb7` (183) and calls `0x0306723c` (sets it).
- `0x0307fda2`: sets `0xb9` (185) through the same function.
- `0x0307fda8`: sets `0xb8` (184).
- `0x030800b6`: loads `0xb8` and calls `0x03067258` (consumes the flag).
- `0x030800bc`: loads `0xb9` and calls `0x03067258`.
- `0x0307d820`: loads event `0xbc` (188) and calls `0x03067258` (test-and-clear).
- `0x0307d4dc`: loads `0xc4` (196) and branches into a drawing path at `0x0307d408`; **not** an observed event-set call.
- `0x0307d5e0`: loads `0xca` (202) as an argument to `0x0306354a`; **not** an observed event-set call.

**Do not label event 184 as "Lock Screen Wallpaper" or event 196 as "Screen Brightness" solely because those are the English resource strings with the same indexes.** These immediate values may index internal event bits only. The localized resource table independently contains the lock-screen, screen timeout, brightness and power-off texts; it does not itself identify their handlers. An old-to-V137 binary comparison and a producer/consumer call graph are needed before associating events with specific features.

The event word containing ID 184 is `0x03023d0c`, bit 24; ID 196 is `0x03023d10`, bit 4; ID 202 is `0x03023d10`, bit 10. These are **RAM bit positions, not MMIO register locations**.

This is useful for the feature work because a new display or power policy may already have a native way to notify the UI/task loop. But injecting arbitrary events without knowing the consumer is unsafe. Trace every set, test, test-clear and clear site for a candidate event before changing the flags.

Reproduce the immediate locations and localized labels *separately* using `python3 tools/feature_landmarks.py DP3_V137.img`. For source-level analysis, import module 0 at `0x03050000` and module 32 at `0x0307d164` in Ghidra, mark embedded literals as data, and label the functions `event_set`, `event_test_clear`, `event_clear`, `event_test` based on their instruction behavior.
