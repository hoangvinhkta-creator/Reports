# S131 — R4: Báo cáo đánh giá vận hành

Phiên triển khai ĐẦY ĐỦ (không phải phiên lập kế hoạch). Task canonical:
`docs/tasks/R4-bao-cao-danh-gia.md`. Đặc tả chỉ tiêu:
`docs/spec/R4-DAC-TA-KPI.md`.

---

## 1. Điều kiện mở phiên — đã xác nhận trước khi sửa dòng mã đầu tiên

```text
nhánh mặc định trên origin   claude/extract-upload-repo-gq2ws4
                             (git remote show origin → "HEAD branch")
nhánh làm việc               claude/r4-reports-evaluation-u3vs4d
HEAD lúc mở phiên            824b5d7  (= merge PR #9, repair revision Alembic R3)
                             git merge-base --is-ancestor 824b5d7 HEAD → chứa
so với production             0 commit lệch (nhánh R4 đúng bằng production)
working tree                  SẠCH (git status --porcelain rỗng)
session khác đang sửa Reports KHÔNG (không nhánh nào khác được checkout; phiên
                              làm việc một mình trên container này)
```

**Deploy Render migration `0009_line_binding_period_close`: KHÔNG xác nhận
được từ phiên này.** Phiên không có credential Render và egress mạng bị chặn ở
tầng proxy tới các endpoint quản trị — cùng giới hạn đã ghi ở `S127` và `S130`.
Điều kiện mở phiên của brief vì vậy chỉ thoả về mặt MÃ NGUỒN (repair
`824b5d7` đã có mặt), không thoả về mặt PLATFORM. Đây là một giới hạn được
NÓI RA, không phải một bước bị bỏ qua trong im lặng.

Điều đó an toàn cho phạm vi R4 vì một lý do kiểm được: **R4 không có migration
và không có đường ghi nào.** Nó không phụ thuộc schema `0009` đã lên
production hay chưa; nếu `0009` chưa lên, chính R3 (không phải R4) là thứ chưa
chạy được. Owner vẫn phải hoàn tất checklist `S130` §6–§7 trước khi nghiệm thu
bất cứ thứ gì trên production.

Đã đọc trước khi sửa: `CLAUDE.md`, `PROJECT/PROJECT_PROGRESS.md`,
`docs/sessions/S126-r1-daily-min-theo-ngay-ban.md`,
`docs/sessions/S128-r2-phan-loai-va-gia-nhap-tay.md`,
`docs/sessions/S129-r3-nhap-so-den-chot-ky.md`,
`docs/sessions/S130-r3-integration-and-deployment-attempt.md`, và brief R4.
Repo KHÔNG có tệp quy ước tên AGENTS (dạng viết hoa, ở root); quy ước
nằm ở `CLAUDE.md` và
`governance/core/`.

---

## 2. HEAD và file đã đổi

```text
HEAD mã nguồn R4   86cee4097194460955fe806a05e3a919a20a0e95
nền                824b5d7 (production, không rebase, không force-push)
```

```text
MỚI   app/modules/reporting/evaluation.py          ngữ nghĩa R4 (THUẦN)
MỚI   app/web/evaluation_presentation.py           trình bày R4 (THUẦN)
MỚI   app/web/templates/kinh_doanh_danh_gia.html   trang đánh giá
MỚI   tests/test_r4_evaluation_metrics.py          50 bài, giá trị thuần
MỚI   tests/test_r4_evaluation_web.py              38 bài, route web thật
SỬA   app/web/server.py                            route ĐỌC + 2 bộ lọc +
                                                   3 tham số thu hẹp + _today()
SỬA   app/web/business_queries.py                  đọc thêm lead_source,
                                                   price_source vào details
SỬA   app/web/templates/kinh_doanh.html            đường vào trang đánh giá
SỬA   app/web/templates/kinh_doanh_gia_nhap.html   nói ra phạm vi đã thu hẹp
SỬA   app/web/static/css/tinphat-ui.css            lớp hiển thị của trang mới
```

**Migration: KHÔNG CÓ.** Không bảng mới, không cột mới, `ALEMBIC_HEAD` không
đổi (vẫn `0009_line_binding_period_close`). R4 chỉ đọc.

**Route ghi mới: KHÔNG CÓ.** `/kinh-doanh/danh-gia` chỉ nhận `GET`; `POST` trả
`405`.

---

## 3. Định nghĩa KPI

Bản đầy đủ: `docs/spec/R4-DAC-TA-KPI.md`. Tóm tắt để đọc nhanh:

| Chỉ tiêu | Công thức | Khi không có số |
|---|---|---|
| Doanh thu bán hàng | `BusinessTotals.sales_revenue` | `NO_LINES` · `NO_REVENUE` |
| Số đơn | `COUNT DISTINCT order_key` trong phạm vi | `NO_LINES` |
| SL đủ điều kiện KPI | `SUM(SL)` khi đơn giá > 1.000.000 | `NO_LINES` |
| Doanh thu/đơn | Doanh thu ÷ Số đơn | `NO_ORDERS` · `NO_REVENUE` |
| Lợi nhuận KPI | `official_kpi_profit` (cổng coverage 100 %) | `PROFIT_NOT_OFFICIAL` |
| Biên KPI | LN KPI chính thức ÷ Doanh thu × 100 | `PROFIT_NOT_OFFICIAL` · `NO_REVENUE` |
| Lãi/đơn | LN KPI chính thức ÷ Số đơn | `PROFIT_NOT_OFFICIAL` · `NO_ORDERS` |
| DS quy đổi | `official_converted_sales` | `CONVERTED_NOT_OFFICIAL` |
| % target | DS quy đổi chính thức ÷ Target × 100 (không cap) | 4 mã ở `docs/spec/R4-DAC-TA-KPI.md` §3 |
| Run-rate | (giá trị đến `as_of` ÷ ngày đã trôi qua) × ngày trong tháng | 4 mã ở §4 |

Ba chỉ tiêu R4 THÊM là ba phép chia hai con số đã có, gom về một hàm `_ratio`.
Mọi chỉ tiêu cộng được vẫn do `business_metrics.totals` quyết định — R4 không
tính lại con số nào của R1–R3.

---

## 4. Test — lệnh và kết quả nguyên văn

### 4.1 Baseline TRƯỚC khi sửa (trên chính `824b5d7`, working tree sạch)

```text
$ python -m pytest -q
3058 passed, 12 skipped in 179.74s (0:02:59)
```

Khớp đúng baseline mà `S129` và `PROJECT/PROJECT_PROGRESS.md` đã ghi cho R3.

```text
$ python governance/scripts/governance/validate_structure.py
GOVERNANCE STRUCTURE: PASS
Deployment root: PASS — /home/user/Reports
Checked 21 required paths.

$ python governance/scripts/governance/validate_project_state.py
PROJECT STATE: PASS

$ python governance/scripts/governance/validate_evidence.py
EVIDENCE VALIDATION: PASS
Checked 161 REQUIRED PASS evidence record(s).

$ python governance/scripts/governance/validate_reference_integrity.py
REFERENCE INTEGRITY: FAIL
Quét 267 file .md (loại trừ 10 file trong governance/reference/history/, docs/audit/).
3 reference không phân giải được:
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md
```

**Ba reference này là BASELINE ĐÃ BIẾT, và đã chạy lại trên base để xác nhận**
— đúng yêu cầu của brief ("chỉ được ghi là baseline khi chạy lại trên base xác
nhận cùng lỗi"). Chúng thuộc `TASK-REM-T06`, không liên quan R4, và R4 không
thêm reference hỏng nào.

### 4.2 Test tập trung sau các gói lớn

```text
$ python -m pytest -q tests/test_business_boundaries.py tests/test_business_metrics.py \
    tests/test_business_vertical.py tests/test_employee_workspace_ux.py \
    tests/test_uiux_refinement.py tests/test_r2_web_workflow.py \
    tests/test_r3_web_workflow.py tests/test_r3_export_and_period_close.py \
    tests/test_web_server.py
300 passed in 23.60s

$ python -m pytest -q tests/test_r4_evaluation_metrics.py tests/test_r4_evaluation_web.py
88 passed in 5.75s
```

### 4.3 Full regression CUỐI CÙNG

```text
$ python -m pytest -q
3146 passed, 12 skipped in 180.91s (0:03:00)
```

`3146 − 3058 = 88` bài mới, `0` bài hồi quy.

### 4.4 Validator/gate sau khi sửa

```text
$ python governance/scripts/governance/validate_structure.py
GOVERNANCE STRUCTURE: PASS

$ python governance/scripts/governance/validate_project_state.py
PROJECT STATE: PASS

$ python governance/scripts/governance/validate_evidence.py
EVIDENCE VALIDATION: PASS

$ python governance/scripts/governance/validate_reference_integrity.py
REFERENCE INTEGRITY: FAIL — ĐÚNG BA reference của TASK-REM-T06 như baseline,
không thêm reference hỏng nào.

$ bash scripts/branch_authority_check.sh
(kết quả ở §7)
```

### 4.5 Điều 88 bài mới thật sự chứng minh

`tests/test_r4_evaluation_metrics.py` (50 bài, giá trị thuần):

- công thức ba chỉ tiêu dẫn xuất; mẫu số 0; biên ÂM; biên > 100 %;
- bất biến "có số ⟺ không có lý do" chạy trên MỌI ô của MỌI tình huống, và
  `Kpi(...)` vi phạm bất biến raise `ValueError`;
- cổng coverage: bốn ô bị chặn cùng lúc, con số một phần ở `partial_value`,
  doanh thu KHÔNG bị chặn theo;
- lịch: tính cả hôm nay, tháng đã qua đo tới ngày cuối, tháng chưa tới không
  có `as_of`, ngày cuối tháng còn 0 ngày;
- target: không cap; unset ≠ zero; MỘT PHẦN ≠ chưa có gì; còn thiếu/ngày; hết
  tháng KHÔNG chia cho 0 và cũng KHÔNG nói thành "đã đạt";
- run-rate: bốn cửa từ chối, mọi mã thuộc tập đóng;
- so cùng số ngày: cắt hai vế; tháng trước NGẮN HƠN cắt cả hai ở ngày ngắn
  hơn; kỳ trước rỗng; kỳ trước bằng 0; dòng không ngày bị loại VÀ được đếm;
- bảng đóng góp: phân hoạch cộng lại bằng tổng; cột Đơn KHÔNG cộng dọc (2 đơn
  thật, cộng cột ra 3); hàng thiếu coverage không có biên mà có LÝ DO; xếp
  biên chỉ nhận hàng đã có biên; bucket "chưa phân loại" không bị bỏ;
- chiết khấu: cộng ngược đúng một lần; dòng "Chiết khấu" cũ KHÔNG bị đếm vào
  cột `discount`; đơn ghi cả hai cách bị NÊU TÊN;
- dòng lỗ: thiếu giá ≠ bán lỗ; phạm vi đã xét;
- provenance: tổng các nhóm bằng số dòng; `POLICY_ZERO` không bị gộp vào
  `PENDING`.

`tests/test_r4_evaluation_web.py` (38 bài, qua route Flask thật): ba luồng
nghiệm thu của Owner, cộng đối soát dashboard-vs-detail, kỳ đã chốt + drift,
và một bài chứng minh trang không ghi gì.

---

## 5. Smoke qua route web THẬT

Server Flask thật trên `127.0.0.1:8099` (không phải test client), dữ liệu tổng
hợp, giả lập hôm nay = `08/09/2026` nên tháng 09/2026 là **tháng đang chạy**.
Sổ có 4 dòng tháng 09 (một dòng THIẾU GIÁ, một dòng LỖ, một dòng có chiết
khấu) và 2 dòng tháng 08 (ngày 02 và ngày 28).

### (C) Coverage thiếu giá — KHÔNG công bố lợi nhuận một phần

```text
GET /kinh-doanh/danh-gia?ky=2026-09          → 200
  eval-sales_revenue         = 23.500        (nghìn đồng)
  eval-orders                = 4
  eval-kpi_profit            = —
  eval-margin_percent        = —
  eval-profit_per_order      = —
  eval-converted_sales       = —
  quality-verdict            = CHƯA ĐỦ
  quality-coverage           = 3 / 4 dòng
  kpi_profit reason          = PROFIT_NOT_OFFICIAL
  converted reason           = CONVERTED_NOT_OFFICIAL
  phần đã tính (bằng chứng)  = "Đã tính được: 5.500 nghìn đồng — đây là phần
                                đã biết, KHÔNG phải kết quả cả kỳ."
```

Bốn chỉ tiêu phụ thuộc lợi nhuận đều `—`, mỗi ô có mã lý do; con số một phần
`5.500` hiện làm BẰNG CHỨNG chứ không ở vị trí kết quả. Doanh thu và số đơn
vẫn có số — chúng không phụ thuộc giá nhập.

### (A) KPI/insight → drill-down đúng, tổng KHỚP

```text
   4 dòng  <- /kinh-doanh/gia-nhap?ky=2026-09&loc=tat-ca
   1 dòng  <- /kinh-doanh/gia-nhap?ky=2026-09&loc=thieu-gia
   4 dòng  <- ...&loc=tat-ca&nhom=noi-thanh
   0 dòng  <- ...&loc=tat-ca&nhom=gia-dung
   1 dòng  <- ...&loc=tat-ca&mat-hang=d38c7fad…
   1 dòng  <- ...&loc=tat-ca&mat-hang=8e66512d…
   1 dòng  <- ...&loc=tat-ca&mat-hang=a98b9f40…
   1 dòng  <- ...&loc=tat-ca&mat-hang=1adc8712…
   4 dòng  <- ...&loc=tat-ca&nhom-hang=DIEN_MAY
   4 dòng  <- ...&loc=tat-ca&nguon=PERSONAL
   1 dòng  <- ...&loc=co-chiet-khau
   1 dòng  <- ...&loc=lo

Σ drill-down theo mặt hàng = 4  ==  bảng kê cả kỳ = 4   → KHỚP
Nhãn phạm vi trên bảng kê mở ra: "TL200"
```

Mỗi con số trên trang mở ra đúng tập dòng của nó; tổng các drill-down theo mặt
hàng bằng đúng số dòng của kỳ; bảng kê NÓI RA phạm vi nó vừa thu hẹp về.

### (B) Tháng đang chạy + target + so CÙNG NGÀY kỳ trước

Nhập nốt giá cho dòng còn thiếu, qua ĐÚNG route POST thật:

```text
POST /kinh-doanh/gia-nhap  (gia_nhap=2.000.000)   → 200

GET /kinh-doanh/danh-gia?ky=2026-09
  as-of                      = Số tính đến 08/09/2026
  elapsed-days / month-days  = 8 / 30
  eval-sales_revenue         = 23.500
  eval-kpi_profit            = 6.500
  eval-margin_percent        = 27,66%      (6.500 / 23.500)
  eval-profit_per_order      = 1.625       (6.500 / 4 đơn)
  eval-converted_sales       = 325.000     (6.500.000 / 2 %)
  quality-verdict            = ĐỦ
  quality-coverage           = 4 / 4 dòng
  revenue-run-rate-value     = 88.125      (23.500 / 8 ngày × 30 ngày)

  compare-window             = ngày 01–08 của cả hai tháng
  compare-current            = 23.500
  compare-previous           = 6.000
  compare-percent            = +291,67%

GET /kinh-doanh/danh-gia?ky=2026-09&nhom=noi-thanh
  target-value               = 600.000
  target-percent             = 54,17%      (325.000 / 600.000)
  target-shortfall           = 275.000
  target-days-remaining      = còn 22 ngày (30 − 8)
  target-required-per-day    = 12.500      (275.000 / 22)
  target-run-rate-value      = 1.218.750

  target ở phạm vi "Cả kỳ"   = KHÔNG có (đúng — không có target công ty)
```

**Bằng chứng quan trọng nhất của luồng này:** tháng 08 có một dòng
`30.000.000` bán ngày **28/08**. Nó KHÔNG lọt vào mốc so sánh — `compare-
previous = 6.000` chỉ gồm dòng ngày 02/08. Nếu cửa sổ so sánh sai, con số này
sẽ là `36.000` và tỉ lệ sẽ là `−34,7 %` thay vì `+291,67 %`.

### (D) Kỳ đã chốt, drift, và chặn ghi

```text
POST /kinh-doanh/chot-ky      → 200
  quality-closed = "Kỳ ĐÃ CHỐT (lần 1) — trang này hiển thị dữ liệu hiện hành
                    của kỳ đã chốt"
  drift          = no
POST /kinh-doanh/gia-nhap (sửa giá sau khi chốt)  → TỪ CHỐI HTTP 409 (đúng)
```

### (E) Bảng thẩm quyền giá + giới hạn MIN nói ra

```text
  min-status-note   = "Trạng thái FINAL/PROVISIONAL của giá MIN theo ngày
                       KHÔNG được lưu lại trên từng dòng… Muốn có
                       FINAL/PROVISIONAL theo dòng thì phải lưu thêm nó lúc
                       nạp sổ; đó là một thay đổi ở đường nhập, ngoài phạm vi R4."
  price-source rows = ['4']     (tổng bằng đúng 4 dòng của kỳ)
```

---

## 6. Một repair, và vì sao nó KHÔNG phải scope creep

`_today()` trả `date.today()` — ngày theo đồng hồ MÁY CHỦ. Container
production chạy UTC, nên **từ 17:00 giờ Việt Nam tới nửa đêm** hàm trả về NGÀY
HÔM TRƯỚC.

Không có triệu chứng: không ngoại lệ, không cờ, không đổi màn hình. Nhưng
`as_of` lệch một ngày làm "còn thiếu mỗi ngày" chia sai, cửa sổ "cùng số ngày
lịch" lệch, và tháng mặc định của không gian làm việc sai vào tối ngày cuối
tháng — nghĩa là một Target có thể được ghi vào THÁNG SAI.

Phân loại theo `xác suất × tác động × khả năng nhân viên phát hiện`: xác suất
CAO (bảy giờ mỗi ngày), tác động THẬT (số sai + ghi vào kỳ sai), phát hiện
KHÓ. Trúng cả ba tiêu chí "PHẢI repair" của brief. Nay đọc theo
`Asia/Ho_Chi_Minh` — cùng chuỗi vùng mà `daily-min-v1` đã freeze cho ranh giới
ngày của giá MIN, để ngày bán và ngày báo cáo cắt theo cùng một ranh giới.

Chi tiết: `docs/tasks/R4-bao-cao-danh-gia.md` §5.

Mọi thứ khác đã được cân nhắc và KHÔNG sửa — xem `AR-R4-01` … `AR-R4-03`.

---

## 7. Branch authority

```text
$ bash scripts/branch_authority_check.sh
=== BRANCH AUTHORITY CHECK (Governance V4.1 Machine Control #1) ===
fetch                : OK (origin --prune)
DEFAULT_REMOTE_REF   : refs/remotes/origin/claude/extract-upload-repo-gq2ws4
DEFAULT_BRANCH       : claude/extract-upload-repo-gq2ws4
DEFAULT_TIP          : 824b5d742dab07b8b0bd301d56748779e35076aa
HEAD_SHA             : ea6413d16ecef3345dc8561cc8a085684269c686
WORKTREE             : CLEAN
MODE                 : BRANCH
CURRENT_BRANCH       : claude/r4-reports-evaluation-u3vs4d
UPSTREAM             : origin/claude/r4-reports-evaluation-u3vs4d
behind upstream      : 0 commit
ahead  upstream      : 0 commit
ahead  default       : 2 commit
behind default       : 0 commit
divergence days      : 0
cumulative LOC       : 4826
DIVERGENCE           : WITHIN_LIMITS

AUTHORITY            : BRANCH_WITH_UPSTREAM
RESULT               : AUTHORITY_OK
```

`ea6413d` là commit TÀI LIỆU (`86cee40` mã nguồn + đúng một commit doc-only),
cùng khuôn đã dùng cho R3. Reviewer nên chạy lại trên chính commit mình review
thay vì tin bản chép lại ở đây.

---

## 8. Giới hạn — nói ra, không giấu

1. **Deploy Render/migration `0009` không xác nhận được từ phiên này** (không
   credential, egress bị chặn). R4 không có migration nên không phụ thuộc điều
   đó, nhưng Owner vẫn phải hoàn tất checklist `S130` §6–§7.
2. **Không đối soát trên dữ liệu nghiệp vụ THẬT.** Khác `S129` (R3 đối soát
   trên hai kỳ golden đã ẩn danh), phiên này chạy trên dữ liệu TỔNG HỢP. Lý do
   an toàn được: R4 không tính lại con số nào — mọi chỉ tiêu cộng được vẫn do
   `business_metrics.totals` cho ra, và các bài golden của R3 vẫn xanh. Nhưng
   điều đó KHÔNG chứng minh hình dạng dữ liệu thật (số mặt hàng, phân bố nguồn
   đơn, kích thước bảng) đọc được trên màn hình thật. Owner nên mở trang trên
   một kỳ thật trước khi nghiệm thu.
3. **`MIN FINAL/PROVISIONAL` không có** — `AR-R4-01`.
4. **"Nguồn đơn" là phân loại SUY RA của pipeline**, không phải kênh bán do
   người nhập chọn — `AR-R4-02`.
5. **Xếp hạng biên giới hạn 5 hàng** và không có ngưỡng "biên thấp" nào. Đây
   là lựa chọn có chủ đích (ngưỡng là quyết định của Owner), không phải một
   thiếu sót.
6. **`AR-R3-05`/`AR-R3-06` của R3 vẫn mở** và R4 không đóng chúng.

---

## 9. Trạng thái và việc còn lại

```text
R4 STATUS = IMPLEMENTED
            CHECK-R4-01 … CHECK-R4-22 = PASS (E1)
            CHECK-R4-23 (Independent Review)  = NOT_TESTED
            CHECK-R4-24 (Owner nghiệm thu)    = NOT_TESTED
            Full regression: 3146 passed, 12 skipped
            (baseline trước R4 cùng môi trường: 3058 passed, 12 skipped)
            Migration: KHÔNG CÓ. Route ghi mới: KHÔNG CÓ.

R3 CHECK-R3-20 (Owner nghiệm thu) = NOT_TESTED — R4 KHÔNG chạm tới nó.
```

Phiên này KHÔNG tự đánh dấu Owner Acceptance của R3 hay R4, và KHÔNG chuyển R4
sang `VERIFYING` hay `DONE`.

---

## 10. Checklist nghiệm thu rút gọn cho Owner

Mở `/kinh-doanh` → bấm **MỞ BÁO CÁO ĐÁNH GIÁ**.

1. **Một KPI và một insight.** Bấm vào Doanh thu, rồi bấm một hàng của bảng
   "theo mặt hàng". Bảng kê mở ra phải đúng tập dòng, và tổng phải khớp con số
   vừa bấm. Bảng kê phải NÓI RA phạm vi nó đang thu hẹp về.
2. **Tháng đang chạy ở phạm vi có target.** Chọn một sheet có target (ví dụ
   Nội thành). Kiểm `% target`, `còn thiếu`, `cần đạt mỗi ngày còn lại`, và
   khối "So với tháng trước" — nó phải ghi rõ **"ngày 01–NN của cả hai
   tháng"**. Kiểm dòng `Số tính đến DD/MM/YYYY` ở đầu trang và đơn vị *nghìn
   đồng* ở mỗi ô tiền.
3. **Một kỳ còn thiếu giá.** Mở một kỳ chưa đủ coverage (hoặc bỏ giá tay của
   một dòng). Trang phải nói `CHƯA ĐỦ`, và **Lợi nhuận KPI · Biên KPI · Lãi/đơn
   · DS quy đổi đều phải là `—`** kèm lý do. Nếu bất kỳ ô nào trong bốn ô đó
   hiện một con số, đó là lỗi — báo lại ngay.

Ba điều Owner nên tự kiểm thêm: (a) hàng TỔNG của mỗi bảng bằng con số đầu
trang; (b) trang không có nút nào sửa được số; (c) mở một kỳ ĐÃ CHỐT và xác
nhận trang nói đúng trạng thái chốt.

**Không session nào được đánh dấu `CHECK-R4-24` thay Owner.**
