"""Build an upstream-format subgraph pickle with extra paths prepended to `connected` (P1).

The one-hop input is kept, extra paths go FIRST so they survive the 512-token cut.
Output keeps the upstream format (DataFrame with column `walked`), so both
fever_predict.py and upstream run_stuff.py/eval_five.py (via FACTKG_SUBGRAPHS_*_PATH)
can read it.

Sources:
  gold    : gold_bridge.py output (oracle; dev/train only)
  bridges : bridge_retrieval.py output, relation sequences ranked by a lexical
            relation-claim score (no learning, no gold information)

  python build_injected.py --factkg DATA/factkg_dev.pickle \
      --subgraphs SUBGRAPHS/subgraphs_one_hop_val.pkl \
      --source gold --source-file OUT/gold_bridges_dev.pkl --groups multi-hop \
      --output OUT/inj_gold_multihop_val.pkl
"""
from __future__ import annotations

import argparse
import re
from collections import Counter

import pandas as pd

from common import (GROUPS, canonical_path, five_group, load_factkg, read_pickle, write_json,
                    write_pickle)

STOP = {"the", "a", "an", "of", "in", "is", "was", "and", "to", "by", "for", "on", "at", "with",
        "as", "it", "its", "that", "which", "who", "has", "had", "be", "from", "are", "were"}


def rel_tokens(rel):
    rel = rel.lstrip("~")
    return [t.lower() for t in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", rel)]


def claim_tokens(claim):
    return {t for t in re.findall(r"[a-z]+", claim.lower()) if t not in STOP}


def lexical_score(seq, ctoks):
    score = 0
    for rel in seq:
        for t in rel_tokens(rel):
            if t in STOP:
                continue
            if t in ctoks or any(len(t) >= 4 and c[:4] == t[:4] for c in ctoks):
                score += 1
    return score


def bridge_paths(entry, claim, max_paths, skip_direct):
    ctoks = claim_tokens(claim)
    cands = []
    for pair in entry["pairs"]:
        if skip_direct and pair["direct"]:
            continue
        a, b = pair["a"], pair["b"]
        for seq, slot in pair["two_hop"].items():
            cands.append((lexical_score(seq, ctoks), slot["count"], [[a, seq[0], x, seq[1], b]
                                                                    for x in slot["examples"]]))
        for seq, slot in pair["three_hop"].items():
            cands.append((lexical_score(seq, ctoks), slot["count"],
                          [[a, seq[0], x, seq[1], y, seq[2], b] for x, y in slot["examples"]]))
    cands.sort(key=lambda c: (-c[0], c[1]))
    out = []
    for _, _, paths in cands:
        for p in paths[:1]:  # one instantiation per relation sequence keeps diversity
            out.append(p)
            if len(out) >= max_paths:
                return out
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--factkg", required=True)
    ap.add_argument("--subgraphs", required=True, help="base one-hop subgraph pickle")
    ap.add_argument("--source", choices=["gold", "bridges"], required=True)
    ap.add_argument("--source-file", required=True)
    ap.add_argument("--groups", default="all", help="comma list of five groups to inject, or 'all'."
                    " NOTE: selecting by group uses FactKG type metadata -> diagnostic only")
    ap.add_argument("--max-paths", type=int, default=5)
    ap.add_argument("--nearmiss", action="store_true", help="gold: also add near-miss walks")
    ap.add_argument("--keep-direct-pairs", action="store_true",
                    help="bridges: also add bridges for pairs that already have a direct edge")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    groups = set(GROUPS) if args.groups == "all" else set(args.groups.split(","))
    unknown = groups - set(GROUPS)
    if unknown:
        ap.error(f"unknown groups {unknown}")
    rows = load_factkg(args.factkg)
    base = read_pickle(args.subgraphs)
    if len(base) != len(rows):
        raise ValueError("subgraph file and factkg pickle differ in length")
    source = read_pickle(args.source_file)

    new_walked, stats = [], Counter()
    for (claim, rec), w in zip(rows, base["walked"]):
        conn, walk = list(w["connected"]), list(w["walkable"])
        g = five_group(rec["types"])
        extra = []
        if g in groups and claim in source:
            if args.source == "gold":
                extra = list(source[claim]["connected"])
                if args.nearmiss:
                    extra += list(source[claim]["walkable"])
                extra = extra[:args.max_paths]
            else:
                extra = bridge_paths(source[claim], claim, args.max_paths, not args.keep_direct_pairs)
        elif g in groups:
            stats["missing_in_source"] += 1
        have = {canonical_path(p) for p in conn}
        extra = [p for p in extra if canonical_path(p) not in have]
        stats[f"{g}/claims_injected"] += bool(extra)
        stats[f"{g}/paths_injected"] += len(extra)
        new_walked.append({"connected": extra + conn, "walkable": walk})

    out = pd.DataFrame({"walked": new_walked})
    if "subgraph" in getattr(base, "columns", []):
        out.insert(0, "subgraph", list(base["subgraph"]))
    write_pickle(out, args.output)
    write_json(dict(sorted(stats.items())) | {"args": vars(args)}, args.output + ".stats.json")
    print(dict(sorted(stats.items())))


if __name__ == "__main__":
    main()
