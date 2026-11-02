"""Build deterministic, label-free one-hop KG evidence for the official FactKG splits.

Independent implementation of the method described in Upadhyay et al. (FEVER 2026).
This does not copy the authors' source code or use FactKG's gold Evidence field.
"""

import argparse
import json
import pickle
from pathlib import Path


SPLITS = ("train", "dev", "test")


def read_pickle(path):
    with path.open("rb") as handle:
        return pickle.load(handle)


def one_hop_triples(kg, entities):
    """Return every outgoing KG triple for each claim entity, including inverse edges."""
    triples = []
    for head in dict.fromkeys(entities):
        for relation, tails in kg.get(head, {}).items():
            triples.extend((str(head), str(relation), str(tail)) for tail in tails)
    return sorted(triples)


def readable(value):
    value = str(value).replace("_", " ")
    return "inverse " + value[1:] if value.startswith("~") else value


def linearize(claim, triples):
    """One BERT input: claim, then one text fragment per complete triple."""
    fragments = [" ".join(map(readable, triple)) for triple in triples]
    return str(claim) + " [SEP] " + " [SEP] ".join(fragments) if fragments else str(claim)


def label_of(row):
    labels = row["Label"]
    if not isinstance(labels, (list, tuple)) or len(labels) != 1:
        raise ValueError("Expected FactKG Label to contain exactly one value")
    return int(labels[0])


def prepare_split(data, kg):
    records = []
    for claim, row in data.items():
        triples = one_hop_triples(kg, row["Entity_set"])
        records.append({
            "claim": claim,
            "text": linearize(claim, triples),
            "label": label_of(row),
            "types": list(row["types"]),
            "triple_count": len(triples),
        })
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--kg-path", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    kg = read_pickle(args.kg_path)
    report = {"method": "all_one_hop_triples", "kg_path": str(args.kg_path), "splits": {}}
    for split in SPLITS:
        source = args.data_dir / f"factkg_{split}.pickle"
        records = prepare_split(read_pickle(source), kg)
        target = args.output_dir / f"{split}.pkl"
        with target.open("wb") as handle:
            pickle.dump(records, handle, protocol=pickle.HIGHEST_PROTOCOL)
        report["splits"][split] = {
            "claims": len(records),
            "mean_triples": sum(row["triple_count"] for row in records) / len(records),
            "output": str(target),
        }
        print(f"{split}: {len(records)} claims, mean triples={report['splits'][split]['mean_triples']:.1f}")
    (args.output_dir / "prepare_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
