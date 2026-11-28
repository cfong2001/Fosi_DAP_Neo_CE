"""tools/port_patches.py: V137 patches re-derived for newer official images.

Needs DP3_V137.img at the repository root. The checks of the committed
patches/ported/ files need capstone. The regeneration and V162 build
checks need the official images: set FOSI_OFFICIAL_IMAGES to a directory
holding DP3_V155.img, DP3_V161.img and DP3_V162.img (and FOSI_ECPATCH_DIR
for the Vorbis transplant). The images are not stored in the repository.
"""
import hashlib
import importlib.util
import json
import os
import re
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import port_patches as pp  # noqa: E402
from official_images import BY_VERSION  # noqa: E402
from rknano_image import Image  # noqa: E402

spec = importlib.util.spec_from_file_location('fw_build', ROOT / 'patches/framework/build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

STOCK = ROOT / 'DP3_V137.img'
PORTED = ROOT / 'patches/ported'
OFFICIAL_DIR = os.environ.get('FOSI_OFFICIAL_IMAGES')
V137_PATCHES = {p['file']: p for p in build.load_manifest(ROOT / 'patches/framework/patches/manifest.txt')}

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
except ImportError:
    Cs = None


def official(version):
    path = Path(OFFICIAL_DIR or '/nonexistent') / f'DP3_{version}.img'
    return path.read_bytes() if path.exists() else None


@unittest.skipUnless(STOCK.exists(), 'DP3_V137.img not present')
class IdentityTest(unittest.TestCase):
    def test_porting_v137_onto_itself_reproduces_every_patch(self):
        raw = STOCK.read_bytes()
        porter = pp.Porter(raw, raw).run()
        for q in porter.ports:
            p = q.patch
            with self.subTest(patch=p['file']):
                self.assertEqual(q.status, 'PORTED', q.reason)
                self.assertEqual(q.address, p['address'])
                self.assertEqual(q.expect, p['expect'])
                self.assertEqual(q.replace, p['replace'])
        self.assertEqual([t['status'] for t in porter.transplants(['vorbis75'])], ['PORTED'])


@unittest.skipUnless(STOCK.exists(), 'DP3_V137.img not present')
class RefusalTest(unittest.TestCase):
    """A target made from V137 with two changes: one instruction inside
    dac_write (the DAC fix's hooked routine), and one module 0 data word
    pointing into the sort-key cave."""

    @classmethod
    def setUpClass(cls):
        raw = bytearray(STOCK.read_bytes())
        im = Image(bytes(raw))
        code, _ = im.module_region(0, 'code')
        o = code + 0x03060C56 - 0x03050000          # ldrb.w ip, [ip, #0x2e8]
        assert raw[o:o + 4] == bytes.fromhex('9cf8e8c2')
        raw[o + 2] = 0xE9                            # now #0x2e9
        data, ln = im.module_region(0, 'data')
        w = next(i for i in range(data, data + ln - 3, 4) if raw[i:i + 4] == bytes(4))
        struct.pack_into('<I', raw, w, 0x0309F101)
        cls.raw = bytes(raw)
        cls.ports = {q.patch['name']: q for q in pp.Porter(STOCK.read_bytes(), cls.raw).run().ports}

    def test_changed_hooked_routine_is_a_conflict(self):
        for name in ('dac-fix-1-branch', 'dac-fix-2-cave'):
            self.assertEqual(self.ports[name].status, 'CONFLICT')
            self.assertIn('dac_write', self.ports[name].reason)

    def test_referenced_cave_is_unported_with_its_whole_feature(self):
        self.assertEqual(self.ports['sortkeys-cave'].status, 'UNPORTED')
        self.assertIn('cave referenced', self.ports['sortkeys-cave'].reason)
        for name in pp.FEATURES['sortkeys'][0]:
            self.assertEqual(self.ports[name].status, 'UNPORTED', name)

    def test_untouched_features_still_port_unchanged(self):
        touched = set(pp.FEATURES['dac-fix'][0]) | set(pp.FEATURES['sortkeys'][0])
        for name, q in self.ports.items():
            if name not in touched:
                self.assertEqual((q.status, q.address, q.replace),
                                 ('PORTED', q.patch['address'], q.patch['replace']), name)

    def test_only_an_official_target_gets_output_files(self):
        with self.assertRaisesRegex(ValueError, 'not an official image'):
            pp.render(STOCK.read_bytes(), self.raw)


BRANCH = re.compile(r'^(b|bl|blx|cbz|cbnz)(eq|ne|cs|hs|cc|lo|mi|pl|vs|vc|hi|ls|ge|lt|gt|le|al)?(\.w|\.n)?$')


def operand(ins):
    """(kind, value) of a PC-relative or MOVW/MOVT operand, else None."""
    m, op = ins.mnemonic, ins.op_str
    base = (ins.address + 4) & ~3
    if m in ('movw', 'movt'):
        return 'imm16', int(op.rsplit('#', 1)[1], 0)
    if '[pc' in op:
        imm = op.split('[pc', 1)[1].strip(' ,]#')
        return 'load', base + (int(imm, 0) if imm else 0)
    if re.match(r'^(add|sub)w?(\.w)?$', m) and ', pc, #' in op:
        imm = int(op.rsplit('#', 1)[1], 0)
        return 'adr', base - imm if m.startswith('sub') else base + imm
    if m == 'adr':
        return 'adr', base + int(op.rsplit('#', 1)[1], 0)
    if BRANCH.match(m) and '#' in op:
        return 'branch', int(op.rsplit('#', 1)[1], 0)
    return None


def ported_versions():
    return sorted(d.name for d in PORTED.iterdir() if (d / 'port_report.json').exists()) \
        if PORTED.exists() else []


@unittest.skipUnless(Cs, 'capstone not installed')
class PortedFilesTest(unittest.TestCase):
    """Every committed ported patch, disassembled next to its V137 original,
    is the same instruction stream: the only differences are PC-relative
    targets and MOVW/MOVT or literal addresses, each equal to the mapping
    the port report records (or to the new address of the patch it points
    into)."""

    def test_versions_present(self):
        self.assertEqual(ported_versions(), ['V155', 'V161', 'V162'])

    def test_files_match_report(self):
        for version in ported_versions():
            d = PORTED / version
            rep = json.loads((d / 'port_report.json').read_text())
            listed = (d / 'manifest.txt').read_text().split()
            with self.subTest(version=version):
                self.assertEqual(rep['target']['sha256'], BY_VERSION[version])
                self.assertEqual(listed, [r['file'] for r in rep['patches'] if r['status'] == 'PORTED'])
                self.assertEqual(sorted(listed), sorted(f.name for f in d.glob('*.patch')))
                for r in rep['patches']:
                    if r['status'] != 'PORTED':
                        self.assertTrue(r['reason'], r['file'])
                for name in listed:
                    p = build.parse_patch(d / name)
                    self.assertEqual(p['base_sha256'], BY_VERSION[version])
                    self.assertIn(name, p['ported_from'])
                    row = next(r for r in rep['patches'] if r['file'] == name)
                    self.assertEqual(hex(p['address']), row['target_address'])

    def test_ported_sites_disassemble_equivalent(self):
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        for version in ported_versions():
            d = PORTED / version
            rep = json.loads((d / 'port_report.json').read_text())
            moved = [(V137_PATCHES[r['file']], int(r['target_address'], 16))
                     for r in rep['patches'] if r['status'] == 'PORTED']
            for r in rep['patches']:
                if r['status'] != 'PORTED':
                    continue
                with self.subTest(version=version, patch=r['file']):
                    self._equivalent(md, V137_PATCHES[r['file']], build.parse_patch(d / r['file']),
                                     r, moved)

    def _equivalent(self, md, old, new, row, moved):
        if old['replace'] == old['expect']:          # the no-op fixture stays a no-op
            self.assertEqual(new['replace'], new['expect'])
            return
        a0, a1, n = old['address'], new['address'], len(old['replace'])
        relocs ={x['offset']: x for x in row['relocations']}
        movt = {x['movt_offset']: x for x in row['relocations'] if 'movt_offset' in x}

        def mapped(v, o):
            if a0 <= v < a0 + n:
                return v + a1 - a0
            if o in relocs:
                self.assertEqual(int(relocs[o]['v137'], 16), v)
                return int(relocs[o]['target'], 16)
            for p, at in moved:
                if p['module'] in (old['module'], 0) and p['address'] <= v < p['address'] + len(p['replace']):
                    return at + v - p['address']
            self.fail(f'+{o:#x} refers to {v:#x} outside every patch with no recorded relocation')

        covered = set()
        for o in row['code_offsets']:
            x = next(md.disasm(old['replace'][o:], a0 + o, 1))
            y = next(md.disasm(new['replace'][o:], a1 + o, 1))
            covered.update(range(o, o + x.size))
            self.assertEqual((x.size, x.mnemonic), (y.size, y.mnemonic), f'+{o:#x}')
            ox, oy = operand(x), operand(y)
            if ox is None:
                self.assertEqual(x.op_str, y.op_str, f'+{o:#x} {x.mnemonic}')
            elif ox[0] == 'imm16':
                rel = relocs.get(o) or movt.get(o)
                if rel is None:
                    self.assertEqual(ox, oy, f'+{o:#x}')
                else:
                    shift = 0 if x.mnemonic == 'movw' else 16
                    self.assertEqual(ox[1], int(rel['v137'], 16) >> shift & 0xFFFF)
                    self.assertEqual(oy[1], int(rel['target'], 16) >> shift & 0xFFFF)
            else:
                self.assertEqual(ox[0], oy[0])
                self.assertEqual(oy[1], mapped(ox[1], o), f'+{o:#x} {x.mnemonic} {x.op_str}')
        for o in range(n):
            if o in covered:
                continue
            word = next((w for w, x in relocs.items() if x['kind'] == 'word' and w <= o < w + 4), None)
            if word is None:
                self.assertEqual(old['replace'][o], new['replace'][o], f'data byte +{o:#x}')
            elif o == word:
                rel = relocs[word]
                self.assertEqual(struct.unpack_from('<I', old['replace'], o)[0], int(rel['v137'], 16))
                self.assertEqual(struct.unpack_from('<I', new['replace'], o)[0], int(rel['target'], 16))

    def test_build_refuses_patches_for_another_base(self):
        ported = build.parse_patch(PORTED / 'V162' / '0019-i2c-reset-pulse.patch')
        stock = V137_PATCHES['0019-i2c-reset-pulse.patch']
        with self.assertRaisesRegex(ValueError, 'another base image'):
            build.build_image(b'', [ported], build.DEFAULT_BUILD_DATE)
        with self.assertRaisesRegex(ValueError, 'another base image'):
            build.build_image(b'', [stock], '20261118', base_version='V162')
        with self.assertRaisesRegex(ValueError, 'input SHA-256'):
            build.build_image(b'', [ported], '20261118', base_version='V162')


@unittest.skipUnless(STOCK.exists() and official('V162'), 'set FOSI_OFFICIAL_IMAGES')
class OfficialImagesTest(unittest.TestCase):
    def test_committed_outputs_regenerate(self):
        for version in ported_versions():
            raw = official(version)
            if raw is None:
                continue
            got_version, files = pp.render(STOCK.read_bytes(), raw)
            self.assertEqual(got_version, version)
            for name, text in files.items():
                with self.subTest(version=version, file=name):
                    self.assertEqual((PORTED / version / name).read_text(), text)

    @unittest.skipUnless(Cs, 'capstone not installed')
    def test_relocations_land_on_the_same_stock_code(self):
        """Checked with capstone, apart from the tool: a relocated branch
        lands on code that opens with the same instructions as its V137
        target, and a relocated RAM constant is one the target's own stock
        code loads."""
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        src = Image(STOCK.read_bytes())
        for version in ported_versions():
            raw = official(version)
            if raw is None:
                continue
            dst = Image(raw)
            rep = json.loads((PORTED / version / 'port_report.json').read_text())
            checked = 0
            for r in rep['patches']:
                for rel in r.get('relocations', ()):
                    old, new = int(rel['v137'], 16), int(rel['target'], 16)
                    if rel['evidence'].startswith('inside '):
                        continue
                    checked += 1
                    with self.subTest(version=version, patch=r['file'], at=rel['offset']):
                        if rel['kind'] in ('movw/movt', 'word'):
                            self.assertTrue(self._loaded_by_stock(dst, new), hex(new))
                        else:
                            self.assertEqual(self._opening(md, src, r['module'], old),
                                             self._opening(md, dst, r['module'], new))
            self.assertGreater(checked, 0, version)

    @staticmethod
    def _segment(im, module, addr):
        for m in (module, 0):
            rec = im.modules[m]
            if rec['code_exec'] <= addr < rec['code_exec'] + rec['code_len']:
                off, _ = im.module_region(m, 'code')
                return im.raw[off + addr - rec['code_exec']:off + rec['code_len']], addr
        raise AssertionError(f'{addr:#x} is not code of module {module} or 0')

    def _opening(self, md, im, module, addr, count=4):
        code, at = self._segment(im, module, addr)
        out = []
        for ins in md.disasm(code[:64], at, count):
            plain = operand(ins) is None and not ins.mnemonic.startswith('bl')
            out.append((ins.mnemonic, ins.op_str if plain else ''))
        return out

    @staticmethod
    def _loaded_by_stock(im, value):
        word = struct.pack('<I', value)
        for m in im.modules:
            off, ln = im.module_region(m['index'], 'code')
            seg, j = im.raw[off:off + ln], 0
            while (j := seg.find(word, j)) >= 0:
                if (m['code_exec'] + j) % 4 == 0:
                    return True
                j += 1
        return False

    def test_v162_minimal_build_validates_and_lists_what_did_not_port(self):
        raw = official('V162')
        d = PORTED / 'V162'
        patches = build.load_manifest(d / 'manifest.txt')
        ecpatch = os.environ.get('FOSI_ECPATCH_DIR')
        transplants = build.load_transplant_names(d / 'transplants.txt') if ecpatch else []
        out, report = build.build_image(raw, patches, build.base_build_date('V162'),
                                        transplants=transplants, ecpatch_dir=ecpatch, base_version='V162')
        self.assertIn('validate_grown() passed', report['validation'])
        self.assertEqual(out[:4], bytes.fromhex('26201811'))
        self.assertEqual(len(report['patches_applied']), len(patches))
        claimed = [(int(e['file_offset'], 16), int(e['file_offset'], 16) + len(bytes.fromhex(e['new_hex'])))
                   for e in report['patches_applied']]
        claimed += [(a, b + 1) for t in report['transplants_applied'] for a, b in t['ranges']]
        mirror = Image(raw).u32(0x1F4)
        claimed += [(0, 4), (mirror, mirror + 4), (len(out) - 4, len(out))]
        stray = [i for i in range(len(out)) if out[i] != raw[i] and not any(a <= i < b for a, b in claimed)]
        self.assertEqual(stray, [])
        rep = json.loads((d / 'port_report.json').read_text())
        unported = {r['file'] for r in rep['patches'] if r['status'] != 'PORTED'}
        self.assertEqual(unported, set(V137_PATCHES) - {p['file'] for p in patches})
        if transplants:
            self.assertEqual(hashlib.sha256(out).hexdigest(), report['output_sha256'])


if __name__ == '__main__':
    unittest.main()
