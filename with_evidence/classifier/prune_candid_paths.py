"""
Phase 1.2 — Tail Trimming: chặt đuôi rác ở hop cuối nếu không liên quan Claim.
Phase 1.3 — Sub-path Expansion: phân mảnh path dài thành các nhánh con để chống lọt lưới.
"""
import argparse
import pickle
import re
from typing import Dict, List


def parse_args():
    parser = argparse.ArgumentParser(description="Prune noisy candidate paths for FactKG classifier")
    parser.add_argument("--input_path", required=True, type=str, help="Input candid_paths .bin")
    parser.add_argument("--output_path", required=True, type=str, help="Output pruned candid_paths .bin")
    parser.add_argument("--max_hops", default=3, type=int, help="Drop paths above this hop length")
    return parser.parse_args()


# ============================================================
# Utility helpers
# ============================================================

def norm_text(text: str) -> str:
    """Normalise a KG string for token comparison."""
    text = text.replace("_", " ")
    text = text.lower()
    return text


def tokenize(text: str) -> set:
    """Extract lowercase alphanumeric tokens from text."""
    return set(re.findall(r"[a-z0-9]+", norm_text(text)))


def path_hops(path: List[str]) -> int:
    """Count the number of hops in a path [E, R, E, R, E, ...]."""
    return max((len(path) - 1) // 2, 0)


def deduplicate_paths(paths: List[List[str]]) -> List[List[str]]:
    """Remove exact-duplicate paths."""
    seen = set()
    out = []
    for p in paths:
        key = tuple(p)
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


# ============================================================
# Phase 1.2 — Tail Trimming
# ============================================================

def trim_tail(path: List[str], claim_tokens: set) -> List[str]:
    """
    Repeatedly chop off the last hop (Relation + Entity) if neither the
    last relation nor the last entity shares any token with the claim.
    Stops when the path is down to 1-hop or the tail is relevant.

    Example:
        path = [E0, R1, E1, R2, E2, R3, E3]
        If tokenize(R3) ∩ claim_tokens == ∅  AND  tokenize(E3) ∩ claim_tokens == ∅:
            -> trim to [E0, R1, E1, R2, E2]
        Repeat check on the new tail.
    """
    while path_hops(path) > 1:
        # Last entity and last relation
        last_entity = path[-1]
        last_relation = path[-2]
        tail_tokens = tokenize(last_entity) | tokenize(last_relation)
        if tail_tokens & claim_tokens:
            # Tail is relevant — stop trimming
            break
        # Chop the last hop (2 elements: relation + entity)
        path = path[:-2]
    return path


# ============================================================
# Phase 1.3 — Sub-path Expansion
# ============================================================

def expand_subpaths(path: List[str]) -> List[List[str]]:
    """
    Given a path [E0, R1, E1, R2, E2, ...], generate ALL sub-paths
    starting from E0:
        [E0, R1, E1]
        [E0, R1, E1, R2, E2]
        [E0, R1, E1, R2, E2, R3, E3]   (= original)

    This ensures that even if the full path is too noisy for BERT,
    a shorter prefix containing the key evidence is still available.
    """
    subpaths = []
    hops = path_hops(path)
    for h in range(1, hops + 1):
        end_idx = 1 + h * 2  # E0 + h*(R+E) = 1 + 2h elements
        subpaths.append(path[:end_idx])
    return subpaths


# ============================================================
# Orchestration
# ============================================================

def prune_group(
    paths: List[List[str]],
    claim_tokens: set,
    max_hops: int,
) -> List[List[str]]:
    """Apply tail-trimming, sub-path expansion, hop filter, and dedup."""
    result = []
    for p in paths:
        # Skip paths that are too long even before trimming
        if path_hops(p) > max_hops:
            continue
        # Phase 1.2 — trim irrelevant tail
        trimmed = trim_tail(p, claim_tokens)
        # Phase 1.3 — expand into sub-paths (includes the trimmed path itself)
        subs = expand_subpaths(trimmed)
        result.extend(subs)

    # Deduplicate after expansion
    return deduplicate_paths(result)


def prune_candids(
    candids: Dict[str, Dict[str, List[List[str]]]],
    max_hops: int = 3,
    **_kwargs,  # accept legacy kwargs without crashing
):
    """
    Main entry point.  For each claim, prune its connected and walkable
    candidate paths using tail-trimming + sub-path expansion.
    """
    output = {}
    for claim, item in candids.items():
        claim_tokens = tokenize(claim)
        connected = item.get("connected", [])
        walkable = item.get("walkable", [])

        pruned_connected = prune_group(connected, claim_tokens, max_hops)
        pruned_walkable = prune_group(walkable, claim_tokens, max_hops)

        output[claim] = {
            "connected": pruned_connected,
            "walkable": pruned_walkable,
        }
    return output


def main():
    args = parse_args()

    with open(args.input_path, "rb") as f:
        candids = pickle.load(f)

    if not isinstance(candids, dict):
        raise ValueError("Expected dict format: claim -> {connected, walkable}")

    pruned = prune_candids(candids, max_hops=args.max_hops)

    with open(args.output_path, "wb") as f:
        pickle.dump(pruned, f)

    print(f"Saved pruned candidates to: {args.output_path}")
    print(f"Claims: {len(pruned)}")


if __name__ == "__main__":
    main()
