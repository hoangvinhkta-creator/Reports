# TASK-105B-RC-1 — CODEX INDEPENDENT REVIEW

Review ID: TASK-105B-RC-1-CODEX

Task / Release: TASK-105B PRICE-PARSER MICRO-HARDENING — HB-105B-07 + HB-105B-08

Reviewer Session: Codex independent review

Executed By: Codex

Timestamp: 2026-08-28T12:07:35+0700

## Phạm vi

Rà soát E2 độc lập chỉ cho repair sau freeze đã được cấp thẩm quyền.

- Frozen implementation base: `c22cef8b47ac4cd71ef49609066a362c9e604313`
- Repair code SHA: `7f7048d65619c2c2198c99ccbfb073d6cb97ebe2`
- Repair final/docs SHA: `b672f78bf45a08253e9aafb04bd8b4717b9c473e`

Review không thay đổi `app/**`, `tests/**`, hay `config/**`; không merge,
re-freeze, integrate, khởi động TASK-105C, hay thay đổi Tracking.

## Tài liệu đầu vào đã đọc

- `CLAUDE.md` (điểm vào governance canonical)
- `governance/core/V4_1_POLICY_FREEZE.md`
- `governance/core/EVIDENCE_STANDARD.md`
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/PROJECT_DECISIONS.md` (`DEC-153`)
- `PROJECT/REVIEW_BUDGET_LEDGER.md`, `PROJECT/LO_TRINH_DE_HIEU.md`
- `docs/tasks/TASK-105B-file-price-provider.md`
- `docs/reviews/TASK-105B-INDEPENDENT-REVIEW-RECONCILIATION.md`

`DEC-153` cấp thẩm quyền cho repair cycle mới của đúng HB-105B-07/HB-105B-08.
V4.1 §3 tính đây là một cycle theo cumulative repair diff, không theo số review.

## Tính toàn vẹn target và diff

```text
git cat-file -t 7f7048d65619c2c2198c99ccbfb073d6cb97ebe2 → commit
git cat-file -t b672f78bf45a08253e9aafb04bd8b4717b9c473e → commit
git rev-parse origin/task/task-105b-price-parser-hardening → b672f78bf45a08253e9aafb04bd8b4717b9c473e
git branch -r --contains 7f7048d65619c2c2198c99ccbfb073d6cb97ebe2 → origin/task/task-105b-price-parser-hardening
```

Exact repair target và remote ref đã được xác minh. So với integrated default
trước repair (`89948df42b510e27b80a9a7902e3c07d4a7066e7`), commit mã chỉ sửa
`app/modules/pricing/file_price_provider.py` (+7) và
`tests/test_file_price_provider.py` (+120). Commit final chỉ thay đổi bốn file
state/evidence: `PROJECT/LO_TRINH_DE_HIEU.md`, `PROJECT/PROJECT_PROGRESS.md`,
`PROJECT/REVIEW_BUDGET_LEDGER.md`, và `docs/tasks/TASK-105B-file-price-provider.md`.
Golden fixture/expected output không đổi. `git diff --check 89948df..b672f78` sạch.

## Xác minh độc lập

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| RC1-PREFIX-07 | PASS | E2 | Tại frozen `c22cef8`, `Decimal("NaN")` thoát ra thành `decimal.InvalidOperation`. | Codex | 2026-08-28T12:07:35+0700 |
| RC1-PREFIX-08 | PASS | E2 | Tại frozen `c22cef8`, `Decimal("Infinity")` được nhận và `lookup()` trả `Decimal('Infinity')`; `-Infinity` báo sai reason `negative_price`. | Codex | 2026-08-28T12:07:35+0700 |
| RC1-IMPLEMENTATION | PASS | E2 | `_parse_price()` parse sang Decimal, chặn `not price.is_finite()` bằng `InvalidPriceMasterError(reason="non_finite_price")`, rồi giữ nguyên check negative-price. Normalization, effective-date, provenance, finite lookup không đổi. | Codex | 2026-08-28T12:07:35+0700 |
| RC1-ADVERSARIAL | PASS | E2 | NaN và ±Infinity qua string, float, Decimal (9 case) đều raise `InvalidPriceMasterError` reason `non_finite_price`; không case nào được nhận hoặc làm lộ `decimal.InvalidOperation`. | Codex | 2026-08-28T12:07:35+0700 |
| RC1-FINITE | PASS | E2 | Decimal dương, zero, `1E+1000`, `1E-1000` load/lookup không đổi; negative hữu hạn vẫn `InvalidPriceMasterError(reason="negative_price")`. | Codex | 2026-08-28T12:07:35+0700 |
| RC1-TARGETED | PASS | E2 | Python 3.11.16: `pytest -q tests/test_file_price_provider.py` → `59 passed in 0.19s`; 26 case mới bao phủ class, reason, representations, YAML loading, no lookup result và finite controls. | Codex | 2026-08-28T12:07:35+0700 |
| RC1-GOLDEN | PASS | E2 | Python 3.11.16: `pytest -q tests/test_golden_baseline.py` → `58 passed, 2 skipped in 2.37s`; Golden files changed: NO. | Codex | 2026-08-28T12:07:35+0700 |
| RC1-REGRESSION | PASS | E2 | Python 3.11.16: `pytest -q` → `756 passed, 11 skipped in 5.82s`, đúng +26 passed, không failure/new skip. Lần thử Python 3.12 kích hoạt đúng environment guard Python 3.11 nên không được coi là product evidence. | Codex | 2026-08-28T12:07:35+0700 |
| RC1-SAFETY | PASS | E2 | `PendingPriceProvider` vẫn là pipeline default; `FilePriceProvider` không có caller ngoài module; RC-1 không thêm production code TASK-105C hay thay đổi Tracking/Firebase. | Codex | 2026-08-28T12:07:35+0700 |
| RC1-GOVERNANCE | PASS | E2 | Validator structure, project state, task completion, evidence đều PASS. Reference integrity chỉ báo ba reference TASK-REM-T06 tiền tồn (README, CODE_OF_CONDUCT, CONTRIBUTING), không có RC-1 reference regression. | Codex | 2026-08-28T12:07:35+0700 |

## Phân loại finding

| Finding | Disposition | Căn cứ |
|---|---|---|
| HB-105B-07 | RESOLVED | NaN bị chặn trước so sánh, qua canonical exception và reason `non_finite_price`. |
| HB-105B-08 | RESOLVED | Infinity dương/âm bị chặn trước acceptance/negative validation, qua canonical exception và reason `non_finite_price`. |

`HB-105B-03`, `HB-105B-05`, `HB-105B-06`, `HB-105B-10` không đổi, không mở
lại. `HB-105B-09`/`HB-105B-11` vẫn superseded. `HB-105B-01`/`HB-105B-02` vẫn
là finding TASK-108B tiền tồn, không liên quan.

## Finding mới

- BLOCKING: không có.
- HARDENING: không có finding nào do repair này tạo hoặc phơi lộ một cách trọng yếu.
- OUT_OF_SCOPE: không có.

## Repair budget và transition bắt buộc

Canonical ledger ghi TASK-105B là HIGH: trước RC-1 `2 allowed / 0 used / 2
remaining`; sau mở RC-1 `2 allowed / 1 used / 1 remaining`. Independent review
này không tiêu thêm cycle theo V4.1 §3.

DEC-153 xác nhận RC-1 là repair mechanism hợp lệ sau freeze. Sau PASS này,
next authorized action là controlled integration riêng của repair lineage đã
review vào default branch, rồi state reconciliation theo governance. Reviewer
không thực hiện transition đó, không re-freeze TASK-105B và không cấp phép
TASK-105C.

## Lệnh đã thực thi

```text
git status --short --branch
git remote -v
git cat-file -t <repair-code-sha>
git cat-file -t <repair-final-sha>
git rev-parse origin/task/task-105b-price-parser-hardening
git branch -r --contains <repair-code-sha>
git diff c22cef8..7f7048d -- app/modules/pricing/file_price_provider.py tests/test_file_price_provider.py
git diff 7f7048d..b672f78
git diff --check 89948df..b672f78
pytest -q tests/test_file_price_provider.py
pytest -q tests/test_golden_baseline.py
pytest -q
governance/scripts/governance/validate_{structure,project_state,task_completion,evidence,reference_integrity}.py
scripts/branch_authority_check.sh
```

## Kết luận

PASS — REPAIR VERIFIED

Mọi non-finite value được chỉ định nay thỏa canonical exception contract;
hành vi hữu hạn và frozen provider contract vẫn nguyên vẹn. Không phát hiện
BLOCKING finding.
