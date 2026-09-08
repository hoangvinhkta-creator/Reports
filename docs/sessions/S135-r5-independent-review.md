# S135 — R5: Independent Review (phiên review ĐỘC LẬP)

Phiên này chỉ ĐỌC, CHẠY và KIỂM. Không sửa một dòng mã sản phẩm nào, không
merge, không deploy, không đánh dấu Owner Acceptance của R3, R4 hay R5.

Bản ghi review đầy đủ: `docs/reviews/R5-INDEPENDENT-REVIEW-RECORD.md`.
Task canonical: `docs/tasks/R5-doi-soat-so-bieu-do-thao-tac-danh-tinh.md`.
Bàn giao triển khai đang được review: `docs/sessions/S134-r5-doi-soat-va-danh-tinh.md`.
Repair brief phiên này tạo: `docs/tasks/R5-REPAIR-1-doi-soat-nhan-vien-va-khoi-phuc.md`.

**Kết luận phiên: `REPAIR_REQUIRED`.**

---

## 1. Tóm tắt cho người đọc vội

Năm gói của R5 làm đúng những gì bàn giao mô tả, và bốn trong năm chuỗi kiểm
đi qua route thật đều sạch. Hai chỗ phải sửa trước khi tích hợp:

1. **Bấm `XONG` gán lại cả đơn cho người đứng đầu danh sách.** R5 §4 gộp mọi
   thứ về một nút gửi, nhưng ô chọn nhân viên vẫn không có mục "giữ nguyên".
   BH chưa có nhân viên, hoặc có nhiều người, sẽ bị gán cho người đầu danh
   sách ở MỌI lần lưu — kể cả khi người dùng chỉ sửa một ô giá. Đây là dời
   doanh thu và KPI của một BH sang một người khác.

2. **Dòng quay lại không được khôi phục nếu hai lần nạp cùng một giây.** Mốc
   snapshot chỉ có độ phân giải GIÂY, còn phép so "dòng đã quay lại chưa" là
   phép so NGẶT. Trước R5 hệ quả là một cảnh báo thừa; sau R5 cùng cái nhãn
   ấy quyết định tổng tiền, nên hệ quả đảo chiều thành **trừ tiền vĩnh viễn**
   — trong khi màn hình vẫn hứa "nạp lại một sổ có chứa dòng đó thì các con
   số tự khôi phục".

Cả hai tái hiện được bằng lệnh. Không cái nào là lỗi cẩu thả: cái thứ hai là
một lập luận đúng ở PRA-002 mà R5 đã làm hết đúng nhưng không ai tính lại.

---

## 2. Exact HEAD đã review

```text
Reports   949e32df7a876d1f6f8003eb5df39e3d11dcc069
          nhánh claude/r5-reports-tracking-deploy-o77n7t · worktree CLEAN
Tracking  f958226f6127e6055eb411e4c22e12c58d09654b
          worktree review RIÊNG (cây có sẵn của container là main @ edeb827)
Nền       b6756fef4b43362201a88f8fe13c45488916d3dd
Mặc định  claude/extract-upload-repo-gq2ws4
```

Bốn khẳng định của brief §1 đều xác minh bằng git — chi tiết ở review record §2.

---

## 3. Finding

```text
REPAIR_REQUIRED  FIND-R5-IR-01  XONG gán lại cả BH cho nhân viên đầu danh sách
REPAIR_REQUIRED  FIND-R5-IR-02  dòng quay lại không khôi phục khi cùng một giây

ACCEPTED_RISK    AR-R5-IR-06  cửa sổ 30 ngày không trùng tháng 31/28/29 ngày
ACCEPTED_RISK    AR-R5-IR-07  modelCua cắt chuỗi thô theo độ dài cat thô
ACCEPTED_RISK    AR-R5-IR-08  modelCua không kiểm biên PHẢI của mã
ACCEPTED_RISK    AR-R5-IR-09  /run nuốt mọi ngoại lệ thành HTTP 400, không log
ACCEPTED_RISK    AR-R5-IR-10  chú thích đã hết đúng ở _with_absence_state
ACCEPTED_RISK    AR-R5-IR-11  docstring hứa một khẳng định không có trong thân bài
ACCEPTED_RISK    AR-R5-IR-12  tools/smoke/r1_daily_min_smoke.py sập giữa chừng

AR-R5-01 … AR-R5-05  tái kiểm chứng — cả năm GIỮ NGUYÊN mức ACCEPTED_RISK
```

`AR-R5-IR-09` và `AR-R5-IR-12` là **lỗi baseline cũ**, đo được là hỏng y hệt
trên `b6756fe`. Cả hai nằm ngoài Scope Lock của R5 và không làm sai một con
số nào.

---

## 4. Trạng thái check

```text
CHECK-R5-01 … CHECK-R5-26   PASS   (giữ nguyên — phiên này chạy lại và khớp)
CHECK-R5-27  Independent Review    FAIL
             Review ĐÃ CHẠY ĐỦ. Kết luận REPAIR_REQUIRED, nên implementation
             CHƯA được chấp nhận. Check chuyển sang PASS ở lần review thứ hai
             sau khi R5-REPAIR-1 xong.
CHECK-R5-28  Owner nghiệm thu      NOT_TESTED — không phiên nào tự đóng
CHECK-R3-20 · CHECK-R4-24          NOT_TESTED — phiên này KHÔNG chạm tới
```

---

## 5. Điều kiện tích hợp — vẫn còn nguyên

`S133` yêu cầu Owner xác nhận production R3/R4 TRƯỚC khi R5 được tích hợp.
Phiên này **không tìm thấy bằng chứng Owner đã nghiệm thu**, nên điều kiện ấy
giữ nguyên là điều kiện TRƯỚC merge, chồng lên `REPAIR_REQUIRED` ở trên.

`INTEGRATION_DECISION_REQUIRED [ loc>5000 ]` tái lập được
(`cumulative LOC = 5336`, `RESULT = AUTHORITY_OK`). Phiên này phân loại nó là
**quyết định governance**, không phải dấu hiệu code cần chia nhỏ: phần
code+test là `4220` dòng — dưới ngưỡng — và không tìm được một lỗi luồng
chính nào do khối lượng gây ra.

**Khuyến nghị cho Owner: tích hợp NGUYÊN KHỐI (phương án 1), sau repair.**
Năm gói không độc lập như phương án 2 giả định — gói 3 và gói 4 đều đọc
`PeriodData` mà gói 1 định nghĩa lại — nên tách ra sẽ tạo một tổ hợp chưa ai
chạy và tốn thêm một vòng review. Lý do đầy đủ ở review record §6.

---

## 6. Thứ tự việc tiếp theo

```text
1. R5-REPAIR-1            hai finding, MỘT phiên, không mở rộng
                          → tiêu repair cycle 1/2 của lineage R5
2. Independent Review 2   trên HEAD sau repair
3. Owner nghiệm thu R3/R4 trên production   → CHECK-R3-20, CHECK-R4-24
4. Merge R5 nguyên khối vào claude/extract-upload-repo-gq2ws4
5. Deploy
6. Owner nghiệm thu R5 trên production      → CHECK-R5-28
```

Bước 3 KHÔNG được đổi chỗ cho bước 4: đó là chính điều kiện `S133`.

---

## 7. Checklist Owner — khi tới bước 3 và bước 6

**Trước merge (bước 3) — nghiệm thu R3/R4 trên production:**

1. Mở một kỳ đã chốt, đối chiếu vân tay và thông điệp drift.
2. Xuất Excel một kỳ và đối chiếu tay ba dòng bất kỳ với sổ kế toán.
3. Đối chiếu KPI, đóng góp và drill-down của R4 trên một tháng thật.

**Sau deploy (bước 6) — tám luồng của R5.** Giữ nguyên tám luồng ở `S134` §9,
với hai điều chỉnh mà phiên review này thêm vào:

4. Ở luồng 5 (sửa một BH nhiều dòng): làm THÊM một lượt **không chạm ô nhân
   viên** — chỉ sửa một ô giá rồi bấm `XONG` — trên một BH chưa có nhân viên
   và trên một BH nhiều người. Nhân viên phải **không đổi**.
5. Ở luồng 2 (nạp lại sổ có đơn bị thiếu): bấm nạp lại **ngay lập tức**, đừng
   chờ. Tổng phải quay về đầy đủ.

**Phần visual cần Owner nghiệm thu bằng mắt** (phiên này chỉ kiểm được
DOM/CSS/JS, không kiểm được hình học thật):

6. Popover phân loại ở một dòng giữa trang, trên màn hình thật: nó xuất hiện
   TẠI CHỖ bấm, không tràn viewport, trang không nhảy lên đầu.
7. Hai cột Hãng/IMEI khi mở: hẹp, cắt ĐÚNG MỘT DÒNG, hàng không cao lên, và
   rê chuột đọc được nội dung đầy đủ.

---

## 8. Việc phiên này KHÔNG làm

- KHÔNG sửa một dòng mã sản phẩm nào (Reports lẫn Tracking).
- KHÔNG merge, KHÔNG deploy, KHÔNG mở PR.
- KHÔNG đóng `CHECK-R3-20`, `CHECK-R4-24`, `CHECK-R5-28`.
- KHÔNG triển khai `category_label`, KHÔNG mở sang R5.1.
- KHÔNG tiêu một repair cycle nào của lineage R5.
