# Báo cáo ngày 29/7: Faico-Lite kết hợp với GEARLite E2

## 1. Mục tiêu và ý tưởng áp dụng

Mục tiêu của tuần này là cải thiện tập **candidate evidence path** đưa vào
GEARLite E2, đặc biệt cho các claim cần suy luận nhiều bước. Ý tưởng lấy từ
Faico là: sau khi đã có các relation liên quan, bước duyệt KG không nên làm mất
path hợp lệ chỉ vì heuristic hoặc việc chọn nhánh ngẫu nhiên.

Trong FactKG, pipeline hiện tại là:

```text
Claim + entity
→ relation predictor: top-5 relation
→ hop predictor: số hop H
→ Faico-Lite candidate retriever
→ evidence path
→ GEARLite E2 attention
→ True / False
```

Faico-Lite được đặt ở bước sinh candidate path, trước E2. Thay vì chọn một
tail ngẫu nhiên hoặc gộp các path khác nhau có cùng endpoint, retriever mới
duyệt KG theo thứ tự xác định, giữ mọi tail/path hợp lệ và chỉ bỏ các path trùng
hoàn toàn. Nhờ đó, nếu có nhiều alternative proof cho cùng một claim, E2 có cơ
hội nhìn thấy chúng và dùng attention để chọn path hữu ích hơn.

Ba cấu hình được kiểm tra là: R1 giữ path đúng độ dài hop dự đoán và không lặp
relation; R2 sinh thêm path ngắn hơn hop dự đoán; R3 cho phép một relation lặp
tối đa hai lần. Mục đích là kiểm tra lần lượt việc traversal cũ có làm mất
proof, hop predictor có dự đoán dài hơn proof thật hay không, và proof
multi-hop có cần relation lặp lại hay không.

## 2. Khác với Faico và phần ý tưởng được sử dụng

Faico gốc dùng LLM fine-tune kết hợp token-trie để sinh relation liên quan với
câu hỏi, dùng k-BET và budget dominance để truy xuất reasoning subgraph, rồi
dùng LLM để sinh câu trả lời. FactKG hiện không dùng hai LLM này; vẫn giữ
relation predictor, hop predictor và GEARLite E2 gốc.

Phần được áp dụng từ Faico là ý tưởng **structural completeness** ở tầng
retrieval: chỉ duyệt theo các relation đã chọn, kiểm soát số lần lặp relation
bằng budget `k`, và tránh làm mất path hợp lệ trong quá trình traversal. Tuy
nhiên, budget dominance hiện chỉ được audit chứ chưa dùng để cắt path, vì E2
cần encode từng serialized path riêng.

Việc chưa thay predictor bằng LLM là có chủ đích. Trước hết cần kiểm tra: với
cùng top-5 relation và cùng hop dự đoán của FactKG, candidate path cũ có đang
làm mất proof không. Vì vậy hiện chưa cần train lại phần `retrieve`; nếu
dataset, KG và checkpoint predictor không đổi thì dùng lại prediction relation
và hop đã có. Nếu R1–R3 cho thấy proof vẫn thiếu do relation/hop dự đoán sai,
bước sau mới xem xét LLM sinh relation hoặc một mô hình dự đoán hop mới.

## 3. Trạng thái và kết quả hiện tại

Candidate R1 đã tạo xong cho 86.367 claim train, 13.266 claim dev và 9.041
claim test. Retrieval report ghi nhận lần lượt 1.745.603, 251.585 và 154.200
path; toàn bộ path được lưu trong artifact, còn E2 chỉ đọc tối đa 32 path cho
mỗi claim khi train/test.

E2 với R1 đang train. Checkpoint dev tạm thời tại epoch 2 đạt Accuracy `0.9390`;
đây chưa phải kết quả test cuối cùng. Sau khi chọn checkpoint dev tốt nhất của
R1, cùng checkpoint này sẽ được dùng để test R2 và R3. Kết quả cuối sẽ so sánh
Test Accuracy, Macro-F1 và đặc biệt là Multi-hop Accuracy/Macro-F1 giữa ba run.
