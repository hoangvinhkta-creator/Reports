"""Cổng LƯU TRỮ của log quyết định Product Identity — `F-A`/`F-B`.

## Vì sao có file này

`JsonlProductIdentityStore` giữ TOÀN BỘ luật thẩm quyền (`INV-01`, `INV-59`,
`INV-68`/`INV-69`, `INV-66`…). Thứ duy nhất nó còn giả định cứng là NƠI các
event nằm: một file JSONL cạnh tiến trình. Trên máy Owner giả định đó đúng —
đĩa thật, một tiến trình. Trên bản Web (`gunicorn --workers 2`, container
không có persistent disk) nó sai theo hai cách khác nhau và cùng lúc:

    F-A  hai worker cùng đọc một log nhưng mỗi worker giữ một ảnh chụp riêng
         trong bộ nhớ ⟹ worker B không thấy xác nhận mà worker A vừa ghi.
    F-B  chính file log nằm trên filesystem của container ⟹ một lần redeploy
         xoá sạch mọi quyết định đã xác nhận.

File này tách NƠI LƯU ra khỏi LUẬT, để đúng một `JsonlProductIdentityStore`
(một thẩm quyền, một đường ghi) chạy được trên hai nơi lưu khác nhau. Nó
KHÔNG thêm một thẩm quyền identity thứ hai: `PHB-01` giữ nguyên — Tracking là
thẩm quyền Product Identity, và log này vẫn đúng là log quyết định của con
người phía Reports (`mapping_source = HUMAN_CONFIRMATION`) mà CLI và màn hình
cùng ghi qua đúng một `store.append()`. Đổi chỗ lưu của một bản ghi không
biến bản ghi đó thành một thẩm quyền mới.

## Hợp đồng

Một journal là một chuỗi bản ghi CHỈ-THÊM (`INV-67`). Ba phép toán:

    transaction()  biên loại trừ của một lần ghi. Người gọi PHẢI `pull()`
                   ngay sau khi vào, trước khi quyết định bất cứ điều gì
                   dựa trên version — đó là nửa còn lại của `INV-59`.
    pull()         các bản ghi đã có thêm kể từ lần `pull()` trước. Journal
                   tự giữ con trỏ đọc của mình.
    append(record) thêm ĐÚNG một bản ghi vào đuôi.

`append()` được phép raise `JournalWriteConflict` khi một người viết khác đã
chiếm đúng vị trí đó. Đây KHÔNG phải lỗi hệ thống: nó là `INV-59` nói bằng
một giọng khác — nạp lại và reconcile (`INV-60`). Store dịch nó ra ngoài sau
khi đã hoàn lại state trong bộ nhớ, nên không bao giờ có một event "có trong
RAM mà không có trong log".
"""

from __future__ import annotations

from typing import Any, ContextManager, Protocol


class JournalWriteConflict(RuntimeError):
    """Một người viết khác đã chiếm vị trí kế tiếp của log.

    Cùng ngữ nghĩa `INV-59`/`INV-60` với `MappingVersionConflict`, chỉ phát
    hiện ở tầng lưu trữ thay vì tầng domain: khi nơi lưu là một object store
    dùng chung (nhiều container, không có khoá file chung), phép ghi-nếu-vắng
    CHÍNH LÀ chỗ hai người viết đồng thời gặp nhau.
    """


class IdentityJournal(Protocol):
    """Nơi lưu chuỗi event của `JsonlProductIdentityStore` (§ Hợp đồng)."""

    def transaction(self) -> ContextManager[None]:
        ...

    def pull(self) -> list[dict[str, Any]]:
        ...

    def append(self, record: dict[str, Any]) -> None:
        ...


__all__ = ["IdentityJournal", "JournalWriteConflict"]
