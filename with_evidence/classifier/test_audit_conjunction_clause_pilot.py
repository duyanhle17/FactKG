"""Small checks for the dev-only clause coverage diagnostic."""

import json
import pickle
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_conjunction_clause_pilot import (
    audit_case, clause_supported, label_of, main, render_markdown,
    strict_and_counterfactual, visible_paths,
)


class ClausePilotTest(unittest.TestCase):
    def test_exact_path_support_and_connected_first_limit(self):
        row = {"connected": [["A", "r", "B"]],
               "walkable": [["A", "s", "C"], ["A", "t", "D"]]}
        self.assertEqual(visible_paths(row, 2), row["connected"] + row["walkable"][:1])
        clause = {"name": "A to B", "support_any": [
            ["B", "~r", "A"], ["A", "r", "B"]]}
        self.assertTrue(clause_supported(clause, visible_paths(row, 2)))
        self.assertFalse(clause_supported(
            {"name": "A to D", "support_any": [["A", "t", "D"]]},
            visible_paths(row, 2)))

    def test_pilot_keeps_unobserved_distinct_from_refuted(self):
        case = {"claim": "A reaches B and D", "group": "partial_false",
                "clauses": [
                    {"name": "A to B", "support_any": [["A", "r", "B"]]},
                    {"name": "A to D", "support_any": [["A", "t", "D"]]},
                ]}
        raw = {"connected": [["A", "r", "B"]],
               "walkable": [["A", "s", "C"], ["A", "t", "D"]]}
        first = {"connected": raw["connected"], "walkable": raw["walkable"][:1]}
        ranked = {"connected": raw["connected"], "walkable": raw["walkable"][1:]}
        result = audit_case(case, raw, first, ranked, 1, 1, 2)
        self.assertEqual(result["coverage"],
                         {"stored_r3": 1, "first5": 1, "ranked5": 2})
        self.assertEqual(result["strict_gate_first5"], 0)
        self.assertEqual(result["strict_gate_ranked5"], 1)
        result["gold_label"] = 0
        report = render_markdown([result], 2)
        self.assertIn("thiếu path ≠ False", report)

    def test_strict_gate_is_a_counterfactual_not_a_truth_test(self):
        self.assertEqual(strict_and_counterfactual(1, False), 0)
        self.assertEqual(strict_and_counterfactual(1, True), 1)
        self.assertEqual(strict_and_counterfactual(0, True), 0)
        self.assertEqual(label_of({"Label": [False]}), 0)
        with self.assertRaises(ValueError):
            label_of({"Label": [False, True]})

    def test_cli_reads_original_dev_and_writes_new_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            claim = "A reaches B"
            data = {claim: {"Label": [False]}}
            gold = {claim: {"Label": [False], "Evidence": {"A": [["r"]]}}}
            candidates = {claim: {"connected": [["A", "r", "B"]],
                                  "walkable": []}}
            prediction = {"label": [0], "reasoning_type": [2],
                          "prediction": [1]}
            files = {"data": data, "gold_dev": gold,
                     "raw_candidates": candidates,
                     "first_candidates": candidates,
                     "ranked_candidates": candidates,
                     "first_prediction": prediction,
                     "ranked_prediction": prediction}
            for name, obj in files.items():
                with (root / f"{name}.bin").open("wb") as handle:
                    pickle.dump(obj, handle)
            spec = {"cases": [{"claim": claim, "group": "label_review",
                               "clauses": [{"name": "A reaches B",
                                            "support_any": [["A", "r", "B"]]}]}]}
            (root / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
            (root / "report.json").write_text(json.dumps({"splits": {"test": {
                "expansion_limited_claims": []}}}), encoding="utf-8")
            args = ["audit_conjunction_clause_pilot.py", "--spec", str(root / "spec.json")]
            for name in files:
                args.extend((f"--{name}", str(root / f"{name}.bin")))
            args.extend(("--report", str(root / "report.json"),
                         "--output", str(root / "pilot.md")))
            with patch.object(sys, "argv", args):
                main()
            text = (root / "pilot.md").read_text(encoding="utf-8")
            self.assertIn("A reaches B", text)
            self.assertIn('"A": [', text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
