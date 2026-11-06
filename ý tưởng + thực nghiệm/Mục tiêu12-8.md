# Mục tiêu 12/8: LLM fine-tune và token-trie cho relation retrieval

## 1. Mục tiêu

FactKG hiện dùng BERT để chấm điểm 1.044 relation trong schema, sau đó lấy 5 relation có logit cao nhất. R3 dùng 5 relation này để dựng các path trong KG; E2 dùng Attention để kiểm chứng claim.

Vấn đề là nếu relation cần thiết không nằm trong top-5 thì R3 không thể tạo proof path đúng, dù KG có chứa proof đó. Mục tiêu của hướng mới là cải thiện tầng chọn relation, nhưng vẫn giữ R3 và E2 để so sánh công bằng.

## 2. Vai trò của hai thành phần

### LLM fine-tune

LLM nhận claim và entity của claim, sau đó học cách dự đoán những relation có khả năng giải thích claim.

LLM được fine-tune từ các cặp dữ liệu:

```text
Input:  claim + entity
Target: tập relation đúng lấy từ Evidence của FactKG
```

LLM chịu trách nhiệm về hiểu ngữ nghĩa. Ví dụ, từ claim nói về nơi sinh của một người, model cần đánh giá relation `birthPlace` cao hơn `spouse`.

Faico dùng LoRA để fine-tune một LLM tổng quát. Bản PDF không nêu rõ một backbone relation-generator cố định và số tham số của nó; Qwen-Plus được nêu ở vai trò reasoning LLM sinh câu trả lời cuối. Vì vậy, với FactKG nên bắt đầu bằng một LLM open-weight khoảng 1.5B–3B tham số và QLoRA.

### Token-trie

Token-trie không tự hiểu claim và không tự chứng minh relation đúng. Nó là bộ ràng buộc đầu ra:

- Trie được xây từ toàn bộ 1.044 relation hợp lệ của FactKG.
- Ở mỗi bước sinh token, các token không thể tạo thành relation hợp lệ sẽ bị khóa.
- Model chỉ được hoàn thành những chuỗi như `birthPlace`, `spouse` hoặc `~range` có trong schema.

Do đó:

```text
LLM fine-tune  → chọn relation phù hợp về ngữ nghĩa
Token-trie     → bảo đảm relation sinh ra hợp lệ về schema
R3             → kiểm tra relation có tạo được path thật trong KG
```

Token-trie không bảo đảm relation phù hợp với claim. Nếu LLM đánh giá sai, trie vẫn cho phép relation sai nhưng hợp lệ trong schema. Vì vậy cần đo riêng `Relation Recall@5` trước khi kết luận phương pháp có ích.

## 3. Flow dự kiến

```text
(1) FactKG train data
    Claim + Entity + Evidence relation
        ↓
(2) Chuẩn hóa nhãn
    relation canonical, gồm cả relation ngược như ~relation
        ↓
(3) Fine-tune LLM bằng LoRA/QLoRA
    học Claim + Entity → relation set
        ↓
(4) Xây token-trie
    trie chứa đúng 1.044 relation của FactKG
        ↓
(5) Inference trên claim mới
    LLM sinh relation, trie chặn relation ngoài schema
    giữ 5 relation có điểm hoàn chỉnh cao nhất
        ↓
(6) R3
    dùng top-5 relation và hop H để dựng path thật
    ưu tiên connected, giữ tối đa K=32 path
        ↓
(7) E2 GEAR-Lite
    encode từng Claim–Path và Attention tổng hợp
    dự đoán True/False
```

Phần thay đổi chính là bước (3)–(5). Hop predictor, R3 và E2 được giữ nguyên trong thí nghiệm đầu tiên để biết điểm tăng có thực sự đến từ relation retrieval hay không.

## 4. Ví dụ cụ thể

Giả sử claim là:

```text
Barack Obama was born in Honolulu.
Entity: Barack Obama
```

Evidence trong train cho biết relation đúng là `birthPlace`.

### Khi train

```text
Input:  Barack Obama was born in Honolulu [SEP] Barack Obama
Target: birthPlace
```

LLM được cập nhật bằng LoRA để tăng xác suất sinh `birthPlace`. Nếu một mẫu có nhiều relation đúng, target là một tập relation đã được chuẩn hóa.

### Khi dự đoán

LLM tạo điểm cho các relation. Token-trie chỉ cho phép các nhãn tồn tại trong schema. Kết quả có thể là:

```text
birthPlace: 0.82
occupation: 0.20
spouse: 0.07
~range: 0.03
...
```

Giữ 5 relation cao nhất, ví dụ:

```text
[birthPlace, occupation, spouse, ~range, nationality]
```

R3 không hỏi LLM lại ở entity trung gian. Nó dùng tập relation này để duyệt KG. Nếu `birthPlace` tạo được edge từ Barack Obama tới Honolulu, path đó được đưa vào candidate set. E2 sau đó encode riêng path và học đặt Attention cao cho path hỗ trợ claim.

## 5. So sánh thực nghiệm

Giữ nguyên cùng R3, `H`, `K=32` và E2:

```text
A. BERT top-5 → R3 → E2
B. LLM + token-trie top-5 → R3 → E2
```

Trên dev cần đo:

- Relation Recall@5: relation vàng có nằm trong top-5 không.
- Gold/path recall@32: proof path có vào candidate set không.
- Multi-hop Accuracy và Macro-F1.
- Số path trung bình và thời gian inference.

Chỉ chọn ngưỡng/beam bằng dev; sau đó chạy test một lần. Nếu Recall@5 của BERT đã cao nhưng path recall thấp, nên ưu tiên R3. Nếu Recall@5 thấp, LLM relation generator mới là hướng có cơ sở.

## 6. Phần cứng và thời gian dự kiến

Faico báo cáo toàn bộ thực nghiệm trên server 10 GPU NVIDIA A100, 1 TB RAM và 128 CPU cores. FactKG không cần hạ tầng lớn như vậy cho bước thử nghiệm ban đầu.

Khuyến nghị thực tế:

| Cấu hình | Khả năng |
|---|---|
| 24 GB VRAM | Phù hợp nhất để thử LLM 1.5B–3B bằng QLoRA, micro-batch 1, gradient accumulation |
| 32 GB VRAM | Thoải mái hơn cho model 3B, context 512–1024 và beam nhỏ |
| 7B | Có thể thử với QLoRA nhưng 24 GB khá sát; 32 GB cần tối ưu mạnh, 48 GB an toàn hơn |

Token-trie chỉ chiếm ít RAM/CPU. Phần tốn tài nguyên là LLM fine-tune và sinh relation autoregressive.

Ước lượng cho một lần thử, với dữ liệu FactKG và model 1.5B–3B:

- Chuẩn hóa nhãn và xây trie: khoảng vài chục phút đến vài giờ.
- Fine-tune QLoRA: khoảng 3–12 giờ cho vài epoch trên một GPU 24–32 GB, tùy số mẫu, độ dài input và batch thực tế.
- Sinh relation cho dev/test và tạo artifact R3: khoảng vài chục phút đến vài giờ.

Đây là ước lượng lập kế hoạch, không phải thời gian cố định. Cần chạy thử một phần dữ liệu trước để đo tốc độ thực tế; context length, số beam và số claim ảnh hưởng trực tiếp đến thời gian.

## 7. Kết luận triển khai

Bước an toàn nhất là chưa thay toàn bộ pipeline. Trước tiên tạo bản LLM + token-trie chỉ để sinh top-5 relation, sau đó đưa chính top-5 đó vào R3 và E2 hiện tại. Nếu `Relation Recall@5`, `gold path recall@32` và `Multi-hop F1` cùng tăng, khi đó mới có cơ sở kết luận Faico-style relation retrieval phù hợp với FactKG.



LLM fine-tune
   ↓
LLM sinh relation cho train/dev/test
   ↓
Chạy build R3 cho cả ba tập
   ↓
Tạo:tư
  llm_train_candidates.bin
  llm_dev_candidates.bin
  llm_test_candidates.bin
   ↓
Train E2 mới trên llm_train_candidates.bin
   ↓
Chọn checkpoint tốt nhất bằng llm_dev_candidates.bin
   ↓
Test trên llm_test_candidates.bin