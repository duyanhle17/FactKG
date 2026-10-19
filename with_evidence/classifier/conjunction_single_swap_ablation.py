"""Prepare and compare one-path-swap V4 ablations for dev Conjunction False.

Prepare selects claims where first5 is correct and ranked5 is wrong. It writes
a small test-style dev subset, a first5/ranked5 control, and one candidate file
per single added/removed walkable-path swap. No KG search or V4 training occurs.
The dev labels select diagnostic cases only; gold Evidence is never copied.
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


def swap_plan(first_paths, ranked_paths):
    removed_indices = [i for i, path in enumerate(first_paths)
                       if path not in ranked_paths]
    added = [path for path in ranked_paths if path not in first_paths]
    if len(removed_indices) != len(added):
        raise ValueError("Walkable path multiplicities differ; cannot pair one-path swaps")
    return list(zip(removed_indices, added))


def make_swap_row(first_row, plan, swap_number):
    updated = dict(first_row)
    paths = list(first_row["walkable"])
    if swap_number <= len(plan):
        index, added_path = plan[swap_number - 1]
        paths[index] = added_path
    updated["walkable"] = paths
    return updated


def prepare(args):
    data = read_pickle(args.data)
    claims = list(data)
    first_result = read_pickle(args.first5)
    ranked_result = read_pickle(args.ranked5)
    labels = [int(x) for x in values(first_result, "label")]
    types = [int(x) for x in values(first_result, "reasoning_type")]
    first_predictions = [int(x) for x in values(first_result, "prediction")]
    ranked_predictions = [int(x) for x in values(ranked_result, "prediction")]
    if any(len(array) != len(claims) for array in
           (labels, types, first_predictions, ranked_predictions)):
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

    selected = [claim for i, claim in enumerate(claims)
                if claim not in limited and types[i] == 2 and labels[i] == 0
                and first_predictions[i] == 0 and ranked_predictions[i] == 1]
    if args.expected_cases is not None and len(selected) != args.expected_cases:
        raise ValueError(f"Expected {args.expected_cases} cases, found {len(selected)}")
    if not selected:
        raise ValueError("No uncapped Conjunction False harmed cases")

    plans = {}
    for claim in selected:
        first_row = first_candidates[claim]
        ranked_row = ranked_candidates[claim]
        if first_row["connected"] != ranked_row["connected"]:
            raise ValueError(f"Connected paths differ for {claim!r}")
        if len(first_row["connected"]) + len(first_row["walkable"]) > args.max_paths:
            raise ValueError(f"first5 exceeds max_paths for {claim!r}")
        if len(ranked_row["connected"]) + len(ranked_row["walkable"]) > args.max_paths:
            raise ValueError(f"ranked5 exceeds max_paths for {claim!r}")
        plan = swap_plan(first_row["walkable"], ranked_row["walkable"])
        if not plan:
            raise ValueError(f"Prediction flipped without a path-set change: {claim!r}")
        plans[claim] = plan

    variants = ["first5", "ranked5"] + [
        f"swap_{number}" for number in range(1, max(map(len, plans.values())) + 1)
    ]
    args.output_dir.mkdir(parents=True, exist_ok=False)
    data_dir = args.output_dir / "data"
    candidates_dir = args.output_dir / "candidates"
    data_dir.mkdir()
    candidates_dir.mkdir()
    subset = {
        claim: {key: data[claim][key] for key in ("Entity_set", "Label", "types")}
        for claim in selected
    }
    with (data_dir / "factkg_test.pickle").open("xb") as handle:
        pickle.dump(subset, handle, protocol=pickle.HIGHEST_PROTOCOL)
    for variant in variants:
        if variant == "first5":
            candidate = {claim: dict(first_candidates[claim]) for claim in selected}
        elif variant == "ranked5":
            candidate = {claim: dict(ranked_candidates[claim]) for claim in selected}
        else:
            number = int(variant.split("_")[1])
            candidate = {
                claim: make_swap_row(first_candidates[claim], plans[claim], number)
                for claim in selected
            }
        with (candidates_dir / f"{variant}.bin").open("xb") as handle:
            pickle.dump(candidate, handle, protocol=pickle.HIGHEST_PROTOCOL)

    positions = {claim: i for i, claim in enumerate(claims)}
    manifest = {
        "variants": variants,
        "cases": [
            {"claim": claim, "gold_label": 0, "full_first5": 0,
             "full_ranked5": 1,
             "swaps": [
                 {"removed_position": position,
                  "removed_path": first_candidates[claim]["walkable"][position],
                  "added_path": added}
                 for position, added in plans[claim]
             ]}
            for claim in selected
        ],
        "source_indices": [positions[claim] for claim in selected],
        "max_paths": args.max_paths,
    }
    with (args.output_dir / "manifest.json").open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
    print(f"Selected {len(selected)} uncapped Conjunction False cases")
    print(f"Variants: {', '.join(variants)}")
    print(f"Output: {args.output_dir}")


def analyze(args):
    with args.manifest.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    cases = manifest["cases"]
    predictions = {}
    for variant in manifest["variants"]:
        path = (args.prediction_dir / variant /
                f"test_pred_gearlite_v4_swap_{variant}_seed{args.seed}.bin")
        result = read_pickle(path)
        predictions[variant] = [int(x) for x in values(result, "prediction")]
        if len(predictions[variant]) != len(cases):
            raise ValueError(f"Prediction length differs for {variant}")
        if [int(x) for x in values(result, "label")] != [0] * len(cases):
            raise ValueError(f"Prediction labels differ for {variant}")
    for variant, expected_key in (("first5", "full_first5"),
                                  ("ranked5", "full_ranked5")):
        expected = [case[expected_key] for case in cases]
        if predictions[variant] != expected:
            raise ValueError(f"{variant} subset self-check differs from full dev")

    for i, case in enumerate(cases, 1):
        index = i - 1
        print(f"\n{i}. {case['claim']}")
        print(f"   first5={predictions['first5'][index]} "
              f"ranked5={predictions['ranked5'][index]}; "
              f"single swaps={len(case['swaps'])}")
        for number, swap in enumerate(case["swaps"], 1):
            variant = f"swap_{number}"
            print(f"   {variant}: prediction={predictions[variant][index]}; "
                  f"removed={swap['removed_path']!r}; added={swap['added_path']!r}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    for name in ("data", "first5", "ranked5", "first_candidates",
                 "ranked_candidates"):
        prepare_parser.add_argument(f"--{name}", required=True, type=Path)
    prepare_parser.add_argument("--report", type=Path)
    prepare_parser.add_argument("--output_dir", required=True, type=Path)
    prepare_parser.add_argument("--max_paths", type=int, default=32)
    prepare_parser.add_argument("--expected_cases", type=int)
    analyze_parser = commands.add_parser("analyze")
    analyze_parser.add_argument("--manifest", required=True, type=Path)
    analyze_parser.add_argument("--prediction_dir", required=True, type=Path)
    analyze_parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.command == "prepare":
        if args.max_paths < 1:
            parser.error("--max_paths must be positive")
        prepare(args)
    else:
        analyze(args)


if __name__ == "__main__":
    main()
