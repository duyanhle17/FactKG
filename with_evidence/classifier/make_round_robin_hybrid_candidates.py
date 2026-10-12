"""Replace only DFS expansion-limited claims with round-robin candidates.

This is a diagnostic artifact, not a new R3 training set. It keeps every
unlimited DFS claim unchanged so a fixed-checkpoint V4 comparison isolates the
effect of changing the search schedule on claims that hit the DFS state cap.
"""

import argparse
import json
import pickle
from pathlib import Path


def read_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_pickle(path):
    with path.open("rb") as handle:
        return pickle.load(handle)


def visible(row, max_paths):
    return (row["connected"] + row["walkable"])[:max_paths]


def build_hybrid(old, new, old_report, new_report, old_manifest, new_manifest, max_paths):
    if list(old) != list(new):
        raise ValueError("DFS and round-robin candidate claim order differs")
    for key in (
        "retrieval_mode", "n_candid", "include_shorter_paths", "relation_budget",
        "dominance_audit", "store_max_paths", "max_expanded_states",
        "test_only_candidates",
    ):
        if old_report["config"].get(key) != new_report["config"].get(key):
            raise ValueError(f"DFS and round-robin retrieval config differs: {key}")
    if old_report["config"].get("search_schedule", "dfs") != "dfs":
        raise ValueError("Old candidate report is not DFS")
    if new_report["config"].get("search_schedule") != "round_robin":
        raise ValueError("New candidate report is not round-robin")
    if (old_manifest["inputs"]["data_dir"]["path"]
            != new_manifest["inputs"]["data_dir"]["path"]):
        raise ValueError("DFS and round-robin data directories differ")
    for key in ("kg", "relation_predictions", "hop_predictions"):
        if old_manifest["inputs"][key] != new_manifest["inputs"][key]:
            raise ValueError(f"DFS and round-robin inputs differ: {key}")
    limited = set(old_report["splits"]["test"]["expansion_limited_claims"])
    if not limited <= set(old):
        raise ValueError("DFS report contains claims absent from candidates")

    hybrid = {claim: new[claim] if claim in limited else old[claim] for claim in old}
    changed = [
        claim for claim in limited
        if visible(old[claim], max_paths) != visible(hybrid[claim], max_paths)
    ]
    summary = {
        "claims": len(hybrid),
        "dfs_expansion_limited": len(limited),
        "v4_inputs_changed": len(changed),
        "changed_outside_dfs_limited": sum(
            visible(old[claim], max_paths) != visible(hybrid[claim], max_paths)
            for claim in old if claim not in limited
        ),
        "changed_with_more_connected": sum(
            len(hybrid[claim]["connected"]) > len(old[claim]["connected"])
            for claim in changed
        ),
        "changed_with_fewer_connected": sum(
            len(hybrid[claim]["connected"]) < len(old[claim]["connected"])
            for claim in changed
        ),
    }
    return hybrid, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old_candidates", required=True, type=Path)
    parser.add_argument("--new_candidates", required=True, type=Path)
    parser.add_argument("--old_report", required=True, type=Path)
    parser.add_argument("--new_report", required=True, type=Path)
    parser.add_argument("--old_manifest", required=True, type=Path)
    parser.add_argument("--new_manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max_paths", type=int, default=32)
    args = parser.parse_args()
    if args.max_paths < 1:
        parser.error("--max_paths must be positive")
    if args.output.exists():
        parser.error(f"Output already exists: {args.output}")

    hybrid, summary = build_hybrid(
        read_pickle(args.old_candidates),
        read_pickle(args.new_candidates),
        read_json(args.old_report),
        read_json(args.new_report),
        read_json(args.old_manifest),
        read_json(args.new_manifest),
        args.max_paths,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as handle:
        pickle.dump(hybrid, handle)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Hybrid candidates: {args.output}")


if __name__ == "__main__":
    main()
