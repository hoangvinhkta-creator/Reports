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

## 5. ĐÍNH CHÍNH giữa phiên — `DEC-219` sai

Sau khi ghi `DEC-219` (mục 2), phiên phát hiện: `CHECK-R6-30`/`CHECK-R6-32`/
`CHECK-R51-26` và `INTEGRATION_DECISION_REQUIRED` của `R6` **đã đóng đúng
từ trước** — `DEC-210` (2026-09-09, MỘT NGÀY TRƯỚC phiên này) đã đóng cả
bốn mục với bằng chứng E1 thật (đối soát trực tiếp trên sổ Owner, khớp 8/8
chỉ tiêu) và đã merge `R6` vào nhánh mặc định (commit `865b58e`). Nguyên
nhân: `docs/tasks/R6-dashboard-phan-tich-kinh-doanh.md` và mục "Root Task:
R6" của `PROJECT/REVIEW_BUDGET_LEDGER.md` chưa từng được đồng bộ lại sau khi
`DEC-210` thực thi — phiên này đọc narrative cũ đó mà không tìm
`PROJECT/PROJECT_DECISIONS.md` trước. Đã đính chính tường minh (`DEC-219` §0),
khôi phục đúng `PASS`/`DONE` ở mọi file liên quan. `R6` chuyển
`Status: DONE`.

Owner sau đó xác nhận thêm bằng lời `CHECK-R5-28` (Owner nghiệm thu `R5`
gốc) — mục này KHÔNG bị ảnh hưởng bởi sai sót trên, ghi tại `DEC-220`.

## 6. Merge `R5.3` vào nhánh mặc định — Owner chỉ thị trực tiếp

Owner chọn lựa chọn (A) (xác nhận lại quyết định đã có sẵn ở `DEC-210`) và
chỉ thị merge `R5.3` vào nhánh mặc định ngay (`R6` không cần merge lại — đã
có sẵn từ `DEC-210`).

**Đồng bộ nhánh trước khi merge** (đúng "Đồng Bộ Nhánh" của `CLAUDE.md`):
`git fetch origin claude/extract-upload-repo-gq2ws4` phát hiện nhánh mặc
định đã tiến thêm 8 commit kể từ `c46e458` — lineage `UI-01/UI-02` (panel
sửa đơn tại chỗ, PR #15, `6c77961`), không liên quan `R5`/`R6`/`R7`. Merge
`origin/claude/extract-upload-repo-gq2ws4` vào nhánh làm việc, xung đột DUY
NHẤT ở `PROJECT/PROJECT_PROGRESS.md` (hai mục canonical chèn cùng vị trí đầu file)
— giải quyết bằng cách giữ NGUYÊN cả hai mục, không mất nội dung nào. Tiện
sửa luôn một link tài liệu hỏng có sẵn từ nhánh `UI-01/UI-02`: 3 chỗ trong
`PROJECT/REVIEW_BUDGET_LEDGER.md` thiếu tiền tố thư mục trước tên file
policy freeze, nay sửa thành đường dẫn đầy đủ
`governance/core/V4_1_POLICY_FREEZE.md`.

```text
$ git merge-base --is-ancestor 865b58e c46e458 && echo OK   # R6 đã ở default
OK

$ pip3 install -e ".[dev,web,history,storage]"   # môi trường thiếu sẵn dependency
$ python3 -m pytest -q
1 failed, 3627 passed, 24 skipped   # TestG25GoldenBaselineUnchanged, "bad object
                                    # 740f396a" — ĐÚNG lỗi môi trường clone nông đã
                                    # biết từ S150 (không phải regression thật)

$ git fetch --unshallow
$ python3 -m pytest -q tests/test_105d_boundaries.py::TestG25GoldenBaselineUnchanged
3 passed   # xác nhận đúng nguyên nhân

$ python3 -m pytest -q   # chạy lại đầy đủ sau unshallow
3628 passed, 24 skipped, 0 failed in 261.40s

$ python3 governance/scripts/governance/validate_structure.py .        # PASS
$ python3 governance/scripts/governance/validate_project_state.py .    # PASS
$ python3 governance/scripts/governance/validate_evidence.py .         # PASS (161 record)
$ python3 governance/scripts/governance/validate_task_completion.py .  # PASS (14 task)
$ python3 governance/scripts/governance/validate_reference_integrity.py .
# 4 finding — ĐÚNG 4 baseline cũ

$ git diff --check
(rỗng — sạch)

$ git merge-base --is-ancestor origin/claude/extract-upload-repo-gq2ws4 HEAD && echo OK
OK   # fast-forward an toàn, không mất commit nào

$ git push origin claude/r5-3-owner-accepted-risk-find01:claude/extract-upload-repo-gq2ws4
   6c77961..5cfd000  claude/r5-3-owner-accepted-risk-find01 -> claude/extract-upload-repo-gq2ws4
```

**Merge ĐÃ THỰC HIỆN.** Nhánh mặc định (`claude/extract-upload-repo-gq2ws4`)
giờ tại `5cfd000`, mang đầy đủ: `R5.3` (implementation + Independent Review
+ `DEC-218` ACCEPTED_RISK), đính chính `DEC-219`, `DEC-220` (`CHECK-R5-28`),
và `R6`/`UI-01-UI-02` đã có sẵn. Render tự động build+deploy ngay sau push
này (Blueprint tự kích hoạt theo `render.yaml`) — phiên KHÔNG có
egress/credential tới Render nên KHÔNG xác nhận được deploy đã Live, cùng
giới hạn đã ghi nhận xuyên suốt các phiên merge trước (`S127`/`S130`/`S133`/
`S137`).

## 7. Trạng thái cuối

- `R5.3`: `IMPLEMENTED` (KHÔNG tự chuyển `DONE`), `CHECK-R53-13 =
  ACCEPT_WITH_RECORDED_RISK`, **đã merge vào nhánh mặc định**.
  `CHECK-R53-14` (Owner nghiệm thu trên production, SAU khi deploy xong)
  vẫn `NOT_TESTED` — chỉ Owner đóng được, để lại cho phiên/thời điểm sau.
- `R6`: `DONE` (đính chính trong phiên này, theo đúng `DEC-210` đã có từ
  trước) — đã merge, đã deploy từ `DEC-210`.
- `R5` (gốc): `CHECK-R5-28` → `ACCEPTED_BY_OWNER_VERBAL` (`DEC-220`). VẪN
  `IMPLEMENTED`, không tự chuyển `DONE` (xác nhận bằng lời, không phải
  bằng chứng E1/E2).

## 8. Việc còn lại cho session sau

1. Owner tự nghiệm thu `CHECK-R53-14` trên production thật, SAU khi xác
   nhận Render đã deploy xong bản `5cfd000` (upload sổ → `/run` → tab Nhân
   viên → chờ một lần restart → mở lại, không chạy lại).
2. Không còn việc nào khác treo cho `R5.3`/`R6` sau khi `CHECK-R53-14`
   đóng — `R5.3` khi đó đủ điều kiện xét `DONE`.
