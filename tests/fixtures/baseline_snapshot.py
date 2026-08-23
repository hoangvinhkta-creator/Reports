"""Chụp ảnh hành vi nghiệp vụ để chứng minh TASK-110 không gây regression.

**Vì sao file này tồn tại.** Bản sửa kiến trúc của Independent Review #5 viết
lại `EmployeeMapper.resolve()` trên một primitive mới (`resolve_record`). Một
test viết tay khẳng định "kết quả vẫn đúng" chỉ khẳng định lại kỳ vọng của
người viết test. Cách duy nhất chứng minh được là so với hành vi THẬT trước
khi sửa: ảnh chụp dưới `tests/fixtures/baseline/` được sinh tại commit
`8386d345b04b754c061ce03b79116e75f0dfae4e` — trước dòng code sửa chữa đầu
tiên — và commit vào repo làm bằng chứng đông cứng.

    L1  `EmployeeMapper.resolve()` trên tích Descartes raw × as_of.
    L2  Toàn bộ trường NGHIỆP VỤ mà `run_import()` sinh ra, đầu-cuối.

Review Queue cố ý KHÔNG nằm trong L2: nó chính là thứ đang được sửa. L2 tồn
tại để chứng minh việc sửa nó không rò rỉ sang tính toán tiền.

Sinh lại ảnh chụp:  python3 -m tests.fixtures.baseline_snapshot
KHÔNG bao giờ sinh lại sau khi đã sửa code — làm vậy là ghi đè chính bằng
chứng, và mọi so sánh sau đó sẽ tự động PASS một cách vô nghĩa.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_DIR = Path(__file__).resolve().parent / "baseline"
CONFIG_DIR = REPO_ROOT / "config"

L1_PATH = BASELINE_DIR / "employee_resolve_matrix.json"
L2_PATH = BASELINE_DIR / "business_output.json"

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


def build_l1() -> list[dict[str, Any]]:
    """L1 — `resolve()` trên tích Descartes raw × as_of.

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


# Đúng danh sách trường nghiệp vụ chủ dự án chốt cho L2. Tiền là `Decimal` nên
# serialize thành chuỗi: `float` sẽ làm mất chính xác và biến so sánh chính
# xác thành so sánh xấp xỉ (ADR-103).
def _money(value) -> Optional[str]:
    return None if value is None else str(value)


def build_l2(raw_path: Path) -> dict[str, Any]:
    """L2 — đầu ra nghiệp vụ đầu-cuối của `run_import()`.

    `review_queue` bị loại khỏi ảnh chụp một cách có chủ đích: chính nó đang
    được sửa, nên đưa vào sẽ khiến so sánh luôn FAIL và che mất câu hỏi thật —
    "tiền có dịch chuyển không?".
    """
    from app.pipeline import run_import

    result = run_import(raw_path, CONFIG_DIR)

    lines: list[dict[str, Any]] = []
    for order in result.orders:
        for line in order.lines:
            lines.append(
                {
                    "source_row": line.raw.source_row,
                    "order_id": line.order_id,
                    "employee_normalized": line.employee_normalized,
                    "employee_mapping_status": line.employee_mapping_status,
                    "employee_group": line.employee_group,
                    "conversion_scheme_final": line.conversion_scheme_final,
                    "conversion_rate_final": _money(line.conversion_rate_final),
                    "product_group_final": line.product_group_final,
                    "accounting_purchase_price": _money(
                        line.accounting_purchase_price
                    ),
                    "accounting_profit": _money(line.accounting_profit),
                    "lead_source_final": line.lead_source_final,
                }
            )

    orders = [
        {
            "order_id": order.order_id,
            "employee_raw": order.employee_raw,
            "employee_normalized": order.employee_normalized,
            "employee_mapping_status": order.employee_mapping_status,
            "employee_group": order.employee_group,
            "lead_source_final": order.lead_source_final,
        }
        for order in result.orders
    ]

    return {
        "lines": sorted(lines, key=lambda r: (r["source_row"], r["order_id"])),
        "orders": sorted(orders, key=lambda r: r["order_id"]),
        "unmapped_line_rows": sorted(
            line.raw.source_row for line in result.unmapped_lines
        ),
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

    _write(L1_PATH, build_l1())
    with tempfile.TemporaryDirectory() as tmp:
        raw_path = Path(tmp) / "synthetic_raw_sample.xlsx"
        build_synthetic_workbook(raw_path)
        _write(L2_PATH, build_l2(raw_path))
    print(f"L1 -> {L1_PATH}")
    print(f"L2 -> {L2_PATH}")


if __name__ == "__main__":
    main()
