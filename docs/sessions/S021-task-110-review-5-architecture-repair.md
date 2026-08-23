# S021 — TASK-110, Architecture Repair sau Independent Review #5

## Metadata

Task:
TASK-110 — Validation + Review Queue

Current Task Mode:
MAJOR

Selected Profile:
PRODUCT

Ngày:
2026-08-23

Commit vào phiên:
`8386d345b04b754c061ce03b79116e75f0dfae4e`

Trạng thái ra khỏi phiên:
**IMPLEMENTED. NOT MERGED. NOT DONE.** CHECK-110-16 tiếp tục **BLOCKED**.
Chờ **Independent Review #6**.

## Vì Sao Phiên Này Khác Bốn Phiên Trước

S017–S020 đều là các vòng patch: reviewer chỉ ra một representation mang
provenance sai, phiên sửa đúng representation đó. Bốn lần liên tiếp, và lần
nào vòng sau cũng tìm ra cái kế tiếp — `source_row` → `source_rows` →
`raw_variants` → `ambiguous_rows` → `details`.

Chủ dự án yêu cầu dừng patch và làm **Architecture Audit** trước khi viết một
dòng code. Audit cho ra một kết luận và một phát hiện thêm:

**Root cause chung.** Validation TÁI TẠO LẠI các sự thật mà production đã
biết, thay vì NHẬN LẠI chúng. `EmployeeMapper.resolve()` chọn đúng một record
rồi **vứt bỏ** nó — chỉ ghi lại `normalized`/`status`/`group`. Sau điểm đó,
danh tính record không tồn tại ở đâu nữa, nên mọi consumer buộc phải đoán lại
bằng giá trị. Đoán lại bằng giá trị có đúng hai chế độ hỏng, và **cả hai đã
xảy ra**: drift (Finding 4) và collision (Finding 3). Song song, `details` là
kênh khóa tùy ý chạy bên cạnh `affected_rows` (Finding 1), và test
falsification không hề chạm tới nó (Finding 2).

**Phát hiện thêm — DRIFT C, reviewer chưa nêu.** `collect_mapping_stats` khớp
prefix trên chuỗi **đã normalize** trong khi production khớp trên chuỗi **thô**.
Đo được: `'Đức  Kiên 0867'` (khoảng trắng đôi) → production `unmapped`, F3 lại
kết luận ambiguous. Đây là bản cài đặt thứ **ba** của cùng một quy tắc, và nó
đã drift sẵn — xác nhận rằng bốn finding không phải bốn bug rời rạc.

## Bằng Chứng Audit (đo tại `8386d34`, trước khi sửa)

```
=== DRIFT A: empty raw_prefix ===
production mapper : MappingResult(normalized='Rỗng', status='mapped', ...)
validation select : None

=== DRIFT B: raw_prefix key vắng hoàn toàn ===
production mapper : RAISES KeyError 'raw_prefix'
validation select : None

=== COLLISION: hai record, cùng _record_key, khác active/group ===
key(A) == key(B) : True ('Vinh', 'Mr Vinh', '2026-01-01', '9999-12-31')
production picks  : active=True group=NOI_THANH

=== FINDING 1: details escape hatch ===
affected_rows      : [6]
item.affected_count: 1
item.source_row    : 6
item.details       : {'criterion': 'F4', 'ambiguous_rows': 'dòng 7 ...', ...}

=== DRIFT C ===
'Đức  Kiên 0867'  | production: False | F3 collector: True
```

## Human Decision

Ba quyết định, chốt trước khi code, ghi thành **DEC-132**:

- **HD-110-06** — `raw_prefix` thiếu / rỗng / chỉ khoảng trắng là **INVALID
  CONFIG**, fail-fast khi load. Ngữ nghĩa `raw_prefix: "" = catch-all` bị bác
  bỏ. Kèm schema tối thiểu cho `normalized`, `group`, `active`. Đặt ở
  `mapping/`, **không** ở `app/modules/config/loader.py` generic.
- **HD-110-07** — mở rộng `EmployeeMapper` (`RecordRef`, `resolve_record`,
  `candidate_records`, `record`, `records`); `WorkingData` mang chính instance
  mapper production. **Không** thêm field vào `WorkingLine`/`Order`.
- **HD-110-08** — F3 dùng đúng matching semantics của production.

Audit **không** tìm thấy xung đột canonical nào với HD-110-03/04/05 hay
DEC-129/130/131 — cả bốn giữ nguyên toàn bộ.

## Đã Làm

1. **Xóa nguồn sự thật thứ hai.** `select_effective_record` và `_record_key`
   bị xóa hẳn (không deprecate, không wrapper), cùng vòng khớp prefix riêng
   trong `collect_mapping_stats`. `_record_label` bị giáng cấp thành hàm render
   cho người đọc, không còn là khóa.
2. **`RecordRef`.** Danh tính của bản ghi **đã load** (vị trí trong list), chứ
   không phải của một bộ giá trị — nên collision là bất khả, không phải "khó
   xảy ra". `candidate_records` lọc theo **định danh đối tượng** (`id()`), vì
   dùng `in` trên dict sẽ gộp lại đúng hai record mà Finding 3 nói tới.
3. **`resolve()` viết trên `resolve_record()`.** Chỉ còn một phép chọn record
   trong toàn hệ thống.
4. **`RowProvenance`.** `affected_count`, `source_row`, `source_rows`,
   `raw_variants`, `ambiguous_rows`, `conflicting_records` đều là property dẫn
   xuất từ đúng một tuple. `MappingFinding` mất hẳn trường `details`;
   `ReviewItem` mất hẳn field `affected_count` và `source_row`; các khóa mang
   thông tin dòng bị từ chối nếu caller cố ghi vào `diagnostics`.
5. **Lan sang cả 7 detector còn lại.** `rules.py` trước đây tự tính
   `affected_count=` và tự nối `source_rows` ở chỗ khác — hôm nay chúng khớp
   nhau **do tình cờ**, không do cấu trúc. Cả 6 construction site chuyển sang
   `RowProvenance`, nên lớp lỗi này đóng ở toàn bộ Review Queue chứ không chỉ ở
   F1–F6.
6. **Fail-fast cho master data hỏng** tại biên `mapping/`.

## Bằng Chứng Ra Khỏi Phiên

- `python3 -m pytest tests/ -q` → **330 passed**, 0 regression.
- **CHECK-110-19 (L1)** — 972 tổ hợp raw × as_of, **0 khác biệt** so với ảnh
  chụp lấy trước dòng sửa đầu tiên.
- **CHECK-110-20 (L2)** — đầu ra nghiệp vụ đầu-cuối, **0 khác biệt**.
- **CHECK-110-21 (L3)** — ba file đóng băng của TASK-108A-1 `sha256sum -c` → OK.
- **CHECK-110-22 (F1–F6)**, **CHECK-110-23 (F7–F9)** — 26 test, tất cả PASS.
- 22 module nghiệp vụ được bảo vệ (conversion, pricing, profit, orders,
  lead_source, adjustment, product, importing, `app/modules/domain/models.py`):
  `sha256sum -c` → không file nào đổi.

## Rủi Ro Còn Lại

- **CHECK-110-16 vẫn BLOCKED.** Chưa có file thô production; không suy diễn PASS.
- **L2 chạy trên workbook synthetic**, không phải dữ liệu thật — nó chứng minh
  không có dịch chuyển nghiệp vụ trên hình dạng dữ liệu đã biết, không chứng
  minh cho hình dạng chưa từng thấy.
- **`reconcile_conversion.py` giờ validate master data khi khởi động**, vì nó
  gọi `EmployeeMapper.from_yaml`. Với `config/employees.yaml` hiện tại không có
  tác dụng gì (đã assert), nhưng nếu master data hỏng thì script sẽ dừng sớm
  thay vì chạy tiếp — đó đúng là ý định của HD-110-06.
- **Script vẫn giữ bản cài đặt khớp prefix riêng** để dựng `ambiguities`. Đây là
  ngoại lệ **có chủ đích** với luật một-nguồn-sự-thật: output của nó là bằng
  chứng đã ký ở CHECK-108A1-15, và đóng băng bằng chứng thắng việc thống nhất.
- **`validate_reference_integrity.py` báo 3 reference hỏng** trong
  `docs/tasks/TASK-REM-T06-repository-root-hygiene.md`. **Có sẵn từ trước**
  phiên này (đã xác nhận bằng `git stash`), không liên quan tới TASK-110.

## Bàn Giao

Chờ **Independent Review #6**. Không merge, không tự chuyển DONE.
