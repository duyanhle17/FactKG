# Đọc ba paper liên quan đến hướng FactKG hiện tại

**Phạm vi.** Trong tài liệu này, “FEVER 2024” chỉ paper *The Automated Verification of Textual Claims (AVeriTeC) Shared Task* đăng tại workshop FEVER 2024; “FEVER 2026” chỉ paper *Evidence Grounding vs. Memorization: Why Neural Semantics Matter for Knowledge Graph Fact Verification* đăng tại FEVER 2026. FEVER là tên workshop; hai paper này không phải hai phiên bản liên tiếp của cùng một model. Paper thứ ba là *Fact Verification on Knowledge Graph via Programmatic Graph Reasoning* (PGR, Findings EMNLP 2025). Nếu “FEVER 2024” được dùng để chỉ một paper khác, cần thay riêng mục 1.

**Cách đọc điểm.** Accuracy trên FactKG, AVeriTeC score, điểm trên toàn test và điểm trên mẫu 300 câu là các đại lượng khác nhau. Bảng so sánh cuối tài liệu đặt chúng cạnh nhau để định vị bài toán. Muốn so **hệ thống đầu cuối**, cần kiểm tra cùng claim test, nhãn, KG/nguồn thông tin được phép dùng và metric; evidence được *truy xuất* có thể khác vì đó chính là một phần phương pháp. Muốn quy chênh lệch điểm cho **một thành phần** như cách gộp path, phải giữ các thành phần còn lại cố định.

## Từ vựng cần nắm trước

| Từ | Nghĩa trong các paper này | Dễ nhầm với |
| --- | --- | --- |
| `shot` | Một ví dụ mẫu được đặt **trong prompt lúc suy luận** để LLM bắt chước cách làm. `12-shot` nghĩa là prompt có 12 ví dụ mẫu; bản thân nó không có nghĩa fine-tune trên 12 câu. | Số hop trong KG; số epoch train; số câu của tập train. |
| `hop` | Số cạnh đi qua trong một đường KG. | Số bước của pipeline hoặc số shot trong prompt. |
| `top-5 relation` | Năm loại quan hệ do relation predictor chọn trước khi R3 duyệt KG. | `walk5`: giữ tối đa năm path thuộc nhóm `walkable` **sau** khi R3 đã dựng candidate. |
| `K=32 path` | Số path tối đa V4 đọc cho một claim, ưu tiên `connected`, rồi `walkable`. | Số relation được predictor dự đoán. |
| PGR “hai bước” | **Tạo chương trình** từ claim, rồi **thực thi chương trình** trên KG để lấy evidence và quyết định nhãn. Một chương trình vẫn có thể chứa nhiều lệnh và nhiều hop. | Bài toán chỉ có hai hop hoặc chỉ cần hai lần gọi LLM. |
| “Subgraph một hop” của FEVER 2026 | Lấy **mọi triple kề một cạnh** với các entity được nhắc trong claim; một subgraph có thể có hơn 50 triple. | Claim thuộc nhóm One-hop; phương pháp đã suy luận đủ một claim Multi-hop. |

## 1. FEVER 2024: AVeriTeC Shared Task

**Nguồn:** [paper ACL Anthology](https://aclanthology.org/2024.fever-1.1/), nhất là mục 2.1–2.4 và bảng 2 trong [PDF](https://aclanthology.org/2024.fever-1.1.pdf).

### Họ nghiên cứu gì, vì sao?

Đây chủ yếu là **paper mô tả dataset, shared task, baseline và kết quả các đội**, không phải paper đề xuất một model duy nhất. Tác giả cho rằng nhiều benchmark cũ có claim được tạo riêng cho nghiên cứu từ Wikipedia, chưa phản ánh tốt claim ngoài đời. Các dataset claim thực tế lại có thể thiếu annotation evidence đủ tốt. Vì vậy họ muốn đánh giá đồng thời: hệ thống **tìm được bằng chứng phù hợp** và **dựa trên đó dự đoán đúng verdict**.

### Dataset và nhãn

- **AVeriTeC, không phải FactKG.** Claim thực tế được thu từ các tổ chức fact-check qua ClaimReview/Google FactCheck Claim Search. Paper nói dataset gốc có 4.568 claim, sau khi mở rộng hidden test có tổng cộng 5.783 claim. Bảng kết quả shared task được tính trên 2.214 claim hidden test được đánh giá.
- Evidence là tài liệu web và thường được chuẩn hóa thành các cặp **câu hỏi – câu trả lời (Q–A)**, kèm URL. Bốn nhãn: `Supported`, `Refuted`, `Not Enough Evidence`, `Conflicting Evidence/Cherrypicking`.
- FactKG trong repo dùng DBpedia 2015 và nhãn **True/False**. Vậy ngay cả khi cùng gọi là “fact verification”, nguồn bằng chứng, số nhãn và cách chấm đều khác. [AVeriTeC task description](https://aclanthology.org/2024.fever-1.1.pdf)

### Flow cụ thể: **baseline của ban tổ chức**

| Bước | Đầu vào → đầu ra | Chức năng |
| --- | --- | --- |
| 1. Nguồn evidence | Claim + kho tài liệu web đã biên soạn hoặc kết quả tìm web → tài liệu khả dĩ | Đưa evidence bên ngoài vào pipeline. |
| 2. Lấy câu | Tài liệu → câu văn → BM25 giữ 100 câu gần claim nhất | Thu hẹp không gian tìm kiếm. |
| 3. Tạo Q–A | Claim + 100 câu → BLOOM sinh cặp Q–A | Biến evidence thành những câu hỏi kiểm chứng cụ thể. Prompt của baseline dùng **10 ví dụ mẫu** từ train; đây là in-context examples, không phải 10 hop. |
| 4. Xếp lại evidence | Các Q–A → BERT rerank → 3 Q–A đứng đầu | Chọn evidence đưa cho verifier. |
| 5. Verdict | Claim + 3 Q–A → BERT → một trong bốn nhãn | Kiểm chứng claim. |
| 6. Chấm điểm | Verdict + evidence đã nộp → AVeriTeC score | Chỉ được tính đúng nếu verdict đúng **và** evidence Q–A đạt ngưỡng chất lượng. |

Flow trên là **baseline**, không phải kiến trúc của đội thắng `TUDA_MAI`. Các đội có thể dùng phương pháp khác. Paper mô tả baseline ở [mục 2.3](https://aclanthology.org/2024.fever-1.1.pdf).

**AVeriTeC score là gì?** Hệ thống ghép các Q–A dự đoán với Q–A tham chiếu bằng Hungarian matching, dùng METEOR đo tương đồng. Nếu điểm evidence dưới **0,25**, claim nhận **0** cho AVeriTeC score dù verdict tình cờ đúng; nếu qua ngưỡng thì mới xét verdict. Chỉ tối đa 10 Q–A đầu được tính vào phép chấm evidence. Đây **không phải accuracy thuần túy**. [Mục 2.4](https://aclanthology.org/2024.fever-1.1.pdf)

### Kết quả và giới hạn khi áp dụng sang repo

Baseline của ban tổ chức đạt **11% AVeriTeC score**, đội thắng `TUDA_MAI` đạt **63%**. `63%` là điểm của **đội thắng**, không phải của baseline trong bảng flow phía trên. Không được diễn giải “V4 đạt 86,74% nên hơn 63%”: hai con số dùng dataset và metric khác nhau. Paper cũng ghi nhận có lỗi trong knowledge store ban đầu: một số tài liệu fact-check viết về chính claim đã lọt vào kho; tác giả sau đó phát hành kho đã sửa. [Bảng 2 và phần mô tả dữ liệu](https://aclanthology.org/2024.fever-1.1.pdf)

**Bài học cho FactKG:** đánh giá nhãn cùng với **tính đầy đủ của evidence**. Với claim hai vế, đúng nhãn nhưng path chỉ chứng minh một vế chưa phải một lời giải thích tốt. Tuy nhiên, muốn áp dụng tinh thần này, ta cần tạo phép chấm evidence trên KG; không thể bê nguyên METEOR của Q–A web sang path DBpedia.

## 2. FEVER 2026: Evidence Grounding vs. Memorization

**Nguồn:** [paper ACL Anthology](https://aclanthology.org/2026.fever-1.3/), đặc biệt mục 3, 5, 7, 8 và bảng 2–8 trong [PDF](https://aclanthology.org/2026.fever-1.3.pdf).

### Họ nghiên cứu gì, vì sao?

Paper hỏi: trên fact verification bằng KG, kết quả đến từ **cấu trúc graph**, từ **ngữ nghĩa token của encoder**, từ **việc chọn evidence**, hay từ kiến thức LLM đã nhớ sẵn? Tác giả coi đây là một nghiên cứu đối chứng nhiều nhánh, **không có một model duy nhất gọi là “FEVER 2026”**. Một động cơ quan trọng là subgraph quanh entity rất dày: khi nối mọi triple thành văn bản, BERT có thể cắt bỏ thông tin ở giới hạn token. [Giới thiệu và mục 3](https://aclanthology.org/2026.fever-1.3.pdf)

### Dataset và protocol

- **Cùng nguồn benchmark FactKG** và DBpedia với repo của bạn; test có **9.041 claim** và nhãn nhị phân. Vì vậy overall test accuracy đáng để đối chiếu về mặt bài toán.
- **Đầu vào evidence khác:** paper lấy *toàn bộ triple cách một cạnh* từ các entity của claim, rồi chuyển subgraph này thành văn bản. Họ **không** dùng relation top-5 → hop predictor → R3 → tối đa 32 path như repo.
- **Cách chia reasoning type cũng khác:** paper cho phép một claim nằm ở nhiều nhóm, có thêm nhóm `Substitution`, và báo `Multi-claim` **3.293** claim test. `baseline.py` của repo gán một nhóm ưu tiên duy nhất, với `Conjunction` **3.069** claim test. Do đó không so trực tiếp `Multi-claim 96,42%` của paper với `Conjunction 84,03%` của repo như thể hai mẫu giống hệt. [Dataset và taxonomy](https://aclanthology.org/2026.fever-1.3.pdf)

### Flow: năm nhánh thí nghiệm, không phải một pipeline nối tiếp

| Nhánh | Flow thực tế | Câu hỏi mà nhánh trả lời |
| --- | --- | --- |
| A. Ký hiệu | Claim + subgraph một hop → 29 feature về cấu trúc/entity/relation → Logistic Regression, Random Forest hoặc XGBoost → True/False | Chỉ dùng feature giải thích được thì đủ chưa? |
| B. BERT trên KG | Claim + **toàn bộ** subgraph một hop đã viết thành chuỗi triple → BERT-base, tối đa 512 token → classifier True/False | Encoder đọc ngữ nghĩa triple mạnh đến đâu? |
| C. GNN | Claim + subgraph một hop → QA-GNN hoặc biến thể có cross-attention → True/False | Message passing trên graph có hơn cách đọc triple như văn bản không? |
| D. Lọc evidence | Subgraph một hop → prefilter từ vựng → LLM chấm liên quan → chọn top-10 triple → BERT | Giảm evidence và chọn đúng evidence đóng góp bao nhiêu? |
| E. LLM có/không KG | Cùng **300 claim được chọn từ test** → LLM chỉ đọc claim **hoặc** đọc claim + subgraph → verdict và giải thích | KG evidence có giúp hơn kiến thức LLM nhớ sẵn không? |

Ở nhánh D, quy trình lọc chi tiết là: giữ tối đa 24 triple bằng heuristic/từ vựng → GPT-4.1-mini chấm mức liên quan → kết hợp thứ hạng LLM và từ vựng → giữ 10 triple. Nhánh E dùng **10 ví dụ mẫu trong prompt** có verdict và chỉ số triple. `10-shot` ở đây, tương tự `12-shot` của PGR, là ví dụ lúc suy luận chứ không phải số epoch train. [Mục 7 và 8](https://aclanthology.org/2026.fever-1.3.pdf)

### Kết quả: mỗi con số thuộc một điều kiện khác nhau

| Điều kiện | Điểm paper báo | Phạm vi đúng của con số |
| --- | ---: | --- |
| BERT trên subgraph một hop, train full (tái lập trong FEVER 2026) | **92,68% accuracy** | Toàn FactKG test 9.041 claim; BERT-base nhận claim + danh sách triple, giới hạn 512 token, fine-tune toàn bộ tham số. |
| [BERT một hop của Opsahl (2024)](https://aclanthology.org/2024.fever-1.32.pdf), được FEVER 2026 dẫn lại | **93,49% accuracy** | Kết quả **công trình trước**, không phải điểm model mới của FEVER 2026. Nếu đặt mục tiêu dẫn đầu overall accuracy, cần đối chiếu cả mốc này. |
| XGBoost feature ký hiệu | **66,54% accuracy** | Toàn test, nhưng evidence/feature khác V4. |
| QA-GNN và biến thể | **69,64% / 69,74% accuracy** | Toàn test trong protocol subgraph một hop. |
| BERT, tập train chỉ **9.645 claim**, evidence top-10 do LLM lọc | **78,85% accuracy** | Không phải mốc full-train 92,68%; là thí nghiệm lọc evidence trên khoảng 10% train. |
| Cùng ngân sách 10 triple, chọn bằng heuristic từ vựng | **77,54% accuracy** | So có kiểm soát với 78,85%: LLM thêm **1,31 điểm phần trăm**. |
| GPT-4o-mini: chỉ claim → claim + KG | **71,67% → 84,33% accuracy** | Chỉ **300 claim test** được chọn, không phải toàn 9.041. |
| GPT-4.1-mini: chỉ claim → claim + KG | **74,67% → 84,00% accuracy** | Cùng mẫu 300 claim. |

Số liệu ở [bảng BERT/GNN](https://aclanthology.org/2026.fever-1.3.pdf), [bảng lọc evidence](https://aclanthology.org/2026.fever-1.3.pdf) và [bảng LLM](https://aclanthology.org/2026.fever-1.3.pdf). Riêng các điểm theo reasoning type của paper dùng **nhóm chồng lấn**, nên chưa thể trừ trực tiếp với các nhóm loại trừ nhau trong báo cáo R3/V4.

### Limitations tác giả nêu và điều cần kiểm tra thêm

| Giới hạn trong FEVER 2026 | Hệ quả khi đọc điểm | Câu hỏi nghiên cứu tiếp cho FactKG của bạn |
| --- | --- | --- |
| **Một hop cho mọi nhánh thí nghiệm:** lấy các triple kề entity có trong claim; claim Multi-hop có thể cần cạnh trung gian ngoài subgraph này. | Overall 92,68% không chứng minh model đã truy xuất đủ chuỗi chứng cứ nhiều hop. Trong taxonomy của paper, BERT đạt **80,08% Multi-hop**, thấp hơn nhiều so với overall; không so trực tiếp với 81,16% Multi-hop của repo vì cách gán nhóm khác nhau. | Khi nào cần mở rộng graph qua entity trung gian, mở rộng theo relation nào, và dừng lúc nào để có proof đủ trong ngân sách? |
| **Subgraph dày và BERT giới hạn 512 token:** nhiều đầu vào bị cắt. | Điểm số có thể phụ thuộc mạnh vào thứ tự triple và lượng evidence được giữ. Nhánh lọc top-10 chỉ dùng 9.645 claim train; không thể lấy 78,85% để kết luận lọc evidence kém hơn 92,68% khi ngân sách train khác. | So các cách chọn path/triple với cùng số token hoặc path, cùng train split và cùng verifier; đo tỷ lệ proof còn nguyên sau khi cắt. |
| **Đánh giá LLM chỉ trên 300 claim test** và chỉ dùng GPT-4o-mini, GPT-4.1-mini. | Mức 84,33%/84,00% khi có KG chưa đại diện chắc chắn cho toàn bộ 9.041 claim hoặc các model khác. | Nếu dùng LLM, đánh giá đủ mẫu hoặc nêu rõ sai số và phạm vi; so với một model nhỏ có cùng evidence. |
| **Có citation chưa chứng minh suy luận trung thực:** paper chưa xác minh thủ công các triple được trích có thực sự entail/contradict claim hay không. | Một verdict đúng vẫn có thể đi kèm proof sai hoặc chỉ chứng minh một phần claim. | Tạo tập kiểm tra proof theo từng vế; xóa, tráo entity hoặc thay cạnh thiết yếu rồi đo verdict có đổi đúng không. |

Các giới hạn và hướng tiếp theo ở đây dựa trên [mục 12: Limitations](https://aclanthology.org/2026.fever-1.3.pdf); các con số BERT nằm ở [bảng 2–3](https://aclanthology.org/2026.fever-1.3.pdf). Tác giả cũng **đã đề xuất** học cách chọn cạnh để duyệt thay vì mở rộng một hop cố định. Vì vậy chỉ nói “retrieval nhiều bước có học” chưa đủ là đóng góp mới; cần chỉ rõ cách biểu diễn trạng thái chứng cứ, chính sách chọn cạnh/dừng, và điều kiện cho thấy nó tốt hơn các heuristic cùng ngân sách.

### Hướng paper rút ra cho R3/V4

**Câu hỏi đề xuất:** Làm sao tìm được **tập path nối được và đủ cho mọi điều kiện của claim** trong ngân sách evidence, rồi đưa ra verdict phụ thuộc thực sự vào tập path đó? Đây là giả thuyết cần kiểm tra, chưa phải kết luận rằng thuật toán mới sẽ vượt 93,49% overall.

| Việc cần làm | Kết quả dùng để quyết định hướng nghiên cứu |
| --- | --- |
| Audit trên **dev có candidate do predictor + R3 sinh ra**: với từng claim sai, đánh dấu fact có trong KG, relation được dự đoán, path được R3 tạo, path có lọt top-32 và V4 có dùng đúng không. | Nếu thường thiếu cạnh/path thì phát triển retriever; nếu proof đã đủ mà verdict sai thì phát triển verifier theo từng vế. |
| Thử retriever có trạng thái các điều kiện **chưa được chứng minh**: chọn bước mở rộng relation/entity tiếp theo, giữ chuỗi path nối được, dừng khi đủ proof hoặc hết ngân sách. Bắt đầu từ heuristic; chỉ huấn luyện chính sách nếu heuristic chưa đủ. | Đo proof recall/coverage, accuracy và số cạnh/token/chi phí; ablation riêng quyết định chọn cạnh, chọn path và dừng. |
| So **R3/V4, BERT một hop, heuristic chọn top-K** dưới cùng split và ngân sách evidence khi có thể; thêm thử nghiệm xóa/thay cạnh thiết yếu. | Xác định lợi ích đến từ thuật toán retrieval hay từ nhiều evidence/model mạnh hơn; kiểm tra verdict có grounding không. |

**Tiêu chí thành công:** cạnh tranh với các mốc **92,68%** (tái lập FEVER 2026) và **93,49%** ([Opsahl 2024](https://aclanthology.org/2024.fever-1.32.pdf)) về overall, đồng thời cải thiện retrieval/proof trên claim khó, độ trung thực của verdict và/hoặc chi phí suy luận. Chỉ vượt 92,68% vài phần mười điểm mà không kiểm soát protocol hoặc không chứng minh đóng góp phương pháp thì chưa phải câu chuyện paper đủ mạnh.

## 3. PGR 2025: Programmatic Graph Reasoning

**Nguồn:** [paper ACL Anthology](https://aclanthology.org/2025.findings-emnlp.293/), nhất là mục 3–4, bảng 1 và phần limitations trong [PDF](https://aclanthology.org/2025.findings-emnlp.293.pdf).

### Họ nghiên cứu gì, vì sao?

PGR cho rằng nhiều hệ thống KG verification lấy triple rồi đưa claim + triple vào NLI/LLM để đoán nhãn theo cách **ngầm**. Với Conjunction và Multi-hop, khó thấy hệ thống đã kiểm tra từng quan hệ nào, nối entity trung gian ra sao và hỏng ở bước nào. PGR chuyển claim thành một **chương trình graph** có thể đọc và thực thi từng lệnh. [Mục 1 và 3](https://aclanthology.org/2025.findings-emnlp.293.pdf)

### Dataset và training strategy

- **Cùng benchmark FactKG**, dùng DBpedia 2015 và test **9.041 claim**; paper báo nhóm Conjunction/Multi-claim **3.069** claim theo cách chia năm nhóm, gần với báo cáo của repo hơn FEVER 2026.
- PGR chính dùng `gpt-4o-2024-08-06` theo chiến lược **few-shot prompting**, không fine-tune BERT verifier như V4. Vì model, chi phí suy luận và dữ liệu huấn luyện khác, đây là đối thủ end-to-end, **không phải** một ablation chỉ thay tầng aggregation của V4. [Thiết lập và bảng 1](https://aclanthology.org/2025.findings-emnlp.293.pdf)

### “Hai bước” của PGR và từng hàm làm gì

| Bước | Đầu vào → đầu ra | Việc xảy ra |
| --- | --- | --- |
| **1. Program generation** | Claim → một chuỗi lệnh có biến trung gian | LLM phân rã câu thành điều kiện cần kiểm tra và viết chương trình dùng `SEARCH`, `MATCH`, `VERIFY`. |
| **2. Graph reasoning / program execution** | Chương trình + KG → evidence trung gian → True/False | Chạy các lệnh theo thứ tự, mang kết quả lệnh trước sang lệnh sau. `MATCH`/`SEARCH` trong triển khai còn dùng LLM lọc triple liên quan. |

| Hàm | Hiểu đơn giản | Ví dụ |
| --- | --- | --- |
| `MATCH(h, r, t)` | Kiểm tra một quan hệ giữa hai entity đã biết có được KG hỗ trợ không. | `MATCH(Baymax, appearedIn, BigHero6)` |
| `SEARCH(h, r, ?)` | Tìm entity chưa biết để nối chuỗi suy luận. | `SEARCH(Person, bornIn, ?city)` |
| `VERIFY(...)` | Ghép các kết quả theo logic của claim, gồm `and` và phủ định khi cần. | `VERIFY(r1 and r2 and r3)` |

Ví dụ Conjunction trong paper: claim có ba sự kiện về Baymax được viết thành **ba `MATCH`**, cuối cùng `VERIFY(r1 and r2 and r3)`. Đây là *cấu trúc chương trình* do LLM sinh; nếu LLM phân rã thiếu vế hoặc ánh xạ nhầm relation, kết quả vẫn sai. [Hình 2 và định nghĩa hàm](https://aclanthology.org/2025.findings-emnlp.293.pdf)

### “12-shot” chính xác là gì?

Khi yêu cầu GPT-4o viết chương trình cho một claim mới, tác giả đặt **12 ví dụ đã làm mẫu** vào prompt để nó nhìn cách chuyển claim thành chương trình. Đây là `12-shot`. Trong giai đoạn thực thi, prompt của các thao tác `MATCH`/`SEARCH` dùng **4 ví dụ mẫu** (`4-shot`) để LLM lọc triple. Vì thế PGR không đơn giản là “gọi LLM một lần, rồi dùng graph thuần ký hiệu”; phần tìm/match KG của triển khai vẫn có LLM. `12-shot` **không** có nghĩa chỉ có 12 claim trong FactKG, không có nghĩa chương trình đi 12 hop, và cũng không phải 12 lần fine-tune. [Mục 4.3](https://aclanthology.org/2025.findings-emnlp.293.pdf)

### Điểm và giới hạn

| Nhóm FactKG test | PGR accuracy |
| --- | ---: |
| Overall | **86,82%** |
| One-hop | **93,30%** |
| Existence | **93,10%** |
| Multi-hop | **75,96%** |
| Multi-claim/Conjunction | **89,95%** |
| Negation | **81,16%** |

Đây là số paper báo ở [bảng 1](https://aclanthology.org/2025.findings-emnlp.293.pdf). Tác giả tự chỉ ra lỗi do sinh chương trình sai, xử lý biến/logic sai và thực thi chương trình chưa đủ mạnh; tập ví dụ few-shot hạn chế cũng có thể không phủ claim lạ. [Error analysis và limitations](https://aclanthology.org/2025.findings-emnlp.293.pdf)

**Bài học cho FactKG của bạn:** PGR đã làm **phân rã claim + AND**. Nếu paper mới chỉ nói “thêm kiểm tra từng vế và lấy AND”, đóng góp sẽ khó phân biệt với PGR. Điểm có thể phát triển là **kiểm soát mức độ đủ evidence và mức không chắc chắn** khi một vế không được tìm thấy, hoặc dùng verifier nhỏ để rẻ hơn mà vẫn giải thích được từng vế.

## 4. FactKG trong repo này đang chạy thế nào?

**Nguồn nội bộ:** [README](README.md), [retriever](with_evidence/classifier/faico_lite_retrieval.py), [preprocess](with_evidence/classifier/preprocess.py), [GEARLite V4](with_evidence/classifier/baseline.py), [báo cáo 8–19/10](báo%20cáo%2014_10.md).

### Cần tách flow huấn luyện và flow suy luận

| Pha | Flow hiện tại | Ghi chú quan trọng |
| --- | --- | --- |
| Học retriever | FactKG train + Evidence vàng → train **relation predictor** và **hop predictor** → checkpoint | Relation predictor chọn top-5 relation; hop predictor chọn độ dài `H` cho suy luận test. |
| Học verifier | FactKG **train/dev Evidence vàng** → R3 dùng chuỗi relation vàng tìm path **thật trong DBpedia** → `connected` và `walkable` → train/chọn checkpoint V4 | Evidence vàng là **chuỗi relation**, không phải path cụ thể dựng sẵn. Dev thông thường dùng candidate theo Evidence vàng. |
| Suy luận test | Claim + `Entity_set` → relation predictor `top-5` + hop predictor `H` → R3 duyệt path trong DBpedia, cho path dài `1..H` và lặp relation tối đa 2 lần → ưu tiên `connected`, rồi `walkable` → V4 đọc tối đa `K=32` path → True/False | V4 mã hóa từng cặp Claim–Path, dùng `c_claim`, trung bình candidate `c_set` và attention để gộp path. Không có phép kiểm tra từng vế tường minh. |
| Thử nghiệm `walk5` | Giữ checkpoint V4 và path `connected`; chỉ giới hạn còn tối đa **5 path `walkable`** ở đầu vào suy luận | Đây là **inference ablation**, chưa phải model mới được train với chính sách walk5. `walk5` không có nghĩa relation top-5. |

**Độ lệch hiện tại:** verifier được train/chọn trên candidate theo Evidence vàng, nhưng test phải dựa vào relation/hop dự đoán. Repo đã tạo dev “giống test” để chẩn đoán, nhưng cần giữ rõ nó khác dev vàng khi diễn giải kết quả. [Preprocess](with_evidence/classifier/preprocess.py), [báo cáo](báo%20cáo%2014_10.md).

## 5. So sánh flow: điểm nào tương ứng, điểm nào không?

| Chặng | AVeriTeC/FEVER 2024 baseline | FEVER 2026 trên FactKG | PGR trên FactKG | Repo của bạn: R3 + V4 |
| --- | --- | --- | --- | --- |
| Claim và nhãn | Claim web; **4 nhãn** | FactKG; **2 nhãn** | FactKG; **2 nhãn** | FactKG; **2 nhãn** |
| Kho evidence | Tài liệu web hoặc knowledge store | DBpedia, mọi triple kề entity claim trong **một hop** | DBpedia 2015 | DBpedia 2015 |
| Xác định cần tìm gì | BM25 câu liên quan; BLOOM sinh Q–A | Toàn subgraph một hop; một nhánh thử heuristic/LLM chọn triple | LLM sinh các phép `MATCH`/`SEARCH` cho từng điều kiện | Relation predictor top-5 + hop predictor `H` |
| Dựng/chọn evidence | BERT rerank Q–A, chọn top-3 | BERT full dùng cả subgraph; thí nghiệm lọc dùng top-10 triple | Chạy chương trình, `MATCH`/`SEARCH` có LLM hỗ trợ lọc triple | R3 duyệt path `1..H`, chia `connected`/`walkable`, V4 lấy tối đa 32 path |
| Ra verdict | BERT trên claim + Q–A | BERT/GNN/LLM tùy nhánh thí nghiệm | `VERIFY` theo logic của chương trình | BERT Claim–Path + attention V4, chưa có nhãn từng vế |
| Chấm evidence | Q–A METEOR + verdict, metric AVeriTeC | Chủ yếu accuracy; có kiểm tra evidence/citation ở thí nghiệm LLM | Có chương trình/evidence trung gian, bảng chính báo accuracy | Chủ yếu accuracy/F1; có audit path, pilot từng vế nhưng chưa có metric proof coverage chính thức |

## 6. So sánh điểm, kèm điều kiện đọc

| Hệ thống/điều kiện | Dataset test | Metric | Overall | Multi-hop | Conjunction/Multi-claim | Có thể kết luận gì? |
| --- | --- | --- | ---: | ---: | ---: | --- |
| FEVER 2024 baseline | AVeriTeC, 2.214 claim hidden | AVeriTeC score | **11%** | — | — | Không so số học với FactKG. |
| FEVER 2024 đội thắng `TUDA_MAI` | AVeriTeC, cùng hidden test | AVeriTeC score | **63%** | — | — | Đây là điểm **đội thắng**, không phải baseline paper. Không so số học với FactKG. |
| FEVER 2026 BERT, full one-hop subgraph | FactKG, 9.041 claim | Accuracy | **92,68%** | **80,08%** | **96,42%** | Overall là baseline đầu cuối rất mạnh cần đối chiếu protocol; theo nhóm **không cùng taxonomy** repo. |
| FEVER 2026 LLM-filtered BERT, chỉ 9.645 train | FactKG, 9.041 claim | Accuracy | **78,85%** | **75,45%** | **80,66%** | Thí nghiệm về evidence selection, không so như mốc full-train. |
| FEVER 2026 GPT-4o-mini có KG | FactKG, **mẫu 300 claim** | Accuracy | **84,33%** | — | — | Mẫu nhỏ có điều kiện chọn; không so với toàn 9.041. |
| PGR GPT-4o, 12-shot | FactKG, 9.041 claim | Accuracy | **86,82%** | **75,96%** | **89,95%** | Đáng đối chiếu bài toán với repo; khác phương pháp, model và chi phí. |
| Repo: R3 Full + V4 | FactKG, 9.041 claim | Accuracy | **86,74%** | **81,16%** | **84,03%** | Mốc local được báo cáo cho checkpoint R3 rerun. |
| Repo: R3 + `walk5`, cùng checkpoint V4 | FactKG, 9.041 claim | Accuracy | **87,55%** | **81,54%** | **85,76%** | Kết quả **thăm dò trên test đã xem nhiều lần**; không dùng để tuyên bố đã vượt PGR. |

Ba điểm cần nhớ khi đọc bảng:

1. **FEVER 2024 dùng dataset/metric khác hẳn.** `63% AVeriTeC score` và `86,74% FactKG accuracy` không có phép trừ ý nghĩa.
2. **PGR và repo gần nhau về overall nhưng khác điểm mạnh.** PGR cao hơn ở Conjunction/Multi-claim (**89,95%** so với **84,03%**); repo cao hơn ở Multi-hop (**81,16%** so với **75,96%**), Existence (**94,94%** so với **93,10%**) và Negation (**88,43%** so với **81,16%**). Đây là đối chiếu chéo paper, chưa phải phép ablation kiểm soát cùng implementation.
3. **FEVER 2026 BERT 92,68% là cảnh báo quan trọng về baseline.** Không thể nói R3 + V4 hiện dẫn đầu FactKG; muốn so công bằng cần tái lập cùng dữ liệu, entity set, KG, cách dựng evidence, split và metric. Riêng per-type của paper 2026 còn dùng nhãn nhóm chồng lấn.

## 7. Ý tưởng cập nhật FactKG: từ “đoán nhãn” đến “proof đủ cho từng vế”

### Câu hỏi paper khả thi

**Làm sao kiểm chứng claim nhiều vế khi retriever chỉ tìm được bằng chứng cho một phần claim, trong khi vẫn phân biệt được “chưa tìm thấy” với “KG đã bác bỏ”?** Đây là câu hỏi hẹp hơn việc thêm LLM hay thêm phép `AND`; nó nối bài học về evidence sufficiency của AVeriTeC với lỗi Conjunction đang quan sát ở R3/V4, và giải quyết một trường hợp khó của PGR: chương trình đúng cú pháp nhưng evidence thực thi không đầy đủ.

Hiện báo cáo repo ghi: `walk5` làm Conjunction True tốt hơn, nhưng tăng số lỗi ở Conjunction False; pilot dev có **5 câu False** mà R3 đã lưu path khớp **1/2 vế** nhưng V4 đoán True, và **2 câu True** đã có path cho **2/2 vế** nhưng V4 đoán False với `first5`. Mẫu pilot chỉ hỗ trợ đặt giả thuyết, chưa đại diện toàn tập. [Báo cáo](báo%20cáo%2014_10.md), [pilot](conjunction_clause_pilot_20261019_154232.md).

### Lộ trình thực nghiệm nên làm theo thứ tự

| Bước | Thay đổi/đo lường | Tại sao cần trước bước sau |
| --- | --- | --- |
| 1. Chốt protocol | Xác nhận cùng claim IDs và split với PGR/FEVER 2026; ghi rõ KG, `Entity_set`, kiểu evidence, taxonomy, seed và checkpoint. Chọn cấu hình trên dev; dành test cho đánh giá cuối. | Không thể biến đối chiếu chéo paper thành khẳng định cải thiện nếu protocol khác. |
| 2. Audit từng vế trên **dev kiểu test** | Với mẫu Conjunction True/False, đánh dấu từng vế: có fact trong KG? relation predictor lấy được? R3 dựng được? path nằm trong đầu vào top-32? V4 đoán gì? Đánh dấu `support`, `contradict`, `not found/unknown` riêng. | Xác định nút thắt ở retrieval hay verifier. Một path không xuất hiện **không tự chứng minh claim sai**. |
| 3. Metric evidence | Báo relation coverage, proof/ clause coverage trước và sau top-32, false positive khi chỉ 1/2 vế có evidence, cùng accuracy/F1 theo True/False. Các annotation Evidence vàng chỉ là tham chiếu, cần đọc thủ công các ca không khớp. | Đưa “evidence đủ” thành kết quả đo được, theo tinh thần FEVER 2024. |
| 4a. Nếu thiếu proof ở đầu vào | Thử chọn path có độ phủ relation/entity/vế tốt hơn trong **cùng ngân sách 32**, so với first-K, ranked-K, random-K. | Theo FEVER 2026, cần giữ ngân sách evidence để tách lợi ích chọn đúng khỏi lợi ích giảm số lượng. |
| 4b. Nếu proof đã đủ mà V4 sai | Thử verifier có score riêng cho từng vế, rồi aggregation có trạng thái `unknown` nội bộ; đầu ra cuối vẫn map về True/False để chấm FactKG. Train thêm hard negative chỉ sai một vế. | PGR đã có AND; đóng góp phải nằm ở xử lý evidence không đầy đủ/không chắc chắn và độ trung thực của quyết định. |
| 5. Baseline mạnh | Tái lập BERT đọc subgraph một hop của FEVER 2026 và một baseline kiểm tra từng vế đơn giản; nếu có điều kiện, đối chiếu PGR cùng protocol. | Nếu hệ mới không hơn 92,68% overall, paper vẫn có thể có đóng góp về proof faithfulness/efficiency, nhưng phải chứng minh rõ. |
| 6. Kiểm tra nhân quả | Xóa path chứng minh một vế, thay bằng path sai entity, tráo một vế trong claim và đo prediction đổi thế nào; báo thời gian, số path và chi phí LLM nếu có. | Attention hoặc citation đẹp chưa chứng minh model thực sự phụ thuộc vào evidence đúng. |

**Giả thuyết nên kiểm tra, chưa phải kết luận:** một chính sách chọn path **cân bằng độ phủ các vế** kết hợp verifier biết phân biệt support/contradict/unknown sẽ giảm lỗi False → True do “một vế đúng kéo cả câu thành True”, mà vẫn giữ cải thiện Multi-hop của R3. Nếu audit cho thấy phần lớn lỗi là relation predictor bỏ sót relation, trọng tâm paper nên chuyển về retrieval theo từng vế thay vì đổi V4.

## Nguồn chính để đọc tiếp

1. Schlichtkrull et al. (2024), [*The Automated Verification of Textual Claims (AVeriTeC) Shared Task*](https://aclanthology.org/2024.fever-1.1/).
2. Upadhyay et al. (2026), [*Evidence Grounding vs. Memorization: Why Neural Semantics Matter for Knowledge Graph Fact Verification*](https://aclanthology.org/2026.fever-1.3/).
3. Hao & Wu (2025), [*Fact Verification on Knowledge Graph via Programmatic Graph Reasoning*](https://aclanthology.org/2025.findings-emnlp.293/).
4. Trong repo: [báo cáo thực nghiệm mới nhất](báo%20cáo%2014_10.md), [pilot từng vế](conjunction_clause_pilot_20261019_154232.md), [mã retriever R3](with_evidence/classifier/faico_lite_retrieval.py), [mã V4](with_evidence/classifier/baseline.py).
