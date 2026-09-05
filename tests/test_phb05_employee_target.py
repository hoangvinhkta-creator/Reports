"""PHB-05 — Target tháng của nhân viên (`DEC-PHB02-06`), đi hết vertical.

`DEC-PHB02-06` đã freeze ở PHB-02: Target là số Owner tự đặt cho từng nhân
viên, sửa được, và KHÔNG được viết cứng. File này chứng minh khẳng định đó
sống sót qua database, qua tầng ráp, và qua HTML thật — không chỉ qua giá trị
thuần.

## Công thức, đọc từ sổ chứ không đoán từ tên cột

`Summary 2026!N4 = IFERROR(F4/M4,"")`, trong đó `F` là **Doanh thu quy đổi**
(`F4 = G4/5.5%`) và `M` là Target — `docs/analysis/02_FORMULA_MAPPING.md` §3
và `docs/analysis/03_RULE_CLASSIFICATION.md` (`PercentTarget =
TotalConvertedRevenue / Target` ⟷ `N = F/M`). Vì vậy:

    So target = DS quy đổi / Target × 100

`IFERROR(...,"")` là chỗ sổ cũ nói ra cách xử lý Target rỗng/bằng 0: để
TRỐNG, không viết `0 %`, và không cap ở `100 %`.

## Bất biến trung tâm

Target ĐỌC kết quả báo cáo. Target KHÔNG làm đổi kết quả báo cáo. Bằng chứng
mạnh nhất trong file này là dấu vân tay tổng hợp trước/sau một lần đổi Target
(`test_case_14_*`): mọi chỉ tiêu nghiệp vụ giữ nguyên từng chữ số.
"""

from __future__ import annotations

import ast
import re
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.modules.reporting import business_metrics as bm
from app.web import business_presentation, business_service, business_store
from app.web import history_store
from app.web import server as web_server
from tests.test_business_vertical import pair, persist
from tools.tracking import live_pull

REPO_ROOT = Path(__file__).resolve().parents[1]


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


@pytest.fixture
def app(monkeypatch, tmp_path, engine, repository):
    legacy = history_store.build(engine=engine)
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "ARTIFACT_DIR", (tmp_path / "outputs").resolve())
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    application = web_server.create_app(db_path=tmp_path / "runs.db", history=legacy,
                                        snapshots=repository)
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


def row_of(html: str, employee: str) -> str:
    """Đúng MỘT dòng `<tr>` của bảng Target, để hai nhân viên không lẫn nhau."""
    match = re.search(
        rf'<tr data-metric="target-row" data-employee="{re.escape(employee)}">(.*?)</tr>',
        html, re.S)
    assert match is not None, f"không tìm thấy dòng Target của {employee!r}"
    return match.group(1)


def save_target(client, *, period: str, employee: str, value: str):
    return client.post("/kinh-doanh/target", data={
        "ky": period, "nhan_vien": employee, "target": value})


# Một nhân viên bán lẻ với đủ dữ liệu để DS quy đổi ra một con số TRÒN, để mọi
# vector "So target" dưới đây đọc được bằng mắt:
#     lợi nhuận KPI 13.750.000 / 5,5 % = 250.000.000 VND DS quy đổi.
def selling(order, *, employee="Ly", month=1, **kwargs):
    kwargs.setdefault("kpi_purchase", "5000000")
    kwargs.setdefault("kpi_profit", "13750000")
    return pair(order, employee=employee, group="STANDARD_SALES", rate="0.055",
                month=month, **kwargs)


CONVERTED_250M = Decimal("250000000")


# --- CASE 1/2/3 — Target là của MỘT người trong MỘT tháng -------------------

def test_case_1_a_target_persists_and_shows_up_on_the_page(repository, client):
    """CASE 1 — đặt Target 500m cho tháng 9 ⟹ lưu lại và hiện ra."""
    persist(repository, [selling("BH1", month=9)])
    save_target(client, period="2026-09", employee="Ly", value="500000000")
    row = row_of(body(client, "/kinh-doanh/target?ky=2026-09"), "Ly")
    assert metric(row, "target-value") == "500.000"  # nghìn đồng
    assert "500.000.000 đồng" in row  # số VND đầy đủ không bao giờ mất


def test_case_2_two_employees_in_one_month_keep_separate_targets(
    repository, client
):
    """CASE 2 — Target của người này không phải Target của người kia."""
    persist(repository, [
        selling("BH1", employee="Ly", month=9),
        selling("BH2", employee="Hiệp", month=9, row=7),
    ])
    save_target(client, period="2026-09", employee="Ly", value="500000000")
    save_target(client, period="2026-09", employee="Hiệp", value="400000000")
    html = body(client, "/kinh-doanh/target?ky=2026-09")
    assert metric(row_of(html, "Ly"), "target-value") == "500.000"
    assert metric(row_of(html, "Hiệp"), "target-value") == "400.000"


def test_case_3_one_employee_keeps_a_different_target_in_each_month(
    repository, client, service
):
    """CASE 3 — sửa Target 09/2026 KHÔNG đụng tới 08/2026.

    Đây là điều `PHB-05` §4 gọi tên: Target khoá theo kỳ báo cáo, nên hai
    tháng là hai dòng độc lập trong database.
    """
    persist(repository, [
        selling("BH8", month=8),
        selling("BH9", month=9, row=7),
    ])
    save_target(client, period="2026-08", employee="Ly", value="400000000")
    save_target(client, period="2026-09", employee="Ly", value="500000000")
    assert service.employee_targets((2026, 8)) == {"Ly": Decimal("400000000")}
    assert service.employee_targets((2026, 9)) == {"Ly": Decimal("500000000")}

    # Sửa tháng 9 lần nữa: tháng 8 vẫn y nguyên.
    save_target(client, period="2026-09", employee="Ly", value="600000000")
    assert service.employee_targets((2026, 8)) == {"Ly": Decimal("400000000")}
    assert service.employee_targets((2026, 9)) == {"Ly": Decimal("600000000")}


# --- CASE 4/15 — Target KHÔNG thuộc về một snapshot ------------------------

def test_case_4_a_new_snapshot_never_touches_a_target(
    repository, client, service
):
    """CASE 4 — nạp lại sổ kế toán, Target của Owner còn nguyên.

    Đây là điểm tới hạn của PHB-05 (§11): một snapshot mới dựng ra version
    mới, `id` mới, dòng mới — và không được sở hữu quyết định của Owner. Khoá
    `(năm, tháng, nhân viên)` không chứa `snapshot_id` nào, nên đường làm mất
    Target không tồn tại.
    """
    persist(repository, [selling("BH1", month=9)])
    save_target(client, period="2026-09", employee="Ly", value="500000000")
    before = metric(body(client, "/kinh-doanh/target?ky=2026-09"), "target-vs")

    # Snapshot THỨ HAI của cùng kỳ, giá bán đổi ⟹ số liệu kỳ đổi.
    persist(repository, [selling("BH1", month=9, sell="9000000")],
            run_id="run-2", at="2026-10-01T00:00:00", fingerprint="fp-b")

    assert service.employee_targets((2026, 9)) == {"Ly": Decimal("500000000")}
    row = row_of(body(client, "/kinh-doanh/target?ky=2026-09"), "Ly")
    assert metric(row, "target-value") == "500.000"
    assert metric(row, "target-vs") == before  # DS quy đổi không đổi ⟹ % không đổi


def test_case_15_a_target_never_enters_the_snapshot_lifecycle(repository, store):
    """CASE 15 — không bảng nào của vòng đời snapshot mang Target.

    Bằng chứng CẤU TRÚC, không phải bằng quan sát: nếu `employee_target` có
    một cột trỏ tới snapshot/version thì lời hứa của CASE 4 chỉ còn là may
    mắn.
    """
    from tools.db import schema

    columns = set(schema.employee_target.c.keys())
    assert columns == {"year", "month", "employee_key", "origin", "target_vnd",
                       "updated_at", "updated_by"}
    assert not schema.employee_target.foreign_keys
    for lifecycle in ("snapshot_id", "version_id", "run_id", "import_id",
                      "order_key", "product_key"):
        assert lifecycle not in columns


# --- CASE 5/6/7/8/9 — ngữ nghĩa ghi ---------------------------------------

def test_case_5_editing_a_target_recomputes_so_target_immediately(
    repository, client
):
    """CASE 5 — 500m → 600m đổi ngay "So target", không cần chạy lại gì."""
    persist(repository, [selling("BH1", month=9)])
    save_target(client, period="2026-09", employee="Ly", value="500000000")
    assert metric(row_of(body(client, "/kinh-doanh/target?ky=2026-09"), "Ly"),
                  "target-vs") == "50%"
    save_target(client, period="2026-09", employee="Ly", value="600000000")
    # 250.000.000 / 600.000.000 = 41,67 %
    assert metric(row_of(body(client, "/kinh-doanh/target?ky=2026-09"), "Ly"),
                  "target-vs") == "41,67%"


def test_case_6_a_blank_input_clears_the_target(repository, client, service):
    """CASE 6 — để trống ô rồi LƯU ⟹ GỠ target, So target về N/A."""
    persist(repository, [selling("BH1", month=9)])
    save_target(client, period="2026-09", employee="Ly", value="500000000")
    save_target(client, period="2026-09", employee="Ly", value="")

    assert service.employee_targets((2026, 9)) == {}  # không còn DÒNG nào
    row = row_of(body(client, "/kinh-doanh/target?ky=2026-09"), "Ly")
    assert metric(row, "target-value") == business_presentation.TARGET_UNSET_LABEL
    assert metric(row, "target-vs") == "—"
    assert 'data-reason="TARGET_UNSET"' in row


def test_case_7_a_zero_target_is_stored_and_is_not_the_same_as_blank(
    repository, client, service
):
    """CASE 7 — `0` được LƯU như một quyết định, KHÔNG bị đọc thành rỗng.

    Hai trạng thái cho ra cùng `So target = N/A`, nhưng cho ra hai CÂU khác
    nhau và hai trạng thái khác nhau trong dữ liệu. Trộn chúng lại là mất khả
    năng phân biệt "đã quyết" với "chưa quyết" (PHB-05 §7).
    """
    persist(repository, [selling("BH1", month=9)])
    save_target(client, period="2026-09", employee="Ly", value="0")

    assert service.employee_targets((2026, 9)) == {"Ly": Decimal("0")}
    row = row_of(body(client, "/kinh-doanh/target?ky=2026-09"), "Ly")
    assert metric(row, "target-value") == "0"
    assert metric(row, "target-value") != business_presentation.TARGET_UNSET_LABEL
    assert metric(row, "target-vs") == "—"
    assert 'data-reason="TARGET_ZERO"' in row
    # Và hai lý do KHÔNG dùng chung một câu.
    assert (business_presentation.TARGET_REASON_LABELS[bm.TARGET_ZERO]
            != business_presentation.TARGET_REASON_LABELS[bm.TARGET_UNSET])


def test_case_8_a_negative_target_is_rejected(repository, client, service):
    """CASE 8 — Target âm bị TỪ CHỐI, và không có dòng nào được ghi."""
    persist(repository, [selling("BH1", month=9)])
    save_target(client, period="2026-09", employee="Ly", value="-1")
    assert service.employee_targets((2026, 9)) == {}
    html = body(client, "/kinh-doanh/target?ky=2026-09&loi=Target+kh%C3%B4ng+"
                        "%C4%91%C6%B0%E1%BB%A3c+%C3%A2m.")
    assert "không được âm" in metric(html, "target-error")
    with pytest.raises(business_store.InvalidTargetError):
        business_store.parse_target("-1")


def test_case_9_invalid_text_is_rejected(repository, client, service):
    """CASE 9 — chữ không phải số bị TỪ CHỐI, không đoán hộ thành 0."""
    persist(repository, [selling("BH1", month=9)])
    save_target(client, period="2026-09", employee="Ly", value="năm trăm triệu")
    assert service.employee_targets((2026, 9)) == {}
    with pytest.raises(business_store.InvalidTargetError):
        business_store.parse_target("năm trăm triệu")


def test_a_target_can_only_be_set_for_a_real_employee_and_a_real_month(
    repository, client, service
):
    """Hai ranh giới còn lại của đường ghi, kiểm bằng POST dựng tay.

    Tên lạ ⟹ từ chối (cùng thẩm quyền master mà `OD-5` dùng); không có kỳ
    (`tat-ca`) ⟹ 404, vì không có tháng nào để ghi vào và đoán hộ một tháng
    là ghi vào tháng sai.
    """
    persist(repository, [selling("BH1", month=9)])
    save_target(client, period="2026-09", employee="Người Lạ", value="500000000")
    assert service.employee_targets((2026, 9)) == {}

    response = save_target(client, period="tat-ca", employee="Ly",
                           value="500000000")
    assert response.status_code == 404
    assert service.employee_targets((2026, 9)) == {}


# --- CASE 10 — không hard-code ---------------------------------------------

# Các con số Target THẬT của sổ cũ (`docs/analysis/04_HARDCODED_VALUES.md` §3).
# Chúng là BẰNG CHỨNG lịch sử; nếu bất kỳ giá trị nào trong số đó xuất hiện
# như một hằng số trong mã sản phẩm thì `DEC-PHB02-06` đã bị vi phạm.
LEGACY_TARGET_NUMBERS = ("1300000", "2700000", "12000000", "28790000",
                         "345474000", "28789481081")

PRODUCT_MODULES = (
    "app/web/business_store.py", "app/web/business_service.py",
    "app/web/business_presentation.py", "app/web/business_queries.py",
    "app/modules/reporting/business_metrics.py", "app/web/server.py",
    "tools/db/schema.py",
)


def _code_constants(path: Path) -> set:
    """Mọi HẰNG SỐ thật sự nằm trong mã của một module — KHÔNG gồm docstring.

    Phân biệt này là toàn bộ điểm của CASE 10. Chỉ thị PHB-05 §5 cấm một
    Target *nhúng trong* Python constant / template / JS / default của
    migration / switch-case theo tên nhân viên — tức là cấm một GIÁ TRỊ mà mã
    dùng tới. Nó KHÔNG cấm trích dẫn ô nguồn của sổ cũ trong phần giải thích;
    ngược lại, governance của repo này BẮT trích nguyên văn bằng chứng
    (`docs/analysis/02_FORMULA_MAPPING.md`), và một test đọc cả comment sẽ ép
    người viết sau này xoá đúng thứ chứng minh vì sao con số đó không được
    viết cứng.

    Vì vậy công cụ ở đây là AST, không phải `grep`: nó thấy đúng những gì
    trình thông dịch thấy.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            first = node.body[0] if node.body else None
            if (isinstance(first, ast.Expr)
                    and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)):
                docstrings.add(id(first.value))
    return {node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and id(node) not in docstrings}


def test_case_10_no_employee_target_is_hard_coded_anywhere():
    """CASE 10 — không nhân viên nào có Target viết cứng trong mã.

    Ba vế, vì một vế không đủ:

    1. Không hằng số nào trong mã Python bằng một Target thật của sổ cũ.
    2. Không tên nhân viên nào của master là một hằng số trong mã — tức là
       không có `if employee == "Ly": target = ...` dưới bất kỳ hình dạng nào.
    3. Không template nào chứa một con số Target.
    """
    for relative in PRODUCT_MODULES:
        constants = _code_constants(REPO_ROOT / relative)
        literal = {str(value).replace(".", "") for value in constants}
        for number in LEGACY_TARGET_NUMBERS:
            assert number not in literal, f"{relative}: hằng số {number}"
            assert int(number) not in constants, f"{relative}: hằng số {number}"

    from app.modules.mapping.employee_mapper import load_employee_master

    names = {record.normalized
             for record in load_employee_master(
                 REPO_ROOT / "config" / "employees.yaml").records}
    assert names, "master nhân viên rỗng — test này sẽ không kiểm được gì"
    for relative in PRODUCT_MODULES:
        clash = _code_constants(REPO_ROOT / relative) & names
        assert not clash, f"{relative}: tên nhân viên viết cứng {sorted(clash)}"

    for relative in ("app/web/templates/kinh_doanh_target.html",
                     "app/web/templates/kinh_doanh_nhan_vien.html"):
        # Comment Jinja (`{# … #}`) là phần giải thích của template, tương
        # đương docstring của module — bỏ ra vì cùng lý do đã nói ở
        # `_code_constants`: một test đọc cả phần giải thích sẽ ép người viết
        # sau này xoá đúng thứ nói vì sao con số/cái tên không được viết cứng.
        markup = re.sub(r"\{#.*?#\}", "",
                        (REPO_ROOT / relative).read_text(encoding="utf-8"),
                        flags=re.S)
        for number in LEGACY_TARGET_NUMBERS:
            assert number not in markup.replace(".", ""), f"{relative}: {number}"
        for name in names:
            assert name not in markup, f"{relative}: {name}"


def test_case_10_no_config_file_seeds_a_target_either():
    """Không `config/targets.yaml`, và không khoá `target` trong config nào.

    `docs/analysis/04_HARDCODED_VALUES.md` §3 đề xuất một `targets.yaml` cho
    MVP. `DEC-PHB02-06` chọn hướng khác — Target là DỮ LIỆU Owner nhập, không
    phải cấu hình triển khai — nên một file như vậy tồn tại sẽ là thẩm quyền
    thứ hai cho cùng một con số.
    """
    assert not (REPO_ROOT / "config" / "targets.yaml").exists()
    for path in (REPO_ROOT / "config").glob("*.yaml"):
        text = path.read_text(encoding="utf-8").lower()
        assert "target" not in text, path.name


# --- CASE 11/12 — công thức So target --------------------------------------

def test_case_11_so_target_is_converted_sales_over_target(repository, client):
    """CASE 11 — 250m / 500m = 50 %, đúng `N = F/M` của sổ cũ."""
    persist(repository, [selling("BH1", month=9)])
    row = row_of(body(client, "/kinh-doanh/target?ky=2026-09"), "Ly")
    assert metric(row, "target-converted-sales") == "250.000"  # nghìn đồng
    save_target(client, period="2026-09", employee="Ly", value="500000000")
    assert metric(row_of(body(client, "/kinh-doanh/target?ky=2026-09"), "Ly"),
                  "target-vs") == "50%"
    assert bm.vs_target_percent(CONVERTED_250M, Decimal("500000000")) == Decimal("50")


def test_case_11_so_target_never_silently_uses_total_sales(repository, client):
    """Doanh thu bán hàng KHÔNG được thay chỗ DS quy đổi.

    Với fixture này Doanh thu bán hàng là 8.000.000 còn DS quy đổi là
    250.000.000 — hai con số cách nhau hơn 30 lần, nên nếu công thức âm thầm
    đổi vế thì tỉ lệ sẽ sai rõ rệt chứ không sai một cách khó thấy.
    """
    persist(repository, [selling("BH1", month=9)])
    save_target(client, period="2026-09", employee="Ly", value="500000000")
    row = row_of(body(client, "/kinh-doanh/target?ky=2026-09"), "Ly")
    assert metric(row, "target-vs") == "50%"
    assert metric(row, "target-vs") != "1,6%"  # = 8.000.000 / 500.000.000


def test_case_12_exceeding_the_target_is_never_capped(repository, client):
    """CASE 12 — vượt target hiện đúng số vượt; `IFERROR(F/M,"")` không cap."""
    persist(repository, [selling("BH1", month=9)])
    save_target(client, period="2026-09", employee="Ly", value="200000000")
    # 250.000.000 / 200.000.000 = 125 %
    assert metric(row_of(body(client, "/kinh-doanh/target?ky=2026-09"), "Ly"),
                  "target-vs") == "125%"
    assert bm.vs_target_percent(Decimal("600000000"),
                                Decimal("500000000")) == Decimal("120")


# --- CASE 13 — trạng thái CHƯA HOÀN CHỈNH được thừa hưởng ------------------

def test_case_13_so_target_inherits_the_incomplete_state_of_converted_sales(
    repository, client
):
    """CASE 13 — DS quy đổi chưa chính thức ⟹ So target cũng vậy.

    PHB-05 §9 cấm dựng một hệ trạng thái thứ hai: nhãn ở đây là ĐÚNG nhãn
    `CHÍNH THỨC`/`CHƯA HOÀN CHỈNH` mà `R-S7`/`R-E8` đã freeze, lấy từ cùng
    `STATE_LABELS`.
    """
    persist(repository, [
        selling("BH1", month=9),
        # Dòng thứ hai thiếu giá nhập ⟹ coverage < 100 % ⟹ CHƯA HOÀN CHỈNH.
        selling("BH2", month=9, row=7, kpi_purchase=None, kpi_profit=None),
    ])
    save_target(client, period="2026-09", employee="Ly", value="500000000")
    row = row_of(body(client, "/kinh-doanh/target?ky=2026-09"), "Ly")
    assert metric(row, "target-vs") == "50%"        # con số một phần vẫn hiện
    assert metric(row, "target-vs-state") == "CHƯA HOÀN CHỈNH"

    # Hoàn thiện dòng còn thiếu ⟹ CẢ HAI cùng chuyển sang CHÍNH THỨC.
    persist(repository, [
        selling("BH1", month=9),
        selling("BH2", month=9, row=7),
    ], run_id="run-2", at="2026-10-01T00:00:00", fingerprint="fp-b")
    row = row_of(body(client, "/kinh-doanh/target?ky=2026-09"), "Ly")
    assert metric(row, "target-vs-state") == "CHÍNH THỨC"
    assert business_presentation.STATE_LABELS[bm.STATE_INCOMPLETE] \
        == "CHƯA HOÀN CHỈNH"


# --- CASE 14 — Target ĐỌC báo cáo, không đổi báo cáo -----------------------

def fingerprint(totals: bm.BusinessTotals) -> tuple:
    """Dấu vân tay của MỌI chỉ tiêu nghiệp vụ mà PHB-05 §21 cấm đụng tới."""
    return (
        totals.lines, totals.orders, totals.sales_revenue,
        totals.qualifying_quantity, totals.kpi_profit, totals.converted_sales,
        totals.employee_attributed_profit, totals.unattributed_profit,
        totals.coverage.covered_lines, totals.coverage.total_lines,
        totals.coverage.missing_price_lines, totals.coverage.owner_fixable_lines,
        totals.coverage.blocked_lines, totals.coverage.unresolved_employee_lines,
        totals.state,
    )


def test_case_14_changing_a_target_changes_no_business_number(
    repository, client, service
):
    """CASE 14 — dấu vân tay tổng hợp TRƯỚC và SAU một lần đổi Target.

    Doanh thu · Số đơn · Tổng số SP · Lợi nhuận KPI · DS quy đổi · coverage ·
    trạng thái: từng chữ số giữ nguyên. Đây là bằng chứng mạnh nhất của bất
    biến "Target reads the reporting result; Target does not alter it".
    """
    persist(repository, [
        selling("BH1", month=9),
        selling("BH2", month=9, employee="Hiệp", row=7),
        selling("BH3", month=9, row=8, kpi_purchase=None, kpi_profit=None),
    ])
    from app.web import analytics_queries

    bounds = analytics_queries.month_bounds(2026, 9)
    before = service.period(date_from=bounds[0], date_to=bounds[1])
    before_company = fingerprint(before.totals)
    before_employee = {name: fingerprint(totals)
                       for name, _group, totals in bm.group_by_employee(before.lines)}

    save_target(client, period="2026-09", employee="Ly", value="500000000")
    save_target(client, period="2026-09", employee="Hiệp", value="0")
    save_target(client, period="2026-09", employee="Ly", value="600000000")
    save_target(client, period="2026-09", employee="Hiệp", value="")

    after = service.period(date_from=bounds[0], date_to=bounds[1])
    assert fingerprint(after.totals) == before_company
    assert {name: fingerprint(totals)
            for name, _group, totals in bm.group_by_employee(after.lines)} \
        == before_employee


def test_case_14_the_report_pages_render_the_same_numbers_after_a_target_edit(
    repository, client
):
    """Cùng khẳng định, đo trên HTML thật của hai trang báo cáo."""
    persist(repository, [
        selling("BH1", month=9),
        selling("BH2", month=9, row=7, kpi_purchase=None, kpi_profit=None),
    ])
    watched = ("sales_revenue", "qualifying_quantity", "kpi_profit",
               "converted_sales", "coverage", "coverage-percent", "orders",
               "lines", "state")
    paths = ("/kinh-doanh?ky=2026-09",
             "/kinh-doanh/nhan-vien?ky=2026-09&nhan-vien=Ly")
    before = {path: {name: metric(body(client, path), name) for name in watched}
              for path in paths}

    save_target(client, period="2026-09", employee="Ly", value="500000000")

    after = {path: {name: metric(body(client, path), name) for name in watched}
             for path in paths}
    assert after == before


def test_the_target_write_path_touches_only_its_own_table(repository, store):
    """Bằng chứng CẤU TRÚC cho cùng bất biến, ở tầng đường ghi.

    `BusinessDecisionStore` chỉ được biết bốn bảng quyết định của con người.
    Nếu một ngày nào đó đường ghi Target chạm tới một bảng số liệu, test này
    gãy trước khi một con số sai kịp lên màn hình.
    """
    source = (REPO_ROOT / "app/web/business_store.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    names |= {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    names |= {alias.name for node in ast.walk(tree)
              if isinstance(node, ast.ImportFrom) for alias in node.names}
    assert "employee_target" in names
    assert names.isdisjoint({
        "order_line_result_version", "order_line_source_version",
        "order_line_current", "source_snapshot", "snapshot_line",
        "reconciliation_flag", "legacy_summary_row", "legacy_import",
        "legacy_daily_sales", "legacy_monthly_reference",
    })


# --- CASE 16 — ranh giới Legacy -------------------------------------------

def test_case_16_the_legacy_target_column_stays_read_only(
    engine, client, legacy_workbook_path
):
    """CASE 16 — Target của SỐ CŨ hiện ra nhưng không có đường nào sửa nó.

    Trang `/nhan-vien` (ma trận số cũ) có cột `Target`/`So target` từ PRA-001.
    PHB-05 KHÔNG được biến nó thành ô nhập: đó là bằng chứng lịch sử, và ghi
    đè một sự thật đã xảy ra là việc khác hẳn với đặt một dự định cho tháng
    tới (PHB-05 §10).

    Seed đi thẳng qua `create_import` vì `POST /du-lieu/legacy` đã khoá vĩnh
    viễn (`R2-B01`) — đúng cách mà `tests/test_web_legacy_routes.py` đã dùng.
    """
    from dataclasses import replace

    from app.legacy import parse_workbook, parse_year_workbook

    repo = history_store.build(engine=engine)
    workbook = (
        parse_year_workbook(legacy_workbook_path)
        if web_server._looks_like_year_workbook(legacy_workbook_path)
        else parse_workbook(legacy_workbook_path)
    )
    repo.create_import(replace(workbook, source_file_name="bao_cao.xlsx"))

    html = body(client, "/nhan-vien")
    assert "Target" in html and "So target" in html
    # Ma trận số cũ KHÔNG có một ô nhập nào, và không đường nào tới route ghi
    # Target của PHB-05.
    matrix = re.search(r"<table.*</table>", html, re.S)
    assert matrix is not None
    for forbidden in ("<input", "<form", "<button", "<select"):
        assert forbidden not in matrix.group(0), forbidden
    assert "business_save_target" not in html
    assert "/kinh-doanh/target" not in html


def test_case_16_the_target_write_route_cannot_reach_a_legacy_table(repository):
    """Cùng khẳng định ở tầng cấu trúc: đường ghi Target không biết Legacy."""
    from tools.db import schema

    legacy_tables = {"legacy_import", "legacy_summary_row", "legacy_daily_sales",
                     "legacy_monthly_reference"}
    source = (REPO_ROOT / "app/web/business_service.py").read_text(encoding="utf-8")
    for table in legacy_tables:
        assert table not in source
    assert schema.employee_target.name not in legacy_tables


# --- CASE 17/18 — R1 và R2 giữ nguyên --------------------------------------

def test_case_17_the_primary_navigation_is_unchanged(repository, client):
    """CASE 17 — Target KHÔNG thêm một tab chính nào.

    Bốn tab của `R1` giữ nguyên; màn hình Target là một khung nhìn CON, mở từ
    trang Nhân viên.
    """
    persist(repository, [selling("BH1", month=9)])
    for path in ("/kinh-doanh?ky=2026-09", "/kinh-doanh/target?ky=2026-09",
                 "/kinh-doanh/nhan-vien?ky=2026-09&nhan-vien=Ly"):
        nav = re.search(r'<nav class="ncc-tabs">(.*?)</nav>',
                        body(client, path), re.S).group(1)
        assert nav.count('class="ncc-tab') == 4
        labels = re.findall(r'>([^<>]+)</a>', nav)
        assert [label.strip() for label in labels] == [
            "Báo cáo", "Nhân viên", "Doanh số ngày", "Dữ liệu"]
        assert "Target" not in nav


def test_case_17_the_target_view_is_reachable_from_the_employee_page(
    repository, client
):
    """Khung nhìn con phải MỞ ĐƯỢC — nếu không nó chỉ là một URL bí mật."""
    persist(repository, [selling("BH1", month=9)])
    html = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&nhan-vien=Ly")
    assert "/kinh-doanh/target" in html
    assert metric(html, "target-link") == "ĐẶT / SỬA TARGET"


def test_case_18_legacy_history_stays_one_locked_source(repository, client):
    """CASE 18 — R2 không đổi: một nguồn logic, khoá, không bộ chọn.

    PHB-05 không thêm đường ghi Legacy nào; `POST /du-lieu/legacy` vẫn là
    ranh giới ghi DUY NHẤT của LEGACY_HISTORY (`R2-B01`), và Target không đi
    qua nó.
    """
    html = body(client, "/du-lieu")
    assert "/kinh-doanh/target" not in html
    rules = (REPO_ROOT / "app/web/server.py").read_text(encoding="utf-8")
    legacy_posts = re.findall(r'@app\.post\("(/du-lieu/legacy[^"]*)"\)', rules)
    assert legacy_posts == ["/du-lieu/legacy"], legacy_posts


# --- CASE khác của kỳ "Toàn bộ dữ liệu" ------------------------------------

def test_the_all_data_view_offers_no_target_editing(repository, client):
    """Không có tháng ⟹ không có ô nhập nào, và trang nói rõ vì sao."""
    persist(repository, [selling("BH1", month=9)])
    html = body(client, "/kinh-doanh/target?ky=tat-ca")
    assert business_presentation.TARGET_NO_PERIOD_NOTE in metric(
        html, "target-no-period")
    assert 'data-metric="target-input"' not in html
    assert metric(row_of(html, "Ly"), "target-value") \
        == business_presentation.TARGET_UNSET_LABEL


def test_an_employee_with_a_target_but_no_lines_still_appears(
    repository, client
):
    """Đặt target xong mở lại trang phải THẤY nó, kể cả khi chưa bán gì.

    Ngược lại, Owner sẽ tưởng thao tác vừa rồi không lưu được.
    """
    persist(repository, [selling("BH1", month=9, employee="Ly")])
    save_target(client, period="2026-09", employee="Hiệp", value="400000000")
    row = row_of(body(client, "/kinh-doanh/target?ky=2026-09"), "Hiệp")
    assert metric(row, "target-value") == "400.000"
    assert metric(row, "target-vs") == "—"
    assert 'data-reason="TARGET_NO_ACTUAL"' in row


def test_the_unresolved_employee_bucket_cannot_be_given_a_target(
    repository, client
):
    """"Chưa xác định nhân viên" không phải một người, nên không có target."""
    persist(repository, [selling("BH1", month=9, employee=None)])
    html = body(client, "/kinh-doanh/target?ky=2026-09")
    row = row_of(html, "")
    assert 'data-metric="target-not-editable"' in row
    assert 'data-metric="target-input"' not in row


# --- CASE 19 — E2E thật qua Flask POST -------------------------------------

def test_the_owner_target_workflow_closes_end_to_end(repository, client, service):
    """PHB-05 §19 — một lần đi hết vòng, qua database và qua HTTP thật.

    nạp dữ liệu kinh doanh → mở kỳ → nhập Target bằng POST Flask thật → mở lại
    trang nhân viên → Target + So target đúng giá trị đã lưu → tạo snapshot
    Current MỚI → Target vẫn còn.
    """
    persist(repository, [selling("BH1", month=9), selling("BH2", month=9, row=7)])

    # DS quy đổi của Ly trong 09/2026 = 2 × 250.000.000 = 500.000.000 VND.
    assert metric(body(client, "/kinh-doanh/nhan-vien?ky=2026-09&nhan-vien=Ly"),
                  "converted_sales") == "500.000"

    response = client.post("/kinh-doanh/target", data={
        "ky": "2026-09", "nhan_vien": "Ly", "target": "1.000.000.000"},
        follow_redirects=True)
    assert response.status_code == 200
    assert "Đã lưu Target của Ly" in metric(
        response.get_data(as_text=True), "target-saved")

    # Mở LẠI trang nhân viên: Target và So target đọc từ giá trị đã lưu.
    html = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&nhan-vien=Ly")
    assert metric(html, "employee-target") == "1.000.000"      # nghìn đồng
    assert "1.000.000.000 đồng" in html                        # VND đầy đủ
    assert metric(html, "employee-vs-target") == "50%"         # 500m / 1.000m

    # Snapshot Current MỚI của cùng kỳ — Target sống sót nguyên vẹn.
    persist(repository, [selling("BH1", month=9), selling("BH2", month=9, row=7)],
            run_id="run-2", at="2026-10-01T00:00:00", fingerprint="fp-b")
    assert service.employee_targets((2026, 9)) == {"Ly": Decimal("1000000000")}
    html = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&nhan-vien=Ly")
    assert metric(html, "employee-target") == "1.000.000"
    assert metric(html, "employee-vs-target") == "50%"

    # Và sửa xong thì con số mới có hiệu lực NGAY, không phải chạy lại gì.
    client.post("/kinh-doanh/target", data={
        "ky": "2026-09", "nhan_vien": "Ly", "target": "500000000"})
    html = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&nhan-vien=Ly")
    assert metric(html, "employee-vs-target") == "100%"


# --- Ngữ nghĩa thuần, không cần database -----------------------------------

@pytest.mark.parametrize("converted,target,expected", [
    (Decimal("250000000"), Decimal("500000000"), Decimal("50")),
    (Decimal("600000000"), Decimal("500000000"), Decimal("120")),
    (Decimal("500000000"), Decimal("500000000"), Decimal("100")),
    (Decimal("0"), Decimal("500000000"), Decimal("0")),
    (Decimal("250000000"), None, None),
    (Decimal("250000000"), Decimal("0"), None),
    (None, Decimal("500000000"), None),
    (None, None, None),
])
def test_vs_target_percent_vectors(converted, target, expected):
    assert bm.vs_target_percent(converted, target) == expected


@pytest.mark.parametrize("raw,expected", [
    ("500000000", Decimal("500000000")),
    ("500.000.000", Decimal("500000000")),
    ("500 000 000", Decimal("500000000")),
    ("0", Decimal("0")),
    ("", None),
    ("   ", None),
    (None, None),
])
def test_parse_target_vectors(raw, expected):
    assert business_store.parse_target(raw) == expected


@pytest.mark.parametrize("raw", ["-1", "-500000000", "abc", "5x", "--1"])
def test_parse_target_rejects_what_it_cannot_mean(raw):
    with pytest.raises(business_store.InvalidTargetError):
        business_store.parse_target(raw)


def test_a_target_survives_a_round_trip_through_the_database_exactly(store):
    """Fidelity: con số đọc ra bằng ĐÚNG con số ghi vào, không sai số nhị phân."""
    store.set_employee_target(year=2026, month=9, employee_key="Ly",
                              target_vnd=Decimal("500000000.55"))
    rows = store.employee_targets(year=2026, month=9)
    assert rows["Ly"]["target_vnd"] == Decimal("500000000.55")


def test_the_store_refuses_a_target_it_cannot_mean(store):
    with pytest.raises(business_store.InvalidTargetError):
        store.set_employee_target(year=2026, month=9, employee_key="Ly",
                                  target_vnd=Decimal("-1"))
    with pytest.raises(business_store.InvalidEmployeeError):
        store.set_employee_target(year=2026, month=9, employee_key="  ",
                                  target_vnd=Decimal("1"))
    with pytest.raises(business_store.InvalidTargetPeriodError):
        store.set_employee_target(year=2026, month=13, employee_key="Ly",
                                  target_vnd=Decimal("1"))
