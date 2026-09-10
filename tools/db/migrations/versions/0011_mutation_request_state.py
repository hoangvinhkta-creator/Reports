"""0011_mutation_request_state — sổ chống lặp biết cả lần ghi ĐANG BAY.

Revision ID: 0011_mutation_request_state
Revises: 0010_mutation_request

## Vì sao có bản này, ngay sau 0010

`0010` dựng `mutation_request` với `response_json NOT NULL`, và hàng chỉ
được chèn SAU khi lần ghi nghiệp vụ đã commit. Review độc lập chứng minh
được bằng probe trên PostgreSQL 16 rằng thiết kế đó KHÔNG cho at-most-once:

    cùng `request_id`, hai request đồng thời   → set_purchase_price() 2 lần
    cùng `base_revision`, hai request đồng thời → set_purchase_price() 2 lần
    crash trước khi chèn hàng                   → ghi vào DB, sổ rỗng

Nguyên nhân là hình dạng của bảng, không phải một lỗi gõ: một sổ chỉ ghi
những lần ghi ĐÃ XONG thì không biết gì về một lần ghi đang diễn ra, nên
hai request cùng thấy sổ rỗng và cùng đi tiếp.

Bản này đổi hình dạng để hàng được chèn TRƯỚC lần ghi, trong CÙNG
transaction:

    `state`          `in_flight` khi vừa nhận, `applied` khi đã ghi xong
    `response_json`  `NULL` được phép — lúc `in_flight` chưa có kết quả

Khoá chính `request_id` nhờ đó trở thành cửa loại trừ THẬT: request thứ hai
mang cùng mã va khoá chính trước khi chạm một bảng nghiệp vụ nào.

## Vì sao là 0011 chứ không sửa tại chỗ 0010

`0010` đã được đẩy lên nhánh và có thể đã chạy trên một database nào đó.
Sửa nội dung một migration đã chạy là để lại hai database cùng khai
`0010` mà có hai lược đồ khác nhau — và không có cách nào phát hiện điều
đó về sau. Một bản mới thì mọi database, dù đã ở `0010` hay chưa, đều đi
tới cùng một đích.

## Vì sao `downgrade()` xoá các hàng `in_flight`

Hạ cấp về `0010` đòi `response_json NOT NULL`, và một hàng `in_flight`
theo định nghĩa chưa có kết quả. Không có gì để điền vào đó: bịa một
payload rỗng sẽ khiến một lần THỬ LẠI nhận về "đã ghi rồi" kèm một kết quả
không nói gì.

Xoá chúng là an toàn, và lý do cần được nói ra: một hàng `in_flight` chỉ
tồn tại BÊN TRONG một transaction đang chạy. Sau khi transaction ấy kết
thúc — commit hay rollback — không còn hàng `in_flight` nào. Nên tập bị
xoá ở đây chỉ khác rỗng nếu ai đó hạ cấp đúng lúc một request đang bay, và
request đó sẽ rollback.

## Rollback (B04)

Bảng này KHÔNG nằm trong `OWNER_INPUT_TABLES` — xem `0010` § "Vì sao KHÔNG
nằm trong OWNER_INPUT_TABLES". Nội dung nó tái tạo được và mất nó không
mất một con số nghiệp vụ nào.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011_mutation_request_state"
down_revision = "0010_mutation_request"
branch_labels = None
depends_on = None

_TABLE = "mutation_request"
_STATE = "state"
_CHECK = "ck_mutation_request_state"


def _columns(bind) -> dict:
    return {column["name"]: column for column in
            sa.inspect(bind).get_columns(_TABLE)}


def upgrade() -> None:
    bind = op.get_bind()
    columns = _columns(bind)

    # `checkfirst` bằng tay, cùng lý do như 0008/0010: migration phải chạy
    # lại được trên một database đã đúng hình dạng (ví dụ vừa được
    # `METADATA.create_all` dựng từ schema hiện tại trong test).
    if _STATE not in columns:
        # `server_default` cho các hàng ĐÃ CÓ: chúng đến từ `0010`, nơi hàng
        # chỉ được chèn sau khi ghi xong — nên `applied` là sự thật về
        # chúng, không phải một giá trị mặc định tiện tay.
        op.add_column(_TABLE, sa.Column(
            _STATE, sa.Text(), nullable=False, server_default="applied"))
        # Gỡ `server_default` sau khi lấp: từ nay mọi lần chèn phải NÓI RÕ
        # trạng thái. Một default ở tầng cột sẽ làm một lần chèn quên khai
        # `state` âm thầm trở thành `applied` — tức một lần ghi đang bay
        # được ghi nhận là đã xong.
        with op.batch_alter_table(_TABLE) as batch:
            batch.alter_column(_STATE, server_default=None)

    # `response_json` nullable: `in_flight` chưa có kết quả để lưu.
    if columns.get("response_json", {}).get("nullable") is False:
        with op.batch_alter_table(_TABLE) as batch:
            batch.alter_column("response_json", existing_type=sa.Text(),
                               nullable=True)

    # CHECK cho tập trạng thái. SQLite không liệt kê CHECK ràng buộc theo
    # tên qua `inspect`, nên trên SQLite ta dựng lại bảng qua batch mode;
    # trên PostgreSQL câu lệnh chạy thẳng và bỏ qua nếu đã có.
    existing = {check.get("name") for check in
                sa.inspect(bind).get_check_constraints(_TABLE)}
    if _CHECK not in existing:
        with op.batch_alter_table(_TABLE) as batch:
            batch.create_check_constraint(
                _CHECK, "state IN ('in_flight', 'applied')")


def downgrade() -> None:
    bind = op.get_bind()
    columns = _columns(bind)

    # Xem docstring § "Vì sao downgrade() xoá các hàng in_flight".
    if _STATE in columns:
        op.execute(sa.text(
            f"DELETE FROM {_TABLE} WHERE {_STATE} = 'in_flight'"))

    existing = {check.get("name") for check in
                sa.inspect(bind).get_check_constraints(_TABLE)}
    if _CHECK in existing:
        with op.batch_alter_table(_TABLE) as batch:
            batch.drop_constraint(_CHECK, type_="check")

    if _STATE in columns:
        with op.batch_alter_table(_TABLE) as batch:
            batch.drop_column(_STATE)

    if columns.get("response_json", {}).get("nullable") is True:
        with op.batch_alter_table(_TABLE) as batch:
            batch.alter_column("response_json", existing_type=sa.Text(),
                               nullable=False)
