# S068 — COHORT THẬT ĐẦU TIÊN SAU AUTHORITY: HOÀN TẤT

Ngày: 2026-09-01 ICT
Task: capture → cohort thật → đo lường → consume Tracking identity authority

## Kết Quả Cuối

Owner xác nhận `2026-09-01` chỉ là cutover kỹ thuật, không phải ranh giới
chính sách giá. Reports có thể consult Public Purchase cho đơn trước ngày đó
khi identity và evidence effective-dated thực sự đủ. Không current-PP
backfill, không suy đoán identity, không nới temporal validation.

Sau đó Owner xác nhận Tracking là authority identity: production chỉ dùng
normalization đã duyệt, `alias.map[normalized_code]` (nếu có), rồi exact key
`board[canonical]`. `name`, `alt`, similarity, substring và Reports mapping
store không được dùng để tạo identity production. Capture/catalog hiện hữu đã
chứa cả hai endpoint authority nên không cần acquisition song song hay sửa
Tracking.

## Capture Và Owner Workflow

```text
CREDENTIAL_AVAILABLE=YES
TRACKING_ENDPOINT_HTTP_STATUS=200
CAPTURE_CREATED=YES
CAPTURE_FILE=data/captures/PPH-20260901T021755Z-s068.json
CAPTURE_ID=PPH-20260901T021755Z-9040fbdf
CAPTURED_AT=2026-09-01T02:17:55.754948+00:00
CAPTURE_STATUS=COMPLETE
CAPTURE_VALIDATION=PASS
SALE_DATE_2026_08_31_COVERED=YES
OWNER_HISTORY_CAPTURE=data/captures/PPH-20260901T021755Z-s068.json
OWNER_CATALOG_CAPTURE=data/tracking_catalog/capture_contract_v1_prod_2.json
ALIAS_ENDPOINT_CONSUMED=YES
BOARD_ENDPOINT_CONSUMED=YES
```

Không xoay credential, không log secret, không sửa Tracking/Firebase.

## Cutover Baseline Check

Đo trước repair routing (không dùng current PP):

| Phân loại evidence | Dòng |
|---|---:|
| `PP_HISTORY_COVERS_SALE_DATE` | 1 |
| `CUTOVER_BASELINE_COVERS_SALE_DATE` | 11 |
| `NO_AUTHORITATIVE_PRODUCT_IDENTITY` | 70 |
| `NO_PP_AUTHORITY_FOR_SALE_DATE` | 1 |
| `OTHER` | 0 |

Baseline accepted có timestamp authority `SERVER`; temporal validation giữ
nguyên. Repair S068 trước đó đã bỏ cổng artificial pre-2026-09-01 nhưng không
cho phép extrapolate hoặc backfill giá.

## Tracking Identity Authority Consumer

Resolver production thực hiện chính xác:

```text
normalized accounting code → alias.map (nếu có) → board[canonical] required
```

Nếu target không có trong `board`, kết quả là Pending; không fallback qua
display field hay candidate ranking. Compatibility fixture cũ phải nêu rõ
legacy mode; Owner workflow/load production vẫn strict Tracking authority.

Đo chỉ đọc trên đúng 50 accounting product trước đây unresolved:

```text
UNIQUE_PREVIOUSLY_UNRESOLVED=50
KNOWN_TO_TRACKING_AS_CONFIRMED_ALIAS=0
KNOWN_CANONICAL_EXACT=0
GENUINELY_UNCLASSIFIED=50
UNKNOWN_DUE_TO_DATA_ACQUISITION=0
LINES_RESOLVED_BY_ALIAS=0
LINES_RESOLVED_BY_CANONICAL_EXACT=0
LINES_STILL_IDENTITY_PENDING=70
```

Trên toàn cohort, 60 unique accounting product / 83 lines đều không có exact
canonical hay confirmed alias. Vì vậy 10 AUTO lines của phép đo trước contract
mới đã không còn hợp lệ: chúng phụ thuộc display-name/`alt` matching và phải
trở thành Pending an toàn.

## Cohort Thật Rerun

```text
REPORT_OUTPUT=outputs/reports/report-20260901T032732Z.xlsx
TOTAL_ORDERS=58
TOTAL_LINES=83
BEFORE_AUTO_LINES=10
AFTER_AUTO_LINES=0
BEFORE_REVIEW_QUEUE_LINES=73
AFTER_REVIEW_QUEUE_LINES=83
AUTO_ORDERS=0
AUTO_LINES=0
REVIEW_QUEUE_ORDERS=58
REVIEW_QUEUE_LINES=83
ERROR_ORDERS=0
DROPPED_ORDERS=0
DROPPED_LINES=0
ACCOUNTING_COVERAGE_PERCENT=100.0%
SILENT_ERROR_CANDIDATES=0
MANUAL_WORK_PERCENT=100.0%
MANUAL_WORK_REDUCTION_PERCENT=0.0%
```

Top queue reason: `IDENTITY_UNRESOLVED` + `Missing.PurchasePrice` covers all
83 lines / 58 orders. One line also has `Suspicious`; two queue entries carry
`EmployeeMapping`. Các reason này đều hiện trong Review Queue, nên không là
silent error. Top blocker là thiếu exact Tracking canonical/confirmed alias
cho cohort thật, không phải acquisition, PP temporal gate hay local loader.

## Regression Và Trạng Thái

- Focused Tracking-authority/capture/identity tests: `104 passed`.
- Affected golden/batch/legacy compatibility tests: `183 passed`; legacy
  fixture explicitly opts out of the strict production contract.
- Full regression: `1313 passed, 11 skipped`; three environment-only
  exceptions are the Python-3.11 interpreter tripwire and two loopback socket
  tests in sandbox. All four boundary cases pass on bundled Python 3.12; both
  socket tests pass with loopback permission.

```text
TRACKING_CHANGE_REQUIRED=NO
REPORTS_IDENTITY_CONSUMER_IMPLEMENTED=YES
FUZZY_MATCHING_USED=NO
SUBSTRING_MATCHING_USED=NO
CURRENT_PP_BACKFILL_ALLOWED=NO
TEMPORAL_AUTHORITY_PRESERVED=YES
CANONICAL_INTEGRATED=NO
REMOTE_PUSHED=NO
```

## Bước Tiếp Theo

Owner/Tracking cần persist confirmed alias hoặc canonical exact cho các
accounting product thật còn thiếu, rồi rerun đúng cohort. Không tạo
Reports-only mapping, không dùng fixture hay giá hiện tại để nâng AUTO.

## Git Safety

Không commit workbook, capture runtime, output report, secret hay dữ liệu
private. Chỉ code, test và tài liệu sanitized của S068 được stage tường minh.
