# S151 — Owner Decision: `FIND-R53-01` ACCEPTED_RISK + đóng ba check Owner Acceptance

Ngày: 2026-09-10
Nhánh: `claude/r5-3-owner-accepted-risk-find01` (dựng từ tip
`claude/r5-3-reports-metadata-review-8bp6be` @ `8c8ac34` — chuỗi review thật
của `R5.3` — để tránh phân nhánh tài liệu governance, đúng "Đồng Bộ Nhánh"
của `CLAUDE.md`).
Task Mode: MICRO (chỉ sửa tài liệu governance, không sửa mã sản phẩm).
Thực hiện bởi: Claude Code, qua trao đổi trực tiếp với Owner trong phiên.

## 0. Bối cảnh

Independent Review của `R5.3` (nhánh `claude/r5-3-reports-metadata-review-8bp6be`,
HEAD `cb7639f88efa8c9fb24f414ac1b6d9f93e58f02e`) kết luận `REPAIR_REQUIRED`:
`FIND-R53-01` — đường đọc bản chiếu nhãn (`_tracking_display`/
`latest_tracking_display`) không phân biệt theo `run_id`/kỳ. Lineage `R5`
đã hết ngân sách repair-cycle (2/2, 0 remaining) nên phiên review escalate
theo `governance/core/ESCALATION_PROTOCOL.md` thay vì tự mở repair cycle
thứ ba, trình ba hướng: `OWNER_EXTENSION`, `ACCEPTED_RISK` mới, mở lineage
riêng. Chi tiết đầy đủ: `docs/reviews/R5-3-INDEPENDENT-REVIEW-RECORD.md`.

Trong phiên này, Owner (qua trao đổi) yêu cầu:
1. Đánh giá lại `FIND-R53-01` với bối cảnh vận hành thật (danh sách nhân
   viên/mã hàng do phần mềm kế toán quản lý, không gõ tay tự do).
2. Chọn `ACCEPTED_RISK` sau khi được cho xem bằng chứng code cụ thể.
3. Xác nhận bằng lời đã tự nghiệm thu `CHECK-R6-30`, `CHECK-R6-32`,
   `CHECK-R51-26` trên production/sổ thật.

## 1. Bằng chứng dẫn tới `DEC-218` (`FIND-R53-01` → `ACCEPTED_RISK`)

Đọc trực tiếp Tracking commit `1c36fa2` ("R5.2.3: ẩn tạm 4 cột
Hashtag/Phân khúc/Nhóm hàng/Hãng, gọn nút Chuẩn hoá thành icon", cùng ngày
2026-09-10, SAU HEAD mà Independent Review đã chốt):

```text
$ git -C Tracking show --stat 1c36fa2
 kiem/bang-gia-cot-gon.js   | 138 ++++++++++++++++++++++++++-------------------
 kiem/r52-bulk-chuan-hoa.js |  11 +++-
 public/index.html          | 115 +++++++++++++++----------------------
```

Xác nhận trực tiếp trong file kiểm (`kiem/bang-gia-cot-gon.js`, phần "3)"):
- `boardRow()` KHÔNG còn gọi `ed("hashtag"/"pk", ...)` hay `r52Cell()` — ô
  Nhóm hàng/Hãng không còn dựng trong DOM.
- `data-viec="editR52"` — 0 kết quả trong toàn bộ HTML (handler mở popover
  sửa tay đã mất chỗ gọi).
- `editR52()`/`commitR52()` còn trong mã nguồn nhưng "không còn ô nào gọi
  tới vì cột đã ẩn" (nguyên văn commit message) — code chết.

Đọc `public/index.html:3623` (`r52ApDungBackfill`, dùng bởi nút tự động
"↻ Chuẩn hoá Nhóm/Hãng" — đường DUY NHẤT còn sống có thể đổi brand/category):

```js
const catManual   = cur.category_provenance === 'manual';
const brandManual = cur.brand_provenance === 'manual';
...
if(!catManual && goiY.category_label){ outCat = goiY.category_label; ... }
if(!brandManual && goiY.brand){ outBrand = goiY.brand; ... }
```

Hàm này tự loại trừ mọi mã đã có provenance `manual` — không bao giờ ghi đè
một mã đã từng khoá tay. Kết luận: điều kiện để `FIND-R53-01` xảy ra thật
trong quy trình vận hành hiện tại của Owner cần CẢ BA: mã còn provenance
`auto`, dữ liệu hashtag/category nguồn của nó bị sửa nơi khác, và ai đó
bấm lại nút Chuẩn hoá sau đó — đường sửa tay trực tiếp (chắc chắn kích hoạt
finding) không còn tồn tại trong UI.

**Quyết định:** `DEC-218` — `ACCEPTED_RISK`, ghi rõ đây là đánh giá lại xác
suất theo bằng chứng vận hành mới, KHÔNG phải hạ nhẹ vì lý lẽ kế thừa (lý
lẽ đó đã bị Independent Review bác tường minh). Cơ chế lỗi trong code không
đổi.

## 2. `DEC-219` — ba check Owner Acceptance

Owner tự xác nhận bằng lời trực tiếp trong phiên: đã đối soát `CHECK-R6-30`
trên sổ thật `So_chi_tiet_ban_hang.xlsx` (file không có trong repo, `DEC-108`),
đã nghiệm thu `CHECK-R6-32` (R6 trên production) và `CHECK-R51-26` (R5.1
trên production). Không có số liệu/ảnh chụp cụ thể đính kèm vào phiên — ghi
nhận đúng bản chất: `ACCEPTED_BY_OWNER_VERBAL`, đúng cơ chế đã dùng cho
`CHECK-R3-20`/`CHECK-R4-24` ở `DEC-203`, KHÔNG phải `PASS` với bằng chứng
E1/E2 trong repo.

`INTEGRATION_DECISION_REQUIRED` (`V4.1` §8, `R6`, cumulative LOC `10.155` >
ngưỡng `5.000`) KHÔNG nằm trong phạm vi `DEC-219` — vẫn MỞ, độc lập, vẫn
chặn merge của `R6`. `CHECK-R5-28` (Owner nghiệm thu `R5` gốc) và
`CHECK-R53-14` (Owner nghiệm thu `R5.3`) cũng KHÔNG nằm trong `DEC-219`.

## 3. File đã sửa

```text
PROJECT/PROJECT_DECISIONS.md                                  DEC-218, DEC-219
PROJECT/PROJECT_PROGRESS.md                                   canonical state mới
PROJECT/REVIEW_BUDGET_LEDGER.md                                Root Task R5 + R6
docs/tasks/R5-3-nhan-hang-nhom-hang-song-qua-restart.md        CHECK-R53-13, AR-R5.3-01, Exit Criteria
docs/tasks/R5-1-nhom-hang-category-label.md                    CHECK-R51-26
docs/tasks/R5-1-REPAIR-2-run-refreshes-catalog-display.md      CHECK-R51-26 (tham chiếu)
docs/tasks/R6-dashboard-phan-tich-kinh-doanh.md                CHECK-R6-30, CHECK-R6-32, Completion Gate
```

Không file mã nguồn (`app/`, `tests/`) nào bị đổi. `git diff --check` sạch
(xem §4).

## 4. Kiểm chứng

```text
$ git diff --check
(rỗng — sạch)

$ python3 governance/scripts/governance/validate_structure.py .
$ python3 governance/scripts/governance/validate_project_state.py .
$ python3 governance/scripts/governance/validate_evidence.py .
$ python3 governance/scripts/governance/validate_task_completion.py .
```

(output đầy đủ — xem lệnh chạy trong phiên; không finding mới ngoài baseline
`reference_integrity` đã biết từ trước).

## 5. Trạng thái cuối

- `R5.3`: `IMPLEMENTED`, `CHECK-R53-13 = ACCEPT_WITH_RECORDED_RISK`,
  `CHECK-R53-14` vẫn `NOT_TESTED`. Được phép tiếp tục sang merge/deploy.
- `R6`: `IMPLEMENTED`, ba check Owner Acceptance đã đóng bằng
  `ACCEPTED_BY_OWNER_VERBAL`, nhưng KHÔNG chuyển `DONE` —
  `INTEGRATION_DECISION_REQUIRED` vẫn MỞ, vẫn chặn merge.
- `R5` (gốc): `CHECK-R5-28` vẫn `NOT_TESTED`.
- Không merge, không deploy trong phiên này.

## 6. Việc còn lại cho session sau

1. Owner chọn hướng cho `INTEGRATION_DECISION_REQUIRED` của `R6` (V4.1 §8):
   (A) merge sớm, (B) cắt scope, (C) tiếp tục divergence có lý do + ngày
   review.
2. Merge `R5.3` (branch `claude/r5-3-reports-brand-category-j37izs`, đã
   `ACCEPT_WITH_RECORDED_RISK`) vào nhánh mặc định, deploy, rồi Owner nghiệm
   thu `CHECK-R53-14` trên production thật.
3. `CHECK-R5-28` (Owner nghiệm thu `R5` gốc) vẫn treo — chưa ai xử lý.
