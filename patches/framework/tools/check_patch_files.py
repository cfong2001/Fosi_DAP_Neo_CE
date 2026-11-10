#!/usr/bin/env python3
"""CI checker for the patch framework: every patch file must parse with
the framework's own parser (build.parse_patch), and every manifest
entry must exist. Needs no firmware image, so it can run in GitHub
Actions; image-level verification (verify.py) runs locally."""
import sys
from pathlib import Path

FW = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(FW))
import build as fw_build  # patches/framework/build.py

patch_dir = FW / "patches"
files = sorted(patch_dir.glob("*.patch"))
if not files:
    raise SystemExit("no patch files found")
for f in files:
    fw_build.parse_patch(str(f))
    print(f"OK {f.name}")
listed = []
for line in (patch_dir / "manifest.txt").read_text().splitlines():
    entry = line.split("#", 1)[0].strip()
    if entry:
        listed.append(entry)
for name in listed:
    if not (patch_dir / name).exists():
        raise SystemExit(f"manifest lists missing file: {name}")
print(f"{len(files)} patch file(s) parse; {len(listed)} manifest entry(ies) OK")
filters = sorted((FW.parent / "dac_filter").glob("*.patch"))
for f in filters:
    p = fw_build.parse_patch(str(f))
    if (p["module"], p["address"], p["expect"]) != (0, 0x03051814, bytes.fromhex("0221")):
        raise SystemExit(f"{f.name}: a DAC filter patch must target the mode-0 immediate")
    print(f"OK {f.name}")
if sorted(fw_build.DAC_FILTERS.values()) != [f.name for f in filters]:
    raise SystemExit("build.py DAC_FILTERS does not match patches/dac_filter/")
print(f"{len(filters)} DAC filter patch(es) match build.py")
autooff = sorted((FW.parent / "bt_auto_off").glob("*.patch"))
for f in autooff:
    p = fw_build.parse_patch(str(f))
    if p["module"] != 0 or p["address"] not in (0x030661E0, 0x030661E6):
        raise SystemExit(f"{f.name}: a Bluetooth auto-off patch must target the supervisor limit check")
    print(f"OK {f.name}")
if sorted(fw_build.BT_AUTO_OFF.values()) != [f.name for f in autooff]:
    raise SystemExit("build.py BT_AUTO_OFF does not match patches/bt_auto_off/")
print(f"{len(autooff)} Bluetooth auto-off patch(es) match build.py")
