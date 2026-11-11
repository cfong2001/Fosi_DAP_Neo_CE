#!/usr/bin/env python3
"""Validation build for the browser icon set.

Builds two images in memory with the framework build.py (nothing
is written to disk):

  1. the default build (framework manifest, no theme config),
     whose SHA-256 must equal the pinned default
     92c446066e715d74a719671d3ee643ed4b7587c94801eb6dc3893f2271ed944d,
     proving the default build is untouched;
  2. the validation build: the v4 manifest (the default patch set
     plus the eight transport repoint patches) and a merged theme
     config carrying the v4 runs plus the browser runs. Every
     browser resource in the output must equal its
     icon_set_browser/asset_<id>.bin byte for byte, and every v4
     resource must still equal its icon_set_v4 asset, proving the
     sets compose without interference.

Needs the transplant inputs: set FOSI_ECPATCH_DIR as for the v4
gate suite.
"""
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image  # noqa: E402

RAW = (ROOT / 'DP3_V137.img').read_bytes()
assert hashlib.sha256(RAW).hexdigest() == \
    'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
DEFAULT_SHA = '92c446066e715d74a719671d3ee643ed4b7587c94801eb6dc3' \
              '893f2271ed944d'


def load_build():
    spec = importlib.util.spec_from_file_location(
        'fwbuild', ROOT / 'patches' / 'framework' / 'build.py')
    fb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fb)
    return fb


def main():
    fb = load_build()
    names = fb.load_transplant_names(
        ROOT / 'patches' / 'framework' / 'patches' / 'transplants.txt')
    ecp = os.environ.get('FOSI_ECPATCH_DIR')
    ecp = Path(ecp) if ecp else None

    out, report = fb.build_image(
        RAW, fb.load_manifest(
            ROOT / 'patches' / 'framework' / 'patches' / 'manifest.txt'),
        fb.DEFAULT_BUILD_DATE, transplants=names, ecpatch_dir=ecp)
    sha = report['output_sha256']
    print(f'default build SHA-256: {sha}')
    assert sha == DEFAULT_SHA, 'default build pin moved'
    print('default build: pin matches, untouched')

    v4 = json.loads((HERE.parent / 'v4-glyphs.json').read_text())
    browser = json.loads((HERE / 'browser-glyphs.json').read_text())
    merged = {'version': 1, 'literal_sites': [],
              'runs': v4['runs'] + browser['runs']}
    out, report = fb.build_image(
        RAW, fb.load_manifest(HERE.parent / 'manifest-v4.txt'),
        fb.DEFAULT_BUILD_DATE, transplants=names, ecpatch_dir=ecp,
        theme_config=merged)
    sha = report['output_sha256']
    print(f'validation build SHA-256: {sha}')

    entries = {e['id']: e for e in Image(out).images()}
    bad = []
    for asset_dir, count in ((HERE / 'icon_set_browser', 38),
                             (HERE.parent / 'icon_set_v4', 54)):
        mapping = json.loads((asset_dir / 'mapping.json').read_text())
        assert mapping['count'] == count, (asset_dir, mapping['count'])
        for a in mapping['assets']:
            e = entries[a['id']]
            got = out[e['data_offset']:e['data_offset'] + e['size']]
            want = (asset_dir / f"asset_{a['id']}.bin").read_bytes()
            if got != want:
                bad.append(a['id'])
    assert not bad, f'resources not byte-exact in build: {bad}'
    print('validation build: all 38 browser resources and all 54 '
          'v4 resources match their .bin files byte for byte')
    print('PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
