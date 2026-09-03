# RÀ SOÁT ĐỘC LẬP E2 (E2 INDEPENDENT REVIEW) — TASK-PRA-002 TOÀN TASK

Review ID:
PRA-002-WHOLE-TASK-REVIEW-1

Task / Release:
TASK-PRA-002 — Pipeline Persistence + Overlapping Snapshot Reconciliation
(slice A + slice B + slice C1 + Real Data Acceptance, đối chiếu với Completion
Gate FROZEN tại S079)

Reviewer Session:
S092 — Independent Review E2 cấp toàn task (nhánh
`claude/pra-002-rda-continuation-814n4h`, docs-only)

Executed By:
S092 — TASK-PRA-002 Whole-Task Independent Review E2 (2026-09-03)

Timestamp:
2026-09-03

Evidence Level:
E2 — mọi kết luận chức năng đều do reviewer tự chạy lại trong phiên (SQLite qua
test suite + PostgreSQL 16.13 thật, cô lập, local). Phần chỉ đọc mã được ghi rõ
là suy luận tĩnh. Bằng chứng RDA trên workbook thật (S090/S091) được review
theo provenance, KHÔNG rerun (workbook thật không có trong phiên này).

## Scope

Independent Review E2 cấp TOÀN TASK để quyết định `CHECK-PRA002-17`. Không
implementation, không RDA mới, không deploy, không Production Acceptance,
không migration/schema, không Tracking, không parser expansion, không A2/A3,
không B2/B3/B4, không REM-T06, không refactor/hardening/tooling mới.

### Authority — xác minh TRƯỚC khi đọc bất kỳ file governance nào

```text
ORIGIN HEAD BRANCH        = claude/extract-upload-repo-gq2ws4
CANONICAL_EXPECTED_SHA    = d7a1154a2892e5869e286e10da49f750aa0611df
CANONICAL_ACTUAL_SHA      = d7a1154a2892e5869e286e10da49f750aa0611df   → KHỚP, canonical KHÔNG moved
RDA_EVIDENCE_BRANCH       = claude/pra-002-rda-continuation-814n4h
RDA_EVIDENCE_HEAD         = 14499dd6e8f193c5656b85c47b7181a169e32709   (== expected 14499dd)
merge-base(RDA, canonical)= d7a1154a…  → RDA branch = canonical + 3 commit (1927965, f5ea80c, 14499dd)
Diff canonical..14499dd   = 4 file, TOÀN BỘ docs (PROJECT/PROJECT_PROGRESS.md, docs/sessions/S090-*.md,
                            docs/sessions/S091-*.md, docs/tasks/TASK-PRA-002-*.md); 0 file ngoài docs/ + PROJECT/
                            → 14499dd = DOCS-ONLY (xác minh bằng git diff --name-only)
branch_authority_check.sh = AUTHORITY_OK (BRANCH_WITH_UPSTREAM; ahead 3 / behind 0; DIVERGENCE WITHIN_LIMITS)
git diff --check          = sạch (d7a1154..14499dd và working tree)
```

Canonical = production-code authority; RDA branch = evidence/docs authority.
Không dùng RDA branch làm implementation base.

## Tài Liệu Đầu Vào Đã Đọc (Inputs Read)

- `docs/tasks/TASK-PRA-002-pipeline-persistence-reconciliation.md` (frozen
  contract S079: mục 3–15, gate 19, CHANGE_BUDGET 17, deferred 18, slices 20).
- `PROJECT/PROJECT_PROGRESS.md` (khối S091 closeout, S091, S090, S088, S087).
- `PROJECT/REVIEW_BUDGET_LEDGER.md` → "Root Task: TASK-PRA-002".
- `docs/reviews/TASK-PRA-002-SLICE-{A,B,C1}-INDEPENDENT-REVIEW-RECORD.md`.
- `docs/sessions/S090-*.md`, `docs/sessions/S091-*.md` (RDA evidence).
- Mã production tại canonical: `app/history/{keys,models,reconciler,coverage,
  extraction}.py`, `app/web/history_store.py`, `app/web/history_writer.py`,
  delta `app/web/server.py`, `app/demo.py`, `app/modules/exporting/
  excel_exporter.py`, `tools/db/{__init__,schema}.py`,
  `tools/db/migrations/versions/0002_snapshots.py`.
- `governance/core/V4_1_POLICY_FREEZE.md` (review budget, repair cycle).

## Implementation Lineage (xác minh bằng git)

```text
BASE_SHA (freeze S079)      = 553d8a36f578b082128a6e45d2748da2bc371e70
Slice A  : 7fad3f7 → 80c6fe1 (impl) → b0ecab7 (E2 + repair cycle 1) → 86f26a0 → 27b9d1c (integration)
Slice B  : 27b9d1c → 7658c5e (impl) → d2c7691 (E2 ACCEPT) → bfe7008 (integration)
Slice C1 : bfe7008 → 3cd92ea (impl) → 579b497 (E2 ACCEPT) → d7a1154 (integration close-out, docs only)
Sau accepted C1 (579b497..d7a1154): diff app/ + tools/ = RỖNG → KHÔNG có production code sau C1
Production diff BASE_SHA..canonical: 17 file (app/demo.py, app/history/*, exporter alias, history_store,
   history_writer, server.py, 3 template, tools/db/__init__.py, 0002_snapshots.py, schema.py)
   — đúng Touch Area mục "Phạm Vi Tác Động"; app/modules/** chỉ có alias exporter (+5 dòng thô, 2 dòng logic)
```

## Completion Gate Matrix (lập từ frozen task TRƯỚC khi đánh giá)

Phân loại nguồn: `OWNER` = OWNER_DECISION · `FROZEN` = frozen inference của
contract · `IMPL` = implementation · `TEST` = test evidence (SQLite/PG) ·
`REAL` = real-data evidence (S090/S091) · `CC` = controlled-copy evidence.

| Check | REQUIRED | Nguồn thẩm quyền | Reviewer tái lập (E2) | Kết quả |
|---|---|---|---|---|
| 01 Migration up/down + DDL PG | YES | FROZEN mục 13 | `alembic upgrade head` trên 3 DB PostgreSQL 16.13 → `0002_snapshots`; downgrade `0001_legacy` → 5 bảng, upgrade lại → 11 bảng | PASS |
| 02 Một upload → snapshot + v1 + result v1 + current | YES | FROZEN mục 4/6 | PG: A 89/61, B 351/254, `SUM(total_sales)` = 3.562.310.000 | PASS |
| 03 Upload lại → SAME, 0 double-count | YES | OWNER 3.2 | PG: B reupload SAME 351, `duplicate_of` đúng, source version không tăng, current identical, result +351 | PASS |
| 04 Overlap A ⊂ B đẳng thức | YES | OWNER 3.1 + FROZEN 11.5 | PG: `state(A,B) == state(B)` trên totals VÀ tập (khoá, fingerprint) 351; đảo thứ tự SAME 89 / INSERT 0 | PASS |
| 05 SOURCE_CHANGED giữ version cũ, changed_fields, current mới | YES | OWNER 3.2 + FROZEN 5.3 | PG: BH62063 v1 (snapshot A, changed_fields NULL) / v2 (B'), `{sell_price, total_sales_raw}` 7500000→8500000, flag from 1 → to 352, delta +1.000.000 đúng | PASS |
| 06 Coverage state machine + xác nhận tường minh | YES | OWNER 3.3 + FROZEN 7.3 | PG qua route web production: 400 thiếu tick · 400 khoảng không bao DETECTED (nêu ngày lệch) · 302 hợp lệ → CONFIRMED_COMPLETE · 409 lần 2; `confirmed_by` NULL; persist sau restart PostgreSQL | PASS |
| 07 NOT_SEEN vs REMOVED_CANDIDATE, không xoá, vẫn tính | YES | OWNER 3.2 + FROZEN 8 bước 4/R | PG: B'' → 1 NOT_SEEN (BH64081, scope DETECTED); xác nhận → 1 REMOVED (scope CONFIRMED); dòng vẫn current, totals không đổi; COUNT(*) mọi bảng fact không giảm; xác nhận A cho 01–10 → REMOVED 0; dòng quay lại → `is_active` False dẫn xuất, cờ cũ giữ nguyên (append-only) | PASS |
| 08 RESULT_REVISED | YES | OWNER 3.2 + FROZEN 6 | PG: PENDING→AUTO cùng source → SAME 2, n_source_changed 0, n_result_revised 1, source pointer giữ, result pointer dịch, from/to là result-version id, detail chỉ F3; rerun y hệt → version +2, 0 cờ; đổi `price_source` → 0 cờ; source + result cùng đổi → chỉ SOURCE_CHANGED; COLLISION → 0 result version, 0 cờ RESULT | PASS |
| 09 Append-only + UNIQUE | YES | FROZEN 9/11 | Suite AST (0 `delete()`, `update()` chỉ `order_line_current` + cột confirm) PASS; PG: 3 mốc COUNT(*) không giảm; version_no sau collision [1,2,3,4] | PASS |
| 10 Fail-closed một đơn vị công việc | YES | FROZEN 11.2/12 | `tests/test_web_history.py` + `test_snapshot_absence.py` rollback tests PASS (SQLite); đọc mã: `on_persisted` trong `engine.begin()` | PASS |
| 11 Golden + regression + exporter parity | YES | FROZEN 14 | Golden `58 passed, 2 skipped`; full suite `1805 passed, 11 skipped` + 1 test môi trường (xem Sai Lệch) → sau unshallow 3/3 PASS; `test_demo.py` 13 PASS | PASS |
| 12 Ranh giới ADR-101 / protected core | YES | FROZEN Touch Area | `test_history_db.py` PASS; diff BASE..canonical không chạm do-not-touch; Tracking không đổi; AUTHORITY_OK | PASS |
| 13 Không PII | YES | FROZEN 10 | `test_no_pra002_table_declares_a_customer_column` PASS; extraction không mang PII; docs RDA quét không có SĐT/địa chỉ | PASS |
| 14 Real Data Acceptance RDA-1..6 | YES | FROZEN 15 + OWNER (xác nhận coverage, cho phép D14) | Review provenance S090/S091 (không rerun); xem mục RDA bên dưới | PASS (E1, review E2 provenance) |
| 15 Production Acceptance Render | YES | FROZEN 16 | Owner deploy; phiên không có egress; không deploy trong review | NOT_TESTED (hợp lệ trong review) |
| 16 Bộ nhớ end-to-end | RECOMMENDED | FROZEN 14 | Số đo S080 75,6 MB / PG 78,7 MB; không đo lại (không thuộc REQUIRED) | PASS (E1, giữ) |
| 17 Independent Review E2 toàn task | YES | FROZEN 19 | Chính bản ghi này; CHECK-03/04/05/07/09 tái lập độc lập trên PostgreSQL thật; `BLOCKING_FINDINGS = 0` | PASS |

## Xác Minh Độc Lập (Independent Verification)

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| Authority / lineage | PASS | E2 | `git rev-parse origin/claude/extract-upload-repo-gq2ws4` = d7a1154a…; `git merge-base` = d7a1154a…; `git diff --name-only d7a1154..14499dd \| grep -vE '^(docs/\|PROJECT/)'` = rỗng; `git diff --stat 579b497..d7a1154 -- app tools` = rỗng | S092 | 2026-09-03 |
| Full suite (SQLite) | PASS | E2 | `python -m pytest tests -q` → `1 failed, 1805 passed, 11 skipped`; lỗi duy nhất `test_105d_boundaries::TestG25GoldenBaselineUnchanged::test_protected_golden_artifacts_match_the_task_105e_review_base` = `fatal: bad object 740f396a…` vì clone shallow (58 commit); sau `git fetch --unshallow` (246 commit) → lớp đó `3 passed` | S092 | 2026-09-03 |
| Golden | PASS | E2 | `tests/test_golden_baseline.py` → `58 passed, 2 skipped in 6.76s` | S092 | 2026-09-03 |
| PRA-002 focused | PASS | E2 | 8 file test (keys, reconciler, coverage_confirmation, snapshot_repository, snapshot_absence, pipeline_history_vertical, web_history, history_db) → `211 passed in 33.24s` | S092 | 2026-09-03 |
| PRA-001 regression | PASS | E2 | legacy importer/repository/source_coverage/web_legacy_routes → `101 passed in 5.90s` | S092 | 2026-09-03 |
| Exporter parity | PASS | E2 | `tests/test_demo.py` → `13 passed` | S092 | 2026-09-03 |
| Migration trên PostgreSQL 16.13 thật | PASS | E2 | `alembic upgrade head` × 3 DB → `alembic_version = 0002_snapshots`; 11 bảng; round-trip downgrade/upgrade trên `rev_misc` (5 → 11 bảng); không có 0003; `assert_schema_current` PASS trên DB đã migrate | S092 | 2026-09-03 |
| CHECK-03/04/05/07 vertical trên PostgreSQL 16.13 (reviewer viết) | PASS | E2 | Script `pg_verify.py` (scratchpad, không commit): A→B→B→B'→B''→confirm trên `rev_ab`; B-only trên `rev_bonly`; đảo thứ tự + narrow confirm; 43/46 assertion PASS, 3 FAIL đều là giả định sai của script (xem Sai Lệch) và được xác minh lại trực tiếp bằng SQL/route → PASS | S092 | 2026-09-03 |
| FIND-PRA002-A1 invariant | PASS | E2 | PG `rev_misc`: collision (gap 91 ngày) → v2 không current; reupload collision → v3; sửa dòng hiện hành → v4 SOURCE_CHANGED current; `version_no` BH1 = [1,2,3,4] (MAX + 1, không phải current + 1); `/run` không 500 | S092 | 2026-09-03 |
| CHECK-08 trên PostgreSQL | PASS | E2 | PG `rev_misc`: 2 capture PENDING→AUTO → n_result_revised 1, flag from/to ∈ id space `order_line_result_version`, source pointer giữ, result cũ PENDING đọc lại được; identical rerun 0 cờ; outside-F3 0 cờ; precedence SOURCE_CHANGED | S092 | 2026-09-03 |
| Route web trên PostgreSQL | PASS | E2 | `create_app(history=LegacyRepository(engine), snapshots=SnapshotRepository(engine))` (wiring production): `/du-lieu` 200 liệt kê snapshot · `/nhan-vien` 200 · trang snapshot 200 · POST xac-nhan-du 400/400/302/409 · nhãn "ĐÃ XÁC NHẬN ĐẦY ĐỦ", form ẩn sau xác nhận | S092 | 2026-09-03 |
| Persistence sau restart PostgreSQL | PASS | E2 | `pg_ctl restart` rồi `SELECT coverage_state, confirmed_range_*, confirmed_at, confirmed_by` → `CONFIRMED_COMPLETE, 2026-01-01, 2026-01-31, …, NULL` | S092 | 2026-09-03 |
| Reappearance / `is_active` | PASS | E2 | PG `rev_ab`: upload lại B sau B'' → BH64081 quay lại; cờ NOT_SEEN + REMOVED giữ nguyên (3 → 4 cờ, chỉ +1 SOURCE_CHANGED do BH62063 về giá cũ), `is_active = False`, `seen_again_in_snapshot_id` = snapshot mới; totals về 3.562.310.000 | S092 | 2026-09-03 |
| LOC budget | PASS | E2 | Script đếm theo phương pháp đã hiệu chuẩn (git diff -U0, bỏ trắng/comment/docstring qua AST): A +1104 · B +289 · C1 +67 · lineage 7fad3f7..d7a1154 = +1460 · BASE_SHA 553d8a3..d7a1154 = +1460 · RDA d7a1154..14499dd = +0 → 1.460 / 1.500, còn 40 | S092 | 2026-09-03 |
| Validators | PASS (1 pre-existing) | E2 | structure / project_state / task_completion / evidence PASS; `reference_integrity` FAIL đúng 3 lỗi pre-existing `TASK-REM-T06` (README/CODE_OF_CONDUCT/CONTRIBUTING) → DEFER như S085/S088 | S092 | 2026-09-03 |
| PII trong docs RDA | PASS | E2 | grep SĐT/địa chỉ/`+84`/`0\d{9}` trên S090/S091 → 0 kết quả PII (chỉ snapshot id) | S092 | 2026-09-03 |

Số đo E2 chính trên PostgreSQL 16.13 (`rev_ab`):

```text
A            : lines 89  orders 61  total_sales   804.980.000
A,B          : lines 351 orders 254 total_sales 3.562.310.000   == B-only (rev_bonly) trên totals VÀ (khoá, fingerprint)
B reupload   : SAME 351 · duplicate_of = B · source version 351 → 351 · result version +351
B'  (edit)   : SOURCE_CHANGED 1 (BH62063) · changed_fields {sell_price, total_sales_raw} 7500000 → 8500000 · +1.000.000
B'' (drop)   : NOT_SEEN 1 (BH64081) · REMOVED 0 · totals KHÔNG đổi
confirm 01–31: CONFIRMED_COMPLETE · n_removed_candidate 1 · REMOVED 1 (BH64081) · dòng vẫn current · totals KHÔNG đổi
facts        : {snapshot 3, source_version 351, snapshot_line 791, result_version 791, current 351, flag 0}
            → {snapshot 5, source_version 352, snapshot_line 1492, result_version 1492, current 351, flag 3}  (không giảm)
```

## Slice A — kết luận

- INSERT / SAME / SOURCE_CHANGED / COLLISION: đúng bảng 3.2 (đọc
  `reconciler._decide` + PG evidence).
- Append-only source versions: `_insert_source_versions` chỉ INSERT; UNIQUE
  `(khoá, version_no)`; PG COUNT(*) không giảm.
- Result observation mỗi run kể cả SAME (`build_result_lines` 1 dòng/khoá;
  PG result version +351 mỗi reupload).
- Current pointer: PK theo khoá; `_update_current` là nơi UPDATE duy nhất;
  COLLISION không dịch con trỏ.
- Transaction: `engine.begin()` bao trọn đọc CUR → reconcile → ghi → `on_persisted`
  (R2) → commit.
- No-double-count: đẳng thức `state(A,B) == state(B)` tái lập trên PG.
- **FIND-PRA002-A1 còn nguyên**: `CurrentState.next_version_no = max(max_version_no,
  version_no) + 1`; `_load_current` nạp `MAX(version_no)` GROUP BY khoá; PG
  [1,2,3,4] sau collision. Version mới đánh số theo MAX, không theo current.
- A2/A3 (nonblocking đã chấp nhận): không tạo hệ quả nghiệp vụ mới trên
  production path → không mở lại.

## Slice B — kết luận

- `DETECTED_ONLY` / `HEADER_CONSISTENT` / `CONFIRMED_COMPLETE`: tầng thuần
  không bao giờ trả CONFIRMED (test AST + PG); chỉ `confirm_coverage` ghi.
- NOT_SEEN (bước 4, phạm vi DETECTED, tính trước mọi lần ghi) và
  REMOVED_CANDIDATE (bước R, phạm vi CONFIRMED, membership của chính snapshot)
  dùng chung hàm thuần `absent_keys` với 4 loại trừ (có mặt / sale_date NULL /
  ngoài phạm vi / collision).
- Current và analytics không phụ thuộc cờ vắng mặt: PG totals không đổi ở cả
  hai nhánh; `is_active` dẫn xuất khi đọc, cờ bất biến.
- Owner semantic "Ngày D tháng M năm YYYY" = single-day coverage: parser vẫn
  DEFERRED, `CODE_REQUIRED = NO` — đọc mã xác nhận `confirm_coverage` không
  đòi `HEADER_CONSISTENT` (chỉ gọi `confirmation_error`), nên snapshot
  `DETECTED_ONLY` vẫn xác nhận được. Không biến thành blocker.
- B2/B3/B4: DEFER giữ nguyên (không hệ quả nghiệp vụ trên current/totals).

## Slice C1 — kết luận

`result_revisions`: giao của 4 điều kiện đúng frozen (có current result ∧ SAME
∧ không collision ∧ fingerprint khác). F3 = đúng 3 trường
(`RESULT_FIELDS`), `result_fingerprint` normalize Decimal. Cờ dùng result-version
id cả hai đầu (PG xác minh ∈ id space `order_line_result_version`). SOURCE_CHANGED
thắng. Outside-F3 → version ghi đủ, 0 cờ. Source pointer không đổi, result pointer
dịch. Tất cả tái lập trên PostgreSQL thật.

## Real Data Acceptance — review provenance (KHÔNG rerun)

| Mục | Evidence | Loại | Kết luận |
|---|---|---|---|
| Snapshot A thật 01/09 | S090: SHA256 `e1c6cec2…`, 48 dòng / 34 đơn, INSERT 48, reupload SAME 48, `COUNT(version_no>1)=0`, net 468.300.000 khớp oracle `run_import` + footer | REAL | Nhất quán nội bộ: 48 + 48 = 96 result version; snapshot_line 96; flag 0 |
| Snapshot B thật 01/09→03/09 | S091: SHA256 `7b421983…`, header `Từ ngày 01/09/2026 đến ngày 03/09/2026`, 61 dòng / 40 đơn, HEADER_CONSISTENT | REAL | Header ⊇ detected → HEADER_CONSISTENT đúng luật 7.1 |
| A ⊂ B; `state(A,B) == state(B)` | S091: key chỉ ở A = 0; INSERT 13 / SAME 35 / SOURCE_CHANGED 13 (35+13 = 48); `rda_ab` vs `rda_bonly`: totals, keyset 61, (khoá, fingerprint), per-order identical; net 593.550.000 ≠ naive 1.061.850.000 | REAL | Số học khớp: 48 + 13 = 61; 468.300.000 + phần mới ≠ double-count. SAME 35 thay vì 48 là bằng chứng THẬT kế toán sửa 13 dòng (delivery_cost/imei), không phải sai lệch |
| Exact B reupload | S091: SAME 61 = line_count, source version 74 → 74, result 109 → 170, current identical | REAL | 74 = 61 + 13 (v2) đúng; 170 − 109 = 61 đúng |
| Accounting oracle | S090/S091: khớp tuyệt đối oracle pipeline + footer XLSX (SL 71, chiết khấu 200.000, doanh số 593.750.000, net 593.550.000) | REAL | Đúng |
| RESULT_REVISED thật | 0 (capture giá rỗng, mọi dòng PENDING) | REAL | Hợp lệ — bảng mục 15 không bắt buộc real RESULT_REVISED; CHECK-08 có E2 riêng |
| Owner coverage confirmation | S091 §19–20: "Đúng, đây là file đầy đủ 01/09–03/09."; `POST /du-lieu/snapshot/SNAP-20260903021014-7b421983/xac-nhan-du` (2026-09-01 → 2026-09-03, xac_nhan=1) → 302; HEADER_CONSISTENT → CONFIRMED_COMPLETE; confirmed_at 2026-09-03T02:27:08+00:00; n_removed_candidate 0; persist sau PostgreSQL restart | OWNER + REAL | Đúng đường ứng dụng, đúng khoảng, không mở rộng range; REMOVED 0 đúng vì A ⊂ B |
| RDA-4 lớp trường tiền | S091 §22–23: B' = B + sửa BH73722 7.800.000 → 8.000.000; đúng 1 SOURCE_CHANGED; `changed_fields` `{sell_price, total_sales_raw}` "7800000" → "8000000"; v1 vẫn thuộc snapshot B; current v2; SUM 593.550.000 → 593.750.000 = +200.000; 0 cờ khác; source version 74 → 75 | CC (nhãn `CONTROLLED_COPY_EVIDENCE`, SHA256 B' `73b0ba45…`) | Nhãn tường minh; B gốc SHA không đổi; đúng phép biến đổi `--edit-line` của mục 15 (openpyxl, không tạo CLI) |
| RDA-5 | S091 §24: B'' = B' − BH73923; trước xác nhận n_not_seen 1; sau POST xac-nhan-du (01→03/09) n_removed_candidate 1, flag REMOVED (from_version_id 72, scope CONFIRMED); dòng vẫn current, vẫn trong SUM (13.350.000); current 61/40/593.750.000 không đổi; COUNT(*) 6 bảng không giảm qua 4 mốc | CC (SHA256 B'' `b366c545…`) trên nền Owner confirmation THẬT | Frozen D14 cho phép controlled-copy fallback; không đòi deletion tự nhiên |
| RDA-6 | Golden 58/2; cohort S068 vắng → mệnh đề có điều kiện không kích hoạt | REAL | Đọc đúng chữ nghĩa bảng 15 |

Provenance: tất cả trên PostgreSQL 16.13 cô lập (`rda_pra002`, `rda_ab`,
`rda_bonly`), qua route production `POST /run` (`REPORTS_REQUIRE_HISTORY_DB=1`),
không patch production code; workbook thật không commit; SHA256 trước == sau.
Giới hạn được ghi trung thực: đường AUTO không thực thi trên dữ liệu thật
(Tracking secret không có) — không phải defect; PRODUCTION AUTO path thuộc
CHECK-15. Kết luận: evidence hỗ trợ đầy đủ các claim; `CHECK-PRA002-14 = PASS`
được reviewer chấp nhận ở E1 (real data) với review provenance E2.

## Database / Migration

Kiến trúc PostgreSQL production không đổi (`HISTORY_DATABASE_URL`,
`postgresql+psycopg://`, `alembic upgrade head` trong Dockerfile CMD — không
sửa). Migration head = `0002_snapshots`, `down_revision = 0001_legacy`, DDL sinh
từ `schema.PIPELINE_TABLES` (6 bảng đúng mục 4: `source_snapshot`,
`order_line_source_version`, `snapshot_line`, `order_line_result_version`,
`order_line_current`, `reconciliation_flag`; UNIQUE/PK/CHECK đúng frozen). Không
có 0003. Slice B/C1 không thêm migration (tools/db/** không đổi sau slice A —
xác minh bằng LOC per-slice: B và C1 không chạm tools/db).

## LOC Budget (đo lại độc lập)

```text
                         thêm   xoá    net
SLICE A  7fad3f7..27b9d1c 1137    33  +1104   (khớp accepted)
SLICE B  27b9d1c..bfe7008  297     8   +289   (khớp accepted)
SLICE C1 bfe7008..d7a1154   73     6    +67   (khớp accepted)
LINEAGE  7fad3f7..d7a1154 1493    33  +1460
BASE_SHA 553d8a3..d7a1154 1493    33  +1460   (S079 chỉ docs)
RDA      d7a1154..14499dd    0     0     +0
TOTAL = 1.460 / 1.500 → REMAINING = 40 LOC — KHỚP, không mismatch
```

## Review Budget

```text
repair_cycles_allowed   = 2
repair_cycles_used      = 1   (PRA-002-RC-1, FIND-PRA002-A1, slice A)
repair_cycles_remaining = 1
Phiên này                = 0 cycle (không có BLOCKING → không repair)
```

## Sai Lệch So Với Tuyên Bố Của Người Triển Khai (Mismatches With Implementer Claims)

- Không có sai lệch về số liệu: LOC, Golden, focused suite, PG semantics, RDA
  arithmetic đều khớp.
- Ghi nhận môi trường (không phải sai lệch của task): full suite lần đầu
  `1805 passed, 11 skipped, 1 failed` vì clone shallow thiếu commit
  `740f396a…` mà `test_105d_boundaries` dùng làm base so golden; sau
  `git fetch --unshallow` lớp test đó PASS. Tổng tương đương `1806 passed,
  11 skipped` của S087.
- Ba assertion FAIL trong script PG của reviewer là giả định sai của script
  (v1 của khoá trong A thuộc snapshot A chứ không phải B; `str(Decimal.normalize())`
  cho `7.5E+6`; `/nhan-vien` cần legacy repo được nối như production wiring),
  được xác minh lại trực tiếp bằng SQL và route → hệ thống đúng.

## Findings

### BLOCKING
Không có. `BLOCKING_FINDINGS = 0`.

### NON_BLOCKING / DEFER (không mới, không mở lại)
- `FIND-PRA002-A2`, `A3` (slice A) — DEFER, không hệ quả nghiệp vụ trên
  production path.
- `FIND-PRA002-B2` (nhân đôi cờ khi xác nhận ĐỒNG THỜI), `B3` (trần 200 cờ
  trên trang), `B4` (CSRF baseline) — DEFER PRA-004 / hardening.
- `FIND-RDA-01` — `OWNER_SEMANTIC_CONFIRMED`; parser dạng
  `Ngày D tháng M năm YYYY` DEFERRED, `CODE_REQUIRED = NO`.
- `FIND-RDA-02` (`Suspicious` review reason) — tín hiệu nghiệp vụ bình thường.
- Quan sát mới (thông tin, không finding): `note_raw` là văn bản tự do có thể
  chứa tên khách — đã được frozen mục 4 dự liệu và phân loại Sensitive; không
  hành động.
- `validate_reference_integrity` 3 lỗi pre-existing `TASK-REM-T06` — DEFER.

## Kết Luận (Conclusion)

```text
REVIEW_RESULT             = PASS
FINAL_ACCEPTANCE          = ACCEPT
BLOCKING_FINDINGS         = 0
REPAIR_CYCLES_THIS_SESSION= 0        (lineage 1/2, còn 1)
CHECK-PRA002-14           = PASS     (E1 real data; provenance review E2)
CHECK-PRA002-15           = NOT_TESTED (Production Acceptance — Owner)
CHECK-PRA002-17           = PASS     (E2)
TASK-PRA-002              = IN_PROGRESS (KHÔNG DONE — CHECK-15 chưa PASS)
INTEGRATE_RDA_DOCS_READY  = YES      (14499dd + bản ghi review này: docs-only)
PRODUCTION_ACCEPTANCE_READY = YES   (sau Controlled Integration docs)
```

## Việc Cần Theo Dõi Tiếp (Required Follow-up)
1. Controlled Integration (fast-forward thuần) nhánh
   `claude/pra-002-rda-continuation-814n4h` (RDA docs + E2 record) vào
   `claude/extract-upload-repo-gq2ws4` — KHÔNG trong phiên review.
2. PRA-002 Production Acceptance (`CHECK-PRA002-15`, mục 16) — Owner deploy
   HEAD canonical sau integration; ghi kết quả vào PROGRESS.
3. Chỉ sau CHECK-15 PASS mới xét `TASK-PRA-002 = DONE`.
