import argparse
import pickle
import re
from typing import Dict, List, Tuple


def parse_args():
    parser = argparse.ArgumentParser(description="Prune noisy candidate paths for FactKG classifier")
    parser.add_argument("--input_path", required=True, type=str, help="Input candid_paths .bin")
    parser.add_argument("--output_path", required=True, type=str, help="Output pruned candid_paths .bin")
    parser.add_argument("--top_connected", default=8, type=int, help="Top connected paths kept per claim")
    parser.add_argument("--top_walkable", default=8, type=int, help="Top walkable paths kept per claim")
    parser.add_argument("--max_hops", default=3, type=int, help="Drop paths above this hop length")
    parser.add_argument(
        "--hub_relations",
        default="type,category,subject,year,date,time,name,label",
        type=str,
        help="Comma-separated relation fragments considered hub/noisy",
    )
    parser.add_argument("--keep_at_least_one", action="store_true", help="Keep one best path even if score <= 0")
    return parser.parse_args()


def norm_text(text: str) -> str:
    text = text.replace("_", " ")
    text = text.lower()
    return text


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", norm_text(text))


def path_hops(path: List[str]) -> int:
    return max((len(path) - 1) // 2, 0)


def relation_tokens(path: List[str]) -> List[str]:
    return path[1::2] if len(path) >= 2 else []


def node_tokens(path: List[str]) -> List[str]:
    return path[0::2] if len(path) >= 1 else []


def deduplicate_paths(paths: List[List[str]]) -> List[List[str]]:
    seen = set()
    out = []
    for p in paths:
        key = tuple(p)
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def score_path(path: List[str], claim_token_set: set, hub_fragments: List[str]) -> float:
    nodes = " ".join(node_tokens(path))
    rels = " ".join(relation_tokens(path))

    node_tok = set(tokenize(nodes))
    rel_tok = set(tokenize(rels))

    overlap_nodes = len(node_tok & claim_token_set)
    overlap_rels = len(rel_tok & claim_token_set)

    hub_penalty = 0.0
    for rel in relation_tokens(path):
        rel_norm = norm_text(rel)
        if any(hf in rel_norm for hf in hub_fragments):
            hub_penalty += 0.5

    # Prefer claim-linked nodes, then relations, then shorter paths.
    return 1.5 * overlap_nodes + 1.0 * overlap_rels - 0.1 * path_hops(path) - hub_penalty


def prune_group(
    paths: List[List[str]],
    claim_token_set: set,
    top_k: int,
    max_hops: int,
    hub_fragments: List[str],
    keep_at_least_one: bool,
) -> List[List[str]]:
    if top_k <= 0:
        return []

    deduped = deduplicate_paths(paths)
    filtered = [p for p in deduped if path_hops(p) <= max_hops]

    scored: List[Tuple[float, List[str]]] = []
    for p in filtered:
        scored.append((score_path(p, claim_token_set, hub_fragments), p))

    scored.sort(key=lambda x: x[0], reverse=True)

    kept = [p for s, p in scored if s > 0][:top_k]
    if keep_at_least_one and not kept and scored:
        kept = [scored[0][1]]

    return kept


def prune_candids(
    candids: Dict[str, Dict[str, List[List[str]]]],
    top_connected: int,
    top_walkable: int,
    max_hops: int,
    hub_fragments: List[str],
    keep_at_least_one: bool,
):
    output = {}
    for claim, item in candids.items():
        claim_token_set = set(tokenize(claim))
        connected = item.get("connected", [])
        walkable = item.get("walkable", [])

        pruned_connected = prune_group(
            connected,
            claim_token_set,
            top_connected,
            max_hops,
            hub_fragments,
            keep_at_least_one,
        )
        pruned_walkable = prune_group(
            walkable,
            claim_token_set,
            top_walkable,
            max_hops,
            hub_fragments,
            keep_at_least_one,
        )

        output[claim] = {
            "connected": pruned_connected,
            "walkable": pruned_walkable,
        }
    return output


def main():
    args = parse_args()
    hub_fragments = [x.strip().lower() for x in args.hub_relations.split(",") if x.strip()]

    with open(args.input_path, "rb") as f:
        candids = pickle.load(f)

    if not isinstance(candids, dict):
        raise ValueError("Expected dict format: claim -> {connected, walkable}")

    pruned = prune_candids(
        candids,
        top_connected=args.top_connected,
        top_walkable=args.top_walkable,
        max_hops=args.max_hops,
        hub_fragments=hub_fragments,
        keep_at_least_one=args.keep_at_least_one,
    )

    with open(args.output_path, "wb") as f:
        pickle.dump(pruned, f)

    print(f"Saved pruned candidates to: {args.output_path}")
    print(f"Claims: {len(pruned)}")


if __name__ == "__main__":
    main()
