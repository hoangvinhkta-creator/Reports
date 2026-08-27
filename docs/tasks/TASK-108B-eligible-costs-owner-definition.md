# TASK-108B — ELIGIBLECOSTS OWNER DEFINITION REPORT

Loại artifact: **OWNER DEFINITION + IMPLEMENTATION READINESS** (artifact **#1**
của root task lineage `TASK-108B` — trước phiên này lineage chưa có artifact
nào; Artifact Budget V4.1 §10 chưa chạm ngưỡng 5).

Phiên: Owner Definition, **KHÔNG implementation**.
Ngày: 2026-08-27.
Governance: V4.1 `FULLY_ENFORCED`.

---

## 1. Repository checkpoint

```
remote            : https://github.com/hoangvinhkta-creator/Reports
default branch    : claude/extract-upload-repo-gq2ws4   (resolve bằng Git, không hardcode)
default tip       : 7e609780c77dd943173db77341bc315589a3a8a7
Owner Golden SHA  : 7e609780c77dd943173db77341bc315589a3a8a7  → ancestor-or-equal: XÁC NHẬN
session branch    : claude/eligible-costs-owner-def-g88bal
HEAD              : 7e609780c77dd943173db77341bc315589a3a8a7
ahead/behind      : 0 / 0
worktree          : CLEAN
```

`scripts/branch_authority_check.sh` → `AUTHORITY: BRANCH_WITH_UPSTREAM`,
`RESULT: AUTHORITY_OK`, `DIVERGENCE: WITHIN_LIMITS`.

Ghi chú quy trình: lần chạy đầu trả `STOP — BRANCH AUTHORITY UNRESOLVED`,
**không phải** `AUTHORITY_MISMATCH`. Lý do duy nhất: nhánh session mới tạo
chưa có upstream. Nội dung authority đã đúng ngay từ đầu (`HEAD` = `DEFAULT_TIP`
= Golden SHA Owner cung cấp). Khắc phục đúng theo hướng dẫn của chính script
(`git push -u origin <branch>`), không đổi nhánh, không chọn nhánh gần giống.

### Xác minh trạng thái Owner cung cấp (không tin prompt, đọc repo)

| Owner nói | Repo nói | Nguồn | Khớp |
|---|---|---|---|
| `TASK-GOLDEN-BASELINE-001 = DONE` | DONE, FROZEN (DEC-142), MERGED `f332a4c` | `PROJECT/REVIEW_BUDGET_LEDGER.md`, `PROJECT_PROGRESS.md:149` | ✅ |
| Golden Baseline = ACTIVE | `tests/test_golden_baseline.py` tồn tại, fixture + expected commit | `tests/fixtures/golden/` | ✅ |
| `V4.1 = FULLY_ENFORCED` | `FULLY_ENFORCED` (2026-08-27) | `PROJECT_PROGRESS.md:20` | ✅ |
| `TASK-110 = NOT DONE` | NOT DONE | `PROJECT_PROGRESS.md:129, 692` | ✅ |
| `CHECK-110-16 = REQUIRED · BLOCKED · POST_MERGE_PRODUCTION_ACCEPTANCE` | đúng nguyên văn (DEC-141) | `PROJECT_PROGRESS.md:131`, ledger | ✅ |
| `R1-A1 = FROZEN` | FROZEN (DEC-139) tại `a853971` | `PROJECT_PROGRESS.md:124` | ✅ |
| `TASK-108B` chặn bởi ambiguity `EligibleCosts` | chặn bởi **C15 + 3 dependency khác** | mục 5 dưới đây | ⚠️ **một phần** |
| `TASK-109` phụ thuộc `TASK-108B` | đúng | `PROJECT_PROGRESS.md:225` | ✅ |

Phiên này **không đổi** bất kỳ trạng thái nào ở trên.

---

## 2. TASK-108B — mục đích khôi phục từ repo

**Business purpose.** Thay thế thao tác gõ tay số `X` mỗi tháng trong workbook
bằng một phép tổng truy vết được. Bằng chứng nguyên bản
(`docs/analysis/02_FORMULA_MAPPING.md` §4): công thức Summary của Hoàng và Kiên
là `= (LợiNhuận − X) / 5,5% + X / 7,5%`, trong đó `X` là phần lợi nhuận đến từ
đơn ADS **của chính họ**, hiện được **gõ tay**. Trong `05.2026 Hoàng` nó là
tổng hai số rời (`3770+16190`) — dấu vết cộng tay từng đơn. Kiên giữ nguyên
`7565` suốt 06, 07, 08.2026 — nhiều khả năng copy công thức, không kiểm chứng
được. Tài liệu ghi rõ: *"Đây chính là chức năng chính của công cụ."*

**Inputs.**

| Input | Trạng thái hiện tại | Nguồn |
|---|---|---|
| `EligibleKpiProfit` cấp line | **CHƯA TỒN TẠI** — không có field, không có module | `app/modules/domain/models.py`, `app/modules/profit/` |
| `LeadSourceFinal` cấp Order | ✅ DONE (TASK-101, DEC-119) | `app/modules/lead_source/classifier.py` |
| `ConversionSchemeFinal` + `conversion_rate_final` cấp line | ✅ DONE (TASK-108A-1) | `app/modules/conversion/conversion_engine.py` |
| `config/conversion_rates.yaml` effective-dated | ✅ DONE | `config/` |

**Outputs** (`docs/analysis/02_FORMULA_MAPPING.md` §4, ánh xạ DEC-119/DEC-120):

```
PersonalProfit           = Σ EligibleKpiProfit của line thuộc đơn LeadSourceFinal = PERSONAL
AdsProfit                = Σ EligibleKpiProfit của line thuộc đơn LeadSourceFinal = ADS
PersonalConvertedRevenue = PersonalProfit / rate(employee, PERSONAL, ngày)
AdsConvertedRevenue      = AdsProfit      / rate(employee, ADS,      ngày)
TotalConvertedRevenue    = PersonalConvertedRevenue + AdsConvertedRevenue
```

Ba ràng buộc bắt buộc đi kèm (nguyên văn tài liệu): rate tra theo
`(employee, lead_source, ngày của đơn)` từ config có effective-dating, **không
hard-code**; **không có đường code nào chia một lợi nhuận gộp cho một tỉ lệ duy
nhất**; không nhân viên nào là trường hợp đặc biệt.

Bổ sung bởi DEC-127 §4: `ConversionScheme` ở **cấp line** (118/10.609 OrderID
chứa cả `DIEN_MAY` lẫn `GIA_DUNG`) — **cấm** cộng lợi nhuận của các line khác
scheme rồi chia chung một tỉ lệ. Nên phép chia thực tế phải ở mức
`(employee, month, lead_source, scheme)`, không phải mức `(employee, month, bucket)`.

**Consumer.** `TASK-109` (summary_engine) — cột "LN KPI" và "DS quy đổi";
sau đó `TASK-111` (excel_exporter). Không có consumer nào khác.

**`EligibleCosts` tác động tới gì?** Nó là số hạng **trừ thẳng vào
`EligibleKpiProfit`**, và `EligibleKpiProfit` là **tử số** của phép chia quy
đổi. Chuỗi tác động đầy đủ:

```
EligibleCosts → EligibleKpiProfit → ConvertedRevenue → % Target → Thưởng → Tổng lương
```

Không phải validation. **Là tiền lương của người thật.** Xem mục 8 để có số đo.

---

## 3. TASK-109 dependency — chính xác cần gì

Nguồn: đặc tả §15 (`docs/spec/Dac_ta_cong_cu_bao_cao_kinh_doanh.docx`, dòng
273–310), trích nguyên văn cấu trúc bảng:

| Chỉ tiêu | Personal | ADS | Total |
|---|---|---|---|
| Tổng đơn | Unique OrderID Personal | Unique OrderID Ads | Unique OrderID toàn bộ |
| Số SP | SUM Qty | SUM Qty | SUM Qty |
| Doanh số bán | SUM Sales | SUM Sales | Tổng |
| **LN KPI** | **SUM EligibleKpiProfit** | **SUM EligibleKpiProfit** | Tổng |
| **DS quy đổi** | **SUM Personal CR** | **SUM Ads CR** | Tổng CR |
| DSQĐ/đơn | Personal CR / Personal Orders | Ads CR / Ads Orders | Total CR / Total Orders |
| Lợi nhuận thực | SUM AccountingProfit | SUM AccountingProfit | Tổng |
| % Target | Có thể cấu hình | Có thể cấu hình | Total CR / Target |

Và: *"Summary phải cho phép xem mỗi nhân viên theo tháng và YTD."*

**Trả lời từng câu hỏi bắt buộc:**

| Câu hỏi | Trả lời | Căn cứ |
|---|---|---|
| Cần scalar `eligible_cost_total`? | **KHÔNG** ở tầng Summary. Cần `EligibleKpiProfit` đã trừ xong, tách theo bucket. | §15 không có dòng "Chi phí" |
| Cần breakdown theo category? | **KHÔNG** cho §15. **CÓ** cho audit/đối soát (GATE-01, TASK-111 sheet Audit/Overrides). | §15 vs §23 |
| Cần provenance? | **CÓ, bắt buộc.** Khuôn `_auto/_manual/_final` + `source_of_value` là chuẩn dự án (ADR-102, DEC-127 §6). Không có provenance thì không phân biệt "0 vì không có chi phí" với "0 vì chưa ai nhập". | ADR-102, DEC-103 |
| Per-line hay per-order? | **PER-LINE.** DEC-127 §4 hạ scheme xuống cấp line; cộng ở cấp order rồi chia một tỉ lệ là điều bị cấm tường minh. | DEC-127 §4 |
| Config-driven keys? | **CÓ.** Category chi phí là chính sách công ty ⇒ loại `B — Business rule`, bắt buộc ở config (đặc tả §28, `docs/analysis/03_RULE_CLASSIFICATION.md`). Cấm hard-code. | `docs/analysis/03_RULE_CLASSIFICATION.md` |
| Effective dating? | **CÓ.** Đặc tả §11 nguyên văn: *"Giá trị adjustment phải cấu hình được, có EffectiveFrom/EffectiveTo"*. `conversion_rates.yaml` đã theo khuôn này. | đặc tả §11 |
| Audit trail? | **CÓ** khi giá trị do người nhập (DEC-126 §4 — `suggested_amount` ≠ `final_amount`). | DEC-126 §4 |

**Ranh giới không được vượt:** §15 không yêu cầu allocation chi phí cấp
tháng/nhân viên, không yêu cầu cost center, không yêu cầu phân bổ chi phí chung.
Đưa những thứ đó vào TASK-108B là gold-plating ngoài production path.

---

## 4. Cost universe — toàn bộ khoản chi phí hiện hữu

Liệt kê từ code + config + spec + data model + workbook thật, không chỉ grep tên.

| # | Loại | Khoản mục | Field / nguồn | Type · đơn vị | Scope | Tham gia profit hiện tại? | Historical authority | Golden phủ? | Double-count? |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **E** | `Chiết khấu` → `Discount` | raw cột 12 → `WorkingLine.discount` | `Decimal`, VND | line | **CÓ** — trừ khỏi `TotalSales` trong `normalizer.py:27` | DEC-114 (doanh số), DEC-122/C4b (lợi nhuận) | ✅ `discount_delta` invariant | ⚠️ **CAO** |
| 2 | **C** | `Lương chuyến` → `DeliveryCost` (`K: Chi phí giao`) | raw cột 15 → `WorkingLine.delivery_cost` | `Decimal`, VND | line | **KHÔNG** — import rồi để đó, không module nào đọc | `K1=SUM(K3:K945)` tính nhưng **không nạp vào Summary** (`docs/analysis/02_FORMULA_MAPPING.md` §2) | ⚠️ chỉ tổng tiền, không phủ ngữ nghĩa | ⚠️ **TRUNG BÌNH** |
| 3 | **F** | `KpiPurchaseAdjustment` (`J: Giao hàng`: `Qua kho`/`NCC giao`/`KHBH`/`Thợ lắp`) | nhập tay sau import; `config/adjustments.yaml` | `Decimal` âm, VND | line, nhiều record/line | **CÓ — đã nhúng sẵn** vào `KpiPurchasePrice` (`F = L + J`) | DEC-125, DEC-126, `docs/analysis/02_FORMULA_MAPPING.md` §1 | ❌ không (chưa có persistence) | 🔴 **RẤT CAO** |
| 4 | **A** | Dòng `Chi phí vận chuyển` (~1.110 dòng/6 tháng) | dòng sản phẩm giả trong raw | tiền, VND | line | **CÓ — tính vào cả doanh số lẫn lợi nhuận** | DEC-110, `docs/analysis/03_RULE_CLASSIFICATION.md` | ✅ có mặt trong fixture (**19** dòng 01.2026, **10** dòng 06.2026) | 🔴 **RẤT CAO** |
| 5 | **A** | Dòng `Chi phí lắp đặt` / `Công lắp đặt` (~85) | như trên | tiền, VND | line | **CÓ** | DEC-110 | ✅ **3** / **1** dòng trong fixture | 🔴 **RẤT CAO** |
| 6 | **H** | Dòng `Chênh VAT` (~43) | như trên | tiền, VND | line | **CÓ** | DEC-110 | ✅ **1** dòng (06.2026) | 🔴 **RẤT CAO** |
| 7 | **A** | Dòng `Chi phí giao hộ…` (~8) | như trên | tiền, VND | line | **CÓ** | DEC-110 | ❌ không xuất hiện trong 2 kỳ fixture | 🔴 **RẤT CAO** |
| 8 | **A** | Dòng `Phí đổi trả` (2) | như trên | tiền, VND | line | **CÓ** | DEC-110 | ❌ | 🔴 **RẤT CAO** |
| 9 | **B** | **`EligibleCosts`** | **KHÔNG CÓ NGUỒN** | — | — | không (chưa tồn tại) | **KHÔNG CÓ** | ❌ | — |
| 10 | **B/I** | **`OtherKpiAdjustment`** | **KHÔNG CÓ NGUỒN** | — | — | không (chưa tồn tại) | **KHÔNG CÓ** | ❌ | — |
| 11 | **D** | Thưởng (`O = F × 0,5%`) | Summary workbook; `config/commission.yaml` **chưa tồn tại** | tiền | employee·month | **KHÔNG** — là *hệ quả* của CR | `docs/analysis/02_FORMULA_MAPPING.md` §3 | ❌ | không |
| 12 | **D** | Lương cứng (`Q = P × 4500/26`), Phụ cấp (`R`) | `config/payroll.yaml` **chưa tồn tại** | tiền | employee·month | **KHÔNG** | `docs/analysis/02_FORMULA_MAPPING.md` §3 | ❌ | không |
| 13 | **G** | Allocation / chi phí chung | **KHÔNG TỒN TẠI** ở bất kỳ đâu | — | — | không | — | — | — |
| 14 | **I** | `SourceProfit` (`Lợi nhuận` ERP) | raw cột 17 | `Decimal`, VND | line | **KHÔNG** — chỉ đối chiếu (DEC-103) | DEC-103 | ✅ `erp_profit_total` | ⚠️ đã gồm khoản chưa biết |

**Ba quan sát quyết định:**

1. **Mục 11–13 không phải chi phí của đơn hàng.** Thưởng/lương/phụ cấp là *đầu
   ra* của chuỗi quy đổi, không phải đầu vào. Đưa chúng vào `EligibleCosts` tạo
   vòng lặp: lương phụ thuộc CR, CR phụ thuộc lương.
2. **Mục 4–8 đã nằm trong lợi nhuận với tư cách dòng sản phẩm.** Đây là quyết
   định đã chốt của Owner (DEC-110), có mặt thật trong Golden fixture. Đưa cùng
   khoản đó vào `EligibleCosts` = trừ hai lần.
3. **Mục 3 đã nằm trong `KpiPurchasePrice`.** `F = L + J` là bằng chứng số học
   trực tiếp từ `06.2026 Tín Phát` dòng 10–11 (`docs/analysis/02_FORMULA_MAPPING.md` §1).

---

## 5. KNOWN / UNKNOWN / CONFLICT

### KNOWN — đã có authority rõ ràng

| Khoản | Kết luận đã có authority | Nguồn |
|---|---|---|
| `Discount` | Trừ khỏi doanh số (DEC-114) **và** trừ khỏi lợi nhuận KPI (DEC-122/C4b — Owner xác nhận trực tiếp 2026-08-23) | DEC-114, DEC-122 |
| `KpiPurchaseAdjustment` | Vào công thức qua `KpiPurchasePrice`, **không** qua `EligibleCosts`; chỉ dùng `final_amount` đã xác nhận; không mặc định 0 | DEC-125, DEC-126 §1–6 |
| Dòng phụ (mục 4–8) | Tính vào doanh số **và** lợi nhuận, loại trừ mềm bằng cờ `excluded_from_report` ở Review Queue | DEC-110, DEC-113 |
| `SourceProfit` | Chỉ đối chiếu, **không** suy ngược giá nhập | DEC-103 |
| Rate quy đổi | Config, effective-dated, 4 chiều | DEC-121, DEC-127, ADR-104/106 |

### UNKNOWN — tồn tại nhưng chưa có quyết định

| # | Khoản | Câu hỏi chưa trả lời |
|---|---|---|
| U1 | **`EligibleCosts` là tập gì** | Gồm khoản nào, ai nhập, nhập ở đâu (C15 nguyên văn) |
| U2 | **`DeliveryCost` có thuộc `EligibleCosts` không** | C15 **cấm tuyệt đối** suy ra là chi phí giao hàng. Vẫn chưa có câu trả lời CÓ/KHÔNG |
| U3 | **`OtherKpiAdjustment` là gì** | Xuất hiện **đúng 1 lần trong toàn repo và toàn đặc tả**, chỉ bên trong công thức. Cùng hạng với `EligibleCosts` nhưng **chưa có open question nào theo dõi** |
| U4 | Sign convention | `EligibleCosts` là số dương bị trừ, hay số âm được cộng? |
| U5 | Scope | Ghi theo line, order, hay tháng? |
| U6 | Null behavior | `NULL = 0` hay `NULL = Pending` (chặn tính)? |
| U7 | Effective date | Có cần `EffectiveFrom/To` như adjustment không? |

### CONFLICT — các nơi đang hiểu khác nhau

**CONFLICT DETECTED — biến thể công thức `EligibleKpiProfit`**

Bốn phiên bản cùng tồn tại trên nhánh mặc định:

| # | Nguồn | Công thức | `− Discount`? |
|---|---|---|---|
| V1 | Đặc tả §11 (docx dòng 216) | `(SellPrice − KpiPurchasePrice) × Qty − EligibleCosts + OtherKpiAdjustment` | **KHÔNG** |
| V2 | `01_DATA_MAPPING.md:69` | giống V1 | **KHÔNG** |
| V3 | `03_RULE_CLASSIFICATION.md:22`, `10_OPEN_QUESTIONS.md:39,186`, `TASK-107:63`, `PROJECT_DECISIONS.md:422` | `… × Qty − Discount − EligibleCosts + OtherKpiAdjustment` | **CÓ** |
| V4 | Workbook thật `In = (Gn−Fn)*En` | `(SellPrice − KpiPurchasePrice) × Qty` | không có số hạng nào |

*Documentation:* V1/V2 nói không trừ chiết khấu; V3 nói có.
*Implementation:* chưa có — nên chưa ai sai, nhưng người implement sẽ phải chọn.
*Risk:* chọn V1 thay vì V3 làm lợi nhuận KPI **cao hơn thực tế**, CR cao hơn,
thưởng cao hơn. Trên dữ liệu thật của Ly, chiết khấu là **0,39 %** doanh số.
*Recommended resolution:* **V3 thắng.** DEC-122 (2026-08-23) đóng C4b bằng câu
trả lời trực tiếp của Owner *"mặc định có"* — đó là authority mới nhất, và V1/V2
là văn bản có trước. `01_DATA_MAPPING.md:69` là **tài liệu lỗi thời cần sửa**,
không phải một ý kiến ngang hàng. Sửa nó thuộc TASK-108B implementation, không
thuộc phiên này.

**CONFLICT DETECTED — V4 vs V1/V3.** Workbook lịch sử **chưa từng** trừ
`EligibleCosts`, `Discount` hay cộng `OtherKpiAdjustment` vào cột `I`. Nghĩa là:
mọi giá trị `EligibleCosts ≠ 0` đều làm công cụ **lệch khỏi mọi con số lịch sử
đã được công ty dùng**. Đây không phải lỗi — đặc tả cố ý mở rộng công thức —
nhưng phải được Owner nhìn thấy trước khi quyết, vì GATE-01 sẽ đối chiếu chính
những con số đó.

---

## 6. Double-count analysis

| COST | HIỆN ĐANG NHÚNG Ở ĐÂU? | ELIGIBLE? | DOUBLE-COUNT RISK | DECISION NEEDED? |
|---|---|---|---|---|
| `Discount` | `TotalSales = SellPrice×Qty − Discount` (`normalizer.py:27`) **và** số hạng `− Discount` của V3 | đã là số hạng **riêng**, không thuộc `EligibleCosts` | 🔴 **RẤT CAO** nếu đưa vào `EligibleCosts` → trừ hai lần trong cùng một công thức | **KHÔNG** — DEC-122 đã đóng. Chỉ cần: **cấm** liệt kê `Discount` trong `EligibleCosts` |
| `KpiPurchaseAdjustment` (`J`) | đã nhúng vào `KpiPurchasePrice`; `F = L + J`, 635/18.148 dòng có `L` nhập tay | **KHÔNG** | 🔴 **RẤT CAO** — `(SellPrice − KpiPurchasePrice)` đã hưởng khoản này rồi | **KHÔNG** — DEC-125/126 đã đóng. Chỉ cần ghi cấm tường minh |
| Dòng `Chi phí vận chuyển` / `lắp đặt` / `Chênh VAT` / `giao hộ` / `đổi trả` | là **dòng sản phẩm**, tính vào doanh số **và** lợi nhuận (DEC-110). Có thật trong Golden: 22 dòng (01.2026), 12 dòng (06.2026) | **KHÔNG** | 🔴 **RẤT CAO** — cùng một khoản tiền vừa là doanh thu vừa là chi phí | **KHÔNG** — DEC-110 đã đóng. Chỉ cần ghi cấm tường minh |
| `DeliveryCost` (`Lương chuyến` / `K`) | **KHÔNG nhúng ở đâu cả.** Import vào `WorkingLine.delivery_cost` rồi không module nào đọc. Workbook tính `K1` nhưng **không nạp vào Summary** | ❓ **CHƯA BIẾT** | 🟡 **THẤP** về double-count (chưa ở đâu), nhưng ⚠️ **CAO** về sai số tuyệt đối | 🔴 **CÓ — đây là quyết định thật duy nhất còn lại** |
| `OtherKpiAdjustment` | không tồn tại | ❓ | không đo được | 🔴 **CÓ** |
| Thưởng / lương / phụ cấp | Summary, tính **từ** CR | **KHÔNG** | 🔴 **vòng lặp logic** | **KHÔNG** |
| `SourceProfit` | chỉ tham chiếu | **KHÔNG** | — | **KHÔNG** |

**Kết luận double-count:** trong toàn bộ cost universe, **chỉ đúng một khoản**
(`DeliveryCost`) là ứng viên `EligibleCosts` chưa bị double-count chặn — và
đó chính là khoản mà C15 **cấm tuyệt đối** suy đoán. Mọi ứng viên khác đều đã
được authority hiện có xử lý ở một chỗ khác trong công thức.

---

## 7. Golden coverage

Golden Baseline = 2 kỳ **Tín Phát** (01.2026, 06.2026), anonymized, FROZEN
(DEC-142). Đối chiếu từng path của TASK-108B:

| Path của TASK-108B | Golden phủ? | Test / fixture / invariant cụ thể | Expected output |
|---|---|---|---|
| `LeadSource` cấp Order + provenance | ✅ **COVERED** | `test_golden_lead_source_split_and_provenance`, `test_golden_lead_source_is_decided_at_order_level` | `orders_by_final: {ADS: 254}` (01), `{ADS: 146}` (06) |
| Tra `ConversionScheme` + rate | ✅ **COVERED** | `test_golden_scheme_distribution`, `test_golden_can_actually_fail_on_a_business_mutation` (4 mutation) | `ADS_7_5@0.075: 351` (01), `180` (06) |
| Unmapped không mượn rate | ✅ **COVERED** | `test_golden_unmapped_never_borrows_a_rate` | `unresolved_lines: 0` |
| `Discount` trừ khỏi **doanh số** | ✅ **COVERED** | `test_golden_discount_delta_equals_discount_column` | `total_delta: 2.300.000` (01), `400.000` (06); `every_delta_equals_that_line_discount: True` |
| Employee ownership | ✅ **COVERED** | `test_golden_employee_ownership_matrix` | `Tín Phát: 351 lines / 254 orders` |
| Integrity cấp dòng | ✅ **COVERED** | `test_golden_lines_digest_is_unchanged` + `_covered_digest_fields` (34 trường) | sha256 digest |
| **`EligibleKpiProfit` (số học)** | ❌ **NOT COVERED** | — | `pricing.accounting_profit_pending: 351/351`, `price_source_distribution: {Pending: 351}` — **mọi giá nhập đều Pending**, nên mọi profit đều `None` |
| **`Discount` trừ khỏi lợi nhuận** (V3) | ❌ **NOT COVERED** | Golden chỉ canh delta **doanh số** | — |
| **`EligibleCosts` bất kỳ hình thức nào** | ❌ **NOT COVERED** | không tồn tại | — |
| **`DeliveryCost` tham gia profit** | 🟡 **PARTIAL** | `money.delivery_cost_total` được ghi (`26.270.000` / `11.670.000`) nhưng **không invariant nào khẳng định nó có/không vào profit** | chỉ là tổng tiền thụ động |
| **Bucket PERSONAL** | ❌ **NOT COVERED** | fixture **100 % ADS** ở cả hai kỳ | `lines_by_final: {ADS: …}` — không có dòng PERSONAL nào |
| **Phép chia hai bucket rồi cộng** | ❌ **NOT COVERED** | hệ quả của dòng trên | — |
| **`NOI_THANH_2` / `GIA_DUNG_8`** | ❌ **NOT COVERED** | `product_group_distribution: {DIEN_MAY: 351}`, provenance `{DEFAULT: 351}` | — |
| **Đơn trộn scheme (118 OrderID)** | ❌ **NOT COVERED** | fixture chỉ có 1 scheme duy nhất | — |

**Áp dụng V4.1 §4.1 một cách trung thực:** Golden **KHÔNG** được dùng để hạ
Blast Radius của TASK-108B. Toàn bộ failure path mà TASK-108B tạo ra —
số học profit, số hạng chi phí, tách hai bucket, nhiều scheme — nằm đúng vào
vùng Golden **không** phủ. Câu "Golden Baseline tồn tại nên module này an toàn"
bị §4.1 cấm tường minh, và ở đây nó còn sai về mặt sự kiện.

**Một hệ quả kỹ thuật phải biết trước khi implement.**
`test_golden_lines_digest_is_unchanged` khẳng định cả `lines_digest` **lẫn**
`_covered_digest_fields`. `covered_digest_fields()` lấy tập trường từ
`dataclasses.fields(WorkingLine)`. Vì vậy **mọi field mới thêm vào
`WorkingLine`** (`eligible_costs`, `eligible_kpi_profit`, …) sẽ làm Golden
**ĐỎ**. Đây là **thiết kế cố ý**, ghi ngay trong docstring: *"một trường thêm
vào ngày mai tự động được canh"*. Xử lý đúng = sinh lại expected một cách tường
minh (`python3 -m tests.fixtures.golden.build_expected`) **kèm Owner Decision**
theo docstring của chính test — **không** phải "sửa test cho xanh". Phải đưa
vào Completion Gate của TASK-108B ngay từ đầu, không để phát hiện giữa chừng.

**Golden coverage proposal (KHÔNG thực hiện trong phiên này).** Sau khi
TASK-108B implement xong, đề xuất mở rộng Golden bằng một kỳ có nhân viên
`PERSONAL` thật (Ly hoặc Thắng) và một kỳ của kênh `NOI_THANH` — hai path
chiếm phần lớn rủi ro và hiện phủ 0 %. Cần Owner cấp dữ liệu và một task riêng.
**Phiên này không sửa Golden.**

---

## 8. Effective Risk

Chấm theo **failure path**, không theo tên file (V4.1 §4).

**Failure path:** `EligibleCosts` sai → `EligibleKpiProfit` sai → chia cho rate
→ `ConvertedRevenue` sai → `% Target` sai → `Thưởng = CR × tỉ lệ` sai →
`Tổng lương` sai → **tiền lương của người thật sai**.

**Đo trên dữ liệu Golden thật** (Tín Phát, 100 % ADS, rate 7,5 %). Dùng
`erp_profit_total` làm bậc độ lớn của lợi nhuận (mọi giá nhập đang Pending nên
`EligibleKpiProfit` chưa tính được — nêu rõ đây là proxy, không phải chính con
số cuối):

| Kỳ | Lợi nhuận (ERP) | `delivery_cost` | % lợi nhuận | Chênh **CR** nếu trừ / không trừ | Chênh **thưởng** @0,5 % |
|---|---:|---:|---:|---:|---:|
| 01.2026 | 240.032.781 | 26.270.000 | **10,94 %** | **350.266.667 VND** | **1.751.333 VND/tháng** |
| 06.2026 | 95.956.942 | 11.670.000 | **12,16 %** | **155.600.000 VND** | **778.000 VND/tháng** |

Đây là **một nhân viên, một tháng**. Một quyết định CÓ/KHÔNG duy nhất về
`DeliveryCost` dịch chuyển thưởng khoảng **0,8–1,8 triệu đồng/người/tháng**, và
không ai phát hiện được bằng cách nhìn kết quả — đúng loại rủi ro mà C15,
DEC-103 và DEC-126 §6 tồn tại để chặn.

```
Local Risk    = MEDIUM   (số học đơn giản, module nhỏ)
Blast Radius  = HIGH     (lương/thưởng người thật; không Golden test nào phủ path này)
Golden giảm bậc = KHÔNG áp dụng (V4.1 §4.1 — không có test cụ thể phủ đúng path)

Effective Risk = max(MEDIUM, HIGH) = HIGH
```

**Lý do không chấm LOW/MEDIUM:** không phải vì "internal tool", mà vì
failure path kết thúc ở bảng lương và không có lưới an toàn tự động nào trên
đường đó.

---

## 9. Review Budget proposal

Theo bảng đã freeze V4.1 §2 và `PROJECT/REVIEW_BUDGET_LEDGER.md`:

```
root_task               : TASK-108B
effective_risk          : HIGH
repair_cycles_allowed   : 2          (HIGH/CRITICAL = 2 — không tồn tại HIGH = 3)
repair_cycles_used      : 0
repair_cycles_remaining : 2
lineage                 : MỚI — độc lập với TASK-110 (EXHAUSTED_PRE_V4.1)
                          và với TASK-GOLDEN-BASELINE-001
```

Ràng buộc kèm theo:

- `TASK-109` **thuộc lineage riêng**, không dùng chung ngân sách này, và
  không được mở để reset ngân sách của `TASK-108B`.
- Sub-unit (`108B-A`, `108B-R1`, …) **không** có ngân sách riêng, **không**
  reset ngân sách (V4.1 §2).
- Vượt 2 cycle → `OWNER_EXTENSION REQUIRED`, không tự tách lineage.
- Ledger entry chỉ được ghi **sau** khi Owner phê duyệt OD-108B-01 — phiên này
  **không** ghi vào `PROJECT/REVIEW_BUDGET_LEDGER.md`.

---

## 10. Owner Options

Ba option, tất cả xuất phát từ code/spec/DEC hiện có.

### OPTION A — `EligibleCosts` = tập rỗng đã đóng (Closed Empty Set)

*Semantics.* `EligibleCosts` được định nghĩa hữu hạn là **tập rỗng**: không
khoản chi phí nào ngoài `Discount` và `KpiPurchaseAdjustment` (đã là số hạng
riêng) được trừ vào `EligibleKpiProfit`. `DeliveryCost` giữ nguyên là chỉ số
logistics, không vào profit.

```
EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity − Discount + OtherKpiAdjustment
```

- *Implementation cost:* **thấp nhất.** Không field mới cho chi phí, không config mới.
- *Compatibility:* **cao nhất** — khớp đúng hành vi workbook lịch sử
  (`K1` không nạp vào Summary), nên GATE-01 đối chiếu thuận lợi.
- *Double-count risk:* **0** theo cấu trúc.
- *TASK-109 compatibility:* đầy đủ — §15 không cần dòng chi phí.
- *Migration cost:* 0.
- ⚠️ **Cảnh báo bắt buộc:** đây **KHÔNG** phải `EligibleCosts = 0` bị C15 cấm.
  C15 cấm **giả định** `= 0` để cho xong. Option A là **Owner tuyên bố tập
  rỗng** kèm lý do và cơ chế mở lại — khác nhau về bản chất authority. Nếu Owner
  **không** tuyên bố tường minh, agent **không** được tự chọn option này.
- *Verdict:* **RECOMMENDED** (xem mục 11).

### OPTION B — Allowlist tường minh có `DeliveryCost`

*Semantics.* `EligibleCosts = DeliveryCost` (khoản duy nhất có dữ liệu thật và
chưa bị nhúng ở đâu). Cấu hình bằng `config/eligible_costs.yaml` với đúng một
key bật/tắt, có effective-dating.

- *Implementation cost:* trung bình — thêm field, config, provenance, test.
- *Compatibility:* **thấp** — làm mọi con số lệch **10–12 %** khỏi lịch sử
  (mục 8). GATE-01 sẽ đỏ ở mọi kỳ, và phải giải thích được lệch là *đúng*.
- *Double-count risk:* thấp về cấu trúc, **nhưng** `Chi phí vận chuyển` đã tồn
  tại như **dòng sản phẩm** tính vào lợi nhuận (DEC-110). Nếu một chuyến giao
  vừa được ghi ở cột `Lương chuyến` vừa được ghi thành dòng `Chi phí vận
  chuyển`, đây **là** double-count thật. **Chưa ai đo tỉ lệ trùng này.**
- *TASK-109 compatibility:* đầy đủ.
- *Migration cost:* cao — mọi số lịch sử phải đọc lại.
- *Verdict:* **NOT RECOMMENDED khi chưa đo trùng lặp** — vi phạm chính điều
  cấm của C15 nếu chọn mà không có bằng chứng.

### OPTION C — Khung config rỗng, mở rộng theo effective date

*Semantics.* Xây đầy đủ cơ chế `EligibleCosts` (config-driven registry,
provenance, effective-dating, audit) nhưng **phát hành với 0 category bật**.
Thêm category sau này chỉ là sửa config + một DEC.

- *Implementation cost:* **cao nhất** — toàn bộ máy móc cho 0 người dùng.
- *Compatibility:* cao (hành vi runtime giống Option A).
- *Double-count risk:* **cao theo thời gian** — khung rỗng mời gọi thêm
  category sau này mà không lặp lại phân tích double-count của mục 6.
- *TASK-109 compatibility:* đầy đủ.
- *Migration cost:* thấp về sau, cao lúc đầu.
- *Verdict:* **NOT RECOMMENDED cho Phase 1** — gold-plating ngoài production
  path (V4.1 §5): không có nguồn production nào hiện tại cần category thứ hai.

---

## 11. Recommended Owner Decision

**OPTION A**, kèm ba điều kiện bắt buộc.

*Vì sao A chứ không phải B.* Mục 6 cho thấy trong 14 khoản của cost universe,
**13 khoản** đã được authority hiện có xử lý ở một chỗ khác trong công thức —
đưa lại vào `EligibleCosts` là trừ hai lần. Khoản thứ 14 (`DeliveryCost`) là
ứng viên duy nhất còn lại, và ba bằng chứng độc lập đều chỉ về "không trừ":

1. Workbook thật tính `K1 = SUM(K3:K945)` rồi **không nạp vào Summary** — công
   ty đã có con số đó và đã chọn không dùng nó cho KPI.
2. `docs/analysis/01_DATA_MAPPING.md` xếp `DeliveryCost → K: Chi phí giao` là một cột **báo
   cáo độc lập**, không phải số hạng của công thức lợi nhuận.
3. Đặc tả §11 đặt `EligibleCosts` trong mục **"Adjustment nghiệp vụ - ví dụ qua
   kho"** — ngữ cảnh là adjustment giá nhập, không phải chi phí logistics.

Ba bằng chứng này **không đủ** để agent tự quyết (C15 cấm suy ra `EligibleCosts`
là chi phí giao hàng — và cấm cả chiều ngược lại là *suy đoán*). Nhưng chúng đủ
để đề xuất một mặc định có lý cho Owner **xác nhận hoặc bác bỏ**.

*Ba điều kiện bắt buộc:*

- **Đ1.** Owner tuyên bố tường minh tập rỗng, kèm câu trả lời **CÓ/KHÔNG** riêng
  cho `DeliveryCost`. Không có câu trả lời đó, C15 **không** đóng.
- **Đ2.** Owner định nghĩa `OtherKpiAdjustment` (U3). Đóng C15 mà bỏ U3 thì
  TASK-108B **vẫn** BLOCKED — chỉ đổi tên khoản chặn.
- **Đ3.** Owner xác nhận biến thể công thức **V3** (có `− Discount`), và chấp
  nhận rằng `01_DATA_MAPPING.md:69` sẽ được sửa cho khớp.

---

## 12. Implementation contract đề xuất

Chỉ có hiệu lực **sau** khi Owner phê duyệt OD-108B-01.

### EligibleCosts registry

```yaml
# config/eligible_costs.yaml  (MỚI)
schema_version: 1
# Tập RỖNG do Owner tuyên bố (OD-108B-01), KHÔNG phải mặc định do thiếu dữ liệu.
# Thêm bất kỳ key nào ở đây đều cần một DEC mới + phân tích double-count lại
# theo docs/tasks/TASK-108B-eligible-costs-owner-definition.md §6.
eligible_cost_categories: []

# Danh sách CẤM — ghi tường minh để lần sau không phải suy luận lại.
# Mỗi mục nêu authority đã xử lý khoản đó ở đâu.
excluded_by_authority:
  discount:              "số hạng riêng '− Discount' (DEC-114, DEC-122); vào EligibleCosts = trừ hai lần"
  kpi_purchase_adjustment: "đã nhúng trong KpiPurchasePrice, F = L + J (DEC-125, DEC-126)"
  non_product_cost_lines:  "đã tính vào doanh số VÀ lợi nhuận dưới dạng dòng sản phẩm (DEC-110)"
  delivery_cost:           "OD-108B-01 — chỉ số logistics, không vào profit KPI"
  commission_salary_allowance: "hệ quả của ConvertedRevenue, không phải đầu vào — đưa vào tạo vòng lặp"
  source_profit:           "chỉ đối chiếu, không suy ngược (DEC-103)"
```

### Từng khoá — schema hữu hạn

Registry hiện rỗng; khi Owner thêm category, mỗi entry **phải** đủ 11 trường:

| Trường | Bắt buộc | Ý nghĩa |
|---|---|---|
| `key` | ✅ | định danh máy đọc, `snake_case` |
| `display_name_vi` | ✅ | tên nghiệp vụ tiếng Việt |
| `eligible` | ✅ | `YES` / `NO` |
| `scope` | ✅ | `LINE` \| `ORDER` \| `EMPLOYEE_MONTH` |
| `sign` | ✅ | `POSITIVE_REDUCES_PROFIT` \| `NEGATIVE_INCREASES_PROFIT` |
| `source_field` | ✅ | đường dẫn field cụ thể; `MANUAL_ENTRY` nếu người nhập |
| `missing_value_rule` | ✅ | `PENDING_BLOCKS_COMPUTE` \| `TREAT_AS_ZERO` |
| `duplicate_rule` | ✅ | `ONCE_PER_ORDER` \| `PER_LINE` |
| `effective_from` / `effective_to` | ✅ | ISO date, `null` = mở |
| `owner_override_allowed` | ✅ | `true` / `false` |
| `reason` | ✅ | tham chiếu DEC/OD |

### Rules (áp dụng khi registry rỗng)

```
scope            : LINE — mọi số hạng của EligibleKpiProfit tính ở cấp line (DEC-127 §4)
sign             : POSITIVE_REDUCES_PROFIT (quy ước; hiện không có khoản nào)
null             : PENDING_BLOCKS_COMPUTE — thiếu input ⇒ EligibleKpiProfit = None,
                   KHÔNG BAO GIỜ 0 (DEC-103, DEC-126 §6, 03_DATA_MODEL_RULES §5)
duplicate        : không áp dụng (registry rỗng). Khi thêm khoản scope=ORDER,
                   bắt buộc ONCE_PER_ORDER — đơn nhiều dòng KHÔNG nhân lên
effective_date   : registry đọc theo NGÀY CỦA ĐƠN, cùng khuôn conversion_rates.yaml
provenance       : eligible_costs_source_of_value = "Config:EmptySet(OD-108B-01)"
                   — hằng số nhìn thấy được, không phải im lặng
```

### Output schema

```python
# app/modules/domain/models.py — WorkingLine (thêm)
eligible_costs: Optional[Decimal] = None            # None = chưa tính được
eligible_costs_source_of_value: Optional[str] = None
eligible_kpi_profit: Optional[Decimal] = None       # None nếu bất kỳ input nào Pending
other_kpi_adjustment: Optional[Decimal] = None      # chờ Đ2 của Owner

# app/modules/conversion/ -> converted_revenue.py (MỚI)
@dataclass(frozen=True)
class ConvertedRevenueBucket:
    lead_source: str                 # PERSONAL | ADS
    scheme: str
    rate: Optional[Decimal]
    eligible_kpi_profit: Optional[Decimal]
    converted_revenue: Optional[Decimal]
    line_count: int
    source_of_value: str

@dataclass(frozen=True)
class EmployeeMonthConvertedRevenue:
    employee_normalized: str
    month: str                                   # "YYYY-MM"
    buckets: tuple[ConvertedRevenueBucket, ...]  # gộp theo (lead_source, scheme)
    total_converted_revenue: Optional[Decimal]   # None nếu bất kỳ bucket nào None
    unresolved_line_count: int
```

Bất biến bắt buộc: **không** có đường code nào chia một lợi nhuận gộp cho một
tỉ lệ duy nhất; gộp theo `(employee, month, lead_source, scheme)` rồi mới chia,
rồi mới cộng (`docs/analysis/02_FORMULA_MAPPING.md` §4 ràng buộc 2 + DEC-127 §4).

---

## 13. Files dự kiến touch khi implementation

| File | Hành động | Ghi chú |
|---|---|---|
| `config/eligible_costs.yaml` | **MỚI** | registry rỗng + danh sách cấm |
| `app/modules/domain/models.py` | SỬA | 4 field mới trên `WorkingLine` |
| `app/modules/profit/` → `kpi_profit.py` | **MỚI** | `EligibleKpiProfit`; **không** sửa `profit_engine.py` (DEC-126 §1 tách hai luồng) |
| `app/modules/conversion/` → `converted_revenue.py` | **MỚI** | gộp bucket + chia rate |
| `app/modules/config/loader.py` | SỬA (nhỏ) | nạp registry mới |
| `app/pipeline.py` | SỬA | bước 11; giữ nguyên chữ ký `run_import` (`test_golden_pipeline_entry_point_signature_is_locked`) |
| `tests/` → `test_kpi_profit.py`, `test_converted_revenue.py` | **MỚI** | |
| `tests/fixtures/golden/expected/*.json` | **SINH LẠI** | bắt buộc do field mới; tường minh + Owner Decision (mục 7) |
| `docs/analysis/01_DATA_MAPPING.md:69` | SỬA | thêm `− Discount` cho khớp V3 (Đ3) |
| `docs/analysis/10_OPEN_QUESTIONS.md` | SỬA | đóng C15, ghi U3 |
| `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/PROJECT_DECISIONS.md`, `PROJECT/REVIEW_BUDGET_LEDGER.md` | SỬA | sau Owner approval |

**FORBIDDEN (Scope Lock đề xuất):**

```
app/modules/profit/profit_engine.py                 : FORBIDDEN (AccountingProfit — DEC-126 §1)
app/modules/adjustment/**, app/modules/pricing/**   : FORBIDDEN
app/modules/validation/**                           : FORBIDDEN
tests/test_golden_baseline.py                       : FORBIDDEN (chỉ sinh lại expected, không sửa test)
tests/fixtures/golden/*.xlsx                        : FORBIDDEN
tests/fixtures/baseline/**, tests/test_task110_non_regression.py : FORBIDDEN
docs/tasks/TASK-110*, CHECK-110-16, R1-A1           : FORBIDDEN
governance/**                                       : FORBIDDEN
TASK-109 (summary_engine)                           : FORBIDDEN — task riêng
```

---

## 14. Completion Gate đề xuất

Hữu hạn, đo được. Mọi check là `REQUIRED` trừ khi ghi khác. `Risk = HIGH` ⇒
E1 bắt buộc cho mọi check REQUIRED (`governance/core/EVIDENCE_STANDARD.md`).

| ID | Check | Evidence Level |
|---|---|---|
| CHECK-108B-01 | `config/eligible_costs.yaml` tồn tại, `eligible_cost_categories == []`, có đủ 6 mục `excluded_by_authority` | E1 |
| CHECK-108B-02 | Grep chứng minh **không** đường code nào cộng `discount`, `delivery_cost`, hay `kpi_purchase_adjustment` vào `eligible_costs` | E1 |
| CHECK-108B-03 | Bất kỳ input nào Pending ⇒ `eligible_kpi_profit is None`; test khẳng định **không bao giờ** `Decimal("0")` | E1 |
| CHECK-108B-04 | `eligible_costs_source_of_value` khác `None` trên **mọi** dòng đã tính | E1 |
| CHECK-108B-05 | Đơn nhiều dòng: chi phí scope=ORDER không nhân lên (property test; hiện vacuous vì registry rỗng — ghi rõ là vacuous, không ghi PASS trống) | E1 |
| CHECK-108B-06 | Bucket gộp theo `(employee, month, lead_source, scheme)`; test chứng minh `(PersonalProfit + AdsProfit) / 5,5%` **khác** kết quả engine | E1 |
| CHECK-108B-07 | Không rate hard-code: grep `0.055`/`0.075`/`0.02`/`0.08` trong `app/` = 0 hit | E1 |
| CHECK-108B-08 | Line `Unresolved` **không bao giờ** lọt vào bucket; vào Review Queue | E1 |
| CHECK-108B-09 | Công thức implement đúng **V3** (có `− Discount`); test số học trên giá trị văn tự | E1 |
| CHECK-108B-10 | `pytest -q` toàn bộ: 0 regression so với baseline `7e60978` (`697 passed, 11 skipped`) | E1 |
| CHECK-108B-11 | Golden: expected sinh lại tường minh; **diff chỉ chứa field mới**; mọi business anchor cũ (`lead_source`, `scheme_distribution`, `discount_delta`, `employees`, `money.*`) **không đổi một byte** | **E2** |
| CHECK-108B-12 | `test_golden_pipeline_entry_point_signature_is_locked` PASS (chữ ký `run_import` không đổi) | E1 |
| CHECK-108B-13 | `01_DATA_MAPPING.md:69` đã sửa; 4 biến thể công thức hội tụ về V3 | E1 |
| CHECK-108B-14 | `scripts/branch_authority_check.sh` = `AUTHORITY_OK` tại SHA giao nộp | E1 |
| CHECK-108B-15 | `OtherKpiAdjustment` có định nghĩa Owner (Đ2) **hoặc** được descope tường minh bằng Owner Decision | E1 |

**Exit Criteria.** 15/15 REQUIRED `PASS`; CHECK-108B-11 đạt `E2`; Owner
Decision OD-108B-01 (kèm Đ1/Đ2/Đ3) đã ghi vào `PROJECT/PROJECT_DECISIONS.md`;
ledger có entry `TASK-108B`. **Không** yêu cầu `TASK-109` PASS — lineage khác.

---

## 15. BLOCKING findings

Phân loại theo V4.1 §7. `BLOCKING` = có production path hiện tại + tác động
correctness/business.

**B-01 — `TASK-108B` bị chặn bởi BỐN dependency, không phải một.**
`docs/tasks/TASK-108A-1-conversion-scheme-resolver.md:72-75` liệt kê nguyên văn:
(1) `AccountingPurchasePrice`/Price Master; (2) confirmed KPI Adjustment
(DEC-126 §3–6); (3) `OtherKpiAdjustment`; (4) `EligibleCosts` (C15).
*Production path:* Golden xác nhận `price_source_distribution: {Pending: 351}` —
**100 % giá nhập đang Pending** trên dữ liệu production thật. DEC-126 §5–6:
chỉ adjustment đã `final_amount` xác nhận mới vào công thức, mà tầng
persistence đó là TASK-202/302/305 (Phase 2/3, chưa tồn tại).
*Hệ quả:* **đóng C15 KHÔNG mở khoá được TASK-108B implementation.** Kể cả sau
OD-108B-01, engine sẽ trả `None` cho **mọi dòng** ở Phase 1.
*Đề xuất:* implement TASK-108B là hợp lệ và có giá trị (cấu trúc + provenance +
test đúng, chờ dữ liệu), nhưng Owner phải biết rằng nó **không** tạo ra con số
dùng được cho tới khi có Price Master. Nếu Owner muốn số thật, thứ tự đúng là
Price Master **trước** TASK-108B.

**B-02 — `OtherKpiAdjustment` chưa có định nghĩa và chưa có ai theo dõi.**
Grep toàn repo + toàn đặc tả: xuất hiện **đúng bên trong công thức**, không có
một dòng định nghĩa nào; đặc tả §9 (bảng field) có `KpiAdjustment` nhưng
**không** có `OtherKpiAdjustment`. Cùng hạng ambiguity với `EligibleCosts`
nhưng **không** có open question nào (C15 chỉ phủ `EligibleCosts`).
*Production path:* là số hạng cộng thẳng vào `EligibleKpiProfit` → cùng failure
path tới bảng lương ở mục 8.
*Đề xuất:* mở **C16** hoặc gộp vào OD-108B-01 điều kiện Đ2.

**B-03 — Công thức `EligibleKpiProfit` tồn tại 4 biến thể không nhất quán.**
Chi tiết ở mục 5. `01_DATA_MAPPING.md:69` (không `− Discount`) mâu thuẫn với
`03_RULE_CLASSIFICATION.md:22` (có `− Discount`).
*Production path:* người implement phải chọn một; chọn sai làm thưởng cao hơn
thực tế. Trên Ly, chiết khấu là 0,39 % doanh số, 302/408 dòng.
*Đề xuất:* Owner xác nhận V3 (Đ3); sửa `docs/analysis/01_DATA_MAPPING.md` trong TASK-108B.

**B-04 — Golden Baseline không phủ path nào của TASK-108B.**
Chi tiết ở mục 7: profit số học NOT COVERED (mọi giá Pending), bucket PERSONAL
NOT COVERED (fixture 100 % ADS), `NOI_THANH_2`/`GIA_DUNG_8` NOT COVERED, đơn
trộn scheme NOT COVERED.
*Production path:* toàn bộ vùng thay đổi của TASK-108B nằm ngoài lưới an toàn.
*Đề xuất:* **không** hạ Blast Radius (V4.1 §4.1). Giữ `Effective Risk = HIGH`.
Golden coverage proposal ở mục 7 — task riêng, sau implementation.

---

## 16. HARDENING findings

Không có production path hiện tại (V4.1 §7), kèm RE-TRIGGER CONDITION cụ thể.

**HB-108B-01 — Trùng lặp giữa `Lương chuyến` và dòng `Chi phí vận chuyển`.**
Chưa ai đo có bao nhiêu chuyến giao vừa xuất hiện ở cột `Lương chuyến` vừa
xuất hiện thành một dòng `Chi phí vận chuyển` riêng. Hiện **không** là
production path vì Option A không đưa `DeliveryCost` vào profit.
*RE-TRIGGER:* kích hoạt ngay khi bất kỳ ai đề xuất `delivery_cost.eligible = YES`
trong `config/eligible_costs.yaml`. Cơ chế: `CHECK-108B-02` grep sẽ đỏ.

**HB-108B-02 — `config/targets.yaml`, `commission.yaml`, `payroll.yaml` được
`docs/analysis/03_RULE_CLASSIFICATION.md` §B tham chiếu nhưng KHÔNG TỒN TẠI** (`ls config/`
chỉ có 5 file). Không chặn TASK-108B (không dùng target/lương).
*RE-TRIGGER:* chặn TASK-109 ở cột `% Target` và cột `Thưởng`. Kiểm bằng
`test -f config/targets.yaml` khi TASK-109 mở Ready Gate.

**HB-108B-03 — `WorkingLine` chưa có `kpi_purchase_price`/`kpi_purchase_adjustment`.**
Công thức cần chúng; hiện chỉ có `accounting_purchase_price`. Không là
production path vì persistence adjustment thuộc Phase 2/3 (DEC-126 §3).
*RE-TRIGGER:* khi TASK-202/302/305 mở, hoặc khi TASK-108B implementation cần
đọc `KpiPurchasePrice` — lúc đó phải quay lại DEC-126 §3 (một Order hỗ trợ
**nhiều** Adjustment record, không phải một field cộng dồn).

**HB-108B-04 — Sinh lại Golden expected là điểm dễ sai nhất của TASK-108B.**
Field mới ⇒ `lines_digest` + `_covered_digest_fields` đổi ⇒ Golden đỏ. Cám dỗ
"sửa test cho xanh" là đúng kịch bản BR-2 mà ledger đã ghi cho
`TASK-GOLDEN-BASELINE-001`.
*RE-TRIGGER:* `CHECK-108B-11` yêu cầu E2 — diff của expected phải **chỉ** chứa
field mới; mọi business anchor cũ không đổi một byte.

---

## 17. OUT_OF_SCOPE findings

- **`TASK-108A-2`** (auto-classification `ProductGroup`) — `NOT REQUIRED FOR PHASE 1`
  (DEC-127 §5). Hệ quả đã biết và được chấp nhận: dòng Gia dụng của kênh Nội
  thành quy đổi 2 % thay vì 8 % cho tới khi có UI checkbox. Không phải lỗi của
  TASK-108B.
- **`CHECK-110-16`** — vẫn `REQUIRED · BLOCKED · POST_MERGE_PRODUCTION_ACCEPTANCE`.
  Không đụng, không đổi, không diễn giải lại (DEC-141).
- **`R1-A2` → `R8`** — `OWNER_EXTENSION REQUIRED`, ngân sách `TASK-110`
  `remaining = 0`. Phiên này không mở.
- **`TASK-109`** — lineage riêng. Phiên này chỉ **đọc** yêu cầu của nó để không
  làm TASK-108B hẹp hơn thực tế cần.
- **Lỗi công thức của workbook mẫu** (`docs/analysis/05_EXCEPTIONS.md` A1/A2/A4) — đã biết,
  thuộc TASK-109/111.
- **Mở rộng Golden sang kỳ PERSONAL / NOI_THANH** — cần dữ liệu Owner + task
  riêng. Đề xuất ghi ở mục 7, **không** thực hiện.

---

## 18. Readiness verdict

```
OWNER_DECISION_REQUIRED
```

**Vì sao không phải `READY_FOR_OWNER_APPROVAL`:** verdict đó ngụ ý phần định
nghĩa nghiệp vụ đã hữu hạn và chỉ chờ chữ ký. Ở đây còn **hai** khoảng trống
định nghĩa thật, không phải một:

1. `EligibleCosts` (C15) — có đề xuất hữu hạn ở mục 11, chờ Owner xác nhận.
2. `OtherKpiAdjustment` (B-02) — **chưa có đề xuất nào**, vì repo không chứa
   một dòng nào để suy ra, và C15 cấm chính xác kiểu suy đoán đó.

Thêm vào đó, B-01 cho thấy ngay cả khi cả hai đóng, `TASK-108B` vẫn còn hai
dependency dữ liệu (Price Master; confirmed KPI Adjustment persistence) khiến
engine trả `None` cho mọi dòng ở Phase 1.

**Không ghi `IMPLEMENTATION_READY`.** Owner chưa phê duyệt semantics.

---

## OWNER DECISION PROPOSAL

```
OWNER DECISION — OD-108B-01

Decision:
  `EligibleCosts` được định nghĩa là TẬP RỖNG ĐÃ ĐÓNG (Closed Empty Set) cho
  Phase 1. Đây là tuyên bố có thẩm quyền của chủ dự án kèm lý do và cơ chế mở
  lại — KHÔNG phải giả định `= 0` mà C15 cấm.

  Công thức chốt (biến thể V3):
    EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity
                        − Discount
                        − EligibleCosts        (= 0 vì tập rỗng)
                        + OtherKpiAdjustment   (chờ Đ2)

EligibleCosts:
  discount                     : NO   — đã là số hạng riêng (DEC-114, DEC-122)
  kpi_purchase_adjustment      : NO   — đã nhúng trong KpiPurchasePrice (F = L + J)
  non_product_cost_lines       : NO   — đã vào doanh số VÀ lợi nhuận (DEC-110)
  delivery_cost                : NO   — chỉ số logistics, không vào profit KPI   ← Đ1
  commission_salary_allowance  : NO   — hệ quả của CR, không phải đầu vào
  source_profit                : NO   — chỉ đối chiếu (DEC-103)
  allocation_shared_cost       : N/A  — không tồn tại trong hệ thống
  tax_fee                      : NO   — `Chênh VAT` đã là dòng sản phẩm (DEC-110)
  (không có key nào = YES)

Rules:
  scope          : LINE  (DEC-127 §4 — cấm cộng line khác scheme rồi chia chung)
  sign           : POSITIVE_REDUCES_PROFIT
  null           : PENDING_BLOCKS_COMPUTE — thiếu input ⇒ EligibleKpiProfit = None,
                   KHÔNG BAO GIỜ 0 (DEC-103, DEC-126 §6)
  duplicate      : ONCE_PER_ORDER bắt buộc cho mọi khoản scope=ORDER thêm sau này
  effective_date : registry đọc theo NGÀY CỦA ĐƠN, khuôn conversion_rates.yaml
  provenance     : eligible_costs_source_of_value = "Config:EmptySet(OD-108B-01)"
  config         : config/eligible_costs.yaml — thêm key mới cần DEC mới
                   + phân tích double-count lại theo báo cáo này §6

TASK-109 contract:
  cung cấp : EligibleKpiProfit cấp line (Optional[Decimal])
             + ConvertedRevenue gộp theo (employee, month, lead_source, scheme)
             + total_converted_revenue theo (employee, month)
             + provenance + unresolved_line_count
  KHÔNG cung cấp : eligible_cost_total, cost breakdown (§15 không yêu cầu)
  bất biến : không đường code nào chia một lợi nhuận gộp cho một tỉ lệ duy nhất

Risk:
  Effective Risk = HIGH
    Local Risk   = MEDIUM
    Blast Radius = HIGH — failure path kết thúc ở bảng lương
    Golden       = KHÔNG hạ bậc (V4.1 §4.1 — không test nào phủ đúng path)
  Đo trên Golden thật: một quyết định CÓ/KHÔNG về delivery_cost dịch chuyển
  thưởng 0,8–1,8 triệu VND/người/tháng (báo cáo §8).

Review Budget:
  root_task = TASK-108B (lineage MỚI)
  effective_risk = HIGH
  repair_cycles_allowed = 2, used = 0, remaining = 2
  sub-unit không có ngân sách riêng, không reset

ĐIỀU KIỆN BẮT BUỘC — quyết định này CHƯA đủ để mở implementation nếu thiếu:
  Đ1. Xác nhận CÓ/KHÔNG riêng cho `delivery_cost`     → [ ] XÁC NHẬN KHÔNG  [ ] BÁC BỎ, phải trừ
  Đ2. Định nghĩa `OtherKpiAdjustment` (B-02)           → [ ] định nghĩa: ______  [ ] DESCOPE Phase 1
  Đ3. Xác nhận công thức V3 (có `− Discount`)          → [ ] XÁC NHẬN  [ ] chọn V1

GHI NHẬN — kể cả khi Đ1/Đ2/Đ3 đều được duyệt, TASK-108B vẫn còn hai dependency
DỮ LIỆU (không phải định nghĩa): Price Master (100% giá nhập đang Pending) và
confirmed KPI Adjustment persistence (TASK-202/302/305). Engine sẽ trả `None`
cho mọi dòng ở Phase 1. Nếu chủ dự án cần CON SỐ THẬT, thứ tự đúng là Price
Master TRƯỚC TASK-108B.

Sau Owner approval (Đ1 + Đ2 + Đ3):

TASK-108B
    OWNER_DEFINITION = APPROVED
    IMPLEMENTATION   = READY (cấu trúc; số thật chờ Price Master)
```

---

## STOP

Phiên này dừng tại đây. Không implementation. Không tự ghi DEC. Không mở
TASK-109. Không tạo repair cycle. Không sửa `app/**`, `config/**`, `tests/**`,
Golden, TASK-110, `CHECK-110-16`, `R1-A2`→`R8`.

---
---

# PHẦN II — CURRENT STATE POINTER (append 2026-08-27)

> **Phần I ở trên là bản ghi DISCOVERY, giữ nguyên không sửa.** Verdict
> `OWNER_DECISION_REQUIRED` của Phần I đã được thay thế bởi phần này. Nơi nào
> Phần I và Phần II mâu thuẫn, **Phần II thắng**.

## 19. Owner Decision đã được ghi

`OD-108B-01` được chủ dự án phê duyệt 2026-08-27 và ghi vào canonical decision
artifact với ID **`DEC-143`** (`PROJECT/PROJECT_DECISIONS.md`). ID cấp sau khi
quét namespace **toàn repo** (không chỉ một file — bài học va chạm `DEC-128`):
`DEC-143` … `DEC-159` xác nhận trống trước khi cấp.

```
EligibleCosts      = {}                      CLOSED EMPTY SET (không phải fallback = 0)
DeliveryCost       = NOT ELIGIBLE FOR NOW    (quyết định, không phải suy đoán)
OtherKpiAdjustment = 0 BY DEFINITION         (định nghĩa, không phải thiếu dữ liệu)
EligibleKpiProfit  = (SellPrice − KpiPurchasePrice) × Quantity − Discount
C15                = ĐÃ ĐÓNG
```

**Bốn khoảng trống semantic của Phần I đều đã đóng:** `EligibleCosts` (§5 U1),
`DeliveryCost` (§5 U2), `OtherKpiAdjustment` (§15 B-02), canonical formula
(§15 B-03).

### 19.1 CONFLICT DETECTED — chuẩn hoá số học của công thức

Văn bản `OD-108B-01` §4 viết dạng
`NormalizedSales − Discount − KpiPurchasePrice − SUM(EligibleCosts) + OtherKpiAdjustment`.
Đọc **nguyên văn** theo định nghĩa các thuật ngữ đang tồn tại trong repo thì
dạng này lệch ở hai điểm:

*Documentation:* `OD-108B-01` §4 trừ `Discount` **sau** `NormalizedSales`, và
trừ `KpiPurchasePrice` **không** nhân `Quantity`.

*Implementation:* `app/modules/importing/normalizer.py:27` —
`total_sales = sell_price * quantity − discount`. `NormalizedSales` **đã trừ
`Discount`**. Xác nhận trên dữ liệu production qua Golden:
`sales_raw_gross − sales_normalized` bằng **đúng** `discount_total` ở cả hai kỳ
(2.300.000 ở 01.2026; 400.000 ở 06.2026). Và `KpiPurchasePrice` là **đơn giá**
(`F: Giá nhập TT`, cùng chiều `SellPrice`/`G`) — workbook nhân số lượng:
`In = (Gn − Fn) * En`.

*Risk:* ví dụ có số — `SellPrice = 10.000`, `KpiPurchasePrice = 8.000`,
`Quantity = 3`, `Discount = 500`. Dạng canonical cho **5.500**; đọc nguyên văn
dạng prose cho **21.000** — sai khoảng **3,8 lần**, và `Discount` bị trừ hai lần.

*Recommended resolution:* dùng dạng canonical ở `DEC-143` Decision §4. Đây
**không** phải đoán ý — nó là cách đọc **duy nhất** thoả mãn đồng thời cả ba
điều `OD-108B-01` tự tuyên bố: (a) `Discount` **có** tham gia công thức (§4);
(b) **NO DOUBLE COUNT** khi khoản đó đã phản ánh trong `NormalizedSales` (§5);
(c) khớp authority có trước là DEC-122 và `docs/analysis/03_RULE_CLASSIFICATION.md` §U.

*Trạng thái:* đã báo cáo theo V4.1 §11 (Artifact Internal Precedence — phần quy
phạm thắng prose, nhưng divergence **phải được báo cáo**, không sửa im lặng).
**Cần chủ dự án xác nhận lại ở lần tương tác kế tiếp.** Không chặn việc ghi
quyết định, vì dạng canonical đã là authority có sẵn từ DEC-122.

## 20. DEPENDENCY READINESS CHECK

Tính lại từ trạng thái **MỚI** sau `OD-108B-01`, không mặc định vẫn còn bốn.

### DEPENDENCY 1 — `KpiPurchasePrice` / Price Master

| Câu hỏi | Trả lời | Bằng chứng |
|---|---|---|
| Source hiện tại ở đâu? | `PriceProvider` Protocol + `PendingPriceProvider` | `app/modules/pricing/provider.py` |
| Có dữ liệu production usable chưa? | **CHƯA.** `PendingPriceProvider.lookup()` trả `None` **vô điều kiện** | `provider.py` — thân hàm đúng một dòng `return None` |
| Bao nhiêu path trả Pending? | **100 %, theo cấu trúc chứ không theo dữ liệu.** Golden production: `price_source_distribution = {Pending: 351}` (01.2026), `{Pending: 180}` (06.2026); `accounting_profit_pending = 351/351` | `tests/fixtures/golden/expected/*.json` |
| Có persistence chưa? | **CHƯA.** Phase 1 là thư viện Python thuần, cấm import `sqlalchemy`/`fastapi` | ADR-101 §62–63, §119 |
| Có effective dating chưa? | **Interface đã có** (`lookup(product_code, sale_date)`), **dữ liệu chưa có** | `provider.py` |
| Thuộc task/phase nào? | `TASK-401` — **PHASE-04** | `PROJECT_PROGRESS.md:414` |
| Task nào phải xong để mở? | Xem §21 — **không nhất thiết phải chờ Phase 4** | đặc tả §10 dòng 212 |

**Đây là blocker cứng.** `KpiPurchasePrice = AccountingPurchasePrice +
KpiPurchaseAdjustment`; vế `AccountingPurchasePrice` là `None` trên **mọi** dòng,
và DEC-103 cấm suy đoán hay coi `0`. Nên `EligibleKpiProfit` sẽ là `None` trên
mọi dòng, và `ConvertedRevenue` cũng vậy. `TASK-108B` implement được **cấu
trúc**, nhưng **không tạo ra một con số nghiệp vụ nào**.

⚠️ **Nghịch lý roadmap:** `TASK-108B` ở **PHASE-01** nhưng dependency dữ liệu
của nó (`TASK-401`) ở **PHASE-04**. Theo thứ tự roadmap hiện tại, `TASK-108B`
không bao giờ chạy được đúng ở Phase 1. Xem §21 để biết đường thoát hợp lệ.

### DEPENDENCY 2 — confirmed KPI Adjustment persistence

| Câu hỏi | Trả lời | Bằng chứng |
|---|---|---|
| Authority hiện tại | DEC-125 (4 quy tắc nghiệp vụ), DEC-126 §3–6 (ranh giới) | `PROJECT/PROJECT_DECISIONS.md` |
| Source | **Nhập tay sau import** — không có cột nào trong 17 cột raw | DEC-125 điểm 4; `docs/analysis/01_DATA_MAPPING.md` |
| Persistence | **KHÔNG CÓ.** `WorkingLine` không có field `kpi_purchase_adjustment` lẫn `kpi_purchase_price`; `AdjustmentResolver` cố ý **không** nối vào `run_import()` | `app/modules/domain/models.py`; `adjustment_resolver.py` docstring |
| Lifecycle | `suggested_amount` (resolver) → `final_amount` (người xác nhận). Chỉ `final_amount` được vào công thức KPI | DEC-126 §4–5 |
| Effective dating | Yêu cầu bởi đặc tả §11 dòng 217; **chưa implement** | đặc tả |
| Task/phase sở hữu | `TASK-202` / `TASK-302` / `TASK-305` — **PHASE-02/03** | `PROJECT_PROGRESS.md:368, 393, 405` |

**Có còn BLOCK sau khi `OtherKpiAdjustment = 0` không? — CÓ, vẫn block.**

Đây là điểm dễ nhầm nhất, nên nói thẳng: `OD-108B-01` §3 định nghĩa
**`OtherKpiAdjustment`** = 0. Đó là **một số hạng khác** với
**`KpiPurchaseAdjustment`**:

```
KpiPurchaseAdjustment  → đi vào KpiPurchasePrice  (F = L + J; cột J "Giao hàng":
                          Qua kho / NCC giao / KHBH / Thợ lắp)   ← VẪN CHƯA CÓ
OtherKpiAdjustment     → số hạng cộng cuối công thức             ← ĐÃ = 0 (OD-108B-01)
```

`OD-108B-01` **không** nói gì về `KpiPurchaseAdjustment`, và DEC-126 §6 cấm mặc
định adjustment chưa xác định bằng `0`: *"thiếu dữ liệu adjustment nghĩa là
`EligibleKpiProfit` chưa tính được cho dòng đó (Pending)"*. Bằng chứng quy mô:
**635/18.148 dòng** của workbook có cột `L` nhập tay thay vì `=F` — tức có
adjustment thật; không có cơ chế nào để biết dòng nào thuộc nhóm đó nếu thiếu
tầng xác nhận.

**Mức độ độc lập:** Dependency 2 là blocker **thật và độc lập**, nhưng nó
**bị che** bởi Dependency 1 — kể cả khi có đủ adjustment persistence,
`accounting_purchase_price = None` vẫn làm `KpiPurchasePrice = None`. Nên thứ
tự giải phải là **Dependency 1 trước**.

### Blocker count: 4 → 2

| # | Blocker (Phần I §15 B-01) | Trạng thái sau `OD-108B-01` |
|---|---|---|
| 1 | `EligibleCosts` (C15) | ✅ **ĐÓNG** — `DEC-143` §1–2 |
| 2 | `OtherKpiAdjustment` | ✅ **ĐÓNG** — `DEC-143` §3 |
| 3 | `AccountingPurchasePrice` / Price Master | 🔴 **CÒN** — dependency dữ liệu |
| 4 | confirmed `KpiPurchaseAdjustment` persistence | 🔴 **CÒN** — dependency cơ chế |
| + | conflict công thức (B-03) | ✅ **ĐÓNG** — `DEC-143` §4 (kèm §19.1 cần xác nhận) |

**Cả hai blocker còn lại đều là DỮ LIỆU/CƠ CHẾ, không phải SEMANTIC.**

## 21. NEXT PRODUCT TASK đề xuất để giải blocker

**`TASK-105B` — `FilePriceProvider` (MICRO/MAJOR, Phase 1).**

*Nội dung:* một implementation thứ hai của `PriceProvider` Protocol đã có sẵn,
đọc bảng giá nhập từ file do chủ dự án cấp (CSV/YAML: `product_key`,
`effective_from`, `effective_to`, `purchase_price`, `source`). Không UI, không
DB.

*Vì sao hợp lệ ở Phase 1, không phải chờ `TASK-401`/Phase 4:*

1. **Đặc tả cho phép tường minh.** §10 dòng 212: *"Version đầu cho phép nhập
   tay; version sau có Price Master theo ProductCode + EffectiveDate."* Bảng giá
   dạng file **chính là** "nhập tay" của version đầu.
2. **Seam đã tồn tại và được thiết kế đúng cho việc này.** `provider.py`
   docstring (DEC-103): *"an interface is defined now so an external Price
   Master can be plugged in later … without touching `price_engine` or
   `app.pipeline`"*. Chi phí sửa `price_engine.py` / `pipeline.py` = **0**.
3. **Không phá Golden.** Không thêm field vào `WorkingLine` ⇒ `lines_digest` và
   `_covered_digest_fields` không đổi; chữ ký `run_import` không đổi
   (`test_golden_pipeline_entry_point_signature_is_locked` vẫn PASS). Golden
   mặc định vẫn chạy với `PendingPriceProvider`.
4. **Không vi phạm ADR-101.** Python thuần, không `sqlalchemy`, không `fastapi`.
5. **Không vi phạm DEC-103.** Giá tra được là *đề xuất*, luôn override được;
   key không khớp vẫn là `Pending`, **không** suy đoán.

*Việc duy nhất chủ dự án cần làm:* cấp một file danh sách **mã hàng / ngày /
giá nhập**. Không cần chờ Phase 4.

**Blocker 2 — hai đường, chủ dự án chọn:**

- **(A)** Owner Decision tuyên bố: ở Phase 1, khi **không có** adjustment record
  nào cho một dòng thì `KpiPurchasePrice = AccountingPurchasePrice` với
  provenance `Config:NoAdjustment`. Đây là **tuyên bố tập rỗng** cùng dạng
  `OD-108B-01` §1 — hợp lệ, và khác hẳn "mặc định 0 vì thiếu dữ liệu" mà
  DEC-126 §6 cấm. Rẻ nhất, mở khoá `TASK-108B` ngay sau `TASK-105B`.
- **(B)** Chờ `TASK-202`/`TASK-302`/`TASK-305` (Phase 2/3) xây tầng override
  thật. Đúng bài bản, nhưng đẩy `TASK-108B` ra sau `GATE-01`.

**Agent không tự chọn (A).** Đó là thẩm quyền Owner, đúng như `OD-108B-01` §1
đã thiết lập tiền lệ.

*Thứ tự đề xuất:* `TASK-105B` → Owner Decision (A hoặc B) → `TASK-108B` →
`TASK-109`.

## 22. Golden coverage implication

Không đổi so với Phần I §7: **không hạ Blast Radius** (V4.1 §4.1). Coverage gap
được **báo cáo**, Golden **không** bị sửa trong phiên này.

Gap cần bổ sung khi implementation thật bắt đầu (task riêng, cần Owner cấp dữ
liệu): một kỳ có nhân viên `PERSONAL` thật (Ly hoặc Thắng) và một kỳ kênh
`NOI_THANH` — hai path chiếm phần lớn rủi ro và hiện phủ **0 %**.

Nhắc lại cảnh báo kỹ thuật của Phần I §7: khi `TASK-108B` thêm field vào
`WorkingLine`, `lines_digest` **và** `_covered_digest_fields` sẽ đổi ⇒ Golden
**ĐỎ theo thiết kế**. Xử lý đúng = sinh lại expected tường minh kèm Owner
Decision, **không** sửa test cho xanh (`CHECK-108B-11`, Evidence Level `E2`).

## 23. Readiness verdict (thay thế §18 của Phần I)

```
TASK-108B
    SEMANTIC_DEFINITION   = APPROVED
    IMPLEMENTATION        = BLOCKED_BY_DEPENDENCY
    BLOCKERS              = [ AccountingPurchasePrice / Price Master,
                              confirmed KpiPurchaseAdjustment persistence ]
    NEXT PRODUCT TASK     = TASK-105B (FilePriceProvider)
                            + Owner Decision cho KpiPurchaseAdjustment (A hoặc B)
```

**Không** ghi `IMPLEMENTATION_READY`. Không hardcode dữ liệu để vượt blocker,
không synthetic PASS, không mở `TASK-109`.

## STOP (Phần II)

Không implementation. Không sửa `app/**`, `config/**`, `tests/**`, Golden
fixture/expected. Không mở `TASK-109`, `TASK-110`, `CHECK-110-16`,
`R1-A2`→`R8`. Không tạo repair cycle. Không mở Independent Review. Không xoá
artifact cũ.
