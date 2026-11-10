#!/usr/bin/env python3
"""Compose the module 31 segment extension payload.

Layout (exec base 0x0307EE48, room to 0x03080B54 = 7,436 bytes):

  +0x000  hook trampoline for patch 0040 (64-byte slot, code + NOPs)
  +0x040  bridge + parser blob, linked at 0x0307EE88 with
          m3u_bridge_node_action as its first byte
  ...     zero padding to 4
  ...     lock-screen routine, relinked at its payload address
          (patch 0033's branch bytes are regenerated for that base)

Every component is asserted .bss-free: the payload is a plain byte
copy, so all writable storage must ride inside the image as .data.
Also emitted: build/site40.bin (patch 0040 replacement bytes) and
build/site33.bin (patch 0033 replacement bytes).
"""
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / 'src'
BUILD = HERE / 'build'
CC = 'arm-none-eabi-gcc'
CFLAGS = ['-std=c99', '-mcpu=cortex-m3', '-mthumb', '-Os',
          '-ffreestanding', '-fno-builtin', '-nostdlib',
          '-fno-zero-initialized-in-bss', '-Wall', '-Wextra']

EXT_BASE = 0x0307EE48
EXT_END = 0x03080B54
TRAMP_SLOT = 64
BP_BASE = EXT_BASE + TRAMP_SLOT


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
    # columns: text data bss dec hex
    fields = out[1].split()
    return int(fields[2])


def main():
    global BUILD
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, required=True, help="scratch directory for generated payload and metadata")
    BUILD = ap.parse_args().out_dir.resolve()
    BUILD.mkdir(parents=True, exist_ok=True)
    libgcc = run([CC, '-print-libgcc-file-name']).stdout.strip()

    # ---- bridge + parser -------------------------------------------
    for src in ('m3u.c', 'm3u_bridge.c'):
        run([CC, *CFLAGS, '-c', str(SRC / src), '-o',
             str(BUILD / (src + '.o'))])
    bp_ld = BUILD / 'bridge_parser.ld'
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
    bp_elf = BUILD / 'bridge_parser.elf'
    run([CC, *CFLAGS, '-T', str(bp_ld),
         str(BUILD / 'm3u.c.o'), str(BUILD / 'm3u_bridge.c.o'), libgcc,
         '-o', str(bp_elf), '-Wl,-Map,' + str(BUILD / 'bridge_parser.map')])
    assert bss_size(bp_elf) == 0, 'bridge+parser has .bss; payload would lose it'
    syms, undef = nm(bp_elf)
    assert not undef, f'undefined symbols: {undef}'
    entry, kind = syms['m3u_bridge_node_action']
    assert entry == BP_BASE and kind in 'Tt', (entry, kind)
    assert 'm3u_import' in syms
    bp_bin = BUILD / 'bridge_parser.bin'
    run(['arm-none-eabi-objcopy', '-O', 'binary', str(bp_elf), str(bp_bin)])
    bp = bp_bin.read_bytes()
    print(f'bridge+parser: {len(bp)} bytes at {BP_BASE:#x}; '
          f'm3u_import at {syms["m3u_import"][0]:#x}')

    # ---- trampoline --------------------------------------------------
    tramp_bin = BUILD / 'trampoline.bin'
    site40 = BUILD / 'site40.bin'
    run([sys.executable, str(SRC / 'asm_trampoline_ext.py'),
         '--base', hex(EXT_BASE), '--bridge', hex(BP_BASE),
         '--slot', str(TRAMP_SLOT), '--out', str(tramp_bin),
         '--site-out', str(site40)])
    tramp = tramp_bin.read_bytes()
    assert len(tramp) == TRAMP_SLOT

    # ---- lock-screen routine, relinked -------------------------------
    lock_base = (EXT_BASE + TRAMP_SLOT + len(bp) + 3) & ~3
    lock_ld = BUILD / 'lockscreen_ext.ld'
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
         str(BUILD / 'lockscreen.o')])
    lock_elf = BUILD / 'lockscreen.elf'
    run([CC, *CFLAGS, '-T', str(lock_ld), str(BUILD / 'lockscreen.o'),
         libgcc, '-o', str(lock_elf),
         '-Wl,-Map,' + str(BUILD / 'lockscreen.map')])
    assert bss_size(lock_elf) == 0, 'lock routine has .bss'
    lsyms, lundef = nm(lock_elf)
    assert not lundef, f'lock undefined symbols: {lundef}'
    lentry, _ = lsyms['ui_lockscreen_paint']
    assert lentry == lock_base, (lentry, lock_base)
    lock_bin = BUILD / 'lockscreen.bin'
    run(['arm-none-eabi-objcopy', '-O', 'binary', str(lock_elf), str(lock_bin)])
    lock = lock_bin.read_bytes()
    print(f'lock routine: {len(lock)} bytes at {lock_base:#x}')

    # ---- patch 0033 site bytes at the new base -----------------------
    spec = importlib.util.spec_from_file_location("asm_trampoline_ext", SRC / "asm_trampoline_ext.py")
    branch_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(branch_mod)
    s33 = branch_mod.branch(0x0307E89E, lock_base)
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    decoded = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(s33, 0x0307E89E))
    assert len(decoded) == 1 and decoded[0].op_str == f"#0x{lock_base:x}", decoded
    (BUILD / 'site33.bin').write_bytes(s33)
    print(f'patch 0033 replace bytes: {s33.hex()} '
          f'(stock expect e4f72fbf, previous build 00f0d3ba)')

    # ---- compose -------------------------------------------------------
    payload = bytearray()
    payload += tramp
    payload += bp
    while len(payload) % 4:
        payload += b'\0'
    lock_off = len(payload)
    assert EXT_BASE + lock_off == lock_base
    payload += lock
    payload = bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    expected = '84b82518bfb02105cb4166914021b0e56a2ba16ea1cbd19ecc88abe70dbbfe28'
    if digest != expected or s33.hex() != '02f007b8' or site40.read_bytes().hex() != '00f095bf':
        raise SystemExit(f'composition differs from reviewed payload or hooks (sha256 {digest}); '
                         'use the documented toolchain or review and repin the complete build')
    room = EXT_END - EXT_BASE
    print(f'payload: {len(payload)} bytes; room {room}; '
          f'spare {room - len(payload)}')
    assert len(payload) <= room, 'PAYLOAD OVERFLOWS THE EXTENSION ROOM'
    out = BUILD / 'payload.bin'
    out.write_bytes(payload)
    layout = {
        'ext_base': hex(EXT_BASE), 'ext_end': hex(EXT_END),
        'room': room, 'payload_bytes': len(payload),
        'spare': room - len(payload),
        'components': [
            {'name': 'trampoline (patch 0040 target)', 'offset': 0,
             'address': hex(EXT_BASE), 'bytes': len(tramp),
             'site40_replace': site40.read_bytes().hex()},
            {'name': 'bridge + parser (m3u_bridge_node_action first)',
             'offset': TRAMP_SLOT, 'address': hex(BP_BASE),
             'bytes': len(bp),
             'm3u_import': hex(syms['m3u_import'][0])},
            {'name': 'padding', 'offset': TRAMP_SLOT + len(bp),
             'bytes': lock_off - TRAMP_SLOT - len(bp)},
            {'name': 'lock-screen routine (ui_lockscreen_paint)',
             'offset': lock_off, 'address': hex(lock_base),
             'bytes': len(lock), 'site33_replace': s33.hex()},
        ],
    }
    (BUILD / 'layout.json').write_text(json.dumps(layout, indent=2) + '\n')
    print(json.dumps(layout, indent=2))


if __name__ == '__main__':
    main()
