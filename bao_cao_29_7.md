# Bao cao 29/7: Faico-Lite x GEARLite E2

## Muc tieu

Tuan nay thu nghiem y tuong tu Faico o tang retrieval, khong thay doi relation
predictor, hop predictor hay kien truc GEARLite E2. Dau vao test cua ba run
giu co dinh top-5 relation, hop prediction, KG, `max_paths=32`, seed va
checkpoint E2 R1.

Faico-Lite thay heuristic traversal cu bang duyet KG co thu tu xac dinh: giu
serialized path rieng biet, khong chon tail ngau nhien va uu tien `connected`
truoc `walkable`. De phu hop voi E2, artifact chi luu toi 32 path ma model co
the encode; khi da du 32 connected path, retrieval dung som cho claim do.

## Ba cau hinh candidate path

| Run | Candidate path test | Cach danh gia |
|---|---|---|
| R1 | Dung do dai hop H du doan, relation khong lap (`k=1`) | Train E2 tren candidate R1, chon best dev checkpoint, test R1 |
| R2 | Sinh path do dai 1 den H, `k=1` | Dung checkpoint R1, chi thay candidate test |
| R3 | R2 + moi relation duoc lap toi 2 lan (`k=2`) | Dung checkpoint R1, chi thay candidate test |

R2 va R3 la retrieval ablation: test claim, label va model giong R1. Chi
evidence path dua vao E2 thay doi, nen chenh lech diem phan anh tac dong cua
quy tac sinh/loc candidate path.

## Du lieu va checkpoint R1

- Candidate R1 da tao xong cho train (86,367), dev (13,266) va test (9,041).
- Retrieval report: artifact luu 1,745,603 path train, 251,585 path dev va
  154,200 path test sau gioi han top-32.
- E2 train toi da 5 epoch, seed 42; best checkpoint la epoch 0 voi Dev Acc
  `0.9408`. R2/R3 dung dung checkpoint nay.

## Ket qua test

| Run | Best dev Acc | Test Acc | Test Macro-F1 | Multi-hop Acc | Multi-hop Macro-F1 |
|---|---:|---:|---:|---:|---:|
| R1 | 0.9408 | 0.8391 | 0.8377 | 0.7567 | 0.7483 |
| R2 | Dung checkpoint R1 | 0.8454 | 0.8442 | 0.7828 | 0.7773 |
| R3 | Dung checkpoint R1 | 0.8460 | 0.8449 | 0.7860 | 0.7808 |

| Reasoning type | R1 Acc / F1 | R2 Acc / F1 | R3 Acc / F1 |
|---|---:|---:|---:|
| One-hop | 0.9044 / 0.9043 | 0.9080 / 0.9079 | 0.9080 / 0.9079 |
| Multi-hop | 0.7567 / 0.7483 | 0.7828 / 0.7773 | 0.7860 / 0.7808 |
| Conjunction | 0.8358 / 0.8283 | 0.8351 / 0.8278 | 0.8351 / 0.8278 |
| Existence | 0.9437 / 0.9437 | 0.9448 / 0.9448 | 0.9448 / 0.9448 |
| Negation | 0.7998 / 0.7983 | 0.8014 / 0.7999 | 0.8014 / 0.7999 |

## Danh gia

- R2 tang so voi R1: Test Acc `+0.0063`, Macro-F1 `+0.0065`; multi-hop tang
  manh nhat, Acc `+0.0261` va Macro-F1 `+0.0290`.
- R3 la ket qua tot nhat: so voi R1, Test Acc `+0.0069`, Macro-F1 `+0.0072`;
  multi-hop Acc `+0.0293` va Macro-F1 `+0.0325`.
- R3 hon R2 chu yeu o multi-hop (`+0.0032` Acc, `+0.0035` F1), trong khi cac
  reasoning type khac giu gan nhu nguyen. Dieu nay phu hop voi gia thuyet
  path ngan hon va relation lap co the khoi phuc proof path bi bo sot, thay vi
  tao nhieu nhieu cho cac case don gian.

Artifact, retrieval report va prediction duoc luu tai
`artifacts/faico_lite_top5/r1`, `r2` va `r3`.

---

# Báo cáo việc tuần này

## R3: kết hợp Faico-Lite retrieval với GEAR-Lite E2 để cải thiện Multi-hop

### 1. Mục tiêu tuần này

Ở lượt trước, **E2 (Pair + Attention / GEAR-Lite)** đã cải thiện cách verifier
đọc evidence: BERT encode riêng từng cặp `Claim–Path`, sau đó Attention đặt trọng
số lớn hơn cho path hữu ích. Tuy nhiên E2 chỉ có thể chọn trong candidate path
đã được retrieval sinh ra; nếu proof multi-hop bị bỏ sót từ trước thì Attention
không thể tự tạo lại proof đó.

Mục tiêu của tuần này là giữ nguyên E2, nhưng cải thiện tầng sinh candidate path
theo ý tưởng **structural completeness** của Faico: giữ các graph path hợp lệ và
alternative proof tốt hơn trước khi đưa chúng vào Attention.

### 2. R3 gồm những gì? — ý tưởng Faico và flow đầy đủ

#### 2.1. R3 lấy cụ thể gì từ Faico?

R3 chỉ lấy **hai ý tưởng retrieval** của Faico:

1. **Giữ path hợp lệ về cấu trúc.** R3 chỉ đi theo các cạnh thật trong KG, không
   chọn tail ngẫu nhiên và giữ các path thay thế thay vì chỉ giữ một path cùng
   endpoint. Mục đích là giảm khả năng bỏ sót proof multi-hop trước khi E2/BERT
   kịp đọc nó.

2. **Relation budget của k-BET.** R3 cho phép một relation xuất hiện tối đa hai
   lần trong một path (`k=2`); vì vậy `r1 → r2 → r1` không bị loại chỉ vì `r1`
   lặp lại. Mục đích là giữ các proof multi-hop hợp lệ có lặp loại relation, nhưng
   vẫn giới hạn số path để graph search không nở quá lớn.

R3 **không dùng** LLM, token-trie, reasoning LLM hay cơ chế budget-dominance để
prune của Faico. Việc chọn relation vẫn do các model FactKG có sẵn thực hiện.

#### 2.2. R3 làm gì để tạo path đưa vào E2/BERT?

Sau khi train xong hai model retrieval của FactKG, R3 chạy theo các bước sau,
trước khi E2/BERT nhận input:

1. **Lấy đầu ra retrieval của FactKG.** Với mỗi claim, relation predictor cho
   5 relation liên quan nhất; hop predictor cho `H`, là số cạnh tối đa của path.
   Mục đích: thu hẹp KG rất lớn thành vùng relation và độ sâu đáng tìm.

   `H` không được R3 đặt cố định là 3. Code đọc `H` riêng cho từng claim từ
   `predictions_hop.json`; cấu hình hop predictor hiện có 3 nhãn nên dự đoán
   `H` từ 1 đến 3. Chỉ khi claim có `H=3`, R3 mới xét path dài 1, 2 hoặc 3 cạnh.
   `top-5` là số relation, không phải số hop.

2. **Tạo các relation chain có thể dùng.** R3 sinh chain dài từ 1 đến `H`; một
   relation được lặp tối đa hai lần (`k=2`). Mục đích: không bỏ proof ngắn hơn
   dự đoán hoặc proof dạng `r1 → r2 → r1`.

3. **Duyệt KG để biến relation chain thành path thật.** R3 bắt đầu từ entity của
   claim, chỉ đi theo edge thật trong KG, duyệt ổn định và giữ full serialized
   path. Mục đích: path đưa vào model phải có thật trong KG; không mất path vì
   chọn tail ngẫu nhiên hoặc vì một path khác có cùng endpoint.

4. **Tạo candidate artifact cho BERT.** R3 xếp path nối các entity trong claim
   vào nhóm `connected`, các path hợp lệ khác vào `walkable`; lấy `connected`
   trước rồi tới `walkable`, tối đa 32 path mỗi claim. Mục đích: ưu tiên path có
   khả năng làm proof nhưng vẫn giữ input vừa với GPU/BERT.

5. **Lưu candidate path.** Artifact này là đầu vào cho E2: mỗi path được ghép
   riêng với claim để BERT encode. R3 không biết path nào là đúng; nó chỉ tạo tập
   path hợp lệ gồm cả path hữu ích và path nhiễu. Attention của E2 mới học cách
   đặt trọng số cao/thấp cho từng path.

`H` là số cạnh tối đa của cả path; `k=2` là số lần tối đa của một relation trong
path. Hai giới hạn này khác nhau.

**Ví dụ ngắn.** Claim có hai entity `A` và `C`; FactKG dự đoán `r1, r2, r3, ...`
và `H=3`. R3 thử các chain như `r1`, `r1 → r2`, `r1 → r2 → r1` (được vì `k=2`),
rồi kiểm tra chúng có đi được thật từ `A` trong KG không. Nếu tìm được
`A →r1 B →r2 C`, path này vào nhóm `connected` vì nó nối hai entity của claim.
Nếu path không kết thúc ở `C` nhưng vẫn hợp lệ, nó vào `walkable`. Sau khi giữ tối
đa 32 path, E2/BERT đọc từng path riêng và tự quyết định path nào hữu ích.

Lưu ý về kết quả đang báo cáo: R3 hiện chỉ thay artifact **test** để so sánh
retrieval bằng cùng checkpoint E2-R1. Nếu train E2 end-to-end với R3 ở lượt sau,
cần tạo artifact R3 cho train/dev/test rồi mới train checkpoint E2-R3 riêng.

#### 2.3. Flow đầy đủ: phần FactKG, phần R3 và phần E2

```text
FactKG retrieval đã train
→ dự đoán top-5 relation và H cho claim
→ R3 sinh/lưu tối đa 32 candidate path hợp lệ
→ E2/BERT đọc từng Claim–Path và dự đoán True / False
```

Nói cách khác: **FactKG nói “tìm relation nào, sâu bao nhiêu”; R3 tìm và giữ
path; E2 đọc path để kiểm chứng claim.**

#### 2.4. Vì sao R2/R3 không train lại E2 trong kết quả hiện tại?

Có, E2 vẫn phải được train ít nhất một lần. Trong báo cáo hiện tại, chỉ có một
checkpoint E2: checkpoint tốt nhất được train trên candidate train/dev của R1.
R2 và R3 **không có checkpoint E2 riêng**; cả ba dùng cùng trọng số E2, chỉ thay
candidate path ở test:

```text
Candidate train/dev R1 → train E2 một lần → checkpoint E2-R1
                                                ├─ test candidate R1
                                                ├─ test candidate R2
                                                └─ test candidate R3
```

Mục đích là so sánh retrieval công bằng: cùng BERT/E2, nếu R3 tốt hơn thì chênh
lệch đến từ candidate path, không phải do lần train khác hay random seed khác.

Tuy nhiên, nếu mục tiêu là lấy **điểm end-to-end tốt nhất của R3**, thì nên làm
một thí nghiệm tiếp theo: sinh train/dev/test candidate theo cùng quy tắc R3,
train E2 riêng, chọn checkpoint bằng dev và chỉ test cuối cùng một lần. Không
nên gọi kết quả hiện tại là kết quả end-to-end cuối cùng; nó là retrieval ablation
để chứng minh path R3 có ích.

### 3. R3 cải tiến gì so với E2 chạy trước đó?

| Thành phần | E2 trước đó | R3 tuần này |
|---|---|---|
| Verifier | Pair BERT + masked Attention + MLP | **Giữ nguyên** Pair BERT + masked Attention + MLP |
| Relation / hop predictor | Top-5 relation và hop prediction | **Giữ nguyên** |
| Candidate path | Path do retrieval cũ sinh ra | Faico-Lite traversal, giữ path đầy đủ và xác định hơn |
| Độ dài path | Theo candidate cũ | Cho phép độ dài từ `1` đến `H` |
| Relation lặp | Không cho lặp (`k=1`) | R3 cho phép mỗi relation lặp tối đa hai lần (`k=2`) |
| Số path vào BERT | Tối đa 32 path | **Giữ nguyên** tối đa 32 path |

Nói ngắn gọn: **E2 giải quyết “trong các path đang có, path nào đáng tin hơn?”**;
R3 bổ sung bước **“làm sao để path đúng có cơ hội xuất hiện trong các path đó?”**.
R3 không phải một classifier mới. Đây là E2 cũ, nhưng được kiểm tra với candidate
path tốt hơn từ retrieval.

### 4. Kết quả của cấu hình R3 hoàn chỉnh

| Cấu hình | Test Acc | Test Macro-F1 | Multi-hop Acc | Multi-hop Macro-F1 |
|---|---:|---:|---:|---:|
| **R3: Faico-Lite retrieval + E2** | **84.60%** | **84.49%** | **78.60%** | **78.08%** |

Kết quả này là của **toàn bộ công thức R3**: traversal đầy đủ hơn, path `1..H`,
relation budget `k=2` và E2 Attention. Vì các thành phần được kết hợp, bảng
này dùng để trả lời câu hỏi thực tế: “R3 có tốt hơn baseline E2 cũ hay không?”

### 5. So sánh với baseline E2 trước đó

Baseline phù hợp để đối chiếu là **E2b: Pair + Attention, 3-hop, top-5 relation**
trong `báo cáo 15_7.md`. Đây là bản chỉ cải tiến verifier bằng Attention, chưa
có Faico-Lite candidate retrieval.

| Mô hình / cấu hình | Test Acc | Test Macro-F1 | Multi-hop Acc | Multi-hop Macro-F1 |
|---|---:|---:|---:|---:|
| E0 cũ: Concat, top-5 | 81.80% | — | 68.84% | — |
| E2b trước đó: Pair + Attention, top-5 | 84.23% | 83.48% | 72.18% | 70.00% |
| **R3: Faico-Lite retrieval + E2, top-5** | **84.60%** | **84.49%** | **78.60%** | **78.08%** |

So với E2b trước đó, R3 tăng `+0.37` điểm Overall Accuracy, `+1.01` điểm Overall
Macro-F1, và quan trọng nhất là tăng **Multi-hop Accuracy `+6.42` điểm** cùng
**Multi-hop Macro-F1 `+8.08` điểm**. So với Concat baseline E0, R3 tăng
Multi-hop Accuracy từ `68.84%` lên `78.60%` (`+9.76` điểm).

Diễn giải đúng: R3 so với E2b là **so sánh hai hệ thống ở hai đợt thực nghiệm**,
nên không được xem là bằng chứng nhân quả tuyệt đối nếu candidate artifact
train/dev hoặc các điều kiện chạy cũ không trùng khít. Tuy vậy, vì R3 giữ nguyên
relation predictor, hop predictor, kiến trúc E2 và giới hạn 32 path, khác biệt
chính có cơ sở là candidate retriever lấy cảm hứng từ Faico. Kết luận an toàn là:
Faico-Lite retrieval kết hợp với E2 đã cải thiện rõ nhóm Multi-hop.

### 6. Kết luận ngắn để trình bày

> R3 giữ nguyên E2 Attention, nhưng thay candidate retriever bằng một công thức
> lấy cảm hứng từ Faico: duyệt path có cấu trúc đầy đủ hơn, cho phép path dài từ
> 1 đến H và cho phép một relation lặp tối đa hai lần. Kết quả R3 đạt Multi-hop
> Accuracy 78.60%, cao hơn E2 top-5 trước đó 6.42 điểm và cao hơn Concat baseline
> 9.76 điểm. Điều này ủng hộ giả thuyết rằng bottleneck Multi-hop không chỉ ở
> classifier mà còn ở việc proof path có được retrieval giữ lại hay không.
