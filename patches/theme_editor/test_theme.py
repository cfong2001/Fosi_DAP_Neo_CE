#!/usr/bin/env python3
"""Run with: FOSI_STOCK_IMAGE=/path/DP3_V137.img python3 -m unittest discover -s patches/theme_editor -v"""
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import firmware_patch
import ui_theme
from rknano_image import Image

STOCK_PATH = os.environ.get("FOSI_STOCK_IMAGE")
if not STOCK_PATH:
    for candidate in (REPO / "DP3_V137.img", REPO.parent / "DP3_V137.img"):
        if candidate.is_file():
            STOCK_PATH = str(candidate)
            break


@unittest.skipUnless(STOCK_PATH and Path(STOCK_PATH).is_file(),
                     "pinned V137 image not available; set FOSI_STOCK_IMAGE")
class ThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock = Path(STOCK_PATH).read_bytes()
        assert hashlib.sha256(cls.stock).hexdigest() == ui_theme.STOCK_SHA256
        cls.image = Image(cls.stock)
        cls.asset = list(cls.image.images())[6]
        cls.source = struct.unpack_from("<H", cls.stock, cls.asset["data_offset"])[0]

    def config(self, count=6060, source="0xA210"):
        return {
            "version": 1,
            "palette": {
                "background": "#141821", "text": "#FFFFFF",
                "highlight": "#38BDF8", "icons": "#E0E7FF",
                "progress_bar": "#38BDF8"
            },
            "resources": [
                {"id": 6, "role": "highlight",
                 "source": source, "expected_count": count}
            ],
            "literal_sites": []
        }

    def test_all_456_resources_are_rgb565(self):
        assets = ui_theme.catalog(self.stock)
        self.assertEqual(len(assets), 456)
        self.assertTrue(all(a["rgb565_bytes"] for a in assets))
        self.assertEqual(assets[6]["observed_label"], "battery graphic, level variant 1")

    def test_recolors_only_selected_source_pixels(self):
        before = self.stock
        after, report = ui_theme.apply_theme(before, self.config())
        self.assertEqual(len(after), len(before))
        a = self.asset
        lo, hi = a["data_offset"], a["data_offset"] + a["size"]
        self.assertEqual(after[:lo], before[:lo])
        self.assertEqual(after[hi:], before[hi:])
        source = 0xA210
        target = ui_theme.rgb565("#38BDF8")
        modified = 0
        for i in range(lo, hi, 2):
            v0, v1 = (struct.unpack_from("<H", x, i)[0] for x in (before, after))
            self.assertEqual(v1, target if v0 == source else v0)
            if v0 == source:
                modified += 1
        self.assertEqual(modified, 6060)
        self.assertEqual(report["changes"][0]["pixels"], 6060)
        self.assertEqual(report["changes"][0]["id"], 6)

    def test_finalization_validates_and_keeps_length(self):
        after, _ = ui_theme.apply_theme(self.stock, self.config())
        from importlib.util import spec_from_file_location, module_from_spec
        path = REPO / "patches" / "framework" / "build.py"
        spec = spec_from_file_location("theme_fwbuild", path)
        build = module_from_spec(spec)
        spec.loader.exec_module(build)
        image = build.finalize(after, "20261023")
        firmware_patch.validate(image)
        self.assertEqual(len(image), len(self.stock))
        self.assertEqual(image[:4], firmware_patch.bcd_date("20261023"))

    def test_bad_counts_and_unsafe_keys_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "expected"):
            ui_theme.apply_theme(self.stock, self.config(count=6061))
        with self.assertRaisesRegex(ValueError, "reserved"):
            ui_theme.apply_theme(self.stock, self.config(count=69926, source="0x0000"))

    def test_overlap_and_literal_gates(self):
        a = self.asset
        with self.assertRaisesRegex(ValueError, "overlaps"):
            ui_theme.apply_theme(self.stock, self.config(),
                                 protected_ranges=[(a["data_offset"], a["data_offset"] + 1)])
        bad = self.config()
        bad["literal_sites"] = [{"module": 0, "region": "code",
                                 "address": "0x03050000", "source": "0x0000",
                                 "role": "text"}]
        with self.assertRaisesRegex(ValueError, "evidence"):
            ui_theme.apply_theme(self.stock, bad)

    def test_blank_config_does_not_mutate_original(self):
        c = self.config()
        c["resources"] = []
        after, report = ui_theme.apply_theme(self.stock, c)
        self.assertEqual(after, self.stock)
        self.assertEqual(report["changed_bytes"], 0)

    def test_catalog_previews_are_valid_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = ui_theme.write_catalog(self.stock, tmp)
            self.assertEqual(len(entries), 456)
            self.assertTrue((Path(tmp) / "index.html").exists())
            data = json.loads((Path(tmp) / "catalog.json").read_text())
            self.assertEqual(data["resource_count"], 456)
            png = (Path(tmp) / "assets" / "asset_006.png").read_bytes()
            self.assertTrue(png.startswith(bytes.fromhex("89504e470d0a1a0a")))


if __name__ == "__main__":
    unittest.main()
