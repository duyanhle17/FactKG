"""Step A: inspect Conjunction errors using saved V4 predictions and R3 paths.

This is a CPU-only, read-only audit of the experiment inputs. It does not
infer missing KG facts or decide whether a path proves a claim automatically.
"""

import argparse
import csv
import json
import pickle
import random
from collections import Counter
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test_data", type=Path, required=True)
    parser.add_argument("--candidate_path", type=Path, required=True)
    parser.add_argument("--prediction_path", type=Path, required=True)
    parser.add_argument("--relation_json", type=Path, required=True)
    parser.add_argument("--hop_json", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--max_paths", type=int, default=32)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max_per_entity_set", type=int, default=2)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.max_paths < 1 or args.max_per_entity_set < 1:
        parser.error("--max_paths and --max_per_entity_set must be positive")
    return args


def read_pickle(path):
    with path.open("rb") as handle:
        return pickle.load(handle)


def read_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def indexed_predictions(document, value_key):
    """Use the same indexed JSON layout as preprocess._load_test_predictions."""
    return {
        document["claims"][index]: document[value_key][index]
        for index in document["claims"]
    }


def as_list(values):
    return values.tolist() if hasattr(values, "tolist") else list(values)


def label_to_int(value):
    if isinstance(value, (list, tuple)):
        if len(value) != 1:
            raise ValueError(f"Expected one label, got {value!r}")
        value = value[0]
    return int(value)


def reasoning_type(types):
    # Match the precedence in baseline.py; some examples have several tags.
    for tag, type_id in (
        ("negation", 4), ("num1", 0), ("multi hop", 1),
        ("multi claim", 2), ("existence", 3),
    ):
        if tag in types:
            return type_id
    raise ValueError(f"Unknown FactKG reasoning type: {types!r}")


def path_groups(candidate):
    connected = candidate["connected"]
    walkable = candidate["walkable"]
    return [("connected", path) for path in connected] + [
        ("walkable", path) for path in walkable
    ]


def sample_diverse(indices, count, claims, database, rng, max_per_entity_set):
    """Cap repeated entity sets so paraphrases do not dominate the audit."""
    indices = list(indices)
    rng.shuffle(indices)
    selected = []
    seen_entity_sets = Counter()
    for index in indices:
        claim = claims[index]
        signature = tuple(sorted(map(str, database[claim].get("Entity_set", []))))
        if seen_entity_sets[signature] >= max_per_entity_set:
            continue
        selected.append(index)
        seen_entity_sets[signature] += 1
        if len(selected) == count:
            break
    return selected


def bucket_counts(indices, claims, candidates, max_paths):
    counts = [
        (len(candidates[claims[index]]["connected"]),
         len(candidates[claims[index]]["walkable"]))
        for index in indices
    ]
    return {
        "n": len(indices),
        "no_path": sum(c + w == 0 for c, w in counts),
        "no_connected": sum(c == 0 for c, _ in counts),
        "at_model_cap_in_artifact": sum(c + w == max_paths for c, w in counts),
        "above_model_cap_in_artifact": sum(c + w > max_paths for c, w in counts),
        "mean_paths_in_artifact": (
            sum(c + w for c, w in counts) / len(counts) if counts else 0.0
        ),
    }


def main():
    args = parse_args()
    for source in (
        args.test_data, args.candidate_path, args.prediction_path,
        args.relation_json, args.hop_json,
    ):
        if not source.is_file():
            raise FileNotFoundError(source)

    database = read_pickle(args.test_data)
    candidates = read_pickle(args.candidate_path)
    predictions = read_pickle(args.prediction_path)
    relations = indexed_predictions(read_json(args.relation_json), "output")
    hops = indexed_predictions(read_json(args.hop_json), "predict")

    claims = list(database)
    predicted = [int(value) for value in as_list(predictions["prediction"])]
    saved_labels = [int(value) for value in as_list(predictions["label"])]
    saved_types = [int(value) for value in as_list(predictions["reasoning_type"])]
    if not len(claims) == len(predicted) == len(saved_labels) == len(saved_types):
        raise ValueError("Test data and prediction lengths differ")

    # A misaligned prediction bin would make every subsequent example invalid.
    for index, claim in enumerate(claims):
        metadata = database[claim]
        if saved_labels[index] != label_to_int(metadata["Label"]):
            raise ValueError(f"Label/order mismatch at test index {index}: {claim!r}")
        if saved_types[index] != reasoning_type(metadata["types"]):
            raise ValueError(f"Reasoning type/order mismatch at test index {index}: {claim!r}")
        if claim not in candidates or claim not in relations or claim not in hops:
            raise KeyError(f"Missing candidate or retrieval prediction: {claim!r}")

    conjunction = [i for i, type_id in enumerate(saved_types) if type_id == 2]
    groups = {
        "true_to_false_connected": [
            i for i in conjunction if saved_labels[i] == 1
            and predicted[i] == 0 and candidates[claims[i]]["connected"]
        ],
        "true_to_false_no_connected": [
            i for i in conjunction if saved_labels[i] == 1
            and predicted[i] == 0 and not candidates[claims[i]]["connected"]
        ],
        "false_to_true": [
            i for i in conjunction if saved_labels[i] == 0 and predicted[i] == 1
        ],
        "true_to_true_control": [
            i for i in conjunction if saved_labels[i] == 1 and predicted[i] == 1
        ],
    }
    no_connected_empty = [
        i for i in groups["true_to_false_no_connected"]
        if not candidates[claims[i]]["walkable"]
    ]
    no_connected_walkable = [
        i for i in groups["true_to_false_no_connected"]
        if candidates[claims[i]]["walkable"]
    ]
    true_control_connected = [
        i for i in groups["true_to_true_control"]
        if candidates[claims[i]]["connected"]
    ]
    true_control_no_connected = [
        i for i in groups["true_to_true_control"]
        if not candidates[claims[i]]["connected"]
    ]

    rng = random.Random(args.seed)
    sample_requests = [
        ("true_to_false_connected", groups["true_to_false_connected"], 20),
        ("true_to_false_no_path", no_connected_empty, 5),
        ("true_to_false_walkable_only", no_connected_walkable, 5),
        ("false_to_true", groups["false_to_true"], 10),
        ("true_to_true_connected_control", true_control_connected, 5),
        ("true_to_true_no_connected_control", true_control_no_connected, 5),
    ]
    sampled = []
    sample_counts = {}
    for bucket, indices, requested in sample_requests:
        selection = sample_diverse(
            indices, requested, claims, database, rng, args.max_per_entity_set
        )
        sample_counts[bucket] = {"available": len(indices), "selected": len(selection)}
        sampled.extend((bucket, index) for index in selection)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "conjunction_cases.csv"
    md_path = args.output_dir / "conjunction_cases.md"
    summary_path = args.output_dir / "conjunction_summary.json"
    for destination in (csv_path, md_path, summary_path):
        if destination.exists() and not args.overwrite:
            raise FileExistsError(f"Output exists: {destination}; use --overwrite")

    summary = {
        "inputs": {name: str(path.resolve()) for name, path in (
            ("test_data", args.test_data),
            ("candidate_path", args.candidate_path),
            ("prediction_path", args.prediction_path),
            ("relation_json", args.relation_json),
            ("hop_json", args.hop_json),
        )},
        "seed": args.seed,
        "max_paths": args.max_paths,
        "conjunction_total": len(conjunction),
        "true_to_false": bucket_counts(
            groups["true_to_false_connected"] + groups["true_to_false_no_connected"],
            claims, candidates, args.max_paths,
        ),
        "true_to_true": bucket_counts(
            groups["true_to_true_control"], claims, candidates, args.max_paths,
        ),
        "false_to_true": bucket_counts(
            groups["false_to_true"], claims, candidates, args.max_paths,
        ),
        "samples": sample_counts,
    }

    fields = [
        "test_index", "bucket", "claim", "gold_label", "prediction",
        "entity_set_json", "top_relations_json", "predicted_hop",
        "connected_count", "walkable_count", "visible_count",
        "stored_after_k_count", "visible_paths_json", "after_k_preview_json",
        "clause_1", "clause_2", "other_clauses",
        "proof_clause_1_positions", "proof_clause_2_positions",
        "proof_other_clauses_positions", "suspected_cause", "notes",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        with md_path.open("w", encoding="utf-8") as report:
            report.write("# Bước A — đọc lỗi Conjunction của V4\n\n")
            report.write(
                "Chỉ các path từ vị trí 1 đến K mới đi vào V4. "
                "`connected` không đồng nghĩa với proof đủ các vế. "
                "Test không có Evidence vàng nên kết luận phải được kiểm tra thủ công. "
                "Nếu artifact đã bị giới hạn khi lưu, không thể biết có path nào "
                "nằm sau K nếu chỉ đọc artifact này; kiểm tra `store_max_paths` "
                "trong manifest R3.\n\n"
            )
            report.write(
                f"K={args.max_paths}; seed lấy mẫu={args.seed}; "
                f"Conjunction={len(conjunction)} câu; mẫu={len(sampled)} câu.\n\n"
            )
            for name in ("true_to_false", "true_to_true", "false_to_true"):
                stats = summary[name]
                report.write(
                    f"- {name}: n={stats['n']}, 0 path={stats['no_path']}, "
                    f"0 connected={stats['no_connected']}, "
                    f"đúng K path={stats['at_model_cap_in_artifact']}\n"
                )
            report.write("\n")
            report.write(
                "Điền `suspected_cause` trong CSV bằng một trong: "
                "`missing_relation`, `relation_but_no_kg_path`, `after_k`, "
                "`model_with_full_proof`, `unclear`. Chỉ chọn `model_with_full_proof` "
                "nếu đã tìm thấy proof cho tất cả vế trong các path V4 nhìn thấy.\n\n"
            )
            for number, (bucket, index) in enumerate(sampled, 1):
                claim = claims[index]
                metadata = database[claim]
                candidate = candidates[claim]
                all_paths = path_groups(candidate)
                visible = all_paths[:args.max_paths]
                after_k_preview = all_paths[args.max_paths:args.max_paths + 16]
                row = {
                    "test_index": index,
                    "bucket": bucket,
                    "claim": claim,
                    "gold_label": saved_labels[index],
                    "prediction": predicted[index],
                    "entity_set_json": json.dumps(
                        metadata.get("Entity_set", []), ensure_ascii=False
                    ),
                    "top_relations_json": json.dumps(
                        relations[claim], ensure_ascii=False
                    ),
                    "predicted_hop": int(hops[claim]),
                    "connected_count": len(candidate["connected"]),
                    "walkable_count": len(candidate["walkable"]),
                    "visible_count": len(visible),
                    "stored_after_k_count": max(0, len(all_paths) - args.max_paths),
                    "visible_paths_json": json.dumps(visible, ensure_ascii=False),
                    "after_k_preview_json": json.dumps(
                        after_k_preview, ensure_ascii=False
                    ),
                    "clause_1": "", "clause_2": "", "other_clauses": "",
                    "proof_clause_1_positions": "",
                    "proof_clause_2_positions": "",
                    "proof_other_clauses_positions": "",
                    "suspected_cause": "", "notes": "",
                }
                writer.writerow(row)
                report.write(f"## {number}. {bucket} — test index {index}\n\n")
                report.write(f"- Claim: {claim}\n")
                report.write(
                    f"- Nhãn thật: {bool(saved_labels[index])}; "
                    f"V4 đoán: {bool(predicted[index])}\n"
                )
                report.write(f"- Entity_set: `{row['entity_set_json']}`\n")
                report.write(
                    f"- Top relations: `{row['top_relations_json']}`; "
                    f"H: {row['predicted_hop']}\n"
                )
                report.write(
                    f"- Candidate: {row['connected_count']} connected + "
                    f"{row['walkable_count']} walkable; "
                    f"V4 thấy {row['visible_count']}; "
                    f"artifact còn {row['stored_after_k_count']} path sau K.\n\n"
                )
                report.write("```text\n")
                if not visible:
                    report.write("Không có path.\n")
                for path_index, (kind, path) in enumerate(visible, 1):
                    report.write(
                        f"{path_index:02d} {kind}: "
                        f"{json.dumps(path, ensure_ascii=False)}\n"
                    )
                report.write("```\n\n")
                if after_k_preview:
                    report.write("16 path đầu sau K (V4 không nhìn thấy):\n\n```text\n")
                    for offset, (kind, path) in enumerate(after_k_preview, args.max_paths + 1):
                        report.write(
                            f"{offset:02d} {kind}: "
                            f"{json.dumps(path, ensure_ascii=False)}\n"
                        )
                    report.write("```\n\n")
                report.write(
                    "- Vế 1 và path chứng minh: ...\n"
                    "- Vế 2 và path chứng minh: ...\n"
                    "- Vế khác nếu có và path chứng minh: ...\n"
                    "- Kết luận sơ bộ và lý do: ...\n\n"
                )

    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    print(f"Conjunction cases: {len(conjunction)}; sampled: {len(sampled)}")
    for name in ("true_to_false", "true_to_true", "false_to_true"):
        stats = summary[name]
        print(
            f"  {name}: n={stats['n']}, no_path={stats['no_path']}, "
            f"no_connected={stats['no_connected']}, "
            f"at_K={stats['at_model_cap_in_artifact']}"
        )
    for bucket, counts in sample_counts.items():
        print(f"  {bucket}: {counts['selected']}/{counts['available']}")
    print(f"Summary: {summary_path}")
    print(f"Review:  {md_path}")
    print(f"CSV:     {csv_path}")


if __name__ == "__main__":
    main()
