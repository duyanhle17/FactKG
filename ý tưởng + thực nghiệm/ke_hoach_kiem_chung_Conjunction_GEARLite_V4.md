# Kế hoạch tìm nguyên nhân giảm điểm Conjunction của GEARLite V4

## 1. Vấn đề và những gì đã biết

Mục tiêu là tìm xem lỗi đến từ **bằng chứng đưa vào model** hay từ **cách V4 dùng bằng chứng**, rồi chỉ sửa đúng tầng gây lỗi.

| Cấu hình | Conjunction Test Acc | Lưu ý khi so sánh |
|---|---:|---|
| E0 Concat, top-5 relation | 85,08% | Kết quả local đã được kiểm chứng; checkpoint không còn, prediction theo từng câu chưa xác nhận còn hay không. |
| E2b Pair + Attention, retrieval cũ | 82,82% | Đã đổi kiến trúc so với E0. |
| R3 Full + V2 | 82,73% | Cùng candidate R3 Full với V3/V4. |
| R3 Full + V3 | 81,43% | Claim được encode riêng. |
| **R3 Full + V4** | **84,03%** | Thêm `c_set`; thấp hơn E0 **1,05 điểm phần trăm**. |

V4 đúng `2.579/3.069` câu Conjunction. Trong 490 câu sai, có **387 câu True → False** và **103 câu False → True**. Với 387 câu True → False: 19 câu không có path, 60 câu không có `connected`, 172 câu có đúng 32 path. Trong 971 câu True → True, các số tương ứng là 1, 9 và 495. Đây là **tương quan**, chưa chứng minh nguyên nhân; `connected` chỉ có nghĩa path nối hai entity của claim, không bảo đảm path chứng minh đủ các vế.

Bốn câu đã đọc cho thấy hai tình huống khác nhau:

- Claim về mã `AGR` của Agra Airport: một câu có **0 path**; câu khác chỉ có 11 path `walkable` không thể hiện mã `AGR` trong các path đã in. `faa` đã được dự đoán nhưng chưa tạo được path, cần kiểm tra relation thực tế, entity và cạnh KG.
- Claim Indian Air Force/Boeing C-17: path `Agra Airport → operator → Indian Air Force` hỗ trợ một vế; không thấy path cho vế Boeing trong ba candidate hiện có.
- Claim sai về Al Taqaddum/Fallujah/Hellenic Navy: ba `connected` đều xoay quanh Fallujah, nhưng V4 đoán True. Có thể model đang tin bằng chứng của một vế; cần xác nhận trên nhiều câu.

Các câu này có tối đa 11 path, nên **giảm `K=32` xuống 24 không giải quyết được chúng**. Chưa có cơ sở coi nhiều path là nguyên nhân chính. Không thể quy toàn bộ chênh lệch E0–V4 cho R3 vì hai cấu hình còn khác kiến trúc; để so từng câu với E0 cần prediction cũ hoặc chạy lại E0.

## 2. Kiểm chứng theo thứ tự, ít tốn thời gian trước

### Bước A — Kiểm tra lỗi đầu vào trên test, không train

Lấy mẫu có chủ đích: khoảng 20 câu **True → False có `connected`**, 10 câu **True → False không có `connected`**, 10 câu **False → True** và 10 câu **True → True** làm đối chứng. Với từng câu, lưu claim, nhãn/dự đoán, `Entity_set`, top-5 relation, hop `H`, toàn bộ candidate theo đúng thứ tự `connected` rồi `walkable`, và 32 path thực sự đi vào V4. Không kết luận chỉ từ ba path đầu.

Đánh dấu **riêng cho từng vế** của claim:

1. Relation cần thiết có trong top-5 không? Nếu có mà không ra path, kiểm tra tên/hướng relation, entity và cạnh trong KG.
2. Có path thực sự hỗ trợ vế đó không? Nó ở vị trí nào, hay nằm sau vị trí 32?
3. Nếu claim sai, candidate có đang hỗ trợ một vế nhưng thiếu/phản bác vế còn lại không?

Phân loại mỗi lỗi vào nhóm **thiếu relation**, **có relation nhưng không dựng được path**, **path bị loại sau K**, **đủ path nhưng model vẫn sai**, hoặc **chưa xác định**. Test của FactKG không có `Evidence` vàng, nên bước này cần đọc thủ công; không coi “không thấy path” là bằng chứng chắc chắn KG phủ định claim.

**Kết quả cần lưu:** số lỗi thuộc từng nhóm, kèm 5–10 ví dụ rõ nhất. Nếu đa số câu True → False thiếu ít nhất một vế, ưu tiên retrieval; nếu nhiều câu đã có bằng chứng cho mọi vế, chuyển sang Bước C.

### Bước B — Đo bằng chứng thiếu ở đâu trên dev

Hiện code sinh candidate **train/dev từ `Evidence` vàng**, còn **test từ relation/hop dự đoán**. Vì vậy dev hiện tại chưa mô phỏng đúng đầu vào test. Cần chạy **inference** relation predictor và hop predictor trên dev, rồi dùng R3 tạo một artifact `dev_predicted_R3` riêng; không ghi đè `dev_candid_paths_r3_full.bin` hiện có. CLI hiện chỉ có `--test_only`, nên cần thêm lối đánh giá dev bằng checkpoint đã lưu hoặc một script inference riêng để so hai artifact dev.

Đối chiếu `dev_predicted_R3` với `Evidence` vàng của từng claim Conjunction True:

- Tỷ lệ **tất cả relation cần thiết** của các vế có trong top-5; không chỉ đo một relation bất kỳ.
- Tỷ lệ có path ứng với **đủ các vế** trong 32 candidate, tỷ lệ không path và tỷ lệ path vàng nằm sau 32.
- Cùng checkpoint V4: đo dự đoán dev với candidate vàng và với `dev_predicted_R3`. Chỉ thay candidate, giữ claim, nhãn và trọng số model.

`Evidence` annotation là mốc tham chiếu, không nhất thiết liệt kê mọi proof thay thế trong KG. Vì vậy cần đọc mẫu những trường hợp bị đánh dấu “thiếu”. Nếu V4 đúng với candidate vàng và sai với candidate dự đoán trên cùng câu, đó là bằng chứng mạnh cho lỗi đầu vào. Đây là **phép chẩn đoán**; checkpoint V4 đã được chọn bằng dev vàng, nên không dùng chênh lệch này làm điểm test chính thức.

### Bước C — Kiểm tra cách V4 xử lý khi path đã đủ

Chỉ chọn những câu đã xác nhận có path cho mọi vế trong top-32. Khi suy luận bằng checkpoint V4, ghi **logit/độ tin cậy nhãn**, thứ tự path và `last_attention_weights`. Kiểm tra path được attention cao có bao phủ đủ vế không; sau đó thử che từng path hỗ trợ một vế và quan sát dự đoán thay đổi. Attention cao một mình **không chứng minh** model đã suy luận theo path đó.

V4 tính `score_i = MLP([c_claim; c_set; h_i])`, rồi lấy tổng có trọng số `o = Σ α_i h_i` để phân loại. `c_set` là trung bình candidate, **không kiểm tra tường minh phép AND** giữa các vế. Nếu các câu False → True thường chỉ có bằng chứng cho một vế, hoặc các câu True → False đã đủ path nhưng model vẫn bỏ qua một vế, đây là lý do để thử cách gộp evidence theo từng vế. Đồng thời kiểm tra giới hạn `pair_max_length=128` có cắt mất relation/entity quyết định ở từng Claim–Path pair không.

## 3. Cách khắc phục sau khi có bằng chứng

| Nút thắt được xác nhận | Thay đổi nhỏ nhất nên thử | Phép so sánh cần giữ cố định |
|---|---|---|
| Relation cho một vế rơi khỏi top-5 | Dự đoán relation theo từng vế hoặc chọn top-5 có độ phủ relation/entity tốt hơn. | Giữ KG, R3 và V4; đo coverage đủ vế trước, rồi accuracy. |
| Relation có nhưng không ra path | Kiểm tra alias/chuẩn hóa entity, chiều relation `~r`, cạnh KG và quy tắc duyệt R3. | Giữ cùng top-5/H, so path trước và sau sửa. |
| Path đúng có nhưng nằm sau vị trí 32 | Xếp path đa dạng theo vế, relation và endpoint trước khi lấy 32; chỉ thử K lớn hơn nếu artifact còn lưu path phía sau. | Đo proof recall@32; train lại nếu đổi K/candidate cho cấu hình cuối. |
| Path cho mọi vế đã có, model vẫn sai | Thử bộ gộp theo từng vế hoặc thêm hard negative “một vế đúng, một vế sai”. | Giữ cùng candidate R3, seed và điều kiện train; so với V4. |

Không bắt đầu bằng ERNet: message passing không thể tạo lại relation/path đã thiếu. Cũng không dùng checkpoint train với `K=32` rồi test `K=24` để kết luận cấu hình K=24 tốt hơn; đó chỉ là phép thử độ nhạy đầu vào.

## 4. Điều kiện kết luận và thứ tự chạy

1. **Ngay bây giờ:** Bước A bằng artifact/prediction có sẵn; không cần GPU hoặc train lại.
2. **Sau khi thấy nhóm lỗi chính:** Bước B bằng inference retrieval trên dev và checkpoint V4 cũ; cần bổ sung đường sinh candidate dev dự đoán trong code, chưa cần train V4.
3. **Chỉ với mẫu đủ proof mà V4 vẫn sai:** Bước C và một ablation cách gộp; lúc này mới train model mới.
4. **Báo cáo cuối:** Conjunction Acc/Macro-F1, tách True/False, số path/proof đủ vế, cùng Overall và bốn nhóm reasoning còn lại. Chọn cấu hình theo dev, rồi báo cáo test; nếu kết quả mới sát ngưỡng, xác nhận thêm seed. Muốn quy chính xác phần giảm so với E0 cho từng claim thì cần prediction E0 cũ hoặc tái chạy E0.

Điểm quyết định: **thiếu proof trước V4 thì sửa retrieval; proof đã đủ mà vẫn sai thì sửa cách gộp và huấn luyện verifier**. Chưa có lý do thực nghiệm để chỉnh K hay thêm ERNet trước hai phép kiểm tra này.
