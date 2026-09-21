import argparse
import os
import pickle as pkl
import random
from itertools import chain
from dataclasses import dataclass

import numpy as np
import torch
import torch.nn as nn
from tqdm import tqdm
from transformers import AutoConfig, AutoModel, AutoTokenizer, BertModel, PreTrainedTokenizerBase

from preprocess import prepare_input
from sparse_ernet import SparseERNet, build_sparse_path_adjacency

try:
    from termcolor import colored
except ImportError:
    # Color is cosmetic; keep training runnable when termcolor is not installed.
    def colored(text, *_args, **_kwargs):
        return str(text)

# [DISABLED] Phase 1.2/1.3 pruning — tạm ẩn để test 5-hop trên code gốc
# from prune_candid_paths import prune_candids


# ============================================================
# [DISABLED] Phase 2 — Soft Flatten Utilities
# Tạm ẩn để test 5-hop trên code gốc FactKG
# ============================================================

# def clean_kg_text(text: str) -> str:
#     """Clean a KG entity or relation string for BERT.
#     - Remove DBpedia prefixes (dbo:, dbp:)
#     - Replace underscores with spaces
#     - Split CamelCase: birthPlace -> birth Place -> birth place
#     - Remove Wikipedia parenthetical disambiguators: Washington_(state) -> Washington
#     """
#     text = text.replace("dbo:", "").replace("dbp:", "")
#     text = re.sub(r'_?\([^)]*\)', '', text)
#     text = text.replace("_", " ")
#     text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)
#     text = text.lstrip("~")
#     return text.strip()
#
#
# def soft_flatten_path(path: list) -> str:
#     """Convert a raw KG path into a clean, lightly formatted string."""
#     cleaned = [clean_kg_text(x) for x in path]
#     hops = []
#     for i in range(0, len(cleaned) - 2, 2):
#         subj = cleaned[i]
#         rel = cleaned[i + 1]
#         obj = cleaned[i + 2]
#         hops.append(f"{subj} {rel} {obj}")
#     return " . ".join(hops) if hops else " ".join(cleaned)


parser = argparse.ArgumentParser()
parser.add_argument('--data_path', type=str, help='')
parser.add_argument('--kg_path', type=str, help='')
parser.add_argument('--lr', default=5e-5, type=float, help='')
parser.add_argument(
    '--model_cls',
    default="cat",
    choices=(
        "sent", "cat", "mean", "gearlite", "gearlite_v2", "gearlite_v3",
        "gearlite_v4", "gearlite_v5",
    ),
    help=(
        'sent: claim-only; cat: E0; mean: E1 Pair+Mean; '
        'gearlite: E2 Pair+Attention; '
        'gearlite_v2: E3 Pair+Attention with path-mean claim condition; '
        'gearlite_v3: E4 Pair+Attention with separately encoded claim condition; '
        'gearlite_v4: E5 hybrid attention with separate claim and path-set mean; '
        'gearlite_v5: E6 V4 plus one sparse ERNet message-passing layer'
    ),
)
parser.add_argument('--epoch', default=10, type=int, help='')
# parser.add_argument('--db_name', default="", type=str, help='')
parser.add_argument('--n_candid', default="3", type=str, help='')
parser.add_argument('--scratch', action='store_true', help='')
parser.add_argument('--prune_noise', action='store_true', help='Legacy no-op: candidate pruning is currently disabled')
parser.add_argument('--train_candid_path', default="", type=str, help='Optional path to train candidate paths (.bin)')
parser.add_argument('--dev_candid_path', default="", type=str, help='Optional path to dev candidate paths (.bin)')
parser.add_argument('--test_candid_path', default="", type=str, help='Optional path to test candidate paths (.bin)')

# ============================================================
# [GEAR-LITE E1/E2 START] Experiment and pair-input arguments
# Remove this block together with PairDataset/PairDataCollator and the two
# pair classifiers below to return to the original E0/Sentence code path.
# ============================================================
parser.add_argument('--batch_size', default=32, type=int, help='Claim batch size for sent/cat (E0)')
parser.add_argument('--pair_batch_size', default=1, type=int, help='Claim batch size for mean/gearlite; each claim has K BERT pairs')
parser.add_argument('--max_paths', default=None, type=int, help='First K paths; default is all for E0 and 32 for E1/E2; 0 always means all')
parser.add_argument('--pair_max_length', default=128, type=int, help='Maximum tokens for each [CLS] Claim [SEP] Path [SEP] pair')
parser.add_argument('--gradient_accumulation_steps', default=0, type=int, help='Optimizer accumulation steps; 0 automatically matches the E0 effective claim batch')
parser.add_argument('--amp', action='store_true', help='Use CUDA FP16 automatic mixed precision for pair-model training/evaluation')
parser.add_argument('--seed', default=42, type=int, help='Random seed used by Python, NumPy and PyTorch')
parser.add_argument('--skip_prepare_input', action='store_true', help='Reuse existing candidate .bin artifacts instead of regenerating them')
parser.add_argument('--prepare_only', action='store_true', help='Generate candidate artifacts and exit before training')
# Các cờ dưới đây không đổi kiến trúc E2. Chúng chỉ giúp lưu checkpoint R1 và
# dùng đúng checkpoint đó để test R2/R3, tránh lẫn ảnh hưởng retriever với
# khác biệt ngẫu nhiên do train GPU lần nữa.
parser.add_argument('--run_name', default='', type=str, help='Nhãn riêng cho file prediction, ví dụ r1_top5')
parser.add_argument('--output_dir', default='.', type=str, help='Thư mục ghi prediction và checkpoint tốt nhất')
parser.add_argument('--test_only', action='store_true', help='Không train; chỉ test một checkpoint dev tốt nhất đã lưu')
parser.add_argument('--checkpoint_path', default='', type=str, help='Checkpoint bắt buộc khi dùng --test_only')
# [GEAR-LITE E1/E2 END]

args = parser.parse_args()

if args.max_paths is None:
    # Preserve the original README behavior for E0 while giving pair models a
    # finite, safer default. Controlled E0/E1/E2/E3/E4/E5/E6 runs should pass K explicitly.
    args.max_paths = 32 if args.model_cls in (
        "mean", "gearlite", "gearlite_v2", "gearlite_v3", "gearlite_v4",
        "gearlite_v5",
    ) else 0

if args.max_paths < 0:
    parser.error('--max_paths must be >= 0')
if args.batch_size <= 0 or args.pair_batch_size <= 0:
    parser.error('--batch_size and --pair_batch_size must be > 0')
if not 1 <= args.pair_max_length <= 512:
    parser.error('--pair_max_length must be in [1, 512] for bert-base-cased')
if args.gradient_accumulation_steps < 0:
    parser.error('--gradient_accumulation_steps must be >= 0')
if args.epoch < 1:
    parser.error('--epoch must be at least 1')
if args.prepare_only and args.skip_prepare_input:
    parser.error('--prepare_only and --skip_prepare_input cannot be used together')
if args.prepare_only and args.test_only:
    parser.error('--prepare_only and --test_only cannot be used together')
if args.test_only and not args.checkpoint_path:
    parser.error('--test_only requires --checkpoint_path')
if not args.skip_prepare_input and any(
    (args.train_candid_path, args.dev_candid_path, args.test_candid_path)
):
    parser.error(
        'Explicit --*_candid_path arguments require --skip_prepare_input; '
        'prepare_input writes only the default artifact filenames.'
    )
if args.run_name and (os.path.sep in args.run_name or (os.path.altsep and os.path.altsep in args.run_name)):
    parser.error('--run_name must be a simple label, not a path')
os.makedirs(args.output_dir, exist_ok=True)

random.seed(args.seed)
np.random.seed(args.seed)
torch.manual_seed(args.seed)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(args.seed)

PT_CLS = "bert-base-cased"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
PAIR_MODEL_NAMES = {
    "mean", "gearlite", "gearlite_v2", "gearlite_v3", "gearlite_v4",
    "gearlite_v5",
}


def _reasoning_type(type_names):
    """Map FactKG reasoning tags to the five evaluation groups."""
    if "negation" in type_names:
        return 4
    if "num1" in type_names:
        return 0
    if "multi hop" in type_names:
        return 1
    if "multi claim" in type_names:
        return 2
    if "existence" in type_names:
        return 3
    raise ValueError(f"Unknown FactKG reasoning type: {type_names}")


def _ordered_paths(evidence_groups, max_paths=0):
    """Preserve the artifact order: connected paths first, then walkable."""
    paths = list(evidence_groups[0]) + list(evidence_groups[1])
    return paths[:max_paths] if max_paths > 0 else paths


def _label_to_int(label):
    """FactKG stores labels as one-element lists, e.g. [True]."""
    if isinstance(label, (list, tuple)):
        if len(label) != 1:
            raise ValueError(f"Expected one FactKG label, got: {label}")
        label = label[0]
    return int(label)


class Dataset(torch.utils.data.Dataset):
    def __init__(
        self,
        split: str,
        claims: list,
        evis: list,
        labels: list,
        types: list = None,
        max_paths: int = 0,
        entity_sets: list = None,
    ):
        super().__init__()
        
        self.claims = claims
        self.labels = labels
        self.split = split
        self.evis = evis
        self.types = types
        self.max_paths = max_paths
        # E0/Sentence models do not use Entity_set. Accept it only so the
        # dataset construction remains uniform with pair models.
        self.entity_sets = entity_sets
        
        assert len(self.evis) == len(self.claims)
        assert len(self.evis) == len(self.labels)
        if self.types is not None:
            assert len(self.evis) == len(self.types)
        
    def __len__(self):
        return len(self.evis)
    
    def __getitem__(self, i):
        paths = _ordered_paths(self.evis[i], self.max_paths)
        flat_evi = list(chain.from_iterable(paths))

        if self.split == "test":
            # [ORIGINAL] Ghép evidence bằng sep_token gốc FactKG
            sample = {
                "e": flat_evi,
                "c":self.claims[i],
                "l":self.labels[i],
                "type":_reasoning_type(self.types[i]),
            }
        else:
            # [ORIGINAL] Ghép evidence bằng sep_token gốc FactKG
            sample = {
                "e": flat_evi,
                "c":self.claims[i],
                "l":self.labels[i],
            }
        
        return sample


# ============================================================
# [GEAR-LITE E1/E2 START] Dataset that keeps path boundaries
# E1/E2 must not flatten all paths into one long evidence string.
# ============================================================
class PairDataset(torch.utils.data.Dataset):
    def __init__(
        self, split, claims, evis, labels, types=None, max_paths=0,
        entity_sets=None,
    ):
        super().__init__()
        self.split = split
        self.claims = claims
        self.evis = evis
        self.labels = labels
        self.types = types
        self.max_paths = max_paths
        self.entity_sets = entity_sets

        assert len(self.evis) == len(self.claims) == len(self.labels)
        if self.types is not None:
            assert len(self.evis) == len(self.types)
        if self.entity_sets is not None:
            assert len(self.evis) == len(self.entity_sets)

    def __len__(self):
        return len(self.evis)

    def __getitem__(self, i):
        sample = {
            "paths": _ordered_paths(self.evis[i], self.max_paths),
            "c": self.claims[i],
            "l": self.labels[i],
            # [GEAR-LITE E6] Raw FactKG Entity_set lets the sparse ERNet
            # distinguish a true shared intermediate from a common claim
            # anchor. It does not alter tokenization or the V1--V4 models.
            "claim_entities": (
                self.entity_sets[i] if self.entity_sets is not None else []
            ),
        }
        if self.split == "test":
            sample["type"] = _reasoning_type(self.types[i])
        return sample
# [GEAR-LITE E1/E2 END]
    
@dataclass
class DataCollator:
    split: str
    tokenizer: PreTrainedTokenizerBase

    def tensorize(self, batch):
        for k, v in batch.items():
            if isinstance(v, list):
                o = torch.tensor(v, device=DEVICE)
            else:
                o = {_k:_v.to(DEVICE) for _k, _v in v.items()}
            batch[k] = o
            
        return batch

    def batchfy(self, features):
        keys = set(features[0].keys())
        batch = {k: [e[k] if k in e else None for e in features] for k in keys}

        claim = batch.pop("c")
        tokenized_claim = self.tokenizer(
                            claim,
                            padding="longest",
                            max_length=128,
                            truncation=True,
                            return_tensors="pt",
                        )
        
        evidence = batch.pop("e")
        seq_evidence = [f"{self.tokenizer.sep_token.join(evi)} {self.tokenizer.sep_token}" for evi in evidence]

        tokenized_evidence = self.tokenizer(
                            seq_evidence,
                            padding="longest",
                            max_length=512-len(tokenized_claim["input_ids"][0]),
                            truncation=True,
                            add_special_tokens=False,
                            return_tensors="pt",
                        )
        
        label = [_label_to_int(x) for x in batch.pop("l")]
            
        pt_batch = {
            "evidence": tokenized_evidence,
            "claim": tokenized_claim,
            "label": label,
        }

        if "type" in batch:
            pt_batch["type"] = batch["type"]

        return pt_batch

    def __call__(self, features):
        batch = self.batchfy(features)

        return self.tensorize(batch)


# ============================================================
# [GEAR-LITE E1/E2/E3/E4/E5/E6 START] Claim-Path pair collator
# Output shapes are [B, K, L] plus path_mask [B, K]. Padding paths are
# tokenized only to make a rectangular tensor and are ignored by the mask.
# E4/v3 and E5/v4 additionally receive `claim_inputs` with shape [B, L]. This
# is the same raw claim, tokenized without any path, so its encoder vector is
# independent of candidate-path noise.
# ============================================================
@dataclass
class PairDataCollator:
    split: str
    tokenizer: PreTrainedTokenizerBase
    max_length: int = 128
    include_sparse_adjacency: bool = False

    def __call__(self, features):
        batch_size = len(features)
        paths_per_claim = [feature["paths"] for feature in features]

        # Null-evidence fallback: a claim with zero retrieved candidates gets
        # one Claim + empty-path pair. It is not a retrieved path, but keeping
        # it unmasked lets BERT encode the claim and prevents all-masked softmax.
        paths_per_claim = [paths if paths else [[]] for paths in paths_per_claim]
        path_count = max(len(paths) for paths in paths_per_claim)

        flat_claims = []
        flat_paths = []
        path_mask = torch.zeros((batch_size, path_count), dtype=torch.bool)

        for batch_index, (feature, paths) in enumerate(zip(features, paths_per_claim)):
            for path_index in range(path_count):
                is_real_path = path_index < len(paths)
                path = paths[path_index] if is_real_path else []

                flat_claims.append(feature["c"])
                # Preserve the original baseline's entity/relation separator.
                flat_paths.append(f" {self.tokenizer.sep_token} ".join(map(str, path)))
                path_mask[batch_index, path_index] = is_real_path

        # FactKG adaptation chosen in Cải tiến 15-7.md:
        # [CLS] Claim [SEP] Path_i [SEP]. Each pair is truncated independently.
        tokenized_pairs = self.tokenizer(
            flat_claims,
            text_pair=flat_paths,
            padding="longest",
            max_length=self.max_length,
            truncation=True,
            return_tensors="pt",
        )

        pair_inputs = {
            key: value.reshape(batch_size, path_count, -1).to(DEVICE)
            for key, value in tokenized_pairs.items()
        }

        # [GEAR-LITE E4/E5] Tokenize each claim once for the separate-claim
        # encoder. E1/E2/E3 simply ignore this field, keeping their behavior
        # and checkpoints unchanged. The encoder itself is shared in E4/E5.
        tokenized_claims = self.tokenizer(
            [feature["c"] for feature in features],
            padding="longest",
            max_length=self.max_length,
            truncation=True,
            return_tensors="pt",
        )
        claim_inputs = {key: value.to(DEVICE) for key, value in tokenized_claims.items()}

        batch = {
            "pair_inputs": pair_inputs,
            "claim_inputs": claim_inputs,
            "path_mask": path_mask.to(DEVICE),
            "label": torch.tensor(
                [_label_to_int(feature["l"]) for feature in features],
                dtype=torch.long,
                device=DEVICE,
            ),
        }
        if self.include_sparse_adjacency:
            # [GEAR-LITE E6] Construct edges from raw serialized paths, before
            # BERT tokenization loses entity/relation positions. The helper
            # returns [B,K,K], leaves padding disconnected, and applies only
            # self-loop/shared-intermediate/tail-head rules.
            sparse_adjacency = build_sparse_path_adjacency(
                paths_per_claim,
                path_count,
                [feature.get("claim_entities", []) for feature in features],
            )
            batch["sparse_adjacency"] = sparse_adjacency.to(DEVICE)
        if self.split == "test":
            batch["type"] = torch.tensor(
                [feature["type"] for feature in features],
                dtype=torch.long,
                device=DEVICE,
            )
        return batch
# [GEAR-LITE E1/E2/E3/E4/E5/E6 END]

data_path = args.data_path
kg_path = args.kg_path

if not data_path:
    parser.error('--data_path is required')
if not args.skip_prepare_input and not kg_path:
    parser.error('--kg_path is required unless --skip_prepare_input is used')

def _resolve_candid_path(default_name, cli_path):
    if cli_path:
        return cli_path
    return os.path.join(".", default_name)

train_candid_path = _resolve_candid_path("train_candid_paths.bin", args.train_candid_path)
dev_candid_path = _resolve_candid_path("dev_candid_paths.bin", args.dev_candid_path)
test_candid_path = _resolve_candid_path(f"test_candid_paths_top{args.n_candid}.bin", args.test_candid_path)

# Generate candidates only once, then use --skip_prepare_input for every E0/E1/E2
# run that belongs to the same comparison. This freezes the candidate set.
if not args.skip_prepare_input:
    prepare_input(data_path, kg_path, args.n_candid)

if args.prepare_only:
    print("Candidate artifacts prepared:")
    print(f"  train: {train_candid_path}")
    print(f"  dev:   {dev_candid_path}")
    print(f"  test:  {test_candid_path}")
    raise SystemExit(0)

for candid_path in (train_candid_path, dev_candid_path, test_candid_path):
    if not os.path.isfile(candid_path):
        raise FileNotFoundError(
            f"Candidate artifact not found: {candid_path}. "
            "Generate it once without --skip_prepare_input, or pass the correct "
            "--train_candid_path/--dev_candid_path/--test_candid_path."
        )

with open(os.path.join(data_path, 'factkg_train.pickle'), 'rb') as pkf:
    db = pkl.load(pkf)
    print(f"Load train DB, # samples: {len(db)}")

with open(train_candid_path, 'rb') as pkf:
    candids = pkl.load(pkf)
    print(f"Load train candids from {train_candid_path}, # samples: {len(candids)}")
    
# [DISABLED] Phase 1.2/1.3 pruning — tạm ẩn để test 5-hop trên code gốc
# if args.prune_noise:
#     from prune_candid_paths import prune_candids
#     candids = prune_candids(candids, max_hops=3)
#     print("Pruned train candids.")

train_claims = list()
train_evis = list()
train_labels = list() 
train_entity_sets = list()

for i, (s, m) in enumerate(db.items()):
    train_claims.append(s)
    train_labels.append(m["Label"])
    train_entity_sets.append(m.get("Entity_set", []))
    evis = [candids[s]["connected"], candids[s]["walkable"]]
    train_evis.append(evis)

with open(os.path.join(data_path, 'factkg_dev.pickle'), 'rb') as pkf:
    db = pkl.load(pkf)
    print(f"Load dev DB, # samples: {len(db)}")

with open(dev_candid_path, 'rb') as pkf:
    candids = pkl.load(pkf)
    print(f"Load dev candids from {dev_candid_path}, # samples: {len(candids)}")

# [DISABLED] Phase 1.2/1.3 pruning — tạm ẩn để test 5-hop trên code gốc
# if args.prune_noise:
#     from prune_candid_paths import prune_candids
#     candids = prune_candids(candids, max_hops=3)
#     print("Pruned dev candids.")

dev_claims = list()
dev_evis = list()
dev_labels = list()
dev_entity_sets = list()

for i, (s, m) in enumerate(db.items()):
    dev_claims.append(s)
    dev_labels.append(m["Label"])
    dev_entity_sets.append(m.get("Entity_set", []))
    evis = [candids[s]["connected"], candids[s]["walkable"]]
    dev_evis.append(evis)

with open(os.path.join(data_path, 'factkg_test.pickle'), 'rb') as pkf:
    db = pkl.load(pkf)
    print(f"Load Test DB, # samples: {len(db)}")

with open(test_candid_path, 'rb') as pkf:
    candids = pkl.load(pkf)
    print(f"Load test candids from {test_candid_path}, # samples: {len(candids)}")

# [DISABLED] Phase 1.2/1.3 pruning — tạm ẩn để test 5-hop trên code gốc
# if args.prune_noise:
#     from prune_candid_paths import prune_candids
#     candids = prune_candids(candids, max_hops=3)
#     print("Pruned test candids.")

test_claims = list()
test_evis = list()
test_labels = list()
test_types = list()
test_entity_sets = list()
for i, (s, m) in enumerate(db.items()):
    test_claims.append(s)
    test_labels.append(m["Label"])
    test_entity_sets.append(m.get("Entity_set", []))
    evis = [candids[s]["connected"], candids[s]["walkable"]]
    test_evis.append(evis)
    test_types.append(m["types"])

tokenizer = AutoTokenizer.from_pretrained(PT_CLS)

is_pair_model = args.model_cls in PAIR_MODEL_NAMES
dataset_class = PairDataset if is_pair_model else Dataset
loader_batch_size = args.pair_batch_size if is_pair_model else args.batch_size
if args.gradient_accumulation_steps > 0:
    gradient_accumulation_steps = args.gradient_accumulation_steps
else:
    # Pair models need a smaller physical batch because one claim expands to K
    # BERT inputs. Accumulation keeps optimizer updates comparable with E0.
    gradient_accumulation_steps = max(
        1, (args.batch_size + loader_batch_size - 1) // loader_batch_size
    )

if is_pair_model and args.max_paths == 0:
    print(
        "[Warning] --max_paths=0 encodes every candidate path. "
        "Use a positive K (for example 32) if GPU memory is insufficient."
    )
    if args.model_cls == "gearlite_v5":
        print(
            "[Warning] gearlite_v5 also builds pairwise ERNet scores with "
            "O(K^2) memory. Keep --max_paths=32 unless an explicit larger-K "
            "ablation fits the GPU."
        )

print(
    f"Run config: model={args.model_cls}, device={DEVICE}, seed={args.seed}, "
    f"max_paths={'all' if args.max_paths == 0 else args.max_paths}, "
    f"physical_batch={loader_batch_size}, "
    f"gradient_accumulation={gradient_accumulation_steps}, "
    f"effective_claim_batch~={loader_batch_size * gradient_accumulation_steps}"
)

train_dataset = dataset_class(
    "train", train_claims, train_evis, train_labels, max_paths=args.max_paths,
    entity_sets=train_entity_sets,
)
if is_pair_model:
    train_collator = PairDataCollator(
        "train", tokenizer, args.pair_max_length,
        include_sparse_adjacency=(args.model_cls == "gearlite_v5"),
    )
else:
    train_collator = DataCollator("train", tokenizer)

train_generator = torch.Generator()
train_generator.manual_seed(args.seed)
train_loader = torch.utils.data.DataLoader(
    train_dataset,
    shuffle=True,
    batch_size=loader_batch_size,
    collate_fn=train_collator,
    drop_last=False,
    num_workers=0,
    pin_memory=False,
    generator=train_generator,
)

dev_dataset = dataset_class(
    "dev", dev_claims, dev_evis, dev_labels, max_paths=args.max_paths,
    entity_sets=dev_entity_sets,
)
if is_pair_model:
    dev_collator = PairDataCollator(
        "dev", tokenizer, args.pair_max_length,
        include_sparse_adjacency=(args.model_cls == "gearlite_v5"),
    )
else:
    dev_collator = DataCollator("dev", tokenizer)
dev_loader = torch.utils.data.DataLoader(
    dev_dataset,
    shuffle=False,
    batch_size=loader_batch_size,
    collate_fn=dev_collator,
    drop_last=False,
    num_workers=0,
    pin_memory=False
)

test_dataset = dataset_class(
    "test",
    test_claims,
    test_evis,
    test_labels,
    test_types,
    max_paths=args.max_paths,
    entity_sets=test_entity_sets,
)
if is_pair_model:
    test_collator = PairDataCollator(
        "test", tokenizer, args.pair_max_length,
        include_sparse_adjacency=(args.model_cls == "gearlite_v5"),
    )
else:
    test_collator = DataCollator("test", tokenizer)
test_loader = torch.utils.data.DataLoader(
    test_dataset,
    shuffle=False,
    batch_size=loader_batch_size,
    collate_fn=test_collator,
    drop_last=False,
    num_workers=0,
    pin_memory=False
)

class ConcatClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.config = AutoConfig.from_pretrained(PT_CLS)
        self.shallow_classifier = nn.Sequential(
                                    nn.Linear(self.config.hidden_size, self.config.hidden_size),
                                    nn.ReLU(),
                                    nn.Linear(self.config.hidden_size, 2)
                                )
        if args.scratch:
            print("Random init models")
            self.encoder = BertModel(self.config)
        else:
            self.encoder = AutoModel.from_pretrained(PT_CLS)
        self.loss_fct = nn.CrossEntropyLoss()
    
    def forward(
        self,
        inputs
    ):
        # process input
        cated_inputs = {k:torch.cat([inputs["claim"][k], inputs["evidence"][k]], dim=-1) for k in inputs["claim"]}
        encoder_outputs = self.encoder(
            **cated_inputs,
            return_dict=False
        )
        cls_output = encoder_outputs[0][:, 0]
        
        assert cls_output.shape[-1]==self.config.hidden_size
        
        logit = self.shallow_classifier(cls_output)
        loss = self.loss_fct(logit, inputs["label"])
        
        return loss, logit

class SentenceClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.config = AutoConfig.from_pretrained(PT_CLS)
        self.shallow_classifier = nn.Sequential(
                                    nn.Linear(self.config.hidden_size, self.config.hidden_size),
                                    nn.ReLU(),
                                    nn.Linear(self.config.hidden_size, 2)
                                )
        if args.scratch:
            print("Random init models")
            self.encoder = BertModel(self.config)
        else:
            self.encoder = AutoModel.from_pretrained(PT_CLS)
        self.loss_fct = nn.CrossEntropyLoss()
    
    def forward(
        self,
        inputs
    ):
        # process input
        cated_inputs = inputs["claim"]
        encoder_outputs = self.encoder(
            **cated_inputs,
            return_dict=False
        )
        cls_output = encoder_outputs[0][:, 0]
        
        assert cls_output.shape[-1]==self.config.hidden_size
        
        logit = self.shallow_classifier(cls_output)
        loss = self.loss_fct(logit, inputs["label"])
        
        return loss, logit


# ============================================================
# [GEAR-LITE E1/E2 START] Shared independent Claim-Path encoder
# Both ablations use exactly the same BERT and output MLP. Their only model
# difference is the path aggregator implemented in the two subclasses below.
# No ERNet/GNN or hard path selector is included in this version.
# ============================================================
class IndependentPathClassifierBase(nn.Module):
    def __init__(self):
        super().__init__()
        self.config = AutoConfig.from_pretrained(PT_CLS)
        if args.scratch:
            print("Random init models")
            self.encoder = BertModel(self.config)
        else:
            self.encoder = AutoModel.from_pretrained(PT_CLS)

        # Same verifier head for E1 and E2, so the aggregation method is the
        # controlled difference between the two experiments.
        self.shallow_classifier = nn.Sequential(
            nn.Linear(self.config.hidden_size, self.config.hidden_size),
            nn.ReLU(),
            nn.Linear(self.config.hidden_size, 2),
        )
        self.loss_fct = nn.CrossEntropyLoss()

    def encode_pairs(self, inputs):
        """Encode [B,K,L] pairs with one shared BERT and return [B,K,H]."""
        pair_inputs = inputs["pair_inputs"]
        if not pair_inputs:
            raise ValueError("pair_inputs cannot be empty")

        reference = next(iter(pair_inputs.values()))
        if reference.ndim != 3:
            raise ValueError(
                f"Expected pair input shape [B,K,L], got {tuple(reference.shape)}"
            )
        batch_size, path_count, sequence_length = reference.shape

        flat_inputs = {
            key: value.reshape(batch_size * path_count, sequence_length)
            for key, value in pair_inputs.items()
        }
        encoder_outputs = self.encoder(**flat_inputs, return_dict=False)
        # GEAR-Lite adaptation: fine-tune BERT end-to-end and use the raw final
        # CLS state. Original GEAR instead precomputed BERT pooled_output.
        path_vectors = encoder_outputs[0][:, 0].reshape(
            batch_size, path_count, self.config.hidden_size
        )

        expected_mask_shape = (batch_size, path_count)
        if tuple(inputs["path_mask"].shape) != expected_mask_shape:
            raise ValueError(
                f"Expected path_mask shape {expected_mask_shape}, "
                f"got {tuple(inputs['path_mask'].shape)}"
            )
        return path_vectors

    def encode_claims(self, inputs):
        """Encode standalone claims with the same BERT and return [B,H].

        This is used by GEARLite v3 and v4. Its representation is independent
        of candidate paths, unlike v2 where the claim condition is estimated
        by averaging Claim--Path vectors.
        """
        claim_inputs = inputs.get("claim_inputs")
        if not claim_inputs:
            raise ValueError(
                "claim_inputs is required for separate-claim attention; "
                "use PairDataCollator to build the batch"
            )

        reference = next(iter(claim_inputs.values()))
        if reference.ndim != 2:
            raise ValueError(
                f"Expected claim input shape [B,L], got {tuple(reference.shape)}"
            )

        encoder_outputs = self.encoder(**claim_inputs, return_dict=False)
        return encoder_outputs[0][:, 0]  # [B, H]

    def classify(self, pooled_evidence, labels):
        logits = self.shallow_classifier(pooled_evidence)
        loss = self.loss_fct(logits, labels)
        return loss, logits


class IndependentPathMeanClassifier(IndependentPathClassifierBase):
    """E1: independent Claim-Path BERT encoding followed by masked mean."""

    def forward(self, inputs):
        path_vectors = self.encode_pairs(inputs)
        path_mask = inputs["path_mask"].to(path_vectors.dtype).unsqueeze(-1)

        # E1 — every real path has equal weight; padded paths contribute zero.
        denominator = path_mask.sum(dim=1).clamp_min(1.0)
        pooled_evidence = (path_vectors * path_mask).sum(dim=1) / denominator
        return self.classify(pooled_evidence, inputs["label"])


class GEARLiteClassifier(IndependentPathClassifierBase):
    """E2: independent Claim-Path encoding plus masked path attention."""

    def __init__(self):
        super().__init__()
        # GEAR-inspired *Lite* scorer (H -> 64 -> 1). h_i is already
        # claim-conditioned inside pair BERT, so E2 does not add GEAR's separate
        # claim-vector attention or its ERNet evidence graph.
        self.path_attention = nn.Sequential(
            nn.Linear(self.config.hidden_size, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )
        self.last_attention_weights = None

    def forward(self, inputs):
        path_vectors = self.encode_pairs(inputs)
        path_mask = inputs["path_mask"].bool()

        # E2 — learn one relevance score per path, mask padding before softmax,
        # then compute the weighted evidence vector used by the same MLP as E1.
        attention_scores = self.path_attention(path_vectors).squeeze(-1)
        attention_scores = attention_scores.masked_fill(
            ~path_mask, torch.finfo(attention_scores.dtype).min
        )
        attention_weights = torch.softmax(attention_scores, dim=1)

        # Defensive renormalization also makes the aggregation finite if a
        # custom collator ever supplies an all-padding sample.
        attention_weights = attention_weights * path_mask.to(attention_weights.dtype)
        attention_weights = attention_weights / attention_weights.sum(
            dim=1, keepdim=True
        ).clamp_min(torch.finfo(attention_weights.dtype).eps)

        pooled_evidence = torch.sum(
            path_vectors * attention_weights.unsqueeze(-1), dim=1
        )
        self.last_attention_weights = attention_weights.detach()
        return self.classify(pooled_evidence, inputs["label"])
# [GEAR-LITE E1/E2 END]


# ============================================================
# [GEAR-LITE E3 START] Claim-conditioned attention (GEAR-style aggregator)
# Unlike E2, E3 concatenates an explicit claim vector with each path vector
# before computing the attention score:  score_j = MLP([claim || h_j]).
# This follows the original GEAR paper's aggregator formula and gives the
# attention layer direct access to claim-level signals (e.g. negation words)
# when deciding which paths are relevant.
# ============================================================
class GEARLiteV2Classifier(IndependentPathClassifierBase):
    """E3: Pair encoding + claim-conditioned masked path attention.

    Key difference from E2 (GEARLiteClassifier):
    - E2 computes  score_j = MLP(h_j)           — path-only scoring
    - E3 computes  score_j = MLP([claim || h_j]) — claim-conditioned scoring

    The claim vector is derived as the masked mean of all path vectors. Since
    each h_i = BERT([CLS] Claim [SEP] Path_i [SEP]), the mean over valid paths
    acts as a stable, claim-dominated representation that is consistent across
    all K paths for the same claim.
    """

    def __init__(self):
        super().__init__()
        # Claim-conditioned scorer: [claim(768) || path(768)] -> 64 -> 1
        self.path_attention = nn.Sequential(
            nn.Linear(self.config.hidden_size * 2, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )
        self.last_attention_weights = None

    def forward(self, inputs):
        path_vectors = self.encode_pairs(inputs)   # [B, K, H]
        path_mask = inputs["path_mask"].bool()      # [B, K]

        # --- Derive a stable claim representation ---
        # Mean-pool over valid path vectors. Each h_i already contains the
        # claim via pair BERT; averaging K of them yields a claim-dominated
        # vector because the claim tokens are shared across all K inputs.
        mask_float = path_mask.to(path_vectors.dtype).unsqueeze(-1)  # [B, K, 1]
        claim_vector = (
            (path_vectors * mask_float).sum(dim=1)
            / mask_float.sum(dim=1).clamp_min(1.0)
        )  # [B, H]

        # --- Claim-conditioned attention scoring ---
        # Broadcast claim to [B, K, H] then concat with path: [B, K, 2H]
        claim_expanded = claim_vector.unsqueeze(1).expand_as(path_vectors)
        conditioned_input = torch.cat([claim_expanded, path_vectors], dim=-1)

        attention_scores = self.path_attention(conditioned_input).squeeze(-1)  # [B, K]
        attention_scores = attention_scores.masked_fill(
            ~path_mask, torch.finfo(attention_scores.dtype).min
        )
        attention_weights = torch.softmax(attention_scores, dim=1)

        # Defensive renormalization (same as E2).
        attention_weights = attention_weights * path_mask.to(attention_weights.dtype)
        attention_weights = attention_weights / attention_weights.sum(
            dim=1, keepdim=True
        ).clamp_min(torch.finfo(attention_weights.dtype).eps)

        pooled_evidence = torch.sum(
            path_vectors * attention_weights.unsqueeze(-1), dim=1
        )  # [B, H]
        self.last_attention_weights = attention_weights.detach()
        return self.classify(pooled_evidence, inputs["label"])
# [GEAR-LITE E3 END]


# ============================================================
# [GEAR-LITE E4 START] Separate-claim conditioned attention
# E4 keeps the exact E3 scoring form score_j = MLP([c || h_j]), but obtains
# c = BERT([CLS] Claim [SEP]) instead of c = mean_j h_j. The BERT weights are
# shared: this is one encoder called for claims and Claim--Path pairs, not two
# independently trained BERT models.
# ============================================================
class GEARLiteV3Classifier(IndependentPathClassifierBase):
    """E4: Pair encoding + separately encoded claim-conditioned attention.

    h_j = BERT([CLS] Claim [SEP] Path_j [SEP])
    c   = BERT([CLS] Claim [SEP])
    score_j = MLP([c || h_j])

    The final verifier remains unchanged: it classifies the attention-pooled
    path vector. This makes E4 a focused ablation of how the claim condition
    is formed, rather than a simultaneous change to candidate retrieval or the
    classifier head.
    """

    def __init__(self):
        super().__init__()
        # Same scorer width as E3/v2: [claim(H) || path(H)] -> 64 -> 1.
        self.path_attention = nn.Sequential(
            nn.Linear(self.config.hidden_size * 2, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )
        self.last_attention_weights = None
        self.last_claim_vector = None

    def forward(self, inputs):
        path_vectors = self.encode_pairs(inputs)  # [B, K, H]
        claim_vector = self.encode_claims(inputs)  # [B, H], independent of paths
        path_mask = inputs["path_mask"].bool()  # [B, K]

        if claim_vector.shape != (path_vectors.shape[0], path_vectors.shape[2]):
            raise ValueError(
                "Standalone claim vectors must have shape [B,H] matching "
                f"path vectors [B,K,H]; got {tuple(claim_vector.shape)} and "
                f"{tuple(path_vectors.shape)}"
            )

        # [GEAR-LITE E4] Use both the standalone claim representation c and
        # each Claim--Path representation h_j to score path relevance.
        claim_expanded = claim_vector.unsqueeze(1).expand_as(path_vectors)
        conditioned_input = torch.cat([claim_expanded, path_vectors], dim=-1)
        attention_scores = self.path_attention(conditioned_input).squeeze(-1)
        attention_scores = attention_scores.masked_fill(
            ~path_mask, torch.finfo(attention_scores.dtype).min
        )
        attention_weights = torch.softmax(attention_scores, dim=1)
        attention_weights = attention_weights * path_mask.to(attention_weights.dtype)
        attention_weights = attention_weights / attention_weights.sum(
            dim=1, keepdim=True
        ).clamp_min(torch.finfo(attention_weights.dtype).eps)

        pooled_evidence = torch.sum(
            path_vectors * attention_weights.unsqueeze(-1), dim=1
        )  # [B, H]
        self.last_attention_weights = attention_weights.detach()
        self.last_claim_vector = claim_vector.detach()
        return self.classify(pooled_evidence, inputs["label"])
# [GEAR-LITE E4 END]


# ============================================================
# [GEAR-LITE E5 START] Hybrid claim + candidate-set attention
# E5 is the next ablation after E3/v2 and E4/v3. It retains the independent
# Claim vector from E4, while restoring E3's summary of all valid candidate
# paths. Retrieval, path encoder, masked softmax and final verifier stay fixed.
# ============================================================
class GEARLiteV4Classifier(IndependentPathClassifierBase):
    """E5: separate Claim + candidate-set mean + per-path attention.

    h_j     = BERT([CLS] Claim [SEP] Path_j [SEP])
    c_claim = BERT([CLS] Claim [SEP])
    c_set   = masked_mean_j(h_j)
    score_j = MLP([c_claim || c_set || h_j])

    c_claim preserves claim-only semantics such as negation. c_set gives the
    scorer global context about the candidate pool, which E4/v3 deliberately
    does not see. The final classifier still receives only the attention-pooled
    evidence vector, making this a focused attention-scorer ablation.
    """

    def __init__(self):
        super().__init__()
        # [GEAR-LITE E5] Each score receives three H-dimensional vectors:
        # Claim-only c_claim, candidate-set summary c_set, and path h_j.
        self.path_attention = nn.Sequential(
            nn.Linear(self.config.hidden_size * 3, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )
        self.last_attention_weights = None
        self.last_claim_vector = None
        self.last_candidate_set_vector = None

    def forward(self, inputs):
        path_vectors = self.encode_pairs(inputs)  # [B, K, H]
        claim_vector = self.encode_claims(inputs)  # [B, H], Claim-only
        path_mask = inputs["path_mask"].bool()  # [B, K]

        if claim_vector.shape != (path_vectors.shape[0], path_vectors.shape[2]):
            raise ValueError(
                "Standalone claim vectors must have shape [B,H] matching "
                f"path vectors [B,K,H]; got {tuple(claim_vector.shape)} and "
                f"{tuple(path_vectors.shape)}"
            )

        # [GEAR-LITE E5] Average real paths only. Padding vectors cannot alter
        # c_set, even when claims in the same batch have different path counts.
        mask_float = path_mask.to(path_vectors.dtype).unsqueeze(-1)  # [B,K,1]
        candidate_set_vector = (
            (path_vectors * mask_float).sum(dim=1)
            / mask_float.sum(dim=1).clamp_min(1.0)
        )  # [B,H]

        # [GEAR-LITE E5] score_j = MLP([c_claim || c_set || h_j]).
        claim_expanded = claim_vector.unsqueeze(1).expand_as(path_vectors)
        set_expanded = candidate_set_vector.unsqueeze(1).expand_as(path_vectors)
        conditioned_input = torch.cat(
            [claim_expanded, set_expanded, path_vectors], dim=-1
        )  # [B,K,3H]
        attention_scores = self.path_attention(conditioned_input).squeeze(-1)
        attention_scores = attention_scores.masked_fill(
            ~path_mask, torch.finfo(attention_scores.dtype).min
        )
        attention_weights = torch.softmax(attention_scores, dim=1)
        attention_weights = attention_weights * path_mask.to(attention_weights.dtype)
        attention_weights = attention_weights / attention_weights.sum(
            dim=1, keepdim=True
        ).clamp_min(torch.finfo(attention_weights.dtype).eps)

        pooled_evidence = torch.sum(
            path_vectors * attention_weights.unsqueeze(-1), dim=1
        )  # [B,H]
        self.last_attention_weights = attention_weights.detach()
        self.last_claim_vector = claim_vector.detach()
        self.last_candidate_set_vector = candidate_set_vector.detach()
        return self.classify(pooled_evidence, inputs["label"])
# [GEAR-LITE E5 END]


# ============================================================
# [GEAR-LITE E6 START] V4 + sparse ERNet message passing
# E6 preserves V4's Claim-only vector, candidate-set mean and final attention.
# Its sole architectural change is h_i -> h'_i through one sparse ERNet layer
# before c_set and attention are computed. This is a FactKG adaptation of GEAR:
# candidate paths are nodes, while graph edges are built in PairDataCollator.
# ============================================================
class GEARLiteV5SparseERNetClassifier(GEARLiteV4Classifier):
    """E6: V4 attention preceded by one sparse GEAR-style ERNet layer.

    h_i      = BERT([CLS] Claim [SEP] Path_i [SEP])
    h'_i     = SparseERNet(h_i, graph_edges)
    c_claim  = BERT([CLS] Claim [SEP])
    c_set    = masked_mean_i(h'_i)
    score_i  = MLP([c_claim || c_set || h'_i])

    The scorer and classifier are inherited unchanged from V4. Therefore the
    V4-versus-V5 comparison isolates message passing between structurally
    related candidate paths, while retrieval/R3 and final path selection stay
    fixed.
    """

    def __init__(self):
        super().__init__()
        # One layer is the first, controlled sparse-ERNet ablation. It uses
        # GEAR's 64-unit pairwise attention MLP without full K-by-K edges.
        self.sparse_ernet = SparseERNet(
            hidden_size=self.config.hidden_size,
            num_layers=1,
            attention_hidden_size=64,
        )
        self.last_sparse_adjacency = None

    def forward(self, inputs):
        path_vectors = self.encode_pairs(inputs)  # [B,K,H]
        path_mask = inputs["path_mask"].bool()  # [B,K]
        sparse_adjacency = inputs.get("sparse_adjacency")
        if sparse_adjacency is None:
            raise ValueError(
                "GEARLite v5 requires sparse_adjacency. Use PairDataCollator "
                "with include_sparse_adjacency=True."
            )

        # [GEAR-LITE E6] Related paths exchange messages before the V4
        # candidate-set summary and final claim-conditioned path attention.
        refined_path_vectors = self.sparse_ernet(
            path_vectors, path_mask, sparse_adjacency
        )  # [B,K,H], h'_i
        claim_vector = self.encode_claims(inputs)  # [B,H], Claim-only c_claim

        if claim_vector.shape != (
            refined_path_vectors.shape[0], refined_path_vectors.shape[2]
        ):
            raise ValueError(
                "Standalone claim vectors must match sparse ERNet output; got "
                f"{tuple(claim_vector.shape)} and "
                f"{tuple(refined_path_vectors.shape)}"
            )

        # V4's c_set is intentionally recomputed from the ERNet-updated paths.
        # Padding is masked, so claims with fewer than K candidates are not
        # biased toward zero vectors from another item in the batch.
        mask_float = path_mask.to(refined_path_vectors.dtype).unsqueeze(-1)
        candidate_set_vector = (
            (refined_path_vectors * mask_float).sum(dim=1)
            / mask_float.sum(dim=1).clamp_min(1.0)
        )  # [B,H]

        claim_expanded = claim_vector.unsqueeze(1).expand_as(refined_path_vectors)
        set_expanded = candidate_set_vector.unsqueeze(1).expand_as(
            refined_path_vectors
        )
        conditioned_input = torch.cat(
            [claim_expanded, set_expanded, refined_path_vectors], dim=-1
        )  # [B,K,3H]
        attention_scores = self.path_attention(conditioned_input).squeeze(-1)
        attention_scores = attention_scores.masked_fill(
            ~path_mask, torch.finfo(attention_scores.dtype).min
        )
        attention_weights = torch.softmax(attention_scores, dim=1)
        attention_weights = attention_weights * path_mask.to(attention_weights.dtype)
        attention_weights = attention_weights / attention_weights.sum(
            dim=1, keepdim=True
        ).clamp_min(torch.finfo(attention_weights.dtype).eps)

        pooled_evidence = torch.sum(
            refined_path_vectors * attention_weights.unsqueeze(-1), dim=1
        )  # [B,H]
        self.last_attention_weights = attention_weights.detach()
        self.last_claim_vector = claim_vector.detach()
        self.last_candidate_set_vector = candidate_set_vector.detach()
        self.last_sparse_adjacency = sparse_adjacency.detach()
        return self.classify(pooled_evidence, inputs["label"])
# [GEAR-LITE E6 END]


model = {
    "sent":SentenceClassifier,
    "cat":ConcatClassifier,
    # [GEAR-LITE E1] Pair encoder + masked mean.
    "mean":IndependentPathMeanClassifier,
    # [GEAR-LITE E2] Pair encoder + masked attention (GEAR-Lite v1).
    "gearlite":GEARLiteClassifier,
    # [GEAR-LITE E3] Pair encoder + claim-conditioned attention (GEAR-Lite v2).
    "gearlite_v2":GEARLiteV2Classifier,
    # [GEAR-LITE E4] Pair encoder + separately encoded claim-conditioned attention.
    "gearlite_v3":GEARLiteV3Classifier,
    # [GEAR-LITE E5] Pair encoder + separate Claim + candidate-set mean attention.
    "gearlite_v4":GEARLiteV4Classifier,
    # [GEAR-LITE E6] V4 plus one sparse ERNet layer over candidate paths.
    "gearlite_v5":GEARLiteV5SparseERNetClassifier,
}[args.model_cls]().to(DEVICE)

use_amp = bool(args.amp and DEVICE.type == "cuda")
if args.amp and not use_amp:
    print("[Warning] --amp requested but CUDA is unavailable; using full precision.")
scaler = torch.cuda.amp.GradScaler(enabled=use_amp)

# E2 initializes an extra attention module after the shared BERT/MLP. Reset the
# training RNG so that this extra initialization does not shift BERT dropout
# randomness relative to E1 when both runs use the same seed.
torch.manual_seed(args.seed)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(args.seed)

best = -1
best_epoch = -1
stop_counter = 0
best_param = None
run_tag_parts = [args.model_cls]
if args.run_name:
    run_tag_parts.append(args.run_name)
run_tag_parts.append(f"seed{args.seed}")
run_tag = "_".join(run_tag_parts)
# Tên có run_name + seed để R1/R2/R3 và các seed không ghi đè file nhau.
valid_prediction_path = os.path.join(args.output_dir, f"valid_pred_{run_tag}.bin")
test_prediction_path = os.path.join(args.output_dir, f"test_pred_{run_tag}.bin")
best_checkpoint_path = os.path.join(args.output_dir, f"best_model_{run_tag}.pth")


def _macro_f1(predictions, labels):
    """Binary macro-F1 over the False (0) and True (1) FactKG labels."""
    predictions = predictions.long().reshape(-1)
    labels = labels.long().reshape(-1)
    f1_values = []
    for label_id in (0, 1):
        true_positive = ((predictions == label_id) & (labels == label_id)).sum().item()
        false_positive = ((predictions == label_id) & (labels != label_id)).sum().item()
        false_negative = ((predictions != label_id) & (labels == label_id)).sum().item()
        denominator = 2 * true_positive + false_positive + false_negative
        f1_values.append(0.0 if denominator == 0 else (2 * true_positive) / denominator)
    return sum(f1_values) / len(f1_values)


REASONING_TYPE_NAMES = {
    0: "one-hop",
    1: "multi-hop",
    2: "conjunction",
    3: "existence",
    4: "negation",
}

if args.test_only:
    if not os.path.isfile(args.checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found: {args.checkpoint_path}")
    loaded_checkpoint = torch.load(args.checkpoint_path, map_location="cpu")
    if isinstance(loaded_checkpoint, dict) and "model_state_dict" in loaded_checkpoint:
        # Different GEARLite variants can have compatible tensor shapes while
        # implementing different claim-conditioning computations. Refuse an
        # accidental cross-model checkpoint load so evaluation remains a valid
        # architecture ablation. Plain legacy state_dict files remain allowed.
        checkpoint_model_cls = loaded_checkpoint.get("model_cls")
        if checkpoint_model_cls and checkpoint_model_cls != args.model_cls:
            raise ValueError(
                "Checkpoint model_cls does not match the requested model: "
                f"checkpoint={checkpoint_model_cls!r}, requested={args.model_cls!r}. "
                "Train a new checkpoint for a cross-architecture comparison."
            )
        best_param = loaded_checkpoint["model_state_dict"]
        best_epoch = int(loaded_checkpoint.get("best_epoch", -1))
        best = float(loaded_checkpoint.get("best_dev_accuracy", float("nan")))
    elif isinstance(loaded_checkpoint, dict):
        # Hỗ trợ cả state_dict PyTorch thuần nếu người dùng đã có checkpoint cũ.
        best_param = loaded_checkpoint
    else:
        raise ValueError("Checkpoint must be a state_dict or contain model_state_dict")
    model.load_state_dict(best_param)
    model.eval()
    print(f"Loaded checkpoint for test only: {args.checkpoint_path}")
else:
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, betas=(0.5, 0.999))
    for epoch in range(args.epoch):
        model.train()
        losses = list()
        scores = list()
        optimizer.zero_grad(set_to_none=True)
        accumulated_batches = 0
        for i, batch in tqdm(enumerate(train_loader), total=len(train_loader), desc=f"Train {epoch}", leave=False):
            with torch.autocast(device_type=DEVICE.type, dtype=torch.float16, enabled=use_amp):
                loss, logit = model(batch)
            scaler.scale(loss).backward()
            accumulated_batches += 1

            should_update = (
                accumulated_batches == gradient_accumulation_steps
                or i == len(train_loader) - 1
            )
            if should_update:
                # Average gradients over the actual number of accumulated batches,
                # including the shorter final group at the end of an epoch.
                scaler.unscale_(optimizer)
                for parameter in model.parameters():
                    if parameter.grad is not None:
                        parameter.grad.div_(accumulated_batches)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
                accumulated_batches = 0

            losses.append(loss.item())
            pred = logit.max(dim=1).indices.bool()
            gt = batch["label"].bool()
            score = pred == gt
            scores.append(score.detach().cpu().reshape(-1))
            progress_interval = max(1, len(train_loader) // 5)
            if i % progress_interval == 0:
                loss = f"{torch.Tensor(losses).mean().item():.5f}"
                accuracy = f"{torch.cat(scores).float().mean().item():.4f}"
                print(f"Epoch {colored(epoch, 'yellow')}, Loss: {colored(loss, 'yellow')}, Acc: {colored(accuracy, 'yellow')}")
                losses = list()
                scores = list()

        model.eval()
        with torch.no_grad():
            scores = list()
            gts = list()
            dev_predictions = list()
            for i, batch in tqdm(enumerate(dev_loader), total=len(dev_loader), desc="Dev", leave=False):
                with torch.autocast(device_type=DEVICE.type, dtype=torch.float16, enabled=use_amp):
                    _, logit = model(batch)
                pred = logit.max(dim=1).indices.bool()
                gt = batch["label"].bool()
                score = pred == gt
                dev_predictions.append(pred.cpu().reshape(-1))
                scores.append(score.cpu().reshape(-1))
                gts.append(gt.cpu().reshape(-1))
            accuracy = torch.cat(scores).float().mean().item()
            str_accuracy = f"{accuracy:.4f}"
            print(f"Dev Acc: {colored(str_accuracy, 'green')}")

        if best < accuracy:
            best = accuracy
            best_epoch = epoch
            # Copy checkpoint tốt nhất sang CPU để không chiếm thêm VRAM và để
            # state tốt nhất không bị thay đổi bởi các epoch train sau.
            best_param = {
                name: value.detach().cpu().clone()
                for name, value in model.state_dict().items()
            }
            # Ghi ngay checkpoint dev tốt nhất. Neu nguoi dung dung run o
            # epoch sau, checkpoint cua epoch tot nhat da hoan tat van co the
            # dung voi --test_only thay vi mat toan bo tien trinh train.
            torch.save(
                {
                    "model_state_dict": best_param,
                    "best_epoch": best_epoch,
                    "best_dev_accuracy": best,
                    "model_cls": args.model_cls,
                    "seed": args.seed,
                },
                best_checkpoint_path,
            )
            print(
                f"Saved current best-dev checkpoint: epoch={best_epoch}, "
                f"dev_acc={best:.4f} -> {best_checkpoint_path}"
            )
            # Prediction dev phải đi cùng chính epoch đã tạo best_param.
            with open(valid_prediction_path, "wb") as pkf:
                result = {
                    "hit": [i for i, hit in enumerate(torch.cat(scores)) if hit],
                    "prediction": torch.cat(dev_predictions).long(),
                    "label": torch.cat(gts).long(),
                    "accuracy": accuracy,
                    "epoch": epoch,
                }
                pkl.dump(result, pkf)
            stop_counter = 0
        else:
            stop_counter += 1
        if stop_counter > 3:
            break

    if best_param is None:
        raise RuntimeError("No checkpoint was produced; --epoch must be at least 1")

    # Lưu checkpoint ra file: R2/R3 sẽ nạp đúng model R1 này ở --test_only.
    torch.save(
        {
            "model_state_dict": best_param,
            "best_epoch": best_epoch,
            "best_dev_accuracy": best,
            "model_cls": args.model_cls,
            "seed": args.seed,
        },
        best_checkpoint_path,
    )
    model.load_state_dict(best_param)
    model.eval()
    print(f"Selected best checkpoint: epoch={best_epoch}, dev_acc={best:.4f}")
    print(f"Saved best-dev checkpoint to: {best_checkpoint_path}")

with torch.no_grad():
    scores = list()
    rtypes = list()
    gts = list()
    predictions = list()
    for i, batch in tqdm(enumerate(test_loader), total=len(test_loader), desc=f"Test", leave=False):
        rtype = batch.pop("type")
        with torch.autocast(device_type=DEVICE.type, dtype=torch.float16, enabled=use_amp):
            _, logit = model(batch)
        pred = logit.max(dim=1).indices.bool()
        gt = batch["label"].bool()
        score = pred==gt
        predictions.append(pred.cpu().reshape(-1))
        gts.append(gt.cpu().reshape(-1))
        scores.append(score.cpu().reshape(-1))
        rtypes.append(rtype.cpu().reshape(-1))
    total_score = torch.cat(scores).float()
    total_rtype = torch.cat(rtypes)
    total_predictions = torch.cat(predictions).long()
    total_labels = torch.cat(gts).long()
    for rt in total_rtype.unique():
        idcs = total_rtype==rt
        type_id = rt.item()
        type_name = REASONING_TYPE_NAMES[type_id]
        print(f"-- # examples in {rt.item()}: {idcs.sum().item()} --")
        print(
            f"{colored(type_name, 'yellow')} (type={type_id}) | "
            f"Acc: {total_score[idcs].mean().item():.4f} | "
            f"Macro-F1: {_macro_f1(total_predictions[idcs], total_labels[idcs]):.4f}"
        )

    accuracy = total_score.mean().item()
    macro_f1 = _macro_f1(total_predictions, total_labels)
    print(f"Total Test Acc: {colored(f'{accuracy:.4f}', 'green')}")
    print(f"Total Test Macro-F1: {colored(f'{macro_f1:.4f}', 'green')}")

with open(test_prediction_path, "wb") as pkf:
    result = {
        "hit": [i for i, hit in enumerate(total_score.bool()) if hit],
        "prediction": total_predictions,
        "label": total_labels,
        "reasoning_type": total_rtype,
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "best_epoch": best_epoch,
        "best_dev_accuracy": best,
    }
    pkl.dump(result, pkf)

if not args.test_only:
    print(f"Saved best-dev predictions to: {valid_prediction_path}")
print(f"Saved test predictions to: {test_prediction_path}")
