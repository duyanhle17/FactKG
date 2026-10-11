# So sánh V4 theo checkpoint và candidate test (9/10/2026)

Cùng 9.041 claim test, `max_paths=32`, seed 42. Mỗi cột ghi **candidate dùng khi train V4 → candidate dùng khi test**. `R3 gốc` (`predictions_hybrid`) và `R3 rerun` (`predictions_hybrid_rerun`) là **hai checkpoint khác nhau**. `Legacy` là checkpoint train ngày 7/10. Các lượt test chéo dùng `--test_only`, không train lại và không dựng lại candidate.

## Accuracy (%)

| Nhóm (số claim) | V4 Legacy → test Legacy | V4 Legacy → test R3 | V4 R3 gốc → test Legacy | V4 R3 gốc → test R3 | V4 R3 rerun → test Legacy | V4 R3 rerun → test R3 |
|---|---:|---:|---:|---:|---:|---:|
| One-hop (1.914) | 87,36 | 75,18 | 89,08 | 91,33 | 89,60 | 91,64 |
| Multi-hop (1.874) | 68,84 | 68,46 | 63,82 | 80,84 | 63,45 | 81,16 |
| Conjunction (3.069) | 76,34 | 68,30 | 84,56 | 84,56 | **85,21** | 84,03 |
| Existence (870) | 93,22 | 93,10 | 92,76 | 92,76 | 94,37 | **94,94** |
| Negation (1.314) | 84,93 | 79,76 | 84,02 | 85,92 | 87,37 | **88,43** |
| **Overall (9.041)** | **79,99** | **73,84** | **81,93** | **86,21** | **82,82** | **86,74** |

## Macro-F1 (%)

| Nhóm | V4 Legacy → test Legacy | V4 Legacy → test R3 | V4 R3 gốc → test Legacy | V4 R3 gốc → test R3 | V4 R3 rerun → test Legacy | V4 R3 rerun → test R3 |
|---|---:|---:|---:|---:|---:|---:|
| One-hop | 87,36 | 74,76 | 89,07 | 91,30 | 89,59 | 91,62 |
| Multi-hop | 67,10 | 66,45 | 59,87 | 80,54 | 59,41 | 80,84 |
| Conjunction | 73,59 | 61,99 | 83,95 | 83,86 | **84,68** | 83,32 |
| Existence | 93,22 | 93,10 | 92,76 | 92,75 | 94,37 | **94,94** |
| Negation | 84,91 | 79,76 | 84,02 | 85,91 | 87,37 | **88,43** |
| **Overall** | **79,45** | **72,59** | **81,65** | **86,10** | **82,57** | **86,63** |

## Cách đọc

- Giữ **cùng checkpoint R3 rerun**, thay candidate test Legacy → R3: Overall **+3,92 điểm %**, Multi-hop **+17,71 điểm %**, nhưng Conjunction **−1,18 điểm %**. Lợi ích ở test tập trung vào Multi-hop, không phải Conjunction.
- Giữ **cùng checkpoint Legacy**, thay candidate test Legacy → R3: Overall **−6,15 điểm %**. Path R3 không tự động giúp một verifier được học trên candidate legacy; checkpoint và candidate test có tương tác.
- Trên **cùng candidate test Legacy**, checkpoint R3 rerun đạt Conjunction **85,21%** so với **76,34%** của checkpoint Legacy. Đây là khác biệt giữa hai lượt train/checkpoint, **chưa thể quy riêng** cho candidate train R3 vì cấu hình/quá trình train không hoàn toàn được kiểm soát.
- `R3 gốc` đạt **86,21%** khi tự test R3; mốc **86,74%** thuộc checkpoint `R3 rerun`. Không trộn hai mốc này trong cùng một phép trừ.

Nguồn: log và các file `test_pred_gearlite_v4_*.bin` của các lượt chạy trên máy GPU. Điểm được làm tròn từ log đến hai chữ số thập phân. Phép so sánh *trong cùng checkpoint* đo tác động của việc thay **file candidate test**; chỉ khi manifest xác nhận cùng JSON relation/hop mới có thể quy khác biệt đó riêng cho cách dựng path Legacy/R3.
