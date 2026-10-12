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
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faico_lite_retrieval import DeterministicPathRetriever, build_relation_sequences
from preprocess import prepare_input
import preprocess


class FaicoLiteRetrievalTest(unittest.TestCase):
    def test_round_robin_reaches_later_connected_branch_with_same_budget(self):
        kg = {"A": {"wide": [f"W{i}" for i in range(20)], "target": ["Z"]}}
        retriever = DeterministicPathRetriever(kg)
        paths = {"A": [["wide"], ["target"]]}
        dfs, dfs_diagnostics = retriever.search(
            ["A", "Z"], paths, store_max_paths=2, max_expanded_states=4
        )
        balanced, balanced_diagnostics = retriever.search(
            ["A", "Z"], paths, store_max_paths=2,
            max_expanded_states=4, search_schedule="round_robin"
        )
        self.assertEqual(dfs["connected"], [])
        self.assertEqual(balanced["connected"], [["A", "target", "Z"]])
        self.assertEqual(dfs_diagnostics["expanded_states"], 4)
        self.assertEqual(balanced_diagnostics["expanded_states"], 4)
        self.assertEqual(balanced_diagnostics["expansion_limit_reached"], 1)
        with self.assertRaises(ValueError):
            retriever.search(["A", "Z"], paths, search_schedule="invalid")

    def test_round_robin_uncapped_preserves_full_candidate_set(self):
        kg = {
            "A": {"r": ["B", "C"], "t": ["Z"]},
            "B": {"s": ["Z"]},
            "C": {"s": ["Z"]},
        }
        retriever = DeterministicPathRetriever(kg)
        paths = {"A": [["r", "s"], ["t"]]}
        dfs, _ = retriever.search(["A", "Z"], paths)
        balanced, _ = retriever.search(["A", "Z"], paths, search_schedule="round_robin")
        repeat, _ = retriever.search(["A", "Z"], paths, search_schedule="round_robin")
        for group in ("connected", "walkable"):
            self.assertEqual(
                {tuple(path) for path in dfs[group]},
                {tuple(path) for path in balanced[group]},
            )
        self.assertEqual(balanced, repeat)

    def test_test_candidates_resume_after_interruption(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            data_dir = root / "data"
            data_dir.mkdir()
            output_dir = root / "candidates"
            kg_path = root / "kg.pickle"
            relations_path = root / "relations.json"
            hops_path = root / "hops.json"
            claims = ["first claim", "second claim"]
            with kg_path.open("wb") as handle:
                pickle.dump({"A": {"r": ["B"]}}, handle)
            with (data_dir / "factkg_test.pickle").open("wb") as handle:
                pickle.dump({
                    claim: {"Entity_set": ["A", "B"], "Label": [True], "types": ["num1"]}
                    for claim in claims
                }, handle)
            relations_path.write_text(json.dumps({
                "claims": {str(i): claim for i, claim in enumerate(claims)},
                "output": {str(i): ["r"] for i in range(len(claims))},
            }), encoding="utf-8")
            hops_path.write_text(json.dumps({
                "claims": {str(i): claim for i, claim in enumerate(claims)},
                "predict": {str(i): 1 for i in range(len(claims))},
            }), encoding="utf-8")
            kwargs = dict(
                data_path=str(data_dir), kg_path=str(kg_path), n_candid="1",
                retrieval_mode="faico_lite", output_dir=str(output_dir),
                run_name="resume", test_only_candidates=True, resume_test=True,
                max_expanded_states=50,
                relation_prediction_path=str(relations_path),
                hop_prediction_path=str(hops_path),
            )
            original = preprocess._retrieve_faico_lite
            calls = []

            def interrupted(*args, **options):
                calls.append(1)
                if len(calls) == 2:
                    raise RuntimeError("simulated interruption")
                return original(*args, **options)

            with mock.patch.object(preprocess, "_retrieve_faico_lite", side_effect=interrupted):
                with self.assertRaisesRegex(RuntimeError, "simulated interruption"):
                    prepare_input(**kwargs)
            self.assertTrue((output_dir / "progress_resume.sqlite3").is_file())
            self.assertFalse((output_dir / "test_candid_paths_top1_resume.bin").exists())

            resumed_calls = []

            def counted(*args, **options):
                resumed_calls.append(1)
                return original(*args, **options)

            with mock.patch.object(preprocess, "_retrieve_faico_lite", side_effect=counted):
                outputs = prepare_input(**kwargs)
            self.assertEqual(len(resumed_calls), 1)
            with Path(outputs["test"]).open("rb") as handle:
                resumed_candidates = pickle.load(handle)
                self.assertEqual(list(resumed_candidates), claims)
            plain_outputs = prepare_input(**{
                **kwargs,
                "output_dir": str(root / "plain"),
                "run_name": "plain",
                "resume_test": False,
            })
            with Path(plain_outputs["test"]).open("rb") as handle:
                self.assertEqual(resumed_candidates, pickle.load(handle))
            with Path(outputs["report"]).open(encoding="utf-8") as handle:
                report = json.load(handle)
            self.assertEqual(report["splits"]["test"]["resumed_claims"], 1)
            self.assertEqual(len(report["splits"]["test"]["claim_diagnostics"]), 2)
            with self.assertRaisesRegex(ValueError, "differ"):
                prepare_input(**{**kwargs, "max_expanded_states": 51})

            limited_kwargs = {
                **kwargs,
                "output_dir": str(root / "limited"),
                "run_name": "limited",
                "max_expanded_states": 1,
            }
            first_outputs = prepare_input(**limited_kwargs)
            with Path(first_outputs["report"]).open(encoding="utf-8") as handle:
                first_report = json.load(handle)
            self.assertEqual(
                first_report["splits"]["test"]["expansion_limited_claims"], claims
            )
            retry_outputs = prepare_input(**{**limited_kwargs, "retry_limited_at": 50})
            with Path(retry_outputs["report"]).open(encoding="utf-8") as handle:
                retry_report = json.load(handle)
            self.assertEqual(retry_report["splits"]["test"]["retried_claims"], 2)
            self.assertEqual(retry_report["splits"]["test"]["expansion_limited_claims"], [])
            with Path(retry_outputs["test"]).open("rb") as handle:
                retried_candidates = pickle.load(handle)
            self.assertIn(["A", "r", "B"], retried_candidates[claims[0]]["connected"])
            final_outputs = prepare_input(**{**limited_kwargs, "retry_limited_at": 50})
            with Path(final_outputs["report"]).open(encoding="utf-8") as handle:
                final_report = json.load(handle)
            self.assertEqual(final_report["splits"]["test"]["retried_claims"], 0)

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

    def test_store_limit_matches_classifier_top_k_order(self):
        # r1/r3 la walkable va duyet truoc r2, nhung baseline.py luon xep
        # connected truoc. Candidate da gioi han phai van giong full[:K].
        kg = {
            "A": {"r1": ["W1"], "r2": ["Z"], "r3": ["W2"]},
        }
        retriever = DeterministicPathRetriever(kg)
        relation_paths = {"A": [["r1"], ["r2"], ["r3"]]}
        full_groups, _ = retriever.search(["A", "Z"], relation_paths)
        limited_groups, diagnostics = retriever.search(
            ["A", "Z"],
            relation_paths,
            store_max_paths=2,
        )

        self.assertEqual(
            limited_groups["connected"] + limited_groups["walkable"],
            (full_groups["connected"] + full_groups["walkable"])[:2],
        )
        self.assertEqual(diagnostics["total_paths"], 2)

    def test_store_limit_stops_after_top_connected_paths(self):
        kg = {
            "A": {"r1": ["Z"], "r2": ["Y"], "r3": ["X"]},
        }
        retriever = DeterministicPathRetriever(kg)
        relation_paths = {"A": [["r1"], ["r2"], ["r3"]]}
        full_groups, _ = retriever.search(["A", "Z", "Y", "X"], relation_paths)
        limited_groups, diagnostics = retriever.search(
            ["A", "Z", "Y", "X"],
            relation_paths,
            store_max_paths=2,
        )

        self.assertEqual(limited_groups["connected"], full_groups["connected"][:2])
        self.assertEqual(limited_groups["walkable"], [])
        self.assertEqual(diagnostics["search_stopped_after_connected_limit"], 1)

    def test_expansion_limit_marks_incomplete_claim(self):
        kg = {
            "A": {"r": ["C", "B"]},
            "B": {"s": ["Z"]},
            "C": {"s": ["Z"]},
        }
        retriever = DeterministicPathRetriever(kg)
        paths = {"A": [["r", "s"]]}
        full, _ = retriever.search(["A", "Z"], paths)
        bounded, diagnostics = retriever.search(
            ["A", "Z"], paths, max_expanded_states=3
        )

        self.assertEqual(len(full["connected"]), 2)
        self.assertEqual(bounded["connected"], full["connected"][:1])
        self.assertEqual(diagnostics["expanded_states"], 3)
        self.assertEqual(diagnostics["expansion_limit_reached"], 1)
        with self.assertRaises(ValueError):
            retriever.search(["A", "Z"], paths, max_expanded_states=0)

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

            test_only_dir = output_dir / "r2"
            test_only_outputs = prepare_input(
                data_path=str(data_dir),
                kg_path=str(kg_path),
                n_candid="2",
                retrieval_mode="faico_lite",
                output_dir=str(test_only_dir),
                run_name="r2",
                include_shorter_paths=True,
                test_only_candidates=True,
                relation_prediction_path=str(relation_prediction_path),
                hop_prediction_path=str(hop_prediction_path),
            )
            self.assertTrue(Path(test_only_outputs["test"]).is_file())
            self.assertFalse(Path(test_only_outputs["train"]).exists())
            self.assertFalse(Path(test_only_outputs["dev"]).exists())

            bounded_outputs = prepare_input(
                data_path=str(data_dir),
                kg_path=str(kg_path),
                n_candid="2",
                retrieval_mode="faico_lite",
                output_dir=str(output_dir / "bounded"),
                run_name="bounded",
                test_only_candidates=True,
                max_expanded_states=2,
                relation_prediction_path=str(relation_prediction_path),
                hop_prediction_path=str(hop_prediction_path),
            )
            with Path(bounded_outputs["report"]).open(encoding="utf-8") as handle:
                bounded_report = json.load(handle)
            self.assertEqual(
                bounded_report["splits"]["test"]["expansion_limited_claims"],
                [test_claim],
            )
            self.assertEqual(
                bounded_report["splits"]["test"]["expansion_limit_reached"], 1
            )

            round_robin_outputs = prepare_input(
                data_path=str(data_dir),
                kg_path=str(kg_path),
                n_candid="2",
                retrieval_mode="faico_lite",
                output_dir=str(output_dir / "round_robin"),
                run_name="round_robin",
                test_only_candidates=True,
                max_expanded_states=2,
                search_schedule="round_robin",
                relation_prediction_path=str(relation_prediction_path),
                hop_prediction_path=str(hop_prediction_path),
            )
            with Path(round_robin_outputs["report"]).open(encoding="utf-8") as handle:
                round_robin_report = json.load(handle)
            self.assertEqual(round_robin_report["config"]["search_schedule"], "round_robin")
            with Path(round_robin_outputs["test"]).open("rb") as handle:
                self.assertEqual(list(pickle.load(handle)), [test_claim])

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
