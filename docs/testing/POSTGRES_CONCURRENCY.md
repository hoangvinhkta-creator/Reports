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
# `-l` nhận một FILE, không phải thư mục — `pg_ctl` không tự tạo thư mục
# cha, và một `-l .../log/server.log` khi `log` chưa tồn tại sẽ báo
# "Directory nonexistent" rồi bỏ luôn lần khởi động.
# `-h ""` tắt TCP: chỉ còn unix socket, đúng thứ URL dưới đây trỏ tới.
su pgtest -c "/usr/lib/postgresql/16/bin/pg_ctl -D /home/pgtest/pg/data \
  -o '-k /home/pgtest/pg/sock -h \"\"' -l /home/pgtest/pg/log start"
chmod 755 /home/pgtest /home/pgtest/pg /home/pgtest/pg/sock

export REPORTS_TEST_POSTGRES_URL="postgresql+psycopg://postgres@/postgres?host=/home/pgtest/pg/sock&port=5432"
.venv/bin/python -m pytest tests/test_p0_single_transaction.py -q -s
```

`-s` để hai test hạ tầng in được số `pg_backend_pid` ra ngoài; không có nó
pytest giữ output lại và bằng chứng chỉ hiện khi test đỏ.

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

**Chứng minh** (`tests/test_p0_single_transaction.py`, 11 test):

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

### Bằng chứng hạ tầng: hai backend thật, khoá trong đúng transaction

Hai test cuối trả lời câu mà mọi test đồng thời ở trên **giả định** mà
không kiểm: hai luồng ấy có thật sự nằm trên hai transaction PostgreSQL
khác nhau hay không. Nếu chúng dùng chung một `Connection`, chúng chạy
**nối đuôi** trong cùng một transaction — và khi ấy cả bộ test xanh vì
không có race nào xảy ra, chứ không vì cửa an toàn làm việc.

- `test_each_concurrent_writer_gets_its_own_postgres_backend` đọc
  `pg_backend_pid()` **trên chính kết nối đang ghi**, ở bên trong vùng
  khoá, và **in ra** số PID (review đòi số này phải đọc được trong log
  CI). Nó bắt buộc hai PID **khác nhau**, bắt buộc `pg_locks` thấy mỗi
  backend giữ ít nhất một khoá `advisory` đã `granted` — tức
  `pg_advisory_xact_lock` chạy trong transaction **đang ghi**, không ở một
  transaction phụ nào — và bắt buộc lần ghi nghiệp vụ chạy trên **đúng**
  một trong hai backend đã khoá.
- `test_the_advisory_lock_really_serializes_the_two_backends` đóng khoảng
  còn lại: hai backend riêng, mỗi backend giữ một khoá, vẫn chưa chứng
  minh hai khoá ấy **loại trừ nhau** (hai `subject` khác nhau cũng cho
  cùng kết quả đo). Bài này giữ luồng thứ nhất ở trong vùng khoá 1,5s và
  bắt buộc luồng thứ hai **không vào được** trong lúc ấy, bằng thứ tự
  vào/ra được ghi lại và in ra.

Bằng chứng của lần chạy đợt này (`pg_advisory_xact_lock` bị gỡ ⟹ **cả hai
test đỏ**, nên chúng không phải mệnh đề rỗng):

```
backend PostgreSQL của từng transaction ghi:
  khoá  thread=Thread-1 (run) pg_backend_pid=1938     advisory_locks_granted=1 subject=BH70002
  khoá  thread=Thread-2 (run) pg_backend_pid=1941     advisory_locks_granted=1 subject=BH70002
  ghi   thread=Thread-1 (run) pg_backend_pid=1938
thứ tự vào/ra vùng khoá: vào:Thread-3, ra:Thread-3, vào:Thread-4, ra:Thread-4
```

**KHÔNG chứng minh** — và điều này cần nói ra thay vì để im:

- Hành vi dưới **nhiều worker gunicorn**. Các test chạy nhiều thread trong
  MỘT tiến trình. Cửa loại trừ là khoá chính + `pg_advisory_xact_lock`,
  cả hai ở tầng database nên chúng đúng qua nhiều tiến trình theo cấu
  tạo — nhưng đó là một lập luận, không phải một phép đo.
- p95 production, độ trễ mạng thật, hành vi khi database quá tải.
- Hành vi khi `pg_advisory_xact_lock` chờ quá lâu: hiện không có timeout
  nào đặt cho nó. Với 1–2 người dùng đây không phải một vấn đề thực tế;
  ở quy mô khác nó là một mục cần xem lại.
