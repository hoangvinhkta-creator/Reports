"""Build a synthetic raw sales-book `.xlsx` matching the real file's layout.

DEC-108: the real `So_chi_tiet_ban_hang.xlsx` is never committed and is not
present in this environment. Every row here is invented for structural
coverage (multi-line orders, ADS keyword, employee default, discount,
unmapped employee, missing quantity) — none of it is derived from any real
customer record. Layout confirmed against the real file in
`docs/analysis/01_DATA_MAPPING.md` §1: header on row 4, row 5 skipped,
data from row 6.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import openpyxl

HEADER = [
    "Ngày", "Số BH", "Diễn giải", "Tên hàng trên chứng từ", "Mã khách hàng",
    "Tên KH", "Địa chỉ", "ĐT di động (Người liên hệ)", "SL", "Đơn giá",
    "Doanh số bán", "Chiết khấu", "NVBH", "Giao vận", "Lương chuyến",
    "Trường mở rộng chi tiết 1", "Lợi nhuận",
]

# (date, order_id, note, product, customer_code, customer, address, phone,
#  qty, unit_price, sales, discount, employee, shipper, trip_pay, imei, profit)
ROWS = [
    # BH0001 — Ly, đơn thường, không ADS.
    (date(2026, 1, 15), "BH0001", "Bán hàng Khách Lẻ A", "Máy giặt Test-1",
     "KH0001", "Khách Test A", "1 Đường Test", "0900000001", 1, 1_000_000,
     1_000_000, 0, "Vũ Hạnh Ly 0868345633", "Shipper A", 50_000, None, 100_000),

    # BH0002 — Hoàng, 2 dòng, dòng 2 có "ADS" -> cả đơn thành ADS.
    (date(2026, 1, 16), "BH0002", "Bán hàng Vanoka", "Máy lạnh Test-2",
     "KH0002", "Khách Test B", "2 Đường Test", "0900000002", 1, 2_000_000,
     2_000_000, 0, "Lê Mạnh Hoàng 0865111533", "Shipper B", 50_000, None, 200_000),
    (date(2026, 1, 16), "BH0002", "Đơn có ADS quảng cáo", "Tủ lạnh Test-3",
     "KH0002", "Khách Test B", "2 Đường Test", "0900000002", 1, 500_000,
     500_000, 0, "Lê Mạnh Hoàng 0865111533", "Shipper B", 0, None, 50_000),

    # BH0003 — Tín Phát, không có chữ ADS -> mặc định cấp nhân viên (DEC-109).
    (date(2026, 1, 17), "BH0003", "Bán hàng CÔNG TY TEST", "Bếp từ Test-4",
     "KH0003", "Công Ty Test", "3 Đường Test", "0900000003", 1, 3_000_000,
     3_000_000, 0, "Tín Phát 0869931931", "Shipper C", 50_000, None, 300_000),

    # BH0004 — Ly, có chiết khấu (DEC-114): total_sales = 300000*2 - 50000.
    (date(2026, 1, 18), "BH0004", "Bán hàng Khách Lẻ D", "Bình nóng lạnh Test-5",
     "KH0004", "Khách Test D", "4 Đường Test", "0900000004", 2, 300_000,
     600_000, 50_000, "Vũ Hạnh Ly 0868345633", "Shipper D", 50_000, None, 40_000),

    # BH0005 — NVBH không khớp mapping nào -> phải bị flag unmapped, không bỏ.
    (date(2026, 1, 19), "BH0005", "Bán hàng Khách Lẻ E", "Quạt Test-6",
     "KH0005", "Khách Test E", "5 Đường Test", "0900000005", 1, 500_000,
     500_000, 0, "Người Lạ Test 0900000009", "Shipper E", 50_000, None, 50_000),

    # BH0006 — Mr Vinh -> Nội thành, PERSONAL qua mặc định hệ thống.
    (date(2026, 1, 20), "BH0006", "Bán hàng Khách Lẻ F", "Tivi Test-7",
     "KH0006", "Khách Test F", "6 Đường Test", "0900000006", 1, 4_000_000,
     4_000_000, 0, "Mr Vinh", "Shipper F", 50_000, None, 400_000),

    # BH0007 — thiếu SL -> total_sales phải là None, không phải 0.
    (date(2026, 1, 21), "BH0007", "Bán hàng Khách Lẻ G", "Lò vi sóng Test-8",
     "KH0007", "Khách Test G", "7 Đường Test", "0900000007", None, 700_000,
     None, 0, "Phước Thắng 0865909022", "Shipper G", 50_000, None, None),
]


def build_synthetic_workbook(path: Path) -> None:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "SỔ CHI TIẾT BÁN HÀNG"

    sheet.append(["SỔ CHI TIẾT BÁN HÀNG"])
    sheet.append(["Từ ngày 01/01/2026 đến ngày 31/01/2026"])
    sheet.append([])
    sheet.append(HEADER)
    sheet.append(["", "", "Diễn giải chung"])  # row 5 — secondary header, skipped
    for row in ROWS:
        sheet.append(list(row))

    workbook.save(path)
