"""Prepare a small false-Conjunction dev subset for a top-5/top-10 R3 audit.

Selection uses dev labels for diagnosis, but the test-style subset passed to
R3/V4 contains no gold Evidence. It does not identify which clause is false.
"""

import argparse
import json
import pickle
import random
from collections import Counter
from pathlib import Path

from audit_relation_topk_conjunction import (
    gold_groups,
    index_predictions,
    is_classifier_conjunction,
    load_json,
    newly_covered_gold_families,
    relation_family,
)


def read_pickle(path):
    with path.open("rb") as handle:
        return pickle.load(handle)


def label_value(example):
    label = example["Label"]
    if isinstance(label, (list, tuple)):
        if len(label) != 1:
            raise ValueError(f"Expected one label, got {label!r}")
        label = label[0]
    return bool(label)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dev_data", required=True, type=Path)
    parser.add_argument("--positive_subset", required=True, type=Path)
    parser.add_argument("--top5_json", required=True, type=Path)
    parser.add_argument("--top10_json", required=True, type=Path)
    parser.add_argument("--hop_json", required=True, type=Path)
    parser.add_argument("--output_dir", required=True, type=Path)
    parser.add_argument("--max_samples", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.max_samples < 1:
        parser.error("--max_samples must be positive")

    dev = read_pickle(args.dev_data)
    positives = read_pickle(args.positive_subset)
    top5 = index_predictions(load_json(args.top5_json), "output")
    top10 = index_predictions(load_json(args.top10_json), "output")
    hops = index_predictions(load_json(args.hop_json), "predict")
    if set(top5) != set(top10):
        raise ValueError("Top-5 and top-10 prediction claim sets differ")

    positive_specs = []
    target_families = set()
    for claim, example in positives.items():
        if claim not in dev or claim not in top5 or claim not in hops:
            raise KeyError(f"Missing positive claim: {claim!r}")
        if not label_value(example) or not is_classifier_conjunction(example):
            raise ValueError(f"Positive subset has an invalid claim: {claim!r}")
        families = set(newly_covered_gold_families(
            gold_groups(dev[claim]), top5[claim], top10[claim], int(hops[claim])
        ))
        positive_specs.append((claim, set(map(str, example["Entity_set"])), families))
        target_families.update(families)
    if not target_families:
        raise ValueError("Positive subset has no newly covered gold relation family")

    eligible = []
    reasons = Counter()
    for claim, example in dev.items():
        if label_value(example) or not is_classifier_conjunction(example):
            continue
        if claim not in top5 or claim not in hops:
            raise KeyError(f"Missing prediction for false claim: {claim!r}")
        if int(hops[claim]) != 1 or len(example.get("Entity_set", ())) < 2:
            continue
        if not set(top5[claim]) <= set(top10[claim]):
            continue
        added_families = (
            {relation_family(relation) for relation in top10[claim]}
            - {relation_family(relation) for relation in top5[claim]}
        ) & target_families
        if not added_families:
            continue
        entities = set(map(str, example["Entity_set"]))
        # Match entity AND newly added relation family to the SAME positive
        # claim. A global union alone pairs unrelated facts (e.g. Hypermarcas
        # with leaderName, although its positive case needs location).
        matches = [
            (positive_claim, len(entities & positive_entities),
             sorted(added_families & positive_families))
            for positive_claim, positive_entities, positive_families in positive_specs
            if entities & positive_entities and added_families & positive_families
        ]
        if not matches:
            continue
        matches.sort(key=lambda row: (-row[1], row[0]))
        matched_positive, shared_entities, matched_families = matches[0]
        positive_entities = next(
            positive_set for positive_claim, positive_set, _ in positive_specs
            if positive_claim == matched_positive
        )
        priority = 0 if entities == positive_entities else 1
        reasons[f"eligible_priority_{priority}"] += 1
        eligible.append((
            priority, claim, example, matched_families, shared_entities,
            matched_positive,
        ))

    rng = random.Random(args.seed)
    rng.shuffle(eligible)
    eligible.sort(key=lambda row: (row[0], -row[4]))
    selected = []
    entity_signatures = Counter()
    for row in eligible:
        signature = tuple(sorted(map(str, row[2]["Entity_set"])))
        if entity_signatures[signature] >= 2:
            continue
        entity_signatures[signature] += 1
        selected.append(row)
        if len(selected) == args.max_samples:
            break

    args.output_dir.mkdir(parents=True, exist_ok=True)
    if any(args.output_dir.iterdir()):
        raise FileExistsError("Output directory is not empty; choose a new path")
    summary = {
        "positive_claims": len(positives),
        "target_relation_families": sorted(target_families),
        "eligible_false_claims": len(eligible),
        "selected_false_claims": len(selected),
        "eligible_by_priority": dict(reasons),
        "priority_meaning": {
            "0": "same entity set and added relation family as one positive claim",
            "1": "shares entity and added relation family with one positive claim",
        },
        "warning": (
            "These are false Conjunction controls, not verified one-true-one-false "
            "clause pairs. Inspect R3 paths and predictions before drawing conclusions."
        ),
    }
    with (args.output_dir / "selection_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
    with (args.output_dir / "claims.md").open("w", encoding="utf-8") as handle:
        handle.write("# False Conjunction diagnostic claims\n\n")
        handle.write("Selected by label, predicted H=1, and relation-family overlap. ")
        handle.write("Not verified clause-level negatives.\n\n")
        for i, (priority, claim, example, families, shared, matched_positive) in enumerate(selected, 1):
            handle.write(f"{i}. {claim}\n")
            handle.write(f"   - Entity_set: `{example['Entity_set']!r}`\n")
            handle.write(f"   - New target families: `{families!r}`; ")
            handle.write(f"priority={priority}; shared entities={shared}\n")
            handle.write(f"   - Matched positive claim: {matched_positive}\n")

    if selected:
        subset_data = args.output_dir / "data"
        subset_data.mkdir()
        test_examples = {
            claim: {
                "Entity_set": example["Entity_set"],
                "Label": example["Label"],
                "types": example["types"],
            }
            for _, claim, example, _, _, _ in selected
        }
        with (subset_data / "factkg_test.pickle").open("wb") as handle:
            pickle.dump(test_examples, handle)
        for name, field, predictions in (
            ("top5_subset.json", "output", top5),
            ("top10_subset.json", "output", top10),
            ("hop_subset.json", "predict", hops),
        ):
            document = {
                "claims": {str(i): claim for i, claim in enumerate(test_examples)},
                field: {
                    str(i): predictions[claim]
                    for i, claim in enumerate(test_examples)
                },
            }
            with (args.output_dir / name).open("w", encoding="utf-8") as handle:
                json.dump(document, handle, ensure_ascii=False, indent=2)

    print(f"Target relation families: {sorted(target_families)}")
    print(f"Eligible false Conjunction H=1 claims: {len(eligible)}")
    print(f"Selected: {len(selected)}")
    print(f"Output: {args.output_dir}")


if __name__ == "__main__":
    main()
