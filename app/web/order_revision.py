"""`STAB-03`/`API-01`/`API-02` — bản (revision) của MỘT đơn và của MỘT kỳ.

Vì sao cần một khái niệm mới: brief yêu cầu mọi mutation nhận
`base_revision` và mọi response đọc trả `order_revision`/`period_revision`.
Đó là điều làm cho "hai người sửa cùng một đơn" trở thành một xung đột nói
ra được, thay vì một lần ghi đè im lặng (last-write-wins).

## Revision KHÔNG phải một cột trong database

Nó là VÂN TAY của trạng thái quyết định đang hiệu lực, tính từ chính dữ
liệu mà màn hình vừa hiển thị. Chọn như vậy có ba hệ quả tốt:

1. Không cần bảng mới, không cần migration, không cần một bộ đếm phải nhớ
   tăng ở mọi đường ghi — và một đường ghi quên tăng bộ đếm là đúng lớp lỗi
   mà cơ chế này tồn tại để đóng.
2. Nó ĐÚNG theo cấu tạo: hai trạng thái khác nhau cho hai vân tay khác
   nhau, và một lần ghi "không đổi gì" (Owner bấm lưu mà không sửa) không
   sinh ra một revision mới làm người kia bị báo xung đột vô cớ.
3. Nó không phụ thuộc thứ tự truy vấn (xem `period_lock.canonical_text`
   về việc `Decimal` được chuẩn hoá trước khi băm).

## Dùng LẠI payload của `period_lock`, không dựng payload thứ hai

`period_lock._LINE_FIELDS` (đọc qua `period_lock.line_payload`) đã là câu
trả lời cho câu hỏi "những gì của một dòng có thể đổi và có ảnh hưởng tới
bộ số" — nó được siết hai lần bởi
`FIND-R3-IR-01`/`FIND-R3-IR-02` sau khi bản đầu tiên mù với phần lớn kết
quả tài chính. Dựng một danh sách trường thứ hai ở đây là mời hai danh
sách ấy trôi khỏi nhau, và khi chúng trôi thì một trong hai sẽ mù đúng
kiểu cũ.

Nên module này KHÔNG định nghĩa trường nào. Nó chỉ băm cùng payload ấy ở
hai phạm vi khác: một đơn, và một kỳ.

## `FINGERPRINT_VERSION` riêng, và vì sao

Vân tay chốt kỳ (`period_lock.content_fingerprint`) là một bản ghi LỊCH SỬ:
nó nằm trong database, gắn với những lần chốt đã xảy ra, và đổi cách tính
nó sẽ làm mọi kỳ đã chốt báo "có thay đổi". Revision ở đây là một giá trị
NHẤT THỜI, sống trong đúng một chu kỳ mở-sửa-lưu của một panel. Hai vòng
đời khác nhau ⟹ hai version tag khác nhau, để không lần nào đổi cái này
buộc phải nghĩ về cái kia.
"""

from __future__ import annotations

import hashlib
from typing import Iterable, Optional

from app.web import period_lock

#: Version tag của CHÍNH cách tính ở file này. Đổi nó khi cách băm đổi:
#: mọi panel đang mở sẽ nhận `REVISION_CONFLICT` ở lần lưu kế tiếp và tải
#: lại — đúng hành vi an toàn, vì bản họ đang giữ được tính theo một quy
#: tắc khác.
REVISION_VERSION = "R7-REV-1"

#: Độ dài chuỗi revision trả ra ngoài. Băm đủ dài để không đụng nhau trong
#: một kỳ (16 hex = 64 bit), đủ ngắn để đọc được trong một URL/log.
_DIGEST_CHARS = 16


def _digest(scope: str, rows: Iterable[tuple]) -> str:
    """Băm một tập dòng đã CHUẨN HOÁ, không phụ thuộc thứ tự đầu vào.

    Sắp theo khoá dòng đầy đủ trước khi băm — cùng lý do và cùng cách
    `period_lock.content_fingerprint` làm: đổi một mệnh đề `ORDER BY` là
    một thay đổi kỹ thuật, và nó không được biến thành "đơn này đã đổi".
    """
    digest = hashlib.sha256()
    digest.update(REVISION_VERSION.encode("utf-8"))
    digest.update(b"\x1d")
    digest.update(scope.encode("utf-8"))
    digest.update(b"\x1d")
    ordered = sorted(rows, key=lambda row: tuple(
        period_lock.canonical_text(value) for value in row[:3]))
    for row in ordered:
        digest.update("\x1f".join(
            period_lock.canonical_text(value) for value in row).encode("utf-8"))
        digest.update(b"\x1e")
    return digest.hexdigest()[:_DIGEST_CHARS]


#: Nhãn PHẠM VI gắn vào mỗi dòng khi gom (`_scope`). Ba trạng thái, và
#: chúng là ba danh sách khác nhau trên `PeriodData` chứ không một cột —
#: nên nhãn được gắn ở ĐÂY, nơi duy nhất biết dòng vừa đến từ danh sách nào.
SCOPE_REPORTED = "reported"
SCOPE_EXCLUDED = "excluded"
SCOPE_REMOVED_IN_SOURCE = "removed_in_source"


def order_lines(data, order_key: str) -> list[dict]:
    """MỌI dòng thuộc về `order_key`, kể cả dòng đã loại/vắng mặt.

    "Cả đơn" nghĩa là CẢ đơn, và tập đúng ở đây không phải `data.details`.
    Đây là cùng lập luận `business_service.plan_order_edit` đã ghi (`DEC-185`
    §F-02): một dòng Owner đã loại (`§30`) hay một dòng đang tạm loại vì
    không còn trong sổ đã xác nhận đầy đủ (R5 §1) vẫn THUỘC về đơn này. Bỏ
    sót chúng khỏi revision nghĩa là một quyết định trên chúng không làm
    revision đổi — và người thứ hai sẽ ghi đè nó mà không thấy xung đột.

    Trả về BẢN SAO nông của từng `detail`, mang thêm `_scope`. Sao chép chứ
    không gắn thẳng vào dict gốc: những dict ấy thuộc về `PeriodData` và
    được cả bảng kê HTML lẫn các phép gộp đọc — thêm một khoá vào chúng là
    sửa trạng thái dùng chung từ một hàm mà không ai gọi để làm việc đó.

    Bản sao NÔNG là đủ và có chủ ý: `detail["line"]` vẫn là chính đối tượng
    `BusinessLine` gốc, nên không có bản sao thứ hai nào của một con số
    nghiệp vụ được tạo ra ở đây.
    """
    scoped = []
    for lines, scope in ((data.details, SCOPE_REPORTED),
                         (data.excluded, SCOPE_EXCLUDED),
                         (data.removed_in_source, SCOPE_REMOVED_IN_SOURCE)):
        for detail in lines:
            if detail["order_key"] == order_key:
                scoped.append({**detail, "_scope": scope})
    return scoped


def of_order(data, order_key: str) -> Optional[str]:
    """Bản của MỘT đơn, hoặc `None` nếu đơn không có dòng nào trong kỳ.

    `None` chứ không một chuỗi rỗng: "đơn không tồn tại trong kỳ này" là
    một câu trả lời khác hẳn "đơn tồn tại và đang ở bản X", và gộp chúng
    lại sẽ làm một PATCH lên một đơn không tồn tại vượt được cửa kiểm
    revision.
    """
    lines = order_lines(data, order_key)
    if not lines:
        return None
    return _digest(f"order:{order_key}",
                   (period_lock.line_payload(line) for line in lines))


def of_period(data, period: Optional[tuple[int, int]]) -> str:
    """Bản của CẢ kỳ — mọi dòng, kể cả đã loại/vắng mặt.

    Client dùng nó để biết KPI trên màn hình có còn khớp với server hay
    không. Nó KHÔNG được dùng làm `base_revision` của một lần sửa đơn: một
    thao tác trên đơn khác cũng đổi nó, và người dùng sẽ nhận xung đột cho
    một thay đổi không liên quan gì tới đơn họ đang mở.

    `period is None` ("toàn bộ dữ liệu") vẫn tính được: phạm vi chỉ đi vào
    chuỗi `scope` để hai lát cắt khác nhau không cho cùng một vân tay.
    """
    scope = "period:" + ("all" if period is None
                         else f"{period[0]:04d}-{period[1]:02d}")
    rows = (period_lock.line_payload(detail) for detail in
            (*data.details, *data.excluded, *data.removed_in_source))
    return _digest(scope, rows)
