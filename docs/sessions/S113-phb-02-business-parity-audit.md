# S113 — PHB-02 Business Parity Contract (Audit)

Mode: READ-ONLY BUSINESS AUDIT.
Docs-only · 0 dòng production code · không migration · không đổi
Render/PostgreSQL/R2/Cloudflare · không mở PHB-03 · không implement PHB-04
(Legacy) hay PHB-05 (Target) · không mở lại PHB-01.

Câu hỏi vertical: *thông tin nghiệp vụ và quy trình nào trong báo cáo tay của
Owner bắt buộc Reports phải bảo toàn hoặc thay thế, để web thay được quy trình
báo cáo thủ công?*

Sản phẩm chính: `docs/tasks/PHB-02-business-parity-contract.md` — hợp đồng
ĐỀ XUẤT, `AWAITING_OWNER`.

## 1. Target Gate

```text
EXPECTED_HEAD  = eaa3fdeb4ffdfd2d5772314ac24cf8a1273cc67e
OBSERVED_HEAD  = eaa3fdeb4ffdfd2d5772314ac24cf8a1273cc67e   → KHỚP
DEFAULT_BRANCH = claude/extract-upload-repo-gq2ws4 (origin HEAD branch)
SESSION_BRANCH = claude/business-parity-contract-me80ij (0 ahead / 0 behind
                 default khi mở phiên — SessionStart hook xác nhận)
WORKTREE       = sạch
PHB-01         = DONE     (khối canonical S112)
PHB-02         = CURRENT  (NEXT_VERTICAL_ACTION của cùng khối)
TARGET_GATE    = PASS
```

Sức khoẻ HEAD (E1, thực thi trong phiên; môi trường cài bằng
`pip install -e ".[dev,web]"`):

```text
python -m pytest tests/ -q                        → 2032 passed, 11 skipped in 89.95s
python -m pytest tests/test_golden_baseline.py -q → 58 passed, 2 skipped
validate_structure            → PASS (21 required path)
validate_project_state        → PASS
validate_evidence             → PASS (155 REQUIRED PASS)
validate_task_completion      → PASS (13 DONE task)
validate_reference_integrity  → FAIL với ĐÚNG 3 reference REM-T06 đã biết
                                (trước VÀ sau khi thêm tài liệu — baseline không đổi)
```

## 2. Định vị báo cáo tay

```text
MANUAL_REPORT           = data/samples/Bao_cao_Kinh_doanh_2026.xlsx
                          59 sheet = 56 sheet nhân viên-tháng (01.2026–08.2026)
                          + Summary 2025 + Summary 2026 + DataChart 2026
MANUAL_REPORT_AVAILABLE = NO   (file .xlsx không có trong session — PII, .gitignore, DEC-108)
MANUAL_REPORT_STRUCTURE_AVAILABLE = YES
                          docs/analysis/_evidence/evidence.json (trích xuất máy,
                          tái tạo được bằng tools/analysis/extract_evidence.py)
                          + docs/analysis/01..07,10 (Owner đã duyệt, GATE-00/DEC-122)
```

Ba loại artifact được phân biệt tường minh và **không** bị thay thế cho nhau:
RAW ACCOUNTING INPUT (`So_chi_tiet_ban_hang.xlsx`) · OWNER MANUAL REPORT
(`Bao_cao_Kinh_doanh_2026.xlsx`) · LEGACY_REFERENCE (`Summary 2025` và các báo
cáo tay trước kỳ hiện hành).

Không có cấu trúc sheet nào bị suy đoán. Chỗ nào trích xuất không trả lời được
thì được đánh dấu `AMBIGUOUS`, không điền bằng phỏng đoán.

## 3. Bằng chứng quyết định — đối chiếu ba nguồn trên cùng kỳ

BC = báo cáo tay (`evidence.json → report.sheet_totals`) ·
THÔ = sổ ERP (`evidence.json → raw_by_month_employee`) ·
REPORTS = pipeline tại HEAD (`tests/fixtures/golden/expected/`).

```text
01.2026 Tín Phát   đơn:   BC 254        THÔ 254        REPORTS 254            KHỚP
                   SP:    BC 387,63     THÔ 407        REPORTS 407
                   bán:   BC 3.544.010k THÔ 3.564.610k REPORTS 3.564.610.000  = THÔ
                   LN:    BC 238.115k   THÔ 240.033k   REPORTS KHÔNG TÍNH ĐƯỢC

06.2026 Tín Phát   đơn:   BC 146        THÔ 146        REPORTS 146            KHỚP
                   SP:    BC 178,80     THÔ 210        REPORTS 210
                   bán:   BC 1.799.920k THÔ 1.925.272k REPORTS 1.924.872.000 (net)
                   LN:    BC 119.236k   THÔ 95.957k    REPORTS KHÔNG TÍNH ĐƯỢC
```

Ba điều rút ra, mỗi điều có bằng chứng riêng:

1. **Reports tái tạo sổ ERP đến từng đồng.** `sales_raw_gross =
   3.564.610.000` ≡ `raw…sales_thousands = 3.564.610`.
2. **Báo cáo tay thì không, và lệch hai chiều ngược nhau.** `01.2026` BC thấp
   hơn ERP 0,58 % ở doanh số; `06.2026` BC thấp hơn 6,5 % ở doanh số nhưng
   **cao hơn 24,3 %** ở lợi nhuận. Cộng với `manual_price_overrides =
   635/18.148` ô giá gõ tay không dấu vết, và `06.2026 Ly` có 98 đơn trên báo
   cáo nhưng chỉ 89 đơn trong sổ nguồn.
3. **Lợi nhuận KPI hiện không tính được.** `price_source_distribution =
   {"Pending": 351}` và `{"Pending": 180}` trên hai kỳ golden — 100 % dòng.
   Production kỳ 09/2026 đạt 34/142 dòng.

Điểm khớp ngữ nghĩa đã chứng minh: `scheme_distribution =
{"ADS_7_5@0.075": 351}` với provenance `Auto:LeadSource`, đúng `=G6/7.5%` mà
báo cáo tay dùng cho Tín Phát ở mọi kỳ. Nhưng `product_group_provenance =
{"DEFAULT": 351}` — 100 % dòng rơi về `DIEN_MAY` theo fallback, nên hai dòng
scheme `NOI_THANH_2` (2 %) và `GIA_DUNG_8` (8 %) hiện không bao giờ kích hoạt
đúng.

## 4. Kết luận parity

Vì báo cáo tay chứa các quyết định của con người (loại trừ đơn, điều chỉnh giá
nhập KPI) chồng lên số ERP mà **không được ghi lại ở đâu**, `MUST_MATCH` không
thể có nghĩa "khớp con số của báo cáo tay". Chỉ hai neo parity được **chứng
minh** hôm nay:

```text
M1  Số đơn theo (nhân viên, tháng)          — 254=254=254 · 146=146=146
M2  Tổng bán gộp so với sổ ERP              — khớp đến từng đồng
```

Toàn bộ phân loại `MUST_MATCH` / `MUST_PRESERVE_SEMANTICS` (S1–S12) /
`MAY_IMPROVE_PRESENTATION` (P1–P5) / `DEFER` (D1–D9) / `DROP_INTENTIONALLY`
(X1–X8) / `LEGACY_DEPENDENT` (L1–L6) / `TARGET_DEPENDENT`, cùng Summary Parity
Matrix và Metric Semantic Audit, nằm ở
`docs/tasks/PHB-02-business-parity-contract.md`.

Một kết luận được bác bỏ dứt khoát: **56 sheet nhân viên-tháng KHÔNG đòi 56
tab web.** 56 sheet chỉ có 6 biến thể layout, 4 trong 6 khác nhau đúng một ký
tự rác ở ô `R1`. Yêu cầu nghiệp vụ đúng là "Owner chọn nhân viên + kỳ và nhận
đủ chuỗi đánh giá".

## 5. Owner Questions

```text
OWNER_DECISIONS_REQUIRED = 7

Q1  Báo cáo tay là oracle SỐ HỌC hay oracle NGHIỆP VỤ?        [chặn PHB-03]
Q2  Ngưỡng coverage Lợi nhuận KPI nào = "parity đã giao"?     [chặn PHB-03]
Q3  "Tổng số SP" nghĩa là gì? (N.7)
Q4  Tổng công ty theo tháng gồm những ai? (lỗi A2)            [chặn PHB-03]
Q5  "Gia dụng" có phải dòng báo cáo hạng nhất trong V1?
Q6  Target: tái dùng số lịch sử hay Owner cấp bảng mới? (PHB-05)
Q7  Mẫu số của tỉ suất và của "So tháng trước"                [chặn PHB-03]
```

Đầy đủ `WHY_REQUIRED` / `WHAT_DECISION_IT_UNLOCKS` / `OPTIONS` tại mục 9 của
hợp đồng. Không câu nào trả lời được từ file hoặc mã nguồn; không câu nào có
tính thẩm mỹ.

## 6. Findings

Finding **không** tự sinh task.

```text
BLOCKING (2)
  FIND-PHB02-B01  Parity oracle không xác định (Q1)
  FIND-PHB02-B02  DS quy đổi sẽ được implement với ngữ nghĩa đoán (Q2/Q4/Q5)

NON-BLOCKING (5)
  FIND-PHB02-N01  635/18.148 ô giá gõ tay trong báo cáo tay, không dấu vết
  FIND-PHB02-N02  Target công ty ≠ tổng target nhân viên (chênh 8.890.000)
  FIND-PHB02-N03  Xung đột đơn vị 1.000 lần trong cùng sheet DataChart
  FIND-PHB02-N04  Repo chưa có vị trí backlog UX canonical (UX-PI-01 ghi trong hợp đồng)
  FIND-PHB02-N05  app/modules/conversion/ chưa có consumer tổng hợp converted_revenue
                  — ĐÚNG theo §L "LATER", ghi lại để phiên sau không nhầm là bug
```

## 7. Biên phạm vi đã tuân thủ

```text
PHB-01           = KHÔNG mở lại. UX-PI-01 chỉ được ghi làm backlog hoãn
                   (mục 5.4 D9 của hợp đồng); NB-6 có thể hấp thụ vào đó.
                   KHÔNG thiết kế API, KHÔNG implement.
PHB-03           = KHÔNG bắt đầu.
PHB-04 (Legacy)  = KHÔNG implement. Yêu cầu bảo toàn L1–L6.
                   Luật đã freeze giữ nguyên: 2025 và các báo cáo tay trước kỳ
                   hiện hành = LEGACY_REFERENCE, KHÔNG chạy lại qua pipeline
                   production như raw accounting input.
PHB-05 (Target)  = KHÔNG implement. Chỉ trích xuất: chỉ tiêu được áp (DS quy
                   đổi), kỳ (tháng + năm), phạm vi (NV/kênh + công ty), target
                   KHÔNG đổi trong 2026, và ba điểm mơ hồ về công thức/đơn vị.
PRODUCTION CODE  = 0 dòng thay đổi
```

## 8. Kết luận

```text
PHB_02               = AWAITING_OWNER
PHB_03_READY         = NO  (chặn bởi Q1, Q2, Q4, Q7)
SCOPE_DRIFT          = NO
BLOCKING_FINDINGS    = 2 (đều là quyết định Owner, không phải defect code)
NEXT_VERTICAL_ACTION = Owner giải quyết 7 quyết định Business Parity còn lại,
                       sau đó freeze PHB-02
```

`PHB-02` **KHÔNG** được đánh dấu `DONE` — theo đúng luật, một task còn quyết
định Owner chưa giải quyết thì chưa `DONE`.
