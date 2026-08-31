# Đề Xuất Cải Tiến Cân Bằng Multi-hop và Negation (FactKG)

> **Tài liệu phân tích chuyên sâu & Kế hoạch thực nghiệm tiếp theo**  
> **Tác giả:** Nghiên cứu & Tối ưu FactKG (Faico-Lite x GEAR-Lite)  
> **Ngày lập:** 23/08/2026

---

## 1. Bối Cảnh & Vấn Đề Hiện Tại

Trong các thử nghiệm gần đây trên benchmark **FactKG**:
* **Baseline Concat (E0, top-5):** Overall Accuracy đạt `81.80%`, nhưng Multi-hop rất thấp (`68.84%`).
* **GEAR-Lite E2b (Pair Encoder + Attention, top-5):** Cải thiện Overall lên `83.69%`, Multi-hop lên `71.18%`, Negation đạt đỉnh `87.98%`.
* **Faico-Lite R3 + E2 (Retrieval nới lỏng $k=2, 1..H$, top-5):** Đưa Multi-hop tăng vọt lên **`78.60%`** (+7.42% so với E2b), nhưng Negation lại bị kéo tụt xuống **`80.14%`** (−7.84%), dẫn đến Overall Accuracy `84.60%` (tăng +0.91% so với E2b).

### Bảng đối chiếu các lượt chạy

| Cấu hình | Overall Acc | Multi-hop Acc | Negation Acc | One-hop Acc | Conjunction Acc | Existence Acc |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **E0 (Concat)** | 81.80% | 68.84% | 84.35% | 84.22% | 85.08% | 89.08% |
| **E2b (GEAR-Lite)** | 83.69% | 71.18% | **87.98%** | **91.12%** | 82.82% | 94.37% |
| **R3 (FaicoLite + E2)** | **84.60%** | **78.60%** | 80.14% | 90.80% | 83.51% | **94.48%** |

> **Vấn đề then chốt:** Tăng Multi-hop nhưng làm giảm Negation là một dạng **zero-sum trade-off**. Để tạo ra một bước nhảy vọt thực sự về Overall Accuracy và đạt chuẩn công bố/báo cáo, hệ thống cần đưa candidate path vào **vừa đủ và đúng**, đồng thời nâng cấp cơ chế suy luận để phục hồi Negation.

---

## 2. So Sánh Chi Tiết: Attention Hiện Tại vs GEAR Gốc

### 2.1. Code Attention hiện tại trong repo (`baseline.py`)

Hiện tại, lớp `GEARLiteClassifier` sử dụng cơ chế chấm điểm path độc lập:

```python
# baseline.py (GEAR-Lite v1)
self.path_attention = nn.Sequential(
    nn.Linear(self.config.hidden_size, 64),   # 768 -> 64
    nn.ReLU(),
    nn.Linear(64, 1),                          # 64 -> 1
)

# Trong hàm forward:
# path_vectors: [B, K, 768] (với K là số path tối đa, vd: 32)
attention_scores = self.path_attention(path_vectors).squeeze(-1)  # [B, K]
attention_weights = torch.softmax(attention_scores, dim=1)        # [B, K]
pooled_evidence = torch.sum(path_vectors * attention_weights.unsqueeze(-1), dim=1) # [B, 768]
```

* **Đặc điểm:** Trọng số `attention_scores` của từng path chỉ được tính từ vector embedding của chính cặp đó (`h_i`).
* **Lập luận ban đầu trong code:** Vì `h_i = BERT([CLS] Claim [SEP] Path_i [SEP])` nên đã có cross-attention giữa Claim và Path bên trong BERT.

### 2.2. Cơ chế Attention trong paper GEAR gốc (ACL 2019)

Trong paper GEAR gốc, sau khi có vector biểu diễn node evidence $h_j$ và vector câu hỏi $c$:

$$\begin{aligned}
p_j &= W_1 \cdot \text{ReLU}(W_0 \cdot [c \,\|\, h_j]) \\
\alpha_j &= \frac{\exp(p_j)}{\sum_k \exp(p_k)} \\
o &= \sum_j \alpha_j h_j
\end{aligned}$$

* **Đặc điểm:** GEAR gốc chủ động **nối trực tiếp vector câu hỏi $c$ với vector bằng chứng $h_j$** trước khi đi qua mạng MLP tính trọng số $\alpha_j$.

### 2.3. Tại sao "cross-attention bên trong BERT" là chưa đủ?

1. **Thông tin bị nén và phân tán:** BERT nén cả Claim và Path vào một vector `[CLS]` 768 chiều. Khi có 32 candidate paths, mỗi vector $h_i$ lại mang một góc nhìn Claim bị biến dạng nhẹ theo ngữ cảnh của $Path_i$.
2. **Thiếu một "ngọn hải đăng" dẫn đường khi so sánh giữa các path:** Khi thực hiện phép gộp Softmax giữa 32 paths, model cần một biểu diễn gốc, bất biến của Claim ($c$) để trả lời câu hỏi: *"Trong 32 path này, path nào thực sự trả lời đúng trọng tâm câu hỏi của Claim?"*.
3. **Ảnh hưởng chí mạng tới Negation:**
   * Claim: *"Obama was **not** born in Honolulu."* (Negation, nhãn **False** vì thực tế sinh ở Honolulu).
   * Path 1: `Obama -> birthPlace -> Honolulu` (Evidence mâu thuẫn).
   * Path 2..32: Các path lan man như `Obama -> spouse -> Michelle`, `Obama -> office -> President`...
   * **Nếu không có Claim vector dẫn đường:** Model thấy cả 32 path đều chứa thực thể `Obama`, Attention bị chia đều (diluted). Khi cộng tổng các vector lại, tín hiệu khẳng định `birthPlace` bị loãng giữa biển facts phụ, dẫn đến phân loại sai.

---

## 3. Ba Nguyên Nhân Khiến Negation Bị Giảm Khi Multi-hop Tăng

1. **Hiệu ứng bùng nổ Candidate (Candidate Explosion & Distraction):**
   * Ở E2b (retrieval cũ), số lượng path sinh ra rất ít và thưa (thường chỉ 1-3 path). Ít path thì BERT rất dễ nhận diện đúng facts mâu thuẫn.
   * Ở Faico-Lite (R1/R2/R3), DFS duyệt vét cạn tất cả tails, sinh tối đa **32 paths**. Với câu Negation (thường là sự thật đơn bước), 32 path mang lại quá nhiều facts rác, gây "ảo giác" (hallucination) cho bộ phân loại.
2. **Đặc thù bất đối xứng của KG đối với Negation:**
   * Knowledge Graph chỉ lưu các tri thức khẳng định (positive triples: `A -> rel -> B`).
   * Để chứng minh câu phủ định là **True** (ví dụ: *"A không kết hôn với B"*), KG thường **không có** đường đi nối A với B. Khi R3 cố sinh ra 32 paths đi vòng vèo giữa A và các thực thể khác, model bị đánh lừa rằng *"có evidence liên quan $\rightarrow$ chọn True"*, gây sai lệch phân phối.
3. **Confounding do Checkpoint Mismatch (R3 test trên model R1):**
   * R2 và R3 chỉ thay đổi tập candidate test, nhưng chạy trên checkpoint E2 được train bằng candidate R1 ($k=1$).
   * Model được train với phân phối ít path, khi test lại gặp phân phối 32 path lặp ($k=2$) nên tầng Attention chưa bao giờ học cách lọc nhiễu ở mức độ này.

---

## 4. Bốn Hướng Giải Pháp Để Cả Multi-hop và Negation Cùng Tăng

```
                        ┌────────────────────────────────────────────────────────┐
                        │   MỤC TIÊU: Cân bằng Multi-hop & Phục hồi Negation    │
                        └──────────────────────────┬─────────────────────────────┘
                                                   │
         ┌────────────────────────┬────────────────┴───────────────┬────────────────────────┐
         │                        │                                │                        │
         ▼                        ▼                                ▼                        ▼
   [HƯỚNG A]                [HƯỚNG B]                        [HƯỚNG C]                [HƯỚNG D]
Claim-Conditioned      Train End-to-End R3              Adaptive Max-Paths        Null Evidence Signal
   Attention          (Đồng bộ Train/Dev/Test)         (Lọc động theo Hop)       (Token [NO_EVIDENCE])
```

---

### Hướng A: Claim-Conditioned Attention (Ưu tiên cao nhất - Làm ngay)

**Ý tưởng:** Nâng cấp lớp Attention trong `GEARLiteClassifier` theo đúng công thức của GEAR gốc.

#### Code thiết kế đề xuất:

```python
class GEARLiteV2Classifier(IndependentPathClassifierBase):
    def __init__(self):
        super().__init__()
        # Input kích thước 768 * 2 = 1536 (nối Claim vector + Path vector)
        self.path_attention = nn.Sequential(
            nn.Linear(self.config.hidden_size * 2, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )

    def forward(self, inputs):
        # path_vectors: [B, K, 768]
        path_vectors = self.encode_pairs(inputs)
        path_mask = inputs["path_mask"].bool() # [B, K]

        # Trích xuất biểu diễn Claim vector (c)
        # Cách 1: Lấy mean của các path_vectors có trọng số mask (tận dụng representation đã encode)
        mask_expanded = inputs["path_mask"].to(path_vectors.dtype).unsqueeze(-1)
        claim_vector = (path_vectors * mask_expanded).sum(dim=1) / mask_expanded.sum(dim=1).clamp_min(1.0) # [B, 768]
        
        # Mở rộng Claim vector ra K paths: [B, K, 768]
        claim_expanded = claim_vector.unsqueeze(1).expand(-1, path_vectors.size(1), -1)

        # Nối [claim || path]: [B, K, 1536]
        conditioned_input = torch.cat([claim_expanded, path_vectors], dim=-1)

        # Tính attention score có điều kiện theo Claim
        attention_scores = self.path_attention(conditioned_input).squeeze(-1) # [B, K]
        attention_scores = attention_scores.masked_fill(~path_mask, torch.finfo(attention_scores.dtype).min)
        attention_weights = torch.softmax(attention_scores, dim=1)

        # Renormalize & Pool
        attention_weights = attention_weights * path_mask.to(attention_weights.dtype)
        attention_weights = attention_weights / attention_weights.sum(dim=1, keepdim=True).clamp_min(1e-9)

        pooled_evidence = torch.sum(path_vectors * attention_weights.unsqueeze(-1), dim=1)
        return self.classify(pooled_evidence, inputs["label"])
```

* **Lợi ích cho Negation:** Khi Claim chứa từ phủ định (`"not"`, `"never"`), vector $c$ sẽ hướng Attention chỉ tập trung vào các path chứa đúng vị từ (relation) được hỏi, triệt tiêu trọng số của các path rác còn lại.
* **Lợi ích cho Multi-hop:** Hướng Attention vào chuỗi quan hệ nối đúng các thực thể được nhắc đến trong Claim.

---

### Hướng B: Train End-to-End E2 với Candidate R3 (Bắt buộc về mặt thực nghiệm)

* **Vấn đề:** Không thể kết luận hiệu quả cuối cùng nếu chỉ dùng ablation test.
* **Quy trình chuẩn:**
  1. Sinh `train_candid_r3.bin`, `dev_candid_r3.bin`, `test_candid_r3.bin` theo cùng quy tắc ($k=2$, $1..H$).
  2. Huấn luyện lại model E2 (hoặc E2-V2 có Claim-Conditioned Attention) từ đầu trên tập train R3.
  3. Chọn checkpoint tốt nhất dựa trên Dev set R3.
  4. Đánh giá một lần duy nhất trên Test set R3.

---

### Hướng C: Adaptive Candidate Filtering (Lọc ứng biến theo độ sâu)

* **Vấn đề:** Áp dụng cố định $K=32$ cho mọi loại claim là không tối ưu. Câu đơn bước/phủ định chỉ cần 4–8 paths, trong khi câu đa bước cần 32 paths.
* **Giải pháp:** Sử dụng đầu ra của `Hop Predictor` để cắt tỉa candidate động ngay trước khi đưa vào classifier:

```python
# Điều chỉnh max_paths linh hoạt:
if predicted_hop == 1:
    k_limit = 8    # Giảm nhiễu tối đa cho One-hop và Negation
elif predicted_hop == 2:
    k_limit = 16
else:
    k_limit = 32   # Đảm bảo Recall tối đa cho Multi-hop
```

---

### Hướng D: Tín Hiệu Null-Evidence Token cho Negation

* **Vấn đề:** Khi một claim phủ định là **True** (sự thật không tồn tại trong KG), retriever không tìm thấy connected path nào. Hiện tại hệ thống đệm bằng các path walkable vô nghĩa hoặc vector padding.
* **Giải pháp:** Khi `connected_paths` rỗng, chủ động chèn một path giả lập `[NO_EVIDENCE_FOUND]`. Tầng Pair BERT sẽ encode `[CLS] Claim [SEP] [NO_EVIDENCE_FOUND] [SEP]`. Khi gặp cặp này, model sẽ dễ dàng học được mẫu hình logic: *Claim phủ định + Không có bằng chứng trong KG $\rightarrow$ Dự đoán TRUE*.

---

## 5. Lộ Trình Thực Nghiệm Khuyến Nghị (Action Plan)

| Giai đoạn | Nhiệm vụ kỹ thuật | Thời gian dự kiến | Mục tiêu đầu ra |
|---|---|:---:|---|
| **Pha 1** | Cập nhật `GEARLiteClassifier` sang **Claim-Conditioned Attention** (Hướng A). | 0.5 ngày | Hoàn thiện code model mới trong `baseline.py`. |
| **Pha 2** | Sinh trọn bộ candidate R3 (Train, Dev, Test) và chạy **Train End-to-End** (Hướng B). | 1 - 2 ngày | Kiểm chứng xem Negation có phục hồi khi model được học phân phối R3 hay không. |
| **Pha 3** | Tích hợp **Adaptive Filtering** (Hướng C) theo hop prediction. | 1 ngày | Triệt tiêu triệt để nhiễu ở các câu 1-hop / Negation. |
| **Pha 4** | Phân tích lỗi (Error Analysis) theo từng Reasoning Type & chuẩn bị báo cáo. | 0.5 ngày | Bảng kết quả hoàn chỉnh phục vụ báo cáo Mentor. |

---

## 6. Đề Xuất Trao Đổi Với Mentor

Khi làm việc với Mentor, bạn có thể tóm tắt và xin ý kiến theo 3 luận điểm trọng tâm sau:

1. **Về kết quả R3 hiện tại:**
   > *"Em đã xác định được nguyên nhân cốt lõi khiến Multi-hop tăng mạnh (+7.42%) nhưng Overall tăng không nhiều: do tập candidate R3 mở rộng (32 paths) làm loãng tín hiệu của nhóm Negation (-7.84%). Ngoài ra, kết quả R3 hiện tại chỉ là retrieval ablation (dùng checkpoint train trên R1). Em đề xuất bước tiếp theo là train end-to-end trên toàn bộ candidate R3."*

2. **Về cải tiến kiến trúc Attention:**
   > *"Code Attention hiện tại của chúng ta chỉ tính score độc lập từ path vector mà chưa có Claim vector dẫn đường như paper GEAR gốc. Em đề xuất nâng cấp lên Claim-Conditioned Attention ($[c \,\|\, h_j]$) để model biết rõ Claim đang hỏi gì/phủ định gì khi cân trọng số giữa 32 paths."*

3. **Về định hướng tiếp theo:**
   > *"Thầy/Anh có đồng ý ưu tiên thử nghiệm kết hợp Claim-Conditioned Attention + Train End-to-End R3 trước, sau đó nếu cần mới mở rộng sang Adaptive Candidate Filtering và LLM fine-tune cho relation retrieval không ạ?"*
