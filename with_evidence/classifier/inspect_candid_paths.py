import argparse
import pickle
from collections import Counter


def parse_args():
    parser = argparse.ArgumentParser(description="Inspect candidate path bins used by baseline classifier")
    parser.add_argument("--candid_path", required=True, type=str, help="Path to candid_paths .bin file")
    parser.add_argument("--max_examples", default=3, type=int, help="Number of sample claims to print")
    parser.add_argument("--top_relations", default=20, type=int, help="Number of top frequent relations to print")
    return parser.parse_args()


def relation_tokens_from_path(path):
    # Path format is usually: [ent, rel, ent, rel, ent, ...]
    return path[1::2] if len(path) >= 2 else []


def summarize(candids):
    n_claims = len(candids)
    connected_counts = []
    walkable_counts = []
    path_hops = []
    relation_counter = Counter()

    for claim, item in candids.items():
        connected = item.get("connected", [])
        walkable = item.get("walkable", [])
        connected_counts.append(len(connected))
        walkable_counts.append(len(walkable))

        for p in connected + walkable:
            hops = max((len(p) - 1) // 2, 0)
            path_hops.append(hops)
            relation_counter.update(relation_tokens_from_path(p))

    def safe_avg(values):
        return (sum(values) / len(values)) if values else 0.0

    summary = {
        "n_claims": n_claims,
        "avg_connected_per_claim": safe_avg(connected_counts),
        "avg_walkable_per_claim": safe_avg(walkable_counts),
        "max_connected_per_claim": max(connected_counts) if connected_counts else 0,
        "max_walkable_per_claim": max(walkable_counts) if walkable_counts else 0,
        "avg_hops_per_path": safe_avg(path_hops),
        "max_hops": max(path_hops) if path_hops else 0,
        "n_total_paths": len(path_hops),
        "relation_counter": relation_counter,
    }
    return summary


def print_samples(candids, max_examples):
    print("\n=== Sample claims ===")
    for i, (claim, item) in enumerate(candids.items()):
        if i >= max_examples:
            break
        connected = item.get("connected", [])
        walkable = item.get("walkable", [])
        print(f"\n[{i + 1}] Claim: {claim}")
        print(f"connected={len(connected)}, walkable={len(walkable)}")
        if connected:
            print(f"connected[0]: {connected[0]}")
        if walkable:
            print(f"walkable[0]: {walkable[0]}")


def main():
    args = parse_args()

    with open(args.candid_path, "rb") as f:
        candids = pickle.load(f)

    if not isinstance(candids, dict):
        raise ValueError("Expected candid bin to be a dict: claim -> {connected, walkable}")

    s = summarize(candids)

    print("=== Candidate Path Summary ===")
    print(f"claims: {s['n_claims']}")
    print(f"total_paths: {s['n_total_paths']}")
    print(f"avg_connected_per_claim: {s['avg_connected_per_claim']:.2f}")
    print(f"avg_walkable_per_claim: {s['avg_walkable_per_claim']:.2f}")
    print(f"max_connected_per_claim: {s['max_connected_per_claim']}")
    print(f"max_walkable_per_claim: {s['max_walkable_per_claim']}")
    print(f"avg_hops_per_path: {s['avg_hops_per_path']:.2f}")
    print(f"max_hops: {s['max_hops']}")

    print("\n=== Top relations ===")
    for rel, cnt in s["relation_counter"].most_common(args.top_relations):
        print(f"{rel}: {cnt}")

    print_samples(candids, args.max_examples)


if __name__ == "__main__":
    main()
