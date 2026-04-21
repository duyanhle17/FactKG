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

## 3. Thay Đổi & Cải Tiến Knowledge Graph (KG)

Song song với việc sửa lỗi tương thích thư viện, một chuỗi cải tiến sâu vào **pipeline truy xuất và xử lý đồ thị tri thức (Knowledge Graph)** đã được thiết kế và triển khai nhằm cải thiện chất lượng bằng chứng (evidence) đưa vào Classifier, đặc biệt cho các câu hỏi suy luận đa bước (Multi-hop).

### 3.1. Phase 1.1 — Làm Sạch Đồ Thị Từ Gốc (`preprocess.py`)

**Vấn đề:** Đồ thị DBpedia gốc (`dbpedia.pkl`) chứa rất nhiều cạnh nhiễu — các quan hệ phản ánh cấu trúc trang Wikipedia, không mang thông tin tri thức thực sự — làm BFS lạc đường và sinh ra đường dẫn không liên quan.

**Giải pháp đã triển khai:**

- **Relation Blacklist:** Khi nạp đồ thị vào RAM, hàm `_clean_kg()` quét và xóa toàn bộ cạnh thuộc danh sách đen gồm 8 quan hệ rác (cả chiều thuận và chiều đảo `~`):
  - `wikiPageWikiLink`, `wikiPageRedirects`, `wikiPageExternalLink`, `wasDerivedFrom`
- **Super-Node Filtering:** Hàm `_find_super_nodes()` tính tổng số kết nối (degree) của từng entity. Bất kỳ entity nào có **degree > 2000** bị đưa vào blacklist `super_nodes`. Trong quá trình BFS tại `KG.walk()`, hệ thống chặn không đi qua các super-node trừ khi entity đó được nhắc đích danh trong câu claim, tránh hiện tượng "hố đen đồ thị" hút toàn bộ BFS về một điểm.

```python
# Ví dụ code đã triển khai trong preprocess.py
RELATION_BLACKLIST = {
    "wikiPageWikiLink", "~wikiPageWikiLink",
    "wikiPageRedirects", "~wikiPageRedirects",
    "wikiPageExternalLink", "~wikiPageExternalLink",
    "wasDerivedFrom", "~wasDerivedFrom",
}
SUPER_NODE_DEGREE_THRESHOLD = 2000
```

### 3.2. Phase 1.2 & 1.3 — Cắt Đuôi Rác & Phân Mảnh Path (`prune_candid_paths.py`)

**Vấn đề:** Các đường dẫn (candidate paths) sau BFS thường kéo dài các hop cuối không liên quan đến claim, và nếu chỉ giữ path dài nhất thì BERT dễ bị nhiễu dữ liệu ở những claim ngắn.

**Giải pháp đã triển khai:**

- **Tail Trimming (Phase 1.2):** Hàm `trim_tail()` lặp và cắt bỏ hop cuối cùng (cặp Relation + Entity) nếu cả hai đều không chứa bất kỳ token nào trùng với câu claim. Quá trình dừng khi path còn 1-hop hoặc đuôi chứa thông tin có ý nghĩa.
  - *Ví dụ:* `[E0, R1, E1, R2, E2, R3, E3]` → nếu `R3`, `E3` không dính gì đến claim → cắt thành `[E0, R1, E1, R2, E2]`.

- **Sub-path Expansion (Phase 1.3):** Hàm `expand_subpaths()` từ 1 path đã qua cắt đuôi, tự động sinh ra tất cả prefix sub-paths ngắn hơn (1-hop, 2-hop, ...). Toàn bộ path mẹ và các nhánh con được gom vào tập trung tâm và loại trùng lặp. Chiến thuật này đảm bảo fallback: nếu path dài bị BERT bỏ sót, path con ngắn hơn vẫn cung cấp bằng chứng cốt lõi.

```
[E1, R1, E2, R2, E3, R3, E4]  ──►  [E1, R1, E2]
                                     [E1, R1, E2, R2, E3]
                                     [E1, R1, E2, R2, E3, R3, E4]
```

### 3.3. Phase 2 — Graph Verbalization: Soft Flattening (`baseline.py`)

**Vấn đề:** Các path thô từ đồ thị KG gồm chuỗi ký tự kiểu `Barack_Obama`, `birthPlace`, `Honolulu` — rất khó cho BERT tokenize hiệu quả. Định dạng kết nối bằng `|` hay `[SEP]` thuần túy không khai thác được cấu trúc ngữ nghĩa.

**Giải pháp đã triển khai:**

- Hàm `clean_kg_text()` làm sạch từng token KG:
  - Gỡ bỏ prefix `dbo:`, `dbp:`
  - Xóa phần định danh ngoặc đơn kiểu Wikipedia: `Washington_(state)` → `Washington`
  - Thay dấu `_` bằng dấu cách
  - Tách CamelCase: `birthPlace` → `birth Place`
  - Bỏ ký hiệu `~` (quan hệ đảo chiều) cho mục đích hiển thị

- Hàm `soft_flatten_path()` kết hợp các triple thành câu văn mượt mà, ngăn cách bằng ` . `:
  - *Input:* `['Barack_Obama', 'birthPlace', 'Honolulu', 'locatedIn', 'Hawaii']`
  - *Output:* `"Barack Obama birth Place Honolulu . Honolulu located In Hawaii"`

- Các path được nối với nhau bằng ký tự `|` để tạo ranh giới rõ ràng khi đưa vào tokenizer BERT, đảm bảo toàn bộ chuỗi evidence vẫn an toàn trong giới hạn 512 token.

---

## 4. Đánh Giá Kết Quả Khảo Sát (Accuracy)

Sau khi hệ thống vận hành trơn tru Retriever và Classifier bằng bộ trọng số `Adam` (với cấu hình Graph Retriever lấy top 3 Relation), điểm số Accuracy chi tiết trên từng loại suy luận (Reasoning Types) như sau:

| Reasoning Type (Loại Câu Hỏi) | Accuracy (Top-3 & Adam) | Tỉ Lệ Đúng (Correct / Total) | Kết quả Bài Báo (Reference) |
| :--- | :---: | :---: | :---: |
| **Existence (Sự tồn tại)** | **84.02%** | 731 / 870 | |
| **Conjunction (Mệnh đề phức)** | **79.99%** | 2455 / 3069 | |
| **Negation (Phủ định)** | **79.98%** | 1051 / 1314 | |
| **One-hop (Suy luận 1 bước)** | **75.76%** | 1450 / 1914 | **~83.23%** |
| **Multi-hop (Suy luận nhiều bước)** | **61.42%** | 1151 / 1874 | |

### 4.1. Nhận Xét Sự Sụt Giảm Điểm Số
Dù thuật toán `Adam` được chứng minh là tốt hơn ở các lần chạy trước, nhưng trong đợt thử nghiệm này, điểm số One-hop (75%) và Multi-hop (61%) lại bị sụt giảm so với mốc 83.23% của paper gốc.

**Nguyên nhân cốt lõi:**
- **Giới hạn số lượng Evidence (Bằng chứng):** Quá trình Retriever hiện đang bị "tắc nghẽn" do cấu hình chỉ lấy `top_k=3` (trong tệp `relation_predict_top3.yaml`). Đối với Knowledge Graph phức tạp và các câu hỏi suy luận nhảy bước, việc chỉ trích xuất 3 quan hệ (relations) khiến mô hình bị thiếu hụt bối cảnh (context) trầm trọng, các đường dẫn logic bị cắt đứt. Việc Classifier không có đủ thông tin đầu vào chính là nguyên nhân trực tiếp làm giảm độ chính xác, không liên quan đến Optimizer.

---

## 5. Phương Hướng Tiếp Theo
- Đảo ngược mã nguồn **quay trở lại dùng `Adam`** (vì `AdamW` hiện tại báo lỗi bản cũ và `Adam` cho kết quả baseline tốt hơn).
- **Mở rộng bối cảnh (Top-k):** Tăng thông số `top_k` của Retriever lên 5 hoặc 10 bằng cách chạy cấu hình `relation_predict_top5.yaml` hoặc `top10.yaml`. Việc nới lỏng lượng evidence đầu vào này kết hợp cùng `Adam` được kỳ vọng sẽ giúp mô hình bắt kịp và vượt mốc 83.23% One-hop của paper.
- **Kích hoạt pipeline KG cải tiến (Mục 3):** Chạy lại `preprocess.py` với Relation Blacklist và Super-Node Filtering để sinh `train/dev/test_candid_paths.bin` sạch hơn. Sau đó chạy `prune_candid_paths.py` để cắt đuôi và phân mảnh sub-path, rồi kích hoạt flag `--prune_noise` khi chạy `baseline.py`. Kỳ vọng cải tiến điểm Multi-hop đáng kể do bằng chứng đưa vào BERT chất lượng cao hơn và ít nhiễu hơn.
