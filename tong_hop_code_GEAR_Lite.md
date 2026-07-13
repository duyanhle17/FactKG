# Tổng hợp code GEAR-Lite cho FactKG

File này tổng hợp các thay đổi đã thêm để chạy hai ablation mới:

- E1: Pair + Mean.
- E2: Pair + Attention, gọi là GEAR-Lite v1.

Mục tiêu chính là kiểm tra giả thuyết: baseline concat hiện tại có thể mất path tốt vì nối nhiều evidence/path thành một chuỗi dài rồi bị giới hạn token của BERT. E1/E2 không nối tất cả path vào một chuỗi nữa, mà encode từng path riêng với claim.

## 1. Các file đã sửa

### `with_evidence/classifier/baseline.py`

Đây là file chính được sửa nhiều nhất.

Các phần đã thêm:

- Thêm CLI `--model_cls mean` cho E1 và `--model_cls gearlite` cho E2.
- Thêm `--max_paths`, `--pair_batch_size`, `--pair_max_length`, `--gradient_accumulation_steps`, `--seed`, `--skip_prepare_input`, `--prepare_only`.
- Thêm `PairDataset`: giữ riêng từng candidate path, không flatten tất cả path thành một string.
- Thêm `PairDataCollator`: tạo input dạng pair `[CLS] Claim [SEP] Path_i [SEP]`.
- Thêm `IndependentPathMeanClassifier`: E1 Pair + Mean.
- Thêm `GEARLiteClassifier`: E2 Pair + Attention.
- Sửa train/dev/test loop để không bỏ batch cuối, dùng checkpoint dev tốt nhất là bản sao thật, và log kết quả theo 5 nhóm reasoning.

Các block mới đều có comment dạng:

```python
# [GEAR-LITE E1/E2 START]
# ...
# [GEAR-LITE E1/E2 END]
```

Nếu sau này muốn rollback phần GEAR-Lite, có thể tìm các block này trước.

### `with_evidence/classifier/preprocess.py`

Sửa `prepare_input(data_path, kg_path, n_candid)` để output candidate path theo đúng `n_candid`.

Ví dụ:

- `--n_candid 3` đọc `test_relations_top3.json` và ghi `test_candid_paths_top3.bin`.
- `--n_candid 5` đọc `test_relations_top5.json` và ghi `test_candid_paths_top5.bin`.
- `--n_candid 10` đọc `test_relations_top10.json` và ghi `test_candid_paths_top10.bin`.

Trước đó code dễ bị lệch vì có chỗ hardcode top5.

### `requirements.txt`

Thêm `numpy` vì code có dùng seed NumPy để chạy ổn định hơn.

### `Cải tiến 15-7.md`

Cập nhật lại kế hoạch chạy E0/E1/E2, lệnh chạy, và giải thích rằng hiện tại đã code E1/E2.

## 2. Top-K / `max_paths` là gì?

Trong code này, `K` là số candidate path giữ lại cho mỗi claim.

Ví dụ một claim có 80 path ứng viên:

```text
connected paths: 30
walkable paths: 50
tổng: 80 path
```

Nếu chạy:

```bash
--max_paths 32
```

thì model chỉ lấy 32 path đầu tiên theo thứ tự:

```text
connected trước, walkable sau
```

Nếu chạy:

```bash
--max_paths 0
```

thì nghĩa là dùng toàn bộ path, tức `K = all`.

Mặc định hiện tại:

- E0 `cat`: `max_paths = 0`, giữ hành vi baseline cũ.
- E1 `mean`: `max_paths = 32`.
- E2 `gearlite`: `max_paths = 32`.

Lý do để E1/E2 mặc định `K=32`: Pair model không đưa một chuỗi concat vào BERT nữa, mà đưa từng path vào BERT riêng. Nếu `K=all`, một claim có 200 path sẽ tạo 200 input BERT. Việc này rất dễ hết VRAM và chạy chậm.

Để so sánh công bằng E0/E1/E2, nên chạy cả ba cùng `--max_paths 32`.

## 3. Luồng tensor `[B,K,L] -> [B,K,H]`

Ký hiệu:

- `B`: số claim trong một batch.
- `K`: số path giữ lại cho mỗi claim.
- `L`: số token tối đa của một pair Claim-Path.
- `H`: hidden size của BERT. Với `bert-base-cased`, `H = 768`.

Với E1/E2, mỗi claim-path được encode riêng:

```text
[CLS] Claim [SEP] Path_i [SEP]
```

Collator tạo tensor:

```text
[B, K, L]
```

Sau đó code flatten thành:

```text
[B*K, L]
```

để đưa qua cùng một BERT shared encoder. BERT trả về vector CLS cho từng pair:

```text
[B*K, H]
```

Rồi reshape lại:

```text
[B, K, H]
```

Nghĩa là với mỗi claim, ta có `K` vector path:

```text
h_1, h_2, ..., h_K
```

Mỗi `h_i` là biểu diễn của một cặp Claim-Path-i.

## 4. E1 Pair + Mean hoạt động như nào?

E1 encode từng pair Claim-Path giống trên, sau đó lấy trung bình các vector path hợp lệ.

Công thức đơn giản:

```text
o = mean(h_1, h_2, ..., h_K)
```

Nếu có padding path để làm tensor đều kích thước, padding đó bị mask và không được tính vào mean.

Vector `o` là vector evidence tổng hợp cho claim. Sau đó đưa vào MLP classifier:

```text
o -> MLP -> logits -> True / False
```

E1 không học path nào quan trọng hơn. Mọi path hợp lệ có trọng số bằng nhau.

Ý nghĩa của E1: kiểm tra xem chỉ riêng việc bỏ concat-level truncation và encode từng path riêng có giúp tăng điểm không.

## 5. E2 Pair + Attention / GEAR-Lite hoạt động như nào?

E2 cũng encode từng Claim-Path riêng để có:

```text
h_1, h_2, ..., h_K
```

Khác E1 ở bước tổng hợp path. E2 không lấy trung bình đều, mà học một điểm quan trọng cho từng path.

Trong code có scorer:

```text
H -> 64 -> 1
```

Nghĩa là:

- Input là `h_i` có kích thước `H = 768`.
- Linear thứ nhất biến `768 -> 64`.
- ReLU thêm phi tuyến để scorer học được pattern phức tạp hơn.
- Linear thứ hai biến `64 -> 1`.
- Output cuối là một scalar score cho path `i`.

Ví dụ một claim có 4 path, scorer có thể trả:

```text
score = [1.2, 0.1, 3.0, -0.5]
```

Sau masked softmax:

```text
attention weight = [0.13, 0.04, 0.80, 0.03]
```

Sau đó E2 tạo vector evidence bằng weighted sum:

```text
o = 0.13*h_1 + 0.04*h_2 + 0.80*h_3 + 0.03*h_4
```

Cuối cùng:

```text
o -> MLP -> logits -> True / False
```

Điểm quan trọng: attention không tự tìm path mới ngoài candidate set. Nó chỉ học cách đặt trọng số cao/thấp cho các path đã có trong `K` path được đưa vào.

## 6. MLP, logits và softmax là gì?

MLP là classifier nhỏ nằm sau vector evidence `o`.

Trong code, MLP trả ra 2 số gọi là logits:

```text
logits = [logit_false, logit_true]
```

Ví dụ:

```text
logits = [1.2, 3.8]
```

Số thứ hai lớn hơn nên model nghiêng về class thứ hai. Khi tính probability, softmax sẽ biến logits thành xác suất:

```text
softmax([1.2, 3.8]) ~= [0.07, 0.93]
```

Khi train, code dùng `CrossEntropyLoss`, nên không cần tự gọi softmax trước loss. Khi đoán nhãn, code lấy class có logit lớn nhất.

## 7. `pair_batch_size` là gì?

Với E0 concat, một claim thường tương ứng một input BERT dài.

Với E1/E2, một claim có `K` path sẽ tương ứng `K` input BERT.

Ví dụ:

```text
pair_batch_size = 1
max_paths = 32
```

thì một batch vật lý có 1 claim, nhưng thực tế BERT phải encode 32 pair:

```text
1 claim * 32 path = 32 BERT inputs
```

Nếu đặt:

```text
pair_batch_size = 4
max_paths = 32
```

thì BERT phải encode:

```text
4 claim * 32 path = 128 BERT inputs
```

Vì vậy `pair_batch_size` cần nhỏ hơn batch size của E0 để tránh hết VRAM.

Mặc định hiện tại:

```text
pair_batch_size = 1
max_paths = 32
```

## 8. Vì sao cần gradient accumulation?

Nếu E0 dùng:

```text
batch_size = 32
```

thì mỗi lần optimizer update sau khoảng 32 claim.

Nhưng E1/E2 dùng:

```text
pair_batch_size = 1
```

nếu update ngay sau mỗi claim thì số lần update nhiều hơn E0 rất nhiều. Như vậy so sánh E0 với E1/E2 sẽ không công bằng.

Vì vậy code có `gradient_accumulation_steps` tự động. Với:

```text
batch_size = 32
pair_batch_size = 1
gradient_accumulation_steps = auto
```

code sẽ tích lũy gradient khoảng 32 mini-batch rồi mới update optimizer một lần.

Hiểu đơn giản:

```text
32 lần forward/backward nhỏ, mỗi lần 1 claim
= 1 lần update tương đương khoảng 32 claim
```

## 9. Nên chạy thí nghiệm thế nào?

Chuẩn nhất là prepare candidate path một lần:

```bash
cd with_evidence/classifier
python baseline.py --data_path <DATA_DIR> --kg_path <KG_PATH> --n_candid 5 --prepare_only
```

Sau đó chạy E0/E1/E2 trên cùng candidate set:

```bash
python baseline.py --data_path <DATA_DIR> --model_cls cat --n_candid 5 --max_paths 32 --batch_size 32 --epoch 10 --seed 42 --skip_prepare_input
```

```bash
python baseline.py --data_path <DATA_DIR> --model_cls mean --n_candid 5 --max_paths 32 --pair_batch_size 1 --pair_max_length 128 --epoch 10 --seed 42 --skip_prepare_input
```

```bash
python baseline.py --data_path <DATA_DIR> --model_cls gearlite --n_candid 5 --max_paths 32 --pair_batch_size 1 --pair_max_length 128 --epoch 10 --seed 42 --skip_prepare_input
```

Nên đọc kết quả theo:

- Accuracy tổng.
- Macro-F1 tổng.
- Accuracy và Macro-F1 cho 5 loại reasoning: one-hop, multi-hop, conjunction, existence, negation.

## 10. Kết luận ngắn

Hiện tại code đã có:

- E0: baseline concat cũ.
- E1: Pair + Mean.
- E2: Pair + Attention, tức GEAR-Lite v1.

GEAR-Lite hiện tại chưa có ERNet/GNN và chưa có learned hard selector. Đây là bước kiểm chứng gọn nhất để trả lời câu hỏi: encode từng path riêng và attention trên path có giúp FactKG multi-hop tốt hơn concat baseline không.
