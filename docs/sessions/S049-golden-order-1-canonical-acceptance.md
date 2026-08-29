# S049 — Golden Order #1 Canonical Acceptance — Session Handoff

Kế tiếp `S048` (TASK-105D INV-81/INV-82 Evidence Closure, `TASK-105D = DONE`,
`DEC-162`). Phiên hẹp, **không phải implementation session**: mục tiêu duy
nhất là persist Golden Order #1 (Owner-confirmed, `BH62063`) thành canonical
`END_TO_END_ACCEPTANCE` / vertical-slice business oracle trong repo, với
thay đổi nhỏ nhất có thể.

Branch / Base SHA:
`governance/golden-order-1-canonicalize`, base = HEAD của `S048`
`ae1e17cd7977db795ae3dfb884090c779bc9032d`.

## Xác minh Git lineage trước khi sửa

```text
$ bash scripts/branch_authority_check.sh
DEFAULT_BRANCH       : claude/extract-upload-repo-gq2ws4
DEFAULT_TIP          : 7464ccaa784f13d887b2d5441d86136ff7d9a61d
HEAD_SHA             : ae1e17cd7977db795ae3dfb884090c779bc9032d
WORKTREE             : CLEAN
CURRENT_BRANCH       : governance/golden-order-1-canonicalize
UPSTREAM             : origin/governance/golden-order-1-canonicalize
behind upstream      : 0 commit
ahead  upstream      : 0 commit
ahead  default       : 5 commit
behind default       : 0 commit
DIVERGENCE           : WITHIN_LIMITS
AUTHORITY            : BRANCH_WITH_UPSTREAM
RESULT               : AUTHORITY_OK
```

Khớp đúng expected của brief S049 (branch, HEAD, working tree clean). Nhánh
mặc định thật (`claude/extract-upload-repo-gq2ws4`) đứng SAU nhánh này (0
commit behind, 5 ahead) — không có rủi ro trùng lặp công việc kiểu DEC-118;
đã kiểm tra `PROJECT/PROJECT_PROGRESS.md` trên nhánh mặc định, không có task nào
làm trùng.

## Tóm tắt thay đổi

```text
PROJECT/PROJECT_PROGRESS.md   — CAP-PRICE-RESOLUTION → END_TO_END_ACCEPTANCE
    cập nhật tại chỗ: PENDING_OWNER_DATA → DEFINED, điền đầy đủ toạ độ
    Owner-confirmed cho BH62063 (identity, price source "Tồn" + guard,
    Public Purchase fallback, giá, oracle, provenance). Thêm khối "Trạng
    thái sau GOLDEN ORDER #1 CANONICAL ACCEPTANCE (S049)" + "HÀNH ĐỘNG KẾ
    TIẾP ĐƯỢC PHÉP (S049 → …)" theo đúng pattern các session trước
    (S045…S048). Thêm câu VERTICAL_SLICE_IMPACT declaration rule cho các
    session kế tiếp trên critical path.
PROJECT/PROJECT_DECISIONS.md  — DEC-163 (Owner Decision ghi nhận chuyển
    PENDING_OWNER_DATA → DEFINED, đầy đủ 9 điều khoản: toạ độ Owner-confirmed,
    "Tồn" semantic guard, Public Purchase fallback-only, identity guard hẹp
    cho BH62063, price unit guard, Golden relationship, TASK-105D remains
    DONE, no new task, critical path kế tiếp = AS-IS trace).
docs/sessions/S049-golden-order-1-canonical-acceptance.md — bản ghi này.
```

`app/`, `config/`, `Tracking` — 0 byte đổi. Không sửa file test nào. Không
tạo file dưới `docs/tasks/` hay `docs/reviews/` (brief cấm task spec mới và
review report lớn cho phiên hẹp này).

## Owner-confirmed data (Golden Order #1)

```text
OrderID                   : BH62063
SaleDate                  : 2026-01-02
RawProductName            : "Máy giặt LG 10kg FV1410S4W1"
TrackingCode               : FV1410S4W1
PublicPurchaseCode         : FV1410S4W1
CrossSystemIdentityConfirmed : YES (Owner-confirmed cho đúng đơn này)
ExpectedCanonicalIdentity  : TRACKING:FV1410S4W1
ExpectedPriceSource        : "Tồn"  (TECHNICAL_SOURCE_MAPPING = UNRESOLVED)
ApplicablePriceDate        : 2026-01-02
ExpectedPurchasePrice      : 7.000.000 VND
PublicPurchaseFallback     : AUTHORIZED (chỉ khi preferred price path
                              không có giá phù hợp — KHÔNG phải preferred)
Quantity                   : 1
SellPrice                  : 7.500.000 VND
Discount                   : 0 VND
ExpectedEligibleKpiProfit  : 500.000 VND
```

Công thức: `EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity −
Discount = (7.500.000 − 7.000.000) × 1 − 0 = 500.000 VND`.

## Kết quả

```text
END_TO_END_ACCEPTANCE : PENDING_OWNER_DATA → DEFINED
TASK-105D              = DONE (không đổi, không reopen, DEC-162 giữ nguyên)
```

## Validation

```text
$ python3 governance/scripts/governance/validate_structure.py
GOVERNANCE STRUCTURE: PASS

$ python3 governance/scripts/governance/validate_project_state.py
PROJECT STATE: PASS

$ python3 governance/scripts/governance/validate_evidence.py
EVIDENCE VALIDATION: PASS

$ python3 governance/scripts/governance/validate_task_completion.py
TASK COMPLETION: PASS — Checked 7 DONE task(s).

$ python3 governance/scripts/governance/validate_reference_integrity.py
REFERENCE INTEGRITY: FAIL — 3 reference không phân giải được
    (docs/tasks/TASK-REM-T06-repository-root-hygiene.md → /README.md,
    CODE_OF_CONDUCT.md, CONTRIBUTING.md)
```

3 issue trên là **PRE-EXISTING BASELINE** — xác nhận đúng 3 issue, không có
issue mới, không sửa trong `S049` (thuộc phạm vi `TASK-REM-T06`, không thuộc
`CAP-PRICE-RESOLUTION`).

```text
$ python3 -m pytest tests/test_golden_baseline.py -q
58 passed, 2 skipped

$ python3 -m pytest -q
965 passed, 11 skipped
```

Khớp tuyệt đối con số tham chiếu trước `S049` — 0 regression, vì `S049`
không sửa `app/`, `config/`, `Tracking`, hay bất kỳ file test nào.

## Task Registry — bằng chứng BEFORE/AFTER

```text
SET A (REGISTERED_TASK_SET, PROJECT_PROGRESS.md) BEFORE = 13   AFTER = 13
SET B (TASK_SPEC_SET, docs/tasks/*.md)            BEFORE = 22   AFTER = 22
new_registered_task_ids = 0
```

## Không làm trong phiên này (theo brief S049)

- Không chạy `BH62063` qua production pipeline.
- Không sửa pricing, identity resolver, KPI.
- Không triển khai `TASK-105C`/`TASK-105E`/`TASK-108B`.
- Không thực hiện V4.2 adoption.
- Không tạo task mới.
- Không merge nhánh `governance/golden-order-1-canonicalize` vào nhánh mặc
  định.

## Bàn giao cho phiên kế tiếp

**S050 — GOLDEN ORDER #1 AS-IS VERTICAL TRACE**

```text
Order          : BH62063
Target oracle  : KpiPurchasePrice = 7.000.000 VND
                 EligibleKpiProfit = 500.000 VND
Next operation : RUN CURRENT SYSTEM AS-IS
Determine      : FIRST_FAILING_BOUNDARY
```

Không tự gán trước `TASK-105C`/`TASK-105E`/`TASK-108B` là bước kế tiếp —
chỉ AS-IS execution mới xác nhận boundary thật. Technical source mapping
cho `"Tồn"` (hiện `UNRESOLVED`) cũng là việc của session AS-IS, dựa trên
boundary phát hiện được, không phải giả định trước.
