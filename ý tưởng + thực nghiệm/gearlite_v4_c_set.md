# GEARLite V4: Vì sao thêm `c_set`?

## 1. Mục đích của V4

V3 dùng hai thông tin để chấm từng path:

```text
c_claim = BERT(Claim)
h_i     = BERT(Claim + Path_i)
score_i = MLP([c_claim ; h_i])
```

V3 biết claim và path hiện tại, nhưng không biết các path khác trong cùng
candidate set đang có đặc điểm gì.

V4 bổ sung một vector tóm tắt toàn bộ candidate set:

```text
c_set = trung bình các h_i hợp lệ
score_i = MLP([c_claim ; c_set ; h_i])
```

Mục đích của `c_set` là cung cấp **bối cảnh chung** khi chấm từng path. Nhờ
đó, model có thể học rằng một path có ý nghĩa khác nhau tùy vào các path còn
lại, thay vì đánh giá từng path hoàn toàn độc lập.

`c_set` không phải danh sách bằng chứng và không tự kiểm tra logic rằng đã đủ
proof. Đây là một vector đặc trưng ẩn do BERT học; thông tin về từng path bị
nén thành giá trị trung bình. Vì vậy V4 là cơ chế attention mềm, không phải
logical coverage checker.

## 2. Flow của V4

1. Dùng candidate artifact R3 có sẵn. Không cần chạy lại retrieval nếu không
   thay đổi relation, hop hoặc KG.
2. Với mỗi claim, BERT encode riêng từng cặp:

   ```text
   [CLS] Claim [SEP] Path_i [SEP]  →  h_i
   ```

   Kết quả có dạng `[K, H]`, thường `H = 768`.
3. Encode claim riêng:

   ```text
   [CLS] Claim [SEP]  →  c_claim
   ```
4. Tính `c_set` bằng trung bình theo từng chiều của các path thật. Path
   padding không được tính:

   ```text
   c_set[j] = (h_1[j] + h_2[j] + ... + h_K[j]) / K
   ```

5. Với từng path, ghép ba vector rồi chấm điểm:

   ```text
   [c_claim ; c_set ; h_i]  →  MLP(2304 → 64 → 1)  →  score_i
   ```

6. Đưa tất cả `score_i` qua masked softmax để có trọng số `α_i`, sau đó tổng
   hợp evidence:

   ```text
   o = α_1 h_1 + α_2 h_2 + ... + α_K h_K
   ```

7. Đưa `o` vào classifier cuối để dự đoán nhãn `True/False`.

## 3. Ví dụ nhỏ

Giả sử có ba path và vector mỗi path chỉ có ba chiều:

```text
h1 = [2, 0, 1]
h2 = [1, 3, 0]
h3 = [0, 0, 2]
```

Khi đó:

```text
c_set = [(2+1+0)/3, (0+3+0)/3, (1+0+2)/3]
      = [1, 1, 1]
```

Với mỗi path, V4 dùng cùng `c_claim` và `c_set`, nhưng thay `h_i` tương ứng:

```text
path 1: [c_claim ; c_set ; h1] → score_1
path 2: [c_claim ; c_set ; h2] → score_2
path 3: [c_claim ; c_set ; h3] → score_3
```

Ví dụ MLP sinh ra `[2.1, 0.8, -0.4]`; softmax có thể tạo trọng số
`[0.72, 0.24, 0.04]`. Khi đó path 1 đóng góp nhiều nhất vào vector evidence `o`.

## 4. Cách chạy

V4 phải train một checkpoint riêng vì scorer có đầu vào `3H`, khác V3 (`2H`).
Có thể giữ nguyên candidate artifact R3 và chỉ chạy lại bước train mô hình
V4 (BERT, attention và classifier); không cần chạy lại retrieval:

```bash
cd /home/namnx/duyanh/FactKG/with_evidence/classifier

python baseline.py \
  --data_path /home/namnx/duyanh/Data \
  --model_cls gearlite_v4 \
  --n_candid 5 \
  --skip_prepare_input \
  --train_candid_path /home/namnx/duyanh/FactKG/artifacts/faico_lite_top5/r3_full/train_candid_paths_r3_full.bin \
  --dev_candid_path /home/namnx/duyanh/FactKG/artifacts/faico_lite_top5/r3_full/dev_candid_paths_r3_full.bin \
  --test_candid_path /home/namnx/duyanh/FactKG/artifacts/faico_lite_top5/r3_full/test_candid_paths_top5_r3_full.bin \
  --max_paths 32 \
  --pair_batch_size 2 \
  --gradient_accumulation_steps 16 \
  --epoch 3 \
  --lr 5e-5 \
  --seed 42 \
  --amp \
  --run_name r3_full_v4 \
  --output_dir /home/namnx/duyanh/FactKG/artifacts/faico_lite_top5/r3_full/predictions_v4
```

Sau khi train, chọn checkpoint có `dev_acc` cao nhất rồi chạy test. So sánh
V4 với V3 trên cùng candidate artifact để biết lợi ích có thực sự đến từ
`c_set`, thay vì do retrieval hoặc số lượng path thay đổi.
