"""0010_mutation_request — sổ chống lặp mutation (`STAB-03`).

Revision ID: 0010_mutation_request
Revises: 0009_line_binding_period_close

Migration ADDITIVE thuần: THÊM ĐÚNG MỘT bảng mới. Không cột nào của bảng
cũ bị đụng, không dòng dữ liệu nào được đọc hay sửa, không backfill.

## Vấn đề bảng này đóng

Một lần POST có thể được server ghi xong rồi response thất lạc trên đường
về (mạng đứt, proxy timeout, tab bị đóng). Browser KHÔNG phân biệt được
tình huống đó với "server chưa nhận", nên bất kỳ cơ chế nào tự gửi lại đều
có thể ghi lần thứ hai. Đó chính là lỗi `submitForm()` mang trước `STAB-03`:
nó gọi `form.submit()` trong `catch`.

Nhánh tự gửi lại đã bị gỡ, và người dùng được cho một nút THỬ LẠI gửi ĐÚNG
`request_id` cũ. Bảng này là nơi mã ấy được nhận ra: khoá chính là
`request_id`, nên lần gửi thứ hai của cùng mã không tạo hàng mới — nó ĐỌC
hàng cũ và trả lại kết quả cũ.

## Vì sao mở một bảng MỚI, trái với thói quen "mở rộng bảng hiện có"

`R2 Execution Brief` §Gói 3 ưu tiên mở rộng bảng cũ, và lý do của nó là:
hai bản ghi cho cùng MỘT quyết định sẽ lệch nhau. Ở đây không có nguy cơ
đó, vì bảng này KHÔNG ghi một quyết định nghiệp vụ nào — nó ghi một sự
kiện về VẬN CHUYỂN ("lần gửi mang mã X đã được cam kết"). Nó không có
khoá nghiệp vụ, không tham gia phép gộp nào, không đi vào vân tay chốt kỳ.

Nhồi nó vào `kpi_purchase_price_override` sẽ buộc mọi mutation KHÁC (loại
dòng, phân loại, gán nhân viên) đi qua bảng giá nhập để được chống lặp, và
đó là một phụ thuộc sai hướng.

## Vì sao KHÔNG nằm trong `OWNER_INPUT_TABLES`

`OWNER_INPUT_TABLES` là tập bảng chứa dữ liệu Owner gõ tay mà không tái
tạo lại được từ file sổ gốc, nên `downgrade()` phải sao lưu chúng. Bảng này
không thuộc tập đó: nội dung của nó tái tạo được (nó là dấu vết của những
lần ghi đã có mặt trong các bảng quyết định), và mất nó không mất một con
số nào.

Cái mất đi khi rollback được nói ra ở đây thay vì để im: một lần THỬ LẠI
đúng vào cửa sổ giữa rollback và nâng cấp lại sẽ không được nhận ra, và
nó có thể ghi lần thứ hai. Đây là một cửa sổ hẹp, trong một thao tác vận
hành có người ngồi trước máy, và đánh đổi ngược lại — sao lưu/nạp lại một
bảng nhật ký vận chuyển trong mỗi lần hạ cấp — không đáng.

## Rollback (B04)

`downgrade()` `DROP TABLE` thẳng, và đó là đúng ở đây vì bảng không chứa
dữ liệu Owner. Cơ chế `owner_backup_name()` của các bảng quyết định không
áp dụng — xem đoạn trên.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0010_mutation_request"
down_revision = "0009_line_binding_period_close"
branch_labels = None
depends_on = None

_TABLE = "mutation_request"
_INDEX = "ix_mutation_request_subject"


def _exists(bind) -> bool:
    return _TABLE in sa.inspect(bind).get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    # `checkfirst` bằng tay, cùng lý do như 0008: migration phải chạy lại
    # được trên một database đã có bảng (ví dụ vừa được
    # `METADATA.create_all` dựng từ schema hiện tại trong test), thay vì
    # đổ vỡ vì một bảng đã đúng như mong muốn.
    if _exists(bind):
        return
    op.create_table(
        _TABLE,
        sa.Column("request_id", sa.Text(), primary_key=True),
        sa.Column("route", sa.Text(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("base_revision", sa.Text(), nullable=True),
        sa.Column("response_json", sa.Text(), nullable=False),
        sa.Column("entered_at", sa.Text(), nullable=False),
        sa.Column("entered_by", sa.Text(), nullable=True),
    )
    op.create_index(_INDEX, _TABLE, ["subject", "entered_at"])


def downgrade() -> None:
    bind = op.get_bind()
    if not _exists(bind):
        return
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes(_TABLE)}
    if _INDEX in indexes:
        op.drop_index(_INDEX, table_name=_TABLE)
    op.drop_table(_TABLE)
