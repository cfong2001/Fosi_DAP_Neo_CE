#!/usr/bin/env python3
"""DAP Neo patch-framework build: stock DP3_V137.img + patches/ -> custom image.

Offline only. The input image is never modified; the output is written
with exclusive-create and must not already exist.

Why this exists alongside repo/tools/firmware_patch.py: that patcher
asserts the *stock* SHA-256 on every call and requires exactly one patch
target per call, so by design it can only ever apply a single patch to a
pristine image — it cannot chain patches, and it cannot produce a
date-only (zero-patch / recovery) image. This script implements the
multi-patch build loop while reusing the patcher's own pieces:
STOCK_SHA256, validate() and bcd_date() from firmware_patch, and Image /
rk_crc32 from rknano_image. The per-patch apply step replicates
firmware_patch.patch()'s offset resolution, module-boundary check and
expected-bytes precondition verbatim in behaviour; finalization
replicates its date stamp, header-mirror sync and trailer CRC.

Build discipline (proven boot rules, analysis/boot_slots.md):
  * input SHA-256 must equal the pinned stock SHA, or the build refuses;
  * output header date defaults to stock + 1 day (2026-10-23) — the boot
    validator boots the slot whose BCD header date is strictly newer;
  * --recovery emits unmodified stock bytes dated one day AFTER the
    build date, so a recovery flash out-dates (and therefore replaces)
    the custom build, which plain stock (older date) would not.

The default build is the UNIFIED build: the byte patches in
patches/manifest.txt PLUS the whole-module transplants listed in
patches/transplants.txt (currently `vorbis75`, the full-precision
Vorbis module — patches/vorbis_swap/transplant.py), applied after the
byte patches and before finalization. The build refuses if a
transplant's claimed ranges overlap any byte patch's range, so the
combined image is provably the disjoint union of its parts. Use
--no-transplants for a framework-only comparison build. A second
transplant, `opus72` (patches/opus_swap/transplant.py), is
registered but opt-in: it is not in the default transplants.txt
and ships with its own manifest and transplant list under
patches/opus_swap/.

A build may also take --theme-config THEME.json: a theme exported
by the theme studio (patches/theme_editor/). After the byte patches
and the transplants, the theme step recolours ROCK26 image
resources by exact colour, checking the studio's per-resource
pixel counts against the image being built, and applies any raw
"runs" edits the config carries (the CE splash mark,
patches/theme_editor/ce-mark.json, ships that way). Theme edits
refuse on any overlap with an earlier modification, on a count
mismatch, and on a runs entry whose expected bytes do not match,
so a theme exported against a different image cannot ship.

Paths are portable: the repo tools, the stock image and the transplant
inputs resolve through tools/fosi_paths.py (CLI flag > environment >
discovery); nothing here knows the development workspace layout.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import struct
import sys
from pathlib import Path


def _tools_dir():
    here = Path(__file__).resolve()
    roots = [Path(os.environ['FOSI_REPO_ROOT'])] if os.environ.get('FOSI_REPO_ROOT') else []
    roots += [here.parent, *here.parents]
    for r in roots:
        for cand in (r / 'tools', r / 'repo' / 'tools'):
            if (cand / 'firmware_patch.py').exists():
                return cand
    raise SystemExit('cannot locate repo tools/ (set FOSI_REPO_ROOT)')


HERE = Path(__file__).resolve().parent
TOOLS = _tools_dir()
sys.path.insert(0, str(TOOLS))

import fosi_paths                          # noqa: E402
import firmware_patch as fp                # noqa: E402  (validate, bcd_date, STOCK_SHA256)
from rknano_image import Image, rk_crc32   # noqa: E402

sys.path.insert(0, str(HERE / 'tools'))
import insert_rebuild                      # noqa: E402  (segment insertion rebuild)
from validate_grown import validate_grown  # noqa: E402  (layout-generalized validator)

REPO = TOOLS.parent

STOCK_DATE = '20261022'                    # BCD header date inside DP3_V137.img
DEFAULT_BUILD_DATE = '20261023'            # stock + 1 day
HEADER_LEN = 0x200
MIRROR_OFF = 0xC94000


def add_days(yyyymmdd, days):
    d = datetime.date(int(yyyymmdd[:4]), int(yyyymmdd[4:6]), int(yyyymmdd[6:8]))
    return (d + datetime.timedelta(days=days)).strftime('%Y%m%d')


# ---------------------------------------------------------------- patches

def parse_patch(path):
    """Parse one .patch file: `key: value` header lines (# = comment,
    indented lines continue the previous value)."""
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
    kind = fields.get('kind')
    if not fields.get('name') or not fields.get('rationale') or not fields.get('gate'):
        raise ValueError(f'{path}: patch must carry name, rationale and gate')
    if kind == 'module':
        for req in ('module', 'region', 'address', 'expect', 'replace'):
            if req not in fields:
                raise ValueError(f'{path}: module patch missing {req}')
        fields['module'] = int(fields['module'])
        fields['address'] = int(fields['address'], 0)
        fields['expect'] = bytes.fromhex(fields['expect'])
        fields['replace'] = bytes.fromhex(fields['replace'])
        if fields['region'] not in ('code', 'data'):
            raise ValueError(f'{path}: region must be code or data')
        if len(fields['expect']) < 1 or len(fields['expect']) != len(fields['replace']):
            raise ValueError(f'{path}: expect/replace must be equal, non-zero length')
    elif kind == 'string':
        for req in ('language', 'string_id', 'expect_text', 'replace_text'):
            if req not in fields:
                raise ValueError(f'{path}: string patch missing {req}')
        fields['language'] = int(fields['language'])
        fields['string_id'] = int(fields['string_id'])
    else:
        raise ValueError(f'{path}: unknown kind {kind!r} (module|string)')
    fields['file'] = Path(path).name
    return fields


def load_manifest(manifest_path):
    manifest_path = Path(manifest_path)
    names = []
    for line in manifest_path.read_text().splitlines():
        line = line.split('#', 1)[0].strip()
        if line:
            names.append(line)
    return [parse_patch(manifest_path.parent / n) for n in names]


# ------------------------------------------------------------- DAC filter

# The four non-default CS43198 PCM filters (patches/dac_filter/). Each
# file rewrites the same byte, so a build takes at most one.
DAC_FILTER_DIR = REPO / 'patches' / 'dac_filter'
DAC_FILTERS = {
    'fast-linear-phase': '0034-dac-filter-fast-linear-phase.patch',
    'slow-low-latency': '0035-dac-filter-slow-low-latency.patch',
    'slow-linear-phase': '0036-dac-filter-slow-linear-phase.patch',
    'nos': '0037-dac-filter-nos.patch',
}


def dac_filter_patch(name):
    return parse_patch(DAC_FILTER_DIR / DAC_FILTERS[name])


# Bluetooth auto-off (patches/bt_auto_off/). Stock turns Bluetooth off
# after 5 minutes without a connection; each option is one patch in the
# supervisor's limit check, so a build takes at most one.
BT_AUTO_OFF_DIR = REPO / 'patches' / 'bt_auto_off'
BT_AUTO_OFF = {
    '10min': '0038-bt-auto-off-10min.patch',
    'never': '0039-bt-auto-off-never.patch',
}


def bt_auto_off_patch(name):
    return parse_patch(BT_AUTO_OFF_DIR / BT_AUTO_OFF[name])


# ------------------------------------------------------------- transplants

TRANSPLANT_MODULES = {'vorbis75': ('vorbis_swap', 'transplant.py'),
                      'opus72': ('opus_swap', 'transplant.py')}


def load_transplant_names(path):
    path = Path(path)
    if not path.exists():
        return []
    names = []
    for line in path.read_text().splitlines():
        line = line.split('#', 1)[0].strip()
        if line:
            names.append(line)
    return names


def load_transplant(name):
    """Import a transplant implementation by file location (the
    patches/ tree is not a package). Returns its apply_transplant()."""
    if name not in TRANSPLANT_MODULES:
        raise ValueError(f'unknown transplant {name!r} '
                         f'(known: {sorted(TRANSPLANT_MODULES)})')
    sub, fname = TRANSPLANT_MODULES[name]
    path = HERE.parent / sub / fname
    spec = importlib.util.spec_from_file_location(f'transplant_{name}', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.apply_transplant


def _ranges_overlap(a, b):
    return a[0] <= b[1] and b[0] <= a[1]


def apply_transplants(raw, names, ecpatch_dir, patch_ranges):
    """Apply whole-module transplants in order. Each transplant claims
    file ranges; the build refuses if any claimed range overlaps a
    byte patch's range or an earlier transplant's — combined effects
    must stay attributable to exactly one modification."""
    records = []
    claimed = list(patch_ranges)
    for name in names:
        apply_fn = load_transplant(name)
        raw, rec = apply_fn(raw, ecpatch_dir)
        for rng in rec['ranges']:
            for other in claimed:
                if _ranges_overlap(rng, other):
                    raise ValueError(
                        f"transplant {rec['transplant']}: range "
                        f"{hex(rng[0])}..{hex(rng[1])} overlaps an earlier "
                        f"modification at {hex(other[0])}..{hex(other[1])}")
            claimed.append(rng)
        records.append(rec)
    return raw, records


# ------------------------------------------------------------ theme step
#
# The theme studio (docs/, patches/theme_editor/) exports a theme
# JSON: a five-role palette of #RRGGBB colours plus per-resource
# exact-colour replacement rules whose expected pixel counts the
# studio verified against the stock image. This step is the build
# consumer for that export. It applies the rules to the ROCK26
# image resources of the image being built, under the framework's
# usual discipline: counts checked exactly, no overlap with any
# earlier modification, size-preserving, a single finalize at the
# end (in build_image).
#
# Word convention: the studio reads and writes resource words
# little-endian (docs/theme-core.mjs reads getUint16 with the
# littleEndian flag set), and its expected counts reproduce on the
# stock image only under that reading (counted both ways during
# this step's development: resource 6 holds 6,060 little-endian
# words of 0xA210 and none big-endian; the byte-swapped word
# 0x10A2 is what a big-endian count finds). This step therefore
# matches the studio exactly, byte for byte. The theme census
# proved from decoded renders that the panel path displays the
# same stored bytes as big-endian RGB565 (natural colours
# big-endian, inverted colours little-endian), and the emulated
# player painter copies resource bytes to the framebuffer in that
# order (tools/gen_sim_data.py). So the two layers differ: a rule's
# source keeps the studio's little-endian naming, so its verified
# counts hold, but the replacement is written big-endian, so the
# panel shows the palette colour the user picked. (Before this,
# replacements were written little-endian and would have shown
# byte-swapped.) Nothing here has been flashed.
#
# Extension beyond the studio format: a top-level "runs" list of
# {offset, expect, replace} hex-string edits, for changes that are
# not exact-colour replacements (the CE splash mark,
# patches/theme_editor/ce-mark.json). A run carries the same
# overlap refusal plus an expected-bytes precondition checked
# against the image state left by the earlier steps.
#
# literal_sites in a config are refused, not ignored: the
# APPROVED_LITERAL_SITES registry in tools/ui_theme.py is empty
# at this revision, so no literal site is approved for patching.
# Approving the census palette sites is a separate decision.

THEME_ROLES = ('background', 'text', 'highlight', 'icons', 'progress_bar')

# Colours the UI sets in code, not in resources. Each role is a
# `movw r0, #imm16` (T3) in module 0 that appears twice: once in the
# palette routine, which fills the colour cells when a scheme is
# chosen, and once in the clock/status painter, which writes the same
# cells again on every repaint. A role is patched at both sites or
# not at all, otherwise the painter restores the stock value on the
# next redraw. Addresses and stock immediates come from the census
# (patches/design_refresh_v2/schemes/palette_registry_proposal.json);
# the build decodes each site from the image and refuses unless it
# is exactly that instruction. Background and text are not here: the
# routines load them from one shared register pair and swap it per
# scheme, so they are not independent sites.
CODE_COLOUR_SITES = {
    'accent_light': (0xFB20, (0x030655DA, 0x03065F4A)),
    'line_light':   (0xEF7D, (0x030655E2, 0x03065F52)),
    'accent_dark':  (0xF220, (0x030655F0, 0x03065F90)),
    'line_dark':    (0x1082, (0x030655F8, 0x03065F98)),
}


def _movw_r0(word):
    """Thumb-2 MOVW r0, #word (encoding T3), as stored bytes."""
    hw1 = 0xF240 | ((word >> 1) & 0x400) | (word >> 12)
    hw2 = ((word >> 8) & 7) << 12 | (word & 0xFF)
    return struct.pack('<HH', hw1, hw2)


def _movw_r0_imm(four):
    """Inverse of _movw_r0, or None if the bytes are not MOVW r0."""
    hw1, hw2 = struct.unpack('<HH', four)
    if hw1 & 0xFBF0 != 0xF240 or hw2 & 0x8F00 != 0:
        return None
    return ((hw1 & 0xF) << 12 | ((hw1 >> 10) & 1) << 11
            | ((hw2 >> 12) & 7) << 8 | (hw2 & 0xFF))
THEME_GUARD_WORDS = (0x0000, 0x00F8)
ROCK26_SIGNATURE = b'ROCK26IMAGERES  '


def _theme_rgb565(value):
    """docs/theme-core.mjs rgb565(): a #RRGGBB string to an RGB565
    word, with the studio's rounding ((c * max + 127) // 255)."""
    if not isinstance(value, str) or len(value) != 7 or value[0] != '#' \
            or any(c not in '0123456789abcdefABCDEF' for c in value[1:]):
        raise ValueError(f'theme: invalid colour {value!r}; use #RRGGBB')
    r, g, b = (int(value[i:i + 2], 16) for i in (1, 3, 5))
    return (((r * 31 + 127) // 255) << 11
            | ((g * 63 + 127) // 255) << 5
            | ((b * 31 + 127) // 255))


def _theme_word(value):
    """docs/theme-core.mjs asWord(): an integer or a 0x-prefixed
    hex string, 0..0xFFFF."""
    word = None
    if isinstance(value, int) and not isinstance(value, bool):
        word = value
    elif isinstance(value, str) and value.lower().startswith('0x') \
            and 1 <= len(value) - 2 <= 4:
        try:
            word = int(value, 16)
        except ValueError:
            word = None
    if word is None or not 0 <= word <= 0xFFFF:
        raise ValueError(f'theme: invalid RGB565 word {value!r}')
    return word


def parse_theme_config(config):
    """Validate a theme JSON document the way the studio's
    validateTheme() (docs/theme-core.mjs) does, plus the runs
    extension. Returns {'palette_words', 'resources', 'runs'}.
    Absent palette / resources / literal_sites keys are treated as
    empty (the runs-only CE mark config relies on this); a palette
    that is present must define exactly the five studio roles."""
    if not isinstance(config, dict) or config.get('version') != 1:
        raise ValueError('theme: config must be a version 1 theme document')
    literal_sites = config.get('literal_sites', [])
    if not isinstance(literal_sites, list):
        raise ValueError('theme: literal_sites must be an array')
    if literal_sites:
        raise ValueError(
            'theme: literal_sites are not accepted by the build: the '
            'APPROVED_LITERAL_SITES registry in tools/ui_theme.py is '
            'empty at this revision, so no literal site is approved '
            'for patching')
    palette = config.get('palette')
    palette_words = {}
    if palette is not None:
        if not isinstance(palette, dict) \
                or set(palette) != set(THEME_ROLES) \
                or any(not isinstance(palette[r], str) for r in THEME_ROLES):
            raise ValueError(
                'theme: palette must define exactly the five roles '
                + ', '.join(THEME_ROLES))
        palette_words = {r: _theme_rgb565(palette[r]) for r in THEME_ROLES}
    resources = config.get('resources', [])
    if not isinstance(resources, list):
        raise ValueError('theme: resources must be an array')
    rules = []
    seen = set()
    for rule in resources:
        if not isinstance(rule, dict):
            raise ValueError('theme: resource rule must be an object')
        rid, role = rule.get('id'), rule.get('role')
        if not isinstance(rid, int) or isinstance(rid, bool) or rid < 0:
            raise ValueError(f'theme: resource id {rid!r} is not a valid id')
        if role not in THEME_ROLES:
            raise ValueError(f'theme: unknown colour role {role!r}')
        if role not in palette_words:
            raise ValueError(
                f'theme: resource rule for asset {rid} names role '
                f'{role!r} but the config carries no palette')
        source = _theme_word(rule.get('source'))
        if source in THEME_GUARD_WORDS:
            raise ValueError(
                f'theme: resource rule for asset {rid} uses reserved '
                f'colour {hex(source)}; the guard words 0x0000 and '
                f'0x00F8 are blocked as replacement sources')
        count = rule.get('expected_count')
        if not isinstance(count, int) or isinstance(count, bool) \
                or count <= 0:
            raise ValueError(
                f'theme: resource rule for asset {rid} must specify '
                f'an exact expected_count')
        if (rid, source) in seen:
            raise ValueError(
                f'theme: duplicate resource rule for asset {rid} '
                f'source {hex(source)}')
        seen.add((rid, source))
        rules.append({'id': rid, 'role': role, 'source': source,
                      'expected_count': count})
    raw_runs = config.get('runs', [])
    if not isinstance(raw_runs, list):
        raise ValueError('theme: runs must be an array')
    runs = []
    for run in raw_runs:
        if not isinstance(run, dict):
            raise ValueError('theme: run must be an object')
        off = run.get('offset')
        if isinstance(off, str) and off.lower().startswith('0x'):
            try:
                off = int(off, 16)
            except ValueError:
                off = None
        if not isinstance(off, int) or isinstance(off, bool) or off < 0:
            raise ValueError(
                f"theme: run offset {run.get('offset')!r} is not a "
                f'valid file offset')
        try:
            expect = bytes.fromhex(run.get('expect'))
            replace = bytes.fromhex(run.get('replace'))
        except (TypeError, ValueError):
            raise ValueError(
                'theme: run expect/replace must be hex strings')
        if not expect or len(expect) != len(replace):
            raise ValueError(
                'theme: run expect/replace must be equal, non-zero length')
        runs.append({'offset': off, 'expect': expect, 'replace': replace})
    code_colours = config.get('code_colours', {})
    if code_colours is None:
        code_colours = {}
    if not isinstance(code_colours, dict):
        raise ValueError('theme: code_colours must be an object')
    code_words = {}
    for role, value in code_colours.items():
        if role not in CODE_COLOUR_SITES:
            raise ValueError(
                f'theme: unknown code colour {role!r}; use '
                + ', '.join(CODE_COLOUR_SITES))
        code_words[role] = _theme_rgb565(value)
    return {'palette_words': palette_words, 'resources': rules, 'runs': runs,
            'code_words': code_words}


def _rock26_resources(raw):
    """Parse the ROCK26 image resource table from the image being
    built: the layout the studio's parseFirmware reads (section
    pointer at header offset 0x14C, signature, count, then 16-byte
    records from section + 0x20). Nothing is hard-coded to the
    stock layout beyond the header fields the format itself pins.
    Returns [{'id', 'width', 'height', 'size', 'data_offset'}]."""
    if len(raw) < 0x154:
        raise ValueError('theme: image too small to carry a resource '
                         'section')
    start, length = struct.unpack_from('<II', raw, 0x14C)
    if length < 0x20 or start + length > len(raw) \
            or raw[start:start + 16] != ROCK26_SIGNATURE:
        raise ValueError('theme: ROCK26 image resource section not found')
    count = struct.unpack_from('<I', raw, start + 16)[0]
    if 0x20 + count * 16 > length:
        raise ValueError('theme: ROCK26 resource table overruns its '
                         'section')
    entries = []
    for i in range(count):
        w, h, _x, _y, size, off = struct.unpack_from(
            '<4H2I', raw, start + 0x20 + i * 16)
        if size != w * h * 2 or off + size > length:
            raise ValueError(
                f'theme: resource {i} is not a raw RGB565 bitmap '
                f'inside the section')
        entries.append({'id': i, 'width': w, 'height': h, 'size': size,
                        'data_offset': start + off})
    return entries


def apply_theme(raw, config, claimed_ranges):
    """Apply a theme config to the image being built.
    claimed_ranges are the inclusive file ranges already modified
    by byte patches and transplants; theme edits must not overlap
    any of them, nor each other. Returns (bytes, record,
    claimed_ranges extended with the theme's own ranges). Raises
    ValueError on any refusal: a theme that does not match the
    image must not ship. NOTE: the stock-SHA gate lives in
    build_image(), not here, so tests can exercise these
    preconditions directly."""
    cfg = parse_theme_config(config)
    entries = _rock26_resources(raw)
    raw = bytearray(raw)
    claimed = list(claimed_ranges)
    taken = set()
    for s, e in claimed:
        taken.update(range(s, e + 1))

    def claim(rng, what):
        for b in range(rng[0], rng[1] + 1):
            if b in taken:
                raise ValueError(
                    f'theme: {what} range {hex(rng[0])}..{hex(rng[1])} '
                    f'overlaps an earlier modification at {hex(b)}')
            taken.add(b)
        claimed.append(rng)

    rec_rules = []
    for rule in cfg['resources']:
        if rule['id'] >= len(entries):
            raise ValueError(
                f"theme: resource id {rule['id']} outside the image's "
                f'{len(entries)} resources')
        ent = entries[rule['id']]
        base, size = ent['data_offset'], ent['size']
        src = struct.pack('<H', rule['source'])
        tgt = struct.pack('>H', cfg['palette_words'][rule['role']])  # panel order
        hits = [base + 2 * i for i in range(size // 2)
                if raw[base + 2 * i:base + 2 * i + 2] == src]
        if len(hits) != rule['expected_count']:
            raise ValueError(
                f"theme: resource {rule['id']}: expected "
                f"{rule['expected_count']} pixels of "
                f"{hex(rule['source'])}, found {len(hits)}; refusing "
                f'(the theme was exported against a different image)')
        start = prev = None
        for off in hits:
            if start is None:
                start = prev = off
            elif off == prev + 2:
                prev = off
            else:
                claim([start, prev + 1], f"resource {rule['id']} recolour")
                start = prev = off
        if start is not None:
            claim([start, prev + 1], f"resource {rule['id']} recolour")
        for off in hits:
            raw[off:off + 2] = tgt
        rec_rules.append({'asset': rule['id'], 'role': rule['role'],
                          'source': hex(rule['source']),
                          'target': hex(cfg['palette_words'][rule['role']]),
                          'count': len(hits),
                          'file_offset': hex(base)})
    rec_code = []
    if cfg['code_words']:
        img = Image(bytes(raw))
        code_off, code_len = img.module_region(0, 'code')
        code_exec = img.modules[0]['code_exec']
    for role in CODE_COLOUR_SITES:
        if role not in cfg['code_words']:
            continue
        stock, sites = CODE_COLOUR_SITES[role]
        word = cfg['code_words'][role]
        for addr in sites:
            rel = addr - code_exec
            if not 0 <= rel <= code_len - 4:
                raise ValueError(
                    f'theme: code colour site {hex(addr)} is outside '
                    f'module 0 code')
            off = code_off + rel
            imm = _movw_r0_imm(bytes(raw[off:off + 4]))
            if imm != stock:
                raise ValueError(
                    f'theme: code colour {role} at {hex(addr)}: expected '
                    f'movw r0, #{hex(stock)}, found '
                    f'{bytes(raw[off:off + 4]).hex()}; refusing')
            claim([off, off + 3], f'code colour {role}')
            raw[off:off + 4] = _movw_r0(word)
        rec_code.append({'role': role, 'stock': hex(stock),
                         'target': hex(word),
                         'sites': [hex(a) for a in sites]})
    rec_runs = []
    for run in cfg['runs']:
        off, expect, replace = run['offset'], run['expect'], run['replace']
        if off + len(expect) > len(raw):
            raise ValueError(f'theme: run at {hex(off)} overruns the image')
        claim([off, off + len(expect) - 1], 'run')
        if bytes(raw[off:off + len(expect)]) != expect:
            raise ValueError(
                f'theme: run at {hex(off)}: expected bytes mismatch: '
                f'expected {expect.hex()}, found '
                f'{bytes(raw[off:off + len(expect)]).hex()}')
        raw[off:off + len(expect)] = replace
        rec_runs.append({'file_offset': hex(off), 'bytes': len(expect),
                         'old_hex': expect.hex(), 'new_hex': replace.hex()})
    record = {'resources': rec_rules, 'runs': rec_runs,
              'code_colours': rec_code,
              'pixels_changed': sum(r['count'] for r in rec_rules),
              'bytes_changed': 2 * sum(r['count'] for r in rec_rules)
              + sum(r['bytes'] for r in rec_runs) + 8 * len(rec_code)}
    return bytes(raw), record, claimed


# ------------------------------------------------------- gap tail step
#
# The package has exactly one large gap: 16,384 zero bytes between
# module 0's code region and its data region. An earlier build step
# (--extension) let a caller place a code blob at the gap base, exec
# 0x03079C14. The resident-home census (analysis/resident_home/)
# proved that range is live runtime workspace: the file descriptor
# table, the directory stack, and FAT driver fields live there and
# are written by resident code, so executable code at the gap base
# is unsafe and the raw step was removed. Do not re-add it.
#
# The census-clean part of the gap is its tail: exec
# 0x0307BFB4..0x0307C7B0 (2,044 bytes, up to the lowest overlay
# base), clear of every documented structure extent. This step is
# the replacement: the caller supplies ONLY the tail payload; the
# build constructs the span itself as zeros across the workspace
# zone (matching stock's don't-care state there, since every
# attributed gap field is written before it is read) with the
# payload at the tail, and extends module 0's code_len in its
# header record (the u32 at file 0x210; the header mirror
# duplicates only the first 0x202 bytes, so the record exists
# exactly once) by the full span. Offsets resolve from the image's
# own module 0 record, so the step composes with --grow insertions
# elsewhere in the package. This is a length-changing edit, so it
# cannot be a manifest patch; it is a build step with the same
# discipline as the rest of the framework (SHA-gated input,
# refusals, report).

TAIL_EXEC = 0x0307BFB4          # first census-clean byte of the gap tail
TAIL_MAX = 0x7FC                # 2,044 bytes (to overlay base 0x0307C7B0)
OVERLAY_BASE = 0x0307C7B0       # lowest overlay exec base
EXT_RECORD_OFF = 0x210          # module 0 code_len u32 in the header
MOD0_CODE_LEN_STOCK = 0x29C14


def apply_tail(raw, payload, claimed_ranges):
    """Deliver payload into the gap tail and extend module 0
    code_len over the whole gap span. `claimed_ranges` are the
    inclusive file ranges already modified by byte patches /
    transplants; the tail's own ranges (span + the record field)
    must not overlap any of them. Returns (bytes, record_dict).
    Raises ValueError on any refusal: a payload that does not fit
    the census-proven tail must not ship.
    """
    if len(payload) < 1:
        raise ValueError('tail: empty payload')
    if len(payload) > TAIL_MAX:
        raise ValueError(
            f'tail: payload is {len(payload)} bytes; the census-clean '
            f'tail is capped at {TAIL_MAX} (exec {hex(TAIL_EXEC)}..'
            f'{hex(OVERLAY_BASE)}, the lowest overlay base)')
    img = Image(raw)
    code_off, code_len = img.module_region(0, 'code')
    code_exec = img.modules[0]['code_exec']
    if code_len != MOD0_CODE_LEN_STOCK:
        raise ValueError(
            f'tail: module 0 code_len is {hex(code_len)}, expected '
            f'stock {hex(MOD0_CODE_LEN_STOCK)}; refusing to extend a '
            f'non-stock record')
    gap_off = code_off + code_len
    gap_exec = code_exec + code_len
    span = OVERLAY_BASE - gap_exec
    tail_off = TAIL_EXEC - gap_exec
    if span < 1 or tail_off < 0 or tail_off + TAIL_MAX != span:
        raise ValueError(
            f'tail: gap geometry from the image records (gap exec '
            f'{hex(gap_exec)}, span {span}) does not match the '
            f'census-proven tail; refusing')
    span_range = [gap_off, gap_off + span - 1]
    rec_range = [EXT_RECORD_OFF, EXT_RECORD_OFF + 3]
    for rng in claimed_ranges:
        for mine, what in ((span_range, 'gap span range'),
                           (rec_range, 'code_len record range')):
            if _ranges_overlap(mine, rng):
                raise ValueError(
                    f'tail: {what} {hex(mine[0])}..{hex(mine[1])} '
                    f'overlaps an earlier modification at '
                    f'{hex(rng[0])}..{hex(rng[1])}')
    if any(raw[gap_off:gap_off + span]):
        raise ValueError(
            'tail: the package gap is not zero across the span; '
            'refusing (wrong image or an overlapping modification '
            'the range check did not model)')
    blob = bytearray(span)
    blob[tail_off:tail_off + len(payload)] = payload
    raw = bytearray(raw)
    raw[gap_off:gap_off + span] = blob
    new_len = MOD0_CODE_LEN_STOCK + span
    struct.pack_into('<I', raw, EXT_RECORD_OFF, new_len)
    record = {'exec': hex(TAIL_EXEC), 'file_offset': hex(gap_off + tail_off),
              'payload_bytes': len(payload),
              'payload_sha256': hashlib.sha256(payload).hexdigest(),
              'span_bytes': span,
              'workspace_zone_zero_bytes': tail_off,
              'code_len_old': hex(MOD0_CODE_LEN_STOCK),
              'code_len_new': hex(new_len),
              'code_len_record_file_offset': hex(EXT_RECORD_OFF)}
    return bytes(raw), record


def apply_patches(raw, patches):
    """Apply parsed patches in order to a copy of raw; return (bytes, edits).

    Each patch's expected bytes are checked against the image state left
    by the previous patches. Raises ValueError on any precondition
    failure — a patch that does not match is a build that must not ship.
    NOTE: the stock-SHA gate lives in build_image(), not here, so tests
    can exercise these preconditions directly.
    """
    raw = bytearray(raw)
    im = Image(bytes(raw))
    edits = []
    for p in patches:
        if p['kind'] == 'module':
            m = im.modules[p['module']]
            region = p['region']
            rel = p['address'] - m[region + '_exec']
            if rel < 0 or rel + len(p['replace']) > m[region + '_len']:
                raise ValueError(f"patch {p['name']}: crosses module boundary")
            base, _ = im.module_region(p['module'], region)
            off = base + rel
            if raw[off:off + len(p['expect'])] != p['expect']:
                raise ValueError(
                    f"patch {p['name']}: stock byte precondition mismatch at "
                    f"module {p['module']} {region} {hex(p['address'])} "
                    f"(file {hex(off)}): expected {p['expect'].hex()}, found "
                    f"{bytes(raw[off:off + len(p['expect'])]).hex()}")
            raw[off:off + len(p['replace'])] = p['replace']
            edits.append({'patch': p['name'], 'file': p['file'], 'kind': 'module',
                          'module': p['module'], 'region': region,
                          'cpu_address': hex(p['address']), 'file_offset': hex(off),
                          'old_hex': p['expect'].hex(), 'new_hex': p['replace'].hex()})
        else:  # string patch — same resource layout as firmware_patch.patch()
            s = im.sections['lang']
            start = s['offset']
            n = struct.unpack_from('<H', raw, start)[0]
            if not 0 <= p['language'] < n or not 0 <= p['string_id'] < 266:
                raise ValueError(f"patch {p['name']}: language/string ID out of bounds")
            lang_offset = im.u32(start + 2 + p['language'] * 4)
            rec = start + lang_offset + p['string_id'] * 258
            if struct.unpack_from('<H', raw, rec)[0] != p['string_id']:
                raise ValueError(f"patch {p['name']}: string resource record ID mismatch")
            off = rec + 58
            original = bytes(raw[off:off + 200]).decode('utf-16le').split('\0', 1)[0]
            if original != p['expect_text']:
                raise ValueError(
                    f"patch {p['name']}: stock UI text precondition mismatch: "
                    f"expected {p['expect_text']!r}, found {original!r}")
            value = p['replace_text'].encode('utf-16le') + b'\0\0'
            if len(value) > 200:
                raise ValueError(f"patch {p['name']}: replacement string too long")
            raw[off:off + 200] = value.ljust(200, b'\0')
            edits.append({'patch': p['name'], 'file': p['file'], 'kind': 'string',
                          'language': p['language'], 'string_id': p['string_id'],
                          'file_offset': hex(off),
                          'old_text': original, 'new_text': p['replace_text']})
    return bytes(raw), edits


def finalize(raw, date, grown=False):
    """Stamp the BCD header date, sync the header mirror, rewrite the
    trailer CRC, and validate the package. Grown builds (segment
    insertions applied) use the layout-generalized validator: the
    stock validator pins the stock image length and duplicate-header
    offset, which a correctly grown image violates by construction."""
    raw = bytearray(raw)
    raw[:4] = fp.bcd_date(date)
    # The duplicate header lives at the offset stored at 0x1F4 (the
    # stock layout's 0xC94000; a grown image's insertions shift it).
    mirror_off = struct.unpack_from('<I', raw, 0x1F4)[0]
    raw[mirror_off:mirror_off + HEADER_LEN] = raw[:HEADER_LEN]
    struct.pack_into('<I', raw, len(raw) - 4, rk_crc32(bytes(raw[:-4])))
    out = bytes(raw)
    if grown:
        validate_grown(out)
    else:
        fp.validate(out)
    return out


def diff_summary(stock, out):
    """Coalesced [start, end] inclusive ranges where out differs from stock.
    Length-aware: a grown build is longer than stock; the appended tail
    counts as one final changed range. Ungrown builds are byte-identical
    in behaviour to the original prefix-only comparison."""
    ranges = []
    start = None
    n = min(len(stock), len(out))
    for i in range(n):
        if stock[i] != out[i]:
            if start is None:
                start = i
        elif start is not None:
            ranges.append([start, i - 1])
            start = None
    if start is not None:
        ranges.append([start, n - 1])
    if len(out) > len(stock):
        ranges.append([len(stock), len(out) - 1])
    elif len(out) < len(stock):
        ranges.append([len(out), len(stock) - 1])
    return {'bytes_changed': sum(e - s + 1 for s, e in ranges),
            'ranges': [[hex(s), hex(e)] for s, e in ranges],
            '_ranges_int': ranges}


def _edit_range(edit):
    off = int(edit['file_offset'], 16)
    if edit['kind'] == 'module':
        return [off, off + len(bytes.fromhex(edit['new_hex'])) - 1]
    return [off, off + 199]                # string patch rewrites 200 bytes


def build_image(input_bytes, patches, date, transplants=(), ecpatch_dir=None,
                tail_payload=None, growths=(), theme_config=None):
    """SHA-gated full build. Returns (output_bytes, report_dict).

    growths: (module, segment, payload_bytes) insertions applied to the
    pristine stock image first (insert_rebuild.apply_insertions), so
    byte patches and transplants resolve their offsets through the
    grown image's own records and no patch file changes."""
    # The classifier edits and decoder replacement must travel together.
    # Compare their actual targets and bytes, not filenames supplied by a caller.
    opus_dir = REPO / 'patches' / 'opus_swap'
    signatures = lambda p: (p.get('kind'), p.get('module'), p.get('region'),
                            p.get('address'), p.get('expect'), p.get('replace'))
    required = {signatures(parse_patch(p)) for p in opus_dir.glob('opus-rename-*.patch')}
    if len(required) != 5:
        raise ValueError('opus72: expected five distinct classifier rename patches')
    targets = {(p[1], p[2], p[3]) for p in required}
    present = [signatures(p) for p in patches
               if (p.get('module'), p.get('region'), p.get('address')) in targets]
    if ('opus72' in transplants or present) and (
            'opus72' not in transplants or len(present) != len(required)
            or set(present) != required):
        raise ValueError('opus72 and all five classifier renames must be used together')
    # Both title patches share control flow: applying either alone can
    # branch into stock instructions with the wrong register contract.
    title_dir = REPO / 'patches' / 'theater' / 'text'
    title_required = {signatures(parse_patch(title_dir / name))
                      for name in ('title-copy.patch', 'title-suffix.patch')}
    title_targets = {(p[1], p[2], p[3]) for p in title_required}
    title_present = [signatures(p) for p in patches
                     if (p.get('module'), p.get('region'), p.get('address')) in title_targets]
    if title_present and (len(title_present) != 2 or set(title_present) != title_required):
        raise ValueError('player title copy and suffix patches must be used together')
    sha = hashlib.sha256(input_bytes).hexdigest()
    if sha != fp.STOCK_SHA256:
        raise ValueError(
            f'input SHA-256 {sha} does not match pinned stock '
            f'{fp.STOCK_SHA256}; refusing to build')
    fp.validate(input_bytes)
    growth_records = []
    base = input_bytes
    if growths:
        base = insert_rebuild.apply_insertions(input_bytes, list(growths))
        growth_records = [{'module': m, 'segment': s,
                           'payload_bytes': len(p),
                           'payload_sha256': hashlib.sha256(p).hexdigest()}
                          for m, s, p in growths]
    patched, edits = apply_patches(base, patches)
    patch_ranges = [_edit_range(e) for e in edits]
    patched, trecords = apply_transplants(patched, list(transplants),
                                          ecpatch_dir, patch_ranges)
    claimed = list(patch_ranges)
    for t in trecords:
        claimed.extend(t['ranges'])
    theme_record = None
    if theme_config is not None:
        patched, theme_record, claimed = apply_theme(
            patched, theme_config, claimed)
    tail_record = None
    if tail_payload is not None:
        patched, tail_record = apply_tail(patched, tail_payload, claimed)
    out = finalize(patched, date, grown=bool(growths))
    diff = diff_summary(input_bytes, out)
    diff.pop('_ranges_int')
    report = {'input_sha256': sha,
              'output_sha256': hashlib.sha256(out).hexdigest(),
              'byte_length': len(out),
              'header_date': date,
              'patches_applied': edits,
              'transplants_applied': trecords,
              'theme': theme_record,
              'tail': tail_record,
              'growth': growth_records,
              'diff_vs_stock': diff,
              'validation': ('validate_grown() passed (structural checks, '
                             'layout derived from the image)'
                             if growths else
                             'firmware_patch.validate() passed '
                             '(header mirror + trailer CRC + V137 layout)'),
              'scope': 'offline package integrity only; device acceptance '
                       'and boot behaviour are hardware-phase questions'}
    return out, report


# ------------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--input', type=Path, default=None,
                    help='stock image (default: FOSI_STOCK_IMAGE or '
                         'discovery — see tools/fosi_paths.py)')
    ap.add_argument('--output', type=Path, required=True,
                    help='output image; must not exist; never the input path')
    ap.add_argument('--manifest', type=Path, default=HERE / 'patches' / 'manifest.txt',
                    help='patch manifest (ignored with --recovery)')
    ap.add_argument('--transplants', type=Path,
                    default=HERE / 'patches' / 'transplants.txt',
                    help='transplant list (ignored with --recovery)')
    ap.add_argument('--no-transplants', action='store_true',
                    help='framework-only build: byte patches, no transplants')
    ap.add_argument('--ecpatch-dir', type=Path, default=None,
                    help='directory with the HIFIEC*.ecpatch transplant '
                         'inputs (default: FOSI_ECPATCH_DIR or discovery)')
    ap.add_argument('--date', default=None,
                    help='output BCD header date YYYYMMDD '
                         f'(build default {DEFAULT_BUILD_DATE} = stock+1; '
                         'recovery default = build date + 1)')
    ap.add_argument('--tail', type=Path, default=None,
                    help='resident payload (max 2,044 bytes) to deliver '
                         'into the census-clean gap tail at exec '
                         '0x0307BFB4; the build zero-fills the workspace '
                         'zone itself and extends module 0 code_len over '
                         'the whole gap span. Not with --recovery.')
    ap.add_argument('--theme-config', type=Path, default=None,
                    help='theme JSON exported by the theme studio '
                         '(patches/theme_editor/): per-resource colour '
                         'replacements checked against the studio pixel '
                         'counts, plus optional raw "runs" edits (the '
                         'CE splash mark). Applied after the byte '
                         'patches and transplants. Not with --recovery.')
    ap.add_argument('--grow', action='append', default=[],
                    metavar='MODULE:SEGMENT:PATH',
                    help='insert the file at PATH at the end of MODULE\'s '
                         'SEGMENT (code|data), growing its declared length '
                         'and shifting later payloads (repeatable). Applied '
                         'to the pristine stock image before patching. '
                         'Not with --recovery.')
    ap.add_argument('--eq-presets', type=Path, default=None,
                    help='JSON config of AutoEQ or custom curves for the six '
                         'EQ menu presets (patches/eq_presets/). Also makes '
                         'every preset distinct. Not with --recovery.')
    ap.add_argument('--dac-filter', choices=sorted(DAC_FILTERS), default=None,
                    help='play PCM through one of the CS43198\'s other '
                         'four interpolation filters instead of stock\'s '
                         'fast roll-off, low latency default (one byte; '
                         'patches/dac_filter/). Not with --recovery.')
    ap.add_argument('--bt-auto-off', choices=sorted(BT_AUTO_OFF), default=None,
                    help='how long Bluetooth stays on without a connection '
                         'before stock turns it off (stock: 5 minutes); '
                         'patches/bt_auto_off/. Not with --recovery.')
    ap.add_argument('--recovery', action='store_true',
                    help='recovery image: zero patches, stock bytes, dated '
                         'one day after the build date')
    ap.add_argument('--report', type=Path, default=None,
                    help='build report JSON (default: <output>.report.json)')
    a = ap.parse_args()

    build_date = a.date or DEFAULT_BUILD_DATE
    input_path = a.input if a.input else fosi_paths.stock_image_path(REPO)
    theme_config = None
    if a.theme_config is not None:
        if a.recovery:
            ap.error('--theme-config cannot be combined with --recovery')
        try:
            theme_config = json.loads(a.theme_config.read_text())
        except (OSError, ValueError) as e:
            print(f'BUILD REFUSED: theme config {a.theme_config}: {e}',
                  file=sys.stderr)
            return 2
    tail_payload = None
    if a.tail is not None:
        if a.recovery:
            ap.error('--tail cannot be combined with --recovery')
        tail_payload = a.tail.read_bytes()

    growths = []
    if a.grow:
        if a.recovery:
            ap.error('--grow cannot be combined with --recovery')
        for spec in a.grow:
            parts = spec.split(':', 2)
            if len(parts) != 3 or parts[1] not in ('code', 'data'):
                ap.error(f'--grow expects MODULE:SEGMENT:PATH with '
                         f'SEGMENT code|data, got {spec!r}')
            try:
                module = int(parts[0])
            except ValueError:
                ap.error(f'--grow module is not a number: {spec!r}')
            growths.append((module, parts[1], Path(parts[2]).read_bytes()))

    if a.eq_presets and a.recovery:
        ap.error('--eq-presets cannot be combined with --recovery')
    if a.dac_filter and a.recovery:
        ap.error('--dac-filter cannot be combined with --recovery')
    if a.bt_auto_off and a.recovery:
        ap.error('--bt-auto-off cannot be combined with --recovery')

    if a.recovery:
        date = a.date or add_days(build_date, 1)
        patches = []
        transplant_names = []
        ecpatch_dir = None
        mode = 'recovery'
    else:
        date = build_date
        patches = load_manifest(a.manifest)
        eq_report = None
        if a.eq_presets:
            sys.path.insert(0, str(REPO / 'patches' / 'eq_presets'))
            import eqfit
            stock_raw = input_path.read_bytes()
            slots, eq_report = eqfit.load_config(a.eq_presets, stock_raw)
            patches = patches + eqfit.slot_patches(stock_raw, slots)
        if a.dac_filter:
            patches = patches + [dac_filter_patch(a.dac_filter)]
        if a.bt_auto_off:
            patches = patches + [bt_auto_off_patch(a.bt_auto_off)]
        transplant_names = ([] if a.no_transplants
                            else load_transplant_names(a.transplants))
        ecpatch_dir = fosi_paths.ecpatch_dir(REPO, a.ecpatch_dir)
        if transplant_names and ecpatch_dir is None:
            ap.error('transplants requested but the .ecpatch inputs were '
                     'not found; pass --ecpatch-dir or set FOSI_ECPATCH_DIR '
                     '(see patches/vorbis_swap/DEPENDENCY.md)')
        mode = 'custom'

    if a.output.resolve() == input_path.resolve():
        ap.error('refusing to overwrite the stock image')
    if a.output.exists():
        ap.error(f'output already exists: {a.output}')

    try:
        out, report = build_image(input_path.read_bytes(), patches, date,
                                  transplants=transplant_names,
                                  ecpatch_dir=ecpatch_dir,
                                  tail_payload=tail_payload,
                                  growths=growths,
                                  theme_config=theme_config)
    except ValueError as e:
        print(f'BUILD REFUSED: {e}', file=sys.stderr)
        return 2

    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open('xb') as f:
        f.write(out)
    report = {'mode': mode, 'input_file': str(input_path),
              'output_file': str(a.output), **report}
    if not a.recovery and eq_report is not None:
        report['eq_presets'] = {str(k): v for k, v in eq_report.items()}
    if a.dac_filter:
        report['dac_filter'] = a.dac_filter
    if a.bt_auto_off:
        report['bt_auto_off'] = a.bt_auto_off
    report_path = a.report or a.output.with_suffix(a.output.suffix + '.report.json')
    report_path.write_text(json.dumps(report, indent=2) + '\n')

    print(f"{mode} build OK -> {a.output}")
    print(f"  date {report['header_date']}  patches applied: "
          f"{len(report['patches_applied'])}")
    for e in report['patches_applied']:
        print(f"    - {e['patch']} ({e.get('file_offset', 'string')})")
    for t in report['transplants_applied']:
        print(f"    - transplant {t['transplant']} "
              f"({t['surgery_bytes']} surgery bytes)")
    if report.get('theme'):
        t = report['theme']
        print(f"    - theme: {len(t['resources'])} resource recolour(s) "
              f"({t['pixels_changed']} pixels), {len(t['runs'])} run(s), "
              f"{len(t['code_colours'])} code colour(s); "
              f"{t['bytes_changed']} bytes")
    if report.get('tail'):
        e = report['tail']
        print(f"    - tail payload: {e['payload_bytes']} bytes at "
              f"{e['file_offset']} (exec {e['exec']}); module 0 "
              f"code_len {e['code_len_old']} -> {e['code_len_new']}")
    d = report['diff_vs_stock']
    print(f"  bytes changed vs stock: {d['bytes_changed']} "
          f"in {len(d['ranges'])} range(s): "
          + ', '.join(f'{s}..{e}' for s, e in d['ranges']))
    print(f"  report: {report_path}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
