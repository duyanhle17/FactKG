"""Rank existing R3 walkable paths against each claim, then keep the top N.

This is a label-free, deterministic diagnostic. It does not search the KG,
change connected paths, train V4, or use gold Evidence/reasoning types.
The score is deliberately simple: overlap with path relations counts twice,
and overlap with non-start path entities counts once. Ties keep R3 order.
"""

import argparse
import pickle
import re
import unicodedata
from pathlib import Path


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "have", "in", "is", "it", "of", "on", "or", "that", "the",
    "this", "to", "was", "were", "which", "who", "with",
}


def tokens(value):
    value = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", str(value))
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return {
        word for word in re.findall(r"[a-z0-9]+", value.lower())
        if len(word) >= 3 and word not in STOPWORDS
    }


def path_score(claim_tokens, path):
    # A KG path alternates entity, relation, entity, ... . The start entity
    # appears in almost every path and is deliberately excluded from scoring.
    relations = set().union(*(tokens(value) for value in path[1::2]))
    entities = set().union(*(tokens(value) for value in path[2::2]))
    return 2 * len(claim_tokens & relations) + len(claim_tokens & entities)


def rank_walkable(claim, paths, cap):
    claim_tokens = tokens(claim)
    scored = [(path_score(claim_tokens, path), index, path)
              for index, path in enumerate(paths)]
    scored.sort(key=lambda row: (-row[0], row[1]))
    return [path for _, _, path in scored[:cap]]


def ranked_candidates(candidates, cap):
    result = {}
    for claim, row in candidates.items():
        updated = dict(row)
        updated["walkable"] = rank_walkable(claim, row["walkable"], cap)
        result[claim] = updated
    return result


def visible_paths(row, max_paths):
    return (list(row["connected"]) + list(row["walkable"]))[:max_paths]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cap", type=int, default=5)
    parser.add_argument("--max_paths", type=int, default=32)
    parser.add_argument("--expected_claims", type=int)
    args = parser.parse_args()
    if args.cap < 0 or args.max_paths < 1:
        parser.error("--cap must be nonnegative and --max_paths positive")

    with args.input.open("rb") as handle:
        candidates = pickle.load(handle)
    if args.expected_claims is not None and len(candidates) != args.expected_claims:
        raise ValueError(f"Expected {args.expected_claims} claims, found {len(candidates)}")
    if not all("connected" in row and "walkable" in row
               for row in candidates.values()):
        raise ValueError("Every candidate must have connected and walkable groups")

    ranked = ranked_candidates(candidates, args.cap)
    changed_from_first = 0
    changed_from_full = 0
    for claim, original in candidates.items():
        first = {
            "connected": original["connected"],
            "walkable": original["walkable"][:args.cap],
        }
        changed_from_first += visible_paths(first, args.max_paths) != visible_paths(
            ranked[claim], args.max_paths
        )
        changed_from_full += visible_paths(original, args.max_paths) != visible_paths(
            ranked[claim], args.max_paths
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as handle:
        pickle.dump(ranked, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"Output: {args.output}; claims={len(ranked)}")
    print(f"V4 input differs from first-{args.cap}: {changed_from_first}")
    print(f"V4 input differs from full R3: {changed_from_full}")


if __name__ == "__main__":
    main()
