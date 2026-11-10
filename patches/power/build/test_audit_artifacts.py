"""Check that linked patch sites cannot silently drift from their hooks."""
import unittest

from audit_artifacts import EXPECTED_HOOKS, audit


class ArtifactAuditTest(unittest.TestCase):
    def test_accepts_expected_geometry_and_rejects_drift(self):
        sites = [bytes.fromhex('02f0babb00bf'), bytes.fromhex('02f047bb00bf')]
        audit(EXPECTED_HOOKS, '', bytes(540), sites)
        bad_cases = [({}, '', bytes(540), sites),
                     (EXPECTED_HOOKS, ' U missing', bytes(540), sites),
                     (EXPECTED_HOOKS, '', bytes(539), sites),
                     (EXPECTED_HOOKS, '', bytes(540), [b'bad', sites[1]])]
        for symbols, undefined, blob, site_bytes in bad_cases:
            with self.subTest(symbols=symbols, undefined=undefined, size=len(blob)):
                with self.assertRaises(ValueError):
                    audit(symbols, undefined, blob, site_bytes)


if __name__ == '__main__':
    unittest.main()
