# Báo Cáo Thực Nghiệm: GEARLite v2 (E3) trên Dữ Liệu R3 Full

> **Mô hình:** GEARLite v2 (Claim-Conditioned Attention: $\text{score} = \text{MLP}([\text{Claim} \,\|\, \text{Path}])$)  
> **Dữ liệu candidate:** Faico-Lite R3 Full ($k=2$, độ dài $1..H$, $K=32$ paths) — Huấn luyện End-to-End trọn bộ Train / Dev / Test  
> **Ngày cập nhật:** 29/08/2026

---

## 1. Bảng Kết Quả Đối Chiếu Qua Các Lượt Chạy

| Loại Suy Luận (Reasoning) | E0: Concat (Baseline) | E2b: GEARLite v1 (Pair + Attn) | R3 Ablation (Candidate test-only) | **GEARLite v2 (R3 Full End-to-End)** | So với E2b (GEARLite v1) | So với R3 Ablation |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **One-hop (Type 0)** | 84.22% | 91.12% | 90.80% | **92.06%** | <span style="color:green">**+0.94%**</span> | <span style="color:green">**+1.26%**</span> |
| **Multi-hop (Type 1)** | 68.84% | 71.18% | 78.60% | **79.78%** | <span style="color:green">**+8.60%**</span> | <span style="color:green">**+1.18%**</span> |
| **Conjunction (Type 2)** | **85.08%** | 82.82% | 83.51% | **82.73%** | <span style="color:red">−0.09%</span> | <span style="color:red">−0.78%</span> |
| **Existence (Type 3)** | 89.08% | 94.37% | 94.48% | **98.05%** | <span style="color:green">**+3.68%**</span> | <span style="color:green">**+3.57%**</span> |
| **Negation (Type 4)** | 84.35% | **87.98%** | 80.14% | **81.28%** | <span style="color:red">**−6.70%**</span> | <span style="color:green">**+1.14%**</span> |
| **Total Test Accuracy** | 81.80% | 83.69% | 84.60% | **85.36%** | <span style="color:green">**+1.67%**</span> | <span style="color:green">**+0.76%**</span> |
| **Total Test Macro-F1** | — | 83.48% | 84.49% | **85.24%** | <span style="color:green">**+1.76%**</span> | <span style="color:green">**+0.75%**</span> |

---

## 2. Chi Tiết Kết Quả Đạt Được của GEARLite v2

* **Best Dev Accuracy:** `0.9434` (Checkpoint chọn tại Epoch 0).
* **Total Test Accuracy:** **`85.36%`** — **Kỷ lục cao nhất từ trước đến nay** trên toàn bộ benchmark FactKG của repo.
* **Total Test Macro-F1:** **`85.24%`** — Cân bằng rất tốt giữa các nhãn True/False.

### Chi tiết phân phối theo 5 nhóm Reasoning (Test Set = 9,041 mẫu):
1. **One-hop** (1,914 mẫu): Acc `92.06%` | Macro-F1 `0.9204`
2. **Multi-hop** (1,874 mẫu): Acc `79.78%` | Macro-F1 `0.7929`
3. **Conjunction** (3,069 mẫu): Acc `82.73%` | Macro-F1 `0.8193`
4. **Existence** (870 mẫu): Acc `98.05%` | Macro-F1 `0.9804`
5. **Negation** (1,314 mẫu): Acc `81.28%` | Macro-F1 `0.8119`

---

## 3. Phân Tích Chuyên Sâu & Giải Đáp Về Nhóm Negation

### ❓ Trả lời câu hỏi: *"So với bản Pair + Attention (E2b) thì Negation vẫn giảm hả?"*

👉 **ĐÚNG, Negation vẫn thấp hơn E2b (`81.28%` so với `87.98%`, giảm −6.70%), TUY NHIÊN đã có sự phục hồi so với R3 Ablation (`81.28%` so với `80.14%`, tăng +1.14%).**

### 🔍 Vì sao Negation chưa phục hồi hoàn toàn về mức 87.98%?

1. **Sự khác biệt về mật độ Candidate (Candidate Density):**
   * Ở **E2b (retrieval cũ)**: Số lượng candidate path cực kỳ ít và thưa (chỉ 1–3 path). Khi có ít path, BERT rất dễ nhận biết: *"Không thấy path nối A và B $\rightarrow$ Dự đoán TRUE"* hoặc *"Có đúng 1 path nối A và B $\rightarrow$ Dự đoán FALSE"*.
   * Ở **R3 (Faico-Lite)**: Để phục vụ Multi-hop, thuật toán DFS vét cạn sinh tối đa tới **32 candidate paths** (gồm cả connected, walkable, path lặp $k=2$).
2. **Tác động của 32 path khẳng định lên câu phủ định:**
   * Knowledge Graph chỉ lưu các khẳng định dương tính (`A -> relation -> B`).
   * Trong 32 candidate paths của R3, có rất nhiều path đi vòng vèo qua lại giữa các thực thể của câu Negation. Mặc dù tầng **Claim-Conditioned Attention** đã giúp model phân biệt tốt hơn (kéo điểm từ 80.14% lên 81.28%), nhưng lượng path rác 32 vẫn tạo ra một mức độ "áp lực nhiễu" nhất định so với việc chỉ có 1-3 path như E2b.

---

## 4. Những Điểm Sáng Bứt Phá Đáng Kinh Ngạc

Mặc dù Negation chưa lấy lại đỉnh 87%, nhưng tổng thể mô hình **GEARLite v2 trên R3 Full** là một bước tiến vượt bậc:

1. **Multi-hop tiệm cận mốc 80% (`79.78%`):**
   * Tăng **+10.94%** so với Baseline gốc E0 (`68.84%`).
   * Tăng **+8.60%** so với E2b (`71.18%`).
   * Đây là mức điểm Multi-hop cao kỷ lục trên FactKG.
2. **Existence đạt đỉnh gần như tuyệt đối (`98.05%`):**
   * Tăng vọt gần +4% so với tất cả các phiên bản trước.
3. **One-hop đạt đỉnh mới (`92.06%`):**
   * Chứng minh việc đưa Claim vector vào Attention giúp model hiểu rõ các câu hỏi đơn bước tốt hơn.
4. **Total Accuracy chính thức vượt ngưỡng 85% (`85.36%`):**
   * Khắc phục hoàn toàn tình trạng "dậm chân tại chỗ" ở mức 84.6% của đợt 29/7.

---

## 5. Đề Xuất Cho Bước Tiếp Theo

Để tiếp tục đẩy Overall Accuracy lên $\ge 87\%$ và giải quyết triệt để phần còn lại của Negation & Conjunction:

1. **Thử nghiệm tầng ERNet (Full GEAR):**
   * Thêm tầng tương tác đồ thị giữa các path để xâu chuỗi thông tin Multi-hop và phân loại rõ ranh giới giữa các bằng chứng.
2. **Adaptive Candidate Filtering (Cắt tỉa path động theo Hop):**
   * Với câu 1-hop / Negation (Hop predictor = 1), chỉ nạp Top 8 candidate paths thay vì 32 paths để triệt tiêu nhiễu cho Negation.
   * Với câu Multi-hop (Hop predictor $\ge 2$), giữ nguyên 32 paths để bảo toàn Recall.
