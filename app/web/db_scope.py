"""`STAB-03 REPAIR` — một nguồn kết nối dùng được cho CẢ hai chế độ.

Vì sao module này tồn tại. Review độc lập chứng minh được bằng probe trên
PostgreSQL 16 rằng ba cửa an toàn của `STAB-03` là *check-then-act*:

    cùng `request_id`, hai request đồng thời  → set_purchase_price() 2 lần
    cùng `base_revision`, hai request đồng thời → set_purchase_price() 2 lần
    crash trước `remember()`                   → ghi vào DB, sổ chống lặp rỗng

Nguyên nhân chung, và nó chỉ có MỘT: sổ chống lặp, phép kiểm revision và
lần ghi nghiệp vụ nằm trong BA transaction khác nhau. Không cửa nào trong
đó có thể bảo vệ hai cửa còn lại, vì giữa chúng có những khoảng mà một
request khác chen vào được.

Cách đóng duy nhất là đưa cả ba vào MỘT transaction. Và điều đó đòi một
thứ mà tầng lưu hiện chưa có: khả năng ghi bằng một `Connection` DO NGƯỜI
GỌI mở, thay vì tự mở lấy một transaction riêng cho mỗi lượt ghi.

## Cái module này làm

`Scope` bọc một trong hai thứ và cho chúng cùng một bề mặt:

    `Engine`      → mỗi lượt đọc/ghi tự mở và tự đóng transaction riêng
                    (hành vi CŨ, không đổi một chút nào)
    `Connection`  → mọi lượt đọc/ghi dùng CHÍNH kết nối đó và KHÔNG commit;
                    transaction thuộc về người gọi bên ngoài

Nhờ vậy `BusinessDecisionStore`, `business_queries` và `PeriodCloseStore`
không cần biết chúng đang chạy ở chế độ nào. Mỗi lớp nhận `engine_or_conn`
và mọi thứ khác giữ nguyên.

## Vì sao KHÔNG dùng một biến toàn cục / `threading.local()`

Một "connection hiện hành" đặt ở module hay ở thread-local là trạng thái
ẩn: hai hàm cách nhau mười tầng gọi sẽ tự nhiên chia sẻ nó, kể cả những
hàm không có ý định tham gia transaction ấy. Ở đây thay vào đó là
`store.bind(connection)` trả về một ĐỐI TƯỢNG MỚI. Không có trạng thái nào
bị đổi trên đối tượng dùng chung của app, nên không có đường nào để một
request làm lệch transaction của request khác.

## `commit()` — vì sao nó im lặng ở chế độ Connection

Một lượt ghi đơn lẻ trên `Engine` phải tự commit, nếu không nó không xảy
ra. Cùng lượt ghi đó bên trong một transaction bên ngoài KHÔNG được commit:
commit sớm sẽ chốt một phần của một thao tác chưa xong, và đó đúng là lớp
lỗi `P0-2` mô tả. Nên `Scope.begin()` ở chế độ Connection chỉ trao lại kết
nối, và quyền commit nằm nguyên ở người mở transaction.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Union

from sqlalchemy.engine import Connection, Engine

#: Kiểu mà mọi tầng lưu của vertical nghiệp vụ nay nhận được.
EngineOrConnection = Union[Engine, Connection]


class Scope:
    """Nguồn kết nối, ở một trong hai chế độ. Xem docstring module."""

    __slots__ = ("_target",)

    def __init__(self, target: EngineOrConnection) -> None:
        self._target = target

    @property
    def target(self) -> EngineOrConnection:
        """Đối tượng gốc — để một tầng cần chính `Engine` vẫn lấy lại được."""
        return self._target

    @property
    def bound(self) -> bool:
        """`True` khi đang chạy trong một transaction của người gọi."""
        return isinstance(self._target, Connection)

    @property
    def engine(self) -> Engine:
        """`Engine` phía sau, ở cả hai chế độ.

        Cần cho những chỗ thật sự phải mở một transaction ĐỘC LẬP (ví dụ
        ghi một dòng nhật ký phải sống sót kể cả khi transaction chính
        rollback). Hiện chưa có chỗ nào như vậy trong vertical này, nhưng
        thuộc tính này là đường ra tường minh nếu cần — thay vì để ai đó
        moi `_target` ra rồi đoán.
        """
        if isinstance(self._target, Connection):
            return self._target.engine
        return self._target

    @contextmanager
    def connect(self) -> Iterator[Connection]:
        """Kết nối để ĐỌC.

        Chế độ Engine: mở và đóng như cũ.
        Chế độ Connection: trao lại kết nối đang mở và KHÔNG đóng nó —
        đóng ở đây sẽ giết transaction của người gọi ngay giữa thao tác.
        """
        if isinstance(self._target, Connection):
            yield self._target
            return
        with self._target.connect() as connection:
            yield connection

    @contextmanager
    def begin(self) -> Iterator[Connection]:
        """Kết nối để GHI.

        Chế độ Engine: `engine.begin()` — tự commit khi khối kết thúc êm,
        tự rollback khi có ngoại lệ. Đúng hành vi cũ.
        Chế độ Connection: trao lại kết nối và KHÔNG commit. Xem docstring
        module § "vì sao nó im lặng".
        """
        if isinstance(self._target, Connection):
            yield self._target
            return
        with self._target.begin() as connection:
            yield connection


def of(target: Union[EngineOrConnection, Scope]) -> Scope:
    """`Scope` từ bất cứ thứ gì hợp lệ. Nhận lại `Scope` là vô hại.

    Cho phép mọi hàm/lớp khai `engine_or_conn` mà không phải tự kiểm kiểu —
    và không phải lo một `Scope` bị bọc hai lần.
    """
    if isinstance(target, Scope):
        return target
    return Scope(target)
