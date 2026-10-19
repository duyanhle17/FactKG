"""Audit hand-annotated conjunction clauses on dev; do not train or score test.

The clause specification is a small, manually reviewed dev-only diagnostic.
An absent stored path means "not observed", not that a KG proposition is false.
The strict-AND result is a counterfactual, not a deployable classifier.
"""

import argparse
import json
import pickle
from pathlib import Path


def read_pickle(path):
    with path.open("rb") as handle:
        return pickle.load(handle)


def values(result, key):
    value = result[key]
    return value.tolist() if hasattr(value, "tolist") else list(value)


def label_of(row):
    label = row["Label"]
    if isinstance(label, (list, tuple)):
        if len(label) != 1:
            raise ValueError("Expected exactly one label per claim")
        label = label[0]
    return int(label)


def visible_paths(row, max_paths):
    return (list(row["connected"]) + list(row["walkable"]))[:max_paths]


def path_keys(paths):
    return {tuple(path) for path in paths}


def clause_supported(clause, paths):
    alternatives = clause["support_any"]
    if not alternatives or any(len(path) < 3 or len(path) % 2 != 1
                               for path in alternatives):
        raise ValueError(f"Invalid support_any for clause {clause.get('name')!r}")
    keys = path_keys(paths)
    return any(tuple(path) in keys for path in alternatives)


def strict_and_counterfactual(v4_prediction, all_clauses_observed):
    """What a strict proof gate would say; missing evidence is NOT refutation."""
    return int(v4_prediction) if all_clauses_observed else 0


def audit_case(case, raw_row, first_row, ranked_row, first_prediction,
               ranked_prediction, max_paths):
    claim = case["claim"]
    if first_row["connected"] != ranked_row["connected"]:
        raise ValueError(f"Connected paths differ between first/ranked: {claim!r}")
    if not case.get("clauses"):
        raise ValueError(f"No annotated clauses for {claim!r}")
    inputs = {
        "stored_r3": visible_paths(raw_row, max_paths),
        "first5": visible_paths(first_row, max_paths),
        "ranked5": visible_paths(ranked_row, max_paths),
    }
    clauses = []
    for clause in case["clauses"]:
        clauses.append({
            "name": clause["name"],
            "support_any": clause["support_any"],
            "observed": {
                name: clause_supported(clause, paths)
                for name, paths in inputs.items()
            },
        })
    coverage = {
        name: sum(clause["observed"][name] for clause in clauses)
        for name in inputs
    }
    return {
        "claim": claim,
        "group": case["group"],
        "note": case.get("note", ""),
        "clauses": clauses,
        "coverage": coverage,
        "total_clauses": len(clauses),
        "stored_path_counts": {
            "connected": len(raw_row["connected"]),
            "walkable": len(raw_row["walkable"]),
        },
        "first5_prediction": int(first_prediction),
        "ranked5_prediction": int(ranked_prediction),
        "strict_gate_first5": strict_and_counterfactual(
            first_prediction, coverage["first5"] == len(clauses)),
        "strict_gate_ranked5": strict_and_counterfactual(
            ranked_prediction, coverage["ranked5"] == len(clauses)),
    }


def render_markdown(rows, max_paths):
    lines = [
        "# Pilot: kiểm tra từng vế Conjunction trên dev\n\n",
        "Chú giải vế được viết thủ công sau khi xem dev và có thể chịu ảnh hưởng "
        "của gold dev. Lúc chạy, script chỉ đối chiếu path đã lưu với chú giải; "
        "Gold label/Evidence chỉ hiển thị để rà soát. "
        "Không thấy path trong candidate không chứng minh vế sai. "
        "Strict-AND bên dưới chỉ là phản thực nghiệm trên mẫu chọn trước, "
        "không phải điểm accuracy hay bộ suy luận dùng cho test.\n\n",
        f"R3 và V4 đều được quan sát qua tối đa {max_paths} path đã lưu.\n\n",
    ]
    for number, row in enumerate(rows, 1):
        n = row["total_clauses"]
        covered = row["coverage"]
        counts = row["stored_path_counts"]
        lines.extend([
            f"## {number}. {row['claim']}\n\n",
            f"Nhóm: `{row['group']}`; nhãn dev={row['gold_label']}; "
            f"V4 first5/ranked5={row['first5_prediction']}/{row['ranked5_prediction']}.\n\n",
            f"Path R3 đã lưu: connected={counts['connected']}, "
            f"walkable={counts['walkable']}. Số vế có path khớp chính xác: "
            f"R3={covered['stored_r3']}/{n}, first5={covered['first5']}/{n}, "
            f"ranked5={covered['ranked5']}/{n}.\n\n",
            "| Vế cần kiểm tra | R3 đã lưu | first5 | ranked5 |\n",
            "| --- | --- | --- | --- |\n",
        ])
        for clause in row["clauses"]:
            observed = clause["observed"]
            name = clause["name"].replace("|", "\\|")
            lines.append(
                f"| {name} | {int(observed['stored_r3'])} | "
                f"{int(observed['first5'])} | {int(observed['ranked5'])} |\n")
        lines.extend([
            "\n",
            f"Nếu dùng strict-AND để chặn dự đoán True: "
            f"first5={row['strict_gate_first5']}, "
            f"ranked5={row['strict_gate_ranked5']} "
            "(**chỉ chẩn đoán; thiếu path ≠ False**).\n\n",
        ])
        if row["note"]:
            lines.append(f"Ghi chú thủ công: {row['note']}\n\n")
        if row["group"] == "label_review":
            lines.append("Evidence gốc để rà soát nhãn (không phải đầu vào V4):\n\n")
            lines.append("```json\n")
            lines.append(json.dumps(row["gold_evidence"], ensure_ascii=False,
                                    indent=2, default=str))
            lines.append("\n```\n\n")
    return "".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("spec", "data", "gold_dev", "raw_candidates",
                 "first_candidates", "ranked_candidates", "first_prediction",
                 "ranked_prediction", "report", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--max_paths", type=int, default=32)
    args = parser.parse_args()
    if args.max_paths < 1:
        parser.error("--max_paths must be positive")

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    cases = spec["cases"]
    if not cases or len({case["claim"] for case in cases}) != len(cases):
        raise ValueError("Spec must contain distinct claims")
    data = read_pickle(args.data)
    gold = read_pickle(args.gold_dev)
    raw = read_pickle(args.raw_candidates)
    first = read_pickle(args.first_candidates)
    ranked = read_pickle(args.ranked_candidates)
    claims = list(data)
    if not all(set(claims) == set(candidate) for candidate in (raw, first, ranked)):
        raise ValueError("Candidate claim sets differ from pseudo-test dev data")
    first_result = read_pickle(args.first_prediction)
    ranked_result = read_pickle(args.ranked_prediction)
    first_labels = [int(x) for x in values(first_result, "label")]
    ranked_labels = [int(x) for x in values(ranked_result, "label")]
    first_types = [int(x) for x in values(first_result, "reasoning_type")]
    ranked_types = [int(x) for x in values(ranked_result, "reasoning_type")]
    first_pred = [int(x) for x in values(first_result, "prediction")]
    ranked_pred = [int(x) for x in values(ranked_result, "prediction")]
    if not all(len(array) == len(claims) for array in
               (first_labels, ranked_labels, first_types, ranked_types,
                first_pred, ranked_pred)):
        raise ValueError("Prediction lengths differ from pseudo-test dev data")
    if first_labels != ranked_labels or first_types != ranked_types:
        raise ValueError("Prediction labels/types differ; check claim order")
    with args.report.open(encoding="utf-8") as handle:
        limited = set(json.load(handle)["splits"]["test"]["expansion_limited_claims"])
    positions = {claim: i for i, claim in enumerate(claims)}
    rows = []
    for case in cases:
        claim = case["claim"]
        if claim not in positions or claim not in gold:
            raise ValueError(f"Claim not found in dev: {claim!r}")
        if claim in limited:
            raise ValueError(f"Claim was expansion-limited: {claim!r}")
        i = positions[claim]
        if label_of(data[claim]) != first_labels[i] or \
                label_of(gold[claim]) != first_labels[i]:
            raise ValueError(f"Data, original dev and prediction labels differ: {claim!r}")
        row = audit_case(case, raw[claim], first[claim], ranked[claim],
                         first_pred[i], ranked_pred[i], args.max_paths)
        row["gold_label"] = first_labels[i]
        row["gold_evidence"] = gold[claim].get("Evidence")
        rows.append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        handle.write(render_markdown(rows, args.max_paths))
    print(f"Pilot cases: {len(rows)}; report: {args.output}")
    for row in rows:
        n = row["total_clauses"]
        coverage = row["coverage"]
        print(f"  {row['group']:12} label={row['gold_label']} "
              f"V4={row['first5_prediction']}/{row['ranked5_prediction']} "
              f"proof R3/first/ranked="
              f"{coverage['stored_r3']}/{coverage['first5']}/{coverage['ranked5']} "
              f"of {n}: {row['claim']}")


if __name__ == "__main__":
    main()
