# FEVER 2026 BERT one-hop trên FactKG gốc

Đây là **pipeline BERT trong [repo tác giả](https://github.com/AnkitKUpadhyay/kg-fact-verification-semantics)** ở commit `ece1dea43467ddd9d13b7a8d5a2ce333503ecafa`, không phải bản BERT-only tự viết trong `fever2026_bert/`. Repo public này chỉ lưu liên kết Git submodule tới nguồn gốc và script dựng bản chạy riêng. `runnable/` được tạo tại máy cá nhân, bị Git bỏ qua và có thể chép thẳng sang GPU; không chép lại mã tác giả vào GitHub FactKG public.

Flow giữ theo code tác giả: `factkg_{train,dev,test}.pickle` + DBpedia → `retrieve_subgraphs.py --method one_hop` → file `subgraphs_one_hop_{train,val,test}.pkl` → `datasets.py` lấy `walked.connected + walked.walkable`, ghép `claim + " | " + str(evidence)`, tokenizer tối đa 512 token → `bert-base-uncased` fine-tune phân loại nhị phân → `evaluate.py` (6 tag chồng lấn của tác giả) → `eval_five.py` (5 nhóm loại trừ nhau theo FactKG R3/V4). Không dùng nhãn hoặc `Evidence` vàng của dev/test để tạo đầu vào. Không chạy LLM, không train QA-GNN, nhưng `datasets.py`/`models.py` có import `torch_geometric` nên môi trường vẫn cần gói đó.

## Khác biệt được chủ ý và giới hạn tái lập

`build_runnable.py` giữ nguyên 9 module Python upstream, chỉ sửa 4 chỗ có kiểm tra chuỗi gốc và ghi vào `provenance.json`: (1) train trên full `factkg_train.pickle` thay vì mặc định sample 10k, (2) thêm `glocal_settings.py` bị thiếu trong repo, (3) chọn checkpoint/dừng sớm theo **dev accuracy** như paper và chụp state dict độc lập, (4) không bỏ batch cuối ở train/dev, dev không shuffle. Tham số chạy: BERT-base-uncased, batch 4, LR `5e-6`, max length 512, AdamW, patience 3 từ code; ví dụ bên dưới đặt tối đa 10 epoch. Vì có các sửa này, đây là **bản tác giả + patch minh bạch để khớp paper**, không phải từng byte y hệt upstream.

Chưa thể cam kết tái lập **92,68%** trước khi train. Paper mô tả “linearized list of triples” một-hop, nhưng code công bố (`retrieve_subgraphs.py` → `kg.py`) tạo relation rồi `KG.search` có thể chọn một tail ngẫu nhiên và khử trùng endpoint. Bản chạy này **giữ hành vi upstream** để đo thực nghiệm; không tự biến nó thành “full mọi triple”. `environment.yaml` của tác giả có Python 3.10, PyTorch 2.0.1, Transformers 4.40.2 và torch-geometric 2.5.3. Môi trường GPU hiện tại của bạn có Transformers 5.13.1; cần kiểm tra tương thích, không mặc nhiên cho là tái lập chuẩn.

## Dựng và chép bản chạy (PowerShell trên máy cá nhân)

```powershell
cd 'C:\Duy Anh Le Code\FactKG'
git submodule update --init fever2026_official/upstream
python -m unittest discover -s fever2026_official -p 'test_build_runnable.py' -v
python fever2026_official/build_runnable.py
ssh namnx@SSH_HOST 'mkdir -p /home/namnx/duyanh/FactKG/fever2026_official'
scp -r 'C:\Duy Anh Le Code\FactKG\fever2026_official\runnable' namnx@SSH_HOST:/home/namnx/duyanh/FactKG/fever2026_official/
```

Thay `SSH_HOST` bằng alias/địa chỉ SSH thực; tránh chép đè bản đang chạy. Nếu `runnable/` đã tồn tại, builder cố tình từ chối ghi đè. Không cần `git pull`, `git commit`, hay dùng tài khoản GitHub của chủ máy GPU.

## Trên GPU (bash, từ thư mục mới; không đụng artifact R3/V4)

```bash
export REPO=/home/namnx/duyanh/FactKG
export PYTHON=/home/namnx/duyanh/.conda/factkg/bin/python
export DATA_DIR=/home/namnx/duyanh/Data
cd "$REPO/fever2026_official/runnable"
"$PYTHON" -c 'import torch, transformers, torch_geometric, pandas, sklearn, spacy, nltk; print("torch", torch.__version__, "transformers", transformers.__version__)'
mkdir -p data/factkg data/dbpedia data/subgraphs models results
ln -s "$DATA_DIR/factkg_train.pickle" data/factkg/factkg_train.pickle
ln -s "$DATA_DIR/factkg_dev.pickle" data/factkg/factkg_dev.pickle
ln -s "$DATA_DIR/factkg_test.pickle" data/factkg/factkg_test.pickle
ln -s "$DATA_DIR/dbpedia_2015_undirected_light.pickle" data/dbpedia/dbpedia_2015_undirected_light.pickle
"$PYTHON" -c 'from datasets import get_df; print({s: len(get_df(s)) for s in ("train", "val", "test")})'
"$PYTHON" retrieve_subgraphs.py --dataset_type all --method one_hop
"$PYTHON" run_stuff.py fever_bert_onehop_full --subgraph_type one_hop --subgraph_to_use walkable --batch_size 4 --learning_rate 0.000005 --n_epochs 10
"$PYTHON" eval_five.py --model-path models/bert-base-uncased.pth --output-dir results/five_reasoning_onehop
```

**Trước khi chạy train:** kiểm tra các symlink chưa tồn tại để tránh `ln` báo lỗi; không dùng `ln -sf` để ghi đè. Lệnh `run_stuff.py` của tác giả **tự đánh giá test sau khi train**, nên chốt cấu hình bằng dev trước, không lặp nhiều biến thể để chọn theo test. Tên checkpoint thực tế cần xem trong `models/` sau khi train (`get_bert_model` đặt `model.name = "bert-base-uncased"`; `utils.save_model` dùng tên này), rồi chỉnh `--model-path` nếu khác. So sánh với R3/V4 trên đúng 9.041 test claims và cùng thứ tự; `eval_five.py` kiểm tra nhãn khớp dữ liệu và xuất `predictions.pkl` để so từng câu. Nếu số lượng train/dev/test hoặc phiên bản DBpedia khác paper, ghi rõ khác biệt.

Nếu `torch_geometric` hoặc Transformers 5.13.1 không tương thích với code tác giả, nên tạo môi trường riêng theo `environment.yaml` thay vì sửa các module nghiên cứu âm thầm. Với GPU đang còn ~11,5 GB trống (lần kiểm tra trước), batch 4 cần kiểm tra lại VRAM trước khi chạy.
