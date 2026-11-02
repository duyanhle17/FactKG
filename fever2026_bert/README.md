# BERT one-hop cho FactKG

Đây là **bản triển khai độc lập** dựa trên phương pháp BERT one-hop mô tả trong
[Upadhyay et al., FEVER 2026](https://aclanthology.org/2026.fever-1.3/) và
[Opsahl 2024](https://aclanthology.org/2024.fever-1.32/), không phải bản copy
code tác giả. Chỉ dùng `Entity_set` và KG để tạo evidence, **không dùng**
`Evidence` vàng của train/dev. Mỗi triple `(head, relation, tail)` kề một entity
đều được giữ; BERT đọc `claim [SEP] triple [SEP] triple ...` (tối đa 512 token).

Cấu hình mặc định: `bert-base-uncased`, AdamW, batch 4, LR `5e-6`, tối đa 10
epoch, dừng sau 3 epoch không tăng dev accuracy. Epoch được chọn chỉ dựa vào
dev; test chạy bằng lệnh riêng. Năm nhóm reasoning dùng đúng thứ tự ưu tiên
trong `with_evidence/classifier/baseline.py` của repo FactKG này.

Trên máy GPU, chỉ cần chép **folder này**, không cần clone GitHub và không cần
commit 84 file đang thay đổi trên máy mượn. Cần cài `torch`, `transformers`,
`numpy` trong một Python environment phù hợp GPU; lần đầu tải
`bert-base-uncased` cần mạng hoặc model đã cache.

Ví dụ chuyển từ Windows PowerShell (thay `SSH_HOST` bằng host/alias bạn đang dùng):

```powershell
scp -r "C:\Duy Anh Le Code\FactKG\fever2026_bert" namnx@SSH_HOST:/home/namnx/duyanh/FactKG/
```

Lệnh này chỉ chép folder, không đụng Git hay các thay đổi khác trên GPU.

```bash
cd /home/namnx/duyanh/FactKG/fever2026_bert
export PYTHON=/home/namnx/duyanh/.conda/factkg/bin/python
export DATA_DIR=/home/namnx/duyanh/Data
export OUT=/home/namnx/duyanh/FactKG/artifacts/fever_onehop_bert_v1

"$PYTHON" -m unittest test_onehop -v
"$PYTHON" prepare.py \
  --data-dir "$DATA_DIR" \
  --kg-path "$DATA_DIR/dbpedia_2015_undirected_light.pickle" \
  --output-dir "$OUT/prepared"

"$PYTHON" train_eval.py train \
  --prepared-dir "$OUT/prepared" \
  --output-dir "$OUT/training"

"$PYTHON" train_eval.py evaluate \
  --checkpoint "$OUT/training/best_checkpoint" \
  --data "$OUT/prepared/test.pkl" \
  --output-dir "$OUT/test"
```

Trước khi train, kiểm tra `prepare_report.json`: paper dùng 86.367 train,
13.267 dev, 9.041 test và trung bình khoảng 57,8/50,0/52,5 triple.
Nếu dữ liệu trên máy khác phiên bản, điểm không thể so trực tiếp. Dù các tham số
chính khớp paper, **không cam kết** tái lập 92,68%: paper không công bố đầy đủ
thứ tự/chuỗi hóa triple, seed và lịch learning rate trong mô tả chính. Bản này
sắp xếp triple ổn định và không dùng scheduler chưa được chỉ định.
