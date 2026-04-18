import json
import pickle as pkl
from random import choice
from itertools import permutations, chain
from termcolor import colored
from tqdm.auto import tqdm
import os

# ============================================================
# Phase 1.1 — Relation Blacklist & Super-Node Detection
# ============================================================
# Relations that only reflect Wikipedia page structure, not facts.
RELATION_BLACKLIST = [
    "wikiPageWikiLink",
    "wikiPageRedirects",
    "wikiPageExternalLink",
    "wasDerivedFrom",
]

SUPER_NODE_DEGREE_THRESHOLD = 2000


def _clean_kg(raw_kg):
    """Remove blacklisted relations from every entity in the KG dict using substring match."""
    removed = 0
    for entity in raw_kg:
        # Substring match covers 'dbo:wikiPageWikiLink', '~wikiPage...', 'http://...', etc.
        bad_rels = [r for r in raw_kg[entity] if any(bad in r for bad in RELATION_BLACKLIST)]
        for r in bad_rels:
            del raw_kg[entity][r]
            removed += 1
    print(f"[Phase 1.1] Removed {removed} blacklisted relation entries from KG.")
    return raw_kg


def _find_super_nodes(raw_kg, threshold=SUPER_NODE_DEGREE_THRESHOLD):
    """Identify entities whose total edge count exceeds the threshold."""
    super_nodes = set()
    for entity in raw_kg:
        degree = sum(len(tails) for tails in raw_kg[entity].values())
        if degree > threshold:
            super_nodes.add(entity)
    print(f"[Phase 1.1] Detected {len(super_nodes)} super-nodes (degree > {threshold}).")
    return super_nodes


class KG():
    def __init__(self, kg, super_nodes=None, claim_entities=None):
        super().__init__()
        self.kg = kg
        self.super_nodes = super_nodes if super_nodes is not None else set()
        # claim_entities is set per-search call, not at init
        self.claim_entities = claim_entities if claim_entities is not None else set()
        
    def search(self, ents, rels, claim_text=""):
        connected = list()
        walkable = list()
        seen = dict()
        # Build a lowercased token set from claim text for super-node gating
        self.claim_entities = set(e.lower().replace("_", " ") for e in ents)
        
        for e in ents:
            if e in rels:
                for path in rels[e]:
                    leaf = ents[:]
                    leaf.remove(e)
                    result = self.walk(start=e, path=path, ends=leaf)
                    if result != (None, None):
                        if result[1] is not None:
                            query = str(sorted([result[1][0], result[1][-1]]))
                            if query not in seen:
                                conn_with_rel = result[1][:1]+list(chain(*[[r, e] for r, e in zip(path, result[1][1:])]))
                                connected.append(conn_with_rel)
                                seen[query] = None
                        if result[0][0] != result[0][-1]:
                            query = str(sorted([result[0][0], result[0][-1]]))
                            if query not in seen:
                                walk_with_rel = result[0][:1]+list(chain(*[[r, e] for r, e in zip(path, result[0][1:])]))
                                walkable.append(walk_with_rel)
                                seen[query] = None
                
        return {"connected":connected, "walkable":walkable}
                
    def walk(self, start, path, ends=None):
        branches = [[start,],]
        for r in path:
            updated_branches = list()
            for branch in branches:
                h = branch[-1]
                ts = self.get_tail(h, r)
                if (r == path[-1]) and ts:
                    rand_branch = branch+[choice(list(ts.keys())),]
                    for e in ends:
                        if e in ts:
                            return rand_branch, branch+[e,]
                    return rand_branch, None
                else:
                    if ts:
                        for t in ts:
                            # Phase 1.1 — Block super-nodes unless they
                            # are directly mentioned in the claim entities.
                            if t in self.super_nodes:
                                t_norm = t.lower().replace("_", " ")
                                if t_norm not in self.claim_entities:
                                    continue
                            updated_branches.append(branch+[t,])
            if len(updated_branches) <= len(branches):
                return None, None
            branches = updated_branches

    def get_tail(self, h, r):
        if h in self.kg:
            if r in self.kg[h]:
                return {x:None for x in self.kg[h][r]}
            else:
                return {}
        else:
            return {}    

def prepare_input(data_path, kg_path):
    predicted_rs = list()

    with open("../retrieve/model/relation_predict/test_relations_top3.json") as jsf:
        js = json.load(jsf)
            
    for idx in js["claims"]:
        predicted_rs.append((idx, js["claims"][idx], js["output"][idx])) 

    predicted_hops = list()

    with open("../retrieve/model/hop_predict/predictions_hop.json") as jsf:
        js = json.load(jsf)
            
    for idx in js["claims"]:
        predicted_hops.append((idx, js["claims"][idx], js["predict"][idx])) 

    with open(kg_path, "rb") as pkf:
        raw_kg = pkl.load(pkf)
    # Phase 1.1 — Clean KG and detect super-nodes once
    raw_kg = _clean_kg(raw_kg)
    super_nodes = _find_super_nodes(raw_kg)
    kg = KG(raw_kg, super_nodes=super_nodes)

    search_results = dict()

    with open(os.path.join(data_path, 'factkg_train.pickle'), "rb") as pkf:
        db = pkl.load(pkf)

    for i, (claim, elem) in tqdm(enumerate(db.items()), total=len(db)):
        ents = elem["Entity_set"]
        rels = elem["Evidence"]
        search_results[claim] = kg.search(ents, rels)
            
    assert len(search_results)==len(db)
    with open("./train_candid_paths.bin", "wb") as pkf:
        pkl.dump(search_results, pkf)

    with open(os.path.join(data_path, 'factkg_dev.pickle'), "rb") as pkf:
        db = pkl.load(pkf)
    kg_dev = KG(raw_kg, super_nodes=super_nodes)

    search_results = dict()

    for i, (claim, elem) in tqdm(enumerate(db.items()), total=len(db)):
        ents = elem["Entity_set"]
        rels = elem["Evidence"]
        search_results[claim] = kg_dev.search(ents, rels)
            
    assert len(search_results)==len(db)
    with open("./dev_candid_paths.bin", "wb") as pkf:
        pkl.dump(search_results, pkf)

    predicted_rs = dict()

    with open("../retrieve/model/relation_predict/test_relations_top3.json") as jsf:
        js = json.load(jsf)
            
    for idx in js["claims"]:
        predicted_rs[js["claims"][idx]] =  js["output"][idx]

    predicted_hops = dict()

    with open("../retrieve/model/hop_predict/predictions_hop.json") as jsf:
        js = json.load(jsf)
            
    for idx in js["claims"]:
        predicted_hops[js["claims"][idx]] =  js["predict"][idx]
        
    with open(os.path.join(data_path, 'factkg_test.pickle'), "rb") as pkf:
        db = pkl.load(pkf)
    kg_test = KG(raw_kg, super_nodes=super_nodes)

    search_results = dict()

    for i, elem in tqdm(enumerate(db.items()), total=len(db)):
        ents = elem[-1]["Entity_set"]
        candids = predicted_rs[elem[0]]
        hop = predicted_hops[elem[0]]
        claim = elem[0]
        
        rels = {e:list(permutations(candids, r=hop)) for e in ents}
        
        search_results[claim] = kg_test.search(ents, rels)

    assert len(search_results)==len(db)
    
    with open("./test_candid_paths_top3.bin", "wb") as pkf:
        pkl.dump(search_results, pkf)