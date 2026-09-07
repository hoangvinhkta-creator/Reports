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
