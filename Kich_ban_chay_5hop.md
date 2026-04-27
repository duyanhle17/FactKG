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
