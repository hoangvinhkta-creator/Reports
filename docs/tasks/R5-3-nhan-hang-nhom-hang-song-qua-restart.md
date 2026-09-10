# R5.3 — Hãng/Nhóm hàng phải sống qua restart, không chỉ qua một lần chạy

## Metadata

Status:
IMPLEMENTED

Current Status Reason:
Lỗi LUỒNG CHÍNH trên production đã sửa: nhãn hiển thị (`model_label` ·
`brand` · `category_label`) nay được lưu BỀN theo từng `run_id` trong chính
database đang giữ con số của kỳ, và tab Nhân viên dựng lại chúng từ đó khi
cache trên đĩa ephemeral của Render đã biến mất. File trên đĩa xuống hạng
CACHE; nó không còn là nguồn sự thật duy nhất.

`CHECK-R53-01` … `CHECK-R53-12` PASS (E1, bằng chứng nguyên văn ở
`docs/sessions/S150-r53-nhan-hang-nhom-hang-ben-vung.md` §4–§6).

`CHECK-R53-13` (Independent Review) và `CHECK-R53-14` (Owner nghiệm thu trên
production) `NOT_TESTED` — phiên triển khai KHÔNG tự đóng chúng.

Phase:
PHASE-01 — Engine tính toán

Task Mode:
MAJOR (repair lỗi production)

Difficulty:
3/5

Risk:
2/5

Blast Radius:
2/5 (`V4.1` §4 — chấm theo FAILURE PATH). Failure path của `R5.3`:

```text
capture danh mục Tracking của lần chạy
   ├─ catalog_display (cache đĩa, đã có từ R5.1 REPAIR-2)
   └─ tracking_display_snapshot (bản BỀN theo run_id, MỚI)
                                  → 3 ô hiển thị trên bảng kê tab Nhân viên
```

Nó DỪNG ở đó, và bốn tính chất CẤU TẠO giữ nó không đi xa hơn:

1. **Bản lưu chỉ mang NHÃN.** Bảng mới không có một cột tiền nào —
   `CHECK-R53-11` khẳng định điều đó bằng chính lược đồ, không bằng câu văn.
   Không đường tính tiền nào đọc nó.
2. **Không mở thêm dòng nào được nhận nhãn.** Phép chặn theo trạng thái
   mapping ở `workspace_presentation._catalog_field` KHÔNG bị chạm; đường
   ĐỌC MỚI đi qua đúng cổng cũ. `CHECK-R53-06`/`CHECK-R53-07` đo rằng một
   dòng chưa xác nhận, một dòng `OUT_OF_CATALOG` và một dòng có tên nhìn
   giống hãng/nhóm hàng đều vẫn là `—`, KỂ CẢ trên đường dựng lại.
3. **Không lời gọi Tracking nào thêm.** `CHECK-R53-04` đếm số lần
   `pull_live_captures` được gọi trong một lần chạy: đúng 1. `CHECK-R53-05`
   đo rằng đường DỰNG LẠI (render trang) không gọi Tracking lần nào.
4. **Migration ADDITIVE thuần.** `0012_tracking_display_snapshot` THÊM đúng
   một bảng; không cột nào của bảng cũ bị đụng, không backfill, không đọc
   một dòng dữ liệu cũ nào.

Nó KHÔNG phải `1/5` vì một nhãn sai gắn vào dòng sai sẽ dẫn người đọc tới kết
luận sai về cơ cấu hàng bán — và từ `R6`, ba trường ấy là khoá gộp của bảng cơ
cấu và bảng giỏ hàng.

Effective Risk:
LOW (Blast Radius quyết định — `V4.1` §4.1; không viện dẫn Golden để hạ bậc)

Project Profile:
PRODUCT

Review Budget lineage:
`R5.3` thuộc root lineage `R5`, và lineage ấy đã HẾT ngân sách review
(`2 allowed / 2 used / 0 remaining`). **Phiên này KHÔNG tự tiêu và KHÔNG tự
miễn một repair cycle** — cùng posture đã ghi cho `R5.1 REPAIR-2` (`S146`),
và vì cùng một lý do: defect do Owner phát hiện trên PRODUCTION SAU nghiệm
thu, không đến từ một vòng Independent Review. Xem §8 và
`PROJECT/REVIEW_BUDGET_LEDGER.md`. Đây là một câu hỏi governance cần
Owner/reviewer xác nhận, không phải điều phiên này được tự quyết.

Owner Authority:
Owner báo lỗi đã xác minh trên production: *"sau upload sổ và chạy báo cáo,
tab Nhân viên vẫn hiển thị `—` ở Model/Hãng/Nhóm hàng cho cả các dòng có mã
sản phẩm rõ ràng"*, kèm chỉ thị *"không được coi R5.1 cũ là đã hoạt động chỉ
vì code hoặc test cũ từng xanh"*.

Tracking dependency:
`main` @ `b7c5f3b0ef13548e4d378e392b6ccd2f1be0d946` (R5.2.2). Đã xác minh là
tổ tiên của `origin/main` hiện tại (`0f7347b`, R5.2.3). Hợp đồng
`chieuBoard()` xuất đúng năm trường `name` · `alt` · `model_label` · `brand`
· `category_label` — KHÔNG thiếu trường nào, nên `R5.3` KHÔNG chạm Tracking.

---

## 1. Nguyên nhân gốc

### Điều đã ĐÚNG từ trước, và bằng chứng

Toàn bộ chuỗi hợp đồng đã đúng, và phiên này đo lại từng tầng trên đường
THẬT trước khi sửa một dòng nào:

```text
tầng                             trạng thái trước R5.3   bằng chứng
Tracking chieuBoard()            ĐÚNG                    §4.1 (producer thật)
capture_tracking_catalog         ĐÚNG                    §4.2
loader (sources.py)              ĐÚNG                    §4.2
POST /run → catalog_display      ĐÚNG (R5.1 REPAIR-2)    §4.3
_catalog_labels → tab Nhân viên  ĐÚNG                    §4.3
```

Không tầng nào trong số đó là chỗ đứt. `R5.1 REPAIR-2` thật sự đã sửa đúng
thứ nó nói là đã sửa.

### Chỗ ĐỨT

`catalog_display` ghi bản chiếu ra MỘT FILE trên đĩa máy chủ
(`data/product_identity/tracking_display.json`). Trên Render, dịch vụ này
KHÔNG có persistent disk (`render.yaml`: *"KHÔNG có `disk:` — S071B
stateless"*). Đĩa ấy là ephemeral: mỗi lần deploy hay restart, file biến mất.

Con số của kỳ thì KHÔNG biến mất — chúng nằm trong PostgreSQL
(`HISTORY_DATABASE_URL`) và sống tiếp. Hệ quả là hai nửa của cùng một màn
hình có hai vòng đời khác nhau:

```text
tiền (order_line_current, …)   PostgreSQL   sống qua deploy
nhãn (tracking_display.json)   đĩa /app     CHẾT ở mỗi deploy
```

Và không đường nào dựng lại nửa đã chết. `catalog_display` chỉ được ghi bởi
`POST /run` và bởi `_tracking_snapshot()` (khi Owner mở bảng chọn), nên sau
một lần restart, MỌI dòng đã `CONFIRMED` hiện `—` ở cả Hãng lẫn Nhóm hàng —
kể cả khi Owner mở lại đúng báo cáo mình vừa chạy hôm qua — cho tới khi có ai
đó nạp lại sổ và chạy lại.

Đo trực tiếp, trên đường thật (`§4.3`, ĐỎ trước sửa):

```text
upload sổ → POST /run → tab Nhân viên   Mặt hàng "QLED 55Q6FA" · Hãng
                                        "Samsung" · Nhóm hàng "Tivi"
xoá đĩa ephemeral (đúng việc Render làm)
mở LẠI tab Nhân viên, CÙNG lần chạy ấy  Hãng "—" · Nhóm hàng "—"
```

### Vì sao test cũ vẫn XANH

`tests/test_r51_repair2_run_refreshes_projection.py` monkeypatch
`catalog_display.DEFAULT_DISPLAY_PATH` sang một `tmp_path` và KHÔNG bao giờ
dọn nó giữa lúc chạy và lúc render. Trong một tiến trình test, đĩa không bao
giờ biến mất — nên bộ kiểm không có một bài nào đo được điều mà Render làm
với đĩa. Đây là đúng nghĩa "code và test cũ từng xanh" mà chỉ thị của Owner
cảnh báo.

## 2. Scope Lock

TRONG phạm vi:

```text
tools/db/schema.py                    THÊM bảng tracking_display_snapshot
tools/db/migrations/versions/
  0012_tracking_display_snapshot.py   MỚI — migration ADDITIVE thuần
tools/db/__init__.py                  ALEMBIC_HEAD → 0012
app/web/history_store.py              +2 phương thức đọc/ghi bản chiếu bền
app/web/catalog_display.py            tách normalise(); thêm restore();
                                      thêm REASON_NO_STORE
app/web/server.py                     _durable_tracking_display(),
                                      _tracking_display(),
                                      _persist_tracking_display();
                                      _refresh_catalog_display trả tuple
app/web/workspace_presentation.py     +product_title (tooltip tên trên sổ)
app/web/templates/
  kinh_doanh_nhan_vien.html           +title trên ô Mặt hàng
tests/**                              bài mới + cập nhật 2 khẳng định đã
                                      đổi NGHĨA (không nới lỏng)
scripts/r53_crossrepo_smoke.py        MỚI — smoke xuyên hai repo
scripts/r51_crossrepo_smoke.py        cập nhật §5 theo nghĩa mới
docs/**, PROJECT/**                   governance
```

NGOÀI phạm vi (không đụng nếu chưa có Scope Expansion):

```text
Tracking (mọi thứ)                    READ-ONLY REFERENCE
công thức doanh thu/lợi nhuận/MIN/    FORBIDDEN
  coverage/chốt kỳ/import/export
logic phân loại R2/R3                 FORBIDDEN
product key / resolver / taxonomy /   FORBIDDEN — không tạo bản song song
  identity store / mapping
R6 (bảng cơ cấu, giỏ hàng, biểu đồ)   FORBIDDEN — R5.3 không làm R6
merge / deploy                        FORBIDDEN
Independent Review / Owner Acceptance FORBIDDEN — phiên này không tự đóng
```

## 3. Thiết kế đã triển khai

### 3.1 Một lượt `/run` — một lần pull, hai nơi lưu

```text
POST /run
  └─ _select_captures_for_run()      ĐÚNG MỘT lần pull Tracking (CHECK-R53-04)
       └─ capture danh mục của lần chạy này
            ├─ pricing / daily-min   (không đổi)
            ├─ resolver mapping      (không đổi)
            ├─ catalog_display.write()          → cache đĩa
            └─ _persist_tracking_display(run_id) → BỀN, khoá theo run_id
```

Cả hai nhánh lưu đọc từ CÙNG một snapshot đã nạp, trong cùng một lời gọi
`_refresh_catalog_display` — không có đường nào để hai nơi lưu chở nội dung
của hai capture khác nhau.

### 3.2 Đường đọc: cache trước, dựng lại sau

`server._tracking_display()` là cửa DUY NHẤT mà mọi tầng trình bày đi qua:

```text
catalog_display.read()   không rỗng ⟹ dùng luôn (rẻ, và nó ĐÚNG là bản chiếu
                                       của lần chạy gần nhất)
                         rỗng      ⟹ latest_tracking_display() → normalise()
                                       → restore() ghi lại cache → dùng
```

Điều kiện dựng lại HẸP có chủ ý: **cache rỗng**, không phải "cache thiếu vài
mã". Một cache CÓ dữ liệu nhưng thiếu mã mới xác nhận là một câu chuyện KHÁC,
và `R5.1 REPAIR-2` vòng 2 đã đo và nói ra nó bằng LỊCH SỬ ghi
(`last_write_status()`), không bằng nội dung. Dựng lại đè lên một cache đang
có sẽ xoá mất chính bằng chứng ấy và làm cảnh báo `kind="cu"` im lặng sai.

### 3.3 Capture không mang nhãn nào ⟹ KHÔNG ghi đè, ở CẢ HAI nơi

`catalog_display.write()` đã có luật này từ `R5.1 REPAIR-2` (giữ nguyên bản
chiếu đang có khi capture là artifact đời cũ). `_persist_tracking_display`
theo ĐÚNG luật đó. Hai nơi lưu lệch luật ở đây sẽ cho hai màn hình khác nhau
cho cùng một lần chạy, tuỳ vào việc đĩa còn hay mất — `CHECK-R53-09` đo trực
tiếp ca này.

### 3.4 Không cửa nào mới để đoán

Đường dựng lại KHÔNG có phép chặn riêng: nó trả về đúng cùng một `dict` mà
`catalog_display.read()` trả về, và `_catalog_labels()` / `_catalog_field()`
vẫn là hai cổng duy nhất quyết định dòng nào được nhận nhãn. Một mã chưa
khớp, xung đột, target cũ, `OUT_OF_CATALOG` hay ngoài catalog vẫn không có
khoá trong bảng nhãn của dòng, nên không có đường nào để nhãn chảy vào chúng
— trước hay sau restart (`CHECK-R53-06`, `CHECK-R53-07`).

## 4. Rủi ro còn lại (ACCEPTED, đã ghi)

### `AR-R5.3-01` — bản chiếu là của lần chạy GẦN NHẤT, không của lần chạy đã sinh ra kỳ đang xem

Bản BỀN được khoá theo `run_id`, nhưng tầng trình bày đọc bản của lần chạy
GẦN NHẤT, không tra ngược từ dòng đang hiển thị về lần chạy đã sinh ra nó.
Lý do: tầng nghiệp vụ (`business_service.period` → `PeriodData.details`)
không chở `run_id` xuống tới dòng, và luồn nó xuống là sửa đúng những đường
mà `R5.3` bị cấm chạm (§2).

Hệ quả thật: nếu Tracking đổi nhãn của một mã giữa hai lần chạy, một kỳ CŨ
mở lại sẽ hiện nhãn MỚI. Đây KHÔNG phải một hồi quy do `R5.3` gây ra — nó
đúng bằng hành vi của cache đĩa từ `R5` §5 (một file duy nhất, bị mỗi lần
chạy ghi đè), và nó là hành vi Owner đã nghiệm thu ở `CHECK-R51-26`. Nó cũng
là hành vi ĐÚNG theo `R5.1` §4: sửa ngành hàng xảy ra bên Tracking, và lần
capture kế tiếp chở giá trị mới sang.

**Cập nhật (`DEC-218`, 2026-09-10).** Independent Review `R5.3` đã nâng rủi
ro này thành `FIND-R53-01` (`REPAIR_REQUIRED`), đo được bằng hai probe HTTP
độc lập — xem `docs/reviews/R5-3-INDEPENDENT-REVIEW-RECORD.md` §3. Owner đã
xem xét bằng chứng đó cộng một bằng chứng vận hành MỚI phát sinh sau thời
điểm review: Tracking commit `1c36fa2` (cùng ngày) xoá đường sửa tay từng mã
khỏi UI (`data-viec="editR52"` không còn trong HTML, `boardRow()` không còn
dựng ô cho Nhóm hàng/Hãng), và đường tự động còn lại
(`r52ApDungBackfill`) tự loại trừ mọi mã đã có `category_provenance`/
`brand_provenance = 'manual'`. Điều kiện để `FIND-R53-01` xảy ra thật trong
quy trình vận hành hiện tại của Owner nay hẹp lại đáng kể (chỉ còn qua nút
Chuẩn hoá tự động, và chỉ với mã còn ở provenance `auto`). Owner quyết định
`ACCEPTED_RISK` cho `FIND-R53-01` trên cơ sở này — **không phải** vì đây là
hành vi kế thừa (lý lẽ đó đã bị review bác rõ ràng). Chi tiết đầy đủ:
`DEC-218`. Cơ chế lỗi trong code KHÔNG đổi — quyết định này có thể cần xem
lại nếu quy trình vận hành thay đổi (xem `DEC-218` §3).

### `AR-R5.3-02` — mất database là mất nhãn

Bản BỀN sống trong cùng database với con số của kỳ. Mất database là mất cả
hai, nên nhãn không tệ hơn tiền. Khi cả hai nơi lưu cùng vắng, cảnh báo
`kind="vang"` của `R5.1 REPAIR-2` vẫn nổi lên (`CHECK-R53-10`) — bảng không
bao giờ im lặng.

### `AR-R5.3-03` — môi trường không có history store

Máy dev chưa `alembic upgrade head` ⟹ `snapshot_repo is None` ⟹ không có
nhánh bền, và bằng chứng của run ghi `REASON_NO_STORE`. Hành vi khi đó ĐÚNG
BẰNG `R5.1 REPAIR-2`. Trên production nhánh này không xảy ra:
`REPORTS_REQUIRE_HISTORY_DB=1` làm container không lên nếu thiếu database.

## 5. Completion Gate

### Functional

#### CHECK-R53-01
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`tests/test_r53_durable_tracking_labels.py::
test_a_confirmed_line_shows_model_brand_and_category_after_one_run` +
`scripts/r53_crossrepo_smoke.py` §3 (producer Tracking THẬT → capture THẬT →
`POST /run` THẬT → tab Nhân viên; KHÔNG mở bảng chọn). Nguyên văn: `S150` §5.

Executed By:
Claude Code (S150)

Timestamp:
2026-09-10

#### CHECK-R53-02
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Restart sau lượt chạy vẫn hiển thị nhãn từ bản lưu của chính lượt đó —
`test_the_labels_survive_a_container_restart` (ĐỎ trước sửa) và
`r53_crossrepo_smoke.py` §4. Nguyên văn: `S150` §4.3, §5.

Executed By:
Claude Code (S150)

Timestamp:
2026-09-10

#### CHECK-R53-03
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Bản BỀN mang NGUYÊN VĂN nhãn của capture đã dùng, kèm `capture_id` —
`test_the_run_stores_the_labels_durably_with_the_capture_it_used`;
smoke §4 đo trên payload do CHÍNH `chieuBoard()` sinh.

Executed By:
Claude Code (S150)

Timestamp:
2026-09-10

#### CHECK-R53-04
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Đúng MỘT lần pull Tracking trong mỗi `/run` —
`test_exactly_one_tracking_pull_per_run` đếm trực tiếp lời gọi
`pull_live_captures`.

Executed By:
Claude Code (S150)

Timestamp:
2026-09-10

#### CHECK-R53-05
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Đường DỰNG LẠI không gọi Tracking — `test_the_rebuild_never_pulls_tracking`
thay `pull_live_captures` bằng một hàm ném lỗi rồi render trang.

Executed By:
Claude Code (S150)

Timestamp:
2026-09-10

#### CHECK-R53-06
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Chưa xác nhận / `OUT_OF_CATALOG` / tên nhìn giống hãng-nhóm hàng ⟹ `—`,
trước VÀ sau restart —
`test_an_unclassified_line_stays_dashed_even_when_its_name_looks_like_a_brand`,
`test_the_same_holds_after_a_restart`,
`test_an_out_of_catalog_line_gets_no_label_after_a_restart`; smoke §5.
Ca xung đột và target cũ giữ nguyên bằng chứng `R5.1`
(`tests/test_r51_category_label.py`, §5) — `R5.3` không chạm cổng chặn ấy.

Executed By:
Claude Code (S150)

Timestamp:
2026-09-10

#### CHECK-R53-07
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Có MIN nhưng KHÔNG `CONFIRMED` ⟹ vẫn `—`, dù bản chiếu đã mang đủ nhãn của
mã đó — `test_a_min_price_without_a_confirmed_mapping_earns_no_label`.

*Cập nhật `R5.4` (2026-09-10, `DEC-221`):* mệnh đề trên là ĐÚNG theo spec
lúc đó nhưng chính nó là lỗi production Owner báo sau merge: dòng khớp TỰ
ĐỘNG với Tracking (có MIN) không bao giờ có mapping `CONFIRMED`, nên không
bao giờ có nhãn. `R5.4` mở rộng điều kiện thành "mapping CONFIRMED HOẶC mã
lần chạy đã phân giải". Bài test này vẫn xanh nguyên (dòng trong bài CHƯA
khớp), chỉ docstring đổi. Xem `docs/tasks/R5-4-nhan-cho-dong-khop-tu-dong.md`.

Executed By:
Claude Code (S150)

Timestamp:
2026-09-10

#### CHECK-R53-08
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`CONFIRMED` nhưng `brand` vắng ⟹ hiện Nhóm hàng, Hãng `—` —
`test_a_confirmed_code_with_no_brand_shows_the_category_and_dashes_the_brand`
(đo SAU restart, tức trên đúng đường dựng lại).

Executed By:
Claude Code (S150)

Timestamp:
2026-09-10

#### CHECK-R53-09
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Capture legacy thiếu ba trường: không crash, không đoán, bằng chứng của run
ghi `NO_METADATA` ở CẢ hai nhánh lưu, và nhãn của lần chạy trước KHÔNG bị xoá
— `test_a_legacy_capture_without_the_new_fields_never_crashes_or_guesses`,
`test_a_legacy_capture_does_not_erase_labels_an_earlier_run_stored`.

Executed By:
Claude Code (S150)

Timestamp:
2026-09-10

#### CHECK-R53-10
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Xoá/làm hỏng cache ⟹ tiền, số dòng KHÔNG đổi và nhãn được dựng lại; mất CẢ
HAI nơi lưu ⟹ cảnh báo đúng nguyên nhân, không im lặng —
`test_wiping_or_corrupting_the_cache_moves_no_money`,
`test_a_broken_durable_row_degrades_to_dashes_not_to_an_error`,
`test_losing_both_places_still_warns_instead_of_going_silent`; smoke §4/§6.

Executed By:
Claude Code (S150)

Timestamp:
2026-09-10

#### CHECK-R53-11
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Bảng nhãn KHÔNG mang một cột tiền nào, và ghi đè theo `run_id` thay vì xếp
chồng — `test_the_durable_store_holds_no_money_column`,
`test_the_durable_store_keeps_one_row_per_run_and_returns_the_latest`,
`test_an_empty_durable_row_reads_back_as_empty_not_as_missing`.

Executed By:
Claude Code (S150)

Timestamp:
2026-09-10

#### CHECK-R53-12
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Full regression `3628 passed / 23 skipped / 0 failed` (nền `3608 passed /
23 skipped`, +20 bài); Golden `58 passed / 2 skipped`; smoke `R5.1`
`86 PASS / 0 FAIL`; smoke `R6` `29 PASS / 0 FAIL`; smoke `R5.3`
`25 PASS / 0 FAIL`; validators = baseline; `git diff --check` sạch.
Nguyên văn: `S150` §6.

Executed By:
Claude Code (S150)

Timestamp:
2026-09-10

### Review / Acceptance

#### CHECK-R53-13
Priority:
REQUIRED

Status:
ACCEPT_WITH_RECORDED_RISK

Evidence Level:
E2

Evidence:
Independent Review đã chạy trên HEAD `cb7639f88efa8c9fb24f414ac1b6d9f93e58f02e`
(nhánh `claude/r5-3-reports-metadata-review-8bp6be`, cùng commit với
`claude/r5-3-reports-brand-category-j37izs`). Kết luận `REPAIR_REQUIRED`:
`FIND-R53-01` — đường đọc bản chiếu nhãn (`_tracking_display`/
`latest_tracking_display`) không phân biệt theo `run_id`/kỳ, luôn trả bản
của lần chạy GẦN NHẤT toàn cục; đo được trực tiếp qua hai lần `/run` cho
hai kỳ khác nhau với cùng mã Tracking bị đổi nhãn giữa hai lần chạy — kỳ CŨ
hiện nhãn của kỳ MỚI, cả trước lẫn sau restart. Không đổi tiền/số dòng/MIN/
coverage/vân tay chốt kỳ; ảnh hưởng gộp Nhóm hàng của `R6` cho kỳ lịch sử.
Bốn chuỗi kiểm còn lại (luồng chính, restart/persistence, fail-closed,
hồi quy) đều PASS. Chi tiết đầy đủ, bằng chứng lệnh và repair tối thiểu:
`docs/reviews/R5-3-INDEPENDENT-REVIEW-RECORD.md`. Lineage `R5` đã hết ngân
sách repair-cycle (2/2, 0 remaining) — phiên review escalate theo
`governance/core/ESCALATION_PROTOCOL.md` thay vì tự mở repair cycle thứ ba;
quyết định tiếp theo thuộc Owner.

**Cập nhật Owner Decision (`DEC-218`, 2026-09-10):** Owner chọn `ACCEPTED_RISK`
cho `FIND-R53-01` (không `OWNER_EXTENSION`, không mở lineage riêng) — căn cứ
trên bằng chứng vận hành mới (Tracking `1c36fa2` xoá đường sửa tay từng mã
khỏi UI + khoá `manual provenance` trong `r52ApDungBackfill`), KHÔNG phải vì
hạ nhẹ finding theo lý lẽ kế thừa. Chi tiết đầy đủ: `DEC-218`; risk ghi tại
`AR-R5.3-01` (bổ sung). `R5.3` được phép tiếp tục sang merge/deploy.
`CHECK-R53-14` (Owner nghiệm thu production) đứng độc lập, KHÔNG bị quyết
định này thay thế.

Executed By:
Independent Review session (Claude Code), nhánh
`claude/r5-3-reports-metadata-review-8bp6be`; Owner Decision (`DEC-218`)
ghi lại bởi Claude Code, nhánh `claude/r5-3-owner-accepted-risk-find01`

Timestamp:
2026-09-10 (Independent Review); 2026-09-10 (Owner Decision)

#### CHECK-R53-14
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
Owner nghiệm thu lại trên production (upload sổ → `/run` → tab Nhân viên →
chờ một lần deploy → mở lại tab Nhân viên). Chỉ Owner đóng check này.

Executed By:
—

Timestamp:
—

## 6. Tiêu Chí Hoàn Thành (Exit Criteria)

- [x] 12/12 check triển khai REQUIRED PASS ở mức `E1`
- [x] Không có lỗi nghiêm trọng chưa xử lý
- [x] Tài liệu bắt buộc đã cập nhật (`PROJECT_PROGRESS`, `PROJECT_DECISIONS`,
      `REVIEW_BUDGET_LEDGER`, session handoff)
- [x] `CHECK-R53-13` Independent Review — ĐÃ chạy, `REPAIR_REQUIRED`
      (`FIND-R53-01`); Owner đóng bằng `ACCEPTED_RISK` (`DEC-218`) →
      `ACCEPT_WITH_RECORDED_RISK`
- [ ] `CHECK-R53-14` Owner nghiệm thu production — CHƯA
- [ ] Task `DONE` — KHÔNG. `CHECK-R53-14` còn `NOT_TESTED`; trạng thái cuối
      vẫn `IMPLEMENTED` cho tới khi Owner nghiệm thu trên production.

## 7. Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- `tools/db/migrations/versions/0012_tracking_display_snapshot.py`
- `tests/test_r53_durable_tracking_labels.py`
- `scripts/r53_crossrepo_smoke.py`
- `docs/tasks/R5-3-nhan-hang-nhom-hang-song-qua-restart.md`
- `docs/sessions/S150-r53-nhan-hang-nhom-hang-ben-vung.md`

Modified:
- `tools/db/schema.py`, `tools/db/__init__.py`
- `app/web/history_store.py`, `app/web/catalog_display.py`,
  `app/web/server.py`, `app/web/workspace_presentation.py`
- `app/web/templates/kinh_doanh_nhan_vien.html`
- `scripts/r51_crossrepo_smoke.py`
- `tests/test_history_db.py`, `tests/test_phb06_brand_reporting.py`,
  `tests/test_phb07_advanced_analytics.py`,
  `tests/test_r51_repair2_run_refreshes_projection.py`,
  `tests/test_web_server.py`
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/PROJECT_DECISIONS.md`,
  `PROJECT/REVIEW_BUDGET_LEDGER.md`

Deleted:
- (không)

Migration Impact:
- `alembic head` `0011_mutation_request_state` → `0012_tracking_display_snapshot`.
  ADDITIVE thuần: `CREATE TABLE tracking_display_snapshot` + một index.
  `downgrade()` `DROP TABLE` thẳng — bảng không chứa dữ liệu Owner, nội dung
  tái tạo được bằng một lần chạy báo cáo. Round-trip upgrade→downgrade đã đo
  (`tests/test_history_db.py::test_migration_upgrade_then_downgrade_round_trips`).

## 8. Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)

- **ĐÃ MET và đã ghi:** *"hành vi ở production khác biệt đáng kể so với các
  giả định đã được tài liệu hóa"*. Giả định đã tài liệu hoá (`catalog_display`
  § "Điểm 3 là lý do file này được phép sống trên đĩa ephemeral") cho rằng cái
  giá của việc mất file là *"một màn hình nói ít đi"* — TẠM THỜI. Đo trên
  đường thật cho thấy nó là VĨNH VIỄN cho tới lần nạp sổ kế tiếp. Rà soát
  nguyên nhân gốc đã thực hiện và ghi lại (§1); không có lần vá suy đoán nào.
- **CHƯA giải quyết — cần Owner/reviewer:** ngân sách review của lineage `R5`
  đã hết (`0 remaining`). Phiên này không tự tiêu và không tự miễn một cycle.
  Nếu Owner/reviewer kết luận rằng một defect production sau nghiệm thu VẪN
  tiêu ngân sách review, lineage `R5` vượt ngân sách và phải escalate theo
  `governance/core/ESCALATION_PROTOCOL.md`.

## 9. Ghi Chú (Notes)

`R5.3` KHÔNG sửa một dòng nào của Tracking, và không cần: audit §4.1 xác minh
hợp đồng production của `chieuBoard()` chở đủ ba trường. Không có blocker
hợp đồng nào để ghi.
