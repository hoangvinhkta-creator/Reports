"""R5.4 — dòng KHỚP TỰ ĐỘNG với Tracking phải nhận model/hãng/nhóm hàng.

## Lỗi production mà file này đóng lại

Sau `R5.3`, Owner báo trên production: *"đã phân loại hãng + ngành hàng bên
Tracking gần như đủ cho các mã bán nhiều, chạy lại báo cáo vẫn không hiện
ngành hàng + hãng, tên mã hàng không được rút gọn"*. Đo lại trên đường thật:

```text
dòng "Máy lạnh Test-2" khớp qua inv.map → mã 55Q6FA
order_line_result_version.canonical_product_code = '55Q6FA'   (pipeline ĐÚNG)
bản chiếu hiển thị CÓ đủ model/hãng/nhóm hàng của 55Q6FA       (capture ĐÚNG)
tab Nhân viên: Mặt hàng "Máy lạnh Test-2" · Hãng "—" · Nhóm hàng "—"
```

Ba cổng hiển thị nhãn (`server._catalog_labels`, `product_taxonomy.
metadata_of`, `brand_identity.bucket_for`) chỉ tra mã qua
`identity_gateway.confirmed_identities()` — mapping do NGƯỜI xác nhận trong
Reports. Nhưng đường sản xuất chính khớp dòng TỰ ĐỘNG (`alias.map`/`board`
theo mã, `inv.map` theo câu tên hàng) và cố ý KHÔNG ghi mapping nào (`INV-70`),
nên những dòng ấy — tức phần lớn dòng đã khớp — không bao giờ nhận nhãn.

`R5.4` thêm ĐÚNG một nguồn mã thứ hai, thấp hơn quyết định của người: mã mà
LẦN CHẠY đã phân giải và lưu trên chính dòng (`line_identity.tracking_
identity_of`). Không lời gọi Tracking nào thêm, không suy một chữ từ tên trên
sổ, và cổng `classification == MATCHED_TRACKING` không nới.

## Vì sao các bài luồng chính đi qua `POST /run` thật

Cùng lý do `R5.3` đã ghi: từng tầng đều ĐÚNG khi đo riêng, lỗi chỉ nhìn thấy
được trên đường người dùng thật. Bộ khung (`app`, `client`, `identity_store`,
`projection_path`, `workbook`, `engine`) mượn nguyên của
`tests/test_r53_durable_tracking_labels.py` — cùng một app thật, cùng một
`/run` thật, cùng một đĩa thật.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import text as sql_text

from app.modules.product.identity.identity import (
    CanonicalProductIdentity, Namespace)
from app.modules.product.identity.tracking_inv_map import inv_map_key
from app.modules.reporting import brand_metrics as bmx
from app.web import (brand_identity, catalog_display, identity_gateway,
                     line_identity, product_taxonomy)
from tools.tracking import live_pull

# Bộ khung + trợ giúp của R5.3 — import ĐÍCH DANH, không `*`: import `*` sẽ
# kéo cả các hàm `test_*` của file kia vào đây và pytest thu thập chúng hai lần.
from tests.test_r53_durable_tracking_labels import (  # noqa: F401 — fixtures
    BRAND_FULL, CATEGORY_FULL, CATEGORY_NO_BRAND, CODE_FULL, CODE_NO_BRAND,
    MODEL_FULL, MODEL_NO_BRAND, RAW_FULL, RAW_NO_BRAND,
    app, catalog_rows, cells, client, confirm, employee_page, engine,
    field_of, identity_store, projection_path, restart_the_container,
    row_of, totals, upload, workbook, write_catalog_capture,
)


# --- Dựng inv.map: câu tên hàng kế toán → mã, ĐÚNG như Tracking xuất ---------

def write_inv_map_capture(path: Path, entries: dict) -> Path:
    path.write_text(json.dumps({
        "capture_id": "TRK-INV-R54",
        "captured_at": datetime(2026, 9, 1, tzinfo=timezone.utc).isoformat(),
        "captured_by": "reports-live-pull",
        "source_system_ref": "tracking/api/xuat/inv_map",
        "content_hash": "hash-inv-r54",
        "capture_status": "COMPLETE",
        "entries": entries,
    }, ensure_ascii=False), encoding="utf-8")
    return path


def set_live_auto_match(monkeypatch, tmp_path: Path, *, entries: dict,
                        rows=None) -> None:
    """`live_pull` trả về danh mục + `inv.map` cho lần chạy sau. KHÔNG có
    daily-min (giá MIN không phải chủ đề của file này) và KHÔNG có mapping
    nào được xác nhận trong Reports — đúng luồng khớp tự động."""
    catalog = write_catalog_capture(
        tmp_path / "tracking_catalog.json",
        catalog_rows() if rows is None else rows)
    inv = write_inv_map_capture(tmp_path / "tracking_inv_map.json", entries)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: True)

    def fake_pull(*, out_dir, sales=None, identity_store_view=None, **kwargs):
        return live_pull.LiveSelectedCaptures(
            tracking_capture=None, tracking_catalog=catalog,
            tracking_inv_map=inv, tracking_daily_min=None,
            evidence={"tracking_catalog_capture_id": "TRK-CAT-R53"},
            temp_paths=())
    monkeypatch.setattr(live_pull, "pull_live_captures", fake_pull)


@pytest.fixture
def auto_matched(tmp_path, monkeypatch):
    """`RAW_FULL` khớp tự động về `CODE_FULL` qua `inv.map`."""
    set_live_auto_match(monkeypatch, tmp_path,
                        entries={inv_map_key(RAW_FULL): CODE_FULL})


def stored_codes(engine) -> dict:
    with engine.begin() as connection:
        rows = connection.execute(sql_text(
            "SELECT s.product_raw, r.identity_namespace, "
            "r.canonical_product_code, r.pending_reasons_json "
            "FROM order_line_result_version r "
            "JOIN order_line_source_version s ON s.id = r.source_version_id"
        )).fetchall()
    return {row[0]: (row[1], row[2], row[3]) for row in rows}


# --- 1. Luồng chính: khớp tự động ⟹ ba ô, KHÔNG confirm gì trong Reports ---

def test_an_auto_matched_line_shows_model_brand_and_category(
    client, workbook, auto_matched, projection_path, identity_store, engine,
):
    """Mệnh đề của `R5.4`. Tiền đề được đo TRƯỚC (không giả định): lần chạy
    đã phân giải dòng về mã Tracking và KHÔNG có mapping nào trong store."""
    upload(client, workbook)
    namespace, code, reasons = stored_codes(engine)[RAW_FULL]
    assert (namespace, code) == ("TRACKING", CODE_FULL)
    assert "IDENTITY_UNRESOLVED" not in reasons
    assert identity_gateway.confirmed_identities(identity_store) == {}

    html = employee_page(client)
    assert field_of(html, MODEL_FULL, "line-product") == MODEL_FULL
    assert field_of(html, MODEL_FULL, "line-brand") == BRAND_FULL
    assert field_of(html, MODEL_FULL, "line-category") == CATEGORY_FULL
    # Tên trên sổ vẫn đọc được qua tooltip (`R5.3` §UI).
    assert RAW_FULL not in cells(html, "line-product")
    assert f'title="{RAW_FULL}"' in row_of(html, MODEL_FULL)


def test_an_auto_matched_line_keeps_its_labels_after_a_restart(
    client, workbook, auto_matched, projection_path, identity_store,
):
    """Đường dựng lại của `R5.3` (bản BỀN theo run) cũng phải phục vụ dòng
    khớp tự động — nếu không, lỗi `R5.3` tái diễn cho đúng tập dòng này."""
    upload(client, workbook)
    restart_the_container(projection_path)
    html = employee_page(client)
    assert field_of(html, MODEL_FULL, "line-product") == MODEL_FULL
    assert field_of(html, MODEL_FULL, "line-brand") == BRAND_FULL
    assert field_of(html, MODEL_FULL, "line-category") == CATEGORY_FULL


# --- 2. Cổng `MATCHED_TRACKING` KHÔNG nới ----------------------------------

def test_a_line_the_owner_marks_out_of_catalog_loses_the_stored_code(
    client, workbook, auto_matched, projection_path, identity_store,
):
    """Quyết định của người SAU lần chạy thắng cột đã lưu: dòng đã được đánh
    dấu ngoài bảng giá không nhận nhãn nào, dù cột còn mang một mã."""
    upload(client, workbook)
    identity_gateway.mark_out_of_catalog(
        identity_store, product_raw=RAW_FULL, actor_id="test-owner",
        affected_orders=("BH0002",), affected_lines=1)
    html = employee_page(client)
    assert field_of(html, RAW_FULL, "line-product") == RAW_FULL
    assert field_of(html, RAW_FULL, "line-brand") == "—"
    assert field_of(html, RAW_FULL, "line-category") == "—"


def test_a_human_confirmation_beats_the_code_the_run_stored(
    client, workbook, auto_matched, projection_path, identity_store,
):
    """Owner chọn một mã KHÁC mã lần chạy đã phân giải ⟹ màn hình theo Owner
    NGAY, không chờ chạy lại sổ (cùng nguyên tắc `line_identity` §"Xác nhận
    của Owner có hiệu lực NGAY")."""
    upload(client, workbook)
    confirm(identity_store, product_raw=RAW_FULL, code=CODE_NO_BRAND)
    html = employee_page(client)
    assert field_of(html, MODEL_NO_BRAND, "line-product") == MODEL_NO_BRAND
    assert field_of(html, MODEL_NO_BRAND, "line-category") == CATEGORY_NO_BRAND
    assert field_of(html, MODEL_NO_BRAND, "line-brand") == "—"


def test_an_unmatched_line_still_shows_the_raw_name_and_dashes(
    client, workbook, auto_matched, projection_path, identity_store, engine,
):
    """`inv.map` chỉ nói về `RAW_FULL`; `RAW_NO_BRAND` vẫn chưa khớp và phải
    giữ tên thô — đây là chỗ một phép suy từ tên sổ sẽ lộ ra nếu có."""
    upload(client, workbook)
    assert stored_codes(engine)[RAW_NO_BRAND][1] is None
    html = employee_page(client)
    assert field_of(html, RAW_NO_BRAND, "line-product") == RAW_NO_BRAND
    assert field_of(html, RAW_NO_BRAND, "line-brand") == "—"
    assert field_of(html, RAW_NO_BRAND, "line-category") == "—"


# --- 3. Chỉ nhãn — không đồng nào đổi ---------------------------------------

def test_labels_for_auto_matched_lines_change_no_money(
    client, workbook, auto_matched, projection_path, identity_store,
):
    upload(client, workbook)
    with_labels = totals(client)
    restart_the_container(projection_path)
    catalog_display.DEFAULT_DISPLAY_PATH.parent.mkdir(parents=True,
                                                      exist_ok=True)
    # Cache đĩa RỖNG hợp lệ (không phải hỏng): tầng đọc coi là "không nhãn",
    # và bản bền vẫn dựng lại được — hai màn hình phải cùng con số.
    assert totals(client) == with_labels


# --- 4. Cảnh báo bản chiếu cũng đo dòng khớp tự động ----------------------

def test_the_projection_warning_covers_auto_matched_lines(
    client, workbook, projection_path, identity_store, tmp_path, monkeypatch,
):
    """Capture đời cũ (không trường hiển thị) + dòng khớp tự động ⟹ cảnh báo
    hình dạng 1 phải nổi lên. Trước `R5.4` nó im lặng vì `confirmed_
    identities()` rỗng — tức chính lỗi production không có một chữ giải
    thích trên màn hình."""
    set_live_auto_match(monkeypatch, tmp_path,
                        entries={inv_map_key(RAW_FULL): CODE_FULL},
                        rows=catalog_rows(with_metadata=False))
    upload(client, workbook)
    html = employee_page(client)
    assert field_of(html, CODE_FULL, "line-product") == CODE_FULL
    assert catalog_display.MISSING_PROJECTION_NOTE[:60] in html


# --- 5. Hai cổng còn lại (R6 taxonomy, PHB-06 thương hiệu) — đơn vị --------

def _detail(product_raw: str, *, namespace, code, reasons=()) -> dict:
    return {
        "product_raw": product_raw,
        "identity_namespace": namespace,
        "canonical_product_code": code,
        "line": SimpleNamespace(pending_reasons=tuple(reasons),
                                purchase_price=Decimal("1")),
    }


DISPLAY = {CODE_FULL: {"model_label": MODEL_FULL, "brand": BRAND_FULL,
                       "category_label": CATEGORY_FULL}}


def test_tracking_identity_of_prefers_the_human_decision():
    human = CanonicalProductIdentity(namespace=Namespace.TRACKING,
                                     source_product_code=CODE_NO_BRAND)
    detail = _detail(RAW_FULL, namespace="TRACKING", code=CODE_FULL)
    key = line_identity.identity_key_of(RAW_FULL)
    assert line_identity.tracking_identity_of(
        detail, identities={key: human}) == human
    assert line_identity.tracking_identity_of(
        detail, identities={}) == CanonicalProductIdentity(
            namespace=Namespace.TRACKING, source_product_code=CODE_FULL)


@pytest.mark.parametrize("namespace, code", [
    ("PUBLIC_PURCHASE", CODE_FULL),   # namespace khác: không phải mã Tracking
    ("TRACKING", None),               # lần chạy không phân giải được
    ("TRACKING", "   "),              # hỏng: không ép thành mã
    (None, None),
])
def test_tracking_identity_of_never_invents_a_code(namespace, code):
    detail = _detail(RAW_FULL, namespace=namespace, code=code)
    assert line_identity.tracking_identity_of(detail, identities={}) is None


def test_r6_metadata_reads_the_stored_code():
    detail = _detail(RAW_FULL, namespace="TRACKING", code=CODE_FULL)
    meta = product_taxonomy.metadata_of(
        detail, decisions=line_identity.Decisions(), identities={},
        display=DISPLAY)
    assert meta.state == product_taxonomy.STATE_MATCHED
    assert (meta.tracking_code, meta.model_label, meta.brand,
            meta.category_label) == (CODE_FULL, MODEL_FULL, BRAND_FULL,
                                     CATEGORY_FULL)


def test_r6_metadata_still_gates_on_identity_state():
    unresolved = _detail(RAW_FULL, namespace="TRACKING", code=CODE_FULL,
                         reasons=("IDENTITY_UNRESOLVED",))
    meta = product_taxonomy.metadata_of(
        unresolved, decisions=line_identity.Decisions(), identities={},
        display=DISPLAY)
    assert meta.state == product_taxonomy.STATE_UNRESOLVED
    assert meta.tracking_code is None


def test_brand_bucket_reads_the_stored_code():
    detail = _detail(RAW_FULL, namespace="TRACKING", code=CODE_FULL)
    bucket = brand_identity.bucket_for(
        detail, confirmed_keys=frozenset(), identities={},
        brand_source=catalog_display.brand_source(DISPLAY))
    assert bucket == bmx.brand_bucket(BRAND_FULL)
    absent = brand_identity.bucket_for(
        _detail(RAW_FULL, namespace="TRACKING", code="KHONG-CO"),
        confirmed_keys=frozenset(), identities={},
        brand_source=catalog_display.brand_source(DISPLAY))
    assert absent == bmx.BRAND_ABSENT_BUCKET
