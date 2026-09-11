"""R3 §1 — hàng đợi NGOẠI LỆ GẮN DÒNG: đọc, và đánh dấu đã xử lý.

Module riêng, không nhét vào `business_store`, vì hai lý do cấu trúc:

1. `business_store` có một hàng rào được canh bằng test
   (`test_the_business_write_layer_never_touches_the_append_only_fact_tables`):
   nó chỉ được chạm các bảng quyết định của chính nó. `line_binding_exception`
   là bảng DẪN XUẤT do đường nạp sổ sinh ra, không phải một quyết định Owner
   gõ vào — để nó ở đây giữ hàng rào kia nguyên vẹn.
2. Vòng đời khác hẳn: một ngoại lệ được MÁY dựng và được NGƯỜI đóng. Các bảng
   của `business_store` thì ngược lại — người dựng, người xoá.

"Đã xử lý" ở đây KHÔNG sửa một khoá nào và KHÔNG di chuyển một quyết định
nào. Nó chỉ ghi rằng người đã nhìn và đã quyết — bằng chính các thao tác sẵn
có (gõ lại giá nhập cho khoá mới, loại dòng cũ khỏi báo cáo, hoặc không làm
gì vì dòng cũ đúng là đã biến mất). Tự động "chuyển quyết định sang khoá mới"
chính là phép đoán mà cả cơ chế này sinh ra để từ chối.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.web.history_store import HistoryUnavailableError
from app.web import db_scope
from tools.db.schema import line_binding_exception


@dataclass(frozen=True)
class BindingException:
    id: int
    order_key: str
    product_key: str
    assigned_occurrence_index: int
    raised_by_snapshot_id: str
    run_id: Optional[str]
    source_row: Optional[int]
    created_at: str
    candidate_occurrence_indexes: tuple[int, ...]
    protected_occurrence_indexes: tuple[int, ...]
    protected_decisions: tuple[str, ...]
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    resolution_note: Optional[str] = None

    @property
    def key(self) -> tuple[str, str, int]:
        return (self.order_key, self.product_key,
                int(self.assigned_occurrence_index))

    @property
    def open(self) -> bool:
        return self.resolved_at is None


class BindingExceptionStore:
    """`STAB-03 REPAIR` — nhận `Engine` hoặc `Connection` (`db_scope`)."""

    def __init__(self, engine) -> None:
        self._scope = db_scope.of(engine)

    @property
    def engine(self) -> Engine:
        return self._scope.engine

    def bind(self, connection) -> "BindingExceptionStore":
        return BindingExceptionStore(connection)

    def open_exceptions(self, *, limit: int = 200) -> list[BindingException]:
        return self._list(
            select(line_binding_exception)
            .where(line_binding_exception.c.resolved_at.is_(None))
            .order_by(line_binding_exception.c.created_at.desc(),
                      line_binding_exception.c.id.desc())
            .limit(limit))

    def open_keys(self) -> dict:
        """``khoá dòng → ngoại lệ`` cho các ngoại lệ CÒN MỞ.

        Một dict cho cả trang: bảng kê chi tiết cần biết "dòng này có ngoại lệ
        không" cho từng dòng, và hỏi database mỗi dòng một câu là cách một
        trang 350 dòng trở thành 350 truy vấn.
        """
        return {item.key: item for item in self.open_exceptions(limit=5000)}

    def resolve(
        self, *, exception_id: int, resolved_by: Optional[str] = None,
        note: Optional[str] = None, resolved_at: Optional[str] = None,
    ) -> None:
        self._execute(
            update(line_binding_exception)
            .where(line_binding_exception.c.id == int(exception_id),
                   line_binding_exception.c.resolved_at.is_(None))
            .values(
                resolved_at=resolved_at or datetime.now(timezone.utc)
                .isoformat(timespec="seconds"),
                resolved_by=resolved_by,
                resolution_note=(note or "").strip() or None))

    def _list(self, statement) -> list[BindingException]:
        return [_to_exception(row) for row in self._read(statement)]

    def _execute(self, statement) -> None:
        try:
            with self._scope.begin() as connection:
                connection.execute(statement)
        except SQLAlchemyError as exc:
            raise HistoryUnavailableError(str(exc)) from exc

    def _read(self, statement) -> list[dict]:
        try:
            with self._scope.connect() as connection:
                return [dict(row._mapping) for row in connection.execute(statement)]
        except SQLAlchemyError as exc:
            raise HistoryUnavailableError(str(exc)) from exc


def _to_exception(row: dict) -> BindingException:
    try:
        detail = json.loads(row.get("detail_json") or "{}")
    except (TypeError, ValueError):
        # Mất phần chi tiết vẫn hơn mất cả ngoại lệ: "đơn nào, dòng nào" nằm
        # ở các cột thật, và đó mới là thứ Owner cần để mở đúng dòng ra xem.
        detail = {}
    return BindingException(
        id=int(row["id"]), order_key=row["order_key"],
        product_key=row["product_key"],
        assigned_occurrence_index=int(row["assigned_occurrence_index"]),
        raised_by_snapshot_id=row["raised_by_snapshot_id"],
        run_id=row.get("run_id"), source_row=row.get("source_row"),
        created_at=row["created_at"],
        candidate_occurrence_indexes=tuple(
            int(value) for value in detail.get("candidate_occurrence_indexes", ())),
        protected_occurrence_indexes=tuple(
            int(value) for value in detail.get("protected_occurrence_indexes", ())),
        protected_decisions=tuple(
            str(value) for value in detail.get("protected_decisions", ())),
        resolved_at=row.get("resolved_at"), resolved_by=row.get("resolved_by"),
        resolution_note=row.get("resolution_note"),
    )


__all__ = ["BindingException", "BindingExceptionStore"]
