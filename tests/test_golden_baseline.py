"""TASK-GOLDEN-BASELINE-001 — Golden Business Baseline.

    python3 -m pytest tests/test_golden_baseline.py -q

Lưới an toàn regression nghiệp vụ chính của dự án, dựng trên HAI kỳ nghiệp vụ
THẬT của Tín Phát (01.2026 và 06.2026) do Owner cung cấp, đã ẩn danh theo
Owner Decision `OD-GB-1 = A + A1`. Contract đầy đủ:
`docs/tasks/TASK-GOLDEN-BASELINE-001-PLAN.md`.

## Golden này trả lời ĐÚNG một câu

    "Với cùng dữ liệu nghiệp vụ đã được xác minh, phiên bản code mới có tạo ra
     kết quả khác baseline đã được Owner chấp nhận hay không?"

Nó **KHÔNG** chứng minh logic mới đúng, **KHÔNG** chứng minh baseline vốn
đúng, **KHÔNG** thay thế exploratory review, và **KHÔNG** bắt được "baseline
và implementation mới cùng sai" (`governance/core/V4_1_POLICY_FREEZE.md` §6).

## Hai tầng, cố ý không rút gọn thành một

**Tầng 1 — so toàn cấu trúc** với file expected đã commit
(`test_golden_expected_output_matches_pipeline`). Bắt mọi dịch chuyển, kể cả
thứ chưa ai nghĩ tới.

**Tầng 2 — invariant có tên**, mỗi cái khẳng định một con số **văn tự** lấy
từ authority đã tồn tại TRƯỚC code này (CHECK-101-08, `evidence.json`,
DEC-109, DEC-114, Completion Gate sơ bộ). Tầng 2 tồn tại vì tầng 1 tự nó là
một tautology có điều kiện: cả hai vế đều đi qua `build_expected()`, nên một
lỗi trong chính hàm đó sẽ đối xứng và vô hình. Tầng 2 không đi qua hàm đó —
nó so với con số đã in trong tài liệu.

## Không tự sinh lại expected output

Không có `UPDATE_SNAPSHOT=1`, không `--accept`, không `--rewrite-golden`. Test
chỉ ĐỌC `tests/fixtures/golden/expected/*.json`. Sinh lại là hành động bảo trì
tường minh (`python3 -m tests.fixtures.golden.build_expected`), và khi nó đổi
giá trị nghiệp vụ thì cần Owner Decision.

## Dataset scope (chỉ thị §6 — không trộn dataset)

Fixture ở đây là **Tín Phát, hai kỳ, xuất riêng theo tháng**. Nó KHÔNG phải
dataset 11.765 dòng của `evidence.json`, KHÔNG phải dataset 14.389 dòng của
CHECK-108A1-15, và KHÔNG phải dataset của `CHECK-110-16`. Không invariant nào
ở đây được mượn con số của ba dataset kia.
"""

from __future__ import annotations

import inspect
import json
import re
import shutil
import subprocess
import sys
import zipfile
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

from app.modules.domain.models import MAPPING_STATUS_MAPPED
from app.pipeline import build_working_data, run_import
from tests.fixtures.golden import build_expected as gb
from tests.fixtures.golden.anonymize import (
    DROPPED_COLUMNS,
    SURROGATE_COLUMNS,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_DIR = REPO_ROOT / "tests" / "fixtures" / "golden"
CONFIG_DIR = REPO_ROOT / "config"

#: Con số văn tự của tầng 2. Nguồn ghi ngay cạnh, không phải "chạy ra thế".
#:
#: orders / sales_raw / discount / sales_normalized / delta_lines
#:   -> docs/tasks/TASK-101-importer-normalizer.md, mục "Đối Chiếu Dữ Liệu
#:      Thật (2026-08-23)" + CHECK-101-08 (REQUIRED, PASS, E1)
#: sales_raw / erp_profit (nghìn đồng)
#:   -> docs/analysis/_evidence/evidence.json -> raw_by_month_employee
#: quantity -> dòng "Tổng cộng" của chính workbook nguồn
DOCUMENTED = {
    "01.2026": {
        "sheet_data_rows": 352,
        "rows_missing_order_id": 1,
        "raw_rows": 351,
        "orders": 254,
        "quantity_total": Decimal("407"),
        "sales_raw_gross": Decimal("3564610000"),
        "discount_total": Decimal("2300000"),
        "sales_normalized": Decimal("3562310000"),
        "erp_profit_total": Decimal("240032781"),
        "lines_differing": 22,
        "lines_mapped": 351,
        "lines_unmapped": 0,
    },
    "06.2026": {
        "sheet_data_rows": 181,
        "rows_missing_order_id": 1,
        "raw_rows": 180,
        "orders": 146,
        "quantity_total": Decimal("210"),
        "sales_raw_gross": Decimal("1925272000"),
        "discount_total": Decimal("400000"),
        "sales_normalized": Decimal("1924872000"),
        "erp_profit_total": Decimal("95956942"),
        "lines_differing": 1,
        "lines_mapped": 180,
        "lines_unmapped": 0,
    },
}

PERIOD_IDS = [spec["period_label"] for spec in gb.PERIODS]

#: `_environment` tách làm hai nhóm. Tên fixture và snapshot_id của config là
#: BUSINESS-SIGNIFICANT (HB-GB-01, I-11) nên so cứng. Version thư viện chỉ để
#: chẩn đoán: bắt cứng chúng khiến mọi lần nâng cấp `openpyxl` làm Golden đỏ,
#: và cách "sửa" hiển nhiên nhất khi đó là sinh lại expected output — tức là
#: xoá chính bằng chứng (HB-GB-02).
_ENV_STRICT = ("fixture_filename", "config_snapshot_id")
_ENV_ADVISORY = ("python", "openpyxl", "pyyaml")


# ------------------------------------------------------------------- fixtures

@pytest.fixture(scope="module")
def expected_by_period() -> dict:
    out = {}
    for spec in gb.PERIODS:
        path = gb.EXPECTED_DIR / f"{Path(spec['fixture_filename']).stem}.json"
        out[spec["period_label"]] = json.loads(path.read_text(encoding="utf-8"))
    return out


@pytest.fixture(scope="module")
def actual_by_period() -> dict:
    return {spec["period_label"]: gb.build_expected(spec) for spec in gb.PERIODS}


@pytest.fixture(scope="module")
def result_by_period() -> dict:
    return {
        spec["period_label"]: run_import(GOLDEN_DIR / spec["fixture_filename"], CONFIG_DIR)
        for spec in gb.PERIODS
    }


def _spec(period: str) -> dict:
    return next(s for s in gb.PERIODS if s["period_label"] == period)


# ------------------------------------------------------- GB-9 readable diff

_MAX_REPORTED = 20


def diff_structures(expected, actual, path: str = "") -> list[str]:
    """Khác biệt theo ĐƯỜNG DẪN, sắp xếp tất định.

    `assert expected == actual` trên hai dict vài trăm khoá in ra một bức
    tường JSON và người đọc không biết con số nghiệp vụ nào đã đổi. Ở đây mỗi
    dòng là một sự thật: đường dẫn, giá trị cũ, giá trị mới.
    """
    if isinstance(expected, dict) and isinstance(actual, dict):
        out: list[str] = []
        for key in sorted(set(expected) | set(actual)):
            sub = f"{path}.{key}" if path else key
            if key not in expected:
                out.append(f"{sub}: THỪA (chỉ có ở actual) = {actual[key]!r}")
            elif key not in actual:
                out.append(f"{sub}: THIẾU (chỉ có ở expected) = {expected[key]!r}")
            else:
                out.extend(diff_structures(expected[key], actual[key], sub))
        return out
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            return [f"{path}: độ dài {len(expected)} -> {len(actual)}"]
        out = []
        for index, (e, a) in enumerate(zip(expected, actual)):
            out.extend(diff_structures(e, a, f"{path}[{index}]"))
        return out
    if expected != actual:
        return [f"{path}: expected={expected!r} actual={actual!r}"]
    return []


def format_diff(expected: dict, actual: dict, period: str) -> str:
    """Thứ tự báo cáo bắt buộc: môi trường -> counts -> money -> phần còn lại."""
    lines = [f"GOLDEN BASELINE khác biệt — kỳ {period}"]

    env_notes = [
        f"  {key}: expected={expected['_environment'][key]!r} "
        f"actual={actual['_environment'][key]!r}"
        for key in _ENV_ADVISORY
        if expected["_environment"][key] != actual["_environment"][key]
    ]
    if env_notes:
        lines.append("CẢNH BÁO MÔI TRƯỜNG — có thể do đổi thư viện/interpreter, "
                     "KHÔNG chắc là đổi nghiệp vụ. Kiểm tra trước khi kết luận:")
        lines.extend(env_notes)

    diffs = diff_structures(_comparable(expected), _comparable(actual))
    priority = {"counts": 0, "money": 1, "source_footer": 2, "discount_delta": 3}
    diffs.sort(key=lambda line: (priority.get(line.split(".")[0].split(":")[0], 9), line))

    lines.append(f"{len(diffs)} khác biệt nghiệp vụ:")
    lines.extend(f"  {line}" for line in diffs[:_MAX_REPORTED])
    if len(diffs) > _MAX_REPORTED:
        lines.append(f"  … và {len(diffs) - _MAX_REPORTED} khác biệt khác.")
    lines.append("Nếu đây là thay đổi nghiệp vụ CÓ CHỦ ĐÍCH: cần Owner Decision, "
                 "rồi chạy `python3 -m tests.fixtures.golden.build_expected`.")
    return "\n".join(lines)


def _comparable(payload: dict) -> dict:
    """Bỏ đúng ba trường version khỏi phép so cứng (xem `_ENV_ADVISORY`)."""
    trimmed = dict(payload)
    trimmed["_environment"] = {
        k: v for k, v in payload["_environment"].items() if k not in _ENV_ADVISORY
    }
    return trimmed


def _strict_bytes(payload: dict) -> bytes:
    """Serialize CHỈ phần STRICT BUSINESS CONTRACT — loại `_ENV_ADVISORY`.

    GB-IR-01: `python`/`pyyaml`/`openpyxl` là metadata môi trường, không phải
    business payload. Chạy Golden trên một interpreter/thư viện hợp lệ khác
    (vd. Python 3.12 thay vì 3.11, PyYAML 6.0.3 thay vì 6.0.1) không được
    làm Golden FAIL khi business semantics giống nhau — đó chính là false
    regression signal mà Independent Review xác nhận.

    Dùng CHUNG bộ serializer với `gb.write` (cùng tham số `json.dumps`) nên
    phép so vẫn là so BYTE thật của phần strict, không phải so cấu trúc: một
    nondeterminism ẩn trong bất kỳ trường business nào — whitespace, thứ tự
    khoá, định dạng số — vẫn lộ ra. Chỉ đúng ba trường advisory bị loại khỏi
    phép so, không hơn.
    """
    return (
        json.dumps(_comparable(payload), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")


# ================================================== TẦNG 1 — so toàn cấu trúc

@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_expected_output_matches_pipeline(period, expected_by_period, actual_by_period):
    """Pipeline THẬT trên fixture đã commit == expected output đã commit."""
    expected = expected_by_period[period]
    actual = actual_by_period[period]
    if _comparable(expected) != _comparable(actual):
        pytest.fail(format_diff(expected, actual, period))


@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_expected_output_is_regenerable_byte_identical(period, expected_by_period,
                                                              actual_by_period):
    """Sinh lại STRICT BUSINESS CONTRACT cho ra ĐÚNG TỪNG BYTE file đã commit.

    Nếu không, còn một nguồn nondeterminism chưa xử lý ở một trường business
    và expected output không được phép coi là đã khoá (GB-6).

    **GB-IR-01 (repair cycle #1).** Trước bản sửa này, phép so là byte-thô
    của TOÀN BỘ file — bao gồm `_environment.python`/`pyyaml`/`openpyxl`.
    Chạy trên một Python/PyYAML hợp lệ khác với lúc sinh fixture (vd. 3.11.15
    → 3.12) làm ba trường advisory đó đổi, và test đỏ dù business payload
    giống hệt — một FALSE REGRESSION SIGNAL. `_strict_bytes()` loại đúng ba
    trường advisory đó, không hơn; mọi trường business vẫn so byte-thật.
    """
    spec = _spec(period)
    committed = (gb.EXPECTED_DIR / f"{Path(spec['fixture_filename']).stem}.json")
    committed_payload = json.loads(committed.read_text(encoding="utf-8"))
    assert _strict_bytes(actual_by_period[period]) == _strict_bytes(committed_payload), (
        f"{committed.name}: sinh lại KHÔNG byte-identical trên phần STRICT "
        f"BUSINESS CONTRACT. Hoặc còn nondeterminism ở một trường business, "
        f"hoặc file đã commit lỗi thời."
    )


# ------------------------------------------------ GB-IR-01 — repair cycle #1

def test_golden_strict_comparison_still_catches_a_business_mutation(expected_by_period):
    """GB-IR-01 TEST 1 — mutate MỘT trường business, `_strict_bytes` phải khác.

    Chứng minh việc tách advisory ra không làm mất khả năng phát hiện regression
    nghiệp vụ thật: `_strict_bytes` chỉ loại đúng ba trường
    `python`/`pyyaml`/`openpyxl`, không loại bất kỳ trường business nào.
    """
    expected = expected_by_period["01.2026"]
    mutated = json.loads(json.dumps(expected))
    mutated["counts"]["orders"] = 253
    assert _strict_bytes(mutated) != _strict_bytes(expected), (
        "mutate `counts.orders` không làm strict-bytes đổi — comparison đã "
        "loại nhầm một trường business")


@pytest.mark.parametrize("advisory_field", sorted(_ENV_ADVISORY))
def test_golden_advisory_metadata_mismatch_does_not_fail_golden(advisory_field, expected_by_period):
    """GB-IR-01 TEST 2+3 — đổi `python`/`pyyaml`/`openpyxl` KHÔNG làm Golden đỏ.

    Đây chính là kịch bản Independent Review tái hiện: chạy trên một
    interpreter/thư viện hợp lệ khác lúc sinh fixture. Business payload không
    đổi, nên `_strict_bytes` phải giữ nguyên dù giá trị advisory khác hẳn.
    """
    expected = expected_by_period["01.2026"]
    mutated = json.loads(json.dumps(expected))
    assert mutated["_environment"][advisory_field] == expected["_environment"][advisory_field]
    mutated["_environment"][advisory_field] = "9.9.9-mutated-for-test"
    assert _strict_bytes(mutated) == _strict_bytes(expected), (
        f"đổi `_environment.{advisory_field}` làm strict-bytes đổi — trường "
        f"advisory đang lọt vào phép so PASS/FAIL")


@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_advisory_metadata_is_still_recorded_for_diagnostics(period, actual_by_period):
    """GB-IR-01 TEST 4 — advisory metadata không bị XOÁ, chỉ không tham gia strict.

    §3 của repair chỉ thị: advisory có thể tiếp tục được ghi để phục vụ
    debugging/evidence. Test này khoá đúng nửa còn lại của invariant B — nó
    vẫn tồn tại và đọc được, không phải bị gỡ bỏ để né finding.
    """
    env = actual_by_period[period]["_environment"]
    for field in _ENV_ADVISORY:
        assert env.get(field), f"`_environment.{field}` bị bỏ trống hoặc mất"
    for field in _ENV_STRICT:
        assert env.get(field), f"`_environment.{field}` (strict) bị bỏ trống hoặc mất"


@pytest.fixture(scope="module", autouse=True)
def _expected_output_files_are_read_only():
    """GB-IR-01 TEST 5 — chạy suite này KHÔNG được tự sinh lại expected output.

    Snapshot bytes của mọi file `expected/*.json` TRƯỚC khi module này chạy
    bất kỳ test nào, so lại SAU KHI toàn bộ module chạy xong — không phụ
    thuộc thứ tự test nào chạy trước/sau. Nếu một dòng code trong bất kỳ test
    nào lỡ gọi `gb.write()`/`gb.main()` vào `EXPECTED_DIR`, assertion ở
    finalizer bắt được ngay, đúng chính sách "không có UPDATE_SNAPSHOT=1
    tự động" của `tests/fixtures/golden/build_expected.py`.
    """
    before = {p.name: p.read_bytes() for p in sorted(gb.EXPECTED_DIR.glob("*.json"))}
    yield
    after = {p.name: p.read_bytes() for p in sorted(gb.EXPECTED_DIR.glob("*.json"))}
    assert after == before, (
        "expected output bị ghi đè trong lúc chạy test suite — expected phải "
        "là read-only đối với mọi test, chỉ sinh lại bằng "
        "`python3 -m tests.fixtures.golden.build_expected` chạy tay")


# ============================================ TẦNG 2 — invariant có tên

@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_period_row_and_order_counts(period, actual_by_period):
    """I-01 (P1) — 254 đơn 01.2026, 146 đơn 06.2026.

    Authority: `PROJECT/PROJECT_PROGRESS.md` -> "Completion Gate sơ bộ" dòng 1;
    `docs/tasks/TASK-101-importer-normalizer.md` CHECK-101-08 (REQUIRED, PASS,
    E1); `docs/analysis/_evidence/evidence.json` -> `raw_by_month_employee`.
    """
    doc = DOCUMENTED[period]
    counts = actual_by_period[period]["counts"]
    assert counts["sheet_data_rows"] == doc["sheet_data_rows"]
    assert counts["rows_missing_order_id"] == doc["rows_missing_order_id"]
    assert counts["raw_rows"] == doc["raw_rows"]
    assert counts["orders"] == doc["orders"], (
        f"{period}: số OrderID duy nhất = {counts['orders']}, "
        f"tài liệu ghi {doc['orders']}"
    )


@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_raw_total_matches_source_total_row(period, actual_by_period):
    """I-02 (P1) — tổng do engine tính khớp dòng "Tổng cộng" của CHÍNH file.

    Dòng đó do ERP ghi, không do engine này tạo, nên đây là oracle **độc lập
    với engine** duy nhất có. Nếu `raw_reader` sót hay đếm trùng một dòng bất
    kỳ, hai vế lệch ngay. Authority: CHECK-101-08 mục "Đối chiếu chéo độc lập".
    """
    payload = actual_by_period[period]
    footer = payload["source_footer"]
    money = payload["money"]
    assert Decimal(money["sales_raw_gross"][0]) == Decimal(str(footer["sales"]))
    assert Decimal(money["discount_total"][0]) == Decimal(str(footer["discount"]))
    assert Decimal(money["quantity_total"][0]) == Decimal(str(footer["quantity"]))
    assert Decimal(money["erp_profit_total"][0]) == Decimal(str(footer["profit"]))
    doc = DOCUMENTED[period]
    assert Decimal(money["sales_raw_gross"][0]) == doc["sales_raw_gross"]
    assert Decimal(money["quantity_total"][0]) == doc["quantity_total"]
    assert Decimal(money["erp_profit_total"][0]) == doc["erp_profit_total"]


@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_discount_delta_equals_discount_column(period, actual_by_period):
    """I-03 (P2) — `TotalSales = SellPrice x Quantity - Discount`.

    Mọi dòng lệch giữa `Doanh số bán` (gross ERP) và số engine tính phải lệch
    ĐÚNG bằng `Chiết khấu` của chính dòng đó — không hơn, không kém, không có
    dòng nào lệch một số khác. Authority: DEC-114; CHECK-101-08 mục Item 4.
    """
    doc = DOCUMENTED[period]
    delta = actual_by_period[period]["discount_delta"]
    money = actual_by_period[period]["money"]
    assert delta["lines_differing"] == doc["lines_differing"]
    assert Decimal(delta["total_delta"]) == doc["discount_total"]
    assert delta["every_delta_equals_that_line_discount"] is True
    assert Decimal(money["sales_normalized"][0]) == doc["sales_normalized"]
    assert (Decimal(money["sales_raw_gross"][0]) - Decimal(money["discount_total"][0])
            == Decimal(money["sales_normalized"][0]))


@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_employee_ownership_matrix(period, actual_by_period):
    """I-11 (P3) — quyền sở hữu dòng thuộc đúng một nhân viên đã map.

    Sai chủ sở hữu dòng là sai KPI, và sai KPI là sai lương. Authority:
    DEC-104, DEC-127 §1, DEC-132; `config/employees.yaml`.
    """
    doc = DOCUMENTED[period]
    payload = actual_by_period[period]
    assert payload["counts"]["lines_mapped"] == doc["lines_mapped"]
    assert payload["counts"]["lines_unmapped"] == doc["lines_unmapped"]
    assert payload["counts"]["orders_with_multiple_employee_raw"] == 0
    assert set(payload["employees"]) == {"Tín Phát"}
    tin_phat = payload["employees"]["Tín Phát"]
    assert tin_phat["orders"] == doc["orders"]
    assert tin_phat["lines"] == doc["raw_rows"]
    assert Decimal(tin_phat["sales_normalized"][0]) == doc["sales_normalized"]


@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_config_snapshot_id_is_pinned(period, expected_by_period, actual_by_period):
    """I-11 (P3) — danh tính master data được chốt bằng `snapshot_id`.

    `snapshot_id` dẫn từ NỘI DUNG LOGIC của `config/employees.yaml`, nên sửa
    comment không làm nó đổi còn sửa một `normalized`/`group`/`raw_prefix` thì
    có. Nó bắt được config drift mà aggregate có thể không thấy.
    """
    assert (actual_by_period[period]["_environment"]["config_snapshot_id"]
            == expected_by_period[period]["_environment"]["config_snapshot_id"])


@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_lead_source_split_and_provenance(period, actual_by_period):
    """I-04 / I-06 (P6) — 100% ADS, TOÀN BỘ qua mặc định cấp nhân viên.

    `0` đơn đi qua rule từ khoá "ADS" — không phải vì rule hỏng mà vì dữ liệu
    thật không có dòng nào chứa từ khoá đó. Authority: DEC-109 (sửa bởi
    DEC-119); `evidence.json` -> `ads_keyword_cell_hits` = 0; CHECK-101-08.
    """
    doc = DOCUMENTED[period]
    lead = actual_by_period[period]["lead_source"]
    assert lead["orders_by_final"] == {"ADS": doc["orders"]}
    assert lead["orders_by_auto"] == {"ADS": doc["orders"]}
    assert lead["lines_by_final"] == {"ADS": doc["raw_rows"]}
    assert lead["orders_by_provenance"] == {
        "Auto:Employee Default (Tín Phát)": doc["orders"]
    }
    assert "Auto:ADS Rule" not in lead["orders_by_provenance"]
    assert set(lead["orders_by_final"]) <= {"PERSONAL", "ADS"}


@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_lead_source_is_decided_at_order_level(period, actual_by_period, result_by_period):
    """I-05 (P6) — hai dòng cùng OrderID không bao giờ mang hai LeadSource."""
    assert actual_by_period[period]["counts"]["orders_with_multiple_lead_source"] == 0
    for order in result_by_period[period].orders:
        assert len({line.lead_source_final for line in order.lines}) == 1


@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_scheme_distribution(period, actual_by_period):
    """I-07 (P7) — tỉ lệ quy đổi tra từ config, không suy từ tên nhân viên.

    Tín Phát 100% ADS ⇒ `ADS_7_5` @ `0.075` cho mọi dòng, và tỉ lệ đó phải
    bằng đúng giá trị trong `config/conversion_rates.yaml`. Authority:
    ADR-106 §3/§4; DEC-127 §3; Completion Gate sơ bộ (TASK-108).
    """
    doc = DOCUMENTED[period]
    conv = actual_by_period[period]["conversion"]
    rates = yaml.safe_load((CONFIG_DIR / "conversion_rates.yaml").read_text("utf-8"))
    ads_rate = next(r["rate"] for r in rates["conversion_schemes"]
                    if r["scheme"] == "ADS_7_5")
    assert conv["scheme_distribution"] == {f"ADS_7_5@{Decimal(ads_rate)}": doc["raw_rows"]}
    assert conv["unresolved_lines"] == 0
    assert conv["scheme_provenance"] == {"Auto:LeadSource (ADS_7_5)": doc["raw_rows"]}


@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_unmapped_never_borrows_a_rate(period, result_by_period):
    """I-09 / I-10 (P7) — dòng chưa map KHÔNG BAO GIỜ nhận tỉ lệ.

    **Trên dataset này khẳng định là VACUOUS**: cả hai kỳ có 0 dòng unmapped
    (đo được, khớp CHECK-101-08). Test vẫn ở đây vì nó là một invariant thật
    và sẽ có hiệu lực ngay khi fixture tương lai có dòng unmapped — nhưng
    Golden Coverage Map ghi path này là **PARTIAL**, không phải COVERED. Nhánh
    unmapped do `tests/test_conversion_engine.py::
    test_unmapped_employee_line_never_receives_a_rate` phủ thật sự.
    """
    for order in result_by_period[period].orders:
        for line in order.lines:
            if line.employee_mapping_status != MAPPING_STATUS_MAPPED:
                assert line.conversion_rate_final is None
                assert line.conversion_scheme_final in (None, "Unresolved")


@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_is_stable_when_a_future_policy_row_is_added(period, actual_by_period, tmp_path):
    """I-08 (P8) — tra tỉ lệ dùng NGÀY CỦA ĐƠN, không dùng "hôm nay".

    Thêm một dòng chính sách `effective_from: 2027-01-01` rồi chạy lại một kỳ
    lịch sử phải cho kết quả KHÔNG ĐỔI. Nếu engine tra theo thời điểm chạy,
    dòng 2027 sẽ nuốt mất kỳ 2026 và một báo cáo đã phát hành bị viết lại.
    Authority: DEC-121; Completion Gate sơ bộ (TASK-108).
    """
    config = tmp_path / "config"
    shutil.copytree(CONFIG_DIR, config)
    rates = yaml.safe_load((config / "conversion_rates.yaml").read_text("utf-8"))
    rates["conversion_schemes"].append({
        "employee": "*", "employee_group": "*", "lead_source": "ADS",
        "product_group": "*", "scheme": "ADS_FUTURE_PROBE", "rate": "0.999",
        "effective_from": "2027-01-01", "effective_to": None,
    })
    (config / "conversion_rates.yaml").write_text(
        yaml.safe_dump(rates, allow_unicode=True), encoding="utf-8")

    spec = _spec(period)
    result = run_import(GOLDEN_DIR / spec["fixture_filename"], config)
    lines = [l for o in result.orders for l in o.lines]
    observed = {}
    for line in lines:
        key = f"{line.conversion_scheme_final}@{line.conversion_rate_final}"
        observed[key] = observed.get(key, 0) + 1
    assert observed == actual_by_period[period]["conversion"]["scheme_distribution"], (
        "Một dòng chính sách có hiệu lực từ 2027 đã làm đổi kết quả của một kỳ "
        "2026 — engine đang tra theo 'hôm nay', không theo ngày của đơn (DEC-121)."
    )


@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_all_prices_pending(period, actual_by_period):
    """P15 — chốt TRẠNG THÁI HIỆN TẠI: chưa có Price Master.

    Mọi giá nhập là `Pending` nên mọi `accounting_profit` cũng `Pending`. Khi
    TASK-105 có Price Master thật, test này sẽ đỏ — và đó là ĐÚNG: đó là một
    thay đổi nghiệp vụ có chủ đích, cần Owner Decision và sinh lại expected
    output, không phải một lỗi.
    """
    doc = DOCUMENTED[period]
    pricing = actual_by_period[period]["pricing"]
    assert pricing["price_source_distribution"] == {"Pending": doc["raw_rows"]}
    assert pricing["accounting_profit_pending"] == doc["raw_rows"]


@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_review_queue_shape(period, expected_by_period, actual_by_period):
    """I-16 (P14) — Review Queue là BÁO CÁO đi kèm, không phải stage sửa dữ liệu.

    So `category`/`severity`/`scope`/`order_id`/tập dòng bị ảnh hưởng — KHÔNG
    so nguyên văn `message`: `message` là projection thuần từ payload có kiểu
    và provenance (DEC-133), nên đổi cách diễn đạt không phải regression
    nghiệp vụ, còn đổi tập dòng thì có.

    Các con số ở đây được đo LẦN ĐẦU trên dataset này tại phiên
    TASK-GOLDEN-BASELINE-001. Chúng KHÔNG được đối chiếu với mốc của
    `CHECK-110-16` (dataset 11.765 dòng, toàn công ty) — đó là dataset khác.
    """
    expected = expected_by_period[period]["review_queue"]
    actual = actual_by_period[period]["review_queue"]
    assert actual["total_items"] == expected["total_items"]
    assert actual["by_category"] == expected["by_category"]
    assert actual["by_severity"] == expected["by_severity"]
    assert actual["by_scope"] == expected["by_scope"]
    assert actual["items"] == expected["items"]


@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_validation_never_blocks_the_import(period, result_by_period):
    """I-16 (P14) — validation không bao giờ chặn import (đặc tả §18, DEC-128).

    Một import mà mọi dòng đều có finding vẫn phải trả về `ImportResult` đầy
    đủ. Ở đây: có 41/30 finding mà vẫn đủ 254/146 đơn.
    """
    result = result_by_period[period]
    assert result.review_queue.items
    assert result.orders
    assert len(result.orders) == DOCUMENTED[period]["orders"]


@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_raw_rows_are_immutable_with_provenance(period, result_by_period):
    """I-15 — lớp RAW bất biến, giữ `source_file`/`source_sheet`/`source_row`.

    Authority: ADR-102; CHECK-101-11.
    """
    spec = _spec(period)
    working = build_working_data(GOLDEN_DIR / spec["fixture_filename"], CONFIG_DIR)
    rows = [line.raw for line in working.lines]
    assert {r.source_file for r in rows} == {spec["fixture_filename"]}
    assert {r.source_sheet for r in rows} == {"SỔ CHI TIẾT BÁN HÀNG"}
    assert len({r.source_row for r in rows}) == len(rows)
    with pytest.raises(Exception):
        rows[0].order_id = "MUTATED"


@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_order_graph_preserves_membership_and_order(period, expected_by_period,
                                                           result_by_period):
    """Thứ tự và thành viên của `Order -> lines` là business state thật.

    `Order.total_sales` và `line_count` đọc từ nó, nên dời một dòng từ đơn A
    sang đơn B mà giữ nguyên mọi scalar phải bị bắt (bài học Audit O2 của
    TASK-110 — aggregate đã sort thì mù với việc này).
    """
    expected = expected_by_period[period]["order_graph"]
    actual = {
        o.order_id: [l.raw.source_row for l in o.lines]
        for o in result_by_period[period].orders
    }
    assert actual == expected


@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_lines_digest_is_unchanged(period, expected_by_period, actual_by_period):
    """Canh mức DÒNG cái mà aggregate mù.

    Hoán đổi giá của hai dòng trong cùng một đơn không đổi bất kỳ tổng nào —
    kể cả tổng của chính đơn đó. Digest lấy tập trường từ
    `dataclasses.fields()`, nên một trường thêm vào ngày mai tự động được canh.
    """
    assert (actual_by_period[period]["lines_digest"]
            == expected_by_period[period]["lines_digest"])
    assert (actual_by_period[period]["_covered_digest_fields"]
            == expected_by_period[period]["_covered_digest_fields"])


# ============================================== GB-4 — khoá điểm vào pipeline

def test_golden_pipeline_entry_point_signature_is_locked():
    """Golden phải đo ĐÚNG đường mà production chạy, không đo một đường khác.

    Nếu ai đó đổi chữ ký `run_import`, test này báo ngay thay vì để Golden
    lặng lẽ đo sai ranh giới.
    """
    assert gb.PIPELINE_ENTRY_POINT == "app.pipeline.run_import"
    params = list(inspect.signature(run_import).parameters)
    # S051: nối biên `TASK-105D` product identity (DEC-154 P00) — hai tham
    # số DI mới, cả hai optional/backward-compatible, không đổi 4 tham số cũ.
    # Golden #1 KPI vertical slice (TASK-108B minimum B7/B8 slice, DEC-143 +
    # DEC-144): thêm `confirmed_adjustment_source`, cũng optional/backward-
    # compatible — không đổi 6 tham số cũ. Golden #1 Repair Batch #1 (B02):
    # thêm `eligible_costs_authority`, optional/backward-compatible — không
    # đổi 7 tham số cũ.
    assert params == ["raw_path", "config_dir", "price_provider",
                      "product_group_provider", "identity_registry",
                      "identity_resolver_factory",
                      "confirmed_adjustment_source",
                      "eligible_costs_authority"]
    assert list(inspect.signature(build_working_data).parameters) == params


# ================================================ GB-1 — provenance bắt buộc

@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_every_metric_group_has_a_provenance_anchor(period, expected_by_period):
    """Mỗi nhóm aggregate phải truy về một artifact đã commit TRƯỚC baseline.

    Không aggregate nào được phép chỉ có nguồn là "output của `run_import()`
    hôm nay" — đó chính là cách một hành vi sai bị đóng băng thành "chuẩn".
    Ngoại lệ DUY NHẤT được tuyên bố tường minh: `review_queue` và `pricing`,
    hai nhóm chưa từng được đo trên hai kỳ Tín Phát trước phiên này; anchor
    của chúng nói rõ điều đó thay vì giả vờ có mốc lịch sử.
    """
    anchors = expected_by_period[period]["_provenance"]["metric_anchors"]
    for key in ("counts.orders", "money.sales_raw_gross", "money.discount_total",
                "money.sales_normalized", "source_footer", "lead_source",
                "conversion", "discount_delta", "employees"):
        assert anchors.get(key), f"thiếu provenance anchor cho {key}"
    assert "TASK-GOLDEN-BASELINE-001" in anchors["review_queue"]


@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_provenance_records_the_real_source_workbook(period, expected_by_period):
    """SHA256 của workbook production gốc được ghi lại, và chỉ SHA256.

    Bản thân workbook không bao giờ vào repo (DEC-108); hash là một chiều nên
    ghi nó không làm rò rỉ gì, và nó là thứ duy nhất chứng minh fixture này
    sinh ra từ đúng file Owner cấp.
    """
    prov = expected_by_period[period]["_provenance"]
    assert prov["source_type"] == "production_workbook"
    assert re.fullmatch(r"[0-9a-f]{64}", prov["source_sha256"])
    assert prov["source_period"] == period
    assert prov["anonymization_version"]
    assert "11.765" in prov["dataset_scope"] and "14.389" in prov["dataset_scope"], (
        "dataset_scope phải nói rõ đây KHÔNG phải ba dataset lịch sử kia")


# ==================================================== HB-GB-01 / HB-GB-03

def test_golden_fixture_filenames_are_pinned(expected_by_period):
    """HB-GB-01 — `RawRow.source_file` = `path.name`, nên tên file là contract.

    Đổi tên fixture sẽ làm Golden vỡ ở một chỗ khó hiểu. Chốt tên ở đây để nó
    vỡ ở một chỗ dễ hiểu.
    """
    for spec in gb.PERIODS:
        path = GOLDEN_DIR / spec["fixture_filename"]
        assert path.is_file(), f"thiếu fixture {spec['fixture_filename']}"
        assert (expected_by_period[spec["period_label"]]["_environment"]
                ["fixture_filename"] == spec["fixture_filename"])


_PHONE = re.compile(r"(?<!\d)(0\d{8,10}|\+?84\d{8,10})(?!\d)")
#: Số điện thoại của chính Tín Phát nằm trong `config/employees.yaml` và trong
#: dòng tiêu đề của workbook. Đó là master data nhân viên đã có sẵn trong repo
#: từ trước, KHÔNG phải PII khách hàng — nên nó là ngoại lệ có tên, không phải
#: một lỗ hổng trong phép quét.
_ALLOWED_EMPLOYEE_PHONES = {"0869931931"}


@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_fixture_contains_no_customer_pii(period):
    """HB-GB-03 — quét CHÍNH blob `.xlsx` đã commit, không quét bản trong bộ nhớ.

    `PII_FIELD_NAMES` không bao gồm `Diễn giải` và IMEI, nên một phép quét dựa
    vào danh sách đó sẽ mù đúng ở hai chỗ nguy hiểm nhất. Ở đây quét toàn bộ
    XML bên trong file — kể cả shared strings — nên không trường nào trốn được.
    """
    path = GOLDEN_DIR / _spec(period)["fixture_filename"]
    blob = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.endswith((".xml", ".rels")):
                blob.append(archive.read(name).decode("utf-8", "replace"))
    text = "\n".join(blob)

    phones = {m.group(0) for m in _PHONE.finditer(text)} - _ALLOWED_EMPLOYEE_PHONES
    assert not phones, f"{path.name}: còn {len(phones)} chuỗi giống số điện thoại"

    result = run_import(path, CONFIG_DIR)
    lines = [l for o in result.orders for l in o.lines]
    for name in DROPPED_COLUMNS:
        field = {"shipper": "shipper_raw"}.get(name, name)
        assert all(getattr(l.raw, field) is None for l in lines), (
            f"cột {name} lẽ ra bị xoá hẳn nhưng vẫn có giá trị")
    for name, prefix in SURROGATE_COLUMNS.items():
        values = {getattr(l.raw, name) for l in lines}
        assert all(v is None or re.fullmatch(rf"{prefix}_\d{{4}}", v) for v in values), (
            f"cột {name} còn giá trị không phải surrogate")
    notes = {l.raw.note_raw for l in lines}
    assert notes <= {None, "ADS", "BAN_HANG"}, (
        f"`Diễn giải` còn văn xuôi thật: {len(notes)} giá trị phân biệt")


# ================================================ GB-10 — falsification

def _mutated_config(tmp_path: Path, mutate) -> Path:
    config = tmp_path / "config"
    shutil.copytree(CONFIG_DIR, config)
    mutate(config)
    return config


def _scheme_distribution(fixture: Path, config: Path) -> dict:
    result = run_import(fixture, config)
    out: dict = {}
    for order in result.orders:
        for line in order.lines:
            key = f"{line.conversion_scheme_final}@{line.conversion_rate_final}"
            out[key] = out.get(key, 0) + 1
    return out


def _bump_ads_rate(config: Path) -> None:
    path = config / "conversion_rates.yaml"
    data = yaml.safe_load(path.read_text("utf-8"))
    for row in data["conversion_schemes"]:
        if row["scheme"] == "ADS_7_5":
            row["rate"] = "0.080"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def _drop_tin_phat_default(config: Path) -> None:
    path = config / "employees.yaml"
    data = yaml.safe_load(path.read_text("utf-8"))
    for row in data["employees"]:
        if row["normalized"] == "Tín Phát":
            row["default_lead_source"] = None
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def _remove_tin_phat(config: Path) -> None:
    path = config / "employees.yaml"
    data = yaml.safe_load(path.read_text("utf-8"))
    data["employees"] = [r for r in data["employees"] if r["normalized"] != "Tín Phát"]
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def _add_matching_ads_keyword(config: Path) -> None:
    path = config / "lead_source.yaml"
    data = yaml.safe_load(path.read_text("utf-8"))
    data["ads_keywords"].append("BAN_HANG")
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


@pytest.mark.parametrize("mutate,name", [
    (_bump_ads_rate, "tỉ lệ ADS 7,5% -> 8,0%"),
    (_drop_tin_phat_default, "Tín Phát mất `default_lead_source: ADS`"),
    (_remove_tin_phat, "xoá Tín Phát khỏi master data"),
])
def test_golden_can_actually_fail_on_a_business_mutation(mutate, name, actual_by_period,
                                                         tmp_path):
    """GB-10 — chứng minh Golden CÓ THỂ đỏ. Không có phép này nó là tautology.

    Mỗi đột biến là một cách con số sai đi vào bảng lương trong đời thật: sai
    tỉ lệ, sai nguồn đơn mặc định, mất nhân viên khỏi master data.
    """
    config = _mutated_config(tmp_path, mutate)
    for spec in gb.PERIODS:
        observed = _scheme_distribution(GOLDEN_DIR / spec["fixture_filename"], config)
        baseline = actual_by_period[spec["period_label"]]["conversion"]["scheme_distribution"]
        assert observed != baseline, (
            f"đột biến '{name}' KHÔNG làm Golden đỏ ở kỳ "
            f"{spec['period_label']} — path này chưa được phủ thật")


def test_golden_note_label_is_functional_not_decorative(actual_by_period, tmp_path):
    """GB-10 — nhãn A1 của `Diễn giải` thật sự được business logic ĐỌC.

    Fixture thay toàn bộ văn xuôi `Diễn giải` bằng nhãn `BAN_HANG`. Nếu nhãn
    đó chỉ là trang trí thì việc thêm `BAN_HANG` vào `ads_keywords` sẽ không
    đổi gì. Ở đây nó phải làm provenance chuyển từ `Auto:Employee Default`
    sang `Auto:ADS Rule` — chứng minh đường `note_raw -> LeadSourceClassifier`
    còn sống trong fixture đã ẩn danh.
    """
    config = _mutated_config(tmp_path, _add_matching_ads_keyword)
    for spec in gb.PERIODS:
        period = spec["period_label"]
        fixture = GOLDEN_DIR / spec["fixture_filename"]

        # Đơn mà MỌI dòng đều có `Diễn giải` trống không thể khớp từ khoá nào —
        # `note_raw` của chúng là `None`. Đó là trạng thái THẬT của dữ liệu
        # nguồn (`Diễn giải` trống ở 2 dòng kỳ 01 và 1 dòng kỳ 06), không phải
        # hệ quả của anonymization; nên chúng được trừ ra tường minh thay vì
        # làm khẳng định yếu đi.
        untouched = {
            o.order_id for o in run_import(fixture, CONFIG_DIR).orders
            if all(l.note_raw is None for l in o.lines)
        }

        result = run_import(fixture, config)
        flipped = {o.order_id for o in result.orders
                   if o.lead_source_source_of_value == "Auto:ADS Rule"}
        still_default = {o.order_id for o in result.orders
                         if o.lead_source_source_of_value != "Auto:ADS Rule"}

        assert flipped, (
            f"{period}: nhãn `Diễn giải` không được đọc — anonymization đã giết "
            f"một đường nghiệp vụ thật")
        assert still_default == untouched, (
            f"{period}: đúng những đơn có `Diễn giải` trống mới được phép không "
            f"đổi; lệch {still_default ^ untouched}")
        assert len(flipped) == len(result.orders) - len(untouched)

        baseline = actual_by_period[period]["lead_source"]
        assert "Auto:ADS Rule" not in baseline["orders_by_provenance"]


def test_golden_diff_reports_the_exact_path_that_changed(expected_by_period):
    """GB-9 — thông báo FAIL nêu đúng đường dẫn và cặp giá trị.

    Một `assert a == b` trên hai dict vài trăm khoá là vô dụng với người đọc.
    """
    expected = expected_by_period["01.2026"]
    broken = json.loads(json.dumps(expected))
    broken["counts"]["orders"] = 253
    message = format_diff(expected, broken, "01.2026")
    assert "counts.orders: expected=254 actual=253" in message
    assert "1 khác biệt nghiệp vụ" in message


def test_golden_diff_truncates_and_says_how_many_were_hidden(expected_by_period):
    """GB-9 — diff dài bị cắt, nhưng KHÔNG im lặng: nói rõ đã giấu bao nhiêu."""
    expected = expected_by_period["01.2026"]
    broken = json.loads(json.dumps(expected))
    for record in broken["orders_detail"]:
        record["line_count"] = -1
    message = format_diff(expected, broken, "01.2026")
    assert "và " in message and "khác biệt khác" in message
    assert message.count("\n") <= _MAX_REPORTED + 6


# ================================================= GB-6 — determinism

_DETERMINISM_ENVS = [
    {"PYTHONHASHSEED": "0"},
    {"PYTHONHASHSEED": "1"},
    {"PYTHONHASHSEED": "12345"},
    {"PYTHONHASHSEED": "7", "TZ": "Pacific/Kiritimati", "LC_ALL": "C"},
    {"PYTHONHASHSEED": "7", "TZ": "UTC", "LC_ALL": "C.UTF-8"},
]

_DETERMINISM_SNIPPET = (
    "import hashlib,json,sys;"
    "sys.path.insert(0,{repo!r});"
    "from tests.fixtures.golden import build_expected as gb;"
    "p=[gb.build_expected(s) for s in gb.PERIODS];"
    "print(hashlib.sha256(json.dumps(p,ensure_ascii=False,sort_keys=True)"
    ".encode('utf-8')).hexdigest())"
)


def test_golden_output_is_deterministic_across_environments(actual_by_period):
    """GB-6 — cùng fixture ⇒ cùng output, bất kể hash seed / timezone / locale.

    Chạy trong tiến trình con thật: `PYTHONHASHSEED` chỉ có hiệu lực lúc
    interpreter khởi động, nên đặt nó bằng `monkeypatch` trong cùng tiến trình
    sẽ không chứng minh được gì.
    """
    import os

    digests = set()
    snippet = _DETERMINISM_SNIPPET.format(repo=str(REPO_ROOT))
    for overrides in _DETERMINISM_ENVS:
        env = dict(os.environ)
        env.pop("TZ", None)
        env.pop("LC_ALL", None)
        env.update(overrides)
        proc = subprocess.run(
            [sys.executable, "-c", snippet],
            capture_output=True, text=True, env=env, cwd=str(REPO_ROOT), timeout=300,
        )
        assert proc.returncode == 0, proc.stderr[-2000:]
        digests.add(proc.stdout.strip())
    assert len(digests) == 1, (
        f"Golden output KHÔNG tất định: {len(digests)} digest khác nhau qua "
        f"{len(_DETERMINISM_ENVS)} môi trường -> {sorted(digests)}")


def test_golden_output_does_not_depend_on_the_working_directory(actual_by_period, tmp_path):
    """GB-6 — chạy từ một thư mục khác không đổi output.

    `run_import` mặc định `config_dir=Path("config")` (đường dẫn TƯƠNG ĐỐI).
    Golden luôn truyền `CONFIG_DIR` tuyệt đối; test này chốt rằng nó thật sự
    làm vậy.
    """
    import os

    snippet = _DETERMINISM_SNIPPET.format(repo=str(REPO_ROOT))
    proc = subprocess.run([sys.executable, "-c", snippet], capture_output=True,
                          text=True, cwd=str(tmp_path), env=dict(os.environ), timeout=300)
    assert proc.returncode == 0, proc.stderr[-2000:]
    import hashlib

    here = hashlib.sha256(
        json.dumps([actual_by_period[s["period_label"]] for s in gb.PERIODS],
                   ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    assert proc.stdout.strip() == here


# ================================= Bằng chứng E1 của phiên tạo fixture

def _raw_workbook(period: str) -> Path | None:
    """File thô production, CHỈ khi Owner cung cấp lại qua biến môi trường.

    Không có -> SKIP. Không bao giờ có đường dẫn mặc định trỏ vào repo: file
    thô không được phép tồn tại ở đó (DEC-108).
    """
    import os

    key = {"01.2026": "GOLDEN_RAW_01", "06.2026": "GOLDEN_RAW_06"}[period]
    value = os.environ.get(key)
    if not value:
        return None
    path = Path(value)
    return path if path.is_file() else None


_ALLOWED_TO_DIFFER_RAW = {"source_file", "row_hash", "note_raw", "customer",
                          "customer_code", "address", "phone", "shipper_raw", "imei"}
_ALLOWED_TO_DIFFER_LINE = {"note_raw", "customer", "customer_code", "address",
                           "phone", "shipper_raw", "imei"}


@pytest.mark.parametrize("period", PERIOD_IDS)
def test_golden_anonymization_preserves_business_output(period):
    """GB-3 — ẩn danh KHÔNG dịch chuyển nghiệp vụ. Chứng minh bằng phép đo.

    Chạy pipeline trên bản GỐC và trên fixture ĐÃ ẨN DANH rồi so **mọi** trường
    của `RawRow`/`WorkingLine`/`Order` lấy từ `dataclasses.fields()`, trừ đúng
    tập trường đã TUYÊN BỐ là bị đổi. Một danh sách trắng viết tay sẽ mù với
    trường nằm ngoài danh sách; tập trường ở đây là dẫn xuất.

    SKIP khi không có file thô — đây là bằng chứng E1 của phiên tạo fixture,
    không phải cổng CI, và file thô không bao giờ nằm trong repo.
    """
    import dataclasses

    raw_path = _raw_workbook(period)
    if raw_path is None:
        pytest.skip(f"không có workbook thô cho {period} "
                    f"(đặt GOLDEN_RAW_01/GOLDEN_RAW_06 để chạy)")

    fixture = GOLDEN_DIR / _spec(period)["fixture_filename"]
    original = run_import(raw_path, CONFIG_DIR)
    anonymized = run_import(fixture, CONFIG_DIR)

    def snap(obj, skip):
        return {f.name: (None if getattr(obj, f.name) is None
                         else str(getattr(obj, f.name)))
                for f in dataclasses.fields(obj) if f.name not in skip}

    assert len(original.orders) == len(anonymized.orders)
    assert ({o.order_id: [l.raw.source_row for l in o.lines] for o in original.orders}
            == {o.order_id: [l.raw.source_row for l in o.lines] for o in anonymized.orders})

    for a, b in zip(sorted(original.orders, key=lambda o: o.order_id),
                    sorted(anonymized.orders, key=lambda o: o.order_id)):
        assert snap(a, {"lines"}) == snap(b, {"lines"})

    la = sorted((l for o in original.orders for l in o.lines), key=lambda l: l.raw.source_row)
    lb = sorted((l for o in anonymized.orders for l in o.lines), key=lambda l: l.raw.source_row)
    assert len(la) == len(lb)
    for a, b in zip(la, lb):
        assert snap(a, {"raw"} | _ALLOWED_TO_DIFFER_LINE) == snap(b, {"raw"} | _ALLOWED_TO_DIFFER_LINE)
        assert snap(a.raw, _ALLOWED_TO_DIFFER_RAW) == snap(b.raw, _ALLOWED_TO_DIFFER_RAW)

    def queue(res):
        return sorted((i.category, i.severity, i.scope, i.order_id or "",
                       tuple(i.provenance.source_rows)) for i in res.review_queue.items)

    assert queue(original) == queue(anonymized)
