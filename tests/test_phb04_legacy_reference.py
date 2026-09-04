"""PHB-04 — Legacy Reference V1: kỳ lịch sử đọc được mà KHÔNG làm sai số mới.

Nhóm test này trả lời đúng mười câu của Done Gate PHB-04 mục 12, và mỗi test
chứng minh một KẾT QUẢ nghiệp vụ chứ không phải "hàm có chạy":

    A kỳ legacy đọc được · B provenance là LEGACY_REFERENCE · C không vào
    pipeline kế toán · D không đụng coverage lợi nhuận · E kỳ PHB-03 y nguyên ·
    F điều hướng phân biệt được hai nguồn · G chỉ tiêu thiếu hiện N/A chứ
    không phải 0 · H chỉ so khi hợp đồng cho phép · I chỉ tiêu tham chiếu
    không âm thầm sinh phép so · J nạp lại cùng một bản không nhân đôi số.
"""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, select

import tools.db as history_db
from app.web import history_store, legacy_presentation, legacy_reference
from app.web import business_service, business_store
from app.web import server as web_server
from tests.test_business_vertical import pair, persist
from tools.db import schema
from tools.tracking import live_pull

JANUARY = {"date_from": date(2026, 1, 1), "date_to": date(2026, 1, 31)}

# Giá trị cột `AH` của fixture (`tests/fixtures/legacy/build_legacy_workbook.py`):
# doanh số cùng kỳ năm trước, đơn vị VND nguyên. Chỉ ba tháng đầu có số —
# chín tháng còn lại là ô TRỐNG, và đó chính là điều test G cần.
FIXTURE_PREV_YEAR = {1: Decimal("2410000000"), 2: Decimal("1520000000"),
                     3: Decimal("870000000")}


# --- Hạ tầng dùng chung ---------------------------------------------------

@pytest.fixture
def engine():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


@pytest.fixture
def repository(engine):
    return history_store.build(engine=engine)


@pytest.fixture
def snapshots(engine):
    return history_store.SnapshotRepository(engine)


@pytest.fixture
def service(engine):
    return business_service.BusinessReportService(
        engine=engine, store=business_store.BusinessDecisionStore(engine))


@pytest.fixture
def app(monkeypatch, tmp_path, repository, snapshots):
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "ARTIFACT_DIR", (tmp_path / "outputs").resolve())
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    application = web_server.create_app(db_path=tmp_path / "runs.db",
                                        history=repository, snapshots=snapshots)
    application.testing = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def upload(client, path):
    return client.post(
        "/du-lieu/legacy",
        data={"workbook": (io.BytesIO(path.read_bytes()), "bao_cao.xlsx")},
        content_type="multipart/form-data",
    )


@pytest.fixture
def loaded(client, legacy_workbook_path):
    upload(client, legacy_workbook_path)
    return client


def page(client, path="/lich-su") -> str:
    response = client.get(path)
    assert response.status_code == 200, f"{path} → {response.status_code}"
    return response.get_data(as_text=True)


def table_counts(engine) -> dict:
    """Số dòng của MỌI bảng trong history store — dấu vân tay của trạng thái."""
    with engine.connect() as connection:
        return {
            table.name: connection.execute(
                select(func.count()).select_from(table)).scalar()
            for table in schema.METADATA.sorted_tables
        }


# --- A. Kỳ legacy đọc được ------------------------------------------------

class TestLegacyPeriodIsReadable:
    def test_reference_year_periods_come_from_the_prev_year_column(self, loaded, repository):
        """Kỳ 2025 sinh ra từ cột `AH` của DataChart 2026, không từ sheet nào khác."""
        periods = legacy_reference.reference_periods(
            repository.query_monthly_reference())
        assert legacy_reference.reference_years(periods) == [2025]
        by_month = {item.month: item.value for item in periods}
        for month, expected in FIXTURE_PREV_YEAR.items():
            assert by_month[month] == expected, f"tháng {month}"

    def test_the_page_shows_the_reference_period_values(self, loaded):
        html = page(loaded)
        assert "Tháng 01/2025" in html
        # 2.410.000.000 — định dạng vi-VN của ô AH3.
        assert "2.410.000.000" in html

    def test_a_workbook_year_period_is_still_readable(self, loaded, repository):
        """Kỳ báo cáo tay của năm workbook không bị PHB-04 làm hụt đi."""
        assert (2026, 1) in repository.available_periods()

    def test_the_page_says_so_when_nothing_has_been_imported(self, client):
        assert "Chưa nhập bản báo cáo cũ nào" in page(client)


# --- B. Provenance --------------------------------------------------------

class TestProvenanceIsExplicit:
    def test_every_projected_period_carries_legacy_reference(self, loaded, repository):
        periods = legacy_reference.reference_periods(
            repository.query_monthly_reference())
        assert periods
        assert {item.provenance for item in periods} == {"LEGACY_REFERENCE"}

    def test_the_page_names_the_provenance_and_the_source_cell(self, loaded):
        html = page(loaded)
        assert "LEGACY_REFERENCE" in html
        assert legacy_reference.PROVENANCE_LABEL in html
        assert "DataChart 2026!AH" in html

    def test_no_reference_value_appears_without_a_legacy_badge(self, loaded, repository):
        """Mọi ô đi qua `cell()` nên luôn có nhãn nguồn và đơn vị."""
        rows = legacy_presentation.reference_rows(
            legacy_reference.reference_periods(repository.query_monthly_reference()))
        assert rows
        for row in rows:
            assert row["cell"]["unit"] == "đồng (số cũ)"

    def test_the_page_never_claims_the_current_engine_produced_these_numbers(self, loaded):
        html = page(loaded)
        assert "KHÔNG do công cụ hiện tại tính lại" in html
        for forbidden in ("AUTO_CALCULATED", "ERP_RECONCILED", "CURRENT_ENGINE"):
            assert forbidden not in html


# --- C. Không vào pipeline kế toán hiện hành ------------------------------

class TestLegacyStaysOutOfTheAccountingPipeline:
    def test_legacy_import_writes_nothing_into_pipeline_tables(
        self, client, legacy_workbook_path, engine
    ):
        pipeline_tables = ("order_line_source_version", "order_line_result_version",
                           "order_line_current", "source_snapshot", "snapshot_line",
                           "reconciliation_flag")
        upload(client, legacy_workbook_path)
        counts = table_counts(engine)
        assert counts["legacy_monthly_reference"] > 0, "chưa nhập được gì thì test vô nghĩa"
        for table in pipeline_tables:
            assert counts[table] == 0, table

    def test_reading_the_legacy_page_writes_nothing_at_all(
        self, loaded, engine
    ):
        before = table_counts(engine)
        page(loaded)
        page(loaded)
        assert table_counts(engine) == before

    def test_every_legacy_row_is_constrained_to_the_legacy_origin(self, loaded, engine):
        """Không phải quy ước đặt tên: đây là CHECK constraint ở tầng schema."""
        with engine.connect() as connection:
            for table in (schema.legacy_import, schema.legacy_summary_row,
                          schema.legacy_daily_sales, schema.legacy_monthly_reference):
                origins = connection.execute(
                    select(table.c.origin).distinct()).scalars().all()
                assert set(origins) <= {"LEGACY_REFERENCE"}, table.name


# --- D. Không đụng coverage lợi nhuận của số mới --------------------------

class TestLegacyDoesNotTouchCurrentProfitCoverage:
    def test_coverage_is_identical_before_and_after_a_legacy_import(
        self, client, legacy_workbook_path, snapshots, service
    ):
        """Nạp một bản legacy KHÔNG được làm nhúc nhích coverage giá nhập."""
        persist(snapshots, [pair("BH1", kpi_purchase=None, kpi_profit=None)])
        before = service.period(**JANUARY).totals

        upload(client, legacy_workbook_path)
        after = service.period(**JANUARY).totals

        assert after.coverage == before.coverage
        assert after.coverage.covered_lines == 0
        assert after.coverage.missing_price_lines == 1
        assert after.kpi_profit is None          # NULL, không phải 0
        assert after.official_kpi_profit is None

    def test_legacy_money_never_reaches_the_current_period_totals(
        self, client, legacy_workbook_path, snapshots, service
    ):
        persist(snapshots, [pair("BH1", sell="8000000", kpi_purchase="5000000",
                                 kpi_profit="3000000")])
        upload(client, legacy_workbook_path)
        totals = service.period(**JANUARY).totals
        # Doanh thu vẫn đúng một dòng bán; không cộng thêm đồng nào của số cũ.
        assert totals.sales_revenue == Decimal("8000000")
        assert totals.lines == 1


# --- E. Kỳ PHB-03 y nguyên ------------------------------------------------

class TestCurrentBusinessPagesAreUnchanged:
    def test_the_business_summary_still_renders_after_a_legacy_import(
        self, loaded, snapshots
    ):
        persist(snapshots, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])
        html = page(loaded, "/kinh-doanh?ky=2026-01")
        assert "8.000.000" in html

    def test_the_legacy_pages_of_pra_001_still_render(self, loaded):
        assert "SỐ CŨ" in page(loaded, "/nhan-vien")
        page(loaded, "/doanh-so-ngay")


# --- F. Điều hướng phân biệt được hai nguồn -------------------------------

class TestNavigationDistinguishesOrigins:
    def test_a_period_with_both_origins_is_labelled_with_both(self):
        rows = legacy_reference.period_navigation(
            legacy_summary_periods=[(2026, 1)],
            legacy_reference_periods=[],
            pipeline_periods=[(2026, 1)],
        )
        assert len(rows) == 1
        assert rows[0].both
        assert rows[0].origin_labels == ["SỐ MỚI", "SỐ CŨ"]

    def test_a_reference_year_period_is_legacy_only(self, loaded, repository):
        periods = legacy_reference.reference_periods(
            repository.query_monthly_reference())
        rows = legacy_reference.period_navigation(
            legacy_summary_periods=[], legacy_reference_periods=periods,
            pipeline_periods=[],
        )
        assert rows
        assert all(row.year == 2025 and row.has_legacy and not row.has_pipeline
                   for row in rows)

    def test_an_empty_reference_cell_never_becomes_a_navigable_period(
        self, loaded, repository
    ):
        """Tháng 04–12/2025 có ô AH TRỐNG ⟹ không phải một kỳ có dữ liệu."""
        periods = legacy_reference.reference_periods(
            repository.query_monthly_reference())
        rows = legacy_reference.period_navigation(
            legacy_summary_periods=[], legacy_reference_periods=periods,
            pipeline_periods=[],
        )
        assert {row.month for row in rows} == set(FIXTURE_PREV_YEAR)

    def test_the_page_links_to_both_the_legacy_and_the_current_view(
        self, loaded, snapshots
    ):
        persist(snapshots, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])
        html = page(loaded)
        assert "/nhan-vien?ky=2026-01" in html
        assert "/kinh-doanh?ky=2026-01" in html

    def test_the_page_says_when_the_current_period_list_is_unreadable(
        self, monkeypatch, tmp_path, repository, legacy_workbook_path
    ):
        """Thiếu snapshot store ⟹ danh mục kỳ KHÔNG được im lặng chỉ có legacy.

        Hôm nay `_build_snapshots()` dựng snapshot repo trên chính engine của
        history store, nên một app CÓ history luôn CÓ cả snapshot — trạng thái
        dưới đây phải dựng bằng monkeypatch. Nhánh này vẫn được giữ và được
        kiểm: nó là cùng một kỷ luật với `not_configured()` của PRA-001 — một
        danh sách thiếu nguồn không bao giờ được trông giống danh sách đủ.
        """
        monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
        monkeypatch.setattr(web_server, "ARTIFACT_DIR", (tmp_path / "outputs").resolve())
        monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
        monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
        monkeypatch.setattr(web_server, "_build_snapshots", lambda legacy: None)
        application = web_server.create_app(db_path=tmp_path / "runs.db",
                                            history=repository)
        application.testing = True
        client = application.test_client()
        upload(client, legacy_workbook_path)
        assert "không phải là toàn bộ kỳ đang có" in page(client)


# --- G. Chỉ tiêu thiếu hiện N/A, KHÔNG phải 0 -----------------------------

class TestMissingMetricsAreNeverFabricated:
    def test_an_empty_reference_month_renders_a_dash_not_a_zero(self, loaded, repository):
        rows = legacy_presentation.reference_rows(
            legacy_reference.reference_periods(repository.query_monthly_reference()))
        empty = [row for row in rows if not row["available"]]
        assert empty, "fixture phải có tháng trống, nếu không test này vô nghĩa"
        for row in empty:
            assert row["cell"]["text"] == "—"
            assert row["cell"]["empty"] is True

    def test_unavailable_metrics_are_declared_not_invented(self):
        keys = {rule.key for rule
                in legacy_reference.unavailable_metrics("REFERENCE_YEAR")}
        # Năm trước KHÔNG có bằng chứng cho bất cứ thứ gì ngoài doanh số tháng.
        assert keys == {"orders", "products", "converted_revenue", "profit",
                        "target", "by_employee", "daily_sales"}

    def test_the_only_supported_reference_year_metric_is_monthly_sales(self):
        supported = legacy_reference.supported_metrics("REFERENCE_YEAR")
        assert [rule.key for rule in supported] == ["sales_vnd"]
        assert supported[0].metric_class == legacy_reference.REFERENCE_ONLY

    def test_the_page_states_why_a_metric_is_unavailable(self, loaded):
        html = page(loaded)
        assert "Không có bằng chứng" in html


# --- H/I. Cổng so sánh ----------------------------------------------------

class TestComparisonGate:
    def test_no_metric_is_comparable_in_v1(self):
        assert legacy_reference.has_comparable_metric() is False
        assert all(rule.metric_class != legacy_reference.COMPARABLE
                   for period_class in legacy_reference.CONTRACTS
                   for rule in legacy_reference.rules(period_class))

    def test_a_reference_only_metric_produces_no_percentage(self):
        result = legacy_reference.compare(
            Decimal("1000"), Decimal("1500"),
            legacy_key="sales_vnd", current_key="sales_revenue")
        assert result.allowed is False
        assert result.percent is None
        assert "Không so được" in result.note

    def test_a_pair_outside_the_contract_is_refused_rather_than_guessed(self):
        result = legacy_reference.compare(
            Decimal("1000"), Decimal("1500"),
            legacy_key="bonus", current_key="kpi_profit")
        assert result.allowed is False
        assert result.percent is None
        assert "chưa xét cặp chỉ tiêu này" in result.note

    def test_the_gate_reads_the_contract_instead_of_hardcoding_a_refusal(self):
        """Cổng phải là cổng THẬT: hợp đồng cho phép ⟹ nó tính."""
        permissive = (legacy_reference.CrossOriginRule(
            "sales_vnd", "sales_revenue", True, "giả định của test"),)
        result = legacy_reference.compare(
            Decimal("1000"), Decimal("1500"),
            legacy_key="sales_vnd", current_key="sales_revenue",
            contract=permissive)
        assert result.allowed is True
        assert result.percent == Decimal("50")

    def test_a_permitted_pair_with_a_missing_side_still_refuses_to_invent(self):
        permissive = (legacy_reference.CrossOriginRule(
            "sales_vnd", "sales_revenue", True, "giả định của test"),)
        for legacy_value, current_value in ((None, Decimal("10")),
                                            (Decimal("10"), None),
                                            (Decimal("10"), Decimal("0"))):
            result = legacy_reference.compare(
                legacy_value, current_value, legacy_key="sales_vnd",
                current_key="sales_revenue", contract=permissive)
            assert result.percent is None
            assert "không tính được" in result.note

    def test_the_page_never_prints_a_growth_percentage_between_origins(
        self, loaded, snapshots
    ):
        persist(snapshots, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])
        html = page(loaded)
        assert "Không so được" in html
        assert "chưa chỉ tiêu nào đạt điều đó" in html

    def test_every_contract_pair_records_why_it_is_refused(self):
        for row in legacy_reference.comparison_summary():
            assert row["allowed"] is False
            assert row["reason"].strip(), row["legacy_key"]


# --- J. Nạp lại cùng một bản không nhân đôi số ----------------------------

class TestReloadingIsIdempotent:
    def test_uploading_the_same_workbook_twice_creates_no_second_version(
        self, client, legacy_workbook_path, engine, repository
    ):
        upload(client, legacy_workbook_path)
        after_first = table_counts(engine)
        first_import = repository.current_import()["import_id"]

        upload(client, legacy_workbook_path)

        assert table_counts(engine) == after_first
        assert repository.current_import()["import_id"] == first_import
        assert repository.count_imports() == 1

    def test_the_projected_reference_periods_do_not_duplicate(
        self, client, legacy_workbook_path, repository
    ):
        upload(client, legacy_workbook_path)
        upload(client, legacy_workbook_path)
        periods = legacy_reference.reference_periods(
            repository.query_monthly_reference())
        keys = [(item.year, item.month) for item in periods]
        assert len(keys) == len(set(keys))


# --- Hợp đồng: bảo toàn ranh giới DEC-169 ---------------------------------

class TestSummary2025StaysOutOfScope:
    def test_no_summary_2025_row_is_ever_persisted(self, loaded, engine):
        """`DEC-169` — không import, không persist, không query, không display."""
        with engine.connect() as connection:
            sheets = connection.execute(
                select(schema.legacy_summary_row.c.sheet_name).distinct()
            ).scalars().all()
        assert "Summary 2025" not in sheets

    def test_the_reference_year_contract_points_at_datachart_not_summary_2025(self):
        rule = legacy_reference.rule_for("REFERENCE_YEAR", "sales_vnd")
        assert "AH3:AH14" in rule.evidence
        by_employee = legacy_reference.rule_for("REFERENCE_YEAR", "by_employee")
        assert by_employee.metric_class == legacy_reference.UNAVAILABLE
        assert "DEC-169" in by_employee.evidence
