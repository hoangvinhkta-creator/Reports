"""Đường upload web THẬT: workbook → Tracking → giá của ngày bán (R1).

Bộ này tồn tại vì một lý do rất cụ thể. `tests/test_daily_min_contract.py` và
`tests/test_daily_min_vertical.py` đều NHẬN sẵn một ảnh chụp MIN, nên cả hai
xanh rực trong khi `app/web/server.py` không hề gọi hợp đồng `daily-min-v1` —
mọi dòng Tracking Pending, báo cáo vẫn tạo ra bình thường, và nó trông y hệt
một báo cáo có giá vốn. Không bài kiểm nào bắt được, vì không bài nào đi qua
ĐÚNG chỗ người dùng bấm nút.

Ở đây thì có: một lượt `POST /run` với workbook thật, đi qua điều phối thật
(`_select_captures_for_run` → `live_pull` → kế hoạch hỏi giá → hợp đồng), qua
pipeline thật, qua xuất Excel thật; rồi mở file kết quả ra đọc con số.

Chỉ MỘT thứ được thay: lớp socket. Hai seam `_http_fetcher`/`_http_poster` —
đúng hai seam mà các script capture đã dùng để test không cần mạng — trả về
payload hợp đồng thay vì đi ra Internet. Không có mock nào ở tầng nghiệp vụ.
"""

from __future__ import annotations

import io
from datetime import date, datetime, timezone
from pathlib import Path

import openpyxl
import pytest

from app import beta_telemetry, owner_usability
from app.web import server as web_server
from tests.support import daily_min_fixtures as dmin
from tests.test_daily_min_vertical import CATALOG, ROWS, write_sales
from tests.test_tracking_history_reader import build_export
from tools.tracking import capture_daily_min, live_pull

SALE_DAY = date(2026, 9, 3)
GIA_NGAY_BAN = 6_800          # nghìn VND — MIN của 03/09
GIA_NGAY_KHAC = 6_000         # nghìn VND — MIN của 04/09, KHÔNG được dùng
GIA_LICH_SU_CU = 4_444        # nghìn VND — `tp/ton`, KHÔNG được dùng


def contract_page(body: dict) -> dict:
    """Trả lời của Tracking cho ĐÚNG những cặp (mã, ngày) đã hỏi.

    Cố ý trả giá KHÁC NHAU cho 03/09 và 04/09: nếu một nhánh nào đó lấy "bản
    mới nhất" thay vì bản của ngày bán, con số trong file Excel đổi ngay.
    """
    records = []
    for code in body["product_codes"]:
        for day, price in (("2026-09-03", GIA_NGAY_BAN), ("2026-09-04", GIA_NGAY_KHAC)):
            if body["date_from"] <= day <= body["date_to"]:
                records.append(dmin.record(code, day, min_price=price))
    return {
        **dmin.contract(
            date_from=body["date_from"], date_to=body["date_to"], records=records,
        ),
        "next_cursor": None,
    }


@pytest.fixture
def tracking(monkeypatch):
    """Tracking giả ở TẦNG SOCKET — mọi tầng trên là mã production thật."""
    calls: dict[str, list] = {"post": []}

    def envelope(kind, extra):
        def build(fetch, *, capture_id, captured_by, source_system_ref,
                  captured_at=None, **kw):
            calls.setdefault(kind, []).append(capture_id)
            return {
                "capture_id": capture_id,
                "captured_at": (captured_at or datetime.now(timezone.utc)).isoformat(),
                "captured_by": captured_by,
                "source_system_ref": source_system_ref,
                "content_hash": f"hash-{kind}",
                "capture_status": "COMPLETE",
                **extra,
            }
        return build

    # Lịch sử `tp/ton` CÓ MẶT và CÓ GIÁ cho đúng những mã ấy: nhánh nào rơi về
    # nguồn cũ sẽ ra 4.444.000 thay vì 6.800.000, và bài kiểm thấy ngay.
    monkeypatch.setattr(live_pull, "_build_history_capture", envelope(
        "history",
        {"data": build_export(
            prices={row["tracking_code"]: GIA_LICH_SU_CU for row in CATALOG})},
    ))
    monkeypatch.setattr(live_pull.capture_tracking_catalog, "build_capture",
                        envelope("catalog", {"rows": CATALOG}))
    monkeypatch.setattr(live_pull.capture_inv_map, "build_capture",
                        envelope("inv_map", {"entries": {}}))

    def poster(source_url, api_key):
        def post(body):
            calls["post"].append(body)
            return contract_page(body)
        return post

    monkeypatch.setattr(capture_daily_min, "_http_poster", poster)
    monkeypatch.setattr(live_pull, "_http_fetcher", lambda url, key: (lambda node: {}))
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: True)
    monkeypatch.setenv("TRACKING_REPORT_SOURCE_URL", "https://tracking.test")
    monkeypatch.setenv("TRACKING_REPORT_API_KEY", "khoa-kiem-thu")
    return calls


@pytest.fixture
def app(monkeypatch, tmp_path, tracking):
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "ARTIFACT_DIR",
                        (tmp_path / "outputs" / "reports").resolve())
    monkeypatch.setattr(web_server, "TRACKING_TEMP_DIR", tmp_path / "tracking_live_tmp")
    monkeypatch.setattr(beta_telemetry, "record_run", lambda record, **kw: None)

    # `run_owner_report` THẬT, chỉ đổi nơi ghi file kết quả sang thư mục tạm —
    # `repo_root` là default argument nên không monkeypatch được từ ngoài.
    real = owner_usability.run_owner_report
    monkeypatch.setattr(
        web_server, "run_owner_report",
        lambda *, sales, captures=None, identity_store_view=None: real(
            sales=sales, captures=captures, repo_root=tmp_path,
            identity_store_view=identity_store_view),
    )
    application = web_server.create_app(db_path=tmp_path / "runs.db")
    application.testing = True
    return application


def upload(client, path: Path):
    return client.post(
        "/run",
        data={"workbook": (io.BytesIO(path.read_bytes()), "so-thang-9.xlsx")},
        content_type="multipart/form-data",
    )


def order_lines(artifact_dir: Path):
    files = sorted(artifact_dir.glob("*.xlsx"))
    assert files, "không có artifact nào được ghi ra"
    book = openpyxl.load_workbook(files[-1], data_only=True)
    try:
        sheet = book["Order Lines"]
        header = [c.value for c in sheet[1]]
        rows = [tuple(c.value for c in row) for row in sheet.iter_rows(min_row=2)]
        return header, rows
    finally:
        book.close()


# ======================================================================


def test_a_web_upload_prices_the_sale_day_end_to_end(app, tracking, tmp_path):
    """Câu hỏi trung tâm của R1, hỏi ở ĐÚNG chỗ Owner bấm nút."""
    sales = write_sales(tmp_path / "so.xlsx", ROWS[:2], day=SALE_DAY)
    resp = upload(app.test_client(), sales)
    assert resp.status_code == 302

    # Hợp đồng ĐƯỢC GỌI, đúng một lượt, với kế hoạch suy từ chính sổ này.
    assert len(tracking["post"]) == 1
    body = tracking["post"][0]
    assert body["product_codes"] == ["TRK-A", "TRK-B"]
    assert (body["date_from"], body["date_to"]) == ("2026-09-03", "2026-09-03")

    header, rows = order_lines(web_server.ARTIFACT_DIR)
    cot_gia = header.index("Giá nhập kế toán / công khai")
    gia = {r[header.index("OrderID / Số BH")]: r[cot_gia] for r in rows}
    assert gia["BH7001"] == GIA_NGAY_BAN * 1000
    assert gia["BH7001"] != GIA_NGAY_KHAC * 1000     # không lấy bản mới nhất
    assert gia["BH7001"] != GIA_LICH_SU_CU * 1000    # không rơi về nguồn cũ


def test_the_web_run_labels_the_price_source_it_actually_used(app, tmp_path):
    sales = write_sales(tmp_path / "so.xlsx", ROWS[:1], day=SALE_DAY)
    upload(app.test_client(), sales)
    header, rows = order_lines(web_server.ARTIFACT_DIR)
    assert rows[0][header.index("Nguồn giá")] == "TRACKING_DAILY_MIN"


def test_the_run_evidence_records_which_capture_priced_it(app, tmp_path):
    """Một run không tra lại được nguồn giá của nó là một run không kiểm được."""
    client = app.test_client()
    upload(client, write_sales(tmp_path / "so.xlsx", ROWS[:1], day=SALE_DAY))
    registry = client.application.config["RUN_REGISTRY"]
    run_id = sorted(p.stem for p in web_server.ARTIFACT_DIR.glob("*.xlsx"))[-1]
    evidence = registry.get_run(run_id).tracking_evidence
    assert evidence["daily_min_status"] == "COMPLETE"
    assert evidence["daily_min_capture_id"].startswith("LIVE-DMIN-")
    assert evidence["daily_min_date_from"] == "2026-09-03"
    assert evidence["daily_min_query_revision"] == dmin.QUERY_REVISION


def test_the_temporary_daily_min_capture_does_not_outlive_the_run(app, tmp_path):
    """`S071 §10` — authority thô của Tracking không ở lại trên đĩa máy chủ."""
    upload(app.test_client(), write_sales(tmp_path / "so.xlsx", ROWS[:1], day=SALE_DAY))
    left = list((tmp_path / "tracking_live_tmp").glob("*.json"))
    assert left == []


def test_a_tracking_price_outage_stops_the_run_instead_of_pricing_nothing(
    app, monkeypatch, tmp_path
):
    """Không có giá thì KHÔNG có báo cáo — chứ không phải một báo cáo rỗng giá.

    Trước bản này, một hợp đồng giá hỏng (hay chỉ đơn giản là chưa được gọi)
    cho ra đúng một báo cáo trông hoàn chỉnh với mọi dòng Tracking Pending.
    """
    monkeypatch.setattr(
        capture_daily_min, "_http_poster",
        lambda url, key: (lambda body: {"ok": False, "ly": "nguon-hong"}),
    )
    resp = upload(app.test_client(),
                  write_sales(tmp_path / "so.xlsx", ROWS[:1], day=SALE_DAY))
    assert resp.status_code == 503
    assert "Tracking" in resp.get_data(as_text=True)
    assert list(web_server.ARTIFACT_DIR.glob("*.xlsx")) == []


def test_a_period_wider_than_one_run_is_refused_with_guidance_not_a_priceless_report(
    app, tmp_path
):
    """Sổ quá rộng ⇒ 400 kèm hướng dẫn TÁCH KỲ, và KHÔNG có artifact nào.

    Bản trước bỏ qua lượt hỏi giá và vẫn tạo báo cáo: đầy đủ hình thức, không
    một giá vốn nào. Đó là kết cục tệ nhất trong ba kết cục có thể — tệ hơn cả
    một lỗi, vì nó trông giống thành công.
    """
    import openpyxl as _oxl

    from tests.fixtures.synthetic_workbook import HEADER

    book = _oxl.Workbook()
    sheet = book.active
    sheet.title = "SỔ CHI TIẾT BÁN HÀNG"
    sheet.append(["SỔ CHI TIẾT BÁN HÀNG"])
    sheet.append(["Từ ngày 01/01/2020 đến ngày 31/12/2026"])
    sheet.append([])
    sheet.append(HEADER)
    sheet.append(["", "", "Diễn giải chung"])
    for (order_id, product, quantity, sell), day in (
        (ROWS[0], date(2020, 1, 5)), (ROWS[1], date(2026, 12, 20)),
    ):
        sheet.append([
            day, order_id, f"Bán hàng {order_id}", product, f"KH{order_id}",
            f"Khách {order_id}", "1 Đường Test", "0900000000", quantity, sell,
            sell * quantity, 0, "Vũ Hạnh Ly 0868345633", "Shipper", 0, None, None,
        ])
        sheet.cell(sheet.max_row, 4).data_type = "s"
    path = tmp_path / "muoi-nam.xlsx"
    book.save(path)
    book.close()

    resp = upload(app.test_client(), path)
    assert resp.status_code == 400
    text = resp.get_data(as_text=True)
    assert "tách sổ" in text.lower()
    assert "thử lại sau" not in text.lower()   # lời khuyên sai ở đây
    assert list(web_server.ARTIFACT_DIR.glob("*.xlsx")) == []
    assert list((tmp_path / "tracking_live_tmp").glob("*.json")) == []


def test_a_broken_legacy_history_does_not_stop_a_web_report(app, monkeypatch, tmp_path):
    """Nhánh `tp/ton` cũ KHÔNG quyết định giá nào từ R1 (`ADR-110` §6).

    Để một sự cố ở đó chặn cả báo cáo là bắt hôm nay phụ thuộc vào một nguồn
    hôm nay không dùng. Giá vẫn phải ra, và bằng chứng phải NÓI RA rằng nhánh
    legacy vắng mặt — chứ không im lặng.
    """
    def hong(fetch, *, capture_id, captured_by, source_system_ref,
             captured_at=None, **kw):
        return {
            "capture_id": capture_id,
            "captured_at": (captured_at or datetime.now(timezone.utc)).isoformat(),
            "captured_by": captured_by,
            "source_system_ref": source_system_ref,
            "content_hash": "hash-pph",
            "capture_status": "FAILED",
            "failure_reason": "SOURCE_UNAVAILABLE: 502 Bad Gateway",
        }

    monkeypatch.setattr(live_pull, "_build_history_capture", hong)
    client = app.test_client()
    resp = upload(client, write_sales(tmp_path / "so.xlsx", ROWS[:1], day=SALE_DAY))
    assert resp.status_code == 302

    header, rows = order_lines(web_server.ARTIFACT_DIR)
    assert rows[0][header.index("Giá nhập kế toán / công khai")] == GIA_NGAY_BAN * 1000

    run_id = sorted(p.stem for p in web_server.ARTIFACT_DIR.glob("*.xlsx"))[-1]
    evidence = client.application.config["RUN_REGISTRY"].get_run(run_id).tracking_evidence
    assert evidence["purchase_price_history_status"] == "FAILED"
    assert "502" in evidence["purchase_price_history_failure_reason"]
