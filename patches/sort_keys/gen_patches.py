#!/usr/bin/env python3
"""Emit the five framework .patch files for the sort-keys series.

Expects are sliced from the extracted stock module 39 binary (no manual
transcription); hook encodings are assembled with rz-asm at the exact
site addresses; the cave replacement is cave.bin verbatim. Run after
sortkey_asm.py so cave.bin / cave_listing.txt are current.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = HERE.parents[2]
MOD39 = WS / 'extracted' / 'module_39_code_0307d5fc.bin'
MOD39_BASE = 0x0307D5FC
RZASM = WS / 'tools-local' / 'bin' / 'rz-asm'
GATE = ("build refuses unless the stock bytes at the target equal `expect`;\n"
        "  the finished image must also pass firmware_patch.validate()")

mod = MOD39.read_bytes()
cave = (HERE / 'cave.bin').read_bytes()


def stock(addr, n):
    off = addr - MOD39_BASE
    b = mod[off:off + n]
    assert len(b) == n, hex(addr)
    return b


def asm(addr, text):
    r = subprocess.run([str(RZASM), '-a', 'arm', '-b', '16', '-o', hex(addr), text],
                       capture_output=True, text=True)
    hx = r.stdout.strip()
    assert hx and len(hx) % 2 == 0, (text, r.stdout, r.stderr)
    return bytes.fromhex(hx)


def hook(site, reg, exit_addr, pfx=0x0309F0B6):
    b = asm(site, f'mov r0, {reg}')
    b += asm(site + len(b), f'bl {pfx:#x}')
    b += asm(site + len(b), f'b.w {exit_addr:#x}')
    assert len(b) <= 0x30
    return b + b'\x00\xbf' * ((0x30 - len(b)) // 2)


def emit(fname, title, name, address, expect, replace, rationale):
    assert len(expect) == len(replace)
    text = (f"# {title}\n"
            f"name: {name}\n"
            f"kind: module\n"
            f"module: 39\n"
            f"region: code\n"
            f"address: {address:#010x}\n"
            f"gate: {GATE}\n"
            f"rationale: {rationale}\n"
            f"expect: {expect.hex()}\n"
            f"replace: {replace.hex()}\n")
    (HERE / fname).write_text(text)
    print(f'{fname}: {name} @ {address:#x}, {len(expect)} bytes')


# 1 -- comparator hook -------------------------------------------------------
emit('0026-sortkeys-comparator-hook.patch',
     'Sort keys: redirect the library comparator into the cave.',
     'sortkeys-comparator-hook', 0x0307D620,
     stock(0x0307D620, 4), asm(0x0307D620, 'b.w 0x0309f000'),
     "Replaces the 4-byte entry of module 39's sort comparator\n"
     "  (push.w prologue) with b.w cave_cmp (0x0309f000, patch 0030).\n"
     "  The comparator is called only from the sorted-insert routine\n"
     "  (BL sites 0x0307d6fe/0x0307d720/0x0307d738), always with\n"
     "  record_pointer + 4, and returns 0 (less) / 1 (equal) / 2\n"
     "  (greater); cave_cmp preserves that exact contract, so no\n"
     "  caller changes. Stock compared 4 inline key units (record\n"
     "  offsets +0x0..+0x6 relative to the +4 pointer) and then fell\n"
     "  back to a raw, unfoldled full-string compare; cave_cmp keeps\n"
     "  a token-aware fast path over the same 4 inline units (now\n"
     "  built by patches 0027-0029) and defers to a full transform\n"
     "  compare (sk_tcmp) whenever a digit-run marker or a 4-unit\n"
     "  tie is involved, which is what makes the on-device order\n"
     "  identical to the pure transform order (host-fuzz proven).")

# 2-4 -- builder hooks ---------------------------------------------------------
emit('0027-sortkeys-builder-a-hook.patch',
     'Sort keys: builder A builds the true transform prefix.',
     'sortkeys-builder-a-hook', 0x0307D87E,
     stock(0x0307D87E, 0x30), hook(0x0307D87E, 'r5', 0x0307D8AE),
     "Replaces the 0x30-byte inline fold loop of key builder A\n"
     "  (function 0x0307d80a) with mov r0, r5 / bl cave_pfx /\n"
     "  b.w 0x0307d8ae (the stock loop exit), NOP-padded. r5 is the\n"
     "  record pointer at this site. Stock's loop uppercased ASCII\n"
     "  a-z only, over exactly the first 4 characters: no accent\n"
     "  fold, no leading-'The ' handling, digits as raw code points\n"
     "  ('Track 10' sorted before 'Track 2'). cave_pfx reads the\n"
     "  record's full name via the string index the builder stored\n"
     "  at record+0xc immediately before this loop (same address\n"
     "  formula and module-0 read call 0x03067510 the comparator\n"
     "  uses), invalidates both comparator string-cache slots so\n"
     "  the scratch reuse cannot serve stale strings, and writes\n"
     "  the first 4 units of the full sort transform (casefold +\n"
     "  Latin-1 accent fold + 'The ' strip + natural-number tokens)\n"
     "  to record+4..+0xa, exactly where stock wrote its prefix.")

emit('0028-sortkeys-builder-bmain-hook.patch',
     'Sort keys: builder B (main loop) builds the true transform prefix.',
     'sortkeys-builder-bmain-hook', 0x0307D954,
     stock(0x0307D954, 0x30), hook(0x0307D954, 'r4', 0x0307D984),
     "Same replacement as patch 0027 for the main fold loop of key\n"
     "  builder B (function 0x0307d8c4); the record pointer is in\n"
     "  r4 at this site and the stock loop exit is 0x0307d984. The\n"
     "  builder stored the full-string index at record+0xc before\n"
     "  this loop, as in builder A. See 0027 for the transform and\n"
     "  the cache-invalidation discipline.")

emit('0029-sortkeys-builder-balt-hook.patch',
     'Sort keys: builder B (alternate loop) builds the true transform prefix.',
     'sortkeys-builder-balt-hook', 0x0307D9F2,
     stock(0x0307D9F2, 0x30), hook(0x0307D9F2, 'r4', 0x0307DA22),
     "Same replacement as patch 0027 for the alternate fold loop\n"
     "  of key builder B (function 0x0307d8c4, second scan path);\n"
     "  the record pointer is in r4 at this site and the stock loop\n"
     "  exit is 0x0307da22. The builder stored the full-string\n"
     "  index at record+0xc before this loop, as in builder A.\n"
     "  See 0027 for the transform and the cache-invalidation\n"
     "  discipline. All three builder loops must be hooked: each\n"
     "  is a live path that writes record prefixes.")

# 5 -- the cave ----------------------------------------------------------------
assert stock(0x0309F000, len(cave)) == bytes(len(cave)), 'cave region not all zero'
emit('0030-sortkeys-cave.patch',
     'Sort keys: transform + comparator implementation in the module 39 zero cave.',
     'sortkeys-cave', 0x0309F000,
     bytes(len(cave)), cave,
     "Installs the sort-key implementation (cave_cmp, cave_pfx,\n"
     "  sk_str_addr, sk_tcmp, sk_pfx4, gen_init, gen_next, sk_fold\n"
     "  and the 128-byte Latin-1 fold table) into the zero region\n"
     "  at the tail of module 39's code span (real code ends at\n"
     "  0x0307e1ec; span ends 0x0309f4ac; an overlap scan over all\n"
     "  82 modules' code/data/bss spans showed only module 39's own\n"
     "  code covers 0x0309f000..0x0309f41c, and the stock bytes\n"
     "  there are all zero, which is what `expect` pins). Blob is\n"
     "  1052 of the 1196 available bytes. Verified offline: host\n"
     "  reference suite (vectors + 4000-pair ordering fuzz) and a\n"
     "  Unicorn differential test of sk_tcmp / sk_pfx4 against the\n"
     "  host model over 349 names, 0 failures; see\n"
     "  work/patches/sort_keys/sort_keys.md. Source:\n"
     "  work/patches/sort_keys/sortkey_asm.py (assembled with\n"
     "  rz-asm; cmp.w is used for every r12 immediate compare\n"
     "  because rz-asm silently truncates `cmp r12, #imm` to r4).")

print('all five patch files written')
