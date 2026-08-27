"""GB-6 + GB-7 — sinh Golden expected output từ fixture ĐÃ ẨN DANH đã commit.

**Chạy TAY, không bao giờ chạy trong test.** Test chỉ ĐỌC file JSON đã commit;
nếu test tự sinh lại expected output thì mọi so sánh sẽ PASS một cách vô
nghĩa — đúng cái bẫy `tests/fixtures/baseline_snapshot.py` đã cảnh báo.

    python3 -m tests.fixtures.golden.build_expected

Không có `UPDATE_SNAPSHOT=1`, không `--accept`, không `--rewrite-golden`.
Sinh lại expected output là một hành động bảo trì tường minh; khi nó làm đổi
giá trị nghiệp vụ thì cần Owner Decision (PLAN §14).

## Hình dạng

Aggregate nghiệp vụ ở mức kỳ + phân rã theo chiều + `order_graph` giữ thứ tự
+ `orders_detail` mức đơn + `lines_digest` mức dòng. **Không** dump từng dòng:
một snapshot 531 dòng × 34 trường cho ra diff không ai đọc được, và PLAN §11
cấm điều đó.

`lines_digest` bù đúng chỗ mà aggregate mù: hoán đổi giá của hai dòng trong
cùng một đơn không đổi bất kỳ tổng nào, kể cả tổng của đơn. Digest được lấy
từ `dataclasses.fields()` chứ không từ một danh sách trắng, nên một trường
thêm vào ngày mai tự động được canh (bài học INVARIANT O của TASK-110).

## Chuẩn hoá

Chuẩn hoá **biểu diễn**, không chuẩn hoá **giá trị nghiệp vụ**:

- `Decimal` -> chuỗi. Không bao giờ `float`: `float` biến so sánh chính xác
  thành xấp xỉ và làm trôi chữ số cuối vào bảng lương (ADR-103).
- `date` -> `isoformat()`.
- `None` giữ nguyên là `null`, KHÔNG thành `0`. Một ô trống và một ô bằng 0 là
  hai sự thật khác nhau (`03_DATA_MODEL_RULES` §5). Mọi tổng tiền vì thế đi
  kèm số ô `pending` tách riêng.
- `json.dumps(sort_keys=True)` cho ổn định — nhưng `order_graph` và
  `orders_detail` là **list**, nên thứ tự dòng trong đơn không bị sort làm mất.

`RawRow.source_file` bị loại khỏi `lines_digest` một cách có chủ đích: nó
bằng `path.name`, nên nếu để vào thì Golden vỡ chỉ vì đổi tên file. Tên file
được canh riêng, tường minh, ở `_environment.fixture_filename`.
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import hashlib
import json
import platform
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Optional

import openpyxl
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.modules.domain.models import MAPPING_STATUS_MAPPED  # noqa: E402
from app.modules.importing.raw_reader import COLUMNS, FIRST_DATA_ROW  # noqa: E402
from app.modules.mapping.employee_mapper import EmployeeMapper  # noqa: E402
from app.modules.validation.text import normalize_text  # noqa: E402
from app.pipeline import run_import  # noqa: E402

from tests.fixtures.golden.anonymize import ANONYMIZATION_VERSION  # noqa: E402

GOLDEN_DIR = Path(__file__).resolve().parent
EXPECTED_DIR = GOLDEN_DIR / "expected"
CONFIG_DIR = REPO_ROOT / "config"

#: Đổi khi HÌNH DẠNG expected output đổi (không phải khi giá trị đổi).
SCHEMA_VERSION = "1.0.0"

#: Điểm vào pipeline được khoá (GB-4). Golden không gọi lại từng module.
PIPELINE_ENTRY_POINT = "app.pipeline.run_import"

#: `source_file` phụ thuộc tên file -> canh riêng ở `_environment`.
_DIGEST_SKIP_RAW = frozenset({"source_file"})

#: Ba kỳ/nguồn dưới đây là DUY NHẤT dataset của Golden này (PLAN §A.4, chỉ thị
#: §6). Không trộn với dataset 11.765 dòng, 14.389 dòng, hay CHECK-110-16.
PERIODS = (
    {
        "period_label": "01.2026",
        "baseline_id": "GOLDEN-TINPHAT-2026-01",
        "fixture_filename": "period_2026_01.xlsx",
        "source_workbook_label": "So_chi_tiet_ban_hang (2)(1).xlsx",
        "source_sha256":
            "4e29747e7c8c40ed58ef728c6f0cf285e2f04ff2f6cf2d5733a334e3e8b78308",
    },
    {
        "period_label": "06.2026",
        "baseline_id": "GOLDEN-TINPHAT-2026-06",
        "fixture_filename": "period_2026_06.xlsx",
        "source_workbook_label": "So_chi_tiet_ban_hang (3).xlsx",
        "source_sha256":
            "ef9a85e0bf9f7c5dc3791ed6852e20978e35bdd19daa5978843007eeb2a0fdaa",
    },
)

#: GB-1 — mỗi aggregate truy về một artifact đã commit TRƯỚC baseline
#: 716ae2e1bcb719c1c8adadbf5506c45c090c2efe. Không aggregate nào chỉ có nguồn
#: là "output của run_import() hôm nay".
PROVENANCE_ANCHORS = {
    "counts.orders":
        "docs/tasks/TASK-101-importer-normalizer.md#CHECK-101-08 · "
        "docs/analysis/_evidence/evidence.json#raw_by_month_employee",
    "counts.raw_rows":
        "docs/tasks/TASK-101-importer-normalizer.md#Đối Chiếu Dữ Liệu Thật",
    "counts.sheet_data_rows":
        "docs/tasks/TASK-101-importer-normalizer.md#Đối Chiếu Dữ Liệu Thật",
    "money.sales_raw_gross":
        "docs/analysis/_evidence/evidence.json#raw_by_month_employee.sales_thousands · "
        "docs/tasks/TASK-101-importer-normalizer.md#CHECK-101-08",
    "money.discount_total":
        "docs/tasks/TASK-101-importer-normalizer.md#Đối Chiếu Dữ Liệu Thật",
    "money.sales_normalized":
        "docs/tasks/TASK-101-importer-normalizer.md#Đối Chiếu Dữ Liệu Thật · DEC-114",
    "money.quantity_total":
        "footer 'Tổng cộng' của chính workbook nguồn (ERP ghi, không do engine tính)",
    "money.erp_profit_total":
        "docs/analysis/_evidence/evidence.json#raw_by_month_employee.profit_thousands",
    "source_footer":
        "dòng 'Tổng cộng' của chính workbook nguồn — oracle độc lập với engine",
    "lead_source":
        "DEC-109 (sửa bởi DEC-119) · docs/analysis/_evidence/evidence.json#ads_keyword_cell_hits · "
        "docs/tasks/TASK-101-importer-normalizer.md#CHECK-101-08",
    "conversion":
        "config/conversion_rates.yaml · ADR-106 §3/§4 · DEC-127 §3",
    "discount_delta":
        "DEC-114 · docs/tasks/TASK-101-importer-normalizer.md#Item 4",
    "employees":
        "config/employees.yaml · DEC-104 · DEC-127 §1",
    "review_queue":
        "đặc tả §18 · DEC-128 — đo LẦN ĐẦU trên dataset này tại phiên "
        "TASK-GOLDEN-BASELINE-001 (không có mốc lịch sử cho hai kỳ Tín Phát)",
    "pricing":
        "TASK-105 PendingPriceProvider — chưa có Price Master (trạng thái hiện tại)",
}


# ------------------------------------------------------------ serialize helpers

def _plain(value: Any) -> Any:
    """Serialize không mất mát. Tiền là `Decimal` nên thành CHUỖI."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, _dt.date):
        return value.isoformat()
    return str(value)


def _dsum(values: Iterable[Optional[Decimal]]) -> list:
    """Tổng + số ô `pending`. `None` KHÔNG bị gộp thành 0."""
    total = Decimal(0)
    pending = 0
    for value in values:
        if value is None:
            pending += 1
        else:
            total += value
    return [str(total), pending]


def _counter(values: Iterable[Any]) -> dict:
    return {str(k): v for k, v in sorted(Counter(values).items(), key=lambda kv: str(kv[0]))}


# ------------------------------------------------------------ source footer

def read_source_footer(path: Path) -> dict:
    """Dòng 'Tổng cộng' do chính ERP ghi — oracle độc lập với engine (I-02).

    Đọc thẳng bằng `openpyxl`, KHÔNG đi qua `read_raw_rows`: nếu đi qua reader
    thì reader vừa là thứ được kiểm vừa là thứ đo, và phép đối chiếu trở thành
    tautology.
    """
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = workbook.active
        footer = None
        sheet_data_rows = 0
        rows_missing_order_id = 0
        for values in sheet.iter_rows(min_row=FIRST_DATA_ROW, values_only=True):
            if all(v is None for v in values):
                continue
            sheet_data_rows += 1
            if not values[COLUMNS["order_id"]]:
                rows_missing_order_id += 1
            if normalize_text(values[0]) == "Tổng cộng":
                footer = {
                    "quantity": _plain(values[COLUMNS["qty"]]),
                    "sales": _plain(values[COLUMNS["sales"]]),
                    "discount": _plain(values[COLUMNS["discount"]]),
                    "profit": _plain(values[COLUMNS["profit"]]),
                }
    finally:
        workbook.close()
    if footer is None:
        raise ValueError(f"{path.name}: không tìm thấy dòng 'Tổng cộng' — "
                         "oracle độc lập I-02 không tồn tại, không sinh Golden.")
    return {
        "footer": footer,
        "sheet_data_rows": sheet_data_rows,
        "rows_missing_order_id": rows_missing_order_id,
    }


# ------------------------------------------------------------ lines digest

def lines_digest(orders: list) -> str:
    """Digest MỌI trường nghiệp vụ của MỌI dòng, DẪN XUẤT chứ không liệt kê.

    Bắt được thay đổi mà aggregate mù: hoán đổi giá hai dòng trong cùng một
    đơn không đổi tổng nào cả. Vì tập trường lấy từ `dataclasses.fields()`,
    một trường thêm vào sau này tự động được canh, và một trường bị xoá cũng
    bị phát hiện.
    """
    payload: list[str] = []
    for order in sorted(orders, key=lambda o: o.order_id):
        for line in order.lines:
            parts = []
            for field in dataclasses.fields(line):
                if field.name == "raw":
                    continue
                parts.append(f"{field.name}={_plain(getattr(line, field.name))!r}")
            for field in dataclasses.fields(line.raw):
                if field.name in _DIGEST_SKIP_RAW:
                    continue
                parts.append(f"raw.{field.name}={_plain(getattr(line.raw, field.name))!r}")
            payload.append("\x1f".join(parts))
    blob = "\x1e".join(payload).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def covered_digest_fields(orders: list) -> dict:
    """Ghi lại CHÍNH tập trường đã đưa vào digest.

    Nếu một trường biến mất khỏi dataclass, so sánh chỉ ra ngay thay vì im
    lặng thu hẹp phạm vi canh gác.
    """
    line = orders[0].lines[0]
    return {
        "line": sorted(f.name for f in dataclasses.fields(line) if f.name != "raw"),
        "raw": sorted(
            f.name for f in dataclasses.fields(line.raw)
            if f.name not in _DIGEST_SKIP_RAW
        ),
    }


# ------------------------------------------------------------ build

def build_expected(spec: dict) -> dict:
    fixture = GOLDEN_DIR / spec["fixture_filename"]
    source = read_source_footer(fixture)
    result = run_import(fixture, CONFIG_DIR)

    orders = result.orders
    lines = [line for order in orders for line in order.lines]
    mapper = EmployeeMapper.from_yaml(CONFIG_DIR / "employees.yaml")

    delta_lines = [
        line for line in lines
        if line.total_sales is not None and line.raw.total_sales_raw is not None
        and line.total_sales != line.raw.total_sales_raw
    ]

    by_employee: dict[str, dict] = defaultdict(
        lambda: {"orders": 0, "lines": 0, "quantity": [], "sales_normalized": []}
    )
    for order in orders:
        key = order.employee_normalized or "<unmapped>"
        by_employee[key]["orders"] += 1
    for line in lines:
        key = line.employee_normalized or "<unmapped>"
        entry = by_employee[key]
        entry["lines"] += 1
        entry["quantity"].append(line.quantity)
        entry["sales_normalized"].append(line.total_sales)
    employees = {
        key: {
            "orders": value["orders"],
            "lines": value["lines"],
            "quantity": _dsum(value["quantity"]),
            "sales_normalized": _dsum(value["sales_normalized"]),
        }
        for key, value in sorted(by_employee.items())
    }

    review_items = sorted(
        [
            {
                "category": item.category,
                "severity": item.severity,
                "scope": item.scope,
                "order_id": item.order_id or None,
                "source_rows": list(item.provenance.source_rows),
            }
            for item in result.review_queue.items
        ],
        key=lambda i: (i["category"], i["severity"], i["scope"],
                       i["order_id"] or "", i["source_rows"]),
    )

    return {
        "_schema": {
            "expected_output_schema_version": SCHEMA_VERSION,
            "generator": "tests.fixtures.golden.build_expected",
        },
        "_provenance": {
            "baseline_id": spec["baseline_id"],
            "source_period": spec["period_label"],
            "source_workbook_label": spec["source_workbook_label"],
            "source_sha256": spec["source_sha256"],
            "source_type": "production_workbook",
            "anonymization_version": ANONYMIZATION_VERSION,
            "pipeline_entry_point": PIPELINE_ENTRY_POINT,
            "dataset_scope":
                "Tín Phát, một kỳ, xuất riêng theo tháng. KHÔNG phải dataset "
                "11.765 dòng của evidence.json, KHÔNG phải dataset 14.389 dòng "
                "của CHECK-108A1-15, KHÔNG phải dataset của CHECK-110-16.",
            "metric_anchors": dict(sorted(PROVENANCE_ANCHORS.items())),
        },
        "_environment": {
            "fixture_filename": spec["fixture_filename"],
            "config_snapshot_id": mapper.snapshot_id,
            "python": platform.python_version(),
            "openpyxl": openpyxl.__version__,
            "pyyaml": yaml.__version__,
        },
        "period": {
            "label": spec["period_label"],
            "date_min": min(line.date for line in lines).isoformat(),
            "date_max": max(line.date for line in lines).isoformat(),
        },
        "source_footer": source["footer"],
        "counts": {
            "sheet_data_rows": source["sheet_data_rows"],
            "rows_missing_order_id": source["rows_missing_order_id"],
            "raw_rows": len(lines),
            "orders": len(orders),
            "lines": len(lines),
            "lines_mapped": sum(
                1 for line in lines
                if line.employee_mapping_status == MAPPING_STATUS_MAPPED
            ),
            "lines_unmapped": len(result.unmapped_lines),
            "orders_with_multiple_employee_raw": sum(
                1 for order in orders if len({l.employee_raw for l in order.lines}) > 1
            ),
            "orders_with_multiple_lead_source": sum(
                1 for order in orders if len({l.lead_source_final for l in order.lines}) > 1
            ),
            "lines_per_order_distribution": {
                str(k): v
                for k, v in sorted(Counter(len(o.lines) for o in orders).items())
            },
        },
        "money": {
            "quantity_total": _dsum(line.quantity for line in lines),
            "sales_raw_gross": _dsum(line.raw.total_sales_raw for line in lines),
            "discount_total": _dsum(line.discount for line in lines),
            "sales_normalized": _dsum(line.total_sales for line in lines),
            "erp_profit_total": _dsum(line.raw.source_profit for line in lines),
            "delivery_cost_total": _dsum(line.delivery_cost for line in lines),
        },
        "discount_delta": {
            "lines_differing": len(delta_lines),
            "total_delta": str(
                sum((l.raw.total_sales_raw - l.total_sales for l in delta_lines),
                    Decimal(0))
            ),
            "every_delta_equals_that_line_discount": all(
                (l.raw.total_sales_raw - l.total_sales) == l.discount
                for l in delta_lines
            ),
        },
        "lead_source": {
            "orders_by_final": _counter(o.lead_source_final for o in orders),
            "orders_by_auto": _counter(o.lead_source_auto for o in orders),
            "orders_by_provenance": _counter(
                o.lead_source_source_of_value for o in orders
            ),
            "lines_by_final": _counter(l.lead_source_final for l in lines),
        },
        "conversion": {
            "scheme_distribution": _counter(
                f"{l.conversion_scheme_final}@{l.conversion_rate_final}" for l in lines
            ),
            "scheme_provenance": _counter(
                l.conversion_scheme_source_of_value for l in lines
            ),
            "product_group_distribution": _counter(l.product_group_final for l in lines),
            "product_group_provenance": _counter(
                l.product_group_source_of_value for l in lines
            ),
            "unresolved_lines": sum(
                1 for l in lines if l.conversion_rate_final is None
            ),
        },
        "pricing": {
            "price_source_distribution": _counter(l.price_source for l in lines),
            "accounting_profit_pending": sum(
                1 for l in lines if l.accounting_profit is None
            ),
        },
        "employees": employees,
        "review_queue": {
            "total_items": len(result.review_queue.items),
            "by_category": _counter(i.category for i in result.review_queue.items),
            "by_severity": _counter(i.severity for i in result.review_queue.items),
            "by_scope": _counter(i.scope for i in result.review_queue.items),
            "items": review_items,
        },
        "order_graph": {
            order.order_id: [line.raw.source_row for line in order.lines]
            for order in sorted(orders, key=lambda o: o.order_id)
        },
        "orders_detail": [
            {
                "order_id": order.order_id,
                "date": order.date.isoformat() if order.date else None,
                "employee_normalized": order.employee_normalized,
                "employee_group": order.employee_group,
                "lead_source_final": order.lead_source_final,
                "line_count": len(order.lines),
                "quantity": _dsum(l.quantity for l in order.lines),
                "sales_normalized": _dsum(l.total_sales for l in order.lines),
                "schemes": sorted({
                    f"{l.conversion_scheme_final}@{l.conversion_rate_final}"
                    for l in order.lines
                }),
            }
            for order in sorted(orders, key=lambda o: o.order_id)
        ],
        "lines_digest": lines_digest(orders),
        "_covered_digest_fields": covered_digest_fields(orders),
    }


def write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    for spec in PERIODS:
        payload = build_expected(spec)
        out = EXPECTED_DIR / f"{Path(spec['fixture_filename']).stem}.json"
        write(out, payload)
        print(f"{spec['period_label']} -> {out.relative_to(REPO_ROOT)} "
              f"({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
