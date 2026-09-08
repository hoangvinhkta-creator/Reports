"""0009_line_binding_and_period_close — hai bảng của R3 (§1 và §5).

Revision ID: 0009_line_binding_and_period_close
Revises: 0008_purchase_price_reason

Migration ADDITIVE thuần: tạo ĐÚNG hai bảng mới, không thêm/sửa/xoá một cột
nào của bảng đang có, không backfill, không đọc một dòng dữ liệu cũ nào.

``line_binding_exception`` (R3 §1)
    Nơi ghi những chỗ hệ thống TỪ CHỐI đoán khi gắn dòng của một sổ đã sửa
    vào khoá dòng đã có. Nó là bằng chứng DẪN XUẤT — nạp lại sổ thì dựng lại
    được — nên ``downgrade()`` xoá thẳng, không cần cất giữ.

``period_close`` (R3 §5)
    Một lần chốt kỳ là một QUYẾT ĐỊNH của Owner, và không có chỗ nào khác lấy
    lại được nó: chạy lại pipeline từ file sổ gốc không dựng lại được "tháng
    01 đã được duyệt ngày nào, bởi ai, trên bộ số nào". Vì vậy bảng này thuộc
    ``OWNER_INPUT_TABLES`` và ``downgrade()`` phải đi qua đúng cơ chế B04:
    cất nội dung sang bảng lưu tạm TRƯỚC khi xoá, ``upgrade()`` nạp lại.

## Vì sao không đổi CHECK constraint của ``reconciliation_flag``

Cách rẻ hơn về số dòng code là thêm một ``kind`` mới vào bảng cờ đã có. Không
chọn cách đó vì hai lý do, và lý do thứ hai là lý do thật:

1. Trên SQLite, đổi một CHECK constraint đòi dựng lại cả bảng
   (``batch_alter_table(recreate="always")``) — một thao tác ghi lại toàn bộ
   lịch sử đối soát, để đổi lấy một dòng từ vựng.
2. Ngữ nghĩa không khớp. ``reconciliation_flag`` là bằng chứng append-only
   của một lần chạy ("snapshot này đã thấy điều đó"), còn một ngoại lệ gắn
   dòng là VIỆC CÒN TREO của con người, có vòng đời mở → đã xử lý. Cột
   ``acknowledged_at`` ở bảng cờ nghĩa là "đã đọc", không phải "đã xử lý", và
   mượn nó sẽ làm hai khái niệm khác nhau dùng chung một cột.
"""

from __future__ import annotations

from alembic import op

from tools.db import owner_data, schema

revision = "0009_line_binding_and_period_close"
down_revision = "0008_purchase_price_reason"
branch_labels = None
depends_on = None

#: Bảng dẫn xuất — xoá được, dựng lại bằng một lần nạp sổ.
_DERIVED_TABLES = (schema.line_binding_exception,)
#: Bảng chứa quyết định của người — KHÔNG được xoá thẳng (B04).
_OWNER_TABLES = (schema.period_close,)

_ALL = _DERIVED_TABLES + _OWNER_TABLES


def upgrade() -> None:
    bind = op.get_bind()
    schema.METADATA.create_all(bind, tables=list(_ALL), checkfirst=True)
    for name, rows in owner_data.restore_owner_tables(bind, _OWNER_TABLES):
        print(f"0009_line_binding_and_period_close: đã nạp lại {rows} dòng "
              f"Owner vào {name}.")


def downgrade() -> None:
    bind = op.get_bind()
    for name, backup, rows in owner_data.archive_owner_tables(bind, _OWNER_TABLES):
        print(f"0009_line_binding_and_period_close: giữ lại {rows} dòng của "
              f"{name} trong {backup} — `alembic upgrade` sẽ nạp lại.")
    schema.METADATA.drop_all(bind, tables=list(reversed(_ALL)), checkfirst=True)
