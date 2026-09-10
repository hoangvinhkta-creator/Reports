"""`STAB-03` — at-most-once và compare-and-swap revision, trong MỘT transaction.

## Bản trước SAI ở đâu, và bằng chứng

Bản đầu của file này xếp ba cửa theo thứ tự `replay_of()` → kiểm revision →
ghi → `remember()`, mỗi bước một transaction riêng. Docstring của nó khẳng
định lần ghi thứ hai "không xảy ra, vì cửa kiểm `replay_of()` đứng trước
MỌI đường ghi nghiệp vụ". Review độc lập chứng minh câu đó sai, bằng probe
trên PostgreSQL 16 với `threading.Barrier` đặt ngay trước `apply_order_edit`:

    cùng `request_id`, hai request đồng thời    → set_purchase_price() 2 lần
    cùng `base_revision`, hai request đồng thời → set_purchase_price() 2 lần
    crash trước `remember()`                    → giá đã vào DB, sổ rỗng

Cả ba là cùng MỘT lỗi: check-then-act. Giữa lúc ĐỌC ("chưa ai ghi", "bản
vẫn khớp") và lúc GHI có một khoảng mà request khác chen vào được, và không
có gì giữ khoảng đó.

## Bản này đóng lỗi bằng cấu tạo, không bằng thứ tự

MỘT transaction, và bốn việc bên trong nó theo thứ tự bắt buộc:

    1. `INSERT mutation_request(state='in_flight')`
       `request_id` là KHOÁ CHÍNH, nên đây là cửa loại trừ THẬT — không
       phải một phép đọc. Request thứ hai mang cùng mã va khoá chính TRƯỚC
       khi chạm một bảng nghiệp vụ nào. Đây là chỗ `P0-1` bị đóng.

    2. KHOÁ theo đối tượng (`_lock_subject`)
       Mọi lần sửa cùng một đơn nối đuôi nhau. Sau khi giữ khoá này, không
       writer nào khác có thể đổi đơn cho tới khi ta commit hoặc rollback.

    3. TÍNH LẠI revision, BÊN TRONG khoá, rồi so với `base_revision`
       Vì bước 2 đã loại trừ mọi writer khác, phép đọc-rồi-so ở đây là một
       compare-and-swap đúng nghĩa: không có khoảng nào để ai chen vào giữa
       lần đọc và lần ghi. Đây là chỗ `P0-3` bị đóng.

    4. GHI nghiệp vụ + `UPDATE … state='applied', response_json=…`
       Cùng transaction, nên hai việc này thành công cùng nhau hoặc thất
       bại cùng nhau. Không còn cửa sổ nào giữa "đã ghi" và "đã nhớ" — vì
       chúng nay là MỘT việc. Đây là chỗ `P0-2` bị đóng.

Rollback ở bất kỳ bước nào xoá cả hàng `mutation_request` lẫn lần ghi
nghiệp vụ. Một lần THỬ LẠI sau đó là một lần đầu tiên hợp lệ, và nó tạo
đúng một hiệu ứng.

## `remember()` đã bị GỠ

Không còn hàm nào ghi sổ sau commit. Đó là một hàm không thể đúng: nó chạy
ở một thời điểm mà lần ghi nghiệp vụ đã không thể lấy lại được nữa.

## Khoá ở bước 2 — hai dialect, một ngữ nghĩa

PostgreSQL: `pg_advisory_xact_lock(key)`. Khoá theo transaction, tự nhả
khi commit/rollback — không có đường nào để một khoá kẹt lại vì một tiến
trình chết. Không cần bảng khoá, không cần dòng nào để `SELECT FOR UPDATE`.

SQLite: không có advisory lock, và không cần — nó chỉ cho MỘT writer tại
một thời điểm trên cả database, nên `BEGIN IMMEDIATE` của transaction ghi
đã là cùng thứ loại trừ, chỉ rộng hơn. Hàm khoá vì thế không làm gì trên
SQLite, và điều đó được nói ra ở đây thay vì để người đọc tưởng mình đang
có một khoá mà thật ra không có.

Hệ quả phải nói rõ: bằng chứng at-most-once trên SQLite là bằng chứng YẾU
hơn, vì khoá ghi toàn cục của nó che bớt race.
`tests/test_p0_single_transaction.py` vì thế chạy trên PostgreSQL và tự bỏ
qua nếu không có — xem docstring của file đó và
`docs/testing/POSTGRES_CONCURRENCY.md`.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Iterator, Optional

from sqlalchemy import select, text, update
from sqlalchemy.exc import IntegrityError

from app.web import db_scope
from tools.db.schema import mutation_request

#: Mã lỗi ỔN ĐỊNH trả về cho client. Client bật nhánh theo mã, không theo
#: câu chữ tiếng Việt (câu chữ được phép sửa cho dễ đọc, mã thì không).
REVISION_CONFLICT = "REVISION_CONFLICT"
VALIDATION_ERROR = "VALIDATION_ERROR"
PERMISSION_DENIED = "PERMISSION_DENIED"
SOURCE_PENDING = "SOURCE_PENDING"
REQUEST_ALREADY_APPLIED = "REQUEST_ALREADY_APPLIED"
REQUEST_IN_FLIGHT = "REQUEST_IN_FLIGHT"
NOT_FOUND = "NOT_FOUND"
PERIOD_CLOSED = "PERIOD_CLOSED"
INTERNAL_ERROR = "INTERNAL_ERROR"

STATE_IN_FLIGHT = "in_flight"
STATE_APPLIED = "applied"

#: `P1-2` — `idempotency_key` nhận từ client CHỈ được là UUID.
#:
#: Bản trước nhận mọi chuỗi dưới 128 ký tự. Hai hệ quả review đã chỉ ra:
#: một mã chứa khoảng trắng/`key=value` chèn được trường giả vào dòng log
#: theo đúng định dạng grep, và một mã tự chọn cho phép hai request khác
#: nhau cố tình dùng chung mã.
#:
#: UUID đóng cả hai: nó không chứa ký tự nào của định dạng log, độ dài cố
#: định, và không gian đủ lớn để hai client không đụng nhau một cách tình
#: cờ. Đây cũng chính là cái `crypto.randomUUID()` ở `app.js` đang sinh,
#: nên không có client hợp lệ nào bị chặn.
_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


class MissingIdempotencyKeyError(ValueError):
    """Mutation không mang `idempotency_key` hợp lệ. Lỗi của CLIENT."""


class RequestInFlightError(RuntimeError):
    """Một request khác mang cùng mã ĐANG ghi, chưa commit.

    Khác hẳn "đã ghi rồi": ta không biết nó sẽ commit hay rollback, nên
    không có kết quả nào để trả lại và cũng KHÔNG được ghi lần thứ hai.
    Đường đúng là nói cho client biết và để họ thử lại — lúc đó request kia
    đã kết thúc, và cùng mã sẽ cho một câu trả lời dứt khoát.
    """


@dataclass(frozen=True)
class Applied:
    """Kết quả của một lần ghi ĐÃ COMMIT, đọc lại từ sổ."""

    idempotency_key: str
    audit_id: str
    response: dict
    entered_at: str
    entered_by: Optional[str]


class RevisionConflict(Exception):
    """`base_revision` không còn là bản hiện tại, phát hiện TRONG transaction.

    Mang theo bản hiện tại để tầng route trả về cho client mà không phải
    mở thêm một lượt đọc — và quan trọng hơn: bản đó được đọc bên trong
    cùng transaction, nên nó là bản THẬT tại thời điểm từ chối, không phải
    một ảnh chụp có thể đã cũ.
    """

    def __init__(self, *, current_revision: Optional[str]) -> None:
        super().__init__(current_revision or "")
        self.current_revision = current_revision


def clean_idempotency_key(raw: Optional[str]) -> str:
    """Chuẩn hoá + kiểm `idempotency_key`, hoặc ném lỗi.

    Chuỗi rỗng bị TỪ CHỐI thay vì được coi là "không có mã": một mutation
    không có mã là một mutation không chống lặp được, và cho nó đi qua im
    lặng là bỏ hẳn cơ chế trong khi vẫn trông như có.
    """
    text_value = (raw or "").strip().lower()
    if not text_value:
        raise MissingIdempotencyKeyError(
            "Mutation thiếu idempotency_key. Mỗi lần gửi phải mang một mã "
            "để server nhận ra khi bạn gửi lại — không có mã thì không phân "
            "biệt được một lần thử lại với một quyết định mới.")
    if not _UUID_PATTERN.match(text_value):
        raise MissingIdempotencyKeyError(
            "idempotency_key phải là một UUID (dạng "
            "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx). Mã tự do bị từ chối vì "
            "nó cho phép chèn ký tự vào dòng log và cho hai request khác "
            "nhau dùng chung một mã.")
    return text_value


def new_audit_id() -> str:
    """Mã của một lần ghi, do SERVER sinh. Không bao giờ nhận từ client.

    `P1-4` — ba loại mã, ba nghĩa, và bản trước gộp hai trong số đó vào
    cùng một tên trường:

        `trace_id`         một REQUEST, phục vụ log/correlation
                           (`request_timing`)
        `idempotency_key`  một LẦN GỬI của client, giữ nguyên qua các lần
                           thử lại
        `audit_id`         một LẦN GHI nghiệp vụ, do server sinh

    Chúng khác nhau ở vòng đời: hai lần thử lại có hai `trace_id`, cùng một
    `idempotency_key`, và cùng một `audit_id` (vì chỉ có một lần ghi).
    """
    return uuid.uuid4().hex


class MutationGuard:
    """Cửa vào duy nhất của một lần ghi có chống lặp + CAS revision."""

    def __init__(self, engine) -> None:
        self._scope = db_scope.of(engine)

    # --- đọc sổ (không ghi) -------------------------------------------

    def applied(self, idempotency_key: str) -> Optional[Applied]:
        """Lần ghi ĐÃ COMMIT của mã này, hoặc `None`.

        Chỉ trả về hàng `applied`. Một hàng `in_flight` nhìn thấy được từ
        NGOÀI transaction của nó là điều không thể xảy ra (nó chưa commit),
        nên nếu thấy thì database đang ở trạng thái ta không hiểu — và trả
        nó về như một kết quả sẽ là nói với người dùng rằng một lần ghi
        chưa xong đã xong.
        """
        with self._scope.connect() as connection:
            row = connection.execute(
                select(mutation_request).where(
                    mutation_request.c.request_id == idempotency_key,
                    mutation_request.c.state == STATE_APPLIED)
            ).mappings().first()
        if row is None:
            return None
        return _to_applied(row)

    # --- ghi (một transaction cho tất cả) -----------------------------

    @contextmanager
    def transaction(
        self, *, idempotency_key: str, route: str, subject: str,
        base_revision: Optional[str],
        revision_of: Callable[[object], Optional[str]],
        entered_by: Optional[str] = None,
    ) -> Iterator[dict]:
        """MỘT transaction bao cả bốn bước. Xem docstring module.

        `revision_of(connection)` được gọi BÊN TRONG transaction, sau khi
        khoá đối tượng đã được giữ. Nó nhận `Connection` và phải tính lại
        revision hiện tại qua CHÍNH kết nối đó — một hàm đọc ngoài
        transaction sẽ trả về ảnh chụp cũ và làm cả cơ chế vô nghĩa.

        Khối `with` nhận một `dict` để đặt hai thứ:

            `ctx["connection"]`  kết nối để ghi nghiệp vụ (bind store vào nó)
            `ctx["response"]`    payload sẽ được lưu và trả về

        Ngoại lệ trong thân `with` ⟹ rollback CẢ hàng sổ lẫn lần ghi.

        Ném `IntegrityError` → chuyển thành `RequestInFlightError` hoặc trả
        lại kết quả đã commit: xem `_on_key_taken`.
        """
        with self._scope.begin() as connection:
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            audit_id = new_audit_id()
            # BƯỚC 1 — cửa loại trừ. Đứng TRƯỚC mọi thứ khác.
            try:
                connection.execute(mutation_request.insert().values(
                    request_id=idempotency_key, route=route, subject=subject,
                    base_revision=base_revision, response_json=None,
                    state=STATE_IN_FLIGHT, entered_at=now,
                    entered_by=entered_by))
                # `flush` bằng một lượt đọc rẻ: trên PostgreSQL lỗi khoá
                # chính đã nổ ngay ở `execute` trên, nhưng viết ra điều đó
                # ở đây để không ai chuyển câu INSERT xuống dưới bước 2 vì
                # tưởng thứ tự không quan trọng.
            except IntegrityError as exc:
                raise self._on_key_taken(idempotency_key) from exc

            # BƯỚC 2 — khoá đối tượng. Xem docstring module § khoá.
            _lock_subject(connection, subject)

            # BƯỚC 3 — CAS thật: tính lại rồi so, bên trong khoá.
            current = revision_of(connection)
            if base_revision is not None and base_revision != current:
                raise RevisionConflict(current_revision=current)

            ctx: dict = {"connection": connection, "audit_id": audit_id,
                         "entered_at": now, "entered_by": entered_by,
                         "current_revision": current, "response": None}
            # BƯỚC 4a — thân `with`: người gọi ghi nghiệp vụ qua
            # `ctx["connection"]` và đặt `ctx["response"]`.
            yield ctx

            # BƯỚC 4b — chốt sổ, CÙNG transaction với lần ghi trên.
            payload = json.dumps(
                {**(ctx["response"] or {}), "audit_id": audit_id},
                ensure_ascii=False, sort_keys=True)
            connection.execute(
                update(mutation_request)
                .where(mutation_request.c.request_id == idempotency_key)
                .values(response_json=payload, state=STATE_APPLIED))

    def _on_key_taken(self, idempotency_key: str) -> Exception:
        """Mã đã bị chiếm: đọc xem nó ĐÃ XONG hay ĐANG BAY.

        Phép đọc này dùng một kết nối RIÊNG, không phải kết nối vừa nổ:
        trên PostgreSQL một transaction đã gặp lỗi không chạy được câu nào
        nữa cho tới khi rollback, nên đọc lại trên chính nó sẽ chỉ cho một
        lỗi thứ hai.

        Hai câu trả lời, và chúng khác nhau ở điều quan trọng nhất:

            `applied`   có kết quả để trả lại → một lần THỬ LẠI hợp lệ
            `in_flight` KHÔNG có kết quả, và cũng KHÔNG được ghi lần hai —
                        ta không biết request kia sẽ commit hay rollback
        """
        engine = self._scope.engine
        with engine.connect() as connection:
            row = connection.execute(
                select(mutation_request).where(
                    mutation_request.c.request_id == idempotency_key)
            ).mappings().first()
        if row is None:
            # Hàng biến mất giữa lúc INSERT nổ và lúc ta đọc lại: request
            # kia đã rollback. Không có kết quả, và ta cũng không nên tự
            # ghi tiếp trong transaction đã lỗi — để client thử lại.
            return RequestInFlightError(
                "Một lần gửi cùng mã vừa kết thúc mà không ghi được. Hãy "
                "thử lại.")
        if row["state"] == STATE_APPLIED:
            return AlreadyApplied(_to_applied(row))
        return RequestInFlightError(
            "Một lần gửi cùng mã đang được xử lý. Chờ một chút rồi thử lại "
            "— server sẽ trả về đúng kết quả của lần ghi đó.")


class AlreadyApplied(Exception):
    """Mã đã có kết quả ĐÃ COMMIT. Đây KHÔNG phải một lỗi.

    Nó là cơ chế đang hoạt động: một lần THỬ LẠI được nhận ra, và kết quả
    lần ghi gốc có sẵn để trả lại. Route bắt nó và trả 200 kèm cờ
    `already_applied`, không phải một trang lỗi.

    Là một ngoại lệ chứ không một giá trị trả về vì nó phát sinh ở giữa
    `transaction()` — sau khi câu INSERT đã nổ — và đường duy nhất ra khỏi
    một context manager ở đó là ném.
    """

    def __init__(self, applied: Applied) -> None:
        super().__init__(applied.idempotency_key)
        self.applied = applied


def _to_applied(row) -> Applied:
    payload = json.loads(row["response_json"]) if row["response_json"] else {}
    return Applied(
        idempotency_key=row["request_id"],
        audit_id=payload.get("audit_id") or "",
        response=payload, entered_at=row["entered_at"],
        entered_by=row["entered_by"])


def _lock_subject(connection, subject: str) -> None:
    """Giữ khoá theo đối tượng trong phạm vi transaction. Xem docstring module.

    PostgreSQL dùng `pg_advisory_xact_lock`, nhận một `bigint`. Khoá đến từ
    băm SHA-256 của `subject` cắt còn 63 bit — dương, để không phải nghĩ về
    dấu, và đủ rộng để hai mã đơn không đụng nhau. Một lần đụng băm chỉ làm
    hai đơn khác nhau nối đuôi nhau một cách không cần thiết; nó KHÔNG làm
    sai một con số nào, nên đây là đánh đổi đúng.
    """
    dialect = connection.engine.dialect.name
    if dialect != "postgresql":
        # SQLite: `BEGIN IMMEDIATE` của chính transaction ghi đã loại trừ
        # mọi writer khác trên cả database. Không có gì để làm ở đây, và
        # giả vờ làm gì đó sẽ tệ hơn.
        return
    digest = hashlib.sha256(subject.encode("utf-8")).digest()
    key = int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)
    connection.execute(text("SELECT pg_advisory_xact_lock(:key)"),
                       {"key": key})


__all__ = [
    "AlreadyApplied", "Applied", "INTERNAL_ERROR", "MissingIdempotencyKeyError", "MutationGuard",
    "NOT_FOUND", "PERIOD_CLOSED", "PERMISSION_DENIED", "REQUEST_ALREADY_APPLIED",
    "REQUEST_IN_FLIGHT", "REVISION_CONFLICT", "RequestInFlightError",
    "RevisionConflict", "SOURCE_PENDING", "STATE_APPLIED", "STATE_IN_FLIGHT",
    "VALIDATION_ERROR", "clean_idempotency_key", "new_audit_id",
]
