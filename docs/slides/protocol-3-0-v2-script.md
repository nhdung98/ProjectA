# Script thuyết trình: Protocol 3.0

Đi kèm deck [protocol-3-0-v2.html](protocol-3-0-v2.html). Thời lượng khoảng 20–22 phút, trung bình hơn 1 phút mỗi slide.

Cách đọc file này:
- Đoạn chữ thường là lời nói.
- Dòng *[in nghiêng trong ngoặc vuông]* là thao tác trên slide, không đọc ra.
- Xưng hô đang dùng "nhóm em". Nếu người nghe không phải giảng viên thì đổi thành "nhóm mình".

---

## Mở đầu: Protocol 3.0 (khoảng 40 giây)

Chào thầy cô và mọi người. Hôm nay nhóm em trình bày protocol 3.0, tức là kế hoạch thí nghiệm cho vòng tiếp theo của dự án phân loại sarcoma.

Nói ngắn gọn: nhóm sẽ so sánh nhiều pipeline học máy, nhưng so sánh một cách công bằng, trên cùng một cách chia dữ liệu. Mục tiêu là phân loại 6 subtype sarcoma từ dữ liệu RNA-seq.

Em nói trước một điều: đây vẫn là bản nháp để thảo luận. Chưa có pipeline nào được chạy, nên mọi con số kết quả trong buổi hôm nay đều là minh hoạ.

*[Chỉ vào dải 6 bước ở giữa slide.]*

Toàn bộ protocol nằm gọn trong dải này: chọn phương án cho từng bước, lọc ra 13 pipeline, chạy thử, khoá cấu hình, chạy chính thức, rồi phân tích. Em sẽ đi lần lượt từng phần.

---

## 01 · Bài toán (khoảng 2 phút)

Trước khi vào phần kỹ thuật, em nhắc lại một chút về bài toán.

*[Chỉ ô 1.]*

Mọi tế bào trong cơ thể có cùng một bộ gene, nhưng mỗi loại tế bào chỉ "bật" một số gene nhất định. Gene nào được bật thì được chép ra thành RNA, rồi RNA được dùng để tạo protein.

*[Chỉ ô 2.]*

RNA-seq là kỹ thuật đếm xem trong mẫu có bao nhiêu RNA của từng gene. Gene càng hoạt động mạnh thì càng nhiều RNA. Kết quả là mỗi khối u được mô tả bằng một dãy khoảng 20 nghìn con số. Có thể coi đó là "dấu vân tay" của khối u.

*[Chỉ ô 3.]*

Việc của nhóm là: nhìn vào dãy số đó và đoán khối u thuộc subtype nào trong 6 subtype.

*[Chỉ panel "Vì sao bài toán khó".]*

Bài toán này khó vì bốn lý do. Một, sarcoma hiếm và có rất nhiều subtype, phân biệt dưới kính hiển vi đã khó. Hai, ngay cả nhãn cũng không chắc: chỉ 206 trên 254 ca được review lại độc lập. Ba, có 254 bệnh nhân nhưng tới hơn 20 nghìn gene, nên mô hình rất dễ học thuộc nhiễu. Bốn, các lớp lệch nhau nhiều: lớp lớn nhất có 104 ca, lớp nhỏ nhất chỉ có 9.

*[Chỉ bảng biomarker.]*

Bảng này giúp hình dung trước lớp nào dễ, lớp nào khó. LMS, DDLPS và SS có dấu hiệu sinh học rõ, ví dụ DDLPS có khuếch đại gene MDM2. Còn UPS và MFS thì không có marker riêng. UPS thậm chí được chẩn đoán bằng cách loại trừ. Vì vậy nhóm dự đoán mô hình sẽ nhầm nhiều nhất giữa UPS và MFS.

Em lưu ý là bảng này chỉ để giải thích kết quả. Nhóm không đưa các marker này vào mô hình, lý do em sẽ nói ở slide 7.

---

## 02 · Ba câu hỏi (khoảng 1 phút 30 giây)

Dự án không chỉ đi tìm mô hình có điểm cao nhất. Nhóm đặt ra ba câu hỏi, và mỗi câu chặn một kiểu khiến kết quả trông đẹp hơn thực tế.

*[Chỉ thẻ 1.]*

Câu thứ nhất: con số báo cáo có trung thực không? Nếu thử 13 pipeline rồi báo điểm của pipeline cao nhất, con số đó sẽ bị thổi phồng, vì pipeline đứng đầu thường là pipeline gặp may. Nhóm dùng một cách gọi là META-SELECT để chấm điểm cả quá trình chọn, chứ không chỉ chấm pipeline thắng.

*[Chỉ thẻ 2.]*

Câu thứ hai: khi đổi một bước trong pipeline mà điểm tăng, cải thiện đó có thật không, hay chỉ do cách chia dữ liệu? Nhóm kiểm định từng thay đổi bằng thống kê. Và nếu kết quả là "không khác biệt" thì đó cũng là một kết luận có giá trị.

*[Chỉ thẻ 3.]*

Câu thứ ba: pipeline nào nên mang ra dùng thực tế? Không nhất thiết là pipeline điểm cao nhất. Nhóm chọn pipeline đơn giản nhất mà không kém rõ ràng so với pipeline đứng đầu.

Ba câu này sẽ quay lại ở slide 12 và slide 15.

---

## 03 · Bối cảnh và mục tiêu (khoảng 1 phút)

*[Chỉ dãy số liệu và biểu đồ lệch lớp.]*

Đây là dữ liệu cụ thể: 254 bệnh nhân từ TCGA-SARC, khoảng 20.500 gene, 6 subtype. Biểu đồ cho thấy rõ lệch lớp: LMS chiếm khoảng 40%, còn MPNST và SS chỉ khoảng 4% mỗi lớp.

Ở Round 1, tức protocol 2.0, nhóm chỉ thử SVM. Kết quả tốt nhất là SVM tuyến tính kết hợp chọn 150 gene bằng ANOVA, đạt macro-F1 0,772. Đây là mốc để so sánh.

Protocol 3.0 có hai mục tiêu: tìm pipeline tốt hơn, và xây một quy trình mà sau này dùng lại được cho các bài toán RNA-seq tương tự.

Nhóm không thử hết mọi tổ hợp. Mỗi pipeline được đưa vào vì một vai trò cụ thể: làm sàn, làm mốc tham chiếu, làm thí nghiệm ablation, làm ứng viên, hoặc làm đối chứng âm.

---

## 04 · Những gì giữ nguyên từ 2.0 (khoảng 1 phút 30 giây)

Phần này giữ nguyên so với Round 1, và điều quan trọng nhất là cách chia dữ liệu.

*[Bấm "Chạy qua 15 lần chia" để các chấm đổi màu.]*

Mỗi chấm là một bệnh nhân. Nhóm dùng nested CV, tức là kiểm định chéo hai tầng. Tầng ngoài chia 5 phần và lặp 3 lần, tổng cộng 15 lần chia. Mỗi lần, một phần được giữ lại làm đề thi cuối, gọi là outer test. Phần còn lại được chia tiếp thành 4 phần ở tầng trong, dùng để chọn tham số.

*[Chỉ bảng số ca bên phải.]*

Nhìn vào bảng: mỗi tập validation ở tầng trong chỉ có 1 đến 2 ca MPNST. Vì vậy grid tham số phải nhỏ, và recall của MPNST luôn phải đi kèm khoảng tin cậy.

Nhóm dùng lại đúng các file chia dữ liệu của Round 1. Nhờ vậy, mọi pipeline mới so được trực tiếp, theo từng cặp, với kết quả cũ. Metric chính vẫn là macro-F1. Nhóm không dùng micro-F1 vì nó bị lớp đông nhất, LMS, chi phối.

---

## 05 · Metric và cách lưu kết quả (khoảng 1 phút)

Nhóm thêm một số metric để nhìn rõ hơn các lớp hiếm.

*[Chọn "MPNST · 9 ca", kéo thanh trượt về 9/9 rồi về 1/9.]*

Đây là lý do cần khoảng tin cậy Wilson. Với lớp chỉ có 9 ca, khoảng tin cậy thông thường, gọi là Wald, có thể tràn ra ngoài khoảng 0 đến 1, hoặc co lại thành một điểm, như thể mô hình chắc chắn tuyệt đối. Cả hai đều vô lý. Wilson luôn cho một khoảng hợp lý.

Ngoài ra, nhóm thêm MCC làm metric phụ, và lưu macro-F1 của từng lần chia, tức 15 giá trị, để làm kiểm định thống kê ở phần sau.

---

## 06 · Pipeline 5 stage (khoảng 1 phút 30 giây)

Một pipeline gồm 5 bước nối tiếp nhau: lọc gene, chuẩn hoá, chọn đặc trưng, xử lý lệch lớp, và cuối cùng là bộ phân loại.

*[Bấm lần lượt P02, rồi P07.]*

Mỗi pipeline là một tổ hợp, chọn một phương án ở mỗi bước. Ví dụ P02 là cấu hình của Round 1. P07 là ứng viên chính: logistic regression elastic-net, kèm trọng số theo lớp. Các ô màu hồng là chỗ pipeline đó khác với pipeline dùng để so sánh.

Hai chi tiết đáng chú ý. Thứ nhất, ngưỡng lọc gene tính bằng số mẫu, ít nhất 5 mẫu, chứ không theo phần trăm, để không vô tình bỏ những gene chỉ bật ở lớp hiếm. Thứ hai, mọi bước, trừ phép log, đều được học lại từ đầu trong từng fold. Điều này để tránh rò rỉ dữ liệu, em sẽ nói kỹ ở slide 13.

---

## 07 · Những gì bị loại hoặc hoãn (khoảng 1 phút)

Slide này trả lời câu hỏi "sao không thử cái này, cái kia".

Có hai thứ đã thử ở Round 1 và không giữ lại: PCA kém hơn ANOVA, còn SVM RBF cho điểm ngang SVM tuyến tính nhưng chậm hơn khoảng 2 lần.

*[Bấm bộ lọc "Loại".]*

Có bốn thứ bị loại hẳn. Đầu tiên là panel marker cố định như MDM2, CDK4: các marker này được tìm ra từ chính dữ liệu TCGA-SARC, nên dùng lại trên cùng dữ liệu sẽ cho điểm cao hơn thực tế. Thứ hai là các phương pháp chọn gene phức tạp như Boruta hay RFE, vì không hơn được cách lọc đơn giản. Thứ ba là deep learning, vì 254 mẫu là quá ít. Cuối cùng là undersampling, vì nó buộc phải bỏ hơn 90% dữ liệu LMS.

ComBat chỉ dùng trong phân tích độ nhạy. Còn các ý tưởng như GSVA hay TabPFN thì để sang vòng sau.

---

## 08 · Shortlist 13 pipeline (khoảng 1 phút 30 giây)

*[Chỉ bản đồ, đi từ P02 sang phải.]*

Đây là bản đồ của 13 pipeline. Đọc từ P02, tức Round 1, sang phải. Mỗi mũi tên đổi đúng một bước, và trả lời đúng một câu hỏi.

*[Bấm vài node: P03, P05, P07.]*

Ví dụ, từ P02 sang P03 chỉ thêm trọng số theo lớp. Câu hỏi là: trọng số có giúp không? Từ P04 sang P05 thì bỏ ANOVA. Câu hỏi là: có cần chọn gene có giám sát không? Cứ thế đi tới P07, ứng viên chính.

Về vai trò: P01 là sàn, mô hình không học gì, điểm khoảng 0,1 đến 0,17. P02 chạy lại Round 1, và engine mới phải ra đúng 0,772, nếu không thì code có lỗi. P10 dùng SMOTE là đối chứng âm. Còn PAM, random forest và kNN là các baseline thuộc họ mô hình khác.

---

## 09 · Hyperparameter (khoảng 1 phút)

Grid tham số được giữ nhỏ có chủ ý, tối đa 20 ứng viên mỗi pipeline.

Lý do: tập validation quá nhỏ. Grid càng lớn thì càng dễ chọn trúng một ứng viên chỉ đơn giản là gặp may. Khi hai ứng viên hoà điểm, nhóm chọn ứng viên đơn giản hơn.

*[Bấm vào cột biên phải ở 3 hàng để kích hoạt quy tắc mở rộng.]*

Còn nếu tham số tốt nhất cứ nằm sát biên của grid thì sao? Nhóm có một quy tắc: nếu ít nhất 3 trên 5 fold chạm cùng một biên, grid được mở rộng thêm một bước theo hướng đó. Chỉ mở rộng một lần, chỉ ở vòng chạy thử, và chỉ dựa vào tầng trong, không nhìn điểm của đề thi cuối.

---

## 10 · Quy trình 2 vòng (khoảng 1 phút 30 giây)

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

## 11 · Chi phí tính toán (khoảng 45 giây)

Tổng cộng khoảng 9.200 lần huấn luyện mô hình, chỉ bằng một nửa protocol 2.0, dù số loại mô hình nhiều hơn. Lý do là nhóm không thử hết mọi tổ hợp.

*[Kéo thanh số lõi CPU từ 1 lên 8.]*

Ước tính tổng khoảng 4,7 giờ CPU trên một lõi. Nếu chạy song song 4 lõi thì mỗi lần lặp mất khoảng 18 phút. Em nói rõ: số đo thật duy nhất hiện có là SVM của Round 1. Các con số khác là ước đoán và sẽ được chỉnh lại sau smoke run. P07 dự kiến là pipeline chậm nhất.

---

## 12 · Chọn pipeline thắng mà không bị thổi phồng (khoảng 2 phút)

Slide này giải thích câu hỏi thứ nhất.

*[Bấm "Chạy 1 lần" vài lần, rồi "Chạy 500 lần".]*

Đây là một mô phỏng. Giả sử 12 pipeline thật ra mạnh ngang nhau, đều 0,78. Mỗi lần chia dữ liệu, điểm của từng pipeline dao động một chút. Pipeline đứng đầu luôn là pipeline gặp may nhiều nhất. Chạy 500 lần thì thấy: điểm của pipeline đứng đầu trung bình cao hơn giá trị thật. Nếu báo con số đó thì nhóm đang tự thổi phồng kết quả.

*[Chỉ panel META-SELECT, bấm "Chạy lại bước chọn".]*

META-SELECT xử lý vấn đề này như sau. Trong mỗi lần chia, nhóm chọn pipeline chỉ dựa trên điểm ở tầng trong, rồi lấy dự đoán của pipeline đó trên đề thi cuối. Ghép 15 lần chia lại, ta được một con số phản ánh cả quá trình chọn. Đó là con số chính mà dự án sẽ báo cáo.

*[Chỉ ba thẻ câu hỏi.]*

Câu 2 dùng kiểm định Bayesian trên 11 cặp ablation đã đăng ký trước. Kết quả là ba xác suất: kém hơn, tương đương, hoặc tốt hơn. Hai pipeline chênh nhau dưới 0,01 macro-F1 được coi là bằng nhau. Câu 3 chọn pipeline đơn giản nhất trong nhóm tương đương với pipeline đứng đầu. Và nhóm vẫn báo cáo mọi pipeline, không chỉ pipeline thắng.

---

## 13 · Chống rò rỉ dữ liệu (khoảng 1 phút 30 giây)

Nguyên tắc: mọi thứ mô hình học thì chỉ được học từ phần train. Phần test chỉ được dùng để áp dụng.

*[Bấm nút "Sai".]*

Lỗi hay gặp nhất là chọn gene, tính ANOVA hay chạy SMOTE trên cả 254 ca rồi mới chia fold. Khi đó, đề thi đã bị lộ từ trước.

*[Bấm "Chạy lại với dữ liệu mới" hai, ba lần.]*

Thí nghiệm này cho thấy tác hại rõ nhất. Dữ liệu ở đây hoàn toàn ngẫu nhiên, không có tín hiệu nào, nên độ chính xác trung thực phải quanh 50%. Nếu chọn gene trên toàn bộ dữ liệu trước rồi mới chia, độ chính xác nhảy lên rất cao, dù không có gì để học. Còn nếu chọn gene trong từng fold thì độ chính xác quay về khoảng 50%, đúng như phải thế.

Vì vậy mọi bước học từ dữ liệu đều nằm trong một Pipeline. Và nhóm không sửa gì sau khi đã xem điểm.

---

## 14 · Phân tích độ nhạy (khoảng 1 phút)

Nhóm có ba phép thử để xem kết quả có còn đứng vững khi nhìn dữ liệu theo cách khác.

Thứ nhất: mô hình học subtype hay học bệnh viện? Nhóm chia dữ liệu theo nơi lấy mẫu, để bệnh viện trong tập test chưa từng xuất hiện khi train. Nếu điểm giảm mạnh thì mô hình đang nhận ra bệnh viện chứ không phải subtype.

Thứ hai: nhãn có nhiễu không? Nhóm chạy lại chỉ với 206 ca đã được review.

Thứ ba: bao nhiêu lỗi nằm ở ranh giới UPS và MFS? Nhóm gộp hai lớp này lại. Như đã nói ở slide 1, hai subtype này có thể chỉ là hai đầu của cùng một phổ sinh học.

---

## 15 · Kết quả mẫu (khoảng 2 phút)

*[Chỉ dải màu vàng.]*

Em nhấn mạnh lại: mọi con số trên slide này là giả lập. Slide chỉ để mọi người thấy output sẽ trông thế nào và đọc ra sao.

*[Chỉ biểu đồ cột.]*

Trong ví dụ này, P07 đứng đầu với 0,807. META-SELECT ra 0,803, thấp hơn một chút. Khoảng chênh đó chính là phần bị thổi phồng nếu chỉ báo điểm của pipeline đứng đầu.

*[Bấm vài cặp ablation, ví dụ P06 → P07.]*

Đây là cách đọc kiểm định. Mỗi cặp cho ba xác suất. Nếu một xác suất vượt 0,95 thì nhóm kết luận. Nếu không thì ghi là chưa kết luận được.

*[Chỉ panel câu 3, đổi ROPE từ 0,01 sang 0,02.]*

Với câu 3, pipeline được chọn mang sang app là P06, logistic regression L2, chứ không phải P07. P06 đơn giản hơn, nhanh hơn khoảng 16 lần, và không có bằng chứng rõ là kém hơn. Nhưng nếu nới ngưỡng từ 0,01 lên 0,02 thì lựa chọn đổi sang P03. Vì vậy ngưỡng này phải được chốt trước khi mở niêm phong.

*[Chỉ confusion matrix.]*

Cuối cùng, lỗi tập trung ở ranh giới UPS và MFS, đúng như dự đoán từ phần biomarker. Còn recall của MPNST là 6 trên 9, nhưng khoảng tin cậy trải từ 0,35 đến 0,88. Với 9 ca, đoán đúng thêm hay bớt một ca có thể chỉ là ngẫu nhiên.

---

## 16 · Quy trình tái sử dụng (khoảng 45 giây)

*[Bấm "Đi qua từng bước".]*

Ngoài kết quả cho sarcoma, protocol này còn là một quy trình 8 bước, dùng lại được cho các bài toán RNA-seq khác có ít mẫu và nhiều gene: cập nhật danh mục phương án, lọc pipeline theo vai trò, dùng chung cách chia dữ liệu, chạy thử rồi khoá cấu hình, chạy chính thức, báo cáo bằng META-SELECT, kiểm định đăng ký trước, và cuối cùng là phân tích độ nhạy.

Những phần chỉ dành cho sarcoma, như marker hay ranh giới UPS và MFS, đều nằm ở phần diễn giải. Nên khi áp dụng cho bệnh khác, có thể tách chúng ra dễ dàng.

---

## 17 · Việc cần chốt và bước tiếp theo (khoảng 1 phút 30 giây)

Trước khi mở niêm phong, nhóm cần thống nhất sáu điểm. Em đọc nhanh:

Một, ngưỡng xác suất để kết luận một cặp ablation, hiện đang giả định 0,95. Hai, khoảng tin cậy Wilson tính trên một lần lặp hay gộp ba lần. Gộp thì mỗi bệnh nhân bị đếm ba lần và khoảng sẽ hẹp giả tạo. Ba, phân tích độ nhạy chạy cho pipeline được chọn hay pipeline có điểm cao nhất. Bốn, định nghĩa bằng số thế nào là "giảm mạnh" trong phép thử theo bệnh viện. Năm, có báo cáo thêm kết quả với ngưỡng 0,02 không. Và sáu, một số tài liệu tham khảo còn cần kiểm chứng lại.

*[Tick các ô khi nhóm thống nhất được từng điểm.]*

Về bước tiếp theo: nhóm sẽ viết engine mới cho 13 pipeline, chạy smoke run để đo thời gian, kiểm tra P02 có ra đúng 0,772 không, rồi bắt đầu vòng A.

Phần trình bày của nhóm em đến đây là hết. Cảm ơn thầy cô và mọi người đã lắng nghe. Nhóm rất mong nhận được góp ý, nhất là về sáu điểm cần chốt ở trên.
