"""Lệnh riêng để sinh candidate cho R1--R4.

File này không chứa thuật toán mới. Nó chỉ biến các tham số terminal thành lời
gọi ``prepare_input(..., retrieval_mode='faico_lite')``. Tách lệnh này ra giúp
không phải nhét thêm nhiều cờ retrieval vào ``baseline.py`` vốn phụ trách train
classifier.
"""

import argparse

from preprocess import prepare_input


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Sinh candidate Faico-Lite có thứ tự xác định cho GEARLite. "
            "Không ghi đè artifact legacy."
        )
    )
    parser.add_argument("--data_path", required=True, help="Thư mục chứa factkg_{train,dev,test}.pickle")
    parser.add_argument("--kg_path", required=True, help="Đường dẫn KG DBpedia dạng pickle")
    parser.add_argument("--n_candid", default="5", help="Số relation top-N từ relation predictor")
    parser.add_argument("--output_dir", required=True, help="Thư mục mới chứa .bin, report và manifest của lần chạy")
    parser.add_argument("--run_name", required=True, help="Tên riêng của lần chạy, ví dụ r1_top5")
    parser.add_argument(
        "--include_shorter_paths",
        action="store_true",
        help="R2+: sinh relation chain dài từ 1 đến H dự đoán",
    )
    parser.add_argument(
        "--relation_budget",
        default=1,
        type=int,
        help="R1/R2 dùng 1; R3 dùng 2 để một relation được lặp hai lần",
    )
    parser.add_argument(
        "--dominance_audit",
        action="store_true",
        help="R4: so raw dominance Faico với full-path; artifact vẫn không bị cắt",
    )
    parser.add_argument(
        "--report_max_paths",
        default=32,
        type=int,
        help="Chỉ dùng để thống kê top-K trong report, không cắt path được lưu",
    )
    parser.add_argument(
        "--store_max_paths",
        default=None,
        type=int,
        help="Giữ tối đa K path/claim theo đúng thứ tự baseline.py dùng, để giới hạn RAM",
    )
    parser.add_argument(
        "--max_expanded_states",
        default=None,
        type=int,
        help=(
            "Giới hạn số trạng thái DFS cho mỗi claim test-style; claim bị cắt "
            "được ghi trong retrieval report. Không dùng cho train/dev gold."
        ),
    )
    parser.add_argument(
        "--test_only_candidates",
        action="store_true",
        help="Chỉ sinh test candidate; dùng cho R2/R3 khi E2 đã train ở R1",
    )
    parser.add_argument(
        "--resume_test",
        action="store_true",
        help=(
            "Save each completed test claim to SQLite and resume on rerun. "
            "Requires --test_only_candidates."
        ),
    )
    parser.add_argument(
        "--retry_limited_at",
        type=int,
        default=None,
        help=(
            "Rerun only previously expansion-limited test claims at this larger "
            "state cap; requires --resume_test and the original --max_expanded_states."
        ),
    )
    parser.add_argument(
        "--search_schedule",
        choices=("dfs", "round_robin"),
        default="dfs",
        help=(
            "DFS is the unchanged R3 default. round_robin interleaves "
            "(entity, relation-chain) branches within a fixed test search budget."
        ),
    )
    parser.add_argument(
        "--relation_prediction_path",
        default=None,
        help="Tùy chọn: đường dẫn rõ ràng tới test_relations_topN.json",
    )
    parser.add_argument(
        "--hop_prediction_path",
        default=None,
        help="Tùy chọn: đường dẫn rõ ràng tới predictions_hop.json",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Chủ động ghi đè artifact đã có cùng tên chạy",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    # Script này luôn dùng Faico-Lite. Legacy vẫn chạy bằng baseline.py như cũ.
    prepare_input(
        data_path=args.data_path,
        kg_path=args.kg_path,
        n_candid=args.n_candid,
        retrieval_mode="faico_lite",
        output_dir=args.output_dir,
        run_name=args.run_name,
        include_shorter_paths=args.include_shorter_paths,
        relation_budget=args.relation_budget,
        dominance_audit=args.dominance_audit,
        report_max_paths=args.report_max_paths,
        store_max_paths=args.store_max_paths,
        max_expanded_states=args.max_expanded_states,
        test_only_candidates=args.test_only_candidates,
        resume_test=args.resume_test,
        retry_limited_at=args.retry_limited_at,
        search_schedule=args.search_schedule,
        relation_prediction_path=args.relation_prediction_path,
        hop_prediction_path=args.hop_prediction_path,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
