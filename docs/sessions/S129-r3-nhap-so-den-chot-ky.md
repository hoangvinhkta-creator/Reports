# S129 — R3: từ nhập sổ tới bảng nhân viên, xuất Excel và chốt kỳ

## 0. Tóm tắt cho người đọc vội

R3 làm năm việc. Việc quan trọng nhất trong số đó sửa một lỗi **không có triệu
chứng**: khoá của một dòng hàng phụ thuộc vào VỊ TRÍ của nó trong file Excel,
nên kế toán đảo hai dòng cùng tên hàng trong một đơn là đủ để giá nhập Owner
đã gõ cho dòng này lặng lẽ chuyển sang dòng kia. Không cờ nào bật, không màn
hình nào đổi, con số thì sai.

Bốn việc còn lại: chuẩn hoá loại dòng (và nhờ đó đóng `TASK-105B-Q3` đã
`BLOCKED_BY [TASK-103]` từ lâu), gom mọi màn hình về MỘT effective data, xuất
Excel từ chính effective data đó thay vì từ kết quả pipeline cũ, và thêm cơ
chế chốt kỳ có phiên bản.

`CHECK-R3-01` … `CHECK-R3-18` PASS. `CHECK-R3-19` (Independent Review) và
`CHECK-R3-20` (Owner nghiệm thu) VẪN `NOT_TESTED` — phiên này không tự tuyên
bố hai check đó, đúng kỷ luật đã áp cho R1 và R2. Task ở `IMPLEMENTED`.

Task canonical: `docs/tasks/R3-nhap-so-den-chot-ky.md`.

## 1. Nền và ranh giới

- Nhánh phát triển: `claude/r3-import-to-period-close-nakk8e`.
- Base: nhánh mặc định `claude/extract-upload-repo-gq2ws4` tại `45f0e1b`
  (Merge PR #7 — R2 + ba repair). Xác nhận đồng bộ trước khi đọc governance:
  `git rev-list --left-right --count origin/<default>...HEAD` → `0 0`.
- Bốn commit của phiên này:

```text
6897234  R3 §2: loại dòng hiệu lực + luật giá nhập theo chính sách
ae27190  R3 §1: khoá dòng đi theo NỘI DUNG, không theo vị trí trong file
80925f4  R3 §3/§4/§5: một effective data, xuất Excel từ nó, và chốt kỳ có phiên bản
7df5f48  R3: đối soát trên dữ liệu thật + test hồi quy qua web thật
```

- Tracking KHÔNG bị sửa. Reports KHÔNG thêm một nguồn giá nào, KHÔNG đổi công
  thức MIN, KHÔNG sửa `ADR-110`, và KHÔNG định nghĩa ngữ nghĩa hoàn/hủy.

## 2. Lỗi trung tâm — tái hiện được

`app/history/extraction.build_source_lines` đánh `occurrence_index` bằng đúng
một quy tắc: sắp theo `source_row` tăng dần rồi đếm `1..n` trong phạm vi
`(order_key, product_key)`. Chính docstring của nó nói vì sao chỉ số ấy tồn
tại — *"dữ liệu thật có đơn chứa hai dòng cùng tên hàng (ví dụ 'Chi phí vận
chuyển')"* — nhưng cách đánh số lại lấy VỊ TRÍ làm danh tính.

Chuỗi hỏng, đo được qua database thật
(`tests/test_r3_import_binding.py::test_reordering_the_rows_keeps_each_override_on_its_own_line`):

```text
lần nạp 1   BH1 · "Chi phí vận chuyển" · 100.000   → occurrence 1
            BH1 · "Chi phí vận chuyển" · 200.000   → occurrence 2
Owner gõ giá nhập 70.000 cho occurrence 1  (tức dòng 100.000)

kế toán đảo hai dòng trong file, KHÔNG đổi một giá trị nào

lần nạp 2   dòng 200.000 đứng trên → occurrence 1
            → giá nhập 70.000 nay thuộc về dòng 200.000
```

Trên nhánh trước R3, `sell_price_of(BH1, "Chi phí vận chuyển", 1)` sau lần nạp
thứ hai trả về `200000`. Sau R3 nó trả về `100000`.

## 3. Ba mỏ neo, và vì sao mỏ neo yếu nhất có điều kiện

```text
1. IMEI          mã máy — gần một ID dòng ổn định nhất mà sổ này có
2. FINGERPRINT   toàn bộ nội dung nghiệp vụ của dòng không đổi
3. POSITION      thứ tự dòng — YẾU NHẤT, và CÓ ĐIỀU KIỆN
```

IMEI thắng cả fingerprint: một chiếc máy có IMEI mà kế toán sửa lại giá bán
VẪN là chiếc máy đó, còn hai chiếc cùng model cùng giá thì fingerprint không
phân biệt nổi.

Vị trí chỉ được dùng khi dùng SAI nó không thể làm hỏng gì:

```text
còn ĐÚNG một dòng vào và ĐÚNG một khoá trống    → ghép (không có gì để nhầm)
không khoá trống nào mang quyết định của người  → ghép theo thứ tự (vô hại)
còn lại                                         → NGOẠI LỆ, không đoán
```

Nhánh thứ hai là một quyết định có chủ đích, không phải một lỗ hổng: nếu ghép
sai ở đó thì hai cách ghép cho ra hai lịch sử version khác nhau nhưng KHÔNG
khác nhau một đồng nào. Bắt mọi lần đổi thứ tự dòng thành một "ngoại lệ" sẽ
tạo ra nhiễu tới mức Owner học cách bấm bỏ qua — và khi đó ngoại lệ THẬT ở
nhánh ba cũng bị bỏ qua theo.

Nhánh ba KHÔNG xoá và KHÔNG hủy khoá cũ: dòng vào nhận khoá MỚI (chỉ số nối
tiếp sau chỉ số lớn nhất đã dùng), khoá cũ chỉ vắng mặt ở snapshot này theo
đúng cơ chế `absent_keys` đã nghiệm thu ở PRA-002 slice B. Đó cũng là câu trả
lời cho ràng buộc *"đơn vắng trong file tải sau không tự bị xóa/hủy"*.

## 4. Loại dòng — điều nó mở khoá

`OD-105B-01` §3 đã ký câu trả lời cho dòng phụ từ lâu:

```text
AccountingPurchasePrice = 0 BY DEFINITION
provenance = Policy:SupplementaryExpenseZeroPurchasePrice
```

Thứ còn thiếu là một tầng phân loại CÓ THẨM QUYỀN để biết dòng nào thuộc nhóm
đó — đúng thứ mà `TASK-105B-Q3` bị `BLOCKED_BY [TASK-103 Product/Transaction
Classification]` chờ. R3 xây tầng đó, ở ĐÚNG chỗ `OD-105B-01` §C yêu cầu: bên
TRÊN provider, không nằm trong `FilePriceProvider`.

Sáu loại, và mỗi loại chỉ tới một quyết định đã ký:

| Loại | Giá nhập | Thẩm quyền |
|---|---|---|
| `SALE` | đi hỏi nguồn giá; không tra ra ⟹ Pending | `OD-105B-01` §3 câu 2 |
| `FEE` | `0` BY DEFINITION | `OD-105B-01` §3 |
| `DISCOUNT` | `0` BY DEFINITION | `OD-105B-01` §3 + `DEC-180` |
| `ACCESSORY_GIFT` | vẫn cần giá THẬT; thiếu ⟹ Pending | `OD-4` |
| `RETURN_CANCEL` | chặn có tên | `OD-2` |
| `UNDECIDED_DOCUMENT` | chặn có tên | `OD-2` |

Thứ tự ưu tiên của giá nhập hiệu lực, và chính sách đứng CUỐI:

```text
giá tay  →  giá tự động (MIN theo ngày bán)  →  chính sách loại dòng  →  None
```

Chính sách đứng cuối là một quyết định thật: nếu một nguồn giá thật trả lời
được cho một dòng phí, con số thật đó THẮNG con số 0 của chính sách. Chính
sách là chỗ dựa khi không ai trả lời, không phải một lệnh ghi đè.

Và `policy_purchase_price` trả `None` cho mọi loại khác — kể cả
`ACCESSORY_GIFT`: một chiếc giá treo tivi tặng kèm VẪN tốn tiền mua, ghi giá
nhập của nó là `0` sẽ biến một khoản lỗ có thật thành lãi 0 đồng.

### Hoàn/hủy — R3 làm cho sự THIẾU VẮNG nhìn thấy được, không lấp nó

`config/line_types.yaml` khai `BH: SALE` và **để trống** phần hoàn/hủy. `BTL`
có mặt trong dữ liệu thật (3 dòng kỳ 01/2026, 1 dòng kỳ 06/2026) và repo
KHÔNG có một quyết định nào của Owner nói `BTL` nghĩa là gì. Suy ra "bán trả
lại" từ ba chữ cái rồi tự cộng một dấu âm vào KPI chính là điều `OD-2` cấm.

Nên các dòng đó nhận `UNDECIDED_DOCUMENT` + cửa chặn `LINE_TYPE_UNDECIDED`, và
đi vào hàng đợi `loai-chua-ro`. Chúng KHÔNG bị tính như dòng bán (im lặng SAI)
và KHÔNG bị bỏ khỏi mọi phép gộp (im lặng MẤT).

### Chiết khấu — nêu tên nguy cơ, không tự sửa

`DEC-180` ghi hai CÁCH GHI của cùng một nghiệp vụ. Một đơn mang CẢ HAI (một
dòng "Chiết khấu" riêng VÀ một cột `discount` khác `0`) là chỗ duy nhất phép
trừ có thể xảy ra hai lần. `discount_double_count_orders` NÊU TÊN đơn đó và
dừng lại: hai cách sửa có thật (bỏ cột, hay bỏ dòng) là hai khẳng định khác
nhau về sổ gốc, và không cái nào hệ thống có thẩm quyền tự chọn.

Trên hai kỳ golden, danh sách này RỖNG — sổ hiện hành chỉ dùng cột.

## 5. Bằng chứng thực thi (E1)

### 5.1. Đối soát trên DỮ LIỆU THẬT

`python3 -m tools.analysis.r3_reconcile` — hai kỳ nghiệp vụ THẬT của Tín Phát
đã ẩn danh theo `OD-GB-1`, đi qua ĐÚNG seam production
(`app/composition.run_import_production` → `present_lines`):

```text
==============================================================================
period_2026_01.xlsx — kỳ 01/2026
==============================================================================
dòng đã trình bày: 351

§2 — phân bố loại dòng:
    SALE                   321  (Hàng bán)
    ACCESSORY_GIFT           5  (Phụ kiện / quà tặng)
    FEE                     22  (Phí)
    UNDECIDED_DOCUMENT       3  (Chứng từ chưa định nghĩa)

§1 — nạp lần đầu: {'INSERT': 351, 'SAME': 0, 'SOURCE_CHANGED': 0, 'ORDER_KEY_COLLISION': 0} · ngoại lệ gắn dòng: 0
§1 — nạp LẠI cùng file: {'INSERT': 0, 'SAME': 351, 'SOURCE_CHANGED': 0, 'ORDER_KEY_COLLISION': 0} · ngoại lệ gắn dòng: 0
§1 — nạp lại file ĐẢO THỨ TỰ DÒNG: {'INSERT': 0, 'SAME': 351, 'SOURCE_CHANGED': 0, 'ORDER_KEY_COLLISION': 0} · ngoại lệ gắn dòng: 0
       khoá dòng mới phát sinh: 0 (0 = không quyết định nào có thể trôi)

§3 — effective data:
    dòng kỳ                351
    Σ dòng theo nhân viên  351
    Σ dòng theo sheet      351
    doanh thu kỳ           3,562,310,000
    Σ doanh thu nhân viên  3,562,310,000
    lợi nhuận KPI kỳ       5,783,750
    coverage               24/351  (INCOMPLETE)
    dòng chưa có giá nhập  327
    dòng giá 0 theo chính sách (OD-105B-01 §3): 22
    cửa chặn                {'LINE_TYPE_UNDECIDED': 3, 'QUANTITY_ZERO': 3, 'PURCHASE_PRICE_MISSING': 327}
    đơn nghi trừ chiết khấu hai lần: []

§4 — file xuất:
    sheet                  ['Tổng kỳ', 'Theo nhân viên', 'Nội thành', 'Gia dụng', 'Tín Phát']
    dòng trong file        351  (màn hình: 351)
    lợi nhuận KPI trong file 5,783,750  (màn hình: 5,783,750)
    KHỚP                   True

==============================================================================
period_2026_06.xlsx — kỳ 06/2026
==============================================================================
dòng đã trình bày: 180

§2 — phân bố loại dòng:
    SALE                   163  (Hàng bán)
    ACCESSORY_GIFT           2  (Phụ kiện / quà tặng)
    FEE                     14  (Phí)
    UNDECIDED_DOCUMENT       1  (Chứng từ chưa định nghĩa)

§1 — nạp lần đầu: {'INSERT': 180, 'SAME': 0, 'SOURCE_CHANGED': 0, 'ORDER_KEY_COLLISION': 0} · ngoại lệ gắn dòng: 0
§1 — nạp LẠI cùng file: {'INSERT': 0, 'SAME': 180, 'SOURCE_CHANGED': 0, 'ORDER_KEY_COLLISION': 0} · ngoại lệ gắn dòng: 0
§1 — nạp lại file ĐẢO THỨ TỰ DÒNG: {'INSERT': 0, 'SAME': 180, 'SOURCE_CHANGED': 0, 'ORDER_KEY_COLLISION': 0} · ngoại lệ gắn dòng: 0
       khoá dòng mới phát sinh: 0 (0 = không quyết định nào có thể trôi)

§3 — effective data:
    dòng kỳ                180
    Σ dòng theo nhân viên  180
    Σ dòng theo sheet      180
    doanh thu kỳ           1,924,872,000
    Σ doanh thu nhân viên  1,924,872,000
    lợi nhuận KPI kỳ       4,852,000
    coverage               14/180  (INCOMPLETE)
    dòng chưa có giá nhập  166
    dòng giá 0 theo chính sách (OD-105B-01 §3): 14
    cửa chặn                {'LINE_TYPE_UNDECIDED': 1, 'QUANTITY_ZERO': 1, 'PURCHASE_PRICE_MISSING': 166}
    đơn nghi trừ chiết khấu hai lần: []

§4 — file xuất:
    sheet                  ['Tổng kỳ', 'Theo nhân viên', 'Nội thành', 'Gia dụng', 'Tín Phát']
    dòng trong file        180  (màn hình: 180)
    lợi nhuận KPI trong file 4,852,000  (màn hình: 4,852,000)
    KHỚP                   True
```

**Đọc con số `coverage 24/351`:** 22 trong 24 dòng chốt được lợi nhuận là các
dòng phí vừa nhận giá `0` theo chính sách. Trước R3 chúng nằm trong nhóm
"thiếu giá vĩnh viễn"; nay chúng không còn khoá coverage. Phần còn lại (327
dòng) thiếu giá vì lý do THẬT — chưa có MIN cho ngày bán, hoặc chưa phân loại
— và đó là việc của R1/R2, không phải của R3.

### 5.2. Bộ test R3 (mới, 92 bài)

```text
$ .venv/bin/python -m pytest -q tests/test_r3_import_binding.py \
    tests/test_r3_line_types.py tests/test_r3_export_and_period_close.py \
    tests/test_r3_web_workflow.py tests/test_r3_golden_reconciliation.py
96 passed in 8.1s
```

- `test_r3_import_binding.py` (16) — ba mỏ neo ở tầng thuần, cộng sáu bài đi
  qua database thật: file trùng, file sửa, đảo thứ tự (nội dung giống và khác
  nhau), đơn nhiều hàng, ngoại lệ khi không kết luận được, và "đơn vắng ở file
  sau KHÔNG bị xoá".
- `test_r3_line_types.py` (25) — sáu loại dòng trên ĐÚNG từ vựng production,
  ranh giới `0`-chính-sách vs `0`-thay-cho-thiếu, chiết khấu không trừ hai
  lần, và ba bài qua database thật.
- `test_r3_export_and_period_close.py` (19) — file xuất mang giá Owner đã sửa;
  đúng một cột `Giá nhập KPI`; ô trống ≠ `0`; tổng khớp; chốt/mở lại/phiên bản.
- `test_r3_web_workflow.py` (14) — qua ứng dụng Flask THẬT: tải file, chốt kỳ,
  thao tác bị TỪ CHỐI 409 sau khi chốt, mở lại kèm lý do, chốt sống qua một
  `create_app` HOÀN TOÀN MỚI, ba hàng đợi ngoại lệ mới, và VÒNG ĐỜI ĐẦY ĐỦ của
  một ngoại lệ gắn dòng (hiện trên dòng → bấm ĐÃ XỬ LÝ → biến khỏi hàng đợi,
  giá nhập tay vẫn nằm đúng khoá cũ).
- `test_r3_golden_reconciliation.py` (22) — các mệnh đề §5.1 thành lưới hồi
  quy, chạy trên chính hai kỳ thật.

### 5.3. Nhóm hồi quy của R1/R2 và Golden

```text
$ .venv/bin/python -m pytest -q tests/test_r2_product_classification.py \
    tests/test_r2_web_workflow.py tests/test_daily_min_orchestration.py \
    tests/test_business_vertical.py tests/test_employee_workspace_ux.py \
    tests/test_golden_baseline.py
294 passed, 2 skipped in 33.19s
```

### 5.4. Full regression

```text
$ .venv/bin/python -m pytest -q tests/
3043 passed, 12 skipped in 208.68s
```

Baseline trước R3 trên cùng môi trường này: `2946 passed, 12 skipped`.
(`S128` ghi `2947 passed, 11 skipped`; chênh đúng một bài là
`test_boto3_putobject_ifnonematch_capability`, skip ở đây vì môi trường phiên
này không cài `boto3` — không liên quan tới R3.)

### 5.5. Migration `0009` — cả hai chiều, trên SQLite

```text
$ alembic upgrade head
head: 0009_line_binding_and_period_close

# nạp một lần CHỐT KỲ và một giá nhập tay, rồi hạ cấp
$ alembic downgrade 0008_purchase_price_reason
0009_line_binding_and_period_close: giữ lại 1 dòng của period_close trong
period_close__owner_backup — `alembic upgrade` sẽ nạp lại.

$ alembic upgrade head
0009_line_binding_and_period_close: đã nạp lại 1 dòng Owner vào period_close.

period_close sau round-trip: [(2026, 1, 1, 'owner-web', 'Đã duyệt', 351, 'fp-r3')]
giá nhập tay còn nguyên:     [('BH1', '4000000', 'MANUAL_OVERRIDE', 'theo hoá đơn')]
line_binding_exception tồn tại: True
```

Điều bài này chứng minh: một lần rollback KHÔNG làm mất **quyết định của
người** — cả giá nhập Owner gõ tay (đã có từ R2) lẫn lần chốt kỳ (mới của R3)
đều sống sót nguyên vẹn. `line_binding_exception` thì ngược lại — nó là bằng
chứng DẪN XUẤT, nạp lại sổ là dựng lại được, nên `downgrade` được phép xoá nó.

### 5.6. Governance validators

```text
validate_evidence.py            PASS  (161 REQUIRED PASS)
validate_project_state.py       PASS
validate_structure.py           PASS  (21 required paths)
validate_task_completion.py     PASS  (14 DONE)
validate_reference_integrity.py FAIL  — ĐÚNG 3 reference `TASK-REM-T06`
                                       đã biết từ trước (baseline không đổi)
```

## 6. Một lỗi lộ ra từ chính bộ test, và nó đã được sửa

`business_presentation.PROVENANCE_LABELS` tra bằng `[...]` và không có mục
`POLICY_ZERO`. Nghĩa là ngay khi một kỳ có MỘT dòng phí, trang bảng kê chi tiết
ném `KeyError` và trả HTTP 500 — trên dữ liệu thật là 22/351 dòng của kỳ
01/2026, tức trang đó sẽ hỏng ở mọi kỳ.

Sửa hai chỗ: thêm nhãn riêng ("Chính sách (dòng phụ)"), và đổi sang `.get(...)`
để một provenance chưa có nhãn hiện NGUYÊN VĂN mã của nó thay vì làm sập cả
trang. Bài bắt được nó:
`tests/test_r3_web_workflow.py::test_the_policy_zero_queue_lists_the_fee_lines`.

## 7. Rủi ro giữ lại

### AR-R3-01 — phân loại mã sản phẩm KHÔNG đi qua cửa chặn kỳ đã chốt

Thẩm quyền Product Identity (R2) là quyết định TOÀN CỤC theo
`raw_identity_key`, không theo dòng và không theo kỳ. Một lần xác nhận mã có
thể làm đổi giá nhập — và vì thế đổi con số — của một kỳ ĐÃ CHỐT.

Không khoá nó là có chủ đích: mapping là toàn cục, nên chặn nó sẽ chặn luôn
việc phân loại cho các kỳ đang mở ngay khi một kỳ bất kỳ được chốt.

Giảm nhẹ ĐÃ CÀI: `period_drift` so vân tay bộ số hiện tại với bộ số lúc chốt,
và trang chốt kỳ nói thẳng khi chúng đã lệch
(`test_drift_is_reported_when_the_numbers_change_after_closing`). Thay đổi
không bị chặn, nhưng không bao giờ im lặng.

### AR-R3-02 — `BTL` vẫn chưa có nghĩa

4 dòng trên hai kỳ golden mang tiền tố `BTL` và ở `UNDECIDED_DOCUMENT`. Chúng
không vào lợi nhuận, và chúng giữ coverage dưới 100 % cho tới khi Owner quyết.
Đúng theo `OD-2`, nhưng có nghĩa hai kỳ này không đạt `OFFICIAL` chỉ vì bốn
dòng. Việc cần Owner: nói `BTL` nghĩa là gì — một dòng trong
`config/line_types.yaml` là đủ để đóng, nhưng dòng đó là một quyết định
nghiệp vụ.

### AR-R3-03 — mỏ neo IMEI chưa đo được trên dữ liệu thật

Cột `imei` rỗng trên toàn bộ hai kỳ golden — `tests/fixtures/golden/anonymize.py`
liệt kê `imei` trong `DROPPED_COLUMNS` và xoá hẳn nó (đo lại: `with imei 0`
trên cả 351 và 180 dòng). Nhánh IMEI vì thế chỉ được kiểm bằng test tổng hợp.

Tác động nếu nhánh này sai: hệ thống lùi về mỏ neo `FINGERPRINT` — đúng hành
vi đã đo được là an toàn trên dữ liệu thật. Không có nhánh nào tệ hơn trạng
thái trước R3.

### AR-R3-04 — `AR-R2-01` chưa được đóng

Lỗi có TRƯỚC R2 (`SetPending` rồi `ConfirmMapping` làm log identity không đọc
được) giữ nguyên. R3 không chạm chuỗi identity; đóng nó cần một quyết định về
`_ACTIVE_STATUSES` của `PENDING`/`STALE`, ngoài Scope Lock của R3.

## 7b. Bước bắt buộc khi triển khai

`ALEMBIC_HEAD` chuyển sang `0009_line_binding_and_period_close`, và
`tools/db.assert_schema_current` fail-closed: một database còn ở `0008` sẽ làm
app TỪ CHỐI khởi động thay vì chạy lên với hai bảng thiếu. Vì vậy thứ tự triển
khai bắt buộc là:

```text
1. alembic upgrade head        (trên database production)
2. deploy code
```

Đảo thứ tự sẽ cho một khoảng thời gian app không khởi động được — không mất dữ
liệu, nhưng là downtime không cần thiết. Đây là cùng ràng buộc đã áp cho
migration `0008` của R2.

## 8. Rollback

Rollback code: `git revert` bốn commit của nhánh này. Không có bước dữ liệu
nào bắt buộc — mọi thay đổi schema là additive.

Rollback schema (chỉ khi cần): `alembic downgrade 0008_purchase_price_reason`.
Nó xoá `line_binding_exception` (dẫn xuất, dựng lại được) và cất
`period_close` vào `period_close__owner_backup` trước khi xoá; `alembic upgrade
head` nạp lại (§5.5 đã chạy thật).

Một điểm vận hành phải nói rõ: **hạ cấp code sau khi đã có ngoại lệ gắn dòng
là một thao tác một chiều về mặt thông tin.** Bản ghi ngoại lệ dựng lại được
bằng cách nạp lại đúng file sổ đó, nhưng phần `resolved_at`/`resolution_note`
mà Owner đã ghi thì không — không có nơi nào khác giữ chúng.

## 9. Checklist cho Owner

1. **Nạp lại một sổ đã sửa.** Mở trang Dữ liệu, tải lên một file đã đổi thứ tự
   vài dòng. Kỳ vọng: số dòng không đổi, không dòng nào thành "mới", và mọi
   giá nhập đã gõ vẫn nằm đúng dòng cũ.
2. **Xem hàng đợi "Giá theo chính sách"** (`/kinh-doanh/gia-nhap?loc=gia-theo-chinh-sach`).
   Kỳ vọng: đúng các dòng `Chi phí vận chuyển` / `Chi phí lắp đặt` / `Chênh
   VAT` / `Phụ Phí`, cột Nguồn giá nhập ghi "Chính sách (dòng phụ)". Nếu MỘT
   mặt hàng thật lọt vào đây, đó là lỗi phân loại — báo lại, đừng sửa từ vựng
   để khớp một con số.
3. **Xem hàng đợi "Ngoại lệ gắn dòng"** (`?loc=gan-dong`). Trên dữ liệu hiện
   tại nó RỖNG — chỉ có dòng nào mà lần nạp lại không ghép chắc chắn được mới
   vào đây. Nút ĐÃ XỬ LÝ chỉ ghi "đã xem xong"; nó KHÔNG đổi khoá và KHÔNG di
   chuyển quyết định nào.
4. **Xem hàng đợi "Loại dòng chưa rõ"** (`?loc=loai-chua-ro`). Kỳ vọng: đúng
   các đơn `BTL`. Đây là chỗ chờ quyết định của Owner (`AR-R3-02`).
5. **Tải Excel** từ trang Báo cáo. Kỳ vọng: sheet `Tổng kỳ` khớp từng con số
   với màn hình; cột `Giá nhập KPI` có đúng MỘT cột; ô trống ở dòng chưa có
   giá — KHÔNG phải số `0`.
6. **Chốt kỳ**, rồi thử sửa một giá nhập của kỳ đó. Kỳ vọng: bị TỪ CHỐI kèm
   câu giải thích, không phải một cảnh báo rồi vẫn lưu. Mở lại kỳ (bắt buộc gõ
   lý do) rồi sửa lại — lần này phải lưu được, và lịch sử chốt kỳ hiện đủ hai
   dòng.

## 10. Đầu vào cho phiên sau

- Sáu loại dòng: `line_type.LINE_TYPES`; từ vựng ở `config/line_types.yaml`.
- Giá nhập KPI hiệu lực: `BusinessLine.purchase_price` — giá tay → MIN đúng
  `sale_date` → chính sách loại dòng.
- Khoá dòng: `(order_key, product_key, occurrence_index)`, gắn theo NỘI DUNG
  (`app/history/line_binding.py`).
- Chốt kỳ: `app/web/period_lock.py`; cửa chặn ghi ở tầng route
  (`_guard_lines`, `guard_period_open`, `guard_product_open`).
- Hai việc còn treo cần Owner: nghĩa của `BTL` (`AR-R3-02`), và `AR-R2-01`.
- Lệnh đối soát: `python3 -m tools.analysis.r3_reconcile`.
- Lệnh test: `python -m pytest -q tests/` (full), hoặc năm file `test_r3_*.py`
  cho riêng R3.
