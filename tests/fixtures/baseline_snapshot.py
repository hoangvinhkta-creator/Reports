"""Chụp ảnh hành vi nghiệp vụ để chứng minh TASK-110 không gây regression.

**Vì sao file này tồn tại.** Bản sửa kiến trúc của Independent Review #5 viết
lại `EmployeeMapper.resolve()` trên một primitive mới (`resolve_record`). Một
test viết tay khẳng định "kết quả vẫn đúng" chỉ khẳng định lại kỳ vọng của
người viết test. Cách duy nhất chứng minh được là so với hành vi THẬT trước
khi sửa: ảnh chụp dưới `tests/fixtures/baseline/` được sinh tại commit
`8386d345b04b754c061ce03b79116e75f0dfae4e` — trước dòng code sửa chữa đầu
tiên — và commit vào repo làm bằng chứng đông cứng.

    L1  `EmployeeMapper.resolve()` trên tích Descartes raw × as_of.
    L2  **Mọi** trường của `RawRow` / `WorkingLine` / `Order` mà `run_import()`
        sinh ra, dẫn xuất bằng `dataclasses.fields()`.

**L2 là STRUCTURAL, không phải danh sách trắng (HD-110-11, INVARIANT O).**
Bản trước liệt kê 9 trường trong 34 của `WorkingLine`. Independent Review #6
chứng minh hậu quả bằng một phép thử: cộng 999.999 vào `total_sales` của MỌI
dòng và đổi `price_source` — oracle vẫn **PASS**. Một oracle dựng từ liệt kê
không thể phát hiện thứ nằm ngoài liệt kê, và cái test "đã phủ đủ trường chưa"
thì đối chiếu danh sách trắng với **chính nó** — một tautology.

Nay mọi trường được lấy từ `dataclasses.fields()`, nên một trường thêm vào
ngày mai tự động được canh, và một trường bị xoá cũng bị phát hiện.

Review Queue cố ý KHÔNG nằm trong L2: nó chính là thứ đang được sửa. L2 tồn
tại để chứng minh việc sửa nó không rò rỉ sang tính toán tiền.

Sinh lại ảnh chụp:  python3 -m tests.fixtures.baseline_snapshot
KHÔNG bao giờ sinh lại sau khi đã sửa code — làm vậy là ghi đè chính bằng
chứng, và mọi so sánh sau đó sẽ tự động PASS một cách vô nghĩa.
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any, Optional

from app.modules.validation.models import PII_FIELD_NAMES

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_DIR = Path(__file__).resolve().parent / "baseline"
CONFIG_DIR = REPO_ROOT / "config"

L1_V1_PATH = BASELINE_DIR / "employee_resolve_matrix_v1.json"
L1_PATH = BASELINE_DIR / "employee_resolve_matrix.json"
L2_PATH = BASELINE_DIR / "business_output.json"

def _digest(value: Any) -> str:
    """Digest ổn định cho trường chứa PII (HD-110-11).

    Ảnh chụp được commit vào repo. Lưu giá trị thô sẽ va
    `governance/product/17_DATA_GOVERNANCE_PRIVACY.md` và CHECK-110-17, còn
    loại trừ các trường đó sẽ dựng lại đúng danh sách trắng mà INVARIANT O vừa
    xoá bỏ. Digest giữ được cả hai: thay đổi vẫn bị phát hiện, giá trị không
    bao giờ nằm trong repo — và điều đó vẫn đúng nếu sau này chạy trên dữ liệu
    thật.

    `hashlib`, không phải `hash()`: `hash()` của Python được salt ngẫu nhiên
    theo tiến trình, nên ảnh chụp sẽ khác nhau giữa hai lần chạy.
    """
    if value is None:
        return "∅"
    return "sha256:" + hashlib.sha256(
        repr(value).encode("utf-8")
    ).hexdigest()[:16]


def _plain(value: Any) -> Any:
    """Serialize không mất mát. Tiền là `Decimal` nên thành chuỗi: `float` sẽ
    biến so sánh chính xác thành so sánh xấp xỉ (ADR-103)."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, _dt.date):
        return value.isoformat()
    return str(value)


def _snapshot_dataclass(obj: Any, skip: frozenset = frozenset()) -> dict[str, Any]:
    """Mọi trường của một dataclass, DẪN XUẤT chứ không liệt kê.

    `skip` chỉ dành cho các trường là **liên kết cấu trúc** (`WorkingLine.raw`,
    `Order.lines`) — chúng được chụp riêng ở cấp của chính chúng, nên đưa vào
    đây sẽ nhân đôi dữ liệu, không phải bỏ sót.
    """
    if not dataclasses.is_dataclass(obj):
        raise TypeError(
            f"{type(obj).__name__} không còn là dataclass — oracle structural "
            "sẽ thoái hoá im lặng. Sửa oracle trước khi đổi kiểu."
        )
    out: dict[str, Any] = {}
    for f in dataclasses.fields(obj):
        if f.name in skip:
            continue
        value = getattr(obj, f.name)
        out[f.name] = _digest(value) if f.name in PII_FIELD_NAMES else _plain(value)
    return out


# Ngày biên của DEC-121: trước `effective_from` sớm nhất, đúng ngày mở, giữa
# kỳ, và mốc chuyển đổi 2027 — cộng "không có ngày" vì mapper chấp nhận None.
AS_OF_DATES: list[Optional[date]] = [
    None,
    date(2025, 12, 31),
    date(2026, 1, 1),
    date(2026, 6, 15),
    date(2026, 12, 31),
    date(2027, 1, 1),
]

# Hậu tố thật mà cột NVBH mang theo: số điện thoại, đôi khi cả tên chi nhánh.
_SUFFIXES = ["", " 0867666533", " - Tân Á 0867666533"]

# Biến thể lệch — đây là nơi drift ẩn náu. Khoảng trắng đôi và khoảng trắng
# đầu chuỗi là chính hai case đã chứng minh `collect_mapping_stats` bất đồng
# với production (Independent Review #5, DRIFT C).
_MUTATIONS = [
    ("nguyên bản", lambda s: s),
    ("khoảng trắng đôi", lambda s: s.replace(" ", "  ", 1)),
    ("khoảng trắng đầu", lambda s: " " + s),
    ("khoảng trắng cuối", lambda s: s + " "),
    ("viết hoa", lambda s: s.upper()),
    ("viết thường", lambda s: s.lower()),
    ("bỏ dấu một ký tự", lambda s: s.replace("ứ", "ư").replace("ạ", "a")),
]

_STANDALONE = [
    None,
    "",
    "   ",
    "Người Lạ Hoàn Toàn 0900000009",
    "Tín",              # prefix cụt — phải KHÔNG khớp
    "Tín Phát Extra",   # prefix lồng
]


def _employee_prefixes() -> list[str]:
    from app.modules.config.loader import load_yaml

    data = load_yaml(CONFIG_DIR / "employees.yaml")
    return [
        row["raw_prefix"]
        for row in data.get("employees", [])
        if row.get("raw_prefix")
    ]


def raw_matrix() -> list[Optional[str]]:
    """Mọi chuỗi raw đưa vào L1, thứ tự tất định."""
    values: list[Optional[str]] = list(_STANDALONE)
    for prefix in _employee_prefixes():
        for suffix in _SUFFIXES:
            for _, mutate in _MUTATIONS:
                candidate = mutate(prefix) + suffix
                if candidate not in values:
                    values.append(candidate)
    return values


def build_l1_v1() -> list[dict[str, Any]]:
    """L1 **bản v1 (lịch sử)** — whitelist 5 trường, giữ nguyên làm bằng chứng.

    Independent Review #7 / Architecture Closure Audit chứng minh bản này bỏ
    sót `MappingResult.record` (O3). Nó KHÔNG bị xoá: nó là bằng chứng đã ký
    của CHECK-110-19 và vẫn được so song song với bản structural.

    Nguyên bản: `resolve()` trên tích Descartes raw × as_of.

    Serialize TOÀN BỘ `MappingResult`, không chỉ `normalized`: `status`,
    `group`, `include_in_kpi` và `default_lead_source` đều là đầu vào của
    KPI/conversion ở hạ nguồn, nên một thay đổi ở bất kỳ trường nào cũng là
    regression.
    """
    from app.modules.mapping.employee_mapper import EmployeeMapper

    mapper = EmployeeMapper.from_yaml(CONFIG_DIR / "employees.yaml")
    rows: list[dict[str, Any]] = []
    for raw_value in raw_matrix():
        for as_of in AS_OF_DATES:
            result = mapper.resolve(raw_value, as_of)
            rows.append(
                {
                    "raw": raw_value,
                    "as_of": as_of.isoformat() if as_of else None,
                    "normalized": result.normalized,
                    "status": result.status,
                    "group": result.group,
                    "include_in_kpi": result.include_in_kpi,
                    "default_lead_source": result.default_lead_source,
                }
            )
    return rows




def _mapping_result_snapshot(result: Any) -> dict[str, Any]:
    """Mọi trường của `MappingResult`, DẪN XUẤT — không liệt kê (HD-110-14).

    `record` là một `RecordRef`, tự nó cũng là dataclass, nên được mở structural
    luôn: một trường thêm vào `RecordRef` ngày mai cũng tự động được canh.
    """
    out: dict[str, Any] = {}
    for f in dataclasses.fields(result):
        value = getattr(result, f.name)
        if dataclasses.is_dataclass(value):
            out[f.name] = {
                sub.name: _plain(getattr(value, sub.name))
                for sub in dataclasses.fields(value)
            }
        else:
            out[f.name] = _plain(value)
    return out


def build_l1() -> list[dict[str, Any]]:
    """L1 **structural** — phủ MỌI trường của `MappingResult` (HD-110-14).

    Bản v1 liệt kê tay 5 trường và vì thế mù với `record`. Ở đây tập trường
    lấy từ `dataclasses.fields()`, nên không trường nào có thể bị bỏ sót — kể
    cả trường thêm vào sau này.
    """
    from app.modules.mapping.employee_mapper import EmployeeMapper

    mapper = EmployeeMapper.from_yaml(CONFIG_DIR / "employees.yaml")
    rows: list[dict[str, Any]] = []
    for raw_value in raw_matrix():
        for as_of in AS_OF_DATES:
            record = {"raw": raw_value, "as_of": as_of.isoformat() if as_of else None}
            record.update(_mapping_result_snapshot(mapper.resolve(raw_value, as_of)))
            rows.append(record)
    return rows


def build_l2(raw_path: Path) -> dict[str, Any]:
    """L2 — đầu ra nghiệp vụ đầu-cuối của `run_import()`, phủ STRUCTURAL.

    Chụp **mọi** trường của cả ba lớp: `RawRow` (lớp RAW bất biến),
    `WorkingLine` và `Order`. Không trường nào được liệt kê bằng tay, nên
    không trường nào có thể bị bỏ sót — kể cả trường được thêm vào sau này.

    `review_queue` bị loại khỏi ảnh chụp một cách có chủ đích: chính nó đang
    được sửa, nên đưa vào sẽ khiến so sánh luôn FAIL và che mất câu hỏi thật —
    "tiền có dịch chuyển không?".
    """
    from app.pipeline import run_import

    result = run_import(raw_path, CONFIG_DIR)

    lines: list[dict[str, Any]] = []
    raws: list[dict[str, Any]] = []
    for order in result.orders:
        for line in order.lines:
            record = _snapshot_dataclass(line, skip=frozenset({"raw"}))
            record["_source_row"] = line.raw.source_row
            lines.append(record)
            raws.append(_snapshot_dataclass(line.raw))

    orders = [
        _snapshot_dataclass(order, skip=frozenset({"lines"}))
        for order in result.orders
    ]

    # **Graph Order -> Lines theo THỨ TỰ** (mục 7). Bản trước làm phẳng lines
    # rồi sort, nên dời một line từ Order A sang Order B mà giữ nguyên mọi
    # scalar là **vô hình** với oracle (Audit, O2). Membership và thứ tự là
    # business state thật: `Order.total_sales` và `line_count` đọc từ nó.
    order_graph = {
        order.order_id: [line.raw.source_row for line in order.lines]
        for order in result.orders
    }

    return {
        "order_graph": order_graph,
        "raw_rows": sorted(raws, key=lambda r: (r["source_row"], r["order_id"])),
        "lines": sorted(lines, key=lambda r: (r["_source_row"], r["order_id"])),
        "orders": sorted(orders, key=lambda r: r["order_id"]),
        "unmapped_line_rows": sorted(
            line.raw.source_row for line in result.unmapped_lines
        ),
        # Ghi lại chính tập trường đã chụp: nếu một trường biến mất khỏi
        # dataclass, so sánh sẽ chỉ ra ngay thay vì im lặng thu hẹp phạm vi.
        "_covered_fields": {
            "raw_rows": sorted(raws[0]) if raws else [],
            "lines": sorted(lines[0]) if lines else [],
            "orders": sorted(orders[0]) if orders else [],
        },
    }


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    import tempfile

    from tests.fixtures.synthetic_workbook import build_synthetic_workbook

    _write(L1_V1_PATH, build_l1_v1())
    _write(L1_PATH, build_l1())
    with tempfile.TemporaryDirectory() as tmp:
        raw_path = Path(tmp) / "synthetic_raw_sample.xlsx"
        build_synthetic_workbook(raw_path)
        _write(L2_PATH, build_l2(raw_path))
    print(f"L1v1 -> {L1_V1_PATH}")
    print(f"L1 -> {L1_PATH}")
    print(f"L2 -> {L2_PATH}")


if __name__ == "__main__":
    main()
