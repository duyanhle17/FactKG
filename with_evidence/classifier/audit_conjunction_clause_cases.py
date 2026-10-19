"""Write a manual casebook for Conjunction errors on pseudo-test dev claims.

This read-only audit never changes candidates or predictions. Gold dev Evidence,
when supplied, is displayed only as an offline reference. The script does not
infer which clause is false or whether missing KG paths prove a negation.
"""

import argparse
import json
import pickle
import random
from pathlib import Path


def read_pickle(path):
    with path.open("rb") as handle:
        return pickle.load(handle)


def values(result, key):
    value = result[key]
    return value.tolist() if hasattr(value, "tolist") else list(value)


def visible_groups(row, max_paths):
    connected = list(row["connected"][:max_paths])
    walkable = list(row["walkable"][:max(0, max_paths - len(connected))])
    return connected, walkable


def cases_by_group(indices, labels, types, first, ranked):
    conjunction = [i for i in indices if types[i] == 2]
    return {
        "FALSE: first5 đúng, ranked5 sai": [
            i for i in conjunction if labels[i] == 0 and first[i] == 0 and ranked[i] == 1
        ],
        "FALSE: cả hai đều sai": [
            i for i in conjunction if labels[i] == 0 and first[i] == 1 and ranked[i] == 1
        ],
        "FALSE: ranked5 cứu": [
            i for i in conjunction if labels[i] == 0 and first[i] == 1 and ranked[i] == 0
        ],
        "TRUE: ranked5 cứu": [
            i for i in conjunction if labels[i] == 1 and first[i] == 0 and ranked[i] == 1
        ],
    }


def append_paths(lines, title, paths):
    lines.append(f"**{title} ({len(paths)}):**\n")
    if not paths:
        lines.append("- Không có path trong đầu vào V4.\n")
    for number, path in enumerate(paths, 1):
        encoded = json.dumps(path, ensure_ascii=False, default=str)
        lines.append(f"{number}. `{encoded}`\n")
    lines.append("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--first5", required=True, type=Path)
    parser.add_argument("--ranked5", required=True, type=Path)
    parser.add_argument("--first_candidates", required=True, type=Path)
    parser.add_argument("--ranked_candidates", required=True, type=Path)
    parser.add_argument("--report", type=Path,
                        help="Skip expansion-limited claims in this first audit")
    parser.add_argument("--gold_dev", type=Path,
                        help="Optional original dev pickle; displayed, never used to select cases")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max_cases", type=int, default=8)
    parser.add_argument("--max_paths", type=int, default=32)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.max_cases < 1 or args.max_paths < 1:
        parser.error("--max_cases and --max_paths must be positive")

    data = read_pickle(args.data)
    claims = list(data)
    first_result = read_pickle(args.first5)
    ranked_result = read_pickle(args.ranked5)
    labels = [int(x) for x in values(first_result, "label")]
    types = [int(x) for x in values(first_result, "reasoning_type")]
    first = [int(x) for x in values(first_result, "prediction")]
    ranked = [int(x) for x in values(ranked_result, "prediction")]
    if any(len(array) != len(claims) for array in (labels, types, first, ranked)):
        raise ValueError("Prediction lengths do not match data claims")
    for field, expected in (("label", labels), ("reasoning_type", types)):
        if [int(x) for x in values(ranked_result, field)] != expected:
            raise ValueError(f"{field} differs between prediction files")
    for i, claim in enumerate(claims):
        raw = data[claim]["Label"]
        if isinstance(raw, (list, tuple)):
            if len(raw) != 1:
                raise ValueError(f"Expected one label for {claim!r}")
            raw = raw[0]
        if int(raw) != labels[i]:
            raise ValueError(f"Prediction/data label mismatch at claim {i}")

    first_candidates = read_pickle(args.first_candidates)
    ranked_candidates = read_pickle(args.ranked_candidates)
    if set(first_candidates) != set(claims) or set(ranked_candidates) != set(claims):
        raise ValueError("Candidate claim sets differ from data")
    limited = set()
    if args.report:
        with args.report.open(encoding="utf-8") as handle:
            limited = set(json.load(handle)["splits"]["test"]["expansion_limited_claims"])
        if not limited <= set(claims):
            raise ValueError("Report has claims absent from data")
    gold = read_pickle(args.gold_dev) if args.gold_dev else None
    if gold is not None and not set(claims) <= set(gold):
        raise ValueError("Gold dev file is missing pseudo-test dev claims")

    indices = [i for i, claim in enumerate(claims) if claim not in limited]
    groups = cases_by_group(indices, labels, types, first, ranked)
    lines = [
        "# Conjunction: kiểm tra từng vế trên dev\n\n",
        "Dùng nhãn/Evidence dev **chỉ để chẩn đoán**, không đưa vào R3/V4. "
        "Không thấy path không chứng minh mệnh đề sai trong KG mở. "
        "Đây là mẫu case để đọc thủ công, chưa phải kết luận lỗi do R3 hay V4.\n\n",
        f"Nguồn: {len(claims)} claim; bỏ qua {len(limited)} claim bị giới hạn duyệt; "
        f"V4 xem tối đa {args.max_paths} path.\n\n",
    ]
    for group_name, group_ids in groups.items():
        lines.append(f"## {group_name}: {len(group_ids)} claim\n\n")
        selected = group_ids if len(group_ids) <= args.max_cases else sorted(
            random.Random(args.seed).sample(group_ids, args.max_cases)
        )
        for i in selected:
            claim = claims[i]
            first_row = first_candidates[claim]
            ranked_row = ranked_candidates[claim]
            first_connected, first_walk = visible_groups(first_row, args.max_paths)
            ranked_connected, ranked_walk = visible_groups(ranked_row, args.max_paths)
            if first_connected != ranked_connected:
                raise ValueError(f"Connected V4 inputs differ at {claim!r}")
            lines.append(f"### {claim}\n\n")
            lines.append(f"Gold label: {labels[i]}; first5: {first[i]}; "
                         f"ranked5: {ranked[i]}\n\n")
            if gold is not None:
                evidence = gold[claim].get("Evidence")
                lines.append("Gold Evidence (chỉ tham khảo offline):\n\n```json\n")
                lines.append(json.dumps(evidence, ensure_ascii=False, indent=2, default=str))
                lines.append("\n```\n\n")
            append_paths(lines, "Connected chung", first_connected)
            append_paths(lines, "Walkable first5", first_walk)
            append_paths(lines, "Walkable ranked5", ranked_walk)
            lines.append("- Vế 1 của claim: _đánh dấu thủ công_\n")
            lines.append("- Vế 2 của claim: _đánh dấu thủ công_\n")
            lines.append("- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_\n")
            lines.append("- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_\n\n")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        handle.writelines(lines)
    print(f"Casebook: {args.output}")
    for name, ids in groups.items():
        print(f"{name}: {len(ids)}; written: {min(len(ids), args.max_cases)}")


if __name__ == "__main__":
    main()
