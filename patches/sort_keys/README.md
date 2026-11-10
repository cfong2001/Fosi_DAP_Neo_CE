# Natural-sort keys

Shipped in both images (Standard and Minimal) as patches 0027 to 0031 in
[`../framework/patches/`](../framework/patches/).

Library sort keys are built with case folding, Latin-1 accent folding, one
leading "The " stripped, and digit runs compared as numbers, and the
comparator is patched to match. Stock uppercases ASCII in the first four
characters only, so Track 10 sorts before Track 2.

- [`sort_keys.md`](sort_keys.md): the transform, why both sides of the comparison change, and the tests.
- `test_vectors.py`, `unicorn_diff_test.py`: a 4,000-pair consistency fuzz and a differential test over 349 names, both with zero failures.
