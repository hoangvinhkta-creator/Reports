# R6 — EXECUTION BRIEF: Dashboard phân tích kinh doanh

Artifact Type:
EXECUTION BRIEF (hợp đồng phạm vi + quyết định nghiệp vụ đã freeze cho `R6`).

Status:
`IMPLEMENTED` — xem `docs/tasks/R6-dashboard-phan-tich-kinh-doanh.md` cho
Checklist và trạng thái từng check.

Authority:
Brief `R6 — Dashboard phân tích kinh doanh` do Owner ban hành 2026-09-09.
Quyết định chiến thuật: `PROJECT/PROJECT_DECISIONS.md` → `DEC-207`.

Session:
`docs/sessions/S143-r6-dashboard-phan-tich.md`.

Nền đã merge (xác nhận bằng `git merge-base --is-ancestor`):

```text
Tracking  main @ 66787c0fb0d867a308c632e7f163cddd0c9dd0f2
          chứa R5.1 taxonomy merge dc9891087687f25b6f92804f46eba2628ebe788b
Reports   claude/extract-upload-repo-gq2ws4 @ 05f2b443e66ee4702d03c003d5f1f960b5765f8d
          chứa R5.1 taxonomy merge a59936ce497ddcc9fb63a87dd0524729931a83f9
```

---

## 0. Điều kiện chặn merge/deploy, nói TRƯỚC mọi thứ khác

`CHECK-R51-26` (Owner nghiệm thu `R5.1` trên production) **VẪN
`NOT_TESTED`**. Điều đó **KHÔNG chặn** việc viết và kiểm chứng `R6` — `R6`
đọc hợp đồng metadata đã merge trên nhánh mặc định của cả hai repo, và mọi
kiểm chứng của nó chạy trên chính hợp đồng ấy.

Điều đó **CHẶN merge/deploy `R6` lên production** cho tới khi:

1. Owner nghiệm thu `R5.1` trên dữ liệu thật (`CHECK-R51-26` → `PASS`), và
2. `R6` qua Independent Review (`CHECK-R6-31`).

Lý do không phải thủ tục: bảng "Nhóm hàng" và bảng "Hãng" của `R6` gộp TIỀN
theo đúng những nhãn mà `CHECK-R51-26` còn chưa xác nhận là đúng trên dữ liệu
thật. Đưa `R6` lên production trước sẽ biến một nhãn chưa nghiệm thu thành
một cơ cấu doanh thu mà Owner đọc để ra quyết định mua hàng.

---

## 1. Nguồn và bất biến tiền

```text
NGUỒN DUY NHẤT   PeriodData hiệu lực của R3–R5 (app/web/business_service.py)
                 — gồm quyết định Owner, dòng bị tạm loại, mapping, giá nhập
                 và nhân viên đã xác nhận.
CẤM              đọc thẳng Excel hoặc ImportResult để tính dashboard.
Excel gốc        chỉ dùng để import, đối soát và drill-down.
Doanh thu        BusinessLine.total_sales — KHÔNG tính lại
                 `sell_price × quantity − discount`.
Chiết khấu       BusinessLine.discount, cộng ĐÚNG MỘT LẦN ở cấp dòng.
KHÔNG ĐỔI        MIN theo ngày bán · giá nhập · lợi nhuận · coverage ·
                 fingerprint · period lock · target engine.
```

`Doanh số bán` (trước chiết khấu) là con số **DẪN XUẤT** = doanh thu sau CK +
chiết khấu, và **chỉ** dùng để đối soát với cột cùng tên của sổ kế toán.
Không bảng, biểu đồ hay bucket nào cộng theo nó
(`dashboard_metrics.GROSS_DERIVED_NOTE`).

## 2. Khoá và metadata sản phẩm

```text
Khoá phân tích DUY NHẤT   product_key hiện hành — không khoá normalize thứ hai
Nhãn sản phẩm đã khớp     model_label (Tracking) → fallback mã Tracking
Hãng                      brand (Tracking)
Nhóm hàng                 category_label (Tracking)
```

Năm trạng thái "chưa xác định" đi vào **năm bucket RIÊNG**, mỗi bucket một lý
do và một chỗ sửa (`app/web/product_taxonomy.py`):

```text
UNRESOLVED       chưa khớp mã           → phân loại trên bảng kê nhân viên
CONFLICT         hai nguồn chỏi nhau    → chọn lại (R2 §4.2)
STALE_TARGET     mã đã khớp biến mất    → khớp lại, KHÔNG xếp ngành hàng
OUT_OF_CATALOG   đã xác nhận ngoài bảng giá → không phải việc phải sửa
METADATA_ABSENT  đã khớp, Tracking chưa xếp → sửa BÊN TRACKING
```

Không nhánh nào suy hãng/nhóm hàng từ tên thô. Canonical taxonomy hiện hành
thuộc **Tracking** (`DEC-205`/`DEC-206`), Reports không giữ bản sao:

```text
Máy lạnh / Điều hòa / Điều hoà  →  Điều hoà
TV / Ti vi / Tivi               →  Tivi
Máy giặt sấy                    →  Máy giặt
```

## 3. Phạm vi thời gian

Mỗi màn hình áp dụng **ĐÚNG MỘT** phạm vi: kỳ có sẵn **hoặc** `Từ ngày`–`Đến
ngày`. Hai phạm vi không bao giờ được cộng gộp hay lấy phần chung
(`app/modules/reporting/analysis_range.py`). Một khoảng ngày không dùng được
bị TỪ CHỐI kèm lý do hiển thị, không âm thầm thành một phạm vi khác.

Phạm vi `CUSTOM` mang `period = None`, nên `PeriodData.closed` là `None`: một
khoảng ngày tự chọn KHÔNG mượn trạng thái chốt kỳ của tháng nào.

Engine thời gian dùng lại nguyên vẹn `app/web/revenue_timeline.py` của `R5`:
30 ngày · 12 tuần · 12 tháng · 8 quý, so với cửa sổ liền trước cùng độ dài.
`R6` bổ sung series `orders` trên **đúng các bucket đó** bằng cách dựng
`Point`/`PairedSeries` của `R5` với số đơn ở trường `revenue` — không một
dòng nào của `revenue_timeline` bị sửa.

**Một đơn thuộc đúng một mốc**: gán vào NGÀY NHỎ NHẤT trong các dòng hiệu lực
của nó. Bất biến kiểm được ở CẢ NĂM mức gộp:

```text
Σ(số đơn của mọi mốc)  +  orders_without_date  ==  tổng số đơn của phạm vi
```

`orders_with_multiple_sale_dates` đếm riêng các đơn có dòng ở nhiều ngày.

## 4. Basket — bốn chỉ tiêu, KHÔNG gộp

```text
multi_line_orders                  >= 2 DÒNG hiệu lực
multi_product_orders               >= 2 product_key, chỉ SALE + ACCESSORY_GIFT
multi_merchandise_category_orders  >= 2 bucket nhóm hàng hoá; loại FEE,
                                   DISCOUNT, RETURN_CANCEL, UNDECIDED_DOCUMENT
service_attachment_orders          có hàng hoá VÀ có FEE/dịch vụ
```

- Cặp sản phẩm dùng **set** `product_key` trong từng đơn — mã lặp hai dòng chỉ
  tính một lần và không tự tạo cặp.
- Cặp nhóm hàng dùng **set** `category_label`; bucket "chưa xác định" là một
  bucket THẬT và không làm mất tiền.
- `pair_orders` = số đơn chứa cả A và B.
- `attachment A→B = pair_orders / orders_with_A`; `B→A` dùng **mẫu số riêng**.
- `pair_revenue` cộng TOÀN BỘ doanh thu hiệu lực của đơn, mỗi đơn đúng một
  lần — và vì thế KHÔNG cộng lại thành doanh thu kỳ.
- Basket theo sản phẩm mặc định chỉ hiện support ≥ 2; Basket theo nhóm hiện
  toàn bộ nhưng LUÔN ghi support ra cột.
- FEE/dịch vụ KHÔNG làm tăng multi-merchandise-category, nhưng có ô attachment
  riêng (`service_attachment_orders`).

## 5. Năm package — mã đã triển khai

| Package | Nội dung | File |
|---|---|---|
| 1 | Aggregate nền + hợp đồng filter | `app/modules/reporting/dashboard_metrics.py`, `app/modules/reporting/analysis_range.py` |
| 2 | Tổng quan + hai biểu đồ hai cửa sổ | `app/web/server.py` (`analytics_overview`), `business_presentation.paired_count_chart` |
| 3 | Mặt hàng · Nhóm hàng · Hãng | `app/modules/reporting/product_metrics.py`, `app/web/product_taxonomy.py` |
| 4 | Nhân viên (lát `for_employee`) | `app/web/server.py` (`analytics_employee`) |
| 5 | Basket + drill-down | `app/modules/reporting/basket_metrics.py`, `app/web/server.py` (`analytics_basket`, `analytics_drilldown`) |

Trình bày: `app/web/dashboard_presentation.py` + năm template
`kinh_doanh_phan_tich*.html` và `_r6_bits.html`.

**KHÔNG có**: migration, bảng mới, warehouse, materialized view, external API,
route GHI, product key thứ hai, engine thời gian thứ hai, taxonomy thứ hai,
store quyết định thứ hai. `alembic` giữ nguyên một head của `R3`.

## 6. Hàng rào dữ liệu của drill-down

Bảng kê drill-down hiện ĐÚNG bốn cột: Số BH · ngày bán · nhân viên · mặt hàng,
cùng nhãn phạm vi lọc đang áp dụng. Nó KHÔNG mở thêm một trường khách hàng
nào — dict trả về của `dashboard_presentation.drilldown_rows` chỉ có bốn khoá,
nên ràng buộc này đúng theo CẤU TẠO chứ không theo lời hứa, kể cả khi
`PeriodData.details` mang sẵn tên/SĐT/địa chỉ cho bảng kê nghiệp vụ
(`DEC-PHB02-08`).

## 7. Giới hạn chất lượng đã áp dụng

Chỉ repair bắt buộc với lỗi có thể làm **sai tổng tiền, sai số đơn, mất
persistence/audit, rò dữ liệu, hoặc gộp sai khó phát hiện**. Các ca hiếm, tác
động nhỏ và dễ thấy khi đối chiếu thủ công chỉ làm bucket `Chưa xác định` được
ghi thành `ACCEPTED_RISK` kèm điều kiện kích hoạt — xem
`docs/tasks/R6-dashboard-phan-tich-kinh-doanh.md` §6.

## 8. Trạng thái kết thúc phiên triển khai

```text
R6                     IMPLEMENTED
CHECK-R6-01 … -29      PASS (E1)
CHECK-R6-30            NOT_TESTED — đối soát trên SỔ THẬT của Owner
CHECK-R6-31            NOT_TESTED — Independent Review
CHECK-R6-32            NOT_TESTED — Owner Acceptance
Merge / PR / deploy    KHÔNG thực hiện trong phiên triển khai
```
