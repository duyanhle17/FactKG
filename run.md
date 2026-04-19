# Hướng dẫn chạy FactKG (With Evidence)

Dưới đây là chuỗi lệnh Terminal được căn chỉnh chính xác theo thứ tự và cấu trúc thư mục của dự án gốc. Vui lòng mở Terminal và **đứng tại thư mục gốc của project (FactKG/)** trước khi bắt đầu copy lần lượt các block code dưới đây.

---

### Bước 1: Trích xuất tri thức (Graph Retriever)

**1. Tiền xử lý dữ liệu**
Chuyển hướng vào thư mục data của retriever và sinh input cho mô hình:
```bash
cd with_evidence/retrieve/data
python data_preprocess.py \
    --data_directory_path <<<thư_mục_chứa_file_factkg_train_dev_test.pickle>>> \
    --output_directory_path ../model/
```

**2. Huấn luyện mô hình đoán Relation**
Tiếp tục lùi một thư mục và vào phần module relation_predict:
```bash
cd ../model/relation_predict

# Train
python main.py --mode train --config ../config/relation_predict_top3.yaml

# Eval (thay đường dẫn .ckpt tương ứng model vừa sinh ra ở folder logs)
python main.py --mode eval --config ../config/relation_predict_top3.yaml --model_path <<<đường_dẫn_file_model.ckpt>>>
```

**3. Huấn luyện mô hình đoán số Hop**
Chuyển qua module đoán Hop nằm kế bên:
```bash
cd ../hop_predict

# Train
python main.py --mode train --config ../config/hop_predict.yaml

# Eval
python main.py --mode eval --config ../config/hop_predict.yaml --model_path ./model.pth
```

---

### Bước 2: Phân loại bằng Mô hình tối ưu chống nhiễu (Classifier)

Lùi về lại thư mục gốc của khối code `with_evidence` và đi đến cụm `classifier`:
```bash
cd ../../../classifier
```

Cuối cùng, khởi động quy trình **tìm đường chạy thuật toán nén nhiễu (Phase 1 Heuristic) và kết dính lại cấu trúc câu (Phase 2 Soft-flattening)** thông qua việc ép cờ dập rác `--prune_noise`:

```bash
python baseline.py \
    --data_path <<<thư_mục_chứa_file_factkg_train_dev_test.pickle>>> \
    --kg_path <<<đường_dẫn_chi_tiết_file_dbpedia_2015_undirected_light.pickle>>> \
    --prune_noise \
    --epoch 10
```

> **Lưu ý đặc biệt:** Luôn nhớ thay thế các đoạn chữ nằm bọc trong dấu `<<<...>>>` thành **Đường dẫn thư mục thực tế** (Absolute Path / Relative Path chuẩn) trên máy bạn trước khi dập Enter.
