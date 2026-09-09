"""R5 §5 — phạm vi CHÍNH XÁC của quyết định mở IMEI (`DEC-R5-03`).

Governance cũ cấm `imei` khỏi mọi query/UI của vertical nghiệp vụ. R5 mở nó
ra, và mở đúng một cánh cửa: bảng kê của tab nhân viên. Nhân viên cần đối
chiếu máy đã bán với máy trên phiếu, và không có mã máy thì họ phải mở sổ
Excel song song.

Một quyết định nới lỏng chỉ an toàn khi phạm vi của nó đọc được từ MÃ NGUỒN,
không từ một câu văn. Bộ này canh đúng điều đó, theo hai chiều:

    CẤU TRÚC   chỉ `server.py` import `workspace_imei`; `business_queries`,
               `business_metrics` và `business_store` vẫn không biết `imei`
               tồn tại.
    HÀNH VI    một mã máy có thật trong database KHÔNG xuất hiện trên bất kỳ
               trang nào khác, và không nằm trong file Excel xuất ra.

Chiều thứ hai là chiều thật sự quan trọng: hàng rào cấu trúc chặn lần thêm
cột tiếp theo, còn hàng rào hành vi chặn những đường rò đã tồn tại.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.web import business_service, business_store, history_store

from tests.test_employee_workspace_ux import SEPTEMBER, body, line, persist
from tests.test_r3_web_workflow import client  # noqa: F401

REPO_ROOT = Path(__file__).resolve().parents[1]
WEB = REPO_ROOT / "app" / "web"
IMEI_VALUE = "356938035643809"


@pytest.fixture
def engine():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


@pytest.fixture
def repository(engine):
    return history_store.SnapshotRepository(engine)


@pytest.fixture
def store(engine):
    return business_store.BusinessDecisionStore(engine)


@pytest.fixture
def service(engine, store):
    return business_service.BusinessReportService(engine=engine, store=store)


def with_imei(repository):
    source, result = line("BH1", "43F6000", day=5, sell="8000000")
    source = type(source)(**{
        **{f: getattr(source, f) for f in source.__dataclass_fields__},
        "imei": IMEI_VALUE,
    })
    persist(repository, [(source, result)])


def _imports(path: Path) -> set:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.update(f"{node.module}.{a.name}" for a in node.names)
        elif isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
    return names


# --- 1. Hàng rào CẤU TRÚC ------------------------------------------------

def test_only_the_web_server_opens_the_imei_door():
    """`workspace_imei` là cánh cửa DUY NHẤT, và chỉ một file mở nó."""
    openers = sorted(
        path.name for path in WEB.glob("*.py")
        if any("workspace_imei" in name for name in _imports(path)))
    assert openers == ["server.py"], openers


def test_the_shared_business_query_layer_still_does_not_know_about_imei():
    """Hàng rào cũ của `business_queries` KHÔNG được nới ra.

    Thêm `imei` vào `_COLUMNS` sẽ đưa nó vào MỌI trang dùng `PeriodData` —
    tổng hợp, cơ cấu, thương hiệu, đánh giá, export. Không trang nào hiện nó
    hôm nay, nhưng tất cả sẽ MANG nó, và trang tiếp theo ai đó viết sẽ có nó
    trong tay mà không phải xin phép ai.
    """
    for name in ("business_queries.py", "business_store.py"):
        tree = ast.parse((WEB / name).read_text(encoding="utf-8"))
        # Soi TÊN trong cây cú pháp, không soi văn bản: docstring của
        # `business_queries` nhắc `imei` để nói rằng nó KHÔNG đi qua đó, và
        # một phép thử theo văn bản sẽ đỏ vì đúng câu giải thích ấy.
        names = {node.attr for node in ast.walk(tree)
                 if isinstance(node, ast.Attribute)}
        names |= {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        names |= {node.value for node in ast.walk(tree)
                  if isinstance(node, ast.Constant) and isinstance(node.value, str)}
        assert "imei" not in names, name


# --- 2. Hàng rào HÀNH VI — trên một mã máy có thật ------------------------

def test_the_workspace_shows_the_imei(repository, client):
    html = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh") \
        if with_imei(repository) is None else ""
    assert IMEI_VALUE in html
    assert 'data-metric="line-imei"' in html


@pytest.mark.parametrize("path", [
    "/kinh-doanh?ky=2026-09",
    "/kinh-doanh/gia-nhap?ky=2026-09&tat-ca=1",
    "/kinh-doanh/thuong-hieu?ky=2026-09",
    "/kinh-doanh/co-cau?ky=2026-09",
    "/kinh-doanh/danh-gia?ky=2026-09",
    "/kinh-doanh/target?ky=2026-09",
    "/du-lieu",
])
def test_no_other_page_carries_the_imei(repository, client, path):
    with_imei(repository)
    response = client.get(path)
    assert response.status_code in (200, 302, 404), path
    assert IMEI_VALUE not in response.get_data(as_text=True), path


def test_the_excel_export_carries_no_imei(repository, service):
    with_imei(repository)
    data = service.period(**SEPTEMBER)
    workbook = service.export_workbook(data=data, period_label="09/2026")
    text = "\n".join(
        str(cell.value)
        for sheet in workbook.worksheets
        for row in sheet.iter_rows()
        for cell in row
        if cell.value is not None)
    assert IMEI_VALUE not in text


def test_the_snapshot_page_carries_no_imei(repository, client):
    """Trang đối chiếu mang `imei` trong `detail_json` DƯỚI database, nhưng
    `snapshot_presentation.NOISE_FIELDS` cắt nó ở tầng trình bày (R5 §2)."""
    with_imei(repository)
    snapshots = history_store.SnapshotRepository(
        repository._engine).list_snapshots()
    html = body(client, f"/du-lieu/snapshot/{snapshots[0]['snapshot_id']}")
    assert IMEI_VALUE not in html
