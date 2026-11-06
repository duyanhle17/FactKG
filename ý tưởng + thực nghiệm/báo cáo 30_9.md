# Báo cáo 30/9 — tìm nguyên nhân giảm điểm Conjunction

## 1. Kết quả đã kiểm chứng trên test

R3 Full + GEARLite V4 đạt **84,03% Accuracy / 83,32% Macro-F1** trên 3.069 câu Conjunction. Mốc E0 Concat top-5 là **85,08% Accuracy**. Hai bản khác cả candidate và kiến trúc, nên chênh lệch 1,05 điểm phần trăm **chưa thể quy cho riêng R3 hay V4**.

Đã đối chiếu prediction test của checkpoint V4 seed 42 với candidate artifact R3 (`K=32`) trên toàn bộ Conjunction, rồi lấy **50 câu có chủ đích** để đọc path cụ thể:

| Nhãn thật → V4 đoán | Số câu | 0 path | 0 `connected` | Đúng 32 path trong artifact |
|---|---:|---:|---:|---:|
| True → False | **387** | 19 | 60 | 172 |
| False → True | **103** | 0 | 7 | 26 |
| True → True | 971 | 1 | 9 | 495 |
| False → False | 1.608 | Chưa thống kê | Chưa thống kê | Chưa thống kê |

V4 sai **490/3.069 câu**, trong đó 387 lỗi là bỏ sót claim True. Các cột `0 path`, `0 connected`, `32 path` **chồng lấn**, không được cộng thành số nguyên nhân. `Connected` chỉ là path nối hai entity của claim, chưa chắc chứng minh đủ các vế. Đúng 32 path cũng xuất hiện ở 495 câu True → True, nên **chưa có bằng chứng rằng K=32 tự nó gây giảm điểm**. Artifact đã bị giới hạn khi lưu ở 32 path; không thể dùng nó để khẳng định KG không có path phía sau.

Các ví dụ trong `conjunction_audit_step_a/conjunction_cases.md` gợi ý **ít nhất hai dạng lỗi**:

- **Thiếu bằng chứng trước V4:** claim đúng về Agra Airport–India–mã `AGR` (index 5168) có **0 path**, V4 đoán False. Top-5 đã có `faa`/`~faa`, nên vẫn phải kiểm tra entity/literal, chiều cạnh và KG; chưa thể đổ lỗi riêng cho predictor.
- **Chỉ một vế có path nhưng V4 đoán cả câu True:** claim sai về Acura/Honda và động cơ `OHV single` (index 2664) chỉ có path Acura–Honda. Đây là dấu hiệu cần kiểm tra khả năng V4 không yêu cầu đủ mọi vế.
- **Path cho các vế đã xuất hiện nhưng V4 vẫn đoán False:** claim Adare Manor–Irish–Enda Kenny (index 5902) có ba path tương ứng; claim Baymax–hai người sáng tạo (index 5374) cũng có path tới cả hai người. Điều này gợi ý cần kiểm tra cách V4 gộp path, không chỉ sửa retrieval.
- **`0 connected` không đồng nghĩa không có path liên quan:** ở index 5742, KG dùng literal `"Adams County, Pennsylvania"` còn `Entity_set` dùng `Adams_County,_Pennsylvania`, khiến path bị xếp `walkable`.

Đây là **ví dụ và tương quan**, chưa phải thống kê nguyên nhân trên cả 490 lỗi. Các cột gán nguyên nhân thủ công trong CSV vẫn chưa được điền; test không có Evidence vàng để tự xác nhận proof của từng vế.

## 2. Phép so sánh A/B dự kiến trên dev và điểm bị ngưng

Dev là tập claim khác test và có `Label`, `Evidence` vàng. Mục tiêu là giữ **cùng claim dev, cùng checkpoint V4 đã train**, chỉ đổi nguồn candidate; V4 **không học lại**:

1. **A — candidate từ Evidence vàng:** `factkg_dev.pickle` → R3 → `dev_candid_paths_r3_full.bin` đã có → V4 dự đoán. Artifact này đã dùng khi chọn checkpoint V4, nhưng chưa chạy lại như nhánh A của phép so sánh có kiểm soát.
2. **B — candidate từ retrieval dự đoán:** cùng claim dev → checkpoint relation/hop cũ sinh top-5 relation và `H` → R3 tìm path KG → cùng V4 dự đoán. Nếu A đúng/B sai trên cùng câu, nghiêng về thiếu bằng chứng đầu vào; nếu đủ path mà V4 vẫn sai, nghiêng về verifier. Đây là **chẩn đoán**, không phải điểm test mới; A có thể lạc quan vì V4 đã được chọn bằng dev vàng.

**Đã hoàn thành:** tạo dev ở định dạng đầu vào test và dùng checkpoint predictor cũ để sinh hai JSON dự đoán dev: `test_relations_top5.json`, `predictions_hop.json` trong `artifacts/conjunction_step_b_20260928_164428/`. Tên JSON có chữ `test` do CLI gốc, nhưng nội dung là **dev**. Không train lại predictor.

**Chưa hoàn thành:** R3 dựng candidate dự đoán cho toàn dev chạy quá chậm gần claim thứ 5.495, sau đó chỉ tiến thêm khoảng 1%; terminal từng ước tính ~7 giờ. Tiến trình dùng gần 100% một CPU, RAM ổn định ~10,3 GiB: có tính toán, không phải treo hẳn. Claim được quan sát là câu về sân bay ở Punjab, Pakistan, với `H=2` và các relation `operator`, `runwayDesignation`, `~operator`, `~location`, `runwaySurface`. Nghi ngờ bùng nổ nhánh KG **chưa được đo xác nhận**. `--store_max_paths 32` giới hạn số path lưu, không chặn toàn bộ lượt duyệt. Do B chưa có artifact hoàn chỉnh, **chưa chạy A/B qua V4 và chưa có kết quả so sánh**.

## 3. Kiểm tra nhẹ đã làm hôm nay, không cần chạy R3

Dùng hai JSON dự đoán dev vừa có đối chiếu với Evidence vàng của **1.970 câu Conjunction True**. Kết quả:

| Điều kiện đo | Số câu |
|---|---:|
| Tất cả relation được annotate đều nằm trong top-5 | 129/1.970 (6,5%) |
| Có hơn 5 relation vàng phân biệt | 818/1.970 (41,5%) |
| Ít nhất **một** chain vàng nằm trong top-5 và không vượt `H` | 1.831/1.970 (92,9%) |
| Mỗi khóa `Evidence` có ít nhất một chain như vậy | 240/1.970 (12,2%) |
| Mọi chain được annotate dài **một cạnh** | 1.970/1.970 |
| Claim thiếu JSON dự đoán | 0 |

**Diễn giải đúng:** `129/1.970` là phép đo quá chặt nếu một claim có nhiều proof/quan hệ thay thế; riêng 818 câu có hơn 5 relation vàng thì top-5 không thể chứa hết. Predictor thường lấy được **ít nhất một chain**, nhưng chưa rõ có phủ đủ *các vế bắt buộc* của Conjunction không. `240/1.970` chỉ là **proxy theo khóa Evidence**, không được gọi là proof recall: một khóa có thể là cách annotate/đường thay thế, chưa xác nhận tương ứng đúng một vế. Vì mọi chain được ghi chú đều dài một cạnh, kết quả `H` đủ cho chúng không chứng minh hop predictor tốt với multi-hop; Conjunction ở đây chủ yếu đòi **kết hợp nhiều sự kiện một cạnh**.

## 4. Các nghi ngờ và cách kiểm chứng tiếp

1. **Độ phủ relation giữa các vế có thể thiếu.** Nếu relation bắt buộc không ở top-5, R3 không thể dựng path của vế ấy. Cần đọc khoảng 20 câu dev kiểu “có một chain khớp nhưng không khớp mọi khóa Evidence”, xác định khóa nào là vế bắt buộc và khóa nào chỉ là proof thay thế. Sau đó mới cân nhắc chọn relation theo từng vế, tăng/đa dạng hóa top-5 hoặc thay đổi predictor. Code hiện train predictor với `Claim + một entity` từ Evidence, còn lúc suy luận test-like dùng `Claim + Entity_set`; đây cũng là **khả năng lệch đầu vào cần kiểm tra**, chưa phải nguyên nhân đã chứng minh.
2. **R3/path construction vẫn có thể lỗi độc lập:** relation đúng có thể không ra path do alias/literal, hướng cạnh, thiếu edge KG hoặc thứ tự cắt top-32. Trước mắt đo nhánh gây chậm; nếu tối ưu R3, phải giữ nguyên candidate và thứ tự top-32 trên mẫu đối chứng. Có thể chạy một mẫu dev nhỏ để chẩn đoán, nhưng không báo điểm mẫu như điểm toàn tập.
3. **V4 có thể gộp sai dù path đã đủ:** trên các câu test như index 5902/5374, nạp checkpoint và artifact cũ, xuất attention/logit và thử che từng path. Attention cao một mình không chứng minh suy luận nhân quả; cần quan sát dự đoán đổi ra sao khi bỏ path của một vế. Bước này không cần chạy lại R3 hay train V4, nhưng cần script audit vì CLI hiện chưa xuất attention.

**Kết luận hiện tại:** có cơ sở nghi ngờ đồng thời **thiếu độ phủ relation/path** và **cách V4 gộp nhiều vế**; chưa đủ bằng chứng khẳng định nguyên nhân chính là train predictor, R3 hay V4. Chưa nên chuyển sang ERNet hoặc train lại model trước khi tách ba tầng lỗi trên.

## 5. Giữ lại để tiếp tục và commit

- Trong repo: báo cáo này, `conjunction_audit_step_a/conjunction_cases.md`, `.csv`, `conjunction_summary.json` và `with_evidence/classifier/audit_conjunction_step_a.py`.
- Trên máy GPU: hai JSON dev tại `artifacts/conjunction_step_b_20260928_164428/`, artifact R3 Full cũ và checkpoint V4 trong `artifacts/faico_lite_top5/r3_full/`.
- `.gitignore` bỏ qua `*.json`, `*.bin`, `*.pkl`, `*.pth`: commit Markdown/CSV/code **không tự mang theo** JSON, candidate hay checkpoint. Giữ riêng các artifact nếu chuyển máy; không cần chạy lại predictor chỉ vì lệnh R3 chưa hoàn tất.
