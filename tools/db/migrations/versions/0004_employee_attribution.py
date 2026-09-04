"""0004_employee_attribution — Owner gán lại nhân viên cho một dòng hàng.

Revision ID: 0004_employee_attribution
Revises: 0003_business

Migration ADDITIVE thuần, đúng khuôn `0003_business`: một bảng mới, không đổi
một cột nào của các bảng đã có, không backfill, không đọc dữ liệu cũ.

## Vì sao cần một bảng thay vì sửa dữ liệu sẵn có

`OD-5` yêu cầu một kết quả cụ thể: dòng "Chưa xác định nhân viên" phải gán
được cho một người, và sau khi lưu thì nó rời khỏi nhóm chưa xác định, hiện
trong trang của người đó, và KPI cập nhật theo — mà **không** phải nạp lại sổ.

Trong repo không có sẵn chỗ nào lưu được khẳng định đó. `order_line_result_version`
là APPEND-ONLY và là bằng chứng kế toán gốc ("sổ ghi tên ai"); ghi đè
`employee_normalized` ở đó sẽ xoá bằng chứng để thay bằng ý kiến, và chỉ thị
PHB-03 cấm việc đó tường minh. `kpi_purchase_price_override` là giá nhập, ngữ
nghĩa khác hẳn.

Vì vậy đây là trường hợp "strictly unavoidable" của chỉ thị: một bảng, ba khoá
nghiệp vụ, một tên nhân viên, và một cột provenance. Không hệ thống sửa đơn
tổng quát, không luồng duyệt, không lịch sử phiên bản.

## Rollback (B04)

`downgrade()` cất dữ liệu vào bảng lưu tạm trước khi xoá, và `upgrade()` nạp
lại — cùng cơ chế `tools/db/owner_data.py` mà `0003_business` dùng. Việc gán
nhân viên là quyết định của con người, không tái tạo lại được từ file sổ nào.
"""

from __future__ import annotations

from alembic import op

from tools.db import owner_data, schema

revision = "0004_employee_attribution"
down_revision = "0003_business"
branch_labels = None
depends_on = None

_TABLES = schema.EMPLOYEE_TABLES


def upgrade() -> None:
    bind = op.get_bind()
    schema.METADATA.create_all(bind, tables=list(_TABLES), checkfirst=False)
    for name, rows in owner_data.restore_owner_tables(bind, _TABLES):
        print(f"0004_employee_attribution: đã nạp lại {rows} dòng Owner vào {name}.")


def downgrade() -> None:
    bind = op.get_bind()
    for name, backup, rows in owner_data.archive_owner_tables(bind, _TABLES):
        print(f"0004_employee_attribution: giữ lại {rows} dòng của {name} "
              f"trong {backup} — `alembic upgrade` sẽ nạp lại.")
    schema.METADATA.drop_all(bind, tables=list(reversed(_TABLES)), checkfirst=False)
