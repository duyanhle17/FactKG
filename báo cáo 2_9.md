# Báo cáo 2/9: Đánh giá R2, R3 và GEARLite v2/v3/v4

## 1. Mục đích

R2 và R3 là hai thay đổi ở tầng tạo candidate path, lấy cảm hứng từ Faico-Lite. Mục tiêu là kiểm tra việc tạo thêm path có giúp nhóm `Multi-hop` hay không, đồng thời theo dõi ảnh hưởng lên `Negation` và các nhóm reasoning khác.

## 2. Định nghĩa các cấu hình

- **R1:** dùng độ dài hop `H` dự đoán, relation không lặp (`k=1`).
- **R2:** sinh path có độ dài từ `1` đến `H`, relation không lặp (`k=1`). Cấu hình này giữ được proof ngắn hơn số hop dự đoán.
- **R3:** dùng cấu hình R2 và cho phép một relation lặp tối đa hai lần (`k=2`). Ví dụ `r1 → r2 → r1` được giữ lại.

R2/R3 không phải là các model học riêng. Đây là các cấu hình của bộ dựng candidate path. Model kiểm chứng được thử qua các phiên bản GEARLite v2, v3 và v4.

## 2.1. Phân biệt hai mốc baseline

Ảnh kết quả bạn cung cấp là số liệu trong paper FactKG:

```text
With Evidence – GEAR
One-hop 83.23% | Conjunction 77.68% | Existence 81.61%
Multi-hop 68.84% | Negation 79.41% | Total 77.65%
```

Đây là **baseline được paper công bố**.

Các số `E0 = 81.80%` xuất hiện trong các báo cáo thực nghiệm trước là **kết quả chạy lại trong repo**, dùng cấu hình Concat, top-5 relation và 3-hop. Đây là mốc local reproduction để so sánh các phiên bản E2/R2/R3 cùng pipeline, không được gọi là kết quả baseline gốc của paper.

Vì hai mốc có thể dùng thiết lập và pipeline khác nhau, so sánh R2/R3 với `77.65%` chỉ mang tính tham khảo. Phép so sánh kiểm soát chính trong báo cáo này vẫn là R1–R3 trong cùng đợt chạy local.

## 3. Kết quả R2 và R3 trước đây

Trong thí nghiệm ngày 29/7, E2 chỉ được train một lần trên candidate R1. Sau đó dùng cùng checkpoint E2-R1 để test candidate R2 và R3. Vì vậy, đây là **retrieval ablation**: thay đổi candidate test, giữ nguyên model verifier.

| Cấu hình | Best dev Acc | Test Acc | Test Macro-F1 | Multi-hop Acc | Multi-hop Macro-F1 |
|---|---:|---:|---:|---:|---:|
| R1 | 0.9408 | 83.91% | 83.77% | 75.67% | 74.83% |
| R2 (`k=1`, path `1..H`) | Dùng checkpoint R1 | **84.54%** | **84.42%** | **78.28%** | **77.73%** |
| R3 (`k=2`) | Dùng checkpoint R1 | **84.60%** | **84.49%** | **78.60%** | **78.08%** |

### So sánh đủ năm nhóm reasoning với E2b

E2b là GEARLite v1 (Pair + Attention) chạy với retrieval cũ, top-5 relation. E2b không dùng Faico-Lite R1/R2/R3, nên đây không phải ablation hoàn toàn cùng candidate set; tuy vậy nó là mốc cần có để thấy trade-off giữa Multi-hop và Negation.

| Cấu hình | Overall Acc | Overall Macro-F1 | One-hop Acc | Multi-hop Acc | Conjunction Acc | Existence Acc | Negation Acc |
|---|---:|---:|---:|---:|---:|---:|---:|
| E2b: GEARLite v1 + retrieval cũ | 83.69% | 83.48% | 91.12% | 71.18% | **82.82%** | 94.37% | 87.98% |
| R1: Faico-Lite, `k=1`, đúng độ dài `H` | 83.91% | 83.77% | 90.44% | 75.67% | **83.58%** | 94.37% | 79.98% |
| R2: Faico-Lite, `k=1`, path `1..H` | 84.54% | 84.42% | 90.80% | 78.28% | 83.51% | **94.48%** | 80.14% |
| R3: Faico-Lite, `k=2`, path `1..H` | **84.60%** | **84.49%** | 90.80% | **78.60%** | 83.51% | **94.48%** | 80.14% |
| **R3: Faico-Lite + GEARLite v2 Full** | **85.36%** | **85.24%** | **92.06%** | **79.78%** | 82.73% | **98.05%** | 81.28% |
| **R3: Faico-Lite + GEARLite v3 (claim riêng)** | 85.33% | 85.17% | 91.80% | 78.82% | 81.43% | 93.22% | **89.12%** |
| **R3: Faico-Lite + GEARLite v4 (lai)** | **86.74%** | **86.63%** | 91.64% | **81.16%** | **84.03%** | 94.94% | 88.43% |

Theo từng nhóm reasoning của R1/R2/R3:

| Nhóm | R1 Acc | R2 Acc | R3 Acc |
|---|---:|---:|---:|
| One-hop | 90.44% | 90.80% | 90.80% |
| Multi-hop | 75.67% | **78.28%** | **78.60%** |
| Conjunction | 83.58% | 83.51% | 83.51% |
| Existence | 94.37% | **94.48%** | **94.48%** |
| Negation | 79.98% | **80.14%** | **80.14%** |

R2 tăng rõ so với R1 ở `Multi-hop` (+2.61 điểm phần trăm). R3 chỉ tăng thêm 0.32 điểm ở `Multi-hop` so với R2, trong khi `Negation` không thay đổi. Điều này cho thấy lợi ích lớn hơn đến từ việc giữ path ngắn `1..H`; việc cho relation lặp `k=2` chỉ đem lại lợi ích nhỏ trong thí nghiệm này.

R3 + GEARLite v2 Full tăng tiếp so với R3 + E2: Overall `+0.76`, Multi-hop `+1.18`, One-hop `+1.26`, Existence `+3.57` và Negation `+1.14` điểm phần trăm. Tuy nhiên, đây là bản được train end-to-end trên candidate R3, nên không được xem là retrieval ablation thuần túy như R1/R2/R3 cũ.

## 4. Kết quả GEARLite v2, v3 và v4 trên R3 Full

GEARLite v2, v3 và v4 đều train end-to-end trên cùng candidate artifact R3 Full, top-5 relation, `max_paths=32`, `pair_max_length=128`, seed 42. Khác biệt cần xét là cách tạo tín hiệu cho attention:

- **v2:** lấy `c = mean(h_1, ..., h_K)`, tức vector ngữ cảnh claim được suy ra từ trung bình các pair Claim–Path.
- **v3:** encode riêng Claim để lấy `c`; attention chấm từng path dựa trên cả `c` và `h_i`.
- **v4:** kết hợp Claim encode riêng, trung bình candidate set và path hiện tại: `score_i = MLP([c_claim ; c_set ; h_i])`.

| Cấu hình | Overall Acc | Overall Macro-F1 | One-hop Acc | Multi-hop Acc | Conjunction Acc | Existence Acc | Negation Acc |
|---|---:|---:|---:|---:|---:|---:|---:|
| E2b: GEARLite v1 + retrieval cũ | 83.69% | 83.48% | 91.12% | 71.18% | **82.82%** | 94.37% | 87.98% |
| GEARLite v2 + R3 Full | **85.36%** | **85.24%** | **92.06%** | **79.78%** | **82.73%** | **98.05%** | 81.28% |
| GEARLite v3 + R3 Full | 85.33% | 85.17% | 91.80% | 78.82% | 81.43% | 93.22% | **89.12%** |
| **GEARLite v4 + R3 Full** | **86.74%** | **86.63%** | 91.64% | **81.16%** | **84.03%** | 94.94% | 88.43% |

Kết quả chi tiết của **v3**: One-hop `91.80%` / F1 `91.78%`; Multi-hop `78.82%` / F1 `78.26%`; Conjunction `81.43%` / F1 `80.36%`; Existence `93.22%` / F1 `93.22%`; Negation `89.12%` / F1 `89.10%`; Total `85.33%` / Macro-F1 `85.17%`.

Kết quả chi tiết của **v4**: One-hop `91.64%` / F1 `91.62%`; Multi-hop `81.16%` / F1 `80.84%`; Conjunction `84.03%` / F1 `83.32%`; Existence `94.94%` / F1 `94.94%`; Negation `88.43%` / F1 `88.43%`; Total `86.74%` / Macro-F1 `86.63%`.

So với v2 trên **cùng R3 Full**, v3 thay đổi như sau: One-hop `-0.26`, Multi-hop `-0.96`, Conjunction `-1.30`, Existence `-4.83`, Negation `+7.84`, Overall `-0.03` điểm phần trăm. Nghĩa là vector Claim độc lập đã phục hồi Negation rất mạnh, còn Overall gần như không đổi vì tổn thất lớn ở Existence bù lại phần tăng đó.

Quy về số ví dụ gần đúng: v3 đúng thêm khoảng `103/1314` ví dụ Negation, nhưng sai thêm khoảng `42/870` Existence, `40/3069` Conjunction, `18/1874` Multi-hop và `5/1914` One-hop. Do đó lợi ích Negation gần như bị triệt tiêu trong Total; đây không phải trường hợp “mọi nhóm đều giảm”.

So với E2b (retrieval cũ), v3-R3 vẫn hơn rõ ở Multi-hop (`+7.64`) và hơn ở Negation (`+1.14`), nhưng thấp hơn ở Conjunction (`-1.39`) và Existence (`-1.15`). So sánh này chỉ mang tính tham khảo vì candidate set của E2b khác R3.

V4 cải thiện so với v2 trên cùng R3 Full ở Overall `+1.38`, Multi-hop `+1.38` và Conjunction `+1.30` điểm phần trăm; Existence vẫn thấp hơn v2 `3.11` điểm, còn Negation tăng `7.15` điểm. So với v3, V4 tăng Overall `1.41`, Multi-hop `2.34`, Conjunction `2.60` và Existence `1.72` điểm; Negation giảm nhẹ `0.69` điểm nhưng vẫn đạt `88.43%`. So với E2b, V4 tăng Overall `3.05` và Multi-hop `9.98` điểm phần trăm.

Kết quả này cho thấy việc bổ sung `c_set` vào Claim riêng đã giúp v4 phục hồi phần lớn Existence/Conjunction của v3, đồng thời giữ Negation ở mức cao. V4 hiện là cấu hình có Overall Accuracy và Multi-hop cao nhất trong các thí nghiệm local.

### Vì sao Existence giảm?

Đây chưa phải kết luận nguyên nhân, nhưng có hai giả thuyết phù hợp với kết quả hiện tại:

1. **Khác biệt nằm ở attention, không phải R3.** V2 và v3 dùng cùng artifact R3 Full. Vì vậy việc Existence giảm `4.83` điểm không thể quy trực tiếp cho retrieval mới; nó xảy ra khi thay `c = mean(h_i)` của v2 bằng vector Claim encode riêng trong v3.
2. **Existence thường cần một bằng chứng trực tiếp, ngắn và quyết định.** Ngữ cảnh tập candidate của v2 (`mean(h_i)`) có thể giúp attention nhận ra sự hiện diện của path trực tiếp đó. V3 chấm từng path theo Claim độc lập; với candidate R3 có nhiều path hợp lệ nhưng nhiễu, attention có thể dồn trọng số sang path nghe giống claim nhưng không phải bằng chứng tồn tại mạnh nhất. Đây là giả thuyết cần kiểm tra bằng attention weight và prediction, không phải khẳng định từ Accuracy.

Mức giảm này tương đương khoảng **43/870** ví dụ Existence, nên cũng cần chạy thêm seed trước khi kết luận kiến trúc v3 thật sự kém ở nhóm này.

## 5. Cần kiểm tra gì trước ERNet?

**Chưa nên chạy ERNet ngay.** V4 đã đưa Multi-hop lên `81.16%`, Conjunction lên `84.03%` và Existence lên `94.94%`, đồng thời giữ Negation ở `88.43%`. Vì vậy cần xác nhận độ ổn định của v4 trước; chưa có bằng chứng rằng thiếu message passing giữa các path là nút thắt chính.

Ưu tiên theo thứ tự:

1. **Đã thử attention lai v4:** giữ Claim encode riêng và bổ sung `mean(h_i)` của candidate set vào scorer. V4 đã tăng Overall, Multi-hop, Conjunction và Existence so với v3; đây là bằng chứng thực nghiệm ủng hộ giả thuyết mất ngữ cảnh candidate set ở v3.
2. **Chạy v4 với seed 43** để kiểm tra kết quả `86.74%` không chỉ do seed 42. Nếu cần phân tích sâu hơn, mới lưu attention weight và đối chiếu các path ở những mẫu v4 sai.
3. **Sau đó mới so sánh candidate path/R2:** nếu v4 vẫn ổn định nhưng cần tách ảnh hưởng relation lặp, chạy R2 với cùng kiến trúc và hyperparameter.

Sau ba bước trên, chỉ thử ERNet nếu candidate/path proof vẫn đủ mà các claim Multi-hop cần ghép quan hệ còn sai có hệ thống.

## 6. Có nên chạy R2 với baseline mới không?

**Có, nên chạy.** Đây là thí nghiệm cần thiết vì hiện tại ta đang so sánh:

```text
GEARLite v2 + R3 (k=2)
```

nhưng chưa có mốc:

```text
GEARLite v2 + R2 (k=1)
```

Nếu chỉ nhìn V2-R3, không thể biết Negation giảm do:

- R3 cho phép relation lặp;
- số lượng candidate path tăng;
- candidate có nhiều path nhiễu;
- hay do chính claim-conditioned attention.

R2-V2 sẽ cung cấp phép đối chứng trực tiếp với R3-V2: cùng kiến trúc, cùng dữ liệu và cùng cách train, chỉ thay `k=2` thành `k=1`.

## 7. Cách chạy được khuyến nghị

### Bước 1: Tạo candidate R2

Giữ nguyên top-5 relation, hop prediction, KG và `max_paths=32`. Chỉ đổi:

```text
include_shorter_paths = True
relation_budget = 1
```

Kết quả được lưu thành artifact riêng, không ghi đè R3.

### Bước 2: Kiểm tra nhanh

Dùng checkpoint GEARLite v2 hiện có để test candidate R2 mới:

```text
R2 candidate (k=1) → checkpoint GEARLite v2 hiện tại → test
```

Cách này trả lời nhanh liệu candidate ít path lặp có giúp Negation hay không.

### Bước 3: Đánh giá chính thức

Nếu kết quả kiểm tra nhanh có tín hiệu tốt, chạy đầy đủ:

```text
R2 candidate train/dev/test → train GEARLite v2 mới → chọn checkpoint dev → test
```

Sau đó so sánh trực tiếp:

```text
GEARLite v2 + R2 (k=1)
GEARLite v2 + R3 (k=2)
```

Nên giữ cùng seed, `pair_max_length=128`, `max_paths=32`, learning rate và số epoch.

## 8. Tiêu chí kết luận

- Nếu R2-V2 tăng `Negation` và vẫn giữ Multi-hop gần R3-V2: chọn R2 làm cấu hình cân bằng hơn.
- Nếu R2-V2 tăng Negation nhưng Multi-hop giảm nhiều: cân nhắc candidate budget thích nghi, ví dụ giảm path cho claim `H=1` và giữ nhiều path cho claim `H≥2`.
- Nếu R2-V2 không cải thiện Negation: nguyên nhân không chỉ nằm ở relation lặp. Kết quả v3 cho thấy attention có Claim riêng là hướng có triển vọng cho Negation, nhưng cần kiểm tra trade-off Existence trước.
- Không nên kết luận ERNet cần thiết chỉ từ một cấu hình; trước hết cần kiểm tra độ ổn định theo seed và lỗi Existence của v3.

## 9. Kết luận

V4 hiện là cấu hình tốt nhất trong các thí nghiệm local: Overall `86.74%`, Multi-hop `81.16%` và Negation `88.43%`. Kết quả này ủng hộ việc kết hợp Claim riêng với ngữ cảnh toàn candidate set. Tuy vậy, cần chạy thêm seed 43 trước khi kết luận đây là cải thiện ổn định; R2-V2 vẫn có thể được dùng sau đó nếu cần tách riêng ảnh hưởng của `k=2`.

Thứ tự hợp lý lúc này là:

```text
chạy v4 seed 43 để xác nhận độ ổn định
        ↓
so sánh v4 với R2/V2 nếu cần tách ảnh hưởng candidate
        ↓
chỉ sau đó mới thử ERNet
```

## 10. Tổng quan các lần cần thử

Để tránh vừa đổi retrieval vừa đổi verifier, các lượt dưới đây đều giữ nguyên
candidate artifact **R3 Full**, top-5 relation và `K=32`; chỉ thay cách
attention tạo score cho path.

1. **R3 + GEARLite v2 — đã chạy.**
   `c_set = mean(h_1, ..., h_K)` là tóm tắt của toàn candidate set. Đây là
   mốc hiện tốt nhất về Overall (`85.36%`) và Existence (`98.05%`).

2. **R3 + GEARLite v3 — đã chạy.**
   `c_claim = BERT(Claim)` được encode riêng. V3 tăng Negation lên `89.12%`,
   nhưng Existence giảm còn `93.22%`; Overall gần như không đổi (`85.33%`).

3. **R3 + GEARLite v4 lai — đã chạy.**
   V4 dùng cả hai tín hiệu:

   ```text
   score_i = MLP([c_claim ; c_set ; h_i])
   ```

   Mục tiêu: giữ lợi ích Negation của v3, đồng thời trả lại ngữ cảnh candidate
   set để phục hồi Existence/Conjunction. V4 đạt Overall `86.74%`, Multi-hop
   `81.16%`, Conjunction `84.03%`, Existence `94.94%` và Negation `88.43%`.
   Không cần chạy lại R3 hay retrieval.

4. **Bước tiếp theo nên là chạy v4 với seed 43.**
   V4 đã có tín hiệu tốt, nên thêm một seed để kiểm tra kết quả không hoàn toàn
   do ngẫu nhiên trước khi kết luận cấu hình cuối.

5. **Sau khi xác nhận seed, mới kiểm tra candidate path hoặc R2 (`k=1`) nếu
   cần tách ảnh hưởng của relation lặp.** ERNet chỉ là bước sau cùng, khi
   candidate đã đủ proof nhưng các claim cần kết hợp path vẫn sai.
