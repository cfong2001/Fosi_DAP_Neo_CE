#!/usr/bin/env python3
"""Build the full build's merged gap-tail payload (2,040 of 2,044 B).

Layout (offsets from the gap-tail base 0x0307BFB4):

  0x000  M3U staging, 552 B of zeros (packed layout: header 16 +
         shared 42-byte context and 2 pad + 32 run clusters x 4 +
         32 run totals x 2 + 150 entries x 2; caps in
         src/m3u_bridge.h, offsets in src/resolver_hook.S)
  0x228  hooks at 0x0307C1DC, assembled from src/resolver_hook.S
         (resolver, fetch and count entry hooks, forward-step helper)
         and src/theater_noart.S (the two no-art exits); addresses
         are read from the ELF
         zeros up to the theater payload
  0x3A0  theater payload, 676 B at 0x0307C354 (reset stub at the base,
         blit trampoline after it), assembled by theater/build_theater.py
         with --base 0x0307C354
  0x644  Bluetooth blob, 436 B at 0x0307C5F8, its audited address;
         byte-identical to the ui_features build (pin below), so
         patch 0032-tail is used unchanged
  0x7F8  spare, 4 B (zeros; not emitted, the tail step zero-fills)

Relocation accounting:
  hooks     every absolute reference in resolver_hook.S is a stock
            address or the staging base 0x0307BFB4. The three external
            branches (0x03059DB0, 0x0305B2C6, 0x03059D5C) are assembled
            as placeholders and re-encoded here, then decoded back.
  theater   build_theater.py assembles symbolically at the base it is
            given; its round-trip check revalidates every branch target.
  bluetooth not relocated: it stays at its audited base 0x0307C5F8.

Emits into ../out: tail-full.bin, layout_tail.json; and into
../patches: 0041 to 0046 (playlist and no-art hook sites) and 0100 to 0104
(theater hooks, copied from the theater sub-build).
"""
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / 'src'
FULL = HERE.parent
OUT = FULL / 'out'
PATCHES = FULL / 'patches'
REPO = FULL.parents[1]

TAIL_BASE = 0x0307BFB4
STAGING = 552
RES_BASE = TAIL_BASE + STAGING          # 0x0307C1DC
THEATER_LEN = 676
BT_BASE = 0x0307C5F8
BT_LEN = 436
BT_SHA256 = 'ce6ef701285885efb17b072df128602c3ee5da8359b7b267cd7e1ca92457cf06'
THEATER_BASE = BT_BASE - THEATER_LEN    # 0x0307C354
TOTAL = 2040

# External branch targets of the hook source, in source order.
EXTERNAL = {'RESUME_P': 0x03059DB0, 'RESUME_C': 0x0305B2C6,
            'RESUME_N': 0x03059D5C, 'RESUME_NA': 0x0307E978,
            'FILL': 0x030632FA, 'HELPER': 0x03063A08}
SOURCES = ('resolver_hook.S', 'theater_noart.S', 'transport_ground.S')
# Module 0 pockets for the hooks: stock routines that nothing can reach
# (patches/space/census_dead.py, tier 1, with the emulation coverage gate),
# each address word-aligned inside its pocket. (source, base, pocket end)
POCKETS = (('resolver_hook.S', 0x0306C878, 0x0306C960),
           ('theater_noart.S', 0x03063CDC, 0x03063D82),
           ('transport_ground.S', 0x030539B4, 0x03053A14))
POCKET_PATCHES = {'resolver_hook.S': '0047-pocket-playlist-hooks',
                  'theater_noart.S': '0048-pocket-theater-noart',
                  'transport_ground.S': '0049-pocket-transport-ground'}
FOCUS_BASE = RES_BASE                   # focus payload where the hooks were
FOCUS_MAX = THEATER_BASE - RES_BASE     # 376 B
V4_PATCHES = REPO / 'patches' / 'design_refresh_v4' / 'patches'
# The eight v4 transport repoints, retargeted to transport_keyed_draw.
TRANSPORT = ('transport-keyed-slot0-state', 'transport-keyed-playpause-bare',
             'transport-keyed-quote-bare', 'transport-keyed-info-bare',
             'transport-keyed-plus-bare', 'transport-keyed-repeat-state',
             'transport-keyed-right-state', 'transport-keyed-right-variants')
# Stock sites (module, address, displaced bytes) and the symbol each enters.
SITES = (
    ('0041-resolver-primary-hook', 0, 0x03059DAC, '2de9f047',
     'resolver_hook_primary', False),
    ('0042-resolver-companion-hook', 0, 0x0305B2C2, '2de9f047',
     'resolver_hook_companion', False),
    ('0043-playlist-count-hook', 0, 0x03059D58, '2de9f041',
     'resolver_hook_count', False),
    ('0044-playlist-forward-step', 0, 0x0305D598, 'a0890128',
     'resolver_hook_advance', True),
    ('0045-theater-noart-close', 27, 0x0307E972, '346098f8',
     'theater_noart_close', False),
    ('0046-theater-noart-open', 27, 0x0307E96C, '3460bde8',
     'theater_noart_open', False),
)

# Filled in after the build passed the resolver and theater emulation
# suites; the build refuses any later drift.
EXPECTED = {
    'resolver_sha256': '8936db72bb9775165d4fe47f111a066a717c213e5baeb94dbbb39abebaf29952',
    'focus_sha256': '479e1c49e92232643b0832f7a7929912298dccc93c7a80eb4fac9d76f913dc33',
    'theater_sha256': '17a558dde5b96ef305236b436e7ec593d7fbf5a3ff56d8437c168e5dd0399d69',
    'tail_sha256': '5100d0d0e4c17f08ea6ede667f3c720edb721013836a7bf6cf7bc0d942446c4c',
}


def run(*args, **kw):
    return subprocess.run(args, check=True, text=True,
                          capture_output=True, **kw).stdout


def branch(site, target, link=False):
    """Thumb-2 B.W (or BL with link=True) from site to target."""
    off = target - (site + 4)
    if off & 1 or not -(1 << 24) <= off < (1 << 24):
        raise ValueError('branch out of range')
    sign, i1, i2 = (off >> 24) & 1, (off >> 23) & 1, (off >> 22) & 1
    j1, j2 = (~(i1 ^ sign)) & 1, (~(i2 ^ sign)) & 1
    low = 0xd000 if link else 0x9000
    return struct.pack('<HH', 0xf000 | (sign << 10) | ((off >> 12) & 0x3ff),
                       low | (j1 << 13) | (j2 << 11) | ((off >> 1) & 0x7ff))


def bw(site, target):
    return branch(site, target)


def build_hooks(scratch):
    """Assemble each hook source into its module 0 pocket. Returns
    ({source: (base, bytes)}, symbol table)."""
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    pattern = re.compile(r'\b(b\.w|bl)(\s+)(' + '|'.join(EXTERNAL) + r')\b')
    flags = ['-mcpu=cortex-m3', '-mthumb', '-Os', '-ffreestanding',
             '-fno-builtin', '-nostdlib', '-Wall', '-Wextra', '-Werror']
    objs, orders, seen = [], {}, []
    for src, base, end in POCKETS:
        text = (SRC / src).read_text()
        orders[src] = [(m.group(1), m.group(3)) for m in pattern.finditer(text)]
        seen += [n for _, n in orders[src]]
        # ld cannot branch to an absolute address, so each external branch
        # is assembled as a branch to itself and re-encoded after linking.
        text = pattern.sub(lambda m: f'{m.group(1)}{m.group(2)}.', text)
        asm, obj = scratch / f'{src}.S', scratch / f'{src}.o'
        asm.write_text(text)
        run('arm-none-eabi-gcc', *flags, '-c', str(asm), '-o', str(obj))
        objs.append(obj)
    if sorted(seen) != sorted(EXTERNAL):
        raise ValueError(f'each external target must appear once: {seen}')
    sections = '\n'.join(
        f' .p{i} {base:#x} : {{ *{Path(src).stem}.S.o(.text .text.*) }}\n'
        f' ASSERT(. <= {end:#x}, "{src} overflows its pocket")'
        for i, (src, base, end) in enumerate(POCKETS))
    ld, elf = scratch / 'hooks.ld', scratch / 'hooks.elf'
    ld.write_text(f'''SECTIONS {{
{sections}
 .data : {{ *(.data) *(.data.*) }}
 .bss : {{ *(.bss) *(.bss.*) *(COMMON) }}
 /DISCARD/ : {{ *(.comment) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }}
 ASSERT(SIZEOF(.data) == 0, "hooks require data")
 ASSERT(SIZEOF(.bss) == 0, "hooks require BSS")
}}
''')
    run('arm-none-eabi-gcc', *flags, '-T', str(ld), *map(str, objs), '-o', str(elf),
        cwd=str(scratch))
    if run('arm-none-eabi-nm', '-u', str(elf)).strip():
        raise ValueError('hooks have undefined symbols')
    symbols = {}
    for line in run('arm-none-eabi-nm', '-n', str(elf)).splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[1] == 'T':
            symbols[parts[2]] = int(parts[0], 16)
    allowed = set(EXTERNAL.values())
    out = {}
    for i, (src, base, end) in enumerate(POCKETS):
        raw = scratch / f'p{i}.bin'
        run('arm-none-eabi-objcopy', '-O', 'binary', '-j', f'.p{i}', str(elf), str(raw))
        code = bytearray(raw.read_bytes())
        placeholders = [x for x in decoder.disasm(bytes(code), base)
                        if x.mnemonic in ('b.w', 'bl') and x.op_str == f'#0x{x.address:x}']
        if [x.mnemonic for x in placeholders] != [k for k, _ in orders[src]]:
            raise ValueError(f'{src}: unexpected external-branch placeholders')
        for insn, (kind, name) in zip(placeholders, orders[src]):
            target = EXTERNAL[name]
            o = insn.address - base
            code[o:o + 4] = branch(insn.address, target, kind == 'bl')
            decoded = list(decoder.disasm(code[o:o + 4], insn.address))
            if len(decoded) != 1 or decoded[0].op_str != f'#0x{target:x}':
                raise ValueError('hook branch audit failed')
        for insn in decoder.disasm(bytes(code), base):
            if insn.mnemonic in ('b.w', 'bl') and insn.op_str.startswith('#'):
                target = int(insn.op_str[1:], 16)
                if not base <= target < base + len(code) and target not in allowed:
                    raise ValueError(f'{insn.address:#x}: {insn.mnemonic} to '
                                     f'unexpected {target:#x}')
        if base + len(code) > end:
            raise ValueError(f'{src}: {len(code)} bytes overflow its pocket')
        out[src] = (base, bytes(code))
    return out, symbols


def build_focus():
    """Assemble focus mode (patches/focus_mode/build_focus.py) at FOCUS_BASE.
    Returns (payload, entries, patch defs)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'build_focus', REPO / 'patches' / 'focus_mode' / 'build_focus.py')
    bf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bf)
    bf.FOCUS_BASE = FOCUS_BASE
    payload, entries = bf.assemble()
    bf.roundtrip(payload, entries)
    if len(payload) > FOCUS_MAX:
        raise ValueError(f'focus payload {len(payload)} > {FOCUS_MAX}')
    return payload, entries, bf


def patch_file(name, title, module, address, expect, replace, gate,
               rationale):
    text = (f'{title}\n'
            f'name: {name}\n'
            f'kind: module\n'
            f'module: {module}\n'
            f'region: code\n'
            f'address: {address:#x}\n'
            f'gate: {gate}\n'
            f'expect: {expect}\n'
            f'replace: {replace}\n'
            f'rationale: {rationale}\n')
    (PATCHES / f'{name}.patch').write_text(text)


RATIONALE = {
    '0041-resolver-primary-hook':
        'Replaces the resolver entry push.w with a B.W to the tail\n'
        '  hook. While a playlist is armed and the call is mode 1 with\n'
        '  the play context descriptor 0x030239B4 as out, position i\n'
        '  serves staged entry i - 1 and returns its 1-based ordinal.\n'
        '  Any other call re-executes the displaced push and continues\n'
        '  at 0x03059DB0 with entry state intact.',
    '0042-resolver-companion-hook':
        'Replaces the fetch entry push.w with a B.W to the tail hook.\n'
        '  While a playlist is armed, a mode 1 call returning to the\n'
        '  playlist start (0x0307E065) or the play-mode switch\n'
        '  (0x0308A6CB) returns its index unchanged, so positions stay\n'
        '  playlist positions. Other calls run the stock fetch.',
    '0043-playlist-count-hook':
        'Replaces the count entry push.w with a B.W to the tail hook.\n'
        '  While a playlist is armed, a mode 1 count returns the staged\n'
        '  entry count, so the play context length is the playlist\n'
        '  length. Other calls run the stock count.',
    '0045-theater-noart-close':
        'The player\'s artwork loader skips artwork setup when the\n'
        '  locator finds no picture, so the theater reset never ran and\n'
        '  the background kept the previous track\'s color. Replaces\n'
        '  "str r4, [r6]" and the first half of "ldrb.w r0, [r8]" with a\n'
        '  B.W to a stub that runs both, restores the theme background,\n'
        '  disarms sampling and resumes at 0x0307E978. Nothing branches\n'
        '  to 0x0307E976.',
    '0046-theater-noart-open':
        'Same restore on the loader\'s exit when the audio file does\n'
        '  not open. Replaces "str r4, [r6]" and the first half of the\n'
        '  exit pop with a B.W to a stub that stores, restores the\n'
        '  theme background and performs the same pop. Nothing branches\n'
        '  to 0x0307E96E or 0x0307E970.',
    '0044-playlist-forward-step':
        'Replaces "ldrh r0, [r4, #0xc]; cmp r0, #1" in the source 6\n'
        '  step with a BL to a helper that runs both instructions and\n'
        '  forces the shuffle-path condition while a playlist is\n'
        '  armed. A forward step then resolves the new position and\n'
        '  advances to its ordinal instead of taking the folder\n'
        '  iterator\'s next file. r1 and lr are dead at this site.',
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PATCHES.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='fosi-full-tail-') as tmp:
        scratch = Path(tmp)
        pockets, symbols = build_hooks(scratch)
        stock = (REPO / 'DP3_V137.img').read_bytes()
        sys.path.insert(0, str(REPO / 'tools'))
        from rknano_image import Image
        sim = Image(stock)
        m0_off, _ = sim.module_region(0, 'code')
        m0_base = sim.modules[0]['code_exec']
        hooks_blob = b''.join(code for _, code in pockets.values())
        res_sha = hashlib.sha256(hooks_blob).hexdigest()
        for src, (base, code) in pockets.items():
            print(f'hooks {src}: {len(code)} bytes at {base:#x} (module 0 pocket)')

        print(f'hooks sha256 {res_sha}')
        focus, focus_entries, bf = build_focus()
        focus_sha = hashlib.sha256(focus).hexdigest()
        print(f'focus: {len(focus)} bytes at {FOCUS_BASE:#x}, sha256 {focus_sha}')

        # ---- theater below the Bluetooth blob ------------------------
        r = subprocess.run([sys.executable,
                            str(HERE / 'theater' / 'build_theater.py'),
                            '--base', hex(THEATER_BASE)],
                           capture_output=True, text=True)
        print(r.stdout, end='')
        if r.returncode != 0:
            print(r.stderr, file=sys.stderr)
            raise SystemExit('theater sub-build failed')
        theater = (HERE / 'theater' / 'theater_tail.bin').read_bytes()
        if len(theater) != THEATER_LEN:
            raise SystemExit(f'theater payload length {len(theater)}')
        th_sha = hashlib.sha256(theater).hexdigest()
        print(f'theater: {len(theater)} bytes at {THEATER_BASE:#x}, '
              f'sha256 {th_sha}')
        for name in ('0100-theater-setup-reset-hook',
                     '0101-theater-blit-sync-a',
                     '0102-theater-blit-sync-b',
                     '0103-theater-blit-painter-a',
                     '0104-theater-blit-painter-b'):
            shutil.copyfile(HERE / 'theater' / f'{name}.patch',
                            PATCHES / f'{name}.patch')

        # ---- bluetooth at its audited base ---------------------------
        bt_path = scratch / 'bt.bin'
        r = subprocess.run([sys.executable,
                            str(REPO / 'patches' / 'ui_features' / 'build'
                                / 'build_bt_tail.py'),
                            '--output', str(bt_path)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr, file=sys.stderr)
            raise SystemExit('bluetooth sub-build failed')
        bt = bt_path.read_bytes()
        if len(bt) != BT_LEN or hashlib.sha256(bt).hexdigest() != BT_SHA256:
            raise SystemExit('bluetooth blob does not match its pin')
        print(f'bluetooth: {len(bt)} bytes at {BT_BASE:#x} (audited pin)')

        # ---- merge ----------------------------------------------------
        tail = bytearray(TOTAL)
        tail[STAGING:STAGING + len(focus)] = focus
        tail[THEATER_BASE - TAIL_BASE:
             THEATER_BASE - TAIL_BASE + len(theater)] = theater
        tail[BT_BASE - TAIL_BASE:BT_BASE - TAIL_BASE + len(bt)] = bt
        tail = bytes(tail)
        tail_sha = hashlib.sha256(tail).hexdigest()
        print(f'merged tail: {len(tail)} bytes, sha256 {tail_sha}')
        if EXPECTED['tail_sha256'] is not None:
            assert res_sha == EXPECTED['resolver_sha256'], 'hooks drift'
            assert focus_sha == EXPECTED['focus_sha256'], 'focus drift'
            assert th_sha == EXPECTED['theater_sha256'], 'theater drift'
            assert tail_sha == EXPECTED['tail_sha256'], 'tail drift'
        (OUT / 'tail-full.bin').write_bytes(tail)

        # ---- pocket patches: the hooks in module 0 dead code ----------
        pgate = ('build refuses unless the stock bytes at the target equal\n'
                 '  `expect`; the finished image must also pass the grown\n'
                 '  build validator.')
        for src, (base, code) in pockets.items():
            o = m0_off + base - m0_base
            patch_file(
                POCKET_PATCHES[src],
                f'# {src} assembled into a module 0 pocket at {base:#010x}.',
                0, base, stock[o:o + len(code)].hex(), code.hex(), pgate,
                'A stock routine here has no caller, branch, pointer or\n'
                '  literal anywhere in core-0 code or data\n'
                '  (patches/space/census_dead.py, tier 1), and no emulation\n'
                '  suite executes it (patches/space/run_coverage.py). The\n'
                '  hooks moved here from the gap tail to make room for focus\n'
                '  mode; module 0 is resident in every window, so every\n'
                '  caller still reaches them.')

        # ---- focus mode hook sites (module 27) -----------------------
        for k, (num, name, site, target, _note) in enumerate(bf.PATCH_DEFS):
            mo = sim.module_region(27, 'code')[0] + site - sim.modules[27]['code_exec']
            patch_file(
                f'{120 + k:04d}-{name}',
                f'# Focus mode: BL to {target} at {focus_entries[target]:#010x}\n'
                f'# in the full build\'s merged tail. Design: patches/focus_mode/.',
                27, site, stock[mo:mo + 4].hex(),
                branch(site, focus_entries[target], link=True).hex(),
                'stock byte precondition; validated by test_focus_mode.py under\n'
                '  emulation on the full build',
                bf.RATIONALES[name])

        # ---- hook site patches ----------------------------------------
        gate = ('build refuses unless the stock bytes at the target equal\n'
                '  `expect`; the finished image must also pass the grown\n'
                '  build validator. Requires the full build\'s merged tail.')
        for name, module, site, expect, symbol, link in SITES:
            target = symbols[symbol]
            kind = 'BL' if link else 'B.W'
            patch_file(
                name,
                f'# Hook site: {kind} to {symbol} at {target:#010x}\n'
                f'# in the full build\'s merged tail.',
                module, site, expect, branch(site, target, link).hex(), gate,
                RATIONALE[name])

        wrapper = symbols['transport_keyed_draw']
        for k, stem in enumerate(TRANSPORT):
            fields = {}
            for line in (V4_PATCHES / f'{stem}.patch').read_text().splitlines():
                key, _, value = line.partition(':')
                if key in ('address', 'expect', 'module'):
                    fields[key] = value.strip()
            site = int(fields['address'], 16)
            patch_file(
                f'{110 + k:04d}-{stem}-ground',
                f'# Player transport draw: BL to transport_keyed_draw at\n'
                f'# {wrapper:#010x}, which fills the glyph rectangle with the\n'
                f'# ground colour and then draws through the keyed helper.\n'
                f'# Same site and stock bytes as design_refresh_v4/{stem}.',
                int(fields['module']), site, fields['expect'],
                branch(site, wrapper, link=True).hex(), gate,
                'The v4 repoint to the keyed helper leaves the previous\n'
                '  glyph\'s ink behind on a segment-only repaint. The wrapper\n'
                '  restores the opaque draw\'s whole-rectangle replacement\n'
                '  with the surround in the ground colour, then draws the\n'
                '  glyph keyed.')

        hooks = {s: hex(symbols[s]) for _, _, _, _, s, _ in SITES}
        hooks['transport_keyed_draw'] = hex(wrapper)
        layout = {
            'tail_base': hex(TAIL_BASE), 'tail_bytes': len(tail),
            'tail_sha256': tail_sha, 'budget': 2044,
            'pieces': [
                {'name': 'M3U staging (zeros)',
                 'offset': 0, 'address': hex(TAIL_BASE),
                 'bytes': STAGING,
                 'layout': 'header 16 + context 44 + 32 runs x 6 + 150 entries x 2'},
                {'name': 'focus mode payload',
                 'offset': STAGING, 'address': hex(FOCUS_BASE),
                 'bytes': len(focus), 'sha256': focus_sha,
                 'entries': {k: hex(v) for k, v in focus_entries.items()}},
                {'name': 'free (zeros)',
                 'offset': STAGING + len(focus),
                 'address': hex(RES_BASE + len(focus)),
                 'bytes': THEATER_BASE - RES_BASE - len(focus)},
                {'name': 'theater payload (reset stub + trampoline)',
                 'offset': THEATER_BASE - TAIL_BASE,
                 'address': hex(THEATER_BASE), 'bytes': len(theater),
                 'sha256': th_sha,
                 'trampoline': hex(THEATER_BASE + 0x54)},
                {'name': 'bluetooth blob (audited placement)',
                 'offset': BT_BASE - TAIL_BASE, 'address': hex(BT_BASE),
                 'bytes': len(bt), 'sha256': BT_SHA256},
                {'name': 'spare (zeros, not emitted)',
                 'offset': TOTAL, 'address': hex(TAIL_BASE + TOTAL),
                 'bytes': 2044 - TOTAL},
            ],
            'pockets': [
                {'source': src, 'address': hex(base), 'bytes': len(code),
                 'patch': POCKET_PATCHES[src]}
                for src, (base, code) in pockets.items()],
            'hook_entries': hooks,
        }
        (OUT / 'layout_tail.json').write_text(
            json.dumps(layout, indent=2) + '\n')


if __name__ == '__main__':
    main()
