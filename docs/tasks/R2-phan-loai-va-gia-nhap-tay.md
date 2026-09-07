# R2 — Phân loại sản phẩm và giá nhập tay

## Metadata

Status:
IMPLEMENTED

Current Status Reason:
Toàn bộ năm gói của `R2 Execution Brief` đã triển khai và có test đi hết
chuỗi. `CHECK-R2-01` … `CHECK-R2-17` PASS (bằng chứng ở §6 và ở
`docs/sessions/S128-r2-phan-loai-va-gia-nhap-tay.md`). Hai check còn lại
KHÔNG do phiên này quyết định và vẫn `NOT_TESTED`: `CHECK-R2-18` (Independent
Review) và `CHECK-R2-19` (Owner nghiệm thu ba luồng production). Brief §9 nói
thẳng "Không tự tuyên bố Independent Review hoặc Owner Acceptance PASS", nên
task DỪNG ở `IMPLEMENTED`, không chuyển `VERIFYING` và không chuyển `DONE`.

Phase:
PHASE-01 — Engine tính toán

Task Mode:
MAJOR

Primary Agent Tier:
C

Escalation Tier:
C

Difficulty:
4/5

Risk:
4/5

Blast Radius:
5/5 (V4.1 §4 — chấm theo failure path: `quyết định phân loại → identity →
giá nhập KPI → EligibleKpiProfit → DS quy đổi → KPI/lương`)

Effective Risk:
HIGH (Blast Radius quyết định, không phải Risk cục bộ — V4.1 §4.1)

Project Profile:
PRODUCT

Review Budget lineage:
**Đề xuất `R2` là root lineage RIÊNG**, `2 allowed / 0 used / 2 remaining`.
Xem `PROJECT/REVIEW_BUDGET_LEDGER.md` → "Root Task: R2", trong đó có ghi một
`CONFLICT DETECTED` chưa giải quyết: bản ledger viết trước khi Owner ban hành
`R2 Execution Brief` có liệt kê chữ "R2" trong ví dụ về sub-unit KHÔNG có ngân
sách riêng. Phiên này KHÔNG tự quyết; nó ghi cả hai cách đọc và để Owner/
reviewer chốt. Không repair cycle nào bị tiêu trong phiên này, nên cách đọc
nào đúng cũng không làm sai số dư hiện tại.

Owner Authority:
`R2 Execution Brief — Phân loại sản phẩm và giá nhập tay`. Nền: `R1` đã
Independent Review ACCEPT (Tracking `f9caaa036cc6fbc9a021aeea99158ba6fce9d20e`,
Reports `eafcb08eb56ca89068d4e91e0c0a126dbab906df`). Quyết định kiến trúc nền:
`docs/adr/ADR-110-daily-min-price-authority.md` (KHÔNG bị R2 sửa).

---

## 1. Mục tiêu

R1 trả lời được câu "giá vốn của ngày bán là bao nhiêu" cho những dòng mà máy
đã biết là mặt hàng nào. R2 trả lời cho phần còn lại: những dòng máy CHƯA biết
là mặt hàng nào, và những dòng thật sự không có trên bảng giá.

Bốn kết quả, và mỗi dòng phải đi tới đúng một trong bốn:

```text
MATCHED_TRACKING   đã có mã Tracking hợp lệ      → tra MIN theo ngày bán
NEEDS_REVIEW       chưa đủ căn cứ                → người chọn mã, hoặc chọn ngoài bảng
OUT_OF_CATALOG     người xác nhận không có trên bảng giá → nhập giá tay
CONFLICT           hai nguồn mapping đã xác nhận chỏi nhau → người chọn LẠI
```

R2 KHÔNG thay công thức MIN của Tracking và KHÔNG xây giá thực nhập.

## 2. Hai mối nối bị ĐỨT mà R2 tồn tại để sửa

Đây là phần quan trọng nhất của task, vì cả hai đều **không có triệu chứng**:
màn hình phân loại chạy đúng, log ghi đúng, và báo cáo không đổi một chữ.

### 2.1. Resolver production không hỏi store của Reports

`ProductIdentityResolver.resolve()` rẽ theo `tracking_identity_authority`.
Đường production (`True` — dùng bởi `composition.py`, `planning.py` và mọi
loader) đi vào `_tracking_authoritative()`, và hàm đó đọc `alias.map`/`board`
rồi `inv.map`, **không hỏi `self.view` một câu nào**. Nhánh duy nhất đọc store
của Reports là `_alias_exact()`, và nó chỉ chạy ở chế độ legacy.

Hệ quả trên tài sản thật: Owner chọn một mặt hàng trên
`/kinh-doanh/nhan-vien/phan-loai`, `ConfirmMapping` được ghi, màn hình đổi từ
"Chưa phân loại" sang "Thiếu giá" — và lần chạy sổ kế tiếp vẫn Pending, vì mã
ấy chưa bao giờ tới được resolver.

### 2.2. Đường chạy báo cáo đọc log ở SAI CHỖ

Ba nơi tự mở một `JsonlProductIdentityStore` trên
`data/product_identity/mappings.jsonl`:

```text
app/demo.py                  (store view cho resolver)
app/owner_usability.py       (`_identity_store_view` cho kế hoạch daily-min)
tools/tracking/live_pull.py  (kế hoạch daily-min ở đường web)
```

Trên máy Owner đường dẫn đó ĐÚNG. Trên bản Web nó SAI: container không có
persistent disk (`Dockerfile`, `render.yaml`), và log thật nằm ở R2 object
store qua `identity_gateway.build_store()`. Cả ba luôn đọc ra một store RỖNG.

Nên kể cả sau khi sửa §2.1, mã Owner vừa chọn vẫn không lọt vào tập mã đi hỏi
`daily-min` và vẫn không được resolver dùng.

## 3. Scope Lock

### Trong phạm vi

- Nối quyết định phân loại vào resolver production và vào kế hoạch `daily-min`.
- `OUT_OF_CATALOG` — command, trạng thái, lưu bền, nút bấm, "Nối lại Tracking".
- `CONFLICT` — phát hiện, hiển thị, và đường thoát KẾT THÚC được.
- Giá nhập tay: `entered_by` + `reason` (provenance còn thiếu), migration
  additive `0008`.
- Hàng đợi/bộ lọc xử lý trên bảng kê chi tiết.
- Test xuyên suốt + full regression.

### Ngoài phạm vi (giữ nguyên từ Brief §3)

Giá thực nhập/FIFO · fuzzy tự xác nhận · thiết kế lại khoá dòng (R3) · chốt
kỳ và Excel/bảng nhân viên (R3) · dashboard quản trị (R4) · hệ thống đăng nhập
mới.

## 4. Quyết định thiết kế và LÝ DO

### 4.1. `CONFLICT` là trạng thái SUY RA, không phải trạng thái LƯU

`MappingStatus.CONFLICT` đã tồn tại trong enum từ Phase 1 và R2 cố ý KHÔNG
dùng nó. Mâu thuẫn là quan hệ giữa một quyết định đã lưu của Reports và
authority của Tracking TẠI MỘT CAPTURE CỤ THỂ. Lưu nó xuống sẽ đóng băng một
quan hệ mà lần capture sau có thể tự giải: mã Tracking đổi lại, mâu thuẫn hết,
nhưng bản ghi vẫn nói còn.

### 4.2. Vì sao mâu thuẫn phải KẾT THÚC được

Nếu lựa chọn của người dùng không mang dấu vết rằng họ đã NHÌN THẤY đúng mâu
thuẫn ấy, lần chạy sau suy ra lại nó và hỏi lại — mãi mãi. Đó là lý do
`MappingSource.HUMAN_CONFLICT_RESOLUTION` tồn tại. Nó KHÔNG phải "last write
wins": nó là "người đã được cho xem cả hai mã và đã chọn", có `reason`, có
actor, có audit event.

### 4.3. `OUT_OF_CATALOG` phải nằm trong `_ACTIVE_STATUSES`

`_project()` trước R2 giữ trong `active` đúng các bản ghi `CONFIRMED`. Nếu
`OUT_OF_CATALOG` rơi ra, hai thứ hỏng và cả hai đều im lặng:

1. **Chuỗi supersede đứt.** Lệnh kế tiếp (chính là "Nối lại Tracking") khai
   `supersedes=None` trong khi `last_record_id` của khoá đã có một bản ghi →
   `INV-33` NỔ ở **mọi lần đọc về sau**. Một thao tác hợp lệ của người dùng
   làm hỏng vĩnh viễn khả năng đọc log.
2. `expected_version` đếm lại từ 0 → xung đột phiên bản không có thật.

`PENDING`/`STALE` có cùng lớp lỗi nhưng KHÔNG được sửa ở đây — xem §7.

### 4.4. `reason` là ràng buộc NGHIỆP VỤ, không phải ràng buộc CỘT

Cột `reason` là `nullable=True`. Ràng buộc "bắt buộc khi thay một giá AUTO"
sống ở `BusinessDecisionStore.set_purchase_price`, nơi duy nhất biết lần ghi
là `MANUAL` hay `MANUAL_OVERRIDE`. Một `NOT NULL` ở tầng cột sẽ buộc phải bịa
một chuỗi cho mọi override đã ghi trước R2 — tức ghi vào audit trail một câu
mà không người nào từng nói.

### 4.5. Giá nhập tay `0` VẪN được chấp nhận

Brief §4.4 viết "là số VND dương … không dùng 0 làm sentinel". Phiên này đọc
mệnh đề đó là **cấm hệ thống dùng 0 để biểu diễn "chưa có giá"**, chứ không
cấm một người cố ý gõ 0. `parse_purchase_price` đã chấp nhận `0` từ trước với
lý do đã được nghiệm thu (hàng khuyến mại/quà tặng có giá nhập 0 là chuyện có
thật, ép nó thành "chưa nhập" sẽ khoá coverage dưới 100 % vĩnh viễn). Hai điều
mà brief thật sự đòi đều đúng và đều có test: `CHECK-R2-08` (ngoài bảng chưa
có giá tay ⟹ Pending, KHÔNG thành 0) và `CHECK-R2-16` (giá 0 từ Tracking vẫn
bị chặn). Ghi ra ở đây vì đây là chỗ DUY NHẤT phiên này đọc brief theo nghĩa
hẹp hơn câu chữ.

## 5. Thay đổi theo file

```text
app/modules/product/identity/mapping.py     +MappingStatus.OUT_OF_CATALOG
                                            +MappingSource.HUMAN_CONFLICT_RESOLUTION
app/modules/product/identity/identity.py    +PendingReason.OUT_OF_CATALOG_CONFIRMED
                                            +PendingReason.IDENTITY_CONFLICT
app/modules/product/identity/audit.py       +EventType.MARK_OUT_OF_CATALOG
app/modules/product/identity/commands.py    +MarkOutOfCatalog
app/modules/product/identity/store.py       nhánh MarkOutOfCatalog · _ACTIVE_STATUSES
                                            · mapping_source vào phép so INV-69
app/modules/product/identity/cli.py         +mark-out-of-catalog (CHECK-105D-22 c)
app/modules/product/identity/resolver.py    quyết định người ĐỨNG TRƯỚC alias.map
                                            · _tracking_authority_code · CONFLICT
app/modules/pricing/resolution/composition.py  +IDENTITY_OUT_OF_CATALOG
                                               +IDENTITY_CONFLICT
app/demo.py · app/owner_usability.py        nhận identity_store_view
tools/tracking/live_pull.py                 nhận identity_store_view
app/web/identity_gateway.py                 store_view · out_of_catalog_keys
                                            · mark_out_of_catalog · resolves_conflict
app/web/line_identity.py                    Decisions · bốn classification
app/web/business_store.py                   reason + MissingPriceReasonError
app/web/business_queries.py                 entered_by/reason vào line_details
app/web/business_presentation.py            trạng thái phân loại trên từng dòng
app/web/workspace_presentation.py           classification + hai affordance mới
app/web/server.py                           _identity_decisions · /ngoai-bang
                                            · bốn hàng đợi · view vào /run
tools/db/schema.py                          +kpi_purchase_price_override.reason
tools/db/migrations/versions/0008_…py        migration additive
```

## 6. Completion Gate

| ID | Nội dung | Status | Evidence |
|---|---|---|---|
| `CHECK-R2-01` | Mapping UI được resolver production dùng | PASS | E1 |
| `CHECK-R2-02` | Mapping lập tập mã daily-min, tra đúng `sale_date` | PASS | E1 |
| `CHECK-R2-03` | Mapping sống qua refresh/worker/restart/import lại | PASS | E1 |
| `CHECK-R2-04` | Mã đích không có trong catalog bị từ chối | PASS | E1 |
| `CHECK-R2-05` | Mâu thuẫn ra `CONFLICT`, không chọn bên thắng | PASS | E1 |
| `CHECK-R2-06` | `OUT_OF_CATALOG` tường minh, lưu bền, không hỏi lại | PASS | E1 |
| `CHECK-R2-07` | `OUT_OF_CATALOG` giữ doanh thu/số lượng | PASS | E1 |
| `CHECK-R2-08` | Ngoài bảng chưa có giá tay vẫn Pending, không phải 0 | PASS | E1 |
| `CHECK-R2-09` | Giá tay lấp thiếu và tính lại lợi nhuận đúng | PASS | E1 |
| `CHECK-R2-10` | `MANUAL_OVERRIDE` giữ `auto_price_at_entry` + provenance | PASS | E1 |
| `CHECK-R2-11` | AUTO xuất hiện sau không đè giá tay | PASS | E1 |
| `CHECK-R2-12` | Gỡ giá tay về AUTO hoặc Pending đúng tình trạng | PASS | E1 |
| `CHECK-R2-13` | Giá tay không lan sang dòng/đơn/ngày khác | PASS | E1 |
| `CHECK-R2-14` | Pending reason cũ không chặn lợi nhuận | PASS | E1 |
| `CHECK-R2-15` | Web/service/hàng đợi đọc cùng effective state | PASS | E1 |
| `CHECK-R2-16` | R1 không hồi quy | PASS | E1 |
| `CHECK-R2-17` | Full regression + migration/rollback | PASS | E1 |
| `CHECK-R2-18` | Independent Review PASS | NOT_TESTED | — |
| `CHECK-R2-19` | Owner nghiệm thu ba luồng production | NOT_TESTED | — |

Lệnh và output nguyên văn: `docs/sessions/S128-r2-phan-loai-va-gia-nhap-tay.md`
§5–§6.

## 7. Rủi ro giữ lại (ACCEPTED_RISK)

### AR-R2-01 — `SetPending` rồi `ConfirmMapping` làm log không đọc được

Lỗi có TRƯỚC R2 và KHÔNG do R2 tạo ra: `_project()` đẩy một mapping `PENDING`
ra khỏi `active`, nên lệnh kế tiếp khai `supersedes=None` và `INV-33` nổ ở mọi
lần đọc sau đó (bằng chứng: §7 của `S128`). R2 sửa đúng nhánh của mình
(`OUT_OF_CATALOG`) và KHÔNG sửa `PENDING`/`STALE`, vì:

- không đường nào từ giao diện web phát `SetPending` (chỉ CLI phát được);
- sửa nó đổi hành vi của `_discover_candidates` với các mapping `STALE` (chúng
  có `namespace`), tức một thay đổi hành vi ngoài Scope Lock của R2.

Ghi lại ở đây để R3 hoặc một task riêng xử lý, không để nó rơi mất.

### AR-R2-02 — mâu thuẫn chỉ đo được trên capture của LẦN CHẠY

`CONFLICT` hiện ra từ `pending_reasons` mà lần chạy gần nhất đã ghi. Nếu
Tracking đổi `alias.map` GIỮA hai lần chạy sổ, mâu thuẫn mới chỉ xuất hiện ở
lần chạy sau. Không dựng một vòng kiểm nền để phát hiện sớm hơn: tần suất
thấp, tác động là một dòng thiếu giá (không phải một số sai), và nhân viên
phát hiện được ở bước đối chiếu thủ công.

## 8. Đầu vào cho R3

- Một effective product identity cho mỗi dòng (`line_identity.state_of`).
- Một effective KPI purchase price (`BusinessLine.purchase_price`).
- `OUT_OF_CATALOG` KHÔNG bị loại khỏi báo cáo.
- Mapping/giá tay đã lưu bền, có provenance đầy đủ.
- Web và service dùng cùng effective state.

Giới hạn còn để R3: khoá dòng vẫn là
`(order_key, product_key, occurrence_index)`; một file sổ bị sửa thứ tự hoặc
đổi cách ghi vẫn có thể sinh khoá khác và làm quyết định cũ không khớp. R2 chỉ
cam kết bền khi mở lại, restart/redeploy và nạp lại CÙNG dữ liệu theo khoá
hiện hành (Brief §3).
