# Báo cáo 2/9: Đánh giá R2, R3 và kế hoạch chạy với GEARLite v2

## 1. Mục đích

R2 và R3 là hai thay đổi ở tầng tạo candidate path, lấy cảm hứng từ Faico-Lite. Mục tiêu là kiểm tra việc tạo thêm path có giúp nhóm `Multi-hop` hay không, đồng thời theo dõi ảnh hưởng lên `Negation` và các nhóm reasoning khác.

## 2. Định nghĩa các cấu hình

- **R1:** dùng độ dài hop `H` dự đoán, relation không lặp (`k=1`).
- **R2:** sinh path có độ dài từ `1` đến `H`, relation không lặp (`k=1`). Cấu hình này giữ được proof ngắn hơn số hop dự đoán.
- **R3:** dùng cấu hình R2 và cho phép một relation lặp tối đa hai lần (`k=2`). Ví dụ `r1 → r2 → r1` được giữ lại.

R2/R3 không phải là các model học riêng. Đây là các cấu hình của bộ dựng candidate path. Model kiểm chứng vẫn là GEARLite E2 (Pair + Attention).

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
| E2b: GEARLite v1 + retrieval cũ | 83.69% | 83.48% | **91.12%** | 71.18% | 82.82% | 94.37% | **87.98%** |
| R1: Faico-Lite, `k=1`, đúng độ dài `H` | 83.91% | 83.77% | 90.44% | 75.67% | **83.58%** | 94.37% | 79.98% |
| R2: Faico-Lite, `k=1`, path `1..H` | 84.54% | 84.42% | 90.80% | 78.28% | 83.51% | **94.48%** | 80.14% |
| R3: Faico-Lite, `k=2`, path `1..H` | **84.60%** | **84.49%** | 90.80% | **78.60%** | 83.51% | **94.48%** | 80.14% |
| **R3: Faico-Lite + GEARLite v2 Full** | **85.36%** | **85.24%** | **92.06%** | **79.78%** | 82.73% | **98.05%** | 81.28% |

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

## 4. Liên hệ với GEARLite v2

GEARLite v2 là phiên bản claim-conditioned attention chạy end-to-end trên R3 Full. Kết quả hiện có:

| Cấu hình | Overall Acc | Multi-hop Acc | Negation Acc |
|---|---:|---:|---:|
| E2b: GEARLite v1 + retrieval cũ | 83.69% | 71.18% | **87.98%** |
| GEARLite v2 + R3 Full | **85.36%** | **79.78%** | 81.28% |

V2 cải thiện Overall và Multi-hop, nhưng `Negation` vẫn thấp hơn E2b cũ. Hiện chưa có kết quả **GEARLite v2 + R2 (`k=1`)**, nên chưa biết việc bỏ relation lặp có giúp phục hồi Negation trong kiến trúc mới hay không.

## 5. Có nên chạy R2 với baseline mới không?

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

## 6. Cách chạy được khuyến nghị

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

## 7. Tiêu chí kết luận

- Nếu R2-V2 tăng `Negation` và vẫn giữ Multi-hop gần R3-V2: chọn R2 làm cấu hình cân bằng hơn.
- Nếu R2-V2 tăng Negation nhưng Multi-hop giảm nhiều: cân nhắc candidate budget thích nghi, ví dụ giảm path cho claim `H=1` và giữ nhiều path cho claim `H≥2`.
- Nếu R2-V2 không cải thiện Negation: nguyên nhân không chỉ nằm ở relation lặp. Khi đó mới xem xét attention có claim vector riêng hoặc ERNet một layer.
- Không nên kết luận ERNet cần thiết chỉ từ việc R3-V2 chưa phục hồi Negation; trước hết phải có mốc R2-V2 để tách ảnh hưởng của `k`.

## 8. Kết luận

R2 là thí nghiệm rất đáng chạy với GEARLite v2. Kết quả cũ cho thấy R2 đã mang phần lớn lợi ích Multi-hop của R3, còn `k=2` chỉ đem lại mức tăng nhỏ. Vì vậy, R2-V2 có khả năng là cấu hình ít nhiễu hơn cho `Negation` nhưng vẫn giữ được phần lớn lợi ích cho `Multi-hop`.

Thứ tự hợp lý là:

```text
R2 candidate với checkpoint V2 hiện tại
        ↓
đo 5 nhóm reasoning
        ↓
nếu có tín hiệu tốt thì train V2-R2 đầy đủ
        ↓
chỉ sau đó mới thử ERNet
```
