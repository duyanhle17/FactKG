# Cải tiến 15/7: GEAR-Lite cho FactKG

Mục tiêu: cải thiện fact verification trên FactKG, ưu tiên multi-hop, nhưng vẫn đánh giá đủ năm loại reasoning: one-hop, conjunction, existence, multi-hop và negation.

## 1. Vấn đề cần giải quyết

Pipeline hiện tại là:

~~~text
Claim + Entity_set
  -> relation predictor + hop predictor
  -> candidate paths từ KG
  -> flatten tất cả path thành một chuỗi
  -> BERT-Concat + MLP
  -> True / False
~~~

Kết quả đã báo cáo với top-5, 3-hop là multi-hop 68.84% và tổng accuracy 81.80%. Multi-hop vẫn là nhóm yếu nhất.

Ba nguyên nhân chính cần tách riêng:

1. **Proof path chưa được sinh ra.** Relation/hop prediction hoặc traversal sai làm evidence cần thiết không đi tới classifier.
2. **Proof path bị mất khi concat.** BERT hiện chỉ nhận tối đa 512 token cho tổng claim và evidence. Tăng top-K/hop có thể sinh thêm path đúng, nhưng path đó nằm sau phần bị cắt.
3. **Nhiễu path.** Nhiều candidate sai được đưa cùng vào BERT-Concat làm tín hiệu evidence đúng bị loãng.

### Truncate là gì?

Tokenization chia input thành token. Khi tổng claim và evidence dài hơn 512 token, **truncate** cắt bỏ token ở cuối. Những token bị cắt không đi vào BERT, không nhận attention và không thể ảnh hưởng đến dự đoán.

Ví dụ: input dài 620 token thì 108 token cuối bị bỏ. Nếu path đúng nằm trong phần đó, tăng top-K không giúp classifier dù retrieval đã sinh được path đúng.

Lưu ý: GEAR-Lite loại bỏ việc cắt do nối **toàn bộ path** vào một input, nhưng mỗi cặp Claim–Path vẫn có giới hạn riêng L, ví dụ 128 hoặc 256 token. Vì vậy vẫn phải log tỷ lệ pair bị truncate.

## 2. Cần cải tiến gì?

### 2.1. GEAR-Lite v1: kiến trúc cần code trước

GEAR-Lite v1 là một verifier mới; nó không thay relation predictor hoặc hop predictor.

| Tầng | Làm gì? | Output |
|:--|:--|:--|
| Tầng 0 — Chuẩn bị path | Giữ từng candidate path riêng, serialize entity/relation/hướng relation, padding và path mask | K path cho mỗi claim |
| Tầng 1 — Pair encoder | Shared BERT encode riêng từng cặp Claim–Path-i | K vector h-i |
| Tầng 2 — Path aggregator | Masked Mean hoặc Masked Attention tổng hợp K vector path | Một vector evidence o |
| Tầng 3 — Verifier | MLP dự đoán nhãn | True / False |

~~~text
(Claim, Path-1) -> BERT -> h1
(Claim, Path-2) -> BERT -> h2
...
(Claim, Path-K) -> BERT -> hK
                   -> masked Attention hoặc Mean
                   -> MLP -> True / False
~~~

Tầng 1 có dạng BERT-Pair-style: claim và một path tương tác trực tiếp bên trong BERT. Nhưng GEAR-Lite không phải BERT-Pair baseline thuần: BERT-Pair thường quyết định từng pair; GEAR-Lite tổng hợp cả tập path để dự đoán một nhãn claim.

Với Attention:

~~~text
score_i = Linear(h_i)
alpha = masked_softmax(score)
o = sum_i(alpha_i * h_i)
label = MLP(o)
~~~

Path padding phải có attention weight bằng 0. Attention là soft selection sau khi BERT đã đọc từng path; nó không thể cứu một path chưa được retrieval sinh ra.

### 2.2. Chưa thêm ERNet ở bản đầu

ERNet/GNN chỉ nên thử sau GEAR-Lite v1. Một path FactKG đã là một chuỗi multi-hop; nhiều path thường là các ứng viên thay thế và có thể nhiễu. Nối fully-connected tất cả path ngay từ đầu dễ lan noise.

Nếu GEAR-Lite v1 còn sai multi-hop dù path đúng đã có mặt, khi đó thử sparse ERNet: node là path, edge chỉ khi hai path chia sẻ entity hoặc nối tiếp được.

### 2.3. Retrieval audit chạy song song

Không cần sửa xong retrieval mới code GEAR-Lite. Tuy nhiên trên predicted-retrieval dev cần log:

| Metric | Ý nghĩa |
|:--|:--|
| Annotation-aligned path recall | Candidate từ relation/hop dự đoán có còn evidence relation-chain mà dev annotation chỉ ra không? |
| Proof-after-truncate rate | Evidence path đó có nằm sau mốc 512 token của Concat không? |
| Candidate count, token/path | Tăng top-K/hop đang thêm proof hay chủ yếu thêm noise? |

Dev có Evidence gold nên đo được các metric này; test không có Evidence. Train/dev candidate hiện dùng gold evidence còn test dùng retrieval dự đoán, vì vậy cần tạo predicted-retrieval dev để đo pipeline thật.

## 3. Các bước thử và code GEAR-Lite như nào?

### 3.1. So sánh E0, E1, E2

Ba model phải dùng **cùng candidate artifact**, cùng path order, cùng max_paths = K, cùng split và seed protocol. Không thêm learned selector trước BERT ở ba lượt này.

| ID | Verifier | Câu hỏi |
|:--|:--|:--|
| E0 | Concat hiện tại: tất cả path nối thành một input BERT | Baseline bị giới hạn bởi concat/token budget đến đâu? |
| E1 | Encode từng Claim–Path, rồi masked Mean | Chỉ riêng việc giữ path độc lập có giúp không? |
| E2 | Encode từng Claim–Path, rồi masked Attention + MLP | Attention có hơn Mean khi nhiều path nhiễu không? Đây là GEAR-Lite v1. |

“Không thêm selector cứng” không có nghĩa là không giới hạn số path. Vẫn phải đặt K để vừa GPU; chỉ là E0/E1/E2 dùng cùng K, chưa thêm model/rule chọn path tốt trước BERT. Khác biệt duy nhất là cách evidence được encode và aggregate.

### 3.2. Phần code cần thay đổi

1. Dataset không flatten path sớm; trả về danh sách path riêng.
2. DataCollator tạo tensor kích thước batch x K x L và path_mask.
3. Gộp batch x K cặp để BERT forward hiệu quả, rồi reshape về batch x K x hidden.
4. Thêm hai verifier:
   - IndependentPathMeanClassifier cho E1.
   - GEARLiteClassifier gồm masked attention và MLP cho E2.
5. Giữ ConcatClassifier làm E0.
6. Đóng băng candidate artifact: classifier không tự sinh lại path ở mỗi lần chạy.

Không nên viết selector, contrastive loss hay ERNet trong commit đầu tiên; nếu làm cùng lúc sẽ không biết phần nào tạo ra thay đổi score.

### 3.3. Cách diễn giải kết quả

| Kết quả | Kết luận | Bước kế tiếp |
|:--|:--|:--|
| E1 > E0, E2 xấp xỉ E1 | Tách path và tránh concat-level truncate là lợi ích chính | Giữ Mean hoặc thêm path feature nhẹ. |
| E2 > E1 rõ ràng | Attention giảm noise có ích | Giữ GEAR-Lite, sau đó thử hard negative/path feature. |
| E0/E1/E2 đều thấp, path recall thấp | Proof mất ở retrieval | Sửa relation/hop, traversal và beam search. |
| E0/E1/E2 đều thấp, path recall cao | Verifier/logic proof còn yếu | Learned selector, hard negative, sau đó sparse ERNet. |

## 4. Quy trình chạy lại

### 4.1. Chuẩn bị baseline và artifact

1. Chạy preprocess, train/eval relation predictor và hop predictor theo hướng dẫn trong implementation.md.
2. Sinh candidate path một lần cho train, predicted-retrieval dev và test; lưu file artifact có ranh giới từng path.
3. Sửa các điểm tái lập tối thiểu: seed Python/NumPy/PyTorch, không bỏ batch cuối ở dev/test, và lưu deep copy checkpoint tốt nhất.
4. Log path recall, proof-after-truncate, số candidate và token/path trên dev.

Luồng retriever hiện có:

~~~bash
cd with_evidence/retrieve/data
python data_preprocess.py --data_directory_path <DATA_DIR> --output_directory_path ../model/

cd ../model/relation_predict
python main.py --mode train --config ../config/relation_predict_top5.yaml
python main.py --mode eval --config ../config/relation_predict_top5.yaml --model_path <RELATION_CKPT>

cd ../hop_predict
python main.py --mode train --config ../config/hop_predict.yaml
python main.py --mode eval --config ../config/hop_predict.yaml --model_path <HOP_CKPT>
~~~

### 4.2. Chạy E0, E1, E2

Hiện code chỉ có ConcatClassifier. Sau khi thêm hai classifier và lựa chọn model vào CLI, quy trình mong muốn là:

~~~bash
cd with_evidence/classifier

# E0: baseline hiện tại
python baseline.py --data_path <DATA_DIR> --kg_path <KG_PATH> --model_cls cat --epoch 10

# E1: sau khi code IndependentPathMeanClassifier
python baseline.py --data_path <DATA_DIR> --kg_path <KG_PATH> --model_cls mean --epoch 10

# E2: sau khi code GEARLiteClassifier
python baseline.py --data_path <DATA_DIR> --kg_path <KG_PATH> --model_cls gearlite --epoch 10
~~~

Hai lệnh E1/E2 là **mục tiêu sau khi implement**, chưa chạy được với code hiện tại. Cả ba model phải đọc cùng artifact thay vì gọi lại bước sinh candidate trong mỗi lệnh.

### 4.3. Chọn model và báo cáo test

1. Chạy E0/E1/E2 ít nhất 3 seed trên dev; chọn cấu hình bằng dev, không chọn bằng test.
2. Sau khi chốt model, chạy test cuối và báo cáo:
   - overall accuracy và macro-F1;
   - accuracy/F1 cho one-hop, conjunction, existence, multi-hop, negation;
   - mean ± standard deviation qua seed;
   - candidate count, truncate rate, thời gian và peak GPU memory.
3. Chỉ sau đó mới thử learned selector/hard negatives; ERNet sparse là bước sau cùng.

**Kết luận:** triển khai ngay GEAR-Lite v1 = encode từng Claim–Path + masked Attention + MLP, đo công bằng với E0/E1, và dùng retrieval audit để biết nếu điểm chưa tăng thì lỗi nằm ở retrieval hay verifier.
