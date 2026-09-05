"""0006_employee_target — Target tháng của một nhân viên (PHB-05, DEC-PHB02-06).

Revision ID: 0006_employee_target
Revises: 0005_legacy_source_authority

Migration ADDITIVE thuần, đúng khuôn `0003_business`/`0004_employee_attribution`:
MỘT bảng mới, không đổi một cột nào của các bảng đã có, không backfill, không
đọc dữ liệu cũ, không đụng một dòng nào của snapshot hay của Legacy.

## Vì sao cần một bảng thay vì một chỗ đã có

`DEC-PHB02-06` chốt Target là số Owner tự đặt cho từng nhân viên và KHÔNG được
viết cứng. Trong repo chưa có chỗ nào lưu được khẳng định đó:

- `kpi_purchase_price_override` là giá nhập của MỘT dòng chứng từ; Target
  không gắn với dòng hàng nào.
- `employee_attribution_override` là "dòng này của ai"; Target là "người này
  phải đạt bao nhiêu trong tháng" — khác khoá, khác ngữ nghĩa.
- `source_snapshot`/`snapshot_line` thuộc vòng đời của MỘT lần nạp sổ. Đặt
  Target vào đó là để một snapshot mới sở hữu quyết định của Owner, đúng điều
  PHB-05 §11 cấm: *"Target must NOT be owned by a snapshot."*
- Bảng `legacy_*` là số cũ đã đóng băng, chỉ đọc (PHB-05 §10).

Vì vậy đây là trường hợp "strictly unavoidable": một bảng, ba khoá nghiệp vụ
`(year, month, employee_key)`, một con số VND, và một cột thời điểm. Không
lịch sử phiên bản, không luồng duyệt, không hệ định danh nhân viên mới —
`employee_key` dùng lại đúng tên đã chuẩn hoá mà Current đang dùng.

## Rollback (B04)

`downgrade()` cất dữ liệu vào bảng lưu tạm trước khi xoá, và `upgrade()` nạp
lại — cùng cơ chế `tools/db/owner_data.py` mà `0003`/`0004` dùng. Target là
quyết định của con người, không tái tạo lại được từ file sổ nào.
"""

from __future__ import annotations

from alembic import op

from tools.db import owner_data, schema

revision = "0006_employee_target"
down_revision = "0005_legacy_source_authority"
branch_labels = None
depends_on = None

_TABLES = schema.TARGET_TABLES


def upgrade() -> None:
    bind = op.get_bind()
    schema.METADATA.create_all(bind, tables=list(_TABLES), checkfirst=False)
    for name, rows in owner_data.restore_owner_tables(bind, _TABLES):
        print(f"0006_employee_target: đã nạp lại {rows} dòng Owner vào {name}.")


def downgrade() -> None:
    bind = op.get_bind()
    for name, backup, rows in owner_data.archive_owner_tables(bind, _TABLES):
        print(f"0006_employee_target: giữ lại {rows} dòng của {name} "
              f"trong {backup} — `alembic upgrade` sẽ nạp lại.")
    schema.METADATA.drop_all(bind, tables=list(reversed(_TABLES)), checkfirst=False)
