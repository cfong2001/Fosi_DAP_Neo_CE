#!/bin/sh
# The former extension base 0x03079C14 is live workspace. Build only
# the validated tail placement; this output is a routine, not an image.
set -eu
cd "$(dirname "$0")"
mkdir -p scratch
exec python3 build_bt_tail.py --output scratch/bt-tail.bin "$@"
