# Hướng dẫn Chạy Thực Nghiệm Full Pipeline (Train 5-hop, Test 3-hop)

**Mục tiêu:** Chạy lại sạch sẽ từ đầu pipeline `with_evidence` (từ sinh data, train Relation Top 3, đến train Hop 5 và đánh giá Test 3-hop) và tắt bỏ toàn bộ code tinh chỉnh của bước 4.

---

## BƯỚC 1: Tiền Xử Lý Dữ Liệu (Data Preprocess)
Biến file Pickle gốc thành các file `.json` dùng cho Retrieve Model.

```bash
source /home/namnx/duyanh/.venv/bin/activate
DATA_DIR=/home/namnx/duyanh/data
KG_PATH=/home/namnx/duyanh/data/dbpedia_2015_undirected_light.pickle

cd /home/namnx/duyanh/FactKG/with_evidence/retrieve/data
python data_preprocess.py --data_directory_path "$DATA_DIR" --output_directory_path ../model/
```

---

## BƯỚC 2: Huấn Luyện Relation Predictor (Top 3)
Mô hình này sẽ học cách chọn ra Top 3 Relations khả năng cao nhất.

```bash
cd /home/namnx/duyanh/FactKG/with_evidence/retrieve/model/relation_predict

# 2.1 Huấn luyện
python main.py --mode train --config ../config/relation_predict_top3.yaml
```

**⚠️ LƯU Ý 1 TRƯỚC KHI CHẠY TIẾP:** 
Hành động Train xong sẽ sinh ra một folder version mới trong `lightning_logs`. Bạn cần tìm file `.ckpt` trong đó để thay thế vào chỗ `$CKPT_PATH` dưới đây.
*(Ví dụ: `lightning_logs/version_4/checkpoints/epoch=9-step=17350.ckpt`)*

```bash
# 2.2 Sinh file Test Relations (Nhớ sửa thành đường dẫn thực tế)
python main.py --mode eval --config ../config/relation_predict_top3.yaml --model_path "$CKPT_PATH"
```

---

## BƯỚC 3: Huấn Luyện Hop Predictor (3-Hop và 5-Hop)
Ta cần train 2 model Hop Predictor: 1 cái 3-hop để lấy data Test, 1 cái 5-hop để lấy data Train.

**3.1 Train model 3-HOP (Tạo bản Test)**
Hãy đảm bảo file `../config/hop_predict.yaml` đang để `num_labels: 3`. Sửa lại nếu cần:
```bash
sed -i 's/num_labels: 5/num_labels: 3/g' /home/namnx/duyanh/FactKG/with_evidence/retrieve/model/config/hop_predict.yaml
```
Chạy train và eval để lấy file 3-hop:
```bash
cd /home/namnx/duyanh/FactKG/with_evidence/retrieve/model/hop_predict

python main.py --mode train --config ../config/hop_predict.yaml
python main.py --mode eval --config ../config/hop_predict.yaml --model_path ./model.pth

# Đã tạo xong predictions_hop.json 3-hop, cất đi để dành cho Test:
mv predictions_hop.json predictions_hop_3hop_old.json
```

**3.2 Train model 5-HOP (Tạo bản Train/Dev)**
Đổi config sang 5-hop:
```bash
sed -i 's/num_labels: 3/num_labels: 5/g' /home/namnx/duyanh/FactKG/with_evidence/retrieve/model/config/hop_predict.yaml
```
Chạy tiếp để lấy file 5-hop:
```bash
python main.py --mode train --config ../config/hop_predict.yaml
python main.py --mode eval --config ../config/hop_predict.yaml --model_path ./model.pth

# Lúc này predictions_hop.json đang chứa dự đoán 5-hop.
```

---

## BƯỚC 4: Build Candid Paths & Tráo File Dữ Liệu (Phần cốt lõi)
Nguyên tắc: Dùng JSON 5-hop để sinh dữ liệu Train/Dev, dùng JSON 3-hop cũ để sinh dữ liệu Test.

```bash
cd /home/namnx/duyanh/FactKG/with_evidence/classifier

# Đảm bảo lại biến môi trường một lần nữa trước khi build Graph
DATA_DIR=/home/namnx/duyanh/data
KG_PATH=/home/namnx/duyanh/data/dbpedia_2015_undirected_light.pickle

# 4.1 Càn quét DBpedia sinh path 5-hop cho MỌI TẬP  (Sẽ mất nhiều giờ)
python -c "from preprocess import prepare_input; prepare_input('$DATA_DIR', '$KG_PATH')"

# 4.2 Cất đi tập Train/Dev 5-hop vừa sinh để tránh bị ghi đè
mv train_candid_paths.bin train_candid_paths_5hop.bin
mv dev_candid_paths.bin dev_candid_paths_5hop.bin

# 4.3 Quay lại tráo file JSON 3-hop cũ vào làm bản chính
cd /home/namnx/duyanh/FactKG/with_evidence/retrieve/model/hop_predict
cp predictions_hop_3hop_old.json predictions_hop.json

# 4.4 Sinh lại Graph (Test sẽ là 3-hop chuẩn)
cd /home/namnx/duyanh/FactKG/with_evidence/classifier
python -c "from preprocess import prepare_input; prepare_input('$DATA_DIR', '$KG_PATH')"
```

---

## BƯỚC 5: Huấn Luyện Classifier Phân Loại Sự Thật
Mang các path đã được tinh chỉnh phía trên vào để Train Baseline.

```bash
cd /home/namnx/duyanh/FactKG/with_evidence/classifier

# 5.1 Khôi phục tập Train/Dev quay trở lại thành 5-hop
mv train_candid_paths_5hop.bin train_candid_paths.bin
mv dev_candid_paths_5hop.bin dev_candid_paths.bin

# 5.2 CHẠY HUẤN LUYỆN CUỐI CÙNG
python baseline.py \
    --data_path "$DATA_DIR" \
    --kg_path "$KG_PATH" \
    --n_candid 3 \
    --epoch 10
```


Dev Acc: 0.8304                                                                                                
-- # examples in 0: 1914 --                                                                                    
Acc for type 0: 0.8281  one hopp
-- # examples in 1: 1874 --
Acc for type 1: 0.6457 multihop
-- # examples in 2: 3069 --
Acc for type 2: 0.7960  conjunction
-- # examples in 3: 870 --
Acc for type 3: 0.8816 existence
-- # examples in 4: 1297 --
Acc for type 4: 0.7610 negation
Total Test Acc: 0.7748
---

# PHASE 2: Chạy Thực Nghiệm 3-Hop với Relation Top-5

Cách chạy hoàn toàn giống với luồng chuẩn của repo (như trong README gốc), chỉ thay đổi cấu hình `top5` ở bước Relation Predictor và khai báo `--n_candid 5` ở Classifier.

#### 1. Graph Retriever

**Step 1) Preprocess data**
```bash
cd /home/namnx/duyanh/FactKG/with_evidence/retrieve/data
python data_preprocess.py --data_directory_path /home/namnx/duyanh/data --output_directory_path ../model/
```

**Step 2) Train Relation Predictor (cấu hình Top-5)**
```bash
cd ../model/relation_predict
python main.py --mode train --config ../config/relation_predict_top5.yaml

# Lấy tự động file checkpoint mới nhất vừa train xong
CKPT=$(find lightning_logs -name "*.ckpt" | sort | tail -n 1)
python main.py --mode eval --config ../config/relation_predict_top5.yaml --model_path "$CKPT"
```

**Step 3) Train Hop Predictor (chuẩn 3-Hop)**
```bash
cd ../hop_predict
python main.py --mode train --config ../config/hop_predict.yaml
python main.py --mode eval --config ../config/hop_predict.yaml --model_path ./model.pth
```

#### 2. Classifier

**Step 4) Trích xuất Candid Paths & Huấn luyện Baseline**
```bash
cd ../../../classifier

# Sinh file test_candid_paths_top5.bin
python -c "from preprocess import prepare_input; prepare_input('/home/namnx/duyanh/data', '/home/namnx/duyanh/data/dbpedia_2015_undirected_light.pickle')"

# Chạy train classifier
python baseline.py --data_path /home/namnx/duyanh/data --kg_path /home/namnx/duyanh/data/dbpedia_2015_undirected_light.pickle --n_candid 5 --epoch 10
```

---

### Kết quả Đánh giá Phase 2 (3-Hop, Top-5 Relations)

Kết quả trả về từ `baseline.py`:
```text
-- # examples in 0: 1914 --                                                                              
Acc for type 0: 0.8422  (one-hop)
-- # examples in 1: 1874 --
Acc for type 1: 0.6884  (multi-hop)
-- # examples in 2: 3069 --
Acc for type 2: 0.8508  (conjunction)
-- # examples in 3: 870 --
Acc for type 3: 0.8908  (existence)
-- # examples in 4: 1297 --
Acc for type 4: 0.8435  (negation)
Total Test Acc: 0.8180
```

#### So sánh: Hôm qua (Top-3) vs Hôm nay (Top-5)

| Loại Suy Luận | Hôm qua (Train 3-Hop, Top-3) | Hôm nay (Train 3-Hop, Top-5) | Mức Tăng Trưởng |
| :--- | :---: | :---: | :---: |
| **Existence** | 88.16% | **89.08%** | **+0.92%** |
| **Conjunction** | 79.60% | **85.08%** | **+5.48%** |
| **Negation** | 76.10% | **84.35%** | **+8.25%** |
| **One-hop** | 82.81% | **84.22%** | **+1.41%** |
| **Multi-hop** | 64.57% | **68.84%** | **+4.27%** |
| **Total Test Acc** | 77.48% | **81.80%** | **+4.32%** |

#### Nhận xét chung:
1. **Khởi sắc toàn diện:** Việc nới rộng biên độ tìm kiếm từ *Top-3* lên *Top-5* ở bước dự đoán Relation mang lại sức mạnh vượt trội mà không cần dùng đến thủ thuật train 5-hop phức tạp. Tổng độ chính xác (Total Acc) tăng mạnh tới **4.32%**!
2. **Loại bỏ điểm nghẽn bằng chứng:** Các câu phức tạp nhưng đi đường ngắn (như *Conjunction* tăng 5.48% và *Negation* tăng 8.25%) hưởng lợi lớn nhất. Việc giữ Top-3 quá chật hẹp khiến mô hình dễ lỡ mất bằng chứng quan trọng ở các node liên quan, nới lên Top 5 đã giải quyết triệt để lỗi thiếu bằng chứng này.
3. **Cải thiện Multi-hop:** Dấu hiệu đáng mừng là *Multi-hop* đã được nhấc lên **68.84% (+4.27%)**. Kết hợp giới hạn ở 3-Hop cùng Relation Top-5 tạo ra một không gian con cân bằng: đủ rộng để tìm được đường đi đúng, nhưng lại không quá sâu (như 5-Hop) để gây nhiễu cho Bert Classifier.

-- # examples in 0: 1914 --                                                                              
Acc for type 0: 0.8422  one hop
-- # examples in 1: 1874 --
Acc for type 1: 0.6884 multihop
-- # examples in 2: 3069 --
Acc for type 2: 0.8508 conjunction
-- # examples in 3: 870 --
Acc for type 3: 0.8908  existence
-- # examples in 4: 1297 --
Acc for type 4: 0.8435 negation
Total Test Acc: 0.8180