# S128 — R2: Phân loại sản phẩm và giá nhập tay

## 0. Tóm tắt cho người đọc vội

R2 sửa hai mối nối bị ĐỨT giữa giao diện phân loại và đường chạy báo cáo, và
cả hai đều không có triệu chứng: màn hình phân loại chạy đúng, log ghi đúng,
và báo cáo không đổi một chữ. Ngoài ra R2 thêm trạng thái `OUT_OF_CATALOG`,
trạng thái `CONFLICT`, phần provenance còn thiếu của giá nhập tay, và một hàng
đợi xử lý.

`CHECK-R2-01` … `CHECK-R2-17` PASS. `CHECK-R2-18` (Independent Review) và
`CHECK-R2-19` (Owner nghiệm thu) VẪN `NOT_TESTED` — phiên này không tự tuyên
bố hai check đó, đúng như Brief §9 yêu cầu. Task ở `IMPLEMENTED`.

**Cập nhật (repair sau Independent Review, HEAD `e7ffaf6`):** review trên
`cccdb58` chấp nhận hai finding, cả hai trên chuỗi CONFLICT (`§4.2`) —
`FIND-R2-IR-01` (mapping cũ che mất conflict của lần chạy hiện hành) và
`FIND-R2-IR-02` (một lần giải conflict miễn trừ MỌI bất đồng tương lai, không
riêng đối thủ đã thấy). Cả hai đã sửa tận gốc, cộng một lỗi vòng hai tự phát
hiện khi verify (idempotency tầng store không tính mã đối lập). Chi tiết đầy
đủ + evidence: §9b. `CHECK-R2-05` vẫn PASS, nay có thêm bằng chứng qua route
Flask thật. Task VẪN `IMPLEMENTED` — repair không tự đánh dấu Independent
Review PASS.

Task canonical: `docs/tasks/R2-phan-loai-va-gia-nhap-tay.md`.

## 1. Nền và ranh giới

- Nhánh phát triển: `claude/r2-reports-product-pricing-0yuh97`.
- Base: nhánh mặc định `claude/extract-upload-repo-gq2ws4` tại `cebfab8`, đã
  xác nhận chứa toàn bộ R1 (`eafcb08` và `4b6006e` đều là ancestor của HEAD).
- Tracking KHÔNG bị sửa trong phiên này. Reports không ghi `inv.map`, không
  thay công thức MIN, không thêm một nguồn giá nào.

## 2. Hai mối nối bị đứt — tái hiện được

### 2.1. Resolver production không hỏi store của Reports

`ProductIdentityResolver.resolve()` rẽ theo `tracking_identity_authority`.
Đường production (`True`) đi vào `_tracking_authoritative()` và hàm đó đọc
`alias.map`/`board` rồi `inv.map`, KHÔNG hỏi `self.view` một câu nào. Nhánh
duy nhất đọc store của Reports là `_alias_exact()`, chỉ chạy ở chế độ legacy —
và đó chính là chế độ mà `tests/support/identity_fixtures.resolver()` dùng,
nên các bộ test cũ vẫn xanh trong khi production hỏng.

Bằng chứng tái hiện: gỡ đúng ba dòng hook mới ra khỏi `_tracking_authoritative`
rồi chạy bộ test R2 —

```text
12 failed, 23 passed in 1.00s
FAILED tests/test_r2_product_classification.py::TestCheckR201MappingReachesTheProductionResolver::test_a_confirmed_mapping_resolves_in_the_production_path
FAILED tests/test_r2_product_classification.py::TestCheckR202MappingDrivesTheDailyMinPlan::test_a_confirmed_mapping_enters_the_daily_min_question_set
FAILED tests/test_r2_product_classification.py::TestCheckR203DecisionsSurviveRestart::test_a_brand_new_store_object_reads_the_same_decision
… (12 bài, đủ các chuỗi 01–06 và 16)
```

Đặt lại hook: `35 passed`.

### 2.2. Đường chạy báo cáo đọc log ở SAI CHỖ

Ba nơi tự mở `JsonlProductIdentityStore` trên
`data/product_identity/mappings.jsonl` — đĩa ephemeral của container, trong
khi log thật của bản Web nằm ở R2 object store:

```text
app/demo.py:99                (store view cho resolver)
app/owner_usability.py:221    (_identity_store_view cho kế hoạch daily-min)
tools/tracking/live_pull.py:342 (kế hoạch daily-min ở đường web)
```

Sửa bằng dependency injection từ composition root: `/run` đọc MỘT ảnh chụp
(`identity_gateway.store_view(identity_store)`) và truyền nó vào cả kế hoạch
lẫn pipeline. `None` giữ nguyên nhánh log cục bộ cho máy Owner và cho test.

Một ảnh chụp chứ không phải hai là có chủ đích: kế hoạch hỏi giá và phép phân
giải phải nhìn cùng trạng thái, nếu không một xác nhận xảy ra giữa hai lần đọc
sẽ làm tập mã được HỎI khác tập mã được PHÂN GIẢI — và dòng đó thiếu giá mà
không lý do nào giải thích được.

## 3. Sơ đồ đường đi sau khi sửa

```text
UI  /kinh-doanh/nhan-vien?phan-loai=1
      │  chọn mã Tracking            │  bấm "KHÔNG CÓ TRÊN BẢNG GIÁ"
      ▼                              ▼
identity_gateway.confirm_identity   identity_gateway.mark_out_of_catalog
      │  ConfirmMapping                 │  MarkOutOfCatalog
      └──────────────┬──────────────────┘
                     ▼
       ProductIdentityStore.append()   ← INV-01 · INV-59 · INV-68/69 · audit
                     │
        journal R2 (web)  |  file cục bộ (máy Owner)
                     │
   POST /run ──► identity_gateway.store_view()  ← ĐỌC MỘT LẦN, ĐÓNG BĂNG
                     ├──────────────► live_pull → plan_daily_min_request
                     │                        └► tập mã + cặp (mã, NGÀY BÁN)
                     └──────────────► demo.run_demo → PriceResolutionSources
                                              └► ProductIdentityResolver
                                                   _reports_human_decision()
                                                        │
             ┌──────────────┬────────────────┬──────────┴─────────┐
             ▼              ▼                ▼                    ▼
      MATCHED_TRACKING  OUT_OF_CATALOG   CONFLICT          MAPPING_STALE
      → daily-min       → Pending giá    → người chọn LẠI  _TARGET_ABSENT
        theo sale_date     (nhập tay)       (không tự chọn)
```

## 4. Bốn trạng thái, và chỗ mỗi trạng thái SỐNG

| Trạng thái | Persistence | Vì sao ở đó |
|---|---|---|
| `MATCHED_TRACKING` | `MappingStatus.CONFIRMED` | đã có sẵn từ Phase 1 |
| `NEEDS_REVIEW` | không lưu — suy từ `pending_reasons` | "chưa ai quyết định" không phải một quyết định để lưu |
| `OUT_OF_CATALOG` | `MappingStatus.OUT_OF_CATALOG` (mới) | là một quyết định của người, phải sống qua redeploy |
| `CONFLICT` | không lưu — suy tại lần chạy | là QUAN HỆ giữa quyết định của Reports và capture của Tracking; lưu nó sẽ đóng băng một quan hệ mà lần capture sau có thể tự giải |

## 5. Bằng chứng thực thi (E1)

### 5.1. Bộ test R2 (mới)

```text
$ .venv/bin/python -m pytest -q tests/test_r2_product_classification.py \
                                tests/test_r2_web_workflow.py
50 passed in 2.14s
```

`tests/test_r2_product_classification.py` (35 bài) kiểm ngữ nghĩa domain qua
resolver production, store trên ĐĨA THẬT, và composition.
`tests/test_r2_web_workflow.py` (15 bài) kiểm ba luồng qua ứng dụng Flask
thật, bao gồm một `create_app` HOÀN TOÀN MỚI trên cùng nơi lưu (mô hình
restart/redeploy) và hai bài canh mối nối `/run`.

### 5.2. Full regression

```text
$ .venv/bin/python -m pytest -q tests/
2932 passed, 11 skipped in 137.59s
```

Baseline trước khi sửa: `2882 passed, 11 skipped in 196.42s`.

### 5.3. Migration `0008` — cả hai chiều, trên SQLite

```text
$ alembic upgrade head
['order_key','product_key','occurrence_index','origin','purchase_price',
 'provenance','auto_price_at_entry','entered_at','entered_by','reason']
version: 0008_purchase_price_reason

# nạp một override thật, rồi hạ cấp
$ alembic downgrade 0007_employee_workspace
cols:      [... 'entered_by']                       ← chỉ `reason` bị bỏ
rows kept: [('BH1','4000000','MANUAL_OVERRIDE','owner-web')]

$ alembic upgrade head
after re-upgrade: [('BH1','4000000','owner-web',None)]
```

Điều bài này chứng minh: **một lần rollback KHÔNG làm mất tiền**. Giá nhập
Owner gõ tay là thứ duy nhất trong database không tái tạo lại được từ file sổ
gốc, và nó nguyên vẹn; chỉ phần văn bản giải thích mất đi.

## 6. Kết quả Completion Gate

`CHECK-R2-01` … `CHECK-R2-17` = PASS (E1). Bảng đầy đủ ở
`docs/tasks/R2-phan-loai-va-gia-nhap-tay.md` §6.

`CHECK-R2-18` = NOT_TESTED — Independent Review chưa chạy.
`CHECK-R2-19` = NOT_TESTED — Owner chưa nghiệm thu trên production.

Phiên này KHÔNG tự đánh dấu hai check đó, và KHÔNG chuyển R2 sang `VERIFYING`
hay `DONE`.

## 7. Rủi ro giữ lại

### AR-R2-01 — `SetPending` rồi `ConfirmMapping` làm log KHÔNG ĐỌC ĐƯỢC

Lỗi có TRƯỚC R2. Tái hiện:

```text
store.append(SetPending(... raw_identity_key="k" ...))
store.append(ConfirmMapping(... raw_identity_key="k" ...))
→ MappingIntegrityError: INV-33: bản ghi <id> cho khoá 'REPORTS_SALES\x1fk'
  khai supersedes=None nhưng bản ghi trước đó là <id cũ>
```

Nguyên nhân: `_project()` đẩy mọi mapping không phải `CONFIRMED` ra khỏi
`active`, nên lệnh kế tiếp không thấy bản ghi trước để khai `supersedes` —
trong khi `last_record_id` vẫn nhớ nó. Log hỏng ở MỌI lần đọc về sau.

R2 sửa đúng nhánh của mình (`OUT_OF_CATALOG` vào `_ACTIVE_STATUSES`) và KHÔNG
sửa `PENDING`/`STALE`, vì (a) không đường nào từ giao diện web phát
`SetPending` — chỉ CLI phát được, và (b) đưa `STALE` vào `active` sẽ đổi hành
vi của `_discover_candidates` (mapping `STALE` có `namespace`), tức một thay
đổi ngoài Scope Lock. Ghi lại để R3 hoặc một task riêng xử lý.

### AR-R2-02 — mâu thuẫn chỉ đo được trên capture của LẦN CHẠY

Nếu Tracking đổi `alias.map` GIỮA hai lần chạy sổ, mâu thuẫn mới chỉ xuất hiện
ở lần chạy sau. Tần suất thấp, tác động là một dòng thiếu giá (KHÔNG phải một
con số sai), và nhân viên phát hiện được ở bước đối chiếu thủ công. Không dựng
một vòng kiểm nền cho tình huống này (Brief §8).

### AR-R2-03 — giá nhập tay `0` vẫn được chấp nhận

Xem `docs/tasks/R2-phan-loai-va-gia-nhap-tay.md` §4.5. Đây là chỗ DUY NHẤT
phiên này đọc Brief theo nghĩa hẹp hơn câu chữ; nếu Owner muốn cấm hẳn `0`,
đó là một dòng sửa ở `parse_purchase_price` cộng một quyết định về hàng khuyến
mại.

## 8. Rollback

Rollback code: `git revert` các commit của nhánh này. Không có bước dữ liệu
nào bắt buộc — mọi thay đổi schema là additive.

Rollback schema (chỉ khi cần): `alembic downgrade 0007_employee_workspace`.
Nó bỏ đúng cột `reason`; giá nhập tay, provenance, `auto_price_at_entry`,
`entered_at` và `entered_by` giữ nguyên (§5.3 đã chạy thật).

Các bản ghi `MARK_OUT_OF_CATALOG` trong log identity KHÔNG bị rollback code xoá
— log là append-only. Sau khi hạ cấp code, một bản ghi mang
`status = OUT_OF_CATALOG` sẽ bị `MappingStatus(...)` từ chối lúc đọc. Nghĩa là
**hạ cấp code sau khi Owner đã dùng nút "ngoài bảng giá" là một thao tác một
chiều**: cần khôi phục cả log identity từ bản sao, hoặc giữ nguyên code. Ghi
rõ ở đây vì đây là ràng buộc vận hành thật, không phải một chi tiết.

## 9. Checklist cho Owner (Brief §12)

Ba ca A/B/C giữ nguyên như Brief. Hai lưu ý từ triển khai:

- Ca A bước 3: nếu ngày bán chưa có lịch sử MIN, dòng được phép Pending GIÁ,
  nhưng nó KHÔNG được trở lại "chưa phân loại". Đây chính là phép chuyển mà
  `CHECK-R2-01`/`-03` canh.
- Ca C bước 2: từ R2, thay một giá tự động BẮT BUỘC có lý do. Ô lý do nằm ngay
  cạnh ô giá; bỏ trống sẽ nhận một câu từ chối, không phải một lần lưu im lặng.

## 9b. Repair sau Independent Review (HEAD `e7ffaf6`, nền `cccdb58`)

Independent Review trên `cccdb58` chấp nhận hai finding, cả hai trên đúng
chuỗi CONFLICT của §4.2. Chi tiết đầy đủ, evidence và test nằm trong commit
`e7ffaf6`; tóm tắt bắt buộc theo yêu cầu bàn giao:

### FIND-R2-IR-01 — ACCEPTED

**Bằng chứng đã xác minh (PROBE-1 tái hiện qua cả domain lẫn route thật):**
mapping CŨ (xác nhận thường, TRƯỚC khi mâu thuẫn xuất hiện) khiến
`decisions.confirmed` LUÔN chứa đúng `raw_identity_key` của một `IDENTITY_
CONFLICT` — vì một conflict chỉ sinh ra khi Reports CÓ SẴN một mapping
CONFIRMED. `state_of()` kiểm `confirmed` TRƯỚC `reasons`, nên nhánh CONFLICT
là dead code trên đường đọc từ `reasons`.

**Sửa:** `line_identity.Decisions` thêm `conflict_resolved` (tập con của
`confirmed`, chỉ những khoá được giải qua ĐÚNG thao tác giải mâu thuẫn —
`mapping_source = HUMAN_CONFLICT_RESOLUTION`). Thứ tự kiểm trong `state_of()`
đảo lại: `out_of_catalog` → `conflict_resolved` (thắng ngay, `§4.5`) →
`reasons & IDENTITY_CONFLICT_REASONS` (CONFLICT của lần chạy hiện hành) →
`confirmed` thường → phần còn lại như cũ.

**Files:** `app/web/line_identity.py` (`Decisions`, `state_of`),
`app/web/server.py` (`_identity_decisions` chiếu thêm `conflict_resolved`).

**Test:** `TestFindR2IR01ConflictNotHiddenByAnOldMapping` (4 bài, domain) +
`TestConflictThroughTheWeb::test_a_stale_mapping_does_not_hide_the_conflict_on_the_page`
(route Flask thật — tái hiện đúng PROBE-1: seed mapping cũ → persist dòng
mang `IDENTITY_CONFLICT` → GET trang → khẳng định `data-classification=
"CONFLICT"` có mặt và hàng đợi `xung-dot` không rỗng).

### FIND-R2-IR-02 — ACCEPTED

**Bằng chứng đã xác minh (PROBE-2 tái hiện, sau khi sửa lỗi trong chính kịch
bản test ban đầu — helper test gọi `confirm()` thường hai lần, tự xoá mất
`HUMAN_CONFLICT_RESOLUTION` trước khi resolver kịp chạy; sau khi tách helper
"chỉ dựng snapshot" khỏi "xác nhận", lỗi tái hiện đúng như finding mô tả):
`_human_decision_resolution` exempt MỌI bất đồng một khi `mapping_source is
HUMAN_CONFLICT_RESOLUTION`, không phân biệt mã đối lập nào. Owner giải
A-vs-B (chọn A), Tracking đổi tiếp sang C (mã thứ ba, chưa ai từng thấy) →
resolver vẫn `Resolved` với A, dùng giá của A.

**Sửa:** `Evidence.candidate_set_ids` của lệnh giải mâu thuẫn nay mang thêm
một entry `CONFLICT_OPPOSING_TRACKING_CODE:<mã>` — mã Tracking mà
`tracking_authority_code()` (free function mới, trước đây là method riêng
của resolver — factor ra để `identity_gateway` gọi được cùng phép tính) trả
về NGAY TẠI thời điểm người dùng chọn. Resolver chỉ exempt khi mã authority
hiện tại TRÙNG mã đã ghi; khác đi (kể cả không xác định được) buộc hỏi lại.
Hằng số + hàm đọc (`CONFLICT_OPPOSING_CODE_PREFIX`,
`conflict_opposing_code()`) đặt ở `evidence.py` — không phải `resolver.py`
hay `store.py` — vì `resolver.py` phụ thuộc `store.py` (`StoreView`), nên
`store.py` không quay lại phụ thuộc `resolver.py` được; cả hai chỉ cần đọc/so
một chuỗi đánh dấu, và đó là việc của tầng `Evidence`.

**Files:** `app/modules/product/identity/evidence.py` (hằng số + hàm mới),
`app/modules/product/identity/resolver.py` (`tracking_authority_code` factor
ra free function, điều kiện exempt trong `_human_decision_resolution`),
`app/web/identity_gateway.py` (`confirm_identity` nhận `inv_map_snapshot`,
tính và ghi mã đối lập khi `resolves_conflict=True`), `app/web/server.py`
(`_tracking_inv_map_snapshot`, route truyền nó vào khi `state.conflict`).

**Test:** `TestFindR2IR02ConflictResolutionDoesNotExemptFutureConflicts`
(4 bài, domain — gồm cả đối chứng "cùng mâu thuẫn không hỏi lại" và "authority
quay về đúng mã đã chọn vẫn Resolved bình thường").

### Vòng hai — tự phát hiện, KHÔNG có trong hai finding gốc

Khi verify FIND-R2-IR-02 bằng test đi hết ("Owner chọn LẠI đúng A cho mâu
thuẫn MỚI A-vs-C — con đường tự nhiên nhất khi được hỏi lại"), phát hiện bản
sửa đầu chưa đủ: idempotency của `_next_mapping` (tầng store, `INV-69`) so
`(identity_tuple, mapping_source)` — cả hai đều KHÔNG đổi khi Owner chọn lại
đúng A — nên bị coi là `NO_CHANGE`. Hệ quả: mã đối lập đã ghi (vẫn là B cũ)
không được cập nhật thành C, và resolver tiếp tục hỏi lại A-vs-C mãi mãi dù
Owner vừa bấm XÁC NHẬN và nhận đúng thông báo "đã ghi nhận".

Đây là hệ quả trực tiếp của repair vừa thêm (mã đối lập giờ là một phần của
STATE KẾT QUẢ), không phải một finding độc lập — sửa trong cùng commit, cùng
mức kiểm chứng (test tái hiện lỗi trước sửa, PASS sau sửa).

**Sửa:** `_next_mapping` (`app/modules/product/identity/store.py`) mở rộng
phép so idempotency: khi `mapping_source is HUMAN_CONFLICT_RESOLUTION`, chỉ
coi là `NO_CHANGE` nếu mã đối lập đã ghi ở bản hiện tại TRÙNG mã đối lập của
lệnh mới.

**Test:**
`TestFindR2IR02...::test_re_choosing_the_same_side_against_a_new_conflict_now_sticks`.

### Bằng chứng thực thi (E1)

```text
$ .venv/bin/python -m pytest -q tests/test_r2_product_classification.py \
                                tests/test_r2_web_workflow.py
61 passed in 3.58s

$ .venv/bin/python -m pytest -q tests/test_105d_resolution.py \
    tests/test_105d_persistence.py tests/test_105d_audit_replay.py \
    tests/test_105d_boundaries.py tests/test_105d_identity_keys.py \
    tests/test_105d_cutover_registry.py \
    tests/test_105d_interprocess_concurrency.py \
    tests/test_105e_price_composition.py tests/test_bh73804_confirmed_identity.py \
    tests/test_dec185_nav_chart_identity.py \
    tests/test_identity_durability_and_timeline_aggregation.py \
    tests/test_daily_min_orchestration.py tests/test_employee_workspace_ux.py \
    tests/test_business_vertical.py tests/test_r2_product_classification.py \
    tests/test_r2_web_workflow.py
554 passed in 34.54s

$ .venv/bin/python -m pytest -q tests/
2943 passed, 11 skipped in 189.21s   (trước repair: 2942 passed, 11 skipped)
```

Migration `0008` re-verified không đổi (repair này không chạm schema):
`alembic upgrade head` trên SQLite mới vẫn dừng đúng
`0008_purchase_price_reason`.

### Rủi ro giữ lại sau repair

`AR-R2-01`, `AR-R2-02`, `AR-R2-03` ở §7 giữ nguyên, không finding nào của
vòng review này chạm tới chúng. Không rủi ro mới được chấp nhận
(`ACCEPTED_RISK`) trong vòng repair này — cả ba vấn đề phát hiện (hai finding
gốc + vòng hai tự phát hiện) đều được sửa tận gốc, không phải khoanh vùng.

### Cập nhật CHECK-R2 (§6 của task)

`CHECK-R2-05` (mapping mâu thuẫn ra CONFLICT, không âm thầm chọn bên thắng)
giữ `PASS`, nay có thêm bằng chứng qua route Flask thật, không chỉ qua
domain. Không CHECK nào bị hạ cấp. `CHECK-R2-18`/`-19` vẫn `NOT_TESTED` —
phiên repair này KHÔNG tự đánh dấu Independent Review PASS; reviewer sẽ kết
luận lại trên HEAD `e7ffaf6`.

## 10. Đầu vào cho R3

- Một effective product identity mỗi dòng — `line_identity.state_of`, bốn
  `CLASSIFICATIONS`.
- Một effective KPI purchase price — `BusinessLine.purchase_price`, thứ tự ưu
  tiên: giá tay → MIN đúng `sale_date` → Pending.
- Khoá dòng đang dùng: `(order_key, product_key, occurrence_index)`.
- Giới hạn re-import còn để R3: một file sổ bị sửa thứ tự/đổi cách ghi vẫn có
  thể sinh khoá khác và làm quyết định cũ không khớp. R2 chỉ cam kết bền khi
  mở lại, restart/redeploy và nạp lại CÙNG dữ liệu theo khoá hiện hành.
- Lệnh test: `python -m pytest -q tests/` (full), hoặc
  `python -m pytest -q tests/test_r2_product_classification.py tests/test_r2_web_workflow.py`
  cho riêng R2.
