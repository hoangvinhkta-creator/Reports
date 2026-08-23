"""Air-conditioner classification on `ProductRaw` (DEC-125 điểm 2–3).

`KHBH`/`Thợ lắp` chỉ có số tiền đề xuất mặc định khi sản phẩm là điều hòa —
file thô ghi rõ chữ "điều hòa" ngay trước mã model, nên dò trực tiếp trên
`ProductRaw` bằng khớp từ khóa là đủ, không cần bảng ProductCode (đã xác nhận
khả thi trên dữ liệu thật tháng 01/2026, 06/2026 — xem DEC-125).

Không dùng viết tắt mơ hồ (`ĐH`) làm từ khóa để tránh false positive — chỉ
khớp các cụm từ được viết ra rõ ràng, cấu hình ở `config/adjustments.yaml`.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Optional

from app.modules.config.loader import load_yaml


def _normalize(value: Optional[str]) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFC", str(value))
    return re.sub(r"\s+", " ", text).strip()


class AirConditionerClassifier:
    def __init__(self, keywords: tuple[str, ...]):
        self._keywords = tuple(_normalize(keyword).upper() for keyword in keywords)

    @classmethod
    def from_yaml(cls, path: Path) -> "AirConditionerClassifier":
        data = load_yaml(path)
        return cls(keywords=tuple(data.get("air_conditioner_keywords", [])))

    def is_air_conditioner(self, product_raw: Optional[str]) -> bool:
        text = _normalize(product_raw).upper()
        if not text:
            return False
        return any(keyword in text for keyword in self._keywords)
