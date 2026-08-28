# TASK-105D — BẢN GHI THỰC THI 32 COMPLETION GATE (FROZEN)

## Metadata

Executed By:
Phiên implementation `S040` — `task/task-105d-implementation`

Timestamp:
2026-08-28

Evidence Level:
E2 — validator, Golden và full suite được thực thi thật; output trích nguyên
văn ở §5. Không có mục nào ghi PASS mà không có lệnh chạy tương ứng.

Base SHA:
`222844dfb5cf576238fda4cc913ef2095789b4eb`

GATE_SET_SHA256 (tái lập tại đầu phiên và tái lập lại sau khi sửa xong):
`0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877`

Selected Profile:
PRODUCT

Current Task Mode:
MAJOR

Risk:
Effective Risk `HIGH` — `max(Local Risk 4, Blast Radius 5)`, theo đường lỗi
`sai identity → sai nguồn giá → sai KpiPurchasePrice → sai KPI/lương`.

## 1. Vì sao bản ghi này là một file RIÊNG

Khối gate canonical nằm ở `docs/tasks/TASK-105D-product-identity-resolver.md`,
dòng 631–2359 ("### Gate G01–G08" cho tới ngay trước "### Ma trận overlap có
chủ đích"), 57.614 byte UTF-8, và được ghim bằng

```text
GATE_SET_SHA256 = 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
```

Mỗi khối `#### CHECK-105D-NN` chứa bốn trường `Status:` / `Evidence:` /
`Executed By:` / `Timestamp:`. Ghi kết quả thực thi **vào trong** các trường đó
sẽ đổi từng byte của khối, và do đó đổi `GATE_SET_SHA256` — trong khi chính
artifact freeze nói:

> Thay đổi gate sau thời điểm này — bất kỳ sửa đổi nào làm đổi
> `GATE_SET_SHA256` — cần một `COMPLETION GATE CHANGE PROPOSAL` mới + authority
> theo `governance/core/TASK_COMPLETION_GATE_STANDARD.md`. Không sửa tại chỗ.

Phiên implementation **không** có authority đó, và brief §3 cấm tường minh:
"KHÔNG sửa frozen gate semantics trong implementation session."

Hai yêu cầu này chỉ mâu thuẫn nếu bản ghi kết quả buộc phải nằm trong khối
gate. Nó không buộc: brief §31 yêu cầu "execute/verify ALL 32 frozen checks",
mỗi check có `PASS/FAIL`, evidence, test reference, execution result — nhưng
không quy định nơi ghi. Phiên này vì thế ghi kết quả **ở đây**, giữ khối gate
byte-identical với bản S038 đã freeze, để reviewer độc lập tái lập được
`GATE_SET_SHA256` bằng đúng một lệnh:

```text
$ sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md | sha256sum
0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877  -
```

Hệ quả cần đọc đúng: trong file task, 32 trường `Status:` vẫn là `NOT_TESTED`.
Đó **không** phải tuyên bố "chưa chạy" — nó là hệ quả của việc giữ nguyên
artifact đã freeze. Trạng thái thực thi thật của 32 check là bảng §3 của file
này. Nếu Owner hoặc một phiên có thẩm quyền gate muốn `NOT_TESTED → PASS` ghi
trực tiếp trong khối gate, đó là một `COMPLETION GATE CHANGE PROPOSAL` thuộc
phiên đó, không phải của phiên này.

## 2. Điều phiên này KHÔNG kết luận

```text
32/32 PASS  ≠  TASK-105D DONE.
```

`Tiêu Chí Hoàn Thành` của task còn bốn mục ngoài gate: 0 BLOCKING finding,
Independent Review E2 PASS, toàn bộ `INV-01`…`INV-87` có assertion hoặc lý do
ghi rõ, và progress/roadmap/handoff cập nhật. Phiên này không tự đánh giá
Independent Review của chính mình (brief: "Không independent-review chính
implementation trong cùng session"). Trạng thái sau phiên này là
**implementation candidate**, không phải `DONE`.

## 3. Bảng thực thi — 32/32 REQUIRED

Mỗi dòng: gate, kết quả, Evidence Level bắt buộc theo bản freeze, và test
reference thực thi được. Lệnh tái lập cho một dòng bất kỳ:

```text
$ python3 -m pytest <test reference> -q
```

| CHECK | Status | Evidence Level | Kết quả chạy | Test reference |
|---|---|---|---|---|
| CHECK-105D-01 | PASS | E2 | 7 passed | `tests/test_105d_cutover_registry.py::TestG01PreCutoverBypass` |
| CHECK-105D-02 | PASS | E1 | 5 passed | `tests/test_105d_resolution.py::TestG02ClosedUnion` |
| CHECK-105D-03 | PASS | E1 | 3 passed | `tests/test_105d_resolution.py::TestG03DistinctBeforeMapping` |
| CHECK-105D-04 | PASS | E1 | 1 passed | `tests/test_105d_resolution.py::TestG04AliasExactReadPath` |
| CHECK-105D-05 | PASS | E2 | 3 passed | `tests/test_105d_resolution.py::TestG05CatalogExactUniqueBothDirections` |
| CHECK-105D-06 | PASS | E2 | 5 passed | `tests/test_105d_resolution.py::TestG06AmbiguousNeverAutoResolves` |
| CHECK-105D-07 | PASS | E2 | 3 passed | `tests/test_105d_resolution.py::TestG07FuzzyHasNoProductionAuthority` |
| CHECK-105D-08 | PASS | E1 | 3 passed | `tests/test_105d_resolution.py::TestG08CandidateRankingIsStableAndEvidenced` |
| CHECK-105D-09 | PASS | E1 | 6 passed | `tests/test_105d_persistence.py::TestG09PersistenceAndStoreIntegrity` |
| CHECK-105D-10 | PASS | E2 | 9 passed | `tests/test_105d_persistence.py::TestG10ReuseAndCatalogDrift` |
| CHECK-105D-11 | PASS | E1 | 1 passed | `tests/test_105d_resolution.py::TestG11OneActionResolvesEveryAffectedLine` |
| CHECK-105D-12 | PASS | E1 | 6 passed | `tests/test_105d_persistence.py::TestG12RejectedCandidateMemory` |
| CHECK-105D-13 | PASS | E1 | 4 passed | `tests/test_105d_resolution.py::TestG13PendingIsItsOwnType` |
| CHECK-105D-14 | PASS | E2 | 3 passed | `tests/test_105d_audit_replay.py::TestG14RawNameIsImmutable` |
| CHECK-105D-15 | PASS | E2 | 2 passed | `tests/test_105d_boundaries.py::TestG15MappingSchemaHasNoPrice` |
| CHECK-105D-16 | PASS | E2 | 3 passed | `tests/test_105d_boundaries.py::TestG16PriceProviderBoundary` |
| CHECK-105D-17 | PASS | E2 | 4 passed | `tests/test_105d_boundaries.py::TestG17TrackingIsNeverMutated` |
| CHECK-105D-18 | PASS | E2 | 5 passed | `tests/test_105d_audit_replay.py::TestG18CorrectionAuditKeepsHistory` |
| CHECK-105D-19 | PASS | E2 | 4 passed | `tests/test_105d_persistence.py::TestG19Idempotency` |
| CHECK-105D-20 | PASS | E2 | 7 passed | `tests/test_105d_persistence.py::TestG20ConcurrencyAndActor` |
| CHECK-105D-21 | PASS | E2 | 8 passed | `tests/test_105d_audit_replay.py::TestG21ProvenanceActorAndReplay` |
| CHECK-105D-22 | PASS | E1 | 3 passed | `tests/test_105d_audit_replay.py::TestG22KeyboardFirstOnPhase1Surface` |
| CHECK-105D-23 | PASS | E1 | 4 passed | `tests/test_105d_resolution.py::TestG23AmbiguousCostsExactlyOneAction` |
| CHECK-105D-24 | PASS | E1 | 1 passed | `tests/test_105d_resolution.py::TestG24KnownMappingInBatch` |
| CHECK-105D-25 | PASS | E2 | 3 passed | `tests/test_105d_boundaries.py::TestG25GoldenBaselineUnchanged` |
| CHECK-105D-26 | PASS | E2 | 1 passed | `…::TestG26G27TrackingMissContinuesToPublicPurchase::test_g26_tracking_miss_plus_pp_unique_resolves_public_purchase` |
| CHECK-105D-27 | PASS | E1 | 1 passed | `…::TestG26G27TrackingMissContinuesToPublicPurchase::test_g27_tracking_miss_alone_is_not_enough_for_pending` |
| CHECK-105D-28 | PASS | E2 | 11 passed | `tests/test_105d_boundaries.py::TestG28UnifiedPublicPurchaseSource` |
| CHECK-105D-29 | PASS | E2 | 5 passed | `tests/test_105d_persistence.py::TestG29G30Namespace` |
| CHECK-105D-30 | PASS | E2 | 5 passed | `tests/test_105d_persistence.py::TestG29G30Namespace` |
| CHECK-105D-31 | PASS | E2 | 8 passed | `tests/test_105d_boundaries.py::TestG31G32CrossSystemMapping` |
| CHECK-105D-32 | PASS | E2 | 8 passed | `tests/test_105d_boundaries.py::TestG31G32CrossSystemMapping` |

```text
REQUIRED            : 32 / 32
PASS                : 32
FAIL                : 0
NOT_TESTED          : 0
Evidence Level đạt  : E2 = 19, E1 = 13   (đúng phân bổ của bản freeze)
```

`G29`/`G30` và `G31`/`G32` dùng chung một lớp test vì chúng bảo vệ hai bất
biến khác nhau trên cùng một entity — đúng "Ma trận overlap có chủ đích" của
`DEC-157`. Bên trong lớp, mỗi bất biến có test riêng (`test_g29_*` vs
`test_g30_*`, `test_g31_*` vs `test_g32_*`), nên evidence không bị đếm trùng.

## 4. Ánh xạ 20 case đối kháng bắt buộc (A–T)

| Case | Nội dung | Gate | Test |
|---|---|---|---|
| A | DISTINCT-before-mapping | `G03` | `TestG03DistinctBeforeMapping::test_ten_thousand_rows_fifty_identities` |
| B | Known mapping | `G04`, `G24` | `TestG04AliasExactReadPath`, `TestG24KnownMappingInBatch` |
| C | Catalog exact unique | `G05` | `TestG05…::test_positive_unique_in_tracking` / `…_in_public_purchase` |
| D | Alias aid unique | `G06`, `G23` | `TestG06…::test_d_alias_aid_unique_is_candidate_only`, `TestG23…::test_alias_aid_unique_costs_one_then_zero` |
| E | Fuzzy only | `G06(c)`, `G07` | `TestG06…::test_c_only_similarity`, `TestG07FuzzyHasNoProductionAuthority` |
| F | Ambiguous | `G06` | `TestG06…::test_the_central_case_two_entries_one_token_apart` |
| G | No match | `G13`, `G27` | `TestG13PendingIsItsOwnType`, `TestG26G27…::test_g27_…` |
| H | PP direct product | `G26`, `G28` A | `TestG26G27…::test_g26_…`, `TestG28…::test_fixture_1_…without_tracking` |
| I | Same code, cross namespace | `G30` | `TestG29G30Namespace::test_g30_same_code_different_namespace_do_not_collide` |
| J | Cross-system mapping boundary | `G31` | `TestG31G32CrossSystemMapping::test_g31_fixture_1…4` |
| K | Rejection memory | `G12` | `TestG12RejectedCandidateMemory` (6 test) |
| L | Correction | `G18` | `TestG18CorrectionAuditKeepsHistory` |
| M | Duplicate import | `G19` | `TestG19Idempotency::test_fixture_1_reimporting_the_same_file_changes_nothing` |
| N | Concurrency | `G20` A | `TestG20…::test_part_a_conflicting_confirmations_are_refused_not_merged` |
| O | Tracking rename | `G10` B1 | `TestG10…::test_b1_rename_keeps_the_confirmed_mapping_valid` |
| P | Tracking disappears | `G10` B2/B3 | `TestG10…::test_b2a_…`, `…test_b2b_…`, `…test_b3_…` |
| Q | Pre-cutover | `G01` | `TestG01PreCutoverBypass` (5 fixture bắt buộc) |
| R | Late import | `G01` fixture 3 | `TestG01…::test_fixture_3_late_arrival_uses_sale_date_not_import_date` |
| S | Declared actor | `G20` B, `G21` B | `TestG20…::test_part_b_…`, `TestG21…::test_part_b_no_artifact_calls_the_phase_1_actor_authenticated` |
| T | Unified PP version/binding | `G28` B, `G21` C | `TestG28UnifiedPublicPurchaseSource`, `TestG21…::test_part_c_…` |

```text
A–T : 20 / 20 PASS
```

## 5. Evidence E2 — output nguyên văn

### 5.1 Freeze integrity (đầu phiên và cuối phiên, cùng kết quả)

```text
$ sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md | wc -c
57614
$ sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md | sha256sum
0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877  -
```

Khối gate cũng được so trực tiếp với bản tại SHA freeze `be835b1`:

```text
$ diff <(git show be835b1:docs/tasks/TASK-105D-product-identity-resolver.md | sed -n '567,2295p') \
       <(sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md)
(không có khác biệt)
```

`TASK_FILE_SHA256` và `COMPLETION_GATE_SECTION_SHA256` **khác** giá trị ghi
trong artifact freeze. Đó là đúng và đã lường trước: phiên `S039` (controlled
integration) đã thêm khối bằng chứng freeze vào file task, nằm **ngoài** khối
gate. Ràng buộc quy phạm là `GATE_SET_SHA256`, và nó khớp tuyệt đối.

### 5.2 Golden Business Baseline

```text
$ python3 -m pytest tests/test_golden_baseline.py -q
..........................................................ss             [100%]
58 passed, 2 skipped in 6.46s
```

Đúng baseline đã công bố (`58 passed, 2 skipped`). `git diff` trên Golden
fixture/expected là RỖNG (`CHECK-105D-25`).

### 5.3 Full suite — trước và sau

```text
BASE (222844d, trước implementation):
$ python3 -m pytest -q
756 passed, 11 skipped in 18.01s

SAU implementation:
$ python3 -m pytest -q
930 passed, 11 skipped in 18.01s
```

Delta: `+174 passed`, `+0 skipped`, `0 failed`. 174 là **toàn bộ** test mới của
`TASK-105D` và không có gì khác:

```text
$ python3 -m pytest tests/ -q -k "105d"
174 passed, 767 deselected in 0.83s
```

`767 deselected + 174 selected = 941 = 930 passed + 11 skipped`. Không có test
cũ nào đổi kết quả, không có test cũ nào bị sửa.

### 5.4 Validator governance

```text
$ python3 governance/scripts/governance/validate_structure.py
GOVERNANCE STRUCTURE: PASS
Deployment root: PASS — /home/user/Reports
Checked 21 required paths.

$ python3 governance/scripts/governance/validate_project_state.py
PROJECT STATE: PASS

$ python3 governance/scripts/governance/validate_reference_integrity.py
REFERENCE INTEGRITY: FAIL
Quét 151 file .md (loại trừ 10 file trong governance/reference/history/, docs/audit/).
3 reference không phân giải được:
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md

$ python3 governance/scripts/governance/validate_evidence.py
EVIDENCE VALIDATION: PASS
Checked 88 REQUIRED PASS evidence record(s).

$ python3 governance/scripts/governance/validate_task_completion.py
TASK COMPLETION: PASS
Checked 6 DONE task(s).
```

Đúng baseline tham chiếu đã biết: **chỉ** 3 issue `TASK-REM-T06`, không có
governance regression mới.

### 5.5 File FROZEN / ngoài Scope Lock — diff RỖNG

```text
$ git diff HEAD --stat -- app/modules/pricing/file_price_provider.py \
                          app/pipeline.py \
                          tests/test_golden_baseline.py \
                          tests/fixtures/
(không có output)
```

## 6. Kết luận

```text
32 frozen check đã thực thi   : CÓ
32 frozen check PASS          : CÓ  (32/32, 0 FAIL, 0 NOT_TESTED)
A–T đối kháng                 : 20/20 PASS
Golden                        : 58 passed, 2 skipped — KHÔNG ĐỔI
Full suite                    : 756 → 930 passed, 11 skipped — 0 regression
Validator                     : baseline tham chiếu, 0 regression mới
GATE_SET_SHA256               : tái lập khớp tuyệt đối
Khối gate frozen              : KHÔNG sửa một byte nào
TASK-105D                     : implementation candidate (KHÔNG phải DONE)
```
