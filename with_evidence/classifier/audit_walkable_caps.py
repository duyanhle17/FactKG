"""Compare fixed-checkpoint R3/walkable-cap predictions on the same claims.

This is a read-only diagnostic. It does not train V4 or rebuild KG candidates.
The prediction pickles must come from the same checkpoint and evaluation setup.
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


def visible_paths(row, walk_limit, max_paths):
    paths = list(row["connected"]) + list(row["walkable"][:walk_limit])
    return paths[:max_paths]


def compare_group(indices, labels, predictions):
    five = predictions["walk5"]
    ten = predictions["walk10"]
    return {
        "n": len(indices),
        "r3_correct": sum(predictions["r3"][i] == labels[i] for i in indices),
        "walk5_correct": sum(five[i] == labels[i] for i in indices),
        "walk10_correct": sum(ten[i] == labels[i] for i in indices),
        "walk5_only": [i for i in indices if five[i] == labels[i] and ten[i] != labels[i]],
        "walk10_only": [i for i in indices if ten[i] == labels[i] and five[i] != labels[i]],
    }


def compare_pair(indices, labels, predictions, left, right):
    left_correct = [i for i in indices if predictions[left][i] == labels[i]]
    right_correct = [i for i in indices if predictions[right][i] == labels[i]]
    return {
        "left_correct": len(left_correct),
        "right_correct": len(right_correct),
        "left_only": [i for i in indices if predictions[left][i] == labels[i]
                      and predictions[right][i] != labels[i]],
        "right_only": [i for i in indices if predictions[right][i] == labels[i]
                       and predictions[left][i] != labels[i]],
    }


def walk_limit_from_name(name):
    if name == "r3":
        return None
    if name.startswith("walk") and name[4:].isdigit():
        return int(name[4:])
    raise ValueError(f"Cannot infer walkable cap from prediction name {name!r}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path,
                        help="Test-style pickle for the same dev claims")
    parser.add_argument("--candidates", required=True, type=Path,
                        help="Full predicted R3 candidates before walkable truncation")
    parser.add_argument("--r3", required=True, type=Path)
    parser.add_argument("--walk5", required=True, type=Path)
    parser.add_argument("--walk10", required=True, type=Path)
    parser.add_argument("--extra", action="append", default=[], metavar="NAME=PATH",
                        help="Additional fixed-checkpoint prediction to compare with R3")
    parser.add_argument("--pair", action="append", default=[], metavar="LEFT,RIGHT",
                        help="Compare two named predictions claim by claim, e.g. walk5,walk7")
    parser.add_argument("--report", type=Path,
                        help="Retrieval report with expansion_limited_claims")
    parser.add_argument("--max_paths", type=int, default=32)
    parser.add_argument("--examples", type=int, default=2)
    args = parser.parse_args()
    if args.max_paths < 1 or args.examples < 0:
        parser.error("--max_paths must be positive and --examples nonnegative")

    data = read_pickle(args.data)
    candidates = read_pickle(args.candidates)
    claims = list(data)
    if set(claims) != set(candidates):
        raise ValueError("Data and candidate claim sets differ")

    results = {
        "r3": read_pickle(args.r3),
        "walk5": read_pickle(args.walk5),
        "walk10": read_pickle(args.walk10),
    }
    extra_names = []
    for spec in args.extra:
        name, separator, path = spec.partition("=")
        if not separator or not name or not path or name in results:
            parser.error(f"Invalid or duplicate --extra NAME=PATH: {spec!r}")
        results[name] = read_pickle(Path(path))
        extra_names.append(name)
    pairs = []
    for spec in args.pair:
        left, separator, right = spec.partition(",")
        if not separator or left not in results or right not in results or left == right:
            parser.error(f"Invalid --pair LEFT,RIGHT: {spec!r}")
        try:
            walk_limit_from_name(left)
            walk_limit_from_name(right)
        except ValueError as exc:
            parser.error(str(exc))
        pairs.append((left, right))
    labels = [int(x) for x in values(results["r3"], "label")]
    types = [int(x) for x in values(results["r3"], "reasoning_type")]
    predictions = {
        name: [int(x) for x in values(result, "prediction")]
        for name, result in results.items()
    }
    if any(len(array) != len(claims) for array in (labels, types, *predictions.values())):
        raise ValueError("Prediction lengths do not match the data claim count")
    for name, result in results.items():
        if [int(x) for x in values(result, "label")] != labels:
            raise ValueError(f"{name} labels differ from R3; check claim order")
        if [int(x) for x in values(result, "reasoning_type")] != types:
            raise ValueError(f"{name} reasoning types differ from R3")
    for i, claim in enumerate(claims):
        raw_label = data[claim]["Label"]
        if isinstance(raw_label, (list, tuple)):
            if len(raw_label) != 1:
                raise ValueError(f"Expected one label for {claim!r}")
            raw_label = raw_label[0]
        if int(raw_label) != labels[i]:
            raise ValueError(f"Prediction/data label mismatch at claim {i}: {claim!r}")

    limited = set()
    if args.report:
        with args.report.open(encoding="utf-8") as handle:
            report = json.load(handle)
        limited = set(report["splits"]["test"]["expansion_limited_claims"])
        if not limited <= set(claims):
            raise ValueError("Retrieval report has claims absent from data")

    print(f"Claims: {len(claims)}; expansion-limited: {len(limited)}")
    subsets = [("ALL", list(range(len(claims))))]
    if args.report:
        subsets.extend((
            ("UNCAPPED", [i for i, claim in enumerate(claims) if claim not in limited]),
            ("EXPANSION-LIMITED", [i for i, claim in enumerate(claims) if claim in limited]),
        ))
    for subset_name, subset_ids in subsets:
        print(f"\n{subset_name}: {len(subset_ids)} claims")
        groups = (
            ("ALL", subset_ids),
            ("MULTI-HOP", [i for i in subset_ids if types[i] == 1]),
            ("CONJ TRUE", [i for i in subset_ids if types[i] == 2 and labels[i] == 1]),
            ("CONJ FALSE", [i for i in subset_ids if types[i] == 2 and labels[i] == 0]),
        )
        for group_name, ids in groups:
            row = compare_group(ids, labels, predictions)
            print(
                f"  {group_name:11} n={row['n']:5}  "
                f"R3={row['r3_correct']:5}  "
                f"walk5={row['walk5_correct']:5}  "
                f"walk10={row['walk10_correct']:5}  "
                f"5-only={len(row['walk5_only']):4}  "
                f"10-only={len(row['walk10_only']):4}"
            )

    # Print only uncapped examples: their candidate search was not interrupted.
    sample_ids = [i for i, claim in enumerate(claims) if claim not in limited]
    for group_name, ids in (
        ("MULTI-HOP", [i for i in sample_ids if types[i] == 1]),
        ("CONJ TRUE", [i for i in sample_ids if types[i] == 2 and labels[i] == 1]),
        ("CONJ FALSE", [i for i in sample_ids if types[i] == 2 and labels[i] == 0]),
    ):
        row = compare_group(ids, labels, predictions)
        for direction, flips in (("walk5-only", row["walk5_only"]),
                                 ("walk10-only", row["walk10_only"])):
            same_input = sum(
                visible_paths(candidates[claims[i]], 5, args.max_paths)
                == visible_paths(candidates[claims[i]], 10, args.max_paths)
                for i in flips
            )
            print(f"\n{group_name} {direction}: {len(flips)}; "
                  f"same visible input: {same_input}")
            for i in flips[:args.examples]:
                claim = claims[i]
                row_candidates = candidates[claim]
                five_paths = visible_paths(row_candidates, 5, args.max_paths)
                ten_paths = visible_paths(row_candidates, 10, args.max_paths)
                print(f"  Claim: {claim}")
                print(f"  connected={len(row_candidates['connected'])}; "
                      f"visible paths 5/10={len(five_paths)}/{len(ten_paths)}")
                print(f"  Newly visible paths (up to 5): "
                      f"{ten_paths[len(five_paths):len(five_paths) + 5]!r}")

    if extra_names:
        print("\nADDITIONAL CAPS (same checkpoint; paired against R3)")
        for subset_name, subset_ids in subsets:
            print(f"\n{subset_name}: {len(subset_ids)} claims")
            groups = (
                ("ALL", subset_ids),
                ("MULTI-HOP", [i for i in subset_ids if types[i] == 1]),
                ("CONJ TRUE", [i for i in subset_ids if types[i] == 2 and labels[i] == 1]),
                ("CONJ FALSE", [i for i in subset_ids if types[i] == 2 and labels[i] == 0]),
            )
            for group_name, ids in groups:
                for name in extra_names:
                    correct = sum(predictions[name][i] == labels[i] for i in ids)
                    rescued = sum(
                        predictions["r3"][i] != labels[i]
                        and predictions[name][i] == labels[i]
                        for i in ids
                    )
                    harmed = sum(
                        predictions["r3"][i] == labels[i]
                        and predictions[name][i] != labels[i]
                        for i in ids
                    )
                    print(f"  {group_name:11} {name:8} n={len(ids):5} "
                          f"correct={correct:5} rescued={rescued:4} harmed={harmed:4}")

    for left, right in pairs:
        print(f"\nPAIRED {left} vs {right}")
        for subset_name, subset_ids in subsets:
            print(f"\n{subset_name}: {len(subset_ids)} claims")
            groups = (
                ("ALL", subset_ids),
                ("MULTI-HOP", [i for i in subset_ids if types[i] == 1]),
                ("CONJ TRUE", [i for i in subset_ids if types[i] == 2 and labels[i] == 1]),
                ("CONJ FALSE", [i for i in subset_ids if types[i] == 2 and labels[i] == 0]),
            )
            for group_name, ids in groups:
                row = compare_pair(ids, labels, predictions, left, right)
                flipped = row["left_only"] + row["right_only"]
                same_input = sum(
                    visible_paths(candidates[claims[i]], walk_limit_from_name(left),
                                  args.max_paths)
                    == visible_paths(candidates[claims[i]], walk_limit_from_name(right),
                                     args.max_paths)
                    for i in flipped
                )
                print(
                    f"  {group_name:11} n={len(ids):5} "
                    f"{left}_correct={row['left_correct']:5} "
                    f"{right}_correct={row['right_correct']:5} "
                    f"{left}-only={len(row['left_only']):4} "
                    f"{right}-only={len(row['right_only']):4} "
                    f"same_input={same_input}"
                )
                # Do not duplicate examples across ALL, uncapped, and group rows.
                example_subset = "UNCAPPED" if args.report else "ALL"
                if subset_name != example_subset or group_name not in (
                    "CONJ TRUE", "CONJ FALSE"
                ):
                    continue
                for direction, flips in ((f"{left}-only", row["left_only"]),
                                         (f"{right}-only", row["right_only"])):
                    for i in flips[:args.examples]:
                        claim = claims[i]
                        candidate = candidates[claim]
                        left_paths = visible_paths(
                            candidate, walk_limit_from_name(left), args.max_paths
                        )
                        right_paths = visible_paths(
                            candidate, walk_limit_from_name(right), args.max_paths
                        )
                        print(f"    {direction}: {claim}")
                        print(f"      connected={len(candidate['connected'])}; "
                              f"visible={len(left_paths)}/{len(right_paths)}")
                        print(f"      Only {right} (up to 3): "
                              f"{[p for p in right_paths if p not in left_paths][:3]!r}")
                        print(f"      Only {left} (up to 3): "
                              f"{[p for p in left_paths if p not in right_paths][:3]!r}")


if __name__ == "__main__":
    main()
