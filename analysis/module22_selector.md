# Module 22 selector: original Thumb execution

For stock `DP3_V137.img` SHA-256 `fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`, the module table maps module 22 code from file `0x8467c` to execution address `0x0307d164`, length `0xb9c`. The routine at file `0x846ba` therefore executes at `0x0307d1a2`. This mapping follows the package records; it does not identify physical flash addresses.

The routine uses an unsigned range check and a Thumb `TBB` jump table. Ghidra 11.0.3's p-code emulator executed the original instructions in a raw image mapped at file offset zero. `r0` supplied the input, and a synthetic return address in `lr` terminated each run. Inputs 0–12 returned:

| Input | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9–12 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Return in r0 | 0 | 1 | 1 | 2 | 3 | 0 | 5 | 6 | 7 | 0 |

The unsigned comparison and conditional return also establish zero for all input values at least 9. At file `0x846ee` (execution address `0x0307d1d6`), a caller reads a halfword from its input, calls the selector and stores the result through a literal-loaded pointer. The role of the selector and its surrounding hardware or UI behavior remain unknown. No peripheral is modeled, and the use of Ghidra's `ARM:LE:32:v8` language is an emulation configuration, not identification of the chip as ARMv8.

Reproduce in Ghidra 11.0.3 with an empty writable project directory:

```sh
analyzeHeadless /path/to/project-directory neo \
  -import DP3_V137.img -loader BinaryLoader \
  -processor ARM:LE:32:v8 -noanalysis \
  -scriptPath tools/ghidra -postScript RunSelector.java
```

The script checks the entry bytes, sets Thumb mode, disassembles the table targets and asserts all 13 observed returns. Addresses in its emulator are **file offsets**, used as a temporary flat mapping; PC-relative jumps within this routine retain their relative distances. The run terminates at synthetic address `0x90000` and does not emulate the device's loader, exceptions or peripherals.
