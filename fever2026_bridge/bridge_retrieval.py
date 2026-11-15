"""Exact bridge search between every pair of claim entities (needs the full DBpedia KG).

For each claim and each unordered pair (a, b) of Entity_set:
  * direct : relations r with b in KG[a][r]
  * 2-hop  : a -r1-> x -r2-> b  via N(a) ∩ N(b)  (meet in the middle, no relation predictor)
  * 3-hop  : a -r1-> x -r2-> y -r3-> b, expanded from the lower-degree side with a work
             budget; only when no 2-hop bridge exists (--three-hop if-no-2hop, default)
Bridges are grouped by relation sequence: {(r1, r2): {"count": n, "examples": [x, ...]}},
which keeps the file small even when a hub (country, year) yields thousands of bridges.

Resumable: results are written in shards of --shard-size claims; rerun the same command
to continue, then add --merge to write the final pickle.

  python bridge_retrieval.py --kg KG/dbpedia_2015_undirected_light.pickle \
      --factkg DATA/factkg_dev.pickle --work-dir OUT/bridges_dev_shards
  python bridge_retrieval.py ... --work-dir OUT/bridges_dev_shards --merge OUT/bridges_dev.pkl
"""
from __future__ import annotations

import argparse
import time
from itertools import combinations
from pathlib import Path

from common import inverse_relation, load_factkg, read_pickle, write_json, write_pickle


def neighbours(kg, e, max_degree):
    """x -> [relations r with x in KG[e][r]]; also returns (degree, truncated)."""
    out, deg, truncated = {}, 0, False
    for rel, tails in kg.get(e, {}).items():
        for x in tails:
            deg += 1
            if deg > max_degree:
                return out, deg, True
            out.setdefault(x, []).append(rel)
    return out, deg, truncated


def search_pair(kg, a, b, nb_cache, opts):
    na, deg_a, trunc_a = nb_cache[a]
    nb, deg_b, trunc_b = nb_cache[b]
    res = {"a": a, "b": b, "deg_a": deg_a, "deg_b": deg_b,
           "degree_truncated": trunc_a or trunc_b,
           "direct": list(na.get(b, [])), "two_hop": {}, "three_hop": {},
           "n2": 0, "n3": 0, "three_hop_truncated": False}
    small, big = (na, nb) if len(na) <= len(nb) else (nb, na)
    for x in small:
        if x == a or x == b or x not in big:
            continue
        for r1 in na[x]:
            for rb in nb[x]:
                key = (r1, inverse_relation(rb))
                slot = res["two_hop"].setdefault(key, {"count": 0, "examples": []})
                slot["count"] += 1
                res["n2"] += 1
                if len(slot["examples"]) < opts.examples:
                    slot["examples"].append(x)

    if opts.three_hop == "always" or (opts.three_hop == "if-no-2hop" and res["n2"] == 0):
        # expand one step from the lower-degree endpoint; check membership on the other side
        if len(na) <= len(nb):
            start, near, far, far_nb = a, na, b, nb
        else:
            start, near, far, far_nb = b, nb, a, na
        work = 0
        for x, rels_sx in near.items():
            if x in (a, b):
                continue
            for r2, ys in kg.get(x, {}).items():
                for y in ys:
                    work += 1
                    if work > opts.work_budget:
                        res["three_hop_truncated"] = True
                        break
                    if y in (a, b, x) or y not in far_nb:
                        continue
                    for r1 in rels_sx:
                        for rf in far_nb[y]:
                            # path start -r1-> x -r2-> y -(inv rf)-> far ; store oriented a -> b
                            seq = (r1, r2, inverse_relation(rf))
                            mids = (x, y)
                            if start != a:
                                seq = tuple(inverse_relation(r) for r in reversed(seq))
                                mids = (y, x)
                            slot = res["three_hop"].setdefault(seq, {"count": 0, "examples": []})
                            slot["count"] += 1
                            res["n3"] += 1
                            if len(slot["examples"]) < opts.examples:
                                slot["examples"].append(mids)
                if res["three_hop_truncated"]:
                    break
            if res["three_hop_truncated"]:
                break
    return res


def process_claim(kg, entities, opts):
    ents = [e for e in dict.fromkeys(entities)]
    cache = {e: neighbours(kg, e, opts.max_degree) for e in ents}
    missing = [e for e in ents if e not in kg]
    pairs = [search_pair(kg, a, b, cache, opts) for a, b in combinations(ents, 2)]
    return {"entities": ents, "missing_in_kg": missing, "pairs": pairs}


def merge(work_dir, out_path):
    shards = sorted(Path(work_dir).glob("shard_*.pkl"))
    merged = {}
    for s in shards:
        merged.update(read_pickle(s))
    write_pickle(merged, out_path)
    print(f"merged {len(shards)} shards, {len(merged)} claims -> {out_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kg", required=False)
    ap.add_argument("--factkg", required=True)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--merge", default=None, help="write merged pickle here and exit")
    ap.add_argument("--shard-size", type=int, default=1000)
    ap.add_argument("--max-degree", type=int, default=500_000)
    ap.add_argument("--work-budget", type=int, default=2_000_000, help="3-hop edge visits per pair")
    ap.add_argument("--three-hop", choices=["never", "if-no-2hop", "always"], default="if-no-2hop")
    ap.add_argument("--examples", type=int, default=3, help="example intermediates per relation sequence")
    ap.add_argument("--limit", type=int, default=None)
    opts = ap.parse_args()

    if opts.merge:
        merge(opts.work_dir, opts.merge)
        return
    if not opts.kg:
        ap.error("--kg is required unless --merge")
    work_dir = Path(opts.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    rows = load_factkg(opts.factkg)
    if opts.limit:
        rows = rows[:opts.limit]
    print("loading KG ...", flush=True)
    t0 = time.time()
    kg = read_pickle(opts.kg)
    print(f"KG loaded: {len(kg)} entities in {time.time() - t0:.0f}s", flush=True)
    write_json(vars(opts), work_dir / "config.json")

    for start in range(0, len(rows), opts.shard_size):
        shard = work_dir / f"shard_{start:07d}.pkl"
        if shard.exists():
            continue
        t1 = time.time()
        out = {claim: process_claim(kg, rec["Entity_set"], opts)
               for claim, rec in rows[start:start + opts.shard_size]}
        write_pickle(out, shard)
        print(f"claims {start}-{start + len(out) - 1} done in {time.time() - t1:.0f}s", flush=True)
    print("all shards done; rerun with --merge OUT.pkl")


if __name__ == "__main__":
    main()
