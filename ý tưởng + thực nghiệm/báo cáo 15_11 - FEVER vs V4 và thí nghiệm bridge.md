# Báo cáo 15–17/11/2026: FEVER BERT với R3/V4, thí nghiệm bridge và kết quả P2

> Phần thực nghiệm P0, P1, P2 của kế hoạch trong [báo cáo 11/11](báo%20cáo%2011_11.md), mục "Brainstorm".
>
> **Dev và test dùng vào việc gì:**
> - **Dev** (13.266 claim) dùng để **chọn**: chọn epoch tốt nhất khi train, và chọn hướng thí nghiệm (P0, P1).
> - **Test** (9.041 claim) là **điểm báo cáo**: chỉ chạy một lần cho cấu hình đã khóa từ trước. Con số 92,60% của FEVER trước đây cũng là điểm test.
>
> Mọi so sánh với paper khác đều dùng **test**.

## Bảng điểm cuối (test, 9.041 claim)

**Cấu hình P2 (`bridge5`):** BERT-base fine-tune từ đầu, giống hệt baseline, gồm batch 4, LR 5e-6, tối đa 10 epoch và chọn epoch theo dev. Khác biệt duy nhất nằm ở input: ngoài one-hop, mỗi claim có thêm tối đa 5 đường nối 2–3 hop giữa các entity, tự tìm trong KG và không dùng evidence vàng. Cấu hình được khóa trước khi chạy test. Epoch được chọn là epoch 10, dev 94,92%.

**Theo 5 nhóm** (taxonomy dùng trong Opsahl và TrustFV):

| Nhóm | n | FEVER baseline (của mình) | **P2 bridge5** | Δ | Opsahl 2024 | TrustFV 2026 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| One-hop | 1.914 | 95,51 | **97,34** | +1,83 | 97,40 | 89,13 |
| **Multi-hop** | 1.874 | 80,68 | **93,60** | **+12,91** | 80,32 | 88,14 |
| Conjunction (multi-claim) | 3.069 | 97,13 | 96,58 | −0,55 | 97,51 | 87,12 |
| Existence | 870 | 97,36 | 97,24 | −0,11 | 97,31 | 96,00 |
| Negation | 1.314 | 91,63 | 90,79 | −0,84 | 92,54 | 88,63 |
| **Overall** | **9.041** | **92,60** (8.372 câu đúng) | **95,34** (8.620) | **+2,74** | 93,49 | 90,07 |

**Theo 6 tag** (cách chia của FEVER 2026, do `run_stuff.py` in ra; một claim có thể mang nhiều tag):

| Tag | FEVER baseline | **P2 bridge5** | Δ |
| --- | ---: | ---: | ---: |
| single hop | 96,28 | 96,25 | −0,03 |
| **multi hop** | 80,22 | **92,28** | **+12,06** |
| multi claim | 96,42 | 95,26 | −1,16 |
| existence | 97,61 | 97,38 | −0,23 |
| negation | 91,63 | 90,79 | −0,84 |
| substitution | 92,57 | 95,25 | +2,68 |
| **Overall** | **92,60** | **95,34** | **+2,74** |

Bài báo FEVER 2026 báo cáo overall 92,68%, multi-hop 80,08%.

**Đọc bảng:**

- **Overall 95,34%**: cao hơn mốc tốt nhất đã biết là Opsahl (93,49%) **1,85 điểm**, và cao hơn baseline của mình **2,74 điểm**. So từng câu với baseline: 476 câu từ sai thành đúng, 228 câu từ đúng thành sai, McNemar p = 5e-21.
- **Multi-hop 93,60%**: nhóm khó nhất trước đây (mọi encoder đều dừng ở khoảng 80%) giờ ngang các nhóm khác. Con số này cao hơn TrustFV (88,14%, dùng LLM 8B, 10–39 s/claim) **5,5 điểm**, trong khi P2 suy luận mất **7 ms/claim**.
- **Các nhóm còn lại gần như giữ nguyên**: one-hop tăng; conjunction, existence và negation giảm dưới 1 điểm, và **các mức giảm theo nhóm đều không có ý nghĩa thống kê** (p ≥ 0,2). Chi tiết theo nhãn và những điểm cần thận trọng nằm ở mục 8.

**Các chỉ số trong báo cáo:**

| Chỉ số | Ý nghĩa |
| --- | --- |
| Accuracy dev / test | Tỷ lệ đoán đúng trên dev (dùng để chọn epoch và chọn hướng) / trên test (điểm báo cáo, so với paper khác) |
| 5 nhóm và 6 tag | **5 nhóm** loại trừ nhau, mỗi claim thuộc đúng 1 nhóm theo thứ tự ưu tiên negation > one-hop (`num1`) > multi-hop > conjunction (`multi claim`) > existence; đây là cách chia của Opsahl và TrustFV. **6 tag** là cách chia của FEVER 2026: một claim có thể mang nhiều tag, nên số của hai cách chia khác nhau một chút |
| Nhóm / True, Nhóm / False | Accuracy riêng trên các claim có nhãn đúng / sai. Cho biết model có thiên về một nhãn hay không |
| Δ | Accuracy mới trừ accuracy baseline, đơn vị là điểm phần trăm |
| +flip | Số câu baseline đoán **sai** mà model mới đoán **đúng** |
| −flip | Số câu baseline đoán **đúng** mà model mới đoán **sai** (bị làm hỏng) |
| NFR | Tỷ lệ câu bị làm hỏng: −flip chia cho số claim của nhóm. Càng thấp càng tốt; đo trực tiếp nỗi lo "tăng multi-hop thì nhóm khác giảm" |
| McNemar p | Kiểm định trên từng cặp câu, xem chênh lệch +flip và −flip có thể do ngẫu nhiên không. p < 0,05 nghĩa là khác biệt có ý nghĩa; p lớn (ví dụ 0,2 hoặc 1) nghĩa là chưa phân biệt được với nhiễu |
| best epoch / dev | Epoch có dev accuracy cao nhất; checkpoint của epoch đó được dùng để chạy test |

## Tóm tắt

1. **Code mới tái lập chính xác model FEVER 10 epoch:** test đạt **92,6004%** (8.372/9.041), dev đạt **90,0648%**. Kết quả khớp trên cả GPU-01 lẫn GPU-03.
2. **FEVER và V4 bổ sung cho nhau ở multi-hop.** Trên test, hai model có accuracy gần bằng nhau (80,7% và 81,2%) nhưng sai ở những câu khác nhau. Nếu luôn chọn đúng model ("oracle"), multi-hop đạt **94,0%**.
3. **Giả thuyết H1 (BERT thiếu evidence) được xác nhận.** Lỗi multi-hop chủ yếu do input **không chứa đường nối liền giữa các entity**, chứ không phải do BERT không biết suy luận 2 bước. Chỉ cần chèn đường nối vào input, không train lại, multi-hop True dev tăng từ **68,06% lên 97–98%** (K2).
4. **Giả thuyết H2 (bridge giả gây hại) được xác nhận, và còn nặng hơn dự kiến.** Checkpoint hiện tại đã học quy tắc tắt "có đường nối giữa các entity thì True". Chèn bridge tự tìm vào mọi claim khiến overall dev giảm từ **90,06% xuống 81,86%**; **100%** số câu bị làm sai là câu được chèn bridge, và mọi claim False trong số đó đều bị đổi thành True (K3).
5. **⇒ Phải train verifier trên input có bridge**, kể cả bridge giả gắn với claim False, để model học cách xét relation thay vì chỉ xét "có nối hay không". Các gate đơn giản không train lại chỉ thêm tối đa khoảng +0,4 điểm (mục 7).
6. **P2 (train lại với bridge) xác nhận điều này:** test **95,34%** (multi-hop **93,60%**), dev 94,92%. Quy tắc tắt của P1 biến mất: claim False có bridge giả giờ được đoán đúng (K5, mục 8).

## 0. Các kết luận chính: giả thuyết → cách chứng minh → kết quả

Mỗi kết luận dưới đây dựa trên một **phép can thiệp có kiểm soát**: giữ nguyên checkpoint, dữ liệu dev và cách chấm điểm, chỉ thay đổi **một** yếu tố trong input, rồi so từng câu với baseline (McNemar, đếm số câu đổi từ đúng sang sai và ngược lại). Các bảng chi tiết nằm ở mục 2–7.

### K1. BERT one-hop thường không có trong input một đường nối liền giữa các entity của claim multi-hop

| Bằng chứng | Kết quả (dev) | Nguồn |
| --- | --- | --- |
| Có cạnh trực tiếp giữa các entity của claim không? | 89,1% claim multi-hop **không có** cạnh trực tiếp nào (nhóm one-hop: 38,2%) | [báo cáo 11/11](báo%20cáo%2011_11.md), mục 3.1 |
| Node trung gian có xuất hiện từ cả hai phía không? | Chỉ 27,5% claim multi-hop, và đây là **cận trên** vì tính trước khi cắt 512 token | 11/11, mục 3.1 |
| Input bị cắt ở 512 token bao nhiêu? | 66,8% input multi-hop vượt 512 token. Tính theo path: chỉ **34,9%** tổng số path multi-hop nằm trong phần BERT đọc được. Tính theo claim: trung vị 64,5%, và 1/4 số claim chỉ giữ được ≤ 30,9% số path | mục 3 |
| Bridge có thật trong KG không? | Có: 95,9% claim multi-hop True có đường 2 hop giữa các entity, 97,5% có bridge đúng relation vàng | mục 4 |

**Kết luận:** KG *có* bằng chứng, nhưng input one-hop không trình bày nó dưới dạng một đường nối liền. Lưu ý quan trọng: **riêng việc bị cắt ở 512 token không giải thích được lỗi multi-hop.** Accuracy multi-hop gần như bằng nhau giữa input bị cắt và không bị cắt (77,5% so với 77,1%, mục 3). Thứ còn thiếu là *đường nối*, không chỉ là độ dài.

### K2. Thiếu đường nối là nguyên nhân chính của lỗi multi-hop True

- **Cách chứng minh:** giữ nguyên checkpoint 92,6% và mọi phần khác của input; chỉ đặt thêm path nối liền lên **đầu** input, để chắc chắn nằm trong 512 token. Thử hai nguồn path: (a) bridge vàng dựng theo relation trong Evidence; (b) bridge **tự tìm** trong KG, không dùng bất kỳ thông tin vàng nào.
- **Kết quả trên multi-hop True** (1.819 claim, baseline đúng 68,06%; tức 581 câu sai):

| Nguồn path chèn vào | Accuracy sau khi chèn | Số câu được sửa / bị làm sai | McNemar |
| --- | ---: | ---: | --- |
| (a) bridge vàng | **98,02%** | 553 / 8 | p ≈ 6e-152 |
| (b) bridge tự tìm, không dùng thông tin vàng | **97,36%** | 549 / 16 | p ≈ 7e-140 |

- **Kết luận:** khi được thấy đường nối, *chính model cũ, không train lại*, sửa được khoảng **95%** số lỗi multi-hop True. Nghĩa là BERT **biết** dùng đường nối 2 bước; nó chỉ thiếu đường nối trong input. Kết luận này không phụ thuộc vào thông tin vàng, vì (b) cho kết quả gần như bằng (a).
- **Giới hạn:** (a) là cận trên vì bridge vàng có thể làm lộ nhãn (có ở 1.812/1.819 claim True nhưng chỉ 543/1.736 claim False). Hệ quả đối xứng với claim False được nêu ở K3.

### K3. Model đã học quy tắc tắt "có đường nối giữa các entity ⇒ True"

- **Cách chứng minh:**
  1. Quan sát: ở one-hop và conjunction, việc có cạnh trực tiếp gần như quyết định nhãn. ≥ 99,3% claim True có cạnh trực tiếp, trong khi 77–84% claim one-hop False không có (11/11, mục 3.2).
  2. Can thiệp: chèn bridge tự tìm vào **mọi** claim, kể cả claim False, rồi xem câu nào bị đổi dự đoán và đổi theo hướng nào.
- **Kết quả (dev):**

| Nhóm / nhãn | Tỷ lệ claim được chèn bridge | Số câu bị làm sai | Trong số đó: có bridge được chèn | Trong số đó: bị đổi thành True |
| --- | ---: | ---: | ---: | ---: |
| One-hop / False | 35,3% | 362 (82% số claim được chèn) | **100%** | **100%** |
| Conjunction / False | 84,1% | 760 | **100%** | **100%** |
| Multi-hop / False | 53,0% | 362 | **100%** | **100%** |
| Negation / True ("A *không* liên quan B") | 35,6% | 207 | **100%** | — (bị đổi thành False) |

- **Kết luận:** mọi câu bị làm sai đều là câu được chèn bridge, và lỗi luôn đi theo cùng một hướng: "có đường nối ⇒ True" (với negation True: "có đường nối ⇒ claim phủ định là sai"). Model **không xét relation có khớp với claim hay không**. Đây là lý do "tăng multi-hop thì các nhóm khác giảm", và lần đầu được đo trực tiếp. Nó cũng khớp với hiện tượng walk5 của R3 làm Conjunction False giảm ([báo cáo 14/10](báo%20cáo%2014_10.md)).

### K4. Evidence nhiều bước có giá trị bổ sung cho FEVER

- **Cách chứng minh:** ghép từng câu dự đoán của FEVER và R3/V4 trên cùng 9.041 claim test (nhãn khớp 100%), đếm câu chỉ một trong hai model đúng.
- **Kết quả:** multi-hop: 241 câu chỉ FEVER đúng, 250 câu chỉ V4 đúng; oracle **94,0%**, trong khi từng model chỉ đạt khoảng 81% (mục 2).
- **Kết luận:** path nhiều bước của R3 sửa được những câu FEVER sai. Đây là bằng chứng độc lập với K2, vì nguồn path khác hẳn (relation/hop predictor thay vì bridge). Oracle chỉ là cận trên.

### K5. Train trên input có bridge vừa giải quyết multi-hop vừa loại bỏ quy tắc tắt

- **Cách chứng minh:** train lại BERT từ pretrained với đúng protocol của baseline. Chỉ thay input: one-hop cộng bridge tự tìm, áp dụng cho **mọi** claim ở cả train, dev lẫn test, nên model gặp cả bridge giả gắn với claim False. So từng câu với baseline (dev, test) và với P1(c), là lần chèn cùng loại bridge nhưng không train lại.
- **Kết quả:**

| Nhóm / nhãn (dev) | Baseline | P1(c): chèn bridge, không train | **P2: train với bridge** |
| --- | ---: | ---: | ---: |
| Multi-hop / True | 68,06 | 97,36 | **92,80** |
| Multi-hop / False | 87,10 | 66,94 | **95,05** |
| One-hop / False | 90,71 | 61,70 | **92,31** |
| Conjunction / False | 95,00 | 63,93 | **96,83** |
| Negation / True | 90,54 | 68,32 | **89,00** |
| **Overall dev** | 90,06 | 81,86 | **94,92** |
| **Overall test** | 92,60 | — | **95,34** |

- **Kết luận:** sau khi train, model không còn hiểu "có đường nối ⇒ True". Claim False có bridge giả vẫn được đoán đúng, thậm chí cao hơn baseline, nên model đã học cách **xét relation trên đường nối**. Multi-hop True thấp hơn P1(c) (92,8 so với 97,4) vì model không còn đoán True chỉ dựa vào việc có đường nối. Đổi lại, multi-hop False tăng từ 66,9 lên 95,1.

### Hệ quả cho hướng nghiên cứu

K2 cho thấy có nhiều chỗ để cải thiện. K3 giải thích vì sao không thể chỉ chèn bridge vào input. K5 cho thấy chỉ cần train trên cùng phân phối là đủ để vượt SOTA, chưa cần gate, marker hay near-miss. Câu hỏi tiếp theo vì vậy không còn là "có tăng được không", mà là: kết quả có ổn định qua nhiều seed không, thành phần nào tạo ra phần tăng, và có giữ được negation không (mục 8).

## 1. Thiết lập

| Thành phần | Chi tiết |
| --- | --- |
| Model FEVER | `bert-base-uncased`, checkpoint 10 epoch từ GPU-03 (sha256 `943aff9c…e6d23b`); suy luận bằng [`fever_predict.py`](../fever2026_bridge/fever_predict.py), không import code upstream |
| Kiểm tra tái lập | Test **8.372/9.041 = 92,6004%**, cả 5 nhóm khớp đến 4 chữ số thập phân với [báo cáo 11/11](báo%20cáo%2011_11.md). Dev **11.948/13.266 = 90,0648%** trên cả hai máy |
| V4 để so sánh | Checkpoint R3 rerun. Test: R3 (86,7382%) và R3 + walk5 (87,5456%). Dev (kiểu test, relation/hop dự đoán, giới hạn duyệt 20k): R3 84,4640% và walk5 84,7053%. Ghép với FEVER theo nội dung claim; nhãn của hai bên khớp 100% |
| KG | `dbpedia_2015_undirected_light.pickle`: 9,91 triệu entity. Nạp mất khoảng 90 s, tốn tối đa **11,8 GB RAM**. Mọi lần chạy đều đặt `ulimit -v 20 GB` để không gây OOM cho job khác |
| Tìm bridge | [`bridge_retrieval.py`](../fever2026_bridge/bridge_retrieval.py): đường 2 hop qua `N(a) ∩ N(b)`; 3 hop chỉ tìm khi không có 2 hop. Toàn bộ dev xong trong khoảng **7 phút** CPU; không claim nào bị cắt do vượt giới hạn tìm kiếm |
| Bridge vàng | [`gold_bridge.py`](../fever2026_bridge/gold_bridge.py): đi trong KG theo relation trong `Evidence` vàng của dev, mất khoảng 2 phút |
| Chèn evidence | [`build_injected.py`](../fever2026_bridge/build_injected.py): đặt path lên **đầu** `connected` để không bị cắt ở 512 token. Bridge tự tìm được xếp theo độ trùng từ giữa relation và claim, giữ tối đa 5 path mỗi claim |
| Phần cứng | GPU-03 (L40S dùng chung): suy luận khoảng **7,7 ms/claim**, dùng khoảng 1,1 GB VRAM. Trước mỗi lượt chạy đều kiểm tra VRAM trống ≥ 2 GB; lúc chạy còn trống 2,45 GB |

## 2. FEVER BERT với R3/V4: hai model sai ở những câu khác nhau

**Test (9.041 claim, chỉ để mô tả):**

| Nhóm | n | FEVER | V4 R3 | Cả hai đúng | Chỉ FEVER đúng | Chỉ V4 đúng | Oracle | V4 walk5 | Oracle với walk5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| One-hop | 1.914 | 95,5% | 91,6% | 1.685 | 143 | 69 | 99,1% | 92,0% | 99,1% |
| **Multi-hop** | 1.874 | 80,7% | 81,2% | 1.271 | **241** | **250** | **94,0%** | 81,5% | **94,3%** |
| Conjunction | 3.069 | 97,1% | 84,0% | 2.530 | 451 | 49 | 98,7% | 85,8% | 98,7% |
| Existence | 870 | 97,4% | 94,9% | 811 | 36 | 15 | 99,1% | 95,2% | 99,2% |
| Negation | 1.314 | 91,6% | 88,4% | 1.093 | 111 | 69 | 96,9% | 88,8% | 96,9% |
| **Overall** | 9.041 | **92,6%** | 86,7% | 7.390 | 982 | 452 | 97,6% | 87,5% | 97,7% |

**Dev (13.266 claim, V4 R3 giới hạn 20k):** overall FEVER **90,1%**, V4 **84,5%**, oracle **96,1%**. Riêng multi-hop: FEVER **77,4%**, V4 **72,7%**; 602 câu chỉ FEVER đúng, 435 câu chỉ V4 đúng; oracle **89,6%**.

**Đọc bảng:**

- Ở các nhóm one-hop, conjunction, existence, negation, FEVER vượt hẳn V4: số câu chỉ V4 đúng ít hơn nhiều so với số câu chỉ FEVER đúng (ví dụ conjunction: 49 so với 451).
- Ở multi-hop thì khác: mỗi model đúng riêng khoảng 250 câu trên test. Path R3 (đi qua relation/hop dự đoán) mang thông tin mà input one-hop của FEVER không có, và ngược lại.
- Oracle chỉ là **cận trên**: muốn đạt được cần một bộ chọn hoàn hảo. Không nên coi 94% là điểm có thể đạt bằng cách ghép đơn giản; đây là bằng chứng định lượng rằng evidence nhiều bước có giá trị.

## 3. Độ dài input thật (tokenizer BERT, dev)

| Nhóm | Token TB | > 512 token | % path còn nằm trong 512 token |
| --- | ---: | ---: | ---: |
| One-hop | 932 | 61,3% | 45,7% |
| **Multi-hop** | 1.162 | **66,8%** | **34,9%** |
| Conjunction | 1.651 | 87,6% | 28,0% |
| Existence | 250 | 8,5% | 94,8% |
| Negation | 905 | 51,9% | 40,8% |

Cột cuối tính **theo path**: tổng số path nằm trong 512 token chia cho tổng số path của cả nhóm. Tính **theo từng claim**, multi-hop có trung vị 64,5%, phân vị 25% là 30,9%, phân vị 75% là 100%. Path `connected` luôn nằm trong phần được đọc vì đứng đầu input; phần bị cắt là các triple `walkable` ở cuối. Ước lượng ký tự/4 dùng trước đây (41% multi-hop bị cắt) **thấp hơn thực tế rất nhiều**, nên đã bỏ.

**Bị cắt có làm FEVER sai nhiều hơn không?** (dev, accuracy FEVER theo độ dài input)

| Nhóm | ≤ 512 token: n / accuracy | > 512 token: n / accuracy | % path còn đọc được khi bị cắt |
| --- | --- | --- | ---: |
| One-hop | 985 / 93,6% | 1.562 / 95,0% | 52,4% |
| **Multi-hop** | 1.179 / **77,1%** | 2.376 / **77,5%** | 45,6% |
| Conjunction | 536 / 91,2% | 3.781 / 96,6% | 39,1% |
| Existence | 851 / 96,7% | 79 / 97,5% | 80,3% |
| **Negation** | 922 / **94,8%** | 995 / **88,0%** | 47,3% |

- **Multi-hop:** accuracy gần như không đổi theo độ dài input, kể cả khi tách theo nhãn (True: 66,0% và 68,8%; False: 84,5% và 88,8%). Vì vậy việc cắt ở 512 token **không** phải nguyên nhân chính của lỗi multi-hop. Nguyên nhân là input không có đường nối liền (K1, K2): kể cả khi đọc được toàn bộ input one-hop, đường nối vẫn không có trong đó.
- **Negation** là nhóm duy nhất bị cắt làm giảm rõ: −6,8 điểm, và claim True giảm từ 94,4% xuống 85,0%. Hợp lý, vì muốn kết luận "A *không* liên quan B" thì phải thấy được phần lớn các cạnh quanh A.
- Đây là **so sánh quan sát**, không phải can thiệp: input dài thường đi kèm entity có nhiều cạnh, nên không suy ra quan hệ nhân quả chặt chẽ. Muốn kiểm chứng nhân quả cần giữ claim cố định và chỉ thay đổi độ dài cắt, ví dụ thử thêm encoder 1.024 token ở P2/P3.

## 4. Bridge có trong KG không? Tách theo nhãn (dev)

| Nhóm / nhãn | n | Có cạnh trực tiếp | Có đường 2 hop | Có bridge nhưng không có cạnh trực tiếp | Có bridge đúng relation vàng |
| --- | ---: | ---: | ---: | ---: | ---: |
| One-hop / True | 1.299 | 99,3% | 41,4% | 0,3% | — |
| One-hop / False | 1.248 | 22,7% | 10,9% | **35,3%** | — |
| **Multi-hop / True** | 1.819 | 17,3% | **95,9%** | 82,5% | **97,5%** |
| **Multi-hop / False** | 1.736 | 4,3% | **34,6%** | 50,1% | 29,1% |
| Conjunction / True | 1.916 | 99,8% | 99,8% | 0,2% | — |
| Conjunction / False | 2.401 | 68,2% | 78,6% | **31,8%** | — |
| Negation / True | 909 | 3,5% | 21,8% | 33,8% | 38,3% |
| Negation / False | 1.008 | 57,6% | 54,7% | 15,1% | 93,7% |
| Existence (cả hai nhãn) | 930 | 0% | 0% | 0% | — |

"Có bridge" tính cả đường 2 lẫn 3 hop. Cột cuối chỉ áp dụng cho claim có relation vàng dài từ 2 hop trở lên.

- **Bridge là tín hiệu mạnh cho multi-hop:** 95,9% claim True có đường 2 hop, so với 34,6% claim False. Điều kiện ở cổng P0 (P(bridge | True) ≫ P(bridge | False)) **đạt**.
- **Bridge giả là có thật và phổ biến:** khoảng 32–35% claim False ở one-hop và conjunction có đường nối nhiều bước giữa các entity, dù giữa chúng không có cạnh trực tiếp. Đây chính là nguồn gây hại ở mục 6.

## 5. Lỗi multi-hop của FEVER nằm ở đâu? (dev, 805 câu sai)

| Nhãn | Vị trí của bridge vàng | n | FEVER sai | Tỷ lệ sai |
| --- | --- | ---: | ---: | ---: |
| True | KG không có bridge vàng | 7 | 0 | 0% |
| True | Node trung gian không có trong input one-hop | 403 | 115 | 28,5% |
| True | Có trong input nhưng bị cắt ở 512 token | 362 | **141** | **39,0%** |
| True | Node trung gian nằm trong phần được đọc | 1.047 | 325 | 31,0% |
| False | Không có bridge vàng (bình thường với claim False) | 1.193 | 137 | 11,5% |
| False | Có bridge vàng; node trung gian vắng mặt / bị cắt / nằm trong phần được đọc | 175 / 60 / 308 | 12 / 10 / 65 | 6,9% / 16,7% / 21,1% |

- **72% lỗi multi-hop rơi vào claim True** (581/805).
- Ở claim True, 256 lỗi xảy ra khi BERT **không thấy node trung gian**. 325 lỗi còn lại xảy ra khi tên node trung gian *có xuất hiện* trong input. Giải thích khả dĩ, chưa kiểm chứng: node chỉ xuất hiện ở một phía (ví dụ `A → con → X`), chưa thành một đường nối liền. Thí nghiệm P1 bên dưới cho thấy một **path nối liền tường minh** mới là thứ sửa được lỗi.
- Cách phân loại dựa trên việc chuỗi tên node có xuất hiện trong input hay không, nên chỉ là ước lượng gần đúng cho câu hỏi "BERT có thấy bridge không".

## 6. P1: chèn bridge vào input, giữ nguyên checkpoint (dev)

| Biến thể | Overall | One-hop | Multi-hop | Conjunction | Existence | Negation | +flip / −flip | NFR toàn tập |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline (input one-hop) | 90,06% | 94,46% | 77,36% | 95,95% | 96,77% | 91,29% | — | — |
| **(a) Bridge vàng, chỉ multi-hop** | **93,97%** | 94,46% | **91,93%** | 95,95% | 96,77% | 91,29% | 564 / 46 | 0,35% |
| (b) Bridge vàng, mọi nhóm | 93,66% | 94,35% | 91,93% | 95,78% | 96,77% | **89,67%** | 614 / 137 | 1,03% |
| (c) Bridge tự tìm, mọi nhóm | **81,86%** | **80,17%** | 82,50% | **78,41%** | 96,77% | 83,46% | 673 / 1.761 | **13,27%** |

"+flip / −flip" là số câu baseline sai mà biến thể làm đúng / số câu baseline đúng mà biến thể làm sai. NFR là tỷ lệ câu bị làm sai (−flip) trên toàn tập. Với (a) và (c), McNemar ở multi-hop cho p < 1e-8.

**Tách theo nhãn** (accuracy trước → sau):

| Nhóm / nhãn | (a) Bridge vàng, chỉ multi-hop | (c) Bridge tự tìm, mọi nhóm |
| --- | --- | --- |
| Multi-hop / True | 68,06 → **98,02** (+553 / −8) | 68,06 → **97,36** (+549 / −16) |
| Multi-hop / False | 87,10 → 85,54 (+11 / −38) | 87,10 → **66,94** (+12 / −362) |
| One-hop / False | không đổi | 90,71 → **61,70** (−362) |
| Conjunction / False | không đổi | 95,00 → **63,93** (−760) |
| Negation / True | không đổi | 90,54 → **68,32** (−207) |

**Kết luận từ P1:**

- **H1 đúng.** Khi thấy một path nối liền, chính checkpoint cũ sửa được gần như mọi lỗi multi-hop True; điều này đúng cả với bridge vàng lẫn bridge tự tìm. Cổng P1 (tăng ≥ 5 điểm multi-hop dev) **đạt với biên độ lớn**: +14,57 điểm.
- **Cần thận trọng với (a):** bridge vàng có thể làm lộ nhãn. Bridge vàng tồn tại ở 1.812/1.819 claim multi-hop True nhưng chỉ ở 543/1.736 claim False. Vì vậy (a) là **cận trên**, không phải kết quả của một phương pháp.
- **H2 đúng, và nặng hơn dự đoán.** Checkpoint hiện tại hiểu "có path nối các entity" ≈ True mà không xét relation. Đây đúng là quy tắc tắt đã nêu trong báo cáo 11/11, mục 3.3: one-hop và conjunction đạt 95–97% nhờ tín hiệu "có cạnh trực tiếp". Bridge giả kích hoạt quy tắc này nên claim False bị đoán thành True, còn negation True (claim dạng "A *không* liên quan B") cũng bị sai theo.
- (c) chỉ là cấu hình chẩn đoán: không gate, không marker, không train. Nó **không phải** cấu hình đề xuất.

## 7. Gate không cần train lại: chưa đủ

Thử trên dev, ghép dự đoán của baseline và của biến thể (c), dùng các quy tắc chọn đơn giản:

| Quy tắc chọn dự đoán của (c) | Số claim được đổi | Overall | Multi-hop | Các nhóm khác |
| --- | ---: | ---: | ---: | --- |
| Không đổi (baseline) | 0 | 90,06% | 77,4% | — |
| Đổi cho mọi claim | 13.266 | 81,86% | 82,5% | giảm mạnh |
| **Oracle theo loại claim: chỉ multi-hop** (dùng nhãn loại, không dùng được ở test) | 3.555 | **91,44%** | 82,5% | giữ nguyên |
| Khi claim không có cạnh trực tiếp nào | 7.141 | 85,17% | 82,1% | one-hop 80,2; conjunction 89,0 |
| Khi baseline thiếu tự tin (\|p − 0,5\| < 0,25) | 815 | **90,48%** | 79,3% | gần như giữ nguyên |
| Không có cạnh trực tiếp **và** baseline thiếu tự tin | 607 | 90,34% | 79,1% | gần như giữ nguyên |

- Gate dựa trên cấu trúc ("không có cạnh trực tiếp") **không** tách được multi-hop khỏi claim False của các nhóm khác, vì claim False ở mọi nhóm cũng thường không có cạnh trực tiếp.
- Gate theo độ tự tin an toàn nhưng chỉ thêm +0,42 điểm.
- Ngay cả oracle theo loại claim cũng chỉ đưa multi-hop lên 82,5%, vì checkpoint chưa phân biệt được bridge đúng với bridge giả ngay trong nhóm multi-hop (multi-hop False giảm còn 66,9%).
- ⇒ Muốn tiến xa hơn, verifier phải **học** từ input có bridge.

## 8. P2: train lại BERT trên input có bridge (16–17/11, GPU-03)

### 8.1 Thiết lập

| Thành phần | Chi tiết |
| --- | --- |
| Model | `bert-base-uncased` **pretrained**, không tiếp tục từ checkpoint 92,6% |
| Protocol | Giống hệt baseline: code upstream `run_stuff.py`, batch 4, LR 5e-6, tối đa 10 epoch, chọn checkpoint theo dev, patience 3. Code upstream được chép sang thư mục riêng, nên checkpoint baseline không bị ghi đè. Bản chép chỉ thêm một bước lưu checkpoint tốt nhất xuống đĩa ở mỗi epoch ([`patch_train_checkpoint.py`](../fever2026_bridge/patch_train_checkpoint.py)); cách chọn và dừng sớm không đổi |
| Input | Subgraph one-hop của baseline, cộng tối đa **5 bridge** cho mỗi claim. Bridge được đặt **lên đầu** input, chỉ tìm cho những cặp entity chưa có cạnh trực tiếp, và xếp hạng theo độ trùng từ giữa relation và claim. Mọi nhóm, mọi nhãn và cả 3 split đều được xử lý giống nhau; **không dùng Evidence vàng** |
| Số claim được chèn bridge | Train: 50.767/86.367 (conjunction 26.706; multi-hop 16.893; negation 4.221; one-hop 2.947). Dev: 7.657. Test: 4.828 (multi-hop 1.392/1.874) |
| Chi phí | Tìm bridge: CPU, trung bình khoảng 40 ms/claim, cần KG trong RAM (11,8 GB). Train: 10 epoch trong khoảng 7 giờ (28–46 phút mỗi epoch tùy tải GPU dùng chung), khoảng 7–8 GB VRAM. Suy luận: **7,05 ms/claim** |
| Toàn bộ quy trình | [`run_p2.sh`](../fever2026_bridge/run_p2.sh) `all` (`check → bridges → inputs → train → eval`). Riêng test theo nhóm được chạy thêm bằng `fever_predict.py` trên cùng checkpoint, ra đúng 95,3434% như `run_stuff.py` |

### 8.2 Đường học trên dev

| Epoch | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline (one-hop) | 51,56 | 59,27 | 75,03 | 80,19 | 84,36 | 86,87 | 88,63 | 89,30 | 89,83 | 90,06 |
| **P2 bridge5** | 51,56 | 59,90 | 68,25 | 79,62 | 85,09 | 89,31 | 92,64 | 94,04 | 94,61 | **94,92** |
| P2 dev loss | 0,704 | 0,669 | 0,612 | 0,465 | 0,349 | 0,275 | 0,197 | 0,160 | 0,156 | 0,156 |

- P2 vượt baseline từ epoch 5, và ở epoch 7 đã bằng điểm cuối của baseline.
- Epoch 10 vẫn là epoch tốt nhất, nhưng dev loss đã đứng yên từ epoch 9 (0,156), nên phần tăng thêm nếu train lâu hơn có lẽ nhỏ. Dev loss của baseline tăng lại từ epoch 8 (0,271 → 0,311), còn P2 thì không.

### 8.3 So từng câu với baseline, theo nhóm và nhãn

| Nhóm / nhãn | Dev: base → P2 | Dev +flip / −flip | **Test: base → P2** | Test +flip / −flip | Test McNemar p |
| --- | --- | ---: | --- | ---: | ---: |
| One-hop / True | 98,08 → 98,92 | 16 / 5 | 97,64 → 99,06 | 20 / 5 | 0,004 |
| One-hop / False | 90,71 → 92,31 | 42 / 22 | 92,85 → 95,19 | 35 / 15 | 0,007 |
| **Multi-hop / True** | 68,06 → **92,80** | 517 / 67 | 74,53 → **92,62** | 209 / 35 | 2e-31 |
| **Multi-hop / False** | 87,10 → **95,05** | 169 / 31 | 87,17 → **94,63** | 88 / 20 | 2e-11 |
| Conjunction / True | 97,13 → 97,96 | 50 / 34 | 98,45 → **95,43** | 17 / 58 | **2e-6** |
| Conjunction / False | 95,00 → 96,83 | 78 / 34 | 96,08 → 97,49 | 52 / 28 | 0,010 |
| Existence / True | 96,89 → 98,96 | 11 / 1 | 98,55 → 98,79 | 1 / 0 | 1 |
| Existence / False | 96,64 → 95,97 | 3 / 6 | 96,27 → 95,83 | 4 / 6 | 0,75 |
| Negation / True | 90,54 → 89,00 | 43 / 57 | 89,88 → 90,38 | 29 / 26 | 0,79 |
| Negation / False | 91,96 → **89,19** | 29 / 57 | 93,11 → **91,14** | 21 / 35 | 0,08 |
| **Overall** | 90,06 → **94,92** | 958 / 314 | 92,60 → **95,34** | 476 / 228 | 5e-21 |

NFR (tỷ lệ câu đúng bị làm sai) toàn tập là 2,37% trên dev và 2,52% trên test, so với 13,27% của P1(c).

### 8.4 Nhận xét và điểm cần thận trọng

1. **Phần tăng đến chủ yếu từ multi-hop:** trên test, multi-hop ròng +242 câu, trong khi tổng ròng là +248. Cả nhãn True lẫn False đều tăng, nên đây không phải do model nghiêng hẳn về một nhãn.
2. **Negation False giảm** ở cả dev (−2,78, p = 0,003) lẫn test (−1,97, p = 0,08). Giải thích khả dĩ: claim "A *không* liên quan B" có nhãn False khi A thật sự liên quan B. Đường nối nhiều bước được chèn vào làm nhiễu tín hiệu cạnh trực tiếp mà nhóm này cần. Đây là chỗ một gate theo loại claim (SBE) có thể giúp.
3. **Conjunction True giảm 3,02 điểm trên test** (58 câu bị làm sai, p = 2e-6), nhưng **trên dev lại tăng** (+0,84). Dev và test không nhất quán ở điểm này nên cần phân tích lỗi trước khi kết luận. Lưu ý: kết quả này không được phép dùng để chỉnh cấu hình, vì sẽ thành chọn theo test.
4. **Mới có 1 seed.** Phần tăng ở multi-hop (+12,9 điểm) và overall (+2,7 điểm) lớn hơn nhiều mức nhiễu seed thường gặp (dưới 1 điểm). Các chênh lệch nhỏ hơn 1 điểm (conjunction, existence, negation) thì chưa thể diễn giải.
5. **Tính hợp lệ của điểm test:** cấu hình (bridge5, 10 epoch, chọn theo dev) được khóa trước khi chạy. Test được tính một lần ở cuối quá trình train, và lần chạy `fever_predict.py` sau đó chỉ tách cùng kết quả ấy theo nhóm. Bridge chỉ dựa vào entity của claim (cùng nguồn entity mà baseline dùng để dựng one-hop), KG và chữ trong claim; không dùng nhãn, không dùng Evidence vàng.

### 8.5 Bước tiếp theo

| Ưu tiên | Việc | Mục đích |
| --- | --- | --- |
| 1 | Chạy lại P2 bridge5 với **2 seed nữa**, kèm 3 seed cho baseline | Báo cáo mean ± std; kiểm tra conjunction True và negation có giảm thật hay không |
| 2 | Phân tích lỗi trên **dev**: các câu negation False và conjunction True bị làm sai | Tìm nguyên nhân trước khi thêm gate hoặc marker |
| 3 | Ablation trên dev: số bridge tối đa 3/10; xếp hạng ngẫu nhiên thay cho theo độ trùng từ; marker `[2HOP]`; thêm near-miss; bỏ chèn cho negation (gate) | Tách xem phần tăng đến từ thành phần nào, và có giữ được negation không |
| 4 | Encoder khác (DeBERTa-v3, ModernBERT) với cùng input | Chứng minh phần tăng không phụ thuộc BERT |
| 5 | Phép đo độ trung thực: xóa hoặc tráo bridge lúc test rồi đo tỷ lệ đổi nhãn | Chứng minh model dùng bridge thật, không dựa vào tín hiệu giả (mục E của báo cáo 11/11) |

## 9. Artifact

| Nội dung | Vị trí |
| --- | --- |
| Code | [`fever2026_bridge/`](../fever2026_bridge/README.md) |
| Dự đoán FEVER test/dev, đo token (GPU-01) | `fever2026_bridge/results_gpu01/out/` |
| Bridge, bridge vàng, dự đoán và flip của P1, log (GPU-03) | `fever2026_bridge/results_20261115/gpu03/` |
| Báo cáo P0 trên dev; so sánh FEVER với V4 trên test | `fever2026_bridge/results_20261115/{p0_report_dev,test_fever_vs_v4_r3,test_fever_vs_v4_walk5}/` |
| P2: dự đoán dev/test, flip, log train, thống kê input | `fever2026_bridge/results_20261117/gpu03/`. File `.pkl`/`.json` bị gitignore, chỉ có ở local |
| Checkpoint R3/V4, dự đoán walk5/hybrid/dev (sao lưu từ GPU-01, nằm ngoài repo) | `C:\Duy Anh Le Code\FactKG_gpu01_backup\FactKG\` |
| Trên GPU-03 | `~/duyanh_bridge/`: KG 1,5 GB, code, `out/` (bridge và input cho cả 3 split), checkpoint P2 tại `p2_bridge5/runnable/models/bert-base-uncased.pth` |
