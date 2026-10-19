# Pilot: kiểm tra từng vế Conjunction trên dev

Chú giải vế được viết thủ công sau khi xem dev và có thể chịu ảnh hưởng của gold dev. Lúc chạy, script chỉ đối chiếu path đã lưu với chú giải; Gold label/Evidence chỉ hiển thị để rà soát. Không thấy path trong candidate không chứng minh vế sai. Strict-AND bên dưới chỉ là phản thực nghiệm trên mẫu chọn trước, không phải điểm accuracy hay bộ suy luận dùng cho test.

R3 và V4 đều được quan sát qua tối đa 32 path đã lưu.

## 1. William M O Dawson is actually the successor of Albert B White.

Nhóm: `label_review`; nhãn dev=0; V4 first5/ranked5=1/1.

Path R3 đã lưu: connected=2, walkable=6. Số vế có path khớp chính xác: R3=1/1, first5=1/1, ranked5=1/1.

| Vế cần kiểm tra | R3 đã lưu | first5 | ranked5 |
| --- | --- | --- | --- |
| Albert B. White's successor is William M. O. Dawson | 1 | 1 | 1 |

Nếu dùng strict-AND để chặn dự đoán True: first5=1, ranked5=1 (**chỉ chẩn đoán; thiếu path ≠ False**).

Ghi chú thủ công: The literal claim has one successor clause, which is a connected path. Original Evidence additionally names a birthplace/Tonga condition absent from the text; verify dataset provenance before calling this a V4 error.

Evidence gốc để rà soát nhãn (không phải đầu vào V4):

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

## 2. Bandeja paisa is made in the Antioquia Department of Colombia.

Nhóm: `label_review`; nhãn dev=0; V4 first5/ranked5=1/1.

Path R3 đã lưu: connected=2, walkable=30. Số vế có path khớp chính xác: R3=2/2, first5=2/2, ranked5=2/2.

| Vế cần kiểm tra | R3 đã lưu | first5 | ranked5 |
| --- | --- | --- | --- |
| Bandeja paisa has region Antioquia Department | 1 | 1 | 1 |
| Antioquia Department is in Colombia | 1 | 1 | 1 |

Nếu dùng strict-AND để chặn dự đoán True: first5=1, ranked5=1 (**chỉ chẩn đoán; thiếu path ≠ False**).

Ghi chú thủ công: The region and country clauses appear in connected paths, while original Evidence additionally names an ingredient/Brown sugar condition absent from the text. Verify the original example and generation process.

Evidence gốc để rà soát nhãn (không phải đầu vào V4):

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

## 3. Acme Airport is located in Asherton, Texas in the United States.

Nhóm: `partial_false`; nhãn dev=0; V4 first5/ranked5=1/1.

Path R3 đã lưu: connected=2, walkable=30. Số vế có path khớp chính xác: R3=1/2, first5=1/2, ranked5=1/2.

| Vế cần kiểm tra | R3 đã lưu | first5 | ranked5 |
| --- | --- | --- | --- |
| Acme Airport is located in Asherton, Texas | 0 | 0 | 0 |
| Asherton, Texas is in the United States | 1 | 1 | 1 |

Nếu dùng strict-AND để chặn dự đoán True: first5=0, ranked5=0 (**chỉ chẩn đoán; thiếu path ≠ False**).

## 4. Yeah, Aurakles was created by Ian James Corlett and Len Wein!

Nhóm: `partial_false`; nhãn dev=0; V4 first5/ranked5=1/1.

Path R3 đã lưu: connected=3, walkable=29. Số vế có path khớp chính xác: R3=1/2, first5=1/2, ranked5=1/2.

| Vế cần kiểm tra | R3 đã lưu | first5 | ranked5 |
| --- | --- | --- | --- |
| Aurakles was created by Ian James Corlett | 0 | 0 | 0 |
| Aurakles was created by Len Wein | 1 | 1 | 1 |

Nếu dùng strict-AND để chặn dự đoán True: first5=0, ranked5=0 (**chỉ chẩn đoán; thiếu path ≠ False**).

## 5. Bandeja paisa (white wine) is part of Colombian cuisine.

Nhóm: `partial_false`; nhãn dev=0; V4 first5/ranked5=1/1.

Path R3 đã lưu: connected=1, walkable=21. Số vế có path khớp chính xác: R3=1/2, first5=1/2, ranked5=1/2.

| Vế cần kiểm tra | R3 đã lưu | first5 | ranked5 |
| --- | --- | --- | --- |
| Bandeja paisa contains white wine | 0 | 0 | 0 |
| Bandeja paisa belongs to Colombian cuisine | 1 | 1 | 1 |

Nếu dùng strict-AND để chặn dự đoán True: first5=0, ranked5=0 (**chỉ chẩn đoán; thiếu path ≠ False**).

## 6. Ciudad Ayala is in the Pacific Standard time zone and in its version, UTC+04:30.

Nhóm: `partial_false`; nhãn dev=0; V4 first5/ranked5=1/1.

Path R3 đã lưu: connected=2, walkable=30. Số vế có path khớp chính xác: R3=1/2, first5=1/2, ranked5=1/2.

| Vế cần kiểm tra | R3 đã lưu | first5 | ranked5 |
| --- | --- | --- | --- |
| Ciudad Ayala has Pacific Standard Time Zone | 1 | 1 | 1 |
| Ciudad Ayala has UTC+04:30 time zone | 0 | 0 | 0 |

Nếu dùng strict-AND để chặn dự đoán True: first5=0, ranked5=0 (**chỉ chẩn đoán; thiếu path ≠ False**).

## 7. It covers the academic discipline of analytic philosophy. The LCCN number is 83646315.

Nhóm: `partial_false`; nhãn dev=0; V4 first5/ranked5=1/1.

Path R3 đã lưu: connected=2, walkable=5. Số vế có path khớp chính xác: R3=1/2, first5=1/2, ranked5=1/2.

| Vế cần kiểm tra | R3 đã lưu | first5 | ranked5 |
| --- | --- | --- | --- |
| Acta Mathematica Hungarica has discipline Analytic philosophy | 0 | 0 | 0 |
| Acta Mathematica Hungarica has LCCN 83646315 | 1 | 1 | 1 |

Nếu dùng strict-AND để chặn dự đoán True: first5=0, ranked5=0 (**chỉ chẩn đoán; thiếu path ≠ False**).

## 8. Arrabbiata sauce is from the Rome region and has chili pepper in it.

Nhóm: `true_control`; nhãn dev=1; V4 first5/ranked5=0/1.

Path R3 đã lưu: connected=3, walkable=7. Số vế có path khớp chính xác: R3=2/2, first5=2/2, ranked5=2/2.

| Vế cần kiểm tra | R3 đã lưu | first5 | ranked5 |
| --- | --- | --- | --- |
| Arrabbiata sauce is from Rome | 1 | 1 | 1 |
| Arrabbiata sauce contains chili pepper | 1 | 1 | 1 |

Nếu dùng strict-AND để chặn dự đoán True: first5=0, ranked5=1 (**chỉ chẩn đoán; thiếu path ≠ False**).

## 9. Tomatoes from the order Solanales are used in Arrabbiata sauce!

Nhóm: `true_control`; nhãn dev=1; V4 first5/ranked5=0/1.

Path R3 đã lưu: connected=3, walkable=29. Số vế có path khớp chính xác: R3=2/2, first5=2/2, ranked5=2/2.

| Vế cần kiểm tra | R3 đã lưu | first5 | ranked5 |
| --- | --- | --- | --- |
| Tomato is of order Solanales | 1 | 1 | 1 |
| Arrabbiata sauce contains Tomato | 1 | 1 | 1 |

Nếu dùng strict-AND để chặn dự đoán True: first5=0, ranked5=1 (**chỉ chẩn đoán; thiếu path ≠ False**).

