"""Unit checks for one-path-swap candidate construction."""

import sys
import json
import pickle
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from conjunction_single_swap_ablation import make_swap_row, prepare, swap_plan


class SingleSwapTest(unittest.TestCase):
    def test_each_variant_changes_only_one_walkable_path(self):
        first = [["A", "r", "X"], ["A", "s", "Y"], ["A", "t", "Z"]]
        ranked = [["A", "u", "U"], first[0], ["A", "v", "V"]]
        plan = swap_plan(first, ranked)
        self.assertEqual(len(plan), 2)
        row = {"connected": [["A", "c", "C"]], "walkable": first}
        first_swap = make_swap_row(row, plan, 1)
        second_swap = make_swap_row(row, plan, 2)
        self.assertEqual(first_swap["walkable"], [first[0], ranked[0], first[2]])
        self.assertEqual(second_swap["walkable"], [first[0], first[1], ranked[2]])
        self.assertEqual(first_swap["connected"], row["connected"])
        self.assertEqual(row["walkable"], first)

    def test_prepare_writes_test_style_subset_without_gold_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            claim = "A and B"
            other = "Other"
            data = {
                claim: {"Entity_set": ["A", "B"], "Label": [False],
                        "types": ["multi claim"], "Evidence": {"A": [["r"]]}},
                other: {"Entity_set": ["C"], "Label": [True],
                        "types": ["num1"], "Evidence": {}},
            }
            first = {claim: {"connected": [], "walkable": [["A", "r", "X"]]},
                     other: {"connected": [], "walkable": []}}
            ranked = {claim: {"connected": [], "walkable": [["B", "s", "Y"]]},
                      other: {"connected": [], "walkable": []}}
            objects = {
                "data": data, "first_candidates": first,
                "ranked_candidates": ranked,
                "first5": {"label": [0, 1], "reasoning_type": [2, 0],
                           "prediction": [0, 1]},
                "ranked5": {"label": [0, 1], "reasoning_type": [2, 0],
                            "prediction": [1, 1]},
            }
            paths = {}
            for name, value in objects.items():
                paths[name] = root / f"{name}.pickle"
                with paths[name].open("wb") as handle:
                    pickle.dump(value, handle)
            output = root / "ablation"
            prepare(Namespace(**paths, report=None, output_dir=output,
                              max_paths=32, expected_cases=1))
            with (output / "data" / "factkg_test.pickle").open("rb") as handle:
                subset = pickle.load(handle)
            self.assertEqual(list(subset), [claim])
            self.assertNotIn("Evidence", subset[claim])
            with (output / "candidates" / "swap_1.bin").open("rb") as handle:
                swapped = pickle.load(handle)
            self.assertEqual(swapped[claim]["walkable"], ranked[claim]["walkable"])
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["variants"], ["first5", "ranked5", "swap_1"])


if __name__ == "__main__":
    unittest.main()
