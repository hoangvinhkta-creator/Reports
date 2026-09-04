# S114 — PHB-02 Owner Decisions + Business Parity Contract Freeze

Mode: BUSINESS CONTRACT FREEZE.
Docs-only · 0 dòng production code · không migration · không đổi
Render/PostgreSQL/R2/Cloudflare · không bắt đầu PHB-03 · không implement
PHB-04 (Legacy) hay PHB-05 (Target) · không mở lại PHB-01 · không redesign
ProductGroup · không code cleanup.

Tiếp nối `S113` (audit). Phiên này áp bảy quyết định Owner
`DEC-PHB02-01…07` lên hợp đồng canonical và freeze nó.

## 1. Target Gate

```text
EXPECTED_HEAD  = a47c164
OBSERVED_HEAD  = a47c164bc018bfc5fdc97af08dacea406812a17c   → KHỚP
BRANCH         = claude/business-parity-contract-me80ij     → KHỚP
WORKTREE       = sạch
TARGET_GATE    = PASS
```

## 2. Bảy quyết định Owner đã áp

```text
DEC-PHB02-01  Mục đích Reports / Parity Oracle
              Reports được xây để THAY THẾ báo cáo thủ công. Báo cáo tay =
              BUSINESS REQUIREMENT / SEMANTIC REFERENCE, KHÔNG phải FINAL
              NUMERIC AUTHORITY. Cấm sửa Reports chỉ để đuổi theo số tay
              không tái tạo được từ nguồn đã chấp nhận + rule đã duyệt.

DEC-PHB02-02  Giá nhập / coverage lợi nhuận
              AUTO-fill bằng thuật toán khớp giá đã chấp nhận · thiếu dữ liệu
              ⟹ cảnh báo tường minh + nhập tay · ô AUTO vẫn SỬA ĐƯỢC ·
              provenance tối thiểu AUTO vs MANUAL/MANUAL_OVERRIDE, cấm âm
              thầm coi override là AUTO · LN KPI CHÍNH THỨC chỉ khi
              PROFIT_COVERAGE = 100 %, KHÔNG có ngưỡng 90/95 %.

DEC-PHB02-03  Tổng số SP = SUM(quantity) khi giá bán > 1.000.000 VND.
              Ngưỡng giá, KHÔNG phải taxonomy, KHÔNG phải đếm SKU/dòng.

DEC-PHB02-04  DS quy đổi = CHỈ TIÊU CỐT LÕI.
              CONVERTED_SALES = PROFIT / CONVERSION_RATE  (PHÉP CHIA).
              profit * rate bị cấm tuyệt đối.
              Phạm vi = TẤT CẢ đơn đủ điều kiện trong tháng, không phải một
              tập con chọn tay. Không bịa từ giá nhập chưa phân giải.

DEC-PHB02-05  Định tuyến tỉ lệ:
                Tín Phát                        7,5 %
                Vinh/Quý/Hiệp (wholesale/NT)    2 %, hoặc 8 % nếu sản phẩm
                                                được TICK GIA_DUNG
                Bán lẻ khác                     5,5 %
              GIA_DUNG là PRODUCT-LEVEL OVERRIDE trong đúng luồng
              wholesale/nội-thành, KHÔNG phải một loại nhân viên. Cấm suy ra
              tự động từ tên hàng. Bán lẻ thường KHÔNG cần luồng này.

DEC-PHB02-06  Target cấu hình được theo từng nhân viên, có chỗ NHẬP/SỬA.
              Cấm hard-code giá trị target vào logic tính. Chi tiết → PHB-05.

DEC-PHB02-07  So tháng trước = % thay đổi DOANH THU BÁN HÀNG so tháng liền
              trước. KHÔNG phải DS quy đổi / lợi nhuận / số lượng / mức đạt
              target. Mẫu số 0 xử lý tường minh.
```

## 3. Bảy câu hỏi S113 — tất cả ĐÓNG

```text
Q1 oracle parity          → CLOSED  DEC-PHB02-01 (đúng phương án A của audit)
Q2 ngưỡng coverage LN KPI → CLOSED  DEC-PHB02-02 — KHÔNG ngưỡng, GATE 100 %
Q3 "Tổng số SP" (N.7)     → CLOSED  DEC-PHB02-03 — đơn giá > 1.000.000
Q4 phạm vi tổng công ty   → CLOSED  dẫn xuất từ DEC-PHB02-01 + 04 + 05
Q5 "Gia dụng"/ProductGroup→ CLOSED  DEC-PHB02-05 — tick cấp sản phẩm, 1 luồng
Q6 nguồn target           → CLOSED  DEC-PHB02-06 (ý định); chi tiết → PHB-05
Q7 mẫu số so sánh         → CLOSED  DEC-PHB02-07 cho "So tháng trước";
                                    phần margin vẫn DEFER D1, không phải
                                    quyết định Owner còn treo

OWNER_DECISIONS_REMAINING = 0
```

`Q4` đóng bằng **dẫn xuất**, được trình bày đầy đủ ở mục 9.1 của hợp đồng
(vùng `SUM` cắt cụt là artifact bị bỏ · DS quy đổi gồm TẤT CẢ đơn · mọi nhóm
đều có tỉ lệ nên mọi nhân viên đều vào tổng · "Gia dụng" không còn là thực
thể). Kết luận: tổng công ty cộng đủ mọi nhân viên `include_in_kpi = true`;
**không** cần cờ `include_in_company_total` — ý tưởng đó bị bác bỏ khỏi mục
10.11.

## 4. Bằng chứng mới đo trong phiên này (E1)

`DEC-PHB02-03` được đo trực tiếp trên hai fixture golden
(`tests/fixtures/golden/period_2026_*.xlsx`), đọc `qty` (cột 8), `unit_price`
(cột 9), `sales` (cột 10):

```text
                        SUM(qty) mọi dòng   DEC-PHB02-03   dòng bị loại   BC tay
01.2026 Tín Phát              407               358             45        387,6271681
06.2026 Tín Phát              210               178             27        178,8029801
```

Hai kết quả làm quy tắc này an toàn để implement:

1. **Đơn giá hay tổng dòng đều cho CÙNG một con số** trên cả hai kỳ (`358` và
   `178`, chênh lệch **bằng 0**). Cách đọc canonical là **đơn giá** (khớp cột
   `Giá bán` của sheet tay và cụm "product sale price"), và sự mơ hồ này vô
   hại trên thực tế.
2. **Quy tắc loại đúng thứ Owner muốn loại.** Mô tả bị loại nhiều nhất:
   `Chi phí vận chuyển` (19/10) · `Giá treo Tivi` (12/9) · `Chân máy giặt Đa
   Năng` (8) · `Chi phí lắp đặt` (2/1) · `Phụ Phí` (1/2) · `Giá treo xoay NB
   P6`.

Hệ quả đã chấp nhận: vì là **ngưỡng giá** chứ không phải taxonomy, vài sản
phẩm thật giá thấp cũng bị loại (2 dòng ở 01.2026 — `Đèn sưởi nhà tắm
Kangaroo KGWH03T`; 1 dòng ở 06.2026 — `Bình nước nóng Ariston Slim 3 20 RS
VN`). Owner chỉ thị rõ không mở rộng thành taxonomy ⟹ đánh đổi có chủ đích,
không phải defect (`FIND-PHB02-N08`).

## 5. Findings sau freeze

```text
BLOCKING = 0
  FIND-PHB02-B01  → CLOSED bởi DEC-PHB02-01
  FIND-PHB02-B02  → CLOSED bởi DEC-PHB02-04 + 05 + 02

NON-BLOCKING
  FIND-PHB02-N01  GIỮ — dữ kiện lịch sử (635/18.148 ô giá gõ tay)
  FIND-PHB02-N02  HẠ CẤP → cảnh báo đơn vị cho PHB-05
  FIND-PHB02-N03  HẠ CẤP → cảnh báo đơn vị cho PHB-05
  FIND-PHB02-N04  GIỮ — repo chưa có backlog UX canonical (UX-PI-01 ở 5.4 D9)
  FIND-PHB02-N05  ĐỔI TRẠNG THÁI → từ "đúng theo §L LATER" thành KHOẢNG TRỐNG
                  ĐÃ BIẾT của PHB-03, vì DEC-PHB02-04 nâng DS quy đổi thành
                  chỉ tiêu cốt lõi bắt buộc
  FIND-PHB02-N06  MỚI — PROFIT trong DEC-PHB02-04 là minh hoạ theo đơn vị sản
                  phẩm; công thức thi hành vẫn là EligibleKpiProfit của
                  DEC-143. Điểm xác nhận một dòng cho PHB-03.
  FIND-PHB02-N07  MỚI — DEC-PHB02-05 định tuyến theo NHÓM và không nhắc
                  lead_source; engine định tuyến qua lead_source. Trên MỌI dữ
                  liệu đã quan sát hai mô hình cho KẾT QUẢ GIỐNG HỆT và chuỗi
                  "ADS" xuất hiện 0 lần trong cả hai workbook. Cách đọc nhất
                  quán: DEC-PHB02-05 đặt MẶC ĐỊNH, cơ chế lead_source đã
                  freeze (DEC-109/DEC-119) giữ nguyên. Tác động thực tế 0 dòng.
  FIND-PHB02-N08  MỚI — DEC-PHB02-03 là ngưỡng giá nên loại cả vài sản phẩm
                  thật giá thấp; đánh đổi có chủ đích.
```

Finding **không** tự sinh task.

## 6. Ghi chú sequencing cho PHB-03 — ghi lại, KHÔNG giải ở đây

```text
DS quy đổi (R-E6) và LN KPI CHÍNH THỨC (R-S7) đều phụ thuộc coverage giá
nhập = 100 %. Coverage đo được hôm nay: 0–2/351 (golden) · 34/142
(production 09/2026). Đường ghi để đạt 100 % (R-P1…R-P4) CHƯA TỒN TẠI —
tầng analytics là CHỈ-ĐỌC theo thiết kế, và PRICE_SOURCE_MANUAL
(app/modules/domain/models.py:43) mới chỉ là một slot từ vựng đã dành sẵn
cho "when override/audit trail exists".

⟹ Khi mở PHB-03: PHB-03 có bao gồm đường nhập/override giá nhập không, hay
   đường đó là một vertical riêng đứng TRƯỚC phần DS quy đổi của PHB-03?
   Đây là quyết định ROADMAP, KHÔNG phải khoảng trống ngữ nghĩa — nên nó
   KHÔNG làm PHB_03_READY = NO.
```

## 7. Governance

```text
validate_structure            → PASS (21 required path)
validate_project_state        → PASS
validate_evidence             → PASS (155 REQUIRED PASS)
validate_task_completion      → PASS (13 DONE task)
validate_reference_integrity  → FAIL với ĐÚNG 3 reference REM-T06 đã biết
                                (baseline không đổi, không phát sinh mới)
git diff --check              → sạch
PRODUCTION_CODE_CHANGED       → NO (chỉ 3 file tài liệu)
```

Bản ghi lịch sử `S113` được **giữ nguyên, không viết lại**.

## 8. Kết luận

```text
OWNER_DECISIONS_APPLIED    = 7 / 7
OWNER_DECISIONS_REMAINING  = 0
BUSINESS_PARITY_CONTRACT   = FROZEN
PHB_03_READY               = YES
BLOCKING_FINDINGS          = 0
SCOPE_DRIFT                = NO
PHB_02                     = DONE
NEXT_VERTICAL_ACTION       = PHB-03 Summary + Employee Business Parity V1
```
