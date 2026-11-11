# Design refresh v4: browser icons (music selection window)

Scope: the file browser window, module 31 (window overlay at the
shared base 0x0307D164). The set redraws every icon resource this
window's own code draws, in the v4 language (bare filled geometric
glyphs, no tiles or rings). It changes no code: delivery is a
theme-config runs file only. All findings below are from the stock
image `DP3_V137.img` (SHA-256
`fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef`);
module 31 code segment `module_31_code_0307d164.bin`, stock code
length 0x1CE4.

## Census: what the browser window draws

Window callbacks (module 31 data at 0x03024800): Service
0x0307DA8B, Key 0x0307E5B9, Paint 0x0307ED41 (a tail branch at
0x0307ED40 into the painter at 0x0307E8F2), plus 0x0307D6A1 and
0x0307D777.

A BL census of the whole module finds no call to DrawImageAt
(0x0306354A) and no call to any keyed helper. The only resource
draws in the module are six DrawImage (0x03063700) sites:

| Site | Resource id | Family |
|---|---|---|
| 0x0307DB60 (Service) | halfword [0x03023144] + 145 | battery gauge, 145..154 |
| 0x0307E840 (helper 0x0307E804) | byte [0x0302312C] + 263 | file state, 263/264 |
| 0x0307E856 (helper) | byte [0x0302312D] + 261 | headphones, 261/262 |
| 0x0307E86A (helper) | byte [0x0302312E] + 143 | play state, 143/144 |
| 0x0307E880 (helper) | byte [0x0302312F] + 265 | sleep timer, 265/266 |
| 0x0307E89E (helper, tail) | bit 2 of byte [0x030230EC], + 38 | hold lock, 38/39 |

The helper at 0x0307E804 consumes the repaint flags 0x27, 0x28,
0x2C, 0x2D, 0x2E, which the shared status routine 0x03063A32
(module 0) posts; this module calls that routine from its Service
(0x0307DB54) and its painter (0x0307E96E, 0x0307E974). No static
caller of the helper exists in any extracted segment (BL census
over all modules, and no stored pointer to it), and DrawImage
takes its position from the display context, so the status icons'
on-screen positions are not derivable offline. That is a Phase E
question; it does not affect the art, which is ground-matched per
resource (see the route section).

The list itself draws no resources at all. The painter
(0x0307E8F2) renders each row from fills and text only:

- Chrome: 0x03063570(0) fills the title band (0, 0)..(239, 39)
  with the palette background; 0x03063570(2) fills the list area
  (0, 40)..(239, 319) with the palette background and draws the
  row separator lines. The title text comes from the list context
  at 0x03025928 + 0xC, drawn with 0x03062F54.
- Rows: 7 visible. Row i occupies y 40+40i..78+40i; the text rect
  is (11, 53+40i)..(231, 68+40i); a separator line fills
  (0, 79+40i)..(239, 80+40i) with the palette line colour. The
  entry name is the UTF-16 string at node + 0x70 (next pointer at
  node + 4, class byte at node + 0x4E, the structure the M3U
  bridge hooks at 0x0307DF1A). Text is drawn with 0x03062CEE; a
  selected row whose name measures wider than 0xDC px takes the
  marquee path (0x0306302A). There are no folder icons, no file
  icons by format, no playlist or CUE icons, and no empty-state
  graphic in this window: per-entry kind is shown by text alone.
  Two list modes share this geometry (painter loops gated by
  flags 0x144 and 0x143).

Selection treatment (kept, unchanged): the palette writer
(0x030655BC) defines four cells, dark / light: background
0x030235B4 = 0x0000 / 0xFFFF, foreground 0x030235B6 = 0xFFFF /
0x0000, accent 0x030235B8 = 0xF220 / 0xFB20, line 0x030235BA =
0x1082 / 0xEF7D. On a selection move the painter fills the
previously selected row's band with the background cell and the
newly selected row's band (0, 40+40i)..(239, 78+40i) with the
accent cell; the text keeps the foreground pen in both cases.
The redraw set touches none of this: it is fills and palette
values, not resources.

Shared chrome drawn on this window but not owned by it (census
only, not in the set): module 0 draws the play-mode icons
286..289 keyed at (76, 5) from inside 0x03063A32, and the
Bluetooth icons 282..285 at (176, 5) from 0x03063642. Resource
130 (6x12 chevron) is drawn per row only by 0x03063570 variant 1;
this window calls variants 0 and 2, so it never appears here.

### The set

38 resources: 20 dark, 18 light (plus the five keyed sprites described under Art spec, 43 in all). Meanings follow the stock art
(the v3 mapping agrees where it covers these ids: lock,
small-pause, small-play, battery-level-n, battery-charging-n,
headphones, clock).

| Ids | Size | Meaning | Ground (measured stock surround) |
|---|---|---|---|
| 38, 39 | 15x17 | hold lock blank / lock | 0x2945 |
| 143, 144 | 12x12 | play state: pause / play (dark) | 0x0000 |
| 309, 310 | 12x12 | play state: pause / play (light) | 0xFFFF |
| 145..149 | 26x14 | battery level 0..4 (dark) | field 0x18C3 |
| 150..154 | 26x14 | battery charging 0..4 (dark) | field 0xF800 |
| 311..315 | 27x14 | battery level 0..4 (light) | field 0xFFFF |
| 316..320 | 28x14 / 27x14 | battery charging 0..4 (light) | interior 0xFFFF, exterior 0xF800 |
| 261, 262 | 19x18 | headphones blank / headphones | 0x2945 |
| 263, 264 | 14x18 | file none (X) / file present (1) | 0x2945 |
| 265, 266 | 18x18 | sleep timer blank / clock | 0x2945 |
| 427..432 | as dark | light copies of 261..266 | 0x2945 |

Light-theme notes, all measured: the resolver remaps ids by +166
in the light theme. Entries 204/205 (the lock's remap targets)
are 1x1 dummies in stock, so the lock has no light art and none
is added. Entries 427..432 are pixel-identical copies of the dark
art in stock (same histograms, same 0x2945 ground); the set
preserves that invariant by emitting the same redrawn art there.
Entries 309/310 are genuine per-theme art (black glyph on white).
The light battery frames are 27 px wide (316 is 28) against the
dark set's 26, with the outline inset by one pixel; each resource
keeps its own stock dimensions and byte length.

Battery frames: bars sit in four measured slots, columns
(3..6, 8..11, 13..16, 18..21), rows 3..10, in green 0x368B; the
dark set's one-bar frame (146, and charging 151) uses amber
0xFE00, the light set's one-bar frame uses green, both as stock.
The charging frames' 0xF800 field is stock's own convention for a
keyed draw on another screen (the keyed-helper control in
test_browser_opaque.py emits exactly their outline and bars).
Which frames the Service draw at 0x0307DB60 can reach depends on
the writer of the halfword at 0x03023144, which is also
the painter's text background pen; its writer was not identified
offline.

## Route decision: (b) opaque, ground-matched

Route (a) does not apply to these sites. The v4 repoint pattern
needs a draw call shaped like the keyed helpers (id, x, y);
DrawImage takes the id alone and reads its position from the
display context, and the helper's sites set up no coordinates in
r1/r2. There is also nothing to repoint the list rows to: they
draw no resources.

Route (b) it is, with one evidence-driven refinement. The brief
for (b) presumes the icons sit on the palette background; the
stock surrounds say otherwise for most families. The status
families were authored on a fixed 0x2945 ground in both themes,
the battery frames on their own fields, and only the small
play/pause pair sits on the palette background (0x0000 dark,
0xFFFF light). Setting the surrounds to the palette cells would
leave a visible rectangle around every status icon. The set
therefore keeps each resource's own measured stock ground, which
is what "sits invisibly the way stock's does" requires. The
opacity gate below proves the ground is precisely what lands on
the panel, so ground matching is the whole requirement.

Scroll behaviour needs no proof under (b): rows are erased by
fills (the 0x03063570(2) background repaint and the per-row band
fills), never by icon transparency, and this set changes no draw
code and no list resource (there are none).

## Art spec

Generator: generate_browser_icons.py (deterministic; 8x
supersampled primitive canvas, box downscale to coverage, with the
antialiasing baked into the pixels). Coverage under 1/16 is the
pixel's ground (or the 0xF800 key), 15/16 or more is the ink, and
partial coverage is the ink blended toward the ground. These
resources are drawn opaque (route (b)), so that blend is exact. Over
a key it blends toward a fixed target instead (see the keyed set
below). Bare filled glyphs:
padlock (accent 0xF220, the state colour stock marks hold with),
pause bars, play triangle, headphones (band and filled pads),
document with X, filled document with a 1 cutout, clock disc
with hand cutouts, battery shell (rounded, stock 2 px wall, rounded
terminal) with bar slots. Ink 0xFFFF on
the dark set, 0x0000 on the light set; battery bars keep the
stock state colours above. The five blank resources (38, 261,
265, 427, 431) are solid ground, byte-identical to stock by
design. Every resource keeps its exact stock dimensions and byte
length.

Keyed set (added with the baked antialiasing): five two-colour stock
sprites redrawn inside their stock footprint, with the 0xF800
surround kept. Black mini pause/play 189/190 (dark) and 355/356
(light) blend toward light grey 0xC618, because a black glyph only
reads on a light surface. The speaker 298 is the light-theme twin
of 132 and blends toward the white light-theme ground.

Contact sheets: sheets/stock_vs_browser_3x_dark.png and
sheets/stock_vs_browser_3x_light.png (stock left, new right, 3x).

## Gates and results

- Pixel audit (runs inside the generator): every replaced
  resource uses only its declared colours (ink, ground or field,
  bar colour) and baked blends of the ink toward them; only keyed
  frames contain the key; blanks are pure ground; battery bar
  column runs match the frame's level.
  Pass.
- Opacity emulation (test_browser_opaque.py, the prove_keying.py
  harness pattern on real module 0 code): DrawImage emits every
  pixel in exact sequence for resources 39, 143, 150, 262, 266,
  stock art and redrawn art alike (255/255, 144/144, 364/364,
  342/342, 324/324). Control: resource 150 through the keyed
  helper emits exactly its 144 non-key pixels. Pass.
- Validation build (test_browser_build.py): the default build
  still hashes to the pinned
  92c446066e715d74a719671d3ee643ed4b7587c94801eb6dc3893f2271ed944d.
  A build with the v4 manifest (default patches plus the eight
  transport repoints) and a merged theme config (v4 runs plus
  the 300 browser runs) produces image SHA-256
  6f83979834998c231cdd598ac20379fcab00606de44a8d038b49fa4cbedf3dca,
  in which all 43 browser resources and all 54 v4 resources match
  their .bin files byte for byte. Pass.
- No interference: the v4 keyed transport gates
  (../test_keyed_transport.py) re-run after this set was added;
  every gate line is identical to the pre-change baseline run.
  Pass.

## Integration note

Art only; no patches, no manifest changes, no repoints. The full
build's theme merge gains the runs from browser-glyphs.json (300
runs) alongside the CE mark and the v4 runs; build.py refuses
overlapping claims, and the validation build above proves this
merge. Files the integrator must take from this directory:

- browser-glyphs.json (the deliverable the merge consumes)
- icon_set_browser/ (the .bin art and mapping.json, provenance
  and the byte-exactness reference for the build gate)
- generate_browser_icons.py (regenerates the art, the runs and
  the sheets deterministically)
- test_browser_opaque.py, test_browser_build.py (the gates)
- design_browser.md (this document)

## Open points

- The status helper at 0x0307E804 has no static caller; whether
  and where the firmware invokes it at runtime, and at what
  positions, is a Phase E on-device question. If it proves dead,
  the five status families are inert and the battery gauge is
  the set's only live member; the art is correct either way
  because it is ground-matched per resource.
- The writer of the battery index cell 0x03023144 was not
  identified; which of the ten frames per theme the opaque
  Service draw reaches is therefore stated as a range, not a
  single frame.
