"""PHB-03 — bằng chứng CẤU TRÚC về các ranh giới, không phải bằng lời hứa.

Bốn ranh giới mà PHB-03 §3/§4/§9 đặt ra đều dễ bị bào mòn bởi một lần sửa
"tiện tay" sau này. Test ở đây đọc chính mã nguồn, nên chúng gãy ngay lần bào
mòn đầu tiên chứ không đợi tới lúc một con số sai lên màn hình.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
QUERY_MODULE = REPO_ROOT / "app/web/business_queries.py"
METRICS_MODULE = REPO_ROOT / "app/modules/reporting/business_metrics.py"
GATE_MODULE = REPO_ROOT / "app/modules/reporting/profit_gate.py"
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
    assert {"kpi_purchase_price_override", "product_group_classification",
            "employee_attribution_override"} <= names


def _imported_modules(path):
    tree = _tree(path)
    modules = {node.module for node in ast.walk(tree)
               if isinstance(node, ast.ImportFrom) and node.module}
    return modules | {alias.name for node in ast.walk(tree)
                      if isinstance(node, ast.Import) for alias in node.names}


@pytest.mark.parametrize("module", [METRICS_MODULE, GATE_MODULE])
def test_the_pure_business_modules_stay_pure(module):
    """`business_metrics` và `profit_gate` không được biết database/web/file.

    Toàn bộ mục 8 của PHB-03 là mệnh đề về NGỮ NGHĨA; giữ hai module này thuần
    là điều kiện để chúng kiểm được mà không dựng database hay browser.

    `app.modules.reporting` được phép ở đây, và CHỈ nó: đó là chính gói này,
    nơi `business_metrics` lấy `profit_gate` — hai module thuần cạnh nhau, chứ
    không phải một cánh cửa ra tầng hạ tầng.
    """
    allowed = {"__future__", "dataclasses", "decimal", "typing",
               "app.modules.reporting"}
    assert _imported_modules(module) <= allowed, _imported_modules(module)


def test_the_profit_gate_never_reads_the_pipeline_status_label():
    """`OD-6` — cửa chặn lợi nhuận KHÔNG được hỏi `status`.

    Đây là bất biến trung tâm của bản sửa PHB-03, và nó kiểm được bằng cấu
    trúc: `status` là kết quả cộng dồn 19 mã lý do rất khác nhau, nên bất kỳ
    lần đọc nào của nó trong `profit_gate` đều là một bước quay lại đúng cái
    cửa chặn tự quy chiếu mà bản audit đã gọi tên.
    """
    source = GATE_MODULE.read_text(encoding="utf-8")
    code = "\n".join(line for line in source.splitlines()
                      if not line.lstrip().startswith("#"))
    body = code.split('"""', 2)[-1]  # bỏ docstring module, nơi có giải thích
    # Tên trường `status` không được xuất hiện ở đâu trong phần mã.
    assert "status" not in body
    # Và hai GIÁ TRỊ của nó cũng không — dạng chuỗi nguyên vẹn. Mã lý do
    # `TRACKING_HISTORY_PENDING` không khớp: nó không phải chuỗi `"PENDING"`.
    for literal in ('"PENDING"', '"AUTO"'):
        assert literal not in body, literal


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
