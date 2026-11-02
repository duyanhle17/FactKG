"""Evaluate an upstream FEVER BERT checkpoint using FactKG's five disjoint groups.

This does not change the trained model or evidence. The six overlapping groups
printed by upstream evaluate.py remain available from its normal test run.
"""

import argparse
import json
import pickle
from pathlib import Path

import torch

from datasets import get_dataloader, get_df
from models import get_bert_model
from utils import load_state_dict


GROUPS = ("one-hop", "multi-hop", "conjunction", "existence", "negation")


def five_group(tags):
    """Use the same mutually exclusive priority as FactKG baseline.py."""
    if "negation" in tags:
        return "negation"
    if "num1" in tags:
        return "one-hop"
    if "multi hop" in tags:
        return "multi-hop"
    if "multi claim" in tags:
        return "conjunction"
    if "existence" in tags:
        return "existence"
    raise ValueError(f"Unknown FactKG reasoning tags: {tags!r}")


def summarize(rows, labels, predictions):
    if len(rows) != len(labels) or len(rows) != len(predictions):
        raise ValueError("Prediction length differs from FactKG test split")
    if not labels:
        raise ValueError("Empty FactKG test split")
    groups = {name: {"n": 0, "correct": 0} for name in GROUPS}
    for gold, tags, label, prediction in zip(rows["Label"], rows["types"], labels, predictions):
        if int(gold[0]) != label:
            raise ValueError("Prediction labels are misaligned with FactKG test rows")
        result = groups[five_group(tags)]
        result["n"] += 1
        result["correct"] += int(label == prediction)
    for result in groups.values():
        result["accuracy"] = result["correct"] / result["n"] if result["n"] else None
    return {"overall": sum(a == b for a, b in zip(labels, predictions)) / len(labels),
            "n": len(labels), "groups": groups}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--batch-size", type=int, default=4)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(f"Use a fresh output directory: {args.output_dir}")
    data = get_df("test")
    loader = get_dataloader("test", "one_hop", subgraph_to_use="walkable",
                            batch_size=args.batch_size, shuffle=False, drop_last=False)
    model = get_bert_model("fever_bert", include_classifier=True, num_labels=2,
                           freeze_up_to_pooler=False)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.load_state_dict(load_state_dict(str(args.model_path), device))
    model.to(device).eval()
    labels, predictions = [], []
    with torch.inference_mode():
        for batch in loader:
            batch = batch.to(device)
            logits = model(**batch).logits
            labels.extend(batch["labels"].cpu().tolist())
            predictions.extend(logits.argmax(dim=-1).cpu().tolist())
    report = summarize(data, labels, predictions)
    args.output_dir.mkdir(parents=True)
    (args.output_dir / "five_reasoning_metrics.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    with (args.output_dir / "predictions.pkl").open("wb") as handle:
        pickle.dump({"claims": data["Sentence"].tolist(),
                     "labels": labels, "predictions": predictions}, handle)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
