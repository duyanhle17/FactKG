# Báo cáo 7/10 — từ phân tích lỗi Conjunction đến thử relation top-10

Mốc thời gian: **phần 1 đến hết 1/10; phần 2 từ 2/10 đến 6/10**. Chưa có kết quả chạy mới trong ngày 7/10. Các lệnh dưới đây ghi **script và tham số chính đã dùng**, không giả làm bản sao nguyên văn của toàn bộ terminal; đường dẫn artifact đầy đủ được giữ trên máy GPU.

## 1. Đến hết 1/10: mốc top-5 và xác định lỗi cần nghiên cứu

### Đã chạy và kiểm tra

| Lệnh/nhóm lệnh | Việc đã làm và trạng thái |
|---|---|
| `relation_predict/main.py --mode train/eval`, `hop_predict/main.py --mode train/eval` | Tạo dự đoán relation **top-5** và hop `H` cho pipeline cũ; checkpoint và JSON cũ vẫn được dùng về sau. Không có log nguyên văn đầy đủ của lần train đầu trong báo cáo này. |
| `build_faico_lite_candidates.py --n_candid 5 --include_shorter_paths --relation_budget 2 --report_max_paths 32` | Dựng R3 top-5 trên KG; lượt test gốc **9.041 claim** đã hoàn thành. R3 ở đây là thuật toán dựng candidate, **không phải model được train**. |
| `baseline.py --model_cls gearlite --max_paths 32 ...` | Train/test GEARLite V4 trên candidate R3 top-5; đã có checkpoint và prediction để audit. |
| `audit_conjunction_step_a.py --test_data ... --candidate_path ... --prediction_path ... --relation_json ... --hop_json ...` | Đối chiếu nhãn V4, số path và các ca Conjunction; đọc mẫu lỗi cụ thể. |
| `relation_predict/main.py --mode eval` và `hop_predict/main.py --mode eval` trên dev; `build_faico_lite_candidates.py --test_only_candidates --n_candid 5 ...` | Đóng gói dev như test để thử candidate từ relation/H **dự đoán**. R3 chậm gần claim **5.495/13.266** (`H=2`, sân bay ở Punjab); nhánh này **chưa tạo xong artifact**, nên phép so sánh V4 dev vàng–dự đoán chưa hoàn tất. |

Đầu vào cần hiểu đúng: ở **train/dev**, R3 lấy các *chuỗi relation* trong `Evidence` vàng để tìm path thực trong KG; ở **test**, R3 lấy relation và `H` do hai predictor dự đoán. `Evidence` không phải path cụ thể đã dựng sẵn. V4 học/đoán từ candidate path cùng nhãn claim, không đọc JSON relation trực tiếp. Faico-Lite/R3 là phần mở rộng trong repo này, không phải tên một model của [paper FactKG gốc](https://aclanthology.org/2023.acl-long.895.pdf).

### Kết quả rút ra ở mốc top-5

- R3 Full top-5 + V4 (`K=32`) đạt **84,03% Accuracy / 83,32% Macro-F1** trên **3.069 claim Conjunction test**. Mốc E0 Concat top-5 là **85,08% Accuracy**; hai hệ thống khác cả candidate lẫn classifier, không thể quy chênh lệch cho riêng R3 hoặc V4.
- V4 sai **490/3.069** câu: **387 True → False**, **103 False → True**. Trong 387 lỗi bỏ sót True, có 19 câu không có path, 60 câu không có `connected`, 172 câu chạm 32 path; các nhóm **chồng lấn**. Nhiều câu đúng cũng chạm 32 path, nên chưa thể kết luận K=32 gây lỗi.
- Các ca Agra Airport, Acura/Honda, Adare Manor, Baymax cho thấy có thể thiếu candidate, có path chỉ cho một vế nhưng V4 đoán cả câu True, hoặc đã có path liên quan nhiều vế mà V4 vẫn đoán False. Đây là dấu hiệu trên ca cụ thể, **chưa phải thống kê nguyên nhân** của cả 490 lỗi.
- Audit dev ban đầu trên **1.970 claim True có tag `multi claim` và Evidence**: top-5 chứa mọi relation vàng ở **129** câu; chứa ít nhất một chain vàng không vượt `H` ở **1.831** câu; mỗi khóa `Evidence` có một chain như vậy ở **240** câu. **818/1.970** câu có hơn năm relation vàng phân biệt nên top-5 không thể chứa hết. Khóa `Evidence` chỉ là **proxy**, chưa chắc là một vế bắt buộc của claim. Xem [báo cáo 30/9](báo%20cáo%2030_9.md).

**Câu hỏi còn lại sau giai đoạn này:** lỗi Conjunction chủ yếu do thiếu relation, R3 không dựng được path dù relation đúng, hay V4 không gộp đủ các vế? Các phép thử từ 2/10 nhằm tách ba khả năng đó.

## 2. Từ 2/10 đến 6/10: kiểm tra top-10 và thử pipeline mới

### Các lệnh đã chạy, theo thứ tự mục đích

| Lệnh/nhóm lệnh | Đầu ra hoặc trạng thái |
|---|---|
| `audit_relation_topk_conjunction.py --dev_data ... --top5_json ... --top10_json ... --hop_json ... --output_dir ...` | So relation dự đoán với Evidence dev, xuất `topk_summary.json`, `recovered_cases.md` và subset True H=1. Đây là **audit retrieval**, không train hoặc chạy V4 toàn tập. |
| `build_faico_lite_candidates.py` cho subset True, lần lượt `--n_candid 5` và `--n_candid 10`; `baseline.py --test_only --checkpoint_path <cùng V4>`; `compare_relation_topk_subset.py ...` | Dựng hai tập candidate và so dự đoán V4 trên **cùng 5 claim True**, cùng checkpoint/K=32. Xem [bảng so sánh](v4_comparison_20261005_083018.md). |
| `prepare_conjunction_false_controls.py --dev_data ... --positive_subset ... --top5_json ... --top10_json ... --hop_json ...` | Bản chọn đầu quá lỏng: **446** False đủ điều kiện. Đã sửa để entity **và** họ relation mới phải khớp **cùng một** claim True: còn **57** ca đủ điều kiện, chọn 10; không khẳng định đây là cặp chỉ khác một vế. |
| `build_faico_lite_candidates.py` cho 10 False, top-5/top-10; `baseline.py --test_only --checkpoint_path <cùng V4>`; `compare_relation_topk_subset.py ...` | Dựng candidate, kiểm tra file `.bin` và so nhãn V4 trên 10 đối chứng False. |
| `relation_predict/main.py --mode train` rồi `--mode eval --config ../config/relation_predict_top10.yaml --model_path <checkpoint mới>` | Train lại relation predictor; checkpoint `version_0/checkpoints/epoch=9-step=17350.ckpt` khoảng **1,3 GB**. Eval top-10 hoàn tất **37/37 batch**; R3 đã đọc `test_relations_top10.json`. Chưa đối chiếu độc lập toàn bộ JSON với 9.041 claim test. |
| `hop_predict/main.py --mode train --config ../config/hop_predict.yaml`; `nvidia-smi` | Train hop mới bị **CUDA OOM** đầu epoch; khi lỗi GPU còn khoảng **48,81 MiB**, các job vLLM/TTS đang chiếm nhiều VRAM. **Không có checkpoint hop mới**; lượt R3 tiếp theo dùng JSON hop cũ. |
| `build_faico_lite_candidates.py --n_candid 10 --run_name r3_top10_full_k32 --include_shorter_paths --relation_budget 2 --store_max_paths 32 --relation_prediction_path <top10 mới> --hop_prediction_path <hop cũ>`; `pgrep -af`, `ps -o pid,etime,pcpu,pmem,rss,stat,cmd -p 3372723` | Lượt **full**, không có `--test_only_candidates`: train/dev đã qua, test chậm ở khoảng **3.528/9.041**. PID dùng **99,9% một CPU**, RSS khoảng **11 GB**; lượt chạy đã dừng, **chưa có candidate test top-10 hoàn chỉnh**. |

Các dấu `...`/`<...>` trong bảng chỉ phần đường dẫn, **không phải lệnh copy để chạy lại**. Lượt train predictor mới không đồng nghĩa “train với 10 relation”: cấu hình `top_k=10` chọn mười relation điểm cao khi **eval**; mục tiêu học multi-label của predictor không đổi chỉ vì đổi top-k.

### Top-10 thực sự giúp ở đâu?

Audit trên **prediction dev của lượt trước**, không phải điểm của checkpoint vừa train, cho thấy hai JSON có cùng **13.266** claim; top-5 là prefix đúng thứ tự của top-10 ở **13.227/13.266**, còn tập relation top-5 nằm trong top-10 ở **13.266/13.266**. Trong 1.970 claim True có Evidence, **1.916** thuộc bucket Conjunction độc quyền của `baseline.py`.

| Độ phủ relation theo annotation dev | Top-5 | Top-10 | Tăng |
|---|---:|---:|---:|
| Chứa tất cả relation vàng được ghi chú | 129 | 394 | +265 |
| Có ít nhất một chain vàng, không vượt `H` | 1.831 | 1.860 | +29 |
| Mỗi khóa `Evidence` có ít nhất một chain như vậy | 240 | 502 | +262 |

“Giúp ở tầng lấy relation” nghĩa là **thêm đúng loại cạnh để R3 có cơ hội tìm path**. Ví dụ một vế cần relation `location`: nếu `location` vắng trong top-5 nhưng có ở top-10, lượt test top-5 không thể cho R3 thử cạnh đó, còn top-10 thì có thể. Điều này hữu ích nhất khi câu nhiều vế thiếu relation cho **một vế bắt buộc**; V4 chỉ có cơ hội xét vế ấy khi candidate thực sự chứa path liên quan. Nhưng top-10 **không bảo đảm** có cạnh đúng trong KG, đúng chiều/entity, không bị giới hạn bởi `H` hoặc cắt path, và cũng không bảo đảm V4 gộp các vế đúng. Vì vậy **240 → 502 là proxy độ phủ annotation, không phải tăng Accuracy 262 câu**; chỉ số “ít nhất một chain” chỉ tăng **29**, cho thấy tác động tùy cách đo.

Kiểm tra end-to-end nhỏ: trên **5 True H=1 được chọn có chủ đích**, cùng checkpoint V4/K=32, top-10 sửa **2** dự đoán False → True, **3** giữ True. Trên **10 False đối chứng** chọn từ 57 ca, cả top-5 và top-10 đều đoán False; một ca tăng từ 15 lên 32 path nhưng nhãn vẫn False. Cùng 32 path không có nghĩa nội dung path giống nhau. Đây là **tín hiệu**, không phải Accuracy toàn dev/test và không chứng minh các path mới là proof đúng.

### Điểm dừng hiện tại và kết luận được phép báo

- R3 train/dev dùng `Evidence` vàng gồm chuỗi relation để tìm KG path; **test** dùng relation/H dự đoán. Vì thế đổi test sang top-10 **không tự động làm V4 cũ học thêm path**. Muốn xem hiệu quả ở suy luận, cần candidate **test top-10 hoàn chỉnh** rồi mới nạp cùng checkpoint V4. Muốn V4 học từ phân phối candidate khác phải thiết kế thí nghiệm train mới, tách riêng khỏi phép so top-k.
- R3 top-5 từng hoàn thành trên **test gốc 9.041 claim**; lượt chẩn đoán top-5 dùng **dev giả test 13.266 claim** cũng chậm ở `H=2` gần claim 5.495. Lượt full top-10 hiện chậm ở claim test khác. Top-10 có thể tăng số nhánh duyệt, nhưng **chưa đo nguyên nhân chính xác** ở claim 3.528. `--store_max_paths 32` chỉ giới hạn path lưu, không chặn toàn bộ trạng thái duyệt. Lượt top-5 cũ trong hướng dẫn dùng `--report_max_paths 32` (chỉ thống kê); cần xem manifest để so cấu hình thực tế.
- **Đã biết:** top-10 tăng độ phủ relation theo annotation dev; trên mẫu nhỏ có 2 True được sửa và 10 False giữ nhãn. **Chưa biết:** top-10 có tăng Accuracy/Macro-F1 toàn test hay không; chưa train/test V4 mới cho top-10. Không báo 5 True/10 False thành kết quả toàn tập.
- **Việc tiếp theo:** xác nhận JSON relation top-10 và hop cũ khớp 9.041 claim, xác định claim nặng và profile R3; ưu tiên khả năng lưu tiến độ/tiếp tục trước khi chạy lại. Nếu phải cắt duyệt hoặc bỏ claim, áp dụng chính sách như nhau cho hai nhánh và báo là thí nghiệm có cắt. Để cô lập tác động top-k, xuất **cả top-5 lẫn top-10 từ cùng checkpoint relation mới**, rồi giữ nguyên hop, KG, R3, V4 và K=32. Chỉ sau đó mới thử train V4 mới hoặc K=64 như thí nghiệm riêng.

Artifact cần giữ trên máy GPU: `artifacts/faico_lite_top5/r3_full/` (mốc cũ), `artifacts/conjunction_step_b_20260928_164428/` (audit dev), `artifacts/r3_top10_v4_fresh_0710/` (checkpoint relation mới và candidate train/dev). File test `candidates_full/test_candid_paths_top10_r3_top10_full_k32.bin` **chưa được tạo hoàn chỉnh** vì R3 dừng giữa test; không chạy `baseline.py --test_only` với file đó. Các file `.bin`, `.json`, `.ckpt`, `.pth` có thể bị `.gitignore` bỏ qua; commit báo cáo không thay cho sao lưu artifact.
