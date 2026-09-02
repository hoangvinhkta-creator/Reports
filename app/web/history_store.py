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
from app.history import coverage as history_coverage
from app.history import models as history_models
from app.history import reconciler as history_reconciler
from app.legacy.models import LegacyWorkbook
from tools.db.schema import (
    ORIGIN_LEGACY, ORIGIN_PIPELINE, legacy_daily_sales, legacy_import,
    legacy_monthly_reference, legacy_summary_row, order_line_current,
    order_line_result_version, order_line_source_version, reconciliation_flag,
    snapshot_line, source_snapshot,
)


class HistoryUnavailableError(RuntimeError):
    """History store không truy cập được — fail rõ, không giả vờ rỗng."""


class CoverageRangeError(ValueError):
    """Yêu cầu xác nhận đủ KHÔNG hợp lệ — không có gì được ghi (fail-closed)."""


class CoverageAlreadyConfirmedError(RuntimeError):
    """Snapshot đã xác nhận rồi. Xác nhận là BẤT BIẾN ở PRA-002 (mục 7.3)."""


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

    @property
    def engine(self) -> Engine:
        """Cùng một ``Engine`` cho mọi repository của history store: hai origin
        tách BẢNG, không tách nơi lưu (ADR-108)."""
        return self._engine

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




# ---------------------------------------------------------------------------
# TASK-PRA-002 — repository origin PIPELINE_GENERATED.
#
# Bất biến của tầng này, theo thứ tự quan trọng:
#
# 1. APPEND-ONLY. Không có một câu ``delete()`` nào. ``update()`` chỉ chạm
#    ``order_line_current`` (bảng CON TRỎ) — mọi bảng fact chỉ được INSERT.
#    Một source version đã ghi là bằng chứng "kế toán đã sửa gì"; ghi đè nó là
#    xoá đúng thứ mà bảng version sinh ra để giữ.
# 2. MỘT ĐƠN VỊ CÔNG VIỆC. Snapshot + version + membership + result + current
#    + cờ + (R2 artifact/run qua callback ``on_persisted``) nằm trong CÙNG một
#    ``engine.begin()``. Không bao giờ có snapshot "một nửa".
# 3. CẤU TRÚC TRƯỚC, QUERY SAU. PK ``order_line_current`` và các UNIQUE làm
#    cho "một khoá có hai current" hay "một run ghi hai result cho một khoá"
#    KHÔNG THỂ tồn tại ở tầng schema — không phụ thuộc vào việc query có nhớ
#    lọc đúng hay không.
# ---------------------------------------------------------------------------

# Kích thước lô cho mệnh đề IN (...): PostgreSQL và SQLite đều có giới hạn số
# tham số của một câu lệnh; chia lô giữ truy vấn hiện trạng chạy được với
# workbook lớn mà không dựng thêm bảng tạm.
_KEY_CHUNK = 400


@dataclass(frozen=True)
class SnapshotWriteResult:
    snapshot_id: str
    counts: dict
    duplicate_of_snapshot_id: Optional[str]
    not_seen: int = 0


@dataclass(frozen=True)
class CoverageConfirmation:
    """Kết quả của MỘT lần xác nhận đủ — số ứng viên đã bị đưa vào Review.

    ``removed_candidates`` là số CỜ được dựng, KHÔNG phải số dòng bị xoá: ở
    PRA-002 không có dòng nào bị xoá, bị huỷ hay bị loại khỏi tổng.
    """

    snapshot_id: str
    confirmed_range_start: object
    confirmed_range_end: object
    removed_candidates: int


def _decode(data: dict, keys: tuple[str, ...]) -> dict:
    for key in keys:
        if key in data:
            data[key] = _loads(data[key])
    return data


def _key_of(row) -> history_models.LineKey:
    return history_models.LineKey(
        row.order_key, row.product_key, int(row.occurrence_index),
    )


class SnapshotRepository:
    """Đọc/ghi lịch sử snapshot của pipeline (origin ``PIPELINE_GENERATED``)."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    @property
    def engine(self) -> Engine:
        return self._engine

    # --- ghi ----------------------------------------------------------

    def write_snapshot(
        self, *, run_id: str, created_at: str, source_file_name: Optional[str],
        file_fingerprint: str, file_size: Optional[int], header_text: Optional[str],
        sheet_data_rows: int, rows_without_order_id: int,
        source_lines, result_lines, evidence: dict, summary: dict,
        on_persisted=None,
    ) -> SnapshotWriteResult:
        """Ghi TRỌN một lần chạy pipeline vào lịch sử, trong một transaction.

        ``on_persisted`` được gọi SAU khi mọi bản ghi đã nằm trong transaction
        nhưng TRƯỚC commit — đó là chỗ lưu artifact/run lên R2. Nó lỗi thì cả
        snapshot rollback: không bao giờ có một run "thành công" mà lịch sử
        không có, cũng không có một snapshot trỏ tới artifact không tồn tại.
        """
        detected = history_coverage.detected_range(line.sale_date for line in source_lines)
        header = history_coverage.parse_header(header_text)
        try:
            with self._engine.begin() as connection:
                duplicate_of = connection.execute(
                    select(source_snapshot.c.snapshot_id)
                    .where(source_snapshot.c.file_fingerprint == file_fingerprint)
                    .order_by(source_snapshot.c.created_at, source_snapshot.c.snapshot_id)
                    .limit(1)
                ).scalar()
                current = self._load_current(connection, source_lines)
                outcome = history_reconciler.reconcile(source_lines, current)
                counts = outcome.counts()
                # Bước 4 (mục 8): khoá hiện hành NẰM TRONG khoảng đo được của
                # snapshot này mà snapshot không chứa. Phạm vi là khoảng ĐO
                # ĐƯỢC — không phải cả database: một sổ 01–10/09 không có thẩm
                # quyền nói gì về đơn ngày 20/09.
                absent, absent_versions = self._absent_keys_in_range(
                    connection, present=[line.key for line in source_lines],
                    start=detected[0], end=detected[1],
                )
                snapshot_id = self._next_snapshot_id(connection, created_at, file_fingerprint)

                connection.execute(insert(source_snapshot).values(
                    snapshot_id=snapshot_id, origin=ORIGIN_PIPELINE, run_id=run_id,
                    created_at=created_at, source_file_name=source_file_name,
                    file_fingerprint=file_fingerprint, file_size=file_size,
                    duplicate_of_snapshot_id=duplicate_of, header_text=header_text,
                    header_date_min=header[0] if header else None,
                    header_date_max=header[1] if header else None,
                    detected_date_min=detected[0], detected_date_max=detected[1],
                    coverage_state=history_coverage.coverage_state(header, detected),
                    sheet_data_rows=sheet_data_rows,
                    rows_without_order_id=rows_without_order_id,
                    line_count=len(source_lines),
                    order_count=len({line.key.order_key for line in source_lines}),
                    n_insert=counts[history_models.OUTCOME_INSERT],
                    n_same=counts[history_models.OUTCOME_SAME],
                    n_source_changed=counts[history_models.OUTCOME_SOURCE_CHANGED],
                    n_collision=counts[history_models.OUTCOME_COLLISION],
                    n_not_seen=len(absent),
                    evidence_json=_json(evidence) or "{}",
                    summary_json=_json(summary) or "{}",
                ))
                versions = self._insert_source_versions(
                    connection, snapshot_id, created_at, outcome.decisions, current,
                )
                self._insert_membership(connection, snapshot_id, outcome.decisions, versions)
                results = self._insert_result_versions(
                    connection, snapshot_id, run_id, created_at, result_lines,
                    outcome.decisions, versions,
                )
                self._update_current(
                    connection, snapshot_id, created_at, outcome.decisions,
                    versions, results, current,
                )
                self._insert_flags(
                    connection, snapshot_id, run_id, created_at, outcome.decisions, versions,
                )
                self._insert_absence_flags(
                    connection, kind=history_models.FLAG_NOT_SEEN, snapshot_id=snapshot_id,
                    run_id=run_id, created_at=created_at, absent=absent,
                    version_ids=absent_versions, scope="DETECTED",
                    start=detected[0], end=detected[1],
                )
                if on_persisted is not None:
                    on_persisted()
        except SQLAlchemyError as exc:
            raise HistoryUnavailableError(str(exc)) from exc
        return SnapshotWriteResult(snapshot_id, counts, duplicate_of, len(absent))

    @staticmethod
    def _next_snapshot_id(connection, created_at: str, file_fingerprint: str) -> str:
        """``SNAP-<UTC compact>-<fingerprint[:8]>``, thêm hậu tố nếu đã tồn tại.

        Hậu tố lặp theo đúng khuôn ``owner_usability.default_output_path``: hai
        lần upload cùng một file trong CÙNG một giây là chuyện có thật (và là
        đúng kịch bản CHECK-PRA002-03), nên id không được phép va nhau.
        """
        moment = created_at.split("+")[0].rstrip("Z")
        compact = "".join(ch for ch in moment if ch.isdigit())
        base = f"SNAP-{compact}-{file_fingerprint[:8]}"
        candidate, suffix = base, 1
        while connection.execute(
            select(source_snapshot.c.snapshot_id)
            .where(source_snapshot.c.snapshot_id == candidate)
        ).scalar() is not None:
            candidate = f"{base}-{suffix:02d}"
            suffix += 1
        return candidate

    def _load_current(self, connection, source_lines) -> dict:
        """Hiện trạng của ĐÚNG các khoá đơn xuất hiện trong snapshot mới.

        Lọc theo ``order_key`` thay vì đọc cả bảng: bộ nhớ của tiến trình phải
        tỉ lệ với snapshot đang xử lý, không với toàn bộ lịch sử (mục 19).
        """
        order_keys = sorted({line.key.order_key for line in source_lines})
        joined = order_line_current.join(
            order_line_source_version,
            order_line_source_version.c.id == order_line_current.c.current_source_version_id,
        )
        state: dict = {}
        for start in range(0, len(order_keys), _KEY_CHUNK):
            chunk = order_keys[start:start + _KEY_CHUNK]
            highest = {
                _key_of(row): int(row.max_version_no)
                for row in connection.execute(
                    select(
                        order_line_source_version.c.order_key,
                        order_line_source_version.c.product_key,
                        order_line_source_version.c.occurrence_index,
                        func.max(order_line_source_version.c.version_no)
                        .label("max_version_no"),
                    )
                    .where(order_line_source_version.c.order_key.in_(chunk))
                    .group_by(
                        order_line_source_version.c.order_key,
                        order_line_source_version.c.product_key,
                        order_line_source_version.c.occurrence_index,
                    )
                ).all()
            }
            rows = connection.execute(
                select(
                    order_line_current.c.order_key, order_line_current.c.product_key,
                    order_line_current.c.occurrence_index,
                    order_line_current.c.order_key_collision,
                    order_line_current.c.first_seen_snapshot_id,
                    order_line_source_version.c.id.label("version_id"),
                    order_line_source_version.c.version_no,
                    order_line_source_version.c.line_fingerprint,
                    order_line_source_version.c.sale_date,
                    order_line_source_version.c.product_raw,
                    order_line_source_version.c.quantity,
                    order_line_source_version.c.sell_price,
                    order_line_source_version.c.discount,
                    order_line_source_version.c.total_sales_raw,
                    order_line_source_version.c.delivery_cost,
                    order_line_source_version.c.imei,
                    order_line_source_version.c.note_raw,
                    order_line_source_version.c.employee_raw,
                    order_line_source_version.c.source_profit,
                )
                .select_from(joined)
                .where(order_line_current.c.order_key.in_(chunk))
            )
            for row in rows:
                state[_key_of(row)] = history_models.CurrentState(
                    source_version_id=int(row.version_id),
                    version_no=int(row.version_no),
                    max_version_no=highest.get(_key_of(row)),
                    fingerprint=row.line_fingerprint,
                    sale_date=row.sale_date,
                    fingerprint_values=(
                        row.sale_date, row.product_raw, row.quantity, row.sell_price,
                        row.discount, row.total_sales_raw, row.delivery_cost, row.imei,
                        row.note_raw, row.employee_raw, row.source_profit,
                    ),
                    order_key_collision=bool(row.order_key_collision),
                    first_seen_snapshot_id=row.first_seen_snapshot_id,
                )
        return state

    @staticmethod
    def _insert_source_versions(connection, snapshot_id, created_at, decisions, current) -> dict:
        """INSERT các version MỚI, rồi đọc lại id theo khoá tự nhiên.

        Đọc lại bằng ``snapshot_id`` (mỗi version thuộc đúng một snapshot tạo
        ra nó) thay vì dựa vào RETURNING: hành vi giống hệt nhau trên SQLite và
        PostgreSQL, không phụ thuộc thứ tự trả về của dialect.
        """
        rows = [
            {
                "origin": ORIGIN_PIPELINE, "order_key": d.line.key.order_key,
                "product_key": d.line.key.product_key,
                "occurrence_index": d.line.key.occurrence_index,
                "version_no": d.version_no, "snapshot_id": snapshot_id,
                "bh_number": d.line.bh_number, "bh_year_hint": d.line.bh_year_hint,
                "sale_date": d.line.sale_date, "product_raw": d.line.product_raw,
                "quantity": d.line.quantity, "sell_price": d.line.sell_price,
                "discount": d.line.discount, "total_sales_raw": d.line.total_sales_raw,
                "delivery_cost": d.line.delivery_cost,
                "source_profit": d.line.source_profit, "imei": d.line.imei,
                "note_raw": d.line.note_raw, "employee_raw": d.line.employee_raw,
                "row_hash": d.line.row_hash, "line_fingerprint": d.line.fingerprint,
                "changed_fields_json": _json(d.changed_fields),
                "created_at": created_at,
            }
            for d in decisions if d.creates_version
        ]
        if rows:
            connection.execute(insert(order_line_source_version), rows)
        versions = {
            _key_of(row): int(row.id)
            for row in connection.execute(
                select(order_line_source_version.c.id,
                       order_line_source_version.c.order_key,
                       order_line_source_version.c.product_key,
                       order_line_source_version.c.occurrence_index)
                .where(order_line_source_version.c.snapshot_id == snapshot_id)
            )
        }
        # Dòng SAME không tạo version mới — chúng trỏ tới version hiện hành.
        for decision in decisions:
            if not decision.creates_version:
                versions[decision.line.key] = current[decision.line.key].source_version_id
        return versions

    @staticmethod
    def _insert_membership(connection, snapshot_id, decisions, versions) -> None:
        rows = [
            {
                "snapshot_id": snapshot_id, "order_key": d.line.key.order_key,
                "product_key": d.line.key.product_key,
                "occurrence_index": d.line.key.occurrence_index,
                "source_version_id": versions[d.line.key],
                "source_row": d.line.source_row, "outcome": d.outcome,
            }
            for d in decisions
        ]
        if rows:
            connection.execute(insert(snapshot_line), rows)

    @staticmethod
    def _insert_result_versions(
        connection, snapshot_id, run_id, created_at, result_lines, decisions, versions,
    ) -> dict:
        """Một result version cho mỗi khoá của snapshot, TRỪ khoá COLLISION.

        Khoá COLLISION cố ý không có kết quả gắn vào hiện trạng: hệ thống chưa
        biết dòng mới có phải cùng một đơn hay không, nên nó không được phép
        đóng góp một con số nào vào trạng thái hiện hành.
        """
        skipped = {d.line.key for d in decisions
                   if d.outcome == history_models.OUTCOME_COLLISION}
        rows = [
            {
                "origin": ORIGIN_PIPELINE, "run_id": run_id, "snapshot_id": snapshot_id,
                "order_key": r.key.order_key, "product_key": r.key.product_key,
                "occurrence_index": r.key.occurrence_index,
                "source_version_id": versions[r.key], "status": r.status,
                "pending_reasons_json": _json(list(r.pending_reasons)),
                "total_sales": r.total_sales,
                "employee_normalized": r.employee_normalized,
                "employee_group": r.employee_group,
                "lead_source_final": r.lead_source_final,
                "identity_namespace": r.identity_namespace,
                "canonical_product_code": r.canonical_product_code,
                "accounting_purchase_price": r.accounting_purchase_price,
                "price_source": r.price_source, "composition_rule": r.composition_rule,
                "accounting_profit": r.accounting_profit,
                "kpi_purchase_price": r.kpi_purchase_price,
                "kpi_purchase_provenance": r.kpi_purchase_provenance,
                "eligible_kpi_profit": r.eligible_kpi_profit,
                "product_group_final": r.product_group_final,
                "conversion_scheme_final": r.conversion_scheme_final,
                "conversion_rate_final": r.conversion_rate_final,
                "result_fingerprint": r.result_fingerprint, "created_at": created_at,
            }
            for r in result_lines if r.key not in skipped
        ]
        if rows:
            connection.execute(insert(order_line_result_version), rows)
        return {
            _key_of(row): int(row.id)
            for row in connection.execute(
                select(order_line_result_version.c.id,
                       order_line_result_version.c.order_key,
                       order_line_result_version.c.product_key,
                       order_line_result_version.c.occurrence_index)
                .where(order_line_result_version.c.run_id == run_id)
            )
        }

    @staticmethod
    def _update_current(
        connection, snapshot_id, created_at, decisions, versions, results, current,
    ) -> None:
        """Bảng con trỏ — nơi DUY NHẤT của tầng này được UPDATE.

        Mỗi lần chạm vào đây đều đi kèm một bản ghi ``snapshot_line`` (và cờ
        khi có) giải thích vì sao, nên không có thay đổi hiện trạng nào không
        truy được về một snapshot cụ thể.
        """
        fresh = []
        for decision in decisions:
            key = decision.line.key
            if key not in current:
                fresh.append({
                    "order_key": key.order_key, "product_key": key.product_key,
                    "occurrence_index": key.occurrence_index, "origin": ORIGIN_PIPELINE,
                    "current_source_version_id": versions[key],
                    "current_result_version_id": results[key],
                    "first_seen_snapshot_id": snapshot_id,
                    "last_seen_snapshot_id": snapshot_id,
                    "sale_date": decision.line.sale_date,
                    "order_key_collision": False, "updated_at": created_at,
                })
                continue
            if not decision.becomes_current:
                # COLLISION: hiện trạng GIỮ NGUYÊN, chỉ bật cờ để người dùng
                # thấy có tranh chấp danh tính trên khoá này.
                connection.execute(
                    update(order_line_current)
                    .where(*_current_where(key))
                    .values(order_key_collision=True, updated_at=created_at)
                )
                continue
            values = {
                "current_result_version_id": results[key],
                "last_seen_snapshot_id": snapshot_id, "updated_at": created_at,
            }
            if decision.creates_version:
                values["current_source_version_id"] = versions[key]
                values["sale_date"] = decision.line.sale_date
            connection.execute(
                update(order_line_current).where(*_current_where(key)).values(**values)
            )
        if fresh:
            connection.execute(insert(order_line_current), fresh)

    @staticmethod
    def _insert_flags(connection, snapshot_id, run_id, created_at, decisions, versions) -> None:
        rows = []
        for decision in decisions:
            key = decision.line.key
            if decision.outcome == history_models.OUTCOME_SOURCE_CHANGED:
                kind, detail = history_models.FLAG_SOURCE_CHANGED, decision.changed_fields
            elif decision.outcome == history_models.OUTCOME_COLLISION:
                kind, detail = history_models.FLAG_COLLISION, decision.collision_detail
            else:
                continue
            rows.append({
                "kind": kind, "order_key": key.order_key, "product_key": key.product_key,
                "occurrence_index": key.occurrence_index,
                "raised_by_snapshot_id": snapshot_id, "run_id": run_id,
                "from_version_id": decision.previous_version_id,
                "to_version_id": versions[key], "detail_json": _json(detail),
                "created_at": created_at, "acknowledged_at": None,
            })
        if rows:
            connection.execute(insert(reconciliation_flag), rows)

    def _absent_keys_in_range(self, connection, *, present, start, end):
        """Khoá hiện hành trong ``[start, end]`` KHÔNG có trong tập ``present``.

        Dùng chung cho bước 4 (phạm vi = khoảng đo được) và bước R (phạm vi =
        khoảng đã xác nhận). Lọc theo ngày NGAY TRONG SQL để bộ nhớ tỉ lệ với
        kỳ của snapshot chứ không với toàn bộ lịch sử; luật vắng mặt thật sự
        vẫn nằm ở hàm thuần ``reconciler.absent_keys`` — SQL ở đây chỉ thu hẹp
        đầu vào, không được phép là nơi định nghĩa nghiệp vụ.
        """
        if start is None or end is None:
            return (), {}
        rows = connection.execute(
            select(
                order_line_current.c.order_key, order_line_current.c.product_key,
                order_line_current.c.occurrence_index, order_line_current.c.sale_date,
                order_line_current.c.order_key_collision,
                order_line_current.c.current_source_version_id,
            )
            .where(order_line_current.c.sale_date >= start,
                   order_line_current.c.sale_date <= end)
        ).all()
        candidates = [
            history_models.CurrentKey(
                key=_key_of(row), sale_date=row.sale_date,
                order_key_collision=bool(row.order_key_collision),
            )
            for row in rows
        ]
        version_ids = {
            _key_of(row): int(row.current_source_version_id) for row in rows
        }
        absent = history_reconciler.absent_keys(
            present=present, candidates=candidates, start=start, end=end,
        )
        return absent, version_ids

    @staticmethod
    def _insert_absence_flags(
        connection, *, kind, snapshot_id, run_id, created_at, absent, version_ids,
        scope, start, end,
    ) -> None:
        """Ghi cờ vắng mặt. KHÔNG chạm ``order_line_current``, KHÔNG xoá gì.

        Đây là toàn bộ hệ quả của "không thấy" ở PRA-002: một dòng trong bảng
        cờ. Con trỏ hiện hành, các bảng version và mọi con số analytics đi ra
        khỏi hàm này y hệt lúc đi vào — bất biến an toàn của slice B.
        """
        if not absent:
            return
        detail = {
            "scope": scope,
            "range_start": start.isoformat() if start else None,
            "range_end": end.isoformat() if end else None,
        }
        connection.execute(insert(reconciliation_flag), [
            {
                "kind": kind, "order_key": key.order_key, "product_key": key.product_key,
                "occurrence_index": key.occurrence_index,
                "raised_by_snapshot_id": snapshot_id, "run_id": run_id,
                "from_version_id": version_ids.get(key), "to_version_id": None,
                "detail_json": _json(detail), "created_at": created_at,
                "acknowledged_at": None,
            }
            for key in absent
        ])

    def confirm_coverage(
        self, snapshot_id: str, *, start, end, confirmed: bool, confirmed_at: str,
    ) -> CoverageConfirmation:
        """Đường DUY NHẤT ghi ``CONFIRMED_COMPLETE`` — và chỉ khi ``confirmed``.

        Hai việc trong MỘT transaction (mục 7.3): nâng coverage của snapshot
        này, và chạy bước R trên đúng phạm vi vừa được xác nhận. Không tách
        được, vì một coverage đã CONFIRMED mà chưa chạy bước R sẽ là một lời
        khẳng định "sổ đầy đủ" chưa ai đối chiếu.

        Thứ hàm này KHÔNG làm, và không bao giờ được làm: xoá dòng, đổi con
        trỏ hiện hành, đổi bất kỳ con số analytics nào, hay kết luận một đơn
        đã bị huỷ. ``REMOVED_IN_SOURCE_CANDIDATE`` là một trạng thái REVIEW,
        không phải một quyết định nghiệp vụ (phân xử = PRA-004 + Owner).
        """
        try:
            with self._engine.begin() as connection:
                row = connection.execute(
                    select(source_snapshot).where(
                        source_snapshot.c.snapshot_id == snapshot_id)
                ).mappings().first()
                if row is None:
                    raise KeyError(snapshot_id)
                already = row["coverage_state"] == history_models.CONFIRMED_COMPLETE
                reason = history_coverage.confirmation_error(
                    confirmed=confirmed, start=start, end=end,
                    detected=(row["detected_date_min"], row["detected_date_max"]),
                    already_confirmed=already,
                )
                if already:
                    raise CoverageAlreadyConfirmedError(reason)
                if reason is not None:
                    raise CoverageRangeError(reason)

                # Bước R dựa trên MEMBERSHIP của chính snapshot này (DEC-171
                # #6), không dựa trên ``last_seen``: một snapshot chồng kỳ
                # upload sau đó đã đổi ``last_seen`` và sẽ tạo REMOVED giả.
                present = [
                    _key_of(member) for member in connection.execute(
                        select(snapshot_line.c.order_key, snapshot_line.c.product_key,
                               snapshot_line.c.occurrence_index)
                        .where(snapshot_line.c.snapshot_id == snapshot_id)
                    )
                ]
                absent, version_ids = self._absent_keys_in_range(
                    connection, present=present, start=start, end=end,
                )
                self._insert_absence_flags(
                    connection, kind=history_models.FLAG_REMOVED_CANDIDATE,
                    snapshot_id=snapshot_id, run_id=row["run_id"],
                    created_at=confirmed_at, absent=absent, version_ids=version_ids,
                    scope="CONFIRMED", start=start, end=end,
                )
                connection.execute(
                    update(source_snapshot)
                    .where(source_snapshot.c.snapshot_id == snapshot_id)
                    .values(
                        coverage_state=history_models.CONFIRMED_COMPLETE,
                        confirmed_range_start=start, confirmed_range_end=end,
                        confirmed_at=confirmed_at,
                        n_removed_candidate=len(absent),
                    )
                )
        except SQLAlchemyError as exc:
            raise HistoryUnavailableError(str(exc)) from exc
        return CoverageConfirmation(snapshot_id, start, end, len(absent))

    # --- đọc ----------------------------------------------------------

    def _read(self, statement) -> list[dict]:
        try:
            with self._engine.connect() as connection:
                return [dict(row._mapping) for row in connection.execute(statement)]
        except SQLAlchemyError as exc:
            raise HistoryUnavailableError(str(exc)) from exc

    def list_snapshots(self, *, limit: int = 50) -> list[dict]:
        return [
            _decode(row, ("summary_json", "evidence_json"))
            for row in self._read(
                select(source_snapshot)
                .order_by(source_snapshot.c.created_at.desc(),
                          source_snapshot.c.snapshot_id.desc())
                .limit(limit)
            )
        ]

    def get_snapshot(self, snapshot_id: str) -> Optional[dict]:
        rows = self._read(
            select(source_snapshot).where(source_snapshot.c.snapshot_id == snapshot_id)
        )
        return _decode(rows[0], ("summary_json", "evidence_json")) if rows else None

    def list_flags(self, *, snapshot_id: Optional[str] = None, limit: int = 200) -> list[dict]:
        statement = select(reconciliation_flag)
        if snapshot_id is not None:
            statement = statement.where(
                reconciliation_flag.c.raised_by_snapshot_id == snapshot_id
            )
        return self._with_absence_state([
            _decode(row, ("detail_json",))
            for row in self._read(statement.order_by(reconciliation_flag.c.id).limit(limit))
        ])

    def _with_absence_state(self, flags: list[dict]) -> list[dict]:
        """Gắn ``is_active`` cho cờ vắng mặt — DẪN XUẤT, không sửa lịch sử.

        Một cờ "không thấy dòng này" là một phát biểu đúng vĩnh viễn về
        snapshot đã dựng nó; nếu kế toán xuất lại sổ và dòng đó quay về, cờ cũ
        KHÔNG sai và KHÔNG được xoá — nó chỉ thôi mô tả hiện tại. Vì vậy trạng
        thái "còn hiệu lực" được tính lúc đọc, bằng cách hỏi lịch sử
        membership: khoá này có xuất hiện ở snapshot nào SAU snapshot đã dựng
        cờ không? (Bảng cờ vẫn append-only — ``acknowledged_at`` luôn NULL.)
        """
        for flag in flags:
            flag["is_active"] = None
            flag["seen_again_in_snapshot_id"] = None
        absence = [f for f in flags
                   if f["kind"] in history_models.ABSENCE_FLAG_KINDS]
        if not absence:
            return flags
        raised_at = self._snapshot_times({f["raised_by_snapshot_id"] for f in absence})
        latest = self._latest_membership({
            (f["order_key"], f["product_key"], f["occurrence_index"]) for f in absence
        })
        for flag in absence:
            key = (flag["order_key"], flag["product_key"], flag["occurrence_index"])
            seen, anchor = latest.get(key), raised_at.get(flag["raised_by_snapshot_id"])
            # So sánh NGẶT: chỉ một snapshot có ``created_at`` LỚN HƠN hẳn mới
            # được coi là "dòng đã quay lại". Hai snapshot cùng một giây không
            # có thứ tự đáng tin (``snapshot_id`` sắp theo fingerprint, không
            # theo thời gian), và ở đây nghiêng về phía an toàn có nghĩa là
            # GIỮ cờ ở trạng thái còn hiệu lực: một cảnh báo thừa để người dùng
            # tự kiểm còn hơn âm thầm giấu một sự vắng mặt thật. Không con số
            # nghiệp vụ nào phụ thuộc vào nhãn này (hiện trạng và tổng tiền
            # không bao giờ do cờ quyết định).
            reappeared = (
                seen is not None and anchor is not None and seen[0] > anchor
            )
            flag["is_active"] = not reappeared
            flag["seen_again_in_snapshot_id"] = seen[1] if reappeared else None
        return flags

    def _snapshot_times(self, snapshot_ids) -> dict:
        """``{snapshot_id: created_at}`` cho đúng các snapshot đã dựng cờ."""
        wanted = sorted(snapshot_ids)
        times: dict = {}
        for start in range(0, len(wanted), _KEY_CHUNK):
            for row in self._read(
                select(source_snapshot.c.snapshot_id, source_snapshot.c.created_at)
                .where(source_snapshot.c.snapshot_id.in_(wanted[start:start + _KEY_CHUNK]))
            ):
                times[row["snapshot_id"]] = row["created_at"]
        return times

    def _latest_membership(self, keys) -> dict:
        """Snapshot MỚI NHẤT từng chứa mỗi khoá, theo bảng ``snapshot_line``."""
        order_keys = sorted({key[0] for key in keys})
        wanted = set(keys)
        latest: dict = {}
        joined = snapshot_line.join(
            source_snapshot, snapshot_line.c.snapshot_id == source_snapshot.c.snapshot_id,
        )
        for start in range(0, len(order_keys), _KEY_CHUNK):
            for row in self._read(
                select(
                    snapshot_line.c.order_key, snapshot_line.c.product_key,
                    snapshot_line.c.occurrence_index, snapshot_line.c.snapshot_id,
                    source_snapshot.c.created_at,
                )
                .select_from(joined)
                .where(snapshot_line.c.order_key.in_(order_keys[start:start + _KEY_CHUNK]))
            ):
                key = (row["order_key"], row["product_key"], row["occurrence_index"])
                if key not in wanted:
                    continue
                position = (row["created_at"], row["snapshot_id"])
                if latest.get(key) is None or position > latest[key]:
                    latest[key] = position
        return latest

    def run_ids_with_snapshot(self, run_ids) -> set:
        """Các ``run_id`` THỰC SỰ có snapshot — dùng để gắn nhãn trung thực.

        Một run tồn tại trên R2 mà không có snapshot là một lần ghi lịch sử đã
        hỏng; tab Dữ liệu phải nói ra điều đó chứ không im lặng bỏ qua.
        """
        wanted = sorted(set(run_ids))
        found: set = set()
        for start in range(0, len(wanted), _KEY_CHUNK):
            found.update(row["run_id"] for row in self._read(
                select(source_snapshot.c.run_id)
                .where(source_snapshot.c.run_id.in_(wanted[start:start + _KEY_CHUNK]))
            ))
        return found

    def current_totals(self, *, date_from=None, date_to=None) -> dict:
        """Trạng thái HIỆN HÀNH theo kỳ — không cộng dồn version lịch sử.

        Mỗi khoá góp đúng MỘT dòng vì ``order_line_current`` có PK theo khoá:
        no-double-count là tính chất của cấu trúc bảng, không phải của việc
        câu truy vấn này có nhớ ``DISTINCT`` hay không.
        """
        joined = order_line_current.join(
            order_line_result_version,
            order_line_result_version.c.id == order_line_current.c.current_result_version_id,
        )
        statement = select(
            func.count().label("lines"),
            func.count(func.distinct(order_line_current.c.order_key)).label("orders"),
            func.sum(order_line_result_version.c.total_sales).label("total_sales"),
        ).select_from(joined)
        for condition in _period(date_from, date_to):
            statement = statement.where(condition)
        row = self._read(statement)[0]
        return {
            "lines": int(row["lines"] or 0), "orders": int(row["orders"] or 0),
            "total_sales": row["total_sales"] or Decimal("0"),
        }

    def current_fingerprints(self, *, date_from=None, date_to=None) -> dict:
        """``{(khoá): line_fingerprint}`` của hiện trạng — oracle cho đẳng thức
        ``state(A rồi B) == state(B)`` (mục 11.5)."""
        joined = order_line_current.join(
            order_line_source_version,
            order_line_source_version.c.id == order_line_current.c.current_source_version_id,
        )
        statement = select(
            order_line_current.c.order_key, order_line_current.c.product_key,
            order_line_current.c.occurrence_index,
            order_line_source_version.c.line_fingerprint,
        ).select_from(joined)
        for condition in _period(date_from, date_to):
            statement = statement.where(condition)
        return {
            (row["order_key"], row["product_key"], row["occurrence_index"]):
                row["line_fingerprint"]
            for row in self._read(statement)
        }

    def count_flags(self, *, kind: Optional[str] = None) -> int:
        statement = select(func.count().label("total")).select_from(reconciliation_flag)
        if kind is not None:
            statement = statement.where(reconciliation_flag.c.kind == kind)
        return int(self._read(statement)[0]["total"] or 0)


def _current_where(key):
    return (
        order_line_current.c.order_key == key.order_key,
        order_line_current.c.product_key == key.product_key,
        order_line_current.c.occurrence_index == key.occurrence_index,
    )


def _period(date_from, date_to) -> list:
    conditions = []
    if date_from is not None:
        conditions.append(order_line_current.c.sale_date >= date_from)
    if date_to is not None:
        conditions.append(order_line_current.c.sale_date <= date_to)
    return conditions


def build_snapshots(
    env: Optional[Mapping[str, str]] = None, *, engine: Optional[Engine] = None,
    verify_schema: bool = True,
) -> SnapshotRepository:
    """Repository PRA-002 trên CÙNG một ``Engine`` với ``LegacyRepository``."""
    if engine is None:
        engine = history_db.build_engine(env)
    if verify_schema:
        history_db.assert_schema_current(engine)
    return SnapshotRepository(engine)


__all__ = [
    "CoverageAlreadyConfirmedError", "CoverageConfirmation", "CoverageRangeError",
    "HistoryUnavailableError", "ImportResult", "LegacyRepository",
    "SnapshotRepository", "SnapshotWriteResult", "build", "build_snapshots",
]
