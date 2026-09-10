"""Dựng app web THẬT cho test, với dữ liệu ở quy mô chọn được.

Vì sao tách ra khỏi từng file test: bốn file test của đợt UI/API (`STAB-04`,
`STAB-03`, `API-01/02`, `UI-02`) cần đúng cùng một thứ — một `test_client()`
nối vào một snapshot repo SQLite trong bộ nhớ đã có dữ liệu, và không đi ra
mạng. Chép sáu dòng ấy vào từng file là chép luôn cả cơ hội để chúng trôi
khỏi nhau.

Điều gì bị CẮT, và vì sao nói ra ở đây: `select_latest_valid_captures` và
`live_pull.is_configured` đi ra Tracking/đĩa máy Owner. Chúng bị cắt để test
không phụ thuộc mạng — nên mọi số đo lấy từ đây KHÔNG bao gồm thời gian
Tracking, và mọi test ở đây KHÔNG nói gì về đường Tracking.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from sqlalchemy import create_engine

import tools.db as history_db
from app.web import business_service, business_store, history_store
from app.web import server as web_server
from tools.tracking import live_pull

#: "Hôm nay" cố định — cùng lý do như `TODAY` của
#: `tests/test_employee_workspace_ux.py`: một test phụ thuộc ngày thật sẽ
#: đổi kết quả vào ngày mai.
TODAY = date(2026, 9, 30)


def make_engine():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


def make_client(engine, monkeypatch, tmp_path: Path):
    monkeypatch.setattr(web_server, "select_latest_valid_captures",
                        lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(web_server, "_today", lambda: TODAY)
    application = web_server.create_app(
        db_path=tmp_path / "runs.db",
        history=history_store.LegacyRepository(engine),
        snapshots=history_store.SnapshotRepository(engine))
    application.testing = True
    return application.test_client()


def make_service(engine):
    return business_service.BusinessReportService(
        engine=engine,
        store=business_store.BusinessDecisionStore(engine))
