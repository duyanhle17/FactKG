# Giải Thích: Tối Ưu Tổ Hợp & Attention trong GEAR-lite

> Tài liệu này giải thích mối liên hệ giữa **Tối Ưu Tổ Hợp (Combinatorial Optimization)**, **Attention Mechanism** và kiến trúc **GEAR-lite** mà thầy yêu cầu nghiên cứu, áp dụng cho bài toán FactKG.

---

## 1. Tối Ưu Tổ Hợp (Combinatorial Optimization) Là Gì?

### 1.1. Định nghĩa đơn giản

**Tối ưu tổ hợp** = Bài toán **tìm lời giải tốt nhất** từ một **tập hợp hữu hạn nhưng cực kỳ lớn** các lời giải khả thi.

Hai đặc điểm quan trọng:
- **Quyết định rời rạc (discrete):** Mỗi lựa chọn là "chọn" hoặc "không chọn" — không có chọn "một nửa".
- **Bùng nổ tổ hợp (combinatorial explosion):** Khi số phần tử tăng, số cách kết hợp tăng theo cấp số nhân → không thể thử hết (NP-hard).

### 1.2. Ví dụ quen thuộc

| Bài toán | Mô tả | Vì sao là tổ hợp? |
|:---|:---|:---|
| **Người bán hàng (TSP)** | Tìm đường đi ngắn nhất qua N thành phố | N! hoán vị đường đi. Với 20 thành phố = 2.4 × 10¹⁸ cách |
| **Cái túi (Knapsack)** | Chọn vật phẩm tối ưu cho túi có giới hạn | Mỗi vật: chọn/không → 2^N tổ hợp |
| **Chọn tập con (Subset Selection)** | Chọn K phần tử tốt nhất từ N | C(N, K) tổ hợp |

### 1.3. Ví dụ cực kỳ dễ hiểu

> Bạn có **10 cuốn sách** trên kệ nhưng ba lô chỉ chứa được **3 cuốn**. Bạn muốn chọn **3 cuốn hữu ích nhất** cho kỳ thi.
>
> - Số cách chọn: C(10, 3) = **120 tổ hợp**
> - Nếu có 50 cuốn chọn 5: C(50, 5) = **2.118.760 tổ hợp**
> - Nếu có 100 cuốn chọn 5: C(100, 5) = **75.287.520 tổ hợp**
>
> → Không thể đọc thử hết tất cả tổ hợp để biết tổ hợp nào tốt nhất! Cần **thuật toán thông minh**.

---

## 2. Vấn Đề FactKG Chính Là Bài Toán Tối Ưu Tổ Hợp

### 2.1. Chuyện gì xảy ra khi BFS chạy?

Sau khi Relation Predictor lấy Top-5 relations và BFS duyệt 3-hop trên Knowledge Graph, hệ thống sinh ra **rất nhiều đường dẫn (paths)**. Ví dụ:

```
Claim: "Barack Obama was born in Hawaii"

BFS sinh ra (giả sử):
  Path 1: Obama → birthPlace → Honolulu → locatedIn → Hawaii        ← ✅ Đúng!
  Path 2: Obama → nationality → United States → capital → Washington  ← ❌ Rác
  Path 3: Obama → almaMater → Harvard → locatedIn → Massachusetts    ← ❌ Rác
  Path 4: Obama → spouse → Michelle → birthPlace → Chicago           ← ❌ Rác
  Path 5: Obama → birthPlace → Honolulu → population → 350000        ← ❌ Rác
  Path 6: Obama → party → Democratic → foundedIn → 1828              ← ❌ Rác
  ...
  Path 20: Obama → successor → Trump → birthPlace → New York         ← ❌ Rác
```

→ **Chỉ 1-2 paths là bằng chứng thật**, còn lại là "rác" do BFS tổ hợp tạo ra.

### 2.2. Bài toán tối ưu tổ hợp xuất hiện ở đây

```
Cho:      N paths (ví dụ N = 20)
Tìm:      Tập con K paths tốt nhất (K = 3~5)
Mục tiêu: Tối đa hóa xác suất phân loại đúng True/False
```

→ Đây chính xác là bài toán **Subset Selection** — một dạng kinh điển của tối ưu tổ hợp!

### 2.3. Cách hiện tại giải quyết (và tại sao nó tệ)

Hiện tại, `ConcatClassifier` giải quyết bằng cách **không chọn gì cả** — nối hết tất cả paths thành 1 chuỗi:

```
Input BERT = "[CLS] Claim [SEP] Path1 | Path2 | Path3 | ... | Path20 [SEP]"
              ←————————————— có thể tới 2000+ tokens ——————————————→
              ←— BERT chỉ đọc được 512 tokens ——→  | bị cắt bỏ (truncate)!
```

**Hậu quả:**
1. Paths cuối (có thể chứa bằng chứng đúng) bị **cắt mất** do quá 512 token.
2. BERT đọc tất cả paths rác cùng lúc → tín hiệu bị **loãng** (diluted).
3. BERT không có cơ chế để biết path nào quan trọng → đối xử **công bằng với tất cả** (kể cả rác).

→ Kết quả: **Multi-hop chỉ đạt 68.8%** — thấp nhất trong tất cả loại suy luận.

---

## 3. Attention = "Lời Giải Mềm" Cho Bài Toán Tổ Hợp

### 3.1. Hai cách tiếp cận

**Cách 1: Chọn cứng (Hard Selection)** — Tối ưu tổ hợp thuần túy

```python
# Dùng argmax: chọn K paths có điểm cao nhất
scores = [score(claim, path_i) for path_i in all_paths]
selected = argmax(scores, K)  # chọn K paths tốt nhất
```

**Vấn đề:** Hàm `argmax` **không khả vi** (non-differentiable). Gradient = 0 ở hầu hết mọi nơi → **Không thể train bằng backpropagation**. Muốn train phải dùng Reinforcement Learning (rất khó, không ổn định).

**Cách 2: Chọn mềm (Soft Selection)** — Attention

```python
# Dùng softmax: gán trọng số [0, 1] cho MỌI path
scores = [score(claim, path_i) for path_i in all_paths]
weights = softmax(scores)     # trọng số mềm, tổng = 1, khả vi!
result  = sum(weights[i] * embedding[i] for i in range(N))
```

**Ưu điểm:** Hàm `softmax` **khả vi** (differentiable) → Train được bằng gradient descent bình thường!

### 3.2. Hình dung trực quan

```
                    Bài toán: Chọn paths tốt nhất

  ┌─────────────────────────────────────────────────────────────────┐
  │  CHỌN CỨNG (argmax) — Tối ưu tổ hợp                          │
  │                                                                 │
  │  Path 1: ████████████ (0.85)  → ✅ CHỌN                       │
  │  Path 2: ███ (0.20)           → ❌ BỎ                          │
  │  Path 3: █ (0.05)             → ❌ BỎ                          │
  │  Path 4: ████████ (0.62)      → ✅ CHỌN                       │
  │  Path 5: ██ (0.12)            → ❌ BỎ                          │
  │                                                                 │
  │  ⚠️ Không thể train! (argmax không khả vi)                     │
  └─────────────────────────────────────────────────────────────────┘

                        ↓ Nới lỏng (Relaxation) ↓

  ┌─────────────────────────────────────────────────────────────────┐
  │  CHỌN MỀM (softmax) — Attention                               │
  │                                                                 │
  │  Path 1: ████████████ (α = 0.42)  → Đóng góp 42%             │
  │  Path 2: ███ (α = 0.08)           → Đóng góp 8%              │
  │  Path 3: █ (α = 0.02)             → Đóng góp 2% (gần như bỏ) │
  │  Path 4: ████████ (α = 0.38)      → Đóng góp 38%             │
  │  Path 5: ██ (α = 0.10)            → Đóng góp 10%             │
  │                                                                 │
  │  ✅ Train được! (softmax khả vi, gradient chạy bình thường)    │
  └─────────────────────────────────────────────────────────────────┘
```

> **Bản chất:** Thay vì hỏi "chọn path nào?" (discrete, NP-hard), ta hỏi "mỗi path quan trọng bao nhiêu %?" (continuous, trainable). Đây được gọi là **differentiable relaxation** — nới lỏng bài toán rời rạc thành bài toán liên tục.

### 3.3. Bảng so sánh tổng hợp

| Tiêu chí | Chọn cứng (Tối ưu tổ hợp) | Chọn mềm (Attention) |
|:---|:---|:---|
| **Phép toán** | argmax (chọn K từ N) | softmax (gán trọng số cho tất cả N) |
| **Khả vi?** | ❌ Không → Không train được | ✅ Có → Train bằng gradient descent |
| **Kết quả** | Giữ đúng K paths, bỏ hết còn lại | Giữ tất cả, nhưng rác có trọng số ≈ 0 |
| **Rủi ro** | Chọn sai → mất thông tin vĩnh viễn | Thông tin yếu vẫn giữ lại (rất nhỏ) |
| **Độ phức tạp train** | Cần RL hoặc heuristic | Backpropagation chuẩn |

---

## 4. GEAR và GEAR-lite

### 4.1. GEAR gốc (Paper: Zhou et al., ACL 2019)

**Paper:** *"GEAR: Graph-based Evidence Aggregating and Reasoning for Fact Verification"*

GEAR giải quyết đúng bài toán mà chúng ta gặp: làm sao tổng hợp nhiều bằng chứng một cách thông minh?

**Cách làm của GEAR:**

```
Bước 1: BERT encode riêng từng evidence thành vector
         e₁ = BERT("[CLS] Claim [SEP] Evidence_1 [SEP]")
         e₂ = BERT("[CLS] Claim [SEP] Evidence_2 [SEP]")
         ...

Bước 2: Xây đồ thị fully-connected (tất cả evidence nối với nhau)
         e₁ ←→ e₂ ←→ e₃ ←→ e₄ ←→ e₅

Bước 3: Chạy Graph Attention Network (GAT) nhiều vòng
         Mỗi node (evidence) "nói chuyện" với các node khác
         để cập nhật biểu diễn của mình

Bước 4: Dùng Attention Aggregator tổng hợp tất cả node
         → vector cuối cùng → Phân loại: Supported / Refuted / NEI
```

**Điểm mạnh:** Evidence được đánh giá **độc lập** rồi mới tổng hợp → tránh giới hạn 512 token, tránh loãng tín hiệu.

**Điểm yếu:** Graph Attention Network (GAT) **rất nặng** — cần xây đồ thị, chạy message passing nhiều vòng, nhiều tham số.

### 4.2. GEAR-lite: Rút gọn cho FactKG

"Lite" = Giữ lại **tinh thần cốt lõi** của GEAR nhưng **bỏ phần đồ thị nặng nề**:

```
GEAR-lite (2 Tầng):

╔══════════════════════════════════════════════════════════════════╗
║  TẦNG 1: Encode độc lập từng path (giống GEAR)                 ║
║                                                                  ║
║  h₁ = BERT("[CLS] Claim [SEP] Path_1 [SEP]")  → vector 768-d  ║
║  h₂ = BERT("[CLS] Claim [SEP] Path_2 [SEP]")  → vector 768-d  ║
║  h₃ = BERT("[CLS] Claim [SEP] Path_3 [SEP]")  → vector 768-d  ║
║  ...                                                             ║
║  hₙ = BERT("[CLS] Claim [SEP] Path_N [SEP]")  → vector 768-d  ║
║                                                                  ║
║  → Mỗi path được BERT "đọc hiểu" riêng biệt                   ║
║  → KHÔNG bị giới hạn 512 token (vì mỗi lần chỉ đọc 1 path)    ║
╚══════════════════════════════════════════════════════════════════╝
                              ↓
╔══════════════════════════════════════════════════════════════════╗
║  TẦNG 2: Attention Aggregation (giải bài toán tổ hợp)          ║
║                                                                  ║
║  1. Tính điểm cho mỗi path:                                     ║
║     score_i = W · h_i        (W là vector trọng số học được)    ║
║                                                                  ║
║  2. Softmax → trọng số:                                         ║
║     α_i = exp(score_i) / Σ exp(score_j)                         ║
║                                                                  ║
║  3. Tổng hợp có trọng số:                                       ║
║     h_final = α₁·h₁ + α₂·h₂ + ... + αₙ·hₙ                    ║
║                                                                  ║
║  4. Phân loại:                                                   ║
║     ŷ = MLP(h_final) → True / False                             ║
║                                                                  ║
║  → Path quan trọng có α cao → đóng góp nhiều vào quyết định     ║
║  → Path rác có α ≈ 0 → tự động bị "lờ đi"                      ║
╚══════════════════════════════════════════════════════════════════╝
```

### 4.3. So sánh GEAR Full vs GEAR-lite

| | GEAR Full (Paper gốc) | GEAR-lite (Cho FactKG) |
|:---|:---|:---|
| **Encode evidence** | BERT riêng từng cái ✅ | BERT riêng từng cái ✅ |
| **Cấu trúc đồ thị** | Fully-connected graph + GAT nhiều tầng | ❌ Không cần đồ thị |
| **Message Passing** | Có (evidence "nói chuyện" qua đồ thị) | ❌ Không cần |
| **Aggregation** | Graph Attention (phức tạp) | 1 lớp Attention đơn giản |
| **Số tham số** | Rất nhiều | Rất ít |
| **Chi phí train** | Cao | Thấp |
| **Tinh thần giữ lại** | Encode riêng + Attention tổng hợp | Giữ nguyên ✅ |

---

## 5. Tại Sao Cách Này Giải Quyết Được Multi-hop?

### Trước (ConcatClassifier):
```
20 paths × ~50 tokens/path = ~1000 tokens
BERT đọc được 512 → cắt mất ~50% thông tin
BERT không biết path nào quan trọng → đối xử công bằng với rác
→ Multi-hop: 68.8%
```

### Sau (GEAR-lite):
```
Mỗi path được BERT đọc riêng → 0% thông tin bị cắt
Attention tự học: "Path 1 quan trọng 42%, Path 6 chỉ 2%"
→ Path rác tự động bị "triệt tiêu" bằng trọng số thấp
→ Kỳ vọng Multi-hop tăng đáng kể
```

---

## 6. Papers Tham Khảo

1. **GEAR: Graph-based Evidence Aggregating and Reasoning for Fact Verification**
   - Tác giả: Zhou et al. (THUNLP, Tsinghua University)
   - Hội nghị: ACL 2019
   - Link: https://arxiv.org/abs/1908.01843
   - Nội dung: Đề xuất kiến trúc đồ thị fully-connected + GAT để tổng hợp multi-evidence

2. **Attention Is All You Need**
   - Tác giả: Vaswani et al. (Google)
   - Hội nghị: NeurIPS 2017
   - Link: https://arxiv.org/abs/1706.03762
   - Nội dung: Đề xuất Transformer và Multi-Head Attention, nền tảng lý thuyết attention

3. **Pointer Networks**
   - Tác giả: Vinyals et al. (Google Brain)
   - Hội nghị: NeurIPS 2015
   - Link: https://arxiv.org/abs/1506.03134
   - Nội dung: Dùng attention để giải bài toán tổ hợp (TSP), chứng minh attention = soft combinatorial selection

---

## 7. GEAR-lite Ảnh Hưởng Cụ Thể Gì Vào Quá Trình Training?

> Phần này phân tích dựa trên code thật trong `with_evidence/classifier/baseline.py`.

### 7.1. Tổng quan: Cái gì thay đổi, cái gì giữ nguyên?

```
╔═══════════════════════════════════════════════════════════════════╗
║                    KHÔNG THAY ĐỔI                                ║
║  ✅ Data loading (pickle files, candid_paths.bin)                ║
║  ✅ Dataset class (claims, evis, labels, types)                  ║
║  ✅ Training loop (epoch, optimizer, early stopping)             ║
║  ✅ Evaluation logic (dev acc, test acc per type)                ║
║  ✅ BERT model (vẫn dùng bert-base-cased)                       ║
╠═══════════════════════════════════════════════════════════════════╣
║                    THAY ĐỔI                                      ║
║  🔄 DataCollator — cách chuẩn bị input cho BERT                 ║
║  🔄 Model class  — từ ConcatClassifier → GEARLiteClassifier     ║
║  🔄 GPU memory   — tăng lên do BERT chạy N lần/sample           ║
╚═══════════════════════════════════════════════════════════════════╝
```

### 7.2. Thay đổi 1: DataCollator (Cách chuẩn bị input)

**Hiện tại** (`DataCollator.batchfy()`, dòng 144-180):

```python
# HIỆN TẠI: Nối TẤT CẢ paths thành 1 chuỗi duy nhất
seq_evidence = [
    f"{sep_token.join(evi)} {sep_token}"    # Path1 [SEP] Path2 [SEP] ... PathN [SEP]
    for evi in evidence
]
# → Tokenize thành 1 tensor duy nhất, max_length = 512 - len(claim)
# → Nếu tổng paths dài hơn → BỊ CẮT (truncate)!
```

**GEAR-lite** sẽ cần:

```python
# GEAR-LITE: Giữ từng path riêng biệt, KHÔNG nối
# Mỗi sample có N paths → tokenize N lần riêng biệt
for sample in batch:
    for path_i in sample["paths"]:
        tokenize("[CLS] Claim [SEP] Path_i [SEP]")  # mỗi cặp < 512 token
# → Output: tensor 3 chiều [batch_size, N_paths, seq_len]
# → KHÔNG BAO GIỜ bị truncate (vì mỗi cặp claim+path rất ngắn)
```

**Tác động:**
- ✅ **Không mất thông tin** — mỗi path đều được BERT đọc đầy đủ
- ⚠️ **Cần xử lý padding** — các sample có số paths khác nhau (sample A có 5 paths, sample B có 12 paths) → cần padding để tạo batch đều

### 7.3. Thay đổi 2: Model Architecture (Kiến trúc mô hình)

**Hiện tại** (`ConcatClassifier`, dòng 315-348):

```
                    ConcatClassifier
                    ================

Input:  [CLS] Claim [SEP] Path1 [SEP] Path2 [SEP] ... [SEP]
         └──────────────── 1 chuỗi dài ────────────────┘
                              │
                              ▼
                     ┌─────────────┐
                     │   BERT      │  ← Chạy 1 lần / sample
                     │ (1 forward) │
                     └──────┬──────┘
                            │
                     [CLS] vector (768-dim)
                            │
                            ▼
                     ┌─────────────┐
                     │     MLP     │  Linear → ReLU → Linear
                     │  (768→768   │
                     │   →2)       │
                     └──────┬──────┘
                            │
                     logit [True, False]
```

**GEAR-lite:**

```
                    GEARLiteClassifier
                    ==================

Input:  N cặp riêng biệt:
        [CLS] Claim [SEP] Path_1 [SEP]
        [CLS] Claim [SEP] Path_2 [SEP]
        ...
        [CLS] Claim [SEP] Path_N [SEP]
                              │
                              ▼
                     ┌─────────────┐
                     │   BERT      │  ← Chạy N lần / sample
                     │ (N forward) │     (hoặc batch N cặp cùng lúc)
                     └──────┬──────┘
                            │
                   N vectors [CLS] (mỗi cái 768-dim)
                     h₁, h₂, h₃, ..., hₙ
                            │
                            ▼
               ┌─────────────────────────┐
               │   ATTENTION LAYER       │  ← ĐÂY LÀ PHẦN MỚI
               │                         │
               │  score_i = W_attn · h_i │  (tính điểm từng path)
               │  α_i = softmax(scores)  │  (trọng số mềm)
               │  h_agg = Σ(α_i · h_i)  │  (tổng hợp có trọng số)
               └────────────┬────────────┘
                            │
                     h_agg (768-dim)     ← 1 vector tổng hợp
                            │
                            ▼
                     ┌─────────────┐
                     │     MLP     │  (giống cũ: 768→768→2)
                     └──────┬──────┘
                            │
                     logit [True, False]
```

**Tác động vào code:**
- `ConcatClassifier.__init__()`: Thêm `self.attention_weight = nn.Linear(768, 1)` ← **Chỉ 769 tham số mới!**
- `ConcatClassifier.forward()`: Thay vì 1 lần `self.encoder()`, giờ chạy N lần (hoặc reshape batch)

### 7.4. Thay đổi 3: Training Loop (Vòng lặp huấn luyện)

**Hiện tại** (dòng 393-412):

```python
# Training loop HIỆN TẠI — KHÔNG CẦN SỬA gì nhiều
for epoch in range(args.epoch):
    for i, batch in enumerate(train_loader):
        loss, logit = model(batch)     # ← model(batch) bên trong thay đổi
        loss.backward()                # ← attention weights cũng được cập nhật
        optimizer.step()               # ← tự động cập nhật cả W_attn
```

**Điều hay:** Training loop **gần như không đổi**! Vì:
- `loss.backward()` tự động tính gradient cho **tất cả** tham số, bao gồm cả `W_attn` mới.
- `optimizer.step()` tự động cập nhật cả tham số attention.
- PyTorch autograd xử lý hết — ta chỉ cần thay đổi bên trong `model.forward()`.

**Cái duy nhất cần chú ý:**
- ⚠️ `batch_size` có thể cần **giảm** (từ 32 xuống 8-16) do BERT chạy nhiều lần hơn → tốn GPU memory hơn.

### 7.5. Thay đổi 4: GPU Memory & Tốc Độ

Đây là **ảnh hưởng lớn nhất** cần cân nhắc:

| Tiêu chí | ConcatClassifier (hiện tại) | GEARLiteClassifier |
|:---|:---|:---|
| **Số lần BERT forward / sample** | 1 | N (= số paths, ~5-20) |
| **GPU Memory / sample** | ~500 MB | ~500 MB × N |
| **Batch size khả thi** | 32 | 4-8 (nếu N ≈ 10) |
| **Thời gian / epoch** | 1x | ~Nx chậm hơn |
| **Số tham số mới** | 0 | ~769 (rất ít) |

**Chiến lược giảm thiểu chi phí:**

```
Cách 1: Gradient Accumulation
  - Giữ effective batch size = 32
  - Nhưng chia thành 4 mini-batch × 8 samples
  - Accumulate gradient rồi mới optimizer.step()

Cách 2: Shared BERT + Batched Forward
  - Gom tất cả N cặp (claim, path_i) trong 1 sample thành 1 mini-batch
  - Chạy BERT 1 lần cho cả N cặp (thay vì N lần riêng)
  - Tiết kiệm overhead nhưng memory vẫn tương đương

Cách 3: Freeze BERT (nếu cần)
  - Freeze BERT weights, chỉ train Attention + MLP
  - Tốc độ nhanh hơn nhiều nhưng accuracy có thể thấp hơn
```

### 7.6. Tóm tắt ảnh hưởng: So sánh trực quan

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  HIỆN TẠI (ConcatClassifier)                                               ║
║                                                                              ║
║  Data: Claim + "Path1 [SEP] Path2 [SEP] ... PathN"  (1 chuỗi nối dài)     ║
║                          ↓                                                   ║
║  BERT:  1 forward pass (nhanh, ít memory)                                   ║
║                          ↓                                                   ║
║  MLP:   [CLS] → logit                                                      ║
║                                                                              ║
║  ⚡ Nhanh    💾 Ít memory    ❌ Bị truncate    ❌ Không phân biệt path      ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  MỚI (GEARLiteClassifier)                                                   ║
║                                                                              ║
║  Data: N cặp riêng biệt (Claim, Path_i)                                    ║
║                          ↓                                                   ║
║  BERT:  N forward passes (chậm hơn, nhiều memory hơn)                      ║
║                          ↓                                                   ║
║  ATTN:  Softmax → trọng số α_i → tổng hợp h_agg                           ║
║                          ↓                                                   ║
║  MLP:   h_agg → logit                                                      ║
║                                                                              ║
║  🐢 Chậm hơn  💾 Nhiều memory  ✅ Không truncate  ✅ Chọn path thông minh  ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### 7.7. Kết luận: Trade-off chính

> **GEAR-lite đánh đổi TỐC ĐỘ và MEMORY lấy ĐỘ CHÍNH XÁC:**
>
> - **Mất:** Chạy chậm hơn ~N lần, tốn GPU memory hơn ~N lần → cần giảm batch size
> - **Được:** Không bao giờ mất thông tin do truncate + Tự động học path nào quan trọng nhất → kỳ vọng Multi-hop tăng đáng kể
>
> Với hệ thống FactKG có ~5-20 paths/sample, đây là trade-off **hoàn toàn chấp nhận được**, đặc biệt khi Multi-hop đang là bottleneck (68.8%).

---

**Người viết:** Antigravity (AI Assistant)
**Ngày:** 07/05/2026 (cập nhật 08/05/2026)
