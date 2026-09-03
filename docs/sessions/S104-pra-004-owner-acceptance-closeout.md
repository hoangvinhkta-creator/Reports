# S104 — TASK-PRA-004 Owner Production Acceptance + Final Closeout

## Metadata

Task: `TASK-PRA-004` — `docs/tasks/TASK-PRA-004-ban-hang-review-detail.md`

Task Mode: MAJOR

Session type: Owner Production Acceptance + Final Closeout (docs/state only,
KHÔNG implementation, KHÔNG sửa production code)

Canonical branch: `claude/extract-upload-repo-gq2ws4`

`BASE_CANONICAL = eb26f7b9500144290069171fc168926ccb2c70d1` — khớp EXACT kỳ
vọng đầu phiên. `CANONICAL_MOVED = KHÔNG`.

---

## Xác Minh Thẩm Quyền (đầu phiên)

- `git fetch origin claude/extract-upload-repo-gq2ws4` → `eb26f7b9500144290069171fc168926ccb2c70d1`.
- Local HEAD của session (`claude/pra-004-owner-acceptance-qbyxl1`) = 0
  ahead / 0 behind so với canonical.
- Working tree sạch trước khi bắt đầu.

---

## Bối Cảnh — Phiên Trước (Owner Production Evidence, một phần)

Một phiên trước trong cùng lineage đã thu thập bằng chứng Owner quan sát
trực tiếp trên production (`reports.tinphatcrm.com/ban-hang?ky=2026-09`):

- Danh sách đơn: **40 đơn**.
- Chi tiết đơn AUTO `BH73844` và đơn TRỘN `BH73877` (xem chi tiết dưới).
- Kết luận tại thời điểm đó: `CHECK-PRA004-14 = NOT_PROVEN` vì ba con số còn
  lại của oracle FROZEN PRA-003 (61 dòng / 15 AUTO / 25 CẦN KIỂM TRA) chưa
  được chứng minh trực tiếp trên production — session không có kết nối
  read-only tới production database để tự đối chiếu, và không được phép suy
  luận từ mẫu quan sát.

---

## Bằng Chứng Owner Ghi Lại (bổ sung) — CHECK-PRA004-14

### Bước 1-3, mục 21 — Danh sách + bốn con số tổng

Owner mở `/ban-hang?ky=2026-09` trên production thật, sau đó dùng DevTools
trình duyệt trên đúng trang danh sách đó để đếm TRỌN VẸN bảng đơn đã render
đầy đủ (không phải suy luận từ mẫu):

```
orders = 40
lines  = 61
auto   = 15
review = 25

Đồng nhất thức phân hoạch: 15 + 25 = 40   (INV-4)
```

Bốn con số này khớp ĐÚNG với oracle FROZEN đã được Owner tự tay nghiệm thu ở
`TASK-PRA-003` (mục 3, mục 20 hợp đồng PRA-004 — PRA-004 tái dụng CHÍNH bốn
con số đó, không phát minh oracle mới).

### Bước 4-6, mục 21 — Mở đơn, drill-down xuống dòng

**CASE A — `BH73844` (AUTO):**

```
Ngày bán 01/09/2026 · Nhân viên Hiệp · 1 dòng · SL 1
Doanh thu 9.550.000
LN KPI 100.000 (coverage 1/1) · LN kế toán 100.000 (coverage 1/1)
Trạng thái đơn: AUTO

Dòng: Máy giặt LG FX1412N5G
  SL 1 · đơn giá 9.550.000 · chiết khấu 0 · doanh thu dòng 9.550.000
  giá vốn kế toán 9.450.000 · giá vốn KPI 9.450.000
  LN kế toán 100.000 · LN KPI 100.000 · trạng thái dòng: AUTO
```

Σ doanh thu dòng = doanh thu đơn (INV-1); Σ số lượng dòng = tổng SL đơn
(INV-2). Không lý do cần kiểm tra nào hiện ra, khớp trạng thái AUTO.

**CASE B — `BH73877` (TRỘN, CẦN KIỂM TRA):**

```
Ngày bán 01/09/2026 · Nhân viên Ly · 3 dòng · SL 3
Doanh thu 32.800.000
LN KPI 456.667 (coverage 2/3) · LN kế toán 590.000 (coverage 2/3)
Trạng thái đơn: CẦN KIỂM TRA

Dòng 1 — Máy giặt Electrolux EWF1143R7SC (CẦN KIỂM TRA)
  SL 1 · đơn giá 13.450.000 · chiết khấu 66.667 · doanh thu dòng 13.383.333
  giá vốn / lợi nhuận: — (chưa biết, KHÔNG hiện 0)
  Lý do (5 mã, tiếng Việt):
    - Chưa nhận diện sản phẩm
    - Thiếu giá mua tham chiếu
    - Thiếu giá nhập kế toán
    - Thiếu lợi nhuận kế toán
    - Thiếu lợi nhuận KPI

Dòng 2 — Máy sấy bơm nhiệt Electrolux EDH903R7SC (AUTO)
  giá vốn kế toán 18.100.000 · giá vốn KPI 18.100.000
  LN kế toán 250.000 · LN KPI 183.333

Dòng 3 — Kệ máy giặt đa năng inox (AUTO)
  giá vốn kế toán 860.000 · giá vốn KPI 860.000
  LN kế toán 340.000 · LN KPI 273.334
```

Coverage một phần (2/3 dòng) hiện tường minh trên cả hai loại lợi nhuận —
đúng INV-7. Giá trị chưa biết hiện `—`, không hiện `0`/`0đ` — đúng INV-6.
Lý do đọc được bằng tiếng Việt, không lộ từ vựng nội bộ — đúng ranh giới đã
verify E2 tại CHECK-PRA004-09/12.

### Bước 7, mục 21 — Reconcile với Tổng quan

`/tong-quan?ky=2026-09` và `/ban-hang?ky=2026-09` cho CÙNG một tập: 40 đơn ·
61 dòng · 15 AUTO · 25 cần kiểm tra. Không freeze thêm giá trị tiền nào của
09/2026 làm oracle mới — các giá trị Owner đọc được ngoài bốn con số trên
giữ nhãn `OBSERVED_ONLY` đúng theo mục 21.

### Bước 8, mục 21 — PII

Owner không quan sát thấy IMEI, tên khách, số điện thoại, địa chỉ, hay ghi
chú thô ở bất kỳ đâu trên hai trang mới.

---

## BH62439 — Reconciliation Vai Trò Bằng Chứng

`BH62439` là oracle KỸ THUẬT (Oracle C, mục 20.3 hợp đồng), đã verify E2 tại
`CHECK-PRA004-03` và `CHECK-PRA004-12` trên dữ liệu golden persisted qua
đường production thật (`run_import_production` → `history_writer`). Nó
**KHÔNG tồn tại** trong dữ liệu production 09/2026 — điều này ĐÚNG, vì
`BH62439` thuộc fixture golden `period_2026_01`, không thuộc kỳ 09/2026.

Phân loại: `BH62439_ROLE = TEST_GOLDEN_ORACLE`, KHÔNG phải bản ghi production
bắt buộc. Vắng mặt của nó trên production 09/2026 là
`EVIDENCE_ROLE_RECONCILIATION` (đúng vai trò bằng chứng, không phải phát
hiện lỗi), KHÔNG làm thay đổi một chữ nào trong oracle kỹ thuật đã freeze.
Owner Production Acceptance dùng `BH73844`/`BH73877` — hai bản ghi production
thật — làm bằng chứng vertical, đúng phạm vi mục 21 (Owner thao tác trên
production thật, không phải golden fixture).

---

## CHECK-PRA004-14 — Kết Luận

Cả 8 bước của mục 21 hợp đồng đã có kết quả Owner ghi lại trên production
thật. Bốn con số 40/61/15/25 khớp ĐÚNG với oracle FROZEN của PRA-003. Không
giá trị tiền nào khác của 09/2026 bị đóng băng ngược thành oracle mới (giữ
`OBSERVED_ONLY`).

**`CHECK-PRA004-14 = PASS` (E1).**

Cập nhật chi tiết đầy đủ tại `docs/tasks/TASK-PRA-004-ban-hang-review-detail.md`
→ `CHECK-PRA004-14`.

---

## Completion Gate — Kiểm Tra Toàn Bộ

```
CHECK PASS      = 14/14  (13/13 REQUIRED · 1/1 RECOMMENDED)
CHECK-PRA004-12  = PASS (E2, S102, không đụng lại)
CHECK-PRA004-14  = PASS (E1, S104 — mục này)
BLOCKING_FINDINGS = 0
```

Exit Criteria (`docs/tasks/TASK-PRA-004-ban-hang-review-detail.md` →
"Tiêu Chí Hoàn Thành") — 9/9:

1. 13/13 REQUIRED PASS với evidence level bắt buộc — ĐẠT (CHECK-14 vừa đóng).
2. 0 BLOCKING finding; mọi HARDENING/DEFER có RE-TRIGGER CONDITION — ĐẠT
   (FIND-PRA004-05/06/07/08 giữ nguyên, không repair).
3. CHANGE_BUDGET không vượt DỪNG CỨNG — ĐẠT (đo tại S102, không đổi; phiên
   này 0 production delta).
4. Review budget không vượt 1 blocking repair cycle — ĐẠT (`0/1` used, xem
   `PROJECT/REVIEW_BUDGET_LEDGER.md` → "Root Task: TASK-PRA-004" → S104).
5. Golden Baseline `58 passed, 2 skipped`; full suite không giảm; validators
   giữ nguyên baseline (3 issue REM-T06 đã biết) — ĐẠT, bảo tồn từ E2 (S102),
   KHÔNG chạy lại full suite trong phiên docs-only này (mục 16 chỉ thị: không
   cần rerun full product suite chỉ vì đóng docs).
6. Toàn bộ test PRA-003 PASS NGUYÊN VẸN, không sửa — ĐẠT (không chạm test).
7. `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`,
   `PROJECT/REVIEW_BUDGET_LEDGER.md` đã cập nhật — ĐẠT (phiên này).
8. Session handoff đã viết — ĐẠT (file này).
9. `SCHEMA_CHANGE=0`, `MIGRATION=0`, `INDEX=0`, `DEPENDENCY=0`, `CONFIG=0`,
   `TRACKING_CHANGED=NO`, `INFRASTRUCTURE_CHANGED=NO`,
   `PROTECTED_CORE_IMPACT=NONE` — ĐẠT (0 file production/test bị chạm).

**`TASK-PRA-004 = DONE`.**

---

## Finding — Trạng Thái Cuối

```
FIND-PRA004-04  = RECONCILED (S103, không mở lại)
FIND-PRA004-09  = RECONCILED (S103, không mở lại)
FIND-PRA004-05  = HARDENING / DEFER, RE-TRIGGER CONDITION giữ nguyên
FIND-PRA004-06  = HARDENING / DEFER, RE-TRIGGER CONDITION giữ nguyên
FIND-PRA004-07  = HARDENING / DEFER, RE-TRIGGER CONDITION giữ nguyên
FIND-PRA004-08  = HARDENING / DEFER, RE-TRIGGER CONDITION giữ nguyên
```

Không finding nào được mở thành task mới trong phiên này.

---

## Ngân Sách

```
repair_cycles_used      = 0 / 1
repair_cycles_remaining = 1 / 1
```

Owner Production Acceptance là bằng chứng đóng một REQUIRED check đã có sẵn
trong Completion Gate FROZEN, KHÔNG phải một vòng sửa lỗi ⟹ không tiêu
repair cycle.

---

## Validators (proportionate — docs/state closeout only)

```
validate_structure.py           → PASS
validate_project_state.py       → PASS
validate_evidence.py            → PASS
validate_task_completion.py     → PASS
validate_reference_integrity.py → FAIL đúng 3 issue REM-T06 pre-existing,
                                   0 issue mới
git diff --check <BASE>..HEAD   → sạch
branch_authority_check.sh       → xem ghi chú dưới
```

Ghi chú `branch_authority_check.sh`: nhánh làm việc của session
(`claude/pra-004-owner-acceptance-qbyxl1`) chưa có upstream trên origin tại
thời điểm chạy script (script báo `BRANCH_AUTHORITY_UNRESOLVED`, exit 2) —
đây là tình trạng "chưa từng push", không phải lệch nội dung; canonical đã
được verify khớp EXACT thủ công qua `git fetch` + so SHA trước khi bắt đầu.
Sau khi push nhánh closeout, tình trạng này tự hết theo bước fast-forward
canonical bên dưới.

---

## Ràng Buộc Đã Tuân Thủ

- KHÔNG sửa bất kỳ file `app/`, `tests/`, `tools/`, `config/` nào.
- KHÔNG sửa `governance/core/V4_1_POLICY_FREEZE.md`.
- KHÔNG mở lại `FIND-PRA004-04`/`-09` (giữ RECONCILED).
- KHÔNG repair `FIND-PRA004-05/06/07/08`.
- KHÔNG mở `TASK-PRA-005` implementation.
- KHÔNG sửa `docs/reviews/TASK-PRA-004-INDEPENDENT-REVIEW-RECORD.md` (bằng
  chứng lịch sử của S102, giữ nguyên).

`PRODUCTION_CODE_DELTA = 0`. File bị chạm trong phiên này: task file +
`PROJECT/PROJECT_PROGRESS.md` + `PROJECT/LO_TRINH_DE_HIEU.md` +
`PROJECT/REVIEW_BUDGET_LEDGER.md` + file session này — toàn bộ đều là
docs/state.

---

## Việc Tiếp Theo

`TASK-PRA-005 DISCOVERY` — chưa mở trong phiên này, đúng theo hard exclusion
của chỉ thị.
