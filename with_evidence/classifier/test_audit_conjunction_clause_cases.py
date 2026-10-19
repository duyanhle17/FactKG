"""Small checks for the offline Conjunction casebook."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_conjunction_clause_cases import cases_by_group, visible_groups


class ConjunctionClauseCasebookTest(unittest.TestCase):
    def test_case_groups_use_only_conjunction_and_requested_indices(self):
        labels = [0, 0, 0, 1, 0]
        types = [2, 2, 2, 2, 1]
        first = [0, 1, 1, 0, 0]
        ranked = [1, 1, 0, 1, 1]
        groups = cases_by_group([0, 1, 2, 3, 4], labels, types, first, ranked)
        self.assertEqual([len(ids) for ids in groups.values()], [1, 1, 1, 1])
        self.assertEqual(list(groups.values())[0], [0])
        self.assertEqual(list(groups.values())[2], [2])

    def test_visible_paths_keep_connected_priority(self):
        row = {"connected": [["c1"], ["c2"]],
               "walkable": [["w1"], ["w2"]]}
        self.assertEqual(visible_groups(row, 3), (row["connected"], [["w1"]]))


if __name__ == "__main__":
    unittest.main()
