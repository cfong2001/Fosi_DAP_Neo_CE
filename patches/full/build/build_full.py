#!/usr/bin/env python3
"""Build the unified "everything" CE image in one build.py pass.

Recipe (all steps deterministic, offline, nothing flashed):

  1. build_compose.py    module 31 payload (trampoline with the
                         playlist start exit, bridge + parser at
                         6 / 59 staging caps, lock routine, disarm
                         stubs) and patches 0033 / 0040 / 0060 / 0061
  2. patches/navigation/build_tag_exit.py
                         tag-library disarm stub (26 B, module 24
                         extension); patch 0062 is checked in
  3. build_tail.py       merged gap tail (staging + resolver +
                         theater + Bluetooth, 2,040 B) and patches
                         0041 / 0042 / 0100..0104
  4. build_theme.py      merged theme config (v4 glyph runs + CE
                         mark runs, offsets shifted by the growth)
  5. patches/framework/build.py with patches/full/manifest.txt
     (60 patches), patches/full/transplants.txt (vorbis75 +
     opus72), two --grow insertions, the merged --tail and the
     merged --theme-config.

The ebook reader (module 30) is NOT shrunk: a fail-safe stub could
not be proven against the window-dispatch contract, so the image is
longer than stock by exactly the two insertions. See README.md.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FULL = HERE.parent
OUT = FULL / 'out'
REPO = FULL.parents[1]
PY = sys.executable


def run(cmd, **kw):
    print('+', ' '.join(str(c) for c in cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.stdout:
        print(r.stdout, end='')
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        raise SystemExit(f'command failed: {cmd[0]}')
    return r


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def check_output_paths(input_path, output):
    """Preserve stock, existing outputs, and reports before any build work."""
    report = Path(str(output) + '.report.json')
    if output.resolve() == input_path.resolve() or report.resolve() == input_path.resolve():
        raise ValueError('output or report resolves to the input image')
    for path in (output, report):
        if path.exists() or path.is_symlink():
            raise ValueError(f'output or report already exists: {path}')
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path,
                    default=OUT / 'DP3_V137_CE_full.img')
    ap.add_argument('--ecpatch-dir', type=Path, required=True,
                    help='directory with the HIFIEC*.ecpatch inputs')
    ap.add_argument('--dac-filter', default=None,
                    help='passed to build.py --dac-filter (one of the '
                         'four non-default CS43198 filters)')
    ap.add_argument('--bt-auto-off', default=None,
                    help='passed to build.py --bt-auto-off (10min or never)')
    a = ap.parse_args()
    input_path = REPO / 'DP3_V137.img'
    try:
        report = check_output_paths(input_path, a.output)
    except ValueError as exc:
        ap.error(str(exc))
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='fosi-full-') as tmp:
        scratch = Path(tmp)
        run([PY, str(HERE / 'build_compose.py'),
             '--scratch', str(scratch / 'compose')])
        run([PY, str(REPO / 'patches' / 'navigation' / 'build_tag_exit.py'),
             '--output', str(OUT / 'tag24.bin')])
        if len((OUT / 'tag24.bin').read_bytes()) != 26:
            raise SystemExit('tag stub length changed')
        run([PY, str(HERE / 'build_tail.py')])
        run([PY, str(HERE / 'build_sort_extension.py')])
        run([PY, str(HERE / 'build_focus_wheel.py')])
        run([PY, str(HERE / 'build_theme.py')])

    output = a.output
    run([PY, str(REPO / 'patches' / 'framework' / 'build.py'),
         '--input', str(input_path),
         '--output', str(output),
         '--manifest', str(FULL / 'manifest.txt'),
         '--transplants', str(FULL / 'transplants.txt'),
         '--ecpatch-dir', str(a.ecpatch_dir),
         '--grow', f'31:code:{OUT / "payload31.bin"}',
         '--grow', f'24:code:{OUT / "tag24.bin"}',
         '--grow', f'39:code:{OUT / "sort39.bin"}',
         '--tail', str(OUT / 'tail-full.bin'),
         '--theme-config', str(OUT / 'theme-full.json')]
        + (['--dac-filter', a.dac_filter] if a.dac_filter else [])
        + (['--bt-auto-off', a.bt_auto_off] if a.bt_auto_off else []))
    data = output.read_bytes()
    rep = json.loads(report.read_text())
    print(f'full image: {len(data)} bytes, sha256 {sha(output)}')
    print(f'patches applied: {len(rep["patches_applied"])}; '
          f'transplants: {len(rep["transplants_applied"])}; '
          f'growths: {[(g["module"], g["payload_bytes"]) for g in rep["growth"]]}')
    stock = len(input_path.read_bytes())
    print(f'length ledger: stock {stock}; growth '
          f'{len(data) - stock:+d}; final {len(data)}')


if __name__ == '__main__':
    main()
