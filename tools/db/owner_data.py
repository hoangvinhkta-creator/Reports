"""B04 — rollback KHÔNG được xoá thứ Owner tự nhập.

## Vấn đề mà module này giải

`downgrade()` của một migration bình thường là `DROP TABLE`. Với chín bảng
pipeline điều đó vô hại: chạy lại máy từ file sổ gốc là dựng lại được toàn bộ.

Với ba bảng quyết-định-của-người thì không. Giá nhập Owner gõ tay, tick Gia
dụng, và việc gán nhân viên cho một dòng **không tái tạo lại được từ bất kỳ
file nào** — chúng ở trong đầu Owner. Một lần rollback production để sửa sự
cố khác sẽ xoá vĩnh viễn công sức nhập liệu của nhiều tuần, và không có thông
báo nào.

## Cơ chế nhỏ nhất đủ an toàn

Trước khi `DROP`, sao nguyên nội dung sang một bảng lưu tạm **trong cùng
database**; lần `upgrade()` sau nạp lại rồi dọn bảng lưu tạm đó đi.

Vì sao chọn cách này chứ không phải một cách "chuẩn" hơn:

- **Không dịch vụ backup, không file dump.** Chỉ thị B04 nói rõ *"Do not
  introduce an enterprise backup subsystem"*. Một file dump lại đặt ra câu hỏi
  ai giữ file, giữ ở đâu, ai được đọc — tức là một hệ thống mới.
- **Cùng database ⟹ cùng transaction, cùng quyền, cùng vòng đời sao lưu.**
  Dữ liệu không rời khỏi nơi nó vốn được bảo vệ.
- **Chạy được trên cả hai phương ngữ.** `CREATE TABLE … AS SELECT` là cú pháp
  chung của SQLite (local/test) và PostgreSQL (production) — ADR-108. Không có
  nhánh riêng cho từng dialect, nên đường này được kiểm ở cả hai nơi.

Bảng lưu tạm cố ý KHÔNG nằm trong `METADATA`: nó không phải một phần của lược
đồ, nó là một cái két chỉ tồn tại giữa một lần rollback và lần nâng cấp lại.

## Thứ module này KHÔNG hứa

Đây không phải bản sao lưu chống mất database. Nếu cả database bị xoá thì bảng
lưu tạm mất cùng nó — chống chuyện đó là việc của sao lưu hạ tầng
(`governance/product/16_BACKUP_DISASTER_RECOVERY.md`), không phải của một
migration. Nó chống đúng MỘT tình huống, và là tình huống đã được nêu tên:
`alembic downgrade` xoá dữ liệu Owner nhập tay.
"""

from __future__ import annotations

from sqlalchemy import inspect

from tools.db import schema


def _table_names(bind) -> set[str]:
    return set(inspect(bind).get_table_names())


def _columns(bind, table_name: str) -> list[str]:
    return [column["name"] for column in inspect(bind).get_columns(table_name)]


def archive_owner_tables(bind, tables) -> list[tuple[str, str, int]]:
    """Sao nội dung sang bảng lưu tạm TRƯỚC khi `downgrade()` xoá bảng thật.

    Trả về `(bảng gốc, bảng lưu tạm, số dòng)` cho từng bảng đã sao, để lệnh
    migration in ra được — một lần rollback im lặng và một lần rollback có ghi
    "đã giữ lại 143 giá nhập" là hai trải nghiệm rất khác nhau.

    Bảng rỗng thì KHÔNG tạo bảng lưu tạm: không có gì để mất, và một cái két
    rỗng nằm lại chỉ làm người vận hành sau này phải đoán nó là gì.

    Nếu đã có sẵn một bảng lưu tạm (rollback hai lần liên tiếp mà chưa nâng
    cấp lại), nội dung mới được CHÈN THÊM chứ không ghi đè — cái két cũ không
    bao giờ bị vứt đi để lấy chỗ cho cái mới.
    """
    existing = _table_names(bind)
    archived: list[tuple[str, str, int]] = []
    for table in tables:
        if table.name not in existing:
            continue
        rows = bind.exec_driver_sql(
            f"SELECT COUNT(*) FROM {table.name}").scalar() or 0
        if not rows:
            continue
        backup = schema.owner_backup_name(table.name)
        if backup in existing:
            shared = [name for name in _columns(bind, backup)
                      if name in set(_columns(bind, table.name))]
            columns = ", ".join(shared)
            bind.exec_driver_sql(
                f"INSERT INTO {backup} ({columns}) "
                f"SELECT {columns} FROM {table.name}")
        else:
            bind.exec_driver_sql(
                f"CREATE TABLE {backup} AS SELECT * FROM {table.name}")
        archived.append((table.name, backup, int(rows)))
    return archived


def restore_owner_tables(bind, tables) -> list[tuple[str, int]]:
    """Nạp lại từ bảng lưu tạm SAU khi `upgrade()` đã dựng lại bảng thật.

    Chỉ chép những cột có mặt ở CẢ HAI bảng. Nếu một bản nâng cấp sau này thêm
    một cột bắt buộc, câu `INSERT` sẽ đỏ ngay tại đây — đó là hành vi đúng:
    một lỗi ồn ào ở migration còn hơn một lần nạp lại âm thầm bỏ mất một cột.

    Bảng lưu tạm được xoá SAU khi nạp xong, trong cùng transaction của
    migration: hoặc dữ liệu đã về chỗ cũ và cái két rỗng đi, hoặc cả hai việc
    cùng không xảy ra.
    """
    existing = _table_names(bind)
    restored: list[tuple[str, int]] = []
    for table in tables:
        backup = schema.owner_backup_name(table.name)
        if backup not in existing or table.name not in existing:
            continue
        shared = [name for name in _columns(bind, backup)
                  if name in set(_columns(bind, table.name))]
        if not shared:
            continue
        columns = ", ".join(shared)
        rows = bind.exec_driver_sql(
            f"SELECT COUNT(*) FROM {backup}").scalar() or 0
        bind.exec_driver_sql(
            f"INSERT INTO {table.name} ({columns}) "
            f"SELECT {columns} FROM {backup}")
        bind.exec_driver_sql(f"DROP TABLE {backup}")
        restored.append((table.name, int(rows)))
    return restored


__all__ = ["archive_owner_tables", "restore_owner_tables"]
