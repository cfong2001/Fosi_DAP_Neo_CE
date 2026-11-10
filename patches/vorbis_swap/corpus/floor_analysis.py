#!/usr/bin/env python3
"""Identify the transplant's float->s16 output conversion and bound its
arithmetic error.

For every corpus file: compare the transplant's s16 output against
floor(ffmpeg_float * 32768) (the conversion the {0,-1} LSB difference
histogram identifies). Where the module's pre-conversion value equals
the reference, the outputs match exactly; a mismatch is a boundary flip
caused by a sub-LSB arithmetic difference. With flip rate p and
epsilon ~ zero-mean RMS sigma (LSB units), p ~= E|epsilon| =
sigma*sqrt(2/pi), so sigma ~= p/0.798 and the implied arithmetic SNR
follows. Model-based estimate; the hard observations are the exact
match rate and the maximum deviation (never above 1 LSB).

Run:  venv/bin/python work/vorbis_corpus/floor_analysis.py
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from measure import load_f32  # noqa: E402


def main():
    manifest = json.loads((HERE / "manifest.json").read_text())
    out = []
    for entry in manifest["files"]:
        stem = Path(entry["file"]).stem
        ref = load_f32(HERE / "refs" / f"{stem}.f32")
        tst = np.fromfile(HERE / "outputs" / f"{stem}__patched.s16",
                          dtype="<i2").astype(np.float64).reshape(-1, 2)
        n = min(len(ref), len(tst))
        ref, tst = ref[:n], tst[:n]
        fl = np.clip(np.floor(ref * 32768.0), -32768, 32767)
        d = tst - fl
        flip = float(np.mean(d != 0))
        sigma = flip / 0.798  # LSB units
        sig = float(np.mean(ref * ref))
        snr_arith = 10 * np.log10(sig / (sigma ** 2 / 32768.0 ** 2)) if sigma > 0 else 300.0
        row = {"file": entry["file"], "source": entry["source"],
               "quality": entry["quality"], "rate": entry["rate"],
               "floor_exact_pct": round(100 * (1 - flip), 3),
               "max_dev_lsb": int(np.abs(d).max()),
               "flip_pct": round(100 * flip, 3),
               "sigma_lsb": round(sigma, 4),
               "snr_arith_est_db": round(snr_arith, 1)}
        out.append(row)
        print(row["file"], "exact", row["floor_exact_pct"], "% maxdev",
              row["max_dev_lsb"], "sigma", row["sigma_lsb"],
              "arith_est", row["snr_arith_est_db"], "dB", flush=True)
    (HERE / "floor_results.json").write_text(json.dumps(out, indent=1))
    est = [r["snr_arith_est_db"] for r in out]
    print("arithmetic SNR estimate: min", min(est), "median",
          float(np.median(est)), "max", max(est))


if __name__ == "__main__":
    sys.exit(main())
