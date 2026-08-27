# TASK-110 — REPAIR MODE / BẾ TẮC KIẾN TRÚC SAU INDEPENDENT REVIEW #8

> **ARTIFACT LỊCH SỬ — SUPERSEDED (2026-08-27, integration V4.1-1).**
> File này là bản handoff đóng băng tại Independent Review #8 và là bản ghi
> tham chiếu duy nhất của Review #8 trong repo. **Giữ nguyên, không sửa nội
> dung.** Nó KHÔNG phải trạng thái hiện tại.
>
> Trạng thái hiện tại: `R1-A1 = FROZEN` (**DEC-139**, reviewed `a853971` →
> freeze `01a03b0`); `R1-A` = NOT FROZEN; `R1` = NOT FROZEN; `TASK-110` =
> **MERGED (V4.1-1) · NOT DONE**; `CHECK-110-16` = REQUIRED · BLOCKED ·
> `POST_MERGE_PRODUCTION_ACCEPTANCE` (**DEC-141**); `R1-A2` → `R8` =
> `OWNER_EXTENSION REQUIRED` (`repair_cycles_remaining = 0`).
> Canonical: `docs/tasks/TASK-110_REPAIR_PROGRESS.md`.

## 1. Trạng thái đóng băng (tại Independent Review #8 — lịch sử)

- Task: TASK-110 — Validation + Review Queue
- Review gần nhất: Independent Review #8
- Exact SHA đã review: `c8c18229e3ef5a9d600b8d99a1cc21bcbbb2d8dd`
- Verdict: **FAIL**
- Trạng thái: **NOT MERGED · NOT DONE**
- `CHECK-110-16`: **BLOCKED** vì chưa có production workbook.
- Không được coi các tuyên bố `ARCHITECTURE CLOSED`, `RC-1→RC-5 CLOSED` trước đây là bằng chứng hoàn tất. Review #8 đã falsify được các invariant này.

## 2. Vì sao TASK-110 đang bế tắc

TASK-110 đã trải qua nhiều vòng repair/review. Mẫu thất bại lặp lại không còn là thiếu một vài test case riêng lẻ. Vấn đề chính là kiến trúc cho phép tồn tại nhiều trạng thái không hợp lệ, sau đó mỗi vòng repair chỉ đóng một đường biểu diễn cụ thể nhưng vẫn còn đường khác.

Hệ quả:
1. Test suite có thể xanh nhưng invariant kiến trúc vẫn bị bypass.
2. Sửa nhiều lớp cùng lúc làm phạm vi thay đổi quá rộng, khó xác định regression đến từ đâu.
3. Mỗi vòng review lại phát hiện một escape hatch khác của cùng lớp lỗi.
4. Việc tiếp tục "sửa toàn bộ TASK-110 trong một lượt" có nguy cơ không hội tụ.

Từ thời điểm này, TASK-110 chuyển sang **REPAIR MODE CÔ LẬP**.

## 3. Findings còn mở từ Independent Review #8

### R1 — Canonical Object Safety — HIGH
Sealed construction chưa thực sự đóng. `dataclasses.replace()` có thể sao chép seal hợp lệ sang object mới nhưng thay dữ liệu thành invalid; subclass cũng có thể bỏ qua `__post_init__`.

Mục tiêu: canonical object invalid phải **không thể biểu diễn qua public/reasonable API**.

### R2 — MappingStats Single Source of Truth — HIGH
`MappingStats` đồng thời giữ Counter/dict mutable và row collections. Hai phía có thể bị sửa độc lập, tạo kết luận tự mâu thuẫn.

Mục tiêu: count/group/ambiguity phải được derive từ canonical row collections; không tồn tại hai nguồn sự thật mutable.

### R3 — WorkingData Ownership — HIGH
`WorkingData` hiện chỉ khai mapper/master ownership chứ chưa chứng minh lines thực sự được enrich bởi mapper/master đó. Lists cũng còn mutable.

Mục tiêu: lines/master A không thể được Validator/master B chấp nhận im lặng.

### R4 — Diagnostics ↔ Provenance — HIGH
Typed `Diagnostics` vẫn có thể chứa identity/employee/order không tương ứng với canonical provenance.

Mục tiêu: user-visible identity phải derive từ hoặc được validate bằng canonical provenance; không có nguồn sự thật song song.

### R5 — ReviewQueue Integrity — HIGH
`ReviewQueue.items` là list mutable; `add()/extend()` chưa đảm bảo runtime type/invariant.

Mục tiêu: queue canonical không thể chứa non-ReviewItem hoặc bị mutate thành invalid state qua public API.

### R6 — Master Identity / snapshot_id — MEDIUM
Cùng logical employee master nhưng chỉ đảo thứ tự YAML có thể sinh `snapshot_id` khác.

Mục tiêu: same logical master → same identity; khác logical master → khác identity; đồng thời không phá semantics cần thiết của RecordRef.

### R7 — Oracle L2 Coverage — MEDIUM
L2 dựa vào `dataclasses.fields()` nên bỏ sót derived business properties như `Order.total_sales`, `Order.line_count`.

Mục tiêu: oracle bắt được mutation của mọi business output quan trọng, gồm cả derived properties.

### R8 — Governance Canonical State — MEDIUM
`PROJECT/PROJECT_PROGRESS.md` có các current-state section mâu thuẫn nhau.

Mục tiêu: chỉ một canonical current truth; các phần lịch sử phải được đánh dấu rõ là lịch sử, không masquerade thành current state.

## 4. Chiến lược repair mới

Không repair R1→R8 cùng lúc.

Thứ tự bắt buộc:

`R1 → Review → Freeze → R2 → Review → Freeze → R3 → ... → R8`

Mỗi repair unit:
1. Đọc thực tế code tại exact HEAD.
2. Tái hiện finding bằng falsification **trước khi sửa**.
3. Xác định invariant tối thiểu cần đóng.
4. Freeze touch-area trước khi code.
5. Chỉ sửa đúng repair unit hiện tại.
6. Chạy focused tests + regression tests liên quan.
7. Tự falsify lại bằng ít nhất một đường không trùng test implementation.
8. Cập nhật `TASK-110_REPAIR_PROGRESS.md`.
9. Commit riêng.
10. STOP để Independent Review.
11. Chỉ khi PASS mới đánh dấu FROZEN và chuyển unit kế tiếp.

Nếu trong khi sửa một unit phát hiện cần thay đổi một unit đã freeze hoặc một module ngoài touch-area: **STOP — không tự mở rộng scope**.

## 5. Quy tắc chống "test xanh giả"

Không được coi số lượng test PASS là bằng chứng chính.

Bằng chứng ưu tiên:
1. Invalid state không thể dựng qua public/reasonable API.
2. Một nguồn sự thật duy nhất cho mỗi invariant.
3. Falsification trước sửa FAIL, sau sửa không còn dựng được lỗi.
4. Mutation oracle chứng minh chính oracle có khả năng FAIL.
5. Business non-regression trên baseline đã đóng băng.
6. Independent reviewer không dựa vào test do implementer viết để kết luận PASS.

## 6. Những thứ không được làm trong Repair Mode

- Không merge TASK-110.
- Không chuyển TASK-110 DONE.
- Không suy diễn `CHECK-110-16` PASS.
- Không sửa TASK-108B/TASK-109.
- Không đổi conversion/pricing/profit/KPI ownership nếu repair unit không yêu cầu.
- Không "tiện tay" dọn architecture khác.
- Không sửa nhiều repair unit trong cùng commit.
- Không đổi invariant đã freeze để làm test dễ PASS.
- Không tin báo cáo/session cũ hơn code thực tế tại HEAD.

## 7. Completion condition mới

TASK-110 chỉ quay lại Final Independent Review khi:
- R1…R8 đều `FROZEN — Independent Review PASS`.
- Regression suite xanh.
- Business non-regression evidence còn nguyên.
- Governance current state nhất quán.
- `CHECK-110-16` vẫn được ghi đúng BLOCKED nếu chưa có production workbook.

Sau đó mới chạy một **Final Integration Review** toàn TASK-110.

Nếu Final Integration Review PASS nhưng CHECK-110-16 vẫn BLOCKED thì TASK-110 vẫn chưa DONE theo gate hiện tại.
