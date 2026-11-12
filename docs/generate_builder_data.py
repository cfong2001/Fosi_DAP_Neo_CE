#!/usr/bin/env python3
"""Generate the CE builder page's data modules from the repo's own files.

The builder page (docs/) never hand-copies patch bytes. This script
reads the framework's manifest and patch files, the CE splash mark
config, and (when their inputs are supplied) the Vorbis transplant
and the preset schemes, and emits plain data modules next to itself:

  builder-data.mjs     the manifest's byte patches, grouped for the
                       page's feature toggles, in manifest order
  builder-cemark.mjs   the runs of patches/theme_editor/ce-mark.json
  builder-theater.mjs  the theater mode hook patches and tail
                       payload from patches/theater/build/ (the
                       payload is the build_theater.py artifact
                       theater_tail.bin; regenerate it there first
                       if it is missing)
  builder-vorbis.mjs   the vorbis75 transplant as file ranges (only
                       when --ecpatch-dir is given): every byte the
                       transplant changes, coalesced, plus a SHA-256
                       pin of the transplanted module 75 segments
  builder-presets.mjs  the preset schemes (only when scheme files
                       are given): CE Standard and CE Tidepool from
                       the design refresh's provisional scheme files,
                       converted to the studio's theme format, and
                       CE Standard v2 and CE Dust, which already are
                       studio-format configs
  builder-opus-data.mjs
                       the opus72 transplant as file ranges (only
                       when --ecpatch-dir is given); the page loads it
                       on demand and checks the transplanted module
                       72 against its pinned SHA-256 before use
  builder-payloads.mjs the standalone Bluetooth shortcut and
                       lock-screen routines (only when --bt-tail and
                       --lock-payload are given), each checked here
                       against its pinned SHA-256; build them with
                       patches/ui_features/build/build_bt_tail.py and
                       patches/ui_features/lockscreen_build/build.sh
                       using the reference toolchain
                       (ci/install_reference_toolchain.sh)
  builder-full.mjs     the unified everything build
                       (patches/full/): the manifest's patches
                       beyond the framework set and the Opus
                       renames, the merged gap tail, the growth
                       payloads and the merged theme runs
                       at stock offsets, each pinned by SHA-256;
                       requires the artifacts under
                       patches/full/out/ (run
                       patches/full/build/build_full.py first)

Every emitted count and byte range is recomputed from the pinned
stock image and checked while generating; a mismatch aborts the
generation instead of shipping stale data.

Usage (from the repo root):

  python3 docs/generate_builder_data.py \
      [--stock DP3_V137.img] [--ecpatch-dir DIR] \
      [--scheme-v1-standard FILE] [--scheme-v1-tidepool FILE] \
      [--scheme-v2-standard FILE] [--scheme-v2-dust FILE]

The transplant inputs (HIFIEC*.ecpatch) are not in this repo; the
--ecpatch-dir flag names the same directory build.py's
FOSI_ECPATCH_DIR names. The v1 scheme files are provisional-format
documents from the design refresh work; the conversion below maps
their per-asset recolors onto studio roles: source words are
byte-swapped from the v1 files' big-endian naming to the studio's
little-endian naming (the counts are over the same stored bytes and
are rechecked), and each distinct target colour is expressed
through one palette role whose #RRGGBB value converts back to
exactly that RGB565 word under the studio's rgb565().
"""
import argparse
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

STOCK_SHA256 = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
THEATER_TAIL_SHA256 = '96931a93bd197782f5efda40974ab31731c801e4231f29f44c1dfa7347c0fc78'
BT_PAYLOAD_SHA256 = 'ce6ef701285885efb17b072df128602c3ee5da8359b7b267cd7e1ca92457cf06'
LOCK_PAYLOAD_SHA256 = '9610d8d7995d821b4289c18e720c21c848494633d2af097e160101a23e2c92d2'
FULL_IMAGE_SHA256 = '317afcac28fdbb5a37e442a2d223a311f35fee06e9c22cd204735fd1c4fef297'
FULL_TAIL_SHA256 = '1443d354b9a388f156d23178eb302b7535e703b0e3295d8dc329cd7b71820f69'
FULL_GROWTH_PINS = ((31, 'payload31.bin',
                     '3f7e09cae9658c4cf21bfc4f9be92a037051f10a74e759f2e7fd8d4c0cac2aa9'),
                    (24, 'tag24.bin',
                     '7b80afb308d276a4d0012cd4302f7a5f2a1c5192a1f2e70d3f23867e195a942a'))
ROLES = ('background', 'text', 'highlight', 'icons', 'progress_bar')
GUARD_WORDS = (0x0000, 0x00F8)

# Feature groups for the page's toggles, by patch-file number.
# Mirrors the component grouping in patches/framework/README.md.
GROUPS = [
    ('fixture', 'Self-test fixture',
     'The 0000 no-op self-test fixture. build.py always applies it; '
     'its replacement bytes equal the stock bytes.', (0,)),
    ('dac', 'DAC error-counter fix',
     'Patches 0001 and 0002: the DAC error counter counts '
     'consecutive failed I2C transactions instead of total ones.',
     (1, 2)),
    ('clock', 'Clock table v1',
     'Patches 0003 to 0018: per-codec clock rows lowered, never '
     'below the RKNanoD SDK figure for the format.', tuple(range(3, 19))),
    ('gapless', 'Gapless fast path',
     'Patches 0019 to 0026 and 0034: at a natural end of track the '
     'decoder core keeps running, same-format tracks reuse it and '
     'start without the start-up silence; 0019 shortens the DAC bus '
     'I2C reset hold.',
     tuple(range(19, 27)) + (34,)),
    ('sort', 'Natural sort keys',
     'Patches 0027 to 0031: library sort folds case and accents '
     'and compares digit runs as numbers.', tuple(range(27, 32))),
    ('wheel', 'Wheel power patch',
     'Patch 0050: the wheel timer period goes from 400 to '
     '1000 microseconds.', (50,)),
]


def parse_patch(path):
    """The framework's patch-file format (build.py's parse_patch):
    `key: value` lines, `#` comments, indented continuations."""
    fields = {}
    key = None
    for line in Path(path).read_text().splitlines():
        if line.startswith('#') or not line.strip():
            continue
        if line[0] in ' \t' and key is not None:
            fields[key] += ' ' + line.strip()
            continue
        k, sep, v = line.partition(':')
        if not sep:
            raise ValueError(f'{path}: malformed line: {line!r}')
        key = k.strip().lower()
        fields[key] = v.strip()
    if fields.get('kind') != 'module':
        raise ValueError(f'{path}: builder data covers module patches only')
    return {'file': Path(path).name,
            'name': fields['name'],
            'module': int(fields['module']),
            'region': fields['region'],
            'address': int(fields['address'], 0),
            'expect': fields['expect'],
            'replace': fields['replace']}


def rgb565(hexs):
    r, g, b = (int(hexs[i:i + 2], 16) for i in (1, 3, 5))
    return (((r * 31 + 127) // 255) << 11
            | ((g * 63 + 127) // 255) << 5
            | ((b * 31 + 127) // 255))


def rgb888_hex(word):
    r = ((word >> 11) & 31) * 255 // 31
    g = ((word >> 5) & 63) * 255 // 63
    b = (word & 31) * 255 // 31
    return '#%02X%02X%02X' % (r, g, b)


def rock26_entries(stock):
    start, length = struct.unpack_from('<II', stock, 0x14C)
    assert stock[start:start + 16] == b'ROCK26IMAGERES  '
    count = struct.unpack_from('<I', stock, start + 16)[0]
    entries = []
    for i in range(count):
        w, h, _x, _y, size, off = struct.unpack_from(
            '<4H2I', stock, start + 0x20 + i * 16)
        assert size == w * h * 2
        entries.append({'id': i, 'size': size, 'data_offset': start + off})
    return entries


def le_word_count(stock, entry, word):
    base, size = entry['data_offset'], entry['size']
    needle = struct.pack('<H', word)
    return sum(1 for i in range(size // 2)
               if stock[base + 2 * i:base + 2 * i + 2] == needle)


def check_rule_counts(stock, entries, config, label):
    for rule in config['resources']:
        actual = le_word_count(stock, entries[rule['id']],
                               int(rule['source'], 16))
        assert actual == rule['expected_count'], (
            f'{label}: asset {rule["id"]} source {rule["source"]} '
            f'count {actual} != {rule["expected_count"]}')
        assert int(rule['source'], 16) not in GUARD_WORDS


def swap16(word):
    return ((word & 0xFF) << 8) | (word >> 8)


def convert_v1_scheme(stock, entries, scheme, label):
    """Map a provisional v1 scheme onto a studio theme config.

    Distinct target colours take roles in first-appearance order;
    unused roles are filled from the scheme's dark palette so the
    loaded editor state still reads as the scheme."""
    targets = []
    for rec in scheme['recolors']:
        to = int(rec['to_rgb565'], 16)
        if to not in targets:
            targets.append(to)
    role_cycle = ('highlight', 'background', 'icons', 'text', 'progress_bar')
    assert len(targets) <= len(role_cycle)
    role_of = {t: role_cycle[i] for i, t in enumerate(targets)}
    palette = {}
    for t, role in role_of.items():
        hexs = rgb888_hex(t)
        assert rgb565(hexs) == t, (label, hex(t))
        palette[role] = hexs
    dark = scheme['palette']['dark']
    fill = {'text': dark['foreground']['hex'],
            'progress_bar': dark['accent']['hex'],
            'background': dark['background']['hex'],
            'icons': dark['foreground']['hex'],
            'highlight': dark['accent']['hex']}
    for role in ROLES:
        palette.setdefault(role, fill[role])
    resources = []
    for rec in scheme['recolors']:
        source = swap16(int(rec['from_rgb565'], 16))
        resources.append({'id': rec['asset'],
                          'role': role_of[int(rec['to_rgb565'], 16)],
                          'source': '0x%04X' % source,
                          'expected_count': rec['count']})
    config = {'version': 1, 'palette': palette, 'resources': resources,
              'literal_sites': []}
    check_rule_counts(stock, entries, config, label)
    return config


def js(obj):
    return json.dumps(obj, indent=1)


def opus_ranges(stock, ecpatch_dir):
    """Produce only the pinned-input Opus byte ranges for local use."""
    sys.path.insert(0, str(ROOT / 'tools'))
    spec = importlib.util.spec_from_file_location(
        'transplant_opus', ROOT / 'patches' / 'opus_swap' / 'transplant.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out, record = mod.apply_transplant(stock, ecpatch_dir)
    ranges, start = [], None
    for i, (before, after) in enumerate(zip(stock, out)):
        if before != after and start is None:
            start = i
        if start is not None and (before == after or i == len(stock) - 1):
            end = i if before != after else i - 1
            assert any(s <= start <= end <= e for s, e in record['ranges'])
            ranges.append({'offset': start, 'replace': out[start:end + 1].hex()})
            start = None
    return ranges


def check_opus_output(stock_path, output):
    """Refuse to replace an input image or an existing local output."""
    if output.resolve() == stock_path.resolve():
        raise ValueError('Opus output resolves to the stock image')
    if output.exists() or output.is_symlink():
        raise ValueError(f'Opus output already exists: {output}')


def write_opus_output(output, ranges):
    # Exclusive creation also prevents an output appearing after preflight
    # from being overwritten. A dangling symbolic link is rejected by 'x'.
    with output.open('x', encoding='utf-8') as stream:
        json.dump({'ranges': ranges}, stream)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stock', type=Path, default=ROOT / 'DP3_V137.img')
    ap.add_argument('--ecpatch-dir', type=Path, default=None)
    ap.add_argument('--opus-data', type=Path, default=None,
                    help='write local Opus range JSON here (do not publish it)')
    ap.add_argument('--opus-data-only', action='store_true',
                    help='generate only the local Opus JSON; no other build artifacts required')
    ap.add_argument('--scheme-v1-standard', type=Path, default=None)
    ap.add_argument('--scheme-v1-tidepool', type=Path, default=None)
    ap.add_argument('--scheme-v2-standard', type=Path, default=None)
    ap.add_argument('--scheme-v2-dust', type=Path, default=None)
    ap.add_argument('--bt-tail', type=Path, default=None,
                    help='bt-tail.bin from build_bt_tail.py')
    ap.add_argument('--lock-payload', type=Path, default=None,
                    help='lockscreen.bin from lockscreen_build/build.sh')
    ap.add_argument('--out-dir', type=Path, default=HERE)
    a = ap.parse_args()

    if a.opus_data_only and (a.opus_data is None or a.ecpatch_dir is None):
        ap.error('--opus-data-only requires --opus-data and --ecpatch-dir')
    if a.opus_data is not None:
        try:
            check_opus_output(a.stock, a.opus_data)
        except ValueError as exc:
            ap.error(str(exc))

    stock = a.stock.read_bytes()
    assert hashlib.sha256(stock).hexdigest() == STOCK_SHA256, \
        'stock image does not match the pinned SHA-256'
    if a.opus_data_only:
        ranges = opus_ranges(stock, a.ecpatch_dir)
        write_opus_output(a.opus_data, ranges)
        print('Opus data:', len(ranges), 'ranges written locally')
        return

    # ---- byte patches, grouped, in manifest order
    manifest = ROOT / 'patches' / 'framework' / 'patches' / 'manifest.txt'
    names = []
    for line in manifest.read_text().splitlines():
        line = line.split('#', 1)[0].strip()
        if line:
            names.append(line)
    patches = [parse_patch(manifest.parent / n) for n in names]
    group_of = {}
    for gid, _label, _blurb, numbers in GROUPS:
        for n in numbers:
            group_of[n] = gid
    grouped = {gid: [] for gid, _l, _b, _n in GROUPS}
    for index, (name, patch) in enumerate(zip(names, patches)):
        number = int(name.split('-', 1)[0])
        assert number in group_of, f'{name}: no feature group'
        patch = dict(patch)
        patch['index'] = index
        grouped[group_of[number]].append(patch)
    assert sum(len(v) for v in grouped.values()) == len(patches) == 34
    groups_out = [{'id': gid, 'label': label, 'blurb': blurb,
                   'patches': grouped[gid]}
                  for gid, label, blurb, _n in GROUPS]
    (a.out_dir / 'builder-data.mjs').write_text(
        '// Generated by docs/generate_builder_data.py from '
        'patches/framework/patches/\n'
        '// (manifest.txt order). Do not edit by hand.\n'
        'export const PATCH_GROUPS = ' + js(groups_out) + ';\n')
    print('builder-data.mjs: 34 patches in', len(groups_out), 'groups')

    # ---- CE splash mark runs
    cemark = json.loads(
        (ROOT / 'patches' / 'theme_editor' / 'ce-mark.json').read_text())
    runs = [{'offset': int(r['offset'], 0) if isinstance(r['offset'], str)
             else r['offset'],
             'expect': r['expect'], 'replace': r['replace']}
            for r in cemark['runs']]
    (a.out_dir / 'builder-cemark.mjs').write_text(
        '// Generated by docs/generate_builder_data.py from '
        'patches/theme_editor/ce-mark.json.\n'
        '// Do not edit by hand.\n'
        'export const CE_MARK_RUNS = ' + js(runs) + ';\n')
    print('builder-cemark.mjs:', len(runs), 'runs,',
          sum(len(bytes.fromhex(r['expect'])) for r in runs), 'bytes')

    # ---- theater mode hook patches and tail payload
    theater_dir = ROOT / 'patches' / 'theater' / 'build'
    tail_path = theater_dir / 'theater_tail.bin'
    assert tail_path.exists(), (
        'patches/theater/build/theater_tail.bin is missing; run '
        'patches/theater/build/build_theater.py first')
    payload = tail_path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    assert digest == THEATER_TAIL_SHA256, \
        'theater tail payload does not match its pinned SHA-256'
    theater_patches = []
    for path in sorted(theater_dir.glob('010*.patch')):
        patch = parse_patch(path)
        patch['index'] = int(path.name.split('-', 1)[0])
        theater_patches.append(patch)
    assert [p['index'] for p in theater_patches] == [100, 101, 102, 103, 104]
    theater = {'patches': theater_patches,
               'tail': {'length': len(payload), 'sha256': digest,
                        'hex': payload.hex()}}
    (a.out_dir / 'builder-theater.mjs').write_text(
        '// Generated by docs/generate_builder_data.py from '
        'patches/theater/build/\n'
        '// (the five hook patches and the build_theater.py tail '
        'payload, SHA-256\n'
        '// pinned). Do not edit by hand.\n'
        'export const THEATER_PATCHES = ' + js(theater['patches']) + ';\n'
        'export const THEATER_TAIL = ' + js(theater['tail']) + ';\n')
    print('builder-theater.mjs:', len(theater_patches), 'hook patches,',
          len(payload), 'tail bytes, sha256', digest[:16] + '...')

    # ---- vorbis75 transplant as ranges
    if a.ecpatch_dir is not None:
        sys.path.insert(0, str(ROOT / 'tools'))
        spec = importlib.util.spec_from_file_location(
            'transplant_vorbis',
            ROOT / 'patches' / 'vorbis_swap' / 'transplant.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out, record = mod.apply_transplant(stock, a.ecpatch_dir)
        ranges = []
        start = prev = None
        for i in range(len(stock)):
            if stock[i] != out[i]:
                if start is None:
                    start = prev = i
                elif i == prev + 1:
                    prev = i
                else:
                    ranges.append((start, prev))
                    start = prev = i
        if start is not None:
            ranges.append((start, prev))
        claimed = set()
        for s, e in record['ranges']:
            claimed.update(range(s, e + 1))
        assert all(s in claimed and e in claimed for s, e in ranges), \
            'transplant diff escapes its claimed ranges'
        run_objs = [{'offset': s,
                     'replace': out[s:e + 1].hex()} for s, e in ranges]
        base = struct.unpack_from('<I', stock, 0x200)[0]
        rec75 = struct.unpack_from('<8I', stock, 0x208 + 75 * 32)
        seg = b''
        for load_i, len_i in ((0, 2), (3, 5)):
            off = rec75[load_i] - base + 0x200
            seg += out[off:off + rec75[len_i]]
        data = {'ranges': run_objs,
                'bytes_changed': sum(e - s + 1 for s, e in ranges),
                'module75_sha256': hashlib.sha256(seg).hexdigest()}
        (a.out_dir / 'builder-vorbis.mjs').write_text(
            '// Generated by docs/generate_builder_data.py from '
            'patches/vorbis_swap/transplant.py\n'
            '// applied to the pinned stock image: every byte the '
            'transplant changes,\n'
            '// coalesced into ranges, plus a SHA-256 pin of the '
            'transplanted module 75\n'
            '// code and data segments. Do not edit by hand.\n'
            'export const VORBIS75 = ' + js(data) + ';\n')
        print('builder-vorbis.mjs:', data['bytes_changed'],
              'bytes in', len(run_objs), 'ranges')

        # Opus is a matched set: classifier renames and module 72.
        ranges = opus_ranges(stock, a.ecpatch_dir)
        manifest = ROOT / 'patches' / 'opus_swap' / 'manifest.txt'
        names = [line.split('#', 1)[0].strip() for line in manifest.read_text().splitlines()]
        names = [name for name in names if name]
        assert len(names) == len(patches) + 5
        assert [parse_patch(manifest.parent / n) for n in names[:len(patches)]] == patches
        renames = [dict(parse_patch(manifest.parent / name), index=len(patches) + i)
                   for i, name in enumerate(names[len(patches):])]
        data = {'ranges': ranges}
        if a.opus_data:
            write_opus_output(a.opus_data, data['ranges'])
        (a.out_dir / 'builder-opus.mjs').write_text(
            '// Generated classifier patches from opus_swap. Do not edit.\n'
            'export const OPUS_PATCHES = ' + js(renames) + ';\n')
        print('builder-opus.mjs:', len(renames), 'renames;',
              len(ranges), 'ranges' + (' written locally' if a.opus_data else ''))
        (a.out_dir / 'builder-opus-data.mjs').write_text(
            '// Generated by docs/generate_builder_data.py from '
            'patches/opus_swap/transplant.py\n'
            '// applied to the pinned stock image with the pinned '
            'HIFIEC52.ecpatch\n'
            '// (berettavexee/echo-mini-opus, BSD-3-Clause; libopus '
            '(C) Xiph.Org Foundation\n'
            '// and contributors, BSD-style): every byte the transplant '
            'changes, as\n'
            '// ranges. The builder checks the transplanted module 72 '
            'against its\n'
            '// pinned SHA-256 before use. Do not edit by hand.\n'
            'export const OPUS_DATA = ' + json.dumps(data, separators=(',', ':')) + ';\n')
        print('builder-opus-data.mjs:', len(ranges), 'ranges')

    # ---- standalone Bluetooth shortcut and lock-screen routines
    if a.bt_tail or a.lock_payload:
        assert a.bt_tail and a.lock_payload, \
            '--bt-tail and --lock-payload are needed together'
        out = {}
        for key, path, length, pin in (
                ('BT_PAYLOAD', a.bt_tail, 436, BT_PAYLOAD_SHA256),
                ('LOCK_PAYLOAD', a.lock_payload, 406, LOCK_PAYLOAD_SHA256)):
            blob = path.read_bytes()
            digest = hashlib.sha256(blob).hexdigest()
            assert len(blob) == length and digest == pin, \
                f'{path} is {len(blob)} bytes, SHA-256 {digest}; expected {length}, {pin}'
            out[key] = {'length': length, 'sha256': digest, 'hex': blob.hex()}
        (a.out_dir / 'builder-payloads.mjs').write_text(
            '// Generated by docs/generate_builder_data.py from the '
            'reference-toolchain\n'
            '// builds of patches/ui_features/build/build_bt_tail.py and\n'
            '// patches/ui_features/lockscreen_build/build.sh. The '
            'builder checks each\n'
            '// against its pinned SHA-256 before use. Do not edit by hand.\n'
            + ''.join(f'export const {k} = {js(v)};\n' for k, v in out.items()))
        print('builder-payloads.mjs: Bluetooth', out['BT_PAYLOAD']['length'],
              'bytes, lock screen', out['LOCK_PAYLOAD']['length'], 'bytes')

    # ---- the unified everything build (patches/full/)
    full_dir = ROOT / 'patches' / 'full'
    full_out = full_dir / 'out'
    for needed in ('tail-full.bin', 'theme-full-stock.json',
                   *(name for _m, name, _s in FULL_GROWTH_PINS)):
        assert (full_out / needed).exists(), (
            f'patches/full/out/{needed} is missing; run '
            'patches/full/build/build_full.py with --ecpatch-dir first')
    full_names = []
    for line in (full_dir / 'manifest.txt').read_text().splitlines():
        line = line.split('#', 1)[0].strip()
        if line:
            full_names.append(line)
    assert len(full_names) == 107, len(full_names)
    full_patches = []
    for index, name in enumerate(full_names):
        patch = parse_patch(full_dir / name)
        patch['index'] = index
        full_patches.append(patch)
    # The first 38 entries are the framework set and the Opus
    # renames, which the page already carries (builder-data.mjs and
    # builder-opus.mjs); only the rest are new data here.
    for i, patch in enumerate(full_patches[:len(patches)]):
        ref = patches[i]
        assert (patch['address'], patch['expect'], patch['replace']) == \
            (ref['address'], ref['expect'], ref['replace']), patch['name']
    full_extra = full_patches[len(patches) + 5:]
    assert len(full_extra) == 68, len(full_extra)
    tail = (full_out / 'tail-full.bin').read_bytes()
    tail_digest = hashlib.sha256(tail).hexdigest()
    assert len(tail) == 2040 and tail_digest == FULL_TAIL_SHA256, \
        'merged tail does not match its pin; rebuild patches/full'
    growths = []
    for module, name, pin in FULL_GROWTH_PINS:
        blob = (full_out / name).read_bytes()
        digest = hashlib.sha256(blob).hexdigest()
        assert digest == pin, f'{name} does not match its pin; rebuild'
        growths.append({'module': module, 'length': len(blob),
                        'sha256': digest, 'hex': blob.hex()})
    stock_cfg = json.loads((full_out / 'theme-full-stock.json').read_text())
    full_runs = [{'offset': int(r['offset'], 0)
                  if isinstance(r['offset'], str) else r['offset'],
                  'expect': r['expect'], 'replace': r['replace']}
                 for r in stock_cfg['runs']]
    assert len(full_runs) == 2220, len(full_runs)
    (a.out_dir / 'builder-full.mjs').write_text(
        '// Generated by docs/generate_builder_data.py from '
        'patches/full/\n'
        '// (the everything build: extra patches beyond the '
        'framework set and\n'
        '// the Opus renames, the merged gap tail, the growth '
        'payloads\n'
        '// and the merged theme runs at stock offsets; every '
        'payload SHA-256\n'
        '// pinned). Do not edit by hand.\n'
        'export const FULL_EXTRA_PATCHES = ' + js(full_extra) + ';\n'
        'export const FULL_TAIL = ' + js({'length': len(tail),
                                          'sha256': tail_digest,
                                          'hex': tail.hex()}) + ';\n'
        'export const FULL_GROWTHS = ' + js(growths) + ';\n'
        'export const FULL_THEME_RUNS = ' + js(full_runs) + ';\n'
        'export const FULL_IMAGE_SHA256 = ' + js(FULL_IMAGE_SHA256) + ';\n')
    print('builder-full.mjs:', len(full_extra), 'extra patches,',
          len(tail), 'tail bytes,',
          sum(g['length'] for g in growths), 'growth bytes,',
          len(full_runs), 'theme runs')

    # ---- preset schemes
    presets = []
    entries = rock26_entries(stock)
    for path, name in ((a.scheme_v1_standard, 'CE Standard'),
                       (a.scheme_v1_tidepool, 'CE Tidepool')):
        if path is None:
            continue
        scheme = json.loads(path.read_text())
        assert scheme['name'] == name
        presets.append({'id': name.lower().replace(' ', '-'),
                        'name': name,
                        'config': convert_v1_scheme(stock, entries,
                                                    scheme, name)})
    for path, name in ((a.scheme_v2_standard, 'CE Standard v2'),
                       (a.scheme_v2_dust, 'CE Dust')):
        if path is None:
            continue
        config = json.loads(path.read_text())
        assert config.get('version') == 1
        check_rule_counts(stock, entries, config, name)
        presets.append({'id': name.lower().replace(' ', '-'),
                        'name': name, 'config': config})
    if presets:
        (a.out_dir / 'builder-presets.mjs').write_text(
            '// Generated by docs/generate_builder_data.py from the '
            'design refresh\n'
            '// scheme files (v1 schemes converted to the studio '
            'format; see the\n'
            '// generator). Do not edit by hand.\n'
            'export const PRESETS = ' + js(presets) + ';\n')
        print('builder-presets.mjs:', [p['name'] for p in presets])


if __name__ == '__main__':
    main()
