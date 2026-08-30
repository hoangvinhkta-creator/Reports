# S065 — RUNTIME REPAIR: 403 Forbidden trên client contract thật (curl PASS)

Nhánh: `claude/reports-tracking-contract-n2it7h` (tiếp tục `S064`, cùng task
lineage, không mở task mới). Base SHA của phiên này = tip của `S064`:
`cf1ad2881c9e2c7ad39a83eae38d9ef0a87dbb46`. Working tree sạch trước khi sửa.
Không merge, không deploy.

## 1. ROOT CAUSE

**Không phải** `MISSING_API_KEY`, **không phải** `WRONG_SECRET`, **không
phải** `EGRESS_BLOCKED` — runtime Mac đã bác bỏ cả ba (curl cùng
secret/cùng máy → `HTTP 200`).

**Là:** client Reports tự xưng `User-Agent: Python-urllib/<version>` và
không gửi `Accept` — đúng chữ ký thư viện HTTP mặc định mà WAF/Cloudflare
phía trước hợp đồng Tracking production chặn. `curl` gửi `User-Agent:
curl/<version>` + `Accept: */*` và qua lọt với CÙNG secret, CÙNG máy, CÙNG
URL — sự khác biệt duy nhất giữa hai request là hình dạng header, không phải
credential hay network path.

### Một giả thuyết đã điều tra và bị LOẠI TRỪ bằng bằng chứng — ghi lại để không lặp lại

Nghi vấn đầu tiên (hợp lý, đúng hướng checklist "case normalization"): tên
header `X-Report-Key` bị `urllib.request.Request(url, headers={...})` đổi
case, vì đường đó chạy `Request.add_header()` → `key.capitalize()` →
`X-Report-Key` thành `X-report-key`. Trace SÂU HƠN một tầng lộ ra
`urllib.request.AbstractHTTPHandler.do_open()`:

```python
headers = {name.title(): val for name, val in headers.items()}
```

Dòng này chạy NGAY TRƯỚC khi gửi, trên MỌI header, bất kể case đặt lúc dựng
`Request`. `"X-report-key".title() == "X-Report-Key"` — case luôn tự đúng
trên dây. Xác nhận bằng thực nghiệm: dựng một `http.server` cục bộ, gửi qua
cả hai đường (constructor `headers={...}` và gán thẳng
`request.headers[...]`), đọc lại chuỗi header thô thật sự nhận được ở tầng
socket — CẢ HAI đều cho `X-Report-Key` (case đúng, giống hệt nhau). Test khoá
lại phát hiện này: `test_the_header_name_reaches_the_socket_with_its_exact_case`.

## 2. Evidence

### 2a. So sánh request curl (PASS) vs urllib mặc định (403), bắt bằng server cục bộ

```text
curl -H "X-Report-Key: abc123" http://<local>/
  Host: <local>
  User-Agent: curl/8.5.0
  Accept: */*
  X-Report-Key: abc123

urllib mặc định (Request(url, headers={"X-Report-Key": key}))
  Accept-Encoding: identity
  Host: <local>
  User-Agent: Python-urllib/3.11
  X-Report-Key: abc123
  Connection: close
```

Khác biệt THẬT: `User-Agent` (curl tự xưng chính nó; urllib tự xưng
`Python-urllib`) và `Accept` (curl gửi `*/*`; urllib mặc định KHÔNG gửi
`Accept` nào). Đây đúng là hai điểm mà checklist của brief đã chỉ tên: "User-
Agent" và "Cloudflare behavior".

### 2b. Repair — end-to-end qua CLI thật, không mock

Không có egress thật tới `price.tinphatcrm.com` trong môi trường phiên này
(giữ nguyên từ `S064`), nên repair được xác nhận bằng một server local giả
lập đúng hình dạng hợp đồng và chạy `python3 -m
tools.tracking.capture_tracking_catalog` THẬT (subprocess, không import
trực tiếp hàm để mọi lớp — argparse, env var, `_http_fetcher`, `urlopen` thật
— đều được exercise):

```text
$ python3 -m tools.tracking.capture_tracking_catalog \
    --source-url http://127.0.0.1:<port> --captured-by e2e-test \
    --out <scratch>/e2e_catalog.json
COMPLETE -> <scratch>/e2e_catalog.json
exit=0

Header thật server nhận được:
  path: /api/xuat/board   User-Agent: TinPhat-Reports-TrackingClient/1.0   Accept: */*   X-Report-Key: có
  path: /api/xuat/alias   User-Agent: TinPhat-Reports-TrackingClient/1.0   Accept: */*   X-Report-Key: có
```

Đây KHÔNG phải bằng chứng production — nó chứng minh mã đúng hình dạng và
đường CLI hoạt động end-to-end, không hơn. Xác nhận production PASS vẫn cần
operator chạy lại thật (§7).

## 3. Files changed

```text
tools/tracking/capture_purchase_price_history.py   (sửa _http_fetcher() + docstring)
tests/test_tracking_contract_client.py              (2 test mới, 1 test sửa để không che lỗi)
docs/sessions/S065-runtime-repair-403-user-agent.md  (mới, file này)
PROJECT/PROJECT_PROGRESS.md                          (mục mới)
```

Không chạm `tools/tracking/capture_tracking_catalog.py` — nó dùng lại nguyên
`_http_fetcher()` nên tự động thừa hưởng repair (giống cách S064 đã thiết
kế: một đường mạng duy nhất cho cả hai công cụ).

## 4. Additional production LOC

**+8 / −1 = 9 dòng code** (đã bỏ docstring/comment/blank), trên nền 72 dòng
đã commit ở `S064`. Cộng dồn: 81 dòng trên trần 100 của `S064`+`S065` cho
cùng một task lineage (repair transport). `CHANGE_BUDGET_EXCEEDED` = NO.

## 5. Tests

`tests/test_tracking_contract_client.py`: **23 passed** (21 cũ + 2 mới).

- `test_the_header_name_reaches_the_socket_with_its_exact_case` (sửa lại,
  §1) — khoá kết luận ĐÃ LOẠI TRỪ giả thuyết case, bằng server thật.
- `test_the_client_sends_a_non_default_user_agent_and_an_accept_header`
  (mới) — regression test cho root cause thật: client không được tự xưng
  `Python-urllib`, phải gửi `Accept`. Đã XÁC NHẬN test này bắt được lỗi:
  revert tạm phần header của `_http_fetcher()` về bản cũ (không có
  `User-Agent`/`Accept` tường minh) → test FAIL đúng với thông điệp trỏ
  thẳng vào `Python-urllib`; áp lại repair → PASS.
- `test_the_secret_travels_only_in_the_report_key_header` (sửa) — quay lại
  so khớp case-insensitive CÓ CHỦ ĐÍCH (đã giải thích tại sao trong comment),
  không còn hàm ý sai rằng case là vấn đề.

```text
$ python3 -m pytest tests/test_tracking_contract_client.py -q
23 passed in 0.11s

$ python3 -m pytest tests/test_tracking_catalog_capture.py \
    tests/test_105e_price_composition.py tests/test_tracking_history_reader.py \
    tests/test_tracking_history_pipeline.py \
    tests/test_tracking_history_batch50_semantics.py \
    tests/test_post_cutover_validation.py -q
211 passed in 3.13s

$ python3 -m pytest -q
1275 passed, 11 skipped in 21.95s
```

Không regression trên Product Identity, TASK-105D/105E, History Reader,
Post-Cutover Validator, Golden #1/#3/#4, Batch 50.

## 6. Failed artifacts — không chạm

`data/tracking_catalog/capture.json`,
`data/tracking_catalog/capture_contract_v1.json`,
`data/tracking_catalog/capture_contract_v1_prod.json` — không nằm trong
checkout của phiên này (`data/tracking_catalog/` không tồn tại; các artifact
này sống trên đĩa cục bộ của operator, không được commit). Không có gì để
overwrite/delete trong repo, và phiên này không tạo bất kỳ file nào dưới
`data/`. `write_capture()` (`INV-11`, không đổi ở phiên này) vẫn từ chối ghi
đè — hành vi bảo toàn artifact `FAILED` cũ đã kiểm trong `S064`
(`test_a_failed_artifact_is_never_overwritten_by_a_later_success`) không đổi.

## 7. Exact operator command cho lần capture tiếp theo

```bash
export TRACKING_REPORT_API_KEY='<secret>'   # đã có trên máy — KHÔNG dán vào chat/log

python3 -m tools.tracking.capture_tracking_catalog \
  --source-url https://price.tinphatcrm.com \
  --captured-by '<ai chạy>' \
  --out data/tracking_catalog/capture_contract_v1_prod_2.json

python3 -m tools.tracking.capture_purchase_price_history \
  --source-url https://price.tinphatcrm.com \
  --captured-by '<ai chạy>' \
  --out data/tracking_price_history/capture_contract_v1_prod_2.json
```

## 8. Tên artifact mới đề xuất

`capture_contract_v1_prod_2.json` (catalog) và
`capture_contract_v1_prod_2.json` dưới `data/tracking_price_history/` (price
history) — hậu tố `_2` nói rõ đây là lần thử kế tiếp sau lần `_prod.json` đã
`FAILED` với `403`, không ghi đè, không gây nhầm lẫn về thứ tự thời gian.

## 9. VERDICT

```text
RUNTIME_REPAIR_READY
```

Local repair hoàn tất và đã kiểm bằng test thật (bao gồm CLI subprocess thật
qua một server local đúng hình dạng hợp đồng). **Không tuyên production
PASS** — operator phải chạy lại lệnh ở §7 trên máy có secret + egress thật;
kết quả `HTTP 200` + `capture_status = COMPLETE` mới là bằng chứng production
hợp lệ.
