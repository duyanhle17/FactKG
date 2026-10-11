"""Create test-style candidate variants by keeping the first N walkable paths.

Connected paths and claim order are preserved. This script never rebuilds paths
from the KG and refuses to overwrite an existing candidate file.
"""

import argparse
import pickle
from pathlib import Path


def capped_candidates(candidates, cap):
    result = {}
    for claim, row in candidates.items():
        updated = dict(row)
        updated["walkable"] = list(row["walkable"][:cap])
        result[claim] = updated
    return result


def visible_paths(row, max_paths):
    return (list(row["connected"]) + list(row["walkable"]))[:max_paths]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output_dir", required=True, type=Path)
    parser.add_argument("--caps", required=True, nargs="+", type=int)
    parser.add_argument("--expected_claims", type=int)
    parser.add_argument("--max_paths", type=int, default=32)
    args = parser.parse_args()
    if any(cap < 0 for cap in args.caps) or len(set(args.caps)) != len(args.caps):
        parser.error("--caps must be distinct nonnegative integers")
    if args.max_paths < 1:
        parser.error("--max_paths must be positive")

    with args.input.open("rb") as handle:
        candidates = pickle.load(handle)
    if args.expected_claims is not None and len(candidates) != args.expected_claims:
        raise ValueError(
            f"Expected {args.expected_claims} claims, found {len(candidates)}"
        )
    if not all("connected" in row and "walkable" in row for row in candidates.values()):
        raise ValueError("Every candidate must have connected and walkable groups")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        cap: args.output_dir / f"test_r3_walkable_{cap}.bin"
        for cap in args.caps
    }
    existing = [str(path) for path in outputs.values() if path.exists()]
    if existing:
        raise FileExistsError(f"Refusing to overwrite existing files: {existing}")
    for cap in args.caps:
        output = outputs[cap]
        capped = capped_candidates(candidates, cap)
        changed = sum(
            visible_paths(candidates[claim], args.max_paths)
            != visible_paths(capped[claim], args.max_paths)
            for claim in candidates
        )
        with output.open("xb") as handle:
            pickle.dump(capped, handle, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"walk{cap}: {output}; claims={len(capped)}; "
              f"V4 input changed for {changed} claims")


if __name__ == "__main__":
    main()
