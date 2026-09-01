"""S071B follow-up — Render production regression (AUTO 22 → 0 trên cùng
workbook đã accepted ở S068).

Root cause: `Dockerfile` chỉ `COPY app`, `tools`, `config` — không `COPY
data` — nên các nguồn "canonical committed" mà
`app/composition.py::run_import_production()` nạp KHÔNG ĐIỀU KIỆN
(`CONFIRMED_ADJUSTMENTS_PATH`, `HISTORICAL_REGISTRY_PATH`) vắng mặt trong
container production. `confirmed_adjustments.jsonl` vắng mặt (khác "tồn
tại nhưng rỗng") khiến `ConfirmedAdjustmentSource` là UNAVAILABLE
(`app/modules/adjustment/confirmed_adjustment_source.py`, DEC-144 §3 —
"absence ≠ unknown ≠ zero") thay vì LOADED-rỗng như checkout local — và
UNAVAILABLE khiến `kpi_purchase_price`/`eligible_kpi_profit` mất trên MỌI
dòng (`app/modules/kpi/kpi_profit_engine.py`), không chỉ những dòng vốn đã
Pending vì thiếu giá — nên order nào cũng thành Review, AUTO = 0.

Đây không phải business logic thay đổi — `confirmed_adjustment_source.py`
hành xử đúng thiết kế (đã có test riêng ở `tests/test_kpi_profit_engine.py`
cho từng trạng thái UNAVAILABLE/LOADED-rỗng/CONFIRMED). Bug nằm ở tầng
đóng gói: file cần thiết không được đưa vào build context Docker, cùng
lớp lỗi với S071B packaging repair trước đó (setuptools).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app import composition
from app.modules.adjustment.confirmed_adjustment_source import (
    load_confirmed_adjustments_from_jsonl,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCKERFILE = REPO_ROOT / "Dockerfile"


def _dockerfile_copy_top_level_dirs() -> set[str]:
    """Tên thư mục top-level ở vế nguồn của mỗi lệnh `COPY <src> <dst>` —
    đúng cách Dockerfile build context này hoạt động (mọi COPY đều lấy một
    thư mục top-level của repo, xem Dockerfile hiện tại)."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    srcs = re.findall(r"(?m)^COPY\s+(\S+)\s+\S+", text)
    return {src.split("/")[0] for src in srcs if src != "pyproject.toml"}


@pytest.mark.parametrize(
    "canonical_path",
    [composition.HISTORICAL_REGISTRY_PATH, composition.CONFIRMED_ADJUSTMENTS_PATH],
    ids=["historical_confirmed_registry", "confirmed_adjustments"],
)
def test_dockerfile_copies_the_directory_of_every_canonical_committed_source(
    canonical_path: Path,
):
    """`run_import_production()` nạp các nguồn này KHÔNG ĐIỀU KIỆN (docstring
    app/composition.py: "nạp các nguồn canonical từ đường dẫn cố định trong
    repo"). Nếu Dockerfile không COPY đúng thư mục top-level chứa chúng,
    production khởi động với input khác hẳn checkout local đã accepted —
    một gap packaging, không phải một quyết định nghiệp vụ."""
    top_level_dir = canonical_path.parts[0]
    assert top_level_dir in _dockerfile_copy_top_level_dirs(), (
        f"Dockerfile không COPY '{top_level_dir}/' — {canonical_path} sẽ "
        "vắng mặt trong container production."
    )


def test_canonical_committed_data_files_actually_exist_in_the_checkout():
    """Sanity ngược: nếu ai đó xoá file thật mà không cập nhật giả định
    trên, test packaging ở trên sẽ pass giả — khẳng định file thật có mặt."""
    assert (REPO_ROOT / composition.HISTORICAL_REGISTRY_PATH).is_file()
    assert (REPO_ROOT / composition.CONFIRMED_ADJUSTMENTS_PATH).is_file()


def test_missing_confirmed_adjustments_file_is_unavailable_not_loaded_empty():
    """Mô phỏng ĐÚNG trạng thái container production trước repair: file
    hoàn toàn vắng mặt (không phải tồn tại-nhưng-rỗng) → UNAVAILABLE."""
    missing_path = REPO_ROOT / "data" / "does-not-exist" / "confirmed_adjustments.jsonl"
    assert not missing_path.exists()
    source = load_confirmed_adjustments_from_jsonl(missing_path)
    assert source.is_available is False


def test_real_committed_confirmed_adjustments_file_loads_as_available():
    """File thật đã commit (rỗng, 0 record) phải là LOADED-rỗng
    (`is_available=True`) — đúng trạng thái checkout local S068 đã dùng khi
    baseline có 22 AUTO order. Nếu test này PASS nhưng production vẫn cho
    UNAVAILABLE, nguyên nhân chắc chắn nằm ở việc container không có file
    này trên đĩa (đúng root cause ở trên), không phải logic loader."""
    source = load_confirmed_adjustments_from_jsonl(
        REPO_ROOT / composition.CONFIRMED_ADJUSTMENTS_PATH
    )
    assert source.is_available is True
    assert source.lookup("BH-any-order") is None  # LOADED rỗng — determined absence
