"""Kế hoạch hỏi giá: sổ bán hàng → (tập mã Tracking, khoảng ngày bán) — R1.

## Vì sao capture MIN theo ngày không thể "chụp một lần dùng mãi"

Hai capture Tracking kia (`purchase_price_history`, `catalog`) là ảnh chụp của
TOÀN BỘ một nhánh dữ liệu: chụp xong thì dùng cho bất kỳ kỳ báo cáo nào.
`daily-min-v1` thì không — hợp đồng của nó nhận `product_codes` và
`date_from..date_to`, nên một ảnh chụp chỉ trả lời được đúng những cặp (mã,
ngày) mà nó đã hỏi. Chụp cho tháng 9 rồi mở lại sổ tháng 8 là hỏi một ảnh chụp
những câu nó chưa từng được hỏi.

Nên trước khi gọi hợp đồng, phải biết HỎI GÌ. Module này trả lời đúng câu ấy và
không làm gì khác: nó đọc sổ, resolve identity bằng CHÍNH resolver production,
rồi trả về tập mã Tracking đã resolve cùng ngày bán nhỏ nhất/lớn nhất.

## Nó KHÔNG tính giá, KHÔNG chạm mạng, KHÔNG ghi gì

Kế hoạch là một phép ĐỌC thuần trên workbook cộng các nguồn identity đã nạp.
Việc gọi mạng nằm ở `tools/tracking/` (`ADR-101`, `CHECK-105D-17`), và việc
tính giá nằm ở `composition.py`. Tách ra như vậy vì cùng một kế hoạch phải dùng
được cho ba đường khác nhau: pull-on-run của bản web, chọn capture cục bộ của
luồng Owner, và công cụ chụp tay.

## Dòng không resolve được KHÔNG bị đoán

Một dòng không có ngày bán, một `product_raw` rỗng, một tên hàng chưa ai nhận
diện — tất cả đều KHÔNG vào kế hoạch. Chúng đã có nhánh Pending riêng với lý do
riêng ở `composition.py`; nhét chúng vào yêu cầu ở đây chỉ làm request phình ra
mà không đổi được câu trả lời nào.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

from app.modules.importing.normalizer import normalize_lines
from app.modules.importing.raw_reader import read_raw_rows
from app.modules.product.identity.identity import Namespace
from app.modules.product.identity.resolver import (
    ProductIdentityResolver,
    Resolved,
    SalesRowRef,
)

__all__ = [
    "DailyMinRequestPlan",
    "MAX_CONTRACT_DAYS",
    "UnreadableSalesWorkbookError",
    "plan_daily_min_request",
    "plan_daily_min_request_for_workbook",
]

class UnreadableSalesWorkbookError(RuntimeError):
    """Không đọc nổi workbook để lập kế hoạch.

    Có kiểu lỗi RIÊNG vì bên gọi cần phân biệt nó với mọi lỗi khác của module
    này. Sổ không đọc được thì không lập được kế hoạch, nhưng đó KHÔNG phải
    kết luận về giá — và chính đường nhập sổ ngay sau đó sẽ đọc lại đúng file
    ấy và báo lỗi đúng chỗ, nơi người dùng hiểu được. Bắt trọn `Exception` ở
    bên gọi thì một lỗi THẬT của resolver cũng lặng lẽ thành "không có ảnh
    chụp", và cả kỳ Pending mà không ai biết vì sao.
    """


MAX_CONTRACT_DAYS = 62
"""Trần số NGÀY của một lượt gọi `daily-min-v1` — gương của `TRAN_NGAY_XUAT`
phía Tracking (`src/min-ngay.js`).

Ghi lại ở đây để một kỳ quá rộng được phát hiện TRƯỚC khi gọi mạng, và được
nói ra bằng một câu người đọc hiểu được, thay vì trở về dưới dạng
`khoang-ngay-qua-dai` từ một hệ thống khác."""


@dataclass(frozen=True)
class DailyMinRequestPlan:
    """Đúng những gì cần để gọi hợp đồng, không hơn."""

    product_codes: tuple[str, ...]
    date_from: _dt.date
    date_to: _dt.date
    #: Từng cặp (mã Tracking, ngày bán) mà lần chạy này THẬT SỰ cần trả lời.
    #: Thưa hơn tích Descartes `product_codes × [date_from, date_to]` rất
    #: nhiều: một kỳ 30 ngày với 200 mã có 6.000 ô, nhưng sổ bán hàng thường
    #: chỉ chạm vài trăm trong số đó.
    pairs: tuple[tuple[str, _dt.date], ...] = ()
    #: Số dòng đã đọc được từ sổ (có ngày bán và có tên hàng).
    lines_read: int = 0
    #: Số dòng có identity Tracking đã resolve — tức số dòng kế hoạch này phục vụ.
    tracking_lines: int = 0

    @property
    def day_span(self) -> int:
        """Số ngày của khoảng hỏi, tính cả hai đầu."""
        return (self.date_to - self.date_from).days + 1

    @property
    def fits_one_contract_call(self) -> bool:
        return self.day_span <= MAX_CONTRACT_DAYS

    def contract_windows(self) -> tuple[tuple[_dt.date, _dt.date], ...]:
        """Chia khoảng hỏi thành các đoạn vừa MỘT lượt gọi hợp đồng.

        Chia theo ngày chứ không theo mã: trần ngày (62) là trần của yêu cầu,
        còn trần mã (100) đã có phân trang lo. Các đoạn liền kề, không chồng
        lấn, phủ đúng `[date_from, date_to]`.
        """
        ra: list[tuple[_dt.date, _dt.date]] = []
        dau = self.date_from
        while dau <= self.date_to:
            cuoi = min(dau + _dt.timedelta(days=MAX_CONTRACT_DAYS - 1), self.date_to)
            ra.append((dau, cuoi))
            dau = cuoi + _dt.timedelta(days=1)
        return tuple(ra)

    def covered_by(self, snapshot: Any) -> bool:
        """Một ảnh chụp đã có sẵn có trả lời được kế hoạch này không.

        Hỏi TỪNG CẶP `(mã, ngày)`, không chỉ hai đầu khoảng ngày. Lý do: hai
        ảnh chụp của cùng một kỳ có thể được chụp cho hai TẬP MÃ khác nhau —
        một lần chụp cho sổ của nhân viên A, một lần cho sổ của nhân viên B —
        và cả hai đều "phủ khoảng ngày". Chọn nhầm thì phần lớn dòng ra
        `NOT_IN_CAPTURE`; đó là một câu trả lời trung thực, nhưng nó nói sai
        vấn đề (người đọc đi tìm hiểu dữ liệu, trong khi việc cần làm là chụp
        lại cho đúng tập mã), và nó xảy ra khi trong kho ĐANG CÓ một ảnh chụp
        trả lời được.

        "Trả lời được" ở đây là ĐÚNG bất biến cân sổ của hợp đồng: mỗi cặp đã
        hỏi nằm ở `records` HOẶC ở `errors`. Một cặp nằm ở `errors` VẪN tính là
        đã trả lời — "Tracking bảo hôm ấy không có dữ liệu" là một câu trả
        lời, và một ảnh chụp mới hơn cũng sẽ nói y như thế.
        """
        if not self.pairs:
            return bool(snapshot.covers(self.date_from) and snapshot.covers(self.date_to))
        for code, day in self.pairs:
            if not snapshot.covers(day):
                return False
            if snapshot.record_for(code, day) is None and (
                snapshot.error_for(code, day) is None
            ):
                return False
        return True


def plan_daily_min_request(
    rows: Iterable[Any],
    *,
    tracking_catalog: Any,
    identity_store_view: Any,
    tracking_inv_map: Any = None,
    tracking_identity_authority: bool = True,
    public_purchase: Any = None,
) -> Optional[DailyMinRequestPlan]:
    """Kế hoạch từ các dòng đã chuẩn hoá. `None` khi không có gì để hỏi.

    `None` KHÔNG phải một lỗi và không được đọc thành "mọi mã đều thiếu giá":
    nó nghĩa là lần chạy này không có dòng nào mang identity Tracking, nên
    không có câu hỏi nào để đặt ra. Những dòng ấy đã Pending với lý do identity
    của chính chúng.
    """
    if tracking_catalog is None or identity_store_view is None:
        # Thiếu nguồn identity thì không resolve được mã nào, và composition
        # đã có nhánh `IDENTITY_SOURCES_UNAVAILABLE` nói đúng chuyện đó. Dựng
        # một kế hoạch từ `product_raw` thô ở đây là gửi tên hàng trên chứng
        # từ sang Tracking như thể chúng là mã — đúng thứ identity tồn tại để
        # ngăn.
        return None

    eligible: list[tuple[Any, SalesRowRef]] = []
    for line in rows:
        sale_date = getattr(line, "date", None)
        raw = getattr(line, "product_raw", None)
        if sale_date is None or not isinstance(raw, str) or not raw.strip():
            continue
        eligible.append((
            line,
            SalesRowRef(
                order_id=getattr(line, "order_id", "") or "",
                sale_date=sale_date,
                raw_product_identity=raw,
            ),
        ))
    if not eligible:
        return None

    resolutions = ProductIdentityResolver(
        tracking_snapshot=tracking_catalog,
        pp_version=public_purchase,
        store_view=identity_store_view,
        tracking_identity_authority=tracking_identity_authority,
        inv_map_snapshot=tracking_inv_map,
    ).resolve_all(tuple(ref for _, ref in eligible))

    tracking_codes: dict[str, None] = {}
    by_key: dict[str, str] = {}
    for resolution in resolutions:
        outcome = resolution.outcome
        if not isinstance(outcome, Resolved):
            continue
        identity = outcome.identity
        if identity.namespace is not Namespace.TRACKING:
            continue
        by_key[resolution.identity.raw_identity_key] = identity.source_product_code
        tracking_codes[identity.source_product_code] = None

    if not tracking_codes:
        return None

    days: list[_dt.date] = []
    pairs: dict[tuple[str, _dt.date], None] = {}
    for _, ref in eligible:
        code = by_key.get(ref.raw_identity_key)
        if code is None:
            continue
        days.append(ref.sale_date)
        pairs[(code, ref.sale_date)] = None
    return DailyMinRequestPlan(
        product_codes=tuple(sorted(tracking_codes)),
        date_from=min(days),
        date_to=max(days),
        pairs=tuple(sorted(pairs)),
        lines_read=len(eligible),
        tracking_lines=len(days),
    )


def plan_daily_min_request_for_workbook(
    sales: Path, **sources: Any
) -> Optional[DailyMinRequestPlan]:
    """Cùng phép trên, đọc thẳng từ workbook kế toán.

    Đọc lại workbook một lần nữa là cái giá phải trả để biết HỎI GÌ trước khi
    gọi mạng, và nó rẻ hơn nhiều so với hai đường vòng còn lại: chạy cả
    pipeline hai lượt, hoặc gọi hợp đồng một lượt cho mỗi dòng bán.
    """
    try:
        raw_rows = read_raw_rows(Path(sales))
    except Exception as exc:  # noqa: BLE001 — mọi lỗi ĐỌC FILE đều là một câu
        raise UnreadableSalesWorkbookError(
            f"Không đọc được workbook để lập kế hoạch hỏi giá: "
            f"{type(exc).__name__}"
        ) from exc
    return plan_daily_min_request(normalize_lines(raw_rows), **sources)
