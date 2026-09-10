from __future__ import annotations

from pathlib import Path

import pytest

from tests.fixtures.legacy.build_legacy_workbook import build_legacy_workbook
from tests.fixtures.synthetic_workbook import build_synthetic_workbook

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "config"


@pytest.fixture
def synthetic_raw_path(tmp_path: Path) -> Path:
    path = tmp_path / "synthetic_raw_sample.xlsx"
    build_synthetic_workbook(path)
    return path


@pytest.fixture
def config_dir() -> Path:
    return CONFIG_DIR


@pytest.fixture
def legacy_workbook_path(tmp_path: Path) -> Path:
    """Workbook legacy tổng hợp (anonymized) có cài sẵn A1/A2/A4/A6."""
    return build_legacy_workbook(tmp_path / "bao_cao_kinh_doanh_fixture.xlsx")


@pytest.fixture
def history_engine():
    """Engine SQLite trong bộ nhớ đã dựng schema — không chạm filesystem."""
    from sqlalchemy import create_engine

    import tools.db as history_db

    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


@pytest.fixture
def legacy_repository(history_engine):
    from app.web import history_store

    return history_store.build(engine=history_engine)


@pytest.fixture(autouse=True)
def _chart_gapfill_disconnected(request, monkeypatch):
    """`DEC-216` — nguồn lấp lỗ hổng KHÔNG tự nối vào workspace của test.

    `data/chart_gapfill/daily_revenue.jsonl` là dữ liệu THẬT của một doanh
    nghiệp cụ thể, đã commit, và `chart_gapfill.daily_rows()` đọc nó theo
    đường dẫn tuyệt đối tính từ gốc repo. Không có fixture này thì mọi test
    dựng một workspace tổng hợp sẽ âm thầm nhận thêm 579 ngày doanh số thật
    vào biểu đồ của nó — và mệnh đề mà test ấy nói ra ("tháng 7 không sinh ra
    ngày nào") sẽ hỏng vì một lý do chẳng liên quan gì tới nó.

    Đây KHÔNG phải một cách làm nhẹ test: nó cắt một nguồn NGOÀI khỏi
    workspace tổng hợp, đúng kỷ luật mà `app/pipeline.py` đã đặt ("DI mặc
    định không nối gì"). Đường dây thật vẫn có test riêng —
    `tests/test_dec216_chart_gapfill.py` bật lại nguồn này bằng marker
    ``chart_gapfill`` và kiểm từ file đã commit ra tới HTML.
    """
    if request.node.get_closest_marker("chart_gapfill") is not None:
        return
    from app.web import chart_gapfill

    monkeypatch.setattr(
        chart_gapfill, "GAPFILL_DAILY_PATH",
        Path(__file__).resolve().parent / "_khong_ton_tai_chart_gapfill.jsonl")
