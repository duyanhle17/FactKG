"""Instantiate gold Evidence relation paths in the KG (train/dev only; test has no Evidence).

FactKG Evidence is {entity: [[r1, r2], [r3], ...]}: relation sequences, not concrete paths.
For each sequence we walk the KG from that entity:
  * "connected": walks that end in another claim entity (the gold bridge / direct edge)
  * "walkable" : walks that end elsewhere (near-miss: shows the real value, useful for False)
Used for the P1 oracle (upper bound) and later as supervision for a bridge scorer.

  python gold_bridge.py --kg KG/dbpedia_2015_undirected_light.pickle \
      --factkg DATA/factkg_dev.pickle --output OUT/gold_bridges_dev.pkl
"""
from __future__ import annotations

import argparse
import time
from collections import Counter

from common import canonical_path, five_group, label_of, load_factkg, read_pickle, write_json, write_pickle


def walk(kg, start, rels, max_frontier):
    """All paths start -rels[0]-> ... ; returns (paths, truncated). Paths = [e0, r1, e1, ...]."""
    frontier = [[start]]
    truncated = False
    for rel in rels:
        nxt = []
        for p in frontier:
            for t in kg.get(p[-1], {}).get(rel, []):
                if t in p[0::2]:
                    continue
                nxt.append(p + [rel, t])
                if len(nxt) >= max_frontier:
                    truncated = True
                    break
            if truncated:
                break
        frontier = nxt
        if not frontier:
            break
    return [p for p in frontier if len(p) == 2 * len(rels) + 1], truncated


def instantiate(kg, record, opts):
    ents = list(dict.fromkeys(record["Entity_set"]))
    evidence = record.get("Evidence") or {}
    connected, walkable, seen = [], [], set()
    stats = Counter()
    for e, seqs in evidence.items():
        for seq in seqs:
            if not seq:
                continue
            paths, trunc = walk(kg, e, seq, opts.max_frontier)
            stats["truncated"] += trunc
            hits = [p for p in paths if p[-1] in ents and p[-1] != e]
            stats[f"seq_len_{len(seq)}"] += 1
            stats["seq_with_hit"] += bool(hits)
            stats["seq_no_path"] += not paths
            for p in hits[:opts.max_per_seq]:
                key = canonical_path(p)
                if key not in seen:
                    seen.add(key)
                    connected.append(p)
            if not hits:
                for p in paths[:opts.max_per_seq]:
                    key = canonical_path(p)
                    if key not in seen:
                        seen.add(key)
                        walkable.append(p)
    return {"connected": connected, "walkable": walkable, "stats": dict(stats)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kg", required=True)
    ap.add_argument("--factkg", required=True, help="train or dev pickle (must contain Evidence)")
    ap.add_argument("--output", required=True)
    ap.add_argument("--max-frontier", type=int, default=20_000)
    ap.add_argument("--max-per-seq", type=int, default=3)
    ap.add_argument("--limit", type=int, default=None)
    opts = ap.parse_args()

    rows = load_factkg(opts.factkg)
    if opts.limit:
        rows = rows[:opts.limit]
    t0 = time.time()
    kg = read_pickle(opts.kg)
    print(f"KG loaded in {time.time() - t0:.0f}s", flush=True)
    out, summary = {}, Counter()
    for i, (claim, rec) in enumerate(rows):
        res = instantiate(kg, rec, opts)
        out[claim] = res
        g, lab = five_group(rec["types"]), "True" if label_of(rec) else "False"
        summary[f"{g}/{lab}/n"] += 1
        summary[f"{g}/{lab}/has_connected"] += bool(res["connected"])
        summary[f"{g}/{lab}/only_walkable"] += (not res["connected"]) and bool(res["walkable"])
        summary[f"{g}/{lab}/nothing"] += not (res["connected"] or res["walkable"])
        if (i + 1) % 2000 == 0:
            print(f"{i + 1}/{len(rows)}", flush=True)
    write_pickle(out, opts.output)
    write_json(dict(sorted(summary.items())), str(opts.output) + ".summary.json")
    print(f"wrote {opts.output}")


if __name__ == "__main__":
    main()
