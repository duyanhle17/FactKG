# fever2026_bridge — P0/P1: multi-hop bridge diagnostics for FEVER-2026 BERT

Mục tiêu và giả thuyết: xem mục "Brainstorm ý tưởng + hướng đi tiếp theo" trong
[báo cáo 11_11](../ý%20tưởng%20+%20thực%20nghiệm/báo%20cáo%2011_11.md). Thư mục này **không sửa và
không import code upstream**; chỉ cần `torch`, `transformers`, `pandas`. File subgraph xuất ra
giữ đúng định dạng upstream (`DataFrame` cột `walked: {connected, walkable}`), nên sau này
`run_stuff.py`/`eval_five.py` đọc được qua `FACTKG_SUBGRAPHS_{TRAIN,VAL,TEST}_PATH`.

| Script | Cần | Làm gì |
|---|---|---|
| `fever_predict.py` | GPU + checkpoint | Dự đoán + xác suất từng claim cho split/subgraph bất kỳ |
| `token_audit.py` | tokenizer | Token thật, % vượt 512, % path còn nhìn thấy sau khi cắt |
| `bridge_retrieval.py` | **KG** (RAM lớn) | Bridge 2–3 hop giữa mọi cặp entity của claim; chạy tiếp được theo shard |
| `gold_bridge.py` | **KG** | Dựng path từ relation vàng (train/dev), gồm cả near-miss |
| `build_injected.py` | — | Chèn bridge (vàng hoặc tìm được) lên đầu `connected` → file subgraph mới |
| `analyze_p0.py` | — | Báo cáo P0: bridge theo nhóm/nhãn, phân rã lỗi multi-hop, oracle FEVER ∪ V4 |
| `flip_compare.py` | — | So 2 lần chạy: Δ, +flip/−flip, NFR, McNemar theo nhóm |

Unit test (không cần torch): `python -m unittest test_bridge -v`.

## Triển khai: dồn P0/P1 về máy R3/V4 (có KG + dự đoán V4)

Máy FEVER chỉ cần gửi **checkpoint** đi. Subgraph one-hop của FEVER đã có sẵn ở máy local
(`fever2026_official/runnable/data/subgraphs/`), không cần lấy từ GPU.

**Trên máy local (PowerShell)**, thay `FEVER_HOST`, `R3_HOST` bằng alias SSH thật:

```powershell
cd 'C:\Duy Anh Le Code\FactKG'
# 1) lấy checkpoint từ máy FEVER về local (~440 MB)
scp FEVER_HOST:/home/namnx/namnx/vault/cts_nambuw/runnable/models/bert-base-uncased.pth .\fever_ckpt_10ep.pth
# 2) đẩy code + checkpoint + subgraph one-hop sang máy R3/V4 (thư mục mới, không đụng gì cũ)
ssh R3_HOST 'mkdir -p ~/fever_bridge/{data,models,out}'
scp -r .\fever2026_bridge R3_HOST:~/fever_bridge/code
scp .\fever_ckpt_10ep.pth R3_HOST:~/fever_bridge/models/
scp .\fever2026_official\runnable\data\subgraphs\subgraphs_one_hop_val.pkl .\fever2026_official\runnable\data\subgraphs\subgraphs_one_hop_test.pkl R3_HOST:~/fever_bridge/data/
```

**Trên máy R3/V4 (bash):** điền đường dẫn thật ở 4 biến đầu.

```bash
export PY=/path/to/python            # env R3/V4 (có torch, transformers, pandas)
export DATA=/path/to/factkg_pickles  # thư mục chứa factkg_{train,dev,test}.pickle
export KG=/path/to/dbpedia_2015_undirected_light.pickle
export W=~/fever_bridge
cd $W/code && $PY -m unittest test_bridge -v
free -h && nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# P0.0 sanity: phải ra 8372/9041 = 92.6004% (khớp lượt 10 epoch). Không khớp thì DỪNG.
$PY fever_predict.py --factkg $DATA/factkg_test.pickle --subgraphs $W/data/subgraphs_one_hop_test.pkl \
    --checkpoint $W/models/fever_ckpt_10ep.pth --output-dir $W/out/p0_fever_test
# P0.1 dự đoán dev + đo token
$PY fever_predict.py --factkg $DATA/factkg_dev.pickle --subgraphs $W/data/subgraphs_one_hop_val.pkl \
    --checkpoint $W/models/fever_ckpt_10ep.pth --output-dir $W/out/p0_fever_dev
$PY token_audit.py --factkg $DATA/factkg_dev.pickle --subgraphs $W/data/subgraphs_one_hop_val.pkl \
    --output-dir $W/out/p0_tokens_dev

# P0.2 bridge + bridge vàng (CPU, chạy nền; thử --limit 200 trước để ước lượng thời gian/RAM)
nohup $PY bridge_retrieval.py --kg $KG --factkg $DATA/factkg_dev.pickle \
    --work-dir $W/out/bridges_dev_shards > $W/out/bridges_dev.log 2>&1 &
$PY bridge_retrieval.py --factkg $DATA/factkg_dev.pickle --work-dir $W/out/bridges_dev_shards \
    --merge $W/out/bridges_dev.pkl          # sau khi log báo "all shards done"
$PY gold_bridge.py --kg $KG --factkg $DATA/factkg_dev.pickle --output $W/out/gold_bridges_dev.pkl

# P0.3 báo cáo (V4: file kết quả có khóa prediction/label + file data V4 đã đánh giá)
$PY analyze_p0.py --factkg $DATA/factkg_dev.pickle --fever $W/out/p0_fever_dev/predictions.pkl \
    --bridges $W/out/bridges_dev.pkl --gold $W/out/gold_bridges_dev.pkl \
    --tokens $W/out/p0_tokens_dev/per_claim.pkl --subgraphs $W/data/subgraphs_one_hop_val.pkl \
    --v4 /path/to/v4_dev_result.pkl --v4-data /path/to/v4_dev_data.pickle \
    --output-dir $W/out/p0_report_dev
```

Hai lần chạy `bridge_retrieval.py` và `gold_bridge.py` mỗi lần nạp KG một lần. Nếu RAM không đủ cho
2 tiến trình cùng lúc thì chạy lần lượt.

## P1: chèn bridge, không train (chỉ dev)

```bash
# (a) oracle: bridge vàng, chỉ claim multi-hop  (b) oracle cho mọi nhóm → đo NFR
# (c) bridge tìm được (không dùng thông tin vàng), mọi nhóm
$PY build_injected.py --factkg $DATA/factkg_dev.pickle --subgraphs $W/data/subgraphs_one_hop_val.pkl \
    --source gold --source-file $W/out/gold_bridges_dev.pkl --groups multi-hop --output $W/out/inj_gold_mh_val.pkl
$PY build_injected.py --factkg $DATA/factkg_dev.pickle --subgraphs $W/data/subgraphs_one_hop_val.pkl \
    --source gold --source-file $W/out/gold_bridges_dev.pkl --groups all --output $W/out/inj_gold_all_val.pkl
$PY build_injected.py --factkg $DATA/factkg_dev.pickle --subgraphs $W/data/subgraphs_one_hop_val.pkl \
    --source bridges --source-file $W/out/bridges_dev.pkl --groups all --output $W/out/inj_bridge_all_val.pkl
for v in gold_mh gold_all bridge_all; do
  $PY fever_predict.py --factkg $DATA/factkg_dev.pickle --subgraphs $W/out/inj_${v}_val.pkl \
      --checkpoint $W/models/fever_ckpt_10ep.pth --output-dir $W/out/p1_${v}_dev
  $PY flip_compare.py --base $W/out/p0_fever_dev/predictions.pkl \
      --new $W/out/p1_${v}_dev/predictions.pkl --output $W/out/p1_${v}_dev/flips.json
done
```

**Cổng quyết định:** (a) tăng multi-hop dev ≥ 5 điểm ⇒ thiếu evidence là nút thắt, sang P2 (train
với bridge). Không đạt ⇒ chuyển sang cải thiện verifier. (b), (c) cho biết NFR ở các nhóm khác khi
mở rộng không chọn lọc (giả thuyết H2). Lưu ý: checkpoint chưa từng thấy path 2 hop lúc train, nên
P1 là **cận dưới** của lợi ích; `--groups` dùng nhãn loại claim nên chỉ là chẩn đoán.

Gửi về local các file nhỏ: `out/p0_report_dev/report.md`, `out/*/metrics.json`, `out/p1_*/flips.json`,
`out/*.stats.json`, `out/gold_bridges_dev.pkl.summary.json`. **Không** chạy test với file injected.
