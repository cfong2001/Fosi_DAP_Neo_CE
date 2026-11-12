#!/usr/bin/env python3
"""Compose the full build's module 31 segment extension payload.

Layout (exec base 0x0307EE48, room to 0x03080B54 = 7,436 bytes):

  +0x000  hook trampoline for patch 0040 (64-byte slot). Full build
          variant: on a successful import the handled exit enters the
          stock folder-play sequence at 0x0307E052 instead of the
          common exit, so playback starts (see src/asm_trampoline_ext.py).
  +0x040  bridge + parser blob, linked at 0x0307EE88 with
          m3u_bridge_node_action as its first byte. Staging uses the
          packed layout in src/m3u_bridge.h (32 folder runs, 150
          entries in the tail's 552-byte span); resolved entries are
          recorded straight into the staging span, so the blob holds
          no resolution log of its own.
  ...     zero padding to 4
  ...     lock-screen routine, relinked at its payload address
          (patch 0033's branch bytes are regenerated for that base)
  ...     zero padding to 4
  ...     navigation disarm stubs (playlist_exit.S), linked at the
          first free payload address; hook sites at module 31
          0x0307E04E (folder) and 0x0307E1CC (file)

Emits into ../out: payload31.bin, layout31.json; and into ../patches:
0040-m3u-browser-hook.patch, 0033-ui-lockscreen-title.patch,
0060-nav-folder-disarm.patch, 0061-nav-file-disarm.patch.
Every component is asserted .bss-free, as in the compose variant.
"""
import argparse
import hashlib
import importlib.util
import json
import re
import struct
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / 'src'
FULL = HERE.parent
OUT = FULL / 'out'
PATCHES = FULL / 'patches'
REPO = FULL.parents[1]
CC = 'arm-none-eabi-gcc'
CFLAGS = ['-std=c99', '-mcpu=cortex-m3', '-mthumb', '-Os',
          '-ffreestanding', '-fno-builtin', '-nostdlib',
          '-fno-zero-initialized-in-bss', '-Wall', '-Wextra']

EXT_BASE = 0x0307EE48
EXT_END = 0x03080B54
TRAMP_SLOT = 64
BP_BASE = EXT_BASE + TRAMP_SLOT

# Filled in after the first build passed the parser suite and the
# host bridge test; the build refuses any later drift.
EXPECTED = {
    'payload_sha256': '4e717adca5c06a13c2f76e981387852d64d86458d3d6eee0b405144d5fc78ac3',
    'site33': '01f0d1be',
    'site40': '00f095bf',
}


def staging_caps():
    """Read the staging caps from src/m3u_bridge.h, the single source."""
    text = (SRC / 'm3u_bridge.h').read_text()

    def define(name):
        m = re.search(r'^#define\s+' + name + r'\s+(\d+)u', text, re.M)
        if not m:
            raise SystemExit(f'm3u_bridge.h: {name} not found')
        return int(m.group(1))
    return {'layout': 'packed', 'max_runs': define('M3U_STAGE_MAX_RUNS'),
            'max_entries': define('M3U_STAGE_MAX_ENT'),
            'staging_bytes': define('M3U_STAGE_TOTAL')}


def run(cmd, **kw):
    print('+', ' '.join(str(c) for c in cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.stdout:
        print(r.stdout, end='')
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        raise SystemExit(f'command failed: {cmd[0]}')
    return r


def nm(elf):
    out = run(['arm-none-eabi-nm', str(elf)]).stdout
    syms = {}
    undef = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3:
            syms[parts[2]] = (int(parts[0], 16), parts[1])
        elif len(parts) == 2 and parts[0] == 'U':
            undef.append(parts[1])
    return syms, undef


def bss_size(elf):
    out = run(['arm-none-eabi-size', str(elf)]).stdout.splitlines()
    fields = out[1].split()
    return int(fields[2])


def stock_bytes(mod, addr, n):
    sys.path.insert(0, str(REPO / 'tools'))
    from rknano_image import Image
    raw = (REPO / 'DP3_V137.img').read_bytes()
    im = Image(raw)
    off, _ = im.module_region(mod, 'code')
    base = im.modules[mod]['code_exec']
    return raw[off + (addr - base):off + (addr - base) + n]


def patch_file(name, title, module, address, expect, replace, gate, rationale):
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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--scratch', type=Path, required=True,
                    help='scratch directory for intermediate objects')
    a = ap.parse_args()
    B = a.scratch.resolve()
    B.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    PATCHES.mkdir(parents=True, exist_ok=True)
    libgcc = run([CC, '-print-libgcc-file-name']).stdout.strip()

    # ---- bridge + parser -------------------------------------------
    for src in ('m3u.c', 'm3u_bridge.c'):
        run([CC, *CFLAGS, '-c', str(SRC / src), '-o',
             str(B / (src + '.o'))])
    bp_ld = B / 'bridge_parser.ld'
    bp_ld.write_text(f"""SECTIONS
{{
    . = {BP_BASE:#x};
    .text : {{ *(.text.entry) *(.text) *(.text.*) }}
    .rodata : {{ *(.rodata) *(.rodata.*) }}
    .data : {{ *(.data) *(.data.*) }}
    /DISCARD/ : {{ *(.comment) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }}
    ASSERT(ADDR(.text) == {BP_BASE:#x}, "bridge entry must sit at the blob base")
}}
""")
    bp_elf = B / 'bridge_parser.elf'
    run([CC, *CFLAGS, '-T', str(bp_ld),
         str(B / 'm3u.c.o'), str(B / 'm3u_bridge.c.o'), libgcc,
         '-o', str(bp_elf), '-Wl,-Map,' + str(B / 'bridge_parser.map')])
    assert bss_size(bp_elf) == 0, 'bridge+parser has .bss; payload would lose it'
    syms, undef = nm(bp_elf)
    assert not undef, f'undefined symbols: {undef}'
    entry, kind = syms['m3u_bridge_node_action']
    assert entry == BP_BASE and kind in 'Tt', (entry, kind)
    assert 'm3u_import' in syms
    bp_bin = B / 'bridge_parser.bin'
    run(['arm-none-eabi-objcopy', '-O', 'binary', str(bp_elf), str(bp_bin)])
    bp = bp_bin.read_bytes()
    print(f'bridge+parser: {len(bp)} bytes at {BP_BASE:#x}; '
          f'm3u_import at {syms["m3u_import"][0]:#x}')

    # ---- trampoline (full-build start variant) ----------------------
    tramp_bin = B / 'trampoline.bin'
    site40 = B / 'site40.bin'
    run([sys.executable, str(SRC / 'asm_trampoline_ext.py'),
         '--base', hex(EXT_BASE), '--bridge', hex(BP_BASE),
         '--slot', str(TRAMP_SLOT), '--out', str(tramp_bin),
         '--site-out', str(site40)])
    tramp = tramp_bin.read_bytes()
    assert len(tramp) == TRAMP_SLOT

    # ---- lock-screen routine, relinked -------------------------------
    lock_base = (EXT_BASE + TRAMP_SLOT + len(bp) + 3) & ~3
    lock_ld = B / 'lockscreen_ext.ld'
    lock_ld.write_text(f"""SECTIONS
{{
    . = {lock_base:#x};
    .text : {{
        *(.text.entry)
        *(.text)
        *(.text.*)
    }}
    .rodata : {{ *(.rodata) *(.rodata.*) }}
    .data : {{ *(.data) *(.data.*) }}
    /DISCARD/ : {{ *(.comment) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }}
    ASSERT(ADDR(.text) == {lock_base:#x}, "lock-screen entry must sit at its link base")
}}
""")
    run([CC, *CFLAGS, '-c', str(SRC / 'lockscreen.c'), '-o',
         str(B / 'lockscreen.o')])
    lock_elf = B / 'lockscreen.elf'
    run([CC, *CFLAGS, '-T', str(lock_ld), str(B / 'lockscreen.o'),
         libgcc, '-o', str(lock_elf),
         '-Wl,-Map,' + str(B / 'lockscreen.map')])
    assert bss_size(lock_elf) == 0, 'lock routine has .bss'
    lsyms, lundef = nm(lock_elf)
    assert not lundef, f'lock undefined symbols: {lundef}'
    lentry, _ = lsyms['ui_lockscreen_paint']
    assert lentry == lock_base, (lentry, lock_base)
    lock_bin = B / 'lockscreen.bin'
    run(['arm-none-eabi-objcopy', '-O', 'binary', str(lock_elf), str(lock_bin)])
    lock = lock_bin.read_bytes()
    print(f'lock routine: {len(lock)} bytes at {lock_base:#x}')

    # ---- patch 0033 site bytes at the new base -----------------------
    spec = importlib.util.spec_from_file_location(
        'asm_trampoline_ext', SRC / 'asm_trampoline_ext.py')
    branch_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(branch_mod)
    s33 = branch_mod.branch(0x0307E89E, lock_base)
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    decoded = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(s33, 0x0307E89E))
    assert len(decoded) == 1 and decoded[0].op_str == f'#0x{lock_base:x}', decoded
    print(f'patch 0033 replace bytes: {s33.hex()} '
          f'(compose variant build: 02f007b8)')

    # ---- compose ------------------------------------------------------
    payload = bytearray()
    payload += tramp
    payload += bp
    while len(payload) % 4:
        payload += b'\0'
    lock_off = len(payload)
    assert EXT_BASE + lock_off == lock_base
    payload += lock
    while len(payload) % 4:
        payload += b'\0'
    compose_len = len(payload)

    # ---- navigation disarm stubs, appended ----------------------------
    nav_base = EXT_BASE + compose_len
    spec = importlib.util.spec_from_file_location(
        'build_exit', SRC / 'build_exit.py')
    nav_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(nav_mod)
    nav, nsyms, nsites = nav_mod.build('arm-none-eabi-', nav_base)
    payload += nav
    payload = bytes(payload)
    print(f'nav stubs: {len(nav)} bytes at {nav_base:#x} '
          f'(folder_start {nsyms["folder_start"]:#x}, '
          f'file_start {nsyms["file_start"]:#x})')

    digest = hashlib.sha256(payload).hexdigest()
    room = EXT_END - EXT_BASE
    print(f'payload: {len(payload)} bytes; room {room}; '
          f'spare {room - len(payload)}')
    assert len(payload) <= room, 'PAYLOAD OVERFLOWS THE EXTENSION ROOM'
    if EXPECTED['payload_sha256'] is not None:
        assert digest == EXPECTED['payload_sha256'], \
            f'payload drifted from pin: {digest}'
        assert s33.hex() == EXPECTED['site33']
        assert site40.read_bytes().hex() == EXPECTED['site40']
    (OUT / 'payload31.bin').write_bytes(payload)

    # ---- patch files ---------------------------------------------------
    patch_file(
        '0040-m3u-browser-hook',
        '# M3U bridge: divert module 31\'s node-action classification call\n'
        '# to the hook trampoline at the base of the full build\'s module 31\n'
        '# segment extension payload (patches/full). Same site and contract\n'
        '# as the compose variant\'s 0040; the trampoline differs only in\n'
        '# its handled exit (folder-play start, see build/src/\n'
        '# asm_trampoline_ext.py).',
        31, 0x0307DF1A, 'fff76df9', site40.read_bytes().hex(),
        'Do NOT stack alone. Requires the full build\'s module 31\n'
        '  segment extension (--grow 31:code: with payload31.bin):\n'
        '  trampoline at exec 0x0307EE48, bridge entry at 0x0307EE88.',
        'The site is the single BL inside module 31\'s node-action\n'
        '  function that dispatches on the selected node\'s class byte;\n'
        '  see the compose variant\'s 0040 for the full register\n'
        '  contract. On a bridge decline the trampoline reproduces the\n'
        '  displaced call exactly. On a successful import it leaves\n'
        '  into the stock folder-play sequence at 0x0307E052 with\n'
        '  r0 = 1, so the stock start sequence (classifier, directory\n'
        '  fetch, source 6 commit, event clears, 0x14D post, message\n'
        '  3) runs with the staging flag armed.')
    patch_file(
        '0033-ui-lockscreen-title',
        '# Lock-screen information: divert module 31\'s painter hold-icon\n'
        '# tail call to the lock-screen routine inside the full build\'s\n'
        '# module 31 segment extension payload. Branch bytes regenerated\n'
        '# for the routine\'s composed position in this build.',
        31, 0x0307E89E, 'e4f72fbf', s33.hex(),
        'build refuses unless the 4 stock bytes at the target equal\n'
        '  `expect`. Do NOT stack without the full build\'s module 31\n'
        '  segment extension carrying the lock routine at the branch\n'
        '  target.',
        'Same site and contract as the compose variant\'s 0033; the\n'
        '  target moved because the full build\'s bridge+parser blob\n'
        '  differs (packed staging layout, no resolution log in the\n'
        '  blob) and is built under the local toolchain.')
    folder_expect = stock_bytes(31, 0x0307E04E, 4).hex()
    file_expect = stock_bytes(31, 0x0307E1CC, 6).hex()
    patch_file(
        '0060-nav-folder-disarm',
        '# Navigation disarm, folder play start: clear the M3U staging\n'
        '# flag before stock folder playback proceeds.',
        31, 0x0307E04E, folder_expect, nsites['folder'].hex(),
        'Do NOT stack alone. Requires the full build\'s module 31\n'
        '  segment extension carrying the disarm stubs at the branch\n'
        '  target.',
        'Stock folder play begins here (movs r5, #1; mov r0, r5,\n'
        '  then the classifier call at 0x0307E052). The stub clears\n'
        '  the staging flag byte at 0x0307BFB4, reproduces both\n'
        '  displaced instructions and resumes at 0x0307E052. The M3U\n'
        '  import path never passes through this site (its trampoline\n'
        '  enters at 0x0307E052), so an armed playlist survives its\n'
        '  own start. Source: patches/navigation/playlist_exit.S,\n'
        '  proven by patches/navigation/test_exit.py at its audited\n'
        '  placement and re-proven at this placement by the full\n'
        '  build\'s lifecycle audit.')
    patch_file(
        '0061-nav-file-disarm',
        '# Navigation disarm, music file play start: clear the M3U\n'
        '# staging flag before stock file playback proceeds.',
        31, 0x0307E1CC, file_expect, nsites['file'].hex(),
        'Do NOT stack alone. Requires the full build\'s module 31\n'
        '  segment extension carrying the disarm stubs at the branch\n'
        '  target.',
        'The validated music-file action reaches this site. The stub\n'
        '  clears the staging flag byte at 0x0307BFB4, reproduces the\n'
        '  displaced PC-relative load and call, restores the original\n'
        '  return address and resumes at 0x0307E1D2. Source and proof:\n'
        '  as 0060.')

    layout = {
        'ext_base': hex(EXT_BASE), 'ext_end': hex(EXT_END),
        'room': room, 'payload_bytes': len(payload),
        'payload_sha256': digest,
        'spare': room - len(payload),
        'site33_replace': s33.hex(),
        'site40_replace': site40.read_bytes().hex(),
        'components': [
            {'name': 'trampoline (patch 0040 target, start variant)',
             'offset': 0, 'address': hex(EXT_BASE), 'bytes': len(tramp)},
            {'name': 'bridge + parser (m3u_bridge_node_action first)',
             'offset': TRAMP_SLOT, 'address': hex(BP_BASE),
             'bytes': len(bp),
             'm3u_import': hex(syms['m3u_import'][0])},
            {'name': 'lock-screen routine (ui_lockscreen_paint)',
             'offset': lock_off, 'address': hex(lock_base),
             'bytes': len(lock)},
            {'name': 'navigation disarm stubs (folder + file)',
             'offset': compose_len, 'address': hex(nav_base),
             'bytes': len(nav),
             'folder_start': hex(nsyms['folder_start']),
             'file_start': hex(nsyms['file_start'])},
        ],
        'staging_caps': staging_caps(),
    }
    (OUT / 'layout31.json').write_text(json.dumps(layout, indent=2) + '\n')
    print(f'payload31.bin: {len(payload)} bytes, sha256 {digest}')


if __name__ == '__main__':
    main()
