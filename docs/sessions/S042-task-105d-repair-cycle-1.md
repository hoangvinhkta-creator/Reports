# S042 — TASK-105D Repair Cycle #1 (B-01)

```text
Timestamp        : 2026-08-28
Selected Profile : PRODUCT
Current Task Mode: MAJOR
Task             : TASK-105D — Product Identity Resolver
Branch           : task/task-105d-rc1
Base SHA         : e6252c06347ed5305fc32a77706a3a63f5a950cf
Trigger          : B-01 (Independent Implementation Review #1, S041)
Review evidence  : 58323e2e59382e2ce4816453cfaaa5d31deba3db
Authority        : Owner APPROVES Repair Cycle #1; Owner Decision B-01 = (a)
Evidence Level   : E2
Risk             : HIGH (max(Local 4, Blast Radius 5))
```

## Phạm vi phiên

Chỉ sửa `B-01` — thiếu khoá liên-tiến-trình quanh giao dịch persistence — cộng
test và bằng chứng cần để chứng minh bản sửa. KHÔNG sửa cơ hội bất kỳ
HARDENING nào khác.

Owner chọn phương án (a): GIỮ hợp đồng concurrency "một máy, nhiều tiến
trình" của data contract `§11.1`, sửa IMPLEMENTATION cho khớp lời hứa đó.
Không thu hẹp `§11.1` xuống một tiến trình; không sửa Completion Gate đã
freeze.

## Việc đã làm

1. Pre-flight: branch/HEAD/worktree khớp; SHA bằng chứng review truy xuất
   được sau `git fetch origin`; đọc nguyên văn artifact review.
2. Tái lập `B-01` bằng hai tiến trình thật: hai APPLIED, hai bản ghi
   `CONFIRMED` độc lập, `MappingIntegrityError` vĩnh viễn.
3. Sửa `store.py`: `_transaction()` (`fcntl.flock` `LOCK_EX` trên
   `<log>.lock`), `_refresh_from_disk()` nạp lại tăng dần trong khoá,
   `_consume()`, `_append_line()`; `append()` / `import_bundle()` /
   `rebuild_index()` đều vào cùng biên giao dịch; xoá đường ghi thứ hai
   `_persist_raw()`.
4. Thêm `tests/test_105d_interprocess_concurrency.py` — 25 test, tranh chấp
   thật bằng `multiprocessing.Barrier`.
5. Chứng minh bộ test bắt được defect: chạy nó ở base `e6252c0` → 18 failed.
6. Chạy targeted / Golden / full suite + toàn bộ validator canonical.
7. Ghi bằng chứng RC-1 và cập nhật ledger/progress.

## Kết quả đo được

```text
race 2 tiến trình, 60 vòng : mọi vòng = 1 APPLIED + 1 MappingVersionConflict
                             phân bố người thắng 26 / 34 (tranh chấp thật)
reopen từ đĩa              : 1 mapping CONFIRMED, version 1, revision 1, 0 lỗi
targeted TASK-105D         : 174 → 199 (+25)
Golden                     : 58 passed, 2 skipped  (KHÔNG ĐỔI)
full suite                 : 930 → 955 (+25), skipped 11 → 11
regression                 : 0
GATE_SET_SHA256            : 0444e58c… KHỚP, khối gate 0 byte thay đổi
validators                 : như base (reference_integrity FAIL = đúng 3 issue
                             TASK-REM-T06 đã biết)
hiệu năng append           : +4…9 % (khoá không phải thành phần chi phối)
```

## Ranh giới đã giữ

```text
production data / Tracking / FilePriceProvider / TASK-105E / default branch /
merge / task-105d-implementation / frozen gate / data contract
    → KHÔNG chạm, KHÔNG đổi, KHÔNG kích hoạt, KHÔNG merge
NOT_TESTED → PASS  : KHÔNG thực hiện (không có gate authority ở phiên này)
```

## Ngân sách

`2 allowed / 0 used / 2 remaining` → `2 allowed / 1 used / 1 remaining`.

## Bàn giao

Trạng thái: **REPAIR CANDIDATE — READY FOR INDEPENDENT REVIEW #2.**

Phiên này KHÔNG tự review chính mình và KHÔNG tuyên bố Independent Review #2
PASS. Hành động kế tiếp được phép: Independent Implementation Review #2 do một
phiên KHÁC thực hiện trên `task/task-105d-rc1`.

Bằng chứng đầy đủ: `docs/reviews/TASK-105D-RC-1-REPAIR-RECORD.md`.
