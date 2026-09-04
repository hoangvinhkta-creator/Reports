"""0003_business — hai bảng quyết định-của-người của PHB-03.

Revision ID: 0003_business
Revises: 0002_snapshots

Migration ADDITIVE thuần, đúng khuôn của ``0002_snapshots``: không đổi một cột
nào của mười bảng đã có, không backfill, không đọc dữ liệu cũ. Dữ liệu
LEGACY_REFERENCE và PIPELINE_GENERATED đang chạy trên production đi qua
migration này nguyên vẹn.

Hai bảng mới KHÔNG mang FK trỏ sang ``order_line_current``/
``order_line_source_version``: chúng khoá theo KHOÁ NGHIỆP VỤ
(``order_key``/``product_key``/``occurrence_index`` và ``product_key``), vốn
phải sống sót qua một lần re-import làm sinh ``id`` version mới. Một FK ở đây
sẽ biến "kế toán gửi lại sổ" thành "mất quyết định của Owner".
"""

from __future__ import annotations

from alembic import op

from tools.db import schema

revision = "0003_business"
down_revision = "0002_snapshots"
branch_labels = None
depends_on = None

_TABLES = schema.BUSINESS_TABLES


def upgrade() -> None:
    schema.METADATA.create_all(op.get_bind(), tables=list(_TABLES), checkfirst=False)


def downgrade() -> None:
    schema.METADATA.drop_all(op.get_bind(), tables=list(reversed(_TABLES)), checkfirst=False)
