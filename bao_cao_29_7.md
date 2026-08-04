# Bao cao 29/7: Faico-Lite x GEARLite E2

## Muc tieu

Tuan nay thu nghiem y tuong tu Faico o tang retrieval, khong thay doi relation
predictor, hop predictor hay kien truc GEARLite E2. Dau vao test cua ba run
giu co dinh top-5 relation, hop prediction, KG, `max_paths=32`, seed va
checkpoint E2 R1.

Faico-Lite thay heuristic traversal cu bang duyet KG co thu tu xac dinh: giu
serialized path rieng biet, khong chon tail ngau nhien va uu tien `connected`
truoc `walkable`. De phu hop voi E2, artifact chi luu toi 32 path ma model co
the encode; khi da du 32 connected path, retrieval dung som cho claim do.

## Ba cau hinh candidate path

| Run | Candidate path test | Cach danh gia |
|---|---|---|
| R1 | Dung do dai hop H du doan, relation khong lap (`k=1`) | Train E2 tren candidate R1, chon best dev checkpoint, test R1 |
| R2 | Sinh path do dai 1 den H, `k=1` | Dung checkpoint R1, chi thay candidate test |
| R3 | R2 + moi relation duoc lap toi 2 lan (`k=2`) | Dung checkpoint R1, chi thay candidate test |

R2 va R3 la retrieval ablation: test claim, label va model giong R1. Chi
evidence path dua vao E2 thay doi, nen chenh lech diem phan anh tac dong cua
quy tac sinh/loc candidate path.

## Du lieu va checkpoint R1

- Candidate R1 da tao xong cho train (86,367), dev (13,266) va test (9,041).
- Retrieval report: artifact luu 1,745,603 path train, 251,585 path dev va
  154,200 path test sau gioi han top-32.
- E2 train toi da 5 epoch, seed 42; best checkpoint la epoch 0 voi Dev Acc
  `0.9408`. R2/R3 dung dung checkpoint nay.

## Ket qua test

| Run | Best dev Acc | Test Acc | Test Macro-F1 | Multi-hop Acc | Multi-hop Macro-F1 |
|---|---:|---:|---:|---:|---:|
| R1 | 0.9408 | 0.8391 | 0.8377 | 0.7567 | 0.7483 |
| R2 | Dung checkpoint R1 | 0.8454 | 0.8442 | 0.7828 | 0.7773 |
| R3 | Dung checkpoint R1 | 0.8460 | 0.8449 | 0.7860 | 0.7808 |

| Reasoning type | R1 Acc / F1 | R2 Acc / F1 | R3 Acc / F1 |
|---|---:|---:|---:|
| One-hop | 0.9044 / 0.9043 | 0.9080 / 0.9079 | 0.9080 / 0.9079 |
| Multi-hop | 0.7567 / 0.7483 | 0.7828 / 0.7773 | 0.7860 / 0.7808 |
| Conjunction | 0.8358 / 0.8283 | 0.8351 / 0.8278 | 0.8351 / 0.8278 |
| Existence | 0.9437 / 0.9437 | 0.9448 / 0.9448 | 0.9448 / 0.9448 |
| Negation | 0.7998 / 0.7983 | 0.8014 / 0.7999 | 0.8014 / 0.7999 |

## Danh gia

- R2 tang so voi R1: Test Acc `+0.0063`, Macro-F1 `+0.0065`; multi-hop tang
  manh nhat, Acc `+0.0261` va Macro-F1 `+0.0290`.
- R3 la ket qua tot nhat: so voi R1, Test Acc `+0.0069`, Macro-F1 `+0.0072`;
  multi-hop Acc `+0.0293` va Macro-F1 `+0.0325`.
- R3 hon R2 chu yeu o multi-hop (`+0.0032` Acc, `+0.0035` F1), trong khi cac
  reasoning type khac giu gan nhu nguyen. Dieu nay phu hop voi gia thuyet
  path ngan hon va relation lap co the khoi phuc proof path bi bo sot, thay vi
  tao nhieu nhieu cho cac case don gian.

Artifact, retrieval report va prediction duoc luu tai
`artifacts/faico_lite_top5/r1`, `r2` va `r3`.
