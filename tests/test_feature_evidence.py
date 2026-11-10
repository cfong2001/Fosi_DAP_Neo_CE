import copy
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "ci" / "check_feature_evidence.py"
spec = importlib.util.spec_from_file_location("check_feature_evidence", MODULE)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class EvidenceValidation(unittest.TestCase):
    def setUp(self):
        self.ledger = {"schema": 1, "scope": "test", "levels": list(check.LEVELS),
                       "features": [{"id": "player", "name": "Player",
                                     "status": dict.fromkeys(check.LEVELS, "not_run"),
                                     "evidence": "No execution yet."}]}

    def test_incomplete_validation_is_explicit(self):
        self.assertEqual(check.validate(self.ledger), [])
        del self.ledger["features"][0]["status"]["hardware"]
        self.assertTrue(check.validate(self.ledger))

    def test_duplicate_and_invalid_status_rejected(self):
        self.ledger["features"].append(copy.deepcopy(self.ledger["features"][0]))
        self.ledger["features"][0]["status"]["emulation"] = "probably"
        errors = check.validate(self.ledger)
        self.assertTrue(any("duplicate" in error for error in errors))
        self.assertTrue(any("invalid emulation" in error for error in errors))

    def test_empty_evidence_rejected(self):
        self.ledger["features"][0]["evidence"] = " "
        self.assertTrue(check.validate(self.ledger))


if __name__ == "__main__":
    unittest.main()
