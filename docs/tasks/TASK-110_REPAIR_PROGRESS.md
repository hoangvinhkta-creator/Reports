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
| R1 | Canonical Object Safety | HIGH | AWAITING_REVIEW | commit R1 duy nhất, parent `0f3a6a4` | — | 39/43 probe BLOCKED, 0 BYPASSED; 3 RESIDUAL + 1 OUT ghi rõ bên dưới |
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

### R2 — MappingStats Single Source of Truth
- Status: BLOCKED BY R1.
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
