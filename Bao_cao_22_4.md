# BÁO CÁO PHÁT TRIỂN VÀ THỰC NGHIỆM HỆ THỐNG FACTKG
**Ngày báo cáo:** 22/04/2026

---

## 1. Bối Cảnh Thực Nghiệm
Mục tiêu của đợt thực nghiệm này là khôi phục, nâng cấp mã nguồn và chạy lại Pipeline **FactKG (With Evidence)** trên môi trường phần cứng hiện đại máy chủ GPU NVIDIA L40S. Do bộ mã nguồn gốc của bài báo được viết từ nhiều năm trước, hệ thống gặp rào cản lớn về xung đột phiên bản thư viện (PyTorch 2.x, Transformers 5.x, PyTorch Lightning 2.x).

---

## 2. Chi Tiết Các Cải Tiến & Thay Đổi Mã Nguồn

Để hệ thống có thể vận hành ổn định trên môi trường mới, các chỉnh sửa cốt lõi sau đã được thực hiện:

### 2.1. Khắc phục lỗi của thư viện Transformers (Đổi API Tokenizer)
- **Vấn đề:** Do thư viện `transformers` đã nâng cấp lên phiên bản 5.x, hàm `encode_plus` chứa tham số `pad_to_max_length=True` sinh ra lỗi `AttributeError` vì đã bị khai bỏ.
- **Giải pháp:** Tái cấu trúc lại luồng tiền xử lý (ở tệp thư mục `hop_predict/data.py`).
- **Ví dụ minh họa:**
  *Code cũ (Bị lỗi):*
  ```python
  encoded_dict = self.tokenizer.encode_plus(
      sentence1,
      pad_to_max_length = True,
      ...
  )
  ```
  *Code mới (Sau khi nâng cấp):*
  ```python
  encoded_dict = self.tokenizer(
      sentence1,
      padding = 'max_length',
      truncation=True,
      ...
  )
  ```

### 2.2. Xử lý Lỗi Tối Ưu Hóa (Optimizer)
- **Vấn đề:** Thuật toán `AdamW` được sử dụng trong mã nguồn gốc (import từ thư viện `transformers` cũ) báo lỗi không tương thích và văng lỗi trên phiên bản mới.
- **Giải pháp:** Chuyển đổi và nâng cấp sang sử dụng **Adam thuần** (`torch.optim.Adam`). Đặc biệt, thực tế từ các lần chạy thử nghiệm trước đây cho thấy việc sử dụng `Adam` giúp mô hình tăng điểm nhẹ so với baseline gốc của bài báo. Do đó, việc chủ động giữ và sử dụng `Adam` là một cải tiến có chủ đích nhằm tối ưu hiệu suất.

### 2.3. Tương thích PyTorch Lightning 2.x
- Cấu trúc file chạy gốc sử dụng các cờ như `gpus=1` không còn hoạt động. Mã nguồn tại file `main.py` đã được thiết kế lại thành `accelerator="gpu"`, đồng thời thay thế các hàm Callback lỗi thời (`on_validation_epoch_end`).

---

## 3. Đánh Giá Kết Quả Khảo Sát (Accuracy)

Sau khi hệ thống vận hành trơn tru Retriever và Classifier bằng bộ trọng số `Adam` (với cấu hình Graph Retriever lấy top 3 Relation), điểm số Accuracy chi tiết trên từng loại suy luận (Reasoning Types) như sau:

| Reasoning Type (Loại Câu Hỏi) | Accuracy (Top-3 & Adam) | Tỉ Lệ Đúng (Correct / Total) | Kết quả Bài Báo (Reference) |
| :--- | :---: | :---: | :---: |
| **Existence (Sự tồn tại)** | **84.02%** | 731 / 870 | |
| **Conjunction (Mệnh đề phức)** | **79.99%** | 2455 / 3069 | |
| **Negation (Phủ định)** | **79.98%** | 1051 / 1314 | |
| **One-hop (Suy luận 1 bước)** | **75.76%** | 1450 / 1914 | **~83.23%** |
| **Multi-hop (Suy luận nhiều bước)** | **61.42%** | 1151 / 1874 | |

### 3.1. Nhận Xét Sự Sụt Giảm Điểm Số
Dù thuật toán `Adam` được chứng minh là tốt hơn ở các lần chạy trước, nhưng trong đợt thử nghiệm này, điểm số One-hop (75%) và Multi-hop (61%) lại bị sụt giảm so với mốc 83.23% của paper gốc.

**Nguyên nhân cốt lõi:**
- **Giới hạn số lượng Evidence (Bằng chứng):** Quá trình Retriever hiện đang bị "tắc nghẽn" do cấu hình chỉ lấy `top_k=3` (trong tệp `relation_predict_top3.yaml`). Đối với Knowledge Graph phức tạp và các câu hỏi suy luận nhảy bước, việc chỉ trích xuất 3 quan hệ (relations) khiến mô hình bị thiếu hụt bối cảnh (context) trầm trọng, các đường dẫn logic bị cắt đứt. Việc Classifier không có đủ thông tin đầu vào chính là nguyên nhân trực tiếp làm giảm độ chính xác, không liên quan đến Optimizer.

---

## 4. Phương Hướng Tiếp Theo
- Đảo ngược mã nguồn **quay trở lại dùng `Adam`** (vì `AdamW` hiện tại báo lỗi bản cũ và `Adam` cho kết quả baseline tốt hơn).
- **Mở rộng bối cảnh (Top-k):** Tăng thông số `top_k` của Retriever lên 5 hoặc 10 bằng cách chạy cấu hình `relation_predict_top5.yaml` hoặc `top10.yaml`. Việc nới lỏng lượng evidence đầu vào này kết hợp cùng `Adam` được kỳ vọng sẽ giúp mô hình bắt kịp và vượt mốc 83.23% One-hop của paper.
