# Kịch bản thuyết trình: phần Analysis

Tài liệu này đi đúng thứ tự **15 slide Analysis** trong [bộ slide](abc-online-shop-sysdes/slides/index.html), từ trang “Analysis” đến “Class phân tích”. Mỗi mục có **lời thoại** để bạn tập nói gần như nguyên văn, sau đó là **ý cần hiểu** để có thể diễn đạt bằng lời của mình. Các số UC, BR và giới hạn được lấy từ bộ slide hiện tại.

**Thời lượng gợi ý:** khoảng 10–13 phút cho cả phần. Các đoạn trong ngoặc vuông như `[chỉ vào sơ đồ]` là động tác, không đọc thành tiếng. Khi nói, giữ một ví dụ xuyên suốt: *“áo sweater trơn, không in hình, màu trầm, đi làm”*.

## Slide 1 — Analysis: mở đầu phần phân tích

**Lời thoại**

> “Ở phần Requirements, nhóm đã xác định hệ thống phải làm những gì: khách có thể tìm sản phẩm bằng nhiều cách, xem và sửa điều kiện tìm kiếm, còn hệ thống phải lọc và xếp hạng theo các quy tắc đã chốt. Sang phần Analysis, nhóm đi thêm một bước: mô tả khách thực sự sử dụng chức năng đó như thế nào, hệ thống xử lý từng tình huống ra sao và cần lưu những thông tin gì. Em sẽ đi từ use case tổng quan, đến kịch bản từng cách tìm, sơ đồ hoạt động, rồi kết thúc bằng class phân tích.”

**Ý cần hiểu:** Đây là slide chuyển pha. Requirements trả lời **làm gì**; Analysis làm rõ **hành vi và dữ liệu**. Không cần đọc hết mục lục trên màn hình.

## Slide 2 — Analysis là gì?

**Lời thoại**

> “Analysis là quá trình biến những câu yêu cầu thành mô hình đủ rõ để cả nhóm hiểu giống nhau. Đầu vào của pha này là yêu cầu chức năng, quy tắc nghiệp vụ, sơ đồ ngữ cảnh và DFD. Đầu ra là use case, kịch bản sử dụng, activity diagram và class phân tích. Ví dụ, yêu cầu ‘tìm bằng giọng nói’ mới chỉ nói *có chức năng*. Phân tích phải trả lời thêm: khách bấm gì, hệ thống làm gì với đoạn ghi âm, nếu không chép được lời thì xử lý thế nào. Ở đây nhóm mô tả nghiệp vụ ở mức khái niệm, chưa gắn nó với một công nghệ cụ thể.”

**Ý cần hiểu:** Có thể gọi chung **AI Service** và **Embedding Service**, vì slide dùng các tên đó. Tên mô hình, framework và cơ sở dữ liệu là nội dung của pha Design.

## Slide 3 — Kỹ thuật và các bước trong Analysis

**Lời thoại**

> “Nhóm dùng ba loại mô hình hành vi chính. Use case cho biết *ai* muốn đạt *mục tiêu gì*. Scenario viết thành từng bước và cả những nhánh khi có sự cố. Activity diagram cho thấy thứ tự xử lý, chỗ rẽ nhánh và ai chịu trách nhiệm. Quy trình của nhóm đi từ use case toàn hệ thống, thu hẹp vào riêng Search Product, viết scenario cho từng trường hợp, vẽ activity để nối các luồng lại, rồi rút ra class phân tích để xác định dữ liệu hệ thống cần nhớ.”

**Ý cần hiểu:** Nhớ chuỗi **toàn cảnh → trọng tâm tìm kiếm → từng tình huống → luồng chung → dữ liệu**. Class phân tích là bước thứ năm dù ba thẻ đầu slide chỉ giới thiệu ba kỹ thuật về hành vi.

## Slide 4 — Use case: các ký hiệu cần đọc

**Lời thoại**

> “Trước khi xem sơ đồ, em nhắc nhanh bốn ký hiệu. Actor là người hoặc hệ thống ở ngoài phạm vi hệ thống của mình. Use case là một mục tiêu hoàn chỉnh của actor, ví dụ khách muốn tìm sản phẩm. Quan hệ «include» chỉ phần luôn cần thực hiện; trong tìm kiếm, kết quả luôn phải được lọc và xếp hạng. Quan hệ «extend» chỉ phần phát sinh theo lựa chọn hoặc điều kiện, ví dụ khách chọn tìm bằng ảnh, hoặc sau khi tìm xong thì bỏ một chip điều kiện. Nhóm dùng «extend» để biểu diễn các cách tìm, thay vì vẽ kế thừa giữa các use case.”

**Ý cần hiểu:** `include` = **luôn có**; `extend` = **chỉ trong tình huống phù hợp**. Trên sơ đồ, mũi tên `extend` trỏ về use case gốc; mũi tên `include` trỏ tới phần được dùng chung.

## Slide 5 — Use case tổng quan

[Mở sơ đồ tổng quan](abc-online-shop-sysdes/slides/img/a0_uc_overview.png).

**Lời thoại**

> “[Chỉ vào hai hình người] Đây là hai actor trực tiếp: Customer và Administrator. Khung xanh là hệ thống ABC Online Shop. Khách có thể tìm sản phẩm, hỏi trợ lý hoặc theo dõi đơn hàng; quản trị viên quản lý sản phẩm. [Chỉ vào Search Product rồi View Product Detail] Trong hành trình mua sắm, tìm kiếm thường là cửa vào. Khi thấy một kết quả phù hợp, khách *có thể* mở chi tiết, xem gợi ý và đặt hàng. Các bước sau không bắt buộc ở mọi lần tìm. Sơ đồ này giúp đặt chức năng tìm kiếm vào bối cảnh toàn bộ shop; từ slide tiếp theo em sẽ phóng to riêng Search Product.”

**Ý cần hiểu:** Actor nằm **ngoài** ranh giới hệ thống. Use case nằm **trong** khung. Không nói rằng mọi lượt tìm đều phải kết thúc bằng đặt hàng.

## Slide 6 — Use case Search Product

[Mở sơ đồ Search Product](abc-online-shop-sysdes/slides/img/a1_uc_search.png).

**Lời thoại**

> “[Chỉ vào Search Product] Đây là mục tiêu chính của khách: tìm được sản phẩm phù hợp. Khách có bốn cách đưa yêu cầu vào: gõ chữ, nói, gửi ảnh hoặc gửi video. Vì mỗi lượt khách chỉ chọn cách phù hợp, sơ đồ biểu diễn chúng bằng «extend». Dù đầu vào là gì, hệ thống vẫn phải lọc và xếp hạng kết quả, nên Filter & Rank Results được nối bằng «include». Sau khi có kết quả, nếu thấy hệ thống hiểu sai một điều kiện, khách có thể bỏ chip và tìm lại; đó là Refine Conditions, cũng là một nhánh tùy chọn.”

**Ý cần hiểu:** Bốn cách tìm có **bước hiểu đầu vào khác nhau** nhưng hướng về **phần lọc và xếp hạng dùng chung**. “Bỏ chip” là hành động sau khi có điều kiện và kết quả.

## Slide 7 — Scenario là gì? UC-01: tìm bằng chữ

**Lời thoại**

> “Scenario là bản mô tả một lượt sử dụng từ đầu tới cuối: actor là ai, các bước chính, nhánh khi xảy ra lỗi và kết quả sau cùng. Với UC-01, khách gõ chẳng hạn ‘áo sweater trơn, không in hình, màu trầm, đi làm’. Trước tiên hệ thống xem câu này đã được tìm trong 60 giây gần đây chưa để trả nhanh kết quả cũ. Nếu chưa, AI Service tách câu thành loại hàng, điều kiện cần có, điều khách không muốn, khoảng giá và phần ý nghĩa. Hệ thống lọc theo các điều kiện ấy, rồi xếp hạng theo độ khớp từ khóa và ý nghĩa. Cuối cùng giao diện hiện sản phẩm, các chip điều kiện và lý do khớp.”
>
> “Scenario cũng phải nói rõ trường hợp không thuận lợi. Ký hiệu 3a nghĩa là rẽ ở bước 3: nếu AI lỗi hoặc chậm quá ba giây thì dùng cách dự phòng theo từ khóa. Ở bước 4, nếu lọc ra danh sách rỗng, hệ thống nới điều kiện theo thứ tự quy định nhưng không nới loại hàng. Điều khách nói ‘không muốn’, như ‘không in hình’, vẫn phải được giữ. Tìm kiếm không làm thay đổi dữ liệu sản phẩm.”

**Ý cần hiểu:** BR-01 = giữ điều loại trừ; BR-02 = nới có thứ tự khi rỗng; BR-04 = dự phòng khi AI lỗi; BR-07 = công thức xếp hạng. “Rẻ hơn chút” là yêu cầu sửa từ lượt trước, không phải một loại sản phẩm mới.

## Slide 8 — UC-02: tìm bằng giọng nói

**Lời thoại**

> “Ở UC-02, khách cho phép dùng micro, ghi âm rồi bấm Gửi. Hệ thống xử lý đoạn ghi âm theo hai nhánh cùng lúc. Nhánh thứ nhất tạo vector ý nghĩa trực tiếp từ âm thanh để tìm sản phẩm gần nghĩa. Nhánh thứ hai chép lời nói thành chữ, rồi rút ra các điều kiện rõ ràng như ‘không in hình’. Sau đó hệ thống đưa các tín hiệu này vào bước lọc và xếp hạng chung. Nếu chép lời thất bại, nhánh vector âm thanh vẫn cho phép tìm theo ý nghĩa, thay vì làm hỏng cả lượt tìm.”

**Ý cần hiểu:** Tìm giọng nói trong slide **không chỉ là đổi tiếng nói thành chữ**. Nó còn dùng vector âm thanh. Bản chép lời hữu ích để nhận diện điều kiện cứng, đặc biệt là câu phủ định.

## Slide 9 — UC-03: tìm bằng ảnh

**Lời thoại**

> “Với tìm bằng ảnh, khách có thể gửi ảnh một bộ đồ và ghi chú thêm, ví dụ ‘nhưng màu đen, tay ngắn’. AI Service nhìn ảnh, xác định tối đa năm món và vị trí của từng món. Hệ thống cắt vùng ảnh của từng món, tạo vector rồi tìm tám sản phẩm tương tự cho mỗi món. Vì xử lý theo từng món nên kết quả cũng hiển thị thành từng hàng: hàng áo, hàng quần, hàng giày, thay vì trộn tất cả vào một danh sách. Nếu AI không nhận ra món nào, hệ thống coi cả ảnh là một món để vẫn có kết quả. Slide còn có biến thể gửi từ hai đến năm ảnh để tìm theo gu chung.”

**Ý cần hiểu:** **5 món × 8 sản phẩm** là giới hạn trong slide, không phải lời hứa lúc nào cũng nhận diện đủ năm món. Hãy phân biệt “một ảnh chứa nhiều món” với “nhiều ảnh tạo một gu chung”.

## Slide 10 — UC-04: video và UC-05: sửa điều kiện

**Lời thoại**

> “Slide này đặt cạnh nhau hai tình huống ngắn. Với video, khách chọn một clip; Embedding Service biến *cả clip* thành một vector, rồi hệ thống tìm những sản phẩm gần nhất và xếp hạng. Ở phiên bản scenario này, video không được tách riêng từng món như ảnh. Nếu file sai định dạng hoặc vượt 25 MB thì hệ thống báo lỗi và không tìm.”
>
> “UC-05 là sửa điều kiện. Giả sử kết quả đang có chip ‘Màu đen’ nhưng khách không muốn giới hạn màu nữa. Khách bấm dấu ✕, hệ thống bỏ điều kiện ấy, lọc và xếp hạng lại. Nó không phải hỏi AI Service để hiểu lại toàn bộ câu. Đây là lý do chip vừa giúp khách kiểm tra hệ thống hiểu gì, vừa giúp sửa tìm kiếm nhanh.”

**Ý cần hiểu:** Bỏ chip khác với **nói hoặc gõ thêm** một ý mới; ý mới có thể cần được hiểu lại. BR-06 giới hạn video ở **25 MB**.

## Slide 11 — UC-06: tìm qua trợ lý chatbot

**Lời thoại**

> “Ngoài ô tìm kiếm, khách còn có thể hỏi trợ lý, ví dụ ‘Mình cần áo sơ mi trắng, quần tây đen và giày da đi làm’. Trợ lý không tự tạo ra một bộ máy tìm kiếm khác. AI Service tách tin nhắn thành ba món; hệ thống gọi lại Search by Text cho từng món, có thể chạy song song, rồi lấy ba sản phẩm đầu của mỗi món. Sau đó AI viết câu trả lời dựa trên dữ liệu sản phẩm vừa lấy, còn giao diện hiện các thẻ sản phẩm. Như vậy trợ lý không được tự bịa giá hay tồn kho.”
>
> “Kịch bản cũng xét các nhánh khác: nếu khách hỏi ‘đơn của tôi đâu’, hệ thống chỉ xét đơn gần nhất thuộc cùng phiên trình duyệt; nếu nhu cầu còn mơ hồ, trợ lý hỏi thêm trước khi tìm. Sau một lượt trao đổi, hệ thống lưu cả tin của khách và câu trả lời, tức hai tin nhắn.”

**Ý cần hiểu:** `session_id` là **mã phiên trình duyệt**, không phải tài khoản. Slide ghi đọc **10 lượt hội thoại gần nhất**, tách tối đa **5 món**, mỗi món giữ **top 3**.

## Slide 12 — So sánh các cách tìm

**Lời thoại**

> “Bảng này là kết luận của sáu scenario. Câu gõ được tách điều kiện và tạo vector chữ. Giọng nói tạo vector âm thanh đồng thời chép lời. Ảnh được nhận diện và cắt theo từng món. Video dùng một vector cho cả clip. Trợ lý tách danh sách món rồi gọi lại tìm bằng chữ. Điểm khác biệt nằm ở *bước hiểu đầu vào*. Sau đó các luồng cùng đi qua lọc, nới điều kiện nếu rỗng và xếp hạng.”
>
> “Theo quy tắc BR-07, điểm cuối dành 90% cho độ phù hợp và 10% cho tình trạng còn hàng. Mục đích là món hợp yêu cầu lên trước, nhưng vẫn ưu tiên món khách có thể mua. Từ bảng này, nhóm rút ra rằng ở pha thiết kế chỉ cần một lõi tìm kiếm dùng chung cho các đầu vào.”

**Ý cần hiểu:** 90% + 10% là **điểm xếp hạng**, không có nghĩa tự động loại sản phẩm hết hàng. “Trộn xếp hạng” trong sơ đồ Activity có nhắc RRF: cách gộp danh sách từ nhiều tín hiệu; nếu chưa trình bày thuật toán, chỉ cần nói “gộp thứ hạng từ khóa và vector”.

## Slide 13 — Activity diagram: ký hiệu

**Lời thoại**

> “Use case cho biết khách muốn làm gì; activity diagram cho biết các bước chạy theo thứ tự nào. Trên sơ đồ, chấm đen là điểm bắt đầu, vòng tròn kép là kết thúc, hộp bo góc là một hành động. Hình thoi cho thấy một quyết định hoặc nơi các đường thay thế nhập lại. Thanh đậm dùng khi tách ra làm hai việc song song; thanh đậm thứ hai là điểm chờ cả hai xong. Sơ đồ còn chia thành hai swimlane: bên Customer là việc khách làm, bên System là việc hệ thống làm.”

**Ý cần hiểu:** Khi chỉ sơ đồ tiếp theo, đừng gọi hình thoi và thanh đậm là cùng một loại gộp. Hình thoi gộp **các lựa chọn thay thế**; thanh đậm gộp **các việc chạy song song**.

## Slide 14 — Activity: Search Product

[Mở activity diagram](abc-online-shop-sysdes/slides/img/b1_act_search.png).

**Lời thoại**

> “[Chỉ vào đầu sơ đồ] Khách bắt đầu bằng cách chọn một trong bốn kiểu nhập: chữ, giọng nói, ảnh hoặc video. Việc của khách nằm ở cột trái; hệ thống xử lý ở cột phải. Mỗi kiểu nhập có phần hiểu riêng. Đặc biệt, với giọng nói, hệ thống tách hai việc song song là tạo vector âm thanh và chép lời để lấy điều kiện. [Chỉ vào hình thoi ở giữa] Sau đó các nhánh nhập lại thành một luồng chung: lọc sản phẩm, nới điều kiện nếu rỗng, rồi trộn các tín hiệu để xếp hạng. Kết quả và chip được trả về cho khách.”
>
> “[Chỉ vòng lặp cuối sơ đồ] Nếu khách bỏ hoặc sửa một chip, quy trình quay về bước lọc. Nó không quay lên bước hiểu câu, vì điều kiện đã ở dạng có cấu trúc. Đây là điểm quan trọng của sơ đồ: một lõi xử lý chung, và một vòng lặp sửa điều kiện nhanh.”

**Ý cần hiểu:** Đi theo mũi tên **từ trên xuống**, rồi mới nói về vòng lặp ở đáy. Tránh đọc hết nhãn tiếng Anh của mọi hộp; hãy kể lại thành một câu chuyện.

## Slide 15 — Class phân tích

[Mở class diagram](abc-online-shop-sysdes/slides/img/d1_class_analysis.png).

**Lời thoại**

> “Đến đây nhóm chuyển từ hành vi sang dữ liệu: hệ thống cần nhớ gì để những lượt tìm kiếm vừa mô tả có thể chạy? Ở giữa là Product, lưu tên, mô tả, giá và các đặc điểm như chất liệu, họa tiết, phong cách. Mỗi Product thuộc một Category. Một Product có ít nhất một ProductVariant, tức biến thể size, màu, SKU và tồn kho; vì vậy tồn kho được theo dõi ở cấp biến thể. ProductImage lưu ảnh của sản phẩm. ProductVector lưu biểu diễn phục vụ tìm theo ý nghĩa; sơ đồ cho phép tối đa hai vector cho một sản phẩm.”
>
> “Các con số 1, 0..* và 0..2 ở đầu đường nối cho biết số lượng có thể liên kết. Thoi đặc thể hiện biến thể, ảnh và vector phụ thuộc vào Product: khi sản phẩm bị xóa thì những dữ liệu thuộc về nó cũng mất theo. Category tồn tại độc lập với từng sản phẩm. Đây vẫn là *class phân tích*: nhóm mới xác định loại thông tin và quan hệ, chưa chốt kiểu dữ liệu, phương thức hay bảng cơ sở dữ liệu. Những quyết định ấy thuộc pha Design.”

**Ý cần hiểu:** Có **5 lớp**: `Category`, `Product`, `ProductVariant`, `ProductImage`, `ProductVector`. Đọc `1..*` là “một hoặc nhiều”; `0..*` là “không hoặc nhiều”; `0..2` là “tối đa hai”.

## Câu kết để chuyển sang Design

> “Tóm lại, Analysis đã cho nhóm một bức tranh thống nhất: ai dùng chức năng tìm kiếm, từng cách tìm và nhánh lỗi diễn ra ra sao, các luồng nhập lại ở bước nào và hệ thống phải nhớ những dữ liệu gì. Từ mô hình đó, phần Design tiếp theo mới quyết định chia tầng, chọn công nghệ và thiết kế chi tiết cách xây dựng.”

## Ba câu hỏi dễ gặp khi trình bày

**1. Vì sao ‘không in hình’ không được nới như màu?** Vì đó là điều khách loại trừ rõ ràng (BR-01). Nếu trả áo in hình, hệ thống đã làm sai yêu cầu. Màu có thể nới theo BR-02 khi không có kết quả, và phải báo rõ đã nới.

**2. Vì sao giọng nói vừa tạo vector vừa chép lời?** Vector âm thanh giúp tìm gần nghĩa; bản chép lời giúp nhận ra điều kiện cụ thể như “không in hình”. Nếu chép lời lỗi, vẫn còn nhánh tìm theo vector.

**3. Class phân tích khác class thiết kế ở đâu?** Class phân tích nói **cần nhớ những loại thông tin nào** và chúng liên hệ thế nào. Class thiết kế sẽ thêm kiểu dữ liệu, phương thức và các chi tiết phục vụ triển khai.

## Hai điểm cần nói cẩn thận nếu bị hỏi sâu

- Slide UC-05 ghi chip có từ UC-01, UC-02, UC-04, còn Activity trình bày chip sau cả bốn nhánh. Với ảnh, scenario có điều kiện từ ghi chú nhưng không nói rõ chip có hiện. Cách nói chắc chắn là: **khi có chip trên kết quả, khách có thể bấm bỏ chip**.
- Trong [hình class phân tích](abc-online-shop-sysdes/slides/img/d1_class_analysis.png), thoi rỗng trên quan hệ Category–Product đặt sát Product, trong khi ý nghiệp vụ là *Product thuộc Category; xóa một Product không xóa Category*. Nếu bị hỏi đúng ký pháp UML, hãy thừa nhận vị trí thoi trong hình cần kiểm tra/sửa; giải thích quan hệ nghiệp vụ và các con số ở hai đầu đường trước.

**Mẹo tập:** Mở bộ slide, nói từng đoạn **lời thoại** mà không đọc phần **ý cần hiểu**. Sau mỗi slide, tự hỏi “vì sao nhóm đưa slide này vào mạch kể?”. Trong lúc trình chiếu, phím **N** mở ghi chú gốc của slide; sơ đồ có thể bấm để phóng to.
