# Báo cáo 7/10 — kiểm tra Conjunction và thử relation top-10 (tính đến 6/10)

## Kết luận ngắn

**Top-10 cải thiện độ phủ relation trên dev và có tín hiệu tốt ở một mẫu True nhỏ, nhưng chưa có điểm V4 toàn test cho top-10.** Lượt R3 top-10 full đã dựng xong candidate train/dev, song phần test chậm ở khoảng 3.528/9.041 claim và đã được dừng. Không được báo rằng top-10 đã tăng Accuracy, V4 mới đã train xong, hoặc R3 test top-10 đã hoàn tất.

## 1. Flow đúng và phạm vi các phép kiểm tra

Flow của lần thử là: **preprocess dữ liệu → train/eval relation predictor → train/eval hoặc dùng lại hop predictor → R3 dựng path candidate trên KG → V4 học hoặc dự đoán từ các path đó**. R3/Faico-Lite là phần mở rộng trong repo này, **không phải một model được train hay tên bước trong paper FactKG gốc**. [Paper FactKG](https://aclanthology.org/2023.acl-long.895.pdf) và [mã baseline gốc](https://github.com/jiho283/FactKG/blob/main/with_evidence/classifier/preprocess.py) mô tả việc dùng relation/hop để truy xuất đồ thị.

Trong code hiện tại, **train/dev** dùng `Evidence` vàng gồm *các chuỗi relation theo entity* để R3 tìm path cụ thể trong KG; `Evidence` không phải file path cụ thể đã dựng sẵn. **Test** không có các chuỗi vàng nên R3 dùng relation và `H` **dự đoán**. Đổi top-5 thành top-10 vì vậy tác động trực tiếp đến **candidate test**, không tự động làm candidate train/dev hoặc V4 đã train trước đó học thêm path. Cấu hình `top_k` của relation predictor chọn số relation tại bước `eval`, không thay mục tiêu học của model.

Phân biệt ba loại số liệu trong báo cáo: **độ phủ relation theo annotation** ≠ **path thật R3 tìm được** ≠ **độ chính xác nhãn của V4**. Các mẫu dev dùng nhãn/Evidence để chọn ca chẩn đoán; dữ liệu test-style đưa vào R3/V4 đã bỏ `Evidence`.

## 2. Mốc top-5 và lỗi Conjunction ban đầu (đến 30/9)

- R3 Full top-5 + GEARLite V4, `K=32`, đạt **84,03% Accuracy / 83,32% Macro-F1** trên **3.069 claim Conjunction test**. Mốc E0 Concat top-5 đạt **85,08% Accuracy**. Hai hệ thống khác cả retriever và classifier, nên chênh lệch 1,05 điểm phần trăm **không chứng minh riêng R3 hay V4 kém hơn**.
- V4 sai **490/3.069** câu: **387 True → False** và **103 False → True**. Trong 387 lỗi bỏ sót True có 19 câu không có path, 60 câu không có `connected`, 172 câu chạm 32 path; các nhóm này chồng lấn. Nhiều câu đúng cũng chạm 32 path, nên chưa thể quy K=32 là nguyên nhân.
- Đọc các ca cụ thể cho thấy cả ba khả năng: thiếu path đầu vào (Agra Airport); có path cho một vế nhưng cả câu False bị đoán True (Acura/Honda); hoặc đã có path liên quan nhiều vế mà V4 vẫn đoán False (Adare Manor, Baymax). Đây là dấu hiệu để điều tra, **chưa phải thống kê nguyên nhân trên cả 490 lỗi**. Xem [báo cáo 30/9](báo%20cáo%2030_9.md).

## 3. Audit relation top-5 so với top-10 trên dev (3–5/10)

Đây là audit trên **prediction dev của lượt trước**, chưa phải đánh giá predictor mới train ngày 5/10. Trong **1.970 claim dev nhãn True có tag `multi claim` và Evidence**, có **1.916 claim** thuộc bucket Conjunction độc quyền của `baseline.py`; không được lấy mẫu số 1.970 làm Accuracy Conjunction. Hai JSON dự đoán có cùng 13.266 claim: top-5 là đúng prefix top-10 ở **13.227/13.266**, và tập relation top-5 nằm trong top-10 ở **13.266/13.266**.

| Chỉ số độ phủ annotation | Top-5 | Top-10 | Tăng |
|---|---:|---:|---:|
| Chứa tất cả relation vàng được ghi chú | 129 | 394 | +265 |
| Chứa ít nhất một chain vàng, không vượt `H` | 1.831 | 1.860 | +29 |
| Mỗi khóa `Evidence` có ít nhất một chain như vậy | 240 | 502 | +262 |

Có **818/1.970** câu có hơn 5 relation vàng phân biệt, nên top-5 không thể chứa hết mọi relation được ghi chú. Tuy nhiên, một khóa `Evidence` không nhất thiết tương ứng đúng một vế bắt buộc; các số trên là **proxy độ phủ relation**, không phải clause recall, KG proof recall hay Accuracy.

Trên **5 claim True H=1 được chọn có chủ đích**, R3 tạo candidate top-5/top-10 rồi nạp **cùng checkpoint V4, cùng K=32**: top-10 sửa **2 câu False → True**, 3 câu giữ True. Trên **10 claim False đối chứng** được chọn từ 57 ca đủ điều kiện cùng entity/họ relation với nhóm True, cả top-5 và top-10 đều đoán False. Đối chứng này không phải các cặp chỉ khác đúng một vế; 5 và 10 claim đều quá nhỏ, có thiên lệch chọn mẫu. Việc cùng ghi 32 path không có nghĩa hai tập path giống nhau. Xem [so sánh 5 ca True](v4_comparison_20261005_083018.md) và báo cáo false-controls trên máy GPU.

## 4. Lượt chạy mới top-10 và nút thắt R3 (5–6/10)

- **Relation predictor:** đã train lại trong `artifacts/r3_top10_v4_fresh_0710/retriever_model/relation_predict/`; checkpoint `lightning_logs/version_0/checkpoints/epoch=9-step=17350.ckpt` khoảng **1,3 GB**. Lệnh `--mode eval` với `relation_predict_top10.yaml` chạy xong **37/37 batch**; R3 đã đọc `test_relations_top10.json` khi dựng test. Tuy nhiên chưa có log đối chiếu số claim/nội dung JSON với `factkg_test.pickle` được gửi lại, nên cần xác nhận trước khi công bố đầu vào đã kiểm định đầy đủ.
- **Hop predictor:** thử train mới nhưng **CUDA OOM** ở đầu epoch với batch 64. Lúc lỗi, tiến trình hop dùng khoảng **11,57 GiB VRAM**, GPU chỉ còn **48,81 MiB**; các job vLLM/TTS khác đang chiếm phần lớn GPU. **Không có checkpoint hop mới hoàn chỉnh**. Lượt R3 sau đó được cấu hình dùng `with_evidence/retrieve/model/hop_predict/predictions_hop.json` cũ; không cần train hop lại chỉ vì đổi relation top-k, nhưng vẫn nên xác nhận JSON hop khớp đúng tập test.
- **R3 full top-10:** tiến trình thực tế **không có** `--test_only_candidates`; nó dựng train → dev → test với `--include_shorter_paths --relation_budget 2 --store_max_paths 32`. Train/dev đã qua và được ghi vào `artifacts/r3_top10_v4_fresh_0710/candidates_full/`. Test đến khoảng **3.528/9.041 claim** rồi đứng rất lâu; `ps` cho thấy PID dùng **99,9% một CPU**, RSS khoảng **11 GB**, tức vẫn tính toán chứ chưa thấy OOM. Lượt này đã được dừng. Theo code, file candidate test chỉ ghi khi xử lý xong toàn tập, nên **chưa có artifact test top-10 hoàn chỉnh** để V4 dự đoán.
- **V4:** chưa train mới và chưa test toàn bộ top-10. Checkpoint V4 top-5 cũ vẫn còn; nó có thể dùng để kiểm tra top-10 *sau khi* R3 tạo xong candidate test top-10. JSON relation/hop không phải đầu vào trực tiếp của V4.

Vì sao R3 top-5 trước từng nhanh nhưng các lượt sau chậm? Lượt top-5 chuẩn trên **test gốc 9.041 claim** đã hoàn thành. Lượt chẩn đoán khác dùng **dev 13.266 claim được đóng gói như test**, dự đoán top-5/H thay vì dùng Evidence vàng, từng chậm gần claim **5.495** (`H=2`, claim sân bay ở Punjab, CPU gần 100%, RAM khoảng 10,3 GB). Lượt hiện tại là **test gốc top-10** và chậm ở claim khác. Như vậy **top-5 cũng có ca nặng**; top-10 có thể tăng số chuỗi/nhánh phải duyệt nhưng chưa xác định chính xác nguyên nhân claim 3.528. `--store_max_paths 32` giới hạn path lưu, **không đảm bảo giới hạn mọi trạng thái KG phải duyệt**. Lệnh R3 top-5 cũ trong hướng dẫn dùng `--report_max_paths 32` (thống kê), khác cờ giới hạn lưu của lượt mới; cần xem manifest cũ trước khi nói hai lần chạy hoàn toàn giống cấu hình.

## 5. Nhận định và việc cần làm tiếp

1. **Kết luận được:** top-10 tăng độ phủ relation theo annotation dev và giúp 2/5 claim True được chọn, không làm 10 False đối chứng đổi nhãn. **Chưa kết luận được:** top-10 tăng Accuracy/Macro-F1 trên toàn test hay giải quyết chính lỗi Conjunction.
2. **Chốt đầu vào:** kiểm tra `test_relations_top10.json` của checkpoint mới và `predictions_hop.json` cũ cùng khớp 9.041 claim test, relation đủ 10 phần tử/claim; giữ manifest/log. Xác định claim test index 3.528, `H`, relation, entity và số trạng thái mở rộng trước khi thay đổi R3.
3. **Xử lý nút thắt R3:** ưu tiên đo/profile claim nặng và thêm lưu tiến độ/khả năng tiếp tục mà không đổi tập candidate. Nếu phải đặt giới hạn duyệt hoặc bỏ claim, ghi rõ đó là thí nghiệm có cắt và áp dụng cùng chính sách cho top-5/top-10; **không báo điểm đó như kết quả full-test nguyên bản**. Không khởi động lại y nguyên lệnh full khi chưa xử lý nút thắt.
4. **So sánh công bằng:** sau khi có candidate test hoàn chỉnh, nạp **cùng checkpoint V4, cùng K=32** cho hai nhánh. Vì relation top-10 full-test mới đến từ **checkpoint relation vừa train**, còn mốc top-5 cũ từ checkpoint trước, so trực tiếp chúng sẽ lẫn *đổi checkpoint* với *đổi top-k*. Muốn cô lập top-k, xuất cả top-5 và top-10 từ **cùng checkpoint relation mới**, dùng cùng hop, KG, R3 và V4. Sau đó mới cân nhắc train V4 mới hoặc tăng `K=64` như thí nghiệm riêng.

## 6. Artifact cần giữ và kiểm tra nhanh trên máy GPU

Các lệnh dưới đây **chỉ kiểm tra**, không chạy lại R3. Nếu file test top-10 chưa có, không chạy `baseline.py --test_only` với tên file đó.

```bash
export REPO=/home/namnx/duyanh/FactKG
export PYTHON=/home/namnx/duyanh/.conda/factkg/bin/python
export DATA_DIR=/home/namnx/duyanh/Data
export OLD="$REPO/artifacts/faico_lite_top5/r3_full"
export RUN="$REPO/artifacts/r3_top10_v4_fresh_0710"
export REL10="$RUN/retriever_model/relation_predict/test_relations_top10.json"
export HOP_JSON="$REPO/with_evidence/retrieve/model/hop_predict/predictions_hop.json"

ls -lh "$OLD/train_candid_paths_r3_full.bin" \
  "$OLD/dev_candid_paths_r3_full.bin" \
  "$OLD/test_candid_paths_top5_r3_full.bin" \
  "$RUN/candidates_full/train_candid_paths_r3_top10_full_k32.bin" \
  "$RUN/candidates_full/dev_candid_paths_r3_top10_full_k32.bin"

ls -lh "$RUN/candidates_full/test_candid_paths_top10_r3_top10_full_k32.bin"
```

Dòng `ls` cuối báo thiếu là **đúng với tình trạng lượt R3 đã dừng giữa test**. Kiểm tra cấu hình và thời gian lượt top-5 cũ bằng manifest/report, nếu hai file đó có sẵn:

```bash
"$PYTHON" -c 'import json,sys; m=json.load(open(sys.argv[1])); r=json.load(open(sys.argv[2])); print("Cấu hình:",m.get("config")); print("Đầu vào:",m.get("inputs")); print("Thời gian từng tập (giây):",{k:v.get("elapsed_seconds") for k,v in r.get("splits",{}).items()})' \
  "$OLD/manifest_r3_full.json" "$OLD/retrieval_report_r3_full.json"
```

`*.bin`, `*.json`, `*.ckpt`, `*.pth` có thể bị `.gitignore` bỏ qua; giữ riêng artifact máy GPU và không coi commit Markdown là đã sao lưu model/kết quả.
