# Reports Demo V1 — tạo báo cáo cho Owner

## Dành cho Owner trên macOS

Nhấp đúp **`Open Reports.command`** trong thư mục Reports. Cửa sổ Reports sẽ
hiện ra: chọn một workbook kế toán `.xlsx`, nhấn **Tạo báo cáo**, rồi chọn mở
tệp khi cửa sổ báo hoàn tất. Không cần biết đường dẫn capture hay chạy lệnh
Python.

Launcher chỉ tự chọn capture lịch sử giá và danh mục Tracking có metadata hợp
lệ, `capture_status = COMPLETE`, và thời điểm `captured_at` mới nhất. Capture
FAILED, hỏng hoặc không có múi giờ bị bỏ qua; nếu không còn capture COMPLETE
hợp lệ, launcher dừng với hướng dẫn tạo capture mới. Nó không suy ra coverage
theo ngày bán: production vẫn quyết định AUTO hay Review Queue cho từng dòng.

Báo cáo mới được lưu tại `outputs/reports/report-<UTC timestamp>.xlsx`. Tên
trùng trong cùng giây nhận hậu tố số, nên không ghi đè báo cáo có sẵn. Workbook
kế toán, capture và các tệp nguồn khác không bị sửa.

Một lệnh đọc workbook kế toán và hai capture Tracking đã có, gọi production
composition rồi xuất **một** workbook Excel. Không kết nối Firebase, không
đọc PP YAML cũ và không tự điền giá còn thiếu.

## Chuẩn bị một lần

Dùng Python 3.11 trở lên. Mở Terminal tại thư mục Reports:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install 'openpyxl>=3.1' 'PyYAML>=6.0'
```

Hai thư viện này đã nằm trong dependency của repo. Nếu môi trường Python đã
có chúng thì dùng thẳng `python3` thay cho `.venv/bin/python`.

## Tạo báo cáo

```sh
.venv/bin/python app/demo.py \
  --sales tests/fixtures/golden/period_2026_01.xlsx \
  --tracking-capture data/captures/PPH-20260831T080038Z.json \
  --tracking-catalog data/tracking_catalog/capture_contract_v1_prod_2.json \
  --output outputs/demo-v1/report-moi.xlsx
```

Thay `--sales` bằng file kế toán cần xem. Hai capture trong ví dụ là artifact
cục bộ đã có, không được commit cùng mã nguồn; máy khác phải cung cấp capture
tương thích của mình. Mỗi lần dùng tên output mới: CLI không ghi đè tệp đã có.
Workbook kế toán phải theo bố cục production: sheet đang chọn, tiêu đề dòng 4,
dữ liệu từ dòng 6, cột Số BH xác định đơn. Không thay parser trong Demo V1.

Có thể gọi `python3 /đường/dẫn/Reports/app/demo.py` từ thư mục khác, với các
đường dẫn đầu vào/đầu ra tương ứng. Config và registry luôn lấy từ repo chứa
entrypoint. Các đường dẫn người dùng truyền được giải quyết trước khi đổi
thư mục sang repo. Wrapper dành cho CLI đơn luồng, không phải API server.

Thành công in:

```text
DEMO_COMPLETE
OUTPUT=<đường dẫn tuyệt đối>
ORDERS=<số đơn>
AUTO=<số đơn>
REVIEW_QUEUE=<số đơn>
ORDER_ACCOUNTING_RATE=100%
```

Lỗi tệp đầu vào, capture không hợp lệ, sai đối chiếu dòng/đơn hoặc output đã
tồn tại sẽ trả exit code 1 và `DEMO_FAILED`. Không in payload hay traceback.
Kiểm tra bốn đường dẫn, trạng thái capture và quyền ghi; không sửa ngày hay
giá để ép thành AUTO. `--help` liệt kê tham số.

## Đọc ba sheet

- **Summary:** tên đầu vào, thời điểm xử lý có múi giờ, số đơn/dòng, số AUTO và
  Review Queue theo đơn duy nhất, tỷ lệ đối chiếu và tự động, tổng doanh thu
  đã xác định, tổng KPI đủ điều kiện, số dòng có KPI/chưa có doanh thu, số
  dòng cần xem, finding cấp lô và tên capture.
- **Order Lines:** ngày, Số BH, nhân viên, sản phẩm, lượng, doanh thu, giá nhập,
  lợi nhuận kế toán/KPI, trạng thái dòng, lý do, nguồn giá, dòng nguồn và
  trạng thái đơn. Cột giá gọi là **Giá nhập kế toán / công khai** vì engine
  còn có giá lịch sử đã xác nhận; nguồn lịch sử không được gắn nhãn thành
  Tracking PP. Giá/lợi nhuận lấy nguyên từ mỗi WorkingLine.
- **Review Queue:** chỉ dòng cần xem và finding cấp lô chưa giải quyết. Giữ
  lý do/chi tiết production, ngày, đơn, nhân viên, sản phẩm, tệp/sheet/dòng
  nguồn; có namespace, mã, raw identity key, nguồn/quy tắc giá, capture,
  identity revision, Tracking reason, fallback reason/detail và KPI provenance
  nếu engine đã cung cấp.

AUTO theo đơn nghĩa là mọi dòng có kết quả và không có finding cần xem.
Một dòng Pending làm đơn thuộc REVIEW_QUEUE; dòng anh em đã resolve vẫn giữ
nguyên giá và KPI riêng. Finding `REVIEW_BATCH` không được gán tùy tiện cho
mọi đơn, không tính vào `REVIEW_QUEUE=<số đơn>`; Summary đếm riêng chúng.
Finding chỉ mang INFO không cần xử lý không được đưa vào, ngoại trừ thông
báo giá còn thiếu vốn giải thích trực tiếp một dòng Pending.

Ô tiền trống là **chưa xác định**, không phải 0. Tổng chỉ cộng giá trị engine
đã trả; tổng KPI trống nếu chưa dòng nào có KPI. Báo cáo là snapshot kết quả,
không phải mô hình tính lại khi sửa Excel. Không có công thức nghiệp vụ thứ
hai trong exporter. Nếu KPI trống nhưng engine không có reason chi tiết,
báo cáo chỉ nói production chưa trả kết quả, không đoán nguyên nhân.

Snapshot Tracking không phủ hết ngày bán thì Pending là đúng. Dữ liệu trước
cutover vẫn đi qua registry lịch sử production; truyền capture mới không
cấp quyền dùng giá hiện tại cho đơn cũ.

Workbook chứa giá vốn/lợi nhuận nhạy cảm, chỉ lưu/chia sẻ trong phạm vi Owner
được phép. Không xuất tên, điện thoại, địa chỉ khách hàng. Không commit báo
cáo/capture. Production identity store có thể tạo sidecar `.lock` khi đọc;
CLI không ghi mapping hay thay capture.

## Kiểm thử

```sh
.venv/bin/python -m pip install 'pytest>=8.0'
.venv/bin/python -m pytest -q tests/test_demo.py
.venv/bin/python -m pytest -q
git diff --check
```

Hai test cũ trong `test_105e_price_composition.py` giả định không có capture
ở đường dẫn mặc định. Nếu máy có capture runtime, chạy regression trong một
checkout Git sạch để kiểm tra đúng giả định, không xóa capture của Owner.
Hai test HTTP hiện có cần quyền bind localhost. Không sửa/skip test để né
các điều kiện môi trường này.

Giao diện Python `run_demo(...)` trả `DemoRun`, giữ `ImportResult` và tuple
`price_records` của đúng instance composition đã chạy để đối chiếu sau xuất.
