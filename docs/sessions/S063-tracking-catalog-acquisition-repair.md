# S063 — IDENTITY SOURCE ACQUISITION REPAIR (Tracking catalog)

Nhánh: `claude/identity-source-acquisition-repair-qoiey4`
Base SHA: `116cc544b32ea26f090ed21577ff99f2fd0665a0` — bằng đúng tip của nhánh
mặc định `claude/extract-upload-repo-gq2ws4` tại thời điểm mở phiên; đã tích
hợp `TASK-105E`, Post-Cutover Validator V1 và bản sửa validator của Codex
(`d8b60f981a5b7a9737a8286121a8c2cc87dfd2fe`, đã xác nhận là ancestor). Không
merge, không deploy.

## VERDICT

```text
ACQUISITION_REPAIR_IMPLEMENTED   = YES
ROOT_CAUSE_CONFIRMED             = YES
REAL_TRACKING_CAPTURE_EXECUTED   = NO   (không có credential trong phiên)
Trạng thái vận hành              = WAITING_REAL_TRACKING_CATALOG_CAPTURE
```

## Root cause — đã trace, không suy đoán

`BH73804` cho `pending_reason = IDENTITY_SOURCES_UNAVAILABLE` vì
`PostCutoverPriceComposition._resolve_eligible()`
(`app/modules/pricing/resolution/composition.py:345-374`) chặn ở một cổng
**AND** trên ba nguồn:

```python
catalog = self._sources.tracking_catalog        # None
pp_version = self._sources.public_purchase      # None
view = self._sources.identity_store_view        # store rỗng, KHÔNG None
if catalog is None or pp_version is None or view is None:
```

`catalog` là `None` vì `load_tracking_catalog_capture()` trả `None` khi
`data/tracking_catalog/capture.json` không tồn tại — và **không có công cụ nào
trong repo ghi ra file đó**. Đây là một nửa ranh giới bị bỏ dở: `TASK-105D`
§4.1 vẽ ra hai phía (`tools/tracking/` ghi, `app/modules/` đọc), `TASK-105E`
xây phía đọc, phía ghi chưa bao giờ được xây.

Discovery trước phiên này nói đúng: `tools/tracking/capture_purchase_price_history.py`
chỉ chụp `purchase_price_baseline` + `purchase_price_history`, không chạm danh
mục. Đã tìm lại toàn bộ `tools/`, `scripts/`, `app/**/cli.py` — **không có**
cơ chế acquisition nào cho `TrackingCatalogSnapshot`. Repair là cần thiết,
không phải trùng lặp.

**Đính chính một tiền đề của đề bài.** Tracking catalog là blocker *đã được
trace*, nhưng không phải blocker *duy nhất*: cổng trên là AND, nên chừng nào
`PublicPurchaseSourceVersion` còn vắng thì `BH73804` vẫn
`IDENTITY_SOURCES_UNAVAILABLE` dù đã có capture danh mục. Phần Public Purchase
bên dưới trả lời vì sao đó **không** phải một implementation gap thứ hai.

## Repair — một công cụ, đúng phía bên kia ranh giới

`tools/tracking/capture_tracking_catalog.py` (mới; 178 dòng mã production, 298 dòng cả docstring).

```text
GET <database_url>/board.json    → khoá node = mã, cùng `name` và `alt[]`
GET <database_url>/alias.json    → `map`: <mã cũ> → <mã chính>
```

Đường nguồn lấy từ bằng chứng đã audit trong chính repo này — `DEC-147` §4
(`board/<MÃ>`, `board/<MÃ>/name`, `board/<MÃ>/alt[]`, `alias.map`) và `S024`
C-01 (13 nhánh gốc của RTDB). Không invent schema, không mở rộng.

Bảy quyết định đáng ghi:

1. **`inv` KHÔNG BAO GIỜ được hỏi tới.** `DEC-147` §2 xác định giá nhập kế
   toán nằm ở `inv.<cu|moi>.gia` / `.lo`. `TrackingCatalogSnapshot` §4.4
   không có trường nào chứa chúng, nên đọc về là thu thập dữ liệu không có chỗ
   dùng. `inv.map` cũng không được đọc, vì cùng lý do: hợp đồng chỉ có
   `alias_map_rows`.
2. **`board` trả cả cây, nhưng chỉ danh sách trắng được ghi ra.** `p/<NCC>`,
   `tp/ton`, `tp/chot`, `_c` đi qua bộ nhớ tiến trình và dừng ở đó — mỗi dòng
   được dựng từ `_IDENTITY_FIELDS = ("name", "alt")`, không phải từ một bản
   sao dict. Một test chấm điều đó trên envelope đã serialize.
3. **Không tái phát minh identity logic.** Khoá node đã là `normCode()` do
   chính Tracking ghi — chép nguyên văn (`D-04`). Và **không** áp `aliasOf()`
   để gộp dòng: `INV-16` đòi resolver tự thấy alias rồi sinh `MAPPING_STALE`,
   gộp sẵn ở tầng capture sẽ xoá mất tín hiệu đó.
4. **`present_in_board` luôn `True`.** Capture là ảnh chụp một thời điểm.
   Chiều `false` của `INV-14` được biểu đạt bằng "vắng khỏi capture mới", và
   `ProductIdentityResolver._present_in_board()` (`resolver.py:532-534`) đọc
   một mã vắng mặt thành `False` — hai cách viết cho cùng một kết quả.
5. **`board` rỗng là `FAILED`, không phải một danh mục rỗng.** RTDB trả cùng
   một `null` cho "nhánh không tồn tại" và "nhánh rỗng", nên từ dây không
   khẳng định được đây là một danh mục thật sự trống. Một danh mục rỗng
   COMPLETE sẽ làm MỌI sản phẩm Pending — đúng lớp lỗi `INV-12` tồn tại để
   chặn. Fail closed. Ngược lại, `alias` rỗng là hợp lệ: "chưa mã nào bị gộp"
   là trạng thái khởi đầu đúng, và `alias_map` là evidence phụ trợ.
6. **Bốn kết cục, hai giá trị enum.** `CaptureStatus` là enum ĐÓNG
   `{COMPLETE, FAILED}` và `INV-12` treo lên đúng nó; thêm một giá trị mới sẽ
   là đổi hợp đồng đã freeze. Nên phân biệt của §7 nằm ở tiền tố máy đọc được
   trong `failure_reason`: `SOURCE_UNAVAILABLE:` / `MALFORMED_SOURCE:` /
   `EMPTY_SOURCE_NOT_ASSERTABLE:`.
7. **Một đường mạng, một đường credential.** Công cụ import lại `_http_fetcher`,
   `write_capture`, `CaptureError` và `TOKEN_ENV_VAR` của
   `capture_purchase_price_history.py` thay vì chép lại — cả repo có đúng một
   `method="GET"`, đúng một `TRACKING_RTDB_TOKEN`, đúng một quy tắc `INV-11`.
   Công cụ cũ **không đổi một dòng nào**.

`content_hash` tính trên đúng nội dung được ghi ra (`rows` + `alias_map`),
không trên provenance — nên hai lần chụp cùng một nguồn cho cùng một hash dù
`capture_id`/`captured_at` khác nhau: hash trả lời "nguồn có đổi không", không
phải "đã chạy lại chưa". Nhánh `FAILED` vẫn mang `content_hash` vì loader đọc
trường đó **trước** khi rẽ nhánh.

## Public Purchase — trace kết luận

`PublicPurchaseSourceVersion` **không** thiếu acquisition mechanism. Nó là một
nguồn **file được publish**, không phải một lần chụp mạng:
`load_public_purchase_source()` đọc `data/public_purchase/source_version.yaml`
qua `PublicPurchaseSourceLoader.load()` — một YAML mang `source_id`,
`version_id`, `status`, `published_at/by`, và hai projection `products` +
`prices` cùng một `content_hash` (`D-01`/`OR-01`, `DEC-156` §1).

```text
production operator lấy nó từ đâu?  → bản publish của nguồn Public Purchase
                                       (import kế toán/danh mục), đặt tại
                                       data/public_purchase/source_version.yaml
mechanism đã tồn tại chưa?          → CÓ — loader STRICT của INV-02 là cơ chế
absence hiện tại là gì?             → EXPECTED, không phải implementation gap
```

Vắng mặt hôm nay đúng nghĩa "chưa ai publish version đầu tiên". Không dựng
capture tool cho nó, và **không** fabricate dữ liệu PP. Nhưng phải ghi rõ:
vì cổng ở `composition.py:349` là AND, `BH73804` chỉ thoát khỏi
`IDENTITY_SOURCES_UNAVAILABLE` khi **cả hai** nguồn có mặt.

## Purchase price history

`tools/tracking/capture_purchase_price_history.py` giữ nguyên semantics, 0
dòng thay đổi. Không duplicate, không redesign. Nếu cần chạy `BH73804` tới
tầng giá sau khi identity resolve, operator cần thêm một lần capture history
thật — lệnh ở phần Runbook.

## Test

Focused: `tests/test_tracking_catalog_capture.py` — **34 test**, phủ đủ 13 mục
§13 chỉ thị: capture hợp lệ; hợp đồng §4.4; xác định (hash ổn định qua
`capture_id`/`captured_at`, thứ tự khoá RTDB không đổi kết quả, nguồn đổi thì
hash đổi); `SOURCE_UNAVAILABLE`; `MALFORMED_SOURCE` (6 hình dạng `board`, 5
hình dạng `alias`); auth/network failure; không secret nào được ghi hay in;
read-only là tính chất của mã; `board` rỗng phân biệt với không với tới được;
mã bị gộp giữ đồng thời ở `rows` và `alias_map`; loader production nuốt được
artifact; resolver production dựng được từ artifact và trả
`TRACKING:T2109NT1G`; capture `FAILED` chặn resolver thay vì làm rỗng danh
mục; không rò trường giá riêng tư.

Regression trên `116cc54` + thay đổi này:

```text
Product Identity / TASK-105D   218 passed
TASK-105E                       43 passed
Post-Cutover Validator          62 passed
Golden Baseline                 58 passed, 2 skipped
Golden #1/#3/#4                 16 passed
Batch 50                         5 passed
Toàn bộ suite                 1251 passed, 11 skipped   (base: 1217 + 34 mới)
```

## Đơn thật `BH73804` — chưa rerun được, và điều gì sẽ xảy ra khi rerun

Phiên này **không** có credential Tracking RTDB, nên **không** có lần capture
thật nào và **không** có rerun nào. Không fake, không tạo source giả.

Một phép dò trên chính resolver production (không phải một tuyên bố về dữ liệu
thật) cho biết trước kết quả, và nó **không** phải `RESOLVED`:

```text
product_raw = "Máy Giặt LG T2109NT1G", catalog có dòng T2109NT1G
  → PendingProduct(reason_code = ONLY_SIMILARITY_EVIDENCE)
     attempted_sources = ALIAS_MEMORY, TRACKING_CATALOG,
                         PUBLIC_PURCHASE_CATALOG, CANDIDATE_RANKING
product_raw = "T2109NT1G"
  → Resolved TRACKING:T2109NT1G
```

Đây là hành vi ĐÚNG theo `INV-01`/`D-04`: `product_raw` là một câu tiếng Việt,
`tracking_code` là một mã, và exact-match-only từ chối bắc cầu giữa hai thứ đó
bằng máy — chính tiền lệ mà Tracking đã thử (`extractCode()`) và bỏ hẳn.

Nên sau khi có capture thật, `BH73804` **vẫn** vào Review Queue, nhưng với một
`pending_reason` khác hẳn về chất: từ "chưa nối được nguồn" thành "đã hỏi cả
bốn nguồn và chỉ có bằng chứng similarity". Đường đi tiếp theo là **một
`confirmation_action` của người dùng Reports**, không phải một thay đổi mã.
Đó là finding kế tiếp; phiên này KHÔNG sửa trước, KHÔNG thêm fuzzy mapping,
KHÔNG special-case `T2109NT1G`.

## Runbook cho operator

Credential KHÔNG bao giờ đi vào repo hay prompt. Đặt vào biến môi trường của
phiên vận hành, rồi:

```bash
export TRACKING_RTDB_TOKEN='<token đọc RTDB>'   # bỏ qua nếu DB không đòi auth

# 1. Chụp danh mục Tracking (READ-ONLY; không chạm inv/phist/backup)
python -m tools.tracking.capture_tracking_catalog \
  --database-url 'https://<tracking-rtdb-host>' \
  --captured-by '<ai chạy lần này>' \
  --out data/tracking_catalog/capture.json

# 2. (khi cần tới tầng giá) chụp lịch sử giá — công cụ đã có, không đổi
python -m tools.tracking.capture_purchase_price_history \
  --database-url 'https://<tracking-rtdb-host>' \
  --captured-by '<ai chạy lần này>' \
  --out data/tracking_price_history/capture.json

# 3. Publish version Public Purchase đầu tiên (không có capture tool — đây là
#    một bản publish, không phải một lần chụp mạng)
#    → data/public_purchase/source_version.yaml

# 4. Chạy lại validator trên đơn thật
python tools/analysis/validate_post_cutover.py \
  --sales '<file đơn thật>' \
  --output '<thư mục artifact>' \
  --tracking-catalog data/tracking_catalog/capture.json \
  --tracking-capture data/tracking_price_history/capture.json \
  --public-purchase data/public_purchase/source_version.yaml
```

Công cụ trả exit code `0` chỉ khi `COMPLETE`; mọi kết cục khác trả `1` và in
`failure_reason` ra stderr. File capture là BẤT BIẾN — ghi đè bị từ chối; muốn
chụp lại thì ghi ra đường dẫn mới rồi thay thế có chủ đích.

## Blocker còn lại

```text
1. Chưa có credential Tracking RTDB trong phiên
   → WAITING_REAL_TRACKING_CATALOG_CAPTURE (không phải architecture blocker)
2. Chưa có version Public Purchase nào được publish
   → cổng AND ở composition.py:349 vẫn giữ BH73804 ở IDENTITY_SOURCES_UNAVAILABLE
3. "Câu tên hàng → mã model" vẫn cần một confirmation_action của người dùng
   → finding kế tiếp, KHÔNG sửa trong phiên này
```

Không merge. Không deploy.
