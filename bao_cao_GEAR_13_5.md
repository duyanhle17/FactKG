# Báo Cáo: Phân Tích Paper GEAR & Kế Hoạch Áp Dụng Cho FactKG

**Ngày báo cáo:** 13/05/2026  
**Người thực hiện:** Lê Duy Anh  
**Paper tham chiếu:** GEAR: Graph-based Evidence Aggregating and Reasoning for Fact Verification (ACL 2019)

---

## 1. Tổng Quan Paper GEAR

### 1.1. Thông Tin Cơ Bản

| Mục | Nội dung |
|:---|:---|
| **Tên đầy đủ** | GEAR: Graph-based Evidence Aggregating and Reasoning for Fact Verification |
| **Tác giả** | Zhou, Han, Yang, Liu, Wang, Li, Sun (THUNLP – Tsinghua University) |
| **Hội nghị** | ACL 2019 |
| **Bài toán** | Fact Verification trên dataset FEVER |
| **Kết quả đạt được** | 74.84% Label Accuracy (dev), 71.60% LA (test), 67.10% FEVER Score (test) |

### 1.2. Bài Toán Mà GEAR Giải Quyết

GEAR giải bài toán **xác minh sự thật (Fact Verification)**: Cho một câu khẳng định (Claim) và một tập bằng chứng (Evidence), hệ thống phải phân loại câu khẳng định đó là **Support** (đúng), **Refute** (sai), hay **Not Enough Info** (thiếu thông tin).

**Thách thức cốt lõi:** Khi có **nhiều bằng chứng** (multi-evidence), mô hình cần tổng hợp thông tin từ tất cả các bằng chứng một cách thông minh, thay vì chỉ nối chuỗi tất cả lại với nhau.

---

## 2. Kiến Trúc GEAR — Chi Tiết 3 Tầng

GEAR đề xuất pipeline 3 bước: *Document Retrieval → Sentence Selection → **Claim Verification (GEAR)***. Phần cốt lõi GEAR gồm 3 tầng:

### Tầng 1: Sentence Encoder (BERT) — Mã hóa độc lập

```
Công thức (Eq. 1):
  eᵢ = BERT(evidenceᵢ, claim)   ← encode riêng TỪNG CẶP (evidence_i, claim)
  c  = BERT(claim)               ← encode claim riêng

Đầu ra: N vectors eᵢ ∈ R^768 (lấy [CLS] token từ BERT)
```

> **Điểm then chốt:** Paper nói rõ (Section 3.2): BERT encode **từng cặp** (evidence, claim) **RIÊNG BIỆT**, không nối hết tất cả evidence thành 1 chuỗi dài. Điều này đảm bảo mỗi bằng chứng được "đọc kỹ" cùng với claim, không bị lẫn lộn hay bị cắt ngắn.

### Tầng 2: Evidence Reasoning Network (ERNet) — Suy luận bằng đồ thị

```
Xây đồ thị fully-connected giữa N evidence nodes (có self-loop).
Chạy T layers message passing:

  Eq. 2: pᵢⱼ = W₁(ReLU(W₀(hᵢ ∥ hⱼ)))    ← attention coefficient giữa 2 evidence
  Eq. 3: αᵢⱼ = softmax_j(pᵢⱼ)              ← chuẩn hóa trọng số
  Eq. 4: hᵢᵗ = Σⱼ αᵢⱼ · hⱼᵗ⁻¹              ← tổng hợp thông tin từ neighbors
```

**Kết quả thực nghiệm từ paper (Table 5, 6):**
- 0 layer ERNet (không dùng graph): 66.17%
- 2 layers ERNet: **67.44%** (best) → Cải thiện **+1.27%** so với 0 layer
- 3 layers ERNet: 66.53% → Giảm → Quá nhiều layer gây over-smoothing

> **Nhận xét quan trọng:** ERNet (Graph Reasoning) chỉ cải thiện ~1.27%. Phần lớn hiệu quả đến từ **cách encode riêng + aggregator** ở Tầng 1 và Tầng 3.

### Tầng 3: Evidence Aggregator — Tổng hợp bằng chứng

Paper thử nghiệm 3 phương pháp tổng hợp:

| Phương pháp | Mô tả | Accuracy (0 layer) | Accuracy (2 layers) |
|:---|:---|:---:|:---:|
| **Attention** | Dùng claim để guide trọng số cho từng evidence | 66.17% | 67.44% |
| **Max** | Lấy giá trị max element-wise | 65.36% | 67.24% |
| **Mean** | Lấy trung bình element-wise | 65.03% | 67.56% |

```
Attention Aggregator (Eq. 5) — Phương pháp chính:
  score_j = W₁'(ReLU(W₀'(claim ∥ evidence_j)))   ← claim "hướng dẫn" attention
  α_j     = softmax(scores)                        ← trọng số mềm cho mỗi evidence
  output  = Σ α_j · evidence_j                     ← tổng hợp có trọng số
```

> **Bài học:** Khi **không dùng graph** (0 layer ERNet), **Attention Aggregator là tốt nhất** (66.17%). Đây là nền tảng cho ý tưởng GEAR-lite mà chúng tôi đề xuất.

### So Sánh Với Baselines Trong Paper

| Mô hình | Dev LA | Test LA | Test FEVER |
|:---|:---:|:---:|:---:|
| BERT-Concat (nối hết evidence) | 73.67% | 71.01% | 65.64% |
| BERT-Pair (encode riêng, lấy top-1) | 73.30% | 69.75% | 65.18% |
| **GEAR (Attention + 2-layer ERNet)** | **74.84%** | **71.60%** | **67.10%** |

→ GEAR tốt hơn BERT-Concat **+1.17%** trên dev, chứng minh rằng **encode riêng + attention tổng hợp tốt hơn nối chuỗi**.

---

## 3. Tại Sao GEAR Liên Quan Đến FactKG?

### 3.1. Điểm tương đồng giữa FEVER (GEAR) và FactKG

| Yếu tố | GEAR (FEVER) | FactKG |
|:---|:---|:---|
| **Bài toán** | Xác minh sự thật (Fact Verification) | Xác minh sự thật trên Knowledge Graph |
| **Input** | Claim + nhiều evidence sentences | Claim + nhiều evidence paths từ KG |
| **Output** | Support / Refute / NEI | True / False |
| **Thách thức chung** | Tổng hợp nhiều bằng chứng để đưa ra 1 quyết định | Tổng hợp nhiều đường dẫn KG để đưa ra 1 quyết định |

### 3.2. Điểm nghẽn hiện tại của FactKG — Giống hệt BERT-Concat

Kiến trúc `ConcatClassifier` hiện tại của FactKG **chính xác là BERT-Concat** — cách mà paper GEAR đã chứng minh là yếu hơn:

```python
# baseline.py hiện tại: Nối TẤT CẢ paths thành 1 chuỗi → đưa vào BERT 1 lần
flat_evi = list(chain(*self.evis[i][0])) + list(chain(*self.evis[i][1]))
cated_inputs = torch.cat([inputs["claim"], inputs["evidence"]], dim=-1)
```

**3 vấn đề cụ thể do cách nối chuỗi gây ra:**

| # | Vấn đề | Mô tả | Ảnh hưởng |
|:---|:---|:---|:---|
| 1 | **Truncation (Cắt ngắn)** | Nối 20-50+ paths > 512 tokens → BERT cắt mất evidence phía sau | Path vàng nằm phía sau sẽ **vĩnh viễn không được BERT thấy** |
| 2 | **Dilution (Pha loãng)** | BERT đọc cả path rác lẫn path đúng cùng lúc | Tín hiệu từ path đúng bị "chìm" giữa hàng chục path rác |
| 3 | **No Discrimination** | BERT không biết path nào quan trọng hơn | Không có cơ chế phân biệt, mọi path được đối xử ngang nhau |

### 3.3. Kết Quả Hiện Tại Của FactKG (Lượt chạy tốt nhất)

| Loại suy luận | Accuracy | Nhận xét |
|:---|:---:|:---|
| Existence | 89.08% | ✅ Tốt |
| Conjunction | 85.08% | ✅ Khá |
| Negation | 84.35% | ✅ Khá |
| One-hop | 84.22% | ✅ Khá |
| **Multi-hop** | **68.84%** | ❌ **Yếu nhất — Điểm nghẽn chính** |
| **Tổng thể** | **81.80%** | — |

> **Multi-hop (68.84%) là loại câu hỏi yếu nhất** vì nó cần nhiều paths nhất → nối chuỗi dài nhất → truncation + dilution nghiêm trọng nhất.

---

## 4. Đề Xuất: Áp Dụng GEAR-lite Vào FactKG

### 4.1. GEAR-lite Là Gì?

**GEAR-lite = GEAR bỏ ERNet (0 layer Graph)**, chỉ giữ 2 thành phần hiệu quả nhất:

- **Tầng 1:** Independent Path Encoding (encode riêng từng cặp claim + path)
- **Tầng 2:** Attention Aggregator (tổng hợp có trọng số dựa trên claim)
- ~~Tầng ERNet~~ → Bỏ (chỉ cải thiện ~1.27% nhưng rất phức tạp)

**Lý do bỏ ERNet:** Dữ liệu GEAR paper cho thấy ERNet chỉ cải thiện 1.27%, trong khi phần lớn hiệu quả (~90%) đến từ cách encode riêng + attention aggregator. Bỏ ERNet giúp đơn giản hóa đáng kể mà gần như không mất hiệu quả.

### 4.2. Quy Trình Hoạt Động Của GEAR-lite Trên FactKG

```
INPUT: Claim = "Barack Obama was born in Hawaii"
       Paths = [path_1, path_2, ..., path_N] (từ KG)

═══════════════════════════════════════════════════════════════
BƯỚC 1: Encode Riêng Từng Cặp (Claim, Path)
═══════════════════════════════════════════════════════════════
  BERT("[CLS] Obama was born in Hawaii [SEP] Obama→birthPlace→Honolulu→locatedIn→Hawaii")  → h₁ (768-d)
  BERT("[CLS] Obama was born in Hawaii [SEP] Obama→nationality→US→capital→Washington")      → h₂ (768-d)
  BERT("[CLS] Obama was born in Hawaii [SEP] Obama→almaMater→Harvard→locatedIn→Mass")       → h₃ (768-d)
  ...
  BERT("[CLS] Obama was born in Hawaii")                                                     → c  (768-d)

  → Mỗi path được BERT đọc KỸ cùng claim, KHÔNG bị cắt ngắn.

═══════════════════════════════════════════════════════════════
BƯỚC 2: Attention Aggregator (Claim Hướng Dẫn)
═══════════════════════════════════════════════════════════════
  Tính điểm cho mỗi path dựa trên claim:
    score_j = W₁(ReLU(W₀(c ∥ hⱼ)))     ← claim "chỉ đạo" chú ý vào path nào
    α_j     = softmax(scores)            ← chuẩn hóa thành trọng số

  Ví dụ kết quả:
    Path 1 (Obama→birthPlace→Honolulu→Hawaii):    α₁ = 0.72  ✅ Liên quan!
    Path 2 (Obama→nationality→US→Washington):     α₂ = 0.05  ❌ Không liên quan
    Path 3 (Obama→almaMater→Harvard→Mass):         α₃ = 0.03  ❌ Không liên quan
    ...

  Tổng hợp:  o = Σ αⱼ · hⱼ = 0.72·h₁ + 0.05·h₂ + 0.03·h₃ + ...
  → Vector 'o' chứa 72% thông tin từ path vàng, path rác gần như bị lờ đi.

═══════════════════════════════════════════════════════════════
BƯỚC 3: Phân Loại Cuối Cùng
═══════════════════════════════════════════════════════════════
  logit = MLP(o)  →  True / False
```

### 4.3. GEAR-lite Giải Quyết Được 3 Vấn Đề Cụ Thể Gì Cho FactKG?

| # | Vấn đề (ConcatClassifier) | GEAR-lite giải quyết |
|:---|:---|:---|
| 1 | **Truncation** — Nối 50+ paths > 512 tokens → BERT cắt mất | Encode **riêng** từng (claim, path) → mỗi cặp < 256 tokens → **không bao giờ bị cắt** |
| 2 | **Dilution** — Path rác làm loãng tín hiệu path đúng | Attention gán trọng số α ≈ 0 cho path rác → **tự động bị lờ đi** |
| 3 | **No Discrimination** — Không phân biệt path quan trọng/không | Claim-guided attention → trọng số phụ thuộc nội dung claim → **chọn path phù hợp nhất** |

---

## 5. Mục Tiêu Cụ Thể (Aiming)

### 5.1. Mục Tiêu Accuracy

| Chỉ số | Hiện tại (ConcatClassifier) | Mục tiêu (GEAR-lite) | Cơ sở dự đoán |
|:---|:---:|:---:|:---|
| **Multi-hop** | 68.84% | **≥ 72%** (+3-5%) | GEAR cải thiện BERT-Concat +1.17% trên FEVER. FactKG có nhiều path rác hơn → attention filtering hiệu quả hơn |
| **Tổng thể** | 81.80% | **≥ 83%** (+1-3%) | Cải thiện multi-hop sẽ kéo tổng lên |

### 5.2. Mục Tiêu Phụ: Explainability (Khả Năng Giải Thích)

Trọng số attention αⱼ cho biết **path nào đóng góp nhiều nhất** vào quyết định. Có thể trích xuất và trình bày:

```
Claim: "Obama was born in Hawaii" → Dự đoán: TRUE
  Path 1: Obama → birthPlace → Honolulu → locatedIn → Hawaii    α = 0.72 ← Bằng chứng chính
  Path 2: Obama → nationality → US → capital → Washington       α = 0.05
  Path 3: Obama → almaMater → Harvard → locatedIn → Mass.       α = 0.03
```

→ Mô hình không chỉ đưa ra đáp án đúng/sai mà còn **giải thích được** tại sao nó chọn đáp án đó.

### 5.3. Lộ Trình Thực Hiện

```
Giai đoạn 1 (Ngắn hạn): Implement GEAR-lite
  ├── Sửa Dataset: Giữ paths riêng biệt (không flatten)
  ├── Sửa DataCollator: Tokenize từng cặp (claim, path) riêng
  ├── Thêm Model: GEARLiteClassifier (BERT shared + Attention Aggregator + MLP)
  └── Chạy thực nghiệm: So sánh với ConcatClassifier trên cùng data split

Giai đoạn 2 (Ablation Study): Phân tích kết quả
  ├── So sánh 3 loại Aggregator: Attention vs Max vs Mean
  ├── Kiểm tra attention weights trên các mẫu multi-hop
  └── Đánh giá accuracy theo 5 loại reasoning type
```

---

## 6. Tóm Tắt Đóng Góp Kỳ Vọng

| Đóng góp | Mô tả |
|:---|:---|
| **Khắc phục Truncation** | Giải quyết triệt để giới hạn 512 token — mỗi path được BERT đọc đầy đủ |
| **Lọc path rác tự động** | Attention Aggregator tự học cách gán trọng số thấp cho path không liên quan |
| **Tăng Multi-hop accuracy** | Kỳ vọng tăng từ 68.84% lên ≥ 72% |
| **Explainability** | Trích xuất attention weights để giải thích quyết định của mô hình |
| **Kiến trúc đơn giản** | Bỏ ERNet (Graph Reasoning) phức tạp, chỉ dùng Attention — dễ implement và debug |

---

**Kết luận:** Paper GEAR cung cấp bằng chứng thực nghiệm rõ ràng rằng encode riêng + attention tổng hợp tốt hơn nối chuỗi (BERT-Concat). FactKG đang sử dụng đúng kiến trúc BERT-Concat mà GEAR đã chỉ ra là yếu. Áp dụng GEAR-lite (bỏ Graph, giữ Encode riêng + Attention) là bước cải tiến hợp lý, có cơ sở lý thuyết vững chắc từ paper, và nhắm trực tiếp vào điểm yếu lớn nhất hiện tại: Multi-hop reasoning.
