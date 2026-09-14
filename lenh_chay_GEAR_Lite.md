# Lệnh chạy GEAR-Lite FactKG

File này dùng để chạy lại pipeline trên máy khác cho cấu hình:

- Relation retrieval: top 3 relation.
- Hop retrieval: dự đoán hop trong khoảng 1/2/3 hop.
- Classifier: E0 Concat, E1 Pair + Mean, E2 Pair + Attention/Gear-Lite.

Lưu ý: trong code hiện tại, "3 hop" nghĩa là hop predictor có thể dự đoán tối đa 3 hop. Code không ép mọi claim đều đúng 3-hop.

## 0. Chuẩn bị path

Thay các biến sau bằng path thật trên máy chạy:

```bash
DATA_DIR=/path/to/factkg_data
KG_PATH=/path/to/dbpedia_2015_undirected_light.pickle
```

`DATA_DIR` cần có:

```text
factkg_train.pickle
factkg_dev.pickle
factkg_test.pickle
```

Nên chạy từ root repo:

```bash
cd /path/to/FactKG
pip install -r requirements.txt
```

## 1. Preprocess data cho retriever

```bash
cd with_evidence/retrieve/data
python data_preprocess.py --data_directory_path "$DATA_DIR" --output_directory_path ../model/
```

Sau bước này cần có:

```text
with_evidence/retrieve/model/train.json
with_evidence/retrieve/model/dev.json
with_evidence/retrieve/model/test.json
with_evidence/retrieve/model/total_data.pkl
```

## 2. Train/eval relation predictor top3

Train:

```bash
cd ../model/relation_predict
python main.py --mode train --config ../config/relation_predict_top3.yaml
```

Sau khi train, tìm checkpoint `.ckpt`. Ví dụ:

```bash
find . -name "*.ckpt"
```

Eval để sinh top3 relation cho test:

```bash
python main.py --mode eval --config ../config/relation_predict_top3.yaml --model_path <RELATION_CKPT>
```

Sau bước này cần có:

```text
with_evidence/retrieve/model/relation_predict/test_relations_top3.json
```

Nếu máy đã có checkpoint relation predictor rồi thì có thể bỏ qua train và chỉ chạy eval.

## 3. Train/eval hop predictor

Train:

```bash
cd ../hop_predict
python main.py --mode train --config ../config/hop_predict.yaml
```

Eval để sinh hop prediction:

```bash
python main.py --mode eval --config ../config/hop_predict.yaml --model_path ./model.pth
```

Sau bước này cần có:

```text
with_evidence/retrieve/model/hop_predict/predictions_hop.json
```

Hop predictor hiện có `num_labels: 3`, nên output là hop 1/2/3.

## 4. Sinh candidate path top3 cho classifier

```bash
cd ../../classifier
python baseline.py --data_path "$DATA_DIR" --kg_path "$KG_PATH" --n_candid 3 --prepare_only
```

Sau bước này cần có:

```text
with_evidence/classifier/train_candid_paths.bin
with_evidence/classifier/dev_candid_paths.bin
with_evidence/classifier/test_candid_paths_top3.bin
```

Chỉ cần prepare một lần cho cùng candidate set. Không cần chạy lại prepare cho từng model.

## 5. Chạy controlled baseline E0

Nếu đã có điểm baseline cũ thì có thể bỏ qua. Tuy nhiên, để so sánh công bằng với E1/E2, nên chạy lại E0 cùng `--max_paths 32`.

```bash
python baseline.py --data_path "$DATA_DIR" --model_cls cat --n_candid 3 --max_paths 32 --batch_size 32 --epoch 10 --seed 42 --skip_prepare_input
```

## 6. Chạy E1 Pair + Mean

```bash
python baseline.py --data_path "$DATA_DIR" --model_cls mean --n_candid 3 --max_paths 32 --pair_batch_size 1 --pair_max_length 128 --epoch 10 --seed 42 --skip_prepare_input
```

Ý nghĩa:

- Mỗi claim lấy tối đa 32 candidate path.
- Mỗi Claim-Path được encode riêng qua BERT.
- Các path vector được lấy trung bình có mask.

## 7. Chạy E2 Pair + Attention/Gear-Lite

```bash
python baseline.py --data_path "$DATA_DIR" --model_cls gearlite --n_candid 3 --max_paths 32 --pair_batch_size 1 --pair_max_length 128 --epoch 10 --seed 42 --skip_prepare_input
```

Ý nghĩa:

- Mỗi Claim-Path được encode riêng qua BERT.
- Attention scorer học trọng số cho từng path.
- Sau đó weighted sum các path vector rồi dự đoán True/False.

### 7.1. Chạy GEARLite v3: Claim riêng + Claim--Path Attention

`gearlite_v3` là ablation của `gearlite_v2`. Mỗi claim được encode riêng để tạo
vector `c`, nhưng attention vẫn chấm từng path bằng cả claim và path:

```text
c = BERT([CLS] Claim [SEP])
h_i = BERT([CLS] Claim [SEP] Path_i [SEP])
score_i = MLP([c || h_i])
```

Nếu candidate R3 đã được tạo sẵn, **không chạy lại Graph Retriever**. Dùng đúng
ba artifact R3 đó và train classifier mới từ đầu:

```bash
ART_ROOT=/path/to/artifacts/faico_lite_top5

python baseline.py \
  --data_path "$DATA_DIR" \
  --model_cls gearlite_v3 \
  --n_candid 5 \
  --skip_prepare_input \
  --train_candid_path "$ART_ROOT/r3/train_candid_paths_r3.bin" \
  --dev_candid_path "$ART_ROOT/r3/dev_candid_paths_r3.bin" \
  --test_candid_path "$ART_ROOT/r3/test_candid_paths_top5_r3.bin" \
  --max_paths 32 \
  --pair_batch_size 1 \
  --pair_max_length 128 \
  --epoch 10 \
  --lr 5e-5 \
  --seed 42 \
  --run_name r3_claim_separate \
  --output_dir "$ART_ROOT/r3/predictions_claim_separate"
```

Lệnh này train checkpoint mới của `gearlite_v3` từ BERT pretrained. Không dùng
checkpoint `gearlite_v2` để tiếp tục train hoặc test V3: tuy hai scorer hiện có
cùng kích thước tensor, chúng thực hiện cách tạo claim condition khác nhau và
sẽ làm hỏng ablation. Code cũng chặn nạp nhầm checkpoint có `model_cls` khác.
Giữ nguyên R3, `K=32`, seed và hyperparameter để chênh lệch điểm phản ánh cách
tạo vector claim độc lập.

### 7.2. Chạy GEARLite v4: Claim riêng + tóm tắt candidate set

`gearlite_v4` là mô hình lai giữa v2 và v3. Nó vẫn encode Claim riêng để giữ
tín hiệu ngữ nghĩa/phủ định của v3, nhưng đưa thêm trung bình các path hợp lệ
vào attention như ngữ cảnh toàn candidate set của v2:

```text
h_i     = BERT([CLS] Claim [SEP] Path_i [SEP])
c_claim = BERT([CLS] Claim [SEP])
c_set   = mean(h_i của các path không padding)
score_i = MLP([c_claim || c_set || h_i])
```

Lệnh dưới đây dùng đúng R3 Full top-5 và hyperparameter của lượt v2/v3 đang
so sánh. Chỉ train lại classifier; không chạy lại R3 hay graph retrieval.

```bash
ART_ROOT=/path/to/artifacts/faico_lite_top5

python baseline.py \
  --data_path "$DATA_DIR" \
  --model_cls gearlite_v4 \
  --n_candid 5 \
  --skip_prepare_input \
  --train_candid_path "$ART_ROOT/r3_full/train_candid_paths_r3_full.bin" \
  --dev_candid_path "$ART_ROOT/r3_full/dev_candid_paths_r3_full.bin" \
  --test_candid_path "$ART_ROOT/r3_full/test_candid_paths_top5_r3_full.bin" \
  --max_paths 32 \
  --pair_batch_size 2 \
  --pair_max_length 128 \
  --gradient_accumulation_steps 16 \
  --epoch 5 \
  --lr 5e-5 \
  --seed 42 \
  --amp \
  --run_name r3_full_v4_hybrid_top5 \
  --output_dir "$ART_ROOT/r3_full/predictions_hybrid"
```

Không nạp checkpoint v2/v3 vào v4: tầng scorer của v4 có input `3H` thay vì
`2H`, nên v4 luôn phải train checkpoint mới từ BERT pretrained.

## 8. Chạy nhiều seed nếu cần

Ví dụ chạy 3 seed:

```bash
python baseline.py --data_path "$DATA_DIR" --model_cls mean --n_candid 3 --max_paths 32 --pair_batch_size 1 --pair_max_length 128 --epoch 10 --seed 42 --skip_prepare_input
python baseline.py --data_path "$DATA_DIR" --model_cls mean --n_candid 3 --max_paths 32 --pair_batch_size 1 --pair_max_length 128 --epoch 10 --seed 43 --skip_prepare_input
python baseline.py --data_path "$DATA_DIR" --model_cls mean --n_candid 3 --max_paths 32 --pair_batch_size 1 --pair_max_length 128 --epoch 10 --seed 44 --skip_prepare_input

python baseline.py --data_path "$DATA_DIR" --model_cls gearlite --n_candid 3 --max_paths 32 --pair_batch_size 1 --pair_max_length 128 --epoch 10 --seed 42 --skip_prepare_input
python baseline.py --data_path "$DATA_DIR" --model_cls gearlite --n_candid 3 --max_paths 32 --pair_batch_size 1 --pair_max_length 128 --epoch 10 --seed 43 --skip_prepare_input
python baseline.py --data_path "$DATA_DIR" --model_cls gearlite --n_candid 3 --max_paths 32 --pair_batch_size 1 --pair_max_length 128 --epoch 10 --seed 44 --skip_prepare_input
```

Output prediction có dạng:

```text
valid_pred_mean_seed42.bin
test_pred_mean_seed42.bin
valid_pred_gearlite_seed42.bin
test_pred_gearlite_seed42.bin
```

## 9. Nếu chạy bằng PowerShell

PowerShell không dùng cú pháp `DATA_DIR=...` giống bash. Dùng:

```powershell
$env:DATA_DIR="C:\path\to\factkg_data"
$env:KG_PATH="C:\path\to\dbpedia_2015_undirected_light.pickle"
```

Ví dụ chạy E2:

```powershell
cd C:\path\to\FactKG\with_evidence\classifier
python baseline.py --data_path $env:DATA_DIR --model_cls gearlite --n_candid 3 --max_paths 32 --pair_batch_size 1 --pair_max_length 128 --epoch 10 --seed 42 --skip_prepare_input
```

## 10. Prompt mẫu để nhờ AI/người khác chạy

Copy prompt này cho người hoặc AI agent ở máy khác:

```text
Bạn đang ở repo FactKG. Hãy đọc file lenh_chay_GEAR_Lite.md và chạy pipeline GEAR-Lite cho cấu hình top 3 relation, hop predictor tối đa 3 hop.

Mục tiêu:
- Không sửa code nếu không gặp lỗi bắt buộc.
- Kiểm tra trước khi chạy xem DATA_DIR có factkg_train/dev/test.pickle không.
- Kiểm tra KG_PATH có tồn tại không.
- Chạy retriever preprocess một lần.
- Chạy/eval relation predictor top3 để sinh test_relations_top3.json.
- Chạy/eval hop predictor để sinh predictions_hop.json.
- Chạy baseline.py --prepare_only một lần để sinh train/dev/test candidate path.
- Sau đó chạy E1 mean và E2 gearlite với cùng candidate set:
  --n_candid 3 --max_paths 32 --pair_batch_size 1 --pair_max_length 128 --epoch 10 --seed 42 --skip_prepare_input
- Nếu cần so sánh công bằng, chạy thêm E0 cat với --max_paths 32.
- Báo cáo lại Accuracy, Macro-F1, và kết quả theo 5 reasoning type: one-hop, multi-hop, conjunction, existence, negation.

Không được rerun prepare_input cho từng model/seed. Nếu thiếu checkpoint relation hoặc hop thì báo rõ cần train trước, không tự bịa đường dẫn checkpoint.
```

## 11. Checklist nhanh

Trước khi chạy classifier E1/E2, kiểm tra đủ 3 file:

```text
with_evidence/retrieve/model/relation_predict/test_relations_top3.json
with_evidence/retrieve/model/hop_predict/predictions_hop.json
with_evidence/classifier/test_candid_paths_top3.bin
```

Nếu thiếu `test_candid_paths_top3.bin`, chạy lại bước prepare candidate path.

Nếu thiếu `test_relations_top3.json`, chạy eval relation predictor top3.

Nếu thiếu `predictions_hop.json`, chạy eval hop predictor.
