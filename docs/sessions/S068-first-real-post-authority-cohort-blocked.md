# S068 — COHORT THẬT ĐẦU TIÊN SAU AUTHORITY: OWNER_DECISION_REQUIRED

Ngày: 2026-09-01 ICT
Task Mode: MICRO
Task: first real post-authority cohort — capture → run → measure
Base SHA: `dc6a02cebb5fd9c6c8c80fc40803402d350c67e0`

## Kết Quả

Safety result của cohort là `PASS_WITH_TRUTHFUL_PENDING`; verdict sau trace
root cause là `OWNER_DECISION_REQUIRED`. Đã tạo capture production immutable
mới, kiểm tra PASS qua strict loader và chạy cohort thật ngày 2026-08-31 qua
Owner production path. Không sửa production code, không đoán giá và không
dùng fixture thay thế.

## Evidence Xác Minh

| Check | Status | Evidence | Kết quả |
|---|---|---|---|
| Branch authority | PASS | `TARGET_SHA=dc6a02cebb5fd9c6c8c80fc40803402d350c67e0 ./scripts/branch_authority_check.sh` sau fetch remote | `DETACHED_EXACT_TARGET`; default remote và HEAD cùng SHA. |
| Runtime worktree | PASS | `git status --short --branch` | Chỉ có `artifacts/`, `data/captures/`, `data/tracking_catalog/`, `data/tracking_price_history/` untracked; không có tracked modification. |
| Capture credential | PASS | Kiểm tra hiện diện biến trong execution environment, không in giá trị | `TRACKING_REPORT_API_KEY=FOUND`. |
| Tracking endpoint | PASS | Một request read-only theo contract với header client canonical | `HTTP 200`. |
| Capture mới | PASS | `capture_purchase_price_history.py` canonical | `PPH-20260901T021755Z-s068.json`, `COMPLETE`. |
| Strict loader và temporal coverage | PASS | `load_tracking_price_history_capture()` + `require_complete()` + `SaleInterval.for_sale_date(2026-08-31, UTC+07:00)` | Capture sau `2026-09-01T00:00:00+07:00` và không còn `SNAPSHOT_DOES_NOT_COVER_SALE_INTERVAL`. |
| Workbook cohort thật | PASS | Workbook Owner cung cấp trực tiếp, đọc bằng raw reader production | 58 OrderID / 83 dòng; toàn bộ có `sale_date=2026-08-31`. |
| Owner capture discovery | PASS | `select_latest_valid_captures()` trước khi chạy report | Chọn `PPH-20260901T021755Z-s068.json` theo metadata `captured_at`. |
| Owner production report | PASS | `run_owner_report()` | Report tồn tại; Summary đối chiếu 58/58 đơn và dùng capture S068. |
| Focused pytest | NOT_TESTED | `python3 -m pytest tests/test_tracking_contract_client.py tests/test_owner_usability.py -q` | Python có sẵn không cài `pytest`; không cài dependency mới chỉ để kiểm tra. |

## Capture Và Cohort

`CAPTURE_CREATED=YES`.

```text
CAPTURE_FILE=data/captures/PPH-20260901T021755Z-s068.json
CAPTURE_ID=PPH-20260901T021755Z-9040fbdf
CAPTURED_AT=2026-09-01T02:17:55.754948+00:00
CAPTURE_STATUS=COMPLETE
CAPTURE_VALIDATION=PASS
SALE_DATE_2026_08_31_COVERED=YES
```

Không sửa capture cũ, không chạm Firebase hay Tracking ngoài các GET
read-only.

## Cohort Thật

```text
COHORT_SOURCE=So_chi_tiet_ban_hang (6).xlsx, sale_date=2026-08-31
REPORT_OUTPUT=outputs/reports/report-20260901T022706Z.xlsx

TOTAL_ORDERS=58
TOTAL_LINES=83
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
MANUAL_WORK_REDUCTION_PERCENT=NOT_YET_MEASURABLE
```

`MANUAL_WORK_PERCENT` là tỷ lệ đơn vào Review Queue (`58/58`); không có
baseline thời gian xử lý tay canonical để tính reduction. Machine check phủ
83 dòng, không tìm thấy Pending không có Review Queue hay đơn/dòng bị mất.
Không có manual verdict nên `SILENT_ERROR_RATE=NOT_YET_MEASURED`; con số
candidate bằng 0 không được diễn giải thành xác nhận thủ công.

Review Queue reason theo số đơn / dòng:

1. `Missing.PurchasePrice` = 58 / 83.
2. `Suspicious` = 1 / 1.

Các trường `Pending.accounting_purchase_price`,
`Pending.accounting_profit` và `Pending.eligible_kpi_profit` đều là hệ quả
cùng của `Missing.PurchasePrice` trên 58 đơn / 83 dòng, không phải ba blocker
độc lập.

`TEST_PP_AUTH_001_REQUIRED=NO`; sự vắng mặt của nó không được kiểm tra và
không ảnh hưởng kết luận này.

## 90/10 Decision

Top blocker là `Missing.PurchasePrice`: ảnh hưởng 58 đơn / 83 dòng. Nó giảm
AUTO nhưng không chặn vertical outcome hiện tại, vì tất cả Pending đều
truthful, accounted và có Review Queue; thêm giá hay đổi cutover để tăng AUTO
là suy đoán/đổi authority ngoài phạm vi S068.

`REPAIR_PERFORMED=NO`; `BUSINESS_RULE_CHANGED=NO`;
`PUBLIC_PURCHASE_SEMANTICS_CHANGED=NO`; `TRACKING_CHANGED=NO`;
`FIREBASE_MUTATED=NO`.

## Root-Cause Trace — tiếp tục S068

Trace dùng năm dòng sản phẩm thật, chọn từ các product identity có một exact
hit trong captured Tracking catalog. Không ghi tên hàng, mã hàng, giá, khách
hàng hoặc raw workbook vào repository.

| Mẫu | Tracking present | Public Purchase history | Resolve ngày 2026-08-31 | Reports result | Primary root cause |
|---|---|---|---|---|---|
| 1–5 | YES | YES | RESOLVED | `PENDING / Pending` | `H: PRE_CUTOVER_AUTHORITY_ROUTING_GATE` |

Tất cả 83 dòng cohort có `sale_date < 2026-09-01`. `app.pipeline` đưa toàn
bộ vào P00 (`_apply_pre_cutover_identity`) và chỉ gọi
`HistoricalConfirmedRegistry`; `remaining_lines` dành cho
`PostCutoverPriceComposition` chỉ chứa dòng `sale_date >= 2026-09-01`.
Catalog, resolver và Public Purchase History vì vậy không được gọi trên bất
kỳ dòng nào trong cohort — đúng một gate có chủ đích, không phải lỗi ingest.

Phép đo hẹp trên toàn cohort: 13/83 dòng có một exact unique catalog match;
12/83 trong số đó có Public Purchase History resolve được cho 2026-08-31;
1/83 còn Pending khi hỏi reader. 70/83 chưa có exact unique catalog match.
Các con số sau chỉ mô tả mức evidence nếu Owner đổi authority; chúng không
được dùng để auto-map hay backfill dưới rule hiện tại.

Kết luận: gate P00 là systemic root cause của 83/83 `Missing.PurchasePrice`.
Evidence Public Purchase đã tồn tại nhưng bị Reports bỏ qua do routing rule
đối với ít nhất 12 dòng; mức evidence của 71 dòng còn lại không đủ để kết
luận từ trace hẹp.

## Owner Decision Required

Owner cần chốt: **Reports có được dùng Public Purchase History đã capture,
có temporal coverage và resolve tại đúng ngày bán, cho các đơn trước
2026-09-01 hay không?**

Chọn “có” thay đổi authority/cutover semantics của P00 (`DEC-154`/`INV-47`),
nên không phải repair local. Chọn “không” giữ trạng thái Pending hiện tại và
chỉ `HistoricalConfirmedRegistry`/authority lịch sử được Owner cấp mới có thể
resolve các dòng này.

## Việc Tiếp Theo

Chờ Owner trả lời quyết định authority ở trên. Sau đó mới được xác định phạm
vi implementation hợp lệ và chạy lại đúng cohort 58 đơn / 83 dòng. Không mở
repair chỉ để thay đổi AUTO.

## Git Safety

Không commit runtime artifact, raw private data hay secret. Chỉ tài liệu
sanitized của S068 có thể được stage/commit theo đường delivery hiện hành.
