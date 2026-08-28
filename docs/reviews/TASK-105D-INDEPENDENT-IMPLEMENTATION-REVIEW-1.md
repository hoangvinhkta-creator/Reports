# TASK-105D — INDEPENDENT IMPLEMENTATION REVIEW #1

## Metadata

Reviewed By:
Phiên Independent Implementation Review #1 — nhánh
`review/task-105d-implementation-1`. Reviewer KHÔNG phải tác giả
implementation (`S040`); KHÔNG kế thừa kết luận PASS của `S040`.

Timestamp:
2026-08-28

Evidence Level:
E2 — toàn bộ kết luận dưới đây có lệnh đã thực thi hoặc trích dẫn mã nguồn
tương ứng. Không mục nào ghi PASS/FAIL mà không có bằng chứng chạy thật.

Implementation target SHA:
`e6252c06347ed5305fc32a77706a3a63f5a950cf`

Implementation base SHA:
`222844dfb5cf576238fda4cc913ef2095789b4eb`

Selected Profile:
PRODUCT

Current Task Mode:
MAJOR

Risk:
Effective Risk `HIGH` — `max(Local Risk 4, Blast Radius 5)`, đường lỗi
`sai identity → sai nguồn giá → sai KpiPurchasePrice → sai KPI/lương`.

Verdict:
**FAIL — REPAIR REQUIRED** (1 BLOCKING).

---

## 1. Pre-flight

```text
branch                : review/task-105d-implementation-1     OK
HEAD                  : e6252c06347ed5305fc32a77706a3a63f5a950cf  OK
implementation base   : 222844dfb5cf576238fda4cc913ef2095789b4eb  OK (parent của HEAD)
worktree              : clean (git status --porcelain rỗng)     OK
```

---

## 2. Freeze integrity — tái lập ĐỘC LẬP

```text
$ sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md | sha256sum
0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877  -

$ sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md | wc -c
57614
```

KHỚP TUYỆT ĐỐI với `GATE_SET_SHA256` của bản freeze `S038`, và khớp cả số byte
đã công bố (57.614). Biên khối được kiểm thủ công: dòng 631 là
`#### CHECK-105D-01 (G01) …`, dòng 2359 là dòng cuối trước
`### Ma trận overlap có chủ đích`. Khối gate KHÔNG bị sửa một byte.

Diff duy nhất trên file task nằm **ngoài** khối frozen — mục
`Đăng Ký File Đã Thay Đổi (Changed Files Registry)` ở cuối file.

### 2.1 Quyết định giữ `Status = NOT_TESTED` — đánh giá

Diễn giải của `S040` là **ĐÚNG**:

```text
frozen gate definition  ≠  execution result
```

Bản freeze tự nó nói "Thay đổi gate sau thời điểm này — bất kỳ sửa đổi nào làm
đổi `GATE_SET_SHA256` — cần một `COMPLETION GATE CHANGE PROPOSAL` mới +
authority". Ghi `PASS` vào 32 trường `Status:` sẽ đổi từng byte của khối và do
đó đổi SHA. Phiên implementation không có authority đó. Ghi kết quả ra một
artifact riêng là lựa chọn duy nhất giữ được khả năng tái lập hash — và chính
nhờ nó phiên review này tái lập được `0444e58c…` bằng đúng một lệnh.

**Nhưng governance THỰC SỰ yêu cầu mutation về sau.**
`governance/core/TASK_COMPLETION_GATE_STANDARD.md` (dòng 75):

> Bất kỳ REQUIRED check nào là FAIL, BLOCKED, hoặc NOT_TESTED đều ngăn task
> đạt DONE, trừ khi được đánh dấu rõ ràng là NOT_APPLICABLE kèm lý do hợp lệ.

Và chính khối freeze viết: "Việc chuyển `NOT_TESTED → PASS` thuộc phiên
implementation."

Hai câu này căng nhau. Đây **không** phải finding chống lại implementation —
`S040` xử lý đúng trong giới hạn thẩm quyền của nó — mà là một bước governance
còn treo: `TASK-105D` KHÔNG THỂ đạt `DONE` khi 32 trường `Status:` còn đọc
`NOT_TESTED`. Ghi thành `HARDENING H-07`, gửi tới một phiên có gate authority,
KHÔNG gửi tới phiên implementation. Reviewer này KHÔNG sửa gate.

---

## 3. Phạm vi diff đã review

```text
$ git diff --stat 222844df e6252c0
30 files changed, 9014 insertions(+), 5 deletions(-)
```

| Nhóm | File | Nhận xét |
|---|---|---|
| domain model | `identity.py`, `keys.py`, `mapping.py`, `evidence.py` | union đóng, enum đóng, dataclass frozen |
| resolver | `resolver.py` (743) | đọc thuần; quét CẢ HAI namespace trước khi kết luận |
| candidates | `evidence.py`, `resolver.py::_rank` | khoá sort thuần dữ liệu, không `hash()`/dict order |
| catalog | `tracking_catalog.py` | snapshot frozen, repository chỉ `register`/`get` |
| Public Purchase | `public_purchase.py` (353) | MỘT loader, HAI projection, strict |
| persistence | `store.py` (931) | JSONL append-only + fsync + index `os.replace` |
| alias index | `store.py::StoreView.alias_index` | *view* dựng lại từ log, không state riêng |
| rejection memory | `rejection.py`, `resolver.py::_apply_rejection_memory` | fingerprint tính TRƯỚC khi suppress |
| cross-system | `cross_system.py`, `service.py::lookup_public_purchase_code` | 1:1, conflict tường minh, không đoán mã |
| historical registry | `registry.py` (323) | store append-only riêng, revision riêng |
| audit | `audit.py` | actor REQUIRED, `ACTOR_DISCLOSURE`, enum đóng |
| idempotency | `store.py::append` | hai lớp, thứ tự kiểm là hợp đồng |
| concurrency | `store.py::_require_version` | **xem B-01** |
| binding/replay | `binding.py` | ghim CẢ BỐN, thiếu = lỗi cứng |
| CLI | `cli.py` (275) | argparse, `--actor-id` bắt buộc, KHÔNG nhận đường dẫn |
| tests | 5 file + `identity_fixtures.py` | 174 test |
| governance evidence | gate record, session S040, PROGRESS | xem §14 |

**Dead code:** không. Cả 19 module đều được tham chiếu.
**Duplicated source-of-truth:** không. `AliasMemory` là view (`alias_index()`
dựng lại từ `_mappings` đã chiếu), không phải store thứ hai.
**Hidden fallback:** không tìm thấy. `binding.py`, `public_purchase.py`,
`tracking_catalog.py` đều raise thay vì rơi về "mới nhất".
**Silent error:** không. Mọi đường lỗi raise một exception có tên miền.
**Non-determinism:** không. `_rank()` sort theo `(rank phương thức, namespace,
mã)` — toàn giá trị dữ liệu.
**Scope creep:** không. `app/pipeline.py` không được nối vào package identity;
`PendingPriceProvider` vẫn là default.

```text
$ git diff 222844df e6252c0 -- app/pipeline.py                                 → 0 dòng
$ git diff 222844df e6252c0 -- app/modules/pricing/file_price_provider.py      → 0 dòng
$ git diff 222844df e6252c0 -- tests/test_golden_baseline.py                   → 0 dòng
$ git diff 222844df e6252c0 -- tests/fixtures                                  → 0 dòng
```

---

## 4. Pure resolve — ĐÁNH GIÁ ĐỘC LẬP: ĐÚNG, và trên thực tế là BẮT BUỘC

`S040` chọn `resolve()` = phép đọc thuần, nên `CATALOG_EXACT_UNIQUE`
auto-resolve **không** persist mapping. Reviewer không dựa vào lập luận của tác
giả mà dựng lại từ frozen contract:

- `CHECK-105D-24` yêu cầu `current_revision()` KHÔNG đổi trước/sau **cả một
  batch**, và fixture bắt buộc của nó trộn thêm "ít nhất một identity chưa
  biết". Nếu auto-resolve persist, một identity chưa biết khớp
  `CATALOG_EXACT_UNIQUE` sẽ làm revision tăng ⇒ `G24` FAIL.
- `CHECK-105D-04` cấm mọi lệnh ghi trên read path, "kể cả một lần touch
  `updated_at`".
- `INV-70` yêu cầu import lại cùng file cho 0 mapping mới / 0 audit mới /
  revision không đổi.

Ba điều đó cộng lại **loại trừ** phương án persist-on-auto-resolve. Không có
điều khoản nào trong contract yêu cầu confirmed mapping phải persist ngay tại
thời điểm auto-resolve; `mapping_source = DETERMINISTIC_CATALOG_MATCH` là một
giá trị enum của bản ghi mapping, không phải một mệnh lệnh persist.

Kiểm chứng:

```text
0-confirmation ⇏ bắt buộc persistence      : ĐÚNG — không invariant nào bắt
repeated deterministic catalog lookup      : ĐÚNG — cùng snapshot ⇒ cùng kết quả
AliasMemory không bị yêu cầu sai           : ĐÚNG — alias chỉ sinh từ command
INV-70 / idempotency                       : KHÔNG bị phá (đo ở case M, §9)
downstream nhận đủ provenance              : ĐỦ — raw, namespace, code,
    mapping_source, resolution_method, resolved_at, pp_version_id,
    tracking_capture_id. `mapping_id`/`mapping_version` = None, đúng với
    contract §Provenance ("mapping_id / mapping_version (nếu có)").
```

Kết luận: **KHÔNG BLOCKING.** Quyết định đúng.

---

## 5. Cutover boundary — vùng trọng yếu

`resolve_batch()` nhận một **factory** và chỉ gọi khi tồn tại ít nhất một dòng
post-cutover (`service.py:100-112`). Reviewer dựng instrumentation đối kháng
riêng (spy raise ngay khi bị gọi):

```text
[1] pre-cutover, registry rỗng : factory calls = 0 | PENDING_HISTORICAL_CONFIRMATION
[2] late import (sale_date 2026-08-20) : factory calls = 0 | historical route = True
[3] SalesRowRef fields = ['order_id','sale_date','raw_product_identity','source_system']
[4] biên 2026-09-01            : factory calls = 1 | resolutions = 1
[5] batch trộn 5 cũ + 5 mới    : factory calls = 1 | historical = 5 | distinct = 5
```

Vì resolver **không được dựng**, không có đường nào đọc current Tracking
catalog, current Public Purchase identity catalog, hay gọi price composition —
`INV-47` được thi hành **bằng cấu trúc**, không bằng một `if` bên trong
resolver. `import_date` không tồn tại như một trường ⇒ `INV-48` không thể vi
phạm bằng nhầm lẫn ([3]).

Kết luận: **PASS.** Không có current catalog read nào trên nhánh pre-cutover.

---

## 6. Auto-resolution authority — không tìm thấy bypass

`_guard_authority()` (`store.py:305`) đặt luật ở tầng `append()` — đường ghi
duy nhất — nên nó áp cho bootstrap, migration và mọi script vận hành. Ma trận
đối kháng do reviewer chạy:

```text
BootstrapMapping   SIMILARITY_RANKED      -> BLOCKED (SimilarityAuthorityError)
BootstrapMapping   ALIAS_AID_UNIQUE       -> BLOCKED
BootstrapMapping   TRACKING_ALIAS_MAP     -> BLOCKED
BootstrapMapping   CROSS_NAMESPACE_TIE    -> BLOCKED
BootstrapMapping   MULTIPLE_EXACT         -> BLOCKED
BootstrapMapping   CATALOG_EXACT_UNIQUE   -> APPLIED   (đúng — thuộc tập auto-resolve)
ConfirmMapping     SIMILARITY_RANKED      -> APPLIED   (đúng — có confirmation_action)
ConfirmMapping     ALIAS_AID_UNIQUE       -> APPLIED   (đúng — có confirmation_action)
```

`AUTO_RESOLVE_METHODS` là một `frozenset` đúng hai phần tử ở cấp module, và
mọi câu hỏi "có được auto-resolve không" đi qua `is_auto_resolvable()`. Không
có nơi thứ hai. `ALIAS_AID_UNIQUE` nằm ở tầng candidate (`_discover_candidates`),
không ở tầng alias memory — nên nó không thể lọt vào đường auto.

Kết luận: **PASS.** Không có helper / fallback / CLI / deserialization /
rebuild / entry point thay thế nào vượt rào.

Một hệ quả phụ của cùng dòng code đó là finding `H-01` (§13).

---

## 7. DISTINCT-before-mapping

```text
[6] 10.000 row -> |D| = 50 trong 0.013s ; tổng line_count = 10.000
```

`distinct_identities()` dùng `dict` + `set` song song để tránh `in` trên list
(O(số order) mỗi dòng). Thứ tự trả về là thứ tự gặp lần đầu — ổn định. Tập
DISTINCT được lập TRƯỚC khi resolver được dựng (`service.py:106-107`), nên
không có đường nào phát sinh confirmation/audit/rejection theo từng dòng.

Kết luận: **PASS.** Thời gian và bộ nhớ hợp lý.

---

## 8. Các vùng còn lại

### 8.1 Canonical identity (§9)

```text
namespace=None      -> IdentityValueError      code=empty      -> IdentityValueError
namespace=str       -> IdentityValueError      code=whitespace -> IdentityValueError
code=None           -> IdentityValueError      code=0          -> IdentityValueError
Namespace("TRACKINGX") -> ValueError (enum đóng)
TRACKING:X != PUBLIC_PURCHASE:X  và  hash khác nhau
```

Pending KHÔNG thể biểu diễn bằng `None`/`""`/`0`: `PendingProduct` là một biến
thể riêng về kiểu, và `CanonicalProductIdentity` từ chối mọi giá trị rỗng.
Round-trip qua `to_record()`/`_mapping_from_record()` giữ nguyên namespace
(kiểm ở `G29`). **PASS.**

### 8.2 Public Purchase / OR-01 (§10)

Chín case dựng sai đều là LỖI LOAD với `reason` máy đọc được:

```text
unknown_top_level_key · missing_products_block · empty_products_block
price_key_absent_from_identity · folded_product_code_collision
alias_collides_with_other_product_code · missing_version_id
malformed_products_block · not_a_mapping
```

Không có nhánh nào biến lỗi shape thành "danh mục rỗng im lặng" — đúng lỗ hổng
`INV-02` chỉ ra ở `FilePriceProvider.from_yaml()`. `PublicPurchaseSourceLoader`
không có phương thức "chỉ nạp identity" hay "chỉ nạp prices" ⇒ không tồn tại
nguồn vận hành thứ hai (`OR-01`/`B6`). `publish()` từ chối `version_id` đã tồn
tại ⇒ published immutable ở đúng lớp repository. Module KHÔNG import
`FilePriceProvider`; `validated_price_rows()` trả dict thuần. **PASS.**
Không yêu cầu TASK-105B activation.

### 8.3 Tracking read-only (§11)

Không chỉ grep tên method: `TrackingCatalogSnapshot` là một `dataclass(frozen)`
chứa dữ liệu đã capture — **không có client nào được cấp**, write-capable hay
không. `TrackingSnapshotRepository` chỉ có `register()` (từ chối ghi đè) và
`get()`. `app/modules/product/identity/**` không import `requests`/`urllib`/
`socket`/firebase/RTDB (kiểm bằng grep toàn package).

Câu hỏi "có cần interface read-only để enforce structural safety không?" —
**không cần**: kiểu dữ liệu đã không có bề mặt ghi. Không có real mutation
risk ⇒ theo `V4.1` không phải blocking, và ở đây thậm chí không phải finding.
**PASS.**

### 8.4 Persistence (§12)

| Case | Kết quả |
|---|---|
| crash giữa append / partial final line | `MappingIntegrityError` — KHÔNG đọc thành state một nửa |
| tampering: xoá một dòng giữa log | `MappingIntegrityError` — phát hiện qua chuỗi `supersedes` |
| dòng không phải JSON | `MappingIntegrityError` |
| null byte trong dòng | `MappingIntegrityError` |
| xoá index → dựng lại từ log | kết quả giống hệt (`G09` fixture 2) |
| reopen sau restart | cùng mapping, cùng version; `client_request_id` được nạp lại từ log |
| deterministic reconstruction | `read_at_revision(R)` = chiếu log tới event R |
| append-only | không có `delete`/`truncate`/`update` trong bất kỳ interface nào |
| ordering | `revision` = số thứ tự event, đơn điệu, không tái sử dụng |
| fsync / atomicity | `write()` cả dòng + `flush` + `os.fsync` trước khi trả về |
| temp/rename | index ghi theo `write-temp` + `os.replace` |

Điểm mạnh đáng ghi: `_project()` thi hành `INV-33` bằng **chuỗi supersede** chứ
không bằng phép đếm — nên một correction hợp lệ (nhiều bản ghi `CONFIRMED`
trong log) không bị báo nhầm là lỗi, trong khi hai bản ghi **độc lập** thì nổ.

Claim "atomic" của một lần append là ĐÚNG trên một tiến trình. Claim
"idempotent" là ĐÚNG cả sau restart (`_load_log()` dựng lại
`_results_by_request` từ log — `store.py:684-694`). Claim **"khoá file"** thì
KHÔNG đúng — xem `B-01`.

Một nit: dòng log là JSON hợp lệ nhưng không phải bản ghi event đúng khuôn thì
raise `AttributeError`/`KeyError` thay vì `MappingIntegrityError`. Vẫn fail
closed, chỉ là chẩn đoán kém — `H-05`.

### 8.5 Idempotency (§14)

```text
[M] duplicate import: revision 1 -> 1 ; len(events) == 1 ; cùng tập kết quả
same request sau restart : ALREADY_APPLIED (nạp lại từ log)
reordered rows           : |D| và tập kết quả không đổi (khoá là tuple, không phải thứ tự)
correction cùng request ID : ALREADY_APPLIED — không supersede lần hai
duplicate rejection      : NO_CHANGE (kiểm `suppression_key` bốn phần)
no-op state update       : NO_CHANGE, không event, không tăng version
```

Thứ tự kiểm trong `append()` đúng và có chủ đích: idempotency lớp 1 **trước**
kiểm version — nếu ngược lại, một retry hợp lệ sẽ bị báo conflict sai. **PASS.**

### 8.6 Audit / actor (§15)

`actor_id` REQUIRED, `None`/`""`/`"   "`/`"\t\n"` đều bị `MissingActorError`
ngay tại `__post_init__` của command ⇒ không có đường nào đổi state mà bỏ qua
validation (mọi command kế thừa `Command`). Grep toàn package: **không** có
`os.environ`/`getenv`/`getuser`/`getpass`/`os.getlogin`, **không** có hằng số
`"system"` nào được dùng làm giá trị mặc định.

`ACTOR_DISCLOSURE` được gắn vào **mọi** bản ghi event (`to_record()`) và vào
output CLI, và `audit.py` giữ một danh sách cụm bị cấm ("authenticated",
"authenticated user", "danh tính đã xác thực") để test quét văn bản. Wording
Phase 1 là "khai báo của người vận hành" — đúng `OR-03`, không claim
authentication. Correction có `reason` REQUIRED (`REASON_REQUIRED_TYPES`),
supersession giữ bản cũ vĩnh viễn, replay kiểm ở §8.8. **PASS.**

### 8.7 AliasMemory (§16) và RejectedCandidate (§17)

Đối kháng A confirmed → correction to B → hành vi alias cũ:

```text
trước correction -> TRK-100
sau correction   -> TRK-200   | alias index size = 1
log giữ cả hai   -> ['TRK-100', 'TRK-200']
```

Alias cũ **không** tiếp tục auto-resolve sai: `_project()` ghi đè `active[key]`
theo chuỗi supersede, và `alias_index()` chỉ trả bản ghi ACTIVE. Không có
authority thứ hai để lệch.

Rejection:

```text
reject rồi chạy lại cùng evidence      -> candidate bị suppress
đổi pp_version_id                      -> candidate quay lại + note "đã từ chối tại …"
```

`_fingerprint()` được tính trên tập candidate **TRƯỚC** khi suppress — nếu tính
sau, mỗi lần từ chối sẽ đổi tập ⇒ đổi fingerprint ⇒ chính candidate vừa từ chối
lại hiện ra. Đây là chi tiết đúng và dễ làm sai. Trường vào hash đúng §7.3
(`pp_version_id`, `tracking_capture_id`, `sorted(candidate_set_ids)`,
`ranking_method_id`); `candidate_set_ids` được sort ⇒ không có hash churn do
thứ tự. Không có blacklist vĩnh viễn: `INV-35` được kiểm ở cả hai chiều.
**PASS.**

### 8.8 Binding / replay (§21)

Đối kháng: ghim binding → correction + capture mới + PP version mới → replay.

```text
replay giống hệt sau correction + capture mới + pp version mới : True
live resolve (không ghim) hiện là                              : TRK-200
```

Đây là **reconstruct thật** qua `ReportReplay.replay()` (đọc lại snapshot theo
`capture_id`, PP theo `version_id`, store theo `mapping_store_revision`,
registry theo `registry_revision`), so khớp bằng `replay_signature()` — bao gồm
cả toàn bộ tập candidate theo thứ tự, không chỉ object equality. Thiếu bất kỳ
thành phần nào trong bốn → `IncompleteBindingError` (4/4 case kiểm). Không có
tham số nào đọc "mới nhất". Repin là một `EventType` riêng có `reason`
REQUIRED. **PASS.**

### 8.9 Cross-system mapping (§19) và Historical registry (§20)

```text
lookup có mapping CONFIRMED      -> trả đúng public_purchase_code của mapping đó
lookup không có mapping          -> None (absence), KHÔNG mã dẫn xuất
mapping thứ hai cho cùng PP code -> CrossSystemConflictError, KHÔNG last-write-wins
reuse mapping đã confirm         -> current_revision() không đổi
```

`lookup_public_purchase_code()` chỉ có một `return` mang dữ liệu, và nó lấy từ
`mapping.public_purchase_code` — không có nhánh nào dựng mã từ `tracking_code`.
Điều kiện (a) của `INV-43` được ghi tường minh là thuộc `TASK-105E` và **không**
được implement ở đây ⇒ không absorb. Không có price lookup/composition nào
trong package (§8.2, và `G16` import-graph).

Registry: khoá `(order_id, raw_identity_key, sale_date)`; `confirmed_identity`
OPTIONAL đúng chỗ contract cho phép (`INV-50`); store append-only + revision
riêng để `ResolutionBinding` ghim được `registry_revision` độc lập; không phụ
thuộc current catalog; correction/audit theo cùng khuôn supersede. Không có
backfill giá hiện tại. **PASS.**

### 8.10 Security / input integrity (§23)

Ngoài §8.2 và §8.4: normalization giữ đúng khác biệt model —

```text
'iPhone 15 Pro'   vs 'iPhone 15 Pro Max'  : raw key khác, aid khác
'Máy giặt LG 9kg' vs 'Máy giặt LG 9 kg'   : raw key khác, aid khác
'Tủ lạnh Sam-sung' vs 'Tủ lạnh Samsung'   : raw key khác, aid khác
'SP-A1'           vs 'SP-A l'             : raw key khác, aid khác
NFC: composed vs decomposed cùng ký tự    : bằng nhau (đúng)
```

Path traversal: `cli.py` **không** nhận đường dẫn file nào (không có `open(`,
không có `Path(`); chỉ `--actor-id` và các tham số nghiệp vụ. Không có bề mặt
traversal.

PII: `SalesRowRef` cố ý chỉ mang `order_id`, `sale_date`,
`raw_product_identity`, `source_system` — không tên khách, SĐT, địa chỉ, IMEI.
`metrics.py` chỉ chứa số đếm và số hiệu version (`INV-86`). Không secret nào
được log. **PASS.**

### 8.11 Performance (§24)

Đo thật (append liên tiếp, có `index_path`):

```text
n = 100 -> 0.18 s
n = 400 -> 2.04 s
n = 800 -> 7.82 s
```

Rõ ràng O(n²) tổng thể: `_persist()` gọi `rebuild_index()`, và `rebuild_index()`
chiếu lại toàn bộ log. Nhưng chi phí **một** append ở n = 800 là ~19 ms và vẫn
dưới một giây cho tới cỡ 10.000 event. Workload thật bị chặn trên bởi `|D|` và
tiến về 0 sau khi ấm máy (reuse qua `ALIAS_EXACT` là đường đọc thuần, không
append). Vì vậy **không** promote lên BLOCKING — theo brief §24, không promote
dựa trên quan ngại lý thuyết. Ghi thành `H-04` cho bulk bootstrap/migration.

Đường đọc không bị O(n²): `resolve_batch` dựng **một** `StoreView` cho cả batch;
`_rank()`/`_apply_rejection_memory()` tuyến tính theo số candidate/rejection của
đúng identity đó. `distinct_identities()` tuyến tính theo số dòng (§7).

### 8.12 Test quality (§25)

```text
monkeypatch/mock trong toàn bộ test 105D : 3 lần — cả 3 là delenv DISPLAY/
    WAYLAND_DISPLAY cho test headless G22. KHÔNG có mock nào che persistence.
test dùng tmp_path (filesystem thật)     : 13
test có reopen-from-disk                 : có (G09, G10, INV-80)
object.__setattr__ (bypass frozen)       : 3 — dựng fixture, không assert
truy cập internals của implementation    : không (các `_ambiguous`/`_batch`/
    `_snapshot` là helper của chính file test)
174 test / 343 assert                    : ~2 assert mỗi test
```

Độc lập thứ tự — chạy từng file riêng và chạy đảo ngược thứ tự collection:

```text
audit_replay 19 · boundaries 41 · cutover_registry 14 · identity_keys 26
persistence 37 · resolution 37            (tổng 174, khớp)
đảo ngược thứ tự: 174 passed
```

Không phát hiện tautological test hay assertion trùng lặp implementation ở mức
đáng kể. Hai test **yếu** đã ghi ở `H-06`.

Một điểm mạnh cần ghi nhận: `fx.pp_version()` nạp qua
`PublicPurchaseSourceLoader.load()` thật thay vì dựng tắt — nên một fixture vi
phạm invariant sẽ nổ ngay tại fixture chứ không làm lệch một assertion khác.

**Điểm yếu duy nhất đáng kể của bộ test là concurrency** — xem `B-01`.

---

## 9. A–T — thực thi ĐỘC LẬP

Reviewer viết bộ đối kháng riêng trong scratchpad ngoài repo, KHÔNG chạy lại và
KHÔNG sao chép test của `S040`.

| Case | Nội dung | Kết quả | Bằng chứng quan sát được |
|---|---|---|---|
| A | DISTINCT | PASS | `\|D\| = 50` từ 10.000 dòng |
| B | known mapping | PASS | `ALIAS_EXACT`, revision + action count không đổi |
| C | catalog exact | PASS | `CATALOG_EXACT_UNIQUE`, `TRACKING:TRK-100`, 0 ghi |
| D | alias aid | PASS | `ALIAS_AID_UNIQUE`, candidate #1, `parent_mapping_id` có |
| E | fuzzy | PASS | `PENDING(ONLY_SIMILARITY_EVIDENCE)` |
| F | ambiguous | PASS | `MULTIPLE_EXACT` và `CROSS_NAMESPACE_TIE` đều không auto |
| G | no match | PASS | `NO_CANDIDATE_IN_ANY_CATALOG`, đủ cả hai catalog trong `attempted_sources` |
| H | PP direct | PASS | `PUBLIC_PURCHASE`, provenance `PUBLIC_PURCHASE_NO_TRACKING` |
| I | same code collision | PASS | `TRACKING:X != PUBLIC_PURCHASE:X`, hash khác |
| J | cross-system | PASS | lookup đúng, conflict raise, reuse revision không đổi |
| K | rejection | PASS | suppress cùng evidence; quay lại + note khi đổi `pp_version_id` |
| L | correction | PASS | supersede, bản cũ còn trong log, thiếu `reason` bị từ chối |
| M | duplicate import | PASS | revision 1 → 1, 1 event |
| N | concurrency | **PASS trong-tiến-trình / FAIL đa-tiến-trình** | xem `B-01` |
| O | Tracking rename | PASS | mapping sống sót, 0 ghi |
| P | Tracking disappears | PASS | mapping đã confirm giữ nguyên; identity MỚI → `MAPPING_STALE_TARGET_ABSENT` |
| Q | pre-cutover | PASS | spy = 0 |
| R | late import | PASS | `sale_date` thắng |
| S | actor | PASS | 4/4 biến thể thiếu actor bị từ chối |
| T | PP version/binding | PASS | binding đủ 4 OK; 4/4 case thiếu → lỗi cứng |

```text
A–T (theo nghĩa hẹp của từng case, chạy độc lập) : 20 / 20 PASS
```

`N` PASS ở đúng phạm vi mà case mô tả (hai confirmation trong một tiến trình).
Race thật nằm ở biên tiến trình và được báo riêng thành `B-01`, không phải bằng
cách đánh trượt case `N`.

---

## 10. 32 frozen check — thực thi ĐỘC LẬP

Mỗi lớp test được chạy riêng bằng `python3 -m pytest <ref> -q`.

```text
CHECK-105D-01 PASS (7)   -09 PASS (6)   -17 PASS (4)   -25 PASS (3)
CHECK-105D-02 PASS (5)   -10 PASS (9)   -18 PASS (5)   -26 PASS (2)*
CHECK-105D-03 PASS (3)   -11 PASS (1)   -19 PASS (4)   -27 PASS (2)*
CHECK-105D-04 PASS (1)   -12 PASS (6)   -20 PASS (7)   -28 PASS (11)
CHECK-105D-05 PASS (3)   -13 PASS (4)   -21 PASS (8)   -29 PASS (5)
CHECK-105D-06 PASS (5)   -14 PASS (3)   -22 PASS (3)   -30 PASS (5)
CHECK-105D-07 PASS (3)   -15 PASS (2)   -23 PASS (4)   -31 PASS (8)
CHECK-105D-08 PASS (3)   -16 PASS (3)   -24 PASS (1)   -32 PASS (8)

REQUIRED   : 32 / 32
PASS       : 32
FAIL       : 0
NOT_TESTED : 0
```

`*` Đường dẫn test trong `TASK-105D-GATE-EXECUTION-RECORD.md` cho hai check này
SAI — xem `H-03`. Lớp test tồn tại và PASS ở
`tests/test_105d_resolution.py::TestG26G27TrackingMissContinuesToPublicPurchase`.

Không trường `Status:` nào bị sửa. Bằng chứng thực thi nằm ở file này, tách
khỏi khối gate.

**Ngưỡng review PASS về mặt gate: 32/32 — ĐẠT.** Ngưỡng đó là điều kiện cần,
không phải điều kiện đủ: `B-01` là một finding ngoài phạm vi assertion của
`G20` fixture (1), và brief §13 yêu cầu reviewer không chấp nhận test
concurrency không tạo contention thật.

---

## 11. Regression

```text
Golden @ 222844df   : 58 passed, 2 skipped
Golden @ e6252c0    : 58 passed, 2 skipped        → KHÔNG ĐỔI

Targeted 105D       : 174 passed

Full suite @ 222844df : 756 passed, 11 skipped
Full suite @ e6252c0  : 930 passed, 11 skipped
delta                 : 930 - 756 = +174          → KHỚP CHÍNH XÁC số test mới
skipped               : 11 → 11                   → KHÔNG ĐỔI
regression            : 0
```

Delta được xác minh độc lập bằng một worktree tách riêng tại base SHA.

Validator governance:

```text
validate_structure           PASS
validate_project_state       PASS
validate_evidence            PASS  (88 REQUIRED PASS evidence record)
validate_task_completion     PASS  (6 DONE task)
validate_reference_integrity FAIL  — 3 issue, GIỐNG HỆT ở base 222844df
                                     (docs/tasks/TASK-REM-T06-…) → O-01
```

---

## 12. HB-105D-F2-03 — ánh xạ độc lập 13 invariant

`S040` **không** claim đóng HB-F2-03; nó giữ phân loại HARDENING. Reviewer
kiểm lại từng mục:

| INV | Implementation | Test | Có diễn tập hành vi? |
|---|---|---|---|
| `INV-08` | — | — | **Cố ý ngoài scope** — `FilePriceProvider` (FROZEN) thi hành. Khai báo đúng, không che. |
| `INV-26` | `keys.py` | `TestRawIdentityKey`, `TestNormalizedMatchingAid` | Có — chiều dấu tiếng Việt/punctuation, reviewer kiểm lại 4 cặp (§8.10) |
| `INV-51` | `registry.py::SourceReportRef` | `test_inv51_prose_only_confirmation_is_rejected` | Có |
| `INV-52` | `registry.py::lookup_key` | `test_inv52_lookup_key_is_order_identity_and_sale_date` | Có |
| `INV-53` | `registry.py` correction | 2 test | Có |
| `INV-65` | `export_bundle`/`import_bundle` | `test_export_then_import_is_bit_equivalent` | Có |
| `INV-79` | store rỗng = trạng thái đúng | `test_inv79_m0_…` | Có — resolve thật ra Pending |
| `INV-80` | reopen từ đĩa | `test_inv80_rollback_loses_no_confirmation` | Có — qua biên file thật |
| `INV-81` | repository immutable | `test_inv81_…` | **Yếu** — dùng `object.__setattr__` dựng fixture; không có rollback API thật để diễn tập |
| `INV-82` | repository immutable | `test_inv82_…` | **Yếu** — chỉ assert `content_hash` không đổi; chứng minh replay đầy đủ nằm ở `G21`, không ở đây |
| `INV-84` | `metrics.py` | `test_inv84_…` | Có |
| `INV-85` | import-graph assertion | `test_inv85_the_resolver_never_imports_metrics` | Có — phủ định cấu trúc, đúng loại |
| `INV-86` | `metrics.py` | `test_inv86_metrics_carry_no_customer_data` | Có |

Kết luận: 12/13 có test diễn tập hành vi; `INV-08` được khai là cố ý ngoài
scope, chính xác. Hai test (`INV-81`, `INV-82`) mỏng → `H-06`.
**HB-105D-F2-03 giữ nguyên HARDENING.** Phân loại của `S040` là đúng, không
phóng đại.

---

## 13. Findings

### BLOCKING

#### `B-01` — Không có khoá file: check-then-append race ở đúng biên "một máy" mà contract tuyên bố phủ

```text
Phân loại : BLOCKING
Cơ sở     : contract + data-integrity
Nguồn     : docs/spec/TASK-105D-DATA-CONTRACT.md §11.1, §10.3 (INV-58…INV-61)
Vị trí    : app/modules/product/identity/store.py::append / _require_version / _persist
```

Cả data contract §11.1 lẫn docstring của chính `store.py` (dòng 19) tuyên bố:

> Hạn chế phải ghi rõ, không giấu: JSONL + **khoá file** cho concurrency
> **một máy**. Nhiều người dùng đồng thời trên nhiều máy là bài toán Phase 2.

Nghĩa là: đa người dùng **trên một máy** nằm TRONG phạm vi Phase 1. Nhưng
`grep -rn "fcntl\|flock\|lockf\|LOCK_EX"` trên toàn `app/` trả **0 kết quả**.
Không có khoá file nào tồn tại, và `append()` không đọc lại log trước khi ghi —
`_require_version()` so `expected_version` với state **trong bộ nhớ** của
instance, vốn được nạp một lần lúc khởi tạo.

Tái lập (hai instance trên cùng một file log = hai tiến trình trên một máy):

```text
A append: AppendOutcome.APPLIED version 1
B append: AppendOutcome.APPLIED version 1   <-- KHÔNG raise MappingVersionConflict

--- log trên đĩa ---
1 CONFIRM_MAPPING code=TRK-A version=1 supersedes=None
2 CONFIRM_MAPPING code=TRK-B version=1 supersedes=None

--- một tiến trình thứ ba đọc store ---
MappingIntegrityError: INV-33: bản ghi … khai supersedes=None nhưng bản ghi
trước đó là … — hai bản ghi CONFIRMED độc lập cho cùng một khoá
```

Hai vi phạm cụ thể:

1. **`INV-59` bị phá.** `expected_version` cũ KHÔNG bị phát hiện; cả hai lệnh
   ghi được chấp nhận. Đây đúng là tình huống `User A / User B (cùng lúc)` mà
   §10.3 dựng ra để bắt buộc xử lý đúng.
2. **Store trở nên không đọc được VĨNH VIỄN.** Từ thời điểm đó mọi
   `read_at_revision()` — tức mọi `resolve`, mọi `append`, mọi replay — raise
   `MappingIntegrityError`. Và `INV-67` cấm DELETE trong mọi interface, `INV-66`
   cấm đường ghi bỏ qua domain contract, nên **không có đường phục hồi hợp lệ
   trong contract**.

Ghi nhận công bằng: append vẫn dùng `open(..., "a")` với một lần `write()` cho
cả dòng, nên log không bị trộn ký tự — hỏng hóc ở đây là **logic**, không phải
văn bản. Và implementation KHÔNG silent last-write-wins: nó nổ. Nhưng "nổ vĩnh
viễn sau khi đã ghi" không phải điều `INV-59` yêu cầu; `INV-59` yêu cầu **từ
chối trước khi ghi, không ghi gì**.

`CHECK-105D-20` Phần A vẫn PASS vì fixture của nó dùng **một** instance store —
đây đúng là "test concurrency không tạo contention thật" mà brief §13 yêu cầu
reviewer không chấp nhận. Và brief §13 phát biểu tiêu chí ngay:

> Nếu contract yêu cầu optimistic concurrency nhưng implementation không atomic
> ở boundary đã claim: BLOCKING.

Boundary đã claim là "một máy". Implementation không atomic ở đó.

**Hướng sửa gợi ý (thuộc phiên repair, KHÔNG thực hiện ở đây):** hoặc (a) thêm
khoá file `fcntl.flock` bao quanh chu trình *đọc-lại-log → kiểm version →
append* để claim §11.1 thành sự thật; hoặc (b) sửa data contract §11.1 và
docstring để thu hẹp phạm vi đã claim xuống **một tiến trình**, và bổ sung một
gate/test khẳng định biên đó. (a) giữ nguyên contract; (b) là một thay đổi data
contract cần authority riêng. Quyết định thuộc Owner / phiên repair.

### HARDENING

#### `H-01` — Tập ĐẾM `confirmation_action` bị dùng làm tập THẨM QUYỀN, khoá mất đường correction

```text
Vị trí : store.py::_guard_authority (dùng CONFIRMATION_ACTION_TYPES)
Nguồn  : data contract §17.1 (định nghĩa ĐẾM) vs §13/INV-74 (correction)
```

`CONFIRMATION_ACTION_TYPES` được §17.1 định nghĩa để **đếm** thao tác cho gate
UX (`G03`/`G23`/`G24`). `_guard_authority()` dùng chính tập đó làm tập **thẩm
quyền ghi**. Hệ quả đo được:

```text
correct với SIMILARITY_RANKED     -> BLOCKED   <-- correction của người bị từ chối
correct với ALIAS_AID_UNIQUE      -> BLOCKED   <-- correction của người bị từ chối
correct với CATALOG_EXACT_UNIQUE  -> APPLIED
correct với ALIAS_EXACT           -> APPLIED
```

`CORRECT_MAPPING` là đường override chính tắc của con người (§13, `INV-74`,
`G18`) và đòi hỏi `reason` + `actor` + audit. Trên thực tế một correction gần
như luôn đến từ tìm kiếm thủ công sau khi máy đoán sai — tức `MANUAL_SEARCH` /
`SIMILARITY_RANKED`. Đúng case phổ biến nhất đó lại bị chặn.

Không có data-integrity risk (fail closed, không ghi gì), nên **HARDENING**,
không BLOCKING. Nhưng nó làm một workflow bắt buộc của contract không dùng
được ngoài fixture.

**Re-trigger:** phiên Repair Cycle #1 của `TASK-105D` (cùng lượt với `B-01`),
hoặc phiên đầu tiên nối permission model `DEC-124` vào correction — tuỳ phiên
nào đến trước.

#### `H-02` (kế thừa `H-05`) — `ranking_method_id` OPTIONAL nhưng được hash

```text
Phân loại độc lập : RESOLVED_AT_IMPLEMENTATION_ONLY — contract text VẪN OPEN
```

Đánh giá độc lập theo bốn tiêu chí của brief §18:

```text
contract ranking_method_id vẫn OPTIONAL          : ĐÚNG (§6.7 không đổi)
implementation luôn cung cấp nó                  : ĐÚNG (RANKING_METHOD_ID gắn
                                                   trong _rank() cho MỌI candidate)
trường vắng dùng sentinel tường minh trong hash   : ĐÚNG (_ABSENT_RANKING_METHOD
                                                   = "\x00<absent>", không bỏ
                                                   trường ra khỏi hash)
test đã bổ sung                                  : ĐÚNG (TestG12…::
                                                   test_fixture_2b_a_new_ranking_
                                                   method_brings_the_candidate_back)
```

Xử lý của `S040` là đúng mức thẩm quyền và **tự khai báo rằng contract vẫn
OPEN** (`evidence.py` docstring: "Trạng thái contract-level của `H-05` vẫn
OPEN"). Reviewer **KHÔNG** đánh dấu finding contract là resolved.

**Re-trigger chính xác cho phần contract còn lại:** một phiên có thẩm quyền sửa
`docs/spec/TASK-105D-DATA-CONTRACT.md` phải làm MỘT trong hai:
(a) đổi `§6.7 ranking_method_id` từ `OPTIONAL` → `REQUIRED`; hoặc
(b) giữ `OPTIONAL` nhưng quy phạm hoá giá trị sentinel dùng trong `§7.3`
`evidence_fingerprint` (nêu đúng giá trị, để một producer bên ngoài tái lập
được cùng fingerprint).
Cho tới khi một trong hai xảy ra, `H-05` **KHÔNG được ghi là closed**.

#### `H-03` — Test reference sai trong Gate Execution Record (E2 không tái lập được nguyên văn)

`docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md` liệt kê `CHECK-105D-26` và
`CHECK-105D-27` dưới dạng `…::TestG26G27…`, nối tiếp dòng `CHECK-105D-25` vốn
trỏ `tests/test_105d_boundaries.py`. Lớp test thật nằm ở
`tests/test_105d_resolution.py`.

```text
$ python3 -m pytest "tests/test_105d_boundaries.py::TestG26G27TrackingMissContinuesToPublicPurchase" -q
ERROR: not found

$ python3 -m pytest "tests/test_105d_resolution.py::TestG26G27TrackingMissContinuesToPublicPurchase" -q
2 passed
```

Gate vẫn PASS; chỉ là con trỏ evidence sai. Với `Evidence Level = E2`, một
reference phải tái lập được nguyên văn.
**Re-trigger:** phiên kế tiếp chạm `TASK-105D-GATE-EXECUTION-RECORD.md`.

#### `H-04` — `rebuild_index()` O(n) mỗi append ⇒ O(n²) cho bulk

Đo: 100 → 0,18 s; 400 → 2,04 s; 800 → 7,82 s. Chấp nhận được cho workload
Phase 1 (số `confirmation_action` bị chặn bởi `|D|` và tiến về 0 nhờ reuse;
một append đơn lẻ ở n = 800 tốn ~19 ms). **Không** promote lên BLOCKING.
**Re-trigger:** phiên bootstrap/migration nạp > 1.000 mapping, hoặc phiên
chuyển store sang cơ chế Phase 2.

#### `H-05` — Dòng log JSON hợp lệ nhưng sai khuôn raise lỗi không thuộc miền

`AttributeError` / `KeyError` thay vì `MappingIntegrityError`. Vẫn fail closed
(không có state một nửa), chỉ kém chẩn đoán.
**Re-trigger:** cùng lượt với bất kỳ sửa đổi nào trên `store.py::_load_log`.

#### `H-06` — Hai test migration/rollback mỏng

`test_inv81_…` dùng `object.__setattr__` để dựng fixture trên một dataclass
frozen và thực chất chỉ assert repository immutability; `test_inv82_…` chỉ
assert `content_hash` không đổi thay vì diễn tập một replay sau rollback (test
tự ghi chú rằng chứng minh đầy đủ nằm ở `G21`). Không phải claim sai của
`S040` — nó giữ HB-105D-F2-03 ở HARDENING.
**Re-trigger:** phiên đầu tiên implement migration/rollback thật.

#### `H-07` — 32 trường `Status:` còn `NOT_TESTED` chặn `DONE`

Xem §2.1. Không phải lỗi của implementation. Cần một phiên có gate authority
mở `COMPLETION GATE CHANGE PROPOSAL` để chuyển `NOT_TESTED → PASS` (kèm chấp
nhận `GATE_SET_SHA256` mới), hoặc một quyết định Owner tường minh rằng bản ghi
thực thi tách rời là đủ cho `DONE`.
**Re-trigger:** trước khi bất kỳ phiên nào đề xuất `TASK-105D = DONE`.

### OUT_OF_SCOPE

```text
O-01  validate_reference_integrity FAIL — 3 reference trong
      docs/tasks/TASK-REM-T06-repository-root-hygiene.md. GIỐNG HỆT tại base
      222844df. Có trước, không liên quan TASK-105D.
O-02  HB-105D-F2-01 — "bộ ba" (§3.3 câu 8) vs "CẢ BỐN" (E-L/INV-55).
      VẪN OPEN. S040 báo cáo divergence trong docstring binding.py thay vì tự
      dàn xếp — đúng V4.1 §11. Cần phiên sửa data contract.
O-03  HB-105D-F2-02 — §16.1 stale ở hai điểm. VẪN OPEN, documentation-only.
```

Không có finding trùng lặp: `B-01` (thiếu khoá file) và `H-01` (tập thẩm quyền
sai) chạm hai dòng code khác nhau vì hai lý do khác nhau.

---

## 14. Ranh giới đã xác minh KHÔNG bị vượt

```text
implementation branch bị reviewer sửa   : KHÔNG
app/** hay tests/** bị reviewer sửa     : KHÔNG (git status sạch trước khi ghi
                                          artifact review này)
production config đổi                   : KHÔNG
Tracking bị chạm                        : KHÔNG — 0 đường ghi tồn tại
production data                         : KHÔNG tạo; toàn bộ fixture tổng hợp
FilePriceProvider activate               : KHÔNG — diff file = 0 dòng
TASK-105E implement                      : KHÔNG — P00–P11 vắng mặt hoàn toàn
default branch đổi                       : KHÔNG
merge                                    : KHÔNG thực hiện
```

Script đối kháng của reviewer nằm trong scratchpad ngoài repo và **không**
được commit (brief §31 — evidence tooling không được commit trừ khi
governance cho phép tường minh).

---

## 15. Review Budget

```text
TASK-105D trước review : 2 allowed / 0 used / 2 remaining
Independent review     : KHÔNG tiêu thụ Repair Cycle (V4.1 §3 — cycle tính
                         theo repair diff của implementation; phiên này 0 dòng
                         code/test)
TASK-105D sau review   : 2 allowed / 0 used / 2 remaining  (KHÔNG ĐỔI)
```

Có `B-01` ⇒ **khuyến nghị mở Repair Cycle #1**. Reviewer KHÔNG tự repair.
Sau khi phiên repair thực hiện: `2 allowed / 1 used / 1 remaining`.

---

## 16. Verdict

```text
FAIL — REPAIR REQUIRED

BLOCKING     : 1   (B-01)
HARDENING    : 7   (H-01 … H-07)
OUT_OF_SCOPE : 3   (O-01, O-02, O-03)

32 frozen check          : 32 / 32 PASS (thực thi độc lập)
A–T                      : 20 / 20 PASS (bộ đối kháng riêng của reviewer)
Golden                   : 58 passed, 2 skipped — KHÔNG ĐỔI
Full suite               : 930 passed, 11 skipped (base 756 + đúng 174)
Regression               : 0
GATE_SET_SHA256          : tái lập KHỚP tuyệt đối
```

Ghi rõ để không bị đọc nhầm: chất lượng tổng thể của implementation này **cao**
— 32/32 gate PASS thật, A–T 20/20 PASS dưới bộ test độc lập, 0 regression,
ranh giới scope giữ sạch, và `S040` tự khai báo trung thực các hardening còn
mở thay vì đánh dấu chúng đã đóng. `B-01` là **một** khiếm khuyết cụ thể ở
đúng một biên mà chính contract tuyên bố phủ, không phải một đánh giá chung về
implementation.

`TASK-105D` **KHÔNG** phải `DONE`. `TASK-105D` **KHÔNG** eligible for
integration cho tới khi `B-01` được đóng.

---

## 17. Next authorized action

```text
1. Owner quyết định hướng đóng B-01:
     (a) thêm khoá file quanh chu trình đọc-lại → kiểm version → append
         (giữ nguyên data contract §11.1); HOẶC
     (b) thu hẹp phạm vi đã claim ở data contract §11.1 + store.py docstring
         xuống MỘT TIẾN TRÌNH, kèm gate/test khẳng định biên mới
         (đây là thay đổi data contract, cần authority riêng).
2. Repair Cycle #1 cho TASK-105D thực hiện quyết định trên, cộng H-01.
   Sau repair: 2 allowed / 1 used / 1 remaining.
3. Independent Implementation Review #2 (phiên KHÁC) trên SHA sau repair.
4. CHỈ SAU (3) PASS: quyết định integration vào default theo V4.1 §8.
5. Song song, không chặn: phiên có thẩm quyền data contract đóng H-02 (H-05),
   O-02, O-03; phiên có gate authority xử lý H-07 trước khi đề xuất DONE.
```

**STOP.** Phiên này dừng ở review state. Không repair, không merge, không
đánh dấu DONE.
