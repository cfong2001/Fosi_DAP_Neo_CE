# Browser marquee emulator checks

The `Browser marquee emulator` workflow regenerates the standalone v5 payload
with pinned Keystone, Capstone and Unicorn versions, checks the payload hash
(`513b3844…`) and the checked-in hooks, and runs the v1, tags, v3 and v5
emulator suites against a stock-decoder build. It needs the pinned V137 image
in the checkout and fails on a missing or mismatched one. It needs no decoder
patch inputs. The v5 suite also needs Pillow for its cover fixtures.

The test variant is built the way `design.md` (Accounting) records it: the
payload as a module 31 growth and the 2,044-byte zero tail from
`marquee_tail.bin`, which holds the slice line buffer at runtime. Both images
are pinned: with decoder transplants `c58e51b5…` (the design record), with
`FOSI_MARQUEE_NO_TRANSPLANTS=1` `320ba607…`. The v4 thumbnail suite was
retired with the thumbnail hooks it tested; v5 replaced them.

These checks cover the UI code under emulation, not the optional decoder
transplant, the everything build or device behavior. The marquee does not fit
in the everything build; `patches/full/README.md` lists what would make room.

From the repository root, after installing the versions in the workflow:

```sh
python patches/browser_marquee/build_marquee.py
FOSI_MARQUEE_NO_TRANSPLANTS=1 python patches/browser_marquee/test_browser_marquee.py
FOSI_MARQUEE_NO_TRANSPLANTS=1 python patches/browser_marquee/test_browser_marquee_tags.py
FOSI_MARQUEE_NO_TRANSPLANTS=1 python patches/browser_marquee/test_browser_marquee_v3.py
FOSI_MARQUEE_NO_TRANSPLANTS=1 python patches/browser_marquee/test_browser_marquee_v5.py
```

Without the environment variable the suites build the unified variant and
need the decoder inputs through `FOSI_ECPATCH_DIR`. Hardware timing, memory
residency and interaction with playback remain open and are listed in
`design.md`.
