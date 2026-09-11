"""0008_purchase_price_reason — lý do của một quyết định giá nhập tay (R2 §4.4).

Revision ID: 0008_purchase_price_reason
Revises: 0007_employee_workspace

Migration ADDITIVE thuần, và nhỏ nhất có thể: THÊM ĐÚNG MỘT cột nullable
``reason`` vào ``kpi_purchase_price_override``. Không bảng mới, không backfill,
không đọc và không sửa một dòng dữ liệu nào đã có.

## Vì sao mở rộng bảng cũ chứ không dựng bảng mới

`R2 Execution Brief` §Gói 3 nói thẳng: "ưu tiên mở rộng bảng hiện có thay vì
tạo bảng mới". Lý do không phải tiết kiệm: một bảng ``kpi_purchase_price_
override_reason`` khoá theo cùng ba cột sẽ là một khoá thứ hai cho cùng một
quyết định, và hai bản ghi lệch nhau về cùng một dòng là chuyện SẼ xảy ra —
gỡ giá xoá bản ghi ở bảng này mà bỏ sót bảng kia là đủ.

Lý do đi CÙNG con số, trong cùng một bản ghi, cam kết cùng một lượt ghi.

## Vì sao ``nullable=True``

Mọi override đã ghi trước R2 không có lý do, và không có nơi nào để lấy lại.
Một ``NOT NULL`` ở đây buộc phải bịa một chuỗi cho chúng — tức ghi vào audit
trail một câu mà không người nào từng nói. Ràng buộc "lý do BẮT BUỘC khi thay
một giá AUTO" là một luật NGHIỆP VỤ và nó sống ở
``BusinessDecisionStore.set_purchase_price``, nơi duy nhất biết được lần ghi
này là ``MANUAL`` hay ``MANUAL_OVERRIDE``.

## Rollback (B04)

``downgrade()`` chỉ bỏ cột ``reason``; nó KHÔNG đụng tới ``purchase_price``,
``provenance``, ``auto_price_at_entry``, ``entered_at`` hay ``entered_by``.
Nghĩa là toàn bộ giá nhập Owner đã gõ tay — thứ duy nhất trong database không
tái tạo lại được từ file sổ gốc — vẫn nguyên vẹn sau một lần hạ cấp. Chỉ phần
văn bản giải thích mất đi, và đó là mất mát chấp nhận được của một rollback;
mất con số thì không.

SQLite cũ không có ``DROP COLUMN``; batch mode của Alembic lo phần đó, còn
trên PostgreSQL (production) câu lệnh chạy thẳng.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008_purchase_price_reason"
down_revision = "0007_employee_workspace"
branch_labels = None
depends_on = None

_TABLE = "kpi_purchase_price_override"
_COLUMN = "reason"


def _has_column(bind) -> bool:
    names = {column["name"] for column in sa.inspect(bind).get_columns(_TABLE)}
    return _COLUMN in names


def upgrade() -> None:
    bind = op.get_bind()
    # `checkfirst` bằng tay: migration này phải chạy lại được trên một database
    # đã có cột (ví dụ vừa được `METADATA.create_all` dựng từ schema hiện tại
    # trong test), thay vì đổ vỡ vì một cột đã đúng như mong muốn.
    if not _has_column(bind):
        op.add_column(_TABLE, sa.Column(_COLUMN, sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind):
        with op.batch_alter_table(_TABLE) as batch:
            batch.drop_column(_COLUMN)
