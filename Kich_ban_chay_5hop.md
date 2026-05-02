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
