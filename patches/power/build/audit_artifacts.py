#!/usr/bin/env python3
"""Refuse a profile blob that no longer matches its fixed-address hooks."""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED_HOOKS = {"hook_dispatch_a": 0x03080664,
                  "hook_dispatch_b": 0x0308067A}


def audit(symbols, undefined, blob, sites):
    if undefined.strip():
        raise ValueError("unresolved symbols: " + undefined.strip())
    for name, address in EXPECTED_HOOKS.items():
        if symbols.get(name) != address:
            raise ValueError(f"{name}: expected {address:#x}, got {symbols.get(name)!r}")
    if len(blob) != 540:
        raise ValueError(f"profile blob is {len(blob)} bytes; expected 540")
    for name, actual in zip(("0051-profile-selector-dispatch-a.patch",
                             "0052-profile-selector-dispatch-b.patch"), sites):
        text = (HERE / name).read_text()
        match = re.search(r"^replace:\s*([0-9a-fA-F]+)\s*$", text, re.MULTILINE)
        if not match or actual != bytes.fromhex(match.group(1)):
            raise ValueError(f"{name}: linked site bytes differ from patch")


def main():
    if len(sys.argv) != 5:
        raise SystemExit("usage: audit_artifacts.py ELF BLOB SITE_A SITE_B")
    elf, blob, site_a, site_b = map(Path, sys.argv[1:])
    output = subprocess.run(["arm-none-eabi-nm", str(elf)], check=True,
                            text=True, capture_output=True).stdout
    symbols = {}
    for line in output.splitlines():
        fields = line.split()
        if len(fields) == 3:
            symbols[fields[2]] = int(fields[0], 16)
    undefined = subprocess.run(["arm-none-eabi-nm", "-u", str(elf)],
                               check=True, text=True, capture_output=True).stdout
    audit(symbols, undefined, blob.read_bytes(),
          [site_a.read_bytes(), site_b.read_bytes()])
    print("Profile blob geometry, linked hooks, and patch sites match.")


if __name__ == "__main__":
    main()
