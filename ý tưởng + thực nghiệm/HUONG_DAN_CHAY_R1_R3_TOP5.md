# Chạy Faico-Lite R1–R3 với relation top-5

Tài liệu này là bản hướng dẫn chạy ngắn cho thí nghiệm hiện tại:

```text
relation predictor và hop predictor giữ nguyên
→ Faico-Lite sinh candidate path mới
→ GEARLite E2 phân loại True / False
```

Mục tiêu là chỉ thay tầng **sinh candidate path**, không thay predictor và
không thay kiến trúc E2. `top-5` ở đây là năm **relation label** được relation
predictor dự đoán, không phải năm path cuối cùng.

## 1. Những gì có thể dùng lại

Nếu lần chạy trước dùng **cùng** dataset, KG và checkpoint predictor, hãy dùng
lại hai file sau; không train lại và cũng không cần chạy lại phần `retrieve`:

```text
with_evidence/retrieve/model/relation_predict/test_relations_top5.json
with_evidence/retrieve/model/hop_predict/predictions_hop.json
```

Hai file này lần lượt chứa top-5 relation và hop dự đoán cho toàn bộ claim
test. Chúng là đầu vào cố định cho cả R1, R2 và R3. Giữ chúng cố định là cần
thiết để khác biệt điểm số chỉ đến từ cách sinh path.

Chỉ chạy lại `retrieve` khi một trong hai JSON bị thiếu, dataset/KG đã đổi,
hoặc bạn chủ động dùng checkpoint predictor khác. Có checkpoint nhưng thiếu
JSON thì chỉ cần chạy **eval**, không cần train lại predictor:

```bash
export REL_CKPT=/duong/dan/relation_predictor.ckpt
export HOP_CKPT=/duong/dan/hop_predictor.pth

cd "$REPO/with_evidence/retrieve/model/relation_predict"
python main.py \
  --mode eval \
  --config ../config/relation_predict_top5.yaml \
  --model_path "$REL_CKPT"

cd "$REPO/with_evidence/retrieve/model/hop_predict"
python main.py \
  --mode eval \
  --config ../config/hop_predict.yaml \
  --model_path "$HOP_CKPT"
```

## 2. Chuẩn bị một lần trên máy SSH

Thay các đường dẫn bên dưới bằng đường dẫn thật trên máy SSH.

```bash
export REPO=/duong/dan/FactKG
export DATA_DIR=/duong/dan/factkg_data
export KG_PATH=/duong/dan/dbpedia_2015_undirected_light.pickle
export ART_ROOT="$REPO/artifacts/faico_lite_top5"

export REL_JSON="$REPO/with_evidence/retrieve/model/relation_predict/test_relations_top5.json"
export HOP_JSON="$REPO/with_evidence/retrieve/model/hop_predict/predictions_hop.json"

cd "$REPO"
test -f "$REL_JSON"
test -f "$HOP_JSON"
```

Hai lệnh `test -f` phải trả về thành công, không in lỗi. Dataset cần chứa:

```text
factkg_train.pickle
factkg_dev.pickle
factkg_test.pickle
```

Kiểm tra nhanh code trước khi chạy dữ liệu lớn:

```bash
cd "$REPO"
python -m unittest with_evidence/classifier/test_faico_lite_retrieval.py -v
```

Không xóa artifact legacy, checkpoint hoặc prediction cũ. Mọi output mới nằm
trong `$ART_ROOT`. Nếu một thư mục R đã tồn tại, đổi `--run_name`/`--output_dir`
hoặc chỉ dùng `--overwrite` khi thật sự muốn ghi đè lần chạy đó.

## 3. Quy tắc so sánh

Mọi run dưới đây giữ cố định:

```text
top-5 relation JSON, hop JSON, KG,
model GEARLite E2, max_paths=32, pair_max_length=128,
seed=42, epoch=10, learning rate=5e-5.
```

R1 là run duy nhất train E2. R2 và R3 chạy lại `baseline.py`, nhưng chỉ nạp
checkpoint tốt nhất của R1 để test toàn bộ test set với candidate test mới.
Không train E2 lại ở R2/R3.

## 4. R1 — Duyệt đầy đủ, đúng hop dự đoán

R1 dùng đúng `H` do hop predictor dự đoán và `k=1` (một relation không lặp
trong relation chain). Khác baseline cũ ở chỗ giữ mọi tail/path hợp lệ theo thứ
tự cố định, không chọn tail ngẫu nhiên và không gộp hai serialized path khác
nhau chỉ vì cùng endpoint.

### 4.1. Sinh candidate R1

```bash
cd "$REPO/with_evidence/classifier"

python build_faico_lite_candidates.py \
  --data_path "$DATA_DIR" \
  --kg_path "$KG_PATH" \
  --n_candid 5 \
  --output_dir "$ART_ROOT/r1" \
  --run_name r1 \
  --relation_budget 1 \
  --report_max_paths 32 \
  --relation_prediction_path "$REL_JSON" \
  --hop_prediction_path "$HOP_JSON"
```

### 4.2. Train E2, chọn dev tốt nhất và test R1

```bash
mkdir -p "$ART_ROOT/r1/predictions"

CUDA_VISIBLE_DEVICES=0 python baseline.py \
  --data_path "$DATA_DIR" \
  --model_cls gearlite \
  --n_candid 5 \
  --skip_prepare_input \
  --train_candid_path "$ART_ROOT/r1/train_candid_paths_r1.bin" \
  --dev_candid_path "$ART_ROOT/r1/dev_candid_paths_r1.bin" \
  --test_candid_path "$ART_ROOT/r1/test_candid_paths_top5_r1.bin" \
  --max_paths 32 \
  --pair_max_length 128 \
  --pair_batch_size 1 \
  --epoch 10 \
  --lr 5e-5 \
  --seed 42 \
  --run_name r1_top5 \
  --output_dir "$ART_ROOT/r1/predictions"
```

Lệnh này tự train, chọn checkpoint có dev tốt nhất, sau đó test R1. Nó tạo:

```bash
export R1_CKPT="$ART_ROOT/r1/predictions/best_model_gearlite_r1_top5_seed42.pth"
test -f "$R1_CKPT"
```

Ghi lại `Total Test Acc`, `Total Test Macro-F1` và Acc/F1 của năm reasoning
type, đặc biệt là `multi-hop`.

## 5. R2 — Thêm path ngắn hơn hop dự đoán

R2 giữ `k=1`, nhưng nếu hop predictor đoán `H=3` thì sinh relation chain dài
1, 2 và 3 cạnh thay vì chỉ dài 3 cạnh. Mục đích là kiểm tra predictor hop có
đoán dài hơn proof thật hay không.

### 5.1. Sinh candidate R2

```bash
cd "$REPO/with_evidence/classifier"

python build_faico_lite_candidates.py \
  --data_path "$DATA_DIR" \
  --kg_path "$KG_PATH" \
  --n_candid 5 \
  --output_dir "$ART_ROOT/r2" \
  --run_name r2 \
  --include_shorter_paths \
  --relation_budget 1 \
  --report_max_paths 32 \
  --relation_prediction_path "$REL_JSON" \
  --hop_prediction_path "$HOP_JSON"
```

Script vẫn ghi candidate train/dev R2 để có manifest/report đầy đủ, nhưng
R2 không train lại. Trong lệnh kế tiếp, chỉ file candidate **test R2** làm
thay đổi đầu vào thực tế của E2; train/dev vẫn dùng artifact R1.

### 5.2. Nạp checkpoint R1 và test toàn bộ test set với R2

```bash
mkdir -p "$ART_ROOT/r2/predictions"

CUDA_VISIBLE_DEVICES=0 python baseline.py \
  --data_path "$DATA_DIR" \
  --model_cls gearlite \
  --n_candid 5 \
  --skip_prepare_input \
  --train_candid_path "$ART_ROOT/r1/train_candid_paths_r1.bin" \
  --dev_candid_path "$ART_ROOT/r1/dev_candid_paths_r1.bin" \
  --test_candid_path "$ART_ROOT/r2/test_candid_paths_top5_r2.bin" \
  --max_paths 32 \
  --pair_max_length 128 \
  --pair_batch_size 1 \
  --epoch 10 \
  --lr 5e-5 \
  --seed 42 \
  --test_only \
  --checkpoint_path "$R1_CKPT" \
  --run_name r2_top5 \
  --output_dir "$ART_ROOT/r2/predictions"
```

## 6. R3 — Cho phép relation lặp tối đa hai lần

R3 trong hướng dẫn này là cấu hình tích lũy: R2 + `k=2`. Nghĩa là vừa cho
path ngắn hơn `H`, vừa cho phép chain như `r1 → r2 → r1`. So sánh R3 với R2
để thấy tác động thêm của việc relation được lặp.

```bash
cd "$REPO/with_evidence/classifier"

python build_faico_lite_candidates.py \
  --data_path "$DATA_DIR" \
  --kg_path "$KG_PATH" \
  --n_candid 5 \
  --output_dir "$ART_ROOT/r3" \
  --run_name r3 \
  --include_shorter_paths \
  --relation_budget 2 \
  --report_max_paths 32 \
  --relation_prediction_path "$REL_JSON" \
  --hop_prediction_path "$HOP_JSON"

mkdir -p "$ART_ROOT/r3/predictions"

CUDA_VISIBLE_DEVICES=0 python baseline.py \
  --data_path "$DATA_DIR" \
  --model_cls gearlite \
  --n_candid 5 \
  --skip_prepare_input \
  --train_candid_path "$ART_ROOT/r1/train_candid_paths_r1.bin" \
  --dev_candid_path "$ART_ROOT/r1/dev_candid_paths_r1.bin" \
  --test_candid_path "$ART_ROOT/r3/test_candid_paths_top5_r3.bin" \
  --max_paths 32 \
  --pair_max_length 128 \
  --pair_batch_size 1 \
  --epoch 10 \
  --lr 5e-5 \
  --seed 42 \
  --test_only \
  --checkpoint_path "$R1_CKPT" \
  --run_name r3_top5_k2 \
  --output_dir "$ART_ROOT/r3/predictions"
```

Nếu muốn cô lập riêng ảnh hưởng `k=2` so với R1, hãy bỏ dòng
`--include_shorter_paths` trong lệnh sinh candidate R3 và đặt tên run là
`r3_k2_only`. Không chạy cả hai biến thể nếu chưa cần, vì số candidate path
tăng nhanh.

## 7. Đọc kết quả đúng cách

| So sánh | Câu hỏi được trả lời |
|---|---|
| R1 với baseline E2 cũ | Việc traversal cũ có làm mất path hợp lệ không? |
| R2 với R1 | Hop predictor có thường đoán dài hơn proof thật không? |
| R3 với R2 | Một relation lặp lại có giúp Multi-hop không? |

Mỗi lần chạy, xem thêm `retrieval_report_*.json`:

```text
total_paths                    số path đã sinh
claims_exceeding_report_limit  số claim có hơn 32 path
paths_visible_to_model_at_report_limit  số path E2 tối đa có thể thấy
```

Nếu số path tăng mà Multi-hop không tăng, chưa thể kết luận retriever vô ích:
proof có thể nằm sau path thứ 32 hoặc E2 chưa đặt attention đúng. Nếu path
đúng không hề xuất hiện, bottleneck vẫn nằm ở relation predictor, hop
predictor hoặc KG.

## 8. Không làm trong R1–R3

Không train lại relation predictor/hop predictor, không dùng LLM, không thay
checkpoint E2 ở R2/R3, và không xóa artifact legacy. Những thay đổi đó sẽ tạo
một thí nghiệm khác và làm khó xác định cải thiện đến từ đâu.
