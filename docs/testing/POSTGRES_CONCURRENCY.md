# Test đồng thời trên PostgreSQL — điều kiện nghiệm thu, không tuỳ chọn

## Vì sao tài liệu này tồn tại

`STAB-03` hứa **at-most-once**: một lần ghi nghiệp vụ xảy ra đúng một lần
cho mỗi `idempotency_key`, kể cả khi hai request đến đồng thời. Bản đầu
của cơ chế KHÔNG giữ được lời hứa đó, và điều quan trọng là **nó vẫn xanh
trên SQLite**.

Review độc lập chứng minh điều đó bằng probe trên PostgreSQL 16, với
`threading.Barrier` đặt ngay trước `apply_order_edit`:

| Tình huống | Bản đầu, trên PostgreSQL |
|---|---|
| Hai request đồng thời, cùng `request_id` | `set_purchase_price()` **2 lần** |
| Hai request đồng thời, cùng `base_revision` | `set_purchase_price()` **2 lần** |
| Crash trước khi ghi sổ | Giá vào database, sổ chống lặp **rỗng** |

Lý do SQLite che được lỗi này: nó chỉ cho **một** writer tại một thời
điểm trên cả database. Kẻ thua nhận một lỗi lock, `_guarded` biến nó thành
`503`, và một lần **ghi trùng** trông như một **sự cố hạ tầng**. Trên
PostgreSQL hai transaction không chặn nhau, nên cả hai commit.

Kết luận vận hành: **một bộ test đồng thời chỉ chạy trên SQLite không phải
bằng chứng.** Nó là một bài kiểm mà lỗi production đi qua được.

## Cần đặt gì

```
REPORTS_TEST_POSTGRES_URL=postgresql+psycopg://<user>@<host>/<db>
```

Ví dụ (unix socket, đúng dạng đã dùng để tạo bằng chứng của đợt này):

```
REPORTS_TEST_POSTGRES_URL="postgresql+psycopg://postgres@/postgres?host=/var/run/postgresql&port=5432"
```

Không đặt biến này thì `tests/test_p0_single_transaction.py` **bỏ qua** —
và dòng skip nói ra chính xác biến cần đặt, để một người đọc log CI thấy
ngay rằng bằng chứng đang **thiếu**, không phải rằng nó đã **có**.

Người dùng của URL này cần quyền `CREATEDB`: mỗi test tạo một database
riêng rồi xoá (xem `tests/support/postgres.py` về lý do — hai test dùng
chung một database sẽ thấy dữ liệu của nhau, và `pg_advisory_xact_lock` là
khoá theo database nên chúng cũng khoá lẫn nhau một cách không liên quan).

## Chạy cục bộ

Cluster PostgreSQL không chạy được dưới `root`, nên tạo một user thường:

```bash
useradd -m pgtest
su pgtest -c "mkdir -p /home/pgtest/pg/data /home/pgtest/pg/sock && \
  /usr/lib/postgresql/16/bin/initdb -D /home/pgtest/pg/data \
  -U postgres --auth=trust"
su pgtest -c "/usr/lib/postgresql/16/bin/pg_ctl -D /home/pgtest/pg/data \
  -o '-p 55432 -k /home/pgtest/pg/sock' -l /home/pgtest/pg/log start"
chmod 755 /home/pgtest /home/pgtest/pg /home/pgtest/pg/sock

export REPORTS_TEST_POSTGRES_URL="postgresql+psycopg://postgres@/postgres?host=/home/pgtest/pg/sock&port=55432"
.venv/bin/python -m pytest tests/test_p0_single_transaction.py -q
```

## Cấu hình CI

Trên GitHub Actions, một service container là đủ:

```yaml
services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_PASSWORD: postgres
    options: >-
      --health-cmd pg_isready --health-interval 10s
      --health-timeout 5s --health-retries 5
    ports: ["5432:5432"]

env:
  REPORTS_TEST_POSTGRES_URL: postgresql+psycopg://postgres:postgres@localhost:5432/postgres
```

`psycopg` được cài qua extra `history` (`pip install -e ".[dev,web,history]"`).

## Cái các test này chứng minh, và cái chúng KHÔNG

**Chứng minh** (`tests/test_p0_single_transaction.py`, 9 test):

- hai và bốn luồng, cùng `idempotency_key` → **đúng một** lần gọi
  `set_purchase_price()`, đúng một hàng `kpi_purchase_price_override`, và
  **không ai nhận `503`**;
- hai luồng, cùng `base_revision`, mã khác nhau → một thắng, một nhận
  `REVISION_CONFLICT`, và kẻ thua **không ghi gì**;
- crash sau khi ghi / trước khi chốt sổ → **rollback cả hai**, và lần thử
  lại cùng mã tạo **đúng một** hiệu ứng cuối cùng;
- `revision` được tính lại **bên trong** transaction đang mở;
- đường ghi **không mở kết nối thứ hai** nào (test canh cấu tạo — bản đầu
  của `bind()` bỏ sót `BindingExceptionStore`, xem `db_scope`).

**KHÔNG chứng minh** — và điều này cần nói ra thay vì để im:

- Hành vi dưới **nhiều worker gunicorn**. Các test chạy nhiều thread trong
  MỘT tiến trình. Cửa loại trừ là khoá chính + `pg_advisory_xact_lock`,
  cả hai ở tầng database nên chúng đúng qua nhiều tiến trình theo cấu
  tạo — nhưng đó là một lập luận, không phải một phép đo.
- p95 production, độ trễ mạng thật, hành vi khi database quá tải.
- Hành vi khi `pg_advisory_xact_lock` chờ quá lâu: hiện không có timeout
  nào đặt cho nó. Với 1–2 người dùng đây không phải một vấn đề thực tế;
  ở quy mô khác nó là một mục cần xem lại.
