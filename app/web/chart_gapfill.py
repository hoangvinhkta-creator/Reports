"""`DEC-216` — doanh số TỪNG NGÀY dùng RIÊNG để lấp lỗ hổng của biểu đồ.

## Vì sao tồn tại một nguồn thứ ba

Owner mở trang Báo cáo ở mức Ngày và thấy đường "Cùng kỳ năm trước" trống
trơn (`DEC-215`). Lý do là thật và đã được xác minh: sổ cũ năm 2025 chỉ có
TỔNG THÁNG. `app/legacy/parser.py::parse_year_workbook` trả
``daily_sales=[]`` — 74 sheet chi tiết của năm 2025 được ghi tên nhưng KHÔNG
đọc một ô nào, theo `LEGACY_LINE_DETAIL_2025 = DEFERRED`
(`governance/product/17_DATA_GOVERNANCE_PRIVACY.md`: các sheet ấy chứa tên,
số điện thoại và địa chỉ khách hàng). Và `§CHART-10` cấm tuyệt đối việc chia
một tổng tháng ra thành ngày — "một tổng tháng không sinh ra ngày nào".

Nên chỗ trống ấy KHÔNG thể lấp bằng dữ liệu đang có trong hệ thống, và cũng
không thể lấp bằng cách nới `DEC-181` (`OWNER_DECISION`, đã freeze: lịch sử
khoá ở đúng hai file nguồn, "Không thêm nguồn legacy nào nữa").

Owner chốt một đường thứ ba, bằng lời của chính Owner: *"đi đường vòng: đọc
và xử lí trước số liệu file thô trong session này, sau đó dùng số liệu đó
(ngày + doanh số ngày) tạo thành 1 data không phải legacy, chỉ phục vụ cho
việc vẽ lấp lỗ hổng biểu đồ"*.

Module này là nguồn đó. Ba tính từ trong câu trên là ba ràng buộc, và cả ba
đều thi hành được:

``không phải legacy``
    Không đụng bảng `legacy_*`, không đi qua `POST /du-lieu/legacy` (vẫn trả
    409 vô điều kiện), không xuất hiện trong `legacy_reference`. Nó mang
    origin RIÊNG — `ORIGIN_GAPFILL` — chứ không mượn nhãn `LEGACY_REFERENCE`.
    Mượn nhãn sẽ làm hỏng đúng chiều mà `DEC-166 E` bắt luôn phải đọc được.

``chỉ phục vụ việc vẽ``
    Bề mặt DUY NHẤT gọi tới đây là biểu đồ (`revenue_timeline.series` qua
    `gapfill_days`). KPI, bảng kê, bảng nhân viên, đối soát số cũ — không
    đường nào đọc module này, và có test giữ điều đó.

``lấp lỗ hổng``
    Một ngày chỉ nhận giá trị ở đây khi KHÔNG nguồn nào khác nói về nó. Thứ
    tự thẩm quyền là sổ nạp → sổ cũ → lấp lỗ hổng, và nó được giải ở ĐÚNG mức
    NGÀY (`revenue_timeline._gapfill_day_points`). `DEC-180` §9 không bị nới:
    một ngày vẫn chỉ có MỘT nguồn và MỘT giá trị.

## Con số này từ đâu ra, và nó KHÔNG phải cái gì

Số liệu được trích trong phiên làm việc từ hai workbook kế toán của Owner,
CHỈ hai cột `Date` và `Tổng bán` — không đọc, không lưu, không in bất kỳ ô
nào chứa dữ liệu cá nhân khách hàng. Toàn bộ luật trích xuất, các bất thường
đã gặp và quyết định của Owner về từng bất thường nằm ở
`data/chart_gapfill/PROVENANCE.md`.

Nó KHÔNG phải một định nghĩa doanh thu thứ hai và KHÔNG được dùng để đối
soát: `legacy_reference.authoritative_period_sales` vẫn là thẩm quyền duy
nhất cho tổng một kỳ số cũ. Ở mức Tháng/Quý/Năm biểu đồ đã có tổng tháng
chính thức nên module này KHÔNG được gọi — thêm nó vào đó là cộng hai nguồn
cho cùng một tháng, đúng thứ `_merge_resolved` sinh ra để chặn.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path
from typing import Optional

#: Gốc repo, suy từ vị trí CHÍNH file này (`app/web/…` → lên hai bậc).
#: `app/composition.py` dùng đường dẫn tương đối vì nó chạy từ gốc repo; route
#: web thì không có bảo đảm ấy — trên Render thư mục làm việc do nền tảng đặt,
#: và một đường dẫn tương đối ở đây sẽ âm thầm "không tìm thấy file" rồi trả
#: về tuple rỗng, tức là biểu đồ mất đường so sánh mà không báo gì.
_REPO_ROOT = Path(__file__).resolve().parents[2]

#: Nguồn canonical đã commit, đường dẫn cố định trong repo — cùng hạng với
#: `HISTORICAL_REGISTRY_PATH` trong `app/composition.py`.
GAPFILL_DAILY_PATH = _REPO_ROOT / "data" / "chart_gapfill" / "daily_revenue.jsonl"

#: Đơn vị của cột `sales_vnd` trong file: VND NGUYÊN, đã nhân sẵn 1.000 từ
#: đơn vị nghìn đồng của sổ kế toán. Ghi ra ở đây vì `revenue_timeline` cố ý
#: không đổi đơn vị: "quên hệ số 1.000 một lần sẽ cho ra một đường cong trông
#: như thật".
FIELD_SALES = "sales_vnd"
FIELD_DATE = "date"


def _parse_row(raw: str, line_no: int) -> dict:
    try:
        row = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{GAPFILL_DAILY_PATH}:{line_no} không phải JSON hợp lệ") from exc
    if not isinstance(row, dict):
        raise ValueError(f"{GAPFILL_DAILY_PATH}:{line_no} phải là một object")
    try:
        when = date.fromisoformat(str(row[FIELD_DATE]))
    except (KeyError, ValueError) as exc:
        raise ValueError(
            f"{GAPFILL_DAILY_PATH}:{line_no} thiếu hoặc sai trường "
            f"{FIELD_DATE!r}") from exc
    try:
        sales = Decimal(str(row[FIELD_SALES]))
    except (KeyError, InvalidOperation) as exc:
        raise ValueError(
            f"{GAPFILL_DAILY_PATH}:{line_no} thiếu hoặc sai trường "
            f"{FIELD_SALES!r}") from exc
    if sales < 0:
        raise ValueError(
            f"{GAPFILL_DAILY_PATH}:{line_no} doanh số âm ({sales}) — một ngày "
            "bán hàng không có doanh số âm; đây là lỗi trích xuất, không phải "
            "một sự thật kinh doanh")
    return {"year": when.year, "month": when.month, "day": when.day,
            "sales_vnd": sales}


def load_daily_rows(path: Optional[Path] = None) -> tuple[dict, ...]:
    """Các dòng `{"year", "month", "day", "sales_vnd"}` đã sắp theo ngày.

    File VẮNG MẶT trả về tuple RỖNG chứ không nổ: nguồn này là một lớp lấp
    lỗ hổng của phần TRÌNH BÀY, và mất nó phải làm biểu đồ trở về đúng hình
    dạng trước `DEC-216` — có lỗ hổng — chứ không được làm sập trang Báo cáo.

    File CÓ MẶT nhưng hỏng thì NỔ: một dòng sai định dạng mà bị bỏ qua trong
    im lặng sẽ vẽ ra một đường thấp hơn sự thật và không ai nhìn ra được.
    """
    source = Path(path) if path is not None else GAPFILL_DAILY_PATH
    if not source.exists():
        return ()
    rows: dict[date, dict] = {}
    with source.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            row = _parse_row(raw, line_no)
            when = date(row["year"], row["month"], row["day"])
            if when in rows:
                raise ValueError(
                    f"{source}:{line_no} ngày {when.isoformat()} xuất hiện hai "
                    "lần — một ngày phải có đúng một giá trị (DEC-180 §9)")
            rows[when] = row
    return tuple(rows[when] for when in sorted(rows))


@lru_cache(maxsize=4)
def _cached(source: str) -> tuple[dict, ...]:
    return load_daily_rows(Path(source))


def daily_rows(path: Optional[Path] = None) -> tuple[dict, ...]:
    """Bản đã cache của `load_daily_rows` — file này là hằng số đã commit.

    Đọc lại nó ở mỗi lần tải trang là một lần I/O lặp lại cho một nội dung
    không đổi giữa hai lần deploy. `load_daily_rows` vẫn công khai để test
    đọc một file cụ thể mà không chạm vào cache.
    """
    return _cached(str(Path(path) if path is not None else GAPFILL_DAILY_PATH))


__all__ = ["FIELD_DATE", "FIELD_SALES", "GAPFILL_DAILY_PATH", "daily_rows",
           "load_daily_rows"]
