"""R5 §5 — MÃ MÁY (IMEI) cho ĐÚNG một màn hình, và không đâu khác.

Đây là một sửa đổi CÓ CHỦ ĐÍCH với hàng rào dữ liệu cá nhân của
`business_queries` (`governance/product/17_DATA_GOVERNANCE_PRIVACY.md`), và
nó được viết ra thành một module riêng chính vì thế: ranh giới mới phải nhìn
thấy được trong cây import, không nằm lẫn trong một tầng truy vấn mà mọi
trang chỉ tiêu đều gọi.

## Quyết định, và phạm vi chính xác của nó

`DEC-R5-03` (Owner, 08/09/2026): IMEI ĐẦY ĐỦ được mở trên tab nhân viên.
Nhân viên cần đối chiếu máy đã bán với máy trên phiếu, và không có mã máy
thì không đối chiếu được — họ đang phải mở sổ Excel song song.

Phạm vi là MỘT route và dừng ở đó:

    ĐI QUA   `/kinh-doanh/nhan-vien` — bảng kê của một sheet, sau xác thực
    KHÔNG    mọi trang chỉ tiêu · trang snapshot · trang thương hiệu · cơ cấu
             · đánh giá · export mới · telemetry · log

`business_queries` vì thế KHÔNG được nới ra: nó vẫn không đọc `imei`, và
`tests/test_business_boundaries.py` vẫn canh đúng điều đó bằng chính mã
nguồn. Module này là cánh cửa DUY NHẤT, và `tests/test_r5_imei_boundary.py`
canh rằng chỉ `server.py` mở nó.

## Vì sao một truy vấn RIÊNG chứ không thêm một cột

Thêm `imei` vào `_COLUMNS` của `business_queries` sẽ đưa nó vào MỌI trang
dùng `PeriodData` — tổng hợp, cơ cấu, thương hiệu, đánh giá, export. Không
trang nào trong số đó hiện nó ra hôm nay, nhưng tất cả sẽ MANG nó trong bộ
nhớ, và trang tiếp theo ai đó viết sẽ có nó trong tay mà không phải xin phép
ai. Một truy vấn riêng đắt hơn một cột đúng một lượt đọc, và đổi lại phạm vi
là thứ đọc được từ mã nguồn.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.web.history_store import HistoryUnavailableError
from tools.db.schema import order_line_current, order_line_source_version

_CURRENT = order_line_current.c
_SOURCE = order_line_source_version.c

#: Cùng trần tham số `IN` với các tầng truy vấn khác của vertical.
_KEY_CHUNK = 500


def imei_of(engine: Engine, keys) -> dict:
    """`{khoá dòng: mã máy}` cho các dòng hỏi tới. Dòng không có mã ⟹ vắng mặt.

    Đọc `imei` của ĐÚNG source version hiện hành, không của lịch sử: một máy
    đã được sửa mã trong lần nạp sau thì mã đúng là mã mới nhất, và cộng dồn
    các version sẽ hiện hai mã cho một dòng.

    Chuỗi rỗng và `NULL` cho ra cùng một kết quả (vắng mặt) vì chúng là cùng
    một sự thật nghiệp vụ: sổ không ghi mã máy cho dòng này.
    """
    wanted = {tuple(key) for key in keys}
    order_keys = sorted({key[0] for key in wanted})
    if not order_keys:
        return {}
    joined = order_line_current.join(
        order_line_source_version,
        _SOURCE.id == _CURRENT.current_source_version_id)
    found: dict = {}
    try:
        with engine.connect() as connection:
            for start in range(0, len(order_keys), _KEY_CHUNK):
                rows = connection.execute(
                    select(_CURRENT.order_key, _CURRENT.product_key,
                           _CURRENT.occurrence_index, _SOURCE.imei)
                    .select_from(joined)
                    .where(_CURRENT.order_key.in_(
                        order_keys[start:start + _KEY_CHUNK]))
                )
                for row in rows:
                    key = (row.order_key, row.product_key, row.occurrence_index)
                    text = (row.imei or "").strip()
                    if key in wanted and text:
                        found[key] = text
    except SQLAlchemyError as exc:
        raise HistoryUnavailableError(str(exc)) from exc
    return found


def imei_for(imeis: dict, detail: dict) -> Optional[str]:
    """Mã máy của MỘT dòng đã hợp nhất, hoặc `None`."""
    return imeis.get((detail["order_key"], detail["product_key"],
                      detail["occurrence_index"]))


__all__ = ["imei_for", "imei_of"]
