"""No CE patch overwrites stock bytes that live code still reaches.

`tools/patch_xref_audit.py` lists stock references into every changed
byte range. Each reference it finds today has been read in context and is
listed in KNOWN with the reason it is harmless. A new reference fails the
test until someone reads it and either fixes the patch or adds it here.
"""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from patch_xref_audit import audit  # noqa: E402

STOCK = (ROOT / 'DP3_V137.img').read_bytes()
REPORTS = {
    'standard': ROOT / 'release/DP3_V137_CE.img.report.json',
    'minimal': ROOT / 'release/DP3_V137_CE_minimal.img.report.json',
}

LITERAL_POOL = 'source is a literal pool word decoded as an instruction'
DEAD_PAINTER = ('source is inside the old metadata painter that patches 0160 to 0163 '
                'replace; nothing outside it reaches 0x0307EBA4..0x0307ECA4')
DEAD_TITLE_LOOP = ('source is the stock title-copy loop that patch 0163 skips with '
                   'b.w 0x0307F9EE; nothing else enters 0x0307F9D6..0x0307F9EE')
I2C_LOG = ('stock i2c_write passes an overwritten debug string to the logger at '
           '0x0306D8F0 on an I2C error; the replacement bytes hold no "%" and reach '
           'a zero byte within 22 bytes, so the log line is garbled and nothing else')

# (patch, target, source) -> why the reference is harmless
KNOWN = {
    ('0173-artwork-pixels', '0x3052efc', '0x3052ce2'): I2C_LOG,
    ('0173-artwork-pixels', '0x3052f14', '0x3052cec'): I2C_LOG,
    ('0173-artwork-pixels', '0x3052f38', '0x3052cf4'): I2C_LOG,
    ('0160-track-info', '0x307eb48', '0x3058fe0'):
        'source is the second halfword of adc.w at 0x03058FE0, not a pointer',
    ('0161-metadata-helpers', '0x307ed64', '0x307ec96'): DEAD_PAINTER,
    ('0161-metadata-helpers', '0x307ed64', '0x307eca2'): DEAD_PAINTER,
    ('0118-progress-knob-keyed', '0x307f79c', '0x307f628'): LITERAL_POOL,
    ('0163-player-tag-title', '0x307f9d4', '0x307f9ec'): DEAD_TITLE_LOOP,
    ('gapless-4-keep-decoder', '0x3089404', '0x3089204'): LITERAL_POOL,
}


def keys(findings):
    return {(f['patch'], f['target'], f['source']) for f in findings}


class PatchReferenceAudit(unittest.TestCase):
    def test_release_images_have_only_triaged_references(self):
        for name, path in REPORTS.items():
            with self.subTest(image=name):
                findings, _ = audit(STOCK, json.loads(path.read_text()), interior_only=True)
                unknown = sorted(keys(findings) - KNOWN.keys())
                self.assertEqual(unknown, [], 'read each new reference in context, then fix '
                                 'the patch or add it to KNOWN with the reason')

    def test_known_list_has_no_stale_entries(self):
        found = set()
        for path in REPORTS.values():
            found |= keys(audit(STOCK, json.loads(path.read_text()), interior_only=True)[0])
        self.assertEqual(sorted(KNOWN.keys() - found), [])

    def test_shutdown_stub_trampoline_is_caught(self):
        """The DAC trampoline at 0x03060D8E, fixed in PR #41, must fail the audit."""
        report = copy.deepcopy(json.loads(REPORTS['minimal'].read_text()))
        cave = next(p for p in report['patches_applied'] if p['patch'] == 'dac-fix-2-cave')
        cave['cpu_address'] = '0x3060d8e'
        cave['new_hex'] = '6870c4e7'
        findings, _ = audit(STOCK, report, interior_only=True)
        hits = {(f['source'], f['filler']) for f in findings if f['patch'] == 'dac-fix-2-cave'}
        self.assertEqual(hits, {('0x30536c4', True), ('0x3067cd8', True)})


if __name__ == '__main__':
    unittest.main()
