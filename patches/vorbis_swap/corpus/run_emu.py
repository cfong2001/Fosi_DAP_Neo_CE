#!/usr/bin/env python3
"""Batch-decode the whole corpus under emu75.py with stock and transplanted
module 75. Resumable: existing outputs are skipped. Logs per-decode facts
(frames, rate, bps, stack high-water, wall time) to emu_runs.json.

Run:  venv/bin/python work/vorbis_corpus/run_emu.py
"""
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SWAP = HERE.parent / "patches" / "vorbis_swap"
EMU = SWAP / "emu75.py"
MODULES = {
    "stock": f"{SWAP}/module75_stock_code.bin,{SWAP}/module75_stock_data.bin",
    "patched": f"{SWAP}/module75_patched_code.bin,{SWAP}/module75_patched_data.bin",
}
OUT = HERE / "outputs"
PY = sys.executable


def main():
    OUT.mkdir(exist_ok=True)
    manifest = json.loads((HERE / "manifest.json").read_text())
    runs_path = HERE / "emu_runs.json"
    runs = json.loads(runs_path.read_text()) if runs_path.exists() else {}
    for entry in manifest["files"]:
        stem = Path(entry["file"]).stem
        ogg = HERE / "corpus" / entry["file"]
        for mod, segs in MODULES.items():
            key = f"{stem}__{mod}"
            out = OUT / f"{key}.s16"
            if key in runs and out.exists():
                continue
            t0 = time.time()
            p = subprocess.run([PY, str(EMU), segs, str(ogg), str(out)],
                               capture_output=True, text=True)
            wall = time.time() - t0
            tail = [ln for ln in p.stdout.splitlines() if ln.strip()]
            runs[key] = {"module": mod, "file": entry["file"], "rc": p.returncode,
                         "wall_s": round(wall, 2), "out_bytes": out.stat().st_size
                         if out.exists() else 0,
                         "info": tail[1] if len(tail) > 1 else "",
                         "frames_line": tail[2] if len(tail) > 2 else "",
                         "stack_line": tail[-1] if tail else "",
                         "stderr": p.stderr[-300:]}
            runs_path.write_text(json.dumps(runs, indent=1))
            print(key, "rc", p.returncode, f"{wall:.1f}s",
                  runs[key]["frames_line"][:60], flush=True)
            if p.returncode != 0:
                print(p.stdout[-500:], p.stderr[-500:], flush=True)
    print("done:", len(runs), "runs")


if __name__ == "__main__":
    sys.exit(main())
