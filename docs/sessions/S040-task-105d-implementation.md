# S040 — TASK-105D Product Identity Resolver: Implementation

Session Type:
IMPLEMENTATION — phiên cấp phép riêng theo Owner authorization. Đây **không**
phải phiên review, **không** phải phiên freeze, **không** phải phiên
integration. Phiên này **không** tự independent-review implementation của
chính nó.

Date:
2026-08-28

Current Task Mode:
MAJOR

Selected Profile:
PRODUCT

Branch:
`task/task-105d-implementation`

Base SHA:
`222844dfb5cf576238fda4cc913ef2095789b4eb`
(= nhánh mặc định `claude/extract-upload-repo-gq2ws4` tại thời điểm mở phiên;
worktree sạch)

Risk:
Effective Risk `HIGH` — `max(Local Risk 4, Blast Radius 5)`, đường lỗi
`sai identity → sai nguồn giá → sai KpiPurchasePrice → sai KPI/lương`. Golden
hiện chỉ phủ `PendingPriceProvider`, nên **không** hạ bậc theo `V4.1` §4.1.
Đây đúng giá trị canonical ghi ở `docs/tasks/TASK-105D-product-identity-resolver.md`
→ Metadata; phiên này không tính lại thành một con số khác.

Authority:
`DEC-154` (semantics), `DEC-155` (data contract), `DEC-156` (`OR-01`/`OR-02`/
`OR-03`), `DEC-157` (gate revision #1 + `V4.1` §8 Option C), `DEC-158`
(controlled integration). Completion Gate `FROZEN` bởi `S038`.

## 0. Pre-flight

```text
branch          task/task-105d-implementation      ✔
HEAD            222844dfb5cf576238fda4cc913ef2095789b4eb   ✔
origin default  222844dfb5cf576238fda4cc913ef2095789b4eb   ✔
worktree        clean                              ✔
```

## 1. Freeze integrity — tái lập TRƯỚC khi viết dòng code đầu tiên

```text
$ sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md | wc -c
57614
$ sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md | sha256sum
0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877  -
```

Khớp tuyệt đối `GATE_SET_SHA256` của bản freeze `S038`, và khối gate được so
byte-wise với chính bản tại SHA freeze `be835b1` — không khác biệt. Chi tiết +
lý do `TASK_FILE_SHA256` khác (do `S039` thêm bằng chứng freeze **ngoài** khối
gate): `docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md` §5.1.

Phiên này **không sửa một byte nào** trong khối gate đã freeze. Kết quả thực
thi 32 check được ghi ở một artifact riêng, đúng lý do trình bày tại §1 của
bản ghi đó.

## 2. Kiến trúc đã triển khai

`app/modules/product/identity/` — 19 module, ánh xạ 1:1 với các entity của data
contract, không có god-file:

```text
keys.py               hai khoá §6.3 (raw_identity_key / normalized_matching_aid)
identity.py           E-E + ResolutionOutcome (union ĐÓNG, tự seal)
evidence.py           §6.6/§6.7 + tập auto-resolve đóng + evidence_fingerprint
tracking_catalog.py   E-D (read-only, INV-11…INV-16)
public_purchase.py    E-A/E-B/E-C + loader STRICT (INV-02…INV-10)
mapping.py            E-F + E-G (AliasMemory là VIEW, không phải store thứ hai)
rejection.py          E-H
cross_system.py       E-I
registry.py           E-J + CUTOVER_DATE
audit.py              E-K + require_actor + CONFIRMATION_ACTION_TYPES
store.py              Protocol D-10 + JSONL append-only D-11 + concurrency
binding.py            E-L + ReportReplay (INV-55…INV-57)
commands.py           command shape §10.3/§11.3/§12/§13
service.py            định tuyến cutover + batch + cross-system lookup
resolver.py           thứ tự phân giải + ranking + Pending
drift.py              rà soát drift catalog (chỉ ĐỀ XUẤT, không ghi)
metrics.py            §15
cli.py                bề mặt vận hành Phase 1 (headless, ADR-101)
__init__.py           bề mặt công khai
```

Ba quyết định thiết kế đáng ghi lại vì chúng biến luật thành cấu trúc thay vì
thành quy ước:

1. **`resolve()` là phép ĐỌC THUẦN.** `G24` yêu cầu `current_revision()` không
   đổi sau cả một batch và `G04` yêu cầu 0 lệnh ghi; cộng lại thì
   `CATALOG_EXACT_UNIQUE` auto-resolve **không** persist mapping. Mapping chỉ
   ra đời từ một command. Nhờ đó `INV-70` đúng theo cấu trúc.
2. **Định tuyến cutover là một CỔNG, không phải một `if` bên trong resolver.**
   `resolve_batch()` nhận một *factory*; với batch toàn pre-cutover, factory
   được gọi 0 lần. Một `if` bên trong resolver không thoả `INV-47` vì để vào
   tới nó, resolver đã được dựng và catalog đã được đọc.
3. **`ALIAS_AID_UNIQUE` nằm ở tầng candidate, sau catalog exact.** `aid` là aid
   tìm candidate (`INV-20`) và `OR-02` đã tước quyền auto-resolve của nó
   (`INV-28b`); đặt sau catalog exact giữ cho chiều dương của `G05` không bị
   một alias cũ cướp mất.

## 3. Xử lý re-trigger bắt buộc

### 3.1 `H-05` — `ranking_method_id` OPTIONAL (§6.7) vs hashed vào fingerprint (§7.3)

Re-trigger **CÓ nổ**: phiên này chạm `RejectedCandidate` và candidate ranking.

```text
Trạng thái contract-level : VẪN OPEN
Data contract §6.7        : KHÔNG SỬA — trường vẫn OPTIONAL
```

Đổi `OPTIONAL → REQUIRED` là một thay đổi **data contract**, ngoài thẩm quyền
phiên implementation; brief §24 cấm tường minh "silently đổi OPTIONAL →
REQUIRED". Phiên này không sửa, và không tuyên bố `H-05` đã đóng.

Hai việc **trong** thẩm quyền implementation đã làm, cả hai đều không đụng
contract, để đường lỗi thực tế không còn mở:

```text
(i)  resolver LUÔN gắn RANKING_METHOD_ID cho mọi candidate nó sinh ra
     → trên đường đi thật, trường không bao giờ vắng
(ii) evidence_fingerprint() thay None bằng một sentinel TƯỜNG MINH thay vì
     bỏ trường ra khỏi hash
     → fingerprint vẫn xác định, và "vắng" phân biệt được với "có";
       chiều 'thuật toán xếp hạng đã đổi' của INV-35 không im lặng biến mất
```

Freeze Review #2 còn ghi một quan sát riêng: bốn fixture bắt buộc của
`CHECK-105D-12` **chỉ** diễn tập chiều `pp_version_id`, không fixture nào diễn
tập chiều `ranking_method_id`. Fixture còn thiếu đó đã được bổ sung ở tầng
implementation, **không** sửa gate:
`tests/test_105d_persistence.py::TestG12RejectedCandidateMemory::test_fixture_2b_a_new_ranking_method_brings_the_candidate_back`.

### 3.2 `HB-105D-F2-03` — 13 invariant không có gate assertion riêng

Re-trigger **CÓ nổ**: phiên này chạm đường ghi/correction của
`HistoricalConfirmedRegistry`, migration/rollback, và module metrics.

Phân loại giữ nguyên **HARDENING** — không có invariant nào tạo mâu thuẫn với
frozen gate, nên không có gì để STOP. Xử lý đúng khuôn brief §25: implement
canonical contract + tests, **không** sửa frozen gate.

| Invariant | Xử lý | Test |
|---|---|---|
| `INV-51` | `SourceReportRef` từ chối bằng chứng không mở lại được | `TestRegistryIntegrityHardening::test_inv51_prose_only_confirmation_is_rejected` |
| `INV-52` | khoá tra cứu đủ ba phần | `…::test_inv52_lookup_key_is_order_identity_and_sale_date` |
| `INV-53` | correction = supersede + `reason` REQUIRED | `…::test_inv53_correction_supersedes_and_keeps_the_old_record`, `…::test_inv53_correction_requires_a_reason` |
| `INV-65` | export/import tương đương bit | `TestG09…::test_export_then_import_is_bit_equivalent` |
| `INV-79`…`INV-82` | migration/rollback không phá huỷ | `TestMigrationRollbackHardening` (4 test) |
| `INV-84` | metric mang ba số hiệu version | `TestMetricsHardening::test_inv84_…` |
| `INV-85` | resolver KHÔNG import metrics (assertion import-graph) | `…::test_inv85_the_resolver_never_imports_metrics` |
| `INV-86` | metric không mang dữ liệu khách hàng | `…::test_inv86_metrics_carry_no_customer_data` |
| `INV-26` | chiều dấu tiếng Việt/punctuation của khoá | `TestRawIdentityKey`, `TestNormalizedMatchingAid` |
| `INV-83` | ba tỉ lệ cộng bằng 1 | `…::test_inv83_the_three_rates_sum_to_one` |
| `INV-08` | **cố ý ngoài scope** — `FilePriceProvider` (FROZEN) thi hành | — |

### 3.3 `HB-105D-F2-01` — `ResolutionBinding` "bộ ba" (§3.3 câu 8) vs "CẢ BỐN" (`E-L`/`INV-55`)

Có chạm vùng code (`binding.py`). Ambiguity **KHÔNG** ảnh hưởng deterministic
implementation: `V4.1` §11 (ARTIFACT INTERNAL PRECEDENCE) giải nó một cách cơ
học — trong cùng một artifact, schema thắng văn xuôi giải thích — và
`CHECK-105D-21` Phần C đã assert đúng bốn thành phần. Implementation ghim CẢ
BỐN. Không có gì để STOP.

```text
HB-105D-F2-01 : GIỮ NGUYÊN OPEN. Không sửa documentation.
```

Divergence được **báo cáo** (ghi trong docstring của `binding.py` và ở đây),
không tự dàn xếp — đúng `V4.1` §11.

### 3.4 `HB-105D-F2-02` — §16.1 stale ở hai điểm

Không chạm: phiên này không soạn Scope Lock/Completion Gate cho `TASK-105E`, và
`G28` B3 đã nói rõ đường nạp hợp lệ nên implementation không có chỗ hiểu nhầm.

```text
HB-105D-F2-02 : GIỮ NGUYÊN OPEN. Re-trigger vẫn là phiên soạn TASK-105E.
```

## 4. Rà soát bảo mật và toàn vẹn dữ liệu

| Vùng | Kết quả |
|---|---|
| Xử lý path/input | `log_path`/`index_path` do caller cấp; không có path nào dẫn xuất từ dữ liệu người dùng ⇒ không có bề mặt traversal |
| Catalog/source dị dạng | loader STRICT; 4 lớp lỗi có `reason` máy đọc được |
| Enum/mã không hợp lệ | mọi enum dựng qua constructor, giá trị lạ nổ ngay |
| ID trùng | `INV-04`/`INV-05`/`INV-09` lúc load; `INV-33` theo chuỗi supersede lúc đọc |
| Persistence hỏng | dòng JSON dở ⇒ từ chối nạp, KHÔNG đọc thành state một nửa |
| `expected_version` cũ | `MappingVersionConflict`, 0 ghi, version không tăng |
| Ngày dị dạng | `sale_date` là `date`; entry registry ép `< CUTOVER_DATE`; giá ép `Decimal` (`ADR-103`) |
| Giả định múi giờ | mọi `datetime` là timezone-aware UTC; so sánh cutover ở mức `date` nên không có ranh giới múi giờ |
| Actor rỗng | `require_actor()` là cổng duy nhất; rỗng và chỉ-khoảng-trắng đều bị từ chối |
| Provenance | đủ trường ở mọi biến thể outcome; Pending không mang identity |
| Nguồn đã publish | `publish()` từ chối `version_id` trùng; capture từ chối ghi đè |
| Log bí mật | không secret/credential ở bất kỳ đâu; metrics chỉ mang số đếm + số hiệu version (`INV-86`) |

Ba defect **do chính phiên này tìm ra trong diff của mình và đã sửa trước khi
commit** (không phải finding của review):

```text
1. distinct_identities(): kiểm tra thành viên order_id bằng `in` trên list
   ⇒ O(số order) cho MỖI dòng. Batch quy phạm của G03 là 10.000 dòng.
   Sửa: thêm set song song, giữ list cho thứ tự ổn định (INV-64).
2. _historical_outcome(): `row.sale_date and _midnight(row)` — đọc như một
   phép kiểm null không tồn tại. Sửa: gọi thẳng.
3. PublicPurchaseSourceVersion._aid_index: field không ai dùng. Sửa: xoá.
```

Một defect nữa lộ ra khi test `INV-65` chạy: `to_record()` trả `audit_event_ids`
dưới dạng tuple, nên bản ghi trong bộ nhớ và bản ghi đọc lại từ log không so
được bằng `==`. Đã sửa: ép sang `list` để bản ghi persist là JSON-native.

### Hạn chế đã biết, ghi rõ không giấu

```text
- JSONL + khoá file là concurrency MỘT MÁY (đúng như D-11 đã ghi). Nhiều
  người dùng đồng thời trên nhiều máy là bài toán Phase 2 và cần DB. Contract
  §10.3 được viết để cùng một bộ test chạy đúng trên cả hai cơ chế.
- `rebuild_index()` chạy sau mỗi append ⇒ một lần append là O(số event).
  Chấp nhận được ở Phase 1 (store rỗng lúc khởi đầu, ghi chỉ xảy ra khi có
  quyết định của người), nhưng là điểm cần xem lại khi chuyển DB.
- `active_from`/`active_to` của identity projection được nạp nhưng chưa dùng
  trong phân giải. Không phải lỗ hổng: contract không đặt nghĩa vụ nào lên
  chúng ở TASK-105D, và `INV-08` (khoảng hiệu lực) thuộc FilePriceProvider.
- actor Phase 1 là KHAI BÁO. Cái audit trail chứng minh được là "bản ghi này
  khai actor X", KHÔNG phải "người thao tác thật là X" (§12.1). Đây là
  CAPABILITY BOUNDARY, đã được OR-03 chấp thuận, và không được che.
```

## 5. Findings

```text
BLOCKING     : 0
HARDENING    : 0 mới  (H-05, HB-105D-F2-01, HB-105D-F2-02 kế thừa, vẫn OPEN;
                       HB-105D-F2-03 đã phủ bằng test, phân loại không đổi)
OUT_OF_SCOPE : 0 mới  (O-01/O-02/O-03 kế thừa nguyên trạng)
```

Phiên này **không** tự đánh giá independent review của chính mình.

## 6. Review budget

```text
TASK-105D : 2 allowed / 0 used / 2 remaining     (KHÔNG ĐỔI)
```

Implementation **không** tiêu repair cycle. Không mở Repair Cycle: theo `V4.1`
§3, cycle chỉ mở bởi một BLOCKING finding **sau** independent review — không
phải bởi vòng lặp sửa lỗi trong chính phiên implementation.

## 7. Trạng thái sau phiên

```text
TASK-105D : READY → IMPLEMENTATION CANDIDATE
            (KHÔNG phải IMPLEMENTED-đã-verify, KHÔNG phải DONE)
default   : KHÔNG đổi
merge     : KHÔNG thực hiện
TASK-105E : KHÔNG mở, KHÔNG implement
FilePriceProvider : KHÔNG activate; PendingPriceProvider vẫn là default
Tracking  : KHÔNG chạm, 0 lệnh ghi
production data / mapping thật : KHÔNG tạo
```

## 8. Bàn giao — hành động kế tiếp được phép

```text
1. Independent Review E2 của TASK-105D implementation, do một phiên KHÁC
   thực hiện (V4.1 §12 — reviewer không phải người viết).
2. Owner quyết định về H-05 (data contract §6.7 OPTIONAL → REQUIRED hoặc
   sentinel) — vẫn cần một phiên có thẩm quyền sửa data contract.
3. Chỉ sau (1) PASS: quyết định integration vào default theo V4.1 §8.
```

Không hành động nào ở trên được thực hiện bởi phiên này.
