"""Regression tests for composition geometry checks (no target tools needed)."""
import copy
import json
from pathlib import Path
import unittest

from ci.check_combined_layout import ROOT, audit, intersections, validate_parts, validate_recorded


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.parts = [{'name': 'one', 'offset': 0, 'address': '0x1000', 'bytes': 8},
                      {'name': 'two', 'offset': 12, 'address': '0x100c', 'bytes': 4}]

    def test_adjacent_and_gapped_pieces(self):
        validate_parts(0x1000, 16, self.parts)
        self.parts[1].update(offset=8, address='0x1008')
        validate_parts(0x1000, 16, self.parts)

    def test_collision_bounds_and_address_drift_rejected(self):
        for update in ({'offset': 7, 'address': '0x1007'},
                       {'offset': 13, 'address': '0x100d'},
                       {'address': '0x1010'}, {'bytes': 0}):
            with self.subTest(update=update):
                parts = copy.deepcopy(self.parts)
                parts[1].update(update)
                with self.assertRaises(ValueError):
                    validate_parts(0x1000, 16, parts)

    def test_half_open_intersections_include_data_and_bss(self):
        m = {'index': 5, 'code_exec': 100, 'code_len': 10,
             'data_exec': 110, 'data_len': 2, 'bss_exec': 111, 'bss_len': 4}
        self.assertEqual([(i, k) for i, k, _, _ in intersections([m], 110, 111)], [(5, 'data')])
        self.assertEqual([(i, k) for i, k, _, _ in intersections([m], 111, 112)], [(5, 'data'), (5, 'bss')])

    def test_recorded_plan_overflow_rejected_without_image(self):
        layout = json.loads((ROOT / 'patches/full/out/layout31.json').read_text())
        tail = json.loads((ROOT / 'patches/full/out/layout_tail.json').read_text())
        validate_recorded(layout, tail)
        tail['pieces'][1]['offset'] = 500
        tail['pieces'][1]['address'] = hex(int(tail['tail_base'], 0) + 500)
        with self.assertRaisesRegex(ValueError, 'collision'):
            validate_recorded(layout, tail)
        tail = json.loads((ROOT / 'patches/full/out/layout_tail.json').read_text())
        layout['staging_caps']['max_entries'] += 1
        with self.assertRaisesRegex(ValueError, 'staging cap'):
            validate_recorded(layout, tail)

    @unittest.skipUnless((ROOT / 'DP3_V137.img').exists(), 'stock image unavailable')
    def test_recorded_layout_and_corrupt_budget(self):
        raw = (ROOT / 'DP3_V137.img').read_bytes()
        layout = json.loads((ROOT / 'patches/full/out/layout31.json').read_text())
        tail = json.loads((ROOT / 'patches/full/out/layout_tail.json').read_text())
        audit(raw, layout, tail)
        layout['spare'] += 1
        with self.assertRaises(ValueError):
            audit(raw, layout, tail)


if __name__ == '__main__':
    unittest.main()
