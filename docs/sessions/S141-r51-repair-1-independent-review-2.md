# S141 — Independent Review vòng 2 cho `R5.1 REPAIR-1`

Ngày: 2026-09-09
Task Mode: `MAJOR` (phiên review, không phải phiên triển khai)
Kết luận: **`ACCEPT_WITH_RECORDED_RISK`**

Phiên chỉ ĐỌC, CHẠY, TẠO PROBE và KIỂM. **Không sửa một dòng mã sản phẩm nào,
không merge, không deploy, không triển khai `R6`, không tự đánh dấu Owner
Acceptance.**

Bản ghi đầy đủ (bằng chứng nguyên văn từng chuỗi):
`docs/reviews/R5-1-REPAIR-1-INDEPENDENT-REVIEW-2-RECORD.md`.

---

## 1. Đối tượng review

```text
Tracking  11a199b222ed1771558cefcdf664aad9de64cfa9
Reports   83b1e07c44b186fffaf1b71e40693485741f32eb

Nền   Tracking  main                              @ 918183c  (KHÔNG đổi từ S140)
      Reports   claude/extract-upload-repo-gq2ws4 @ 3b35b7a  (KHÔNG đổi từ S140)
```

Preflight: cả hai HEAD là hậu duệ của nền; không commit lạ ngoài lineage
`R5.1` + `REPAIR-1`; worktree cả hai repo CLEAN.
`branch_authority_check.sh` trả `STOP` vì **nhánh review chưa có upstream** —
trạng thái của nhánh review, không phải của nội dung được review (`HEAD_SHA`
khớp mục tiêu, `WORKTREE = CLEAN`, `DEFAULT_TIP` khớp SHA `S140` ghi).

---

## 2. Kết luận và finding

```text
REPAIR_REQUIRED          0
ACCEPTED_RISK mới        2   AR-R5.1R1-04, AR-R5.1R1-05
Đính chính tài liệu      2   COR-R5.1R1-01, COR-R5.1R1-02
Cần Owner quyết          1   OWNER_DECISION_REQUIRED — alias taxonomy
Lỗi BASELINE tách ra     2   1 bài pytest (clone nông) + 4 reference integrity

CHECK-R51R1-17  NOT_TESTED → PASS (E1)
CHECK-R51-26    VẪN NOT_TESTED
Repair cycle tiêu  0   (lineage R5 giữ 2 allowed / 2 used / 0 remaining)
```

`AR-R5.1R1-04` — nhắc lại cùng một nhóm trong `cat` ra `null`: `"Tivi TV"`,
`"Máy lạnh Điều hoà"`, `"Nồi cơm Nồi cơm điện"`. Hai đoạn khớp cùng độ dài trỏ
về cùng canonical, `nhat[0]` lấy đoạn đầu, từ của đoạn kia rơi vào phép kiểm
"còn lại phải là hãng". Hiếm, chỉ giảm độ phủ, hiện rõ thành `"—"`.

`AR-R5.1R1-05` — ngành hàng GHÉP ra `null`, và có ca THẬT: `"Máy giặt sấy"`.
Đơn golden `BH62439` có `"Máy Giặt Sấy LG"`. Từ điển có `"Máy giặt"` và
`"Máy sấy"` nhưng không có mục ghép. Quan trọng: hỏng theo hướng AN TOÀN — nó
KHÔNG xếp nhầm vào bucket `"Máy giặt"`. Sửa đúng chỗ: thêm một dòng vào `NHOM`.

`COR-R5.1R1-01` — hai chú thích mô tả LUẬT CŨ còn lại trong mã Reports
(`app/web/catalog_display.py:17-18`, `tools/tracking/capture_tracking_catalog.py:134-135`
đều nói "lọc hình dạng"/"danh sách trắng hình dạng"), nay mâu thuẫn `DEC-205`.
Chú thích thôi — 0 tác động hành vi. Phiên nào chạm Reports kế tiếp nên sửa.

`COR-R5.1R1-02` — bảng quan hệ của `DEC-205` ghi `DEC-204 §5 → GIỮ NGUYÊN`,
nhưng `§5` còn câu *"Gộp tên đồng nghĩa khác: KHÔNG làm"* mà `DEC-205` §4 đã
đảo. Lập luận đảo có tường minh ở §4 và task §6 — chỉ dòng tóm tắt là thiếu
chính xác. KHÔNG sửa `DEC-204` (artifact lịch sử).

---

## 3. Kiểm đã chạy (không tin số trong bàn giao `S140`)

```text
Tracking  npm test        62 bộ · 2850 đạt · 0 hỏng · 2 bỏ qua   (khớp S140)
          npm run build   OK (dist, 658 KB → 411 KB)

Reports   pytest tests/test_r51_category_label.py   26 passed
          pytest -q (toàn bộ)   1 failed, 3258 passed, 11 skipped
                                bài đỏ = BASELINE, xem mục 5
          smoke của dự án       58 PASS / 0 FAIL   (khớp S140)

Probe ĐỘC LẬP của phiên (không dùng bộ smoke của dự án)
          probe 1  nhomCua() qua module THẬT + fuzz 200k    (xem AR-R5.1R1-04)
          probe 2  ranh giới chieuBoard() + fuzz 50k dòng   21/21 ok
          probe 3  producer thật → capture thật → Flask thật 22/22 ok
          probe 4  stale target + phạm vi lộ diện            9/9 ok

Governance  structure PASS · project_state PASS · evidence PASS
            task_completion PASS
            reference_integrity 4 reference — BASELINE, xem mục 5
```

Phiên chạy `nhomCua()`/`chieuBoard()` bằng cách **import module thật**, không
dùng lối `new Function` + trích đoạn regex mà producer của `S140` dùng. Hai
đường cho kết quả TRÙNG KHỚP — phép trích đoạn của producer được xác nhận độc
lập là không trượt.

**Phép đo mạnh nhất, và nó mạnh hơn phép đo bàn giao.** `S140` kiểm 4 ô tổng
tiền. Phiên này chạy CÙNG một trang HAI lần — bản chiếu CÓ `category_label` vs
bản chiếu bị TƯỚC `category_label` — rồi so TOÀN BỘ HTML:

```text
ok   A và B KHÁC nhau khi còn ô nhóm hàng
ok   A và B GIỐNG HỆT sau khi che riêng các phần tử `line-category`
```

Doanh thu, MIN, giá nhập, lợi nhuận, độ phủ, mọi ô còn lại: **giống nhau tới
từng ký tự**. Và `evidence_fingerprint()` cùng `period_lock` không nhắc
`category_label` ở đâu cả.

---

## 4. Điều đã xác minh theo từng điểm của brief

```text
1  đầu ra ∈ NHOM ∪ {null}      250 000 mẫu fuzz, 0 vi phạm; nhãn là hằng lấy
                               từ NHOM, không phải lát cắt của cat
   6 chuỗi bẩn bắt buộc        cả 6 ra null
   hãng mới / hai hãng /
   category không ở đầu /
   đoạn dài nhất / sentinel /
   cat rỗng                    tất cả đúng như hợp đồng §4.6

2  chieuBoard() đúng 5 khoá    12 loại dữ liệu nhạy cảm ném vào, 0 loại đi ra
   artifact R5 cũ              vẫn load COMPLETE, category_label = None
   Reports không taxonomy      không mục từ điển nào; không đọc product_raw;
                               category_label vắng mặt ở tầng export/report/KPI
   conflict/stale/OOC/chưa     cả bốn ra "—", chặn bằng HAI lớp độc lập

3  kiểm chứng                  xem mục 3
4  taxonomy                    xem mục 6
```

---

## 5. Lỗi BASELINE — tách rõ khỏi lỗi mới

**`pytest` đỏ một bài, và nó là BASELINE.**

```text
FAILED tests/test_105d_boundaries.py::TestG25GoldenBaselineUnchanged
       ::test_protected_golden_artifacts_match_the_task_105e_review_base
E  AssertionError: fatal: bad object 740f396acb11cf279f303f09ea22dffd0ca95462
```

Container này clone NÔNG (`is-shallow-repository = true`, 88 commit), nên
object base của bài đó không có. Chứng minh bằng thực nghiệm — dựng worktree
trên `3b35b7a` (nền, TRƯỚC cả `R5.1` lẫn `REPAIR-1`) và chạy đúng bài ấy:
**đỏ Y HỆT**. Khác biệt MÔI TRƯỜNG, không phải hồi quy, và không phải bằng
chứng `S140` khai sai: `3258 passed + 1 failed` = `3259 passed` của `S140`,
cùng một tập bài.

**`REFERENCE INTEGRITY: FAIL` — cả 4 đều BASELINE.** Không file nào trong số
đó (`S136-r5-integration.md`, `TASK-REM-T06` ×3) nằm trong diff
`dd7cd04..HEAD`. Trùng khớp đúng 4 finding `S139`/`S140` đã ghi là baseline.

---

## 6. `OWNER_DECISION_REQUIRED` — alias taxonomy

Đây là **quyết định bucket báo cáo, không phải thay đổi tiền** (đã chứng minh
ở mục 3). Phiên KHÔNG coi đó là lỗi code và KHÔNG sửa từ điển.

```text
Máy lạnh -> Điều hoà   bằng chứng dữ liệu MẠNH; thẩm quyền Owner chỉ có lời
                       dẫn của phiên triển khai (brief không phải artifact
                       trong repo); CHECK-R51R1-08 có canh
TV -> Tivi             bằng chứng YẾU — dấu vết in-repo duy nhất là
                       Tracking/public/kpi-demo.js `any:["tivi","tv"]`, một
                       cấu hình KPI, không phải giá trị `cat`; không check nào canh
Ti vi -> Tivi          KHÔNG có bằng chứng in-repo nào; không check nào canh
```

Bằng chứng dữ liệu tìm được độc lập: chín tiền tố ngành hàng phân biệt được
trong dữ liệu đã ghi của Reports — **cả chín đều có trong từ điển 13 mục**, nên
mệnh đề "từ điển được ĐỌC RA từ dữ liệu" (`DEC-205` §3) đứng vững. Và **cả
`"Máy lạnh"` lẫn `"Điều hòa"` đều có thật** (`Máy lạnh Test-2` trong fixture
golden; `Điều hòa Daikin FTHF25XVMV` trong `data/historical_confirmed/registry.jsonl`,
bản ghi Owner xác nhận), cộng `config/adjustments.yaml` đã coi `"điều hòa"` là
từ chỉ mặt hàng ấy từ trước `R5.1`.

Đính chính nhỏ kèm theo: `src/index.js`, `kiem/nhom-hang.js` và `DEC-205` §4
dẫn `"Điều hòa Daikin"` là nằm trong *fixture golden* — thực tế nó nằm trong
`registry.jsonl` Owner xác nhận. Mệnh đề thực chất ĐÚNG, và còn được chống đỡ
mạnh hơn mức được dẫn; chỉ vị trí dẫn là sai.

Khung rủi ro để Owner quyết: ba alias này **không thể** tạo category giả (đầu
ra vẫn ∈ `NHOM`), **không thể** rò dữ liệu, **không chạm** tiền. Xấu nhất là
hai bucket thật bị gộp trong khi Owner muốn tách — hiện ra ở `R6` thành một
nhóm lớn hơn dự kiến, sửa bằng cách bỏ một dòng alias.

---

## 7. Bàn giao cho bước kế tiếp

Bước MERGE + DEPLOY **chưa xảy ra**. `S139` §4 còn nguyên hiệu lực. Bổ sung:

1. Mở phiên đúng quy trình (`CLAUDE.md` → S000; xác định nhánh mặc định THẬT
   trên origin của cả hai repo; fetch; `branch_authority_check.sh` tới
   `AUTHORITY_OK`).
2. **Owner quyết trước merge**: `CHECK-R51-26` còn `NOT_TESTED`, và `R5` cho
   thấy Reports merge xong là Render tự deploy production.
3. **Thứ tự merge: Tracking TRƯỚC, Reports SAU** (lý do không đổi; §4.2 của
   bản ghi chứng minh lại rằng Reports đọc artifact chưa có trường này ra
   `None` mà không lỗi).
4. **Đóng `OWNER_DECISION_REQUIRED` (mục 6) TRƯỚC khi `R6` dùng
   `category_label` làm khoá gộp** — đặc biệt alias `Ti vi`.
5. **`COR-R5.1R1-01`**: phiên nào chạm mã Reports kế tiếp nên sửa hai chú
   thích cũ. Không mở phiên riêng.
6. Sau merge Reports cần MỘT lần capture mới thì cột Nhóm hàng mới có dữ liệu
   (`AR-R5.1-04`); trước đó cột hiện `"—"` và đó là trạng thái ĐÚNG.
7. **KHÔNG gộp `R6` vào phiên merge.**

Cân nhắc cho Owner (không phải finding): thêm `['Máy giặt sấy', []]` vào `NHOM`
đóng được `AR-R5.1R1-05`, vốn có ca thật trong đơn golden `BH62439`.

---

## 8. Trạng thái cuối

```text
Kết luận review          ACCEPT_WITH_RECORDED_RISK
CHECK-R51R1-01..16       PASS (E1) — tái kiểm chứng độc lập, giữ nguyên
CHECK-R51R1-17           NOT_TESTED → PASS (E1)   ← phiên này
CHECK-R51-26             NOT_TESTED               ← GIỮ NGUYÊN
Merge / deploy / R6      KHÔNG thực hiện
Repair cycle tiêu        0 → lineage R5 vẫn 2 allowed / 2 used / 0 remaining
Escalation               KHÔNG mở (REPAIR_REQUIRED = 0)
```

Phiên này **không** tự đánh dấu Owner Acceptance.

### Ghi chú môi trường

Container không có sẵn phụ thuộc Python của Reports; phiên dựng `.venv` mới
(`pip install -e ".[dev,web,storage,history]"`, gồm cả extra `storage` nên
`botocore` có mặt và số skip là `11`). `.venv/` nằm trong `.gitignore` và
KHÔNG được commit. Clone Reports trong container này là clone NÔNG (88 commit)
— nguồn của bài pytest đỏ ở mục 5.
