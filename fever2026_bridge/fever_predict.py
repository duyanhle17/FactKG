"""Run the trained FEVER-2026 BERT checkpoint on any split / any (injected) subgraph file.

Reproduces upstream inference (claim + " | " + str(connected + walkable), truncation at
512, argmax over 2 logits) without importing upstream code, so torch_geometric is not
needed. Saves per-claim probabilities so later scripts can compare claim by claim.

Sanity check before anything else: on the original test subgraphs this must give
8,372/9,041 (92.6004%) for the 10-epoch checkpoint.

Example (machine with checkpoint):
  python fever_predict.py \
    --factkg  DATA/factkg_dev.pickle \
    --subgraphs SUBGRAPHS/subgraphs_one_hop_val.pkl \
    --checkpoint MODELS/bert-base-uncased.pth \
    --output-dir OUT/p0_fever_dev
"""
from __future__ import annotations

import argparse
import time
from collections import Counter

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from common import (GROUPS, build_input, evidence_of, five_group, fresh_dir, label_of,
                    load_factkg, load_walked, write_json, write_pickle)


def summarize(groups, labels, preds):
    out = {"n": len(labels), "correct": sum(int(a == b) for a, b in zip(labels, preds))}
    out["accuracy"] = out["correct"] / max(out["n"], 1)
    per = {}
    for g in GROUPS:
        for lab in (None, 1, 0):
            idx = [i for i, gg in enumerate(groups) if gg == g and (lab is None or labels[i] == lab)]
            key = g if lab is None else f"{g}/{'True' if lab else 'False'}"
            c = sum(int(labels[i] == preds[i]) for i in idx)
            per[key] = {"n": len(idx), "correct": c, "accuracy": c / len(idx) if idx else None}
    out["groups"] = per
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--factkg", required=True, help="factkg_{dev,test}.pickle (defines claim order)")
    ap.add_argument("--subgraphs", required=True, help="upstream-format subgraph pickle (column `walked`)")
    ap.add_argument("--checkpoint", required=True, help="state dict saved by upstream run_stuff.py")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--model-name", default="bert-base-uncased")
    ap.add_argument("--cache-dir", default=None, help="HF cache dir for model weights (upstream used ./cache)")
    ap.add_argument("--tokenizer-cache-dir", default=None, help="HF cache dir for the tokenizer (default HF cache)")
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--limit", type=int, default=None, help="smoke test on first N claims")
    args = ap.parse_args()

    out_dir = fresh_dir(args.output_dir)
    rows = load_factkg(args.factkg)
    walked = load_walked(args.subgraphs, expected_len=len(rows))
    if args.limit:
        rows, walked = rows[:args.limit], walked[:args.limit]
    claims = [c for c, _ in rows]
    labels = [label_of(r) for _, r in rows]
    groups = [five_group(r["types"]) for _, r in rows]
    texts = [build_input(c, evidence_of(w)) for c, w in zip(claims, walked)]

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    # Upstream loads the tokenizer from the default HF cache (weights may live in ./cache).
    tok = AutoTokenizer.from_pretrained(args.model_name, cache_dir=args.tokenizer_cache_dir)
    if len(tok) < 1000 or tok.unk_token_id in tok("knowledge graph")["input_ids"]:
        raise RuntimeError(f"Broken tokenizer (vocab size {len(tok)}); set --tokenizer-cache-dir "
                           "to a cache that contains vocab.txt")
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name, num_labels=2, cache_dir=args.cache_dir)
    state = torch.load(args.checkpoint, map_location="cpu")
    # Transformers versions differ only in whether the non-learned `position_ids` buffer is saved.
    missing, unexpected = model.load_state_dict(state, strict=False)
    bad = [k for k in list(missing) + list(unexpected) if not k.endswith("position_ids")]
    if bad:
        raise RuntimeError(f"checkpoint/model mismatch: {bad[:10]}")
    model.to(device).eval()

    # Sort by length for speed; padding does not change per-example logits.
    order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
    prob_true = [0.0] * len(texts)
    t0 = time.time()
    with torch.inference_mode():
        for s in range(0, len(order), args.batch_size):
            idx = order[s:s + args.batch_size]
            enc = tok([texts[i] for i in idx], return_tensors="pt", padding=True,
                      truncation=True, max_length=args.max_length).to(device)
            probs = torch.softmax(model(**enc).logits.float(), dim=-1)[:, 1].cpu().tolist()
            for i, p in zip(idx, probs):
                prob_true[i] = p
    elapsed = time.time() - t0
    preds = [int(p > 0.5) for p in prob_true]

    report = summarize(groups, labels, preds)
    report.update({"factkg": args.factkg, "subgraphs": args.subgraphs, "checkpoint": args.checkpoint,
                   "seconds": elapsed, "ms_per_claim": 1000 * elapsed / max(len(texts), 1),
                   "label_counts": dict(Counter(labels))})
    write_pickle({"claim": claims, "label": labels, "group": groups,
                  "types": [r["types"] for _, r in rows], "prob_true": prob_true,
                  "prediction": preds}, out_dir / "predictions.pkl")
    write_json(report, out_dir / "metrics.json")
    print(f"accuracy {report['accuracy']:.4%} ({report['correct']}/{report['n']}) in {elapsed:.0f}s")
    for g in GROUPS:
        r = report["groups"][g]
        if r["n"]:
            print(f"  {g:12s} {r['accuracy']:.4%}  (n={r['n']})")


if __name__ == "__main__":
    main()
