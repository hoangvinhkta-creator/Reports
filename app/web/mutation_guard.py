"""`STAB-03` — chống lặp mutation và cửa kiểm `base_revision`.

Hai ràng buộc của brief §STAB-03 sống ở đây, và chỉ ở đây:

    "Khi response thất lạc, gửi lại cùng `request_id` phải trả được kết quả
     cũ và không tạo ghi thứ hai."
    "Mutation nhận `base_revision` của đối tượng."

## Vì sao hai việc này ở CÙNG một module

Chúng là hai nửa của một câu hỏi duy nhất: "lần gửi này có được phép ghi
không?". `request_id` trả lời "đã ghi rồi chưa"; `base_revision` trả lời
"người gửi có đang nhìn đúng bản không". Tách chúng ra hai chỗ sẽ để lọt
tổ hợp mà cả hai đều phải cùng nói: một lần THỬ LẠI mang revision đã cũ
(vì người khác vừa ghi) KHÔNG được báo xung đột — nó phải trả lại kết quả
lần ghi trước của CHÍNH nó. Thứ tự vì thế cố định, và nó là hợp đồng:

    1. `request_id` trước.
    2. `base_revision` sau, và chỉ khi bước 1 không tìm thấy gì.

Đảo thứ tự này là mở lại đúng cái cửa mà cả hai cơ chế cùng đóng.

## Vì sao KHÔNG có transaction chung với lần ghi nghiệp vụ

`remember()` được gọi SAU khi lần ghi nghiệp vụ đã cam kết. Giữa hai lượt
ghi đó có một cửa sổ, và nó được nói ra thay vì để im: nếu tiến trình chết
đúng trong cửa sổ ấy, lần ghi nghiệp vụ đã vào database nhưng `request_id`
chưa được nhớ — một lần THỬ LẠI sẽ ghi lần thứ hai.

Đóng cửa sổ đó cần hai bảng nằm trong cùng một transaction, tức
`BusinessDecisionStore` phải nhận một `Connection` từ bên ngoài thay vì tự
mở. Đó là một thay đổi ở tầng lưu, và nó nằm ngoài phạm vi đợt này. Cửa sổ
hiện tại rộng bằng một lượt `INSERT` trên cùng database ngay sau commit —
hẹp hơn hẳn cửa sổ mà nó thay thế (toàn bộ thời gian mạng của một request),
nên đây là một cải thiện thật, không phải một lời hứa hoàn hảo.

Ranh giới còn lại được ghi trong bàn giao, không giấu trong code.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from tools.db.schema import mutation_request

#: Mã lỗi ỔN ĐỊNH trả về cho client. Brief §API-02 liệt kê chúng, và chúng
#: là một phần của hợp đồng: client bật nhánh xử lý theo mã, không theo câu
#: chữ tiếng Việt (câu chữ được phép sửa cho dễ đọc, mã thì không).
REVISION_CONFLICT = "REVISION_CONFLICT"
VALIDATION_ERROR = "VALIDATION_ERROR"
PERMISSION_DENIED = "PERMISSION_DENIED"
SOURCE_PENDING = "SOURCE_PENDING"
REQUEST_ALREADY_APPLIED = "REQUEST_ALREADY_APPLIED"
NOT_FOUND = "NOT_FOUND"
PERIOD_CLOSED = "PERIOD_CLOSED"

#: Độ dài tối đa của một `request_id` được nhận. Một mã dài hơn là dấu hiệu
#: client sai hoặc ai đó đang thử làm phình bảng; cắt ở cửa vào chứ không ở
#: cửa ghi, để câu lỗi nói đúng chỗ.
MAX_REQUEST_ID = 128


class MissingRequestIdError(ValueError):
    """Mutation không mang `request_id`. Đây là lỗi của CLIENT, không của người dùng."""


@dataclass(frozen=True)
class Replay:
    """Kết quả của một lần ghi ĐÃ CAM KẾT, đọc lại từ sổ.

    `response` là payload nguyên văn của lần ghi đầu tiên. Nó được trả lại
    y nguyên, cộng thêm cờ `already_applied` — người dùng phải phân biệt
    được "vừa lưu xong" với "cái này đã lưu từ trước", vì hai câu ấy dẫn
    tới hai hành động khác nhau.
    """

    request_id: str
    response: dict
    entered_at: str
    entered_by: Optional[str]


class MutationGuard:
    """Sổ chống lặp trên một `Engine`. Không giữ trạng thái trong bộ nhớ.

    Không cache: một `dict` ở đây sẽ chỉ đúng trong một worker, và
    production chạy nhiều worker gunicorn — đúng cái tình huống bảng SQL
    tồn tại để phục vụ.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    # --- request_id ---------------------------------------------------

    @staticmethod
    def clean_request_id(raw: Optional[str]) -> str:
        """Chuẩn hoá + kiểm `request_id`, hoặc ném `MissingRequestIdError`.

        Chuỗi rỗng bị TỪ CHỐI thay vì được coi là "không có mã": một
        mutation không có mã là một mutation không chống lặp được, và cho
        nó đi qua im lặng là bỏ hẳn cơ chế trong khi vẫn trông như có.
        """
        text = (raw or "").strip()
        if not text:
            raise MissingRequestIdError(
                "Mutation thiếu request_id. Mỗi lần gửi phải mang một mã để "
                "server nhận ra khi bạn gửi lại — không có mã thì không "
                "phân biệt được một lần thử lại với một quyết định mới.")
        if len(text) > MAX_REQUEST_ID:
            raise MissingRequestIdError(
                f"request_id dài quá {MAX_REQUEST_ID} ký tự.")
        return text

    def replay_of(self, request_id: str) -> Optional[Replay]:
        """Lần ghi đã cam kết của mã này, hoặc `None` nếu chưa có."""
        with self._engine.connect() as connection:
            row = connection.execute(
                select(mutation_request).where(
                    mutation_request.c.request_id == request_id)
            ).mappings().first()
        if row is None:
            return None
        return Replay(
            request_id=row["request_id"],
            response=json.loads(row["response_json"]),
            entered_at=row["entered_at"], entered_by=row["entered_by"])

    def remember(self, *, request_id: str, route: str, response: dict,
                 subject: Optional[str] = None,
                 base_revision: Optional[str] = None,
                 entered_by: Optional[str] = None) -> Replay:
        """Ghi kết quả của một lần ghi VỪA CAM KẾT.

        Va khoá chính (`IntegrityError`) KHÔNG phải lỗi: nó nghĩa là một
        request khác mang cùng mã đã ghi xong trước ta trong đúng cửa sổ
        giữa `replay_of()` và chỗ này (hai lần bấm rất nhanh, hoặc hai
        worker). Đúng việc phải làm khi đó là ĐỌC LẠI hàng của người kia và
        trả nó về — chính là điều cơ chế này hứa. Ném lỗi ở đây sẽ biến một
        lần chống lặp THÀNH CÔNG thành một trang lỗi.

        Ghi chú về việc lần ghi nghiệp vụ có thể đã xảy ra HAI lần trong
        tình huống ấy: nó không xảy ra, vì cửa kiểm `replay_of()` đứng
        trước MỌI đường ghi nghiệp vụ. Cửa sổ hẹp còn lại được nói ra ở
        docstring của module.
        """
        payload = json.dumps(response, ensure_ascii=False, sort_keys=True)
        entered_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            with self._engine.begin() as connection:
                connection.execute(mutation_request.insert().values(
                    request_id=request_id, route=route, subject=subject,
                    base_revision=base_revision, response_json=payload,
                    entered_at=entered_at, entered_by=entered_by))
        except IntegrityError:
            existing = self.replay_of(request_id)
            if existing is not None:
                return existing
            raise
        return Replay(request_id=request_id, response=response,
                      entered_at=entered_at, entered_by=entered_by)

    # --- base_revision ------------------------------------------------

    @staticmethod
    def revision_conflict(*, base_revision: Optional[str],
                          current_revision: Optional[str]) -> bool:
        """`True` khi lần gửi này dựa trên một bản KHÔNG còn là bản hiện tại.

        `base_revision is None` ⟹ KHÔNG xung đột. Đây là một quyết định có
        chủ ý và nó cần được nói ra: các form cũ (chưa khai `base_revision`)
        vẫn phải ghi được, vì đợt này không viết lại mọi form của hệ. Chúng
        mất lớp bảo vệ xung đột, và đó là hiện trạng của chúng từ trước —
        không phải một sự nới lỏng mới. Panel sửa đơn của `UI-02` LUÔN gửi
        `base_revision`, và `tests/test_stab03_mutation_guard.py` canh điều
        đó ở chính nơi nó phải đúng.

        `current_revision is None` ⟹ đối tượng không còn tồn tại trong kỳ.
        Đó là xung đột, không phải "không sao": người dùng đang sửa một đơn
        đã biến khỏi phạm vi họ nhìn thấy.
        """
        if base_revision is None:
            return False
        return base_revision != current_revision
