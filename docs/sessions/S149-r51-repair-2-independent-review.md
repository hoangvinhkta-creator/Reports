# S149 — Independent Review cho `R5.1 REPAIR-2`

Ngày: 2026-09-09
Task Mode: `MAJOR` (phiên review, không phải phiên triển khai)
Kết luận: **`ACCEPT_WITH_RECORDED_RISK`**

Phiên chỉ ĐỌC, CHẠY, TẠO PROBE và KIỂM. **Không sửa một dòng mã sản phẩm nào,
không merge, không deploy, không tự đánh dấu Owner Acceptance.**

Bản ghi đầy đủ (bằng chứng nguyên văn từng chuỗi, kèm lệnh tái lập):
`docs/reviews/R5-1-REPAIR-2-INDEPENDENT-REVIEW-RECORD.md`.

---

## 1. Đối tượng review

```text
Repo    Reports
Nhánh   claude/r51-repair-2-integration
HEAD    98778bc795dea62e78a23b4afa65c3cee304c890

Nền     Reports   claude/extract-upload-repo-gq2ws4 @ 05f2b443e66ee4702d03c003d5f1f960b5765f8d
        Tracking  main                              @ KHÔNG ĐỔI (diff rỗng)
```

Preflight: HEAD khớp đúng mục tiêu; nền là ancestor của HEAD (`merge-base` =
chính nền); worktree CLEAN; ba commit trong lineage `REPAIR-2` + `S148`.
`git diff --check` sạch.

`branch_authority_check.sh` xác nhận nền đúng là nhánh mặc định thật trên
origin và `WORKTREE = CLEAN`; script trả `STOP` chỉ vì **nhánh review cục bộ
chưa có upstream** — trạng thái của nhánh review phiên này, không phải của nội
dung được review.

**Diff KHÔNG mang bất kỳ phần nào của `R6`.** 14 file thay đổi, không một
module/route/template/test/tài liệu `R6` nào. Mọi lần chuỗi `R6` xuất hiện đều
nằm trong văn xuôi tài liệu phiên giải thích việc tách nhánh, hoặc trong đoạn
Evidence trích nguyên văn lịch sử. Repo `Tracking` KHÔNG bị đụng tới — nên
smoke xuyên repo chạy trên mã producer Tracking NGUYÊN BẢN.

---

## 2. Kết luận và finding

```text
REPAIR_REQUIRED     0
ACCEPTED_RISK mới   2   AR-R5.1R2-01, AR-R5.1R2-02
Lỗi BASELINE tách   2   1 bài pytest (clone nông) + 4 reference integrity
Repair cycle tiêu   0   (phiên review không tiêu cycle)
```

`AR-R5.1R2-01` — `NO_SNAPSHOT` không kích hoạt cảnh báo "CŨ một phần". Cần HAI
lỗi liên tiếp; và phiên đã ĐO rằng một lần chạy không có capture danh mục
thất bại với HTTP 400 TRƯỚC bước làm mới bản chiếu, nên ca này gần như không
đạt tới được trên nhánh live. Chỉ ảnh hưởng NHÃN; dòng hiện MÃ Tracking + `—`,
KHÔNG phải tên sổ kế toán, nên triệu chứng production ban đầu KHÔNG tái diễn.

`AR-R5.1R2-02` — ghi bản chiếu/trạng thái không nguyên tử. Phiên đã đo ca file
rách: hỏng theo hướng AN TOÀN — `read()` trả `{}`, cảnh báo tự hiện, tiền
không đổi.

Cả hai: xác suất thấp × tác động chỉ-nhãn × nhân viên dễ phát hiện →
`ACCEPTED_RISK`, không mở rộng phạm vi.

---

## 3. Sáu chuỗi đã kiểm độc lập

```text
1 Luồng chính          PASS  producer Tracking THẬT → POST /run → tab Nhân
                             viên, KHÔNG mở popover: Mặt hàng = model_label
                             ngắn, Hãng = brand, Nhóm hàng = category_label
2 Projection trống     PASS  tự dựng lại từ capture của CHÍNH run;
                             số lần pull Tracking = 1 (đo trực tiếp)
3 Projection cũ 1 phần PASS  NO_METADATA và WRITE_FAILED đều ra cảnh báo
                             kind="cu", câu chữ phân biệt rõ với "chưa phân
                             loại"; nhãn cũ còn nguyên
4 Hàng rào dữ liệu     PASS  unconfirmed/conflict/stale target/OUT_OF_CATALOG
                             giữ tên gốc hoặc mã + "—"; không suy diễn từ tên
                             kế toán; không lộ metadata sang dòng khác
5 Bất biến nghiệp vụ   PASS  trước/sau khi xoá bản chiếu: doanh thu, lợi
                             nhuận, số lượng, số dòng GIỐNG HỆT; capture đời
                             cũ không crash và KHÔNG xoá nhãn đã có
6 Độ bền / vận hành    PASS  .gitignore che cả hai file runtime;
                             evidence có catalog_display {written,rows,reason};
                             status hỏng ⟹ im lặng TRUNG TÍNH, không crash
```

Probe của phiên review được viết ĐỘC LẬP (3 file, 19 assertion nhóm), không
dùng lại assertion của tác giả — chỉ dùng lại scaffolding dựng app.

---

## 4. Bằng chứng thực thi (E1)

```text
Executed By: phiên Independent Review S149
Timestamp:   2026-09-09
Evidence Level: E1

$ .venv/bin/python -m pytest -q tests/test_r51_repair2_run_refreshes_projection.py
15 passed in 3.82s

$ .venv/bin/python -m pytest -q          (test web + identity + presentation)
180 passed in 3.34s

$ .venv/bin/python -m pytest -q          (full)
3275 passed, 11 skipped in 175.14s (0:02:55)

$ .venv/bin/python scripts/r51_crossrepo_smoke.py --tracking ../Tracking
KẾT QUẢ SMOKE: 83 PASS, 0 FAIL

$ git diff --check 05f2b44..98778bc
(rỗng)

GOVERNANCE STRUCTURE: PASS
PROJECT STATE:        PASS
EVIDENCE VALIDATION:  PASS
TASK COMPLETION:      PASS
REFERENCE INTEGRITY:  FAIL — 4 reference, CÓ SẴN TỪ NỀN (xem §5)
```

Full regression TÁI LẬP CHÍNH XÁC con số `S148` ghi (`3275 passed, 11
skipped`).

---

## 5. Hai lỗi BASELINE tách khỏi nội dung review

1. `tests/test_105d_boundaries.py::TestG25GoldenBaselineUnchanged` đỏ ở lần
   chạy đầu (`fatal: bad object 740f396...`) vì clone của môi trường review là
   clone NÔNG. File test không nằm trong diff; sau `git fetch --unshallow` bài
   chạy XANH. Không phải lỗi của `REPAIR-2`.

2. `validate_reference_integrity` FAIL với 4 reference. Chạy validator trên
   ĐÚNG nền `05f2b44` (worktree riêng) cho ra **y hệt 4 reference đó**, trong
   các file không thuộc diff. 7 file `.md` mới của `REPAIR-2` KHÔNG thêm một
   reference hỏng nào. Có sẵn từ nền.

---

## 6. Bàn giao — việc còn lại KHÔNG thuộc phiên này

- **Owner Acceptance**: chưa đánh dấu. Thuộc Owner.
- **Ngân sách review**: `PROJECT/REVIEW_BUDGET_LEDGER.md` ghi mục "REPAIR-2 production
  (`S146`) — CẦN XÁC NHẬN ngân sách" và cố ý KHÔNG tự tiêu/tự miễn một repair
  cycle. Phiên review này cũng không giả định theo chiều nào — quyết định
  thuộc Owner/reviewer theo `V4.1` §2–§3.
- **Merge / deploy**: chưa thực hiện, và không thuộc phiên review.
- **Hai `ACCEPTED_RISK` mới** (`AR-R5.1R2-01`, `AR-R5.1R2-02`) cần được Owner
  chuẩn y hoặc bác khi nghiệm thu.
