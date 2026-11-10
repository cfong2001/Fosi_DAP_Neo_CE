#!/usr/bin/env python3
"""Generate the pinned Vorbis test corpus for the module-75 finish-line run.

Deterministic synthesis (numpy PCG64, fixed seeds; closed-form signals
otherwise). Sources are stereo float32, 6.0 s, peak-normalised to 0.92 FS
with 3 ms fade-in / 30 ms fade-out edges. Encoded with ffmpeg libvorbis
at q0/q3/q5/q7/q9, 44.1 kHz and 48 kHz. Writes corpus files + manifest.json.

Run with the project venv python (numpy required):
  venv/bin/python work/vorbis_corpus/gen_corpus.py
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CORPUS = HERE / "corpus"
DUR = 6.0
PEAK = 0.92
QUALITIES = [0, 3, 5, 7, 9]
RATES = [44100, 48000]
MASTER_SEED = 20261031


def edges(x, rate):
    """3 ms fade-in, 30 ms fade-out, raised cosine."""
    n = len(x)
    fi = int(0.003 * rate)
    fo = int(0.030 * rate)
    w = np.ones(n)
    w[:fi] = 0.5 - 0.5 * np.cos(np.pi * np.arange(fi) / fi)
    w[-fo:] = 0.5 + 0.5 * np.cos(np.pi * np.arange(fo) / fo)
    return x * w[:, None]


def norm_peak(x):
    p = np.max(np.abs(x))
    return x * (PEAK / p)


def sweep(rate):
    n = int(DUR * rate)
    t = np.arange(n) / rate

    def log_sweep(f0, f1):
        k = np.log(f1 / f0)
        phase = 2 * np.pi * f0 * DUR / k * (np.exp(t * k / DUR) - 1.0)
        return np.sin(phase)

    lch = log_sweep(20.0, 0.46 * rate)
    rch = log_sweep(30.0, 0.40 * rate)
    return norm_peak(edges(np.stack([lch, rch], axis=1), rate))


def multitone(rate):
    n = int(DUR * rate)
    t = np.arange(n) / rate
    base = [50, 110, 223, 330, 440, 557, 660, 880, 1110, 1480, 1980, 2960, 4430, 6640, 9960]
    out = np.zeros((n, 2))
    for ch in range(2):
        sig = np.zeros(n)
        for k, f0 in enumerate(base):
            f = f0 * (1.0 if ch == 0 else 1.003)
            if f >= 0.48 * rate:
                continue
            amp = 1.0 / np.sqrt(k + 1)
            phase = k * 2.399963 + ch * 1.7 * k
            sig += amp * np.sin(2 * np.pi * f * t + phase)
        out[:, ch] = sig
    return norm_peak(edges(out, rate))


def pink(rate, seed):
    n = int(DUR * rate)
    out = np.zeros((n, 2))
    for ch in range(2):
        rng = np.random.default_rng(seed + ch)
        w = rng.standard_normal(n)
        W = np.fft.rfft(w)
        f = np.fft.rfftfreq(n, 1.0 / rate)
        f[0] = f[1]
        W = W / np.sqrt(f)
        out[:, ch] = np.fft.irfft(W, n)
    return norm_peak(edges(out, rate))


def music(rate, seed):
    """Additive plucks + bass + pad + seeded noise-burst percussion, 120 BPM."""
    n = int(DUR * rate)
    t = np.arange(n) / rate
    out = np.zeros((n, 2))
    rng = np.random.default_rng(seed)
    beat = 0.5
    chords = [  # (root Hz, chord tones Hz) C, G, Am, F ; 3 beats each
        (130.81, [261.63, 329.63, 392.00]),
        (98.00, [246.94, 293.66, 392.00]),
        (110.00, [220.00, 261.63, 329.63]),
        (87.31, [174.61, 220.00, 261.63]),
    ]
    # Pad: two detuned harmonic stacks per chord, slow attack/release.
    for ci, (root, tones) in enumerate(chords):
        t0 = ci * 3 * beat
        seg = (t >= t0) & (t < t0 + 3 * beat + 0.4)
        lt = t[seg] - t0
        env = np.minimum(1.0, lt / 0.4) * np.exp(-np.maximum(0.0, lt - 3 * beat) / 0.2)
        for ch in range(2):
            det = 1.0 + (0.0015 if ch else -0.0015)
            s = np.zeros(int(seg.sum()))
            for f in tones:
                for h in (1, 2):
                    s += (0.05 / h) * np.sin(2 * np.pi * f * h * det * lt + 0.3 * h)
            out[seg, ch] += env * s
    # Melody plucks on every beat (deterministic walk over chord tones + octave)
    # and a bass note on every beat.
    pattern = [0, 1, 2, 1, 2, 0, 1, 2, 2, 1, 0, 1]
    for b in range(12):
        root, tones = chords[b // 3]
        t0 = b * beat
        f = tones[pattern[b] % 3] * (2.0 if b % 4 == 3 else 1.0)
        dur = int(0.45 * rate)
        i0 = int(t0 * rate)
        lt = np.arange(dur) / rate
        for ch in range(2):
            det = 1.0 + (0.0008 if ch else 0.0)
            s = np.zeros(dur)
            for h in range(1, 7):
                s += (0.30 / h ** 1.2) * np.exp(-lt * h / 0.35) * np.sin(
                    2 * np.pi * f * h * det * lt + 0.11 * h)
            out[i0:i0 + dur, ch] += s
        # bass
        bd = int(0.42 * rate)
        lt = np.arange(bd) / rate
        benv = np.exp(-lt / 0.28)
        for ch in range(2):
            out[i0:i0 + bd, ch] += 0.34 * benv * (
                np.sin(2 * np.pi * root * lt) + 0.4 * np.sin(4 * np.pi * root * lt)
                + 0.15 * np.sin(6 * np.pi * root * lt))
        # percussion: noise burst on the beat, quieter one off-beat
        for tt, amp in ((t0, 0.20), (t0 + beat / 2, 0.08)):
            i1 = int(tt * rate)
            bl = int(0.03 * rate)
            burst = rng.standard_normal(bl)
            burst *= np.exp(-np.arange(bl) / (0.006 * rate))
            # one-pole high-pass emphasis
            burst = np.diff(np.concatenate([[0.0], burst])) * 3.0
            for ch in range(2):
                out[i1:i1 + bl, ch] += amp * burst
    return norm_peak(edges(np.clip(out, -1.2, 1.2), rate))


SOURCES = {
    "sweep": lambda rate: sweep(rate),
    "tones": lambda rate: multitone(rate),
    "pink": lambda rate: pink(rate, MASTER_SEED + 100),
    "music": lambda rate: music(rate, MASTER_SEED + 200),
}


def sha256(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    CORPUS.mkdir(parents=True, exist_ok=True)
    ffv = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout.splitlines()[0]
    manifest = {"generator": "gen_corpus.py", "ffmpeg": ffv, "duration_s": DUR,
                "peak_normalised": PEAK, "master_seed": MASTER_SEED, "files": []}
    for name, gen in SOURCES.items():
        for rate in RATES:
            src = gen(rate).astype("<f4")
            raw = CORPUS / f"src_{name}_{rate}.f32"
            raw.write_bytes(src.tobytes())
            for q in QUALITIES:
                ogg = CORPUS / f"{name}_q{q}_{rate}.ogg"
                subprocess.run(
                    ["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(rate),
                     "-ac", "2", "-i", str(raw), "-c:a", "libvorbis", "-q:a", str(q),
                     str(ogg)], check=True)
                manifest["files"].append({
                    "file": ogg.name, "source": name, "quality": q, "rate": rate,
                    "source_raw": raw.name, "source_sha256": sha256(raw),
                    "ogg_sha256": sha256(ogg), "ogg_bytes": ogg.stat().st_size,
                })
                print("wrote", ogg.name)
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print("manifest:", len(manifest["files"]), "files")


if __name__ == "__main__":
    sys.exit(main())
