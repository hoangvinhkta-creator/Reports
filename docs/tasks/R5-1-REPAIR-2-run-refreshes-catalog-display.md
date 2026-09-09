# R5.1 REPAIR-2 — luồng chạy báo cáo phải làm mới bản chiếu hiển thị

## Metadata

Status:
IMPLEMENTED

Current Status Reason:
Lỗi LUỒNG CHÍNH trên production đã sửa: `POST /run` nay ghi/cập nhật bản chiếu
`catalog_display` từ ĐÚNG capture danh mục Tracking của chính lần chạy đó, nên
tab Nhân viên hiện `model_label` ngắn và `brand` cho các dòng đã CONFIRMED mà
Owner KHÔNG phải mở bảng chọn phân loại.

`CHECK-R51R2-01` … `CHECK-R51R2-14` PASS (E1, bằng chứng nguyên văn ở
`docs/sessions/S146-r51-repair-2-run-refreshes-projection.md` §4).

**Vòng 2 (`S147`, `DEC-209`).** Trước khi mở Independent Review, Owner chỉ thị
đóng thêm ca "bản chiếu đã có dữ liệu CŨ, lần chạy KẾ TIẾP không làm mới được
nó" — khác ca "vắng hoàn toàn" mà vòng 1 đã đóng. `catalog_display.write()`
nay ghi lại LỊCH SỬ của chính lần ghi gần nhất (`last_write_status()`), và tab
Nhân viên hiện cảnh báo hình dạng thứ hai (`kind="cu"`) khi có bằng chứng lần
ghi gần nhất `NO_METADATA`/`WRITE_FAILED` VÀ có mã CONFIRMED thiếu nhãn.
`CHECK-R51R2-17` … `CHECK-R51R2-19` PASS (E1, bằng chứng nguyên văn ở
`docs/sessions/S147-r51-repair-2-stale-projection-warning.md` §3–§5).

`CHECK-R51R2-15` (Independent Review của REPAIR-2, bao CẢ HAI vòng) và
`CHECK-R51R2-16` (Owner nghiệm thu lại trên production) `NOT_TESTED` — phiên
repair KHÔNG tự đóng.

`CHECK-R51-26` (Owner nghiệm thu `R5.1` trên production) VẪN `NOT_TESTED`. Nó
là chính check mà lỗi này đã CHẶN: Owner không thể nghiệm thu một cột luôn hiện
dấu gạch. Sau `REPAIR-2` nó nghiệm thu được, nhưng vẫn chỉ Owner đóng nó.

Phase:
PHASE-01 — Engine tính toán

Task Mode:
MAJOR (repair lỗi production)

Difficulty:
2/5

Risk:
2/5

Blast Radius:
2/5 (`V4.1` §4 — chấm theo FAILURE PATH). Failure path của `REPAIR-2`:

```text
capture danh mục Tracking của lần chạy → catalog_display (bản chiếu NHÃN)
                                       → 3 ô hiển thị trên bảng kê tab Nhân viên
```

Nó DỪNG ở đó, và ba tính chất CẤU TẠO giữ nó không đi xa hơn:

1. **Bản chiếu chỉ mang NHÃN.** Không đường tính tiền nào đọc nó.
   `CHECK-R51R2-09` đo trực tiếp: xoá bản chiếu rồi so lại doanh thu, lợi
   nhuận, SL tính KPI, số đơn và số dòng — giống hệt từng đồng.
2. **Không mở thêm dòng nào được nhận nhãn.** Phép chặn theo trạng thái mapping
   ở `workspace_presentation._catalog_field` KHÔNG bị chạm; `CHECK-R51R2-07`
   đo rằng một dòng chưa xác nhận vẫn giữ tên thô và `—` KỂ CẢ khi bản chiếu
   trên đĩa đã có nhãn cho mã đó.
3. **Không lời gọi Tracking nào thêm.** `CHECK-R51R2-05` đếm số lần
   `pull_live_captures` được gọi trong một lần chạy: đúng 1.

Nó KHÔNG phải `1/5` vì một nhãn sai gắn vào dòng sai sẽ dẫn người đọc tới kết
luận sai về cơ cấu hàng bán — và từ `R6`, ba trường ấy là khoá gộp của bảng cơ
cấu và bảng giỏ hàng.

Effective Risk:
LOW (Blast Radius quyết định — `V4.1` §4.1; không viện dẫn Golden để hạ bậc)

Project Profile:
PRODUCT

Review Budget lineage:
`R5.1` thuộc root lineage `R5`, và lineage ấy đã HẾT ngân sách review
(`2 allowed / 2 used / 0 remaining`). **Phiên này KHÔNG tự tiêu và KHÔNG tự
miễn một repair cycle** — xem §7 và `PROJECT/REVIEW_BUDGET_LEDGER.md`. Đây là
một câu hỏi governance cần Owner/reviewer xác nhận, không phải một điều phiên
repair được tự quyết.

Owner Authority:
Owner báo lỗi đã xác minh trên production (cột `Hãng` là `—`, cột `Mặt hàng`
còn tên dài) và chỉ thị: *"Đây là lỗi luồng chính, không phải accepted risk."*
Quyết định chiến thuật: `PROJECT/PROJECT_DECISIONS.md` → `DEC-208`.

---

## 1. Nguyên nhân gốc

```text
app/web/server.py:_tracking_snapshot()   ← chỗ DUY NHẤT ghi catalog_display
                                            (chỉ chạy khi Owner mở bảng chọn)
app/web/server.py:run_report()           ← luồng CHÍNH, KHÔNG ghi gì
```

Tầng trình bày ĐÚNG từ `R5` §5: `workspace_presentation._catalog_field` tra bản
chiếu và chặn đúng các trạng thái chưa xác nhận. Tầng hợp đồng ĐÚNG từ `R5.1`:
capture Tracking chở đủ ba trường. Chỉ MỐI NỐI giữa hai tầng ấy trên luồng
chính là không tồn tại.

Trên đĩa ephemeral của Render, bản chiếu biến mất sau mỗi deploy và không có gì
dựng lại nó — nên trạng thái "chưa có nhãn" là VĨNH VIỄN, không phải tạm.

## 2. Scope Lock

TRONG phạm vi:

```text
app/web/catalog_display.py     `write()` trả `WriteResult` thay cho `None`;
                               ba mã lý do đóng; `MISSING_PROJECTION_NOTE`
app/web/server.py              `_refresh_catalog_display()` MỚI;
                               `run_report` gọi nó trên đường THÀNH CÔNG;
                               `_catalog_projection_warning()` MỚI cho tab NV
app/web/templates/kinh_doanh_nhan_vien.html   một dòng cảnh báo (notice)
scripts/r51_crossrepo_smoke.py §5 MỚI — upload/run THẬT; §6 MỚI (vòng 2) —
                               bản chiếu CŨ một phần
tests/test_r51_repair2_run_refreshes_projection.py   MỚI (12 bài; +3 vòng 2
                               → 15 bài)
tests/test_web_server.py       một assertion mở rộng theo bằng chứng mới
```

Vòng 2 (`DEC-209`) mở rộng scope lock THÊM đúng ba chỗ, không chạm gì khác:
`catalog_display.py` (`_status_path`/`_record_status`/`_finish`/`last_write_
status`/`stale_metadata_note`), `server.py` (`_catalog_projection_warning()`
hình dạng 2), `kinh_doanh_nhan_vien.html` (`data-kind`).

NGOÀI phạm vi (và không file nào bị chạm):

```text
app/modules/pricing/**        MIN theo ngày bán, giá nhập
app/modules/profit/**  app/modules/kpi/**
app/web/period_lock.py        chốt kỳ, fingerprint
app/web/business_store.py  app/web/business_queries.py  app/web/business_service.py
app/modules/reporting/**      mọi ngữ nghĩa nghiệp vụ đã freeze
app/web/workspace_presentation.py   quy tắc hiển thị/phép chặn của R5 §5
app/modules/exporting/**      export
tools/db/migrations/**        KHÔNG migration mới
Tracking (toàn bộ repo)       KHÔNG đổi một dòng code nào
```

## 3. Checklist

| Check | Nội dung | Trạng thái | Evidence Level |
|---|---|---|---|
| `CHECK-R51R2-01` | Run THÀNH CÔNG ghi bản chiếu (trước đó không tồn tại) | PASS | E1 |
| `CHECK-R51R2-02` | Tab Nhân viên hiện `55Q6FA` + `Samsung` KHÔNG cần mở bảng chọn | PASS | E1 |
| `CHECK-R51R2-03` | Tên dài trên sổ kế toán BIẾN KHỎI dòng đã xác nhận | PASS | E1 |
| `CHECK-R51R2-04` | Lần chạy SAU làm mới bản chiếu tại chỗ (đổi ngành hàng ⟹ nhãn đổi) | PASS | E1 |
| `CHECK-R51R2-05` | ĐÚNG MỘT lần gọi Tracking cho mỗi lần chạy | PASS | E1 |
| `CHECK-R51R2-06` | Capture ĐỜI CŨ (thiếu ba trường) ⟹ fallback mã Tracking + `—`, không crash | PASS | E1 |
| `CHECK-R51R2-07` | Mapping CHƯA xác nhận ⟹ tên thô + `—`, dù bản chiếu ĐÃ có nhãn | PASS | E1 |
| `CHECK-R51R2-08` | Ghi bản chiếu thất bại ⟹ `tracking_evidence` NÓI RA lý do | PASS | E1 |
| `CHECK-R51R2-09` | Bản chiếu có/không KHÔNG đổi một đồng nào của kỳ | PASS | E1 |
| `CHECK-R51R2-10` | Ghi thất bại vẫn để run THÀNH CÔNG | PASS | E1 |
| `CHECK-R51R2-11` | Mất bản chiếu + có mapping đã xác nhận ⟹ tab NV CẢNH BÁO | PASS | E1 |
| `CHECK-R51R2-12` | Bản chiếu lành ⟹ KHÔNG có cảnh báo | PASS | E1 |
| `CHECK-R51R2-13` | Smoke xuyên hai repo: producer Tracking THẬT → upload/run → bảng NV | PASS | E1 |
| `CHECK-R51R2-14` | Full regression `R1`–`R6` xanh; validator = baseline; `git diff --check` sạch | PASS | E1 |
| `CHECK-R51R2-17` | Vòng 2: bản chiếu CŨ + mã MỚI xác nhận + `NO_METADATA` ⟹ cảnh báo `kind="cu"`, tên/mapping/tiền KHÔNG đổi | PASS | E1 |
| `CHECK-R51R2-18` | Vòng 2: cùng ca trên nhưng `WRITE_FAILED` ⟹ cùng cảnh báo | PASS | E1 |
| `CHECK-R51R2-19` | Vòng 2: làm mới ĐỦ cho mọi mã ⟹ KHÔNG cảnh báo (không over-fire) | PASS | E1 |
| `CHECK-R51R2-15` | Independent Review của `REPAIR-2` (bao CẢ HAI vòng) | NOT_TESTED | — |
| `CHECK-R51R2-16` | Owner nghiệm thu lại trên production | NOT_TESTED | — |

Bằng chứng nguyên văn:
`docs/sessions/S146-r51-repair-2-run-refreshes-projection.md` §4 (vòng 1) và
`docs/sessions/S147-r51-repair-2-stale-projection-warning.md` §3–§5 (vòng 2).

## 4. Exit Criteria

```text
[x] Luồng upload/run ghi bản chiếu từ capture CỦA CHÍNH lần chạy
[x] Không gọi Tracking lần thứ hai chỉ để hiển thị
[x] CONFIRMED + metadata ⟹ model ngắn · brand · category
[x] Chưa xác nhận / conflict / stale / OUT_OF_CATALOG / thiếu metadata ⟹ tên gốc + "—"
[x] Ghi thất bại ⟹ cảnh báo trong run evidence VÀ trên UI, không im lặng
[x] Nghiệp vụ R1–R6 không đổi một đồng
[x] Tương thích capture cũ, fallback an toàn, không crash
[x] Test qua route web thật + smoke xuyên hai repo
[x] Vòng 2: bản chiếu CŨ một phần ⟹ cảnh báo (kind="cu"), không đổi tên
    hàng/mapping/giá MIN/lợi nhuận/tổng tiền
[ ] Independent Review (CHECK-R51R2-15)
[ ] Owner nghiệm thu lại trên production (CHECK-R51R2-16)
```

## 5. Rủi ro đã chấp nhận

`ACCEPTED_RISK R5.1R2-01` — **Giữa hai lần chạy, mất đĩa vẫn tạm mất nhãn.**
Bản chiếu vẫn sống trên đĩa ephemeral. Nếu container bị thay giữa hai lần chạy,
nhãn tạm mất cho tới lần chạy kế tiếp.

*Điều kiện kích hoạt:* Owner thấy cảnh báo bản chiếu xuất hiện mà một lần chạy
mới KHÔNG làm nó biến mất.
*Vì sao chấp nhận:* khác hẳn `AR-R5.1-04` (đã đóng), trạng thái này nay **tự
thoát ra** ở lần chạy kế tiếp và **có cảnh báo nói ra**. Đưa bản chiếu vào một
kho bền là một quyết định về hạ tầng lưu trữ, không phải một bước của repair
này.

## 6. Escalation — trigger ĐÃ MET, ghi lại theo protocol

`governance/core/ESCALATION_PROTOCOL.md` liệt kê: *"hành vi ở production khác
biệt đáng kể so với các giả định đã được tài liệu hóa"*. Trigger ấy ĐÃ MET —
`R5.1` giả định bản chiếu sẽ được làm mới bởi "lần capture danh mục mới đầu
tiên", và production hành xử khác.

Hành động bắt buộc đã thực hiện: bảo toàn evidence (bằng chứng production của
Owner + baseline đo trước khi sửa), ghi lại blocker, **rà soát nguyên nhân gốc**
(§1 — một mối nối duy nhất, xác định được bằng đọc mã, không phải suy đoán), và
cập nhật kế hoạch (file này + `DEC-208`).

Escalate agent tier KHÔNG cần thiết: nguyên nhân gốc xác định chính xác, bản sửa
là một mối nối hẹp, và không có lần vá suy đoán nào. Điều CẦN escalate là câu
hỏi ngân sách ở §7.

## 7. Ngân sách review — CẦN Owner/reviewer xác nhận

```text
lineage R5 (chứa R5.1)   2 allowed / 2 used / 0 remaining
```

Phiên này **KHÔNG tự tiêu** và **KHÔNG tự miễn** một repair cycle. Lập luận của
phiên, để Owner/reviewer bác hoặc chuẩn y:

- Ngân sách repair cycle của `V4.1` §2–§3 điều tiết việc đưa MỘT task qua
  Independent Review: nó đếm các lần sửa sau một vòng review ra finding
  `BLOCKING`.
- `REPAIR-2` KHÔNG đến từ một vòng review. `CHECK-R51-25` đã `PASS` từ `S139`,
  và defect này do **Owner phát hiện trên production SAU khi merge**.
- Nếu mọi defect production sau nghiệm thu đều tiêu ngân sách review, thì một
  tính năng đã merge sẽ không sửa được nữa khi lineage hết ngân sách — đó không
  phải điều `V4.1` §3 nói tới.

Vì vậy phiên này ghi `REPAIR-2` là **PRODUCTION DEFECT REPAIR**, tách khỏi
review repair cycle, và **đánh dấu cần xác nhận**. Nếu Owner/reviewer kết luận
nó PHẢI tiêu một cycle, lineage `R5` vượt ngân sách và phải escalate theo
`ESCALATION_PROTOCOL` — quyết định ấy KHÔNG thuộc phiên repair.

## 8. Điều kiện merge/deploy

Phiên này KHÔNG merge, KHÔNG deploy. Sau `REPAIR-2`:

1. `CHECK-R51R2-15` (Independent Review của `REPAIR-2`) → `PASS`;
2. câu hỏi ngân sách §7 được Owner/reviewer trả lời;
3. rồi merge, deploy, và Owner nghiệm thu lại `CHECK-R51-26` +
   `CHECK-R51R2-16` trên production.
