"""PHB-07 — CƠ CẤU doanh thu theo ĐƠN VỊ BÁO CÁO: phân hoạch, tỉ trọng, đối soát.

Bốn lớp khẳng định, và thứ tự của chúng là cố ý:

1. **Ranh giới** — chứng minh bằng CHÍNH MÃ NGUỒN rằng tầng cơ cấu không có
   một công thức doanh thu/lợi nhuận nào của riêng nó, không dựng một phép
   phân loại đơn vị thứ hai, không mở một đường ghi nào và không thêm một
   bảng nào. Một test chỉ chạy hàm sẽ không bắt được một nhánh tính lại thêm
   vào ngày mai; một test đọc mã nguồn thì bắt được.
2. **Phân hoạch thuần** — chứng minh mọi chỉ tiêu cộng được của bảng cộng lại
   ĐÚNG BẰNG tổng kỳ, kể cả phần chưa xác định nhân viên, và tỉ trọng không
   bao giờ bịa ra một con số khi chưa có gì để chia.
3. **Vertical qua database** — chứng minh các bất biến trên đứng vững trước
   loại dòng, thiếu giá nhập, gán lại nhân viên và tick Gia dụng.
4. **Trang thật** — route sống, mặc định đúng tháng dương lịch hiện tại,
   không thêm mục điều hướng chính, không một đường ghi nào.

Cuối file là các MUTATION PROBE: mỗi probe cố ý làm hỏng đúng một tính chất
rồi khẳng định phép kiểm tương ứng THẤT BẠI. Không có chúng, một bộ test toàn
PASS không phân biệt được "bất biến đúng" với "bất biến chưa bao giờ được đo".
"""

from __future__ import annotations

import inspect
import io
import re
import tokenize
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.modules.reporting import business_metrics as bm
from app.modules.reporting import contribution as cb
from app.modules.reporting import reporting_sheets
from app.web import business_presentation, business_service, business_store
from app.web import history_store, legacy_presentation
from app.web import server as web_server
from tests.test_business_vertical import JANUARY, pair, persist
from tools.tracking import live_pull

REPO_ROOT = Path(__file__).resolve().parents[1]

PRIMARY_TABS = ["Báo cáo", "Nhân viên", "Dữ liệu"]


def executable_source(module) -> str:
    """Mã CHẠY của một module — mọi chuỗi và mọi comment đã bị bỏ.

    Quét thô cả file sẽ bắt nhầm chính phần văn xuôi đang GIẢI THÍCH điều bị
    cấm: `contribution` phải nói được vì sao nó không đọc giá bán. Cấm cả cách
    gọi tên sẽ làm tài liệu không viết được, nên phép quét đi qua `tokenize`
    và chỉ nhìn token thật. Cùng kỹ thuật `tests/test_phb06_brand_reporting.py`.
    """
    kept = []
    source = inspect.getsource(module)
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        kept.append(token.string)
    return " ".join(kept)


def route_source(name: str) -> str:
    """Mã nguồn của ĐÚNG một route trong `server.py`."""
    source = inspect.getsource(web_server)
    match = re.search(rf"\n    def {name}\(\):\n(.*?)(?=\n    @app\.)",
                      source, re.S)
    assert match is not None, f"không tìm thấy route {name}"
    return match.group(1)


def primary_tabs(html: str) -> list[str]:
    return [t.strip() for t in
            re.findall(r'class="ncc-tab[^"]*"[^>]*>([^<]+)</a>', html)]


def assert_three_primary_tabs(html: str) -> None:
    """`DEC-185` — thanh điều hướng chính có ĐÚNG BA mục."""
    assert primary_tabs(html) == PRIMARY_TABS


def analytics_write_names(names) -> list[str]:
    """Tên bảng/cột gợi ý một thẩm quyền GHI của tầng phân tích.

    PHB-07 là CHỈ ĐỌC: nó không lưu một kết quả phân tích nào, không có bảng
    quyết định riêng, không có ảnh chụp cơ cấu. Danh sách từ khoá được tách ra
    thành hàm để mutation probe gọi được đúng phép kiểm này trên một tên bịa.
    """
    keywords = ("composition", "co_cau", "cocau", "contribution", "share",
                "analytic")
    return sorted(n for n in names
                  if any(word in n.lower() for word in keywords))


# ==========================================================================
# 1. RANH GIỚI
# ==========================================================================

def test_the_composition_layer_never_recomputes_a_business_number():
    """`AN-01`/`AN-09` — tầng cơ cấu KHÔNG có công thức nghiệp vụ nào.

    Nó nhận `BusinessTotals` đã do `business_metrics` tính và chỉ cộng/chia
    những con số đó. Không một đại lượng ĐẦU VÀO của công thức lợi nhuận hay
    doanh thu được nhắc tới trong mã chạy, nên một phép tính lại không thể lọt
    vào đây mà không làm test này đỏ.
    """
    forbidden = ("sell_price", "purchase_price", "discount", "quantity",
                 "auto_kpi_profit", "manual_purchase_price",
                 "conversion_rate", "total_sales", "product_raw",
                 "eligible_kpi_profit")
    source = executable_source(cb)
    for name in forbidden:
        assert name not in source, name


def test_the_composition_layer_is_pure():
    """Không SQL, không Flask, không I/O, không sổ cũ — tầng gộp phải kiểm
    được mà không dựng database hay browser."""
    source = executable_source(cb)
    for name in ("sqlalchemy", "flask", "requests", "open", "legacy",
                 "business_queries", "business_store"):
        assert name not in source.lower(), name


def test_the_unit_partition_is_read_from_the_accepted_sheet_authority():
    """`AN-02` — KHÔNG có phép phân loại đơn vị thứ hai.

    Một dòng thuộc đơn vị nào là câu hỏi mà `reporting_sheets.sheet_key_of`
    đã trả lời cho không gian làm việc Nhân viên. `unit_for` chỉ ĐỌC câu trả
    lời đó: chữ ký của nó nhận sẵn một khoá sheet và không nhận nhóm nhân
    viên hay nhóm mặt hàng, nên nó KHÔNG THỂ tự quyết định.
    """
    parameters = list(inspect.signature(cb.unit_for).parameters)
    assert parameters == ["sheet_key", "employee"]
    source = executable_source(cb)
    assert "employee_group" not in source
    assert "product_group" not in source


def test_the_route_reads_the_official_period_and_the_accepted_assignments():
    """`AN-01` — đường production đọc ĐÚNG `service.period(...)` và ĐÚNG
    `sheet_assignments()`; nó không chạm dòng đã bị loại và không đọc sổ thô."""
    source = route_source("business_composition")
    assert "service.period" in source
    assert "data.sheet_assignments()" in source
    for forbidden in ("data.excluded", "raw_lines", "order_line_current",
                      "legacy"):
        assert forbidden not in source, forbidden


def test_phb07_adds_no_migration():
    """`AN-12` — `NEW_MIGRATION = NONE`. Thư mục version giữ nguyên 7 bản."""
    versions = sorted(
        p.name for p in (REPO_ROOT / "tools/db/migrations/versions").glob("*.py"))
    assert versions == [
        "0001_legacy.py", "0002_snapshots.py", "0003_business.py",
        "0004_employee_attribution.py", "0005_legacy_source_authority.py",
        "0006_employee_target.py", "0007_employee_workspace.py",
        # `0008_purchase_price_reason` là của R2 (`R2 Execution Brief` §4.4),
        # KHÔNG phải của vertical này. Nó có mặt trong danh sách vì phép
        # khẳng định ở đây là một phép PIN thư mục; điều nó chứng minh vẫn
        # nguyên vẹn — không có bản migration nào mang tên hay nội dung của
        # vertical này.
        "0008_purchase_price_reason.py",
        # `0009_line_binding_and_period_close` là của R3 (§1 gắn dòng, §5 chốt
        # kỳ) — cùng lý do như dòng trên: phép khẳng định ở đây PIN thư mục,
        # và điều nó chứng minh vẫn nguyên vẹn.
        "0009_line_binding_and_period_close.py",
    ]


def test_no_analytics_table_exists_anywhere_in_the_schema():
    """`AN-11` — không thẩm quyền ghi mới. Đọc chính metadata đang chạy.

    Phép quét nhìn TÊN BẢNG: một kết quả phân tích được lưu lại phải có một
    bảng để nằm vào. Cột `order_line_result_version.composition_rule` là của
    engine giá và đã có từ trước PHB-07 — test dưới đây khẳng định nó không
    bị đụng tới, thay vì chỉ tránh nhắc tới nó.
    """
    from tools.db import schema

    assert analytics_write_names(schema.METADATA.tables) == []
    assert "composition_rule" in schema.METADATA.tables[
        "order_line_result_version"].columns
    assert "composition_rule" not in executable_source(cb)


def test_no_employee_name_is_hard_coded_in_the_new_code_or_template():
    """§13 + PHB-05 CASE 10, mở rộng sang đúng hai file MỚI của PHB-07.

    CASE 10 canh danh sách module của PHB-05; hai file dưới đây ra đời sau nó
    và phải chịu cùng luật: thành phần của nhóm Nội thành nằm ở
    `config/employees.yaml` và CHỈ ở đó. Một cái tên viết cứng trong mã hay
    trong template là một thẩm quyền nhân sự thứ hai.

    Phần văn xuôi (docstring của Python, comment `{# … #}` của Jinja) được bỏ
    ra — cùng lý do `_code_constants` của PHB-05: một test đọc cả phần giải
    thích sẽ ép người viết sau này xoá đúng thứ nói vì sao cái tên không được
    viết cứng.
    """
    import ast

    from app.modules.mapping.employee_mapper import load_employee_master

    names = {record.normalized for record in load_employee_master(
        REPO_ROOT / "config" / "employees.yaml").records}
    assert names, "master nhân viên rỗng — test này sẽ không kiểm được gì"

    tree = ast.parse(
        (REPO_ROOT / "app/modules/reporting/contribution.py").read_text("utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
            first = node.body[0] if node.body else None
            if (isinstance(first, ast.Expr)
                    and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)):
                docstrings.add(id(first.value))
    constants = {node.value for node in ast.walk(tree)
                 if isinstance(node, ast.Constant) and id(node) not in docstrings}
    assert not constants & names

    markup = re.sub(
        r"\{#.*?#\}", "",
        (REPO_ROOT / "app/web/templates/kinh_doanh_co_cau.html")
        .read_text("utf-8"), flags=re.S)
    for name in names:
        assert name not in markup, name


def test_the_store_gains_no_write_method_for_the_composition_view():
    """Trang cơ cấu KHÔNG nhân bản một thẩm quyền ghi nào đã có."""
    methods = [m for m in dir(business_store.BusinessDecisionStore)
               if not m.startswith("_")]
    assert analytics_write_names(methods) == []


# ==========================================================================
# 2. PHÂN HOẠCH THUẦN
# ==========================================================================

def line(*, sales="1000", quantity="1", sell="2000000", profit="300000",
         order="BH1", employee="Vinh"):
    """Một `BusinessLine` dựng bằng tay — không cần database."""
    return bm.BusinessLine(
        order_key=order, employee=employee, employee_group=None,
        status="AUTO", sell_price=Decimal(sell), quantity=Decimal(quantity),
        discount=Decimal(0), total_sales=Decimal(sales),
        auto_purchase_price=Decimal("1000000"),
        auto_kpi_profit=None if profit is None else Decimal(profit),
        kpi_authority_valid=True, conversion_rate=Decimal("0.055"))


NOI_THANH = reporting_sheets.NOI_THANH_SHEET
GIA_DUNG = reporting_sheets.GIA_DUNG_SHEET
UNRESOLVED = reporting_sheets.UNRESOLVED_SHEET


def test_group_by_unit_is_a_partition_that_sums_back_to_the_period():
    """`AN-02`/`AN-03` — bốn chỉ tiêu cộng được cộng lại đúng bằng tổng kỳ."""
    lines = [line(sales="1000"), line(sales="3000"), line(sales="2000")]
    units = [cb.unit_for(NOI_THANH, None), cb.unit_for("nv:Ly", "Ly"),
             cb.unit_for(GIA_DUNG, None)]
    grouped = cb.group_by_unit(lines, units)

    assert len(grouped) == 3
    assert cb.reconciliation(grouped, bm.totals(lines)).is_exact


def test_the_three_noi_thanh_sellers_never_become_three_rows():
    """`AN-02` + §13 — Vinh · Quý · Hiệp KHÔNG bị đếm hai lần.

    Ba người bán của nhóm Nội thành cho ra ĐÚNG MỘT dòng "Nội thành". Đây là
    hệ quả của việc chỉ có MỘT phân hoạch, không phải một quy tắc phải nhớ.
    """
    lines = [line(sales="1000", employee="Vinh"),
             line(sales="2000", employee="Quý"),
             line(sales="3000", employee="Hiệp")]
    grouped = cb.group_by_unit(lines, [cb.unit_for(NOI_THANH, None)] * 3)

    assert [unit.label for unit, _ in grouped] == ["Nội thành"]
    assert grouped[0][1].sales_revenue == Decimal("6000")
    assert cb.reconciliation(grouped, bm.totals(lines)).is_exact


def test_the_unresolved_unit_keeps_its_money_and_stays_last():
    """`AN-05` — dòng chưa biết của ai KHÔNG biến mất, và luôn ở cuối bảng."""
    lines = [line(sales="1000"), line(sales="9000")]
    grouped = cb.group_by_unit(
        lines, [cb.unit_for(UNRESOLVED, None), cb.unit_for("nv:Ly", "Ly")])

    assert [unit.kind for unit, _ in grouped] == [
        cb.KIND_EMPLOYEE, cb.KIND_UNRESOLVED]
    assert grouped[-1][1].sales_revenue == Decimal("1000")
    assert cb.reconciliation(grouped, bm.totals(lines)).is_exact


def test_rows_are_sorted_by_revenue_without_any_ranking_label():
    """`TASK-PRA-005` §17 — sắp xếp là TRÌNH BÀY, không phải phân loại.

    Không nhãn `top`/`best`/`kém` nào tồn tại: mọi nhãn kiểu đó cần một công
    thức và một quyết định Owner chưa tồn tại.
    """
    lines = [line(sales="1000"), line(sales="5000"), line(sales="3000")]
    units = [cb.unit_for("nv:A", "A"), cb.unit_for("nv:B", "B"),
             cb.unit_for("nv:C", "C")]
    grouped = cb.group_by_unit(lines, units)

    assert [unit.label for unit, _ in grouped] == ["B", "C", "A"]
    source = executable_source(cb).lower()
    for word in ("top", "best", "worst", "rank", "score"):
        assert word not in source, word


def test_a_length_mismatch_is_a_hard_error_not_a_silent_truncation():
    with pytest.raises(ValueError):
        cb.group_by_unit([line(), line()], [cb.unit_for("nv:Ly", "Ly")])


def test_an_employee_sheet_without_a_name_is_refused():
    """Một khoá sheet nhân viên mà không có tên là mâu thuẫn nội tại — nó phải
    nổ ngay, chứ không thành một dòng nhãn rỗng cạnh các dòng thật."""
    with pytest.raises(ValueError):
        cb.unit_for("nv:", None)


def test_null_profit_never_becomes_zero_in_a_unit():
    """`AN-04` — thiếu giá nhập KHÔNG bao giờ thành lợi nhuận bằng không."""
    lines = [line(profit=None)]
    lines[0] = bm.BusinessLine(**{
        **{f: getattr(lines[0], f) for f in lines[0].__dataclass_fields__},
        "auto_purchase_price": None, "auto_kpi_profit": None,
    })
    grouped = cb.group_by_unit(lines, [cb.unit_for(NOI_THANH, None)])

    assert grouped[0][1].kpi_profit is None
    assert grouped[0][1].official_kpi_profit is None
    assert cb.reconciliation(grouped, bm.totals(lines)).is_exact


# --- Tỉ trọng --------------------------------------------------------------

def test_share_is_a_plain_ratio_of_two_official_numbers():
    assert cb.share_percent(Decimal("13000000"),
                            Decimal("45000000")) == Decimal("28.89")
    assert cb.share_percent(Decimal("45000000"),
                            Decimal("45000000")) == Decimal("100.00")


@pytest.mark.parametrize("part,whole", [
    (None, Decimal("1000")),      # đơn vị chưa có doanh thu nào
    (Decimal("1000"), None),      # kỳ chưa có doanh thu nào
    (Decimal("1000"), Decimal(0)),  # mẫu số 0 — không chia được
])
def test_share_says_nothing_instead_of_saying_zero(part, whole):
    """`AN-04` cùng tinh thần: "chưa nói được" KHÁC "bằng không"."""
    assert cb.share_percent(part, whole) is None
    assert business_presentation.share_cell(part, whole)["text"] == "—"
    assert business_presentation.share_cell(part, whole)["missing"] is True


def test_a_negative_share_is_shown_not_clamped():
    """Một đơn vị mà chiết khấu lớn hơn doanh số là sự thật kế toán."""
    assert cb.share_percent(Decimal("-500"), Decimal("1000")) == Decimal("-50")


def test_there_is_no_profit_share_anywhere(service):
    """`D1`/`N.7` — mẫu số của tỉ suất lợi nhuận chưa được Owner chốt, nên
    KHÔNG có cột nào như vậy và trang nói ra khoảng trống đó."""
    assert "Tỉ trọng doanh thu" in business_presentation.COMPOSITION_COLUMNS
    assert not [c for c in business_presentation.COMPOSITION_COLUMNS
                if "suất" in c or "Tỉ trọng lợi nhuận" in c]


# ==========================================================================
# 3. VERTICAL QUA DATABASE
# ==========================================================================

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


def composition_view(data):
    """Đúng ba bước mà route production chạy, không hơn."""
    units = [cb.unit_for(sheet_key, employee)
             for sheet_key, employee in data.sheet_assignments()]
    grouped = cb.group_by_unit(data.lines, units)
    return grouped, cb.reconciliation(grouped, data.totals)


def sales_by_unit(grouped) -> dict:
    return {unit.label: totals.sales_revenue for unit, totals in grouped}


def four_unit_period(repository, service):
    """Hai người của nhóm Nội thành, một dòng Gia dụng, một nhân viên bán lẻ.

    Doanh thu: Nội thành 13.000.000 · Gia dụng 12.000.000 · Ly 20.000.000
    ⟹ tổng kỳ 45.000.000.

    Dòng Gia dụng đi qua ĐÚNG đường production — quyết định phân loại của
    Owner (`set_line_product_group`), không phải một giá trị nhét sẵn vào
    `product_group_final`: `business_queries.effective_product_group` chỉ đọc
    hai bảng quyết định, nên một fixture nhét thẳng vào pipeline sẽ dựng một
    trạng thái không tồn tại trên sản phẩm thật.
    """
    persist(repository, [
        pair("BH1", employee="Vinh", group="NOI_THANH", sell="8000000"),
        pair("BH2", employee="Hiệp", group="NOI_THANH", sell="5000000",
             product="Tivi Sony"),
        pair("BH3", employee="Quý", group="NOI_THANH", sell="12000000",
             product="Bếp từ Bosch"),
        pair("BH4", employee="Ly", group="STANDARD_SALES", sell="20000000",
             product="Máy giặt LG"),
    ])
    gia_dung = next(d for d in service.period(**JANUARY).details
                    if d["order_key"] == "BH3")
    service.store.set_line_product_group(
        order_key=gia_dung["order_key"], product_key=gia_dung["product_key"],
        occurrence_index=gia_dung["occurrence_index"],
        product_group="GIA_DUNG")


def test_the_composition_reconciles_to_the_official_company_totals(
    repository, service
):
    """`AN-03` — phép đối soát CHẠY THẬT trên chính các con số đang hiện."""
    four_unit_period(repository, service)
    data = service.period(**JANUARY)
    grouped, recon = composition_view(data)

    assert sales_by_unit(grouped) == {
        "Ly": Decimal("20000000"),
        "Nội thành": Decimal("13000000"),
        "Gia dụng": Decimal("12000000"),
    }
    assert data.totals.sales_revenue == Decimal("45000000")
    assert recon.is_exact


def test_the_shares_of_the_period_add_up_to_the_whole(repository, service):
    four_unit_period(repository, service)
    data = service.period(**JANUARY)
    grouped, _recon = composition_view(data)
    whole = data.totals.sales_revenue

    shares = [cb.share_percent(totals.sales_revenue, whole)
              for _unit, totals in grouped]
    assert shares == [Decimal("44.44"), Decimal("28.89"), Decimal("26.67")]
    assert sum(shares) == Decimal("100.00")


def test_an_excluded_line_is_absent_from_every_unit(repository, service):
    """`AN-01` — dòng Owner đã loại không góp vào bất kỳ đơn vị nào."""
    four_unit_period(repository, service)
    detail = next(d for d in service.period(**JANUARY).details
                  if d["order_key"] == "BH4")
    service.store.exclude_line(
        order_key=detail["order_key"], product_key=detail["product_key"],
        occurrence_index=detail["occurrence_index"], reason="Trả hàng")

    data = service.period(**JANUARY)
    grouped, recon = composition_view(data)

    assert "Ly" not in sales_by_unit(grouped)
    assert data.totals.sales_revenue == Decimal("25000000")
    assert recon.is_exact


def test_a_line_without_a_purchase_price_keeps_its_unit_and_its_revenue(
    repository, service
):
    """`AN-04` — thiếu giá nhập làm mất LỢI NHUẬN, không làm mất DOANH THU."""
    persist(repository, [
        pair("BH1", employee="Ly", group="STANDARD_SALES",
             kpi_purchase=None, kpi_profit=None),
    ])
    data = service.period(**JANUARY)
    grouped, recon = composition_view(data)

    assert [unit.label for unit, _ in grouped] == ["Ly"]
    assert grouped[0][1].sales_revenue == Decimal("8000000")
    assert grouped[0][1].kpi_profit is None
    assert grouped[0][1].official_kpi_profit is None
    assert grouped[0][1].converted_sales is None
    assert recon.is_exact


def test_a_line_with_no_employee_gets_its_own_unit(repository, service):
    """`AN-05` — dòng chưa biết của ai vẫn nhìn thấy được, cùng tiền của nó."""
    persist(repository, [
        pair("BH1", employee="Ly", group="STANDARD_SALES", sell="6000000"),
        pair("BH2", employee=None, group=None, sell="4000000",
             product="Tivi Sony"),
    ])
    data = service.period(**JANUARY)
    grouped, recon = composition_view(data)

    unresolved = [item for item in grouped if not item[0].resolved]
    assert len(unresolved) == 1
    assert unresolved[0][1].sales_revenue == Decimal("4000000")
    assert recon.is_exact


def test_reassigning_an_employee_moves_the_line_and_keeps_the_period_whole(
    repository, service
):
    """`AN-06` — gán lại nhân viên ĐI QUA đúng phân hoạch đã nghiệm thu, và
    không làm đổi một đồng nào của tổng kỳ."""
    four_unit_period(repository, service)
    before = service.period(**JANUARY).totals.sales_revenue
    detail = next(d for d in service.period(**JANUARY).details
                  if d["order_key"] == "BH1")
    service.store.set_employee(
        order_key=detail["order_key"], product_key=detail["product_key"],
        occurrence_index=detail["occurrence_index"], employee="Ly",
        employee_group="STANDARD_SALES")

    data = service.period(**JANUARY)
    grouped, recon = composition_view(data)

    assert data.totals.sales_revenue == before
    assert sales_by_unit(grouped)["Ly"] == Decimal("28000000")
    assert sales_by_unit(grouped)["Nội thành"] == Decimal("5000000")
    assert recon.is_exact


def test_moving_a_line_to_gia_dung_moves_it_between_units_only(
    repository, service
):
    """`AN-07` — tick Gia dụng đổi ĐƠN VỊ của dòng (đúng như nó đổi tỉ lệ quy
    đổi), và KHÔNG đổi tổng doanh thu của kỳ."""
    four_unit_period(repository, service)
    before = service.period(**JANUARY).totals.sales_revenue
    detail = next(d for d in service.period(**JANUARY).details
                  if d["order_key"] == "BH1")
    service.store.set_line_product_group(
        order_key=detail["order_key"], product_key=detail["product_key"],
        occurrence_index=detail["occurrence_index"], product_group="GIA_DUNG")

    data = service.period(**JANUARY)
    grouped, recon = composition_view(data)

    assert data.totals.sales_revenue == before
    assert sales_by_unit(grouped)["Gia dụng"] == Decimal("20000000")
    assert sales_by_unit(grouped)["Nội thành"] == Decimal("5000000")
    assert recon.is_exact


def test_an_empty_period_reconciles_without_inventing_a_zero(service):
    """`AN-04` — kỳ rỗng: bảng rỗng, tỉ trọng `—`, không một số 0 bịa."""
    data = service.period(**JANUARY)
    grouped, recon = composition_view(data)

    assert grouped == []
    assert recon.is_exact
    rows = business_presentation.composition_rows(grouped, data.totals)
    assert len(rows) == 1 and rows[0]["total_row"]
    assert rows[0]["share"]["text"] == "—"


def test_the_unit_partition_matches_the_employee_workspace_tabs(
    repository, service
):
    """`AN-02` — bảng cơ cấu và hàng tab của không gian làm việc KHÔNG THỂ nói
    hai câu khác nhau: cả hai đọc cùng một `sheet_key_of`."""
    four_unit_period(repository, service)
    data = service.period(**JANUARY)
    grouped, _recon = composition_view(data)

    tab_keys = {sheet.key for sheet in service.sheets(data)}
    unit_keys = {unit.key for unit, _ in grouped}
    assert unit_keys <= tab_keys


# ==========================================================================
# 4. TRANG THẬT
# ==========================================================================

@pytest.fixture
def app(monkeypatch, tmp_path, engine, repository):
    legacy = history_store.build(engine=engine)
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "ARTIFACT_DIR", (tmp_path / "outputs").resolve())
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    application = web_server.create_app(db_path=tmp_path / "runs.db",
                                        history=legacy, snapshots=repository)
    application.testing = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def body(client, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200, f"{path} → {response.status_code}"
    return response.get_data(as_text=True)


def metric(html: str, name: str) -> str:
    match = re.search(rf'data-metric="{re.escape(name)}"[^>]*>(.*?)<', html, re.S)
    assert match is not None, f"không tìm thấy data-metric={name}"
    return match.group(1).strip()


def test_the_composition_page_renders(client, repository, service):
    four_unit_period(repository, service)
    html = body(client, "/kinh-doanh/co-cau?ky=2026-01")
    assert "CƠ CẤU DOANH THU" in html
    assert "Nội thành" in html and "Gia dụng" in html
    assert metric(html, "units") == "3"


def test_the_page_states_the_reconciliation_result_it_actually_measured(
    client, repository, service
):
    four_unit_period(repository, service)
    html = body(client, "/kinh-doanh/co-cau?ky=2026-01")
    assert 'data-reconciled="yes"' in html
    assert business_presentation.COMPOSITION_RECONCILED_NOTE in html


def test_the_page_shows_the_share_of_each_unit(client, repository, service):
    four_unit_period(repository, service)
    html = body(client, "/kinh-doanh/co-cau?ky=2026-01")
    shares = re.findall(r'data-metric="share"[^>]*>([^<]+)<', html)
    assert [s.strip() for s in shares] == ["44,44%", "28,89%", "26,67%", "100%"]


def test_the_composition_page_defaults_to_the_current_calendar_month(
    client, repository, monkeypatch, service
):
    monkeypatch.setattr(web_server, "_today", lambda: date(2026, 3, 17))
    four_unit_period(repository, service)  # dữ liệu nằm ở 01/2026
    html = body(client, "/kinh-doanh/co-cau")
    assert "Tháng 03/2026" in html
    assert 'value="2026-03"' in html


def test_the_month_can_still_be_selected(client, repository, service):
    four_unit_period(repository, service)
    html = body(client, "/kinh-doanh/co-cau?ky=2026-01")
    assert "Tháng 01/2026" in html
    assert metric(html, "lines") == "4"


def test_the_composition_page_has_no_toan_bo_du_lieu_option(
    client, repository, service
):
    four_unit_period(repository, service)
    html = body(client, "/kinh-doanh/co-cau?ky=2026-01")
    assert "Toàn bộ dữ liệu" not in html
    assert 'value="tat-ca"' not in html


def test_the_primary_navigation_is_unchanged(client, repository, service):
    """`AN-10` — thanh điều hướng chính vẫn ĐÚNG BA mục (`DEC-185`)."""
    four_unit_period(repository, service)
    for path in ("/kinh-doanh", "/kinh-doanh/co-cau", "/kinh-doanh/thuong-hieu"):
        assert_three_primary_tabs(body(client, path))


def test_the_composition_page_is_reachable_from_bao_cao(
    client, repository, service
):
    """§6 — một khung nhìn con của Báo cáo, không một tab mới."""
    four_unit_period(repository, service)
    assert "/kinh-doanh/co-cau" in body(client, "/kinh-doanh")


def test_the_composition_page_offers_no_write_surface(
    client, repository, service
):
    """`AN-11` — khung nhìn CHỈ ĐỌC: không form ghi, không ô nhập nào."""
    four_unit_period(repository, service)
    html = body(client, "/kinh-doanh/co-cau?ky=2026-01")

    assert 'method="post"' not in html.lower()
    assert html.lower().count("<form") == 1
    assert 'method="get"' in html.lower()
    assert "<input" not in html.split("Bảng cơ cấu", 1)[1]


def test_the_composition_page_carries_no_legacy_series(
    client, repository, service
):
    """`AN-08` — bảng là ảnh chụp của MỘT kỳ, một nguồn (`DEC-180` §9).

    Không bộ chọn nguồn, không nhãn số cũ, không chuỗi nhiều tháng — và trang
    nói ra điều đó thay vì để người đọc tự đoán.
    """
    four_unit_period(repository, service)
    html = body(client, "/kinh-doanh/co-cau?ky=2026-01")

    assert legacy_presentation.ORIGIN_BADGE not in html
    assert "LEGACY" not in html
    assert business_presentation.COMPOSITION_ONE_PERIOD_NOTE in html


def test_the_page_says_plainly_that_there_is_no_profit_ratio(
    client, repository, service
):
    four_unit_period(repository, service)
    html = body(client, "/kinh-doanh/co-cau?ky=2026-01")
    assert business_presentation.COMPOSITION_NO_PROFIT_SHARE_NOTE in html


def test_the_page_says_that_noi_thanh_is_one_reporting_unit(
    client, repository, service
):
    """§13 — người đọc phải biết Nội thành gộp cả nhóm trước khi đi tìm dòng
    của Vinh và kết luận rằng bảng thiếu."""
    four_unit_period(repository, service)
    html = body(client, "/kinh-doanh/co-cau?ky=2026-01")
    assert business_presentation.COMPOSITION_UNIT_NOTE in html
    assert "Vinh" not in html and "Hiệp" not in html


def test_the_page_shows_no_engineering_identifier(client, repository, service):
    """§22 — không rò rỉ enum nội bộ ra màn hình."""
    four_unit_period(repository, service)
    html = body(client, "/kinh-doanh/co-cau?ky=2026-01")
    labels = re.findall(r'data-metric="unit-label"[^>]*>([^<]+)<', html)
    for label in labels:
        assert "nv:" not in label
        assert label.strip() not in {"NOI_THANH", "GIA_DUNG", "STANDARD_SALES"}


def test_the_business_summary_still_renders_after_phb07(
    client, repository, service
):
    """`AN-01` — trang BÁO CÁO và trang cơ cấu nói CÙNG một doanh thu kỳ."""
    four_unit_period(repository, service)
    summary = body(client, "/kinh-doanh?ky=2026-01")
    composition = body(client, "/kinh-doanh/co-cau?ky=2026-01")
    assert (metric(summary, "sales_revenue")
            == metric(composition, "period-sales-revenue"))


# ==========================================================================
# 5. MUTATION PROBES (§26)
# ==========================================================================
#
# Mỗi probe làm hỏng ĐÚNG MỘT tính chất rồi khẳng định phép kiểm tương ứng
# THẤT BẠI. Chúng chạy trên chính các hàm production — không có bản sao nào
# của phép gộp ở đây.

def test_M1_using_the_raw_book_instead_of_the_official_result_breaks_totals(
    repository, service
):
    """M1 — gộp trên sổ THÔ (gồm cả dòng đã loại) thay vì kết quả chính thức."""
    four_unit_period(repository, service)
    detail = next(d for d in service.period(**JANUARY).details
                  if d["order_key"] == "BH4")
    service.store.exclude_line(
        order_key=detail["order_key"], product_key=detail["product_key"],
        occurrence_index=detail["occurrence_index"], reason="Trả hàng")

    data = service.period(**JANUARY)
    raw_lines = [*data.lines, *(d["line"] for d in data.excluded)]
    raw_units = [
        *[cb.unit_for(k, e) for k, e in data.sheet_assignments()],
        *[cb.unit_for("nv:Ly", "Ly") for _ in data.excluded],
    ]
    mutated = cb.group_by_unit(raw_lines, raw_units)

    assert cb.reconciliation(mutated, data.totals).sales_revenue is False


def test_M2_letting_an_excluded_line_contribute_breaks_reconciliation(
    repository, service
):
    """M2 — cùng lỗi, nhìn từ phía một dòng bị loại được cộng trở lại."""
    four_unit_period(repository, service)
    detail = next(d for d in service.period(**JANUARY).details
                  if d["order_key"] == "BH1")
    service.store.exclude_line(
        order_key=detail["order_key"], product_key=detail["product_key"],
        occurrence_index=detail["occurrence_index"], reason="Trả hàng")

    data = service.period(**JANUARY)
    grouped, recon = composition_view(data)
    assert recon.is_exact  # đường thật vẫn đúng

    excluded_line = data.excluded[0]["line"]
    mutated = cb.group_by_unit(
        [*data.lines, excluded_line],
        [*[cb.unit_for(k, e) for k, e in data.sheet_assignments()],
         cb.unit_for(NOI_THANH, None)])
    assert cb.reconciliation(mutated, data.totals).sales_revenue is False


def test_M3_fabricating_a_zero_profit_for_a_missing_price_line_is_visible(
    repository, service
):
    """M3 — biến `None` thành `0` làm phép đối soát đỏ ngay."""
    persist(repository, [
        pair("BH1", employee="Ly", group="STANDARD_SALES",
             kpi_purchase=None, kpi_profit=None),
    ])
    data = service.period(**JANUARY)
    grouped, recon = composition_view(data)
    assert recon.is_exact
    assert grouped[0][1].kpi_profit is None

    unit, totals = grouped[0]
    mutated = [(unit, bm.BusinessTotals(**{
        **{f: getattr(totals, f) for f in totals.__dataclass_fields__},
        "kpi_profit": Decimal(0),
    }))]
    assert cb.reconciliation(mutated, data.totals).kpi_profit is False


def test_M4_dropping_the_unresolved_unit_breaks_reconciliation():
    """M4 — bỏ dòng "chưa xác định nhân viên" khỏi bảng."""
    lines = [line(sales="1000"), line(sales="3000")]
    grouped = cb.group_by_unit(
        lines, [cb.unit_for("nv:Ly", "Ly"), cb.unit_for(UNRESOLVED, None)])
    mutated = [item for item in grouped if item[0].resolved]

    assert cb.reconciliation(mutated, bm.totals(lines)).sales_revenue is False


def test_M5_duplicating_one_line_into_two_units_breaks_reconciliation():
    """M5 — đúng lỗi "Nội thành CỘNG THÊM Vinh/Quý/Hiệp"."""
    lines = [line(sales="1000")]
    company = bm.totals(lines)
    mutated = cb.group_by_unit(
        [*lines, *lines],
        [cb.unit_for(NOI_THANH, None), cb.unit_for("nv:Vinh", "Vinh")])
    recon = cb.reconciliation(mutated, company)

    assert recon.sales_revenue is False
    assert recon.lines is False


def test_M6_introducing_a_business_formula_breaks_the_authority_scan():
    """M6 — một công thức nghiệp vụ trong tầng cơ cấu làm phép quét đỏ ngay."""
    forbidden = ("sell_price", "purchase_price", "discount", "quantity")
    source = executable_source(cb)
    assert all(name not in source for name in forbidden)

    mutated = source + " def margin ( self ) : return self . sell_price * 2 "
    assert any(name in mutated for name in forbidden)


def test_M7_adding_a_primary_nav_item_breaks_the_navigation_test():
    """M7 — một mục điều hướng chính thứ tư làm `AN-10` đỏ ngay."""
    good = ('<a class="ncc-tab on">Báo cáo</a><a class="ncc-tab">Nhân viên</a>'
            '<a class="ncc-tab">Dữ liệu</a>')
    assert_three_primary_tabs(good)

    mutated = good + '<a class="ncc-tab">Phân tích</a>'
    with pytest.raises(AssertionError):
        assert_three_primary_tabs(mutated)


def test_M8_introducing_an_analytics_write_table_breaks_the_scope_test():
    """M8 — một bảng lưu kết quả phân tích làm `AN-11` đỏ ngay."""
    from tools.db import schema

    names = [t.name for t in schema.METADATA.tables.values()]
    assert analytics_write_names(names) == []
    assert analytics_write_names([*names, "composition_snapshot"]) == [
        "composition_snapshot"]


def test_M9_computing_the_share_against_the_known_units_only_breaks_the_whole(
    repository, service
):
    """M9 (capability-specific) — mẫu số bỏ qua phần "chưa xác định" làm tổng
    tỉ trọng vượt 100 %, tức là nói dối về cơ cấu."""
    persist(repository, [
        pair("BH1", employee="Ly", group="STANDARD_SALES", sell="6000000"),
        pair("BH2", employee=None, group=None, sell="4000000",
             product="Tivi Sony"),
    ])
    data = service.period(**JANUARY)
    grouped, _recon = composition_view(data)

    honest = [cb.share_percent(t.sales_revenue, data.totals.sales_revenue)
              for _u, t in grouped]
    assert sum(honest) == Decimal("100.00")

    known_only = sum((t.sales_revenue for u, t in grouped if u.resolved),
                     Decimal(0))
    mutated = [cb.share_percent(t.sales_revenue, known_only)
               for _u, t in grouped]
    assert sum(mutated) > Decimal("100.00")


def test_M10_splitting_noi_thanh_into_its_three_sellers_double_counts(
    repository, service
):
    """M10 (capability-specific) — thay phân hoạch đơn vị bằng phân hoạch NGƯỜI
    rồi để cả hai cùng có mặt: đúng lỗi đếm hai lần mà §13 cấm."""
    four_unit_period(repository, service)
    data = service.period(**JANUARY)
    grouped, recon = composition_view(data)
    assert recon.is_exact

    by_person = cb.group_by_unit(
        data.lines,
        [cb.unit_for(f"nv:{ln.employee}", ln.employee) for ln in data.lines])
    mutated = [*grouped, *by_person]

    assert cb.reconciliation(mutated, data.totals).sales_revenue is False
