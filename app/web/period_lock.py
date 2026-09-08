"""R3 §5 — CHỐT KỲ: một bộ số đã duyệt, và cái khoá đi kèm nó.

Chốt một kỳ nghĩa là nói: *"bộ số của tháng này đã được duyệt"*. Từ lúc đó,
mọi thay đổi ảnh hưởng tới kỳ ấy phải đi qua một lần MỞ LẠI có ghi chép.

## Ba điều một lần chốt KHÔNG làm

1. **Không đóng băng dữ liệu.** Sổ vẫn nạp lại được, pipeline vẫn chạy, lịch
   sử vẫn ghi. Nếu chốt kỳ chặn cả đường nạp sổ thì một lần nạp bổ sung cho
   tháng SAU cũng bị chặn theo, chỉ vì nó chạm vào cùng một database.
2. **Không xoá gì.** Không bản ghi nào bị đụng tới.
3. **Không trở thành nguồn đọc.** Màn hình vẫn tính từ dữ liệu HIỆN HÀNH.
   `totals_json` là bản chụp để ĐỐI CHIẾU — đọc báo cáo ra từ đó sẽ biến một
   bằng chứng thành một nguồn thứ hai, và hai nguồn thì sẽ có lúc lệch nhau.

Cái nó khoá là ĐƯỜNG GHI QUYẾT ĐỊNH của Owner cho đúng kỳ đó: giá nhập tay,
gán nhân viên, phân loại Gia dụng cấp dòng, loại/khôi phục dòng, Target.

## Vì sao là PHIÊN BẢN chứ không phải một cột `closed` nhị phân

Một kỳ có thể chốt, mở lại vì phát hiện sai, rồi chốt lần nữa. Một cột nhị
phân ghi đè lịch sử đó, và câu hỏi "bộ số nào đã được duyệt hồi tháng trước"
mất luôn câu trả lời. Mỗi lần chốt vì thế là một dòng MỚI, append-only; lần
chốt ĐANG hiệu lực là bản có ``version_no`` lớn nhất mà ``reopened_at`` còn
rỗng.

Mở lại KHÔNG xoá dòng cũ — nó ghi ``reopened_at``/``reopen_reason`` lên chính
dòng đó. Nhờ vậy "kỳ này từng được duyệt, rồi mở lại lúc nào, vì sao" đọc
được từ một bảng, không phải suy từ sự vắng mặt của một dòng.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, insert, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.web.history_store import HistoryUnavailableError
from tools.db.schema import ORIGIN_PIPELINE, period_close


class PeriodClosedError(RuntimeError):
    """Một lần ghi quyết định rơi vào kỳ đã chốt — TỪ CHỐI, không ghi lặng lẽ.

    Đây là toàn bộ tác dụng của việc chốt kỳ. Nếu ghi vẫn thành công và chỉ
    hiện một cảnh báo, thì cái chốt là một lời khuyên chứ không phải một chốt,
    và bộ số đã duyệt vẫn đổi được sau lưng người đã duyệt nó.
    """

    def __init__(self, year: int, month: int) -> None:
        self.year, self.month = year, month
        super().__init__(
            f"Kỳ {month:02d}/{year} đã được chốt. Hãy MỞ LẠI kỳ (kèm lý do) "
            "trước khi sửa bất kỳ con số nào của nó.")


class InvalidPeriodError(ValueError):
    """Kỳ không phải một tháng thật — không có chỗ nào để chốt."""


@dataclass(frozen=True)
class ClosedPeriod:
    year: int
    month: int
    version_no: int
    closed_at: str
    closed_by: Optional[str]
    note: Optional[str]
    line_count: Optional[int]
    content_fingerprint: Optional[str]
    totals: Optional[dict]

    @property
    def period(self) -> tuple[int, int]:
        return (self.year, self.month)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def content_fingerprint(*, lines, overrides_count: int) -> str:
    """Vân tay của CHÍNH bộ số đang được chốt.

    Nó gồm khoá dòng, giá nhập hiệu lực, provenance và lợi nhuận KPI của từng
    dòng đang được báo cáo, cộng số quyết định giá nhập tay. Hai lần chốt cùng
    vân tay ⟹ giữa chúng không có gì đổi; khác vân tay ⟹ có, và trang chốt kỳ
    nói ra điều đó thay vì để người dùng tự so bằng mắt.

    Không gồm thời điểm chạy hay id snapshot: chạy lại pipeline trên CÙNG dữ
    liệu mà ra cùng con số thì không có gì để báo.
    """
    digest = hashlib.sha256()
    for line in lines:
        digest.update("\x1f".join((
            line.order_key or "",
            "" if line.purchase_price is None else str(line.purchase_price),
            line.purchase_provenance,
            "" if line.kpi_profit is None else str(line.kpi_profit),
            line.employee or "",
            line.line_type,
        )).encode("utf-8"))
        digest.update(b"\x1e")
    digest.update(f"overrides={overrides_count}".encode("utf-8"))
    return digest.hexdigest()


class PeriodCloseStore:
    """Đọc/ghi các lần chốt kỳ. Nhỏ đúng bằng bốn việc nó làm."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    @property
    def engine(self) -> Engine:
        return self._engine

    def closed(self, *, year: int, month: int) -> Optional[ClosedPeriod]:
        """Lần chốt ĐANG hiệu lực của một kỳ, hoặc `None` (kỳ đang mở)."""
        rows = self._read(
            select(period_close)
            .where(period_close.c.year == int(year),
                   period_close.c.month == int(month),
                   period_close.c.reopened_at.is_(None))
            .order_by(period_close.c.version_no.desc())
            .limit(1))
        return _to_closed(rows[0]) if rows else None

    def is_closed(self, period: Optional[tuple[int, int]]) -> bool:
        """Kỳ `None` ("toàn bộ dữ liệu") KHÔNG bao giờ bị coi là đã chốt.

        Chốt là một khẳng định về MỘT THÁNG. Coi khung nhìn "toàn bộ" là đã
        chốt sẽ khoá mọi thao tác ngay khi tháng đầu tiên được chốt — kể cả
        thao tác trên những tháng chưa ai duyệt.
        """
        if period is None:
            return False
        return self.closed(year=period[0], month=period[1]) is not None

    def history(self, *, year: int, month: int) -> list[ClosedPeriod]:
        """Mọi lần chốt của một kỳ, mới nhất trước — kể cả bản đã mở lại."""
        rows = self._read(
            select(period_close)
            .where(period_close.c.year == int(year),
                   period_close.c.month == int(month))
            .order_by(period_close.c.version_no.desc()))
        return [_to_closed(row) for row in rows]

    def closed_periods(self) -> set:
        """`{(năm, tháng)}` đang chốt — một câu truy vấn cho cả trang."""
        rows = self._read(
            select(period_close.c.year, period_close.c.month)
            .where(period_close.c.reopened_at.is_(None))
            .distinct())
        return {(int(row["year"]), int(row["month"])) for row in rows}

    def close(
        self, *, year: int, month: int, closed_by: Optional[str] = None,
        note: Optional[str] = None, totals: Optional[dict] = None,
        line_count: Optional[int] = None,
        fingerprint: Optional[str] = None, closed_at: Optional[str] = None,
    ) -> ClosedPeriod:
        """Chốt một kỳ. Kỳ đã chốt ⟹ `PeriodClosedError`, không chốt hai lần."""
        year, month = _validate(year, month)
        if self.closed(year=year, month=month) is not None:
            raise PeriodClosedError(year, month)
        version_no = self._next_version(year, month)
        moment = closed_at or _now()
        self._execute(insert(period_close).values(
            year=year, month=month, version_no=version_no,
            origin=ORIGIN_PIPELINE, closed_at=moment, closed_by=closed_by,
            note=(note or "").strip() or None,
            totals_json=None if totals is None else json.dumps(
                totals, ensure_ascii=False, sort_keys=True),
            line_count=line_count, content_fingerprint=fingerprint,
        ))
        return ClosedPeriod(
            year=year, month=month, version_no=version_no, closed_at=moment,
            closed_by=closed_by, note=(note or "").strip() or None,
            line_count=line_count, content_fingerprint=fingerprint,
            totals=totals,
        )

    def reopen(
        self, *, year: int, month: int, reason: str,
        reopened_by: Optional[str] = None, reopened_at: Optional[str] = None,
    ) -> None:
        """Mở lại một kỳ đã chốt. LÝ DO là bắt buộc.

        Bắt buộc vì mở lại một kỳ đã duyệt là khẳng định rằng bộ số đã duyệt
        có gì đó sai — và một khẳng định như thế không được để lại không dấu
        vết. Cùng kỷ luật với `MissingPriceReasonError` của R2 §4.4.
        """
        year, month = _validate(year, month)
        text = (reason or "").strip()
        if not text:
            raise MissingReopenReasonError(
                "Mở lại một kỳ đã chốt phải kèm lý do.")
        current = self.closed(year=year, month=month)
        if current is None:
            raise PeriodNotClosedError(
                f"Kỳ {month:02d}/{year} đang mở — không có gì để mở lại.")
        self._execute(
            update(period_close)
            .where(period_close.c.year == year, period_close.c.month == month,
                   period_close.c.version_no == current.version_no)
            .values(reopened_at=reopened_at or _now(),
                    reopened_by=reopened_by, reopen_reason=text))

    def _next_version(self, year: int, month: int) -> int:
        rows = self._read(
            select(func.max(period_close.c.version_no).label("top"))
            .where(period_close.c.year == year, period_close.c.month == month))
        top = rows[0]["top"] if rows else None
        return int(top or 0) + 1

    def _execute(self, statement) -> None:
        try:
            with self._engine.begin() as connection:
                connection.execute(statement)
        except SQLAlchemyError as exc:
            raise HistoryUnavailableError(str(exc)) from exc

    def _read(self, statement) -> list[dict]:
        try:
            with self._engine.connect() as connection:
                return [dict(row._mapping) for row in connection.execute(statement)]
        except SQLAlchemyError as exc:
            raise HistoryUnavailableError(str(exc)) from exc


class MissingReopenReasonError(ValueError):
    """Mở lại một kỳ đã chốt mà không nói vì sao."""


class PeriodNotClosedError(ValueError):
    """Mở lại một kỳ chưa từng chốt."""


def _validate(year, month) -> tuple[int, int]:
    try:
        year, month = int(year), int(month)
    except (TypeError, ValueError):
        raise InvalidPeriodError(f"Kỳ {year!r}/{month!r} không đọc được.") from None
    if not 1 <= month <= 12:
        raise InvalidPeriodError(f"Tháng {month!r} không phải một tháng thật.")
    return year, month


def _to_closed(row: dict) -> ClosedPeriod:
    raw = row.get("totals_json")
    try:
        totals = json.loads(raw) if raw else None
    except (TypeError, ValueError):
        # JSON hỏng KHÔNG được biến trang chốt kỳ thành một trang trắng: bản
        # chụp chỉ là bằng chứng đi kèm, còn "kỳ này đã chốt" vẫn đúng.
        totals = None
    return ClosedPeriod(
        year=int(row["year"]), month=int(row["month"]),
        version_no=int(row["version_no"]), closed_at=row["closed_at"],
        closed_by=row.get("closed_by"), note=row.get("note"),
        line_count=row.get("line_count"),
        content_fingerprint=row.get("content_fingerprint"), totals=totals,
    )


__all__ = [
    "ClosedPeriod", "InvalidPeriodError", "MissingReopenReasonError",
    "PeriodCloseStore", "PeriodClosedError", "PeriodNotClosedError",
    "content_fingerprint",
]
