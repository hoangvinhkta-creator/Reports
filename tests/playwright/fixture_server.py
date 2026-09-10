"""`UI-01`/`UI-02` — máy chủ Flask THẬT cho bộ kiểm Playwright.

Playwright cần một trình duyệt thật nói chuyện với một máy chủ HTTP thật —
`test_client()` (dùng ở mọi test pytest khác, và ở `scripts/stab01_
baseline.py`) không phục vụ qua cổng mạng. File này dựng CÙNG app Flask
thật (`app.web.server.create_app`, không mock tầng nghiệp vụ nào — chỉ cắt
mạng ngoài, cùng cách `scripts/stab01_baseline.py` đã làm) và chạy nó bằng
máy chủ dev của Werkzeug trên một cổng cố định.

Dữ liệu: `tests.fixtures.workspace_scale` (cùng fixture dùng cho
`stab01_baseline.py`/`test_p0_single_transaction.py`) cho một lượng đơn đa
dạng (giá 0, giá null, đơn PENDING…), CỘNG một BH năm dòng dựng riêng ở đây
— fixture gốc chỉ lặp 1/2/3 dòng mỗi đơn (`LINES_PER_ORDER_CYCLE`), và
`UI-02` cần ít nhất một đơn "nhiều dòng" để bài kiểm panel xác nhận nó mở ở
hình dạng side-panel thay vì popover.

Chạy: `.venv/bin/python tests/playwright/fixture_server.py --port 8931`.
Được gọi tự động bởi `playwright.config.mjs` (khối `webServer`) — không cần
chạy tay khi chạy `npx playwright test` hay bộ pytest bọc nó
(`tests/test_playwright_ui_suite.py`).
"""

from __future__ import annotations

import argparse
import datetime
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import tools.db as history_db  # noqa: E402
from app.web import history_store  # noqa: E402
from app.web import server as web_server  # noqa: E402
from tools.tracking import live_pull  # noqa: E402
from tests.fixtures import workspace_scale as ws  # noqa: E402
from tests.test_snapshot_repository import (  # noqa: E402
    result_line, source_line, write,
)

#: Mã của BH năm dòng dựng riêng — bài kiểm panel trỏ thẳng vào mã này để
#: xác nhận hình dạng side-panel (`SIMPLE_LINE_THRESHOLD` của `app.js`).
MULTILINE_ORDER = "BH79999"


def _install_multiline_order(repository) -> None:
    pairs = []
    for i in range(5):
        source = source_line(
            MULTILINE_ORDER, f"SP-EXTRA-{i}", 1, row=10_000 + i,
            sale_date=datetime.date(ws.YEAR, ws.MONTH, 10),
            sell_price=str(2_000_000 + i * 100_000), quantity=Decimal("1"),
            discount=Decimal("0"), customer_name="Khách Nhiều Dòng",
            customer_phone="0909000000", customer_address="1 Đồng Khởi, Q1")
        base = result_line(source, status="AUTO")
        fields = {name: getattr(base, name) for name in base.__dataclass_fields__}
        total = Decimal(str(2_000_000 + i * 100_000))
        purchase = Decimal("1000000")
        fields.update({
            "employee_normalized": "Vinh", "employee_group": "NOI_THANH",
            "lead_source_final": "PERSONAL", "total_sales": total,
            "kpi_purchase_price": purchase,
            "eligible_kpi_profit": total - purchase,
            "product_group_final": "DIEN_MAY",
            "conversion_rate_final": Decimal("0.02"),
        })
        pairs.append((source, type(base)(**fields)))
    write(repository, [pair[0] for pair in pairs], run_id="run-scale-multiline",
          created_at="2026-10-01T00:00:01", fingerprint="fp-scale-multiline",
          results=[pair[1] for pair in pairs])


def build_app():
    """App THẬT trên SQLite `StaticPool` — một kết nối sống suốt tiến trình
    (máy chủ dev không đa luồng ở đây, xem `main()`), nên dữ liệu bộ nhớ
    không biến mất giữa hai request như `sqlite://` mặc định có thể làm."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False},
        poolclass=StaticPool)
    history_db.create_all_for_test(engine)
    repo = history_store.SnapshotRepository(engine)
    ws.install(repo, 90)
    _install_multiline_order(repo)

    web_server.select_latest_valid_captures = lambda: None
    live_pull.is_configured = lambda env=None: False
    web_server._today = lambda: datetime.date(2026, 9, 30)
    app = web_server.create_app(
        db_path=Path(tempfile.mkdtemp()) / "runs.db",
        history=history_store.LegacyRepository(engine),
        snapshots=history_store.SnapshotRepository(engine))
    return app


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8931)
    args = parser.parse_args(argv)
    app = build_app()
    print(f"reports-playwright-fixture: sẵn sàng trên cổng {args.port}",
          flush=True)
    app.run(host="127.0.0.1", port=args.port, use_reloader=False,
             threaded=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
