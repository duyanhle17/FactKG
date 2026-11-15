# P0 report — ../fever2026_official/runnable/data/factkg/factkg_test.pickle

## 1. FEVER BERT accuracy (low-confidence = |p-0.5| < 0.25)

| group | n | acc | errors | low-conf | share of errors that are low-conf |
|---|---:|---:|---:|---:|---:|
| one-hop | 1914 | 95.5% | 86 | 3.5% | 39.5% |
| one-hop/True | 1061 | 97.6% | 25 | 2.6% | 40.0% |
| one-hop/False | 853 | 92.8% | 61 | 4.6% | 39.3% |
| multi-hop | 1874 | 80.7% | 362 | 9.8% | 23.5% |
| multi-hop/True | 962 | 74.5% | 245 | 11.2% | 16.7% |
| multi-hop/False | 912 | 87.2% | 117 | 8.3% | 37.6% |
| conjunction | 3069 | 97.1% | 88 | 2.2% | 26.1% |
| conjunction/True | 1358 | 98.5% | 21 | 2.3% | 33.3% |
| conjunction/False | 1711 | 96.1% | 67 | 2.1% | 23.9% |
| existence | 870 | 97.4% | 23 | 2.5% | 26.1% |
| existence/True | 414 | 98.6% | 6 | 1.4% | 33.3% |
| existence/False | 456 | 96.3% | 17 | 3.5% | 23.5% |
| negation | 1314 | 91.6% | 110 | 9.0% | 37.3% |
| negation/True | 603 | 89.9% | 61 | 11.3% | 34.4% |
| negation/False | 711 | 93.1% | 49 | 7.0% | 40.8% |

## 4. FEVER BERT vs R3/V4 (label mismatches between files: 0)

| group | n | FEVER | V4 | both | FEVER only | V4 only | oracle (either) |
|---|---:|---:|---:|---:|---:|---:|---:|
| one-hop | 1914 | 95.5% | 91.6% | 1685 | 143 | 69 | 99.1% |
| multi-hop | 1874 | 80.7% | 81.2% | 1271 | 241 | 250 | 94.0% |
| conjunction | 3069 | 97.1% | 84.0% | 2530 | 451 | 49 | 98.7% |
| existence | 870 | 97.4% | 94.9% | 811 | 36 | 15 | 99.1% |
| negation | 1314 | 91.6% | 88.4% | 1093 | 111 | 69 | 96.9% |
| overall | 9041 | 92.6% | 86.7% | 7390 | 982 | 452 | 97.6% |
