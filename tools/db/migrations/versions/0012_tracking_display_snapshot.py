"""0012_tracking_display_snapshot — nhãn hiển thị Tracking sống qua restart.

Revision ID: 0012_tracking_display_snapshot
Revises: 0011_mutation_request_state

Migration ADDITIVE thuần: THÊM ĐÚNG MỘT bảng mới. Không cột nào của bảng cũ
bị đụng, không dòng dữ liệu nào được đọc hay sửa, không backfill.

## Vấn đề bảng này đóng (`R5.3`)

`R5.1 REPAIR-2` đã bắt `POST /run` ghi bản chiếu hiển thị (`mã Tracking →
model · hãng · nhóm hàng`) từ capture Tracking của chính lần chạy đó. Nhưng
nó ghi ra MỘT FILE trên đĩa máy chủ, và trên Render đĩa ấy là ephemeral: mỗi
lần deploy/restart file biến mất. Con số của kỳ thì không — chúng nằm ở đúng
database này.

Đo trực tiếp trên đường thật (`R5.3` §Audit): chạy báo cáo ⟹ tab Nhân viên
hiện `QLED 55Q6FA` / `Samsung` / `Tivi`; xoá đĩa ephemeral (đúng cái Render
làm) ⟹ CÙNG lần chạy ấy hiện `—` ở cả Hãng lẫn Nhóm hàng, VĨNH VIỄN, vì
không đường nào dựng lại được bản chiếu. Đó là triệu chứng production mà
Owner báo.

Bảng này là nửa BỀN của chính bản chiếu ấy: một hàng cho mỗi `run_id`, mang
nguyên văn những gì capture của lần chạy đó nói. Khi file trên đĩa vắng mặt,
tầng trình bày dựng lại bản chiếu TỪ ĐÂY — không gọi Tracking lần nào, không
suy một chữ nào từ tên trên sổ kế toán.

## Vì sao mở một bảng MỚI thay vì nhồi vào `source_snapshot`

`source_snapshot` là bản ghi ĐỐI CHIẾU của một lần nạp sổ: mọi cột của nó
tham gia coverage/reconcile, và `evidence_json` của nó là bằng chứng về CHÍNH
phép đối chiếu ấy. Nhãn hiển thị không thuộc phép đối chiếu nào — nó không có
mặt trong một vân tay nào, không đổi một `outcome` nào. Nhét nó vào đó sẽ làm
một trường hiển thị trở thành một phần của bản ghi đối chiếu, và một lần ghi
nhãn thất bại sẽ rollback cả một lần nạp sổ đã đúng.

Ngược lại, đây KHÔNG phải một danh mục thứ hai của Reports: không đường
resolve nào đọc bảng này, không dòng nào trong nó được suy ra, và nó không
mang tiền (`app/web/catalog_display.py` § Đây KHÔNG phải một bảng danh mục).

## Vì sao KHÔNG nằm trong `OWNER_INPUT_TABLES`

Cùng lý lẽ như `0010_mutation_request`: nội dung ở đây TÁI TẠO ĐƯỢC — chạy
lại báo cáo là dựng lại nó từ capture mới — và mất nó không mất một con số
nào. Cái mất đi khi rollback được nói ra thay vì để im: cột Hãng/Nhóm hàng
quay lại phụ thuộc một mình file trên đĩa ephemeral cho tới lần nâng cấp lại,
tức đúng hành vi `R5.1 REPAIR-2`. Không đồng nào sai vì điều đó.

## Rollback (B04)

`downgrade()` `DROP TABLE` thẳng — bảng không chứa dữ liệu Owner. Cơ chế
`owner_backup_name()` của các bảng quyết định không áp dụng, xem đoạn trên.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0012_tracking_display_snapshot"
down_revision = "0011_mutation_request_state"
branch_labels = None
depends_on = None

_TABLE = "tracking_display_snapshot"
_INDEX = "ix_tracking_display_created_at"


def _exists(bind) -> bool:
    return _TABLE in sa.inspect(bind).get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    # `checkfirst` bằng tay, cùng lý do như 0008/0010: migration phải chạy lại
    # được trên một database đã có bảng (ví dụ vừa được `METADATA.create_all`
    # dựng từ schema hiện tại trong test), thay vì đổ vỡ vì một bảng đã đúng
    # như mong muốn.
    if _exists(bind):
        return
    op.create_table(
        _TABLE,
        sa.Column("run_id", sa.Text(), primary_key=True),
        sa.Column("capture_id", sa.Text(), nullable=True),
        sa.Column("captured_at", sa.Text(), nullable=True),
        sa.Column("rows_json", sa.Text(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False,
                  server_default="0"),
        sa.Column("created_at", sa.Text(), nullable=False),
    )
    op.create_index(_INDEX, _TABLE, ["created_at"])


def downgrade() -> None:
    bind = op.get_bind()
    if not _exists(bind):
        return
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes(_TABLE)}
    if _INDEX in indexes:
        op.drop_index(_INDEX, table_name=_TABLE)
    op.drop_table(_TABLE)
