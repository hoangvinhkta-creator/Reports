# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S079

Task:
TASK-PRA-002 — Roadmap Finalization / Freeze Contract (Pipeline Persistence
+ Overlapping Snapshot Reconciliation)

Task Mode:
SPIKE (planning/finalization; KHÔNG implementation, KHÔNG code production,
KHÔNG migration, KHÔNG deploy)

Project Profile:
PRODUCT

Status:
DONE — planning finalization. `TASK-PRA-002` = READY, Completion Gate FROZEN.

Nhánh làm việc: `claude/pra-002-roadmap-finalization-xis6vb`, cắt từ nhánh
canonical `claude/extract-upload-repo-gq2ws4` tại
`BASE_SHA = 553d8a36f578b082128a6e45d2748da2bc371e70` (fetch đầu phiên: local
HEAD == origin, 0 behind / 0 ahead). Không dùng `main`. Tracking không đụng
(READ-ONLY, không cần đọc trong phiên này).

## Kết Quả (Result)

- Task file `docs/tasks/TASK-PRA-002-pipeline-persistence-reconciliation.md`
  đủ 20 mục Owner yêu cầu (Goal, Non-goals, Owner business contract, Data
  model tối thiểu 6 bảng, Source-/Result-version contract, Coverage
  contract + UX tối thiểu, State machine, Current-state rule, Provenance,
  Idempotency/no-double-count, Fail-safe, Migration, Test, Real Data
  Acceptance, Production Acceptance, Change budget, Deferred/UNKNOWN,
  Completion Gate 17 check FROZEN, 3 implementation slices).
- Reverse-engineering vừa đủ (mục "CURRENT STATE" trong task file): A
  business objects pipeline; B key/provenance hiện có; C schema Postgres
  hiện tại (4 bảng legacy, head `0001_legacy`); D khoảng cách nhỏ nhất
  (`DemoRun` +2 trường, exporter alias, writer sau `run_owner_report`,
  migration `0002_snapshots`, `SnapshotRepository`); E boundary mới
  (`app/history/` thuần + `history_writer`).
- DEC-171 ghi các quyết định chiến thuật (INFERENCE) tách khỏi Owner
  Decision đã có (DEC-166/167/170).
- Ledger mở lineage `TASK-PRA-002` (HIGH = 2 blocking repair cycles).
- PROGRESS + LO_TRINH cập nhật cùng checkpoint.

## FACT đo được trong phiên (E1)

```text
BASE_SHA                       = 553d8a36f578b082128a6e45d2748da2bc371e70
Golden baseline                = 58 passed, 2 skipped
Full suite                     = 1608 passed, 11 skipped   (venv riêng; SQLAlchemy 2.0.52, alembic 1.19.1, psycopg 3.3.5)
golden period_2026_01.xlsx     = 351 dòng có BH / 254 đơn / 1 dòng không BH / 0 đơn nhiều ngày /
                                 0 cặp (đơn, sản phẩm) lặp / DETECTED 2026-01-02..2026-01-31 /
                                 dòng ≤ 10/01 = 89, đơn ≤ 10/01 = 61
golden period_2026_06.xlsx     = 180 / 146 / 1 / 0 / 0 / 2026-06-01..2026-06-30 / ≤10: 53 dòng, 44 đơn
ô A2 fixture golden            = "Nhân viên: Tín Phát 0869931931, Tháng 1 năm 2026"   (KHÔNG phải "Từ ngày … đến ngày …")
ô A2 file production (doc)     = "Từ ngày 01/01/2026 đến ngày …"                      (docs/analysis/01_DATA_MAPPING.md §1)
AUTO/PENDING                   = chỉ tồn tại trong _PresentedLine.status (exporter, private)
DemoRun                        = (result, price_records, summary, output_path) — không raw_rows, không presented lines
RunRecord                      = không đơn/dòng/fingerprint/coverage
PostgreSQL local sẵn có        = psql/initdb 16 (như S078) — dùng cho CHECK-PRA002-01 khi implement
```

## Subtask Đã Hoàn Thành (Subtasks Completed)
- Đồng bộ nhánh (bước 0), đọc S000 + V4.1 overlay, PROFILE/PROGRESS, PRA-000
  (A–R + F1–F8), ADR-108, PRA-001, DEC-166…170, S073/S077/S078/S078R.
- Reverse-engineer: `app/web/server.py::run_report`, `app/demo.py`,
  `app/owner_usability.py`, `app/pipeline.py`, `app/composition.py`,
  `app/modules/exporting/excel_exporter.py`, `raw_reader.py`,
  `order_builder.py`, domain models, `PriceEvidenceSnapshot`, `ReviewItem`,
  `tools/db/*`, `app/web/history_store.py`, `storage_backend.py`,
  `run_registry.py`, golden expected JSON + fixture.
- Đo baseline test; đo hình dạng fixture golden (cho fixture hai snapshot).
- Viết task file, DEC-171, ledger, PROGRESS, LO_TRINH, handoff này.

## Subtask Còn Lại (Subtasks Remaining)
- Implementation theo slice A → B → C (task file mục 20); Independent
  Review E2; Controlled Integration; Real Data + Production Acceptance.

## Tóm Tắt Completion Gate (Completion Gate Summary)

Required:
Không có Completion Gate riêng cho phiên SPIKE này; tiêu chí học hỏi:
contract có bảng + phân loại FACT/OWNER_DECISION/INFERENCE/ASSUMPTION/
UNKNOWN, gate task kế tiếp FROZEN, evidence baseline có thật.

PASS:
Validator governance (xem "Validator run cuối"); `git diff --check` sạch.

FAIL:
(không)

BLOCKED:
(không)

NOT_TESTED:
Mọi CHECK-PRA002-xx (đúng thiết kế: chưa implement).

## Evidence Xác Minh (Verification Evidence)

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| S079-V1 | PASS | E1 | Golden `58 passed, 2 skipped`; full suite `1608 passed, 11 skipped` trên BASE_SHA | Claude (S079) | 2026-09-02 |
| S079-V2 | PASS | E1 | Đo fixture golden (bảng FACT ở trên) bằng openpyxl | Claude (S079) | 2026-09-02 |
| S079-V3 | PASS | E1 | Validator governance + `branch_authority_check.sh` + `git diff --check` (mục "Validator run cuối") | Claude (S079) | 2026-09-02 |

## File Đã Thay Đổi (Files Changed)

Created:
- `docs/tasks/TASK-PRA-002-pipeline-persistence-reconciliation.md`
- `docs/sessions/S079-pra-002-roadmap-finalization.md`

Modified:
- `PROJECT/PROJECT_PROGRESS.md`
- `PROJECT/LO_TRINH_DE_HIEU.md`
- `PROJECT/PROJECT_DECISIONS.md` (DEC-171)
- `PROJECT/REVIEW_BUDGET_LEDGER.md` (Root Task: TASK-PRA-002)

Deleted:
- (không)

Không file nào dưới `app/`, `tools/`, `config/`, `data/`, `tests/`,
`render.yaml`, `Dockerfile` bị sửa. `PROTECTED_CORE_IMPACT = NONE`.
`TRACKING_CHANGED = NO`. `PRA002_IMPLEMENTATION_STARTED = NO`.

## Quyết Định Chính (Key Decisions)
- DEC-171 (session tactical): normalize BH = engine; fingerprint không PII
  + có `source_profit`; không persist PII; xác nhận coverage là POST riêng
  sau upload; guard COLLISION 90 ngày giữ; thêm `snapshot_line`; bỏ
  `order_source_version`/`review_item`; result_fingerprint 3 trường; một
  transaction bao R2; 3 slice; budget 1.200/1.500; review HIGH = 2.
- Không có OWNER_DECISION_REQUIRED chặn implementation.

## Rủi Ro / Vướng Mắc (Risks / Blockers)
- ASSUMPTION D14: export kỳ ngắn = tập con export kỳ dài — chỉ đóng được
  bằng hai export thật của Owner (RDA-3). Nếu sai, mô hình vẫn an toàn
  (SOURCE_CHANGED/NOT_SEEN hiển thị) nhưng số cờ sẽ nhiều.
- Header dòng 2 có ít nhất hai dạng; dạng thứ ba sẽ rơi về DETECTED_ONLY
  (fail-safe, không chặn).
- Production Acceptance phụ thuộc Owner deploy (session không có egress);
  V4.1 §9 timeout 30 ngày.
- Change budget PRA-001 đã vượt kế hoạch 2×; PRA-002 đặt 1.200/1.500 theo
  hình dạng thật — vẫn có thể vượt nếu template/route phình; escalation rõ.

## Hạng Mục Regression (Regression Items)
- Không (không đổi code).

## Chưa Được Thay Đổi (Do Not Change Yet)
- Toàn bộ code production; schema; Tracking; R2/RunStore; Dockerfile/render.yaml.
- Không prebuild gì trước session implement A.

## Session Tiếp Theo Được Khuyến Nghị (Next Recommended Session)

### IMPLEMENTATION HANDOFF — TASK-PRA-002 slice A (đi thẳng vào implement)

Điều kiện mở: ĐÃ THOẢ (task READY, gate FROZEN, dependency DONE). Bắt đầu:

1. Bước 0 Session Open Protocol: `git remote show origin` → HEAD branch
   `claude/extract-upload-repo-gq2ws4`; fetch; nhánh làm việc mới cắt từ
   HEAD canonical (sau khi nhánh S079 này được gộp). Ghi baseline full
   suite + Golden.
2. Đọc task file mục 4, 5, 6, 8, 9, 11, 12, 14 và Touch Area trước khi
   viết dòng code nào.
3. A1 schema + migration `0002_snapshots` (DDL từ `schema.METADATA`,
   `tables=` 6 bảng, `checkfirst=False`); `ALEMBIC_HEAD`; cập nhật hai
   guard trong `tests/test_history_db.py`; up/down SQLite; PG 16 local
   (`initdb`/`pg_ctl` như S078).
4. A2 `app/history/keys` (ORDER_KEY = `line.order_id`; `product_key`;
   `occurrence_index` theo `line.raw.source_row`; `line_fingerprint` canon)
   + `app/history/coverage` (DETECTED từ RawRow; header 2 regex; state).
5. A3 `app/history/reconciler` thuần (input: dict khoá→(fingerprint,
   sale_date, current ids); output: quyết định) + unit test.
6. A4 `DemoRun` +`raw_rows`, +`presented_lines` (gọi
   `excel_exporter.present_lines` sau `export_report`, assert
   `len == summary.total_lines`); alias trong exporter.
7. A5 `SnapshotRepository` (đọc CUR theo tập khoá; insert batch; update
   current) + `history_writer.write(...)` mở `engine.begin()` bao R2.
8. A6 `run_report`: gọi writer trong `try` trước `finally` xoá temp; đọc ô
   A2 bằng openpyxl `read_only` trong `app/history/coverage` (không sửa
   `raw_reader`); tab Dữ liệu + trang snapshot; test Flask + integration
   A(≤10)→B đẳng thức.
9. Chạy CHECK-01/02/03/04/05/09/10/11/12/13; handoff S080; PROGRESS/LO_TRINH.

Giữ trong đầu: không `delete(`; `update(` chỉ `order_line_current` và cột
confirm; không PII; không import driver DB dưới `app/`; không sửa
`raw_reader`/`order_builder`/pipeline; Golden phải giữ `58 passed, 2
skipped`.

## File Agent Tiếp Theo Cần Đọc (Files Next Agent Should Read)
- `CLAUDE.md`
- `PROJECT/PROJECT_PROGRESS.md` → "CANONICAL CURRENT STATE — TASK-PRA-002"
- `docs/tasks/TASK-PRA-002-pipeline-persistence-reconciliation.md` (toàn bộ)
- `PROJECT/PROJECT_DECISIONS.md` → DEC-166, DEC-167, DEC-170, DEC-171
- `PROJECT/REVIEW_BUDGET_LEDGER.md` → "Root Task: TASK-PRA-002"
- `docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md` (H, I, J, K, F3, F4)
- `docs/adr/ADR-108-persistent-history-store.md`
- `app/web/server.py`, `app/demo.py`, `app/web/history_store.py`, `tools/db/schema.py`,
  `app/modules/exporting/excel_exporter.py` (chỉ đọc `_present_lines`)
- `tests/test_web_server.py`, `tests/test_demo.py`, `tests/test_history_db.py`,
  `tests/test_web_legacy_routes.py` (pattern engine/fixture)
- `governance/core/V4_1_POLICY_FREEZE.md`

## Validator run cuối (nguyên văn, 2026-09-02, S079)

```
$ git diff --check && echo diff-check clean
diff-check clean
$ for s in validate_structure validate_project_state validate_task_completion validate_evidence validate_reference_integrity; do python3 governance/scripts/governance/$s.py; echo "exit=$?"; done
GOVERNANCE STRUCTURE: PASS
Deployment root: PASS — /home/user/Reports
Checked 21 required paths.
exit=0
PROJECT STATE: PASS
exit=0
TASK COMPLETION: PASS
Checked 9 DONE task(s).
exit=0
EVIDENCE VALIDATION: PASS
Checked 100 REQUIRED PASS evidence record(s).
exit=0
REFERENCE INTEGRITY: FAIL
Quét 207 file .md (loại trừ 10 file trong governance/reference/history/, docs/audit/).
3 reference không phân giải được:
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md
exit=1
# 3 reference hỏng là có sẵn từ trước (REM-T06 DO_WHEN_IDLE), y hệt baseline S077/S078; S079 thêm 0 reference hỏng (207 file quét, +3 file mới so với S077).
$ bash scripts/branch_authority_check.sh
DEFAULT_BRANCH       : claude/extract-upload-repo-gq2ws4
DEFAULT_TIP          : 553d8a36f578b082128a6e45d2748da2bc371e70
HEAD_SHA             : 553d8a36f578b082128a6e45d2748da2bc371e70   (trước commit S079)
# Trước push: STOP — nhánh chưa có upstream (đúng thiết kế; giải quyết bằng `git push -u`).
$ git push -u origin claude/pra-002-roadmap-finalization-xis6vb && bash scripts/branch_authority_check.sh   (sau commit c83f58c)
ahead  default       : 1 commit
behind default       : 0 commit
divergence days      : 0
cumulative LOC       : 1803
DIVERGENCE           : WITHIN_LIMITS
AUTHORITY            : BRANCH_WITH_UPSTREAM
RESULT               : AUTHORITY_OK
$ Golden: 58 passed, 2 skipped · Full suite: 1608 passed, 11 skipped   (BASE_SHA, venv riêng)
```
