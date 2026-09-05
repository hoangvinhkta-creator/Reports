"""0007_employee_workspace — không gian làm việc Nhân viên (`DEC-PHB02-08`).

Revision ID: 0007_employee_workspace
Revises: 0006_employee_target

Migration ADDITIVE thuần. Nó làm đúng hai việc, và không việc nào đụng tới
một dòng dữ liệu đang có:

1. Thêm BA CỘT nullable vào ``order_line_source_version``:
   ``customer_name`` · ``customer_phone`` · ``customer_address``.
2. Tạo BA BẢNG mới của quyết định Owner: ``line_product_group_classification``
   · ``line_exclusion`` · ``group_target``.

Không backfill, không đọc dữ liệu cũ, không sửa một cột nào đã có, không đụng
snapshot hay Legacy. Ba cột mới nhận ``NULL`` trên mọi dòng đã nạp trước đây —
đó là sự thật: sổ đã nạp rồi thì thông tin khách hàng của nó không còn ở đâu
để lấy lại, và tầng trình bày viết ``—`` chứ không bịa.

## Vì sao ba cột khách hàng là ADD COLUMN chứ không phải bảng mới

Chúng là dữ liệu của chính DÒNG NGUỒN, do cùng một lần nạp sổ sinh ra, và có
cùng vòng đời version với ``product_raw``/``sell_price``. Tách sang một bảng
riêng sẽ dựng ra một khoá thứ hai cho cùng một dòng và mở đường cho hai bản
ghi lệch nhau về cùng một đơn.

Chúng KHÔNG vào ``FINGERPRINT_FIELDS``: kế toán sửa tên khách hàng không phải
là "dòng bán này đã bị sửa", nên reconcile giữ nguyên ngữ nghĩa cũ.

## Rollback (B04)

``downgrade()`` cất nội dung ba bảng quyết định vào bảng lưu tạm trước khi
xoá, và ``upgrade()`` nạp lại — cùng cơ chế ``tools/db/owner_data.py`` mà
`0003`/`0004`/`0006` dùng. Phân loại Gia dụng cấp dòng, việc loại một dòng
khỏi báo cáo và Target của nhóm đều là quyết định của con người: chạy lại
pipeline từ file sổ gốc KHÔNG dựng lại được chúng.

Ba cột khách hàng thì ngược lại — chúng ĐẾN TỪ file sổ, nên ``downgrade()``
được phép bỏ chúng: một lần nạp lại sổ dựng lại đúng giá trị đó. SQLite cũ
không có ``DROP COLUMN``; batch mode của Alembic lo phần đó và trên
PostgreSQL (production) câu lệnh chạy thẳng.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from tools.db import owner_data, schema

revision = "0007_employee_workspace"
down_revision = "0006_employee_target"
branch_labels = None
depends_on = None

_TABLES = schema.WORKSPACE_TABLES

_CUSTOMER_COLUMNS = ("customer_name", "customer_phone", "customer_address")


def _existing_customer_columns(bind) -> set[str]:
    """Cột khách hàng ĐANG có thật trong database.

    Migration phải chạy được hai lần liên tiếp mà không sập: một
    ``downgrade`` + ``upgrade`` trên production là chuyện bình thường, và
    ``ADD COLUMN`` một cột đã tồn tại là lỗi ở cả hai phương ngữ.
    """
    names = {column["name"] for column in
             sa.inspect(bind).get_columns("order_line_source_version")}
    return names & set(_CUSTOMER_COLUMNS)


def upgrade() -> None:
    bind = op.get_bind()
    present = _existing_customer_columns(bind)
    for name in _CUSTOMER_COLUMNS:
        if name not in present:
            op.add_column("order_line_source_version",
                          sa.Column(name, sa.Text(), nullable=True))

    schema.METADATA.create_all(bind, tables=list(_TABLES), checkfirst=True)
    for name, rows in owner_data.restore_owner_tables(bind, _TABLES):
        print(f"0007_employee_workspace: đã nạp lại {rows} dòng Owner vào {name}.")


def downgrade() -> None:
    bind = op.get_bind()
    for name, backup, rows in owner_data.archive_owner_tables(bind, _TABLES):
        print(f"0007_employee_workspace: giữ lại {rows} dòng của {name} "
              f"trong {backup} — `alembic upgrade` sẽ nạp lại.")
    schema.METADATA.drop_all(bind, tables=list(reversed(_TABLES)), checkfirst=True)

    present = _existing_customer_columns(bind)
    with op.batch_alter_table("order_line_source_version") as batch:
        for name in _CUSTOMER_COLUMNS:
            if name in present:
                batch.drop_column(name)
