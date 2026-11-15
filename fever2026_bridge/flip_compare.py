"""Compare two fever_predict.py runs claim by claim: accuracy, PFR/NFR per group, McNemar.

NFR (negative flip rate) = baseline correct -> new wrong, divided by n of the group.
This is the "do no harm" number: a gain on multi-hop is only useful if NFR elsewhere ~ 0.

  python flip_compare.py --base OUT/p0_fever_dev/predictions.pkl \
      --new OUT/p1_gold_multihop_dev/predictions.pkl
"""
from __future__ import annotations

import argparse
import math
from collections import Counter

from common import GROUPS, read_pickle, write_json


def mcnemar_p(b, c):
    """Exact two-sided McNemar test on discordant counts b, c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--output", default=None, help="optional JSON output")
    args = ap.parse_args()

    base, new = read_pickle(args.base), read_pickle(args.new)
    bp = dict(zip(base["claim"], base["prediction"]))
    rows = list(zip(new["claim"], new["label"], new["group"], new["prediction"]))
    missing = [c for c, *_ in rows if c not in bp]
    if missing:
        raise ValueError(f"{len(missing)} claims of --new are missing in --base")

    c = Counter()
    for claim, y, g, p_new in rows:
        p_old = bp[claim]
        lab = "True" if y else "False"
        for k in ("overall", g, f"{g}/{lab}"):
            c[(k, "n")] += 1
            c[(k, "old")] += p_old == y
            c[(k, "new")] += p_new == y
            c[(k, "pos")] += p_old != y and p_new == y
            c[(k, "neg")] += p_old == y and p_new != y

    out = {}
    print(f"{'group':22s} {'n':>6s} {'base':>8s} {'new':>8s} {'delta':>7s} {'+flip':>6s} {'-flip':>6s} "
          f"{'NFR':>6s} {'McNemar p':>9s}")
    keys = ["overall"] + [k for g in GROUPS for k in (g, f"{g}/True", f"{g}/False")]
    for k in keys:
        n = c[(k, "n")]
        if not n:
            continue
        r = {x: c[(k, x)] for x in ("n", "old", "new", "pos", "neg")}
        r["p"] = mcnemar_p(r["pos"], r["neg"])
        out[k] = r
        print(f"{k:22s} {n:6d} {100 * r['old'] / n:7.2f}% {100 * r['new'] / n:7.2f}% "
              f"{100 * (r['new'] - r['old']) / n:+6.2f} {r['pos']:6d} {r['neg']:6d} "
              f"{100 * r['neg'] / n:5.2f}% {r['p']:9.3g}")
    if args.output:
        write_json(out, args.output)


if __name__ == "__main__":
    main()
