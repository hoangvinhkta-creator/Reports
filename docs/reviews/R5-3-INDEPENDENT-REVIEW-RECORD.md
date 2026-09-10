# `R5.3` — Bản ghi Independent Review (bằng chứng nguyên văn)

Ngày: 2026-09-10
Kết luận: **`REPAIR_REQUIRED`**
Phiên chỉ ĐỌC, CHẠY, TẠO PROBE và KIỂM — không sửa một dòng mã sản phẩm nào.

---

## 0. Đối tượng review và preflight

```text
Repo Reports    claude/r5-3-reports-brand-category-j37izs
                HEAD  cb7639f88efa8c9fb24f414ac1b6d9f93e58f02e
                (== nhánh review claude/r5-3-reports-metadata-review-8bp6be,
                cùng commit — nhánh review mở thẳng từ tip nhánh triển khai)
Commit triển khai bàn giao (theo brief)  36312ea5805fb79c40e4af61e3501b47c8c7d1e8
                (= cb7639f~1: "R5.3: ghi SHA của commit triển khai vào bàn giao
                S150" là commit tài liệu-thuần đứng SAU nó, không đổi code)
Nền             origin/claude/extract-upload-repo-gq2ws4 @
                c46e458ef6e6653b7cba210dc4393e1160f158dd
Repo Tracking   main @ 0f7347ba677d248ceb8c7983cb76322888cf09e3
                (>= b7c5f3b theo yêu cầu dependency — xác nhận b7c5f3b là
                ancestor của 0f7347b)
```

```text
$ git rev-parse HEAD
cb7639f88efa8c9fb24f414ac1b6d9f93e58f02e

$ git rev-parse origin/claude/r5-3-reports-brand-category-j37izs
cb7639f88efa8c9fb24f414ac1b6d9f93e58f02e

$ git merge-base --is-ancestor c46e458ef6e6653b7cba210dc4393e1160f158dd \
    cb7639f88efa8c9fb24f414ac1b6d9f93e58f02e && echo "YES ancestor"
YES ancestor

$ git status --porcelain
(rỗng — WORKTREE CLEAN)
```

`scripts/branch_authority_check.sh`:

```text
DEFAULT_REMOTE_REF   : refs/remotes/origin/claude/extract-upload-repo-gq2ws4
DEFAULT_BRANCH       : claude/extract-upload-repo-gq2ws4
DEFAULT_TIP          : c46e458ef6e6653b7cba210dc4393e1160f158dd
HEAD_SHA             : cb7639f88efa8c9fb24f414ac1b6d9f93e58f02e
WORKTREE             : CLEAN
STOP — nhánh review cục bộ chưa có upstream (chưa `push -u`)
```

Script dừng vì nhánh REVIEW cục bộ chưa có upstream — đúng trạng thái của
nhánh review phiên này (chưa push), KHÔNG phải của nội dung được review.
`DEFAULT_TIP` khớp CHÍNH XÁC với base ghi trong brief (`c46e458…`).

### Diff CHỈ nằm trong Reports, không chạm Tracking

```text
$ git diff --stat c46e458..cb7639f
 PROJECT/PROJECT_DECISIONS.md                       | 144 +++++
 PROJECT/PROJECT_PROGRESS.md                        |  60 ++
 PROJECT/REVIEW_BUDGET_LEDGER.md                    |  58 ++
 app/web/catalog_display.py                         |  87 ++-
 app/web/history_store.py                           |  74 ++-
 app/web/server.py                                  | 172 +++++-
 app/web/templates/kinh_doanh_nhan_vien.html        |   4 +
 app/web/workspace_presentation.py                  |  29 +-
 docs/sessions/S150-r53-nhan-hang-nhom-hang-ben-vung.md       | 343 ++
 docs/tasks/R5-3-nhan-hang-nhom-hang-song-qua-restart.md      | 642 ++
 scripts/r51_crossrepo_smoke.py                     |  26 +-
 scripts/r53_crossrepo_smoke.py                     | 261 ++++++++
 tests/test_history_db.py                           |  21 +-
 tests/test_phb06_brand_reporting.py                |   5 +
 tests/test_phb07_advanced_analytics.py             |   5 +
 tests/test_r51_repair2_run_refreshes_projection.py |  44 +-
 tests/test_r53_durable_tracking_labels.py          | 670 ++++
 tests/test_web_server.py                           |   7 +-
 tools/db/__init__.py                               |   2 +-
 tools/db/migrations/versions/0012_tracking_display_snapshot.py | 101 ++
 tools/db/schema.py                                 |  67 +++
 21 files changed, 2780 insertions(+), 42 deletions(-)
```

Không một file nào thuộc `app/modules/pricing/`, `app/modules/profit/`,
`app/modules/kpi/`, `period_lock.py`, `business_export`, resolver/product
identity, hay bất kỳ đường công thức tiền/MIN/coverage/import/export nào.
Đúng phạm vi Scope Lock của `docs/tasks/R5-3-…md` §2 (bảng schema mới, hai
phương thức repository, bốn hàm/route ở `server.py`/`catalog_display.py`,
một trường trình bày, test, script smoke, tài liệu).

```text
$ cd /home/user/Tracking && git log --oneline b7c5f3b..HEAD
0f7347b Merge R5.2.3: ẩn tạm 4 cột Hashtag/Phân khúc/Nhóm hàng/Hãng, gọn nút
        Chuẩn hoá thành icon (#28)
1c36fa2 R5.2.3: ẩn tạm 4 cột Hashtag/Phân khúc/Nhóm hàng/Hãng, gọn nút
        Chuẩn hoá thành icon
```

Hai commit trên là UI-thuần của `R5.2.3` (ẩn cột, gọn nút) — không thuộc
`R5.3`, không chạm hợp đồng `/api/xuat/board`. **Tracking không có thay đổi
nào cho `R5.3`.**

### Lệnh bắt buộc

```text
$ pytest -q
3627 passed, 24 skipped in 318.83s

$ git diff --check c46e458..cb7639f
(rỗng — sạch)

$ alembic heads
0012_tracking_display_snapshot (head)     ← ĐÚNG MỘT head
```

Lệch `3627/24` so với `3628 passed / 23 skipped` mà bàn giao `S150` ghi:
chênh đúng 1 test, và nguyên nhân đo được là môi trường — `botocore` không
cài trong container review này
(`tests/test_boto3_putobject_ifnonematch_capability.py` SKIP thay vì PASS).
19/19 skip còn lại đều thuộc `postgresql`/`jsdom`/golden-workbook-thô —
cùng lớp phụ thuộc môi trường, không liên quan diff `R5.3`. Không skip nào
nằm trong `tests/test_r53_durable_tracking_labels.py` (19/19 PASS).

### Migration `0012` — upgrade/downgrade thật trên dữ liệu có sẵn (SQLite)

```text
$ alembic upgrade 0011_mutation_request_state
$ python3 -c "... insert probe row vào employee_target (year=2026, month=9,
    employee_key='nv-probe', origin=ORIGIN_PIPELINE, target_vnd=100000000) ..."
probe inserted into employee_target OK

$ alembic upgrade head            # tạo tracking_display_snapshot
$ alembic downgrade 0011_mutation_request_state   # DROP TABLE thẳng
$ alembic upgrade head            # tạo lại bảng

tracking_display_snapshot present: True
PRE-EXISTING probe row survived full upgrade->downgrade->upgrade cycle:
('nv-probe', '100000000')
```

Dữ liệu KHÔNG thuộc `R5.3` sống sót nguyên vẹn qua trọn vòng
upgrade→downgrade→upgrade; `tracking_display_snapshot` dựng lại đúng shape
(`run_id` PK, 5 cột phụ, 1 index `created_at`) và nhận ghi lại được ngay sau
đó. Migration đúng như docstring của nó tự tả: ADDITIVE thuần, `downgrade()`
`DROP TABLE` thẳng vì bảng không mang dữ liệu Owner (con số kỳ không đi qua
bảng này — đã xác nhận bằng `test_the_durable_store_holds_no_money_column`).

---

## 1. Luồng chính qua entry point thật (chuỗi 1)

```text
$ python3 scripts/r53_crossrepo_smoke.py --tracking /home/user/Tracking
KẾT QUẢ SMOKE: 25 PASS, 0 FAIL
```

Script này dùng `node` chạy CHÍNH `chieuBoard()` thật của Tracking (không gõ
tay dict `{"brand": ..., "category_label": ...}`) để sinh board/alias cho một
mã đã CONFIRMED, rồi đi đúng đường production: `POST /run` thật → tab Nhân
viên qua HTTP thật (Flask test client, không gọi hàm trình bày trực tiếp) —
không mở popover phân loại nào. Kết quả đo được:

```text
ok   KHÔNG mở bảng chọn: Mặt hàng hiện MODEL NGẮN từ Tracking
ok   cột Hãng hiện brand từ Tracking
ok   cột Nhóm hàng hiện category_label từ Tracking
ok   tên dài trên sổ đã biến khỏi Ô Mặt hàng
ok   ...nhưng vẫn đọc đủ được qua tooltip (R5.3 §UI)
ok   bản chiếu lành ⟹ KHÔNG có cảnh báo
```

`tests/test_r53_durable_tracking_labels.py::test_exactly_one_tracking_pull_per_run`
xác nhận riêng: đúng MỘT lần gọi `live_pull.pull_live_captures` mỗi `/run`
(19/19 test file PASS ở lệnh `pytest -q` trên).

**Chuỗi 1: PASS.**

## 2. Restart và persistence (chuỗi 2)

```text
4) RESTART container: xoá đĩa ephemeral, KHÔNG đụng database
ok   lần chạy đã lưu BỀN bản chiếu, kèm capture đã dùng
ok   bản bền mang NGUYÊN VĂN nhãn của capture Tracking thật
ok   sau restart: cache đĩa đã biến mất
ok   R5.3: Mặt hàng vẫn hiện MODEL NGẮN sau restart
ok   R5.3: Hãng vẫn hiện sau restart
ok   R5.3: Nhóm hàng vẫn hiện sau restart
ok   ...và cache đĩa được ghi lại
ok   ...và KHÔNG có cảnh báo nào, vì không có gì hỏng
ok   restart KHÔNG đổi một đồng nào của bảng kê
ok   ...và không thêm/bớt một dòng nào
```

`restart_the_container()` trong bộ test/smoke xoá ĐÚNG những gì Render dọn ở
mỗi deploy (mọi file trong thư mục cache đĩa, kể cả `*.status.json`) —
KHÔNG đụng database, đúng mô hình thất bại thật của môi trường. Đọc code xác
nhận: `_tracking_display()` (`app/web/server.py`) đi qua ĐÚNG một cổng đọc
(`catalog_display.read()` → nếu rỗng, `_durable_tracking_display()` →
`snapshot_repo.latest_tracking_display()`), và PostgreSQL (không phải file)
là nguồn dựng lại — khớp đúng khẳng định "cache đĩa chỉ là cache, PostgreSQL
là nguồn bền" trong brief.

**Chuỗi 2: PASS**, cho ĐÚNG lần chạy gần nhất (xem §3 cho giới hạn của phát
biểu này khi có NHIỀU lần chạy).

## 3. Bất biến "đúng lượt chạy" (chuỗi 3) — **FAIL, `FIND-R53-01`**

### Vì sao không dùng lại giả định "cache cũ cũng vậy"

`docs/tasks/R5-3-nhan-hang-nhom-hang-song-qua-restart.md` §4 đã tự ghi hành
vi này thành `AR-R5.3-01` ("bản chiếu là của lần chạy GẦN NHẤT, không của
lần chạy đã sinh ra kỳ đang xem"), lý lẽ: hành vi này giống hệt cache đĩa từ
trước `R5.3`, và Owner đã nghiệm thu nó ở `CHECK-R51-26`. Brief review yêu
cầu tường minh KHÔNG chấp nhận lý lẽ đó mà không đo — nên phiên này đo trực
tiếp bằng hai probe độc lập.

### Đọc code trước khi đo

`tracking_display_snapshot` có PK là `run_id` (`tools/db/schema.py`) —
bảng CÓ ĐỦ dữ liệu để phân biệt lần chạy nào ghi cái gì. Nhưng đường ĐỌC
(`app/web/server.py::_durable_tracking_display` →
`SnapshotRepository.latest_tracking_display()`) chỉ có MỘT chế độ:
"hàng có `created_at` mới nhất, toàn cục" — không tham số `run_id`, không
tham số kỳ/period. Mọi nơi gọi `_tracking_display()`
(`_catalog_labels`, `_confirmed_lines_matched...`, brand report §2823,
`_analysis_view` của R6 §3564) đều nhận CÙNG một bản chiếu, bất kể đang
render kỳ nào. Chính `tests/test_r53_durable_tracking_labels.py::
test_the_durable_store_keeps_one_row_per_run_and_returns_the_latest` khẳng
định "trả về lần chạy GẦN NHẤT" như một hành vi ĐÃ ĐỊNH, không phải một
edge case bị bỏ sót — và không có bài test nào trong 19 bài của file này đo
"mở lại kỳ CŨ sau khi có một lần chạy MỚI cho kỳ KHÁC".

### Probe 1 — hai lần chạy, hai kỳ khác nhau, cùng mã Tracking

Kịch bản ĐÚNG như brief mục 3: lần chạy A (kỳ 2026-01, mã `55Q6FA` →
`model=QLED 55Q6FA, brand=Samsung, category=Tivi`), lần chạy B sau đó (kỳ
2026-02, CÙNG mã `55Q6FA` nhưng Tracking đã đổi nhãn →
`model=55Q6FA-v2, brand=LG, category=Điều hoà`), rồi mở lại BÁO CÁO CỦA A
và CỦA B RIÊNG RẼ qua `/kinh-doanh/nhan-vien?ky=…` (hai kỳ dùng mã đơn hàng
KHÁC nhau để không đè version-hiện-hành của nhau — xem §9 cho script đầy
đủ).

```text
Sau run A (kỳ 2026-01): ['Samsung'] ['Tivi']
Sau run B (kỳ 2026-02): ['LG'] ['Điều hoà']

Sau run B, TRƯỚC restart, kỳ 2026-01 mở lại:
  brand/category cho mã X: ['LG'] ['Điều hoà']     ← SAI, phải là Samsung/Tivi

=== SAU RESTART (đĩa đã xoá, chỉ còn database) ===
Báo cáo 2026-01 (LƯỢT A) — brand/category cho mã X: ['LG'] ['Điều hoà']  ← SAI
Báo cáo 2026-02 (LƯỢT B) — brand/category cho mã X: ['LG'] ['Điều hoà']  ← ĐÚNG

KỲ VỌNG: 2026-01 -> Samsung/Tivi ; 2026-02 -> LG/Điều hoà
```

Kiểm tra cô lập ảnh hưởng — tiền/số dòng của kỳ 2026-01 KHÔNG đổi dù nhãn
sai:

```text
totals-purchase: ['0']       (khớp dữ liệu gốc của kỳ 2026-01)
totals-sell:     ['2.500']   (khớp dữ liệu gốc của kỳ 2026-01)
line-product:    2           (khớp — không mất/thêm dòng)
```

**Kết quả: lỗi CÓ THẬT, độc lập với restart** (đã tái hiện cả TRƯỚC và SAU
khi xoá cache đĩa) — và độc lập với tiền: doanh thu/lợi nhuận/số dòng của kỳ
2026-01 giữ nguyên đúng, chỉ ba ô nhãn hiển thị sai.

### Ảnh hưởng thật: `R6` gộp theo Nhóm hàng đọc CÙNG cổng này

`app/web/server.py::_analysis_view()` (hạ tầng đọc của `R6`, dùng chung cho
mọi trang phân tích) gọi:

```python
metadata = product_taxonomy.metadata_for(
    data.details, decisions=_identity_decisions(),
    identities=identity_gateway.confirmed_identities(identity_store),
    display=_tracking_display())
```

và `_analysis_range()` nhận `ky=`/`tu-ngay=`/`den-ngay=` tuỳ ý từ
querystring — Owner mở trang phân tích cho BẤT KỲ kỳ nào, kể cả kỳ đã đóng
từ lâu. Vì `display=_tracking_display()` luôn là bản chiếu TOÀN CỤC của lần
chạy gần nhất, một trang phân tích Nhóm hàng cho kỳ CŨ, mở SAU khi Tracking
đổi phân loại một mã ở một kỳ MỚI hơn, sẽ gộp doanh thu của kỳ CŨ vào Nhóm
hàng MỚI — âm thầm, không cảnh báo, không sai một đồng tiền nào nhưng sai
đúng trục mà `R6` được xây để trả lời.

### Phân loại

Đúng định nghĩa `REPAIR_REQUIRED` mà brief đã cho trước: *"sai metadata
giữa các lượt chạy"*. Đây không phải một hồi quy MỚI do `R5.3` gây ra —
cùng lỗi tái hiện được về mặt logic trên cache đĩa của `R5`/`R5.1 REPAIR-2`
(một file toàn cục, luôn bị lần chạy sau đè) — nhưng `R5.3` xây đúng cấu
trúc dữ liệu (`tracking_display_snapshot` khoá theo `run_id`) có thể đóng
lỗ hổng này mà không dùng nó cho mục đích đó; và task này ghi rõ trong tên
của chính nó ("nhãn... sống qua restart", tức đúng lượt chạy) là mục tiêu
mà lỗ hổng này trực tiếp phá vỡ. Theo đúng chỉ dẫn của brief, phát hiện này
KHÔNG được hạ nhẹ thành `ACCEPTED_RISK` chỉ vì hành vi kế thừa.

`FIND-R53-01` — REPAIR_REQUIRED, xem §6.

**Chuỗi 3: FAIL.**

## 4. Hàng rào fail-closed (chuỗi 4)

```text
5) Dòng chưa xác nhận: dấu gạch, không suy từ tên kế toán
ok   `Tivi Test-7` chưa xác nhận ⟹ giữ TÊN THÔ
ok   ...và Hãng/Nhóm hàng là dấu gạch, dù tên chứa chữ 'Tivi'

6) Mất cả hai nơi lưu ⟹ cảnh báo, không im lặng
ok   mất cả hai ⟹ tab Nhân viên CẢNH BÁO
ok   ...và vẫn KHÔNG đổi một đồng nào
```

Bổ sung từ 19 bài `pytest` chuyên biệt của `tests/test_r53_durable_tracking_labels.py`
(toàn bộ PASS ở lệnh `pytest -q` §0):

```text
test_a_confirmed_code_with_no_brand_shows_the_category_and_dashes_the_brand
    CONFIRMED + brand=null ⟹ nhóm hàng hiện, Hãng "—"
test_a_legacy_capture_without_the_new_fields_never_crashes_or_guesses
    capture legacy thiếu field mới ⟹ không crash, không suy tên kế toán
test_a_legacy_capture_does_not_erase_labels_an_earlier_run_stored
    capture cũ KHÔNG xoá nhãn lần chạy trước đã ghi được
test_an_unclassified_line_stays_dashed_even_when_its_name_looks_like_a_brand
test_the_same_holds_after_a_restart
    chưa xác nhận, tên nhìn giống hãng/nhóm hàng ⟹ "—" cả TRƯỚC và SAU restart
test_an_out_of_catalog_line_gets_no_label_after_a_restart
    OUT_OF_CATALOG ⟹ "—" sau restart
test_a_min_price_without_a_confirmed_mapping_earns_no_label
    có MIN/giá nhưng chưa CONFIRMED ⟹ "—"
test_wiping_or_corrupting_the_cache_moves_no_money
test_a_broken_durable_row_degrades_to_dashes_not_to_an_error
    hàng bền hỏng ⟹ suy thành "{}" (dấu gạch), KHÔNG lỗi 500
test_losing_both_places_still_warns_instead_of_going_silent
```

Không bài nào trong nhóm này suy nhãn từ tên trên sổ kế toán; mọi trạng
thái chưa-CONFIRMED/conflict/stale/OUT_OF_CATALOG đều thiếu KHOÁ trong bảng
nhãn (cả cache đĩa lẫn bảng bền), nên không có nhánh code nào có thể làm
nhãn "rò" vào chúng — xác nhận lại đúng bất biến mà `R5.1 REPAIR-2` đã
nghiệm thu và `R5.3` không chạm tới cổng đọc đó
(`_catalog_labels`/`identity_gateway.confirmed_identities`).

**Chuỗi 4: PASS.**

## 5. Hồi quy và biên dữ liệu (chuỗi 5)

```text
$ pytest -q
3627 passed, 24 skipped   (xem §0 cho giải thích lệch 1 test vì môi trường)

$ python3 scripts/r51_crossrepo_smoke.py --tracking /home/user/Tracking
KẾT QUẢ SMOKE: 86 PASS, 0 FAIL
```

`r51_crossrepo_smoke.py` (đã cập nhật trong diff `R5.3` §5 theo nghĩa mới)
xác nhận riêng: "đổi nhóm hàng bên Tracking hiện ra ngay ở lần đọc sau" là
hành vi ĐÃ NGHIỆM THU cho kỳ HIỆN HÀNH (kỳ vừa `/run`) — đúng, và KHÔNG mâu
thuẫn với `FIND-R53-01`: `FIND-R53-01` chỉ xảy ra khi mở một kỳ KHÁC kỳ vừa
chạy.

Không file nào trong diff chạm `app/modules/pricing/`, `.../profit/`,
`.../kpi/`, `period_lock.py`, resolver/product-identity, import/export
(xem §0 diff scope). Bảng mới `tracking_display_snapshot` không mang cột
tiền nào (`test_the_durable_store_holds_no_money_column`, PASS). Capture cũ
(`with_metadata=False`) và run không có metadata vẫn tương thích
(`test_a_legacy_capture_without_the_new_fields_never_crashes_or_guesses`,
PASS). Không truy vấn Tracking mới nào khi render tab Nhân viên
(`test_the_rebuild_never_pulls_tracking`, PASS — grep code xác nhận
`_durable_tracking_display`/`_tracking_display` không import `live_pull`).
Không tên kế toán/hashtag thô/NCC/giá nào đi vào `rows_json` của bảng bền —
`catalog_display.rows_of()` (không đổi field set ở `R5.3`) chỉ trích
`{tracking_code, model_label, brand, category_label}`.

**Chuỗi 5: PASS**, ngoại trừ hệ quả của `FIND-R53-01` lên gộp `R6` đã ghi ở
§3 (không phải một hồi quy MỚI ở chuỗi này, nhưng là nơi tác động thật của
nó xuất hiện).

## 6. Finding

| ID | Loại | Mô tả | Tác động | Repair tối thiểu |
|---|---|---|---|---|
| `FIND-R53-01` | `REPAIR_REQUIRED` | Đường đọc bản chiếu nhãn (`_tracking_display`/`latest_tracking_display`) không phân biệt theo `run_id`/kỳ — luôn trả bản của lần chạy GẦN NHẤT toàn cục, kể cả khi đang mở một kỳ KHÁC. | Không đổi tiền/số dòng/MIN/coverage/vân tay chốt kỳ. Gây sai `Hãng`/`Nhóm hàng` hiển thị cho kỳ CŨ sau khi một kỳ MỚI hơn khiến Tracking đổi phân loại một mã dùng chung; ảnh hưởng trực tiếp tới gộp Nhóm hàng của `R6` cho lịch sử. | Thêm đường đọc theo `run_id` cụ thể ở `SnapshotRepository` (ví dụ `tracking_display_for_run(run_id)`), và truyền `run_id`/kỳ đang xem xuống `_tracking_display()` tại các nơi gọi đang có sẵn thông tin đó (`_catalog_labels`, `_analysis_view`, brand report) — **KHÔNG** đổi hợp đồng ghi (`write_tracking_display` đã đúng, khoá theo `run_id` sẵn). Phạm vi sửa nằm gọn trong tầng đọc đã liệt ở Scope Lock `R5.3` §2 (`history_store.py` + `server.py`), không cần đụng `business_service.period`/resolver theo đúng ràng buộc mà `AR-R5.3-01` đã nêu — cần một khảo sát nhỏ để xác nhận `PeriodData.details`/route nào đã CÓ `run_id` sẵn trong tay trước khi viết code. |

Không có finding `ACCEPTED_RISK` MỚI nào phát sinh từ phiên review này
(`AR-R5.3-01/02/03` trong task file được XÁC NHẬN đúng như đã ghi, nhưng
`AR-R5.3-01` được NÂNG thành `FIND-R53-01` theo đúng chỉ dẫn brief — xem
trên).

`OBSERVATION`: không có.

## 7. Ngân sách repair-cycle (`V4.1`) và escalation

`PROJECT/REVIEW_BUDGET_LEDGER.md` — lineage `R5`:

```text
repair_cycles_allowed: 2
repair_cycles_used:    2
repair_cycles_remaining: 0
```

### Xác nhận bookkeeping "CẦN XÁC NHẬN" của `S146` và `S150`

Cả hai phiên repair sản xuất (`R5.1 REPAIR-2` và `R5.3`) tự ghi là KHÔNG
tiêu repair cycle, với lý lẽ: ngân sách `V4.1` §2–§3 đếm LẦN SỬA sau một
vòng review ra finding BLOCKING; cả hai defect đến từ Owner trên
PRODUCTION, SAU khi Independent Review trước đó (`CHECK-R51-25`) đã PASS —
không phải một repair theo sau một review thất bại. Phiên này **XÁC NHẬN**
lý lẽ đó: nó nhất quán với cách `V4.1` xử lý các trường hợp tương tự ở
lineage khác trong cùng ledger (ví dụ `TASK-PRA-004` §"phiên implement tự
sửa khiếm khuyết trong CHÍNH mã nó vừa viết ... KHÔNG phải một repair
cycle"), và với chính cách tính "theo VÒNG REVIEW", không theo "mọi commit
sửa lỗi". Số dư `R5` giữ nguyên `2 allowed / 2 used / 0 remaining` sau cả
`S146` lẫn `S150` — **KHÔNG cần escalate vì việc này**.

### Nhưng: `FIND-R53-01` của CHÍNH phiên review này thì khác

`FIND-R53-01` đến từ một vòng Independent Review (chính phiên này,
`CHECK-R53-13`) kết luận `REPAIR_REQUIRED` — đây LÀ đúng loại sự kiện mà
`V4.1` §2–§3 đếm vào ngân sách repair-cycle nếu một phiên repair được mở để
sửa nó. Lineage `R5` đang ở `0 remaining`. Mọi cảnh báo trước đó trong
ledger (`S135`, `S140`, `S144`) đều nói cùng một câu: *"nếu vòng review kế
tiếp lại ra `REPAIR_REQUIRED`, lineage KHÔNG được mở thêm một repair cycle
— phải escalate theo `governance/core/ESCALATION_PROTOCOL.md`"*. Điều kiện
đó nay ĐÚNG.

**Escalation Record** (`governance/core/ESCALATION_PROTOCOL.md`):

```text
Reason: Lineage R5 đã hết ngân sách repair-cycle (2/2 đã dùng, 0 remaining)
  TRƯỚC KHI vòng Independent Review của R5.3 (phiên này) tìm ra một finding
  REPAIR_REQUIRED mới (FIND-R53-01). Mở một repair cycle bình thường cho
  finding này sẽ là cycle thứ BA của lineage — vượt bảng ngân sách đã
  freeze (`HIGH = 2 blocking repair cycles`, không có `HIGH = 3`).

Attempts made: Không có lần thử sửa nào trong phiên này (Independent Review
  chỉ đọc/chạy/kiểm — không sửa mã sản phẩm, theo đúng brief).

Observed evidence: §3 — hai probe HTTP thật, một trước một sau restart,
  đo trực tiếp trên server Flask thật; kết quả tái lập được 100% (không
  flaky), độc lập với `_persist_tracking_display`/cache đĩa (lỗi tồn tại ở
  CẢ HAI nơi lưu, vì cả hai đều đọc qua cùng cổng `_tracking_display`).

Suspected root cause: `SnapshotRepository.latest_tracking_display()` không
  nhận tham số phân biệt lần chạy/kỳ; mọi nơi gọi `_tracking_display()`
  không truyền `run_id`/kỳ đang xem, dù dữ liệu đó có sẵn ở phần lớn call
  site. Không phải lỗi kiến trúc mới của `R5.3` — kế thừa nguyên trạng từ
  cache đĩa của `R5`/`R5.1 REPAIR-2`, nhưng `R5.3` là nơi ĐẦU TIÊN có cấu
  trúc dữ liệu (`run_id` PK) có thể đóng nó mà không tận dụng.

Affected scope: CHỈ tầng hiển thị (`Hãng`/`Nhóm hàng`/`Mặt hàng` trên tab
  Nhân viên và gộp Nhóm hàng của R6 cho các kỳ KHÔNG phải kỳ vừa `/run`).
  KHÔNG chạm tiền/MIN/coverage/vân tay chốt kỳ/export (đo trực tiếp, §3).

Recommended agent tier: Không cần leo thang năng lực agent — đây là một
  sửa cục bộ, phạm vi rõ (tầng đọc `history_store.py` + call site
  `server.py`), không phải một xung đột kiến trúc hay bất định về nguyên
  nhân gốc. Vấn đề CẦN escalate là NGÂN SÁCH, không phải NĂNG LỰC.

Recommended next action: Owner quyết định theo `V4.1` §2 cho lineage đã
  cạn ngân sách — hoặc (a) `OWNER_EXTENSION` cấp thêm repair cycle riêng
  cho `FIND-R53-01` (kèm phạm vi cụ thể như bảng repair tối thiểu ở §6),
  hoặc (b) Owner tự quyết định chấp nhận `FIND-R53-01` làm `ACCEPTED_RISK`
  MỚI có ghi lại tường minh (khác với việc để nguyên `AR-R5.3-01` — Owner
  phải thấy đúng bằng chứng ở §3 trước khi quyết, không phải bản tóm tắt
  giảm nhẹ của task file), hoặc (c) mở một lineage/task riêng (không phải
  sub-unit của `R5`, theo đúng cách `R6` đã tách khỏi `R5`) để sửa
  `FIND-R53-01` mà không tiêu ngân sách `R5` — phù hợp vì phạm vi sửa nằm
  gọn ở tầng đọc hiển thị, không mở rộng contract `R5`/`R5.1`.
```

## 8. Kết luận

**`REPAIR_REQUIRED`.**

Bốn trong năm chuỗi bắt buộc (luồng chính, restart/persistence, hàng rào
fail-closed, hồi quy/biên dữ liệu) đều PASS với bằng chứng E2 độc lập —
smoke qua HTTP thật dùng producer Tracking THẬT (`chieuBoard()` qua Node),
19 bài test chuyên biệt, và một round-trip migration thật trên dữ liệu có
sẵn. Chuỗi thứ ba (bất biến "đúng lượt chạy") FAIL: `FIND-R53-01` là một
finding thật, tái lập được, không phải một lỗi flaky hay một khác biệt môi
trường — bản chiếu nhãn hiển thị của một kỳ CŨ bị GHI ĐÈ bởi lần chạy MỚI
NHẤT toàn cục, dù dữ liệu bền của kỳ CŨ (đúng bằng chứng của LẦN CHẠY đã
sinh ra nó) vẫn còn nguyên trong `tracking_display_snapshot`.

Đây KHÔNG phải một hồi quy do `R5.3` MỚI gây ra — hành vi giống hệt cache
đĩa từ trước — nhưng nó trái đúng bất biến mà brief review yêu cầu kiểm
tường minh và cấm hạ nhẹ, và nó có tác động thật lên gộp Nhóm hàng của `R6`
cho các kỳ lịch sử. Repair tối thiểu được đề xuất ở §6 nằm gọn trong Scope
Lock của `R5.3` (tầng đọc, không đổi hợp đồng ghi).

Vì lineage `R5` đã hết ngân sách repair-cycle (`2/2`, `0 remaining`) TRƯỚC
khi finding này xuất hiện, phiên này **escalate theo
`governance/core/ESCALATION_PROTOCOL.md`** (§7) thay vì tự đề xuất mở một
repair cycle thứ ba. Quyết định tiếp theo (`OWNER_EXTENSION`, chấp nhận
làm `ACCEPTED_RISK`, hay mở lineage riêng) thuộc thẩm quyền Owner.

Phiên này **KHÔNG** đánh dấu `CHECK-R53-14` (Owner Acceptance) — chỉ Owner
đóng check đó. Phiên này **KHÔNG** merge, **KHÔNG** deploy, **KHÔNG** bấm
nút Firebase nào.

`CHECK-R53-13`: `NOT_TESTED` → **`FAIL`** (E2, bằng chứng ở tài liệu này).

## 9. Lệnh tái lập

```bash
# Preflight
cd /home/user/Reports
git fetch origin claude/r5-3-reports-brand-category-j37izs \
    claude/extract-upload-repo-gq2ws4
git rev-parse HEAD origin/claude/r5-3-reports-brand-category-j37izs \
    origin/claude/extract-upload-repo-gq2ws4
git merge-base --is-ancestor \
    c46e458ef6e6653b7cba210dc4393e1160f158dd HEAD && echo OK
git status --porcelain
bash scripts/branch_authority_check.sh
git diff --stat c46e458ef6e6653b7cba210dc4393e1160f158dd..HEAD
git diff --check c46e458ef6e6653b7cba210dc4393e1160f158dd..HEAD

# Cài đặt + lệnh bắt buộc
pip install -e ".[dev,web]"
pytest -q
alembic heads

# Chuỗi 1 + 4 + 5 — smoke qua HTTP thật, producer Tracking thật
python3 scripts/r53_crossrepo_smoke.py --tracking /home/user/Tracking
python3 scripts/r51_crossrepo_smoke.py --tracking /home/user/Tracking

# Chuỗi 3 — probe "đúng lượt chạy" (hai kỳ, cùng mã, Tracking đổi nhãn
# giữa hai lần chạy; mã đơn hàng của hai kỳ KHÔNG trùng để không đè
# version-hiện-hành của nhau) — script độc lập, KHÔNG commit vào repo,
# dựng lại từ đặc tả §3 của tài liệu này bằng chính các fixture/helper của
# tests/test_r53_durable_tracking_labels.py (build_synthetic_workbook,
# set_live_catalog, confirm_identity, /run thật qua Flask test client).
```

Migration round-trip (§0) chạy tay bằng `HISTORY_DATABASE_URL=sqlite:///…`
trỏ vào một file scratch, `alembic upgrade 0011_mutation_request_state`,
chèn một hàng vào `employee_target` qua `tools.db.schema.METADATA`
(`origin=ORIGIN_PIPELINE`), rồi `alembic upgrade head` →
`alembic downgrade 0011_mutation_request_state` → `alembic upgrade head`,
đọc lại hàng đó bằng SQL thô.
