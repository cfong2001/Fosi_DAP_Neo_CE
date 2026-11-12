#!/usr/bin/env python3
"""AutoEQ and custom curves for the stock 31-band EQ (patches/eq_presets/).

The stock EQ (module 36, coefficients in module 35) is a 31-band graphic
EQ on the ISO third-octave centres, 20 Hz to 20 kHz, each band -12 to
+12 dB in 1 dB steps (gain index = dB + 12). The six menu presets are
31-entry gain arrays in module 33's data at 0x030489CC + 62 * (n - 1).

This module turns a curve into an integer gain array by fitting it to the
firmware's own band filters (the 48 kHz coefficient set), so overlapping
bands are accounted for, and builds the byte patches. docs/eq-core.mjs is
the browser port; tests/eq-core.test.mjs keeps the two identical.
"""
import json
import math
import re
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tools'))
from rknano_image import Image  # noqa: E402

ISO = [20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500,
       630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000,
       10000, 12500, 16000, 20000]
SLOTS = {1: 'Pop', 2: 'Jazz', 3: 'Rock', 4: 'Classical', 5: 'Bass Boost', 6: 'Heavy Metal'}
TABLE = 0x030489CC          # module 33 data, slot 1; slot n at +62 * (n - 1)
SELECTOR = 0x0308AD08       # tbb bytes for EQ modes 4, 5, 6
SELECTOR_STOCK = bytes.fromhex('051632')
SELECTOR_FIXED = bytes.fromhex('0b0b0b')   # every mode uses table + 62 * (mode - 1)
FS = 48000
GRID = [20 * 2 ** (i / 12) for i in range(120)]   # 20 Hz to ~19.5 kHz, 1/12 octave
TREBLE_HOLD = 16000   # the fit holds the curve level above this: the top of a
# headphone measurement is the least repeatable part, and AutoEQ targets there often
# fall below the -12 dB floor, which only makes the top bands oscillate


def coefficient_set(raw, rate_set=4):
    """Return coeffs[band][gain] = (b0, b1, b2, a1, a2) for one rate set
    (4 = 48 kHz) from module 35."""
    img = Image(raw)
    off, _ = img.module_region(35, 'data')
    out = []
    for band in range(31):
        row = []
        for g in range(25):
            if band < 10:
                a1, a2, b0, b1, b2 = (x / 2 ** 20 for x in struct.unpack_from(
                    '<5i', raw, off + rate_set * 5000 + (band * 25 + g) * 20))
            else:
                a1, a2, b1, b2, k = (x / 8192 for x in struct.unpack_from(
                    '<5h', raw, off + 25000 + rate_set * 5250 + ((band - 10) * 25 + g) * 10))
                b0, b1, b2 = k, b1 * k, b2 * k
            row.append((b0, b1, b2, a1, a2))
        out.append(row)
    return out


def response_db(c, f):
    b0, b1, b2, a1, a2 = c
    w = 2 * math.pi * f / FS
    zr, zi = math.cos(w), -math.sin(w)            # z^-1
    z2r, z2i = zr * zr - zi * zi, 2 * zr * zi     # z^-2
    nr, ni = b0 + b1 * zr + b2 * z2r, b1 * zi + b2 * z2i
    dr, di = 1 - a1 * zr - a2 * z2r, -a1 * zi - a2 * z2i
    return 10 * math.log10((nr * nr + ni * ni) / (dr * dr + di * di))


def band_table(raw):
    """R[band][gain][grid point] in dB."""
    coeffs = coefficient_set(raw)
    return [[[response_db(coeffs[b][g], f) for f in GRID] for g in range(25)]
            for b in range(31)]


def parse_curve(text):
    """AutoEQ GraphicEQ ('GraphicEQ: 20 -0.2; 21 -0.2; ...'), or 31
    numbers (dB at the ISO centres) separated by spaces, commas or lines."""
    m = re.search(r'GraphicEQ:\s*(.*)', text)
    if m:
        pts = []
        for pair in m.group(1).split(';'):
            parts = pair.split()
            if len(parts) == 2:
                pts.append((float(parts[0]), float(parts[1])))
        if len(pts) < 2:
            raise ValueError('GraphicEQ line has fewer than two points')
        return sorted(pts)
    nums = [float(x) for x in re.findall(r'[-+]?\d+(?:\.\d+)?', text)]
    if len(nums) != 31:
        raise ValueError(f'expected an AutoEQ GraphicEQ line or 31 dB values, got {len(nums)} numbers')
    return list(zip(ISO, nums))


def target_at(points, f):
    if f <= points[0][0]:
        return points[0][1]
    if f >= points[-1][0]:
        return points[-1][1]
    for (f0, g0), (f1, g1) in zip(points, points[1:]):
        if f0 <= f <= f1:
            t = (math.log(f) - math.log(f0)) / (math.log(f1) - math.log(f0))
            return g0 + t * (g1 - g0)
    return points[-1][1]


RIDGE = 0.1


def ridge_start(target, R):
    """Least-squares gains with a small ridge penalty, using each band's
    per-dB slope (its +12 dB response minus its -12 dB response, / 24).
    Plain Gaussian elimination with partial pivoting, so the browser port
    gives the same numbers."""
    n = len(GRID)
    A = [[(R[b][24][i] - R[b][0][i]) / 24 for b in range(31)] for i in range(n)]
    M = [[sum(A[i][a] * A[i][b] for i in range(n)) + (RIDGE if a == b else 0)
          for b in range(31)] for a in range(31)]
    v = [sum(A[i][a] * target[i] for i in range(n)) for a in range(31)]
    for c in range(31):
        p = max(range(c, 31), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        v[c], v[p] = v[p], v[c]
        for r in range(31):
            if r != c:
                f = M[r][c] / M[c][c]
                for k in range(c, 31):
                    M[r][k] -= f * M[c][k]
                v[r] -= f * v[c]
    return [max(-12, min(12, round(v[c] / M[c][c]))) for c in range(31)]


def fit(points, R):
    """Integer gain per band (-12..12 dB) whose realised response, computed
    with the firmware's own band filters, best matches the curve on a
    1/12-octave grid: a ridge least-squares start, then greedy +/-1 dB
    coordinate descent. Deterministic."""
    target = [target_at(points, min(f, TREBLE_HOLD)) for f in GRID]
    gains = ridge_start(target, R)
    total = [sum(R[b][gains[b] + 12][i] for b in range(31)) for i in range(len(GRID))]

    def err(tot):
        return sum((t - r) ** 2 for t, r in zip(target, tot))
    best = err(total)
    for _ in range(60):
        changed = False
        for b in range(31):
            for step in (1, -1):
                g = gains[b] + step
                if not -12 <= g <= 12:
                    continue
                trial = [total[i] - R[b][gains[b] + 12][i] + R[b][g + 12][i] for i in range(len(GRID))]
                e = err(trial)
                if e < best - 1e-9:
                    best, total, gains[b], changed = e, trial, g, True
                    break
        if not changed:
            break
    rms = math.sqrt(best / len(GRID))
    return gains, rms, max(total)


def slot_patches(raw, slots):
    """Patches for build.py: the selector fix plus one gain array per slot.
    slots maps slot number (1..6) to a list of 31 integer dB values.
    Slots left out keep exactly what stock applies for that menu item."""
    img = Image(raw)
    m = img.modules[33]
    doff, _ = img.module_region(33, 'data')
    file_of = lambda a: doff + a - m['data_exec']  # noqa: E731
    stock = lambda k: raw[file_of(TABLE + 62 * k):file_of(TABLE + 62 * k) + 62]  # noqa: E731
    # what stock applies per menu item (selector before the fix)
    applied = {1: stock(0), 2: stock(1), 3: stock(2), 4: stock(0), 5: stock(1),
               6: struct.pack('<31H', *[12] * 31)}
    patches = [{'name': 'eq-selector-distinct-presets', 'kind': 'module', 'module': 33,
                'region': 'code', 'address': SELECTOR, 'expect': SELECTOR_STOCK,
                'replace': SELECTOR_FIXED, 'file': 'eq_presets', 'rationale': 'eq', 'gate': 'eq'}]
    for n in range(1, 7):
        if n in slots:
            gains = slots[n]
            if len(gains) != 31 or any(not -12 <= g <= 12 for g in gains):
                raise ValueError(f'slot {n}: need 31 integer gains in -12..12')
            new = struct.pack('<31H', *[g + 12 for g in gains])
        else:
            new = applied[n]
        addr = TABLE + 62 * (n - 1)
        old = stock(n - 1)
        if new != old:
            patches.append({'name': f'eq-preset-{n}', 'kind': 'module', 'module': 33,
                            'region': 'data', 'address': addr, 'expect': old,
                            'replace': new, 'file': 'eq_presets', 'rationale': 'eq', 'gate': 'eq'})
    return patches


NAME_IDS = {n: 174 + n for n in SLOTS}   # menu string records 175..180, every language
NAME_MAX = 24                             # the longest stock name is 24 characters
LANGUAGES = 21


def check_name(n, name):
    """A slot name: 1 to NAME_MAX printable BMP characters, no edge spaces."""
    if not isinstance(name, str) or not name or name != name.strip():
        raise ValueError(f'slot {n}: name must be non-empty text without leading or trailing spaces')
    if len(name) > NAME_MAX:
        raise ValueError(f'slot {n}: name longer than {NAME_MAX} characters')
    if any(ord(c) < 0x20 or 0x7f <= ord(c) < 0xa0 or ord(c) > 0xffff for c in name):
        raise ValueError(f'slot {n}: name has a control character or one outside the BMP')
    return name


def name_patches(raw, names):
    """String patches that rename EQ menu items. names maps slot (1..6) to
    the new name, written to that item's record in all 21 languages; each
    patch expects the stock text of its own language."""
    img = Image(raw)
    langs = [list(img.lang(lang)) for lang in range(LANGUAGES)]
    patches = []
    for n in sorted(names):
        name = check_name(n, names[n])
        sid = NAME_IDS[n]
        for lang in range(LANGUAGES):
            patches.append({'name': f'eq-name-{n}-lang{lang}', 'kind': 'string',
                            'language': lang, 'string_id': sid,
                            'expect_text': langs[lang][sid]['text'], 'replace_text': name,
                            'file': 'eq_presets', 'rationale': 'eq', 'gate': 'eq'})
    return patches


def load_config(path, raw):
    """Config JSON: {"slots": {"1": {"file": "x GraphicEQ.txt"} | {"text": "..."}
    | {"gains": [31 ints]}, each optionally with "name": "..."}}.
    A slot may carry only a name. Returns {slot: gains}, {slot: name} and
    a report."""
    cfg = json.loads(Path(path).read_text())
    R = None
    slots, names, report = {}, {}, {}
    for key, spec in cfg.get('slots', {}).items():
        n = int(key)
        if n not in SLOTS:
            raise ValueError(f'slot {n}: must be 1..6')
        if 'name' in spec:
            names[n] = check_name(n, spec['name'])
            report.setdefault(n, {})['name'] = names[n]
        if 'gains' in spec:
            slots[n] = [int(g) for g in spec['gains']]
            report.setdefault(n, {})['source'] = 'gains'
            continue
        if 'text' not in spec and 'file' not in spec:
            continue
        text = spec['text'] if 'text' in spec else (Path(path).parent / spec['file']).read_text()
        R = R or band_table(raw)
        gains, rms, peak = fit(parse_curve(text), R)
        slots[n] = gains
        report.setdefault(n, {}).update(source=spec.get('file', 'text'),
                                        rms_error_db=round(rms, 3), peak_db=round(peak, 2))
    return slots, names, report


if __name__ == '__main__':
    raw = (REPO / 'DP3_V137.img').read_bytes()
    pts = parse_curve(Path(sys.argv[1]).read_text())
    g, rms, peak = fit(pts, band_table(raw))
    print(json.dumps({'gains': g, 'rms_error_db': round(rms, 3), 'peak_db': round(peak, 2)}))
