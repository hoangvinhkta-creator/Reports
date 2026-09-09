# R5-REPAIR-1 — Gán nhân viên ngoài ý muốn, và dòng quay lại không được khôi phục

## Metadata

Status:
READY

Current Status Reason:
Independent Review của R5 (`docs/reviews/R5-INDEPENDENT-REVIEW-RECORD.md`,
`CHECK-R5-27` = FAIL) kết luận `REPAIR_REQUIRED` với ĐÚNG HAI finding. Task
này gom cả hai vào MỘT phiên repair. Không finding nào khác được kéo vào, và
R5.1 / `category_label` KHÔNG thuộc phạm vi.

Phase:
PHASE-01 — Engine tính toán

Task Mode:
MAJOR

Primary Agent Tier:
C

Escalation Tier:
C

Difficulty:
2/5

Risk:
4/5

Blast Radius:
4/5 (V4.1 §4 — chấm theo failure path, KHÔNG theo kích thước bản vá. Cả hai
finding nằm trên đúng failure path chính của R5: `cờ vắng mặt → effective data
→ MỌI chỉ tiêu kinh doanh → vân tay chốt kỳ → export`, cộng thêm đường gán
nhân viên vốn quyết định KPI thuộc về ai. Bản vá nhỏ không làm bán kính nhỏ
đi.)

Effective Risk:
HIGH (Blast Radius quyết định — V4.1 §4.1)

Project Profile:
PRODUCT

Review Budget lineage:
`R5` — `2 allowed / 0 used / 2 remaining` TRƯỚC phiên này. Phiên repair này
tiêu **repair cycle thứ 1**, còn lại 1. Xem
`PROJECT/REVIEW_BUDGET_LEDGER.md` → "Root Task: R5".

ADR:
`docs/adr/ADR-111-absence-effective-data-imei-scope-and-brand-authority.md` —
KHÔNG đổi. Cả hai bản sửa nằm trong đúng ranh giới thẩm quyền mà ADR-111 đã
vẽ; chúng làm cho hành vi khớp với ADR, không đổi ADR.

Owner Authority:
`docs/reviews/R5-INDEPENDENT-REVIEW-RECORD.md` §3 (`FIND-R5-IR-01`,
`FIND-R5-IR-02`).

Base:
`claude/r5-reports-tracking-deploy-o77n7t` @
`949e32df7a876d1f6f8003eb5df39e3d11dcc069`. Tracking KHÔNG cần sửa —
`f958226` giữ nguyên.

---

## 1. Scope Lock

**ĐƯỢC LÀM — và chỉ ba file mã.**

1. `app/web/templates/kinh_doanh_nhan_vien.html` — thêm MỘT `<option
   value="">` đứng đầu ô chọn nhân viên của form cấp BH, và chỉ khi
   `group.employee_value` rỗng.
2. `app/web/history_writer.py` — `timespec="seconds"` → `"microseconds"` cho
   mốc snapshot.
3. `app/web/history_store.py` — `seen[0] > anchor` → `seen[0] >= anchor`
   trong `_with_absence_state`, và viết lại chú thích đã hết đúng ở ngay
   trên nó.

Cộng các test tương ứng ở §4.

**KHÔNG ĐƯỢC LÀM.**

- KHÔNG đổi `business_presentation.assignable_employee_options()` — nó còn
  phục vụ các bề mặt khác của `OD-5`, và thêm mục trống ở đó là đổi hành vi
  của những màn hình không có finding nào.
- KHÔNG migration, KHÔNG backfill `source_snapshot.created_at` cũ.
- KHÔNG đụng `plan_order_edit`/`apply_order_edit` ngoài phần test.
- KHÔNG đụng Tracking.
- KHÔNG sửa `AR-R5-IR-06` … `AR-R5-IR-12` (chúng là `ACCEPTED_RISK`, không
  phải repair). Ngoại lệ DUY NHẤT: `AR-R5-IR-10` (chú thích) đi kèm mục 3 vì
  nó chính là lập luận đã tạo ra lỗi.
- KHÔNG `category_label`, KHÔNG R5.1.

---

## 2. `FIND-R5-IR-01` — bấm `XONG` gán lại cả đơn

**Hiện trạng.** Ô chọn nhân viên của form cấp BH không có mục trống. Khi BH
có 0 hoặc ≥2 nhân viên hiệu lực, `group.employee_value` là `""`, không option
nào mang `selected`, và trình duyệt gửi option ĐẦU TIÊN ở mọi lần bấm `XONG`
— kể cả khi người dùng chỉ sửa một ô giá.

**Sửa.** Trong `kinh_doanh_nhan_vien.html`, ngay trước vòng `{% for option in
assignable %}` của `<select name="nhan_vien_moi">`:

```jinja
{% if not group.employee_value %}
<option value="" selected>— Giữ nguyên —</option>
{% endif %}
```

`app/web/server.py::business_save_order` đã sẵn sàng: `chosen or None` biến
chuỗi rỗng thành *"không đổi nhân viên"*, và `plan_order_edit` bỏ qua nhánh
nhân viên khi `employee is None`.

**Vì sao mục trống ở ĐÂY không mâu thuẫn với docstring của
`assignable_employee_options()`.** Câu ấy nói về một ô mà nút gửi của nó
CHÍNH LÀ hành động gán. Sau R5 §4, ô này đi cùng một nút gửi làm nhiều việc,
nên "không nói gì về nhân viên" trở thành một câu trả lời hợp lệ và phải nói
ra được. Ghi lý do ấy vào chú thích ngay chỗ sửa.

---

## 3. `FIND-R5-IR-02` — dòng quay lại không được khôi phục

**Hiện trạng.** `history_writer.py` ghi `created_at` với `timespec="seconds"`;
`_with_absence_state` so `seen[0] > anchor` NGẶT. Hai snapshot trong cùng một
giây ⟹ `reappeared = False` ⟹ cờ còn hiệu lực ⟹ R5 trừ dòng khỏi mọi con số,
vĩnh viễn và không có đường khôi phục thủ công.

**Sửa — làm CẢ HAI.**

1. `app/web/history_writer.py:136` — `timespec="microseconds"`. Chuỗi ISO
   vẫn xếp đúng thứ tự với bản ghi cũ (`…T00:00:00` < `…T00:00:00.000001`),
   nên không cần migration và không cần backfill.
2. `app/web/history_store.py:1408` — `seen[0] >= anchor`. An toàn theo cấu
   tạo: snapshot dựng cờ theo định nghĩa KHÔNG chứa khoá ấy, nên nó không bao
   giờ có mặt trong `_latest_membership` của chính khoá đó. Trường hợp biên
   còn lại đổi lỗi từ *"âm thầm trừ tiền"* sang *"vẫn tính, kèm cảnh báo"* —
   đúng chiều an toàn.
3. Viết lại chú thích ở `history_store.py:1400-1407`. Câu *"Không con số
   nghiệp vụ nào phụ thuộc vào nhãn này (hiện trạng và tổng tiền không bao
   giờ do cờ quyết định)"* đã hết đúng từ R5 §1: `removed_candidate_keys()`
   đọc đúng `is_active` này để quyết định tổng tiền. Chú thích mới phải nói
   ra chiều an toàn ĐÃ ĐẢO và vì sao phép so nay là `>=`.

---

## 4. Test bắt buộc thêm

1. `tests/test_r5_order_edit_form.py` — hai bài mới: một BH hai nhân viên
   khác nhau, một BH không có nhân viên nào. Mỗi bài ĐỌC `<select>` từ chính
   HTML, suy ra giá trị trình duyệt sẽ gửi khi không ai chạm, POST đúng giá
   trị đó, rồi khẳng định tập nhân viên của BH **không đổi**. Thêm một bài
   dương: chọn một tên thật ⟹ cả đơn đổi.
2. `tests/test_r5_removed_lines.py` — tham số hoá
   `test_a_line_that_comes_back_is_restored_to_the_totals_by_itself` theo ba
   mốc: cách NGÀY, cách MỘT GIÂY, và CÙNG MỘT GIÂY. Cả ba phải cho
   `12.000.000` và `removed_in_source == []`.
3. Một bài canh chính đường ghi mốc: `history_writer` sinh `created_at` có
   phần thập phân của giây (độ phân giải nhỏ hơn giây).

Bộ khung tái hiện của phiên review nằm nguyên văn trong
`docs/reviews/R5-INDEPENDENT-REVIEW-RECORD.md` §3 — dùng lại được.

---

## 5. Completion Gate

| ID | Nội dung | Status | Evidence |
|---|---|---|---|
| `CHECK-R5R1-01` | Bấm `XONG` không chạm ô nhân viên trên BH nhiều nhân viên ⟹ nhân viên KHÔNG đổi | NOT_TESTED | E1 |
| `CHECK-R5R1-02` | Bấm `XONG` không chạm ô nhân viên trên BH chưa có nhân viên ⟹ vẫn chưa có | NOT_TESTED | E1 |
| `CHECK-R5R1-03` | Chọn một tên thật rồi `XONG` ⟹ cả đơn đổi, câu tóm tắt nói đúng | NOT_TESTED | E1 |
| `CHECK-R5R1-04` | Dòng quay lại được khôi phục ở CẢ BA mốc (ngày · giây · cùng giây) | NOT_TESTED | E1 |
| `CHECK-R5R1-05` | Mốc snapshot của đường production có độ phân giải nhỏ hơn giây | NOT_TESTED | E1 |
| `CHECK-R5R1-06` | Smoke qua HTTP server thật: nạp lại sổ NGAY LẬP TỨC (không chờ) vẫn khôi phục tổng | NOT_TESTED | E1 |
| `CHECK-R5R1-07` | Full regression Reports không có FAIL mới so với `949e32d` | NOT_TESTED | E1 |
| `CHECK-R5R1-08` | `CHECK-R5-01` … `CHECK-R5-26` vẫn PASS | NOT_TESTED | E1 |
| `CHECK-R5R1-09` | Independent Review lần 2 | NOT_TESTED | — |
| `CHECK-R5-28` | Owner nghiệm thu trên production | NOT_TESTED | — |

`CHECK-R5R1-09` và `CHECK-R5-28` KHÔNG được tự đánh dấu bởi phiên repair.

---

## 6. Exit Criteria

1. Hai finding hết tái hiện được bằng đúng lệnh đã ghi ở review record §3.
2. Không FAIL mới trong full regression, và không con số nào của
   `CHECK-R5-01` … `CHECK-R5-26` đổi.
3. Smoke xuyên repo chạy được mà KHÔNG cần chèn quãng chờ nhân tạo.
4. Không file nào ngoài Scope Lock §1 bị chạm.
5. Independent Review lần 2 kết luận ACCEPT hoặc
   ACCEPT_WITH_RECORDED_RISK. — `CHECK-R5R1-09`.
6. Owner nghiệm thu trên production. — `CHECK-R5-28`.
