"""0002_snapshots — sáu bảng PIPELINE_GENERATED của TASK-PRA-002.

Revision ID: 0002_snapshots
Revises: 0001_legacy

Migration ADDITIVE thuần: không đổi một cột nào của bốn bảng ``legacy_*``,
không backfill, không đọc dữ liệu cũ. Dữ liệu PRA-001 đang có trên production
đi qua migration này nguyên vẹn — điều kiện bắt buộc của TASK-PRA-002 mục 13.
"""

from __future__ import annotations

from alembic import op

from tools.db import schema

revision = "0002_snapshots"
down_revision = "0001_legacy"
branch_labels = None
depends_on = None

_TABLES = schema.PIPELINE_TABLES


def upgrade() -> None:
    # DDL sinh từ chính ``schema.METADATA`` — cùng nguồn duy nhất mà
    # ``SnapshotRepository`` đọc, nên schema thật không trôi khỏi định nghĩa.
    schema.METADATA.create_all(op.get_bind(), tables=list(_TABLES), checkfirst=False)


def downgrade() -> None:
    schema.METADATA.drop_all(op.get_bind(), tables=list(reversed(_TABLES)), checkfirst=False)
