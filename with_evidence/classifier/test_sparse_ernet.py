"""Small CPU tests for sparse ERNet graph construction and masking.

Run from this directory with:
    python -m unittest test_sparse_ernet
"""

import unittest

import torch

from sparse_ernet import SparseERNetLayer, build_sparse_path_adjacency


class SparseAdjacencyTest(unittest.TestCase):
    def test_intermediate_and_continuation_edges_without_shared_head_edge(self):
        # P0/P1 share B as a genuine intermediate entity.
        # P0/P3 connect because P0 ends at C where P3 begins.
        # P0/P2 share only claim-source A and must not connect.
        paths = [[
            ["A", "r1", "B", "r2", "C"],
            ["D", "r3", "B", "r4", "E"],
            ["A", "r5", "F"],
            ["C", "r6", "G"],
        ]]
        adjacency = build_sparse_path_adjacency(paths, path_count=5)

        expected = torch.tensor(
            [[
                [1, 1, 0, 1, 0],
                [1, 1, 0, 0, 0],
                [0, 0, 1, 0, 0],
                [1, 0, 0, 1, 0],
                [0, 0, 0, 0, 0],
            ]],
            dtype=torch.bool,
        )
        torch.testing.assert_close(adjacency, expected)

    def test_isolated_real_path_keeps_own_vector_and_padding_stays_zero(self):
        layer = SparseERNetLayer(hidden_size=3)
        vectors = torch.tensor([[[1.0, 2.0, 3.0], [9.0, 9.0, 9.0]]])
        path_mask = torch.tensor([[True, False]])
        adjacency = torch.tensor([[[True, False], [False, False]]])

        output = layer(vectors, path_mask, adjacency)
        torch.testing.assert_close(output[:, 0], vectors[:, 0])
        torch.testing.assert_close(output[:, 1], torch.zeros_like(output[:, 1]))

    def test_claim_anchor_is_not_a_shared_intermediate_edge(self):
        # C is mentioned in the claim but appears in the middle of both paths.
        # It must not turn the paths into a graph hub.
        paths = [[
            ["A", "r1", "C", "r2", "X"],
            ["Z", "r3", "C", "r4", "Y"],
        ]]
        adjacency = build_sparse_path_adjacency(
            paths, path_count=2, claim_entity_sets=[["A", "C", "Z"]]
        )
        expected = torch.tensor([[[True, False], [False, True]]])
        torch.testing.assert_close(adjacency, expected)

    def test_tail_head_continuation_can_join_at_a_claim_entity(self):
        # C is a claim entity. It is excluded from shared-intermediate edges,
        # but tail(P0)=head(P1)=C remains a valid continuation edge.
        paths = [[
            ["A", "r1", "B", "r2", "C"],
            ["C", "r3", "D"],
        ]]
        adjacency = build_sparse_path_adjacency(
            paths, path_count=2, claim_entity_sets=[["A", "C"]]
        )
        expected = torch.tensor([[[True, True], [True, True]]])
        torch.testing.assert_close(adjacency, expected)

    def test_empty_fallback_has_only_self_loop_and_malformed_path_fails(self):
        adjacency = build_sparse_path_adjacency([[[]]], path_count=2)
        expected = torch.tensor([[[True, False], [False, False]]])
        torch.testing.assert_close(adjacency, expected)

        with self.assertRaisesRegex(ValueError, "odd length"):
            build_sparse_path_adjacency([[["A", "r1"]]], path_count=1)

    def test_forward_and_backward_are_finite_for_sparse_batch(self):
        paths = [[
            ["A", "r1", "B", "r2", "C"],
            ["D", "r3", "B", "r4", "E"],
        ], [["X", "r5", "Y"]]]
        adjacency = build_sparse_path_adjacency(paths, path_count=2)
        vectors = torch.randn(2, 2, 4, requires_grad=True)
        path_mask = torch.tensor([[True, True], [True, False]])
        layer = SparseERNetLayer(hidden_size=4)

        output = layer(vectors, path_mask, adjacency)
        self.assertTrue(torch.isfinite(output).all())
        output.square().sum().backward()
        self.assertIsNotNone(vectors.grad)
        self.assertTrue(torch.isfinite(vectors.grad).all())


if __name__ == "__main__":
    unittest.main()
