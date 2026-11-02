# Báo cáo screening vòng A

Chỉ chứa thông tin kỹ thuật và điểm inner. Vòng A không dự đoán outer test, nên không có điểm outer nào để xem.

## 1. Trạng thái và runtime

| Pipeline | Member | Commit | Dev | Trạng thái | Fold | Fit | Giây/fit | Phút |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P01-MF | 1 | bf2c2ba20 | không | complete | 5/5 | 25 | 0,11 | 0,1 |
| P01-ST | 1 | bf2c2ba20 | không | complete | 5/5 | 25 | 0,10 | 0,1 |
| P02 | 1 | bf2c2ba20 | không | complete | 5/5 | 105 | 0,32 | 0,6 |
| P03 | 1 | bf2c2ba20 | không | complete | 5/5 | 105 | 0,31 | 0,6 |
| P04 | 1 | bf2c2ba20 | không | complete | 5/5 | 405 | 0,31 | 2,2 |
| P05 | 1 | bf2c2ba20 | không | complete | 5/5 | 105 | 0,38 | 0,7 |
| P06 | 2 | 26e8d1125 | không | complete | 5/5 | 105 | 1,20 | 0,7 |
| P07 | 2 | bf2c2ba20 | không | complete | 5/5 | 185 | 223,95 | 107,1 |
| P08 | 2 | 26e8d1125 | không | complete | 5/5 | 305 | 1,09 | 1,5 |
| P09 | 3 | bf2c2ba20 | không | complete | 5/5 | 305 | 0,30 | 1,6 |
| P10 | 3 | bf2c2ba20 | không | complete | 5/5 | 305 | 0,81 | 4,3 |
| P11 | 4 | bf2c2ba20 | không | complete | 5/5 | 105 | 0,19 | 0,4 |
| P12 | 4 | bf2c2ba20 | không | complete | 5/5 | 85 | 2,09 | 3,0 |
| P13 | 4 | bf2c2ba20 | không | complete | 5/5 | 165 | 0,17 | 0,5 |

## 2. Warning và hội tụ

| Pipeline | Tổng | Theo loại | n_iter lúc refit (max/giới hạn) | Ví dụ |
| --- | --- | --- | --- | --- |
| P01-MF | 0 | none | n/a |  |
| P01-ST | 0 | none | n/a |  |
| P02 | 0 | none | n/a |  |
| P03 | 0 | none | n/a |  |
| P04 | 0 | none | n/a |  |
| P05 | 0 | none | n/a |  |
| P06 | 0 | none | 197/5000 |  |
| P07 | 0 | none | 4375/10000 |  |
| P08 | 0 | none | 175/5000 |  |
| P09 | 0 | none | 183/5000 |  |
| P10 | 0 | none | 126/5000 |  |
| P11 | 0 | none | n/a |  |
| P12 | 0 | none | n/a |  |
| P13 | 0 | none | n/a |  |

## 3. Tham số được chọn (g*) và điểm inner

| Pipeline | Fold | g* | Inner macro-F1 |
| --- | --- | --- | --- |
| P01-MF | R1·F1 | {} | 0,097 |
| P01-MF | R1·F2 | {} | 0,098 |
| P01-MF | R1·F3 | {} | 0,097 |
| P01-MF | R1·F4 | {} | 0,097 |
| P01-MF | R1·F5 | {} | 0,096 |
| P01-ST | R1·F1 | {} | 0,153 |
| P01-ST | R1·F2 | {} | 0,159 |
| P01-ST | R1·F3 | {} | 0,157 |
| P01-ST | R1·F4 | {} | 0,138 |
| P01-ST | R1·F5 | {} | 0,153 |
| P02 | R1·F1 | {"model__C": 0.1} | 0,741 |
| P02 | R1·F2 | {"model__C": 0.1} | 0,774 |
| P02 | R1·F3 | {"model__C": 0.1} | 0,676 |
| P02 | R1·F4 | {"model__C": 0.1} | 0,772 |
| P02 | R1·F5 | {"model__C": 0.01} | 0,736 |
| P03 | R1·F1 | {"model__C": 0.01} | 0,743 |
| P03 | R1·F2 | {"model__C": 1} | 0,772 |
| P03 | R1·F3 | {"model__C": 0.01} | 0,712 |
| P03 | R1·F4 | {"model__C": 0.1} | 0,772 |
| P03 | R1·F5 | {"model__C": 0.1} | 0,726 |
| P04 | R1·F1 | {"model__C": 0.1, "select__k": 500} | 0,780 |
| P04 | R1·F2 | {"model__C": 1, "select__k": 150} | 0,772 |
| P04 | R1·F3 | {"model__C": 0.01, "select__k": 150} | 0,712 |
| P04 | R1·F4 | {"model__C": 0.1, "select__k": 150} | 0,772 |
| P04 | R1·F5 | {"model__C": 0.01, "select__k": 2000} | 0,765 |
| P05 | R1·F1 | {"model__C": 0.01} | 0,722 |
| P05 | R1·F2 | {"model__C": 0.01} | 0,738 |
| P05 | R1·F3 | {"model__C": 0.01} | 0,675 |
| P05 | R1·F4 | {"model__C": 0.01} | 0,698 |
| P05 | R1·F5 | {"model__C": 0.01} | 0,687 |
| P06 | R1·F1 | {"model__C": 10} | 0,737 |
| P06 | R1·F2 | {"model__C": 0.001} | 0,749 |
| P06 | R1·F3 | {"model__C": 0.01} | 0,683 |
| P06 | R1·F4 | {"model__C": 0.001} | 0,730 |
| P06 | R1·F5 | {"model__C": 0.001} | 0,720 |
| P07 | R1·F1 | {"model__C": 0.1, "model__l1_ratio": 0.5} | 0,752 |
| P07 | R1·F2 | {"model__C": 1, "model__l1_ratio": 0.1} | 0,740 |
| P07 | R1·F3 | {"model__C": 0.01, "model__l1_ratio": 0.1} | 0,733 |
| P07 | R1·F4 | {"model__C": 0.1, "model__l1_ratio": 0.5} | 0,764 |
| P07 | R1·F5 | {"model__C": 1, "model__l1_ratio": 0.9} | 0,733 |
| P08 | R1·F1 | {"model__C": 0.001, "model__alpha": 0.5} | 0,737 |
| P08 | R1·F2 | {"model__C": 0.001, "model__alpha": 0.5} | 0,750 |
| P08 | R1·F3 | {"model__C": 10, "model__alpha": 1} | 0,699 |
| P08 | R1·F4 | {"model__C": 0.1, "model__alpha": 0.5} | 0,709 |
| P08 | R1·F5 | {"model__C": 0.1, "model__alpha": 1} | 0,706 |
| P09 | R1·F1 | {"model__C": 0.01, "select__k": 2000} | 0,796 |
| P09 | R1·F2 | {"model__C": 0.01, "select__k": 2000} | 0,742 |
| P09 | R1·F3 | {"model__C": 0.001, "select__k": 1000} | 0,747 |
| P09 | R1·F4 | {"model__C": 0.01, "select__k": 1000} | 0,754 |
| P09 | R1·F5 | {"model__C": 0.1, "select__k": 2000} | 0,764 |
| P10 | R1·F1 | {"model__C": 0.01, "select__k": 500} | 0,797 |
| P10 | R1·F2 | {"model__C": 0.001, "select__k": 500} | 0,744 |
| P10 | R1·F3 | {"model__C": 0.1, "select__k": 500} | 0,731 |
| P10 | R1·F4 | {"model__C": 0.01, "select__k": 1000} | 0,751 |
| P10 | R1·F5 | {"model__C": 0.001, "select__k": 500} | 0,760 |
| P11 | R1·F1 | {"model__shrink_threshold": null} | 0,633 |
| P11 | R1·F2 | {"model__shrink_threshold": null} | 0,634 |
| P11 | R1·F3 | {"model__shrink_threshold": null} | 0,628 |
| P11 | R1·F4 | {"model__shrink_threshold": null} | 0,643 |
| P11 | R1·F5 | {"model__shrink_threshold": null} | 0,647 |
| P12 | R1·F1 | {"model__max_features": "sqrt", "model__min_samples_leaf": 3} | 0,650 |
| P12 | R1·F2 | {"model__max_features": "sqrt", "model__min_samples_leaf": 3} | 0,686 |
| P12 | R1·F3 | {"model__max_features": "sqrt", "model__min_samples_leaf": 3} | 0,604 |
| P12 | R1·F4 | {"model__max_features": 0.01, "model__min_samples_leaf": 3} | 0,673 |
| P12 | R1·F5 | {"model__max_features": "sqrt", "model__min_samples_leaf": 3} | 0,683 |
| P13 | R1·F1 | {"model__n_neighbors": 1, "select__k": 100} | 0,741 |
| P13 | R1·F2 | {"model__n_neighbors": 3, "select__k": 500} | 0,724 |
| P13 | R1·F3 | {"model__n_neighbors": 5, "select__k": 500} | 0,681 |
| P13 | R1·F4 | {"model__n_neighbors": 3, "select__k": 100} | 0,764 |
| P13 | R1·F5 | {"model__n_neighbors": 5, "select__k": 100} | 0,742 |

## 4. Chạm biên grid (≥ 3/5 fold ở cùng một biên)

| Pipeline | Tham số | Biên | Số fold | Việc cần làm |
| --- | --- | --- | --- | --- |
| P04 | select__k | 150 | 3/5 | extend once: one step past 150; choose the value |
| P05 | model__C | 0.01 | 5/5 | extend once: add 0.001 |
| P06 | model__C | 0.001 | 3/5 | extend once: add 0.0001 |
| P09 | select__k | 2000 | 3/5 | extend once: add 4000 |
| P10 | select__k | 500 | 4/5 | extend once: add 250 |
| P11 | model__shrink_threshold | None | 5/5 | natural limit: nothing to extend |
| P12 | model__max_features | sqrt | 4/5 | not applicable: only 2 grid values |
| P12 | model__min_samples_leaf | 3 | 5/5 | not applicable: only 2 grid values |
| P13 | select__k | 100 | 3/5 | not applicable: only 2 grid values |

## 5. Kiểm tra engine bằng P02

Điểm inner của P02 so với Round 1 lệch tối đa 2.22e-16: **khớp**.

## 6. Trước khi gắn tag `p3.0-frozen`

- Sửa mọi lỗi và warning ở mục 1–2, hoặc ghi rõ vì sao chấp nhận.
- Mỗi dòng "extend once" ở mục 4: mở rộng grid đúng một bước trong `configs/protocol3.json`, chạy lại vòng A cho pipeline đó với `--replace`, rồi chạy lại lệnh này.
- Không loại pipeline vì điểm thấp. Chỉ được bỏ pipeline không chạy nổi trong ngân sách thời gian.
