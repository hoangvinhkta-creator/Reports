# R4 — Báo cáo đánh giá vận hành

## Metadata

Status:
IMPLEMENTED

Current Status Reason:
Toàn bộ năm gói của brief R4 đã triển khai, có test đơn vị trên giá trị thuần
và test tích hợp đi qua route web thật, cộng một lượt smoke qua HTTP thật cho
cả ba luồng nghiệm thu của Owner. Không migration, không schema mới, không
route ghi mới.

`CHECK-R4-01` … `CHECK-R4-22` PASS (E1, bằng chứng ở §7 và ở
`docs/sessions/S131-r4-bao-cao-danh-gia.md`). `CHECK-R4-23` (Independent
Review) PASS — phiên review độc lập `S132` kết luận
`ACCEPT_WITH_RECORDED_RISK` trên exact HEAD `63a066e9`. `CHECK-R4-24` (Owner
nghiệm thu trên production) VẪN `NOT_TESTED` — không phiên nào có thẩm quyền
đóng nó thay Owner. Task DỪNG ở `IMPLEMENTED`.

R4 KHÔNG chạm và KHÔNG được coi là đã xác nhận `CHECK-R3-20` (Owner nghiệm thu
R3 trên production): nó vẫn `NOT_TESTED`, và không con số nào của R4 thay đổi
điều đó.

Phase:
PHASE-01 — Engine tính toán

Task Mode:
MAJOR

Primary Agent Tier:
C

Escalation Tier:
C

Difficulty:
3/5

Risk:
3/5

Blast Radius:
3/5 (V4.1 §4 — chấm theo failure path. Failure path của R4 là
`effective data của R3 → chỉ tiêu đánh giá → kết luận của Owner về kết quả
tháng`. Nó DỪNG ở đó: R4 không có đường ghi nào, nên không lỗi nào của nó đi
tiếp được vào `giá nhập KPI hiệu lực`, `EligibleKpiProfit`, `DS quy đổi` hay
`bộ số đã chốt`. Bán kính hẹp hơn R1–R3 theo cấu tạo, không theo lời hứa —
xem `CHECK-R4-22`.)

Effective Risk:
MEDIUM (Blast Radius quyết định — V4.1 §4.1)

Project Profile:
PRODUCT

Review Budget lineage:
`R4` là root lineage RIÊNG, `1 allowed / 0 used / 1 remaining`
(`MEDIUM = 1` theo bảng đã freeze `V4.1` §2). Xem
`PROJECT/REVIEW_BUDGET_LEDGER.md` → "Root Task: R4". Cùng cách đọc đã dùng cho
`R1`, `R2` và `R3`: R4 KHÔNG sửa tiếp triển khai của R3 — nó ĐỌC một R3 đã
merge vào nhánh mặc định (`824b5d7`). Không repair cycle nào bị tiêu trong
phiên triển khai này.

Owner Authority:
`R4 Execution Brief — Báo cáo đánh giá vận hành` (bàn giao tiếp từ R3), năm
gói ở §2. Nền đã merge: `claude/extract-upload-repo-gq2ws4` @ `824b5d7`
(merge PR #9, repair revision Alembic của R3).

---

## 1. Vì sao R4 tồn tại

Reports sau R1–R3 đã có đủ số: doanh thu, lợi nhuận KPI, DS quy đổi, coverage,
target, chốt kỳ. Nhưng để trả lời câu Owner thật sự hỏi cuối tháng — *"tháng
này ra sao, đạt bao nhiêu phần target, phần nào tạo ra kết quả, và số này đã
đủ tin chưa"* — người dùng phải mở bốn màn hình và tự cộng trong đầu.

R4 gom bốn câu đó vào MỘT trang, và không thêm một con số mới nào: mọi chỉ
tiêu cộng được vẫn do `business_metrics` quyết định.

Người dùng chính là 2–3 người. Vì vậy R4 cố ý KHÔNG dựng một hệ BI: không biểu
đồ trang trí, không forecast ML, không tab top-level mới, không export mới.

---

## 2. Năm gói của brief

1. **Bộ KPI và một lớp trình bày thống nhất** — tám chỉ tiêu đầu trang, mỗi ô
   mang số + đơn vị + phạm vi + coverage + trạng thái chính thức/chưa hoàn
   chỉnh + đường drill-down. `None` đi tới UI là `—` kèm lý do, không coalesce
   thành 0.
2. **Target, tiến độ và xu hướng** — target theo nhân viên/sheet đã có; % đạt,
   còn thiếu, cần đạt mỗi ngày còn lại, run-rate có nhãn; tháng đang chạy so
   với tháng trước trên CÙNG số ngày lịch.
3. **Phân tích đóng góp có thể hành động** — đơn vị báo cáo, mặt hàng, nhóm
   hàng, nguồn đơn, chiết khấu, dòng lỗ, xếp hạng biên.
4. **Chất lượng dữ liệu và trạng thái kỳ** — khối "Đủ dữ liệu để kết luận?".
5. **Drill-down, UI, export và tài liệu.**

Đặc tả nghiệp vụ đầy đủ của từng chỉ tiêu: `docs/spec/R4-DAC-TA-KPI.md`.

---

## 3. Scope Lock

**ĐƯỢC LÀM**

- Một module NGỮ NGHĨA thuần mới (`app/modules/reporting/evaluation.py`) và
  một module TRÌNH BÀY thuần mới (`app/web/evaluation_presentation.py`).
- Một route ĐỌC mới (`GET /kinh-doanh/danh-gia`) và một template mới.
- Mở rộng bảng kê chi tiết ĐÃ CÓ để làm đích drill-down: hai chế độ lọc
  (`lo`, `co-chiet-khau`) và ba tham số thu hẹp (`mat-hang`, `nhom-hang`,
  `nguon`).
- Đọc thêm hai trường CHỈ-HIỂN-THỊ vào `line_details` (`lead_source`,
  `price_source`) — không cột PII nào, không phép tính nào đọc chúng.

**KHÔNG ĐƯỢC LÀM**

- Sửa công thức MIN, resolver sản phẩm, đường import, giá tay, loại dòng, cơ
  chế chốt kỳ — trừ khi chính thay đổi R4 làm chúng SAI TRỰC TIẾP.
- Dựng nguồn số thứ hai: không đọc `ImportResult`, snapshot cũ hay Excel thô.
- Tạo target mới, suy target cấp công ty, hoa hồng/lương, giá thực nhập,
  backfill MIN, đồng bộ Tracking.
- Forecast ML, biểu đồ trang trí, tab top-level mới, làm lại file export R3.
- Tự đánh dấu Owner Acceptance của R3 hay của R4.

**Ngoại lệ đã dùng, và lý do** — đúng một, ở §5.

---

## 4. Thẩm quyền và giới hạn

- `PeriodData` của R3 là nguồn DUY NHẤT. Mọi chỉ tiêu cộng được đi qua
  `business_metrics.totals` của cùng lát dữ liệu mà trang Báo cáo và không
  gian làm việc đang hiển thị.
- Ba chỉ tiêu R4 thêm (`Doanh thu/đơn`, `Biên KPI`, `Lãi/đơn`) là ba phép CHIA
  hai con số đã có, gom về đúng một hàm `_ratio`.
- Target chỉ đọc `employee_target`/`group_target` qua
  `BusinessReportService.sheet_target`. Không phép cộng target nào.
- Kỳ đã chốt hiển thị dữ liệu hiện hành kèm trạng thái `period_drift`; R4
  không ghi gì nên không làm số đã phát hành tự đổi.

---

## 5. Repair ngoài năm gói — `_today()` theo múi giờ nghiệp vụ

**Đúng một repair**, và nó nằm trên LUỒNG CHÍNH của chính R4.

`app/web/server.py::_today()` trả `date.today()` — ngày theo đồng hồ của MÁY
CHỦ. Container production chạy UTC, nên từ **17:00 giờ Việt Nam tới nửa đêm**
hàm trả về NGÀY HÔM TRƯỚC.

Phân loại theo `xác suất × tác động × khả năng nhân viên phát hiện`:

```text
xác suất       CAO   — bảy giờ mỗi ngày, mỗi ngày
tác động       THẬT  — `as_of` lệch một ngày ⟹ "còn thiếu mỗi ngày" chia cho
                       số ngày còn lại SAI; cửa sổ "cùng số ngày lịch" lệch;
                       tháng mặc định của không gian làm việc sai vào tối
                       ngày cuối tháng (Target ghi vào tháng sai)
phát hiện      KHÓ   — không ngoại lệ, không cờ, không đổi màn hình; con số
                       sai trông hoàn toàn bình thường
```

Ba tiêu chí "PHẢI repair" của brief đều trúng: lỗi nằm trên luồng chính, làm
sai số khó phát hiện, và (qua tháng mặc định của Target) có thể ghi một quyết
định vào kỳ sai. Vì vậy nó được sửa thay vì ghi `ACCEPTED_RISK`.

**Sửa:** đọc theo `Asia/Ho_Chi_Minh` — cùng chuỗi vùng mà
`daily_min.snapshot.SUPPORTED_BUSINESS_TIMEZONE` đã freeze cho ranh giới ngày
của giá MIN. Dùng lại chuỗi vùng thay vì một `timedelta(hours=7)` viết cứng:
chuỗi đi qua cơ sở dữ liệu múi giờ của hệ thống nên nó vẫn đúng nếu quy ước
giờ của Việt Nam đổi.

Phạm vi ảnh hưởng: `_today()` đã là điểm tập trung DUY NHẤT của khái niệm "hôm
nay" trong `server.py` từ trước (nó được gom lại chính vì lý do đó), và nó
được monkeypatch trong mọi bộ test — nên hành vi vẫn kiểm được. Full regression
xác nhận không bài nào đổi kết quả.

---

## 6. Những gì R4 CỐ Ý không làm

| Việc | Vì sao không |
|---|---|
| Thêm tab top-level thứ tư | `DEC-185` rút thanh tab còn ba mục có chủ đích. Đổi thanh tab là một quyết định điều hướng riêng, không phải hệ quả của R4. Trang mở từ một đường dẫn trên trang Báo cáo, mang theo kỳ đang chọn. |
| Export mới | Brief §5: "export chỉ khi cần và cùng effective data". File xuất R3 đã đọc đúng `PeriodData` và đã có đủ cột; R4 không thêm chỉ tiêu nào cần một cột mới trong file. Làm lại file xuất chỉ để đổi cách trình bày là điều brief cấm. |
| Ngưỡng "biên thấp" | Ngưỡng là một quyết định của Owner. R4 chỉ SẮP XẾP biên tăng dần và nói rõ đó là thứ tự, không phải phán quyết. |
| Target cấp công ty | `DEC-PHB02-08` §7 — cộng target các đơn vị lên cho ra một con số chưa ai đặt. |
| Trạng thái MIN `FINAL`/`PROVISIONAL` theo dòng | Không được lưu vào dữ liệu hiệu lực; dựng lại nó là một thay đổi ở đường NHẬP, ngoài phạm vi R4. Trang NÓI RA giới hạn này — xem `AR-R4-01`. |

---

## 7. Completion Gate

| ID | Nội dung | Status | Evidence |
|---|---|---|---|
| `CHECK-R4-01` | Tám chỉ tiêu đầu trang đúng công thức và đúng thứ tự đã freeze | PASS | E1 |
| `CHECK-R4-02` | Mọi ô không có số đều mang MỘT mã lý do thuộc tập đóng | PASS | E1 |
| `CHECK-R4-03` | `None` không bao giờ thành `0`; mẫu số 0 ⟹ `—`, không phải `0` | PASS | E1 |
| `CHECK-R4-04` | Biên âm hiện đúng như nó là; biên không bị cap ở 100 % | PASS | E1 |
| `CHECK-R4-05` | Coverage < 100 % ⟹ LN KPI, Biên, Lãi/đơn, DS quy đổi đều `—` | PASS | E1 |
| `CHECK-R4-06` | Con số một phần hiện làm BẰNG CHỨNG, không bao giờ ở vị trí kết quả | PASS | E1 |
| `CHECK-R4-07` | Doanh thu/Số đơn KHÔNG bị cổng coverage chặn theo | PASS | E1 |
| `CHECK-R4-08` | `as_of` theo giờ Việt Nam; ngày đã trôi qua TÍNH CẢ hôm nay | PASS | E1 |
| `CHECK-R4-09` | Ngày còn lại = 0 ⟹ lý do, KHÔNG chia cho 0 | PASS | E1 |
| `CHECK-R4-10` | Target unset · zero · chưa có số · chưa chính thức là BỐN lý do riêng | PASS | E1 |
| `CHECK-R4-11` | Đã đạt/vượt ⟹ còn thiếu 0 và cần đạt mỗi ngày 0, nói rõ đã đạt | PASS | E1 |
| `CHECK-R4-12` | Không có target cấp công ty; hàng TỔNG để trống hai cột target | PASS | E1 |
| `CHECK-R4-13` | Run-rate luôn mang nhãn ước tính; bốn cửa từ chối đúng thứ tự | PASS | E1 |
| `CHECK-R4-14` | Tháng đang chạy so kỳ trước trên CÙNG số ngày lịch | PASS | E1 |
| `CHECK-R4-15` | Tháng trước ngắn hơn ⟹ cắt CẢ HAI vế ở ngày ngắn hơn | PASS | E1 |
| `CHECK-R4-16` | Dòng không có ngày bán bị loại khỏi phép so và được ĐẾM RIÊNG | PASS | E1 |
| `CHECK-R4-17` | Kỳ trước rỗng/bằng 0 ⟹ lý do bằng chữ, không `0 %`/vô cực/`-100 %` | PASS | E1 |
| `CHECK-R4-18` | Bảng đóng góp là PHÂN HOẠCH; cột Đơn không cộng dọc và trang nói ra | PASS | E1 |
| `CHECK-R4-19` | Chiết khấu CỘNG NGƯỢC, không trừ hai lần; đơn ghi hai cách được nêu tên | PASS | E1 |
| `CHECK-R4-20` | Dòng lỗ chỉ xét tập đã tính được lợi nhuận, có nhãn phạm vi | PASS | E1 |
| `CHECK-R4-21` | Khối chất lượng dữ liệu đủ sáu mục; MIN FINAL/PROVISIONAL nói ra giới hạn | PASS | E1 |
| `CHECK-R4-22` | Trang chỉ ĐỌC — mở nó không đổi một con số nào; POST trả 405 | PASS | E1 |
| `CHECK-R4-23` | Independent Review | PASS | E1 |
| `CHECK-R4-24` | Owner nghiệm thu trên production | NOT_TESTED | — |

Bằng chứng nguyên văn (lệnh + output): `docs/sessions/S131-r4-bao-cao-danh-gia.md`
§4–§6.

`CHECK-R4-23` và `CHECK-R4-24` KHÔNG được tự đánh dấu bởi bất kỳ phiên triển
khai nào.

`CHECK-R4-23` được đóng bởi PHIÊN REVIEW ĐỘC LẬP `S132` (không phải phiên
triển khai `S131`), trên exact HEAD `63a066e9275919df92bceaee58876f2724cf9df0`,
kết luận **`ACCEPT_WITH_RECORDED_RISK`**: `0` finding REPAIR_REQUIRED, `4`
`ACCEPTED_RISK` mới (`AR-R4-04` … `AR-R4-07` ở §9). Bằng chứng nguyên văn —
lệnh, kết quả test, tự tính lại độc lập bảy chuỗi, smoke qua HTTP thật —
ở `docs/sessions/S132-r4-independent-review.md`. `CHECK-R4-24` VẪN
`NOT_TESTED`: phiên review KHÔNG được nghiệm thu thay Owner.

---

## 8. Exit Criteria

1. Mở một KPI và một insight; drill-down ra đúng đơn/dòng và tổng khớp số trên
   trang. — `CHECK-R4-18`, smoke (A).
2. Mở tháng đang chạy ở phạm vi có target; % target, còn thiếu/ngày và so cùng
   ngày kỳ trước đúng; `as_of` và đơn vị hiển thị rõ. — `CHECK-R4-08`,
   `CHECK-R4-14`, smoke (B).
3. Kỳ thiếu MIN/giá tay: trang nói coverage chưa đủ và KHÔNG công bố LN
   KPI/biên/DS quy đổi một phần như toàn kỳ. — `CHECK-R4-05`, smoke (C).
4. Full regression xanh và không hồi quy so với baseline. — §7 của `S131`.
5. Independent Review kết luận trên exact HEAD. — `CHECK-R4-23`, ĐÃ CÓ:
   `ACCEPT_WITH_RECORDED_RISK` trên `63a066e9` (`S132`).
6. Owner nghiệm thu trên production. — `CHECK-R4-24`, CHƯA CÓ.

---

## 9. Rủi ro chấp nhận ghi nhận

### `AR-R4-01` — Trạng thái MIN `FINAL`/`PROVISIONAL` không có trong dữ liệu hiệu lực

**Tần suất:** mọi kỳ. **Tác động:** khối chất lượng dữ liệu không nói được bao
nhiêu dòng đang dùng một giá MIN của ngày chưa chốt. **Phát hiện:** trang tự
nói ra giới hạn này bằng chữ, ngay cạnh bảng thẩm quyền giá.

**Vì sao chấp nhận:** `day_status` sống trong ảnh chụp `daily-min-v1` lúc chạy
và không được ghi vào `order_line_result_version`. Dựng lại nó là sửa đường
NHẬP — brief cấm. Không con số tiền nào sai vì điều này: giá đã dùng là giá
Tracking đã trả về, và nó không đổi vì thiếu một nhãn trạng thái.

**Cách đóng:** lưu `day_status` cùng `price_source` lúc nạp sổ (một cột
additive), rồi khối chất lượng dữ liệu đọc nó. Việc của một task đường nhập,
không phải của R4.

### `AR-R4-02` — Bảng "theo nguồn đơn" phản ánh phân loại của pipeline, không phải kênh bán thật

**Tần suất:** mọi kỳ. **Tác động:** `lead_source_final` do
`app/modules/lead_source/classifier.py` gán theo từ khoá ghi chú và mặc định theo nhân
viên (`DEC-109`, `DEC-119`), nên nó là một PHÂN LOẠI SUY RA chứ không phải một
trường kênh bán do người nhập chọn. Đọc bảng này như "doanh thu theo kênh
marketing" sẽ vượt quá điều dữ liệu nói.

**Phát hiện:** dễ — phần lớn dòng rơi vào một bucket mặc định.

**Vì sao chấp nhận:** brief §3 cho phép hiện nguồn đơn "nếu module hiện có cho
phép và dữ liệu có nguồn", và yêu cầu hiện bucket rõ ràng thay vì suy nguyên
nhân. Bảng làm đúng điều đó: nó ĐẾM, và trang không viết một câu nguyên nhân
nào. Định nghĩa lại nguồn đơn là một quyết định của Owner.

**Cách đóng:** Owner quyết định nghĩa của "nguồn đơn" và đường nhập ghi nó
tường minh.

### `AR-R4-03` — `PeriodData._slice` chưa chiếu `excluded` theo lát (kế thừa `AR-R3-06`)

**Tần suất:** khi Owner đã loại dòng khỏi báo cáo. **Tác động:** trang đánh giá
không hiển thị danh sách dòng đã loại, nên rủi ro này KHÔNG có bề mặt mới ở
R4 — không con số nào của trang đọc `excluded`. Ghi lại ở đây để phiên sau
không tưởng R4 đã đóng nó.

**Cách đóng:** thuộc lineage R3.

---

### `AR-R4-04` — Run-rate nhân từ giá trị CẢ KỲ, không phải "giá trị đến `as_of`"

Ghi bởi Independent Review `S132`.

`docs/spec/R4-DAC-TA-KPI.md` §4 và docstring của `evaluation.run_rate` viết
công thức là `(giá trị đến as_of / ngày đã trôi qua) × ngày trong tháng`, còn
route truyền vào `totals.sales_revenue`/`totals.official_converted_sales`, tức
tổng CẢ KỲ. Hai con số đó chỉ bằng nhau khi trong kỳ KHÔNG có dòng nào mang
ngày bán SAU `as_of`.

**Tần suất:** THẤP — cần một dòng ghi ngày trong tương lai (gõ nhầm ngày, hoặc
đơn đặt trước ghi ngày giao); repo không có luật chặn ngày tương lai.
**Tác động:** HẠN CHẾ — reviewer tái hiện được mức lệch `380.000` so với
`80.000` (nghìn đồng) khi một dòng `30.000.000` mang ngày `20/09` trong khi
`as_of` là `03/09`. Nhưng con số này luôn mang nhãn "ước tính", KHÔNG đi vào
`% target`, `còn thiếu`, `cần đạt/ngày` hay bất kỳ chỉ tiêu công bố nào, và
không được ghi xuống đâu cả. **Phát hiện:** TRUNG BÌNH — chính trang đó hiện
"Ngày bán mới nhất trong phạm vi" (sẽ là một ngày TƯƠNG LAI) và
`compare-current` cắt theo cửa sổ nên lệch hẳn khỏi doanh thu đầu trang.

**Vì sao chấp nhận:** không thuộc sáu loại bắt buộc repair của brief review —
không nằm trên luồng chính của dữ liệu bình thường, không công bố một kết quả
kỳ, không làm sai coverage/target/cutoff, không lệch drill-down, không chạm
trạng thái chốt.

**Cách đóng:** cắt đầu vào run-rate theo `as_of` trước khi nhân — dùng lại
`evaluation._lines_up_to_day(data.details, as_of.day)` rồi `bm.totals(...)`;
hoặc thêm một cửa từ chối thứ năm khi `latest_sale_date > as_of`.

### `AR-R4-05` — "Ngoại lệ gắn dòng" là con số TOÀN CỤC, đứng cạnh bốn con số đã thu hẹp

Ghi bởi Independent Review `S132`. Đây là một BỀ MẶT MỚI của `AR-R3-05` đã
được chấp nhận, không phải một lỗi mới về bản chất.

`PeriodData.binding_exceptions` là `BindingExceptionStore.open_keys()` — TẤT CẢ
ngoại lệ còn mở của MỌI kỳ — và `_slice` chở nguyên vẹn nó sang lát sheet. Khối
"Hàng đợi cần xử lý" hiện `len(...)` của nó ngay cạnh bốn hàng đợi ĐÃ thu hẹp
theo kỳ + sheet, mà nhãn không nói ra sự khác biệt đó. Reviewer tái hiện: một
ngoại lệ của kỳ `2026-08` vẫn hiện là `1` khi đang xem kỳ `2026-09`.

**Tần suất:** TRUNG BÌNH khi đã có ngoại lệ gắn dòng. **Tác động:** NHỎ — một
con số HÀNG ĐỢI, không phải con số tiền: không vào coverage, không vào chỉ tiêu
nào, không đổi kết luận nào về kết quả tháng. **Phát hiện:** TRUNG BÌNH.

**Cách đóng (rẻ nhất):** thêm nhãn `(toàn bộ dữ liệu)` vào dòng đó, y như dòng
"Dòng KHÔNG có ngày bán" đang có. Đóng triệt để thì phải lọc `open_keys()` theo
khoá dòng của lát đang xem — việc của lineage R3 (`AR-R3-05`).

### `AR-R4-06` — Khối "so kỳ trước" in `01–00` ở khung nhìn "Toàn bộ dữ liệu"

Ghi bởi Independent Review `S132`. Khi không chọn kỳ nào,
`SameDaysComparison.day_cutoff = 0` và template vẫn in nhãn cửa sổ: *"ngày
01–00 của cả hai tháng"*, thẻ *"Kỳ này (01–00)"*.

**Tác động:** KHÔNG con số nào sai — cả ba ô đều `—` và mã lý do đúng
(`COMPARE_NO_PERIOD`). Đây là CHỮ hiển thị vô nghĩa. **Phát hiện:** DỄ.
**Cách đóng:** ẩn nhãn cửa sổ và hai thẻ khi `reason == COMPARE_NO_PERIOD`.

### `AR-R4-07` — Khoá `nhom` lạ rơi về "Cả kỳ" trong IM LẶNG, trái docstring

Ghi bởi Independent Review `S132`. Docstring của `_evaluation_scope` viết
*"Khoá lạ ⟹ về cả kỳ VÀ nói ra"*; thực tế trang không nói gì.

**Tác động:** NHỎ — hành vi (rơi về cả kỳ) là AN TOÀN và đúng ý định; tiêu đề
và ô chọn Phạm vi đều hiện "Cả kỳ" nên người đọc thấy ngay mình đang xem gì.
**Phát hiện:** DỄ. **Cách đóng:** hoặc thêm một câu trên trang, hoặc sửa
docstring cho khớp hành vi (rẻ hơn và đủ).

---

## 10. Đầu vào cho Independent Review

Reviewer nên tấn công đúng bốn chỗ sau, xếp theo mức nguy hiểm giảm dần:

1. **Cửa coverage có thật sự đóng ở MỌI đường không?** Tìm một đường nào đó
   trên trang (một bảng, một ô, một run-rate, một % target) mà một con số dẫn
   xuất từ lợi nhuận vẫn ra số khi coverage < 100 %. Bài
   `TestCoverageGate`/`TestIncompleteCoverageNeverPublishesAPartialResult` đã
   đi bốn ô đầu trang và target; các bảng đóng góp đi qua `row_for` chung.
2. **Cửa sổ "cùng số ngày lịch" có đối xứng không?** Đặc biệt: tháng 31 ngày
   so tháng 28/29 ngày, và ngày cuối tháng. Xem
   `test_a_shorter_previous_month_shortens_both_sides`.
3. **Có phép cộng nào sai không?** Cột Đơn cộng dọc, target cộng dọc, chiết
   khấu trừ hai lần, tỉ trọng dùng sai mẫu số khi trang đang thu hẹp phạm vi.
   Bảng đơn vị báo cáo cố ý dùng mẫu số CẢ KỲ — kiểm xem trang có nói ra
   không.
4. **Drill-down có mở đúng tập dòng không?** Tổng các drill-down theo mặt hàng
   phải bằng số dòng của kỳ; một khoá thu hẹp không khớp gì phải cho bảng RỖNG
   chứ không im lặng mở rộng về "tất cả".

Nền so sánh: `claude/extract-upload-repo-gq2ws4` @ `824b5d7`, full regression
`3058 passed, 12 skipped`.

**Đã thực hiện.** `S132` kiểm cả bốn chỗ trên và không tìm được lỗi ở chỗ nào:
cửa coverage đóng ở mọi đường (kể cả `% target` và run-rate DS quy đổi); cửa
sổ "cùng số ngày lịch" đối xứng, kể cả 31/03 so tháng 02 (cắt CẢ HAI ở ngày
28); không phép cộng sai nào (cột Đơn cộng dọc `5` vs TỔNG `3` lấy từ tổng
phạm vi — đúng; chiết khấu cộng ngược đúng một lần; bảng đơn vị nói ra mẫu số
cả kỳ); và tổng các drill-down theo mặt hàng bằng đúng số dòng của kỳ, khoá
không khớp cho bảng RỖNG. Chi tiết:
`docs/sessions/S132-r4-independent-review.md`.
