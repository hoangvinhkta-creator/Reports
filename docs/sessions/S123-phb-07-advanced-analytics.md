# S123 — PHB-07: Advanced Analytics (Cơ Cấu Doanh Thu Theo Đơn Vị Báo Cáo)

Mode: BOUNDED VERTICAL — một nhánh, một `BASE_HEAD`, không merge canonical,
không deploy.

Không mở lại vertical đã đóng · không migration mới · không thẩm quyền ghi
mới · không thẩm quyền Product Identity mới · không Target mới · không đổi
điều hướng chính · không đổi PHB-06 · không công thức nghiệp vụ mới.

## 0. Exact Gate

```text
SOURCE_BRANCH         = claude/phb-06-brand-reporting-0i2oun
EXPECTED_SOURCE_HEAD  = d0edb0937476be81991687e0b7c1d64e30a41592
OBSERVED HEAD         = d0edb0937476be81991687e0b7c1d64e30a41592  → KHỚP
ANCESTOR CHECK        = 0d9d93111c7955fa407e5b43ebee682e5c728c56 là tổ tiên
                        của HEAD → ĐÚNG (`git merge-base --is-ancestor`)
CANONICAL_BRANCH      = claude/extract-upload-repo-gq2ws4
                        (origin HEAD = 0d9d931…, tức FINAL_REVIEW_BASE)
WORKTREE              = sạch
GATE                  = PASS
```

PHB-07 được triển khai CHỒNG LÊN đúng head của PHB-06 theo chỉ thị: cả hai
vertical sẽ đi qua MỘT lần Independent Review tích luỹ trên dải
`0d9d931… → FINAL_HEAD`.

## 1. Audit thẩm quyền — "Advanced Analytics" nghĩa là gì trong repo này

Kết quả đo trước tiên, vì nó quyết định toàn bộ phạm vi:

```text
Chuỗi "PHB-07"            xuất hiện 0 lần trong toàn repo
Chuỗi "Advanced Analytics" xuất hiện 8 lần — TẤT CẢ đều trong danh sách
                           "cố ý KHÔNG làm" của các vertical trước
                           (PHB-03 §11 · PHB-04 §7 · S116 · bốn review)
⟹ KHÔNG có một đặc tả PHB-07 nào tồn tại.
```

Nguồn phân loại phân tích DUY NHẤT của repo là
`docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md` §L
(`ANALYTICS OPPORTUNITIES — NOW / LATER / DEFER`, roadmap FROZEN ở §F5), bổ
sung bằng §C.1–C.2 (hình dạng sổ cũ) và các freeze sau nó (`PHB-02` §11,
`PHB-04` §3.6, `TASK-PRA-005` §17/§19/§26/§27, `DEC-180`, `DEC-185`).

### 1.1 Ma trận thẩm quyền

| Capability | Source | Business question | Formula / semantic authority | Current support | Legacy support | Safe to implement | Owner decision required |
|---|---|---|---|---|---|---|---|
| Doanh thu theo kỳ / nhân viên / kênh | PRA-000 §L `NOW` | Ai bán được bao nhiêu? | `DEC-114` · `business_metrics.totals` | **ĐÃ CÓ** (`/kinh-doanh`, sheets) | Summary cột "Tổng bán" | — đã có | KHÔNG |
| Số đơn | PRA-000 §L `NOW` | Bao nhiêu đơn? | `M1` `COUNT DISTINCT order_key` | **ĐÃ CÓ** | `count Trans` | — đã có | KHÔNG |
| Tổng số SP | PRA-000 §L `NOW` | Bao nhiêu SP đủ điều kiện? | `DEC-PHB02-03` | **ĐÃ CÓ** | Summary (có lỗi `A1`) | — đã có | KHÔNG |
| Lợi nhuận KPI + coverage | PRA-000 §L `NOW` | Lãi bao nhiêu, đã chắc chưa? | `DEC-143` + `DEC-PHB02-02` §4 | **ĐÃ CÓ** | Summary "Tổng lợi nhuận" | — đã có | KHÔNG |
| So tháng trước | PRA-000 §L `NOW` | Tháng này hơn/kém tháng trước? | `DEC-PHB02-07` | **ĐÃ CÓ** | Summary "Vs. Tháng trước" | — đã có | KHÔNG |
| Target attainment + tiến độ tháng | PRA-000 §L `NOW` | Đã đạt bao nhiêu phần target? | `DEC-PHB02-06` · PHB-05 · `§15` | **ĐÃ CÓ** | Summary "Target"/"Vs.Target" | — đã có | KHÔNG |
| **Tỉ trọng đóng góp (contribution share)** | **PRA-000 §L `NOW`** — *"Employee contribution (share) · doanh thu NV / tổng"* | **Doanh thu kỳ này đến từ đâu, mỗi đơn vị chiếm bao nhiêu %?** | Phép chia hai con số ĐÃ CÓ; phân hoạch = `DEC-PHB02-08` §42 | **CHƯA CÓ** | Khối tháng Summary = 5–7 dòng người bán/kênh + dòng tổng (§C.1) | **CÓ — ĐÃ CHỌN** | KHÔNG |
| Review burden theo nhóm lý do | PRA-000 §L `NOW` (slice 4) | Còn vướng gì, bao nhiêu dòng? | `profit_gate.PROFIT_BLOCKERS` · `Coverage.blocked_lines` | **ĐÃ CÓ** (khối coverage) | — | — đã có | KHÔNG |
| Source-data revisions | PRA-000 §L `NOW` (slice 2) | Sổ nạp đổi gì? | reconciler PRA-002 | **ĐÃ CÓ** (`/du-lieu`) | — | — đã có | KHÔNG |
| Đối chiếu legacy ↔ pipeline | PRA-000 §L `NOW-lite` | Số cũ và số mới lệch bao nhiêu? | **ĐÃ ĐÓNG**: `PHB-04` §3.6 — `COMPARABLE = KHÔNG CÓ CHỈ TIÊU NÀO`, mọi cặp bị chặn kèm lý do | Cổng `compare()` chặn | Có số | **KHÔNG** — mở lại một freeze | CÓ (mở lại `PHB-04` §3.6) |
| Tỉ suất lợi nhuận (margin) | PRA-000 §L `LATER` (N.7) | Lãi trên doanh thu bao nhiêu %? | **CHƯA CÓ**: `PHB-02` §11 `DEFER D1`; mẫu số chưa chốt | KHÔNG | Summary cột H `=G/E`, 86/86 ô có số | **KHÔNG** | **CÓ — xem §4 lựa chọn A** |
| Doanh thu bình quân/đơn | PRA-000 §L `LATER` | — | — | KHÔNG | Không có trong sổ cũ | **KHÔNG** — §L ghi *"chưa có nhu cầu trong Excel cũ"* | KHÔNG (chưa có nhu cầu) |
| Cùng kỳ năm trước · YTD | PRA-000 §L `LATER` | Năm nay so năm ngoái? | Chặn bởi `PHB-04` §3.6 + `DEC-180` §9 | KHÔNG | `Summary 2025` + `DataChart` | **KHÔNG** | CÓ |
| Sales mix kênh × nhóm hàng | PRA-000 §L `LATER` | Kênh nào bán nhóm hàng nào? | `reporting_sheets.sheet_key_of` | **ĐÃ CÓ** — sheet Nội thành/Gia dụng CHÍNH LÀ kênh × nhóm hàng | Sheet `MM.2026 Nội thành`/`Gia dụng` | — đã có | KHÔNG |
| Cơ cấu theo SẢN PHẨM (top N, Pareto) | PRA-000 §L `LATER` (slice 5) | Mặt hàng nào gánh kỳ này? | Xung đột: `OD-PRA005-01` chọn gộp theo `product_key` (tên trên chứng từ); §L đòi canonical identity | `/san-pham` có, nhưng đọc sổ thô và gộp theo tên | Không có | **KHÔNG** | **CÓ — xem §4 lựa chọn B** |
| Xu hướng nhân viên nhiều tháng | PRA-000 §L `LATER` (cần ≥3 tháng) | Người này đang lên hay xuống? | Chặn bởi `DEC-180` §9 + `PHB-04` §3.6 | KHÔNG | Ma trận `Summary` 8 tháng (chỉ đọc, `/nhan-vien` SỐ CŨ) | **KHÔNG** | **CÓ — xem §4 lựa chọn C** |
| Ranking · scoring · "bán chậm" · nhãn top/best | `TASK-PRA-005` §17 + S105 §27 | — | **CẤM**: mọi nhãn kiểu đó cần một công thức và một quyết định Owner chưa tồn tại | KHÔNG | Không có | **KHÔNG** | CÓ |
| Thương hiệu | `DEC-186` / PHB-06 | Thương hiệu nào bán chạy? | `BRAND_AUTHORITY = PRODUCT_IDENTITY_CANONICAL`, hôm nay trả `None` cho MỌI dòng | Trang đã ship, số chưa có nguồn | Không có cột thương hiệu | — PHB-06 đã ship phần làm được | CÓ (đã nêu ở `S117` §4) |
| Tỉ lệ tồn kho (Kho/NCC) | PRA-000 §L `DEFER` | — | Nguồn `Nơi nhập` KHÔNG tồn tại trong ERP | KHÔNG | Summary có số, ngữ nghĩa không chắc | **KHÔNG** | KHÔNG (thiếu nguồn) |
| Lương · thưởng · ngày công | PRA-000 §L `DEFER` (N.9) | — | Ngoài spec KPI của Reports | KHÔNG | Summary cột O–S | **KHÔNG** | KHÔNG (ngoài phạm vi) |
| Anomaly · forecast · gợi ý · confidence | PRA-000 §L `DEFER` + chỉ thị §16 | — | Không có yêu cầu đã freeze nào | KHÔNG | Không có | **KHÔNG** | KHÔNG |
| Dashboard realtime hôm nay/tuần | PRA-000 §L `DEFER` | — | Nguồn theo lô, không realtime | KHÔNG | Không có | **KHÔNG** | KHÔNG |

### 1.2 Kết luận của audit

```text
PHB07_SELECTED_CAPABILITIES = 1
  C1 — Tỉ trọng đóng góp doanh thu theo ĐƠN VỊ BÁO CÁO (cơ cấu doanh thu)

PHB07_REJECTED_AS_UNSUPPORTED = 12
  tỉ suất lợi nhuận (margin) · cơ cấu theo sản phẩm / top-N / Pareto ·
  xu hướng nhiều tháng · cùng kỳ năm trước / YTD · đối chiếu legacy↔pipeline ·
  doanh thu bình quân mỗi đơn · ranking/scoring/nhãn "bán chạy" ·
  tỉ lệ tồn kho · lương/thưởng · anomaly/forecast/gợi ý ·
  dashboard realtime · phân tích thương hiệu sâu hơn PHB-06
```

Đúng MỘT chỉ tiêu được xếp `NOW` trong bảng phân loại đã freeze mà chưa có
mặt trên kết quả nghiệp vụ chính thức. Vertical này ship đúng một chỉ tiêu
đó, không hơn.

## 2. Điều đã ship

```text
ROUTE            = GET /kinh-doanh/co-cau (khung nhìn CON của Báo cáo, CHỈ ĐỌC)
PRIMARY_NAV      = KHÔNG ĐỔI — vẫn đúng ba mục (`DEC-185`)
PARTITION        = reporting_sheets.sheet_key_of (`DEC-PHB02-08` §42) đọc lại
                   qua PeriodData.sheet_assignments() — KHÔNG phân loại mới
METRICS          = Đơn · Tổng số SP · Doanh thu · Lợi nhuận KPI (gated) ·
                   DS quy đổi · Coverage — ĐÚNG bộ chỉ tiêu đã có
NEW_METRIC       = Tỉ trọng doanh thu = doanh thu đơn vị / doanh thu kỳ
NEW_MODULE       = app/modules/reporting/contribution.py (THUẦN)
RECONCILIATION   = brand_metrics.reconciliation dùng lại NGUYÊN VẸN (không
                   viết bản thứ hai), chạy THẬT ở mỗi lần tải trang
PERIOD           = _workspace_period() — tháng dương lịch hiện tại, không có
                   mục "Toàn bộ dữ liệu", không khung lọc mới
NEW_MIGRATION    = NONE · NEW_WRITE_AUTHORITY = NONE · NEW_PII = NONE
```

Mẫu số của mọi ô tỉ trọng (doanh thu bán hàng của kỳ) hiện ngay trên bảng:
một cột phần trăm mà người đọc không biết chia cho cái gì là một cột không
kiểm lại được.

## 3. Vì sao ĐƠN VỊ BÁO CÁO chứ không phải từng nhân viên

`TASK-PRA-000` §L viết chỉ tiêu là *"doanh thu NV / tổng"*. PHB-07 áp nó ở
độ mịn ĐƠN VỊ BÁO CÁO, và đó là một lựa chọn có căn cứ chứ không phải một
lần trượt phạm vi:

1. `DEC-PHB02-08` freeze rằng đơn vị báo cáo KHÁC con người. Nội thành có
   Target của RIÊNG nó (`group_target`), và sổ cũ cũng để Nội thành làm MỘT
   dòng (§C.1: *"5–7 dòng người bán/kênh"*).
2. Đặt cả dòng "Nội thành" LẪN ba dòng nhân viên của nhóm vào cùng một bảng
   là ĐẾM HAI LẦN cùng một số tiền — đúng điều chỉ thị §13 cấm. Chỉ có MỘT
   phân hoạch trong mã, nên lỗi đó không có chỗ để xảy ra.
3. Cột Nhân viên của bảng kê KHÔNG đổi: người bán vẫn được ghi đúng tên ở
   nơi nó là câu trả lời đúng (`DEC-127` §1 giữ nguyên).

Trang nói ra điều này bằng chữ, ngay trên bảng, để không ai đi tìm dòng của
một nhân viên Nội thành rồi kết luận rằng bảng thiếu.

## 4. OWNER_DECISION_REQUIRED — lát cắt phân tích tiếp theo

PHB-07 KHÔNG bị chặn bởi quyết định nào: phần không mơ hồ đã ship. Ba lựa
chọn dưới đây là toàn bộ những gì bằng chứng trong repo còn cho phép làm
tiếp, và MỖI lựa chọn đều vướng đúng một quyết định của chủ dự án.

**A (KHUYẾN NGHỊ) — Tỉ suất lợi nhuận (margin).**
Sổ cũ có cột H `=G/E` với 86/86 ô có số (`PHB-04` §8c). `PHB-02` §11 đang
`DEFER D1` và `TASK-PRA-000` N.7 hỏi đúng một câu: mẫu số là **lợi nhuận KPI
/ doanh thu bán hàng** hay **lợi nhuận kế toán / doanh thu**? Đây là lựa chọn
rẻ nhất: một câu trả lời của Owner mở khoá một chỉ tiêu mà sổ cũ đã dùng suốt
tám tháng. Khuyến nghị: LN KPI / doanh thu bán hàng, và ô chỉ CHÍNH THỨC khi
coverage đạt 100 % (đúng cổng `R-S7` đang chạy).

**B — Cơ cấu theo SẢN PHẨM trên kết quả nghiệp vụ chính thức.**
`TASK-PRA-000` §L đòi gộp theo **canonical identity, chỉ dòng đã resolve, và
phải hiện coverage identity**; `OD-PRA005-01` lại đã chọn gộp theo **tên hàng
trên chứng từ** cho trang `/san-pham` (đọc sổ thô). Hai khoá gộp khác nhau
trên cùng một khái niệm "sản phẩm" là hai bảng nói hai con số. Owner cần
quyết: khoá gộp nào là chính thống, và `/san-pham` cũ có bị thay thế không.
Khuôn dựng đã sẵn (`PHB-06` đã chứng minh phân hoạch theo Product Identity
với bucket "chưa xác định" cộng lại đúng bằng tổng kỳ).

**C — Ma trận ĐƠN VỊ BÁO CÁO × THÁNG (nhiều tháng).**
`TASK-PRA-000` §C.2 xếp *"ma trận Nhân viên × Tháng"* là giá trị quản lý cốt
lõi số một của sổ cũ; §L xếp nó `LATER` và cần ≥3 tháng dữ liệu pipeline.
Vướng mắc thật nằm ở chỗ khác: `DEC-180` §9 (một kỳ ⟹ một nguồn) và `PHB-04`
§3.6 (mọi cặp cũ↔mới bị chặn) khiến một ma trận trải dài qua ranh giới bàn
giao không được phép cộng chung. Owner cần quyết: ma trận CHỈ gồm các tháng
có sổ nạp, hay hiện thêm các tháng số cũ ở một khối tách bạch chỉ-đọc.

## 5. Findings

| Mã | Nội dung | Mức |
|---|---|---|
| `FIND-PHB07-01` | Không có đặc tả PHB-07 nào trong repo. "Advanced Analytics" chỉ xuất hiện trong các danh sách "cố ý KHÔNG làm". Vertical được định phạm vi bằng bảng phân loại đã freeze `TASK-PRA-000` §L thay vì bằng suy đoán; điều đó được ghi ra để lần sau không ai phải đoán lại. | `NON_BLOCKING` |
| `FIND-PHB07-02` | Đúng MỘT chỉ tiêu `NOW` còn thiếu ⟹ vertical này nhỏ theo bằng chứng, không theo ngân sách. Mọi chỉ tiêu còn lại đều `LATER`/`DEFER` hoặc đã bị một freeze đóng lại. | `NON_BLOCKING` |
| `FIND-PHB07-03` | `reference_integrity` FAIL với đúng 3 lỗi CÓ SẴN trên `BASE_HEAD` — cả ba đều xuất phát từ task REM-T06 và trỏ tới ba file quy ước cộng đồng chưa từng tồn tại ở gốc repo. Chạy validator trên `BASE_HEAD` cho ra CÙNG ba lỗi đó, nên chúng không do PHB-06 cũng không do PHB-07 gây ra; trùng `FIND-PHB06-03`/`F-05`. Bản ghi này cố ý KHÔNG viết lại ba đường dẫn hỏng: viết ra sẽ tạo thêm ba reference hỏng mới trong chính file này. | `NON_BLOCKING` |
| `FIND-PHB07-04` | Hai khoá gộp "sản phẩm" cùng tồn tại trong repo (§4 lựa chọn B). Chưa gây sai số nào hôm nay vì PHB-07 không đụng tới sản phẩm, nhưng nó là mâu thuẫn phải giải trước lát cắt sản phẩm tiếp theo. | `NON_BLOCKING` |

Không finding nào được biến thành task mới (chỉ thị §27).

## 6. Bằng chứng thực thi (E1)

```text
FOCUSED   tests/test_phb07_advanced_analytics.py   → 54 passed
PHB-06    tests/test_phb06_brand_reporting.py      → 42 passed (không đổi)
REGRESSION  PHB-03/04/05 · workspace UX · DEC-185 · business vertical ·
            business metrics · business boundaries · golden baseline ·
            DEC-180 · R2/timeline · journal ghi có điều kiện ·
            governance task-completion validator
                                                   → 597 passed, 2 skipped
GOLDEN    tests/test_golden_baseline.py            → 58 passed, 2 skipped
                                                     (khớp Golden Baseline
                                                      đã freeze)
FULL_SUITE  BASE_HEAD  d0edb09 → 2630 passed, 11 skipped
            FINAL_HEAD         → 2684 passed, 11 skipped
            chênh lệch +54 = ĐÚNG số test mới, không test nào cũ bị đổi

GOVERNANCE  validate_structure          → PASS
            validate_project_state      → PASS
            validate_evidence           → PASS (155 bản ghi)
            validate_reference_integrity→ FAIL (3 lỗi CÓ SẴN trên BASE_HEAD,
                                          xem `FIND-PHB07-03`)

MUTATION_PROBES  M1…M10 = 10/10 BITE
  M1  gộp trên sổ THÔ thay vì kết quả chính thức        → đối soát ĐỎ
  M2  dòng đã loại được cộng trở lại                    → đối soát ĐỎ
  M3  thiếu giá nhập thành lợi nhuận 0                  → đối soát ĐỎ
  M4  bỏ đơn vị "chưa xác định nhân viên"               → đối soát ĐỎ
  M5  một dòng nằm ở hai đơn vị                         → đối soát ĐỎ
  M6  thêm một công thức nghiệp vụ vào tầng cơ cấu      → quét thẩm quyền ĐỎ
  M7  thêm mục điều hướng chính thứ tư                  → test điều hướng ĐỎ
  M8  thêm một bảng lưu kết quả phân tích               → test phạm vi ĐỎ
  M9  tỉ trọng chia cho riêng phần đã xác định          → tổng vượt 100 %
  M10 tách Nội thành thành ba người rồi giữ cả hai      → đối soát ĐỎ
```

## 7. Bàn giao

Nhánh này mang CẢ HAI vertical (PHB-06 + PHB-07). Hành động tiếp theo là MỘT
lần Independent Review tích luỹ trên dải `0d9d931… → FINAL_HEAD`, review cả
hai. Không merge canonical, không deploy.
