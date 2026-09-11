"""PostgreSQL THẬT cho test đồng thời. Bỏ qua có tiếng nói khi không có.

## Vì sao SQLite không đủ, và đây là điều kiện nghiệm thu chứ không tuỳ chọn

Review độc lập chỉ ra chính xác vấn đề: SQLite chỉ cho MỘT writer tại một
thời điểm trên cả database, nên khoá ghi toàn cục của nó CHE BỚT race. Một
test đồng thời xanh trên SQLite không nói gì về production, nơi hai
transaction PostgreSQL không chặn nhau.

Bằng chứng cho điều đó, đo được trên chính repo này: probe hai request
đồng thời cùng `request_id` cho `set_purchase_price()` chạy 2 lần trên
PostgreSQL, trong khi kẻ thua trên SQLite chỉ nhận một `503` do lock —
tức SQLite làm lỗi TRÔNG như một sự cố hạ tầng thay vì như một lần ghi
trùng.

## Bỏ qua như thế nào

Không có PostgreSQL ⟹ `pytest.skip` với câu nói RÕ phải làm gì. Đây là
một lựa chọn có đánh đổi và nó cần được nói ra: một test bị bỏ qua trông
y hệt một test đã đạt trong dòng tổng kết của pytest. Nên:

- CI phải đặt `REPORTS_TEST_POSTGRES_URL`, và đó là nơi bằng chứng
  at-most-once được tạo ra (xem `docs/testing/POSTGRES_CONCURRENCY.md`).
- Dòng skip nói ra chính xác biến môi trường cần đặt, để một người đọc
  log CI thấy ngay rằng bằng chứng đang thiếu, không phải rằng nó đã có.

## Biến môi trường

    REPORTS_TEST_POSTGRES_URL   URL SQLAlchemy tới một PostgreSQL DÙNG ĐƯỢC
                                cho test. Ví dụ:
                                postgresql+psycopg://postgres@/postgres?host=/tmp/pg&port=5432

Mỗi test tạo một DATABASE RIÊNG (tên có hậu tố ngẫu nhiên) rồi xoá nó khi
xong: hai test đồng thời trên cùng một database sẽ thấy dữ liệu của nhau,
và `pg_advisory_xact_lock` là khoá theo database nên chúng cũng khoá lẫn
nhau một cách không liên quan.
"""

from __future__ import annotations

import os
import uuid

import pytest

#: Biến môi trường trỏ tới PostgreSQL của test. Xem docstring module.
URL_ENV = "REPORTS_TEST_POSTGRES_URL"

SKIP_REASON = (
    f"Cần PostgreSQL thật: đặt {URL_ENV} (ví dụ "
    "postgresql+psycopg://postgres@/postgres?host=/tmp/pg&port=5432). "
    "SQLite KHÔNG đủ cho test đồng thời — khoá ghi toàn cục của nó che bớt "
    "race, xem tests/support/postgres.py."
)


def url() -> str | None:
    return (os.environ.get(URL_ENV) or "").strip() or None


def require() -> str:
    """URL PostgreSQL, hoặc `pytest.skip` với câu nói rõ phải làm gì."""
    value = url()
    if not value:
        pytest.skip(SKIP_REASON)
    return value


def fresh_engine(prefix: str):
    """`(engine, dispose)` — một DATABASE MỚI, schema đã dựng.

    `dispose()` xoá database. Gọi nó trong `finally`/fixture teardown: một
    database bỏ lại sau mỗi lần chạy test sẽ làm cluster của CI phình lên
    và làm lần chạy sau chậm dần mà không ai biết vì sao.
    """
    from sqlalchemy import create_engine, text

    import tools.db as history_db

    base = require()
    name = f"{prefix}_{uuid.uuid4().hex[:10]}"
    admin = create_engine(base, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{name}"'))
        connection.execute(text(f'CREATE DATABASE "{name}"'))

    # Đổi tên database trong URL. `create_engine` không có API đổi
    # database, nên đường ngắn nhất là dựng lại URL qua đối tượng `URL`
    # của SQLAlchemy — chứ không nối chuỗi, vì URL có thể mang query
    # (`?host=…` cho unix socket) mà nối chuỗi sẽ làm hỏng.
    from sqlalchemy.engine import make_url

    target = make_url(base).set(database=name)
    # `pool_size` đủ cho vài luồng test đồng thời; mặc định 5 là vừa,
    # nhưng nói ra tường minh để một test 4 luồng không kẹt ở hàng đợi
    # pool và trông như một deadlock của khoá.
    engine = create_engine(target, pool_size=10, max_overflow=10)
    history_db.create_all_for_test(engine)

    def dispose() -> None:
        engine.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{name}"'))
        admin.dispose()

    return engine, dispose
