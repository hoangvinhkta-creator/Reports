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

Không có. Đây là sửa hẹp trên một script governance, không chạm code sản
phẩm, không đổi hành vi báo cáo cho bất kỳ finding thật nào.

## 7. Session tiếp theo được khuyến nghị

Xác nhận check `governance / validate` XANH trên PR kế tiếp — đây là điều
kiện hoàn thành thật của việc sửa này, không chỉ chạy cục bộ.
