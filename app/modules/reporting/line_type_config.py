"""R3 §2 — nạp từ vựng loại dòng từ `config/line_types.yaml`.

Module RIÊNG, và một dòng lý do cho việc tách: `line_type.py` là ngữ nghĩa
THUẦN và `test_business_boundaries` canh cho `business_metrics` chỉ được import
những module thuần. Đặt `yaml`/`pathlib` cạnh `classify()` sẽ kéo tầng đọc file
vào đúng chỗ mà hàng rào đó tồn tại để giữ sạch.

Ranh giới vì thế là: ngữ nghĩa ở `line_type.py`, I/O ở đây, và chỉ tầng dịch vụ
(`app/web/business_service.py`) gọi module này.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from app.modules.reporting.line_type import LineTypeVocabulary


def load_vocabulary(path: Path) -> LineTypeVocabulary:
    """Nạp `config/line_types.yaml`. File hỏng ⟹ NỔ, không im lặng.

    Không có nhánh "thiếu file thì coi mọi dòng là hàng bán": mặc định đó sẽ
    làm luật giá nhập 0 theo chính sách BIẾN MẤT trong im lặng, và cả kỳ quay
    lại tình trạng không bao giờ đạt 100 % coverage mà không ai biết vì sao.
    Tầng gọi bắt lỗi này và biến nó thành một câu nói được cho Owner.
    """
    with open(path, "r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{path} không phải một ánh xạ YAML.")
    return LineTypeVocabulary.of(
        document_prefixes=raw.get("document_prefixes") or {},
        fee_keywords=raw.get("fee_keywords") or (),
        discount_keywords=raw.get("discount_keywords") or (),
    )



__all__ = ["load_vocabulary"]
