"""0001_legacy — bốn bảng LEGACY_REFERENCE của TASK-PRA-001.

Revision ID: 0001_legacy
Revises:
"""

from __future__ import annotations

from alembic import op

from tools.db import schema

revision = "0001_legacy"
down_revision = None
branch_labels = None
depends_on = None

# Thứ tự tạo/xoá tường minh (FK legacy_import ← ba bảng fact) để migration
# deterministic trên cả SQLite lẫn PostgreSQL, không phụ thuộc thứ tự sắp xếp
# nội bộ của SQLAlchemy.
_TABLES = (
    schema.legacy_import,
    schema.legacy_summary_row,
    schema.legacy_daily_sales,
    schema.legacy_monthly_reference,
)


def upgrade() -> None:
    # DDL sinh từ chính ``schema.METADATA`` — nguồn DDL duy nhất, nên schema
    # thật và định nghĩa mà repository đọc không thể trôi khỏi nhau.
    schema.METADATA.create_all(op.get_bind(), tables=list(_TABLES), checkfirst=False)


def downgrade() -> None:
    schema.METADATA.drop_all(op.get_bind(), tables=list(reversed(_TABLES)), checkfirst=False)
