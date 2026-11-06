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

### 2.1.1. Pair + Mean hoạt động như nào?

Mean ở đây không phải chọn path tốt nhất. Mean chỉ là cách gom các vector path sau khi BERT đã encode từng path.

~~~text
Claim + Path-1 -> BERT -> h1
Claim + Path-2 -> BERT -> h2
Claim + Path-3 -> BERT -> h3
...
Claim + Path-K -> BERT -> hK
~~~

Mỗi `h_i` là một vector, không phải một điểm số đơn lẻ. Có thể hiểu `h_i` là biểu diễn của câu hỏi: "path_i giúp kiểm chứng claim này như thế nào?".

Với Mean:

~~~text
o = mean(h1, h2, ..., hK)
label = MLP(o)
~~~

`o` cũng là một vector. Nó là vector evidence chung của cả tập path. Vì Mean chia đều vai trò cho các path, nó không học path nào quan trọng hơn path nào. E1 dùng Mean để kiểm tra riêng giả thuyết: chỉ cần tách path khỏi concat dài thì có cải thiện không?

### 2.1.2. MLP, logits và softmax là gì?

Sau khi có vector evidence `o`, model cần biến nó thành nhãn `True/False`. Bước đó do MLP làm.

MLP là một classifier nhỏ, thường gồm vài lớp Linear/ReLU/Dropout. Nó nhận vector `o` và trả ra hai số thô:

~~~text
logits = MLP(o) = [score_False, score_True]
~~~

`logits` chưa phải xác suất. Nó chỉ là raw score. Ví dụ:

~~~text
logits = [1.2, 3.8]
~~~

Score thứ hai cao hơn nên model nghiêng về nhãn thứ hai. Nếu đưa qua softmax:

~~~text
prob = softmax(logits)
~~~

thì hai score được đổi thành xác suất, ví dụ gần như:

~~~text
prob = [0.07, 0.93]
~~~

Khi train bằng `CrossEntropyLoss`, PyTorch tự xử lý log-softmax bên trong loss. Khi predict, chỉ cần lấy nhãn có logit lớn nhất:

~~~text
prediction = argmax(logits)
~~~

### 2.1.3. Pair + Attention, tức GEAR-Lite v1

Attention khác Mean ở chỗ nó học trọng số cho từng path. Path quan trọng được weight cao hơn, path nhiễu được weight thấp hơn.

Với Attention:

~~~text
score_i = Linear(h_i)
alpha = masked_softmax(score)
o = sum_i(alpha_i * h_i)
label = MLP(o)
~~~

Path padding phải có attention weight bằng 0. Attention là soft selection sau khi BERT đã đọc từng path; nó không thể cứu một path chưa được retrieval sinh ra.

Vì vậy:

~~~text
E1 = Pair encoder + Mean + MLP
E2 = Pair encoder + Attention + MLP = GEAR-Lite v1
~~~

E1 và E2 có thể dùng chung phần Dataset, Collator và BERT pair encoder. Khác nhau ở tầng aggregator: E1 dùng Mean, E2 dùng Attention. Khi thí nghiệm, vẫn nên chạy thành hai lượt riêng để biết Attention có thật sự hơn Mean hay không.

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

Code hiện đã có đủ `cat` (E0), `mean` (E1) và `gearlite` (E2). Chạy từ thư mục `with_evidence/classifier`.

Đầu tiên chỉ sinh candidate artifact **một lần**. Ví dụ dưới đây dùng relation top-5:

~~~bash
cd with_evidence/classifier
python baseline.py --data_path <DATA_DIR> --kg_path <KG_PATH> --n_candid 5 --prepare_only
~~~

Sau đó mọi model và mọi seed phải thêm `--skip_prepare_input` để không sinh lại candidate. `--n_candid 5` chọn artifact `test_candid_paths_top5.bin`, còn `--max_paths 32` là số path tối đa đi vào classifier; hai tham số này không phải một.

~~~bash
# E0: chạy lại baseline trên đúng cùng K để so sánh công bằng
python baseline.py --data_path <DATA_DIR> --model_cls cat --n_candid 5 --max_paths 32 --batch_size 32 --epoch 10 --seed 42 --skip_prepare_input

# E1: Pair + masked Mean
python baseline.py --data_path <DATA_DIR> --model_cls mean --n_candid 5 --max_paths 32 --pair_batch_size 1 --pair_max_length 128 --epoch 10 --seed 42 --skip_prepare_input

# E2: Pair + masked Attention = GEAR-Lite v1
python baseline.py --data_path <DATA_DIR> --model_cls gearlite --n_candid 5 --max_paths 32 --pair_batch_size 1 --pair_max_length 128 --epoch 10 --seed 42 --skip_prepare_input
~~~

Với pair batch 1, code tự dùng gradient accumulation để effective claim batch xấp xỉ batch 32 của E0. Nếu GPU đủ bộ nhớ có thể tăng `--pair_batch_size`; code sẽ tự giảm số bước accumulation tương ứng. `--max_paths 0` giữ toàn bộ path giống baseline cũ nhưng có nguy cơ hết GPU. Nếu điểm E0 trước đây được đo với toàn bộ path thì đó chỉ là kết quả lịch sử; để ablation sạch cần chạy lại E0 với cùng `K=32` như E1/E2.

Mỗi lượt tự chọn checkpoint tốt nhất theo dev accuracy, rồi báo cáo test accuracy và macro-F1 cho đủ năm loại reasoning. Prediction được lưu riêng theo model/seed, ví dụ `test_pred_mean_seed42.bin` và `test_pred_gearlite_seed42.bin`.

Lưu ý phương pháp: `prepare_input` hiện vẫn tạo train/dev candidate từ gold `Evidence`, còn test candidate từ relation/hop prediction. Vì vậy phần đã code là ablation verifier E0–E2; predicted-retrieval dev và path-recall audit ở mục 2.3 vẫn là bước riêng chưa được triển khai.

### 4.3. Chọn model và báo cáo test

1. Chạy E0/E1/E2 ít nhất 3 seed trên dev; chọn cấu hình bằng dev, không chọn bằng test.
2. Sau khi chốt model, chạy test cuối và báo cáo:
   - overall accuracy và macro-F1;
   - accuracy/F1 cho one-hop, conjunction, existence, multi-hop, negation;
   - mean ± standard deviation qua seed;
   - candidate count, truncate rate, thời gian và peak GPU memory.
3. Chỉ sau đó mới thử learned selector/hard negatives; ERNet sparse là bước sau cùng.

**Kết luận:** triển khai ngay GEAR-Lite v1 = encode từng Claim–Path + masked Attention + MLP, đo công bằng với E0/E1, và dùng retrieval audit để biết nếu điểm chưa tăng thì lỗi nằm ở retrieval hay verifier.
