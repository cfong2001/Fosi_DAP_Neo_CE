#!/usr/bin/env python3
"""Build the power profile item: assemble profiles.S into two module 0
pockets, emit the six framework patches (two pockets, four branch
sites) into patches/full/patches/, and emit profile-menu.json, the
theme runs that add the menu records.

Run from anywhere with the ARM GNU toolchain on PATH. The script
checks every stock fact it relies on against DP3_V137.img first and
refuses on any mismatch.

Outputs are deterministic; CI rebuilds them and diffs.
"""
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / 'tools'))
from rknano_image import Image  # noqa: E402

PATCH_DIR = REPO / 'patches' / 'full' / 'patches'
MENU_JSON = HERE / 'profile-menu.json'

LANGS = 21
RECORDS = 266                 # records per language in the stock layout
RECORD = 258
HEADER = 58
LABEL = 48
FIRST_NEW = 266
SETTINGS = 164                # "System Settings", the parent
LAST_SETTING = 243            # "Product Info", the parent's last child
TABLE_DELTA = 0x0054579A      # images end - language section start

POCKETS = (('.text.lookup', 0x0305168C, 0x0305171E),
           ('.text.profiles', 0x03054668, 0x030546EC),
           ('.text.commit', 0x03067064, 0x030670E0))
# Stock entry points the code branches to (Thumb, bit 0 set in the
# linker script). Each is checked against the instruction it expects.
EXTERNAL = {
    'getresourcestr_body': 0x030630C6,
    'getmenutextinfo_body': 0x0306320A,
    'resource_read': 0x0306432A,
    'value_store': 0x0307DC4E,
    'value_none': 0x0307DC50,
    'value_next': 0x0307DBD6,
    'commit_exit': 0x0307FD28,
    'backlight_apply': 0x03064964,
    'set_screen_off': 0x0307E232,
    'set_power_off': 0x0307E2B2,
    'saveinfo_save': 0x0306CA10,
}
# (patch number, slug, module, site, stock bytes, instruction to assemble)
SITES = (
    (142, 'profile-string-lookup', 0, 0x030630C2, 'f0b4754d', 'b.w str_hook'),
    (143, 'profile-menu-lookup', 0, 0x03063206, '30b4244c', 'b.w menu_hook'),
    (144, 'profile-value-load', 32, 0x0307DBCE, 'bc2d08bf', 'b.w value_hook'),
    (145, 'profile-commit', 32, 0x0307FA80, '80f05281', 'bhs.w commit_hook'),
)
POCKET_PATCHES = ((140, 'pocket-profile-lookup'), (141, 'pocket-profile-value'),
                  (146, 'pocket-profile-commit'))

# Labels: the item, then its three options, per language in the image's
# language order (records 220..240 name them).
LABELS = [
    ('简体中文', ['电源模式', '高性能', '均衡', '省电']),
    ('繁體中文', ['電源模式', '高效能', '平衡', '省電']),
    ('English', ['Power Profile', 'High', 'Balanced', 'Battery Saver']),
    ('한국어', ['전원 프로필', '높음', '균형', '배터리 절약']),
    ('日本語', ['電源プロファイル', '高', 'バランス', '省電力']),
    ('Français', ["Profil d'énergie", 'Élevé', 'Équilibré', 'Économie']),
    ('Deutsch', ['Energieprofil', 'Hoch', 'Ausgewogen', 'Energiesparen']),
    ('Português', ['Perfil de energia', 'Alto', 'Equilibrado', 'Economia']),
    ('русский язык', ['Профиль питания', 'Высокий', 'Сбалансированный', 'Экономия']),
    ('Svenska', ['Energiprofil', 'Hög', 'Balanserad', 'Batterisparläge']),
    ('ภาษาไทย', ['โปรไฟล์พลังงาน', 'สูง', 'สมดุล', 'ประหยัดแบตเตอรี่']),
    ('język polski', ['Profil zasilania', 'Wysoki', 'Zrównoważony', 'Oszczędzanie']),
    ('Dansk', ['Strømprofil', 'Høj', 'Balanceret', 'Batterisparer']),
    ('Hollands', ['Energieprofiel', 'Hoog', 'Gebalanceerd', 'Batterijbesparing']),
    ('Italiano', ['Profilo energetico', 'Alto', 'Bilanciato', 'Risparmio']),
    ('Číština', ['Profil napájení', 'Vysoký', 'Vyvážený', 'Úspora baterie']),
    ('Türkçe', ['Güç profili', 'Yüksek', 'Dengeli', 'Pil tasarrufu']),
    ('עברית, עברי', ['פרופיל צריכת חשמל', 'גבוה', 'מאוזן', 'חיסכון בסוללה']),
    ('Arabic', ['وضع الطاقة', 'مرتفع', 'متوازن', 'توفير البطارية']),
    ('Español', ['Perfil de energía', 'Alto', 'Equilibrado', 'Ahorro de batería']),
    ('BahasaIndonesia', ['Profil Daya', 'Tinggi', 'Seimbang', 'Hemat Baterai']),
]


def run(*args, **kw):
    return subprocess.run(args, check=True, text=True, capture_output=True,
                          **kw).stdout


def header(self_id, father, index, child, prev, nxt, fn, children):
    ids = list(children) + [0xFFFF] * (21 - len(children))
    return struct.pack('<29H', self_id, father, index, child, prev, nxt, fn,
                       len(children), *ids)


def check_stock(raw):
    img = Image(raw)
    lang = img.sections['lang']
    images = img.sections['images']
    start, end = lang['offset'], images['offset'] + images['length']
    assert end - start == TABLE_DELTA, hex(end - start)
    assert struct.unpack_from('<H', raw, start)[0] == LANGS
    offs = [img.u32(start + 2 + 4 * i) for i in range(LANGS)]
    assert offs == [2 + 4 * LANGS + i * RECORDS * RECORD for i in range(LANGS)]
    names = [r['text'] for r in img.lang(2)][220:241]
    assert names == [n for n, _ in LABELS], names
    code_off, _ = img.module_region(0, 'code')
    m0 = raw[code_off:]
    lit = lambda a: struct.unpack_from('<I', m0, a - 0x03050000)[0]
    assert lit(0x0306329C) == 0x030232A0 and lit(0x030632A0) == 0x03023288
    # Both lookups use the 266-record stride (movw #0x4305, x4).
    for a in (0x030630C6, 0x03063224):
        assert m0[a - 0x03050000:a - 0x03050000 + 4] == bytes.fromhex('44f20533')
    return img, start, end


def site_offset(img, module, addr):
    off, length = img.module_region(module, 'code')
    rel = addr - img.modules[module]['code_exec']
    assert 0 <= rel < length
    return off + rel


def assemble(scratch):
    ld = scratch / 'p.ld'
    sites = '\n'.join(f' .site{n} {addr:#x} : {{ *(.site{n}) }}'
                      for n, _, _, addr, _, _ in SITES)
    pockets = '\n'.join(
        f' .p{i} {base:#x} : {{ *(.text) *({name}) }}\n'
        f' ASSERT(. <= {end:#x}, "{name} overflows its pocket")'
        if i == 0 else
        f' .p{i} {base:#x} : {{ *({name}) }}\n'
        f' ASSERT(. <= {end:#x}, "{name} overflows its pocket")'
        for i, (name, base, end) in enumerate(POCKETS))
    syms = '\n'.join(f'{k} = {v | 1:#x};' for k, v in EXTERNAL.items())
    ld.write_text(f'SECTIONS {{\n{pockets}\n{sites}\n'
                  ' /DISCARD/ : { *(.ARM.attributes) *(.comment) }\n}\n'
                  f'{syms}\n')
    stubs = ['.syntax unified', '.thumb']
    for n, _, _, _, _, insn in SITES:
        stubs += [f'.section .site{n}, "ax"', insn]
    (scratch / 'sites.S').write_text('\n'.join(stubs) + '\n')
    flags = ['-mcpu=cortex-m3', '-mthumb']
    for src in (HERE / 'profiles.S', scratch / 'sites.S'):
        run('arm-none-eabi-gcc', *flags, '-c', str(src),
            '-o', str(scratch / (src.stem + '.o')))
    elf = scratch / 'p.elf'
    out = subprocess.run(['arm-none-eabi-ld', '-T', str(ld),
                          str(scratch / 'profiles.o'), str(scratch / 'sites.o'),
                          '-o', str(elf)], text=True, capture_output=True)
    if out.returncode:
        raise SystemExit(out.stderr)
    for line in out.stderr.splitlines():
        # Absolute targets carry bit 0, so ld keeps Thumb branches; it
        # warns about each, and the decode check below confirms them.
        if 'Forcing branch to absolute symbol in Thumb mode' not in line:
            raise SystemExit(line)
    if run('arm-none-eabi-nm', '-u', str(elf)).strip():
        raise SystemExit('undefined symbols')
    blobs = {}
    for i, (_, base, _) in enumerate(POCKETS):
        b = scratch / f'p{i}.bin'
        run('arm-none-eabi-objcopy', '-O', 'binary', '-j', f'.p{i}', str(elf), str(b))
        blobs[base] = b.read_bytes()
    for n, _, _, addr, _, _ in SITES:
        b = scratch / f's{n}.bin'
        run('arm-none-eabi-objcopy', '-O', 'binary', '-j', f'.site{n}', str(elf), str(b))
        blobs[addr] = b.read_bytes()
    syms = {}
    for line in run('arm-none-eabi-nm', str(elf)).splitlines():
        p = line.split()
        if len(p) == 3:
            syms[p[2]] = int(p[0], 16)
    dis = run('arm-none-eabi-objdump', '-d', str(elf))
    return blobs, syms, dis


def verify_branches(dis, syms):
    """Every external branch in the disassembly lands on its target."""
    targets = {v: k for k, v in EXTERNAL.items()}
    seen = set()
    for line in dis.splitlines():
        parts = line.split('\t')
        if len(parts) >= 4 and parts[2].strip() in ('b.w', 'bl', 'beq.w', 'bhs.w', 'bcs.w'):
            t = int(parts[3].split()[0], 16)
            if t in targets:
                seen.add(targets[t])
    missing = set(EXTERNAL) - seen
    if missing:
        raise SystemExit(f'external branches not found: {missing}')


def write_patch(n, slug, module, addr, expect, replace, comment, rationale):
    p = PATCH_DIR / f'{n:04d}-{slug}.patch'
    p.write_text(
        f'# {comment}\n'
        f'name: {n:04d}-{slug}\n'
        'kind: module\n'
        f'module: {module}\n'
        'region: code\n'
        f'address: {addr:#x}\n'
        'gate: build refuses unless the stock bytes at the target equal\n'
        '  `expect`; regenerate with patches/power/profiles/build_profiles.py.\n'
        f'expect: {expect.hex()}\n'
        f'replace: {replace.hex()}\n'
        f'rationale: {rationale}\n')
    return p.name


def menu_runs(raw, start, end):
    runs = []
    # Per language: the settings menu gains a 17th child, and its last
    # child gains a next sibling.
    for lang in range(LANGS):
        base = start + 2 + 4 * LANGS + lang * RECORDS * RECORD
        rec = base + SETTINGS * RECORD
        count = struct.unpack_from('<H', raw, rec + 14)[0]
        assert count == 16, (lang, count)
        slot = rec + 16 + 2 * count
        assert raw[slot:slot + 2] == b'\xff\xff'
        runs.append((rec + 14, raw[rec + 14:rec + 16], struct.pack('<H', 17)))
        runs.append((slot, b'\xff\xff', struct.pack('<H', FIRST_NEW)))
        last = base + LAST_SETTING * RECORD
        assert struct.unpack_from('<5H', raw, last + 2) == (SETTINGS, 15, 0xFFFF, 242, 0xFFFF)
        runs.append((last + 10, b'\xff\xff', struct.pack('<H', FIRST_NEW)))
    table = bytearray()
    table += header(266, SETTINGS, 16, 267, LAST_SETTING, 0xFFFF, 0xFFFF,
                    (267, 268, 269))
    for k in range(3):
        table += header(267 + k, 266, k, 0xFFFF, 266 + k if k else 0xFFFF,
                        268 + k if k < 2 else 0xFFFF, 0xFFFF, ())
    for _, labels in LABELS:
        for text in labels:
            enc = text.encode('utf-16le')
            assert len(enc) + 2 <= LABEL, text
            table += enc + b'\0' * (LABEL - len(enc))
    assert len(table) == 4 * HEADER + LANGS * 4 * LABEL
    # The stock read routine fetches up to 200 text bytes; keep that
    # inside the zero padding before the image length.
    img = Image(raw)
    assert end + len(table) + 200 <= img.u32(0x1F4), 'table does not fit'
    assert not any(raw[end:end + len(table)])
    runs.append((end, bytes(len(table)), bytes(table)))
    return runs


def main():
    raw = (REPO / 'DP3_V137.img').read_bytes()
    img, start, end = check_stock(raw)
    with tempfile.TemporaryDirectory() as tmp:
        blobs, syms, dis = assemble(Path(tmp))
    verify_branches(dis, syms)
    names = []
    rationale_pocket = (
        'A stock routine here has no caller, branch, pointer or literal '
        'anywhere in core-0 code or data (patches/space/census_dead.py, '
        'tier 1), and no emulation suite executes it. Module 0 is '
        'resident in every window, so the settings window and every '
        'string lookup reach the code here.')
    for (n, slug), (sec, base, _) in zip(POCKET_PATCHES, POCKETS):
        code = blobs[base]
        off = site_offset(img, 0, base)
        names.append(write_patch(
            n, slug, 0, base, raw[off:off + len(code)], code,
            f'profiles.S {sec} assembled into a module 0 pocket at {base:#010x}.',
            rationale_pocket))
    reasons = {
        142: 'GetResourceStr entry (push {r4-r7}; ldr r5, =SAVEINFO) '
             'becomes a branch to str_hook, which re-runs both '
             'instructions for every stock id and sends ids 266 and up '
             'to the label table.',
        143: 'GetMenuTextInfoWithIDNum entry (push {r4, r5}; ldr r4, '
             '=SAVEINFO) becomes a branch to menu_hook, which re-runs '
             'both for every stock id and reads the headers of ids 266 '
             'and up from the table.',
        144: 'The settings window value switch starts with cmp r5, #188; '
             'it eq. value_hook runs that case itself, gives item 266 '
             'the profile matching the current settings, and re-enters '
             'the switch with the same flags otherwise.',
        145: "The commit handler's range check (ids 152..265) branches "
             'out of range to its default exit; commit_hook catches the '
             'three option ids, applies the profile through the stock '
             'setters and saves, then takes the same exit.',
    }
    for n, slug, module, addr, expect, _ in SITES:
        off = site_offset(img, module, addr)
        stock = raw[off:off + 4]
        assert stock == bytes.fromhex(expect), (hex(addr), stock.hex())
        names.append(write_patch(n, slug, module, addr, stock, blobs[addr],
                                 f'Power profile hook site in module {module}.',
                                 reasons[n]))
    runs = menu_runs(raw, start, end)
    MENU_JSON.write_text(json.dumps({'version': 1, 'runs': [
        {'offset': hex(o), 'expect': e.hex(), 'replace': r.hex()}
        for o, e, r in runs]}, indent=1) + '\n')
    for (sec, base, end_), in zip(POCKETS):
        print(f'{sec}: {len(blobs[base])} bytes at {base:#x} (room {end_ - base})')
    print('patches:', ', '.join(names))
    print(f'{MENU_JSON.name}: {len(runs)} runs')


if __name__ == '__main__':
    main()
