"""`API-01`/`API-02` — payload JSON của MỘT đơn, và của một lần PATCH.

Vì sao module này tồn tại, bằng con số đo được: mở chế độ sửa một đơn hiện
trả ~14,5 MB HTML với fixture 5.000 dòng, vì nó dựng lại CẢ bảng kê. Ngân
sách của brief §6 cho chi tiết một đơn là **dưới 50 KB**.

## Ranh giới cứng: module này KHÔNG tính một con số nào

Mọi giá trị ở đây đọc từ `PeriodData` mà `BusinessReportService.period()`
đã dựng — cùng đối tượng, cùng đường, cùng `Decimal` mà bảng HTML đang
hiển thị. Không có phép cộng, phép chia, phép làm tròn hay phép chọn nguồn
giá nào trong file này. Đó là điều kiện để một API mới KHÔNG trở thành một
thẩm quyền nghiệp vụ thứ hai (`§28` cấm dựng thẩm quyền giá nhập thứ hai,
và cùng lý lẽ áp cho mọi con số khác).

## Tiền được truyền như thế nào, và vì sao có HAI trường

Mỗi ô tiền là một đối tượng HAI trường, không một số:

    {"value": "8000000", "text": "8.000"}

    `value`  chuỗi thập phân CHÍNH XÁC, để so sánh, để gửi lại, để kiểm —
             không bao giờ là JSON number.
    `text`   chữ ĐÃ ĐỊNH DẠNG do server dựng (nghìn đồng), để hiển thị.

Hai trường chứ không một, vì brief §3 cấm browser tự làm tròn số chính
thức và §8 đòi phân biệt `null` với `0`. Một JSON number sẽ đi qua
`double` của JavaScript và mất chính xác ở những con số lớn nhất; một
chuỗi đã định dạng sẵn thì không so sánh được.

`null` ⟹ `{"value": null, "text": "—"}`. Đây KHÔNG phải `0`, và đó là toàn
bộ điểm: `value` là `null` nên mọi phép so sánh của client thấy "chưa có
giá trị", và `text` là dấu gạch nên mắt người đọc cũng thấy đúng điều đó.
Một `0` ở đây là một con số trông hợp lệ cho một ô chưa có dữ liệu.

Đơn vị hiển thị là NGHÌN ĐỒNG, đúng `DEC-212`, và nó được lấy qua chính
`business_presentation.money_kvnd` mà bảng đang dùng — không có phép chia
1.000 thứ hai trong file này.

## Những gì KHÔNG có trong payload, và vì sao từng thứ

`imei` — `DEC-R5-03` nói mã máy chỉ tồn tại ở đúng một route
(`business_employee`, qua `workspace_imei`), và một endpoint JSON mới là
đúng chỗ mà ranh giới ấy sẽ bị nới ra nếu không ai nói không.

`brand`/`category_label` — hai cột HIỂN THỊ của bảng kê, dựng từ bản chiếu
danh mục Tracking qua `line_identity` + `_catalog_labels()`. Panel sửa đơn
không cần chúng để sửa gì (nó sửa giá nhập và nhân viên), và lấy chúng vào
đây sẽ buộc endpoint này phải dựng lại cả đường danh tính — tức là dựng
một bản thứ hai của một logic đã có, để hiển thị hai ô mà bảng phía sau
panel đang hiện rồi.

`tags` hiển thị — chúng được dẫn xuất từ chính các trường có trong payload
(`profit_blockers`, `purchase_price`, `employee_resolved`). Gửi cả hai là
gửi cùng một sự thật hai lần, và hai bản sẽ lệch nhau khi một bên đổi.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.web import business_presentation, business_service, order_revision

#: Version của CHÍNH hình dạng payload này. Client đọc nó để biết mình đang
#: nói cùng một thứ tiếng với server; một lần đổi hình dạng không tương
#: thích phải tăng nó, và panel cũ sẽ tải lại thay vì đọc sai.
SCHEMA_VERSION = "R7-ORDER-1"


def _exact(value: Optional[Decimal]) -> Optional[str]:
    """`Decimal` → chuỗi thập phân chính xác; `None` giữ nguyên `None`.

    `normalize()` trước khi viết: `2.0` và `2` là cùng một số, và hai cách
    viết của cùng một số sẽ làm client tưởng giá trị đã đổi. Cùng quy ước
    `period_lock.canonical_text` dùng cho vân tay, vì cùng lý do.
    """
    if value is None:
        return None
    return format(value.normalize(), "f")


def _money(value: Optional[Decimal]) -> dict:
    """Một ô tiền: giá trị chính xác + chữ đã định dạng. Xem docstring module."""
    return {
        "value": _exact(value),
        "text": business_presentation.money_kvnd(value),
    }


def line_payload(detail: dict) -> dict:
    """Một DÒNG của đơn, đúng những trường panel sửa cần.

    Không có `imei` (xem docstring module). Không có tag hiển thị: chúng
    được dựng từ chính các trường dưới đây, và gửi cả hai là gửi cùng một
    sự thật hai lần — hai bản sẽ lệch nhau khi một bên đổi.
    """
    line = detail["line"]
    return {
        # Khoá ỔN ĐỊNH của dòng (`§8` brief) — ba phần, không phải chỉ số
        # hàng. R3 §1 đã trả giá một lần cho việc để vị trí làm danh tính.
        "order_key": detail["order_key"],
        "product_key": detail["product_key"],
        "occurrence_index": detail["occurrence_index"],
        "product_raw": detail.get("product_raw"),
        "sale_date": (detail["sale_date"].isoformat()
                      if detail.get("sale_date") else None),
        "quantity": _exact(line.quantity),
        "sell_price": _money(line.sell_price),
        "discount": _money(line.discount),
        "total_sales": _money(line.total_sales),
        # Giá nhập HIỆU LỰC + giá AUTO + provenance. Ba trường, và cả ba
        # cần thiết: panel phải biết ô này đang là giá tay hay giá tự động
        # để nói đúng câu "gỡ giá tay" hay "nhập giá", và phải biết giá
        # AUTO để nói ra cái sẽ quay về sau khi gỡ.
        "purchase_price": _money(line.purchase_price),
        "auto_purchase_price": _money(line.auto_purchase_price),
        "purchase_provenance": line.purchase_provenance,
        # Ô NHẬP: chuỗi điền sẵn trong input của panel. Đây là giá HIỆU
        # LỰC (kể cả khi nó là giá AUTO), đúng cùng cách
        # `workspace_presentation._line_row` điền ô của bảng — panel và
        # bảng phải điền cùng một con số, nếu không cùng một dòng đọc ra
        # hai giá tuỳ theo người dùng mở nó ở đâu.
        #
        # Điền sẵn giá AUTO KHÔNG biến nó thành giá tay khi người dùng bấm
        # lưu: `plan_order_edit` bỏ qua mọi ô có giá trị BẰNG giá hiện tại
        # ("không đổi ⟹ không quyết định mới"), nên một `MANUAL_OVERRIDE`
        # chỉ sinh ra khi con số thật sự khác. Rỗng ⟹ chưa có giá nào.
        "purchase_price_input": (
            "" if line.purchase_price is None
            else _exact(line.purchase_price) or ""),
        "kpi_profit": _money(line.kpi_profit),
        "converted_sales": _money(line.converted_sales),
        "conversion_rate": _exact(line.conversion_rate),
        "employee": line.employee,
        "employee_resolved": line.employee_resolved,
        "employee_group": line.employee_group,
        "line_type": line.line_type,
        # Nhóm sản phẩm HIỆU LỰC: quyết định của Owner ở cấp dòng thắng
        # nhóm do pipeline suy ra. Cùng thứ tự ưu tiên mà bảng kê dùng —
        # đọc từ `detail`, không tính lại ở đây.
        "product_group": (detail.get("line_product_group")
                          or detail.get("classified_product_group")
                          or detail.get("pipeline_product_group")),
        # `price_source` là NGUỒN giá mua, và nó là một authority riêng
        # (`§8` brief: nguồn công khai và nguồn Tracking là hai phạm vi,
        # thiếu một nguồn không cho phép dùng nguồn còn lại). Panel hiện
        # nó nguyên văn, không dịch và không đoán.
        "price_source": detail.get("price_source"),
        "auto_provenance": detail.get("auto_provenance"),
        # Provenance của lần ghi TAY gần nhất trên chính dòng này, nếu có.
        "override_entered_at": detail.get("override_entered_at"),
        "override_entered_by": detail.get("override_entered_by"),
        "override_reason": detail.get("override_reason"),
        # `profit_blockers` nói VÌ SAO một ô dẫn xuất trống. Đây là chỗ
        # `SOURCE_PENDING` của brief được nhìn thấy: thiếu nguồn giá không
        # phải giá bằng 0, và panel phải hiện "chưa có nguồn" chứ không
        # hiện một số 0 trông hợp lệ.
        "profit_blockers": list(line.profit_blockers or ()),
        # Trạng thái PHẠM VI của dòng, gắn bởi `order_revision.order_lines`.
        # `detail` gốc KHÔNG mang cờ này — "đã loại" và "vắng mặt trong sổ"
        # là thành viên của hai danh sách khác nhau trên `PeriodData`, chứ
        # không phải một cột. Panel cần biết, nên `order_lines` gắn nhãn khi
        # gom, và ở đây chỉ đọc lại.
        "scope": detail.get("_scope", "reported"),
    }


def detail_payload(*, data, order_key: str, period, service,
                   can_edit: bool) -> Optional[dict]:
    """Payload của `GET /api/v1/orders/{order_key}`, hoặc `None` nếu không có.

    `reason_required` là câu trả lời cho "lần lưu này có buộc phải ghi lý
    do không", và nó được tính bằng ĐÚNG cùng điều kiện mà server sẽ áp
    lúc ghi: có ít nhất một dòng đang có giá AUTO mà người dùng có thể
    thay. Panel dùng nó để hiện ô lý do NGAY thay vì để người dùng gõ xong
    rồi bị từ chối — nhưng server vẫn kiểm lại ở `plan_order_edit`, và đó
    mới là nơi ràng buộc sống (`R2 §4.4`).
    """
    lines = order_revision.order_lines(data, order_key)
    if not lines:
        return None
    first = lines[0]
    return {
        "schema_version": SCHEMA_VERSION,
        "order_key": order_key,
        "order_revision": order_revision.of_order(data, order_key),
        "period_revision": order_revision.of_period(data, period),
        "period": (None if period is None
                   else f"{period[0]}-{period[1]:02d}"),
        # Khách hàng thuộc về ĐƠN, không về từng dòng (`§23`).
        "customer_name": first.get("customer_name"),
        "customer_phone": first.get("customer_phone"),
        "customer_address": first.get("customer_address"),
        "sale_date": (first["sale_date"].isoformat()
                      if first.get("sale_date") else None),
        "date_text": business_presentation.business_date(first.get("sale_date")),
        "permissions": {"can_edit": bool(can_edit)},
        "lines": [line_payload(detail) for detail in lines],
        "reason_required": _reason_required(lines),
        # Kỳ đã chốt khoá mọi đường ghi (R3 §5). Panel phải biết TRƯỚC khi
        # người dùng gõ, không phải sau khi họ bấm lưu.
        "period_closed": bool(service.period_store.is_closed(period)),
        # Danh sách nhân viên gán được, đọc qua ĐÚNG hàm mà ô chọn của bảng
        # dùng (`keep_option=True` giữ mục "giữ nguyên" mang giá trị rỗng —
        # `FIND-R5-IR-01`: thiếu nó thì trình duyệt gửi option ĐẦU TIÊN và
        # cả đơn đổi chủ vì một cú bấm để lưu giá).
        "employees": [
            {"value": option["value"], "label": option["label"]}
            for option in business_presentation.assignable_employee_options(
                service.assignable_employees(), keep_option=True)],
        "employee_value": _order_employee(lines),
        "updated_at": _latest_decision_at(lines),
        "updated_by": _latest_decision_by(lines),
    }


def _reason_required(lines) -> bool:
    """`True` khi ĐƠN có ít nhất một dòng đang mang giá AUTO thay được.

    Cùng điều kiện `plan_order_edit` áp (`overrides` = các lần ghi có
    `auto_price is not None`), đọc trước thay vì sau. Nó là một GỢI Ý cho
    giao diện; server vẫn là nơi từ chối.
    """
    return any(line["line"].auto_purchase_price is not None for line in lines)


def _order_employee(lines) -> str:
    """Nhân viên của CẢ đơn, hoặc chuỗi rỗng khi đang chia cho nhiều người.

    Rỗng chứ không đoán một người: `§27` nói một BH có đúng một người bán,
    và gợi ý sai ở đây dời KPI của người khác chỉ vì một cú bấm để lưu giá
    (`FIND-R5-IR-01`).
    """
    names = {line["line"].employee for line in lines if line["line"].employee}
    return names.pop() if len(names) == 1 else ""


def _latest_decision_at(lines) -> Optional[str]:
    """Mốc thời gian quyết định GẦN NHẤT trên đơn, hoặc `None`.

    `None` nghĩa là chưa có quyết định nào của người trên đơn này — không
    phải "chưa biết". Panel hiện "chưa có sửa tay nào" chứ không hiện một
    ngày trống trông như dữ liệu bị mất.
    """
    stamps = [line.get("override_entered_at") for line in lines]
    stamps = [stamp for stamp in stamps if stamp]
    return max(stamps) if stamps else None


def _latest_decision_by(lines) -> Optional[str]:
    """Người ra quyết định GẦN NHẤT — người của chính mốc `updated_at` trên.

    Sắp theo mốc thời gian rồi lấy người của mốc lớn nhất, chứ không lấy
    `max()` của tập tên: `max()` trên tên trả về tên xếp cuối theo thứ tự
    chữ, và nó sẽ nói sai ai vừa sửa ngay khi đơn có hai người sửa.
    """
    pairs = [(line.get("override_entered_at"), line.get("override_entered_by"))
             for line in lines]
    pairs = [pair for pair in pairs if pair[0]]
    if not pairs:
        return None
    return max(pairs, key=lambda pair: pair[0])[1]


def patch_payload(*, data, order_key: str, period, service,
                  plan: business_service.OrderEditPlan,
                  message: str, sheet=None) -> dict:
    """Payload thành công của `PATCH /api/v1/orders/{order_key}`.

    Brief §API-02 nói response chỉ trả "đơn/dòng vừa cập nhật; aggregate/KPI
    THỰC SỰ bị ảnh hưởng; revision mới; audit ID, người và thời điểm".

    "KPI thực sự bị ảnh hưởng" ở đây là: tổng của CẢ KỲ và tổng của SHEET
    đang xem. Không phải mọi sheet — một lần sửa giá nhập của một đơn không
    đổi tổng của sheet người khác, và gửi cả chúng là gửi lại cả màn hình
    dưới một cái tên khác. Tổng kỳ có mặt vì nó LUÔN đổi khi một con số
    dòng đổi, và vì brief §6 nói "KPI/tổng luôn tính trên toàn bộ kỳ, không
    chỉ các dòng đã tải".

    `data` phải là `PeriodData` ĐỌC LẠI SAU khi ghi. Truyền bản trước khi
    ghi vào đây sẽ trả về revision cũ, và panel sẽ gửi lần sau với một
    `base_revision` đã lỗi thời ngay từ lúc nó nhận được.
    """
    payload = {
        "schema_version": SCHEMA_VERSION,
        "order_key": order_key,
        "order_revision": order_revision.of_order(data, order_key),
        "period_revision": order_revision.of_period(data, period),
        "message": message,
        "applied": {
            "price_writes": len(plan.price_writes),
            "price_clears": len(plan.price_clears),
            "employee": plan.employee,
        },
        "lines": [line_payload(detail)
                  for detail in order_revision.order_lines(data, order_key)],
        "totals": {
            "period": business_service.snapshot_of(data.totals),
        },
    }
    if sheet is not None:
        payload["totals"]["sheet"] = {
            "key": sheet.key,
            **business_service.snapshot_of(data.for_sheet(sheet).totals),
        }
    return payload
