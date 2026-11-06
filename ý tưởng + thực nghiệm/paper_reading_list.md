# 📚 Paper Reading List — Tối Ưu Tổ Hợp, Attention & Evidence Aggregation

> Danh sách paper được chia theo **3 hướng nghiên cứu** mà thầy đề cập, sắp xếp theo thứ tự ưu tiên đọc.
> Mỗi paper có tóm tắt ngắn + lý do nên đọc + link truy cập.

---

## Hướng 1: GEAR & Evidence Aggregation (Tổng hợp bằng chứng)
> *Trực tiếp liên quan tới GEAR-lite — ĐỌC TRƯỚC*

### 📖 1.1. [BẮT BUỘC] GEAR: Graph-based Evidence Aggregating and Reasoning for Fact Verification
- **Tác giả:** Zhou, Han, Yang, Liu, Wang, Li, Sun (THUNLP - Tsinghua)
- **Hội nghị:** ACL 2019
- **Link:** https://arxiv.org/abs/1908.01843
- **Code:** https://github.com/thunlp/GEAR
- **Tóm tắt:** Paper gốc mà "GEAR-lite" dựa trên. Đề xuất xây đồ thị fully-connected giữa các evidence, dùng Graph Attention Network (GAT) để tổng hợp thay vì nối chuỗi. Đạt 67.10% FEVER score.
- **Đọc gì:**
  - Section 3 (Model): Hiểu kiến trúc Sentence Encoder → Evidence Graph → Aggregator
  - Section 3.3 (Evidence Aggregating): **Đọc kỹ nhất** — 3 loại aggregator (Attention, Max, Mean)
  - Table 2: So sánh hiệu quả các aggregator
- **Liên quan:** Đây là nền tảng lý thuyết cho GEAR-lite. Ta lấy ý tưởng "encode riêng + attention tổng hợp" nhưng bỏ phần GNN nặng.

### 📖 1.2. [BẮT BUỘC] FactKG: Fact Verification via Reasoning on Knowledge Graphs
- **Tác giả:** Kim et al.
- **Hội nghị:** ACL 2023
- **Link:** https://arxiv.org/abs/2305.06590
- **Tóm tắt:** Paper gốc của dataset FactKG mà bạn đang làm. Định nghĩa 5 loại suy luận (one-hop, multi-hop, conjunction, existence, negation) và baseline ConcatClassifier.
- **Đọc gì:**
  - Section 4 (Baseline Models): Hiểu cách ConcatClassifier hiện tại hoạt động
  - Section 5 (Results): Xem baseline nào yếu nhất (multi-hop) → confirm đúng vấn đề ta đang giải
- **Liên quan:** Phải hiểu rõ hệ thống gốc trước khi sửa.

### 📖 1.3. [NÊN ĐỌC] Fine-grained Fact Verification with Kernel Graph Attention Network
- **Tác giả:** Liu, Xiong, Sun, Liu (THUNLP)
- **Hội nghị:** ACL 2020
- **Link:** https://aclanthology.org/2020.acl-main.655/
- **Tóm tắt:** Cải tiến GEAR bằng Kernel-based Graph Attention. Đo "khoảng cách" giữa evidence theo kernel function thay vì chỉ dùng attention chuẩn. Tinh vi hơn GEAR nhưng cùng tinh thần.
- **Đọc gì:**
  - Section 3 (Kernel Graph Attention): Cách kernel đo mối quan hệ giữa evidence
  - So sánh với GEAR trong bảng kết quả
- **Liên quan:** Nếu GEAR-lite cơ bản chưa đủ mạnh, có thể nâng cấp attention bằng kernel trick.

---

## Hướng 2: Attention = Tối Ưu Tổ Hợp Mềm (Differentiable Relaxation)
> *Hiểu nền tảng lý thuyết tại sao Attention giải quyết được bài toán tổ hợp*

### 📖 2.1. [BẮT BUỘC] Attention Is All You Need
- **Tác giả:** Vaswani et al. (Google)
- **Hội nghị:** NeurIPS 2017
- **Link:** https://arxiv.org/abs/1706.03762
- **Tóm tắt:** Paper nền tảng của cơ chế Attention và Transformer. Đề xuất Multi-Head Attention, Scaled Dot-Product Attention.
- **Đọc gì:**
  - Section 3.2 (Scaled Dot-Product Attention): Công thức Q, K, V → softmax → weighted sum
  - Section 3.2.2 (Multi-Head Attention): Nhiều "góc nhìn" cùng lúc
- **Liên quan:** Hiểu cơ chế attention cơ bản mà GEAR-lite sẽ dùng.

### 📖 2.2. [NÊN ĐỌC] Pointer Networks
- **Tác giả:** Vinyals, Fortunato, Jaitly (Google Brain)
- **Hội nghị:** NeurIPS 2015
- **Link:** https://arxiv.org/abs/1506.03134
- **Tóm tắt:** Paper đầu tiên dùng Attention để giải bài toán tổ hợp (TSP, Convex Hull). Attention "trỏ" (point) vào phần tử input cần chọn → thay thế argmax bằng softmax.
- **Đọc gì:**
  - Section 2 (Ptr-Net): Cách attention thay thế fixed-size output bằng "con trỏ" vào input
  - Section 4 (Experiments): Kết quả trên TSP — chứng minh attention giải được tối ưu tổ hợp
- **Liên quan:** Đây là minh chứng mạnh nhất cho thầy thấy rằng "Attention = giải bài toán tổ hợp". Paper này kết nối trực tiếp 2 khái niệm thầy đề cập.

### 📖 2.3. [THAM KHẢO THÊM] Attention, Learn to Solve Routing Problems!
- **Tác giả:** Kool, van Hoof, Welling (UvA Amsterdam)
- **Hội nghị:** ICLR 2019
- **Link:** https://arxiv.org/abs/1803.08475
- **Code:** https://github.com/wouterkool/attention-learn-to-route
- **Tóm tắt:** Dùng kiến trúc Transformer (Multi-Head Attention) thay cho Pointer Network để giải TSP và VRP. Hiệu quả hơn Pointer Net, chứng minh Transformer-style attention mạnh hơn cho tối ưu tổ hợp.
- **Đọc gì:**
  - Section 3 (Attention Model): Encoder-Decoder Transformer cho bài toán routing
  - Table 1: So sánh với Pointer Network trên TSP
- **Liên quan:** Nếu thầy hỏi sâu về "tối ưu tổ hợp bằng attention", paper này là câu trả lời hiện đại nhất.

---

## Hướng 3: Logistic & Stacking (Tổng hợp dự đoán)
> *Kỹ thuật meta-classifier mà thầy gợi ý*

### 📖 3.1. [NÊN ĐỌC] UNC-NLP at SemEval-2019 Task 7: Rumor Verification (FEVER Shared Task approaches)
- **Hội nghị:** FEVER Shared Task (EMNLP 2018) — nhiều đội dùng Logistic Stacking
- **Link tổng hợp:** https://aclanthology.org/volumes/W18-55/
- **Tóm tắt:** Trong giải đấu FEVER, nhiều đội top sử dụng kỹ thuật **Stacking Ensemble**: dùng BERT/Neural model làm tầng 1 (scoring), rồi dùng Logistic Regression làm tầng 2 (aggregation). Đơn giản nhưng hiệu quả bất ngờ.
- **Đọc gì:** Đọc các system description papers trong FEVER Shared Task proceedings
- **Liên quan:** Đây là cách thực tế nhất nếu ta muốn thay attention bằng Logistic Regression ở tầng 2.

### 📖 3.2. [THAM KHẢO] Stacked Generalization (Wolpert, 1992)
- **Link:** https://doi.org/10.1016/S0893-6080(05)80023-1
- **Tóm tắt:** Paper gốc đề xuất kỹ thuật "Stacking" — dùng meta-learner (ví dụ: Logistic Regression) để kết hợp dự đoán của nhiều base learners. Đây là nền tảng lý thuyết cho phương pháp "logistic thuật toán" mà thầy nói.
- **Đọc gì:** Section 2 — ý tưởng chính về stacked generalization
- **Liên quan:** Nếu thầy hỏi "logistic" ở đây dùng như thế nào, đây là lý thuyết gốc.

---

## 🗺️ Lộ Trình Đọc Đề Xuất

```
Tuần 1 (Ưu tiên cao — đọc ngay):
  ├── 📖 1.1. GEAR (ACL 2019)         ← Hiểu evidence aggregation = tối ưu tổ hợp
  ├── 📖 1.2. FactKG (ACL 2023)       ← Hiểu hệ thống gốc ta đang cải tiến
  └── 📖 2.1. Attention Is All You Need ← Hiểu công thức attention cơ bản

Tuần 2 (Quan trọng — đọc để trình bày với thầy):
  ├── 📖 2.2. Pointer Networks (2015)  ← Attention giải tối ưu tổ hợp (TSP)
  └── 📖 1.3. Kernel GAT (ACL 2020)   ← Cải tiến GEAR

Khi cần (Tham khảo thêm):
  ├── 📖 2.3. Attention Learn to Route  ← Transformer cho tối ưu tổ hợp
  ├── 📖 3.1. FEVER Shared Task         ← Logistic stacking thực tế
  └── 📖 3.2. Stacked Generalization    ← Lý thuyết gốc stacking
```

---

## 💡 Gợi Ý Khi Trình Bày Với Thầy

Khi thầy hỏi "tối ưu tổ hợp liên quan gì tới attention", bạn có thể nói:

> "Bài toán chọn K paths tốt nhất từ N paths là bài toán tối ưu tổ hợp (Subset Selection). Giải trực tiếp bằng argmax thì không train được. **Pointer Networks (Vinyals, 2015)** đã chứng minh rằng Attention (softmax) chính là phiên bản nới lỏng vi phân (differentiable relaxation) của argmax, cho phép giải bài toán tổ hợp bằng gradient descent. **GEAR (Zhou, 2019)** áp dụng ý tưởng này cho fact verification: encode riêng từng evidence rồi dùng attention tổng hợp. Em đề xuất GEAR-lite — giữ nguyên tinh thần nhưng bỏ GNN nặng, chỉ dùng 1 lớp attention đơn giản."

---

**Ngày tạo:** 08/05/2026
