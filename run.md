# Hướng dẫn chạy FactKG (Tiếp cận có Evidence)

Cụm code đồ án FactKG được thiết kế chia làm 2 giai đoạn: **Retriever** (Mò mẫm tìm Node/Cạnh trên đồ thị) và **Classifier** (Mô hình phân loại độ thật-giả dựa trên Evidence).

Dưới đây là các lệnh CMD cần thiết để chạy pipeline hoàn chỉnh từ đầu chí cuối:

---

## Bước 1: Retriever (Trích xuất tri thức thô)

**1. Tiền xử lý dữ liệu**
Để tạo ra các file input phục vụ train Relation và Hop, hãy chạy lệnh sau:
```bash
cd with_evidence/retrieve/data
python data_preprocess.py --data_directory_path ../../../data --output_directory_path ../model/
```

**2. Huấn luyện Model Đoán Relation (Relation Predictor)**
Model này sẽ nhìn câu Claim để đoán ra top 3 cụm Relation có thể xuất hiện (VD: `birthPlace`).
```bash
cd ../model/relation_predict
python main.py --mode train --config ../config/relation_predict_top3.yaml
```
Dự đoán ra file:
```bash
python main.py --mode eval --config ../config/relation_predict_top3.yaml --model_path <ĐƯỜNG_DẪN_TỚI_FILE_CKPT_VỪA_HỌC>
```

**3. Huấn luyện Model Đoán số Hop (Hop Predictor)**
Model này quyết định path của câu hỏi cần chĩa ra độ dài bao nhiêu (1, 2 hay 3 hop).
```bash
cd ../hop_predict
python main.py --mode train --config ../config/hop_predict.yaml
```
Dự đoán ra file:
```bash
python main.py --mode eval --config ../config/hop_predict.yaml --model_path ./model.pth
```

---

## Bước 2: Classifier (Phân loại thật giả + Module Chống Nhiễu)

Đây là nơi kết nối mô hình BERT, tiếp nhận các Node của Bước 1, kích hoạt luồng **cắt đuôi rác Heuristic**, **Flatten** văn bản và đưa ra phán quyết.

Để chạy Classifier với bộ code vừa nâng cấp tối ưu chống rác, luôn nhớ dập thẻ cờ `--prune_noise`:

```bash
cd ../../../classifier
python baseline.py \
    --data_path "../../../data" \
    --kg_path "../../../data/dbpedia_2015_undirected_light.pickle" \
    --prune_noise \
    --epoch 10
```

> **Lưu ý:**
> - Tham số `--data_path` trỏ tới thư mục chứa các file `factkg_train/dev/test.pickle`.
> - Tham số `--kg_path` phải trỏ đúng tới file gốc DBpedia của hệ thống.
> - Cờ `--prune_noise` sẽ tự động kích hoạt Phase 1 & Phase 2 mà chúng ta vừa update ở `prune_candid_paths.py` và `baseline.py`.
