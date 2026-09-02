# RÀ SOÁT ĐỘC LẬP — BẢN GHI DURABLE (TASK-PRA-001)

Review ID:
`TASK-PRA-001-IR-RECORD`

Task / Release:
`TASK-PRA-001` — Legacy Reference Vertical (PHASE-PRA, Slice 1)

Reviewer Session:
Ba vòng review độc lập tách biệt (xem bảng "Ba vòng review" bên dưới).
Bản ghi này KHÔNG phải một vòng review thứ tư và KHÔNG tạo verdict mới.

Executed By:
Claude (S077 — close-out session) — *ghi chép* bản ghi durable

Timestamp:
2026-09-02

## Vì sao có file này

Finding `N11` của Final Independent Delta Review: `Independent Review #1`
chưa có review record durable dưới `docs/reviews/`, trong khi tiền lệ của
repo (`TASK-105B`, `TASK-105D`, `TASK-GOLDEN-BASELINE-001`) đều lưu record
tại đây. Thiếu record khiến ba vòng review của `TASK-PRA-001` chỉ tồn tại
rải rác trong session log và ledger, và không phân biệt được vòng nào cho
verdict nào.

**Ranh giới nguồn (đọc trước khi trích dẫn file này).** Đây là bản ghi
**tổng hợp có nguồn**, KHÔNG phải biên bản gốc của reviewer. Mọi dòng dưới
đây truy nguyên được về artifact đã tồn tại trước S077:

- `docs/sessions/S076-pra-001-repair-cycle-1.md` — nội dung hai blocking
  finding của Review #1, cách tái tạo và cách sửa.
- `PROJECT/REVIEW_BUDGET_LEDGER.md` → `## Root Task: TASK-PRA-001` — hạch
  toán repair cycle 1/1 và SHA được review.
- `PROJECT/PROJECT_DECISIONS.md` → `DEC-168`, `DEC-169`.
- `docs/tasks/TASK-PRA-001-legacy-reference-vertical.md` — Completion Gate.
- Owner-supplied verdict của Final Independent Delta Review (S077 prompt).

Không có bằng chứng nào ở đây được chế tạo. Chỗ nào review artifact gốc
không tồn tại trong repo, file này nói thẳng là không tồn tại thay vì dựng
lại nội dung.

## Ba vòng review

| Vòng | SHA được review | Verdict | Nguồn |
|---|---|---|---|
| Independent Review #1 | `7d84072765288b7a9dc28679a09325fce7860b48` | `CHANGES_REQUIRED` — 2 blocking finding | S076, ledger |
| Repair Re-review (repair cycle 1/1) | `5bea87a152b303138dff89ac8e3aef78bec5a630` | `PASS` — cả hai finding đóng | S076, ledger, gate PRA-001 |
| Final Independent Delta Review | `3faedfdebc1f14d8a27e89955d9cfa64d6a462cd` | `PASS` — `DEC169_REVIEW = FAITHFUL`, 0 blocking | Owner verdict (S077) |

Ba vòng này KHÔNG được gộp: verdict `PASS` cuối cùng thuộc về delta của
`DEC-169`, không xoá việc Review #1 từng `CHANGES_REQUIRED`.

## Tài Liệu Đầu Vào Đã Đọc (Inputs Read)

- Repository state tại `3faedfde` (nhánh
  `claude/reports-pipeline-architecture-gj8bji`).
- Frozen task gate: `docs/tasks/TASK-PRA-001-legacy-reference-vertical.md`
  (10 check; 9 REQUIRED, 1 RECOMMENDED).
- Diff thật của ba commit `7d84072` → `5bea87a` → `3faedfde`.
- Governance liên quan: `governance/core/V4_1_POLICY_FREEZE.md` (§2 review
  budget, §4 blast radius theo failure path), `governance/core/EVIDENCE_STANDARD.md`,
  `governance/core/TASK_COMPLETION_GATE_STANDARD.md`.

## Independent Review #1 — `CHANGES_REQUIRED`

### FIND-PRA001-R01 (BLOCKING) — thiếu dòng nguồn vẫn báo "khớp 100 %"

`tools/analysis/verify_legacy_import.py` duyệt từ DB → Excel, nên chỉ trả
lời được *"những gì đã nhập có đúng không"*, không bao giờ trả lời được
*"có gì chưa được nhập không"*. Một sheet bị bỏ trọn vẫn cho
`matched>0 mismatched=0`.

Tái tạo của reviewer (giữ nguyên giá trị nghiệp vụ, bóc dấu hiệu công thức):

```text
Summary 2025 imported rows = 0
Source rows có giá trị nghiệp vụ: [4, 5, 6]
VERIFIER: matched=372 mismatched=0     ← mất trọn một kỳ mà vẫn PASS
```

### FIND-PRA001-R02 (BLOCKING) — sự cố database hiện ra như lỗi workbook của Owner

`abort(503)` của `_guarded` ném `HTTPException`, bị `except Exception` của
route import bắt và biến thành redirect kèm thông điệp "Không đọc được
workbook" — đổ lỗi cho file của Owner trong khi nguyên nhân là DB không
khả dụng.

Cả hai finding là **cùng một loại lỗi**: một sự cố được trình bày như một
trạng thái bình thường — đúng loại sai mà `TASK-PRA-001` tồn tại để ngăn.

## Repair Re-review — `PASS`

Repair cycle **1/1** thực hiện ở S076 trên base `7d84072` (KHÔNG rewrite),
kết quả `5bea87a`:

- R01 → `app/legacy/parser.py` raise `LegacyImportError` nêu đích danh
  sheet + số dòng cho dòng có giá trị nghiệp vụ nhưng không khớp contract
  phân loại (DEC-168: không đoán `row_kind` từ "dòng có số"); verifier đổi
  chiều vòng lặp Summary thành EXCEL → DB, in ba con số coverage, exit ≠ 0
  khi thiếu dòng nguồn.
- R02 → `except HTTPException: raise` đặt trước `except Exception` trong
  route import, để `abort(503)` không bị nuốt.

Bằng chứng đóng finding, nguyên văn theo S076:

```text
UNACCOUNTED Summary 2025!4 / !5 / !6
SUMMARY_SOURCE_ROWS_WITH_VALUES = 16
SUMMARY_IMPORTED_ROWS           = 13
SUMMARY_UNACCOUNTED_ROWS        = 3
exit=1
```

(Các con số fixture `16 / 13 / 3` và `matched=628` thuộc phạm vi **trước**
`DEC-169`, khi `Summary 2025` còn nằm trong phạm vi import. Xem mục
"Cập nhật sau DEC-169" ở cuối `docs/sessions/S076-pra-001-repair-cycle-1.md`
để có con số tái tạo hiện hành.)

## Final Independent Delta Review — `PASS`

Phạm vi: delta `5bea87a` → `3faedfde`, tức thay đổi do `DEC-169`
(`Summary 2025 = REFERENCE_ONLY`).

```text
FINAL_DELTA_REVIEW_RESULT   = PASS
DEC169_REVIEW               = FAITHFUL
PRA001_CODE_ACCEPTANCE      = PASS
PRA001_REAL_DATA_ACCEPTANCE = PASS
PRA001_REQUIRED_GATES       = 9/9 PASS
BLOCKING_FINDINGS           = NONE
REPAIR_CYCLES_REMAINING     = 0
```

`FAITHFUL` ở đây nghĩa là: code tại `3faedfde` thực hiện đúng những gì
`DEC-169` cho phép và **không hơn** — thu hẹp phạm vi import chứ không nới
lỏng guard. Toàn bộ test guard R01/DEC-168 được chĩa sang `Summary 2026`
(sheet REQUIRED_IMPORT) nên ngưỡng không bị hạ, và có thêm test bắt trường
hợp `Summary 2025` bị persist trở lại.

Finding không blocking của vòng này (`N07`, `N08`, `N11`, `N12`, `N13`) đều
là docs/evidence, đã được xử lý trong close-out S077 — xem
`docs/sessions/S077-pra-001-closeout-controlled-integration.md`.

## Sai Lệch So Với Tuyên Bố Của Người Triển Khai (Mismatches With Implementer Claims)

- Review #1: **CÓ** — implementer tuyên bố fidelity 100 % dựa trên
  `matched/mismatched`; reviewer chứng minh chỉ tiêu đó không đo được
  completeness. Đã đóng bằng repair cycle 1.
- Repair Re-review và Final Delta Review: **None**.

## Kết Luận (Conclusion)

`PASS` tại `3faedfdebc1f14d8a27e89955d9cfa64d6a462cd`.

`TASK_READY_TO_CLOSE = YES`, `READY_FOR_CONTROLLED_INTEGRATION = YES`.

## Việc Cần Theo Dõi Tiếp (Required Follow-up)

- `CHECK-PRA001-09` (RECOMMENDED) vẫn `BLOCKED` — cần PostgreSQL thật.
  Đây là **gate deploy của Owner**, tách khỏi PRA-001 DONE; quy trình ở
  `docs/deployment/S071_DEPLOYMENT.md` bước 8–12.
- Repair budget `TASK-PRA-001` = `0 remaining`. Mọi blocking finding tiếp
  theo phải leo thang theo `governance/core/ESCALATION_PROTOCOL.md`, không
  tự mở cycle 2.

## Bản Ghi Gốc Không Tồn Tại Trong Repo (ghi rõ, không dựng lại)

Không có file biên bản gốc do reviewer viết cho cả ba vòng. Những gì tồn
tại là session log, ledger và Owner verdict đã dẫn nguồn ở đầu file. File
này KHÔNG thay thế biên bản gốc và không được trích dẫn như thể là biên
bản đó.
