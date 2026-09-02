# ADR-108 — Nơi lưu structured history cho Persistent Reporting & Analytics

## Status
Proposed — chờ Owner approve (decision audit thực hiện tại S073, 2026-09-02).
Không được coi là Accepted cho tới khi `PROJECT/PROJECT_DECISIONS.md` có DEC
ghi nhận Owner approve.

## Date
2026-09-02

## Context

`docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md` (S072) đề
xuất PostgreSQL managed. Owner chưa approve và yêu cầu một decision audit
nhỏ dựa trên workload THỰC của Reports, không dựa vào việc `ADR-101` từng
nhắc PostgreSQL. Ba ứng viên bắt buộc so sánh: R2 structured objects,
Cloudflare D1, Managed PostgreSQL. SQLite production không phải ứng viên
chính vì runtime production hiện STATELESS (S071B: Render Web Service, không
Disk, toàn bộ state ở R2); SQLite vẫn có thể giữ cho local/test.

### Workload thực (baseline Tín Phát + Beta, số liệu đã đo)

| Đại lượng | Giá trị thực | Nguồn |
|---|---|---|
| Dòng kế toán / tháng | ≈ 2.000 (11.765 dòng / 6 tháng) | `docs/analysis/_evidence/evidence.json` |
| Đơn / tháng | ≈ 1.450 (8.714 / 6) | cùng nguồn |
| Snapshot upload / tháng (dự kiến Beta) | 2–4 (giữa tháng + cuối tháng, thêm sửa) | Owner mô tả 10/09 vs 30/09 |
| Dòng source version / năm | ≈ 25.000–30.000 (SAME không tạo dòng mới) | suy từ trên |
| Dòng result version / năm | ≈ 30.000–60.000 (mỗi run ghi lại mọi dòng của snapshot đó) | suy từ trên |
| Legacy reference | ≈ 100 dòng Summary + 12×31 ô DataChart (+ ≈ 30.000 dòng chi tiết nếu sau này nhập) | audit Excel S072 |
| 3 năm | < 500.000 dòng fact, < 300 MB kể cả index | ước lượng thô |
| Người xem đồng thời | 2–5 (Owner + quản lý), 1 instance Render, gunicorn nhiều worker | S071 |
| Người ghi đồng thời | hiếm (upload thủ công), nhưng 2 upload gần nhau đã từng xảy ra trong test S071B | `tests/test_web_server.py` |

Loại truy vấn cần (từ kế hoạch PRA): lọc theo ngày/kỳ, nhân viên, sản
phẩm (canonical), đơn, dòng; aggregation theo kỳ × nhân viên/kênh;
reconciliation = tra cứu theo khoá đơn/dòng qua mọi snapshot trước, ghi
nhiều bản ghi trong MỘT đơn vị công việc; version/provenance = đọc lịch sử
theo khoá; đối chiếu legacy ↔ pipeline theo (tháng, nhân viên).

Ràng buộc kiến trúc không đổi: driver mạng/DB không được import dưới
`app/modules/` (`ADR-101`, `CHECK-105D-17`); pattern hiện có là driver ở
`tools/` (`tools/storage/r2_store.py`) và adapter ở `app/web/`
(`app/web/storage_backend.py`).

## Decision

**Đề xuất (chờ approve): HYBRID — Managed PostgreSQL cho structured
analytical records; R2 giữ nguyên cho workbook/XLSX artifact và run JSON;
Tracking giữ nguyên là authority upstream, chỉ tham chiếu bằng capture id.
SQLite chỉ cho local/test qua cùng một lớp SQL (SQLAlchemy Core).**

## Alternatives Considered

### Ma trận so sánh

Thang: ✅ đáp ứng tốt · ◐ đáp ứng có điều kiện/tự xây · ❌ không đáp ứng
hoặc tạo phức tạp không cần thiết.

| Tiêu chí | 1. R2 structured objects | 2. Cloudflare D1 | 3. Managed PostgreSQL |
|---|---|---|---|
| Workload hiện tại (≈2k dòng/tháng) | ✅ đủ sức | ✅ đủ sức | ✅ đủ sức (dư rất nhiều) |
| Query historical analytics (kỳ, nhiều tháng) | ◐ phải đọc nhiều object rồi gộp trong Python, hoặc tự vật chất hoá | ✅ SQL | ✅ SQL |
| Filter theo date | ◐ chỉ theo prefix khoá object; ngoài prefix = scan | ✅ index | ✅ index |
| Filter theo employee / product / order / order line | ❌ không có index thứ cấp; phải tự dựng index object | ✅ | ✅ |
| Aggregation | ◐ trong Python mỗi request (hoặc cache tự quản) | ✅ | ✅ |
| Reconciliation (tra khoá qua mọi snapshot, ghi nhiều bản ghi một lần) | ❌ không transaction; read-modify-write index; trạng thái dở dang khi lỗi giữa chừng | ◐ SQL có, nhưng qua HTTP API không có interactive transaction | ✅ transaction thật |
| Version / provenance | ◐ tự quản bằng quy ước tên khoá | ✅ | ✅ |
| Concurrent viewers | ✅ | ✅ | ✅ |
| Concurrent writers | ❌ conditional PUT có, nhưng multi-object atomic không có | ◐ | ✅ |
| Backup / recovery | ◐ versioning object; không point-in-time nhất quán giữa nhiều object | ◐ time-travel 30 ngày (Cloudflare), export qua wrangler | ✅ backup managed hằng ngày + `pg_dump` chuẩn |
| Operational complexity | ❌ tự viết index, khoá, versioning, cache = tự viết một DB | ❌ hai toolchain (Python + wrangler/Node cho migration), API token CF, không driver Python chuẩn | ◐ thêm 1 dịch vụ managed; Alembic chuẩn |
| Migration complexity (schema đổi) | ❌ không có schema; đổi hình dạng object = viết script đọc/ghi lại toàn bộ | ◐ SQL migration nhưng chạy ngoài Python | ✅ Alembic, chạy khi deploy |
| Cost | ✅ ≈ 0 (đã có bucket) | ✅ ≈ 0 ở mức này (free tier) | ◐ ≈ US$6–7/tháng (Render Basic-256mb; giá cần xác minh lúc tạo) |
| Compatibility Flask/Python | ◐ boto3 (đã có) | ❌ chỉ REST API qua HTTPS + token; không SQLAlchemy/psycopg; mỗi query 1 round-trip Render↔Cloudflare | ✅ psycopg 3 + SQLAlchemy Core |
| Compatibility Render stateless | ✅ | ✅ | ✅ (Render Postgres cùng region, private network) |
| Current R2 architecture | ✅ mở rộng tự nhiên | ◐ không liên quan | ✅ không đụng; R2 giữ vai trò artifact |
| Vendor coupling | ◐ S3-compatible (chuyển được) | ❌ Cloudflare-only; **cùng tài khoản/toolchain với Tracking** → cám dỗ dùng chung Worker/binding của Tracking = coupling bị cấm | ✅ Postgres chuẩn, `pg_dump` sang bất kỳ đâu |
| Expected Beta volume | ✅ | ✅ | ✅ |
| Mở rộng 1–3 năm (< 500k dòng) | ◐ số object tăng, list/scan chậm dần | ✅ (giới hạn 10 GB/DB) | ✅ |

### Trả lời bốn câu hỏi bắt buộc

**A. R2 structured objects — analytics có thành scan/object-read problem
không?** Có, ở đúng hai chỗ Reports cần nhất: (1) reconciliation phải trả
lời "khoá X đã thấy ở snapshot nào trước đây" cho ≈700 khoá mỗi lần upload
→ hoặc đọc mọi snapshot chồng kỳ (scan), hoặc tự duy trì một index object
`order_key → [snapshot_id]` bằng read-modify-write; (2) lọc theo nhân
viên/sản phẩm/đơn không có index thứ cấp → scan trong kỳ. Ở 2k dòng/tháng
scan vẫn chạy được, nhưng cái phải tự xây (index, khoá tối ưu, atomic
multi-object, cache) chính là một database — và không có transaction:
upload lỗi giữa chừng để lại snapshot đã ghi nhưng index chưa cập nhật,
đúng loại "silent wrong result" bị cấm. R2 làm đúng việc của nó: lưu
artifact bất biến theo `run_id`.

**B. D1 — Python/Render truy cập thế nào? Có coupling/phức tạp không cần
thiết không?** Từ Render (Python) chỉ có hai đường: (i) Cloudflare REST API
`POST /accounts/{id}/d1/database/{id}/query` với API token — mỗi câu SQL là
một HTTPS round-trip, không interactive transaction, không driver
SQLAlchemy/psycopg, module gọi mạng phải nằm ở `tools/`; (ii) một Worker
làm proxy — mà Worker duy nhất đang có là Tracking, và dùng nó là vi phạm
"không runtime dependency Reports → Tracking". Migration schema chạy bằng
`wrangler` (Node) — thêm một toolchain thứ hai vào repo Python. Kết luận:
D1 tạo coupling vendor + coupling tổ chức với hạ tầng Tracking và phức tạp
vận hành không tương xứng với một DB < 300 MB.

**C. PostgreSQL — lợi ích relational có đủ lớn để thêm một database
service không?** Có, vì lợi ích không nằm ở "SQL đẹp" mà ở đúng ba yêu cầu
integrity của PRA-002: (1) **transaction** — snapshot + N source version +
N result version + cập nhật current phải all-or-nothing; (2) **index theo
khoá** cho reconciliation và drill-down; (3) **migration có kiểm soát**
(Alembic) khi schema tiến hoá từ PRA-001 → PRA-005. Cả ba đều phải tự xây
nếu dùng R2, và đều bị suy giảm qua HTTP nếu dùng D1. Chi phí ≈ US$6–7/tháng
là nhỏ so với chi phí sửa một lần double-count lương/thưởng.

**D. Hybrid có hợp lý không?** Có, và là phương án đề xuất. Ownership:

```
Managed PostgreSQL  = structured analytical records: legacy_* (LEGACY_REFERENCE), source_snapshot,
                      order/line source & result versions, current views, review_item, acknowledgement.
                      Là nơi DUY NHẤT trả lời câu hỏi lịch sử/so sánh/đối chiếu.
R2                  = artifact bất biến theo run_id: runs/<id>.json (RunRecord hiện có, KHÔNG đổi),
                      artifacts/<id>.xlsx; sau này thêm backup dump định kỳ. Không query R2 để phân tích.
Tracking            = authority upstream (identity, PP, public purchase). Reports chỉ lưu capture id /
                      version id / content hash làm provenance; không mirror payload.
SQLite              = local dev + test (cùng SQLAlchemy Core, cùng migration chain); KHÔNG production.
```

## Rationale

- Chọn theo failure path, không theo tên công nghệ: rủi ro lớn nhất của PRA
  là ghi dở dang / đếm hai lần; chỉ Postgres cho transaction thật từ Python.
- Không tối ưu cho scale giả định: 256 MB Postgres là đủ cho 3 năm; không
  cần read replica, không cần warehouse.
- Giữ nguyên toàn bộ kiến trúc R2/S071B; Postgres là lớp THÊM cho history,
  không thay thế `RunStore`.
- Tách rõ khỏi Tracking cả về vendor lẫn toolchain.
- Đồng thời khớp `ADR-101` (PostgreSQL shared / SQLite dev-test) — đây là
  hệ quả, không phải lý do.

## Consequences

### Positive
- PRA-002 reconciliation viết được như một transaction; test được trên
  SQLite với cùng câu SQL Core.
- Backup managed + `pg_dump` sang R2 định kỳ thoả `16_BACKUP_DISASTER_RECOVERY`.
- Drill-down và aggregation là SQL có index; không cache tự quản.

### Negative / Tradeoffs
- Thêm một dịch vụ trả phí và một secret (`HISTORY_DATABASE_URL`) Owner phải
  tạo/dán trong Render; thêm dependency `sqlalchemy`, `alembic`, `psycopg`.
- Hai dialect (SQLite test / Postgres prod): phải giữ SQL trong tập giao
  (không dùng JSONB operator, dùng `INSERT … ON CONFLICT` qua Core, kiểu
  `Numeric` cho tiền). Một check REQUIRED của PRA-001 là DDL Postgres-compatible.
- Free tier Render Postgres hết hạn sau 30 ngày → KHÔNG dùng free tier cho
  history.

## Migration / Implementation Notes

- Env: `HISTORY_DATABASE_URL` (secret, `sync: false` trong `render.yaml`),
  `REPORTS_REQUIRE_HISTORY_DB=1` ở production → fail-closed lúc khởi động
  khi thiếu URL hoặc schema chưa ở đúng revision (cùng tinh thần
  `REPORTS_REQUIRE_R2`). Local/test: mặc định SQLite file dưới
  `REPORTS_DATA_ROOT` hoặc `sqlite:///:memory:` trong test.
- Vị trí code: engine/migration ở `tools/db/` (mới); repository/queries ở
  `app/web/` (được phép import `sqlalchemy` Core — `ADR-101` chỉ cấm dưới
  `app/modules/`); `app/modules/` không biết DB tồn tại.
- Migration chạy tường minh (`alembic upgrade head`) trong bước deploy hoặc
  entrypoint, không auto-migrate ngầm trong request.
- Backup: Render managed daily; `pg_dump` hằng tuần lên R2 là hardening
  ≤10 % của PRA-002, không phải PRA-001.
- Nếu Owner từ chối phương án này: phương án dự phòng duy nhất còn hợp lý là
  quay lại Render Disk + SQLite (S071, đã bị S071B supersede) — kém hơn về
  multi-worker và backup; R2-only và D1 bị loại theo ma trận trên.

## Supersedes
None

## Superseded By
None
