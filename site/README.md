# Site pictures (Stageshow)

The illustrations on the Pages site (`docs/`) are built here with
[Stageshow](https://github.com/benjitaylor/skills/tree/main/stageshow), Benji
Taylor's skill and React kit for faux product UI. The kit is vendored in
`src/kit/` (MIT; see `src/kit/README.md` for the commit and the two changes).

- `src/hero/`: the hero demo, the install in one loop. The update file is
  carried into the player's storage, the copy row fills, and the read-back
  check rises beside it: `SHA-256 matches` over the Standard image's hash.
  Copied from the Stageshow gold `upload`. A compact design for phone columns.
- `src/features/`: the "What CE changes" bento. One Stage per tile picture at
  the tile's width; the tile copy is page HTML in `docs/index.html`. Theater
  mode (grounds by the firmware's rule), the Vorbis stat, a fitted EQ curve,
  natural sort and the Bluetooth key. Copied from the Stageshow gold `bento`.
- `src/main.tsx`: mounts them into `#ce-hero-stage` and the `[data-picture]`
  slots, following the page's color scheme.

The page itself (`docs/theme.css`) uses the same tokens: the kit's neutral
surfaces, three inks, one accent, its radii and shadows, light and dark.

## Build

```sh
cd site
npm ci
npm run typecheck
npm run build      # writes docs/stage/stage.js and docs/stage/stage.css
```

The bundle is committed so Pages needs no build step. It is reproducible:
CI (`.github/workflows/ci.yml`) rebuilds it and fails on any difference, so
change `src/` and rebuild together.

## Checks

`tests/site-comparison.test.cjs` mounts every picture in light and dark. The
pictures were rehearsed with Stageshow's own film script and gate, from a
checkout of the skill with the site served on port 8765:

```sh
CHROME_PATH=/path/to/chrome node scripts/film.mjs http://127.0.0.1:8765/ \
  --select '#ce-hero-stage' --gate --width 1280            # also --width 390, --dark
CHROME_PATH=/path/to/chrome node scripts/film.mjs http://127.0.0.1:8765/#features \
  --select '.tile-picture' --gate --count 12 --width 1280  # also --width 390, --dark
```

All eight runs end `rehearsal passed`.
