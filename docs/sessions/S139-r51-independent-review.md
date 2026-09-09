# S139 — Independent Review `R5.1` (nhóm hàng `category_label`)

Ngày: 2026-09-09
Task Mode: `MAJOR` (phiên review, không phải phiên triển khai)
Kết luận: **`ACCEPT_WITH_RECORDED_RISK`**

Phiên chỉ ĐỌC, CHẠY, TẠO PROBE và KIỂM. **Không sửa một dòng mã sản phẩm
nào, không merge, không deploy, không triển khai `R6`, không tự đánh dấu
Owner Acceptance.**

Bản ghi đầy đủ (bằng chứng nguyên văn từng chuỗi):
`docs/reviews/R5-1-INDEPENDENT-REVIEW-RECORD.md`.

---

## 1. Đối tượng review

```text
Reports   claude/r5-1-category-label-1nnct7 @ 2c2c139d9d7ec34d8007a463a82a694956496940
Tracking  claude/r5-1-category-label-1nnct7 @ 39528ee5260f4cd5a6bdf92c7f020ad5ecbda362

Nền       Reports  claude/extract-upload-repo-gq2ws4 @ 3b35b7acee2159b007c4398045f4b6f6843f7de8
          Tracking main                              @ 918183c48c4d4c45b5ce1348d734e073e537c6e4
```

`0b8ac31` (code-only) KHÔNG review riêng — review chạy trên `2c2c139`, HEAD
có đủ tài liệu handoff/task, đúng chỉ thị.

Preflight: `R5` đã merge ở cả hai nền; base Reports là ancestor của `R5.1`;
không commit lạ ngoài `R5.1`; worktree CLEAN; `branch_authority_check.sh` =
`AUTHORITY_OK` (`DETACHED_EXACT_TARGET`).

---

## 2. Kết luận và finding

```text
REPAIR_REQUIRED   0
ACCEPTED_RISK mới 2   AR-R5.1-05, AR-R5.1-06
Đính chính        1   COR-R5.1-01
AR-R5.1-01 … -04      tái kiểm chứng, cả bốn GIỮ NGUYÊN

CHECK-R51-25  NOT_TESTED → PASS (E1)
CHECK-R51-26  VẪN NOT_TESTED
Repair cycle tiêu  0  (lineage R5 vẫn 2 allowed / 1 used / 1 remaining)
```

`AR-R5.1-05` — `cat` bẩn nhưng ĐÚNG HÌNH DẠNG (toàn chữ cái, ≤4 từ, ≤40 ký
tự) đi ra nguyên văn: `"Tivi kho anh Ba"`, `"Tủ lạnh nợ NCC"`, `"Tivi Đất
Việt"`. Đường vào có thật (`setCat()` ghi thẳng chuỗi `prompt()` vào
`board/<mã>/cat`). Hậu quả dừng ở một ô nhãn trên cột mặc định ẨN; không đổi
tiền, mapping hay vân tay chốt kỳ; giá/tồn/NCC/note/link vẫn không đi ra.
Không có phép sửa nào nằm trong kiến trúc `DEC-204` đã duyệt.

`AR-R5.1-06` — hãng ngoài danh sách đóng `HANG` ở lại trong nhãn
(`"Tivi Vsmart"`). Sửa đúng chỗ: thêm một dòng vào `HANG`.

`COR-R5.1-01` — `DEC-204` §3 ("Không lọt ⟹ null, KHÔNG đi ra nguyên văn")
phát biểu mạnh hơn hành vi thật. KHÔNG sửa `DEC-204` (artifact lịch sử);
trạng thái đúng giữ ở bản ghi review và mục 6 của task.

---

## 3. Kiểm đã chạy (không tin số trong bàn giao `S138`)

```text
Tracking  npm test        62 bộ · 2825 đạt · 0 hỏng · 2 bỏ qua
          npm run build   OK (dist, 658 KB → 411 KB)
          probe nhomCua/chieuBoard độc lập   33 đạt / 0 hỏng

Reports   pytest tests/test_r51_category_label.py   24 passed
          pytest -q (toàn bộ)                       3256 passed, 12 skipped
          R1/R2/R3 bất biến                         333 passed
          R5 identity/workspace/IMEI/capture        225 passed
          probe hash/backcompat độc lập             11 đạt / 0 hỏng
          probe DOM/CSS độc lập                     17 đạt / 0 hỏng

Smoke xuyên hai repo (producer THẬT + route Flask THẬT)   45 PASS / 0 FAIL

Governance  structure PASS · project_state PASS · evidence PASS
            task_completion PASS · branch_authority AUTHORITY_OK
            reference_integrity 4 reference — BASELINE (tái hiện y hệt trên
            nền 3b35b7a); R5.1 không thêm reference hỏng nào
```

Bàn giao `S138` ghi `3257 passed / 11 skipped`; phiên này đo `3256 / 12` —
cùng tổng `3268`, chênh đúng một bài skip vì máy review không cài extra
`storage` (`No module named 'botocore'`). Khác biệt MÔI TRƯỜNG, không phải
hồi quy. Mọi số còn lại tái hiện đúng.

---

## 4. Bàn giao cho bước MERGE + DEPLOY `R5.1`

Bước kế tiếp **chưa xảy ra**. Phiên sau cần làm, theo đúng thứ tự:

1. **Mở phiên đúng quy trình**: `CLAUDE.md` → S000; xác định nhánh mặc định
   THẬT trên origin của cả hai repo (`git remote show origin`); fetch; chạy
   `scripts/branch_authority_check.sh` cho tới `AUTHORITY_OK`.
2. **Quyết định của Owner trước khi merge.** `CHECK-R51-26` (nghiệm thu
   production) còn `NOT_TESTED`, và `R5` cho thấy Reports merge xong là
   Render tự deploy production. Owner cần nói rõ chấp nhận merge trước
   nghiệm thu, hay nghiệm thu trên staging trước. **Không phiên nào tự
   quyết thay.**
3. **Thứ tự merge — Tracking TRƯỚC, Reports SAU.** `category_label` là
   trường TÙY CHỌN: Reports đọc artifact chưa có trường này ra `None` mà
   không lỗi (đã chứng minh), nhưng Reports merge trước sẽ có một khoảng
   thời gian cột Nhóm hàng trống toàn bộ. Merge Tracking `39528ee` vào
   `main` trước, rồi Reports `2c2c139` vào `claude/extract-upload-repo-gq2ws4`.
4. **Sau merge Tracking**: chạy lại `npm run build` trên `main` và xác nhận
   `/api/xuat/board` production trả năm khoá.
5. **Sau merge Reports**: cần MỘT lần capture danh mục mới thì cột Nhóm hàng
   mới có dữ liệu — bản chiếu `data/product_identity/tracking_display.json`
   sống trên đĩa ephemeral (`AR-R5.1-04`). Trước lần capture đó, cột hiện
   "—", và đó là trạng thái ĐÚNG, không phải lỗi.
6. **Nghiệm thu `CHECK-R51-26`** (Owner, bằng mắt, trên production):
   - bật nút "HIỆN NHÓM HÀNG, HÃNG & IMEI" — cả ba cột cùng hiện/ẩn;
   - dòng đã phân loại hiện đúng nhóm hàng; dòng chưa phân loại hiện "—";
   - cột hẹp, một dòng, ellipsis, tooltip đọc đủ (phần hình học thật);
   - **đối chiếu `AR-R5.1-05`**: soát cột Nhóm hàng tìm nhãn mang tên NCC,
     tên người hay ghi chú (ví dụ "Tivi kho anh Ba"). Có thì sửa tên ngành
     hàng bên Tracking — không sửa ở Reports.
7. **KHÔNG gộp `R6` vào phiên merge.** `R5.1` chưa có KPI, dashboard,
   Basket, bảng tổng hợp nhóm hay giao diện sửa category, và không phiên
   merge nào được thêm.

Nếu Owner muốn siết `AR-R5.1-05` thay vì chấp nhận: đó là mở lại `DEC-204`
§3 (danh sách trắng HÌNH DẠNG vs GIÁ TRỊ) bằng một quyết định mới, **không
phải** một repair cycle của lineage `R5`.
