# S064 — REPORTS → TRACKING DATA CONTRACT V1 INTEGRATION

Nhánh: `claude/reports-tracking-contract-n2it7h`
Base SHA: `9d02f3e07a85814bb70ca9948725b6248cda87dd` — bằng đúng tip của nhánh
mặc định `claude/extract-upload-repo-gq2ws4` tại thời điểm mở phiên (không
tiến lên, không cần chứng minh ancestor). Working tree sạch trước khi sửa.
Không merge, không deploy.

## VERDICT

```text
CONTRACT_CLIENT_IMPLEMENTED        = YES
FIREBASE_DIRECT_PATH_RETIRED       = YES
REAL_TRACKING_CAPTURE_EXECUTED     = NO  (hai blocker môi trường, xem §5)
BH73804_REAL_TRACE_EXECUTED        = NO  (không có capture thật + không có sales file)
BH73804_PREFLIGHT_TRACE_EXECUTED   = YES
Verdict                            = IMPLEMENTATION_PASS_RUNTIME_PENDING
```

Không tuyên bố Production Acceptance. Không có N=1 nào được chạy trên dữ liệu
thật trong phiên này, nên không có gì để accept.

## 1. Thay đổi — một điểm, không phải một framework mới

Repair nằm gọn ở **một** hàm: `_http_fetcher()` trong
`tools/tracking/capture_purchase_price_history.py`. Đó vốn đã là đường mạng
DUY NHẤT của cả repo (`capture_tracking_catalog.py` import lại chính nó), nên
sửa transport ở đó là đủ để cả hai công cụ capture đổi nguồn cùng lúc — không
có acquisition framework thứ hai, không có client thứ hai.

TRƯỚC:

```text
GET <database_url>/<node>.json?auth=<TRACKING_RTDB_TOKEN>
```

SAU:

```text
GET <source_url>/api/xuat/<node>
Header: X-Report-Key: <TRACKING_REPORT_API_KEY>
```

`ALLOWED_NODES` là danh sách ĐÓNG bốn node của hợp đồng V1 (`board`, `alias`,
`purchase_price_baseline`, `purchase_price_history`). Một node ngoài danh sách
bị chặn tại client, không phát request.

Thay đổi khác, đều là hệ quả trực tiếp:

- `--database-url` → `--source-url` ở CẢ hai CLI. Không giữ alias cũ: tên
  `--database-url` nói rằng Reports còn đọc một database Firebase, điều đó
  không còn đúng và một người vận hành đọc `--help` phải thấy đúng sự thật.
  Không có caller nào ngoài test dùng cờ cũ (đã grep toàn repo).
- `TOKEN_ENV_VAR`/`TRACKING_RTDB_TOKEN` bị XOÁ khỏi mã. Không còn đọc biến
  môi trường đó ở bất kỳ đâu; `API_KEY_ENV_VAR = "TRACKING_REPORT_API_KEY"`
  thay chỗ.
- `--source-system-ref` mặc định `tracking/rtdb` → `tracking/api/xuat`, để
  provenance ghi trong artifact nói đúng nguồn đã đọc.
- Kiểm `Content-Type` phải là `application/json`. Một trang HTML trả 200
  (login/redirect/error page) là cách im lặng nhất để rác trở thành "capture
  thành công"; `json.loads` một mình không bắt được mọi biến thể.

**Không có fallback Firebase.** Hợp đồng lỗi → capture `FAILED`. Hai đường
nguồn song song đúng là thứ `INV-12` tồn tại để chặn, nên không dựng lại nó
dưới tên "fallback".

Ngân sách: **72 dòng code production chạm tới** (+50/−22, đã bỏ docstring,
comment, dòng trắng) trên trần 100. `CHANGE_BUDGET_EXCEEDED` = NO.

## 2. Cái gì KHÔNG đổi — và vì sao đó là điểm mạnh

Hợp đồng V1 trả `board` đã chiếu sẵn xuống `{name, alt[]}` với `alt` đã
normalize thành mảng — đúng hình dạng mà `_rows_from_board()` đã đọc từ
S063. Nên **không dòng nào của tầng dựng envelope phải sửa**:

- `_rows_from_board()`, `_alias_map_from()` — nguyên vẹn.
- `canonical_content_hash()`, `write_capture()` (`INV-11`) — nguyên vẹn.
- `load_tracking_catalog_capture()`, `TrackingCatalogSnapshot`,
  `ProductIdentityResolver`, History Reader — không chạm.
- `app/modules/**` — không chạm. Ranh giới `ADR-101` giữ nguyên: mạng chỉ
  tồn tại ở `tools/tracking/**`, và assertion import-graph
  (`CHECK-105D-17`) được chạy lại trong bộ test mới.

Bộ kiểm hình dạng nguồn vẫn giữ đủ: hợp đồng là lời hứa của một hệ thống
khác, không phải một bất biến của repo này.

## 3. Artifact bất biến — lần thử Firebase hỏng KHÔNG bị viết đè

`write_capture()` từ chối ghi đè (`INV-11`) và điều đó KHÔNG được nới ra để
lần capture qua API chạy được. Đường đúng là một file MỚI:

```text
lần thử cũ (Firebase/App Check)  = FAILED, capture_id cũ, còn nguyên
lần capture mới (hợp đồng V1)    = file mới, capture_id mới
```

`test_a_failed_artifact_is_never_overwritten_by_a_later_success` khoá đúng
điều này: sau khi một `FAILED` đã nằm trên đĩa, một envelope `COMPLETE` ghi
vào cùng đường dẫn phải nổ, và nội dung trên đĩa vẫn phải là `FAILED` với
`capture_id` cũ.

Ghi chú trung thực: artifact `FAILED` của phiên trước **không có trong repo**
(`data/tracking_catalog/` không tồn tại; nó nằm ở máy/phiên đã chạy). Phiên
này không tạo ra một artifact `FAILED` giả để "có bằng chứng" — không xoá gì,
cũng không bịa gì.

## 4. Tests — 21 test mới, tất cả 18 điểm của brief

`tests/test_tracking_contract_client.py` (mới). `urlopen` được thay tại chỗ:
thứ cần chứng minh ở đây là hình dạng request và tính fail-closed của mọi
nhánh lỗi, không phải endpoint production đang sống hay chết.

| # | Yêu cầu | Test |
|---|---|---|
| 1 | đúng source URL | `test_the_client_calls_the_contract_endpoint_not_a_firebase_node`, `test_a_trailing_slash_on_the_source_url_does_not_double_up` |
| 2 | header `X-Report-Key` | `test_the_secret_travels_only_in_the_report_key_header` |
| 3 | thiếu secret fail-closed | `test_a_missing_secret_fails_closed_without_sending_a_request` |
| 4 | sai key / 401 / 403 | `test_an_http_error_fails_closed[401,403]` |
| 5 | 404 fail-closed | `test_an_http_error_fails_closed[404]` + node ngoài hợp đồng chặn tại client |
| 6 | HTML bị từ chối | `test_an_html_response_is_rejected_even_with_status_200` |
| 7 | JSON hỏng bị từ chối | `test_a_malformed_json_body_is_rejected` |
| 8 | board rỗng bị từ chối | `test_an_empty_board_over_the_contract_is_failed_not_an_empty_catalog` |
| 9 | catalog COMPLETE | `test_a_catalog_capture_over_the_contract_is_complete_and_loadable` |
| 10 | `content_hash` | cùng test #9 (so với `canonical_content_hash()` thật) |
| 11 | alias map | cùng test #9 (qua `snapshot.alias_map()`) |
| 12–13 | baseline + history | `test_a_price_history_capture_over_the_contract_carries_both_nodes` |
| 14 | không còn query auth Firebase | `test_the_capture_tools_hold_no_firebase_transport_left` |
| 15 | không phụ thuộc `TRACKING_RTDB_TOKEN` | `test_the_rtdb_token_env_var_is_no_longer_an_operational_input` |
| 16 | secret vắng khỏi log/lỗi/artifact | `test_no_error_message_ever_carries_the_secret`, `test_the_secret_never_lands_in_a_capture_artifact`, `test_no_api_key_is_persisted_or_printed` |
| 17 | artifact FAILED được bảo toàn | `test_a_failed_artifact_is_never_overwritten_by_a_later_success` |
| 18 | `app/modules` không chạm mạng | `test_no_module_under_app_reaches_the_network` |

Điểm 15 cố ý được kiểm bằng HÀNH VI chứ không bằng grep chuỗi: đặt
`TRACKING_RTDB_TOKEN` mà không đặt `TRACKING_REPORT_API_KEY` rồi chạy CLI
thật → phải `FAILED` với `MISSING_API_KEY`. Một biến môi trường không còn
được đọc thì đặt nó vào cũng không cứu được lần chạy.

### Kết quả (E1)

```text
$ python3 -m pytest tests/test_tracking_contract_client.py -q
21 passed in 0.20s

$ python3 -m pytest tests/test_tracking_catalog_capture.py \
    tests/test_105e_price_composition.py tests/test_tracking_history_reader.py \
    tests/test_tracking_history_pipeline.py \
    tests/test_tracking_history_batch50_semantics.py \
    tests/test_post_cutover_validation.py -q
211 passed in 3.42s

$ python3 -m pytest -q
1273 passed, 11 skipped in 22.06s
```

Full suite bao gồm Product Identity, TASK-105D/105E, History Reader,
Post-Cutover Validator, Golden #1/#3/#4 và Batch 50. Không có regression.

## 5. Real capture — KHÔNG chạy được, hai blocker độc lập

Cả hai đều thuộc môi trường phiên, không thuộc mã:

1. **Không có secret.** `TRACKING_REPORT_API_KEY` vắng mặt trong môi trường.
   Không yêu cầu chủ dự án dán secret vào chat.
2. **Egress bị chặn.** Ngay cả một probe không key cũng không ra được:

```text
$ curl -s -o /dev/null -w "http=%{http_code}\n" \
    https://price.tinphatcrm.com/api/xuat/board
http=000
[agent-proxy] price.tinphatcrm.com:443 — connect_rejected
  "gateway answered 403 to CONNECT (policy denial or upstream failure)"
```

`http=000` là proxy từ chối CONNECT, **không phải** `403` của hợp đồng. Hai
thứ này không được nhầm lẫn: phiên này chưa từng chạm tới endpoint hợp đồng,
nên không có bằng chứng nào về hành vi production được tạo ra ở đây. Bằng
chứng production duy nhất đang có là bằng chứng phía Tracking đã dẫn trong
brief (board 200/3503 sản phẩm), không phải quan sát của phiên này.

Đường CLI đã được chạy thật trong phiên (E1) — không có key nên nó phải
FAIL CLOSED, và nó fail closed đúng cách:

```text
$ python3 -m tools.tracking.capture_tracking_catalog \
    --source-url https://price.tinphatcrm.com \
    --captured-by 'S064-preflight' --out <scratch>/cli_catalog.json
FAILED -> <scratch>/cli_catalog.json
failure_reason: SOURCE_UNAVAILABLE: MISSING_API_KEY: thiếu biến môi trường
TRACKING_REPORT_API_KEY — hợp đồng Tracking đòi header X-Report-Key; không
phát request không key.
exit=1

artifact: capture_status = FAILED
          source_system_ref = tracking/api/xuat
          keys = capture_id, capture_status, captured_at, captured_by,
                 content_hash, failure_reason, source_system_ref
```

Công cụ chị em cho cùng kết cục (`MISSING_API_KEY`, exit 1). Artifact vẫn là
một file HỢP LỆ đọc lại được, không phải file rỗng và không phải không có
file — đúng `INV-12`.

### Lệnh vận hành (chạy trên máy có secret + có egress)

```bash
export TRACKING_REPORT_API_KEY='<secret>'   # KHÔNG dán vào chat/PR/log

python3 -m tools.tracking.capture_tracking_catalog \
  --source-url https://price.tinphatcrm.com \
  --captured-by '<ai chạy>' \
  --out data/tracking_catalog/capture.json

python3 -m tools.tracking.capture_purchase_price_history \
  --source-url https://price.tinphatcrm.com \
  --captured-by '<ai chạy>' \
  --out data/tracking_price_history/capture.json
```

Chấp nhận capture danh mục: `capture_status = COMPLETE`, số dòng ≈ 3503,
`content_hash` khớp khi nạp lại, `alias_map` load được, không trường riêng tư
(`p`/`tp`/`_c`), `alt` là mảng. Nếu ra `FAILED`, đọc `failure_reason`:
`MISSING_API_KEY` / `SOURCE_UNAVAILABLE` / `MALFORMED_SOURCE` /
`EMPTY_SOURCE_NOT_ASSERTABLE` — mỗi tiền tố chỉ đúng một loại nguyên nhân.
KHÔNG ghi đè file cũ; ghi ra đường dẫn mới rồi thay có chủ đích.

## 6. BH73804 — preflight, KHÔNG phải real trace

`tools/analysis/validate_post_cutover.py --sales <file>` không chạy được:
không có capture thật, và không có file doanh số thật trong container
(`data/samples/` là gitignore, rỗng). Nên phần chạy được là câu hỏi duy nhất
xác định được offline: **với một board CÓ mã `T2109NT1G`, hai chuỗi raw của
`BH73804` đi tới kết cục nào** — chạy qua `ProductIdentityResolver` thật.

```text
board name = 'T2109NT1G'                             (mã làm tên)
  raw='T2109NT1G'              -> Resolved  TRACKING:T2109NT1G
  raw='Máy Giặt LG T2109NT1G'  -> PendingProduct  ONLY_SIMILARITY_EVIDENCE (1 candidate)

board name = 'Máy Giặt LG T2109NT1G'                 (giả định: tên = đúng chuỗi raw)
  raw='T2109NT1G'              -> Resolved  TRACKING:T2109NT1G
  raw='Máy Giặt LG T2109NT1G'  -> Resolved  TRACKING:T2109NT1G

board name = 'Máy giặt LG inverter 9kg T2109NT1G'    (tên thương mại dài)
  raw='T2109NT1G'              -> Resolved  TRACKING:T2109NT1G
  raw='Máy Giặt LG T2109NT1G'  -> PendingProduct  ONLY_SIMILARITY_EVIDENCE (1 candidate)
```

Điều này XÁC NHẬN dự đoán §XIV của brief, và nói thêm một điều: kết cục phụ
thuộc `board/<mã>/name` THẬT, thứ chỉ biết được sau một capture thật. Không
suy đoán giá trị đó ở đây.

`ONLY_SIMILARITY_EVIDENCE` là **TRUTHFUL PENDING**, không phải lỗi. Không
thêm regex extraction, fuzzy matching, AI matching hay contains-code shortcut
để `BH73804` AUTO — mọi thứ đó đều là mở authority mà không có evidence.

Preflight chạy bằng script tạm ngoài repo (không commit): nó không phải công
cụ vận hành, và một script chạy trên fixture không nên nằm cạnh các công cụ
chạy trên dữ liệu thật.

## 7. Xác nhận identity — dùng cơ chế đã có, không tạo cơ chế thứ hai

`TASK-105D` đã có đủ: `CONFIRM_MAPPING` là một trong bốn `confirmation_action`
(`app/modules/product/identity/commands.py:104`), có bề mặt CLI không cần con
trỏ (`app/modules/product/identity/cli.py:91`, `build_parser()` §239). Không
viết thêm gì.

**Đính chính một giả định của brief.** Cơ chế confirmation TỒN TẠI, nhưng
bề mặt của nó hôm nay là **hàm gọi được**, không phải một lệnh shell chạy
ngay: `cli.build_parser()` định nghĩa đủ tham số (`--actor-id`,
`--raw-identity-key`, `--client-request-id`, `--expected-version`,
`--candidate-rank`) và `cli.callable_surfaces()` ánh xạ cả bốn action, nhưng
**không có `main()` nào nối parser với các hàm đó** — `python3 -m
app.modules.product.identity.cli` không chạy được. Đã kiểm: không có `def
main`, không có `if __name__ == "__main__"` trong file. Đây là một khoảng
trống thật, ghi ra ở đây chứ không lấp bằng cách viết thêm entrypoint trong
phiên này (ngoài Scope Lock của một repair transport, và §XVIII cấm mở rộng).

Thao tác đúng bằng cơ chế đã có, đúng như bộ test `TASK-105D` gọi nó
(`tests/test_105d_audit_replay.py:446`):

```python
from app.modules.product.identity import cli
# resolution = kết quả resolve() của raw 'Máy Giặt LG T2109NT1G'
print(cli.render_candidates(resolution))   # đọc candidate + expected_version
cli.confirm(
    store, resolution,
    candidate_rank=1,                       # phải là TRACKING:T2109NT1G
    actor_id='<người xác nhận>',
    client_request_id='<uuid>',
    expected_version=<version hiện tại của store>,
)
```

`raw_identity_key` của chuỗi này bằng chính chuỗi đó (đã tính bằng
`raw_identity_key()` thật); `normalized_matching_aid` = `máy giặt lg
t2109nt1g`. Xem candidate TRƯỚC để xác nhận hạng 1 đúng là
`TRACKING:T2109NT1G` — không confirm mù.

Đây là **OWNER ACTION hợp lệ**, không phải implementation failure: hệ thống
đang từ chối tự gán một identity mà nó chỉ có bằng chứng similarity.

## 8. Public Purchase — blocker riêng, KHÔNG phải Tracking transport

```text
PUBLIC_PURCHASE_VERSION_REQUIRED
```

Chặn ở `app/modules/pricing/resolution/composition.py:349` — cổng **AND** ba
nguồn trong `_resolve_eligible()`:

```python
if catalog is None or pp_version is None or view is None:
    ... IDENTITY_SOURCES_UNAVAILABLE
```

`data/public_purchase/source_version.yaml` không tồn tại (thư mục
`data/public_purchase/` cũng không). Không bịa một `PublicPurchaseSourceVersion`
để `BH73804` chạy được — làm thế là chế ra authority về giá nhập.

Hệ quả phải nói rõ: **kể cả khi capture Tracking thật thành công**, `BH73804`
vẫn dừng ở `IDENTITY_SOURCES_UNAVAILABLE` chừng nào Public Purchase còn vắng.
Đây là đúng blocker mà `S063` đã ghi (`D-02` của `TASK-105E`), không phải một
gap mới, và KHÔNG được nhầm với transport: transport là PASS.

## 9. Blocker còn lại

| # | Blocker | Loại | Ai gỡ |
|---|---|---|---|
| 1 | `TRACKING_REPORT_API_KEY` vắng trong môi trường phiên | môi trường | vận hành (chạy local) |
| 2 | Egress tới `price.tinphatcrm.com` bị network policy chặn | môi trường | vận hành (chạy local) |
| 3 | Không có file doanh số thật chứa `BH73804` trong container | dữ liệu | vận hành |
| 4 | `PUBLIC_PURCHASE_VERSION_REQUIRED` | dữ liệu/owner | chủ dự án |
| 5 | `board/<mã>/name` thật của `T2109NT1G` chưa biết | dữ liệu | tự trả lời khi có capture |
| 6 | `app/modules/product/identity/cli.py` có `build_parser()` nhưng KHÔNG có `main()` — bề mặt confirm hôm nay là hàm gọi được, không phải lệnh shell | mã (ngoài scope phiên) | một task riêng, xem §7 |

Không blocker nào trong số này sửa được bằng mã trong phiên này, và không cái
nào là `ARCHITECTURE_CHANGE_REQUIRED` hay `DATA_INTEGRITY_RISK`.

## 10. NEXT ACTION

Chạy hai lệnh capture ở §5 trên máy có secret + egress. Sau đó chạy
`validate_post_cutover.py` với file doanh số thật trên `BH73804`, đọc kết quả
identity, và nếu ra `ONLY_SIMILARITY_EVIDENCE` thì dùng đúng lệnh `confirm` ở
§7. Public Purchase (§8) đi song song và độc lập.
