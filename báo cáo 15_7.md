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

Mục tiêu chung của E1/E2 là thay cách cũ **nối toàn bộ path thành một chuỗi dài** bằng cách giữ từng path riêng. Với mỗi claim, retrieval đã sinh sẵn một tập candidate path; classifier lấy tối đa `K` path đầu tiên (`max_paths`, lượt E1 hiện tại dùng `K=32`) để xử lý.

```text
Claim + K candidate paths
→ Tầng 1: encode từng Claim–Path thành các vector h_i
→ Tầng 2: gộp các vector path thành một vector evidence o
→ Tầng 3: dùng o để dự đoán True/False
```

### 3.1. Tầng 1 — Pair encoder: biến từng path thành vector riêng

Ở tầng này, model chưa quyết định path nào đúng hay sai. Việc chính là cho BERT đọc **claim cùng từng path riêng lẻ**. Với mỗi path `Path_i`, input đưa vào BERT có dạng:

```text
[CLS] Claim [SEP] Path_i [SEP] ,  i = 1 ... K
```

Nếu một claim có 32 path thì tạo ra 32 cặp `Claim–Path`. Tất cả các cặp này dùng chung một BERT, tức là BERT có cùng trọng số cho mọi path. Sau khi encode, mỗi path có một vector `[CLS]` riêng:

```text
Claim–Path_1 → BERT → h_1
Claim–Path_2 → BERT → h_2
...
Claim–Path_K → BERT → h_K
```

Các vector này được lưu tạm trong một tensor:

```text
[B, K, H]
```

- `B`: số claim trong batch.
- `K`: số path của mỗi claim.
- `H`: kích thước vector BERT (768 với `bert-base-cased`).

Đi kèm tensor này là `path_mask` để biết đâu là path thật, đâu là padding. Mục đích của tầng 1 là tạo một biểu diễn riêng cho từng path, tránh tình huống path tốt bị chìm hoặc bị cắt mất vì đứng sau nhiều path khác trong chuỗi concat dài. Kết quả mong muốn là: nếu một path chứa evidence quan trọng, nó vẫn có một vector `h_i` riêng để tầng sau sử dụng.

### 3.2. Tầng 2 của E1 — Mean aggregator: lấy trung bình vector path

Sau tầng 1, E1 có `K` vector path cho một claim. E1 không chọn path nào quan trọng hơn, mà lấy trung bình các vector path hợp lệ:

```text
o = sum(h_i * mask_i) / sum(mask_i)
```

Vector `o` là vector evidence chung của toàn bộ candidate set. `mask` bảo đảm path padding không đi vào phép trung bình.

Mục đích của E1 là làm ablation cơ sở: kiểm tra xem **chỉ cần tách từng path ra để BERT encode riêng** đã giúp tốt hơn concat cũ chưa. Cải tiến kỳ vọng của E1 là giảm lỗi do concat quá dài và giữ tín hiệu của từng path rõ hơn. Giới hạn của E1 là mọi path thật đều có trọng số như nhau, nên nếu có nhiều path nhiễu thì vector trung bình vẫn có thể bị loãng.

### 3.3. Tầng 2 của E2 — Attention aggregator: học path nào quan trọng hơn

E2 giữ nguyên tầng 1 như E1, nhưng thay phép trung bình bằng attention. Với mỗi vector path `h_i`, model học một điểm quan trọng `score_i`:

```text
h_i → Linear(H→64) → ReLU → Linear(64→1) → score_i
score_1 ... score_K → masked softmax → α_1 ... α_K
o = Σ α_i h_i
```

`α_i` là trọng số attention của path `i`. Path nào model cho là hữu ích hơn sẽ có `α_i` lớn hơn; path padding có trọng số 0. Vector evidence cuối cùng `o` là tổng có trọng số của các vector path.

Mục đích của E2 là giảm ảnh hưởng của path nhiễu. Thay vì chia đều như E1, E2 học cách đặt trọng số cao hơn cho path có khả năng hỗ trợ hoặc phản bác claim. Cải tiến kỳ vọng là các claim cần nhiều bước suy luận, đặc biệt `Multi-hop` và `Conjunction`, sẽ được lợi vì model có cơ chế tập trung vào path liên quan hơn. Tuy nhiên, attention chỉ chọn mềm trong các path đã được retrieval đưa vào; nếu proof path không có trong candidate set thì E2 cũng không tự tạo ra được.

### 3.4. Tầng 3 — Verifier: biến vector evidence thành True/False

Sau tầng 2, cả E1 và E2 đều có một vector evidence chung `o`. Tầng cuối cùng dùng cùng một MLP để biến `o` thành hai điểm số:

```text
o → Linear(H→H) → ReLU → Linear(H→2) → logits
```

`logits` có hai giá trị:

```text
[score_False, score_True]
```

Tầng này là tầng ra quyết định. Khi train, hai score này được so với label thật bằng `CrossEntropyLoss`. Khi dev/test, model chọn score lớn hơn:

```text
pred = logits.argmax(dim=1)
```

Nếu `pred = 0` thì trả lời `False`; nếu `pred = 1` thì trả lời `True`. Mục đích của tầng cuối là biến toàn bộ thông tin evidence đã được encode và gộp lại thành một nhãn claim-level duy nhất. Vì E1 và E2 dùng cùng verifier, khác biệt chính giữa hai mô hình nằm ở tầng 2: E1 gộp bằng mean, còn E2 gộp bằng attention.

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
