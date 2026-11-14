# Live format-error diagnostics

`tools/runtime_diagnostics.py` creates an opt-in diagnostic image from
Standard CE. It replaces the format-error text with a compact live readout
and captures the activated browser item's class and three-byte extension.
The normal release image is unchanged. It does not change decoding,
classification, automatic skipping or clock settings.

```sh
python tools/runtime_diagnostics.py \
  --input release/DP3_V137_CE.img --output /path/to/new-diagnostic.img
```

The output and its `.diagnostics.json` sidecar must not already exist.
Unexpected bytes or occupied code pockets are refused. Date ordering,
recovery preparation and installation still follow [FLASH_REVIEW.md](FLASH_REVIEW.md).
This utility does not enumerate or write to a device.

For example, a format-error popup might show:

```text
CE:OPU opu 06 FF FF 6F
```

| Field | Meaning |
| --- | --- |
| First three letters | Live resident browser audio-table extension |
| Next three letters | Last activated browser item's short extension |
| First hex pair | Last browser item's class: `00` directory (extension shown as `---`), `01` audio, `06` unrecognized/all-files |
| Second hex pair | Current codec ID; `01` selects the transplanted Opus decoder |
| Third hex pair | Raw per-open marker; its success/error semantics are not established |
| Fourth hex pair | First byte of the captured extension: `4F` is uppercase O, `6F` lowercase o |

Browser fields describe the last browser activation, even if a later error
comes from the library. A codec ID outside `00` through `09` can be stale
or uninitialized before codec selection; it is not itself a decoder error
code. Short text buffers and every other resource ID retain their original
lookup path. This distinction prevents a raw marker from being mistaken
for a diagnosed cause.

Only three extension bytes and one class byte are captured in reserved
settings workspace after the theater and focus state. They may persist
when stock settings are saved. No filename, path, media content, serial
number or host information is captured. The sidecar contains image hashes
and field definitions, not a device capture.

Tests execute the actual diagnostic instructions with guarded buffers,
check the displaced browser instruction and calling convention, and verify
that existing inputs/outputs are protected:

```sh
python -m unittest discover -s tests -p test_runtime_diagnostics.py -v
```

The short repair gate also tests browser admission, codec-module selection
and 3,840 initial PCM frames from a generated silence stream. These modeled
checks and a live readout are complementary; neither substitutes for
successful physical playback.
