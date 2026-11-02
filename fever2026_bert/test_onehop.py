"""CPU-only checks; no FACTKG dataset or pretrained model download required."""

import json
import pickle
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from prepare import linearize, main, one_hop_triples, prepare_split
from train_eval import grouped_metrics, reasoning_group


class OneHopTest(unittest.TestCase):
    def test_keeps_every_tail_and_inverse_edge(self):
        kg = {"A": {"r": ["C", "B"], "~s": ["D"]}}
        self.assertEqual(one_hop_triples(kg, ["A"]), [
            ("A", "r", "B"), ("A", "r", "C"), ("A", "~s", "D")
        ])

    def test_preparation_does_not_use_gold_evidence(self):
        claim = "A reaches B"
        data = {claim: {"Entity_set": ["A"], "Label": [True],
                        "types": ["num1"], "Evidence": {"A": [["wrong"]]}}}
        records = prepare_split(data, {"A": {"r": ["B"]}})
        self.assertEqual(records[0]["triple_count"], 1)
        self.assertIn("A r B", records[0]["text"])
        self.assertNotIn("wrong", records[0]["text"])
        self.assertEqual(records[0]["text"], linearize(claim, [("A", "r", "B")]))

    def test_five_exclusive_reasoning_groups_match_factkg_priority(self):
        self.assertEqual(reasoning_group(["multi claim", "negation"]), "negation")
        rows = [
            {"types": ["num1"], "label": 1},
            {"types": ["multi hop"], "label": 0},
            {"types": ["multi claim", "substitution"], "label": 0},
            {"types": ["existence"], "label": 1},
            {"types": ["negation"], "label": 0},
        ]
        metrics = grouped_metrics(rows, [1, 1, 0, 1, 0])
        self.assertEqual(sum(group["n"] for group in metrics.values()), 5)
        self.assertEqual(metrics["multi-hop"]["accuracy"], 0.0)

    def test_prepare_cli_writes_three_splits(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data_dir = root / "data"
            data_dir.mkdir()
            for split in ("train", "dev", "test"):
                with (data_dir / f"factkg_{split}.pickle").open("wb") as handle:
                    pickle.dump({"A reaches B": {"Entity_set": ["A"], "Label": [True],
                                                  "types": ["num1"]}}, handle)
            kg_path = root / "kg.pickle"
            with kg_path.open("wb") as handle:
                pickle.dump({"A": {"r": ["B", "C"]}}, handle)
            output = root / "out"
            argv = ["prepare.py", "--data-dir", str(data_dir),
                    "--kg-path", str(kg_path), "--output-dir", str(output)]
            with patch.object(sys, "argv", argv):
                main()
            report = json.loads((output / "prepare_report.json").read_text())
            self.assertEqual(report["splits"]["test"]["claims"], 1)
            self.assertEqual(report["splits"]["test"]["mean_triples"], 2)


if __name__ == "__main__":
    unittest.main()
