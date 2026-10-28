# Hướng dẫn đọc và thuyết trình phần Analysis

Tài liệu này đi theo **15 slide của pha Analysis** trong [`slides/index.html`](../slides/index.html), từ tiêu đề “Analysis” đến “Class phân tích”. Đây là bản giải thích để hiểu ý và tập nói, không phải đặc tả triển khai. Các quy tắc được đối chiếu với các slide FR, BR, NFR ngay trước phần Analysis.

## 1. Nắm mạch trước khi học từng slide

Đề bài của shop nói **muốn khách tìm được sản phẩm**. Pha Requirements đã chốt *hệ thống phải làm gì* (FR), *theo luật nào* (BR), *tốt đến mức nào* (NFR). Pha Analysis biến các câu đó thành bốn góc nhìn:

| Công cụ | Câu hỏi cần trả lời | Đầu ra trong slide |
|---|---|---|
| Use case | Ai muốn đạt việc gì? | Sơ đồ tổng quan và sơ đồ Search Product |
| Scenario | Một lượt dùng diễn ra thế nào, khi lỗi thì sao? | UC-01 đến UC-06 |
| Activity diagram | Các bước đi theo thứ tự nào, ai làm, chỗ nào rẽ hoặc chạy song song? | Sơ đồ Search Product có hai swimlane |
| Class phân tích | Hệ thống cần nhớ những loại thông tin nào? | 5 lớp dữ liệu liên quan đến sản phẩm |

**Câu chốt để mở phần:** “Requirements nói hệ thống *phải làm gì*. Analysis mô tả *khách và hệ thống tương tác ra sao*, đồng thời chỉ ra dữ liệu nào cần được lưu. Ở pha này nhóm chưa chọn công nghệ cụ thể.”

Ví dụ xuyên suốt: khách tìm “áo sweater trơn, **không in hình**, màu trầm, đi làm”. Hệ thống phải hiểu “áo sweater” là loại hàng; “không in hình” là điều kiện loại trừ cứng; màu là điều kiện có thể nới nếu rỗng; “đi làm” chủ yếu giúp xếp hạng. Sau đó hiện kết quả cùng các chip để khách nhìn thấy hệ thống đã hiểu gì.

## 2. Đi theo từng slide

### Slide 1 — Mở pha Analysis

Slide này là mục lục. Hãy nói ngắn rằng nhóm sẽ đi từ **hành vi** (use case, scenario, activity) sang **dữ liệu** (class phân tích). Đừng giải thích chi tiết các sơ đồ ngay tại đây.

### Slide 2 — Analysis là gì?

- **Đầu vào:** FR, BR, context diagram và DFD từ Requirements.
- **Đầu ra:** use case, scenario, activity, class phân tích.
- **Độc lập công nghệ:** nói “AI Service hiểu câu” và “Embedding Service tạo vector”, chưa cần nêu tên mô hình, cơ sở dữ liệu hay framework.

**Cách nói:** “Một câu yêu cầu như ‘tìm bằng giọng nói’ còn quá ngắn để lập trình. Phân tích làm rõ ai khởi động, hệ thống xử lý gì, lỗi chép lời thì sao và dữ liệu nào cần có.”

### Slide 3 — Kỹ thuật và các bước

Nhớ chuỗi **tổng quan → tìm kiếm → kịch bản → luồng hoạt động → dữ liệu**. Sơ đồ tổng quan giữ bối cảnh cả shop; sơ đồ Search Product thu hẹp đúng trọng tâm. Kịch bản viết chi tiết các đường đi; activity gom các nhánh thành một quy trình; class phân tích mô tả thông tin cần nhớ để quy trình chạy được.

### Slide 4 — Ký hiệu use case

- **Actor:** vai trò ở ngoài ranh giới hệ thống, không nhất thiết là một cá nhân cụ thể.
- **Use case:** một mục tiêu có ý nghĩa với actor, ví dụ “Tìm sản phẩm”.
- **«include»:** việc con luôn cần trong use case gốc. Ở đây tìm sản phẩm luôn cần lọc và xếp hạng.
- **«extend»:** phần chỉ xảy ra theo điều kiện hoặc biến thể. Ở đây khách chọn chữ, giọng nói, ảnh, video; bỏ chip chỉ khi muốn sửa điều kiện.

Khi chỉ vào sơ đồ, đọc **mũi tên nét đứt**: `extend` từ use case mở rộng về use case gốc; `include` từ use case gốc đến việc được bao gồm.

### Slide 5 — Use case tổng quan

Mở [sơ đồ tổng quan](../slides/img/a0_uc_overview.png). Khung xanh là hệ thống ABC Online Shop. **Customer** và **Administrator** là hai actor ở ngoài khung. Customer có các mục tiêu tìm sản phẩm, hỏi trợ lý, tra đơn; Administrator quản lý sản phẩm. Từ kết quả tìm kiếm, khách *có thể* xem chi tiết, lấy gợi ý rồi đặt hàng. “Có thể” rất quan trọng: không phải lượt tìm nào cũng dẫn đến mua.

**Cách nói:** “Sơ đồ này đặt chức năng tìm kiếm vào hành trình mua hàng. Sau đây em phóng to riêng Search Product.”

### Slide 6 — Use case Search Product

Mở [sơ đồ tìm kiếm](../slides/img/a1_uc_search.png). Customer bắt đầu **Search Product**. Bốn biến thể đầu vào là **Text, Voice, Image, Video**. Phần **Filter & Rank Results** là bước chung bắt buộc. **Refine Conditions** là thao tác tùy chọn sau khi có kết quả và chip.

Đừng nhầm “bốn cách nhập” với “bốn hệ tìm kiếm tách biệt”. Điểm chung của cả pha là chúng đưa ra tín hiệu/điều kiện rồi dùng lại lõi lọc và xếp hạng.

### Slide 7 — Scenario và UC-01: tìm bằng chữ

Một scenario nên đọc theo **actor → tiền điều kiện → luồng chính → luồng thay thế → hậu điều kiện**. Ký hiệu `3a` là nhánh rẽ tại bước 3.

1. Khách gõ câu và bấm Tìm.
2. Hệ thống xem câu này đã được tìm trong 60 giây chưa; nếu có, trả kết quả đã lưu tạm.
3. AI Service tách câu thành điều kiện cần có, điều không muốn, giá và phần ý nghĩa.
4. Hệ thống lọc trước, rồi xếp hạng theo từ khóa và ý nghĩa.
5. Giao diện hiện kết quả, chip điều kiện và lý do khớp.

Nếu AI lỗi hoặc quá 3 giây, dùng cách dự phòng theo từ khóa (**BR-04**). Nếu lọc xong không có kết quả, nới điều kiện theo thứ tự đã định (**BR-02**), nhưng **không nới loại hàng**. Điều “không muốn” vẫn phải loại tuyệt đối (**BR-01**). “Rẻ hơn chút” là một lượt sửa điều kiện đã hiểu. Tìm kiếm chỉ đọc dữ liệu sản phẩm, không sửa bản ghi sản phẩm.

**Cách nói:** “Điểm khó không nằm ở gõ chữ, mà ở hiểu câu phủ định và xử lý khi không có kết quả hoặc AI chậm.”

### Slide 8 — UC-02: tìm bằng giọng nói

Khách cho phép micro, ghi âm và bấm Gửi. Hệ thống làm **song song** hai việc: tạo vector ý nghĩa trực tiếp từ âm thanh; chép lời để rút điều kiện rõ ràng, chẳng hạn “không in hình”. Hai tín hiệu này bổ sung nhau: vector giúp tìm gần về ý nghĩa, bản chép lời giúp giữ điều kiện cứng. Nếu chép lời lỗi, hệ thống vẫn tìm theo vector âm thanh, nhưng có thể thiếu điều kiện chỉ xuất hiện trong lời nói.

**Ví dụ nói:** “Tôi nói ‘áo trơn không in hình’. Nếu chỉ so độ giống của âm thanh, ta khó bảo đảm ý phủ định; bản chép lời giúp tách ‘không in hình’ thành điều kiện loại trừ.”

### Slide 9 — UC-03: tìm bằng ảnh

Với ảnh một bộ đồ, AI Service nhận diện **tối đa 5 món** và vị trí của chúng. Hệ thống cắt vùng từng món, tạo vector ảnh, rồi tìm **8 sản phẩm** gần nhất cho mỗi món. Vì thế kết quả được chia **mỗi món một hàng**, thay vì một danh sách trộn áo, quần và giày. Ghi chú của khách như “nhưng màu đen, tay ngắn” cũng được đưa vào điều kiện.

Nếu không nhận ra món hoặc AI lỗi, tìm cả ảnh như một món. Nếu khách gửi 2–5 ảnh, slide mô tả một biến thể “tìm theo gu chung” (moodboard). Đừng nói rằng mọi ảnh đều được tách đúng mọi món; đây là luồng mong muốn và có nhánh dự phòng.

### Slide 10 — UC-04: video và UC-05: sửa điều kiện

**Video:** cả clip được chuyển thành **một vector**, rồi tìm sản phẩm gần nhất; slide không mô tả tách từng món hay từng khung hình. File sai định dạng hoặc quá **25 MB** bị từ chối theo BR-06.

**Sửa điều kiện:** khi đã có chip, khách bấm ✕ trên chip “Màu đen”; hệ thống bỏ đúng điều kiện đó, lọc và xếp hạng lại. Không cần nhờ AI hiểu lại yêu cầu. Phân biệt thao tác này với việc **nói/gõ thêm một câu mới**, vốn có thể cần bước hiểu ngôn ngữ.

### Slide 11 — UC-06: tìm qua trợ lý

Khách nói “Mình cần áo sơ mi trắng, quần tây đen và giày da đi làm”. AI Service tách thành **ba món**, tối đa năm món; hệ thống gọi lại luồng **Search by Text** cho từng món, có thể tìm song song, rồi giữ **top 3** mỗi món. AI viết câu trả lời **dựa trên dữ liệu sản phẩm vừa lấy**, không tự đặt giá hoặc tồn kho. Hệ thống đọc 10 lượt hội thoại gần nhất trong cùng `session_id` và lưu hai tin nhắn của lượt mới.

Hai nhánh cần nhớ: hỏi trạng thái đơn → chỉ xét đơn gần nhất của cùng phiên; yêu cầu mơ hồ → hỏi thêm rồi mới tìm. `session_id` là mã phiên trình duyệt, không đồng nghĩa với tài khoản đăng nhập.

### Slide 12 — So sánh các cách tìm

| Đầu vào | Bước hiểu riêng | Điểm cần nhớ khi nói |
|---|---|---|
| Chữ | Tách điều kiện và tạo vector chữ | Kết hợp từ khóa với ý nghĩa |
| Giọng nói | Vector âm thanh song song với chép lời | Chép lời giúp giữ điều kiện phủ định |
| Ảnh | Nhận diện từng món, cắt vùng và tạo vector | Mỗi món một hàng kết quả |
| Video | Một vector cho cả clip | Không tách từng món trong clip ở scenario này |
| Chatbot | Tách danh sách món | Gọi lại tìm bằng chữ cho từng món |

Sau bước hiểu là **lọc → nới nếu rỗng → xếp hạng**. BR-07 ghi điểm cuối gồm **90% độ hợp + 10% tình trạng còn hàng**. Đây là quy tắc xếp hạng, không có nghĩa món hết hàng bị loại hoàn toàn. “Trộn xếp hạng” là gộp tín hiệu từ khóa và vector; Activity có ghi RRF, nhưng không cần giải công thức nếu bài nói chỉ ở mức Analysis.

**Câu chuyển:** “Năm cửa vào khác nhau, nhưng chỉ cần một quy trình chọn và xếp kết quả. Activity diagram cho thấy chỗ chúng nhập lại.”

### Slide 13 — Ký hiệu activity diagram

Chấm đen là điểm bắt đầu; vòng tròn kép là kết thúc. Hộp bo góc là hành động. Hình thoi dùng để chọn một nhánh hoặc gộp các nhánh thay thế. Thanh đậm tách việc chạy song song; thanh đậm thứ hai chờ các việc ấy hoàn tất. **Swimlane** chia cột theo bên chịu trách nhiệm: Customer và System.

Điểm dễ nhầm: **hình thoi** gộp một trong nhiều đường đi; **thanh đậm** gộp các việc song song cần cùng hoàn thành.

### Slide 14 — Activity Search Product

Mở [activity diagram](../slides/img/b1_act_search.png) và lần theo mũi tên từ trên xuống:

1. Customer chọn một trong bốn đầu vào: chữ, giọng nói, ảnh hoặc video.
2. System xử lý riêng từng loại. Giọng nói có hai nhánh song song: vector âm thanh và chép lời/điều kiện.
3. Bốn đường nhập lại ở hình thoi, rồi qua lọc; nếu rỗng thì nới điều kiện theo BR-02.
4. System gộp tín hiệu xếp hạng và tính điểm; Customer nhìn kết quả và chip.
5. Nếu khách bỏ/sửa chip, luồng quay về **lọc**, không quay về bước hiểu đầu vào. Nếu xong, quy trình kết thúc.

**Cách nói:** “Sơ đồ này chứng minh một lõi xử lý chung sau phần hiểu riêng, và cho thấy thao tác sửa chip tiết kiệm một lần gọi AI.”

### Slide 15 — Class phân tích

Mở [class diagram](../slides/img/d1_class_analysis.png). Đây là **mô hình khái niệm dữ liệu**, có thuộc tính nhưng chưa chốt kiểu dữ liệu, phương thức hay bảng SQL.

| Lớp | Hệ thống cần nhớ gì? | Quan hệ cần đọc |
|---|---|---|
| `Category` | Danh mục như áo, quần | Một danh mục có thể có `0..*` sản phẩm; mỗi sản phẩm thuộc `1` danh mục |
| `Product` | Tên, mô tả, giá, chất liệu, họa tiết, phong cách... | Lớp trung tâm |
| `ProductVariant` | Size, màu, SKU, tồn kho | Mỗi sản phẩm có `1..*` biến thể; tồn kho nằm ở biến thể |
| `ProductImage` | Ảnh và khóa lưu trữ | Mỗi sản phẩm có `0..*` ảnh trong sơ đồ |
| `ProductVector` | Vector, loại đầu vào, phiên bản mô hình | Mỗi sản phẩm có `0..2` vector trong sơ đồ |

**Thoi đặc** ở phía Product thể hiện quan hệ thành phần với biến thể, ảnh và vector: các phần này phụ thuộc vào sản phẩm. **Thoi rỗng** được dùng để biểu đạt quan hệ lỏng hơn với Category. Khi bị hỏi, hãy nhấn mạnh ý nghiệp vụ: *xóa một sản phẩm không làm mất danh mục; biến thể, ảnh và vector của sản phẩm phụ thuộc vào sản phẩm đó*. Xem thêm lưu ý về vị trí thoi rỗng ở cuối tài liệu.

**Câu kết phần:** “Analysis đã chỉ ra hành trình dùng, các nhánh ngoại lệ, bước xử lý chung và dữ liệu cần có. Từ đó pha Design mới quyết định kiến trúc và công nghệ cụ thể.”

## 3. Những câu dễ bị hỏi

**Tại sao ‘không in hình’ không được nới?** Vì đó là ý khách *không muốn* (BR-01). Nếu nới nó, kết quả trái yêu cầu dù có nhiều sản phẩm hơn.

**Tại sao phong cách ‘đi làm’ không lọc cứng?** BR-03 dùng phong cách và dịp mặc để xếp trước/sau. Lọc cứng có thể bỏ sót món phù hợp chưa được gắn nhãn “đi làm”.

**Vì sao cần cả từ khóa lẫn vector?** Từ khóa giữ những từ/thuộc tính rõ ràng; vector giúp tìm món diễn đạt khác nhưng gần nghĩa. Điều kiện cứng vẫn cần được lọc trước khi xếp hạng.

**Tại sao ảnh và video xử lý khác nhau?** Scenario ảnh yêu cầu tách từng món trong một bộ đồ. Scenario video hiện tại chỉ dùng một biểu diễn cho cả clip, nên kết quả là các sản phẩm gần với clip nói chung.

**Class phân tích khác class thiết kế thế nào?** Class phân tích trả lời *cần nhớ loại thông tin nào và quan hệ ra sao*; class thiết kế bổ sung kiểu dữ liệu, phương thức, giao diện và chi tiết triển khai.

## 4. Lưu ý khi đối chiếu slide và sơ đồ

- Slide UC-05 ghi tiền điều kiện đã có chip từ **UC-01, UC-02, UC-04**; câu ở Activity lại nói kết quả có chip sau cả bốn nhánh. Với ảnh, scenario có điều kiện từ ghi chú nhưng không nói rõ chip có hiện hay không. Khi thuyết trình, chỉ khẳng định **bỏ chip khi chip đang hiển thị**.
- [Class diagram](../slides/img/d1_class_analysis.png) đặt **thoi rỗng sát Product** trên đường nối Category–Product, trong khi lời giải thích slide nói “sản phẩm thuộc danh mục” và xóa Product thì Category vẫn còn. Nếu bị hỏi về ký pháp UML, hãy nêu ý nghiệp vụ trước; vị trí thoi rỗng trong hình có thể cần sửa để phù hợp với cách nói Category chứa Products.
- README ở gốc repo mô tả một phạm vi/phiên bản khác ở vài điểm, chẳng hạn phần giọng nói và video. Tài liệu này bám theo **deck hiện tại** trong `slides/index.html` và BR ngay trong deck; hãy dùng cùng một phiên bản khi trình bày.

## 5. Cách luyện nhanh

Đọc một lượt chỉ theo **câu in đậm/câu chuyển**; lượt hai mở bốn sơ đồ và tự lần theo mũi tên; lượt ba tập kể ví dụ “áo sweater trơn, không in hình” từ UC-01 đến Activity và Class. Trong trình chiếu, nhấn **N** để mở ghi chú thuyết trình của slide; [`deck.css`](../slides/deck.css) ẩn các ghi chú này trên chính slide, còn [`deck.js`](../slides/deck.js) đưa chúng vào bảng ghi chú.
