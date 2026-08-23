# SESSION HANDOFF

Session ID:
S004

Task:
REM-T04 / MICRO-001 — Sửa các reference đường dẫn canonical bị gãy

Task Mode:
MICRO

Project Profile:
PRODUCT

Status:
DONE

Date:
2026-08-23 (UTC)

Branch:
`claude/s001-discovery-pka3fu`

Commit lúc mở session:
`81c115a`

## Kết Quả

Đóng REM-T04. Cả ba reference trong Scope Lock đã đúng và phân giải được;
FIND-003 và FIND-004 chuyển sang RESOLVED. Tổng finding đã đóng: 4/12.

Điểm đáng chú ý nhất của session này **không phải** là việc sửa, mà là việc
xử lý một gate đã frozen không còn thỏa mãn được.

### Vấn đề gate

Ba sửa đổi trong Scope Lock đã được thực hiện **tiện thể** bên trong commit
`81c115a` (dịch repo sang tiếng Việt, DEC-011), chứ không phải trong một commit
riêng của MICRO-001. Hệ quả: check thứ hai của Compact Completion Gate đã
frozen —

> "`git diff` chỉ cho thấy thay đổi path-token trên đúng ba dòng — E1"

— trở thành **không thể thỏa mãn**. Diff cô lập ba dòng đó không tồn tại và
không thể tạo ra mà không viết lại lịch sử đã push.

Có ba cách xử lý, và hai trong số đó sai:
- Đánh PASS cho check chưa từng chạy → vi phạm `governance/core/EVIDENCE_STANDARD.md`.
- Âm thầm bỏ qua check → vi phạm `governance/core/TASK_COMPLETION_GATE_STANDARD.md`
  ("Không được âm thầm hạ thấp tiêu chí chất lượng").
- Phát hành COMPLETION GATE CHANGE PROPOSAL tường minh → đã chọn.

Gate được thay bằng hai check có **độ phủ rộng hơn** check gốc: thay vì chứng
minh "ba dòng đã đổi trong một diff", chứng minh trạng thái reference của
**toàn bộ repo** không hồi quy so với baseline. Chi tiết: DEC-012.

## Subtask Hoàn Thành
- Xác minh trạng thái thực tế của cả ba token trong Scope Lock
- Chạy scan reference-integrity toàn repo (T04-C1)
- Xác minh từng token đích mang giá trị canonical đúng và đích tồn tại (T04-C2a)
- So sánh broken-reference giữa baseline `0394267` và HEAD (T04-C2b)
- Xác minh riêng FIND-004 (`templates/` không có đuôi mở rộng nên nằm ngoài scan)
- Xác minh 2 file `PROJECT/` có broken-ref mới thực chất là nội dung mới
  (baseline là template rỗng, 0 token liên quan)
- Phát hành COMPLETION GATE CHANGE PROPOSAL (DEC-012)
- Cập nhật MICRO-001, roadmap, traceability

## Subtask Còn Lại
- Không có cho REM-T04.

## Tóm Tắt Completion Gate

Required:
3 (sau khi sửa gate qua DEC-012; gate gốc có 2, một trong đó tách thành hai)

PASS:
3

FAIL:
0

BLOCKED:
0

NOT_TESTED:
0

## Bằng Chứng Xác Minh

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| T04-C1 | PASS | E1 | Scan reference-integrity toàn repo → `BROKEN (ngoài ngoại lệ): 0`, `EXEMPT: 20` | S004 agent | 2026-08-23T02:1xZ |
| T04-C2a | PASS | E1 | `CLAUDE.md:228` và `PROJECT_PROFILE_STANDARD.md:77` → `governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md`; `CLAUDE.md:40` → `governance/templates/`; cả hai đích `EXISTS` trên đĩa | S004 agent | 2026-08-23T02:1xZ |
| T04-C2b | PASS | E1 | Baseline `0394267` ↔ HEAD: `ĐÃ SỬA: 2` (đúng hai broken ref của FIND-003); FIND-004 xác minh riêng bằng đối chiếu token; 12 mục "broken mới" đều nằm trong file tạo mới S001–S003 hoặc 2 file `PROJECT/` có baseline là template rỗng (0 token liên quan) → **0 hồi quy** | S004 agent | 2026-08-23T02:1xZ |

Trạng thái E2:
KHÔNG THU THẬP. Task này Risk 2 — `governance/core/EVIDENCE_STANDARD.md` chỉ
yêu cầu E1 cho Risk 1–2, nên đây không phải thiếu sót. RSK-004 (chưa có nguồn
E2 bền vững) vẫn còn mở và vẫn thuộc REM-T07.

## File Đã Thay Đổi

Đã tạo:
- `docs/sessions/S004-reference-repair.md`

Đã sửa:
- `PROJECT/PROJECT_DECISIONS.md` — DEC-012 (kèm COMPLETION GATE CHANGE PROPOSAL)
- `PROJECT/PROJECT_PROGRESS.md` — MICRO-001 → DONE kèm evidence; roadmap
  checkbox; findings register (FIND-003, FIND-004 → RESOLVED, 4/12); bảng gate
  freeze; lịch sử session; session tiếp theo
- `docs/audit/REMEDIATION_ROADMAP.md` — REM-T04 → DONE; traceability; dependency
  graph; revision history rev 4; resolved count

**Không đụng tới** `governance/` — không cần, vì cả ba sửa đổi đã có sẵn.
**Không đụng tới** `docs/audit/S001_*` — bản ghi audit bất biến.

## Quyết Định Chính
- DEC-012 — COMPLETION GATE CHANGE PROPOSAL cho MICRO-001; thay check "diff ba
  dòng" bằng T04-C2a + T04-C2b; ghi nhận quan sát về kỷ luật phạm vi

## Rủi Ro / Blocker

Blocker:
- Không có.

Rủi ro:
- RSK-001 — FIND-001 đã đóng; FIND-007 vẫn mở, REM-T03 đang READY để đóng.
- RSK-002 — chưa đổi. Không coi bất kỳ điều gì dưới `governance/reference/` là
  evidence cho tới khi REM-T05 hoàn tất.
- RSK-004 — chưa có nguồn E2 bền vững. REM-T07 vẫn là task tạo ra nó.
- RSK-005 — chưa đổi.
- **RSK-006 (mới)** — Kỷ luật phạm vi. Đây là lần thứ hai công việc thuộc một
  task được thực hiện bên ngoài task đó (lần đầu: `.gitignore` của REM-T06 ở
  S003). Cả hai lần đều được ghi nhận trung thực, nhưng sửa "tiện thể" làm
  hỏng khả năng kiểm chứng của gate vốn được thiết kế quanh giả định
  một-task-một-diff — chính là nguyên nhân buộc phải sửa gate ở session này.
  Giảm thiểu: khi phát hiện sửa đổi thuộc task khác trong lúc làm việc, ghi
  nhận thay vì tự sửa, trừ khi task đó đang READY và chủ dự án đồng ý gộp.

## Hạng Mục Regression
- Không có. T04-C2b xác nhận 0 hồi quy trên mọi file đã tồn tại ở baseline.

## Chưa Được Thay Đổi
- Gate PHASE-01 đã frozen của REM-T07 và REM-T03.
- `docs/audit/S001_*` — bản ghi audit bất biến.
- `governance/reference/history/` — kho lưu trữ đóng băng. FIND-011 xử lý bằng
  cách giới hạn phạm vi validator (REM-T03), không phải viết lại lịch sử.

## Session Tiếp Theo Được Đề Xuất

S005 — REM-T07 (CI enforcement) hoặc REM-T03 (validator hardening). Cả hai
đang READY, chạy song song an toàn, Scope Lock không giao nhau.

Khuyến nghị REM-T07 trước: nó tạo nguồn E2 bền vững (đóng RSK-004), mà các
task rủi ro cao sau này nên dựa vào thay vì spawn reviewer dùng một lần như
REM-T02 đã phải làm.

REM-T03 cũng đáng chú ý: nó tạo `validate_reference_integrity.py` — sẽ thay
thế script ad-hoc mà S004 vừa dùng, biến T04-C1/C2a/C2b thành kiểm tra tự
động, tái lập được.

## File Agent Tiếp Theo Nên Đọc
1. `CLAUDE.md`
2. `PROJECT/PROJECT_PROFILE.md`
3. `PROJECT/PROJECT_PROGRESS.md`
4. `docs/sessions/S004-reference-repair.md`  ← file này
5. File task được chọn (`docs/tasks/TASK-REM-T07-ci-enforcement.md` hoặc
   `docs/tasks/TASK-REM-T03-validator-hardening.md`)
6. `governance/core/EVIDENCE_STANDARD.md`
7. `governance/core/TASK_COMPLETION_GATE_STANDARD.md`

## Prompt Mở Session Tiếp Theo

```text
Đây là S005 — tiếp tục PHASE-01. REM-T07 và REM-T03 đều đang READY và độc lập
với nhau. Tiếp tục từ repository state, không dựa vào trí nhớ hội thoại.

Chạy Session Open Protocol:
1. Đọc CLAUDE.md
2. Đọc PROJECT/PROJECT_PROFILE.md
3. Đọc PROJECT/PROJECT_PROGRESS.md
4. Đọc docs/sessions/S004-reference-repair.md
5. Đọc task file của task được chọn

Nếu chưa được chỉ định task cụ thể, đề xuất REM-T07 trước (thiết lập nguồn E2
bền vững, đóng RSK-004), rồi hỏi xác nhận trước khi bắt đầu.

Yêu cầu khi thực hiện:
- Tuân thủ đúng Scope Lock và Completion Gate đã frozen của task được chọn.
- Không sửa gì ngoài scope. Nếu phát hiện sửa đổi thuộc task khác, GHI NHẬN
  thay vì tự sửa (RSK-006) — trừ khi task đó đang READY và chủ dự án đồng ý.
- Không hạ bất kỳ REQUIRED check nào. Nếu một check trở thành không thể thỏa
  mãn, dùng COMPLETION GATE CHANGE PROPOSAL như S004 đã làm, không đánh PASS.
- Với REM-T07: CHECK-T07-03 bắt buộc phải quan sát được CI thực sự FAIL trên
  một breakage cố ý. Không merge breakage đó.
```
