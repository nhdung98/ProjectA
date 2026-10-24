# Script thuyết trình: Protocol 3.0

Đi kèm deck [protocol-3-0-presentation.html](protocol-3-0-presentation.html). Thời lượng khoảng 17–19 phút. Slide 10 (kết quả mẫu) là phần dài nhất, khoảng 4–5 phút.

Cách đọc file này:
- Đoạn chữ thường là lời nói.
- Dòng *[in nghiêng trong ngoặc vuông]* là thao tác trên slide, không đọc ra.
- Xưng hô đang dùng "nhóm em". Nếu người nghe không phải giảng viên thì đổi thành "nhóm mình".

---

## Mở đầu: Protocol 3.0 (khoảng 40 giây)

Chào thầy cô và mọi người. Hôm nay nhóm em trình bày protocol 3.0, tức là kế hoạch thí nghiệm cho vòng tiếp theo của dự án phân loại sarcoma.

Nói ngắn gọn: đây là một benchmark so sánh công bằng nhiều pipeline học máy trên dữ liệu RNA-seq (TCGA-SARC) để phân loại 6 subtype sarcoma. Các pipeline được so sánh trên cùng một cách chia dữ liệu. Dự án không chỉ tìm mô hình tốt nhất, mà còn dùng nhiều phương pháp và chỉ số đánh giá để biết kết quả có trung thực và đáng tin hay không.

Em nói trước một điều: đây vẫn là bản nháp để thảo luận. Chưa có pipeline nào được chạy, nên mọi con số kết quả trong buổi hôm nay đều là minh hoạ.

*[Chỉ vào dải 6 bước ở giữa slide.]*

Toàn bộ protocol nằm gọn trong dải này: chọn phương án cho từng bước, lọc ra 13 pipeline, chạy thử, khoá cấu hình, chạy chính thức, rồi phân tích. Em sẽ đi lần lượt từng phần.

---

## 01 · Bài toán (khoảng 1 phút 15 giây)

Trước khi vào phần kỹ thuật, em nhắc lại một chút về bài toán.

*[Chỉ ô 1.]*

Mọi tế bào trong cơ thể có cùng một bộ gene, nhưng mỗi loại tế bào chỉ "bật" một số gene nhất định. Gene nào được bật thì được chép ra thành RNA, rồi RNA được dùng để tạo protein.

*[Chỉ ô 2.]*

RNA-seq là kỹ thuật đếm xem trong mẫu có bao nhiêu RNA của từng gene. Gene càng hoạt động mạnh thì càng nhiều RNA. Kết quả là mỗi khối u được mô tả bằng một dãy khoảng 20 nghìn con số. Có thể coi đó là "dấu vân tay" của khối u.

*[Chỉ ô 3.]*

Việc của nhóm là: nhìn vào dãy số đó và đoán khối u thuộc subtype nào trong 6 subtype.

---

## 02 · Bối cảnh và mục tiêu (khoảng 1 phút 15 giây)

*[Chỉ dãy số liệu và biểu đồ lệch lớp.]*

Đây là dữ liệu cụ thể: 254 bệnh nhân từ TCGA-SARC, khoảng 20.500 gene, 6 subtype. Số gene gấp khoảng 80 lần số bệnh nhân, nên mô hình rất dễ học thuộc nhiễu. Biểu đồ cũng cho thấy lệch lớp rõ: LMS chiếm khoảng 40%, còn MPNST và SS chỉ khoảng 4% mỗi lớp.

Ở Round 1, tức protocol 2.0, nhóm chỉ thử SVM. Kết quả tốt nhất là SVM tuyến tính kết hợp chọn 150 gene bằng ANOVA, đạt macro-F1 0,772. Đây là mốc để so sánh.

Protocol 3.0 có hai mục tiêu: tìm pipeline tốt hơn, và xây một quy trình mà sau này dùng lại được cho các bài toán RNA-seq tương tự.

Nhóm không thử hết mọi tổ hợp. Mỗi pipeline được đưa vào vì một vai trò cụ thể: làm sàn, làm mốc tham chiếu, làm thí nghiệm ablation, làm ứng viên, hoặc làm đối chứng âm.

---

## 03 · Ba câu hỏi (khoảng 1 phút 30 giây)

Dự án không chỉ đi tìm mô hình có điểm cao nhất. Nhóm đặt ra ba câu hỏi, và mỗi câu chặn một kiểu khiến kết quả trông đẹp hơn thực tế.

*[Chỉ thẻ 1.]*

Câu thứ nhất: con số báo cáo có trung thực không? Nếu thử 13 pipeline rồi báo điểm của pipeline cao nhất, con số đó sẽ bị thổi phồng, vì pipeline đứng đầu thường là pipeline gặp may. Nhóm dùng một cách gọi là META-SELECT để chấm điểm cả quá trình chọn, chứ không chỉ chấm pipeline thắng.

*[Chỉ thẻ 2.]*

Câu thứ hai: khi đổi một bước trong pipeline mà điểm tăng, cải thiện đó có thật không, hay chỉ do cách chia dữ liệu? Nhóm kiểm định từng thay đổi bằng thống kê. Và nếu kết quả là "không khác biệt" thì đó cũng là một kết luận có giá trị.

*[Chỉ thẻ 3.]*

Câu thứ ba: pipeline nào nên mang ra dùng thực tế? Không nhất thiết là pipeline điểm cao nhất. Nhóm chọn pipeline đơn giản nhất mà không kém rõ ràng so với pipeline đứng đầu.

Cả ba câu sẽ được trả lời bằng ví dụ ở slide 10.

---

## 04 · Pipeline 5 stage (khoảng 1 phút 30 giây)

Một pipeline gồm 5 bước nối tiếp nhau: lọc gene, chuẩn hoá, chọn đặc trưng, xử lý lệch lớp, và cuối cùng là bộ phân loại.

*[Bấm lần lượt P02, rồi P07.]*

Mỗi pipeline là một tổ hợp, chọn một phương án ở mỗi bước. Ví dụ P02 là cấu hình của Round 1. P07 là ứng viên chính: logistic regression elastic-net, kèm trọng số theo lớp. Các ô màu hồng là chỗ pipeline đó khác với pipeline dùng để so sánh.

Hai chi tiết đáng chú ý. Thứ nhất, ngưỡng lọc gene tính bằng số mẫu, ít nhất 5 mẫu, chứ không theo phần trăm, để không vô tình bỏ những gene chỉ bật ở lớp hiếm. Thứ hai, mọi bước, trừ phép log, đều được học lại từ đầu chỉ trên phần dữ liệu train của mỗi lần chia. Phần test không bao giờ được dùng để học, nên không có rò rỉ dữ liệu. Cách chia dữ liệu em sẽ nói ở slide 6.

---

## 05 · Shortlist 13 pipeline (khoảng 1 phút 30 giây)

*[Chỉ bản đồ, đi từ P02 sang phải.]*

Đây là bản đồ của 13 pipeline. Đọc từ P02, tức Round 1, sang phải. Mỗi mũi tên đổi đúng một bước, và trả lời đúng một câu hỏi.

*[Bấm vài node: P03, P05, P07.]*

Ví dụ, từ P02 sang P03 chỉ thêm trọng số theo lớp. Câu hỏi là: trọng số có giúp không? Từ P04 sang P05 thì bỏ ANOVA. Câu hỏi là: có cần chọn gene có giám sát không? Cứ thế đi tới P07, ứng viên chính.

Về vai trò: P01 là sàn, mô hình không học gì, điểm khoảng 0,1 đến 0,17. P02 chạy lại Round 1, và engine mới phải ra đúng 0,772, nếu không thì code có lỗi. P10 dùng SMOTE là đối chứng âm. Còn PAM, random forest và kNN là các baseline thuộc họ mô hình khác.

---

## 06 · Những gì giữ nguyên từ 2.0 (khoảng 1 phút 30 giây)

Phần này giữ nguyên so với Round 1, và điều quan trọng nhất là cách chia dữ liệu.

*[Bấm "Chạy qua 15 lần chia" để các chấm đổi màu.]*

Mỗi chấm là một bệnh nhân. Nhóm dùng nested CV, tức là kiểm định chéo hai tầng. Tầng ngoài chia 5 phần và lặp 3 lần, tổng cộng 15 lần chia. Mỗi lần, một phần được giữ lại làm đề thi cuối, gọi là outer test. Phần còn lại được chia tiếp thành 4 phần ở tầng trong, dùng để chọn tham số.

*[Chỉ bảng số ca bên phải.]*

Nhìn vào bảng: mỗi tập validation ở tầng trong chỉ có 1 đến 2 ca MPNST. Vì vậy grid tham số phải nhỏ, và recall của MPNST luôn phải đi kèm khoảng tin cậy. Em sẽ quay lại điểm này ở slide 10.

Nhóm dùng lại đúng các file chia dữ liệu của Round 1. Nhờ vậy, mọi pipeline mới so được trực tiếp, theo từng cặp, với kết quả cũ. Metric chính vẫn là macro-F1. Nhóm không dùng micro-F1 vì nó bị lớp đông nhất, LMS, chi phối.

---

## 07 · Hyperparameter (khoảng 1 phút)

Grid tham số được giữ nhỏ có chủ ý, tối đa 20 ứng viên mỗi pipeline.

Lý do: tập validation quá nhỏ. Grid càng lớn thì càng dễ chọn trúng một ứng viên chỉ đơn giản là gặp may. Khi hai ứng viên hoà điểm, nhóm chọn ứng viên đơn giản hơn.

*[Bấm vào cột biên phải ở 3 hàng để kích hoạt quy tắc mở rộng.]*

Còn nếu tham số tốt nhất cứ nằm sát biên của grid thì sao? Nhóm có một quy tắc: nếu ít nhất 3 trên 5 fold chạm cùng một biên, grid được mở rộng thêm một bước theo hướng đó. Chỉ mở rộng một lần, chỉ ở vòng chạy thử, và chỉ dựa vào tầng trong, không nhìn điểm của đề thi cuối.

---

## 08 · Quy trình 2 vòng (khoảng 1 phút 30 giây)

Đây là phần nhóm thấy quan trọng nhất về mặt quy trình.

*[Bấm "Bước tiếp" qua từng bước.]*

Đầu tiên là smoke run: chạy thử một fold cho mỗi pipeline để đo thời gian và bắt lỗi sớm.

Tiếp theo là vòng A. Nhóm chạy toàn bộ một lần, nhưng chỉ được xem thông tin kỹ thuật: có lỗi không, có hội tụ không, chạy mất bao lâu. Điểm trên đề thi cuối vẫn được niêm phong.

Nếu có lỗi kỹ thuật thì sửa. Nhưng không được loại pipeline nào vì điểm thấp.

*[Dừng ở bước "Đóng băng config".]*

Sau đó nhóm khoá toàn bộ cấu hình bằng một commit có tag. Cách này tương tự việc đăng ký trước trong nghiên cứu lâm sàng: viết sẵn mình sẽ làm gì và so sánh gì, trước khi nhìn kết quả.

Cuối cùng là vòng B, chạy chính thức đủ 3 lần lặp từ đúng commit đó. Chỉ sau vòng B mới mở niêm phong điểm.

*[Chỉ callout màu hồng.]*

Có thể có người hỏi: kết quả vòng A sẽ bị bỏ, sao vẫn không được xem điểm? Vì vòng B dùng lại đúng cách chia đó. Xem điểm ở vòng A rồi chỉnh cấu hình thì cũng là đang chỉnh theo đề thi của vòng B.

---

## 09 · Chi phí tính toán (khoảng 45 giây)

Tổng cộng khoảng 9.200 lần huấn luyện mô hình, chỉ bằng một nửa protocol 2.0, dù số loại mô hình nhiều hơn. Lý do là nhóm không thử hết mọi tổ hợp.

*[Kéo thanh số lõi CPU từ 1 lên 8.]*

Ước tính tổng khoảng 4,7 giờ CPU trên một lõi. Nếu chạy song song 4 lõi thì mỗi lần lặp mất khoảng 18 phút. Em nói rõ: số đo thật duy nhất hiện có là SVM của Round 1. Các con số khác là ước đoán và sẽ được chỉnh lại sau smoke run. P07 dự kiến là pipeline chậm nhất.

---

## 10 · Kết quả mẫu (khoảng 4–5 phút)

*[Chỉ dải màu vàng.]*

Em nhấn mạnh lại: mọi con số trên slide này là giả lập. Slide chỉ để mọi người thấy output sẽ trông thế nào và đọc ra sao. Slide này trả lời lần lượt ba câu hỏi ở slide 3.

### Câu 1: con số chính

*[Chỉ biểu đồ cột.]*

Trong ví dụ này, P07 đứng đầu với 0,807. META-SELECT ra 0,803, thấp hơn một chút. Khoảng chênh đó chính là phần bị thổi phồng nếu chỉ báo điểm của pipeline đứng đầu.

*[Chỉ panel macro-F1 bên phải.]*

Trước khi đi tiếp, em nói nhanh macro-F1 là gì. Với mỗi lớp, nhóm tính F1 riêng, tức là kết hợp precision và recall của lớp đó. Sau đó lấy trung bình cộng 6 giá trị F1, nên mỗi lớp nặng như nhau, dù LMS có 104 ca còn MPNST chỉ có 9. Trong ví dụ này, LMS và SS có F1 trên 0,9, còn MFS chỉ 0,6. Macro-F1 ra 0,792, trong khi accuracy là 0,831. Accuracy cao hơn vì bị LMS, lớp đông nhất, kéo lên. Đó là lý do nhóm dùng macro-F1.

*[Chỉ panel META-SELECT ở hàng dưới, bên trái.]*

META-SELECT làm như sau: trong mỗi lần chia, nhóm chọn pipeline chỉ dựa trên điểm ở tầng trong, rồi lấy dự đoán của pipeline đó trên đề thi cuối. Ghép 15 lần chia lại thì được con số chính của dự án. Ở đây họ LR được chọn ở 14 trên 15 lần chia, nhưng không có cấu hình LR nào áp đảo. Tầng trong chỉ dùng để chọn, tầng ngoài chỉ dùng để chấm.

*[Chỉ panel mô phỏng bên cạnh. Bấm "Chạy 1 lần" vài lần, rồi "Chạy 500 lần".]*

Vì sao phải làm phức tạp vậy? Đây là một mô phỏng. Giả sử 12 pipeline thật ra mạnh ngang nhau, đều 0,78. Mỗi cách chia dữ liệu cho mỗi pipeline một điểm hơi khác. Pipeline đứng đầu thường là pipeline gặp may nhiều nhất, nên điểm của nó thường cao hơn giá trị thật. Chạy 500 lần thì thấy rõ: điểm của pipeline đứng đầu trung bình cao hơn giá trị thật khoảng 0,02. Nếu báo con số đó thì nhóm đang tự thổi phồng kết quả.

### Câu 2: cải thiện có thật không

*[Bấm vài cặp ablation, ví dụ P06 → P07.]*

Đây là cách đọc kiểm định. Nhóm lưu macro-F1 của từng lần chia, tức 15 giá trị, rồi dùng kiểm định Bayesian trên 11 cặp ablation đã đăng ký trước. Mỗi cặp cho ba xác suất: kém hơn, tương đương, hoặc tốt hơn. Hai pipeline chênh nhau dưới 0,01 macro-F1 được coi là bằng nhau. Nếu một xác suất vượt 0,95 thì nhóm kết luận. Nếu không thì ghi là chưa kết luận được.

### Câu 3: mang pipeline nào sang app

*[Chỉ panel câu 3, đổi ROPE từ 0,01 sang 0,02.]*

Với câu 3, pipeline được chọn mang sang app là P06, logistic regression L2, chứ không phải P07. P06 đơn giản hơn, nhanh hơn khoảng 16 lần, và không có bằng chứng rõ là kém hơn. Nhưng nếu nới ngưỡng từ 0,01 lên 0,02 thì lựa chọn đổi sang P03. Vì vậy ngưỡng này phải được chốt trước khi mở niêm phong.

### Đọc lỗi theo từng lớp

*[Chỉ confusion matrix, rồi bảng biomarker bên cạnh.]*

Cuối cùng là nhìn xem mô hình sai ở đâu. Lỗi tập trung ở ranh giới UPS và MFS, 7 cộng 8 ca. Bảng biomarker bên cạnh giải thích vì sao: LMS, DDLPS và SS có dấu hiệu sinh học rõ, ví dụ DDLPS có khuếch đại gene MDM2. Còn UPS và MFS thì không có marker riêng, UPS thậm chí được chẩn đoán bằng cách loại trừ. Nên mô hình nhầm giữa hai lớp này là điều đã kỳ vọng. Em lưu ý là bảng này chỉ để diễn giải, nhóm không đưa các marker này vào mô hình.

*[Chỉ dòng MPNST trong phần recall.]*

Còn recall của MPNST là 6 trên 9, nhưng khoảng tin cậy trải từ 0,35 đến 0,88. Với 9 ca, đoán đúng thêm hay bớt một ca có thể chỉ là ngẫu nhiên.

*[Ở panel Wilson CI: chọn "MPNST · 9 ca", kéo thanh trượt về 9/9 rồi về 1/9.]*

Đó là lý do nhóm dùng khoảng tin cậy Wilson. Với lớp chỉ có 9 ca, khoảng tin cậy thông thường, gọi là Wald, có thể tràn ra ngoài khoảng 0 đến 1, hoặc co lại thành một điểm, như thể mô hình chắc chắn tuyệt đối. Cả hai đều vô lý. Wilson luôn cho một khoảng hợp lý.

---

## 11 · Quy trình tái sử dụng (khoảng 1 phút 15 giây)

*[Bấm "Đi qua từng bước".]*

Ngoài kết quả cho sarcoma, protocol này còn là một quy trình 8 bước, dùng lại được cho các bài toán RNA-seq khác có ít mẫu và nhiều gene: cập nhật danh mục phương án, lọc pipeline theo vai trò, dùng chung cách chia dữ liệu, chạy thử rồi khoá cấu hình, chạy chính thức, báo cáo bằng META-SELECT, kiểm định đăng ký trước, và cuối cùng là phân tích độ nhạy.

Những phần chỉ dành cho sarcoma, như marker hay ranh giới UPS và MFS, đều nằm ở phần diễn giải. Nên khi áp dụng cho bệnh khác, có thể tách chúng ra dễ dàng.

Về bước tiếp theo: nhóm sẽ viết engine mới cho 13 pipeline, chạy smoke run để đo thời gian, kiểm tra P02 có ra đúng 0,772 không, rồi bắt đầu vòng A.

Phần trình bày của nhóm em đến đây là hết. Cảm ơn thầy cô và mọi người đã lắng nghe. Nhóm rất mong nhận được góp ý.
