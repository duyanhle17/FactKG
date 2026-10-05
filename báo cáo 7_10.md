# Báo cáo 7/10 — kiểm tra top-10 relation cho R3 + GEARLite V4

## Đúc kết từ các kiểm tra vừa qua

- V4 + R3 top-5, `K=32` đạt **84,03% Conjunction Accuracy** trên test; mốc E0 top-5 là **85,08%**. Hai hệ thống khác cả cách lấy path lẫn classifier, nên chưa thể quy chênh lệch 1,05 điểm phần trăm cho riêng bước nào.
- Trên **1.970 claim dev nhãn True có tag `multi claim` và Evidence**, tăng relation từ top-5 lên top-10 làm số claim có *ít nhất một chain vàng* nằm trong relation dự đoán tăng **1.831 → 1.860** (+29). Số claim có *ít nhất một chain cho mỗi khóa Evidence* tăng **240 → 502** (+262). Đây chỉ là **độ phủ relation theo annotation**, chưa phải proof/path recall: một khóa Evidence không nhất thiết là một vế bắt buộc của claim. Nhóm 1.970 claim theo tag cũng không hoàn toàn trùng nhóm Conjunction độc quyền dùng để tính Accuracy.
- Trên **5 claim True được chọn có chủ đích**, dùng cùng checkpoint V4 và `K=32`, top-10 sửa **2 câu False → True**, 3 câu còn lại giữ True. R3 đã thêm một số path `connected` liên quan đến relation mới. Trên **10 claim False đối chứng được chọn**, cả top-5 lẫn top-10 đều dự đoán False; không có câu nào bị lật sai sang True. Một số đối chứng chỉ trùng entity/giá trị hoặc họ relation, không phải cặp claim chỉ khác đúng một vế.
- Nhiều artifact đều chạm **32 path**. `32 → 32` chỉ là số lượng: top-10 có thể thay path cũ bằng path mới, không có nghĩa hai tập path giống nhau.

**Nhận định:** top-10 **có tín hiệu tốt hơn ở độ phủ relation và trên mẫu True nhỏ**, chưa đủ chứng minh Accuracy toàn test tăng hoặc giải thích hoàn toàn lỗi Conjunction. Cần chạy **toàn test với cùng checkpoint V4, cùng `K=32`** để chỉ cô lập tác động của top-10. Sau đó mới thử `K=64` riêng; đổi cả top-k relation và K cùng lúc sẽ khó biết nguyên nhân thay đổi điểm.

## Flow chuẩn và điều cần chạy lần này

Flow đầy đủ khi bắt đầu từ đầu là: **data preprocess → train/eval relation predictor → train/eval hop predictor → R3 dựng candidate → train/test V4**. R3 **không phải model được train**. Trong code hiện tại, R3 dùng chuỗi relation trong `Evidence` vàng cho candidate **train/dev**, nhưng dùng relation/hop **dự đoán** cho candidate **test**. `top_k=10` chỉ đổi số relation được xuất ở bước `eval`; không làm V4 học thêm path trong lần train cũ.

Lần thử này **tái sử dụng checkpoint relation, hop và V4 đã có**: chỉ cần xuất JSON top-10/hop đúng *tập test*, dựng candidate R3 top-10 cho test, rồi dùng `--test_only`. Không lấy các JSON **dev** trong `artifacts/conjunction_step_b_...` làm đầu vào test gốc.

## Lệnh chuẩn bị và chạy top-10 trên toàn test (`K=32`)

Chạy trên máy GPU Linux, từ repo đã cập nhật code. Khi dán lệnh, dấu `\` phải đứng cuối dòng, không có khoảng trắng phía sau.

### 1. Gán đường dẫn, kiểm tra dữ liệu preprocess và checkpoint

```bash
export REPO=/home/namnx/duyanh/FactKG
export PYTHON=/home/namnx/duyanh/.conda/factkg/bin/python
export DATA_DIR=/home/namnx/duyanh/Data
export MODEL_DIR="$REPO/with_evidence/retrieve/model"
export R3_DIR="$REPO/artifacts/faico_lite_top5/r3_full"
export RUN="$REPO/artifacts/r3_top10_fulltest_k32_0710"
export REL_CKPT="$MODEL_DIR/relation_predict/lightning_logs/version_1/checkpoints/epoch=9-step=17350.ckpt"
export REL10="$MODEL_DIR/relation_predict/test_relations_top10.json"
export HOP_CKPT="$MODEL_DIR/hop_predict/model.pth"
export HOP_JSON="$MODEL_DIR/hop_predict/predictions_hop.json"
export KG_PATH="$DATA_DIR/dbpedia_2015_undirected_light.pickle"
export V4_CKPT="$R3_DIR/predictions_hybrid_rerun/best_model_gearlite_v4_r3_full_v4_hybrid_rerun_seed42.pth"
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

ls -lh "$DATA_DIR/factkg_test.pickle" "$KG_PATH" "$REL_CKPT" "$HOP_CKPT" "$V4_CKPT"
ls -lh "$MODEL_DIR/total_data.pkl" "$MODEL_DIR/train.json" "$MODEL_DIR/dev.json" "$MODEL_DIR/test.json" "$MODEL_DIR/relation_predict/relations_for_final.pickle"
```

Nếu **thiếu** `total_data.pkl`/JSON preprocess, mới chạy lệnh sau; nếu đã có từ cùng bộ dữ liệu thì **bỏ qua**:

```bash
cd "$REPO/with_evidence/retrieve/data"
"$PYTHON" data_preprocess.py \
  --data_directory_path "$DATA_DIR" \
  --output_directory_path "$MODEL_DIR"
```

### 2. Xuất top-10 relation và hop từ checkpoint cũ

Nếu `test_relations_top10.json` chưa có, chạy **eval**, không chạy `train`:

```bash
if [ ! -f "$REL10" ]; then
  cd "$MODEL_DIR/relation_predict"
  "$PYTHON" main.py \
    --mode eval \
    --config ../config/relation_predict_top10.yaml \
    --model_path "$REL_CKPT"
fi
```

Nếu `predictions_hop.json` test chưa có:

```bash
if [ ! -f "$HOP_JSON" ]; then
  cd "$MODEL_DIR/hop_predict"
  "$PYTHON" main.py \
    --mode eval \
    --config ../config/hop_predict.yaml \
    --model_path "$HOP_CKPT"
fi
```

**Bắt buộc kiểm tra** JSON là của test gốc, không phải bản dev chẩn đoán. Lệnh phải in `Khớp test: True` và `Đủ 10 relation: True`:

```bash
"$PYTHON" -c 'import json,pickle,sys; d=pickle.load(open(sys.argv[1],"rb")); r=json.load(open(sys.argv[2])); h=json.load(open(sys.argv[3])); ok=set(d)==set(r["claims"].values())==set(h["claims"].values()); ten=all(len(v)==10 for v in r["output"].values()); print("Số claim:",len(d),len(r["claims"]),len(h["claims"])); print("Khớp test:",ok,"Đủ 10 relation:",ten); assert ok and ten, "Dừng: JSON không đúng tập test"' "$DATA_DIR/factkg_test.pickle" "$REL10" "$HOP_JSON"
```

Nếu kiểm tra sai, **dừng và kiểm tra nguồn JSON**; không dựng R3 bằng JSON dev. Không ghi đè file dự đoán đang có nếu chưa xác định nó thuộc tập nào.

### 3. R3 dựng candidate top-10 cho test

```bash
cd "$REPO/with_evidence/classifier"
"$PYTHON" build_faico_lite_candidates.py \
  --data_path "$DATA_DIR" \
  --kg_path "$KG_PATH" \
  --n_candid 10 \
  --output_dir "$RUN/candidates" \
  --run_name r3_top10_k32 \
  --include_shorter_paths \
  --relation_budget 2 \
  --store_max_paths 32 \
  --test_only_candidates \
  --relation_prediction_path "$REL10" \
  --hop_prediction_path "$HOP_JSON"

ls -lh "$RUN/candidates/test_candid_paths_top10_r3_top10_k32.bin"
```

`--store_max_paths 32` chỉ giới hạn path **được lưu**, không chặn mọi nhánh KG phải duyệt. R3 top-5 trên full dev từng rất chậm ở claim `H=2`; top-10 toàn test có thể gặp lại hoặc nặng hơn. Nếu tiến độ đứng ở cùng claim khoảng 10–15 phút, dừng bằng `Ctrl+C`, ghi lại vị trí/log; **không chạy V4 khi chưa có artifact hoàn chỉnh**. Không dùng `--overwrite` lên artifact cũ.

### 4. Test cùng checkpoint V4, không train lại

```bash
"$PYTHON" baseline.py \
  --data_path "$DATA_DIR" \
  --model_cls gearlite_v4 \
  --n_candid 10 \
  --skip_prepare_input \
  --train_candid_path "$R3_DIR/train_candid_paths_r3_full.bin" \
  --dev_candid_path "$R3_DIR/dev_candid_paths_r3_full.bin" \
  --test_candid_path "$RUN/candidates/test_candid_paths_top10_r3_top10_k32.bin" \
  --max_paths 32 \
  --pair_batch_size 2 \
  --pair_max_length 128 \
  --seed 42 \
  --amp \
  --test_only \
  --checkpoint_path "$V4_CKPT" \
  --run_name r3_top10_k32_v4_testonly \
  --output_dir "$RUN/predictions"
```

Ghi lại **Accuracy và Macro-F1 của cả năm reasoning type và toàn test**; so với kết quả top-5 của **cùng checkpoint V4**. Nếu sau đó muốn thử `K=64`, phải tạo artifact mới với `--store_max_paths 64` rồi suy luận với `--max_paths 64`; chỉ đổi `--max_paths` trên artifact đã lưu 32 path sẽ không có tác dụng. K=64 với checkpoint học ở K=32 chỉ là phép thử chẩn đoán; đánh giá huấn luyện K=64 là thí nghiệm khác.
