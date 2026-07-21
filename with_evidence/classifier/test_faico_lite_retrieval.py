"""Các kiểm tra KG nhỏ cho Faico-Lite, không cần dataset hay GPU thật.

File này chỉ dùng khi phát triển/kiểm tra code. Nó không được gọi trong lúc
train E2 trên máy SSH.
"""

import sys
import unittest
import json
import pickle
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faico_lite_retrieval import DeterministicPathRetriever, build_relation_sequences
from preprocess import prepare_input


class FaicoLiteRetrievalTest(unittest.TestCase):
    def test_keeps_two_paths_with_the_same_endpoint(self):
        # Hai chain cùng tới Z đều phải giữ: E2 có thể đánh giá chúng khác nhau.
        kg = {
            "A": {"r1": ["B"], "r3": ["C"]},
            "B": {"r2": ["Z"]},
            "C": {"r4": ["Z"]},
        }
        retriever = DeterministicPathRetriever(kg)
        groups, diagnostics = retriever.search(
            ["A", "Z"],
            {"A": [["r1", "r2"], ["r3", "r4"]]},
        )

        self.assertEqual(diagnostics["connected_paths"], 2)
        self.assertEqual(
            groups["connected"],
            [["A", "r1", "B", "r2", "Z"], ["A", "r3", "C", "r4", "Z"]],
        )

    def test_keeps_all_final_tails_in_a_stable_order(self):
        # KG cố tình để tail C trước B; retriever mới vẫn phải ra B rồi C ổn định.
        kg = {"A": {"r": ["C", "B"]}}
        retriever = DeterministicPathRetriever(kg)

        first_groups, _ = retriever.search(["A"], {"A": [["r"]]})
        second_groups, _ = retriever.search(["A"], {"A": [["r"]]})

        self.assertEqual(first_groups, second_groups)
        self.assertEqual(
            first_groups["walkable"],
            [["A", "r", "B"], ["A", "r", "C"]],
        )

    def test_relation_budget_one_matches_no_repeat_constraint(self):
        # k=1 tái lập ràng buộc permutations cũ: không lặp relation.
        sequences = build_relation_sequences(["r1", "r2"], hop=3, relation_budget=1)
        self.assertEqual(sequences, [])

        sequences = build_relation_sequences(["r1", "r2", "r3"], hop=3, relation_budget=1)
        self.assertEqual(len(sequences), 6)
        self.assertNotIn(("r1", "r2", "r1"), sequences)

    def test_relation_budget_two_allows_a_repeated_relation(self):
        # R3 chỉ nới đúng một điều: relation được lặp tối đa hai lần.
        sequences = build_relation_sequences(["r1", "r2"], hop=3, relation_budget=2)
        self.assertIn(("r1", "r2", "r1"), sequences)
        self.assertNotIn(("r1", "r1", "r1"), sequences)

    def test_shorter_path_option_includes_every_length(self):
        # R2 phải thêm đủ path 1-hop, 2-hop và 3-hop khi H=3.
        sequences = build_relation_sequences(
            ["r1", "r2", "r3"],
            hop=3,
            include_shorter_paths=True,
            relation_budget=1,
        )
        self.assertEqual(len(sequences), 15)
        self.assertIn(("r1",), sequences)
        self.assertIn(("r1", "r2"), sequences)
        self.assertIn(("r1", "r2", "r3"), sequences)

    def test_dominance_audit_does_not_remove_paths(self):
        # Chế độ audit không được làm mất path; chỉ raw prune trong R4 mới thử cắt.
        kg = {"A": {"r1": ["B"], "r2": ["C"]}}
        retriever = DeterministicPathRetriever(kg, dominance_mode="audit")
        groups, _ = retriever.search(
            ["A"],
            {"A": [["r1"], ["r2"]]},
            allowed_relations=["r1", "r2"],
        )
        self.assertEqual(len(groups["walkable"]), 2)

    def test_preprocess_writes_separate_faico_lite_artifacts(self):
        # Kiểm tra tên artifact R1/R4 tách biệt, tránh ghi đè train_candid_paths.bin cũ.
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            data_dir = root / "data"
            output_dir = root / "artifacts"
            data_dir.mkdir()
            kg_path = root / "kg.pickle"
            relation_prediction_path = root / "relations.json"
            hop_prediction_path = root / "hops.json"

            kg = {
                "A": {"r1": ["B"], "r2": ["C"]},
                "B": {"r2": ["Z"]},
                "C": {"r1": ["Z"]},
            }
            with kg_path.open("wb") as handle:
                pickle.dump(kg, handle)

            for split in ("train", "dev"):
                database = {
                    f"{split} claim": {
                        "Entity_set": ["A", "B"],
                        "Evidence": {"A": [["r1"]]},
                        "Label": [True],
                        "types": ["num1"],
                    }
                }
                with (data_dir / f"factkg_{split}.pickle").open("wb") as handle:
                    pickle.dump(database, handle)

            test_claim = "test claim"
            with (data_dir / "factkg_test.pickle").open("wb") as handle:
                pickle.dump(
                    {test_claim: {"Entity_set": ["A", "Z"], "Label": [True], "types": ["multi hop"]}},
                    handle,
                )
            relation_prediction_path.write_text(
                json.dumps({"claims": {"0": test_claim}, "output": {"0": ["r1", "r2"]}}),
                encoding="utf-8",
            )
            hop_prediction_path.write_text(
                json.dumps({"claims": {"0": test_claim}, "predict": {"0": 2}}),
                encoding="utf-8",
            )

            outputs = prepare_input(
                data_path=str(data_dir),
                kg_path=str(kg_path),
                n_candid="2",
                retrieval_mode="faico_lite",
                output_dir=str(output_dir),
                run_name="r1",
                relation_prediction_path=str(relation_prediction_path),
                hop_prediction_path=str(hop_prediction_path),
            )

            for key in ("train", "dev", "test", "report", "manifest"):
                self.assertTrue(Path(outputs[key]).is_file())
            with Path(outputs["test"]).open("rb") as handle:
                test_candidates = pickle.load(handle)
            self.assertIn(["A", "r1", "B", "r2", "Z"], test_candidates[test_claim]["connected"])
            self.assertFalse((output_dir / "train_candid_paths.bin").exists())

            audit_outputs = prepare_input(
                data_path=str(data_dir),
                kg_path=str(kg_path),
                n_candid="2",
                retrieval_mode="faico_lite",
                output_dir=str(output_dir / "r4"),
                run_name="r4",
                dominance_audit=True,
                relation_prediction_path=str(relation_prediction_path),
                hop_prediction_path=str(hop_prediction_path),
            )
            with Path(audit_outputs["report"]).open(encoding="utf-8") as handle:
                audit_report = json.load(handle)
            self.assertIn("r4_audit_candidate_set_equal", audit_report["splits"]["test"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
