# Định hướng paper FactKG sau kết quả BERT one-hop

*Ghi chú nghiên cứu, 10/11/2026. Các số accuracy lấy từ báo cáo trong repo hoặc từ paper đã công bố. Mọi hướng ở mục 4 đều là **giả thuyết chưa có thực nghiệm**.*

## 1. Kết luận ngắn

- **Không nên lấy "đánh bại SOTA" làm luận điểm chính.** Mốc cao nhất tìm được là 93,49% (Opsahl 2024). BERT one-hop của ta đạt 92,60%, là bản chạy lại phương pháp đã có, nên chưa phải đóng góp mới.
- **Nên viết paper về kiểm chứng sự thật trên KG, tạo cải thiện ở Multi-hop, với ràng buộc không làm hỏng các nhóm khác.** Multi-hop chiếm 362/669 lỗi (54%) của BERT, trong khi Conjunction chỉ còn 88 lỗi.
- **Hướng thử đầu tiên:** cổng định tuyến giữa BERT one-hop và R3/V4 (hướng A). Nó rẻ, dùng lại phần việc đã có, và trả lời nhanh việc hai hệ thống có bù nhau không.
- **Conjunction chuyển từ mục tiêu sửa thành nhóm cần bảo vệ.** Theo dõi từng vế chỉ sửa điểm yếu riêng của R3/V4.

## 2. Các paper liên quan đang đi hướng nào?

"Đề xuất" và "SOTA" không phải hai loại paper đối lập. **Đề xuất** nói về đóng góp là gì. **SOTA** là một phát biểu về kết quả, và chỉ đúng trong phạm vi baseline mà paper chọn để so.

| Paper | Loại đóng góp | Có model mới? | Có nhận SOTA? | Trên FactKG | Mục đích, điểm bán chính |
|---|---|---|---|---:|---|
| FactKG (2023) | Dataset + baseline | Không | Không | 77,65% | Tạo bài toán kiểm chứng trên KG |
| Opsahl (2024) | Đơn giản hóa retrieval | Không có kiến trúc mới: BERT + subgraph một hop | **Có, và đúng về số** ("best performance achieved so far") | **93,49%** | Retrieval đơn giản thắng retrieval phức tạp, rẻ hơn. Bảng kết quả không báo độ lệch giữa các seed |
| PGR (2025) | Phương pháp | Có: sinh chương trình trên KG | DARE gọi là baseline mạnh nhất nhóm sinh chương trình | 86,82% | Thấy được từng bước suy luận |
| FEVER 2026 (Upadhyay et al.) | Nghiên cứu phân tích có kiểm soát | Không: tái lập BERT của Opsahl | Không | 92,68% | Tìm yếu tố nào tạo ra kết quả: ngữ nghĩa, cấu trúc graph, chọn evidence hay trí nhớ LLM |
| DARE (2026) | Phương pháp | Có: agent lặp retrieve, reason, reflect | **Có**, nhưng chỉ so với nhóm LLM và sinh chương trình | 88,12% | Qwen3-8B zero-shot ngang hoặc hơn GPT-4o |
| TrustFV (2026) | Phương pháp | Có: KG-Trie + process reward | **Có** trên FactKG và CWQ, baseline cũng không gồm BERT one-hop | 90,07% ±1,6 | Path đáng tin: 100% path nằm trong KG, độ khớp path vàng tăng từ 84% lên 92% |
| More Evidence (2026) | Diagnostic + bộ gộp LGED | Có, vai trò phụ | Không | Không chạy (HoVer) | Đo verifier phân biệt fact lặp với fact mới |
| Fact-FOLX-KG (ACL 2026) | Dataset mới + phương pháp (mới đọc qua tóm tắt) | Có | Trên chính dataset của họ | Không chạy | Mở rộng sang lượng từ, so sánh, đếm |

**Bài học:**

1. DARE và TrustFV đều là paper phương pháp được nhận dù thấp hơn 93,49%. Họ thắng trong nhóm baseline đã chọn và có điểm bán khác accuracy (model nhỏ, path đáng tin). Cả hai đều không trích dẫn Opsahl hay FEVER 2026.
2. Ta không nên đi lại cách đó, vì đã biết mốc 93,49% và reviewer có thể biết. Phải đưa BERT one-hop vào bảng so sánh.
3. Bảng theo nhóm của DARE và TrustFV khi nhân với `n` chỉ cho 87,82% và 88,83%, thấp hơn số tổng họ báo (88,12% và 90,07%). Khi so sánh nên dùng số theo nhóm và ghi chú điểm này.
4. Một paper không có model mới vẫn có giá trị (FEVER 2026, More Evidence), miễn là câu hỏi rõ và đo có kiểm soát.

## 3. Vị trí hiện tại

Năm nhóm dưới đây loại trừ nhau và có cùng `n` ở DARE, TrustFV và repo này.

| Nhóm (n) | Claim-only BERT | R3/V4 gốc | R3/V4 + walk5 | BERT one-hop 10 epoch | DARE | TrustFV |
|---|---:|---:|---:|---:|---:|---:|
| One-hop (1.914) | 69,64 | 91,64 | 91,95 | **95,51** | 94,44 | 89,13 |
| Existence (870) | 61,84 | 94,94 | 95,17 | **97,36** | 95,23 | 96,00 |
| Multi-hop (1.874) | 70,06 | 81,16 | 81,54 | 80,68 | 77,28 | **88,14** |
| Conjunction (3.069) | 63,31 | 84,03 | 85,76 | **97,13** | 87,58 | 87,12 |
| Negation (1.314) | 63,62 | 88,43 | 88,81 | **91,63** | 88,89 | 88,63 |
| **Overall (9.041)** | 65,20 | 86,74 | 87,55 | **92,60** | 88,12 | 90,07 |

Cách đọc đúng:

- `walk5` được xem sau khi đã nhìn test nhiều lần, nên phải chọn lại trên dev trước khi đưa vào paper.
- R3/V4 và BERT coi như **ngang nhau ở Multi-hop**. Chênh 0,48–0,86 điểm nằm trong sai số khoảng ±1,8 điểm của nhóm này.
- Evidence one-hop chỉ thêm 10,6 điểm so với claim-only ở Multi-hop, trong khi các nhóm khác thêm 26–36 điểm.
- Khoảng tin cậy 95% của overall là ±0,54 điểm, nên 92,60% và 92,68% là ngang nhau.
- Opsahl đạt 93,49% với LR 5e-5, batch 4, best epoch 7. Ta dùng LR 5e-6 theo FEVER 2026, nên chưa quét LR thì chưa có baseline công bằng.

**Mục tiêu định lượng:** để vượt 93,49% cần ròng thêm 81 claim, tương đương Multi-hop lên khoảng 85% nếu các nhóm khác giữ nguyên. Dùng nguyên R3/V4 cho toàn bộ Multi-hop chỉ đạt khoảng 92,78%, nên dư địa nằm ở việc hai hệ thống **sai ở những câu khác nhau**, điều chưa được đo.

**Rủi ro tụt điểm chéo nhóm đã xuất hiện trong dữ liệu của ta:**

| Thay đổi | Nhóm tăng | Nhóm giảm |
|---|---|---|
| Retrieval cũ (E2b) sang R3, cùng verifier E2 | Multi-hop 71,18 lên 78,60 | Negation 87,98 xuống 80,14 |
| Cùng checkpoint V4 rerun, candidate test Legacy sang R3 | Multi-hop +17,71 điểm | Conjunction −1,18 điểm |
| `walk5` so với R3 gốc | Conjunction True đúng thêm 72 câu | Conjunction False đúng ít đi 19 câu |

Nguyên nhân khả dĩ là các nhóm dùng chung ngân sách evidence và ranh giới quyết định. Với BERT, 51% input test đã bị cắt ở 512 token (FEVER 2026, Table 5). `kg.py` còn chỉ giữ một tail ngẫu nhiên cho mỗi cặp entity–relation và không đặt seed ở bước dựng subgraph, nên phải giữ nguyên file subgraph giữa các lượt.

## 4. Các hướng đi và mục đích

| Hướng | Loại paper | Mục đích | Chi phí | Điều kiện đi tiếp | Rủi ro chính |
|---|---|---|---|---|---|
| **A. Cổng định tuyến BERT + R3/V4** | Phương pháp | Tăng Multi-hop mà giữ nguyên dự đoán BERT cho phần lớn claim | Thấp | Trần chọn-đúng-từng-câu của Multi-hop trên dev từ 85% | Bị xem là "chỉ là ensemble"; câu bị chuyển nhầm vẫn có thể hỏng |
| **B. Verifier dư (residual)** | Phương pháp | Cho nhánh nhỏ đọc path R3 sửa logit BERT, phạt khi lật câu BERT rất chắc | Trung bình | A có trần đủ cao nhưng cổng thực tế chưa đạt | Khó train, phụ thuộc chất lượng path |
| **C. Ngăn token cho path bắc cầu** | Phương pháp | Đưa chuỗi trung gian vào BERT bằng phần token đang bị cắt | Trung bình | Đo với path vàng cho thấy Multi-hop tăng mạnh | Train lại làm lệch các nhóm khác |
| **D. Trạng thái bằng chứng từng mắt xích** | Phương pháp | Phân biệt cầu đúng relation, cầu sai relation, không thấy cầu | Trung bình đến cao | C cho thấy path có ích nhưng verifier đọc chưa đúng | Gần với `SEARCH` của PGR |
| **E. Chỉ gọi LLM cho câu khó** | Phương pháp, chất lượng–chi phí | Đạt accuracy cao với ít lời gọi LLM hơn nhiều | Trung bình | A chạy được và có nhóm câu cổng không chắc | Cần so công bằng về chi phí |
| **F. Chẩn đoán: can thiệp evidence** | Phân tích | Biết BERT thực sự dựa vào relation, entity hay vị trí `connected` | Thấp đến trung bình | Luôn cần, dù đi hướng nào | Làm riêng thì cần câu chuyện đủ mạnh |
| **G. Audit nhãn FactKG** | Benchmark | Ước lượng bao nhiêu lỗi là do nhãn hoặc claim lệch Evidence | Trung bình, cần chú giải thủ công | Mẫu ngẫu nhiên có tỷ lệ lệch đáng kể | Pilot mới có 2/9 câu, lại là mẫu chọn có chủ đích |
| **H. KG không đầy đủ** | Bài toán mới | Đo model còn khẳng định đúng/sai không khi thiếu cạnh, phân biệt "chưa thấy" với "bị bác bỏ" | Cao, phải dựng benchmark | Sau paper đầu | Tốn công, chỉ dùng được trên dev vì test không có `Evidence` |
| **I. Mở rộng sang suy luận logic** | Phương pháp, benchmark | Thử trên Fact-FOLX-KG, nơi BERT có evidence chỉ đạt 70,12% theo bảng của DARE | Cao | Lấy được dataset | Chưa thấy link tải; có thể là pipeline BERT khác |
| **J. Chỉ đuổi SOTA** | Phương pháp | Vượt 93,49% bằng encoder lớn hơn, tinh chỉnh | Trung bình | Không khuyến nghị làm luận điểm chính | Thắng vài phần mười thì nằm trong sai số, novelty yếu |

**Chi tiết hướng A.** Mặc định giữ dự đoán BERT, chỉ chuyển sang R3/V4 khi KG cho thấy cần suy luận nhiều bước. Tín hiệu gồm hop predictor `H ≥ 2`, không có `connected` một hop, có `connected` từ R3, và độ tự tin của hai model. Cổng là logistic stacking, đúng hướng 3 trong [reading list](paper_reading_list.md). Không dùng nhãn `types` khi suy luận. Câu không qua cổng giữ nguyên dự đoán, nhưng câu Conjunction bị chuyển nhầm vẫn có thể hỏng, nên không được hứa là không tụt.

**Khung đóng góp nếu A đạt:** (1) đo được evidence one-hop và path nhiều bước bù nhau ra sao, (2) cổng dựa trên độ đủ của evidence KG, (3) chỉ số số câu bị làm hỏng theo nhóm và phép kiểm chứng can thiệp.

**Cách viết về nguồn gốc:** không gọi là "cải tiến từ FEVER". Nên viết là kết hợp baseline BERT one-hop (Opsahl 2024, tái lập bởi Upadhyay et al. 2026) với R3/V4 để giải quyết giới hạn one-hop mà FEVER 2026 tự nêu ở Multi-hop.

## 5. Thứ tự đề xuất

| Bước | Việc | Quyết định |
|---|---|---|
| 0 | Quét LR, ít nhất 3 seed, đóng băng BERT theo dev | Có baseline công bằng |
| 1 | Chạy BERT trên 13.266 claim dev, ghép với dự đoán R3/V4 dev kiểu test, tính trần Multi-hop | Từ 85% sang bước 2, dưới 85% sang bước 3 |
| 2 | Hướng A. Nếu trần đủ cao mà cổng thực tế dưới 85%, thử hướng B | Đạt thì sang bước 4 |
| 3 | Đo trần với path bắc cầu vàng. Tăng mạnh thì làm hướng C, rồi D | Không tăng thì chuyển sang G và F thành paper chẩn đoán |
| 4 | Hướng F và các kiểm chứng ở mục 6 | Tạo độ tin cậy cho paper |
| 5 | Hướng E nếu còn thời gian | Thêm câu chuyện chi phí |

Hướng H và I để cho paper sau, trừ khi cần benchmark thứ hai và lấy được Fact-FOLX-KG.

## 6. Những điều phải kiểm chứng

Chỉ đề xuất một model tốt hơn thì chưa đủ. Paper cần trả lời:

1. **Hai model có bù nhau không:** đo độ chồng lấn lỗi trên dev.
2. **Cổng có giỏi thật không:** thắng ba mốc là luôn dùng BERT, chỉ dùng độ tự tin, và chia theo nhóm claim.
3. **Có làm hỏng nhóm khác không:** báo số câu cứu và làm hỏng theo từng nhóm.
4. **Lợi ích có đến từ evidence không:** thay path R3 bằng path sai hoặc xáo trộn. Nếu cải thiện vẫn còn thì đó chỉ là ensemble.
5. **BERT dựa vào gì:** trên dev, xóa cạnh vàng, thay tail sai, che tên relation, bỏ khối `connected`, xáo thứ tự, rồi đo tỷ lệ đổi nhãn. FEVER 2026 thấy số thành phần liên thông là feature quan trọng nhất, nhưng BERT chỉ dùng cạnh trực tiếp của Opsahl chỉ đạt 79,64%, nên câu hỏi còn mở.
6. **Kết quả có vững không:** ít nhất 3 seed, kiểm định theo cặp McNemar, test chạy một lần, ghi rõ test đã xem nhiều lần với R3/V4.

**Nơi nộp, theo đánh giá chủ quan:** cải thiện vừa phải với đủ kiểm chứng hợp workshop FEVER. Call 2026 nhận long 8 trang, short 4 trang, bắt buộc có mục Limitations; chưa thấy call 2027. Findings cần cải thiện rõ ở Multi-hop, vượt 93,49% qua nhiều seed và có benchmark thứ hai.

## 7. Những việc nên dừng

- Lấy Conjunction theo từng vế làm câu chuyện chính.
- So "BERT hơn DARE" như đóng góp của mình. BERT train trên 86 nghìn claim có nhãn, DARE là zero-shot.
- Tinh chỉnh `walkN` hoặc K theo test.
- Coi ERNet là bước kế tiếp. Lần chạy V5 thấp hơn V4 ở cả năm nhóm.
- Tái lập DARE như baseline chính. Repo vẫn chỉ có "Coming soon", paper không nêu `top-k` và chỉ công bố prompt Reasoner. Nếu cần baseline LLM chạy được, thử [code TrustFV](https://github.com/2twentytwo2/Trust_KG_FV) (chưa chạy thử).

## Phụ lục: số liệu lịch sử các cấu hình

Bảng gộp để tra cứu, cùng 9.041 claim test. Các hàng không phải cùng một phép so sánh có kiểm soát; xem [báo cáo 2/9](báo%20cáo%202_9.md) và [báo cáo 14/10](báo%20cáo%2014_10.md).

| Cấu hình | One-hop | Multi-hop | Conjunction | Existence | Negation | Overall | Macro-F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| E0 Concat, top-5 | 84,22 | 68,84 | 85,08 | 89,08 | 84,35 | 81,80 | — |
| E2b Pair + Attention, retrieval cũ | 91,12 | 71,18 | 82,82 | 94,37 | 87,98 | 83,69 | 83,48 |
| R1 + E2 | 90,44 | 75,67 | 83,58 | 94,37 | 79,98 | 83,91 | 83,77 |
| R2 + checkpoint R1 | 90,80 | 78,28 | 83,51 | 94,48 | 80,14 | 84,54 | 84,42 |
| R3 + checkpoint R1 | 90,80 | 78,60 | 83,51 | 94,48 | 80,14 | 84,60 | 84,49 |
| R3 Full + V2 | 92,06 | 79,78 | 82,73 | 98,05 | 81,28 | 85,36 | 85,24 |
| R3 Full + V3 | 91,80 | 78,82 | 81,43 | 93,22 | 89,12 | 85,33 | 85,17 |
| R3 Full + V4 | 91,64 | 81,16 | 84,03 | 94,94 | 88,43 | 86,74 | 86,63 |
| R3 + V4 + walk5 (thăm dò) | 91,95 | 81,54 | 85,76 | 95,17 | 88,81 | 87,55 | 87,47 |
| R3 Full + V5 sparse ERNet, seed 42 | 86,15 | 62,81 | 79,77 | 92,99 | 86,99 | 79,92 | 79,33 |
| BERT one-hop 5 epoch | 91,22 | 79,14 | 95,05 | 86,32 | 74,73 | 87,15 | — |
| BERT one-hop 10 epoch | 95,51 | 80,68 | 97,13 | 97,36 | 91,63 | 92,60 | — |

V5 đạt dev 95,65% nhưng test chỉ 79,92%. Chênh lệch này chưa được giải thích, và một seed chưa đủ để kết luận sparse ERNet luôn có hại.

## Nguồn

- [Opsahl 2024](https://arxiv.org/pdf/2408.07453), [code](https://github.com/Tobias-Opsahl/Fact-or-Fiction)
- [Upadhyay et al., FEVER 2026](https://aclanthology.org/2026.fever-1.3.pdf)
- [PGR 2025](https://aclanthology.org/2025.findings-emnlp.293.pdf)
- [DARE 2026](https://aclanthology.org/2026.findings-emnlp.1315.pdf), [repo](https://github.com/inflee/DARE)
- [TrustFV 2026](https://aclanthology.org/2026.findings-emnlp.726.pdf)
- [More Evidence Is Not Always More Support 2026](https://aclanthology.org/2026.findings-emnlp.747.pdf)
- [Fact-FOLX-KG, ACL 2026](https://aclanthology.org/2026.acl-long.1230/)
- [Call for Papers FEVER](https://fever.ai/workshop.html)
- Trong repo: [báo cáo 11/11](báo%20cáo%2011_11.md), [so sánh V4 theo candidate](so_sanh_V4_legacy_R3_20261009.md), [pilot từng vế](conjunction_clause_pilot_20261019_154232.md)
