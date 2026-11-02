"""Fine-tune and evaluate BERT on FactKG claim + complete one-hop triples.

Paper settings: bert-base-uncased, 512 tokens, AdamW, batch 4, LR 5e-6,
all parameters trainable, checkpoint and early stopping by dev accuracy.
"""

import argparse
import json
import pickle
import random
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader
from transformers import AutoModelForSequenceClassification, AutoTokenizer


def read_records(path):
    with path.open("rb") as handle:
        return pickle.load(handle)


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def collator(tokenizer, max_length):
    def collate(rows):
        batch = tokenizer(
            [row["text"] for row in rows], padding=True, truncation=True,
            max_length=max_length, return_tensors="pt",
        )
        batch["labels"] = torch.tensor([row["label"] for row in rows], dtype=torch.long)
        return batch
    return collate


def make_loader(records, tokenizer, batch_size, max_length, shuffle):
    return DataLoader(
        records, batch_size=batch_size, shuffle=shuffle, drop_last=False,
        collate_fn=collator(tokenizer, max_length),
    )


def run_epoch(model, loader, device, optimizer=None):
    training = optimizer is not None
    model.train(training)
    correct = 0
    total_loss = 0.0
    predictions = []
    for batch in loader:
        batch = {key: value.to(device) for key, value in batch.items()}
        if training:
            optimizer.zero_grad(set_to_none=True)
            outputs = model(**batch)
            outputs.loss.backward()
            optimizer.step()
        else:
            with torch.inference_mode():
                outputs = model(**batch)
        predicted = outputs.logits.argmax(dim=-1)
        predictions.extend(predicted.cpu().tolist())
        correct += (predicted == batch["labels"]).sum().item()
        total_loss += outputs.loss.item() * len(batch["labels"])
    n = len(loader.dataset)
    return {"accuracy": correct / n, "loss": total_loss / n}, predictions


def reasoning_group(types):
    """Match the original FactKG classifier's five disjoint groups."""
    if "negation" in types:
        return "negation"
    if "num1" in types:
        return "one-hop"
    if "multi hop" in types:
        return "multi-hop"
    if "multi claim" in types:
        return "conjunction"
    if "existence" in types:
        return "existence"
    raise ValueError(f"Unrecognized FactKG reasoning tags: {types!r}")


def grouped_metrics(records, predictions):
    groups = {name: {"correct": 0, "n": 0} for name in (
        "one-hop", "multi-hop", "conjunction", "existence", "negation"
    )}
    for row, predicted in zip(records, predictions, strict=True):
        result = groups[reasoning_group(row["types"])]
        result["n"] += 1
        result["correct"] += int(predicted == row["label"])
    for result in groups.values():
        result["accuracy"] = result["correct"] / result["n"] if result["n"] else None
    return groups


def train(args):
    if args.output_dir.exists():
        raise FileExistsError(f"Use a new output directory: {args.output_dir}")
    set_seed(args.seed)
    train_rows = read_records(args.prepared_dir / "train.pkl")
    dev_rows = read_records(args.prepared_dir / "dev.pkl")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = AutoModelForSequenceClassification.from_pretrained(args.model_name, num_labels=2)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    train_loader = make_loader(train_rows, tokenizer, args.batch_size, args.max_length, True)
    dev_loader = make_loader(dev_rows, tokenizer, args.batch_size, args.max_length, False)

    args.output_dir.mkdir(parents=True)
    best_accuracy = -1.0
    stale_epochs = 0
    history = []
    for epoch in range(1, args.epochs + 1):
        train_result, _ = run_epoch(model, train_loader, device, optimizer)
        dev_result, _ = run_epoch(model, dev_loader, device)
        improved = dev_result["accuracy"] > best_accuracy
        history.append({"epoch": epoch, "train": train_result, "dev": dev_result,
                        "selected": improved})
        print(f"epoch {epoch}: train={train_result['accuracy']:.4f} "
              f"dev={dev_result['accuracy']:.4f} selected={improved}", flush=True)
        if improved:
            best_accuracy = dev_result["accuracy"]
            stale_epochs = 0
            checkpoint = args.output_dir / "best_checkpoint"
            model.save_pretrained(checkpoint)
            tokenizer.save_pretrained(checkpoint)
        else:
            stale_epochs += 1
        (args.output_dir / "history.json").write_text(
            json.dumps(history, indent=2), encoding="utf-8"
        )
        if stale_epochs >= args.patience:
            print(f"early stop: no dev accuracy improvement for {args.patience} epochs")
            break
    config = {"model_name": args.model_name, "batch_size": args.batch_size,
              "learning_rate": args.learning_rate, "max_length": args.max_length,
              "seed": args.seed, "best_dev_accuracy": best_accuracy,
              "train_claims": len(train_rows), "dev_claims": len(dev_rows),
              "selection": "dev_accuracy"}
    (args.output_dir / "config.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )


def evaluate(args):
    if args.output_dir.exists():
        raise FileExistsError(f"Use a new output directory: {args.output_dir}")
    rows = read_records(args.data)
    tokenizer = AutoTokenizer.from_pretrained(args.checkpoint)
    model = AutoModelForSequenceClassification.from_pretrained(args.checkpoint)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    loader = make_loader(rows, tokenizer, args.batch_size, args.max_length, False)
    overall, predictions = run_epoch(model, loader, device)
    report = {"n": len(rows), "overall": overall,
              "five_reasoning_groups": grouped_metrics(rows, predictions)}
    args.output_dir.mkdir(parents=True)
    (args.output_dir / "metrics.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    with (args.output_dir / "predictions.pkl").open("wb") as handle:
        pickle.dump({"claims": [row["claim"] for row in rows],
                     "labels": [row["label"] for row in rows],
                     "predictions": predictions}, handle)
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    train_parser = commands.add_parser("train")
    train_parser.add_argument("--prepared-dir", type=Path, required=True)
    train_parser.add_argument("--output-dir", type=Path, required=True)
    train_parser.add_argument("--model-name", default="bert-base-uncased")
    train_parser.add_argument("--batch-size", type=int, default=4)
    train_parser.add_argument("--learning-rate", type=float, default=5e-6)
    train_parser.add_argument("--max-length", type=int, default=512)
    train_parser.add_argument("--epochs", type=int, default=10)
    train_parser.add_argument("--patience", type=int, default=3)
    train_parser.add_argument("--seed", type=int, default=57)
    eval_parser = commands.add_parser("evaluate")
    eval_parser.add_argument("--checkpoint", type=Path, required=True)
    eval_parser.add_argument("--data", type=Path, required=True)
    eval_parser.add_argument("--output-dir", type=Path, required=True)
    eval_parser.add_argument("--batch-size", type=int, default=4)
    eval_parser.add_argument("--max-length", type=int, default=512)
    args = parser.parse_args()
    if args.batch_size < 1 or args.max_length < 1:
        parser.error("batch size and max length must be positive")
    if args.command == "train":
        if args.epochs < 1 or args.patience < 1:
            parser.error("epochs and patience must be positive")
        train(args)
    else:
        evaluate(args)


if __name__ == "__main__":
    main()
