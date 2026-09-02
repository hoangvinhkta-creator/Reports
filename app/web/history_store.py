"""Repository đọc/ghi history store — ranh giới database DUY NHẤT của app/.

Tầng này nói SQLAlchemy Core với ``Engine`` được TIÊM VÀO (dựng ở
``tools/db``, xem ADR-108). Nó không tự chọn driver, không đọc biến môi
trường kết nối, và tuyệt đối không import ``psycopg``/``alembic``. Business
engine (``app/modules/**``) không biết module này tồn tại.

Mọi lỗi database được gói thành ``HistoryUnavailableError`` để tầng web trả
HTTP 503 — KHÔNG BAO GIỜ biến thành "chưa có dữ liệu": một trang rỗng vì mất
kết nối trông y hệt một trang rỗng vì chưa nhập gì, và Owner sẽ đọc nhầm.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Mapping, Optional

from sqlalchemy import func, insert, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

import tools.db as history_db
from app.legacy.models import LegacyWorkbook
from tools.db.schema import (
    ORIGIN_LEGACY, legacy_daily_sales, legacy_import, legacy_monthly_reference,
    legacy_summary_row,
)


class HistoryUnavailableError(RuntimeError):
    """History store không truy cập được — fail rõ, không giả vờ rỗng."""


@dataclass(frozen=True)
class ImportResult:
    import_id: str
    created: bool


def _json(value) -> Optional[str]:
    if value in (None, {}, []):
        return None
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _loads(value) -> Optional[object]:
    return json.loads(value) if value else None


def _row_to_dict(row) -> dict:
    data = dict(row._mapping)
    for key in ("formula_text", "known_defects", "sheets_imported"):
        if key in data:
            data[key] = _loads(data[key])
    return data


class LegacyRepository:
    """Truy cập bản ghi origin = ``LEGACY_REFERENCE``."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    # --- ghi ----------------------------------------------------------

    def create_import(
        self, workbook: LegacyWorkbook, *, version_label: str = "",
        imported_by: Optional[str] = None, notes: str = "",
        make_current: bool = True,
    ) -> ImportResult:
        """Nhập một workbook legacy. Cùng fingerprint → KHÔNG tạo bản mới.

        Upload lại đúng một file đã nhập là thao tác vô hại của người dùng,
        không phải một phiên bản dữ liệu mới; trả về import cũ để lịch sử
        không phình ra những bản trùng khít nhau.
        """
        imported_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        import_id = f"LEG-{imported_at[:10].replace('-', '')}-{workbook.file_fingerprint[:8]}"
        try:
            with self._engine.begin() as connection:
                existing = connection.execute(
                    select(legacy_import.c.import_id).where(
                        legacy_import.c.file_fingerprint == workbook.file_fingerprint
                    )
                ).scalar()
                if existing is not None:
                    return ImportResult(import_id=existing, created=False)

                connection.execute(insert(legacy_import).values(
                    import_id=import_id, origin=ORIGIN_LEGACY,
                    source_file_name=workbook.source_file_name,
                    file_fingerprint=workbook.file_fingerprint,
                    file_size=workbook.file_size, imported_at=imported_at,
                    imported_by=imported_by, version_label=version_label,
                    sheets_imported=_json(workbook.sheets_imported),
                    is_current=False, notes=notes,
                ))
                self._insert_facts(connection, import_id, workbook)
                if make_current:
                    self._set_current(connection, import_id)
        except SQLAlchemyError as exc:
            raise HistoryUnavailableError(str(exc)) from exc
        return ImportResult(import_id=import_id, created=True)

    def _insert_facts(self, connection, import_id: str, workbook: LegacyWorkbook) -> None:
        summary_rows = [
            {
                "import_id": import_id, "origin": ORIGIN_LEGACY, "year": row.year,
                "month": row.month, "seller_label": row.seller_label,
                "row_kind": row.row_kind, "sheet_name": row.sheet_name,
                "sheet_row": row.sheet_row, "unit": row.unit,
                "formula_text": _json(row.formula_text),
                "known_defects": _json(row.known_defects),
                **row.values,
            }
            for row in workbook.summary_rows
        ]
        if summary_rows:
            connection.execute(insert(legacy_summary_row), summary_rows)
        daily = [
            {
                "import_id": import_id, "origin": ORIGIN_LEGACY, "year": item.year,
                "month": item.month, "day": item.day, "sales_vnd": item.sales_vnd,
                "source_sheet": item.source_sheet,
            }
            for item in workbook.daily_sales
        ]
        if daily:
            connection.execute(insert(legacy_daily_sales), daily)
        monthly = [
            {
                "import_id": import_id, "origin": ORIGIN_LEGACY, "year": item.year,
                "month": item.month,
                "sales_current_year_vnd": item.sales_current_year_vnd,
                "sales_prev_year_vnd": item.sales_prev_year_vnd,
                "vs_last_year_ratio": item.vs_last_year_ratio,
                "vs_target_ratio": item.vs_target_ratio,
                "target_year": item.target_year,
                "average_per_day": item.average_per_day,
                "target_per_day": item.target_per_day,
                "formula_text": _json(item.formula_text),
            }
            for item in workbook.monthly_reference
        ]
        if monthly:
            connection.execute(insert(legacy_monthly_reference), monthly)

    @staticmethod
    def _set_current(connection, import_id: str) -> None:
        # Đúng MỘT bản current; bản cũ không bị xoá, chỉ thôi là current.
        connection.execute(update(legacy_import).values(is_current=False))
        connection.execute(
            update(legacy_import)
            .where(legacy_import.c.import_id == import_id)
            .values(is_current=True)
        )

    def set_current(self, import_id: str) -> None:
        try:
            with self._engine.begin() as connection:
                exists = connection.execute(
                    select(legacy_import.c.import_id)
                    .where(legacy_import.c.import_id == import_id)
                ).scalar()
                if exists is None:
                    raise KeyError(import_id)
                self._set_current(connection, import_id)
        except SQLAlchemyError as exc:
            raise HistoryUnavailableError(str(exc)) from exc

    # --- đọc ----------------------------------------------------------

    def _query(self, statement) -> list[dict]:
        try:
            with self._engine.connect() as connection:
                return [_row_to_dict(row) for row in connection.execute(statement)]
        except SQLAlchemyError as exc:
            raise HistoryUnavailableError(str(exc)) from exc

    def list_imports(self, *, limit: int = 50) -> list[dict]:
        return self._query(
            select(legacy_import)
            .order_by(legacy_import.c.imported_at.desc(), legacy_import.c.import_id.desc())
            .limit(limit)
        )

    def current_import(self) -> Optional[dict]:
        rows = self._query(
            select(legacy_import).where(legacy_import.c.is_current.is_(True)).limit(1)
        )
        return rows[0] if rows else None

    def _resolve_import_id(self, import_id: Optional[str]) -> Optional[str]:
        if import_id:
            return import_id
        current = self.current_import()
        return current["import_id"] if current else None

    def query_summary(
        self, year: int, month: Optional[int] = None, *, import_id: Optional[str] = None,
    ) -> list[dict]:
        """Dòng Summary của một kỳ. ``month=None`` → cả năm (kể cả dòng cấp năm)."""
        resolved = self._resolve_import_id(import_id)
        if resolved is None:
            return []
        statement = select(legacy_summary_row).where(
            legacy_summary_row.c.import_id == resolved,
            legacy_summary_row.c.year == year,
        )
        if month is not None:
            statement = statement.where(legacy_summary_row.c.month == month)
        return self._query(statement.order_by(
            legacy_summary_row.c.sheet_name, legacy_summary_row.c.sheet_row,
        ))

    def query_daily(
        self, year: int, month: int, *, import_id: Optional[str] = None,
    ) -> list[dict]:
        resolved = self._resolve_import_id(import_id)
        if resolved is None:
            return []
        return self._query(
            select(legacy_daily_sales)
            .where(
                legacy_daily_sales.c.import_id == resolved,
                legacy_daily_sales.c.year == year,
                legacy_daily_sales.c.month == month,
            )
            .order_by(legacy_daily_sales.c.day)
        )

    def query_monthly_reference(
        self, year: int, *, import_id: Optional[str] = None,
    ) -> list[dict]:
        resolved = self._resolve_import_id(import_id)
        if resolved is None:
            return []
        return self._query(
            select(legacy_monthly_reference)
            .where(
                legacy_monthly_reference.c.import_id == resolved,
                legacy_monthly_reference.c.year == year,
            )
            .order_by(legacy_monthly_reference.c.month)
        )

    def available_periods(self, *, import_id: Optional[str] = None) -> list[tuple[int, Optional[int]]]:
        """Các kỳ (năm, tháng) THỰC SỰ có dòng người bán trong bản hiện tại."""
        resolved = self._resolve_import_id(import_id)
        if resolved is None:
            return []
        rows = self._query(
            select(legacy_summary_row.c.year, legacy_summary_row.c.month)
            .where(
                legacy_summary_row.c.import_id == resolved,
                legacy_summary_row.c.month.isnot(None),
            )
            .group_by(legacy_summary_row.c.year, legacy_summary_row.c.month)
            .order_by(legacy_summary_row.c.year.desc(), legacy_summary_row.c.month.desc())
        )
        return [(row["year"], row["month"]) for row in rows]

    def count_imports(self) -> int:
        rows = self._query(select(func.count().label("total")).select_from(legacy_import))
        return int(rows[0]["total"]) if rows else 0


def build(
    env: Optional[Mapping[str, str]] = None, *, engine: Optional[Engine] = None,
    verify_schema: bool = True,
) -> LegacyRepository:
    """Dựng repository. ``engine`` tiêm sẵn dùng cho test/dev.

    ``verify_schema`` giữ nguyên nguyên tắc fail-closed: database chưa
    ``alembic upgrade head`` thì app KHÔNG khởi động, thay vì chạy lên rồi
    hiển thị lịch sử rỗng.
    """
    if engine is None:
        engine = history_db.build_engine(env)
    if verify_schema:
        history_db.assert_schema_current(engine)
    return LegacyRepository(engine)


__all__ = [
    "HistoryUnavailableError", "ImportResult", "LegacyRepository", "build",
]
