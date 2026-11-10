#!/bin/sh
# Build the battery-profile blob and the two patch-site byte strings.
# Offline and scratch only: outputs land in this directory's out/.
set -eu
cd "$(dirname "$0")"

CC=arm-none-eabi-gcc
CFLAGS="-mcpu=cortex-m3 -mthumb -Os -ffreestanding -nostdlib \
        -fno-unwind-tables -fno-asynchronous-unwind-tables -Wall -Wextra"

mkdir -p out
$CC $CFLAGS -c src/profiles.c -o out/profiles.o
$CC $CFLAGS -c src/hooks.S    -o out/hooks.o
$CC $CFLAGS -c src/sites.S    -o out/sites.o
$CC $CFLAGS -T src/profiles.ld -o out/profiles.elf \
    out/profiles.o out/hooks.o out/sites.o

arm-none-eabi-objcopy -O binary -j .text -j .rodata \
    out/profiles.elf out/blob.bin
arm-none-eabi-objcopy -O binary -j .site_a out/profiles.elf out/site_a.bin
arm-none-eabi-objcopy -O binary -j .site_b out/profiles.elf out/site_b.bin

echo "== validate linked payload and branch sites =="
python3 audit_artifacts.py out/profiles.elf out/blob.bin out/site_a.bin out/site_b.bin
echo "== symbols =="
arm-none-eabi-nm out/profiles.elf | grep -i ' [tTrR] ' || true
echo "== sizes =="
wc -c out/blob.bin out/site_a.bin out/site_b.bin
echo "== site bytes =="
printf 'site_a: '; od -An -tx1 out/site_a.bin | tr -d ' \n'; echo
printf 'site_b: '; od -An -tx1 out/site_b.bin | tr -d ' \n'; echo
