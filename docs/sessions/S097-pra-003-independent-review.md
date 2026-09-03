# S097 — TASK-PRA-003 Independent Review E2 (Tổng Quan + Nhân Viên)

## Metadata

```
SESSION                : S097 — PRA-003 Independent Review E2 (docs-only)
NGÀY                   : 2026-09-03
TASK MODE              : MAJOR (phiên review, không implement)
TASK                   : TASK-PRA-003 — Tổng Quan + Nhân Viên
TRẠNG THÁI TASK SAU PHIÊN: IN_PROGRESS (KHÔNG phải DONE — còn CHECK-07)
PROJECT PROFILE        : PRODUCT
RISK                   : 3        BLAST RADIUS : 3/5
BASE_SHA               : facf090c782b022730ecc5f1cf0d0b02e29ca8d7
REVIEW_TARGET_SHA      : a36f95917ce35acee0a05e215fbfa08df3a9ebe9
FROZEN_CONTRACT_SHA    : c12c5635b5e4298a9584b5fa93e21762c0d70c5b
NHÁNH REVIEW           : claude/pra-003-roadmap-finalization-di33bn
ARTIFACT               : docs/reviews/TASK-PRA-003-INDEPENDENT-REVIEW-RECORD.md
```

Phiên này là **reviewer ĐỘC LẬP**. Không tiếp nối lập luận của implementer,
không coi báo cáo S096 là thẩm quyền. Thứ tự đọc:
`OWNER DECISIONS → FROZEN CONTRACT → DIFF → TESTS → EVIDENCE`.

## Xác Minh Thẩm Quyền (đầu phiên, TRƯỚC khi đọc governance)

```
git remote show origin → HEAD branch : claude/extract-upload-repo-gq2ws4
git rev-parse origin/claude/extract-upload-repo-gq2ws4
  → facf090c782b022730ecc5f1cf0d0b02e29ca8d7   ✓ khớp BASE_SHA kỳ vọng
git rev-parse origin/claude/pra-003-roadmap-finalization-di33bn
  → a36f95917ce35acee0a05e215fbfa08df3a9ebe9   ✓ khớp REVIEW_TARGET kỳ vọng
git cat-file -t c12c5635…                      ✓ commit tồn tại
```

`REVIEW_TARGET_MOVED = KHÔNG`. `branch_authority_check.sh` → `AUTHORITY_OK`,
`DIVERGENCE = WITHIN_LIMITS`.

Clone ban đầu là **shallow**; đã `git fetch --unshallow` (252 commit) TRƯỚC khi
đo, nên không gặp lỗi `bad object` ở các test tham chiếu SHA lịch sử. Đây là
điều kiện môi trường, đã xử lý, KHÔNG phải finding.

## Frozen Contract Có Bị Nới Lỏng Giữa Freeze Và Implementation Không?

Reviewer đọc nguyên văn `git diff c12c563..a36f959 -- docs/tasks/TASK-PRA-003-*.md`.

**KHÔNG bị nới lỏng.** Mọi thay đổi nằm ở trường ghi bằng chứng
(`Status: NOT_TESTED → PASS`, `Executed By`, `Timestamp`, khối "Kết quả S096")
và bảng touch-area cuối file. Không một dòng `Yêu cầu:`, không một oracle
`O-A…O-K`, không một Owner Decision `D1–D3` nào bị sửa chữ.

`CHECK-PRA003-07` và `CHECK-PRA003-12` được implementer giữ đúng `NOT_TESTED` —
không tự chấm check thuộc thẩm quyền khác.

`tests/fixtures/golden/**` KHÔNG bị sửa một byte — oracle độc lập còn nguyên.

## Cách Reviewer Tự Chứng Minh (không mượn test của implementer)

1. **Recompute bằng SQL THÔ.** Nạp fixture golden qua đường production, rồi
   tính lại `lines/orders/quantity/sales/status` bằng một câu SQL viết tay
   trong Python — KHÔNG gọi `analytics_queries`. Sau đó mới so ba nguồn:
   raw SQL ↔ `expected/period_2026_01.json` ↔ implementation. **Cả ba KHỚP.**
2. **Khẳng định do reviewer tự viết.** Bộ kiểm tra ngữ nghĩa
   (no-double-count, `NULL ≠ 0`, KPI chỉ AUTO, đối soát nhân viên, biên năm,
   thiếu `sale_date`) dùng hàm dựng dòng của `TASK-PRA-002`, nhưng mọi
   `assert` là của reviewer.
3. **PII dò bằng GIÁ TRỊ THẬT.** Đọc ngược `imei` / `note_raw` / `employee_raw`
   / `product_raw` / `source_profit` từ DB rồi tìm từng giá trị đó trong body
   trang — không dò bằng từ khoá.
4. **Chứng minh cấu trúc.** Đọc `tools/db/schema.py` để chứng minh tính chất
   ở cấp ràng buộc DB thay vì cấp câu truy vấn.

## Kết Quả Rút Gọn

```
oracle golden (3 nguồn KHỚP): 351 dòng · 254 đơn · SL 407 · 3.562.310.000
                              AUTO 2 / PENDING 349 · auto+review = 254 = orders
test  : PRA-003 67 · Golden 58 passed 2 skipped · legacy 34 · PRA-002 vertical 12
        FULL SUITE 1873 passed, 11 skipped (exit 0)
budget: Python 284 · template 191 · CSS 16 — reviewer TÁI LẬP ĐÚNG số của S096
scope : 0 vi phạm Scope Lock · schema/migration/index/dependency/config = 0
```

## Finding

```
BLOCKING     : 0
NON_BLOCKING : FIND-PRA003-01  CONTRACT_MISMATCH
               FIND-PRA003-02  EVIDENCE_DEFECT
               FIND-PRA003-03  HARDENING
repair cycle : 0 / 1 — KHÔNG mở (không finding nào đe doạ 5 điều mục 14)
```

### FIND-PRA003-01 — quyết định

Reviewer chạy CẢ HAI đường trên CÙNG fixture golden:

```
run_import() TRẦN (build_expected.py:261) : {'Pending': 351}
run_import_production (app/composition.py:72): {'OWNER_MANUAL_LEGACY_CONFIRMATION': 2,
                                               'Pending': 349}
trạng thái ĐÃ PERSIST                      : AUTO = 2, PENDING = 349
```

Chuỗi ingest thật: upload web → `run_owner_report` (`app/owner_usability.py:170`)
→ `demo.run_demo` → `run_import_production` (`app/demo.py:92`) →
`history_writer.write_run_history`. **Mọi dòng từng được persist đều đi qua
đường production**; đường trần không bao giờ sinh dữ liệu mà PRA-003 đọc.

Vậy: (A) phân biệt ĐÚNG SỰ THẬT; (B) `2/351` là hành vi ĐÚNG của đường
production; (C) O-C đòi **tính chất an toàn** ("lợi nhuận thiếu hiện `—`, không
hiện `0`") — cặp số `0/351` chỉ là minh hoạ, và nó dẫn xuất từ một tiền đề
(`{Pending: 351}`) chỉ đúng cho đường trần; (D) implementation **KHÔNG** làm
yếu oracle: fixture không sửa, test còn assert ngược lại rằng golden JSON vẫn
đọc ra `{Pending: 351}`, và tính chất O-C được chứng minh riêng trên dữ liệu có
kiểm soát.

`PHÂN LOẠI = CONTRACT_MISMATCH`, NON_BLOCKING. Khắc phục đúng là **sửa TÀI
LIỆU O-C**, không sửa mã. Reviewer KHÔNG repair trong phiên review.

## Quyết Định

```
FINAL_DECISION  = ACCEPT_WITH_NON_BLOCKING_FINDINGS
CHECK-PRA003-12 = PASS
TASK-PRA-003    = IN_PROGRESS
NEXT            = Controlled Integration
```

## Việc Cần Theo Dõi Tiếp

1. **Controlled Integration** nhánh review vào canonical
   `claude/extract-upload-repo-gq2ws4`.
2. `CHECK-PRA003-07` — Owner nghiệm thu real vertical Tháng 09/2026 trên
   production sau deploy. Ngoài thẩm quyền reviewer.
3. Một lượt **DOCS** (không phải repair) gộp `FIND-PRA003-01` +
   `FIND-PRA003-02`: sửa minh hoạ số học của O-C cho khớp đường production, và
   dọn 1 trailing whitespace ở `docs/sessions/S094-…md:341`.
4. `FIND-PRA003-03` giữ ở `HARDENING` với RE-TRIGGER CONDITION đã ghi trong
   artifact review.

## Ràng Buộc Đã Tuân Thủ

Phiên này **KHÔNG**: sửa mã production · repair finding · sửa Tracking · sửa
schema/migration · sửa hạ tầng · mở PRA-004/PRA-005 · thêm tính năng · refactor
· repair REM-T06 · đổi Owner decision đã freeze · rerun production acceptance ·
đánh dấu CHECK-07 PASS · đánh dấu task DONE · tích hợp canonical.
