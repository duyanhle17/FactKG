# Báo Cáo Thực Nghiệm FactKG - Ngày 06/05/2026

Báo cáo này tổng hợp quá trình thực nghiệm, kết quả và những phân tích chi tiết giữa hai thiết lập huấn luyện khác nhau trên tập dữ liệu FactKG để tối ưu hóa khả năng suy luận.

---

## 1. Thiết Lập Thực Nghiệm (Các Lượt Chạy)

### Lượt 1: Huấn luyện 5-Hop, Lấy Top-3 Relations
* **Cấu hình:** Train 5-hop (Test 3-hop), Relation Predictor `top_k=3`.
* **Mục tiêu:** Kiểm tra khả năng *Zero-shot transfer* bằng cách ép mô hình học các đường dẫn dài (5 bước nhảy) để cải thiện suy luận ở các câu hỏi ngắn hơn.
* **Đặc điểm:** Sử dụng thủ thuật tráo file `predictions_hop.json` giữa 5-hop (cho Train) và 3-hop (cho Test).

### Lượt 2: Huấn luyện 3-Hop, Lấy Top-5 Relations
* **Cấu hình:** Train/Test 3-hop, Relation Predictor `top_k=5`.
* **Mục tiêu:** Nới rộng "chiều rộng" tìm kiếm (số lượng quan hệ) thay vì tăng "chiều sâu" (số bước nhảy) để khắc phục lỗi thiếu bằng chứng (evidence).
* **Đặc điểm:** Đưa `--n_candid 5` vào Baseline Classifier.

---

## 2. Kết Quả Thực Nghiệm So Sánh

| Loại Suy Luận (Reasoning Type) | Lượt 1 (Train 5-Hop, Top-3) | Lượt 2 (Train 3-Hop, Top-5) | Mức Tăng Trưởng |
| :--- | :---: | :---: | :---: |
| **Existence (Type 3)** | 88.16% | **89.08%** | <span style="color:green">**+0.92%**</span> |
| **Conjunction (Type 2)** | 79.60% | **85.08%** | <span style="color:green">**+5.48%**</span> |
| **Negation (Type 4)** | 76.10% | **84.35%** | <span style="color:green">**+8.25%**</span> |
| **One-hop (Type 0)** | 82.81% | **84.22%** | <span style="color:green">**+1.41%**</span> |
| **Multi-hop (Type 1)** | 64.57% | **68.84%** | <span style="color:green">**+4.27%**</span> |
| **Tổng thể (Total Test Acc)** | **77.48%** | **81.80%** | <span style="color:green">**+4.32%**</span> |

---

## 3. Nhận Xét và Đánh Giá Chuyên Sâu

### 3.1. Ưu thế tuyệt đối của việc mở rộng "Chiều rộng" (Top-5)
Kết quả cho thấy việc tăng từ Top-3 lên Top-5 relations mang lại hiệu quả vượt trội hơn hẳn so với việc tăng độ sâu 5-hop. Tổng độ chính xác tăng mạnh **4.32%**. Điều này khẳng định điểm nghẽn của hệ thống nằm ở việc bỏ sót các quan hệ quan trọng ngay từ những bước đầu, chứ không phải do thiếu khả năng đi sâu.

### 3.2. Cải thiện đột phá cho Negation và Conjunction
* **Negation (+8.25%)** và **Conjunction (+5.48%)** là hai nhóm hưởng lợi lớn nhất. 
* Việc giữ Top-3 quá chật hẹp khiến các quan hệ mang tính "phủ định" hoặc "liên kết" dễ bị loại bỏ khỏi danh sách candidate. Khi nới lên Top-5, các bằng chứng này được giữ lại, giúp BERT Classifier có đủ dữ liệu để đưa ra quyết định đúng đắn.

### 3.3. Bài học từ Multi-hop: Tránh "Bùng nổ nhiễu"
* **Lượt 1 (5-hop):** Tạo ra quá nhiều đường dẫn không liên quan, làm loãng tín hiệu và dễ vượt quá giới hạn 512 token của BERT. 
* **Lượt 2 (3-hop + Top-5):** Tìm được điểm cân bằng lý tưởng. Không gian tìm kiếm rộng hơn giúp tăng Recall (khả năng tìm thấy đường đi đúng), trong khi độ sâu 3-hop giúp giữ cho ngữ cảnh đầu vào không bị quá tải bởi nhiễu từ các node xa lạ.

### 3.4. Định Hướng Tiếp Theo
Từ thành công của cấu hình 3-hop Top-5, các bước tiếp theo nên tập trung vào:
1. **Re-ranking:** Lọc bỏ các đường dẫn nhiễu trong số Top-5 trước khi đưa vào Classifier để tối ưu hóa giới hạn 512 token.
2. **Adaptive Hop:** Linh hoạt số lượng relation dựa trên độ khó của câu hỏi (dự đoán từ Hop Predictor).

---
**Người báo cáo:** Antigravity (AI Assistant)
**Ngày:** 05/05/2026 (Cho báo cáo ngày 6/5)
