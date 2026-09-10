"""PHB-06 — báo cáo theo THƯƠNG HIỆU: thẩm quyền, phân hoạch, đối soát.

Ba lớp khẳng định, và thứ tự của chúng là cố ý:

1. **Thẩm quyền** (`BR-01`, `BR-02`, `BR-10`) — chứng minh bằng CHÍNH MÃ NGUỒN
   rằng không có đường nào suy thương hiệu từ tên hàng và không có thẩm quyền
   thương hiệu thứ hai nào được dựng. Một test chỉ chạy hàm sẽ không bắt được
   một nhánh suy luận thêm vào ngày mai; một test đọc mã nguồn thì bắt được.
2. **Phân hoạch + đối soát** (`BR-04`…`BR-09`) — chứng minh tổng của bảng
   thương hiệu cộng lại ĐÚNG BẰNG tổng kỳ, kể cả phần chưa xác định, và bất
   biến trước gán lại nhân viên / chuyển nhóm Gia dụng / loại dòng.
3. **Trang thật** (`BR-03`, `BR-11`, `BR-12`) — chứng minh route sống, mặc
   định đúng tháng dương lịch hiện tại, không thêm mục điều hướng chính và
   không có Target thương hiệu.

Cuối file là tám MUTATION PROBE: mỗi probe cố ý làm hỏng đúng một tính chất
rồi khẳng định phép kiểm tương ứng THẤT BẠI. Không có chúng, một bộ test toàn
PASS không phân biệt được "bất biến đúng" với "bất biến chưa bao giờ được đo".
"""

from __future__ import annotations

import inspect
import re
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.modules.product.identity.identity import (
    CanonicalProductIdentity, Namespace,
)
from app.modules.reporting import brand_metrics as bmx
from app.modules.reporting import business_metrics as bm
from app.web import brand_identity, business_service, business_store
from app.web import history_store, line_identity
from app.web import server as web_server
from tests.test_business_vertical import JANUARY, pair, persist
from tools.tracking import live_pull

REPO_ROOT = Path(__file__).resolve().parents[1]


# --- Nguồn thương hiệu GIẢ, chỉ dùng trong test --------------------------
#
# Dữ liệu thật hôm nay cho ra ĐÚNG MỘT bucket (xem
# `test_the_canonical_identity_contract_still_carries_no_brand`), và một phép
# đối soát chỉ từng chạy trên một bucket chưa chứng minh được gì về việc cộng
# đúng. Nguồn giả này dựng một kỳ NHIỀU thương hiệu để các bất biến cộng
# được đo thật. Nó KHÔNG có mặt trên đường production — test
# `test_the_route_wires_only_the_canonical_brand_source` canh điều đó.

BRANDS_BY_CODE = {
    "T2109NT1G": "LG",
    "FTKB50ZVMV": "Daikin",
    "NR-BX471": "Panasonic",
}


def stub_brand_source(identity):
    if identity is None:
        return None
    return BRANDS_BY_CODE.get(identity.source_product_code)


def identities_for(*items: tuple[str, str]) -> dict:
    """`{raw_identity_key(tên hàng): CanonicalProductIdentity}`.

    Khoá đi qua đúng `line_identity.identity_key_of` mà đường production dùng,
    nên test không dựng một phép chuẩn hoá thứ hai (`INV-05`).
    """
    return {
        line_identity.identity_key_of(product_raw):
            CanonicalProductIdentity(Namespace.TRACKING, code)
        for product_raw, code in items
    }


def executable_source(module) -> str:
    """Mã CHẠY của một module — mọi chuỗi và mọi comment đã bị bỏ.

    Quét thô cả file sẽ bắt nhầm chính phần văn xuôi đang GIẢI THÍCH điều bị
    cấm: `brand_metrics` phải nói được vì sao nó không đọc `product_raw`. Cấm
    cả cách gọi tên sẽ làm tài liệu không viết được, nên phép quét đi qua
    `tokenize` và chỉ nhìn token thật.
    """
    import io
    import tokenize

    kept = []
    source = inspect.getsource(module)
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        kept.append(token.string)
    return " ".join(kept)


# ==========================================================================
# 1. THẨM QUYỀN THƯƠNG HIỆU
# ==========================================================================

def test_the_canonical_identity_contract_still_carries_no_brand():
    """RE-TRIGGER GATE của PHB-06 — đọc kỹ trước khi "sửa" test này.

    Bằng chứng audit của PHB-06: `CanonicalProductIdentity` là hợp đồng danh
    tính canonical và nó KHÔNG có trường thương hiệu. Đó là lý do bảng thương
    hiệu hôm nay chưa có dòng chính danh nào, và là lý do PHB-06 kết thúc bằng
    một `OWNER_DECISION_REQUIRED` thay vì một bảng dựng từ tên hàng.

    Test này THẤT BẠI đúng vào ngày hợp đồng đó có thêm trường thương hiệu —
    và đó là hành vi mong muốn: nó là chuông báo rằng PHB-06 nên được mở lại
    có chủ đích, chứ không phải một test hỏng cần tắt đi. Khi chuông kêu:
    xoá test này, và `brand_identity.canonical_brand` sẽ tự đọc được trường
    mới mà không phải sửa dòng nào.
    """
    fields = set(CanonicalProductIdentity.__dataclass_fields__)
    assert fields == {"namespace", "source_product_code"}
    assert brand_identity.CANONICAL_BRAND_FIELD not in fields


def test_brand_modules_never_look_at_the_product_description():
    """`BR-02` — không suy thương hiệu từ mô tả sản phẩm, và không bằng bất kỳ
    phép so gần đúng nào.

    Đọc MÃ NGUỒN chứ không chỉ chạy hàm: một nhánh `if "LG" in product_raw`
    thêm vào ngày mai vẫn làm mọi test hành vi hôm nay PASS, vì hôm nay chưa
    có dòng nào có thương hiệu để so.
    """
    forbidden = ("product_raw", "startswith", "endswith", "difflib",
                 "SequenceMatcher", "similarity", "fuzz", "levenshtein",
                 "search", "match", "fold")
    for module in (brand_identity, bmx):
        for token in forbidden:
            assert token not in executable_source(module), (
                f"{module.__name__} nhắc tới {token!r} trong MÃ CHẠY — thẩm "
                "quyền thương hiệu phải chỉ đọc hợp đồng Product Identity")


def test_bucket_for_cannot_even_see_the_product_description():
    """Ranh giới bằng CHỮ KÝ HÀM: `bucket_for` không nhận tên hàng.

    `detail` vốn có `product_raw`, nhưng đường duy nhất từ `detail` tới thương
    hiệu đi qua `line_identity.state_of` → `identity_key` → `identities` — tức
    qua thẩm quyền danh tính, không qua câu chữ.
    """
    params = set(inspect.signature(brand_identity.bucket_for).parameters)
    assert params == {"detail", "confirmed_keys", "identities", "brand_source"}


def test_no_brand_table_or_column_exists_anywhere_in_the_schema():
    """`BR-10` + `BR-13` — không thẩm quyền thương hiệu thứ hai, không schema
    mới. Đọc chính metadata đang chạy, không đọc một danh sách viết tay."""
    from tools.db import schema

    for table in schema.METADATA.tables.values():
        assert "brand" not in table.name.lower(), table.name
        for column in table.columns:
            assert "brand" not in column.name.lower(), f"{table.name}.{column.name}"


def test_phb06_adds_no_migration():
    """`BR-13` — `NEW_MIGRATION = NONE`: PHB-06 không thêm bản migration nào."""
    versions = sorted(
        p.name for p in (REPO_ROOT / "tools/db/migrations/versions").glob("*.py"))
    assert versions == [
        "0001_legacy.py", "0002_snapshots.py", "0003_business.py",
        "0004_employee_attribution.py", "0005_legacy_source_authority.py",
        "0006_employee_target.py", "0007_employee_workspace.py",
        # `0008_purchase_price_reason` là của R2 (`R2 Execution Brief` §4.4),
        # KHÔNG phải của vertical này. Nó có mặt trong danh sách vì phép
        # khẳng định ở đây là một phép PIN thư mục; điều nó chứng minh vẫn
        # nguyên vẹn — không có bản migration nào mang tên hay nội dung của
        # vertical này.
        "0008_purchase_price_reason.py",
        # `0009_line_binding_period_close` là của R3 (§1 gắn dòng, §5 chốt
        # kỳ) — cùng lý do như dòng trên: phép khẳng định ở đây PIN thư mục,
        # và điều nó chứng minh vẫn nguyên vẹn.
        "0009_line_binding_period_close.py",
        # `0010_mutation_request` là của `STAB-03` (chống lặp mutation sau
        # khi nhánh tự gửi lại bị gỡ) — cùng lý do như hai dòng trên: phép
        # khẳng định ở đây PIN thư mục, và điều nó chứng minh vẫn nguyên
        # vẹn. Bảng `mutation_request` không lưu một kết quả phân tích nào
        # và không thêm một thẩm quyền ghi nghiệp vụ nào.
        "0010_mutation_request.py",
        # `0011_mutation_request_state` là bản sửa hình dạng của `0010` sau
        # review độc lập (sổ chống lặp phải biết cả lần ghi đang bay) —
        # cùng lý do: phép khẳng định ở đây PIN thư mục.
        "0011_mutation_request_state.py",
    ]


def test_the_route_wires_only_the_canonical_brand_source():
    """`BR-01`/`BR-10` — đường production đọc ĐÚNG MỘT nguồn canonical.

    Tham số `brand_source` tồn tại để test dựng được một kỳ nhiều thương
    hiệu. Test này là cái giá của tham số đó: nó khẳng định bằng mã nguồn
    rằng `server.py` không truyền một nguồn nào khác.

    R5 §5 (`DEC-R5-04`) đổi nguồn từ `brand_identity.canonical_brand` sang
    `catalog_display.brand_source` — một sửa đổi CÓ CHỦ ĐÍCH, và là đúng
    đường thứ hai mà `PHB-06 §4` đã để ngỏ ("một read model canonical tương
    đương"). Điều bộ test này canh KHÔNG đổi: đường production wire ĐÚNG MỘT
    nguồn, và nguồn ấy chỉ tra `source_product_code` của một danh tính đã
    CONFIRM trong bản chiếu mà TRACKING đã chuẩn hoá — không phải một bảng
    ánh xạ của Reports, không phải một phép so chuỗi nào (`BR-02`, `BR-10`).

    Vì sao không dùng `canonical_brand` nữa: nó đọc trường `brand` TRÊN chính
    `CanonicalProductIdentity`, và thêm một trường hiển thị vào value object
    đó sẽ phá `INV-18` (so sánh LUÔN bằng đủ tuple) — hai danh tính cùng mã
    khác hãng sẽ thành hai danh tính KHÁC NHAU. Hàm ấy vẫn ở lại, vẫn là
    đường đọc đúng nếu hợp đồng danh tính có ngày mang trường đó, và vẫn
    được canh ở các test khác của chính file này.
    """
    source = inspect.getsource(web_server)
    calls = re.findall(r"brand_source=([A-Za-z_.]+)", source)
    assert calls == ["catalog_display.brand_source"]


def test_the_canonical_brand_reader_returns_nothing_today():
    """Trạng thái ĐO ĐƯỢC, không phải giả định: mọi danh tính hôm nay đều
    không có thương hiệu."""
    identity = CanonicalProductIdentity(Namespace.TRACKING, "T2109NT1G")
    assert brand_identity.canonical_brand(identity) is None
    assert brand_identity.canonical_brand(None) is None


# ==========================================================================
# 2. PHÂN HOẠCH THUẦN
# ==========================================================================

def line(*, sales="1000", quantity="1", sell="2000000", profit="300000",
         rate="0.020", order="BH1", employee="Vinh"):
    """Một `BusinessLine` tối thiểu.

    `profit=None` dựng đúng tình trạng THIẾU GIÁ NHẬP: cả `auto_purchase_price`
    lẫn `auto_kpi_profit` đều `None`, nên `profit_blockers` có tên và
    `kpi_profit` là `None`. Để giá nhập lại mà chỉ bỏ lợi nhuận sẽ khiến engine
    tính lại theo công thức đã freeze — tức fixture nói dối về chính trạng thái
    nó định dựng.
    """
    return bm.BusinessLine(
        order_key=order, employee=employee, employee_group="NOI_THANH",
        status="AUTO", sell_price=Decimal(sell), quantity=Decimal(quantity),
        discount=Decimal(0), total_sales=Decimal(sales),
        auto_purchase_price=None if profit is None else Decimal("100000"),
        auto_kpi_profit=None if profit is None else Decimal(profit),
        kpi_authority_valid=True, conversion_rate=Decimal(rate))


def test_group_by_brand_is_a_partition_that_sums_back_to_the_period():
    """`BR-04` — cột cộng được của bảng cộng lại ĐÚNG BẰNG tổng kỳ."""
    lines = [line(sales="1000", order="BH1"), line(sales="2000", order="BH2"),
             line(sales="4000", order="BH3")]
    buckets = [bmx.brand_bucket("LG"), bmx.brand_bucket("Daikin"),
               bmx.brand_bucket("LG")]
    company = bm.totals(lines)
    grouped = bmx.group_by_brand(lines, buckets)

    assert [bucket.label for bucket, _ in grouped] == ["LG", "Daikin"]
    assert grouped[0][1].sales_revenue == Decimal("5000")
    assert grouped[1][1].sales_revenue == Decimal("2000")
    assert bmx.reconciliation(grouped, company).is_exact


def test_the_two_unknown_buckets_stay_separate_and_stay_last():
    """`BR-09` + §10 — "chưa nhận diện" và "không có thương hiệu" là HAI dòng,
    và cả hai luôn nằm cuối bảng dù doanh thu lớn tới đâu."""
    lines = [line(sales="1"), line(sales="9999"), line(sales="8888")]
    buckets = [bmx.brand_bucket("LG"), bmx.IDENTITY_UNRESOLVED_BUCKET,
               bmx.BRAND_ABSENT_BUCKET]
    grouped = bmx.group_by_brand(lines, buckets)

    assert [bucket.kind for bucket, _ in grouped] == [
        bmx.KIND_BRAND, bmx.KIND_IDENTITY_UNRESOLVED, bmx.KIND_BRAND_ABSENT]
    assert bmx.reconciliation(grouped, bm.totals(lines)).is_exact


def test_unknown_lines_keep_their_money_in_the_table():
    """`BR-04` — dòng chưa xác định thương hiệu KHÔNG biến mất; tiền của chúng
    vẫn nằm trong bảng và vẫn cộng vào tổng."""
    lines = [line(sales="1000"), line(sales="3000")]
    grouped = bmx.group_by_brand(
        lines, [bmx.brand_bucket("LG"), bmx.IDENTITY_UNRESOLVED_BUCKET])
    assert grouped[1][1].sales_revenue == Decimal("3000")
    assert bmx.reconciliation(grouped, bm.totals(lines)).is_exact


def test_an_empty_brand_name_is_refused_instead_of_becoming_a_blank_row():
    for name in ("", "   ", None):
        with pytest.raises(ValueError):
            bmx.brand_bucket(name)


def test_a_length_mismatch_is_a_hard_error_not_a_silent_truncation():
    """Cắt ngắn im lặng làm một số dòng biến mất khỏi mọi bucket trong khi
    tổng vẫn trông hợp lệ — đúng lớp lỗi đối soát tồn tại để bắt."""
    with pytest.raises(ValueError, match="cùng độ dài"):
        bmx.group_by_brand([line(), line()], [bmx.brand_bucket("LG")])


def test_the_same_brand_across_several_products_is_one_row():
    """`BR` §14 D — một thương hiệu, một dòng, không nhân đôi."""
    lines = [line(sales="1000"), line(sales="2000"), line(sales="3000")]
    grouped = bmx.group_by_brand(lines, [bmx.brand_bucket("LG")] * 3)
    assert len(grouped) == 1
    assert grouped[0][1].sales_revenue == Decimal("6000")
    assert grouped[0][1].lines == 3


def test_orders_is_the_only_column_that_does_not_sum_and_it_is_documented():
    """Một đơn có hàng hai thương hiệu được đếm ở cả hai dòng — sự thật `R-E5`
    đổi chiều gộp, và trang phải NÓI RA nó."""
    lines = [line(order="BH1"), line(order="BH1")]
    grouped = bmx.group_by_brand(
        lines, [bmx.brand_bucket("LG"), bmx.brand_bucket("Daikin")])
    assert sum(t.orders for _, t in grouped) == 2
    assert bm.totals(lines).orders == 1
    assert bmx.reconciliation(grouped, bm.totals(lines)).is_exact

    from app.web import business_presentation as bp
    assert "cột Đơn cộng lại có thể lớn hơn" in bp.BRAND_ORDER_COLUMN_NOTE


def test_null_profit_never_becomes_zero_in_a_brand_bucket():
    """`BR-08`/`R-S2` — thiếu giá nhập ⟹ lợi nhuận `None`, KHÔNG phải 0."""
    lines = [line(profit=None), line(profit=None)]
    grouped = bmx.group_by_brand(
        lines, [bmx.brand_bucket("LG"), bmx.BRAND_ABSENT_BUCKET])
    assert grouped[0][1].kpi_profit is None
    assert grouped[0][1].converted_sales is None
    assert bmx.reconciliation(grouped, bm.totals(lines)).is_exact


# ==========================================================================
# 3. VERTICAL QUA DATABASE
# ==========================================================================

@pytest.fixture
def engine():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


@pytest.fixture
def repository(engine):
    return history_store.SnapshotRepository(engine)


@pytest.fixture
def store(engine):
    return business_store.BusinessDecisionStore(engine)


@pytest.fixture
def service(engine, store):
    return business_service.BusinessReportService(engine=engine, store=store)


IDENTITIES = identities_for(
    ("Máy Giặt LG T2109NT1G", "T2109NT1G"),
    ("Điều hoà Daikin FTKB50ZVMV", "FTKB50ZVMV"),
    ("Tủ lạnh Panasonic NR-BX471", "NR-BX471"),
)


def brand_view(data, *, brand_source=stub_brand_source):
    """Đúng ba bước mà route production chạy, không hơn."""
    buckets = brand_identity.buckets_for(
        data.details, confirmed_keys=frozenset(), identities=IDENTITIES,
        brand_source=brand_source)
    grouped = bmx.group_by_brand(data.lines, buckets)
    return buckets, grouped, bmx.reconciliation(grouped, data.totals)


def sales_by_brand(grouped) -> dict:
    return {bucket.label: totals.sales_revenue for bucket, totals in grouped}


def three_brand_period(repository):
    persist(repository, [
        pair("BH1", product="Máy Giặt LG T2109NT1G",
             kpi_purchase="5000000", kpi_profit="3000000"),
        pair("BH2", product="Điều hoà Daikin FTKB50ZVMV", sell="12000000",
             kpi_purchase="9000000", kpi_profit="3000000"),
        pair("BH3", product="Tủ lạnh Panasonic NR-BX471", sell="20000000",
             kpi_purchase="15000000", kpi_profit="5000000"),
    ])


def test_brand_totals_reconcile_to_the_official_company_totals(
    repository, service
):
    """`BR-04` — qua database thật, trên kết quả nghiệp vụ CHÍNH THỨC."""
    three_brand_period(repository)
    data = service.period(**JANUARY)
    _buckets, grouped, recon = brand_view(data)

    assert recon.is_exact
    assert recon.sales_revenue and recon.qualifying_quantity
    assert recon.kpi_profit and recon.converted_sales and recon.lines
    assert sales_by_brand(grouped) == {
        "Panasonic": Decimal("20000000"),
        "Daikin": Decimal("12000000"),
        "LG": Decimal("8000000"),
    }
    assert data.totals.state == bm.STATE_OFFICIAL


def test_an_excluded_line_is_absent_from_every_brand_total(repository, service):
    """`BR-05` — dòng Owner đã loại không có mặt trong bất kỳ bucket nào."""
    three_brand_period(repository)
    before = service.period(**JANUARY)
    detail = next(d for d in before.details if "Daikin" in d["product_raw"])
    service.store.exclude_line(
        order_key=detail["order_key"], product_key=detail["product_key"],
        occurrence_index=detail["occurrence_index"], reason="hàng trả lại")

    after = service.period(**JANUARY)
    _buckets, grouped, recon = brand_view(after)

    assert "Daikin" not in sales_by_brand(grouped)
    assert recon.is_exact
    assert after.totals.sales_revenue == (
        before.totals.sales_revenue - Decimal("12000000"))


def test_reassigning_an_employee_does_not_move_one_dong_between_brands(
    repository, service
):
    """`BR-06` — thương hiệu TRỰC GIAO với người bán."""
    three_brand_period(repository)
    before = brand_view(service.period(**JANUARY))[1]
    detail = next(d for d in service.period(**JANUARY).details
                  if "Daikin" in d["product_raw"])
    service.store.set_employee(
        order_key=detail["order_key"], product_key=detail["product_key"],
        occurrence_index=detail["occurrence_index"], employee="Ly",
        employee_group="GIA_DUNG")

    data = service.period(**JANUARY)
    _buckets, after, recon = brand_view(data)

    assert sales_by_brand(after) == sales_by_brand(before)
    assert recon.is_exact
    # Bằng chứng phép gán THẬT SỰ đã xảy ra — nếu không, test trên chỉ khẳng
    # định rằng không làm gì thì không có gì đổi.
    assert any(l.employee == "Ly" for l in data.lines)


def test_moving_a_line_to_gia_dung_does_not_move_one_dong_between_brands(
    repository, service
):
    """`BR-07` — thương hiệu TRỰC GIAO với nhóm báo cáo Gia dụng.

    Phép chuyển nhóm được phép đổi DS quy đổi qua định tuyến tỉ lệ đã nghiệm
    thu; nó KHÔNG được đổi doanh thu của một thương hiệu nào.
    """
    three_brand_period(repository)
    before = brand_view(service.period(**JANUARY))[1]
    detail = next(d for d in service.period(**JANUARY).details
                  if "Panasonic" in d["product_raw"])
    service.store.set_line_product_group(
        order_key=detail["order_key"], product_key=detail["product_key"],
        occurrence_index=detail["occurrence_index"], product_group="GIA_DUNG")

    data = service.period(**JANUARY)
    _buckets, after, recon = brand_view(data)

    assert sales_by_brand(after) == sales_by_brand(before)
    assert recon.is_exact
    assert any(d["classified_product_group"] == "GIA_DUNG" for d in data.details)


def test_a_resolved_identity_without_a_purchase_price_keeps_its_brand(
    repository, service
):
    """`BR-08` + §14 C — thương hiệu VẪN biết, lợi nhuận KPI thì KHÔNG bịa."""
    persist(repository, [
        pair("BH1", product="Máy Giặt LG T2109NT1G",
             kpi_purchase=None, kpi_profit=None),
    ])
    data = service.period(**JANUARY)
    buckets, grouped, recon = brand_view(data)

    assert [b.kind for b in buckets] == [bmx.KIND_BRAND]
    assert grouped[0][0].label == "LG"
    assert grouped[0][1].sales_revenue == Decimal("8000000")
    assert grouped[0][1].kpi_profit is None
    assert grouped[0][1].official_kpi_profit is None
    assert grouped[0][1].converted_sales is None
    assert recon.is_exact


def test_an_unresolved_identity_never_receives_a_fabricated_brand(
    repository, service
):
    """`BR-09` + §14 B — chưa nhận diện ⟹ bucket riêng, không thương hiệu.

    Tên hàng chứa nguyên chữ `LG`, và đó chính là điểm: một phép so chuỗi con
    sẽ xếp nó vào LG. Thẩm quyền danh tính thì không.
    """
    persist(repository, [
        pair("BH1", product="Máy Giặt LG T2109NT1G", kpi_purchase=None,
             kpi_profit=None, reasons=("IDENTITY_UNRESOLVED",)),
    ])
    data = service.period(**JANUARY)
    buckets, grouped, recon = brand_view(data)

    assert [b.kind for b in buckets] == [bmx.KIND_IDENTITY_UNRESOLVED]
    assert grouped[0][0].label == bmx.LABEL_IDENTITY_UNRESOLVED
    assert recon.is_exact


def test_identity_unresolved_and_brand_absent_are_never_merged(
    repository, service
):
    """§10 — hai nguyên nhân, hai dòng. Gộp chúng nói với Owner rằng cách sửa
    là như nhau, trong khi chỉ một trong hai sửa được từ Reports."""
    persist(repository, [
        pair("BH1", product="Máy Giặt LG T2109NT1G", kpi_purchase=None,
             kpi_profit=None, reasons=("IDENTITY_UNRESOLVED",)),
        pair("BH2", product="Bếp từ không rõ danh mục", kpi_purchase=None,
             kpi_profit=None),
    ])
    data = service.period(**JANUARY)
    buckets, grouped, recon = brand_view(data)

    assert {b.kind for b in buckets} == {
        bmx.KIND_IDENTITY_UNRESOLVED, bmx.KIND_BRAND_ABSENT}
    assert len(grouped) == 2
    assert recon.is_exact

    coverage = brand_identity.coverage(buckets)
    assert coverage.branded_lines == 0
    assert coverage.identity_unresolved_lines == 1
    assert coverage.brand_absent_lines == 1
    assert coverage.is_complete is False


def test_on_todays_real_authority_every_line_lands_in_brand_absent(
    repository, service
):
    """Trạng thái ĐO ĐƯỢC của đường production hôm nay.

    Không phải một khiếm khuyết của phép gộp: mọi dòng đã nhận diện đều rơi
    vào `BRAND_ABSENT` vì hợp đồng danh tính không mang thương hiệu. Tổng vẫn
    đối soát tuyệt đối — tiền không mất đi đâu, nó chỉ chưa tách được.
    """
    three_brand_period(repository)
    data = service.period(**JANUARY)
    buckets, grouped, recon = brand_view(
        data, brand_source=brand_identity.canonical_brand)

    assert {b.kind for b in buckets} == {bmx.KIND_BRAND_ABSENT}
    assert len(grouped) == 1
    assert grouped[0][1].sales_revenue == data.totals.sales_revenue
    assert recon.is_exact


def test_an_empty_period_reconciles_without_inventing_a_zero(
    repository, service
):
    data = service.period(date_from=date(2030, 1, 1), date_to=date(2030, 1, 31))
    _buckets, grouped, recon = brand_view(data)
    assert grouped == []
    assert recon.is_exact
    assert data.totals.sales_revenue is None


# ==========================================================================
# 4. TRANG THẬT
# ==========================================================================

@pytest.fixture
def app(monkeypatch, tmp_path, engine, repository):
    legacy = history_store.build(engine=engine)
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "ARTIFACT_DIR", (tmp_path / "outputs").resolve())
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    application = web_server.create_app(db_path=tmp_path / "runs.db",
                                        history=legacy, snapshots=repository)
    application.testing = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def body(client, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200, f"{path} → {response.status_code}"
    return response.get_data(as_text=True)


def metric(html: str, name: str) -> str:
    match = re.search(rf'data-metric="{re.escape(name)}"[^>]*>(.*?)<', html, re.S)
    assert match is not None, f"không tìm thấy data-metric={name}"
    return match.group(1).strip()


def test_the_brand_page_renders(client, repository):
    three_brand_period(repository)
    html = body(client, "/kinh-doanh/thuong-hieu")
    assert "THEO THƯƠNG HIỆU" in html
    assert brand_identity.BRAND_AUTHORITY in html


def test_the_brand_page_defaults_to_the_current_calendar_month(
    client, repository, monkeypatch
):
    """`BR-03` — mặc định là THÁNG DƯƠNG LỊCH HIỆN TẠI, không phải "Toàn bộ
    dữ liệu" và không phải tháng có nhiều dữ liệu nhất."""
    monkeypatch.setattr(web_server, "_today", lambda: date(2026, 3, 17))
    three_brand_period(repository)  # dữ liệu nằm ở 01/2026
    html = body(client, "/kinh-doanh/thuong-hieu")
    assert "Tháng 03/2026" in html
    # Tháng 03 chưa có dòng nào ⟹ trang nói ra sự thật đó, không hiện số của
    # một tháng khác.
    assert 'value="2026-03"' in html


def test_the_month_can_still_be_selected(client, repository):
    three_brand_period(repository)
    html = body(client, "/kinh-doanh/thuong-hieu?ky=2026-01")
    assert "Tháng 01/2026" in html
    assert metric(html, "total-lines") == "3"


def test_the_brand_page_has_no_toan_bo_du_lieu_option(client, repository):
    """§5 — không thêm khung nhìn "Toàn bộ dữ liệu" vào vertical thương hiệu."""
    three_brand_period(repository)
    html = body(client, "/kinh-doanh/thuong-hieu?ky=2026-01")
    assert "Toàn bộ dữ liệu" not in html
    assert 'value="tat-ca"' not in html


def test_the_page_states_the_reconciliation_result_it_actually_measured(
    client, repository
):
    """`BR-04` trên HTML: phép đối soát CHẠY ở mỗi lần tải trang và kết quả
    của nó lên màn hình — không phải một câu khẳng định viết sẵn."""
    three_brand_period(repository)
    html = body(client, "/kinh-doanh/thuong-hieu?ky=2026-01")
    assert 'data-reconciled="yes"' in html
    assert "cộng lại ĐÚNG BẰNG tổng kỳ" in html


def test_the_page_says_plainly_that_no_brand_authority_exists_today(
    client, repository
):
    """Khoảng trống được NÓI RA bằng chữ, ở đúng chỗ tiền đang nằm."""
    three_brand_period(repository)
    html = body(client, "/kinh-doanh/thuong-hieu?ky=2026-01")
    assert brand_identity.BRAND_UNAVAILABLE_NOTE in html
    assert bmx.LABEL_BRAND_ABSENT in html
    assert metric(html, "branded-lines") == "0"


def test_the_primary_navigation_is_unchanged(client, repository):
    """`BR-12` — thanh điều hướng chính vẫn ĐÚNG BA mục (`DEC-185`)."""
    three_brand_period(repository)
    for path in ("/kinh-doanh", "/kinh-doanh/thuong-hieu"):
        html = body(client, path)
        # Bóc thẻ con trước khi so: `DEC-213` đặt một `<svg>` trước nhãn.
        tabs = re.findall(r'class="ncc-tab[^"]*"[^>]*>(.*?)</a>', html, re.S)
        assert [re.sub(r"<[^>]+>", "", t).strip() for t in tabs] == [
            "Báo cáo", "Nhân viên", "Dữ liệu"]


def test_the_brand_page_is_reachable_from_bao_cao(client, repository):
    """§6 — một khung nhìn con của Báo cáo, không một tab mới."""
    three_brand_period(repository)
    assert "/kinh-doanh/thuong-hieu" in body(client, "/kinh-doanh")


def test_the_brand_page_offers_no_target_and_no_edit_surface(client, repository):
    """`BR-11` + §13 — không Target thương hiệu, và không một đường ghi nào.

    Bảng thương hiệu là một khung nhìn CHỈ ĐỌC: mọi thẩm quyền sửa (giá nhập,
    Gia dụng, gán nhân viên, loại dòng, phân loại danh tính) vẫn chỉ có một
    chỗ, và nhân bản chúng ở đây là nhân bản thẩm quyền.
    """
    three_brand_period(repository)
    html = body(client, "/kinh-doanh/thuong-hieu?ky=2026-01")

    # Không một form GHI nào trên trang. Bộ chọn kỳ là `method="get"` —
    # nó điều hướng, nó không ghi gì.
    assert 'method="post"' not in html.lower()
    assert html.lower().count("<form") == 1
    assert 'method="get"' in html.lower()

    # Chữ "Target" chỉ xuất hiện trong ĐÚNG câu nói rằng chưa có Target
    # thương hiệu — không một ô nhập, không một cột nào.
    from app.web import business_presentation as bp
    assert bp.BRAND_NO_TARGET_NOTE in html
    assert "Target" not in html.replace(bp.BRAND_NO_TARGET_NOTE, "")

    # Bảng thương hiệu tự nó không có ô nhập nào.
    assert "<input" not in html.split("Bảng thương hiệu", 1)[1]


def test_no_brand_target_exists_in_the_store_or_the_schema():
    """`BR-11` — không bảng, không cột, không phương thức Target thương hiệu."""
    from tools.db import schema

    target_tables = [t for t in schema.METADATA.tables if "target" in t]
    assert sorted(target_tables) == ["employee_target", "group_target"]
    methods = [m for m in dir(business_store.BusinessDecisionStore)
               if "target" in m.lower()]
    assert all("brand" not in m.lower() for m in methods)


# ==========================================================================
# 5. MUTATION PROBES (§22)
# ==========================================================================
#
# Mỗi probe làm hỏng ĐÚNG MỘT tính chất rồi khẳng định phép kiểm tương ứng
# THẤT BẠI. Chúng chạy trên chính các hàm production — không có bản sao nào
# của phép gộp ở đây.

def test_M1_dropping_the_unknown_bucket_breaks_reconciliation():
    lines = [line(sales="1000"), line(sales="3000")]
    grouped = bmx.group_by_brand(
        lines, [bmx.brand_bucket("LG"), bmx.IDENTITY_UNRESOLVED_BUCKET])
    mutated = [item for item in grouped if item[0].known]
    assert bmx.reconciliation(mutated, bm.totals(lines)).sales_revenue is False


def test_M2_deriving_the_brand_by_substring_breaks_the_authority_test():
    """Nguồn thương hiệu suy từ mã máy: phép gộp vẫn "chạy", nhưng nó gán tiền
    cho một thương hiệu mà không thẩm quyền nào xác nhận."""
    def substring_source(identity):
        if identity is None:
            return None
        code = identity.source_product_code
        return "LG" if code.startswith("T") else None

    detail = {"product_raw": "Máy Giặt LG T2109NT1G", "line": line()}
    honest = brand_identity.bucket_for(
        detail, confirmed_keys=frozenset(), identities=IDENTITIES,
        brand_source=brand_identity.canonical_brand)
    fabricated = brand_identity.bucket_for(
        detail, confirmed_keys=frozenset(), identities=IDENTITIES,
        brand_source=substring_source)

    assert honest.kind == bmx.KIND_BRAND_ABSENT
    assert fabricated.label == "LG"
    # Và chính vì hai kết quả khác nhau, test canh wiring của route là thứ duy
    # nhất chặn được nguồn thứ hai này lọt lên production.
    source = inspect.getsource(web_server)
    assert "substring_source" not in source


def test_M3_including_an_excluded_line_breaks_the_totals(repository, service):
    three_brand_period(repository)
    detail = next(d for d in service.period(**JANUARY).details
                  if "Daikin" in d["product_raw"])
    service.store.exclude_line(
        order_key=detail["order_key"], product_key=detail["product_key"],
        occurrence_index=detail["occurrence_index"])

    data = service.period(**JANUARY)
    _b, grouped, recon = brand_view(data)
    assert recon.is_exact

    # Mutation: nhét dòng đã loại trở lại bảng thương hiệu.
    smuggled = [*data.lines, detail["line"]]
    mutated = bmx.group_by_brand(
        smuggled, [bmx.brand_bucket("X")] * len(smuggled))
    assert bmx.reconciliation(mutated, data.totals).sales_revenue is False


def test_M4_letting_the_employee_decide_the_brand_breaks_the_invariant(
    repository, service
):
    """Nguồn thương hiệu đọc NGƯỜI BÁN: doanh thu thương hiệu đổi sau một lần
    gán lại — đúng điều `BR-06` cấm."""
    three_brand_period(repository)

    def by_employee(lines):
        return {l.employee: l.total_sales for l in lines}

    def employee_buckets(data):
        return [bmx.brand_bucket(d["line"].employee or "?") for d in data.details]

    before = service.period(**JANUARY)
    before_rows = sales_by_brand(
        bmx.group_by_brand(before.lines, employee_buckets(before)))

    detail = next(d for d in before.details if "Daikin" in d["product_raw"])
    service.store.set_employee(
        order_key=detail["order_key"], product_key=detail["product_key"],
        occurrence_index=detail["occurrence_index"], employee="Ly",
        employee_group="GIA_DUNG")

    after = service.period(**JANUARY)
    after_rows = sales_by_brand(
        bmx.group_by_brand(after.lines, employee_buckets(after)))

    assert before_rows != after_rows
    assert by_employee(before.lines) != by_employee(after.lines)
    # Nguồn thật thì KHÔNG đổi — đây là đối chứng của chính probe này.
    assert sales_by_brand(brand_view(before)[1]) == sales_by_brand(
        brand_view(after)[1])


def test_M5_letting_the_product_group_decide_the_brand_breaks_the_invariant(
    repository, service
):
    three_brand_period(repository)

    def group_buckets(data):
        return [bmx.brand_bucket(d["classified_product_group"] or "DIEN_MAY")
                for d in data.details]

    before = service.period(**JANUARY)
    before_rows = sales_by_brand(
        bmx.group_by_brand(before.lines, group_buckets(before)))

    detail = next(d for d in before.details if "Panasonic" in d["product_raw"])
    service.store.set_line_product_group(
        order_key=detail["order_key"], product_key=detail["product_key"],
        occurrence_index=detail["occurrence_index"], product_group="GIA_DUNG")

    after = service.period(**JANUARY)
    after_rows = sales_by_brand(
        bmx.group_by_brand(after.lines, group_buckets(after)))

    assert before_rows != after_rows
    assert sales_by_brand(brand_view(before)[1]) == sales_by_brand(
        brand_view(after)[1])


def test_M6_fabricating_a_kpi_profit_for_a_missing_price_line_is_visible(
    repository, service
):
    """`BR-08` — bịa lợi nhuận cho dòng thiếu giá làm bucket nói một con số
    "chính thức" mà thẩm quyền giá chưa hề đưa ra."""
    persist(repository, [
        pair("BH1", product="Máy Giặt LG T2109NT1G",
             kpi_purchase=None, kpi_profit=None),
    ])
    data = service.period(**JANUARY)
    _b, grouped, _r = brand_view(data)
    assert grouped[0][1].kpi_profit is None
    assert grouped[0][1].official_kpi_profit is None

    fabricated = [
        bm.BusinessLine(**{**{f: getattr(data.lines[0], f)
                              for f in data.lines[0].__dataclass_fields__},
                           "auto_purchase_price": Decimal("5000000"),
                           "auto_kpi_profit": Decimal("3000000")})
    ]
    mutated = bmx.group_by_brand(fabricated, [bmx.brand_bucket("LG")])
    assert mutated[0][1].kpi_profit == Decimal("3000000")
    assert bmx.reconciliation(mutated, data.totals).kpi_profit is False


def test_M7_introducing_a_brand_target_breaks_the_scope_test():
    """`BR-11` — một bảng Target thương hiệu làm test phạm vi đỏ ngay."""
    from tools.db import schema

    target_tables = {t for t in schema.METADATA.tables if "target" in t}
    assert "brand_target" not in target_tables
    mutated = target_tables | {"brand_target"}
    assert sorted(mutated) != ["employee_target", "group_target"]


def test_M8_duplicating_one_line_into_two_brands_breaks_reconciliation():
    lines = [line(sales="1000")]
    company = bm.totals(lines)
    duplicated = [*lines, *lines]
    mutated = bmx.group_by_brand(
        duplicated, [bmx.brand_bucket("LG"), bmx.brand_bucket("Daikin")])
    recon = bmx.reconciliation(mutated, company)
    assert recon.sales_revenue is False
    assert recon.lines is False
