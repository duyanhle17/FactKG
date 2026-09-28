# Bước A — đọc lỗi Conjunction của V4

Chỉ các path từ vị trí 1 đến K mới đi vào V4. `connected` không đồng nghĩa với proof đủ các vế. Test không có Evidence vàng nên kết luận phải được kiểm tra thủ công. Nếu artifact đã bị giới hạn khi lưu, không thể biết có path nào nằm sau K nếu chỉ đọc artifact này; kiểm tra `store_max_paths` trong manifest R3.

K=32; seed lấy mẫu=42; Conjunction=3069 câu; mẫu=50 câu.

- true_to_false: n=387, 0 path=19, 0 connected=60, đúng K path=172
- true_to_true: n=971, 0 path=1, 0 connected=9, đúng K path=495
- false_to_true: n=103, 0 path=0, 0 connected=7, đúng K path=26

Điền `suspected_cause` trong CSV bằng một trong: `missing_relation`, `relation_but_no_kg_path`, `after_k`, `model_with_full_proof`, `unclear`. Chỉ chọn `model_with_full_proof` nếu đã tìm thấy proof cho tất cả vế trong các path V4 nhìn thấy.

## 1. true_to_false_connected — test index 6204

- Claim: The 11th Mississippi Infantry Monument, in Adams County, Pennsylvania, USA, was established in the year 2000.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["\"2000\"", "11th_Mississippi_Infantry_Monument", "Adams_County,_Pennsylvania", "\"United States\""]`
- Top relations: `["location", "open", "city", "material", "country"]`; H: 1
- Candidate: 1 connected + 1 walkable; V4 thấy 2; artifact còn 0 path sau K.

```text
01 connected: ["11th_Mississippi_Infantry_Monument", "country", "\"United States\""]
02 walkable: ["Adams_County,_Pennsylvania", "country", "United_States"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 2. true_to_false_connected — test index 5902

- Claim: Adare Manor is in the Irish speaking Republic of Ireland, where the leader is Enda Kenny.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["Republic_of_Ireland", "Irish_language", "Enda_Kenny", "Adare_Manor"]`
- Top relations: `["country", "language", "leaderName", "location", "leaderTitle"]`; H: 1
- Candidate: 3 connected + 11 walkable; V4 thấy 14; artifact còn 0 path sau K.

```text
01 connected: ["Adare_Manor", "country", "Republic_of_Ireland"]
02 connected: ["Republic_of_Ireland", "language", "Irish_language"]
03 connected: ["Republic_of_Ireland", "leaderName", "Enda_Kenny"]
04 walkable: ["Adare_Manor", "location", "Adare"]
05 walkable: ["Adare_Manor", "location", "County_Limerick"]
06 walkable: ["Republic_of_Ireland", "language", "English_language"]
07 walkable: ["Republic_of_Ireland", "leaderName", "Joan_Burton"]
08 walkable: ["Republic_of_Ireland", "leaderName", "Michael_D._Higgins"]
09 walkable: ["Republic_of_Ireland", "leaderTitle", "\"President\""]
10 walkable: ["Republic_of_Ireland", "leaderTitle", "\"Taoiseach\""]
11 walkable: ["Republic_of_Ireland", "leaderTitle", "\"Tánaiste\""]
12 walkable: ["Republic_of_Ireland", "leaderTitle", "President_of_Ireland"]
13 walkable: ["Republic_of_Ireland", "leaderTitle", "Taoiseach"]
14 walkable: ["Republic_of_Ireland", "leaderTitle", "Tánaiste"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 3. true_to_false_connected — test index 5945

- Claim: Adare Manor is located in the Republic of Ireland, the leader of this country is Enda Kenny and one of the languages used is English.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["Republic_of_Ireland", "Enda_Kenny", "Adare_Manor", "English_language"]`
- Top relations: `["~leader", "leaderTitle", "~language", "country", "~leaderName"]`; H: 1
- Candidate: 4 connected + 28 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 connected: ["Adare_Manor", "country", "Republic_of_Ireland"]
02 connected: ["Enda_Kenny", "~leader", "Republic_of_Ireland"]
03 connected: ["Enda_Kenny", "~leaderName", "Republic_of_Ireland"]
04 connected: ["English_language", "~language", "Republic_of_Ireland"]
05 walkable: ["Enda_Kenny", "~leader", "Department_of_the_Taoiseach"]
06 walkable: ["Enda_Kenny", "~leader", "European_Parliament_election,_2004_(Ireland)"]
07 walkable: ["Enda_Kenny", "~leader", "European_Parliament_election,_2009_(Ireland)"]
08 walkable: ["Enda_Kenny", "~leader", "European_Parliament_election,_2014_(Ireland)"]
09 walkable: ["Enda_Kenny", "~leader", "Fine_Gael"]
10 walkable: ["Enda_Kenny", "~leader", "Irish_local_elections,_2004"]
11 walkable: ["Enda_Kenny", "~leader", "Irish_local_elections,_2009"]
12 walkable: ["Enda_Kenny", "~leader", "Irish_local_elections,_2014"]
13 walkable: ["Enda_Kenny", "~leader", "Next_Irish_general_election"]
14 walkable: ["English_language", "~language", "$5_Cover"]
15 walkable: ["English_language", "~language", "%22...And_Ladies_of_the_Club%22"]
16 walkable: ["English_language", "~language", "%22B%22_Is_for_Burglar"]
17 walkable: ["English_language", "~language", "%22C%22_Is_for_Corpse"]
18 walkable: ["English_language", "~language", "%22D%22_Is_for_Deadbeat"]
19 walkable: ["English_language", "~language", "%22E%22_Is_for_Evidence"]
20 walkable: ["English_language", "~language", "%22F%22_Is_for_Fugitive"]
21 walkable: ["English_language", "~language", "%22G%22_Is_for_Gumshoe"]
22 walkable: ["English_language", "~language", "%22H%22_Is_for_Homicide"]
23 walkable: ["English_language", "~language", "%22I%22_Is_for_Innocent"]
24 walkable: ["English_language", "~language", "%22J%22_Is_for_Judgment"]
25 walkable: ["English_language", "~language", "%22K%22_Is_for_Killer"]
26 walkable: ["English_language", "~language", "%22L%22_Is_for_Lawless"]
27 walkable: ["English_language", "~language", "%22M%22_Is_for_Malice"]
28 walkable: ["English_language", "~language", "%22N%22_Is_for_Noose"]
29 walkable: ["English_language", "~language", "%22O%22_Is_for_Outlaw"]
30 walkable: ["English_language", "~language", "%22P%22_Is_for_Peril"]
31 walkable: ["English_language", "~language", "%22Q%22_Is_for_Quarry"]
32 walkable: ["English_language", "~language", "%22R%22_Is_for_Ricochet"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 4. true_to_false_connected — test index 5859

- Claim: The musical genre of Alfredo Zitarrosa is Candombe, he started out as a solo singer and is signed to the Uruguayan record label Orfeo.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["Alfredo_Zitarrosa", "Candombe", "Orfeo_(Uruguayan_record_label)", "\"solo_singer\""]`
- Top relations: `["genre", "~background", "recordLabel", "background", "~recordLabel"]`; H: 1
- Candidate: 5 connected + 27 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 connected: ["\"solo_singer\"", "~background", "Alfredo_Zitarrosa"]
02 connected: ["Alfredo_Zitarrosa", "genre", "Candombe"]
03 connected: ["Alfredo_Zitarrosa", "recordLabel", "Orfeo_(Uruguayan_record_label)"]
04 connected: ["Alfredo_Zitarrosa", "background", "\"solo_singer\""]
05 connected: ["Orfeo_(Uruguayan_record_label)", "~recordLabel", "Alfredo_Zitarrosa"]
06 walkable: ["\"solo_singer\"", "~background", "%22King%22_Bennie_Nawahi"]
07 walkable: ["\"solo_singer\"", "~background", "%22Weird_Al%22_Yankovic"]
08 walkable: ["\"solo_singer\"", "~background", "12_Gauge_(rapper)"]
09 walkable: ["\"solo_singer\"", "~background", "1987_(artist)"]
10 walkable: ["\"solo_singer\"", "~background", "2Mex"]
11 walkable: ["\"solo_singer\"", "~background", "2Play"]
12 walkable: ["\"solo_singer\"", "~background", "2_Chainz"]
13 walkable: ["\"solo_singer\"", "~background", "2_Pistols"]
14 walkable: ["\"solo_singer\"", "~background", "2face_Idibia"]
15 walkable: ["\"solo_singer\"", "~background", "360_(rapper)"]
16 walkable: ["\"solo_singer\"", "~background", "3D_Na'Tee"]
17 walkable: ["\"solo_singer\"", "~background", "40_Cal."]
18 walkable: ["\"solo_singer\"", "~background", "40_Glocc"]
19 walkable: ["\"solo_singer\"", "~background", "5Zic"]
20 walkable: ["\"solo_singer\"", "~background", "60_Second_Assassin_(emcee)"]
21 walkable: ["\"solo_singer\"", "~background", "6_Tre_G"]
22 walkable: ["\"solo_singer\"", "~background", "88-Keys"]
23 walkable: ["\"solo_singer\"", "~background", "9ice"]
24 walkable: ["\"solo_singer\"", "~background", "9th_Prince"]
25 walkable: ["\"solo_singer\"", "~background", "A*M*E"]
26 walkable: ["\"solo_singer\"", "~background", "A+_(rapper)"]
27 walkable: ["\"solo_singer\"", "~background", "A-L-X"]
28 walkable: ["\"solo_singer\"", "~background", "A-Lee"]
29 walkable: ["\"solo_singer\"", "~background", "A-Love"]
30 walkable: ["\"solo_singer\"", "~background", "A-Plus_(rapper)"]
31 walkable: ["\"solo_singer\"", "~background", "A-do"]
32 walkable: ["\"solo_singer\"", "~background", "A.B._Quintanilla"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 5. true_to_false_connected — test index 5980

- Claim: Steven T Seagle and Duncan Rouleau created Baymax which appeared in Big Hero 6.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["Big_Hero_6_(film)", "Steven_T._Seagle", "Baymax", "Duncan_Rouleau"]`
- Top relations: `["~creators", "creator", "~creator", "fullName", "creators"]`; H: 1
- Candidate: 8 connected + 24 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 connected: ["Baymax", "creator", "Duncan_Rouleau"]
02 connected: ["Baymax", "creator", "Steven_T._Seagle"]
03 connected: ["Baymax", "creators", "Duncan_Rouleau"]
04 connected: ["Baymax", "creators", "Steven_T._Seagle"]
05 connected: ["Duncan_Rouleau", "~creators", "Baymax"]
06 connected: ["Duncan_Rouleau", "~creator", "Baymax"]
07 connected: ["Steven_T._Seagle", "~creators", "Baymax"]
08 connected: ["Steven_T._Seagle", "~creator", "Baymax"]
09 walkable: ["Duncan_Rouleau", "~creators", "Aries_(comics)"]
10 walkable: ["Duncan_Rouleau", "~creators", "Axis_Amerika"]
11 walkable: ["Duncan_Rouleau", "~creators", "Big_Hero_6_(comics)"]
12 walkable: ["Duncan_Rouleau", "~creators", "Bridgette_Crosby"]
13 walkable: ["Duncan_Rouleau", "~creators", "GoGo_Tomago"]
14 walkable: ["Duncan_Rouleau", "~creators", "Hiro_Takachiho"]
15 walkable: ["Duncan_Rouleau", "~creators", "Honey_Lemon"]
16 walkable: ["Duncan_Rouleau", "~creator", "Aries_(comics)"]
17 walkable: ["Duncan_Rouleau", "~creator", "Bridgette_Crosby"]
18 walkable: ["Duncan_Rouleau", "~creator", "Honey_Lemon"]
19 walkable: ["Steven_T._Seagle", "~creators", "American_Virgin_(comics)"]
20 walkable: ["Steven_T._Seagle", "~creators", "Aries_(comics)"]
21 walkable: ["Steven_T._Seagle", "~creators", "Big_Hero_6_(comics)"]
22 walkable: ["Steven_T._Seagle", "~creators", "Flex_(comics)"]
23 walkable: ["Steven_T._Seagle", "~creators", "GoGo_Tomago"]
24 walkable: ["Steven_T._Seagle", "~creators", "Hiro_Takachiho"]
25 walkable: ["Steven_T._Seagle", "~creators", "Honey_Lemon"]
26 walkable: ["Steven_T._Seagle", "~creators", "Jack_O'Lantern_(DC_Comics)"]
27 walkable: ["Steven_T._Seagle", "~creators", "Murmur_(Marvel_Comics)"]
28 walkable: ["Steven_T._Seagle", "~creators", "Primal_Force"]
29 walkable: ["Steven_T._Seagle", "~creators", "Radius_(comics)"]
30 walkable: ["Steven_T._Seagle", "~creators", "Supergirl_(Cir-El)"]
31 walkable: ["Steven_T._Seagle", "~creator", "Aries_(comics)"]
32 walkable: ["Steven_T._Seagle", "~creator", "Flex_(comics)"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 6. true_to_false_connected — test index 5863

- Claim: Alfredo Zitarrosa's record label is RCA Records, his background includes solo singing and his musical genre is Milonga.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["Alfredo_Zitarrosa", "RCA_Records", "Milonga_(music)", "\"solo_singer\""]`
- Top relations: `["recordLabel", "~background", "~genre", "background", "genre"]`; H: 1
- Candidate: 5 connected + 27 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 connected: ["\"solo_singer\"", "~background", "Alfredo_Zitarrosa"]
02 connected: ["Alfredo_Zitarrosa", "recordLabel", "RCA_Records"]
03 connected: ["Alfredo_Zitarrosa", "background", "\"solo_singer\""]
04 connected: ["Alfredo_Zitarrosa", "genre", "Milonga_(music)"]
05 connected: ["Milonga_(music)", "~genre", "Alfredo_Zitarrosa"]
06 walkable: ["\"solo_singer\"", "~background", "%22King%22_Bennie_Nawahi"]
07 walkable: ["\"solo_singer\"", "~background", "%22Weird_Al%22_Yankovic"]
08 walkable: ["\"solo_singer\"", "~background", "12_Gauge_(rapper)"]
09 walkable: ["\"solo_singer\"", "~background", "1987_(artist)"]
10 walkable: ["\"solo_singer\"", "~background", "2Mex"]
11 walkable: ["\"solo_singer\"", "~background", "2Play"]
12 walkable: ["\"solo_singer\"", "~background", "2_Chainz"]
13 walkable: ["\"solo_singer\"", "~background", "2_Pistols"]
14 walkable: ["\"solo_singer\"", "~background", "2face_Idibia"]
15 walkable: ["\"solo_singer\"", "~background", "360_(rapper)"]
16 walkable: ["\"solo_singer\"", "~background", "3D_Na'Tee"]
17 walkable: ["\"solo_singer\"", "~background", "40_Cal."]
18 walkable: ["\"solo_singer\"", "~background", "40_Glocc"]
19 walkable: ["\"solo_singer\"", "~background", "5Zic"]
20 walkable: ["\"solo_singer\"", "~background", "60_Second_Assassin_(emcee)"]
21 walkable: ["\"solo_singer\"", "~background", "6_Tre_G"]
22 walkable: ["\"solo_singer\"", "~background", "88-Keys"]
23 walkable: ["\"solo_singer\"", "~background", "9ice"]
24 walkable: ["\"solo_singer\"", "~background", "9th_Prince"]
25 walkable: ["\"solo_singer\"", "~background", "A*M*E"]
26 walkable: ["\"solo_singer\"", "~background", "A+_(rapper)"]
27 walkable: ["\"solo_singer\"", "~background", "A-L-X"]
28 walkable: ["\"solo_singer\"", "~background", "A-Lee"]
29 walkable: ["\"solo_singer\"", "~background", "A-Love"]
30 walkable: ["\"solo_singer\"", "~background", "A-Plus_(rapper)"]
31 walkable: ["\"solo_singer\"", "~background", "A-do"]
32 walkable: ["\"solo_singer\"", "~background", "A.B._Quintanilla"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 7. true_to_false_connected — test index 6018

- Claim: MTU Friedrichshafen of Friedrichshafen, owned by Rolls-Royce Holdings, manufactures the A-Rosa Luna engine.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["A-Rosa_Luna", "Rolls-Royce_Holdings", "MTU_Friedrichshafen", "Friedrichshafen"]`
- Top relations: `["~manufacturer", "powerType", "manufacturer", "keyPerson", "fate"]`; H: 1
- Candidate: 1 connected + 22 walkable; V4 thấy 23; artifact còn 0 path sau K.

```text
01 connected: ["A-Rosa_Luna", "powerType", "MTU_Friedrichshafen"]
02 walkable: ["Friedrichshafen", "~manufacturer", "USS_Los_Angeles_(ZR-3)"]
03 walkable: ["Rolls-Royce_Holdings", "~manufacturer", "Allison_Model_250"]
04 walkable: ["Rolls-Royce_Holdings", "~manufacturer", "General_Electric/Rolls-Royce_F136"]
05 walkable: ["Rolls-Royce_Holdings", "~manufacturer", "Rolls-Royce_LiftSystem"]
06 walkable: ["Rolls-Royce_Holdings", "~manufacturer", "Rolls-Royce_MT30"]
07 walkable: ["Rolls-Royce_Holdings", "~manufacturer", "Rolls-Royce_Marine_Spey"]
08 walkable: ["Rolls-Royce_Holdings", "~manufacturer", "Rolls-Royce_Mustang_Mk.X"]
09 walkable: ["Rolls-Royce_Holdings", "~manufacturer", "Rolls-Royce_Pegasus"]
10 walkable: ["Rolls-Royce_Holdings", "~manufacturer", "Rolls-Royce_RB.183_Tay"]
11 walkable: ["Rolls-Royce_Holdings", "~manufacturer", "Rolls-Royce_RB211"]
12 walkable: ["Rolls-Royce_Holdings", "~manufacturer", "Rolls-Royce_RB282"]
13 walkable: ["Rolls-Royce_Holdings", "~manufacturer", "Rolls-Royce_RB3011"]
14 walkable: ["Rolls-Royce_Holdings", "~manufacturer", "Rolls-Royce_RR300"]
15 walkable: ["Rolls-Royce_Holdings", "~manufacturer", "Rolls-Royce_Trent"]
16 walkable: ["Rolls-Royce_Holdings", "~manufacturer", "Rolls-Royce_Trent_1000"]
17 walkable: ["Rolls-Royce_Holdings", "~manufacturer", "Rolls-Royce_Trent_500"]
18 walkable: ["Rolls-Royce_Holdings", "~manufacturer", "Rolls-Royce_Trent_700"]
19 walkable: ["Rolls-Royce_Holdings", "~manufacturer", "Rolls-Royce_Trent_800"]
20 walkable: ["Rolls-Royce_Holdings", "~manufacturer", "Rolls-Royce_Trent_900"]
21 walkable: ["Rolls-Royce_Holdings", "~manufacturer", "Rolls-Royce_Trent_XWB"]
22 walkable: ["Rolls-Royce_Holdings", "keyPerson", "Ian_Davis_(businessman)"]
23 walkable: ["Rolls-Royce_Holdings", "keyPerson", "Warren_East"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 8. true_to_false_connected — test index 5393

- Claim: Big Hero 6 with Alan Tudyk had a character called Baymax.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["Big_Hero_6_(film)", "Baymax", "Alan_Tudyk"]`
- Top relations: `["~starring", "starring", "runtime", "activeYearsEndYear", "writer"]`; H: 1
- Candidate: 2 connected + 30 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 connected: ["Alan_Tudyk", "~starring", "Big_Hero_6_(film)"]
02 connected: ["Big_Hero_6_(film)", "starring", "Alan_Tudyk"]
03 walkable: ["Alan_Tudyk", "~starring", "3:10_to_Yuma_(2007_film)"]
04 walkable: ["Alan_Tudyk", "~starring", "A_Knight's_Tale"]
05 walkable: ["Alan_Tudyk", "~starring", "Beautiful_Boy_(film)"]
06 walkable: ["Alan_Tudyk", "~starring", "Conception_(film)"]
07 walkable: ["Alan_Tudyk", "~starring", "Death_at_a_Funeral_(2007_film)"]
08 walkable: ["Alan_Tudyk", "~starring", "I,_Robot_(film)"]
09 walkable: ["Alan_Tudyk", "~starring", "Justice_League:_War"]
10 walkable: ["Alan_Tudyk", "~starring", "Maze_Runner:_The_Scorch_Trials"]
11 walkable: ["Alan_Tudyk", "~starring", "Meet_Market_(film)"]
12 walkable: ["Alan_Tudyk", "~starring", "Oddball_(film)"]
13 walkable: ["Alan_Tudyk", "~starring", "Rogue_One:_A_Star_Wars_Story"]
14 walkable: ["Alan_Tudyk", "~starring", "Serenity_(film)"]
15 walkable: ["Alan_Tudyk", "~starring", "Strange_Frame"]
16 walkable: ["Alan_Tudyk", "~starring", "Suburgatory"]
17 walkable: ["Alan_Tudyk", "~starring", "Tell_(2014_film)"]
18 walkable: ["Alan_Tudyk", "~starring", "Tucker_&_Dale_vs._Evil"]
19 walkable: ["Big_Hero_6_(film)", "starring", "\"*\""]
20 walkable: ["Big_Hero_6_(film)", "starring", "Damon_Wayans,_Jr."]
21 walkable: ["Big_Hero_6_(film)", "starring", "Daniel_Henney"]
22 walkable: ["Big_Hero_6_(film)", "starring", "Génesis_Rodríguez"]
23 walkable: ["Big_Hero_6_(film)", "starring", "James_Cromwell"]
24 walkable: ["Big_Hero_6_(film)", "starring", "Jamie_Chung"]
25 walkable: ["Big_Hero_6_(film)", "starring", "Maya_Rudolph"]
26 walkable: ["Big_Hero_6_(film)", "starring", "Ryan_Potter"]
27 walkable: ["Big_Hero_6_(film)", "starring", "Scott_Adsit"]
28 walkable: ["Big_Hero_6_(film)", "starring", "T._J._Miller"]
29 walkable: ["Big_Hero_6_(film)", "runtime", "\"6120.0\""]
30 walkable: ["Big_Hero_6_(film)", "writer", "Andy_Hurley"]
31 walkable: ["Big_Hero_6_(film)", "writer", "Dan_Gerson"]
32 walkable: ["Big_Hero_6_(film)", "writer", "Joe_Trohman"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 9. true_to_false_connected — test index 5583

- Claim: Alvah Sabin represented Vermon and worked as Secretary of State of Vermont.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["Vermont", "\"Secretary of State of Vermont\"", "Alvah_Sabin"]`
- Top relations: `["birthPlace", "~office", "almaMater", "nationality", "placeOfBirth"]`; H: 1
- Candidate: 1 connected + 2 walkable; V4 thấy 3; artifact còn 0 path sau K.

```text
01 connected: ["\"Secretary of State of Vermont\"", "~office", "Alvah_Sabin"]
02 walkable: ["Alvah_Sabin", "birthPlace", "Georgia,_Vermont"]
03 walkable: ["Alvah_Sabin", "placeOfBirth", "Georgia,_Vermont"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 10. true_to_false_connected — test index 5227

- Claim: Universal Music Group's, Philips Records, is the label of Agustín Barboza.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["Universal_Music_Group", "Philips_Records", "Agustín_Barboza"]`
- Top relations: `["recordLabel", "~recordLabel", "label", "genre", "~label"]`; H: 1
- Candidate: 4 connected + 28 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 connected: ["Agustín_Barboza", "recordLabel", "Philips_Records"]
02 connected: ["Agustín_Barboza", "label", "Philips_Records"]
03 connected: ["Philips_Records", "~recordLabel", "Agustín_Barboza"]
04 connected: ["Philips_Records", "~label", "Agustín_Barboza"]
05 walkable: ["Agustín_Barboza", "genre", "Guarania_(music)"]
06 walkable: ["Philips_Records", "~recordLabel", "'Til_the_Band_Comes_In"]
07 walkable: ["Philips_Records", "~recordLabel", "(Baby)_You_Don't_Have_to_Tell_Me"]
08 walkable: ["Philips_Records", "~recordLabel", "-Fa-Tal-_Gal_a_Todo_Vapor"]
09 walkable: ["Philips_Records", "~recordLabel", "1001°_Centigrades"]
10 walkable: ["Philips_Records", "~recordLabel", "10_Anos_Depois"]
11 walkable: ["Philips_Records", "~recordLabel", "14_Apo_Ta_Oreotera_Tragoudia_Mou"]
12 walkable: ["Philips_Records", "~recordLabel", "15_Chronia_Marinella"]
13 walkable: ["Philips_Records", "~recordLabel", "4_Gouden_Hits"]
14 walkable: ["Philips_Records", "~recordLabel", "5000_Volts"]
15 walkable: ["Philips_Records", "~recordLabel", "A_Brand_New_Me_(Dusty_Springfield_album)"]
16 walkable: ["Philips_Records", "~recordLabel", "A_Girl_Called_Dusty"]
17 walkable: ["Philips_Records", "~recordLabel", "A_Tábua_de_Esmeralda"]
18 walkable: ["Philips_Records", "~recordLabel", "Acker_Bilk"]
19 walkable: ["Philips_Records", "~recordLabel", "Aima,_Dakrya_&_Idrotas"]
20 walkable: ["Philips_Records", "~recordLabel", "Ajax,_Olé_Olé_Olé"]
21 walkable: ["Philips_Records", "~recordLabel", "Ajda_Pekkan"]
22 walkable: ["Philips_Records", "~recordLabel", "Albania_(album)"]
23 walkable: ["Philips_Records", "~recordLabel", "Alfred_Brendel_–_Unpublished_Live_and_Radio_Performances_1968–2001"]
24 walkable: ["Philips_Records", "~recordLabel", "Allegria"]
25 walkable: ["Philips_Records", "~recordLabel", "Alli_Mia_Fora_(Marinella_album)"]
26 walkable: ["Philips_Records", "~recordLabel", "Am_I_the_Same_Girl"]
27 walkable: ["Philips_Records", "~recordLabel", "American_Look"]
28 walkable: ["Philips_Records", "~recordLabel", "Amours_des_feintes"]
29 walkable: ["Philips_Records", "~recordLabel", "Andrea_Bocelli"]
30 walkable: ["Philips_Records", "~recordLabel", "Andy_Lau"]
31 walkable: ["Philips_Records", "~recordLabel", "Another_Monty_Python_Record"]
32 walkable: ["Philips_Records", "~recordLabel", "Another_Tear_Falls"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 11. true_to_false_connected — test index 5367

- Claim: Created by Jan Duursema, the comic character Arion is also known as Ahri'ahn.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["Jan_Duursema", "Arion_(comics)", "\"Ahri'ahn\""]`
- Top relations: `["~creators", "~creator", "nationality", "~nationality", "creator"]`; H: 1
- Candidate: 3 connected + 1 walkable; V4 thấy 4; artifact còn 0 path sau K.

```text
01 connected: ["Arion_(comics)", "creator", "Jan_Duursema"]
02 connected: ["Jan_Duursema", "~creators", "Arion_(comics)"]
03 connected: ["Jan_Duursema", "~creator", "Arion_(comics)"]
04 walkable: ["Arion_(comics)", "creator", "Paul_Kupperberg"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 12. true_to_false_connected — test index 6241

- Claim: Train followed Mermaid with Imagine, a song by John Lennon was produced by the production team Espionage and written by Pat Monahan.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["Pat_Monahan", "Espionage_(production_team)", "Imagine_(John_Lennon_song)", "Mermaid_(Train_song)"]`
- Top relations: `["subsequentWork", "producer", "author", "~subsequentWork", "genre"]`; H: 1
- Candidate: 3 connected + 17 walkable; V4 thấy 20; artifact còn 0 path sau K.

```text
01 connected: ["Imagine_(John_Lennon_song)", "~subsequentWork", "Mermaid_(Train_song)"]
02 connected: ["Mermaid_(Train_song)", "subsequentWork", "Imagine_(John_Lennon_song)"]
03 connected: ["Mermaid_(Train_song)", "producer", "Espionage_(production_team)"]
04 walkable: ["Espionage_(production_team)", "genre", "Pop_music"]
05 walkable: ["Espionage_(production_team)", "genre", "Rhythm_and_blues"]
06 walkable: ["Espionage_(production_team)", "genre", "Rock_music"]
07 walkable: ["Imagine_(John_Lennon_song)", "subsequentWork", "Happy_Xmas_(War_Is_Over)"]
08 walkable: ["Imagine_(John_Lennon_song)", "producer", "\"John Lennon\""]
09 walkable: ["Imagine_(John_Lennon_song)", "producer", "John_Lennon"]
10 walkable: ["Imagine_(John_Lennon_song)", "producer", "Phil_Spector"]
11 walkable: ["Imagine_(John_Lennon_song)", "producer", "Yoko_Ono"]
12 walkable: ["Imagine_(John_Lennon_song)", "~subsequentWork", "Counting_Bodies_Like_Sheep_to_the_Rhythm_of_the_War_Drums"]
13 walkable: ["Imagine_(John_Lennon_song)", "~subsequentWork", "Power_to_the_People_(song)"]
14 walkable: ["Imagine_(John_Lennon_song)", "~subsequentWork", "Symptoms_of_True_Love"]
15 walkable: ["Imagine_(John_Lennon_song)", "~subsequentWork", "Talk_of_the_Town_(song)"]
16 walkable: ["Imagine_(John_Lennon_song)", "genre", "Pop_music"]
17 walkable: ["Imagine_(John_Lennon_song)", "genre", "Soft_rock"]
18 walkable: ["Mermaid_(Train_song)", "producer", "\"Espionage, Butch Walker\""]
19 walkable: ["Mermaid_(Train_song)", "genre", "Pop_rock"]
20 walkable: ["Mermaid_(Train_song)", "genre", "Reggae"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 13. true_to_false_connected — test index 6332

- Claim: 103 Colmore Row was designed by the architect John Madin whose home town is Birmingham, a town where Khalid Mahmood (British politician) is one of the leaders.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["John_Madin", "Birmingham", "103_Colmore_Row", "\"Khalid_Mahmood_(British_politician)\""]`
- Top relations: `["architect", "location", "~architect", "birthPlace", "significantBuilding"]`; H: 1
- Candidate: 4 connected + 10 walkable; V4 thấy 14; artifact còn 0 path sau K.

```text
01 connected: ["103_Colmore_Row", "architect", "John_Madin"]
02 connected: ["103_Colmore_Row", "location", "Birmingham"]
03 connected: ["John_Madin", "~architect", "103_Colmore_Row"]
04 connected: ["John_Madin", "birthPlace", "Birmingham"]
05 walkable: ["103_Colmore_Row", "location", "\"Colmore Row, Birmingham, England\""]
06 walkable: ["103_Colmore_Row", "location", "Colmore_Row"]
07 walkable: ["Birmingham", "location", "\"5940.0\""]
08 walkable: ["Birmingham", "~architect", "Bama_Theatre"]
09 walkable: ["John_Madin", "~architect", "Birmingham_Central_Library"]
10 walkable: ["John_Madin", "~architect", "Metropolitan_House"]
11 walkable: ["John_Madin", "~architect", "Post_and_Mail_building,_Birmingham"]
12 walkable: ["John_Madin", "~architect", "Quayside_Tower"]
13 walkable: ["John_Madin", "birthPlace", "England"]
14 walkable: ["John_Madin", "birthPlace", "Moseley"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 14. true_to_false_connected — test index 5289

- Claim: Alan B. Miller Hall is at 101 Ukrop Way and was completed on 1 June 2009.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["Alan_B._Miller_Hall", "\"1 June 2009\"", "\"101 Ukrop Way\""]`
- Top relations: `["architect", "buildingEndDate", "~completionDate", "completionDate", "~buildingEndDate"]`; H: 1
- Candidate: 2 connected + 2 walkable; V4 thấy 4; artifact còn 0 path sau K.

```text
01 connected: ["\"1 June 2009\"", "~buildingEndDate", "Alan_B._Miller_Hall"]
02 connected: ["Alan_B._Miller_Hall", "buildingEndDate", "\"1 June 2009\""]
03 walkable: ["Alan_B._Miller_Hall", "architect", "Robert_A._M._Stern"]
04 walkable: ["Alan_B._Miller_Hall", "completionDate", "\"2009-06-01\""]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 15. true_to_false_connected — test index 6152

- Claim: Duncan Rouleau and Steven T. Seagle created Baymax who had his first movie appearance in Big Hero 6.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["Steven_T._Seagle", "Baymax", "Duncan_Rouleau", "\"Big Hero 6(2014)\""]`
- Top relations: `["creator", "~creators", "~creator", "fullName", "creators"]`; H: 1
- Candidate: 8 connected + 24 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 connected: ["Baymax", "creator", "Duncan_Rouleau"]
02 connected: ["Baymax", "creator", "Steven_T._Seagle"]
03 connected: ["Baymax", "creators", "Duncan_Rouleau"]
04 connected: ["Baymax", "creators", "Steven_T._Seagle"]
05 connected: ["Duncan_Rouleau", "~creators", "Baymax"]
06 connected: ["Duncan_Rouleau", "~creator", "Baymax"]
07 connected: ["Steven_T._Seagle", "~creators", "Baymax"]
08 connected: ["Steven_T._Seagle", "~creator", "Baymax"]
09 walkable: ["Duncan_Rouleau", "~creators", "Aries_(comics)"]
10 walkable: ["Duncan_Rouleau", "~creators", "Axis_Amerika"]
11 walkable: ["Duncan_Rouleau", "~creators", "Big_Hero_6_(comics)"]
12 walkable: ["Duncan_Rouleau", "~creators", "Bridgette_Crosby"]
13 walkable: ["Duncan_Rouleau", "~creators", "GoGo_Tomago"]
14 walkable: ["Duncan_Rouleau", "~creators", "Hiro_Takachiho"]
15 walkable: ["Duncan_Rouleau", "~creators", "Honey_Lemon"]
16 walkable: ["Duncan_Rouleau", "~creator", "Aries_(comics)"]
17 walkable: ["Duncan_Rouleau", "~creator", "Bridgette_Crosby"]
18 walkable: ["Duncan_Rouleau", "~creator", "Honey_Lemon"]
19 walkable: ["Steven_T._Seagle", "~creators", "American_Virgin_(comics)"]
20 walkable: ["Steven_T._Seagle", "~creators", "Aries_(comics)"]
21 walkable: ["Steven_T._Seagle", "~creators", "Big_Hero_6_(comics)"]
22 walkable: ["Steven_T._Seagle", "~creators", "Flex_(comics)"]
23 walkable: ["Steven_T._Seagle", "~creators", "GoGo_Tomago"]
24 walkable: ["Steven_T._Seagle", "~creators", "Hiro_Takachiho"]
25 walkable: ["Steven_T._Seagle", "~creators", "Honey_Lemon"]
26 walkable: ["Steven_T._Seagle", "~creators", "Jack_O'Lantern_(DC_Comics)"]
27 walkable: ["Steven_T._Seagle", "~creators", "Murmur_(Marvel_Comics)"]
28 walkable: ["Steven_T._Seagle", "~creators", "Primal_Force"]
29 walkable: ["Steven_T._Seagle", "~creators", "Radius_(comics)"]
30 walkable: ["Steven_T._Seagle", "~creators", "Supergirl_(Cir-El)"]
31 walkable: ["Steven_T._Seagle", "~creator", "Aries_(comics)"]
32 walkable: ["Steven_T._Seagle", "~creator", "Flex_(comics)"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 16. true_to_false_connected — test index 6184

- Claim: AFC Blackpool have had Stuart Parker as their manager. He has represented the club KV Mechelen and is a member of the Irlam Town F.C.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["A.F.C._Blackpool", "KV_Mechelen", "Irlam_Town_F.C.", "Stuart_Parker_(footballer)"]`
- Top relations: `["~manager", "managerClub", "~team", "team", "~managerClub"]`; H: 1
- Candidate: 9 connected + 23 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 connected: ["A.F.C._Blackpool", "~team", "Stuart_Parker_(footballer)"]
02 connected: ["A.F.C._Blackpool", "~managerClub", "Stuart_Parker_(footballer)"]
03 connected: ["Irlam_Town_F.C.", "~team", "Stuart_Parker_(footballer)"]
04 connected: ["KV_Mechelen", "~team", "Stuart_Parker_(footballer)"]
05 connected: ["Stuart_Parker_(footballer)", "~manager", "A.F.C._Blackpool"]
06 connected: ["Stuart_Parker_(footballer)", "managerClub", "A.F.C._Blackpool"]
07 connected: ["Stuart_Parker_(footballer)", "team", "A.F.C._Blackpool"]
08 connected: ["Stuart_Parker_(footballer)", "team", "Irlam_Town_F.C."]
09 connected: ["Stuart_Parker_(footballer)", "team", "KV_Mechelen"]
10 walkable: ["A.F.C._Blackpool", "~team", "Ciaran_Donnelly"]
11 walkable: ["A.F.C._Blackpool", "~team", "Ciaran_Donnelly__10"]
12 walkable: ["A.F.C._Blackpool", "~team", "Keigan_Parker"]
13 walkable: ["A.F.C._Blackpool", "~team", "Keigan_Parker__11"]
14 walkable: ["A.F.C._Blackpool", "~team", "Stuart_Parker_(footballer)__18"]
15 walkable: ["A.F.C._Blackpool", "~team", "Stuart_Parker_(footballer)__20"]
16 walkable: ["Irlam_Town_F.C.", "~team", "Derrick_Parker"]
17 walkable: ["Irlam_Town_F.C.", "~team", "Derrick_Parker__16"]
18 walkable: ["Irlam_Town_F.C.", "~team", "Stuart_Parker_(footballer)__14"]
19 walkable: ["Irlam_Town_F.C.", "~team", "Tony_Caldwell_(footballer)"]
20 walkable: ["Irlam_Town_F.C.", "~team", "Tony_Caldwell_(footballer)__2"]
21 walkable: ["KV_Mechelen", "~team", "1987–88_FC_Dinamo_București_season"]
22 walkable: ["KV_Mechelen", "~team", "1988_European_Cup_Winners'_Cup_Final"]
23 walkable: ["KV_Mechelen", "~team", "2006–07_Belgian_Cup"]
24 walkable: ["KV_Mechelen", "~team", "2007–08_Belgian_Cup"]
25 walkable: ["KV_Mechelen", "~team", "2007–08_Standard_Liège_season"]
26 walkable: ["KV_Mechelen", "~team", "2008–09_Belgian_Cup"]
27 walkable: ["KV_Mechelen", "~team", "2009_Belgian_Cup_Final"]
28 walkable: ["KV_Mechelen", "~team", "2009–10_Belgian_Cup"]
29 walkable: ["KV_Mechelen", "~team", "2010–11_Belgian_Cup"]
30 walkable: ["KV_Mechelen", "~team", "2011–12_Belgian_Cup"]
31 walkable: ["KV_Mechelen", "~team", "2011–12_Oud-Heverlee_Leuven_season"]
32 walkable: ["KV_Mechelen", "~team", "2012–13_Belgian_Cup"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 17. true_to_false_connected — test index 6257

- Claim: The Stargate produced Train song Mermaid of the reggae genre was written by Amund Bjørklund.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["Reggae", "Amund_Bjørklund", "Stargate_(production_team)", "Mermaid_(Train_song)"]`
- Top relations: `["producer", "genre", "~producer", "~associatedMusicalArtist", "creator"]`; H: 1
- Candidate: 1 connected + 31 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 connected: ["Mermaid_(Train_song)", "genre", "Reggae"]
02 walkable: ["Mermaid_(Train_song)", "producer", "\"Espionage, Butch Walker\""]
03 walkable: ["Mermaid_(Train_song)", "producer", "Espionage_(production_team)"]
04 walkable: ["Mermaid_(Train_song)", "genre", "Pop_rock"]
05 walkable: ["Stargate_(production_team)", "~producer", "50/50_&_Lullaby"]
06 walkable: ["Stargate_(production_team)", "~producer", "7_(S_Club_7_album)"]
07 walkable: ["Stargate_(production_team)", "~producer", "A_Place_with_No_Name"]
08 walkable: ["Stargate_(production_team)", "~producer", "A_Public_Affair"]
09 walkable: ["Stargate_(production_team)", "~producer", "Alexis_Jordan_(album)"]
10 walkable: ["Stargate_(production_team)", "~producer", "All_Kinds_of_Trouble"]
11 walkable: ["Stargate_(production_team)", "~producer", "All_Rise_(song)"]
12 walkable: ["Stargate_(production_team)", "~producer", "Always_Come_Back_to_Your_Love"]
13 walkable: ["Stargate_(production_team)", "~producer", "Ave_Maria_(Beyoncé_song)"]
14 walkable: ["Stargate_(production_team)", "~producer", "Be_on_You"]
15 walkable: ["Stargate_(production_team)", "~producer", "Beautiful_Monster"]
16 walkable: ["Stargate_(production_team)", "~producer", "Because_of_You_(Ne-Yo_album)"]
17 walkable: ["Stargate_(production_team)", "~producer", "Because_of_You_(Ne-Yo_song)"]
18 walkable: ["Stargate_(production_team)", "~producer", "Blacc_Hollywood"]
19 walkable: ["Stargate_(production_team)", "~producer", "Black_Star_Elephant"]
20 walkable: ["Stargate_(production_team)", "~producer", "Black_and_Yellow"]
21 walkable: ["Stargate_(production_team)", "~producer", "Bye_Bye_(Mariah_Carey_song)"]
22 walkable: ["Stargate_(production_team)", "~producer", "Can't_Help_but_Wait"]
23 walkable: ["Stargate_(production_team)", "~producer", "Can't_Tell_Me_Nothing_(mixtape)"]
24 walkable: ["Stargate_(production_team)", "~producer", "Cannonball_(Lea_Michele_song)"]
25 walkable: ["Stargate_(production_team)", "~producer", "Closer_(Ne-Yo_song)"]
26 walkable: ["Stargate_(production_team)", "~producer", "Come_&_Get_It_(Selena_Gomez_song)"]
27 walkable: ["Stargate_(production_team)", "~producer", "Come_Back_to_Me_(Hikaru_Utada_song)"]
28 walkable: ["Stargate_(production_team)", "~producer", "Coming_Home_(Lionel_Richie_album)"]
29 walkable: ["Stargate_(production_team)", "~producer", "Contraband_(Madcon_album)"]
30 walkable: ["Stargate_(production_team)", "~producer", "Contrast_(Conor_Maynard_album)"]
31 walkable: ["Stargate_(production_team)", "~producer", "Crowded"]
32 walkable: ["Stargate_(production_team)", "~producer", "Curtain_Falls"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 18. true_to_false_connected — test index 5895

- Claim: 103 Colmore Row is located in Colmore Row, Birmingham, England and was completed in 1976 having 23 floors.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["\"1976\"", "103_Colmore_Row", "\"Colmore Row, Birmingham, England\"", "\"23\""]`
- Top relations: `["~floorCount", "~completionDate", "floorCount", "floorArea", "completionDate"]`; H: 1
- Candidate: 4 connected + 28 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 connected: ["\"1976\"", "~completionDate", "103_Colmore_Row"]
02 connected: ["\"23\"", "~floorCount", "103_Colmore_Row"]
03 connected: ["103_Colmore_Row", "floorCount", "\"23\""]
04 connected: ["103_Colmore_Row", "completionDate", "\"1976\""]
05 walkable: ["\"1976\"", "~completionDate", "Alexandra_House"]
06 walkable: ["\"1976\"", "~completionDate", "Allendale_Square"]
07 walkable: ["\"1976\"", "~completionDate", "AllerWeltHaus_Hagen"]
08 walkable: ["\"1976\"", "~completionDate", "Astro_Tower"]
09 walkable: ["\"1976\"", "~completionDate", "CN_Tower"]
10 walkable: ["\"1976\"", "~completionDate", "Cameron_Offices,_Belconnen"]
11 walkable: ["\"1976\"", "~completionDate", "Campus_of_the_Massachusetts_Institute_of_Technology"]
12 walkable: ["\"1976\"", "~completionDate", "Champasak_Palace"]
13 walkable: ["\"1976\"", "~completionDate", "Chatterjee_International_Center"]
14 walkable: ["\"1976\"", "~completionDate", "Clorox_Building"]
15 walkable: ["\"1976\"", "~completionDate", "Complexe_Desjardins"]
16 walkable: ["\"1976\"", "~completionDate", "Durland–Rathbone–Fiedler_Hall"]
17 walkable: ["\"1976\"", "~completionDate", "Edgbaston_House"]
18 walkable: ["\"1976\"", "~completionDate", "Edward_A._Garmatz_United_States_Courthouse"]
19 walkable: ["\"1976\"", "~completionDate", "Empire_State_Plaza"]
20 walkable: ["\"1976\"", "~completionDate", "First_Federal_Plaza"]
21 walkable: ["\"1976\"", "~completionDate", "First_Place_Hamilton_(building)"]
22 walkable: ["\"1976\"", "~completionDate", "Garden_Tower"]
23 walkable: ["\"1976\"", "~completionDate", "Holiday_Inn,_Townsville"]
24 walkable: ["\"1976\"", "~completionDate", "Hong_Leong_Building"]
25 walkable: ["\"1976\"", "~completionDate", "Hotel_Alba_Caracas"]
26 walkable: ["\"1976\"", "~completionDate", "Hyatt_Regency_New_Orleans"]
27 walkable: ["\"1976\"", "~completionDate", "Hyatt_Regency_Phoenix"]
28 walkable: ["\"1976\"", "~completionDate", "IBM_Building,_Johannesburg"]
29 walkable: ["\"1976\"", "~completionDate", "International_Plaza_(Singapore)"]
30 walkable: ["\"1976\"", "~completionDate", "John_Hancock_Tower"]
31 walkable: ["\"1976\"", "~completionDate", "OCBC_Centre"]
32 walkable: ["\"1976\"", "~completionDate", "Office_of_the_Bangsamoro_People"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 19. true_to_false_connected — test index 5374

- Claim: I know, Baymax was created by Duncan Rouleau and Steven T. Seagle.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["Steven_T._Seagle", "Baymax", "Duncan_Rouleau"]`
- Top relations: `["~creators", "~creator", "creator", "nationality", "creators"]`; H: 1
- Candidate: 8 connected + 24 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 connected: ["Baymax", "creator", "Duncan_Rouleau"]
02 connected: ["Baymax", "creator", "Steven_T._Seagle"]
03 connected: ["Baymax", "creators", "Duncan_Rouleau"]
04 connected: ["Baymax", "creators", "Steven_T._Seagle"]
05 connected: ["Duncan_Rouleau", "~creators", "Baymax"]
06 connected: ["Duncan_Rouleau", "~creator", "Baymax"]
07 connected: ["Steven_T._Seagle", "~creators", "Baymax"]
08 connected: ["Steven_T._Seagle", "~creator", "Baymax"]
09 walkable: ["Duncan_Rouleau", "~creators", "Aries_(comics)"]
10 walkable: ["Duncan_Rouleau", "~creators", "Axis_Amerika"]
11 walkable: ["Duncan_Rouleau", "~creators", "Big_Hero_6_(comics)"]
12 walkable: ["Duncan_Rouleau", "~creators", "Bridgette_Crosby"]
13 walkable: ["Duncan_Rouleau", "~creators", "GoGo_Tomago"]
14 walkable: ["Duncan_Rouleau", "~creators", "Hiro_Takachiho"]
15 walkable: ["Duncan_Rouleau", "~creators", "Honey_Lemon"]
16 walkable: ["Duncan_Rouleau", "~creator", "Aries_(comics)"]
17 walkable: ["Duncan_Rouleau", "~creator", "Bridgette_Crosby"]
18 walkable: ["Duncan_Rouleau", "~creator", "Honey_Lemon"]
19 walkable: ["Duncan_Rouleau", "nationality", "\"American\""]
20 walkable: ["Duncan_Rouleau", "nationality", "Americans"]
21 walkable: ["Steven_T._Seagle", "~creators", "American_Virgin_(comics)"]
22 walkable: ["Steven_T._Seagle", "~creators", "Aries_(comics)"]
23 walkable: ["Steven_T._Seagle", "~creators", "Big_Hero_6_(comics)"]
24 walkable: ["Steven_T._Seagle", "~creators", "Flex_(comics)"]
25 walkable: ["Steven_T._Seagle", "~creators", "GoGo_Tomago"]
26 walkable: ["Steven_T._Seagle", "~creators", "Hiro_Takachiho"]
27 walkable: ["Steven_T._Seagle", "~creators", "Honey_Lemon"]
28 walkable: ["Steven_T._Seagle", "~creators", "Jack_O'Lantern_(DC_Comics)"]
29 walkable: ["Steven_T._Seagle", "~creators", "Murmur_(Marvel_Comics)"]
30 walkable: ["Steven_T._Seagle", "~creators", "Primal_Force"]
31 walkable: ["Steven_T._Seagle", "~creators", "Radius_(comics)"]
32 walkable: ["Steven_T._Seagle", "~creators", "Supergirl_(Cir-El)"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 20. true_to_false_connected — test index 5974

- Claim: The comic book character Arion, aka Ahri'ahn, was created by Jan Duursema and Paul Kupperberg.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["Jan_Duursema", "Arion_(comics)", "\"Ahri'ahn\"", "Paul_Kupperberg"]`
- Top relations: `["~creators", "~creator", "nationality", "creator", "~nationality"]`; H: 1
- Candidate: 6 connected + 26 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 connected: ["Arion_(comics)", "creator", "Jan_Duursema"]
02 connected: ["Arion_(comics)", "creator", "Paul_Kupperberg"]
03 connected: ["Jan_Duursema", "~creators", "Arion_(comics)"]
04 connected: ["Jan_Duursema", "~creator", "Arion_(comics)"]
05 connected: ["Paul_Kupperberg", "~creators", "Arion_(comics)"]
06 connected: ["Paul_Kupperberg", "~creator", "Arion_(comics)"]
07 walkable: ["Paul_Kupperberg", "~creators", "Black_Thorn_(comics)"]
08 walkable: ["Paul_Kupperberg", "~creators", "Celsius_(comics)"]
09 walkable: ["Paul_Kupperberg", "~creators", "Centrix"]
10 walkable: ["Paul_Kupperberg", "~creators", "Ch'p"]
11 walkable: ["Paul_Kupperberg", "~creators", "Checkmate_(comics)"]
12 walkable: ["Paul_Kupperberg", "~creators", "Dorothy_Spinner"]
13 walkable: ["Paul_Kupperberg", "~creators", "General_Glory"]
14 walkable: ["Paul_Kupperberg", "~creators", "H'lven"]
15 walkable: ["Paul_Kupperberg", "~creators", "Harry_Stein_(comics)"]
16 walkable: ["Paul_Kupperberg", "~creators", "Joshua_Clay"]
17 walkable: ["Paul_Kupperberg", "~creators", "Psi_(comics)"]
18 walkable: ["Paul_Kupperberg", "~creators", "Reactron"]
19 walkable: ["Paul_Kupperberg", "~creators", "Rhea_Jones"]
20 walkable: ["Paul_Kupperberg", "~creators", "Takion"]
21 walkable: ["Paul_Kupperberg", "~creators", "Valentina_Vostok"]
22 walkable: ["Paul_Kupperberg", "~creator", "Black_Thorn_(comics)"]
23 walkable: ["Paul_Kupperberg", "~creator", "Celsius_(comics)"]
24 walkable: ["Paul_Kupperberg", "~creator", "Centrix"]
25 walkable: ["Paul_Kupperberg", "~creator", "Ch'p"]
26 walkable: ["Paul_Kupperberg", "~creator", "Dorothy_Spinner"]
27 walkable: ["Paul_Kupperberg", "~creator", "General_Glory"]
28 walkable: ["Paul_Kupperberg", "~creator", "Harry_Stein_(comics)"]
29 walkable: ["Paul_Kupperberg", "~creator", "Joshua_Clay"]
30 walkable: ["Paul_Kupperberg", "~creator", "Psi_(comics)"]
31 walkable: ["Paul_Kupperberg", "~creator", "Reactron"]
32 walkable: ["Paul_Kupperberg", "~creator", "Rhea_Jones"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 21. true_to_false_no_path — test index 5787

- Claim: Adams County, Pennsylvania, United States is home to the 11th Mississippi Infantry Monument.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["11th_Mississippi_Infantry_Monument", "Adams_County,_Pennsylvania", "\"United States\""]`
- Top relations: `["location", "regionServed", "locationCountry", "city", "headquarter"]`; H: 1
- Candidate: 0 connected + 0 walkable; V4 thấy 0; artifact còn 0 path sau K.

```text
Không có path.
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 22. true_to_false_no_path — test index 5168

- Claim: Agra airport is in India and they have the ATA location identifier AGR.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["India", "Agra_Airport", "\"AGR\""]`
- Top relations: `["~faa", "faa", "order", "runwaySurface", "r3Surface"]`; H: 2
- Candidate: 0 connected + 0 walkable; V4 thấy 0; artifact còn 0 path sau K.

```text
Không có path.
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 23. true_to_false_no_path — test index 5478

- Claim: The 11th Mississippi Infantry Monument falls under the category of Contributing property and is placed in the municipality of Gettysburg in Pennsylvania.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["11th_Mississippi_Infantry_Monument", "Contributing_property", "Gettysburg,_Pennsylvania"]`
- Top relations: `["material", "currentTenants", "dedicatedTo", "architect", "faa"]`; H: 1
- Candidate: 0 connected + 0 walkable; V4 thấy 0; artifact còn 0 path sau K.

```text
Không có path.
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 24. true_to_false_no_path — test index 7364

- Claim: I remembered that the 11th Mississippi Infantry Monument, a contributing property, is located in Adams County, Pennsylvania which is east to the Pennsylvania's Franklin County.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["Franklin_County,_Pennsylvania", "11th_Mississippi_Infantry_Monument", "Adams_County,_Pennsylvania", "Contributing_property"]`
- Top relations: `["location", "nrhpReferenceNumber", "material", "yearOfConstruction", "added"]`; H: 1
- Candidate: 0 connected + 0 walkable; V4 thấy 0; artifact còn 0 path sau K.

```text
Không có path.
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 25. true_to_false_no_path — test index 5741

- Claim: Frederick County Maryland is southwest of Adams County Pennsylvania which is home to the 11th Mississippi Infantry Monument.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["Frederick_County,_Maryland", "11th_Mississippi_Infantry_Monument", "Adams_County,_Pennsylvania"]`
- Top relations: `["city", "headquarters", "location", "~ground", "rector"]`; H: 1
- Candidate: 0 connected + 0 walkable; V4 thấy 0; artifact còn 0 path sau K.

```text
Không có path.
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 26. true_to_false_walkable_only — test index 5499

- Claim: To the southeast of Adams County, Pennsylvania, where 11th Mississippi Infantry Monument is located, lies Carroll County, Maryland.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["Carroll_County,_Maryland", "11th_Mississippi_Infantry_Monument", "Adams_County,_Pennsylvania"]`
- Top relations: `["location", "headquarters", "~northeast", "northeast", "MeanOfTransportation/diameter"]`; H: 1
- Candidate: 0 connected + 1 walkable; V4 thấy 1; artifact còn 0 path sau K.

```text
01 walkable: ["Carroll_County,_Maryland", "northeast", "\"York County, Pennsylvania\""]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 27. true_to_false_walkable_only — test index 5794

- Claim: Well the 11th Mississippi Infantry Monument stands in Adams County, Pennsylvania.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["\"Pennsylvania\"", "11th_Mississippi_Infantry_Monument", "Adams_County,_Pennsylvania"]`
- Top relations: `["location", "material", "dedicatedTo", "~location", "isPartOf"]`; H: 1
- Candidate: 0 connected + 16 walkable; V4 thấy 16; artifact còn 0 path sau K.

```text
01 walkable: ["\"Pennsylvania\"", "~location", "Houdini_Museum"]
02 walkable: ["\"Pennsylvania\"", "~location", "Idlewild_and_Soak_Zone"]
03 walkable: ["\"Pennsylvania\"", "~location", "Knoebels_Amusement_Resort"]
04 walkable: ["\"Pennsylvania\"", "~location", "Lakemont_Park"]
05 walkable: ["\"Pennsylvania\"", "~location", "Leonard_Davis_Institute_of_Health_Economics"]
06 walkable: ["\"Pennsylvania\"", "~location", "List_of_Pennsylvania_weather_records"]
07 walkable: ["\"Pennsylvania\"", "~location", "The_Farnsworth_House_Inn"]
08 walkable: ["\"Pennsylvania\"", "~location", "Uplifting_Entertainment"]
09 walkable: ["\"Pennsylvania\"", "~location", "Washington_Run_Railroad"]
10 walkable: ["Adams_County,_Pennsylvania", "~location", "Camp_Colt,_Pennsylvania"]
11 walkable: ["Adams_County,_Pennsylvania", "~location", "Carbaugh_Run_Rhyolite_Quarry_Site"]
12 walkable: ["Adams_County,_Pennsylvania", "~location", "Cemetery_Ridge"]
13 walkable: ["Adams_County,_Pennsylvania", "~location", "East_Cemetery_Hill"]
14 walkable: ["Adams_County,_Pennsylvania", "~location", "Gettysburg_Battlefield_Historic_District"]
15 walkable: ["Adams_County,_Pennsylvania", "~location", "Gettysburg_Electric_Railway"]
16 walkable: ["Adams_County,_Pennsylvania", "~location", "Gettysburg_National_Military_Park"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 28. true_to_false_walkable_only — test index 5786

- Claim: Abdul Taib Mahmud is a part of the Parti Pesaka Bumiputera Bersatu in Sarawak.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["Parti_Pesaka_Bumiputera_Bersatu", "Sarawak", "Abdul_Taib_Mahmud"]`
- Top relations: `["~team", "~birthPlace", "occupation", "status", "president"]`; H: 1
- Candidate: 0 connected + 32 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 walkable: ["Parti_Pesaka_Bumiputera_Bersatu", "president", "Adenan_Satem"]
02 walkable: ["Sarawak", "~birthPlace", "Abdul_Rahman_Ya'kub"]
03 walkable: ["Sarawak", "~birthPlace", "Aidil_Mohammad"]
04 walkable: ["Sarawak", "~birthPlace", "Alan_Ling_Sie_Kiong"]
05 walkable: ["Sarawak", "~birthPlace", "Annuar_Rapaee"]
06 walkable: ["Sarawak", "~birthPlace", "Azizan_Saperi"]
07 walkable: ["Sarawak", "~birthPlace", "Bolly_Lapok"]
08 walkable: ["Sarawak", "~birthPlace", "Bryan_Nickson_Lomas"]
09 walkable: ["Sarawak", "~birthPlace", "Chan_Seng_Khai"]
10 walkable: ["Sarawak", "~birthPlace", "Chong_Chieng_Jen"]
11 walkable: ["Sarawak", "~birthPlace", "Clare_Rewcastle_Brown"]
12 walkable: ["Sarawak", "~birthPlace", "Dan_Sullivan_(Australian_politician)"]
13 walkable: ["Sarawak", "~birthPlace", "Daniel_Bego"]
14 walkable: ["Sarawak", "~birthPlace", "Depha_masterpiece"]
15 walkable: ["Sarawak", "~birthPlace", "Dewi_Liana_Seriestha"]
16 walkable: ["Sarawak", "~birthPlace", "Elizabeth_Jimie"]
17 walkable: ["Sarawak", "~birthPlace", "Elwyn_Brook-Jones"]
18 walkable: ["Sarawak", "~birthPlace", "George_Chan_Hong_Nam"]
19 walkable: ["Sarawak", "~birthPlace", "Gilbert_Cassidy_Gawing"]
20 walkable: ["Sarawak", "~birthPlace", "Hii_King_Chiong"]
21 walkable: ["Sarawak", "~birthPlace", "James_Chan_Khay_Syn"]
22 walkable: ["Sarawak", "~birthPlace", "Joseph_Kalang_Tie"]
23 walkable: ["Sarawak", "~birthPlace", "Julian_Tan_Kok_Ping"]
24 walkable: ["Sarawak", "~birthPlace", "Kanang_anak_Langkau"]
25 walkable: ["Sarawak", "~birthPlace", "Koreyoshi_Kurahara"]
26 walkable: ["Sarawak", "~birthPlace", "Lana_Nodin"]
27 walkable: ["Sarawak", "~birthPlace", "Made_Katib"]
28 walkable: ["Sarawak", "~birthPlace", "Mazwandi_Zekeria"]
29 walkable: ["Sarawak", "~birthPlace", "Melvin_Sia"]
30 walkable: ["Sarawak", "~birthPlace", "Mohd_Azlan_Iskandar"]
31 walkable: ["Sarawak", "~birthPlace", "Mohd_Dzulazlan_Ibrahim"]
32 walkable: ["Sarawak", "~birthPlace", "Mohd_Dzulfadli_Awang_Marajeh"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 29. true_to_false_walkable_only — test index 6424

- Claim: Alvah Sabin was from Vermont where the largest city is Burlington and represented the state's 3rd Congressional District.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["Alvah_Sabin", "Burlington,_Vermont", "Vermont", "Vermont's_3rd_congressional_district", "\"Vermont\""]`
- Top relations: `["nationality", "deathPlace", "~birthPlace", "~office", "residence"]`; H: 1
- Candidate: 0 connected + 32 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 walkable: ["\"Vermont\"", "~birthPlace", "Dave_Rogers_(NASCAR)"]
02 walkable: ["\"Vermont\"", "~birthPlace", "Karen_Anders"]
03 walkable: ["\"Vermont\"", "~birthPlace", "Robert_Hastings_Hunkins"]
04 walkable: ["Alvah_Sabin", "deathPlace", "Sycamore,_Illinois"]
05 walkable: ["Burlington,_Vermont", "~birthPlace", "Adam_Grimes"]
06 walkable: ["Burlington,_Vermont", "~birthPlace", "Albert_Wheeler_Coffrin"]
07 walkable: ["Burlington,_Vermont", "~birthPlace", "Andrea_Davidovich"]
08 walkable: ["Burlington,_Vermont", "~birthPlace", "Anne_Donahue"]
09 walkable: ["Burlington,_Vermont", "~birthPlace", "Ben_Kinmont"]
10 walkable: ["Burlington,_Vermont", "~birthPlace", "Billy_Kidd"]
11 walkable: ["Burlington,_Vermont", "~birthPlace", "Birdie_Tebbetts"]
12 walkable: ["Burlington,_Vermont", "~birthPlace", "Brian_D._Burns"]
13 walkable: ["Burlington,_Vermont", "~birthPlace", "Caroline_Bright"]
14 walkable: ["Burlington,_Vermont", "~birthPlace", "Charles_Doolittle"]
15 walkable: ["Burlington,_Vermont", "~birthPlace", "Christian_XXX"]
16 walkable: ["Burlington,_Vermont", "~birthPlace", "Donald_DeMag"]
17 walkable: ["Burlington,_Vermont", "~birthPlace", "Doug_Racine"]
18 walkable: ["Burlington,_Vermont", "~birthPlace", "Edward_D._Robie"]
19 walkable: ["Burlington,_Vermont", "~birthPlace", "Edward_G._Wilkin"]
20 walkable: ["Burlington,_Vermont", "~birthPlace", "Elizabeth_M._Ready"]
21 walkable: ["Burlington,_Vermont", "~birthPlace", "Erica_Skinger"]
22 walkable: ["Burlington,_Vermont", "~birthPlace", "Ernest_Owusu"]
23 walkable: ["Burlington,_Vermont", "~birthPlace", "Field_Cate"]
24 walkable: ["Burlington,_Vermont", "~birthPlace", "Gary_Wright_(ice_hockey)"]
25 walkable: ["Burlington,_Vermont", "~birthPlace", "Geoffrey_W._Crawford"]
26 walkable: ["Burlington,_Vermont", "~birthPlace", "George_G._Benedict"]
27 walkable: ["Burlington,_Vermont", "~birthPlace", "Grace_Coolidge"]
28 walkable: ["Burlington,_Vermont", "~birthPlace", "Harry_Blanchard"]
29 walkable: ["Burlington,_Vermont", "~birthPlace", "Jackie_Croft"]
30 walkable: ["Burlington,_Vermont", "~birthPlace", "Jacqueline_Noonan"]
31 walkable: ["Burlington,_Vermont", "~birthPlace", "James_B._Twitchell"]
32 walkable: ["Burlington,_Vermont", "~birthPlace", "James_P._Leddy"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 30. true_to_false_walkable_only — test index 5486

- Claim: The 11th Mississippi Infantry Monument in Adams County, Pennsylvania was made in 2000.
- Nhãn thật: True; V4 đoán: False
- Entity_set: `["\"2000\"", "11th_Mississippi_Infantry_Monument", "Adams_County,_Pennsylvania"]`
- Top relations: `["architect", "buildingEndDate", "material", "~location", "~buildingEndDate"]`; H: 1
- Candidate: 0 connected + 32 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 walkable: ["\"2000\"", "~location", "2000_Market_Street"]
02 walkable: ["\"2000\"", "~location", "Albuquerque_Museum_of_Art_and_History"]
03 walkable: ["\"2000\"", "~location", "AnMed_Health_Women's_&_Children's_Hospital"]
04 walkable: ["\"2000\"", "~location", "Angel_Stadium_of_Anaheim"]
05 walkable: ["\"2000\"", "~location", "Annenberg_Foundation"]
06 walkable: ["\"2000\"", "~location", "Ares_Management"]
07 walkable: ["\"2000\"", "~location", "Babcock-Shattuck_House"]
08 walkable: ["\"2000\"", "~location", "Barlow_Respiratory_Hospital"]
09 walkable: ["\"2000\"", "~location", "Beth_Israel_Congregation_(Ann_Arbor,_Michigan)"]
10 walkable: ["\"2000\"", "~location", "Birmingham_Museum_of_Art"]
11 walkable: ["\"2000\"", "~location", "Blackbaud"]
12 walkable: ["\"2000\"", "~location", "Buena_Vista_Downtown_Historic_District"]
13 walkable: ["\"2000\"", "~location", "CenturyLink_Center"]
14 walkable: ["\"2000\"", "~location", "Cibola_County_Correctional_Center"]
15 walkable: ["\"2000\"", "~location", "Concord_Pavilion"]
16 walkable: ["\"2000\"", "~location", "D'Iberville_Apartments"]
17 walkable: ["\"2000\"", "~location", "David_and_Lucy_Tarr_Fleming_Mansion"]
18 walkable: ["\"2000\"", "~location", "Doctors_Medical_Center_San_Pablo_Campus"]
19 walkable: ["\"2000\"", "~location", "East_Providence_High_School"]
20 walkable: ["\"2000\"", "~location", "Edward_D._Hansen_Conference_Center"]
21 walkable: ["\"2000\"", "~location", "Fearrington_Village"]
22 walkable: ["\"2000\"", "~location", "First_Christian_Church_(Longview,_Washington)"]
23 walkable: ["\"2000\"", "~location", "First_Church_of_Christ,_Scientist_(Little_Rock,_Arkansas)"]
24 walkable: ["\"2000\"", "~location", "Ford_Field"]
25 walkable: ["\"2000\"", "~location", "Former_Parks-Cramer_Company_Complex"]
26 walkable: ["\"2000\"", "~location", "Gas_Works_Park"]
27 walkable: ["\"2000\"", "~location", "Gen._John_Stark_House"]
28 walkable: ["\"2000\"", "~location", "Granbury_High_School"]
29 walkable: ["\"2000\"", "~location", "Greater_Cleveland_Aquarium"]
30 walkable: ["\"2000\"", "~location", "Greene-Marston_House"]
31 walkable: ["\"2000\"", "~location", "Hawthorne_Christian_Academy"]
32 walkable: ["\"2000\"", "~location", "Herndon_Hall"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 31. false_to_true — test index 2664

- Claim: Acura is a division of Honda which manufactured the Acura TLX which has a OHV single.
- Nhãn thật: False; V4 đoán: True
- Entity_set: `["Acura_TLX", "Honda", "Acura", "\"OHV single\""]`
- Top relations: `["~enginetype", "~class", "~division", "~bodyStyle", "~unrankedDivisio"]`; H: 1
- Candidate: 1 connected + 0 walkable; V4 thấy 1; artifact còn 0 path sau K.

```text
01 connected: ["Acura", "~division", "Honda"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 32. false_to_true — test index 1684

- Claim: He died in Montevideo. The leader of Montevideo is Daniel Martinez.
- Nhãn thật: False; V4 đoán: True
- Entity_set: `["\"Daniel_Martínez_(politician)\"", "Montevideo", "Bohdan_Pawłowicz"]`
- Top relations: `["deathPlace", "~leaderName", "~placeOfDeath", "~deathPlace", "~birthPlace"]`; H: 1
- Candidate: 1 connected + 31 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 connected: ["\"Daniel_Martínez_(politician)\"", "~leaderName", "Montevideo"]
02 walkable: ["Bohdan_Pawłowicz", "deathPlace", "\"New York State, US\""]
03 walkable: ["Bohdan_Pawłowicz", "deathPlace", "New_York"]
04 walkable: ["Montevideo", "~placeOfDeath", "Alberto_Abdala"]
05 walkable: ["Montevideo", "~placeOfDeath", "Alberto_Héber_Usher"]
06 walkable: ["Montevideo", "~placeOfDeath", "Alberto_Suppici"]
07 walkable: ["Montevideo", "~placeOfDeath", "Andrés_Martínez_Trueba"]
08 walkable: ["Montevideo", "~placeOfDeath", "Aparicio_Méndez"]
09 walkable: ["Montevideo", "~placeOfDeath", "Atilio_García"]
10 walkable: ["Montevideo", "~placeOfDeath", "Baltasar_Brum"]
11 walkable: ["Montevideo", "~placeOfDeath", "Carlos_Parteli"]
12 walkable: ["Montevideo", "~placeOfDeath", "Carmen_Barradas"]
13 walkable: ["Montevideo", "~placeOfDeath", "Diego_Rodríguez_Cano"]
14 walkable: ["Montevideo", "~placeOfDeath", "Duncan_Stewart_(Uruguayan_politician)"]
15 walkable: ["Montevideo", "~placeOfDeath", "Eladio_Dieste"]
16 walkable: ["Montevideo", "~placeOfDeath", "Elena_Zuasti"]
17 walkable: ["Montevideo", "~placeOfDeath", "Eliana_Ramos"]
18 walkable: ["Montevideo", "~placeOfDeath", "Enrique_Ballestrero"]
19 walkable: ["Montevideo", "~placeOfDeath", "Enrique_Tarigo"]
20 walkable: ["Montevideo", "~placeOfDeath", "Ernesto_Mascheroni"]
21 walkable: ["Montevideo", "~placeOfDeath", "Esteban_Echeverría"]
22 walkable: ["Montevideo", "~placeOfDeath", "Esther_de_Cáceres"]
23 walkable: ["Montevideo", "~placeOfDeath", "Eugen_Relgis"]
24 walkable: ["Montevideo", "~placeOfDeath", "Francisco_Antonino_Vidal"]
25 walkable: ["Montevideo", "~placeOfDeath", "Francisco_Antonio_Maciel"]
26 walkable: ["Montevideo", "~placeOfDeath", "Gigi_Peronace"]
27 walkable: ["Montevideo", "~placeOfDeath", "Herberts_Cukurs"]
28 walkable: ["Montevideo", "~placeOfDeath", "Hermann_Vallendor"]
29 walkable: ["Montevideo", "~placeOfDeath", "Inocencio_María_Yéregui"]
30 walkable: ["Montevideo", "~placeOfDeath", "Jorge_Pacheco_Areco"]
31 walkable: ["Montevideo", "~placeOfDeath", "José_Batlle_y_Ordóñez"]
32 walkable: ["Montevideo", "~placeOfDeath", "José_Eugenio_Ellauri"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 33. false_to_true — test index 2779

- Claim: The Alan B. Miller Hall was completed on 1st June 2009 and currently hosts the US Ontario Court of Justice.
- Nhãn thật: False; V4 đoán: True
- Entity_set: `["United_States", "Alan_B._Miller_Hall", "\"1 June 2009\"", "Ontario_Court_of_Justice"]`
- Top relations: `["completionDate", "architect", "buildingEndDate", "location", "country"]`; H: 1
- Candidate: 1 connected + 5 walkable; V4 thấy 6; artifact còn 0 path sau K.

```text
01 connected: ["Alan_B._Miller_Hall", "buildingEndDate", "\"1 June 2009\""]
02 walkable: ["Alan_B._Miller_Hall", "completionDate", "\"2009-06-01\""]
03 walkable: ["Alan_B._Miller_Hall", "architect", "Robert_A._M._Stern"]
04 walkable: ["Alan_B._Miller_Hall", "location", "Virginia"]
05 walkable: ["Alan_B._Miller_Hall", "location", "Williamsburg,_Virginia"]
06 walkable: ["Ontario_Court_of_Justice", "country", "\"Ontario\""]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 34. false_to_true — test index 1218

- Claim: Alfredo Zitarrosa died in Luquillo, Puerto Rico, a country led by Raul Fernando Sendic Rodriguez.
- Nhãn thật: False; V4 đoán: True
- Entity_set: `["Alfredo_Zitarrosa", "Raúl_Fernando_Sendic_Rodríguez", "Luquillo,_Puerto_Rico"]`
- Top relations: `["leaderName", "deathPlace", "placeOfDeath", "leaderTitle", "~placeOfDeath"]`; H: 1
- Candidate: 0 connected + 12 walkable; V4 thấy 12; artifact còn 0 path sau K.

```text
01 walkable: ["Alfredo_Zitarrosa", "deathPlace", "Montevideo"]
02 walkable: ["Alfredo_Zitarrosa", "deathPlace", "Uruguay"]
03 walkable: ["Alfredo_Zitarrosa", "placeOfDeath", "\"Montevideo, Uruguay\""]
04 walkable: ["Luquillo,_Puerto_Rico", "leaderName", "\"36\""]
05 walkable: ["Luquillo,_Puerto_Rico", "leaderName", "\"8\""]
06 walkable: ["Luquillo,_Puerto_Rico", "leaderName", "\"Hon. Jesús Márquez Rodríguez\""]
07 walkable: ["Luquillo,_Puerto_Rico", "leaderName", "Jesús_Márquez_Rodríguez"]
08 walkable: ["Luquillo,_Puerto_Rico", "leaderName", "Puerto_Rico_Senatorial_district_VIII"]
09 walkable: ["Luquillo,_Puerto_Rico", "leaderTitle", "\"Mayor\""]
10 walkable: ["Luquillo,_Puerto_Rico", "leaderTitle", "\"Representative dist.\""]
11 walkable: ["Luquillo,_Puerto_Rico", "leaderTitle", "\"Senatorial dist.\""]
12 walkable: ["Luquillo,_Puerto_Rico", "leaderTitle", "Mayor"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 35. false_to_true — test index 1834

- Claim: The song Mermaid by the band Train written by Jason Popson is on the Sony Music Entertainment record label.
- Nhãn thật: False; V4 đoán: True
- Entity_set: `["Mermaid_(Train_song)", "Sony_Music_Entertainment", "Jason_Popson"]`
- Top relations: `["author", "mediaType", "isbn", "recordLabel", "~author"]`; H: 1
- Candidate: 1 connected + 1 walkable; V4 thấy 2; artifact còn 0 path sau K.

```text
01 connected: ["Mermaid_(Train_song)", "recordLabel", "Sony_Music_Entertainment"]
02 walkable: ["Mermaid_(Train_song)", "recordLabel", "Columbia_Records"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 36. false_to_true — test index 2312

- Claim: The manager of A.F.C. Blackpool is Stuart Parker (footballer) who is attached to Chesterfield football club and plays for North Shields A.F.C.
- Nhãn thật: False; V4 đoán: True
- Entity_set: `["Chesterfield_F.C.", "A.F.C._Blackpool", "Stuart_Parker_(footballer)", "North_Shields_A.F.C."]`
- Top relations: `["~manager", "~team", "managerClub", "team", "~managerClub"]`; H: 1
- Candidate: 7 connected + 25 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 connected: ["A.F.C._Blackpool", "~team", "Stuart_Parker_(footballer)"]
02 connected: ["A.F.C._Blackpool", "~managerClub", "Stuart_Parker_(footballer)"]
03 connected: ["Chesterfield_F.C.", "~team", "Stuart_Parker_(footballer)"]
04 connected: ["Stuart_Parker_(footballer)", "~manager", "A.F.C._Blackpool"]
05 connected: ["Stuart_Parker_(footballer)", "managerClub", "A.F.C._Blackpool"]
06 connected: ["Stuart_Parker_(footballer)", "team", "A.F.C._Blackpool"]
07 connected: ["Stuart_Parker_(footballer)", "team", "Chesterfield_F.C."]
08 walkable: ["A.F.C._Blackpool", "~team", "Ciaran_Donnelly"]
09 walkable: ["A.F.C._Blackpool", "~team", "Ciaran_Donnelly__10"]
10 walkable: ["A.F.C._Blackpool", "~team", "Keigan_Parker"]
11 walkable: ["A.F.C._Blackpool", "~team", "Keigan_Parker__11"]
12 walkable: ["A.F.C._Blackpool", "~team", "Stuart_Parker_(footballer)__18"]
13 walkable: ["A.F.C._Blackpool", "~team", "Stuart_Parker_(footballer)__20"]
14 walkable: ["Chesterfield_F.C.", "~team", "1891–92_Sheffield_United_F.C._season"]
15 walkable: ["Chesterfield_F.C.", "~team", "1895–96_Newcastle_United_F.C._season"]
16 walkable: ["Chesterfield_F.C.", "~team", "1921–22_Nelson_F.C._season"]
17 walkable: ["Chesterfield_F.C.", "~team", "1975–76_Cardiff_City_F.C._season"]
18 walkable: ["Chesterfield_F.C.", "~team", "1982–83_Cardiff_City_F.C._season"]
19 walkable: ["Chesterfield_F.C.", "~team", "1990_Football_League_play-offs"]
20 walkable: ["Chesterfield_F.C.", "~team", "1994–95_Wolverhampton_Wanderers_F.C._season"]
21 walkable: ["Chesterfield_F.C.", "~team", "1995_Football_League_Third_Division_play-off_Final"]
22 walkable: ["Chesterfield_F.C.", "~team", "1995_Football_League_play-offs"]
23 walkable: ["Chesterfield_F.C.", "~team", "1995–96_Burnley_F.C._season"]
24 walkable: ["Chesterfield_F.C.", "~team", "1996–97_Burnley_F.C._season"]
25 walkable: ["Chesterfield_F.C.", "~team", "1996–97_Chesterfield_F.C._season"]
26 walkable: ["Chesterfield_F.C.", "~team", "1996–97_FA_Cup"]
27 walkable: ["Chesterfield_F.C.", "~team", "1997–98_Burnley_F.C._season"]
28 walkable: ["Chesterfield_F.C.", "~team", "1998–99_Burnley_F.C._season"]
29 walkable: ["Chesterfield_F.C.", "~team", "1998–99_Fulham_F.C._season"]
30 walkable: ["Chesterfield_F.C.", "~team", "1998–99_Manchester_City_F.C._season"]
31 walkable: ["Chesterfield_F.C.", "~team", "1998–99_Reading_F.C._season"]
32 walkable: ["Chesterfield_F.C.", "~team", "1999–2000_Burnley_F.C._season"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 37. false_to_true — test index 2374

- Claim: The College of William and Mary is the owner of the Alan B. Miller Hall in Corpus Christi, Texas, USA which began construction on 30 March, 2007.
- Nhãn thật: False; V4 đoán: True
- Entity_set: `["College_of_William_&_Mary", "\"30 March 2007\"", "Alan_B._Miller_Hall", "\"Corpus Christi, Texas, USA\""]`
- Top relations: `["~owner", "owner", "completionDate", "architect", "~location"]`; H: 1
- Candidate: 2 connected + 12 walkable; V4 thấy 14; artifact còn 0 path sau K.

```text
01 connected: ["Alan_B._Miller_Hall", "owner", "College_of_William_&_Mary"]
02 connected: ["College_of_William_&_Mary", "~owner", "Alan_B._Miller_Hall"]
03 walkable: ["\"Corpus Christi, Texas, USA\"", "~location", "World_Fantasy_Convention"]
04 walkable: ["Alan_B._Miller_Hall", "completionDate", "\"2009-06-01\""]
05 walkable: ["Alan_B._Miller_Hall", "architect", "Robert_A._M._Stern"]
06 walkable: ["College_of_William_&_Mary", "~owner", "Blow_Gymnasium"]
07 walkable: ["College_of_William_&_Mary", "~owner", "Busch_Field"]
08 walkable: ["College_of_William_&_Mary", "~owner", "Jimmye_Laycock_Football_Center"]
09 walkable: ["College_of_William_&_Mary", "~owner", "McCormack–Nagelsen_Tennis_Center"]
10 walkable: ["College_of_William_&_Mary", "~owner", "Millie_West_Tennis_Facility"]
11 walkable: ["College_of_William_&_Mary", "~owner", "Plumeri_Park"]
12 walkable: ["College_of_William_&_Mary", "~owner", "WCWM"]
13 walkable: ["College_of_William_&_Mary", "~owner", "William_&_Mary_Hall"]
14 walkable: ["College_of_William_&_Mary", "~owner", "Zable_Stadium"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 38. false_to_true — test index 1678

- Claim: A Wizard of Mars is published in Print ; Digital and was written by Diane Duane.
- Nhãn thật: False; V4 đoán: True
- Entity_set: `["A_Wizard_of_Mars", "Diane_Duane", "\"Print ; Digital\""]`
- Top relations: `["mediaType", "author", "~mediaType", "isbn", "~author"]`; H: 1
- Candidate: 2 connected + 30 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 connected: ["A_Wizard_of_Mars", "author", "Diane_Duane"]
02 connected: ["Diane_Duane", "~author", "A_Wizard_of_Mars"]
03 walkable: ["\"Print ; Digital\"", "~mediaType", "Sole_Agent_(novel)"]
04 walkable: ["\"Print ; Digital\"", "~mediaType", "Spy_in_Chancery_(novel)"]
05 walkable: ["\"Print ; Digital\"", "~mediaType", "Twenty-fourth_Level_(novel)"]
06 walkable: ["A_Wizard_of_Mars", "mediaType", "\"Print\""]
07 walkable: ["A_Wizard_of_Mars", "mediaType", "Hardcover"]
08 walkable: ["A_Wizard_of_Mars", "isbn", "\"978\""]
09 walkable: ["A_Wizard_of_Mars", "isbn", "\"978-0-15-204770-2\""]
10 walkable: ["Diane_Duane", "~author", "A_Wizard_Abroad"]
11 walkable: ["Diane_Duane", "~author", "A_Wizard_Alone"]
12 walkable: ["Diane_Duane", "~author", "Dark_Mirror_(Star_Trek_novel)"]
13 walkable: ["Diane_Duane", "~author", "Deep_Wizardry"]
14 walkable: ["Diane_Duane", "~author", "Doctor's_Orders_(novel)"]
15 walkable: ["Diane_Duane", "~author", "High_Wizardry"]
16 walkable: ["Diane_Duane", "~author", "My_Enemy,_My_Ally"]
17 walkable: ["Diane_Duane", "~author", "So_You_Want_to_Be_a_Wizard"]
18 walkable: ["Diane_Duane", "~author", "The_Book_of_Night_with_Moon_(novel)"]
19 walkable: ["Diane_Duane", "~author", "The_Romulan_Way"]
20 walkable: ["Diane_Duane", "~author", "The_Wizard's_Dilemma"]
21 walkable: ["Diane_Duane", "~author", "The_Wounded_Sky"]
22 walkable: ["Diane_Duane", "~author", "To_Visit_the_Queen"]
23 walkable: ["Diane_Duane", "~author", "Tom_Clancy's_Net_Force_Explorers:_Death_Match"]
24 walkable: ["Diane_Duane", "~author", "Tom_Clancy's_Net_Force_Explorers:_Deathworld"]
25 walkable: ["Diane_Duane", "~author", "Tom_Clancy's_Net_Force_Explorers:_End_Game"]
26 walkable: ["Diane_Duane", "~author", "Tom_Clancy's_Net_Force_Explorers:_One_is_the_Loneliest_Number"]
27 walkable: ["Diane_Duane", "~author", "Tom_Clancy's_Net_Force_Explorers:_Runaways"]
28 walkable: ["Diane_Duane", "~author", "Tom_Clancy's_Net_Force_Explorers:_Safe_House"]
29 walkable: ["Diane_Duane", "~author", "Tom_Clancy's_Net_Force_Explorers:_The_Deadliest_Game"]
30 walkable: ["Diane_Duane", "~author", "Tom_Clancy's_Net_Force_Explorers:_Virtual_Vandals"]
31 walkable: ["Diane_Duane", "~author", "Wizard's_Holiday"]
32 walkable: ["Diane_Duane", "~author", "Wizards_at_War"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 39. false_to_true — test index 2274

- Claim: Alfons Gorbach was born in Imst, Austria-Hungary and died in Mexico City,.
- Nhãn thật: False; V4 đoán: True
- Entity_set: `["Imst", "Alfons_Gorbach", "Austria-Hungary", "\"Mexico City,\""]`
- Top relations: `["birthPlace", "~deathPlace", "~birthPlace", "status", "placeOfBirth"]`; H: 1
- Candidate: 5 connected + 27 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 connected: ["Alfons_Gorbach", "birthPlace", "Austria-Hungary"]
02 connected: ["Alfons_Gorbach", "birthPlace", "Imst"]
03 connected: ["Alfons_Gorbach", "placeOfBirth", "Imst"]
04 connected: ["Austria-Hungary", "~birthPlace", "Alfons_Gorbach"]
05 connected: ["Imst", "~birthPlace", "Alfons_Gorbach"]
06 walkable: ["\"Mexico City,\"", "~deathPlace", "Mariano_Gálvez"]
07 walkable: ["\"Mexico City,\"", "~birthPlace", "Diana_Estrada"]
08 walkable: ["\"Mexico City,\"", "~birthPlace", "Ernesto_Cordero_Arroyo"]
09 walkable: ["\"Mexico City,\"", "~birthPlace", "Martha_Revuelta"]
10 walkable: ["\"Mexico City,\"", "~birthPlace", "Patricia_Espinosa"]
11 walkable: ["\"Mexico City,\"", "~birthPlace", "Ricardo_Bernal"]
12 walkable: ["Alfons_Gorbach", "birthPlace", "Austria"]
13 walkable: ["Alfons_Gorbach", "birthPlace", "County_of_Tyrol"]
14 walkable: ["Alfons_Gorbach", "birthPlace", "Tirol,_Austria"]
15 walkable: ["Alfons_Gorbach", "birthPlace", "Tyrol_(state)"]
16 walkable: ["Alfons_Gorbach", "placeOfBirth", "Austria"]
17 walkable: ["Alfons_Gorbach", "placeOfBirth", "Tirol,_Austria"]
18 walkable: ["Alfons_Gorbach", "placeOfBirth", "Tyrol_(state)"]
19 walkable: ["Austria-Hungary", "~deathPlace", "Adalbert_Stifter"]
20 walkable: ["Austria-Hungary", "~deathPlace", "Adam_Asnyk"]
21 walkable: ["Austria-Hungary", "~deathPlace", "Adolf_Lieben"]
22 walkable: ["Austria-Hungary", "~deathPlace", "Adolf_Mošinsky"]
23 walkable: ["Austria-Hungary", "~deathPlace", "Adolf_Waldinger"]
24 walkable: ["Austria-Hungary", "~deathPlace", "Agaton_Giller"]
25 walkable: ["Austria-Hungary", "~deathPlace", "Aladár_Andrássy"]
26 walkable: ["Austria-Hungary", "~deathPlace", "Albert_Chmielowski"]
27 walkable: ["Austria-Hungary", "~deathPlace", "Albert_Salomon_von_Rothschild"]
28 walkable: ["Austria-Hungary", "~deathPlace", "Albin_Csáky"]
29 walkable: ["Austria-Hungary", "~deathPlace", "Aleksander_Zawadzki_(naturalist)"]
30 walkable: ["Austria-Hungary", "~deathPlace", "Alexander_Wittek"]
31 walkable: ["Austria-Hungary", "~deathPlace", "Alexander_of_Battenberg"]
32 walkable: ["Austria-Hungary", "~deathPlace", "Alfred,_Hereditary_Prince_of_Saxe-Coburg_and_Gotha"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 40. false_to_true — test index 1921

- Claim: The epoch of 1000 Piazzia is on the 31st of July 2016 and it has a mass of 5.7 kilograms.
- Nhãn thật: False; V4 đoán: True
- Entity_set: `["\"2006-12-31\"", "\"5.7\"", "1000_Piazzia"]`
- Top relations: `["epoch", "mass", "periapsis", "Planet/apoapsis", "orbitalPeriod"]`; H: 1
- Candidate: 0 connected + 10 walkable; V4 thấy 10; artifact còn 0 path sau K.

```text
01 walkable: ["1000_Piazzia", "epoch", "\"2011-08-27\""]
02 walkable: ["1000_Piazzia", "epoch", "\"2015-06-27\""]
03 walkable: ["1000_Piazzia", "epoch", "\"August 27, 2011 (JD2455800.5)\""]
04 walkable: ["1000_Piazzia", "mass", "\"1.1\""]
05 walkable: ["1000_Piazzia", "mass", "\"1100.0\""]
06 walkable: ["1000_Piazzia", "periapsis", "\"3.52497e+11\""]
07 walkable: ["1000_Piazzia", "periapsis", "\"3.52737E11\""]
08 walkable: ["1000_Piazzia", "Planet/apoapsis", "\"5.96013E8\""]
09 walkable: ["1000_Piazzia", "orbitalPeriod", "\"1.7819974079999998E8\""]
10 walkable: ["1000_Piazzia", "orbitalPeriod", "\"488160.0\""]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 41. true_to_true_connected_control — test index 6199

- Claim: The College of William and Mary, located in Williamsburg Virginia is the location of the Mason School of Business located inside Alan B Miller Hall.
- Nhãn thật: True; V4 đoán: True
- Entity_set: `["Alan_B._Miller_Hall", "College_of_William_&_Mary", "Williamsburg,_Virginia", "Mason_School_of_Business"]`
- Top relations: `["city", "location", "headquarters", "locationTown", "isPartOf"]`; H: 1
- Candidate: 3 connected + 3 walkable; V4 thấy 6; artifact còn 0 path sau K.

```text
01 connected: ["Alan_B._Miller_Hall", "location", "Williamsburg,_Virginia"]
02 connected: ["College_of_William_&_Mary", "city", "Williamsburg,_Virginia"]
03 connected: ["Mason_School_of_Business", "city", "Williamsburg,_Virginia"]
04 walkable: ["Alan_B._Miller_Hall", "location", "Virginia"]
05 walkable: ["Williamsburg,_Virginia", "location", "\"Williamsburg, Virginia\""]
06 walkable: ["Williamsburg,_Virginia", "isPartOf", "Virginia"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 42. true_to_true_connected_control — test index 5216

- Claim: Alfredo Zitarrosa sings solo and his musical genre is Candombe.
- Nhãn thật: True; V4 đoán: True
- Entity_set: `["Alfredo_Zitarrosa", "Candombe", "\"solo_singer\""]`
- Top relations: `["genre", "~background", "background", "occupation", "birthPlace"]`; H: 1
- Candidate: 3 connected + 29 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 connected: ["\"solo_singer\"", "~background", "Alfredo_Zitarrosa"]
02 connected: ["Alfredo_Zitarrosa", "genre", "Candombe"]
03 connected: ["Alfredo_Zitarrosa", "background", "\"solo_singer\""]
04 walkable: ["\"solo_singer\"", "~background", "%22King%22_Bennie_Nawahi"]
05 walkable: ["\"solo_singer\"", "~background", "%22Weird_Al%22_Yankovic"]
06 walkable: ["\"solo_singer\"", "~background", "12_Gauge_(rapper)"]
07 walkable: ["\"solo_singer\"", "~background", "1987_(artist)"]
08 walkable: ["\"solo_singer\"", "~background", "2Mex"]
09 walkable: ["\"solo_singer\"", "~background", "2Play"]
10 walkable: ["\"solo_singer\"", "~background", "2_Chainz"]
11 walkable: ["\"solo_singer\"", "~background", "2_Pistols"]
12 walkable: ["\"solo_singer\"", "~background", "2face_Idibia"]
13 walkable: ["\"solo_singer\"", "~background", "360_(rapper)"]
14 walkable: ["\"solo_singer\"", "~background", "3D_Na'Tee"]
15 walkable: ["\"solo_singer\"", "~background", "40_Cal."]
16 walkable: ["\"solo_singer\"", "~background", "40_Glocc"]
17 walkable: ["\"solo_singer\"", "~background", "5Zic"]
18 walkable: ["\"solo_singer\"", "~background", "60_Second_Assassin_(emcee)"]
19 walkable: ["\"solo_singer\"", "~background", "6_Tre_G"]
20 walkable: ["\"solo_singer\"", "~background", "88-Keys"]
21 walkable: ["\"solo_singer\"", "~background", "9ice"]
22 walkable: ["\"solo_singer\"", "~background", "9th_Prince"]
23 walkable: ["\"solo_singer\"", "~background", "A*M*E"]
24 walkable: ["\"solo_singer\"", "~background", "A+_(rapper)"]
25 walkable: ["\"solo_singer\"", "~background", "A-L-X"]
26 walkable: ["\"solo_singer\"", "~background", "A-Lee"]
27 walkable: ["\"solo_singer\"", "~background", "A-Love"]
28 walkable: ["\"solo_singer\"", "~background", "A-Plus_(rapper)"]
29 walkable: ["\"solo_singer\"", "~background", "A-do"]
30 walkable: ["\"solo_singer\"", "~background", "A.B._Quintanilla"]
31 walkable: ["\"solo_singer\"", "~background", "A.D.O.R."]
32 walkable: ["\"solo_singer\"", "~background", "A.J._Crew"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 43. true_to_true_connected_control — test index 5407

- Claim: There is an area within Derbyshire called the Derbyshire dales where Bakewell pudding originated.
- Nhãn thật: True; V4 đoán: True
- Entity_set: `["Bakewell_pudding", "Derbyshire_Dales", "Derbyshire"]`
- Top relations: `["region", "country", "~region", "ingredient", "~ingredient"]`; H: 1
- Candidate: 2 connected + 30 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 connected: ["Bakewell_pudding", "region", "Derbyshire_Dales"]
02 connected: ["Derbyshire_Dales", "~region", "Bakewell_pudding"]
03 walkable: ["Bakewell_pudding", "country", "\"England\""]
04 walkable: ["Derbyshire", "region", "East_Midlands"]
05 walkable: ["Derbyshire", "country", "United_Kingdom"]
06 walkable: ["Derbyshire", "~region", "Arbor_Low"]
07 walkable: ["Derbyshire", "~region", "Bentley_Brook"]
08 walkable: ["Derbyshire", "~region", "Bentley_Brook,_Bradbourne"]
09 walkable: ["Derbyshire", "~region", "Burbage_Brook"]
10 walkable: ["Derbyshire", "~region", "Derbyshire_FA_Centenary_Cup"]
11 walkable: ["Derbyshire", "~region", "Derbyshire_Senior_Cup"]
12 walkable: ["Derbyshire", "~region", "Dovedale"]
13 walkable: ["Derbyshire", "~region", "Gib_Hill"]
14 walkable: ["Derbyshire", "~region", "Henmore_Brook"]
15 walkable: ["Derbyshire", "~region", "Markeaton_Brook"]
16 walkable: ["Derbyshire", "~region", "Peak_District"]
17 walkable: ["Derbyshire", "~region", "Randall_Carr"]
18 walkable: ["Derbyshire", "~region", "River_Alport"]
19 walkable: ["Derbyshire", "~region", "River_Amber"]
20 walkable: ["Derbyshire", "~region", "River_Ashop"]
21 walkable: ["Derbyshire", "~region", "River_Derwent,_Derbyshire"]
22 walkable: ["Derbyshire", "~region", "River_Dove,_Central_England"]
23 walkable: ["Derbyshire", "~region", "River_Ecclesbourne"]
24 walkable: ["Derbyshire", "~region", "River_Erewash"]
25 walkable: ["Derbyshire", "~region", "River_Lathkill"]
26 walkable: ["Derbyshire", "~region", "River_Mease"]
27 walkable: ["Derbyshire", "~region", "River_Noe"]
28 walkable: ["Derbyshire", "~region", "River_Trent"]
29 walkable: ["Derbyshire", "~region", "River_Westend"]
30 walkable: ["Derbyshire", "~region", "River_Wye,_Derbyshire"]
31 walkable: ["Derbyshire", "~region", "Swarkestone_Bridge"]
32 walkable: ["Derbyshire", "~region", "The_Bull_Ring"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 44. true_to_true_connected_control — test index 5468

- Claim: Acura is a division of Honda that make the Acura TLX.
- Nhãn thật: True; V4 đoán: True
- Entity_set: `["Acura_TLX", "Acura", "Honda"]`
- Top relations: `["manufacturer", "builder", "~division", "designCompany", "~r3Surface"]`; H: 1
- Candidate: 2 connected + 0 walkable; V4 thấy 2; artifact còn 0 path sau K.

```text
01 connected: ["Acura", "~division", "Honda"]
02 connected: ["Acura_TLX", "manufacturer", "Honda"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 45. true_to_true_connected_control — test index 5211

- Claim: Alfredo Zitarrosa was born in Montevideo where the leader is the politician Daniel Martínez.
- Nhãn thật: True; V4 đoán: True
- Entity_set: `["Alfredo_Zitarrosa", "\"Daniel_Martínez_(politician)\"", "Montevideo"]`
- Top relations: `["birthPlace", "leaderName", "placeOfBirth", "~placeOfBirth", "primeMinister"]`; H: 1
- Candidate: 2 connected + 30 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 connected: ["Alfredo_Zitarrosa", "birthPlace", "Montevideo"]
02 connected: ["Montevideo", "leaderName", "\"Daniel_Martínez_(politician)\""]
03 walkable: ["Alfredo_Zitarrosa", "birthPlace", "Uruguay"]
04 walkable: ["Alfredo_Zitarrosa", "placeOfBirth", "\"Montevideo, Uruguay\""]
05 walkable: ["Montevideo", "leaderName", "Daniel_Martínez"]
06 walkable: ["Montevideo", "~placeOfBirth", "Abel_Carlevaro"]
07 walkable: ["Montevideo", "~placeOfBirth", "Adolfo_Barán"]
08 walkable: ["Montevideo", "~placeOfBirth", "Adrian_Vallarino"]
09 walkable: ["Montevideo", "~placeOfBirth", "Adrián_Berbia"]
10 walkable: ["Montevideo", "~placeOfBirth", "Adrián_Caetano"]
11 walkable: ["Montevideo", "~placeOfBirth", "Adrián_Gunino"]
12 walkable: ["Montevideo", "~placeOfBirth", "Alberto_Breccia"]
13 walkable: ["Montevideo", "~placeOfBirth", "Alberto_Fay"]
14 walkable: ["Montevideo", "~placeOfBirth", "Alberto_Héber_Usher"]
15 walkable: ["Montevideo", "~placeOfBirth", "Alberto_Ortega"]
16 walkable: ["Montevideo", "~placeOfBirth", "Alberto_Uria"]
17 walkable: ["Montevideo", "~placeOfBirth", "Alberto_Varela"]
18 walkable: ["Montevideo", "~placeOfBirth", "Alcides_Silveira"]
19 walkable: ["Montevideo", "~placeOfBirth", "Alejandro_Acosta"]
20 walkable: ["Montevideo", "~placeOfBirth", "Alejandro_Atchugarry"]
21 walkable: ["Montevideo", "~placeOfBirth", "Alejandro_Correa"]
22 walkable: ["Montevideo", "~placeOfBirth", "Alejandro_Curbelo"]
23 walkable: ["Montevideo", "~placeOfBirth", "Alejandro_Foglia"]
24 walkable: ["Montevideo", "~placeOfBirth", "Alejandro_González_(Uruguayan_footballer)"]
25 walkable: ["Montevideo", "~placeOfBirth", "Alejandro_Grandi"]
26 walkable: ["Montevideo", "~placeOfBirth", "Alejandro_Mello"]
27 walkable: ["Montevideo", "~placeOfBirth", "Alejandro_Meloño"]
28 walkable: ["Montevideo", "~placeOfBirth", "Alejandro_Traversa"]
29 walkable: ["Montevideo", "~placeOfBirth", "Alejandro_Zaffaroni"]
30 walkable: ["Montevideo", "~placeOfBirth", "Alexander_Rosso"]
31 walkable: ["Montevideo", "~placeOfBirth", "Alexis_Rolín"]
32 walkable: ["Montevideo", "~placeOfBirth", "Alfonso_Cardoso"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 46. true_to_true_no_connected_control — test index 5742

- Claim: Frederick County, Maryland is to the southwest of Adams County, Pennsylvania, where the 11th Mississippi Infantry Monument is located.
- Nhãn thật: True; V4 đoán: True
- Entity_set: `["Frederick_County,_Maryland", "11th_Mississippi_Infantry_Monument", "Adams_County,_Pennsylvania"]`
- Top relations: `["~northeast", "location", "northeast", "headquarters", "anthem"]`; H: 1
- Candidate: 0 connected + 1 walkable; V4 thấy 1; artifact còn 0 path sau K.

```text
01 walkable: ["Frederick_County,_Maryland", "northeast", "\"Adams County, Pennsylvania\""]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 47. true_to_true_no_connected_control — test index 7239

- Claim: If only the James L. Pugh stands in Adams County, Pennsylvania.
- Nhãn thật: True; V4 đoán: True
- Entity_set: `["Adams_County,_Pennsylvania", "\"Pennsylvania\"", "James_L._Pugh"]`
- Top relations: `["material", "isPartOf", "~location", "foundationPlace", "dedicatedTo"]`; H: 1
- Candidate: 0 connected + 16 walkable; V4 thấy 16; artifact còn 0 path sau K.

```text
01 walkable: ["\"Pennsylvania\"", "~location", "Houdini_Museum"]
02 walkable: ["\"Pennsylvania\"", "~location", "Idlewild_and_Soak_Zone"]
03 walkable: ["\"Pennsylvania\"", "~location", "Knoebels_Amusement_Resort"]
04 walkable: ["\"Pennsylvania\"", "~location", "Lakemont_Park"]
05 walkable: ["\"Pennsylvania\"", "~location", "Leonard_Davis_Institute_of_Health_Economics"]
06 walkable: ["\"Pennsylvania\"", "~location", "List_of_Pennsylvania_weather_records"]
07 walkable: ["\"Pennsylvania\"", "~location", "The_Farnsworth_House_Inn"]
08 walkable: ["\"Pennsylvania\"", "~location", "Uplifting_Entertainment"]
09 walkable: ["\"Pennsylvania\"", "~location", "Washington_Run_Railroad"]
10 walkable: ["Adams_County,_Pennsylvania", "~location", "Camp_Colt,_Pennsylvania"]
11 walkable: ["Adams_County,_Pennsylvania", "~location", "Carbaugh_Run_Rhyolite_Quarry_Site"]
12 walkable: ["Adams_County,_Pennsylvania", "~location", "Cemetery_Ridge"]
13 walkable: ["Adams_County,_Pennsylvania", "~location", "East_Cemetery_Hill"]
14 walkable: ["Adams_County,_Pennsylvania", "~location", "Gettysburg_Battlefield_Historic_District"]
15 walkable: ["Adams_County,_Pennsylvania", "~location", "Gettysburg_Electric_Railway"]
16 walkable: ["Adams_County,_Pennsylvania", "~location", "Gettysburg_National_Military_Park"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 48. true_to_true_no_connected_control — test index 5743

- Claim: The location of the 11th Mississippi Infantry Monument is Adams County, Pennsylvania, which has Frederick County, Maryland to its southwest.
- Nhãn thật: True; V4 đoán: True
- Entity_set: `["Frederick_County,_Maryland", "11th_Mississippi_Infantry_Monument", "Adams_County,_Pennsylvania"]`
- Top relations: `["location", "~northeast", "northeast", "~leaderName", "headquarters"]`; H: 1
- Candidate: 0 connected + 1 walkable; V4 thấy 1; artifact còn 0 path sau K.

```text
01 walkable: ["Frederick_County,_Maryland", "northeast", "\"Adams County, Pennsylvania\""]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 49. true_to_true_no_connected_control — test index 7229

- Claim: I imagined that Buttermilk pie includes vegetables as ingredients and comes from the Karnataka region.
- Nhãn thật: True; V4 đoán: True
- Entity_set: `["Karnataka", "Vegetable", "Buttermilk_pie"]`
- Top relations: `["ingredient", "country", "mainIngredient", "ingredientName", "region"]`; H: 1
- Candidate: 0 connected + 13 walkable; V4 thấy 13; artifact còn 0 path sau K.

```text
01 walkable: ["Buttermilk_pie", "ingredient", "Butter"]
02 walkable: ["Buttermilk_pie", "ingredient", "Buttermilk"]
03 walkable: ["Buttermilk_pie", "ingredient", "Egg_(food)"]
04 walkable: ["Buttermilk_pie", "ingredient", "Sugar"]
05 walkable: ["Buttermilk_pie", "ingredient", "Wheat_flour"]
06 walkable: ["Buttermilk_pie", "mainIngredient", "Butter"]
07 walkable: ["Buttermilk_pie", "mainIngredient", "Buttermilk"]
08 walkable: ["Buttermilk_pie", "mainIngredient", "Egg_(food)"]
09 walkable: ["Buttermilk_pie", "mainIngredient", "Sugar"]
10 walkable: ["Buttermilk_pie", "mainIngredient", "Wheat_flour"]
11 walkable: ["Buttermilk_pie", "ingredientName", "\"Buttermilk,wheat flour,butter,eggs,sugar\""]
12 walkable: ["Buttermilk_pie", "region", "Southern_United_States"]
13 walkable: ["Karnataka", "country", "India"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

## 50. true_to_true_no_connected_control — test index 7230

- Claim: I imagined that the birth place of Feng Guozhang was Paraguay and Asuncion is where he died.
- Nhãn thật: True; V4 đoán: True
- Entity_set: `["Asunción", "Paraguay", "Feng_Guozhang"]`
- Top relations: `["~birthPlace", "deathPlace", "status", "birthDate", "bird"]`; H: 1
- Candidate: 0 connected + 32 walkable; V4 thấy 32; artifact còn 0 path sau K.

```text
01 walkable: ["Asunción", "~birthPlace", "Abraham_Acevedo"]
02 walkable: ["Asunción", "~birthPlace", "Adolfino_Cañete"]
03 walkable: ["Asunción", "~birthPlace", "Adolfo_Jara_Heyn"]
04 walkable: ["Asunción", "~birthPlace", "Adolfo_Vaccaro"]
05 walkable: ["Asunción", "~birthPlace", "Agustín_Barboza"]
06 walkable: ["Asunción", "~birthPlace", "Alba_Riquelme"]
07 walkable: ["Asunción", "~birthPlace", "Alberto_Jara_Saguier"]
08 walkable: ["Asunción", "~birthPlace", "Alejandro_Guanes"]
09 walkable: ["Asunción", "~birthPlace", "Alfredo_Mazacotte"]
10 walkable: ["Asunción", "~birthPlace", "Alonso_de_Escobar"]
11 walkable: ["Asunción", "~birthPlace", "Andrea_Prono"]
12 walkable: ["Asunción", "~birthPlace", "Andrea_Quattrocchi"]
13 walkable: ["Asunción", "~birthPlace", "Andrés_Barbero"]
14 walkable: ["Asunción", "~birthPlace", "Andrés_Duarte"]
15 walkable: ["Asunción", "~birthPlace", "Anna_Camila_Pirelli"]
16 walkable: ["Asunción", "~birthPlace", "Antonio_Leon_(swimmer)"]
17 walkable: ["Asunción", "~birthPlace", "Antonio_Ortiz_Mayans"]
18 walkable: ["Asunción", "~birthPlace", "Antony_Silva"]
19 walkable: ["Asunción", "~birthPlace", "Aquilino_Villalba"]
20 walkable: ["Asunción", "~birthPlace", "Arnaldo_Espínola"]
21 walkable: ["Asunción", "~birthPlace", "Arsenio_Erico"]
22 walkable: ["Asunción", "~birthPlace", "Attila_Sallustro"]
23 walkable: ["Asunción", "~birthPlace", "Augusto_Roa_Bastos"]
24 walkable: ["Asunción", "~birthPlace", "Aureliano_Torres"]
25 walkable: ["Asunción", "~birthPlace", "Benny_Ricardo"]
26 walkable: ["Asunción", "~birthPlace", "Bernardo_Medina"]
27 walkable: ["Asunción", "~birthPlace", "Berta_Rojas"]
28 walkable: ["Asunción", "~birthPlace", "Brian_Montenegro"]
29 walkable: ["Asunción", "~birthPlace", "Bruno_Aranda_Pertile"]
30 walkable: ["Asunción", "~birthPlace", "Camila_Giangreco_Campiz"]
31 walkable: ["Asunción", "~birthPlace", "Carlos_Antonio_López"]
32 walkable: ["Asunción", "~birthPlace", "Carlos_Bonet"]
```

- Vế 1 và path chứng minh: ...
- Vế 2 và path chứng minh: ...
- Vế khác nếu có và path chứng minh: ...
- Kết luận sơ bộ và lý do: ...

