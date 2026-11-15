# P0 report — ../fever2026_official/runnable/data/factkg/factkg_dev.pickle

## 1. FEVER BERT accuracy (low-confidence = |p-0.5| < 0.25)

| group | n | acc | errors | low-conf | share of errors that are low-conf |
|---|---:|---:|---:|---:|---:|
| one-hop | 2547 | 94.5% | 141 | 4.4% | 26.2% |
| one-hop/True | 1299 | 98.1% | 25 | 3.3% | 40.0% |
| one-hop/False | 1248 | 90.7% | 116 | 5.6% | 23.3% |
| multi-hop | 3555 | 77.4% | 805 | 11.3% | 21.6% |
| multi-hop/True | 1819 | 68.1% | 581 | 12.8% | 17.6% |
| multi-hop/False | 1736 | 87.1% | 224 | 9.7% | 32.1% |
| conjunction | 4317 | 95.9% | 175 | 2.4% | 26.9% |
| conjunction/True | 1916 | 97.1% | 55 | 2.8% | 38.2% |
| conjunction/False | 2401 | 95.0% | 120 | 2.0% | 21.7% |
| existence | 930 | 96.8% | 30 | 2.7% | 56.7% |
| existence/True | 483 | 96.9% | 15 | 2.3% | 60.0% |
| existence/False | 447 | 96.6% | 15 | 3.1% | 53.3% |
| negation | 1917 | 91.3% | 167 | 9.0% | 38.3% |
| negation/True | 909 | 90.5% | 86 | 11.8% | 37.2% |
| negation/False | 1008 | 92.0% | 81 | 6.4% | 39.5% |

## 2. Bridges in the KG between claim entities (by group / label)

| group/label | n | direct | any 2-hop | any 3-hop | bridge & no direct | gold rel-seq bridge found | search truncated |
|---|---:|---:|---:|---:|---:|---:|---:|
| one-hop/True | 1299 | 99.3% | 41.4% | 37.5% | 0.3% | — | 0.0% |
| one-hop/False | 1248 | 22.7% | 10.9% | 43.8% | 35.3% | — | 0.0% |
| multi-hop/True | 1819 | 17.3% | 95.9% | 8.5% | 82.5% | 97.5% | 0.0% |
| multi-hop/False | 1736 | 4.3% | 34.6% | 33.6% | 50.1% | 29.1% | 0.0% |
| conjunction/True | 1916 | 99.8% | 99.8% | 64.6% | 0.2% | — | 0.0% |
| conjunction/False | 2401 | 68.2% | 78.6% | 80.9% | 31.8% | — | 0.0% |
| existence/True | 483 | 0.0% | 0.0% | 0.0% | 0.0% | — | 0.0% |
| existence/False | 447 | 0.0% | 0.0% | 0.0% | 0.0% | — | 0.0% |
| negation/True | 909 | 3.5% | 21.8% | 19.8% | 33.8% | 38.3% | 0.0% |
| negation/False | 1008 | 57.6% | 54.7% | 34.0% | 15.1% | 93.7% | 0.0% |

## 3. Multi-hop: where is the gold bridge? (FEVER errors per bucket)

| label/bucket | n | FEVER errors | error rate |
|---|---:|---:|---:|
| False/B_bridge_node_absent_from_onehop_input | 175 | 12 | 6.9% |
| False/C_bridge_node_cut_by_512 | 60 | 10 | 16.7% |
| False/D_bridge_node_visible | 308 | 65 | 21.1% |
| False/F_false_no_gold_bridge(expected) | 1193 | 137 | 11.5% |
| True/A_gold_bridge_not_in_KG | 7 | 0 | 0.0% |
| True/B_bridge_node_absent_from_onehop_input | 403 | 115 | 28.5% |
| True/C_bridge_node_cut_by_512 | 362 | 141 | 39.0% |
| True/D_bridge_node_visible | 1047 | 325 | 31.0% |

B/C/D use the bridge node string inside the one-hop input as a proxy for 'BERT could see the bridge'. If most errors are in B/C, evidence access is the bottleneck (H1).

## 4. FEVER BERT vs R3/V4 (label mismatches between files: 0)

| group | n | FEVER | V4 | both | FEVER only | V4 only | oracle (either) |
|---|---:|---:|---:|---:|---:|---:|---:|
| one-hop | 2547 | 94.5% | 91.8% | 2217 | 189 | 122 | 99.3% |
| multi-hop | 3555 | 77.4% | 72.7% | 2148 | 602 | 435 | 89.6% |
| conjunction | 4317 | 95.9% | 85.7% | 3576 | 566 | 124 | 98.8% |
| existence | 930 | 96.8% | 95.2% | 860 | 40 | 25 | 99.5% |
| negation | 1917 | 91.3% | 88.6% | 1610 | 140 | 88 | 95.9% |
| overall | 13266 | 90.1% | 84.5% | 10411 | 1537 | 794 | 96.1% |
