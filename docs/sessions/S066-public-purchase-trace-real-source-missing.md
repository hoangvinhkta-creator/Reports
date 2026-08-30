# S066 — PUBLIC PURCHASE TRACE: REAL_SOURCE_MISSING (BH73804 blocked)

Nhánh: `claude/reports-tracking-contract-n2it7h` (tiếp tục `S064`/`S065`,
cùng task lineage, không mở task mới). Base SHA của phiên này = tip của
`S065`: `b0f83d6680629823915cb44050f701b76e2d1d06`. Working tree sạch trước
khi trace. **0 dòng production code sửa** — phiên này là TRACE + OPERATION
thuần, không REPAIR (đúng §XII của brief: ưu tiên trace, không sửa code nếu
không cần).

## VERDICT

```text
CLASSIFICATION       = CASE B — REAL_SOURCE_MISSING
IMPLEMENTATION        = ĐẦY ĐỦ, FROZEN, INTEGRATED (TASK-105B/105D/105E)
REAL_DATA             = CHƯA TỪNG ĐƯỢC CUNG CẤP (xác nhận bằng lịch sử
                         PROJECT_PROGRESS/PROJECT_DECISIONS, không phải suy
                         đoán của phiên này)
PUBLIC_PURCHASE_STATUS = PUBLIC_PURCHASE_VERSION_REQUIRED (không đổi)
BH73804_STATUS         = BLOCKED_AT_GATE — không tiến được qua
                          IDENTITY_SOURCES_UNAVAILABLE
```

**Không fabricate.** Không có version_id, không có product/price row nào
được tạo trong phiên này.

## 1–10. Trace (bắt buộc trả lời bằng code evidence)

**A. Public Purchase về mặt nghiệp vụ là dữ liệu gì?**
Một nguồn giá nhập **CÔNG KHAI, ĐỘC LẬP VỚI TRACKING** — theo `DEC-156` §1
(`D-01`/`OR-01`, APPROVED): "Owner làm rõ mô hình production thật có hai
product namespaces và Public Purchase vừa là identity source độc lập vừa là
price fallback." Nó là MỘT nguồn versioned mang HAI projection cùng lúc:
identity (E-B: `product_code`/`product_name`/`aliases`) và giá
(E-C: `product_key`/`effective_from`/`effective_to`/`purchase_price`), cùng
`version_id`, cùng `content_hash` (`app/modules/product/identity/
public_purchase.py:1-28`, `docs/spec/TASK-105D-DATA-CONTRACT.md` §D-01).

**B. Ai/nguồn nào tạo dữ liệu đó?**
**Chủ dự án (Tín Phát) cung cấp trực tiếp** — không phải một hệ thống ngoài,
không phải Tracking. `docs/tasks/TASK-108B-eligible-costs-owner-definition.md`
§38.4: `config/prices.yaml` được đánh dấu "**MỚI** — bảng giá **chủ dự án
cấp**". `docs/spec/TASK-105D-DATA-CONTRACT.md` §3.3 câu 11: "Ai được publish?
Quyền `PUBLIC_PURCHASE_SOURCE_PUBLISH`. Phase 1: role `ADMIN`" — publish là
một **hành động Owner có phân quyền**, không phải một bước kỹ thuật Reports
tự làm.

**C. File/source thực tế nằm ở đâu?**
`data/public_purchase/source_version.yaml` — một đường dẫn committed-repo
DUY NHẤT (`app/modules/pricing/resolution/sources.py:84`,
`PUBLIC_PURCHASE_SOURCE_PATH`). Khác Tracking (một file MỚI mỗi lần capture,
`capture_id` bất biến): Public Purchase là một file, git-versioned tại chỗ —
`D-02` cho phép "không bắt buộc một file vật lý duy nhất" về mặt kiến trúc,
nhưng implementation hiện tại (`load_public_purchase_source()`) chỉ đọc ĐÚNG
một đường dẫn cố định.

**D. `source_version.yaml` có schema chính xác thế nào?**
Đã FROZEN tại `docs/spec/TASK-105D-DATA-CONTRACT.md` §3.2, implementation
khớp 1:1 tại `public_purchase.py:65-78` (`_TOP_LEVEL_KEYS`):

```yaml
source_id: PUBLIC_PURCHASE          # REQUIRED IMMUTABLE (mặc định nếu vắng)
version_id: PP-<YYYYMMDD>-<NN>      # REQUIRED IMMUTABLE, duy nhất toàn cục
status: PUBLISHED                    # DRAFT | PUBLISHED | ROLLED_BACK
published_at: <ISO datetime>         # REQUIRED khi PUBLISHED
published_by: <actor>                # REQUIRED khi PUBLISHED
supersedes: <version_id cũ>          # OPTIONAL
rollback_of: <version_id bị rollback># OPTIONAL
note: <text>                         # OPTIONAL
products:                            # REQUIRED, KHÔNG được rỗng (INV-02)
  - product_code: <mã>
    product_name: <tên>
    aliases: [<alias>, ...]          # OPTIONAL
    active_from: <date>              # OPTIONAL
    active_to: <date>                # OPTIONAL
prices:                              # REQUIRED, KHÔNG được rỗng (INV-02)
  - product_key: <mã, phải khớp một product_code/alias trong CÙNG version>
    effective_from: <date>
    effective_to: <date | null>      # null = còn hiệu lực
    purchase_price: <số>
    source: <text tuỳ chọn>
```

Ví dụ minh hoạ nguyên văn đã có sẵn trong spec đã FROZEN
(`docs/spec/TASK-105D-DATA-CONTRACT.md` §D-02, sản phẩm `KG36A2` — dữ liệu
minh hoạ của spec, KHÔNG phải dữ liệu thật của phiên này).

**E. `version_id` được tạo theo nguyên tắc nào?**
Convention từ spec: `PP-<YYYYMMDD>-<NN>`, đơn điệu tăng trong một
`source_id`, IMMUTABLE sau publish (§3.3 câu 2). **Ghi chú trung thực:**
loader code (`_require_text`) chỉ ép buộc "chuỗi không rỗng" — KHÔNG có
regex nào ép định dạng `PP-YYYYMMDD-NN` ở tầng kỹ thuật. Đây là một convention
tài liệu hoá, chưa phải một gate thực thi được. Không phải blocker cho
BH73804 (Owner tuân theo convention khi publish, không cần sửa mã), nên
KHÔNG repair trong phiên này (ngoài phạm vi CASE B).

**F. price rows được lấy từ đâu?**
Từ chính khối `prices` của `source_version.yaml` — do chủ dự án cấp. KHÔNG
có đường nào lấy `price_rows` từ Tracking (`purchase_price_baseline`/
`purchase_price_history`). Hai nguồn không giao nhau trong code: `sources.py`
đọc Tracking capture và Public Purchase YAML qua hai hàm độc lập
(`load_tracking_catalog_capture`/`load_public_purchase_source`), không hàm
nào gọi hàm kia.

**G. Effective-date semantics là gì?**
Khoảng **đóng** `[effective_from, effective_to]`; `effective_to = null` =
còn hiệu lực (`FilePriceProvider`, FROZEN `DEC-153`, dùng lại nguyên —
`OD-105B-01` Q1-A). Tra theo `sale_date` của đơn (P05). Giá hiện tại KHÔNG
được backfill một đơn lịch sử (P07) — không có nhánh `latest`/`nearest`.

**H. Loader validate những gì?**
`PublicPurchaseSourceLoader.load()` (`public_purchase.py:157-221`):
top-level phải là mapping; khoá lạ → lỗi (`unknown_top_level_key`); thiếu/
sai kiểu/**rỗng** `products` hoặc `prices` → lỗi LOAD (`INV-02`, KHÔNG bao
giờ trở thành "danh mục rỗng" hợp lệ); `version_id` bắt buộc non-empty;
`product_code` unique cả trên giá trị thô (`INV-04`) lẫn sau `fold()`
(`INV-05`); alias không được đụng `product_code` khác (`INV-09`); mọi
`price_rows[*].product_key` phải khớp một `product_code`/alias trong CÙNG
version (`INV-06`, referential integrity).

**I. Có tool/CLI publication hiện hữu hay chưa?**
**CHƯA.** Đã grep toàn bộ `tools/` và `app/modules/product/identity/` —
không có script "publish". `load_public_purchase_source()` chỉ ĐỌC một file
tĩnh đã có sẵn trên đĩa; không có cơ chế ghi/version/audit publish nào được
implement. Đây là một khoảng trống ĐÃ ĐƯỢC BIẾT (spec đặt "publish" là một
quyền `PUBLIC_PURCHASE_SOURCE_PUBLISH` tương lai cho role `ADMIN` — chưa xây
UI/CLI cho quyền đó) chứ không phải một lỗ hổng mới. **Không phải blocker
của BH73804**: đại diện vật lý được khuyến nghị của `D-02` là "một file YAML"
— Owner (hoặc người thay mặt Owner) có thể tự tay đặt file đúng schema vào
đúng đường dẫn mà không cần CLI, giống cách `config/*.yaml` khác được sửa.

**J. Có real data trong repo/local artifacts hiện tại đủ để publish legitimate
version hay chưa?**
**KHÔNG.** `data/public_purchase/` không tồn tại trong checkout này. Tìm
toàn bộ lịch sử `PROJECT/PROJECT_PROGRESS.md`/`PROJECT/PROJECT_DECISIONS.md`
xác nhận: dòng 2621 của `PROJECT/PROJECT_PROGRESS.md` — *"NEXT AUTHORIZED ACTION = chờ Owner cấp
bảng giá production thật"*; dòng 2660 — *"Còn mở, không phải code blocker:
bảng giá production thật của chủ dự [án]"*; `PROJECT/PROJECT_DECISIONS.md:5816`
(`DEC-156` §12) xác nhận lại: *"data dependency bảng giá production thật vẫn
mở"* cho `TASK-105B`. Không có dòng nào trong toàn bộ lịch sử project ghi
nhận việc chủ dự án đã cấp bảng giá thật. Dữ liệu duy nhất từng xuất hiện
trong test/fixture (`PPC-1000`, `KG36A2`) là dữ liệu tổng hợp/minh hoạ, tự
khai rõ trong docstring của chính fixture (`tests/support/identity_fixtures.py`
§1: *"Toàn bộ dữ liệu ở đây là tổng hợp"*).

## 2. Phân biệt Tracking vs Public Purchase (§III của brief)

Đã kiểm bằng code, không suy đoán:

```text
sources.py: load_tracking_catalog_capture() và load_public_purchase_source()
            là hai hàm ĐỘC LẬP, đọc hai đường dẫn khác nhau
            (data/tracking_catalog/ vs data/public_purchase/), không hàm
            nào gọi hàm kia.

composition.py (_tracking_branch): giá cho identity TRACKING đến TỪ
            TrackingHistoryPriceProvider (đọc purchase_price_baseline/
            purchase_price_history THẬT của Tracking) — P03 fallback sang
            Public Purchase bị CHẶN có chủ đích (VENDOR_SOURCE_NOT_AUTHORIZED
            — TASK-105C chưa cấp phép, "chưa hỏi" ≠ "đã hỏi và không có").
```

**Không có đường nào trong code hiện tại lấy dữ liệu Tracking rồi đóng gói
lại dưới namespace `PUBLIC_PURCHASE`.** Không tạo đường đó trong phiên này —
làm vậy sẽ vi phạm chính `D-01`/`OR-01` (hai namespace độc lập) mà `DEC-156`
đã APPROVED.

## 3. Vì sao Public Purchase là hard gate dù giá BH73804 (nếu resolve) sẽ đến
   từ Tracking, không phải Public Purchase

Phát hiện quan trọng nhất của phiên trace này, đáng ghi lại vì phản trực
giác: `ProductIdentityResolver.__init__` (`app/modules/product/identity/
resolver.py:144-155`) nhận `pp_version: PublicPurchaseSourceVersion`
**KHÔNG `Optional`** — resolver không dựng được nếu thiếu nó, vì đây là một
phần bề mặt candidate-discovery cho CẢ HAI namespace (kể cả một raw string
cuối cùng resolve về `TRACKING:<mã>` vẫn cần Public Purchase để loại trừ khả
năng đó là một mã Public Purchase). `PostCutoverPriceComposition
._resolve_eligible()` (`composition.py:340-349`) vì thế chặn ở cổng **AND**
trên CẢ BA nguồn trước khi chạm dòng nào — không phải vì Public Purchase
*content* sẽ được dùng để định giá `T2109NT1G` (nó sẽ không, theo §2 ở
trên), mà vì thiếu nó làm cho bước RESOLVE IDENTITY tự nó không thực hiện
được, không riêng bước định giá.

**Hệ quả:** không có cách nào "publish một version rỗng/tối giản không ảnh
hưởng gì" để mở gate — `INV-02` cấm `products`/`prices` rỗng (LỖI LOAD),
nên MỌI version hợp lệ đều phải mang ít nhất một dòng identity + một dòng
giá THẬT. Không có version giả vô hại nào khả dĩ trong kiến trúc hiện tại.

## 4. Changes made

**KHÔNG.** 0 file `app/**`/`config/**`/`data/**` sửa. 0 dòng production code.
Chỉ tạo: file session doc này và một mục trong `PROJECT/PROJECT_PROGRESS.md`.

## 5. Production LOC

**0.**

## 6. Public Purchase status

`PUBLIC_PURCHASE_VERSION_REQUIRED` — không đổi, xác nhận lại bằng trace đầy
đủ thay vì suy đoán. Implementation (`PublicPurchaseSourceLoader`,
`PublicPurchaseSourceVersion`, referential integrity, composition wiring)
đầy đủ, FROZEN (`DEC-153`), INTEGRATED. Blocker DUY NHẤT là dữ liệu thật —
CASE B.

## 7. Tracking source status

Không đổi từ `S065`: **RUNTIME_REPAIR_READY**, real production capture
(`COMPLETE`, catalog + price history) đã chạy trên Mac theo evidence của
prompt phiên này (`capture_contract_v1_prod_2.json`). Các artifact đó KHÔNG
nằm trong checkout của phiên này (environment separation — §VI của brief) —
không coi đó là source missing.

## 8. BH73804 real/preflight status

**BLOCKED_AT_GATE.** Không chạy được `validate_post_cutover.py` thật: (a)
Public Purchase gate chặn trước khi chạm dòng nào (§3 ở trên) — dù có real
Tracking artifacts trên Mac, composition vẫn trả `IDENTITY_SOURCES_UNAVAILABLE`
cho MỌI dòng, kể cả BH73804; (b) không có sales file thật trong checkout của
phiên này (`So_chi_tiet_ban_hang (4).xlsx` không có ở đây — cần locate/verify
trên Mac trước, không fabricate fixture thay thế). Không có gì mới để chạy
preflight thêm so với `S064` §6 (không có thay đổi code identity resolution
kể từ đó).

## 9. Product Identity result

Không đạt tới (chặn ở gate, §8). Dự đoán từ `S064` §6 (không đổi, vì
`ProductIdentityResolver`/`ProductIdentityLoader` không sửa gì kể từ đó) vẫn
là tài liệu tham khảo hợp lệ: `"T2109NT1G"` → `Resolved TRACKING:T2109NT1G`;
`"Máy Giặt LG T2109NT1G"` → phụ thuộc `board/T2109NT1G/name` THẬT, có thể
`ONLY_SIMILARITY_EVIDENCE`.

## 10. Purchase Price result

Không đạt tới.

## 11. KPI result

Không đạt tới.

## 12. Review Queue result

Không quan sát được (cần real E2E). Nếu chạy, mọi dòng post-cutover (không
riêng BH73804) sẽ vào Pending/Review Queue với `reason =
IDENTITY_SOURCES_UNAVAILABLE` — canonical, không phải queue thứ hai.

## 13. Remaining blockers

| # | Blocker | Loại |
|---|---|---|
| 1 | Bảng giá Public Purchase thật (≥1 product + ≥1 price row thật, đúng schema §1.D) chưa được chủ dự án cung cấp | **OWNER — dữ liệu** |
| 2 | Publish là hành động có phân quyền (`PUBLIC_PURCHASE_SOURCE_PUBLISH`, role `ADMIN`) — không phải bước Reports/Claude tự thực hiện | **OWNER — quy trình** |
| 3 | Chưa có sales file thật (`So_chi_tiet_ban_hang (4).xlsx`) trong checkout của phiên này | môi trường — cần locate/verify trên Mac |
| 4 | Real Tracking artifacts (`capture_contract_v1_prod_2.json` ×2) không nằm trong checkout này | môi trường — chạy trên Mac |

Không blocker nào là `ARCHITECTURE_CHANGE_REQUIRED`, `DATA_INTEGRITY_RISK`,
hay `CHANGE_BUDGET_EXCEEDED`. Blocker 1–2 là `OWNER_DECISION_REQUIRED` đúng
nghĩa CASE D một phần (ai có authority publish) lồng trong CASE B (dữ liệu
chưa có) — nhưng bản thân "Public Purchase có authority nghiệp vụ hay không"
đã được `DEC-156`/`OR-01` trả lời dứt khoát (`APPROVED`), nên đây KHÔNG phải
CASE D thuần: authority nghiệp vụ đã rõ, chỉ dữ liệu và quyền publish còn
thiếu.

## 14. Owner action

**Cần, không phải implementation failure:**

1. Cung cấp ít nhất một dòng dữ liệu Public Purchase THẬT (product_code +
   product_name + ít nhất một price row hiệu lực) — schema đầy đủ ở §1.D.
2. Xác nhận/thực hiện publish (role `ADMIN` theo `DEC-124`, quyền
   `PUBLIC_PURCHASE_SOURCE_PUBLISH`) — đặt file đúng schema vào
   `data/public_purchase/source_version.yaml` với `version_id =
   PP-<YYYYMMDD>-<NN>`, `status: PUBLISHED`, `published_by: <actor>`.
3. Nếu chủ dự án muốn dùng `T2109NT1G`/`Máy Giặt LG T2109NT1G` làm ví dụ đầu
   tiên: xác nhận đây có phải sản phẩm có bán CÔNG KHAI (không riêng nội bộ
   Tracking) hay không — vì Public Purchase và Tracking là hai namespace độc
   lập theo thiết kế đã duyệt.

## 15. Final full SHA

`b0f83d6680629823915cb44050f701b76e2d1d06` — **không đổi**, phiên này không
tạo commit code. (Commit tài liệu của phiên này, nếu có, đứng SAU sha này.)

## 16. NEXT ACTION

Chờ Owner cấp bảng giá Public Purchase thật (§14 mục 1) và xác nhận publish
(§14 mục 2). Song song, trên Mac: locate/verify `So_chi_tiet_ban_hang (4).xlsx`
thật, xác nhận `data/tracking_catalog/capture_contract_v1_prod_2.json` và
`data/tracking_price_history/capture_contract_v1_prod_2.json` còn nguyên
(`INV-11`, không ghi đè). Khi cả ba có mặt, chạy:

```bash
python3 tools/analysis/validate_post_cutover.py \
  --sales "<đường dẫn thật So_chi_tiet_ban_hang (4).xlsx>" \
  --output <thư mục output> \
  --tracking-catalog data/tracking_catalog/capture_contract_v1_prod_2.json \
  --tracking-capture data/tracking_price_history/capture_contract_v1_prod_2.json \
  --public-purchase data/public_purchase/source_version.yaml
```

rồi soi kết quả cho `BH73804` cụ thể.
