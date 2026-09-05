"""0005_legacy_source_authority — thẩm quyền nguồn của một bản nhập legacy.

Revision ID: 0005_legacy_source_authority
Revises: 0004_employee_attribution

Migration ADDITIVE thuần và là loại nhẹ nhất trong repo này: MỘT cột
nullable trên MỘT bảng. Không bảng mới, không backfill, không đọc dữ liệu
cũ, không đụng một dòng nào đang có.

## Vì sao cần một cột thay vì suy ra

`DEC-178` (chủ dự án) chốt: workbook lịch sử một năm độc lập là nguồn CHUẨN
cho năm đó, và bản sao `Summary <năm>` nhúng trong workbook năm hiện hành
chỉ là bằng chứng THỨ CẤP; khi hai bên lệch nhau thì bản độc lập thắng, và
hệ thống KHÔNG BAO GIỜ được để bản thứ cấp âm thầm thay thế bản chuẩn.

Repo chưa có chỗ nào ghi được khẳng định đó. `is_current` là con trỏ MỘT bản
"đang xem" cho toàn bộ history, không phải thẩm quyền THEO NĂM — dùng nó sẽ
khiến việc nhập workbook 2025 làm biến mất dữ liệu 2026, và ngược lại.
`version_label`/`notes` là văn bản tự do do người dùng gõ; giải quyết một quy
tắc thẩm quyền bằng cách so chuỗi tự do là để một quyết định của chủ dự án
phụ thuộc vào lỗi chính tả.

Suy từ tên sheet cũng bị bác: nó biến thẩm quyền thành một hệ quả tình cờ của
cách đặt tên, đúng kiểu ngầm định mà `DEC-178` cấm.

Vì vậy: một cột `TEXT NULL` mang đúng một trong hai giá trị, do tầng parser
xác định tại thời điểm đọc file. NULL = bản nhập có trước quyết định này,
đọc như `WORKBOOK_SNAPSHOT` — nên các bản nhập cũ giữ nguyên hành vi.

## Vì sao `upgrade()` phải kiểm tra trước khi thêm

`0001_legacy` dựng bảng từ `schema.METADATA` — nguồn DDL DUY NHẤT của repo
này (xem đầu `tools/db/schema.py`). Nên trên một database DỰNG MỚI hôm nay,
`legacy_import` đã có sẵn cột này ngay từ `0001`, và `0005` không còn gì để
thêm. Trên database ĐANG CHẠY (dựng khi `METADATA` chưa có cột), `0001` đã
chạy từ lâu và `0005` chính là chỗ cột được thêm vào.

Hai đường đó phải cùng dẫn tới một schema, nên `upgrade()` hỏi database xem
cột đã tồn tại chưa thay vì giả định. Đây KHÔNG phải nuốt lỗi: điều kiện được
hỏi là một sự thật của schema, không phải một exception bị bỏ qua.

## Rollback

`downgrade()` xoá cột. KHÔNG cần cất dữ liệu như `0003`/`0004`: giá trị của
cột này được TÁI TẠO ĐƯỢC hoàn toàn từ chính file workbook khi nhập lại —
nó là một phân loại do máy suy ra, không phải một quyết định của con người
nhập tay. SQLite cũ không có `DROP COLUMN`, nên dùng batch mode để alembic
tự dựng lại bảng khi cần.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_legacy_source_authority"
down_revision = "0004_employee_attribution"
branch_labels = None
depends_on = None

_TABLE = "legacy_import"
_COLUMN = "source_authority"


def _has_column(bind) -> bool:
    return _COLUMN in {
        column["name"] for column in sa.inspect(bind).get_columns(_TABLE)
    }


def upgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind):
        print(f"0005_legacy_source_authority: {_TABLE}.{_COLUMN} đã có sẵn "
              "(database dựng mới từ METADATA) — không thêm lại.")
        return
    op.add_column(_TABLE, sa.Column(_COLUMN, sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    if not _has_column(bind):
        return
    with op.batch_alter_table(_TABLE) as batch:
        batch.drop_column(_COLUMN)
