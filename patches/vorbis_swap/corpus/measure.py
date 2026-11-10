#!/usr/bin/env python3
"""Measure the corpus: align each module decode to the ffmpeg float
reference and decompose the error.

Metrics per (file, decoder), over the aligned intersection, both
channels pooled, float64:
  snr_total_db   test (s16 -> float) vs ffmpeg float decode.
                 This is the performance plan's finish-line metric.
  snr_s16ceil_db round-to-s16(ffmpeg float) vs ffmpeg float: the pure
                 output-quantisation ceiling of a 16-bit interface for
                 this exact signal.
  snr_grid_db    test vs round-to-s16(ffmpeg float): decoder arithmetic
                 differences as delivered on the 16-bit grid.
  snr_arith_db   implied arithmetic-only SNR from power subtraction,
                 P_arith = P_total - P_quant (proxy; see doc).
  enc_floor_db   ffmpeg float decode vs lossless source (encoder loss,
                 identical for every decoder of the same file).
Alignment: full-signal FFT cross-correlation on the mixdown, lag search
+/-4096 samples, top candidate lags disambiguated by measured SNR.
Nothing is assumed from prior runs; every lag is measured per file.

Run:  venv/bin/python work/vorbis_corpus/measure.py
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REFS = HERE / "refs"
MAXLAG = 4096


def load_f32(p):
    return np.fromfile(p, dtype="<f4").astype(np.float64).reshape(-1, 2)


def load_s16(p):
    return np.fromfile(p, dtype="<i2").astype(np.float64).reshape(-1, 2) / 32768.0


def ref_decode(ogg: Path) -> np.ndarray:
    REFS.mkdir(exist_ok=True)
    out = REFS / (ogg.stem + ".f32")
    if not out.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(ogg),
                        "-f", "f32le", "-ac", "2", str(out)], check=True)
    return load_f32(out)


def find_lag(ref, test):
    """lag L with test[i] ~= ref[i+L], L in [-MAXLAG, MAXLAG]."""
    r = ref[:, 0] + ref[:, 1]
    t = test[:, 0] + test[:, 1]
    n = 1
    while n < len(r) + len(t):
        n <<= 1
    R = np.fft.rfft(r, n)
    T = np.fft.rfft(t, n)
    corr = np.fft.irfft(R * np.conj(T), n)  # corr[L] = sum_i r[i+L] t[i]
    idx = np.concatenate([np.arange(0, MAXLAG + 1),
                          np.arange(n - MAXLAG, n)])
    vals = corr[idx]
    lags = np.concatenate([np.arange(0, MAXLAG + 1),
                           np.arange(-MAXLAG, 0)])
    order = np.argsort(vals)[::-1]
    cands = []
    for j in order:
        L = int(lags[j])
        if all(abs(L - c) > 8 for c in cands):
            cands.append(L)
        if len(cands) >= 5:
            break
    best, best_snr = None, -1e18
    for L in cands:
        s = snr_at(ref, test, L, stride=7)
        if s is not None and s > best_snr:
            best, best_snr = L, s
    return best


def window(ref, test, L):
    """Slices (ref_seg, test_seg) for lag L (test[i] ~ ref[i+L])."""
    i0 = max(0, -L)
    j0 = max(0, L)
    n = min(len(test) - i0, len(ref) - j0)
    if n <= 0:
        return None
    return ref[j0:j0 + n], test[i0:i0 + n]


def snr_at(ref, test, L, stride=1):
    w = window(ref[::1], test[::1], L)
    if w is None:
        return None
    a, b = w
    a, b = a[::stride], b[::stride]
    e = a - b
    pe = float(np.sum(e * e))
    if pe == 0.0:
        return 300.0
    return 10 * np.log10(float(np.sum(a * a)) / pe)


def quant16(x):
    return np.clip(np.rint(x * 32768.0), -32768, 32767) / 32768.0


def analyse(ref, test):
    L = find_lag(ref, test)
    a, b = window(ref, test, L)
    q = quant16(a)
    sig = float(np.sum(a * a))
    err_tot = a - b
    err_q = a - q
    err_g = q - b
    p_tot = float(np.sum(err_tot * err_tot))
    p_q = float(np.sum(err_q * err_q))
    p_g = float(np.sum(err_g * err_g))
    p_arith = p_tot - p_q
    # In-range view: the float reference can overshoot 0 dBFS on low-q
    # encodes of loud sources; every s16 output clips those samples, so
    # the plain total conflates clipping with decoder error there.
    # Mask to samples with |ref| <= 1.0 and recompute without clipping.
    mask = np.abs(a) <= 1.0
    am, bm = a[mask], b[mask]
    qm = np.rint(am * 32768.0) / 32768.0
    sig_m = float(np.sum(am * am))
    p_tot_m = float(np.sum((am - bm) ** 2))
    p_q_m = float(np.sum((am - qm) ** 2))
    return {
        "lag": L, "n_common": int(len(a)),
        "ref_rms_dbfs": round(10 * np.log10(sig / a.size), 2),
        "snr_total_db": round(10 * np.log10(sig / p_tot), 2) if p_tot else 300.0,
        "snr_s16ceil_db": round(10 * np.log10(sig / p_q), 2) if p_q else 300.0,
        "snr_grid_db": round(10 * np.log10(sig / p_g), 2) if p_g else 300.0,
        "snr_arith_db": round(10 * np.log10(sig / p_arith), 2) if p_arith > 0 else None,
        "grid_diff_pct": round(100.0 * float(np.mean(b != q)), 3),
        "grid_rms_lsb": round(float(np.sqrt(np.mean((err_g * 32768.0) ** 2))), 3),
        "ref_peak": round(float(np.max(np.abs(a))), 4),
        "ref_over_pct": round(100.0 * float(np.mean(~mask)), 4),
        "snr_total_ir_db": round(10 * np.log10(sig_m / p_tot_m), 2) if p_tot_m else 300.0,
        "snr_s16ceil_ir_db": round(10 * np.log10(sig_m / p_q_m), 2) if p_q_m else 300.0,
    }


def main():
    manifest = json.loads((HERE / "manifest.json").read_text())
    rows = []
    for entry in manifest["files"]:
        ogg = HERE / "corpus" / entry["file"]
        stem = ogg.stem
        ref = ref_decode(ogg)
        src = load_f32(HERE / "corpus" / entry["source_raw"])
        enc = analyse(src, ref)  # ref measured against the lossless source
        row = {"file": entry["file"], "source": entry["source"],
               "quality": entry["quality"], "rate": entry["rate"],
               "ref_frames": int(len(ref)),
               "enc_floor_db": enc["snr_total_db"], "enc_lag": enc["lag"]}
        for mod in ("stock", "patched"):
            outp = HERE / "outputs" / f"{stem}__{mod}.s16"
            if not outp.exists() or outp.stat().st_size < 0.9 * len(ref) * 4:
                row[mod] = {"status": "decode_failed",
                            "test_frames": int(outp.stat().st_size // 4)
                            if outp.exists() else 0}
                print(stem, mod, "DECODE FAILED (see emu_runs.json)", flush=True)
                continue
            test = load_s16(outp)
            m = analyse(ref, test)
            m["test_frames"] = int(len(test))
            m["status"] = "ok"
            row[mod] = m
            print(stem, mod, "lag", m["lag"], "total", m["snr_total_db"],
                  "ceil", m["snr_s16ceil_db"], "grid", m["snr_grid_db"],
                  "arith", m["snr_arith_db"], flush=True)
        rows.append(row)
    (HERE / "results.json").write_text(json.dumps(rows, indent=1))
    flat = []
    for r in rows:
        for mod in ("stock", "patched"):
            flat.append({"file": r["file"], "source": r["source"],
                         "quality": r["quality"], "rate": r["rate"],
                         "decoder": mod, "enc_floor_db": r["enc_floor_db"],
                         **r[mod]})
    with open(HERE / "results.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(flat[0].keys()))
        w.writeheader()
        w.writerows(flat)
    print("wrote results.json / results.csv:", len(flat), "rows")


if __name__ == "__main__":
    sys.exit(main())
