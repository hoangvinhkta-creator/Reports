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
