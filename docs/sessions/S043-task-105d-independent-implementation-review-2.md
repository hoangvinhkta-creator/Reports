# S043 — TASK-105D Independent Implementation Review #2 (RC-1 Verification)

```text
Session       : S043
Ngày          : 2026-08-28
Loại phiên    : INDEPENDENT IMPLEMENTATION REVIEW #2 (read-only reviewer)
Root task     : TASK-105D — Product Identity Resolver
Nhánh         : review/task-105d-implementation-2
Target review : origin/task/task-105d-rc1 = a09823506fc17b7903e44be848672a18f92bc6ee
Selected Profile  : PRODUCT
Current Task Mode : MAJOR
Risk          : Effective Risk HIGH — max(Local Risk 4, Blast Radius 5)
Evidence Level: E2
Artifact      : docs/reviews/TASK-105D-INDEPENDENT-IMPLEMENTATION-REVIEW-2.md
```

## Mục đích

Xác định **độc lập** xem `RC-1` có thật sự đóng finding `BLOCKING` `B-01` hay
không. Tuyên bố của phiên repair (`S042`) — `B-01 = CODE-LEVEL RESOLVED /
READY FOR INDEPENDENT RE-REVIEW` — được đối xử như giả thuyết cần chứng minh
hoặc bác bỏ, **không** phải kết luận kế thừa.

Reviewer không phải tác giả `S040` (implementation) và không phải tác giả
`S042` (repair) — `V4.1` §12.

## SHA

```text
RC-1 final          : a09823506fc17b7903e44be848672a18f92bc6ee
repair              : 1cc96a99638326513b26280b72bbeb3bce9d454d
implementation gốc  : e6252c06347ed5305fc32a77706a3a63f5a950cf
Review #1 evidence  : 58323e2e59382e2ce4816453cfaaa5d31deba3db
base / default      : 222844dfb5cf576238fda4cc913ef2095789b4eb
```

`HEAD == origin/task/task-105d-rc1`; worktree sạch. Artifact Review #1 đọc bằng
`git show 58323e2e:…` — **không** merge nhánh review-1 vào RC-1.

## Việc đã làm

1. Pre-flight + xác minh ba object tham chiếu; `branch_authority_check.sh` =
   `AUTHORITY_OK`.
2. Đọc canonical evidence: `CLAUDE.md`,
   `governance/core/V4_1_POLICY_FREEZE.md`,
   `governance/core/TASK_COMPLETION_GATE_STANDARD.md`, task `TASK-105D`, data contract,
   khối gate đã freeze, `DEC-154`…`DEC-158`, `S039`/`S040`/`S042`,
   artifact Review #1 (`58323e2e`), repair record `RC-1`, `PROJECT_PROGRESS`,
   `REVIEW_BUDGET_LEDGER`.
3. Rà **từng dòng production** của diff `e6252c06 → 1cc96a99`; phân loại
   A (mã sửa) / B (test mới) / C (governance). Scope creep = KHÔNG.
4. **Tái lập `B-01`** trên mã trước repair bằng bộ đối kháng RIÊNG (`spawn`,
   `multiprocessing.Barrier`, không `sleep`, store dựng sau khi tiến trình con
   khởi động): 10/10 vòng cho hai `APPLIED` + integrity error vĩnh viễn.
5. Chạy cùng race trên RC-1: **135 vòng / >300 tiến trình HĐH** ở 7 kịch bản
   (n = 2/4/8, request-id giống và khác, `append` vs `rebuild_index`) —
   0 bất thường.
6. Kiểm cơ chế khoá thật ở mức HĐH: `store.append()` production bị chặn > 2 s
   sau một holder; `SIGKILL` → nhân trả khoá → probe hoàn tất.
7. Liệt kê **độc lập** mọi đường ghi bền vững bằng quét tĩnh toàn `app/` —
   không tin con số "ba" của tác giả.
8. Anti-tautology: chạy 25 test mới trên mã trước repair → **19 failed**.
9. Thực thi lại **32 frozen check** (32/32 PASS) và **A–T** (20/20 PASS);
   tái lập `GATE_SET_SHA256`; chạy Golden, targeted, full suite, 5 validator.
10. Đo hiệu năng RC-1 vs pre-repair để tách chi phí khoá khỏi `H-04`.
11. Đối chiếu 10 `HARDENING` đã có bằng **phép đo lại**, không bằng trích dẫn.

## Kết quả

```text
VERDICT : PASS WITH HARDENING — RC-1 VERIFIED / ELIGIBLE FOR CONTROLLED INTEGRATION

B-01                : CLOSED — 10/10 tiêu chí đóng PASS (xác minh độc lập)
BLOCKING            : 0
HARDENING           : 5 mới (H2-01…H2-05) + 10 kế thừa VẪN OPEN
OUT_OF_SCOPE        : 4

32 frozen check     : 32 / 32 PASS
A–T                 : 20 / 20 PASS
GATE_SET_SHA256     : 0444e58c…  KHỚP TUYỆT ĐỐI (57.614 byte)
targeted TASK-105D  : 199 passed
Golden              : 58 passed, 2 skipped — KHÔNG ĐỔI
Full suite          : 955 passed, 11 skipped   (930 → 955 = +25)
Regression          : 0
Validator           : 4/5 PASS; reference_integrity 3 (baseline) → 4  (H2-02)
Repair budget       : 2 allowed / 1 used / 1 remaining — KHÔNG ĐỔI
Repair Cycle #2     : KHÔNG mở
```

`HARDENING` mới:

```text
H2-01  _consume() mutate state trước khi đẩy _log_offset ⇒ thử lại sau lỗi
       nạp trùng bản ghi; current_revision() phồng đơn điệu. Fail closed ở
       MỌI lần, 0 byte ghi xuống đĩa. Nằm TRONG cumulative repair diff RC-1
       (V4.1 §3 ⇒ sửa thuộc CÙNG cycle #1).
H2-02  RC-1 tạo thêm ĐÚNG MỘT lỗi reference_integrity (repair record trỏ tới
       artifact Review #1 chưa có trên lineage này). Baseline 3 → 4.
H2-03  Event đã commit nhưng caller nhận exception khi ghi index lỗi. Hình
       dạng CÓ SẴN trước repair — không phải hồi quy RC-1.
H2-04  test_both_orderings_actually_occur_across_rounds không khẳng định điều
       tên nó nói (PASS cả trên mã hỏng).
H2-05  Log truncate về rỗng: instance sống phát hiện, store mở mới thì không.
```

`H-07` (gate authority): `NOT_TESTED` trong khối gate chặn **`DONE`**, **không**
chặn integration. Reconciliation bắt buộc **trước `DONE`**; khuyến nghị đường
Owner Decision công nhận bản ghi thực thi tách rời, giữ nguyên
`GATE_SET_SHA256`. Chi tiết: `§23` của artifact.

## Ranh giới

```text
app/** , tests/** , config/**        : 0 dòng thay đổi
khối Completion Gate đã freeze        : KHÔNG SỬA (hash khớp sau khi ghi artifact)
data contract                         : KHÔNG SỬA
nhánh task/task-105d-rc1              : KHÔNG mutate
nhánh task/task-105d-implementation   : KHÔNG mutate
default branch / merge                : KHÔNG
production data / Tracking            : KHÔNG CHẠM
FilePriceProvider activate            : KHÔNG
TASK-105E implement                   : KHÔNG
DONE                                  : KHÔNG đánh dấu
```

Script đối kháng nằm ở scratchpad ngoài repo, **không** commit.

## Bàn giao — hành động kế tiếp được phép

```text
1. OWNER INTEGRATION DECISION (V4.1 §8 — DIVERGENCE = INTEGRATION_DECISION_
   REQUIRED, loc > 5.000): chọn (A)/(B)/(C). Khuyến nghị (A).
2. NẾU (A): phiên CONTROLLED INTEGRATION merge --no-ff lineage TASK-105D,
   kèm cả artifact Review #1 và Review #2 ⇒ tự phân giải H2-02.
3. TRƯỚC khi đề xuất DONE: Owner reconcile H-07 (§23 của artifact).
4. KHÔNG mở Repair Cycle #2. H2-01 + H-05 cùng vùng mã (_consume) — nếu Owner
   cho sửa, sửa MỘT lượt, thuộc CÙNG cycle #1.
5. Song song: phiên có thẩm quyền data contract đóng H-02, HB-105D-F2-01/-02.
```
