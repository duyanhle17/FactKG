"""Sinh candidate-path artifact cho FactKG classifier.

Class ``KG`` cũ được giữ nguyên để baseline vẫn chạy được. Chế độ
``faico_lite`` chỉ thêm đường đi mới cho R1--R4: duyệt path xác định, ghi mỗi
lần chạy vào thư mục riêng và không ghi đè candidate legacy.
"""

import json
import os
import pickle as pkl
import hashlib
import sqlite3
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


class _TestCandidateProgress:
    """Commit one completed claim at a time; never persist a half-searched claim."""

    def __init__(self, path: str, identity: Mapping[str, object]) -> None:
        self.path = path
        self.connection = sqlite3.connect(path)
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS claims ("
            "claim TEXT PRIMARY KEY, position INTEGER NOT NULL, "
            "groups BLOB NOT NULL, diagnostics TEXT NOT NULL, "
            "elapsed_ms INTEGER NOT NULL, cap_used INTEGER)"
        )
        expected = json.dumps(identity, sort_keys=True, ensure_ascii=False)
        row = self.connection.execute(
            "SELECT value FROM metadata WHERE key = 'identity'"
        ).fetchone()
        if row is None:
            with self.connection:
                self.connection.execute(
                    "INSERT INTO metadata (key, value) VALUES ('identity', ?)", (expected,)
                )
        elif row[0] != expected:
            self.connection.close()
            raise ValueError(
                "Progress database inputs/config/code differ from this run. "
                "Use the original settings or choose a new output_dir/run_name."
            )

    def load(self, claims: list) -> Dict[str, tuple]:
        positions = {claim: i for i, claim in enumerate(claims)}
        saved = {}
        for claim, position, groups, diagnostics, elapsed_ms, cap_used in self.connection.execute(
            "SELECT claim, position, groups, diagnostics, elapsed_ms, cap_used FROM claims"
        ):
            if claim not in positions or positions[claim] != position:
                raise ValueError(f"Progress database contains an unexpected claim: {claim!r}")
            saved[claim] = (pkl.loads(groups), json.loads(diagnostics), elapsed_ms, cap_used)
        return saved

    def save(self, claim: str, position: int, groups: object,
             diagnostics: Mapping[str, int], elapsed_ms: int, cap_used: int) -> None:
        with self.connection:
            self.connection.execute(
                "INSERT OR REPLACE INTO claims "
                "(claim, position, groups, diagnostics, elapsed_ms, cap_used) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (claim, position, sqlite3.Binary(pkl.dumps(groups)),
                 json.dumps(dict(diagnostics), sort_keys=True), elapsed_ms, cap_used),
            )

    def close(self) -> None:
        self.connection.close()


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
    store_max_paths=None,
    allowed_relations=None,
    max_expanded_states=None,
    search_schedule="dfs",
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
        store_max_paths=store_max_paths,
        max_expanded_states=max_expanded_states,
        search_schedule=search_schedule,
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


def _write_split_atomic(path: str, candidates: Mapping[str, object]) -> None:
    temporary = f"{path}.partial"
    with open(temporary, "wb") as handle:
        pkl.dump(dict(candidates), handle)
    os.replace(temporary, path)


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
    store_max_paths=None,
    max_expanded_states=None,
    test_only_candidates=False,
    relation_prediction_path=None,
    hop_prediction_path=None,
    overwrite=False,
    resume_test=False,
    retry_limited_at=None,
    search_schedule="dfs",
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
    if store_max_paths is not None and store_max_paths < 1:
        raise ValueError("store_max_paths must be at least 1 when provided")
    if max_expanded_states is not None and max_expanded_states < 1:
        raise ValueError("max_expanded_states must be at least 1 when provided")
    if search_schedule not in {"dfs", "round_robin"}:
        raise ValueError("search_schedule must be 'dfs' or 'round_robin'")
    if search_schedule == "round_robin" and (
        retrieval_mode != "faico_lite" or not test_only_candidates
        or dominance_audit or max_expanded_states is None
    ):
        raise ValueError(
            "round_robin requires bounded test-only Faico-Lite without dominance_audit"
        )
    if max_expanded_states is not None and (
        retrieval_mode != "faico_lite" or not test_only_candidates or dominance_audit
    ):
        raise ValueError(
            "max_expanded_states is only supported for predicted test-style "
            "Faico-Lite candidates without dominance_audit"
        )
    if resume_test and (not test_only_candidates or retrieval_mode != "faico_lite"):
        raise ValueError("resume_test requires test-only Faico-Lite candidates")
    if resume_test and overwrite:
        raise ValueError("resume_test and overwrite cannot be combined")
    if retry_limited_at is not None and (
        not resume_test or max_expanded_states is None
        or retry_limited_at <= max_expanded_states
    ):
        raise ValueError(
            "retry_limited_at requires resume_test and must exceed max_expanded_states"
        )
    if dominance_audit and store_max_paths is not None:
        raise ValueError(
            "store_max_paths cannot be combined with dominance_audit because R4 "
            "must compare complete candidate sets."
        )

    if relation_prediction_path is None:
        relation_prediction_path = (
            f"../retrieve/model/relation_predict/test_relations_top{n_candid}.json"
        )
    if hop_prediction_path is None:
        hop_prediction_path = "../retrieve/model/hop_predict/predictions_hop.json"

    outputs = _candidate_output_paths(output_dir, n_candid, run_name)
    progress_path = str(Path(output_dir) / f"progress_{run_name}.sqlite3")
    candidate_splits = ("test",) if test_only_candidates else ("train", "dev", "test")
    if os.path.exists(progress_path) and not resume_test:
        raise FileExistsError(
            f"A resumable run exists at {progress_path}; use --resume_test "
            "with its original settings or choose a new output_dir/run_name"
        )
    if retrieval_mode == "faico_lite" and not overwrite:
        # Không vô tình ghi đè một thí nghiệm đã chạy xong. Muốn chạy lại cùng
        # tên thì người dùng phải chủ động truyền --overwrite ở script CLI.
        existing_outputs = [
            outputs[split] for split in candidate_splits if os.path.exists(outputs[split])
        ]
        existing_outputs.extend(
            path for name, path in outputs.items()
            if name in {"report", "manifest"} and os.path.exists(path)
        )
        if existing_outputs and not (resume_test and os.path.exists(progress_path)):
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
            "store_max_paths": store_max_paths,
            "max_expanded_states": max_expanded_states,
            "test_only_candidates": bool(test_only_candidates),
            "resume_test": bool(resume_test),
            "retry_limited_at": retry_limited_at,
            "search_schedule": search_schedule,
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
            store_max_paths=store_max_paths,
        )

    for split in ("train", "dev"):
        if split not in candidate_splits:
            continue
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

    if "test" in candidate_splits:
        relation_predictions, hop_predictions = _load_test_predictions(
            relation_prediction_path,
            hop_prediction_path,
        )
        with open(os.path.join(data_path, "factkg_test.pickle"), "rb") as handle:
            test_database = pkl.load(handle)

        test_candidates = {}
        expansion_limited_claims = []
        claim_diagnostics = {}
        test_stats = _new_split_stats(report_max_paths)
        test_started = perf_counter()
        progress = None
        saved = {}
        if resume_test:
            code_paths = (Path(__file__), Path(__file__).with_name("faico_lite_retrieval.py"))
            identity = {
                "format": 1,
                "config": {
                    key: value for key, value in report["config"].items()
                    if key != "retry_limited_at"
                },
                "test_data": _file_fingerprint(os.path.join(data_path, "factkg_test.pickle")),
                "kg": _file_fingerprint(kg_path),
                "relations": _file_fingerprint(relation_prediction_path),
                "hops": _file_fingerprint(hop_prediction_path),
                "claim_order_sha256": hashlib.sha256(
                    pkl.dumps(list(test_database))
                ).hexdigest(),
                "code_sha256": {
                    path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in code_paths
                },
            }
            progress = _TestCandidateProgress(progress_path, identity)
            try:
                saved = progress.load(list(test_database))
            except BaseException:
                progress.close()
                raise
            print(f"Resuming test candidates: {len(saved)}/{len(test_database)} claims saved")
        report["config"]["progress_path"] = progress_path if resume_test else None
        retried_claims = 0
        try:
            for position, (claim, example) in enumerate(
                tqdm(test_database.items(), total=len(test_database), desc="test: candidates")
            ):
                previous = saved.get(claim)
                retry = (
                    previous is not None
                    and retry_limited_at is not None
                    and previous[1].get("expansion_limit_reached")
                    and (previous[3] is None or previous[3] < retry_limited_at)
                )
                if previous is not None and not retry:
                    groups, diagnostics, elapsed_ms, cap_used = previous
                else:
                    cap_used = retry_limited_at if retry else max_expanded_states
                    claim_started = perf_counter()
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
                        # Test khong co Evidence gold. R1/R2/R3 khac nhau chinh o day:
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
                            store_max_paths=store_max_paths,
                            allowed_relations=predicted_relations,
                            max_expanded_states=cap_used,
                            search_schedule=search_schedule,
                        )
                        diagnostics["generated_relation_sequences"] = len(relation_paths)
                    elapsed_ms = max(0, round((perf_counter() - claim_started) * 1000))
                    if progress is not None:
                        progress.save(claim, position, groups, diagnostics, elapsed_ms, cap_used)
                    if retry:
                        retried_claims += 1
                if diagnostics.get("expansion_limit_reached"):
                    expansion_limited_claims.append(claim)
                test_candidates[claim] = groups
                claim_diagnostics[claim] = {
                    **diagnostics,
                    "elapsed_milliseconds": elapsed_ms,
                    "max_expanded_states_used": cap_used,
                }
                _record_split_stats(test_stats, diagnostics, report_max_paths)
        finally:
            if progress is not None:
                progress.close()

        if list(test_candidates) != list(test_database):
            raise RuntimeError("test: candidate count/order does not match data")
        if resume_test:
            _write_split_atomic(outputs["test"], test_candidates)
        else:
            _write_split(outputs["test"], test_candidates)
        test_stats["elapsed_seconds"] = round(perf_counter() - test_started, 3)
        test_stats["resumed_claims"] = len(saved)
        test_stats["retried_claims"] = retried_claims
        report["splits"]["test"] = dict(test_stats)
        report["splits"]["test"]["expansion_limited_claims"] = expansion_limited_claims
        if resume_test:
            report["splits"]["test"]["claim_diagnostics"] = claim_diagnostics

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
            if name in candidate_splits
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
