"""Alembic environment — lấy URL từ ``tools.db`` chứ không từ alembic.ini.

Một nguồn cấu hình duy nhất (``HISTORY_DATABASE_URL``) cho cả app lẫn
migration: không thể có chuyện app nói chuyện với một database còn
``alembic upgrade`` lại nâng cấp một database khác.
"""

from __future__ import annotations

from alembic import context

import tools.db as history_db
from tools.db import schema

target_metadata = schema.METADATA


def run_migrations_offline() -> None:
    context.configure(
        url=history_db.resolve_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = history_db.build_engine()
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
