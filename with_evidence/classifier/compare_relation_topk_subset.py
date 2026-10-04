"""Compare top-5/top-10 R3 candidates and V4 predictions on the same dev subset.

The subset is diagnostic only; its accuracy is not a full-dev/test score.
"""

import argparse
import pickle
from pathlib import Path


def load_pickle(path):
    with path.open("rb") as handle:
        return pickle.load(handle)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--candidates5", required=True, type=Path)
    parser.add_argument("--candidates10", required=True, type=Path)
    parser.add_argument("--predictions5", required=True, type=Path)
    parser.add_argument("--predictions10", required=True, type=Path)
    parser.add_argument("--output_path", required=True, type=Path)
    args = parser.parse_args()

    if args.output_path.exists():
        raise FileExistsError(f"Output exists: {args.output_path}")
    database = load_pickle(args.data)
    candidates5 = load_pickle(args.candidates5)
    candidates10 = load_pickle(args.candidates10)
    predictions5 = load_pickle(args.predictions5)["prediction"]
    predictions10 = load_pickle(args.predictions10)["prediction"]
    claims = list(database)
    if set(claims) != set(candidates5) or set(claims) != set(candidates10):
        raise ValueError("Different claim sets in data and candidate artifacts")
    if len(predictions5) != len(claims) or len(predictions10) != len(claims):
        raise ValueError("Prediction count differs from subset claim count")

    lines = [
        "# Same V4 checkpoint: predicted top-5 versus top-10 candidates",
        "",
        "Small dev subset; do not report this as full-dev/test accuracy. ",
        "A path count or a changed label does not itself establish proof correctness.",
        "",
        "| Claim | Label | V4 top-5 | V4 top-10 | Paths top-5 | Paths top-10 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for i, claim in enumerate(claims):
        gold = database[claim]["Label"]
        if isinstance(gold, (tuple, list)):
            gold = gold[0]
        count5 = sum(len(candidates5[claim][key]) for key in ("connected", "walkable"))
        count10 = sum(len(candidates10[claim][key]) for key in ("connected", "walkable"))
        pred5 = int(predictions5[i])
        pred10 = int(predictions10[i])
        safe_claim = claim.replace("|", "&#124;")
        lines.append(
            f"| {safe_claim} | {int(gold)} | {pred5} | "
            f"{pred10} | {count5} | {count10} |"
        )
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Compared {len(claims)} claims; report: {args.output_path}")


if __name__ == "__main__":
    main()
