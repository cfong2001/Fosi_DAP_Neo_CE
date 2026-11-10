#!/usr/bin/env python3
"""Build the Bluetooth routine for the shared experimental gap tail.

The resulting file is the routine only, linked at 0x0307c5f8. It is not
a firmware image or a standalone tail payload. Combine it with the M3U
tail layout and dispatcher patch 0032-tail; the old patch 0032 targets a
withdrawn placement and must not be used. Run the Unicorn suite on the
resulting image before using it. No image is flashed by this script.
"""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
BASE = 0x0307C5F8
END = 0x0307C7B0
VALIDATED_SHA256 = 'ce6ef701285885efb17b072df128602c3ee5da8359b7b267cd7e1ca92457cf06'


def run(*args):
    return subprocess.run(args, check=True, text=True, capture_output=True).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='write the binary routine to this path')
    parser.add_argument('--prefix', default=os.environ.get('CROSS_COMPILE', 'arm-none-eabi-'),
                        help='cross tool prefix, default arm-none-eabi-')
    args = parser.parse_args()
    cc = args.prefix + 'gcc'
    flags = ['-mcpu=cortex-m3', '-mthumb', '-Os', '-ffreestanding',
             '-fno-builtin', '-nostdlib', '-Wall', '-Wextra', '-Werror']
    with tempfile.TemporaryDirectory(prefix='fosi-bt-') as tmp:
        tmp = Path(tmp)
        objects = []
        for name in ('hooks.S', 'bt_toggle.c'):
            obj = tmp / (name + '.o')
            run(cc, *flags, '-c', str(HERE / 'src' / name), '-o', str(obj))
            objects.append(str(obj))
        script = tmp / 'tail.ld'
        script.write_text('''SECTIONS {
 . = 0x0307C5F8;
 .text : { *(.text.hook) *(.text) *(.text.*) }
 .rodata : { *(.rodata) *(.rodata.*) }
 .data : { *(.data) *(.data.*) }
 .bss : { *(.bss) *(.bss.*) *(COMMON) }
 /DISCARD/ : { *(.comment) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }
 ASSERT(SIZEOF(.bss) == 0, "Bluetooth tail must not need BSS")
 ASSERT(. <= 0x0307C7B0, "Bluetooth tail exceeds reserved space")
}\n''')
        elf = tmp / 'bt.elf'
        run(cc, *flags, '-T', str(script), *objects, '-o', str(elf))
        symbols = run(args.prefix + 'nm', '-n', str(elf))
        if not any(line.split() == [f'{BASE:08x}', 'T', 'ui_dispatcher_hook']
                   for line in symbols.splitlines()):
            raise ValueError('dispatcher hook is not at the pinned tail address')
        if run(args.prefix + 'nm', '-u', str(elf)).strip():
            raise ValueError('Bluetooth payload has unresolved symbols')
        binary = tmp / 'bt.bin'
        run(args.prefix + 'objcopy', '-O', 'binary', str(elf), str(binary))
        data = binary.read_bytes()
        if not data or len(data) > END - BASE:
            raise ValueError('Bluetooth payload does not fit its reserved tail')
        digest = hashlib.sha256(data).hexdigest()
        if digest != VALIDATED_SHA256:
            raise ValueError(f'Bluetooth payload hash {digest} does not match the '
                             'emulation-validated build; use GCC 14.2.1 and binutils 2.44')
        args.output.write_bytes(data)
        print(f'Bluetooth routine: {len(data)} bytes, SHA-256 {digest}')


if __name__ == '__main__':
    main()
