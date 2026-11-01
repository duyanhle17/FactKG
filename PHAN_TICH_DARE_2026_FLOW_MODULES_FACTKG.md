# DARE 2026: mô hình, luồng suy luận và khả năng kết hợp với FactKG R3 → V4

*Ghi chú nghiên cứu, 01/11/2026. Nguồn chính: Li et al., [DARE: Dialectical Agentic Reasoning for Structured Knowledge Fact Checking](https://aclanthology.org/2026.findings-emnlp.1315.pdf), Findings EMNLP 2026. Các mục “đề xuất” bên dưới là giả thuyết của chúng ta, **không phải** thành phần đã có trong DARE.*

## 1. DARE giải quyết bài toán gì?

Đầu vào là claim, các entity được liên kết với claim và KG; đầu ra là nhãn nhị phân **Supported/Refuted**. DARE nhắm ba lỗi của cách để LLM sinh một chương trình duyệt KG rồi thực thi một lượt: tên relation do LLM đề xuất có thể không có trong KG; đường suy luận đầu tiên sai thì khó sửa; và lập luận một chiều dễ thiên về bằng chứng ủng hộ. DARE thay bằng vòng **retrieve → reason → reflect**, lặp đến khi đủ phân định hoặc hết ngân sách. Đây là một *hệ thống suy luận lúc inference*, không phải ba mạng được fine-tune riêng. [Paper, §1–3](https://aclanthology.org/2026.findings-emnlp.1315.pdf).

```text
Claim + entity đã liên kết + KG
          │
          ▼
Retriever: lấy các triple kề entity → LLM lọc triple liên quan
          │
          ▼
Reasoner: cùng evidence → lập luận ủng hộ và phản bác, cho hai điểm
          │
          ▼
Controller: khoảng cách hai điểm đủ lớn?
          ├─ Có → LLM đối chiếu hai lập luận → Supported/Refuted
          └─ Chưa → thêm entity mới từ triple vừa lấy → truy xuất vòng sau
                    (tối đa 5 vòng; hết vòng vẫn phải ra nhãn)
```

**“Ba agent” là ba vai trò prompt trên cùng Qwen3-8B**, không phải ba checkpoint khác nhau. Paper gọi cấu hình là *zero-shot*: không đưa ví dụ tác vụ vào prompt và không báo fine-tune Qwen3-8B trên FactKG. Điều đó **không** có nghĩa là mô hình không cần đọc claim/triple khi test. Paper không đưa đủ mã chạy để xác nhận cách triển khai local/API, chi phí hay thời gian suy luận cụ thể. [Paper, §4.1](https://aclanthology.org/2026.findings-emnlp.1315.pdf); [repo tác giả, hiện chỉ “Coming soon”](https://github.com/inflee/DARE).

## 2. Từng module thực sự làm gì?

| Thành phần | Đầu vào | Phép xử lý paper mô tả | Đầu ra | Vai trò của LLM |
| --- | --- | --- | --- | --- |
| **Entity linking** | Claim | Xác định entity trong KG được claim nhắc đến; Algorithm 1 giả định có bước này nhưng paper không đặc tả chi tiết bộ linker. | Tập entity ban đầu `Eₛ` | Không đủ thông tin để khẳng định cách triển khai. |
| **Retriever, adjacency** | `Eₛ`, KG | Lấy **mọi** triple `(h,r,o)` mà `h` hoặc `o` là một entity trong `Eₛ`. Vòng sau thêm entity xuất hiện trong evidence đã chọn. | Láng giềng KG có relation hợp lệ | Tra cứu KG, chưa cần LLM để *sinh* tên relation. |
| **Retriever, semantic filter** | Claim, các triple kề | Qwen3-8B xếp/lọc `top-k` triple liên quan. Paper không công bố rõ `k` dùng cho kết quả chính. | `E⁽ᵗ⁾`, tập triple chọn ở vòng `t` | Prompt theo vai Retriever. |
| **Reasoner** | Claim, **hợp** evidence từ vòng 1 đến `t` | Sinh lập luận ủng hộ `α⁺`, phản bác `α⁻` và hai điểm `c⁺`, `c⁻` trong `[0,1]`. | Hai lập luận + hai điểm | Cùng backbone; paper trình bày hai góc nhìn, §4.1 nói output chung có cả hai điểm. Đừng mặc định là hai mô hình độc lập. |
| **Controller** | Lập luận/điểm tốt nhất qua các vòng | Giữ `C⁺ = max c⁺`, `C⁻ = max c⁻`; tính `Δ = |C⁺−C⁻|`. Nếu `Δ ≥ τ`, gọi adjudicator để ra nhãn; nếu chưa thì mở rộng entity và lặp. | `CONTINUE` hoặc nhãn | Prompt theo vai Controller/adjudicator, **không** phải phép `argmax(c⁺,c⁻)` thuần túy. |

Ở cấu hình chính: **`τ = 0,5`, tối đa `T = 5` vòng, temperature `0,1`, top-p `0,9`**. Khi hết 5 vòng, hệ thống vẫn gọi adjudicator với lập luận mạnh nhất để buộc ra Supported/Refuted. Không có nhãn “chưa xác định” ở đầu ra cuối. [Paper, §3, Algorithm 1, §4.1](https://aclanthology.org/2026.findings-emnlp.1315.pdf).

### Điểm dễ hiểu nhầm

- DARE **không chạy predictor relation top-5/hop rồi R3** như repo của ta. Nó xem các cạnh thật quanh entity, sau đó LLM lọc. Vì vậy nó không thể bịa một relation *trong danh sách đã truy xuất*; nhưng bộ lọc vẫn có thể **bỏ sót** cạnh quan trọng.
- DARE làm việc với **triple**; chuỗi nhiều hop hình thành qua *mở rộng entity nhiều vòng*, không phải một lần sinh toàn bộ relation sequence rồi DFS như R3.
- Hai điểm `c⁺/c⁻` là **điểm LLM tự đưa ra**, paper không trình bày phép hiệu chuẩn xác suất theo nghĩa thống kê. `Δ` lớn chưa tự chứng minh rằng evidence đã đủ cho *mọi vế* của claim. Đây là giới hạn **suy ra từ thiết kế**, không phải kết luận thực nghiệm mà paper đã chứng minh.
- Phụ lục prompt Reasoner **cho phép dựa vào kiến thức nội tại khi các triple truy xuất không liên quan**. Vì vậy quyết định cuối không nhất thiết chỉ được suy ra từ KG; muốn nói “faithful to KG” cần đánh giá riêng xem các triple được viện dẫn thực sự đủ chứng minh/bác bỏ không. [Paper, Appendix D](https://aclanthology.org/2026.findings-emnlp.1315.pdf).

## 3. Một claim đi qua hệ thống như thế nào?

Ví dụ paper: “Aaron Boogaard đến từ Canada, nơi có tiếng Pháp là một ngôn ngữ được sử dụng.”

1. Từ entity ban đầu, vòng 1 lấy và chọn triple `(Aaron_Boogaard, placeOfBirth, Canada)`. Nó làm rõ phần “đến từ Canada”, **chưa kiểm tra đủ** phần ngôn ngữ.
2. Reasoner cho `c⁺=0,55`, `c⁻=0,45`; `Δ=0,10 < 0,5`, nên Controller chưa kết luận.
3. Thêm `Canada` vào frontier. Vòng 2 truy xuất `(Canada, language, French_language)`.
4. Với evidence tích lũy, paper minh họa `c⁺=0,95`, `c⁻=0,10`, `Δ=0,85 ≥ 0,5`; adjudicator kết luận Supported.

**Điều đáng học** là *tìm tiếp khi bằng chứng hiện tại chưa phân định được*, không phải chỉ tăng số path cố định. Tuy nhiên đây là một **case study được chọn**, chưa chứng minh DARE theo dõi trạng thái riêng cho mọi vế ở mọi claim. [Paper, Table 3](https://aclanthology.org/2026.findings-emnlp.1315.pdf).

## 4. Điểm số và đóng góp của từng module

Trên **9.041 claim FactKG test**, các số dưới đây là cách chia **năm reasoning type của DARE**, không phải bảng Conjunction True/False riêng của repo ta. [Paper, Table 1–2](https://aclanthology.org/2026.findings-emnlp.1315.pdf).

| Phương pháp | One-hop | Existence | Multi-hop | Conjunction | Negation | Overall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| PGR (GPT-4o, bảng DARE) | 93,30 | 93,10 | 75,96 | **89,95** | 81,16 | 86,82 |
| **DARE (Qwen3-8B, zero-shot)** | **94,44** | **95,23** | **77,28** | 87,58 | **88,89** | **88,12** |

DARE hơn PGR **+1,30 điểm phần trăm overall**, nhưng **thua 2,37 điểm ở Conjunction**; không thể kết luận nó sửa được lỗi Conjunction của chúng ta chỉ từ overall. Bảng ablation của DARE báo: bỏ reasoning hai chiều còn **63,20%** (−24,92 điểm); bỏ Controller/phản tư còn **70,11%** (−18,01); bỏ semantic filter còn **72,21%** (−15,91). Đây là ablation **trong toàn bộ cấu hình DARE**; không được suy thẳng rằng gắn một module tương tự vào V4 sẽ tăng đúng bấy nhiêu điểm. [Paper, Table 1–2](https://aclanthology.org/2026.findings-emnlp.1315.pdf).

Theo đồ thị độ nhạy trong paper, tối đa 3/4/5/6 vòng cho **80,60/85,88/88,12/87,96%**; ngưỡng `τ` 0,3/0,4/0,5/0,6 cho **79,20/82,11/88,12/87,82%**. Các mức này là cấu hình paper thử trên FactKG; cần hỏi họ chọn trên dev hay test trước khi coi là phép chọn tham số sạch. [Paper, Figures 3–4](https://aclanthology.org/2026.findings-emnlp.1315.pdf).

**Cảnh báo về “SOTA”:** DARE gọi 88,12% là tốt nhất so với **các baseline trong bảng của họ**, không phải cao hơn mọi kết quả FactKG đã công bố: BERT one-hop của [FEVER 2026 báo 92,68%](https://aclanthology.org/2026.fever-1.3.pdf), còn [Opsahl 2024 báo 93,49%](https://aclanthology.org/2024.fever-1.32.pdf). Các pipeline và protocol có khác biệt; trước khi phát biểu ai tốt hơn tuyệt đối phải đối chiếu entity linking, KG, cách chia dữ liệu, evidence, ngân sách và chi phí. [DARE, Table 1](https://aclanthology.org/2026.findings-emnlp.1315.pdf).

## 5. Đối chiếu đúng tầng với hệ R3 → V4 của ta

| Câu hỏi | R3 → V4 hiện tại | DARE |
| --- | --- | --- |
| Relation/hop từ đâu? | Ở test, predictor sinh relation top-5 và hop; R3 dựng relation sequence rồi duyệt KG. | Tra cứu adjacency KG trước; LLM lọc các triple có relation thật. Không có predictor top-5/hop kiểu FactKG gốc. |
| Evidence biểu diễn ra sao? | Path `connected` trước `walkable`; V4 thường chỉ thấy tối đa 32 path. | Tập triple lọc, tích lũy qua nhiều vòng; không mặc định 32 path. |
| Ai quyết định nhãn? | V4 là BERT verifier đã fine-tune, mã hóa từng cặp claim–path và gộp attention. | Qwen3-8B theo vai Reasoner/Controller bằng prompt zero-shot; không dùng checkpoint V4. |
| Có tìm tiếp khi chưa chắc? | Retrieval một lượt theo relation/hop dự đoán, với giới hạn trạng thái nếu cấu hình; sau đó V4 phân loại. | Có, dựa vào confidence gap giữa lập luận ủng hộ/phản bác, tối đa 5 vòng. |
| “Không thấy path” nghĩa là gì? | V4 vẫn phải ra nhãn từ input còn lại. | Controller vẫn phải ra nhãn sau vòng cuối; prompt Reasoner cho phép dùng kiến thức nội tại. Không có trạng thái unknown cuối. |

Đối chiếu code repo: [R3 tạo relation sequences từ dự đoán test](with_evidence/classifier/preprocess.py), [V4 đọc `connected + walkable`, giới hạn `max_paths`](with_evidence/classifier/baseline.py). **Không thể chuyển trực tiếp điểm DARE sang checkpoint V4** vì cả evidence, backbone, huấn luyện và số lần suy luận đều khác.

## 6. Có thể mượn gì, và thử ra sao để thành đóng góp riêng?

**Nên mượn như baseline/module kiểm soát:** (a) lấy adjacency rồi chọn relation/triple hợp lệ trong KG, tránh relation dự đoán “có vẻ đúng” nhưng không tồn tại; (b) kiểm tra cả hướng ủng hộ và phản bác; (c) truy xuất thêm khi chứng cứ chưa đủ. Ba ý này **đã thuộc DARE**, nên chỉ ghép chúng với V4 rồi nói là phương pháp mới sẽ yếu về novelty.

**Giả thuyết đáng phát triển:** thay điều kiện dừng theo **độ chênh hai điểm của cả claim** bằng điều kiện **đủ chứng cứ cho từng vế**. Ví dụ claim `A sinh ở B và A làm nghề C`: sau khi tìm được path cho vế sinh, ngân sách tiếp theo tập trung vào vế nghề; path mới lặp lại nơi sinh không làm tăng “độ đủ”. Mỗi vế giữ `ủng hộ / bác bỏ / chưa thấy`; *chưa thấy* không tự biến thành *bác bỏ*. Sau đó verifier nhận cả evidence lẫn mặt nạ vế còn thiếu. Đây là **đề xuất của ta**; cần khảo sát thêm công trình gần giống trước khi tuyên bố mới.

Một chuỗi thực nghiệm có thể kiểm chứng, **chọn tham số trên dev, không chọn bằng test**:

1. **Cố định điều kiện so sánh.** Cùng 13.266 claim dev kiểu test, cùng KG và `Entity_set` ở inference, cùng ngân sách token/triple/path, ghi chi phí và thời gian. Giữ 9.041 test cho xác nhận cuối; các con số test cũ đã xem chỉ là tham chiếu quan sát.
2. **Truy xuất:** so predicted top-5/hop→R3; adjacency một hop→lọc lexical; adjacency→lọc LLM; và phương pháp tìm tiếp theo vế. Đo không chỉ accuracy mà cả *evidence recall/coverage* trên subset dev có gán nhãn proof, số claim bị cap, số lần mở rộng và số LLM calls.
3. **Verifier:** cùng một bộ evidence, so V4 một chiều; cặp support/refute kiểu DARE; và verifier theo từng vế. Nếu thay dữ liệu train, cần train lại verifier phù hợp, không dùng checkpoint V4 cũ như kết quả so sánh cuối; dùng checkpoint cũ chỉ cho diagnostic.
4. **Ablation nhân quả:** bỏ chọn vế, bỏ dừng theo độ đủ, bỏ nhánh phản bác, thay evidence mới bằng path trùng vế, giữ nguyên ngân sách. Báo riêng Conjunction True/False, Multi-hop, Negation, overall và faithfulness của path được viện dẫn.

**Cổng quyết định:** nếu adjacency/LLM lọc chỉ cải thiện vì tăng lượng chứng cứ hoặc tăng token, hướng method chưa mạnh; nếu chọn vế + dừng theo proof coverage tăng độ đúng **với cùng ngân sách** và giảm False→True ở Conjunction mà không phá True, đó mới là đóng góp đáng viết paper. DARE cũng có hạn chế tác giả tự nhận: adjacency toàn bộ có thể tốn ở node bậc cao; bài toán ngoài structured evidence chưa được đánh giá rộng. [Paper, Limitations](https://aclanthology.org/2026.findings-emnlp.1315.pdf).

## 7. Những gì chưa nên khẳng định khi tái lập DARE

- Repo tác giả hiện chưa có mã chạy đầy đủ; `top-k`, cách entity linking, định dạng prompt cho mọi vai, cache, batch, chi phí và số vòng thực tế theo từng claim **chưa được tái lập độc lập**. [Repo DARE](https://github.com/inflee/DARE).
- “Hai điểm tự tin” chưa phải xác suất đã hiệu chuẩn. Cần đo calibration, tỷ lệ dừng sai, và trường hợp điểm cao khi một vế vẫn chưa được kiểm tra.
- Appendix D cho phép dùng kiến thức nội tại; nếu mục tiêu của ta là *KG-grounded proof*, phải tách nhãn đúng nhờ KG khỏi nhãn đúng nhờ ký ức mô hình. [Paper, Appendix D](https://aclanthology.org/2026.findings-emnlp.1315.pdf).
- Paper ghi tổng FactKG **108.764** ở phần dataset; một số tài liệu FactKG/FEVER ghi con số khác. Khi so thực nghiệm, ưu tiên **claim ID và split thực tế** thay vì suy từ tổng được ghi trong bài. [DARE, §4.1](https://aclanthology.org/2026.findings-emnlp.1315.pdf); [FEVER 2026, §3](https://aclanthology.org/2026.fever-1.3.pdf).
