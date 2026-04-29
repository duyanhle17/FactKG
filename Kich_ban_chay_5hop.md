# Kịch Bản Thử Nghiệm Huấn Luyện 5-Hop (FactKG)

**Mục tiêu:** Tạm ẩn các tinh chỉnh tối ưu của tuần trước để quay về kiến trúc xử lý Evidence phẳng (flat text) gốc của FactKG. Sau đó, tiến hành nâng cấp Hop Predictor lên 5 lớp để kiểm tra năng lực suy luận dài (5-hop) của mô hình.

---

## 1. Tổng Quan Pipeline Đã Chỉnh Sửa

Hệ thống hoạt động qua 2 giai đoạn:
1. **Retriever (Tìm kiếm bằng chứng):**
   - **Hop Predictor:** Đã được cấu hình lại từ `num_labels=3` lên `num_labels=5`. Mô hình sẽ dự đoán độ sâu của câu tìm kiếm (1 đến 5 bước).
   - **Relation Predictor:** Giữ nguyên cấu hình `top_k=3` (chọn 3 quan hệ tốt nhất để đi tiếp tại mỗi bước).
2. **Classifier (Bộ phân loại BERT):**
   - Các tinh chỉnh `soft_flatten_path` và `prune_candid_paths` đã bị vô hiệu hóa (comment out). 
   - Đầu vào của mô hình quay lại định dạng gốc: một mảng phẳng các Node và Relation được nối trực tiếp bằng thẻ `[SEP]`.
   - Giữ nguyên thuật toán tối ưu `torch.optim.Adam`.

---

## 2. Chi Tiết Lệnh Chạy Thực Nghiệm (Server L40S)

### 2.1. Chuẩn bị môi trường
```bash
source /home/namnx/duyanh/.venv/bin/activate
cd /home/namnx/duyanh/FactKG

DATA_DIR=/home/namnx/duyanh/data
KG_PATH=/home/namnx/duyanh/data/dbpedia_2015_undirected_light.pickle
```

### 2.2. Huấn luyện lại Hop Predictor (Lên 5-hop)
```bash
cd /home/namnx/duyanh/FactKG/with_evidence/retrieve/model/hop_predict

# Train mô hình dự đoán hop mới (hỗ trợ 1-5 hop)
python main.py --mode train --config ../config/hop_predict.yaml

# Đánh giá và sinh ra file predictions_hop.json (chứa dự đoán 5-hop)
python main.py --mode eval --config ../config/hop_predict.yaml --model_path ./model.pth
```

---

### 2.3. Pha Chạy 1: Cross-Test (Train 5-hop, Test 3-hop)
**Mục đích:** Kiểm tra hiện tượng *Zero-shot transfer / OOD*. Xem việc bắt mô hình học cấu trúc suy luận dài (5-hop) có giúp nó giải quyết tốt hơn các câu hỏi ngắn (3-hop) hay không, hay sẽ gây ra nhiễu (overthinking).

```bash
# --- Bước A: Cất file 3-hop cũ để dự phòng ---
cd /home/namnx/duyanh/FactKG/with_evidence/retrieve/model/hop_predict
# (Giả định bạn đã chạy Bước 2.2 ở trên và có predictions_hop.json là 5-hop)
cp predictions_hop.json predictions_hop_5hop_backup.json

# --- Bước B: Sinh dữ liệu Train 5-hop ---
cd /home/namnx/duyanh/FactKG/with_evidence/classifier
python -c "from preprocess import prepare_input; prepare_input('$DATA_DIR', '$KG_PATH')"
mv train_candid_paths.bin train_candid_paths_5hop.bin
mv dev_candid_paths.bin dev_candid_paths_5hop.bin

# --- Bước C: Sinh lại dữ liệu Test 3-hop ---
cd /home/namnx/duyanh/FactKG/with_evidence/retrieve/model/hop_predict
# (Lấy file hop 3-hop cũ, đổi tên nó lại thành chuẩn)
cp predictions_hop_3hop_old.json predictions_hop.json

cd /home/namnx/duyanh/FactKG/with_evidence/classifier
python -c "from preprocess import prepare_input; prepare_input('$DATA_DIR', '$KG_PATH')"
# File test_candid_paths_top3.bin lúc này được sinh ra là 3-hop chuẩn.

# --- Bước D: Phục hồi tên file và chạy Classifier ---
mv train_candid_paths_5hop.bin train_candid_paths.bin
mv dev_candid_paths_5hop.bin dev_candid_paths.bin

python baseline.py \
    --data_path "$DATA_DIR" \
    --kg_path "$KG_PATH" \
    --n_candid 3 \
    --epoch 10
```

---

### 2.4. Pha Chạy 2: Đồng nhất (Train 5-hop, Test 5-hop)
**Mục đích:** Đánh giá hiệu suất toàn diện của FactKG khi cả hệ thống (từ lúc train đến lúc test) đều vận hành trên độ sâu 5 bước nhảy. So sánh kết quả Accuracy tổng và Multi-hop với mốc baseline 61.42% của tuần trước.

```bash
# --- Bước A: Khôi phục lại hop 5-hop ---
cd /home/namnx/duyanh/FactKG/with_evidence/retrieve/model/hop_predict
cp predictions_hop_5hop_backup.json predictions_hop.json

# --- Bước B: Sinh toàn bộ candid_paths (Tất cả đều 5-hop) ---
cd /home/namnx/duyanh/FactKG/with_evidence/classifier
python -c "from preprocess import prepare_input; prepare_input('$DATA_DIR', '$KG_PATH')"

# --- Bước C: Chạy Classifier ---
python baseline.py \
    --data_path "$DATA_DIR" \
    --kg_path "$KG_PATH" \
    --n_candid 3 \
    --epoch 10
```

---

## 3. Khía Cạnh Nghiên Cứu & Đánh Giá

Quá trình tinh chỉnh cấu hình và thực nghiệm này đóng góp vào 3 mảng nghiên cứu chính của hệ thống:
1. **Knowledge Graph-based Fact Verification:** Trực tiếp cải thiện khả năng suy luận đa bước (multi-hop reasoning) trên đồ thị. Đánh giá xem việc nới lỏng giới hạn tìm kiếm có khắc phục được lỗi thiếu evidence hay không.
2. **Evidence Retrieval Quality:** Tìm điểm cân bằng giữa Độ rộng (Relation `top_k`) và Độ sâu (Hop Prediction) để không làm tràn giới hạn tokenizer 512 của BERT.
3. **Ablation Study:** Tạo cơ sở dữ liệu vững chắc cho bài báo cáo khoa học bằng việc so sánh đối chứng giữa nhiều cấu hình (Train 5-hop vs Train 3-hop).

---

## 4. Chiến Lược Cải Tiến Multi-hop (Không Làm Suy Giảm One-hop & Reasoning)

> **Nguyên tắc xuyên suốt:** Mọi cải tiến đều phải đảm bảo: (1) Không tăng nhiễu vào đầu vào BERT cho các câu hỏi 1-hop đơn giản, (2) Giữ nguyên hoặc cải thiện chất lượng evidence cho Existence / Conjunction / Negation.

### 4.1. Chiến Lược A — Claim-Aware Path Re-Ranking (Ưu tiên cao nhất)

**Vấn đề cốt lõi:** Hiện tại, tất cả candidate paths được ghép vào BERT một cách "dân chủ" — không path nào được ưu tiên hơn path nào. Với multi-hop, số lượng path bùng nổ tổ hợp (permutation của `top_k` relations qua `hop` bước), dẫn đến path đúng bị "chìm" giữa hàng chục path rác. Trong khi đó, one-hop ít bị ảnh hưởng vì số path ít.

**Giải pháp — Thêm bước Re-Rank trước khi ghép vào BERT:**

Xây dựng một hàm scoring nhẹ (không cần train riêng model) để chấm điểm từng candidate path theo mức độ liên quan với claim, sau đó **chỉ giữ lại Top-N path có điểm cao nhất** để ghép vào evidence:

```python
# === Thêm vào baseline.py (trước khi tạo Dataset) ===

def score_path_relevance(path: list, claim: str) -> float:
    """Tính điểm liên quan giữa 1 path với claim bằng token overlap.
    
    Path format: [Entity, Relation, Entity, Relation, Entity, ...]
    Score = tỷ lệ token trong path trùng với claim tokens.
    Bonus: nhân hệ số cao hơn cho entity trùng (x2) so với relation trùng (x1).
    """
    claim_tokens = set(re.findall(r'[a-z0-9]+', claim.lower()))
    if not claim_tokens:
        return 0.0

    total_score = 0.0
    for idx, element in enumerate(path):
        elem_tokens = set(re.findall(r'[a-z0-9]+', element.replace('_', ' ').lower()))
        overlap = elem_tokens & claim_tokens
        # Entity (vị trí chẵn) quan trọng hơn Relation (vị trí lẻ)
        weight = 2.0 if idx % 2 == 0 else 1.0
        total_score += len(overlap) * weight
    
    # Normalize theo độ dài claim
    return total_score / len(claim_tokens)


def rerank_evidence(connected: list, walkable: list, claim: str, max_paths: int = 5):
    """Chấm điểm và giữ lại top-N path liên quan nhất."""
    all_paths = [(p, 'c') for p in connected] + [(p, 'w') for p in walkable]
    scored = [(score_path_relevance(p, claim), p, src) for p, src in all_paths]
    scored.sort(key=lambda x: x[0], reverse=True)
    
    top_connected = [p for _, p, src in scored[:max_paths] if src == 'c']
    top_walkable = [p for _, p, src in scored[:max_paths] if src == 'w']
    return top_connected, top_walkable
```

**Tại sao an toàn cho One-hop & Reasoning:**
- Với câu hỏi 1-hop: Số path ít, gần như tất cả đều được giữ lại → không đổi.
- Với Existence/Conjunction/Negation: Các path liên quan sẽ luôn có score cao vì entity trùng trực tiếp với claim → không bị lọc mất.
- Chỉ multi-hop mới hưởng lợi lớn vì loại bỏ được path rác do BFS tổ hợp tạo ra.

**Lệnh chạy thí nghiệm:**
```bash
cd /home/namnx/duyanh/FactKG/with_evidence/classifier

# Tích hợp hàm rerank vào baseline.py, sau đó chạy:
python baseline.py \
    --data_path "$DATA_DIR" \
    --kg_path "$KG_PATH" \
    --n_candid 3 \
    --epoch 10
```

---

### 4.2. Chiến Lược B — Adaptive Top-K Theo Dự Đoán Hop

**Vấn đề:** Hiện tại `top_k` (số relation được chọn ở mỗi bước) là **cố định cho tất cả các claim** (luôn = 3). Câu hỏi 1-hop chỉ cần 1 relation đúng, nhưng câu hỏi 3-hop trở lên cần nhiều ứng viên hơn tại mỗi bước để tăng xác suất trúng chuỗi đúng.

**Giải pháp — Map hop dự đoán sang top_k riêng:**

```python
# === Sửa trong preprocess.py, hàm prepare_input(), phần xử lý test ===

# Thay vì dùng cố định top_k=3 cho tất cả claim:
# candids = predicted_rs[elem[0]]   # luôn lấy 3 relation

# Dùng mapping linh hoạt:
HOP_TO_TOPK = {
    1: 3,   # 1-hop: 3 relation là đủ (giữ nguyên)
    2: 4,   # 2-hop: nới lên 4 để tăng recall
    3: 5,   # 3-hop: cần 5 relation
    4: 5,   # 4-hop: giữ ở 5 để không tràn token
    5: 5,   # 5-hop: giữ ở 5
}

# Trong vòng lặp sinh test data:
hop = predicted_hops[elem[0]]
adaptive_k = HOP_TO_TOPK.get(hop, 3)
candids_for_claim = predicted_rs_top5[elem[0]][:adaptive_k]
# ^ Lấy từ file top-5 nhưng chỉ dùng adaptive_k relation
rels = {e: list(permutations(candids_for_claim, r=hop)) for e in ents}
```

**Điều kiện tiên quyết:** Phải chạy lại Relation Predictor với config `relation_predict_top5.yaml` để có file `test_relations_top5.json`:
```bash
cd /home/namnx/duyanh/FactKG/with_evidence/retrieve/model/relation_predict
python main.py --mode eval \
    --config ../config/relation_predict_top5.yaml \
    --model_path "$CKPT"
```

**Tại sao an toàn:**
- Câu 1-hop vẫn dùng `top_k=3` → **hoàn toàn không đổi**.
- Câu multi-hop được nới rộng có kiểm soát (tối đa 5, không phải 10) → tăng recall mà không làm tràn 512 token.
- Conjunction/Negation thường là 1-hop → không bị ảnh hưởng.

---

### 4.3. Chiến Lược C — Kích Hoạt Có Chọn Lọc Pipeline Prune + Soft Flatten

**Phân tích từ tuần trước:** Pipeline KG cải tiến (Phase 1.1 → 1.3 + Phase 2) đã được chứng minh tăng điểm Existence/Conjunction/Negation nhưng lại giảm nhẹ Multi-hop (-7%). Nguyên nhân: Tail Trimming cắt quá mạnh vào path multi-hop (mất thông tin ở hop cuối), và Sub-path Expansion sinh quá nhiều path ngắn làm "pha loãng" tín hiệu path dài.

**Giải pháp — Kích hoạt có chọn lọc theo hop:**

```python
# === Sửa prune_candid_paths.py — Chỉ prune path NGẮN, giữ nguyên path DÀI ===

def prune_group_adaptive(
    paths: list, 
    claim_tokens: set, 
    max_hops: int,
    trim_threshold: int = 2,   # Chỉ trim tail cho path <= 2 hop
    expand_threshold: int = 2, # Chỉ expand sub-path cho path <= 2 hop
):
    """Phiên bản cải tiến: Bảo vệ path dài khỏi bị cắt xén quá mức."""
    result = []
    for p in paths:
        hops = path_hops(p)
        if hops > max_hops:
            continue
        
        if hops <= trim_threshold:
            # Path ngắn: trim tail bình thường
            trimmed = trim_tail(p, claim_tokens)
        else:
            # Path dài (3+ hop): KHÔNG trim → giữ nguyên toàn bộ
            trimmed = p
        
        if hops <= expand_threshold:
            # Path ngắn: expand sub-paths
            subs = expand_subpaths(trimmed)
            result.extend(subs)
        else:
            # Path dài: Chỉ thêm path gốc, không sinh sub-path
            result.append(trimmed)
    
    return deduplicate_paths(result)
```

**Kết hợp với Soft Flatten (Phase 2):**
```python
# === Bật lại soft_flatten_path trong baseline.py ===
# Nhưng CHỈ áp dụng cho evidence, KHÔNG thay đổi claim

# Trong Dataset.__getitem__():
flat_evi = list(chain(*self.evis[i][0])) + list(chain(*self.evis[i][1]))

# Sửa thành:
connected_strs = [soft_flatten_path(p) for p in self.evis[i][0]]
walkable_strs = [soft_flatten_path(p) for p in self.evis[i][1]]
flat_evi = connected_strs + walkable_strs
```

**Tại sao an toàn:**
- One-hop (1 bước): Được trim + expand bình thường → vẫn hưởng lợi từ Soft Flatten.
- Multi-hop (3+ bước): **Không bị cắt tail**, không bị pha loãng bởi sub-path → giữ nguyên chuỗi suy luận dài.
- Soft Flatten giúp BERT tokenize tốt hơn cho **tất cả** loại câu hỏi.

---

### 4.4. Chiến Lược D — Evidence Attention Pooling (Nâng Cấp Classifier)

**Vấn đề kiến trúc:** `ConcatClassifier` hiện tại chỉ lấy `[CLS]` token của BERT rồi đưa qua MLP 2 lớp. Với multi-hop, evidence dài và phức tạp, thông tin nằm rải rác khắp sequence — chỉ dùng `[CLS]` sẽ mất nhiều tín hiệu quan trọng.

**Giải pháp — Thêm Attention Pooling trên evidence tokens:**

```python
class AttentionPool(nn.Module):
    """Lightweight attention pooling over evidence token representations."""
    def __init__(self, hidden_size):
        super().__init__()
        self.query = nn.Linear(hidden_size, 1)
    
    def forward(self, hidden_states, attention_mask):
        # hidden_states: [batch, seq_len, hidden]
        # attention_mask: [batch, seq_len]
        scores = self.query(hidden_states).squeeze(-1)  # [batch, seq_len]
        scores = scores.masked_fill(attention_mask == 0, -1e9)
        weights = torch.softmax(scores, dim=-1)          # [batch, seq_len]
        pooled = (hidden_states * weights.unsqueeze(-1)).sum(dim=1)  # [batch, hidden]
        return pooled


class ImprovedConcatClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.config = AutoConfig.from_pretrained(PT_CLS)
        hidden = self.config.hidden_size
        
        self.encoder = AutoModel.from_pretrained(PT_CLS)
        self.attn_pool = AttentionPool(hidden)
        
        # Kết hợp CLS + Attention Pooled
        self.shallow_classifier = nn.Sequential(
            nn.Linear(hidden * 2, hidden),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden, 2),
        )
        self.loss_fct = nn.CrossEntropyLoss()
    
    def forward(self, inputs):
        cated_inputs = {
            k: torch.cat([inputs["claim"][k], inputs["evidence"][k]], dim=-1)
            for k in inputs["claim"]
        }
        encoder_outputs = self.encoder(**cated_inputs, return_dict=True)
        
        cls_output = encoder_outputs.last_hidden_state[:, 0]        # [CLS]
        attn_output = self.attn_pool(
            encoder_outputs.last_hidden_state,
            cated_inputs["attention_mask"]
        )
        
        combined = torch.cat([cls_output, attn_output], dim=-1)     # [batch, hidden*2]
        logit = self.shallow_classifier(combined)
        loss = self.loss_fct(logit, inputs["label"])
        
        return loss, logit
```

**Tại sao an toàn:**
- One-hop: Evidence ngắn → Attention Pool gần như tương đương Mean Pool → không tệ hơn CLS.
- Multi-hop: Evidence dài → Attention Pool học được cách tập trung vào các token quan trọng nhất → **cải thiện đáng kể**.
- Dropout 0.1 giúp chống overfitting cho các loại câu hỏi ít mẫu.

---

### 4.5. Thứ Tự Ưu Tiên Thực Hiện

| Thứ tự | Chiến lược | Độ khó | Rủi ro One-hop | Kỳ vọng Multi-hop |
| :---: | :--- | :---: | :---: | :---: |
| **①** | **A. Claim-Aware Re-Rank** | Thấp | ✅ Không đổi | +3~5% |
| **②** | **B. Adaptive Top-K** | Thấp | ✅ Không đổi | +2~4% |
| **③** | **C. Prune Chọn Lọc + Soft Flatten** | Trung bình | ✅ Cải thiện nhẹ | +3~6% |
| **④** | **D. Attention Pooling Classifier** | Trung bình | ✅ Tương đương | +2~4% |

> **Khuyến nghị:** Chạy tuần tự **A → B → C → D**, mỗi bước đo đầy đủ 5 loại câu hỏi trước khi tiến sang bước tiếp theo. Nếu A+B đã đạt >67% Multi-hop mà không giảm One-hop, có thể bỏ qua D để tiết kiệm thời gian.

### 4.6. Lệnh Chạy Tổng Hợp (Kịch Bản Kết Hợp A+B+C)

```bash
# === Bước 1: Chạy lại Relation Predictor với top_k=5 ===
cd /home/namnx/duyanh/FactKG/with_evidence/retrieve/model/relation_predict
python main.py --mode eval \
    --config ../config/relation_predict_top5.yaml \
    --model_path "$CKPT"

# === Bước 2: Bật lại code prune adaptive + soft flatten trong baseline.py ===
# (Uncomment các hàm đã tạm ẩn, thay prune_group bằng prune_group_adaptive)
# (Thêm hàm score_path_relevance + rerank_evidence)

# === Bước 3: Chạy Classifier với pipeline mới ===
cd /home/namnx/duyanh/FactKG/with_evidence/classifier
python baseline.py \
    --data_path "$DATA_DIR" \
    --kg_path "$KG_PATH" \
    --n_candid 5 \
    --prune_noise \
    --epoch 10
```

### 4.7. Bảng So Sánh Dự Kiến Kết Quả

| Reasoning Type | Baseline hiện tại | Kỳ vọng A+B | Kỳ vọng A+B+C+D |
| :--- | :---: | :---: | :---: |
| Existence | 84.02% | 84~85% | 84~86% |
| Conjunction | 79.99% | 80~81% | 80~82% |
| Negation | 79.98% | 80% | 80~81% |
| One-hop | 75.76% | 75~77% | 76~78% |
| **Multi-hop** | **61.42%** | **65~68%** | **68~72%** |
