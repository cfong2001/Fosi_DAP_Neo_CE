# Stageshow kit (vendored)

The React kit from Benji Taylor's Stageshow skill,
https://github.com/benjitaylor/skills (`stageshow/kit/`), at commit
299140fafd08df55a9c234e610c3f64af3f45531 (2026-11-04). MIT licensed; see
`LICENSE` here. The rest of this repository is GPL-3.0.

Changes from upstream:

- `brands/`, `parts/BrandMark.tsx` and `parts/BrandMark.css` are not
  included: the brand marks carry third-party artwork under their own
  terms, and this site uses none of them. `parts/index.ts` no longer
  exports `BrandMark`, and `stageshow.css` no longer imports its stylesheet.
- `index.ts` (the barrel, which re-exports the brand marks) is not
  included; the site imports each part from its own module.

Nothing else is modified. To update, copy `stageshow/kit/` again and repeat
the changes above.
