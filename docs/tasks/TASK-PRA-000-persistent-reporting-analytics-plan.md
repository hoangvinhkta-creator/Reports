# TASK-PRA-000 — Kế hoạch kiến trúc: Persistent Reporting & Analytics

## Metadata
Status:
DONE

Phase:
PHASE-PRA (Persistent Reporting & Analytics) — bước 0, chỉ lập kế hoạch

Task Mode:
SPIKE

Primary Agent Tier:
Tier C

Escalation Tier:
Owner

Difficulty:
3/5

Risk:
2/5

Blast Radius:
1/5

Project Profile:
PRODUCT

Session:
S072 (2026-09-02) — `docs/sessions/S072-persistent-reporting-analytics-planning.md`

Phạm vi ghi (write scope) của session tạo ra tài liệu này: CHỈ repo Reports.
Tracking là READ-ONLY REFERENCE — không sửa, không commit, không đổi
contract. Mọi phương án cần sửa Tracking đều được đánh dấu
`ARCHITECTURE_DEPENDENCY` và KHÔNG thực hiện.

Tài liệu này không code feature, không refactor, không migration, không
deploy. Nó chốt: data model tối thiểu, mô hình dedup/version/reconciliation,
information architecture của UI, analytics ưu tiên, roadmap vertical slice,
và các quyết định Owner thực sự cần.

Quy ước trong tài liệu: đường dẫn file **dự kiến tạo** được viết KHÔNG kèm
phần mở rộng (ví dụ `app/web/history_store`) để phân biệt với file đã tồn
tại trong repo (ví dụ `app/web/storage_backend.py`).

---

## A. EXECUTIVE SUMMARY

1. Reports hôm nay là một **file analyzer** đúng nghĩa: mỗi lần chạy giữ lại
   đúng 7 con số tổng hợp + 1 file XLSX trên R2. Toàn bộ dữ liệu theo đơn,
   dòng, nhân viên, tiền, giá, lý do Review chỉ tồn tại trong bộ nhớ và
   trong XLSX. Không có JSON API, không có định danh người dùng trong app
   (chỉ Cloudflare Access chắn phía trước). Trạng thái AUTO/Review **không
   phải một trường domain** — nó được suy ra bên trong exporter.
2. File Excel cũ ("Báo cáo Kinh doanh 2026", 59 sheet) là một hệ thống báo
   cáo **theo trục Nhân viên × Tháng**: 56 sheet chi tiết `MM.2026 <tên>`,
   một `Summary 2026` (ma trận tháng × người bán với 17 cột KPI/lương/thưởng),
   một `DataChart 2026` (doanh số theo ngày × tháng, so 2025, so target).
   Reports đã từng reverse-engineer file này (`docs/analysis/`) — tài liệu
   này KHÔNG làm lại việc đó, chỉ bổ sung góc nhìn "người dùng xem báo cáo
   thế nào" và "cần lưu gì để so sánh".
3. Dữ liệu lịch sử phải tách thành hai origin không bao giờ trộn:
   `LEGACY_REFERENCE` (số đã tính tay, nhập nguyên trạng, kèm cờ lỗi công
   thức đã biết, không tính lại) và `PIPELINE_GENERATED` (kết quả pipeline
   authoritative, có provenance đầy đủ tới snapshot nguồn + evidence
   Tracking + config).
4. Khoá đơn: `ORDER_KEY = Số BH` (chuẩn hoá) — đủ cho nguồn ERP thật (8.714
   BH duy nhất/11.765 dòng, 0 đơn có nhiều ngày hoặc nhiều nhân viên trong
   fixture golden). **Không có khoá dòng tự nhiên** trong file kế toán: dòng
   chỉ có `source_row` + `row_hash`. Khoá dòng đề xuất là
   `ORDER_LINE_KEY = (ORDER_KEY, product_key, occurrence_index)` kết hợp
   `line_fingerprint` nội dung để phân biệt SAME / CHANGED / ADDED / REMOVED.
   Trong Excel cũ, BH chỉ xuất hiện ở các sheet 08.2026 (gõ tay, có lỗi gõ)
   → không dùng BH làm khoá cho legacy; legacy khoá theo
   `(import_id, sheet, row)`.
5. Mô hình snapshot: mỗi lần upload = một `SOURCE_SNAPSHOT` có coverage
   tường minh; mỗi đơn/dòng có **hai trục phiên bản** tách biệt: phiên bản
   NGUỒN (kế toán đổi số) và phiên bản KẾT QUẢ (pipeline chạy lại với
   evidence Tracking mới). Nhầm hai trục này là cách nhanh nhất để tạo
   "conflict giả" hoặc "double-count thật".
6. UI giữ 6 khu vực nhưng chỉnh nội dung: "Cần kiểm tra" gộp Review Queue +
   Thay đổi nguồn + Đối chiếu cũ/mới; "Lịch sử dữ liệu" đổi thành "Dữ liệu"
   với lịch coverage; "Sản phẩm" lùi về slice cuối vì chỉ có ý nghĩa trên
   dòng đã resolve identity. Điều hướng dùng **tab ngang + thanh ngữ cảnh
   sticky** giống Tracking (Tracking không có sidebar).
7. Roadmap 5 slice dọc; slice 2 (persistence + reconciliation) là slice nặng
   nhất và là nền cho mọi thứ sau; slice 1 (legacy) nhỏ, cho Owner thấy dữ
   liệu cũ trong Reports sớm nhất và đồng thời đặt nền DB.
8. Có **13 quyết định Owner** thật sự cần (mục N); trong đó 4 quyết định chặn
   slice 2 (DB production, nguồn coverage, chính sách xung đột, chính sách
   đơn biến mất).
9. `SCOPE_DRIFT = NO`. Không đề xuất sửa protected core, không sửa Tracking,
   không mirror Tracking.

---

## B. CURRENT STATE (audit Reports, HEAD `596564b` trên nhánh mặc định `claude/extract-upload-repo-gq2ws4`)

### B.1 Luồng hiện tại
```
Upload .xlsx (≤25MB)
→ app/web/server.py::run_report  (Flask, PRG, không JSON API)
→ live pull Tracking (tools/tracking/live_pull.py, fail-closed)
→ app/owner_usability.py::run_owner_report → app/composition.py::run_import_production
→ ImportResult (orders, lines, review_queue) + PriceResolutionRecord[] (song song, không gắn vào line)
→ app/modules/exporting/excel_exporter.py (Summary / Order Lines / Review Queue; AUTO/PENDING suy ra TẠI ĐÂY)
→ store.save_artifact + store.create_run  (R2: runs/<id>.json + artifacts/<id>.xlsx; local: SQLite + file)
→ redirect /?run_id=…
```

### B.2 Cái gì được persist (toàn bộ)
`RunRecord`: `run_id, created_at, status, workbook_display_name, artifact_path,
view, tracking_evidence, error_message`. `view` = 6 số (`input_orders,
auto_orders, review_orders, error_count, dropped_lines, accounting_rate`) +
`review_reason_lines`. **Không có** đơn, dòng, nhân viên, tiền, giá, lý do
theo đơn. Không có fingerprint workbook (chỉ có `RawRow.row_hash` theo dòng,
dùng trong-lần-nhập). Không có coverage. Không có xoá/retention.

### B.3 Điểm mạnh dùng được ngay
- Domain model giàu và đã đóng băng qua Golden Baseline (`WorkingLine` 38
  trường, `Order`, `PriceResolutionRecord`, `ReviewItem` typed payload,
  `PriceEvidenceSnapshot` với đủ capture id, `EmployeeMaster.snapshot_id()`,
  `config_snapshot_id` trong golden JSON).
- `tests/fixtures/golden/expected/period_2026_01.json` đã là một
  **de-facto analytics schema** (`counts, money, employees, lead_source,
  pricing, conversion, review_queue, orders_detail, order_graph,
  lines_digest`). Persistence nên đi theo hình dạng này thay vì phát minh
  schema mới.
- `RunStore` interface (`app/web/storage_backend.py`) đã tách backend; R2
  adapter nằm ở `tools/storage/r2_store.py` đúng ranh giới ADR-101 (không
  module nào dưới `app/` import network primitive — `CHECK-105D-17`).
- Tiền là `Decimal` VND nguyên; `None ≠ 0` (DEC-103); bất biến
  `PriceResolutionRecord.__post_init__` chặn RESOLVED-thiếu-giá.

### B.4 Khoảng trống so với mục tiêu
| Khoảng trống | Hệ quả cho analytics |
|---|---|
| Không persist đơn/dòng | Không query lịch sử được, phải parse XLSX |
| AUTO/Review chỉ có trong exporter | Không lưu được trạng thái nếu không tách hàm |
| Không fingerprint workbook, không coverage | Không dedup, không biết ngày nào đã có dữ liệu |
| Không định danh người dùng trong Flask | Không có `uploaded_by`/`acknowledged_by` |
| Production stateless (R2), SQLite chỉ local | Chưa có nơi đặt relational history — cần quyết định Owner |
| `beta_feedback`/`beta_telemetry` ghi JSONL vào REPO_ROOT | Mất trên Render mỗi lần restart (bug sống, không chặn) |
| Không JSON API | Mọi màn hình mới cần route + presentation model mới |

### B.5 Mâu thuẫn tài liệu ↔ triển khai (ghi nhận, không tự giải quyết)
```
CONFLICT DETECTED
Documentation: docs/adr/ADR-101-architecture-and-stack.md — backend FastAPI + SQLAlchemy + Alembic, frontend React/Vite.
Implementation: app/web/ dùng Flask + Jinja (S070/S071, đã accepted, Independent Review PASS, đã deploy Render).
Risk: một session sau có thể "sửa cho đúng ADR" và refactor toàn bộ web layer — đúng loại scope creep bị cấm.
Recommended resolution: giữ Flask + Jinja làm presentation layer (không refactor); áp dụng phần DB của ADR-101 (PostgreSQL shared / SQLite dev-test, migration có kiểm soát) cho history schema; ghi một ADR ngắn "ADR-101 amendment: web layer = Flask, không đổi engine boundary" khi mở slice 1. Cần Owner ratify (mục N, quyết định 12).
```

---

## C. LEGACY EXCEL FINDINGS (file "Báo cáo Kinh doanh 2026.xlsx", audit 2026-09-02)

### C.1 Cấu trúc và cách người dùng xem
| Loại sheet | Số lượng | Người dùng dùng để | Ghi chú |
|---|---|---|---|
| `Summary 2026` (visible) | 1 | Xem KPI tháng × người bán, lương/thưởng | 8 khối tháng (01–08), mỗi khối: 5–7 dòng người bán/kênh + 1 dòng tổng tháng + 1 dòng "Tiến độ" (số ngày đã qua / số ngày tháng). Đơn vị **nghìn đồng**. |
| `DataChart 2026` (visible) | 1 | Xem doanh số theo ngày, so 2025, so target | Lưới 12 tháng × 31 ngày, VND nguyên; `AveragePerDay`, `TargetPerDay`, target năm 345.474.000 (k). Nguồn số **khác** Summary (tháng 01: 25,47 tỷ vs 24,78 tỷ) — ý nghĩa `UNKNOWN / OWNER_DECISION_REQUIRED`. |
| `Summary 2025` (hidden) | 1 | So cùng kỳ | Chỉ giá trị (không công thức), có "Miền Bắc" là người bán không còn ở 2026. |
| `MM.2026 <Người>` (cá nhân) | 40 | Drill-down của một người trong một tháng | Ly, Thắng, Tín Phát, Hoàng, Kiên, Fanpage/Linh. Dòng 1 = KPI header (`count Trans`, tỉ lệ Kho, số SP, tổng bán, lợi nhuận, margin, lợi nhuận gộp). Dòng 2 = tiêu đề. Dữ liệu theo ngày: dòng đầu mỗi ngày có `Date`, `Trans` = STT đơn trong ngày, dòng nối tiếp (phụ kiện/vận chuyển/chiết khấu) để trống `Trans`. |
| `MM.2026 Nội thành`, `MM.2026 Gia dụng` (kênh) | 16 | Kênh bán buôn/kênh gia dụng | Không có `Nơi nhập`, không `Trans`, không BH; khách là cửa hàng; có **dòng tổng ngày nằm lẫn trong dữ liệu** → header `SUM/2` (DEC-115). |

Chỉ 7 sheet đang visible (Summary 2026, DataChart 2026, 5 sheet 08.2026):
người dùng **ẩn tháng cũ** để điều hướng — bằng chứng trực tiếp rằng
spreadsheet không có khái niệm "chọn kỳ", họ phải ẩn/hiện sheet bằng tay.

### C.2 KPI và bảng summary đang có giá trị quản lý
Cột `Summary 2026` (theo tháng, theo người bán): Tổng đơn (`count Trans`),
Tổng số SP, Tổng bán, **Doanh thu quy đổi** (= Lợi nhuận / tỉ lệ: 5,5 %
cá nhân, 7,5 % Tín Phát/ADS, 2 % Nội thành, 8 % Gia dụng; Hoàng/Kiên tách
hai bucket tay `=(G−X)/5.5%+X/7.5%`), Tổng lợi nhuận, Tỉ suất lợi nhuận,
**Vs. tháng trước**, Tỉ lệ tồn kho (phần doanh thu có `Nơi nhập = Kho`),
Lợi nhuận thực tế (gộp), Mỗi ngày, **Target**, **Vs. Target**, Thưởng
(bậc theo attainment: <100 % ×0,3 %, đạt ×0,4 %, vượt 10 % ×0,45 %, vượt
20 % ×0,5 %), Ngày công, Lương cứng, Phụ cấp, Tổng lương.

→ Giá trị quản lý cốt lõi mà UI mới phải giữ: **(1) ma trận Nhân viên ×
Tháng, (2) so tháng trước, (3) target attainment, (4) tiến độ trong tháng
(ngày đã qua), (5) drill-down người → ngày → đơn → dòng.** Lương/thưởng là
tầng HR nằm trên KPI — Reports chưa có business rule cho nó (mục N, quyết
định 9).

### C.3 Drill-down hiện tại
`Summary` → click ô tham chiếu `'MM.2026 Tên'!$H$1` → sheet chi tiết →
cuộn theo ngày (`Date` chỉ ghi ở dòng đầu ngày) → đơn (`Trans`) → dòng nối
tiếp. Không có cách lọc theo sản phẩm, theo khách, theo kênh trong cùng
tháng; không có cách xem một người qua nhiều tháng ngoài Summary.

### C.4 Hạn chế do spreadsheet gây ra (đã xác minh trên file)
- 6 lỗi công thức đã ghi nhận trước (`docs/analysis/05_EXCEPTIONS.md` A1–A6):
  Số SP là số thập phân (trừ nhầm tỉ lệ), dòng tổng tháng bỏ sót Nội
  thành/Gia dụng ở cột DS quy đổi (thiếu 60 % ở tháng 01), tham chiếu sai
  sheet (`D64`/`D71` lấy số SP Tín Phát cho Nội thành — **vẫn còn ở bản
  hiện tại, tháng 07 và 08**), số cứng tháng trước ở tháng 01.
- Số BH chỉ có ở sheet 08.2026 (gõ tay vào cột `IMEI`), 194 BH, dải
  66731–82897 có giá trị ngoài dải tháng 8 (ví dụ BH82897 khi các đơn cùng
  ngày là BH73xxx) → lỗi gõ. BH trùng trong cùng sheet (6 trường hợp) đều là
  **đơn nhiều dòng** ghi lặp BH, không phải trùng đơn.
- `Trans` đếm lại từ 1 mỗi ngày → không có khoá đơn ổn định trong 7 tháng
  đầu.
- Dòng số lượng 0 = huỷ/hoàn (ghi ở cột `Giao hàng`: "Huỷ", "Hoàn", "Trả
  hàng"); dòng âm = chiết khấu/vận chuyển/giá treo. Không có trạng thái
  đơn tường minh.
- Cột `Hãng` (R) thực tế chứa ghi chú giao hàng/đặt cọc (1.120 ô là dấu `,`).
- Ẩn/hiện sheet là cơ chế điều hướng duy nhất; không có kỳ tuỳ chọn, không
  có so cùng kỳ ngoài DataChart.
- PII (tên, SĐT, địa chỉ khách) nằm ngay trên sheet chi tiết cá nhân.

### C.5 Sự thật cần giữ nguyên khi import legacy
Đơn vị nghìn đồng, lỗi công thức, `/2`, số cứng — **tất cả được lưu nguyên
trạng** kèm cờ `known_defect` tham chiếu A1–A6; Reports không "sửa" số cũ.

---

## D. UI INFORMATION ARCHITECTURE

Nguyên tắc: 6 khu vực là đủ; mỗi khu trả lời một câu hỏi quản lý có bằng
chứng trong Excel cũ hoặc trong nhu cầu vận hành Review. Không thêm tab
Kho/NCC/Marketing/Lương.

| # | Đề xuất gốc (MD) | Quyết định | Lý do theo dữ liệu/người dùng |
|---|---|---|---|
| 1 | Tổng quan | **GIỮ** | Trang mặc định: KPI kỳ + so kỳ trước + target + "có gì cần chú ý". Tương đương dòng tổng tháng + dòng "Tiến độ" của Summary. |
| 2 | Bán hàng | **GIỮ, đổi trọng tâm** = "Kỳ → Đơn → Dòng" | Excel không có view danh sách đơn theo kỳ; đây là thứ spreadsheet không làm được. Bộ lọc: kỳ, nhân viên, kênh (employee_group × product_group), trạng thái AUTO/Review, origin. |
| 3 | Nhân viên | **GIỮ, nâng ưu tiên** = trục chính | Toàn bộ Excel cũ tổ chức theo Nhân viên × Tháng. Ma trận này + drill-down người → tháng → ngày → đơn là "tính năng tương đương file cũ". |
| 4 | Sản phẩm | **GIỮ tên, lùi slice** | Chỉ đúng trên dòng đã resolve identity (cohort thật: 52/83 dòng). Phải hiện coverage; không dùng `product_raw` thay canonical. |
| 5 | Cần kiểm tra | **GỘP 3 nguồn** | Review Queue (pipeline) + Thay đổi nguồn (SOURCE_CHANGED/REMOVED) + Đối chiếu cũ/mới (legacy vs pipeline). Cùng một hành vi người dùng: "có gì tôi phải xử lý?". Badge đếm tổng. |
| 6 | Lịch sử dữ liệu | **ĐỔI TÊN → "Dữ liệu"** | Không chỉ lịch sử run: snapshot upload, coverage calendar (ngày nào đã có dữ liệu, từ snapshot nào), legacy import version, tải XLSX. Trả lời "dữ liệu ngày nào đã nhập/xử lý, truy ngược run nào". |

### D.1 Dữ liệu hiển thị và drill-down theo khu vực
```
Tổng quan (kỳ = tháng mặc định, chọn tuỳ chọn; so kỳ trước)
  KPI: Doanh thu · Số đơn · Số lượng SP · Lợi nhuận KPI (chỉ AUTO, kèm % coverage) · Tiến độ (ngày đã qua/ngày kỳ) · Vs target
  Cần chú ý: N đơn Review · N dòng SOURCE_CHANGED · N đơn REMOVED · N lệch legacy
  Top: nhân viên (doanh thu, đơn) · sản phẩm (chỉ resolved)
  ↓ click KPI → Bán hàng (lọc sẵn) · click nhân viên → Nhân viên/<tên> · click "cần chú ý" → Cần kiểm tra

Nhân viên
  Ma trận: hàng = nhân viên/kênh, cột = tháng (doanh thu, đơn, SP, LN KPI, vs tháng trước, target)
  Cột nguồn: [PIPELINE] / [LEGACY] badge theo ô; ô có cả hai → hiện pipeline, tooltip legacy
  ↓ /nhan-vien/<tên>?ky=… → theo ngày → danh sách đơn → đơn → dòng

Bán hàng
  Bộ lọc → bảng đơn (BH, ngày, NV, kênh, SL, doanh thu, LN KPI, trạng thái, nguồn snapshot)
  ↓ /don/<BH> → dòng (sản phẩm raw + canonical nếu có, SL, giá, LN, lý do Review, nguồn giá, phiên bản nguồn, lịch sử thay đổi)

Sản phẩm (slice cuối)
  Bảng canonical product (SL, doanh thu, LN KPI, số người bán, coverage) → chi tiết → nhân viên bán → đơn

Cần kiểm tra
  [Review Queue] [Thay đổi nguồn] [Đối chiếu cũ/mới]
  Review Queue: theo đơn, nhóm lý do (IDENTITY / PP / ACCOUNTING / KHÁC), tỉ lệ nguyên nhân theo kỳ
  Thay đổi nguồn: dòng CHANGED (cũ → mới, snapshot A → B), đơn REMOVED, đơn ADDED muộn
  Đối chiếu: (tháng, người) legacy vs pipeline: đơn, doanh thu, LN; lệch đã giải thích (A1, DEC-120) vs chưa

Dữ liệu
  Snapshot: uploaded_at, coverage, file, fingerprint, run, trạng thái, số đơn/dòng, AUTO/Review, [Xem][Tải Excel]
  Coverage calendar: ngày × (có dữ liệu từ snapshot nào / trống / đang có xung đột)
  Legacy import: version, ngày import, sheet đã nhập
```

### D.2 Điều hướng
Tab ngang (6 tab) trên header sticky + thanh ngữ cảnh sticky thứ hai chứa bộ
chọn kỳ và bộ lọc — đúng mẫu `.ncc-tabs` + `.ctx-bar` của Tracking. **Không
dựng sidebar**: Tracking không có sidebar để tham chiếu, và 6 tab không cần
"không gian mở rộng" (anti-scope-creep). Mobile: tab cuộn ngang, giữ banner
"tối ưu cho máy tính" như Tracking.

---

## E. TRACKING DESIGN REFERENCE (chỉ đọc; không runtime dependency)

Nguồn tham chiếu: `/Tracking/public/index.html` (CSS inline, token
`--tp-*`, dòng 21–83), `/Tracking/public/kpi-demo.css`. Không framework,
không Tailwind, không build step — Reports chép token + class sang một file
CSS tĩnh riêng (`app/web/static/css/` dự kiến) và dùng trong Jinja.

```
TRACKING_DESIGN_ELEMENTS_TO_REUSE =
  - Token màu: --tp-ink/--tp-ink2/--tp-mut, --tp-bg #f7f7f5, --tp-card/--tp-line (glass),
    --tp-blue #1d5bea (+ -d, --tp-sky), --tp-green/--tp-gold/--tp-red (+ *-bg); quy tắc 80/20 trung tính/thương hiệu
  - Radius --tp-r-sm/md/lg/xl/pill; spacing --tp-s1..s8; một bậc shadow --tp-shadow; transition --tp-tr
  - Typography: 'Segoe UI',system-ui,-apple-system,Roboto,Arial; 16px gốc; font-variant-numeric: tabular-nums trên body;
    nhãn nhỏ uppercase letter-spacing .05em; thang 11/12/13/14/15/17/21–30px; weight 500–800
  - Layout: header sticky 58px + .ctx-bar sticky 38px; container full-width; breakpoint 1180/900/820/760/600; body.lite cho mobile;
    prefers-reduced-motion
  - Điều hướng: .ncc-tabs/.ncc-tab (gạch chân 2px), .sec-nav pill, .kpi-filter pill .on
  - Card: .module/.rules-box (card + border --tp-line + radius xl + h3 14px 18px + .cnt pill)
  - Table: th uppercase 11px/700 nền --tp-line2; td.num căn phải nowrap 600; td.code đậm nowrap; hover dòng = viền inset (không tô nền);
    cột số không bao giờ cắt, cột chữ ellipsis; sticky header chỉ trong khung cuộn nhỏ
  - Button: .act (primary), .ghost, .btn-mini (.danger/.ok/.warn-b), .iconbtn
  - Badge: .tag + .tag-up/.tag-down/.tag-new/.tag-gone; .kpi-status.good/.bad/.warn (color-mix)
  - KPI tiles: .chips/.chip dải liền (auto-fit minmax(130px,1fr), số 30px/700) và .kpi-chip thẻ rời
  - Filter/date: .filter-row, .kpi-period (hộp viền chứa input date)
  - Modal/popover: .pk-ov/.pk-box, .ph-card (label ↔ value), toast #toast, .empty/.kpi-empty, .insight/.kpi-note
  - Format: Intl.NumberFormat("vi-VN") → 1.250.000; rút gọn " tr"/" tỷ"; ngày dd/mm/yyyy; khoá sort YYYY-MM-DD
  - Quy ước màu VN: tăng = đỏ, giảm = xanh lá (chỉ áp cho GIÁ; với doanh thu/lợi nhuận Reports dùng tăng = xanh lá, giảm = đỏ — xem REPORTS_SPECIFIC)
  - Dark mode: ghi đè biến trên body.dark, alias theme khai trên body (không :root)

REPORTS_SPECIFIC_ELEMENTS =
  - Badge origin: [PIPELINE] / [LEGACY] / [SOURCE_CHANGED] / [REMOVED] / [RESULT_REVISED] — Tracking không có khái niệm này
  - Badge trạng thái đơn: AUTO / REVIEW (không tô đẹp Review thành AUTO)
  - Coverage calendar (ngày × snapshot) — component riêng
  - Bảng so kỳ (kỳ này / kỳ trước / Δ %) và ma trận Nhân viên × Tháng có ô hai nguồn
  - Ngữ nghĩa màu cho KPI kinh doanh: tăng doanh thu/lợi nhuận = xanh lá, giảm = đỏ (ngược quy ước giá của Tracking; ghi rõ trong CSS comment)
  - Đơn vị: Reports hiển thị VND nguyên (Decimal) và rút gọn "tr/tỷ" đúng bậc; legacy hiển thị kèm nhãn "nghìn đồng (số cũ)"
  - Nhãn tiếng Việt cho lý do Review (app/beta_presentation.py) — giữ, mở rộng
  - Không có realtime/online presence (.vb-live) — bỏ

DO_NOT_COUPLE =
  - Không import/fetch/hot-link bất kỳ file nào từ domain Tracking (CSP default-src 'self', no-store) — chép CSS vào Reports
  - Không dùng src/auth.js, Firebase Auth/App Check, luồng 2FA, #loginScreen — Reports auth = Cloudflare Access
  - Không dùng src/firebase.js, RTDB rules, listener/node path, cache đồng bộ
  - Không dùng wrangler.toml, _headers, _redirects, CSP của Tracking
  - Không dùng inv-engine/, price-engine/, src/nghiepvu.js, src/ton-sheet.js, public/kpi-engine.js, kpi-demo.js (phụ thuộc DOM/state Tracking), cong-cu/*, kiem/*
  - Không sao chép data contract: inv_map projection, khoá <mã>/<NCC>/<ngày>, mốc cutover, alias — Reports chỉ consume qua contract hiện có (tools/tracking/)
  - Không mirror Tracking sang Reports DB; không lưu raw authority payload xuống browser
```

Rủi ro kỹ thuật khi chép: `--tp-card`/`--tp-line` là màu trong suốt — chỉ
đúng khi có nền `--tp-bg`; phải đặt nền trang trước.

---

## F. HISTORICAL DATA ARCHITECTURE

```
                 ┌─────────────────────────┐        ┌──────────────────────────┐
  Excel cũ ────► │ LEGACY IMPORTER (1 lần / │        │ Accounting workbook upload│
                 │ mỗi phiên bản file)     │        └────────────┬─────────────┘
                 └──────────┬──────────────┘                     ▼
                            ▼                        SOURCE_SNAPSHOT (coverage, fingerprint)
                 legacy_* tables                                 │
                 origin = LEGACY_REFERENCE                       ▼
                 (nguyên trạng, kèm known_defect)   Existing Core Pipeline (KHÔNG ĐỔI)
                            │                                    │  ImportResult + PriceResolutionRecord[] + presented lines
                            │                                    ▼
                            │                        HISTORY WRITER (mới, bên cạnh exporter, không thay exporter)
                            │                                    │
                            │                        order_source_version / order_line_source_version   (trục NGUỒN)
                            │                        order_line_result_version                          (trục KẾT QUẢ)
                            │                        RECONCILER: SAME / CHANGED / ADDED / REMOVED / RESULT_REVISED
                            │                                    │
                            ▼                                    ▼
                 ┌──────────────────────────────────────────────────────────┐
                 │ QUERY / AGGREGATION BACKEND (Python, backend-only)        │
                 │  current view = latest authoritative source × result     │
                 │  legacy view  = phiên bản legacy hiện hành                │
                 │  reconciliation view = legacy ↔ pipeline theo (tháng, NV) │
                 └──────────────────────────┬───────────────────────────────┘
                                            ▼
                                   Presentation models → Jinja → Browser
```

Nguyên tắc chốt:
1. **Pipeline không đổi.** History writer đọc `ImportResult` +
   `PriceResolutionRecord[]` + kết quả trình bày của exporter (để lấy
   AUTO/PENDING đúng một nguồn sự thật) và ghi xuống DB. Golden Baseline
   không bị chạm.
2. **XLSX vẫn là artifact**, không phải database. Mọi query đi qua DB.
3. **Hai origin, hai bộ bảng, một cột `origin` tường minh** trên mọi bảng
   fact; không có view nào `UNION` hai origin thành một con số mà không mang
   nhãn.
4. **Ranh giới network/ADR-101 giữ nguyên:** driver DB (psycopg / sqlite3)
   chỉ được import trong `tools/db/` (mới) hoặc `app/web/`; `app/modules/`
   không biết DB tồn tại.
5. **Backend tính, frontend vẽ.** Không aggregate trong Jinja/JS.

### F.1 Lựa chọn nơi lưu (cần Owner — mục N, quyết định 1)
Production hiện stateless (Render, không Disk, R2 object store). R2 không
phải relational store; history cần query theo kỳ/nhân viên/đơn.

| Phương án | Ưu | Nhược | Khuyến nghị |
|---|---|---|---|
| A. PostgreSQL managed (Render Postgres hoặc tương đương) + SQLite local/test | Đúng ADR-101; nhiều worker gunicorn an toàn; backup managed (16_BACKUP bắt buộc khi có DB) | Thêm 1 dịch vụ trả phí (~US$6–7/tháng) | **KHUYẾN NGHỊ** |
| B. SQLite file trên R2 (tải về/ghi/đẩy lên) | Không thêm dịch vụ | Single-writer; gunicorn nhiều worker → race/corrupt; không backup point-in-time | Loại |
| C. Quay lại Render Disk + SQLite (S071) | Đơn giản | Đã bị S071B supersede; 1 disk/service; không multi-instance | Chỉ khi Owner từ chối A |
| D. Parquet/DuckDB trên R2 | Analytics tốt | Versioning/ghi tăng dần phức tạp, quá sớm cho ~2k dòng/tháng | Loại |

Khối lượng dữ liệu: ~12k dòng/6 tháng (ERP) + ~30k dòng legacy → bất kỳ
lựa chọn nào cũng dư sức; tiêu chí là **an toàn ghi + backup**, không phải
hiệu năng.

---

## G. LEGACY_REFERENCE MODEL (contract/schema, chưa build importer)

```
legacy_import
  import_id            TEXT PK   (ví dụ LEG-20260902-01)
  origin               = 'LEGACY_REFERENCE'  (cột tường minh, không default ẩn)
  source_file_name     TEXT      ("Báo cáo Kinh doanh 2026.xlsx")
  file_fingerprint     TEXT      (sha256 toàn file)
  imported_at          TIMESTAMP (UTC)
  imported_by          TEXT NULL (email từ Cloudflare Access nếu có — xem N.11)
  version_label        TEXT      (Owner đặt: "bản cuối tháng 08/2026")
  sheets_imported      JSON      (danh sách sheet + trạng thái visible/hidden lúc import)
  is_current           BOOL      (đúng một import current; import mới → cũ SUPERSEDED, không xoá)
  notes                TEXT

legacy_summary_row            -- từ Summary 2026 và Summary 2025, mỗi (tháng, người bán) một dòng
  import_id, year, month, seller_label (nguyên văn: "Ly", "Tín Phát", "Nội thành", "Gia dụng", "Linh", "Fanpage", "Miền Bắc"...)
  row_kind             ENUM('SELLER','MONTH_TOTAL','PROGRESS')
  sheet_name, sheet_row
  orders, products, sales_kvnd, converted_revenue_kvnd, profit_kvnd, margin_ratio,
  vs_prev_month_ratio, stock_ratio, actual_profit_kvnd, per_day_kvnd, target_kvnd, vs_target_ratio,
  bonus_kvnd, workdays, base_salary_kvnd, allowance_kvnd, total_salary_kvnd
  formula_text         JSON      (công thức nguyên văn theo cột, để audit; ví dụ F: "=(G7-2750)/5.5%+2750/7.5%")
  unit                 = 'kVND'  (nghìn đồng, tường minh)
  known_defects        JSON      (mã A1..A6 áp cho dòng; ví dụ D64/D71 → 'A4')

legacy_daily_sales            -- từ DataChart 2026 (VND nguyên) + cột so 2025 và target
  import_id, year, month, day, sales_vnd, source_sheet='DataChart 2026'
legacy_monthly_reference      -- DataChart cột AH/AI/AJ + target năm, AveragePerDay, TargetPerDay
  import_id, year, month, sales_2025_vnd, target_year_kvnd, ...

legacy_detail_line            -- từ 56 sheet MM.2026 <tên>; MỖI DÒNG GIỮ NGUYÊN, kể cả dòng số lượng 0, dòng âm, dòng tổng ngày (row_kind)
  import_id, sheet_name, sheet_row (khoá: (import_id, sheet_name, sheet_row))
  year, month, seller_label, layout ENUM('PERSONAL','CHANNEL')
  row_kind ENUM('DETAIL','CONTINUATION','DAY_TOTAL','BLANK_FORMULA')
  date (NULL ở dòng nối tiếp — KHÔNG tự điền, lưu thêm date_inferred từ dòng đầu ngày, cột riêng)
  trans_no, purchase_source (Nơi nhập), product_code_text, quantity,
  kpi_purchase_price_kvnd, sell_price_kvnd, total_sales_kvnd, profit_kvnd,
  delivery_note, delivery_cost_kvnd, actual_purchase_price_kvnd, gross_profit_kvnd,
  brand_note, imei_or_bh_text (nguyên văn; bh_parsed NULL nếu không khớp ^BH\d+$), warranty_text
  -- PII (customer_name, phone, address): KHÔNG import mặc định — xem N.5
  known_defects JSON
```

Quy tắc:
- **Không tính lại** bất kỳ số nào từ dòng chi tiết để "kiểm tra" Summary
  trong importer. Đối chiếu là việc của view reconciliation, và chỉ đối
  chiếu với pipeline, không "sửa" legacy.
- **Version** = mỗi import là một bản; UI chọn bản current; diff giữa hai
  bản legacy (cùng ô, khác giá trị) hiển thị ở "Dữ liệu" → Legacy import.
- Số cũ mang đơn vị `kVND` nguyên trạng; presentation quy đổi để hiển thị
  và luôn ghi nhãn "số cũ (tham chiếu)".
- Legacy **không có** ORDER_KEY; không bao giờ join legacy_detail_line với
  order/line pipeline theo BH (kể cả tháng 08 có BH gõ tay).

---

## H. PIPELINE_GENERATED MODEL

```
source_snapshot                       -- một lần upload workbook kế toán
  snapshot_id          TEXT PK (SNAP-<UTC ts>-<nn>, sortable)
  origin               = 'PIPELINE_GENERATED'
  uploaded_at, uploaded_by NULL
  source_file_name, file_fingerprint (sha256 bytes), file_size
  coverage_start, coverage_end DATE
  coverage_source      ENUM('PARSED_HEADER','DECLARED_BY_UPLOADER','DATA_DERIVED')   -- xem N.2
  data_date_min, data_date_max        (từ dữ liệu, để đối chiếu với coverage)
  row_count, rows_without_order_id, order_count, line_count
  status               ENUM('INGESTED','RECONCILED','REJECTED','SUPERSEDED')
  run_id               FK → run (RunRecord hiện có; giữ nguyên bảng/JSON run hiện tại)
  evidence             JSON (PriceEvidenceSnapshot: tracking capture ids, public_purchase_version_id, identity_store_revision, business_timezone)
  config_snapshot_id, employee_master_snapshot_id, app_version (git sha)

order_source_version                  -- trục NGUỒN, cấp đơn
  order_key            TEXT  (= BH chuẩn hoá)
  snapshot_id          FK
  version_no           INT   (tăng theo thứ tự snapshot mà đơn xuất hiện)
  order_date, employee_raw, employee_normalized, employee_group, customer_code
  line_count, total_sales_vnd, order_fingerprint (sha256 của tập line_fingerprint đã sort)
  change_kind          ENUM('INSERT','SAME','CHANGED','REMOVED_CANDIDATE') so với version trước
  PK (order_key, snapshot_id)

order_line_source_version             -- trục NGUỒN, cấp dòng
  order_key, product_key, occurrence_index      (= ORDER_LINE_KEY, mục I)
  snapshot_id, version_no
  source_row, row_hash, line_fingerprint
  date, product_raw, quantity, sell_price, discount, total_sales_raw, delivery_cost, imei, note_raw, source_profit
  change_kind          ENUM('INSERT','SAME','CHANGED','REMOVED_CANDIDATE')
  changed_fields       JSON  (tên trường + giá trị cũ/mới, khi CHANGED)
  PK (order_key, product_key, occurrence_index, snapshot_id)

order_line_result_version             -- trục KẾT QUẢ (pipeline authoritative), 1 dòng/run/line
  run_id, order_key, product_key, occurrence_index
  status               ENUM('AUTO','PENDING')  (từ exporter presentation — một nguồn sự thật)
  pending_reasons      JSON  (typed: review category, PriceResolutionReason, Pending.<field>)
  identity_namespace, canonical_product_code, identity_status
  accounting_purchase_price, price_source, composition_rule, accounting_profit
  kpi_purchase_price, kpi_purchase_provenance, eligible_kpi_profit
  lead_source_final, product_group_final, conversion_scheme_final, conversion_rate_final, converted_revenue (nếu engine có)
  evidence_ref         (trỏ source_snapshot.evidence)
  PK (run_id, order_key, product_key, occurrence_index)

order_current / order_line_current    -- VIEW (hoặc bảng vật chất hoá) = latest authoritative
  chọn source version theo chính sách N.3 + result version = run mới nhất COMPLETE trên snapshot đó
  cột thêm: conflict_state ENUM('NONE','SOURCE_CHANGED','REMOVED_IN_SOURCE','RESULT_REVISED'), acknowledged_at NULL

review_item                           -- ReviewItem typed payload theo run (không lưu chuỗi render)
  run_id, scope, order_key NULL, source_row NULL, category, severity, diagnostics JSON, provenance JSON
```

Ghi chú:
- `converted_revenue`: engine hiện có `conversion_rate_final` theo dòng; DS
  quy đổi = `eligible_kpi_profit / rate` chỉ có nghĩa khi cả hai không
  `None`. Persist đúng như engine trả, không tự tính ở tầng lưu.
- `run` giữ nguyên `RunRecord` hiện tại (không đổi `RunStore`); chỉ thêm
  liên kết `snapshot_id` trong `view` JSON hoặc cột mới ở bảng history.
- Không persist PII ngoài mức pipeline đã có (`customer`, `phone`, `address`
  nằm trong `WorkingLine`): quyết định N.5 áp cho cả hai origin; mặc định
  đề xuất persist `customer_code` + `customer` (tên) để drill-down, KHÔNG
  persist `phone`/`address`.

---

## I. ORDER / ORDER_LINE IDENTITY (audit dữ liệu thật)

### I.1 Bằng chứng
| Nguồn | Quan sát | Ý nghĩa |
|---|---|---|
| Raw ERP 6 tháng (`docs/analysis/_evidence/evidence.json`) | 11.765 dòng, **8.714 Số BH duy nhất**, 2.139 đơn nhiều dòng (tối đa 10 dòng/đơn), 2 dòng thiếu NV, 52 dòng thiếu SL | BH là khoá đơn tự nhiên; ~25 % đơn có >1 dòng |
| Golden fixture 01/2026 (351 dòng/254 đơn) và 06/2026 (180/146) | 0 đơn nhiều ngày, 0 đơn nhiều nhân viên, 0 đơn có hai dòng cùng chữ ký (sản phẩm, SL, đơn giá, doanh số); 1 dòng không có BH (bị `raw_reader` bỏ) | BH ổn định theo đơn; dòng trùng chữ ký hiếm nhưng KHÔNG loại trừ được (1.074 dòng "Chi phí vận chuyển" trong 6 tháng) |
| `app/modules/orders/order_builder.py` | Nhóm theo `order_id` DUY NHẤT; lấy ngày/NV của dòng đầu; lệch → `OrderInconsistency` | Engine đã coi BH = khoá đơn |
| `app/modules/exporting/excel_exporter.py` | Ghép `PriceResolutionRecord` với dòng theo `(order_id, product_raw, date)` + `deque.popleft` cho dòng lặp | Engine đã ngầm dùng "product + thứ tự xuất hiện" làm khoá dòng |
| Excel cũ, sheet 08.2026 | BH gõ tay ở cột IMEI, có lỗi gõ (BH82897 giữa dải 73xxx); BH lặp trong sheet = đơn nhiều dòng | BH không dùng được cho legacy |
| MISA voucher numbering | BH tăng dần liên tục 62063 (01/2026) → 73xxx (08/2026); có reset đầu năm hay không: **UNKNOWN** | Cần Owner/kế toán xác nhận (N.13) |

### I.2 Kết luận
```
ORDER_KEY      = normalize(Số BH)   -- trim, upper, bỏ khoảng trắng; ví dụ "BH73320"
                 + guard: cùng ORDER_KEY nhưng |order_date_mới − order_date_cũ| > 90 ngày
                   → ORDER_KEY_COLLISION (không SAME, không CHANGED; vào Cần kiểm tra)
                 + nếu kế toán xác nhận BH reset theo năm → ORDER_KEY = (fiscal_year, BH) (N.13)

ORDER_LINE_KEY = (ORDER_KEY, product_key, occurrence_index)
                 product_key      = sha256(NFC(product_raw).casefold().strip())  -- không dùng canonical identity làm khoá (identity có thể đổi giữa hai run)
                 occurrence_index = thứ tự xuất hiện (1..n) của product_key trong đơn, theo source_row tăng dần
line_fingerprint = sha256(date, product_raw_norm, quantity, sell_price, discount, total_sales_raw, delivery_cost, imei_norm, note_raw_norm, employee_raw_norm)
                 (= row_hash hiện có nhưng loại source_row/source_file để bền qua hai lần export)
```

Vì sao không dùng `row_hash` làm khoá dòng: `row_hash` đổi khi bất kỳ trường
nào đổi → CASE 3 sẽ hiện như "1 dòng biến mất + 1 dòng mới", mất khả năng
chỉ ra *trường nào* đổi. Vì sao không dùng `source_row`: thứ tự dòng giữa
hai lần export không được đảm bảo. Vì sao không dùng IMEI làm khoá: vắng ở
phụ kiện/dịch vụ, nhiều IMEI/ô — chỉ dùng làm tín hiệu ghép phụ.

Giới hạn thừa nhận: nếu kế toán **đổi tên hàng** trên một dòng, thuật toán
thấy `REMOVED + INSERT` trong cùng đơn → hiển thị ở cấp đơn là `CHANGED`
(kèm cặp dòng ghép theo `occurrence`/IMEI nếu có). Đây là fail-safe đúng:
không đoán, người dùng nhìn thấy.

---

## J. SNAPSHOT / VERSION / RECONCILIATION MODEL

### J.1 Thuật toán reconcile khi có snapshot mới S_new
```
1. Fingerprint file: nếu file_fingerprint đã tồn tại → ghi sự kiện RE_UPLOAD, KHÔNG tạo source version mới
   (vẫn được phép tạo run mới → chỉ sinh result version; xem J.3).
2. Coverage: [cov_start, cov_end] theo N.2. Ứng viên so sánh = tập dòng current có date ∈ coverage
   (từ mọi snapshot trước KHÔNG bị REJECTED).
3. Với mỗi ORDER_LINE_KEY trong S_new:
     không có version trước                       → INSERT           (CASE 1)
     có, line_fingerprint bằng                     → SAME             (CASE 2; version_no giữ, trỏ snapshot mới nhất)
     có, fingerprint khác                          → CHANGED          (CASE 3; version_no+1, changed_fields, conflict_state=SOURCE_CHANGED)
4. Với mỗi ORDER_LINE_KEY current có date ∈ coverage nhưng KHÔNG có trong S_new
                                                    → REMOVED_CANDIDATE (CASE 4; conflict_state=REMOVED_IN_SOURCE; KHÔNG xoá)
5. Cấp đơn: tổng hợp từ dòng; ORDER_KEY_COLLISION theo I.2.
6. Nếu coverage_source = DATA_DERIVED (không có header/declared): bước 4 bị TẮT (không thể phân biệt
   "ngày không có đơn" với "ngày ngoài coverage") và snapshot được gắn cờ COVERAGE_UNVERIFIED.
```

### J.2 Latest authoritative view
- Mặc định đề xuất (cần Owner N.3/N.4): **snapshot mới nhất thắng** cho
  CHANGED (sổ kế toán mới nhất là sự thật kế toán) nhưng cờ
  `SOURCE_CHANGED` tồn tại đến khi có người bấm "đã xem"; REMOVED
  **loại khỏi tổng hiện hành** nhưng giữ bản ghi + cờ.
- Không bao giờ có hai source version cùng "current" cho một khoá → không
  double-count ở tầng mô hình, không chỉ ở tầng query.

### J.3 Trục kết quả (RESULT_REVISED)
Chạy lại cùng file (hoặc snapshot mới có dòng SAME) với evidence Tracking
mới có thể đổi AUTO/PENDING, giá, LN KPI. Đây **không** là conflict nguồn:
ghi `order_line_result_version` mới, current trỏ run mới nhất COMPLETE,
cờ `RESULT_REVISED` khi `status` hoặc `eligible_kpi_profit` đổi so với
result version trước. Người dùng thấy "đơn X: PENDING → AUTO sau run
R2 (capture PP mới)". Không có "wrong AUTO" mới sinh ra ở tầng lưu vì tầng
lưu không quyết định gì — nó chỉ ghi lại engine đã quyết gì và với evidence
nào.

### J.4 Điều gì được phép và không được phép
- Được: đánh dấu SUPERSEDED/REJECTED một snapshot (soft), ghi
  acknowledged_at cho conflict.
- Không: `DELETE` bản ghi fact; `UPDATE` tại chỗ một source version;
  tự "merge" hai dòng; tự chọn giá trị "đúng" giữa cũ/mới ở tầng lưu.

---

## K. OVERLAPPING UPLOAD EXAMPLE — 01–10/09 vs 01–30/09

```
Ngày 10/09 15:00  upload "So_chi_tiet_ban_hang (9a).xlsx"  coverage 01/09–10/09 (parse header dòng 2)
  → SNAP-A: 210 dòng / 152 đơn (giả định), fingerprint fa…
  → tất cả INSERT (CASE 1). Run R-A: 60 AUTO / 92 REVIEW.
  → Coverage calendar: 01–10/09 = SNAP-A. Lưu ý 10/09 có thể chưa trọn ngày.

Ngày 01/10 09:00  upload "So_chi_tiet_ban_hang (9).xlsx"   coverage 01/09–30/09
  → SNAP-B: 655 dòng / 470 đơn, fingerprint fb… (khác fa… → không phải RE_UPLOAD)
  Reconcile với current có date ∈ [01/09, 30/09]:
    - 204 dòng của SNAP-A có fingerprint bằng → SAME     : current trỏ SNAP-B, KHÔNG tăng version, KHÔNG đếm 2 lần
    - 3 dòng SNAP-A khác fingerprint             → CHANGED  : ví dụ BH74102/FV1410S4W1#1: sell_price 7.500.000 → 7.300.000
                                                              (changed_fields ghi rõ; conflict_state=SOURCE_CHANGED; hiện ở Cần kiểm tra → Thay đổi nguồn)
    - 2 dòng SNAP-A không còn trong SNAP-B       → REMOVED_CANDIDATE : ví dụ BH74088 (kế toán huỷ chứng từ)
                                                              (loại khỏi tổng hiện hành theo N.4, KHÔNG xoá, hiện cảnh báo "đơn biến mất")
    - 8 dòng mới có date ≤ 10/09                 → INSERT    : đơn nhập muộn cho ngày 09–10/09 (bình thường; ghi "ADDED_LATE" để thống kê)
    - 440 dòng có date 11–30/09                  → INSERT
  Run R-B trên SNAP-B: kết quả theo dòng ghi result version; dòng SAME có thể đổi PENDING→AUTO nếu PP history đã bổ sung → RESULT_REVISED (không phải conflict nguồn).

Tổng quan tháng 09 sau 01/10:
  Số đơn = COUNT(order_current, date ∈ 09, conflict_state ≠ REMOVED_IN_SOURCE) = 468 (470 − 2 REMOVED)
  Doanh thu = SUM(order_line_current.total_sales) — mỗi khoá đúng một lần
  Cần chú ý: 3 dòng SOURCE_CHANGED · 2 đơn REMOVED · 8 đơn ADDED_LATE · N đơn REVIEW
Dữ liệu → Coverage calendar: 01–30/09 = SNAP-B (01–10/09 ghi "SNAP-A → SNAP-B, 3 changed, 2 removed")
```

Trường hợp biên đã tính đến: (a) upload lại đúng file 9a → RE_UPLOAD, không
sinh version; (b) upload 15–30/09 trước rồi 01–30/09 sau → vẫn đúng vì
reconcile theo coverage chứ không theo thứ tự upload; (c) BH của tháng 09
trùng BH tháng 01 do reset năm (nếu có) → ORDER_KEY_COLLISION vì lệch >90
ngày, không SAME.

---

## L. ANALYTICS OPPORTUNITIES — NOW / LATER / DEFER

Định nghĩa dùng chung: "kỳ" = tháng (mặc định) hoặc khoảng ngày; "kỳ trước"
= kỳ liền trước cùng độ dài; mọi số tiền = VND nguyên từ engine; LN KPI chỉ
tính trên dòng AUTO và luôn kèm `coverage = dòng AUTO / tổng dòng`.

| Analytics | Phân loại | Nguồn/định nghĩa | Ghi chú |
|---|---|---|---|
| Doanh thu theo kỳ, theo nhân viên/kênh | **NOW** (slice 3) | `total_sales` current | Khớp cột "Tổng bán" cũ |
| Số đơn | **NOW** | COUNT order_current | Khớp "Tổng đơn" (count Trans) |
| Số lượng SP | **NOW** (định nghĩa cần Owner N.7) | SUM quantity dòng không thuộc `non_product_lines` (config validation hiện có) | Excel cũ tính sai (A1); Reports ra số nguyên, lớn hơn 0,05–0,3 |
| Lợi nhuận KPI (eligible) + coverage | **NOW** | `eligible_kpi_profit` dòng AUTO | Không "đẹp hoá": Review không tính |
| So tháng trước (Δ %, tuyệt đối) | **NOW** | current kỳ vs kỳ trước | Trống khi kỳ trước không có dữ liệu (không dùng 0) |
| Target attainment + tiến độ trong tháng | **NOW** (cần target — N.8) | `config/targets` (mới) theo (nhân viên/kênh, tháng) | Excel: target/người/tháng + target năm |
| Employee contribution (share) | **NOW** | doanh thu NV / tổng | |
| Review burden (đơn/dòng Review, theo nhóm lý do, theo kỳ) | **NOW** (slice 4) | `review_item` + `pending_reasons` | Bằng chứng để chọn vertical tiếp theo |
| Source-data revisions (CHANGED/REMOVED/ADDED_LATE theo snapshot) | **NOW** (slice 2) | reconciler | |
| Legacy-vs-pipeline reconciliation (đơn, doanh thu, LN theo tháng × NV) | **NOW-lite** (slice 3: bảng lệch) | legacy_summary_row vs aggregate pipeline | Lệch "đã giải thích" (A1, A2, DEC-120 6 %) tách riêng |
| Doanh thu quy đổi (ConversionScheme) | **LATER** | `conversion_rate_final` × LN KPI | Chờ engine chốt `converted_revenue` theo dòng có provenance; không tính ở tầng UI |
| Margin (tỉ suất) | **LATER** (N.7) | LN KPI/doanh thu hay LN kế toán/doanh thu — Owner chọn | |
| Average order value | **LATER** | doanh thu/đơn | Rẻ, nhưng chưa có nhu cầu trong Excel cũ |
| Cùng kỳ năm trước, YTD | **LATER** | legacy Summary 2025 (tháng) + DataChart | Chỉ theo tháng; nguồn 2025 là legacy |
| Sales mix theo kênh (employee_group) × nhóm hàng (product_group) | **LATER** | model đã có 2 chiều | Sau khi có ≥2 tháng pipeline |
| Product contribution / concentration (top N, Pareto) | **LATER** (slice 5) | canonical identity, chỉ dòng resolved | Phải hiện coverage identity |
| Employee trend (nhiều tháng) | **LATER** | cần ≥3 tháng pipeline | Legacy có 8 tháng nhưng khác định nghĩa |
| Tỉ lệ tồn kho (Kho vs NCC) | **DEFER** | cần `Nơi nhập` — không có trong file ERP; có thể nằm ở Tracking | Nếu lấy từ Tracking → ARCHITECTURE_DEPENDENCY, không làm |
| Thưởng/lương (bậc thưởng, ngày công) | **DEFER** (N.9) | HR rule ngoài spec Reports hiện có | |
| Anomaly detection | **DEFER** | | Chưa có baseline đủ dài; cảnh báo rule-based (đơn REMOVED, giá đổi) đã phủ nhu cầu |
| Dashboard hôm nay/tuần realtime | **DEFER** | dữ liệu đến theo lần upload, không realtime | Bộ chọn "hôm nay/tuần" trong MD là hứa hẹn sai với nguồn batch |

---

## M. VERTICAL ROADMAP

Thứ tự: **1 → 2 → 3 → 4 → 5.** Slice 1 nhỏ, cho thấy dữ liệu cũ trong
Reports và đặt nền DB; slice 2 là nền cho mọi thứ sau; slice 3 mới là
"dashboard". Không dựng 6 trang trước persistence.

### SLICE 1 — TASK-PRA-001: Legacy reference + nền history DB
```
GOAL                     = Owner xem được Summary/DataChart cũ trong Reports, với badge LEGACY, đúng số như Excel; DB history tồn tại và có migration.
USER_VISIBLE_OUTCOME     = Tab "Dữ liệu" (khung tối thiểu) hiển thị legacy import đã nhập; tab "Nhân viên" bản legacy: ma trận tháng × người bán (Tổng đơn, SP, Tổng bán, LN, vs tháng trước, target, vs target) + trang "Doanh số theo ngày" từ DataChart; ô có known_defect hiện dấu (i) "Số cũ có lỗi công thức A4".
DATA_REQUIRED            = File Excel cũ (Owner cung cấp, không commit — PII, xem .gitignore hiện có); bảng legacy_* (mục G).
MODULES_TOUCHED          = tools/db (mới: engine/migration, driver ngoài app/), app/web/history_store (mới, interface), tools/legacy (mới: importer CLI đọc openpyxl), app/web/server.py (+3 route GET), templates mới + app/web/static/css (token Tracking), tests mới.
PROTECTED_CORE_IMPACT    = NONE (không import app/modules/* ngoài domain models; không chạm pipeline/exporter).
TRACKING_CHANGE_REQUIRED = NO.
TEST_STRATEGY            = Fixture Excel legacy tổng hợp (anonymized, 2 tháng × 3 người + 1 kênh, cố ý chứa A1/A3/A4/A6) → import → assert từng ô bằng giá trị Excel; test "importer không tính lại" (mutate công thức nhưng giữ giá trị → số không đổi); migration up/down trên SQLite; route render (Flask test client); CHECK-105D-17 giữ PASS (không import network/DB driver dưới app/).
ACCEPTANCE_CRITERIA      = (1) 100 % ô Summary 2026/2025/DataChart của file thật khớp giá trị Excel (E1: script đối chiếu in tổng ô khớp/lệch = N/0); (2) mọi bảng legacy có origin='LEGACY_REFERENCE'; (3) không có phép chia bù /2 hay công thức nào trong importer; (4) UI có badge LEGACY trên mọi số; (5) full regression không giảm; (6) validator governance PASS.
DEFERRED                 = import legacy_detail_line 56 sheet (làm ở slice 3 nếu cần đối chiếu theo ngày; Summary đủ cho so sánh tháng); PII legacy (N.5); diff giữa hai bản legacy (chỉ ghi version, chưa diff UI).
RECOMMENDED_MODEL        = Tier B (Sonnet) implement; Tier C (Opus) review độc lập schema/migration.
RECOMMENDED_EFFORT       = 1–2 session MAJOR (nhỏ nếu Owner đã chốt N.1 trước khi mở).
```

### SLICE 2 — TASK-PRA-002: Persistence pipeline + overlapping-upload reconciliation
```
GOAL                     = Mỗi run ghi snapshot + source/result version; upload 01–10 rồi 01–30 không double-count; CHANGED/REMOVED nhìn thấy được.
USER_VISIBLE_OUTCOME     = Tab "Dữ liệu": danh sách snapshot (coverage, fingerprint, run, đơn/dòng, AUTO/Review), coverage calendar theo ngày; Tab "Cần kiểm tra" → "Thay đổi nguồn": dòng CHANGED (cũ→mới), đơn REMOVED, ADDED_LATE, ORDER_KEY_COLLISION; form upload có ô coverage (điền sẵn từ header dòng 2, cho phép sửa theo N.2).
DATA_REQUIRED            = source_snapshot, order_source_version, order_line_source_version, order_line_result_version, review_item, current views (mục H); parse "Từ ngày … đến ngày …" ở dòng 2 workbook.
MODULES_TOUCHED          = app/web/history_writer (mới, gọi sau exporter), app/modules/exporting/excel_exporter.py (CHỈ tách hàm present_lines() thành public, không đổi hành vi — cần test parity byte-identical XLSX), app/web/reconciler (mới, thuần Python, không I/O), app/web/server.py (run_report gọi writer trong cùng transaction với create_run: fail-closed — writer lỗi → run FAILED, không có run "thành công" mà history trống), templates.
PROTECTED_CORE_IMPACT    = NONE về business rule. Chạm exporter ở mức "expose hàm" — Golden Baseline + test XLSX parity là gate; nếu không tách được sạch → persist từ output exporter (đọc lại _PresentedLine) thay vì sửa exporter.
TRACKING_CHANGE_REQUIRED = NO.
TEST_STRATEGY            = Unit reconciler với 4 CASE + 3 biên (RE_UPLOAD, coverage lệch thứ tự, COLLISION) bằng fixture synthetic hai snapshot; integration: golden period_2026_01.xlsx cắt thành 01–10 và 01–31 (script tạo fixture, anonymized) → chạy hai lần qua Flask test client → assert COUNT đơn = 254, không dòng nào đếm 2 lần, CHANGED=0; thêm biến thể sửa 1 đơn giá + xoá 1 đơn → CHANGED=1, REMOVED=1; test fail-closed (DB lỗi → 503, không có run mồ côi); test PII không vào bảng ngoài phạm vi N.5; CHECK-105D-17.
ACCEPTANCE_CRITERIA      = (1) kịch bản mục K tái hiện bằng fixture, số đơn/doanh thu tháng bằng đúng file 01–30 trừ REMOVED; (2) mọi thay đổi có provenance (snapshot A → B, trường đổi); (3) không DELETE/UPDATE-in-place fact nào (test grep + test hành vi); (4) Golden Baseline `58 passed, 2 skipped` không đổi; (5) real cohort S068 rerun cho đúng 22 AUTO/36 Review và history ghi đúng 58 đơn/83 dòng; (6) coverage DATA_DERIVED tắt CASE 4 và gắn cờ.
DEFERRED                 = acknowledge/resolve conflict bằng UI (chỉ đọc ở slice này); uploaded_by; retention/xoá snapshot; multi-file batch upload.
RECOMMENDED_MODEL        = Tier C (Opus) — data integrity, blast radius theo failure path = sai tổng doanh thu/đơn; Independent Review E2 theo `governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`.
RECOMMENDED_EFFORT       = 2–3 session MAJOR (+1 review). Review budget HIGH = 2 blocking repair cycles (V4.1).
```

### SLICE 3 — TASK-PRA-003: Tổng quan + Nhân viên từ history thật
```
GOAL                     = Trang mặc định trả lời "kỳ này thế nào, so kỳ trước, có gì cần chú ý" từ DB, và ma trận Nhân viên × Tháng hai nguồn.
USER_VISIBLE_OUTCOME     = Tổng quan: KPI kỳ (doanh thu, đơn, SP, LN KPI + coverage, tiến độ, vs target), so kỳ trước, "cần chú ý" (Review, SOURCE_CHANGED, REMOVED, lệch legacy), top nhân viên; Nhân viên: ma trận + trang chi tiết người → theo ngày → đơn; Cần kiểm tra → Đối chiếu cũ/mới: bảng lệch theo (tháng, NV) với cột "đã giải thích".
DATA_REQUIRED            = current views (slice 2), legacy_summary_row (slice 1), config/targets (mới, YAML, Owner cung cấp theo N.8), định nghĩa Số SP (N.7).
MODULES_TOUCHED          = app/web/analytics_queries (mới: SQL/aggregation, backend-only), app/web/presentation (mới: presentation models), routes + templates, config/targets (mới). Không chạm engine.
PROTECTED_CORE_IMPACT    = NONE.
TRACKING_CHANGE_REQUIRED = NO.
TEST_STRATEGY            = Test aggregation trên DB seed từ golden expected JSON (`money`, `counts`, `employees`) → số trên trang = số trong JSON; test "kỳ trước trống → ô trống, không 0"; test LN KPI chỉ cộng dòng AUTO; test badge nguồn khi ô có cả LEGACY và PIPELINE; snapshot test HTML tối thiểu (không test CSS).
ACCEPTANCE_CRITERIA      = (1) Tổng quan tháng golden 01/2026 khớp `tests/fixtures/golden/expected/period_2026_01.json` (`money.total_sales`, `counts.orders`); (2) không có tính toán nghiệp vụ trong Jinja/JS (grep + review); (3) trang không lộ secret/absolute path/raw authority; (4) legacy và pipeline không bao giờ cộng chung một ô; (5) tải trang < 1 s trên 12k dòng (đo, E1).
DEFERRED                 = biểu đồ xu hướng (chỉ bảng + sparkline text ở slice này); YTD/cùng kỳ; AOV; margin.
RECOMMENDED_MODEL        = Tier B (Sonnet); Tier D cho polish visual nếu có.
RECOMMENDED_EFFORT       = 1–2 session MAJOR.
```

### SLICE 4 — TASK-PRA-004: Bán hàng drill-down + Review Operations trên web
```
GOAL                     = Kỳ → đơn → dòng trên web; Review Queue vận hành được không cần mở XLSX.
USER_VISIBLE_OUTCOME     = Bán hàng: bộ lọc + bảng đơn + trang đơn (dòng, lý do, nguồn giá, lịch sử source/result version); Cần kiểm tra → Review Queue: danh sách đơn theo nhóm lý do (Identity / PP / Accounting / Khác), tỉ lệ nguyên nhân theo kỳ, [Xem đơn]; nút "đã xem" cho SOURCE_CHANGED/REMOVED (ghi acknowledged_at, không đổi dữ liệu).
DATA_REQUIRED            = review_item, order_line_result_version.pending_reasons, current views; ánh xạ lý do → nhóm (mở rộng `app/beta_presentation.py`, không tạo taxonomy thứ hai).
MODULES_TOUCHED          = routes/templates/queries; app/beta_presentation.py (thêm nhãn nhóm); bảng acknowledgement (mới).
PROTECTED_CORE_IMPACT    = NONE (Review không bị biến thành AUTO; acknowledge chỉ là metadata UI).
TRACKING_CHANGE_REQUIRED = NO.
TEST_STRATEGY            = Test nhóm lý do phủ 100 % enum PriceResolutionReason + review category (test exhaustiveness); test acknowledge không đổi conflict_state/dữ liệu; test bộ lọc trả đúng tập; test trang đơn hiển thị đủ phiên bản.
ACCEPTANCE_CRITERIA      = (1) mọi đơn Review trong XLSX xuất hiện trên web với cùng lý do (đối chiếu cohort 36 đơn/60 dòng); (2) tỉ lệ nguyên nhân theo kỳ cộng đúng 100 %; (3) không route nào nhận path/ID tuỳ ý ngoài khoá đã validate.
DEFERRED                 = hành động xử lý Review từ web (classify identity, nhập giá) — đó là Tracking workflow/Owner workflow, KHÔNG làm trong Reports; export CSV bộ lọc.
RECOMMENDED_MODEL        = Tier B.
RECOMMENDED_EFFORT       = 1–2 session MAJOR.
```

### SLICE 5 — TASK-PRA-005: Sản phẩm (canonical) + analytics LATER
```
GOAL                     = Phân tích theo canonical product trên dòng đã resolve, có coverage; bật các analytics LATER đã có dữ liệu.
USER_VISIBLE_OUTCOME     = Sản phẩm: bảng + chi tiết (SL, doanh thu, LN KPI, số người bán, coverage identity); Tổng quan thêm top sản phẩm; sales mix kênh × nhóm hàng; xu hướng nhân viên ≥3 tháng; YTD/cùng kỳ từ legacy 2025.
DATA_REQUIRED            = order_line_result_version.canonical_product_code + identity_namespace; ≥2–3 tháng pipeline; legacy_summary_row 2025.
MODULES_TOUCHED          = queries/presentation/templates.
PROTECTED_CORE_IMPACT    = NONE; Product Identity Authority vẫn là Tracking; không fuzzy, không suy đoán identity từ product_raw ở tầng analytics.
TRACKING_CHANGE_REQUIRED = NO (nếu cần thêm thuộc tính hãng/nhóm hàng từ Tracking → ARCHITECTURE_DEPENDENCY, không làm).
TEST_STRATEGY            = Test chỉ dòng identity RESOLVED được gộp; test coverage hiển thị; test top-N ổn định (tie-break xác định).
ACCEPTANCE_CRITERIA      = (1) tổng doanh thu theo sản phẩm + phần "chưa xác định" = tổng doanh thu kỳ; (2) không có sản phẩm nào sinh từ tên raw.
DEFERRED                 = hãng/nhóm hàng; tồn kho; anomaly; forecasting.
RECOMMENDED_MODEL        = Tier B.
RECOMMENDED_EFFORT       = 1–2 session MAJOR.
```

Ngân sách 90/10: mỗi slice dành ≤10 % cho hardening (retention, uploaded_by,
dark mode, mobile polish) và chỉ khi vertical đã xanh.

---

## N. OWNER_DECISIONS_REQUIRED

| # | Quyết định | Chặn | Khuyến nghị |
|---|---|---|---|
| 1 | Nơi lưu history trên production (PostgreSQL managed / Render Disk / khác) — kéo theo chi phí và backup | Slice 1 | PostgreSQL managed + SQLite local/test (ADR-101) |
| 2 | Nguồn coverage của snapshot: parse dòng 2 workbook ("Từ ngày … đến ngày …") là authority, hay người upload khai báo và có thể sửa | Slice 2 | Parse header là mặc định; cho phép sửa có ghi vết; nếu không có cả hai → DATA_DERIVED + tắt CASE 4 |
| 3 | Chính sách CHANGED: snapshot mới nhất thắng (có cờ) hay giữ cũ đến khi xác nhận | Slice 2 | Mới nhất thắng + cờ + acknowledge |
| 4 | Chính sách REMOVED: loại khỏi tổng hiện hành (có cờ) hay vẫn tính | Slice 2 | Loại khỏi tổng + cờ, không xoá |
| 5 | PII trong DB history: persist tên khách? SĐT/địa chỉ? (cả pipeline lẫn legacy) | Slice 1–2 | Tên + mã KH có; SĐT/địa chỉ không |
| 6 | Legacy: lưu nguyên trạng + annotate lỗi A1–A6, không sửa số cũ | Slice 1 | Đồng ý như đề xuất |
| 7 | Định nghĩa "Số lượng SP" (loại dòng phí/phụ kiện theo `non_product_lines`?) và "Lợi nhuận"/"Margin" trên dashboard (KPI eligible vs kế toán) | Slice 3 | SP = SUM qty trừ non_product_lines; LN = eligible KPI (AUTO) + coverage; margin LATER |
| 8 | Nguồn target theo (nhân viên/kênh, tháng) và target công ty 2026 — Owner cung cấp file/YAML | Slice 3 | `config/targets` YAML có effective_from |
| 9 | Lương/thưởng/ngày công (cột O–S Summary) có thuộc scope Reports không | Roadmap | DEFER, ngoài spec KPI hiện có |
| 10 | Ô có cả LEGACY và PIPELINE (tháng 01–08/2026): hiển thị pipeline chính, legacy tooltip — đồng ý? | Slice 3 | Đồng ý |
| 11 | Dùng header Cloudflare Access (email) làm `uploaded_by`/`acknowledged_by` — xác nhận Access đang bật trên production | Slice 2 (hardening) | Có, fallback "unknown" |
| 12 | Ratify amendment ADR-101: web layer = Flask/Jinja (không FastAPI/React), DB theo ADR-101 | Slice 1 | Ratify |
| 13 | Kế toán xác nhận: Số BH có reset theo năm/kỳ không; có tái sử dụng BH khi huỷ chứng từ không | Slice 2 | Hỏi kế toán; guard 90 ngày vẫn bật |

Ngoài ra `UNKNOWN`: ý nghĩa "Doanh số" trong DataChart khác "Tổng bán"
Summary (không chặn; lưu legacy nguyên trạng, không diễn giải).

---

## O. RISKS

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| Nhầm trục nguồn ↔ trục kết quả → conflict giả hoặc double-count | CAO | Hai bảng version tách, reconciler thuần, test 4 CASE + RESULT_REVISED |
| Persistence gắn vào exporter làm lệch AUTO/PENDING với XLSX | CAO | Một nguồn sự thật (present_lines), test parity XLSX byte-identical, Golden Baseline |
| Production stateless không có nơi đặt DB; chọn sai → mất dữ liệu | CAO | Quyết định N.1 trước slice 1; backup managed; fail-closed khi DB vắng (như REPORTS_REQUIRE_R2) |
| PII mở rộng vào DB (17_DATA_GOVERNANCE) | TRUNG | N.5; không persist SĐT/địa chỉ; DB có access control + backup mã hoá |
| Coverage sai (header thiếu/ngày chưa trọn) → REMOVED giả | TRUNG | N.2; DATA_DERIVED tắt CASE 4; ADDED_LATE thống kê riêng |
| BH reset theo năm | THẤP–TRUNG | Guard 90 ngày; N.13 |
| Session sau refactor web layer "cho đúng ADR-101" | TRUNG | N.12; ghi amendment ADR |
| Legacy bị hiểu là authority mới; người dùng so sánh số cũ/mới rồi "sửa" | TRUNG | Badge origin bắt buộc, lệch đã-giải-thích tách riêng, không sửa legacy |
| Scope creep dashboard (chart vì vẽ được) | TRUNG | Bảng trước, chart sau khi có nhu cầu; DEFER list |
| Result thay đổi theo evidence Tracking gây "nhiễu" RESULT_REVISED | THẤP | Chỉ cờ khi status/LN đổi; gộp theo run |
| `beta_feedback`/`beta_telemetry` ghi REPO_ROOT trên Render (mất) | THẤP (không chặn) | Chuyển sang DB history ở slice 2 hardening (≤10 %) |

---

## P. DEFERRED_FINDINGS (không tự sinh task)

1. `beta_feedback.py`/`beta_telemetry.py` ghi JSONL vào REPO_ROOT → mất
   trên Render mỗi lần restart. Không chặn vertical hiện tại; gộp vào
   hardening slice 2.
2. `raw_reader.py` bỏ im lặng dòng không có Số BH (fixture: 1 dòng). Snapshot
   sẽ đếm `rows_without_order_id` độc lập (đọc sheet) — không sửa reader.
3. Không có retention/xoá cho `runs/` và `artifacts/` trên R2.
4. Excel cũ: lỗi A4 (tham chiếu sai sheet cho số SP Nội thành) vẫn tồn tại
   ở tháng 07 và 08/2026 — chỉ annotate, không sửa file.
5. Excel cũ: DataChart và Summary dùng hai nguồn doanh số khác nhau —
   UNKNOWN, ghi nhận.
6. Tên hàng kế toán đổi giữa hai snapshot hiện ra là REMOVED+INSERT trong
   đơn — fail-safe, chấp nhận; cải thiện ghép bằng IMEI nếu thực tế cần.
7. `inv.map`/`alias.map`/`board` không có temporal safety net (đã DEFERRED từ
   S069) — analytics chỉ ghi lại engine quyết gì; không xử lý thêm.
8. Tỉ lệ tồn kho (`Nơi nhập`) không có trong nguồn ERP — không tái tạo
   được; nếu muốn cần Tracking → ARCHITECTURE_DEPENDENCY, không làm.

---

## Q. SCOPE_DRIFT = NO

Không sửa Tracking; không sửa protected core (Product Identity, PP/PP
History/Baseline, PricingEffectiveDate, Accounting reconciliation,
AUTO/Pending); không refactor web layer; không mirror Tracking; không thêm
tab ngoài 6; không biến finding thành task.

---

## R. RECOMMENDED_NEXT_VERTICAL_ACTION

1. Owner trả lời tối thiểu 4 quyết định chặn: **N.1 (DB production), N.2
   (coverage), N.3 (CHANGED), N.4 (REMOVED)** và ratify N.12 — có thể trả
   lời trong một tin nhắn.
2. Mở **TASK-PRA-001 (Slice 1)** theo Roadmap Finalization
   (`governance/core/00_SESSION_ORCHESTRATION.md` → "Hoàn thiện Roadmap"):
   viết task file từ `governance/templates/TASK_DEFINITION_TEMPLATE.md`,
   freeze Completion Gate từ ACCEPTANCE_CRITERIA của slice 1, Ready Gate
   gồm: N.1 đã chốt, file Excel cũ có trên máy chạy (không commit), ADR
   amendment N.12 đã ghi.
3. Ngay trong slice 1, chuẩn bị fixture hai-snapshot cho slice 2 (cắt golden
   01/2026 thành 01–10 và 01–31, anonymized) để slice 2 mở là có test ngay.

---

## Ready Gate (của chính task planning này)
- [x] Đồng bộ nhánh: HEAD = origin/`claude/extract-upload-repo-gq2ws4` = `596564b`.
- [x] Đọc S000: PROJECT_PROFILE_STANDARD, RULE_PRECEDENCE, TASK_MODE_STANDARD, 00_SESSION_ORCHESTRATION, V4_1_POLICY_FREEZE.
- [x] Đọc PROJECT_PROFILE (PRODUCT), PROJECT_PROGRESS (canonical 2026-09-01).
- [x] Audit Reports (web, persistence, pipeline output, import, export, validation, Tracking integration, tests, deployment).
- [x] Audit Excel cũ bằng script (59 sheet, BH, Trans, dòng âm/0, kênh, công thức).
- [x] Audit file MD kiến trúc UI.
- [x] Audit Tracking design (chỉ đọc).

## Completion Gate

### CHECK-PRA000-01 — Kế hoạch có đủ 18 mục A–R, mỗi slice đủ 11 trường
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`grep -c "^## [A-R]\. " docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md` → 18; `grep -c "^GOAL " …` → 5, `grep -c "^RECOMMENDED_EFFORT " …` → 5 (xem session handoff S072 mục Evidence).

Executed By:
Claude (S072)

Timestamp:
2026-09-02

### CHECK-PRA000-02 — Số liệu audit Excel/raw trong tài liệu tái tạo được bằng script
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Script audit (openpyxl) trên file Owner cung cấp: 59 sheet; BH chỉ ở 3 sheet 08.2026 (86/57/58 dòng có BH; 84/56/54 BH duy nhất); 6 BH lặp trong sheet đều là đơn nhiều dòng; `BH appearing in >1 sheet: 0`; dải BH 66731–82897; Nội thành 15 dòng tổng ngày, `SUM(G)=12.770.800`, tổng dòng sản phẩm `6.385.400 = G1`. Fixture golden: 351 dòng/254 đơn và 180/146, `orders_multi_date=0`, `orders_multi_employee=0`, `orders_with_identical_line_sig=0`. Output nguyên văn lưu trong session handoff S072.

Executed By:
Claude (S072)

Timestamp:
2026-09-02

### CHECK-PRA000-03 — Không thay đổi code production/Tracking; validator governance PASS
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`git diff --stat` chỉ gồm docs/tasks, docs/sessions, PROJECT/*.md; `git -C /home/user/Tracking status` không dùng để ghi (không có thay đổi nào tạo ra ở Tracking); 4/5 validator governance PASS sau khi viết tài liệu (structure, project_state, task_completion 8 DONE, evidence 91 record); `validate_reference_integrity.py` FAIL với đúng 3 reference có sẵn từ trước trong `docs/tasks/TASK-REM-T06-repository-root-hygiene.md` (README/CODE_OF_CONDUCT/CONTRIBUTING — forward reference của task DO_WHEN_IDLE), kết quả y hệt khi chạy trên baseline không có thay đổi của S072 (`git stash -u` rồi chạy lại) — S072 thêm 0 reference hỏng. Output nguyên văn trong session handoff S072.

Executed By:
Claude (S072)

Timestamp:
2026-09-02

## Tiêu Chí Hoàn Thành (Exit Criteria)
- [x] 100% REQUIRED checks PASS
- [x] Không có lỗi nghiêm trọng (critical) chưa xử lý
- [x] Đạt mức evidence yêu cầu (Risk 2 → E1)
- [x] Tài liệu bắt buộc đã được cập nhật
- [x] Tiến độ dự án đã được cập nhật (`PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`)
- [x] Đã viết Session Handoff (`docs/sessions/S072-persistent-reporting-analytics-planning.md`)

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- `docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md`
- `docs/sessions/S072-persistent-reporting-analytics-planning.md`

Modified:
- `PROJECT/PROJECT_PROGRESS.md`
- `PROJECT/LO_TRINH_DE_HIEU.md`

Deleted:
- (không)

Migration Impact:
- Không. Chỉ tài liệu.
