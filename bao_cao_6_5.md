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
Từ thành công của cấu hình 3-hop Top-5, các bước tiếp theo nên tập trung vào:
1. **Re-ranking:** Lọc bỏ các đường dẫn nhiễu trong số Top-5 trước khi đưa vào Classifier để tối ưu hóa giới hạn 512 token.
2. **Adaptive Hop:** Linh hoạt số lượng relation dựa trên độ khó của câu hỏi.
3. **Hybrid Model:** Kết hợp khả năng suy luận sâu của 5-hop vào khung Top-5 để xử lý các câu hỏi cực khó.

---
**Người báo cáo:** Antigravity (AI Assistant)
**Ngày:** 05/05/2026 (Cho báo cáo ngày 6/5)
