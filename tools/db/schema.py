"""Schema history tối thiểu cho PRA-001 (LEGACY_REFERENCE).

Nguồn DDL DUY NHẤT: migration ``0001_legacy`` và ``LegacyRepository`` cùng
đọc ``METADATA`` ở đây, nên schema thật và migration không thể trôi khỏi
nhau. Bốn bảng dưới đây là toàn bộ DATA_MODEL_MINIMUM đã freeze ở
``docs/tasks/TASK-PRA-001-legacy-reference-vertical.md`` — KHÔNG thêm bảng
snapshot/version/reconciliation của PRA-002 vào đây.

Ràng buộc dialect: chỉ dùng kiểu nằm trong tập giao SQLite ↔ PostgreSQL
(``Text``, ``Integer``, ``Numeric``, ``Boolean``). JSON lưu dưới dạng TEXT
(chuỗi JSON do tầng repository tự mã hoá) để không phụ thuộc kiểu JSON riêng
của từng dialect.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean, CheckConstraint, Column, Date, ForeignKey, Index, Integer,
    MetaData, Numeric, Table, Text, TypeDecorator, UniqueConstraint,
)


class ExactNumeric(TypeDecorator):
    """NUMERIC trên PostgreSQL, TEXT trên SQLite — giá trị luôn khứ hồi ĐÚNG.

    Fidelity của số cũ là ranh giới chấp nhận cứng của TASK-PRA-001: giá trị
    đọc ra khỏi database phải bằng đúng giá trị đọc từ ô Excel. SQLite không
    có kiểu thập phân thật — cột khai báo NUMERIC ở đó mang affinity số và
    biến chuỗi thập phân thành REAL, tức là đưa sai số nhị phân vào một con
    số mà công cụ KHÔNG có thẩm quyền thay đổi. Nên: production (PostgreSQL)
    giữ đúng kiểu NUMERIC như DATA_MODEL_MINIMUM đã freeze, còn local/test
    (SQLite) lưu chuỗi thập phân nguyên văn và dựng lại Decimal khi đọc.
    """

    cache_ok = True
    impl = Numeric

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(Text())
        return dialect.type_descriptor(Numeric())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "sqlite":
            return str(value)
        return value

    def process_result_value(self, value, dialect) -> Optional[Decimal]:
        if value is None:
            return None
        return value if isinstance(value, Decimal) else Decimal(str(value))


ORIGIN_LEGACY = "LEGACY_REFERENCE"

ROW_KINDS = ("SELLER", "MONTH_TOTAL", "PROGRESS", "YEAR_TOTAL")

METADATA = MetaData()

# Cột `origin` tường minh trên MỌI bảng fact (quy ước chung với PRA-002):
# không bao giờ suy ra nguồn dữ liệu từ tên bảng.
_ORIGIN_CHECK = f"origin = '{ORIGIN_LEGACY}'"


def _origin_column() -> Column:
    return Column("origin", Text, nullable=False, server_default=ORIGIN_LEGACY)


legacy_import = Table(
    "legacy_import", METADATA,
    Column("import_id", Text, primary_key=True),
    _origin_column(),
    Column("source_file_name", Text),
    Column("file_fingerprint", Text, nullable=False),
    Column("file_size", Integer),
    Column("imported_at", Text),
    Column("imported_by", Text, nullable=True),
    Column("version_label", Text),
    Column("sheets_imported", Text),
    Column("is_current", Boolean, nullable=False, default=False),
    Column("notes", Text),
    # `DEC-178` — THẨM QUYỀN NGUỒN của lần nhập này.
    #
    #   AUTHORITATIVE_YEAR  workbook lịch sử MỘT NĂM độc lập. Là nguồn CHUẨN
    #                       cho năm đó; không bản nhập nào ghi đè nó.
    #   WORKBOOK_SNAPSHOT   bản sao Summary của một năm khác nằm nhúng trong
    #                       workbook năm hiện hành. Bằng chứng THỨ CẤP.
    #
    # NULL = các bản nhập có trước `DEC-178`, đọc như WORKBOOK_SNAPSHOT. Cột
    # nullable nên migration là ADDITIVE thuần: không backfill, không đụng
    # một dòng dữ liệu nào đang có.
    #
    # Vì sao là cột tường minh chứ không suy từ tên sheet: "nguồn nào thắng"
    # là một quyết định của chủ dự án đã freeze, và một quyết định như thế
    # không được phép phụ thuộc vào việc ai đó có đặt tên sheet đúng hay không.
    Column("source_authority", Text, nullable=True),
    UniqueConstraint("file_fingerprint", name="uq_legacy_import_fingerprint"),
    CheckConstraint(_ORIGIN_CHECK, name="ck_legacy_import_origin"),
)

_NUMERIC_SUMMARY_COLUMNS = (
    "orders", "products", "sales", "converted_revenue", "profit", "margin_ratio",
    "vs_prev_month_ratio", "stock_ratio", "actual_profit", "per_day", "target",
    "vs_target_ratio", "bonus", "workdays", "base_salary", "allowance",
    "total_salary",
)

legacy_summary_row = Table(
    "legacy_summary_row", METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("import_id", Text, ForeignKey("legacy_import.import_id"), nullable=False),
    _origin_column(),
    Column("year", Integer, nullable=False),
    Column("month", Integer, nullable=True),
    Column("seller_label", Text),
    Column("row_kind", Text, nullable=False),
    Column("sheet_name", Text, nullable=False),
    Column("sheet_row", Integer, nullable=False),
    Column("unit", Text, nullable=False, server_default="kVND"),
    *(Column(name, ExactNumeric, nullable=True) for name in _NUMERIC_SUMMARY_COLUMNS),
    Column("formula_text", Text),
    Column("known_defects", Text),
    UniqueConstraint("import_id", "sheet_name", "sheet_row", name="uq_legacy_summary_cell"),
    CheckConstraint(_ORIGIN_CHECK, name="ck_legacy_summary_origin"),
    CheckConstraint(
        "row_kind IN (%s)" % ", ".join("'%s'" % kind for kind in ROW_KINDS),
        name="ck_legacy_summary_row_kind",
    ),
)

legacy_daily_sales = Table(
    "legacy_daily_sales", METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("import_id", Text, ForeignKey("legacy_import.import_id"), nullable=False),
    _origin_column(),
    Column("year", Integer, nullable=False),
    Column("month", Integer, nullable=False),
    Column("day", Integer, nullable=False),
    Column("sales_vnd", ExactNumeric, nullable=True),
    Column("source_sheet", Text, nullable=False),
    UniqueConstraint("import_id", "year", "month", "day", name="uq_legacy_daily_cell"),
    CheckConstraint(_ORIGIN_CHECK, name="ck_legacy_daily_origin"),
)

legacy_monthly_reference = Table(
    "legacy_monthly_reference", METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("import_id", Text, ForeignKey("legacy_import.import_id"), nullable=False),
    _origin_column(),
    Column("year", Integer, nullable=False),
    Column("month", Integer, nullable=False),
    Column("sales_current_year_vnd", ExactNumeric, nullable=True),
    Column("sales_prev_year_vnd", ExactNumeric, nullable=True),
    Column("vs_last_year_ratio", ExactNumeric, nullable=True),
    Column("vs_target_ratio", ExactNumeric, nullable=True),
    Column("target_year", ExactNumeric, nullable=True),
    Column("average_per_day", ExactNumeric, nullable=True),
    Column("target_per_day", ExactNumeric, nullable=True),
    Column("formula_text", Text),
    UniqueConstraint("import_id", "year", "month", name="uq_legacy_monthly_cell"),
    CheckConstraint(_ORIGIN_CHECK, name="ck_legacy_monthly_origin"),
)


# ---------------------------------------------------------------------------
# TASK-PRA-002 — origin PIPELINE_GENERATED (migration ``0002_snapshots``).
#
# Sáu bảng dưới đây là DATA_MODEL_MINIMUM đã freeze ở
# ``docs/tasks/TASK-PRA-002-pipeline-persistence-reconciliation.md`` mục 4.
# Chúng KHÔNG bao giờ trộn với bốn bảng ``legacy_*`` ở trên: hai origin là hai
# thẩm quyền khác nhau (DEC-166 E, ADR-107/108) và không view nào được UNION
# chúng thành một con số không nhãn.
#
# Append-only là bất biến của tầng này. Chỉ ``order_line_current`` (bảng con
# trỏ) và ba cột xác nhận coverage của ``source_snapshot`` được UPDATE; mọi
# bảng fact khác chỉ INSERT — một version đã ghi là bằng chứng kế toán, ghi đè
# nó là xoá dấu vết "kế toán đã sửa gì".
# ---------------------------------------------------------------------------

ORIGIN_PIPELINE = "PIPELINE_GENERATED"

COVERAGE_STATES = ("DETECTED_ONLY", "HEADER_CONSISTENT", "CONFIRMED_COMPLETE")

# Kết quả reconcile cấp dòng của MỘT snapshot (mục 8 bước 2 của task).
OUTCOMES = ("INSERT", "SAME", "SOURCE_CHANGED", "ORDER_KEY_COLLISION")

FLAG_KINDS = (
    "SOURCE_CHANGED", "NOT_SEEN_IN_LATEST_SNAPSHOT",
    "REMOVED_IN_SOURCE_CANDIDATE", "RESULT_REVISED", "ORDER_KEY_COLLISION",
)

_ORIGIN_PIPELINE_CHECK = f"origin = '{ORIGIN_PIPELINE}'"


def _pipeline_origin_column() -> Column:
    return Column("origin", Text, nullable=False, server_default=ORIGIN_PIPELINE)


def _in_check(column: str, values: tuple[str, ...]) -> str:
    return "%s IN (%s)" % (column, ", ".join("'%s'" % value for value in values))


source_snapshot = Table(
    "source_snapshot", METADATA,
    Column("snapshot_id", Text, primary_key=True),
    _pipeline_origin_column(),
    Column("run_id", Text, nullable=False),
    Column("created_at", Text, nullable=False),
    Column("source_file_name", Text),
    Column("file_fingerprint", Text, nullable=False),
    Column("file_size", Integer),
    Column("duplicate_of_snapshot_id", Text,
           ForeignKey("source_snapshot.snapshot_id"), nullable=True),
    Column("header_text", Text, nullable=True),
    Column("header_date_min", Date, nullable=True),
    Column("header_date_max", Date, nullable=True),
    Column("detected_date_min", Date, nullable=True),
    Column("detected_date_max", Date, nullable=True),
    Column("coverage_state", Text, nullable=False),
    Column("confirmed_range_start", Date, nullable=True),
    Column("confirmed_range_end", Date, nullable=True),
    Column("confirmed_at", Text, nullable=True),
    Column("confirmed_by", Text, nullable=True),
    Column("sheet_data_rows", Integer, nullable=False),
    Column("rows_without_order_id", Integer, nullable=False),
    Column("line_count", Integer, nullable=False),
    Column("order_count", Integer, nullable=False),
    Column("n_insert", Integer, nullable=False, server_default="0"),
    Column("n_same", Integer, nullable=False, server_default="0"),
    Column("n_source_changed", Integer, nullable=False, server_default="0"),
    Column("n_collision", Integer, nullable=False, server_default="0"),
    Column("n_not_seen", Integer, nullable=False, server_default="0"),
    Column("n_removed_candidate", Integer, nullable=False, server_default="0"),
    Column("n_result_revised", Integer, nullable=False, server_default="0"),
    Column("evidence_json", Text, nullable=False),
    Column("summary_json", Text, nullable=False),
    UniqueConstraint("run_id", name="uq_source_snapshot_run"),
    CheckConstraint(_ORIGIN_PIPELINE_CHECK, name="ck_source_snapshot_origin"),
    CheckConstraint(_in_check("coverage_state", COVERAGE_STATES),
                    name="ck_source_snapshot_coverage_state"),
)

order_line_source_version = Table(
    "order_line_source_version", METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    _pipeline_origin_column(),
    Column("order_key", Text, nullable=False),
    Column("product_key", Text, nullable=False),
    Column("occurrence_index", Integer, nullable=False),
    Column("version_no", Integer, nullable=False),
    Column("snapshot_id", Text, ForeignKey("source_snapshot.snapshot_id"), nullable=False),
    # Đường nâng cấp namespace theo năm (F4): giữ sẵn hai cột, KHÔNG dùng để
    # reconcile ở PRA-002 — BH có reset theo năm hay không vẫn là UNKNOWN.
    Column("bh_number", Integer, nullable=True),
    Column("bh_year_hint", Integer, nullable=True),
    Column("sale_date", Date, nullable=True),
    Column("product_raw", Text, nullable=True),
    Column("quantity", ExactNumeric, nullable=True),
    Column("sell_price", ExactNumeric, nullable=True),
    Column("discount", ExactNumeric, nullable=True),
    Column("total_sales_raw", ExactNumeric, nullable=True),
    Column("delivery_cost", ExactNumeric, nullable=True),
    Column("source_profit", ExactNumeric, nullable=True),
    Column("imei", Text, nullable=True),
    Column("note_raw", Text, nullable=True),
    Column("employee_raw", Text, nullable=True),
    # EMPLOYEE WORKSPACE UX (`DEC-PHB02-08`) — ba trường KHÁCH HÀNG của chính
    # sổ kế toán đang nạp (`app/modules/importing/raw_reader.py` cột 5/6/7).
    #
    # Trước quyết định này, PRA-002 mục 2/mục 10 loại chúng khỏi tầng lưu trữ
    # theo hướng tối thiểu hoá dữ liệu. Owner — người kiểm soát chính sổ kế
    # toán này — đã yêu cầu tường minh rằng bảng kê nghiệp vụ phải hiện Tên
    # KH · SĐT · Địa chỉ, vì một dòng bán không có khách hàng thì không đối
    # chiếu được với đơn thật. Ranh giới cũ vì thế được THU HẸP, không bị xoá:
    #
    # - Đúng BA trường này, lấy từ ĐÚNG sổ đang nạp. Không CRM, không ghép
    #   danh tính liên hệ thống (`§49` của chỉ thị).
    # - `imei`, `note_raw`, `employee_raw` VẪN nằm ngoài mọi đường báo cáo —
    #   `tests/test_business_boundaries.py` canh việc đó bằng chính mã nguồn.
    # - KHÔNG vào `FINGERPRINT_FIELDS`: kế toán sửa tên khách KHÔNG phải là
    #   "dòng bán này đã bị sửa", nên reconcile không được đổi nghĩa vì nó.
    Column("customer_name", Text, nullable=True),
    Column("customer_phone", Text, nullable=True),
    Column("customer_address", Text, nullable=True),
    Column("row_hash", Text, nullable=False),
    Column("line_fingerprint", Text, nullable=False),
    Column("changed_fields_json", Text, nullable=True),
    Column("created_at", Text, nullable=False),
    UniqueConstraint("order_key", "product_key", "occurrence_index", "version_no",
                     name="uq_source_version_key_version"),
    CheckConstraint(_ORIGIN_PIPELINE_CHECK, name="ck_source_version_origin"),
    Index("ix_source_version_order_key", "order_key"),
    Index("ix_source_version_sale_date", "sale_date"),
)

snapshot_line = Table(
    "snapshot_line", METADATA,
    Column("snapshot_id", Text, ForeignKey("source_snapshot.snapshot_id"),
           primary_key=True),
    Column("order_key", Text, primary_key=True),
    Column("product_key", Text, primary_key=True),
    Column("occurrence_index", Integer, primary_key=True),
    Column("source_version_id", Integer,
           ForeignKey("order_line_source_version.id"), nullable=False),
    Column("source_row", Integer, nullable=False),
    Column("outcome", Text, nullable=False),
    CheckConstraint(_in_check("outcome", OUTCOMES), name="ck_snapshot_line_outcome"),
)

order_line_result_version = Table(
    "order_line_result_version", METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    _pipeline_origin_column(),
    Column("run_id", Text, nullable=False),
    Column("snapshot_id", Text, ForeignKey("source_snapshot.snapshot_id"), nullable=False),
    Column("order_key", Text, nullable=False),
    Column("product_key", Text, nullable=False),
    Column("occurrence_index", Integer, nullable=False),
    Column("source_version_id", Integer,
           ForeignKey("order_line_source_version.id"), nullable=False),
    Column("status", Text, nullable=False),
    Column("pending_reasons_json", Text, nullable=True),
    Column("total_sales", ExactNumeric, nullable=True),
    Column("employee_normalized", Text, nullable=True),
    Column("employee_group", Text, nullable=True),
    Column("lead_source_final", Text, nullable=True),
    Column("identity_namespace", Text, nullable=True),
    Column("canonical_product_code", Text, nullable=True),
    Column("accounting_purchase_price", ExactNumeric, nullable=True),
    Column("price_source", Text, nullable=False),
    Column("composition_rule", Text, nullable=True),
    Column("accounting_profit", ExactNumeric, nullable=True),
    Column("kpi_purchase_price", ExactNumeric, nullable=True),
    Column("kpi_purchase_provenance", Text, nullable=False),
    Column("eligible_kpi_profit", ExactNumeric, nullable=True),
    Column("product_group_final", Text, nullable=True),
    Column("conversion_scheme_final", Text, nullable=True),
    Column("conversion_rate_final", ExactNumeric, nullable=True),
    Column("result_fingerprint", Text, nullable=False),
    Column("created_at", Text, nullable=False),
    UniqueConstraint("run_id", "order_key", "product_key", "occurrence_index",
                     name="uq_result_version_run_key"),
    CheckConstraint(_ORIGIN_PIPELINE_CHECK, name="ck_result_version_origin"),
    CheckConstraint(_in_check("status", ("AUTO", "PENDING")),
                    name="ck_result_version_status"),
    Index("ix_result_version_key", "order_key", "product_key", "occurrence_index"),
)

order_line_current = Table(
    "order_line_current", METADATA,
    Column("order_key", Text, primary_key=True),
    Column("product_key", Text, primary_key=True),
    Column("occurrence_index", Integer, primary_key=True),
    _pipeline_origin_column(),
    Column("current_source_version_id", Integer,
           ForeignKey("order_line_source_version.id"), nullable=False),
    Column("current_result_version_id", Integer,
           ForeignKey("order_line_result_version.id"), nullable=False),
    Column("first_seen_snapshot_id", Text,
           ForeignKey("source_snapshot.snapshot_id"), nullable=False),
    Column("last_seen_snapshot_id", Text,
           ForeignKey("source_snapshot.snapshot_id"), nullable=False),
    Column("sale_date", Date, nullable=True),
    Column("order_key_collision", Boolean, nullable=False, server_default="0"),
    Column("updated_at", Text, nullable=False),
    CheckConstraint(_ORIGIN_PIPELINE_CHECK, name="ck_order_line_current_origin"),
    Index("ix_order_line_current_sale_date", "sale_date"),
)

reconciliation_flag = Table(
    "reconciliation_flag", METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("kind", Text, nullable=False),
    Column("order_key", Text, nullable=False),
    Column("product_key", Text, nullable=False),
    Column("occurrence_index", Integer, nullable=False),
    Column("raised_by_snapshot_id", Text,
           ForeignKey("source_snapshot.snapshot_id"), nullable=False),
    Column("run_id", Text, nullable=True),
    Column("from_version_id", Integer, nullable=True),
    Column("to_version_id", Integer, nullable=True),
    Column("detail_json", Text, nullable=True),
    Column("created_at", Text, nullable=False),
    Column("acknowledged_at", Text, nullable=True),
    CheckConstraint(_in_check("kind", FLAG_KINDS), name="ck_reconciliation_flag_kind"),
    Index("ix_reconciliation_flag_kind", "kind"),
    Index("ix_reconciliation_flag_order_key", "order_key"),
)

# Thứ tự tạo/xoá tường minh cho migration 0002 (FK source_snapshot ← các bảng
# fact; snapshot_line/current phụ thuộc source_version + result_version).
PIPELINE_TABLES = (
    source_snapshot, order_line_source_version, snapshot_line,
    order_line_result_version, order_line_current, reconciliation_flag,
)


# ---------------------------------------------------------------------------
# PHB-03 — Summary + Employee Business Parity V1 (migration ``0003_business``).
#
# Hai bảng dưới đây là TOÀN BỘ persistence mới mà PHB-03 cần, và chúng cố ý
# KHÔNG phải một subsystem: không workflow duyệt, không lịch sử phiên bản,
# không audit service, không trình soạn dữ liệu kinh tế tổng quát. Mỗi bảng
# giữ ĐÚNG MỘT quyết định hiện hành của con người, ghi đè tại chỗ khi người đó
# đổi ý (DEC-PHB02-02, DEC-PHB02-05 + chỉ thị "keep it SMALL" của PHB-03 §3).
#
# Vì sao chúng là bảng RIÊNG chứ không phải cột mới trên
# ``order_line_result_version``: bảng đó là APPEND-ONLY và mỗi dòng là kết quả
# của MỘT lần chạy pipeline — bằng chứng kế toán. Một giá trị do Owner nhập
# sau khi pipeline đã chạy không phải kết quả của lần chạy đó; ghi đè vào đấy
# sẽ xoá dấu vết "engine đã tính ra gì" và biến một input của con người thành
# một output của máy. Hai thẩm quyền khác nhau ⟹ hai bảng khác nhau, và tầng
# truy vấn hợp nhất chúng LÚC ĐỌC (COALESCE), nơi provenance vẫn nhìn thấy được.
#
# Thẩm quyền KHÔNG bị đụng tới: ``accounting_purchase_price``/``price_source``
# (PriceProvider, TASK-105/105D/105E) và ``HistoricalConfirmedRegistry`` (E-J,
# chỉ pre-cutover, INV-47/INV-51) giữ nguyên. Override ở đây chỉ tác động tới
# ĐƯỜNG BÁO CÁO KPI (``kpi_purchase_price`` → ``EligibleKpiProfit`` → DS quy
# đổi), đúng slot từ vựng đã dành sẵn ở ``PRICE_SOURCE_MANUAL``
# (``app/modules/domain/models.py``), không tạo ra một authority giá nhập thứ hai.
# ---------------------------------------------------------------------------

# Provenance của giá nhập KPI dùng cho báo cáo (DEC-PHB02-02 §3).
PURCHASE_PROVENANCE_AUTO = "AUTO"
PURCHASE_PROVENANCE_MANUAL = "MANUAL"
PURCHASE_PROVENANCE_MANUAL_OVERRIDE = "MANUAL_OVERRIDE"
# Chỉ hai giá trị dưới đây được LƯU: ``AUTO`` là trạng thái "chưa có dòng
# override nào", nên nó không bao giờ là một dòng trong bảng.
STORED_PURCHASE_PROVENANCES = (
    PURCHASE_PROVENANCE_MANUAL, PURCHASE_PROVENANCE_MANUAL_OVERRIDE,
)

PRODUCT_GROUPS = ("DIEN_MAY", "GIA_DUNG")

kpi_purchase_price_override = Table(
    "kpi_purchase_price_override", METADATA,
    Column("order_key", Text, primary_key=True),
    Column("product_key", Text, primary_key=True),
    Column("occurrence_index", Integer, primary_key=True),
    _pipeline_origin_column(),
    Column("purchase_price", ExactNumeric, nullable=False),
    Column("provenance", Text, nullable=False),
    # Giá AUTO tại thời điểm Owner ghi đè. Đây KHÔNG phải lịch sử phiên bản —
    # nó là bằng chứng một dòng cho chính chữ ``MANUAL_OVERRIDE``: không có nó,
    # "override" chỉ là một cái nhãn tự khai. ``NULL`` ⟺ lúc nhập không có giá
    # AUTO nào, tức provenance phải là ``MANUAL``.
    Column("auto_price_at_entry", ExactNumeric, nullable=True),
    Column("entered_at", Text, nullable=False),
    Column("entered_by", Text, nullable=True),
    CheckConstraint(_ORIGIN_PIPELINE_CHECK, name="ck_price_override_origin"),
    CheckConstraint(_in_check("provenance", STORED_PURCHASE_PROVENANCES),
                    name="ck_price_override_provenance"),
)

product_group_classification = Table(
    "product_group_classification", METADATA,
    # Khoá theo ``product_key`` = sha256(NFC(product_raw).strip()) — CÙNG khoá
    # mà ``order_line_source_version`` dùng. Nhờ vậy một mặt hàng đã được tick
    # một lần thì mọi kỳ sau vẫn giữ phân loại đó, không phải tick lại
    # (DEC-PHB02-05: "persisted sufficiently for repeat reporting").
    Column("product_key", Text, primary_key=True),
    _pipeline_origin_column(),
    Column("product_group", Text, nullable=False),
    # Nhãn hiển thị, KHÔNG phải khoá: ``product_key`` là hash nên một danh
    # sách chỉ có hash thì không ai tick đúng được. Lấy đúng cách mà
    # ``sales_queries.product_totals`` đã nghiệm thu (``MIN(product_raw)``).
    Column("product_label", Text, nullable=True),
    Column("classified_at", Text, nullable=False),
    Column("classified_by", Text, nullable=True),
    CheckConstraint(_ORIGIN_PIPELINE_CHECK, name="ck_product_group_origin"),
    CheckConstraint(_in_check("product_group", PRODUCT_GROUPS),
                    name="ck_product_group_value"),
)

# PHB-03 REPAIR (OD-5) — Owner gán lại nhân viên cho MỘT dòng hàng.
#
# Vì sao cần một bảng riêng thay vì sửa ``order_line_result_version``: bảng đó
# APPEND-ONLY, mỗi dòng là kết quả của một lần chạy engine và là BẰNG CHỨNG KẾ
# TOÁN GỐC. Ghi đè ``employee_normalized`` ở đó sẽ xoá mất "sổ ghi ai" để thay
# bằng "Owner nghĩ là ai" — hai thứ khác nhau, và chỉ thị PHB-03 cấm việc đó
# tường minh (*"Do NOT overwrite the raw source field destructively"*).
#
# ``source_employee_at_entry`` là provenance một-cột, đúng khuôn
# ``auto_price_at_entry`` của bảng giá nhập: nó ghi lại giá trị mà pipeline
# ĐANG nói tại thời điểm Owner sửa. ``NULL`` ⟺ lúc đó dòng chưa có nhân viên
# nào (trường hợp "Chưa xác định nhân viên" thường gặp).
employee_attribution_override = Table(
    "employee_attribution_override", METADATA,
    Column("order_key", Text, primary_key=True),
    Column("product_key", Text, primary_key=True),
    Column("occurrence_index", Integer, primary_key=True),
    _pipeline_origin_column(),
    Column("employee_normalized", Text, nullable=False),
    Column("employee_group", Text, nullable=True),
    Column("source_employee_at_entry", Text, nullable=True),
    Column("assigned_at", Text, nullable=False),
    Column("assigned_by", Text, nullable=True),
    CheckConstraint(_ORIGIN_PIPELINE_CHECK, name="ck_employee_override_origin"),
    # Một tên rỗng KHÔNG phải một lần gán: nó sẽ trông như đã sửa xong trong
    # khi dòng vẫn vô chủ, và làm ô đếm "chưa xác định nhân viên" nói dối.
    CheckConstraint("length(trim(employee_normalized)) > 0",
                    name="ck_employee_override_not_blank"),
)

# PHB-05 — TARGET THÁNG CỦA MỘT NHÂN VIÊN (DEC-PHB02-06).
#
# ``DEC-PHB02-06`` đã freeze ở PHB-02: Target là số Owner tự đặt cho từng nhân
# viên, sửa được, và KHÔNG được viết cứng trong mã. Bảng này là chỗ duy nhất
# trong repo lưu được khẳng định đó.
#
# ## Vì sao một bảng riêng, khoá theo ``(năm, tháng, nhân viên)``
#
# Target KHÔNG phải một sự thật kế toán đọc ra từ sổ — nó là một dự định
# nghiệp vụ có TRƯỚC khi bán được đồng nào. Vì vậy nó không thuộc về bất kỳ
# bảng nào của đường nạp sổ:
#
# - ``order_line_*`` là dòng chứng từ; một Target không gắn với dòng hàng nào.
# - ``source_snapshot``/``snapshot_line`` thuộc vòng đời của MỘT lần nạp sổ.
#   Đặt Target vào đó thì mỗi lần nạp lại sổ kế toán, Target của Owner sẽ bị
#   một snapshot mới sở hữu — và biến mất hoặc phải nhập lại. Chỉ thị PHB-05
#   §11 gọi đúng điều này là điểm tới hạn: *"Target must NOT be owned by a
#   snapshot."*
# - Bảng ``legacy_*`` là số cũ đã đóng băng, chỉ đọc (PHB-05 §10).
#
# Khoá nghiệp vụ ``(year, month, employee_key)`` vì thế độc lập hoàn toàn với
# ``snapshot_id``/``version_id``: nạp lại sổ, sửa giá, phân giải Product
# Identity hay sửa PP đều không chạm được vào nó.
#
# ``employee_key`` DÙNG LẠI đúng danh tính nhân viên hiện hành của Current —
# tên đã chuẩn hoá (``employee_normalized``), cùng khoá mà
# ``employee_attribution_override`` và ``config/employees.yaml`` đã dùng. PHB-05
# §13 cấm dựng một hệ định danh nhân viên thứ hai, và ở đây không có cái nào
# được dựng.
#
# ## Vì sao ``0`` khác RỖNG
#
# Không có dòng ⟺ Owner CHƯA đặt target. Một dòng mang ``target_vnd = 0`` ⟺
# Owner đã cố ý đặt target bằng không. Hai điều đó dẫn tới hai câu khác nhau
# trên màn hình, nên chúng phải là hai trạng thái khác nhau trong dữ liệu —
# "gỡ target" là XOÁ DÒNG, không phải ghi số 0 (PHB-05 §7).
#
# Đơn vị lưu là VND nguyên (PHB-05 §7). Sổ cũ viết cột ``M`` theo NGHÌN ĐỒNG
# (``UNIT_SUMMARY = "kVND"``) và chính workbook đó cũng mang cả hai đơn vị cho
# CÙNG một target (``Summary 2026!M11 = 28.790.000`` kVND so với
# ``DataChart!AJ2 = 28.789.481.081`` VND) — một hệ đơn vị kép là thứ đã có sẵn
# hậu quả trong bằng chứng, nên kho lưu chỉ nhận MỘT đơn vị và tầng trình bày
# tự đổi cách viết.
employee_target = Table(
    "employee_target", METADATA,
    Column("year", Integer, primary_key=True),
    Column("month", Integer, primary_key=True),
    Column("employee_key", Text, primary_key=True),
    _pipeline_origin_column(),
    Column("target_vnd", ExactNumeric, nullable=False),
    Column("updated_at", Text, nullable=False),
    Column("updated_by", Text, nullable=True),
    CheckConstraint(_ORIGIN_PIPELINE_CHECK, name="ck_employee_target_origin"),
    CheckConstraint("month >= 1 AND month <= 12", name="ck_employee_target_month"),
    # Target âm không phải một sự thật nghiệp vụ nào; chấp nhận nó sẽ cho ra
    # một "So target" âm trông như một tỉ lệ có nghĩa.
    CheckConstraint("target_vnd >= 0", name="ck_employee_target_not_negative"),
    CheckConstraint("length(trim(employee_key)) > 0",
                    name="ck_employee_target_employee_not_blank"),
)


# ---------------------------------------------------------------------------
# EMPLOYEE WORKSPACE UX — ba quyết định MỚI của Owner (migration ``0007``).
#
# Cả ba giữ đúng khuôn đã nghiệm thu của `0003`/`0004`/`0006`: khoá NGHIỆP VỤ,
# không ``snapshot_id``/``version_id`` nào, ghi đè tại chỗ, không lịch sử
# phiên bản, không luồng duyệt. Nhờ khoá nghiệp vụ, cả ba sống sót qua một lần
# nạp lại sổ, một lần sửa giá nhập, và một lần phân giải Product Identity.
# ---------------------------------------------------------------------------

# `line_product_group_classification` — PHÂN LOẠI GIA DỤNG Ở CẤP DÒNG.
#
# ## Vì sao KHÔNG dùng lại `product_group_classification`
#
# Bảng đó khoá theo ``product_key`` duy nhất, nên nó chỉ nói được "MẶT HÀNG
# này là Gia dụng" — mọi lần bán của mọi đơn, mọi kỳ. Quyết định mới của Owner
# là ở cấp DÒNG: một BH có ba dòng, và Owner chuyển đúng MỘT dòng sang Gia
# dụng trong khi hai dòng còn lại ở lại Nội thành (`§10` của chỉ thị). Không
# có cách nào biểu diễn điều đó bằng một khoá ``product_key`` mà không nói dối
# về hai dòng kia.
#
# Đây vì thế KHÔNG phải một thẩm quyền Gia dụng thứ hai: nó là cùng một từ
# vựng (``PRODUCT_GROUPS``), cùng một hệ quả (``ConversionRateRouter`` hỏi lại
# đúng ``ConversionSchemeResolver``), chỉ khác GRAIN. Quy tắc hợp nhất được
# viết đúng một chỗ (``app/web/business_queries.effective_product_group``):
# quyết định cấp DÒNG cụ thể hơn nên thắng quyết định cấp mặt hàng.
line_product_group_classification = Table(
    "line_product_group_classification", METADATA,
    Column("order_key", Text, primary_key=True),
    Column("product_key", Text, primary_key=True),
    Column("occurrence_index", Integer, primary_key=True),
    _pipeline_origin_column(),
    Column("product_group", Text, nullable=False),
    Column("classified_at", Text, nullable=False),
    Column("classified_by", Text, nullable=True),
    CheckConstraint(_ORIGIN_PIPELINE_CHECK, name="ck_line_product_group_origin"),
    CheckConstraint(_in_check("product_group", PRODUCT_GROUPS),
                    name="ck_line_product_group_value"),
)

# `line_exclusion` — LOẠI MỘT DÒNG KHỎI TOÀN BỘ BÁO CÁO NGHIỆP VỤ.
#
# Owner quyết định: cái nút hình thùng rác nghĩa là "dòng này không được tính
# vào báo cáo nữa" (`§30`). Nhưng nó KHÔNG được xoá bằng chứng kế toán gốc
# (`§31`): ``order_line_source_version``/``order_line_result_version`` là bản
# ghi append-only của một lần nạp sổ, và xoá một dòng ở đó là xoá dấu vết sổ
# đã ghi gì.
#
# Vì vậy đây là một quyết định CÓ THỂ ĐẢO NGƯỢC nằm cạnh dữ liệu, đúng khuôn
# ba bảng override đã có: sự TỒN TẠI của một dòng ở đây ⟺ dòng nghiệp vụ
# tương ứng bị loại khỏi mọi phép gộp; xoá dòng ở đây ⟺ khôi phục. Không cột
# ``active``/``deleted_at`` nào — một cột trạng thái mở đường cho "đã xoá
# nhưng vẫn còn tính", tức là đúng lớp lỗi mà bảng này sinh ra để đóng.
line_exclusion = Table(
    "line_exclusion", METADATA,
    Column("order_key", Text, primary_key=True),
    Column("product_key", Text, primary_key=True),
    Column("occurrence_index", Integer, primary_key=True),
    _pipeline_origin_column(),
    # Ghi chú tuỳ chọn của Owner. KHÔNG tham gia phép tính nào.
    Column("reason", Text, nullable=True),
    Column("excluded_at", Text, nullable=False),
    Column("excluded_by", Text, nullable=True),
    CheckConstraint(_ORIGIN_PIPELINE_CHECK, name="ck_line_exclusion_origin"),
)

# `group_target` — TARGET THÁNG CỦA MỘT NHÓM BÁO CÁO (`§7`, `§13`, `§43`).
#
# ## Vì sao KHÔNG nhét "Nội thành" vào `employee_target`
#
# ``employee_target.employee_key`` dùng lại danh tính nhân viên hiện hành, và
# `config/employees.yaml` nói thẳng rằng gộp Vinh · Quý · Hiệp thành một
# "Employee" tên "Nội thành" là cách đã LÀM MẤT danh tính nhân viên có thật
# (DEC-127 §1). Ghi một dòng ``employee_key = 'Nội thành'`` sẽ dựng lại đúng
# cái mô hình danh tính giả đó, và mọi màn hình đọc `employee_target` sẽ thấy
# một "nhân viên" không tồn tại.
#
# ``group_target`` vì thế là bảng ANH EM, không phải bảng thay thế: cùng khoá
# ``(year, month, …)``, cùng đơn vị VND, cùng quy ước "không có dòng = chưa
# thiết lập, ``0`` = đã đặt bằng không". Khác đúng một điều — chủ thể của con
# số là một NHÓM BÁO CÁO, và điều đó được nói ra bằng tên bảng và tên cột chứ
# không bằng một quy ước ngầm trong dữ liệu.
#
# Target của nhóm là con số Owner tự đặt: nó KHÔNG bao giờ được suy ra bằng
# cách cộng target của Vinh · Quý · Hiệp (`§7`), đúng cùng lý do mà
# `TARGET_COMPANY_DEFERRED_NOTE` đã nói cho cấp công ty.
group_target = Table(
    "group_target", METADATA,
    Column("year", Integer, primary_key=True),
    Column("month", Integer, primary_key=True),
    # Khoá của NHÓM BÁO CÁO (``NOI_THANH`` · ``GIA_DUNG``), không phải tên
    # người. Từ vựng nằm ở ``app/modules/reporting/reporting_sheets.py``.
    Column("group_key", Text, primary_key=True),
    _pipeline_origin_column(),
    Column("target_vnd", ExactNumeric, nullable=False),
    Column("updated_at", Text, nullable=False),
    Column("updated_by", Text, nullable=True),
    CheckConstraint(_ORIGIN_PIPELINE_CHECK, name="ck_group_target_origin"),
    CheckConstraint("month >= 1 AND month <= 12", name="ck_group_target_month"),
    CheckConstraint("target_vnd >= 0", name="ck_group_target_not_negative"),
    CheckConstraint("length(trim(group_key)) > 0",
                    name="ck_group_target_group_not_blank"),
)

# Thứ tự tạo/xoá tường minh cho migration 0003/0004. Không FK nào trỏ ra
# ngoài: cả ba bảng là quyết định của con người trên một KHOÁ NGHIỆP VỤ, và
# khoá đó phải sống sót qua một lần re-import làm đổi ``id`` của version.
BUSINESS_TABLES = (kpi_purchase_price_override, product_group_classification)
EMPLOYEE_TABLES = (employee_attribution_override,)
TARGET_TABLES = (employee_target,)
# Thứ tự tạo/xoá tường minh cho migration 0007.
WORKSPACE_TABLES = (
    line_product_group_classification, line_exclusion, group_target,
)

# ---------------------------------------------------------------------------
# B04 — ROLLBACK KHÔNG ĐƯỢC XOÁ DỮ LIỆU OWNER TỰ NHẬP
# ---------------------------------------------------------------------------
# Bốn bảng dưới đây chứa thứ DUY NHẤT trong toàn bộ database không tái tạo
# lại được: giá nhập Owner gõ tay, tick Gia dụng, việc gán nhân viên, và
# Target tháng của từng nhân viên. Chạy lại pipeline dựng lại được mọi bảng
# khác từ file sổ gốc — nhưng không dựng lại được những con số này, vì chúng ở
# trong đầu Owner chứ không ở trong file.
#
# ``downgrade()`` của migration vì thế KHÔNG được ``DROP TABLE`` thẳng. Cơ chế
# nhỏ nhất đủ an toàn cho production: trước khi xoá, sao nguyên nội dung sang
# một bảng lưu tạm cùng database; ``upgrade()`` sau đó nạp lại. Không backup
# subsystem, không file dump, không dịch vụ mới — một câu ``CREATE TABLE AS
# SELECT`` chạy được trên cả SQLite lẫn PostgreSQL (ADR-108).
OWNER_INPUT_TABLES = (
    BUSINESS_TABLES + EMPLOYEE_TABLES + TARGET_TABLES + WORKSPACE_TABLES
)

#: Hậu tố của bảng lưu tạm. Nó nằm NGOÀI ``METADATA`` một cách có chủ đích:
#: đây không phải một bảng của lược đồ, nó là một cái két chỉ tồn tại giữa một
#: lần rollback và lần nâng cấp lại.
OWNER_BACKUP_SUFFIX = "__owner_backup"


def owner_backup_name(table_name: str) -> str:
    return f"{table_name}{OWNER_BACKUP_SUFFIX}"
