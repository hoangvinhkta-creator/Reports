# S115 — PHB-03 Summary + Employee Business Parity V1 (IMPLEMENTATION)

Mode: MAJOR IMPLEMENTATION.
Không deploy production · không merge vào nhánh production · không implement
PHB-04 (Legacy) hay PHB-05 (Target) · không mở lại PHB-01 · không redesign
Product Master / ProductGroup · không refactor rộng.

Tiếp nối `S114` (freeze hợp đồng). Phiên này implement vertical đầu tiên
đứng trên hợp đồng đó.

Task canonical: `docs/tasks/PHB-03-summary-employee-business-parity.md`.

## 1. Target Gate

```text
SOURCE_BRANCH   = claude/business-parity-contract-me80ij
EXPECTED_HEAD   = c996ca8
OBSERVED_HEAD   = c996ca8f92a5abd7d004ffb85a802992dd3c367f   → KHỚP
WORKING_BRANCH  = claude/phb-03-summary-employee-parity-7x3uid
DEFAULT_BRANCH  = claude/extract-upload-repo-gq2ws4 (origin HEAD branch)
BEHIND_DEFAULT  = 0 commit
CONTRACT        = FROZEN · PHB_03_READY = YES
TARGET_GATE     = PASS
```

## 2. Quyết định phạm vi đã đóng trong phiên

Mục 11.1 hợp đồng để mở đúng một câu hỏi ROADMAP. Chỉ thị phiên đóng nó:

```text
PHB-03 BAO GỒM đường ghi giá nhập, ở dạng BOUNDED (hai bảng, ghi đè tại chỗ).
Lý do: giá nhập → EligibleKpiProfit → LN KPI chính thức → DS quy đổi.
Tách ra sẽ giao một PHB-03 mà chỉ tiêu quyết định (DS quy đổi) không chạy được.
```

## 3. Điểm cần Independent Review đọc kỹ nhất

`DEC-PHB02-02` chốt **gate 100 %** nhưng không nói *100 % của cái gì*. Phiên
này trả lời:

```text
PROFIT_COVERAGE = (dòng THỰC SỰ góp giá trị lợi nhuận KPI) / (mọi dòng của kỳ)
```

Tử số **đúng bằng** tập được cộng, nên `100 %` tương đương "mọi dòng đã có mặt
trong con số này" và nhãn CHÍNH THỨC không thể nói dối. Hệ quả đã lường trước
và nói thẳng: vì `D1/P1` (`TASK-PRA-003`) giữ nguyên, một kỳ còn dòng
`PENDING` sẽ **không** đạt 100 % dù Owner nhập đủ giá nhập. Hai lý do "chưa
đủ" vì vậy được đếm và hiển thị RIÊNG (`FIND-PHB03-N01`).

Người review nên chất vấn đúng chỗ này trước tiên — nó là suy luận DUY NHẤT
mà phiên này thêm vào phần hợp đồng chưa nói hết.

## 4. Ranh giới thẩm quyền

```text
PURCHASE_PRICE_AUTHORITY_CONFLICT = KHÔNG PHÁT SINH

KHÔNG chạm:  accounting_purchase_price / price_source (PriceProvider)
             HistoricalConfirmedRegistry (E-J, pre-cutover, INV-47/51/54)
             order_line_result_version (append-only)

Giá do Owner nhập → bảng riêng kpi_purchase_price_override, hợp nhất LÚC ĐỌC.
Đúng slot PRICE_SOURCE_MANUAL đã chừa từ TASK-105.
```

Gia dụng: bảng `product_group_classification`, khoá theo `product_key`, quyết
định tường minh của người. Ranh giới 8 % chỉ cho `NOI_THANH` là **cấu trúc của
`config/conversion_rates.yaml`**, không phải một câu `if` trong mã.

## 5. Bề mặt đã giao

```text
/kinh-doanh                 Summary V1        R-S1…R-S8
/kinh-doanh/nhan-vien       Employee V1       R-E1…R-E8
/kinh-doanh/gia-nhap        Hoàn thiện giá nhập  R-P1…R-P4
/kinh-doanh/gia-dung        Tick Gia dụng     DEC-PHB02-05 (chỉ Nội thành)
```

`/tong-quan`, `/nhan-vien?nguon=moi`, `/ban-hang`, `/san-pham`,
`/doanh-so-ngay` **không đổi một dòng** — chúng là bề mặt đã nghiệm thu.

## 6. Bằng chứng (E1, thực thi trong phiên)

```text
python -m pytest tests/ -q                        → 2106 passed, 11 skipped
python -m pytest tests/test_golden_baseline.py -q → 58 passed, 2 skipped
74 test mới (business_metrics 33 · business_vertical 35 · boundaries 6)
13/13 vector nghiệm thu A–M PASS

validate_structure           → PASS (21 required path)
validate_project_state       → PASS
validate_evidence            → PASS (155 REQUIRED PASS)
validate_task_completion     → PASS (13 DONE task)
validate_reference_integrity → FAIL với ĐÚNG 3 reference REM-T06 đã biết
                               (baseline không đổi)
```

## 7. Việc kế tiếp

```text
NEXT_VERTICAL_ACTION = Independent Review của PHB-03 implementation.
```

`PHB-03 = IMPLEMENTED_AWAITING_REVIEW`, **chưa** `DONE`.

Lưu ý triển khai (không phải task): `ALEMBIC_HEAD` chuyển
`0002_snapshots` → `0003_business`. Quy trình `alembic upgrade head` trước khi
mở cổng đã có ở `docs/deployment/S071_DEPLOYMENT.md`; migration là ADDITIVE
thuần và có test round-trip. Phiên này KHÔNG deploy.
