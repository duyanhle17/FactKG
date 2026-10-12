"""Small checks for the DFS/round-robin diagnostic merge."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_round_robin_hybrid_candidates import build_hybrid


class HybridCandidateTest(unittest.TestCase):
    def test_only_dfs_limited_claims_are_replaced(self):
        old = {
            "limited": {"connected": [], "walkable": [["A", "r", "B"]]},
            "unlimited": {"connected": [["C", "s", "D"]], "walkable": []},
        }
        new = {
            "limited": {"connected": [["A", "t", "Z"]], "walkable": []},
            "unlimited": {"connected": [], "walkable": [["C", "s", "X"]]},
        }
        report = {
            "config": {"search_schedule": "dfs"},
            "splits": {"test": {"expansion_limited_claims": ["limited"]}},
        }
        new_report = {"config": {"search_schedule": "round_robin"}}
        inputs = {key: {"path": key} for key in (
            "data_dir", "kg", "relation_predictions", "hop_predictions"
        )}
        manifest = {"inputs": inputs}
        hybrid, summary = build_hybrid(
            old, new, report, new_report, manifest, manifest, 32
        )
        self.assertEqual(hybrid["limited"], new["limited"])
        self.assertEqual(hybrid["unlimited"], old["unlimited"])
        self.assertEqual(summary["dfs_expansion_limited"], 1)
        self.assertEqual(summary["v4_inputs_changed"], 1)
        self.assertEqual(summary["changed_outside_dfs_limited"], 0)

    def test_rejects_different_prediction_inputs(self):
        row = {"A": {"connected": [], "walkable": []}}
        report = {
            "config": {"search_schedule": "dfs"},
            "splits": {"test": {"expansion_limited_claims": ["A"]}},
        }
        new_report = {"config": {"search_schedule": "round_robin"}}
        manifest_a = {"inputs": {key: {"path": "same"} for key in (
            "data_dir", "kg", "relation_predictions", "hop_predictions"
        )}}
        manifest_b = {"inputs": {key: dict(value) for key, value in manifest_a["inputs"].items()}}
        manifest_b["inputs"]["relation_predictions"]["path"] = "different"
        with self.assertRaisesRegex(ValueError, "relation_predictions"):
            build_hybrid(row, row, report, new_report, manifest_a, manifest_b, 32)


if __name__ == "__main__":
    unittest.main()
