# ERNet và hướng ghép với GEARLite V4

## 1. Trạng thái hiện tại

**V4 không có ERNet.** `gearlite_v4` chỉ gồm BERT pair, vector claim riêng,
`c_set`, attention và classifier. ERNet gốc có trong code GEAR tham khảo ở
`temp_gear_repo/gear/models.py`.

Đã thêm một mô hình mới là **`gearlite_v5` = V4 + sparse ERNet 1 layer**. V4
được giữ nguyên làm baseline đối chứng; không có checkpoint V4 nào bị thay đổi.

## 2. ERNet là gì?

ERNet (*Evidence Reasoning Network*) là tầng cho các evidence/path **trao đổi
thông tin với nhau** trước khi attention chọn evidence quan trọng.

Giả sử BERT đã tạo `K` vector path:

```text
h1, h2, ..., hK       (mỗi vector có H = 768 chiều)
```

ERNet xem mỗi path là một node. Với node/path `i`, nó tính mức liên quan đến
mỗi node/path `j`:

```text
a_ij = MLP([h_i ; h_j])
alpha_ij = softmax_j(a_ij)
h'_i = sum_j(alpha_ij * h_j)
```

Nghĩa là `h'_i` không còn chỉ chứa thông tin của `Path_i`; nó có thể nhận thêm
thông tin từ những path liên quan khác. `alpha_ij` là trọng số: path `j` đóng
góp bao nhiêu vào việc cập nhật path `i`.

Ví dụ, một path chứa entity trung gian, path khác chứa relation quyết định. Nếu
hai path được nối cạnh, ERNet có thể làm representation của mỗi path mang một
phần thông tin từ path còn lại. ERNet **không tạo path mới, không retrieval lại
KG và không biết gold path**; nó chỉ trộn thông tin giữa candidate paths đã có.

## 3. ERNet khác attention của V4 ở đâu?

V4 hiện tại có một attention cuối:

```text
score_i = MLP([c_claim ; c_set ; h_i])
alpha_i = softmax_i(score_i)
o = sum_i(alpha_i * h_i)
```

Attention này trả lời: **path nào nên đóng góp nhiều vào đáp án cuối?** Nó tạo
một trọng số cho mỗi path rồi gộp cả tập thành một vector `o`.

ERNet trả lời câu khác: **khi cập nhật path i, path j nên gửi bao nhiêu thông
tin cho path i?** Nó có ma trận trọng số `K x K` và tạo ra các path đã được cập
nhật `h'_1, ..., h'_K`.

```text
ERNet:    h_i + các path khác  -> h'_i, cho mọi i
V4:       h'_1 ... h'_K        -> o -> True/False
```

Do đó ERNet nằm **trước** attention V4, không thay attention V4.

## 4. Flow thực thi: R3 + V4 + sparse ERNet

```text
Claim
  ├─ R3 candidate artifact: tối đa K = 32 path hợp lệ
  │       └─ BERT([Claim, Path_i]) -> h_i, i = 1..K
  │               └─ sparse ERNet message passing -> h'_i
  │
  └─ BERT([Claim]) -> c_claim

c_set = masked_mean(h'_1, ..., h'_K)
score_i = MLP([c_claim ; c_set ; h'_i])
alpha_i = masked_softmax(score_i)
o = sum_i(alpha_i * h'_i)
o -> classifier -> True / False
```

`path_mask` mask cả node/cạnh padding. Sau đó `masked_mean` và
`masked_softmax` tiếp tục loại padding khỏi `c_set`, attention và classifier.

Khác với V4 hiện tại chỉ ở một điểm: V4 dùng `h_i` trực tiếp; biến thể mới dùng
`h'_i` sau ERNet. Nhờ vậy đây là một ablation rõ ràng về giá trị của graph
reasoning.

## 5. Quy tắc cạnh sparse đã cài

GEAR gốc nối đầy đủ mọi evidence sentence. `gearlite_v5` là bản điều chỉnh cho
FactKG: node là một candidate path, không phải một evidence sentence.

- Mỗi node là một candidate path.
- Luôn có self-loop: path giữ thông tin của chính nó.
- Chỉ nối hai path khi chúng chia sẻ **intermediate entity không nằm trong
  `Entity_set` của claim**, hoặc tail của path này trùng head của path kia.
- Không có cạnh thì hai path không trao đổi thông tin.
- Không nối chỉ vì cùng head/entity bắt đầu, cùng relation, hoặc cùng endpoint.

Ví dụ, `P1=[A,r1,B,r2,C]` và `P2=[D,r3,B,r4,E]` nối với nhau vì cùng có
intermediate entity `B`. `P1=[A,r1,B]` và `P3=[A,r5,F]` không nối chỉ vì cùng
bắt đầu từ `A`. Các cạnh được tạo sau top-K R3, trực tiếp từ path raw trước khi
BERT tokenize, nên không cần build lại R3 artifact.

Mục tiêu là hỗ trợ proof có nhiều path liên quan, đồng thời hạn chế path nhiễu
làm loãng evidence tốt.

## 6. Cách chạy và so sánh đúng

Không cần chạy lại retrieval/R3 nếu dùng chính candidate artifact R3 hiện có.
Phải **train lại `gearlite_v5` từ đầu**, vì ERNet là module mới và path vector
đi vào attention đã thay đổi; không dùng checkpoint V4 cũ để kết luận về ERNet.

Các thí nghiệm nên dùng cùng R3 artifact, `K=32`, BERT, batch, seed và cách
chọn best-dev checkpoint:

| Cấu hình | Ý nghĩa |
|---|---|
| V4, 0 ERNet layer | Baseline hiện có: không message passing. |
| V4 + sparse ERNet, 1 layer (`gearlite_v5`) | Thử nghiệm chính đã được code: mỗi path nhận một lượt thông tin từ path liên quan. |
| V4 + sparse ERNet, 2 layers | Chưa code; chỉ làm nếu 1 layer có tín hiệu tốt. |

Đo Total Accuracy/Macro-F1 và đủ năm reasoning type. Đặc biệt theo dõi
Multi-hop và Conjunction, vì đây là hai nhóm có khả năng cần kết hợp nhiều
path nhất. Nếu điểm giảm, cần kiểm tra candidate, các cạnh sparse và dự đoán
sai để xác định nguyên nhân; ERNet không thể tự tạo proof bị retrieval bỏ sót.

Lệnh train trên cùng R3 Full artifact:

```bash
cd /home/namnx/duyanh/FactKG/with_evidence/classifier

export REPO=/home/namnx/duyanh/FactKG
export PYTHON=/home/namnx/duyanh/.conda/factkg/bin/python
export DATA_DIR=/home/namnx/duyanh/Data
export ART_ROOT="$REPO/artifacts/faico_lite_top5"
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

mkdir -p "$ART_ROOT/r3_full/predictions_sparse_ernet"

"$PYTHON" baseline.py \
  --data_path "$DATA_DIR" \
  --model_cls gearlite_v5 \
  --n_candid 5 \
  --skip_prepare_input \
  --train_candid_path "$ART_ROOT/r3_full/train_candid_paths_r3_full.bin" \
  --dev_candid_path "$ART_ROOT/r3_full/dev_candid_paths_r3_full.bin" \
  --test_candid_path "$ART_ROOT/r3_full/test_candid_paths_top5_r3_full.bin" \
  --max_paths 32 \
  --pair_batch_size 2 \
  --pair_max_length 128 \
  --gradient_accumulation_steps 16 \
  --epoch 4 \
  --lr 5e-5 \
  --seed 42 \
  --amp \
  --run_name r3_full_v5_sparse_ernet \
  --output_dir "$ART_ROOT/r3_full/predictions_sparse_ernet"
```

## 7. Kết quả lần chạy V5

Đã chạy `gearlite_v5` với R3 Full, top-5 relation, `max_paths=32`, seed 42 và
4 epoch. Checkpoint tốt nhất theo dev là epoch 2 (`dev_acc=95.65%`). Kết quả
test:

| Reasoning type | Số mẫu | Accuracy | Macro-F1 |
|---|---:|---:|---:|
| One-hop | 1,914 | 86.15% | 86.15% |
| Multi-hop | 1,874 | 62.81% | 58.28% |
| Conjunction | 3,069 | 79.77% | 78.06% |
| Existence | 870 | 92.99% | 92.99% |
| Negation | 1,314 | 86.99% | 86.96% |
| **Tổng** | **9,041** | **79.92%** | **79.33%** |

So với V4 trên cùng R3 Full và seed 42, V5 giảm ở cả năm nhóm: One-hop
`−5.49`, Multi-hop `−18.35`, Conjunction `−4.26`, Existence `−1.95`, Negation
`−1.44` điểm phần trăm. Overall Accuracy giảm từ `86.74%` xuống `79.92%`
(`−6.82` điểm); Macro-F1 giảm từ `86.63%` xuống `79.33%` (`−7.30` điểm).

Dev `95.65%` cao hơn Test `79.92%` đáng kể. Vì vậy kết quả hiện tại cho thấy
cấu hình V5 lần chạy này chưa cải thiện V4; riêng một seed chưa đủ để kết luận
sparse ERNet luôn có hại. Trước khi thử kiến trúc khác, cần kiểm tra lại cách
tạo/đọc candidate và sự tương ứng giữa Dev với Test, rồi xem các dự đoán sai
Multi-hop của V5.

Checkpoint và prediction được lưu tại:

```text
/home/namnx/duyanh/FactKG/artifacts/faico_lite_top5/r3_full/predictions_sparse_ernet/
```

Checkpoint:
`best_model_gearlite_v5_r3_full_v5_sparse_ernet_seed42.pth`.

## 8. Kết luận ngắn

V4 giải quyết việc **chọn mềm path** bằng claim riêng và bối cảnh toàn
candidate set. `gearlite_v5` thêm một lượt để các path liên quan **trao đổi
thông tin trước khi được chọn**. Trong lần chạy hiện tại, V5 thấp hơn V4, nhất
là ở Multi-hop. Cần kiểm tra chênh lệch Dev/Test và lỗi dự đoán trước khi kết
luận về giá trị của sparse ERNet.
