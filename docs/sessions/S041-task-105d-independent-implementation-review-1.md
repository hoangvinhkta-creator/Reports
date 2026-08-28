# S041 — TASK-105D Independent Implementation Review #1

## Metadata

Session Type:
Independent Implementation Review (`V4.1` §12) — reviewer độc lập, KHÔNG phải
tác giả implementation.

Timestamp:
2026-08-28

Selected Profile:
PRODUCT

Current Task Mode:
MAJOR

Risk:
Effective Risk `HIGH` — `max(Local Risk 4, Blast Radius 5)`.

Evidence Level:
E2

Branch:
`review/task-105d-implementation-1`

Implementation target SHA:
`e6252c06347ed5305fc32a77706a3a63f5a950cf`

Implementation base SHA:
`222844dfb5cf576238fda4cc913ef2095789b4eb`

Verdict:
**FAIL — REPAIR REQUIRED** (1 BLOCKING, 7 HARDENING, 3 OUT_OF_SCOPE).

Bằng chứng đầy đủ:
`docs/reviews/TASK-105D-INDEPENDENT-IMPLEMENTATION-REVIEW-1.md`

## 1. Điều phiên này làm

- Tái lập ĐỘC LẬP `GATE_SET_SHA256` = `0444e58c…` → KHỚP tuyệt đối (57.614 byte).
- Review toàn bộ diff `222844df → e6252c0` (30 file, +9.014 dòng) theo 17 nhóm.
- Thực thi ĐỘC LẬP cả 32 frozen check → 32/32 PASS.
- Viết bộ đối kháng A–T RIÊNG (không sao chép test của `S040`) → 20/20 PASS.
- Chạy Golden, targeted, full suite, và full suite tại base SHA trên một
  worktree tách riêng để xác minh delta `+174`.
- Chạy 5 script đối kháng ngoài repo: concurrency đa tiến trình, persistence/
  tampering/performance, cutover spy, authority matrix, input integrity.

## 2. Điều phiên này KHÔNG làm

```text
sửa app/**                     : KHÔNG
sửa tests/**                   : KHÔNG
sửa production config          : KHÔNG
sửa frozen gate block          : KHÔNG — 32 trường Status: giữ nguyên NOT_TESTED
sửa data contract              : KHÔNG
repair bất kỳ finding nào      : KHÔNG — reviewer không tự repair
merge vào default              : KHÔNG
đánh dấu TASK-105D DONE        : KHÔNG
commit script đối kháng         : KHÔNG (nằm ở scratchpad ngoài repo)
```

## 3. Kết quả đo được

```text
GATE_SET_SHA256   tái lập KHỚP
32 frozen check   32 / 32 PASS
A–T               20 / 20 PASS
Golden            58 passed, 2 skipped   (base: giống hệt)
Targeted 105D     174 passed
Full @ base       756 passed, 11 skipped
Full @ candidate  930 passed, 11 skipped
delta             +174 — khớp chính xác
regression        0
validator         4 PASS; reference_integrity FAIL giống hệt base (O-01)
```

## 4. Findings

```text
BLOCKING     1   B-01  thiếu khoá file → check-then-append race ở đúng biên
                       "một máy" mà data contract §11.1 tuyên bố phủ; INV-59
                       không được thi hành qua biên tiến trình; store trở nên
                       không đọc được vĩnh viễn, không có đường phục hồi
                       trong contract (INV-66/INV-67).

HARDENING    7   H-01  CONFIRMATION_ACTION_TYPES (tập ĐẾM) bị dùng làm tập
                       THẨM QUYỀN → CORRECT_MAPPING bị chặn đúng case phổ biến
                 H-02  (H-05 kế thừa) ranking_method_id — RESOLVED_AT_
                       IMPLEMENTATION_ONLY; contract text VẪN OPEN
                 H-03  test reference sai cho CHECK-105D-26/-27 trong Gate
                       Execution Record (E2 không tái lập nguyên văn)
                 H-04  rebuild_index() O(n) mỗi append ⇒ O(n²) bulk
                 H-05  dòng log sai khuôn raise lỗi không thuộc miền
                 H-06  hai test migration/rollback mỏng (INV-81/INV-82)
                 H-07  32 trường Status: còn NOT_TESTED ⇒ chặn DONE

OUT_OF_SCOPE 3   O-01  reference_integrity — có trước, giống hệt base
                 O-02  HB-105D-F2-01 binding "bộ ba" vs "CẢ BỐN" — VẪN OPEN
                 O-03  HB-105D-F2-02 §16.1 stale — VẪN OPEN
```

## 5. Review Budget

```text
trước : 2 allowed / 0 used / 2 remaining
sau   : 2 allowed / 0 used / 2 remaining   (KHÔNG ĐỔI)
```

Independent review KHÔNG tiêu thụ Repair Cycle (`V4.1` §3 — phiên này 0 dòng
code/test). Có BLOCKING ⇒ **khuyến nghị mở Repair Cycle #1**; reviewer không
tự repair.

## 6. Handoff — hành động kế tiếp được phép

```text
1. Owner quyết định hướng đóng B-01: (a) thêm khoá file, giữ nguyên contract;
   HOẶC (b) thu hẹp phạm vi đã claim ở §11.1 xuống MỘT TIẾN TRÌNH (thay đổi
   data contract, cần authority riêng).
2. Repair Cycle #1 thực hiện quyết định đó + H-01. Sau repair: 2/1/1.
3. Independent Implementation Review #2 (phiên KHÁC) trên SHA sau repair.
4. CHỈ SAU (3) PASS: quyết định integration theo V4.1 §8.
5. Song song: phiên có thẩm quyền data contract đóng H-02/O-02/O-03; phiên có
   gate authority xử lý H-07 trước khi bất kỳ ai đề xuất DONE.
```

`TASK-105D` giữ nguyên **IMPLEMENTATION CANDIDATE** — KHÔNG eligible for
integration cho tới khi `B-01` được đóng.
