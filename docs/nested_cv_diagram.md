# Nested CV của Protocol 3.0: sơ đồ đầy đủ

Tài liệu đi kèm [protocol_3.0_proposal.md](protocol_3.0_proposal.md). Mục đích: chỉ cần nhìn sơ đồ là biết dữ liệu đi qua những tầng nào, mỗi tầng sinh ra gì, và thứ đó đi đâu tiếp theo. Mọi con số điểm (0,79, 0,80, …) trong ví dụ là **số minh hoạ**, không phải kết quả thật.

## Đọc nhanh trong 30 giây

- Cả dự án dùng **một** khung nested CV duy nhất: 3 repeat × 5 outer fold = **15 outer fold**. Mỗi outer fold có **4 inner fold**.
- Trong **mỗi** outer fold, **cả 13 pipeline** đều chạy, độc lập với nhau. Mỗi pipeline tự grid search trên **cùng** 4 inner fold đó.
- **Vòng A** là một lượt chạy thử repeat 1 để tra lỗi kỹ thuật, mù outer, rồi **bỏ kết quả đi**. **Vòng B** chạy lại **đủ 3 repeat** từ config đã đóng băng. Hai vòng dùng cùng một khung nested CV và cùng `outer.csv`; chỉ kết quả vòng B được phân tích.
- Điểm của một pipeline = macro-F1 trên 254 dự đoán ghép từ 5 outer test của một repeat. Tham số tốt nhất g\* có thể **khác nhau** giữa các fold.
- Con số chính của dự án là **META-SELECT**: chọn pipeline bằng điểm inner trong từng outer fold, không chọn bằng điểm outer.

**Màu dùng chung cho mọi sơ đồ:** xanh dương = đầu vào · vàng = bước chạy (có fit) · tím = output được lưu · đỏ = cổng kiểm soát hoặc dữ liệu bị khoá · xanh lá = kết quả cuối.

**Nội dung:**
[1. Toàn bộ quy trình](#1-toàn-bộ-quy-trình-theo-giai-đoạn) ·
[2. Chia dữ liệu](#2-chia-dữ-liệu-repeat-outer-fold-inner-fold) ·
[3. Trong một outer fold](#3-bên-trong-một-outer-fold-13-pipeline) ·
[4. Trong một pipeline](#4-bên-trong-một-pipeline-grid--inner-fold-ví-dụ-p07) ·
[5. Trong một lần fit](#5-bên-trong-một-lần-fit-các-stage) ·
[6. Gom kết quả](#6-gom-kết-quả-lên-từ-51-dự-đoán-tới-con-số-chính) ·
[7. Output đi đâu](#7-mỗi-output-đi-đâu) ·
[8. Đếm số lượng](#8-đếm-số-lượng) ·
[9. Hiểu nhầm](#9-những-chỗ-hay-hiểu-nhầm)

---

## 1. Toàn bộ quy trình theo giai đoạn

Đây là bản đồ tổng. Các mục sau phóng to từng ô.

```mermaid
flowchart TD
  classDef inp fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
  classDef run fill:#fef3c7,stroke:#d97706,color:#78350f
  classDef out fill:#f3e8ff,stroke:#9333ea,color:#581c87
  classDef gate fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
  classDef fin fill:#dcfce7,stroke:#16a34a,color:#14532d

  subgraph G0["GĐ 0 · Đầu vào (đã có, không đổi)"]
    direction LR
    D["Dữ liệu<br/>254 ca × 20.531 gene<br/>6 subtype"]:::inp
    SO["outer.csv<br/>3 repeat × 5 outer fold"]:::inp
    SI["inner.csv<br/>4 inner fold cho mỗi outer fold"]:::inp
    CF["Config<br/>13 pipeline + grid"]:::inp
  end

  subgraph G1["GĐ 1 · Smoke run"]
    SM["Mỗi pipeline chạy 1 outer fold"]:::run
    SMO["Runtime thật + lỗi<br/>➜ chỉ để sửa code và ước thời gian<br/>KHÔNG dùng cho kết quả"]:::out
    SM --> SMO
  end

  subgraph G2["GĐ 2 · VÒNG A = chạy thử repeat 1 · 5 outer fold × 13 pipeline"]
    RA["Nested CV repeat 1<br/>(chi tiết ở mục 3–5)"]:::run
    RAx["Run folder vòng A<br/>dự đoán outer + điểm inner<br/>🔒 không ai tính hay xem điểm outer<br/>➜ chỉ lưu để tra lỗi, KHÔNG vào phân tích"]:::out
    RAs["Báo cáo screening<br/>warning · hội tụ · runtime<br/>điểm inner · g* có nằm ở biên grid không"]:::out
    RA --> RAx & RAs
  end

  Q{"Lỗi kỹ thuật, hoặc g* chạm<br/>biên grid ở ≥3/5 fold?"}:::gate
  FX["Sửa lỗi / tăng max_iter /<br/>mở rộng grid 1 bước, 1 lần<br/>➜ chạy lại vòng A cho pipeline đó<br/>(vẫn mù outer) để xác nhận đã sửa"]:::run
  FR["🧊 GĐ 3 · Đóng băng config<br/>tag p3.0-frozen"]:::gate

  subgraph G4["GĐ 4 · VÒNG B = chạy lại ĐỦ 3 repeat · 15 outer fold × 13 pipeline"]
    RB["Nested CV repeat 1, 2, 3<br/>(chi tiết ở mục 3–5)"]:::run
    RBp["Dự đoán outer test<br/>13 pipeline × 254 ca × 3 repeat"]:::out
    RBi["Điểm inner của mọi ứng viên<br/>+ g* ở mỗi fold"]:::out
    RB --> RBp & RBi
  end

  subgraph G5["GĐ 5 · Mở niêm phong, lập bảng (mục 6)"]
    PP["Toàn bộ dự đoán outer<br/>13 pipeline × 254 ca × 3 repeat"]:::out
    TA["Bảng A · macro-F1 gộp 254 ca<br/>13 pipeline × 3 repeat"]:::out
    TB["Bảng B · macro-F1 từng fold<br/>13 pipeline × 15 outer fold"]:::out
    TC["Bảng C · điểm inner<br/>mọi cặp (pipeline, ứng viên) × 15 fold"]:::out
  end

  subgraph G6["GĐ 6 · Phân tích: 3 câu hỏi"]
    Q1["Câu 1 · META-SELECT<br/>➜ CON SỐ CHÍNH của dự án"]:::fin
    Q2["Câu 2 · 11 cặp ablation<br/>➜ stage nào quan trọng"]:::fin
    Q3["Câu 3 · nhóm tương đương<br/>➜ pipeline mang sang app"]:::fin
  end

  subgraph G7["GĐ 7 · Sau phân tích"]
    SE["Độ nhạy S-TSS · S-206 · S-5CLASS<br/>cho pipeline được chọn, P02, P06"]:::run
    FM["Refit pipeline được chọn trên cả 254 ca<br/>➜ mô hình cuối cho app"]:::fin
    RP["Báo cáo / Methods"]:::fin
  end

  G0 --> SM
  SMO --> RA
  RAs --> Q
  Q -->|"có"| FX
  FX --> RA
  Q -->|"không"| FR
  FR --> RB
  RBp --> PP
  RBi --> TC
  PP --> TA & TB
  PP --> Q1
  TC --> Q1
  TB --> Q2
  TA --> Q3
  TB --> Q3
  Q1 --> RP
  Q2 --> RP
  Q3 --> SE
  SE --> RP
  Q3 --> FM
  Q1 -.->|"hiệu năng ghi trong model card"| FM
```

Ba điểm cần nhớ từ sơ đồ này:

1. Kết quả smoke run **dừng lại ở đó**. Nó chỉ dùng để sửa code và ước thời gian chạy.
2. Vòng A chạy thật, kể cả bước dự đoán outer, nhưng không ai tính hay xem điểm outer, và toàn bộ kết quả của nó **bị bỏ**. Vòng A vẫn phải mù vì vòng B dùng **cùng** `outer.csv`: xem outer ở vòng A rồi chỉnh config cũng chính là chỉnh theo test của vòng B.
3. Điểm outer chỉ được mở **sau** khi đã đóng băng config. Vì vậy không ai sửa được grid hay pipeline dựa trên điểm outer.

---

## 2. Chia dữ liệu: repeat, outer fold, inner fold

### 2.1 Outer: 3 repeat × 5 outer fold = 15 outer fold

Mỗi repeat xáo trộn 254 ca theo một cách khác (cố định sẵn trong `outer.csv`) rồi cắt thành 5 phần, phân tầng theo subtype. **Outer fold k** lấy phần k làm **outer test**, 4 phần còn lại làm **outer train**. "Outer fold" là cả lần chia đó; "outer test" chỉ là một nửa của nó.

| Repeat 1 | Phần 1 (≈51 ca) | Phần 2 (≈51) | Phần 3 (≈51) | Phần 4 (≈51) | Phần 5 (≈50) |
| --- | --- | --- | --- | --- | --- |
| **Outer fold 1** | 🔒 **test** | train | train | train | train |
| **Outer fold 2** | train | 🔒 **test** | train | train | train |
| **Outer fold 3** | train | train | 🔒 **test** | train | train |
| **Outer fold 4** | train | train | train | 🔒 **test** | train |
| **Outer fold 5** | train | train | train | train | 🔒 **test** |

Mỗi ca nằm trong outer test **đúng một lần** trong mỗi repeat. Vì vậy, sau 5 outer fold, mỗi pipeline có đúng 254 dự đoán cho repeat đó. Repeat 2 và 3 làm lại y hệt, chỉ khác cách xáo trộn.

Vòng A chạy thử repeat 1, sau đó vòng B chạy lại cả 15 outer fold:

```mermaid
flowchart TD
  classDef a fill:#f3f4f6,stroke:#9ca3af,color:#374151
  classDef b fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
  classDef gate fill:#fee2e2,stroke:#dc2626,color:#7f1d1d

  ALL["254 ca"]

  subgraph VA["VÒNG A · chạy thử repeat 1 · mù outer · kết quả bỏ đi"]
    direction LR
    a1["R1·F1<br/>train ≈203<br/>test ≈51 🔒"]:::a ~~~ a2["R1·F2<br/>train ≈203<br/>test ≈51 🔒"]:::a ~~~ a3["R1·F3<br/>train ≈203<br/>test ≈51 🔒"]:::a ~~~ a4["R1·F4<br/>train ≈203<br/>test ≈51 🔒"]:::a ~~~ a5["R1·F5<br/>train ≈204<br/>test ≈50 🔒"]:::a
  end

  FR["🧊 Đóng băng config · tag p3.0-frozen"]:::gate

  subgraph VB["VÒNG B · chạy lại đủ 3 repeat từ commit đã tag"]
    direction TB
    subgraph R1["Repeat 1 · cùng split với vòng A"]
      direction LR
      r1f1["R1·F1"]:::b ~~~ r1f2["R1·F2"]:::b ~~~ r1f3["R1·F3"]:::b ~~~ r1f4["R1·F4"]:::b ~~~ r1f5["R1·F5"]:::b
    end
    subgraph R2["Repeat 2"]
      direction LR
      r2f1["R2·F1"]:::b ~~~ r2f2["R2·F2"]:::b ~~~ r2f3["R2·F3"]:::b ~~~ r2f4["R2·F4"]:::b ~~~ r2f5["R2·F5"]:::b
    end
    subgraph R3["Repeat 3"]
      direction LR
      r3f1["R3·F1"]:::b ~~~ r3f2["R3·F2"]:::b ~~~ r3f3["R3·F3"]:::b ~~~ r3f4["R3·F4"]:::b ~~~ r3f5["R3·F5"]:::b
    end
    R1 ~~~ R2 ~~~ R3
  end

  ALL --> VA
  VA --> FR
  FR --> VB
```

Repeat 1 của vòng B dùng **đúng** cách chia của vòng A. Đó là lý do vòng A phải mù outer dù kết quả của nó bị bỏ: nếu ai xem điểm outer ở vòng A rồi chỉnh config, thì cũng là đã chỉnh theo test của vòng B.

**Mỗi ô R·F ở trên chứa toàn bộ nội dung của mục 3** (13 pipeline, mỗi cái có grid search riêng).

### 2.2 Inner: 4 inner fold bên trong mỗi outer fold

Inner CV chỉ chia **outer train** (≈203 ca). Outer test không bao giờ có mặt ở đây. Ví dụ với R1·F1:

| Outer train của R1·F1 | Phần a (≈51 ca) | Phần b (≈51) | Phần c (≈51) | Phần d (≈50) |
| --- | --- | --- | --- | --- |
| **Inner fold 1** | **val** | train | train | train |
| **Inner fold 2** | train | **val** | train | train |
| **Inner fold 3** | train | train | **val** | train |
| **Inner fold 4** | train | train | train | **val** |

Mỗi inner fold có inner train ≈152 ca và inner val ≈51 ca. Tổng cộng có 15 × 4 = 60 cách chia inner, tất cả nằm sẵn trong `inner.csv` theo khoá (repeat, outer_fold).

**Điểm quan trọng nhất:** trong cùng một outer fold, **cả 13 pipeline và mọi ứng viên grid** đều dùng **chung** 4 inner fold này. Nhờ vậy điểm inner của P06 và của P07 so sánh trực tiếp được với nhau, và META-SELECT ở mục 6.3 mới làm được mà không cần fit thêm.

---

## 3. Bên trong một outer fold: 13 pipeline

Phóng to ô **R1·F1**. 14 ô còn lại giống hệt, chỉ khác dữ liệu train/test.

```mermaid
flowchart TD
  classDef inp fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
  classDef run fill:#fef3c7,stroke:#d97706,color:#78350f
  classDef out fill:#f3e8ff,stroke:#9333ea,color:#581c87
  classDef gate fill:#fee2e2,stroke:#dc2626,color:#7f1d1d

  OT["Outer train của R1·F1 · ≈203 ca"]:::inp
  IN["4 inner fold của R1·F1 (inner.csv)<br/>DÙNG CHUNG cho mọi pipeline, mọi ứng viên<br/>➜ 13 pipeline chạy độc lập, mỗi pipeline = 1 GridSearchCV (mục 4)"]:::inp
  OTE["Outer test của R1·F1 · ≈51 ca 🔒<br/>chỉ được dùng ở bước predict cuối"]:::gate
  OT --> IN

  subgraph SVM["Lô SVM (W4a)"]
    direction TB
    P01["P01 DUMMY<br/>log2 → Dummy, 2 biến thể<br/>không tune · G=1<br/>4 + 1 = 5 fit"]:::run
    P02["P02 R1-REF<br/>F0 → Z1 → ANOVA k=150 → SVM<br/>C: 0,01 · 0,1 · 1 · 10 · 100 · G=5<br/>20 + 1 = 21 fit"]:::run
    P03["P03 SVM-BAL<br/>như P02 + class weight<br/>C × 5 · G=5<br/>21 fit"]:::run
    P04["P04 SVM-BAL-K<br/>như P03 nhưng tune k<br/>k: 150 · 500 · 1000 · 2000 × C × 5 · G=20<br/>80 + 1 = 81 fit"]:::run
    P05["P05 SVM-BAL-MAD<br/>F2 MAD 5000 → Z1 → SVM, balanced<br/>C × 5 · G=5<br/>21 fit"]:::run
    P01 ~~~ P02 ~~~ P03 ~~~ P04 ~~~ P05
  end
  subgraph LRL["Lô LR (W4b)"]
    direction TB
    P06["P06 LR-L2-BAL<br/>F2 → Z1 → LR L2, balanced<br/>C: 1e-3 · 1e-2 · 0,1 · 1 · 10 · G=5<br/>21 fit"]:::run
    P07["P07 LR-EN-BAL ★<br/>F2 → Z1 → LR elastic-net, balanced<br/>l1_ratio: 0,1 · 0,5 · 0,9 × C: 0,01 · 0,1 · 1 · G=9<br/>36 + 1 = 37 fit"]:::run
    P08["P08 LR-L2-PRIOR<br/>F2 → Z1 → LR L2 + ngưỡng α<br/>C × 5 × α: 0 · 0,5 · 1 · G=15<br/>60 + 1 = 61 fit"]:::run
    P06 ~~~ P07 ~~~ P08
  end
  subgraph FSI["Lô FS & imbalance (W4c)"]
    direction TB
    P09["P09 LR-L2-ANOVA<br/>F1 → Z1 → ANOVA → LR L2, balanced<br/>k: 500 · 1000 · 2000 × C × 5 · G=15<br/>61 fit"]:::run
    P10["P10 LR-L2-ANOVA-SMOTE<br/>như P09, SMOTE thay class weight<br/>G=15<br/>61 fit"]:::run
    P09 ~~~ P10
  end
  subgraph OTH["Lô baseline khác (W4d)"]
    direction TB
    P11["P11 PAM<br/>F2 → nearest shrunken centroid<br/>shrink: 4 · 2 · 1 · 0,5 · 0 · G=5<br/>21 fit"]:::run
    P12["P12 RF-BAL<br/>F2 → random forest, balanced<br/>max_features: sqrt · 0,01 × leaf: 3 · 1 · G=4<br/>16 + 1 = 17 fit"]:::run
    P13["P13 KNN<br/>F1 → Z1 → ANOVA → kNN<br/>k: 100 · 500 × neighbors: 7 · 5 · 3 · 1 · G=8<br/>32 + 1 = 33 fit"]:::run
    P11 ~~~ P12 ~~~ P13
  end

  IN --> SVM & LRL & FSI & OTH

  SVM & LRL & FSI & OTH --> EACH["Mỗi pipeline sinh ra 3 thứ"]
  EACH --> O1["51 dự đoán outer × 13 pipeline<br/>➜ ghép ở mục 6.1"]:::out
  EACH --> O2["Điểm inner: 112 ứng viên × 4 inner fold<br/>+ g* của từng pipeline<br/>➜ Bảng C, META-SELECT (mục 6.3)"]:::out
  EACH --> O3["Runtime, warning, g* có ở biên grid không<br/>➜ báo cáo screening (chỉ vòng A)"]:::out
  OTE -.->|"mô hình refit của từng pipeline<br/>chỉ predict, không fit"| O1
```

Trong một outer fold có tổng cộng **461 fit** (cộng các số "fit" ở trên). P01 chạy để tham chiếu nhưng **không** được tham gia META-SELECT.

Pipeline nào chạy trước không quan trọng. Trên thực tế mỗi người chạy một lô, và mỗi run tự lặp qua 15 outer fold:

```text
for pipeline in lô của mình:            # vd W4b: P06, P07, P08
    for repeat in [1] nếu vòng A, [1, 2, 3] nếu vòng B:
        for outer_fold in 1..5:          # đọc outer.csv
            GridSearchCV(grid của pipeline, cv = 4 inner fold đọc từ inner.csv)
            refit g* trên outer train → predict outer test → lưu
```

Kết quả giống hệt như khi đặt vòng lặp outer fold ra ngoài, vì các pipeline không phụ thuộc nhau. Thứ duy nhất nối chúng lại là **hai file split dùng chung**.

---

## 4. Bên trong một pipeline: grid × inner fold (ví dụ P07)

Phóng to ô **P07 tại R1·F1**. Mọi pipeline khác làm y hệt, chỉ khác số ứng viên G.

```mermaid
flowchart TD
  classDef inp fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
  classDef run fill:#fef3c7,stroke:#d97706,color:#78350f
  classDef out fill:#f3e8ff,stroke:#9333ea,color:#581c87
  classDef gate fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
  classDef note fill:#f3f4f6,stroke:#9ca3af,color:#374151

  OT["Outer train của R1·F1 · ≈203 ca"]:::inp

  subgraph IF["4 inner fold của R1·F1"]
    direction LR
    i1["Inner 1<br/>train b+c+d ≈152<br/>val a ≈51"]:::inp ~~~ i2["Inner 2<br/>train a+c+d<br/>val b"]:::inp ~~~ i3["Inner 3<br/>train a+b+d<br/>val c"]:::inp ~~~ i4["Inner 4<br/>train a+b+c<br/>val d"]:::inp
  end

  subgraph GR["Grid của P07 · 9 ứng viên, theo thứ tự khai báo"]
    direction LR
    g1["g1<br/>l1 0,1 · C 0,01"]:::run ~~~ g2["g2<br/>l1 0,1 · C 0,1"]:::run ~~~ g3["g3<br/>l1 0,1 · C 1"]:::run
    g4["g4<br/>l1 0,5 · C 0,01"]:::run ~~~ g5["g5<br/>l1 0,5 · C 0,1"]:::run ~~~ g6["g6<br/>l1 0,5 · C 1"]:::run
    g7["g7<br/>l1 0,9 · C 0,01"]:::run ~~~ g8["g8<br/>l1 0,9 · C 0,1"]:::run ~~~ g9["g9<br/>l1 0,9 · C 1"]:::run
  end

  OT --> IF
  IF -->|"MỖI ứng viên × MỖI inner fold:<br/>fit trên ≈152, chấm macro-F1 trên ≈51<br/>9 × 4 = 36 fit"| GR
  GR --> SC["36 điểm inner<br/>➜ lấy trung bình theo ứng viên (bảng bên dưới)"]:::out
  SC --> PK["Chọn g* = ứng viên có mean cao nhất<br/>ví dụ g5 (l1 0,5 · C 0,1) = 0,790<br/>hoà tuyệt đối ➜ lấy ứng viên khai báo trước"]:::run
  SC -.->|"lưu vào search_results"| SR["➜ Bảng C và META-SELECT (mục 6.3)<br/>➜ báo cáo screening: g* có ở biên grid không"]:::out
  PK --> RF["REFIT P07 với g* trên CẢ ≈203 ca outer train<br/>(fit thứ 37)"]:::run
  OTE["Outer test của R1·F1 · ≈51 ca 🔒"]:::gate
  RF --> PR["Predict ≈51 ca outer test"]:::run
  OTE --> PR
  PR --> OUT["51 dự đoán + g* đã dùng<br/>➜ predictions.csv ➜ mục 6.1"]:::out
  RF -.->|"dùng xong thì bỏ"| X["Mô hình refit này KHÔNG phải mô hình cuối.<br/>Nó chỉ tồn tại để sinh 51 dự đoán trung thực."]:::note
```

Bảng 36 điểm inner (số minh hoạ). Mỗi ô là **một lần fit**: fit trên inner train, chấm macro-F1 trên inner val.

| Ứng viên | Inner 1 | Inner 2 | Inner 3 | Inner 4 | **Mean** |
| --- | --- | --- | --- | --- | --- |
| g1 · l1 0,1 · C 0,01 | 0,70 | 0,74 | 0,69 | 0,72 | 0,713 |
| g2 · l1 0,1 · C 0,1 | 0,76 | 0,79 | 0,74 | 0,77 | 0,765 |
| g3 · l1 0,1 · C 1 | 0,75 | 0,78 | 0,73 | 0,76 | 0,755 |
| g4 · l1 0,5 · C 0,01 | 0,68 | 0,71 | 0,66 | 0,70 | 0,688 |
| **g5 · l1 0,5 · C 0,1** | 0,80 | 0,81 | 0,76 | 0,79 | **0,790 ⭐ g\*** |
| g6 · l1 0,5 · C 1 | 0,77 | 0,80 | 0,75 | 0,78 | 0,775 |
| g7 · l1 0,9 · C 0,01 | 0,61 | 0,65 | 0,61 | 0,63 | 0,625 |
| g8 · l1 0,9 · C 0,1 | 0,78 | 0,80 | 0,75 | 0,77 | 0,775 |
| g9 · l1 0,9 · C 1 | 0,76 | 0,78 | 0,75 | 0,77 | 0,765 |

Đọc theo hàng: một ứng viên được chấm trên cả 4 inner fold, và điểm của nó là trung bình 4 số. Đọc theo cột: cùng một inner fold được dùng cho cả 9 ứng viên, nên so sánh giữa các hàng là công bằng.

Một hàng, ví dụ g5, khi mở ra:

```mermaid
flowchart LR
  classDef run fill:#fef3c7,stroke:#d97706,color:#78350f
  classDef out fill:#f3e8ff,stroke:#9333ea,color:#581c87

  subgraph G5["Ứng viên g5 (l1 0,5 · C 0,1) trên 4 inner fold của R1·F1"]
    direction TB
    a["Inner 1: fit trên b+c+d (≈152 ca)<br/>chấm trên a (≈51 ca) ➜ 0,80"]:::run
    b["Inner 2: fit trên a+c+d<br/>chấm trên b ➜ 0,81"]:::run
    c["Inner 3: fit trên a+b+d<br/>chấm trên c ➜ 0,76"]:::run
    d["Inner 4: fit trên a+b+c<br/>chấm trên d ➜ 0,79"]:::run
    a ~~~ b ~~~ c ~~~ d
  end
  G5 --> M["mean = 0,790<br/>= điểm inner của g5<br/>➜ hàng g5 trong bảng trên"]:::out
```

---

## 5. Bên trong một lần fit: các stage

Mỗi ô trong bảng 36 điểm, và cả bước refit, đều là một lần chạy như dưới đây. Mọi thứ được **học trên phần train** rồi **chỉ áp dụng** lên phần chấm. Ví dụ với P07:

```mermaid
flowchart TD
  classDef run fill:#fef3c7,stroke:#d97706,color:#78350f
  classDef gate fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
  classDef out fill:#f3e8ff,stroke:#9333ea,color:#581c87

  subgraph TR["Phần train · ≈152 hoặc ≈203 khi refit"]
    direction TB
    t0["log2(x+1)"]:::run --> t1["F2: học gene nào qua ngưỡng<br/>+ top 5000 theo MAD"]:::run --> t2["Z1: học mean, SD từng gene"]:::run --> t3["LR elastic-net, balanced<br/>học trọng số"]:::run
  end

  subgraph TE["Phần chấm · inner val hoặc outer test"]
    direction TB
    v0["log2(x+1)"]:::gate --> v1["giữ đúng 5000 gene đã học"]:::gate --> v2["áp mean, SD đã học"]:::gate --> v3["dự đoán subtype"]:::gate
  end

  t1 -.->|"danh sách gene"| v1
  t2 -.->|"mean, SD"| v2
  t3 -.->|"mô hình"| v3
  v3 --> S["Inner: so với nhãn thật ➜ 1 điểm macro-F1<br/>Outer: lưu dự đoán, chưa chấm"]:::out
```

Nếu tính MAD, ANOVA hay SMOTE trên cả 254 ca **trước** khi chia fold, phần chấm sẽ "nhìn thấy" chính nó và điểm số đẹp giả. Danh sách ràng buộc chống leakage đầy đủ ở mục 6 của [proposal](protocol_3.0_proposal.md).

---

## 6. Gom kết quả lên: từ 51 dự đoán tới con số chính

### 6.1 Một pipeline, một repeat ➜ 1 điểm

Ví dụ P07 ở repeat 1. Lưu ý g\* **khác nhau** giữa các fold.

```mermaid
flowchart LR
  classDef out fill:#f3e8ff,stroke:#9333ea,color:#581c87
  classDef fin fill:#dcfce7,stroke:#16a34a,color:#14532d

  f1["R1·F1 · g* = l1 0,5 · C 0,1<br/>51 dự đoán"]:::out
  f2["R1·F2 · g* = l1 0,9 · C 0,1<br/>51 dự đoán"]:::out
  f3["R1·F3 · g* = l1 0,5 · C 1<br/>51 dự đoán"]:::out
  f4["R1·F4 · g* = l1 0,5 · C 0,1<br/>51 dự đoán"]:::out
  f5["R1·F5 · g* = l1 0,1 · C 0,1<br/>50 dự đoán"]:::out

  f1 & f2 & f3 & f4 & f5 --> POOL["Ghép = 254 dự đoán<br/>mỗi ca đúng 1 lần"]:::out
  POOL --> A["macro-F1 gộp của P07 · R1<br/>➜ 1 ô của Bảng A"]:::fin
  POOL --> CM["Confusion matrix, recall theo lớp + Wilson CI<br/>➜ báo cáo, phân tích lỗi (W5)"]:::fin
  POOL -->|"tách lại theo từng fold"| PF["5 điểm macro-F1, mỗi điểm trên ≈51 ca<br/>➜ 5 ô của Bảng B"]:::out
```

Vì g\* đổi theo fold, điểm này **không** thuộc về một bộ tham số cố định. Nó đo cả quy trình "P07 kèm tự tune grid": nếu đưa P07 cho dữ liệu mới và để nó tự chọn tham số, nó đạt bao nhiêu.

Điểm chính dùng dự đoán **gộp 254 ca** thay vì trung bình 5 fold, vì mỗi fold chỉ có 1–2 ca MPNST, nên macro-F1 trên một fold rất nhiễu. Điểm theo fold chỉ được lưu để chạy kiểm định thống kê.

### 6.2 13 pipeline × 3 repeat ➜ Bảng A và Bảng B

Lặp mục 6.1 cho 13 pipeline và 3 repeat (số minh hoạ):

**Bảng A** · macro-F1 gộp 254 ca. Dùng cho: báo cáo mọi pipeline, và chọn T ở Câu 3.

| Pipeline | R1 | R2 | R3 | Mean ± SD |
| --- | --- | --- | --- | --- |
| P01 DUMMY | 0,097 | 0,097 | 0,097 | 0,097 ± 0,000 |
| P02 R1-REF | 0,77 | 0,76 | 0,78 | 0,770 ± 0,010 |
| … | | | | |
| P07 LR-EN-BAL | 0,80 | 0,81 | 0,79 | 0,800 ± 0,010 |
| … (13 dòng) | | | | |

**Bảng B** · macro-F1 theo từng outer fold, 15 cột. Dùng cho: kiểm định ở Câu 2 và Câu 3.

| Pipeline | R1·F1 | R1·F2 | … | R3·F5 |
| --- | --- | --- | --- | --- |
| P02 | 0,75 | 0,79 | … | 0,77 |
| P03 | 0,77 | 0,80 | … | 0,78 |
| … (13 dòng) | | | | |

### 6.3 Câu 1 · META-SELECT ➜ con số chính

Ý tưởng giống hệt grid search ở mục 4, nhưng lên một tầng: coi "chọn pipeline nào" cũng là một hyperparameter, và chọn nó **chỉ bằng điểm inner**.

```mermaid
flowchart TD
  classDef out fill:#f3e8ff,stroke:#9333ea,color:#581c87
  classDef run fill:#fef3c7,stroke:#d97706,color:#78350f
  classDef fin fill:#dcfce7,stroke:#16a34a,color:#14532d

  subgraph F["Trong MỘT outer fold, ví dụ R1·F1"]
    C["Bảng C của R1·F1:<br/>điểm inner (mean 4 inner fold) của 111 cặp<br/>(pipeline, ứng viên) thuộc P02–P13<br/>không gồm P01"]:::out
    C --> W["Lấy cặp cao nhất, ví dụ P07·g5 = 0,790<br/>hoà ➜ theo thứ tự đơn giản ở mục 5.1 proposal"]:::run
    W --> T["Lấy 51 dự đoán outer của P07 ở R1·F1<br/>đã có sẵn, KHÔNG fit thêm"]:::run
  end

  T --> G["Lặp cho 5 outer fold của repeat ➜ ghép 254 dự đoán<br/>fold khác có thể thắng là P06, P09, …"]:::out
  G --> M["macro-F1 META-SELECT cho mỗi repeat<br/>3 repeat ➜ mean ± SD"]:::fin
  M --> R["CON SỐ CHÍNH<br/>➜ báo cáo, model card của app"]:::fin
  W --> FQ["Tần suất mỗi pipeline thắng qua 15 fold<br/>➜ báo cáo độ ổn định"]:::fin
```

Tại sao không cần fit thêm: cặp thắng chung (P07, g5) chắc chắn cũng là cặp thắng **trong** P07, nên g\* của P07 ở fold này chính là g5, và dự đoán outer của P07 ở fold này đã được làm bằng g5.

Tại sao con số này trung thực: ở mọi tầng (chọn tham số, chọn pipeline), quyết định chỉ dựa trên inner. Outer test chỉ được dùng để chấm.

### 6.4 Câu 2 và Câu 3

```mermaid
flowchart LR
  classDef out fill:#f3e8ff,stroke:#9333ea,color:#581c87
  classDef run fill:#fef3c7,stroke:#d97706,color:#78350f
  classDef fin fill:#dcfce7,stroke:#16a34a,color:#14532d

  TB["Bảng B<br/>15 điểm mỗi pipeline"]:::out
  TA["Bảng A<br/>mean của 13 pipeline"]:::out

  subgraph C2["Câu 2 · stage nào quan trọng"]
    D["Cặp đã đăng ký trước, ví dụ P02 vs P03<br/>hiệu d₁ … d₁₅ theo từng fold"]:::run
    T2["Bayesian correlated t-test<br/>ROPE ±0,01"]:::run
    A2["Kết luận từng cặp, ví dụ<br/>class weight có giúp không<br/>➜ chương ablation trong báo cáo"]:::fin
    D --> T2 --> A2
  end

  subgraph C3["Câu 3 · mang pipeline nào sang app"]
    TOP["T = pipeline có mean cao nhất"]:::run
    EQ["So T với từng pipeline X bằng Bayesian t-test<br/>X vào nhóm tương đương nếu<br/>P(T hơn X quá ROPE) < 0,95"]:::run
    S["Chọn pipeline ĐƠN GIẢN NHẤT trong nhóm"]:::fin
    TOP --> EQ --> S
  end

  TB --> D
  TA --> TOP
  TB --> EQ
  S --> SE["Độ nhạy S-TSS · S-206 · S-5CLASS<br/>➜ báo cáo"]:::fin
  S --> FM["Refit trên cả 254 ca ➜ app<br/>hiệu năng ghi = số META-SELECT,<br/>không phải điểm riêng của nó"]:::fin
```

---

## 7. Mỗi output đi đâu

| Output | Sinh ra ở | Đi tiếp tới | Mục đích (nếu không đi tiếp) |
| --- | --- | --- | --- |
| Runtime và lỗi của smoke run | GĐ 1 | Không | Sửa code, ước thời gian. Không dùng cho kết quả |
| Điểm từng inner fold của mỗi ứng viên (`search_results`) | Mục 4, mỗi GridSearch | Mean theo ứng viên ➜ chọn g\*; Bảng C | |
| g\* của mỗi pipeline ở mỗi fold | Mục 4 | Refit; báo cáo screening (chạm biên grid); báo cáo cuối (tham số được chọn) | |
| Báo cáo screening | Vòng A | Quyết định sửa hay đóng băng | |
| Run folder vòng A (dự đoán outer, điểm inner) | Vòng A | Không | Chỉ lưu để tra lỗi. Không ai xem điểm outer, không vào phân tích |
| Mô hình refit trên outer train | Mục 4 | Predict outer test | **Bỏ sau khi dự đoán.** 13 × 15 = 195 mô hình này không phải mô hình cuối |
| 51 dự đoán outer của mỗi pipeline ở mỗi fold | Mục 4 | Ghép 254 (mục 6.1); META-SELECT (mục 6.3) | |
| Bảng A · macro-F1 gộp | Mục 6.2 | Câu 3 (chọn T) | Báo cáo **mọi** pipeline, không chỉ winner |
| Bảng B · macro-F1 theo fold | Mục 6.2 | Câu 2, Câu 3 (kiểm định) | |
| Bảng C · điểm inner | Mục 4, gom ở GĐ 5 | Câu 1 (META-SELECT) | |
| Confusion matrix, recall theo lớp + Wilson CI | Mục 6.1 | Phân tích lỗi (W5) | Báo cáo recall MFS/MPNST |
| Số META-SELECT | Câu 1 | Model card của app | **Con số chính** của dự án |
| Tần suất mỗi pipeline thắng | Câu 1 | Không | Báo cáo độ ổn định của việc chọn |
| Kết luận ablation | Câu 2 | Không | Báo cáo: stage nào quan trọng |
| Pipeline được chọn | Câu 3 | Độ nhạy; refit cuối | |
| Mô hình cuối (refit trên 254 ca) | GĐ 7 | App | Cách làm theo quyết định D11 trong [architecture.md](architecture.md) |

---

## 8. Đếm số lượng

| Thứ | Số lượng | Cách tính |
| --- | --- | --- |
| Repeat | 3 | |
| Outer fold | 15 | 3 × 5 |
| Inner fold | 60 | 15 × 4 |
| Pipeline trong mỗi outer fold | 13 | P01–P13 |
| Ứng viên grid trong mỗi outer fold | 112 | tổng G của P01–P13 |
| Cặp (pipeline, ứng viên) tham gia META-SELECT mỗi outer fold | 111 | bỏ P01 |
| Fit trong mỗi outer fold | 461 | 112 × 4 inner + 13 refit |
| Fit của vòng A (chạy thử 1 repeat) | 2.305 | 461 × 5 |
| Fit của vòng B (chính thức, 3 repeat) | 6.915 | 2.305 × 3 |
| **Tổng fit** | **9.220** | 2.305 + 6.915 |
| Dự đoán outer dùng cho phân tích (vòng B) | 9.906 | 13 pipeline × 254 ca × 3 repeat |
| Mô hình refit của vòng B (bỏ sau khi dự đoán) | 195 | 13 × 15 |

Chưa tính các phân tích độ nhạy.

---

## 9. Những chỗ hay hiểu nhầm

| Hiểu nhầm | Thực tế |
| --- | --- |
| "Outer fold" và "outer test" là một | Outer fold là cả lần chia (train ≈203 + test ≈51). Outer test chỉ là phần test của nó |
| Vòng A và vòng B là hai thiết kế khác nhau | Cùng một nested CV, cùng `outer.csv`. Vòng A là lượt chạy thử repeat 1 để tra lỗi. Vòng B chạy lại đủ 3 repeat từ config đã đóng băng |
| Kết quả repeat 1 của vòng A được dùng lại ở vòng B | Không. Vòng B chạy lại cả repeat 1 từ commit đã tag, nên mọi kết quả chính thức đến từ cùng một phiên bản code. Vòng A vẫn phải mù vì vòng B dùng cùng split |
| Inner CV chọn giữa 13 pipeline | Khi **fit**, inner CV chỉ phục vụ grid của **một** pipeline. So sánh giữa các pipeline bằng điểm inner chỉ xảy ra ở META-SELECT, sau khi chạy xong, và không fit thêm |
| Sau 5 outer fold có 13 điểm của 13 cặp (p, g\*) | Có 13 điểm của **13 pipeline**. Mỗi pipeline có thể dùng g\* khác nhau ở mỗi fold |
| Pipeline có điểm outer cao nhất chính là con số báo cáo | Không. Như vậy là chọn bằng đề thi rồi chấm bằng chính đề thi đó, nên số sẽ lạc quan. Con số báo cáo là META-SELECT |
| Mô hình đưa vào app là một trong các mô hình refit | Không. 195 mô hình refit chỉ để sinh dự đoán trung thực rồi bỏ. Mô hình cuối được refit trên cả 254 ca |
| Vòng A được loại pipeline điểm thấp | Không. Vòng A chỉ được sửa lỗi kỹ thuật và mở rộng biên grid một lần |
