# Power profiles

A Power Profile item at the end of System Settings, with three options:

| Option | Brightness | Auto screen off | Auto power off |
|---|---|---|---|
| High | 100 % | 1 minute | never |
| Balanced | 60 % | 30 seconds | 10 minutes |
| Battery Saver | 20 % | 10 seconds | 5 minutes |

The item marks the option whose three values match the current settings. If
the user changes one of them by hand, no option is marked. Choosing an option
writes the three settings through the same stock setters their own items use,
applies the backlight and saves. A profile is not a new mode. Nothing is
stored beyond the three stock settings, and stock boot restores those as it
always has. The labels are translated into all 21 menu languages.

Standard image only (patches 0140 to 0146 and 64 theme runs in
[`../../full/`](../../full/README.md#power-profiles)).

## How the item is added

**The menu tree is data.** Every string record (258 bytes, 266 per language)
begins with the SDK's `MENU_TEXT_INFO_STRUCT` (`Common/Display/LcdChar.h`):
self id, parent, index in parent, first child, previous and next sibling,
function index, child count, and up to 21 child ids. The text follows at +58.
System Settings is record 164 with 16 children, ending in 243 (Product Info).

**Only two routines turn an id into an address.**
- `GetResourceStr` (0x030630C2) reads text.
- `GetMenuTextInfoWithIDNum` (0x03063206) reads the 58-byte header.

Both compute `language base + language × 266 × 258 + id × 258` (the constant
is `movw #0x4305` × 4 at 0x030630C6 and 0x03063224, the only two in the
firmware). They then call the flash read at 0x0306432A.

**New ids live past the table.** Ids 266 to 269 are the item and its options.
The hook at each routine's entry (patches 0142, 0143) re-runs the two
displaced instructions for every stock id, so stock lookups are unchanged.
Ids 266 and up go to a table placed in the zero padding after the image
resources:
- four headers, which are the same in every language;
- then 21 × 4 label slots of 48 bytes.

That padding is inside the firmware length, so it is flashed. Its distance
from the language section (0x0054579A) is the same in every build, because
module growth shifts all resource sections together. Stock code never
fetches ids 266 to 269: on stock they would land in the next language's
records 0 to 3.

**Tree edits, per language** (theme runs):
- record 164's child count goes from 16 to 17;
- record 164's 17th child slot gets 266;
- record 243's next sibling gets 266.

The item's own header names 164 as parent, index 16, children 267 to 269.

**The settings window** (module 32) needs two hooks, because it keys behaviour
on item ids rather than on the records' function index:
- *Value switch* at 0x0307DBCE (patch 0144). When a submenu opens, a switch
  on the item id loads the current option from SAVEINFO:
  - 188 → +0x15
  - 196 → +0x14
  - 202 → +0x18
  - and so on.

  The hook runs the displaced 188 case itself. For 266 it returns the
  matching profile, or takes the switch's own "no value" exit. Every other id
  re-enters the switch with the flags it expects.
- *Commit* at 0x0307FA80 (patch 0145). Choosing an option calls
  0x0307FA74 with the option's id, which switches on `id - 152` for ids 152
  to 265 and sends anything else to its default exit. The hook catches 267
  to 269 on that branch. It writes:
  - brightness to +0x14, then calls the backlight apply (0x03064964), as the
    window's brightness case does;
  - auto screen off through module 32's setter 0x0307E232;
  - auto power off through its setter 0x0307E2B2, which re-arms the power-off
    timer.

  It then saves SAVEINFO (0x0306CA10) and takes the same default exit.

**Placement.** The code is 240 bytes in three module 0 routines that the
reachability census found dead ([`../../space/`](../../space/README.md)):
- 0x0305168C: the lookups, 104 bytes;
- 0x03054668: the value hook and the preset table, 76 bytes;
- 0x03067064: the commit hook, 60 bytes.

Module 0 is resident in every window, so lookups from any window and both
module 32 hooks reach the code.

## What changed from the first design

The first design ([`../power.md`](../power.md), [`../build/`](../build/))
had four problems:
- *No settings item:* its working id 0xC5 was brightness's own "20%" record.
- *Clock caps below Rockchip's figures:* 240 MHz for lossless decoders,
  where the SDK's table asks 400 for APE and ALAC.
- *A wheel-timer change:* like the clock caps, it had no boot reapply path.
- *A 32-byte area in SAVEINFO's string block.*

This version uses only stock settings with their stock setters. The wheel
timer is already 1000 µs in every CE image (patch 0050).

## Checks

`test_profiles.py` runs the real firmware code under Unicorn on the patched
image. CI runs it on the built Standard image. The flash read is replaced by
a reader over the image file.
- `GetResourceStr` and `GetMenuTextInfoWithIDNum` return the stock text and
  header for all 266 ids in all 21 languages. They return the new labels and
  headers for 266 to 269.
- 164 lists 266 as its 17th child, and 243 links to it, in every language.
- The value switch marks each profile when SAVEINFO matches it, and marks
  none otherwise. Items 188, 196 and 202 still load their stock bytes.
- Each option writes its three values, applies the backlight with the new
  level and saves once. A stock option (197) never enters the hook. An id
  past the options changes nothing.

`build_profiles.py` checks every stock fact it relies on before emitting
anything, and CI rebuilds its outputs and diffs them:
- the section layout and the 0x0054579A distance;
- the 266-record stride;
- the language order;
- the literals;
- each site's stock bytes.

Every ld branch to a stock address is checked in the disassembly.

One condition comes from the stock lookups themselves. They use the
266-record stride only while SAVEINFO +0x1F (the SDK's `FMEnable`, copied
from the firmware header at boot) is nonzero. The image lays out every
language at that stride, so a unit that shows its languages correctly runs
with it set. The test sets it the same way.

## Not yet proven

- On hardware: the 17-item settings list drawing and scrolling, the new
  labels in each script, and the options selecting as emulated.
- What each profile saves in battery life.
