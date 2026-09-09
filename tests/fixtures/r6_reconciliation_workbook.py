"""R6 — sổ TỔNG HỢP dựng theo ĐÚNG hình dạng vector đối soát của Owner.

`DEC-108`: sổ kế toán thật (`So_chi_tiet_ban_hang.xlsx`) KHÔNG BAO GIỜ được
commit và không có mặt trong môi trường này. Mọi dòng dưới đây do script sinh
ra — không dòng nào lấy từ một bản ghi khách hàng thật.

## Vì sao file này tồn tại

`scripts/r6_book_reconciliation.py` là công cụ đối soát sổ thật. Không có sổ
thật thì công cụ ấy chưa được chứng minh là đo ĐÚNG tám con số Owner đưa ra —
và một công cụ đối soát chưa được đối soát thì không nói lên điều gì.

File này đóng đúng khoảng trống đó: nó dựng một sổ có CHÍNH XÁC tám đặc trưng
ấy, để `tests/test_r6_book_reconciliation.py` chạy công cụ trên nó và đo rằng
công cụ trả về đúng tám con số. Khi sổ thật được đưa vào, công cụ hoặc khớp,
hoặc chỉ ra ĐÚNG ô nào lệch — và người đọc biết công cụ không phải là chỗ sai.

```text
466 dòng nguồn                       345 BH khác nhau
338 BH có doanh thu sau CK dương     tổng SL 626
doanh số bán   4.500.085.001         chiết khấu       1.550.000
doanh thu sau CK 4.498.535.001       85 BH có ít nhất hai dòng
```

## Hình dạng được dựng ra sao

```text
260 BH một dòng          260 dòng
 49 BH hai dòng           98 dòng
 36 BH ba dòng           108 dòng
---------------------------------
345 BH                   466 dòng      85 BH có >= 2 dòng (49 + 36)
```

Bảy trong số các BH một dòng là hàng tặng giá 0 (`OD-4` — giá 0 là giá bán
THẬT), nên chúng có doanh thu sau CK bằng 0 và KHÔNG được đếm là "dương":
`345 − 7 = 338`. Đó cũng là lý do bảy dòng ấy có mặt: chúng làm cho phép đếm
"doanh thu dương" thật sự phải phân biệt `> 0` với `>= 0`.

Chiết khấu 1.550.000 nằm trên ĐÚNG ba dòng (1.000.000 + 500.000 + 50.000) để
một lỗi cộng chiết khấu hai lần lộ ra ngay ở con số tổng.

Dòng CUỐI CÙNG mang phần dư của doanh số bán, nên tổng khớp tới từng đồng
thay vì gần đúng.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import openpyxl

from tests.fixtures.synthetic_workbook import HEADER

#: Vector kỳ vọng — cùng tám con số mà brief R6 đưa ra, viết một lần ở đây và
#: import lại ở test để không có bản sao thứ hai trôi khỏi bản này.
EXPECTED = {
    "source_rows": 466,
    "orders": 345,
    "positive_revenue_orders": 338,
    "total_quantity": Decimal("626"),
    "gross_before_discount": Decimal("4500085001"),
    "discount_total": Decimal("1550000"),
    "sales_revenue": Decimal("4498535001"),
    "multi_line_orders": 85,
}

SINGLE_LINE_ORDERS = 260
TWO_LINE_ORDERS = 49
THREE_LINE_ORDERS = 36
ZERO_REVENUE_ORDERS = 7

#: Ba dòng mang toàn bộ chiết khấu của sổ, theo chỉ số dòng (0-based).
DISCOUNTS = {3: Decimal("1000000"), 17: Decimal("500000"),
             120: Decimal("50000")}

#: Đơn giá nền. Con số cụ thể không quan trọng — điều quan trọng là nó cố
#: định, nên sổ sinh ra là XÁC ĐỊNH và hai lần chạy cho ra cùng một file.
BASE_PRICE = Decimal("7270000")

EMPLOYEES = ("Vũ Hạnh Ly 0868345633", "Lê Mạnh Hoàng 0865111533",
             "Tín Phát 0869931931", "Mr Vinh")


def _plan() -> list[dict]:
    """Kế hoạch từng dòng, TRƯỚC khi cân số dư — thuần, kiểm được."""
    rows: list[dict] = []
    order_number = 0

    def add(order_id: str, *, price: Decimal, quantity: Decimal):
        rows.append({"order_id": order_id, "price": price,
                     "quantity": quantity})

    for index in range(SINGLE_LINE_ORDERS):
        order_number += 1
        order_id = f"BH{order_number:05d}"
        # Bảy đơn hàng tặng: giá 0 là giá bán THẬT (`OD-4`), và doanh thu sau
        # CK của chúng bằng 0 nên chúng KHÔNG phải "doanh thu dương".
        gift = index < ZERO_REVENUE_ORDERS
        add(order_id, price=Decimal(0) if gift else BASE_PRICE,
            quantity=Decimal(1))
    for _ in range(TWO_LINE_ORDERS):
        order_number += 1
        order_id = f"BH{order_number:05d}"
        for _line in range(2):
            add(order_id, price=BASE_PRICE, quantity=Decimal(1))
    for _ in range(THREE_LINE_ORDERS):
        order_number += 1
        order_id = f"BH{order_number:05d}"
        for _line in range(3):
            add(order_id, price=BASE_PRICE, quantity=Decimal(1))

    # Tổng SL: 466 dòng × 1 = 466; cần thêm 160 để đạt 626. Nâng SL của 160
    # dòng CÓ GIÁ (không nâng dòng hàng tặng — nhân 0 với 2 vẫn là 0 và sẽ làm
    # con số SL đúng mà chẳng chứng minh được gì về phép nhân).
    remaining = int(EXPECTED["total_quantity"]) - len(rows)
    for row in rows:
        if remaining == 0:
            break
        if row["price"] == 0:
            continue
        row["quantity"] += Decimal(1)
        remaining -= 1
    assert remaining == 0, "không phân bổ hết số lượng"

    for index, discount in DISCOUNTS.items():
        rows[index]["discount"] = discount
    for row in rows:
        row.setdefault("discount", Decimal(0))

    # Dòng CUỐI mang phần dư để doanh số bán khớp tới từng đồng.
    gross = sum((row["price"] * row["quantity"] for row in rows), Decimal(0))
    last = rows[-1]
    gross -= last["price"] * last["quantity"]
    last["quantity"] = Decimal(1)
    last["price"] = EXPECTED["gross_before_discount"] - gross
    assert last["price"] > 0, "phần dư âm — kế hoạch cần chỉnh lại"
    return rows


def build_reconciliation_workbook(path: Path) -> Path:
    """Ghi sổ tổng hợp ra `path` và trả lại chính đường dẫn đó."""
    rows = _plan()
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "SỔ CHI TIẾT BÁN HÀNG"
    sheet.append(["SỔ CHI TIẾT BÁN HÀNG"])
    sheet.append(["Từ ngày 01/09/2026 đến ngày 30/09/2026"])
    sheet.append([])
    sheet.append(HEADER)
    sheet.append(["", "", "Diễn giải chung"])  # dòng 5 — bị bỏ qua, đúng layout
    for index, row in enumerate(rows):
        day = index % 28 + 1
        sheet.append([
            date(2026, 9, day), row["order_id"], "Bán hàng Khách Lẻ",
            f"Mặt hàng {index % 40:02d}", f"KH{index % 90:04d}",
            f"Khách {index % 90:04d}", f"{index % 90} Đường Test",
            f"09{index % 90:08d}",
            int(row["quantity"]), int(row["price"]),
            int(row["price"] * row["quantity"]), int(row["discount"]),
            EMPLOYEES[index % len(EMPLOYEES)], "Shipper", 0, None, None,
        ])
    workbook.save(path)
    return path


__all__ = ["EXPECTED", "build_reconciliation_workbook"]
