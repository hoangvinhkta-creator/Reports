# S068 — COHORT THẬT ĐẦU TIÊN SAU AUTHORITY: HOÀN TẤT

Ngày: 2026-09-01 ICT
Task: capture → cohort thật → đo lường → sửa cổng định tuyến tối thiểu

## Kết Quả

Owner đã xác nhận `2026-09-01` chỉ là cutover kỹ thuật, không phải ranh giới
chính sách giá. Reports nay có thể hỏi Public Purchase cho đơn trước ngày này
nhưng chỉ khi identity là exact/đã xác nhận và evidence authoritative thực sự
phủ toàn bộ ngày bán. Không có backfill giá hiện tại, không suy đoán identity
và không nới temporal validation.

Capture immutable `PPH-20260901T021755Z-s068.json` được strict loader chấp
nhận. Owner workflow chọn chính capture này và catalog COMPLETE mới nhất, rồi
chạy workbook thật ngày 2026-08-31 thành công.

## Cutover Baseline Check Trước Sửa

| Phân loại evidence | Dòng |
|---|---:|
| `PP_HISTORY_COVERS_SALE_DATE` | 1 |
| `CUTOVER_BASELINE_COVERS_SALE_DATE` | 11 |
| `NO_AUTHORITATIVE_PRODUCT_IDENTITY` | 70 |
| `NO_PP_AUTHORITY_FOR_SALE_DATE` | 1 |
| `OTHER` | 0 |

Baseline tồn tại, mang timestamp authority `SERVER`, tại
`2026-08-29T12:35:37.774000+00:00`; history authoritative có điểm cho 39 mã.
Dòng còn thiếu authority nhận `NO_BASELINE_PRICE_AT_CUTOVER`, không nhận giá
thay thế. Kết quả này được đo trước khi sửa routing và không dùng current PP.

## Sửa Tối Thiểu

`HistoricalConfirmedRegistry` vẫn được chạy trước và entry `CONFIRMED` không
bị composition ghi đè. Với miss lịch sử, production composition nay gọi exact
identity resolver và Tracking History Reader bất kể ngày bán trước hay sau
01/09/2026. Reader vẫn quyết định bằng baseline, temporal coverage và chuỗi
history; bất kỳ thiếu hụt nào là `Pending` có provenance. Catalog không
`COMPLETE` được xem là identity source unavailable, không làm report crash và
không tự tạo identity/giá.

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
REPORT_OUTPUT=outputs/reports/report-20260901T024747Z.xlsx
```

Không xoay credential, không log secret, không sửa Tracking/Firebase hay luật
nghiệp vụ ngoài Owner decision về quyền consult evidence.

## Cohort Thật Sau Sửa

```text
TOTAL_ORDERS=58
TOTAL_LINES=83
BEFORE_AUTO_LINES=0
AFTER_AUTO_LINES=10
AFTER_REVIEW_QUEUE_LINES=73
AUTO_ORDERS=5
AUTO_LINES=10
REVIEW_QUEUE_ORDERS=53
REVIEW_QUEUE_LINES=73
ERROR_ORDERS=2
DROPPED_ORDERS=0
DROPPED_LINES=0
ACCOUNTING_COVERAGE_PERCENT=100.0%
SILENT_ERROR_CANDIDATES=0
MANUAL_WORK_PERCENT=91.38%
MANUAL_WORK_REDUCTION_PERCENT=8.62%
```

Có 12/83 dòng resolve `AccountingPurchasePrice`; 10 dòng trong số đó thành
AUTO hoàn toàn. 71 dòng Pending đều có record giá và Review Queue tương ứng
(`UNQUEUED_PRICE_PENDING_LINES=0`). Hai `ERROR` là finding đã hiển thị trong
queue, không phải silent error.

Top Review Queue theo dòng / đơn: `Missing.PurchasePrice` 71 / 52,
`Suspicious` 6 / 3 và `Suspicious.ERP` 1 / 1. Top blocker là
`NO_AUTHORITATIVE_PRODUCT_IDENTITY` (70 dòng), không phải temporal gate.
Theo 90/10, cohort chưa đạt ngưỡng AUTO 90%; không có sửa thêm để nâng AUTO
vì mọi dòng chưa đủ evidence đang Pending trung thực.

## Regression

- Focused: `tests/test_105e_price_composition.py`,
  `tests/test_tracking_history_pipeline.py`, `tests/test_pipeline.py` —
  `79 passed`.
- Golden/batch affected by source-unavailable handling — `22 passed`.
- Full regression: `1307 passed, 11 skipped`; ba fail còn lại là environment
  only: tripwire yêu cầu Python 3.11 nhưng runtime bundled là Python 3.12, và
  hai test socket loopback bị sandbox chặn. Bốn boundary cases pass trên 3.12;
  hai test socket đều pass khi chạy với quyền loopback.

## Trạng Thái Và Bước Tiếp Theo

```text
PRE_2026_09_01_GATE_REMOVED=YES
CURRENT_PP_BACKFILL_ALLOWED=NO
TEMPORAL_AUTHORITY_PRESERVED=YES
CANONICAL_INTEGRATED=NO
REMOTE_PUSHED=NO
```

`TEST_PP_AUTH_001` không cần có trong catalog hiện tại và không được tạo lại.
Bước vertical tiếp theo là xác nhận identity authoritative cho 70 dòng Pending
qua luồng mapping/confirmation hiện có; không dùng fixture hoặc giá hiện tại
để thay thế cohort thật.

## Git Safety

Không commit workbook, capture runtime, output report, secret hay dữ liệu
private. Chỉ code, test và tài liệu sanitized của S068 được stage tường minh.
