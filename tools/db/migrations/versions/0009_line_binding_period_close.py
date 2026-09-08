"""0009_line_binding_period_close — hai bảng của R3 (§1 và §5).

Revision ID: 0009_line_binding_period_close
Revises: 0008_purchase_price_reason

Migration ADDITIVE thuần: tạo ĐÚNG hai bảng mới, không thêm/sửa/xoá một cột
nào của bảng đang có, không backfill, không đọc một dòng dữ liệu cũ nào.

Revision ID dài 30 ký tự để nằm trong giới hạn ``VARCHAR(32)`` mặc định của
``alembic_version.version_num`` trên PostgreSQL. Bản tên dài hơn đã khiến lần
deploy R3 đầu tiên rollback khi Alembic ghi revision sau DDL.
"""

from __future__ import annotations

from alembic import op

from tools.db import owner_data, schema

revision = "0009_line_binding_period_close"
down_revision = "0008_purchase_price_reason"
branch_labels = None
depends_on = None

_DERIVED_TABLES = (schema.line_binding_exception,)
_OWNER_TABLES = (schema.period_close,)
_ALL = _DERIVED_TABLES + _OWNER_TABLES


def upgrade() -> None:
    bind = op.get_bind()
    schema.METADATA.create_all(bind, tables=list(_ALL), checkfirst=True)
    for name, rows in owner_data.restore_owner_tables(bind, _OWNER_TABLES):
        print(f"0009_line_binding_period_close: đã nạp lại {rows} dòng Owner "
              f"vào {name}.")


def downgrade() -> None:
    bind = op.get_bind()
    for name, backup, rows in owner_data.archive_owner_tables(bind, _OWNER_TABLES):
        print(f"0009_line_binding_period_close: giữ lại {rows} dòng của "
              f"{name} trong {backup} — `alembic upgrade` sẽ nạp lại.")
    schema.METADATA.drop_all(bind, tables=list(reversed(_ALL)), checkfirst=True)
