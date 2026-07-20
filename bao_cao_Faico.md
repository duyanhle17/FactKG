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

---

# 8. Đề xuất tiếp theo cho FactKG: Faico-Lite candidate retriever cho GEAR-Lite

## 8.1. Ý tưởng chính: cải thiện path **trước** khi attention chọn path

Kết quả GEAR-Lite hiện tại cho thấy E2 (Pair + Attention) đã có cơ chế gộp nhiều path tốt hơn E1 (Pair + Mean). Tuy nhiên, E2 chỉ có thể đặt trọng số lên các path đã nằm trong candidate set. Nếu proof multi-hop đúng bị bỏ ở bước graph traversal, attention không thể tự tạo lại nó.

Vì vậy, hướng lấy cảm hứng từ Faico phù hợp nhất **không phải** thay BERT/attention bằng LLM hoặc triển khai toàn bộ token-trie của Faico. Hướng nhỏ, khả thi hơn là:

> Giữ nguyên relation predictor, hop predictor và E2 Attention; thay cách sinh candidate path bằng một traversal có cấu trúc, xác định và ít làm mất alternative proof hơn.

Ta gọi bản thử này là **Faico-Lite candidate retriever**. Đây là một adaptation cho FactKG, không phải khẳng định rằng ta đã tái lập nguyên vẹn Faico.

```text
Claim + entity trong claim + top-N relation dự đoán + hop cap H
                    │
                    ▼
Faico-Lite candidate retriever
(path hợp lệ, không ngẫu nhiên, giữ alternative proof)
                    │
                    ▼
Candidate paths p_1 ... p_K
                    │
                    ▼
GEAR-Lite E2 hiện có:
[Claim, Path_i] → shared BERT → h_i → Attention → o → MLP → True / False
```

Như vậy, Faico-Lite sửa tầng **retrieval/candidate construction**; E2 sửa tầng **aggregation/verifier**. Hai phần bổ sung cho nhau.

## 8.2. Vì sao đây có thể là bottleneck của multi-hop hiện tại?

Trong `with_evidence/classifier/preprocess.py`, test hiện tạo relation chain như sau:

```python
rels = {e: list(permutations(candids, r=hop)) for e in ents}
```

Điều này có ba hệ quả cần kiểm chứng:

1. `top-3`/`top-5` ở đây là số **relation label** được lấy từ relation predictor, không phải số path cuối cùng. Số path còn phụ thuộc vào entity, KG, graph branching, deduplication và traversal thất bại.
2. `permutations(..., r=hop)` chỉ sinh chain có **đúng** số hop dự đoán và không cho một relation xuất hiện hai lần. Nếu hop predictor sai, hoặc proof hợp lệ cần lặp relation, cả proof có thể không được sinh ra.
3. `KG.walk` hiện chọn ngẫu nhiên một tail ở hop cuối; `KG.search` lại gộp path theo cặp endpoint. Vì vậy hai relation chain khác nhau nhưng nối cùng một cặp entity có thể chỉ còn một path. Ngoài ra, heuristic dừng nhánh hiện tại có thể bỏ một chain tuyến tính chỉ có một tail ở intermediate hop. Các lựa chọn này giảm chi phí, nhưng làm candidate set không hoàn chỉnh và không xác định giữa các lần chạy.

Đây chính là liên hệ với Faico: Faico nhấn mạnh rằng trước khi reasoning, retriever cần giữ các path **hợp lệ về cấu trúc** và không bỏ mất proof chỉ vì heuristic traversal. Với FactKG, lỗi mất proof này tác động mạnh nhất đến nhóm `Multi-hop`.

## 8.3. Đề xuất kỹ thuật nhỏ: budgeted, deterministic path traversal

### Hai tham số cần phân biệt

- `H`: **hop cap** — số cạnh tối đa của path. Với cấu hình hiện tại có thể bắt đầu bằng `H = hop` dự đoán cho từng claim để so sánh công bằng với pipeline cũ.
- `k`: **relation budget** — một relation được phép xuất hiện tối đa bao nhiêu lần trong một path. Đây là ý tưởng lấy từ k-BET của Faico, không phải số hop.

Ví dụ, nếu `H = 3`, `R_q = {r1, r2, r3}` và `k = 1`, path `r1 → r2 → r1` bị loại vì `r1` lặp hai lần. Nếu `k = 2`, path đó được phép.

Lưu ý rất quan trọng: `permutations` hiện đã ngầm tương đương với `k = 1` khi chỉ xét một chain dài đúng `H`. Vì vậy, chỉ thêm chữ “k = 1” sẽ **không tự làm điểm tăng**. Giá trị của retriever mới ở lượt đầu là traversal đầy đủ, xác định, giữ full path và dedup đúng; `k = 2` là ablation sau để kiểm tra proof cần relation lặp.

### Faico-Lite retriever đề xuất

Với entity trong claim `T_q`, top-N relation `R_q` và `H`, duyệt state:

```text
state = (entity hiện tại, depth, số lần mỗi relation còn được dùng, serialized path)
```

Quy tắc:

1. Chỉ đi theo edge có relation thuộc `R_q`, đúng hướng và còn budget.
2. Duyệt tail theo thứ tự ổn định; không dùng `random.choice`.
3. Lưu mọi path hợp lệ đã tìm được, kể cả nhiều path có cùng endpoint; chỉ deduplicate bằng **toàn bộ serialized path** `(entity, relation, entity, ...)`, không chỉ bằng hai endpoint.
4. Dùng budget dominance kiểu Faico để tránh mở rộng state dư thừa: tại cùng một entity, không cần mở rộng một state nếu đã có state khác còn đủ hoặc nhiều budget hơn cho mọi relation. Tuy nhiên path đã tìm được vẫn phải được lưu để không mất alternative proof.
5. Giữ `depth ≤ H` ở bản đầu để kiểm soát graph explosion. Chia `connected`/`walkable` như artifact hiện có, đồng thời sắp xếp ổn định trước khi cắt `max_paths`.

Đầu ra vẫn có thể giữ schema cũ:

```python
{"connected": [...], "walkable": [...]}
```

Do đó E2 không cần đổi kiến trúc ở thử nghiệm đầu tiên. `max_paths=32`, `pair_max_length=128`, relation predictor và checkpoint E2 cần được giữ cố định để phép so sánh công bằng.

## 8.4. Thứ tự ablation nên chạy

Không nên bật đồng thời k-BET, thêm hop, tăng `K`, và thay attention: nếu điểm tăng sẽ không biết nguyên nhân là gì. Thứ tự sau tách được từng giả thuyết.

| Run | Candidate retriever | E2 classifier | Câu hỏi được trả lời |
|---|---|---|---|
| R0 | Artifact legacy hiện có | Attention hiện có | Mốc so sánh, ví dụ E2 top-5 hiện tại. |
| R1 | Cùng `top-N`, cùng hop chính xác như R0, nhưng traversal xác định; không `random.choice`; giữ full-path alternatives | Không đổi | Việc bỏ sót path do heuristic traversal có làm giảm Multi-hop không? |
| R2 | Faico-Lite k-BET, `k=1`, `depth ≤ H` | Không đổi | Budget-dominance có giữ candidate structure tốt hơn với chi phí chấp nhận được không? |
| R3 | R2, nhưng cho `depth ∈ [1, H]` | Không đổi | Hop predictor có đang loại proof ngắn hơn không? |
| R4 | R2/R3 tốt nhất, `k=2` chỉ trên claim multi-hop | Không đổi | Có proof quan trọng cần lặp relation không? |

`R3` và `R4` phải chạy riêng, không gộp, vì cả hai đều tăng số candidate path và tăng nhiễu. Với `top-3`, `H=3`, `k=1`, việc cho độ dài từ 1 đến 3 tạo tối đa `3 + 6 + 6 = 15` relation sequence cho mỗi start entity trước khi xét graph branching; đây là một ablation còn kiểm soát được. `k=2` nên chỉ thử sau khi log cho thấy coverage vẫn thiếu, vì graph có thể nở nhanh.

## 8.5. Cần đo gì ngoài accuracy?

Mục tiêu của thay đổi này là tăng khả năng proof đi vào candidate set, nên không đủ nếu chỉ nhìn Total Accuracy. Mỗi run cần log ít nhất:

- `Multi-hop` Accuracy và Macro-F1: chỉ số chính.
- Overall Accuracy/Macro-F1: để biết có làm hỏng các nhóm khác không.
- Số path trung bình/tối đa mỗi claim; tỷ lệ claim có hơn `K=32` path; tỷ lệ `connected` và `walkable`.
- Số path bị bỏ vì duplicate hoặc vì vượt `K`; nếu annotation đủ chi tiết, đo thêm gold relation-chain/path recall@32.
- Runtime, GPU memory và tính xác định: chạy lại cùng seed phải tạo cùng candidate artifact.

Điểm quyết định tiếp theo:

```text
Nếu R1/R2 tăng candidate coverage và Multi-hop tăng
    → giữ retriever mới, sau đó mới thử E2 có structural feature.
Nếu coverage tăng nhưng proof thường nằm sau path thứ 32
    → mới cân nhắc K=64 hoặc rank/select candidate trước E2.
Nếu coverage không tăng
    → bottleneck nằm ở relation/hop predictor; attention hay tăng K không thể tự tạo relation bị thiếu.
```

Điều này cũng trả lời vì sao chưa nên tăng `max_paths` một cách mù quáng: `K=32` là số path mà BERT pair encoder thực sự được thấy. Nếu proof đã bị traversal loại bỏ thì tăng K không giúp; nếu proof đã có nhưng bị cắt sau path 32 thì mới có bằng chứng để tăng K hoặc thiết kế selector.

## 8.6. Bước sau retrieval: structural attention nhỏ, nhưng không làm trước R1/R2

Nếu R1/R2 chứng minh candidate set đã tốt hơn nhưng E2 vẫn chọn nhầm path, có thể mở rộng scorer của E2 từ:

```text
score_i = MLP(h_i)
```

thành:

```text
score_i = MLP([h_i ; f_i])
```

Trong đó `h_i` vẫn là vector BERT của cặp Claim–Path, còn `f_i` là feature cấu trúc nhỏ, ví dụ:

- path có nối hai entity trong claim (`connected`) hay chỉ là walkable;
- số hop và relation budget đã dùng;
- log-probability của relation chain, nếu relation predictor xuất được score;
- cờ entity continuity/hướng relation hợp lệ.

Sau đó vẫn dùng masked softmax để có `α_i` và `o = Σ_i α_i h_i` như E2 cũ. Đây là **soft prior**, không phải hard pruning: một path có feature yếu vẫn có thể được BERT-attention chọn nếu nó thực sự chứng minh claim.

Không nên code bước này trước R1/R2. Nếu proof chưa xuất hiện trong candidate set, thêm feature vào attention chỉ làm model chọn “tốt hơn” giữa các path đều không đúng.

## 8.7. Phạm vi code hợp lý cho lượt đầu

Lượt đầu chỉ cần thêm mode mới, không ghi đè baseline:

```text
with_evidence/classifier/preprocess.py
  └─ thêm search_kbet(...) / retrieval_mode=legacy|kbet
     và ghi artifact riêng, ví dụ test_candid_paths_top5_kbet1.bin

with_evidence/classifier/baseline.py
  └─ không cần sửa kiến trúc E2 ở R1/R2;
     chỉ nạp artifact mới bằng cùng lệnh classifier hiện có.
```

Không nên thay relation predictor bằng token-trie/LLM ngay. FactKG đã có relation predictor theo schema; huấn luyện lại một Faico token-trie cần supervision relation riêng và là một đề tài lớn khác. Ý tưởng Faico có giá trị nhất ở giai đoạn này là **structural completeness của candidate path**, sau đó GEAR-Lite Attention mới phát huy đúng vai trò chọn mềm trong tập path đủ tốt.
