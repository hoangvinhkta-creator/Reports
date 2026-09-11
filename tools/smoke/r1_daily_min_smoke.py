"""SMOKE R1 (bước 2/2) — ảnh chụp Tracking → Reports → giá nhập → lợi nhuận.

Bước 1/2 nằm ở repo Tracking: `kiem/smoke/xuat-thang-min.mjs` sinh ra một ảnh
chụp `daily-min-v1` cho cả tháng 09/2026 bằng CHÍNH mã Tracking thật. Script
này nạp ảnh chụp ấy qua ĐÚNG loader production và chạy đường nhập sổ thật.

Kịch bản nghiệp vụ được dựng đúng như Owner mô tả: **đơn bán 03/09, sổ nạp
30/09**. Hai cái bẫy được cài sẵn để một lỗi im lặng phải lộ ra thành con số:

* Ảnh chụp CÓ giá của ngày 30/09 (5.200 nghìn). Nhánh nào lấy "bản mới nhất"
  sẽ ra 5.200.000 thay vì 6.800.000.
* Nguồn lịch sử `tp/ton` cũ CÓ MẶT và CÓ GIÁ (4.444 nghìn) cho đúng những mã
  ấy. Nhánh nào rơi về nguồn cũ sẽ ra 4.444.000.

Cả hai con số sai đều "hợp lệ" về kiểu và đi lọt mọi phép nhân — đó chính là
lớp lỗi bộ smoke này tồn tại để bắt.

Script CỐ Ý dùng lại bộ khung của `tests/test_daily_min_vertical.py`
(`build`/`run`/`write_sales`): smoke và bộ kiểm phải đi trên cùng một đường
production, không được phép trôi ra khỏi nhau theo thời gian.

Chạy (từ gốc repo Reports):
    python tools/smoke/r1_daily_min_smoke.py <file-capture.json> [thư-mục-tạm]

Thoát 0 nếu mọi khẳng định PASS, 1 nếu có mục FAIL.
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.modules.domain.models import (  # noqa: E402
    PRICE_SOURCE_PENDING,
    PRICE_SOURCE_TRACKING_DAILY_MIN,
)
from tests.test_daily_min_vertical import (  # noqa: E402
    ROWS,
    build,
    lines_by_order,
    record_for,
    run,
    write_sales,
)

NGAY_BAN = date(2026, 9, 3)

_ok = True


def kiem(nhan: str, dieu_kien: bool) -> None:
    global _ok
    _ok = _ok and bool(dieu_kien)
    print(("  PASS  " if dieu_kien else "  FAIL  ") + nhan)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    capture = Path(argv[1])
    tmp = Path(argv[2]) if len(argv) > 2 else Path(tempfile.mkdtemp(prefix="smoke-r1-"))
    tmp.mkdir(parents=True, exist_ok=True)

    payload = json.loads(capture.read_text(encoding="utf-8"))
    print(f"CAPTURE  id={payload['capture_id']} captured_at={payload['captured_at']} "
          f"status={payload['capture_status']}")
    print(f"SỔ BÁN   ngày bán = {NGAY_BAN}, kỳ sổ 01/09–30/09 (nạp cuối tháng)\n")

    comp = build(tmp, daily_min=capture)  # lịch sử tp/ton cũ = 4.444 nghìn, CÓ MẶT
    result = run(write_sales(tmp / "sales.xlsx", ROWS, day=NGAY_BAN), comp)
    lines = lines_by_order(result)

    for order_id, ten, *_ in ROWS:
        line = lines[order_id][0]
        rec = record_for(comp, order_id)
        dm = rec.daily_min_resolution
        print(f"[{order_id}] {ten}")
        print(f"   giá nhập kế toán = {line.accounting_purchase_price!r}   "
              f"lợi nhuận = {line.accounting_profit!r}")
        print(f"   price_source     = {line.price_source}   rule = {rec.rule.value}   "
              f"reason = {rec.reason.value if rec.reason else None}")
        prov = dm.provenance
        if prov is not None:
            print(f"   provenance       = sale_date={prov.sale_date} "
                  f"observed={prov.observed_on} carried_from={prov.carried_from} "
                  f"day_status={prov.day_status.value}")
            print(f"                      nguồn={list(prov.min_sources)} "
                  f"raw={prov.raw_value_thousand_vnd} nghìn → "
                  f"{prov.resolved_price_vnd} VND rv={prov.rule_version} "
                  f"fp={prov.source_fingerprint}")
            print(f"                      capture_id="
                  f"{rec.evidence.tracking_daily_min_capture_id}")
        else:
            print(f"   provenance       = (không có bản ghi giá) lý do={dm.reason.value}")
        print()

    print("=== KHẲNG ĐỊNH SMOKE ===")

    a = lines["BH7001"][0]
    kiem("A. đơn 03/09 nạp 30/09 → 6.800.000 (giá NGÀY BÁN)",
         a.accounting_purchase_price == Decimal("6800000"))
    kiem("A. KHÔNG lấy giá hiện tại 30/09 (5.200.000)",
         a.accounting_purchase_price != Decimal("5200000"))
    kiem("A. KHÔNG lấy giá ngày 04/09 (6.000.000)",
         a.accounting_purchase_price != Decimal("6000000"))
    kiem("A. KHÔNG rơi về lịch sử tp/ton cũ (4.444.000)",
         a.accounting_purchase_price != Decimal("4444000"))
    kiem("A. nguồn thắng là NCC Tuấn Ngoan",
         list(record_for(comp, "BH7001").daily_min_resolution.provenance.min_sources)
         == ["SUPPLIER:Tuấn Ngoan"])
    kiem("A. nhãn nguồn = TRACKING_DAILY_MIN",
         a.price_source == PRICE_SOURCE_TRACKING_DAILY_MIN)

    b = lines["BH7002"][0]
    kiem("B. TON_KHO thắng → 5.000.000",
         b.accounting_purchase_price == Decimal("5000000"))
    kiem("B. nguồn thắng là INVENTORY:TON_KHO",
         list(record_for(comp, "BH7002").daily_min_resolution.provenance.min_sources)
         == ["INVENTORY:TON_KHO"])

    c = lines["BH7003"][0]
    kiem("C. hết hàng → KHÔNG có giá (không phải 0)",
         c.accounting_purchase_price is None)
    kiem("C. sentinel 0 KHÔNG thành giá vốn 0",
         c.accounting_purchase_price != Decimal("0"))
    kiem("C. lợi nhuận KHÔNG bằng doanh thu",
         c.accounting_profit is None)
    kiem("C. Pending với lý do OUT_OF_STOCK",
         c.price_source == PRICE_SOURCE_PENDING
         and record_for(comp, "BH7003").daily_min_resolution.reason.value
         == "OUT_OF_STOCK")

    d = lines["BH7004"][0]
    kiem("D. thiếu lịch sử → Pending, lý do NO_DATA",
         d.accounting_purchase_price is None
         and record_for(comp, "BH7004").daily_min_resolution.reason.value == "NO_DATA")

    e = lines["BH7005"][0]
    kiem("E. NCC báo 150 bị luật lọc → 9.500.000, không phải 150.000",
         e.accounting_purchase_price == Decimal("9500000"))

    kiem("Kỳ 03/09 chỉ dùng ngày ĐÃ CHỐT → resolved_prices_are_final",
         comp.report.resolved_prices_are_final and comp.report.provisional_count == 0)
    # Cổng cấp KỲ khắt khe hơn: kỳ này còn TRK-C/TRK-D Pending nên nó CHƯA chốt
    # được, dù mọi giá đã resolve đều đến từ ngày đã chốt. Hai câu khác nhau.
    kiem("   nhưng kỳ CHƯA chốt được vì còn dòng Pending",
         not comp.report.period_is_final and comp.report.pending_count == 2)

    # Cùng ảnh chụp, đổi MỖI ngày bán: mốc mang qua, và ngày còn tạm.
    print("\n=== NGÀY BÁN KHÁC, CÙNG ẢNH CHỤP ===")
    for day, mong in ((date(2026, 9, 10), "6000000"), (date(2026, 9, 30), "5200000")):
        sub = tmp / day.isoformat()
        sub.mkdir(exist_ok=True)
        comp2 = build(sub, daily_min=capture)
        result2 = run(write_sales(sub / "s.xlsx", ROWS[:1], day=day), comp2)
        line2 = lines_by_order(result2)["BH7001"][0]
        prov2 = record_for(comp2, "BH7001").daily_min_resolution.provenance
        print(f"  bán {day} → {line2.accounting_purchase_price} VND  "
              f"observed={prov2.observed_on} carried_from={prov2.carried_from} "
              f"day_status={prov2.day_status.value} "
              f"giá_đã_chốt={comp2.report.resolved_prices_are_final} "
              f"kỳ_đã_chốt={comp2.report.period_is_final} "
              f"tạm={comp2.report.provisional_count}")
        kiem(f"   ngày bán {day} → {mong}",
             line2.accounting_purchase_price == Decimal(mong))
        if day == date(2026, 9, 10):
            kiem("   mốc 10/09 nói rõ nó được mang từ 04/09",
                 prov2.carried_from == date(2026, 9, 4)
                 and prov2.observed_on == date(2026, 9, 4))
        else:
            kiem("   ngày 30/09 còn PROVISIONAL → kỳ KHÔNG được coi là đã chốt",
                 not comp2.report.resolved_prices_are_final
                 and not comp2.report.period_is_final
                 and comp2.report.provisional_count == 1)

    print("\nKẾT QUẢ SMOKE:", "TẤT CẢ PASS" if _ok else "CÓ MỤC FAIL")
    return 0 if _ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
