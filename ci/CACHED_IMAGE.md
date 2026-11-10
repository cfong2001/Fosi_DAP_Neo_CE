# Reproducing the cached combined image

This is an offline binary-reproduction check for the payloads already
embedded in the browser builder. It **does not compile the corresponding
source** or prove that the embedded code corresponds to the current source.
The combined image has known unresolved theater, playlist and redraw defects;
a matching hash does not make it ready to install. Device capacity, firmware
updates, playback and recovery remain unverified on hardware.

Prerequisites: Node.js and Python 3, the pinned stock V137 image and the local
decoder inputs used by `patches/opus_swap/transplant.py`. Generate local Opus
range data with the `--opus-data-only` mode of `docs/generate_builder_data.py`
in the separate build-safety workstream, then pass the three local paths:

```sh
python3 docs/generate_builder_data.py --stock /path/to/DP3_V137.img \
  --ecpatch-dir /path/to/decoder-inputs --opus-data /path/to/new-opus.json --opus-data-only
node ci/build_cached_full.mjs /path/to/DP3_V137.img /path/to/new-opus.json /path/to/new-output.img
```

Both outputs must be new paths. Do not distribute decoder range data or the
generated firmware image. The assembler checks the stock hash, embedded tail
and module payload hashes, decoded Opus module hash, and the final image hash.
It uses exclusive output creation to refuse existing files and links. A hash
check establishes identity with a previously recorded binary, not safety or
equivalence between source code and binary.

The host test runs without proprietary inputs and checks refusal of an invalid
stock image, as well as exclusive output creation for ordinary files,
symbolic links and hard links. With the inputs available, it also checks the full hash
and that existing output and input aliases cannot be overwritten:

```sh
node --test tests/test_cached_full.test.mjs
DAP_NEO_STOCK=/path/to/DP3_V137.img DAP_NEO_OPUS_DATA=/path/to/new-opus.json \
  node --test tests/test_cached_full.test.mjs
```
