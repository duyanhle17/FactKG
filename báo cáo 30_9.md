# Báo cáo 30/9 — kiểm chứng lỗi Conjunction của R3 + GEARLite V4

## 1. Mục tiêu và kết quả đã có

GEARLite V4 + R3 Full đạt **84,03% Accuracy / 83,32% Macro-F1** trên 3.069 câu Conjunction test. Mốc E0 Concat top-5 đã được kiểm chứng là **85,08% Accuracy**; hai cấu hình khác cả candidate lẫn kiến trúc, nên chưa thể quy chênh lệch 1,05 điểm phần trăm cho riêng R3 hoặc V4. Mục tiêu kiểm tra lần này là phân biệt **thiếu path trước khi vào V4** với **V4 dùng sai các path đã có**.

## 2. Đã kiểm tra gì trên test (Bước A)

Dùng prediction test của V4 seed 42 và artifact R3 Full (`K=32`) để thống kê toàn bộ Conjunction; sau đó lấy **50 câu theo nhóm lỗi/đối chứng** để đọc claim, top-5 relation, hop và các path V4 nhìn thấy.

| Nhãn thật → V4 dự đoán | Số câu | 0 path | 0 `connected` | Artifact có đúng 32 path |
|---|---:|---:|---:|---:|
| True → False | **387** | 19 | 60 | 172 |
| True → True | 971 | 1 | 9 | 495 |
| False → True | **103** | 0 | 7 | 26 |
| False → False | 1.608 | — | — | — |

Tổng cộng V4 **sai 490/3.069 câu**; lỗi True → False chiếm 387/490. Các cột `0 path`, `0 connected`, `32 path` **có thể chồng lấn**: chẳng hạn `0 path` cũng là `0 connected`. `Connected` chỉ nghĩa là path nối hai entity của claim theo quy tắc R3, **không chứng minh đủ mọi vế**. Hơn nữa, 495 câu True → True cũng có đúng 32 path, nên chưa thể nói `K=32` là nguyên nhân chính. Artifact R3 được lưu tối đa 32 path; số “không có path sau K” trong audit **không cho biết** KG ban đầu có thêm path nào bị bỏ trước lúc lưu hay không.

### Ví dụ tiêu biểu và kết luận sơ bộ

- **Thiếu đầu vào rõ ràng — test index 5168:** câu đúng về Agra Airport, India và mã `AGR` được dự đoán False; R3 tạo **0 connected + 0 walkable** dù top-5 có `faa`/`~faa`. Xác nhận được là *V4 không nhận path nào*; chưa xác định do relation, entity/literal, hướng cạnh hay dữ liệu KG.
- **Một vế có bằng chứng nhưng cả câu sai — index 2664:** câu sai về Acura/Honda và động cơ `OHV single` được dự đoán True. Candidate chỉ có `Acura → ~division → Honda`, không thấy path cho vế động cơ. Đây là dấu hiệu V4 có thể tin một vế đúng rồi bỏ qua vế còn lại; cần kiểm tra thêm trước khi kết luận cơ chế này phổ biến.
- **Path cho các vế đã xuất hiện nhưng vẫn đoán sai — index 5902:** câu đúng về Adare Manor, tiếng Irish và lãnh đạo Enda Kenny có ba connected path tương ứng, V4 vẫn đoán False. Trường hợp Baymax có path tới cả Duncan Rouleau và Steven T. Seagle (index 5374) cũng bị đoán False. Những câu này gợi ý phải kiểm tra attention/cách gộp bằng chứng, không chỉ retrieval.
- **`0 connected` có thể do không khớp biểu diễn entity — index 5742:** path đi tới literal `"Adams County, Pennsylvania"`, trong khi `Entity_set` dùng `Adams_County,_Pennsylvania`; path được xếp `walkable`. Vì vậy không được đồng nhất `0 connected` với “không có bằng chứng”.

Đây là **quan sát trên mẫu chọn có chủ đích**, chưa phải tỷ lệ nguyên nhân của toàn bộ 490 lỗi. Các cột gán nguyên nhân thủ công trong `conjunction_cases.csv` hiện còn trống; test không có Evidence vàng để tự động xác nhận proof cho từng vế.

## 3. Hai cách so sánh trên dev để tìm nguyên nhân (Bước B)

**Dev** là tập dùng kiểm tra/chọn model, khác với các claim test ở trên. Dev có `Label` và `Evidence` vàng. Hai cách sau dùng **cùng claim dev và cùng checkpoint V4 đã train**, chỉ thay cách tạo candidate; V4 **chỉ dự đoán, không học lại**.

1. **Cách A — candidate dựa trên Evidence vàng:** `factkg_dev.pickle` → R3 tạo `dev_candid_paths_r3_full.bin` (đã có từ trước) → checkpoint V4 → dự đoán dev. Candidate này đã được dùng khi chọn checkpoint V4, nhưng **chưa chạy lại như nhánh A của phép so sánh có kiểm soát**.
2. **Cách B — candidate từ retrieval dự đoán:** cùng claim dev → checkpoint relation/hop cũ dự đoán top-5 relation và `H` → R3 duyệt KG, lưu tối đa 32 path → **cùng checkpoint V4** → dự đoán dev. Nếu A đúng/B sai trên cùng câu, ưu tiên điều tra đầu vào; nếu path cho mọi vế đã có mà V4 vẫn sai, điều tra verifier. So sánh này chỉ để chẩn đoán; điểm A có thể lạc quan vì checkpoint V4 được chọn trên dev vàng.

### Trạng thái chạy đến 30/9

- **Đã xong:** chuẩn bị dev theo định dạng đầu vào test trong `artifacts/conjunction_step_b_20260928_164428/`; nạp **checkpoint relation/hop cũ** để sinh `test_relations_top5.json` và `predictions_hop.json` cho **claim dev**. Tên file relation có chữ `test` do CLI gốc đặt, nhưng nội dung lần này là dev. Không train lại predictor.
- **Chưa xong:** lệnh R3 biến hai JSON dev trên thành candidate `.bin`. Tiến trình chậm bất thường gần claim thứ 5.495, sau đó chỉ tiến thêm khoảng 1%; terminal báo ETA khoảng 7 giờ (chỉ là ước lượng). Claim được quan sát là câu về sân bay tại Punjab, Pakistan; top-5 gồm `operator`, `runwayDesignation`, `~operator`, `~location`, `runwaySurface`, `H=2`. Tiến trình dùng gần 100% một CPU và khoảng 10,3 GiB RAM ổn định, nên **đang tính chứ không đứng hẳn**. Khả năng bùng nổ nhánh duyệt KG là giả thuyết, chưa đo số nhánh để xác nhận. `--store_max_paths 32` chỉ giới hạn path lưu, không tự giới hạn mọi lượt duyệt.
- **Chưa chạy:** nạp V4 để đánh giá hai nhánh A/B trên cùng dev; vì B chưa có candidate hoàn chỉnh, hiện **chưa có kết quả so sánh A/B**. Cũng chưa train lại V4 hay thay đổi điểm test đã báo.

## 4. Việc tiếp theo

1. Kiểm tra R3 còn chạy và file `artifacts/conjunction_step_b_20260928_164428/candidates/test_candid_paths_top5_dev_predicted_r3.bin` đã xuất hiện chưa. Nếu chưa, **giữ nguyên hai JSON dev đã tạo**, không chạy lại predictor.
2. Để hoàn tất B: đo nhánh gây chậm rồi tối ưu duyệt R3 **mà không đổi thứ tự/top-32 path**, hoặc trước mắt chạy trên một mẫu Conjunction dev có kiểm soát. Không dùng điểm mẫu làm điểm dev/test chính thức, và không âm thầm bỏ claim khó khi báo kết quả toàn tập.
3. Khi có candidate dự đoán: dùng **cùng checkpoint V4** dự đoán A và B, so Accuracy theo nhãn True/False, các câu đổi từ đúng sang sai, và độ phủ Evidence của từng vế.
4. Có thể làm kiểm tra nhỏ song song trên test đã có: nạp V4 + artifact R3 cũ, xuất attention/logit cho vài câu **đủ path nhưng sai** (như index 5902, 5374). Việc này không cần chạy lại retrieval hay train; code hiện chưa có CLI xuất attention nên cần script audit riêng.

## 5. File cần giữ để tiếp tục

- Trong repo: `conjunction_audit_step_a/conjunction_cases.md`, `conjunction_cases.csv`, `conjunction_summary.json`, `with_evidence/classifier/audit_conjunction_step_a.py` và báo cáo này.
- Trên máy chạy: thư mục `artifacts/conjunction_step_b_20260928_164428/` chứa JSON dự đoán dev và dữ liệu chẩn đoán; checkpoint V4 tại `artifacts/faico_lite_top5/r3_full/predictions_hybrid_rerun/`.
- `.gitignore` đang bỏ qua `*.json`, `*.bin`, `*.pkl`, `*.pth`; **commit Markdown/CSV/code không tự mang theo** JSON chẩn đoán, candidate hay checkpoint trên máy chạy. Cần giữ riêng các artifact đó nếu ngày mai tiếp tục trên máy khác.
