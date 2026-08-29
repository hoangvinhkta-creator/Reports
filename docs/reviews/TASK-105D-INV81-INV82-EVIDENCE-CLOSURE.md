# TASK-105D — INV-81 / INV-82 Evidence Closure (S048)

Session Type:
EVIDENCE CLOSURE — phiên hẹp nối tiếp `S047`. Mục tiêu duy nhất: đóng đúng
khoảng trống evidence mà `S047` xác định là `NEAREST_REMAINING_BLOCKING_CONDITION`
cho `TASK-105D = DONE` — `INV-81` và `INV-82` chỉ có test "yếu" (`H-06`).
Không phải architecture review, không phải adversarial review, không phải
hardening campaign, không phải repair cycle.

Date:
2026-08-29

Branch / Base SHA:
`review/task-105d-inv81-inv82-closure`, base = HEAD của `S047`
`feb57a677ce8467ce4f422d2549eb6ecb9f5d3e7`.

## 1. Git Preflight

```text
current branch     : review/task-105d-inv81-inv82-closure
initial HEAD        : feb57a677ce8467ce4f422d2549eb6ecb9f5d3e7  (KHỚP base SHA yêu cầu)
upstream             : origin/review/task-105d-inv81-inv82-closure (0 ahead / 0 behind)
working tree          : CLEAN
branch_authority_check.sh : AUTHORITY_OK (BRANCH_WITH_UPSTREAM, ahead default 4 / behind default 0,
    DIVERGENCE = WITHIN_LIMITS)
```

Ancestry liên tục từ `S038` → … → `S046` → `S047` → `S048` (không rebase/
squash/cherry-pick).

## 2. Phân loại INV-81 (Primary Rule — Evidence First)

Đọc canonical definition trước khi đọc test:

```text
docs/spec/TASK-105D-DATA-CONTRACT.md:1205-1206
INV-81  Rollback của một PublicPurchaseSourceVersion = publish version mới với
        rollback_of, KHÔNG sửa/xoá version cũ (§3.3 câu 10).

docs/spec/TASK-105D-DATA-CONTRACT.md:248 (§3.3 câu 10)
"Rollback version thế nào? Không sửa, không xoá version đã publish. Publish
một version MỚI với rollback_of = <version lỗi> và nội dung khôi phục."
```

Đọc production behavior (không suy diễn từ tên test):

```text
app/modules/product/identity/public_purchase.py:157-221
  PublicPurchaseSourceLoader.load() — đường nạp DUY NHẤT (INV-03). Đọc
  data.get("rollback_of") trực tiếp (dòng 219) và gán vào
  PublicPurchaseSourceVersion.rollback_of. `rollback_of` là một khoá
  top-level HỢP LỆ (_TOP_LEVEL_KEYS, dòng 73) — production ĐÃ hỗ trợ publish
  một version với rollback_of qua đúng đường loader thật.

app/modules/product/identity/public_purchase.py:332-344
  PublicPurchaseSourceRepository.publish() — version_id đã tồn tại thì raise
  PublicPurchaseSourceError (reason="version_already_published"); không có
  đường edit-in-place nào. "Rollback = version mới, không phải edit" được
  chính repository thực thi bằng ràng buộc immutability này, không phải một
  API "rollback" riêng — không có API nào như vậy tồn tại (đúng theo §3.3 câu
  10: rollback CHÍNH LÀ một publish() thường, chỉ khác ở rollback_of).

$ grep -rn "rollback_of" app/
app/modules/product/identity/public_purchase.py:73   (khoá cho phép)
app/modules/product/identity/public_purchase.py:105  (field dataclass)
app/modules/product/identity/public_purchase.py:219  (parse từ data thật)
```

`rollback_of` không được đọc/rẽ nhánh ở bất kỳ nơi nào khác trong `app/` — nó
là metadata thụ động, không có logic đặc biệt nào phân biệt "version rollback"
với "version publish thường" ngoài giá trị của chính field đó.

Đọc test hiện tại (trước sửa):

```text
tests/test_105d_boundaries.py:744-752 (bản trước S048)
  rollback = fx.pp_version(version_id=fx.PP_V2)
  object.__setattr__(rollback, "rollback_of", fx.PP_V1)
  repo.publish(rollback)
```

`object.__setattr__` bơm thẳng field `rollback_of` vào một dataclass `frozen`
SAU khi nó đã được `fx.pp_version()` dựng xong qua loader thật — bỏ qua hoàn
toàn đường parse thật của `PublicPurchaseSourceLoader.load()` (dòng 219 ở
trên). Test chỉ chứng minh "field đã set thì đọc lại đúng", không chứng minh
loader thật CHẤP NHẬN và XỬ LÝ ĐÚNG khoá `rollback_of` khi nó đến từ input
thật — đúng nhận định của `H-06`/`S041`/`S047`.

```text
CÂU HỎI TRUNG TÂM: có thể chứng minh INV-81 bằng production behavior hiện có
mà KHÔNG sửa production code?
TRẢ LỜI: CÓ — production đã hỗ trợ đầy đủ qua loader + repository immutability.

CLASSIFICATION: A
  PRODUCTION BEHAVIOR EXISTS + TEST/EVIDENCE INSUFFICIENT
```

## 3. Sửa evidence cho INV-81 (thay đổi nhỏ nhất)

Hai file `tests/` bị chạm — KHÔNG chạm `app/`, `config/`, `Tracking`:

**`tests/support/identity_fixtures.py`** — thêm tham số `rollback_of` (mặc
định `None`, không đổi hành vi mọi lời gọi hiện có) vào `pp_version()`, đi
thẳng vào payload cho `PublicPurchaseSourceLoader.load()` — đúng khoá loader
thật đọc, không có đường tắt nào khác.

**`tests/test_105d_boundaries.py`** — viết lại
`test_inv81_a_rolled_back_pp_version_is_a_new_version_not_an_edit`: dựng
version rollback bằng `fx.pp_version(version_id=fx.PP_V2, rollback_of=fx.PP_V1)`
(đi qua loader thật) thay vì `object.__setattr__`. Assertion mạnh hơn bản cũ:

```python
assert repo.get(fx.PP_V1) == original          # version cũ 0 byte đổi
assert repo.get(fx.PP_V1).rollback_of is None  # rollback_of cũ không bị ghi đè
assert repo.get(fx.PP_V2).rollback_of == fx.PP_V1  # version mới mang đúng rollback_of
assert repo.get(fx.PP_V2) is not repo.get(fx.PP_V1)  # hai object riêng biệt
```

`repo.get(fx.PP_V1) == original` là assertion mới (bản cũ không có) — chứng
minh trực tiếp "KHÔNG sửa version cũ" bằng so sánh toàn bộ field (dataclass
`eq=True` mặc định), không chỉ một field `rollback_of`.

**Exact assertion proving invariant:**
`tests/test_105d_boundaries.py::TestMigrationRollbackHardening::test_inv81_a_rolled_back_pp_version_is_a_new_version_not_an_edit`
— 4 dòng assertion ở trên, PASS qua đúng `PublicPurchaseSourceLoader.load()`
+ `PublicPurchaseSourceRepository.publish()`/`.get()` thật.

```text
INV-81 = PASS
```

## 4. Phân loại INV-82

Canonical definition:

```text
docs/spec/TASK-105D-DATA-CONTRACT.md:1207
INV-82  Report đã ghim binding cũ replay không đổi sau rollback.
```

Test hiện có riêng cho INV-82
(`tests/test_105d_boundaries.py::test_inv82_a_report_pinned_to_the_old_binding_replays_unchanged`)
tự ghi trong docstring rằng chứng minh đầy đủ nằm ở
`TestG21ProvenanceActorAndReplay::test_part_c_replay_is_identical_after_store_catalog_and_price_change`.
`S047` xác nhận đúng — nhưng chưa xác minh ĐỘC LẬP xem G21 có thật sự phủ hết
nội dung `INV-82` hay không (khác với "generic new version" so với đúng
"rollback").

**Đọc G21 (`tests/test_105d_audit_replay.py:344-376`):**

```text
1. Seed một mapping, dựng binding pin vào pp_version_id = PP_V1.
2. before = replay_signature(replay.replay(rows, binding))
3. Đổi CẢ BA: store (_correct đổi mapping), catalog (tracking snapshot mới,
   capture khác), VÀ Public Purchase — publish MỘT VERSION MỚI (PP_V2) qua
   replay.pp_repository.publish(fx.pp_version(...)).
4. assert replay_signature(replay.replay(rows, binding)) == before.
```

Đây là "report đã ghim binding cũ (`PP_V1`) replay không đổi" sau khi một
version MỚI được publish — đúng cấu trúc của `INV-82`, qua đường replay THẬT
(`replay.replay()`), không chỉ đọc trực tiếp field trên repository như test
`test_inv82_…` hiện có (`content_hash` equality). G21 mạnh hơn: nó đi qua
toàn bộ pipeline resolve/replay + so khớp `replay_signature` đầy đủ, không
chỉ một field.

**Khác biệt duy nhất với "rollback" nghiêm ngặt:** version mới publish ở G21
không mang `rollback_of`. Xác minh độc lập (§2 ở trên, nhắc lại):
`rollback_of` là metadata thụ động — không có nhánh logic nào trong `app/`
đọc/rẽ nhánh theo nó (`grep -rn "rollback_of" app/` chỉ trả về 3 dòng, đều ở
`public_purchase.py`: khai báo khoá, khai báo field, parse — không có nơi nào
khác dùng nó để quyết định hành vi resolve/replay). Vì vậy một publish với
`rollback_of` KHÔNG khác một publish thường ở bất kỳ đường nào mà `replay()`
đi qua — G21 chứng minh trường hợp TỔNG QUÁT hơn (bất kỳ version mới nào),
nên nó chứng minh luôn trường hợp CON là "version mới là một rollback".

```text
G21 hiện đã có assertion cụ thể chứng minh chính xác INV-82?
TRẢ LỜI: CÓ — xác minh độc lập tại phiên này (không chỉ kế thừa self-report
của test_inv82_…), cộng bằng chứng rollback_of không được rẽ nhánh ở đâu khác.

CLASSIFICATION: B
  EXISTING TEST ALREADY PROVES INVARIANT + CANONICAL EVIDENCE BINDING INSUFFICIENT
```

## 5. Evidence binding cho INV-82 (không tạo test trùng lặp)

Theo đúng chỉ thị brief §6 — không viết test mới chỉ để mang tên `INV-82`.
Ghi canonical evidence binding tại đây (artifact này) thay vì sửa `tests/`:

```text
INV-82
  → docs/spec/TASK-105D-DATA-CONTRACT.md:1207 (định nghĩa)
  → tests/test_105d_audit_replay.py::TestG21ProvenanceActorAndReplay::
      test_part_c_replay_is_identical_after_store_catalog_and_price_change
      (tests/test_105d_audit_replay.py:344-376)
  → độc lập xác minh tại S048: rollback_of không rẽ nhánh ở app/ nào khác
    ngoài public_purchase.py (parse/khai báo khoá) — publish có rollback_of
    và publish thường đi qua CÙNG một đường replay/resolve.
  → PASS (chạy thật tại S048, §7)
```

`test_inv82_a_report_pinned_to_the_old_binding_replays_unchanged` giữ nguyên
100% (0 byte đổi) — nó vẫn là một assertion phụ hợp lệ (content_hash không
đổi sau publish version mới), không phải bằng chứng đầy đủ, và không cần là
bằng chứng đầy đủ vì G21 đã đủ.

```text
INV-82 = PASS
```

## 6. H-06 Disposition

```text
Trước: OPEN (S041, không đổi qua RC-1/S043/S044/S045/S046/S047)

H-06 → INV-81 evidence → tests/test_105d_boundaries.py::TestMigrationRollbackHardening::
  test_inv81_a_rolled_back_pp_version_is_a_new_version_not_an_edit (viết lại
  S048, qua PublicPurchaseSourceLoader.load() thật) → PASS

H-06 → INV-82 evidence → tests/test_105d_audit_replay.py::TestG21ProvenanceActorAndReplay::
  test_part_c_replay_is_identical_after_store_catalog_and_price_change
  (không đổi, xác minh độc lập phủ đúng INV-82 tại S048) → PASS

Sau: RESOLVED
```

Lý do RESOLVED (không chỉ vì test suite PASS): cả hai điều kiện `H-06` nêu
("`test_inv81_…` dùng `object.__setattr__`" và "`test_inv82_…` tự ghi chứng
minh đầy đủ nằm ở `G21`, chưa xác minh độc lập") đều đã được xử lý trực tiếp
— `object.__setattr__` đã bị loại bỏ khỏi `test_inv81_…`, và claim "`G21`
chứng minh đầy đủ" đã được xác minh độc lập (không chỉ kế thừa) bằng cách đọc
mã G21 + xác nhận `rollback_of` không được rẽ nhánh ở nơi khác. Re-trigger
condition gốc của `H-06` ("phiên đầu tiên implement migration/rollback thật")
không áp dụng ở đây — phiên này không implement migration/rollback MỚI, nó
chứng minh lại một hành vi rollback ĐÃ TỒN TẠI trong production
(`rollback_of` đã được loader hỗ trợ từ trước) bằng đúng đường sản xuất đó.

## 7. Validation sau evidence closure (chạy thật tại phiên này)

```text
$ python3 -m pytest tests/test_105d_boundaries.py -k "inv81 or inv82" -v
  test_inv81_a_rolled_back_pp_version_is_a_new_version_not_an_edit PASSED
  test_inv82_a_report_pinned_to_the_old_binding_replays_unchanged PASSED

$ python3 -m pytest tests/test_105d_audit_replay.py -k test_part_c_replay_is_identical -v
  test_part_c_replay_is_identical_after_store_catalog_and_price_change PASSED

$ python3 -m pytest tests/test_105d_*.py -q
  199 passed   (khớp tuyệt đối reference point S047 — sửa tại chỗ, không
                thêm test function mới, nên count không đổi)

$ python3 -m pytest tests/test_golden_baseline.py -q
  58 passed, 2 skipped   (khớp tuyệt đối)

$ python3 -m pytest -q
  965 passed, 11 skipped, 0 failed   (khớp tuyệt đối)
```

Production diff:

```text
$ git diff feb57a677ce8467ce4f422d2549eb6ecb9f5d3e7 -- app/ config/ Tracking
(rỗng)
PRODUCTION DIFF = 0
```

Frozen gate:

```text
$ sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md | sha256sum
0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
BEFORE = AFTER — byte-identical.
```

Canonical validators:

```text
validate_structure.py             : PASS (21 required paths)
validate_project_state.py         : PASS
validate_evidence.py              : PASS (88 REQUIRED PASS evidence record)
validate_reference_integrity.py   : FAIL — 3 issue, TASK-REM-T06 (baseline
                                     tiền tồn, không liên quan TASK-105D,
                                     không đổi so với S047)
validate_task_completion.py       : xem §8 — chạy LẠI sau khi Status: DONE
branch_authority_check.sh          : AUTHORITY_OK
```

## 8. INV-01…INV-87 — Recheck (không mở lại toàn bộ audit)

85/87 invariant đã có assertion qua 32 `CHECK-105D-*` (không đổi từ `S047`).
`INV-08` có lý do ghi rõ (không đổi). `INV-81`, `INV-82` nay `PASS` (§3, §5).

```text
INV-01…INV-87 = PASS
```

## 9. TASK-105D — Điều kiện DONE (đối chiếu lại toàn bộ 8 điều kiện S047)

```text
0 BLOCKING finding re-verify        : PASS (không đổi — không có finding nào
    chạm bởi phiên này)
Independent Review cho hành động DONE : PASS (đã thực hiện tại S047, không
    lặp lại — không có claim PASS mới nào cần review độc lập lại, phiên này
    chỉ đóng đúng MỘT điều kiện S047 để ngỏ)
INV-01…INV-87                        : PASS (§8 — thay đổi duy nhất so với
    S047)
progress/roadmap/handoff cập nhật     : khối này + PROJECT_PROGRESS.md +
    docs/sessions/S048-*.md (đang viết)
```

Không còn `NEAREST_REMAINING_BLOCKING_CONDITION` nào theo đúng danh sách mà
`S047` để lại. Toàn bộ 8 điều kiện binding của `DEC-159`/`DEC-161` cho `H-07`
giữ nguyên `PASS` (không đổi, phiên này không chạm gate/validator tooling).

**Authority cho việc ghi `Status: DONE`:** chỉ thị mở phiên `S048` tường minh
liệt kê toàn bộ điều kiện DONE, yêu cầu phiên tự đối chiếu, và tường minh cho
phép: *"Nếu authority cho phép: → cập nhật minimum canonical state/evidence →
TASK-105D = DONE"* — cùng cấu trúc chỉ thị mà `DEC-161` (`S046`) đã công nhận
là một Owner Decision cấp thẩm quyền cho đúng phạm vi hẹp của phiên đó. Áp
dụng tiền lệ đó: chỉ thị mở phiên `S048` là Owner Decision cấp thẩm quyền ghi
`TASK-105D = DONE` **nếu và chỉ nếu** mọi điều kiện ở trên thật sự `PASS` sau
khi đo lại — điều đó đã xảy ra ở phiên này. Ghi `DEC-162` (Owner Decision
record) tại `PROJECT/PROJECT_DECISIONS.md` để đóng dấu quyết định này theo
đúng khuôn `DEC-159`/`DEC-161`.

```text
TASK-105D = DONE  (§10 dưới đây — cập nhật Status field + validator re-run)
```

## 10. Cập nhật Status field + validator re-run (sau mutation)

`docs/tasks/TASK-105D-product-identity-resolver.md` dòng 5-6 (NGOÀI vùng
frozen 631-2359): `Status: READY` → `Status: DONE`, kèm `Status Note:` mới
(đúng khuôn `TASK-101`/`TASK-108A-1`). Exit Criteria (dòng 2378-2388, cũng
NGOÀI vùng frozen) đánh dấu `[x]` kèm ghi chú ngắn.

```text
$ sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md | sha256sum
0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
(khớp tuyệt đối §7 — 0 byte đổi trong vùng frozen)

$ python3 governance/scripts/governance/validate_task_completion.py
TASK COMPLETION: PASS
Checked 7 DONE task(s).
(6 trước + TASK-105D — Layer 2 kích hoạt thật lần đầu trên dữ liệu thật,
32/32 CHECK-105D-* PASS qua GATE_SET_SHA256 = 0444e58c…, 0 lỗi)

$ python3 governance/scripts/governance/validate_structure.py
GOVERNANCE STRUCTURE: PASS

$ python3 governance/scripts/governance/validate_project_state.py
PROJECT STATE: PASS

$ python3 governance/scripts/governance/validate_evidence.py
EVIDENCE VALIDATION: PASS

$ python3 governance/scripts/governance/validate_reference_integrity.py
REFERENCE INTEGRITY: FAIL — 3 issue, TASK-REM-T06 (không đổi, baseline
tiền tồn, không liên quan TASK-105D)
```

## 11. Task Registration Guard

```text
SET A — REGISTERED_TASK_SET: BEFORE = 13   AFTER = 13   (không đổi — TASK-105D
  đã đăng ký từ trước, chỉ đổi trạng thái, không phải một ID mới)
SET B — TASK_SPEC_SET (docs/tasks/*.md): BEFORE = 22   AFTER = 22 (không đổi)
new_registered_task_ids = 0
```

## 12. Repair Budget

```text
TASK-105D: allowed = 2, used = 1, remaining = 1   (KHÔNG ĐỔI)
RC-2 OPENED? NO
```

Toàn bộ thay đổi ở phiên này là test-strengthening + evidence-binding +
completion-evidence correction (Status field ngoài frozen gate) — theo brief
§12, đây KHÔNG phải production repair, nên KHÔNG tiêu Repair Cycle.

## 13. Ranh giới đã xác nhận KHÔNG vượt

```text
- app/**, config/**, Tracking                            : 0 byte đổi
- Frozen gate (dòng 631-2359)                             : 0 byte đổi
- GATE_SET_SHA256                                          : không đổi
- 32 khối check embedded Status (NOT_TESTED literal)       : không đổi
- Repair Cycle #2                                          : KHÔNG mở
- Task ID mới                                              : KHÔNG tạo
- TASK-105B/C/E/108B                                       : không chạm
- V4.2 migration                                            : không thực hiện
- Default branch / merge                                    : không chạm
- BH62063 (Golden Order vertical)                           : không implement
```

## 14. Kết Luận

```text
TASK-105D = DONE

INV-81 PASS.  INV-82 PASS.  H-06 RESOLVED.
INV-01…INV-87 PASS. H-07 CLOSED (không đổi).
32/32 REQUIRED PASS. B-01 CLOSED (không đổi). unresolved BLOCKING = 0.
Golden 58+2, targeted 199, full 965+11+0, production diff = 0.
Frozen gate byte-identical. Repair budget 2/1/1 không đổi. RC-2 KHÔNG mở.
Registry không đổi.

NEXT VERTICAL CRITICAL PATH:
  Golden Order BH62063 — persist END_TO_END_ACCEPTANCE = DEFINED, sau đó
  chạy hệ thống hiện tại AS-IS để tìm FIRST_FAILING_BOUNDARY. KHÔNG implement
  trong S048.
```
