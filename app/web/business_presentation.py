"""PHB-03 — trình bày Summary/Employee: định dạng và GẮN NHÃN, không tính toán.

Cùng kỷ luật với `analytics_presentation`, cộng một điều riêng của PHB-03:

1. Không phép tính nghiệp vụ nào ở đây. Mọi con số do
   `app/modules/reporting/business_metrics` tính; tầng này chỉ đổi cách VIẾT.
2. **`None` LUÔN thành `—`, không bao giờ thành `0`** (`R-S2`).
3. **CHÍNH THỨC và CHƯA HOÀN CHỈNH không bao giờ trông giống nhau** (`R-S7`).
   Một con số phụ thuộc coverage luôn đi kèm trạng thái của chính nó trong
   CÙNG một cấu trúc, nên không có đường nào render con số mà rơi mất nhãn.

## Ngôn ngữ hướng về Owner, không hướng về pipeline

Chỉ thị PHB-03 §5: *"Do not fill the page with technical provenance details by
default; make warnings understandable to Owner."* Vì vậy các nhãn ở đây nói
"Giá nhập tự động" / "Owner đã sửa" / "Owner đã nhập" thay vì `AUTO` /
`MANUAL_OVERRIDE` / `MANUAL`. Mã provenance vẫn được lưu và vẫn hiện ở đúng
một chỗ — bảng hoàn thiện giá nhập, nơi nó là thông tin cần thiết chứ không
phải nhiễu.
"""

from __future__ import annotations

import calendar
import math
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from app.beta_presentation import REASON_DISPLAY_LABELS
from app.modules.reporting import brand_metrics as bmx
from app.modules.reporting import contribution
from app.modules.reporting import business_metrics as bm
from app.modules.reporting import profit_gate
from app.modules.reporting import reporting_sheets
from app.web.analytics_presentation import (
    ALL_DATA_LABEL, UNKNOWN_EMPLOYEE, count, employee_master_rank, group_label,
    money, period_label, period_options, period_value, previous_period,
)
from app.web.legacy_presentation import format_number
from app.web import brand_identity, line_identity, revenue_timeline

ORIGIN_BADGE = "SỐ MỚI"

# Nhãn trạng thái của mọi chỉ tiêu phụ thuộc coverage giá nhập.
STATE_LABELS = {
    bm.STATE_OFFICIAL: "CHÍNH THỨC",
    bm.STATE_INCOMPLETE: "CHƯA HOÀN CHỈNH",
}

# `B03` — hai câu này TỪNG quy mọi thiếu sót về "thiếu giá nhập", trong khi
# một dòng có thể chưa tính được vì số lượng bằng 0, thiếu giá bán, hoặc file
# thẩm quyền KPI hỏng. Nói sai nguyên nhân là đẩy Owner đi sửa nhầm chỗ, nên
# câu chung chỉ nói CÓ THIẾU; phần "thiếu cái gì" nằm ở bảng liệt kê bên dưới,
# nơi mỗi cửa chặn tự nói tên mình.
OFFICIAL_NOTE = (
    "Mọi dòng hàng của kỳ đều đã tính được lợi nhuận, nên lợi nhuận KPI và DS "
    "quy đổi dưới đây là số CHÍNH THỨC."
)
INCOMPLETE_NOTE = (
    "Còn dòng hàng của kỳ chưa tính được lợi nhuận. Các con số lợi nhuận KPI "
    "và DS quy đổi dưới đây CHƯA phải số chính thức — chúng chỉ cộng phần đã "
    "tính được. Danh sách ngay dưới nói rõ thiếu cái gì và sửa ở đâu."
)
EMPTY_NOTE = "Kỳ này chưa có dòng hàng nào."

# Nhãn provenance hướng Owner (`DEC-PHB02-02` §3 vẫn phân biệt đủ ba trạng thái).
PROVENANCE_LABELS = {
    bm.PROVENANCE_AUTO: "Tự động",
    bm.PROVENANCE_MANUAL: "Owner đã nhập",
    bm.PROVENANCE_MANUAL_OVERRIDE: "Owner đã sửa",
    # R3 §2 — giá `0` do CHÍNH SÁCH loại dòng quy định (`OD-105B-01` §3), không
    # do một nguồn giá nào trả về. Nhãn riêng vì "Tự động" sẽ khiến một dòng
    # phí trông như đã tra ra giá 0 từ Tracking.
    bm.PROVENANCE_POLICY_ZERO: "Chính sách (dòng phụ)",
    bm.PROVENANCE_PENDING: "Chưa có",
}

# `R1` — cảnh báo "sổ mới nhất không thấy lại một số dòng đang tính".
# Đây là CẢNH BÁO + ĐƯỜNG DẪN, không phải một phép đối soát: không dòng nào bị
# gộp, bị sửa hay bị loại khỏi tổng vì cảnh báo này (`OD_C` giữ nguyên ngữ
# nghĩa PRA-002 — KHÔNG fuzzy-merge, KHÔNG tự đối soát).
NOT_SEEN_WARNING = (
    "Sổ nạp gần nhất KHÔNG thấy lại một số dòng đang được tính vào tổng bên "
    "trên. Chúng VẪN được tính và KHÔNG bị xoá — nhưng nên soi trước khi tin "
    "vào tổng."
)

MOM_NO_PREVIOUS = "Chưa có dữ liệu tháng trước"
MOM_PREVIOUS_ZERO = "Tháng trước doanh thu 0 — không so được"
MOM_ALL_DATA = "Đang xem toàn bộ dữ liệu — không có tháng liền trước để so"

# `S121`/`DEC-180` §9 — tháng liền trước nằm bên kia ranh giới bàn giao.
# Tháng trước KHÔNG có dòng số mới nào, nhưng nó CÓ một Tổng bán chính thức
# trong sổ cũ. Trước bản sửa này, đúng tháng bàn giao luôn hiện "chưa có dữ
# liệu tháng trước" — một sự đứt gãy của MÀN HÌNH, không phải của nghiệp vụ.
#
# `DEC-180` đã chứng minh Tổng bán của hai bên là CÙNG một chỉ tiêu, nên phép
# so là hợp lệ. Điều KHÔNG hợp lệ, và không xảy ra ở đây, là trộn: mỗi kỳ vẫn
# lấy số từ ĐÚNG MỘT nguồn có thẩm quyền, và nguồn đó được nói ra trên màn
# hình thay vì ẩn đi.
MOM_LEGACY_PREVIOUS_NOTE = (
    "Tháng trước chưa có dòng nào của số mới, nên mốc so sánh lấy Tổng bán "
    "của SỐ CŨ cho đúng tháng đó. Hai kỳ vẫn là hai nguồn tách bạch — không "
    "con số nào bị cộng chung."
)

QUALIFYING_QUANTITY_LABEL = "Tổng số SP"
QUALIFYING_QUANTITY_NOTE = (
    "Tổng số SP chỉ cộng số lượng của những dòng có ĐƠN GIÁ BÁN trên "
    "1.000.000 đồng, để loại giá treo, chân kê và phụ kiện giá trị thấp."
)
KPI_PROFIT_NOTE = (
    "Lợi nhuận KPI cộng lợi nhuận đủ điều kiện của từng dòng hàng trong kỳ. "
    "Dòng chưa có giá nhập chưa tính được lợi nhuận, nên khi còn dòng như vậy "
    "con số này mang nhãn CHƯA HOÀN CHỈNH."
)
CONVERTED_SALES_NOTE = (
    "DS quy đổi = lợi nhuận KPI CHIA cho tỉ lệ quy đổi của từng dòng, rồi "
    "cộng lại. Tỉ lệ có thể khác nhau ngay trong cùng một nhân viên."
)
ORDER_COLUMN_NOTE = (
    "Một đơn có nhiều nhân viên được đếm ở TỪNG dòng nhân viên liên quan, nên "
    "cột Đơn cộng lại có thể lớn hơn tổng đơn của kỳ."
)

# `TASK-OWNER-UIUX-002` R2 — cột Nhóm bị bỏ khỏi bảng NÀY theo yêu cầu trực
# tiếp của chủ dự án: tên nhóm (Kinh doanh tiêu chuẩn/Kênh Nội thành) không
# đổi việc đọc bảng, và hàng "Nội thành"/"Gia dụng" đã tự nói tên nhóm của
# nó qua chính nhãn hàng. Dữ liệu nhóm (`employee_group`/`employee_group_code`)
# vẫn được `reporting_rows` tính — chỉ không render ở đây; bảng Target vẫn
# hiện cột Nhóm vì đó là màn hình khác, không bị chỉ thị này chạm tới.
EMPLOYEE_COLUMNS: tuple[str, ...] = (
    "Nhân viên", "Đơn", QUALIFYING_QUANTITY_LABEL, "Doanh thu",
    "Lợi nhuận KPI", "DS quy đổi", "Đã tính được lợi nhuận",
)

# Bảng kê chi tiết — mỗi dòng hàng là MỘT dòng bảng, ô nhập được nằm ngay
# trong dòng đó, và các ô tiền suy ra tự cập nhật sau khi lưu (chỉ thị
# `ORDER DETAIL TABLE`). Bốn cột cuối là SUY RA, không gõ tay được.
DETAIL_COLUMNS: tuple[str, ...] = (
    "Ngày", "Mã đơn", "Mặt hàng", "SL", "Giá bán", "Giá nhập KPI", "Nguồn giá",
    "Doanh thu", "Lợi nhuận KPI", "DS quy đổi", "Nhân viên",
)
# Tên cũ, giữ lại để không phá vỡ nơi nào còn tham chiếu.
MISSING_PRICE_COLUMNS = DETAIL_COLUMNS

DERIVED_COLUMNS_NOTE = (
    "Ba cột Doanh thu · Lợi nhuận KPI · DS quy đổi là số SUY RA — không gõ "
    "trực tiếp được. Sửa Số lượng/Giá bán trên sổ gốc, hoặc sửa Giá nhập ngay "
    "tại đây, rồi bấm LƯU: các con số đó tự tính lại trên chính trang này."
)
UNRESOLVED_EMPLOYEE_NOTE = (
    "Những dòng chưa biết của ai VẪN được cộng vào lợi nhuận của cả kỳ. "
    "Chúng chỉ chưa được cộng cho một nhân viên cụ thể — chọn tên rồi bấm LƯU "
    "là chúng chuyển sang bảng của người đó."
)
NET_SALES_NOTE = (
    "Cột Doanh thu lấy đúng con số kế toán mà hệ thống đã ghi khi nạp sổ, "
    "KHÔNG phải phép nhân Số lượng × Giá bán làm lại."
)

# `S121`/`DEC-180` — dòng "Chiết khấu" của sổ tay cũ, dựng lại từ cột
# `discount` của sổ kế toán hiện hành. Nó là DỮ LIỆU TRÌNH BÀY suy ra, không
# phải một dòng hàng: không có ô nhập nào, không tra giá nhập, không đếm vào
# bất kỳ chỉ tiêu nào của kỳ.
DISCOUNT_ROW_LABEL = bm.DISCOUNT_DISPLAY_LABEL
DISCOUNT_PROVENANCE = "SOURCE_DISCOUNT"
DISCOUNT_PROVENANCE_LABEL = "Chiết khấu trên sổ"
DISCOUNT_ROW_NOTE = (
    "Dòng có chiết khấu được tách làm hai như sổ tay cũ vẫn ghi: dòng sản "
    "phẩm hiện số TRƯỚC chiết khấu, rồi một dòng \u201cChiết khấu\u201d "
    "ngay dưới mang số ÂM. Hai dòng cộng lại đúng bằng con số kế toán của "
    "kỳ — không có đồng nào bị trừ hai lần. Dòng \u201cChiết khấu\u201d là "
    "số suy ra từ sổ, không sửa được và không được đếm như một sản phẩm."
)

GIA_DUNG_COLUMNS: tuple[str, ...] = (
    "Mặt hàng", "Số dòng", "Doanh thu", "Phân loại hiện tại", "Tick Gia dụng",
)


# --- PHB-06: báo cáo theo THƯƠNG HIỆU ------------------------------------

BRAND_COLUMNS: tuple[str, ...] = (
    "Thương hiệu", "Đơn", QUALIFYING_QUANTITY_LABEL, "Doanh thu",
    "Lợi nhuận KPI", "DS quy đổi", "Đã tính được lợi nhuận",
)

# Bảng thương hiệu là một PHÂN HOẠCH của đúng tập dòng đang được báo cáo, nên
# bốn cột cộng được của nó cộng lại đúng bằng tổng kỳ. Cột Đơn thì không —
# cùng sự thật `R-E5` mà bảng nhân viên đã phải nói ra, chỉ đổi chiều gộp.
BRAND_ORDER_COLUMN_NOTE = (
    "Một đơn có hàng của nhiều thương hiệu được đếm ở TỪNG dòng thương hiệu "
    "liên quan, nên cột Đơn cộng lại có thể lớn hơn tổng đơn của kỳ. Bốn cột "
    "còn lại cộng lại đúng bằng tổng kỳ."
)

# Hai lý do KHÁC NHAU khiến một dòng chưa có thương hiệu. Gộp chúng thành một
# ô "chưa xác định" duy nhất sẽ nói với Owner rằng cách sửa là như nhau —
# trong khi chỉ một trong hai sửa được từ trong Reports (`PHB-06 §10`).
BRAND_UNKNOWN_REASON_NOTES = {
    bmx.KIND_IDENTITY_UNRESOLVED: (
        "Chưa nhận diện được mặt hàng, nên chưa có danh tính nào để hỏi "
        "thương hiệu. Phân loại các dòng này ở bảng kê trang NHÂN VIÊN."),
    bmx.KIND_BRAND_ABSENT: (
        "Đã nhận diện được mặt hàng, nhưng danh tính của nó không mang thương "
        "hiệu. Việc này KHÔNG sửa được từ Reports — nó là một khoảng trống của "
        "chính nguồn danh tính."),
}

BRAND_RECONCILED_NOTE = (
    "Doanh thu · Tổng số SP · Lợi nhuận KPI · DS quy đổi của bảng này cộng "
    "lại ĐÚNG BẰNG tổng kỳ, kể cả phần chưa xác định thương hiệu. Không dòng "
    "hàng nào bị bỏ rơi và không dòng nào bị đếm hai lần."
)
BRAND_RECONCILE_FAILED_NOTE = (
    "CẢNH BÁO: bảng thương hiệu KHÔNG cộng lại đúng bằng tổng kỳ. Đây là lỗi "
    "hệ thống, không phải một trạng thái dữ liệu — đừng dùng bảng này để ra "
    "quyết định cho tới khi nó được sửa."
)
BRAND_EXCLUDED_NOTE = (
    "Dòng Owner đã loại khỏi báo cáo KHÔNG có mặt ở đây, đúng như ở mọi chỉ "
    "tiêu khác của kỳ."
)
BRAND_NO_TARGET_NOTE = (
    "Chưa có Target theo thương hiệu. Target hiện chỉ đặt cho nhân viên và "
    "cho hai nhóm Nội thành · Gia dụng — hệ thống không cộng dồn để bịa ra "
    "một con số Owner chưa đặt."
)

# --- PHB-07: CƠ CẤU doanh thu theo ĐƠN VỊ BÁO CÁO ------------------------

COMPOSITION_COLUMNS: tuple[str, ...] = (
    "Đơn vị báo cáo", "Đơn", QUALIFYING_QUANTITY_LABEL, "Doanh thu",
    "Tỉ trọng doanh thu", "Lợi nhuận KPI", "DS quy đổi",
    "Đã tính được lợi nhuận",
)

# Đơn vị báo cáo KHÁC con người (`DEC-PHB02-08`). Câu này phải đứng ngay trên
# bảng: một người đọc thấy "Nội thành" mà không biết nó gộp ba người sẽ đi
# tìm dòng của Vinh và kết luận rằng bảng thiếu.
COMPOSITION_UNIT_NOTE = (
    "Mỗi dòng là một ĐƠN VỊ BÁO CÁO, không phải một con người. Nội thành và "
    "Gia dụng mỗi cái là MỘT dòng gộp cả nhóm — đúng như sổ cũ và đúng như "
    "Target đang đặt cho hai nhóm đó. Nhân viên thuộc nhóm Nội thành vì vậy "
    "không có dòng riêng ở đây; bảng kê trang NHÂN VIÊN vẫn ghi đúng người "
    "bán của từng dòng."
)

COMPOSITION_SHARE_NOTE = (
    "Tỉ trọng = doanh thu của đơn vị CHIA cho doanh thu bán hàng của cả kỳ. "
    "Phần trăm hiện ra đã làm tròn hai chữ số nên cộng lại có thể lệch vài "
    "phần trăm nhỏ; phép đối soát ở trên chạy trên số tiền đầy đủ, không trên "
    "phần trăm đã làm tròn."
)

# Tỉ suất lợi nhuận (`D1` của PHB-02, `N.7` của TASK-PRA-000) vẫn đang DEFER:
# mẫu số của nó chưa được Owner chốt. Trang nói ra khoảng trống đó thay vì
# lặng lẽ không có cột nào.
COMPOSITION_NO_PROFIT_SHARE_NOTE = (
    "Chỉ có tỉ trọng DOANH THU. Chưa có tỉ trọng hay tỉ suất lợi nhuận: mẫu "
    "số của một tỉ suất lợi nhuận là câu hỏi chủ dự án chưa chốt, và hệ thống "
    "không tự chọn giúp."
)

COMPOSITION_ORDER_COLUMN_NOTE = (
    "Một đơn có cả hàng Gia dụng lẫn hàng khác được đếm ở TỪNG đơn vị liên "
    "quan, nên cột Đơn cộng lại có thể lớn hơn tổng đơn của kỳ. Bốn cột còn "
    "lại cộng lại đúng bằng tổng kỳ."
)

COMPOSITION_RECONCILED_NOTE = (
    "Doanh thu · Tổng số SP · Lợi nhuận KPI · DS quy đổi của bảng này cộng "
    "lại ĐÚNG BẰNG tổng kỳ, kể cả phần chưa xác định nhân viên. Không dòng "
    "hàng nào bị bỏ rơi và không dòng nào bị đếm hai lần."
)
COMPOSITION_RECONCILE_FAILED_NOTE = (
    "CẢNH BÁO: bảng cơ cấu KHÔNG cộng lại đúng bằng tổng kỳ. Đây là lỗi hệ "
    "thống, không phải một trạng thái dữ liệu — đừng dùng bảng này để ra "
    "quyết định cho tới khi nó được sửa."
)
COMPOSITION_EXCLUDED_NOTE = (
    "Dòng Owner đã loại khỏi báo cáo KHÔNG có mặt ở đây, đúng như ở mọi chỉ "
    "tiêu khác của kỳ."
)
COMPOSITION_UNRESOLVED_NOTE = (
    "Dòng chưa biết của nhân viên nào vẫn có dòng riêng và vẫn mang đủ tiền "
    "của nó. Gán người bán cho những dòng đó ở bảng kê trang NHÂN VIÊN."
)

# Bảng này là ảnh chụp của MỘT kỳ. Không có chuỗi nhiều tháng theo đơn vị báo
# cáo: sổ cũ và sổ hiện hành là hai nguồn khác nhau (`DEC-180` §9 — một kỳ,
# một nguồn), và dựng một chuỗi lịch sử theo đơn vị báo cáo sẽ phải trộn
# chúng. Xu hướng doanh thu của công ty đã có ĐÚNG MỘT chỗ (`DEC-185`).
COMPOSITION_ONE_PERIOD_NOTE = (
    "Bảng này là cơ cấu của ĐÚNG kỳ đang chọn. Xu hướng doanh thu theo thời "
    "gian xem ở biểu đồ trên trang BÁO CÁO — hệ thống không dựng thêm một "
    "dòng thời gian thứ hai."
)


# --- PHB-05: Target tháng của nhân viên (DEC-PHB02-06) -------------------

TARGET_COLUMNS: tuple[str, ...] = (
    "Nhân viên", "DS quy đổi hiện tại", "Target", "So target", "Sửa",
)

# Ba lý do KHÁC NHAU khiến ô "So target" không có số. Gộp chúng thành một chữ
# "N/A" duy nhất sẽ xoá đúng thông tin Owner cần để biết phải làm gì tiếp.
TARGET_REASON_LABELS = {
    bm.TARGET_UNSET: "Chưa thiết lập target",
    bm.TARGET_ZERO: "Target = 0 — không so được",
    bm.TARGET_NO_ACTUAL: "Chưa có DS quy đổi để so",
}

TARGET_UNSET_LABEL = "Chưa thiết lập"

TARGET_NOTE = (
    "Target là con số Owner tự đặt cho TỪNG nhân viên trong TỪNG tháng — hệ "
    "thống không tự tính và không viết cứng nó ở đâu. Đổi Target của tháng "
    "này không đụng tới tháng khác."
)
TARGET_FORMULA_NOTE = (
    "So target = DS quy đổi CHIA cho Target, viết dạng phần trăm — đúng công "
    "thức của sổ cũ (ô N = F/M). Vượt target thì hiện đúng số vượt, không "
    "chặn ở 100%."
)
TARGET_UNIT_NOTE = (
    "Nhập Target theo ĐỒNG (VND). Ví dụ: 500.000.000. Bảng hiện lại theo "
    "nghìn đồng cho gọn, số đầy đủ xem ở ô nhập và ở tooltip."
)
TARGET_ZERO_VS_BLANK_NOTE = (
    "Để trống ô rồi bấm LƯU là GỠ target (trở lại “chưa thiết lập”). Gõ số 0 "
    "là ĐẶT target bằng không — hai điều khác nhau, và cả hai đều làm So "
    "target không có số."
)
TARGET_NO_PERIOD_NOTE = (
    "Target gắn với MỘT tháng cụ thể. Chọn một kỳ báo cáo ở ô trên để xem và "
    "sửa Target — khung nhìn “Toàn bộ dữ liệu” không có Target."
)
TARGET_COMPANY_DEFERRED_NOTE = (
    "Chưa có Target ở cấp công ty. Sổ cũ có một target công ty đặt RIÊNG, và "
    "nó KHÔNG bằng tổng target của các nhân viên — nên hệ thống không cộng "
    "dồn để bịa ra một con số Owner chưa đặt."
)
TARGET_LEGACY_READ_ONLY_NOTE = (
    "Target trong SỐ CŨ là bằng chứng lịch sử, chỉ đọc. Ô nhập ở đây chỉ ghi "
    "Target của hệ thống báo cáo hiện hành."
)



def business_date(value) -> str:
    """Mọi ngày nghiệp vụ viết `DD/MM/YYYY` (`DEC-184` §24) — không bao giờ ISO
    trên màn hình: `03/08` là hai ngày khác nhau ở hai quy ước, và không gì
    trên trang nói người đọc đang ở quy ước nào. TASK-UIUX-001 dời hàm này
    từ `workspace_presentation` về đây để bảng kê chi tiết dùng CÙNG một
    cách viết ngày với không gian làm việc."""
    return "—" if value is None else value.strftime("%d/%m/%Y")


def _decimal(value: Optional[Decimal]) -> str:
    return "—" if value is None else format_number(value)


# `R1` §9 — Owner-approved: trang BÁO CÁO/NHÂN VIÊN hiện tiền theo NGHÌN ĐỒNG
# thay vì VND đầy đủ, để bớt số 0. Đây CHỈ là cách VIẾT lại: giá trị lưu trữ
# và mọi phép tính vẫn dùng `value` VND đầy đủ y nguyên — hàm này không được
# gọi ở bất kỳ đường TÍNH nào, chỉ ở tầng trình bày, và luôn đi kèm bản VND
# đầy đủ (`_decimal`) để không đường nào mất khả năng xem lại số gốc.
def _thousand_vnd(value: Optional[Decimal]) -> str:
    if value is None:
        return "—"
    return format_number(
        (value / Decimal(1000)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


# R6 §2 — hai tên CÔNG KHAI cho đúng hai hàm viết tiền ở trên. Chúng không
# thêm một cách viết thứ ba: chúng chỉ cho các trang R6 dùng lại ĐÚNG hai hàm
# này thay vì import xuyên qua dấu gạch dưới hoặc — tệ hơn — viết lại phép
# chia 1.000 ở một file khác và làm tròn lệch đi ở đúng những con số lớn nhất.
def money_text(value: Optional[Decimal]) -> str:
    """VND đầy đủ, `—` khi `None`."""
    return _decimal(value)


def money_kvnd(value: Optional[Decimal]) -> str:
    """Nghìn đồng — CHỈ để hiển thị, không bao giờ ở một đường tính."""
    return _thousand_vnd(value)


# `DEC-212` — Owner chốt 09/09/2026: MỌI con số tiền trên màn hình viết theo
# NGHÌN ĐỒNG, kể cả ĐƠN GIÁ của từng dòng hàng, không riêng các ô tổng đã đổi
# ở `R1` §9. Lý do là lý do cũ, chỉ mở rộng phạm vi: một bảng mà cột tổng viết
# `13.550` còn cột giá bán ngay cạnh viết `13.550.000` bắt người đọc đổi đơn
# vị giữa hai cột kề nhau, và đó là chỗ một con số bị đọc lệch một nghìn lần.
#
# Bản VND đầy đủ KHÔNG bị bỏ: nó chuyển sang tooltip, đúng hợp đồng mà
# `gated_cell`/`money_cell` đã dựng — không đường nào mất khả năng xem lại số
# gốc. Ô NHẬP LIỆU là ngoại lệ có chủ đích, xem `PRICE_INPUT_NOTE`.
#: Vì sao Ô NHẬP giữ VND đầy đủ trong khi mọi ô ĐỌC đã rút gọn.
#:
#: Rút gọn là một cách VIẾT ra; ô nhập là một cách ĐỌC vào, và hai chiều đó
#: không đối xứng. Một ô hiện `5.000` mà lưu `5.000.000` buộc Owner phải nhớ
#: mình đang gõ đơn vị nào — và lần quên đầu tiên ghi vào sổ một giá nhập sai
#: đúng một nghìn lần, ở một trường mà cả lợi nhuận KPI lẫn DS quy đổi đều
#: đọc. Không có tooltip nào cứu được một con số đã ghi sai.
PRICE_INPUT_NOTE = (
    "Ô nhập giá vẫn dùng VND đầy đủ (13.550.000), khác các ô chỉ để đọc — "
    "gõ vào và đọc ra là hai chiều khác nhau."
)


def price_pair(value: Optional[Decimal], key: str) -> dict:
    """`{key: bản nghìn đồng, key + "_full": bản VND đầy đủ}`.

    Trả về một `dict` để nơi gọi `**`-ghép thẳng vào hàng, giữ hai bản LUÔN
    đi cùng nhau: tách chúng thành hai lệnh gán riêng là mở đường cho một
    hàng có bản rút gọn mà không có bản đối chiếu.
    """
    return {key: _thousand_vnd(value), f"{key}_full": _decimal(value)}


def percent(value: Optional[Decimal], *, sign: bool = False) -> str:
    """`None` ⟹ `—`. KHÔNG BAO GIỜ in vô cực hay một phần trăm bịa."""
    if value is None:
        return "—"
    prefix = "+" if sign and value > 0 else ""
    return f"{prefix}{format_number(value)}%"


def coverage_cell(coverage: bm.Coverage) -> dict:
    """Coverage viết dạng `N / M dòng` KÈM phần trăm, không thay cho nhau.

    `N / M dòng` là con số Owner hành động được ("còn 11 dòng phải nhập"); phần
    trăm là con số Owner cảm nhận được. Gate thì không đọc cái nào trong hai —
    nó đọc `is_complete`, vì `350/351` làm tròn thành `99,72 %` và không phần
    trăm nào được phép đứng thay cho một phép so bằng (`DEC-PHB02-02` §4).
    """
    return {
        "text": f"{count(coverage.covered_lines)} / {count(coverage.total_lines)} dòng",
        "percent": percent(coverage.percent),
        "complete": coverage.is_complete,
        "missing_price_lines": coverage.missing_price_lines,
        "owner_fixable_lines": coverage.owner_fixable_lines,
        "unresolved_employee_lines": coverage.unresolved_employee_lines,
        # Mỗi mục là một VIỆC CỤ THỂ, kèm chỗ phải sửa — thay cho ô đếm gộp cũ
        # vốn nói "nhập giá không cứu được" cho gần như mọi dòng (`B03`).
        "blockers": [
            {"code": code, "lines": lines, "label": profit_gate.label(code)}
            for code, lines in coverage.blocked_lines
        ],
    }


def gated_cell(
    value: Optional[Decimal], official: Optional[Decimal], state: str
) -> dict:
    """Một chỉ tiêu phụ thuộc coverage + trạng thái của chính nó.

    `value` là con số cộng được đến hôm nay; `official` là `None` cho tới khi
    coverage đạt 100 %. Cả hai nằm trong cùng một dict để template không thể
    lấy con số mà bỏ nhãn.
    """
    return {
        "text": _decimal(value),
        "text_kvnd": _thousand_vnd(value),
        "official": official is not None,
        "state": state,
        "state_label": STATE_LABELS[state],
        "missing": value is None,
    }


def month_over_month(
    current: Optional[Decimal], previous: Optional[Decimal], *,
    has_period: bool, previous_has_lines: bool,
    previous_origin: str = "", previous_source: str = "",
) -> dict:
    """`DEC-PHB02-07` — mọi nhánh "không so được" đều có CHỮ, không có số.

    Ba nhánh, cố ý không gộp: đang xem "Toàn bộ dữ liệu" (không có tháng liền
    trước), tháng trước không có dòng nào, và tháng trước có dòng nhưng doanh
    thu bằng 0. Owner đọc ba câu khác nhau vì ba tình huống đó dẫn tới ba hành
    động khác nhau.

    `previous_origin`/`previous_source` chỉ dùng để GẮN NHÃN khi mốc so sánh
    đến từ một nguồn khác engine hiện hành (`DEC-180` §9). Chúng KHÔNG đổi
    một nhánh nào ở trên và KHÔNG tham gia phép tính: hàm này nhận một con
    số đã sẵn sàng, không đi tìm số ở đâu cả.
    """
    if not has_period:
        return {"percent": "—", "note": MOM_ALL_DATA, "missing": True,
                "origin": "", "source": ""}
    if not previous_has_lines:
        return {"percent": "—", "note": MOM_NO_PREVIOUS, "missing": True,
                "origin": "", "source": ""}
    value = bm.month_over_month_percent(current, previous)
    if value is None:
        return {"percent": "—", "note": MOM_PREVIOUS_ZERO, "missing": True,
                "origin": previous_origin, "source": previous_source}
    return {"percent": percent(value, sign=True),
            "note": MOM_LEGACY_PREVIOUS_NOTE if previous_origin else "",
            "missing": False,
            "origin": previous_origin, "source": previous_source}


def _previous_basis(
    previous_totals, fallback: Optional[dict]
) -> tuple[Optional[Decimal], bool, str, str]:
    """Mốc so sánh của "So tháng trước": `(giá trị, có mốc, origin, nguồn)`.

    Thứ tự là thứ tự THẨM QUYỀN và nó không đảo được: engine hiện hành trước,
    nguồn dự phòng SAU và CHỈ khi tháng trước không có dòng số mới nào. Một
    tháng đã có số mới không bao giờ bị số cũ thay chỗ (`CASE 9`), và một
    tháng không có ở cả hai nguồn vẫn trả về "chưa có dữ liệu" (`CASE 10`).

    `fallback` là một dict THUẦN do tầng ráp truyền xuống — tầng trình bày
    không biết nguồn đó là gì và không tự đi tìm nó.
    """
    if previous_totals is not None and previous_totals.lines > 0:
        return previous_totals.sales_revenue, True, "", ""
    if fallback and fallback.get("sales_revenue") is not None:
        return (fallback["sales_revenue"], True,
                fallback.get("origin_label") or "",
                fallback.get("source_label") or "")
    return None, False, "", ""


def _metrics(totals: bm.BusinessTotals) -> dict:
    state = totals.state
    return {
        "orders": count(totals.orders),
        "lines": count(totals.lines),
        "sales_revenue": _decimal(totals.sales_revenue),
        "sales_revenue_kvnd": _thousand_vnd(totals.sales_revenue),
        "qualifying_quantity": _decimal(totals.qualifying_quantity),
        "kpi_profit": gated_cell(
            totals.kpi_profit, totals.official_kpi_profit, state),
        "converted_sales": gated_cell(
            totals.converted_sales, totals.official_converted_sales, state),
        "coverage": coverage_cell(totals.coverage),
        # `OD-5` — hai con số này luôn cộng lại bằng `kpi_profit`. Hiện cả hai
        # cạnh nhau để phần đang treo không biến mất không dấu vết.
        "employee_attributed_profit": _decimal(totals.employee_attributed_profit),
        "employee_attributed_profit_kvnd": _thousand_vnd(totals.employee_attributed_profit),
        "unattributed_profit": _decimal(totals.unattributed_profit),
        "unattributed_profit_kvnd": _thousand_vnd(totals.unattributed_profit),
        "unattributed_lines": totals.coverage.unresolved_employee_lines,
        "state": state,
        "state_label": STATE_LABELS[state],
        "official": totals.coverage.is_complete,
    }


def not_seen_warning(absence: Optional[dict]) -> Optional[dict]:
    """`R1` — mô hình hiển thị của cảnh báo, hoặc `None` khi không có gì để nói.

    `None` và "đã đo, bằng 0" cho ra CÙNG một kết quả hiển thị (không có cảnh
    báo) nhưng KHÔNG cùng một nguyên nhân, nên cả hai đều đi qua đây thay vì
    để template tự đoán từ một con số. Không có snapshot nào ⟹ `None`: chưa
    nạp sổ lần nào thì không có gì để cảnh báo.
    """
    if not absence or not absence.get("not_seen"):
        return None
    return {
        "lines": absence["not_seen"],
        "snapshot_id": absence.get("snapshot_id") or "",
        "note": NOT_SEEN_WARNING,
    }


def summary(
    totals: bm.BusinessTotals, *, period, previous_totals, undated: int,
    previous_fallback: Optional[dict] = None,
) -> dict:
    """Mô hình hiển thị của Summary V1 (`R-S1`…`R-S8`).

    `previous_fallback` là mốc so sánh của tháng trước khi tháng đó nằm bên
    kia ranh giới bàn giao (`DEC-180` §9). Mặc định `None` ⟹ hành vi cũ y
    nguyên, nên mọi nơi gọi hàm này mà không biết tới nguồn dự phòng vẫn chạy
    đúng như trước.
    """
    previous_value, previous_has, origin, source = _previous_basis(
        previous_totals, previous_fallback)
    return {
        **_metrics(totals),
        "period_label": period_label(period),
        "previous_label": (
            None if period is None else period_label(previous_period(period))),
        "mom": month_over_month(
            totals.sales_revenue, previous_value,
            has_period=period is not None,
            previous_has_lines=previous_has,
            previous_origin=origin, previous_source=source,
        ),
        "note": _state_note(totals),
        "undated_lines": undated,
    }


def _state_note(totals: bm.BusinessTotals) -> str:
    if totals.lines == 0:
        return EMPTY_NOTE
    return OFFICIAL_NOTE if totals.coverage.is_complete else INCOMPLETE_NOTE


def close_summary(totals: bm.BusinessTotals) -> dict:
    """R3 §5 — bộ số SẮP ĐƯỢC DUYỆT, viết ra để người duyệt đọc trước khi ký.

    Cố ý dùng lại `_metrics` — đúng bộ chỉ tiêu mà trang Báo cáo hiện. Trang
    chốt kỳ mà tính riêng một bộ số sẽ cho người duyệt ký vào một con số họ
    chưa từng nhìn thấy ở đâu khác.

    `can_close` là một mệnh đề, không phải một lời khuyên: chốt một kỳ chưa
    đủ coverage nghĩa là duyệt một bộ số mà chính hệ thống từ chối gọi là
    CHÍNH THỨC (`R-S7`).
    """
    return {
        **_metrics(totals),
        "state": totals.state,
        "state_label": STATE_LABELS.get(totals.state, totals.state),
        "official": totals.coverage.is_complete,
        "coverage": coverage_cell(totals.coverage),
        "can_close": totals.lines > 0,
    }


def employee_rows(by_employee: list[tuple], company: bm.BusinessTotals) -> list[dict]:
    """Bảng nhân viên + dòng `TỔNG`.

    Dòng TỔNG lấy từ tổng KỲ chứ không cộng các dòng phía trên: một đơn có hai
    nhân viên được đếm ở cả hai dòng nhân viên, và dòng TỔNG phải đếm mỗi đơn
    đúng MỘT lần (`R-E5`).
    """
    # TASK-UIUX-001 — cột Nhóm viết tên người đọc được (`group_label`); mã
    # nhóm vẫn đi cùng dòng ở `employee_group_code` cho máy đọc.
    rows = [
        {"employee": name or UNKNOWN_EMPLOYEE,
         "employee_group": group_label(group), "employee_group_code": group or "",
         "key": name or "", "total_row": False, **_metrics(totals)}
        for name, group, totals in by_employee
    ]
    rows.append({"employee": "TỔNG", "employee_group": "", "employee_group_code": "",
                 "key": "", "total_row": True, **_metrics(company)})
    return rows


def brand_rows(
    by_brand: list[tuple], company: bm.BusinessTotals,
) -> list[dict]:
    """Bảng thương hiệu + dòng `TỔNG` (`PHB-06 §7`).

    Dòng TỔNG lấy từ tổng KỲ chứ không cộng các dòng phía trên — cùng lý do
    `employee_rows`: cột Đơn của các dòng trên cộng lại có thể lớn hơn tổng
    đơn của kỳ, nên một dòng TỔNG cộng dọc sẽ hiện một con số sai.

    `unknown_note` chỉ có mặt ở hai dòng "chưa xác định", và nó nói ĐÚNG lý do
    của chính dòng đó chứ không một câu chung — dòng đầu sửa được từ trang
    Nhân viên, dòng sau thì không.
    """
    rows = [
        {"brand": bucket.label, "key": bucket.key, "kind": bucket.kind,
         "known": bucket.known, "total_row": False,
         "unknown_note": BRAND_UNKNOWN_REASON_NOTES.get(bucket.kind),
         **_metrics(totals)}
        for bucket, totals in by_brand
    ]
    rows.append({"brand": "TỔNG", "key": "", "kind": "", "known": True,
                 "total_row": True, "unknown_note": None, **_metrics(company)})
    return rows


def brand_summary(
    coverage, reconciliation, *, period, totals: bm.BusinessTotals,
) -> dict:
    """Mô hình hiển thị của đầu trang thương hiệu.

    `reconciled` là kết quả một phép so ĐÃ CHẠY trên chính các con số đang
    hiện, không phải một lời khẳng định viết sẵn: nếu bảng lệch, trang phải
    nói ra ngay trên đầu thay vì để Owner tự phát hiện bằng máy tính tay.
    """
    return {
        "period_label": period_label(period),
        "authority": brand_identity.BRAND_AUTHORITY,
        "branded_lines": count(coverage.branded_lines),
        "identity_unresolved_lines": count(coverage.identity_unresolved_lines),
        "brand_absent_lines": count(coverage.brand_absent_lines),
        "total_lines": count(coverage.total_lines),
        "brand_complete": coverage.is_complete,
        "brand_unavailable": (
            coverage.total_lines > 0 and coverage.branded_lines == 0),
        "reconciled": reconciliation.is_exact,
        "reconcile_note": (BRAND_RECONCILED_NOTE if reconciliation.is_exact
                           else BRAND_RECONCILE_FAILED_NOTE),
        "note": _state_note(totals),
        "empty": totals.lines == 0,
    }


def share_cell(
    part: Optional[Decimal], whole: Optional[Decimal],
) -> dict:
    """Ô TỈ TRỌNG. `None` ⟹ `—`, không bao giờ `0%`.

    `missing` đi cùng con số trong CÙNG một dict để template không thể lấy
    chữ mà bỏ mất chiều "chưa nói được": một `0 %` in ra thay cho một ô trống
    sẽ đọc thành "đơn vị này không đóng góp gì", trong khi sự thật có thể là
    kỳ chưa có doanh thu nào để chia.
    """
    value = contribution.share_percent(part, whole)
    return {"text": percent(value), "missing": value is None}


def composition_rows(
    by_unit: list[tuple], company: bm.BusinessTotals,
) -> list[dict]:
    """Bảng cơ cấu theo đơn vị báo cáo + dòng `TỔNG` (`PHB-07`).

    Dòng TỔNG lấy từ tổng KỲ chứ không cộng các dòng phía trên — cùng lý do
    `employee_rows`/`brand_rows`: cột Đơn của các dòng trên cộng lại có thể
    lớn hơn tổng đơn của kỳ, nên một dòng TỔNG cộng dọc sẽ hiện số sai.

    Tỉ trọng của dòng TỔNG là `100 %` theo đúng phép chia mà mọi dòng khác
    dùng, không phải một hằng số viết cứng: khi kỳ chưa có doanh thu, ô đó
    hiện `—` giống hệt các dòng còn lại thay vì một `100 %` không có thật.
    """
    whole = company.sales_revenue
    rows = [
        {"unit": unit.label, "key": unit.key, "kind": unit.kind,
         "resolved": unit.resolved, "total_row": False,
         "share": share_cell(totals.sales_revenue, whole),
         **_metrics(totals)}
        for unit, totals in by_unit
    ]
    rows.append({"unit": "TỔNG", "key": "", "kind": "", "resolved": True,
                 "total_row": True, "share": share_cell(whole, whole),
                 **_metrics(company)})
    return rows


def composition_summary(
    reconciliation, *, period, totals: bm.BusinessTotals, units: int,
) -> dict:
    """Mô hình hiển thị của đầu trang cơ cấu.

    `reconciled` là kết quả một phép so ĐÃ CHẠY trên chính các con số đang
    hiện, không phải một lời khẳng định viết sẵn — cùng kỷ luật `brand_summary`.
    """
    return {
        "period_label": period_label(period),
        "units": count(units),
        "lines": count(totals.lines),
        "orders": count(totals.orders),
        "sales_revenue": _decimal(totals.sales_revenue),
        "sales_revenue_kvnd": _thousand_vnd(totals.sales_revenue),
        "reconciled": reconciliation.is_exact,
        "reconcile_note": (COMPOSITION_RECONCILED_NOTE if reconciliation.is_exact
                           else COMPOSITION_RECONCILE_FAILED_NOTE),
        "note": _state_note(totals),
        "empty": totals.lines == 0,
    }


def employee_detail(
    name: Optional[str], group: Optional[str], totals: bm.BusinessTotals, *,
    period, previous_totals, gia_dung: bool,
) -> dict:
    """Mô hình hiển thị của Employee V1 (`R-E1`…`R-E8`)."""
    return {
        **_metrics(totals),
        "employee": name or UNKNOWN_EMPLOYEE,
        "employee_group": group or "—",
        "period_label": period_label(period),
        "previous_label": (
            None if period is None else period_label(previous_period(period))),
        "mom": month_over_month(
            totals.sales_revenue,
            None if previous_totals is None else previous_totals.sales_revenue,
            has_period=period is not None,
            previous_has_lines=(
                previous_totals is not None and previous_totals.lines > 0),
        ),
        "note": _state_note(totals),
        "gia_dung_workflow": gia_dung,
    }


def employee_options(
    employees: list[tuple[Optional[str], Optional[str]]]
) -> list[dict]:
    return [{"value": name or "", "label": name or UNKNOWN_EMPLOYEE}
            for name, _group in employees]


def _derived_cell(value: Optional[Decimal], blockers: tuple[str, ...]) -> dict:
    """Một ô tiền SUY RA: có số, hoặc `—` KÈM lý do — không bao giờ bịa `0`.

    Chỉ thị `ORDER DETAIL TABLE`: *"Missing required inputs: show blank/N/A +
    reason rather than fabricate 0."* Một ô `0` trông như đã tính xong và ra
    kết quả bằng không; một ô `—` kèm câu "chưa có giá nhập" nói đúng sự thật
    và chỉ luôn việc phải làm.
    """
    # `DEC-212` — HỢP ĐỒNG Ô TIỀN của repo, giống hệt `gated_cell`/`money_cell`
    # đã dựng từ `R1` §9 và KHÔNG được đảo: `text` là bản VND ĐẦY ĐỦ (dùng cho
    # tooltip và cho mọi phép cộng kiểm chứng), `text_kvnd` là bản NGHÌN ĐỒNG
    # để in ra. Đặt ngược hai tên này là chỗ một `gated_cell` đi qua cùng một
    # macro sẽ in bản đầy đủ trong khi hàng bên cạnh in bản rút gọn — đúng lỗi
    # đã xảy ra một lần ở hàng TỔNG của bảng kê.
    if value is not None:
        return {"text": _decimal(value), "text_kvnd": _thousand_vnd(value),
                "missing": False, "reason": ""}
    reason = profit_gate.label(blockers[0]) if blockers else ""
    return {"text": "—", "text_kvnd": "—", "missing": True, "reason": reason}


# `TASK-OWNER-UIUX-002` — bảng "Theo nhân viên" của trang Báo cáo đọc CHÍNH
# phân hoạch mà không gian làm việc đã dùng từ `DEC-PHB02-08`
# (`reporting_sheets.sheet_key_of`), thay vì gộp lại theo `employee` một lần
# nữa ở đây. Đó là lý do bảng này KHÔNG phát minh ra một quy tắc cộng nào:
#
#     Vinh · Quý · Hiệp   nhóm `NOI_THANH` ⟹ dòng của họ nằm trên sheet
#                         Nội thành (hoặc Gia dụng nếu dòng là hàng gia dụng)
#     Gia dụng            bucket `ProductGroup` đã có từ ADR-106
#     mọi người còn lại   sheet của chính họ, giữ nguyên tên
#
# `sheet_key_of` là hàm TOÀN PHẦN, nên mỗi dòng thuộc ĐÚNG MỘT hàng của bảng
# và tổng các hàng luôn đúng bằng tổng kỳ (`§42`) — không hàng nào đếm hai
# lần, và Nội thành không bao giờ đứng cạnh Vinh/Quý/Hiệp.
#
# Thứ tự đọc: nhân viên theo thứ tự khai báo trong master (Tín Phát trước),
# rồi "chưa xác định", rồi Nội thành, cuối cùng là Gia dụng. Thứ tự là điều
# DUY NHẤT file này quyết định thêm; nó không đổi một con số nào.
_ROW_ORDER_EMPLOYEE = 0
_ROW_ORDER_UNRESOLVED = 1
_ROW_ORDER_NOI_THANH = 2
_ROW_ORDER_GIA_DUNG = 3

_SHEET_ROW_ORDER = {
    reporting_sheets.NOI_THANH_SHEET: _ROW_ORDER_NOI_THANH,
    reporting_sheets.GIA_DUNG_SHEET: _ROW_ORDER_GIA_DUNG,
    reporting_sheets.UNRESOLVED_SHEET: _ROW_ORDER_UNRESOLVED,
}


def sheet_display_order(sheet) -> tuple:
    """Khoá sắp xếp DÙNG CHUNG cho mọi màn hình liệt kê sheet: nhân viên theo
    thứ tự master (`config/employees.yaml`) trước, "chưa xác định" sau, rồi
    Nội thành, cuối cùng Gia dụng (`TASK-OWNER-UIUX-002` §5). Trang Báo cáo
    (`reporting_rows`) và thanh tab của không gian làm việc
    (`workspace_presentation.sheet_tabs`) đều sort theo ĐÚNG một hàm này —
    một nguồn thứ tự duy nhất, nên hai màn hình không bao giờ lệch nhau."""
    if sheet.employee:
        return (_ROW_ORDER_EMPLOYEE, employee_master_rank(sheet.employee),
                sheet.employee)
    return (_SHEET_ROW_ORDER[sheet.key], 0, "")


# `TASK-OWNER-UIUX-002` — MỘT khối "Cần kiểm tra" ở CUỐI trang, thay cho hai
# thẻ lớn từng chen giữa các chỉ tiêu. Hàm này KHÔNG quyết định điều kiện cảnh
# báo nào: nó nhận đúng hai mô hình đã dựng sẵn (`not_seen_warning` và
# `coverage_cell`) và chỉ xếp chúng thành danh sách. Không đếm lại số dòng,
# không đọc lại coverage, không thêm ngưỡng.
#
# Ba mức giọng giữ nguyên nghĩa của `DEC-190` §2 và KHÔNG bị hạ cấp: một tình
# trạng LỖI thật vẫn là `error` khi nằm trong danh sách này.
def pending_items(*, not_seen: Optional[dict], coverage: dict,
                  coverage_url: str) -> dict:
    """Danh sách việc cần soi, đã sắp theo mức nghiêm trọng giảm dần."""
    items = []
    if not_seen:
        items.append({
            "code": "not-seen",
            "title": "Sổ nạp gần nhất không thấy lại một số dòng",
            # `data-metric` của hai con số này là ĐÚNG tên cũ: khối cảnh báo
            # dời chỗ, nhưng thứ đọc được bằng máy thì không được dời theo.
            "count": str(not_seen["lines"]),
            "count_metric": "not-seen-lines",
            "count_unit": "dòng",
            "severity": "error",
            "note": not_seen["note"],
            "note_metric": "not-seen-warning",
            "action_label": "MỞ SỔ NẠP GẦN NHẤT",
            "snapshot_id": not_seen["snapshot_id"],
            "url": "",
        })
    if not coverage["complete"]:
        items.append({
            "code": "coverage",
            "title": "Còn dòng chưa tính được lợi nhuận",
            # `coverage`/`coverage-percent`/`coverage-note` ở lại dòng trạng
            # thái cạnh chính hai ô chỉ tiêu chúng quyết định; ở đây chỉ nhắc
            # lại con số cho người đang đọc danh sách việc phải làm.
            "count": coverage["text"],
            "count_metric": "pending-count",
            "count_unit": "",
            "severity": "warn",
            # `TASK-OWNER-UIUX-002` R3 — câu giải thích dài (`INCOMPLETE_NOTE`)
            # bị bỏ theo yêu cầu trực tiếp của chủ dự án: tiêu đề + số + danh
            # sách "thiếu cái gì, sửa ở đâu" (`coverage_reasons` bên dưới) đã
            # đủ để hành động, không cần thêm một đoạn văn giải thích.
            "note": "",
            "note_metric": "pending-note",
            "action_label": "MỞ BẢNG KÊ CHI TIẾT",
            "snapshot_id": None,
            "url": coverage_url,
        })
    return {"items": items, "count": len(items),
            "has_error": any(item["severity"] == "error" for item in items)}


def reporting_rows(sheet_totals: list[tuple], company: bm.BusinessTotals,
                   *, groups: dict) -> list[dict]:
    """Một hàng cho mỗi sheet của kỳ, cộng thêm hàng TỔNG.

    `sheet_totals` là `(Sheet, BusinessTotals)` của từng sheet — tầng route
    dựng chúng bằng `PeriodData.for_sheet`, tức là cùng một phép chiếu mà
    không gian làm việc dùng. `groups` là master `{tên: mã nhóm}`; cột Nhóm
    chỉ có nghĩa với một CON NGƯỜI, nên hàng nhóm/chưa xác định để `—`.
    """
    rows = []
    for sheet, totals in sorted(sheet_totals,
                                key=lambda item: sheet_display_order(item[0])):
        rows.append({
            "employee": sheet.label or UNKNOWN_EMPLOYEE,
            "key": sheet.employee or "",
            "sheet_key": sheet.key,
            "is_employee": bool(sheet.employee),
            "employee_group": (group_label(groups.get(sheet.employee))
                               if sheet.employee else "—"),
            "employee_group_code": (groups.get(sheet.employee) or ""
                                    if sheet.employee else ""),
            "total_row": False,
            **_metrics(totals),
        })
    rows.append({"employee": "TỔNG", "key": "", "sheet_key": "",
                 "is_employee": False, "employee_group": "",
                 "employee_group_code": "", "total_row": True,
                 **_metrics(company)})
    return rows


def detail_rows(details: list[dict], *, decisions=None,
                binding_exceptions: Optional[dict] = None) -> list[dict]:
    """Bảng kê chi tiết — một dòng hàng là một dòng, sửa được ngay tại chỗ.

    Đây là "trang tính" mà chỉ thị `ORDER DETAIL TABLE` mô tả, và nó cố ý
    KHÔNG phải một Excel trong trình duyệt:

    - Ô nhập được: **giá nhập** (`DEC-PHB02-02` §3 — sửa được kể cả khi đã
      AUTO-fill) và **nhân viên** (`OD-5`).
    - Ô suy ra: doanh thu, lợi nhuận KPI, DS quy đổi. Chúng không gõ được, và
      tự tính lại từ đầu vào hiện tại sau mỗi lần lưu. Không có nút "tính".
    - Doanh thu lấy NGUYÊN `total_sales` kế toán đã ghi, không thay bằng
      `số lượng × đơn giá` (chỉ thị: *"Do NOT casually replace authoritative
      net sales"*).

    Danh sách gồm CẢ dòng đã đủ giá: quyền sửa một giá tự động phải có chỗ
    thực hiện, và Owner cần nhìn thấy cả kỳ chứ không chỉ phần lỗi.

    `binding_exceptions` (R3 §1) là `{khoá dòng: ngoại lệ gắn dòng còn mở}`.
    Nó đi cùng dòng chứ không ở một trang riêng, vì hành động Owner cần làm là
    một hành động TRÊN DÒNG ĐÓ (gõ lại giá cho khoá mới, hay loại dòng cũ khỏi
    báo cáo) — một danh sách ngoại lệ tách khỏi bảng kê sẽ bắt Owner mở hai
    trang để làm một việc. `None`/rỗng cho ra chính xác hành vi trước R3.

    `decisions` (R2 §Gói 4) mang trạng thái phân loại HIỆU LỰC vào từng dòng,
    để bảng này vừa là bảng kê vừa là HÀNG ĐỢI XỬ LÝ: một dòng thiếu giá vì
    chưa phân loại và một dòng thiếu giá vì ngoài bảng giá hiện cùng một ô
    trống, nhưng cần hai hành động khác nhau. `None` cho ra chính xác hành vi
    trước R2.
    """
    binding_exceptions = binding_exceptions or {}
    rows = []
    for detail in details:
        line = detail["line"]
        identity = line_identity.state_of(detail, decisions=decisions)
        raised = binding_exceptions.get((
            detail["order_key"], detail["product_key"],
            detail["occurrence_index"]))
        provenance = line.purchase_provenance
        blockers = line.profit_blockers
        # `S121` — một dòng hàng cho ra MỘT dòng bảng khi không có chiết khấu,
        # HAI khi có. Phép tách nằm ở `business_metrics`, không ở đây: tầng này
        # vẫn chỉ đổi cách viết ra những con số đã có.
        product, *discount_parts = bm.display_contributions(line)
        rows.append({
            "kind": product.kind,
            "synthetic": False,
            "order_key": detail["order_key"],
            "product_key": detail["product_key"],
            "occurrence_index": detail["occurrence_index"],
            "sale_date": business_date(detail["sale_date"]),
            "product_raw": detail["product_raw"] or "—",
            "quantity": _decimal(product.quantity),
            **price_pair(product.sell_price, "sell_price"),
            **price_pair(product.purchase_price, "purchase_price"),
            # Ô NHẬP giữ VND ĐẦY ĐỦ (`PRICE_INPUT_NOTE`).
            "purchase_price_input": (
                "" if line.purchase_price is None else format_number(line.purchase_price)),
            "provenance": provenance,
            # `.get(...)` chứ không `[...]`: một provenance chưa có nhãn phải
            # hiện NGUYÊN VĂN mã của nó, không làm sập cả trang bảng kê.
            "provenance_label": PROVENANCE_LABELS.get(provenance, provenance),
            "pending": line.purchase_price is None,
            "overridden": provenance in (
                bm.PROVENANCE_MANUAL, bm.PROVENANCE_MANUAL_OVERRIDE),
            # `R2` — bối cảnh của chính lần Owner sửa: giá tự động NGAY TRƯỚC
            # lần sửa đó, và lúc sửa. Chỉ có ở dòng MANUAL_OVERRIDE; dòng
            # MANUAL không có giá tự động nào để thay, nên `—`.
            **price_pair(detail.get("override_auto_price_at_entry"),
                         "auto_price_at_entry"),
            "has_auto_price_at_entry": (
                detail.get("override_auto_price_at_entry") is not None),
            "entered_at": detail.get("override_entered_at") or "",
            # R2 §4.4 — hai nửa còn lại của provenance giá tay.
            "entered_by": detail.get("override_entered_by") or "",
            "override_reason": detail.get("override_reason") or "",
            # --- R2 §4.1: trạng thái phân loại HIỆU LỰC của dòng --------
            # Bốn giá trị, và mỗi giá trị dẫn tới một hành động khác nhau ở
            # cột thao tác. Gộp chúng lại sẽ làm hàng đợi xử lý mất nghĩa.
            "identity_classification": identity.classification,
            "identity_label": identity.label,
            "identity_title": identity.title,
            "identity_key": identity.identity_key,
            "can_identify": identity.classifiable,
            # --- R3 §1: ngoại lệ gắn dòng còn mở trên chính dòng này -----
            "binding_exception_id": None if raised is None else raised.id,
            "binding_exception_note": (
                "" if raised is None else _binding_note(raised)),
            "can_mark_out_of_catalog": bool(
                identity.identity_key is not None
                and identity.classification in (
                    line_identity.CLASS_NEEDS_REVIEW,
                    line_identity.CLASS_CONFLICT)),
            # --- ba ô SUY RA -------------------------------------------
            # Có chiết khấu ⟹ đây là số TRƯỚC chiết khấu; dòng "Chiết khấu"
            # ngay dưới mang phần âm, và hai dòng cộng lại đúng bằng canonical.
            "total_sales": _derived_cell(product.total_sales, ()),
            "kpi_profit": _derived_cell(product.kpi_profit, blockers),
            "converted_sales": _derived_cell(product.converted_sales, blockers),
            # --- nhân viên, sửa được ------------------------------------
            "employee": line.employee or UNKNOWN_EMPLOYEE,
            "employee_value": line.employee or "",
            "employee_resolved": line.employee_resolved,
            "employee_reassigned": line.employee_provenance == "MANUAL",
            "source_employee": line.source_employee,
            # --- cửa chặn và cảnh báo -----------------------------------
            "blockers": [{"code": code, "label": profit_gate.label(code)}
                         for code in blockers],
            "warnings": [{"code": code, "label": profit_gate.label(code)}
                         for code in line.warnings],
            # Mã pipeline hiện NGUYÊN VĂN dưới nhãn tiếng Việt: chúng là bằng
            # chứng lịch sử của lần chạy máy, không còn là cửa chặn.
            "pipeline_reasons": [REASON_DISPLAY_LABELS.get(code, code)
                                 for code in line.pending_reasons],
            "pipeline_status": line.status,
        })
        for part in discount_parts:
            rows.append(_discount_row(detail, line, part))
    return rows


def _binding_note(raised) -> str:
    """Một câu nói ĐỦ để Owner quyết, không phải một mã lỗi.

    Nó phải trả lời được ba câu: hệ thống đang phân vân giữa những khoá nào,
    quyết định nào đang treo ở đó, và vì sao dòng này lại mang một khoá mới.
    """
    decisions = ", ".join(raised.protected_decisions) or "một quyết định"
    candidates = ", ".join(str(index)
                           for index in raised.candidate_occurrence_indexes)
    return (
        f"Khi nạp lại sổ, hệ thống KHÔNG ghép chắc chắn được dòng này với các "
        f"khoá cũ ({candidates}) của cùng đơn và cùng mặt hàng — ở đó đang "
        f"treo {decisions}. Dòng nhận một khoá mới và không quyết định nào bị "
        f"gắn nhầm. Hãy kiểm tra rồi bấm ĐÃ XỬ LÝ."
    )


def _discount_row(detail: dict, line: bm.BusinessLine,
                  part: bm.LineContribution) -> dict:
    """Dòng "Chiết khấu" NGAY SAU dòng cha của nó (`DEC-180`).

    Nó cố ý mang CÙNG khoá nghiệp vụ với dòng cha (`order_key`,
    `product_key`, `occurrence_index`) vì nó là một phần TRÌNH BÀY của chính
    dòng đó — không phải một dòng hàng thứ hai, không phải một đơn riêng, và
    không bao giờ là một mặt hàng cần Product Identity.

    Ba điều dòng này KHÔNG BAO GIỜ mang, và mỗi điều đóng một cửa hỏng:

        `synthetic = True` ⟹ template không dựng form nào ⟹ không có đường
        ghi nào từ đây xuống database.
        `pending = False`  ⟹ nó không bao giờ nằm trong "CHƯA CÓ GIÁ NHẬP",
        dù cột Giá nhập KPI của nó có số (số đó là TIỀN CHIẾT KHẤU, đúng cách
        sổ tay cũ ghi, không phải một giá nhập tra được).
        `blockers/warnings` rỗng ⟹ nó không tự sinh thêm việc cho Owner; lý
        do thật đã nằm ở dòng cha ngay trên.

    Nhân viên lấy NGUYÊN của dòng cha, nên bộ lọc nhân viên và trang nhân
    viên luôn giữ hai dòng cạnh nhau.
    """
    return {
        "kind": part.kind,
        "synthetic": True,
        "order_key": detail["order_key"],
        "product_key": detail["product_key"],
        "occurrence_index": detail["occurrence_index"],
        "sale_date": business_date(detail["sale_date"]),
        "product_raw": DISCOUNT_ROW_LABEL,
        "quantity": _decimal(part.quantity),
        **price_pair(part.sell_price, "sell_price"),
        **price_pair(part.purchase_price, "purchase_price"),
        "purchase_price_input": "",
        "provenance": DISCOUNT_PROVENANCE,
        "provenance_label": DISCOUNT_PROVENANCE_LABEL,
        "pending": False,
        "overridden": False,
        "auto_price_at_entry": "—",
        "auto_price_at_entry_full": "—",
        "has_auto_price_at_entry": False,
        "entered_at": "",
        "entered_by": "",
        "override_reason": "",
        # Dòng "Chiết khấu" là số suy ra từ sổ, không phải một mặt hàng — nó
        # không có trạng thái phân loại nào và không được mời Owner xử lý.
        "identity_classification": None,
        "identity_label": None,
        "identity_title": None,
        "identity_key": None,
        "can_identify": False,
        "can_mark_out_of_catalog": False,
        # Lý do "—" (nếu có) đã hiện ở dòng cha ngay trên; lặp lại nó ở đây
        # chỉ làm màn hình nói cùng một việc hai lần.
        "total_sales": _derived_cell(part.total_sales, ()),
        "kpi_profit": _derived_cell(part.kpi_profit, ()),
        "converted_sales": _derived_cell(part.converted_sales, ()),
        "employee": line.employee or UNKNOWN_EMPLOYEE,
        "employee_value": line.employee or "",
        "employee_resolved": line.employee_resolved,
        "employee_reassigned": False,
        "source_employee": line.source_employee,
        "blockers": [],
        "warnings": [],
        "pipeline_reasons": [],
        "pipeline_status": line.status,
    }


def missing_price_rows(details: list[dict]) -> list[dict]:
    """Tên cũ của `detail_rows`, giữ lại cho các nơi còn gọi theo tên cũ."""
    return detail_rows(details)


#: Nhãn của mục "không đổi gì" trong ô chọn nhân viên (`FIND-R5-IR-01`).
#: Có dấu gạch hai đầu để nó KHÔNG đọc như một cái tên người khi nằm giữa
#: một danh sách tên người.
KEEP_EMPLOYEE_LABEL = "— Giữ nguyên —"


def assignable_employee_options(
    employees: list[tuple[str, Optional[str]]], *, keep_option: bool = False,
) -> list[dict]:
    """Danh sách nhân viên trong ô chọn của bảng kê (`OD-5`).

    Mặc định KHÔNG có mục trống: ở bảng kê chi tiết, ô này có nút gửi RIÊNG,
    nên mở nó ra và bấm nó nghĩa là bạn muốn gán. Muốn trả dòng về trạng thái
    chưa xác định thì dùng nút GỠ, và nút đó nói rõ nó làm gì — một mục trống
    lẫn giữa các tên người thì không.

    `keep_option=True` thêm MỘT mục "giữ nguyên" mang giá trị rỗng, và nó bắt
    buộc ở mọi chỗ ô chọn này đi cùng một nút gửi DÙNG CHUNG với thứ khác
    (R5 §4: `XONG` lưu cả giá lẫn nhân viên).

    Vì sao nó bắt buộc ở đó, và đây là `FIND-R5-IR-01` nguyên văn: một `<select>`
    mà KHÔNG option nào mang `selected` thì trình duyệt gửi option ĐẦU TIÊN —
    không phải chuỗi rỗng, không phải "không có gì". Một BH chưa có nhân viên,
    hay đang chia cho hai người, không có nhân viên hiệu lực DUY NHẤT để chọn
    sẵn; trước R5 điều đó vô hại vì ô ấy có nút gửi riêng, còn sau R5 nó làm
    cả đơn đổi chủ vì một cú bấm mà người dùng nghĩ là để lưu giá.

    Mục "giữ nguyên" đứng ĐẦU danh sách một cách có chủ đích: nó cũng là thứ
    trình duyệt rơi về nếu một ngày nào đó không option nào được chọn sẵn nữa.
    Fail-safe là "không đổi gì", không phải "gán cho người đầu bảng chữ cái".
    """
    options = [{"value": name, "label": name, "group": group}
               for name, group in employees]
    if not keep_option:
        return options
    return [{"value": "", "label": KEEP_EMPLOYEE_LABEL, "group": None},
            *options]


def target_cell(target: Optional[Decimal]) -> dict:
    """Một ô Target: con số VND, cách viết nghìn đồng, và trạng thái của nó.

    Ba trạng thái, và chúng KHÔNG bao giờ trông giống nhau (PHB-05 §7):

        chưa thiết lập  →  `unset=True`,  chữ "Chưa thiết lập"
        target = 0      →  `zero=True`,   số `0`
        target > 0      →  số

    `input_value` là chuỗi VND ĐẦY ĐỦ, không phân cách, để ô nhập trả lại
    đúng con số canonical khi Owner bấm LƯU mà không sửa gì — làm tròn hay
    rút gọn ở đây sẽ âm thầm đổi một con số Owner đã đặt.
    """
    if target is None:
        return {"text": TARGET_UNSET_LABEL, "text_kvnd": TARGET_UNSET_LABEL,
                "input_value": "", "unset": True, "zero": False}
    return {
        "text": _decimal(target),
        "text_kvnd": _thousand_vnd(target),
        "input_value": format(Decimal(target).normalize(), "f"),
        "unset": False,
        "zero": Decimal(target) == 0,
    }


def vs_target_cell(
    converted: Optional[Decimal], target: Optional[Decimal], *,
    state: str, official: bool,
) -> dict:
    """Ô "So target" — con số, HOẶC `—` kèm lý do; và trạng thái đi cùng.

    `state`/`official` là trạng thái của chính DS QUY ĐỔI mà ô này chia
    (`R-S7`/`R-E8`). PHB-05 §9 cấm dựng một hệ trạng thái thứ hai: nếu DS quy
    đổi còn CHƯA HOÀN CHỈNH thì So target cũng vậy, vì nó chỉ là con số đó
    chia cho một hằng số. Nhãn được lấy từ đúng `STATE_LABELS` mà mọi chỉ tiêu
    phụ thuộc coverage đang dùng.

    Không cap ở 100 %, không thay DS quy đổi bằng Doanh thu bán hàng: cả hai
    đều là sửa định nghĩa của một chỉ tiêu Owner đã dùng nhiều năm.
    """
    value = bm.vs_target_percent(converted, target)
    reason = bm.vs_target_reason(converted, target)
    return {
        "text": percent(value),
        "missing": value is None,
        "reason": "" if reason is None else TARGET_REASON_LABELS[reason],
        "reason_code": reason or "",
        "official": official and value is not None,
        "state": state,
        "state_label": STATE_LABELS[state],
    }


def target_rows(rows: list[tuple], *, editable: bool) -> list[dict]:
    """Bảng Target của một kỳ: một dòng cho mỗi nhân viên.

    `rows` đến từ `BusinessReportService.target_rows` — mỗi phần tử là
    `(tên, nhóm, chỉ tiêu kỳ, Target)`. Cột "DS quy đổi hiện tại" lấy NGUYÊN
    `totals.converted_sales` của cùng phân hoạch mà trang Báo cáo đang hiện;
    không có phép tính nghiệp vụ nào ở tầng này.

    Nhóm "chưa xác định nhân viên" (`name is None`) KHÔNG sửa được Target: nó
    không phải một người, và đặt target cho nó sẽ là đặt target cho một cái ô
    đếm. Nó vẫn hiện để tổng của bảng không giấu mất dòng nào.
    """
    result = []
    for name, group, totals, target in rows:
        state = totals.state
        result.append({
            "employee": name or UNKNOWN_EMPLOYEE,
            "employee_key": name or "",
            "employee_group": group_label(group),
            "employee_group_code": group or "",
            "is_employee": name is not None,
            "editable": editable and name is not None,
            "converted_sales": gated_cell(
                totals.converted_sales, totals.official_converted_sales, state),
            "target": target_cell(target),
            "vs_target": vs_target_cell(
                totals.converted_sales, target,
                state=state, official=totals.coverage.is_complete),
            "lines": count(totals.lines),
        })
    return result


def employee_target_block(
    totals: bm.BusinessTotals, target: Optional[Decimal],
) -> dict:
    """Hai ô Target/So target của trang MỘT nhân viên.

    Cùng hai hàm `target_cell`/`vs_target_cell` mà bảng Target dùng — hai
    màn hình không được có hai cách tính "So target".
    """
    return {
        "target": target_cell(target),
        "vs_target": vs_target_cell(
            totals.converted_sales, target,
            state=totals.state, official=totals.coverage.is_complete),
    }


def gia_dung_rows(products: list[dict]) -> list[dict]:
    """Một dòng cho mỗi MẶT HÀNG (không phải mỗi dòng chứng từ) để tick.

    Gộp theo `product_key` vì `DEC-PHB02-05` gọi Gia dụng là một
    *product-level override*: tick một lần cho mặt hàng, không phải tick lại
    cho từng lần bán của nó.
    """
    return [
        {
            "product_key": product["product_key"],
            "product_label": product["product_label"] or "—",
            "lines": count(product["lines"]),
            "sales": _decimal(product["sales"]),
            "current_group": product["current_group"],
            "current_label": (
                "Gia dụng" if product["current_group"] == "GIA_DUNG"
                else "Điện máy"),
            "classified": product["classified"],
            "gia_dung": product["current_group"] == "GIA_DUNG",
        }
        for product in products
    ]


# --------------------------------------------------------------------------
# `DEC-185` — MỘT biểu đồ doanh thu theo thời gian.
#
# Tầng này KHÔNG tính doanh thu và KHÔNG quyết định điểm nào thuộc mốc nào —
# `revenue_timeline` đã làm xong cả hai. Việc ở đây đúng bằng: đổi số sang
# chữ, và tính CHIỀU CAO tương đối của từng cột.
#
# Chiều cao là một phép chia trình bày, không phải một chỉ tiêu: nó chuẩn hoá
# theo cột LỚN NHẤT đang hiện, nên hai lần tải trang với hai mức gộp khác
# nhau cho hai thang khác nhau — đúng như hai biểu đồ khác nhau phải thế.
# Chính vì vậy nó nằm ở tầng trình bày chứ không ở `revenue_timeline`: một
# con số chỉ có nghĩa bên trong MỘT khung nhìn thì không phải dữ liệu nghiệp
# vụ.
# --------------------------------------------------------------------------

CHART_EMPTY_NOTE = (
    "Chưa có kỳ nào có doanh thu để vẽ. Nạp sổ ở tab Dữ liệu, hoặc nhập bản "
    "báo cáo cũ để thấy phần lịch sử."
)

CHART_PARTIAL_NOTE = (
    "Mốc có dấu ∗ được dựng từ ít tháng hơn số tháng nó bao trùm — bằng chứng "
    "chỉ có tới đó, và hệ thống không cộng thêm gì cho đủ."
)

CHART_UNDATED_NOTE = (
    "dòng chưa có ngày bán, nên không nằm trong mốc nào của biểu đồ"
)

# Hình học của biểu đồ ĐƯỜNG (`TASK-OWNER-UIUX-002` R4), đơn vị SVG.
#
# `TASK-OWNER-UIUX-004` §1 đổi từ bề rộng TĂNG THEO SỐ ĐIỂM (mỗi điểm
# `_CHART_STEP_X` cũ = 64px, nên 6 điểm ra một biểu đồ bé tí giữa một card
# rộng) sang một `viewBox` CỐ ĐỊNH (`_CHART_VIEW_W`), co giãn 100% bề rộng
# card qua CSS (`width: 100%` trên `<svg>`, `preserveAspectRatio="none"` đã
# có sẵn). Card luôn ĐẦY, và khi kỳ đang xem CHƯA đi hết, đường chỉ vẽ tới
# đúng điểm dữ liệu cuối rồi dừng — phần còn lại để trống, không suy diễn.
_CHART_PLOT_H = 160
_CHART_VIEW_W = 960
#: `DEC-211` — Owner: "biểu đồ được thể hiện đầy đủ từ mép trái sang mép
#: phải". Đệm bằng 0 để mốc đầu nằm ĐÚNG mép trái và mốc cuối ĐÚNG mép phải,
#: thay vì thụt vào 8 đơn vị mỗi bên. Nhãn trục Y nằm ở một khối riêng ngoài
#: `<svg>` nên không có gì bị cắt khi bỏ đệm.
_CHART_PAD_X = 0

#: Ngày cố định làm nhãn trục X ở mức Ngày — số tròn Owner yêu cầu, không
#: phải MỌI ngày có dữ liệu. Ngày nào không tồn tại trong tháng đang xem
#: (vd 30 của tháng 2) tự động bị lọc bởi điều kiện `<= days_in_month`.
_CHART_DAY_TICKS = (5, 10, 15, 20, 25, 30)


def _chart_day_container(period: Optional[tuple[int, int]]):
    """`(days_in_month)` của kỳ đang xem — trục X mức Ngày cần con số này để
    đặt vị trí LỊCH của từng điểm (ngày mấy trên tổng bao nhiêu ngày), chứ
    không phải thứ tự điểm thứ mấy trong danh sách bằng chứng có được."""
    if period is None:
        return None
    year, month = period
    return calendar.monthrange(year, month)[1]


def _chart_quarter_container(period: Optional[tuple[int, int]]):
    """`(ngày đầu quý, tổng số ngày của quý)` chứa kỳ đang xem — dùng
    `window_bounds(WEEK, ...)` đã có sẵn thay vì tính lại ranh giới quý."""
    if period is None:
        return None
    bounds = revenue_timeline.window_bounds(revenue_timeline.WEEK, period)
    if bounds is None:
        return None
    start = date.fromisoformat(bounds[0])
    end = date.fromisoformat(bounds[1])
    return start, (end - start).days


def _chart_x_fraction(key: str, granularity: str, period: Optional[tuple[int, int]],
                       index: int, count: int) -> float:
    """Vị trí NGANG (0..1) của một điểm trên trục X.

    Ngày/Tuần/Tháng có một CONTAINER cố định (tháng/quý/năm của kỳ đang
    xem) nên vị trí tính theo LỊCH — đúng ngày/tuần/tháng nào trong
    container đó — thay vì theo thứ tự điểm. Quý/Năm không bị khoanh
    (`TASK-OWNER-UIUX-003` §2), không có container cố định để so, nên giữ
    cách chia đều theo THỨ TỰ điểm như cũ.
    """
    if granularity == revenue_timeline.DAY:
        days_in_month = _chart_day_container(period)
        if days_in_month:
            day = int(key[8:10])
            return (day - 1) / max(days_in_month - 1, 1)
    elif granularity == revenue_timeline.WEEK:
        container = _chart_quarter_container(period)
        if container:
            start, quarter_days = container
            elapsed = (date.fromisoformat(key) - start).days
            return max(0.0, min(1.0, elapsed / max(quarter_days - 1, 1)))
    elif granularity == revenue_timeline.MONTH:
        if period is not None:
            month = int(key[5:7])
            return (month - 1) / 11
    return index / max(count - 1, 1)


def _chart_x_ticks(granularity: str, period: Optional[tuple[int, int]]) -> list[dict]:
    """Nhãn trục X CỐ ĐỊNH theo lịch (Ngày/Tuần/Tháng) — tách khỏi điểm dữ
    liệu thật: một mốc lịch tròn (5, 10, 15...) hiện ra dù kỳ đó chưa có
    dòng nào, và một điểm dữ liệu không rơi đúng mốc tròn vẫn được vẽ (bằng
    chấm), chỉ không mang nhãn riêng — tránh "một bức tường chữ" của
    `_CHART_MAX_X_LABELS` cũ mà vẫn không bịa thêm dữ liệu nào.
    """
    if period is None:
        return []
    if granularity == revenue_timeline.DAY:
        days_in_month = _chart_day_container(period)
        if not days_in_month:
            return []
        return [
            {"x_pct": (day - 1) / max(days_in_month - 1, 1) * 100,
             "label": f"{day:02d}"}
            for day in _CHART_DAY_TICKS if day <= days_in_month
        ]
    if granularity == revenue_timeline.WEEK:
        container = _chart_quarter_container(period)
        if not container:
            return []
        start, quarter_days = container
        ticks = []
        cursor = start
        for _ in range(3):
            elapsed = (cursor - start).days
            ticks.append({
                "x_pct": max(0.0, min(1.0, elapsed / max(quarter_days - 1, 1))) * 100,
                "label": f"{cursor.day:02d}/{cursor.month:02d}",
            })
            next_month = cursor.month + 1
            next_year = cursor.year
            if next_month > 12:
                next_month, next_year = 1, next_year + 1
            cursor = date(next_year, next_month, 1)
        return ticks
    if granularity == revenue_timeline.MONTH:
        return [
            {"x_pct": month / 11 * 100, "label": f"Th{month + 1}"}
            for month in range(12)
        ]
    return []
#: Số đường lưới ngang, KHÔNG kể đường đáy (0). Bốn đường + đáy = năm mốc,
#: đủ để đọc độ lớn tương đối mà không dày đặc như một tờ kẻ ô ly.
_CHART_Y_TICKS = 4
#: Trần hiển thị của Ox: quá nhiều mốc thì MỖI nhãn dưới MỖI điểm là một bức
#: tường chữ không ai đọc nổi (đúng thứ Owner gọi là "kinh khủng"). Mọi điểm
#: vẫn có dữ liệu đầy đủ để máy đọc và để rê chuột xem — chỉ chữ hiện dưới
#: trục là thưa lại.
_CHART_MAX_X_LABELS = 8


def _chart_nice_ceiling(value: Decimal) -> Decimal:
    """Trần "tròn" phía trên `value`, dùng làm đỉnh trục Y.

    Neo lưới vào chính đỉnh dữ liệu sẽ luôn vẽ đường ra chạm mép trên — không
    khoảng thở, và đường lưới trên cùng không mang một con số tròn để đọc
    nhẩm. Tham chiếu đúng cách các thư viện biểu đồ vẫn làm: làm tròn LÊN một
    trong các bậc 1/2/2,5/5/10 nhân luỹ thừa của 10 gần `value` nhất.
    """
    if value <= 0:
        return Decimal(0)
    magnitude = math.floor(math.log10(float(value)))
    scale = Decimal(10) ** magnitude
    normalized = value / scale
    for step in (Decimal("1"), Decimal("2"), Decimal("2.5"), Decimal("5"), Decimal(10)):
        if normalized <= step:
            return (step * scale).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return (Decimal(10) * scale).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _chart_y_axis(ceiling: Decimal, *, money: bool = True) -> list[dict]:
    """Nhãn + toạ độ của các đường lưới ngang, từ đỉnh xuống đáy.

    `money=True` (mặc định, biểu đồ Doanh thu) viết nhãn theo NGHÌN ĐỒNG.
    `money=False` (biểu đồ SỐ ĐƠN — `paired_count_chart`) viết nguyên số
    đếm: chia 1.000 một trần nhỏ như "3 đơn" cho ra toàn số 0 trên trục Y,
    đúng lỗi từng có khi hai biểu đồ dùng chung hàm này mà không tách đơn
    vị — sửa ở `DEC-214`.
    """
    ticks = []
    for i in range(_CHART_Y_TICKS, -1, -1):
        fraction = Decimal(i) / Decimal(_CHART_Y_TICKS)
        value = (ceiling * fraction).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        if ceiling <= 0:
            label = "0"
        else:
            label = _thousand_vnd(value) if money else format_number(value)
        ticks.append({
            "y": _CHART_PLOT_H - round(float(fraction) * _CHART_PLOT_H),
            "label": label,
        })
    return ticks


#: `TASK-OWNER-UIUX-003` §2 — câu chữ của `F-E` khi biểu đồ bị KHOANH cửa sổ
#: quanh kỳ đang chọn (Ngày/Tuần/Tháng). Không windowed (Quý/Năm, hoặc đang
#: xem "Toàn bộ dữ liệu") vẫn dùng nguyên `revenue_timeline.CHART_SCOPE_NOTE`
#: — F-E không bị bỏ, chỉ ĐỔI CÂU theo đúng phạm vi thật của từng trường hợp,
#: để không câu nào trên trang nói sai biểu đồ đang nhìn xa tới đâu.
_CHART_WINDOW_SCOPE_TEXT = {
    revenue_timeline.DAY: (
        "Ở mức Ngày, biểu đồ chỉ hiện các ngày trong tháng {label} — "
        "chưa phải toàn bộ dữ liệu."),
    revenue_timeline.WEEK: (
        "Ở mức Tuần, biểu đồ chỉ hiện các tuần trong {label} — "
        "chưa phải toàn bộ dữ liệu."),
    revenue_timeline.MONTH: (
        "Ở mức Tháng, biểu đồ chỉ hiện các tháng trong {label} — "
        "chưa phải toàn bộ dữ liệu."),
}


def _chart_scope_note(granularity: str, window_label: str) -> str:
    if window_label:
        return _CHART_WINDOW_SCOPE_TEXT[granularity].format(label=window_label)
    return revenue_timeline.CHART_SCOPE_NOTE


def _slot_x(index: int, size: int) -> float:
    """Toạ độ X của vị trí thứ `index` trong một cửa sổ `size` mốc.

    Trục X của R5 §3 là trục TƯƠNG ĐỐI: nó đo "mốc thứ mấy của cửa sổ", không
    đo ngày tháng. Đó là điều kiện để hai cửa sổ khác thời gian nằm chồng
    được lên nhau — và cũng là lý do `_chart_x_fraction` (toạ độ theo vị trí
    lịch trong container) không dùng được ở chế độ hai đường.
    """
    if size <= 1:
        return 0.0
    return index / (size - 1)


def _slot_points(slots, *, ceiling: Decimal, size: int) -> list[dict]:
    """Toạ độ + nhãn của từng vị trí có dữ liệu. Khoảng trống KHÔNG có mặt.

    Một mốc chưa có bằng chứng không sinh ra phần tử nào: không chấm, không
    ô rê chuột, không `data-revenue`. Vẽ nó thành một chấm ở đáy là vẽ ra
    con số 0 mà không ai đo được.
    """
    out = []
    for slot in slots:
        if slot.is_gap:
            continue
        x = _CHART_PAD_X + _slot_x(slot.index, size) * (_CHART_VIEW_W - 2 * _CHART_PAD_X)
        y_fraction = float(slot.revenue / ceiling) if ceiling > 0 else 0.0
        out.append({
            "index": slot.index,
            "key": slot.key,
            "label": slot.label,
            "revenue_raw": format(slot.revenue, "f"),
            "revenue": format_number(slot.revenue),
            "revenue_kvnd": _thousand_vnd(slot.revenue),
            "origin": slot.origin or revenue_timeline.ORIGIN_CURRENT,
            "legacy": slot.origin == revenue_timeline.ORIGIN_LEGACY,
            "mixed": slot.origin == revenue_timeline.ORIGIN_MIXED,
            "partial": slot.partial,
            "x": x,
            "x_pct": x / _CHART_VIEW_W * 100,
            "y": _CHART_PLOT_H - round(y_fraction * _CHART_PLOT_H),
        })
    return out


def _slot_polylines(points: list[dict]) -> list[str]:
    """Đường vẽ, CẮT tại mỗi khoảng trống.

    Trả về nhiều đoạn thay vì một chuỗi: nối thẳng qua một mốc không có bằng
    chứng sẽ vẽ ra một đoạn dốc mà người đọc hiểu thành "doanh thu đi từ đây
    tới kia", trong khi sự thật là hệ thống không biết ở giữa có gì.
    """
    segments, run = [], []
    previous = None
    for point in points:
        if previous is not None and point["index"] != previous + 1:
            if len(run) > 1:
                segments.append(" ".join(run))
            run = []
        run.append(f"{point['x']},{point['y']}")
        previous = point["index"]
    if len(run) > 1:
        segments.append(" ".join(run))
    return segments


def _slot_title(point: dict, window_label: str, *, unit: str = "đồng") -> str:
    """Lời giải thích của MỘT chấm — nói rõ nó thuộc cửa sổ nào.

    Không nói rõ là đúng lớp lỗi mà hai đường sinh ra: hai chấm cùng vị trí,
    hai con số khác nhau, và không gì trên màn hình cho biết cái nào là kỳ
    này.

    `unit` mặc định `"đồng"` để mọi nơi gọi cũ giữ nguyên từng ký tự. R6 dùng
    lại ĐÚNG hàm này cho biểu đồ SỐ ĐƠN với `unit="đơn"` — một chuỗi tooltip
    thứ hai sẽ là chỗ hai biểu đồ cùng trang mô tả cùng một mốc bằng hai giọng
    khác nhau.
    """
    parts = [f"{window_label} · {point['label']}",
             f"{point['revenue']} {unit}"]
    # Chiều origin của `DEC-166 E` vẫn phải đọc được, và vẫn chỉ đọc được ở
    # đây — trong lời của đúng cái mốc đó, bằng ngôn ngữ THỜI GIAN, không
    # bằng một bộ chọn nguồn.
    if point["legacy"]:
        parts.append(revenue_timeline.LEGACY_POINT_NOTE)
    elif point["mixed"]:
        parts.append(revenue_timeline.MIXED_POINT_NOTE)
    return " — ".join(parts)


#: `DEC-215` — Owner: trục X của biểu đồ hai-cửa-sổ lặp lại năm trên mỗi
#: nhãn ("21/08/2026", "25/08/2026", …) trong khi dòng "Kỳ này: … → …" ngay
#: trên biểu đồ đã nói năm một lần. Tám nhãn cùng năm là chữ thừa trên một
#: trục hẹp. Rút gọn CHỈ ở đây — nhãn trục, không phải `bucket_of` hay
#: tooltip (`_slot_title` vẫn dùng `slot.label` đầy đủ): một người rê chuột
#: vào một chấm để tra cứu chính xác vẫn cần thấy năm, nhất là ở mức Tuần
#: khi cửa sổ có thể vắt qua hai năm dương lịch (`DEC-211`).
def _axis_tick_label(key: str, label: str, granularity: str) -> str:
    """Nhãn trục X ngắn — DD/MM cho Ngày/Tuần, giữ nguyên `label` cho các
    mức còn lại (Tháng/Quý/Năm đã đủ ngắn, và năm ở đó KHÔNG lặp vô nghĩa
    — một cửa sổ 12 tháng thật sự trải qua hai năm dương lịch khác nhau).

    Đọc lại NGÀY THẬT từ `key` (ISO) rồi viết lại, không cắt chuỗi
    `label`: cắt chuỗi giả định một định dạng cụ thể và sẽ âm thầm sai nếu
    `bucket_of` đổi cách viết nhãn; đọc lại ngày rồi viết lại luôn đúng bất
    kể `label` được viết thế nào.
    """
    if granularity in (revenue_timeline.DAY, revenue_timeline.WEEK):
        day = date.fromisoformat(key)
        return f"{day.day:02d}/{day.month:02d}"
    return label


def _window_x_ticks(slots, *, size: int, granularity: str) -> list[dict]:
    """Nhãn trục X của một cửa sổ — thưa đều, và KHÔNG chồng lên nhãn cuối.

    Mốc CUỐI luôn có nhãn: nó là mép phải, tức là "đến bao giờ", và một biểu
    đồ không nói được điều đó thì mọi mốc còn lại cũng mất chỗ neo. Nhưng mốc
    cuối không rơi đúng bước thưa, nên nó hạ cánh sát ngay cạnh nhãn thưa gần
    nhất: với cửa sổ 31 ngày, bước 4, hai nhãn cuối là mốc 28 và mốc 30 —
    cách nhau 6% bề rộng trong khi mỗi nhãn rộng hơn thế, và chúng chồng lên
    nhau thành một vệt chữ không đọc được.

    Cách xử lý: nhãn thưa nào cách mốc cuối CHƯA ĐỦ MỘT BƯỚC thì bỏ đi. Bỏ
    cái thưa chứ không bỏ cái cuối — mất mép phải là mất nhiều hơn. Khoảng
    trống rộng hơn một bước ở cuối trục là cái giá đã biết, và nó nhỏ hơn
    hẳn cái giá của hai nhãn đè lên nhau.
    """
    if size <= 0:
        return []
    stride = max(1, math.ceil(size / _CHART_MAX_X_LABELS))
    last = size - 1
    keep = [slot for slot in slots
            if slot.index == last
            or (slot.index % stride == 0 and last - slot.index >= stride)]
    return [
        {"x_pct": (_CHART_PAD_X + _slot_x(slot.index, size)
                   * (_CHART_VIEW_W - 2 * _CHART_PAD_X)) / _CHART_VIEW_W * 100,
         "label": _axis_tick_label(slot.key, slot.label, granularity)}
        for slot in keep
    ]


def paired_revenue_chart(
    paired, *, granularity: str, has_legacy_months: bool = False,
    undated: int = 0,
) -> dict:
    """Mô hình hiển thị của biểu đồ HAI CỬA SỔ (`DEC-R5-02`).

    Hai chuỗi, MỘT trục, MỘT trần tròn. Trần dùng chung là điều bắt buộc, chứ
    không phải một lựa chọn thẩm mỹ: hai đường tự chuẩn hoá theo đỉnh riêng
    sẽ trông ngang nhau kể cả khi một cửa sổ bán gấp ba cửa sổ kia — và cả
    biểu đồ tồn tại để trả lời đúng câu đó.
    """
    both = [slot for slot in (*paired.current, *paired.comparison)
            if not slot.is_gap]
    peak = max((slot.revenue for slot in both), default=Decimal(0))
    ceiling = _chart_nice_ceiling(peak)
    size = paired.size
    bars = _slot_points(paired.current, ceiling=ceiling, size=size)
    previous_bars = _slot_points(paired.comparison, ceiling=ceiling, size=size)
    for point in bars:
        point["title"] = _slot_title(point, paired.current_label)
    for point in previous_bars:
        point["title"] = _slot_title(point, paired.comparison_label)

    # Nhãn trục X đọc từ CỬA SỔ HIỆN TẠI — trục là tương đối, nên nó chỉ
    # mang được một bộ nhãn thời gian, và bộ đúng là bộ của cửa sổ người
    # dùng đang hỏi về. Cửa sổ so sánh nói tên mốc của nó trong tooltip.
    x_ticks = _window_x_ticks(paired.current, size=size, granularity=granularity)
    current_total = sum((slot.revenue for slot in paired.current
                         if not slot.is_gap), Decimal(0))
    comparison_total = sum((slot.revenue for slot in paired.comparison
                            if not slot.is_gap), Decimal(0))
    return {
        "svg_width": _CHART_VIEW_W,
        "svg_height": _CHART_PLOT_H,
        "y_axis": _chart_y_axis(ceiling),
        "x_ticks": x_ticks,
        "fixed_x_axis": True,
        "paired": True,
        "polylines": _slot_polylines(bars),
        "comparison_polylines": _slot_polylines(previous_bars),
        "granularity": granularity,
        "options": [
            {"key": key, "label": label, "on": key == granularity}
            for key, label in revenue_timeline.GRANULARITIES
        ],
        "bars": bars,
        "comparison_bars": previous_bars,
        "current_label": paired.current_label,
        "comparison_label": paired.comparison_label,
        "current_range": _window_range_text(paired.current),
        "comparison_range": _window_range_text(paired.comparison),
        "empty": not both,
        "empty_note": CHART_EMPTY_NOTE,
        "note": revenue_timeline.CHART_NOTE,
        "scope_note": revenue_timeline.COMPARISON_SCOPE_TEXT.format(
            current=_window_range_text(paired.current),
            comparison=_window_range_text(paired.comparison)),
        "comparison_note": revenue_timeline.COMPARISON_NOTE,
        "gap_note": revenue_timeline.GAP_NOTE,
        "has_gap": any(slot.is_gap for slot in (*paired.current,
                                                *paired.comparison)),
        "windowed": True,
        "total": format_number(current_total),
        "total_kvnd": _thousand_vnd(current_total),
        "comparison_total_kvnd": _thousand_vnd(comparison_total),
        "has_partial": any(bar["partial"] for bar in (*bars, *previous_bars)),
        "partial_note": CHART_PARTIAL_NOTE,
        "no_daily_legacy_note": (
            revenue_timeline.NO_DAILY_LEGACY_NOTE
            if granularity in (revenue_timeline.DAY, revenue_timeline.WEEK)
            and has_legacy_months and not any(bar["legacy"] for bar in bars)
            else None),
        "undated": undated,
        "undated_note": CHART_UNDATED_NOTE,
    }


# --- R6 §2: biểu đồ SỐ ĐƠN, cùng engine cửa sổ với biểu đồ doanh thu --------
#
# Nó nằm ở ĐÂY, cạnh `paired_revenue_chart`, chứ không ở một module trình bày
# riêng của R6 — và đó là một quyết định về ranh giới, không phải sự tiện tay:
# hai biểu đồ phải chia mốc, chọn cửa sổ, cắt đường tại khoảng trống và tính
# trần tròn GIỐNG NHAU, nên chúng phải dùng chung đúng những hàm dựng hình đó.
# Đặt bản sao thứ hai ở một file khác là mở đường cho hai trục X trôi khỏi
# nhau, và khi ấy hai điểm cùng vị trí trên hai biểu đồ sẽ là hai mốc thời
# gian khác nhau mà không gì trên trang nói ra.
#
# `revenue_timeline` KHÔNG được sửa một dòng nào cho việc này: R6 dựng
# `Point`/`PairedSeries` bằng chính `paired_series()` của R5, chỉ với SỐ ĐƠN
# thay cho số tiền ở trường `revenue`.

COUNT_CHART_UNIT = "đơn"

COUNT_CHART_EMPTY_NOTE = (
    "Chưa có đơn nào rơi vào cửa sổ đang xem, nên không có gì để vẽ. Đây khác "
    "\"không có đơn nào\": một mốc chỉ được vẽ số 0 khi khoảng ngày ấy nằm "
    "trong một sổ đã được xác nhận đầy đủ."
)


def paired_count_chart(
    paired, *, granularity: str, undated_orders: int = 0,
    unit: str = COUNT_CHART_UNIT, title_note: str = "",
) -> dict:
    """Mô hình hiển thị của biểu đồ SỐ ĐƠN hai cửa sổ (`R6 §2`).

    Cùng hình dạng dict với `paired_revenue_chart` để một macro template duy
    nhất vẽ được cả hai, nhưng các ô CHỮ nói bằng đơn vị đếm: `total_text` là
    "N đơn", không phải "N nghìn đồng". Trộn hai đơn vị vào cùng một ô là cách
    một người đọc nhanh lấy số đơn làm số tiền.

    `paired` là `revenue_timeline.PairedSeries` mà trường `revenue` của mỗi
    `Slot` mang SỐ ĐƠN. Việc dùng lại đúng value object của R5 là điều kiện để
    hai biểu đồ trên cùng trang có cùng cửa sổ, cùng trục và cùng quy ước
    khoảng trống — xem chú thích ở đầu khối này.
    """
    both = [slot for slot in (*paired.current, *paired.comparison)
            if not slot.is_gap]
    peak = max((slot.revenue for slot in both), default=Decimal(0))
    ceiling = _chart_nice_ceiling(peak)
    size = paired.size
    bars = _slot_points(paired.current, ceiling=ceiling, size=size)
    previous_bars = _slot_points(paired.comparison, ceiling=ceiling, size=size)
    for point in bars:
        point["title"] = _slot_title(point, paired.current_label, unit=unit)
    for point in previous_bars:
        point["title"] = _slot_title(point, paired.comparison_label, unit=unit)
    x_ticks = _window_x_ticks(paired.current, size=size, granularity=granularity)
    current_total = sum((slot.revenue for slot in paired.current
                         if not slot.is_gap), Decimal(0))
    comparison_total = sum((slot.revenue for slot in paired.comparison
                            if not slot.is_gap), Decimal(0))
    return {
        "svg_width": _CHART_VIEW_W,
        "svg_height": _CHART_PLOT_H,
        "y_axis": _chart_y_axis(ceiling, money=False),
        "x_ticks": x_ticks,
        "fixed_x_axis": True,
        "paired": True,
        "unit": unit,
        "polylines": _slot_polylines(bars),
        "comparison_polylines": _slot_polylines(previous_bars),
        "granularity": granularity,
        "options": [
            {"key": key, "label": label, "on": key == granularity}
            for key, label in revenue_timeline.GRANULARITIES
        ],
        "bars": bars,
        "comparison_bars": previous_bars,
        "current_label": paired.current_label,
        "comparison_label": paired.comparison_label,
        "current_range": _window_range_text(paired.current),
        "comparison_range": _window_range_text(paired.comparison),
        "empty": not both,
        "empty_note": COUNT_CHART_EMPTY_NOTE,
        "note": title_note or revenue_timeline.CHART_NOTE,
        "scope_note": revenue_timeline.COMPARISON_SCOPE_TEXT.format(
            current=_window_range_text(paired.current),
            comparison=_window_range_text(paired.comparison)),
        "comparison_note": revenue_timeline.COMPARISON_NOTE,
        "gap_note": revenue_timeline.GAP_NOTE,
        "has_gap": any(slot.is_gap for slot in (*paired.current,
                                                *paired.comparison)),
        "windowed": True,
        "total": format_number(current_total),
        "total_text": f"{format_number(current_total)} {unit}",
        "comparison_total_text": f"{format_number(comparison_total)} {unit}",
        "has_partial": any(bar["partial"] for bar in (*bars, *previous_bars)),
        "partial_note": CHART_PARTIAL_NOTE,
        "no_daily_legacy_note": None,
        "undated": undated_orders,
        "undated_note": (
            "đơn không có ngày bán nào, nên không rơi vào mốc nào của biểu đồ. "
            "Chúng vẫn nằm đủ trong tổng số đơn của phạm vi."),
    }



def _window_range_text(slots) -> str:
    """`"<mốc đầu> → <mốc cuối>"` của một cửa sổ, theo LỊCH.

    Đọc từ mốc đầu và mốc cuối của cửa sổ chứ không từ mốc đầu/cuối CÓ dữ
    liệu: cửa sổ là một khoảng thời gian cố định, và thu nó lại quanh phần
    có số sẽ nói sai về khoảng mà biểu đồ đang nhìn.
    """
    if not slots:
        return ""
    return f"{slots[0].label} → {slots[-1].label}"


def revenue_chart(
    points, *, granularity: str, has_legacy_months: bool = False,
    undated: int = 0, window_label: str = "",
    period: Optional[tuple[int, int]] = None,
) -> dict:
    """Mô hình hiển thị của biểu đồ — MỘT biểu đồ, năm nút đổi mức gộp.

    `period` là kỳ ĐANG XEM (không phải kỳ của từng điểm) — chỉ dùng để
    dựng CONTAINER lịch cho trục X ở mức Ngày/Tuần/Tháng (`§1`). `None` khi
    không có kỳ nào đang chọn ("Toàn bộ dữ liệu"): trục X khi đó rơi về
    cách chia đều theo thứ tự điểm như trước `TASK-OWNER-UIUX-004`.
    """
    peak = max((point.revenue for point in points), default=Decimal(0))
    ceiling = _chart_nice_ceiling(peak)
    bars = []
    for point in points:
        bars.append({
            "key": point.key,
            "label": point.label,
            # Giá trị MÁY đọc, không định dạng: `data-revenue` là chỗ test
            # và công cụ ngoài đọc con số, và một dấu chấm phân nhóm hàng
            # nghìn trong đó buộc mỗi bên đọc phải tự gỡ định dạng vi-VN ra
            # — một phép biến đổi mà một dòng có phần thập phân sẽ làm hỏng.
            "revenue_raw": format(point.revenue, "f"),
            "revenue": format_number(point.revenue),
            "revenue_kvnd": _thousand_vnd(point.revenue),
            "legacy": point.is_legacy,
            # Origin THẬT của mốc, không phải một phép suy hai nhánh. Từ khi
            # quý/năm gộp các tháng đã giải (`F-C`), một mốc có thể mang
            # `MIXED_AUTHORITY`, và `legacy else PIPELINE_GENERATED` sẽ khai
            # nó là số mới thuần — sai đúng ở chiều mà `DEC-166 E` bắt phải
            # đọc được.
            "origin": point.origin,
            "mixed": point.is_mixed,
            "partial": point.partial,
            "covered_months": point.covered_months,
            "span_months": point.span_months,
            "title": _chart_bar_title(point),
        })
    day_level = granularity in (revenue_timeline.DAY, revenue_timeline.WEEK)
    # `TASK-OWNER-UIUX-004` §1 — hình học của ĐƯỜNG, tính ở tầng trình bày và
    # vẽ bằng SVG tĩnh: không JavaScript, không thư viện, in ra giấy vẫn
    # đúng (JS ở `app.js` chỉ THÊM tooltip khi rê chuột — không đổi hình học
    # gốc). Toạ độ Y so với TRẦN TRÒN (`ceiling`), không so với đỉnh dữ liệu
    # — nên đường lưới và đường doanh thu luôn cùng một thước đo. Toạ độ X
    # nay theo VỊ TRÍ LỊCH trong container của kỳ đang xem (`_chart_x_
    # fraction`), không theo thứ tự điểm — nên khi kỳ chưa đi hết, đường
    # dừng đúng chỗ và phần còn lại của card để trống, không co giãn ra cho
    # vừa đủ mấy điểm đang có.
    count = len(bars)
    fixed_x_axis = (
        period is not None
        and granularity in (revenue_timeline.DAY, revenue_timeline.WEEK,
                            revenue_timeline.MONTH))
    for index, (point, bar) in enumerate(zip(points, bars)):
        y_fraction = float(point.revenue / ceiling) if ceiling > 0 else 0.0
        x_fraction = _chart_x_fraction(point.key, granularity, period, index, count)
        bar["x"] = _CHART_PAD_X + x_fraction * (_CHART_VIEW_W - 2 * _CHART_PAD_X)
        bar["x_pct"] = bar["x"] / _CHART_VIEW_W * 100
        bar["y"] = _CHART_PLOT_H - round(y_fraction * _CHART_PLOT_H)
    # Nhãn dưới TỪNG điểm chỉ còn dùng khi trục X KHÔNG có lưới cố định
    # (Quý/Năm, không container) — Ngày/Tuần/Tháng đọc nhãn từ `x_ticks`
    # thay vào, tách khỏi việc điểm đó có dữ liệu hay không (`§1`). Mốc ĐẦU
    # và mốc CUỐI của chuỗi thưa vẫn luôn hiện, để biết biểu đồ bắt đầu và
    # kết thúc ở đâu.
    stride = max(1, math.ceil(count / _CHART_MAX_X_LABELS)) if bars else 1
    for index, bar in enumerate(bars):
        bar["show_label"] = (
            not fixed_x_axis
            and ((index % stride == 0) or index == count - 1))
    return {
        "svg_width": _CHART_VIEW_W,
        "svg_height": _CHART_PLOT_H,
        "y_axis": _chart_y_axis(ceiling),
        "x_ticks": _chart_x_ticks(granularity, period) if fixed_x_axis else [],
        "fixed_x_axis": fixed_x_axis,
        "polyline": " ".join(f"{bar['x']},{bar['y']}" for bar in bars),
        "single_point": len(bars) == 1,
        "granularity": granularity,
        "options": [
            {"key": key, "label": label, "on": key == granularity}
            for key, label in revenue_timeline.GRANULARITIES
        ],
        "bars": bars,
        "empty": not bars,
        "empty_note": CHART_EMPTY_NOTE,
        "note": revenue_timeline.CHART_NOTE,
        # `F-E` — phạm vi thời gian của biểu đồ, nói cạnh chính biểu đồ.
        "scope_note": _chart_scope_note(granularity, window_label),
        "windowed": bool(window_label),
        "total": format_number(revenue_timeline.totals_of(points)),
        "total_kvnd": _thousand_vnd(revenue_timeline.totals_of(points)),
        "has_partial": any(bar["partial"] for bar in bars),
        "partial_note": CHART_PARTIAL_NOTE,
        # Nói ra chỗ biểu đồ KHÔNG biết, thay vì để một khoảng trống im lặng
        # trông như "tháng đó không bán được gì" (`§CHART-10`).
        "no_daily_legacy_note": (
            revenue_timeline.NO_DAILY_LEGACY_NOTE
            if day_level and has_legacy_months
            and not any(bar["legacy"] or bar["mixed"] for bar in bars)
            else None),
        "undated": undated,
        "undated_note": CHART_UNDATED_NOTE,
    }


def _chart_bar_title(point) -> str:
    """Câu giải thích của MỘT cột — nơi duy nhất origin được nói thành lời.

    Owner cấm một bộ chọn nguồn và cấm nhãn "Số cũ"/"Số mới" trên biểu đồ:
    người đọc đang hỏi một câu về thời gian kinh doanh. Nhưng `DEC-166 E` bắt
    LUÔN phân biệt được hai origin. Cách thoả cả hai là ở đây — trong lời giải
    thích của đúng cái cột đó, bằng ngôn ngữ THỜI GIAN ("bản ghi lịch sử"),
    không bằng tên hệ thống, và không phải một cái nút bấm được.
    """
    parts = [f"{point.label}: {format_number(point.revenue)} đồng"]
    if point.is_legacy:
        parts.append(revenue_timeline.LEGACY_POINT_NOTE)
    if point.is_mixed:
        # Cùng chỗ, cùng giọng: một câu trong lời giải thích của ĐÚNG cột đó.
        # Không một điều khiển nào được thêm cho nó (`§11` — không bộ chọn
        # nguồn, không chuỗi thứ hai, không nhãn Số cũ/Số mới).
        parts.append(revenue_timeline.MIXED_POINT_NOTE)
    if point.partial:
        parts.append(
            f"Dựng từ {point.covered_months}/{point.span_months} tháng có "
            "bằng chứng.")
    return " ".join(parts)


__all__ = [
    "ALL_DATA_LABEL", "CHART_EMPTY_NOTE", "CHART_PARTIAL_NOTE",
    "COUNT_CHART_EMPTY_NOTE", "COUNT_CHART_UNIT", "paired_count_chart",
    "paired_revenue_chart",
    "CHART_UNDATED_NOTE", "revenue_chart", "CONVERTED_SALES_NOTE", "DERIVED_COLUMNS_NOTE",
    "KEEP_EMPLOYEE_LABEL",
    "DETAIL_COLUMNS", "EMPLOYEE_COLUMNS", "GIA_DUNG_COLUMNS", "INCOMPLETE_NOTE",
    "DISCOUNT_PROVENANCE", "DISCOUNT_PROVENANCE_LABEL", "DISCOUNT_ROW_LABEL",
    "DISCOUNT_ROW_NOTE",
    "MISSING_PRICE_COLUMNS", "MOM_ALL_DATA", "MOM_LEGACY_PREVIOUS_NOTE",
    "MOM_NO_PREVIOUS",
    "TARGET_COLUMNS", "TARGET_COMPANY_DEFERRED_NOTE", "TARGET_FORMULA_NOTE",
    "TARGET_LEGACY_READ_ONLY_NOTE", "TARGET_NO_PERIOD_NOTE", "TARGET_NOTE",
    "TARGET_REASON_LABELS", "TARGET_UNIT_NOTE", "TARGET_UNSET_LABEL",
    "TARGET_ZERO_VS_BLANK_NOTE",
    "MOM_PREVIOUS_ZERO", "NET_SALES_NOTE", "NOT_SEEN_WARNING", "OFFICIAL_NOTE",
    "ORDER_COLUMN_NOTE",
    "ORIGIN_BADGE", "PROVENANCE_LABELS", "QUALIFYING_QUANTITY_LABEL",
    "QUALIFYING_QUANTITY_NOTE", "STATE_LABELS", "UNKNOWN_EMPLOYEE",
    "UNRESOLVED_EMPLOYEE_NOTE",
    "assignable_employee_options", "close_summary", "coverage_cell",
    "detail_rows",
    "KPI_PROFIT_NOTE", "pending_items", "reporting_rows", "sheet_display_order",
    "employee_detail", "employee_options", "employee_rows", "gated_cell",
    "gia_dung_rows", "missing_price_rows", "month_over_month",
    "not_seen_warning", "percent",
    "money_kvnd", "money_text", "share_cell",
    "period_label", "period_options", "period_value", "summary",
    "employee_target_block", "target_cell", "target_rows", "vs_target_cell",
]
