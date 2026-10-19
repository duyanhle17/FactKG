"""Compare first-5 and ranked-5 V4 predictions on the same claims.

Both prediction files must use the same V4 checkpoint and evaluation options.
"""

import argparse
import json
import pickle
from pathlib import Path

from make_ranked_walkable_candidates import path_score, tokens


def read_pickle(path):
    with path.open("rb") as handle:
        return pickle.load(handle)


def values(result, key):
    value = result[key]
    return value.tolist() if hasattr(value, "tolist") else list(value)


def count_group(indices, labels, first, ranked):
    first_correct = sum(first[i] == labels[i] for i in indices)
    ranked_correct = sum(ranked[i] == labels[i] for i in indices)
    rescued = sum(first[i] != labels[i] and ranked[i] == labels[i] for i in indices)
    harmed = sum(first[i] == labels[i] and ranked[i] != labels[i] for i in indices)
    return first_correct, ranked_correct, rescued, harmed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--first5", required=True, type=Path)
    parser.add_argument("--ranked5", required=True, type=Path)
    parser.add_argument("--first_candidates", type=Path)
    parser.add_argument("--ranked_candidates", type=Path)
    parser.add_argument("--report", type=Path,
                        help="Optional retrieval report to separate expansion-limited claims")
    parser.add_argument("--examples", type=int, default=3)
    args = parser.parse_args()
    if (args.first_candidates is None) != (args.ranked_candidates is None):
        parser.error("Pass both --first_candidates and --ranked_candidates")
    if args.examples < 0:
        parser.error("--examples must be nonnegative")

    data = read_pickle(args.data)
    first_result = read_pickle(args.first5)
    ranked_result = read_pickle(args.ranked5)
    claims = list(data)
    labels = [int(x) for x in values(first_result, "label")]
    types = [int(x) for x in values(first_result, "reasoning_type")]
    first = [int(x) for x in values(first_result, "prediction")]
    ranked = [int(x) for x in values(ranked_result, "prediction")]
    if not all(len(array) == len(claims) for array in (labels, types, first, ranked)):
        raise ValueError("Prediction lengths do not match the data")
    for field, expected in (("label", labels), ("reasoning_type", types)):
        if [int(x) for x in values(ranked_result, field)] != expected:
            raise ValueError(f"Prediction {field} arrays differ; check claim order")
    for i, claim in enumerate(claims):
        raw = data[claim]["Label"]
        if isinstance(raw, (list, tuple)):
            if len(raw) != 1:
                raise ValueError(f"Expected one label for {claim!r}")
            raw = raw[0]
        if int(raw) != labels[i]:
            raise ValueError(f"Prediction/data label mismatch at claim {i}")

    limited = set()
    if args.report:
        with args.report.open(encoding="utf-8") as handle:
            limited = set(json.load(handle)["splits"]["test"]["expansion_limited_claims"])
        if not limited <= set(claims):
            raise ValueError("Retrieval report has claims absent from data")

    subsets = [("ALL", list(range(len(claims))))]
    if args.report:
        subsets.extend((
            ("UNCAPPED", [i for i, claim in enumerate(claims) if claim not in limited]),
            ("EXPANSION-LIMITED", [i for i, claim in enumerate(claims) if claim in limited]),
        ))
    for subset_name, subset in subsets:
        print(f"\n{subset_name} (n={len(subset)})")
        groups = (
            ("ALL", subset),
            ("MULTI-HOP", [i for i in subset if types[i] == 1]),
            ("CONJ TRUE", [i for i in subset if types[i] == 2 and labels[i] == 1]),
            ("CONJ FALSE", [i for i in subset if types[i] == 2 and labels[i] == 0]),
        )
        for name, ids in groups:
            old_ok, new_ok, rescued, harmed = count_group(ids, labels, first, ranked)
            print(f"  {name:11} n={len(ids):5} first5={old_ok:5} "
                  f"ranked5={new_ok:5} rescued={rescued:4} harmed={harmed:4}")

    if args.first_candidates is None:
        return
    first_candidates = read_pickle(args.first_candidates)
    ranked_candidates = read_pickle(args.ranked_candidates)
    if set(first_candidates) != set(claims) or set(ranked_candidates) != set(claims):
        raise ValueError("Candidate claim sets differ from data")
    for claim in claims:
        if first_candidates[claim]["connected"] != ranked_candidates[claim]["connected"]:
            raise ValueError(f"Connected paths differ at {claim!r}")

    # Exclude claims whose KG search was interrupted when a report is given.
    uncapped = [i for i, claim in enumerate(claims) if claim not in limited]
    for group_name, ids, wanted in (
        ("MULTI-HOP RESCUED", [i for i in uncapped if types[i] == 1], "rescued"),
        ("CONJ FALSE HARMED", [i for i in uncapped if types[i] == 2 and labels[i] == 0], "harmed"),
    ):
        if wanted == "rescued":
            flips = [i for i in ids if first[i] != labels[i] and ranked[i] == labels[i]]
        else:
            flips = [i for i in ids if first[i] == labels[i] and ranked[i] != labels[i]]
        print(f"\n{group_name}: {len(flips)} claims; showing up to {args.examples}")
        for i in flips[:args.examples]:
            claim = claims[i]
            old_paths = first_candidates[claim]["walkable"]
            new_paths = ranked_candidates[claim]["walkable"]
            removed = [path for path in old_paths if path not in new_paths]
            added = [path for path in new_paths if path not in old_paths]
            claim_tokens = tokens(claim)
            print(f"  Claim: {claim}")
            print(f"    walkable first/ranked={len(old_paths)}/{len(new_paths)}; "
                  f"removed={len(removed)}; added={len(added)}")
            for label, paths in (("removed", removed[:2]), ("added", added[:2])):
                for path in paths:
                    print(f"    {label} score={path_score(claim_tokens, path)}: {path!r}")


if __name__ == "__main__":
    main()
