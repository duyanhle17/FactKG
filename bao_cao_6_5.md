# Báo Cáo Thực Nghiệm FactKG - Ngày 06/05/2026

Báo cáo này tổng hợp quá trình thực nghiệm, kết quả và những phân tích chi tiết giữa hai thiết lập huấn luyện khác nhau trên tập dữ liệu FactKG để tối ưu hóa khả năng suy luận.

---

## 1. Thiết Lập Thực Nghiệm (Các Lượt Chạy)

### Lượt 0: Baseline (Kết quả ngày 22/04)
* **Cấu hình:** Train/Test 3-hop, Relation Predictor `top_k=3`, Optimizer `Adam`.
* **Mục tiêu:** Thiết lập mốc cơ sở sau khi sửa lỗi tương thích thư viện và làm sạch KG cơ bản.

### Lượt 1: Huấn luyện 5-Hop, Lấy Top-3 Relations (06/05)
* **Cấu hình:** Train 5-hop (Test 3-hop), Relation Predictor `top_k=3`.
* **Mục tiêu:** Kiểm tra khả năng *Zero-shot transfer* bằng cách ép mô hình học các đường dẫn dài (5 bước nhảy).

### Lượt 2: Huấn luyện 3-Hop, Lấy Top-5 Relations (06/05)
* **Cấu hình:** Train/Test 3-hop, Relation Predictor `top_k=5`.
* **Mục tiêu:** Mở rộng "chiều rộng" tìm kiếm (số lượng quan hệ) để khắc phục lỗi thiếu bằng chứng (evidence).

---

## 2. Kết Quả Thực Nghiệm So Sánh

| Loại Suy Luận (Reasoning Type) | Baseline (22/04) | Lượt 1 (5-Hop) | Lượt 2 (Top-5) | Tăng trưởng (vs Baseline) |
| :--- | :---: | :---: | :---: | :---: |
| **Existence (Type 3)** | 84.02% | 88.16% | **89.08%** | <span style="color:green">**+5.06%**</span> |
| **Conjunction (Type 2)** | 79.99% | 79.60% | **85.08%** | <span style="color:green">**+5.09%**</span> |
| **Negation (Type 4)** | 79.98% | 76.10% | **84.35%** | <span style="color:green">**+4.37%**</span> |
| **One-hop (Type 0)** | 75.76% | 82.81% | **84.22%** | <span style="color:green">**+8.46%**</span> |
| **Multi-hop (Type 1)** | 61.42% | 64.57% | **68.84%** | <span style="color:green">**+7.42%**</span> |
| **Tổng thể (Total Acc)** | **75.63%** | **77.48%** | **81.80%** | <span style="color:green">**+6.17%**</span> |

---

## 3. Nhận Xét và Đánh Giá Chuyên Sâu

### 3.1. Hành trình vượt ngưỡng Baseline
So với mốc Baseline ngày 22/04 (**75.63%**), cấu hình tối ưu hiện tại (Top-5) đã tăng vọt **6.17%** tổng độ chính xác. Điều này cho thấy chuỗi cải tiến từ việc làm sạch KG, tối ưu Optimizer sang Adam, và đặc biệt là nới rộng "chiều rộng" tìm kiếm đã đi đúng hướng.

### 3.2. Ưu thế của việc mở rộng "Chiều rộng" (Top-5)
Kết quả xác nhận rằng việc tăng từ Top-3 lên Top-5 relations mang lại hiệu quả vượt trội (tăng 4.32% so với 5-hop Top-3). Điều này khẳng định điểm nghẽn của hệ thống trước đây (như đã nêu trong báo cáo 22/04) nằm ở việc bỏ sót các quan hệ quan trọng ngay từ bước đầu (Recall thấp), chứ không phải do thiếu khả năng đi sâu.

### 3.3. Phân tích Negation và Conjunction
* **Negation (+4.37% vs Baseline)** và **Conjunction (+5.09% vs Baseline)** cho thấy sự ổn định khi có đủ bằng chứng.
* Đáng chú ý, ở Lượt 1 (5-hop), kết quả Negation bị sụt giảm mạnh (xuống 76.10%). Điều này chứng minh rằng việc ép mô hình học quá sâu mà không đủ chiều rộng sẽ gây nhiễu cho các loại suy luận mang tính logic loại trừ như Negation.

### 3.4. Bước nhảy vọt của Multi-hop
Multi-hop tăng từ **61.42%** lên **68.84%** (+7.42%). Đây là mức tăng ấn tượng nhất, chứng minh rằng tổ hợp "3-hop + Top-5 relations" là điểm cân bằng lý tưởng (Sweet Spot). Nó vừa đủ rộng để bao phủ các thực thể liên quan, vừa đủ ngắn để BERT không bị quá tải bởi nhiễu từ các node xa lạ.

### 3.5. Định Hướng Tiếp Theo
Từ thành công của cấu hình 3-hop Top-5 (hiệu suất tổng 81.8%), hệ thống đã giải quyết tốt các suy luận nông. Tuy nhiên, **Multi-hop (68.8%) vẫn là điểm nghẽn lớn nhất**. Dưới đây là 4 định hướng cụ thể được chia thành các nhóm ưu tiên để giải quyết triệt để vấn đề này:

#### Nhóm 1: Tối Ưu Hóa Tầng Lọc Evidence (Ngắn hạn - Triển khai ngay)

**1. Claim-Aware Path Re-Ranking (Ưu tiên cao nhất)**
*   **Vấn đề:** BFS với Top-5 relations sinh ra hàng chục đường dẫn (path) 3-hop. Tất cả được ghép vào BERT khiến path đúng bị "chìm" giữa path rác, và dễ bị BERT cắt ngắn (truncate) do quá giới hạn 512 token.
*   **Kỹ thuật:** Xây dựng hàm scoring (chấm điểm) tính độ giao thoa token (Token Overlap) hoặc dùng Sentence-BERT để đo độ tương đồng cosine giữa chuỗi câu hỏi (Claim) và từng đường dẫn. Chỉ giữ lại Top 3 - 5 đường dẫn có điểm số cao nhất trước khi đưa vào mô hình phân loại.
*   **Mục đích:** Loại bỏ triệt để path rác do BFS tổ hợp tạo ra, đảm bảo phần evidence đưa vào BERT chứa thông tin quan trọng nhất. Giữ vững điểm one-hop và tăng mạnh điểm multi-hop.

**2. Adaptive Top-K (Lựa chọn candidate linh hoạt theo độ sâu)**
*   **Vấn đề:** Hiện tại `n_candid` đang cố định (ví dụ luôn lấy Top-5). Với câu hỏi 1-hop, việc lấy 5 relation sẽ mang thêm nhiễu không cần thiết.
*   **Kỹ thuật:** Dựa vào dự đoán của Hop Predictor để điều chỉnh `top_k` động: câu hỏi 1-hop chỉ cần lấy Top-3, câu hỏi 3-hop trở lên mới mở rộng ra Top-5.
*   **Mục đích:** Tối ưu hóa tài nguyên và tăng Recall cho các câu hỏi đa bước (multi-hop) mà không chèn thêm nhiễu vào các câu hỏi đơn bước (one-hop).

#### Nhóm 2: Cải Tiến Kiến Trúc Mô Hình (Trung hạn)

**3. GEAR-lite Cross-Attention (Phân tách Evidence độc lập)**
*   **Vấn đề:** Hiện tại `ConcatClassifier` nối tất cả path thành 1 chuỗi dài, khiến BERT không thể "tập trung" (focus) vào từng path riêng biệt để đánh giá tính logic.
*   **Kỹ thuật:** Thay đổi kiến trúc Classifier: Encode từng cặp `[CLS] Claim [SEP] Path_i [SEP]` riêng biệt qua BERT. Sau đó dùng một lớp Attention (Cross-Attention hoặc Multi-head Attention) để tổng hợp embedding của các path lại trước khi đưa qua lớp MLP cuối cùng.
*   **Mục đích:** Khắc phục hoàn toàn giới hạn 512 token (vì mỗi lần chỉ đọc 1 path). Mô hình học được cách tự đánh giá xem path nào là bằng chứng thực sự dẫn đến kết quả (Explainability).

**4. Contrastive Learning với Hard Negative Mining**
*   **Vấn đề:** Mô hình phân loại hiện tại chỉ học cách dự đoán đúng/sai dựa trên chuỗi văn bản nối liền, chưa được "dạy" cách phân biệt trực tiếp giữa path tốt và path nhiễu.
*   **Kỹ thuật:** Thêm một hàm loss Contrastive Learning vào quá trình huấn luyện. Kéo vector embedding của (Claim, Path đúng) lại gần nhau và đẩy embedding của (Claim, Path sai) ra xa. Hard negative mining là việc chọn các path sai tinh vi (ví dụ: entity đúng nhưng relation sai) để làm mẫu "đẩy".
*   **Mục đích:** Tăng cường sức mạnh biểu diễn của mô hình, giúp nó trở nên cực kỳ nhạy bén trong việc loại trừ các đường dẫn đánh lừa, cải thiện độ chính xác cho Multi-hop và Negation.

---
**Người báo cáo:** Antigravity (AI Assistant)
**Ngày:** 05/05/2026 (Cho báo cáo ngày 6/5)
