# Kịch Bản Thử Nghiệm: Huấn Luyện 5-Hop, Đánh Giá 3-Hop

**Mục tiêu:** Kiểm tra hiện tượng *Zero-shot transfer*. Chúng ta muốn xem việc ép mô hình học cách suy luận qua các đường dẫn dài (5-hop) trong lúc huấn luyện (Train) có giúp nó trả lời tốt hơn các câu hỏi ngắn (3-hop) lúc kiểm tra (Test) hay không.

---

## 🛑 Vấn đề cốt lõi: Tại sao phải đổi tên file và cất dự phòng?

Hệ thống FactKG được thiết kế để đọc cấu hình số hop từ **một file duy nhất** tên là `predictions_hop.json`. File này chứa số hop dự đoán cho CẢ tập Train, Dev và Test.
1. Khi bạn train mô hình lên 5-hop, file `predictions_hop.json` sẽ chứa toàn bộ là dự đoán 5-hop.
2. Nếu cứ thế chạy tiếp, tập Test cũng sẽ biến thành 5-hop (sai mục tiêu Train 5, Test 3).
3. Do đó, ta bắt buộc phải dùng **thủ thuật tráo file**: Dùng file 5-hop để sinh dữ liệu Train, sau đó tráo lại file 3-hop cũ để sinh dữ liệu Test.

Dưới đây là các bước chạy chi tiết và đã được làm rõ:

---

## Các Bước Thực Hiện Chi Tiết

### Bước 1: Chuẩn bị môi trường
Kích hoạt môi trường và set biến môi trường.
```bash
source /home/namnx/duyanh/.venv/bin/activate
cd /home/namnx/duyanh/FactKG

DATA_DIR=/home/namnx/duyanh/data
KG_PATH=/home/namnx/duyanh/data/dbpedia_2015_undirected_light.pickle
```

### Bước 2: Sinh file dự đoán Hop 5-hop
Bước này huấn luyện Hop Predictor mới với cấu hình 5-hop.
```bash
cd /home/namnx/duyanh/FactKG/with_evidence/retrieve/model/hop_predict

# 2.1. CẤT DỰ PHÒNG FILE 3-HOP CŨ
# Trước khi train 5-hop, ta phải cất file 3-hop của tuần trước đi để lát nữa dùng cho tập Test.
cp predictions_hop.json predictions_hop_3hop_old.json

# 2.2. Huấn luyện mô hình 5-hop (đã chỉnh num_labels: 5 trong config)
python main.py --mode train --config ../config/hop_predict.yaml

# 2.3. Sinh file dự đoán MỚI
python main.py --mode eval --config ../config/hop_predict.yaml --model_path ./model.pth
# LƯU Ý: Lúc này file 'predictions_hop.json' đã mang dữ liệu 5-hop.
```

### Bước 3: Sinh dữ liệu đường dẫn (Candid Paths) cho Train 5-hop
Dùng file 5-hop vừa tạo để BFS trên Knowledge Graph, sinh ra các đường dẫn dài 5 bước.
```bash
cd /home/namnx/duyanh/FactKG/with_evidence/classifier

# 3.1. Chạy preprocess để sinh đường dẫn
python -c "from preprocess import prepare_input; prepare_input('$DATA_DIR', '$KG_PATH')"
# Kết quả: Sinh ra 3 file: train_candid_paths.bin, dev_candid_paths.bin, test_candid_paths_top3.bin
# (Hiện tại cả 3 file này đều là đường dẫn 5-hop)

# 3.2. ĐỔI TÊN ĐỂ TRÁNH BỊ GHI ĐÈ
# Vì ta chỉ lấy Train/Dev 5-hop, ta sẽ đổi tên chúng đi cất.
mv train_candid_paths.bin train_candid_paths_5hop.bin
mv dev_candid_paths.bin dev_candid_paths_5hop.bin
```

### Bước 4: Sinh lại dữ liệu Test 3-hop chuẩn
Giờ ta cần tạo lại file Test 3-hop bằng cách tráo lại file `predictions_hop.json` cũ.
```bash
# 4.1. TRÁO FILE: Lấy lại file 3-hop lúc nãy làm file chính
cd /home/namnx/duyanh/FactKG/with_evidence/retrieve/model/hop_predict
cp predictions_hop_3hop_old.json predictions_hop.json

# 4.2. Chạy lại preprocess
cd /home/namnx/duyanh/FactKG/with_evidence/classifier
python -c "from preprocess import prepare_input; prepare_input('$DATA_DIR', '$KG_PATH')"
# Kết quả: File test_candid_paths_top3.bin được sinh ra lại, lúc này ĐÚNG CHUẨN LÀ 3-HOP.
# (Nó cũng sinh ra train/dev 3-hop nhưng ta kệ chúng, không xài)
```

### Bước 5: Phục hồi tên và Huấn Luyện Classifier
Mang các file Train/Dev 5-hop đã cất ở Bước 3 ra dùng chung với Test 3-hop ở Bước 4.
```bash
cd /home/namnx/duyanh/FactKG/with_evidence/classifier

# 5.1. Đưa file 5-hop trở lại tên mặc định để Classifier có thể đọc
mv train_candid_paths_5hop.bin train_candid_paths.bin
mv dev_candid_paths_5hop.bin dev_candid_paths.bin

# CHỐT LẠI LÚC NÀY TA CÓ:
# - train_candid_paths.bin: 5-hop
# - dev_candid_paths.bin: 5-hop
# - test_candid_paths_top3.bin: 3-hop

# 5.2. Chạy Baseline Classifier
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

---

## 5. Báo Cáo 6/5: Phân Tích Kết Quả Chạy 5-Hop & Giải Pháp Đột Phá Cho Multi-hop

**Kết quả thực tế đo được:**
- **One-hop (Type 0):** `0.8281` (Tăng mạnh so với mốc 75.76%)
- **Multi-hop (Type 1):** `0.6457` (Tăng nhẹ từ 61.42% lên 64.57%, NHƯNG CHƯA ĐẠT KỲ VỌNG)
- **Conjunction (Type 2):** `0.7960` (Giảm nhẹ so với 79.99%)
- **Existence (Type 3):** `0.8816` (Tăng tốt so với 84.02%)
- **Negation (Type 4):** `0.7610` (Giảm so với 79.98%)
- **Total Test Acc:** `0.7748`

### 5.1. Lý giải: Tại sao huấn luyện 5-hop gần như không cải thiện Multi-hop?

Dù chúng ta kỳ vọng việc cấp cho mô hình các đường dẫn dài (5-hop) sẽ giúp nó giải quyết các câu hỏi phức tạp tốt hơn, nhưng thực tế mức tăng lại rất khiêm tốn (+3% và chưa đột phá). Nguyên nhân cốt lõi bao gồm:

1. **Hiệu ứng "Bùng nổ nhiễu" (Noise Amplification):** 
   - Khi tăng độ sâu lên 5 bước nhảy, số lượng candidate paths sinh ra từ thuật toán BFS trên Knowledge Graph tăng theo cấp số nhân. 
   - Một câu hỏi thực chất chỉ cần 2-3 hop nhưng lại bị ghép kèm hàng loạt path 5-hop không liên quan. Các path rác này làm loãng tín hiệu của path đúng, khiến Classifier (BERT) bị "ngợp" thông tin.
2. **Giới hạn 512 Tokens của BERT:** 
   - Khi nối (concat) quá nhiều đường dẫn 5-hop lại với nhau, tổng số token dễ dàng vượt qua giới hạn độ dài `max_length = 512` của mô hình BERT.
   - Hệ quả là BERT sẽ cắt bỏ (truncate) phần đuôi của chuỗi văn bản. Rất có thể phần bị cắt đi lại chứa chính evidence quan trọng nhất, khiến mô hình không có đủ thông tin để kết luận, do đó độ chính xác không thể tăng thêm.
3. **Đặc thù dữ liệu Multi-hop của tập FactKG:**
   - Đa số câu hỏi được phân loại là "multi-hop" trong tập FactKG thực chất chỉ đòi hỏi 2 hoặc 3 bước suy luận. Các câu hỏi thực sự cần đến 4 hoặc 5 bước là cực kỳ hiếm. Việc ép mô hình phải duyệt 5-hop cho toàn bộ tập dữ liệu là sự lãng phí tài nguyên và rước thêm nhiễu không đáng có.
4. **Hạn chế của kiến trúc Classifier (`ConcatClassifier`) hiện tại:**
   - Hệ thống hiện tại chỉ nối toàn bộ chuỗi văn bản và dùng token `[CLS]` để phân loại. Việc đọc một chuỗi dài dằng dặc các entity và relation lộn xộn khiến mô hình mất khả năng "chú ý" (focus) vào các kết nối logic hẹp. Càng đưa nhiều path dài, `[CLS]` càng dễ mất phương hướng.

### 5.2. Các hướng cải tiến Đột Phá cho Multi-hop

Vì phương pháp "nhồi nhét" đường dẫn dài đã chạm ngưỡng (hiệu năng đi ngang), ta cần chuyển sang hướng **Tinh lọc (Precision)** và **Cấu trúc hóa (Structuring)**. Dưới đây là các nâng cấp cần thiết nhất lúc này:

#### 🌟 Cải tiến 1: Re-ranking & Filtering (Lọc đường dẫn trước khi phân loại - Quan trọng nhất)
Không phải path nào cũng có giá trị. Thay vì ném tất cả path sinh ra cho BERT, ta cần một bộ lọc thô.
- **Cách làm:** Tính độ tương đồng (Similarity) giữa chuỗi câu hỏi (Claim) và từng đường dẫn (Path) - có thể dùng token overlap (như Chiến lược A ở mục 4.1) hoặc dùng một mô hình Sentence-BERT tính Cosine Similarity.
- **Hành động:** Sau khi sinh ra hàng chục path 5-hop, **chỉ giữ lại Top 3 - 5 đường dẫn có điểm số liên quan cao nhất** để đưa vào Classifier. Điều này giải quyết triệt để vấn đề nhiễu rác và giới hạn 512 token.

#### 🌟 Cải tiến 2: Phân tách Context thay vì Concat (Kiến trúc Cross-Attention / GEAR)
Đừng nối tất cả đường dẫn thành một đoạn văn duy nhất. Hãy cho BERT đánh giá mức độ đúng/sai của *từng đường dẫn* một cách độc lập.
- **Cách làm:** Đưa qua BERT theo từng cặp: `[CLS] Claim [SEP] Path 1 [SEP]`, `[CLS] Claim [SEP] Path 2 [SEP]`, v.v... Lấy embedding của từng path rồi dùng thuật toán Attention (hoặc Max-Pooling) để tổng hợp lại.
- **Lợi ích:** Mô hình không bao giờ bị tràn token và nó có thể xác định rõ ràng path nào là bằng chứng thực sự dẫn đến kết quả. (Đây là nền tảng của kiến trúc GEAR).

#### 🌟 Cải tiến 3: Adaptive Hop Retrieval (Số bước nhảy linh hoạt)
Tuyệt đối không cố định tìm 5-hop cho tất cả câu hỏi.
- **Cách làm:** Phụ thuộc hoàn toàn vào kết quả của mô hình *Hop Predictor*. Nếu Hop Predictor dự đoán câu hỏi là 2-hop, BFS chỉ tìm tối đa 2-hop. Nếu đoán 3-hop, tìm 3. (Đây chính là Chiến lược B ở mục 4.2).
- **Lợi ích:** Giữ nguyên hiệu năng cực tốt của One-hop (82%) và Existence (88%) do không bị chèn thêm nhiễu, đồng thời cung cấp đủ path cho các câu hỏi đa bước thực sự.

#### 🌟 Cải tiến 4: Verbalization ("Mềm hóa" đường dẫn)
Đường dẫn dạng thô `Entity A -> relation -> Entity B -> relation -> Entity C` rất thiếu tự nhiên.
- **Cách làm:** Viết một hàm verbalizer chuyển đổi đường dẫn thành câu văn trôi chảy (Soft Flattening). Ngôn ngữ tự nhiên hơn sẽ giúp mô hình BERT pre-trained phát huy tối đa khả năng suy luận logic thay vì bị bối rối bởi các dấu phẩy hay ký tự gạch dưới `_`.

---
**Kết luận:** 
Điểm số One-hop và Existence trong bài test này đã lên rất ấn tượng (lần lượt 82.8% và 88.1%), minh chứng rõ ràng rằng baseline hiện tại học các suy luận nông cực kỳ xuất sắc. Việc Multi-hop bị "nghẽn" ở mức 64% khẳng định rằng **tăng độ sâu BFS (lên 5) sinh ra quá nhiều nhiễu, làm mờ đi tín hiệu đúng**. 

Để bức phá, nhiệm vụ tiếp theo không phải là mở rộng tìm kiếm, mà là **LỌC (Re-rank) đường dẫn** (Cải tiến 1) và **Xử lý linh hoạt theo số Hop** (Cải tiến 3).

