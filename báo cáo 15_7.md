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
| **E1** | Pair + Mean | 3-hop, relation top-3, `max_paths=32`, `pair_max_length=128`, seed 42 | Đã chạy |
| **E2a** | Pair + Attention / GEAR-Lite | 3-hop, relation top-3, seed 42 | Đã chạy; best dev: epoch 0, `dev_acc=0.8859` |
| **E2b** | Pair + Attention / GEAR-Lite | 3-hop, relation top-5, seed 42 | Đã chạy; best dev: epoch 0, `dev_acc=0.8994` |

`top-3`/`top-5` là số **relation** được retrieval giữ lại, không phải số graph path cuối cùng. Pair models dùng mặc định `max_paths=32` và `pair_max_length=128` nếu lệnh chạy không ghi đè hai tham số này. Tập test gồm 9,041 mẫu.

## 5. Kết quả test

### 5.1. Accuracy theo năm reasoning type

| Reasoning type | E0: Concat<br>3-hop top-5 | E1: Pair + Mean<br>3-hop top-3 | E2a: Attention<br>3-hop top-3 | E2b: Attention<br>3-hop top-5 |
|---|---:|---:|---:|---:|
| One-hop | 84.22% | 86.42% | 90.49% | **91.12%** |
| Multi-hop | 68.84% | 67.29% | 69.32% | **72.18%** |
| Conjunction | **85.08%** | 79.41% | 83.61% | 82.82% |
| Existence | 89.08% | **94.83%** | **94.83%** | 94.37% |
| Negation | 84.35% | 86.76% | 87.29% | **87.98%** |
| **Total Test Accuracy** | 81.80% | ≈80.93% | **83.72%** | 84.23% |
| **Total Test Macro-F1** | — | — | **83.50%** | 83.48% |

`≈80.93%` là overall accuracy tái tính từ accuracy theo nhóm đã làm tròn trong log E1; E1 chưa có dòng `Total Test Acc` gốc để đối chiếu.

### 5.2. Macro-F1 của hai lượt GEAR-Lite

| Reasoning type | E2a: top-3 | E2b: top-5 |
|---|---:|---:|
| One-hop | 0.9048 | **0.9110** |
| Multi-hop | 0.6781 | **0.7000** |
| Conjunction | **0.8285** | 0.8087 |
| Existence | **0.9483** | 0.9437 |
| Negation | 0.8725 | **0.8797** |
| **Total Test Macro-F1** | **0.8350** | 0.8348 |

### 5.3. Nhận xét so với E1 và E0

**E2a top-3 so với E1 top-3** là phép so sánh kiến trúc quan trọng nhất: nếu hai lượt dùng cùng candidate artifact và các hyperparameter Pair giống nhau, khác biệt chính chỉ là `Mean` so với `Attention`. E2a tăng ở mọi nhóm hoặc giữ nguyên:

- One-hop: `+4.07` điểm phần trăm; Multi-hop: `+2.03`; Conjunction: `+4.20`.
- Existence giữ nguyên `94.83%`; Negation tăng `+0.53`.
- Total Test Accuracy tăng từ `≈80.93%` lên `83.72%` (khoảng `+2.79` điểm phần trăm).

Đây là tín hiệu tốt rằng attention giúp giảm ảnh hưởng của path nhiễu tốt hơn Mean trong candidate set hiện có.

**E2b top-5 so với E2a top-3:** mở rộng relation retrieval làm Multi-hop tăng rõ từ `69.32%` lên **`71.18%`** (`+1.86` điểm phần trăm), đồng thời One-hop và Negation cũng tăng. Tuy nhiên Conjunction giảm `1.79` điểm và Existence giảm `0.46` điểm; Total Test Accuracy giảm rất nhỏ từ `83.72%` xuống `83.69%` (`-0.03` điểm). Vì vậy, ở seed 42, top-5 là cấu hình tốt nhất cho **Multi-hop**, nhưng chưa tốt hơn toàn diện về Overall; hai cấu hình gần như hòa về tổng thể.

**E2b top-5 so với E0 Concat top-5:** đây là so sánh cùng độ rộng retrieval. E2b tăng Multi-hop từ `68.84%` lên **`71.18%`** (`+2.34` điểm), tăng Overall từ `81.80%` lên **`83.69%`** (`+1.89` điểm), và tăng One-hop/Existence/Negation. Riêng Conjunction giảm từ `85.08%` xuống `81.82%` (`-3.26` điểm). Kết quả cho thấy Pair + Attention có triển vọng hơn Concat cho Multi-hop, nhưng không được diễn giải là ablation nhân quả tuyệt đối nếu candidate artifact, seed hoặc các hyperparameter của E0 cũ không hoàn toàn trùng khớp.

## 6. Kết luận và bước tiếp theo

GEAR-Lite Attention đã cải thiện rõ so với Pair + Mean ở top-3; đây là bằng chứng thực nghiệm đầu tiên ủng hộ việc dùng attention để gộp candidate path trong FactKG.

- Nếu ưu tiên **Overall Accuracy** của seed hiện tại, E2a top-3 đang cao nhất: **83.72%**.
- Nếu ưu tiên riêng **Multi-hop**, E2b top-5 đang tốt nhất: **71.18%**.
- Chênh lệch Overall giữa E2a và E2b chỉ `0.03` điểm phần trăm, nên chưa đủ để kết luận top-3 tốt hơn top-5 từ một seed.

Bước xác nhận phù hợp là chạy E2a và E2b thêm các seed khác, báo cáo `mean ± std`. Song song, cần thống kê tổng candidate path và tỷ lệ claim bị cắt ở `max_paths=32`/budget 512 token của Concat trước khi thử tăng `max_paths` lên 64.

Nguồn kết quả E0: [bao_cao_6_5.md](bao_cao_6_5.md).
