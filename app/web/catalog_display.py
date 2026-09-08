"""R5 §5 — bản chiếu HIỂN THỊ của danh mục Tracking: mã → model + hãng.

Module này tồn tại để trả lời đúng một câu trên màn hình nhân viên: *dòng
này, sau khi đã được phân loại, là model gì và của hãng nào?* Và nó tồn tại
theo cách nhỏ nhất có thể trả lời được câu đó.

## Vì sao KHÔNG đọc thẳng danh mục ở mỗi lần tải trang

`server._tracking_snapshot()` nói rõ vì sao nó chỉ được gọi khi Owner thật sự
mở bảng chọn của MỘT dòng: một lần pull live giữ authority thô của Tracking
trên đĩa máy chủ, và `S071` §10 bắt dọn nó ngay sau khi dùng. Gọi nó cho mọi
lần render bảng kê là biến một ngoại lệ có kiểm soát thành thói quen — và
thành một lần gọi mạng cho mỗi lần bấm.

Vì vậy R5 ghi lại ĐÚNG hai trường hiển thị mỗi khi một lần pull đã được cho
phép xảy ra vì một lý do khác, rồi đọc lại từ file đó. Không lần gọi mạng
nào được thêm vào.

## Đây KHÔNG phải một bảng danh mục của Reports

Ba ranh giới, và cả ba là ranh giới của `PHB-06 §3`/`BR-02`/`BR-10`:

1. Nó chỉ chứa những gì Tracking ĐÃ NÓI. Không dòng nào được suy ra, và
   không có đường ghi tay nào vào file này.
2. Nó KHÔNG tham gia nhận diện. `TrackingCatalogSnapshot._match_field` không
   đọc `model_label`/`brand`, và module này không được gọi từ bất kỳ đường
   resolve nào — nó chỉ đi vào tầng trình bày.
3. Nó KHÔNG phải nguồn sự thật. Mất file (deploy mới, đĩa ephemeral) ⟹ màn
   hình hiện TÊN THÔ và "chưa xác định" — đúng trạng thái mà một hệ thống
   chưa biết hãng phải hiện. Không nhánh nào đoán bù.

Điểm 3 là lý do file này được phép sống trên đĩa ephemeral: cái giá của việc
mất nó là một màn hình nói ít đi, không phải một màn hình nói sai.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

#: Cùng thư mục với log quyết định Product Identity — cùng vòng đời, và cùng
#: một chỗ để tìm khi cần dọn.
DEFAULT_DISPLAY_PATH = Path("data/product_identity/tracking_display.json")


def rows_of(snapshot) -> dict:
    """`{tracking_code: {"model_label", "brand"}}` cho các dòng CÓ ít nhất
    một trong hai trường. Dòng không có gì để nói thì không chiếm chỗ."""
    if snapshot is None:
        return {}
    out = {}
    for row in getattr(snapshot, "rows", ()):
        if row.model_label is None and row.brand is None:
            continue
        out[row.tracking_code] = {"model_label": row.model_label,
                                  "brand": row.brand}
    return out


def write(snapshot, path: Optional[Path] = None) -> None:
    """Ghi bản chiếu hiển thị. Lỗi ghi KHÔNG được làm hỏng lần gọi đang chạy.

    Đây là một tác dụng phụ tiện ích của một thao tác khác (mở bảng chọn, chạy
    báo cáo). Nếu nó thất bại, thứ duy nhất mất đi là vài cái nhãn — biến điều
    đó thành một trang lỗi sẽ đánh đổi một tính năng chính lấy một tính năng
    phụ.
    """
    target = Path(path or DEFAULT_DISPLAY_PATH)
    rows = rows_of(snapshot)
    if not rows:
        return
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(rows, ensure_ascii=False, sort_keys=True),
            encoding="utf-8")
    except OSError:
        return


def read(path: Optional[Path] = None) -> dict:
    """Bản chiếu đã ghi, hoặc `{}`.

    Mọi hư hỏng đều cho ra `{}` — file chưa có, JSON hỏng, kiểu sai. Cả ba
    dẫn tới cùng một màn hình: tên thô và "chưa xác định". Phân biệt chúng ở
    đây sẽ tạo ra ba nhánh mà không nhánh nào đổi được điều người dùng thấy.
    """
    target = Path(path or DEFAULT_DISPLAY_PATH)
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    out = {}
    for code, value in payload.items():
        if not isinstance(code, str) or not isinstance(value, dict):
            continue
        model = value.get("model_label")
        brand = value.get("brand")
        out[code] = {
            "model_label": model if isinstance(model, str) and model else None,
            "brand": brand if isinstance(brand, str) and brand else None,
        }
    return out


def brand_source(display: dict):
    """`BrandSource` của PHB-06 đọc từ bản chiếu này — mở lại `PHB-06` CÓ CHỦ ĐÍCH.

    `brand_identity.canonical_brand` đọc trường `brand` TRÊN chính danh tính,
    và hợp đồng danh tính hôm nay vẫn không có trường đó (`INV-18`: so sánh
    LUÔN bằng đủ tuple — thêm một trường hiển thị vào value object sẽ làm hai
    danh tính cùng mã khác hãng thành hai danh tính KHÁC NHAU). Nên R5 đi
    đường thứ hai mà `PHB-06 §4` đã để ngỏ: một read model canonical tương
    đương, cắm vào đúng tham số `brand_source` đã có sẵn.

    Không có bảng brand nào của riêng Reports được tạo ra: bảng chiếu này chỉ
    chứa những gì Tracking đã nói, và hàm này chỉ tra `source_product_code`.
    """
    def source(identity) -> Optional[str]:
        if identity is None:
            return None
        code = getattr(identity, "source_product_code", None)
        if not code:
            return None
        return (display.get(code) or {}).get("brand")
    return source


def label_of(display: dict, code: Optional[str]) -> Optional[str]:
    """Model canonical của một mã, hoặc `None`.

    `None` KHÔNG có nghĩa "dùng mã": tầng gọi tự quyết định fallback, và câu
    trả lời của R5 §5 cho dòng ĐÃ phân loại là fallback về chính mã Tracking
    — một mã đối chiếu được vẫn hơn một ô trống.
    """
    if not code:
        return None
    return (display.get(code) or {}).get("model_label")


__all__ = ["DEFAULT_DISPLAY_PATH", "brand_source", "label_of", "read",
           "rows_of", "write"]
