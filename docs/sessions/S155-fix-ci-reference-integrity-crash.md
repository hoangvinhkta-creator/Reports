# S155 — Sửa lỗi CI: `validate_reference_integrity.py` sập với `PermissionError`

Ngày: 2026-09-11
Nhánh: `claude/reports-category-brand-display-gkpp9b` (dựng từ nhánh mặc
định `claude/extract-upload-repo-gq2ws4` @ `da6186c`, đã đồng bộ đầu phiên).
Task Mode: MICRO (sửa một script governance, không chạm code sản phẩm).
Project Profile: PRODUCT
Status: DONE

## 1. Yêu cầu

Owner: "sửa lỗi CI giúp tôi", kèm ảnh chụp một banner đỏ trên trang tải sổ
của Reports (không liên quan — xem phần trả lời riêng ở hội thoại).

## 2. Lỗi

Check CI duy nhất của repo (`governance` workflow) đã đỏ trên MỌI lần chạy
kể từ tích hợp R4 — kể cả trên chính nhánh mặc định — vì
`validate_reference_integrity.py` sập với `PermissionError` thay vì báo
một finding, khi gặp ba file trích dẫn nguyên văn đường dẫn tuyệt đối
/root/.ccr/README.md (không đặt trong backtick ở đây, để không tự tạo
thêm reference cho chính đoạn văn xuôi này) làm bằng chứng lịch sử. Chi
tiết đầy đủ, bằng chứng
tái hiện, và bản sửa: `PROJECT/PROJECT_DECISIONS.md` → `DEC-225`.

## 3. File đã thay đổi

Modified:
- `governance/scripts/governance/validate_reference_integrity.py` —
  `_exists_safe()` bọc `.exists()`; ba cặp /root/.ccr/README.md (không
  backtick — lý do như trên) vào `KNOWN_EXEMPT_PAIRS`.
- `governance/scripts/governance/README.md` — tài liệu fixture mới.
- `PROJECT/PROJECT_DECISIONS.md` — `DEC-225`.

Created:
- `governance/scripts/governance/fixtures/regression_permission_denied_reference.py`
- `docs/sessions/S155-fix-ci-reference-integrity-crash.md` (file này)

## 4. Bằng chứng

```text
Bốn validator còn lại              PASS (không đổi)
validate_reference_integrity.py    PASS/FAIL đúng 4 finding baseline —
                                    KHÔNG còn phụ thuộc UID đang chạy
                                    (đo bằng cả root lẫn user `daemon`
                                    trong chính phiên này, xem DEC-225 §2)
Fixture regression MỚI             fail-trước (3/4 đỏ, PermissionError) /
                                    pass-sau (4/4), ở cả hai điều kiện UID
Full pytest                        3659 passed, 23 skipped, 4 deselected
                                    in 263.38s (0:04:23)
git diff --check                   sạch
```

## 5. Quyết định chính

`DEC-225` — bọc `OSError` trong `resolves()`; miễn trừ ba trích dẫn lịch
sử /root/.ccr/README.md (không backtick — lý do như trên) vào
`KNOWN_EXEMPT_PAIRS` để kết luận không phụ thuộc UID chạy validator.

## 6. Rủi ro / vướng mắc

Không có trên phạm vi sửa lỗi sập. Nhưng lưu ý quan trọng phát hiện khi xác
nhận trên CI thật (PR #20): workflow `.github/workflows/governance.yml`
chạy `set -euo pipefail` qua cả 5 validator liên tiếp — bất kỳ validator
nào exit khác 0 (kể cả một `FAIL` sạch, không sập) đều làm cả job
`governance / validate` báo `failure`. `validate_reference_integrity.py`
đã, và VẪN SẼ, báo đúng 4 finding baseline đã biết (TASK-REM-T06 × 3, S136
× 1 — xem DEC-189/DEC-193, `PROJECT/PROJECT_PROGRESS.md` dòng ~665) — một
tình trạng đã được ghi nhận và CHẤP NHẬN xuyên suốt nhiều phiên/PR trước
đây (ví dụ closeout DEC-189/DEC-193 đều xác nhận "đúng 3 reference hỏng có
sẵn của TASK-REM-T06, không tăng thêm" thay vì yêu cầu về 0). Baseline này
không phải lỗi của lượt sửa này, và việc giải quyết nó thật sự (tạo
README.md/LICENSE ở gốc repo theo TASK-REM-T06) cần quyết định của chủ
dự án về nội dung license — ngoài phạm vi MICRO của lượt sửa sập này.
(README.md/LICENSE cố ý không đặt trong backtick ở đây — cùng lý do tránh
tự tạo thêm reference nêu ở §2.)

## 7. Xác nhận trên CI thật (PR #20)

Push commit `d690ac2` lên PR #20 → job `validate` chạy xong SẠCH (không
traceback, không `PermissionError`), in đúng:

```text
REFERENCE INTEGRITY: FAIL
4 reference không phân giải được: ... (đúng 4 baseline TASK-REM-T06/S136)
##[error]Process completed with exit code 1.
```

Đây LÀ điều kiện hoàn thành thật của lượt sửa này: KHÔNG CÒN SẬP, danh
sách finding giống hệt baseline cục bộ đã biết trước khi sửa — không phải
"check chuyển XANH", vì bản thân workflow không tha một `FAIL` sạch nào,
kể cả FAIL đã biết trước và được chấp nhận theo tiền lệ dự án. Check
`governance / validate` trên PR này (và trên default branch sau khi merge)
sẽ tiếp tục hiện đỏ cho tới khi TASK-REM-T06 được hoàn thành riêng — đây
là tình trạng đã biết, không phải regression của lượt sửa này.
