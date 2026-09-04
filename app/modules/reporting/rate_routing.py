"""PHB-03 — tỉ lệ quy đổi HIỆU LỰC của một dòng, sau tick Gia dụng của Owner.

Module này KHÔNG phải một authority tỉ lệ thứ hai. Bảng tỉ lệ vẫn là
`config/conversion_rates.yaml` và bộ phân giải vẫn là
`ConversionSchemeResolver` (ADR-104/ADR-106, DEC-127) — nguyên vẹn. Việc duy
nhất ở đây là: khi Owner đã TICK một mặt hàng là `GIA_DUNG`, hỏi lại đúng bộ
phân giải đó với chiều `product_group` mới.

## Vì sao hỏi lại lúc ĐỌC thay vì chạy lại pipeline

`conversion_rate_final` được pipeline ghi lúc import, khi `ProductGroupProvider`
còn trả `None` cho mọi dòng (`DefaultProductGroupProvider`, ADR-106 §6). Một
tick Gia dụng xảy ra SAU đó, trên dữ liệu đã nạp. Hai đường khả dĩ:

- chạy lại pipeline ⟹ Owner phải nạp lại sổ mỗi lần tick một mặt hàng;
- hỏi lại bộ phân giải lúc dựng báo cáo ⟹ tick có hiệu lực ngay, và tỉ lệ
  vẫn do đúng một authority quyết định.

Đường thứ hai được chọn. Nó KHÔNG sửa `conversion_rate_final` đã lưu: giá trị
đó là kết quả của lần chạy đó và vẫn là bằng chứng của lần chạy đó.

## Hiệu lực theo NGÀY CỦA ĐƠN, không phải "hôm nay"

`rate_for` truyền `as_of = sale_date` xuống resolver, đúng `DEC-121`: chạy lại
báo cáo tháng 01/2026 sau khi tỉ lệ 2027 đã có hiệu lực vẫn phải ra con số của
tháng 01/2026.

## Ranh giới Gia dụng tự nó giữ mình

`DEC-PHB02-05` giới hạn 8 % cho riêng nhóm `NOI_THANH` (Vinh · Quý · Hiệp).
Ranh giới đó KHÔNG được canh bằng một câu `if` ở đây — nó là CẤU TRÚC của
chính bảng cấu hình: dòng `GIA_DUNG_8` khoá trên `employee_group: NOI_THANH`,
nên một nhân viên bán lẻ có dòng hàng được tick `GIA_DUNG` vẫn khớp đúng dòng
phổ quát `* + PERSONAL + *` và ra 5,5 %. Một nhân viên bán lẻ vì thế KHÔNG
BAO GIỜ đi qua 8 % được, kể cả khi mặt hàng đã bị tick (vector nghiệm thu L/M).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

from app.modules.conversion.scheme_resolver import ConversionSchemeResolver

# Nhóm nhân viên DUY NHẤT mà `DEC-PHB02-05` cho phép định tuyến qua 8 %, và
# vì vậy là nhóm DUY NHẤT được thấy giao diện tick Gia dụng. Hằng số này chỉ
# điều khiển việc PHƠI BÀY luồng đó ra UI; nó không tham gia tính tỉ lệ.
GIA_DUNG_ELIGIBLE_GROUP = "NOI_THANH"

GIA_DUNG = "GIA_DUNG"
DIEN_MAY = "DIEN_MAY"


class ConversionRateRouter:
    """Bọc `ConversionSchemeResolver` đúng một lớp mỏng, không thêm luật."""

    def __init__(self, resolver: ConversionSchemeResolver) -> None:
        self._resolver = resolver

    @classmethod
    def from_yaml(cls, path: Path) -> "ConversionRateRouter":
        return cls(ConversionSchemeResolver.from_yaml(path))

    @property
    def default_product_group(self) -> str:
        return self._resolver.default_product_group

    def rate_for(
        self,
        *,
        stored_rate: Optional[Decimal],
        classified_group: Optional[str],
        employee: Optional[str],
        employee_group: Optional[str],
        lead_source: Optional[str],
        sale_date: Optional[date],
    ) -> Optional[Decimal]:
        """Tỉ lệ hiệu lực của một dòng.

        `classified_group is None` (Owner chưa tick mặt hàng này) ⟹ trả NGUYÊN
        `stored_rate` mà pipeline đã ghi. Không tính lại: kết quả của lần chạy
        đó là bằng chứng của lần chạy đó, và tính lại sẽ âm thầm áp cấu hình
        HÔM NAY lên một con số đã phát hành.

        Có tick ⟹ hỏi lại resolver với `product_group` mới. Dòng chưa xác định
        được người bán vẫn trả `None` (Unresolved) đúng như `DEC-127` §8 —
        không có tỉ lệ nào được sinh ra cho một dòng chưa biết ai bán.
        """
        if classified_group is None:
            return stored_rate
        resolution = self._resolver.resolve_auto(
            employee=employee,
            employee_group=employee_group,
            lead_source=lead_source,
            product_group=classified_group,
            as_of=sale_date,
        )
        return resolution.rate


def gia_dung_workflow_applies(employee_group: Optional[str]) -> bool:
    """`DEC-PHB02-05` — chỉ nhóm Nội thành được thấy luồng tick Gia dụng.

    "KHÔNG hiện và KHÔNG bắt buộc luồng đó với nhân viên bán lẻ thường" là một
    yêu cầu về TRÌNH BÀY, nên nó sống ở đây và được UI hỏi, chứ không lẫn vào
    phép tính tỉ lệ.
    """
    return employee_group == GIA_DUNG_ELIGIBLE_GROUP


__all__ = [
    "ConversionRateRouter", "DIEN_MAY", "GIA_DUNG", "GIA_DUNG_ELIGIBLE_GROUP",
    "gia_dung_workflow_applies",
]
