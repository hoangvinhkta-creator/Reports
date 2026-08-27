# REVIEW BUDGET LEDGER

Machine Control #2 của Governance V4.1 (`TASK-V4-ADOPTION`, §18).

Ledger này là bản ghi tường minh, đọc được bằng máy lẫn con người, về ngân
sách repair-cycle của từng root task lineage theo bảng đã freeze ở
`governance/core/RULE_PRECEDENCE.md` §... *(bảng ngân sách nằm trong chính
Owner Decision của V4.1 — xem `PROJECT/PROJECT_DECISIONS.md` DEC-V4.1-ADOPT-01
và các mục liên quan)*. Không phải nơi diễn giải lại luật; chỉ ghi trạng
thái.

## Bảng ngân sách đã freeze (V4.1)

```
LOW              = 1 blocking repair cycle
MEDIUM           = 1 blocking repair cycle
HIGH / CRITICAL  = 2 blocking repair cycles
```

Không tồn tại `HIGH = 3`. Owner được phép đặt budget thấp hơn bảng này cho
một root task cụ thể. Vượt budget → `OWNER_EXTENSION REQUIRED`.

Ngân sách gắn với **ROOT TASK LINEAGE**. Sub-unit (ví dụ R1-A2, R1-B, R2…)
không có ngân sách riêng, không reset ngân sách, và không được tạo lineage
mới chỉ để reset ngân sách.

---

## Root Task: TASK-V4-ADOPTION

```
root_task: TASK-V4-ADOPTION
effective_risk: MEDIUM
repair_cycles_allowed: 1
repair_cycles_used: 0
repair_cycles_remaining: 1
```

Production code changes: FORBIDDEN (theo phạm vi V4.1-0).

Nếu adoption không hoàn thành sau 1 blocking repair cycle: DESCOPE →
MINIMAL V4.1 OVERLAY (không tạo V4.1-R1, V4.1-R1A, V4.1-Repair-2, hay bất kỳ
decomposition nào nhằm reset budget).

cycles:
- id: (chưa mở — adoption hoàn thành trong 0 repair cycle tính đến thời
  điểm ghi ledger này)
  base_sha: N/A
  head_sha: N/A

---

## Root Task: TASK-110

Đây là **transition ledger có chủ ý** cho một root task lineage đã tồn tại
từ trước V4.1, được V4.1 tiếp nhận nguyên trạng — không được cấp lại ngân
sách, không được đưa giá trị `repair_cycles_remaining` về khác 0 chỉ vì V4.1
mới có hiệu lực.

```
root_task: TASK-110
effective_risk: HIGH
repair_cycles_allowed: 2
repair_cycles_used: EXHAUSTED_PRE_V4.1
repair_cycles_remaining: 0

historical_evidence:
    independent_reviews: ">=8"
    repairs: ">=3"

authorized_actions:
    - FINAL_REVIEW_ONLY
    - ACCEPT_AS_IS
    - DESCOPE
    - OWNER_EXTENSION
```

**TASK-110 BUDGET = EXHAUSTED.** Đây là trạng thái chuyển tiếp có chủ ý, ghi
tại thời điểm V4.1 adoption (2026-08-27), không phải placeholder chờ điền
sau.

### Sub-unit lineage — không có ngân sách riêng

R1-A2, R1-A3, R1-A4, R1-B … R1-E, R2 … R8 — nếu thuộc `TASK-110` thì đều
thuộc cùng lineage `TASK-110`. Vì `TASK-110.repair_cycles_remaining = 0`,
**không unit nào trong nhóm này được tự mở**. Mỗi unit muốn tiếp tục phải
có một `OWNER_EXTENSION` riêng, kèm:

- production path cụ thể;
- kịch bản nghiệp vụ sai cụ thể nếu không xử lý;
- phạm vi được phép;
- budget được Owner cấp.

Không có Owner Extension tương ứng → `STOP`.

### Cycle accounting lịch sử (tham chiếu, không phải ngân sách còn lại)

Cumulative repair diff của TASK-110 được ghi trong các session log dưới
`docs/sessions/S015` … `S023` và trong `PROJECT/PROJECT_DECISIONS.md`
(DEC-128 … DEC-134 trở lên tại các nhánh review đang hoạt động). Ledger này
không sao chép lại toàn bộ lịch sử đó — chỉ xác nhận điểm chốt: ngân sách
repair-cycle của lineage `TASK-110` đã cạn TRƯỚC khi V4.1 có hiệu lực.

cycles:
- id: PRE_V4.1_HISTORICAL
  base_sha: (xem lịch sử session TASK-110 — ngoài phạm vi ghi lại tại đây)
  head_sha: (xem lịch sử session TASK-110 — ngoài phạm vi ghi lại tại đây)
  note: >
    Lịch sử đầy đủ (>=8 Independent Review, >=3 repair) nằm trong
    docs/sessions/ và PROJECT/PROJECT_DECISIONS.md trên các nhánh review
    TASK-110 đang hoạt động. Ledger V4.1 chỉ ghi nhận điểm chốt ngân sách,
    không viết lại lịch sử.

### Merge gate liên quan

`CHECK-110-16` vẫn là **merge gate**, không phải review gate, và hiện
**BLOCKED** (thiếu production workbook thật để đối chiếu). Không được giả
lập PASS hay bypass. Xem `governance/core/TASK_COMPLETION_GATE_STANDARD.md`
và các quyết định liên quan trong `PROJECT/PROJECT_DECISIONS.md`.

Nếu merge gate `BLOCKED` quá 30 ngày kể từ ngày phát sinh: `OWNER DECISION
REQUIRED` (cung cấp dependency/data; đổi thành
`POST_MERGE_PRODUCTION_ACCEPTANCE`; hoặc gỡ khỏi gate set). Không được tiếp
tục BLOCKED vô thời hạn mà không có quyết định.

### Branch divergence đã biết

`TASK-110` hiện có nhiều nhánh review độc lập vượt xa các ngưỡng
`ahead > 10 commits` / `divergence > 3 ngày` / `cumulative changed LOC >
5,000` so với nhánh mặc định của remote. Đây là **KNOWN PRE-V4.1
DIVERGENCE**, phải được Owner xử lý tại V4.1-1 (integrate/merge sớm; cắt
scope; hoặc tiếp tục divergence có lý do + review date). Không grandfather
thành permanent exception.

---

## Cách xác định phạm vi một repair cycle (tham chiếu)

```
git diff <base_sha>..<head_sha> --name-only
```

Cycle được tính theo LẦN SỬA, không theo số review. Nếu repair tiếp tục
trong cùng cycle, `head_sha` phải tiến lên SHA mới; `base_sha` không reset.
Không dùng session mới / sub-unit mới / branch mới để reset `base_sha`.

## Owner Extension log

*(Trống tại thời điểm adoption. Mỗi Owner Extension được cấp sau này phải
thêm một mục vào đây, kèm root task, phạm vi, và budget cụ thể.)*

## Cập nhật gần nhất

- 2026-08-27 — Khởi tạo ledger tại `TASK-V4-ADOPTION` (V4.1-0, Policy
  Adoption). `TASK-V4-ADOPTION` mở với 1 repair cycle khả dụng, 0 đã dùng.
  `TASK-110` ghi nhận ở trạng thái transition `EXHAUSTED_PRE_V4.1`, remaining
  = 0.
