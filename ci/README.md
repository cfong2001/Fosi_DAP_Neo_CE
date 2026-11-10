# GitHub Actions

Four workflows live in `.github/workflows/`. They require no repository secrets.

## Source CI: `ci.yml`

Runs on pull requests to `main` and `codex/**` branches, pushes to `main`,
and manual dispatch:

- Python syntax compile over `tools/` and `patches/`.
- Patch-file grammar, manifest entry existence.
- Natural-sort reference vectors and consistency fuzz (4,000 pairs).
- The M3U C parser host test suite, compiled using the runner's C compiler.
- The combined build's parser and mocked bridge host suites, plus a static
  budget and collision census over recorded layouts and the pinned stock
  image. The census lists stock code/data/BSS intersections; it does not
  prove runtime coexistence. Recorded-layout budget checks run without the
  stock image; the module-boundary census requires it. The bridge test uses
  mocked firmware calls and does not exercise playback or build an image.
  Combined steps skip when their source tree is absent.
- Embedded combined-build bytes are checked against recorded component
  hashes and budgets. Negative tests reject corrupt payloads and layouts.
  The independent `patches/full/growth-ledger.json` lists the expected
  modules, lengths and hashes; intentional changes must update the ledger
  and embedded payloads together. This is not proof of source equivalence.
  This compares recorded artifacts; it does not prove a source rebuild,
  runtime coexistence or device behavior.
- Browser theme tests if the theme editor files exist (including on PR #10).
- On Linux x86_64, install the hash-verified reference compiler and
  recompile module 31 when the pinned stock image is present; compare the
  result against both the recorded layout and the browser payload. See
  [REFERENCE_BUILD.md](REFERENCE_BUILD.md) for the exact toolchain and scope.
- Theater preview contrast and transparent-artwork tests after RGB565 quantization.
- The standalone RGB565 top-third averaging component's host tests.
- Theme Python test discovery if present, plus browser-builder parity tests when the stock image is available. Image-dependent tests are skipped when the image is absent.

The hosted run checks out the repository and therefore sees `DP3_V137.img` when it is tracked. It does not obtain third-party `.ecpatch` files or run flashing commands. A green check does not establish full framework verification, decoder behavior, or hardware safety. The optional Opus browser parity case requires locally generated range data and is not run in hosted CI.

For full image-level verification, run the existing verifier on a trusted local machine using your licensed original image and independently obtained third-party files:

```sh
FOSI_STOCK_IMAGE=/absolute/path/DP3_V137.img \
FOSI_ECPATCH_DIR=/absolute/path/to/ecpatch-inputs \
python3 patches/framework/verify.py
```

This exercises the SHA gate, known byte diffs, recovery mode, and unified image reproducibility.

## Firmware build and release: `firmware.yml`

Runs on pull requests to `main`, pushes to `main`, `v*` tags and manual
dispatch. It fetches the two hash-pinned decoder inputs
(`ci/fetch_decoder_inputs.sh`), installs the reference toolchain, and then:

- runs `patches/framework/verify.py` (all 13 checks);
- builds the release set with `ci/build_release.sh`, which refuses any
  image that differs from its pin;
- checks that the three images in `release/` (standard, minimal and
  recovery) are byte-identical to the rebuild;
- runs the everything build's playlist, theater, transport and Bluetooth
  emulation suites against the rebuilt image, and rebuilds the standalone
  theater and focus variants with their suites;
- uploads the images as a 30-day workflow artifact.

A `v*` tag also creates a GitHub prerelease with the images, the build
report and `SHA256SUMS`, using `release/RELEASE_NOTES.md` as the text.

The repository is private and already tracks the stock image, so built
images are kept in `release/`, workflow artifacts and private releases.
They must never be published to Pages; `pages.yml` refuses any `.img` or
`.ecpatch` under `docs/`. If the repository is ever made public, revisit
whether the stock image and derived images may be redistributed.

To change an image on purpose: rebuild with `ci/build_release.sh`, update
the pin in that script and in `patches/framework/verify.py`, and replace the
files and `SHA256SUMS` in `release/` in the same pull request.

## Browser marquee: `marquee.yml`

Rebuilds the standalone browser-marquee payload, checks it against its pin,
and runs the v1 to v4 marquee emulator suites.

## Pages: `pages.yml`

After the theme editor PR is merged to `main`, navigate to **Settings > Pages** and choose **Build and deployment > Source > GitHub Actions**. The workflow publishes `docs/` when those files change or when manually dispatched. It refuses to publish if the static site is absent or proprietary `.img`/`.ecpatch` files are present in `docs/`.

Publishing the site is separate from source CI: deployment does not imply firmware safety. The site operates on a user-selected local firmware file and exports JSON; it does not distribute stock firmware.

The repository is private; check whether its GitHub Pages visibility and plan are appropriate before enabling the site. A Pages site can be publicly reachable even if its repository is private.

## Require CI before merging (optional)

After the first successful run, use repository **Settings > Rules > Rulesets** (or branch protection) to require the `Static checks and host tests` job for merges to `main`. This setting is not changed by the workflow PR itself.

Do not give untrusted pull request jobs access to a self-hosted runner containing proprietary firmware or device-writing capabilities.

