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