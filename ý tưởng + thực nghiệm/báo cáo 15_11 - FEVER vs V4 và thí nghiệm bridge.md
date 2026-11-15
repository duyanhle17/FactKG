# Báo cáo 15/11/2026: so sánh FEVER BERT với R3/V4 và thí nghiệm bridge cho multi-hop

> Đây là phần thực nghiệm P0/P1 của kế hoạch trong [báo cáo 11/11](báo%20cáo%2011_11.md), mục "Brainstorm".
> Mọi kết quả dùng để **chọn hướng** đều tính trên **dev** (13.266 claim). Test chỉ được dùng để kiểm tra tái lập và mô tả, không dùng để chọn cấu hình.

## Tóm tắt

1. **Code mới tái lập chính xác model FEVER 10 epoch:** test đạt **92,6004%** (8.372/9.041), dev đạt **90,0648%**. Kết quả khớp trên cả GPU-01 lẫn GPU-03.
2. **FEVER và V4 bổ sung cho nhau ở multi-hop.** Trên test, hai model có accuracy gần bằng nhau (80,7% và 81,2%) nhưng sai ở những câu khác nhau. Nếu luôn chọn đúng model ("oracle"), multi-hop đạt **94,0%**.
3. **Giả thuyết H1 (BERT thiếu evidence) được xác nhận.** Lỗi multi-hop chủ yếu do input **không chứa đường nối liền giữa các entity**, chứ không phải do BERT không biết suy luận 2 bước. Chỉ cần chèn đường nối vào input, không train lại, multi-hop True dev tăng từ **68,06% lên 97–98%** (K2).
4. **Giả thuyết H2 (bridge giả gây hại) được xác nhận, và còn nặng hơn dự kiến.** Checkpoint hiện tại đã học quy tắc tắt "có đường nối giữa các entity thì True". Chèn bridge tự tìm vào mọi claim khiến overall dev giảm từ **90,06% xuống 81,86%**; **100%** số câu bị làm sai là câu được chèn bridge, và mọi claim False trong số đó đều bị đổi thành True (K3).
5. **⇒ Hướng SBE đúng, nhưng bắt buộc phải train verifier trên input có bridge**, kể cả bridge giả gắn với claim False, để model học cách xét relation thay vì chỉ xét "có nối hay không". Các gate đơn giản không train lại chỉ thêm tối đa khoảng +0,4 điểm (mục 7).

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

### Hệ quả cho hướng nghiên cứu

K2 cho thấy **có rất nhiều chỗ để cải thiện**: multi-hop True có thể lên khoảng 97%. K3 cho thấy **tại sao không thể chỉ chèn bridge vào input**. Bước tiếp theo vì vậy là **train lại verifier trên input có bridge (P2)**, để model gặp cả bridge đúng lẫn bridge giả ngay khi học.

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

## 8. Bước tiếp theo đề xuất: P2, train lại với bridge

| Bước | Nội dung | Lý do |
| --- | --- | --- |
| P2.0 | Chạy `bridge_retrieval.py` cho **train** (86.367 claim, ước lượng khoảng 45 phút CPU) và cho test. Không dùng Evidence vàng khi dựng input | Train và test phải có cùng phân phối evidence |
| P2.1 | Train BERT với input one-hop + bridge tự tìm cho **mọi** claim, đánh dấu `[2HOP]`. So với baseline cùng số epoch | Cho model thấy bridge giả gắn với nhãn False, để học xét relation (H2) |
| P2.2 | Ablation: có / không marker; có / không near-miss; số bridge tối đa 3/5/10; xếp bridge theo từ vựng hay ngẫu nhiên | Tách xem phần tăng đến từ thành phần nào |
| P2.3 | Báo NFR theo từng nhóm và từng nhãn so với baseline; chọn cấu hình trên dev | Mục tiêu: multi-hop ≥ 85% với NFR các nhóm khác ≈ 0 |

**Cách train:** fine-tune lại **từ `bert-base-uncased` pretrained**, không tiếp tục từ checkpoint 92,6%. Mọi thiết lập giữ như baseline: batch 4, LR 5e-6, tối đa 10 epoch, chọn checkpoint theo dev, dừng sớm sau 3 epoch dev không tăng. Như vậy khác biệt duy nhất so với baseline là input có thêm bridge. Có thể thêm một biến thể phụ rẻ hơn là fine-tune tiếp từ checkpoint 92,6% trong 1–3 epoch, nhưng kết quả của biến thể này bị lẫn với hiệu ứng "train lâu hơn", nên chỉ dùng tham khảo. Mọi bước đã gói trong [`run_p2.sh`](../fever2026_bridge/run_p2.sh) (`check → bridges → inputs → train → eval`).

**Điều kiện tài nguyên:** train BERT-base ở batch 4 và 512 token cần khoảng 6–8 GB VRAM. Lần kiểm tra gần nhất, GPU-03 còn khoảng **2,4 GB** trống, GPU-01 khoảng **4 GB**. Có hai lựa chọn: chờ máy rảnh hơn, hoặc dùng bf16 + gradient checkpointing để train vừa khoảng 3–4 GB (cách này làm thay đổi protocol so với baseline, nên phải train lại cả baseline theo cùng cách).

## 9. Artifact

| Nội dung | Vị trí |
| --- | --- |
| Code | [`fever2026_bridge/`](../fever2026_bridge/README.md) |
| Dự đoán FEVER test/dev, đo token (GPU-01) | `fever2026_bridge/results_gpu01/out/` |
| Bridge, bridge vàng, dự đoán và flip của P1, log (GPU-03) | `fever2026_bridge/results_20261115/gpu03/` |
| Báo cáo P0 trên dev; so sánh FEVER với V4 trên test | `fever2026_bridge/results_20261115/{p0_report_dev,test_fever_vs_v4_r3,test_fever_vs_v4_walk5}/` |
| Checkpoint R3/V4, dự đoán walk5/hybrid/dev (sao lưu từ GPU-01, nằm ngoài repo) | `C:\Duy Anh Le Code\FactKG_gpu01_backup\FactKG\` |
| Trên GPU-03 | `~/duyanh_bridge/`: KG 1,5 GB, code, `out/`. Giữ lại để chạy P2 |
