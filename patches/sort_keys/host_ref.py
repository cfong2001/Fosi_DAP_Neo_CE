#!/usr/bin/env python3
"""Host reference implementation of the DAP Neo natural-sort key transform T.

This is the semantic source of truth for the on-device Thumb-2 routines in
sortkey_asm.py: the assembler build generates its Latin-1 fold table from
FOLD_TABLE below, and the Unicorn differential test checks the device code
against tcmp()/pfx4() here.

T(name) — name is a list of UTF-16 code units (or a Python str, converted):
  1. Trailing spaces (U+0020) are ignored; leading spaces are skipped.
  2. A leading article "The" (matched on folded units, any case) followed by
     at least one space and further content is stripped, with all spaces
     after it.
  3. Each remaining unit is folded:
       ASCII a-z -> A-Z
       Latin-1 accented letters -> base uppercase letter (FOLD_TABLE),
         with expansions AE (Ae-ligature), OE (Oe-ligature), SS (sharp s)
       combining marks U+0300..U+036F are dropped
       everything else is identity (CJK, Cyrillic, digits handled below, ...)
  4. A maximal run of ASCII digits is emitted as a numeric token:
       MARK (0x0001), count n of significant digits (leading zeros stripped;
       an all-zero run counts as the single digit '0'), then the significant
       digits themselves. Token order therefore equals numeric order, and a
       token sorts before any letter (MARK < 'A') but after end-of-string.

tcmp(a, b) compares T(a) vs T(b) lexicographically (end-of-key = unit 0).
pfx4(name) is the first 4 units of T(name), zero-padded — what the patched
builders store inline in the 14-byte sort record.

device_cmp() models the patched comparator exactly: a token-aware walk of
the two 4-unit prefixes that defers to tcmp() at the first numeric-token
unit (MARK), on a full 4-unit tie, and otherwise decides on the prefix.
"""

MARK = 0x0001

# Latin-1 fold table for U+00C0..U+00FF: (first, second) unit chars,
# (0, 0) = identity, second 0 = no second unit. Generated into the device
# blob by sortkey_asm.py — do not edit the two places separately.
def _build_fold_table():
    t = {}
    for lo, hi, base in ((0xC0, 0xC5, 'A'), (0xE0, 0xE5, 'A'),
                         (0xC8, 0xCB, 'E'), (0xE8, 0xEB, 'E'),
                         (0xCC, 0xCF, 'I'), (0xEC, 0xEF, 'I'),
                         (0xD2, 0xD6, 'O'), (0xF2, 0xF6, 'O'),
                         (0xD9, 0xDC, 'U'), (0xF9, 0xFC, 'U')):
        for c in range(lo, hi + 1):
            t[c] = (ord(base), 0)
    for c, base in ((0xC7, 'C'), (0xE7, 'C'), (0xD1, 'N'), (0xF1, 'N'),
                    (0xD8, 'O'), (0xF8, 'O'), (0xDD, 'Y'), (0xFD, 'Y'),
                    (0xFF, 'Y')):
        t[c] = (ord(base), 0)
    t[0xC6] = (ord('A'), ord('E'))
    t[0xE6] = (ord('A'), ord('E'))
    t[0xDF] = (ord('S'), ord('S'))
    return t

FOLD_TABLE = _build_fold_table()
# Byte table for the device build: 64 entries x (first, second) for
# U+00C0..U+00FF; (0,0) = identity.
FOLD_TABLE_BYTES = bytes(
    b for c in range(0xC0, 0x100) for b in FOLD_TABLE.get(c, (0, 0)))


def fold_unit(c):
    """Fold one code unit -> list of 0 (dropped), 1 or 2 key units."""
    if 0x61 <= c <= 0x7A:            # a-z
        return [c - 0x20]
    if 0x300 <= c <= 0x36F:          # combining marks: dropped
        return []
    if c in FOLD_TABLE:
        first, second = FOLD_TABLE[c]
        return [first] + ([second] if second else [])
    if c in (0x152, 0x153):          # OE ligatures (Latin Extended-A)
        return [ord('O'), ord('E')]
    return [c]


def _units(name):
    if isinstance(name, str):
        return [ord(ch) for ch in name]
    return list(name)


def content_range(units):
    """(start, end) after leading-space skip and trailing-space trim."""
    end = len(units)
    while end > 0 and units[end - 1] == 0x20:
        end -= 1
    start = 0
    while start < end and units[start] == 0x20:
        start += 1
    return start, end


def article_start(units, start, end):
    """Index past a leading 'The ' article, or `start` if there is none."""
    if end - start < 5:
        return start
    folded = []
    for i in range(3):
        f = fold_unit(units[start + i])
        if len(f) != 1:
            return start
        folded.append(f[0])
    if folded != [0x54, 0x48, 0x45]:        # T H E
        return start
    if units[start + 3] != 0x20:
        return start
    after = start + 4
    while after < end and units[after] == 0x20:
        after += 1
    return after if after < end else start


def gen_units(name):
    """T(name) as a list of key units (no terminator)."""
    units = _units(name)
    # stop at the first NUL unit, like the on-device buffers
    if 0 in units:
        units = units[:units.index(0)]
    start, end = content_range(units)
    start = article_start(units, start, end)
    out = []
    i = start
    while i < end:
        c = units[i]
        if 0x30 <= c <= 0x39:                       # digit run -> token
            q = i
            while q < end and 0x30 <= units[q] <= 0x39:
                q += 1
            sig = i
            while sig < q - 1 and units[sig] == 0x30:
                sig += 1
            # if all zeros, sig stops at the last zero: digits = ['0'], n = 1
            digits = units[sig:q]
            out.append(MARK)
            out.append(len(digits))
            out.extend(digits)
            i = q
        else:
            out.extend(fold_unit(c))
            i += 1
    return out


def tcmp(a, b):
    """Compare two names by T: -1 / 0 / +1. End-of-key counts as unit 0."""
    ka, kb = gen_units(a), gen_units(b)
    for i in range(max(len(ka), len(kb))):
        ua = ka[i] if i < len(ka) else 0
        ub = kb[i] if i < len(kb) else 0
        if ua != ub:
            return -1 if ua < ub else 1
    return 0


def pfx4(name):
    """The 4 inline record units the patched builders store."""
    k = gen_units(name)
    return (k + [0, 0, 0, 0])[:4]


def device_cmp(name_a, name_b):
    """Exact model of the patched comparator (prefix phase + full phase)."""
    pa, pb = pfx4(name_a), pfx4(name_b)
    for i in range(4):
        ua, ub = pa[i], pb[i]
        if ua == MARK or ub == MARK:
            return tcmp(name_a, name_b)
        if ua != ub:
            return -1 if ua < ub else 1
        if ua == 0:
            return 0
    return tcmp(name_a, name_b)


def sort_records(records):
    """Sort (category0, category2, name) records the patched way.

    Stock compares the category u16 fields first only in the raw-record
    layout sense — see sort_keys.md: the comparator's field compares are
    the key prefix itself. This helper sorts plain name lists with
    device_cmp for the test suites.
    """
    from functools import cmp_to_key
    return sorted(records, key=cmp_to_key(device_cmp))
