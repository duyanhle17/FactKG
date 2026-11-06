# Hướng dẫn chạy Faico-Lite cho GEARLite trên máy SSH/GPU

## 1. Mục tiêu của phần code này

Phần này không thay BERT, attention hay verifier của GEARLite. Nó chỉ thay
**cách sinh path ứng viên trước khi E2 đọc path**.

```text
Claim
→ relation predictor và hop predictor hiện có
→ bộ sinh path Faico-Lite mới
→ các path ứng viên
→ GEARLite E2
→ True / False
```

Mục tiêu lấy từ Faico là: trong phạm vi relation và hop đã dự đoán, không để
heuristic traversal làm mất một đường chứng minh hợp lệ trước khi attention có
cơ hội chọn nó.

Phần code này **không** cài token-trie, LLM hay answer generator của Faico.
Những thành phần đó thuộc một bài toán khác và không cần cho thí nghiệm này.

## 2. Các file đã thêm hoặc sửa

| File | Thay đổi |
|---|---|
| `with_evidence/classifier/faico_lite_retrieval.py` | Bộ duyệt KG có hướng, xác định, giữ full serialized path; sinh relation sequence theo ngân sách `k`; có audit R4. |
| `with_evidence/classifier/preprocess.py` | Giữ nguyên class `KG` legacy; thêm chế độ `faico_lite`, ghi candidate vào thư mục/tên mới, report và manifest. |
| `with_evidence/classifier/build_faico_lite_candidates.py` | Lệnh riêng để sinh candidate cho R1–R4. |
| `with_evidence/classifier/baseline.py` | Thêm `--run_name`, `--output_dir`, lưu checkpoint dev tốt nhất và `--test_only --checkpoint_path` để kiểm tra R2/R3 bằng đúng model của R1. |
| `with_evidence/classifier/test_faico_lite_retrieval.py` | Kiểm tra KG nhỏ: giữ mọi tail, giữ path cùng endpoint, `k=1`, `k=2`, R2 và artifact riêng. |

Candidate của mỗi lần chạy được lưu riêng, ví dụ:

```text
artifacts/faico_lite/r1/
├── train_candid_paths_r1.bin
├── dev_candid_paths_r1.bin
├── test_candid_paths_top5_r1.bin
├── retrieval_report_r1.json
└── manifest_r1.json
```

Không có file legacy nào bị ghi đè bởi lệnh Faico-Lite.

Để tránh ghi đè nhầm một lần chạy trước, bộ sinh candidate sẽ dừng nếu thư mục
đích đã có artifact cùng tên. Chỉ thêm `--overwrite` khi chủ động muốn thay thế
toàn bộ artifact của đúng lần chạy đó.

## 3. Ý nghĩa từng lần chạy

Các lần chạy dưới đây đều giữ nguyên:

```text
- relation predictor và hop predictor;
- top-5 relation;
- BERT, attention E2 và verifier;
- max_paths = 32;
- pair_max_length = 128;
- seed, epoch và learning rate trong cùng một phép so sánh.
```

`top-5 relation` là năm **nhãn relation** có điểm dự đoán cao nhất. Nó không
phải là năm path. Từ năm relation này, KG có thể sinh rất nhiều path; E2 chỉ
đọc tối đa 32 path đầu theo thứ tự `connected`, rồi `walkable`.

### R1 — Duyệt đầy đủ và xác định

Thêm so với code cũ:

```text
- không chọn tail ngẫu nhiên ở hop cuối;
- giữ mọi tail hợp lệ;
- không gộp hai path chỉ vì cùng endpoint;
- chỉ bỏ hai path có chuỗi entity–relation–entity giống hệt nhau;
- tail được sắp xếp ổn định.
```

Vẫn giữ:

```text
- path dài đúng bằng H do hop predictor dự đoán;
- một relation không được lặp trong cùng path (k = 1).
```

Mục đích: kiểm tra heuristic traversal cũ có làm mất proof path Multi-hop hay
không.

### R2 — Cho phép path ngắn hơn số hop dự đoán

R2 = R1 + sinh path có độ dài từ `1` đến `H`.

Ví dụ hop predictor đoán `H=3`:

```text
R1: chỉ sinh path 3 cạnh.
R2: sinh path 1 cạnh, 2 cạnh và 3 cạnh.
```

Mục đích: kiểm tra hop predictor có đoán dài hơn proof thực tế hay không.

### R3 — Cho phép relation lặp tối đa hai lần

R3 lấy cấu hình tốt hơn giữa R1 và R2, rồi đổi `k` từ 1 sang 2.

```text
k = 1: r1 → r2 → r1 bị loại.
k = 2: r1 → r2 → r1 được phép.
```

Mục đích: kiểm tra proof Multi-hop có cần dùng lại một loại relation không.

`k=2` không phải mặc định bắt buộc. Nếu R3 không tốt hơn, giữ `k=1` vì ít
nhiễu và ít tốn thời gian hơn.

### R4 — Audit budget dominance của Faico

Faico dùng budget dominance để giữ subgraph nhỏ. Nhưng Faico không cần giữ mọi
serialized path, còn GEARLite lại encode từng Claim–Path riêng. Nếu bê nguyên
cơ chế Faico sang, một prefix path khác có thể bị mất dù nó là evidence hữu
ích cho BERT.

Vì vậy R4 hiện là **audit**, không phải candidate dùng để train:

```text
- code sinh artifact đầy đủ, không cắt path;
- đồng thời mô phỏng raw dominance của Faico;
- report so sánh hai tập full-path trước giới hạn 32.
```

Chỉ khi report cho thấy raw dominance không làm mất path mới được cân nhắc tối
ưu tiếp. Không train E2 trên kết quả path bị raw dominance cắt.

## 4. Những file cần có trên máy SSH

Do `.gitignore` bỏ qua `*.bin`, `*.json`, `*.pkl`, `*.pth` và `*.ckpt`, chỉ
`git clone` repo là **không đủ**. Cần copy/upload riêng:

```text
DATA_DIR/
├── factkg_train.pickle
├── factkg_dev.pickle
└── factkg_test.pickle

KG_PATH
└── dbpedia_2015_undirected_light.pickle
```

Nếu không chạy lại predictor, cần thêm hai file:

```text
with_evidence/retrieve/model/relation_predict/test_relations_top5.json
with_evidence/retrieve/model/hop_predict/predictions_hop.json
```

Hoặc có thể đặt chúng ở đâu cũng được rồi truyền đường dẫn rõ ràng bằng:

```text
--relation_prediction_path
--hop_prediction_path
```

Không xoá các candidate, checkpoint hoặc prediction cũ. Tạo thư mục
`artifacts/faico_lite/` riêng cho R1–R4.

Thư mục `Faico/` chỉ là nguồn tham khảo khi phát triển. Code Faico-Lite không
import thư mục đó, nên không cần copy Faico sang máy SSH để chạy thí nghiệm.

## 5. Chuẩn bị môi trường trên SSH

Ví dụ dưới đây dùng biến môi trường để tránh gõ lại đường dẫn. Thay các đường
dẫn bằng đường dẫn thật trên máy SSH.

```bash
export REPO=/duong/dan/FactKG
export DATA_DIR=/duong/dan/factkg_data
export KG_PATH=/duong/dan/dbpedia_2015_undirected_light.pickle
export REL_JSON=/duong/dan/test_relations_top5.json
export HOP_JSON=/duong/dan/predictions_hop.json
export ART_ROOT="$REPO/artifacts/faico_lite"

cd "$REPO"
nvidia-smi
```

Tạo môi trường Python riêng nếu máy SSH chưa có môi trường phù hợp:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Cài PyTorch đúng phiên bản CUDA của máy theo hướng dẫn chính thức của PyTorch.
Sau đó cài các thư viện còn lại:

```bash
python -m pip install -r requirements.txt
python -m pip install datasets tqdm PyYAML termcolor
```

Kiểm tra GPU trước khi chạy:

```bash
python -c "import torch; print('torch:', torch.__version__); print('cuda:', torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'KHONG_CO_GPU')"
```

Kiểm tra code retriever trước khi dùng dữ liệu lớn:

```bash
cd "$REPO"
python -m unittest with_evidence/classifier/test_faico_lite_retrieval.py -v
```

## 6. Có cần chạy lại relation predictor và hop predictor không?

Không cần chạy lại predictor khi đồng thời đúng cả bốn điều kiện:

```text
1. Dataset không đổi.
2. KG không đổi.
3. Checkpoint predictor không đổi.
4. Đã có test_relations_top5.json và predictions_hop.json đúng với dataset đó.
```

Lý do: train/dev candidate được tạo từ `Evidence` có sẵn trong dataset; chỉ
test candidate dùng output của relation predictor và hop predictor.

Vẫn phải sinh lại candidate cho cả train/dev/test vì cách duyệt graph đã đổi.

### Khi có checkpoint nhưng thiếu JSON dự đoán

Không cần train lại. Chỉ chạy `eval` để sinh JSON.

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

Hai lệnh trên ghi lần lượt:

```text
with_evidence/retrieve/model/relation_predict/test_relations_top5.json
with_evidence/retrieve/model/hop_predict/predictions_hop.json
```

Sau đó đặt lại biến:

```bash
export REL_JSON="$REPO/with_evidence/retrieve/model/relation_predict/test_relations_top5.json"
export HOP_JSON="$REPO/with_evidence/retrieve/model/hop_predict/predictions_hop.json"
```

### Khi thiếu checkpoint hoặc đổi dataset/KG

Lúc đó mới chạy lại toàn bộ predictor:

```bash
cd "$REPO/with_evidence/retrieve/data"
python data_preprocess.py \
  --data_directory_path "$DATA_DIR" \
  --output_directory_path ../model/

cd "$REPO/with_evidence/retrieve/model/relation_predict"
python main.py --mode train --config ../config/relation_predict_top5.yaml
# Sau khi train, dùng checkpoint thật được tạo ra để chạy eval như phần trên.

cd "$REPO/with_evidence/retrieve/model/hop_predict"
python main.py --mode train --config ../config/hop_predict.yaml
python main.py \
  --mode eval \
  --config ../config/hop_predict.yaml \
  --model_path ./model.pth
```

Không tự chọn checkpoint bằng tên gần đúng. Hãy ghi rõ đường dẫn checkpoint đã
kiểm tra vào biến `REL_CKPT` và `HOP_CKPT`.

## 7. Cách dùng checkpoint E2 cho đúng

R1 phải train E2 từ đầu vì R1 thay đổi traversal ở train/dev so với candidate
legacy. Sau khi chọn dev tốt nhất, `baseline.py` lưu checkpoint:

```text
best_model_gearlite_r1_top5_seed42.pth
```

FactKG hiện dùng `Evidence` gold để sinh candidate train/dev, còn top relation,
hop dự đoán, R2 và R3 chỉ tác động trực tiếp tới candidate **test**. Vì vậy để
kiểm tra sạch giả thuyết retrieval:

```text
R1: train E2 một lần với candidate R1 train/dev.
R2: dùng đúng checkpoint R1, chỉ đổi test candidate sang R2.
R3: dùng đúng checkpoint R1, chỉ đổi test candidate sang R3.
```

Cách này tránh việc điểm khác đi vì một lần train GPU khác. Script vẫn cần ba
đường dẫn candidate ở chế độ `--test_only`, nhưng train/dev path có thể dùng
artifact R1 vì chúng không được train lại.

Lệnh sinh candidate R2/R3 vẫn ghi đủ train/dev/test cùng report để dễ kiểm
tra và lưu manifest. Nhưng trong lệnh `--test_only`, chỉ test path R2/R3 được
dùng để thay đổi đầu vào của E2; train/dev path luôn trỏ về R1.

Mẫu dưới đây nhận ba đường dẫn candidate và một tên chạy:

```bash
cd "$REPO/with_evidence/classifier"

CUDA_VISIBLE_DEVICES=0 python baseline.py \
  --data_path "$DATA_DIR" \
  --model_cls gearlite \
  --n_candid 5 \
  --skip_prepare_input \
  --train_candid_path "DUONG_DAN_TRAIN_BIN" \
  --dev_candid_path "DUONG_DAN_DEV_BIN" \
  --test_candid_path "DUONG_DAN_TEST_BIN" \
  --max_paths 32 \
  --pair_max_length 128 \
  --pair_batch_size 1 \
  --epoch 10 \
  --lr 5e-5 \
  --seed 42 \
  --run_name "TEN_CHAY" \
  --output_dir "THU_MUC_PREDICTION"
```

`--run_name` và `--output_dir` là bắt buộc trong thực hành để prediction của
R1/R2/R3 không ghi đè nhau. Script lưu prediction dev tốt nhất, prediction
test và checkpoint dev tốt nhất dưới `output_dir`.

Nếu muốn train lại E2 cho từng R như một kiểm tra phụ, có thể bỏ
`--test_only --checkpoint_path`. Nhưng đó không còn là phép kiểm tra thuần về
retrieval vì train GPU có thể tạo khác biệt riêng.

## 8. Lệnh R1

### 8.1. Sinh candidate R1

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

### 8.2. Kiểm tra candidate R1 trước khi train

```bash
python inspect_candid_paths.py \
  --candid_path "$ART_ROOT/r1/test_candid_paths_top5_r1.bin" \
  --max_examples 3

python -m json.tool "$ART_ROOT/r1/retrieval_report_r1.json" | less
```

### 8.3. Train/test E2 với R1

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

Checkpoint để dùng ở R2/R3 là:

```bash
export R1_CKPT="$ART_ROOT/r1/predictions/best_model_gearlite_r1_top5_seed42.pth"
```

## 9. Lệnh R2

R2 thêm `--include_shorter_paths`.

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

## 10. Lệnh R3

Chỉ chạy R3 sau khi đã xem R1 và R2. Nếu R2 tốt hơn, dùng lệnh dưới đây. Nếu
R1 tốt hơn, bỏ dòng `--include_shorter_paths` để R3 chỉ khác R1 ở `k=2`.

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

## 11. Lệnh R4

R4 chỉ audit raw budget dominance của Faico. Nó **không** tạo artifact đã bị
cắt dominance để train E2.

Nếu R3 là cấu hình tốt nhất, chạy:

```bash
cd "$REPO/with_evidence/classifier"

python build_faico_lite_candidates.py \
  --data_path "$DATA_DIR" \
  --kg_path "$KG_PATH" \
  --n_candid 5 \
  --output_dir "$ART_ROOT/r4_audit" \
  --run_name r4_audit \
  --include_shorter_paths \
  --relation_budget 2 \
  --dominance_audit \
  --report_max_paths 32 \
  --relation_prediction_path "$REL_JSON" \
  --hop_prediction_path "$HOP_JSON"

python -m json.tool "$ART_ROOT/r4_audit/retrieval_report_r4_audit.json" | less
```

Trong phần `splits.test`, so sánh:

```text
claims
r4_audit_candidate_set_equal
r4_audit_paths_removed_by_raw_dominance
r4_audit_full_milliseconds
r4_audit_pruned_milliseconds
r4_audit_pruned_states
r4_audit_pruned_expanded_states
elapsed_seconds
```

R4 chỉ được coi là an toàn nếu:

```text
r4_audit_candidate_set_equal = claims
r4_audit_paths_removed_by_raw_dominance = 0
```

Trong đa số trường hợp raw dominance của Faico có thể không đạt điều kiện này;
đó là kết quả có ích, vì nó chứng minh không thể dùng nguyên cơ chế subgraph
của Faico cho GEARLite path-level. Khi đó dừng ở R3 và không train R4.

## 12. Sau khi chọn cấu hình tốt nhất

Chạy lại với nhiều seed, ví dụ 42, 43, 44. Nếu R2 là cấu hình tốt nhất, mỗi
seed cần train R1 trước, rồi dùng checkpoint R1 đó để test R2:

```bash
for SEED in 42 43 44; do
  mkdir -p "$ART_ROOT/r1/predictions_seed${SEED}"
  CUDA_VISIBLE_DEVICES=0 python "$REPO/with_evidence/classifier/baseline.py" \
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
    --seed "$SEED" \
    --run_name "r1_top5" \
    --output_dir "$ART_ROOT/r1/predictions_seed${SEED}"

  mkdir -p "$ART_ROOT/r2/predictions_seed${SEED}"
  CUDA_VISIBLE_DEVICES=0 python "$REPO/with_evidence/classifier/baseline.py" \
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
    --seed "$SEED" \
    --test_only \
    --checkpoint_path "$ART_ROOT/r1/predictions_seed${SEED}/best_model_gearlite_r1_top5_seed${SEED}.pth" \
    --run_name "r2_top5" \
    --output_dir "$ART_ROOT/r2/predictions_seed${SEED}"
done
```

Sau đó báo cáo trung bình và độ lệch chuẩn của Overall Accuracy, Overall
Macro-F1, Multi-hop Accuracy và Multi-hop Macro-F1.

## 13. Cách diễn giải kết quả

| Kết quả | Kết luận tiếp theo |
|---|---|
| R1 tốt hơn kết quả E2 cũ | Heuristic traversal cũ có thể làm mất proof path; giữ R1. |
| R2 tốt hơn R1 | Hop predictor có thể dự đoán dài hơn proof thật; dùng path dài 1 đến H. |
| R3 tốt hơn cấu hình trước đó | Một số proof cần relation lặp; `k=2` có giá trị. |
| Số path tăng nhưng Multi-hop không tăng | Path tốt có thể đã vào tập nhưng E2 chưa chọn đúng; khi đó mới xem structural attention. |
| Proof thô vẫn không có | Bottleneck là relation predictor, hop predictor hoặc KG; attention không tự tạo relation bị thiếu. |
| Nhiều path nằm sau vị trí 32 | Cần xem bước xếp hạng candidate hoặc tăng `max_paths`; không tăng mù quáng. |

## 14. Lưu ý cuối

1. Không dùng kết quả E2 cũ làm kết luận nhân quả tuyệt đối nếu dataset, KG,
   predictor JSON, top-N hoặc seed khác với lần chạy mới. Nó chỉ là mốc tham
   chiếu khi không chạy lại baseline.
2. Traversal Faico-Lite được sắp xếp xác định, nhưng việc train GPU vẫn có thể
   không hoàn toàn giống bit-for-bit giữa các máy.
3. `top-5 relation` và `max_paths=32` là hai giới hạn khác nhau.
4. Train R1 một lần cho mỗi seed; dùng checkpoint R1 để test R2/R3. R4 chỉ
   audit, không train artifact raw-dominance.
5. Không cần xoá file cũ. Việc tách thư mục artifact là cách an toàn để có thể
   quay lại baseline bất kỳ lúc nào.
