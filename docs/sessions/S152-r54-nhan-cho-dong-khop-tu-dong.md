# S152 — `R5.4`: nhãn cho dòng khớp TỰ ĐỘNG với Tracking

Ngày: 2026-09-10
Nhánh: `claude/reports-category-brand-display-gkpp9b` (dựng từ nhánh mặc định
`claude/extract-upload-repo-gq2ws4` @ `16d1806`, đã đồng bộ đầu phiên).
Task: `R5.4` — `docs/tasks/R5-4-nhan-cho-dong-khop-tu-dong.md`
Task Mode: MAJOR
Project Profile: PRODUCT
Status: DONE (code + test + governance); `CHECK-R54-11` chờ Owner.
Thực hiện bởi: Claude Code, theo chỉ thị trực tiếp của Owner trong phiên.

## 0. Bối cảnh

Owner báo (kèm ảnh chụp tab Nhân viên): sau `R5.3` và sau khi phân loại
hãng/ngành hàng bên Tracking, chạy lại báo cáo vẫn không hiện ngành hàng +
hãng, tên mã hàng không rút gọn; nhiều model đã phân loại nhưng không có
giá nhập từ cột MIN. Yêu cầu: điều tra (không sửa), rồi sau khi có kết
luận: "xử lí luôn, tạo PR và merge bên Reports".

## 1. Điều tra — kết luận

Đo từng tầng trên đường thật (chi tiết: task file §1):

```text
Tracking chieuBoard()              ĐÚNG    src/index.js (chonBrand/chonCategoryLabel/modelCua)
Worker đọc Firebase                service account (fbToken) — rules KHÔNG chi phối
capture_tracking_catalog           ĐÚNG    chở đủ ba trường
catalog_display + bản BỀN R5.3     ĐÚNG    nhãn của MỌI mã board
resolver production                ĐÚNG    inv.map → Resolved, canonical_product_code ghi DB
_catalog_labels / metadata_of /
  bucket_for                       ĐỨT     chỉ tra confirmed_identities()
```

Resolve là phép đọc thuần (`INV-70`): khớp tự động không tạo mapping ⟹ không
khoá trong bảng nhãn ⟹ tên dài + `—`. `CHECK-R53-07` đã chốt hành vi này.

Hai vấn đề KHÁC không thuộc code Reports (ghi ở task file §4, `DEC-221`
§2.4): độ phủ "câu tên hàng → mã" (vận hành Tracking, màn "Phân loại theo
tên hàng"); giá MIN `—` theo ngày 06/09, 09/09 (nghi thiếu bản ngày, chưa
xác minh).

## 2. Tái hiện E1 trước sửa

Bài tạm (không đưa vào repo) trên bộ khung `tests/test_r53_durable_tracking_labels.py`:

```text
RESULT ROWS: ('55Q6FA', '["TRACKING_DAILY_MIN_SOURCE_UNAVAILABLE", ...]', 'PENDING')
line-product: Máy lạnh Test-2
line-brand: —
line-category: —
AssertionError: assert 'Máy lạnh Test-2' == 'QLED 55Q6FA'
```

## 3. Sửa

Xem task file §2 (Scope Lock) và §3 (Thiết kế). Tóm tắt: một helper
`line_identity.tracking_identity_of()` (mapping CONFIRMED thắng, không có
thì mã lần chạy đã lưu), nối vào ba cổng; `business_queries` chở hai cột
đã có sẵn xuống dòng. Fixture chung `tests/test_snapshot_repository.py::
result_line` bỏ mã giả `A1` mặc định (nay mã là bằng chứng được đọc).

## 4. Bằng chứng

```text
tests/test_r54_nhan_cho_dong_khop_tu_dong.py   16 passed
tests/test_r53_durable_tracking_labels.py      19 passed (không đổi)
tests/test_employee_workspace_ux.py            87 passed
Full pytest (trừ 2 suite trình duyệt)          3640 passed / 23 skipped / 0 failed (nền S151: 3628 / 24 / 0; +16 bài mới, không bài nào bị xoá)
Validators governance                          structure/project_state/evidence/task_completion PASS; reference_integrity 4 finding — đúng 4 baseline cũ
git diff --check                               sạch
```

Ghi chú môi trường: lượt full đầu tiên đỏ ở
`test_105d_boundaries.py::test_protected_golden_artifacts_match_the_task_105e_review_base`
vì clone nông thiếu object `740f396` (lỗi môi trường đã biết từ `S151`);
`git fetch --unshallow` rồi chạy lại.

## 5. File đã thay đổi

Xem "Đăng Ký File Đã Thay Đổi" trong task file.

## 6. Quyết định chính

`DEC-221` (Owner): mở root task mới `R5.4`; merge thẳng theo chỉ thị Owner,
không qua Independent Review; `CHECK-R53-07` ghi chú superseded.

## 7. Rủi ro / vướng mắc

- `CHECK-R54-11` (nghiệm thu production) chỉ Owner đóng được sau deploy.
- Phiên KHÔNG có credential Render: không xác nhận được deploy Live.
- Giá MIN `—` theo ngày chưa được xác minh (cần `pending_reasons` production).

## 8. Session tiếp theo được khuyến nghị

Owner mở tab Nhân viên sau deploy: dòng có giá MIN phải hiện model gọn +
Hãng + Nhóm hàng. Nếu vẫn `—` ở dòng CÓ giá: đó là lỗi mới, không phải
`R5.4`. Nếu `—` ở dòng KHÔNG có giá: dòng chưa khớp (xem task file §4).
