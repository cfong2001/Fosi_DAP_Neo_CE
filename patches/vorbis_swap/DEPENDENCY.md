# Rebuild dependency + artifact hashes

`build_image.py` rebuilds `DP3_V137_vorbis.img` deterministically from
the pinned stock image plus berettavexee's BSD-3-Clause patch files.
The same inputs feed the unified build (`patches/framework/build.py`,
transplant step `vorbis75` via `transplant.py`), which combines this
module with the DAC and clock patches into one image. Combined
SHA-256 `15990d8d9d7378e073597bb422388451384ca05d07325c9fc078245fad097b22`
(dated 2026-10-23), verified by `patches/framework/verify.py` check 7.
Paths to these inputs resolve via `--ecpatch-dir` / `FOSI_ECPATCH_DIR`
/ discovery (tools/fosi_paths.py); nothing is hard-coded.
Those .ecpatch files are binary, and this repo's push channel is
text-only, so they are not stored here. Source:

- Repo: https://github.com/berettavexee/echo-mini-opus
  (commit 7d727fd4f30e68fecbf6566d3c3e64213e56e7f7, 2026-10-17)
- patch/HIFIEC52.ecpatch (Opus-only baseline used to isolate the
  Vorbis surgery): SHA-256
  acad5a624aacdceb3868a118b56959260f08ee9600ac5378d9f516e0872ccd03
- patch/HIFIEC56.ecpatch (Opus + full-accuracy Vorbis): SHA-256
  8c31278ea9b6e730d913dbe2897ba3a126eaf156dc836a4eab09e87532903b2a

Expected outputs of a correct rebuild:

- module75_patched.bin: SHA-256
  dd8f772fb5c7fa128ed5bdfde99401cff66798847eb6c993feea89a0997ab695
  (includes the round-to-nearest output fix applied by
  transplant.py's post-step, rounding.py: 70 bytes at the four
  conversion sites and their caves; see vorbis_rounding.md. The
  transplant without the fix hashes to
  42c42796ad8f2e931c82db470cdaf754ca101a192834c11259a8bf05e787a3ca.)
- DP3_V137_vorbis.img (dated 2026-10-23): SHA-256
  aed16842d8daa569d06efdc18cd9e7eb298a0129fd38fdb2cdabaa7ec72cd10a

Licences: project surgery BSD-3-Clause (berettavexee); Tremor
(C) Xiph.Org Foundation, BSD-style. See vorbis_swap.md credits.
