# Rebuild dependency + artifact hashes

`transplant.py` in this directory rebuilds the Opus module 72
deterministically from the pinned stock image plus berettavexee's
BSD-3-Clause patch file, and `patches/framework/build.py` applies
it as the `opus72` transplant step (opt-in; see README.md here
for the variant build command). Paths to the input resolve via
`--ecpatch-dir` / `FOSI_ECPATCH_DIR` / discovery
(tools/fosi_paths.py); nothing is hard-coded.
The .ecpatch file is binary, and this repo's push channel is
text-only, so it is not stored here. Source:

- Repo: https://github.com/berettavexee/echo-mini-opus
  (commit 7d727fd4f30e68fecbf6566d3c3e64213e56e7f7, 2026-10-17)
- patch/HIFIEC52.ecpatch (the optimised Opus-only build:
  fixed-point libopus 1.5.2 plus a minimal Ogg demuxer, linked
  into the WMA library's freed regions): SHA-256
  acad5a624aacdceb3868a118b56959260f08ee9600ac5378d9f516e0872ccd03

HIFIEC52 contains no Vorbis surgery (that is HIFIEC56, used by
patches/vorbis_swap/ and not used here), so every byte it changes
inside the Echo Mini module 74 file range is an Opus plug-in
byte.

Expected output of a correct rebuild:

- module 72 (code + data, 117,376 bytes): SHA-256
  6a7d50d2647c6623181e3cbbc16a13d2bd9a8724559d62c84f25b83ae8cbb07d
  (84,231 surgery bytes; the kept runtime regions stay
  byte-identical to stock, audited by transplant.py on every run)

Correction (2026-10-31): the hash first pinned here,
abc98c1163985de677dc0d9da200e8c1986d769b57fa594e2e066b6ed4707a5d,
was the output of a defective construction. transplant.py
erased the freed regions before writing the diff bytes, and
because an ECPATCH is a sparse diff, the 630 bytes where the
plug-in coincides with the Echo stock library were zeroed;
that module faults on open. Offline harness validation caught
the defect before merge. The corrected transplant.py writes
the diff onto the stock bytes without erasing, and its output
is byte-identical to the harness control build that passed
every validation step. Do not use the old hash, or any module
built by the erase-first construction.

Licences: project surgery BSD-3-Clause (berettavexee); libopus
(C) Xiph.Org Foundation and contributors, BSD-style.
