"""Shared helpers for the FEVER-2026 bridge experiments (P0/P1).

Only depends on the standard library and pandas. Inputs are built exactly like
upstream `datasets.FactKGDataset`: ``claim + " | " + str(connected + walkable)``.
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

GROUPS = ("one-hop", "multi-hop", "conjunction", "existence", "negation")


def five_group(tags):
    """Mutually exclusive FactKG groups, same priority as eval_five.py / baseline.py."""
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


def read_pickle(path):
    with open(path, "rb") as handle:
        return pickle.load(handle)


def write_pickle(obj, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "wb") as handle:
        pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)
    tmp.replace(path)


def write_json(obj, path):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def fresh_dir(path):
    """Create an output directory that must not exist yet (never overwrite results)."""
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"Output already exists, choose a new path: {path}")
    path.mkdir(parents=True)
    return path


def load_factkg(path):
    """Return a list of (claim, record) in the pickle's dict order (= upstream get_df order)."""
    data = read_pickle(path)
    return list(data.items())


def label_of(record):
    return int(bool(record["Label"][0]))


def load_walked(path, expected_len=None):
    """Load the `walked` column of an upstream-format subgraph pickle (DataFrame) as a list."""
    obj = read_pickle(path)
    walked = list(obj["walked"]) if hasattr(obj, "columns") or isinstance(obj, dict) else list(obj)
    if expected_len is not None and len(walked) != expected_len:
        raise ValueError(f"{path}: {len(walked)} rows, expected {expected_len}")
    return walked


def evidence_of(walked_row):
    return list(walked_row["connected"]) + list(walked_row["walkable"])


def build_input(claim, evidence):
    """Byte-identical to upstream FactKGDataset input string."""
    return claim + " | " + str(evidence)


def inverse_relation(rel):
    return rel[1:] if rel.startswith("~") else "~" + rel


def reverse_path(path):
    """[e0, r1, e1, r2, e2] -> [e2, ~r2, e1, ~r1, e0]."""
    nodes = path[0::2][::-1]
    rels = [inverse_relation(r) for r in path[1::2]][::-1]
    out = [nodes[0]]
    for rel, node in zip(rels, nodes[1:]):
        out += [rel, node]
    return out


def canonical_path(path):
    """Same key for a path and its reverse (undirected KG stores both directions)."""
    a, b = tuple(path), tuple(reverse_path(path))
    return min(a, b)
