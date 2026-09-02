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
    Boolean, CheckConstraint, Column, ForeignKey, Integer, MetaData,
    Numeric, Table, Text, TypeDecorator, UniqueConstraint,
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
