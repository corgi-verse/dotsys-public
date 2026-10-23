import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("exchange", ROOT / "tools/validate_exchange.py")
exchange = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exchange)


class ExchangeTests(unittest.TestCase):
    def test_registry_has_real_original_and_credited_adaptation(self):
        records = exchange.registry(ROOT)
        self.assertEqual(records["quiet-listening-room-clay"]["parent"], "quiet-listening-room-jade")
        self.assertIn("quiet-listening-room-jade", records["quiet-listening-room-clay"]["credits"])

    def test_proposal_hash_missing_file_and_parent_errors(self):
        original = exchange.read(ROOT / "creations/quiet-listening-room/original/submission.json")
        self.assertEqual(exchange.submission(ROOT, original)["id"], "quiet-listening-room-jade")
        for field, value in [("artifact_sha256", "0" * 64), ("editable", "missing.json"), ("process", "../private.md"), ("tool", "latest"), ("parent", original["id"])]:
            bad = copy.deepcopy(original)
            bad[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                exchange.submission(ROOT, bad)


if __name__ == "__main__":
    unittest.main()
