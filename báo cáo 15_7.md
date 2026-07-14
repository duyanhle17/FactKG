# Báo cáo thử nghiệm GEAR-Lite cho FactKG — 15/07/2026

## 1. Vấn đề của FactKG trước khi cải tiến

Pipeline FactKG cũ dùng **E0 / `ConcatClassifier`**: sau khi retrieval sinh các candidate path, hệ thống nối claim và nhiều path thành một input duy nhất cho BERT. Cách này đơn giản nhưng có hai rủi ro chính:

1. BERT chỉ nhận tối đa 512 token. Khi có nhiều path hoặc path dài, phần evidence ở cuối chuỗi **có thể bị truncate**; path đúng khi đó không còn được BERT đọc.
2. Các path tốt và path nhiễu bị trộn trong cùng một chuỗi, nên classifier phải tự tìm proof trong một input dài. Điều này đặc biệt bất lợi cho claim cần nhiều bước suy luận.

Cấu hình E0 tốt nhất trước đây là **train/test 3-hop, relation retrieval top-5**. Nó đạt **81.80% Total Test Accuracy**, nhưng `Multi-hop` chỉ đạt **68.84%**, thấp nhất trong năm loại reasoning. Vì vậy, mục tiêu của cải tiến là giữ từng path riêng để giảm rủi ro truncate do nối toàn bộ path, đồng thời giúp model tổng hợp evidence có chọn lọc hơn.

> Đây là giả thuyết kiến trúc. Báo cáo hiện chưa đo trực tiếp tỷ lệ path bị truncate, nên không khẳng định đây là nguyên nhân duy nhất của lỗi multi-hop.

## 2. Hai mô hình cải tiến

Hai mô hình đều dùng **cùng candidate paths**, cùng BERT và cùng classifier cuối. Chúng chỉ khác nhau ở cách gộp các vector path sau khi BERT đã đọc từng cặp claim–path.

| Mô hình | Tên trong code | Vai trò |
|---|---|---|
| **E1: Pair + Mean** | `--model_cls mean` | Ablation cơ sở: kiểm tra riêng việc bỏ nối toàn bộ path có ích hay không. |
| **E2: Pair + Attention (GEAR-Lite)** | `--model_cls gearlite` | Mô hình đề xuất: ngoài việc đọc riêng từng path, model học trọng số cho các path quan trọng hơn. |

`GEAR-Lite` là tên cho phiên bản rút gọn lấy cảm hứng từ GEAR paper; nó **không** bao gồm ERNet/GNN hay attention claim–evidence đầy đủ của GEAR gốc.

## 3. Cách hoạt động của E1 và E2

E1 và E2 có cùng luồng chạy đến trước bước gộp path. Có thể đọc theo bốn tầng sau:

```text
Tầng 0: candidate artifact  →  lấy tối đa K path theo thứ tự có sẵn
Tầng 1: [CLS] Claim [SEP] Path_i [SEP]  →  BERT  →  h_i
Tầng 2: gộp h_1 ... h_K bằng Mean hoặc Attention  →  vector evidence o
Tầng 3: MLP(o)  →  logits [score_False, score_True]  →  argmax  →  False/True
```

### 3.1. Tầng 0 — lấy path trước khi encode

Path không được E1/E2 tự sinh ra trong classifier. Chúng được lấy từ các file candidate đã chuẩn bị sẵn:

- Train: `train_candid_paths.bin`
- Dev: `dev_candid_paths.bin`
- Test: `test_candid_paths_top{n_candid}.bin`, ví dụ `test_candid_paths_top3.bin`

Khi chạy với `--skip_prepare_input`, code chỉ đọc lại các artifact này để giữ nguyên candidate set. Với mỗi claim `s`, classifier lấy:

```text
candids[s]["connected"] + candids[s]["walkable"]
```

Thứ tự được giữ nguyên là `connected` trước, `walkable` sau. Sau đó `_ordered_paths(..., max_paths)` chỉ lấy tối đa `K = max_paths` path đầu tiên. Ở lượt E1 hiện tại, `max_paths=32`, nên chỉ 32 path đầu được đưa vào BERT. Nếu một proof path nằm ngoài 32 path này, E1/E2 sẽ không nhìn thấy nó.

### 3.2. Tầng 1 — Pair encoder dùng chung cho E1 và E2

Sau khi có danh sách path, `PairDataCollator` tạo từng cặp riêng:

```text
[CLS] Claim [SEP] Path_i [SEP] ,  i = 1 ... K
```

Trong text của `Path_i`, các entity/relation trong path được nối bằng token `[SEP]` của tokenizer. Ví dụ khái niệm:

```text
Claim: "A is related to B"
Path_i: entity_1 [SEP] relation_1 [SEP] entity_2 [SEP] relation_2 [SEP] entity_3
```

Tokenizer biến cả batch thành tensor:

```text
[B, K, L]
```

- `B`: số claim trong batch.
- `K`: số path được giữ cho mỗi claim (`max_paths`; lượt E1 hiện tại dùng `K=32`).
- `L`: số token tối đa của mỗi cặp (`pair_max_length=128`).
- `H`: kích thước vector BERT (768 với `bert-base-cased`).

Trước khi đưa vào BERT, code reshape `[B, K, L]` thành `[B*K, L]`, tức là xem mỗi Claim-Path như một input BERT độc lập. Một shared BERT mã hoá tất cả cặp này, lấy vector `[CLS]` cuối cùng, rồi reshape ngược lại:

```text
[B*K, L]  →  Shared BERT  →  [B*K, H]  →  [B, K, H]
```

Vector `h_i` là biểu diễn của riêng cặp `Claim–Path_i`. Do từng pair được giới hạn độc lập, E1/E2 loại bỏ việc một path bị mất chỉ vì nó đứng sau các path khác trong chuỗi concat. Tuy vậy, path dài vẫn có thể bị cắt ở giới hạn 128 token, và path nằm ngoài `max_paths` vẫn không được encode.

`path_mask` đi kèm có shape `[B, K]`: path thật là `True`, path padding là `False`. Mask này được dùng ở tầng gộp để padding không ảnh hưởng kết quả.

### 3.3. Tầng 2 của E1 — Pair + Mean

E1 coi mọi **path hợp lệ** có vai trò như nhau. Nó lấy trung bình có mask của các vector `h_i`:

```text
o = sum(h_i * mask_i) / sum(mask_i)
```

`mask` bảo đảm các vị trí padding không đi vào phép trung bình. E1 không học path nào quan trọng hơn; vì vậy nó là phép kiểm tra công bằng cho câu hỏi: **chỉ tách từng path ra khỏi concat đã có ích chưa?**

### 3.4. Tầng 2 của E2 — Pair + Attention (GEAR-Lite)

E2 giữ nguyên tầng lấy path và tầng BERT pair encoder của E1, nhưng thay `mean` bằng attention học được:

```text
h_i → Linear(H→64) → ReLU → Linear(64→1) → score_i
score_1 ... score_K → masked softmax → α_1 ... α_K
o = Σ α_i h_i
```

`α_i` là trọng số attention của path `i`; các padding nhận trọng số 0. Khi train bằng loss nhãn True/False, BERT, lớp attention và MLP được cập nhật cùng nhau. Vì thế E2 có thể ưu tiên path hữu ích hơn thay vì chia đều như E1. Attention chỉ lựa chọn trong candidate set đã có; nó không tự tạo ra path bị retrieval bỏ sót và không phải hard selector.

### 3.5. Tầng 3 — lấy True/False ở đâu

Sau tầng gộp, cả E1 và E2 đều có một vector evidence chung `o` cho claim. Vector này đi qua cùng một MLP:

```text
o → Linear(H→H) → ReLU → Linear(H→2) → logits
```

`logits` có hai giá trị:

```text
[score_False, score_True]
```

Khi train, `logits` được so với label gốc bằng `CrossEntropyLoss`. Label gốc trong FactKG được lưu dạng `[True]` hoặc `[False]`, sau đó code đổi thành số bằng `int(label)`: `False = 0`, `True = 1`.

Khi dev/test, code lấy nhãn dự đoán bằng:

```text
pred = logits.argmax(dim=1)
```

Nếu `pred = 0` thì trả lời `False`; nếu `pred = 1` thì trả lời `True`. Accuracy được tính bằng cách so sánh `pred` với label thật đã đổi sang 0/1.

## 4. Các mô hình đã chạy và cấu hình

| Lượt chạy | Model | Retrieval / path setting | Trạng thái |
|---|---|---|---|
| **E0 (cũ)** | `ConcatClassifier` | 3-hop, relation top-5; nối evidence thành một input BERT | Đã chạy — báo cáo ngày 06/05 |
| **E1 (mới)** | Pair + Mean | 3-hop, relation top-3, `max_paths=32`, `pair_max_length=128`, seed 42 | Đã chạy — báo cáo này |
| **E2 (mới)** | Pair + Attention / GEAR-Lite | Dự kiến giữ đúng candidate set và hyperparameter của E1 để so sánh | Chưa chạy test |

Ở lượt E1, checkpoint được chọn trên dev là **epoch 0**, với `dev_acc = 0.8746`. Tập test gồm 9,041 mẫu, được báo cáo theo năm reasoning type của FactKG.

## 5. Kết quả test

| Reasoning type | E0: Concat<br>3-hop top-5 | E1: Pair + Mean<br>3-hop top-3 | Chênh lệch E1 − E0 | Macro-F1 của E1 |
|---|---:|---:|---:|---:|
| One-hop | 84.22% | 86.42% | +2.20% | 0.8641 |
| Multi-hop | 68.84% | 67.29% | -1.55% | 0.6492 |
| Conjunction | 85.08% | 79.41% | -5.67% | 0.7791 |
| Existence | 89.08% | 94.83% | +5.75% | 0.9483 |
| Negation | 84.35% | 86.76% | +2.41% | 0.8675 |
| **Overall accuracy** | **81.80%** | **≈80.93%** | **≈-0.87%** | — |

`≈80.93%` là overall accuracy ước tính từ accuracy theo nhóm đã làm tròn trong log E1; cần lấy dòng `Total Test Acc` hoặc prediction thô nếu cần con số chính xác tuyệt đối.

### Nhận xét đúng về bảng trên

- E1 cao hơn E0 ở `One-hop`, `Existence` và `Negation`.
- E1 thấp hơn ở `Conjunction` (-5.67 điểm) và `Multi-hop` (-1.55 điểm); do đó chưa đạt mục tiêu cải thiện multi-hop.
- Bảng này **không phải ablation kiến trúc thuần túy**: E0 dùng retrieval top-5, còn E1 dùng top-3. Mức giảm của E1 có thể đến từ việc top-3 bỏ sót relation/path cần thiết, không thể kết luận Pair + Mean kém hơn Concat chỉ từ bảng này.

## 6. Kết luận và bước thử tiếp theo

Hiện mới có kết quả cho **E1**. Bước quyết định tiếp theo là chạy **E2** với đúng candidate artifact, `n_candid=3`, `max_paths=32`, `pair_max_length=128` và seed như E1. Khi đó khác biệt E1–E2 chỉ còn là **Mean so với Attention**, nên mới trả lời được attention của GEAR-Lite có giúp chọn evidence hay không.

Sau so sánh E1–E2, nên chạy cùng một kiến trúc với top-5 (hoặc chạy E0 với top-3) để tách riêng ảnh hưởng của **retrieval width** khỏi ảnh hưởng của **kiến trúc classifier**. Model nên được chọn bằng dev trước, rồi mới dùng test để báo cáo kết quả cuối.

Nguồn kết quả E0: [bao_cao_6_5.md](bao_cao_6_5.md).
