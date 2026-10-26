# Ba paper 2026 cần đọc tiếp cho hướng FactKG R3 → V4

*Cập nhật 27/10/2026.* Tài liệu này nối tiếp [survey FEVER 2026 và PGR](SURVEY_FEVER2024_FEVER2026_PGR_FACTKG.md). Ba paper ở đây không phải ba phiên bản của cùng một pipeline. DARE và TrustFV thử **kiểm chứng claim trên KG FactKG**; *More Evidence Is Not Always More Support* chủ yếu nghiên cứu **cách verifier gộp evidence dạng đoạn văn trên HoVer**, không báo accuracy FactKG.

## 1. DARE — tìm, lập luận hai chiều, quyết định có tìm tiếp

**Nguồn:** Li et al., [*DARE: Dialectical Agentic Reasoning for Structured Knowledge Fact Checking*](https://aclanthology.org/2026.findings-emnlp.1315/), Findings EMNLP 2026; [PDF](https://arxiv.org/pdf/2609.13808).

**Vấn đề họ nhắm tới.** PGR có thể sinh relation không tồn tại trong KG, theo một chương trình một chiều khó sửa sai, và đánh giá quá thiên về bằng chứng *ủng hộ*. DARE thay chương trình cố định bằng vòng `retrieve → reason → reflect`.

| Chặng | Đầu vào → thao tác → đầu ra |
| --- | --- |
| 1. Retriever | Từ entity của claim, lấy các triple kề nó trong KG; LLM lọc các triple liên quan. Relation được lấy từ cạnh **có thật**, không phải tên relation tự bịa. Vòng sau có thể mở rộng từ entity mới tìm được. |
| 2. Reasoner | Cùng tập evidence, một lập luận theo hướng **ủng hộ** và một theo hướng **phản bác**, kèm hai mức tin cậy. Đây là hai vai trò prompt, không phải hai KG. |
| 3. Controller | Nếu hai phía còn chưa phân định, tìm evidence tiếp; nếu đủ tự tin hoặc đạt giới hạn vòng lặp, tổng hợp và ra `Supported/Refuted`. |

Ví dụ claim “A sinh ở Canada **và** Canada nói tiếng Pháp”: lượt đầu chỉ thấy cạnh `A → Canada` thì chưa nên khẳng định cả câu đúng hay sai; lượt sau mở từ `Canada` để kiểm tra vế còn thiếu. DARE dùng **Qwen3-8B zero-shot**, ba vai trò dùng cùng backbone với prompt khác nhau; không train verifier V4. Thiết lập chính tối đa **5 vòng**. [Mục phương pháp, ví dụ và thiết lập](https://arxiv.org/pdf/2609.13808).

**Kết quả.** Trên 9.041 claim FactKG test, DARE báo **88,12% overall**, so với **86,82% PGR** trong bảng của họ; Multi-hop **77,28%**, Conjunction **87,58%**, Negation **88,89%**. DARE *thấp hơn PGR ở Conjunction* (**87,58% so với 89,95%**), dù cao hơn ở overall và Negation. Bỏ lập luận hai chiều, bỏ bước phản tư, hoặc bỏ semantic filtering đều làm điểm giảm trong ablation của họ. Các con số theo nhóm ở đây dùng cách chia năm nhóm của paper, không thay thế bảng True/False riêng của repo. [DARE, Bảng 1–2](https://arxiv.org/pdf/2609.13808).

**Giới hạn tác giả nêu:** truy xuất mọi triple kề entity có thể rất tốn khi gặp node bậc cao; đánh giá chủ yếu ở tác vụ có evidence cấu trúc. **Câu hỏi của ta:** có thể dùng R3 để duyệt có ngân sách, theo dõi *vế nào còn thiếu*, và chỉ tìm tiếp khi cần — không gọi LLM ở mọi claim — hay không? Nhưng “support vs refute” và “tìm lại khi chưa chắc” **đã là đóng góp của DARE**; ý tưởng mới phải chỉ rõ phép đo/thuật toán khác và chứng minh lợi ích về proof coverage, lỗi False→True, chi phí. [DARE, Limitations](https://arxiv.org/pdf/2609.13808).

## 2. TrustFV — sinh path bị ràng buộc bởi KG, chấm điểm từng bước

**Nguồn:** Zhang et al., [*TrustFV: Trustworthy Fact Verification on Knowledge Graph via Process Reward-Guided Step-Level Constrained Decoding*](https://aclanthology.org/2026.findings-emnlp.726/), Findings EMNLP 2026; [PDF gốc](https://aclanthology.org/2026.findings-emnlp.726.pdf).

**Vấn đề họ nhắm tới.** Beam search trên KG có thể chọn nhánh sai từ sớm; đi tiếp từ nhánh đó tạo lỗi dây chuyền. Một path gồm cạnh có thật cũng chưa chắc là *path phù hợp để chứng minh claim*.

| Chặng | Đầu vào → thao tác → đầu ra |
| --- | --- |
| 1. Evidence và KG-Trie | Một phương pháp retrieval (paper nêu ví dụ SimGRAG) lấy vài subgraph liên quan, có thể **rời nhau**. Chuyển thành chuỗi token và lưu trong trie để biết bước sinh nào hợp lệ theo KG. |
| 2. Huấn luyện model | SFT một Llama-3.1-8B-Instruct bằng LoRA để sinh reasoning path và nhãn. Tạo nhiều đường suy luận, từ mỗi tiền tố chạy Monte Carlo để ước lượng xác suất cuối cùng đúng; dùng các tín hiệu đó huấn luyện **UPRM** (process reward model có xét bất định). |
| 3. Suy luận | LLM chỉ được sinh token/path hợp lệ trong KG-Trie; sau **mỗi bước**, UPRM chấm khả năng thành công và độ bất định; beam search loại nhánh rủi ro; path được chọn → đáp án True/False. |

Khác R3: ở đây **không có predictor relation top-5 + hop rồi DFS như repo**. Cũng khác `walk5`: “top-5 evidence subgraphs” của TrustFV là ngân sách evidence **trước/khi sinh**, không phải giữ năm `walkable` đã có để đưa vào V4. Paper dùng hai GPU A800 80 GB cho thí nghiệm; suy luận theo nhóm khó có thể mất hàng chục giây/claim. [TrustFV, mục 3–4 và phụ lục C](https://aclanthology.org/2026.findings-emnlp.726.pdf).

**Kết quả.** Paper báo **90,07% ± 1,6** FactKG accuracy qua năm lượt; Multi-hop **88,14%**, Multi-claim **87,12%**. Bỏ constrained decoding, UPRM hoặc chấm điểm theo từng bước đều làm điểm giảm trong ablation. Nhưng `90,07%` **không vượt** BERT one-hop **92,68%** được FEVER 2026 tái lập, càng không vượt mốc **93,49%** của Opsahl 2024. Phát biểu “SOTA” trong TrustFV phải hiểu là **trong tập baseline paper ấy chọn để so**, không phải mọi kết quả từng công bố trên FactKG. [TrustFV, Bảng 1–4](https://aclanthology.org/2026.findings-emnlp.726.pdf); [FEVER 2026, Bảng 2–3](https://aclanthology.org/2026.fever-1.3.pdf).

**Lưu ý protocol và đọc bảng:** TrustFV ghi **99.133 train + 500 validation + 9.041 test**, còn FEVER 2026 ghi **86.367 train + 13.267 validation + 9.041 test**; chưa thể quy chênh điểm chỉ cho mô hình. Bảng chính của TrustFV ghi PGR 86,82% nhưng ghi backbone `GPT-4o-mini`; paper PGR gốc dùng `GPT-4o` cho mức 86,82%. Phụ lục kiểm định của TrustFV lại báo PGR chạy lại **85,13% ± 2,9**. Đây là các điểm cần đối chiếu code/protocol trước khi trích làm so sánh định lượng chặt chẽ, **không tự ý gộp thành một kết quả PGR**. [TrustFV, Bảng 1 và phụ lục B/F](https://aclanthology.org/2026.findings-emnlp.726.pdf); [PGR, mục 4.3](https://aclanthology.org/2025.findings-emnlp.293.pdf).

**Giới hạn tác giả nêu:** độ rộng beam và cách prune hiện cố định dù độ khó claim thay đổi. **Giới hạn suy ra từ thiết kế:** bị ràng buộc theo KG chứng minh path *tồn tại trong KG*, không tự chứng minh path đó *đủ cho mọi vế* của claim; mô hình còn phụ thuộc subgraph được retrieval trước đó. Vì TrustFV đã làm “KG-constrained beam + process reward + uncertainty”, đề xuất ToT/beam search chung chung sẽ khó mới. Hướng còn đáng thử là **ngân sách thích ứng theo độ phủ vế, và kiểm tra tính đầy đủ của proof dưới giới hạn tìm kiếm**, với chi phí thấp hơn; đây là giả thuyết của ta, không phải limitation tác giả tự nhận ở toàn bộ các ý. [TrustFV, phương pháp và Limitations](https://aclanthology.org/2026.findings-emnlp.726.pdf).

## 3. More Evidence Is Not Always More Support — thêm evidence mới khác với lặp evidence cũ

**Nguồn:** Zhong et al., [*More Evidence Is Not Always More Support: Controlled Diagnostics for Evidence Aggregation in Fact Verification*](https://aclanthology.org/2026.findings-emnlp.747/), Findings EMNLP 2026; [PDF](https://aclanthology.org/2026.findings-emnlp.747.pdf). **Không phải paper FactKG**: thí nghiệm chính dùng *HoVer*, evidence là câu/đoạn văn, không phải path DBpedia.

**Câu hỏi nghiên cứu.** Hai verifier có accuracy/F1 gần nhau vẫn có thể hành xử rất khác khi evidence tăng. Nếu claim cần hai fact, thêm *một bản lặp của fact 1* không nên thay nhãn; thêm *fact 2 còn thiếu* có thể thay nhãn. Chỉ nhìn accuracy trên tập evidence cuối cùng không phát hiện được sự khác nhau này.

| Chặng | Họ làm gì? |
| --- | --- |
| 1. Dựng diagnostic | Từ annotation HoVer, tạo **prefix evidence giống hệt nhau** cho mỗi cặp: prefix đã có một “họ fact” nhưng thiếu một họ khác. |
| 2. Can thiệp có kiểm soát | Nhánh A thêm evidence **lặp họ đã có**; nhánh B thêm evidence **cho họ còn thiếu**. Một phép thử khác lặp nguyên một câu 1, 2, 4, 8 lần. |
| 3. Đo và học thử | Đo tỷ lệ nhãn bị đảo vì lặp (`FR-8`) và mức margin tăng khi thêm fact thiếu. So nhiều verifier; giới thiệu **LGED**, bộ gộp có trạng thái và loss khuyến khích ổn định trước lặp nhưng nhận ra fact mới. |

Diagnostic chính có **1.180 cặp same-prefix**. Các supervised verifier có clean F1 trong khoảng **0,6324–0,6528** nhưng tỷ lệ đảo nhãn sau tám bản lặp trải từ **8,5% đến 30,3%**. LGED có FR-8 khoảng **1,37%**, nhưng base score ở bảng được báo bằng **accuracy**, trong khi nhiều dòng khác dùng **F1**: không xếp các base score này thành bảng ai mạnh hơn ai. Giá trị chính của paper là *phép đo hành vi evidence*, không phải mốc accuracy FactKG. [Phương pháp và Bảng 2](https://aclanthology.org/2026.findings-emnlp.747.pdf).

**Giới hạn tác giả nêu:** diagnostic chính phụ thuộc cấu trúc supporting-fact của HoVer; cần kiểm chứng thêm ở bối cảnh retrieval đầu-cuối, dữ liệu yếu nhãn và đa ngôn ngữ; LGED mạnh nhất ở chống lặp nhưng lợi ích từ fact thiếu không đồng đều hơn mọi supervised model. **Liên hệ R3/V4:** `walk5`/`ranked5` có thể bỏ bớt nhiễu hoặc bỏ fact của vế còn thiếu. Ta có thể thiết kế phép thử *same-prefix trên path KG*: giữ claim + path cho vế 1, so việc thêm path trùng vế 1 với thêm path chứng minh vế 2, trong cùng 32-path budget. Đây sẽ là **mở rộng sang evidence graph/FactKG và lỗi Conjunction của R3/V4**, không được tuyên bố phát minh lại phép thử same-prefix. [Limitations của paper](https://aclanthology.org/2026.findings-emnlp.747.pdf).

## 4. Vì sao accuracy thấp hơn FEVER 2026 vẫn có thể công bố?

**Không có quy tắc “paper mới phải có overall accuracy cao nhất lịch sử”.** Một công trình có thể đóng góp thuật toán, phân tích lỗi có kiểm soát, benchmark/metric mới, khả năng giải thích, độ tin cậy, hoặc trade-off chất lượng–chi phí. Nhưng điều đó **không miễn** yêu cầu so baseline mạnh, cùng protocol, và giới hạn phát biểu SOTA.

- **DARE 88,12%:** đóng góp là vòng tìm–phản biện–tìm tiếp và so với PGR 86,82% trong thiết lập agent/program. Không nên diễn giải là tốt hơn BERT one-hop 92,68% về overall. Nó còn thua PGR ở riêng Conjunction; đây là chi tiết quan trọng với mục tiêu của ta.
- **TrustFV 90,07%:** đóng góp là path sinh hợp lệ theo KG + reward và prune từng bước, với ablation và thử thêm trên CWQ. Tuy vậy, bảng của họ không đưa BERT one-hop 92,68% vào so trực tiếp và cách chia train/dev khác; bởi thế **không gọi nó là SOTA FactKG tuyệt đối**. Bản thân accuracy theo từng paper chỉ có ý nghĩa sau khi xét nguồn evidence, training budget, backbone, inference cost và tập baseline.
- **More Evidence…:** không thi “điểm cao nhất FactKG”. Họ cho thấy **hai model điểm cuối gần nhau có độ nhạy lặp evidence khác xa**, và cung cấp phép thử riêng cho *fact mới* so với *fact lặp*. Một paper diagnostic tốt có thể rất có giá trị dù model minh họa không đứng đầu leaderboard.

Nói cách khác, paper của mình **không buộc phải đạt >92,68% mới có giá trị**, nhưng nếu thấp hơn thì phải có luận điểm được đo rõ, chẳng hạn: cùng ngân sách evidence, giảm False→True ở Conjunction, tăng proof coverage và độ bền khi lặp path, hoặc đạt chất lượng gần ngang với ít thời gian/GPU/LLM calls hơn. Nếu chỉ đổi `walk5` thành `walk7` và báo overall tăng nhỏ trên test đã dùng để lựa chọn cấu hình, luận điểm paper sẽ yếu.

## 5. Hướng thực nghiệm kế tiếp cho R3 → V4

1. **Audit nguyên nhân trên dev kiểu test.** Với mẫu Conjunction True/False, gắn nhãn mỗi vế `support / contradict / chưa thấy`, rồi xác định nó có mặt trong KG, trong candidate R3, trong top-32 V4 hay không. Không đồng nhất “chưa tìm thấy” với “sai”.
2. **Diagnostic same-prefix cho path KG.** Giữ cố định claim và các path ban đầu; thêm path trùng một vế hoặc path cho vế còn thiếu; đo thay đổi xác suất True/False và lỗi riêng Conjunction False. Đây là chỗ nối *More Evidence…* với hiện tượng `walk5/ranked5`.
3. **Chỉ sau khi biết nút thắt mới chọn sửa.** Thiếu proof trước top-32 → chọn path theo độ phủ vế/duyệt bổ sung có ngân sách. Proof đã đủ mà V4 vẫn sai → train verifier theo từng vế hoặc loss chống đếm lặp; so với pooling V4 và baseline BERT one-hop. Báo accuracy **và** evidence coverage, phản ứng trước can thiệp, chi phí, seed. Chọn cấu hình trên dev, giữ test 9.041 claim cho đánh giá cuối.

**Phát biểu paper khả thi, còn cần chứng minh:** *Kiểm chứng FactKG không chỉ cần nhiều path liên quan; cần evidence mới cho từng phần của claim và verifier không được coi path lặp là nhiều chứng cứ độc lập. Một pipeline KG-path có ngân sách, theo dõi độ phủ vế và tình trạng chưa quan sát, có thể cải thiện tính đúng và tính trung thực của proof với chi phí thấp.*
