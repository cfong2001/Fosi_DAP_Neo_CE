#!/usr/bin/env python3
"""PCM comparison helpers for the module 72 harness validation.

Compares harness-captured PCM (s16le interleaved) against the ffmpeg
reference decode of the same file. Reports the best alignment (signed
integer frame lag, by normalised cross-correlation) and per-sample
error statistics at that alignment: maximum absolute error, RMS error,
SNR in dB, and whether the aligned regions are bit-identical.

Lag convention: harness frame i corresponds to reference frame
i + lag. A negative lag means the harness stream carries extra leading
frames (for example a priming block) that the reference does not have.
"""
import numpy as np


def _as_frames(pcm_bytes, channels):
    a = np.frombuffer(pcm_bytes, dtype=np.int16)
    n = (len(a) // channels) * channels
    return a[:n].reshape(-1, channels)


def _mono(pcm_bytes, channels):
    return _as_frames(pcm_bytes, channels).astype(np.float64).sum(axis=1)


def _corr(a, b):
    na = np.sqrt((a ** 2).sum()) or 1.0
    nb = np.sqrt((b ** 2).sum()) or 1.0
    return float((a * b).sum() / (na * nb))


def best_lag(harness_pcm, ref_pcm, channels, search=9600, head_s=3.0, rate=48000):
    """Find the signed integer frame lag of harness PCM vs reference."""
    h = _mono(harness_pcm, channels)
    r = _mono(ref_pcm, channels)
    total_min = min(len(h), len(r))
    head = int(min(total_min, head_s * rate))
    if total_min > search:
        head = min(head, total_min - search)
    else:
        head = max(1, total_min // 2)
    if head <= 0:
        return 0
    best, bestv = 0, -2.0
    # lag >= 0: harness head matches reference starting at lag
    rs = r[:head + search]
    for lag in range(0, min(search, len(rs) - head) + 1):
        v = _corr(h[:head], rs[lag:lag + head])
        if v > bestv:
            bestv, best = v, lag
    # lag < 0: reference head matches harness starting at -lag
    hs = h[:head + search]
    for lag in range(1, min(search, len(hs) - head) + 1):
        v = _corr(hs[lag:lag + head], r[:head])
        if v > bestv:
            bestv, best = v, -lag
    return best


def compare(harness_pcm, ref_pcm, channels, rate=48000, search=9600):
    """Returns a dict of comparison statistics."""
    lag = best_lag(harness_pcm, ref_pcm, channels, search=search, rate=rate)
    h = _as_frames(harness_pcm, channels)
    r = _as_frames(ref_pcm, channels)
    if lag >= 0:
        n = min(len(h), len(r) - lag)
        hh, rr = h[:max(n, 0)], r[lag:lag + max(n, 0)]
    else:
        n = min(len(r), len(h) + lag)
        hh, rr = h[-lag:-lag + max(n, 0)], r[:max(n, 0)]
    out = {'lag_frames': int(lag), 'harness_frames': int(len(h)),
           'ref_frames': int(len(r)), 'compared_frames': int(max(n, 0))}
    if n <= 0:
        out['error'] = 'no overlap'
        return out
    err = hh.astype(np.int64) - rr.astype(np.int64)
    sig = rr.astype(np.float64)
    noise = err.astype(np.float64)
    sp = float((sig ** 2).sum())
    npow = float((noise ** 2).sum())
    out.update({
        'bit_identical': bool((err == 0).all()),
        'max_abs_err': int(np.abs(err).max()),
        'rms_err': float(np.sqrt((noise ** 2).mean())),
        'snr_db': float(10 * np.log10(sp / npow)) if npow > 0 else float('inf'),
        'first_diff_frame': int(np.argmax((err != 0).any(axis=1))) if (err != 0).any() else -1,
    })
    return out
