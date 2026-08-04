"""Lõi duyệt path cho thí nghiệm Faico-Lite.

File này chỉ chứa thuật toán duyệt KG. Nó được tách khỏi ``preprocess.py`` để
phần đọc/ghi dữ liệu FactKG không bị lẫn với phần duyệt graph và để có thể test
trên KG nhỏ một cách độc lập.

Khác với Faico gốc, ở đây bắt buộc giữ *toàn bộ chuỗi path đã serialize*.
GEARLite mã hóa từng cặp Claim--Path riêng; hai path cùng endpoint vẫn có thể
chứa evidence khác nhau.

R1: duyệt mọi path hợp lệ theo relation chain cố định, có thứ tự xác định.
R2: sinh thêm relation chain có độ dài từ 1 đến H.
R3: cho phép một relation xuất hiện tối đa ``relation_budget`` lần trong path.
R4: chỉ audit budget dominance của Faico, không dùng nó để cắt artifact.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


Path = Tuple[str, ...]


def _stable_key(value: object) -> str:
    """Tạo khóa sắp xếp cố định cho entity/relation.

    Mục đích là cùng input luôn sinh cùng candidate artifact, kể cả khi thứ tự
    tail trong dictionary của KG không cố định.
    """
    return str(value)


def _ordered_unique(values: Iterable[object]) -> List[object]:
    """Bỏ phần tử lặp nhưng giữ thứ tự điểm của predictor/Evidence."""
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def serialize_path(nodes: Sequence[object], relations: Sequence[object]) -> Path:
    """Đổi node và relation thành format path phẳng mà FactKG đang dùng.

    Ví dụ: nodes=[A, B, C], relations=[r1, r2]
    trở thành [A, r1, B, r2, C].
    """
    if len(nodes) != len(relations) + 1:
        raise ValueError("A path must contain exactly one more node than relations.")

    serialised: List[str] = [str(nodes[0])]
    for relation, node in zip(relations, nodes[1:]):
        serialised.extend((str(relation), str(node)))
    return tuple(serialised)


def normalise_relation_paths(raw_paths: Iterable[object]) -> List[Tuple[str, ...]]:
    """Chuẩn hóa Evidence hoặc path sinh ra thành tuple relation.

    Train/dev có thể chứa ``['r']`` hoặc ``[['r1', 'r2']]``; hàm này đưa hai
    dạng đó về một representation chung trước khi duyệt.
    """
    paths: List[Tuple[str, ...]] = []
    for raw_path in raw_paths:
        if isinstance(raw_path, str):
            path = (raw_path,)
        else:
            path = tuple(str(relation) for relation in raw_path)
        if path:
            paths.append(path)
    return paths


def build_relation_sequences(
    relations: Sequence[object],
    hop: int,
    include_shorter_paths: bool = False,
    relation_budget: int = 1,
) -> List[Tuple[str, ...]]:
    """Sinh relation chain theo ngân sách lặp relation kiểu k-BET.

    ``relation_budget=1`` tương đương ràng buộc cũ: relation không được lặp.
    ``relation_budget=2`` cho phép chain như r1 -> r2 -> r1.

    Không sắp xếp lại relation ở đây: thứ tự top-N từ relation predictor vẫn
    được giữ để path sinh ra ưu tiên relation có điểm dự đoán cao hơn.
    """
    if hop < 1:
        raise ValueError("hop must be at least 1")
    if relation_budget < 1:
        raise ValueError("relation_budget must be at least 1")

    ordered_relations = [str(relation) for relation in _ordered_unique(relations)]
    if not ordered_relations:
        return []

    lengths = range(1, hop + 1) if include_shorter_paths else (hop,)
    sequences: List[Tuple[str, ...]] = []

    def expand(prefix: List[str], used: Counter, target_length: int) -> None:
        if len(prefix) == target_length:
            sequences.append(tuple(prefix))
            return
        for relation in ordered_relations:
            if used[relation] >= relation_budget:
                continue
            used[relation] += 1
            prefix.append(relation)
            expand(prefix, used, target_length)
            prefix.pop()
            used[relation] -= 1

    for target_length in lengths:
        expand([], Counter(), target_length)
    return sequences


def _dominates(old_budget: Tuple[int, ...], current_budget: Tuple[int, ...]) -> bool:
    """Kiểm tra budget cũ có lớn hơn hoặc bằng budget mới ở mọi relation."""
    return all(old >= current for old, current in zip(old_budget, current_budget))


class DeterministicPathRetriever:
    """Duyệt mọi path FactKG có hướng cho các relation chain đã cho.

    ``dominance_mode='audit'`` chỉ đếm số state mà raw dominance của Faico sẽ
    cắt. Nó không xóa path. ``'prune'`` chỉ tồn tại để R4 so sánh hai kết quả;
    tuyệt đối không dùng output đó để train nếu chưa chứng minh tập serialized
    path giống hệt chế độ không cắt.
    """

    VALID_DOMINANCE_MODES = {"off", "audit", "prune"}

    def __init__(self, kg: Mapping[object, Mapping[object, Iterable[object]]], relation_budget: int = 1,
                 dominance_mode: str = "off") -> None:
        if relation_budget < 1:
            raise ValueError("relation_budget must be at least 1")
        if dominance_mode not in self.VALID_DOMINANCE_MODES:
            raise ValueError(
                "dominance_mode must be one of "
                f"{sorted(self.VALID_DOMINANCE_MODES)}"
            )
        self.kg = kg
        self.relation_budget = relation_budget
        self.dominance_mode = dominance_mode

    def get_tails(self, head: object, relation: object) -> List[object]:
        # Sort tail ở đúng một chỗ để R1 không còn phụ thuộc thứ tự dictionary.
        relation_map = self.kg.get(head, {})
        tails = relation_map.get(relation, ())
        return sorted(tails, key=_stable_key)

    def search(
        self,
        entities: Sequence[object],
        relation_paths_by_entity: Mapping[object, Iterable[object]],
        allowed_relations: Optional[Sequence[object]] = None,
        store_max_paths: Optional[int] = None,
    ) -> Tuple[Dict[str, List[List[str]]], Dict[str, int]]:
        """Trả về ``connected``/``walkable`` và thống kê cho một claim.

        ``allowed_relations`` chỉ có ở test, nơi path được tạo từ relation
        predictor. Nó phục vụ R4. Train/dev dùng Evidence gold nên không ép
        budget k lên Evidence; tránh làm thay đổi nhãn evidence có sẵn.

        ``store_max_paths`` giới hạn số path ghi vào artifact cho mỗi claim.
        Nó vẫn duyệt hết KG, nhưng chỉ giữ prefix có thể được ``baseline.py``
        dùng khi lấy ``connected + walkable`` rồi cắt top-K. Nhờ đó builder
        không tích lũy những path mà E2 không bao giờ encode.
        """
        if store_max_paths is not None and store_max_paths < 1:
            raise ValueError("store_max_paths must be at least 1 when provided")

        ordered_entities = sorted(_ordered_unique(entities), key=_stable_key)
        entity_set = set(ordered_entities)
        connected: List[List[str]] = []
        walkable: List[List[str]] = []
        # Dedup theo group là tương đương với set chung: một serialized path
        # luôn có endpoint cố định, nên khong the vua connected vua walkable.
        # Khi group da du top-K, khong can giu/nhin nho cac path ve sau nua.
        connected_seen = set()
        walkable_seen = set()
        diagnostics: Counter = Counter()
        stop_after_connected_limit = False

        audit_relations = (
            tuple(str(relation) for relation in _ordered_unique(allowed_relations))
            if allowed_relations is not None
            else tuple()
        )
        budget_history: Dict[Tuple[str, str, int, int], List[Tuple[int, ...]]] = defaultdict(list)

        def register(nodes: Sequence[object], relation_path: Sequence[str], start: object) -> None:
            nonlocal stop_after_connected_limit
            diagnostics["terminal_paths"] += 1
            if nodes[0] == nodes[-1]:
                diagnostics["self_loop_paths_skipped"] += 1
                return
            serialised = serialize_path(nodes, relation_path)
            is_connected = nodes[-1] in entity_set and nodes[-1] != start
            bucket = connected if is_connected else walkable
            seen = connected_seen if is_connected else walkable_seen

            if serialised in seen:
                diagnostics["duplicate_serialized_paths_removed"] += 1
                return
            if store_max_paths is not None and len(bucket) >= store_max_paths:
                # Khong dua path nay vao set: no nam sau prefix da du va khong
                # the anh huong top-K ma classifier doc tu artifact.
                diagnostics["terminal_paths_not_stored_due_to_limit"] += 1
                diagnostics["candidate_store_limit_reached"] = 1
                return

            seen.add(serialised)
            bucket.append(list(serialised))
            if is_connected and store_max_paths is not None and len(connected) >= store_max_paths:
                # connected luon dung truoc walkable trong baseline.py. Khi da
                # co K connected path theo thu tu DFS, top-K da co dinh va
                # phan con lai cua claim khong the thay doi input cua E2.
                stop_after_connected_limit = True
                diagnostics["search_stopped_after_connected_limit"] = 1

        for start in ordered_entities:
            raw_paths = relation_paths_by_entity.get(start, ())
            relation_paths = normalise_relation_paths(raw_paths)
            diagnostics["relation_sequences"] += len(relation_paths)

            for relation_path in relation_paths:
                target_length = len(relation_path)

                def visit(node: object, depth: int, nodes: List[object], used: Counter) -> None:
                    if stop_after_connected_limit:
                        return
                    diagnostics["expanded_states"] += 1
                    diagnostics["max_depth"] = max(diagnostics["max_depth"], depth)

                    # Raw dominance của Faico có thể cắt một prefix khác nhưng
                    # GEARLite vẫn cần encode prefix đó. Vì vậy mặc định chỉ
                    # ghi nhận để audit, không được phép return/cắt path.
                    if audit_relations:
                        remaining_budget = tuple(
                            max(0, self.relation_budget - used[relation])
                            for relation in audit_relations
                        )
                        history_key = (str(start), str(node), target_length, depth)
                        old_budgets = budget_history[history_key]
                        dominated = any(
                            _dominates(old_budget, remaining_budget)
                            for old_budget in old_budgets
                        )
                        if dominated:
                            diagnostics["dominance_detected"] += 1
                            if self.dominance_mode == "prune":
                                diagnostics["dominance_pruned_states"] += 1
                                return
                        if not dominated:
                            budget_history[history_key] = [
                                old_budget
                                for old_budget in old_budgets
                                if not _dominates(remaining_budget, old_budget)
                            ] + [remaining_budget]

                    if depth == target_length:
                        register(nodes, relation_path, start)
                        return

                    relation = relation_path[depth]
                    tails = self.get_tails(node, relation)
                    if not tails:
                        diagnostics["dead_end_states"] += 1
                        return
                    for tail in tails:
                        used[relation] += 1
                        visit(tail, depth + 1, nodes + [tail], used)
                        used[relation] -= 1
                        if stop_after_connected_limit:
                            return

                visit(start, 0, [start], Counter())
                if stop_after_connected_limit:
                    break
            if stop_after_connected_limit:
                break

        if store_max_paths is not None:
            # baseline.py luon uu tien connected truoc walkable. Trong luc
            # duyet chua biet se co bao nhieu connected, nen tam giu toi K
            # walkable; o day cat lai de artifact dung bang top-K legacy.
            remaining_walkable = max(0, store_max_paths - len(connected))
            if len(walkable) > remaining_walkable:
                diagnostics["walkable_paths_trimmed_after_connected_priority"] = (
                    len(walkable) - remaining_walkable
                )
                diagnostics["candidate_store_limit_reached"] = 1
                walkable = walkable[:remaining_walkable]

        diagnostics["connected_paths"] = len(connected)
        diagnostics["walkable_paths"] = len(walkable)
        diagnostics["total_paths"] = len(connected) + len(walkable)
        return {"connected": connected, "walkable": walkable}, dict(diagnostics)


def canonical_path_set(groups: Mapping[str, Iterable[Sequence[object]]]) -> set:
    """Đưa path về set chuẩn để R4 so sánh trước/sau khi thử cắt dominance."""
    return {
        tuple(str(item) for item in path)
        for group in ("connected", "walkable")
        for path in groups.get(group, ())
    }
