#!/bin/sh
# Build the lock-screen blob (standalone link at the module 31 segment
# extension base 0x0307EE48) and the patch 0033 branch bytes.
set -e
cd "$(dirname "$0")"
CC=arm-none-eabi-gcc
CFLAGS="-mcpu=cortex-m3 -mthumb -Os -ffreestanding -fno-builtin -nostdlib -Wall -Wextra"
LIBGCC=$($CC -print-libgcc-file-name)
mkdir -p scratch
$CC $CFLAGS -c src/lockscreen.c -o scratch/lockscreen.o
$CC $CFLAGS -T src/lockscreen.ld scratch/lockscreen.o "$LIBGCC" \
    -o scratch/lockscreen.elf -Wl,-Map,scratch/lockscreen.map
arm-none-eabi-objcopy -O binary scratch/lockscreen.elf scratch/lockscreen.bin
# Patch-site branch bytes: assemble the B.W at the site address.
$CC -mcpu=cortex-m3 -mthumb -c src/site33.S -o scratch/site33.o
$CC -mcpu=cortex-m3 -mthumb -nostdlib -T src/site33.ld scratch/site33.o -o scratch/site33.elf
arm-none-eabi-objcopy -O binary scratch/site33.elf scratch/site33.bin
site=$(od -An -tx1 scratch/site33.bin | tr -d ' \n')
if [ "$site" != 00f0d3ba ]; then
    echo "Unexpected standalone 0033 branch: $site" >&2
    exit 1
fi
ls -l scratch/lockscreen.bin scratch/site33.bin
arm-none-eabi-nm scratch/lockscreen.elf | grep -i ' [TtDdRr] '
echo "site33 replace bytes: $site"
