"""Tầng history THUẦN của TASK-PRA-002 — khoá, fingerprint, coverage, reconcile.

Ranh giới cứng (ADR-101, CHECK-PRA002-12): không module nào trong package này
được import ``sqlalchemy``, ``psycopg``, ``alembic`` hay ``flask``. Nó chỉ nói
về giá trị nghiệp vụ; việc ghi xuống database là của
``app/web/history_store.py`` và ``app/web/history_writer.py``.
"""

from app.history import coverage, extraction, keys, models, reconciler

__all__ = ["coverage", "extraction", "keys", "models", "reconciler"]
