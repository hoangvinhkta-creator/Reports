# R4 — Đặc tả chỉ tiêu của Báo cáo đánh giá

Tài liệu này là bản mô tả NGHIỆP VỤ của trang `/kinh-doanh/danh-gia`: mỗi ô
trên trang là con số gì, tính từ đâu, và khi nào nó KHÔNG có số.

Nó không thay bất kỳ hợp đồng nào đã freeze. Mọi chỉ tiêu cộng được vẫn do
`app/modules/reporting/business_metrics.py` quyết định; R4 chỉ đọc lại chúng
và thêm ba phép chia. Khi tài liệu này và mã nguồn nói khác nhau, mã nguồn
đúng và tài liệu này sai — hãy sửa tài liệu.

Nguồn: `app/modules/reporting/evaluation.py` (ngữ nghĩa) và
`app/web/evaluation_presentation.py` (câu chữ hiển thị).

---

## 0. Ba nguyên tắc chi phối toàn bộ trang

**`None` không bao giờ là `0`.** Một ô không có số hiện `—` kèm MỘT câu lý do.
Bất biến này được canh ở constructor (`evaluation.Kpi.__post_init__`): dựng
một chỉ tiêu vừa có số vừa có lý do, hoặc không có cả hai, là một `ValueError`
ngay lúc dựng chứ không phải một ô trống trên màn hình.

**Kết quả một phần không bao giờ là kết luận cả kỳ.** Lợi nhuận KPI, Biên KPI,
Lãi/đơn, DS quy đổi và % target đều chỉ có số khi coverage đạt **đúng 100 %**
(`Coverage.is_complete` — một phép SO BẰNG, không phải một ngưỡng phần trăm đã
làm tròn). Con số một phần vẫn hiện, nhưng ở dòng "Đã tính được…" cạnh
coverage, cỡ chữ nhỏ hơn, và luôn kèm câu "KHÔNG phải kết quả cả kỳ".

**Trang này chỉ ĐỌC.** Không route POST, không chạm `business_store`, không
migration. Mở trang không đổi một con số nào — có một bài test nói đúng câu đó
(`test_the_page_never_writes_anything`).

---

## 1. Tám chỉ tiêu đầu trang

Thứ tự đã freeze ở `evaluation.HEADLINE_ORDER`.

| Chỉ tiêu | Đơn vị | Nguồn/công thức | Khi không có số |
|---|---|---|---|
| Doanh thu bán hàng | VND | `BusinessTotals.sales_revenue` — `Σ(giá bán × SL − chiết khấu)` | `NO_LINES` · `NO_REVENUE` |
| Số đơn | đơn | `BusinessTotals.orders` = `COUNT DISTINCT order_key` trong phạm vi | `NO_LINES` |
| SL đủ điều kiện KPI | cái | `BusinessTotals.qualifying_quantity` — `SUM(SL)` khi ĐƠN GIÁ > 1.000.000 | `NO_LINES` |
| Doanh thu/đơn | VND | Doanh thu ÷ Số đơn, cùng phạm vi | `NO_LINES` · `NO_ORDERS` · `NO_REVENUE` |
| Lợi nhuận KPI | VND | `BusinessTotals.official_kpi_profit` (đã qua cổng coverage) | `NO_LINES` · `PROFIT_NOT_OFFICIAL` |
| Biên KPI | % | LN KPI CHÍNH THỨC ÷ Doanh thu × 100 | `NO_LINES` · `PROFIT_NOT_OFFICIAL` · `NO_REVENUE` |
| Lãi/đơn | VND | LN KPI CHÍNH THỨC ÷ Số đơn | `NO_LINES` · `PROFIT_NOT_OFFICIAL` · `NO_ORDERS` |
| DS quy đổi | VND | `BusinessTotals.official_converted_sales` | `NO_LINES` · `CONVERTED_NOT_OFFICIAL` |

**Ba chỉ tiêu R4 thêm** là ba phép CHIA hai con số đã có (`revenue_per_order`,
`margin_percent`, `profit_per_order`), và cả ba đi qua đúng một hàm `_ratio`
nên không có nơi thứ hai để quên nhánh "mẫu số bằng 0".

**Biên KPI không cap và không kẹp.** Biên âm là một sự thật kế toán; biên trên
100 % xảy ra khi giá nhập bằng 0 theo chính sách. Cả hai hiện đúng như nó là.

**Số đơn KHÔNG cộng dọc được.** Một đơn có hai mặt hàng, hai nhân viên hay hai
sheet được đếm ở mỗi hàng nó xuất hiện. Vì vậy mọi hàng TỔNG của mọi bảng trên
trang lấy từ tổng của PHẠM VI, không bao giờ cộng cột.

### Mã lý do (tập ĐÓNG)

| Mã | Nghĩa | Việc phải làm |
|---|---|---|
| `NO_LINES` | Phạm vi chưa có dòng hàng nào | Nạp sổ, hoặc chọn kỳ/phạm vi khác |
| `NO_ORDERS` | Số đơn bằng 0 — không có mẫu số | Kiểm số chứng từ của các dòng |
| `NO_REVENUE` | Doanh thu chưa xác định hoặc bằng 0 | Kiểm dữ liệu bán của kỳ |
| `PROFIT_NOT_OFFICIAL` | Coverage < 100 % | Nhập nốt giá nhập cho các dòng còn thiếu |
| `CONVERTED_NOT_OFFICIAL` | Nền lợi nhuận chưa đủ | Như trên |

---

## 2. Đơn vị tiền

Mọi phép TÍNH chạy trên VND canonical. Chỉ tầng trình bày đổi sang **nghìn
đồng**, và mỗi ô tiền luôn mang số VND đầy đủ trong chú thích của chính nó
(`title`). Không có ô tiền nào trên trang thiếu đơn vị.

---

## 3. Target và tiến độ

### Phạm vi của target

Target chỉ tồn tại ở **nhân viên** (`employee_target`) hoặc **sheet nhóm**
(`group_target`). R4 KHÔNG tạo target mới và KHÔNG suy ra target cấp công ty:
phạm vi "Cả kỳ" không hiện ô target nào, và hàng TỔNG của bảng đơn vị báo cáo
để trống hai cột target. Cộng target của các đơn vị lên sẽ cho ra một con số
chưa ai đặt và không ai chịu trách nhiệm (`DEC-PHB02-08` §7).

### Công thức

```text
% target      = DS quy đổi CHÍNH THỨC / Target × 100      (không cap 100 %)
Còn thiếu     = Target − DS quy đổi CHÍNH THỨC            (0 khi đã đạt/vượt)
Ngày còn lại  = số ngày lịch SAU ngày đang xét, trong cùng tháng
Cần đạt/ngày  = Còn thiếu / Ngày còn lại                  (0 khi đã đạt)
```

### Năm lý do "không có % target"

| Mã | Nghĩa |
|---|---|
| `TARGET_UNSET` | Owner chưa đặt target cho phạm vi này |
| `TARGET_ZERO` | Owner đã đặt target, và đặt bằng 0 |
| `TARGET_NO_ACTUAL` | Chưa có DS quy đổi nào để so |
| `TARGET_ACTUAL_NOT_OFFICIAL` | Đã tính được MỘT PHẦN DS quy đổi, nhưng chưa được phép công bố |
| `TARGET_NO_DAYS_REMAINING` | Hết tháng — không còn ngày nào để chia phần còn thiếu |

Ba mã đầu là của `business_metrics` và giữ nguyên nghĩa. `TARGET_ACTUAL_NOT_
OFFICIAL` là mã R4 thêm, và nó lấp một khe chứ không lấy chỗ của mã nào: trước
đó "chưa bán được gì" và "đã bán, còn thiếu vài giá nhập" cùng ra
`TARGET_NO_ACTUAL`, trong khi việc phải làm của hai tình huống hoàn toàn khác
nhau. `TARGET_NO_DAYS_REMAINING` chỉ áp cho ô "Cần đạt mỗi ngày" và **không**
có nghĩa là đã đạt — đã đạt hay chưa là một câu độc lập.

### `as_of` và số ngày

```text
tháng đang chạy   as_of = HÔM NAY theo giờ Việt Nam (Asia/Ho_Chi_Minh)
tháng đã qua      as_of = ngày cuối tháng
tháng chưa tới    as_of = (không có)

Ngày đã trôi qua  = as_of.day        — TÍNH CẢ hôm nay
Ngày còn lại      = số ngày của tháng − as_of.day
```

"Tính cả hôm nay" là đúng quy ước `reporting_sheets.month_progress_percent`
§15 đã freeze: ngày hôm nay là một ngày bán hàng đang diễn ra.

Múi giờ nghiệp vụ là `Asia/Ho_Chi_Minh` — cùng vùng mà hợp đồng `daily-min-v1`
đã freeze cho ranh giới ngày của giá MIN. Ngày bán và ngày báo cáo phải cắt
theo cùng một ranh giới.

---

## 4. Run-rate

```text
Run-rate = (giá trị đến as_of / số ngày đã trôi qua) × số ngày trong tháng
```

Nhãn bắt buộc và không tắt được: **"Ước tính nếu tốc độ hiện tại giữ nguyên"**.
Đây KHÔNG phải dự báo, KHÔNG phải cam kết, và không mang bất kỳ mô hình, mùa
vụ hay nguyên nhân nào.

Bốn cửa từ chối, theo thứ tự:

| Mã | Khi nào |
|---|---|
| `RUNRATE_NOT_RUNNING` | Kỳ đã kết thúc — con số thật đã có, không ước tính |
| `RUNRATE_VALUE_NOT_OFFICIAL` | Chỉ tiêu nền chưa chính thức — nhân một con số một phần lên cả tháng là nhân cả phần thiếu lên |
| `RUNRATE_NO_DAILY_DATA` | Không dòng nào mang ngày bán |
| `RUNRATE_NO_ELAPSED_DAYS` | Chưa có ngày nào trôi qua |

Trang có hai ô run-rate: **doanh thu** (luôn tính được khi kỳ đang chạy) và
**DS quy đổi** (chỉ khi DS quy đổi đã chính thức).

---

## 5. So với kỳ trước — CÙNG SỐ NGÀY LỊCH

Tháng đang chạy được so với tháng liền trước trên **cùng một khoảng ngày**:
01–08/09 so với 01–08/08, không phải 8 ngày so với cả tháng.

Tháng trước ngắn hơn thì **cắt cả hai vế** ở ngày ngắn hơn (31/03 so tháng 02
⟹ cả hai cắt ở ngày 28). Cắt hai vế ở hai số ngày khác nhau thì phép so không
còn là "cùng số ngày lịch", và tháng ngắn sẽ luôn trông kém hơn.

Kỳ đã kết thúc thì không cắt gì — hai tháng trọn vẹn so với nhau.

Dòng **không có ngày bán** bị loại khỏi cả hai vế và được đếm riêng trên trang.

| Mã | Nghĩa |
|---|---|
| `COMPARE_NO_PERIOD` | Đang xem "Toàn bộ dữ liệu" — không có kỳ liền trước |
| `COMPARE_PREVIOUS_NO_LINES` | Kỳ trước không có dòng nào trong khoảng ngày đang so |
| `COMPARE_PREVIOUS_ZERO` | Kỳ trước có dòng nhưng doanh thu bằng 0 |
| `COMPARE_CURRENT_NO_REVENUE` | Kỳ NÀY chưa có doanh thu trong khoảng ngày đang so |

Không nhánh nào in ra `0 %`, `-100 %` hay vô cực.

---

## 6. Bảng đóng góp — cách đọc

Năm bảng, tất cả là **PHÂN HOẠCH** của cùng tập dòng đang được báo cáo:

| Bảng | Khoá gộp | Ghi chú |
|---|---|---|
| Theo đơn vị báo cáo | khoá sheet (`reporting_sheets.sheet_key_of`) | LUÔN nói về CẢ KỲ, kể cả khi trang đang thu hẹp; có cột Target |
| Theo mặt hàng | `product_key` | Nhãn = `min(product_raw)` — cùng quy ước `sales_queries.product_totals` |
| Theo nhóm hàng | nhóm hàng HIỆU LỰC (quyết định của Owner thắng, rồi tới pipeline) | |
| Theo nguồn đơn | `lead_source_final` | Dòng không có nguồn vào bucket "Chưa phân loại nguồn", không bị bỏ |
| Biên KPI thấp nhất | `product_key`, sắp biên TĂNG DẦN, 5 hàng | Chỉ hàng đã đủ coverage của chính nó mới có biên để xếp |

**"Biên thấp nhất" là một THỨ TỰ SẮP XẾP, không phải một phán quyết.** Không
có ngưỡng "biên thấp" nào được đặt ra — ngưỡng đó là một quyết định của Owner
mà không phiên triển khai nào được tự chọn giúp. Cũng không có nhãn `top`,
`tốt` hay `kém` ở bất kỳ bảng nào.

**Tỉ trọng** chia doanh thu của hàng cho doanh thu của phạm vi. Riêng bảng đơn
vị báo cáo dùng mẫu số là doanh thu CẢ KỲ, và trang nói ra điều đó ngay dưới
bảng.

Mỗi hàng bấm được → mở bảng kê chi tiết đã thu hẹp về đúng tập dòng của hàng
đó, giữ nguyên kỳ và phạm vi.

---

## 7. Chiết khấu

`total_sales` mà pipeline ghi **đã là số NET** — chiết khấu đã trừ một lần
(`DEC-114`). Khối chiết khấu vì vậy chỉ **CỘNG NGƯỢC** phần đã trừ để nói ra
quy mô của nó:

```text
Doanh thu trước chiết khấu = Doanh thu (NET) + Tổng chiết khấu
Tỉ lệ chiết khấu           = Tổng chiết khấu / Doanh thu trước chiết khấu × 100
```

Mẫu số là doanh thu **trước** chiết khấu, và nhãn trên trang nói đúng chữ đó.
Không có phép trừ thứ hai ở bất kỳ đâu.

Dòng "Chiết khấu" theo cách ghi của sổ tay cũ (`line_type = DISCOUNT`) KHÔNG
được cộng vào tổng chiết khấu — số tiền của nó nằm ở doanh thu ÂM của chính
nó. Đơn ghi bằng **cả hai cách** là chỗ duy nhất phép trừ có thể xảy ra hai
lần; những đơn ấy được **nêu tên** trên trang, và hệ thống KHÔNG tự chọn một
cách hiểu (`DEC-180`, R3 §2).

---

## 8. Dòng lỗ

Một dòng lỗ là dòng có **lợi nhuận KPI ÂM** — một mệnh đề khách quan trên con
số đã tính. Dòng **chưa** tính được lợi nhuận KHÔNG phải dòng lỗ; gộp hai thứ
đó lại là báo lỗ oan cho những dòng chỉ đang thiếu giá nhập.

Khối này luôn ghi **phạm vi đã xét** (`đã xét N / M dòng`). Khi coverage chưa
đủ, trang nói rõ đây không phải toàn bộ đơn lỗ của kỳ.

---

## 9. Khối "Đủ dữ liệu để kết luận?"

Kết luận `ĐỦ`/`CHƯA ĐỦ` đọc thẳng `Coverage.is_complete` — phép so bằng, không
phải phần trăm đã làm tròn. `350/351` làm tròn ra `99,72 %` và không phần trăm
nào được đứng thay cho một phép so bằng.

Khối gồm:

1. **Coverage** — tử số / mẫu số / % / danh sách blocker kèm chỗ phải sửa.
2. **Thẩm quyền giá nhập KPI của từng dòng** — `AUTO` · `MANUAL` ·
   `MANUAL_OVERRIDE` · `POLICY_ZERO` · `PENDING`. `POLICY_ZERO` (giá 0 do
   chính sách loại dòng) đứng **TÁCH** khỏi `PENDING` (chưa có câu trả lời
   nào): gộp chúng là quay lại đúng lỗi mà R3 đã tách ra.
3. **Nguồn giá mà lần chạy pipeline đã dùng** — `TRACKING_DAILY_MIN`,
   `TRACKING_PRICE_HISTORY`, `PriceMaster`, `Pending`, …
4. **Hàng đợi cần xử lý** — thiếu giá, chưa phân loại mã, ngoài bảng giá, xung
   đột mã, ngoại lệ gắn dòng. Mỗi mục dẫn tới đúng chỗ xử lý.
5. **Ngày dữ liệu** — ngày bán mới nhất trong phạm vi, số dòng KHÔNG có ngày
   bán (những dòng này rơi khỏi MỌI kỳ).
6. **Trạng thái kỳ** — đã chốt hay chưa, lần chốt thứ mấy, và `period_drift`.

### Giới hạn nói ra: MIN `FINAL`/`PROVISIONAL`

Trạng thái `day_status` (`FINAL`/`PROVISIONAL`) của giá MIN theo ngày **không
được lưu trên từng dòng**: hợp đồng `daily-min-v1` mang nó trong ảnh chụp lúc
chạy, và ảnh chụp đó không được ghi vào `order_line_result_version`. R4 chỉ
đọc dữ liệu hiệu lực nên nó KHÔNG dựng lại con số đó và cũng **không đoán** —
trang nói ra giới hạn này và đưa bảng thẩm quyền giá (mục 3 ở trên) là thứ gần
nhất mà dữ liệu hiệu lực trả lời được.

Muốn có `FINAL`/`PROVISIONAL` theo dòng thì phải lưu thêm nó lúc nạp sổ — một
thay đổi ở đường nhập, ngoài phạm vi R4.

---

## 10. Kỳ đã chốt

Trang hiển thị **dữ liệu hiện hành** của kỳ, và nói rõ kỳ đã chốt lần thứ mấy.
Nếu bộ số hiện tại đã khác bộ số lúc chốt, trang bật cảnh báo `period_drift`
và dẫn sang trang Chốt kỳ để đối chiếu.

R4 **không** làm số đã phát hành tự đổi: bản chụp lúc chốt nằm ở `period_close`
và trang này không ghi gì. Mọi đường ghi quyết định vào một kỳ đã chốt vẫn bị
từ chối `HTTP 409` như R3 đã dựng.

---

## 11. Drill-down

Mỗi KPI, mỗi hàng bảng và mỗi insight đều mở được đúng tập dòng đứng sau con
số của nó, trên **bảng kê chi tiết đã có** (`/kinh-doanh/gia-nhap`) — R4 không
dựng một màn hình chi tiết thứ hai và không lộ trường dữ liệu nào mới.

Đường dẫn luôn mang theo kỳ, phạm vi (sheet) và chế độ lọc. Bảng kê **nói ra**
phạm vi nó vừa thu hẹp về, kèm một đường dẫn "bỏ thu hẹp".

| Bấm vào | Mở ra |
|---|---|
| Doanh thu · Số đơn · SL · Doanh thu/đơn | `loc=tat-ca` |
| LN KPI · Biên · Lãi/đơn · DS quy đổi (khi coverage chưa đủ) | `loc=thieu-gia` — việc phải làm |
| Hàng "theo đơn vị báo cáo" | `nhom=<khoá sheet>` |
| Hàng "theo mặt hàng" | `mat-hang=<product_key>` |
| Hàng "theo nhóm hàng" | `nhom-hang=<nhóm>` |
| Hàng "theo nguồn đơn" | `nguon=<nguồn>` |
| Tổng chiết khấu | `loc=co-chiet-khau` |
| Số dòng lỗ | `loc=lo` |
| Coverage | `loc=thieu-gia` |

**Bất biến đã kiểm:** tổng các drill-down theo mặt hàng bằng đúng số dòng của
kỳ, và hàng TỔNG của mỗi bảng bằng đúng con số đầu trang. Ngoại lệ duy nhất là
cột **Đơn**, vốn không cộng được giữa các phạm vi — trang nói ra lý do ngay
dưới mỗi bảng.
