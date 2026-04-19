# Hướng dẫn chạy FactKG (With Evidence) - bản dùng trực tiếp trên máy này

Tài liệu này đã điền sẵn đường dẫn đúng cho workspace hiện tại:
- Thư mục project: /home/namnx/duyanh/FactKG
- Thư mục dữ liệu: /home/namnx/duyanh/data
- File KG: /home/namnx/duyanh/data/dbpedia_2015_undirected_light.pickle

## 0. Chuẩn bị môi trường
Chạy từ bất kỳ thư mục nào:

~~~bash
source /home/namnx/duyanh/.venv/bin/activate
cd /home/namnx/duyanh/FactKG

# Cài dependency của repo
python -m pip install -r requirements.txt

# Bổ sung các package còn thiếu thường gặp khi chạy with_evidence
python -m pip install datasets tqdm termcolor pyyaml

# Gán biến để dùng lại trong các bước dưới
DATA_DIR=/home/namnx/duyanh/data
KG_PATH=/home/namnx/duyanh/data/dbpedia_2015_undirected_light.pickle

# Kiểm tra nhanh dữ liệu đầu vào có đủ chưa
ls "$DATA_DIR"/factkg_train.pickle "$DATA_DIR"/factkg_dev.pickle "$DATA_DIR"/factkg_test.pickle "$KG_PATH"
~~~

## 1. Graph Retriever

### 1.1 Tiền xử lý dữ liệu
~~~bash
cd /home/namnx/duyanh/FactKG/with_evidence/retrieve/data
python data_preprocess.py --data_directory_path "$DATA_DIR" --output_directory_path ../model/
~~~

### 1.2 Train và Eval Relation Predictor
~~~bash
cd /home/namnx/duyanh/FactKG/with_evidence/retrieve/model/relation_predict

# Train
python main.py --mode train --config ../config/relation_predict_top3.yaml

# Lấy checkpoint mới nhất
CKPT=$(find lightning_logs -name "*.ckpt" | sort | tail -n 1)
echo "$CKPT"

# Eval
python main.py --mode eval --config ../config/relation_predict_top3.yaml --model_path "$CKPT"
~~~

### 1.3 Train và Eval Hop Predictor
~~~bash
cd /home/namnx/duyanh/FactKG/with_evidence/retrieve/model/hop_predict

# Train
python main.py --mode train --config ../config/hop_predict.yaml

# Eval
python main.py --mode eval --config ../config/hop_predict.yaml --model_path ./model.pth
~~~

### 1.4 Báo cáo kết quả Evaluation (Top-3 Relations, Adam Optimizer)
Dưới đây là kết quả đánh giá (Accuracy) phân tách theo từng loại suy luận (Reasoning Types) trên tập Test:

| Loại Suy Luận (Reasoning Type) | Accuracy | Correct / Total | 
| :--- | :---: | :---: | 
| **Existence** (Sự tồn tại) | **84.02%** | 731 / 870 | 
| **Conjunction** (Mệnh đề phức hợp) | **79.99%** | 2455 / 3069 | 
| **Negation** (Phủ định) | **79.98%** | 1051 / 1314 | 
| **One-hop (num1)** | **75.76%** | 1450 / 1914 | 
| **Multi-hop** (Nhiều bước) | **61.42%** | 1151 / 1874 | 

**Nhận xét:**
- Mô hình xử lý tốt các câu hỏi Existence, Conjunction, và Negation.
- Điểm nghẽn lớn nhất nằm ở **Multi-hop** (61.42%). Việc hạn chế bằng chứng (`top_k: 3`) và sử dụng thuật toán tối ưu hóa `Adam` thuần (không có Weight Decay như `AdamW`) là nguyên nhân làm giảm đi khả năng tổng quát hóa của quá trình lý luận, khiến kết quả sụt giảm so với baseline gốc.

**Khuyến nghị bước tiếp theo:**
Đổi cấu hình lấy bằng chứng lên thành Top-5 (`relation_predict_top5.yaml`) hoặc chuyển lại thuật toán tối ưu về `AdamW` cho bộ BERT Classifier để khắc phục được các hạn chế này.

## 2. Classifier
~~~bash
cd /home/namnx/duyanh/FactKG/with_evidence/classifier
python baseline.py --data_path "$DATA_DIR" --kg_path "$KG_PATH" --prune_noise --epoch 10
~~~

## Lỗi thường gặp
1. ModuleNotFoundError: No module named datasets

~~~bash
python -m pip install datasets
~~~

2. Vào nhầm Python (không phải venv)

~~~bash
which python
python -c "import sys; print(sys.executable)"
~~~

Kết quả cần nằm trong /home/namnx/duyanh/.venv
