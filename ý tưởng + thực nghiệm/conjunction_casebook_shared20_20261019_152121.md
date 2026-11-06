# Conjunction: kiểm tra từng vế trên dev

Dùng nhãn/Evidence dev **chỉ để chẩn đoán**, không đưa vào R3/V4. Không thấy path không chứng minh mệnh đề sai trong KG mở. Đây là mẫu case để đọc thủ công, chưa phải kết luận lỗi do R3 hay V4.

Nguồn: 13266 claim; bỏ qua 429 claim bị giới hạn duyệt; V4 xem tối đa 32 path.

## FALSE: first5 đúng, ranked5 sai: 8 claim

### Well it comes from the Middlesbrough region.

Gold label: 0; first5: 0; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Amatriciana_sauce": [
    [
      "region"
    ],
    [
      "ingredient"
    ]
  ],
  "Guanciale": [
    [
      "~ingredient"
    ]
  ],
  "Middlesbrough": [
    [
      "~region"
    ]
  ]
}
```

**Connected chung (1):**
1. `["Amatriciana_sauce", "ingredient", "Guanciale"]`

**Walkable first5 (5):**
1. `["Amatriciana_sauce", "ingredient", "Olive_oil"]`
2. `["Amatriciana_sauce", "ingredient", "Pecorino_Romano"]`
3. `["Amatriciana_sauce", "ingredient", "Tomato"]`
4. `["Amatriciana_sauce", "mainIngredient", "\"Tomatoes, guanciale, cheese , olive oil\""]`
5. `["Amatriciana_sauce", "course", "Italian_meal_structure"]`

**Walkable ranked5 (5):**
1. `["Middlesbrough", "~region", "Middlesbrough_meteorite"]`
2. `["Amatriciana_sauce", "ingredient", "Olive_oil"]`
3. `["Amatriciana_sauce", "ingredient", "Pecorino_Romano"]`
4. `["Amatriciana_sauce", "ingredient", "Tomato"]`
5. `["Amatriciana_sauce", "mainIngredient", "\"Tomatoes, guanciale, cheese , olive oil\""]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### The Chevrolet Cavalier  Third generation  1 and the Fiat Croma are similar means of transport and the latter is also related to the Saab 9000.

Gold label: 0; first5: 0; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Fiat_Croma": [
    [
      "related"
    ],
    [
      "~relatedMeanOfTransportation"
    ]
  ],
  "Saab_9000": [
    [
      "~related"
    ]
  ],
  "Chevrolet_Cavalier__Third_generation__1": [
    [
      "relatedMeanOfTransportation"
    ]
  ]
}
```

**Connected chung (5):**
1. `["Fiat_Croma", "related", "Saab_9000"]`
2. `["Fiat_Croma", "~related", "Saab_9000"]`
3. `["Saab_9000", "relatedMeanOfTransportation", "Fiat_Croma"]`
4. `["Saab_9000", "related", "Fiat_Croma"]`
5. `["Saab_9000", "~related", "Fiat_Croma"]`

**Walkable first5 (5):**
1. `["Chevrolet_Cavalier__Third_generation__1", "relatedMeanOfTransportation", "Pontiac_Sunfire"]`
2. `["Chevrolet_Cavalier__Third_generation__1", "successor", "Chevrolet_Cobalt"]`
3. `["Fiat_Croma", "related", "Alfa_Romeo_164"]`
4. `["Fiat_Croma", "related", "Cadillac_BLS"]`
5. `["Fiat_Croma", "related", "Lancia_Thema"]`

**Walkable ranked5 (5):**
1. `["Fiat_Croma", "related", "Saab_9-3"]`
2. `["Fiat_Croma", "~related", "Chevrolet_Malibu"]`
3. `["Fiat_Croma", "~related", "Saab_9-3"]`
4. `["Chevrolet_Cavalier__Third_generation__1", "relatedMeanOfTransportation", "Pontiac_Sunfire"]`
5. `["Fiat_Croma", "related", "Alfa_Romeo_164"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Albert B. White's successor Gallienus died in Charleston, West Virginia.

Gold label: 0; first5: 0; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Albert_B._White": [
    [
      "successor"
    ]
  ],
  "Charleston,_West_Virginia": [
    [
      "~deathPlace"
    ]
  ],
  "Gallienus": [
    [
      "deathPlace"
    ],
    [
      "~successor"
    ]
  ]
}
```

**Connected chung (0):**
- Không có path trong đầu vào V4.

**Walkable first5 (5):**
1. `["Albert_B._White", "successor", "William_M._O._Dawson"]`
2. `["Albert_B._White", "deathPlace", "Parkersburg,_West_Virginia"]`
3. `["Albert_B._White", "office", "\"Governor of West Virginia\""]`
4. `["Albert_B._White", "~successor", "George_W._Atkinson"]`
5. `["Charleston,_West_Virginia", "~birthPlace", "Alec_Ross_(innovator)"]`

**Walkable ranked5 (5):**
1. `["Albert_B._White", "successor", "William_M._O._Dawson"]`
2. `["Albert_B._White", "deathPlace", "Parkersburg,_West_Virginia"]`
3. `["Albert_B._White", "office", "\"Governor of West Virginia\""]`
4. `["Albert_B._White", "~successor", "George_W._Atkinson"]`
5. `["Charleston,_West_Virginia", "~birthPlace", "Anne_White"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Yes! Peter Vogel was born on May 2, 1908 in the German Empire.

Gold label: 0; first5: 0; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "\"1908-05-02\"": [
    [
      "~birthDate"
    ]
  ],
  "German_Empire": [
    [
      "~birthPlace"
    ]
  ],
  "Peter_Vogel_(actor)": [
    [
      "birthDate"
    ],
    [
      "birthPlace"
    ]
  ]
}
```

**Connected chung (0):**
- Không có path trong đầu vào V4.

**Walkable first5 (5):**
1. `["\"1908-05-02\"", "~birthDate", "Alister_Watson"]`
2. `["\"1908-05-02\"", "~birthDate", "Allan_Liddell"]`
3. `["\"1908-05-02\"", "~birthDate", "Bill_Harvey_(footballer,_born_1908)"]`
4. `["\"1908-05-02\"", "~birthDate", "Ellis_Hagler"]`
5. `["\"1908-05-02\"", "~birthDate", "Frank_Rowlett"]`

**Walkable ranked5 (5):**
1. `["\"1908-05-02\"", "~birthDate", "Bill_Harvey_(footballer,_born_1908)"]`
2. `["Peter_Vogel_(actor)", "occupation", "Peter_Vogel_(actor)__1"]`
3. `["\"1908-05-02\"", "~birthDate", "Alister_Watson"]`
4. `["\"1908-05-02\"", "~birthDate", "Allan_Liddell"]`
5. `["\"1908-05-02\"", "~birthDate", "Ellis_Hagler"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Hugh Griffith was born on March 15, 1932 and received a Bachelor of Science degree at the University of Texas at Austin in 1955.

Gold label: 0; first5: 0; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "\"1932-03-15\"": [
    [
      "~birthDate"
    ]
  ],
  "\"UT Austin, B.S. 1955\"": [
    [
      "~almaMater"
    ]
  ],
  "Hugh_Griffith": [
    [
      "birthDate"
    ],
    [
      "almaMater"
    ]
  ]
}
```

**Connected chung (0):**
- Không có path trong đầu vào V4.

**Walkable first5 (5):**
1. `["\"1932-03-15\"", "~birthDate", "Alan_Bean"]`
2. `["\"1932-03-15\"", "~birthDate", "Alexey_Gogua"]`
3. `["\"1932-03-15\"", "~birthDate", "Arif_Mardin"]`
4. `["\"1932-03-15\"", "~birthDate", "John_Humphreys_(fencer)"]`
5. `["\"1932-03-15\"", "~birthDate", "List_of_Playboy_Playmates_of_1954"]`

**Walkable ranked5 (5):**
1. `["Hugh_Griffith", "occupation", "Hugh_Griffith__1"]`
2. `["\"1932-03-15\"", "~birthDate", "Alan_Bean"]`
3. `["\"1932-03-15\"", "~birthDate", "Alexey_Gogua"]`
4. `["\"1932-03-15\"", "~birthDate", "Arif_Mardin"]`
5. `["\"1932-03-15\"", "~birthDate", "John_Humphreys_(fencer)"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Alan Jaggs was the editor and Joseph J. Lilley was the composer in a 89 minute film called 'English Without Tears.'

Gold label: 0; first5: 0; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "English_Without_Tears": [
    [
      "musicComposer"
    ],
    [
      "editing"
    ],
    [
      "runtime"
    ]
  ],
  "Alan_Jaggs": [
    [
      "~editing"
    ]
  ],
  "\"89.0\"": [
    [
      "~runtime"
    ]
  ],
  "Joseph_J._Lilley": [
    [
      "~musicComposer"
    ]
  ]
}
```

**Connected chung (2):**
1. `["Alan_Jaggs", "~editing", "English_Without_Tears"]`
2. `["English_Without_Tears", "editing", "Alan_Jaggs"]`

**Walkable first5 (5):**
1. `["English_Without_Tears", "musicComposer", "Nicholas_Brodszky"]`
2. `["Joseph_J._Lilley", "~musicComposer", "Beau_James"]`
3. `["Joseph_J._Lilley", "~musicComposer", "Blue_Hawaii"]`
4. `["Joseph_J._Lilley", "~musicComposer", "Fun_in_Acapulco"]`
5. `["Joseph_J._Lilley", "~musicComposer", "G.I._Blues"]`

**Walkable ranked5 (5):**
1. `["Joseph_J._Lilley", "~musicComposer", "Isn't_It_Romantic%3F_(film)"]`
2. `["Joseph_J._Lilley", "~musicComposer", "The_Forest_Rangers_(film)"]`
3. `["Joseph_J._Lilley", "~musicComposer", "The_Mating_Season_(film)"]`
4. `["English_Without_Tears", "musicComposer", "Nicholas_Brodszky"]`
5. `["Joseph_J._Lilley", "~musicComposer", "Beau_James"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### S.A. corporation Hypermarcas, which was founded on January 1st, 2001, has a subsidiary called Extreme Championship Wrestling.

Gold label: 0; first5: 0; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Hypermarcas": [
    [
      "foundingYear"
    ],
    [
      "type"
    ],
    [
      "subsidiary"
    ]
  ],
  "\"2001-01-01\"": [
    [
      "~foundingYear"
    ]
  ],
  "S.A._(corporation)": [
    [
      "~type"
    ]
  ],
  "Extreme_Championship_Wrestling": [
    [
      "~subsidiary"
    ]
  ]
}
```

**Connected chung (2):**
1. `["Hypermarcas", "type", "S.A._(corporation)"]`
2. `["Hypermarcas", "foundingYear", "\"2001-01-01\""]`

**Walkable first5 (5):**
1. `["Extreme_Championship_Wrestling", "type", "Privately_held_company"]`
2. `["Extreme_Championship_Wrestling", "industry", "Professional_wrestling"]`
3. `["Extreme_Championship_Wrestling", "product", "WWE_Network"]`
4. `["Extreme_Championship_Wrestling", "foundingYear", "\"1992\""]`
5. `["Hypermarcas", "subsidiary", "Mantecorp"]`

**Walkable ranked5 (5):**
1. `["Hypermarcas", "subsidiary", "Mantecorp"]`
2. `["Extreme_Championship_Wrestling", "industry", "Professional_wrestling"]`
3. `["Hypermarcas", "foundingYear", "\"2001\""]`
4. `["Extreme_Championship_Wrestling", "type", "Privately_held_company"]`
5. `["Extreme_Championship_Wrestling", "product", "WWE_Network"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Hypermarcas is located in Bohicon, Brazil, where the President of the Supreme Federal Court is a leader title.

Gold label: 0; first5: 0; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Hypermarcas": [
    [
      "location"
    ],
    [
      "location"
    ]
  ],
  "Brazil": [
    [
      "leaderTitle"
    ],
    [
      "~location"
    ]
  ],
  "\"President of the Supreme Federal Court\"": [
    [
      "~leaderTitle"
    ]
  ],
  "\"Bohicon\"": [
    [
      "~location"
    ]
  ]
}
```

**Connected chung (3):**
1. `["\"President of the Supreme Federal Court\"", "~leaderTitle", "Brazil"]`
2. `["Brazil", "leaderTitle", "\"President of the Supreme Federal Court\""]`
3. `["Brazil", "~location", "Hypermarcas"]`

**Walkable first5 (5):**
1. `["\"Bohicon\"", "~location", "Bohicon"]`
2. `["Brazil", "leaderTitle", "\"President of the Federal Senate\""]`
3. `["Brazil", "leaderTitle", "\"President of theChamber of Deputies\""]`
4. `["Brazil", "leaderTitle", "\"President\""]`
5. `["Brazil", "leaderTitle", "\"Vice President\""]`

**Walkable ranked5 (5):**
1. `["Brazil", "leaderTitle", "President_of_the_Federal_Senate_(Brazil)"]`
2. `["Brazil", "leaderTitle", "Supreme_Federal_Court"]`
3. `["Brazil", "leaderTitle", "\"President of the Federal Senate\""]`
4. `["Brazil", "leaderTitle", "President_of_Brazil"]`
5. `["Brazil", "leaderTitle", "President_of_the_Chamber_of_Deputies_(Brazil)"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

## FALSE: cả hai đều sai: 144 claim

### Acme Airport is located in Asherton, Texas in the United States.

Gold label: 0; first5: 1; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Asherton,_Texas": [
    [
      "country"
    ],
    [
      "~location"
    ]
  ],
  "United_States": [
    [
      "~country"
    ]
  ],
  "Acme_Airport": [
    [
      "location"
    ]
  ]
}
```

**Connected chung (2):**
1. `["Asherton,_Texas", "country", "United_States"]`
2. `["Asherton,_Texas", "subdivisionName", "United_States"]`

**Walkable first5 (5):**
1. `["Acme_Airport", "location", "\"Kneehill County, near Acme, Alberta\""]`
2. `["Acme_Airport", "location", "Acme,_Alberta"]`
3. `["Acme_Airport", "location", "Kneehill_County"]`
4. `["Asherton,_Texas", "~location", "Asher_and_Mary_Isabelle_Richardson_House"]`
5. `["Asherton,_Texas", "isPartOf", "Dimmit_County,_Texas"]`

**Walkable ranked5 (5):**
1. `["Acme_Airport", "location", "\"Kneehill County, near Acme, Alberta\""]`
2. `["Acme_Airport", "location", "Acme,_Alberta"]`
3. `["Asherton,_Texas", "isPartOf", "Dimmit_County,_Texas"]`
4. `["Asherton,_Texas", "isPartOf", "Texas"]`
5. `["Asherton,_Texas", "subdivisionName", "Dimmit_County,_Texas"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Yeah, Aurakles was created by Ian James Corlett and Len Wein!

Gold label: 0; first5: 1; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Aurakles": [
    [
      "creator"
    ],
    [
      "creators"
    ]
  ],
  "Len_Wein": [
    [
      "~creators"
    ]
  ],
  "Ian_James_Corlett": [
    [
      "~creator"
    ]
  ]
}
```

**Connected chung (3):**
1. `["Aurakles", "creator", "Len_Wein"]`
2. `["Len_Wein", "~creators", "Aurakles"]`
3. `["Len_Wein", "~creator", "Aurakles"]`

**Walkable first5 (5):**
1. `["Aurakles", "creator", "Dick_Dillin"]`
2. `["Ian_James_Corlett", "~creator", "Being_Ian"]`
3. `["Ian_James_Corlett", "~creator", "Yvon_of_the_Yukon"]`
4. `["Ian_James_Corlett", "nationality", "\"Canadian\""]`
5. `["Len_Wein", "~creators", "Abby_Holland"]`

**Walkable ranked5 (5):**
1. `["Ian_James_Corlett", "~creator", "Being_Ian"]`
2. `["Aurakles", "creator", "Dick_Dillin"]`
3. `["Ian_James_Corlett", "~creator", "Yvon_of_the_Yukon"]`
4. `["Ian_James_Corlett", "nationality", "\"Canadian\""]`
5. `["Len_Wein", "~creators", "Abby_Holland"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Ross Duffer and Len Wein created the character Aurakles!

Gold label: 0; first5: 1; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Aurakles": [
    [
      "creator"
    ],
    [
      "creators"
    ]
  ],
  "Len_Wein": [
    [
      "~creators"
    ]
  ],
  "\"Ross Duffer\"": [
    [
      "~creator"
    ]
  ]
}
```

**Connected chung (3):**
1. `["Aurakles", "creator", "Len_Wein"]`
2. `["Len_Wein", "~creators", "Aurakles"]`
3. `["Len_Wein", "~creator", "Aurakles"]`

**Walkable first5 (5):**
1. `["\"Ross Duffer\"", "~creator", "Stranger_Things_(TV_series)"]`
2. `["Aurakles", "creator", "Dick_Dillin"]`
3. `["Len_Wein", "~creators", "Abby_Holland"]`
4. `["Len_Wein", "~creators", "Alpha_the_Ultimate_Mutant"]`
5. `["Len_Wein", "~creators", "Alternative_versions_of_Colossus"]`

**Walkable ranked5 (5):**
1. `["\"Ross Duffer\"", "~creator", "Stranger_Things_(TV_series)"]`
2. `["Aurakles", "creator", "Dick_Dillin"]`
3. `["Len_Wein", "~creators", "Abby_Holland"]`
4. `["Len_Wein", "~creators", "Alpha_the_Ultimate_Mutant"]`
5. `["Len_Wein", "~creators", "Alternative_versions_of_Colossus"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Bandeja paisa (white wine) is part of Colombian cuisine.

Gold label: 0; first5: 1; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Bandeja_paisa": [
    [
      "ingredient"
    ],
    [
      "country"
    ]
  ],
  "Colombian_cuisine": [
    [
      "~country"
    ]
  ],
  "White_wine": [
    [
      "~ingredient"
    ]
  ]
}
```

**Connected chung (1):**
1. `["Bandeja_paisa", "country", "Colombian_cuisine"]`

**Walkable first5 (5):**
1. `["Bandeja_paisa", "ingredient", "Arepa"]`
2. `["Bandeja_paisa", "ingredient", "Avocado"]`
3. `["Bandeja_paisa", "ingredient", "Black_pudding"]`
4. `["Bandeja_paisa", "ingredient", "Chicharrón"]`
5. `["Bandeja_paisa", "ingredient", "Chorizo"]`

**Walkable ranked5 (5):**
1. `["Bandeja_paisa", "ingredient", "Arepa"]`
2. `["Bandeja_paisa", "ingredient", "Avocado"]`
3. `["Bandeja_paisa", "ingredient", "Black_pudding"]`
4. `["Bandeja_paisa", "ingredient", "Chicharrón"]`
5. `["Bandeja_paisa", "ingredient", "Chorizo"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### buckwheat is an ingredient of Bandeja paisa which is a dish from Colombian.

Gold label: 0; first5: 1; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Bandeja_paisa": [
    [
      "ingredient"
    ],
    [
      "country"
    ]
  ],
  "Colombian_cuisine": [
    [
      "~country"
    ]
  ],
  "Buckwheat": [
    [
      "~ingredient"
    ]
  ]
}
```

**Connected chung (1):**
1. `["Bandeja_paisa", "country", "Colombian_cuisine"]`

**Walkable first5 (5):**
1. `["Bandeja_paisa", "ingredient", "Arepa"]`
2. `["Bandeja_paisa", "ingredient", "Avocado"]`
3. `["Bandeja_paisa", "ingredient", "Black_pudding"]`
4. `["Bandeja_paisa", "ingredient", "Chicharrón"]`
5. `["Bandeja_paisa", "ingredient", "Chorizo"]`

**Walkable ranked5 (5):**
1. `["Buckwheat", "~ingredient", "Buckwheat_gateau"]`
2. `["Buckwheat", "~ingredient", "Stip_(dish)"]`
3. `["Bandeja_paisa", "ingredient", "Arepa"]`
4. `["Bandeja_paisa", "ingredient", "Avocado"]`
5. `["Bandeja_paisa", "ingredient", "Black_pudding"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### The SEAT Inca is related to the Lancia Thema and also the Fiat Croma.

Gold label: 0; first5: 1; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Fiat_Croma": [
    [
      "~relatedMeanOfTransportation"
    ]
  ],
  "Lancia_Thema": [
    [
      "~related"
    ]
  ],
  "SEAT_Inca": [
    [
      "relatedMeanOfTransportation"
    ],
    [
      "related"
    ]
  ]
}
```

**Connected chung (6):**
1. `["Fiat_Croma", "~related", "Lancia_Thema"]`
2. `["Fiat_Croma", "related", "Lancia_Thema"]`
3. `["Fiat_Croma", "~relatedMeanOfTransportation", "Lancia_Thema"]`
4. `["Lancia_Thema", "~related", "Fiat_Croma"]`
5. `["Lancia_Thema", "relatedMeanOfTransportation", "Fiat_Croma"]`
6. `["Lancia_Thema", "related", "Fiat_Croma"]`

**Walkable first5 (5):**
1. `["Fiat_Croma", "~related", "Alfa_Romeo_164"]`
2. `["Fiat_Croma", "~related", "Cadillac_BLS"]`
3. `["Fiat_Croma", "~related", "Chevrolet_Malibu"]`
4. `["Fiat_Croma", "~related", "Opel_Signum"]`
5. `["Fiat_Croma", "~related", "Pontiac_G6"]`

**Walkable ranked5 (5):**
1. `["Fiat_Croma", "~related", "Alfa_Romeo_164"]`
2. `["Fiat_Croma", "~related", "Cadillac_BLS"]`
3. `["Fiat_Croma", "~related", "Chevrolet_Malibu"]`
4. `["Fiat_Croma", "~related", "Opel_Signum"]`
5. `["Fiat_Croma", "~related", "Pontiac_G6"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### The Lancia Thema is a realted transport to the Alfa Romeo 164 which in turn, is a similar means of transport to the Alfa Romeo 33 Stradale.

Gold label: 0; first5: 1; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Alfa_Romeo_164": [
    [
      "relatedMeanOfTransportation"
    ],
    [
      "related"
    ]
  ],
  "Lancia_Thema": [
    [
      "~related"
    ]
  ],
  "Alfa_Romeo_33_Stradale": [
    [
      "~relatedMeanOfTransportation"
    ]
  ]
}
```

**Connected chung (6):**
1. `["Alfa_Romeo_164", "related", "Lancia_Thema"]`
2. `["Alfa_Romeo_164", "~related", "Lancia_Thema"]`
3. `["Alfa_Romeo_164", "relatedMeanOfTransportation", "Lancia_Thema"]`
4. `["Lancia_Thema", "related", "Alfa_Romeo_164"]`
5. `["Lancia_Thema", "~related", "Alfa_Romeo_164"]`
6. `["Lancia_Thema", "relatedMeanOfTransportation", "Alfa_Romeo_164"]`

**Walkable first5 (5):**
1. `["Alfa_Romeo_164", "related", "Fiat_Croma"]`
2. `["Alfa_Romeo_164", "related", "Saab_9000"]`
3. `["Alfa_Romeo_164", "~related", "Alfa_Romeo_Proteo"]`
4. `["Alfa_Romeo_164", "~related", "Fiat_Croma"]`
5. `["Alfa_Romeo_164", "~related", "Saab_9000"]`

**Walkable ranked5 (5):**
1. `["Alfa_Romeo_164", "~related", "Alfa_Romeo_Proteo"]`
2. `["Alfa_Romeo_164", "successor", "Alfa_Romeo_166"]`
3. `["Alfa_Romeo_33_Stradale", "related", "Alfa_Romeo_Tipo_33"]`
4. `["Alfa_Romeo_33_Stradale", "~related", "Alfa_Romeo_Carabo"]`
5. `["Alfa_Romeo_33_Stradale", "relatedMeanOfTransportation", "Alfa_Romeo_Tipo_33"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### William M O Dawson is actually the successor of Albert B White.

Gold label: 0; first5: 1; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Albert_B._White": [
    [
      "successor"
    ]
  ],
  "William_M._O._Dawson": [
    [
      "placeOfBirth"
    ],
    [
      "~successor"
    ]
  ],
  "\"tonga\"": [
    [
      "~placeOfBirth"
    ]
  ]
}
```

**Connected chung (2):**
1. `["Albert_B._White", "successor", "William_M._O._Dawson"]`
2. `["William_M._O._Dawson", "~successor", "Albert_B._White"]`

**Walkable first5 (5):**
1. `["Albert_B._White", "~successor", "George_W._Atkinson"]`
2. `["Albert_B._White", "office", "\"Governor of West Virginia\""]`
3. `["Albert_B._White", "profession", "Politician"]`
4. `["William_M._O._Dawson", "successor", "William_E._Glasscock"]`
5. `["William_M._O._Dawson", "office", "\"Governor of West Virginia\""]`

**Walkable ranked5 (5):**
1. `["William_M._O._Dawson", "successor", "William_E._Glasscock"]`
2. `["Albert_B._White", "~successor", "George_W._Atkinson"]`
3. `["Albert_B._White", "office", "\"Governor of West Virginia\""]`
4. `["Albert_B._White", "profession", "Politician"]`
5. `["William_M._O._Dawson", "office", "\"Governor of West Virginia\""]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Liselotte Grschebina died in Petah Tikva in Botswana.

Gold label: 0; first5: 1; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Liselotte_Grschebina": [
    [
      "deathPlace"
    ]
  ],
  "Petah_Tikva": [
    [
      "country"
    ],
    [
      "~deathPlace"
    ]
  ],
  "\"Botswana\"": [
    [
      "~country"
    ]
  ]
}
```

**Connected chung (1):**
1. `["Liselotte_Grschebina", "deathPlace", "Petah_Tikva"]`

**Walkable first5 (5):**
1. `["Liselotte_Grschebina", "deathPlace", "Israel"]`
2. `["Liselotte_Grschebina", "birthPlace", "German_Empire"]`
3. `["Liselotte_Grschebina", "birthPlace", "Germany"]`
4. `["Liselotte_Grschebina", "birthPlace", "Karlsruhe"]`
5. `["Petah_Tikva", "~birthPlace", "Amnon_Carmeli"]`

**Walkable ranked5 (5):**
1. `["Liselotte_Grschebina", "deathPlace", "Israel"]`
2. `["Liselotte_Grschebina", "birthPlace", "German_Empire"]`
3. `["Liselotte_Grschebina", "birthPlace", "Germany"]`
4. `["Liselotte_Grschebina", "birthPlace", "Karlsruhe"]`
5. `["Petah_Tikva", "~birthPlace", "Amnon_Carmeli"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Dennis William Sciama is the doctoral advisor of John R. Ross who discovered the Carter constant.

Gold label: 0; first5: 1; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Carter_constant": [
    [
      "~knownFor"
    ]
  ],
  "Dennis_William_Sciama": [
    [
      "~doctoralAdvisor"
    ]
  ],
  "John_R._Ross": [
    [
      "knownFor"
    ],
    [
      "doctoralAdvisor"
    ]
  ]
}
```

**Connected chung (0):**
- Không có path trong đầu vào V4.

**Walkable first5 (3):**
1. `["Dennis_William_Sciama", "~doctoralAdvisor", "Brandon_Carter"]`
2. `["John_R._Ross", "~doctoralAdvisor", "Richard_Kayne"]`
3. `["John_R._Ross", "doctoralAdvisor", "Noam_Chomsky"]`

**Walkable ranked5 (3):**
1. `["Dennis_William_Sciama", "~doctoralAdvisor", "Brandon_Carter"]`
2. `["John_R._Ross", "~doctoralAdvisor", "Richard_Kayne"]`
3. `["John_R._Ross", "doctoralAdvisor", "Noam_Chomsky"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Liselotte Grschebina was born on 1908-05-02 and died in Bridgeport, Connecticut, USA.

Gold label: 0; first5: 1; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Liselotte_Grschebina": [
    [
      "birthDate"
    ],
    [
      "deathPlace"
    ]
  ],
  "\"1908-05-02\"": [
    [
      "~birthDate"
    ]
  ],
  "\"Bridgeport, Connecticut, USA\"": [
    [
      "~deathPlace"
    ]
  ]
}
```

**Connected chung (2):**
1. `["\"1908-05-02\"", "~birthDate", "Liselotte_Grschebina"]`
2. `["Liselotte_Grschebina", "birthDate", "\"1908-05-02\""]`

**Walkable first5 (5):**
1. `["\"1908-05-02\"", "~birthDate", "Alister_Watson"]`
2. `["\"1908-05-02\"", "~birthDate", "Allan_Liddell"]`
3. `["\"1908-05-02\"", "~birthDate", "Bill_Harvey_(footballer,_born_1908)"]`
4. `["\"1908-05-02\"", "~birthDate", "Ellis_Hagler"]`
5. `["\"1908-05-02\"", "~birthDate", "Frank_Rowlett"]`

**Walkable ranked5 (5):**
1. `["\"1908-05-02\"", "~birthDate", "Bill_Harvey_(footballer,_born_1908)"]`
2. `["\"1908-05-02\"", "~birthDate", "Alister_Watson"]`
3. `["\"1908-05-02\"", "~birthDate", "Allan_Liddell"]`
4. `["\"1908-05-02\"", "~birthDate", "Ellis_Hagler"]`
5. `["\"1908-05-02\"", "~birthDate", "Frank_Rowlett"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Liselotte Grschebina, an Rotterdami was born in Karlsruhe?

Gold label: 0; first5: 1; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Liselotte_Grschebina": [
    [
      "birthPlace"
    ],
    [
      "nationality"
    ]
  ],
  "Karlsruhe": [
    [
      "~birthPlace"
    ]
  ],
  "Rotterdam": [
    [
      "~nationality"
    ]
  ]
}
```

**Connected chung (2):**
1. `["Karlsruhe", "~birthPlace", "Liselotte_Grschebina"]`
2. `["Liselotte_Grschebina", "birthPlace", "Karlsruhe"]`

**Walkable first5 (5):**
1. `["Karlsruhe", "~birthPlace", "Adolf_Holtzmann"]`
2. `["Karlsruhe", "~birthPlace", "Adolf_Marschall_von_Bieberstein"]`
3. `["Karlsruhe", "~birthPlace", "Adolf_des_Coudres"]`
4. `["Karlsruhe", "~birthPlace", "Adolph_Alexander_Weinman"]`
5. `["Karlsruhe", "~birthPlace", "Adolph_Hausrath"]`

**Walkable ranked5 (5):**
1. `["Karlsruhe", "~birthPlace", "Adolf_Holtzmann"]`
2. `["Karlsruhe", "~birthPlace", "Adolf_Marschall_von_Bieberstein"]`
3. `["Karlsruhe", "~birthPlace", "Adolf_des_Coudres"]`
4. `["Karlsruhe", "~birthPlace", "Adolph_Alexander_Weinman"]`
5. `["Karlsruhe", "~birthPlace", "Adolph_Hausrath"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Geoffrey Jackson graduated from the University of Cambridge which is considered a research University.

Gold label: 0; first5: 1; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "University_of_Cambridge": [
    [
      "type"
    ],
    [
      "~almaMater"
    ]
  ],
  "Research_university": [
    [
      "~type"
    ]
  ],
  "Geoffrey_Jackson": [
    [
      "almaMater"
    ]
  ]
}
```

**Connected chung (0):**
- Không có path trong đầu vào V4.

**Walkable first5 (5):**
1. `["Geoffrey_Jackson", "almaMater", "\"Emmanuel College, Cambridge\""]`
2. `["Geoffrey_Jackson", "almaMater", "Bolton_School"]`
3. `["Geoffrey_Jackson", "almaMater", "Emmanuel_College,_Cambridge"]`
4. `["University_of_Cambridge", "affiliation", "European_University_Association"]`
5. `["University_of_Cambridge", "affiliation", "G5_(universities)"]`

**Walkable ranked5 (5):**
1. `["Geoffrey_Jackson", "almaMater", "\"Emmanuel College, Cambridge\""]`
2. `["Geoffrey_Jackson", "almaMater", "Emmanuel_College,_Cambridge"]`
3. `["University_of_Cambridge", "affiliation", "European_University_Association"]`
4. `["University_of_Cambridge", "affiliation", "International_Alliance_of_Research_Universities"]`
5. `["University_of_Cambridge", "affiliation", "League_of_European_Research_Universities"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Ciudad Ayala is in the Pacific Standard time zone and in its version, UTC+04:30.

Gold label: 0; first5: 1; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Ciudad_Ayala": [
    [
      "timeZone"
    ],
    [
      "timeZone"
    ]
  ],
  "Pacific_Standard_Time_Zone": [
    [
      "~timeZone"
    ]
  ],
  "UTC+04:30": [
    [
      "~timeZone"
    ]
  ]
}
```

**Connected chung (2):**
1. `["Ciudad_Ayala", "timeZone", "Pacific_Standard_Time_Zone"]`
2. `["Pacific_Standard_Time_Zone", "~timeZone", "Ciudad_Ayala"]`

**Walkable first5 (5):**
1. `["Ciudad_Ayala", "utcOffset", "\"−6\""]`
2. `["Ciudad_Ayala", "timeZone", "Pacific_Daylight_Time"]`
3. `["Ciudad_Ayala", "timeZone", "Pacific_Time_Zone"]`
4. `["UTC+04:30", "~timeZone", "Andar,_Ghazni"]`
5. `["UTC+04:30", "~timeZone", "Aqcha"]`

**Walkable ranked5 (5):**
1. `["Ciudad_Ayala", "timeZone", "Pacific_Time_Zone"]`
2. `["Ciudad_Ayala", "timeZone", "Pacific_Daylight_Time"]`
3. `["UTC+04:30", "~timeZone", "Andar,_Ghazni"]`
4. `["UTC+04:30", "~timeZone", "Aqcha"]`
5. `["UTC+04:30", "~timeZone", "Badakhshan_Province"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### FK Babi currently has 5300 members and played in 2014.

Gold label: 0; first5: 1; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "\"2014\"": [
    [
      "~season"
    ]
  ],
  "\"5300\"": [
    [
      "~capacity"
    ]
  ],
  "FK_Babi": [
    [
      "season"
    ],
    [
      "capacity"
    ]
  ]
}
```

**Connected chung (2):**
1. `["\"2014\"", "~season", "FK_Babi"]`
2. `["FK_Babi", "season", "\"2014\""]`

**Walkable first5 (5):**
1. `["\"2014\"", "~capacity", "Audi_R18"]`
2. `["\"2014\"", "~season", "1._CfR_Pforzheim"]`
3. `["\"2014\"", "~season", "1._FCA_Darmstadt"]`
4. `["\"2014\"", "~season", "1._FC_Bad_Kötzting"]`
5. `["\"2014\"", "~season", "1._FC_Bocholt"]`

**Walkable ranked5 (5):**
1. `["\"2014\"", "~capacity", "Audi_R18"]`
2. `["\"2014\"", "~season", "1._CfR_Pforzheim"]`
3. `["\"2014\"", "~season", "1._FCA_Darmstadt"]`
4. `["\"2014\"", "~season", "1._FC_Bad_Kötzting"]`
5. `["\"2014\"", "~season", "1._FC_Bocholt"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### The Accademia di Architettura di Mendrisio was established in Malaysia in 1996 and has 100 academic staff.

Gold label: 0; first5: 1; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Accademia_di_Architettura_di_Mendrisio": [
    [
      "country"
    ],
    [
      "established"
    ],
    [
      "faculty"
    ]
  ],
  "\"1996\"": [
    [
      "~established"
    ]
  ],
  "\"100\"": [
    [
      "~faculty"
    ]
  ],
  "\"Malaysia\"": [
    [
      "~country"
    ]
  ]
}
```

**Connected chung (1):**
1. `["Accademia_di_Architettura_di_Mendrisio", "established", "\"1996\""]`

**Walkable first5 (5):**
1. `["\"100\"", "~staff", "Abbeyfield_School,_Chippenham"]`
2. `["\"100\"", "~staff", "Accademia_italiana"]`
3. `["\"100\"", "~staff", "Addey_and_Stanhope_School"]`
4. `["\"100\"", "~staff", "Al_Dhafra_Private_School"]`
5. `["\"100\"", "~staff", "Altwood_Church_of_England_School"]`

**Walkable ranked5 (5):**
1. `["\"100\"", "~staff", "Accademia_italiana"]`
2. `["\"100\"", "~staff", "Abbeyfield_School,_Chippenham"]`
3. `["\"100\"", "~staff", "Addey_and_Stanhope_School"]`
4. `["\"100\"", "~staff", "Al_Dhafra_Private_School"]`
5. `["\"100\"", "~staff", "Altwood_Church_of_England_School"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### It covers the academic discipline of analytic philosophy. The LCCN number is 83646315.

Gold label: 0; first5: 1; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Acta_Mathematica_Hungarica": [
    [
      "lccn"
    ],
    [
      "abbreviation"
    ],
    [
      "discipline"
    ]
  ],
  "\"83646315\"": [
    [
      "~lccn"
    ]
  ],
  "\"Acta Math. Hungar.\"": [
    [
      "~abbreviation"
    ]
  ],
  "Analytic_philosophy": [
    [
      "~discipline"
    ]
  ]
}
```

**Connected chung (2):**
1. `["Acta_Mathematica_Hungarica", "abbreviation", "\"Acta Math. Hungar.\""]`
2. `["Acta_Mathematica_Hungarica", "lccn", "\"83646315\""]`

**Walkable first5 (5):**
1. `["Acta_Mathematica_Hungarica", "discipline", "Mathematics"]`
2. `["Acta_Mathematica_Hungarica", "publisher", "Springer_Science+Business_Media"]`
3. `["Acta_Mathematica_Hungarica", "issn", "\"0236-5294\""]`
4. `["Acta_Mathematica_Hungarica", "issn", "\"1588-2632\""]`
5. `["Acta_Mathematica_Hungarica", "issn", "\"236\""]`

**Walkable ranked5 (5):**
1. `["Acta_Mathematica_Hungarica", "discipline", "Mathematics"]`
2. `["Acta_Mathematica_Hungarica", "publisher", "Springer_Science+Business_Media"]`
3. `["Acta_Mathematica_Hungarica", "issn", "\"0236-5294\""]`
4. `["Acta_Mathematica_Hungarica", "issn", "\"1588-2632\""]`
5. `["Acta_Mathematica_Hungarica", "issn", "\"236\""]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Bandeja paisa is made in the Antioquia Department of Colombia.

Gold label: 0; first5: 1; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Antioquia_Department": [
    [
      "country"
    ],
    [
      "~region"
    ]
  ],
  "Bandeja_paisa": [
    [
      "ingredient"
    ],
    [
      "region"
    ]
  ],
  "Colombia": [
    [
      "~country"
    ]
  ],
  "Brown_sugar": [
    [
      "~ingredient"
    ]
  ]
}
```

**Connected chung (2):**
1. `["Antioquia_Department", "country", "Colombia"]`
2. `["Antioquia_Department", "~region", "Bandeja_paisa"]`

**Walkable first5 (5):**
1. `["Antioquia_Department", "~region", "Fabio_Valencia_Cossio"]`
2. `["Antioquia_Department", "~region", "Gerardo_Molina"]`
3. `["Antioquia_Department", "~region", "Luis_Alfredo_Ramos"]`
4. `["Antioquia_Department", "~region", "Mario_Uribe_Escobar"]`
5. `["Antioquia_Department", "~region", "Piedad_Córdoba"]`

**Walkable ranked5 (5):**
1. `["Antioquia_Department", "~region", "Fabio_Valencia_Cossio"]`
2. `["Antioquia_Department", "~region", "Gerardo_Molina"]`
3. `["Antioquia_Department", "~region", "Luis_Alfredo_Ramos"]`
4. `["Antioquia_Department", "~region", "Mario_Uribe_Escobar"]`
5. `["Antioquia_Department", "~region", "Piedad_Córdoba"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### William M O Dawson whose birthplace was Bloomington Maryland was the successor to Albert B White who died in Western Front, France.

Gold label: 0; first5: 1; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Albert_B._White": [
    [
      "placeOfDeath"
    ],
    [
      "successor"
    ]
  ],
  "William_M._O._Dawson": [
    [
      "placeOfBirth"
    ],
    [
      "~successor"
    ]
  ],
  "Bloomington,_Maryland": [
    [
      "~placeOfBirth"
    ]
  ],
  "\"Western Front, France\"": [
    [
      "~placeOfDeath"
    ]
  ]
}
```

**Connected chung (2):**
1. `["Albert_B._White", "successor", "William_M._O._Dawson"]`
2. `["William_M._O._Dawson", "birthPlace", "Bloomington,_Maryland"]`

**Walkable first5 (5):**
1. `["\"Western Front, France\"", "~deathPlace", "Leigh_Richmond_Roose"]`
2. `["Albert_B._White", "birthPlace", "Cleveland"]`
3. `["Albert_B._White", "office", "\"Governor of West Virginia\""]`
4. `["William_M._O._Dawson", "successor", "William_E._Glasscock"]`
5. `["William_M._O._Dawson", "office", "\"Governor of West Virginia\""]`

**Walkable ranked5 (5):**
1. `["William_M._O._Dawson", "successor", "William_E._Glasscock"]`
2. `["\"Western Front, France\"", "~deathPlace", "Leigh_Richmond_Roose"]`
3. `["Albert_B._White", "birthPlace", "Cleveland"]`
4. `["Albert_B._White", "office", "\"Governor of West Virginia\""]`
5. `["William_M._O._Dawson", "office", "\"Governor of West Virginia\""]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Ciudad Ayala is a part of Morelos where Francisco Nascimento de Brito is a leading official, but the leader of Ciudad Ayala is Juan Nolasco.

Gold label: 0; first5: 1; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Ciudad_Ayala": [
    [
      "isPartOf"
    ],
    [
      "leaderName"
    ]
  ],
  "Morelos": [
    [
      "leaderName"
    ],
    [
      "~isPartOf"
    ]
  ],
  "Juan_Nolasco": [
    [
      "~leaderName"
    ]
  ],
  "\"Francisco Nascimento de Brito\"": [
    [
      "~leaderName"
    ]
  ]
}
```

**Connected chung (1):**
1. `["Juan_Nolasco", "~leaderName", "Ciudad_Ayala"]`

**Walkable first5 (5):**
1. `["\"Francisco Nascimento de Brito\"", "~leaderName", "Embu_das_Artes"]`
2. `["Morelos", "~location", "2012–13_Irapuato_FC_season"]`
3. `["Morelos", "~location", "2012–13_Jaguares_de_Chiapas_season"]`
4. `["Morelos", "~location", "2012–13_San_Luis_F.C._season"]`
5. `["Morelos", "~location", "2014–15_Club_Tijuana_season"]`

**Walkable ranked5 (5):**
1. `["\"Francisco Nascimento de Brito\"", "~leaderName", "Embu_das_Artes"]`
2. `["Morelos", "~placeOfDeath", "Juan_García_Esquivel"]`
3. `["Morelos", "~location", "2012–13_Irapuato_FC_season"]`
4. `["Morelos", "~location", "2012–13_Jaguares_de_Chiapas_season"]`
5. `["Morelos", "~location", "2012–13_San_Luis_F.C._season"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

## FALSE: ranked5 cứu: 4 claim

### It's from the Lazio region and one of it's ingredients is pecorino.

Gold label: 0; first5: 1; ranked5: 0

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Lazio": [
    [
      "~region"
    ]
  ],
  "Pecorino_Romano": [
    [
      "~ingredient"
    ]
  ],
  "Ploatz": [
    [
      "region"
    ],
    [
      "ingredient"
    ]
  ]
}
```

**Connected chung (0):**
- Không có path trong đầu vào V4.

**Walkable first5 (5):**
1. `["Lazio", "country", "Italy"]`
2. `["Pecorino_Romano", "~ingredient", "Amatriciana_sauce"]`
3. `["Pecorino_Romano", "~ingredient", "Cacio_e_pepe"]`
4. `["Pecorino_Romano", "~ingredient", "New_Haven-style_pizza"]`
5. `["Pecorino_Romano", "country", "\"Italy\""]`

**Walkable ranked5 (5):**
1. `["Ploatz", "region", "Hesse"]`
2. `["Lazio", "country", "Italy"]`
3. `["Pecorino_Romano", "~ingredient", "Amatriciana_sauce"]`
4. `["Pecorino_Romano", "~ingredient", "Cacio_e_pepe"]`
5. `["Pecorino_Romano", "~ingredient", "New_Haven-style_pizza"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### It is an ingredient of Arrabbiata sauce which is a traditional dish from Rome.

Gold label: 0; first5: 1; ranked5: 0

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Arrabbiata_sauce": [
    [
      "ingredient"
    ],
    [
      "region"
    ]
  ],
  "\"Rome\"": [
    [
      "~region"
    ]
  ],
  "Honeydew_(melon)": [
    [
      "~ingredient"
    ]
  ]
}
```

**Connected chung (0):**
- Không có path trong đầu vào V4.

**Walkable first5 (5):**
1. `["Arrabbiata_sauce", "ingredient", "Chili_pepper"]`
2. `["Arrabbiata_sauce", "ingredient", "Garlic"]`
3. `["Arrabbiata_sauce", "ingredient", "Olive_oil"]`
4. `["Arrabbiata_sauce", "ingredient", "Tomato"]`
5. `["Arrabbiata_sauce", "country", "Italy"]`

**Walkable ranked5 (5):**
1. `["Arrabbiata_sauce", "ingredient", "Chili_pepper"]`
2. `["Arrabbiata_sauce", "ingredient", "Garlic"]`
3. `["Arrabbiata_sauce", "ingredient", "Olive_oil"]`
4. `["Arrabbiata_sauce", "ingredient", "Tomato"]`
5. `["Arrabbiata_sauce", "ingredientName", "\"Tomatoes,red chili,garlic,olive oil\""]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Barco oil is a Colombian dish in the Antioquia Department region.

Gold label: 0; first5: 1; ranked5: 0

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Colombian_cuisine": [
    [
      "~country"
    ]
  ],
  "Antioquia_Department": [
    [
      "~region"
    ]
  ],
  "Barco_oil_concession": [
    [
      "country"
    ],
    [
      "region"
    ]
  ]
}
```

**Connected chung (0):**
- Không có path trong đầu vào V4.

**Walkable first5 (5):**
1. `["Antioquia_Department", "country", "Colombia"]`
2. `["Antioquia_Department", "~region", "Bandeja_paisa"]`
3. `["Antioquia_Department", "~region", "Fabio_Valencia_Cossio"]`
4. `["Antioquia_Department", "~region", "Gerardo_Molina"]`
5. `["Antioquia_Department", "~region", "Luis_Alfredo_Ramos"]`

**Walkable ranked5 (5):**
1. `["Barco_oil_concession", "region", "Norte_de_Santander_Department"]`
2. `["Antioquia_Department", "~region", "Bandeja_paisa"]`
3. `["Antioquia_Department", "~region", "Fabio_Valencia_Cossio"]`
4. `["Antioquia_Department", "~region", "Gerardo_Molina"]`
5. `["Antioquia_Department", "~region", "Luis_Alfredo_Ramos"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### David O'Sullivan (civil servant) graduated from the University of Cambridge which is affiliated with the League of European Research Universities.

Gold label: 0; first5: 1; ranked5: 0

Gold Evidence (chỉ tham khảo offline):

```json
{
  "University_of_Cambridge": [
    [
      "affiliation"
    ],
    [
      "~almaMater"
    ]
  ],
  "League_of_European_Research_Universities": [
    [
      "~affiliation"
    ]
  ],
  "David_O'Sullivan_(civil_servant)": [
    [
      "almaMater"
    ]
  ]
}
```

**Connected chung (3):**
1. `["League_of_European_Research_Universities", "~affiliation", "University_of_Cambridge"]`
2. `["League_of_European_Research_Universities", "~affiliations", "University_of_Cambridge"]`
3. `["University_of_Cambridge", "affiliation", "League_of_European_Research_Universities"]`

**Walkable first5 (5):**
1. `["David_O'Sullivan_(civil_servant)", "almaMater", "Bruges"]`
2. `["David_O'Sullivan_(civil_servant)", "almaMater", "College_of_Europe"]`
3. `["David_O'Sullivan_(civil_servant)", "almaMater", "Trinity_College,_Dublin"]`
4. `["League_of_European_Research_Universities", "~affiliation", "Faculty_of_Theology_and_Religious_Studies,_Catholic_University_of_Leuven"]`
5. `["League_of_European_Research_Universities", "~affiliation", "Heidelberg_University"]`

**Walkable ranked5 (5):**
1. `["League_of_European_Research_Universities", "~affiliation", "Faculty_of_Theology_and_Religious_Studies,_Catholic_University_of_Leuven"]`
2. `["League_of_European_Research_Universities", "~affiliation", "Heidelberg_University"]`
3. `["League_of_European_Research_Universities", "~affiliation", "Ludwig_Maximilian_University_of_Munich"]`
4. `["League_of_European_Research_Universities", "~affiliation", "Lund_University"]`
5. `["League_of_European_Research_Universities", "~affiliation", "Pierre_and_Marie_Curie_University"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

## TRUE: ranked5 cứu: 6 claim

### Arrabbiata sauce is from the Rome region and has chili pepper in it.

Gold label: 1; first5: 0; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Arrabbiata_sauce": [
    [
      "ingredient"
    ],
    [
      "region"
    ]
  ],
  "Chili_pepper": [
    [
      "~ingredient"
    ]
  ],
  "\"Rome\"": [
    [
      "~region"
    ]
  ]
}
```

**Connected chung (3):**
1. `["\"Rome\"", "~region", "Arrabbiata_sauce"]`
2. `["Arrabbiata_sauce", "ingredient", "Chili_pepper"]`
3. `["Arrabbiata_sauce", "region", "\"Rome\""]`

**Walkable first5 (5):**
1. `["\"Rome\"", "~region", "Carciofi_alla_giudia"]`
2. `["\"Rome\"", "~region", "Maxim_(given_name)"]`
3. `["Arrabbiata_sauce", "ingredient", "Garlic"]`
4. `["Arrabbiata_sauce", "ingredient", "Olive_oil"]`
5. `["Arrabbiata_sauce", "ingredient", "Tomato"]`

**Walkable ranked5 (5):**
1. `["Arrabbiata_sauce", "region", "Rome"]`
2. `["\"Rome\"", "~region", "Carciofi_alla_giudia"]`
3. `["\"Rome\"", "~region", "Maxim_(given_name)"]`
4. `["Arrabbiata_sauce", "mainIngredient", "\"Tomatoes, red chili, garlic, olive oil\""]`
5. `["Arrabbiata_sauce", "ingredient", "Garlic"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Tomatoes from the order Solanales are used in Arrabbiata sauce!

Gold label: 1; first5: 0; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Arrabbiata_sauce": [
    [
      "ingredient"
    ]
  ],
  "Tomato": [
    [
      "order"
    ],
    [
      "~ingredient"
    ]
  ],
  "Solanales": [
    [
      "~order"
    ]
  ]
}
```

**Connected chung (3):**
1. `["Arrabbiata_sauce", "ingredient", "Tomato"]`
2. `["Solanales", "~order", "Tomato"]`
3. `["Tomato", "~ingredient", "Arrabbiata_sauce"]`

**Walkable first5 (5):**
1. `["Arrabbiata_sauce", "ingredient", "Chili_pepper"]`
2. `["Arrabbiata_sauce", "ingredient", "Garlic"]`
3. `["Arrabbiata_sauce", "ingredient", "Olive_oil"]`
4. `["Arrabbiata_sauce", "mainIngredient", "\"Tomatoes, red chili, garlic, olive oil\""]`
5. `["Solanales", "~order", "Acnistus"]`

**Walkable ranked5 (5):**
1. `["Solanales", "~order", "Acnistus"]`
2. `["Solanales", "~order", "Acnistus_arborescens"]`
3. `["Solanales", "~order", "Alona_(plant)"]`
4. `["Solanales", "~order", "Anisodus"]`
5. `["Solanales", "~order", "Anisodus_tanguticus"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Lemon is the main ingredient of Bandeja paisa and is part of Colombian cuisine.

Gold label: 1; first5: 0; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Bandeja_paisa": [
    [
      "ingredient"
    ],
    [
      "country"
    ]
  ],
  "Lemon": [
    [
      "~ingredient"
    ]
  ],
  "Colombian_cuisine": [
    [
      "~country"
    ]
  ]
}
```

**Connected chung (2):**
1. `["Bandeja_paisa", "ingredient", "Lemon"]`
2. `["Colombian_cuisine", "~country", "Bandeja_paisa"]`

**Walkable first5 (5):**
1. `["Bandeja_paisa", "ingredient", "Arepa"]`
2. `["Bandeja_paisa", "ingredient", "Avocado"]`
3. `["Bandeja_paisa", "ingredient", "Black_pudding"]`
4. `["Bandeja_paisa", "ingredient", "Chicharrón"]`
5. `["Bandeja_paisa", "ingredient", "Chorizo"]`

**Walkable ranked5 (5):**
1. `["Bandeja_paisa", "mainIngredient", "\"red beans, pork belly, white rice, ground meat, chicharon, fried egg, plantain , chorizo, arepa, hogao sauce, black pudding , avocado and lemon\""]`
2. `["Lemon", "~mainIngredient", "Ceviche"]`
3. `["Lemon", "~mainIngredient", "Lady_Grey_(tea)"]`
4. `["Lemon", "~mainIngredient", "Liverpool_Tart"]`
5. `["Lemon", "~mainIngredient", "Passatelli"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Bill Oddie, who starred in Bananaman, was born in Rochdale and has a daughter called Kate Hardie.

Gold label: 1; first5: 0; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Bananaman": [
    [
      "starring"
    ]
  ],
  "Bill_Oddie": [
    [
      "children"
    ],
    [
      "birthPlace"
    ],
    [
      "~starring"
    ]
  ],
  "Kate_Hardie": [
    [
      "~children"
    ]
  ],
  "Rochdale": [
    [
      "~birthPlace"
    ]
  ]
}
```

**Connected chung (4):**
1. `["Bananaman", "starring", "Bill_Oddie"]`
2. `["Bill_Oddie", "birthPlace", "Rochdale"]`
3. `["Bill_Oddie", "~starring", "Bananaman"]`
4. `["Rochdale", "~birthPlace", "Bill_Oddie"]`

**Walkable first5 (5):**
1. `["Bananaman", "starring", "Graeme_Garden"]`
2. `["Bananaman", "starring", "Jill_Shilling"]`
3. `["Bananaman", "starring", "Tim_Brooke-Taylor"]`
4. `["Bill_Oddie", "birthPlace", "\"Rochdale, Lancashire, England\""]`
5. `["Bill_Oddie", "birthPlace", "Lancashire"]`

**Walkable ranked5 (5):**
1. `["Bill_Oddie", "~starring", "Bill_Oddie_Goes_Wild"]`
2. `["Bill_Oddie", "occupation", "Bill_Oddie__1"]`
3. `["Bill_Oddie", "birthPlace", "\"Rochdale, Lancashire, England\""]`
4. `["Bill_Oddie", "~starring", "Bananaman__Bananaman__1"]`
5. `["Bananaman", "starring", "Graeme_Garden"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### It is a traditional dish that comes from the Antioquia Department of Colombia.

Gold label: 1; first5: 0; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "Bandeja_paisa": [
    [
      "country"
    ],
    [
      "ingredient"
    ],
    [
      "region"
    ]
  ],
  "Colombian_cuisine": [
    [
      "~country"
    ]
  ],
  "Kidney_bean": [
    [
      "~ingredient"
    ]
  ],
  "Antioquia_Department": [
    [
      "~region"
    ]
  ]
}
```

**Connected chung (3):**
1. `["Antioquia_Department", "~region", "Bandeja_paisa"]`
2. `["Bandeja_paisa", "country", "Colombian_cuisine"]`
3. `["Bandeja_paisa", "ingredient", "Kidney_bean"]`

**Walkable first5 (5):**
1. `["Antioquia_Department", "~region", "Fabio_Valencia_Cossio"]`
2. `["Antioquia_Department", "~region", "Gerardo_Molina"]`
3. `["Antioquia_Department", "~region", "Luis_Alfredo_Ramos"]`
4. `["Antioquia_Department", "~region", "Mario_Uribe_Escobar"]`
5. `["Antioquia_Department", "~region", "Piedad_Córdoba"]`

**Walkable ranked5 (5):**
1. `["Antioquia_Department", "country", "Colombia"]`
2. `["Antioquia_Department", "~region", "Fabio_Valencia_Cossio"]`
3. `["Antioquia_Department", "~region", "Gerardo_Molina"]`
4. `["Antioquia_Department", "~region", "Luis_Alfredo_Ramos"]`
5. `["Antioquia_Department", "~region", "Mario_Uribe_Escobar"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

### Harold French directed the film English Without Tears which was edited by Alan Jaggs and released on 07-28-1944.

Gold label: 1; first5: 0; ranked5: 1

Gold Evidence (chỉ tham khảo offline):

```json
{
  "English_Without_Tears": [
    [
      "releaseDate"
    ],
    [
      "director"
    ],
    [
      "editing"
    ]
  ],
  "\"1944-07-28\"": [
    [
      "~releaseDate"
    ]
  ],
  "Harold_French": [
    [
      "~director"
    ]
  ],
  "Alan_Jaggs": [
    [
      "~editing"
    ]
  ]
}
```

**Connected chung (3):**
1. `["Alan_Jaggs", "~editing", "English_Without_Tears"]`
2. `["English_Without_Tears", "director", "Harold_French"]`
3. `["Harold_French", "~director", "English_Without_Tears"]`

**Walkable first5 (5):**
1. `["English_Without_Tears", "musicComposer", "Nicholas_Brodszky"]`
2. `["Harold_French", "~director", "Adam_and_Evelyne"]`
3. `["Harold_French", "~director", "Dear_Octopus_(film)"]`
4. `["Harold_French", "~director", "Encore_(1951_film)"]`
5. `["Harold_French", "~director", "Forbidden_Cargo_(1954_film)"]`

**Walkable ranked5 (5):**
1. `["Harold_French", "~director", "Dear_Octopus_(film)"]`
2. `["Harold_French", "~director", "Encore_(1951_film)"]`
3. `["Harold_French", "~director", "Forbidden_Cargo_(1954_film)"]`
4. `["Harold_French", "~director", "Isn't_Life_Wonderful!_(1953_film)"]`
5. `["Harold_French", "~director", "Jeannie_(film)"]`

- Vế 1 của claim: _đánh dấu thủ công_
- Vế 2 của claim: _đánh dấu thủ công_
- Path hỗ trợ từng vế / sai đối tượng: _đánh dấu thủ công_
- Chưa rõ do thiếu candidate hay V4 gộp sai: _đánh dấu thủ công_

