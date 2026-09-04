"""PHB-03 — bằng chứng CẤU TRÚC về các ranh giới, không phải bằng lời hứa.

Bốn ranh giới mà PHB-03 §3/§4/§9 đặt ra đều dễ bị bào mòn bởi một lần sửa
"tiện tay" sau này. Test ở đây đọc chính mã nguồn, nên chúng gãy ngay lần bào
mòn đầu tiên chứ không đợi tới lúc một con số sai lên màn hình.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
QUERY_MODULE = REPO_ROOT / "app/web/business_queries.py"
METRICS_MODULE = REPO_ROOT / "app/modules/reporting/business_metrics.py"
STORE_MODULE = REPO_ROOT / "app/web/business_store.py"


def _tree(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"))


def _names(tree: ast.AST) -> set[str]:
    names = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    names |= {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    names |= {alias.name for node in ast.walk(tree)
              if isinstance(node, ast.ImportFrom) for alias in node.names}
    return names


def test_the_business_query_layer_has_no_way_to_write():
    """Cùng bằng chứng cấu trúc mà PRA-003/PRA-004 đã dùng.

    Không import được `insert`/`update`/`delete`/`text` thì không dựng được
    câu ghi nào; không `begin()`/`commit()` thì kể cả SQL thô cũng không bao
    giờ được commit (SQLAlchemy 2.0 không autocommit).
    """
    tree = _tree(QUERY_MODULE)
    imported = {alias.name for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) for alias in node.names}
    assert imported.isdisjoint({"insert", "update", "delete", "text"})
    called = {node.func.attr for node in ast.walk(tree)
              if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    assert called.isdisjoint({"begin", "commit", "execution_options"})
    assert "connect" in called, "tầng này chỉ mở kết nối CHỈ-ĐỌC"


def test_the_business_query_layer_never_sums_a_run_summary():
    """Cộng `summary_json` qua các run chính là double-count mà PRA-002 sinh
    ra để chống."""
    names = _names(_tree(QUERY_MODULE))
    assert "summary_json" not in names
    assert "source_snapshot" not in names


def test_no_business_module_reads_a_personal_data_column():
    """Hàng rào PII, canh bằng chính mã nguồn.

    `product_raw` CỐ Ý nằm ngoài hàng rào (lý do ở docstring của
    `business_queries`, cùng lý do đã nghiệm thu ở PRA-004). Ba cột còn lại là
    dữ liệu cá nhân và không có đường nào ra tới một trang chỉ tiêu.
    """
    for module in (QUERY_MODULE, METRICS_MODULE, STORE_MODULE):
        names = _names(_tree(module))
        for column in ("imei", "note_raw", "employee_raw"):
            assert column not in names, f"{module.name} đọc {column}"


def test_the_business_write_layer_never_touches_the_append_only_fact_tables():
    """`order_line_result_version` là bằng chứng kế toán của MỘT lần chạy.

    Ghi đè nó bằng một giá trị do người nhập sẽ xoá dấu vết "engine đã tính ra
    gì" và biến một input của con người thành một output của máy. Đường ghi
    của PHB-03 vì vậy chỉ được chạm đúng hai bảng của chính nó.
    """
    names = _names(_tree(STORE_MODULE))
    forbidden = {
        "order_line_result_version", "order_line_source_version",
        "order_line_current", "source_snapshot", "snapshot_line",
        "reconciliation_flag", "legacy_summary_row",
    }
    assert names.isdisjoint(forbidden), sorted(names & forbidden)
    assert {"kpi_purchase_price_override", "product_group_classification"} <= names


def test_the_pure_metrics_module_stays_pure():
    """`business_metrics` không được biết database, web hay filesystem.

    Toàn bộ mục 8 của PHB-03 là mệnh đề về NGỮ NGHĨA; giữ module này thuần là
    điều kiện để chúng kiểm được mà không dựng database hay browser.
    """
    tree = _tree(METRICS_MODULE)
    modules = {node.module for node in ast.walk(tree)
               if isinstance(node, ast.ImportFrom) and node.module}
    modules |= {alias.name for node in ast.walk(tree)
                if isinstance(node, ast.Import) for alias in node.names}
    assert modules <= {"__future__", "dataclasses", "decimal", "typing"}, modules


def test_the_conversion_rate_table_is_the_only_source_of_rates():
    """Không có tỉ lệ nào viết cứng trong mã PHB-03.

    `DEC-PHB02-05` liệt kê bốn tỉ lệ; nếu chúng xuất hiện dưới dạng hằng số
    trong mã, dự án sẽ có hai bảng tỉ lệ và một ngày nào đó chúng lệch nhau.
    Chúng chỉ được sống ở `config/conversion_rates.yaml`.
    """
    for path in (QUERY_MODULE, METRICS_MODULE, STORE_MODULE,
                 REPO_ROOT / "app/modules/reporting/rate_routing.py",
                 REPO_ROOT / "app/web/business_service.py",
                 REPO_ROOT / "app/web/business_presentation.py"):
        source = path.read_text(encoding="utf-8")
        code = "\n".join(
            line for line in source.splitlines()
            if not line.lstrip().startswith("#")
        )
        for rate in ("0.075", "0.055", "0.080", "0.020"):
            assert rate not in code, f"{path.name} viết cứng tỉ lệ {rate}"
