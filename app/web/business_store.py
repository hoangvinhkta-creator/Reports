"""PHB-03 — đường GHI DUY NHẤT cho các quyết định của Owner.

Repository này là toàn bộ persistence mới của PHB-03 (và, từ PHB-05, của
Target), và nó cố ý nhỏ. Nó biết đúng bốn việc:

1. `set_purchase_price` — ghi/ghi đè giá nhập KPI của MỘT dòng hàng.
2. `set_product_group` — ghi/gỡ phân loại Gia dụng của MỘT mặt hàng.
3. `set_employee` — gán/gỡ nhân viên cho MỘT dòng hàng (`OD-5`).
4. `set_employee_target` — đặt/gỡ Target tháng của MỘT nhân viên (PHB-05,
   `DEC-PHB02-06`).

Việc thứ ba dùng lại NGUYÊN cấu trúc của việc thứ nhất — cùng khoá nghiệp vụ,
cùng kiểu upsert, cùng cột provenance-một-cột. Đó là lý do nó không làm module
này lớn thêm về mặt khái niệm: nó là cùng một hình dạng, áp lên một trường
khác. Việc thứ tư cũng vậy, chỉ khác KHOÁ: `(năm, tháng, nhân viên)` thay vì
`(đơn, mặt hàng, lần xuất hiện)` — vì Target là một dự định của cả tháng, chứ
không phải một sự thật của một dòng chứng từ.

Những gì module này KHÔNG phải, và không được lớn thành (chỉ thị PHB-03 §3):
không hệ thống quản lý giá nhập, không luồng duyệt, không lịch sử phiên bản,
không audit service, không trình soạn dữ liệu kinh tế tổng quát.

## Ranh giới thẩm quyền — cái gì KHÔNG bị đụng tới

`accounting_purchase_price` / `price_source` (PriceProvider — TASK-105,
105B–105E) và `HistoricalConfirmedRegistry` (E-J, chỉ pre-cutover, `INV-47`/
`INV-51`) **không** được ghi ở đây, và không có đường nào từ đây tới chúng.
Giá do Owner nhập chỉ đi vào ĐƯỜNG BÁO CÁO KPI: `kpi_purchase_price` hiệu lực
→ `EligibleKpiProfit` → DS quy đổi. Đó đúng là slot mà
`app/modules/domain/models.py` đã dành sẵn từ TASK-105 (`PRICE_SOURCE_MANUAL`
— *"for when override/audit trail exists"*), nên PHB-03 lấp một chỗ đã chừa,
không mở một thẩm quyền thứ hai.

`order_line_result_version` cũng KHÔNG bị UPDATE: nó append-only, mỗi dòng là
kết quả của một lần chạy engine. Giá do người nhập được lưu ở bảng riêng và
hợp nhất lúc ĐỌC (`business_queries`), nên "engine tính ra gì" và "Owner
quyết định gì" không bao giờ bị trộn thành một con số không nhãn.

## Vì sao ghi đè tại chỗ (UPSERT) chứ không append version

`DEC-PHB02-02` yêu cầu phân biệt `AUTO` với `MANUAL`/`MANUAL_OVERRIDE` — nó
KHÔNG yêu cầu lịch sử các lần sửa, và PHB-03 §3 cấm dựng version-control.
Bằng chứng cho chữ `MANUAL_OVERRIDE` vì thế được giữ bằng đúng MỘT cột
(`auto_price_at_entry`: giá AUTO tại thời điểm ghi đè), không bằng một chuỗi
phiên bản.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional

from sqlalchemy import delete, insert, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.web.history_store import HistoryUnavailableError
from tools.db.schema import (
    ORIGIN_PIPELINE, PURCHASE_PROVENANCE_MANUAL,
    PURCHASE_PROVENANCE_MANUAL_OVERRIDE, employee_attribution_override,
    employee_target, kpi_purchase_price_override, product_group_classification,
)

PRODUCT_GROUPS = ("DIEN_MAY", "GIA_DUNG")


class InvalidPurchasePriceError(ValueError):
    """Giá trị Owner nhập không dùng được — TỪ CHỐI, không đoán hộ."""


class InvalidProductGroupError(ValueError):
    """Nhóm sản phẩm không thuộc tập đã freeze (`DEC-127`, ADR-106)."""


class InvalidEmployeeError(ValueError):
    """Tên nhân viên không dùng được — TỪ CHỐI, không gán bừa cho ai."""


class InvalidTargetError(ValueError):
    """Target Owner nhập không dùng được — TỪ CHỐI, không đoán hộ (PHB-05 §14)."""


class InvalidTargetPeriodError(ValueError):
    """Kỳ của Target không phải một tháng thật — không có chỗ nào để lưu."""


def parse_purchase_price(raw: Optional[str]) -> Decimal:
    """Chuỗi người gõ → `Decimal` VND, hoặc `InvalidPurchasePriceError`.

    Chấp nhận dấu chấm/khoảng trắng phân cách nghìn theo thói quen vi-VN
    (`12.500.000`) và dấu phẩy thập phân (`12500000,5`) — đó là cách Owner
    thật sự gõ số, và bắt người dùng học một định dạng khác chỉ để phần mềm
    đỡ phải parse là đẩy việc sang phía sai.

    Từ chối: rỗng, không phải số, âm. Giá nhập âm không phải một sự thật
    nghiệp vụ nào; chấp nhận nó sẽ thổi phồng lợi nhuận KPI trong im lặng.
    `0` được CHẤP NHẬN — hàng khuyến mại/quà tặng có giá nhập 0 là chuyện có
    thật, và ép nó thành "chưa nhập" sẽ khoá coverage ở dưới 100 % vĩnh viễn.
    """
    text = (raw or "").strip().replace(" ", "").replace(" ", "")
    if not text:
        raise InvalidPurchasePriceError("Chưa nhập giá nhập.")
    # Dấu chấm là phân cách nghìn trong cách viết vi-VN; dấu phẩy là thập phân.
    text = text.replace(".", "").replace(",", ".")
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError):
        raise InvalidPurchasePriceError(
            f"Giá nhập {raw!r} không phải một số hợp lệ."
        ) from None
    if value < 0:
        raise InvalidPurchasePriceError("Giá nhập không được âm.")
    return value


def parse_target(raw: Optional[str]) -> Optional[Decimal]:
    """Chuỗi Owner gõ → `Decimal` VND, `None` (gỡ target), hoặc lỗi.

    Dùng LẠI đúng quy ước gõ số của `parse_purchase_price` — dấu chấm là phân
    cách nghìn kiểu vi-VN, dấu phẩy là thập phân — vì đó là cùng một Owner gõ
    cùng một loại con số trong cùng một sản phẩm. Hai quy ước nhập số trong
    một màn hình là một lỗi chờ xảy ra.

    Ba kết quả, cố ý KHÔNG gộp (PHB-05 §7/§14):

        rỗng      ⟹ `None`  — "gỡ target", tức là CHƯA THIẾT LẬP.
        `>= 0`    ⟹ `Decimal` — kể cả `0`, và `0` KHÔNG phải rỗng.
        còn lại   ⟹ `InvalidTargetError` — âm, hoặc không phải số.

    `0` và rỗng là hai câu khác nhau: "Owner đặt target bằng không" và "Owner
    chưa đặt target". Cả hai dẫn tới `So target = N/A` trên màn hình, nhưng
    dẫn tới hai CÂU khác nhau và hai trạng thái khác nhau trong dữ liệu —
    trộn chúng lại là mất khả năng phân biệt "đã quyết" với "chưa quyết".

    Đơn vị luôn là VND nguyên. Sổ cũ viết Target theo NGHÌN ĐỒNG và chính
    workbook đó mang cả hai đơn vị cho cùng một con số (`Summary 2026!M11`
    so với `DataChart!AJ2`); kho lưu vì thế chỉ nhận một đơn vị.
    """
    text = (raw or "").strip().replace(" ", "").replace("\u00a0", "")
    if not text:
        return None
    text = text.replace(".", "").replace(",", ".")
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError):
        raise InvalidTargetError(
            f"Target {raw!r} không phải một số hợp lệ."
        ) from None
    if value < 0:
        raise InvalidTargetError("Target không được âm.")
    return value


def parse_target_period(raw_year, raw_month) -> tuple[int, int]:
    """`(năm, tháng)` của một Target, hoặc `InvalidTargetPeriodError`.

    Target được khoá theo KỲ BÁO CÁO, nên một kỳ không hợp lệ không có chỗ
    nào để lưu. Từ chối ở đây thay vì để `CheckConstraint` của database ném
    ra một lỗi mà người dùng không đọc được.
    """
    try:
        year, month = int(raw_year), int(raw_month)
    except (TypeError, ValueError):
        raise InvalidTargetPeriodError(
            "Target phải gắn với một tháng cụ thể."
        ) from None
    if not 1 <= month <= 12 or year < 1:
        raise InvalidTargetPeriodError(
            f"Kỳ {raw_year!r}-{raw_month!r} không phải một tháng thật.")
    return year, month


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class BusinessDecisionStore:
    """Đọc/ghi bốn bảng quyết định của Owner trên CÙNG engine history."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    @property
    def engine(self) -> Engine:
        return self._engine

    # --- giá nhập ------------------------------------------------------

    def set_purchase_price(
        self,
        *,
        order_key: str,
        product_key: str,
        occurrence_index: int,
        price: Decimal,
        auto_price: Optional[Decimal],
        entered_by: Optional[str] = None,
        entered_at: Optional[str] = None,
    ) -> str:
        """Ghi giá nhập KPI của một dòng; trả về provenance đã lưu.

        `auto_price` là giá AUTO mà tầng gọi vừa ĐỌC THẤY trên chính dòng đó.
        Nó quyết định provenance, và quyết định đó không thể bị người gọi tự
        khai:

            auto_price is None  ⟹  MANUAL           (không có gì để ghi đè)
            auto_price có giá trị ⟹ MANUAL_OVERRIDE (đang thay một số đã có)

        `DEC-PHB02-02` §3: một override KHÔNG BAO GIỜ được ghi thành `AUTO`.
        Nhập lại đúng bằng giá AUTO vẫn là `MANUAL_OVERRIDE` — Owner đã ra một
        quyết định, và xoá dấu vết quyết định đó là nói dối về nguồn con số.
        """
        provenance = (PURCHASE_PROVENANCE_MANUAL if auto_price is None
                      else PURCHASE_PROVENANCE_MANUAL_OVERRIDE)
        values = {
            "purchase_price": price, "provenance": provenance,
            "auto_price_at_entry": auto_price,
            "entered_at": entered_at or _now(), "entered_by": entered_by,
        }
        keys = {"order_key": order_key, "product_key": product_key,
                "occurrence_index": occurrence_index}
        self._upsert(kpi_purchase_price_override, keys, values)
        return provenance

    def clear_purchase_price(
        self, *, order_key: str, product_key: str, occurrence_index: int
    ) -> None:
        """Gỡ override, trả dòng về đúng giá trị pipeline đã tính.

        Đây KHÔNG phải "undo lịch sử" — nó là cách duy nhất để một lần nhập
        nhầm không mắc kẹt vĩnh viễn. Sau khi gỡ, dòng lại mang provenance
        `AUTO` (hoặc `PENDING` nếu pipeline chưa phân giải được).
        """
        table = kpi_purchase_price_override
        self._execute(delete(table).where(
            table.c.order_key == order_key,
            table.c.product_key == product_key,
            table.c.occurrence_index == occurrence_index,
        ))

    def purchase_price_overrides(self) -> dict[tuple[str, str, int], dict]:
        """Toàn bộ override, khoá theo `(order_key, product_key, occurrence)`.

        Đọc một lần rồi map trong Python thay vì JOIN: số override là số dòng
        Owner đã đích thân sửa — luôn nhỏ so với số dòng của sổ — và cách này
        giữ được `business_queries` ở đúng một câu truy vấn cho mỗi bảng.
        """
        table = kpi_purchase_price_override
        rows = self._read(select(
            table.c.order_key, table.c.product_key, table.c.occurrence_index,
            table.c.purchase_price, table.c.provenance,
            table.c.auto_price_at_entry, table.c.entered_at, table.c.entered_by,
        ))
        return {
            (row["order_key"], row["product_key"], int(row["occurrence_index"])): row
            for row in rows
        }

    # --- phân loại Gia dụng --------------------------------------------

    def set_product_group(
        self,
        *,
        product_key: str,
        product_group: str,
        product_label: Optional[str] = None,
        classified_by: Optional[str] = None,
        classified_at: Optional[str] = None,
    ) -> None:
        """Ghi quyết định phân loại của một mặt hàng.

        `DEC-PHB02-05` cấm suy ra Gia dụng từ TÊN HÀNG. Module này vì vậy
        không có bất kỳ luật nào đọc `product_label` — nhãn chỉ để hiển thị
        lại cho người tick, và giá trị `product_group` luôn đến từ một lựa
        chọn tường minh của con người ở tầng route.
        """
        if product_group not in PRODUCT_GROUPS:
            raise InvalidProductGroupError(
                f"Nhóm sản phẩm {product_group!r} không hợp lệ."
            )
        self._upsert(
            product_group_classification, {"product_key": product_key},
            {"product_group": product_group, "product_label": product_label,
             "classified_at": classified_at or _now(),
             "classified_by": classified_by},
        )

    def clear_product_group(self, *, product_key: str) -> None:
        """Gỡ phân loại; mặt hàng trở lại giá trị pipeline đã tính."""
        table = product_group_classification
        self._execute(delete(table).where(table.c.product_key == product_key))

    def product_groups(self) -> dict[str, dict]:
        table = product_group_classification
        return {
            row["product_key"]: row
            for row in self._read(select(
                table.c.product_key, table.c.product_group,
                table.c.product_label, table.c.classified_at,
                table.c.classified_by,
            ))
        }

    # --- gán nhân viên (OD-5) -------------------------------------------

    def set_employee(
        self,
        *,
        order_key: str,
        product_key: str,
        occurrence_index: int,
        employee: str,
        employee_group: Optional[str] = None,
        source_employee: Optional[str] = None,
        assigned_by: Optional[str] = None,
        assigned_at: Optional[str] = None,
    ) -> None:
        """Gán dòng hàng này cho một nhân viên, KHÔNG đụng bằng chứng gốc.

        `source_employee` là giá trị mà pipeline ĐANG nói tại thời điểm gán —
        thường là `None` (đó chính là lý do dòng nằm trong nhóm "Chưa xác định
        nhân viên"). Lưu nó lại để sau này còn trả lời được câu "sổ ghi ai, và
        Owner sửa thành ai" mà không phải mở lại lịch sử chạy máy.

        Tên rỗng bị TỪ CHỐI: một bản ghi gán mang tên rỗng sẽ trông như dòng
        đã được sửa xong trong khi nó vẫn vô chủ, và làm ô đếm "chưa xác định
        nhân viên" nói dối — đúng lớp lỗi mà `B02` là ví dụ.
        """
        name = (employee or "").strip()
        if not name:
            raise InvalidEmployeeError("Chưa chọn nhân viên.")
        keys = {"order_key": order_key, "product_key": product_key,
                "occurrence_index": occurrence_index}
        self._upsert(employee_attribution_override, keys, {
            "employee_normalized": name,
            "employee_group": employee_group,
            "source_employee_at_entry": source_employee,
            "assigned_at": assigned_at or _now(),
            "assigned_by": assigned_by,
        })

    def clear_employee(
        self, *, order_key: str, product_key: str, occurrence_index: int
    ) -> None:
        """Gỡ việc gán; dòng trở lại đúng nhân viên mà pipeline đã đọc."""
        table = employee_attribution_override
        self._execute(delete(table).where(
            table.c.order_key == order_key,
            table.c.product_key == product_key,
            table.c.occurrence_index == occurrence_index,
        ))

    def employee_overrides(self) -> dict[tuple[str, str, int], dict]:
        """Toàn bộ lần gán, khoá theo `(order_key, product_key, occurrence)`.

        Cùng cách đọc-một-lần-rồi-map như `purchase_price_overrides`: số dòng
        Owner đích thân gán luôn nhỏ so với sổ, và cách này giữ tầng truy vấn
        ở đúng một câu cho mỗi bảng.
        """
        table = employee_attribution_override
        rows = self._read(select(
            table.c.order_key, table.c.product_key, table.c.occurrence_index,
            table.c.employee_normalized, table.c.employee_group,
            table.c.source_employee_at_entry, table.c.assigned_at,
            table.c.assigned_by,
        ))
        return {
            (row["order_key"], row["product_key"], int(row["occurrence_index"])): row
            for row in rows
        }

    # --- Target tháng của nhân viên (PHB-05, DEC-PHB02-06) ---------------

    def set_employee_target(
        self,
        *,
        year: int,
        month: int,
        employee_key: str,
        target_vnd: Decimal,
        updated_by: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> None:
        """Đặt Target VND của MỘT nhân viên trong MỘT tháng.

        Khoá là `(năm, tháng, nhân viên)` và KHÔNG có `snapshot_id` nào trong
        đó. Đó là toàn bộ cơ chế giữ lời hứa của PHB-05 §11: nạp lại sổ kế
        toán dựng ra snapshot mới, version mới, `id` mới — nhưng không chạm
        được vào một dòng nào ở đây, vì không dòng nào ở đây trỏ tới chúng.

        Ghi đè tại chỗ (UPSERT), không append version: `DEC-PHB02-06` yêu cầu
        Target sửa được, KHÔNG yêu cầu lịch sử các lần sửa, và PHB-05 §12 cấm
        dựng version history cho nó.
        """
        name = (employee_key or "").strip()
        if not name:
            raise InvalidEmployeeError("Chưa chọn nhân viên cho Target.")
        if target_vnd is None or target_vnd < 0:
            raise InvalidTargetError("Target không được âm.")
        if not 1 <= int(month) <= 12:
            raise InvalidTargetPeriodError(
                f"Tháng {month!r} không phải một tháng thật.")
        self._upsert(
            employee_target,
            {"year": int(year), "month": int(month), "employee_key": name},
            {"target_vnd": target_vnd, "updated_at": updated_at or _now(),
             "updated_by": updated_by},
        )

    def clear_employee_target(
        self, *, year: int, month: int, employee_key: str
    ) -> None:
        """Gỡ Target của một nhân viên trong một tháng — về CHƯA THIẾT LẬP.

        XOÁ DÒNG, không ghi `0`: `0` là một target Owner đã cố ý đặt, còn
        không có dòng là chưa đặt gì. Ghi `0` để "gỡ" sẽ xoá đúng sự phân biệt
        mà PHB-05 §7 bắt phải giữ.
        """
        table = employee_target
        self._execute(delete(table).where(
            table.c.year == int(year),
            table.c.month == int(month),
            table.c.employee_key == (employee_key or "").strip(),
        ))

    def employee_targets(self, *, year: int, month: int) -> dict[str, dict]:
        """Target đã đặt của MỘT tháng, khoá theo tên nhân viên.

        Chỉ đọc đúng kỳ đang xem: Target của 09/2026 và của 08/2026 là hai
        dòng khác nhau, và một truy vấn không lọc kỳ sẽ để tháng này đè lên
        tháng kia (PHB-05 §4).

        Nhân viên KHÔNG có dòng ⟹ vắng mặt trong dict. "Chưa thiết lập" được
        biểu diễn bằng sự VẮNG MẶT, không bằng một giá trị `0` giả.
        """
        table = employee_target
        rows = self._read(select(
            table.c.year, table.c.month, table.c.employee_key,
            table.c.target_vnd, table.c.updated_at, table.c.updated_by,
        ).where(table.c.year == int(year), table.c.month == int(month)))
        return {row["employee_key"]: row for row in rows}

    # --- hạ tầng --------------------------------------------------------

    def _upsert(self, table, keys: dict, values: dict) -> None:
        """UPDATE nếu khoá đã có, ngược lại INSERT — trong MỘT transaction.

        Không dùng cú pháp `ON CONFLICT` riêng của dialect: repo này chạy
        SQLite ở local/test và PostgreSQL ở production (ADR-108), và một đường
        ghi có hai phương ngữ là một đường ghi chỉ được kiểm ở một nửa.
        """
        conditions = [table.c[name] == value for name, value in keys.items()]
        try:
            with self._engine.begin() as connection:
                existing = connection.execute(
                    select(table.c[next(iter(keys))]).where(*conditions)
                ).first()
                if existing is None:
                    connection.execute(insert(table).values(
                        origin=ORIGIN_PIPELINE, **keys, **values))
                else:
                    connection.execute(
                        update(table).where(*conditions).values(**values))
        except SQLAlchemyError as exc:
            raise HistoryUnavailableError(str(exc)) from exc

    def _execute(self, statement) -> None:
        try:
            with self._engine.begin() as connection:
                connection.execute(statement)
        except SQLAlchemyError as exc:
            raise HistoryUnavailableError(str(exc)) from exc

    def _read(self, statement) -> list[dict]:
        try:
            with self._engine.connect() as connection:
                return [dict(row._mapping) for row in connection.execute(statement)]
        except SQLAlchemyError as exc:
            raise HistoryUnavailableError(str(exc)) from exc


__all__ = [
    "BusinessDecisionStore", "InvalidEmployeeError", "InvalidProductGroupError",
    "InvalidPurchasePriceError", "InvalidTargetError",
    "InvalidTargetPeriodError", "PRODUCT_GROUPS", "parse_purchase_price",
    "parse_target", "parse_target_period",
]
