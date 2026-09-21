"""Sparse Evidence Reasoning Network for FactKG candidate paths.

This module adapts the ERNet message-passing equation from GEAR to FactKG.
The original GEAR graph is fully connected because its inputs are a small set
of FEVER evidence sentences. FactKG instead supplies up to K serialized KG
paths, so the graph is deliberately sparse:

* every real path has a self-loop;
* two paths connect when they share an intermediate entity; or
* two paths connect when one's tail is the other's head.

Sharing only a claim-source/head entity is intentionally not an edge. R3
starts many paths at a claim entity, so that rule would make the graph almost
fully connected and spread retrieval noise.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Iterable, Optional, Sequence

import torch
import torch.nn as nn


@dataclass(frozen=True)
class PathSignature:
    """Entity-only view of a flat [entity, relation, entity, ...] path."""

    head: Optional[str]
    tail: Optional[str]
    intermediate_entities: FrozenSet[str]


def _path_signature(
    path: Iterable[object], claim_entities: FrozenSet[str]
) -> PathSignature:
    """Extract entities without treating relation strings as graph nodes.

    R3 stores paths in the alternating format ``[e0, r1, e1, ..., rm, em]``.
    The function tolerates an empty fallback path used for claims with no
    retrieved evidence; that path later receives only its self-loop.
    """

    if isinstance(path, str):
        # R3 artifacts are sequences. A bare string would otherwise be read
        # character by character and silently create an invalid graph.
        raise ValueError(
            "Serialized candidate path must be [entity, relation, ..., entity], "
            "not a bare string"
        )
    items = tuple(path)

    if not items:
        return PathSignature(None, None, frozenset())
    if len(items) < 3 or len(items) % 2 == 0:
        raise ValueError(
            "Serialized candidate path must have odd length >= 3 in the form "
            "[entity, relation, ..., entity]; got "
            f"{list(items)!r}"
        )

    entities = tuple(str(item) for item in items[0::2])
    return PathSignature(
        head=entities[0],
        tail=entities[-1],
        # Do not use the head or tail in this rule. In particular, many R3
        # paths share a claim-source head but are not a useful reasoning pair.
        # A claim entity can reappear in the middle of a KG path. It is still
        # an anchor, not evidence that two candidate paths are meaningfully
        # connected, so remove every Entity_set member here.
        intermediate_entities=frozenset(entities[1:-1]) - claim_entities,
    )


def build_sparse_path_adjacency(
    paths_per_claim: Sequence[Sequence[Sequence[object]]],
    path_count: int,
    claim_entity_sets: Optional[Sequence[Iterable[object]]] = None,
) -> torch.Tensor:
    """Build a symmetric boolean adjacency matrix of shape ``[B, K, K]``.

    ``paths_per_claim`` contains only real paths for each claim; positions
    after its length are batch padding and remain False in the matrix. An edge
    ``adjacency[b, i, j]`` means path ``i`` may receive a message from path
    ``j``. The relation is symmetric in this first sparse ERNet ablation, so
    connected paths can exchange information in both directions.
    """

    if path_count < 1:
        raise ValueError("path_count must be at least 1")
    if claim_entity_sets is not None and len(claim_entity_sets) != len(paths_per_claim):
        raise ValueError(
            "claim_entity_sets must have one entry per claim: "
            f"expected {len(paths_per_claim)}, got {len(claim_entity_sets)}"
        )

    adjacency = torch.zeros(
        (len(paths_per_claim), path_count, path_count), dtype=torch.bool
    )

    for batch_index, paths in enumerate(paths_per_claim):
        real_count = min(len(paths), path_count)
        raw_claim_entities = (
            () if claim_entity_sets is None else claim_entity_sets[batch_index]
        )
        claim_entities = frozenset(str(entity) for entity in raw_claim_entities)
        signatures = [
            _path_signature(path, claim_entities) for path in paths[:real_count]
        ]

        # Every real path must retain its own representation, including the
        # empty-path fallback used when retrieval returns no candidate.
        for path_index in range(real_count):
            adjacency[batch_index, path_index, path_index] = True

        for left_index in range(real_count):
            left = signatures[left_index]
            for right_index in range(left_index + 1, real_count):
                right = signatures[right_index]

                shares_intermediate = bool(
                    left.intermediate_entities & right.intermediate_entities
                )
                is_continuation = bool(
                    left.tail is not None
                    and right.head is not None
                    and (left.tail == right.head or right.tail == left.head)
                )

                if shares_intermediate or is_continuation:
                    adjacency[batch_index, left_index, right_index] = True
                    adjacency[batch_index, right_index, left_index] = True

    return adjacency


class SparseERNetLayer(nn.Module):
    """One GEAR-style attention/message-passing layer over sparse path edges.

    For each allowed edge i <- j, the layer computes:

    ``a_ij = MLP([h_i ; h_j])``
    ``alpha_ij = softmax_j(a_ij)``
    ``h'_i = sum_j(alpha_ij * h_j)``

    The MLP width 64 matches the ERNet hidden width reported in the GEAR
    paper. Masked/padded nodes cannot send or receive messages.
    """

    def __init__(self, hidden_size: int, attention_hidden_size: int = 64):
        super().__init__()
        # This is mathematically the first Linear(2H -> 64) from GEAR:
        # W[h_i ; h_j] + b = W_receiver h_i + W_sender h_j + b.
        # Splitting the projection avoids materializing [B,K,K,2H], important
        # when FactKG uses K=32 candidate paths on a 6-GB GPU.
        self.receiver_projection = nn.Linear(
            hidden_size, attention_hidden_size, bias=True
        )
        self.sender_projection = nn.Linear(
            hidden_size, attention_hidden_size, bias=False
        )
        self.output_projection = nn.Linear(attention_hidden_size, 1)

    def forward(
        self,
        path_vectors: torch.Tensor,
        path_mask: torch.Tensor,
        adjacency: torch.Tensor,
    ) -> torch.Tensor:
        if path_vectors.ndim != 3:
            raise ValueError(
                "path_vectors must have shape [B,K,H], got "
                f"{tuple(path_vectors.shape)}"
            )
        batch_size, path_count, _ = path_vectors.shape
        expected_shape = (batch_size, path_count)
        if tuple(path_mask.shape) != expected_shape:
            raise ValueError(
                "path_mask must have shape "
                f"{expected_shape}, got {tuple(path_mask.shape)}"
            )
        expected_adjacency_shape = (batch_size, path_count, path_count)
        if tuple(adjacency.shape) != expected_adjacency_shape:
            raise ValueError(
                "adjacency must have shape "
                f"{expected_adjacency_shape}, got {tuple(adjacency.shape)}"
            )
        if path_mask.device != path_vectors.device:
            raise ValueError(
                "path_mask and path_vectors must be on the same device; got "
                f"{path_mask.device} and {path_vectors.device}"
            )
        if adjacency.device != path_vectors.device:
            raise ValueError(
                "adjacency and path_vectors must be on the same device; got "
                f"{adjacency.device} and {path_vectors.device}"
            )

        path_mask = path_mask.bool()
        adjacency = adjacency.bool()
        valid_nodes = path_mask.unsqueeze(2) & path_mask.unsqueeze(1)

        # Add a defensive self-loop. The collator already creates it, but this
        # keeps an isolated real path valid if a custom caller supplies edges.
        identity = torch.eye(path_count, dtype=torch.bool, device=path_vectors.device)
        self_loops = identity.unsqueeze(0) & valid_nodes
        edge_mask = (adjacency & valid_nodes) | self_loops

        receiver_features = self.receiver_projection(path_vectors).unsqueeze(2)
        sender_features = self.sender_projection(path_vectors).unsqueeze(1)
        attention_scores = self.output_projection(
            torch.relu(receiver_features + sender_features)
        ).squeeze(-1)
        attention_scores = attention_scores.masked_fill(
            ~edge_mask, torch.finfo(attention_scores.dtype).min
        )
        attention_weights = torch.softmax(attention_scores, dim=-1)

        # An all-padding row would otherwise receive a numerically valid but
        # meaningless softmax. Zero it and renormalize real rows defensively.
        attention_weights = attention_weights * edge_mask.to(attention_weights.dtype)
        attention_weights = attention_weights / attention_weights.sum(
            dim=-1, keepdim=True
        ).clamp_min(torch.finfo(attention_weights.dtype).eps)

        updated_vectors = torch.bmm(attention_weights, path_vectors)
        return updated_vectors * path_mask.to(updated_vectors.dtype).unsqueeze(-1)


class SparseERNet(nn.Module):
    """Stack of sparse ERNet layers; V5 currently instantiates one layer."""

    def __init__(
        self,
        hidden_size: int,
        num_layers: int = 1,
        attention_hidden_size: int = 64,
    ):
        super().__init__()
        if num_layers < 1:
            raise ValueError("SparseERNet requires at least one layer")
        self.layers = nn.ModuleList(
            [
                SparseERNetLayer(hidden_size, attention_hidden_size)
                for _ in range(num_layers)
            ]
        )

    def forward(
        self,
        path_vectors: torch.Tensor,
        path_mask: torch.Tensor,
        adjacency: torch.Tensor,
    ) -> torch.Tensor:
        for layer in self.layers:
            path_vectors = layer(path_vectors, path_mask, adjacency)
        return path_vectors
