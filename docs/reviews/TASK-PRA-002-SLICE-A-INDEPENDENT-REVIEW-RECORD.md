# RÀ SOÁT ĐỘC LẬP E2 (E2 INDEPENDENT REVIEW) — TASK-PRA-002 SLICE A

Review ID:
PRA-002-SLICE-A-REVIEW-1

Task / Release:
TASK-PRA-002 — slice A (persistence + reconcile trục NGUỒN + result version + current)

Reviewer Session:
S081 — Independent Review Slice A (nhánh `claude/pra-002-slice-a-umygjq`)

Executed By:
S081 — PRA-002 Slice A Independent Review (2026-09-02)

Timestamp:
2026-09-02

## Scope

Chỉ vertical của slice A. KHÔNG review slice B (coverage confirmation,
`NOT_SEEN`, `REMOVED_CANDIDATE`), KHÔNG review slice C (`RESULT_REVISED`,
Real Data Acceptance, Production Acceptance), KHÔNG review legacy detail,
KHÔNG redesign PRA-002.

Lineage đã xác minh trước khi đọc bất kỳ dòng mã nào:

```text
REVIEW_BASE_SHA = 7fad3f76908d6d56114a5e2e947d83e15f8eda02   (== origin/claude/extract-upload-repo-gq2ws4, canonical CHƯA dịch chuyển)
REVIEW_HEAD_SHA = 80c6fe1d1c98497d821a8802fdbc9a1ca6a48b60   (== origin/claude/pra-002-slice-a-umygjq)
BASE là tổ tiên của HEAD  : ĐÚNG (git merge-base --is-ancestor → 0)
Working tree              : sạch
Diff review               : 28 file, +3.854 / −104
```

## Tài Liệu Đầu Vào Đã Đọc (Inputs Read)

- `docs/tasks/TASK-PRA-002-pipeline-persistence-reconciliation.md` (FROZEN
  tại S079) — mục 3 (Owner Business Contract), 4 (DATA_MODEL_MINIMUM),
  5 (source-version), 6 (result-version), 7 (coverage), 8 (state machine),
  9 (current-state), 10 (provenance), 11 (idempotency), 12 (fail-safe),
  13 (migration), 17 (CHANGE_BUDGET), 18 (deferred/UNKNOWN), 20 (slices).
- `docs/sessions/S080-pra-002-slice-a-implementation.md`.
- `docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md` (F3, I.2, N.13).
- `PROJECT/PROJECT_DECISIONS.md` (DEC-166, DEC-171), `docs/adr/ADR-108-persistent-history-store.md`.
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/REVIEW_BUDGET_LEDGER.md`.
- Toàn bộ diff `7fad3f7..80c6fe1` (mã production + test + template + migration).

## Xác Minh Độc Lập (Independent Verification)

Mọi bằng chứng dưới đây do phiên review TỰ CHẠY, không chép lại từ S080.

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| CHECK-PRA002-01 | PASS | E2 | `alembic upgrade head` → 11 bảng trên PostgreSQL 16.13 thật (socket local); `downgrade 0001_legacy` → còn đúng 5 bảng (`alembic_version` + 4 `legacy_*`), 6 bảng PRA-002 biến mất; `upgrade head` lại → `alembic_version = 0002_snapshots`. DDL PG: `origin` DEFAULT `'PIPELINE_GENERATED'::text`, `order_key_collision boolean DEFAULT false`, `uq_source_version_key_version` UNIQUE, FK/Index đúng mục 4 | S081 | 2026-09-02 |
| CHECK-PRA002-02 | PASS | E2 | `tests/test_pipeline_history_vertical.py` chạy lại: 351 dòng / 254 đơn / `sheet_data_rows=352` / `rows_without_order_id=1`, tổng `3.562.310.000` khớp exporter | S081 | 2026-09-02 |
| CHECK-PRA002-03 | PASS | E2 | Probe độc lập A→A: `SAME` toàn bộ, source version KHÔNG tăng, `current_totals()` bất biến từng đồng, `duplicate_of_snapshot_id` trỏ snapshot đầu | S081 | 2026-09-02 |
| CHECK-PRA002-04 | PASS | E2 | Probe độc lập: `state(A rồi B) == state(B một mình)` trên (số dòng current, số đơn, `SUM(total_sales)`, tập `(khoá, fingerprint)`); và B→A (hẹp hơn, upload sau) KHÔNG làm mất trạng thái hiện hành | S081 | 2026-09-02 |
| CHECK-PRA002-05 | PASS | E2 | Probe độc lập: đổi đúng một trường nguồn → đúng 1 `SOURCE_CHANGED`; version cũ còn nguyên (`changed_fields_json` NULL); current chuyển sang version mới; doanh thu dịch đúng delta, số dòng không đổi | S081 | 2026-09-02 |
| CHECK-PRA002-09 | PASS | E2 | UNIQUE `(khoá, version_no)` chặn ghi trùng (quan sát trực tiếp trên cả SQLite và PostgreSQL); không có `delete()` trong đường ghi; chỉ `order_line_current` bị UPDATE | S081 | 2026-09-02 |
| CHECK-PRA002-10 | PASS | E2 | Probe độc lập: `on_persisted` (R2) ném lỗi giữa transaction → rollback sạch, số hàng của cả 6 bảng bằng đúng trước khi ghi; `_build_history` fail-closed khi `REPORTS_REQUIRE_HISTORY_DB=1`; `index.html` báo "KHÔNG được lưu lịch sử" khi dev chưa cấu hình | S081 | 2026-09-02 |
| CHECK-PRA002-11 | PASS | E2 | Golden `58 passed, 2 skipped` (== baseline); full suite `1710 passed, 11 skipped` trước repair và `1711 passed, 11 skipped` sau repair (baseline `1608 passed, 11 skipped`); không skip mới | S081 | 2026-09-02 |
| CHECK-PRA002-12 | PASS | E2 | `app/history/**` không import `sqlalchemy`/`psycopg`/`alembic`/`flask` (chỉ `openpyxl` cho `scan_sheet` — được mục D.3 cho phép tường minh) | S081 | 2026-09-02 |
| CHECK-PRA002-13 | PASS | E2 | Tập cột của cả 6 bảng ∩ {`customer`, `customer_code`, `phone`, `address`, `shipper_raw`} = ∅ (đo bằng `schema.PIPELINE_TABLES`); `SourceLine`/`ResultLine` cũng không mang trường PII nào; `FINGERPRINT_FIELDS` ∩ PII = ∅ | S081 | 2026-09-02 |
| CHECK-PRA002-16 | PASS | E1 | Chỉ review structural: writer không mở workbook thứ hai không-read-only (`scan_sheet` dùng `read_only=True` + `close()`, fingerprint đọc khối 1 MB) | S081 | 2026-09-02 |
| CHECK-PRA002-06/07/08/14/15 | NOT_TESTED | — | Ngoài slice A (B/C/Owner) | S081 | 2026-09-02 |

## Sai Lệch So Với Tuyên Bố Của Người Triển Khai (Mismatches With Implementer Claims)

Không có sai lệch về con số. Ba tuyên bố chính của S080 đã được đo lại độc
lập và khớp: LOC production 1.080 dòng logic (đo lại bằng AST, bỏ docstring
và comment), Golden `58 passed, 2 skipped`, full suite `1710 passed, 11
skipped`.

S080 KHÔNG tuyên bố sai; nó thiếu một kịch bản — xem FIND-PRA002-A1.

## Findings

### FIND-PRA002-A1 — BLOCKING (đã sửa trong chính phiên này)

Version nguồn mới được đánh số theo version **hiện hành** (`state.version_no
+ 1`) thay vì theo version **lớn nhất đã ghi**, trái mục 5.3 ("`SOURCE_CHANGED`
→ `version_no = max + 1`").

`ORDER_KEY_COLLISION` ghi một version mới nhưng CỐ Ý không làm nó hiện hành
(mục 8 bước 2). Từ thời điểm đó, hiện hành tụt lại phía sau max. Mọi lần ghi
version tiếp theo trên khoá đó tính lại đúng con số đã dùng → vi phạm UNIQUE
`(order_key, product_key, occurrence_index, version_no)` → cả transaction
rollback → `/run` trả HTTP 500.

Hậu quả nghiệp vụ: sau cờ tranh chấp ĐẦU TIÊN trên production — chính sự kiện
mà mục 18 D2 nói là sẽ xảy ra — Owner không còn chạy được báo cáo nào chứa Số
BH đó. Không mất dữ liệu, không sai số (fail-closed), nhưng lá chắn an toàn
tự biến thành một cửa chặn vĩnh viễn trên đường production.

Bằng chứng (probe độc lập, tái hiện trên CẢ SQLite và PostgreSQL 16.13):

```text
upload 1: BH1 ngày 05/01  → INSERT v1, current = v1
upload 2: BH1 ngày 05/06  → ORDER_KEY_COLLISION, ghi v2, current vẫn v1
upload 3: nạp lại ĐÚNG file của upload 2
          → (psycopg.errors.UniqueViolation) duplicate key value violates
            unique constraint "uq_source_version_key_version"
          → HistoryUnavailableError → HTTP 500
kịch bản 2: kế toán sửa giá dòng gốc sau collision → cùng lỗi
```

Vì sao test cũ không bắt được: `test_a_colliding_key_is_stored_flagged_and_left_out_of_the_current_state`
dừng lại ngay sau lần collision đầu tiên; không có test nào ghi tiếp trên
khoá đã tranh chấp.

Thẩm quyền để sửa tại chỗ: mục 5.3 của chính task đã freeze nói "max + 1" —
đây là lệch so với contract, không phải quyết định nghiệp vụ mới. Sửa cục bộ,
không đổi kiến trúc, không cần Owner.

### FIND-PRA002-A2 — NON_BLOCKING

`app/demo.py` gọi lại `present_lines(...)` để lấy `presented_lines`, trong khi
`export_report` đã tính đúng danh sách đó bên trong. Mục D.1 nói "chỉ chưa trả
ra … không tính lại gì". Bước trình bày vì vậy chạy hai lần.

Không có hậu quả đúng/sai: `_present_lines` là hàm thuần trên
`(result, records, raw_rows)` — `by_key` được dựng mới mỗi lần gọi, không tiêu
thụ đầu vào — nên hai lần gọi cho kết quả bằng nhau (đã kiểm bằng đọc mã và
bằng test alias `is`). Không có regression bộ nhớ đáng kể: danh sách thứ nhất
đã được giải phóng khi `export_report` trả về, và `_PresentedLine` chỉ giữ
tham chiếu tới object đã có.

Sửa triệt để đòi trả `presented` ra khỏi `export_report`, tức sửa thân hàm
trong `app/modules/exporting/**` — vượt hạn mức "chỉ thêm alias ≤ 4 dòng" của
mục 17 và chạm protected core. DEFER sang slice C hoặc hardening, kèm điều
kiện re-trigger: khi `ru_maxrss` hoặc thời gian `/run` trở thành ràng buộc thật.

### FIND-PRA002-A3 — NON_BLOCKING

`source_snapshot.detected_date_min/max` khai `nullable=True`, mục 4 ghi
`NOT NULL`. Nới lỏng có chủ đích: `detected_range` trả `(None, None)` khi mọi
`sale_date` là None. Mục 7.1 khẳng định trường hợp đó đã bị pipeline/exporter
chặn từ trước, nên trên thực tế cột luôn có giá trị.

Hậu quả nếu xảy ra: snapshot đó không lọc được theo kỳ trên trang chi tiết.
Không sai số, không mất dữ liệu. Siết lại `NOT NULL` sau này là một migration
riêng — không đáng mở trong slice A.

### FIND-PRA002-A4 — NON_BLOCKING (quan sát, không sửa)

Trang chi tiết snapshot in "CHƯA XÁC NHẬN ĐỦ" cố định thay vì theo
`coverage_state`. Ở slice A câu đó luôn đúng vì không có đường nào đặt
`CONFIRMED_COMPLETE`. Slice B (mục 7.3) phải biến nó thành điều kiện — ghi ở
đây để không rơi.

### Đã kiểm và KHÔNG phải finding

- **`SAME` vẫn tạo result version mỗi run (351 → 702).** Đây là
  OWNER-FROZEN, không phải suy diễn của implementation: mục 6 viết nguyên văn
  "Mỗi run (mỗi snapshot) ghi ĐÚNG một result version cho MỖI khoá của snapshot
  đó, **kể cả dòng `SAME`** (pipeline đã chạy lại thật với evidence mới) —
  không 'copy' result cũ", và mục 8 bước 0 nhắc lại "run vẫn tạo result version
  mới". Semantic không lệch: `order_line_result_version` là bản ghi
  **quan sát theo run** (UNIQUE `(run_id, khoá)`), không phải "kết quả nghiệp
  vụ"; thứ mang nghĩa nghiệp vụ là `order_line_current.current_result_version_id`.
  Nguy cơ PRA-003/004 đọc 702 hàng thành 702 kết quả đã được chặn bằng CẤU
  TRÚC chứ không bằng kỷ luật truy vấn: `order_line_current` có PK theo khoá,
  và `current_totals()` join qua đúng con trỏ đó. Đo lại: sau hai lần upload
  cùng một sổ, `result_versions = 4`, `current = 2`, tổng tiền không đổi một
  đồng. Current projection KHÔNG double-count.
- **Ngưỡng 90 ngày.** Có thẩm quyền hợp lệ, không phải implementation tự sinh:
  `TASK-PRA-000` F3 dòng 533 ("guard: cùng ORDER_KEY nhưng
  `|order_date_mới − order_date_cũ| > 90 ngày`"), N.13, bảng rủi ro; và được
  chép vào TASK-PRA-002 đã freeze ở mục 3.5 (phân loại tường minh **INFERENCE
  (fail-safe)**, KHÔNG phải business rule), mục 8 bước 2, mục 12, mục 14.
  Implementation trung thành: 91 ngày → collision, đúng 90 ngày → reconcile
  bình thường, thiếu ngày một trong hai bên → KHÔNG collision. UNKNOWN "BH
  reset theo năm" KHÔNG bị biến thành rule 90 ngày — nó vẫn là D2 với
  re-trigger nguyên vẹn, và `bh_number`/`bh_year_hint` được lưu sẵn để nâng
  cấp namespace mà không phải đọc lại lịch sử. Không cần `OWNER_DECISION_REQUIRED`
  cho slice A.
- **Khoá và fingerprint.** `ORDER_KEY` = `order_id` của engine, không chuẩn
  hoá thêm (mục 3.5). `occurrence_index` đo được là deterministic: sắp theo
  `source_row` tăng dần, ổn định khi snapshot dịch toàn bộ vị trí dòng
  (`source_row` 6,7,8 → 20,21,22 cho cùng occurrence 1,2,1), và bất biến với
  thứ tự đầu vào (đảo ngược danh sách cho cùng kết quả). `canon(Decimal)` dùng
  `format(x.normalize(), "f")` — mạnh hơn `str()` của mục 5.2 vì tránh ký hiệu
  khoa học, đúng ý định đã ghi (`1E+3` → `"1000"`), không phải lệch.
  Fingerprint không chứa trường result-derived nào.
- **Transaction.** Toàn bộ đọc CUR → reconcile → ghi → `on_persisted` (R2)
  nằm trong một `engine.begin()`; R2 lỗi → rollback toàn phần (đo được: số
  hàng cả 6 bảng bằng đúng trước khi ghi). `run_report` KHÔNG nuốt lỗi ghi
  lịch sử: trả 500 với thông điệp hiện có.
- **`note_raw` hiển thị trong `changed_fields` trên trang snapshot.** Mục 4
  phân loại `note_raw` là Internal business data (engine đọc nó để phân loại
  ADS, nó nằm trong fingerprint) và cho phép hiển thị "không phơi ra browser
  ngoài trang Dữ liệu nội bộ" — đây đúng là trang nội bộ đó. Trong thẩm quyền.
- **`index.html` +3 dòng ngoài Allowed Touch Area.** Là cách tối thiểu để thoả
  CHECK-PRA002-10 (c) đã freeze ("trang hiển thị 'KHÔNG được lưu lịch sử'").
  Touch area thiếu tên file là thiếu sót tài liệu, không phải scope drift.
  ACCEPT deviation, không mở task.

## Repair đã áp dụng trong phiên (repair cycle 1/2)

Sửa FIND-PRA002-A1, cục bộ, không đổi kiến trúc, không đổi contract:

- `app/history/models.py`: `CurrentState` thêm `max_version_no` và property
  `next_version_no` = max đã ghi + 1.
- `app/history/reconciler.py`: nhánh `ORDER_KEY_COLLISION` và
  `SOURCE_CHANGED` dùng `state.next_version_no` thay cho `state.version_no + 1`.
- `app/web/history_store.py::_load_current`: nạp thêm `MAX(version_no)` theo
  khoá (một truy vấn GROUP BY trên cùng chunk `order_key`, dùng index
  `ix_source_version_order_key` đã có; bộ nhớ vẫn tỉ lệ với snapshot).
- `tests/test_snapshot_repository.py`: thêm
  `test_uploading_again_after_a_collision_still_works` — bịt đúng lỗ hổng đã
  để lọt (nạp lại file gây tranh chấp + sửa dòng hiện hành sau tranh chấp;
  khẳng định version numbering `[1, 2, 3, 4]`, hiện trạng và tiền không đổi).

Regression sau repair (tự chạy):

```text
tests/test_snapshot_repository.py + test_history_reconciler.py : 35 passed
Golden Baseline                                                : 58 passed, 2 skipped
Full suite                                                     : 1711 passed, 11 skipped
PostgreSQL 16.13 (migration + INSERT/SAME/SOURCE_CHANGED/COLLISION + nạp lại sau collision) : PASS
LOC production Python sau repair                               : 1.104 (mục tiêu ≤ 1.200, dừng cứng 1.500)
```

## Kết Luận (Conclusion)

E2 PASS

Slice A đạt vertical đã yêu cầu: pipeline hiện có → structured output →
PostgreSQL persistence → INSERT/SAME/SOURCE_CHANGED/COLLISION → result
version → current pointer → đọc lại/truy vấn. Không double-count, không ghi
đè âm thầm, version lịch sử bất biến, current projection đúng, legacy không
đổi, PII không rò, fail-closed đúng, migration additive và đảo được. Sau
repair cycle 1, không còn finding BLOCKING nào.

## Việc Cần Theo Dõi Tiếp (Required Follow-up)

1. Controlled Integration slice A vào canonical `claude/extract-upload-repo-gq2ws4`.
2. Slice B: `coverage_state` phải điều khiển câu "CHƯA XÁC NHẬN ĐỦ"
   (FIND-PRA002-A4); reconciler bước 4 + R; `POST xac-nhan-du`.
3. Slice C: cân nhắc FIND-PRA002-A2 (trả `presented` ra khỏi `export_report`)
   khi chạm ngân sách bộ nhớ/thời gian thật; siết `detected_date_*` về
   `NOT NULL` nếu có migration khác đi cùng (FIND-PRA002-A3).
4. `CHECK-PRA002-14` (Real Data Acceptance) và `CHECK-PRA002-15` (Production
   Acceptance) vẫn `NOT_TESTED` — gate của Owner, không thuộc slice A.
