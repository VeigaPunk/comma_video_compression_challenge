import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.m04_evaluate_proof import (
    OFFICIAL_EVALUATE_SH_SHA256,
    OFFICIAL_EVALUATOR_SHA256,
    assert_exact_raw,
    full_precision_source,
)


ROOT = Path(__file__).resolve().parents[1]


class OfficialEvaluatorProofTest(unittest.TestCase):
    def test_official_evaluator_is_byte_exact(self):
        source = (ROOT / "evaluate.py").read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(), OFFICIAL_EVALUATOR_SHA256)
        shell = (ROOT / "evaluate.sh").read_bytes()
        self.assertEqual(hashlib.sha256(shell).hexdigest(), OFFICIAL_EVALUATE_SH_SHA256)

    def test_precision_transform_only_changes_result_formats(self):
        official = (ROOT / "evaluate.py").read_text(encoding="utf-8")
        precise = full_precision_source(official)
        self.assertEqual(precise.count(".17g"), 4)
        self.assertNotIn(".8f", precise)
        self.assertNotIn(".2f", precise)

    def test_exact_raw_cardinality(self):
        with tempfile.TemporaryDirectory() as temporary:
            raw = Path(temporary) / "video.raw"
            raw.write_bytes(b"\0" * (4 * 3 * 3 * 4))
            proof = assert_exact_raw(raw, pairs=2, width=4, height=3)
            self.assertEqual(proof["frames"], 4)
            self.assertEqual(proof["raw_shape"], [4, 3, 4, 3])
            raw.write_bytes(raw.read_bytes() + b"\0")
            with self.assertRaisesRegex(ValueError, "raw byte cardinality"):
                assert_exact_raw(raw, pairs=2, width=4, height=3)


if __name__ == "__main__":
    unittest.main()
