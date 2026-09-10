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
from datetime import date, datetime, timezone
from decimal import Decimal
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


#: Nhãn phiên bản của THUẬT TOÁN vân tay, nằm ngay đầu payload được băm.
#:
#: Nó tồn tại để một lần đổi payload về sau là một sự kiện NHÌN THẤY ĐƯỢC
#: trong mã, chứ không phải một hằng số hash lặng lẽ đổi nghĩa. Đổi nhãn này
#: nghĩa là mọi vân tay đã lưu không còn so được với vân tay tính ra hôm nay,
#: và hệ quả (kỳ đã chốt báo drift một lần, cần chốt lại) phải được ghi vào
#: tài liệu bàn giao — không được để người vận hành tự đoán.
FINGERPRINT_VERSION = "R3-FP-2"

#: Các trường của MỘT dòng đi vào vân tay, theo ĐÚNG thứ tự này.
#:
#: `FIND-R3-IR-01` — payload đầu tiên chỉ có sáu trường (`order_key`, giá nhập,
#: provenance, lợi nhuận KPI, nhân viên, loại dòng) và vì thế MÙ với phần lớn
#: kết quả tài chính đã được duyệt. Ca đo được: Owner tick Gia dụng, tỉ lệ quy
#: đổi đi từ 2 % lên 8 %, DS quy đổi rơi từ 150.000.000 xuống 37.500.000 — và
#: vân tay không đổi một bit, nên kỳ đã chốt báo "không có gì đổi".
#:
#: Nguyên tắc thay thế: vân tay phải phủ TOÀN BỘ những gì một người duyệt đã
#: nhìn thấy và ký vào. Bốn nhóm dưới đây, và mỗi nhóm đóng một lớp mù riêng:
#:
#:     danh tính   khoá dòng ĐẦY ĐỦ + ngày bán — hai dòng của cùng một đơn
#:                 phải phân biệt được, kể cả khi truy vấn đổi thứ tự
#:     đầu vào     số lượng · đơn giá · chiết khấu · doanh thu
#:     giá vốn     giá nhập hiệu lực + provenance của nó
#:     kết quả     lợi nhuận KPI · tỉ lệ quy đổi · DS quy đổi · cửa chặn
#:     quy thuộc   nhân viên + nhóm + nguồn gán · loại dòng · nhóm sản phẩm
_LINE_FIELDS = (
    "order_key", "product_key", "occurrence_index", "sale_date",
    "quantity", "sell_price", "discount", "total_sales",
    "purchase_price", "purchase_provenance",
    "kpi_profit", "conversion_rate", "converted_sales", "profit_blockers",
    "employee", "employee_group", "employee_provenance",
    "line_type", "product_group",
)


def _text(value) -> str:
    """Dạng chuỗi ỔN ĐỊNH của một giá trị đi vào vân tay.

    `Decimal` đi qua `normalize()` trước: `2.0` và `2` là CÙNG một tỉ lệ, và
    một lần đổi cách viết số trong database KHÔNG được biến thành "bộ số đã
    duyệt đã thay đổi". `None` ra chuỗi rỗng — nhưng vì mọi trường luôn có mặt
    theo đúng thứ tự `_LINE_FIELDS`, một ô trống không bao giờ trượt sang vị
    trí của ô bên cạnh.
    """
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    if isinstance(value, (tuple, list)):
        return ",".join(_text(item) for item in value)
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _line_payload(detail: dict) -> tuple:
    """Một dòng của kỳ → bộ giá trị đi vào vân tay, theo `_LINE_FIELDS`.

    Đọc từ `detail` (bảng kê đã hợp nhất) chứ không từ `BusinessLine` một
    mình: `BusinessLine` cố ý KHÔNG mang `product_key`/`occurrence_index`/
    `sale_date` — nó là ngữ nghĩa nghiệp vụ thuần — nên chỉ nó thì danh tính
    dòng không đầy đủ, và đó chính là một nửa của `FIND-R3-IR-01`.
    """
    line = detail["line"]
    return (
        detail.get("order_key"),
        detail.get("product_key"),
        detail.get("occurrence_index"),
        detail.get("sale_date"),
        line.quantity,
        line.sell_price,
        line.discount,
        line.total_sales,
        line.purchase_price,
        line.purchase_provenance,
        line.kpi_profit,
        line.conversion_rate,
        line.converted_sales,
        line.profit_blockers,
        line.employee,
        line.employee_group,
        line.employee_provenance,
        line.line_type,
        detail.get("classified_product_group"),
    )


#: Tên CÔNG KHAI của hai hàm dưới. `app/web/order_revision.py` băm cùng
#: payload này ở hai phạm vi khác (một đơn, một kỳ), và nó phải dùng LẠI
#: `_LINE_FIELDS` chứ không dựng một danh sách trường thứ hai — hai danh
#: sách sẽ trôi khỏi nhau, và khi trôi thì một trong hai mù đúng kiểu
#: `FIND-R3-IR-01` đã trả giá một lần.
#:
#: Chúng là alias, không phải hàm mới: đổi cách tính ở `_line_payload`/
#: `_text` đổi cả hai nơi gọi cùng lúc, đúng như phải vậy.
line_payload = _line_payload
canonical_text = _text


def content_fingerprint(*, details, totals: dict) -> str:
    """Vân tay của CHÍNH bộ số đang được chốt.

    Hai đầu vào, và cả hai đều là thứ người duyệt đã nhìn thấy:

        `details`  các dòng ĐÃ HỢP NHẤT của đúng kỳ đó (`PeriodData.details`)
        `totals`   bản chụp chỉ tiêu SẼ ĐƯỢC LƯU cùng lần chốt
                   (`business_service.snapshot_of`)

    `totals` đi vào vân tay chứ không chỉ đi vào cột `totals_json`, và đó là
    một khẳng định có ích: vân tay và bản chụp không thể trôi khỏi nhau, vì
    chúng là hai cách viết của cùng một payload.

    ## Thứ tự canonical — không phụ thuộc truy vấn

    Các dòng được SẮP theo khoá dòng đầy đủ trước khi băm. `raw_lines` hôm nay
    trả về theo `(sale_date, order_key, occurrence_index)`, nhưng vân tay
    KHÔNG được phụ thuộc vào chi tiết đó: đổi một mệnh đề `ORDER BY` là một
    thay đổi kỹ thuật, và nó không được biến thành "bộ số đã duyệt đã đổi".

    ## `FIND-R3-IR-02` — vân tay chỉ phụ thuộc dữ liệu CỦA KỲ NÀY

    Payload đầu tiên cộng thêm `len(store.purchase_price_overrides())` — số
    override của TOÀN DATABASE. Owner gõ một giá tay cho tháng 02 làm tháng 01
    đã chốt báo drift, dù không một dòng nào của tháng 01 đổi.

    Phụ thuộc đó nay bị gỡ hẳn, và không có gì thay chỗ nó: giá nhập HIỆU LỰC
    cùng provenance của TỪNG DÒNG đã nói đủ về mọi quyết định có ảnh hưởng tới
    kỳ này. Một quyết định không chạm dòng nào của kỳ thì theo định nghĩa
    không đổi bộ số của kỳ — và vân tay phải im lặng đúng như vậy.

    ## `details` phải là CẢ KỲ

    Hàm này không kiểm được điều đó, nên nó được nói ra ở đây: truyền một lát
    cắt (một nhân viên, một sheet) sẽ cho ra vân tay của lát cắt ấy. Hai nơi
    gọi (`close_period`, `period_drift`) đều truyền `PeriodData` của cả kỳ.
    """
    digest = hashlib.sha256()
    digest.update(FINGERPRINT_VERSION.encode("utf-8"))
    digest.update(b"\x1d")
    # Bản chụp chỉ tiêu, khoá sắp xếp — `snapshot_of` đã trả về dict, và thứ
    # tự chèn của dict KHÔNG được là một phần của vân tay.
    digest.update(json.dumps(
        totals or {}, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8"))
    digest.update(b"\x1d")
    rows = sorted(
        (_line_payload(detail) for detail in details),
        key=lambda row: tuple(_text(value) for value in row[:3]),
    )
    for row in rows:
        digest.update("\x1f".join(_text(value) for value in row).encode("utf-8"))
        digest.update(b"\x1e")
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
    "ClosedPeriod", "FINGERPRINT_VERSION", "InvalidPeriodError",
    "MissingReopenReasonError", "PeriodCloseStore", "PeriodClosedError",
    "PeriodNotClosedError", "content_fingerprint",
]
