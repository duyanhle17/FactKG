"""P0 report: join FEVER predictions, bridges, gold bridges, token audit and V4 by claim text.

Every input except --factkg and --fever is optional; sections are skipped when missing.

  python analyze_p0.py --factkg DATA/factkg_dev.pickle \
      --fever OUT/p0_fever_dev/predictions.pkl \
      --bridges OUT/bridges_dev.pkl --gold OUT/gold_bridges_dev.pkl \
      --tokens OUT/p0_tokens_dev/per_claim.pkl --subgraphs SUBGRAPHS/subgraphs_one_hop_val.pkl \
      --v4 V4_RESULT.pkl --v4-data V4_DATA.pickle \
      --output-dir OUT/p0_report_dev
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict

from common import (GROUPS, build_input, evidence_of, five_group, fresh_dir, label_of, load_factkg,
                    load_walked, read_pickle, write_json)


def as_list(v):
    return v.tolist() if hasattr(v, "tolist") else list(v)


def pct(a, b):
    return f"{100 * a / b:.1f}%" if b else "—"


def load_v4(result_path, data_path):
    res = read_pickle(result_path)
    claims = list(read_pickle(data_path))
    preds = [int(x) for x in as_list(res["prediction"])]
    labels = [int(x) for x in as_list(res["label"])] if "label" in res else None
    if len(preds) != len(claims):
        raise ValueError("V4 predictions and V4 data differ in length")
    return {c: (p, None if labels is None else labels[i]) for i, (c, p) in enumerate(zip(claims, preds))}


def bridge_flags(entry):
    pairs = entry["pairs"]
    return {"direct": any(p["direct"] for p in pairs),
            "two_hop": any(p["n2"] for p in pairs),
            "three_hop": any(p["n3"] for p in pairs),
            "any_bridge": any(p["n2"] or p["n3"] for p in pairs),
            "truncated": any(p["three_hop_truncated"] or p["degree_truncated"] for p in pairs)}


def gold_seq_found(entry, record):
    """Does a bridge with exactly a gold relation sequence (>=2 hops) exist between claim entities?"""
    seqs = {(e, tuple(s)) for e, ss in (record.get("Evidence") or {}).items() for s in ss if len(s) >= 2}
    if not seqs:
        return None
    for p in entry["pairs"]:
        for table in (p["two_hop"], p["three_hop"]):
            for seq in table:
                if (p["a"], tuple(seq)) in seqs:
                    return True
                rev = tuple(r[1:] if r.startswith("~") else "~" + r for r in reversed(seq))
                if (p["b"], rev) in seqs:
                    return True
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--factkg", required=True)
    ap.add_argument("--fever", required=True, help="fever_predict.py predictions.pkl")
    ap.add_argument("--bridges")
    ap.add_argument("--gold")
    ap.add_argument("--tokens", help="token_audit.py per_claim.pkl")
    ap.add_argument("--subgraphs", help="one-hop subgraphs (needed with --gold and --tokens)")
    ap.add_argument("--v4")
    ap.add_argument("--v4-data", help="the data pickle V4 was evaluated on (defines its order)")
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()

    out_dir = fresh_dir(args.output_dir)
    rows = load_factkg(args.factkg)
    fever = read_pickle(args.fever)
    fpred = dict(zip(fever["claim"], fever["prediction"]))
    fprob = dict(zip(fever["claim"], fever["prob_true"]))
    bridges = read_pickle(args.bridges) if args.bridges else None
    gold = read_pickle(args.gold) if args.gold else None
    tokens = read_pickle(args.tokens) if args.tokens else None
    walked = load_walked(args.subgraphs, len(rows)) if args.subgraphs else None
    v4 = load_v4(args.v4, args.v4_data) if args.v4 else None

    lines, report = [], defaultdict(dict)
    lines.append(f"# P0 report — {args.factkg}\n")

    # 1. FEVER accuracy and confidence
    c = Counter()
    for claim, rec in rows:
        if claim not in fpred:
            continue
        g, y = five_group(rec["types"]), label_of(rec)
        ok = fpred[claim] == y
        conf = abs(fprob[claim] - 0.5) < 0.25
        for k in (g, f"{g}/{'True' if y else 'False'}"):
            c[(k, "n")] += 1
            c[(k, "ok")] += ok
            c[(k, "lowconf")] += conf
            c[(k, "lowconf_err")] += conf and not ok
            c[(k, "err")] += not ok
    lines.append("## 1. FEVER BERT accuracy (low-confidence = |p-0.5| < 0.25)\n")
    lines.append("| group | n | acc | errors | low-conf | share of errors that are low-conf |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for g in GROUPS:
        for k in (g, f"{g}/True", f"{g}/False"):
            n = c[(k, "n")]
            if n:
                lines.append(f"| {k} | {n} | {pct(c[(k, 'ok')], n)} | {c[(k, 'err')]} | "
                             f"{pct(c[(k, 'lowconf')], n)} | {pct(c[(k, 'lowconf_err')], c[(k, 'err')])} |")
                report["fever"][k] = {"n": n, "acc": c[(k, "ok")] / n, "errors": c[(k, "err")]}

    # 2. Bridge statistics by group x label (KG-level, independent of the model)
    if bridges is not None:
        b = Counter()
        for claim, rec in rows:
            if claim not in bridges:
                continue
            g, y = five_group(rec["types"]), "True" if label_of(rec) else "False"
            f = bridge_flags(bridges[claim])
            k = f"{g}/{y}"
            b[(k, "n")] += 1
            for name, val in f.items():
                b[(k, name)] += val
            b[(k, "bridge_no_direct")] += f["any_bridge"] and not f["direct"]
            gs = gold_seq_found(bridges[claim], rec) if "Evidence" in rec else None
            if gs is not None:
                b[(k, "gold_seq_n")] += 1
                b[(k, "gold_seq_found")] += gs
        lines.append("\n## 2. Bridges in the KG between claim entities (by group / label)\n")
        lines.append("| group/label | n | direct | any 2-hop | any 3-hop | bridge & no direct | "
                     "gold rel-seq bridge found | search truncated |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
        for g in GROUPS:
            for y in ("True", "False"):
                k = f"{g}/{y}"
                n = b[(k, "n")]
                if not n:
                    continue
                lines.append(f"| {k} | {n} | {pct(b[(k, 'direct')], n)} | {pct(b[(k, 'two_hop')], n)} | "
                             f"{pct(b[(k, 'three_hop')], n)} | {pct(b[(k, 'bridge_no_direct')], n)} | "
                             f"{pct(b[(k, 'gold_seq_found')], b[(k, 'gold_seq_n')])} | "
                             f"{pct(b[(k, 'truncated')], n)} |")
                report["bridges"][k] = {key: b[(k, key)] for key in
                                        ("n", "direct", "two_hop", "three_hop", "bridge_no_direct",
                                         "gold_seq_n", "gold_seq_found", "truncated")}

    # 3. Multi-hop error decomposition with gold bridges (dev only)
    if gold is not None and walked is not None:
        d = Counter()
        examples = defaultdict(list)
        for (claim, rec), w in zip(rows, walked):
            if five_group(rec["types"]) != "multi-hop" or claim not in gold or claim not in fpred:
                continue
            y = label_of(rec)
            gb = gold[claim]
            text = build_input(claim, evidence_of(w))
            visible = text[:tokens[claim]["cut_char"]] if tokens and claim in tokens else text
            mids = {x for p in gb["connected"] for x in p[2:-1:2]}
            if not gb["connected"] and y == 1:
                cat = "A_gold_bridge_not_in_KG"
            elif not gb["connected"]:
                cat = "F_false_no_gold_bridge(expected)"
            elif not any(repr(x) in text for x in mids):
                cat = "B_bridge_node_absent_from_onehop_input"
            elif not any(repr(x) in visible for x in mids):
                cat = "C_bridge_node_cut_by_512"
            else:
                cat = "D_bridge_node_visible"
            ok = fpred[claim] == y
            key = f"{'True' if y else 'False'}/{cat}"
            d[(key, "n")] += 1
            d[(key, "err")] += not ok
            if not ok and len(examples[key]) < 3:
                examples[key].append(claim)
        lines.append("\n## 3. Multi-hop: where is the gold bridge? (FEVER errors per bucket)\n")
        lines.append("| label/bucket | n | FEVER errors | error rate |")
        lines.append("|---|---:|---:|---:|")
        for key in sorted({k for k, _ in d}):
            lines.append(f"| {key} | {d[(key, 'n')]} | {d[(key, 'err')]} | {pct(d[(key, 'err')], d[(key, 'n')])} |")
            report["multihop_buckets"][key] = {"n": d[(key, "n")], "errors": d[(key, "err")],
                                               "examples": examples[key]}
        lines.append("\nB/C/D use the bridge node string inside the one-hop input as a proxy for "
                     "'BERT could see the bridge'. If most errors are in B/C, evidence access is the bottleneck (H1).")

    # 4. FEVER vs V4 complementarity
    if v4 is not None:
        v = Counter()
        mismatch = 0
        for claim, rec in rows:
            if claim not in v4 or claim not in fpred:
                continue
            y = label_of(rec)
            p4, y4 = v4[claim]
            mismatch += y4 is not None and y4 != y
            g = five_group(rec["types"])
            f_ok, v_ok = fpred[claim] == y, p4 == y
            for k in (g, "overall"):
                v[(k, "n")] += 1
                v[(k, "fever")] += f_ok
                v[(k, "v4")] += v_ok
                v[(k, "both")] += f_ok and v_ok
                v[(k, "fever_only")] += f_ok and not v_ok
                v[(k, "v4_only")] += v_ok and not f_ok
        lines.append(f"\n## 4. FEVER BERT vs R3/V4 (label mismatches between files: {mismatch})\n")
        lines.append("| group | n | FEVER | V4 | both | FEVER only | V4 only | oracle (either) |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
        for k in (*GROUPS, "overall"):
            n = v[(k, "n")]
            if n:
                orc = v[(k, "both")] + v[(k, "fever_only")] + v[(k, "v4_only")]
                lines.append(f"| {k} | {n} | {pct(v[(k, 'fever')], n)} | {pct(v[(k, 'v4')], n)} | "
                             f"{v[(k, 'both')]} | {v[(k, 'fever_only')]} | {v[(k, 'v4_only')]} | {pct(orc, n)} |")
                report["v4"][k] = {key: v[(k, key)] for key in ("n", "fever", "v4", "both", "fever_only", "v4_only")}
        if mismatch:
            lines.append("\n**WARNING:** labels differ for some claims — check that --v4-data matches --v4.")

    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(report, out_dir / "report.json")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
