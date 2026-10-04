"""Compare dev top-5/top-10 relation coverage for true Conjunction claims.

This is a retrieval diagnostic, not R3 path recall or classifier accuracy.
It reads existing predictions and gold Evidence; it does not train models or
traverse the KG. Run ``python audit_relation_topk_conjunction.py --help``.
"""

import argparse
import json
import pickle
import random
from collections import Counter
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dev_data", required=True, type=Path)
    parser.add_argument("--top5_json", required=True, type=Path)
    parser.add_argument("--top10_json", required=True, type=Path)
    parser.add_argument("--hop_json", required=True, type=Path)
    parser.add_argument("--output_dir", required=True, type=Path)
    parser.add_argument("--sample_size", type=int, default=20)
    parser.add_argument(
        "--r3_sample_size", type=int, default=5,
        help="Small H=1 nested-top5 subset for optional R3 comparison; 0 disables it",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.sample_size < 1 or args.r3_sample_size < 0:
        parser.error("--sample_size must be positive and --r3_sample_size nonnegative")
    return args


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def index_predictions(document, value_key):
    """Read the pandas column-oriented JSON written by FactKG predictors."""
    claims = document["claims"]
    values = document[value_key]
    if set(claims) != set(values):
        raise ValueError(f"JSON claims/{value_key} indices differ")
    by_claim = {claim: values[index] for index, claim in claims.items()}
    if len(by_claim) != len(claims):
        raise ValueError("Duplicate claims in prediction JSON")
    return by_claim


def is_true_conjunction(example):
    label = example["Label"]
    if isinstance(label, (tuple, list)):
        if len(label) != 1:
            raise ValueError(f"Expected one label, got {label!r}")
        label = label[0]
    return bool(label) and "multi claim" in example["types"]


def is_classifier_conjunction(example):
    """Follow baseline.py's tag precedence for the Conjunction score bucket."""
    return "multi claim" in example["types"] and not any(
        tag in example["types"] for tag in ("negation", "num1", "multi hop")
    )


def gold_groups(example):
    """Match earlier audit: ignore empty Evidence keys, not nonempty keys."""
    groups = {}
    for key, paths in example["Evidence"].items():
        if paths:
            groups[str(key)] = [tuple(path) for path in paths if path]
    return groups


def coverage(groups, relations, hop):
    relations = set(relations)
    chains = [chain for paths in groups.values() for chain in paths]
    if not chains:
        raise ValueError("Cannot score claim without gold chains")
    matched = {
        key: [chain for chain in paths if len(chain) <= hop and set(chain) <= relations]
        for key, paths in groups.items()
    }
    return {
        "all_relations": set(rel for chain in chains for rel in chain) <= relations,
        "any_chain": any(matched.values()),
        "each_Evidence_key": all(matched.values()),
        "matched": matched,
    }


def relation_family(relation):
    """Treat r and ~r as one family for sampling, not as proven KG paths."""
    return relation[1:] if relation.startswith("~") else relation


def newly_covered_gold_families(groups, top5, top10, hop):
    gold = {
        relation_family(relation)
        for paths in groups.values()
        for chain in paths if len(chain) <= hop
        for relation in chain
    }
    old = {relation_family(relation) for relation in top5}
    new = {relation_family(relation) for relation in top10}
    return sorted((new - old) & gold)


def main():
    args = parse_args()
    with args.dev_data.open("rb") as handle:
        dev = pickle.load(handle)
    top5 = index_predictions(load_json(args.top5_json), "output")
    top10 = index_predictions(load_json(args.top10_json), "output")
    hops = index_predictions(load_json(args.hop_json), "predict")

    if set(top5) != set(top10):
        raise ValueError(
            f"Different claim sets: only top5={len(set(top5) - set(top10))}, "
            f"only top10={len(set(top10) - set(top5))}"
        )
    prefix_count = sum(top5[claim] == top10[claim][:5] for claim in top5)
    subset_count = sum(set(top5[claim]) <= set(top10[claim]) for claim in top5)
    rank_mismatch_examples = [
        {"claim": claim, "top5": top5[claim], "top10": top10[claim]}
        for claim in top5 if top5[claim] != top10[claim][:5]
    ][:5]
    set_mismatch_examples = [
        {"claim": claim, "top5": top5[claim], "top10": top10[claim]}
        for claim in top5 if not set(top5[claim]) <= set(top10[claim])
    ][:5]

    totals = Counter()
    recovered = []
    for claim, example in dev.items():
        if not is_true_conjunction(example):
            continue
        groups = gold_groups(example)
        if not groups:
            continue
        if claim not in top5 or claim not in hops:
            raise KeyError(f"Missing prediction for dev claim: {claim!r}")
        hop = int(hops[claim])
        old = coverage(groups, top5[claim], hop)
        new = coverage(groups, top10[claim], hop)
        novel_families = newly_covered_gold_families(
            groups, top5[claim], top10[claim], hop
        )
        totals["claims"] += 1
        totals["claims_in_classifier_conjunction_bucket"] += is_classifier_conjunction(example)
        totals["gained_gold_relation_family"] += bool(novel_families)
        for metric in ("all_relations", "any_chain", "each_Evidence_key"):
            totals[f"top5_{metric}"] += old[metric]
            totals[f"top10_{metric}"] += new[metric]
            totals[f"gained_{metric}"] += not old[metric] and new[metric]
            totals[f"lost_{metric}"] += old[metric] and not new[metric]
        if not old["each_Evidence_key"] and new["each_Evidence_key"]:
            totals["gained_each_key_with_new_family"] += bool(novel_families)
            if is_classifier_conjunction(example):
                totals["gained_each_key_in_classifier_conjunction_bucket"] += 1
            recovered.append((claim, example, groups, hop, old, new, novel_families))

    if not totals["claims"]:
        raise ValueError("No true Conjunction dev claims with Evidence were found")
    rng = random.Random(args.seed)
    rng.shuffle(recovered)
    # Review genuinely new relation families first; inverse-only additions
    # often repeat a fact already reachable from another claim entity.
    recovered.sort(key=lambda case: not case[6])
    selected = []
    seen_entity_sets = Counter()
    for case in recovered:
        signature = tuple(sorted(map(str, case[1].get("Entity_set", ()))))
        if seen_entity_sets[signature] >= 2:
            continue
        seen_entity_sets[signature] += 1
        selected.append(case)
        if len(selected) == args.sample_size:
            break

    # Require predicted H=1 for the optional KG traversal: top-10 with H>=2
    # can hit the same combinatorial hub expansion that stalled full-dev R3.
    r3_selected = []
    r3_signatures = Counter()
    for case in recovered if args.r3_sample_size else ():
        claim, example, _, hop, _, _, novel_families = case
        if not novel_families:
            continue
        if not set(top5[claim]) <= set(top10[claim]):
            continue
        if hop != 1 or not is_classifier_conjunction(example):
            continue
        signature = tuple(sorted(map(str, example.get("Entity_set", ()))))
        if r3_signatures[signature] >= 1:
            continue
        r3_signatures[signature] += 1
        r3_selected.append(case)
        if len(r3_selected) == args.r3_sample_size:
            break

    summary = {
        "prediction_claims": len(top5),
        "top5_is_prefix_of_top10": prefix_count,
        "top5_set_is_subset_of_top10": subset_count,
        "rank_mismatch_examples": rank_mismatch_examples,
        "set_mismatch_examples": set_mismatch_examples,
        "raw_multi_claim_true_with_evidence": totals["claims"],
        "true_conjunction_with_evidence": totals["claims"],
        "sample_size": len(selected),
        "r3_sample_size": len(r3_selected),
        "counts": dict(totals),
        "note": (
            "The 1970-style totals use the raw multi-claim tag; see "
            "claims_in_classifier_conjunction_bucket for baseline.py's exclusive "
            "Conjunction category. Evidence-key coverage is a proxy, not proof "
            "or clause recall. Relation families ignore ~ direction only for "
            "sample prioritization, not as a proof of KG reachability. "
            "No KG traversal or classifier inference was performed."
        ),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "topk_summary.json"
    cases_path = args.output_dir / "recovered_cases.md"
    subset_dir = args.output_dir / "r3_subset"
    if summary_path.exists() or cases_path.exists() or subset_dir.exists():
        raise FileExistsError("Output exists; choose a new --output_dir")
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)

    with cases_path.open("w", encoding="utf-8") as handle:
        handle.write("# Dev Conjunction True: top-10 recovers Evidence-key coverage\n\n")
        handle.write(
            "These are diagnostic examples, not proven recovered clauses or model scores.\n\n"
        )
        for number, (claim, example, groups, hop, old, new, novel_families) in enumerate(selected, 1):
            five = top5[claim]
            ten = top10[claim]
            added = [relation for relation in ten if relation not in set(five)]
            handle.write(f"## {number}. {claim}\n\n")
            handle.write(f"- Entities: `{example.get('Entity_set', [])!r}`\n")
            handle.write(f"- H: `{hop}`\n")
            handle.write(f"- Top-5: `{five!r}`\n")
            handle.write(f"- Top-10: `{ten!r}`\n")
            handle.write(f"- Relations added: `{added!r}`\n")
            handle.write(f"- Newly covered gold relation families: `{novel_families!r}`\n")
            for key, paths in groups.items():
                handle.write(f"- Evidence key `{key}`: chains `{paths!r}`; ")
                handle.write(
                    f"matched top-5 `{old['matched'][key]!r}`, "
                    f"top-10 `{new['matched'][key]!r}`\n"
                )
            handle.write("- Manual check: which keys are required claim clauses, ")
            handle.write("and do added relations lead to real KG paths?\n\n")

    if r3_selected:
        subset_dir.mkdir()
        subset_data = subset_dir / "data"
        subset_data.mkdir()
        subset = {
            claim: {
                "Entity_set": example["Entity_set"],
                "Label": example["Label"],
                "types": example["types"],
            }
            for claim, example, _, _, _, _, _ in r3_selected
        }
        # Deliberately omit Evidence from the test-style subset: R3 must use
        # only predicted relations/H and the KG, never dev gold relations.
        with (subset_data / "factkg_test.pickle").open("wb") as handle:
            pickle.dump(subset, handle)
        for name, value_key, values in (
            ("top5_subset.json", "output", top5),
            ("top10_subset.json", "output", top10),
            ("hop_subset.json", "predict", hops),
        ):
            document = {
                "claims": {str(i): claim for i, claim in enumerate(subset)},
                value_key: {
                    str(i): values[claim] for i, claim in enumerate(subset)
                },
            }
            with (subset_dir / name).open("w", encoding="utf-8") as handle:
                json.dump(document, handle, ensure_ascii=False, indent=2)
        with (subset_dir / "claims.md").open("w", encoding="utf-8") as handle:
            handle.write("# Small predicted-H=1 Conjunction subset for R3\n\n")
            handle.write("Dev gold Evidence is excluded from the test-style input.\n\n")
            handle.write("Each claim has a newly covered gold relation family, ")
            handle.write("but this does not establish a new KG proof.\n\n")
            for number, (claim, _, _, _, _, _, families) in enumerate(r3_selected, 1):
                handle.write(f"{number}. {claim} — new families: `{families!r}`\n")

    print(f"Prediction claims: {len(top5)}")
    print(f"Top-5 exact prefix of top-10: {prefix_count}/{len(top5)}")
    print(f"Top-5 relation set contained in top-10: {subset_count}/{len(top5)}")
    print(f"True dev claims tagged multi claim with Evidence: {totals['claims']}")
    print(
        "Of these, baseline.py Conjunction bucket: "
        f"{totals['claims_in_classifier_conjunction_bucket']}"
    )
    for metric in ("all_relations", "any_chain", "each_Evidence_key"):
        print(
            f"{metric}: top5={totals[f'top5_{metric}']}, "
            f"top10={totals[f'top10_{metric}']}, "
            f"gained={totals[f'gained_{metric}']}, "
            f"lost={totals[f'lost_{metric}']}"
        )
    print(f"Sampled recovered claims: {len(selected)}")
    print(
        "Each-key gains with new gold relation family: "
        f"{totals['gained_each_key_with_new_family']}"
    )
    print(f"Optional R3 H=1 subset: {len(r3_selected)} claims at {subset_dir}")
    print(f"Summary: {summary_path}")
    print(f"Cases: {cases_path}")


if __name__ == "__main__":
    main()
