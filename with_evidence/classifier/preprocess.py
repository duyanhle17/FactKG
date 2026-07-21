"""Sinh candidate-path artifact cho FactKG classifier.

Class ``KG`` cũ được giữ nguyên để baseline vẫn chạy được. Chế độ
``faico_lite`` chỉ thêm đường đi mới cho R1--R4: duyệt path xác định, ghi mỗi
lần chạy vào thư mục riêng và không ghi đè candidate legacy.
"""

import json
import os
import pickle as pkl
from collections import Counter
from datetime import datetime, timezone
from itertools import chain, permutations
from pathlib import Path
from random import choice
from time import perf_counter
from typing import Dict, Iterable, Mapping, Tuple

from tqdm.auto import tqdm

from faico_lite_retrieval import (
    DeterministicPathRetriever,
    build_relation_sequences,
    canonical_path_set,
)

# Phân tách có chủ đích:
# - File này: đọc train/dev/test, gọi retriever, rồi ghi các file .bin.
# - faico_lite_retrieval.py: chỉ chứa thuật toán duyệt graph và unit test.
# Nhờ vậy preprocess.py không trở thành một file vừa xử lý dữ liệu vừa chứa
# toàn bộ DFS/k-BET khó kiểm tra.


class KG:
    """Traversal FactKG nguyên gốc, giữ lại để baseline legacy vẫn tái lập được."""

    def __init__(self, kg):
        self.kg = kg

    def search(self, ents, rels):
        connected = []
        walkable = []
        seen = {}

        for entity in ents:
            if entity in rels:
                for path in rels[entity]:
                    leaf = ents[:]
                    leaf.remove(entity)
                    result = self.walk(start=entity, path=path, ends=leaf)
                    if result != (None, None):
                        if result[1] is not None:
                            query = str(sorted([result[1][0], result[1][-1]]))
                            if query not in seen:
                                connected_path = result[1][:1] + list(
                                    chain(*[[relation, tail] for relation, tail in zip(path, result[1][1:])])
                                )
                                connected.append(connected_path)
                                seen[query] = None
                        if result[0][0] != result[0][-1]:
                            query = str(sorted([result[0][0], result[0][-1]]))
                            if query not in seen:
                                walkable_path = result[0][:1] + list(
                                    chain(*[[relation, tail] for relation, tail in zip(path, result[0][1:])])
                                )
                                walkable.append(walkable_path)
                                seen[query] = None

        return {"connected": connected, "walkable": walkable}

    def walk(self, start, path, ends=None):
        branches = [[start]]
        for relation in path:
            updated_branches = []
            for branch in branches:
                head = branch[-1]
                tails = self.get_tail(head, relation)
                if relation == path[-1] and tails:
                    random_branch = branch + [choice(list(tails.keys()))]
                    for entity in ends:
                        if entity in tails:
                            return random_branch, branch + [entity]
                    return random_branch, None
                if tails:
                    for tail in tails:
                        updated_branches.append(branch + [tail])
            if len(updated_branches) <= len(branches):
                return None, None
            branches = updated_branches

    def get_tail(self, head, relation):
        if head in self.kg and relation in self.kg[head]:
            return {tail: None for tail in self.kg[head][relation]}
        return {}


def _candidate_output_paths(output_dir: str, n_candid: str, run_name: str) -> Dict[str, str]:
    """Tạo tên file riêng cho từng R để không đè train/dev/test candidate cũ."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    suffix = f"_{run_name}" if run_name else ""
    return {
        "train": str(destination / f"train_candid_paths{suffix}.bin"),
        "dev": str(destination / f"dev_candid_paths{suffix}.bin"),
        "test": str(destination / f"test_candid_paths_top{n_candid}{suffix}.bin"),
        "report": str(destination / f"retrieval_report{suffix}.json"),
        "manifest": str(destination / f"manifest{suffix}.json"),
    }


def _file_fingerprint(path: str) -> Dict[str, object]:
    # Manifest chỉ lưu đường dẫn, kích thước và mốc sửa file. Không hash cả KG
    # vì KG DBpedia lớn, hash đầy đủ sẽ làm chậm bước chuẩn bị vô ích.
    resolved = os.path.abspath(path)
    if not os.path.exists(resolved):
        return {"path": resolved, "exists": False}
    stat = os.stat(resolved)
    return {
        "path": resolved,
        "exists": True,
        "size_bytes": stat.st_size,
        "modified_at_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }


def _new_split_stats(report_max_paths: int) -> Counter:
    return Counter({"claims": 0, "report_max_paths": report_max_paths})


def _record_split_stats(summary: Counter, diagnostics: Mapping[str, int], report_max_paths: int) -> None:
    # Candidate được lưu đầy đủ; con số 32 ở đây chỉ để báo trước E2 thực sự
    # nhìn thấy bao nhiêu path sau khi PairDataset lấy top-K.
    summary["claims"] += 1
    for key, value in diagnostics.items():
        summary[key] += int(value)
    total_paths = int(diagnostics.get("total_paths", 0))
    summary["paths_visible_to_model_at_report_limit"] += min(total_paths, report_max_paths)
    if total_paths > report_max_paths:
        summary["claims_exceeding_report_limit"] += 1
        summary["paths_after_report_limit"] += total_paths - report_max_paths


def _load_test_predictions(relation_prediction_path: str, hop_prediction_path: str) -> Tuple[Dict[str, list], Dict[str, int]]:
    """Đọc hai JSON predictor và đổi chúng thành dict theo nội dung claim."""
    with open(relation_prediction_path) as handle:
        relation_json = json.load(handle)
    with open(hop_prediction_path) as handle:
        hop_json = json.load(handle)

    relation_predictions = {
        relation_json["claims"][index]: relation_json["output"][index]
        for index in relation_json["claims"]
    }
    hop_predictions = {
        hop_json["claims"][index]: int(hop_json["predict"][index])
        for index in hop_json["claims"]
    }
    return relation_predictions, hop_predictions


def _same_grouped_path_set(left: Mapping[str, Iterable], right: Mapping[str, Iterable]) -> bool:
    # R4 không chỉ so set chung mà còn giữ riêng số path connected/walkable.
    return (
        canonical_path_set(left) == canonical_path_set(right)
        and len(left.get("connected", ())) == len(right.get("connected", ()))
        and len(left.get("walkable", ())) == len(right.get("walkable", ()))
    )


def _retrieve_faico_lite(
    kg,
    entities,
    relation_paths,
    relation_budget: int,
    dominance_audit: bool,
    allowed_relations=None,
):
    """Lấy full path; nếu bật R4 thì audit raw dominance của Faico.

    Giá trị trả về luôn là path *không bị dominance cắt*. Phần dominance chỉ
    chạy song song để report cho biết nếu copy Faico nguyên xi thì mất bao
    nhiêu serialized path.
    """
    full_retriever = DeterministicPathRetriever(kg, relation_budget=relation_budget)
    full_started = perf_counter()
    groups, diagnostics = full_retriever.search(
        entities,
        relation_paths,
        allowed_relations=allowed_relations if dominance_audit else None,
    )

    if not dominance_audit or allowed_relations is None:
        return groups, diagnostics

    diagnostics["r4_audit_full_milliseconds"] = round((perf_counter() - full_started) * 1000)

    # Raw dominance Faico chỉ chạy để so sánh. Không ghi output đã cắt thành
    # artifact train/dev/test vì nó có thể làm mất alternative path mà E2 cần.
    pruned_retriever = DeterministicPathRetriever(
        kg,
        relation_budget=relation_budget,
        dominance_mode="prune",
    )
    audit_started = perf_counter()
    pruned_groups, pruned_diagnostics = pruned_retriever.search(
        entities,
        relation_paths,
        allowed_relations=allowed_relations,
    )
    full_paths = canonical_path_set(groups)
    pruned_paths = canonical_path_set(pruned_groups)
    diagnostics["r4_audit_candidate_set_equal"] = int(_same_grouped_path_set(groups, pruned_groups))
    diagnostics["r4_audit_paths_removed_by_raw_dominance"] = len(full_paths - pruned_paths)
    diagnostics["r4_audit_paths_added_by_raw_dominance"] = len(pruned_paths - full_paths)
    diagnostics["r4_audit_pruned_expanded_states"] = int(pruned_diagnostics.get("expanded_states", 0))
    diagnostics["r4_audit_pruned_states"] = int(pruned_diagnostics.get("dominance_pruned_states", 0))
    diagnostics["r4_audit_pruned_milliseconds"] = round((perf_counter() - audit_started) * 1000)
    return groups, diagnostics


def _write_split(path: str, candidates: Mapping[str, object]) -> None:
    with open(path, "wb") as handle:
        pkl.dump(dict(candidates), handle)


def prepare_input(
    data_path,
    kg_path,
    n_candid="5",
    retrieval_mode="legacy",
    output_dir=".",
    run_name="",
    include_shorter_paths=False,
    relation_budget=1,
    dominance_audit=False,
    report_max_paths=32,
    relation_prediction_path=None,
    hop_prediction_path=None,
    overwrite=False,
):
    """Sinh artifact legacy hoặc Faico-Lite.

    ``legacy`` giữ nguyên tên file và hành vi cũ.
    ``faico_lite`` thực hiện R1--R3.
    ``dominance_audit=True`` thêm report R4 nhưng artifact ghi ra vẫn là full
    path chưa bị cắt, nên an toàn cho GEARLite.
    """
    n_candid = str(n_candid)
    retrieval_mode = str(retrieval_mode)
    if retrieval_mode not in {"legacy", "faico_lite"}:
        raise ValueError("retrieval_mode must be 'legacy' or 'faico_lite'")
    if retrieval_mode == "faico_lite" and not run_name:
        raise ValueError("Faico-Lite runs require a non-empty run_name to protect legacy artifacts.")
    if relation_budget < 1:
        raise ValueError("relation_budget must be at least 1")
    if report_max_paths < 1:
        raise ValueError("report_max_paths must be at least 1")

    if relation_prediction_path is None:
        relation_prediction_path = (
            f"../retrieve/model/relation_predict/test_relations_top{n_candid}.json"
        )
    if hop_prediction_path is None:
        hop_prediction_path = "../retrieve/model/hop_predict/predictions_hop.json"

    outputs = _candidate_output_paths(output_dir, n_candid, run_name)
    if retrieval_mode == "faico_lite" and not overwrite:
        # Không vô tình ghi đè một thí nghiệm đã chạy xong. Muốn chạy lại cùng
        # tên thì người dùng phải chủ động truyền --overwrite ở script CLI.
        existing_outputs = [
            path for path in outputs.values()
            if os.path.exists(path)
        ]
        if existing_outputs:
            raise FileExistsError(
                "Refusing to overwrite an existing Faico-Lite run. "
                "Choose a new --run_name/output_dir or pass overwrite=True. "
                f"Existing: {existing_outputs}"
            )
    with open(kg_path, "rb") as handle:
        raw_kg = pkl.load(handle)

    legacy_retriever = KG(raw_kg) if retrieval_mode == "legacy" else None
    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": {
            "retrieval_mode": retrieval_mode,
            "run_name": run_name,
            "n_candid": int(n_candid),
            "include_shorter_paths": bool(include_shorter_paths),
            "relation_budget": int(relation_budget),
            "dominance_audit": bool(dominance_audit),
            "report_max_paths": int(report_max_paths),
        },
        "splits": {},
    }

    def retrieve_gold(entities, evidence):
        if retrieval_mode == "legacy":
            return legacy_retriever.search(entities, evidence), {}
        # Train/dev dùng Evidence gold; R1 thay traversal nhưng không thay
        # relation/hop predictor ở hai split này.
        return _retrieve_faico_lite(
            raw_kg,
            entities,
            evidence,
            relation_budget=relation_budget,
            dominance_audit=False,
        )

    for split in ("train", "dev"):
        split_path = os.path.join(data_path, f"factkg_{split}.pickle")
        with open(split_path, "rb") as handle:
            database = pkl.load(handle)

        candidates = {}
        split_stats = _new_split_stats(report_max_paths)
        split_started = perf_counter()
        for claim, example in tqdm(database.items(), total=len(database), desc=f"{split}: candidates"):
            groups, diagnostics = retrieve_gold(example["Entity_set"], example["Evidence"])
            candidates[claim] = groups
            _record_split_stats(split_stats, diagnostics, report_max_paths)
        if len(candidates) != len(database):
            raise RuntimeError(f"{split}: candidate count does not match data count")
        _write_split(outputs[split], candidates)
        split_stats["elapsed_seconds"] = round(perf_counter() - split_started, 3)
        report["splits"][split] = dict(split_stats)

    relation_predictions, hop_predictions = _load_test_predictions(
        relation_prediction_path,
        hop_prediction_path,
    )
    with open(os.path.join(data_path, "factkg_test.pickle"), "rb") as handle:
        test_database = pkl.load(handle)

    test_candidates = {}
    test_stats = _new_split_stats(report_max_paths)
    test_started = perf_counter()
    for claim, example in tqdm(test_database.items(), total=len(test_database), desc="test: candidates"):
        if claim not in relation_predictions:
            raise KeyError(f"Test claim is missing from relation predictions: {claim!r}")
        if claim not in hop_predictions:
            raise KeyError(f"Test claim is missing from hop predictions: {claim!r}")

        predicted_relations = relation_predictions[claim]
        predicted_hop = hop_predictions[claim]
        if retrieval_mode == "legacy":
            relation_paths = list(permutations(predicted_relations, r=predicted_hop))
            relation_paths_by_entity = {
                entity: relation_paths for entity in example["Entity_set"]
            }
            groups = legacy_retriever.search(example["Entity_set"], relation_paths_by_entity)
            diagnostics = {}
        else:
            # Test không có Evidence gold. R1/R2/R3 khác nhau chính ở đây:
            # R1: exact H, k=1; R2: include_shorter_paths; R3: k=2.
            relation_paths = build_relation_sequences(
                predicted_relations,
                predicted_hop,
                include_shorter_paths=include_shorter_paths,
                relation_budget=relation_budget,
            )
            relation_paths_by_entity = {
                entity: relation_paths for entity in example["Entity_set"]
            }
            groups, diagnostics = _retrieve_faico_lite(
                raw_kg,
                example["Entity_set"],
                relation_paths_by_entity,
                relation_budget=relation_budget,
                dominance_audit=dominance_audit,
                allowed_relations=predicted_relations,
            )
            diagnostics["generated_relation_sequences"] = len(relation_paths)
        test_candidates[claim] = groups
        _record_split_stats(test_stats, diagnostics, report_max_paths)

    if len(test_candidates) != len(test_database):
        raise RuntimeError("test: candidate count does not match data count")
    _write_split(outputs["test"], test_candidates)
    test_stats["elapsed_seconds"] = round(perf_counter() - test_started, 3)
    report["splits"]["test"] = dict(test_stats)

    manifest = {
        "created_at_utc": report["created_at_utc"],
        "config": report["config"],
        "inputs": {
            "data_dir": _file_fingerprint(data_path),
            "kg": _file_fingerprint(kg_path),
            "relation_predictions": _file_fingerprint(relation_prediction_path),
            "hop_predictions": _file_fingerprint(hop_prediction_path),
        },
        "outputs": {
            name: _file_fingerprint(path)
            for name, path in outputs.items()
            if name in {"train", "dev", "test"}
        },
    }
    with open(outputs["report"], "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
    with open(outputs["manifest"], "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)

    print("Candidate artifacts written:")
    for split in ("train", "dev", "test"):
        print(f"  {split}: {outputs[split]}")
    print(f"  report: {outputs['report']}")
    print(f"  manifest: {outputs['manifest']}")
    return outputs
