#!/usr/bin/env python3
"""Vector suite + consistency fuzz for the natural-sort host reference.

Run: venv/bin/python test_vectors.py
Exit code 0 = all pass. Also imported by the Unicorn differential test.
"""
import random
import sys
from functools import cmp_to_key

from host_ref import device_cmp, gen_units, pfx4, tcmp

FAILS = []


def check(cond, msg):
    if not cond:
        FAILS.append(msg)
        print('FAIL:', msg)


def lt(a, b):
    check(tcmp(a, b) == -1 and device_cmp(a, b) == -1,
          f'expected {a!r} < {b!r}: tcmp={tcmp(a, b)} device={device_cmp(a, b)}')


def eq(a, b):
    check(tcmp(a, b) == 0 and device_cmp(a, b) == 0,
          f'expected {a!r} == {b!r}: tcmp={tcmp(a, b)} device={device_cmp(a, b)}')


def vectors():
    # --- the brief's vectors (one direction corrected, see sort_keys.md) ---
    # 'The Beatles' keys to BEATLES, 'Beach House' to BEACH HOUSE; at unit 3
    # 'C' (0x43) < 'T' (0x54), so Beach House sorts FIRST under the stated
    # rules. The brief listed the pair as ["The Beatles" < "Beach House"],
    # which is backwards under its own rule set; asserted correctly here.
    lt('Beach House', 'The Beatles')
    lt('track 2', 'Track 10')                 # natural numbers + case fold
    eq('Abba', 'ABBA')                        # case variants equal-fold
    eq('aBbA', 'AbBa')
    lt('Émile', 'Emma')                       # accent strip: EMILE < EMMA
    eq('Beyoncé', 'Beyonce')
    eq('Björk', 'Bjork')
    eq('Track 02', 'Track 2')                 # leading zeros fold away
    lt('Track 02', 'Track 10')
    eq('a01', 'a1')

    # --- articles ---
    lt('The Beach Boys', 'The Beatles')       # BEACH < BEATLES after strip
    eq('The 39 Steps', '39 Steps')            # strip, then numeric token
    lt('The', 'Theodore')                     # bare 'The' is not an article
    eq('The The', 'The')                      # one strip only: key THE
    lt('The', 'Thriller')                     # THE < THR...
    eq('the beatles', 'Beatles')
    eq('  The   Beatles  ', 'Beatles')        # outer spaces + article
    lt('The Cars', 'Theodore')                # CARS < THEODORE once stripped

    # --- natural numbers ---
    lt('2Pac', '10cc')                        # token at key start
    lt('a2b', 'a10b')
    lt('a02b', 'a10b')
    lt('Track 9', 'Track 10')
    lt('Track 99', 'Track 100')
    lt('9 Songs', 'A Song')                   # numbers before letters
    lt('Vol 2', 'Vol 10')
    eq('Song 007', 'Song 7')
    lt('Song 7', 'Song 07a')                  # 7 == 07, then end < 'A'
    lt('123', '1234')                         # numeric, not lexicographic
    lt('x1y2', 'x1y10')

    # --- accents / expansions / combining ---
    eq('Weiß', 'Weiss')                       # sharp s -> SS
    eq('Æsop', 'Aesop')                       # ligature -> AE
    eq('Œuvre', 'Oeuvre')
    eq('Caf\u00e9', 'Cafe\u0301')            # precomposed vs combining acute
    # (\u00d1and\u00fa direction check lives in fix_directional below)

    # --- prefix-zone stress (token inside the first 4 key units) ---
    lt('Be9x', 'Be10x')
    lt('The 9', '99')                         # T(9) token vs token(99): 9 < 99
    lt('ab12', 'ab123')                       # 12 < 123 at prefix edge
    lt('ab9x', 'ab12')                        # 9 < 12, run ends inside prefix
    eq('ab02', 'ab2')
    lt('A1', 'A01b')                          # equal token, then end < 'B'

    # --- misc identity / passthrough ---
    eq('中文歌', '中文歌')
    lt('ZZ Top', '中文歌')                    # code-point order past ASCII
    eq('', '')
    lt('', 'A')
    eq('   ', '')


def fix_directional():
    # Ñandú -> NANDU, Nana -> NANA: unit 3 'A'(NANA) < 'D'(NANDU)
    lt('Nana', 'Ñandú')


def fuzz_consistency(trials=4000, seed=20261031):
    """device_cmp must never disagree with tcmp (the consistency theorem),
    and tcmp must be antisymmetric."""
    rng = random.Random(seed)
    alphabet = (list('aAbBzZtThHeE ') + list('0123456789') +
                ['é', 'É', 'ö', 'ß', 'Æ', 'ñ', '́', '中', 'x', 'X', '.'])
    words = ['the', 'The', 'THE', 'track', 'Track', 'Beach', 'Beatles', '']
    names = set()
    for _ in range(400):
        n = ''.join(rng.choice(alphabet) for _ in range(rng.randrange(0, 11)))
        if rng.random() < 0.4:
            n = rng.choice(words) + ' ' + n
        names.add(n)
    names = sorted(names)
    bad = 0
    for _ in range(trials):
        a, b = rng.choice(names), rng.choice(names)
        d, t = device_cmp(a, b), tcmp(a, b)
        if d != t or tcmp(b, a) != -t:
            bad += 1
            print(f'FUZZ FAIL {a!r} vs {b!r}: device={d} tcmp={t} tcmp_rev={tcmp(b, a)}')
            if bad > 5:
                break
    check(bad == 0, f'fuzz consistency: {bad} disagreements')
    # sorted-order stability: sorting shuffles of the same set converges
    base = sorted(names, key=cmp_to_key(device_cmp))
    for _ in range(30):
        shuffled = names[:]
        rng.shuffle(shuffled)
        got = sorted(shuffled, key=cmp_to_key(device_cmp))
        # equal-key groups may permute; compare the key sequence instead
        check([gen_units(x) for x in got] == [gen_units(x) for x in base],
              'fuzz: sorted key sequence differs across shuffles')
        break


def main():
    vectors()
    fix_directional()
    fuzz_consistency()
    print(f'\n{len(FAILS)} failure(s)')
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
