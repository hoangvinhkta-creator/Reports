# TASK-110 REPAIR PROGRESS

> File theo dõi riêng cho giai đoạn cô lập repair sau Independent Review #8.
> Không thay thế `PROJECT/PROJECT_PROGRESS.md`. Chỉ dùng để điều phối R1→R8.
> Mỗi unit chỉ được chuyển `FROZEN` sau Independent Review PASS.

## Baseline

| Trường | Giá trị |
|---|---|
| Review source | Independent Review #8 |
| Reviewed SHA | `c8c18229e3ef5a9d600b8d99a1cc21bcbbb2d8dd` |
| TASK-110 | NOT MERGED · NOT DONE |
| CHECK-110-16 | BLOCKED |
| Repair mode | ACTIVE |

## Tiến độ

| Unit | Chủ đề | Severity | Trạng thái | Repair SHA | Review verdict | Ghi chú |
|---|---|---:|---|---|---|---|
| R1 | Canonical Object Safety | HIGH | **NOT FROZEN** — tách sub-unit R1-A→R1-E | — | **Review R1 FAIL** tại `2be5bfe` | Vòng R1 đầu đóng cơ chế seal; Review R1 tìm thêm 5 finding, tách thành R1-A→R1-E |
| R1-A | Canonical Type Coverage | HIGH | **NOT FROZEN** — tách sub-unit R1-A1→R1-A4 | — | **Review R1-A FAIL** tại `dead82e` | Vòng R1-A đóng hợp đồng + registry; Review R1-A tìm thêm 4 finding |
| R1-A1 | Annotation Contract | HIGH | AWAITING_REVIEW | commit R1-A1 duy nhất, parent `dead82e` | — | 51 dạng annotation: 23 ô hỏng → **0**; 10 UNSUPPORTED có tuyên bố |
| R1-A2 | (Finding #2 của Review R1-A) | — | BLOCKED BY R1-A1 | — | — | Không sửa trước R1-A1 PASS |
| R1-A3 | (Finding #3 của Review R1-A) | — | BLOCKED | — | — | — |
| R1-A4 | (Finding #4 của Review R1-A) | — | BLOCKED | — | — | — |
| R1-B | Ambient permit / re-entrant callback | — | BLOCKED BY R1-A | — | — | Không sửa trước R1-A PASS |
| R1-C | `AffectedRow.from_line` duck typing / fabricated provenance | — | BLOCKED | — | — | — |
| R1-D | `FrozenMapping` shallow nested values | — | BLOCKED | — | — | — |
| R1-E | `ReviewItem` discriminator str subclass | — | BLOCKED | — | — | — |
| R2 | MappingStats Single Source of Truth | HIGH | BLOCKED BY R1 | — | — | Không sửa trước R1 PASS |
| R3 | WorkingData Ownership | HIGH | BLOCKED BY R2 | — | — | — |
| R4 | Diagnostics ↔ Provenance | HIGH | BLOCKED BY R3 | — | — | — |
| R5 | ReviewQueue Integrity | HIGH | BLOCKED BY R4 | — | — | — |
| R6 | Master Identity / snapshot_id | MEDIUM | BLOCKED BY R5 | — | — | — |
| R7 | Oracle L2 Coverage | MEDIUM | BLOCKED BY R6 | — | — | — |
| R8 | Governance Canonical State | MEDIUM | BLOCKED BY R7 | — | — | — |
| FINAL | Final Integration Review | — | BLOCKED BY R1–R8 | — | — | Không chạy sớm |

## State machine

`READY → IMPLEMENTING → AWAITING_REVIEW → FROZEN`

Nếu review FAIL:

`AWAITING_REVIEW → REPAIRING → AWAITING_REVIEW`

Không được chuyển sang unit tiếp theo khi unit hiện tại chưa `FROZEN`.

## Nhật ký repair

### R1 — Canonical Object Safety

- Status: **AWAITING_REVIEW**
- Exact starting SHA: `0f3a6a48ca29612b2ea78dca25a4575bf7bee9e2`
  (== `origin/claude/r1-canonical-object-safety-fon9lb` lúc mở phiên;
  worktree sạch, 0 commit behind nhánh mặc định
  `origin/claude/extract-upload-repo-gq2ws4`)
- Repair SHA: commit R1 **duy nhất** trên nhánh này — parent `0f3a6a4`,
  subject `TASK-110 R1 — canonical object safety: seal thành cơ chế, không
  còn là field`. SHA đầy đủ không ghi cứng được vào chính commit chứa nó;
  tra bằng `git rev-parse claude/r1-canonical-object-safety-fon9lb`
  (hoặc `git log --oneline 0f3a6a4..HEAD`, phải ra đúng MỘT commit).
- Independent Review: **CHƯA CHẠY**. R1 **KHÔNG** được đánh dấu FROZEN ở đây.

#### Artefact tham chiếu của Review #8

Repo không lưu Review #8 thành file riêng. Bản ghi mà repo tham chiếu là
`docs/tasks/TASK-110-REPAIR-MODE.md` §3 (8 finding) — đó là handoff dùng cho
phiên này, cùng với `PROJECT/PROJECT_PROGRESS.md` dòng 84–92.

#### Kiểm kê canonical object liên quan

Toàn bộ frozen dataclass trong `app/` và `tools/` đã được liệt kê bằng AST.
Chín kiểu MANG BẤT BIẾN LÚC DỰNG, và đó là phạm vi R1:

| Kiểu | File | Trước R1 | Sau R1 |
|---|---|---|---|
| `EmployeeRecord` | `app/modules/mapping/employee_mapper.py` | field `_seal` | SEALED |
| `EmployeeMaster` | `app/modules/mapping/employee_mapper.py` | field `_seal` | SEALED |
| `AffectedRow` | `app/modules/validation/models.py` | field `_seal` | SEALED |
| `AmbiguousRow` | `app/modules/validation/models.py` | thừa kế `_seal` | SEALED |
| `RowProvenance` | `app/modules/validation/models.py` | field `_seal` | SEALED |
| `MappingStats` | `app/modules/validation/employee_mapping.py` | field `_STATS_SEAL` | SEALED |
| `DateWindow` | `app/modules/mapping/employee_mapper.py` | không kiểm gì | FINAL + tự validate |
| `Diagnostics` | `app/modules/validation/models.py` | `__post_init__` ghi đè được | FINAL |
| `ReviewItem` | `app/modules/validation/models.py` | `__post_init__` ghi đè được | FINAL |

`RecordRef` và `MappingResult` cũng được đánh FINAL, **không đổi ngữ nghĩa**
— chỉ để `isinstance` là bằng chứng. Danh tính `snapshot_id` là **R6**, không
chạm.

Các đường dựng/mutate công khai đã liệt kê: constructor công khai;
`dataclasses.replace()`; kế thừa (câu lệnh `class`, `type()`, metaclass);
đọc lại seal từ instance hoặc từ module; `copy`/`deepcopy`;
`pickle` mọi protocol; `copyreg._reconstructor`; alias container truyền vào
factory; alias container đọc ra từ object; `cls.__new__`; đăng ký factory từ
module khác; object caller giả mạo lợi dụng cửa sổ dựng.

#### ROOT CAUSE

Cơ chế "sealed construction" trước R1 là:

    @dataclass(frozen=True)
    class X:
        ...
        _seal: Any = None
        def __post_init__(self):
            if self._seal is not _SEAL: raise SealedConstruction(...)

Ba tính chất cấu trúc làm nó không đóng được:

1. **Seal là một FIELD**, tức là dữ liệu công khai của object — nên nó đọc lại
   được (`obj._seal`), sao chép được bởi `dataclasses.replace()`, và truyền
   vào được qua `__init__`. Một capability token mà chính object trao lại cho
   mọi caller thì không phải capability token.
2. **`__post_init__` là method thường, ghi đè được.** Một subclass ghi đè nó
   xoá sạch phép validate trong khi `isinstance()` vẫn trả `True`.
3. **Phép kiểm là `_seal is _SEAL`, không phải kiểm lại bất biến.** Phần parse
   thật (`parse_employee_record`, `parse_employee_master_rows`,
   `AffectedRow.from_line`) nằm NGOÀI kiểu, nên vào lại constructor với seal
   hợp lệ + dữ liệu khác cho ra object chưa từng được parse.

Phát biểu gọn nhất:

> **Biên canonical là một token truyền vào constructor công khai, chứ không
> phải chính constructor.** Chừng nào `X(...)` còn là public API mà cổng duy
> nhất là một giá trị nó cũng sẽ trả lại, "giữ được một X" không thể là bằng
> chứng X đã được parse.

#### INVARIANT đã chọn (duy nhất)

> Với mọi canonical type `C`: một object thoả `isinstance(x, C)` chỉ tồn tại
> nếu nó do factory của chính `C` dựng ra VÀ mọi bất biến của `C` đúng tại
> thời điểm dựng; vì `C` bất biến sâu, chúng còn đúng mãi về sau. Không
> public/reasonable API nào — kể cả `C(...)`, `dataclasses.replace`,
> `copy`/`deepcopy`, `pickle`, hay kế thừa — tạo được ngoại lệ.

Bốn lớp đóng (chi tiết trong docstring `app/modules/domain/canonical.py`):

1. **Kiểu tự validate** — mọi bất biến của `C` nằm trong `__post_init__` của
   `C`, container được SAO CHÉP sang dạng bất biến. `replace()` vì thế trở nên
   *vô hại* thay vì bị chặn bằng danh sách.
2. **Construction đóng kín** — permit theo class, ambient, KHÔNG phải field.
   Không còn sentinel nào để đọc, sao chép hay truyền vào.
3. **FINAL** — canonical type từ chối subclass khai báo ngoài module chủ, nên
   `__post_init__` không ghi đè được và `isinstance` lại là bằng chứng.
4. **Mọi đường tái tạo quay về constructor** — `copy`/`deepcopy` trả về chính
   object; sealed type từ chối pickle; `slots=True` khiến cái vỏ mà
   `copyreg._reconstructor` tạo ra không có `__dict__` để nạp trạng thái.

Không thêm seal/sentinel mới: R1 **xoá** cả `_SEAL` lẫn `_STATS_SEAL` và mọi
field `_seal`.

#### FROZEN TOUCH-AREA

    app/modules/domain/canonical.py              (MỚI — cơ chế)
    app/modules/mapping/employee_mapper.py       (áp dụng cơ chế)
    app/modules/validation/models.py             (áp dụng cơ chế)
    app/modules/validation/employee_mapping.py   (CHỈ an toàn dựng của MappingStats)
    tests/test_r1_canonical_object_safety.py     (MỚI — regression)
    tools/analysis/r1_falsification_probes.py    (MỚI — probe chạy được trên mọi SHA)
    docs/tasks/TASK-110_REPAIR_PROGRESS.md       (file này)

Không file nào khác bị sửa.

#### Ranh giới với R2→R8 — tuyên bố tường minh

- **R2 (MappingStats truth model) KHÔNG sửa.** R1 chỉ chạm hai thứ ở
  `MappingStats`: cổng dựng, và việc container phải bất biến. Việc
  `mapped`/`groups`/`ambiguities` là biểu diễn **song song** với row
  collections và phải được DẪN XUẤT từ chúng — mục tiêu R2 — vẫn nguyên vẹn.
  Cấu trúc dữ liệu, cách gom, mọi con số: không đổi (chứng minh: probe
  `CHECK-110-14` byte-identical).
- **R3 (WorkingData ownership)**: `app/pipeline.py` không bị chạm. Probe
  `G12` cho thấy `collect_mapping_stats` vẫn nhận mapper duck-typed — đó là
  R3, ghi nhận chứ không sửa.
- **R4 (Diagnostics/provenance semantics)**: `Diagnostics` và `ReviewItem`
  chỉ được đánh FINAL và ép `str` thuần cho hai field chuỗi tự do còn sót.
  Không trường nào đổi ngữ nghĩa, không quan hệ identity↔provenance nào đổi.
- **R5 (ReviewQueue)**: probe `E3` vẫn BYPASSED có chủ đích và được đóng đinh
  bằng test `test_out_of_scope_review_queue_stays_mutable_for_r5`.
- **R6 (snapshot_id)**: công thức và ngữ nghĩa `RecordRef` không đổi.
- **R7 (oracle L2)**: không mở rộng oracle.
- **R8 (governance)**: chỉ cập nhật file này.
- **TASK-108B / TASK-109**: không chạm.

Không phát sinh boundary conflict: R1 đóng được mà không cần sửa module thuộc
unit khác.

#### BEFORE falsification — tại `0f3a6a4`, TRƯỚC mọi thay đổi

    PYTHONPATH=<repo> python tools/analysis/r1_falsification_probes.py
    TỔNG: 43 probe | BLOCKED=11 | BYPASSED=29 | OUT=1 | RESIDUAL=2

29 đường dựng được canonical object invalid. Nhóm A–F viết TRƯỚC khi sửa, từ
finding của Review #8; nhóm G là wave hai, các đường cùng lớp mà bản sửa
KHÔNG nhắm trực tiếp (yêu cầu Bước 3 của phiên repair).

#### AFTER falsification — cùng bộ probe, cùng file, tại repair SHA

    TỔNG: 43 probe | BLOCKED=39 | BYPASSED=0 | OUT=1 | RESIDUAL=3

| Probe | Đường tấn công | BEFORE `0f3a6a4` | AFTER |
|---|---|---|---|
| `A1` | replace(EmployeeMaster, records=<rác>) | **BYPASSED** | **BLOCKED** |
| `A2` | replace(EmployeeRecord, raw_prefix='') — prefix rỗng khớp mọi chuỗi (HD-110-06) | **BYPASSED** | **BLOCKED** |
| `A3` | replace(EmployeeRecord, group=<group ma>) — HD-110-09 | **BYPASSED** | **BLOCKED** |
| `A4` | replace(EmployeeRecord, window=<start > end>) — cửa sổ bất khả | **BYPASSED** | **BLOCKED** |
| `A5` | replace(AffectedRow, source_file='BIA.xlsx', source_row=99999) — RC-1 | **BYPASSED** | **BLOCKED** |
| `A6` | replace(RowProvenance, batch_scoped=<non-bool truthy>) | **BYPASSED** | **BLOCKED** |
| `A7` | replace(MappingStats, total_rows=-1, mapper=None) | **BYPASSED** | **BLOCKED** |
| `A8` | replace(EmployeeMaster, records=<hai record trùng prefix, cửa sổ chồng>) — HD-110-15 | **BYPASSED** | **BLOCKED** |
| `B1` | subclass EmployeeMaster ghi đè __post_init__ | **BYPASSED** | **BLOCKED** |
| `B2` | subclass EmployeeRecord ghi đè __post_init__ | **BYPASSED** | **BLOCKED** |
| `B3` | subclass AffectedRow ghi đè __post_init__ — provenance bịa | **BYPASSED** | **BLOCKED** |
| `B4` | subclass RowProvenance ghi đè __post_init__ | **BYPASSED** | **BLOCKED** |
| `B5` | subclass ReviewItem ghi đè __post_init__ — item không truy vết được | **BYPASSED** | **BLOCKED** |
| `B6` | subclass Diagnostics ghi đè __post_init__ — str động qua được coercion | **BYPASSED** | **BLOCKED** |
| `B7` | subclass MappingStats ghi đè __post_init__ | **BYPASSED** | **BLOCKED** |
| `C1` | đọc `._seal` từ object hợp lệ rồi dựng object bịa | **BYPASSED** | **BLOCKED** |
| `C2` | đọc `_SEAL` module-level rồi dựng EmployeeMaster rác | **BYPASSED** | **BLOCKED** |
| `C3` | `_seal` còn là field của canonical type không? | **BYPASSED** | **BLOCKED** |
| `D1` | copy.deepcopy tạo bản sao RIÊNG không đi qua constructor? | **BYPASSED** | **BLOCKED** |
| `D2` | pickle round-trip AffectedRow — tái tạo không qua factory | **BYPASSED** | **BLOCKED** |
| `D3` | copy.copy tạo bản sao RIÊNG? | **BYPASSED** | **BLOCKED** |
| `E1` | EmployeeMaster.records / group_codes có bất biến không? | **BLOCKED** | **BLOCKED** |
| `E2` | MappingStats giữ Counter/dict mutable — sửa từ ngoài | **BYPASSED** | **BLOCKED** |
| `E3` | ReviewQueue.items list mutable, add() không kiểm kiểu | **OUT** | **OUT** |
| `E4` | AmbiguousRow.records: truyền list rồi sửa list đó từ ngoài | **BLOCKED** | **BLOCKED** |
| `F1` | EmployeeMapper resolve theo master giả mạo (prefix rỗng khớp mọi chuỗi) | **BYPASSED** | **BLOCKED** |
| `F2` | ReviewItem sở hữu dòng bịa qua provenance giả mạo | **BYPASSED** | **BLOCKED** |
| `G1` | tạo subclass động bằng `type()` thay vì câu lệnh `class` | **BYPASSED** | **BLOCKED** |
| `G2` | metaclass tuỳ biến để né `__init_subclass__` | **BYPASSED** | **BLOCKED** |
| `G3` | đăng ký một factory MỚI cho AffectedRow từ module khác | **BLOCKED** | **BLOCKED** |
| `G4` | gọi thẳng materialiser private của module (`_materialise_affected_row`) | **BLOCKED** | **RESIDUAL** |
| `G5` | `cls.__new__(cls)` rồi để dataclass __init__ chạy | **BLOCKED** | **BLOCKED** |
| `G6` | `line` giả mạo lợi dụng cửa sổ permit của `AffectedRow.from_line` | **BLOCKED** | **BLOCKED** |
| `G7` | `__reduce_ex__(2)` (copyreg) thay vì `__reduce__` | **BYPASSED** | **BLOCKED** |
| `G8` | `copyreg._reconstructor` dựng instance rỗng rồi nạp __dict__ | **BYPASSED** | **BLOCKED** |
| `G9` | replace() trên canonical KHÔNG sealed (Diagnostics) với giá trị rác | **BLOCKED** | **BLOCKED** |
| `G10` | replace() trên ReviewItem với category/severity không tồn tại | **BLOCKED** | **BLOCKED** |
| `G11` | sửa nội dung `FrozenMapping._data` (thò tay vào private) | **BLOCKED** | **BLOCKED** |
| `G12` | MappingStats nhận `mapper` giả mạo (duck-typing) | **RESIDUAL** | **RESIDUAL** |
| `G13` | `object.__setattr__` trên instance frozen hợp lệ | **RESIDUAL** | **RESIDUAL** |
| `G14` | EmployeeMapper nhận master giả mạo không phải EmployeeMaster | **BLOCKED** | **BLOCKED** |
| `G15` | dựng EmployeeMaster hợp lệ rồi replace group_codes bỏ trống | **BYPASSED** | **BLOCKED** |
| `G16` | `_materialise_*` có bị đăng ký nhầm ngoài module chủ không? | **BLOCKED** | **BLOCKED** |

Ba `RESIDUAL` và một `OUT` là **cố ý và có tuyên bố**:

- `G4` gọi thẳng `models._materialise_affected_row` — một tên `_`-private của
  module khác. Không có đường public nào tới nó (`G3`/`G16` chứng minh
  `factory_for` từ chối đăng ký ngoài module chủ).
- `G12` mapper duck-typed → **R3**.
- `G13` `object.__setattr__` xuyên qua `frozen=True` → giới hạn của Python,
  ngoài phạm vi "public/reasonable API" mà invariant phát biểu.
- `E3` `ReviewQueue` → **R5**.

Cả bốn đều có test riêng trong `tests/test_r1_canonical_object_safety.py`, nên
một lần siết chặt hay nới lỏng về sau phải đi qua code review.

Ba đường `BLOCKED` ở BEFORE (`G3`, `G4`, `G16`) là **artefact**: chúng import
`app.modules.domain.canonical`, module chưa tồn tại tại `0f3a6a4`. Đọc chúng
là "không áp dụng", không phải "đã đóng từ trước".

#### Chứng minh construction hợp lệ vẫn chạy

- `test_f_the_valid_paths_all_still_work` — master, mapper, provenance,
  `ReviewItem`, `RowProvenance.batch`, `MappingStats` đều dựng bình thường.
- `test_b_the_in_module_subclass_that_must_keep_working` — `AmbiguousRow`
  (subclass hợp lệ, cùng module) vẫn dựng được.
- 346/346 test nghiệp vụ có sẵn vẫn xanh, không sửa một test nào.

#### Tests / evidence

| Bằng chứng | Lệnh | Kết quả |
|---|---|---|
| Regression toàn bộ | `python -m pytest -q` | **410 passed** (346 cũ + 64 mới, 0 test cũ bị sửa) |
| R1 falsification (pytest) | `python -m pytest tests/test_r1_canonical_object_safety.py -q` | **64 passed** |
| R1 probe BEFORE | probe script tại `0f3a6a4` | 29 BYPASSED |
| R1 probe AFTER | probe script tại repair SHA | **0 BYPASSED** |
| Non-regression nghiệp vụ L1+L2 | so sánh byte JSON `build_l1()`+`build_l2()` giữa hai SHA | `sha256` **giống hệt** (`3d8b2544...5ba9`) |
| CHECK-110-14 | stdout `reconcile_raw()` trên workbook tổng hợp, hai SHA | **0 dòng khác** |
| `validate_structure` | governance validator | **PASS** |
| `validate_project_state` | governance validator | **PASS** |
| `validate_evidence` | governance validator | **PASS** (88 record) |
| `validate_task_completion` | governance validator | **PASS** (6 task DONE) |
| `validate_reference_integrity` | governance validator | **FAIL — CÓ TỪ TRƯỚC**, giống hệt tại `0f3a6a4`: 3 reference hỏng trong `TASK-REM-T06`, ngoài touch-area R1 |
| `git diff --check` | whitespace | **sạch** |

Evidence Level: **E1** (lệnh đã thực thi, output trích ở trên và tái lập được
bằng probe script đã commit).

#### Residual risk

1. Python không có kiểu thật sự đóng: `object.__setattr__`, ghi thẳng vào
   slot, `ctypes`, `gc.get_objects()` vẫn phá được. Invariant phát biểu với
   *public/reasonable API* và điều đó là cố ý.
2. Materialiser `_`-private gọi được bằng tên (`G4`). Đóng hẳn sẽ cần frame
   inspection — một heuristic, đúng loại giải pháp mà repair này tránh.
3. Permit là ambient theo thread. Thân materialiser chỉ có đúng lời gọi
   constructor nên không có code của caller chạy trong cửa sổ đó (`G6` đo
   được), nhưng một materialiser tương lai viết dài ra sẽ mở lại cửa sổ này.
4. `slots=True` khiến `@dataclass` **tạo lại** class, nên `super()` không
   tham số trong method của canonical type sẽ trỏ nhầm. `AmbiguousRow` đã gọi
   tường minh và có comment; một subclass hợp lệ mới trong tương lai phải làm
   như vậy.
5. Ownership thật của `mapper`/`master` (`G12`) và `ReviewQueue` (`E3`) vẫn
   mở — đúng thiết kế, thuộc R3 và R5.

### R1-A — Canonical Type Coverage (sub-repair của R1)

- Status: **NOT FROZEN** — Independent Review R1-A chấm **FAIL** tại
  `dead82e` với 4 finding. Tách tiếp thành R1-A1→R1-A4; xem nhật ký R1-A1 bên
  dưới. Phần ghi chép dưới đây giữ nguyên làm bản ghi của vòng R1-A.
- Status (vòng R1-A, lịch sử): AWAITING_REVIEW
- Exact starting SHA: `2be5bfe982bce9a2e5656eb8444b5302288582bf`
  (== `origin/claude/r1-canonical-object-safety-fon9lb` lúc mở phiên; worktree
  sạch; đúng SHA mà Independent Review R1 đã chấm **FAIL**)
- Repair SHA: commit R1-A **duy nhất** trên nhánh này — parent `2be5bfe`,
  subject `TASK-110 R1-A — canonical type coverage: @canonical thành hợp đồng,
  không còn là nhãn`. Tra bằng `git log --oneline 2be5bfe..HEAD` (phải ra đúng
  MỘT commit).
- Independent Review R1-A: **CHƯA CHẠY**. R1-A **KHÔNG** được đánh dấu FROZEN ở
  đây. R1 tổng vẫn **NOT FROZEN**.

#### Audit trước khi code (đọc code thật tại `2be5bfe`)

| Câu hỏi | Trả lời đo được |
|---|---|
| A. Bao nhiêu type mang `@canonical`? | **11** (quét AST `app/`) |
| B. Type nào thực sự validate? | 9 — có `__post_init__` |
| C. Type nào chỉ được decorate mà không validate? | **2 — `RecordRef`, `MappingResult`** |
| D. `CANONICAL_TYPES` tạo thế nào? | **Thủ công** — tuple viết tay trong `tests/test_r1_canonical_object_safety.py` |
| E. Thêm `@canonical` mới mà quên oracle được không? | **Được, và đã xảy ra** — inventory liệt kê 9/11, bỏ sót đúng hai type ở (C) |

**F. `RecordRef`** — `snapshot_id` sinh từ `sha256(...)[:16]`, ownership do
`EmployeeMaster.record()` kiểm bằng so `snapshot_id`; `index` chỉ sinh từ
`enumerate(self.records)` nên miền hợp lệ là `0 <= index < len(records)`;
`label` CHỈ để render, không bao giờ là khoá tra cứu. Không field nào được kiểm.

**G. `MappingResult`** — `status` phải thuộc `("mapped", "unmapped", "inactive")`
(`app/modules/domain/models.py`) và đi THẲNG vào
`WorkingLine.employee_mapping_status`; `record` phải là `RecordRef`;
`normalized`/`group`/`default_lead_source` là `Optional[str]`, `include_in_kpi`
là `Optional[bool]`. Mọi field là vô hướng nên bất kỳ container mutable nào lọt
vào cũng là alias sống. Không field nào được kiểm.

#### ROOT CAUSE R1-A

> **`@canonical` là một LỜI TUYÊN BỐ, không phải một HỢP ĐỒNG.**

Decorator ép được frozen, final, copy/pickle và cổng dựng sealed — nhưng nó
**không đòi hỏi bằng chứng nào** rằng type được decorate có validate field của
chính nó. Nên hai trạng thái tách rời nhau được:

    "được framework coi là canonical"   vs   "thực sự có validation"

và chúng đã tách rời ngay ở commit đầu tiên dùng framework.

Root cause có **hai nửa**, và chỉ vá một nửa thì lần sau sẽ có type thứ ba:

1. **Không có nghĩa vụ validate.** `@canonical()` nhận một class rỗng hoàn toàn
   mà không kêu một tiếng nào (probe `A7`/`A7b`).
2. **Inventory của oracle viết tay.** `CANONICAL_TYPES` là một tuple phải nhớ
   cập nhật, và nó đã drift: 9 liệt kê / 11 thực tế, bỏ sót đúng hai type không
   validate (probe `A7c`/`A7d`). Nên chính bộ falsification cũng mù.

#### Kiến trúc đã chọn

Không viết thêm `__post_init__` cho hai type rồi coi là xong. Ba thay đổi cấu
trúc, tất cả trong `app/modules/domain/canonical.py`:

**1. Hợp đồng field DẪN XUẤT TỪ ANNOTATION, cài tự động cho MỌI canonical type.**
Annotation vốn đã có, đã được đọc lúc review, và không ai quên viết nó — nên nó
là nguồn đáng tin để sinh phép kiểm:

- `Any` — không kiểm kiểu, nhưng vẫn cấm container mutable;
- `Optional[X]` — `None` hoặc `X`;
- builtin vô hướng — **kiểu chính xác** (`type(v) is X`): một lớp con của `str`
  đổi giá trị giữa hai lần đọc, và `True` qua được mọi phép kiểm `int`;
- class khác — `isinstance` (kế thừa ngoài module chủ đã bị Lớp 3 cấm);
- **mọi field** — không được là `list`/`dict`/`set`/`bytearray`.

Một canonical type MỚI được bảo vệ đầy đủ mà tác giả **không phải nhớ gì**.

**2. Nghĩa vụ khai validator.** `@canonical` **raise lúc import** nếu class không
khai `__post_init__`. "Quên nghĩ về bất biến ngữ nghĩa" nổ ngay khi import, không
nằm im chờ một test ai đó quên viết. Điều này còn *load-bearing*: `@dataclass`
chỉ sinh lời gọi `__post_init__` khi class có nó, nên không có `__post_init__`
thì chính hợp đồng field cũng không chạy.

**3. Registry tự động.** Decorator tự ghi mọi class nó nhận; `canonical_types()`
và `sealed_canonical_types()` trả về registry đó.
`tests/test_r1_canonical_object_safety.py` nay **dẫn xuất** inventory từ registry
thay vì tuple viết tay (9 → 11 type, +4 test tự động), và một test mới so chéo
registry với AST scan `app/` để bắt cả trường hợp "quên import module".

**Ba pha, framework giữ thứ tự.** Bản đầu của lượt này bọc `__init__` nên hợp
đồng chạy SAU `__post_init__`; hệ quả đo được: `RecordRef(sid, "0", "x")` nổ
`TypeError: '<' not supported between instances of 'str' and 'int'` — một lỗi
của trình thông dịch rò ra từ bên trong validator. Nay framework bọc
`__post_init__` và chạy:

1. `__canonical_coerce__` — ép kiểu ở biên (nếu type khai);
2. hợp đồng field — khẳng định kiểu + bất biến của trạng thái SAU khi ép;
3. `__post_init__` — bất biến NGỮ NGHĨA.

Pha 1 tách ra là điều khiến pha 3 **được phép giả định kiểu đã đúng**. Ép chứ
không nổ ở pha 1 giữ nguyên luật đã lập ở R1: dữ liệu một DÒNG GIAO DỊCH méo mó
không được làm gãy cả lượt import (§18 đặc tả).

`field_error=` cho phép type khai lớp ngoại lệ riêng cho vi phạm field. Master
data khai `InvalidEmployeeConfig`: lằn ranh "công cụ hỏng" khác "dữ liệu giao
dịch xấu" (HD-110-09) là quyết định nghiệp vụ, không phải chi tiết cài đặt.

**Bất biến ngữ nghĩa đã thêm cho hai type:**

- `RecordRef` — `index >= 0` (index âm là một vị trí HỢP LỆ với Python, nên nó
  IM LẶNG chọn employee khác, nguy hiểm hơn index ngoài range); `snapshot_id` và
  `label` không rỗng. Định dạng `snapshot_id` **cố ý không kiểm** — đó là R6.
- `EmployeeMaster.record()` / `ref_for_index()` — cận trên của `index` cần biết
  master nên nó thuộc về master; lỗi là `ForeignRecordRef` (domain) thay vì
  `IndexError` thô.
- `MappingResult` — `status` thuộc enum; `record` có mặt kéo theo
  `status != unmapped`; `status == unmapped` tương đương `normalized`/`group`
  đều rỗng.

#### Ràng buộc CỐ Ý KHÔNG thêm — cần Human Decision

Chiều ngược lại, "`record is None` kéo theo `status == unmapped`", **không**
được cài. Hai lý do:

1. Codebase tự khai `record` là bổ sung **chẩn đoán** của Review #5 và "KHÔNG
   ảnh hưởng trường nghiệp vụ nào phía trên" (comment ngay tại field). Ép chiều
   đó là tự đặt hợp đồng chặt hơn thứ codebase tuyên bố.
2. Nó làm vector phá hoại của một mutation oracle đã đóng băng —
   `test_oracle_detects_a_mapping_result_field_mutation` dựng
   `status='mapped', record=None` để chứng minh oracle bắt được thay đổi ở
   trường `record` — **không còn biểu diễn được**. Sửa test đó để làm xanh là
   điều lượt này bị cấm nếu chưa có Human Decision.

Nếu chủ dự án muốn ràng buộc hai chiều: cần đổi vector của mutation test sang
"đổi `record` sang một ref hợp lệ KHÁC" (ý định của test vẫn nguyên vẹn), rồi
mới siết `MappingResult`. Đề xuất, chưa thực hiện.

#### FROZEN TOUCH-AREA

    app/modules/domain/canonical.py              (hợp đồng + registry + 3 pha)
    app/modules/domain/models.py                 (+1 hằng MAPPING_STATUSES)
    app/modules/mapping/employee_mapper.py       (RecordRef, MappingResult, bounds)
    app/modules/validation/models.py             (tách pha ép kiểu, KHÔNG đổi luật)
    app/modules/validation/employee_mapping.py   (tách pha ép kiểu, KHÔNG đổi luật)
    tests/test_r1_canonical_object_safety.py     (inventory dẫn xuất từ registry)
    tests/test_r1a_canonical_type_coverage.py    (MỚI)
    tools/analysis/r1a_falsification_probes.py   (MỚI)
    docs/tasks/TASK-110_REPAIR_PROGRESS.md       (file này)

Việc tách `__canonical_coerce__` chạm vào file của R1-C/R1-D/R1-E nhưng **không
chạm finding nào của chúng**: các câu lệnh ép kiểu được DI CHUYỂN nguyên văn,
không luật nào đổi, không thông báo nào đổi. Đã kiểm chứng bằng L1/L2
byte-identical và toàn bộ test cũ xanh không sửa một dòng.

#### Ranh giới với R1-B→R1-E và R2→R8 — tuyên bố tường minh

- **R1-B (ambient permit / re-entrant callback)** — cơ chế permit không đổi.
- **R1-C (`from_line` duck typing)** — còn mở, đóng đinh bằng test
  `test_out_of_scope_r1c_from_line_still_accepts_a_duck_typed_line` và probe `O1`.
- **R1-D (`FrozenMapping` shallow nested)** — còn mở, đóng đinh bằng test
  `test_out_of_scope_r1d_frozen_mapping_values_stay_shallow` và probe `O2`. Hợp
  đồng field của R1-A **cố tình NÔNG** vì lý do này: nó cấm chính field là
  container mutable, không đi vào bên trong tuple/mapping.
- **R1-E (`ReviewItem` discriminator str subclass)** — không sửa; phép ép
  `as_exact_str` chỉ được di chuyển sang `__canonical_coerce__`, không đổi.
- **R2→R8** — không chạm. `MappingStats` truth model nguyên vẹn; `app/pipeline.py`
  không chạm; công thức `snapshot_id` không đổi (R6); oracle L2 không mở rộng.
- **TASK-108B / TASK-109** — không chạm.

Không phát sinh boundary conflict: R1-A đóng được mà không cần sửa finding của
unit khác.

#### BEFORE falsification — tại `2be5bfe`, TRƯỚC mọi thay đổi

    PYTHONPATH=<repo> python tools/analysis/r1a_falsification_probes.py
    TỔNG: 25 probe | BLOCKED=2 | BYPASSED=21 | OUT=2

#### AFTER falsification — cùng bộ probe, cùng file, tại repair SHA

    TỔNG: 25 probe | BLOCKED=23 | BYPASSED=0 | OUT=2

| Probe | Đường tấn công | BEFORE `2be5bfe` | AFTER |
|---|---|---|---|
| `A1` | RecordRef(index=-1) — Python negative index chọn thầm employee cuối | **BYPASSED** | **BLOCKED** |
| `A2` | RecordRef index vượt range — boundary có chặn không | **BYPASSED** | **BLOCKED** |
| `A3` | replace(valid RecordRef, index=-1) — tái dựng không được validate lại | **BYPASSED** | **BLOCKED** |
| `A3b` | RecordRef field sai kiểu hoàn toàn (snapshot_id=None, index=bool, label=list) | **BYPASSED** | **BLOCKED** |
| `A4` | MappingResult(status='NOT_A_MAPPING_STATUS') | **BYPASSED** | **BLOCKED** |
| `A5` | MappingResult(record='not-a-RecordRef') | **BYPASSED** | **BLOCKED** |
| `A6` | MappingResult mutable alias — normalized=[] rồi sửa list từ ngoài | **BYPASSED** | **BLOCKED** |
| `A6b` | MappingResult mâu thuẫn: status=unmapped nhưng record vẫn có | **BYPASSED** | **BLOCKED** |
| `A6c` | MappingResult(include_in_kpi=<str>) — không phải bool | **BYPASSED** | **BLOCKED** |
| `A7` | khai báo một @canonical type MỚI hoàn toàn rỗng — framework phát hiện? | **BYPASSED** | **BLOCKED** |
| `A7b` | @canonical type mới có bị bắt buộc khai báo validator không? | **BYPASSED** | **BLOCKED** |
| `A7c` | oracle của R1 có phủ MỌI type @canonical không? | **BYPASSED** | **BLOCKED** |
| `A7d` | registry tự động có tồn tại VÀ khớp với AST scan không? | **BYPASSED** | **BLOCKED** |
| `W1` | bool thay int: RecordRef(index=True) rồi dùng làm khoá | **BYPASSED** | **BLOCKED** |
| `W2` | str subclass đổi giá trị giữa hai lần đọc trong RecordRef.snapshot_id | **BYPASSED** | **BLOCKED** |
| `W3` | dict mutable trong MappingResult.group | **BYPASSED** | **BLOCKED** |
| `W4` | replace() nhiều field cùng lúc trên MappingResult | **BYPASSED** | **BLOCKED** |
| `W5` | pickle round-trip RecordRef rác | **BYPASSED** | **BLOCKED** |
| `W6` | deepcopy MappingResult rác | **BYPASSED** | **BLOCKED** |
| `W7` | MappingResult(status=mapped) nhưng normalized=None — mapped mà không có tên | **BYPASSED** | **BLOCKED** |
| `W8` | RecordRef(snapshot_id='') — snapshot rỗng khớp master nào? | **BYPASSED** | **BLOCKED** |
| `W9` | resolve() trên dữ liệu hợp lệ có còn chạy đúng không? (non-regression) | **BLOCKED** | **BLOCKED** |
| `W10` | master.record(ref hợp lệ) vẫn trả đúng employee? (non-regression) | **BLOCKED** | **BLOCKED** |
| `O1` | R1-C — AffectedRow.from_line nhận `line` duck-typed | **OUT** | **OUT** |
| `O2` | R1-D — FrozenMapping giữ value lồng nhau mutable | **OUT** | **OUT** |

`W1`–`W8` là **wave hai**: adversarial, viết để đánh vào những đường mà bản sửa
không nhắm trực tiếp — `bool` thay `int` kèm va chạm hash, `str` subclass đổi
giá trị giữa hai lần đọc, dict mutable, `replace` nhiều field cùng lúc, pickle
mọi protocol, deepcopy, tổ hợp optional mâu thuẫn, `snapshot_id` rỗng. `W9`/`W10`
là non-regression ngược: đường hợp lệ phải vẫn chạy.

Hai `OUT` là **cố ý**: `O1` thuộc R1-C, `O2` thuộc R1-D.

Hai probe `BLOCKED` ở BEFORE (`W9`, `W10`) là non-regression, không phải phòng
thủ — chúng phải BLOCKED ở cả hai phía.

#### Adversarial probes bổ sung trong suite pytest

Ngoài A1–A7, `tests/test_r1a_canonical_type_coverage.py` còn **parametrize trên
registry** — nghĩa là mọi canonical type, kể cả type thêm sau này, tự động bị
kiểm:

- mọi field của mọi type từ chối container mutable;
- mọi field khai `str` từ chối `str` subclass đổi giá trị;
- mọi field khai `int` từ chối `bool`;
- mọi type có hợp đồng phủ ĐÚNG tập field của nó;
- mọi type khai `__post_init__`.

Cộng thêm: annotation không phân giải được bị từ chối lúc decorate (`W12`); `Any`
vẫn cấm mutable (`W11`); hợp đồng chạy SAU pha ép kiểu (`W13`); frozen dataclass
thường KHÔNG bị ảnh hưởng (`W14`); pickle đi qua hợp đồng (`W5`).

#### Tests / evidence

| Bằng chứng | Lệnh | Kết quả |
|---|---|---|
| Regression toàn bộ | `python -m pytest -q` | **497 passed, 9 skipped** (0 test cũ bị sửa, 0 test cũ đỏ) |
| R1-A falsification (pytest) | `pytest tests/test_r1a_canonical_type_coverage.py -q` | passed |
| R1 falsification (vòng trước) | `pytest tests/test_r1_canonical_object_safety.py -q` | passed, inventory 9 → **11** type |
| R1-A probe BEFORE | probe script tại `2be5bfe` | **21 BYPASSED** |
| R1-A probe AFTER | probe script tại repair SHA | **0 BYPASSED** |
| R1 probe (vòng trước, không thoái lui) | `tools/analysis/r1_falsification_probes.py` | 39 BLOCKED / **0 BYPASSED** |
| TASK-108A-1 reconciliation (CHECK-110-14) | stdout `reconcile_raw()`, hai SHA | **0 dòng khác**, EXIT=0 |
| L1+L2 business non-regression | so byte JSON `build_l1()` + `build_l2()` | `sha256` **giống hệt** (`3d8b2544…5ba9`, cùng giá trị như tại `0f3a6a4`) |
| `validate_structure` | governance validator | **PASS** |
| `validate_project_state` | governance validator | **PASS** |
| `validate_evidence` | governance validator | **PASS** |
| `validate_task_completion` | governance validator | **PASS** |
| `validate_reference_integrity` | governance validator | **FAIL — CÓ TỪ TRƯỚC**, giống hệt tại `0f3a6a4` và `2be5bfe`: 3 reference hỏng trong `TASK-REM-T06`, ngoài touch-area |
| `git diff --check` | whitespace | **sạch** |

Evidence Level: **E1**.

#### Residual risk

1. Hợp đồng field **nông** theo thiết kế: nó cấm chính field là container mutable
   nhưng không đi vào bên trong một tuple. Một `tuple` chứa `list` vẫn lọt — đó
   là **R1-D**, cố ý để lại.
2. Framework bảo đảm được **kiểu**, không bảo đảm được **ngữ nghĩa**. Nó ép tác
   giả khai `__post_init__`, nhưng một thân rỗng vẫn hợp lệ. Đó là giới hạn thật:
   không framework nào suy ra được bất biến nghiệp vụ. Điều đã đổi là khoảng lặng
   trở thành một dòng nhìn thấy được trong code review.
3. `typing.get_type_hints` phân giải annotation lúc decorate; một forward
   reference tới type định nghĩa muộn hơn trong cùng module sẽ làm import fail.
   Nổ to và sớm, nhưng là một ràng buộc mới lên thứ tự khai báo.
4. `field_error=` là một tham số tác giả phải nhớ khai. Khai sai chỉ đổi lớp
   ngoại lệ, không mở lỗ hổng — nhưng nó vẫn là một mẩu "phải nhớ".
5. Chi phí runtime: mỗi canonical object chịu thêm 2–12 phép kiểm lúc dựng. Đo
   gián tiếp qua suite (11.7s so với 9.8s trước R1-A) — chấp nhận được ở quy mô
   hiện tại, cần đo lại nếu `AffectedRow` được dựng cho hàng triệu dòng.
6. Ràng buộc `record`/`status` hai chiều chưa cài — xem mục Human Decision ở trên.

### R1-A1 — Annotation Contract (sub-repair của R1-A)

- Status: **AWAITING_REVIEW**
- Exact starting SHA: `dead82e2d9ffa87b9d25483b5c98b8c266bfeb9e`
  (== `origin/claude/r1-canonical-object-safety-fon9lb` lúc mở phiên; worktree
  sạch; đúng SHA mà Independent Review R1-A đã chấm **FAIL** ở Finding #1)
- Repair SHA: commit R1-A1 **duy nhất** trên nhánh này — parent `dead82e`,
  subject `TASK-110 R1-A1 — annotation contract: ngữ pháp đóng, UNKNOWN không
  còn là ANY`. Tra bằng `git log --oneline dead82e..HEAD` (phải ra đúng MỘT
  commit).
- Independent Review R1-A1: **CHƯA CHẠY**. R1-A1 **KHÔNG** được đánh dấu FROZEN
  ở đây. R1-A tổng vẫn **NOT FROZEN**; R1 tổng vẫn **NOT FROZEN**.

#### Finding cần repair

Independent Review R1-A Finding #1: *Compound Union annotations bypass
structural contract.* Năm falsification đã FAIL: `Union[int, str]` nhận `1.5`;
`Optional[Union[int, str]]` nhận `object()`; `str | None` xử lý sai; constrained
`TypeVar` nhận giá trị ngoài ràng buộc; `Literal` nhận giá trị không hợp lệ.

#### Annotation inventory thực tế (đo tại `dead82e`)

11 canonical type / **72 field** / **17 annotation khác nhau**. Nhưng chỉ có
**ba hình thái**:

| Hình thái | Số field | Ví dụ |
|---|---:|---|
| `Optional[<lớp>]` | 34 | `AffectedRow.source_file`, `MappingResult.record` |
| `<lớp>` trần (vô hướng, `tuple`, `frozenset`, canonical class, `FrozenMapping`) | 37 | `AffectedRow.source_row`, `EmployeeRecord.window` |
| `Any` | 1 | `MappingStats.mapper` |

Production **không** dùng `Union` nhiều nhánh, `Literal`, `TypeVar`, PEP 604,
hay generic có tham số. Đây là căn cứ để chọn một ngữ pháp NHỎ và từ chối rõ
phần còn lại, thay vì xây một trình kiểm kiểu thu nhỏ.

Các nhánh xử lý của `_field_checker()` tại `dead82e`, và đường rơi của mỗi
nhánh:

| Nhánh | Xử lý | Đường rơi |
|---|---|---|
| `origin is typing.Union`, đúng 1 nhánh non-None | đặt cờ `optional`, kiểm nhánh còn lại | — |
| `origin is typing.Union`, ≥2 nhánh non-None | **`hint, origin = Any, None`** | mất hoàn toàn phép kiểm |
| PEP 604 (`types.UnionType`) | không nhận ra là union | `isinstance(value, types.UnionType)` → loại MỌI giá trị |
| `Literal`, `TypeVar`, `Final`, special form | `isinstance(target, type)` là False | `checkable=False` → **không kiểm gì** |
| còn lại | `isinstance` / kiểu chính xác | — |

#### BEFORE falsification — 51 dạng annotation tại `dead82e`

    PYTHONPATH=<repo> python tools/analysis/r1a1_annotation_probes.py
    TỔNG: 51 annotation | BYPASSED=10 | REJECTED=4 | SUPPORTED=27
                        | UNDECLARED=9 | UNSUPPORTED=1

**23/51 ô hỏng**, chia ba kiểu hỏng khác nhau:

- `BYPASSED` (10) — nhận cả giá trị KHÔNG hợp lệ;
- `REJECTED` (4) — loại cả giá trị HỢP LỆ (`str | None`, `int | str`,
  `int | str | None`, và annotation `None`);
- `UNDECLARED` (9) — framework KHÔNG mô hình hoá được construct nhưng vẫn
  decorate lọt. Đây chính là *"UNKNOWN âm thầm thành ANY"*, và nó nguy hiểm hơn
  `BYPASSED` vì không có giá trị nào để mà quan sát thấy.

Bốn ô mà reviewer chưa nêu tên cũng hỏng: `Final[int]`, `Union[str, bytes, None]`
(ba nhánh + None), `Union[Marker, int]` (lớp + vô hướng), và annotation `None`.

#### ROOT CAUSE

> **Nhánh cuối cùng của phép phân tích annotation là "bỏ qua", không phải
> "từ chối".**

`_field_checker()` là một chuỗi `if` phẳng trên vài construct `typing`, và
trường hợp mặc định là `checkable=False → không kiểm`. Một trình phân tích mà
mặc định là im lặng thì **mọi annotation nó chưa gặp đều là một lỗ hổng chưa
được phát hiện** — và danh sách construct của `typing` sẽ còn dài ra
(`Self`, `LiteralString`, `TypeVarTuple`… đều mới trong vài bản Python gần đây).

Vì thế thêm năm nhánh `if` cho năm case của Finding #1 sẽ KHÔNG đóng finding:
nó chỉ dời cái mặc định im lặng sang những construct tiếp theo.

#### Supported annotation contract

Ngữ pháp **đóng**, phân tích bằng **đệ quy xuống**, nhánh cuối là `raise`:

    spec    := Any | none | atom | union | literal
    none    := None | NoneType                (chỉ `None` hợp lệ)
    atom    := <lớp cụ thể>                   vô hướng dựng sẵn -> KIỂU CHÍNH XÁC
                                              lớp khác          -> `isinstance`
               <generic có tham số>           kiểm theo `origin`; phần tử KHÔNG
                                              kiểm (đó là R1-D)
    union   := Union[s1..sn] | s1 | .. | sn   khớp ÍT NHẤT MỘT nhánh
    literal := Literal[v1..vn]                bằng VÀ đúng kiểu chính xác

Ngữ nghĩa được giữ ĐỦ, không chỉ ở tầng ngoài:

- `Union` khớp ít nhất một nhánh, mỗi nhánh dùng luật của chính nó — nên
  `Union[int, str]` loại `1.5`, và loại cả `True` (kiểu chính xác của `True` là
  `bool`, không phải `int`).
- `Optional[X]` chính là `Union[X, NoneType]`, không còn là một cờ riêng.
- PEP 604 (`types.UnionType`) đi cùng một đường với `typing.Union`.
- `Literal` so bằng **và** kiểu chính xác — `True == 1` trong Python, nên chỉ
  so bằng thì `Literal[1]` sẽ nhận `True`.
- Nghiêm ngặt của vô hướng SỐNG SÓT xuyên union: `Optional[str]` vẫn loại một
  lớp con của `str`.
- Chính sách container mutable KHÔNG đổi và vẫn chạy SAU phép khớp kiểu.

#### Unsupported annotation policy

Ngoài ngữ pháp → `CanonicalContractViolation` **lúc import**, không phải lúc
chạy, và không bao giờ là im lặng:

| Construct | Vì sao từ chối |
|---|---|
| `TypeVar` (constrained / bound) | canonical dataclass trong dự án này không generic; đỡ cho đúng nghĩa là phải mô hình hoá binding và variance — trình kiểm kiểu thu nhỏ mà production không cần |
| `Final[...]`, `NoReturn`, `Self`, `Optional` chưa subscript | special form chưa được mô hình hoá |
| Giá trị `Literal` ngoài `str`/`int`/`bool`/`bytes`/`None` | không so được kiểu chính xác một cách có nghĩa |
| Forward reference không giải được | đã có từ R1-A |
| Bất kỳ thứ gì khác | nhánh `raise` cuối cùng của `_build_spec()` |

`Any` **chỉ** không bị kiểm kiểu khi tác giả thực sự viết `Any`. Đó là khác
biệt cốt lõi: trước đây `Any` là nơi mọi thứ không hiểu được rơi vào.

#### Files changed

    app/modules/domain/canonical.py              ngữ pháp đóng `_build_spec()` + `_Spec`
    tests/test_r1a1_annotation_contract.py       MỚI — 62 test
    tests/test_r1a_canonical_type_coverage.py    1 assertion: lọc registry theo `app.`
    tools/analysis/r1a1_annotation_probes.py     MỚI — ma trận 51 annotation
    docs/tasks/TASK-110_REPAIR_PROGRESS.md       file này

Sửa duy nhất tại biên trừu tượng của `@canonical` / `_field_checker`. **Không**
production canonical type nào bị sửa để né framework; không business rule nào
đổi; không mapping semantics nào đổi.

**Một assertion cũ được sửa, và không phải để làm PASS.**
`test_r1a_root_cause_the_inventory_is_derived_not_hand_written` so **toàn bộ
registry** với **AST scan chỉ `app/`** — hai tập khác nhau. Nó chỉ đúng một
cách tình cờ vì khi đó chưa file test nào khai canonical type; các test R1-A1
khai type động để dò ngữ pháp nên tập bên trái đầy thêm. Sửa thành lọc registry
theo module `app.` là so ĐÚNG hai tập giống nhau; phép bảo đảm thật — registry
phủ hết mọi `@canonical` trong `app/` — giữ nguyên, và test nay độc lập thứ tự
chạy (đã kiểm cả hai chiều).

#### AFTER falsification — cùng bộ probe, cùng file, tại repair SHA

    TỔNG: 51 annotation | SUPPORTED=41 | UNSUPPORTED=10
                        | BYPASSED=0 | REJECTED=0 | UNDECLARED=0

**Dạng production đang dùng thật**

| Probe | Annotation / đường tấn công | BEFORE `dead82e` | AFTER |
|---|---|---|---|
| `P1` | builtin scalar `int` | **SUPPORTED** | **SUPPORTED** |
| `P2` | builtin scalar `str` | **SUPPORTED** | **SUPPORTED** |
| `P3` | builtin scalar `bool` | **SUPPORTED** | **SUPPORTED** |
| `P4` | `datetime.date` | **SUPPORTED** | **SUPPORTED** |
| `P5` | `Optional[str]` | **SUPPORTED** | **SUPPORTED** |
| `P6` | `Optional[int]` | **SUPPORTED** | **SUPPORTED** |
| `P7` | `Optional[date]` | **SUPPORTED** | **SUPPORTED** |
| `P8` | `tuple` (bare) | **SUPPORTED** | **SUPPORTED** |
| `P9` | `frozenset` | **SUPPORTED** | **SUPPORTED** |
| `P10` | class reference (`FrozenMapping`) | **SUPPORTED** | **SUPPORTED** |
| `P11` | `Any` | **SUPPORTED** | **SUPPORTED** |

**Finding #1 — case Independent Review đã falsify**

| Probe | Annotation / đường tấn công | BEFORE `dead82e` | AFTER |
|---|---|---|---|
| `F1` | `Union[int, str]` | **BYPASSED** | **SUPPORTED** |
| `F2` | `Optional[Union[int, str]]` | **BYPASSED** | **SUPPORTED** |
| `F3` | `str \| None` (PEP 604) | **REJECTED** | **SUPPORTED** |
| `F4` | `int \| str` (PEP 604) | **REJECTED** | **SUPPORTED** |
| `F5` | `Literal['a', 'b']` | **BYPASSED** | **SUPPORTED** |
| `F6` | constrained `TypeVar(int, str)` | **UNDECLARED** | **UNSUPPORTED** |
| `F7` | bound `TypeVar(bound=int)` | **UNDECLARED** | **UNSUPPORTED** |

**Construct khác framework có thể gặp**

| Probe | Annotation / đường tấn công | BEFORE `dead82e` | AFTER |
|---|---|---|---|
| `X1` | `tuple[int, ...]` | **SUPPORTED** | **SUPPORTED** |
| `X2` | `Mapping[str, int]` | **SUPPORTED** | **SUPPORTED** |
| `X3` | `Sequence[int]` | **SUPPORTED** | **SUPPORTED** |
| `X4` | `list[int]` (chính sách bất biến phải loại) | **SUPPORTED** | **SUPPORTED** |
| `X5` | `dict[str, int]` (chính sách bất biến phải loại) | **SUPPORTED** | **SUPPORTED** |
| `X6` | `Final[int]` | **UNDECLARED** | **UNSUPPORTED** |
| `X7` | `Annotated[int, 'meta']` | **SUPPORTED** | **SUPPORTED** |
| `X8` | `Callable[[], None]` | **SUPPORTED** | **SUPPORTED** |
| `X9` | `None` (chỉ None hợp lệ) | **REJECTED** | **SUPPORTED** |
| `X10` | forward reference GIẢI ĐƯỢC (`'Marker'`) | **SUPPORTED** | **SUPPORTED** |
| `X11` | forward reference KHÔNG giải được | **UNSUPPORTED** | **UNSUPPORTED** |
| `X12` | `type` (class object) | **SUPPORTED** | **SUPPORTED** |
| `X13` | `Union[int, None]` (= Optional[int]) | **SUPPORTED** | **SUPPORTED** |
| `X14` | `Union[str, bytes, None]` ba nhánh + None | **BYPASSED** | **SUPPORTED** |
| `X15` | `Union[Marker, int]` class + scalar | **BYPASSED** | **SUPPORTED** |

**Wave 2 — tấn công vào thiết kế**

| Probe | Annotation / đường tấn công | BEFORE `dead82e` | AFTER |
|---|---|---|---|
| `W1` | `Union[int, <TypeVar>]` — không hỗ trợ NẰM TRONG được hỗ trợ | **UNDECLARED** | **UNSUPPORTED** |
| `W2` | `Optional[Literal['a','b']]` | **BYPASSED** | **SUPPORTED** |
| `W3` | `Union[Literal[1], Literal['a']]` | **BYPASSED** | **SUPPORTED** |
| `W4` | `Literal[1]` không được nhận `True` (True == 1) | **BYPASSED** | **SUPPORTED** |
| `W4b` | `Literal[True]` không được nhận `1` | **BYPASSED** | **SUPPORTED** |
| `W5` | `Literal[1.5]` — giá trị literal ngoài kiểu cho phép | **UNDECLARED** | **UNSUPPORTED** |
| `W6` | `int \| str \| None` (PEP 604 ba nhánh) | **REJECTED** | **SUPPORTED** |
| `W7` | `Annotated[Union[int, str], 'meta']` | **BYPASSED** | **SUPPORTED** |
| `W8` | `Annotated[<TypeVar>, 'meta']` — bóc Annotated ra vẫn phải loại | **UNDECLARED** | **UNSUPPORTED** |
| `W9` | `typing.NoReturn` | **UNDECLARED** | **UNSUPPORTED** |
| `W10` | `typing.Optional` (chưa subscript) | **UNDECLARED** | **UNSUPPORTED** |
| `W11` | `typing.Self` | **UNDECLARED** | **UNSUPPORTED** |
| `W12` | `Optional[str]` vẫn loại lớp con của `str` (nghiêm ngặt xuyên union) | **SUPPORTED** | **SUPPORTED** |
| `W13` | `Union[Any, None]` — Any khớp mọi thứ NHƯNG mutable vẫn bị loại | **SUPPORTED** | **SUPPORTED** |
| `W14` | `Union[list, int]` — chính sách bất biến thắng nhánh khớp | **SUPPORTED** | **SUPPORTED** |
| `W15` | replace() trên field union | **SUPPORTED** | **SUPPORTED** |
| `W16` | pickle round-trip field union | **SUPPORTED** | **SUPPORTED** |

**Non-regression production**

| Probe | Annotation / đường tấn công | BEFORE `dead82e` | AFTER |
|---|---|---|---|
| `N1` | production canonical types vẫn decorate được | **SUPPORTED** | **SUPPORTED** |


#### New attack wave — tấn công vào THIẾT KẾ

`W1`–`W16` không nhắm vào năm case của Finding #1 mà hỏi: ngữ pháp đóng có
THỰC SỰ đóng không, hay chỉ đóng ở tầng ngoài cùng?

- **`W1`, `W8` — đệ quy.** Một construct KHÔNG hỗ trợ nằm SÂU bên trong một
  construct ĐƯỢC hỗ trợ (`Union[int, <TypeVar>]`, `Annotated[<TypeVar>]`) vẫn
  phải nổ. Đây là điểm phân biệt "thêm năm nhánh `if`" với "đóng ngữ pháp".
- **`W4`, `W4b` — `True == 1`.** `Literal[1]` không được nhận `True`, và
  `Literal[True]` không được nhận `1`.
- **`W5` — giá trị literal ngoài kiểu cho phép** nổ lúc decorate.
- **`W9`–`W11` — special form mới của Python** (`NoReturn`, `Self`, `Optional`
  chưa subscript) rơi vào nhánh `raise` cuối, không vào im lặng.
- **`W12` — nghiêm ngặt xuyên union**: `Optional[str]` vẫn loại `str` subclass.
- **`W13`, `W14` — giao giữa hai chính sách**: `Any` khớp mọi thứ nhưng chính
  sách bất biến vẫn loại `[]`; `Union[list, int]` có nhánh KHỚP `[]` nhưng
  chính sách bất biến vẫn thắng.
- **`W15`, `W16` — tái dựng**: `replace()` kiểm lại field union; `pickle`
  round-trip đi qua constructor (đo trên `MappingResult` THẬT của production —
  class động của probe không pickle được, đo trên nó sẽ đo nhầm hạn chế của
  chính bộ probe).
- **`N1` — non-regression ngược**: 11 canonical type production vẫn decorate
  bình thường.

Ngoài ra suite pytest kiểm một tính chất mà bảng không diễn đạt được: một
**annotation là object lạ hoàn toàn** (không phải type, không phải special
form) cũng rơi vào nhánh `raise`. Đó là bằng chứng cho "annotation mới thêm sau
này" — bất biến không phụ thuộc vào việc liệt kê đủ construct hôm nay.

#### Tests / evidence

| Bằng chứng | Lệnh | Kết quả |
|---|---|---|
| Regression toàn bộ | `python -m pytest -q` | **559 passed, 9 skipped** (0 test cũ đỏ) |
| R1-A1 focused | `pytest tests/test_r1a1_annotation_contract.py -q` | **62 passed** |
| Độc lập thứ tự chạy | chạy R1-A1 trước/sau R1-A | 145 passed cả hai chiều |
| R1-A1 probe BEFORE | probe script tại `dead82e` | **23/51 ô hỏng** |
| R1-A1 probe AFTER | probe script tại repair SHA | **0/51 ô hỏng** |
| R1 probe (không thoái lui) | `tools/analysis/r1_falsification_probes.py` | 39 BLOCKED / 0 BYPASSED |
| R1-A probe (không thoái lui) | `tools/analysis/r1a_falsification_probes.py` | 23 BLOCKED / 0 BYPASSED |
| TASK-108A-1 reconciliation (CHECK-110-14) | stdout `reconcile_raw()`, hai SHA | **0 dòng khác**, EXIT=0 |
| L1+L2 business non-regression | so byte JSON `build_l1()` + `build_l2()` | `sha256` **giống hệt** (`3d8b2544…5ba9`, cùng giá trị từ `0f3a6a4`) |
| `validate_structure` | governance validator | **PASS** |
| `validate_project_state` | governance validator | **PASS** |
| `validate_evidence` | governance validator | **PASS** |
| `validate_task_completion` | governance validator | **PASS** |
| `validate_reference_integrity` | governance validator | **FAIL — CÓ TỪ TRƯỚC**, y hệt tại `dead82e`: 3 reference hỏng trong `TASK-REM-T06`, ngoài touch-area |
| `git diff --check` | whitespace | **sạch** |

Evidence Level: **E1**.

#### Residual risk

1. Ngữ pháp cố ý **nhỏ**. `TypeVar`, `Final`, `Self`, Enum trong `Literal` đều
   bị từ chối. Nếu production về sau thật sự cần một trong số đó, phải mở rộng
   ngữ pháp — nhưng lúc đó việc mở rộng là một thay đổi CÓ Ý THỨC, không phải
   một lỗ hổng im lặng. Đó chính là điều R1-A1 mua được.
2. Phép kiểm generic vẫn **nông**: `tuple[int, ...]` chỉ kiểm là `tuple`, không
   kiểm phần tử. Đó là **R1-D**, cố ý để lại.
3. `_LITERAL_VALUE_TYPES` không gồm `Enum` dù PEP 586 cho phép. Từ chối lúc
   decorate nên an toàn, nhưng là một khoảng cách so với chuẩn.
4. Union nhiều nhánh làm phép kiểm mỗi field thành một vòng lặp ngắn thay vì
   một phép so. Production chỉ có union hai nhánh nên chi phí không đáng kể
   (suite 12.4s so với 12.0s), cần đo lại nếu sau này có union rộng trong
   đường nóng.
5. `_UnionSpec.label` nối nhãn các nhánh bằng " hoặc ". Với union nhiều nhánh
   thông báo sẽ dài. Không ảnh hưởng đúng/sai.
6. `Annotated[...]` được `typing.get_type_hints()` bóc trước khi framework
   nhìn thấy. Đó là hành vi của thư viện chuẩn, không phải lựa chọn của ngữ
   pháp này — nếu một bản Python tương lai đổi mặc định đó, `Annotated` sẽ rơi
   vào nhánh `raise` chứ không vào im lặng.

### R2 — MappingStats Single Source of Truth
- Status: BLOCKED BY R1 (R1 tổng chưa FROZEN; R1-A→R1-E phải PASS trước).
- Không thực hiện trước khi R1 FROZEN.

### R3 — WorkingData Ownership
- Status: BLOCKED BY R2.

### R4 — Diagnostics ↔ Provenance
- Status: BLOCKED BY R3.

### R5 — ReviewQueue Integrity
- Status: BLOCKED BY R4.

### R6 — Master Identity / snapshot_id
- Status: BLOCKED BY R5.

### R7 — Oracle L2 Coverage
- Status: BLOCKED BY R6.

### R8 — Governance Canonical State
- Status: BLOCKED BY R7.

## Quy tắc cập nhật file này

Mỗi session repair chỉ được cập nhật:
- trạng thái unit hiện tại;
- exact starting SHA;
- falsification evidence;
- touch-area;
- tests/evidence;
- repair SHA;
- verdict review.

Không được đánh dấu unit PASS/FROZEN dựa trên self-review của Claude. `FROZEN` cần Independent Review PASS.
