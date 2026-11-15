#!/usr/bin/env bash
# P2: fine-tune BERT (from pretrained bert-base-uncased, same as the 92.6% baseline) on
# one-hop + retrieved bridges, then compare with the baseline on dev (flips / NFR).
#
# Stages (run in order, each can be rerun alone):
#   ./run_p2.sh check     # read-only: files, RAM, VRAM, disk
#   ./run_p2.sh bridges   # CPU + KG (~12 GB RAM): bridges for train and test (dev is reused if present)
#   ./run_p2.sh inputs    # CPU: one-hop + bridges subgraph files for train/val/test
#   ./run_p2.sh train     # GPU: upstream run_stuff.py, max N_EPOCHS, best-dev checkpoint, patience 3
#   ./run_p2.sh eval      # GPU: dev predictions with the best checkpoint + flip comparison vs baseline
#   ./run_p2.sh all       # everything above
# Run long stages in the background, e.g.:
#   nohup ./run_p2.sh all > ~/duyanh_bridge/logs/p2_all.log 2>&1 &
#
# Every path can be overridden with an environment variable (defaults = GPU-03 layout).
set -euo pipefail

RUNNABLE=${RUNNABLE:-/home/namnx/namnx/vault/cts_nambuw/runnable}   # FEVER code + data + cache (read only)
PY=${PY:-$RUNNABLE/.venv_fever_l40s/bin/python}
B=${B:-$HOME/duyanh_bridge}                                          # this project's work dir
CODE=${CODE:-$B/code}                                                # fever2026_bridge scripts
KG=${KG:-$B/data/dbpedia_2015_undirected_light.pickle}
FACTKG_DIR=${FACTKG_DIR:-$RUNNABLE/data/factkg}                      # factkg_{train,dev,test}.pickle
SUBG_DIR=${SUBG_DIR:-$RUNNABLE/data/subgraphs}                       # subgraphs_one_hop_{train,val,test}.pkl
VARIANT=${VARIANT:-bridge5}                                          # name of this experiment
MAX_PATHS=${MAX_PATHS:-5}                                            # bridges injected per claim
N_EPOCHS=${N_EPOCHS:-10}
MIN_VRAM_MB=${MIN_VRAM_MB:-8000}                                     # refuse to train below this
MIN_RAM_GB=${MIN_RAM_GB:-16}                                         # refuse to load the KG below this
BASE_DEV_PRED=${BASE_DEV_PRED:-$B/out/p0_fever_dev/predictions.pkl}  # baseline dev predictions (P0)
GPU=${GPU:-0}

OUT=$B/out
P2=$B/p2_$VARIANT
LOGS=$B/logs
mkdir -p "$OUT" "$LOGS"
log() { echo "[$(date '+%F %T')] $*"; }

check_ram() {
  local avail
  avail=$(free -g | awk '/^Mem:/{print $7}')
  log "RAM available: ${avail} GB (need >= ${MIN_RAM_GB})"
  if [ "$avail" -lt "$MIN_RAM_GB" ]; then log "STOP: not enough RAM to load the KG"; exit 3; fi
}

check_vram() {
  local free
  free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits -i "$GPU" | head -1)
  log "GPU $GPU free VRAM: ${free} MiB (need >= $1)"
  if [ "$free" -lt "$1" ]; then log "STOP: not enough VRAM; other jobs are left untouched"; exit 4; fi
}

bridges_for() {  # split-name factkg-pickle
  local split=$1 pickle=$2
  if [ -f "$OUT/bridges_${split}.pkl" ]; then log "bridges_${split}.pkl exists, skip"; return; fi
  check_ram
  ( ulimit -v 20971520
    "$PY" "$CODE/bridge_retrieval.py" --kg "$KG" --factkg "$pickle" --work-dir "$OUT/bridges_${split}_shards" )
  "$PY" "$CODE/bridge_retrieval.py" --factkg "$pickle" --work-dir "$OUT/bridges_${split}_shards" \
    --merge "$OUT/bridges_${split}.pkl"
}

stage_bridges() {
  cd "$CODE"
  bridges_for dev   "$FACTKG_DIR/factkg_dev.pickle"
  bridges_for train "$FACTKG_DIR/factkg_train.pickle"
  bridges_for test  "$FACTKG_DIR/factkg_test.pickle"
}

stage_inputs() {
  cd "$CODE"
  local split pickle sub
  for split in train val test; do
    case $split in
      train) pickle=factkg_train.pickle; b=train ;;
      val)   pickle=factkg_dev.pickle;   b=dev ;;
      test)  pickle=factkg_test.pickle;  b=test ;;
    esac
    sub="$OUT/inj_${VARIANT}_${split}.pkl"
    if [ -f "$sub" ]; then log "$sub exists, skip"; continue; fi
    log "building $sub"
    "$PY" build_injected.py --factkg "$FACTKG_DIR/$pickle" --subgraphs "$SUBG_DIR/subgraphs_one_hop_${split}.pkl" \
      --source bridges --source-file "$OUT/bridges_${b}.pkl" --groups all --max-paths "$MAX_PATHS" --output "$sub"
  done
}

stage_train() {
  if [ -e "$P2/runnable/models/bert-base-uncased.pth" ]; then
    log "STOP: $P2 already has a trained model; choose another VARIANT"; exit 5
  fi
  check_vram "$MIN_VRAM_MB"
  # Fresh copy of the upstream code so the baseline checkpoint in $RUNNABLE/models is never overwritten.
  mkdir -p "$P2/runnable"/{data,models,results}
  cp "$RUNNABLE"/*.py "$P2/runnable/"
  [ -e "$P2/runnable/data/factkg" ] || ln -s "$FACTKG_DIR" "$P2/runnable/data/factkg"
  [ -e "$P2/runnable/cache" ] || cp -r "$RUNNABLE/cache" "$P2/runnable/cache"   # model weights, own copy
  cd "$P2/runnable"
  log "training $VARIANT: max $N_EPOCHS epochs, best dev checkpoint, patience 3 (same as baseline)"
  CUDA_VISIBLE_DEVICES=$GPU \
  FACTKG_SUBGRAPHS_TRAIN_PATH="$OUT/inj_${VARIANT}_train.pkl" \
  FACTKG_SUBGRAPHS_VAL_PATH="$OUT/inj_${VARIANT}_val.pkl" \
  FACTKG_SUBGRAPHS_TEST_PATH="$OUT/inj_${VARIANT}_test.pkl" \
    "$PY" run_stuff.py "fever_bert_${VARIANT}" --subgraph_type one_hop --subgraph_to_use walkable \
      --batch_size 4 --learning_rate 0.000005 --n_epochs "$N_EPOCHS" 2>&1 | tee "$LOGS/p2_${VARIANT}_train.log"
  log "NOTE: run_stuff.py also prints a test score. Do not use it to choose between variants (dev only)."
}

stage_eval() {
  check_vram 2048
  cd "$CODE"
  local res="$OUT/p2_${VARIANT}_dev"
  [ -e "$res" ] && { log "STOP: $res exists"; exit 6; }
  CUDA_VISIBLE_DEVICES=$GPU HF_HUB_OFFLINE=1 "$PY" fever_predict.py \
    --factkg "$FACTKG_DIR/factkg_dev.pickle" --subgraphs "$OUT/inj_${VARIANT}_val.pkl" \
    --checkpoint "$P2/runnable/models/bert-base-uncased.pth" --cache-dir "$P2/runnable/cache" \
    --output-dir "$res" --batch-size 8
  "$PY" flip_compare.py --base "$BASE_DEV_PRED" --new "$res/predictions.pkl" --output "$res/flips.json" \
    | tee "$LOGS/p2_${VARIANT}_flips.txt"
  log "best epoch / dev accuracy from training log:"
  grep -E "best|Best|Early stopping|Test accuracy" "$LOGS/p2_${VARIANT}_train.log" | tail -5 || true
}

stage_check() {  # read-only: verify inputs and show resources before starting anything
  local ok=1 f
  for f in "$PY" "$KG" "$RUNNABLE/run_stuff.py" "$RUNNABLE/cache" "$BASE_DEV_PRED" \
           "$FACTKG_DIR"/factkg_{train,dev,test}.pickle "$SUBG_DIR"/subgraphs_one_hop_{train,val,test}.pkl \
           "$CODE"/{bridge_retrieval,build_injected,fever_predict,flip_compare}.py; do
    if [ -e "$f" ]; then echo "  ok      $f"; else echo "  MISSING $f"; ok=0; fi
  done
  free -h | head -2
  nvidia-smi --query-gpu=index,memory.used,memory.free --format=csv,noheader
  df -h "$B" | tail -1
  [ "$ok" = 1 ] || { log "STOP: missing files above"; exit 2; }
}

case "${1:-}" in
  check)   stage_check ;;
  bridges) stage_bridges ;;
  inputs)  stage_inputs ;;
  train)   stage_train ;;
  eval)    stage_eval ;;
  all)     stage_check; stage_bridges; stage_inputs; stage_train; stage_eval ;;
  *) echo "usage: $0 {check|bridges|inputs|train|eval|all}"; exit 1 ;;
esac
log "done: ${1}"
