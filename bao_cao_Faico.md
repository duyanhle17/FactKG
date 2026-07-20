# Báo cáo paper Faico: Faithful and Complete Knowledge Graph Augmented Reasoning

Nguồn: [Faico: Faithful and Complete Knowledge Graph Augmented Reasoning](<Faico_ Faithful and Complete Knowledge Graph Augmented Reasoning.pdf>).

## Tóm tắt một câu

Faico tách bài toán KG-augmented reasoning thành hai phần: **LLM hiểu câu hỏi và sinh relation type hợp lệ**, còn **thuật toán graph truy xuất đầy đủ các path hợp lệ**. Mục tiêu là tránh việc LLM vừa phải hiểu semantics vừa điều khiển traversal từng bước.

```text
Question q
├── Entity linking → topic entities Tq
└── Fine-tuned LLM + token-trie → relevant relation types Rq

(Tq, Rq, KG, k)
→ budget-dominance k-BET retrieval
→ reasoning subgraph Gr

(q + Gr)
→ reasoning LLM
→ answer
```

---

## Abstract

### Vấn đề

LLM có năng lực ngôn ngữ mạnh nhưng kiến thức nội tại có thể lỗi thời, không có cấu trúc rõ ràng và dễ hallucinate. Knowledge Graph (KG) cung cấp fact có cấu trúc, nên phù hợp để hỗ trợ factual reasoning và multi-hop reasoning.

Tuy nhiên, các hệ thống KG + LLM trước đây thường gặp hai lỗi:

1. **Semantic misalignment**: model chọn sai hoặc bỏ sót relation phù hợp với ý nghĩa câu hỏi.
2. **Incomplete subgraph retrieval**: subgraph có thể chứa một số edge đúng nhưng mất edge trung gian, làm reasoning path bị đứt.

### Đề xuất của paper

Faico đề xuất một framework nhằm đồng thời đạt:

- **Semantic faithfulness**: relation trong subgraph phải thật sự liên quan đến câu hỏi.
- **Structural completeness**: subgraph phải giữ các path hoàn chỉnh nối topic entity với answer.

Hai thành phần chính là:

| Thành phần | Vai trò |
|---|---|
| Token-trie relation type generator | Fine-tune LLM để sinh relation hợp lệ trong schema KG và liên quan tới câu hỏi. |
| k-BET retriever + budget dominance | Duyệt KG theo relation đã sinh, giữ mọi path hợp lệ nhưng bỏ các trạng thái traversal dư thừa. |

---

# 1. Introduction

## 1.1. LLM và KG đang bổ sung cho nhau như thế nào?

LLM giỏi hiểu ngôn ngữ nhưng không bảo đảm fact đúng. KG lưu fact dạng:

```text
Entity --Relation→ Entity
```

KG có thể cung cấp:

- fact có thể kiểm tra;
- cấu trúc entity-relation rõ ràng;
- multi-hop reasoning;
- khả năng giải thích bằng path.

Nhưng chỉ đưa một phần KG vào LLM chưa đủ. Chất lượng answer phụ thuộc trực tiếp vào **reasoning subgraph** được lấy ra.

## 1.2. Hai kiểu phương pháp cũ và lỗi của chúng

### Model pre-select

LLM chọn relation tại từng bước traversal:

```text
topic entity
→ LLM chọn relation bước 1
→ graph traversal
→ LLM chọn relation bước 2
→ ...
```

Lỗi ở một bước sớm sẽ lan sang các bước sau (**cascading error**). Hệ thống cũng phải gọi LLM nhiều lần và thường dùng pruning để kiềm chế graph bùng nổ; pruning có thể làm mất path đúng.

### Model post-filter

Hệ thống lấy một candidate subgraph lớn trước, rồi dùng model lọc edge/triple. Cách này có thể bỏ nhầm một edge trung gian có vẻ ít liên quan khi xét riêng lẻ nhưng lại cần thiết trong proof path.

Ví dụ paper dùng câu hỏi:

> What country bordering France contains an airport that serves Nijmegen?

Reasoning cần các relation tương ứng với `airports`, `contained_by`, `adjoins` để nối tới `Germany`. Nếu pre-select bỏ `adjoins`, hoặc post-filter xóa edge `contained_by` giữa airport và Germany, chain không còn hoàn chỉnh.

## 1.3. Mục tiêu thực sự của Faico

Paper cho rằng model inference và graph retrieval đang bị ghép quá chặt. Faico tách rõ:

| Công việc | Thành phần phụ trách |
|---|---|
| Hiểu câu hỏi, chọn loại relation | Fine-tuned LLM |
| Giữ các path hợp lệ, đầy đủ | Thuật toán graph |
| Đọc subgraph để trả lời | Reasoning LLM |

Ba thách thức được nêu ra:

1. Tách model inference khỏi graph traversal.
2. Ánh xạ chính xác câu hỏi tự nhiên sang KG schema có relation dài và long-tail.
3. Lấy subgraph vừa đầy đủ vừa không quá lớn.

---

# 2. Preliminaries & Analysis

| Ký hiệu | Ý nghĩa |
|---|---|
| \(G=(V,E)\) | Knowledge Graph |
| \(q\) | Câu hỏi ngôn ngữ tự nhiên |
| \(T_q\) | Topic entities từ entity linking |
| \(\mathcal R_q\) | Tập relation type liên quan đến câu hỏi |
| \(G_r\) | Reasoning subgraph |
| \(k\) | Số lần tối đa mỗi relation được phép lặp trên một path |

Paper định nghĩa reasoning subgraph tốt cần đồng thời có hai thuộc tính.

## Semantic faithfulness

Subgraph phải chứa tất cả relation type thật sự được câu hỏi yêu cầu về mặt ngữ nghĩa.

Lưu ý: `faithfulness` ở paper này là faithfulness của **relation/subgraph với câu hỏi**, không phải chứng minh rằng lời văn final của LLM faithful theo nghĩa nhân quả.

## Structural completeness

Các edge phải ghép thành path hợp lệ từ topic entity tới answer. Có nhiều relation đúng nhưng mất một edge giữa chuỗi vẫn không đủ cho reasoning.

Hai thuộc tính phụ thuộc nhau:

```text
Thiếu relation đúng → không thể dựng path đầy đủ.
Thiếu edge/path → relation coverage không còn hữu ích cho answer.
```

---

# 3. Overview & Reasoning Subgraph Modeling

## 3.1. Tại sao không dùng BFS với số hop cố định?

BFS có depth lớn làm search space bùng nổ. Paper báo cáo trên CWQ: với depth 5, **47.72%** câu hỏi (1,680/3,531) sinh hơn **128 nghìn triple**. Điều này vừa chậm vừa vượt context window của LLM.

Ngược lại, depth nhỏ sẽ bỏ lỡ câu hỏi cần path dài. Faico không giới hạn tổng hop trực tiếp, mà giới hạn số lần mỗi relation được lặp.

## 3.2. k-Bounded Edge Type Path (k-BET)

Một path là k-BET nếu:

1. Mọi edge có relation thuộc \(\mathcal R_q\).
2. Mỗi relation \(\sigma\in\mathcal R_q\) xuất hiện không quá \(k\) lần trên path.

Ví dụ:

```text
Rq = {airports, contained_by, adjoins}
k = 1

Nijmegen
--airports→ Weeze Airport
--contained_by→ Germany
--adjoins→ France
```

Đây là path 3-hop hợp lệ dù \(k=1\), vì mỗi relation chỉ dùng một lần.

> \(k\) không phải số hop.

Nếu có \(|\mathcal R_q|\) relation, path có thể dài tối đa \(k|\mathcal R_q|\) trong không gian relation đã chọn.

## 3.3. Maximal k-BET subgraph

Faico tìm subgraph sao cho:

- chứa topic entities \(T_q\);
- mỗi node khác reachable từ topic entity qua k-BET path;
- không thể thêm node/edge hợp lệ nào nữa mà vẫn giữ điều kiện k-BET.

`Maximal` không có nghĩa là proof nhỏ nhất hay toàn bộ KG. Nó nghĩa là đầy đủ nhất **trong phạm vi**:

```text
topic entities Tq
predicted relation types Rq
relation budget k
facts có thật trong KG
```

Vì vậy Faico không thể cứu trường hợp entity linking sai, relation generator bỏ sót relation đúng hoặc KG thiếu fact.

---

# 4. Reasoning Subgraph Retrieval

## 4.1. State phải là `(node, budget)`, không chỉ là `node`

Trong BFS thông thường, đã thăm node thì không cần thăm lại. Với k-BET, hai path tới cùng node có thể còn relation budget khác nhau:

```text
Path A: [r1=1, r2=0]
Path B: [r1=0, r2=1]
```

Hai trạng thái này không thay thế nhau: A có thể đi tiếp bằng `r1`, B có thể đi tiếp bằng `r2`.

Ban đầu:

\[
B(\sigma)=k,\qquad \forall\sigma\in\mathcal R_q
\]

Sau khi dùng relation \(\sigma\):

\[
B(\sigma)\leftarrow B(\sigma)-1
\]

## 4.2. Budget dominance

Hai path tới cùng node có budget \(B\) và \(B'\). Nếu:

\[
B(\sigma)\le B'(\sigma),\qquad
\forall\sigma\in\mathcal R_q
\]

thì \(B\) bị \(B'\) thống trị: mọi bước tiếp theo từ \(B\) cũng có thể thực hiện từ \(B'\).

Ví dụ:

```text
B_current = [r1=0, r2=0, r3=1]
B_old     = [r1=0, r2=1, r3=1]
```

`B_current` không mở ra khả năng traversal mới, nên có thể bỏ qua an toàn.

## 4.3. Budget-dominance node skipping algorithm

```text
Input: Tq, Rq, KG G, k
Output: maximal k-BET reasoning subgraph Gr

1. Khởi tạo budget k cho mọi relation ở từng topic entity.
2. Duyệt edge có relation thuộc Rq và còn budget.
3. Thêm triple hợp lệ vào Gr.
4. Tại node kế tiếp, so sánh budget mới với lịch sử budget của node đó.
5. Nếu budget mới bị thống trị: không mở rộng sâu hơn.
6. Nếu không: lưu budget mới, xóa các budget cũ bị thống trị, tiếp tục traversal.
```

Mỗi node giữ một tập budget không thống trị lẫn nhau, tương tự **Pareto frontier**.

Điểm mạnh của cách này là nó không cắt path dựa trên similarity heuristic; nó bỏ một state chỉ khi state khác tại cùng node chắc chắn còn nhiều hoặc bằng khả năng mở rộng.

Trường hợp xấu vẫn lớn, nhưng paper cho rằng \(|\mathcal R_q|\) và \(k\) thường nhỏ, nên pruning giảm đáng kể các nhánh lặp trong thực tế.

---

# 5. Trie-based Relation Type Learning

Mục này tạo \(\mathcal R_q\), tức relation type cần dùng cho retrieval.

Relation generator phải thỏa hai điều kiện:

1. **Schema validity**: relation sinh ra phải tồn tại trong KG.
2. **Semantic coverage**: không bỏ sót relation cần cho câu hỏi.

## 5.1. Token-trie relation generation

Toàn bộ relation label hợp lệ được token hóa và tổ chức thành prefix tree:

```text
root
├── sports
│   └── team
│       ├── mascot
│       └── champion
└── time
    └── event
        └── end_date
```

Các leaf path tương ứng với relation hợp lệ:

```text
sports_team_mascot
sports_team_champion
time_event_end_date
```

### Masked softmax

LLM tạo logits trên toàn bộ vocabulary, nhưng chỉ token là child hợp lệ trong trie mới được phép có xác suất khác 0:

\[
P(\tau\mid p,q)=
\frac{\exp(z_\tau)}
{\sum_{\tau'\in\mathrm{Child}(p)}\exp(z_{\tau'})}
\]

với \(\tau\) là child hợp lệ; token khác có xác suất bằng 0.

Kết quả:

- LLM không thể hallucinate relation ngoài KG schema.
- Mọi output relation hoàn chỉnh đều tồn tại trong KG.
- Trie chỉ đảm bảo schema-valid, chưa bảo đảm semantic relevance.

### Beam width \(b\) và threshold \(\theta\)

Faico không chỉ chọn một relation. Nó duyệt nhiều branch trên trie:

1. Mask token không hợp lệ.
2. Tính softmax.
3. Giữ tối đa top-\(b\) token.
4. Chỉ giữ branch có xác suất lớn hơn \(\theta\).
5. Tới leaf thì thêm relation hoàn chỉnh vào \(\mathcal R_q\).

Trade-off:

```text
θ thấp / beam lớn → recall relation cao hơn, nhưng graph lớn và nhiều nhiễu.
θ cao / beam nhỏ → precision cao hơn, nhưng dễ mất proof relation.
```

## 5.2. Trie-based Path Learning

`Path` tại mục này là **đường token trên trie**, không phải multi-hop path trong KG.

Pipeline train:

```text
Ground-truth SPARQL
→ trích relation type
→ tách thành token sequence theo trie
→ tạo supervision cho từng prefix
→ LoRA fine-tuning với masked KL divergence
```

Loss chỉ tính trên token là child hợp lệ của trie. Điều này giảm gradient noise từ những token không thể tạo thành relation KG hợp lệ.

Điểm cần nhớ:

> Relation generator cần ground-truth SPARQL/relation type để train; Faico không phải phương pháp hoàn toàn zero-shot.

---

# 6. Experimental Studies

## 6.1. Thiết lập

### Datasets

- WebQSP
- CWQ (Complex WebQuestions)
- GrailQA

KG nền là Freebase đã làm sạch, gồm khoảng:

- 100.1 triệu node;
- 736.2 triệu edge;
- hơn 20,400 relation type.

### Baselines

LLM-native: `LLM-direct`, `LLM-CoT`.

KG-augmented: `ToG`, `RoG`, `Plan-on-Graph`, `GoG`, `Paths-over-Graph`, `SubgraphRAG`.

### Thiết lập chính

- Default \(k=1\), \(\theta=0.01\).
- Relation generator được fine-tune với LoRA.
- Qwen-Plus được dùng làm reasoning LLM cho answer.
- Metric gồm Hit*, Hit@1, macro Precision/Recall/F1, query time, LLM calls và token usage.

## 6.2. RQ1 — Query Performance

| Dataset | Model | Hit* | Hit@1 | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|---:|
| WebQSP | Paths-over-Graph | 81.7 | 73.6 | 66.9 | 60.9 | 60.1 |
|  | **Faico** | **88.6** | **84.0** | 77.3 | **75.3** | **73.4** |
| CWQ | Paths-over-Graph | 72.1 | 69.1 | 66.8 | **65.4** | **65.2** |
|  | **Faico** | **75.2** | **70.5** | **67.6** | 65.3 | 64.9 |
| GrailQA | **Paths-over-Graph** | **84.8** | **79.0** | **75.1** | **71.3** | **70.2** |
|  | Faico | 78.4 | 68.4 | 66.1 | 61.8 | 62.1 |

Diễn giải:

- Trên WebQSP, Faico tăng Hit@1 từ 73.6 lên 84.0: **+10.4 điểm tuyệt đối**, tương đương khoảng **14.1% tương đối**.
- Trên CWQ, Faico tăng Hit@1 từ 69.1 lên 70.5: khoảng **2.0% tương đối**, nhưng thua rất nhẹ về Recall/F1.
- Trên GrailQA, Faico không thắng; Paths-over-Graph tốt hơn ở toàn bộ metric chính.

## 6.3. OOD và completeness — RQ2

| Dataset | Unseen relation-label ratio | Label F1 | Label Hit | Graph Answer Hit |
|---|---:|---:|---:|---:|
| WebQSP | 4.8% | 13.6 | 39.2 | 67.1 |
| CWQ | 2.7% | 38.5 | 71.6 | 43.2 |
| GrailQA | **56.2%** | 34.1 | 69.0 | 86.5 |

GrailQA có tỷ lệ relation label chưa thấy trong train rất cao. Dù Graph Answer Hit đạt 86.5, Hit@1 cuối chỉ 68.4. Điều này cho thấy:

> Subgraph chứa answer không đảm bảo reasoning LLM sẽ chọn đúng answer.

Trên WebQSP, Faico đạt:

- Edge Recall: 75.9%;
- Edge Precision: 58.7%;
- Edge Coverage: 62.7%.

Thông điệp của Figure 6 là: có nhiều relation đúng vẫn chưa đủ; chúng phải nối thành cấu trúc/path giúp tới được answer.

## 6.4. RQ3 — Efficiency

| Dataset | Faico LLM calls | Input tokens | Avg. edges | Time/query | Hit@1 |
|---|---:|---:|---:|---:|---:|
| WebQSP | 1 | 2,290.3 | 57.0 | 6.91 s | 84.0 |
| CWQ | 1 | 3,295.0 | 101.7 | 10.27 s | 70.5 |
| GrailQA | 1 | 1,601.2 | 18.4 | 6.26 s | 68.4 |

So với Paths-over-Graph, Faico nhanh hơn khoảng:

- 21 lần trên WebQSP;
- 17.5 lần trên CWQ;
- 12.5 lần trên GrailQA.

Faico cũng giảm hơn 73.9% input token so với Plan-on-Graph trên WebQSP.

Tuy nhiên, `LLM calls` trong Table 3 chỉ tính generative LLM calls; nó không mô tả đầy đủ chi phí local model inference, graph traversal, GPU memory hay năng lượng.

## 6.5. RQ4 — Ablation và robustness

| Cấu hình trên WebQSP | Hit@1 | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| **Faico: Token-trie + k-BET** | **84.0** | **77.3** | 75.3 | **73.4** |
| Token-trie → LLM rerank | 60.5 | 54.5 | 52.0 | 50.7 |
| Token-trie → Direct SFT | 77.3 | 72.7 | 70.8 | 69.6 |
| k-BET → Graph-level occurrence | 74.7 | 70.0 | 59.3 | 60.0 |
| k-BET → Bounded BFS | 78.6 | 72.8 | 62.3 | 62.9 |

Kết quả này là bằng chứng mạnh nhất cho đóng góp của paper:

- Bỏ token-trie làm Hit@1 giảm mạnh, nhất là khi dùng LLM rerank.
- Thay k-BET bằng bounded BFS/GLO làm Recall và F1 giảm đáng kể.
- Nghĩa là baseline có thể vẫn tìm được vài answer đúng, nhưng không giữ complete answer set tốt bằng k-BET.

Đổi reasoning LLM:

| Backbone | Hit@1 |
|---|---:|
| Qwen-Plus | 84.0 |
| GPT-4o-mini | 83.1 |
| DeepSeek-v3.1 | 80.2 |

Faico khá ổn định khi đổi backbone, nhưng backbone vẫn ảnh hưởng đến chất lượng final answer.

### Threshold sensitivity

Paper cho thấy end-to-end performance đạt đỉnh quanh \(\theta=0.02\). Threshold quá cao sẽ giảm relation recall/coverage và bỏ proof path.

Lưu ý quan trọng: phần văn bản của paper mô tả Precision và Recall cùng tăng theo \(\theta\), nhưng Figure 7 cho thấy Recall/Coverage giảm khi threshold tăng. Đồ thị và trực giác retrieval ủng hộ cách hiểu: threshold cao hơn thường đổi recall lấy precision.

---

# 7. Conclusion

Kết luận của tác giả là Faico đạt semantic faithfulness, structural completeness, answer accuracy và efficiency bằng cách tách:

```text
Semantic alignment      → fine-tuned LLM + token-trie
Structural retrieval    → maximal k-BET + budget dominance
Answer generation       → reasoning LLM
```

Điểm mạnh nhất của paper không phải là một classifier mới, mà là thiết kế retrieval:

> Dùng LLM để dự đoán **relation nào cần tìm**, sau đó dùng thuật toán graph để đảm bảo **path nào cần giữ**.

## Đánh giá khách quan

### Điểm mạnh

- Phân tách semantics và structure rõ ràng.
- Token-trie chặn relation hallucination ngoài schema.
- k-BET linh hoạt hơn fixed-depth search.
- Budget dominance có cơ sở logic, không chỉ là pruning heuristic.
- Ablation cho thấy token-trie và k-BET đều có đóng góp lớn.
- Hiệu quả token và latency tốt so với các phương pháp gọi LLM nhiều bước.

### Giới hạn

- Faico không thắng trên GrailQA.
- Relation generator cần supervision từ SPARQL/relation label.
- Completeness chỉ đúng có điều kiện theo \(T_q\), \(\mathcal R_q\), \(k\) và KG snapshot.
- Relation generator bỏ sót relation đúng thì graph algorithm không thể tự sửa.
- Subgraph có answer vẫn chưa bảo đảm final LLM chọn answer đúng.
- Không thấy báo cáo mean/std qua nhiều seed hoặc significance test.
- Ablation chỉ thực hiện trên WebQSP.
- Một số proof/parameter detail nằm ở Appendix B–H nhưng không xuất hiện trong bản PDF được cung cấp.

## Liên hệ với FactKG và GEAR-Lite

Faico và GEAR-Lite giải quyết hai bottleneck khác nhau:

```text
Faico: relation/path nào được sinh và giữ trong candidate set?
GEAR-Lite: trong candidate set đó, path nào nên được đặt trọng số cao hơn?
```

Vì vậy chúng có thể ghép nối:

```text
Faico-style relation/path retrieval
→ candidate paths ít bỏ sót và hợp lệ hơn
→ GEAR-Lite Attention
→ giảm trọng số path nhiễu
→ True / False
```
