"""R5 §2 — mô hình hiển thị của bảng cờ trên trang snapshot.

Module này THUẦN: không SQL, không Flask, không đọc file. Nó nhận các cờ đã
đọc sẵn cùng một bảng tra "khoá dòng → dòng hiện hành" mà tầng route đã dựng,
rồi trả về đúng thứ template cần in ra.

## Lọc nhiễu là chuyện TRÌNH BÀY, và chỉ được là chuyện trình bày

`delivery_cost` và `imei` nằm trong `line_fingerprint` và PHẢI ở lại đó. Đó
không phải một chi tiết kỹ thuật — nó là điều kiện để một lần xuất sổ bổ sung
IMEI tạo ra một source version mới và giá trị ấy được LƯU. Bỏ chúng khỏi vân
tay sẽ làm đúng dữ liệu đó im lặng biến mất giữa hai lần nạp.

Nhưng chúng cũng không phải thứ người dùng cần soi. Một lần xuất sổ bổ sung
phí giao cho ba trăm dòng làm ba trăm mục "Nguồn đã sửa" hiện lên, và mục thứ
ba trăm lẻ một — cái đổi doanh thu thật — chìm nghỉm giữa chúng. Danh sách
cảnh báo mà không ai đọc hết thì không cảnh báo được gì.

Vì vậy ranh giới ở đây rất hẹp và được nói ra thành lời:

    fingerprint / source version / `detail_json` dưới database   KHÔNG ĐỔI
    danh sách và con số TRÊN MÀN HÌNH                             lọc `NOISE_FIELDS`

Hệ quả kiểm được: `tests/test_r5_change_list.py` khẳng định cả hai chiều —
bảng cờ trong database vẫn mang đủ hai trường, còn trang thì không hiện chúng.

## IMEI không đi qua đây

Một lý do thứ hai, độc lập với chuyện nhiễu: `imei` là dữ liệu cá nhân theo
`governance/product/17_DATA_GOVERNANCE_PRIVACY.md`, và R5 chỉ mở nó ở ĐÚNG
workspace nhân viên đã xác thực (`DEC-R5-03`). Trang snapshot không nằm trong
phạm vi đó. Nên kể cả nếu mai này ai đó quyết định `delivery_cost` đáng hiện,
`imei` vẫn phải ở lại trong danh sách này.

## Không đoán nhân viên

Một cờ là bằng chứng lịch sử; nó nói về một dòng ở thời điểm nó được dựng.
Dòng ấy hôm nay có thể đã bị Owner loại khỏi báo cáo, đã bị tạm loại vì không
còn trong sổ đã xác nhận đầy đủ, hoặc chưa bao giờ có ngày bán. Trong cả ba
trường hợp, câu trả lời ĐÚNG là nói ra rằng không còn dòng hiện hành — không
phải hiện tên người bán cuối cùng từng gắn với nó. Một cái tên sai ở đây làm
người đọc đi hỏi nhầm người.
"""

from __future__ import annotations

from typing import Optional

from app.history import models as history_models

#: Trường NGUỒN không đáng để người dùng soi. Chúng vẫn nằm trong fingerprint,
#: vẫn sinh source version, vẫn nằm trong `detail_json` — chỉ không lên màn
#: hình và không được đếm vào số "việc cần soi".
NOISE_FIELDS = frozenset({"delivery_cost", "imei"})

#: Câu cho một cờ mà dòng của nó không còn hiện hành trong kỳ nào.
NO_CURRENT_LINE = "Không còn trong kỳ hiện tại"

REVIEW_NOTE = (
    "Số “Cần soi” đếm các thay đổi nguồn có phần người dùng cần đối chiếu. "
    "Thay đổi chỉ gồm phí giao hàng hoặc mã máy không được đếm và không được "
    "liệt kê ở đây — chúng vẫn được lưu đầy đủ trong bản ghi đối chiếu."
)


def visible_changed_fields(detail_json) -> dict:
    """`detail_json` của một cờ → phần người dùng cần soi.

    Trả về `{}` khi cờ không mang diff (các cờ vắng mặt mang `scope`/khoảng
    ngày chứ không mang trường đã đổi) hoặc khi mọi trường đã đổi đều là
    nhiễu. Hai trường hợp cho ra cùng một giá trị vì chúng cho ra cùng một
    kết luận trên màn hình: không có gì để đọc ở dòng này.
    """
    if not isinstance(detail_json, dict):
        return {}
    return {name: change for name, change in detail_json.items()
            if name not in NOISE_FIELDS and isinstance(change, dict)
            and {"old", "new"} <= set(change)}


def is_noise_only(flag: dict) -> bool:
    """Cờ `SOURCE_CHANGED` mà MỌI trường đã đổi đều là nhiễu.

    Chỉ áp cho `SOURCE_CHANGED`: một cờ vắng mặt hay `ORDER_KEY_COLLISION`
    không mang diff nào, và coi "không có trường nào không nhiễu" của chúng
    là "toàn nhiễu" sẽ làm chúng biến mất khỏi màn hình — đúng những cờ mà
    người dùng cần thấy nhất.
    """
    if flag.get("kind") != history_models.OUTCOME_SOURCE_CHANGED:
        return False
    detail = flag.get("detail_json")
    if not isinstance(detail, dict) or not detail:
        return False
    return not visible_changed_fields(detail)


def review_rows(flags: list[dict], locations: dict) -> list[dict]:
    """Bảng cờ như người dùng đọc nó.

    `locations` là `{(order_key, product_key, occurrence_index): {...}}` do
    tầng route dựng từ chính effective data — nên nhân viên hiện ở đây là
    nhân viên HIỆU LỰC (đã áp mọi lần Owner gán lại), không phải tên mà
    pipeline ghi lúc chạy.

    Cờ toàn nhiễu bị bỏ khỏi danh sách; mọi cờ khác ở lại, kể cả khi không
    tra được vị trí — một cờ không có chỗ để bấm vào vẫn là một cờ.
    """
    rows = []
    for flag in flags:
        if is_noise_only(flag):
            continue
        key = (flag["order_key"], flag["product_key"], flag["occurrence_index"])
        where = locations.get(key)
        rows.append({
            "kind": flag["kind"],
            "order_key": flag["order_key"],
            "occurrence_index": flag["occurrence_index"],
            "is_active": flag.get("is_active"),
            "seen_again_in_snapshot_id": flag.get("seen_again_in_snapshot_id"),
            "changes": visible_changed_fields(flag.get("detail_json")),
            "detail_text": _detail_text(flag),
            "employee": (where or {}).get("employee") or NO_CURRENT_LINE,
            "period": (where or {}).get("period"),
            "sheet": (where or {}).get("sheet"),
            "located": where is not None,
        })
    return rows


def _detail_text(flag: dict) -> str:
    """Phần `detail_json` KHÔNG phải diff trường, viết gọn thành một dòng.

    Các cờ vắng mặt mang `scope` + khoảng ngày; in chúng nguyên dạng JSON lên
    một ô bảng là bắt người đọc tự dịch. `""` khi không có gì để nói.
    """
    detail = flag.get("detail_json")
    if not isinstance(detail, dict):
        return ""
    start, end = detail.get("range_start"), detail.get("range_end")
    if not start or not end:
        return ""
    scope = detail.get("scope")
    prefix = ("phạm vi đã xác nhận đầy đủ" if scope == "CONFIRMED"
              else "phạm vi đo được của sổ")
    return f"{prefix}: {start} → {end}"


def review_count(flags: list[dict]) -> int:
    """Số thay đổi nguồn CẦN NGƯỜI DÙNG SOI trên màn hình này.

    Cố ý KHÔNG dùng lại `snapshot.n_source_changed`: con số đó là bằng chứng
    thô của lần đối chiếu và phải giữ nguyên trong bản ghi (nó trả lời "hệ
    thống đã thấy bao nhiêu dòng đổi nguồn"). Con số ở đây trả lời một câu
    khác — "còn bao nhiêu việc cho tôi" — và hai câu đó có quyền khác nhau.
    """
    return sum(
        1 for flag in flags
        if flag.get("kind") == history_models.OUTCOME_SOURCE_CHANGED
        and not is_noise_only(flag)
    )


__all__ = [
    "NOISE_FIELDS", "NO_CURRENT_LINE", "REVIEW_NOTE", "is_noise_only",
    "review_count", "review_rows", "visible_changed_fields",
]
