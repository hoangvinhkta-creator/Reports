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
from app.web import identity_gateway  # noqa: E402
from app.web import server as web_server  # noqa: E402
from tools.tracking import live_pull  # noqa: E402
from tests.fixtures import workspace_scale as ws  # noqa: E402
from tests.test_snapshot_repository import (  # noqa: E402
    result_line, source_line, write,
)

#: Mã của BH năm dòng dựng riêng — bài kiểm panel trỏ thẳng vào mã này để
#: xác nhận hình dạng side-panel (`SIMPLE_LINE_THRESHOLD` của `app.js`).
MULTILINE_ORDER = "BH79999"

#: `UI-03` — BA BH khác nhau dùng CHUNG một câu tên hàng chưa phân loại.
#: Bộ `workspace_scale` không có dòng nào ở trạng thái ấy (nó chỉ dựng
#: `TRACKING_DAILY_MIN_MISSING`, tức "thiếu giá", không phải "chưa phân
#: loại"), nên ca quan trọng nhất của `UI-03` — MỘT quyết định phân loại
#: chạm NHIỀU dòng ở NHIỀU BH — sẽ không có mặt để kiểm.
SHARED_IDENTITY_ORDERS = ("BH78001", "BH78002", "BH78003")
SHARED_IDENTITY_PRODUCT = "TIVI SAMSUNG 55 INCH CHUA PHAN LOAI"


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


def _install_shared_identity_lines(repository) -> None:
    """Ba BH dùng chung một tên hàng CHƯA PHÂN LOẠI (`UI-03`).

    Cùng `product_raw` ⟹ cùng `raw_identity_key` ⟹ MỘT lần xác nhận phân
    loại áp cho cả ba (`INV-76`/`INV-87`). Đây chính là mệnh đề mà bài kiểm
    `UI-03` phải chứng minh: client vá ĐỦ mọi dòng bị ảnh hưởng, không riêng
    dòng vừa bấm.
    """
    pairs = []
    for i, order in enumerate(SHARED_IDENTITY_ORDERS):
        source = source_line(
            order, f"SP-SHARED-{i}", 1, row=20_000 + i,
            sale_date=datetime.date(ws.YEAR, ws.MONTH, 12),
            sell_price="3000000", quantity=Decimal("1"),
            discount=Decimal("0"), customer_name=f"Khách Chung {i}",
            customer_phone="0909111222", customer_address="2 Nguyễn Huệ, Q1",
            product_raw=SHARED_IDENTITY_PRODUCT)
        base = result_line(source, status="PENDING")
        fields = {name: getattr(base, name) for name in base.__dataclass_fields__}
        fields.update({
            "status": "PENDING",
            # "Chưa phân loại", KHÔNG phải "thiếu giá": hai trạng thái khác
            # nhau mở hai đường khác nhau trên màn hình (`§PI-01`).
            "pending_reasons": ("IDENTITY_UNRESOLVED",),
            "employee_normalized": "Vinh", "employee_group": "NOI_THANH",
            "lead_source_final": "PERSONAL",
            "total_sales": Decimal("3000000"),
            "kpi_purchase_price": None, "eligible_kpi_profit": None,
            "product_group_final": "DIEN_MAY",
            "conversion_rate_final": Decimal("0.02"),
        })
        pairs.append((source, type(base)(**fields)))
    write(repository, [pair[0] for pair in pairs], run_id="run-scale-shared",
          created_at="2026-10-01T00:00:02", fingerprint="fp-scale-shared",
          results=[pair[1] for pair in pairs])


#: Số dòng mặc định của máy chủ fixture. 90 là đủ cho mọi mệnh đề `UI-01`/
#: `UI-02`/`UI-03` và giữ thời gian khởi động dưới một giây.
DEFAULT_LINES = 90


def build_app(lines: int = DEFAULT_LINES, *, extras: bool = True):
    """App THẬT trên SQLite `StaticPool` — một kết nối sống suốt tiến trình
    (máy chủ dev không đa luồng ở đây, xem `main()`), nên dữ liệu bộ nhớ
    không biến mất giữa hai request như `sqlite://` mặc định có thể làm.

    `lines` — số dòng của `workspace_scale`. `UI-04` chạy một máy chủ THỨ HAI
    ở 5.000 dòng (xem `playwright.config.mjs`): ngân sách DOM chỉ có nghĩa
    trên một khối lượng đại diện, và 90 dòng sẽ xanh với mọi kiến trúc.

    `extras=False` bỏ hai bộ dựng tay ở trên. Bộ `UI-04` không cần chúng và
    bỏ chúng giữ cho bảng kê của nó chỉ có một hình dạng dữ liệu, dễ đếm.
    """
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False},
        poolclass=StaticPool)
    history_db.create_all_for_test(engine)
    repo = history_store.SnapshotRepository(engine)
    ws.install(repo, lines)
    if extras:
        _install_multiline_order(repo)
        _install_shared_identity_lines(repo)

    # `UI-03` — thẩm quyền Product Identity phải sống trong một thư mục
    # TẠM, không trong `data/product_identity/` của repo. Bộ kiểm `UI-03`
    # GHI thật (phân loại, ngoài bảng giá) qua đúng đường sản xuất, và một
    # lần chạy test không được để lại quyết định trong tài sản đã commit —
    # lần chạy sau sẽ thấy dòng ĐÃ phân loại và mọi mệnh đề của `UI-03`
    # biến mất mà không ai thấy vì sao.
    store_dir = Path(tempfile.mkdtemp()) / "product_identity"
    store_dir.mkdir(parents=True, exist_ok=True)
    identity_gateway.DEFAULT_LOG_PATH = store_dir / "mappings.jsonl"
    identity_gateway.DEFAULT_INDEX_PATH = store_dir / "index.json"

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
    parser.add_argument("--lines", type=int, default=DEFAULT_LINES)
    parser.add_argument("--no-extras", action="store_true")
    args = parser.parse_args(argv)
    app = build_app(args.lines, extras=not args.no_extras)
    print(f"reports-playwright-fixture: sẵn sàng trên cổng {args.port}",
          flush=True)
    app.run(host="127.0.0.1", port=args.port, use_reloader=False,
             threaded=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
