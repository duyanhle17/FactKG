# Kế Hoạch Cải Tiến Mô Hình GEAR (Mục Tiêu Deadline: 15/04)

Tài liệu này được biên soạn để vạch ra lộ trình học tập, nghiên cứu và thử nghiệm mã nguồn nhằm tối ưu hóa khả năng suy luận đồ thị đa bước (Multi-hop Reasoning) trên mô hình GEAR (FactKG). Tập trung trực tiếp vào giải quyết giới hạn "chỉ ghép chuỗi String của BERT" và hiện tượng phân rã đồ thị trên chuỗi dài.

---

## 1. Ôn Tập Nhanh: Hiểu Luồng Chạy Của GEAR (With Evidence)

Để tác động đúng chỗ, ta cần nhớ hệ thống chia làm **2 giai đoạn độc lập**. Ta KHÔNG cần sửa toàn bộ mà chỉ "đánh tạt sườn" vào giai đoạn nạp dữ liệu và Classifier.

*   **Giai đoạn 1 (Retriever):** Các file `data_preprocess.py`, `relation_predict`, `hop_predict` đọc `factkg_train.pickle` và KG `dbpedia_...pickle` để sinh ra các **ứng viên đồ thị rác + thực**. Dữ liệu này được đóng gói cất vào `train_candid_paths.bin`, `dev_candid_paths.bin`, và `test_candid_paths_topX.bin`.
*   **Giai đoạn 2 (Classifier):** Mọi thí nghiệm sẽ diễn ra ở file `FactKG/with_evidence/classifier/baseline.py`. Nó load danh sách đồ thị ứng viên `.bin` kết hợp nhãn `.pickle` để train.

---

## 2. Điểm Nghẽn Tử Huyệt Trong Source Code Hiện Tại

Tại file `baseline.py`, phần hàm Tokenize Dữ liệu (tại DataCollator, dòng 116-125) đang xử lý rất thô sơ:
```python
seq_evidence = [f"{self.tokenizer.sep_token.join(evi)} {self.tokenizer.sep_token}" for evi in evidence]
tokenized_evidence = self.tokenizer(
    seq_evidence, 
    max_length=512-len(tokenized_claim["input_ids"][0]), ...
)
```
**Hậu quả:** 
Graph bị "đập bẹp" cấu trúc vòng và các mối quan hệ đa chiều, trở thành một câu text vô hồn được ghép bằng dấu ngang `[SEP]`. Chạm ngưỡng 512 token, thư viện xẻo cụt phần cuối - khiến các chặng ở đuôi của lập luận bị vứt sọt rác, gây ra lỗi nghiêm trọng đặc biệt cho Multi-hop dài.

---

## 3. Action Plan (Các Hướng Thử Nghiệm Tác Chiến Cho 15/04)

Dưới đây là 3 hướng thử nghiệm tính từ Dễ đến Khó. Giai đoạn này nên tập trung làm dứt điểm từng Pha để kiểm chứng độ chính xác.

### Pha 1 (Dễ): Data Pruning - Làm Sạch và Thêm Thắt Node 
Thay vì đổ hết file `train_candid_paths.bin` vào Classifier. Viết một Script trung gian làm bước lọc.
1.  **Lọc độ nhiễu (Semantic Pruning):** Đọc nội dung mảng ứng viên, sử dụng thuật toán TF-IDF, BM25, hoặc cấu trúc nhẹ `sentence-transformers` để tính độ tương quan (Cosine Similarity) giữa Top-K Triples trong Subgraph với câu Claim gốc. 
2.  **Bỏ qua "Hub-nodes":** Xóa các đường đi/cạnh đổ vào những khái niệm gốc mang tính phân tán (như 'Country', 'Năm') để tập trung vào logic sâu.
3.  **Khắc phục lỗi Multi-hop:** Việc lược bỏ node rác nhường không gian trong ngưỡng 512 token để đưa tối đa những cạnh có ích vào thay vì bị cắt cụt ngang chừng.

### Pha 2 (Trung bình): Đổi định dạng Graph bằng Verbalization
Mục tiêu: Đập bỏ việc ghép cụm `.join()` bằng `[SEP]`.
1.  **Sửa thuật toán Collator (baseline.py):** Hủy bỏ việc tự động nối tổng thể Graph theo mảng dẹt.
2.  **Tự Nhiên hóa Text (Template-based Verbalization):** Thay vì dạng `Node A [SEP] Rel [SEP] Node B`, ta biến đổi thành câu tiếng Anh lưu loát: `Node A is Rel of Node B.`. Điều này kích hoạt triệt để sức mạnh ngôn ngữ của BERT (vốn được học từ báo chí/sách truyền thống) và làm giảm nhiễu rác Context.

### Pha 3 (Khó, Tính Tiên Phong Học Thuật): Triển khai kiến trúc lai SAT (Structure-Aware Transformer)
Nâng cấp Architecture (Ghi điểm báo cáo cực mạnh): Giúp mô hình cảm nhận được "HÌNH HỌC" của đồ thị qua Sequence dẹt.
1.  **Can thiệp Topology:** Kế thừa / Tùy chỉnh (Override) ma trận `attention_mask` của thư viện `transformers` class `BertModel`.
2.  **Mask Ràng buộc Cạnh:** Thay vì cho "Full Self-Attention", Token $i$ chỉ Attention chéo với Token $j$ NẾU chúng kề nhau trên KG. Kết hợp cộng ma trận "Khoảng cách đường đi" vào tỷ trọng Score, ép AI "dò đường" thay vì đọc lướt một chuỗi ngẫu nhiên.

---

## 4. Tóm Lược Work-flow Cụ Thể Tới 15/4

- [ ] **Bước 1:** Chạy lại `baseline.py` gốc lấy kết quả tham chiếu làm Benchmark chính xác (Validation/Test Loss và Acc).
- [ ] **Bước 2:** View lại ruột của `dev_candid_paths.bin`, bóc dữ liệu ra xem trực tiếp để dễ dàng code hàm Format/Verbalize.
- [ ] **Bước 3:** Cắm logic cấu trúc hóa Verbalizer (Pha 2) vào đoạn `DataCollator` chạy nghiệm thu.
- [ ] **Bước 4:** Xây dựng file Python/Colab mới chứa Mask Đồ Thị SAT áp dụng kỹ thuật Pha 3.