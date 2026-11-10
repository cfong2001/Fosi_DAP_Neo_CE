# Bluetooth shortcut tail build

The earlier `0x03079C14` extension placement is withdrawn: it overlaps
runtime workspace. Build the Bluetooth routine for the reserved tail using
GNU Arm Embedded GCC 14.2.1 and binutils 2.44, or the reference toolchain from
`ci/install_reference_toolchain.sh` (GCC 13.2.1, binutils 2.44), which
reproduces the same 436-byte payload (SHA-256 `ce6ef701…`):

```sh
python3 patches/ui_features/build/build_bt_tail.py --output /tmp/bt-tail.bin
```

The script rejects binaries whose SHA-256 differs from the build tested in
the six-case emulator. The routine is linked at `0x0307C5F8`; it is not an
image and cannot be used with the old `0032-ui-bt-dispatcher-hook.patch`.
For a Bluetooth-only framework build, prepend `0x644` zero bytes to the
routine, pass that file as `--tail`, and include the paired
`patches/m3u/tail_build/patches/0032-ui-bt-dispatcher-hook-tail.patch` in the
manifest. The padding reserves the M3U staging and resolver region, so the
same Bluetooth address may be used in a combined build. Build compositions
must check that each tail occupant fits without overlap.

With Unicorn installed, run the patched image through:

```sh
python3 patches/ui_features/build/emu/emu_bt.py /path/to/built.img
```

The suite covers on, off, timeout and three unrelated input events. It
intercepts delays and does not model a real Bluetooth receiver or device.
The gap-tail canary and actual power, input and playback behavior remain
unverified on hardware. The toggle may wait up to five seconds for the
receiver banner in the dispatcher path.
