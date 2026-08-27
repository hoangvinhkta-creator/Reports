# TASK-110 — R1-A1 FINITE CONTRACT (BẢN ĐỀ XUẤT, CHƯA FREEZE)

Status: IMPLEMENTED — chờ Independent Review
Task Mode: MAJOR (sub-unit R1-A1)
Evidence Level: E1 (mọi số liệu trong file này là output lệnh đã thực thi tại exact SHA)
Executed By: Claude Code session `claude/r1-a1-contract-freeze-9lkh3h`
Risk: 4

> **ĐÃ FREEZE VÀ ĐÃ IMPLEMENT.** Owner duyệt HD-A1-01 → HD-A1-18 đúng như đề
> xuất (đặc biệt HD-A1-16: mọi generic có tham số là UNSUPPORTED). Hợp đồng
> §3–§14 dưới đây là bất biến; corpus §12 là ACCEPTANCE CORPUS và không được bổ
> sung trong vòng repair này. Kết quả implementation ở **§21**.
>
> **HD-POST-A1-01 — FROZEN CORPUS = 105 CASE.** Bản plan ghi "95 case" ở phần
> văn xuôi, trong khi chính bảng §12 liệt kê **105 ID**. 95 là số học còn sót
> từ bản nháp (80 case shadow + 15 case tầng decoration) trước khi các nhóm
> K/L/N/O/P/T/X được mở rộng trong bảng. Owner phân loại việc sửa này là
> **DOCUMENTATION COUNT CORRECTION**, KHÔNG phải CONTRACT EXPANSION: không case
> nào được thêm, bớt, renumber, hay đổi expected outcome. Corpus = **105 case**
> (101 case đánh ID + 4 bất biến Z).

---

## 1. Exact SHA / state

| Mục | Giá trị |
|---|---|
| Exact reviewed SHA | `1b0da151c2dae9020c0adcc4118a3e2543cefb77` |
| `git rev-parse HEAD` | `1b0da151c2dae9020c0adcc4118a3e2543cefb77` — **khớp** |
| Nhánh session | `claude/r1-a1-contract-freeze-9lkh3h` |
| Upstream | chưa cấu hình (nhánh cục bộ, chưa push) |
| `git status --short` | rỗng (worktree sạch) |
| Nhánh mặc định origin | `claude/extract-upload-repo-gq2ws4` |
| Quan hệ với nhánh mặc định | behind 0, ahead 18 |
| Baseline test tại SHA này | `702 passed, 9 skipped` (`python3 -m pytest tests/ -q`) |

Trạng thái governance khi mở phiên: R1-A1 **FAIL — NOT FROZEN**; R1-A **NOT
FROZEN**; R1 **NOT FROZEN**; R2→R8 **BLOCKED**; CHECK-110-16 **BLOCKED**;
TASK-110 **NOT DONE / NOT MERGED**.

Không có artifact review nào cho SHA `1b0da151` nằm trong repo — verdict FAIL
đến từ Independent Review bên ngoài, qua chỉ thị của Owner.

### 1.1. Bốn lỗ hổng còn lại, đo được tại SHA này

Không dùng để mở vòng repair theo finding. Ghi lại vì hợp đồng đóng dưới đây
phải đóng chúng **bằng cấu trúc**, và vì chúng là bằng chứng BEFORE của
mutation-by-revert (§15).

| # | Probe | Đo được tại `1b0da151` |
|---|---|---|
| 1 | `get_origin` raise một exception lạ có `__str__` thù địch | **`RuntimeError` THÔ thoát ra** — `_foreign()` gọi `str(exc)[:60]` để dựng thông báo, và chính việc dựng thông báo là đường rò |
| 2 | Giá trị runtime có `__class__` property raise | **`RuntimeError` THÔ thoát ra** — `isinstance(value, target)` tra `value.__class__` |
| 3 | Giá trị runtime có `__class__` property nói dối | **CHẤP NHẬN** — một object không phải `Target` qua được field khai `Target` |
| 4 | Metaclass có `__setattr__` raise giữa chừng decoration | **`RuntimeError` THÔ thoát ra**, class còn lại nửa vời (`__canonical_contract__` đã ghi, `__post_init__` chưa bọc) |

Cả bốn có chung một gốc với các vòng trước: **framework vẫn còn hỏi object lạ**
(qua `isinstance`, qua `repr`/`str`, qua `setattr` trên class lạ) tại những
điểm mà nó chưa chứng minh được là an toàn.

---

## 2. Production annotation inventory

Nguồn: introspection trực tiếp `canonical_types()` tại exact SHA (không phải
danh sách viết tay).

**11 canonical type / 72 field.**

| Type | Module | sealed | fields |
|---|---|---|---|
| `AffectedRow` | `app.modules.validation.models` | ✔ | 4 |
| `AmbiguousRow` | `app.modules.validation.models` | ✔ | 6 |
| `RowProvenance` | `app.modules.validation.models` | ✔ | 2 |
| `Diagnostics` | `app.modules.validation.models` | — | 21 |
| `ReviewItem` | `app.modules.validation.models` | — | 7 |
| `MappingStats` | `app.modules.validation.employee_mapping` | ✔ | 12 |
| `RecordRef` | `app.modules.mapping.employee_mapper` | — | 3 |
| `MappingResult` | `app.modules.mapping.employee_mapper` | — | 6 |
| `DateWindow` | `app.modules.mapping.employee_mapper` | — | 2 |
| `EmployeeRecord` | `app.modules.mapping.employee_mapper` | ✔ | 7 |
| `EmployeeMaster` | `app.modules.mapping.employee_mapper` | ✔ | 2 |

### 2.1. Toàn bộ hình thái annotation production — **17 dạng, không hơn**

| n | Annotation | Hình thái |
|---:|---|---|
| 25 | `Optional[str]` | optional |
| 12 | `str` | class |
| 6 | `tuple` | class (TRẦN, không tham số) |
| 5 | `FrozenMapping` | class |
| 4 | `int` | class |
| 4 | `Optional[date]` | optional |
| 2 | `FrozenCounter` | class |
| 2 | `bool` | class |
| 2 | `date` | class |
| 2 | `Optional[bool]` | optional |
| 2 | `Optional[int]` | optional |
| 1 | `DateWindow` | class (canonical) |
| 1 | `Diagnostics` | class (canonical) |
| 1 | `RowProvenance` | class (canonical) |
| 1 | `frozenset` | class (TRẦN) |
| 1 | `Any` | any |
| 1 | `Optional[RecordRef]` | optional (canonical) |

Tổng: **72**.

**Ba sự thật quyết định toàn bộ hợp đồng dưới đây:**

1. **KHÔNG có một generic có tham số nào trong production.** Không
   `tuple[int, ...]`, không `list[X]`, không `dict[K, V]`. `tuple` và
   `frozenset` xuất hiện ở dạng TRẦN.
2. **KHÔNG có `Literal`, `Union` nhiều nhánh, hay PEP 604 nào trong
   production.** Union duy nhất là `Optional[X]` — đúng hai nhánh, một nhánh
   là `None`.
3. **Toàn bộ 11 type có `type(cls) is type`** — không type nào dùng metaclass
   tuỳ biến.

Toàn bộ 72 field quy về đúng **ba** hình thái: `class` (37), `optional` (34),
`any` (1).

---

## 3. Frozen supported grammar

    spec     := any | none | class | optional

    any      := typing.Any                        [định danh: `hint is typing.Any`]
    none     := None | type(None)                 [định danh]
    class    := <T thuộc FROZEN_CLASS_ALLOWLIST>  [định danh, §6]
    optional := <U> sao cho
                  get_origin(U) is typing.Union HOẶC is types.UnionType,
                  type(get_args(U)) is tuple,
                  len(get_args(U)) == 2,
                  ĐÚNG MỘT phần tử `is type(None)`,
                  phần tử còn lại thuộc FROZEN_CLASS_ALLOWLIST

**Bốn production. Không có production thứ năm.** Nhánh cuối của parser là
`raise`, không phải `return`.

Ngữ nghĩa runtime của từng hình thái:

| Hình thái | Phép kiểm runtime | Ghi chú |
|---|---|---|
| `any` | luôn khớp | vẫn chịu MUTABLE GUARD (C5) |
| `none` | `value is None` | |
| `class` | `type(value) is T` | **ĐỊNH DANH KIỂU CHÍNH XÁC**, không `isinstance` |
| `optional` | `value is None or type(value) is T` | |

Mọi field, mọi hình thái, còn chịu thêm **MUTABLE GUARD** (C5).

Độ sâu tối đa của cây parse: **2**. Số nút tối đa cho một annotation hợp lệ:
**3** (đo được trên cả 72 field production — max = 3).

---

## 4. Frozen unsupported grammar

DEFAULT DENY. Bất kỳ annotation nào không khớp đúng một trong bốn production
ở §3 đều là **UNSUPPORTED**, nổ `CanonicalContractViolation` tại decoration.
Không có ô thứ ba, không `UNKNOWN`, không `AUTO-DETECT`, không
`PROBE-TO-TRUST`, không `BEST-EFFORT`, không `SILENT FALLBACK`.

Liệt kê tường minh những nhóm **hiện đang SUPPORTED** và bị hợp đồng này
chuyển sang UNSUPPORTED (không phải danh sách đóng — danh sách đóng là §3):

| Nhóm | Ví dụ | Lý do |
|---|---|---|
| Generic có tham số | `tuple[int, ...]`, `frozenset[int]`, `tuple[()]`, `Box[int]` | production không dùng; mỗi nhánh generic mang theo `Ellipsis`, `ParamSpec`, `Unpack`, `TypeVarTuple`, và toàn bộ tranh cãi ranh giới R1-A1/R1-D |
| Union tổng quát | `Union[int, str]`, `Union[str, bytes, None]`, `int \| str` | production chỉ dùng `Optional` |
| `Literal[...]` | `Literal['a','b']`, `Literal[1]` | production không dùng; mang theo bẫy `True == 1` và `__eq__` trên giá trị literal |
| Class ngoài allowlist | `re.Pattern`, `type`, `NamedTuple`, class người dùng, `Enum`, `abc.ABC`, `Protocol`, `TypedDict`, `typing.IO` | không gian vô hạn; §9 của chỉ thị |
| Origin mutable | `list`, `dict[str,int]`, `set[int]`, `bytearray` | §8 của chỉ thị: hợp đồng rỗng |
| Special form | `TypeVar`, `Final`, `NoReturn`, `Never`, `Self`, `LiteralString`, `Concatenate`, `TypeAlias` | chưa mô hình hoá |
| `Callable` | trần lẫn có tham số | hình dạng tham số `([A,B], R)` không giống generic nào khác |
| Object bất kỳ làm annotation | module, lambda, `functools.partial`, instance | |

**Không một field production nào nằm trong bảng này** — đo được: 0/72 (§17).

---

## 5. Identity-safe classification primitives

Toàn bộ đường **phân loại** chỉ được dùng đúng những primitive sau.

### 5.1. Được phép (đã có trong chỉ thị §4)

| Primitive | Vì sao không chạy code lạ |
|---|---|
| `type(x)` | đọc thẳng slot `ob_type` trong header object |
| `x is y` | so con trỏ |
| duyệt tuple hằng của framework | `for c in FROZEN_TUPLE` |
| `any(x is c for c in FROZEN_TUPLE)` | chỉ dùng `is` |
| metadata do framework tự parse từ trusted source | registry canonical, bảng tên do chính decorator ghi |

### 5.2. Primitive BỔ SUNG cần Owner duyệt (chỉ thị §4 yêu cầu liệt kê + chứng minh)

**`issubclass(type(value), MUTABLE_TUPLE)`** — dùng DUY NHẤT cho MUTABLE GUARD (C5).

Chứng minh không gọi hook người dùng:

- `issubclass(A, B)` điều phối theo **metaclass của vế PHẢI**. Vế phải ở đây là
  hằng `(list, dict, set, bytearray)`; `type(list) is type`, nên
  `type.__subclasscheck__` chạy.
- `type.__subclasscheck__` với cả hai vế là type thật rơi vào `PyType_IsSubtype`,
  vốn đọc trường C `tp_mro`, **không** đi qua tra thuộc tính.
- Vế trái là `type(value)` — lấy từ header object, không giả mạo được.

Đo được tại exact SHA:

    issubclass(type(Spy()), MUTABLES) = False; user hooks invoked = []
    issubclass(type(hostile __class__), MUTABLES) = False; hooks = []
    isinstance(hostile __class__, MUTABLES) RAISED RuntimeError; hooks = ['__class__']
    list-subclass: type(v) is list -> False | issubclass(type(v), list) -> True

Tức là primitive này **vừa** không chạy hook, **vừa** bắt được lớp con của
`list` mà phép so định danh bỏ sót, **vừa** miễn nhiễm `__class__` thù địch —
trong khi `isinstance` hiện tại thua cả ba.

### 5.3. Cấm tuyệt đối trên đường phân loại

`hash(target)` · `target == other` · `target in set/frozenset/dict` ·
`isinstance(value, target)` · `issubclass(target, ...)` ·
`repr(target)` · `str(target)` · `target.__name__` · `target.__module__` ·
truy cập thuộc tính tuỳ ý.

`isinstance` **bị xoá khỏi toàn bộ đường validate của canonical**, không chỉ
đường phân loại. Bằng chứng đủ điều kiện: xem §9 / HD-A1-09.

---

## 6. Runtime class policy

### 6.1. FROZEN_CLASS_ALLOWLIST — bốn category hữu hạn, so bằng ĐỊNH DANH

| Category | Thành viên | Nguồn |
|---|---|---|
| `FROZEN_SCALARS` | `str`, `int`, `bool`, `date` | hằng của framework |
| `FROZEN_CONTAINERS` | `tuple`, `frozenset` | hằng của framework |
| `FROZEN_FRAMEWORK` | `FrozenMapping`, `FrozenCounter` | hằng của framework |
| `CANONICAL_REGISTRY` | mọi type đã được `@canonical` nhận | metadata do chính decorator ghi (trusted source) |

Phép kiểm thuộc allowlist là `any(target is c for c in <category>)` — thuần
định danh, không `hash`, không `==`, không tra tập hợp.

Class-like target không thuộc bốn category trên: **UNSUPPORTED**. Framework
không đoán "có vẻ runtime-checkable".

Hệ quả: luật metaclass (`type(target) is type`) của bản hiện tại **không còn
cần thiết cho tính an toàn** — với `type(value) is target`, metaclass của
`target` không tham gia phép kiểm. Nó bị thay bằng allowlist, chặt hơn hẳn.

Ràng buộc thứ tự của `CANONICAL_REGISTRY`: một canonical type chỉ tham chiếu
được canonical type đã decorate TRƯỚC nó. Production đã thoả (`RecordRef` trước
`MappingResult`; `DateWindow` trước `EmployeeRecord`; `RowProvenance`/
`Diagnostics` trước `ReviewItem`). Vi phạm → UNSUPPORTED tại decoration, nổ to.

### 6.2. Phép kiểm runtime: `type(value) is target`

Bằng chứng đủ điều kiện — instrument `_ClassSpec.matches` trên **toàn bộ 702
test** tại exact SHA, ghi lại mọi cặp (target, type(value)) đi qua nhánh
`isinstance`:

    TOTAL DIVERGENCES (isinstance True but exact False, or vice versa): 0

Không một giá trị nào trong toàn bộ suite cần dung sai lớp con. Cụ thể:

| Target | Giá trị thật đã thấy | n |
|---|---|---|
| `tuple` | chỉ `tuple` | 2639 |
| `RecordRef` | chỉ `RecordRef` | 1073 |
| `DateWindow` | chỉ `DateWindow` | 868 |
| `FrozenMapping` | chỉ `FrozenMapping` (KHÔNG bao giờ `FrozenCounter`) | 593 |
| `RowProvenance` / `Diagnostics` | chỉ chính nó | 427 mỗi loại |
| `frozenset` | chỉ `frozenset` | 239 |
| `FrozenCounter` | chỉ `FrozenCounter` | 236 |

Điều `isinstance` mua thêm (dung sai lớp con) production **không dùng**; điều
nó bán đi (chạy `__instancecheck__`/`__subclasshook__`, tra `value.__class__`)
là đúng ba lỗ hổng #1–#3 ở §1.1.

Đo được tại exact SHA:

    isinstance(fake, tuple) = True    <-- SPOOFED qua __class__ property
    type(fake) is tuple     = False   <-- miễn nhiễm

### 6.3. MUTABLE GUARD (C5)

Áp cho **mọi** field, mọi hình thái, sau khi spec đã khớp:

    if issubclass(type(value), (list, dict, set, bytearray)): reject

Đây là phòng tuyến duy nhất cho field khai `Any`, và nó bắt cả **lớp con** của
container mutable — điều phép so định danh không làm được.

---

## 7. InitVar / ClassVar policy

Đã được Owner chốt tại §7 của chỉ thị. Hợp đồng ghi lại nguyên văn, implementation
**không đổi** so với `1b0da151` (đã đúng, đã có test canh, đã xanh).

| Hình thái | Chính sách |
|---|---|
| `InitVar[...]` | **UNSUPPORTED** → `CanonicalContractViolation` tại decoration, nêu tên từng field |
| `ClassVar[...]` | **không phải** canonical instance field → không vào runtime field contract, không làm wrapper/construction fail |
| Pseudo-field khác chưa biết | **DEFAULT DENY** |

Nhận diện: `pseudo = set(cls.__dataclass_fields__) − {f.name for f in fields(cls)}`;
`ClassVar` nhận ra bằng `get_origin(resolved) is typing.ClassVar` (biên lạ B2,
§11); mọi thứ còn lại từ chối.

Đo được tại exact SHA: R01 `InitVar` → `CanonicalContractViolation`;
S01 `ClassVar` → ACCEPTED và constructor chạy bình thường.

---

## 8. Mutable-origin policy

R1-A1 **không** sửa chính sách nội dung sâu R1-D. `_MUTABLE_CONTAINERS` giữ
nguyên bộ `(list, dict, set, bytearray)`.

Chính sách annotation: `list`, `dict`, `set`, `bytearray` — cùng mọi generic
origin tương ứng — **UNSUPPORTED trong R1-A1**, vì chúng không nằm trong
`FROZEN_CLASS_ALLOWLIST` (§6.1).

Điều này đóng mâu thuẫn "gọi SUPPORTED rồi reject mọi witness runtime" **bằng
cấu trúc chứ không bằng một phép kiểm thêm**: máy móc `is_inhabited()` của bản
`1b0da151` trở thành **thừa** và được gỡ. Một class chỉ vào được allowlist nếu
framework tự biết ngữ nghĩa của nó, và không class nào trong allowlist có miền
giá trị rỗng — mỗi cái có witness ở §13.

Ranh giới generic lồng nhau: **không còn tồn tại**. Vì mọi generic có tham số
đều UNSUPPORTED, `tuple[list[int], ...]` bị từ chối tại nút NGOÀI CÙNG, parser
không đi xuống. Toàn bộ tranh cãi "parse đủ nhưng không kiểm phần tử" (ranh
giới R1-A1/R1-D) **biến mất khỏi R1-A1**. R1-D vẫn giữ nguyên phạm vi của nó
đối với nội dung phần tử bên trong `tuple` trần.

---

## 9. Parser design

### 9.1. Hình dạng

Không đệ quy. Ngữ pháp sâu tối đa 2 tầng, nên parser là mã thẳng, không cần
work stack:

    parse(hint):
        node_count = 1
        if hint is Any:                    return ANY
        if hint is None or hint is NoneType: return NONE
        if in_allowlist(hint):             return CLASS(hint)         # thuần định danh
        origin = BOUNDARY_B2(get_origin, hint)
        if origin is not typing.Union and origin is not types.UnionType:
            raise CanonicalContractViolation(REASON_NOT_IN_GRAMMAR)
        args = BOUNDARY_B3(get_args, hint)
        if type(args) is not tuple:        raise ...(REASON_ARGS_NOT_TUPLE)
        node_count += len(args)
        if node_count > MAX_ANNOTATION_NODES: raise ...(REASON_NODE_BUDGET)
        if len(args) != 2:                 raise ...(REASON_UNION_ARITY)
        a, b = args
        if a is NoneType and b is not NoneType and in_allowlist(b): return OPTIONAL(b)
        if b is NoneType and a is not NoneType and in_allowlist(a): return OPTIONAL(a)
        raise CanonicalContractViolation(REASON_UNION_SHAPE)

`in_allowlist()` chạy TRƯỚC `get_origin`, nên với mọi annotation hợp lệ,
**không một lời gọi lạ nào** được thực hiện.

`_MAX_ANNOTATION_DEPTH` bị **gỡ**: ngữ pháp tự chặn độ sâu ở 2. Không phụ
thuộc `sys.setrecursionlimit`, không phụ thuộc stack còn lại — cùng một
annotation luôn cho cùng một verdict, ở mọi độ sâu stack.

### 9.2. Commit nguyên tử (C13)

Hai pha, và cổng metaclass đứng trước tất cả:

1. **Cổng** — `type(cls) is type`, câu lệnh ĐẦU TIÊN của `decorate()`. Không
   thoả → `CanonicalContractViolation`, class **chưa bị chạm**.
2. **Tính** — resolve hints, dựng contract, dựng mọi closure. Không ghi gì.
3. **Ghi** — mọi `setattr` lên `cls`, rồi `_REGISTRY.append(cls)` cuối cùng.

Vì cổng đảm bảo `type(cls) is type`, mọi `setattr` đi qua `type.__setattr__`
và không chạy code người dùng — nên pha 3 không thể hỏng giữa chừng.

Đo được tại exact SHA:

    KHÔNG cổng: ***RAW RuntimeError; class half-written = True (__canonical_contract__ đã ghi,
                __post_init__ CHƯA bọc); registry 0 -> 0
    CÓ  cổng:   CanonicalContractViolation; class UNTOUCHED = True; registry 0 -> 0

Cả 11 canonical type production đều qua cổng (`type(cls) is type` = True cho
cả 11).

---

## 10. Node budget

    MAX_ANNOTATION_NODES = 512      (Owner đã freeze tại §10 chỉ thị)
    MAX_ANNOTATION_DEPTH             — GỠ BỎ

Vượt budget → `CanonicalContractViolation`.

**Phát biểu trung thực về tính khả dụng.** Dưới ngữ pháp §3, số nút tối đa của
một annotation HỢP LỆ là **3** (đo được: max 3 trên cả 72 field production).
Trên đường TỪ CHỐI, budget được đếm sau `len(args)` nhưng trước phép kiểm arity,
nên nó bắt được `__args__` khổng lồ (case T01: 100 000 phần tử → UNSUPPORTED).
Ngoài case đó, budget là backstop có tuyên bố, **không** phải hàng rào chịu tải:
hàng rào chịu tải là chính ngữ pháp.

Ranh giới CPython (chỉ thị §10 yêu cầu phân loại rõ): với annotation cực sâu,
`typing` **tự nó** không dựng nổi object trước khi framework nhìn thấy —
đo được `RecursionError` bên trong `typing.__hash__` ở khoảng độ sâu 500 với
`recursionlimit` mặc định. Đó là biên NGOÀI framework: không canonical type nào
được tạo ra, không có trạng thái nửa vời, và corpus ghi nhận nó ở nhóm T.

---

## 11. Error boundaries

### 11.1. Toàn bộ điểm chạm object lạ — ba biên, không hơn

| Biên | Lời gọi | Khi nào chạy | Chính sách |
|---|---|---|---|
| **B1** | `typing.get_type_hints(cls)` | một lần cho mỗi class | `try` HẸP quanh đúng lời gọi này |
| **B2** | `typing.get_origin(hint)` | chỉ khi allowlist trượt | `try` HẸP |
| **B3** | `typing.get_args(hint)` | chỉ khi origin là union | `try` HẸP |

Runtime: **không biên nào.** `type(value) is T` và `issubclass(type(v), MUTABLES)`
đều không chạy code người dùng (§5).

Không `try` nào bọc cả parser. Lỗi lập trình BÊN TRONG framework nổ nguyên
hình — không bị nuốt thành `CanonicalContractViolation`.

### 11.2. Chính sách thông báo (C11)

Thông báo tại decoration chứa **KHÔNG một ký tự nào** do object lạ sinh ra:

- **Được phép**: tên field (từ `dataclasses.fields()`), đường dẫn nút do
  framework tự sinh, hằng lý do (`REASON_NOT_IN_GRAMMAR`,
  `REASON_UNION_ARITY`, `REASON_UNION_SHAPE`, `REASON_ARGS_NOT_TUPLE`,
  `REASON_NODE_BUDGET`, `REASON_B1`, `REASON_B2`, `REASON_B3`).
- **Cấm**: `repr(hint)`, `str(hint)`, `hint.__name__`, `hint.__module__`,
  `str(exc)`, `type(exc).__name__`. Hàm `_safe_name()` bị **xoá** — nó gọi
  `repr()` trên object lạ, tức là vẫn chạy code người khác (đo được: hai lần
  gọi `__repr__` với side effect, tại probe L02).
- Ở ba biên lạ, dùng `raise CanonicalContractViolation(REASON_Bx) from None`.
  `from None` thay vì `from exc`: giữ `exc` trong chain nghĩa là bất kỳ ai in
  traceback về sau đều chạy `__str__` của nó — chính lỗ hổng #1 ở §1.1, chỉ
  bị dời chỗ. Mã lý do đã đủ chỉ ra biên nào hỏng.

### 11.3. Thông báo RUNTIME — safe renderer

Thông báo lỗi field lúc chạy là bằng chứng nghiệp vụ đã trích dẫn (HD-110-09),
nên phải giữ nguyên giọng. Chúng đi qua một renderer an toàn:

| Thành phần | Nguồn |
|---|---|
| nhãn kiểu (`chuỗi thuần`, `` `RecordRef` ``) | bảng hằng của framework + tên hiển thị ghi lúc decoration (trusted source) |
| tên kiểu của giá trị sai | tra ĐỊNH DANH trong bảng tên đóng băng; ngoài bảng → hằng `<kiểu không xác định>` |
| giá trị | `repr(v)` CHỈ khi `type(v)` thuộc `FROZEN_SCALARS`/`FROZEN_CONTAINERS` (khi đó `repr` là hàm C); ngược lại → hằng `<giá trị không hiển thị được>`; cắt ở 200 ký tự |

Ba thông báo production đang bị test ghim, đo được tại exact SHA:

    `snapshot_id` không được là None (khai chuỗi thuần).
    `normalized` phải là chuỗi thuần hoặc `None`, gặp int (1). Kiểm CHÍNH XÁC …
    `record` phải là `RecordRef` hoặc `None`, gặp str ('not-a-RecordRef').

Cả ba chỉ trích dẫn giá trị kiểu `int`/`str` và nhãn do framework sở hữu, nên
renderer an toàn giữ chúng **nguyên văn từng byte**.

---

## 12. Frozen attack corpus

95 case. Mọi case có ID ổn định và ĐÚNG MỘT expected outcome trong ba giá trị:
`SUPPORTED_VALID` · `SUPPORTED_INVALID_REJECT` · `UNSUPPORTED_AT_DECORATION`.

**105 case**: 101 case đánh ID + 4 bất biến Z quét toàn corpus. Định nghĩa
sống trong `tools/analysis/r1a1_annotation_probes.py` (`FROZEN_CORPUS`), và
`tests/test_r1a1_annotation_contract.py` import lại chính nó — một nguồn sự
thật duy nhất, không có bản sao song song để lệch nhau.

Trước khi implement, 80 case tầng annotation đã được chạy thử bằng shadow
classifier tại `1b0da151`: `RAW_ERROR_or_HOOKS_RAN=0`. Kết quả trên
implementation thật ở §21.

Clause ID: **C1** closed-world/default-deny · **C2** grammar · **C3** class
allowlist · **C4** `type(v) is T` · **C5** mutable guard · **C6** optional form ·
**C7** any · **C8** pseudo-field · **C9** decoration gate · **C10** foreign
boundary · **C11** message safety · **C12** node budget · **C13** atomic commit ·
**C14** witness.

| ID | Attack / hình thái | Expected outcome | Clause |
|---|---|---|---|
| A01 | `Union[int, str]` (không phải Optional) | UNSUPPORTED_AT_DECORATION | C2, C6 |
| A02 | `Union[int, str, None]` — 3 nhánh | UNSUPPORTED_AT_DECORATION | C6 |
| A03 | PEP 604 `int \| str` | UNSUPPORTED_AT_DECORATION | C6 |
| A04 | PEP 604 `str \| None` | SUPPORTED_VALID | C6 |
| A05 | `Optional[str]` | SUPPORTED_VALID | C6 |
| A06 | `Union[None, str]` — `None` đứng trước | SUPPORTED_VALID | C6 |
| A07 | `Optional[Optional[str]]` (typing làm phẳng) | SUPPORTED_VALID | C6 |
| A08 | `Union[str]` (typing thu về `str`) | SUPPORTED_VALID | C2 |
| B01 | `Literal['a','b']` | UNSUPPORTED_AT_DECORATION | C2 |
| B02 | `Literal[1]` (bẫy `True == 1`) | UNSUPPORTED_AT_DECORATION | C2 |
| B03 | `Optional[Literal['a','b']]` | UNSUPPORTED_AT_DECORATION | C6 |
| B04 | `Literal[1.5]` | UNSUPPORTED_AT_DECORATION | C2 |
| C01 | `TypeVar` trần | UNSUPPORTED_AT_DECORATION | C2 |
| C02 | `TypeVar` có ràng buộc | UNSUPPORTED_AT_DECORATION | C2 |
| C03 | `Final[int]` | UNSUPPORTED_AT_DECORATION | C2 |
| C04 | `NoReturn` | UNSUPPORTED_AT_DECORATION | C2 |
| C05 | `Never` | UNSUPPORTED_AT_DECORATION | C2 |
| C06 | `Self` | UNSUPPORTED_AT_DECORATION | C2 |
| C07 | `LiteralString` | UNSUPPORTED_AT_DECORATION | C2 |
| D01 | `tuple[<TypeVar>]` — hậu duệ không hỗ trợ | UNSUPPORTED_AT_DECORATION | C2 |
| D02 | `tuple[int, ...]` | UNSUPPORTED_AT_DECORATION | C2 |
| D03 | `tuple[list[int], ...]` | UNSUPPORTED_AT_DECORATION | C2, C3 |
| D04 | `frozenset[int]` | UNSUPPORTED_AT_DECORATION | C2 |
| D05 | `tuple[()]` | UNSUPPORTED_AT_DECORATION | C2 |
| D06 | `Optional[tuple[int, ...]]` | UNSUPPORTED_AT_DECORATION | C6 |
| E01 | `Callable` trần | UNSUPPORTED_AT_DECORATION | C3 |
| E02 | `Callable[[int], str]` | UNSUPPORTED_AT_DECORATION | C2 |
| E03 | `Callable[..., str]` | UNSUPPORTED_AT_DECORATION | C2 |
| F01 | `TypedDict` class | UNSUPPORTED_AT_DECORATION | C3 |
| G01 | `Protocol` `runtime_checkable` | UNSUPPORTED_AT_DECORATION | C3 |
| G02 | `typing.Protocol` | UNSUPPORTED_AT_DECORATION | C3 |
| G03 | `typing.SupportsInt` | UNSUPPORTED_AT_DECORATION | C3 |
| H01 | `typing.IO` | UNSUPPORTED_AT_DECORATION | C3 |
| H02 | `typing.TextIO` | UNSUPPORTED_AT_DECORATION | C3 |
| H03 | `io.TextIOBase` (class thật) | UNSUPPORTED_AT_DECORATION | C3 |
| I01 | metaclass `__instancecheck__` đổi hành vi theo GIÁ TRỊ | UNSUPPORTED_AT_DECORATION | C3, C4 |
| I02 | `Optional[<I01>]` | UNSUPPORTED_AT_DECORATION | C6 |
| J01 | giá trị runtime có `__class__` raise, field `tuple` | SUPPORTED_INVALID_REJECT | C4 |
| J02 | giá trị runtime có `__class__` nói dối là `tuple` | SUPPORTED_INVALID_REJECT | C4 |
| J03 | `__class__` nói dối, field `Optional[RecordRef]` | SUPPORTED_INVALID_REJECT | C4, C6 |
| K01 | metaclass có `__repr__` raise VÀ `__name__` raise | UNSUPPORTED_AT_DECORATION | C3, C11 |
| K02 | metaclass `__repr__` trả chuỗi 100 000 ký tự | UNSUPPORTED_AT_DECORATION | C11 |
| K03 | metaclass `__getattr__` raise trên mọi thuộc tính | UNSUPPORTED_AT_DECORATION | C3, C11 |
| L01 | instance class thường làm annotation, `__repr__` có side effect | UNSUPPORTED_AT_DECORATION | C2, C11 |
| L02 | annotation có `__name__` trả về không phải `str` | UNSUPPORTED_AT_DECORATION | C11 |
| L03 | annotation có `__module__` raise | UNSUPPORTED_AT_DECORATION | C11 |
| M01 | `get_origin` raise exception có `__str__` thù địch | UNSUPPORTED_AT_DECORATION | C10, C11 |
| M02 | `get_args` raise exception có `__str__` thù địch | UNSUPPORTED_AT_DECORATION | C10, C11 |
| N01 | class target không hash được (`__hash__ = None`) | UNSUPPORTED_AT_DECORATION | C3, C5 |
| N02 | `Optional[<N01>]` | UNSUPPORTED_AT_DECORATION | C6 |
| O01 | class target có `__hash__` raise | UNSUPPORTED_AT_DECORATION | C3 |
| O02 | class target có `__hash__` trả giá trị khác nhau mỗi lần | UNSUPPORTED_AT_DECORATION | C3 |
| P01 | class target có `__eq__`/`__hash__` đếm side effect | UNSUPPORTED_AT_DECORATION | C3 |
| P02 | class target có `__eq__` raise | UNSUPPORTED_AT_DECORATION | C3 |
| P03 | class target có `__eq__` luôn trả `True` | UNSUPPORTED_AT_DECORATION | C3 |
| Q01 | `list` trần | UNSUPPORTED_AT_DECORATION | C3 |
| Q02 | `dict[str, int]` | UNSUPPORTED_AT_DECORATION | C2, C3 |
| Q03 | `set[int]` | UNSUPPORTED_AT_DECORATION | C2, C3 |
| Q04 | `bytearray` | UNSUPPORTED_AT_DECORATION | C3 |
| Q05 | `Optional[list[int]]` | UNSUPPORTED_AT_DECORATION | C6 |
| Q06 | `Union[list, dict]` | UNSUPPORTED_AT_DECORATION | C6 |
| Q07 | field `Any` nhận một `list` | SUPPORTED_INVALID_REJECT | C5, C7 |
| Q08 | field `Any` nhận một LỚP CON của `list` | SUPPORTED_INVALID_REJECT | C5 |
| R01 | một `InitVar[int]` | UNSUPPORTED_AT_DECORATION | C8 |
| R02 | nhiều `InitVar`, phải nêu ĐỦ tên | UNSUPPORTED_AT_DECORATION | C8 |
| R03 | dataclass CHỈ có `InitVar` | UNSUPPORTED_AT_DECORATION | C8 |
| R04 | `InitVar` dạng `kw_only` | UNSUPPORTED_AT_DECORATION | C8 |
| S01 | `ClassVar[int]` — phải VẪN hợp lệ | SUPPORTED_VALID | C8 |
| S02 | `ClassVar` cùng field thường — không vào contract | SUPPORTED_VALID | C8 |
| T01 | `__args__` rộng 100 000 phần tử | UNSUPPORTED_AT_DECORATION | C12 |
| T02 | `tuple` lồng 30 tầng | UNSUPPORTED_AT_DECORATION | C2 |
| T03 | annotation sâu tới mức `typing` tự nổ khi DỰNG | ngoài biên framework — không canonical type nào được tạo | C12 |
| U01 | forward ref không phân giải được | UNSUPPORTED_AT_DECORATION | C10 |
| U02 | forward ref trỏ vòng về chính class | UNSUPPORTED_AT_DECORATION | C10 |
| V01 | metaclass có `__setattr__` raise giữa decoration | UNSUPPORTED_AT_DECORATION, class NGUYÊN VẸN, registry KHÔNG ĐỔI | C9, C13 |
| V02 | decoration hỏng ở B1 → registry không đổi | UNSUPPORTED_AT_DECORATION, registry KHÔNG ĐỔI | C13 |
| V03 | decoration hỏng ở field thứ hai → class nguyên vẹn | UNSUPPORTED_AT_DECORATION, class NGUYÊN VẸN | C13 |
| W01 | module object làm annotation | UNSUPPORTED_AT_DECORATION | C2 |
| W02 | lambda làm annotation | UNSUPPORTED_AT_DECORATION | C2 |
| W03 | `Enum` class | UNSUPPORTED_AT_DECORATION | C3 |
| W04 | `abc.ABC` subclass | UNSUPPORTED_AT_DECORATION | C3 |
| W05 | class người dùng thường (metaclass `type`) | UNSUPPORTED_AT_DECORATION | C3 |
| W06 | `re.Pattern` | UNSUPPORTED_AT_DECORATION | C3 |
| W07 | `type` | UNSUPPORTED_AT_DECORATION | C3 |
| X01 | field `str`, witness `"x"`, loại `1` | SUPPORTED_VALID | C4, C14 |
| X02 | field `int`, witness `1`, loại `True` | SUPPORTED_VALID | C4, C14 |
| X03 | field `bool`, witness `True`, loại `1` | SUPPORTED_VALID | C4, C14 |
| X04 | field `date`, witness `date(2026,1,1)` | SUPPORTED_VALID | C4, C14 |
| X05 | field `tuple`, witness `(1,2)`, loại `[1,2]` | SUPPORTED_VALID | C4, C5, C14 |
| X06 | field `frozenset`, witness `frozenset([1])`, loại `{1}` | SUPPORTED_VALID | C4, C14 |
| X07 | field `FrozenMapping`, witness `FrozenMapping({})` | SUPPORTED_VALID | C3, C14 |
| X08 | field `FrozenCounter`, witness `FrozenCounter({})` | SUPPORTED_VALID | C3, C14 |
| X09 | field `Any`, witness một object bất kỳ | SUPPORTED_VALID | C7, C14 |
| X10 | field `NoneType`, witness `None` | SUPPORTED_VALID | C2, C14 |
| X11 | field `DateWindow`, witness từ constructor thật | SUPPORTED_VALID | C3, C14 |
| X12 | field `RecordRef`, witness từ constructor thật | SUPPORTED_VALID | C3, C14 |
| X13 | field `RowProvenance` (SEALED), witness từ factory | SUPPORTED_VALID | C3, C14 |
| Y01 | `Optional[str]` — nhánh `None` | SUPPORTED_VALID | C6 |
| Y02 | `Optional[str]` — nhánh `str`, loại `1.5` | SUPPORTED_VALID | C6 |
| Y03 | `Optional[int]` — loại `True` trong nhánh `int` | SUPPORTED_INVALID_REJECT | C4, C6 |
| Y04 | `Optional[RecordRef]` — loại `"x"` | SUPPORTED_INVALID_REJECT | C4, C6 |
| Z01 | mọi exception thoát ra khỏi decoration ĐÚNG là `CanonicalContractViolation` | bất biến | C10 |
| Z02 | không thông báo lỗi nào chứa ký tự do object lạ sinh ra | bất biến | C11 |
| Z03 | không hook nào của object lạ được gọi trong toàn bộ đường phân loại | bất biến | C1, C4 |
| Z04 | lỗi lập trình BÊN TRONG framework KHÔNG bị nuốt thành `CanonicalContractViolation` | bất biến | C10 |

Z01–Z04 chạy như meta-test quét toàn bộ 91 case còn lại, không phải bốn case rời.

---

## 13. Witness matrix

Theo §6 chỉ thị: đây là ORACLE CONTRACT, không phải định lý về type inhabitation
của Python. Mỗi hình thái SUPPORTED có ít nhất một witness do corpus quy định.

| Hình thái frozen | Witness hợp lệ | Witness KHÔNG hợp lệ | Case |
|---|---|---|---|
| `any` | `object()` | `[1, 2]` (mutable guard) | X09, Q07 |
| `none` | `None` | `1` | X10 |
| `str` | `"x"` | `1` | X01 |
| `int` | `1` | `True` | X02 |
| `bool` | `True` | `1` | X03 |
| `date` | `date(2026,1,1)` | `"2026-01-01"` | X04 |
| `tuple` | `(1, 2)` | `[1, 2]` | X05 |
| `frozenset` | `frozenset([1])` | `{1}` | X06 |
| `FrozenMapping` | `FrozenMapping({})` | `{}` | X07 |
| `FrozenCounter` | `FrozenCounter({})` | `{}` | X08 |
| canonical không sealed | `DateWindow(...)`, `RecordRef(...)` | `"x"` | X11, X12 |
| canonical sealed | `RowProvenance` dựng qua factory | `"x"` | X13 |
| `optional` | `None` VÀ witness của nhánh class | witness của kiểu khác | Y01–Y04 |

Bảng này là **đóng**: mỗi thành viên của `FROZEN_CLASS_ALLOWLIST` có đúng một
dòng, và một meta-test khẳng định `set(bảng) == set(allowlist) ∪ {any, none, optional}`.
Thêm một thành viên vào allowlist mà quên witness ⇒ meta-test FAIL.

---

## 14. Review verdict protocol

Từ sau khi Owner freeze, mọi review finding phải thuộc **đúng một**:

**BLOCKING** — chỉ khi reviewer chỉ ra ĐƯỢC một trong bốn điều:
1. clause nào của Frozen Contract (C1–C14) bị vi phạm; HOẶC
2. case nào của Frozen Attack Corpus (95 case) fail; HOẶC
3. một annotation production nằm NGOÀI frozen grammar; HOẶC
4. business non-regression bị phá.

**HARDENING** — attack mới nằm ngoài frozen contract/corpus.
→ ghi backlog. **KHÔNG** làm R1-A1 FAIL.

**OUT_OF_SCOPE** — thuộc R1-A2/A3/A4, R1-B→E, R2→R8.
→ **KHÔNG** làm R1-A1 FAIL.

Luật "reviewer nghĩ ra attack mới ⇒ FAIL" **không còn hiệu lực**.

Corpus blocking không được bổ sung trong cùng vòng repair sau khi freeze.
Ngoại lệ DUY NHẤT: phát hiện Frozen Contract tự mâu thuẫn, hoặc production
behavior không thể implement theo contract → **STOP → HUMAN DECISION**, không
âm thầm đổi corpus.

---

## 15. Mutation-by-revert plan

Sau implementation, với từng nhóm enforcement: tạm revert / inject mutation
tương đương, chạy toàn bộ frozen corpus, ghi ma trận. **Không commit mutation.**

Yêu cầu: FIX ON → 95/95 PASS. FIX REMOVED → ít nhất các blocking case liệt kê
dưới đây FAIL.

| # | Mutation | Case BẮT BUỘC fail |
|---|---|---|
| M-1 | `type(v) is T` → `isinstance(v, T)` | J01, J02, J03 |
| M-2 | allowlist → "mọi class có metaclass `type`" | W05, W06, W07, F01 |
| M-3 | re-admit generic có tham số | D01–D06, Q02, Q03, Q05 |
| M-4 | re-admit union tổng quát (n nhánh) | A01, A02, A03, Q06 |
| M-5 | re-admit `Literal[...]` | B01–B04 |
| M-6 | khôi phục `_safe_name()` / `str(exc)` trong thông báo | K01–K03, L01–L03, M01, M02, Z02, Z03 |
| M-7 | gỡ cổng metaclass ở `decorate()` | V01, Z01 |
| M-8 | mutable guard `issubclass(type(v),…)` → `isinstance(v,…)` | Q07, Q08, J01 |
| M-9 | gỡ luật từ chối pseudo-field | R01–R04 |
| M-10 | gỡ node budget | T01 |
| M-11 | `from None` → `from exc` ở ba biên lạ | Z02 (chain render chạy `__str__` lạ) |

Ma trận kết quả ghi vào `docs/tasks/TASK-110_REPAIR_PROGRESS.md`.

---

## 16. Allowed touch-area

**Được sửa:**

| Đường dẫn | Phạm vi |
|---|---|
| `app/modules/domain/canonical.py` | CHỈ vùng annotation contract: `_build_spec*`, `_Spec` và lớp con, `_classify_class_target`, `_field_checker`, `_build_field_contract`, `_foreign`, `_safe_name`, `_Budget`, các hằng ngữ pháp, và cổng metaclass ở đầu `decorate()` |
| `tests/test_r1a1_annotation_contract.py` | thay bằng suite dẫn từ frozen corpus |
| `tools/analysis/r1a1_annotation_probes.py` | thay ma trận 128 ô bằng 95 case frozen |
| `docs/tasks/TASK-110-R1-A1-FROZEN-CONTRACT.md` | file này |
| `docs/tasks/TASK-110_REPAIR_PROGRESS.md` | nhật ký + ma trận mutation |
| `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/PROJECT_DECISIONS.md` | trạng thái + DEC |

**KHÔNG được sửa:** mọi module khác dưới `app/modules/**`; mọi logic
business/policy của A3/D; `_MUTABLE_CONTAINERS`; Lớp 2 (permit/factory),
Lớp 3 (final), Lớp 4 (copy/pickle) của R1; `FrozenMapping`/`FrozenCounter`
semantics; `as_exact_str`/`as_exact_date`.

Nếu cần sửa logic A3/D: **STOP**.

---

## 17. Allowed migration exceptions

Đo được tại exact SHA, bằng shadow classifier chạy trên chính inventory
production:

    fields checked : 72
    OUTSIDE grammar: 0
    max nodes visited for any production field: 3
    form histogram: {'optional': 34, 'class': 37, 'any': 1}

→ **KHÔNG có annotation production nào cần migrate.** Không một dòng
`app/modules/**` nào ngoài `canonical.py` bị chạm.

Quét toàn bộ `tests/` tìm annotation sẽ chuyển SUPPORTED → UNSUPPORTED, loại
trừ chính file R1-A1: **0 kết quả**. Không file test A3/D nào bị ảnh hưởng.

Toàn bộ migration nằm gọn trong hai artifact oracle của chính R1-A1:

| File | Hình thái mất SUPPORTED |
|---|---|
| `tests/test_r1a1_annotation_contract.py` | generic có tham số (`tuple[int,...]`, `tuple[()]`, `frozenset[int]`, `tuple[list[int],...]`, `Box[int]`, `typing.Tuple[int,...]`, tuple lồng sâu); union tổng quát (`Union[int,str]`, `Union[int,str,None]`, `Union[str,bytes,None]`, `Union[Marker,int]`, `int\|str`, `int\|str\|None`); `Literal` (5 dạng) + `Optional[Literal[...]]`; class ngoài allowlist (`re.Pattern`, `type`, `NTuple`, `Box`, `Marker`, `bytes`, `float`) |
| `tools/analysis/r1a1_annotation_probes.py` | cùng tập trên, trong ma trận 128 ô |

Mỗi migration chỉ đổi annotation/fixture/expected outcome — **không** đổi
business/policy logic — và phải được liệt kê từng dòng trong báo cáo repair.

---

## 18. Hardening backlog rule

Attack mới phát hiện SAU freeze:

- **Vi phạm clause C1–C14 hiện hữu** → BLOCKING theo contract, được sửa trong
  vòng này.
- **Ngoài frozen contract** → ghi `HARDENING BACKLOG` trong
  `TASK-110_REPAIR_PROGRESS.md`. KHÔNG mở scope. KHÔNG đổi corpus. KHÔNG làm
  R1-A1 FAIL.
- **Làm contract hiện tại bất khả thi / tự mâu thuẫn** → **STOP + HUMAN
  DECISION**.

Claude không tự quyết ba nhánh này.

---

## 19. Human Decisions Required

**Không được implement khi còn bất kỳ dòng nào chưa chốt.**

| ID | Quyết định | Đề xuất | Hệ quả nếu chọn khác |
|---|---|---|---|
| HD-A1-01 | Ngữ pháp đóng = đúng 4 production `any \| none \| class \| optional` (§3) | **DUYỆT** | mỗi production thêm vào là một bề mặt tấn công vĩnh viễn |
| HD-A1-02 | `FROZEN_SCALARS = (str, int, bool, date)` | **DUYỆT** (đúng nhu cầu production) | phương án rộng hơn `(str,int,bool,float,bytes,complex,date)` = `_EXACT_TYPES` hiện tại; không thêm rủi ro (so định danh), nhưng trái luật "production không cần ⇒ UNSUPPORTED" ở §5 chỉ thị. Đổi 2 dòng corpus |
| HD-A1-03 | `FROZEN_CONTAINERS = (tuple, frozenset)` | **DUYỆT** | production dùng cả hai; bỏ bớt sẽ phá 7 field |
| HD-A1-04 | `FROZEN_FRAMEWORK = (FrozenMapping, FrozenCounter)` | **DUYỆT** | production dùng 7 field |
| HD-A1-05 | `CANONICAL_REGISTRY` là một category, so bằng định danh; canonical type chỉ tham chiếu được type đã decorate TRƯỚC | **DUYỆT** | không có nó, 4 field production (`DateWindow`, `Diagnostics`, `RowProvenance`, `Optional[RecordRef]`) mất SUPPORTED |
| HD-A1-06 | Chấp nhận PEP 604 `X \| None` như một cách viết của `optional` | **DUYỆT** | từ chối thì `str \| None` nổ lúc import dù tương đương `Optional[str]` — bẫy khó hiểu cho người viết sau; chấp nhận không thêm bề mặt (so định danh với `types.UnionType`) |
| HD-A1-07 | Chấp nhận `None` ở CẢ HAI vị trí của union 2 nhánh | **DUYỆT** | `Union[None, str]` cho `args = (NoneType, str)` — đo được; chỉ nhận vị trí thứ hai là một bẫy im lặng |
| HD-A1-08 | `Any` GIỮ SUPPORTED (1 field production) + luôn chịu mutable guard | **DUYỆT** | bỏ `Any` ⇒ `MappingStats.mapper` phải đổi kiểu ⇒ chạm logic A3, vi phạm §16 |
| HD-A1-09 | Phép kiểm class runtime = `type(v) is T`, **xoá `isinstance` khỏi toàn bộ đường validate canonical** | **DUYỆT** | bằng chứng: 0 divergence trên 702 test; giữ `isinstance` là giữ nguyên lỗ #2 và #3 ở §1.1 |
| HD-A1-10 | Primitive BỔ SUNG `issubclass(type(v), MUTABLE_TUPLE)` cho mutable guard | **DUYỆT** | chứng minh ở §5.2; không có nó, field `Any` không chặn được lớp con của `list` |
| HD-A1-11 | `MAX_ANNOTATION_NODES = 512`; **GỠ** `MAX_ANNOTATION_DEPTH` | **DUYỆT** | ngữ pháp tự chặn ở độ sâu 2; giữ depth limit là giữ một hằng số không còn ý nghĩa |
| HD-A1-12 | InitVar UNSUPPORTED / ClassVar không phải field / pseudo-field lạ DEFAULT DENY | **DUYỆT** (Owner đã chốt §7) | implementation không đổi |
| HD-A1-13 | Cổng `type(cls) is type` là câu lệnh ĐẦU TIÊN của `decorate()` | **DUYỆT** | không có nó, nhóm V để lọt exception thô và class nửa vời (đo được) |
| HD-A1-14 | Chính sách thông báo: 0 ký tự từ object lạ tại decoration; safe renderer tại runtime; `from None` ở ba biên | **DUYỆT** | ba thông báo production bị ghim giữ nguyên từng byte (đã kiểm) |
| HD-A1-15 | `list`/`dict`/`set`/`bytearray` UNSUPPORTED do vắng mặt trong allowlist; **gỡ** máy móc `is_inhabited()` | **DUYỆT** | giữ `is_inhabited()` là giữ một phép kiểm không còn đường nào chạm tới |
| HD-A1-16 | MỌI generic có tham số UNSUPPORTED; ranh giới R1-A1/R1-D biến mất khỏi R1-A1 | **DUYỆT** | đây là quyết định có ảnh hưởng lớn nhất tới corpus (nhóm D, Q) — cần Owner chốt rõ |
| HD-A1-17 | Migrate 2 artifact oracle R1-A1 (§17); 0 file production, 0 file A3/D | **DUYỆT** | |
| HD-A1-18 | Cắt `repr` giá trị ở 200 ký tự trong thông báo runtime | **DUYỆT** | quyết định nhỏ; ảnh hưởng 0 thông báo production hiện có |

---

## 20. Exit criteria

R1-A1 được phép FROZEN sau implementation + independent review khi:

1. Frozen grammar (§3) đã implement đúng như freeze.
2. **95/95** frozen corpus PASS.
3. Production inventory (72 field) nằm trong grammar — đã đo trước: 0 ngoài.
4. Mutation-by-revert (§15, 11 mutation) chứng minh oracle bắt được regression.
5. Không BLOCKING finding theo §14.
6. HARDENING finding chỉ được ghi backlog.
7. Business non-regression PASS — baseline `702 passed, 9 skipped` giữ nguyên
   hoặc chỉ đổi ở đúng những dòng migration đã liệt kê ở §17.
8. Scope sạch: `git diff --stat` chỉ chạm các đường dẫn ở §16.

**Không yêu cầu**: "không ai có thể nghĩ ra attack Python mới".


---

## 20b. Biên framework — FREEZE (HD-POST-A1-02)

Biên R1-A1 bắt đầu tại thời điểm **code của `@canonical` bắt đầu execution**.

Exception xảy ra TRƯỚC biên đó — do `dataclasses`, `typing`, interpreter, hay
quá trình dựng chính annotation object — được phân loại
`OUTSIDE_FRAMEWORK_BOUNDARY`, nhưng **chỉ khi chứng minh đủ bốn mệnh đề**:

| | Mệnh đề |
|---|---|
| **A** | `@canonical` chưa bắt đầu xử lý class mục tiêu |
| **B** | registry canonical không đổi |
| **C** | class mục tiêu không nhận canonical partial state / canonical mutation |
| **D** | `canonical.py` KHÔNG xuất hiện trong traceback, và frame chịu trách nhiệm nằm trong stdlib |

Nếu `@canonical` ĐÃ bắt đầu execution rồi mới để raw foreign exception thoát ra:
đó là **BLOCKING R1-A1 DEFECT**, không phải outside-boundary.
`OUTSIDE_FRAMEWORK_BOUNDARY` không được dùng để che lỗi bên trong canonical.

R1-A1 **không** mở rộng biên ngược vào `dataclasses`, `typing`, quá trình dựng
annotation, hay interpreter internals. `canonical.py` **không** được sửa để cố
bắt các exception này.

## 21. Kết quả implementation

Repair SHA: xem §21.1. Exact starting SHA cho mọi so sánh correctness vẫn là
`1b0da151c2dae9020c0adcc4118a3e2543cefb77`; `5a0f27c` chỉ là plan checkpoint và
KHÔNG được dùng làm bằng chứng defect đã tồn tại hay đã được sửa.

### 21.1. Kết quả tổng hợp

| Hạng mục | Kết quả |
|---|---|
| Frozen corpus | **102/105 PASS**, 3 case chờ quyết định Owner (§21.2) |
| Mutation-by-revert M-1 → M-11 | **11/11** bị bắt; không mutation nào sót lại trong worktree |
| Production inventory | 11 type / 72 field, **0 field ngoài ngữ pháp**; hình thái `class` 37, `optional` 34, `any` 1 |
| Thông báo lỗi production | 3/3 giữ **nguyên từng byte** |
| Suite ngoài R1-A1 | 497 passed, 9 skipped — **không đổi so với `1b0da151`** |
| R1 probes | 43 probe, BLOCKED=39, OUT=1, RESIDUAL=3 — khớp baseline |
| R1-A probes | 25 probe, BLOCKED=23, OUT=2 — khớp baseline |

### 21.2. BA case OUTSIDE_FRAMEWORK_BOUNDARY (HD-POST-A1-02 — Owner ĐÃ DUYỆT)

`K03`, `L03`, `M02` được phân loại `OUTSIDE_FRAMEWORK_BOUNDARY`. Cả ba nhắm vào
thuộc tính mà CPython tự đọc TRƯỚC khi `@canonical` bắt đầu chạy. Không tùy
chọn `@dataclass` nào tránh được (`repr=False`, `eq=False` đều đã thử).

**Bằng chứng bốn mệnh đề, đo trên interpreter đã ghim (§21.2b):**

| Case | A: canonical chưa chạy | B: registry | C: partial state | D: canonical.py trong traceback | Foreign component chịu trách nhiệm |
|---|---|---|---|---|---|
| `K03` | ✔ chưa | 11 → 11 | không | không | `dataclasses._process_class` |
| `L03` | ✔ chưa | 11 → 11 | không | không | `inspect.formatannotation` (gọi từ `dataclasses`) |
| `M02` | ✔ chưa | 11 → 11 | không | không | `typing._GenericAlias.__repr__` (gọi từ `inspect` ← `dataclasses`) |

Chuỗi module quan sát được:

    K03  <caller> -> dataclasses -> dataclasses
    L03  <caller> -> dataclasses -> dataclasses -> inspect -> inspect -> inspect
    M02  <caller> -> dataclasses -> dataclasses -> inspect -> inspect -> inspect -> typing

**Oracle KHÔNG dùng `xfail`.** `xfail` chỉ chứng minh test fail; nó không chứng
minh fail ĐÚNG VÌ biên. Ba case nay là oracle **PASS** với assertion tường minh
(`test_outside_boundary_case_is_proven_not_merely_failing`), và assertion dựa
trên biên NGỮ NGHĨA — `canonical.py` vắng mặt trong traceback, canonical chưa
entered, registry bất biến, class sạch — chứ không dựa vào
`filename == dataclasses.py:946`. Nếu CPython đổi và `canonical` bắt đầu xuất
hiện trong đường xử lý trước exception, mệnh đề A và D sai và **test FAIL**.

Đây là **TEST-ONLY CHANGE**: `app/modules/domain/canonical.py` không bị sửa.

### 21.2b. Ghim interpreter (§6)

| | |
|---|---|
| implementation | `cpython` |
| `sys.version` | `3.11.15 (main, Mar  3 2026, 09:26:23) [GCC 13.3.0]` |
| `sys.version_info` | `(3, 11, 15, 'final', 0)` |
| foreign component quan sát được | `dataclasses` · `inspect` · `typing` |
| call site evidence (interpreter HIỆN TẠI, **không** phải invariant) | `dataclasses.py:946 in _process_class` · `inspect.py:1438 in formatannotation` · `typing.py:1535 in __repr__` |

Số dòng chỉ là evidence của interpreter hiện tại và **không** được hard-code
thành invariant lâu dài.

**Cách re-verify trên interpreter khác:**

    PYTHONPATH=. python3 -m pytest tests/test_r1a1_annotation_contract.py \
        -k "outside_boundary or interpreter" -q

`test_outside_boundary_classification_is_pinned_to_a_verified_interpreter` FAIL
ngay khi minor version khác `3.11`, buộc re-verify thay vì im lặng carry phân
loại cũ. Sau khi re-verify, cập nhật `VERIFIED_PYTHON_VERSION` /
`VERIFIED_VERSION_INFO` trong `tools/analysis/r1a1_annotation_probes.py`.

### 21.2c. Số học corpus (§8)

    FROZEN CORPUS:                105/105 CLASSIFIED
    IN-SCOPE:                     102/102 PASS
    OUTSIDE_FRAMEWORK_BOUNDARY:     3/3   correctly classified (K03, L03, M02)
    UNCLASSIFIED:                     0
    BLOCKING FAIL:                    0

    105 = 102 + 3

Sắc thái cần biết: `T03` ("`typing` tự nổ khi DỰNG annotation") cũng mang
expected outcome `OUTSIDE_FRAMEWORK_BOUNDARY`, nhưng nó mang **từ bản freeze
gốc** chứ không do HD-POST-A1-02 phân loại lại — nó chưa bao giờ là case hỏng.
Theo cách chia §8, bucket `OUTSIDE_FRAMEWORK_BOUNDARY` gồm ĐÚNG ba ID được
phân loại lại, nên `T03` được đếm trong 102 IN-SCOPE. Nếu chia theo
expected-outcome thay vì theo quyết định, số học là `105 = 101 + 4`. Hai cách
chia đều đúng; §8 chốt cách thứ nhất.

### 21.2d. K01 / M01 / M02 — CASE CONSTRUCTION CORRECTION (HD-POST-A1-03)

Owner ratify ba correction dưới đây. Phân loại: **CASE CONSTRUCTION
CORRECTION**, KHÔNG phải EXPECTED OUTCOME CHANGE — mỗi correction làm case
chạm đúng boundary mà nó tuyên bố kiểm tra, thay vì PASS/FAIL vì một cơ chế
khác.

**K01**

| | |
|---|---|
| 1. Mô tả trong PLAN | metaclass có `__repr__` raise **VÀ** `__name__` raise |
| 2. Construction ban đầu | `__getattribute__` nổ với `__name__` **và `__module__`** |
| 3. Vấn đề | `__module__` không nằm trong mô tả; nó đúng là thuộc tính CPython `@dataclass` đọc, nên case rơi vào biên CPython và không còn đo được điều nó tuyên bố |
| 4. Construction đã sửa | `__getattribute__` chỉ nổ với `__name__` |
| 5. Boundary chạm thật | biên framework — `@canonical` chạy và từ chối |
| 6. Expected trước | `UNSUPPORTED_AT_DECORATION` |
| 7. Expected sau | `UNSUPPORTED_AT_DECORATION` — **không đổi** |
| 8. Semantic intent | không đổi: class target có `__repr__`/`__name__` thù địch phải bị từ chối mà không ai chạy chúng |

**M01**

| | |
|---|---|
| 1. Mô tả trong PLAN | `get_origin` NỔ với exception có `__str__` thù địch |
| 2. Construction ban đầu | object thường mang property `__origin__` raise |
| 3. Vấn đề | `typing.get_origin()` kiểm `isinstance(tp, (_BaseGenericAlias, GenericAlias, …))` TRƯỚC, nên với object thường nó trả `None` mà **không hề chạm `__origin__`** — case PASS đúng kết quả nhưng SAI CƠ CHẾ (bị loại ở C2 "ngoài ngữ pháp") |
| 4. Construction đã sửa | `types.GenericAlias` subclass, `__getattribute__` nổ với `__origin__` |
| 5. Boundary chạm thật | biên lạ **B1** (`get_type_hints`) — vẫn là biên framework, exception lạ được normalize không render |
| 6. Expected trước | `UNSUPPORTED_AT_DECORATION` |
| 7. Expected sau | `UNSUPPORTED_AT_DECORATION` — **không đổi** |
| 8. Semantic intent | không đổi: exception lạ có `__str__` thù địch phải thành `CanonicalContractViolation` mà không bị render |

**M02**

| | |
|---|---|
| 1. Mô tả trong PLAN | `get_args` NỔ với exception có `__str__` thù địch |
| 2. Construction ban đầu | object thường mang `__origin__` + property `__args__` raise |
| 3. Vấn đề | như M01: `get_args()` không chạm `__args__` của object thường. Bản sửa thứ nhất dùng `__getattr__` cũng không đủ — `_GenericAlias` lưu `__args__` trong `__dict__` nên `__getattr__` không bao giờ được gọi |
| 4. Construction đã sửa | `typing._GenericAlias` subclass, **`__getattribute__`** nổ với `__args__` |
| 5. Boundary chạm thật | **ngoài biên framework** — CPython `@dataclass` đọc `__args__` trước khi `@canonical` chạy |
| 6. Expected trước | `UNSUPPORTED_AT_DECORATION` |
| 7. Expected sau | `OUTSIDE_FRAMEWORK_BOUNDARY` (HD-POST-A1-02) |
| 8. Semantic intent | không đổi: hostility trên `__args__` không được để lại raw leak hay partial state. Correction làm lộ ra rằng chủ thể xử lý là CPython chứ không phải framework — chính đó là lý do HD-POST-A1-02 tồn tại |

**Từ Review Candidate SHA của phiên này trở đi: K01 / M01 / M02 CONSTRUCTION =
FROZEN.** Mọi thay đổi construction tiếp theo cần HUMAN ESCALATION.

### 21.3. Ma trận mutation-by-revert

| # | Mutation | Corpus FAIL | Test FAIL |
|---|---|---|---|
| M-1 | `type(v) is T` → `isinstance(v, T)` | J01, J02, J03, X02, Y03, Z01 | 4 test |
| M-2 | allowlist → mọi class metaclass `type` | 26 case (F, G, H, I, K, N, O, P, Q, V, W) | 2 test |
| M-3 | re-admit generic có tham số | A03, A04, D01–D06, E01–E03, Q02, Q03, T02 | 1 test |
| M-4 | re-admit union tổng quát | A02 | 1 test |
| M-5 | re-admit `Literal[...]` | B01, B02, B04 | 1 test |
| M-6 | khôi phục text object lạ trong thông báo | K01, Z01, Z02, Z03 | 3 test |
| M-7 | gỡ cổng metaclass C9 | V01, Z01 | 3 test |
| M-8 | mutable guard → `isinstance` | — | `test_the_mutable_guard_never_consults_a_hostile_class_attribute` |
| M-9 | gỡ luật pseudo-field | R01–R04 | 1 test |
| M-10 | gỡ ngân sách node | — | `test_a_wide_union_is_stopped_by_the_node_budget_not_by_arity` |
| M-11 | `from None` → `from exc` | — | 2 test |

**Phân loại evidence (§10).** `11/11 MUTATIONS DISCRIMINATED`, tách hai loại:

| Loại | Mutation |
|---|---|
| **A — Frozen-corpus discrimination** | M-1, M-2, M-3, M-4, M-5, M-6, M-7, M-9 (8) |
| **B — Hardening coverage discrimination** | M-8, M-10, M-11 (3) |

M-8/M-10/M-11 **không** được retroactively thêm vào frozen corpus. Ba test bắt
chúng được phân loại **HARDENING COVERAGE**, khai báo tường minh trong
`HARDENING_COVERAGE` của `tests/test_r1a1_annotation_contract.py` và có test
canh (`test_hardening_coverage_is_declared_and_is_not_part_of_the_corpus`).
Corpus vẫn là 105; acceptance gate không đổi; không renumber.

### 21.4. HARDENING BACKLOG phát hiện trong lúc implement

| # | Phát hiện | Vì sao không sửa ở vòng này |
|---|---|---|
| HB-A1-01 | Corpus thiếu case "field `Any` + giá trị có `__class__` nổ" — case duy nhất phân biệt `issubclass(type(v),…)` với `isinstance(v,…)` | Rule B: ngoài frozen corpus |
| HB-A1-02 | Corpus thiếu case `Union` > 511 nhánh — case duy nhất chạm ngân sách node C12 | Rule B |
| HB-A1-03 | Corpus thiếu case khẳng định `__cause__ is None` ở biên lạ | Rule B |
| HB-A1-04 | Biên B2/B3 tới được biệt lập nhưng CPython `@dataclass` luôn nổ trước từ một khai báo canonical thật; chỉ B1 tới được thực sự | Là quan sát về biên, không phải lỗ hổng |
| HB-A1-05 | `validate_reference_integrity.py` FAIL với 3 reference chết trong `TASK-REM-T06` | Có SẴN từ trước, ngoài touch-area R1-A1. **CẤM sửa** trong task này — sửa là SCOPE VIOLATION |
| HB-A1-06 | **B2/B3 không có mutation coverage độc lập.** HB-A1-04 đã xác định chỉ **B1** reachable từ một khai báo production-like. `M02` từng chạm B2/B3 nhưng nay là `OUTSIDE_FRAMEWORK_BOUNDARY`. Ghi rõ: **B2/B3 = defensive boundary, unreachable-by-current-construction, independently untested** | HARDENING. Không repair trong R1-A1 finalization |
| HB-A1-07 | **Mutable guard phụ thuộc một invariant chưa được canh.** `issubclass(type(v), MUTABLES)` an toàn vì `issubclass` điều phối theo metaclass của VẾ PHẢI, và mọi member của `MUTABLES` hiện có metaclass ĐÚNG là builtin `type`. Nếu ai đó thêm vào `MUTABLES` một type có custom metaclass, phép kiểm sẽ chạy `__subclasscheck__` của người dùng và primitive mất tính an toàn. **CẤM thêm type có custom metaclass vào `MUTABLES` nếu chưa mở Owner Decision / hardening task riêng.** Không mở rộng `MUTABLES` trong phiên này | HARDENING |

### 21.5. Scope audit

Đúng 3 file production/test/tool bị sửa, tất cả nằm trong touch-area §16:

    app/modules/domain/canonical.py
    tests/test_r1a1_annotation_contract.py
    tools/analysis/r1a1_annotation_probes.py

Không file nào dưới `app/modules/**` ngoài `canonical.py`. Không file test
A3/D nào. **Không annotation production nào phải migrate** (0/72 ngoài ngữ
pháp), đúng như §17 đã dự đoán trước khi implement.


### 21.6. Audit metaclass — 11 production canonical type (§13)

| Class | Module | Metaclass | `type(cls) is type` |
|---|---|---|---|
| `AffectedRow` | `app.modules.validation.models` | `type` | TRUE |
| `AmbiguousRow` | `app.modules.validation.models` | `type` | TRUE |
| `RowProvenance` | `app.modules.validation.models` | `type` | TRUE |
| `Diagnostics` | `app.modules.validation.models` | `type` | TRUE |
| `ReviewItem` | `app.modules.validation.models` | `type` | TRUE |
| `MappingStats` | `app.modules.validation.employee_mapping` | `type` | TRUE |
| `RecordRef` | `app.modules.mapping.employee_mapper` | `type` | TRUE |
| `MappingResult` | `app.modules.mapping.employee_mapper` | `type` | TRUE |
| `DateWindow` | `app.modules.mapping.employee_mapper` | `type` | TRUE |
| `EmployeeRecord` | `app.modules.mapping.employee_mapper` | `type` | TRUE |
| `EmployeeMaster` | `app.modules.mapping.employee_mapper` | `type` | TRUE |

**Không** production canonical type nào dùng `EnumMeta`, `ABCMeta`,
`_ProtocolMeta`, hay metaclass tự viết. Cổng C9 vì thế **không** từ chối một
canonical type nào của chính dự án. 11/11 qua cổng.

**Hai "framework class" trong allowlist là gì, và vì sao không xung đột C9:**

| Class | Metaclass | MRO | Mang `@canonical`? |
|---|---|---|---|
| `FrozenMapping` | `ABCMeta` | `FrozenMapping → Mapping → Collection → Sized → Iterable → Container → object` | KHÔNG |
| `FrozenCounter` | `ABCMeta` | `FrozenCounter → FrozenMapping → …` | KHÔNG |

Cả hai có metaclass `ABCMeta` (thừa hưởng từ `collections.abc.Mapping`), nhưng
**không xung đột với C9** vì hai vai trò khác nhau:

- **C9 áp lên TARGET CỦA `@canonical`** — class đang được decorate. Framework
  phải GHI thuộc tính lên class đó, và với metaclass tuỳ biến thao tác ghi ấy
  chạy code người dùng. `FrozenMapping`/`FrozenCounter` **không** mang
  `@canonical`, nên C9 không bao giờ chạm tới chúng.
- **Chúng chỉ là ANNOTATION TARGET**, và phép kiểm cho annotation target là
  `type(value) is T` — một phép so con trỏ **không** điều phối qua metaclass.
  Vì thế `ABCMeta` của chúng không tham gia bất kỳ quyết định an toàn nào.

Đây chính là lý do bản này bỏ được luật metaclass cũ
(`_TRUSTED_NON_TYPE_METACLASS_CLASSES`): khi phép kiểm là định danh, metaclass
của annotation target thôi liên quan.

### 21.7. Reachability audit (§12) — audit, KHÔNG repair

**HB-A1-02 — "Union > 511 branches": `REACHABLE`.**

Đường đi cụ thể: bất kỳ tác giả nào viết `Union[<512+ nhánh>]` làm annotation.
`typing.get_origin()` trả `typing.Union`, `get_args()` trả tuple 600 phần tử,
parser cộng `len(args)` vào `nodes` và chạm `_MAX_ANNOTATION_NODES` **trước**
phép kiểm arity (đo được: node-budget ở vị trí 894 trong `_build_spec`, arity ở
977). Đo trực tiếp: `Union` 600 nhánh → từ chối bởi **NODE BUDGET (C12)`.

Lưu ý quan trọng: reachable với tư cách **INPUT**, không phải với tư cách một
production hợp lệ của ngữ pháp. Ngữ pháp chỉ nhận `Optional[X]` (đúng 2 nhánh),
nên một union 600 nhánh không bao giờ nằm trên đường SUPPORTED — nó chỉ tới
được vì parser buộc phải ĐẾM args trước khi biết arity sai.

**M-10 — node budget enforcement: `REACHABLE` nhưng OUTCOME-REDUNDANT.**

Enforcement được thực thi thật và có đường tới (như trên), nên **không** phải
`DEFENSIVE_UNREACHABLE`. Nhưng dưới ngữ pháp hiện tại nó **không quyết định
outcome**: gỡ ngân sách đi thì union 600 nhánh vẫn bị từ chối — bởi luật arity
thay vì bởi C12. Chỉ *lý do* từ chối đổi, không phải *kết quả*. Đó đúng là lý
do M-10 không bị frozen corpus bắt (corpus khẳng định outcome) mà chỉ bị
hardening test bắt (test khẳng định lý do).

Kết luận: C12 là **defense-in-depth cho một ngữ pháp tương lai** có thể nhận
union n-ary. **Không xoá enforcement. Không xoá test. Không repair.**

### 21.8. Bảng ánh xạ Test ID → Frozen Case ID (§20)

Toàn bộ 105 case. Node ID của pytest mang chính Case ID, nên bảng này đọc thẳng
được từ `python3 -m pytest tests/test_r1a1_annotation_contract.py --collect-only -q`.

| Frozen Case ID | Test node | Classification | Result |
|---|---|---|---|
| `A01` | `test_frozen_corpus_case[A01-A]` | IN-SCOPE | PASS |
| `A02` | `test_frozen_corpus_case[A02-A]` | IN-SCOPE | PASS |
| `A03` | `test_frozen_corpus_case[A03-A]` | IN-SCOPE | PASS |
| `A04` | `test_frozen_corpus_case[A04-A]` | IN-SCOPE | PASS |
| `A05` | `test_frozen_corpus_case[A05-A]` | IN-SCOPE | PASS |
| `A06` | `test_frozen_corpus_case[A06-A]` | IN-SCOPE | PASS |
| `A07` | `test_frozen_corpus_case[A07-A]` | IN-SCOPE | PASS |
| `A08` | `test_frozen_corpus_case[A08-A]` | IN-SCOPE | PASS |
| `B01` | `test_frozen_corpus_case[B01-B]` | IN-SCOPE | PASS |
| `B02` | `test_frozen_corpus_case[B02-B]` | IN-SCOPE | PASS |
| `B03` | `test_frozen_corpus_case[B03-B]` | IN-SCOPE | PASS |
| `B04` | `test_frozen_corpus_case[B04-B]` | IN-SCOPE | PASS |
| `C01` | `test_frozen_corpus_case[C01-C]` | IN-SCOPE | PASS |
| `C02` | `test_frozen_corpus_case[C02-C]` | IN-SCOPE | PASS |
| `C03` | `test_frozen_corpus_case[C03-C]` | IN-SCOPE | PASS |
| `C04` | `test_frozen_corpus_case[C04-C]` | IN-SCOPE | PASS |
| `C05` | `test_frozen_corpus_case[C05-C]` | IN-SCOPE | PASS |
| `C06` | `test_frozen_corpus_case[C06-C]` | IN-SCOPE | PASS |
| `C07` | `test_frozen_corpus_case[C07-C]` | IN-SCOPE | PASS |
| `D01` | `test_frozen_corpus_case[D01-D]` | IN-SCOPE | PASS |
| `D02` | `test_frozen_corpus_case[D02-D]` | IN-SCOPE | PASS |
| `D03` | `test_frozen_corpus_case[D03-D]` | IN-SCOPE | PASS |
| `D04` | `test_frozen_corpus_case[D04-D]` | IN-SCOPE | PASS |
| `D05` | `test_frozen_corpus_case[D05-D]` | IN-SCOPE | PASS |
| `D06` | `test_frozen_corpus_case[D06-D]` | IN-SCOPE | PASS |
| `E01` | `test_frozen_corpus_case[E01-E]` | IN-SCOPE | PASS |
| `E02` | `test_frozen_corpus_case[E02-E]` | IN-SCOPE | PASS |
| `E03` | `test_frozen_corpus_case[E03-E]` | IN-SCOPE | PASS |
| `F01` | `test_frozen_corpus_case[F01-F]` | IN-SCOPE | PASS |
| `G01` | `test_frozen_corpus_case[G01-G]` | IN-SCOPE | PASS |
| `G02` | `test_frozen_corpus_case[G02-G]` | IN-SCOPE | PASS |
| `G03` | `test_frozen_corpus_case[G03-G]` | IN-SCOPE | PASS |
| `H01` | `test_frozen_corpus_case[H01-H]` | IN-SCOPE | PASS |
| `H02` | `test_frozen_corpus_case[H02-H]` | IN-SCOPE | PASS |
| `H03` | `test_frozen_corpus_case[H03-H]` | IN-SCOPE | PASS |
| `I01` | `test_frozen_corpus_case[I01-I]` | IN-SCOPE | PASS |
| `I02` | `test_frozen_corpus_case[I02-I]` | IN-SCOPE | PASS |
| `J01` | `test_frozen_corpus_case[J01-J]` | IN-SCOPE | PASS |
| `J02` | `test_frozen_corpus_case[J02-J]` | IN-SCOPE | PASS |
| `J03` | `test_frozen_corpus_case[J03-J]` | IN-SCOPE | PASS |
| `K01` | `test_frozen_corpus_case[K01-K]` | IN-SCOPE | PASS |
| `K02` | `test_frozen_corpus_case[K02-K]` | IN-SCOPE | PASS |
| `K03` | `test_frozen_corpus_case[K03-K]` | OUTSIDE_FRAMEWORK_BOUNDARY | PASS |
| `L01` | `test_frozen_corpus_case[L01-L]` | IN-SCOPE | PASS |
| `L02` | `test_frozen_corpus_case[L02-L]` | IN-SCOPE | PASS |
| `L03` | `test_frozen_corpus_case[L03-L]` | OUTSIDE_FRAMEWORK_BOUNDARY | PASS |
| `M01` | `test_frozen_corpus_case[M01-M]` | IN-SCOPE | PASS |
| `M02` | `test_frozen_corpus_case[M02-M]` | OUTSIDE_FRAMEWORK_BOUNDARY | PASS |
| `N01` | `test_frozen_corpus_case[N01-N]` | IN-SCOPE | PASS |
| `N02` | `test_frozen_corpus_case[N02-N]` | IN-SCOPE | PASS |
| `O01` | `test_frozen_corpus_case[O01-O]` | IN-SCOPE | PASS |
| `O02` | `test_frozen_corpus_case[O02-O]` | IN-SCOPE | PASS |
| `P01` | `test_frozen_corpus_case[P01-P]` | IN-SCOPE | PASS |
| `P02` | `test_frozen_corpus_case[P02-P]` | IN-SCOPE | PASS |
| `P03` | `test_frozen_corpus_case[P03-P]` | IN-SCOPE | PASS |
| `Q01` | `test_frozen_corpus_case[Q01-Q]` | IN-SCOPE | PASS |
| `Q02` | `test_frozen_corpus_case[Q02-Q]` | IN-SCOPE | PASS |
| `Q03` | `test_frozen_corpus_case[Q03-Q]` | IN-SCOPE | PASS |
| `Q04` | `test_frozen_corpus_case[Q04-Q]` | IN-SCOPE | PASS |
| `Q05` | `test_frozen_corpus_case[Q05-Q]` | IN-SCOPE | PASS |
| `Q06` | `test_frozen_corpus_case[Q06-Q]` | IN-SCOPE | PASS |
| `Q07` | `test_frozen_corpus_case[Q07-Q]` | IN-SCOPE | PASS |
| `Q08` | `test_frozen_corpus_case[Q08-Q]` | IN-SCOPE | PASS |
| `R01` | `test_frozen_corpus_case[R01-R]` | IN-SCOPE | PASS |
| `R02` | `test_frozen_corpus_case[R02-R]` | IN-SCOPE | PASS |
| `R03` | `test_frozen_corpus_case[R03-R]` | IN-SCOPE | PASS |
| `R04` | `test_frozen_corpus_case[R04-R]` | IN-SCOPE | PASS |
| `S01` | `test_frozen_corpus_case[S01-S]` | IN-SCOPE | PASS |
| `S02` | `test_frozen_corpus_case[S02-S]` | IN-SCOPE | PASS |
| `T01` | `test_frozen_corpus_case[T01-T]` | IN-SCOPE | PASS |
| `T02` | `test_frozen_corpus_case[T02-T]` | IN-SCOPE | PASS |
| `T03` | `test_frozen_corpus_case[T03-T]` | IN-SCOPE | PASS |
| `U01` | `test_frozen_corpus_case[U01-U]` | IN-SCOPE | PASS |
| `U02` | `test_frozen_corpus_case[U02-U]` | IN-SCOPE | PASS |
| `V01` | `test_frozen_corpus_case[V01-V]` | IN-SCOPE | PASS |
| `V02` | `test_frozen_corpus_case[V02-V]` | IN-SCOPE | PASS |
| `V03` | `test_frozen_corpus_case[V03-V]` | IN-SCOPE | PASS |
| `W01` | `test_frozen_corpus_case[W01-W]` | IN-SCOPE | PASS |
| `W02` | `test_frozen_corpus_case[W02-W]` | IN-SCOPE | PASS |
| `W03` | `test_frozen_corpus_case[W03-W]` | IN-SCOPE | PASS |
| `W04` | `test_frozen_corpus_case[W04-W]` | IN-SCOPE | PASS |
| `W05` | `test_frozen_corpus_case[W05-W]` | IN-SCOPE | PASS |
| `W06` | `test_frozen_corpus_case[W06-W]` | IN-SCOPE | PASS |
| `W07` | `test_frozen_corpus_case[W07-W]` | IN-SCOPE | PASS |
| `X01` | `test_frozen_corpus_case[X01-X]` | IN-SCOPE | PASS |
| `X02` | `test_frozen_corpus_case[X02-X]` | IN-SCOPE | PASS |
| `X03` | `test_frozen_corpus_case[X03-X]` | IN-SCOPE | PASS |
| `X04` | `test_frozen_corpus_case[X04-X]` | IN-SCOPE | PASS |
| `X05` | `test_frozen_corpus_case[X05-X]` | IN-SCOPE | PASS |
| `X06` | `test_frozen_corpus_case[X06-X]` | IN-SCOPE | PASS |
| `X07` | `test_frozen_corpus_case[X07-X]` | IN-SCOPE | PASS |
| `X08` | `test_frozen_corpus_case[X08-X]` | IN-SCOPE | PASS |
| `X09` | `test_frozen_corpus_case[X09-X]` | IN-SCOPE | PASS |
| `X10` | `test_frozen_corpus_case[X10-X]` | IN-SCOPE | PASS |
| `X11` | `test_frozen_corpus_case[X11-X]` | IN-SCOPE | PASS |
| `X12` | `test_frozen_corpus_case[X12-X]` | IN-SCOPE | PASS |
| `X13` | `test_frozen_corpus_case[X13-X]` | IN-SCOPE | PASS |
| `Y01` | `test_frozen_corpus_case[Y01-Y]` | IN-SCOPE | PASS |
| `Y02` | `test_frozen_corpus_case[Y02-Y]` | IN-SCOPE | PASS |
| `Y03` | `test_frozen_corpus_case[Y03-Y]` | IN-SCOPE | PASS |
| `Y04` | `test_frozen_corpus_case[Y04-Y]` | IN-SCOPE | PASS |
| `Z01` | `test_frozen_corpus_invariant[Z01]` | IN-SCOPE | PASS |
| `Z02` | `test_frozen_corpus_invariant[Z02]` | IN-SCOPE | PASS |
| `Z03` | `test_frozen_corpus_invariant[Z03]` | IN-SCOPE | PASS |
| `Z04` | `test_frozen_corpus_invariant[Z04]` | IN-SCOPE | PASS |

Tổng: **105 dòng** · 102 IN-SCOPE · 3 OUTSIDE_FRAMEWORK_BOUNDARY (`K03`,
`L03`, `M02`) · 0 duplicate · 0 case thiếu oracle.
