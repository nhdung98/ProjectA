# Kết quả giả lập của Protocol 3.0: output trông như thế nào và đọc ra sao

> ⚠️ **TOÀN BỘ SỐ TRONG FILE NÀY LÀ GIẢ LẬP.** Chưa có pipeline nào được chạy. Các con số được sinh bằng một script ngẫu nhiên có seed, chỉ để cho thấy **hình dạng** của từng output và **cách đọc** nó. Không được trích bất kỳ số nào ở đây vào báo cáo.

## Mục lục

| Phần | Mục | Output | Lấy từ | Trả lời câu hỏi |
| --- | --- | --- | --- | --- |
| **I. Bảng kết quả gốc** | 1 | **Bảng A** · macro-F1 gộp 254 ca | Dự đoán outer, gộp theo repeat | Mỗi pipeline đạt bao nhiêu? |
| | 2 | **Bảng A2** · BA, MCC, recall MFS/MPNST có Wilson CI | Dự đoán outer, gộp theo repeat | Metric phụ của mọi pipeline |
| | 3 | **Bảng B** · macro-F1 theo 15 outer fold | Dự đoán outer, tách theo fold | Dữ liệu đầu vào cho kiểm định |
| | 4 | **Bảng D** · tham số được chọn ở mỗi outer fold | `search_results` của từng run | Grid có hợp lý không, việc tune có ổn định không? |
| **II. Ba câu hỏi chính** | 5 | **META-SELECT** | Điểm inner (Bảng C) + Bảng B | Câu 1: **quy trình của nhóm đạt bao nhiêu?** (con số chính) |
| | 6 | **Ablation** · Bayesian correlated t-test, ROPE 0,01 và 0,02 | Bảng B | Câu 2: **stage nào thật sự quan trọng?** |
| | 7 | **Nhóm tương đương** | Bảng A + Bảng B | Câu 3: **mang pipeline nào sang app?** |
| **III. Pipeline được chọn** | 8 | **Confusion matrix + recall theo lớp có Wilson CI** | Dự đoán outer của pipeline được chọn | Mô hình sai ở đâu, nhất là với lớp hiếm? |
| | 9 | **Độ nhạy** S-TSS · S-206 · S-5CLASS | Chạy thêm cho pipeline được chọn | Kết quả có vững khi đổi góc nhìn dữ liệu? |
| **IV. Chi phí** | 10 | **Runtime và số fit** | `run_manifest` của từng run | Chi phí của mỗi pipeline |
| **V. Ghi chú** | 11 | Đoạn văn mẫu cho báo cáo | Các mục trên | Kết quả được viết thành văn ra sao? |
| | 12 | Output không nằm trong file này | — | Protocol còn sinh ra gì nữa? |
| | 13 | Giả định của file, chờ nhóm chốt | — | Nhóm cần quyết định gì trước khi mở niêm phong? |

## Ghi chú chung

- Mọi bảng trong file này đến từ **vòng B** (3 repeat chạy từ commit đã tag `p3.0-frozen`). Kết quả vòng A đã bị bỏ và không xuất hiện ở đâu cả.
- **Bảng C** (điểm inner của mọi ứng viên ở mọi fold) là bảng trung gian rất lớn. Nó chỉ dùng để tính META-SELECT nên không in ra ở đây.
- Các con số giả lập **khớp với nhau** như số thật sẽ khớp. Kiểm định ở mục 6 và 7 được tính thật từ Bảng B. META-SELECT ở mục 5 đọc điểm outer từ Bảng B. Macro-F1, BA và MCC của confusion matrix ở mục 8 đúng bằng các ô P06 · R1 ở mục 1 và 2. Số fit ở mục 10 khớp với mục 4.3 của proposal. Nhờ vậy có thể dò theo bất kỳ con số nào để xem nó từ đâu ra.
- Những chỗ ghi **"Đề xuất, chờ nhóm chốt"** là quy tắc mà file này phải giả định để tính được, nhưng proposal chưa quy định. Danh sách đầy đủ ở mục 13.
- Muốn biết các bảng được tạo ra ở bước nào của nested CV, xem [nested_cv_diagram.md](nested_cv_diagram.md), mục 6 và 7.

---

## 1. Bảng A · macro-F1 gộp 254 ca

Mỗi ô là macro-F1 tính trên **254 dự đoán** của một repeat, tức là ghép 5 outer test lại. Cột cuối là mean ± SD qua 3 repeat.

| Pipeline | Vai trò | R1 | R2 | R3 | **Mean ± SD** |
| --- | --- | --- | --- | --- | --- |
| P01 DUMMY · most_frequent | Sàn | 0,097 | 0,097 | 0,097 | 0,097 ± 0,000 |
| P01 DUMMY · stratified | Sàn | 0,161 | 0,172 | 0,166 | 0,166 ± 0,006 |
| P02 R1-REF | Tham chiếu Round 1 | 0,768 | 0,759 | 0,789 | 0,772 ± 0,015 |
| P03 SVM-BAL | Ablation | 0,781 | 0,783 | 0,776 | 0,780 ± 0,004 |
| P04 SVM-BAL-K | Ablation | 0,785 | 0,787 | 0,786 | 0,786 ± 0,001 |
| P05 SVM-BAL-MAD | Ablation | 0,775 | 0,785 | 0,784 | 0,781 ± 0,006 |
| **P06 LR-L2-BAL** | Ứng viên | **0,792** | 0,805 | 0,804 | 0,800 ± 0,007 |
| P07 LR-EN-BAL | Ứng viên chính | 0,802 | 0,812 | 0,807 | **0,807 ± 0,005** (cao nhất) |
| P08 LR-L2-PRIOR | Ablation | 0,803 | 0,789 | 0,802 | 0,798 ± 0,008 |
| P09 LR-L2-ANOVA | Ứng viên | 0,801 | 0,796 | 0,809 | 0,802 ± 0,007 |
| P10 LR-L2-ANOVA-SMOTE | Đối chứng âm | 0,787 | 0,792 | 0,794 | 0,791 ± 0,004 |
| P11 PAM | Baseline omics | 0,763 | 0,756 | 0,761 | 0,760 ± 0,004 |
| P12 RF-BAL | Baseline phi tuyến | 0,743 | 0,730 | 0,739 | 0,737 ± 0,007 |
| P13 KNN | Baseline đơn giản | 0,713 | 0,710 | 0,710 | 0,711 ± 0,002 |

**Cách đọc:**

- **P01** có hai biến thể, đều là sàn. Biến thể most_frequent luôn đoán LMS. Biến thể stratified đoán ngẫu nhiên theo tỉ lệ lớp, nên điểm dao động nhẹ giữa các repeat. Pipeline nào không vượt xa khoảng 0,10–0,17 thì gần như chưa học được gì.
- **P02** là bài kiểm tra engine mới. Mean phải ra đúng 0,772 như Round 1. Nếu lệch thì engine có lỗi, và phải sửa trước khi đọc tiếp.
- **SD** ở đây chỉ phản ánh việc chia dữ liệu khác nhau giữa 3 repeat. Đó **không** phải khoảng tin cậy, vì 3 repeat dùng lại cùng 254 bệnh nhân.
- Bảng này **không** được dùng để tuyên bố "P07 thắng, đạt 0,807". Chọn dòng cao nhất rồi báo cáo chính số đó là con số lạc quan (xem mục 5).

---

## 2. Bảng A2 · metric phụ của mọi pipeline

BA (balanced accuracy) và MCC là mean ± SD qua 3 repeat, tính trên 254 dự đoán gộp như Bảng A. Recall MFS và MPNST lấy từ **repeat 1**, kèm khoảng tin cậy 95% Wilson.

| Pipeline | BA | MCC | Recall MFS (R1) | Recall MPNST (R1) |
| --- | --- | --- | --- | --- |
| P01 most_frequent | 0,167 ± 0,000 | 0,000 ± 0,000 | 0/25 = 0,000 (0,000–0,133) | 0/9 = 0,000 (0,000–0,299) |
| P01 stratified | 0,170 ± 0,011 | −0,002 ± 0,007 | 2/25 = 0,080 (0,022–0,250) | 0/9 = 0,000 (0,000–0,299) |
| P02 R1-REF | 0,761 ± 0,013 | 0,750 ± 0,016 | 14/25 = 0,560 (0,371–0,733) | 7/9 = 0,778 (0,453–0,937) |
| P03 SVM-BAL | 0,775 ± 0,008 | 0,759 ± 0,009 | 15/25 = 0,600 (0,407–0,766) | 5/9 = 0,556 (0,267–0,811) |
| P04 SVM-BAL-K | 0,774 ± 0,001 | 0,762 ± 0,005 | 14/25 = 0,560 (0,371–0,733) | 5/9 = 0,556 (0,267–0,811) |
| P05 SVM-BAL-MAD | 0,768 ± 0,010 | 0,755 ± 0,007 | 14/25 = 0,560 (0,371–0,733) | 5/9 = 0,556 (0,267–0,811) |
| **P06 LR-L2-BAL** | 0,791 ± 0,011 | 0,777 ± 0,008 | 15/25 = 0,600 (0,407–0,766) | 6/9 = 0,667 (0,354–0,879) |
| P07 LR-EN-BAL | 0,796 ± 0,009 | 0,784 ± 0,006 | 14/25 = 0,560 (0,371–0,733) | 6/9 = 0,667 (0,354–0,879) |
| P08 LR-L2-PRIOR | 0,786 ± 0,010 | 0,769 ± 0,013 | 14/25 = 0,560 (0,371–0,733) | 6/9 = 0,667 (0,354–0,879) |
| P09 LR-L2-ANOVA | 0,793 ± 0,009 | 0,771 ± 0,004 | 16/25 = 0,640 (0,445–0,798) | 7/9 = 0,778 (0,453–0,937) |
| P10 LR-L2-ANOVA-SMOTE | 0,781 ± 0,006 | 0,769 ± 0,005 | 16/25 = 0,640 (0,445–0,798) | 5/9 = 0,556 (0,267–0,811) |
| P11 PAM | 0,744 ± 0,002 | 0,737 ± 0,005 | 14/25 = 0,560 (0,371–0,733) | 6/9 = 0,667 (0,354–0,879) |
| P12 RF-BAL | 0,727 ± 0,005 | 0,715 ± 0,004 | 13/25 = 0,520 (0,335–0,700) | 5/9 = 0,556 (0,267–0,811) |
| P13 KNN | 0,699 ± 0,007 | 0,683 ± 0,006 | 9/25 = 0,360 (0,202–0,555) | 4/9 = 0,444 (0,189–0,733) |

**Cách đọc:**

- **BA và MCC xếp hạng gần giống macro-F1.** Nếu một pipeline có macro-F1 cao nhưng BA thấp hẳn, nó đang đánh đổi recall của lớp nhỏ để lấy precision. Đó là dấu hiệu cần xem confusion matrix của nó.
- **Recall MPNST không phân biệt được các pipeline.** P02 đúng 7/9 còn P06 đúng 6/9, nhưng hai khoảng tin cậy (0,45–0,94 và 0,35–0,88) chồng lên nhau gần hết. Với 9 ca, chênh 1 ca là chuyện ngẫu nhiên. Vì vậy protocol **cấm** chọn pipeline theo recall của một lớp (ràng buộc L9).
- **Đề xuất, chờ nhóm chốt:** proposal yêu cầu "recall MFS/MPNST có Wilson CI" nhưng không nói tính trên một repeat hay gộp 3 repeat. File này dùng repeat 1, vì gộp 3 repeat sẽ đếm mỗi bệnh nhân 3 lần và làm CI hẹp một cách giả tạo (xem mục 8).

---

## 3. Bảng B · macro-F1 theo từng outer fold

Mỗi ô là macro-F1 trên ≈51 ca outer test của **một** outer fold. Mỗi pipeline có 15 ô.

| Pipeline | R1·F1 | R1·F2 | R1·F3 | R1·F4 | R1·F5 | R2·F1 | R2·F2 | R2·F3 | R2·F4 | R2·F5 | R3·F1 | R3·F2 | R3·F3 | R3·F4 | R3·F5 | TB 15 fold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P01 mf | 0,097 | 0,097 | 0,097 | 0,097 | 0,097 | 0,097 | 0,097 | 0,097 | 0,097 | 0,097 | 0,097 | 0,097 | 0,097 | 0,097 | 0,097 | 0,097 |
| P01 strat | 0,142 | 0,173 | 0,109 | 0,208 | 0,185 | 0,157 | 0,157 | 0,175 | 0,158 | 0,159 | 0,188 | 0,181 | 0,164 | 0,163 | 0,171 | 0,166 |
| P02 | 0,755 | 0,767 | 0,793 | 0,722 | 0,758 | 0,756 | 0,749 | 0,754 | 0,712 | 0,778 | 0,799 | 0,797 | 0,750 | 0,817 | 0,737 | 0,763 |
| P03 | 0,756 | 0,797 | 0,801 | 0,741 | 0,765 | 0,787 | 0,756 | 0,797 | 0,740 | 0,790 | 0,782 | 0,757 | 0,739 | 0,804 | 0,753 | 0,771 |
| P04 | 0,753 | 0,779 | 0,822 | 0,737 | 0,789 | 0,793 | 0,744 | 0,802 | 0,741 | 0,810 | 0,789 | 0,782 | 0,741 | 0,824 | 0,748 | 0,777 |
| P05 | 0,756 | 0,784 | 0,800 | 0,725 | 0,764 | 0,790 | 0,759 | 0,795 | 0,747 | 0,788 | 0,785 | 0,772 | 0,730 | 0,821 | 0,767 | 0,772 |
| P06 | 0,757 | 0,806 | 0,818 | 0,752 | 0,781 | 0,797 | 0,777 | 0,800 | 0,778 | 0,828 | 0,809 | 0,795 | 0,764 | 0,831 | 0,775 | 0,791 |
| P07 | 0,777 | 0,811 | 0,841 | 0,747 | 0,789 | 0,815 | 0,785 | 0,829 | 0,763 | 0,823 | 0,808 | 0,790 | 0,760 | 0,861 | 0,771 | 0,798 |
| P08 | 0,768 | 0,803 | 0,841 | 0,747 | 0,812 | 0,781 | 0,769 | 0,793 | 0,758 | 0,799 | 0,806 | 0,800 | 0,722 | 0,848 | 0,789 | 0,789 |
| P09 | 0,776 | 0,801 | 0,827 | 0,754 | 0,801 | 0,790 | 0,771 | 0,804 | 0,760 | 0,810 | 0,803 | 0,810 | 0,766 | 0,860 | 0,761 | 0,793 |
| P10 | 0,777 | 0,812 | 0,813 | 0,720 | 0,768 | 0,799 | 0,766 | 0,812 | 0,751 | 0,787 | 0,798 | 0,788 | 0,740 | 0,840 | 0,759 | 0,782 |
| P11 | 0,753 | 0,735 | 0,797 | 0,708 | 0,777 | 0,764 | 0,731 | 0,765 | 0,698 | 0,777 | 0,768 | 0,759 | 0,711 | 0,803 | 0,719 | 0,751 |
| P12 | 0,753 | 0,744 | 0,757 | 0,674 | 0,742 | 0,712 | 0,710 | 0,739 | 0,689 | 0,755 | 0,741 | 0,728 | 0,691 | 0,791 | 0,698 | 0,728 |
| P13 | 0,705 | 0,725 | 0,744 | 0,634 | 0,712 | 0,696 | 0,688 | 0,732 | 0,675 | 0,714 | 0,729 | 0,697 | 0,682 | 0,748 | 0,649 | 0,702 |

**Cách đọc:**

- **Đọc theo cột** thấy có fold "khó" với mọi pipeline. Ví dụ R1·F4 thấp ở tất cả các dòng, còn R3·F4 cao ở tất cả. Độ khó do cách chia này là lý do kiểm định phải **so theo cặp, cùng fold** (lấy hiệu từng cột), thay vì so hai trung bình.
- **Cột "TB 15 fold" thấp hơn mean ở Bảng A** khoảng 0,01. Điều này bình thường: mỗi fold chỉ có 1–2 ca MPNST, nên F1 của lớp hiếm trên một fold dễ rơi về 0 và kéo macro-F1 xuống. Vì vậy điểm chính luôn lấy từ Bảng A, còn Bảng B **chỉ** dùng cho kiểm định.

---

## 4. Bảng D · tham số được chọn ở mỗi outer fold

Mỗi ô là g\*, tức ứng viên grid có điểm inner cao nhất của pipeline đó ở outer fold đó. Ký hiệu: P04, P09, P10 ghi `k · C`; P07 ghi `l1_ratio · C`; P08 ghi `C · α`; P12 ghi `max_features · min_samples_leaf`; P13 ghi `k ANOVA · số láng giềng`.

| Pipeline | R1·F1 | R1·F2 | R1·F3 | R1·F4 | R1·F5 | R2·F1 | R2·F2 | R2·F3 | R2·F4 | R2·F5 | R3·F1 | R3·F2 | R3·F3 | R3·F4 | R3·F5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P01 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| P02 | C 1 | C 0,1 | C 0,1 | C 0,1 | C 0,1 | C 0,1 | C 1 | C 0,1 | C 0,1 | C 1 | C 1 | C 1 | C 0,1 | C 0,1 | C 1 |
| P03 | C 10 | C 1 | C 0,1 | C 1 | C 0,1 | C 0,1 | C 0,1 | C 0,1 | C 0,1 | C 0,1 | C 1 | C 0,01 | C 0,1 | C 0,01 | C 0,1 |
| P04 | 500 · 1 | 150 · 0,1 | 1000 · 0,1 | 500 · 0,01 | 1000 · 0,1 | 500 · 1 | 1000 · 1 | 1000 · 0,1 | 1000 · 10 | 2000 · 0,1 | 500 · 0,1 | 1000 · 0,1 | 150 · 1 | 1000 · 0,1 | 500 · 1 |
| P05 | C 1 | C 0,1 | C 1 | C 0,01 | C 0,01 | C 0,1 | C 0,1 | C 1 | C 1 | C 1 | C 1 | C 0,1 | C 1 | C 0,1 | C 1 |
| P06 | C 0,1 | C 0,1 | C 0,01 | C 0,01 | C 0,01 | C 0,1 | C 0,1 | C 0,1 | C 0,01 | C 0,01 | C 0,01 | C 0,01 | C 0,1 | C 0,1 | C 1 |
| P07 | 0,5 · 0,1 | 0,9 · 0,1 | 0,5 · 1 | 0,5 · 0,1 | 0,1 · 0,1 | 0,1 · 1 | 0,1 · 1 | 0,5 · 0,01 | 0,5 · 0,1 | 0,9 · 1 | 0,1 · 0,01 | 0,5 · 1 | 0,5 · 0,1 | 0,5 · 0,1 | 0,1 · 0,1 |
| P08 | 0,1 · α 0 | 0,01 · α 0,5 | 0,1 · α 0,5 | 0,1 · α 0,5 | 0,01 · α 0 | 1 · α 1 | 1 · α 0 | 0,1 · α 0,5 | 0,01 · α 0,5 | 0,1 · α 1 | 0,01 · α 0,5 | 0,1 · α 0 | 0,1 · α 0 | 1 · α 0 | 0,1 · α 0,5 |
| P09 | 500 · 0,01 | 500 · 1 | 1000 · 0,01 | 1000 · 0,1 | 2000 · 0,1 | 1000 · 0,1 | 1000 · 0,1 | 2000 · 0,01 | 2000 · 0,01 | 500 · 0,1 | 2000 · 0,1 | 2000 · 0,01 | 1000 · 1 | 1000 · 1 | 2000 · 0,1 |
| P10 | 500 · 1 | 2000 · 0,1 | 1000 · 0,1 | 2000 · 0,1 | 1000 · 0,1 | 1000 · 0,01 | 1000 · 1 | 1000 · 0,01 | 1000 · 1 | 1000 · 1 | 2000 · 0,1 | 500 · 0,01 | 2000 · 0,1 | 2000 · 0,1 | 1000 · 0,1 |
| P11 | shrink 1 | shrink 1 | shrink 1 | shrink 4 | shrink 0,5 | shrink 2 | shrink 0,5 | shrink 2 | shrink 1 | shrink 2 | shrink 1 | shrink 1 | shrink 1 | shrink 1 | shrink 1 |
| P12 | sqrt · 1 | 0,01 · 1 | 0,01 · 3 | sqrt · 1 | sqrt · 3 | sqrt · 1 | sqrt · 1 | sqrt · 1 | sqrt · 1 | sqrt · 1 | 0,01 · 3 | sqrt · 1 | 0,01 · 1 | sqrt · 3 | sqrt · 1 |
| P13 | 500 · 7 | 500 · 5 | 100 · 5 | 100 · 5 | 500 · 5 | 500 · 7 | 100 · 5 | 500 · 3 | 100 · 3 | 100 · 7 | 500 · 5 | 500 · 5 | 100 · 5 | 100 · 5 | 100 · 5 |

**Cách đọc:**

- **g\* đổi theo fold là bình thường.** Đó là lý do điểm ở Bảng A thuộc về cả quy trình "pipeline kèm tự tune", không thuộc về một bộ tham số cố định. Hàng P07 ở repeat 1 chính là ví dụ trong mục 6.1 của [nested_cv_diagram.md](nested_cv_diagram.md).
- **Ổn định:** P06 gần như luôn chọn C = 0,01 hoặc 0,1, nghĩa là mô hình cần regularization khá mạnh. P08 chọn α = 0 ở 6/15 fold, tức là ngưỡng hiệu chỉnh thường không được dùng. Điều này khớp với kết quả ablation P06 → P08 ở mục 6.
- Bảng này cũng là chỗ để kiểm toán META-SELECT: cặp thắng ở mục 5 phải trùng với g\* của pipeline đó ở cùng fold.

**Chạm biên grid.** Ở vòng B, grid đã đóng băng, nên việc chạm biên chỉ được **báo cáo**, không được dẫn tới sửa grid (quy tắc mở rộng biên chỉ áp dụng ở vòng A). Repeat 1 của vòng B dùng cùng split, seed và config với vòng A, nên g\* ở R1 trùng với vòng A. Vì vậy R1 không thể có pipeline nào chạm biên ở ≥3/5 fold: nếu có, vòng A đã mở rộng grid trước khi đóng băng. Các trường hợp chạm biên chỉ có thể xuất hiện ở R2 và R3. Các trường hợp g\* nằm ở cùng một biên ở ≥3/5 fold trong một repeat:

| Pipeline | Tham số | Repeat | Biên | Số fold | Ý nghĩa |
| --- | --- | --- | --- | --- | --- |
| P07 | C | R2 | trên (C = 1) | 3/5 | Chỉ ở một repeat; R1 và R3 không lặp lại |
| P08 | α | R3 | dưới (α = 0) | 3/5 | α = 0 là "không hiệu chỉnh ngưỡng", một giới hạn tự nhiên chứ không phải grid quá hẹp |
| P09 | k | R3 | trên (k = 2000) | 3/5 | Chỉ ở một repeat; R1 và R2 không lặp lại |
| P10 | k | R3 | trên (k = 2000) | 3/5 | Cùng hướng với P09 ở cùng repeat (hai pipeline có chung bước ANOVA). Có thể k lớn hơn sẽ tốt hơn. Ghi vào phần hạn chế và để dành cho vòng sau |

Ba trường hợp không được tính. P13 tune k ANOVA trên grid chỉ có 2 giá trị, nên giá trị nào cũng là biên và quy tắc không có nghĩa. `max_features` của P12 cũng chỉ có 2 giá trị, nên tương tự. P12 thường chọn `min_samples_leaf = 1`, nhưng 1 là giá trị nhỏ nhất có thể có nên không có gì để mở rộng.

---

## 5. Câu 1 · META-SELECT: con số chính của dự án

Trong mỗi outer fold, chọn cặp (pipeline, tham số) có **điểm inner** cao nhất trong P02–P13 (không gồm P01), rồi lấy dự đoán outer của cặp đó. Điểm outer không tham gia vào việc chọn.

| Outer fold | Pipeline thắng (theo inner) | Điểm inner | Điểm outer của nó (từ Bảng B) |
| --- | --- | --- | --- |
| R1·F1 | P07 LR-EN-BAL | 0,790 | 0,777 |
| R1·F2 | P06 LR-L2-BAL | 0,811 | 0,806 |
| R1·F3 | P07 LR-EN-BAL | 0,798 | 0,841 |
| R1·F4 | P09 LR-L2-ANOVA | 0,806 | 0,754 |
| R1·F5 | P07 LR-EN-BAL | 0,815 | 0,789 |
| R2·F1 | P08 LR-L2-PRIOR | 0,801 | 0,781 |
| R2·F2 | P07 LR-EN-BAL | 0,809 | 0,785 |
| R2·F3 | P06 LR-L2-BAL | 0,797 | 0,800 |
| R2·F4 | P09 LR-L2-ANOVA | 0,812 | 0,760 |
| R2·F5 | P07 LR-EN-BAL | 0,804 | 0,823 |
| R3·F1 | P04 SVM-BAL-K | 0,794 | 0,789 |
| R3·F2 | P06 LR-L2-BAL | 0,808 | 0,795 |
| R3·F3 | P09 LR-L2-ANOVA | 0,800 | 0,766 |
| R3·F4 | P07 LR-EN-BAL | 0,817 | 0,861 |
| R3·F5 | P08 LR-L2-PRIOR | 0,805 | 0,789 |

**Tần suất thắng qua 15 fold:** P07 thắng 6 lần, P06 3, P09 3, P08 2, P04 1.

**Kết quả META-SELECT** (macro-F1 gộp 254 ca của các dự đoán được chọn): R1 0,802 · R2 0,799 · R3 0,809 → **0,803 ± 0,005**.

**Cách đọc:**

- **0,803** là con số dự án được phép báo cáo là "hiệu năng của quy trình". Nó thấp hơn 0,807 của P07 trong Bảng A. Khoảng chênh đó chính là phần lạc quan sẽ xuất hiện nếu nhóm lấy dòng cao nhất của Bảng A rồi báo cáo luôn.
- **Tần suất thắng** cho biết việc chọn có ổn định không. Ở đây pipeline thắng hầu như luôn thuộc họ LR (14/15 fold), nhưng không có một cấu hình LR nào áp đảo. Điều đó khớp với kết quả ở mục 6: các biến thể LR không phân biệt được với nhau.
- Điểm inner và điểm outer của cùng một fold thường lệch nhau, ví dụ R1·F4 có inner 0,806 nhưng outer chỉ 0,754. Inner chỉ dùng để **chọn**, outer chỉ dùng để **chấm**.

---

## 6. Câu 2 · Ablation: stage nào thật sự quan trọng?

### 6.1 Cách tính, với một cặp làm ví dụ (P05 → P06, đổi SVM sang LR L2)

1. **Lấy hiệu theo từng fold** từ Bảng B: d = P06 − P05 cho 15 cột.
   - d = 0,001 · 0,022 · 0,018 · 0,027 · 0,017 · 0,007 · 0,018 · 0,005 · 0,031 · 0,040 · 0,024 · 0,023 · 0,034 · 0,010 · 0,008
   - Mean d = **+0,019**, SD = 0,0113.
2. **Bayesian correlated t-test** (Benavoli 2017). Các fold dùng chung bệnh nhân nên không độc lập. Phép kiểm định bù cho điều này bằng cách nới rộng độ bất định: scale = √(1/15 + ρ/(1−ρ)) × SD, với ρ/(1−ρ) = n_test/n_train ≈ 0,25. Hệ số 1/15 + 0,25 ≈ 0,317 chính là hiệu chỉnh phương sai của Nadeau & Bengio, nên không cần chạy thêm corrected t-test. Ở đây scale = √0,317 × 0,0113 ≈ 0,0064. Kết quả là phân phối t (df = 14) cho "mức hơn thật sự", rồi chia nó thành ba vùng quanh **ROPE = ±0,01** (khoảng chênh mà nhóm coi là không đáng kể trong thực tế):

   ```text
        P06 kém hơn       |    tương đương     |     P06 tốt hơn
   ◄──────────────────────┼────────────────────┼──────────────────────►
                        −0,01                +0,01
             0,00                 0,09                  0,91
   ```

3. **Đọc:** P(P06 tốt hơn quá ROPE) = 0,91. Con số này chưa đạt ngưỡng 0,95, nên kết luận là "**nghiêng về LR tốt hơn, chưa đủ chắc**".

**Quy tắc đọc ba xác suất (đề xuất, chờ nhóm chốt):** nếu một trong ba xác suất ≥ 0,95 thì kết luận theo vùng đó. Nếu không có xác suất nào đạt 0,95 thì ghi "chưa kết luận được", kèm hướng nghiêng. Proposal mục 5.2 mới yêu cầu báo cáo ba xác suất, chưa đăng ký ngưỡng để kết luận. Ngưỡng 0,95 ở đây mượn từ quy tắc nhóm tương đương ở mục 5.3 của proposal.

Kết quả là **xác suất**, không phải p-value, nên không có hiệu chỉnh Holm. Số phép so sánh được giữ nhỏ bằng cách chỉ kiểm định các cặp đã đăng ký trước.

### 6.2 Toàn bộ 11 cặp đã đăng ký trước, ROPE 0,01

d = (pipeline sau mũi tên) − (pipeline trước mũi tên). "Kém / Tương đương / Tốt hơn" là ba xác suất Bayesian, nói về pipeline sau mũi tên.

| Cặp | Thay đổi | Mean d | Kém hơn | Tương đương | Tốt hơn | Kết luận |
| --- | --- | --- | --- | --- | --- | --- |
| P02 → P03 | S4: + class weight | +0,008 | 0,08 | 0,48 | 0,44 | Chưa kết luận được |
| P03 → P04 | S3: tune k 150–2000 | +0,006 | 0,03 | 0,67 | 0,30 | Chưa kết luận, nghiêng tương đương |
| P04 → P05 | S3: bỏ ANOVA, dùng MAD 5000 | −0,005 | 0,24 | 0,73 | 0,03 | Chưa kết luận; gần như chắc **không tốt hơn** |
| P05 → P06 | S5: SVM → LR L2 | +0,019 | 0,00 | 0,09 | **0,91** | Nghiêng LR tốt hơn, chưa đủ chắc |
| P06 → P07 | S5: L2 → elastic-net | +0,007 | 0,03 | 0,63 | 0,35 | Chưa kết luận được |
| P06 → P08 | S4: class weight → ngưỡng α | −0,002 | 0,25 | 0,61 | 0,15 | Chưa kết luận được |
| P06 → P09 | S3: + ANOVA | +0,002 | 0,08 | 0,75 | 0,16 | Chưa kết luận, nghiêng tương đương |
| P09 → P10 | S4: class weight → SMOTE | −0,011 | 0,54 | 0,44 | 0,01 | SMOTE gần như chắc **không giúp** |
| P06 → P11 | Họ khác: PAM | −0,040 | **0,99** | 0,01 | 0,00 | **P06 tốt hơn PAM** |
| P06 → P12 | Họ khác: RF | −0,063 | **1,00** | 0,00 | 0,00 | **P06 tốt hơn RF** |
| P09 → P13 | Họ khác: kNN | −0,091 | **1,00** | 0,00 | 0,00 | **P09 tốt hơn kNN** |

**Cách đọc:**

- Các thay đổi **lớn** (đổi sang PAM, RF, kNN) cho kết luận rõ ràng.
- Các thay đổi **nhỏ** trong cùng họ (class weight, k, ANOVA, elastic-net, ngưỡng α) đều "chưa kết luận được". Proposal đã ghi trước điều này ở mục 5.2: với 15 fold, chênh lệch dưới khoảng 0,03–0,05 nhiều khả năng không có ý nghĩa. "Không phân biệt được" là một kết quả hợp lệ và phải được báo cáo như vậy.
- Muốn khẳng định "hai pipeline **tương đương**" thì cột "Tương đương" phải ≥ 0,95. Với ROPE 0,01 chưa cặp nào đạt, nên chỉ được viết "chưa kết luận được", không được viết "không khác nhau".

### 6.3 Cùng 11 cặp, với ROPE 0,02

Proposal mục 5.2 chỉ quy định ROPE ±0,01. File này thêm ROPE 0,02 như một phân tích độ nhạy (**đề xuất, chờ nhóm chốt**, xem mục 13) để cho thấy cỡ ROPE ảnh hưởng tới kết luận ra sao. ROPE rộng hơn nghĩa là nhóm coi chênh lệch tới 0,02 là không đáng kể.

| Cặp | Kém hơn | Tương đương | Tốt hơn | Kết luận | Đổi so với ROPE 0,01? |
| --- | --- | --- | --- | --- | --- |
| P02 → P03 | 0,02 | 0,81 | 0,17 | Chưa kết luận, nghiêng tương đương | Không |
| P03 → P04 | 0,00 | **0,96** | 0,04 | **Tương đương** | **Có** |
| P04 → P05 | 0,03 | **0,97** | 0,00 | **Tương đương** | **Có** |
| P05 → P06 | 0,00 | 0,56 | 0,44 | Chưa kết luận được | Yếu hơn |
| P06 → P07 | 0,00 | 0,94 | 0,06 | Chưa kết luận, nghiêng tương đương | Không |
| P06 → P08 | 0,07 | 0,90 | 0,03 | Chưa kết luận, nghiêng tương đương | Không |
| P06 → P09 | 0,01 | **0,97** | 0,02 | **Tương đương** | **Có** |
| P09 → P10 | 0,15 | 0,85 | 0,00 | Chưa kết luận; SMOTE không tốt hơn | Không |
| P06 → P11 | 0,94 | 0,06 | 0,00 | Chưa kết luận, nghiêng P06 tốt hơn | **Có** (mất kết luận) |
| P06 → P12 | **1,00** | 0,00 | 0,00 | **P06 tốt hơn RF** | Không |
| P09 → P13 | **1,00** | 0,00 | 0,00 | **P09 tốt hơn kNN** | Không |

**Cách đọc:**

- ROPE rộng hơn làm dễ kết luận "tương đương" hơn (3 cặp mới đạt), nhưng lại khó kết luận "tốt hơn" hơn (P06 → P11 mất kết luận).
- Cỡ ROPE vì vậy phải được **chốt trước** khi mở niêm phong outer. Nếu chọn sau khi đã thấy bảng này, nhóm có thể vô tình chọn mức ROPE cho ra kết luận mình muốn. Mục 7 cho thấy ROPE còn làm đổi cả pipeline được chọn.

---

## 7. Câu 3 · Chọn pipeline mang sang app

1. **T** = pipeline có mean cao nhất trong Bảng A, ở đây là **P07** (0,807). P01 không được xét vì không được phép làm winner.
2. So T với từng pipeline X bằng Bayesian t-test trên Bảng B (d = T − X). X **bị loại** nếu P(T tốt hơn X quá ROPE) ≥ 0,95. Ngược lại thì X nằm trong **nhóm tương đương** với T.

| X | Mean d (T − X) | P(T tốt hơn X quá ROPE) | Kết quả với ROPE 0,01 | P(…) với ROPE 0,02 | Kết quả với ROPE 0,02 |
| --- | --- | --- | --- | --- | --- |
| P02 | +0,035 | 0,974 | Loại | 0,888 | Trong nhóm |
| P03 | +0,027 | 0,989 | Loại | 0,845 | Trong nhóm |
| P04 | +0,021 | 0,955 | Loại (sát ngưỡng) | 0,568 | Trong nhóm |
| P05 | +0,026 | 0,995 | Loại | 0,850 | Trong nhóm |
| **P06** | +0,007 | 0,347 | **Trong nhóm** | 0,059 | Trong nhóm |
| P08 | +0,009 | 0,460 | Trong nhóm | 0,154 | Trong nhóm |
| P09 | +0,005 | 0,252 | Trong nhóm | 0,028 | Trong nhóm |
| P10 | +0,016 | 0,836 | Trong nhóm | 0,255 | Trong nhóm |
| P11 | +0,047 | 0,999 | Loại | 0,994 | Loại |
| P12 | +0,070 | 1,000 | Loại | 1,000 | Loại |
| P13 | +0,096 | 1,000 | Loại | 1,000 | Loại |

3. **Nhóm tương đương (ROPE 0,01):** P07, P06, P08, P09, P10.
4. Chọn pipeline **đơn giản nhất** trong nhóm theo thứ tự đã khai báo trước (P11 < P03 < P02 < P05 < P04 < **P06** < P08 < P09 < P07 < P10 < P13 < P12). Kết quả là **P06 LR-L2-BAL**.

**Cách đọc:**

- Pipeline được chọn **không phải** pipeline có điểm cao nhất, và đó là chủ ý. P07 chỉ hơn P06 0,007 và không phân biệt được với P06, trong khi P06 ít tham số hơn (không có thành phần L1, 5 thay vì 9 ứng viên grid) và theo bảng runtime ở mục 10 thì chạy nhanh hơn khoảng 16 lần.
- Khi báo cáo hiệu năng của P06, dùng **con số META-SELECT 0,803 ± 0,005**, không dùng 0,800 của riêng P06 và không dùng 0,807 của P07.
- **Cỡ ROPE thay đổi kết quả.** Với ROPE 0,02, nhóm tương đương mở rộng thêm cả P02–P05, và pipeline được chọn sẽ là **P03 SVM-BAL**. Đây là lý do file này đề xuất báo cáo cả hai mức, và cùng lý do với mục 6.3: ROPE phải được chốt trước.

---

## 8. Confusion matrix và recall theo lớp kèm Wilson CI

Pipeline được chọn là **P06**, repeat 1 của vòng B, 254 dự đoán. Hàng là nhãn thật, cột là nhãn dự đoán.

| Thật \ Dự đoán | LMS | DDLPS | UPS | MFS | SS | MPNST | **Tổng** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **LMS** | **96** | 2 | 4 | 1 | 0 | 1 | 104 |
| **DDLPS** | 1 | **51** | 4 | 1 | 0 | 0 | 57 |
| **UPS** | 5 | 3 | **34** | 7 | 0 | 0 | 49 |
| **MFS** | 1 | 1 | 8 | **15** | 0 | 0 | 25 |
| **SS** | 0 | 0 | 0 | 0 | **9** | 1 | 10 |
| **MPNST** | 1 | 0 | 1 | 1 | 0 | **6** | 9 |
| **Tổng dự đoán** | 104 | 57 | 51 | 25 | 9 | 8 | 254 |

| Lớp | Số ca | Đúng | Precision | Recall | F1 | **Recall 95% Wilson CI** |
| --- | --- | --- | --- | --- | --- | --- |
| LMS | 104 | 96 | 0,923 | 0,923 | 0,923 | 0,856 – 0,961 |
| DDLPS | 57 | 51 | 0,895 | 0,895 | 0,895 | 0,789 – 0,951 |
| UPS | 49 | 34 | 0,667 | 0,694 | 0,680 | 0,555 – 0,805 |
| MFS | 25 | 15 | 0,600 | 0,600 | 0,600 | 0,407 – 0,766 |
| SS | 10 | 9 | 1,000 | 0,900 | 0,947 | 0,596 – 0,982 |
| **MPNST** | **9** | **6** | 0,750 | **0,667** | 0,706 | **0,354 – 0,879** |
| **Macro** | | | | 0,780 (= BA) | **0,792** | |

Multiclass MCC = 0,768. Macro-F1 0,792, BA 0,780 và MCC 0,768 đúng bằng các ô P06 · R1 ở Bảng A và Bảng A2, vì tất cả được tính từ cùng 254 dự đoán.

**Cách đọc:**

- **Lỗi tập trung ở UPS ↔ MFS:** có 7 ca UPS bị đoán là MFS và 8 ca MFS bị đoán là UPS. Đây là ranh giới sinh học đã biết (hai lớp này có thể là một phổ liên tục), và cũng là lý do có phân tích độ nhạy S-5CLASS ở mục 9. Ngoài ra, UPS bị lẫn với LMS (5 ca) và DDLPS (3 ca). Đây là những ca W5 cần audit theo MDM2/CDK4 và panel cơ trơn.
- **MPNST** đúng 6/9, nhưng khoảng tin cậy trải từ 0,35 đến 0,88. Với 9 ca, dữ liệu chỉ cho phép nói "recall ở đâu đó giữa khoảng 1/3 và gần 9/10". Đây là lý do protocol bắt báo cáo CI thay vì một con số trơn, và cấm tối ưu riêng cho MPNST.
- **Tại sao dùng Wilson** thay vì công thức p ± 1,96·SE thông thường: với n nhỏ và recall gần 0 hoặc 1, công thức thông thường cho khoảng tràn ra ngoài [0, 1] hoặc hẹp sai. Ví dụ SS (9/10) sẽ ra cận trên 1,086.
- **Đề xuất, chờ nhóm chốt: không cộng dồn 3 repeat thành 762 ca** để tính CI. Mỗi bệnh nhân sẽ bị đếm 3 lần, làm CI hẹp đi một cách giả tạo. File này báo cáo CI theo repeat 1. Proposal chỉ ghi "từ confusion matrix gộp" mà chưa nói rõ gộp ở mức nào.

---

## 9. Phân tích độ nhạy

Chạy cho pipeline được chọn (**P06**) và tham chiếu Round 1 (**P02**). Mỗi phân tích chạy **1 repeat**, nên so sánh với cột R1 của Bảng A.

**Đề xuất, chờ nhóm chốt:** proposal ghi "chỉ chạy cho winner, P02 và P06" nhưng không định nghĩa "winner". File này hiểu winner là pipeline được chọn ở Câu 3. Vì pipeline đó chính là P06, nên chỉ còn hai pipeline. Nếu winner nghĩa là pipeline có điểm cao nhất (T = P07), thì phải chạy thêm P07.

| Phân tích | Thay đổi so với main | Số lớp | P06 | P02 | Chênh so với main (P06 / P02) |
| --- | --- | --- | --- | --- | --- |
| **Main** (Bảng A, R1) | — | 6 | 0,792 | 0,768 | — |
| **S-TSS** | Outer fold nhóm theo nơi lấy mẫu (`StratifiedGroupKFold`), không có TSS nào nằm cả ở train lẫn test | 6 | 0,741 | 0,702 | −0,051 / −0,066 |
| **S-206** | Chỉ dùng 206 ca đã qua pathology review (Cell 2017) | 6 | 0,823 | 0,797 | +0,031 / +0,029 |
| **S-5CLASS** | Gộp MFS + UPS thành một lớp | 5 | 0,861 | 0,838 | Không so trực tiếp (khác số lớp) |

**Cách đọc:**

- **S-TSS** hỏi: mô hình có đang học "bệnh viện nào" thay vì "subtype nào" không? Cả hai pipeline đều giảm khoảng 0,05–0,07 khi bệnh viện ở outer test chưa từng xuất hiện trong train. Như vậy một phần hiệu năng ở main có thể đến từ tín hiệu nơi lấy mẫu, và phải ghi điều này trong phần hạn chế. Proposal mới chỉ nói "giảm mạnh" mà chưa định nghĩa bằng số, nên **nhóm cần chốt ngưỡng trước khi chạy**. Ngoài ra, chia theo nhóm làm các fold kém cân bằng lớp hơn, nên một phần mức giảm có thể đến từ việc đó.
- **S-206** hỏi: nhãn có nhiễu không? Điểm tăng khi chỉ dùng ca đã được review lại, nên có thể trong 48 ca còn lại có nhãn sai hoặc ca ranh giới. Điều này **không** có nghĩa mô hình tốt hơn: cohort khác và nhỏ hơn, nên chỉ so được về hướng thay đổi.
- **S-5CLASS** hỏi: bao nhiêu lỗi nằm ở ranh giới MFS/UPS? Macro-F1 với 5 lớp không so trực tiếp được với 6 lớp. Có thể kiểm tra chéo bằng confusion matrix ở mục 8: khối UPS + MFS có 34 + 7 + 8 + 15 = 64 trên 74 ca nằm trong khối, tức recall của lớp gộp khoảng 0,86. Mức tăng chủ yếu đến từ việc bỏ đi đúng loại lỗi đó.
- **Hai pipeline đổi theo cùng hướng** ở cả ba phân tích, nên kết luận "P06 nhỉnh hơn P02" vững khi đổi góc nhìn dữ liệu.

---

## 10. Runtime và số fit (vòng B)

Mỗi pipeline có 3 repeat × 5 outer fold × (4G + 1) fit. Thời gian dưới đây là giả lập cho một lõi CPU. Khi chạy thật, `run_manifest` phải ghi thông tin máy, vì runtime chỉ so được giữa các run trên **cùng một máy**.

Máy (giả lập): 8 lõi, chạy 1 lõi mỗi fit, Python 3.12, scikit-learn 1.7.2.

| Pipeline | G | Fit vòng B | Giây / fit | Thời gian vòng B (phút) |
| --- | --- | --- | --- | --- |
| P01 | 1 | 75 | 0,02 | < 0,1 |
| P02 | 5 | 315 | 0,44 | 2,3 |
| P03 | 5 | 315 | 0,46 | 2,4 |
| P04 | 20 | 1.215 | 0,52 | 10,5 |
| P05 | 5 | 315 | 0,55 | 2,9 |
| P06 | 5 | 315 | 1,40 | 7,3 |
| P07 | 9 | 555 | 12,6 | 116,5 |
| P08 | 15 | 915 | 1,45 | 22,1 |
| P09 | 15 | 915 | 1,62 | 24,7 |
| P10 | 15 | 915 | 2,10 | 32,0 |
| P11 | 5 | 315 | 0,28 | 1,5 |
| P12 | 4 | 255 | 3,30 | 14,0 |
| P13 | 8 | 495 | 0,31 | 2,6 |
| **Lõi P01–P13** | | **6.915** | | **≈ 239 phút ≈ 4,0 giờ** |

**Cách đọc:**

- Tổng 6.915 fit khớp với mục 4.3 của proposal. Cộng thêm 2.305 fit của vòng A (đã bỏ kết quả) thì cả quy trình là 9.220 fit.
- **P07 chiếm khoảng một nửa tổng thời gian** dù chỉ có 9 ứng viên grid, vì solver `saga` của elastic-net chậm. Đây là thông tin cần cho Câu 3: P07 không tốt hơn P06 một cách thuyết phục nhưng đắt hơn khoảng 16 lần.
- 4,0 giờ nằm trong khoảng ước tính 3–10,5 giờ của proposal. Nếu số thật vượt xa khoảng này, cần xem lại `max_iter` hoặc chạy song song theo ứng viên grid.

---

## 11. Kết quả này sẽ được viết trong báo cáo như thế nào (ví dụ)

Proposal không yêu cầu đoạn này. Nó chỉ minh hoạ cách các output ở trên được ghép thành văn bản.

> Quy trình chọn pipeline trong nested CV (META-SELECT) đạt macro-F1 0,803 ± 0,005 qua 3 repeat (dữ liệu giả lập). Họ LR được chọn ở 14/15 outer fold. Pipeline mang sang ứng dụng là LR-L2 có class weight (P06), là pipeline đơn giản nhất trong nhóm không phân biệt được với pipeline đứng đầu (ROPE ±0,01). Các biến thể trong họ LR (elastic-net, ngưỡng α, thêm ANOVA) không khác nhau một cách thuyết phục. LR có xu hướng tốt hơn SVM tuyến tính nhưng chưa đủ chắc (P = 0,91), còn LR vượt rõ PAM, random forest và kNN. SMOTE không cải thiện so với class weight. Recall MPNST là 6/9 (95% Wilson CI 0,35–0,88). Phần lớn lỗi nằm ở ranh giới UPS/MFS. Hiệu năng giảm 0,05 khi tách theo nơi lấy mẫu, cho thấy có một phần tín hiệu từ TSS.

Mọi con số trong đoạn trên đều giả lập. Khi có kết quả thật, chỉ cần thay số; cấu trúc câu và thứ tự trình bày giữ nguyên.

---

## 12. Output của protocol không nằm trong file này

File này chỉ minh hoạ các bảng **kết quả** của vòng B. Protocol còn sinh ra những output sau, nhưng chúng thuộc workstream khác hoặc là bằng chứng kiểm toán, không phải bảng kết quả:

| Output | Ai làm | Vì sao không có ở đây |
| --- | --- | --- |
| Báo cáo screening của vòng A | W4a–d | Kết quả vòng A bị bỏ, báo cáo này chỉ dùng để quyết định sửa hay đóng băng |
| Run folder: `predictions.csv`, `search_results`, `feature_details` (gene giữ lại theo fold), α của P08 theo fold, `run_manifest` | W1, W4 | Là bằng chứng để kiểm toán và là nguồn của các bảng trên, không phải bảng để đọc |
| Đối chiếu gene và trọng số với bảng marker; audit lỗi UPS/MFS theo MDM2/CDK4 và panel cơ trơn; độ ổn định gene Nogueira Φ | W5 | Thuộc chương phân tích lỗi, cần dữ liệu gene thật |
| Báo cáo khác biệt nhãn khi đối chiếu với 206 ca đã review; bảng chéo TSS × subtype | W3 | Là đầu vào của S-206 và S-TSS, làm trước khi chạy |
| Chạy xác nhận top 2–3 với outer seed mới | Tuỳ chọn (mục 5.3, bước 4) | Không bắt buộc. Nếu chạy, phải ghi rõ đây không phải validation độc lập |
| Mô hình cuối refit trên 254 ca và model card cho app | Sau phân tích (D11 trong [architecture.md](architecture.md)) | Thuộc giai đoạn đưa sang app |

---

## 13. Các giả định của file này, chờ nhóm chốt

Để tính được các bảng ở trên, file này phải giả định một số điểm mà proposal chưa quy định rõ. Nhóm nên chốt các điểm này **trước khi mở niêm phong outer**, rồi ghi vào proposal.

| # | Điểm cần chốt | File này đang giả định | Ảnh hưởng nếu chọn khác |
| --- | --- | --- | --- |
| 1 | Ngưỡng để kết luận một cặp ablation | Một xác suất ≥ 0,95 (mượn từ mục 5.3 của proposal) | Ngưỡng thấp hơn sẽ cho nhiều kết luận hơn, kể cả P05 → P06 |
| 2 | Wilson CI tính trên một repeat hay gộp 3 repeat | Repeat 1 | Gộp 3 repeat làm CI hẹp giả tạo, vì đếm mỗi bệnh nhân 3 lần |
| 3 | Recall MFS/MPNST có Wilson CI: báo cáo cho mọi pipeline hay chỉ pipeline được chọn | Mọi pipeline (Bảng A2) | Chỉ báo cáo cho pipeline được chọn thì gọn hơn nhưng mất phần so sánh |
| 4 | "Winner" trong phân tích độ nhạy | Pipeline được chọn ở Câu 3 (P06) | Nếu là T (P07) thì phải chạy độ nhạy thêm cho P07 |
| 5 | Ngưỡng "giảm mạnh" của S-TSS | Chưa có; file chỉ mô tả mức giảm | Không có ngưỡng thì không thể kết luận "mô hình đang học TSS" một cách khách quan |
| 6 | Có báo cáo thêm ROPE 0,02 không | Có, như phân tích độ nhạy; ROPE chính vẫn là 0,01 theo proposal mục 5.2 | Mục 6.3 và 7 cho thấy ROPE đổi cả kết luận ablation lẫn pipeline được chọn |
