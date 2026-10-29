# Hướng dẫn chạy Protocol 3.0

Mọi lệnh chạy từ thư mục gốc của repo, trên branch `protocol3`. Lệnh giống nhau trên PowerShell và macOS; chỉ bước kích hoạt môi trường khác nhau. Thiết kế nằm ở [proposal](protocol_3.0_proposal.md) và [nested CV diagram](nested_cv_diagram.md).

## Ai chạy gì

| Member | Người | Lô | Pipeline |
| --- | --- | --- | --- |
| 1 | Trương Nam Hùng | W4a SVM | P01-MF, P01-ST, P02, P03, P04, P05 |
| 2 | Bùi Tiến Hưng | W4b LR | P06, P07, P08 |
| 3 | Nguyễn Thành Kiên | W4c FS & imbalance | P09, P10 |
| 4 | Lê Đức Hoàng Vy | W4d baseline | P11, P12, P13 |

Dung không chạy lô nào: Dung chạy `screen` sau vòng A và `analyze` sau vòng B. P01 có hai biến thể Dummy nên chạy thành hai ID.

## 1. Cài đặt (một lần)

Dùng Python 3.12 và một bản Git clone (bản tải ZIP không có commit nên không chạy chính thức được).

```powershell
git fetch origin
git checkout protocol3
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # macOS: source .venv/bin/activate
python -m pip install -r requirements-protocol3.txt
python -m src.data.prepare
python -m src.p3 check --member N
```

`check` kiểm tra phiên bản Python và package, checksum dữ liệu, `outer.csv`/`inner.csv`, config, rồi in số fit của lô. Nếu báo lỗi checksum dataset, chạy lại `python -m src.data.prepare` từ code mới nhất.

## 2. Smoke run

```powershell
python -m src.p3 smoke --member N --jobs 4
```

Chạy 1 outer fold cho mỗi pipeline của lô, in thời gian và ước tính cho vòng A và B. Kết quả nằm ở `results/p3/smoke/` (không commit). Với P02, lệnh còn so điểm inner với Round 1: phải thấy `(match)`.

`--jobs` là số fit chạy song song. Để chừa 1–2 lõi cho máy. Kết quả không phụ thuộc `--jobs`.

## 3. Vòng A: screening (mù outer)

```powershell
python -m src.p3 run --round A --member N --jobs 4
```

Chạy repeat 1 (5 outer fold). Vòng A **không dự đoán outer test**, nên không ai thấy được điểm outer. Kết quả nằm ở `experiments/p3.0/roundA/memberN/<pipeline>/`. Lệnh từ chối chạy khi code, config hoặc split có thay đổi chưa commit.

Nộp: tạo branch `roundA-memberN` từ `protocol3`, commit thư mục `experiments/p3.0/roundA/memberN/`, mở PR vào `protocol3`. Không sửa file trong thư mục kết quả: `screen` và `analyze` kiểm checksum từng file.

Khi cần chạy lại một pipeline sau khi sửa: `python -m src.p3 run --round A --member N --pipeline P07 --replace`.

## 4. Screening và đóng băng (Dung, người giữ repo)

```powershell
python -m src.p3 screen experiments/p3.0/roundA/member1 experiments/p3.0/roundA/member2 experiments/p3.0/roundA/member3 experiments/p3.0/roundA/member4
```

Ra `experiments/p3.0/roundA/screening/screening.md`: trạng thái, runtime, warning, hội tụ, g* từng fold, chạm biên grid, và kiểm tra P02 so với Round 1. Theo mục 4.1 của proposal, chỉ được sửa lỗi kỹ thuật, tăng `max_iter`, hoặc mở rộng biên grid đúng một lần. Pipeline nào sửa config thì chạy lại vòng A cho pipeline đó.

Khi xong, người giữ repo commit config cuối và gắn tag:

```powershell
git tag p3.0-frozen
git push origin p3.0-frozen
```

## 5. Vòng B: chính thức (3 repeat)

```powershell
git pull
git fetch --tags
python -m src.p3 run --round B --member N --jobs 4
```

Lệnh chỉ chạy khi code, config và split giống hệt tag `p3.0-frozen`, và cây làm việc sạch. Kết quả: `experiments/p3.0/roundB/memberN/<pipeline>/` gồm dự đoán outer, điểm inner của mọi ứng viên, g*, gene giữ lại theo fold, warning, runtime, manifest và checksum. Nộp qua PR như vòng A (branch `roundB-memberN`).

## 6. Phân tích (Dung)

```powershell
python -m src.p3 analyze experiments/p3.0/roundB/member1 experiments/p3.0/roundB/member2 experiments/p3.0/roundB/member3 experiments/p3.0/roundB/member4
```

Ra `experiments/p3.0/roundB/analysis/`: `report.md` theo khung của [mock_results_example.md](mock_results_example.md) (bảng A, A2, B, D, META-SELECT, 11 cặp ablation với ROPE 0,01 và 0,02, nhóm tương đương, confusion matrix có Wilson CI, runtime), các bảng CSV (A, B, C, META-SELECT, ablation) và `summary.json`. Mục 0 của báo cáo so P02 với Round 1; nếu không khớp thì dừng lại. Các ô "Nhận xét" để Dung viết.

## 7. Độ nhạy (chưa chốt người chạy)

```powershell
python -m src.p3 sensitivity --analysis S-5CLASS --pipeline P06 --pipeline P02
```

- `S-5CLASS`: gộp MFS + UPS, dùng lại split chính.
- `S-TSS`: outer `StratifiedGroupKFold` theo nơi lấy mẫu. Lệnh từ chối chạy cho tới khi nhóm điền ngưỡng "giảm mạnh" vào `sensitivity.s_tss_max_drop` trong config **trước khi đóng băng**.
- `S-206`: cần danh sách 206 Sample ID đã review (Cell 2017) ở `data/raw/cell2017_reviewed_206.txt`, mỗi dòng một ID. Hiện repo chưa có file này.

Mỗi phân tích chạy 1 repeat, ghi split mới kèm checksum vào `experiments/p3.0/sensitivity/<phân tích>/splits/`.

## 8. Mô hình cuối cho app (Giang)

```powershell
python -m src.p3 final
```

Lấy pipeline được chọn ở Câu 3 từ `summary.json` (hoặc `--pipeline PXX`), tune bằng 4-fold CV trên cả 254 ca, refit, và ghi `experiments/p3.0/final/<pipeline>/`: `model.joblib`, `input_features.txt` (thứ tự gene đầu vào), `model_card.json` (tham số, con số META-SELECT để báo cáo, phiên bản package), cùng bằng chứng tune. Mô hình chỉ trả nhãn, chưa có calibration (D11).

## Ghi chú kỹ thuật

### Một lệnh chạy, hai file để gửi leader

Sau khi cài môi trường và chuẩn bị dữ liệu lần đầu, mỗi member chạy lệnh như cũ:

```powershell
python -m src.p3 run --round A --member 2
```

Thay số member theo phân công. Chương trình tự tạo:

- Một file log tại `results/p3/logs/member2/`: tiến độ, warning và traceback lỗi; log bắt đầu trước khi import thư viện ML.
- Một file ZIP tại `results/p3/submissions/member2/`: toàn bộ bằng chứng kết quả của các pipeline được bắt đầu trong lần chạy, cùng `submission_summary.json` ghi complete/failed.

Thư mục member được tạo tự động từ `--member`; member 1/3/4 có thư mục riêng tương ứng. Mỗi lần chạy có tên file riêng, không ghi đè lần trước.

Terminal in đường dẫn hai file. Chỉ gửi hai file đó; không tự tính điểm, ghép bảng hoặc nén thư mục. ZIP là gói bàn giao nguyên trạng, không phải một bảng điểm tổng hợp và không làm lộ outer scores ở vòng A. Leader giải nén vào thư mục riêng rồi dùng lệnh screen/analyze hiện có với thư mục đã giải nén.

Không cần copy file hoặc tạo branch riêng. Khi đang ở `finalized-protocol3`, member 2 nộp qua Git:

```powershell
git add results/p3/submissions/member2/ results/p3/logs/member2/
git commit -m "Submit member 2 round A results and logs"
git pull --rebase origin finalized-protocol3
git push origin finalized-protocol3
```

Thay số member theo phân công. Lệnh add lấy tất cả ZIP/LOG trong thư mục của mình, gồm cả lần chạy lỗi; không thay đổi code/config. Chương trình không tự push. Nếu người khác vừa push và Git từ chối, chạy lại pull --rebase rồi push; không force push.

Nếu dừng do lỗi, ZIP giữ bằng chứng hiện có và ghi failed; pipeline chưa chạy không có kết quả. Không coi gói failed là kết quả hoàn chỉnh. Lỗi trước khi bắt đầu lệnh run (ví dụ thiếu thư viện lúc import) có log nhưng có thể chưa tạo ZIP. Tắt cưỡng bức tiến trình hoặc mất điện không bảo đảm tạo được ZIP; log đã ghi vẫn được giữ.

- Grid của PAM ghi "không co rút" là `null`, vì scikit-learn 1.7 không nhận `shrink_threshold = 0`.
- Warning không làm dừng run; mọi warning được ghi vào `warnings.csv` và hiện trong báo cáo để review.
- `python -m src.data.prepare` ghi file theo kiểu xuống dòng CRLF trên mọi hệ điều hành, để checksum dataset giống nhau trên Windows và macOS.
