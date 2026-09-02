# S078R — Repair Legacy Import Memory (OOM production)

Date: 2026-09-02
Task Mode: MICRO (một bug fix trên production path; không kiến trúc mới)
Branch: `claude/extract-upload-repo-gq2ws4`
Base: `c0fc2f764bde9237ed3ffaa04a518c07db5fbb85`

## Sự cố

Sau khi deploy `c0fc2f7`, Owner import workbook Legacy (~3 MB). Render Event:

```text
Instance failed
Ran out of memory (used over 512MB) while running your code.
```

Render tự restart, service recovered. Cloudflare 502 là hậu quả của việc
origin bị kill, không phải nguyên nhân độc lập.

Owner KHÔNG chấp nhận nâng lên 2 GB / $25 tháng — Reports phục vụ 2–3 người,
mục tiêu kiến trúc là giữ hệ thống đơn giản và chạy trong 512 MB.

## Root cause (FACT, đo được)

`app/legacy/parser.py::parse_workbook` mở workbook **hai lần cùng lúc**
(`data_only=True` cho giá trị, `data_only=False` cho công thức) ở chế độ
**đầy đủ** (`read_only=False`).

Ở chế độ đầy đủ, `load_workbook` phân tích XML và dựng cây `Cell` cho **MỌI
sheet trong file ngay tại thời điểm mở** — không lazy. Workbook thật của
Owner không chỉ có 3 sheet REQUIRED: nó còn hàng chục sheet sổ bán hàng thô
dạng `01.2026 Ly` (chính các sheet mà công thức Summary trỏ tới — xem
`docs/analysis/02_FORMULA_MAPPING.md` §3: `='01.2026 Ly'!$B$1`). Import
legacy **không đọc một dòng nào** trong các sheet đó, nhưng vẫn trả tiền RAM
cho toàn bộ chúng — và trả **hai lần**, vì hai workbook phải sống đồng thời
để ghép value/formula theo từng dòng.

Yếu tố thứ hai, cùng gốc: `_read_rows` và `_parse_datachart` truy cập ô theo
kiểu **ngẫu nhiên** (`sheet["C7"]`). Chính kiểu truy cập này là lý do phải
dùng chế độ đầy đủ ngay từ đầu.

Những chỗ **KHÔNG** phải root cause (đã loại trừ bằng đo đạc, không phải suy
đoán):

- Tầng database: tổng ghi là 13 + 6 + 12 dòng trên fixture, 71 + 174 + 12
  trên workbook thật — vài trăm dòng. `_insert_facts` đã ghi theo batch một
  lần cho mỗi bảng. Không có gì để tối ưu ở đây.
- Tầng web: `upload.save(temp_path)` ghi thẳng ra đĩa, không giữ file trong
  RAM; `MAX_CONTENT_LENGTH` = 25 MB.
- `app/modules/importing/raw_reader.py` (pipeline chính) **đã** dùng
  `read_only=True` từ trước — chỉ đường legacy bị sót.

## Bằng chứng đo được

Không có workbook production trong session (không được yêu cầu Owner gửi dữ
liệu thật). Thay vào đó dựng workbook **đúng hình dạng production**: fixture
chuẩn của repo (3 sheet REQUIRED, giữ nguyên cached value qua cơ chế inject
của chính fixture) + 60 sheet sổ bán hàng thô → **3.15 MB**, khớp "khoảng
3 MB" Owner mô tả.

Metric: `resource.getrusage(RUSAGE_SELF).ru_maxrss` — peak RSS, đúng thứ
Render đếm khi kill container.

`parse_workbook` đơn lẻ (process trần, baseline 24 MB):

```text
                     peak RSS     thời gian
BEFORE  3.15 MB       379.6 MB      13.94 s
AFTER   3.15 MB        32.0 MB       0.15 s
AFTER   7.79 MB        31.8 MB       0.17 s   ← file gấp 2.5 lần, RAM không đổi
```

End-to-end qua **đúng route `/du-lieu/legacy`** (Flask app đã boot, PostgreSQL
thật, upload multipart), baseline sau boot app = 68.6 MB:

```text
                  import #1     import #2
BEFORE             427.7 MB      474.2 MB
AFTER               81.1 MB       81.9 MB
```

Đây là **một** gunicorn worker. `Dockerfile` chạy `gunicorn --workers 2`, nên
container còn phải cộng worker thứ hai + master. 474 MB ở một worker giải
thích trọn vẹn "used over 512MB".

Điểm quan trọng nhất không phải con số mà là **hình dạng**: sau repair, peak
RAM không còn phụ thuộc vào kích thước sổ bán hàng trong workbook. File 7.79
MB tốn đúng bằng file 3.15 MB, vì các sheet không được đọc thì XML của chúng
không bao giờ được phân tích. Đây là sửa cấu trúc, không phải chỉnh tham số.

## Repair (thay đổi tối thiểu — 1 file)

`app/legacy/parser.py`:

1. `load_workbook(..., read_only=True)` cho cả hai bản. Ở chế độ read-only,
   worksheet là lazy: sheet nào không được duyệt thì không tốn gì.
2. Thêm `_sheet_cells(sheet, columns)` — đọc **tuần tự** (`iter_rows`) và chỉ
   giữ lại đúng các cột cần. Summary: 18 cột × ~15 dòng. DataChart: 36 cột ×
   15 dòng. Cả hai đều bé.
3. `_read_rows` nhận sẵn hai cell map thay vì hai worksheet.
4. `_parse_datachart` đọc từ cell map thay vì `sheet["AG5"]`.
5. `DATACHART_TARGET_YEAR_CELL` / `_PER_DAY_CELL` đổi từ `"J15"` thành
   `("J", 15)` để dùng chung đường đọc. Không module nào ngoài parser tham
   chiếu hai hằng số này (đã grep toàn repo).

**KHÔNG** đụng: `SUMMARY_IMPORT_SHEETS`, `SUMMARY_REFERENCE_ONLY_SHEETS`,
`_classify`, `defects.py`, `models.py`, guard DEC-168, ngưỡng fidelity, hay
bất kỳ giá trị nghiệp vụ nào. Không thêm dependency. Không thêm biến môi
trường. Không worker/queue/Redis/service/database mới.

## Business fidelity: KHÔNG ĐỔI (chứng minh, không khẳng định)

Serialize toàn bộ `LegacyWorkbook` ra JSON (mọi `SummaryRow`, `DailySales`,
`MonthlyReference`, `formula_text`, `known_defects`, `Decimal` giữ nguyên
dạng chuỗi) rồi `diff` output của parser **cũ** và **mới** trên hai workbook:

```text
fixture chuẩn repo : IDENTICAL — 0 khác biệt (767 dòng JSON)
workbook 3.15 MB   : IDENTICAL — 0 khác biệt (767 dòng JSON)
```

Fidelity bằng công cụ canonical trên PostgreSQL thật:

```text
python3 -m tools.analysis.verify_legacy_import <workbook>
SUMMARY_SOURCE_ROWS_WITH_VALUES  = 13
SUMMARY_IMPORTED_ROWS            = 13
SUMMARY_UNACCOUNTED_ROWS         = 0
SUMMARY_REFERENCE_ONLY_PERSISTED = 0
matched=580 mismatched=0
```

`SUMMARY_REFERENCE_ONLY_PERSISTED = 0` xác nhận `Summary 2025` vẫn là
REFERENCE_ONLY (DEC-169) — repair không mở rộng scope import.

## PostgreSQL

`alembic upgrade head` trên PostgreSQL 16.13 thật → `0001_legacy`. Upload qua
route thật → HTTP 302, `count_imports = 1`. Upload **lại cùng file** → 302
với thông điệp "File này đã được nhập trước đó (LEG-…) — không tạo bản mới",
`count_imports` vẫn 1: contract fingerprint giữ nguyên.

Dừng hẳn PostgreSQL (`pg_ctl -m fast stop`) → khởi động lại → đọc bằng
**process Python mới**: `current_import` đúng, `periods` đúng, `87.6` khứ hồi
chính xác từ cột `NUMERIC`.

Trang render từ PostgreSQL: `/nhan-vien?ky=2026-1` → 200 với 66 nhãn
`LEGACY`; `/doanh-so-ngay?ky=2026-1` → 200, 19 nhãn; `/du-lieu` → 200.

## Tests

```text
full suite                     1608 passed, 11 skipped   (y hệt trước repair)
Golden baseline                  58 passed,  2 skipped
PRA-001 focused                 114 passed
  (legacy_importer, legacy_repository, legacy_source_coverage,
   web_legacy_routes, history_db)
R2 / storage / run_registry      55 passed
Tracking                        210 passed
git diff --check                clean
```

## Giới hạn của bằng chứng (không được đọc rộng hơn)

- Workbook dùng để đo là **dựng lại theo hình dạng production**, không phải
  file thật của Owner. Cơ chế gây OOM đã chứng minh chắc chắn (peak RAM tỉ lệ
  với TỔNG số ô của workbook, không phải phần được import); con số peak chính
  xác trên file thật thì chưa đo được. Sau repair điều đó không còn quan
  trọng: peak không còn phụ thuộc phần workbook không được đọc.
- PostgreSQL dùng ở đây là 16.13 local, không phải Render PostgreSQL 18
  production.
- Session không có egress tới Render (403), nên không tự retest production
  được.

## Finding DEFER (không sửa trong session này)

`tools/analysis/verify_legacy_import.py:83` dùng `load_workbook(path,
data_only=True)` không read-only, cùng lỗi một hệ với root cause ở trên.
KHÔNG sửa vì: đây là công cụ CLI chạy trên máy Owner để lấy bằng chứng
fidelity, **không nằm trong container 512 MB** — không cản production
persistence. Ghi lại để một task sau xử lý, không im lặng bỏ qua.

## Chưa được làm (Do Not Change Yet)

- KHÔNG nâng plan Render, KHÔNG thêm worker/queue/Redis/one-off service.
- KHÔNG bắt đầu `TASK-PRA-002`.
- KHÔNG đụng Tracking, R2, hay pipeline chính.
- KHÔNG refactor ngang sang các module dùng openpyxl khác.
