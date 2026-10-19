"""Small deterministic checks for the label-free walkable reranker."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from make_ranked_walkable_candidates import ranked_candidates, rank_walkable, tokens


class RankedWalkableCandidatesTest(unittest.TestCase):
    def test_camel_case_and_underscores_are_tokenized(self):
        self.assertEqual(tokens("birthPlace New_York"), {"birth", "place", "new", "york"})

    def test_relevant_later_path_displaces_irrelevant_first_path(self):
        claim = "Alice was born in Paris"
        paths = [
            ["Alice", "genre", "Rock"],
            ["Alice", "birthPlace", "Paris"],
        ]
        self.assertEqual(rank_walkable(claim, paths, 1), [paths[1]])

    def test_zero_score_ties_keep_original_order_and_connected_unchanged(self):
        paths = [["A", "r1", "X"], ["A", "r2", "Y"]]
        source = {"A": {"connected": [["A", "linked", "Z"]],
                        "walkable": paths, "diagnostic": 42}}
        result = ranked_candidates(source, 1)
        self.assertEqual(result["A"]["connected"], source["A"]["connected"])
        self.assertEqual(result["A"]["walkable"], paths[:1])
        self.assertEqual(result["A"]["diagnostic"], 42)
        self.assertEqual(source["A"]["walkable"], paths)


if __name__ == "__main__":
    unittest.main()
