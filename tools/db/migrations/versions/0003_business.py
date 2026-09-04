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

from tools.db import owner_data, schema

revision = "0003_business"
down_revision = "0002_snapshots"
branch_labels = None
depends_on = None

_TABLES = schema.BUSINESS_TABLES


def upgrade() -> None:
    bind = op.get_bind()
    schema.METADATA.create_all(bind, tables=list(_TABLES), checkfirst=False)
    # B04 — nếu một lần rollback trước đó đã cất dữ liệu Owner vào két, nạp
    # lại ngay tại đây. Không có két thì đây là no-op.
    for name, rows in owner_data.restore_owner_tables(bind, _TABLES):
        print(f"0003_business: đã nạp lại {rows} dòng Owner vào {name}.")


def downgrade() -> None:
    """B04 — KHÔNG `DROP` thẳng: hai bảng này chứa dữ liệu Owner gõ tay.

    Giá nhập và tick Gia dụng không tái tạo lại được từ file sổ gốc. Xoá
    chúng để quay lại `0002_snapshots` là một mất mát vĩnh viễn, và một lệnh
    rollback thường được gõ vội lúc đang có sự cố khác — đúng lúc không ai
    kịp nghĩ tới hậu quả đó.
    """
    bind = op.get_bind()
    for name, backup, rows in owner_data.archive_owner_tables(bind, _TABLES):
        print(f"0003_business: giữ lại {rows} dòng của {name} trong {backup} "
              f"— `alembic upgrade` sẽ nạp lại.")
    schema.METADATA.drop_all(bind, tables=list(reversed(_TABLES)), checkfirst=False)
