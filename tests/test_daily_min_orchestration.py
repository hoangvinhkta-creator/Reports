"""Điều phối R1: sổ bán hàng → kế hoạch hỏi giá → ảnh chụp MIN đúng KỲ.

Bộ này canh khoảng trống giữa "provider đọc đúng" và "hệ thống thật sự hỏi".
`tests/test_daily_min_contract.py` và `tests/test_daily_min_vertical.py` đều
NHẬN một capture đã có sẵn, nên cả hai xanh rực trong khi đường upload thật
không hề gọi hợp đồng `daily-min-v1` và mọi dòng Tracking Pending. Đó chính là
hình dạng lỗi đã lọt qua R1 vòng đầu.

Ba câu hỏi ở đây, và không câu nào trả lời được từ một capture cho sẵn:

1. Từ một workbook, hệ thống có suy ra ĐÚNG tập mã Tracking và khoảng ngày bán
   để hỏi không?
2. Khi trong kho có nhiều ảnh chụp, nó có chọn ảnh chụp phủ ĐÚNG kỳ đang chạy
   không — hay chọn "cái mới nhất" và ném cả kỳ ra ngoài cửa sổ?
3. Đường pull-on-run của bản web có thật sự gọi hợp đồng, đóng băng kết quả
   cho lần chạy ấy, rồi dọn file tạm không?
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from app import owner_usability
from app.modules.pricing.daily_min import load_daily_min_capture
from app.modules.pricing.daily_min.planning import (
    MAX_CONTRACT_DAYS,
    UnreadableSalesWorkbookError,
    plan_daily_min_request_for_workbook,
)
from app.modules.pricing.resolution.sources import load_tracking_catalog_capture
from app.modules.product.identity.store import JsonlProductIdentityStore
from tests.support import daily_min_fixtures as dmin
from tests.test_105e_price_composition import write_catalog_capture
from tests.test_daily_min_vertical import CATALOG, ROWS, write_sales
from tests.test_owner_usability import add_valid_captures
from tests.test_tracking_history_reader import CUTOVER
from tools.tracking import live_pull

AUG = date(2026, 8, 12)
SEP = date(2026, 9, 3)


def write_sales_over_days(path: Path, entries) -> Path:
    """Một workbook có nhiều NGÀY BÁN khác nhau.

    `write_sales` của bộ vertical ghi cả sổ vào một ngày, nên nó không dựng
    được cảnh "sổ trải rộng hơn một lượt gọi hợp đồng" — cảnh duy nhất chạm
    tới trần 62 ngày.
    """
    import openpyxl

    from tests.fixtures.synthetic_workbook import HEADER

    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "SỔ CHI TIẾT BÁN HÀNG"
    sheet.append(["SỔ CHI TIẾT BÁN HÀNG"])
    sheet.append(["Từ ngày 01/01/2026 đến ngày 31/12/2026"])
    sheet.append([])
    sheet.append(HEADER)
    sheet.append(["", "", "Diễn giải chung"])
    for (order_id, product, quantity, sell), day in entries:
        sheet.append([
            day, order_id, f"Bán hàng {order_id}", product, f"KH{order_id}",
            f"Khách {order_id}", "1 Đường Test", "0900000000", quantity, sell,
            sell * quantity, 0, "Vũ Hạnh Ly 0868345633", "Shipper", 0, None, None,
        ])
        sheet.cell(sheet.max_row, 4).data_type = "s"
    book.save(path)
    book.close()
    return path


def catalog_snapshot(tmp_path: Path):
    return load_tracking_catalog_capture(write_catalog_capture(tmp_path, CATALOG))


def empty_store_view(tmp_path: Path):
    store = JsonlProductIdentityStore(log_path=tmp_path / "identity.jsonl")
    return store.read_at_revision(store.current_revision())


def plan_for(tmp_path: Path, sales: Path):
    return plan_daily_min_request_for_workbook(
        sales,
        tracking_catalog=catalog_snapshot(tmp_path),
        identity_store_view=empty_store_view(tmp_path),
        tracking_identity_authority=True,
    )


# ======================================================================
# 1. Kế hoạch hỏi giá — suy từ SỔ, không đoán, không hỏi thừa
# ======================================================================


def test_the_plan_asks_for_exactly_the_tracking_codes_the_ledger_uses(tmp_path):
    """Hỏi thừa thì chậm; hỏi thiếu thì một mã im lặng Pending."""
    plan = plan_for(tmp_path, write_sales(tmp_path / "s.xlsx", ROWS, day=SEP))
    assert plan is not None
    assert plan.product_codes == ("TRK-A", "TRK-B", "TRK-C", "TRK-D", "TRK-E")


def test_the_plan_spans_the_real_sale_dates_not_the_upload_day(tmp_path):
    """Khoảng ngày phải là khoảng NGÀY BÁN. Lấy ngày nạp sổ làm biên là đúng
    lỗi mà cả R1 tồn tại để chặn — chỉ dời một tầng lên trên."""
    rows = ROWS[:1]
    early = write_sales(tmp_path / "a.xlsx", rows, day=date(2026, 9, 3))
    late = write_sales(tmp_path / "b.xlsx", rows, day=date(2026, 9, 20))
    assert plan_for(tmp_path, early).date_from == date(2026, 9, 3)
    assert plan_for(tmp_path, late).date_to == date(2026, 9, 20)


def test_a_ledger_with_no_tracking_identity_has_nothing_to_ask(tmp_path):
    """`None` nghĩa là "không có câu hỏi nào", KHÔNG phải "mọi mã thiếu giá".

    Những dòng ấy đã Pending với lý do identity của chính chúng; hỏi Tracking
    bằng tên hàng trên chứng từ là đúng thứ tầng identity tồn tại để ngăn.
    """
    rows = [("BH9001", "Tên hàng chưa ai nhận diện", 1, 1_000_000)]
    assert plan_for(tmp_path, write_sales(tmp_path / "la.xlsx", rows, day=SEP)) is None


def test_a_ledger_with_no_rows_has_nothing_to_ask(tmp_path):
    assert plan_for(tmp_path, write_sales(tmp_path / "rong.xlsx", [], day=SEP)) is None


def test_a_plan_without_identity_sources_is_not_built_from_raw_names(tmp_path):
    """Thiếu danh mục ⇒ không có kế hoạch. Dựng kế hoạch từ `product_raw` thô
    là gửi tên hàng trên chứng từ sang Tracking như thể chúng là mã."""
    assert plan_daily_min_request_for_workbook(
        write_sales(tmp_path / "s.xlsx", ROWS, day=SEP),
        tracking_catalog=None,
        identity_store_view=empty_store_view(tmp_path),
    ) is None


def test_a_plan_knows_when_the_period_is_wider_than_one_contract_call(tmp_path):
    """Trần 62 ngày là của hợp đồng Tracking (`TRAN_NGAY_XUAT`).

    Biết trước thì nói được bằng một câu người đọc hiểu, thay vì nhận
    `khoang-ngay-qua-dai` trở về từ một hệ thống khác — hoặc tệ hơn, gọi một
    lượt mạng chắc chắn hỏng rồi coi đó là "Tracking đang lỗi".
    """
    assert MAX_CONTRACT_DAYS == 62

    narrow = plan_for(tmp_path, write_sales(tmp_path / "hep.xlsx", ROWS[:1], day=SEP))
    assert narrow.day_span == 1 and narrow.fits_one_contract_call

    wide = plan_for(tmp_path, write_sales_over_days(
        tmp_path / "ca-nam.xlsx",
        [(ROWS[0], date(2026, 1, 5)), (ROWS[1], date(2026, 12, 20))],
    ))
    assert wide.date_from == date(2026, 1, 5)
    assert wide.date_to == date(2026, 12, 20)
    assert wide.day_span > MAX_CONTRACT_DAYS
    assert not wide.fits_one_contract_call


def test_an_unreadable_workbook_is_its_own_error_not_a_silent_empty_plan(tmp_path):
    """Nuốt lỗi ở đây thì một sổ hỏng thành một kỳ Pending im lặng."""
    bad = tmp_path / "hong.xlsx"
    bad.write_bytes(b"day khong phai xlsx")
    with pytest.raises(UnreadableSalesWorkbookError):
        plan_for(tmp_path, bad)


# ======================================================================
# 2. Chọn ảnh chụp theo KỲ, không theo "mới nhất toàn cục"
# ======================================================================


def write_daily_min_capture(
    directory: Path, name: str, *, date_from: str, date_to: str,
    captured_at: datetime, codes=("TRK-A",),
) -> Path:
    """Một capture MIN thật, đi qua đúng loader production khi được chọn."""
    directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "capture_id": f"DMIN-{name}",
        "captured_at": captured_at.isoformat(),
        "captured_by": "kiem",
        "source_system_ref": "tracking/api/min-ngay",
        "capture_status": "COMPLETE",
        "data": dmin.contract(
            date_from=date_from, date_to=date_to,
            records=[dmin.record(code, date_from, min_price=6800) for code in codes],
        ),
    }
    path = directory / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    add_valid_captures(
        tmp_path,
        history_at=CUTOVER,
        catalog_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
    )
    # Danh mục THẬT (có TRK-*) để identity resolve được; bản trong
    # `add_valid_captures` cố ý rỗng.
    write_catalog_capture(tmp_path, CATALOG).replace(
        tmp_path / "data" / "tracking_catalog" / "catalog.json"
    )
    return tmp_path


def test_reopening_an_august_ledger_picks_the_august_capture(repo):
    """Ca trung tâm của bộ này.

    Ảnh chụp tháng 9 MỚI HƠN và hoàn toàn vô dụng cho sổ tháng 8: mọi ngày bán
    nằm ngoài cửa sổ của nó. Chọn theo "mới nhất" thì cả kỳ Pending với lý do
    `SALE_DATE_OUTSIDE_CAPTURE`, và người đọc sẽ đi chụp lại tháng 9 lần nữa.
    """
    kho = repo / "data" / "tracking_daily_min"
    thang_8 = write_daily_min_capture(
        kho, "thang-8", date_from="2026-08-01", date_to="2026-08-31",
        captured_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
    )
    write_daily_min_capture(
        kho, "thang-9", date_from="2026-09-01", date_to="2026-09-30",
        captured_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )

    selected = owner_usability.select_latest_valid_captures(
        repo_root=repo,
        sales=write_sales(repo / "so-thang-8.xlsx", ROWS[:1], day=AUG),
    )
    assert selected.tracking_daily_min == thang_8


def test_a_september_ledger_still_picks_the_september_capture(repo):
    kho = repo / "data" / "tracking_daily_min"
    write_daily_min_capture(
        kho, "thang-8", date_from="2026-08-01", date_to="2026-08-31",
        captured_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
    )
    thang_9 = write_daily_min_capture(
        kho, "thang-9", date_from="2026-09-01", date_to="2026-09-30",
        captured_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )

    selected = owner_usability.select_latest_valid_captures(
        repo_root=repo,
        sales=write_sales(repo / "so-thang-9.xlsx", ROWS[:1], day=SEP),
    )
    assert selected.tracking_daily_min == thang_9


def test_a_capture_that_only_half_covers_the_period_is_not_used(repo):
    """Phủ MỘT PHẦN kỳ vẫn là không trả lời được kỳ ấy. Dùng nó thì nửa đầu
    tháng có giá, nửa sau Pending — và bảng tổng vẫn ra một con số."""
    kho = repo / "data" / "tracking_daily_min"
    write_daily_min_capture(
        kho, "nua-thang", date_from="2026-09-01", date_to="2026-09-10",
        captured_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )
    rows = [ROWS[0]]
    sales = write_sales(repo / "trai-rong.xlsx", rows, day=date(2026, 9, 20))
    selected = owner_usability.select_latest_valid_captures(repo_root=repo, sales=sales)
    assert selected.tracking_daily_min is None


def test_without_a_workbook_no_daily_min_capture_is_chosen(repo):
    """Không có kỳ thì không có tiêu chí; chọn bừa là đúng lỗi đang sửa."""
    write_daily_min_capture(
        repo / "data" / "tracking_daily_min", "thang-9",
        date_from="2026-09-01", date_to="2026-09-30",
        captured_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )
    selected = owner_usability.select_latest_valid_captures(repo_root=repo)
    assert selected.tracking_daily_min is None


def test_the_chosen_capture_really_answers_the_period(repo):
    """Không chỉ so đường dẫn: nạp lại qua loader production và hỏi thật."""
    kho = repo / "data" / "tracking_daily_min"
    write_daily_min_capture(
        kho, "thang-8", date_from="2026-08-01", date_to="2026-08-31",
        captured_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
    )
    write_daily_min_capture(
        kho, "thang-9", date_from="2026-09-01", date_to="2026-09-30",
        captured_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )
    selected = owner_usability.select_latest_valid_captures(
        repo_root=repo,
        sales=write_sales(repo / "so.xlsx", ROWS[:1], day=AUG),
    )
    snapshot = load_daily_min_capture(selected.tracking_daily_min)
    assert snapshot.covers(AUG)
    assert not snapshot.covers(SEP)


# ======================================================================
# 3. Pull-on-run của bản web — có GỌI, có đóng băng, có dọn
# ======================================================================


def fake_tracking(monkeypatch, tmp_path: Path, *, posts: list):
    """Ba capture kia trả về envelope COMPLETE rỗng; chỉ MIN là thật."""
    def envelope(prefix):
        def build(fetch, *, capture_id, captured_by, source_system_ref,
                  captured_at=None, **kw):
            return {
                "capture_id": capture_id,
                "captured_at": (captured_at or datetime.now(timezone.utc)).isoformat(),
                "captured_by": captured_by,
                "source_system_ref": source_system_ref,
                "content_hash": f"hash-{prefix}",
                "capture_status": "COMPLETE",
                **({"rows": CATALOG} if prefix == "cat" else {}),
                **({"entries": {}} if prefix == "inv" else {}),
                **({"nodes": {}} if prefix == "pph" else {}),
            }
        return build

    monkeypatch.setattr(live_pull, "_build_history_capture", envelope("pph"))
    monkeypatch.setattr(live_pull.capture_tracking_catalog, "build_capture", envelope("cat"))
    monkeypatch.setattr(live_pull.capture_inv_map, "build_capture", envelope("inv"))

    def post(body):
        posts.append(body)
        return {
            **dmin.contract(
                date_from=body["date_from"], date_to=body["date_to"],
                records=[dmin.record(code, body["date_from"], min_price=6800)
                         for code in body["product_codes"]],
            ),
            "next_cursor": None,
        }

    return post


def test_the_web_pull_asks_the_contract_once_for_the_whole_period(monkeypatch, tmp_path):
    """Một lượt gọi cho cả kỳ — không phải một lượt cho mỗi dòng bán."""
    posts: list = []
    post = fake_tracking(monkeypatch, tmp_path, posts=posts)
    sales = write_sales(tmp_path / "so.xlsx", ROWS, day=SEP)

    live = live_pull.pull_live_captures(
        out_dir=tmp_path / "tmp", source_url="https://tracking.test",
        api_key="k", fetch=lambda node: {}, sales=sales, post=post,
    )

    assert len(posts) == 1
    assert posts[0]["product_codes"] == ["TRK-A", "TRK-B", "TRK-C", "TRK-D", "TRK-E"]
    assert (posts[0]["date_from"], posts[0]["date_to"]) == ("2026-09-03", "2026-09-03")
    assert live.tracking_daily_min is not None
    assert live.evidence["daily_min_status"] == "COMPLETE"
    assert live.evidence["daily_min_query_revision"] == dmin.QUERY_REVISION


def test_the_pulled_capture_is_frozen_for_this_run_and_then_removed(monkeypatch, tmp_path):
    """`S071 §10`: authority thô của Tracking không ở lại trên đĩa máy chủ lâu
    hơn một lần chạy."""
    post = fake_tracking(monkeypatch, tmp_path, posts=[])
    live = live_pull.pull_live_captures(
        out_dir=tmp_path / "tmp", source_url="https://tracking.test", api_key="k",
        fetch=lambda node: {}, sales=write_sales(tmp_path / "s.xlsx", ROWS, day=SEP),
        post=post,
    )
    path = live.tracking_daily_min
    assert path in live.temp_paths and path.is_file()
    assert load_daily_min_capture(path).covers(SEP)

    live.cleanup()
    assert not path.exists()


def test_a_run_without_a_workbook_does_not_call_the_price_contract(monkeypatch, tmp_path):
    """Đường đọc danh mục cho bảng chọn mặt hàng KHÔNG cần giá — và gọi hợp
    đồng giá ở đó là gọi mạng cho một câu hỏi không ai đặt ra."""
    posts: list = []
    post = fake_tracking(monkeypatch, tmp_path, posts=posts)
    live = live_pull.pull_live_captures(
        out_dir=tmp_path / "tmp", source_url="https://tracking.test", api_key="k",
        fetch=lambda node: {}, post=post,
    )
    assert posts == []
    assert live.tracking_daily_min is None
    assert live.evidence["daily_min_skip_reason"] == "NO_SALES_WORKBOOK"


def test_a_failed_price_contract_stops_the_run_instead_of_pricing_nothing(
    monkeypatch, tmp_path
):
    """Từ R1, MIN theo ngày bán LÀ nguồn giá nhập tự động.

    Một báo cáo mà mọi dòng Tracking đều Pending không phải một báo cáo "gần
    đúng" — nó là một báo cáo không có giá vốn, và nó trông y hệt một báo cáo
    có. Thà dừng và nói ra.
    """
    fake_tracking(monkeypatch, tmp_path, posts=[])

    def post(body):
        return {"ok": False, "ly": "nguon-hong"}

    with pytest.raises(live_pull.TrackingUnavailableError) as exc:
        live_pull.pull_live_captures(
            out_dir=tmp_path / "tmp", source_url="https://tracking.test", api_key="k",
            fetch=lambda node: {}, sales=write_sales(tmp_path / "s.xlsx", ROWS, day=SEP),
            post=post,
        )
    assert exc.value.node == "daily_min"


def test_a_period_wider_than_the_contract_is_skipped_with_its_own_reason(
    monkeypatch, tmp_path
):
    """Kỳ quá rộng là tính chất của SỔ, không phải của Tracking.

    Nên nó KHÔNG được dựng thành "Tracking đang lỗi" (lần chạy dừng, Owner
    được bảo thử lại sau — và thử lại bao nhiêu lần cũng thế). Lần chạy đi
    tiếp, dòng Tracking Pending vì nguồn chưa nối, và lý do thật nằm trong
    bằng chứng của run để người đọc tìm đúng chỗ.
    """
    posts: list = []
    post = fake_tracking(monkeypatch, tmp_path, posts=posts)
    sales = write_sales_over_days(
        tmp_path / "ca-nam.xlsx",
        [(ROWS[0], date(2026, 1, 5)), (ROWS[1], date(2026, 12, 20))],
    )
    live = live_pull.pull_live_captures(
        out_dir=tmp_path / "tmp", source_url="https://tracking.test", api_key="k",
        fetch=lambda node: {}, sales=sales, post=post,
    )
    assert posts == []
    assert live.tracking_daily_min is None
    assert live.evidence["daily_min_skip_reason"] == "PERIOD_WIDER_THAN_CONTRACT"
    assert live.evidence["daily_min_day_span"] > MAX_CONTRACT_DAYS


def test_an_unreadable_workbook_does_not_look_like_a_tracking_outage(
    monkeypatch, tmp_path
):
    """Sổ hỏng thì đường nhập sổ ngay sau đây báo lỗi ở nơi người dùng hiểu
    được. Dựng nó thành lỗi Tracking là chỉ sai chỗ cho người đi sửa."""
    posts: list = []
    post = fake_tracking(monkeypatch, tmp_path, posts=posts)
    bad = tmp_path / "hong.xlsx"
    bad.write_bytes(b"khong phai xlsx")
    live = live_pull.pull_live_captures(
        out_dir=tmp_path / "tmp", source_url="https://tracking.test", api_key="k",
        fetch=lambda node: {}, sales=bad, post=post,
    )
    assert posts == []
    assert live.evidence["daily_min_skip_reason"] == "UNREADABLE_SALES_WORKBOOK"


def test_a_ledger_with_no_tracking_lines_is_not_a_tracking_failure(monkeypatch, tmp_path):
    posts: list = []
    post = fake_tracking(monkeypatch, tmp_path, posts=posts)
    rows = [("BH9001", "Tên hàng chưa ai nhận diện", 1, 1_000_000)]
    live = live_pull.pull_live_captures(
        out_dir=tmp_path / "tmp", source_url="https://tracking.test", api_key="k",
        fetch=lambda node: {}, sales=write_sales(tmp_path / "la.xlsx", rows, day=SEP),
        post=post,
    )
    assert posts == []
    assert live.tracking_daily_min is None
    assert live.evidence["daily_min_skip_reason"] == "NO_TRACKING_IDENTITY_LINES"
