import math
import unittest

from scripts.m03_onepair_delta_screen import exact_prediction, parse_official_report


class ExactPredictionTest(unittest.TestCase):
    def test_exact_one_pair_formula(self):
        baseline = {
            "samples": 600,
            "pose": 0.00003,
            "seg": 0.0005,
            "rate": 0.0047,
            "uncompressed_bytes": 1_000_000,
        }
        pair = {"pose_delta": 0.0006, "seg_delta": -0.0003}
        predicted = exact_prediction(baseline, pair, 4701)
        expected = 100 * (0.0005 - 0.0003 / 600) + math.sqrt(
            10 * (0.00003 + 0.0006 / 600)
        ) + 25 * 0.004701
        self.assertAlmostEqual(predicted["final"], expected, places=15)


if __name__ == "__main__":
    unittest.main()
