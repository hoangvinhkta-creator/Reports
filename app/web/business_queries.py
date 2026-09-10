"""PHB-03 — đọc các dòng hàng hiện hành và dựng `BusinessLine`.

Tầng này là nơi DUY NHẤT của PHB-03 nói SQL ĐỌC. Nó giữ nguyên ba kỷ luật đã
freeze ở `analytics_queries` (`TASK-PRA-003`) và `sales_queries`
(`TASK-PRA-004`):

1. **CHỈ ĐỌC.** Không `INSERT`/`UPDATE`/`DELETE` nào. Mọi đường ghi của PHB-03
   nằm ở `app/web/business_store.py`, tách bạch và kiểm được bằng cấu trúc.
2. **Chỉ trạng thái hiện hành.** Mọi dòng đi qua `order_line_current` và hai
   con trỏ `current_source_version_id`/`current_result_version_id`. PK của
   bảng đó là `(order_key, product_key, occurrence_index)` nên mỗi khoá góp
   ĐÚNG một dòng. Không bao giờ cộng `summary_json` qua các run.
3. **`NULL` không phải `0`.** Không coalesce gì. Việc phân biệt "chưa biết"
   với "bằng không" được `business_metrics` giữ tiếp.

## Hàng rào dữ liệu cá nhân — hẹp hơn PRA-003, và nói ra từng trường

Tầng này ĐỌC `product_raw`, giống `sales_queries` và vì cùng một lý do đã
được nghiệm thu (`TASK-PRA-004`, frozen contract mục 14.4): danh sách "dòng
còn thiếu giá nhập" và danh sách "mặt hàng cần tick Gia dụng" phải cho Owner
biết ĐANG NÓI VỀ MẶT HÀNG NÀO. `canonical_product_code` rỗng trên dữ liệu
thật nên không thay thế được, và `product_key` là một hash.

`DEC-PHB02-08` mở thêm ĐÚNG BA trường, và đóng lại ngay sau đó:

    ĐI QUA   `customer_name` · `customer_phone` · `customer_address`

Owner yêu cầu tường minh rằng bảng kê nghiệp vụ phải hiện Tên KH · SĐT · Địa
chỉ: một dòng bán không có khách hàng thì không đối chiếu được với đơn thật,
và ba trường đó nằm sẵn trong chính sổ kế toán đang nạp (`raw_reader` cột
5/6/7). Không CRM, không ghép danh tính liên hệ thống.

Cột VẪN KHÔNG được đọc ở đây (`governance/product/17_DATA_GOVERNANCE_PRIVACY.md`):
mã máy, `note_raw`, `employee_raw`. Danh sách này được
`tests/test_business_boundaries.py` canh bằng chính mã nguồn.

R5 §5 (`DEC-R5-03`) mở mã máy trên ĐÚNG bảng kê của tab nhân viên — và cố ý
KHÔNG mở nó ở đây. Tầng này là đầu vào của MỌI trang dùng `PeriodData` (tổng
hợp, cơ cấu, thương hiệu, đánh giá, export); thêm một cột vào đây là trao nó
cho tất cả cùng lúc, kể cả những trang chưa được viết. Cánh cửa hẹp nằm ở
`app/web/workspace_imei.py`, và `tests/test_r5_imei_boundary.py` canh rằng
chỉ `server.py` mở nó.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import distinct, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.modules.reporting import line_type as line_type_module
from app.modules.reporting.business_metrics import BusinessLine
from app.modules.reporting.rate_routing import ConversionRateRouter
from app.web.history_store import HistoryUnavailableError
from app.web import db_scope
from tools.db.schema import (
    order_line_current, order_line_result_version, order_line_source_version,
)

_RESULT = order_line_result_version.c
_SOURCE = order_line_source_version.c
_CURRENT = order_line_current.c

#: Số khoá tối đa nhét vào một mệnh đề `IN` — cùng giới hạn mà
#: `history_store` đã dùng, và cùng lý do: SQLite có trần tham số.
_KEY_CHUNK = 500


def _joined():
    """`order_line_current` nối sang ĐÚNG version hiện hành của nó."""
    return order_line_current.join(
        order_line_result_version,
        _RESULT.id == _CURRENT.current_result_version_id,
    ).join(
        order_line_source_version,
        _SOURCE.id == _CURRENT.current_source_version_id,
    )


def _period(date_from: Optional[date], date_to: Optional[date]) -> list:
    """`sale_date IS NOT NULL` LUÔN có mặt — dòng thiếu ngày bán rơi khỏi MỌI
    kỳ một cách nhất quán, đúng ngữ nghĩa kỳ đã freeze ở PRA-003."""
    conditions = [_CURRENT.sale_date.is_not(None)]
    if date_from is not None:
        conditions.append(_CURRENT.sale_date >= date_from)
    if date_to is not None:
        conditions.append(_CURRENT.sale_date <= date_to)
    return conditions


def _read(engine: db_scope.EngineOrConnection, statement) -> list[dict]:
    """Lỗi database KHÔNG BAO GIỜ được biến thành "chưa có dữ liệu".

    `STAB-03 REPAIR` — `engine` nay là `Engine` HOẶC `Connection`. Đọc qua
    một `Connection` do người gọi mở là điều kiện để phép kiểm revision
    nhìn thấy ĐÚNG trạng thái mà lần ghi sắp tới sẽ ghi lên, thay vì một
    ảnh chụp đọc trước transaction (`P0-3`). Xem `app/web/db_scope.py`.
    """
    try:
        with db_scope.of(engine).connect() as connection:
            return [dict(row._mapping) for row in connection.execute(statement)]
    except SQLAlchemyError as exc:
        raise HistoryUnavailableError(str(exc)) from exc


_COLUMNS = (
    _CURRENT.order_key, _CURRENT.product_key, _CURRENT.occurrence_index,
    _CURRENT.sale_date,
    _RESULT.status, _RESULT.pending_reasons_json,
    _RESULT.employee_normalized, _RESULT.employee_group,
    _RESULT.lead_source_final, _RESULT.total_sales, _RESULT.kpi_purchase_price,
    _RESULT.kpi_purchase_provenance, _RESULT.eligible_kpi_profit,
    # R4 — THẨM QUYỀN GIÁ mà pipeline đã dùng cho dòng này (`Tracking:DailyMin`,
    # `Pending`, …). CHỈ để hiển thị ở khối chất lượng dữ liệu: nó trả lời câu
    # "giá vốn của kỳ này đến từ đâu", vốn khác hẳn câu `kpi_purchase_
    # provenance` trả lời ("ai/cái gì chốt con số KPI"). Không phép tính nghiệp
    # vụ nào đọc trường này — thêm nó vào một cửa chặn lợi nhuận sẽ dựng một
    # thẩm quyền giá thứ hai bên cạnh ba thẩm quyền đã freeze ở R3.
    _RESULT.price_source,
    _RESULT.product_group_final, _RESULT.conversion_rate_final,
    # repair `FIND-R2-IR-03` — mốc lần chạy đã tính ra CHÍNH dòng này, không
    # phải mốc của bất kỳ bảng nào khác cùng tên cột (`order_line_source_
    # version` cũng có `created_at`) — `.label()` để tránh đụng khoá khi
    # `_read()` gộp mọi cột vào MỘT dict phẳng theo tên. `line_identity.
    # state_of` so nó với `confirmed_at` của một mapping giải mâu thuẫn để
    # biết quyết định đó MỚI HƠN hay CŨ HƠN bằng chứng đang hiển thị — không
    # cột/bảng mới nào được thêm, đây là cột ĐÃ CÓ SẴN từ trước R2.
    _RESULT.created_at.label("result_created_at"),
    # `R5.4` — mã Tracking mà LẦN CHẠY đã phân giải cho dòng này, cùng
    # namespace của nó. Hai cột ĐÃ CÓ SẴN trong `order_line_result_version`
    # từ `TASK-105D` (`history/extraction.py` ghi chúng ở mỗi lần chạy); chỉ
    # đến `R5.4` tầng đọc mới chở chúng xuống dòng. CHỈ để `line_identity.
    # tracking_identity_of` tra NHÃN (model/hãng/nhóm hàng) cho dòng đã khớp
    # TỰ ĐỘNG với Tracking (`alias.map`/`board`/`inv.map`) — những dòng mà
    # store Product Identity của Reports cố ý KHÔNG lưu mapping nào (resolve
    # là phép đọc thuần, `INV-70`). Không phép tính tiền nào đọc hai cột này.
    _RESULT.identity_namespace, _RESULT.canonical_product_code,
    _SOURCE.product_raw, _SOURCE.quantity, _SOURCE.sell_price, _SOURCE.discount,
    _SOURCE.customer_name, _SOURCE.customer_phone, _SOURCE.customer_address,
)


def reasons(raw: Optional[str]) -> tuple[str, ...]:
    """`pending_reasons_json` đã lưu → tuple mã, khử trùng lặp, GIỮ thứ tự.

    Cùng cách giải mã đã nghiệm thu ở `sales_queries._reasons` (TASK-PRA-004),
    và cùng lý do: JSON hỏng trả về tuple RỖNG chứ không phải HTTP 500 — một
    dòng mất danh sách lý do vẫn hiện đúng mọi con số, còn một trang trắng thì
    không nói được gì cả.

    Các mã này KHÔNG tham gia vào cửa chặn lợi nhuận (`OD-6`). Chúng chỉ dùng
    để dựng cảnh báo (`Duplicate`) và để hiện cho Owner biết pipeline đã ghi
    chú gì trên dòng.
    """
    try:
        parsed = json.loads(raw or "[]")
    except (TypeError, ValueError):
        return ()
    if not parsed:
        return ()
    return tuple(dict.fromkeys(str(value) for value in parsed))


def raw_lines(
    engine: Engine, *, date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> list[dict]:
    """Các dòng hiện hành của kỳ, chưa hợp nhất quyết định của Owner."""
    statement = select(*_COLUMNS).select_from(_joined())
    for condition in _period(date_from, date_to):
        statement = statement.where(condition)
    return _read(engine, statement.order_by(
        _CURRENT.sale_date, _CURRENT.order_key, _CURRENT.occurrence_index))


def employee_names(
    engine: Engine, *, date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> list[tuple[Optional[str], Optional[str]]]:
    """`(nhân viên, nhóm)` có dòng trong kỳ, đã sắp theo tên.

    Chuỗi rỗng và `NULL` là CÙNG một tình trạng nghiệp vụ ("chưa xác định được
    ai bán") — gộp về `None` ở đây đúng như PRA-003/PRA-004 đã làm, để bộ chọn
    nhân viên không hiện hai mục trống cạnh nhau như thể đó là hai người.
    """
    statement = select(
        distinct(_RESULT.employee_normalized).label("employee"),
        _RESULT.employee_group.label("employee_group"),
    ).select_from(_joined())
    for condition in _period(date_from, date_to):
        statement = statement.where(condition)
    seen: dict[Optional[str], Optional[str]] = {}
    for row in _read(engine, statement):
        name = row["employee"] or None
        seen.setdefault(name, row["employee_group"])
    return sorted(seen.items(), key=lambda item: (item[0] is None, item[0] or ""))


def merge_assigned_names(
    names: list[tuple[Optional[str], Optional[str]]], lines: list[BusinessLine],
) -> list[tuple[Optional[str], Optional[str]]]:
    """Bộ chọn nhân viên phải phản ánh CẢ những lần Owner gán lại (`OD-5`).

    `employee_names` đọc thẳng cột của pipeline, nên nó không thấy một người
    vừa được gán lại — và nếu bộ chọn không có tên đó thì trang nhân viên trả
    404 ngay sau khi Owner vừa lưu thành công. Ngược lại, nhóm "chưa xác định"
    phải BIẾN MẤT khỏi bộ chọn khi dòng cuối cùng của nó đã được gán, nếu
    không Owner sẽ mở ra một trang trống và tưởng mất dữ liệu.

    Vì vậy danh sách được dựng lại từ chính tập dòng ĐÃ HỢP NHẤT — một nguồn
    sự thật, không phải hai.
    """
    seen: dict[Optional[str], Optional[str]] = {}
    for line in lines:
        seen.setdefault(line.employee or None, line.employee_group)
    for name, group in names:
        # Giữ tên chỉ có trong bộ chọn cũ (ví dụ nhân viên có dòng ngoài kỳ
        # đang xem) thay vì âm thầm bỏ đi — trừ mục "chưa xác định", vốn phải
        # tự tắt khi không còn dòng nào vô chủ.
        if name is not None:
            seen.setdefault(name, group)
    return sorted(seen.items(), key=lambda item: (item[0] is None, item[0] or ""))


def periods_for_product(engine: Engine, product_key: str) -> set:
    """`{(năm, tháng)}` có ít nhất một dòng của mặt hàng này (R3 §5).

    Phân loại Gia dụng ở cấp MẶT HÀNG là một quyết định TOÀN CỤC: nó đổi tỉ lệ
    quy đổi của mọi dòng mang mã đó, ở mọi kỳ. Nên cửa chặn "kỳ đã chốt" cho
    thao tác này không thể chỉ hỏi kỳ đang xem — nó phải hỏi mọi kỳ mà quyết
    định ấy chạm tới. Một câu truy vấn cho một thao tác hiếm.
    """
    rows = _read(engine, select(_CURRENT.sale_date).distinct()
                 .where(_CURRENT.product_key == product_key,
                        _CURRENT.sale_date.is_not(None)))
    return {(row["sale_date"].year, row["sale_date"].month) for row in rows}


def sale_dates_of(engine: Engine, keys) -> dict:
    """`{khoá dòng: sale_date}` cho các khoá hỏi tới (R5 §2).

    Chỉ đọc `order_line_current` — không join sang version nào, vì câu hỏi
    duy nhất ở đây là "dòng này thuộc kỳ nào". Lọc theo `order_key` NGAY
    TRONG SQL rồi mới đối chiếu đủ ba thành phần khoá trong Python: khoá là
    một bộ ba, và SQLite/PostgreSQL không có cùng cách viết `IN` cho tuple.

    Khoá không còn hiện hành cố ý VẮNG khỏi kết quả, không mang `None` —
    "không có dòng" và "có dòng nhưng chưa biết ngày bán" là hai sự thật
    khác nhau, và người gọi phân biệt được chúng.
    """
    wanted = {tuple(key) for key in keys}
    order_keys = sorted({key[0] for key in wanted})
    if not order_keys:
        return {}
    found: dict = {}
    for start in range(0, len(order_keys), _KEY_CHUNK):
        rows = _read(engine, select(
            _CURRENT.order_key, _CURRENT.product_key,
            _CURRENT.occurrence_index, _CURRENT.sale_date,
        ).where(_CURRENT.order_key.in_(order_keys[start:start + _KEY_CHUNK])))
        for row in rows:
            key = (row["order_key"], row["product_key"], row["occurrence_index"])
            if key in wanted:
                found[key] = row["sale_date"]
    return found


def undated_lines(engine: Engine) -> int:
    """Dòng hiện hành KHÔNG có `sale_date`, đếm KHÔNG lọc kỳ (`R-S5`)."""
    rows = _read(engine, select(func.count().label("total"))
                 .select_from(order_line_current)
                 .where(_CURRENT.sale_date.is_(None)))
    return int(rows[0]["total"] or 0)


def effective_product_group(
    *, product_key: str, key: tuple, classifications: dict,
    line_classifications: Optional[dict] = None,
) -> Optional[str]:
    """Phân loại Gia dụng HIỆU LỰC của một dòng — quy tắc hợp nhất DUY NHẤT.

    Owner có hai cách nói cùng một câu, ở hai độ mịn khác nhau:

        `product_group_classification`       "MẶT HÀNG này là Gia dụng"
        `line_product_group_classification`  "ĐÚNG DÒNG này là Gia dụng"

    `DEC-PHB02-08` §10: một BH có ba dòng và Owner chuyển đúng MỘT dòng sang
    Gia dụng. Không có cách nào biểu diễn điều đó bằng khoá `product_key`, nên
    quyết định cấp DÒNG tồn tại — và vì nó CỤ THỂ HƠN, nó thắng.

    Đây KHÔNG phải một thẩm quyền Gia dụng thứ hai: cả hai bảng dùng chung từ
    vựng `PRODUCT_GROUPS`, và kết quả của hàm này đi vào ĐÚNG một chỗ —
    `ConversionRateRouter`, vốn hỏi lại `ConversionSchemeResolver`. Việc viết
    quy tắc ưu tiên ở một hàm duy nhất là cách bảo đảm hai bảng không bao giờ
    cho ra hai câu trả lời khác nhau trên hai màn hình khác nhau.

    `None` ⟹ Owner chưa nói gì về dòng này, và tầng gọi giữ nguyên giá trị mà
    pipeline đã ghi.
    """
    line_classifications = line_classifications or {}
    at_line = line_classifications.get(key)
    if at_line is not None:
        return at_line["product_group"]
    classified = classifications.get(product_key)
    return None if classified is None else classified["product_group"]


def build_lines(
    rows: list[dict], *, overrides: dict, classifications: dict,
    router: ConversionRateRouter, kpi_authority_valid: bool,
    employee_overrides: Optional[dict] = None,
    line_classifications: Optional[dict] = None,
    line_type_vocabulary: Optional[line_type_module.LineTypeVocabulary] = None,
) -> list[BusinessLine]:
    """Hợp nhất dòng pipeline + quyết định Owner thành `BusinessLine`.

    Đây là điểm hợp nhất DUY NHẤT của các thẩm quyền, và nó xảy ra lúc ĐỌC —
    không có bản ghi nào bị sửa để đạt được kết quả này. Đó cũng là lý do việc
    Owner sửa giá nhập hay gán lại nhân viên có hiệu lực NGAY ở lần tải trang
    kế tiếp, không cần chạy lại pipeline (`OD-5`, chỉ thị `PURCHASE PRICE
    EDITING`).

    `kpi_authority_valid` KHÔNG có giá trị mặc định: nó là van fail-closed của
    `DEC-143` §1, và một van an toàn có giá trị mặc định "mở" thì không phải
    van an toàn. Tầng gọi phải đọc `config/eligible_costs.yaml` và nói ra kết
    quả.

    `discount` được coalesce về `0` (và CHỈ nó): công thức đã freeze của
    `DEC-143` là `(SellPrice − KpiPurchasePrice) × Quantity − Discount`, trong
    đó `Discount` là một khoản TRỪ, nên "không có chiết khấu" đúng nghĩa là
    "trừ đi 0". Điều đó khác hẳn `sell_price`/`quantity` vắng mặt — hai cái đó
    làm lợi nhuận KHÔNG XÁC ĐỊNH và vẫn phải là `None`.
    """
    employee_overrides = employee_overrides or {}
    lines = []
    for row in rows:
        # R3 §2 — loại dòng tính LÚC ĐỌC, cùng chỗ và cùng lý do với override:
        # nó là một luật nghiệp vụ áp lên bằng chứng đã lưu, không phải một
        # kết quả của lần chạy máy. Sửa `config/line_types.yaml` vì thế có
        # hiệu lực ở lần tải trang kế tiếp, không cần nạp lại sổ.
        #
        # Bốn đầu vào, và chỉ bốn: số chứng từ, tên hàng, đơn giá, số lượng.
        # `note_raw` KHÔNG được đọc — hàng rào dữ liệu ở đầu file này liệt kê
        # nó trong nhóm cột không đi qua tầng truy vấn, và R3 không mở nó ra.
        effective_line_type = line_type_module.classify(
            vocabulary=line_type_vocabulary,
            order_key=row["order_key"],
            product_raw=row["product_raw"],
            sell_price=row["sell_price"],
            quantity=row["quantity"],
        )
        key = (row["order_key"], row["product_key"], int(row["occurrence_index"]))
        override = overrides.get(key)
        assigned = employee_overrides.get(key)
        classified_group = effective_product_group(
            product_key=row["product_key"], key=key,
            classifications=classifications,
            line_classifications=line_classifications)
        # Bằng chứng gốc ĐI KÈM chứ không bị thay thế: `source_employee` giữ
        # nguyên tên mà sổ ghi, `employee` mới là tên có hiệu lực để cộng KPI.
        source_employee = row["employee_normalized"] or None
        lines.append(BusinessLine(
            order_key=row["order_key"],
            employee=(source_employee if assigned is None
                      else assigned["employee_normalized"]),
            employee_group=(row["employee_group"] if assigned is None
                            else assigned["employee_group"]),
            source_employee=source_employee,
            employee_provenance="SOURCE" if assigned is None else "MANUAL",
            pending_reasons=reasons(row["pending_reasons_json"]),
            kpi_authority_valid=kpi_authority_valid,
            status=row["status"],
            sell_price=row["sell_price"],
            quantity=row["quantity"],
            discount=row["discount"] if row["discount"] is not None else Decimal(0),
            total_sales=row["total_sales"],
            auto_purchase_price=row["kpi_purchase_price"],
            auto_kpi_profit=row["eligible_kpi_profit"],
            manual_purchase_price=(
                None if override is None else override["purchase_price"]),
            manual_provenance=(
                None if override is None else override["provenance"]),
            line_type=effective_line_type,
            # Tỉ lệ hỏi lại resolver bằng danh tính HIỆU LỰC của dòng, không
            # phải danh tính thô của pipeline.
            #
            # `rate_routing` nói rõ ranh giới mà `DEC-PHB02-05` đặt ra: *"một
            # nhân viên bán lẻ vì thế KHÔNG BAO GIỜ đi qua 8 % được, kể cả khi
            # mặt hàng đã bị tick"*. Đọc `row["employee_group"]` làm thủng
            # đúng ranh giới đó sau một lần Owner gán lại dòng (`OD-5`): dòng
            # sang bảng của Ly nhưng vẫn quy đổi theo nhóm Nội thành.
            #
            # Phạm vi ảnh hưởng hẹp theo cấu tạo: `rate_for` trả NGUYÊN
            # `stored_rate` khi `classified_group is None`, nên chỉ những dòng
            # ĐÃ được phân loại Gia dụng mới hỏi lại resolver — tức đúng tập
            # dòng mà ranh giới trên nói về.
            conversion_rate=router.rate_for(
                stored_rate=row["conversion_rate_final"],
                classified_group=classified_group,
                employee=(source_employee if assigned is None
                          else assigned["employee_normalized"]),
                employee_group=(row["employee_group"] if assigned is None
                                else assigned["employee_group"]),
                lead_source=row["lead_source_final"],
                sale_date=row["sale_date"],
            ),
        ))
    return lines


def line_details(
    rows: list[dict], lines: list[BusinessLine], *, classifications: dict,
    overrides: Optional[dict] = None,
    line_classifications: Optional[dict] = None,
) -> list[dict]:
    """Ghép mỗi `BusinessLine` với các trường CHỈ dùng để hiển thị/định danh.

    `BusinessLine` cố ý không mang `product_raw`, `product_key` hay `sale_date`
    — nó là ngữ nghĩa nghiệp vụ thuần, và nhồi thêm trường trình bày vào đó sẽ
    làm mọi test nghiệp vụ phải dựng dữ liệu mà chúng không quan tâm. Hai danh
    sách đi song song vì `build_lines` giữ nguyên thứ tự của `rows`.

    `R2` — `overrides` chỉ để LẤY LẠI hai trường đã lưu sẵn từ lúc Owner bấm
    LƯU: `auto_price_at_entry` (giá tự động ngay TRƯỚC lần sửa đó) và
    `entered_at`. Không có kiến trúc lịch sử mới nào ở đây, và hai trường này
    KHÔNG tham gia bất kỳ phép tính nào — chúng là bối cảnh để Owner đọc lại
    quyết định của chính mình. `auto_price_at_entry` khác `line.auto_purchase
    _price`: cái sau là giá tự động HÔM NAY, cái trước là giá tự động LÚC ĐÓ.
    """
    overrides = overrides or {}
    line_classifications = line_classifications or {}
    details = []
    for row, line in zip(rows, lines):
        key = (row["order_key"], row["product_key"], int(row["occurrence_index"]))
        classified_group = effective_product_group(
            product_key=row["product_key"], key=key,
            classifications=classifications,
            line_classifications=line_classifications)
        override = overrides.get(key)
        details.append({
            "order_key": row["order_key"],
            "product_key": row["product_key"],
            "occurrence_index": int(row["occurrence_index"]),
            "product_raw": row["product_raw"],
            "sale_date": row["sale_date"],
            "auto_provenance": row["kpi_purchase_provenance"],
            # R4 — hai trường CHỈ ĐỂ ĐỌC của báo cáo đánh giá. `lead_source`
            # đã được `build_lines` dùng cho định tuyến tỉ lệ từ trước; đưa nó
            # sang `details` không mở thêm cột nào của database, chỉ thôi vứt
            # đi một giá trị đã đọc. Không trường nào ở đây tham gia một phép
            # gộp tiền nào.
            "lead_source": row.get("lead_source_final"),
            "price_source": row.get("price_source"),
            # repair `FIND-R2-IR-03` — xem chú thích ở `_COLUMNS`. Chỉ dùng để
            # ĐỌC LẠI trong `line_identity.state_of`; không phép tính nghiệp
            # vụ nào khác chạm vào trường này.
            "result_created_at": row.get("result_created_at"),
            # `R5.4` — xem chú thích ở `_COLUMNS`. Chỉ `line_identity.
            # tracking_identity_of` đọc hai trường này.
            "identity_namespace": row.get("identity_namespace"),
            "canonical_product_code": row.get("canonical_product_code"),
            "customer_name": row.get("customer_name"),
            "customer_phone": row.get("customer_phone"),
            "customer_address": row.get("customer_address"),
            "pipeline_product_group": row["product_group_final"],
            "classified_product_group": classified_group,
            # `DEC-PHB02-08` — Owner đã nói về ĐÚNG DÒNG NÀY hay chưa. Khác
            # `classified_product_group`, vốn có thể đến từ quyết định cấp mặt
            # hàng: chỉ dòng có quyết định riêng mới được phép "gỡ" quyết định
            # riêng đó, còn gỡ một quyết định cấp mặt hàng là việc của trang
            # phân loại mặt hàng.
            "line_product_group": (
                None if line_classifications.get(key) is None
                else line_classifications[key]["product_group"]),
            "override_auto_price_at_entry": (
                None if override is None else override["auto_price_at_entry"]),
            "override_entered_at": (
                None if override is None else override["entered_at"]),
            # R2 §4.4 — hai nửa còn lại của provenance: AI quyết định và VÌ
            # SAO. Cả hai chỉ để ĐỌC LẠI; không phép tính nào chạm vào chúng.
            "override_entered_by": (
                None if override is None else override["entered_by"]),
            "override_reason": (
                None if override is None else override["reason"]),
            "line": line,
        })
    return details


__all__ = [
    "build_lines", "employee_names", "line_details", "merge_assigned_names",
    "periods_for_product", "raw_lines", "reasons", "undated_lines",
]
