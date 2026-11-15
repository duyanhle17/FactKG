"""Unit tests on a toy undirected KG (no torch / no real data needed).

  python -m unittest test_bridge -v
"""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

import bridge_retrieval as br
import gold_bridge as gb
from build_injected import bridge_paths, lexical_score, rel_tokens
from common import build_input, canonical_path, inverse_relation, reverse_path, write_pickle
from flip_compare import mcnemar_p
from token_audit import path_spans


def make_kg(triples):
    kg = {}
    for h, r, t in triples:
        kg.setdefault(h, {}).setdefault(r, []).append(t)
        kg.setdefault(t, {}).setdefault(inverse_relation(r), []).append(h)
    return kg


KG = make_kg([
    ("A", "child", "X"), ("X", "birthYear", '"1998"'),
    ("A", "child", "Z"), ("Z", "birthYear", '"1997"'),
    ("A", "country", "Hub"), ("P", "country", "Hub"),
    ("M", "location", "C"), ("C", "country", "J"), ("J", "leaderName", "Abe"),
    ("A", "spouse", "B"),
])
OPTS = SimpleNamespace(max_degree=10_000, work_budget=10_000, three_hop="if-no-2hop", examples=3)


class TestCommon(unittest.TestCase):
    def test_build_input_matches_upstream(self):
        ev = [["A", "child", "X"], ["A", "spouse", "B"]]
        self.assertEqual(build_input("c", ev), "c | [['A', 'child', 'X'], ['A', 'spouse', 'B']]")

    def test_reverse_and_canonical(self):
        p = ["A", "child", "X", "birthYear", '"1998"']
        self.assertEqual(reverse_path(p), ['"1998"', "~birthYear", "X", "~child", "A"])
        self.assertEqual(canonical_path(p), canonical_path(reverse_path(p)))

    def test_path_spans(self):
        ev = [["A", "r", "B"], ["C", "s", "D"]]
        text = build_input("claim", ev)
        for (s, e), p in zip(path_spans("claim", ev), ev):
            self.assertEqual(text[s:e], str(p))


class TestBridgeRetrieval(unittest.TestCase):
    def test_two_hop_bridge(self):
        res = br.process_claim(KG, ["A", '"1998"'], OPTS)
        pair = res["pairs"][0]
        self.assertFalse(pair["direct"])
        self.assertIn(("child", "birthYear"), pair["two_hop"])
        self.assertEqual(pair["two_hop"][("child", "birthYear")]["examples"], ["X"])

    def test_direct_edge(self):
        pair = br.process_claim(KG, ["A", "B"], OPTS)["pairs"][0]
        self.assertEqual(pair["direct"], ["spouse"])

    def test_spurious_hub_bridge_is_found(self):
        pair = br.process_claim(KG, ["A", "P"], OPTS)["pairs"][0]
        self.assertIn(("country", "~country"), pair["two_hop"])

    def test_three_hop_both_orientations(self):
        for ents in (["M", "Abe"], ["Abe", "M"]):
            pair = br.process_claim(KG, ents, OPTS)["pairs"][0]
            self.assertEqual(pair["n2"], 0)
            a = pair["a"]
            expected = ("location", "country", "leaderName") if a == "M" else ("~leaderName", "~country", "~location")
            self.assertIn(expected, pair["three_hop"], pair["three_hop"])
            mids = pair["three_hop"][expected]["examples"][0]
            self.assertEqual(mids, ("C", "J") if a == "M" else ("J", "C"))

    def test_shards_and_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_pickle({"c1": 1}, Path(tmp) / "shard_0000000.pkl")
            write_pickle({"c2": 2}, Path(tmp) / "shard_0001000.pkl")
            br.merge(tmp, Path(tmp) / "m.pkl")
            self.assertEqual(pd.read_pickle(Path(tmp) / "m.pkl"), {"c1": 1, "c2": 2})


class TestGoldBridge(unittest.TestCase):
    def test_true_claim_connected(self):
        rec = {"Entity_set": ["A", '"1998"'], "Evidence": {"A": [["child", "birthYear"]],
                                                         '"1998"': [["~birthYear", "~child"]]}}
        res = gb.instantiate(KG, rec, SimpleNamespace(max_frontier=100, max_per_seq=3))
        self.assertEqual(len(res["connected"]), 1)  # forward and reverse deduplicated
        self.assertEqual(res["walkable"], [])

    def test_false_claim_near_miss(self):
        rec = {"Entity_set": ["A", '"2001"'], "Evidence": {"A": [["child", "birthYear"]]}}
        res = gb.instantiate(KG, rec, SimpleNamespace(max_frontier=100, max_per_seq=3))
        self.assertEqual(res["connected"], [])
        ends = sorted(p[-1] for p in res["walkable"])
        self.assertEqual(ends, ['"1997"', '"1998"'])


class TestInjection(unittest.TestCase):
    def test_rel_tokens_and_score(self):
        self.assertEqual(rel_tokens("~birthYear"), ["birth", "year"])
        self.assertGreater(lexical_score(("child", "birthYear"), {"child", "born", "year"}), 0)

    def test_ranking_prefers_claim_relations(self):
        entry = br.process_claim(KG, ["A", "P"], OPTS)
        entry["pairs"][0]["two_hop"][("child", "birthYear")] = {"count": 1, "examples": ["X"]}
        paths = bridge_paths(entry, "A has a child born in that year", 5, True)
        self.assertEqual(paths[0], ["A", "child", "X", "birthYear", "P"])


class TestMcNemar(unittest.TestCase):
    def test_values(self):
        self.assertEqual(mcnemar_p(0, 0), 1.0)
        self.assertAlmostEqual(mcnemar_p(10, 0), 2 / 2 ** 10)


if __name__ == "__main__":
    unittest.main()
