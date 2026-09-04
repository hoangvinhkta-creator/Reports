"""Driver database cho history store (ADR-108).

Đây là TẦNG DRIVER — nơi duy nhất dưới repo biết database tồn tại ở dạng
kết nối cụ thể. Tầng business/domain (``app/modules/**``) không import module
này; tầng repository (``app/web/history_store``) nhận sẵn một ``Engine`` đã
dựng ở đây và chỉ nói SQLAlchemy Core.

Production = Managed PostgreSQL; local/test = SQLite (ADR-108, DEC-167).
Cấu hình qua biến môi trường:

``HISTORY_DATABASE_URL``
    URL SQLAlchemy đầy đủ. Nếu không đặt, mặc định là SQLite dưới
    ``<REPORTS_DATA_ROOT|REPO_ROOT>/data/history/history.db``.
``REPORTS_REQUIRE_HISTORY_DB``
    ``1`` (production) → THIẾU ``HISTORY_DATABASE_URL`` là lỗi cấu hình,
    app KHÔNG khởi động. Không bao giờ âm thầm rơi về SQLite/ổ đĩa tạm rồi
    trông như đã lưu lịch sử trong khi thực tế không persistent.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping, Optional

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

from tools.db import schema

REPO_ROOT = Path(__file__).resolve().parents[2]

ALEMBIC_HEAD = "0003_business"

# Alembic ghi phiên bản schema hiện tại vào bảng này; ``assert_schema_current``
# đọc trực tiếp thay vì gọi alembic (alembic KHÔNG được import dưới app/).
VERSION_TABLE = "alembic_version"


class HistoryConfigurationError(RuntimeError):
    """Cấu hình history store sai/thiếu — fail closed, không fallback ngầm."""


def _env(env: Optional[Mapping[str, str]]) -> Mapping[str, str]:
    return os.environ if env is None else env


def default_sqlite_path(env: Optional[Mapping[str, str]] = None) -> Path:
    values = _env(env)
    root = Path(values.get("REPORTS_DATA_ROOT") or REPO_ROOT)
    return root / "data" / "history" / "history.db"


def resolve_url(env: Optional[Mapping[str, str]] = None) -> str:
    values = _env(env)
    url = (values.get("HISTORY_DATABASE_URL") or "").strip()
    if url:
        return url
    if (values.get("REPORTS_REQUIRE_HISTORY_DB") or "").strip() == "1":
        raise HistoryConfigurationError(
            "REPORTS_REQUIRE_HISTORY_DB=1 nhưng thiếu HISTORY_DATABASE_URL. "
            "Production PHẢI trỏ vào PostgreSQL quản lý — không dùng SQLite "
            "trên filesystem tạm của container (lịch sử sẽ mất khi redeploy)."
        )
    path = default_sqlite_path(values)
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path}"


def build_engine(env: Optional[Mapping[str, str]] = None) -> Engine:
    """Dựng ``Engine`` theo cấu hình môi trường. Không tạo schema."""
    return create_engine(resolve_url(env), future=True)


def assert_schema_current(engine: Engine) -> None:
    """Fail closed nếu database chưa được ``alembic upgrade head``.

    Một database trống (hoặc dừng ở revision cũ) mà app vẫn khởi động sẽ cho
    ra trang "chưa có dữ liệu" trong khi sự thật là schema chưa tồn tại — đó
    đúng là kiểu im lặng sai mà check CHECK-PRA001-06 cấm.
    """
    with engine.connect() as connection:
        names = set(inspect(connection).get_table_names())
        if VERSION_TABLE not in names:
            raise HistoryConfigurationError(
                "History database chưa có schema (thiếu bảng "
                f"{VERSION_TABLE}). Chạy `alembic upgrade head` trước khi khởi động."
            )
        current = connection.exec_driver_sql(
            f"SELECT version_num FROM {VERSION_TABLE}"
        ).scalar()
    if current != ALEMBIC_HEAD:
        raise HistoryConfigurationError(
            f"History database ở revision {current!r}, cần {ALEMBIC_HEAD!r}. "
            "Chạy `alembic upgrade head`."
        )


def create_all_for_test(engine: Engine) -> None:
    """Dựng schema TRỰC TIẾP từ ``METADATA`` — chỉ dùng trong test/dev nhanh.

    Đường production luôn đi qua alembic; hàm này tồn tại để test không phải
    khởi tạo alembic runtime cho mỗi database tạm.
    """
    schema.METADATA.create_all(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql(
            f"CREATE TABLE IF NOT EXISTS {VERSION_TABLE} (version_num VARCHAR(32) NOT NULL)"
        )
        connection.exec_driver_sql(f"DELETE FROM {VERSION_TABLE}")
        connection.exec_driver_sql(
            f"INSERT INTO {VERSION_TABLE} (version_num) VALUES ('{ALEMBIC_HEAD}')"
        )
