# DAP Neo theme editor

Status: the editor page, the catalog tooling, and the framework
build step are in the tree. `build.py --theme-config` applies an
exported theme after the manifest patches and the transplants, and
`verify.py` check 10 covers the default build, the example theme,
the CE splash mark, and the refusals. The CE splash mark ships as
`ce-mark.json` in this directory as a runs-only config. Literal
code sites are still not themeable because the approved-site
registry is empty. Rule sources keep the studio's little-endian
naming, and replacement colours are written big-endian, the order
the panel displays (see the word convention below).

## What is here

The browser page lives in [`docs/index.html`](../../docs/index.html)
(with `docs/theme.js`, `docs/theme.css`, `docs/theme-core.mjs`, and
the builder files `docs/builder.js`, `docs/builder-core.mjs`, and
the generated builder data modules). It is both the theme editor
and the CE builder. The tree carries a `Publish theme studio` workflow
(`.github/workflows/pages.yml`) that deploys `docs/` to GitHub Pages
on pushes to main that touch `docs/`, and skips if the page is absent.
Whether that workflow has completed a deployment is not recorded in
the tree. The page can also be served locally:

```sh
python3 -m http.server 8000 --directory docs
# Open http://localhost:8000
```

The player mockup includes a local-artwork theater preview with a
contrast-checked RGB565 ground, transparent text backgrounds, and a
one-pixel contrasting edge. Its transport icons use vectors instead of
system-dependent text glyphs. The preview is not a firmware patch and
does not change the stock font. The remaining device work is listed in
[`theater_mode.md`](../design_refresh_v2/theater_mode.md).

The page uses only HTML, CSS and JavaScript. It has no remote services,
dependencies or telemetry. The 240 by 320 playback, library and settings
screens in the page are **approximate mockups**, not pixel-perfect
captures. The colors update as you edit them. For actual firmware
artwork, select your original `DP3_V137.img` in the browser. The page
verifies its SHA-256, reads the 456 RGB565 resource records, lets you
compare original and edited pixels, and can project a selected bitmap
over the mock screen at its stored coordinates. The firmware file never
leaves the browser.

The editor exports a `dap-neo-theme.json` file. It **does not write or
flash firmware**. Only explicitly selected RGB565 source words are
recolored. The exported JSON includes exact per-asset pixel counts.
Black (`0x0000`) and `0x00F8` are blocked in the browser because they
may be transparency or background key values. Neither interpretation is
claimed proven.

The same page now also carries the CE builder: feature toggles,
theme application from the live editor state, a CE mark toggle, and
a gated-features list. It patches the verified stock image in the
browser and downloads the finished image; an offline test in
`tests/builder.test.mjs` proves its outputs byte-for-byte against
`build.py`, including the pinned unified build with the Vorbis
transplant on. The page also accepts locally generated, hash-checked
Opus, Bluetooth and standalone lock-screen payloads; their device
validation gates and build commands are shown next to the controls. The
combined M3U/lock-screen build is disabled until playlist start and exit
transitions are implemented and verified.

## The build consumer

The build step this file used to wait for has landed.
`build.py --theme-config THEME.json` applies an exported theme after
the manifest patches and the transplants, before the single finalize:
per-resource exact-colour recolors whose counts must match the
export's `expected_count` exactly, and raw `runs` edits
({offset, expect, replace}) for changes that are not recolors. The CE
splash mark ships as a runs-only config, `ce-mark.json` in this
directory. Theme edits refuse on any overlap with an earlier
modification, on a count mismatch, and on a runs entry whose expected
bytes do not match; `--theme-config` with `--recovery` is refused.
`verify.py` check 10 pins all of it: the default build unchanged, the
example theme's diff confined to resources 6 to 10 at exactly 32,760
bytes, the CE mark diff at exactly its 496 bytes, and the refusals.

Two things remain open. Literal code sites are still not themeable:
the APPROVED_LITERAL_SITES registry in `tools/ui_theme.py` is empty,
and the build refuses a config whose `literal_sites` list is
non-empty; approving the palette sites the colour census pinned is a
separate decision. The word convention: the studio names resource
words little-endian and its counts hold under that reading, while the
colour census proved from decoded renders, and the emulated player
painter confirms (`tools/gen_sim_data.py`), that the panel displays
the stored bytes big-endian. So a rule's source stays in the studio's
naming, but the build writes the replacement palette colour
big-endian, and the studio's previews show pixels in panel order.
Builds before this change wrote the replacement little-endian, which
would have shown on the panel byte-swapped.

Device boot and color and transparency behavior remain untested either
way: nothing in this project has been flashed.

## What the editor knows

The firmware contains 456 uncompressed little-endian RGB565 bitmap
records. Each record's ID, dimensions, x/y, file offset and top colors
are exported by the catalog tool:

```sh
python3 tools/ui_theme.py /path/DP3_V137.img catalog /tmp/neo-catalog
python3 tools/ui_theme.py /path/DP3_V137.img preview \
  dap-neo-theme.json /tmp/neo-preview
```

The resource table does not provide a reliable semantic role for every
asset. Unidentified assets are labeled *unclassified*, not assigned
speculative names.

Some UI colors are computed in drawing code rather than stored as
bitmaps. The command below lists **unverified literal candidates**
and their module addresses:

```sh
python3 tools/ui_theme.py /path/DP3_V137.img scan-literals 0xFFFF 0xA210 \
  --output /tmp/literal-candidates.json
```

The generated list is not a safe patch map. Code and data bytes can
coincidentally equal an RGB565 word. `tools/ui_theme.py` therefore
has an explicit `APPROVED_LITERAL_SITES` registry, currently empty.
A site must be traced to the display renderer and reviewed before it
can be used in `literal_sites`. No generic raw-byte replacement is
allowed.

## Validation

```sh
node --test tests/theme-core.test.mjs
FOSI_STOCK_IMAGE=/path/DP3_V137.img \
  python3 -m unittest discover -s patches/theme_editor -p 'test*.py' -v
FOSI_STOCK_IMAGE=/path/DP3_V137.img \
  python3 patches/framework/verify.py
```

The tests check resource metadata, exact-color replacement,
confined diffs, refusal of mismatched counts and overlapping edits,
and PNG previews.

The example `theme.example.json` recolors the `0xA210` pixels
of image resources 6 to 10. Its original counts (6,060, 4,668, 3,276,
1,884 and 492) were verified against the pinned stock image.
These are useful test fixtures, not a claim about all rendered colors
on the device.
