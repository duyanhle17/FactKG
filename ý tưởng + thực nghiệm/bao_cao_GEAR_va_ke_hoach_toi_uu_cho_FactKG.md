# Báo cáo GEAR và kế hoạch tối ưu cho FactKG

**Ngày cập nhật:** 28/06/2026  
**Người thực hiện:** Lê Duy Anh  
**Paper tham chiếu:** *GEAR: Graph-based Evidence Aggregating and Reasoning for Fact Verification* (ACL 2019)

---

## 1. Phạm vi báo cáo

Báo cáo gồm hai phần cần được phân biệt rõ:

1. **Phân tích paper GEAR:** mô tả những gì tác giả thực sự đề xuất và kiểm chứng trên FEVER.
2. **Kế hoạch áp dụng cho FactKG:** các suy luận kỹ thuật và giả thuyết cần được kiểm chứng bằng thực nghiệm riêng trên FactKG.

GEAR không trực tiếp thử nghiệm trên knowledge graph và không đề xuất mô hình mang tên “GEAR-lite”. Vì vậy, các dự đoán về hiệu quả của GEAR-lite trong báo cáo này không phải là kết luận của paper.

---

## 2. Tổng quan paper GEAR

### 2.1. Thông tin cơ bản

| Mục | Nội dung |
|:---|:---|
| **Tên đầy đủ** | GEAR: Graph-based Evidence Aggregating and Reasoning for Fact Verification |
| **Tác giả** | Jie Zhou, Xu Han, Cheng Yang, Zhiyuan Liu, Lifeng Wang, Changcheng Li, Maosong Sun |
| **Hội nghị** | ACL 2019 |
| **Bài toán** | Fact verification trên FEVER |
| **Kết quả pipeline cuối** | Dev: 74.84% LA, 70.69% FEVER; Test: 71.60% LA, 67.10% FEVER |

Mục tiêu của GEAR là xác minh một claim bằng nhiều câu evidence. Động lực chính của paper là những phương pháp chỉ nối evidence hoặc xử lý từng cặp evidence-claim độc lập không mô hình hóa đầy đủ quan hệ giữa các evidence.

### 2.2. Dataset FEVER

FEVER gồm claim do con người tạo từ Wikipedia và ba nhãn:

- **SUPPORTED:** evidence hỗ trợ claim.
- **REFUTED:** evidence mâu thuẫn với claim.
- **NOT ENOUGH INFO (NEI):** không có đủ evidence để kết luận.

| Đặc điểm | Chi tiết |
|:---|:---|
| **Nguồn dữ liệu** | 5,416,537 tài liệu từ Wikipedia dump tháng 06/2017 |
| **Số claim theo các split ở Table 2** | 185,445 |
| **Train** | 80,035 SUPPORTS; 29,775 REFUTES; 35,639 NEI |
| **Dev/Test** | Mỗi split có 6,666 mẫu cho từng nhãn |

> Lưu ý: phần văn bản ở Section 4.1 của paper ghi 185,455, nhưng các số trong Table 2 cộng lại thành 185,445. Báo cáo sử dụng số theo bảng dữ liệu.

### 2.3. Metrics đánh giá

| Metric | Ý nghĩa |
|:---|:---|
| **Label Accuracy (LA)** | Tỷ lệ claim được dự đoán đúng nhãn, không xét evidence trả về có đầy đủ hay không |
| **FEVER Score** | Với SUPPORTS/REFUTES, dự đoán phải đúng nhãn và cung cấp ít nhất một gold evidence set hoàn chỉnh; claim NEI không cần evidence |
| **Oracle FEVER (OFEVER)** | Upper bound của FEVER score khi giả định hệ thống downstream hoàn hảo; được dùng để đánh giá retrieval/selection |

Vì FEVER Score kiểm tra thêm tính đầy đủ của evidence nên thông thường:

```text
FEVER Score <= Label Accuracy
```

Khoảng cách giữa hai metric phản ánh ảnh hưởng của retrieval và sentence selection, nhưng không nên xem đây là nguyên nhân duy nhất của mọi lỗi dự đoán.

---

## 3. Pipeline của GEAR

Trong paper, từ “pipeline” chỉ **toàn bộ quy trình xử lý từ claim thô đến nhãn cuối**. GEAR không tự tìm evidence trực tiếp từ toàn bộ Wikipedia; nó là module claim verification đứng sau hai module retrieval.

```text
Claim
  -> (1) Document Retrieval
       Output: tập tài liệu Wikipedia ứng viên
  -> (2) Sentence Selection + Threshold Filter
       Output: tối đa 5 evidence sentences
  -> (3) Claim Verification bằng kiến trúc GEAR
       Output: P(SUPPORTS), P(REFUTES), P(NEI)
  -> Nhãn có xác suất cao nhất
```

Ba giai đoạn được xây dựng và huấn luyện như các thành phần riêng. Vì vậy, lỗi ở upstream có thể truyền xuống downstream: nếu document retrieval không lấy được tài liệu cần thiết thì GEAR không thể tự khôi phục evidence đã mất.

### 3.1. Document Retrieval

**Mục tiêu:** từ một claim, tìm một tập nhỏ tài liệu Wikipedia có khả năng chứa evidence.

Paper kế thừa entity-linking approach của Hanselowski et al. (2018):

1. Dùng constituency parser của AllenNLP để lấy các cụm từ có khả năng là entity trong claim.
2. Dùng từng entity làm search query cho MediaWiki API.
3. Giữ bảy kết quả xếp hạng cao nhất của mỗi query để tạo candidate article set.
4. Loại tài liệu không có trong Wikipedia dump ngoại tuyến của FEVER.
5. Tiếp tục lọc bằng mức độ trùng từ giữa title của tài liệu và claim.

```text
Claim
  -> potential entity mentions
  -> MediaWiki search results
  -> title/word-overlap filtering
  -> candidate Wikipedia documents
```

Module này chỉ tìm **tài liệu**, chưa xác định câu nào là evidence. Paper đánh giá nó bằng OFEVER, tức upper bound của FEVER Score nếu các module phía sau hoàn hảo. Document retrieval của nhóm tác giả đạt 93.33% OFEVER trên dev set.

### 3.2. Sentence Selection

**Mục tiêu:** từ tất cả câu trong candidate documents, chọn các câu liên quan nhất tới claim.

Sentence selector dùng biến thể ESIM để tính relevance score giữa một câu ứng viên và claim. Trong quá trình huấn luyện, model dùng negative sampling và hinge loss:

```text
L = Σ max(0, 1 + s_negative - s_positive)
```

Trong đó `s_positive` là score của gold evidence và `s_negative` là score của một câu không phải evidence. Loss buộc evidence đúng có score cao hơn negative evidence ít nhất một margin.

Khi inference, phương pháp kế thừa từ Hanselowski et al. ensemble kết quả của 10 sentence-selection models được khởi tạo bằng các random seed khác nhau. Hệ thống gốc giữ top 5 câu có relevance score cao nhất.

GEAR bổ sung threshold `τ`:

```text
E = {sentence thuộc top 5 và relevance_score >= τ}
```

Vì vậy, tập evidence cuối có kích thước `N <= 5`. Threshold tạo ra trade-off:

- `τ` thấp: recall/OFEVER cao hơn nhưng giữ nhiều câu nhiễu.
- `τ` cao: precision cao hơn nhưng có thể loại mất evidence cần thiết.

Thực nghiệm ở Table 4 cho thấy `τ = 10^-3` đạt label accuracy cao nhất trong nhóm threshold được thử. Threshold quá thấp giữ nhiều noise; threshold quá cao có thể loại mất evidence cần thiết.

### 3.3. Claim Verification

**Input:** claim `c` và tập evidence đã truy xuất `E = {e1, ..., eN}`.

**Output:** một trong ba nhãn SUPPORTS, REFUTES hoặc NEI.

Đây là phần đóng góp chính của paper và là nơi kiến trúc GEAR được sử dụng:

```text
(claim, evidence set)
  -> BERT Sentence Encoder
  -> fully-connected Evidence Graph
  -> T layers of ERNet message passing
  -> Attention / Max / Mean Aggregator
  -> one-layer classifier
  -> label distribution
```

Claim verification không chỉ hỏi “câu evidence nào liên quan?”, mà hỏi “sau khi kết hợp các evidence, chúng hỗ trợ, bác bỏ hay chưa đủ để kết luận claim?”. Đây là khác biệt giữa sentence selection và fact verification.

### 3.4. Dòng dữ liệu và sự lan truyền lỗi

| Giai đoạn | Input | Output | Nếu giai đoạn này sai |
|:---|:---|:---|:---|
| Document Retrieval | Claim | Candidate documents | Tài liệu chứa gold evidence có thể không bao giờ được xem xét |
| Sentence Selection | Claim + các câu ứng viên | Tối đa 5 evidence sentences | Evidence đúng bị loại hoặc evidence nhiễu được giữ lại |
| GEAR Verification | Claim + evidence set | Ba xác suất nhãn | Có thể tổng hợp/reasoning sai dù evidence đã đầy đủ |

Điểm này giải thích vì sao paper báo cáo cả LA, FEVER Score và OFEVER. LA tập trung vào nhãn; FEVER Score còn yêu cầu evidence đầy đủ; OFEVER đo giới hạn do upstream retrieval gây ra.

---

## 4. Kiến trúc GEAR

“Kiến trúc GEAR” là cấu tạo **bên trong giai đoạn Claim Verification**, không bao gồm MediaWiki search hay ESIM sentence selector. Kiến trúc nhận một evidence set đã được pipeline chuẩn bị và biến nó thành dự đoán nhãn.

### 4.1. Sentence Encoder

Với claim `c` và tập evidence `{e1, e2, ..., eN}`, paper dùng BERTBASE để mã hóa:

```text
e_i = BERT(evidence_i, claim)
c   = BERT(claim)
```

Về mặt input BERT, mỗi evidence được ghép cặp với claim theo dạng khái quát:

```text
[CLS] evidence_i [SEP] claim [SEP]
```

Final hidden state của token `[CLS]` được dùng làm evidence representation. Với BERTBASE:

```text
e_i ∈ R^768
c   ∈ R^768
```

Mỗi cặp evidence-claim được mã hóa trong một BERT forward riêng. Vì vậy, evidence thứ nhất không nhìn thấy evidence thứ hai ở bước encoder; việc trao đổi thông tin chỉ xảy ra sau đó trong ERNet.

Paper encode claim riêng vì claim representation `c` được dùng để điều khiển attention ở tầng aggregator. Đồng thời, claim cũng xuất hiện trong mỗi BERT pair để evidence representation đã mang thông tin về mức độ liên quan và quan hệ ngữ nghĩa với claim.

Một chi tiết quan trọng trong thiết lập huấn luyện:

- BERT-Pair được fine-tune trên FEVER trước.
- GEAR dùng BERT-Pair đã fine-tune để trích xuất feature.
- Paper cho biết BERT chưa fine-tune khiến accuracy gần random guess. Do đó, fine-tuning theo nhiệm vụ là yếu tố thiết yếu, không thể thay thế bằng embedding BERT tổng quát một cách trực tiếp.

Nói cách khác, protocol của paper gồm hai bước: học representation evidence-claim bằng BERT-Pair trước, sau đó dùng các representation đó để huấn luyện ERNet và aggregator.

### 4.2. Evidence Reasoning Network (ERNet)

Sau khi encode, GEAR xây một đồ thị riêng cho mỗi claim:

- Mỗi node tương ứng với một evidence sentence.
- Mọi node kết nối với mọi node khác.
- Mỗi node có self-loop để giữ và tái sử dụng thông tin của chính nó.
- Nếu có `N` evidence thì attention được tính trên ma trận quan hệ `N x N`.

Trạng thái ban đầu của node `i`:

```text
h_i^0 = e_i
```

Tại ERNet layer `t`, GEAR thực hiện ba thao tác.

**Bước 1 - Tính compatibility giữa hai evidence:**

```text
p_ij = W1^(t-1)(ReLU(W0^(t-1)(h_i^(t-1) || h_j^(t-1))))
```

Hai node được concatenate, chiếu qua một MLP và tạo scalar `p_ij`. Với thiết lập của paper, feature size `F = 768` và hidden size của MLP `H = 64`.

**Bước 2 - Chuẩn hóa attention trên các neighbor của node `i`:**

```text
α_ij = exp(p_ij) / Σ_k exp(p_ik)
```

Với mỗi node `i`, tổng các trọng số gửi tới những node `j` bằng 1.

**Bước 3 - Cập nhật node bằng weighted sum:**

```text
h_i^t = Σ_j α_ij h_j^(t-1)
```

Sau một layer, mỗi node không còn chỉ biểu diễn câu evidence ban đầu mà chứa tổng hợp có trọng số từ toàn bộ evidence set. Khi xếp chồng nhiều layer, thông tin tiếp tục được truyền và tái tổng hợp.

Ví dụ:

```text
e1: Rodney King riots occurred in Los Angeles County
e2: Los Angeles County is the most populous county in the USA

ERNet cho phép node e1 nhận thông tin “most populous county” từ e2,
giúp hình thành representation phục vụ xác minh claim nhiều bước.
```

Nếu `T = 0`, ERNet bị bỏ qua và aggregator nhận trực tiếp các BERT representations. Paper thử `T` từ 0 đến 3. ERNet cho phép evidence trao đổi thông tin trước khi pooling; đây là điểm phân biệt quan trọng giữa GEAR và một mô hình chỉ encode độc lập rồi tổng hợp.

### 4.3. Evidence Aggregator

Sau `T` ERNet layers, model có tập node states `{h1^T, ..., hN^T}` nhưng classifier cần một vector kích thước cố định. Aggregator thực hiện phép biến đổi:

```text
{h1^T, ..., hN^T} -> o ∈ R^768
```

Paper thử ba chiến lược:

- **Attention:** học trọng số evidence dựa trên claim.
- **Max:** lấy giá trị lớn nhất ở từng chiều feature.
- **Mean:** lấy trung bình ở từng chiều feature.

Attention aggregator:

```text
p_j = W1'(ReLU(W0'(c || h_j^T)))
α_j = exp(p_j) / Σ_k exp(p_k)
o   = Σ_j α_j h_j^T
```

Khác với attention trong ERNet:

- **ERNet attention `α_ij`:** node evidence `i` nên nhận bao nhiêu thông tin từ node `j`.
- **Aggregator attention `α_j`:** evidence node `j` nên đóng góp bao nhiêu vào representation cuối của claim.

Max và Mean không sử dụng claim representation trực tiếp ở bước pooling, dù mỗi node đã chứa thông tin claim từ BERT pair.

### 4.4. Classifier và hàm loss

Vector tổng hợp `o` được đưa qua one-layer classifier. Paper viết:

```text
l = softmax(ReLU(Wo + b))
```

Trong đó:

- `W ∈ R^(3 x 768)` vì FEVER có ba nhãn.
- `b ∈ R^3`.
- `l` là phân phối dự đoán trên SUPPORTS, REFUTES và NEI.

ERNet được huấn luyện bằng negative log-likelihood loss với Adam. Thiết lập được paper nêu gồm learning rate `5 x 10^-3`, L2 weight decay `5 x 10^-4` và early stopping theo dev label accuracy với patience 20.

### 4.5. Pipeline GEAR và kiến trúc GEAR khác nhau thế nào?

| Khái niệm | Phạm vi | Thành phần | Câu hỏi nó giải quyết |
|:---|:---|:---|:---|
| **Pipeline của paper** | Toàn bộ hệ thống end-to-end | Document Retrieval + Sentence Selection + GEAR Claim Verification | “Từ claim và Wikipedia, tìm evidence rồi dự đoán nhãn thế nào?” |
| **Kiến trúc GEAR** | Chỉ module claim verification | BERT Encoder + ERNet + Aggregator + Classifier | “Khi đã có evidence, kết hợp và reasoning trên chúng thế nào?” |

Có thể hình dung pipeline là cả dây chuyền nhà máy, còn kiến trúc GEAR là cỗ máy suy luận ở công đoạn cuối:

```text
PIPELINE
├── Retrieval: tìm đúng tài liệu
├── Selection: tìm đúng câu
└── GEAR ARCHITECTURE
    ├── Encode từng evidence
    ├── Cho evidence trao đổi thông tin
    ├── Tổng hợp evidence
    └── Phân loại claim
```

Do đó, một kết quả “GEAR pipeline” như FEVER Score 67.10% chịu ảnh hưởng của cả retrieval lẫn kiến trúc GEAR. Còn các thí nghiệm thay số ERNet layers trên difficult subset chủ yếu phân tích năng lực của kiến trúc claim verification.

### 4.6. BERT-Concat, BERT-Pair và ERNet giữ vai trò gì?

Các thuật ngữ trong paper không nằm ở cùng một cấp độ. Có cái là mô hình hoàn chỉnh, có cái chỉ là một tầng bên trong mô hình, và có cái chỉ được dùng khi huấn luyện hoặc đánh giá.

| Tên | Thực chất là gì? | Có tham số được học? | Đóng góp trong train/test |
|:---|:---|:---:|:---|
| **BERTBASE** | Pre-trained language model/backbone | Có | Được fine-tune để tạo representation cho claim và evidence |
| **BERT-Concat** | Một baseline model hoàn chỉnh | Có | Nối evidence rồi huấn luyện dự đoán nhãn; được đo LA/FEVER riêng trong Table 7 |
| **BERT-Pair** | Một baseline model hoàn chỉnh; đồng thời là feature encoder cho GEAR | Có | Học trên từng evidence-claim pair; checkpoint đã fine-tune được dùng để trích xuất feature cho GEAR |
| **ERNet** | Neural-network module bên trong GEAR | Có | Học attention/message passing giữa evidence; được kiểm tra qua ablation 0-3 layers |
| **Attention Aggregator** | Module pooling bên trong GEAR | Có | Học evidence nào nên đóng góp nhiều vào vector cuối |
| **Max/Mean Aggregator** | Phép pooling thay thế attention | Không có tham số pooling | Dùng làm ablation để kiểm tra ảnh hưởng của cách tổng hợp |
| **Classifier** | Tầng dự đoán cuối bên trong mỗi model | Có | Chuyển representation thành xác suất ba nhãn |
| **GEAR** | Claim-verification model do paper đề xuất | Có | Kết hợp BERT-Pair features, ERNet, aggregator và classifier |
| **ESIM Sentence Selector** | Upstream retrieval model riêng | Có | Học relevance score để chọn tối đa 5 evidence trước khi chạy GEAR |
| **Adam** | Thuật toán optimizer | Không | Chỉ dùng trong train để cập nhật tham số theo gradient |
| **Negative log-likelihood** | Hàm loss/objective | Không | Cho biết dự đoán sai bao nhiêu để optimizer cập nhật model |
| **Random seed** | Thiết lập ngẫu nhiên của một lần chạy | Không | Dùng để kiểm tra kết quả có ổn định qua nhiều lần train hay không |
| **LA/FEVER/OFEVER** | Metrics đánh giá | Không | Chỉ đo kết quả; không phải model và không trực tiếp học tham số |

#### Thành phần nào thực sự được cập nhật khi train?

```text
Giai đoạn A - Train Sentence Selector
  Cập nhật: tham số ESIM sentence selector
  Chưa train: BERT-Concat, BERT-Pair, ERNet

Giai đoạn B - Fine-tune BERT baselines
  BERT-Concat: cập nhật BERT + classification head của BERT-Concat
  BERT-Pair:   cập nhật BERT + classification head của BERT-Pair

Giai đoạn C - Train GEAR reasoning layers
  Input: features do BERT-Pair đã fine-tune trích xuất
  Cập nhật: ERNet + Attention Aggregator (nếu dùng) + Classifier
```

Trong protocol được paper mô tả, BERT-Pair đã fine-tune được dùng để **extract features** cho GEAR. Paper không trình bày đây là một lần huấn luyện end-to-end trong đó BERT, ERNet và retrieval cùng được cập nhật đồng thời.

#### Thành phần nào chạy khi inference?

```text
Claim
  -> Document Retrieval
  -> ESIM Sentence Selector
  -> BERT-Pair feature encoder
  -> ERNet
  -> Aggregator
  -> Classifier
  -> Nhãn dự đoán
```

BERT-Concat không nằm bên trong GEAR; nó là đường chạy baseline riêng để so sánh. BERT-Pair vừa có một đường chạy baseline riêng, vừa cung cấp encoder đã fine-tune cho đường chạy GEAR.

Do đó, BERT-Concat và BERT-Pair có accuracy riêng trong bảng full pipeline. ERNet không có một “accuracy độc lập”; paper thay số ERNet layers và loại aggregator rồi đo accuracy của **toàn bộ GEAR configuration** tương ứng.

---

## 5. Kết quả thực nghiệm

### 5.1. Paper đã huấn luyện và chạy mô hình như thế nào?

Quy trình thực nghiệm có thể tóm tắt thành ba bước:

```text
Bước 1: Huấn luyện document retrieval và sentence selection
  -> tạo tối đa 5 retrieved evidence cho mỗi claim

Bước 2: Fine-tune các BERT baselines trên FEVER
  -> BERT-Concat để làm baseline concat
  -> BERT-Pair để làm baseline và tạo evidence-claim features

Bước 3: Dùng features từ BERT-Pair đã fine-tune
  -> huấn luyện ERNet + Aggregator + Classifier
  -> thử 0-3 ERNet layers và Attention/Max/Mean
```

Các hyperparameter chính:

| Thành phần | Thiết lập trong paper |
|:---|:---|
| **BERT dùng chung** | BERTBASE, fine-tuning learning rate `2 x 10^-5` |
| **BERT-Concat** | Max sequence length 256; evidence tối đa 240 token; claim tối đa 16 token; batch 16; 2 epochs |
| **BERT-Pair** | Max sequence length 128; batch 32; 1 epoch |
| **GEAR feature extraction** | Dùng BERT-Pair đã fine-tune; batch 512 |
| **ERNet** | Feature size `F=768`; attention-MLP hidden size `H=64`; batch 256 |
| **ERNet optimizer** | Adam; learning rate `5 x 10^-3`; L2 weight decay `5 x 10^-4` |
| **Early stopping** | Theo dev label accuracy; patience 20 epochs |
| **Số ERNet layers thử nghiệm** | 0, 1, 2 và 3 |

#### Cách huấn luyện BERT-Concat

- Khi train, paper thêm gold evidence vào retrieved evidence set với relevance score bằng 1 rồi lấy năm evidence có score cao nhất.
- Các evidence này được nối thành một chuỗi và đưa vào BERT cùng claim.
- Khi test, model chỉ được dùng retrieved evidence, không được cung cấp gold evidence.

#### Cách huấn luyện BERT-Pair

- Với SUPPORTS/REFUTES khi train, model dùng từng gold evidence-claim pair và nhãn của claim làm target.
- Với NEI, do không có gold evidence, model dùng retrieved evidence-claim pairs.
- Khi test, BERT-Pair dự đoán cho mọi retrieved evidence-claim pair.
- Vì các cặp có thể dự đoán khác nhau, paper dùng aggregator lấy nhãn dự đoán từ evidence có relevance cao nhất; đây là cách hoạt động tốt nhất trong các cách tác giả thử.

Hai baseline vì vậy không chỉ khác cách đóng gói input mà còn khác cách tạo training examples và tổng hợp dự đoán.

#### “Chạy 10 random seeds” có nghĩa là gì?

Với các thí nghiệm GEAR trên dev set, paper chạy cùng cấu hình **10 lần**, mỗi lần dùng random seed khác nhau, rồi báo cáo giá trị trung bình của LA/FEVER Score:

```text
mean_metric = (run_1 + run_2 + ... + run_10) / 10
```

Đây không phải 10-fold cross-validation: train/dev split không đổi. Seed khác nhau có thể làm thay đổi khởi tạo tham số, thứ tự mini-batch và các phép toán ngẫu nhiên trong huấn luyện, từ đó tạo ra kết quả hơi khác nhau. Lấy trung bình giúp giảm nguy cơ kết luận dựa trên một lần chạy may mắn hoặc không may. Paper không báo cáo độ lệch chuẩn, nên ta biết mean nhưng chưa biết đầy đủ mức dao động giữa 10 runs.

Các kết quả test của pipeline cuối được gửi với cấu hình được chọn theo dev FEVER Score. Không nên hiểu rằng mọi số của các baseline trong Table 7 đều mặc nhiên là trung bình 10 seeds; phát biểu 10-run mean của paper áp dụng rõ ràng cho các kết quả GEAR báo cáo trên dev set.

### 5.2. Kết quả document retrieval và sentence selection

**Document Retrieval - OFEVER trên dev set:**

| Hệ thống | OFEVER |
|:---|---:|
| Athene | 93.55 |
| UNC NLP | 92.82 |
| **Hệ thống của paper** | **93.33** |

OFEVER 93.33% có nghĩa: ngay cả khi các module downstream hoàn hảo, document retrieval hiện tại vẫn tạo ra một giới hạn do một số gold documents không được tìm thấy.

**Sentence Selection - ảnh hưởng của threshold trên dev set:**

| Threshold `τ` | OFEVER | Precision | Recall | F1 | GEAR LA |
|---:|---:|---:|---:|---:|---:|
| 0 | 91.10 | 24.08 | **86.72** | 37.69 | 74.84 |
| `10^-4` | 91.04 | 30.88 | 86.63 | 45.53 | 74.86 |
| `10^-3` | 90.86 | 40.60 | 86.36 | 55.23 | **74.91** |
| `10^-2` | 90.27 | 53.12 | 85.47 | 65.52 | 74.89 |
| `10^-1` | 87.70 | **70.61** | 81.64 | **75.72** | 74.81 |

Khi `τ` tăng, precision/F1 tăng vì nhiều evidence nhiễu bị loại, nhưng recall/OFEVER giảm vì một phần evidence đúng cũng bị mất. `τ=10^-3` cho GEAR LA cao nhất trong riêng Table 4. Tuy nhiên, pipeline cuối ở Table 7 được chọn theo dev FEVER Score trong toàn bộ thí nghiệm nên dev LA được báo cáo là 74.84, không phải 74.91.

### 5.3. Kết quả full pipeline

| Model | Dev LA | Dev FEVER | Test LA | Test FEVER |
|:---|---:|---:|---:|---:|
| Athene | 68.49 | 64.74 | 65.46 | 61.58 |
| UCL MRG | 69.66 | 65.41 | 67.62 | 62.52 |
| UNC NLP | 69.72 | 66.49 | 68.21 | 64.21 |
| BERT-Pair | 73.30 | 68.90 | 69.75 | 65.18 |
| BERT-Concat | 73.67 | 68.89 | 71.01 | 65.64 |
| **GEAR pipeline** | **74.84** | **70.69** | **71.60** | **67.10** |

So với BERT-Concat:

- Dev LA tăng 1.17 điểm phần trăm.
- Test LA tăng 0.59 điểm phần trăm.
- Test FEVER tăng 1.46 điểm phần trăm.

Đây là bằng chứng rằng **toàn bộ pipeline GEAR** hiệu quả hơn BERT-Concat trong thiết lập của paper. Các kết quả này không tách riêng mức đóng góp của independent encoding, ERNet và attention aggregator.

### 5.4. Difficult dev subset

Paper tạo một tập khó gồm 7,870 mẫu, chiếm hơn 39% dev set:

- Với SUPPORTS/REFUTES, loại claim có thể được xác minh đầy đủ bằng một evidence duy nhất.
- Giữ toàn bộ claim NEI vì mô hình phải xem tập evidence được truy xuất trước khi kết luận thiếu thông tin.

| ERNet layers | Attention | Max | Mean |
|---:|---:|---:|---:|
| 0 | 66.17 | 65.36 | 65.03 |
| 1 | 67.13 | 66.63 | 66.76 |
| 2 | 67.44 | 67.24 | **67.56** |
| 3 | 66.53 | 66.72 | 66.89 |

Với attention, hai ERNet layers tăng 1.27 điểm so với zero layer trên tập khó. Kết quả này hỗ trợ vai trò của reasoning giữa nhiều evidence, nhưng chỉ áp dụng trực tiếp cho difficult subset. Paper không kết luận việc giảm ở ba layers là do over-smoothing.

### 5.5. Evidence-enhanced dev set

Paper bổ sung gold evidence vào evidence được truy xuất để ước lượng upper bound khi upstream retrieval tốt hơn:

| ERNet layers | Attention | Max | Mean |
|---:|---:|---:|---:|
| 0 | 77.12 | 76.95 | 76.30 |
| 1 | 77.74 | 77.66 | 77.62 |
| 2 | **77.82** | **77.66** | **77.73** |
| 3 | 77.70 | 77.55 | 77.60 |

Các kết quả tăng hơn 1.4 điểm so với full dev cho thấy retrieval và sentence selection vẫn là điểm nghẽn đáng kể.

### 5.6. Mô hình cuối cùng

Một điểm dễ nhầm giữa Table 5 và Table 7:

- Hai ERNet layers hoạt động tốt nhất trên difficult subset.
- **Pipeline cuối báo cáo ở Table 7 dùng một ERNet layer, attention aggregator và threshold `10^-3`.**
- Tác giả chọn mô hình cuối theo dev FEVER score, không phải chỉ theo label accuracy.

### 5.7. Case study

Trong ví dụ “Al Jardine is an American rhythm guitarist”, hai evidence đầu cung cấp lần lượt thông tin “rhythm guitarist” và “American musician”. Attention map cho thấy các node tập trung vào hai evidence hữu ích này.

Case study chứng minh mô hình có thể học trọng số phù hợp trong một ví dụ. Tuy nhiên, attention weight chỉ nên được xem là tín hiệu để phân tích mô hình, không mặc nhiên là lời giải thích nhân quả hoặc faithful explanation.

---

## 6. Kết luận đúng phạm vi từ paper

Có thể rút ra các kết luận sau:

1. Toàn bộ GEAR pipeline vượt BERT-Concat và BERT-Pair trên FEVER.
2. GEAR có lợi trên tập claim cần nhiều evidence.
3. Fine-tuning BERT-Pair theo FEVER là thành phần quan trọng.
4. ERNet cải thiện kết quả trên difficult subset so với zero-layer variants.
5. Chất lượng retrieval giới hạn đáng kể kết quả cuối.
6. Mô hình cuối không phải cấu hình hai layers có accuracy cao nhất trong mọi bảng; nó được chọn theo dev FEVER score.

Không nên diễn giải paper thành các khẳng định sau:

- “Khoảng 90% hiệu quả đến từ encode riêng và attention.”
- “ERNet chỉ đóng góp 1.27% trên toàn bộ bài toán.”
- “Bỏ ERNet gần như không làm giảm hiệu quả.”
- “Paper chứng minh riêng attention pooling tốt hơn concat.”
- “Attention weight luôn là lời giải thích đáng tin cậy.”

Paper không cung cấp ablation đầy đủ để chứng minh các mệnh đề trên.

### 6.1. Hướng tương lai do chính tác giả đề xuất

Paper kết thúc với hai hướng:

1. **Multi-step evidence extraction:** cải thiện retrieval để tìm evidence qua nhiều bước, thay vì chỉ phụ thuộc entity xuất hiện trực tiếp trong claim. Đây là phản ứng trực tiếp với lỗi upstream không tìm được tài liệu thứ hai cần cho reasoning.
2. **External knowledge:** bổ sung tri thức bên ngoài vào GEAR để hỗ trợ các trường hợp mà evidence văn bản hiện có chưa đủ.

Hai hướng này liên quan chặt với FactKG: knowledge graph có thể hỗ trợ multi-step retrieval và cung cấp external relational knowledge. Tuy nhiên, đây là future work của paper, chưa được kiểm chứng trong các bảng kết quả GEAR.

---

## 7. Liên hệ với FactKG

### 7.1. Điểm tương đồng và khác biệt

| Yếu tố | GEAR/FEVER | FactKG |
|:---|:---|:---|
| **Input evidence** | Câu văn từ Wikipedia | Path được sinh từ knowledge graph |
| **Output** | SUPPORTS/REFUTES/NEI | True/False |
| **Số evidence trong GEAR** | Tối đa 5 sau sentence selection | Có thể lớn hơn, phụ thuộc retrieval/path generation |
| **Quan hệ giữa evidence** | Quan hệ ngữ nghĩa giữa các câu | Quan hệ cấu trúc và logic giữa các KG path |
| **Thách thức chung** | Lọc noise và kết hợp nhiều evidence | Lọc path rác và kết hợp nhiều path |

GEAR là nguồn cảm hứng phù hợp cho FactKG, nhưng kết quả FEVER không thể chuyển trực tiếp thành mức tăng accuracy dự kiến trên FactKG.

### 7.2. Baseline hiện tại của FactKG

Trong `with_evidence/classifier/baseline.py`, các path được flatten, nối bằng separator, tokenize với truncation, rồi ghép claim và evidence trước khi đưa vào BERT. Vì vậy, kiến trúc có tính chất tương tự BERT-Concat.

Tuy nhiên, không nên gọi hai hệ thống “giống hệt nhau” vì:

- GEAR BERT-Concat chỉ nhận tối đa 5 evidence sentences.
- GEAR đặt maximum sequence length là 256 cho baseline này.
- FactKG sử dụng KG paths, quy trình retrieval và giới hạn input khác.

Các rủi ro hợp lý cần kiểm chứng trên FactKG gồm:

1. **Truncation:** path ở cuối chuỗi có thể bị cắt khi tổng input vượt giới hạn.
2. **Noise dilution:** path không liên quan có thể làm giảm tín hiệu của path quan trọng.
3. **Thiếu path-level discrimination:** classifier không tạo một trọng số tường minh cho từng path.

Trước khi kết luận đây là nguyên nhân của lỗi multi-hop, cần đo trực tiếp tỷ lệ mẫu bị truncate, số path mỗi mẫu và vị trí của gold/relevant path.

### 7.3. Baseline nội bộ cần tái xác nhận

Các kết quả đã được ghi nhận trong báo cáo cũ:

| Loại suy luận | Accuracy |
|:---|---:|
| Existence | 89.08% |
| Conjunction | 85.08% |
| Negation | 84.35% |
| One-hop | 84.22% |
| Multi-hop | 68.84% |
| **Tổng thể** | **81.80%** |

Đây là kết quả nội bộ, không thuộc paper GEAR. Trước khi dùng làm baseline chính thức, cần lưu kèm checkpoint, data split, seed, cấu hình retrieval và command chạy để bảo đảm khả năng tái lập.

---

## 8. Đề xuất GEAR-lite cho FactKG

### 8.1. Định nghĩa

Trong kế hoạch này, **GEAR-lite** là tên nội bộ cho kiến trúc:

```text
Claim + từng KG path
  -> Shared BERT path encoder
  -> Path representations
  -> Claim-guided attention pooling
  -> Binary classifier
  -> True / False
```

GEAR-lite bỏ ERNet nên không còn khả năng message passing trực tiếp giữa các path. Vì vậy, đây là một ablation lấy cảm hứng từ GEAR, không phải bản triển khai đầy đủ của GEAR.

### 8.2. Kiến trúc đề xuất

Với claim `c` và các path `{p1, ..., pN}`:

```text
h_i = BERT(path_i, claim)
c   = BERT(claim)

s_i = W1(ReLU(W0(c || h_i)))
α_i = softmax(s_i)
o   = Σ_i α_i h_i

ŷ = Classifier(o)
```

Cần áp dụng mask trước softmax để padding path không nhận attention weight.

Mỗi cặp vẫn phải có `max_length` và `truncation=True`; independent encoding loại bỏ việc các path cạnh tranh trong một chuỗi chung nhưng không đảm bảo tuyệt đối rằng một path đơn lẻ không bao giờ bị cắt.

### 8.3. Giả thuyết nghiên cứu

GEAR-lite được thiết kế để kiểm tra ba giả thuyết:

- **H1:** Independent path encoding giảm mất evidence do concat-level truncation.
- **H2:** Claim-guided attention giảm ảnh hưởng của path không liên quan.
- **H3:** Lợi ích rõ nhất xuất hiện ở nhóm multi-hop có nhiều candidate paths.

Các giả thuyết này chỉ được chấp nhận sau khi so sánh trên cùng data split và retrieval output.

### 8.4. Giới hạn dự kiến

- Chi phí BERT tăng gần tuyến tính theo số path.
- Soft attention không thực sự loại path; path nhiễu vẫn đóng góp một phần.
- Không có ERNet nên mô hình có thể yếu khi kết luận đòi hỏi kết hợp logic giữa nhiều path.
- Attention weight không bảo đảm là faithful explanation.
- Nếu path encoder không được fine-tune phù hợp, pooling phía sau khó bù được representation yếu.

---

## 9. Kế hoạch thực nghiệm

### Giai đoạn 0: Chuẩn hóa baseline

- Cố định train/dev/test split và random seeds.
- Lưu command, config, checkpoint và retrieval artifacts.
- Đo accuracy tổng thể và theo reasoning type.
- Ghi nhận số path, số token và tỷ lệ truncate theo từng reasoning type.

### Giai đoạn 1: Implement GEAR-lite

- Giữ từng path riêng trong Dataset.
- DataCollator tạo tensor `[batch, num_paths, seq_len]` và `path_mask`.
- Dùng một shared BERT cho tất cả path.
- Thêm claim-guided attention aggregator và binary classifier.
- Hỗ trợ giới hạn `max_paths` và batching/chunking để tránh hết GPU memory.

### Giai đoạn 2: Ablation study

So sánh tối thiểu:

| Mô hình | Mục đích |
|:---|:---|
| ConcatClassifier | Baseline hiện tại |
| Independent + Mean | Tách ảnh hưởng của independent encoding |
| Independent + Max | Kiểm tra pooling không tham số |
| Independent + Attention | GEAR-lite đề xuất |
| Independent + Attention + ERNet | Kiểm tra giá trị thực của graph reasoning nếu tài nguyên cho phép |

Không thể quy cải thiện cho attention nếu chỉ so GEAR-lite với concat; cần Mean/Max ablation để tách ảnh hưởng của encoder và aggregator.

### Giai đoạn 3: Phân tích lỗi

- Accuracy theo số path và độ dài input.
- Accuracy riêng trên mẫu concat baseline bị truncate.
- Accuracy theo one-hop/multi-hop/conjunction/negation/existence.
- Kiểm tra attention trên cả mẫu đúng và mẫu sai.
- Thử loại top-attended path để xem dự đoán có thực sự phụ thuộc vào nó hay không.
- Đo latency, peak GPU memory và throughput.

### Tiêu chí đánh giá

GEAR-lite được xem là có giá trị khi:

1. Cải thiện ổn định qua nhiều seed trên cùng retrieval output.
2. Cải thiện multi-hop mà không làm giảm đáng kể các nhóm còn lại.
3. Mức tăng không chỉ đến từ số lần BERT xử lý nhiều token hơn.
4. Chi phí tính toán vẫn phù hợp với tài nguyên dự án.

Mốc 72% multi-hop hoặc 83% tổng thể có thể dùng làm mục tiêu kỹ thuật nội bộ, nhưng không nên trình bày là mức tăng được paper GEAR bảo đảm.

---

## 10. Kết luận

GEAR chứng minh rằng một pipeline dùng BERT đã fine-tune, graph reasoning và evidence aggregation có thể tận dụng multi-evidence tốt hơn các baseline trên FEVER. Paper cũng cho thấy retrieval vẫn là điểm nghẽn quan trọng và ERNet mang lại lợi ích trên tập claim khó cần nhiều evidence. Vì vậy, tác giả đề xuất tiếp tục phát triển multi-step evidence extraction và tích hợp external knowledge.

Đối với FactKG, independent path encoding kết hợp claim-guided attention là một hướng thử nghiệm hợp lý nhằm giảm concat-level truncation và noise dilution. Tuy nhiên, GEAR-lite đã bỏ thành phần graph reasoning trung tâm của GEAR, nên hiệu quả của nó phải được xác nhận bằng ablation trên FactKG thay vì suy ra trực tiếp từ kết quả FEVER.
