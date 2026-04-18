import torch
import re
import argparse
import pickle as pkl
from itertools import chain
from dataclasses import dataclass
from tqdm import trange, tqdm
from random import choices
import torch.nn as nn
from termcolor import colored
from transformers import BertModel, AutoModel, AutoTokenizer, PreTrainedTokenizerBase, AutoConfig, AutoModel
from preprocess import prepare_input
from prune_candid_paths import prune_candids
import os


# ============================================================
# Phase 2 — Soft Flatten Utilities
# ============================================================

def clean_kg_text(text: str) -> str:
    """Clean a KG entity or relation string for BERT.
    - Remove DBpedia prefixes (dbo:, dbp:)
    - Replace underscores with spaces
    - Split CamelCase: birthPlace -> birth Place -> birth place
    - Remove Wikipedia parenthetical disambiguators: Washington_(state) -> Washington
    """
    text = text.replace("dbo:", "").replace("dbp:", "")
    # Remove parenthetical disambiguation e.g. _(state), _(company)
    text = re.sub(r'_?\([^)]*\)', '', text)
    text = text.replace("_", " ")
    # Split CamelCase: birthPlace -> birth Place
    text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)
    # Remove leading ~ (reverse relation marker) for display
    text = text.lstrip("~")
    return text.strip()


def soft_flatten_path(path: list) -> str:
    """Convert a raw KG path into a clean, lightly formatted string.
    
    Example:
        ['Barack_Obama', 'birthPlace', 'Honolulu', 'locatedIn', 'Hawaii']
        -> 'Barack Obama birth Place Honolulu . Honolulu located In Hawaii'
    
    Each hop (Entity-Relation-Entity triple) is separated by ' . '
    """
    cleaned = [clean_kg_text(x) for x in path]
    hops = []
    for i in range(0, len(cleaned) - 2, 2):
        subj = cleaned[i]
        rel = cleaned[i + 1]
        obj = cleaned[i + 2]
        hops.append(f"{subj} {rel} {obj}")
    return " . ".join(hops) if hops else " ".join(cleaned)


parser = argparse.ArgumentParser()
parser.add_argument('--data_path', type=str, help='')
parser.add_argument('--kg_path', type=str, help='')
parser.add_argument('--lr', default=5e-5, type=float, help='')
parser.add_argument('--model_cls', default="cat", type=str, help='')
parser.add_argument('--epoch', default=10, type=int, help='')
# parser.add_argument('--db_name', default="", type=str, help='')
parser.add_argument('--n_candid', default="3", type=str, help='')
parser.add_argument('--scratch', action='store_true', help='')
parser.add_argument('--prune_noise', action='store_true', help='Filter noisy candidate paths in memory before training')
parser.add_argument('--train_candid_path', default="", type=str, help='Optional path to train candidate paths (.bin)')
parser.add_argument('--dev_candid_path', default="", type=str, help='Optional path to dev candidate paths (.bin)')
parser.add_argument('--test_candid_path', default="", type=str, help='Optional path to test candidate paths (.bin)')
args = parser.parse_args()

torch.manual_seed(42)

PT_CLS = "bert-base-cased"

class Dataset(torch.utils.data.Dataset):
    def __init__(
        self,
        split: str,
        claims: list,
        evis: list,
        labels: list, 
        types: list = None,
    ):
        super().__init__()
        
        self.claims = claims
        self.labels = labels
        self.split = split
        self.evis = evis
        self.types = types
        
        assert len(self.evis) == len(self.claims)
        assert len(self.evis) == len(self.labels)
        if self.types is not None:
            assert len(self.evis) == len(self.types)
        
    def __len__(self):
        return len(self.evis)
    
    def __getitem__(self, i):

        if self.split == "test":
            if "negation" in self.types[i]:
                rtype = 4
            elif "num1" in self.types[i]:
                rtype = 0
            elif "multi hop" in self.types[i]:
                rtype = 1
            elif "multi claim" in self.types[i]:
                rtype = 2
            elif "existence" in self.types[i]:
                rtype = 3
            else:
                raise ValueError()

            # Phase 2 — Soft Flatten: convert each path to clean text
            conn_text = " | ".join([soft_flatten_path(c) for c in self.evis[i][0]])
            walk_text = " | ".join([soft_flatten_path(c) for c in self.evis[i][1]])
            sample = {
                "e": (conn_text, walk_text),
                "c":self.claims[i],
                "l":self.labels[i],
                "type":rtype,
            }
        else:
            # Phase 2 — Soft Flatten: convert each path to clean text
            conn_text = " | ".join([soft_flatten_path(c) for c in self.evis[i][0]])
            walk_text = " | ".join([soft_flatten_path(c) for c in self.evis[i][1]])
            sample = {
                "e": (conn_text, walk_text),
                "c":self.claims[i],
                "l":self.labels[i],
            }
        
        return sample
    
@dataclass
class DataCollator:
    split: str
    tokenizer: PreTrainedTokenizerBase

    def tensorize(self, batch):
        for k, v in batch.items():
            if isinstance(v, list):
                o = torch.tensor(v).cuda()
            else:
                o = {_k:_v.cuda() for _k, _v in v.items()}
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
        
        label = [int(x) for x in list(chain(*batch.pop("l")))]
            
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


data_path = args.data_path
kg_path = args.kg_path

def _resolve_candid_path(default_name, cli_path):
    if cli_path:
        return cli_path
    return os.path.join(".", default_name)

train_candid_path = _resolve_candid_path("train_candid_paths.bin", args.train_candid_path)
dev_candid_path = _resolve_candid_path("dev_candid_paths.bin", args.dev_candid_path)
test_candid_path = _resolve_candid_path(f"test_candid_paths_top{args.n_candid}.bin", args.test_candid_path)

prepare_input(data_path, kg_path)

with open(os.path.join(data_path, 'factkg_train.pickle'), 'rb') as pkf:
    db = pkl.load(pkf)
    print(f"Load train DB, # samples: {len(db)}")

with open(train_candid_path, 'rb') as pkf:
    candids = pkl.load(pkf)
    print(f"Load train candids from {train_candid_path}, # samples: {len(candids)}")
    
if args.prune_noise:
    from prune_candid_paths import prune_candids
    candids = prune_candids(candids, max_hops=3)
    print("Pruned train candids.")

train_claims = list()
train_evis = list()
train_labels = list() 

for i, (s, m) in enumerate(db.items()):
    train_claims.append(s)
    train_labels.append(m["Label"])
    evis = [candids[s]["connected"], candids[s]["walkable"]]
    train_evis.append(evis)

with open(os.path.join(data_path, 'factkg_dev.pickle'), 'rb') as pkf:
    db = pkl.load(pkf)
    print(f"Load dev DB, # samples: {len(db)}")

with open(dev_candid_path, 'rb') as pkf:
    candids = pkl.load(pkf)
    print(f"Load dev candids from {dev_candid_path}, # samples: {len(candids)}")

if args.prune_noise:
    from prune_candid_paths import prune_candids
    candids = prune_candids(candids, max_hops=3)
    print("Pruned dev candids.")

dev_claims = list()
dev_evis = list()
dev_labels = list()

for i, (s, m) in enumerate(db.items()):
    dev_claims.append(s)
    dev_labels.append(m["Label"])
    evis = [candids[s]["connected"], candids[s]["walkable"]]
    dev_evis.append(evis)

with open(os.path.join(data_path, 'factkg_test.pickle'), 'rb') as pkf:
    db = pkl.load(pkf)
    print(f"Load Test DB, # samples: {len(db)}")

with open(test_candid_path, 'rb') as pkf:
    candids = pkl.load(pkf)
    print(f"Load test candids from {test_candid_path}, # samples: {len(candids)}")

if args.prune_noise:
    from prune_candid_paths import prune_candids
    candids = prune_candids(candids, max_hops=3)
    print("Pruned test candids.")

test_claims = list()
test_evis = list()
test_labels = list()
test_types = list()
for i, (s, m) in enumerate(db.items()):
    test_claims.append(s)
    test_labels.append(m["Label"])
    evis = [candids[s]["connected"], candids[s]["walkable"]]
    test_evis.append(evis)
    test_types.append(m["types"])

tokenizer = AutoTokenizer.from_pretrained(PT_CLS)

train_dataset = Dataset("train", train_claims, train_evis, train_labels)
collator = DataCollator("train", tokenizer)
train_loader = torch.utils.data.DataLoader(
    train_dataset, 
    shuffle=True, 
    batch_size=32, 
    collate_fn=collator, 
    drop_last=True,
    num_workers=0, 
    pin_memory=False
)

dev_dataset = Dataset("dev", dev_claims, dev_evis, dev_labels)
collator = DataCollator("dev", tokenizer)
dev_loader = torch.utils.data.DataLoader(
    dev_dataset, 
    shuffle=False, 
    batch_size=32, 
    collate_fn=collator, 
    drop_last=True,
    num_workers=0, 
    pin_memory=False
)

test_dataset = Dataset("test", test_claims, test_evis, test_labels, test_types)
collator = DataCollator("test", tokenizer)
test_loader = torch.utils.data.DataLoader(
    test_dataset, 
    shuffle=False, 
    batch_size=32, 
    collate_fn=collator, 
    drop_last=True,
    num_workers=0, 
    pin_memory=False
)

print(test_dataset[-1])

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

model = {
    "sent":SentenceClassifier,
    "cat":ConcatClassifier,
}[args.model_cls]().cuda()
optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, betas=(0.5, 0.999))
best = -1
stop_counter = 0

for epoch in range(args.epoch):
    model.train()
    losses = list()
    scores = list()
    for i, batch in tqdm(enumerate(train_loader), total=len(train_loader), desc=f"Train {epoch}", leave=False):
        optimizer.zero_grad()
        loss, logit = model(batch)
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
        pred = logit.max(dim=1).indices.bool()
        gt = batch["label"].bool()
        score = pred==gt
        scores.append(score.detach().cpu().squeeze())
        if i%(len(train_loader)//5) == 0:
            loss = f"{torch.Tensor(losses).mean().item():.5f}"
            accuracy = f"{torch.cat(scores).float().mean().item():.4f}"
            print(f"Epoch {colored(epoch, 'yellow')}, Loss: {colored(loss, 'yellow')}, Acc: {colored(accuracy, 'yellow')}")
            losses = list()
            scores = list()
            
    model.eval()
    with torch.no_grad():
        scores = list()
        gts = list()
        for i, batch in tqdm(enumerate(dev_loader), total=len(dev_loader), desc=f"Dev", leave=False):
            _, logit = model(batch)
            pred = logit.max(dim=1).indices.bool()
            gt = batch["label"].bool()
            score = pred==gt
            scores.append(score.cpu().squeeze())
            gts.append(gt.cpu().squeeze())
        accuracy = torch.cat(scores).float().mean().item()
        str_accuracy = f"{accuracy:.4f}"
        print(f"Dev Acc: {colored(str_accuracy, 'green')}")

    with open('./valid_pred.bin', "wb") as pkf:
        result = {
            "hit": [i for i, hit in enumerate(torch.cat(scores)) if hit],
            "label": torch.cat(gts)
        }
        pkl.dump(result, pkf)

    if best < accuracy:
        best = accuracy
        best_param = model.state_dict()
        stop_counter = 0
    else:
        stop_counter += 1
    if stop_counter > 3:
        break

model.load_state_dict(best_param)
model.eval()

with torch.no_grad():
    scores = list()
    rtypes = list()
    gts = list()
    for i, batch in tqdm(enumerate(test_loader), total=len(test_loader), desc=f"Test", leave=False):
        rtype = batch.pop("type")
        _, logit = model(batch)
        pred = logit.max(dim=1).indices.bool()
        gt = batch["label"].bool()
        score = pred==gt
        gts.append(gt.cpu().squeeze())
        scores.append(score.cpu().squeeze())
        rtypes.append(rtype)
    total_score = torch.cat(scores).float()
    total_rtype = torch.cat(rtypes)
    for rt in total_rtype.unique():
        idcs = total_rtype==rt
        print(f"-- # examples in {rt.item()}: {idcs.sum().item()} --")
        print(f"Acc for type {colored(str(rt.item()), 'yellow')}: {total_score[idcs.cpu()].mean().item():.4f}")

    accuracy = f"{torch.cat(scores).float().mean().item():.4f}"
    print(f"Total Test Acc: {colored(accuracy, 'green')}") 

with open('./test_pred.bin', "wb") as pkf:
    result = {
        "hit": [i for i, hit in enumerate(total_score.bool()) if hit],
        "label": torch.cat(gts)
    }
    pkl.dump(result, pkf)