"""Measure real BERT token lengths and how much evidence survives the 512-token cut.

For every claim: total tokens without truncation, whether it exceeds --max-length,
how many evidence paths (connected / walkable) lie completely inside the window,
and the character offset where the window ends (used by analyze_p0.py to check
whether a bridge node is actually visible to BERT). CPU only, needs a fast tokenizer.

  python token_audit.py --factkg DATA/factkg_dev.pickle \
      --subgraphs SUBGRAPHS/subgraphs_one_hop_val.pkl --output-dir OUT/p0_tokens_dev
"""
from __future__ import annotations

import argparse
from collections import defaultdict

from common import (GROUPS, build_input, five_group, fresh_dir, label_of, load_factkg,
                    load_walked, write_json, write_pickle)


def path_spans(claim, evidence):
    """Char (start, end) of each path inside build_input(claim, evidence)."""
    pos = len(claim) + len(" | ") + 1  # after "["
    spans = []
    for k, path in enumerate(evidence):
        s = str(path)
        spans.append((pos, pos + len(s)))
        pos += len(s) + (2 if k < len(evidence) - 1 else 0)  # ", "
    return spans


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--factkg", required=True)
    ap.add_argument("--subgraphs", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--model-name", default="bert-base-uncased")
    ap.add_argument("--cache-dir", default=None)
    ap.add_argument("--max-length", type=int, default=512)
    args = ap.parse_args()

    from transformers import AutoTokenizer  # lazy: unit tests run without torch

    out_dir = fresh_dir(args.output_dir)
    tok = AutoTokenizer.from_pretrained(args.model_name, cache_dir=args.cache_dir, use_fast=True)
    rows = load_factkg(args.factkg)
    walked = load_walked(args.subgraphs, expected_len=len(rows))
    budget = args.max_length - 2  # [CLS] ... [SEP]

    per_claim = {}
    agg = defaultdict(lambda: defaultdict(float))
    for (claim, rec), w in zip(rows, walked):
        conn, walk = list(w["connected"]), list(w["walkable"])
        ev = conn + walk
        text = build_input(claim, ev)
        enc = tok(text, add_special_tokens=False, return_offsets_mapping=True)
        n_tok = len(enc["input_ids"])
        cut_char = enc["offset_mapping"][budget - 1][1] if n_tok > budget else len(text)
        spans = path_spans(claim, ev)
        visible = [end <= cut_char for _, end in spans]
        vis_conn = sum(visible[:len(conn)])
        vis_walk = sum(visible[len(conn):])
        g = five_group(rec["types"])
        lab = label_of(rec)
        per_claim[claim] = {"tokens": n_tok + 2, "cut_char": cut_char, "n_conn": len(conn),
                            "n_walk": len(walk), "vis_conn": vis_conn, "vis_walk": vis_walk}
        for key in (g, f"{g}/{'True' if lab else 'False'}"):
            a = agg[key]
            a["n"] += 1
            a["tokens"] += n_tok + 2
            a["over"] += n_tok + 2 > args.max_length
            a["paths"] += len(ev)
            a["visible_paths"] += vis_conn + vis_walk
            a["conn"] += len(conn)
            a["visible_conn"] += vis_conn

    report = {}
    for key, a in sorted(agg.items()):
        n = a["n"]
        report[key] = {"n": int(n), "mean_tokens": a["tokens"] / n,
                       "pct_over_max": 100 * a["over"] / n,
                       "pct_paths_visible": 100 * a["visible_paths"] / max(a["paths"], 1),
                       "pct_connected_visible": 100 * a["visible_conn"] / max(a["conn"], 1)}
    write_json(report, out_dir / "token_report.json")
    write_pickle(per_claim, out_dir / "per_claim.pkl")
    print(f"{'group':22s} {'n':>6s} {'meanTok':>8s} {'>max':>7s} {'paths vis':>9s} {'conn vis':>8s}")
    for g in GROUPS:
        for key in (g, f"{g}/True", f"{g}/False"):
            if key in report:
                r = report[key]
                print(f"{key:22s} {r['n']:6d} {r['mean_tokens']:8.0f} {r['pct_over_max']:6.1f}% "
                      f"{r['pct_paths_visible']:8.1f}% {r['pct_connected_visible']:7.1f}%")


if __name__ == "__main__":
    main()
