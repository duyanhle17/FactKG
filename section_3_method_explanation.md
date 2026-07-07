# Giải thích đầy đủ Section 3 - Method của GEAR

File này bám theo phần **3. Method** trong `9_6.md`.

Mục tiêu:

- Giải thích full pipeline trong Section 3.
- Nói rõ từng bước có mục đích gì.
- Đi sâu vào phần **GEAR** trong pipeline: Sentence Encoder, ERNet, Evidence Aggregator, Classifier.
- Chú thích các công thức: đại lượng đó đo gì, dùng để làm gì.
- Làm rõ chuyện **encode bằng BERT** là gì, BERT có phải LLM không.

Lưu ý trước: các công thức trong Method **không trực tiếp tính metric** như Label Accuracy hay FEVER Score. Chúng tạo representation và prediction. Sau đó evaluation mới dùng metric để đo prediction đó tốt hay không.

---

## 1. Full pipeline trong Section 3

Trong `9_6.md`, paper sử dụng pipeline:

```text
Claim
  -> Document Retrieval
  -> Sentence Selection + Evidence Filter
  -> Claim Verification bằng GEAR
  -> SUPPORTS / REFUTES / NEI
```

Nói đơn giản:

| Bước | Input | Output | Mục đích |
|:---|:---|:---|:---|
| **Document Retrieval** | Claim | Candidate Wikipedia documents | Tìm các trang Wikipedia có khả năng chứa evidence |
| **Sentence Selection** | Claim + candidate documents | Candidate evidence sentences | Tìm các câu liên quan nhất trong các trang đó |
| **Evidence Filter** | Top evidence sentences | Evidence set `E` | Loại bớt câu có relevance thấp |
| **Claim Verification bằng GEAR** | Claim + evidence set | SUPPORTS / REFUTES / NEI | Dùng evidence để xác minh claim |

Ví dụ claim:

```text
The Rodney King riots took place in the most populous county in the USA.
```

Pipeline cần làm:

```text
1. Tìm trang liên quan đến Rodney King riots, Los Angeles County, ...
2. Chọn các câu evidence trong những trang đó.
3. Dùng GEAR để kết hợp evidence và dự đoán nhãn.
```

---

## 2. Document Retrieval

### 2.1. Bước này làm gì?

Document Retrieval là bước tìm các trang Wikipedia liên quan đến claim.

Ở bước này, hệ thống chưa tìm câu evidence cụ thể. Nó chỉ tìm **candidate documents**.

Ví dụ:

```text
Claim:
The Rodney King riots took place in the most populous county in the USA.
```

Các trang có thể cần tìm:

```text
Rodney King riots
Los Angeles County
List of United States counties by population
```

### 2.2. Paper làm như thế nào?

Theo `9_6.md`, GEAR kế thừa entity-linking approach của Hanselowski et al.:

1. Dùng constituency parser của AllenNLP để trích xuất potential entities từ claim.
2. Dùng các entity làm query cho MediaWiki API.
3. Giữ bảy kết quả xếp hạng cao nhất cho mỗi query.
4. Loại tài liệu không thuộc Wikipedia dump của FEVER.
5. Lọc tiếp theo word overlap giữa title và claim.

### 2.3. Mục đích thực tế

Mục đích của Document Retrieval:

```text
Thu hẹp không gian tìm kiếm từ toàn bộ Wikipedia
về một tập nhỏ các trang có khả năng chứa evidence.
```

Nếu retrieval sai, GEAR phía sau rất khó sửa. Vì nếu trang chứa evidence đúng không được lấy về, claim verification không có đủ thông tin để kết luận.

Nói dễ nhớ:

```text
Document Retrieval = tìm đúng trang cần đọc.
```

---

## 3. Sentence Selection

### 3.1. Bước này làm gì?

Sau khi có candidate documents, hệ thống cần tìm các câu có khả năng làm evidence.

Một trang Wikipedia có nhiều câu, nhưng chỉ vài câu thật sự liên quan đến claim.

Ví dụ:

```text
Evidence 1:
The Rodney King riots occurred in Los Angeles County.

Evidence 2:
Los Angeles County is the most populous county in the United States.
```

Hai câu này cùng nhau có thể support claim.

### 3.2. ESIM-based model ở đây dùng để làm gì?

Theo `9_6.md`:

```text
Từ các câu trong candidate documents,
một ESIM-based model tính relevance score với claim.
```

Tức là với mỗi câu candidate:

```text
sentence_i + claim -> relevance score
```

`relevance score` đo:

```text
Câu này có liên quan đến claim đến mức nào?
```

Điểm này không phải nhãn SUPPORTS / REFUTES / NEI. Nó chỉ phục vụ việc chọn evidence.

Ví dụ:

```text
Claim:
The Rodney King riots took place in the most populous county in the USA.

Sentence A:
The Rodney King riots occurred in Los Angeles County.

Sentence B:
The album was released in 1994.
```

Sentence A nên có relevance score cao hơn Sentence B.

### 3.3. Training của sentence selector

Khi train, sentence selector dùng negative sampling và hinge loss:

```text
L = Σ max(0, 1 + s_negative - s_positive)
```

Ý nghĩa:

- `s_positive`: relevance score của câu evidence đúng.
- `s_negative`: relevance score của câu không phải evidence đúng.
- Loss này ép model học sao cho:

```text
s_positive > s_negative
```

Không chỉ lớn hơn một chút, mà lớn hơn với margin khoảng 1.

Nói dễ hiểu:

```text
Câu evidence đúng phải được chấm điểm cao hơn câu nhiễu.
```

### 3.4. Khi test thì chọn evidence như thế nào?

Theo `9_6.md`, khi test:

- Hệ thống ensemble kết quả của 10 sentence-selection models có random seed khác nhau.
- Phương pháp gốc giữ top 5 câu có relevance score cao nhất.

GEAR bổ sung evidence filter với threshold `τ`:

```text
E = {sentence thuộc top 5 và relevance_score >= τ}
```

Ý nghĩa:

- Chỉ giữ các câu nằm trong top 5.
- Đồng thời câu đó phải có relevance score đủ cao.

Mục đích:

```text
Giảm evidence nhiễu đưa vào claim verification.
```

Sau bước này, ta có evidence set:

```text
E = {e1, e2, ..., eN}
```

Với `N` không vượt quá 5.

---

## 4. Claim Verification bằng GEAR

Đây là đóng góp chính trong Method.

GEAR nhận:

```text
Claim c
Evidence set E = {e1, e2, ..., eN}
```

GEAR cần dự đoán:

```text
SUPPORTS
REFUTES
NEI
```

Kiến trúc:

```text
Evidence-claim pairs
  -> BERT Sentence Encoder
  -> Fully-connected Evidence Graph
  -> ERNet
  -> Evidence Aggregator
  -> Classifier
  -> Label
```

Các phần tiếp theo giải thích kỹ từng khối.

---

## 5. Encode là gì? BERT có phải LLM không?

### 5.1. Encode có phải là encode vector không?

Đúng. Trong ngữ cảnh này, **encode** nghĩa là biến text thành vector.

Ví dụ câu:

```text
The film was released in 1997.
```

Sau khi encode bằng BERT, câu này được biến thành các vector số, ví dụ khái niệm:

```text
[0.12, -0.08, 0.44, ..., 0.31]
```

Trong GEAR, vector quan trọng là vector `[CLS]`:

```text
e_i ∈ R^768
```

Nghĩa là mỗi evidence-claim pair được biểu diễn bằng một vector 768 chiều.

### 5.2. BERT encode text như thế nào?

BERT không đọc text theo kiểu con người. Nó xử lý qua các bước khái quát:

```text
Text
  -> Tokenization
  -> Token IDs
  -> Embedding vectors
  -> Transformer encoder layers
  -> Contextual vectors
```

Ví dụ input:

```text
[CLS] evidence_i [SEP] claim [SEP]
```

BERT tạo vector cho từng token. Vector cuối của `[CLS]` thường được dùng như representation cho toàn bộ input pair.

Trong GEAR:

```text
Final hidden state của [CLS] = representation của evidence-claim pair
```

### 5.3. BERT là model gì?

BERT là viết tắt của:

```text
Bidirectional Encoder Representations from Transformers
```

BERT là một **pre-trained language model** dựa trên Transformer.

Nó là model ngôn ngữ, nhưng khác GPT ở điểm chính:

| Model | Kiểu kiến trúc | Mục đích phổ biến |
|:---|:---|:---|
| **BERT** | Encoder-only Transformer | Hiểu văn bản, tạo representation, classification, NLI |
| **GPT** | Decoder-only Transformer | Sinh văn bản, chat, completion |

Vì vậy:

```text
BERT có thể được gọi là language model,
nhưng không phải LLM sinh văn bản kiểu ChatGPT/GPT.
```

Nếu nói chính xác hơn:

```text
BERT là encoder-only pre-trained language model.
```

Trong GEAR, BERT không dùng để viết câu trả lời. Nó dùng để:

```text
Mã hóa claim và evidence thành vector ngữ nghĩa.
```

---

## 6. Sentence Encoder trong GEAR

### 6.1. Sentence Encoder dùng để làm gì?

Sentence Encoder là khối đầu tiên của GEAR.

Với mỗi evidence `e_i`, GEAR ghép evidence đó với claim:

```text
[CLS] evidence_i [SEP] claim [SEP]
```

Sau đó đưa vào BERT:

```text
e_i = BERT(evidence_i, claim)
c   = BERT(claim)
```

Và lấy vector `[CLS]`:

```text
e_i ∈ R^768
c   ∈ R^768
```

### 6.2. `e_i = BERT(evidence_i, claim)` đo cái gì?

Công thức này không chỉ đo semantic similarity.

Nó tạo một vector biểu diễn:

```text
Evidence i có quan hệ gì với claim?
```

Vector `e_i` có thể chứa tín hiệu như:

- Evidence và claim nói về cùng entity không?
- Evidence có support claim không?
- Evidence có mâu thuẫn claim không?
- Evidence chỉ liên quan nhưng chưa đủ kết luận không?
- Có chi tiết nào cần chú ý như năm, địa điểm, quốc tịch, nghề nghiệp không?

Ví dụ:

```text
Evidence:
The film was released in 1997.

Claim:
The film was released in 2001.
```

BERT representation cần ghi nhận chi tiết:

```text
1997 khác 2001
```

Tín hiệu này quan trọng cho nhãn **REFUTES**.

### 6.3. Vì sao chỉ BERT encoder là chưa đủ?

Vì mỗi evidence được encode riêng.

```text
Evidence 1 + claim -> vector e1
Evidence 2 + claim -> vector e2
Evidence 3 + claim -> vector e3
```

Ở bước này:

```text
Evidence 1 chưa nhìn thấy Evidence 2.
```

Nhưng nhiều claim cần kết hợp nhiều evidence.

Ví dụ:

```text
Claim:
The Rodney King riots took place in the most populous county in the USA.

Evidence 1:
The Rodney King riots occurred in Los Angeles County.

Evidence 2:
Los Angeles County is the most populous county in the United States.
```

Evidence 1 chỉ biết:

```text
Rodney King riots -> Los Angeles County
```

Evidence 2 chỉ biết:

```text
Los Angeles County -> most populous county
```

Muốn support claim, cần nối hai thông tin này lại. Đây là lý do cần ERNet.

---

## 7. ERNet - Evidence Reasoning Network

### 7.1. ERNet là gì?

ERNet là viết tắt của:

```text
Evidence Reasoning Network
```

Mục đích:

```text
Cho các evidence trao đổi thông tin với nhau.
```

GEAR xây một fully-connected evidence graph:

- Mỗi evidence là một node.
- Mọi node nối với mọi node khác.
- Có self-loop.

Trạng thái ban đầu:

```text
h_i^0 = e_i
```

Trong đó:

- `e_i` là vector BERT của evidence `i`.
- `h_i^0` là hidden state ban đầu của node `i`.

### 7.2. Một ERNet layer tính gì?

Tại layer `t`, `9_6.md` ghi:

```text
p_ij = W1(ReLU(W0(h_i^(t-1) || h_j^(t-1))))
α_ij = exp(p_ij) / Σ_k exp(p_ik)
h_i^t = Σ_j α_ij h_j^(t-1)
```

Đây là một vòng message passing.

Nói bằng lời:

```text
Mỗi evidence i nhìn tất cả evidence j,
tính xem evidence j hữu ích với evidence i đến mức nào,
rồi cập nhật evidence i bằng tổng có trọng số của các evidence khác.
```

### 7.3. `p_ij` đo cái gì?

```text
p_ij = W1(ReLU(W0(h_i^(t-1) || h_j^(t-1))))
```

`p_ij` là điểm quan hệ giữa evidence `i` và evidence `j`.

Nó đo:

```text
Evidence j hữu ích như thế nào khi cập nhật evidence i?
```

Trong đó:

- `h_i^(t-1)`: trạng thái evidence `i` ở layer trước.
- `h_j^(t-1)`: trạng thái evidence `j` ở layer trước.
- `||`: nối hai vector.
- `W0`, `W1`: tham số học được.
- `ReLU`: giúp mô hình học quan hệ phi tuyến.

Ví dụ:

```text
Evidence i:
The Rodney King riots occurred in Los Angeles County.

Evidence j:
Los Angeles County is the most populous county in the United States.
```

Nếu claim hỏi về “most populous county”, thì `p_ij` nên cao vì evidence `j` bổ sung thông tin còn thiếu cho evidence `i`.

### 7.4. `α_ij` đo cái gì?

```text
α_ij = exp(p_ij) / Σ_k exp(p_ik)
```

`α_ij` là attention weight trong ERNet.

Nó đo:

```text
Trong tất cả evidence mà node i có thể nhận thông tin,
evidence j nên chiếm trọng số bao nhiêu?
```

Softmax làm cho:

```text
Σ_j α_ij = 1
```

Ví dụ:

```text
α_i1 = 0.10
α_i2 = 0.75
α_i3 = 0.15
```

Nghĩa là khi cập nhật evidence `i`, model lấy nhiều thông tin nhất từ evidence 2.

### 7.5. `h_i^t` là gì?

```text
h_i^t = Σ_j α_ij h_j^(t-1)
```

`h_i^t` là trạng thái mới của evidence `i` sau layer `t`.

Nó là:

```text
Tổng có trọng số của các evidence khác.
```

Mục đích:

```text
Biến evidence i từ một representation riêng lẻ
thành representation đã hấp thụ thông tin từ toàn evidence set.
```

### 7.6. Số ERNet layers nghĩa là gì?

Paper thử:

```text
0, 1, 2, 3 ERNet layers
```

Ý nghĩa:

| Số layer | Ý nghĩa |
|---:|:---|
| `0` | Không message passing; aggregator nhận trực tiếp BERT vectors |
| `1` | Evidence trao đổi thông tin một lần |
| `2` | Evidence trao đổi thông tin hai lần |
| `3` | Message passing sâu hơn |

Theo `9_6.md`, trên difficult dev subset:

| ERNet layers | Attention | Max | Mean |
|---:|---:|---:|---:|
| 0 | 66.17 | 65.36 | 65.03 |
| 1 | 67.13 | 66.63 | 66.76 |
| 2 | 67.44 | 67.24 | **67.56** |
| 3 | 66.53 | 66.72 | 66.89 |

Cách đọc bảng:

- `0` layer là không có ERNet reasoning.
- Tăng lên `1` hoặc `2` thường giúp kết quả tốt hơn trên difficult subset.
- `3` không nhất thiết tốt hơn, vì message passing quá nhiều có thể làm thông tin bị trộn quá mức.

Lưu ý:

```text
ERNet layer không phải BERT layer.
BERT encode text trước.
ERNet reasoning giữa các evidence sau.
```

---

## 8. Evidence Aggregator

### 8.1. Aggregator dùng để làm gì?

Sau ERNet, ta có nhiều node states:

```text
h_1^T, h_2^T, ..., h_N^T
```

Nhưng classifier cần một vector duy nhất:

```text
o
```

Vì vậy cần Evidence Aggregator:

```text
Nhiều evidence vectors -> một vector cuối o
```

Mục đích thực tế:

```text
Gom toàn bộ thông tin evidence sau reasoning
thành một representation cấp claim.
```

Paper thử ba cách:

- Attention
- Max
- Mean

Ba cách này không phải metric. Chúng là ba cách tạo vector cuối `o`. Vector `o` tốt hơn thì classifier có cơ hội dự đoán nhãn đúng hơn, từ đó metric evaluation cao hơn.

---

### 8.2. Mean aggregator

Mean lấy trung bình các evidence vectors:

```text
o = mean(h_1^T, h_2^T, ..., h_N^T)
```

Nó đo/gom theo kiểu:

```text
Thông tin trung bình của toàn bộ evidence set là gì?
```

Mục đích thực tế:

```text
Cho các evidence đóng góp tương đối ngang nhau.
```

Ưu điểm:

- Đơn giản.
- Ổn định.
- Không cần học trọng số riêng cho từng evidence.

Nhược điểm:

- Evidence quan trọng và evidence nhiễu bị trộn tương đối ngang nhau.
- Nếu có nhiều evidence nhiễu, vector cuối có thể bị loãng.

Ví dụ:

```text
Evidence 1: rất quan trọng
Evidence 2: khá quan trọng
Evidence 3: nhiễu
```

Mean vẫn lấy trung bình cả ba.

Trong evaluation:

```text
Mean không tính metric.
Mean chỉ tạo vector o.
Metric đo xem prediction từ vector o đúng hay sai.
```

---

### 8.3. Max aggregator

Max lấy giá trị lớn nhất theo từng chiều vector:

```text
o_k = max(h_1k^T, h_2k^T, ..., h_Nk^T)
```

Trong đó `k` là một chiều của vector.

Nó đo/gom theo kiểu:

```text
Ở mỗi loại tín hiệu,
evidence nào có tín hiệu mạnh nhất thì giữ tín hiệu đó.
```

Ví dụ trực giác:

- Một chiều vector có thể đang biểu diễn tín hiệu contradiction.
- Nếu một evidence có tín hiệu contradiction rất mạnh ở chiều đó, Max giữ lại tín hiệu này.

Mục đích thực tế:

```text
Bắt các tín hiệu nổi bật nhất trong evidence set.
```

Ưu điểm:

- Tốt khi chỉ một hoặc vài evidence chứa tín hiệu rất mạnh.
- Có thể giữ lại tín hiệu quan trọng dù các evidence khác yếu hơn.

Nhược điểm:

- Không học evidence nào quan trọng theo claim.
- Có thể lấy tín hiệu mạnh nhưng nhiễu.
- Không mềm như attention.

Trong evaluation:

```text
Max là một configuration của GEAR.
Nó ảnh hưởng đến prediction, rồi prediction mới được metric đánh giá.
```

---

### 8.4. Attention aggregator

Attention aggregator học trọng số evidence dựa trên claim.

Trong `9_6.md`, công thức là:

```text
p_j = W1'(ReLU(W0'(c || h_j^T)))
α_j = exp(p_j) / Σ_k exp(p_k)
o   = Σ_j α_j h_j^T
```

### 8.5. `p_j` đo cái gì?

```text
p_j = W1'(ReLU(W0'(c || h_j^T)))
```

`p_j` là điểm quan trọng của evidence `j` đối với claim.

Nó đo:

```text
Evidence j quan trọng thế nào cho quyết định cuối?
```

Trong đó:

- `c`: representation của claim.
- `h_j^T`: representation của evidence `j` sau ERNet.
- `W0'`, `W1'`: tham số học được.
- `ReLU`: giúp học quan hệ phi tuyến.

Khác với `p_ij` trong ERNet:

| Điểm | Nằm ở đâu? | Câu hỏi |
|:---|:---|:---|
| `p_ij` | ERNet | Evidence `j` hữu ích cho evidence `i` không? |
| `p_j` | Aggregator | Evidence `j` quan trọng với claim cuối không? |

### 8.6. `α_j` đo cái gì?

```text
α_j = exp(p_j) / Σ_k exp(p_k)
```

`α_j` là trọng số attention của evidence `j`.

Nó đo:

```text
Evidence j nên đóng góp bao nhiêu vào vector cuối o?
```

Ví dụ:

```text
α_1 = 0.55
α_2 = 0.35
α_3 = 0.10
```

Cách hiểu:

```text
Evidence 1 đóng góp nhiều nhất vào vector cuối.
Evidence 3 ít quan trọng hơn.
```

### 8.7. `o` là gì?

```text
o = Σ_j α_j h_j^T
```

`o` là vector cuối của toàn bộ evidence set.

Nó là:

```text
Tổng có trọng số của các evidence sau ERNet.
```

Mục đích thực tế:

```text
Tập trung vào evidence quan trọng,
giảm ảnh hưởng của evidence nhiễu,
tạo representation cuối cho classifier.
```

### 8.8. So sánh Mean, Max, Attention

| Aggregator | Gộp thông tin như thế nào? | Mục đích thực tế | Điểm mạnh | Điểm yếu |
|:---|:---|:---|:---|:---|
| **Mean** | Trung bình tất cả evidence vectors | Lấy thông tin chung | Đơn giản, ổn định | Dễ bị evidence nhiễu làm loãng |
| **Max** | Lấy tín hiệu mạnh nhất theo từng chiều | Giữ tín hiệu nổi bật | Bắt tín hiệu mạnh từ một evidence | Có thể bắt cả tín hiệu nhiễu |
| **Attention** | Học trọng số từng evidence dựa trên claim | Tập trung vào evidence quan trọng | Linh hoạt, claim-guided | Attention không luôn là giải thích hoàn hảo |

Theo `9_6.md`, mô hình cuối được chọn theo dev FEVER Score dùng:

```text
Threshold τ = 10^-3
Một ERNet layer
Attention aggregator
```

Điểm cần nhớ:

```text
Aggregator không tính FEVER Score.
Aggregator tạo vector o.
Classifier tạo prediction.
FEVER Score đánh giá prediction và evidence sau đó.
```

---

## 9. Classifier

### 9.1. Classifier dùng để làm gì?

Sau aggregator, model có vector cuối:

```text
o
```

Classifier biến vector này thành xác suất trên ba nhãn:

```text
SUPPORTS
REFUTES
NEI
```

Trong `9_6.md`, công thức là:

```text
l = softmax(ReLU(Wo + b))
```

`l` là phân phối xác suất trên ba nhãn.

Ví dụ:

```text
l = [0.82, 0.07, 0.11]
```

Có thể đọc là:

```text
P(SUPPORTS) = 0.82
P(REFUTES)  = 0.07
P(NEI)      = 0.11
```

Model chọn nhãn có xác suất cao nhất:

```text
Predicted label = SUPPORTS
```

### 9.2. `Wo + b` đo cái gì?

```text
Wo + b
```

Đây là phép biến đổi tuyến tính từ vector `o` sang score của các nhãn.

Nó tạo score thô:

```text
score_SUPPORTS
score_REFUTES
score_NEI
```

Nói dễ hiểu:

```text
Từ representation cuối,
model chấm điểm từng nhãn.
```

### 9.3. `ReLU` dùng để làm gì?

```text
ReLU(Wo + b)
```

ReLU thêm phi tuyến.

Mục đích:

```text
Giúp classifier học quyết định phức tạp hơn
thay vì chỉ là một phép tuyến tính đơn giản.
```

### 9.4. `softmax` đo cái gì?

```text
softmax(...)
```

Softmax biến score thành xác suất.

Mục đích:

```text
Cho biết model tin mỗi nhãn bao nhiêu.
```

Ví dụ:

```text
SUPPORTS: 82%
REFUTES: 7%
NEI: 11%
```

---

## 10. Các khối Method ảnh hưởng tới evaluation như thế nào?

Dòng chảy đúng là:

```text
Document Retrieval
  -> Sentence Selection
  -> Evidence Filter
  -> Sentence Encoder
  -> ERNet
  -> Aggregator
  -> Classifier
  -> Predicted label
  -> Evaluation metrics
```

Các khối trong Method không tự tính metric. Chúng ảnh hưởng metric gián tiếp thông qua prediction.

| Thành phần | Nếu làm tốt thì giúp gì? |
|:---|:---|
| **Document Retrieval** | Lấy đúng trang chứa evidence |
| **Sentence Selection** | Lấy đúng câu evidence |
| **Evidence Filter** | Giảm câu nhiễu đưa vào GEAR |
| **Sentence Encoder** | Tạo vector tốt cho từng evidence-claim pair |
| **ERNet** | Kết hợp thông tin giữa nhiều evidence |
| **Aggregator** | Gom evidence thành vector cuối hợp lý |
| **Classifier** | Dự đoán đúng nhãn |

Nếu label đúng nhiều:

```text
Label Accuracy tăng.
```

Nếu label đúng và evidence đúng theo yêu cầu FEVER:

```text
FEVER Score tăng.
```

Vì vậy:

```text
GEAR mạnh hơn giúp verification tốt hơn,
nhưng full pipeline vẫn phụ thuộc rất nhiều vào retrieval và sentence selection.
```

---

## 11. Ví dụ chạy qua full Method

Claim:

```text
The Rodney King riots took place in the most populous county in the USA.
```

### Bước 1: Document Retrieval

Tìm các trang liên quan:

```text
Rodney King riots
Los Angeles County
United States counties by population
```

Mục đích:

```text
Tìm đúng nơi có thể chứa evidence.
```

### Bước 2: Sentence Selection + Evidence Filter

Chọn các câu:

```text
e1:
The Rodney King riots occurred in Los Angeles County.

e2:
Los Angeles County is the most populous county in the United States.
```

Mục đích:

```text
Lọc ra các câu có relevance cao với claim.
```

### Bước 3: Sentence Encoder

Encode từng cặp:

```text
BERT(e1, claim) -> vector e1
BERT(e2, claim) -> vector e2
```

Mục đích:

```text
Biến text thành vector ngữ nghĩa.
```

### Bước 4: ERNet

Cho evidence trao đổi thông tin:

```text
e1 học thêm: Los Angeles County là most populous county.
e2 học thêm: Rodney King riots xảy ra ở Los Angeles County.
```

Mục đích:

```text
Kết nối hai mảnh evidence.
```

### Bước 5: Aggregator

Gom evidence:

```text
{h1, h2} -> o
```

Nếu dùng attention:

```text
Evidence nào quan trọng hơn cho claim thì có trọng số lớn hơn.
```

### Bước 6: Classifier

Dự đoán:

```text
o -> SUPPORTS
```

Kết luận:

```text
Claim được support bởi hai evidence kết hợp với nhau.
```

---

## 12. Một câu tóm tắt để trình bày

Section 3 của GEAR mô tả full pipeline từ claim đến label: đầu tiên retrieval tìm trang Wikipedia liên quan, sentence selection chọn các câu evidence, evidence filter loại câu relevance thấp, rồi GEAR thực hiện claim verification. Trong GEAR, BERT sentence encoder biến từng evidence-claim pair thành vector, ERNet cho các evidence trao đổi thông tin trong fully-connected graph, evidence aggregator gom nhiều evidence vectors thành một vector cuối bằng Mean, Max hoặc Attention, và classifier dự đoán SUPPORTS, REFUTES hoặc NEI. Các bước này không trực tiếp tính metric, nhưng quyết định prediction cuối, từ đó ảnh hưởng đến Label Accuracy và FEVER Score.
