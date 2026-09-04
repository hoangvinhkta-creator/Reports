# TIẾN ĐỘ DỰ ÁN

## CANONICAL CURRENT STATE — PHB-03 = PRODUCTION_VERIFICATION_INCOMPLETE (AUTHORITATIVE, 2026-09-04, S118)

`PHB-03` đã qua **Controlled Integration** vào nhánh canonical và **sẵn sàng
deploy**, nhưng **CHƯA `DONE`**: toàn bộ cửa E2E production yêu cầu tác nhân
Owner (phiên KHÔNG có egress tới `reports.tinphatcrm.com`/`api.render.com` —
đúng lớp policy denial đã ghi ở `S093`/`S110`/`S112`). Báo cáo đầy đủ cho Owner:
`docs/reviews/PHB-03-production-verification-e2e.md`.

Bằng chứng review/audit nay nằm trên canonical (docs-only, gom từ các nhánh
khác): `docs/reviews/PHB-03-bounded-semantics-independent-re-review.md` ·
`docs/reviews/PHB-03-import-lifecycle-persistence-audit.md` ·
`docs/reviews/PHB-03-pending-reason-business-classification.md`.

```text
TARGET_GATE                = PASS (HEAD = d066d227da852b17a57d4a8492fa79c7fc7b2aff,
                             worktree CLEAN)
CANDIDATE_SHA              = d066d227da852b17a57d4a8492fa79c7fc7b2aff
CANDIDATE_UNCHANGED        = PASS — diff mã chạy = 0 so với nhánh re-review
                             (5bdd838) và nhánh audit (c02d42a)

PRODUCTION_BEFORE_SHA      = NOT_OBSERVABLE_FROM_SESSION. Bản Owner nghiệm thu
                             gần nhất = 1a011ee (S111); canonical trước phiên =
                             eaa3fde; diff mã chạy 1a011ee↔eaa3fde = 0 (ba commit
                             ở giữa docs-only) ⟹ production đang chạy nội dung
                             tương đương eaa3fde.
ROLLBACK_SHA               = eaa3fdeb4ffdfd2d5772314ac24cf8a1273cc67e
PRODUCTION_DEPLOYED_SHA    = NOT_DEPLOYED_BY_SESSION

CANONICAL_INTEGRATION      = DONE — fast-forward từ eaa3fde (không force ·
                             không rewrite · không squash · không merge commit)
DEPLOY_THIS_COMMIT         = commit MỚI NHẤT trên canonical. INVARIANT: mọi
                             commit từ d066d22 trở về sau có mã chạy IDENTICAL
                             với candidate đã duyệt — phần thêm chỉ là docs.
                             Owner không phải dò SHA.
PRODUCTION_CODE_DELTA      = 0 — app/ tools/ config/ Dockerfile render.yaml
                             alembic.ini pyproject.toml identical với d066d22;
                             phần thêm CHỈ là docs (§6 giữ nguyên)

FULL_TESTS                 = PASS — 2136 passed, 11 skipped (88.87s) — KHỚP baseline
GOLDEN_TESTS               = PASS — 74 passed, 2 skipped — KHỚP baseline
PRODUCTION_PATH_TESTS      = PASS — 101 passed — KHỚP baseline
MIGRATION_ROLLBACK_SAFETY  = PASS — 3 passed (round-trip qua alembic thật)

ALEMBIC_CHAIN              = 0001 → 0002 → 0003 → 0004 (một head duy nhất)
PRODUCTION_DB_CURRENT      = 0002_snapshots (canonical eaa3fde chỉ có 0001+0002)
MIGRATION_REQUIRED         = HAI bước: 0003_business + 0004_employee_attribution.
                             Chỉ thị PHB-03 chỉ nêu 0004 — 0003 cũng thuộc PHB-03
                             và cũng chưa có trên production. Ghi lại cho đúng.
MIGRATION_DRY_RUN          = PASS — 0002_snapshots → 0004_employee_attribution:
                             11 bảng → 14 bảng · DROPPED [] · ALTERED [] ·
                             ADDED [kpi_purchase_price_override,
                             product_group_classification,
                             employee_attribution_override]
MIGRATION (production)     = NOT_RUN — chạy tự động lúc container khởi động
                             (Dockerfile CMD `alembic upgrade head && gunicorn`),
                             fail-closed: migrate hỏng ⟹ service KHÔNG lên
APP_BOOT_SMOKE             = PASS (cục bộ, trên DB đã migrate) — / · /kinh-doanh ·
                             /kinh-doanh/gia-nhap · /kinh-doanh/nhan-vien ·
                             /du-lieu → 200; /kinh-doanh/gia-dung → 404 ĐÚNG
                             THIẾT KẾ (chưa chọn nhân viên Nội thành)

PRODUCTION_FINGERPRINT     = NOT_VERIFIABLE_FROM_SESSION
FINGERPRINT_MECHANISM      = thẻ nav "Kinh doanh" trong layout.html — VẮNG ở
                             eaa3fde, CÓ ở d066d22. Owner kiểm bằng mắt, không
                             cần dev tools. KHÔNG chấp nhận "Render báo Live"
                             làm bằng chứng.

E2E1_PRICE_COVERAGE        = NOT_EXECUTED_NO_SESSION_EGRESS
E2E2_MANUAL_PP             = NOT_EXECUTED_NO_SESSION_EGRESS (và KHÔNG được đoán
                             giá vốn kể cả khi có egress)
E2E2B_CUMULATIVE_REUPLOAD  = NOT_APPLICABLE_NO_SAFE_REAL_CASE — chấp nhận bằng
                             chứng cấu trúc của import lifecycle audit
                             (OWNER_PRICE PRESERVED · MANUAL_PROVENANCE PRESERVED ·
                             PROFIT CORRECT · NO_DUPLICATE_REVENUE YES)
E2E3_UNKNOWN_EMPLOYEE      = NOT_EXECUTED_NO_SESSION_EGRESS
E2E4_QUANTITY_ZERO         = NOT_EXECUTED_NO_SESSION_EGRESS
E2E5_NEGATIVE_QUANTITY     = NOT_EXECUTED_NO_SESSION_EGRESS
E2E_CROSS_MONTH            = NOT_EXECUTED_NO_SESSION_EGRESS (audit: CROSS_MONTH_MOM
                             = PASS)
LATEST_SNAPSHOT_NOT_SEEN       = NOT_MEASURED (chưa có upload thật)
LATEST_SNAPSHOT_SOURCE_CHANGED = NOT_MEASURED
UNEXPLAINED_NOT_SEEN           = NOT_MEASURED
OWNER_DATA_PRESERVED       = NOT_VERIFIED_ON_PRODUCTION — nhưng migration
                             ADDITIVE thuần (0 drop · 0 alter) ⟹ không có đường
                             cơ chế nào làm mất dữ liệu Owner sẵn có

EGRESS_EVIDENCE            = reports.tinphatcrm.com:443 → CONNECT tunnel failed,
                             response 403 · api.render.com:443 ·
                             dashboard.render.com:443 · price.tinphatcrm.com:443
                             → không kết nối được

GOVERNANCE_VALIDATORS      = validate_structure PASS · validate_project_state PASS ·
                             validate_evidence PASS (155 REQUIRED) ·
                             validate_task_completion PASS (13 DONE task) ·
                             validate_reference_integrity FAIL với ĐÚNG 3 reference
                             REM-T06 đã biết (baseline không đổi)

NEW_PRODUCTION_BLOCKERS    = NONE
NON_BLOCKING_FINDINGS      = F-S118-01 — PROJECT_PROGRESS.md và báo cáo bản sửa
                             trỏ tới docs/reviews/PHB-03-pending-reason-business-
                             classification.md vốn không có trên canonical ⟹
                             reference integrity 5 thay vì baseline 3. Phân loại F
                             (pre-existing, non-blocking, docs-only). ĐÃ SỬA bằng
                             cách gom file đó (c597f5a) về canonical; validator
                             trở lại đúng 3.
OWNER_DECISIONS_REQUIRED   = NONE
OD_A / OD_B                = R1 · R2 · R3 GIỮ HOÃN — không implement trong phiên
OD_C                       = GIỮ NGUYÊN ngữ nghĩa PRA-002: KHÔNG fuzzy-merge,
                             KHÔNG tự đối soát khi đổi tên hàng / đổi số BH;
                             NOT_SEEN > 0 ⟹ phải soi trước khi duyệt tổng
SCOPE_DRIFT                = NO

PHB03_STATUS               = PRODUCTION_VERIFICATION_INCOMPLETE
NEXT_VERTICAL_ACTION       = Owner deploy commit mới nhất trên canonical + 8 bước
                             kiểm ở mục 17 của docs/reviews/PHB-03-production-
                             verification-e2e.md. Đủ bằng chứng ⟹ PHB-03 = DONE
                             ⟹ PHB-04 Legacy Reference V1.
```

Khối canonical `PHB-03 = REPAIRED_AWAITING_RE_REVIEW` (S117) ngay bên dưới được
**GIỮ NGUYÊN như bản ghi lịch sử đúng tại thời điểm của nó** — kể cả dòng
`NEXT_VERTICAL_ACTION = Independent Re-Review; KHÔNG deploy.`, vốn đúng khi đó.
Khi nó mâu thuẫn với mục này về trạng thái *hiện tại*, mục này đúng.

## CANONICAL CURRENT STATE — PHB-03 = REPAIRED_AWAITING_RE_REVIEW (AUTHORITATIVE, 2026-09-04, S117)

`PHB-03` đã được **sửa có ranh giới** theo Owner Decisions `OD-1`…`OD-6`, trên
đúng HEAD của bản triển khai gốc. Trạng thái là `REPAIRED_AWAITING_RE_REVIEW` —
**chưa** `DONE`: cần Independent Re-Review, và **KHÔNG deploy**.

Căn cứ nghiệp vụ: `docs/reviews/PHB-03-pending-reason-business-classification.md`
(audit chỉ-đọc, commit `c597f5a`). Báo cáo triển khai bản sửa:
`docs/reviews/PHB-03-bounded-business-semantics-repair.md`.

```text
TARGET_GATE               = PASS (BASE_HEAD = 60adb2ec22efdb4967d6971bbee852db660c8c18,
                            trùng đúng HEAD của claude/phb-03-summary-employee-parity-7x3uid)
MODE                      = BOUNDED REPAIR
REPAIR_BRANCH             = claude/phb-03-bounded-semantics-repair-685gf4

PROFIT_GATE               = ĐỔI. Cửa chặn lợi nhuận nay đọc ĐẦU VÀO KINH TẾ
                            (giá bán · số lượng > 0 · giá nhập hiệu lực ·
                            thẩm quyền KPI), KHÔNG đọc `status`. Tập cửa chặn
                            đã freeze tại app/modules/reporting/profit_gate.py.
GENERIC_PENDING_BLOCKS    = NO (OD-6). Nhãn `PENDING` là bằng chứng lịch sử
                            của lần chạy máy, không còn là luật tính toán.
B01 giá tay có hiệu lực   = PASS — vòng tự khoá đã cắt; giá MANUAL/
                            MANUAL_OVERRIDE tính lại theo công thức DEC-143.
B02 missing_price_lines   = PASS — bỏ vế `status == "AUTO"` vốn khiến ô đếm
                            luôn bằng 0 theo cấu tạo; thêm owner_fixable_lines.
B03 prose/UI              = PASS — coverage liệt kê TỪNG cửa chặn kèm số dòng;
                            câu cảnh báo chung thôi quy mọi thiếu sót về giá nhập.
B04 rollback              = PASS — tools/db/owner_data.py: downgrade cất dữ
                            liệu Owner vào bảng lưu tạm cùng database, upgrade
                            nạp lại rồi dọn. KHÔNG backup subsystem.

OD-1 số lượng 0           = CHẶN, cảnh báo, không chốt lợi nhuận (không ghi 0)
OD-2 số lượng âm          = CHẶN, cảnh báo, KHÔNG vào KPI nhân viên. Cũng
                            KHÔNG vào tổng công ty — phía thận trọng, cần Owner
                            xác nhận (mục 13 báo cáo).
OD-3 Duplicate            = WARNING_ONLY — doanh thu VÀ lợi nhuận đều cộng;
                            hết mâu thuẫn "cộng doanh thu, bỏ lợi nhuận".
OD-4 giá bán 0            = WARNING_ONLY — tính đúng phép trừ, ra số âm thật.
OD-5 chưa rõ nhân viên    = lợi nhuận vào tổng kỳ; KPI cá nhân chưa gán; nhóm
                            "Chưa xác định nhân viên" mở xem được; gán lại
                            bằng thao tác hẹp, có provenance, không ghi đè
                            bằng chứng gốc.
KPI_AUTHORITY_FAIL_CLOSED = PASS — DEC-143 §1 giữ nguyên, và nay là một vế
                            TƯỜNG MINH của cửa chặn (bịt đường đi vòng qua van
                            mà audit mục 9.3 cảnh báo).

SCHEMA_CHANGE             = 0004_employee_attribution (MỘT bảng, ADDITIVE).
                            Bắt buộc cho OD-5: không có chỗ nào sẵn lưu được
                            việc gán nhân viên mà không ghi đè bằng chứng kế
                            toán gốc. ALEMBIC_HEAD = 0004_employee_attribution.
DETAIL_TABLE              = /kinh-doanh/gia-nhap hoạt động như trang tính:
                            2 ô nhập (giá nhập · nhân viên), 3 ô suy ra tự
                            tính lại sau khi lưu, không có bước "tính" riêng.
                            total_sales GIỮ ngữ nghĩa kế toán, không thay bằng
                            quantity × unit price.

FULL_TESTS                = PASS — 2136 passed, 11 skipped
GOLDEN_TESTS              = PASS — 74 passed, 2 skipped
PRODUCTION_PATH_TESTS     = PASS — 101 passed (business_metrics + vertical +
                            boundaries). Fixture `pair()` nay dựng trạng thái
                            production THẬT (PENDING + mã lý do đã lưu); tổ hợp
                            bất khả `status=AUTO` + thiếu giá nhập đã bị loại.
MIGRATION_ROLLBACK_SAFETY = PASS — 2 passed (round-trip qua alembic thật)
SCOPE_DRIFT               = NO — không đụng Tracking · Product Identity ·
                            Review Queue · sales_queries · analytics_queries ·
                            Target · Legacy · Brand · Advanced Analytics.
OWNER_DECISIONS_REQUIRED  = 1 — dòng số lượng ÂM có vào tổng lợi nhuận công ty
                            không? (bản sửa chọn KHÔNG; xem mục 13 báo cáo)
PHB03_STATUS              = REPAIRED_AWAITING_RE_REVIEW
NEXT_VERTICAL_ACTION      = Independent Re-Review; KHÔNG deploy.
```

Khối canonical `PHB-03 = IMPLEMENTED_AWAITING_REVIEW` (S115) ngay bên dưới
được **GIỮ NGUYÊN như bản ghi lịch sử đúng tại thời điểm của nó**, không viết
lại — kể cả dòng `D1_P1_PRESERVED = YES`, vốn mô tả đúng hành vi lúc đó và
chính là hành vi mà `OD-6` đã thay thế. Khi nó mâu thuẫn với mục này về trạng
thái *hiện tại*, mục này đúng.

## CANONICAL CURRENT STATE — PHB-03 = IMPLEMENTED_AWAITING_REVIEW (AUTHORITATIVE, 2026-09-04, S115)

`PHB-03` (Summary + Employee Business Parity V1) đã **implement xong** trên
hợp đồng FROZEN của `PHB-02`. Trạng thái là `IMPLEMENTED_AWAITING_REVIEW` —
**chưa** `DONE`: Completion Gate của task yêu cầu Independent Review trước.
Task canonical tại `docs/tasks/PHB-03-summary-employee-business-parity.md`;
bàn giao phiên tại `docs/sessions/S115-phb-03-summary-employee-parity.md`.

```text
TARGET_GATE               = PASS (BASE_HEAD = c996ca8, branch
                            claude/phb-03-summary-employee-parity-7x3uid,
                            behind default 0 commit)
MODE                      = MAJOR IMPLEMENTATION

SCOPE_DECISION_11_1       = ĐÓNG. PHB-03 BAO GỒM đường ghi giá nhập, dạng
                            BOUNDED. Lý do: giá nhập → EligibleKpiProfit →
                            LN KPI chính thức → DS quy đổi; tách ra sẽ giao
                            một PHB-03 mà chỉ tiêu quyết định không chạy được.

SUMMARY_V1                = DONE — /kinh-doanh (R-S1…R-S8)
EMPLOYEE_V1               = DONE — /kinh-doanh/nhan-vien (R-E1…R-E8), MỘT
                            trang có bộ chọn nhân viên + kỳ, KHÔNG phải một
                            tab mỗi nhân viên (P1)
PURCHASE_PRICE_COMPLETION = DONE — /kinh-doanh/gia-nhap (R-P1…R-P4)
GIA_DUNG_CLASSIFICATION   = DONE — /kinh-doanh/gia-dung, chỉ nhóm NOI_THANH

PROFIT_COVERAGE_DEFINITION = (dòng THỰC SỰ góp giá trị LN KPI) / (mọi dòng
                            của kỳ). Tử số ĐÚNG BẰNG tập được cộng, nên
                            coverage = 100 % tương đương "mọi dòng đã có mặt
                            trong con số này". Đây là suy luận DUY NHẤT
                            PHB-03 thêm vào phần DEC-PHB02-02 chưa nói hết —
                            điểm cần Independent Review chất vấn trước tiên.
PROFIT_COVERAGE_GATE      = PASS — 99,72 % KHÔNG mở khoá (vector F);
                            100 % mở khoá (vector G)
D1_P1_PRESERVED           = YES — dòng PENDING vẫn KHÔNG vào tổng LN KPI kể
                            cả khi Owner đã nhập giá nhập. Hai lý do "chưa
                            đủ" đếm RIÊNG (missing_price / review_blocked).

PURCHASE_PRICE_AUTHORITY  = bảng kpi_purchase_price_override (origin
                            PIPELINE_GENERATED, migration 0003_business),
                            hợp nhất LÚC ĐỌC. Đúng slot PRICE_SOURCE_MANUAL
                            đã chừa từ TASK-105.
PURCHASE_PRICE_PROVENANCE = AUTO / MANUAL / MANUAL_OVERRIDE đầy đủ.
                            Provenance do SERVER quyết từ giá AUTO đọc lại
                            tại chỗ, KHÔNG do form khai. Nhập trùng đúng giá
                            AUTO vẫn là MANUAL_OVERRIDE.
PURCHASE_PRICE_AUTHORITY_CONFLICT = KHÔNG PHÁT SINH. accounting_purchase_price
                            /price_source (PriceProvider) và
                            HistoricalConfirmedRegistry (E-J, pre-cutover,
                            INV-47/51/54) KHÔNG bị chạm;
                            order_line_result_version vẫn append-only.
GIA_DUNG_AUTHORITY        = bảng product_group_classification, khoá theo
                            product_key (tick một lần, hiệu lực mọi kỳ).
                            Ranh giới 8 % chỉ cho NOI_THANH là CẤU TRÚC của
                            config/conversion_rates.yaml, không phải một câu
                            if. Cấm suy từ tên hàng — không luật nào đọc
                            product_label.

CONVERTED_SALES           = DONE — EligibleKpiProfit ÷ rate theo TỪNG DÒNG
                            rồi cộng (R-E6, không bao giờ tỉ lệ pha trộn).
                            profit * rate KHÔNG tồn tại trong mã.
CONVERSION_RATE_MATRIX    = PASS — đo trên config/conversion_rates.yaml thật
TOTAL_PRODUCT_QUANTITY    = PASS — SUM(quantity) khi ĐƠN GIÁ > 1.000.000
                            (`>` chặt; dòng đúng 1.000.000 BỊ LOẠI)
MOM_SALES                 = PASS — % doanh thu bán hàng; ba nhánh "không so
                            được" tách riêng, không nhánh nào in phần trăm
TARGET                    = KHÔNG implement (PHB-05). Layout Summary/Employee
                            KHÔNG chừa hạ tầng riêng cho nó.

BUSINESS_ACCEPTANCE_TESTS = 13/13 vector A–M PASS
FULL_TEST_SUITE           = 2106 passed, 11 skipped (trước: 2032/11)
GOLDEN_BASELINE           = 58 passed, 2 skipped — KHÔNG ĐỔI
NEW_TESTS                 = 74 (business_metrics 33 · business_vertical 35 ·
                            business_boundaries 6)
UPDATED_TESTS             = 4 trong tests/test_history_db.py — bản kiểm kê
                            schema/migration vẫn ĐÓNG, chỉ dài thêm đúng hai
                            bảng và một revision, vì DEC-PHB02-02/05 yêu cầu
                            persistence. Frozen business decision supersede
                            một kỳ vọng cũ, KHÔNG phải nới lỏng tuỳ tiện.

GOVERNANCE_VALIDATORS     = validate_structure PASS · validate_project_state
                            PASS · validate_evidence PASS (155 REQUIRED PASS) ·
                            validate_task_completion PASS (13 DONE task) ·
                            validate_reference_integrity FAIL với ĐÚNG 3
                            reference REM-T06 đã biết (baseline không đổi)

ALEMBIC_HEAD              = 0002_snapshots → 0003_business (ADDITIVE thuần,
                            có test round-trip; `alembic upgrade head` trước
                            khi mở cổng — quy trình đã có, không bước mới)
DEPLOYED                  = NO (phiên này KHÔNG deploy, KHÔNG merge production)

BLOCKING_FINDINGS         = 0
NON_BLOCKING_FINDINGS     = FIND-PHB03-N01 coverage 100 % không đạt được bằng
                            riêng luồng nhập giá khi còn dòng PENDING (đã phơi
                            riêng trên trang) · N02 FIND-PHB02-N07 xác nhận
                            lại: hai cách đọc cho CÙNG kết quả trên mọi tổ hợp
                            thật · N03 giá nhập tay không có lịch sử sửa (đúng
                            chỉ thị cấm version-control) · N04 entered_by /
                            classified_by luôn NULL (chưa có xác thực người
                            dùng; KHÔNG điền giá trị bịa) · N05 migration 0003
                            phải chạy trước deploy
SCOPE_DRIFT               = NO
PHB03_STATUS              = IMPLEMENTED_AWAITING_REVIEW
NEXT_VERTICAL_ACTION      = Independent Review của PHB-03 implementation
```

Khối canonical `PHB-02 = DONE` (S114) ngay bên dưới được **GIỮ NGUYÊN như bản
ghi lịch sử đúng tại thời điểm của nó**, không viết lại. Khi nó mâu thuẫn với
mục này về trạng thái *hiện tại*, mục này đúng.

## CANONICAL CURRENT STATE — PHB-02 = DONE (AUTHORITATIVE, 2026-09-04, S114)

`PHB-02` (Business Parity Contract) **TỔNG THỂ = `DONE`**. Owner đã ban hành
bảy quyết định `DEC-PHB02-01…07` (đăng ký tại `PROJECT/PROJECT_DECISIONS.md`
→ `DEC-174`), đóng toàn bộ bảy câu hỏi mà audit `S113` mở. Hợp đồng
**FROZEN** tại `docs/tasks/PHB-02-business-parity-contract.md`; bàn giao phiên
tại `docs/sessions/S114-phb-02-owner-decisions-freeze.md`.

```text
TARGET_GATE               = PASS (HEAD = a47c164, branch
                            claude/business-parity-contract-me80ij, worktree sạch)
MODE                      = BUSINESS CONTRACT FREEZE — 0 dòng production code
OWNER_DECISIONS_APPLIED   = 7 / 7
OWNER_DECISIONS_REMAINING = 0

PARITY_ORACLE             = DEC-PHB02-01 — báo cáo tay = BUSINESS REQUIREMENT /
                            SEMANTIC REFERENCE, KHÔNG phải FINAL NUMERIC
                            AUTHORITY. Cấm sửa Reports chỉ để tái tạo số tay
                            không tái tạo được từ nguồn đã chấp nhận + rule
                            đã duyệt.
PURCHASE_PRICE_RULE       = DEC-PHB02-02 — AUTO-fill bằng thuật toán khớp giá
                            đã chấp nhận · thiếu dữ liệu ⟹ cảnh báo tường minh
                            + nhập tay · ô AUTO vẫn SỬA ĐƯỢC · provenance tối
                            thiểu AUTO vs MANUAL/MANUAL_OVERRIDE, cấm âm thầm
                            coi override là AUTO
PROFIT_COVERAGE_GATE      = DEC-PHB02-02 — LN KPI CHÍNH THỨC chỉ khi
                            PROFIT_COVERAGE = 100 %. KHÔNG ngưỡng 90/95 %.
                            Dưới 100 %: không trình bày như số chính thức,
                            phơi rõ phần thiếu, cho hoàn thiện bằng tay.
TOTAL_PRODUCT_QUANTITY    = DEC-PHB02-03 — SUM(quantity) khi giá bán >
                            1.000.000 VND. Ngưỡng giá, KHÔNG phải taxonomy,
                            KHÔNG phải đếm SKU/dòng. Đóng N.7 cho chỉ tiêu này.
CONVERTED_SALES_FORMULA   = DEC-PHB02-04 — CONVERTED_SALES = PROFIT /
                            CONVERSION_RATE (PHÉP CHIA). `profit * rate` bị
                            CẤM TUYỆT ĐỐI. Phạm vi = TẤT CẢ đơn đủ điều kiện
                            trong tháng. PROFIT = EligibleKpiProfit (DEC-143).
CONVERSION_RATE_MATRIX    = DEC-PHB02-05 — Tín Phát 7,5 % · Vinh/Quý/Hiệp
                            2 % (8 % khi sản phẩm được tick GIA_DUNG) ·
                            bán lẻ khác 5,5 %
GIA_DUNG_SCOPE            = PRODUCT-LEVEL OVERRIDE, chỉ trong luồng
                            wholesale/nội-thành (Vinh/Quý/Hiệp). KHÔNG phải
                            một loại nhân viên. Cấm suy tự động từ tên hàng.
                            Bán lẻ thường KHÔNG cần luồng này.
TARGET_REQUIREMENT        = DEC-PHB02-06 — cấu hình được theo từng nhân viên,
                            có chỗ nhập/sửa, cấm hard-code vào logic tính.
                            Implementation → PHB-05.
MOM_RULE                  = DEC-PHB02-07 — % thay đổi DOANH THU BÁN HÀNG so
                            tháng liền trước. KHÔNG phải DS quy đổi/lợi
                            nhuận/số lượng/mức đạt target. Mẫu số 0 xử lý
                            tường minh.

Q1..Q7                    = CLOSED toàn bộ (Q4 đóng bằng dẫn xuất từ
                            DEC-PHB02-01+04+05 — xem hợp đồng mục 9.1;
                            phần margin của Q7 giữ DEFER D1, không phải
                            quyết định Owner còn treo)
DEC_PHB02_03_MEASURED     = E1 trên hai fixture golden: 358 (01.2026, loại 45
                            dòng) · 178 (06.2026, loại 27 dòng) so với
                            SUM(quantity) mọi dòng 407/210. Đọc "giá bán" là
                            đơn giá hay tổng dòng cho CÙNG kết quả (chênh 0).
CONTRACT_ADDITIONS        = S13 giá nhập sửa được có provenance · S14 gate
                            coverage 100 % · S15 phạm vi tick GIA_DUNG ·
                            S16 target cấu hình được · M3/M4/M5 ·
                            X9/X10 · R-P1…R-P4 · R-S7/R-S8 · R-E7/R-E8

BLOCKING_FINDINGS         = 0 — FIND-PHB02-B01 CLOSED (DEC-PHB02-01),
                            FIND-PHB02-B02 CLOSED (DEC-PHB02-04+05+02)
NON_BLOCKING_FINDINGS     = N01 giữ · N02/N03 hạ cấp thành cảnh báo đơn vị cho
                            PHB-05 · N04 giữ · N05 đổi trạng thái thành khoảng
                            trống đã biết của PHB-03 · N06/N07/N08 mới
PRA003_D2_D3              = D2 KHÔNG mở lại (cấm sao chép legacy target vào
                            chỉ tiêu PIPELINE_GENERATED vẫn nguyên hiệu lực).
                            D3 nay CÓ điều kiện gỡ vì DEC-PHB02-03 chính là
                            quy tắc có thẩm quyền D3 chờ — nhưng UI KHÔNG đổi
                            trong PHB-02; áp dụng thuộc PHB-03.
PHB03_SEQUENCING_NOTE     = DS quy đổi và LN KPI chính thức đều cần coverage
                            100 %; đường ghi để đạt được (nhập/override giá
                            nhập) CHƯA TỒN TẠI. PHB-03 phải chốt PHẠM VI:
                            bao gồm đường ghi đó, hay tách vertical riêng
                            đứng trước? Đây là quyết định ROADMAP, KHÔNG phải
                            khoảng trống ngữ nghĩa.

GOVERNANCE_VALIDATORS     = validate_structure PASS · validate_project_state
                            PASS · validate_evidence PASS (155 REQUIRED PASS) ·
                            validate_task_completion PASS (13 DONE task) ·
                            validate_reference_integrity FAIL với ĐÚNG 3
                            reference REM-T06 đã biết (baseline không đổi)
PRODUCTION_CODE_CHANGED   = NO
BUSINESS_PARITY_CONTRACT  = FROZEN
PHB_03_READY              = YES
SCOPE_DRIFT               = NO
PHB02_FINAL_STATUS        = DONE
NEXT_VERTICAL_ACTION      = PHB-03 Summary + Employee Business Parity V1
                            (KHÔNG bắt đầu trong phiên này)
```

Khối canonical `PHB-02 = AWAITING_OWNER` (S113) ngay bên dưới được **GIỮ
NGUYÊN như bản ghi lịch sử đúng tại thời điểm của nó**, không viết lại — nó
ghi trạng thái trước khi Owner ban hành bảy quyết định. Khi nó mâu thuẫn với
mục này về trạng thái *hiện tại*, mục này đúng.

## CANONICAL CURRENT STATE — PHB-02 = AWAITING_OWNER (AUTHORITATIVE, 2026-09-04, S113)

`PHB-02` (Business Parity Contract — báo cáo tay của Owner so với Reports hiện
tại) đã hoàn tất phần AUDIT và sinh ra một hợp đồng **ĐỀ XUẤT**. `PHB-02`
**CHƯA `DONE`**: còn 7 quyết định thuộc thẩm quyền Owner. Hợp đồng đầy đủ tại
`docs/tasks/PHB-02-business-parity-contract.md`; bàn giao phiên tại
`docs/sessions/S113-phb-02-business-parity-audit.md`.

```text
TARGET_GATE               = PASS (HEAD = eaa3fdeb4ffdfd2d5772314ac24cf8a1273cc67e,
                            worktree sạch, PHB-01 = DONE, PHB-02 = CURRENT)
MODE                      = READ-ONLY BUSINESS AUDIT — 0 dòng production code
MANUAL_REPORT             = data/samples/Bao_cao_Kinh_doanh_2026.xlsx
                            (59 sheet = 56 nhân viên-tháng 01–08.2026 +
                            Summary 2025 + Summary 2026 + DataChart 2026)
MANUAL_REPORT_AVAILABLE   = NO  (.xlsx không có trong session — PII, DEC-108)
MANUAL_REPORT_STRUCTURE   = YES qua trích xuất đã chấp nhận
                            (docs/analysis/_evidence/evidence.json + docs/analysis/*)
                            ⟹ đủ thẩm quyền để kết luận parity mà KHÔNG bịa cấu trúc

PARITY_ORACLE_FINDING     = Reports tái tạo sổ ERP ĐẾN TỪNG ĐỒNG
                            (sales_raw_gross 3.564.610.000 ≡ THÔ 3.564.610k);
                            báo cáo tay thì KHÔNG và lệch hai chiều ngược nhau
                            (01.2026 BC thấp hơn ERP 0,58 % doanh số; 06.2026
                            BC thấp hơn 6,5 % doanh số nhưng CAO HƠN 24,3 %
                            lợi nhuận) vì chứa 635/18.148 ô giá gõ tay và các
                            loại trừ đơn thủ công KHÔNG có dấu vết
MUST_MATCH_PROVEN         = M1 số đơn theo (nhân viên, tháng) — 254=254=254 ·
                            146=146=146
                            M2 tổng bán gộp so với sổ ERP — khớp từng đồng
KPI_PROFIT_COVERAGE       = golden 01/06.2026: price_source = Pending trên
                            351/351 và 180/180 dòng ⟹ LN KPI KHÔNG TÍNH ĐƯỢC;
                            production 09/2026 đạt 34/142 dòng
CONVERSION_SEMANTICS      = MATCH ở chiều lead_source (ADS_7_5@0.075 trên
                            351/351 dòng Tín Phát, đúng =G6/7.5% của báo cáo
                            tay); NOT_IMPLEMENTED ở chiều product_group
                            (product_group_provenance = DEFAULT 100 %)
CONVERTED_REVENUE         = NOT_IMPLEMENTED trên đường pipeline (chỉ có
                            conversion_rate_final theo dòng; không có tổng hợp)
TARGET                    = NOT_IMPLEMENTED trên pipeline (D2 khoá cứng);
                            target KHÔNG đổi theo thời gian trong 2026
CLASSIFICATION            = MUST_MATCH 2 · MUST_PRESERVE_SEMANTICS 12 (S1–S12) ·
                            MAY_IMPROVE_PRESENTATION 5 (P1–P5) · DEFER 9
                            (D1–D9, gồm UX-PI-01) · DROP_INTENTIONALLY 8
                            (X1–X8) · LEGACY_DEPENDENT 6 (L1–L6) ·
                            TARGET_DEPENDENT 1 khối (PHB-05)
SHEET_COUNT_CONCLUSION    = 56 sheet nhân viên-tháng KHÔNG đòi 56 tab web
                            (chỉ 6 biến thể layout; 4/6 khác nhau đúng một ký
                            tự rác ở ô R1)

OWNER_DECISIONS_REQUIRED  = 7 (Q1 oracle parity · Q2 ngưỡng coverage LN KPI ·
                            Q3 định nghĩa "Tổng số SP" (N.7) · Q4 phạm vi tổng
                            công ty (lỗi A2) · Q5 "Gia dụng"/ProductGroup ·
                            Q6 nguồn target (PHB-05) · Q7 mẫu số tỉ suất và
                            "So tháng trước")
PHB_03_READY              = NO — chặn bởi Q1, Q2, Q4, Q7
                            (Q3/Q5/Q6 KHÔNG chặn PHB-03)
BLOCKING_FINDINGS         = 2 — FIND-PHB02-B01 (parity oracle không xác định),
                            FIND-PHB02-B02 (DS quy đổi sẽ implement với ngữ
                            nghĩa đoán). Cả hai là quyết định Owner, KHÔNG
                            phải defect code.
NON_BLOCKING_FINDINGS     = FIND-PHB02-N01…N05
GOVERNANCE_VALIDATORS     = validate_structure PASS · validate_project_state
                            PASS · validate_evidence PASS (155 REQUIRED PASS) ·
                            validate_task_completion PASS (13 DONE task) ·
                            validate_reference_integrity FAIL với ĐÚNG 3
                            reference REM-T06 đã biết (baseline không đổi)
TEST_BASELINE             = full suite 2032 passed, 11 skipped ·
                            Golden Baseline 58 passed, 2 skipped (KHÔNG đổi)
SCOPE_DRIFT               = NO
PHB02_FINAL_STATUS        = AWAITING_OWNER
NEXT_VERTICAL_ACTION      = Owner giải quyết 7 quyết định Business Parity còn
                            lại, sau đó freeze PHB-02 (KHÔNG bắt đầu PHB-03)
```

Khối canonical `PHB-01` (S112) bên dưới GIỮ NGUYÊN, không viết lại.

## CANONICAL CURRENT STATE — PHB-01 = DONE (AUTHORITATIVE, 2026-09-04, S112)

`PHB-01` (Product Identity — phân loại theo TÊN HÀNG, vertical của repo
**Tracking**) **TỔNG THỂ = `DONE`**. Ghi ở đây vì Reports là bên tiêu thụ hợp
đồng `inv.map` (`app/modules/product/identity/tracking_inv_map.py`) và
`IDENTITY_UNRESOLVED` là một trạng thái của pipeline Reports. Đầy đủ tại
`docs/sessions/S112-phb-01-tracking-reconciliation-closure.md`.

```text
TRACKING_REPO             = hoangvinhkta-creator/Tracking
TRACKING_GIT_GATE         = PASS (main tổ tiên nghiêm ngặt, 0 behind/3 ahead,
                            worktree sạch, không commit lạ)
PRE_MERGE_TEST_GATE       = PASS — 59 bộ · 2594 đạt · 0 hỏng · 2 bỏ qua · build OK
TRACKING_MAIN_BEFORE      = 9ede079413065ae0beef2c3ae005d332d8d92eca
TRACKING_MAIN_AFTER       = 598b4b1390cc96e552455ab85e2c48d78198b89c
TRACKING_CANDIDATE        = 598b4b1390cc96e552455ab85e2c48d78198b89c
FAST_FORWARD              = YES (không force · không rewrite · không squash ·
                            không rebase · không cherry-pick · không merge commit)
PUSH_MAIN                 = YES (9ede079..598b4b1)
ROLLBACK_SHA              = 9ede079413065ae0beef2c3ae005d332d8d92eca
APP_BUILD                 = b126 (trên main sau reconcile = trên production)
PRODUCTION_FINGERPRINT    = PASS (nguồn: Owner) — live có `invActiveRow(`
                            đúng 3 lần; hàm này vắng qua 53993f1, xuất hiện ở
                            598b4b1 → production khớp bản sửa NB-2 CUỐI CÙNG
SMOKE_LIVE_HTTP           = NOT_OBSERVABLE (proxy egress 403 tới
                            price.tinphatcrm.com — cùng lớp denial S093/S110)
SMOKE_VALUE_TYPE          = PASS bằng đọc-tĩnh + test bắt buộc (`chieuInvMap()`
                            chỉ giữ giá trị CHUỖI, loại object wrapper;
                            `kiem/xuat-baocao.js` mục 7b)
SMOKE_CROSS_REPO_KEY      = PASS ba chiều — Tracking `invKeyOfName()` ≡ Reports
                            `inv_map_key()` ≡ UI production
REAL_E2E                  = PASS (Owner, production thật)
E2E_CASE                  = BH73877 / "Máy giặt Electrolux EWF1143R7SC"
E2E_KEY                   = N_MYGITELECTROLUXEWF1143R7SC -> EWF1143R7SC
IDENTITY_BEFORE           = IDENTITY_UNRESOLVED
IDENTITY_AFTER            = IDENTITY_UNRESOLVED đã biến mất
ECONOMIC_STATE_AFTER      = PENDING — TRACKING_HISTORY_PENDING /
                            Missing.PurchasePrice (ĐÚNG: identity không được
                            bịa bằng chứng kinh tế, không ép AUTO)
RERUN_WORKBOOK            = So_chi_tiet_ban_hang (10).xlsx
RERUN_TOTALS              = 106 đơn không đổi · AUTO 17 → 56 · cần review
                            89 → 50 · identity unresolved 36 → 35
ECONOMIC_ISOLATION        = GIỮ NGUYÊN (không auto-recalc từ màn mới; khoá
                            trùng dòng INV.cu/INV.moi đang hoạt động thì TỪ
                            CHỐI ghi và đẩy về luồng Tồn kho — chốt NB-2)
BLOCKING_FINDINGS         = 0
DEFERRED                  = NB-1 · NB-3/4/5 · NB-6 (UI polish) · 35 mô tả chưa
                            phân giải (OPERATIONAL DATA CLEANUP, không phải
                            implementation, không chặn PHB-01)
D8                        = CLOSED trong PHB-01 (không mở task D8 khác)
SCOPE_DRIFT               = NO
PHB01_FINAL_STATUS        = DONE
NEXT_VERTICAL_ACTION      = PHB-02 BUSINESS PARITY CONTRACT (chưa bắt đầu
                            implementation)
```

Không cần thêm implementation nào cho Product Identity. Khối canonical
`TASK-PRA-005` (S111) bên dưới GIỮ NGUYÊN, không viết lại.

## CANONICAL CURRENT STATE — TASK-PRA-005 = DONE (AUTHORITATIVE, 2026-09-03, S111)

`TASK-PRA-005` (Sản phẩm — Mặt hàng trên chứng từ) **TỔNG THỂ = `DONE`**.
Owner đã trực tiếp mở `reports.tinphatcrm.com` thật, chọn CÙNG kỳ **Tháng
09/2026** trên `/tong-quan` và `/san-pham`, và bốn cặp số reconcile EXACT.
`CHECK-PRA005-15` đổi từ `NOT_TESTED` → **`PASS`**. Đầy đủ tại
`docs/sessions/S111-pra-005-owner-acceptance-closeout.md` và
`docs/tasks/TASK-PRA-005-san-pham.md` → CHECK-PRA005-15.

```text
CANONICAL_BRANCH        = claude/extract-upload-repo-gq2ws4
DEPLOY_CANDIDATE_SHA     = 1a011ee66f9e2b2ffee4d04f6864bfb0eeb45948 (không đổi)
OWNER_PRODUCTION_ACCEPTANCE = PASS
PERIOD                  = Tháng 09/2026
QUANTITY                = 185 (`/tong-quan`) = 185 (`/san-pham`)   — MATCH
REVENUE                 = 1.470.385.000 = 1.470.385.000            — MATCH
KPI                     = 9.586.667 = 9.586.667                    — MATCH
KPI_COVERAGE            = 34/142 dòng = 34/142 dòng                — MATCH
ITEM_COUNT              = 102 (Số mặt hàng trên chứng từ, Tháng 09/2026)
NULL_SEMANTICS          = PASS — "Tivi Xiaomi L55MB-ASEA"/"Tủ lạnh Funiki
                          HR-T6185TDG" hiện `—` (0/1 dòng); "Tivi Samsung
                          75Q6FA" hiện 1.400.000 (1/1 dòng, biết chắc)
DEFAULT_SORT            = PASS — REVENUE DESC quan sát trực tiếp
                          (107.100.000 · 69.500.000 · 68.800.000 · …)
PRODUCT_LEVEL_PP        = ABSENT (quan sát trực tiếp)
ACCEPTANCE_A..F         = PASS (Owner + cấu trúc product_summary() tái dụng
                          period_totals(), E2 mục 5/11)
ACCEPTANCE_G, H         = PASS — ví dụ cụ thể NOT_PRESENT_IN_CURRENT_REAL_DATA
                          (Tháng 09/2026), hành vi generic đã PASS tại E2
                          (docs/reviews/TASK-PRA-005-INDEPENDENT-REVIEW-
                          RECORD.md mục 8-9), không phụ thuộc kỳ
ACCEPTANCE_I, J, K       = PASS (Owner, trực tiếp)
ACCEPTANCE_L             = DEFERRED_WITHIN_CONTRACT (RECOMMENDED, không chặn)
COMPLETION_GATE          = 14/14 REQUIRED PASS · 1/1 RECOMMENDED
                          NOT_APPLICABLE có giải thích
BLOCKING_FINDINGS        = 0
NON_BLOCKING_FINDINGS    = FIND-PRA005-01/02/03, FIND-PRA005-R1/R2 (không đổi,
                          không repair)
DRILLDOWN_STATUS         = DEFERRED_WITHIN_CONTRACT
SCOPE_DRIFT              = NO
PRA005_FINAL_STATUS      = DONE
GOVERNANCE_VALIDATORS    = validate_structure PASS · validate_project_state
                          PASS · validate_evidence PASS (155 REQUIRED PASS) ·
                          validate_task_completion PASS (13 DONE task) ·
                          validate_reference_integrity FAIL với ĐÚNG 3
                          reference REM-T06 đã biết (baseline không đổi)
```

Bản ghi lịch sử S110 (session AI KHÔNG thể tự thực hiện nghiệm thu vì không
có egress tới production) được GIỮ NGUYÊN, không viết lại — xem khối canonical
S110 bên dưới và `docs/sessions/S110-pra-005-production-acceptance-attempt.md`.

## CANONICAL CURRENT STATE — TASK-PRA-005 PRODUCTION ACCEPTANCE ATTEMPT (AUTHORITATIVE, 2026-09-03, S110)

`PRA-005` **Discovery = DONE** · **Contract = FROZEN** · **Implementation =
INTEGRATED** (canonical HEAD = commit S109, không cần bước Controlled
Integration tách biệt — nhánh review S109 chính là nhánh fast-forward) ·
**Independent Review E2 = ACCEPT** (S109). `CHECK-PRA005-15` (Owner
Production Acceptance) **VẪN `NOT_TESTED`** — phiên S110 xác nhận session
KHÔNG có egress tới `reports.tinphatcrm.com`/`api.render.com` (đúng policy
denial đã ghi nhận ở `CHECK-PRA002-15`/S093) và gate này chỉ định rõ tác
nhân Owner. `PRA-005` TỔNG THỂ **CHƯA `DONE`**.

```text
CANONICAL_BRANCH        = claude/extract-upload-repo-gq2ws4
REQUIRED_SHA            = 1a011ee66f9e2b2ffee4d04f6864bfb0eeb45948
REMOTE_CANONICAL_SHA    = 1a011ee66f9e2b2ffee4d04f6864bfb0eeb45948 (KHỚP)
CANONICAL_MOVED         = KHÔNG
DEPLOY_RESULT           = NOT_EXECUTED_BY_SESSION (không có egress; Owner
                          runbook phát hành)
CHECK-PRA005-15         = NOT_TESTED (không đổi)
COMPLETION_GATE         = 13/14 REQUIRED PASS (01..12 E1 + 14 E2); 15
                          NOT_TESTED; 13 NOT_APPLICABLE (RECOMMENDED)
BLOCKING_FINDINGS       = 0
SCOPE_DRIFT             = NO
PRA005_FINAL_STATUS     = PRODUCTION_ACCEPTANCE_PENDING (không đổi)
OWNER_RUNBOOK           = docs/sessions/S110-pra-005-production-acceptance-
                          attempt.md mục 5 (ánh xạ 1-1 Acceptance A–L)
NEXT_VERTICAL_ACTION    = PRA-005 OWNER PRODUCTION ACCEPTANCE (Owner thực
                          hiện Bước 0–7 của runbook trên hệ thống thật)
```

Governance validators (phiên S110): `validate_structure` PASS ·
`validate_project_state` PASS · `validate_evidence` PASS (154 REQUIRED PASS)
· `validate_task_completion` PASS (12 DONE task, PRA-005 không nằm trong tập
này vì chưa DONE) · `validate_reference_integrity` FAIL với ĐÚNG 3 reference
REM-T06 đã biết (baseline không đổi, không issue mới) · `git diff --check`
sạch.

## CANONICAL CURRENT STATE — PRICE AUTHORITY NORMALIZATION (AUTHORITATIVE, 2026-09-03)

**Phân loại: `OWNER_DECISION` / `PRICE_AUTHORITY_NORMALIZATION`** — thẩm quyền
cao nhất, SUPERSEDES ngữ nghĩa hiện hành khi có xung đột về price authority kể
từ thời điểm này. Quyết định đầy đủ: **DEC-172**
(`PROJECT/PROJECT_DECISIONS.md`). KHÔNG phải PRA-004 defect —
`TASK-PRA-004` giữ nguyên `DONE`, evidence PASS lịch sử KHÔNG bị mở lại.
`PRA-005` DISCOVERY = DONE (S105, xác minh + tích hợp tại S106) · `PRA-005`
CONTRACT = FROZEN (S107) · `PRA-005` IMPLEMENTATION = COMPLETE (S108, nhánh
dedicated `claude/pra-005-v1-implementation-3dcd5k`) · `PRA-005` INDEPENDENT
REVIEW E2 = **ACCEPT** (S109, `BLOCKING_FINDINGS = 0`, không repair,
`FINAL_REVIEWED_HEAD_SHA = 18ab5d39a15b224d34aa04e5c6bbe8261f60efeb`,
`docs/reviews/TASK-PRA-005-INDEPENDENT-REVIEW-RECORD.md`). VẪN **CHƯA tích
hợp canonical**. `PRA-005` TỔNG THỂ CHƯA `DONE` — còn `CHECK-PRA005-15`
Owner Production Acceptance (`NOT_TESTED`).
`NEXT_VERTICAL_ACTION = PRA-005 CONTROLLED INTEGRATION`. Xem khối "CANONICAL
CURRENT STATE — TASK-PRA-005 INDEPENDENT REVIEW E2" bên dưới.

Owner xác nhận: trong Reports chỉ có **MỘT** authority cho giá mua phục vụ
phân tích bán hàng — **Tracking PP có hiệu lực tại ngày bán**, gọi ở nghiệp vụ
là **"Giá mua tham chiếu"**. Sổ bán hàng KHÔNG phải nguồn giá nhập; nó chỉ
cung cấp `sản phẩm + ngày bán` để đối chiếu Tracking. **Không tồn tại** một
`Accounting Purchase Price Authority` hay `Accounting Profit` management metric
chạy song song. Lợi nhuận quản trị chính là **LN KPI**.

```text
BASE_CANONICAL          = 522a093ff952702b479d975aab42d0e10deb461a
                         (khớp EXACT kỳ vọng đầu phiên, CANONICAL_MOVED = KHÔNG)
BRANCH                  = claude/price-authority-semantic-norm-vh43s3

PRICE_AUTHORITY         = TRACKING_PP_AT_SALE_DATE_ONLY
ACCOUNTING_INDEPENDENT_SOURCE = NO — không có nguồn giá nhập kế toán độc lập
                         nào feed vào field; carrier chở đúng Tracking PP đã
                         resolve theo sale_date

LEGACY_FIELD_CLASSIFICATION =
                         accounting_purchase_price = LEGACY_INTERNAL_PP_CARRIER
                         accounting_profit         = LEGACY_DERIVED_FIELD
                         (tồn tại nội bộ; KHÔNG mang business authority)

GENERATION_POINT_TRACED = app/modules/exporting/excel_exporter.py::
                         _present_lines — vòng lặp `Pending.<field>`. Đây là
                         nguồn sự thật DUY NHẤT cho status AUTO/PENDING,
                         review_reason_counts, và pending_reasons được persist.

ACCOUNTING_REASON_CHANGE = Pending.accounting_purchase_price ĐÃ GỠ khỏi đường
                         sinh reason mới
                         Pending.accounting_profit ĐÃ GỠ khỏi đường sinh mới
                         (backend field/công thức/storage/schema KHÔNG đổi)

KPI_REASON_DECISION     = KEEP — Pending.eligible_kpi_profit là lý do ĐỘC LẬP,
                         có bằng chứng: khi config/eligible_costs.yaml hỏng
                         hoặc confirmed_adjustment_source UNAVAILABLE, nó là
                         None NGAY CẢ KHI identity đã nhận diện và PP đã
                         resolve — và là mã DUY NHẤT báo lỗi authority đó.
                         KHÔNG phải KPI_REASON_OWNER_DECISION_REQUIRED.

STATUS_PRESENTATION_MISMATCH = ĐÃ ĐÓNG (được nêu "TIỀM ẨN" ở mục KPI-FIRST
                         PRESENTATION bên dưới). Giả thuyết "một dòng có thể
                         PENDING CHỈ VÌ thiếu dữ liệu kế toán" đã được ĐO
                         trên đường production thật: accounting-only Pending
                         lines = 0 ở CẢ HAI fixture Golden, TRƯỚC lẫn SAU —
                         khớp audit fact F. Mọi dòng từng mang mã kế toán đều
                         còn ít nhất một mã actionable khác
                         (Missing.PurchasePrice), nên không dòng nào lật
                         PENDING → AUTO.

STATUS_SEMANTICS_GLOBAL_REDESIGN = NO — không đại tu AUTO/PENDING, không
                         Review Management System, không status architecture
                         mới.

STATUS_DELTA            = 0 — AUTO/PENDING lines và AUTO/Review orders KHÔNG
                         đổi ở cả period_2026_01 và period_2026_06.
REASON_COUNT_DELTA      = period_2026_01: −349 accounting_purchase_price,
                                          −349 accounting_profit
                         period_2026_06: −180 accounting_purchase_price,
                                          −180 accounting_profit
                         (Số Review KHÔNG giảm — đúng kỳ vọng audit, KHÔNG
                         phải thất bại. Mục tiêu là SEMANTIC CORRECTNESS +
                         REASON CLARITY.)

HISTORICAL_DATA_REWRITE = NO — DO NOT BACKFILL. pending_reasons_json của các
                         result version đã lưu giữ nguyên hai mã kế toán;
                         không migration, không mutate historical evidence.
                         UI hiển thị kết quả CŨ vẫn hiện mã lịch sử — hành vi
                         này được chấp nhận tường minh, không phải bug. Hai
                         nhãn tiếng Việt vì thế GIỮ LẠI trong
                         REASON_DISPLAY_LABELS, đánh dấu bằng
                         app/beta_presentation.py::RETIRED_PENDING_REASONS.

REASON_UNIVERSE_TIERS   = reason_universe()     = 19 mã (sinh cho kết quả MỚI)
                         renderable_universe() = 21 mã = 19 + RETIRED (đọc
                         lại lịch sử). Cả hai dẫn xuất TỪ MÃ NGUỒN qua AST,
                         không chép tay.

SCHEMA_CHANGE           = NO
TRACKING_CHANGE         = NO (Tracking = READ-ONLY REFERENCE)
PP_ALGORITHM_CHANGE     = NO (PricingEffectiveDate = sale date giữ nguyên;
                         không backfill giá hiện tại, không ngoại suy,
                         NULL != 0 giữ nguyên)
KPI_FORMULA_CHANGE      = NO
IDENTITY_CHANGE         = NO (Tracking vẫn là Product Identity Authority)

PRODUCTION_LOGIC_LOC    = ~14 dòng (2 file: excel_exporter.py vòng lặp reason;
                         beta_presentation.py thêm RETIRED_PENDING_REASONS)
                         — trong change budget ≤ 80 LOC.

NUMERIC_ORACLES         = KHÔNG ĐỔI. BH73844 (9.550.000 / 9.450.000 /
                         100.000) và BH73877 (32.800.000 / 456.667 /
                         coverage 2/3) giữ nguyên. Chỉ ngữ nghĩa reason đổi,
                         và chỉ trên xử lý MỚI.

BH73877_NEW_SEMANTIC    = Chưa nhận diện sản phẩm · Thiếu giá mua tham chiếu ·
                         Thiếu lợi nhuận KPI
                         (bản đã persist KHÔNG bị sửa)

TESTS                   = Full suite 1984 passed, 11 skipped
                         Golden baseline 58 passed, 2 skipped (khớp con số
                         authority trong CLAUDE.md)
                         PRA-003 68 passed · PRA-004 94 passed
                         Focused mới: tests/test_price_authority_
                         normalization.py — 16 passed (brief §17 A–K)
GOVERNANCE_VALIDATORS   = structure PASS · project_state PASS ·
                         reference_integrity FAIL với ĐÚNG 3 issue REM-T06 đã
                         biết từ trước (không phát sinh issue mới)
```

**Bài học governance (DEC-172 §9):** `SOURCE FIELD / LEGACY FIELD NAME` không
tự động tạo ra `BUSINESS AUTHORITY`. Một metric/status/reason mới có tác động
tới business state đòi hỏi **authority classification tường minh** — không
được suy ra từ tên field, tên cột nguồn, hay tên module.


## CANONICAL CURRENT STATE — TASK-PRA-005 DISCOVERY (AUTHORITATIVE, 2026-09-03, S106 — Evidence Verification + Integration)

`PRA-005` **Discovery = DONE**. `PRA-005` **Contract = NOT STARTED**. Discovery
gốc chạy tại phiên S105 trên nhánh `claude/pra-005-discovery-dsryx5` (docs-only,
0 dòng production code); phiên S106 xác minh lineage (branch tồn tại, ancestry
sạch, diff đúng 1 file `docs/sessions/S105-pra-005-san-pham-discovery.md`, 822
dòng thêm, không production/schema/migration/Tracking) rồi tích hợp bằng
**fast-forward** vào canonical. Không rerun Discovery — chỉ tái lập độc lập
được ví dụ SPLIT `FTKB50ZVMV` (đọc trực tiếp `tests/fixtures/golden/
period_2026_01.xlsx`: dòng `BH63724` qty 7 / doanh thu 113.750.000, dòng
`BH62439` qty 1 / doanh thu 16.300.000 — khớp đúng số trong S105) và các tham
chiếu mã nguồn (`app/history/keys.py:70`, `analytics_presentation.py`,
`tools/db/schema.py`, `product_group.py`).

```text
SESSION                      = S106 — PRA-005 Discovery Evidence Verification + Integration
DISCOVERY_SESSION            = S105 (nhánh claude/pra-005-discovery-dsryx5)
DISCOVERY_HEAD               = f01464c72eac00858c7c0b78cc26329febaf5219
DISCOVERY_BASE               = 4dfe4b2525ec9496be27b3856e9b3698588dc22a
                              (= BASE_CANONICAL đầu phiên S106, khớp EXACT)
ANCESTRY                     = CLEAN (canonical là ancestor trực tiếp của
                              Discovery HEAD, 1 commit ahead, 0 behind)
DIFF                         = 1 file, docs/sessions/S105-pra-005-san-pham-
                              discovery.md, +822/-0, KHÔNG production code
INTEGRATION_STRATEGY         = FAST_FORWARD (ff-only, không cherry-pick,
                              không rebase, không squash)
PRODUCTION_CODE_DELTA        = 0
SCHEMA_REQUIRED              = NO · NEW_AUTHORITY_REQUIRED = NO ·
                              TRACKING_CHANGE_REQUIRED = NO
DISCOVERY_ACCEPTANCE         = ACCEPT
BLOCKING_FINDINGS            = 0
SCOPE_DRIFT                  = NO

NEXT_VERTICAL_ACTION         = PRA-005 CONTRACT FREEZE
```

OD-PRA005-1 (khoá gộp sản phẩm) và OD-PRA005-2 (dòng dịch vụ trong bảng sản
phẩm) là **khuyến nghị Discovery**, chưa phải `OWNER_DECISION` — *(trạng
thái lịch sử tại thời điểm S106; đã được khoá thành `OWNER_DECISION` chính
thức tại S107, xem khối "TASK-PRA-005 CONTRACT FREEZE" ngay dưới đây)*.


## CANONICAL CURRENT STATE — TASK-PRA-005 CONTRACT FREEZE (AUTHORITATIVE, 2026-09-03, S107)

`PRA-005` **Discovery = DONE** (không đổi, S105/S106). `PRA-005`
**Contract = FROZEN** (phiên này, S107). `PRA-005` **Implementation = NOT
STARTED**. Contract chạy trên nhánh `claude/pra-005-contract-freeze-99nuai`,
mở trực tiếp từ canonical HEAD hiện hành — KHÔNG cần fast-forward để đồng bộ
(0 ahead, 0 behind lúc mở phiên).

```text
SESSION                      = S107 — PRA-005 Contract Freeze SẢN PHẨM
BASE_CANONICAL                = 1ebb0021e13f85fe7ac7825e1219583e4c682889
                              (khớp EXACT kỳ vọng đầu phiên, CANONICAL_MOVED = KHÔNG)
BRANCH                        = claude/pra-005-contract-freeze-99nuai
DISCOVERY_STATUS               = DONE (S105, xác minh + tích hợp S106)
DISCOVERY_ARTIFACT             = docs/sessions/S105-pra-005-san-pham-discovery.md

OD_PRA005_01                   = RAW_DOCUMENT_DESCRIPTION — nâng từ khuyến
                              nghị Discovery thành OWNER_DECISION, ghi
                              PROJECT/PROJECT_DECISIONS.md DEC-173
OD_PRA005_02                   = INCLUDE_ALL_DOCUMENT_LINES — nâng từ khuyến
                              nghị Discovery thành OWNER_DECISION, ghi
                              PROJECT/PROJECT_DECISIONS.md DEC-173
OWNER_DECISIONS_RECORDED       = YES

GROUPING_CONTRACT              = NORMALIZED_RAW_DOCUMENT_DESCRIPTION
                              (= product_key đã tồn tại, TÁI DỤNG nguyên vẹn)
PRODUCT_IDENTITY_CLAIM         = NOT_CANONICAL_PRODUCT_IDENTITY
SERVICE_FEE_TREATMENT          = INCLUDE_ALL
SUMMARY_CONTRACT               = 4 chỉ tiêu (Số mặt hàng trên chứng từ ·
                              Tổng số lượng · Doanh thu NET · LN KPI + coverage)
TABLE_CONTRACT                 = 5 cột (Mặt hàng · Số lượng · Số đơn ·
                              Doanh thu · LN KPI)
DEFAULT_SORT                   = REVENUE_DESC (trình bày, KHÔNG phân loại)
KPI_PROFIT_SEMANTICS           = SUM_KNOWN_VALUES_WITH_EXPLICIT_COVERAGE
NULL_SEMANTICS                 = UNKNOWN_IS_NOT_ZERO
REFERENCE_PRICE_CONTRACT       = LINE_LEVEL_ONLY

SCHEMA_REQUIRED                = NO
NEW_AUTHORITY_REQUIRED         = NO
TRACKING_CHANGE_REQUIRED       = NO
PRODUCTION_CODE_CHANGE         = NO

BLOCKING_FINDINGS              = 0
SCOPE_DRIFT                    = NO

CONTRACT_ARTIFACT              = docs/tasks/TASK-PRA-005-san-pham.md
                              Status: READY · Completion Gate FROZEN
                              (15 check: 14 REQUIRED · 1 RECOMMENDED, tất cả NOT_TESTED)
CONTRACT_EXIT_GATE             = PASS (13/13 điều kiện)
IMPLEMENTATION_READY           = YES

NEXT_VERTICAL_ACTION           = PRA-005 IMPLEMENTATION
```

Bằng chứng thực thi của phiên (E1):

```text
validate_structure           : PASS (21 required path)
validate_project_state       : PASS
validate_evidence            : PASS (141 REQUIRED PASS evidence record)
validate_task_completion     : PASS (12 DONE task)
validate_reference_integrity : FAIL — ĐÚNG 3 issue đã biết của TASK-REM-T06
                               (/README.md, CODE_OF_CONDUCT.md,
                                CONTRIBUTING.md) — không phát sinh mới. Một
                               forward-reference mới của phiên này
                               (docs/tasks/TASK-PRA-005-san-pham.md →
                               docs/reviews/TASK-PRA-005-INDEPENDENT-REVIEW-
                               RECORD.md, file CHECK-PRA005-14 sẽ tạo ở
                               implementation) đã được thêm vào
                               KNOWN_EXEMPT_PAIRS của
                               validate_reference_integrity.py, đúng khuôn
                               tiền lệ TASK-105C (DEC-152) — đây là thay đổi
                               governance-script tối thiểu, KHÔNG phải
                               production feature code.
git diff --check              : sạch
branch_authority_check.sh     : AUTHORITY_OK (sau khi push
                               `git push -u origin
                               claude/pra-005-contract-freeze-99nuai`) —
                               AUTHORITY = BRANCH_WITH_UPSTREAM, ahead
                               default 1 commit / behind 0, DIVERGENCE =
                               WITHIN_LIMITS (cumulative LOC 1783, dưới
                               ngưỡng 5.000 của V4.1 §8)
```

Contract artifact đầy đủ (30 mục theo brief Contract Freeze, ánh xạ 1:1 vào
cấu trúc Task file chuẩn của dự án): `docs/tasks/TASK-PRA-005-san-pham.md`.
Bàn giao chi tiết: `docs/sessions/S107-pra-005-contract-freeze.md`.


## CANONICAL CURRENT STATE — TASK-PRA-005 INDEPENDENT REVIEW E2 (AUTHORITATIVE, 2026-09-03, S109)

`TASK-PRA-005` V1 implementation đã qua **Independent Review E2** — chu kỳ
review DUY NHẤT đã hoạch định cho lineage PRA-005. Kết quả: **ACCEPT**.
Bản ghi đầy đủ: `docs/reviews/TASK-PRA-005-INDEPENDENT-REVIEW-RECORD.md`.

```
REVIEW_RESULT                 = ACCEPT
CANONICAL_SHA                 = 4e06515895814d8fff41580dc0f3c64da464ac83
                                (khớp EXACT kỳ vọng; CANONICAL_MOVED = KHÔNG)
CANDIDATE_FULL_SHA            = 18ab5d39a15b224d34aa04e5c6bbe8261f60efeb
CANDIDATE_BASE                = 4e06515895814d8fff41580dc0f3c64da464ac83 (cha TRỰC TIẾP)
ANCESTRY                      = tuyến tính, 1 commit, 0 behind / 1 ahead
CONTRACT_VERDICT              = PASS
DEC173_VERDICT                = PASS
GROUPING_VERDICT              = PASS — product_key re-derive khớp 226/226 nhóm
PRODUCT_IDENTITY_CLAIM        = NOT_CANONICAL_PRODUCT_IDENTITY
ALL_LINE_INCLUSION            = PASS
QUANTITY / ORDER_COUNT / REVENUE = PASS / PASS / PASS
KPI_SOURCE / NULL / KNOWN_ZERO / COVERAGE = PASS / PASS / PASS / PASS
REFERENCE_PRICE_VERDICT       = PASS — 10/10 thuật ngữ PP đếm 0 trên HTML thật
DISCLOSURE_VERDICT            = PASS
EMPTY_STATE_VERDICT           = PASS
SPLIT_ORACLE / SERVICE_FEE_ORACLE = PASS / PASS
ORACLE                        = quantity 407 · revenue 3.562.310.000 ·
                                kpi 900.000 · 226 nhóm · 351 dòng
                                (reviewer recompute bằng SQL THÔ, 0 sai lệch)
PERFORMANCE_EVIDENCE          = CREDIBLE_SESSION_MEASUREMENT (+ hình dạng
                                truy vấn do reviewer đo: 1 query phẳng,
                                4 query/trang, không N+1)
FULL_SUITE                    = 2032 passed, 11 skipped, 0 failed (chạy lại độc lập)
GOLDEN_EXPECTATION_CHANGE     = NO
BLOCKING_FINDINGS             = 0
NON_BLOCKING_FINDINGS         = 2 (FIND-PRA005-R1, FIND-PRA005-R2)
REPAIR_BATCH_USED             = NO
SCOPE_DRIFT                   = NO
COMPLETION_GATE               = 13/14 REQUIRED PASS (01..12 E1 + 14 E2);
                                CHECK-PRA005-13 NOT_APPLICABLE (RECOMMENDED);
                                CHECK-PRA005-15 NOT_TESTED
GOVERNANCE_VALIDATORS         = validate_structure PASS · validate_project_state
                                PASS · validate_evidence PASS · validate_task_
                                completion PASS · validate_reference_integrity
                                FAIL với ĐÚNG 3 reference REM-T06 đã biết
                                (baseline, không issue mới)
FINAL_REVIEWED_HEAD_SHA       = 18ab5d39a15b224d34aa04e5c6bbe8261f60efeb
INTEGRATION_READY             = YES
CANONICAL_INTEGRATION_STATUS  = NOT_YET_INTEGRATED
NEXT_VERTICAL_ACTION          = PRA-005 CONTROLLED INTEGRATION
```

`TASK-PRA-005` tổng thể **CHƯA `DONE`**: `CHECK-PRA005-15` (Owner Production
Acceptance) giữ `NOT_TESTED` — không đánh PASS bất kỳ tiêu chí deployment /
dữ liệu thật nào trước khi có bằng chứng production.

SHA đầy đủ 40 ký tự `18ab5d39a15b224d34aa04e5c6bbe8261f60efeb` là ứng viên
**DUY NHẤT** được uỷ quyền cho Controlled Integration.

## CANONICAL CURRENT STATE — TASK-PRA-005 IMPLEMENTATION (AUTHORITATIVE, 2026-09-03, S108)

`PRA-005` **Discovery = DONE** (không đổi). `PRA-005` **Contract = FROZEN**
(không đổi, S107). `PRA-005` **Implementation = COMPLETE / REVIEW_PENDING**
(phiên này, S108) — trên nhánh dedicated `claude/pra-005-v1-implementation-
3dcd5k`, tạo ĐÚNG từ `BASE_SHA` freeze, **CHƯA tích hợp vào canonical**.
`PRA-005` tổng thể **CHƯA `DONE`** — còn Independent Review E2 (CHECK-
PRA005-14) và Owner Production Acceptance (CHECK-PRA005-15).

```text
SESSION                       = S108 — PRA-005 MAJOR Implementation
BASE_CANONICAL                = 4e06515895814d8fff41580dc0f3c64da464ac83
                              (khớp EXACT kỳ vọng đầu phiên, CANONICAL_MOVED = KHÔNG)
BRANCH                        = claude/pra-005-v1-implementation-3dcd5k

QUERY_IMPLEMENTATION          = app/web/sales_queries.py::product_totals()
                              — khuôn employee_totals()/_order_metrics() đã
                              có, GROUP BY product_key
GROUPING_IMPLEMENTATION       = product_key (NORMALIZED_RAW_DOCUMENT_
                              DESCRIPTION, OD-PRA005-01/DEC-173), TÁI DỤNG
                              NGUYÊN VẸN — không hàm chuẩn hoá thứ hai
ALL_LINE_INCLUSION            = PASS — is_non_product_line() KHÔNG được gọi
                              (xác nhận AST + test trên oracle thật)
SUMMARY_IMPLEMENTATION        = sales_presentation.product_summary() TÁI
                              DỤNG NGUYÊN VẸN analytics_queries.
                              period_totals() (đã fetch sẵn ở _pipeline_
                              view() cho /tong-quan cùng kỳ) cho 3/4 chỉ
                              tiêu; item_count = len(rows) là chỉ tiêu MỚI
TABLE_IMPLEMENTATION          = đúng 5 cột (Mặt hàng · Số lượng · Số đơn ·
                              Doanh thu · LN KPI)
WEB_ROUTE                     = GET /san-pham (app/web/server.py::products)
DEFAULT_SORT                  = REVENUE_DESC, tie-breaker product_key
REFERENCE_PRICE_AGGREGATE     = NOT_PRESENT (AST + grep template xác nhận)
DRILLDOWN_STATUS              = DEFERRED_WITHIN_CONTRACT (mục 18 cho phép;
                              CHECK-PRA005-13 = NOT_APPLICABLE, RECOMMENDED
                              nên không chặn task)

SCHEMA_CHANGE                 = NO
NEW_AUTHORITY                 = NO
TRACKING_CHANGE                = NO
PRODUCTION_PYTHON_LOC_DELTA    = 126 dòng (sales_queries.py 54 + sales_
                              presentation.py 48 + server.py 24) — dưới
                              ngân sách mềm 200 dòng (mục 24)

FOCUSED_TESTS                  = 48 test PRA-005 mới, tất cả PASS
                              (28 tests/test_product_queries.py + 14
                              tests/test_web_product_view.py + 6 tests/
                              test_sales_presentation.py)
PRA003_REGRESSION              = PASS, không đổi
PRA004_REGRESSION              = PASS, không đổi
GOLDEN_REGRESSION              = PASS, không sửa Golden expectation nào
FULL_SUITE                     = 2032 passed, 11 skipped, 0 failed

SPLIT_REGRESSION               = PASS (FTKB50ZVMV đo lại đúng chính tả
                              fixture: 'Điều hoà Daikin  FTKB50ZVMV' SL 7/
                              113.750.000 · 'Máy lạnh Daikin Inverter 2 HP
                              FTKB50ZVMV' SL 1/16.250.000 — HAI dòng riêng)
SERVICE_FEE_REGRESSION         = PASS ('Chi phí vận chuyển'/'Giá treo Tivi'/
                              'Chi phí lắp đặt' vẫn trong bảng)
RECONCILIATION_RESULT          = PASS trên oracle THẬT (period_2026_01, 226
                              nhóm): Σ quantity=407, Σ total_sales=
                              3.562.310.000, Σ kpi_profit=900.000,
                              Σ kpi_lines=2, Σ lines=351 — khớp EXACT
                              analytics_queries.period_totals() cùng kỳ.
                              Σ(order_count theo mặt hàng)=351 ≠
                              totals["orders"]=254 — đúng cảnh báo mục 17
                              (KHÔNG cộng được).

PERFORMANCE_MEASUREMENT        = PostgreSQL 16 (local, sqlalchemy+psycopg3),
                              12.000 dòng/2.491 nhóm: 81,7/65,4/102,8 ms
                              (3 lần) — KHÔNG freeze SLA, không blocker

BLOCKING_FINDINGS              = 0
SCOPE_DRIFT                    = NO
REPAIR_BATCH_USED               = 1 (tự-review nội bộ — chuyển product_
                              summary() sang tái dụng period_totals() thay
                              vì tự cộng lại các dòng đã gộp; KHÔNG phải
                              repair cycle của Review Budget — chưa có
                              Independent Review nào chạy ở phiên này)

COMPLETION_GATE                 = 12/14 REQUIRED check đã PASS (E1) tại phiên
                              này (CHECK-PRA005-01..12); CHECK-PRA005-13
                              (RECOMMENDED) = NOT_APPLICABLE (DEFERRED);
                              CHECK-PRA005-14 (Independent Review E2) và
                              CHECK-PRA005-15 (Owner Production Acceptance)
                              GIỮ NGUYÊN NOT_TESTED — KHÔNG fabricate.
GOVERNANCE_VALIDATORS           = validate_structure PASS · validate_
                              project_state PASS · validate_evidence PASS
                              (141 REQUIRED PASS evidence) · validate_task_
                              completion PASS (12 DONE task) · validate_
                              reference_integrity FAIL ĐÚNG 3 issue baseline
                              REM-T06 (không phát sinh mới) · git diff
                              --check sạch

IMPLEMENTATION_REVIEW_READY     = YES
CANONICAL_INTEGRATION_STATUS    = NOT_YET_INTEGRATED — ở lại nhánh dedicated
                              chờ Independent Review E2, theo mặc định mục
                              27 Contract (không tích hợp trong phiên
                              implementation trừ khi governance yêu cầu)

NEXT_VERTICAL_ACTION            = PRA-005 INDEPENDENT REVIEW E2
```

Bàn giao chi tiết, oracle verification, và quyết định triển khai đáng ghi
lại: `docs/sessions/S108-pra-005-major-implementation.md`. Completion Gate
cập nhật evidence đầy đủ tại `docs/tasks/TASK-PRA-005-san-pham.md`.


## CANONICAL CURRENT STATE — MANAGEMENT UI SIMPLIFICATION (AUTHORITATIVE, 2026-09-03 — KPI-FIRST PRESENTATION)

**Phân loại: `OWNER_PRESENTATION_DECISION`** — KHÔNG phải PRA-004 defect,
KHÔNG phải accounting model defect, KHÔNG phải yêu cầu PRA-005.
`TASK-PRA-004` giữ nguyên `DONE`, evidence PASS lịch sử KHÔNG bị mở lại.

Owner quyết định: trên management UI mặc định, "Giá vốn kế toán" và "Lợi
nhuận kế toán" không còn là chỉ tiêu quản trị chính. Chỉ tiêu quản trị chính
là PP có hiệu lực tại ngày bán ("Giá mua tham chiếu") và Lợi nhuận KPI theo
PP. `accounting_purchase_price`/`accounting_profit` TIẾP TỤC tồn tại ở
backend (persistence, query layer, audit/reconciliation) — chỉ không còn
render trên `/tong-quan`, `/ban-hang`, `/ban-hang/<order_key>`,
`/nhan-vien?nguon=moi`.

```text
BASE_CANONICAL          = 5f38d5e6e875e5425f6225fe47210475f2b375cb
                         (khớp EXACT kỳ vọng đầu phiên, CANONICAL_MOVED = KHÔNG)
BRANCH                  = claude/kpi-first-ui-simplification-g0sl87

SURFACES_TRACED         = /tong-quan · /ban-hang · /ban-hang/<order_key> ·
                         /nhan-vien?nguon=moi (SỐ MỚI only) — SỐ CŨ/legacy
                         KHÔNG bị chạm (nhánh khác trong nhan_vien.html)

SALES_LIST_CHANGE       = ORDER_COLUMNS (sales_presentation.py) bỏ "LN kế
                         toán"; macro profit_cells (_pipeline_bits.html,
                         dùng chung ban_hang.html + nhan_vien.html SỐ MỚI)
                         chỉ còn kpi_profit
ORDER_DETAIL_CHANGE     = bỏ profit_kpi "Lợi nhuận kế toán" (khối tổng hợp);
                         LINE_COLUMNS bỏ "Giá vốn (kế toán)"/"LN kế toán";
                         "Giá vốn (KPI)" đổi tên "Giá mua tham chiếu" (giá
                         trị KHÔNG đổi, chỉ đổi nhãn — data-metric giữ
                         nguyên "kpi_purchase_price")
TONG_QUAN_CHANGE        = bỏ profit_kpi "Lợi nhuận kế toán"; LN KPI + coverage
                         giữ nguyên
NHAN_VIEN_CHANGE        = EMPLOYEE_COLUMNS (analytics_presentation.py) bỏ
                         "LN kế toán" trên nhánh SỐ MỚI; SỐ CŨ không đổi

REVIEW_REASON_ANALYSIS  = excel_exporter.py:141-149 — status của
                         _PresentedLine = "PENDING" if self.reasons else
                         "AUTO" (dòng 72-73). "Pending.accounting_purchase_
                         price"/"Pending.accounting_profit" là hai trong ba
                         nguồn reason ĐỘC LẬP với "Pending.eligible_kpi_
                         profit" — một dòng có thể bị PENDING CHỈ VÌ thiếu
                         dữ liệu kế toán dù PP/KPI đã đủ điều kiện AUTO.
STATUS_PRESENTATION_MISMATCH = TIỀM ẨN, KHÔNG sửa status engine trong task
                         này. Vì gỡ hai reason "Thiếu giá nhập kế toán"/
                         "Thiếu lợi nhuận kế toán" khỏi UI có thể để lại một
                         dòng CẦN KIỂM TRA không còn lý do management-facing
                         nào hiển thị (nếu đó là hai reason DUY NHẤT của
                         dòng), nên REASON LABELS GIỮ NGUYÊN — beta_
                         presentation.py và sales_presentation.reason_labels
                         KHÔNG bị sửa. Mọi Review reason hiện tại (kể cả hai
                         reason gốc accounting) tiếp tục hiển thị nguyên vẹn.
                         Đây là giới hạn CÓ CHỦ Ý của UI simplification lần
                         này, không phải sai sót.

ACCOUNTING_BACKEND_PRESERVED = YES — không sửa app/modules/, app/pipeline.py,
                         app/history/, tools/db/schema.py; query layer
                         (sales_queries.py, analytics_queries.py) giữ
                         nguyên, vẫn trả accounting_purchase_price/
                         accounting_profit cho tầng trình bày (chỉ không
                         render ra template nữa)
STATUS_SEMANTICS_CHANGED = NO · KPI_FORMULA_CHANGED = NO ·
PP_SEMANTICS_CHANGED    = NO · SCHEMA_CHANGE = NO · TRACKING_CHANGE = NO

FOCUSED_TESTS           = 107 passed (test_sales_presentation.py +
                         test_web_sales_detail.py + test_analytics_
                         presentation.py + test_web_pipeline_analytics.py)
PRA003_TESTS            = PASS (test_analytics_queries.py, test_sales_
                         queries.py, test_web_pipeline_analytics.py)
PRA004_TESTS            = PASS (test_web_sales_detail.py — oracle BH62439/
                         BH62063 giữ nguyên coverage/partial/reasons)
GOLDEN                  = 58 passed, 2 skipped (test_golden_baseline.py) —
                         KHỚP ĐÚNG con số frozen trong CLAUDE.md
FULL_SUITE              = 1966 passed, 11 skipped, 0 failed

CHANGE_BUDGET           = Python production 26 dòng thay đổi (trần 80) ·
                         template 31 dòng thay đổi (trần 100) · CSS 0
                         (trần 20) — KHÔNG vượt ngân sách, KHÔNG
                         SCOPE_EXPANSION_REQUIRED
BLOCKING_FINDINGS       = 0
SCOPE_DRIFT             = NO
PRODUCTION_ORACLE_REGRESSION = PASS (golden/PRA-003/PRA-004 fixture oracles
                         không đổi; BH73844/BH73877 production thật cần
                         Owner visual check sau deploy — không có DB
                         production để verify trực tiếp từ phiên này)

NEXT_VERTICAL_ACTION    = CONTROLLED INTEGRATION → DEPLOY → OWNER VISUAL
                         CHECK → PRA-005 DISCOVERY
```

---

## CANONICAL CURRENT STATE — TASK-PRA-004 (AUTHORITATIVE, 2026-09-03, S104 — OWNER PRODUCTION ACCEPTANCE + FINAL CLOSEOUT)

`TASK-PRA-004` **ĐÃ DONE**. Owner tự mở `/ban-hang?ky=2026-09` trên production
thật (`reports.tinphatcrm.com`) và thực hiện TRỌN VẸN 8 bước nghiệm thu của
mục 21 hợp đồng đã freeze. Bốn con số oracle FROZEN của PRA-003 khớp ĐÚNG
trên production hiện hành: **40 đơn · 61 dòng · 15 AUTO · 25 CẦN KIỂM TRA**.
Owner mở trực tiếp hai đơn thật — `BH73844` (AUTO) và `BH73877` (TRỘN,
CẦN KIỂM TRA) — xác nhận drill-down, coverage một phần, hiển thị lý do bằng
tiếng Việt, và "chưa biết ≠ 0" đều đúng như đã hứa. Đây là trạng thái hiện
hành có thẩm quyền của `TASK-PRA-004`, thay thế khối S103 bên dưới. Khối
`TASK-PRA-003` phía dưới KHÔNG bị khối này thay thế — `TASK-PRA-003` vẫn
`DONE`.

```text
SESSION                    = S104 — PRA-004 Owner Production Acceptance + Final Closeout
TASK-PRA-004                = DONE
BASE_CANONICAL              = eb26f7b9500144290069171fc168926ccb2c70d1
                             (khớp EXACT kỳ vọng đầu phiên, CANONICAL_MOVED = KHÔNG)
TASK_FILE                   = docs/tasks/TASK-PRA-004-ban-hang-review-detail.md
SESSION_FILE                = docs/sessions/S104-pra-004-owner-acceptance-closeout.md

CHECK PASS                  = 14/14  (13/13 REQUIRED + 1/1 RECOMMENDED)
CHECK-PRA004-12              = PASS (E2) — Independent Review E2 (S102)
CHECK-PRA004-14              = PASS (E1) — Owner Production Acceptance Tháng 09/2026 (S104)
repair_cycles_used           = 0 / 1  — Owner evidence completion KHÔNG tiêu repair cycle
BLOCKING_FINDINGS            = 0
OWNER_DECISIONS_REQUIRED     = NONE
SCOPE_DRIFT                  = NO
PRODUCTION_CODE_DELTA        = 0  (đóng gate CHỈ bằng file docs/state)

PRODUCTION_TOTALS (Tháng 09/2026, Owner-observed trên production thật)
  40 đơn · 61 dòng · 15 AUTO · 25 CẦN KIỂM TRA
  15 + 25 = 40  (INV-4, phân hoạch đúng)
  Khớp ĐÚNG oracle FROZEN của PRA-003 (mục 3, mục 20 hợp đồng PRA-004)

BH73844 (AUTO)        : 1 dòng · doanh thu 9.550.000 · LN kế toán = LN KPI =
                         100.000 (coverage 1/1) · không lý do kiểm tra
BH73877 (CẦN KIỂM TRA) : 3 dòng (1 cần kiểm tra + 2 AUTO) · doanh thu
                         32.800.000 · LN kế toán 590.000 (coverage 2/3) ·
                         LN KPI 456.667 (coverage 2/3) · 5 lý do tiếng Việt
                         đọc được trên dòng cần kiểm tra · giá vốn/lợi nhuận
                         thiếu hiện "—", KHÔNG hiện 0

BH62439_ROLE                = TEST_GOLDEN_ORACLE (kỹ thuật, E2 tại CHECK-03/12
                             trên dữ liệu golden persisted) — KHÔNG phải bản
                             ghi production bắt buộc. Vắng mặt trên production
                             09/2026 = EVIDENCE_ROLE_RECONCILIATION, KHÔNG
                             phải lỗi sản phẩm, KHÔNG đổi oracle kỹ thuật.

FINDINGS                    = FIND-PRA004-04, -09 = RECONCILED (S103, không
                             đổi lại). FIND-PRA004-05/06/07/08 = giữ nguyên
                             HARDENING/DEFER với RE-TRIGGER CONDITION đã ghi,
                             KHÔNG mở task mới.

NEXT_VERTICAL_ACTION         = PRA-005 DISCOVERY
```

---

## CANONICAL CURRENT STATE — TASK-PRA-004 (lịch sử, 2026-09-03, S103 — CONTROLLED INTEGRATION)

Phiên triển khai hợp đồng đã freeze tại S100, Independent Review E2 PASS tại
S102, docs reconciliation (`FIND-PRA004-04` + `FIND-PRA004-09`) tại S103.
Vertical Bán hàng + chi tiết đơn/dòng + Review visibility đã CHẠY THẬT trên
fixture golden, nhưng `TASK-PRA-004` **CHƯA DONE**: còn Owner Production
Acceptance. Đây là trạng thái hiện hành có thẩm quyền của `TASK-PRA-004`.
Khối `TASK-PRA-003` phía dưới KHÔNG bị khối này thay thế — `TASK-PRA-003`
vẫn `DONE`.

```text
SESSION                    = S103 — PRA-004 Controlled Integration (docs reconciliation)
IMPLEMENTATION_RESULT      = PASS
TASK-PRA-004               = IN_PROGRESS   (KHÔNG phải DONE)
BASE_CANONICAL             = 8181cebe0619a9c8d12604168a90914c04b3692f
                             (khớp EXACT kỳ vọng, CANONICAL_MOVED = KHÔNG)
FROZEN_CONTRACT_HEAD       = 46a5cdb08bbac77eb4c6a7a3ad483edba988b7f9
                             (khớp EXACT kỳ vọng, CONTRACT_HEAD_MOVED = KHÔNG)
PRA004_BRANCH              = claude/pra-004-sales-review-detail-0b2z4w
TASK_FILE                  = docs/tasks/TASK-PRA-004-ban-hang-review-detail.md
SESSION_FILE               = docs/sessions/S101-pra-004-major-implementation.md

ROUTE MỚI                  = GET /ban-hang · GET /ban-hang/<order_key>
MODULE MỚI                 = app/web/sales_queries.py · app/web/sales_presentation.py
TEMPLATE MỚI               = ban_hang.html · ban_hang_chi_tiet.html
NAVIGATION                 = Option A — MỘT tab "Bán hàng" (Option B vẫn DEFER)

CHANGE_BUDGET  Python production = +282  (MỤC TIÊU 266 · CẢNH BÁO MỀM 330 · DỪNG CỨNG 400)
               Template          = +126  (trần 220)
               CSS               = +10   (trần 25)
               Test              = 89 test mới (sàn 30 · 0 skip mới)
SCHEMA = 0 · MIGRATION = 0 · INDEX = 0 · DEPENDENCY = 0 · CONFIG = 0
TRACKING_CHANGED = NO · INFRASTRUCTURE_CHANGED = NO · PROTECTED_CORE_IMPACT = NONE
PRA-001 / PRA-002 / PRA-003 CHANGED = NO (không một file production hay test nào bị chạm)

CHECK PASS                 = 13/14  (12/13 REQUIRED + 1/1 RECOMMENDED)
CHECK-PRA004-12            = PASS (E2) — Independent Review E2 ĐÃ CHẠY (S102)
CHECK-PRA004-14            = NOT_TESTED — Owner Production Acceptance Tháng 09/2026
repair_cycles_used         = 0 / 1  — implement, review VÀ reconciliation đều KHÔNG tiêu cycle
BLOCKING_FINDINGS          = 0
OWNER_DECISIONS_REQUIRED   = NONE
SCOPE_DRIFT                = NO
DOCS_RECONCILIATION        = XONG (S103) — FIND-PRA004-04 + FIND-PRA004-09
NEXT_VERTICAL_ACTION       = FAST-FORWARD CANONICAL → DEPLOY → OWNER PRODUCTION ACCEPTANCE
```

### Docs Reconciliation — ĐÃ CHẠY (S103, 2026-09-03)

```text
RECONCILED           = FIND-PRA004-04, FIND-PRA004-09
CLASSIFICATION        = DOC_INCONSISTENCY_RECONCILED (cả hai)
SEMANTIC_CONTRACT_DELTA = 0
PRODUCTION_DELTA_AFTER_E2 = 0  (chỉ 1 file docs bị chạm: task file)
repair_cycles_used    = 0 / 1  (KHÔNG tiêu — không phải blocking defect)
```

`FIND-PRA004-04`: header Completion Gate (dòng 1148) "13 check: 11 REQUIRED
· 2 RECOMMENDED" → "14 check: 13 REQUIRED · 1 RECOMMENDED"; Exit Criteria số
1 "11/11 REQUIRED" → "13/13 REQUIRED". Xác minh: 14 dòng `Yêu cầu:` giữa bản
FROZEN và bản đã sửa = IDENTICAL; `Priority` = 13 REQUIRED · 1 RECOMMENDED ở
CẢ HAI; mục 20.5 (bất biến), mục 3 (Owner decisions), mục 19 (Hard
Exclusions) = IDENTICAL.

`FIND-PRA004-09`: văn bản `Yêu cầu:` của CHECK-PRA004-12 và CHECK-PRA004-13
đã bị đặt nhầm khối trong S101 — trả về đúng khối của từng check;
`Executed By:` của CHECK-12 sửa từ "Session S101" thành "Session S102 —
TASK-PRA-004 Independent Review E2". Không đổi `Priority`, không đổi
`Evidence Level`, không đổi nội dung `Yêu cầu:` của bất kỳ check nào.

Chi tiết đầy đủ: `docs/reviews/TASK-PRA-004-INDEPENDENT-REVIEW-RECORD.md`.

### Independent Review E2 — ĐÃ CHẠY (S102, 2026-09-03)

```text
REVIEW_RESULT       = E2 PASS
FINAL_DECISION      = ACCEPT_WITH_NON_BLOCKING_FINDINGS
BASE_SHA            = 8181cebe0619a9c8d12604168a90914c04b3692f   ✓ KHỚP
CONTRACT_SHA        = 46a5cdb08bbac77eb4c6a7a3ad483edba988b7f9   ✓ KHỚP
REVIEW_TARGET_SHA   = 6a23c328788af254104b335c80d7091b8c8e8163   ✓ KHỚP
TARGET_MOVED        = KHÔNG        CANONICAL_MOVED = KHÔNG
CHECK-PRA004-12     = PASS         CHECK-PRA004-14 = NOT_TESTED (KHÔNG đụng)
BLOCKING_FINDINGS   = 0
NON_BLOCKING        = 6  (FIND-PRA004-04 xác nhận · 05 · 06 · 07 · 08 · 09 mới)
repair_cycles_used  = 0 / 1
Artifact            = docs/reviews/TASK-PRA-004-INDEPENDENT-REVIEW-RECORD.md
```

Reviewer RECOMPUTE ĐỘC LẬP bằng SQL THÔ (`sqlalchemy.text()`, KHÔNG qua
`sales_queries`): danh sách đơn golden khớp `sales_queries` **0 lệch** trên
254 đơn × 9 trường; `BH62439` đọc thẳng persisted rows khớp TRỌN VẸN Oracle C
(4 dòng · CẦN KIỂM TRA · 66.000.000 · LN kế toán 500.000 coverage 1/4 · LN
KPI 400.000 coverage 1/4 · ba dòng PENDING mỗi dòng ĐÚNG 5 mã lý do đúng thứ
tự · mọi giá vốn/lợi nhuận `NULL`). INV-1…INV-7: 0 vi phạm. Vũ trụ reason
code reviewer TỰ dẫn xuất = ĐÚNG 21 mã, bảng nhãn phủ TOÀN PHẦN. PII kiểm
theo GIÁ TRỊ bằng sentinel trên HTML thật: 0 giá trị cấm. CHỈ-ĐỌC chứng minh
bằng AST + hash 4 bảng trước/sau 7 lượt GET (không một byte đổi). Đối chiếu
kỳ với Tổng quan: KHỚP HOÀN TOÀN trên "Toàn bộ dữ liệu", "Tháng 01/2026" và
tháng rỗng. Golden Baseline `58 passed, 2 skipped`; full suite 1962 passed /
11 skipped so với baseline `8181ceb` 1873 / 11 (+89 = đúng số test mới).
Budget đo lại: Python 226 · template 132 · CSS 13 · 85 test — dưới MỌI biên.

**Finding mới của phiên review** (chi tiết đầy đủ + RE-TRIGGER CONDITION trong
artifact): `FIND-PRA004-05` (docstring `_line()` nói sai — `{**row, …}` mở gói
TRƯỚC `row.pop()` nên `pending_reasons_json` còn lại trong dict tầng truy vấn;
KHÔNG tới template, không PII, `HARDENING`/DEFER) · `FIND-PRA004-06` (tử số
coverage KPI đếm dòng AUTO — ngữ nghĩa TÁI DỤNG NGUYÊN VẸN từ PRA-003, đổi sẽ
vỡ `CHECK-PRA004-07`, DEFER) · `FIND-PRA004-07` (trang danh sách 3,7 MB ở mốc
4.000 đơn, vẫn dưới ngưỡng RE-TRIGGER 3 giây, DEFER) · `FIND-PRA004-08` (ổn
định thứ tự dòng khi `SOURCE_CHANGED`, không hệ quả nghiệp vụ, DEFER) ·
`FIND-PRA004-09` (`DOC_INCONSISTENCY` — văn bản `Yêu cầu:` của CHECK-12 và
CHECK-13 bị đặt nhầm khối trong file task, `Executed By:` của CHECK-12 ghi
S101; bản FROZEN `46a5cdb` NGUYÊN VẸN; gộp vào cùng lần docs reconciliation
với `FIND-PRA004-04`).

`FIND-PRA004-04` — reviewer ĐẾM ĐỘC LẬP các check trong chính bản FROZEN và
XÁC NHẬN phân loại **A. `DOC_INCONSISTENCY`**, KHÔNG phải
`CONTRACT_SEMANTIC_CHANGE`: cả 14 check đã tồn tại đầy đủ trong `46a5cdb`,
`diff` 14 dòng `Yêu cầu:` = IDENTICAL, `Priority` = 13 REQUIRED · 1
RECOMMENDED ở CẢ HAI bản. Chỉ con số TÓM TẮT sai ⟹ **KHÔNG tiêu repair
cycle**; sửa một lần ở khâu chuẩn bị Controlled Integration.

### Vertical đã chạy thật

Đường truy vết mà `TASK-PRA-004` tồn tại để dựng đã hoạt động đầu-cuối trên
fixture golden `period_2026_01`, khẳng định trên HTML THẬT:

```text
Tổng quan → Bán hàng (254 đơn) → mở BH62439 → 4 dòng hiện hành
          → 1 AUTO + 3 CẦN KIỂM TRA → 5 lý do tiếng Việt cho mỗi dòng PENDING
```

Ca TRỘN `BH62439` — oracle quan trọng nhất của hợp đồng — render ĐÚNG:

```text
Trạng thái   : CẦN KIỂM TRA   (dù chứa 1 dòng AUTO)
Doanh thu    : 66.000.000
LN kế toán   : 500.000   coverage 1 / 4 dòng   ← coverage MỘT PHẦN
LN KPI       : 400.000   coverage 1 / 4 dòng   ← coverage MỘT PHẦN
Ba dòng PENDING: mọi giá vốn và mọi lợi nhuận hiện "—", KHÔNG BAO GIỜ 0
Cảnh báo     : trang nói thẳng rằng con số này KHÔNG phải lợi nhuận toàn đơn
```

### Bằng chứng kiểm thử

```text
Focused PRA-004  : 89 passed in 6.55s
PRA-003          : 67 passed in 7.07s  (3 file test KHÔNG bị sửa một dòng nào)
Golden Baseline  : 58 passed, 2 skipped in 6.45s
FULL SUITE       : 1962 passed, 11 skipped in 78.83s
Baseline 8181ceb : 1873 passed, 11 skipped in 77.08s  (đo lại bằng git worktree)
                   → chênh +89 = ĐÚNG số test mới; số skip KHÔNG đổi
CHECK-PRA004-13  : 4000 đơn / 12.000 dòng · order_list = 85,2 ms
                   (ngưỡng RE-TRIGGER 3 giây ⟹ KHÔNG thêm pagination)

GOVERNANCE STRUCTURE : PASS      PROJECT STATE   : PASS
EVIDENCE VALIDATION  : PASS      TASK COMPLETION : PASS
REFERENCE INTEGRITY  : FAIL — ĐÚNG 3 issue REM-T06 pre-existing, KHÔNG thêm mới
git diff --check     : sạch trên DẢI COMMIT 8181cebe..HEAD
branch authority     : AUTHORITY_OK · DIVERGENCE = WITHIN_LIMITS
```

### Ranh giới đã giữ

- **CHỈ-ĐỌC tuyệt đối** — chứng minh bằng AST trên `app/web/sales_queries.py`,
  không phải bằng grep chuỗi: không import `insert`/`update`/`delete`/`text`,
  không gọi `begin`/`commit`/`execution_options`. SQLAlchemy 2.0 không
  autocommit ⟹ đường ghi KHÔNG TỒN TẠI.
- **Ranh giới PII riêng của PRA-004** — `sales_queries` không tham chiếu
  `.c.imei`/`.c.note_raw`/`.c.employee_raw`/`.c.customer`/`.c.phone`/
  `.c.address`; `product_raw` CỐ Ý nằm ngoài hàng rào (REQUIRED_NOW, mục
  14.4). Gate PII của PRA-003 tiếp tục PASS NGUYÊN VẸN, KHÔNG bị sửa.
- **Không trạng thái mới** — đúng hai nhãn `AUTO` / `CẦN KIỂM TRA`.
- **Không taxonomy reason mới** — `REASON_DISPLAY_LABELS` chỉ được THÊM key
  để phủ trọn vũ trụ ĐÓNG 21 mã; 7 nhãn S069 giữ NGUYÊN TỪNG CHỮ.

### Finding mới của phiên

`FIND-PRA004-04` — `DOC_INCONSISTENCY` · KHÔNG BLOCKING · **KHÔNG tự sửa**.
Header Completion Gate của file task viết "13 check: 11 REQUIRED · 2
RECOMMENDED" trong khi phần liệt kê có 14 check (13 REQUIRED · 1 RECOMMENDED);
Exit Criteria số 1 viết "11/11 REQUIRED". Sai lệch SỐ ĐẾM trong tài liệu, KHÔNG
phải check bị thiếu hay bị làm yếu — cả 14 check đều còn nguyên. Phiên
implement không sửa vì đó là phần đã FROZEN, phải đi qua
`COMPLETION GATE CHANGE PROPOSAL`. RE-TRIGGER: giải quyết TRƯỚC khi đóng
`TASK-PRA-004` = DONE. Chi tiết:
`docs/sessions/S101-pra-004-major-implementation.md`.

`FIND-PRA004-01` / `-02` / `-03` của S100 giữ nguyên trạng thái đã ghi
(`-02` đã giải bằng thiết kế; `-01` và `-03` vẫn DEFER với RE-TRIGGER
CONDITION nguyên vẹn).

### Việc KHÔNG được làm tiếp

Independent Review E2 ĐÃ xong (`CHECK-PRA004-12 = PASS`). Vẫn KHÔNG tích hợp
vào canonical trong phiên review, KHÔNG deploy, KHÔNG Owner production
acceptance (`CHECK-PRA004-14` giữ `NOT_TESTED`). Không mở PRA-005, không
pagination, không review workflow. Không repair REM-T06 hay FIND-PRA003-03.

VIỆC TIẾP THEO = **`CONTROLLED INTEGRATION`** — trong khâu chuẩn bị, thực
hiện **MỘT** lần docs reconciliation gộp `FIND-PRA004-04` (header Completion
Gate + Exit Criteria số 1) và `FIND-PRA004-09` (trả văn bản `Yêu cầu:` của
CHECK-12/CHECK-13 về đúng khối, sửa `Executed By:` của CHECK-12). Việc này
KHÔNG tiêu repair cycle. Sau đó: **`DEPLOY`** → **`OWNER PRODUCTION
ACCEPTANCE Tháng 09/2026`** (`CHECK-PRA004-14`, Owner tự thực hiện trọn vẹn 8
bước của contract mục 21; bốn con số 40 / 15 / 25 / 61 phải khớp ĐÚNG).

---

## CANONICAL CURRENT STATE — TASK-PRA-004 (lịch sử, 2026-09-03, S100 — DISCOVERY + VERTICAL CONTRACT FREEZE)

Phiên discovery cho vertical slice tiếp theo (Bán hàng + chi tiết đơn/dòng +
Review visibility). Contract đã FREEZE, task = `READY`. Trạng thái hiện hành
có thẩm quyền của `TASK-PRA-004` nằm ở khối S101 phía TRÊN; khối này là bản
ghi lịch sử của phiên freeze contract. Khối `TASK-PRA-003` bên dưới KHÔNG bị
khối này thay thế — `TASK-PRA-003` vẫn `DONE`.

```text
SESSION                    = S100 — PRA-004 Discovery + Vertical Contract Freeze (docs-only)
DISCOVERY_RESULT           = CONTRACT_FROZEN
TASK-PRA-004               = READY
CANONICAL_BEFORE           = 8181cebe0619a9c8d12604168a90914c04b3692f
                             (khớp EXACT kỳ vọng, CANONICAL_MOVED = KHÔNG)
PRA004_BRANCH              = claude/pra-004-sales-review-detail-0b2z4w
                             (tạo từ ĐÚNG canonical trên, KHÔNG dùng main)
TASK_FILE                  = docs/tasks/TASK-PRA-004-ban-hang-review-detail.md
SESSION_FILE               = docs/sessions/S100-pra-004-ban-hang-review-detail-discovery.md

PRODUCTION_CODE_DELTA      = 0 — phiên này CHỈ sửa docs/state
SCHEMA = 0 · MIGRATION = 0 · INDEX = 0 · DEPENDENCY = 0 · CONFIG = 0
TRACKING_CHANGED = NO · INFRASTRUCTURE_CHANGED = NO · PROTECTED_CORE_IMPACT = NONE
PRA-001 / PRA-002 / PRA-003 CHANGED = NO (không một file production hay test nào bị chạm)

BLOCKING_FINDINGS          = 0
OWNER_DECISIONS_REQUIRED   = NONE
SCOPE_DRIFT                = NO
IMPLEMENTATION_READY       = YES
NEXT_VERTICAL_ACTION       = PRA-004 MAJOR IMPLEMENTATION
```

### Câu trả lời discovery quan trọng nhất — Review reason ĐỦ để trình bày

Câu hỏi chặn của §6 chỉ thị PRA-004 ("hiện tại Reports có lưu đủ dữ liệu
authoritative để giải thích lý do PENDING/Review không?") — **CÓ**. Toàn bộ
`FACT`, đo trong phiên này:

```text
Vị trí        : order_line_result_version.pending_reasons_json
Phía          : RESULT (không phải source)
Current ptr   : current_result_version_id (nullable=False)
Nhiều reason/dòng : CÓ — đo được 5 hoặc 6 reason trên một dòng
Dạng          : MÃ NGỮ NGHĨA ỔN ĐỊNH, vũ trụ ĐÓNG ≤ 21 mã
                (10 PriceResolutionReason ∪ 8 validation CATEGORIES ∪ 3 Pending.<field>)
PII / chẩn đoán nội bộ : KHÔNG — `details` (văn xuôi có số dòng nguồn,
                order_id, thông điệp chẩn đoán) KHÔNG được persist; chỉ
                `reasons` đi vào JSON (app/web/history_store.py:662)
Thẩm quyền trình bày : ĐÃ TỒN TẠI và ĐANG CHẠY PRODUCTION —
                app/beta_presentation.py::REASON_DISPLAY_LABELS (S069,
                dùng bởi Owner Launcher + trang /). PRA-004 TÁI DỤNG và chỉ
                MỞ RỘNG cho 14 mã còn thiếu. KHÔNG xây taxonomy mới.
```

⟹ KHÔNG mở subsystem mới. KHÔNG BLOCKING.

### Đo được trên fixture golden `period_2026_01` (E1, đường production thật)

Chạy `run_import_production` → `present_lines` → `extraction.build_*_lines` →
`history_writer.write_run_history`, rồi truy vấn SQL trên dữ liệu đã persist:

```text
351 dòng · 254 đơn
Q1 danh sách 254 đơn (1 câu SQL, GROUP BY order_key) : 6,6 ms
Q2 chi tiết đơn BH62439 (4 dòng)                     : 1,3 ms

Đơn TOÀN AUTO        : 1   (BH62063)      Đơn CẦN KIỂM TRA : 253
Đơn TRỘN AUTO+PENDING: 1   (BH62439)      Đơn nhiều ngày bán: 0
Phân bố số dòng/đơn  : {1:191, 2:41, 3:16, 4:3, 5:1, 6:1, 7:1} → Σ = 351

Coverage / 351 dòng:
  total_sales 351 · employee_normalized 351 · product_group_final 351
  accounting_purchase_price 2 · kpi_purchase_price 2
  accounting_profit 2 · eligible_kpi_profit 2
  canonical_product_code 0   ← KHÔNG dùng được làm tên sản phẩm
  product_raw rỗng 0/351     ← dùng được trên MỌI dòng

Reason codes: IDENTITY_SOURCES_UNAVAILABLE 349 · Missing.PurchasePrice 349 ·
  Pending.accounting_purchase_price 349 · Pending.accounting_profit 349 ·
  Pending.eligible_kpi_profit 349 · Suspicious 8
  Số reason/dòng: {0: 2 dòng, 5: 341 dòng, 6: 8 dòng}
```

### Acceptance Oracle đã FREEZE (độc lập, đo lại được)

```text
O-A  254 đơn · 351 dòng · 1 đơn AUTO · 253 đơn cần kiểm tra
     auto_orders + review_orders = 254 = COUNT(DISTINCT order_key)
O-B  BH62063 — AUTO thuần, 1 dòng, net 7.500.000,
     LN kế toán 500.000 (1/1), LN KPI 500.000 (1/1), reasons = []
O-C  BH62439 — TRỘN (1 AUTO + 3 PENDING) ⟹ đơn = CẦN KIỂM TRA
     4 dòng · SL 5 · net 66.000.000
     LN kế toán 500.000 coverage 1/4 dòng   ← COVERAGE MỘT PHẦN
     LN KPI     400.000 coverage 1/4 dòng
     3 dòng PENDING mỗi dòng ĐÚNG 5 mã lý do, mọi giá vốn/lợi nhuận = NULL ⟹ "—"
O-D  Vũ trụ reason code ĐÓNG ≤ 21 mã; bảng nhãn phủ TOÀN PHẦN;
     7 nhãn S069 giữ NGUYÊN TỪNG CHỮ
INV-1…INV-7  bất biến an toàn thắng mọi literal (mục 20.5 file task)
```

`BH62439` là oracle quan trọng nhất: nó bắt CẢ HAI failure path của Blast
Radius trong một đơn — trạng thái TRỘN (đơn phải là CẦN KIỂM TRA dù có dòng
AUTO) và coverage MỘT PHẦN (lợi nhuận 500.000 chỉ phủ 1/4 dòng của một đơn
66 triệu).

### Quyết định kiến trúc

```text
PAGINATION          = KHÔNG (254 đơn / 6,6 ms; production 09/2026 = 40 đơn).
                      Thay vào đó CHECK-PRA004-13 ĐO trên ≥12k dòng kèm
                      RE-TRIGGER CONDITION (> 3 giây ⟹ pagination thành REQUIRED)
SCHEMA / MIGRATION  = 0. Mọi trường đã persisted; `order_key` là cột DẪN ĐẦU
                      của PK `order_line_current` ⟹ đã index;
                      `ix_order_line_current_sale_date` đã tồn tại
PRODUCTION WRITE    = KHÔNG · TRACKING DEPENDENCY = KHÔNG · DEPENDENCY MỚI = 0
NAVIGATION          = Option A (một tab "Bán hàng"). Option B (bấm ô số trên
                      Tổng quan) = USEFUL_BUT_DEFER, KHÔNG triển khai
SOURCE SEPARATION   = SỐ MỚI ONLY, bảo đảm bằng CheckConstraint(origin) × 3 bảng
PII                 = customer/phone/address/shipper_raw KHÔNG tồn tại như cột
                      trong schema ⟹ không thể rò rỉ (bảo đảm CẤU TRÚC).
                      imei · note_raw · employee_raw · source_profit = PROHIBITED.
                      product_raw = REQUIRED_NOW (anonymize.py xếp là dữ liệu
                      nghiệp vụ, giữ nguyên văn trong fixture)
```

### Findings (không cái nào BLOCKING)

```text
FIND-PRA004-01 TRUTHFULNESS_CONSTRAINT — chỉ 2 dòng AUTO trong fixture và cả
  hai đều delivery_cost = NULL (trong khi 325/351 dòng CÓ delivery_cost), nên
  KHÔNG chứng minh được lợi nhuận luôn dẫn xuất từ (SL, đơn giá, chiết khấu,
  giá vốn). Xử lý ĐÃ đưa vào contract: trang KHÔNG in công thức, KHÔNG tuyên
  bố tự dẫn xuất; delivery_cost = USEFUL_BUT_DEFER kèm RE-TRIGGER CONDITION.

FIND-PRA004-02 DOC_INCONSISTENCY — analytics_queries.py (docstring) xếp
  `product_raw` chung nhóm PII và test PRA-003 canh điều đó, trong khi
  tests/fixtures/golden/anonymize.py (đo trên workbook production thật, GB-3
  / OD-GB-1) xếp nó là dữ liệu nghiệp vụ. Giải bằng THIẾT KẾ, KHÔNG nới gate:
  PRA-004 tạo module truy vấn RIÊNG với hàng rào PII riêng, KHÔNG chạm
  analytics_queries.py và KHÔNG sửa test nào của PRA-003.

FIND-PRA004-03 HARDENING — "0 đơn nhiều nhân viên" trên fixture là ARTEFACT
  của ẩn danh hoá (mọi dòng mang cùng một surrogate), KHÔNG phải bằng chứng
  về production. Contract vẫn thiết kế cho n ≥ 1 và CẤM lấy nhân viên của
  dòng đầu tiên. RE-TRIGGER: khi production lần đầu có một đơn mà các dòng
  mang từ hai employee_normalized trở lên.
```

### Ngân sách

```text
Python production : mục tiêu 266 · cảnh báo mềm 330 · DỪNG CỨNG 400
Template ≤ 220 · CSS ≤ 25 · Test ≥ 30 (0 skip mới)
Review budget     : MEDIUM = 1 blocking repair cycle · 1 Independent Review E2
                    repair_cycles_used 0 / 1 — phiên discovery KHÔNG tiêu cycle
Completion Gate   : FROZEN — 11 REQUIRED + 2 RECOMMENDED
```

### VALIDATORS (E1, phiên này)

```text
validate_structure       : GOVERNANCE STRUCTURE: PASS · Deployment root: PASS · 21 required paths
validate_project_state   : PROJECT STATE: PASS
validate_evidence        : EVIDENCE VALIDATION: PASS
validate_task_completion : TASK COMPLETION: PASS
git diff --check         : sạch (không output)
branch_authority_check   : DEFAULT_TIP = HEAD_SHA = 8181cebe...; nhánh phiên chưa
                           có upstream ở thời điểm chạy — giải quyết bằng chính
                           lần push của phiên này
reference_integrity      : KHÔNG chạy repair — 3 issue REM-T06 pre-existing giữ nguyên
```

### Việc phiên này KHÔNG làm

Không viết production code. Không sửa schema/migration/index. Không thêm
dependency vào `pyproject.toml`. Không sửa `analytics_queries.py`,
`analytics_presentation.py`, hay bất kỳ test nào của PRA-003. Không sửa
`tests/fixtures/golden/**`. Không upload workbook mới. Không truy vấn
PostgreSQL production. Không deploy. Không tích hợp canonical. Không đánh dấu
PRA-004 DONE. Không repair REM-T06 hay FIND-PRA003-03. Không mở PRA-005.

VIỆC TIẾP THEO = `PRA-004 MAJOR IMPLEMENTATION`. Thứ tự bắt buộc:
`sales_queries` → mở rộng `REASON_DISPLAY_LABELS` → `sales_presentation` →
hai route → hai template → CSS. Test đơn vị viết TRƯỚC test route và
integration.

---

## CANONICAL CURRENT STATE — TASK-PRA-003 (AUTHORITATIVE, 2026-09-03, S099 — OWNER PRODUCTION ACCEPTANCE + TASK CLOSEOUT) — TASK-PRA-003 = DONE

Owner đã tự tay nghiệm thu `CHECK-PRA003-07` trên production thật (Tháng
09/2026). Toàn bộ 12/12 check REQUIRED nay PASS. Đây là trạng thái hiện hành
có thẩm quyền của `TASK-PRA-003`; khối S098 ngay bên dưới là bản ghi lịch sử
đúng của phiên đối chiếu tài liệu + tích hợp. Khối `TASK-PRA-002` phía dưới
KHÔNG bị khối này thay thế.

```text
SESSION                    = S099 — PRA-003 Owner Production Acceptance + Task Closeout
TASK-PRA-003               = DONE
CANONICAL_BEFORE           = d368b2d21a21dbb92b59d2676061b10938b2a9de (khớp kỳ vọng, không moved)
CHECK-PRA003-07            = PASS — Owner Production Acceptance (E1)

FROZEN_EXPECTED (oracle O-G, khớp ĐÚNG):
  Tổng đơn = 40 · Số dòng hàng = 61 · AUTO = 15 · Cần kiểm tra = 25
  So tháng trước = TRỐNG/"—" kèm "chưa có dữ liệu kỳ trước", KHÔNG 0%

OBSERVED_ONLY (Owner đọc trên production 2026-09-03 — KHÔNG phải oracle đặt
trước, KHÔNG viết ngược thành kỳ vọng mới trong task file):
  Tổng số lượng      = 71
  Doanh thu (net)    = 593.550.000 VND
  Lợi nhuận KPI      = 8.936.667 VND    coverage 32/61 dòng
  Lợi nhuận kế toán  = 8.085.000 VND    coverage 35/61 dòng
  Dòng chưa có ngày bán = 0

Tách nguồn (Owner quan sát trực tiếp): /nhan-vien không tham số → SỐ CŨ,
LEG-20260902-4ffe5198 (Báo cáo Kinh doanh 2026.xlsx, Tháng 08/2026) vẫn đọc
được nguyên vẹn; SỐ CŨ/SỐ MỚI phân biệt tường minh, không cộng chung.

CHECK MATRIX (sau closeout)
  01 PASS  02 PASS  03 PASS  04 PASS  05 PASS  06 PASS
  07 PASS  08 PASS  09 PASS  10 PASS  11 PASS  12 PASS   (12/12 REQUIRED)
  13 PASS  14 PASS                                        (2/2 RECOMMENDED)

EXIT CRITERIA (mục cuối task file) — cả 8 điều đã thoả:
  1. 12/12 REQUIRED PASS với evidence level bắt buộc          ✓
  2. 0 BLOCKING; HARDENING (FIND-03) có RE-TRIGGER CONDITION   ✓
  3. CHANGE_BUDGET (284/191/16) dưới DỪNG CỨNG                 ✓
  4. Review budget 0/1 — chưa vượt                             ✓
  5. Golden 58 passed 2 skipped; full suite không giảm;
     validators giữ nguyên baseline (3 issue REM-T06 đã biết)  ✓
  6. PROJECT_PROGRESS.md + REVIEW_BUDGET_LEDGER.md đã cập nhật ✓ (phiên này)
  7. Session handoff đã viết (MAJOR)                           ✓ (docs/sessions/S099-*.md)
  8. SCHEMA=0 · MIGRATION=0 · DEPENDENCY=0 · TRACKING=NO ·
     INFRASTRUCTURE=NO · PROTECTED_CORE_IMPACT=NONE             ✓

BLOCKING_FINDINGS   = 0
NON_BLOCKING        = FIND-PRA003-01 CONTRACT_MISMATCH — đã đối chiếu tài liệu (S098)
                      FIND-PRA003-02 EVIDENCE_DEFECT — đã đối chiếu tài liệu (S098)
                      FIND-PRA003-03 HARDENING — DEFER/RECORD ONLY, RE-TRIGGER CONDITION
                      giữ nguyên trong docs/reviews/TASK-PRA-003-INDEPENDENT-REVIEW-RECORD.md
CHANGE_BUDGET       = Python 284 · template 191 · CSS 16 — KHÔNG đổi (closeout = 0 LOC)
REVIEW_BUDGET       = repair_cycles_used 0 / 1 — closeout KHÔNG tiêu cycle

PRODUCTION_CODE_DELTA (phiên này) = 0 — chỉ sửa docs/state
Không upload workbook mới, không query PostgreSQL, không inspect R2/Render
Metrics, không restart, không repair REM-T06/FIND-03, không mở PRA-004/005.

VIỆC TIẾP THEO      = PRA-004 — Bán hàng + Review/detail (chưa mở trong
                      phiên này).
```

---

## CANONICAL CURRENT STATE — TASK-PRA-003 (lịch sử, 2026-09-03, S098 — NON-BLOCKING DOC RECONCILIATION + CONTROLLED INTEGRATION)

Sau Independent Review E2 (S097, `ACCEPT_WITH_NON_BLOCKING_FINDINGS`), phiên
này (a) đối chiếu tài liệu cho hai finding non-blocking KHÔNG cần repair cycle,
rồi (b) tích hợp nhánh đã accept vào canonical bằng fast-forward THUẦN TUÝ. Đây
là BẢN GHI LỊCH SỬ đúng của phiên đối chiếu + tích hợp — trạng thái hiện hành
có thẩm quyền của `TASK-PRA-003` nằm ở khối S099 phía TRÊN. Khối `TASK-PRA-002`
phía dưới KHÔNG bị khối này thay thế.

```text
SESSION                    = S098 — PRA-003 Doc Reconciliation + Controlled Integration
FIND-PRA003-01             = ĐỐI CHIẾU TÀI LIỆU (KHÔNG repair) — xem bên dưới
FIND-PRA003-02             = ĐỐI CHIẾU TÀI LIỆU (KHÔNG repair) — xem bên dưới
FIND-PRA003-03             = DEFER / RECORD ONLY — không sửa, không mở task
repair_cycles_used         = 0 / 1  (đối chiếu tài liệu KHÔNG tiêu repair cycle)
INTEGRATION_RESULT         = PASS (fast-forward thuần tuý, không merge/squash/rebase)
CANONICAL_BEFORE           = facf090c782b022730ecc5f1cf0d0b02e29ca8d7
FINAL_ACCEPTED_HEAD        = chính commit đối chiếu tài liệu này (SHA in trong
                             commit message + tại git log claude/extract-upload-repo-gq2ws4
                             sau fast-forward)
TASK-PRA-003               = IN_PROGRESS — CHỜ CHECK-PRA003-07 (Owner nghiệm thu production)
```

### FIND-PRA003-01 — đối chiếu tài liệu (không phải repair)

Minh hoạ số học literal của oracle O-C (mục 16 file task) gây hiểu nhầm: nó
viết `coverage 0/351` như thể đó là con số DUY NHẤT đúng, trong khi có HAI
ngữ cảnh thực thi trên cùng fixture golden — `0/351` thuộc đường sinh golden
TRẦN (`build_expected.py` gọi `run_import()` không nạp registry), `2/351`
thuộc đường giống production mà PRA-003 thực sự đọc (`run_import_production`).
Đã sửa: thêm footnote `[^oc-context]` ngay dưới bảng Acceptance Oracle, nói rõ
CẢ HAI con số đều đúng cho ngữ cảnh của mình, và bất biến CÓ THẨM QUYỀN của
O-C là tính chất an toàn `NULL ≠ 0` (lợi nhuận thiếu/không đủ điều kiện PHẢI
hiện `—`, không bao giờ `0`) — không phải một literal cụ thể nào.

KHÔNG đổi: Owner Decision D1–D3, implementation, fixture, expected JSON,
`Yêu cầu:` gốc của `CHECK-PRA003-03`/`CHECK-PRA003-04` (văn bản gate FROZEN
tại S095), hay bất kỳ business semantics nào. Đây là làm rõ ngữ cảnh thực thi,
không phải thiết kế lại contract.

### FIND-PRA003-02 — đối chiếu tài liệu (không phải repair)

`git diff --check` trên dải commit `facf090..bb5b63a` có đúng 1 trailing
whitespace: `docs/sessions/S094-pra-003-vertical-slice-discovery.md:341`. Đã
xoá khoảng trắng cuối dòng đó — KHÔNG dọn định dạng nào khác trong file. Xác
nhận lại: `git diff --check` trên working tree sạch (không output).

### FIND-PRA003-03 — DEFER, không sửa

Một `employee_normalized` mang nhiều `employee_group` trong cùng kỳ sẽ hiện
thành nhiều dòng cùng tên trên bảng Nhân viên; bất biến cộng được VẪN đúng
(đã kiểm chứng ở Independent Review S097). Phiên này KHÔNG sửa grouping
semantics, KHÔNG mở task, chỉ ghi nhận RE-TRIGGER CONDITION đã có trong
`docs/reviews/TASK-PRA-003-INDEPENDENT-REVIEW-RECORD.md`: kích hoạt lại khi
dữ liệu thật lần đầu có một nhân viên mang hai nhóm trong cùng kỳ.

### Verify Accepted Production Delta (facf090 → final accepted HEAD)

```
18 file: 2 module Python mới (analytics_queries, analytics_presentation) +
2 template mới (tong_quan.html, _pipeline_bits.html) + 4 file sửa
(server.py, nhan_vien.html, layout.html, tinphat-ui.css) + 3 file test mới +
docs (task/session/review/progress/ledger)

Tracking = 0     schema = 0     migration = 0     index = 0
dependency = 0   config = 0     infrastructure = 0
protected persistence/reconciliation core (app/history/**, history_store.py,
history_writer.py, run_registry.py, storage_backend.py, app/modules/**,
app/pipeline.py, app/composition.py) = KHÔNG đổi
```

### Change Budget (đo lại sau đối chiếu tài liệu)

```
Python production = 284   (mục tiêu 255 · cảnh báo mềm 320 · DỪNG CỨNG 400) → TRONG NGƯỠNG
Template           = 191   (trần 220) ✓
CSS                =  16   (trần  25) ✓
Đối chiếu tài liệu thêm 0 dòng Python/template/CSS production — chỉ docs.
```

### Fast-Forward Integration

```
Phương pháp bắt buộc : PURE FAST-FORWARD ONLY
Nhánh nguồn           : claude/pra-003-roadmap-finalization-di33bn (sau đối chiếu tài liệu)
Nhánh đích             : claude/extract-upload-repo-gq2ws4 (canonical)
merge commit / squash / cherry-pick / rebase / force-push = KHÔNG dùng cái nào
```

VIỆC TIẾP THEO = Deploy canonical (nếu chưa) và thực hiện tối thiểu quy trình
Owner nghiệm thu production cho `CHECK-PRA003-07` (mở `/tong-quan`, chọn
"Tháng 09/2026", đọc và ghi lại các giá trị thật). Phiên này KHÔNG deploy,
KHÔNG đánh dấu CHECK-07 PASS, KHÔNG đánh dấu task DONE.

---

## CANONICAL CURRENT STATE — TASK-PRA-003 (lịch sử, 2026-09-03, S097 — INDEPENDENT REVIEW E2)

Phiên reviewer ĐỘC LẬP đã chạy lại toàn bộ và ra quyết định. Đây là BẢN GHI
LỊCH SỬ đúng của phiên review — trạng thái hiện hành có thẩm quyền của
`TASK-PRA-003` nằm ở khối S098 phía TRÊN; khối S096 bên dưới là bản ghi lịch
sử của phiên implement.

```text
SESSION                    = S097 — PRA-003 Independent Review E2 (docs-only)
REVIEW_RESULT              = ACCEPT_WITH_NON_BLOCKING_FINDINGS
TASK-PRA-003               = IN_PROGRESS — review ĐÃ ACCEPT, CHỜ Controlled Integration
                             (KHÔNG phải DONE: còn CHECK-07 — Owner nghiệm thu production)
BASE_SHA                   = facf090c782b022730ecc5f1cf0d0b02e29ca8d7   ✓ KHỚP kỳ vọng
REVIEW_TARGET_SHA          = a36f95917ce35acee0a05e215fbfa08df3a9ebe9   ✓ KHỚP kỳ vọng
FROZEN_CONTRACT_SHA        = c12c5635b5e4298a9584b5fa93e21762c0d70c5b   ✓ KHỚP kỳ vọng
REVIEW_TARGET_MOVED        = KHÔNG
ARTIFACT                   = docs/reviews/TASK-PRA-003-INDEPENDENT-REVIEW-RECORD.md

FROZEN CONTRACT CÓ BỊ NỚI LỎNG KHÔNG?
  KHÔNG. Diff c12c563..a36f959 trên file task chỉ đổi các trường ghi bằng chứng
  (Status/Executed By/Timestamp/khối "Kết quả S096"). KHÔNG một dòng "Yêu cầu:",
  KHÔNG một oracle O-A…O-K, KHÔNG một Owner Decision D1–D3 nào bị sửa chữ.
  tests/fixtures/golden/** KHÔNG bị sửa một byte — oracle độc lập còn nguyên.

RECOMPUTE ĐỘC LẬP (SQL THÔ, không qua analytics_queries — rồi mới đem so)
  raw SQL        : 351 dòng · 254 đơn · SL 407 · doanh thu 3.562.310.000 · AUTO 2 / PENDING 349
  expected JSON  : 351 dòng · 254 đơn · SL 407 · doanh thu 3.562.310.000
  implementation : KHỚP cả hai · auto_orders + review_orders = 1 + 253 = 254 = orders

CHỨNG MINH CẤU TRÚC (mạnh hơn grep)
  PK order_line_current + hai join đều trỏ vào cột `id` là PRIMARY KEY
    ⟹ many-to-one nghiêm ngặt, KHÔNG có đường nhân bản cardinality
  current_source_version_id / current_result_version_id đều nullable=False
    ⟹ inner join KHÔNG âm thầm đánh rơi dòng nào
  CheckConstraint(status IN ('AUTO','PENDING'))       ⟹ phân hoạch thật ở cấp DB
  CheckConstraint(origin='PIPELINE_GENERATED') × 3 bảng
    ⟹ dòng legacy KHÔNG THỂ lọt vào về mặt vật lý (tách nguồn theo cấu trúc)

CHECK MATRIX (sau review)
  01 PASS  02 PASS  03 PASS  04 PASS  05 PASS  06 PASS
  07 NOT_TESTED — real vertical production 09/2026, CHỜ Owner sau deploy
  08 PASS  09 PASS  10 PASS  11 PASS
  12 PASS — Independent Review E2 ĐÃ ACCEPT (phiên này)
  13 PASS  14 PASS

REVIEWER CHẠY LẠI
  PRA-003 focused : 67 passed
  Golden Baseline : 58 passed, 2 skipped        ← khớp O-K
  legacy routes   : 34 passed                   ← non-regression PRA-001
  PRA-002 vertical: 12 passed
  FULL SUITE      : 1873 passed, 11 skipped (exit 0)
  validators      : structure/project_state/evidence/task_completion = PASS
                    reference_integrity = FAIL đúng 3 issue REM-T06 đã biết, không issue mới
  budget đo lại   : Python 284 · template 191 · CSS 16 — tái lập ĐÚNG số implementer báo
  Scope Lock      : 0 vi phạm · schema/migration/index/dependency/config = 0

BLOCKING_FINDINGS   = 0
NON_BLOCKING        = FIND-PRA003-01 CONTRACT_MISMATCH — minh hoạ số học của O-C
                      (`0/351`) dẫn xuất từ block `pricing` của golden JSON, vốn do
                      build_expected.py sinh bằng run_import() TRẦN. Đường persist
                      THẬT là run_owner_report → demo.run_demo → run_import_production
                      (có nạp registry canonical), nên coverage đúng của kỳ golden là
                      2/351. Reviewer chạy CẢ HAI đường trên cùng fixture để xác nhận.
                      Implementation test ĐÚNG đường production, KHÔNG sửa fixture, còn
                      assert ngược lại rằng golden JSON vẫn đọc {Pending: 351} — bảo tồn
                      oracle chứ không làm yếu. Khắc phục = sửa TÀI LIỆU O-C, không sửa mã.
                      FIND-PRA003-02 EVIDENCE_DEFECT — `git diff --check` trên DẢI COMMIT
                      có 1 trailing whitespace (docs/sessions/S094-…md:341, chỉ file docs);
                      dạng working-tree của lệnh đúng là sạch, nên tuyên bố S096 "sạch"
                      đúng cho dạng lệnh đó nhưng không đúng cho dải commit.
                      FIND-PRA003-03 HARDENING — một employee_normalized mang hai
                      employee_group sẽ hiện thành hai dòng cùng tên; bất biến cộng được
                      VẪN đúng và dòng TỔNG vẫn đếm mỗi đơn một lần. RE-TRIGGER: khi dữ
                      liệu thật lần đầu có một nhân viên mang hai nhóm trong cùng kỳ.
REVIEW BUDGET       = repair_cycles_used 0 / 1 — review KHÔNG tiêu cycle; KHÔNG finding
                      nào đe doạ 1 trong 5 điều kiện mục 14 ⟹ KHÔNG mở repair cycle

VIỆC TIẾP THEO      = Controlled Integration vào canonical
                      (claude/extract-upload-repo-gq2ws4), SAU ĐÓ Owner nghiệm thu
                      CHECK-PRA003-07 trên production. Phiên này KHÔNG tích hợp canonical,
                      KHÔNG đánh dấu task DONE, KHÔNG sửa mã production.
```

---

## CANONICAL CURRENT STATE — TASK-PRA-003 (lịch sử, 2026-09-03, S096 — IMPLEMENTATION)

Phiên MAJOR implement hợp đồng đã freeze ở S095 đã xong. Đây là BẢN GHI LỊCH
SỬ đúng của phiên implement — trạng thái hiện hành có thẩm quyền của
`TASK-PRA-003` nằm ở khối S097 phía TRÊN; khối S095 bên dưới là bản ghi lịch
sử của phiên freeze gate. Khối `TASK-PRA-002` phía dưới KHÔNG bị
khối này thay thế — hai task khác nhau.

```text
SESSION                    = S096 — PRA-003 MAJOR Implementation
IMPLEMENTATION_RESULT      = PASS
TASK-PRA-003               = IN_PROGRESS — implementation XONG, CHỜ Independent Review E2
                             (KHÔNG phải DONE: còn CHECK-07 và CHECK-12)
BASE_CANONICAL             = claude/extract-upload-repo-gq2ws4 @ facf090c782b022730ecc5f1cf0d0b02e29ca8d7
                             (xác minh đầu phiên — CANONICAL_NOT_MOVED)
FROZEN_CONTRACT_SHA        = c12c5635b5e4298a9584b5fa93e21762c0d70c5b
NHÁNH IMPLEMENT            = claude/pra-003-roadmap-finalization-di33bn
HANDOFF                    = docs/sessions/S096-pra-003-major-implementation.md

FILE PRODUCTION MỚI (4)
  app/web/analytics_queries.py           117 dòng mã  — toàn bộ SQL, CHỈ-ĐỌC
  app/web/analytics_presentation.py      105 dòng mã  — định dạng + nhãn nguồn
  app/web/templates/tong_quan.html        80 dòng
  app/web/templates/_pipeline_bits.html   63 dòng
FILE PRODUCTION SỬA (4)
  app/web/server.py                      +62 dòng mã  — route /tong-quan, tham số nguon
  app/web/templates/nhan_vien.html       +47 dòng     — bộ chuyển nguồn + nhánh SỐ MỚI
  app/web/static/css/tinphat-ui.css      +16 dòng
  app/web/templates/layout.html           +1 dòng     — tab "Tổng quan"
TEST MỚI (3 file, 67 test)
  tests/test_analytics_queries.py         22 test
  tests/test_analytics_presentation.py    20 test
  tests/test_web_pipeline_analytics.py    25 test

SCHEMA_CHANGED = NO     MIGRATION = 0     INDEX_ADDED = 0     DEPENDENCY_ADDED = 0
CONFIG_ADDED   = 0      TRACKING_CHANGED = NO      INFRASTRUCTURE_CHANGED = NO
PROTECTED_CORE_IMPACT = NONE               ALEMBIC_HEAD = 0002_snapshots (không đổi)
PRA-001 / PRA-002 CHANGED = NO             MỌI INSERT/UPDATE/DELETE = 0 (tầng CHỈ-ĐỌC)

CHANGE_BUDGET (đo bằng script AST, dòng mã — bỏ trống/comment/docstring)
  Python production  = 284   mục tiêu 255 · cảnh báo mềm 320 · DỪNG CỨNG 400 → TRONG NGƯỠNG
  Template           = 191   trần 220  ✓
  CSS                =  16   trần  25  ✓
  Test mới           =  67   sàn  30, 0 skip mới ✓

CHECK MATRIX
  01 PASS  02 PASS  03 PASS  04 PASS  05 PASS  06 PASS
  07 NOT_TESTED — real vertical production 09/2026, CHỜ Owner sau deploy
  08 PASS  09 PASS  10 PASS  11 PASS
  12 NOT_TESTED — Independent Review E2, phiên implement KHÔNG tự review mình
  13 PASS  14 PASS — đo thật: chậm nhất 64 ms trên 12.000 dòng ⟹ KHÔNG thêm index

REGRESSION (đo TRƯỚC và SAU)
  Golden Baseline : 58 passed, 2 skipped  →  58 passed, 2 skipped   (KHÔNG đổi)
  Full suite      : 1806 passed, 11 skipped  →  1873 passed, 11 skipped
  Validators      : structure/project_state/evidence/task_completion = PASS (cả hai lần)
                    reference_integrity = FAIL đúng 3 issue REM-T06 đã biết, không issue mới
  git diff --check: sạch

BLOCKING_FINDINGS   = 0
NON_BLOCKING        = FIND-PRA003-01 (HARDENING) — block `pricing` của
                      tests/fixtures/golden/expected/period_2026_01.json mô tả đường
                      `run_import()` TRẦN (build_expected), không phải đường production
                      `run_import_production` mà PRA-003 đọc. Trên cùng fixture, đường
                      production cho 2 dòng AUTO (price_source =
                      OWNER_MANUAL_LEGACY_CONFIRMATION), nên coverage thật là 2/351 chứ
                      không phải 0/351 như O-C mô tả. Không phải defect mã; chi tiết và
                      RE-TRIGGER CONDITION ở handoff S096.
REVIEW BUDGET       = repair_cycles_used 0 / 1 (phiên implement KHÔNG tiêu repair cycle)

VIỆC TIẾP THEO      = Independent Review E2 (CHECK-PRA003-12), artifact tại docs/reviews/
                      theo governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md.
                      Phiên này KHÔNG tích hợp canonical và KHÔNG đánh dấu task DONE.
```

---

## CANONICAL CURRENT STATE — TASK-PRA-003 (lịch sử, 2026-09-03, S095 — GATE FROZEN)

Roadmap Finalization đã đóng: task file tồn tại, Completion Gate FROZEN,
lineage review budget đã mở. Khối này là bản ghi LỊCH SỬ của phiên freeze gate
— trạng thái hiện hành có thẩm quyền của `TASK-PRA-003` nằm ở khối S096 phía
TRÊN; khối S094 bên dưới là bản ghi lịch sử của phiên discovery. Khối `TASK-PRA-002` phía dưới KHÔNG bị khối này thay thế — hai
task khác nhau.

```text
SESSION                    = S095 — PRA-003 Roadmap Finalization (docs-only)
FINALIZATION_RESULT        = CONTRACT_FROZEN — PRA-003 sẵn sàng cho MỘT phiên MAJOR implement
TASK-PRA-003               = IN_PROGRESS / READY_FOR_IMPLEMENTATION
CANONICAL_SHA              = facf090c782b022730ecc5f1cf0d0b02e29ca8d7
                             (khớp EXPECTED — CANONICAL_NOT_MOVED)
DISCOVERY_INPUT_SHA        = c776c8ae2656458099f5bcbc054bfec6f73ed058
                             (claude/pra-003-vertical-slice-346ebn — planning input,
                              KHÔNG phải production authority; đã fast-forward vào
                              nhánh phiên này để giữ nguyên ancestry)

PRODUCTION_CODE_ADDED      = 0 dòng      SCHEMA_CHANGED = NO      MIGRATION = NO
TRACKING_CHANGED           = NO          INFRASTRUCTURE_CHANGED = NO
PRA-001 / PRA-002 CHANGED  = NO          DEPENDENCY_ADDED = 0

OWNER_DECISIONS_LOCKED
  D1 = LN KPI là số CHÍNH (chỉ cộng dòng AUTO) · LN kế toán là số PHỤ ·
       CẢ HAI bắt buộc kèm coverage · source_profit KHÔNG lên dashboard
  D2 = Target/So target DEFER hoàn toàn khỏi PRA-003. Cấm sao chép hoặc kết
       hợp legacy_summary_row.target vào bất kỳ chỉ tiêu PIPELINE_GENERATED
       nào (vi phạm DEC-166 E). Không config/schema/ingestion target.
  D3 = Nhãn ô số lượng = "Tổng số lượng" (mọi dòng). Cấm nhãn "Số lượng sản
       phẩm"/"Tổng số SP" cho tới khi có quy tắc phân loại product-line có
       thẩm quyền (N.7 vẫn MỞ).

MINIMUM_VALUE_FILTER       = Tổng quan: 12 đề xuất → 10 REQUIRED_NOW ·
                               1 USEFUL_BUT_DEFER (top nhân viên) ·
                               1 NOT_NEEDED (ô AUTO/Review theo DÒNG — trùng
                               lặp với coverage LN KPI, thông tin KHÔNG mất)
                             Nhân viên: 10 cột → 8 REQUIRED_NOW ·
                               1 USEFUL_BUT_DEFER (Δ doanh thu theo nhân viên) ·
                               1 NOT_NEEDED (cột AUTO/Review — cùng lý do trùng lặp)
                             Không chỉ tiêu trang trí nào lọt vào.

PERIOD_MODEL               = "Toàn bộ dữ liệu" + "Tháng MM/YYYY", MỌI tuỳ chọn
                             dẫn xuất từ order_line_current.sale_date.
                             So sánh = tháng dương lịch liền trước; kỳ trước
                             không có dữ liệu ⟹ TRỐNG/"—", TUYỆT ĐỐI không 0/0%.
                             "Toàn bộ dữ liệu" ⟹ KHÔNG có kỳ so sánh.
                             DEFER: khoảng ngày tự do, quý, năm, "hôm nay".
                             Cấm dẫn xuất kỳ từ header workbook (FIND-RDA-01).

TOUCH_AREA                 = MỚI: app/web/analytics_queries, analytics_presentation,
                             templates/tong_quan.html, templates/_pipeline_bits.html
                             SỬA: app/web/server.py (+1 route /tong-quan, +1 tham số
                             nguon), templates/layout.html (+1 tab), nhan_vien.html,
                             static/css/tinphat-ui.css
                             FORBIDDEN: tools/db/**, app/history/**, history_store.py,
                             history_writer.py, run_registry.py, storage_backend.py,
                             legacy_presentation.py, app/modules/**, config/**, data/**,
                             tests/fixtures/golden/**, alembic.ini, render.yaml,
                             Dockerfile, Tracking, và MỌI câu INSERT/UPDATE/DELETE
                             (PRA-003 là tầng CHỈ-ĐỌC)
PROTECTED_CORE_IMPACT      = NONE

CHANGE_BUDGET (riêng PRA-003, KHÔNG kế thừa 40 LOC còn lại của PRA-002)
                           = Python production mục tiêu ~255 · CẢNH BÁO MỀM 320 ·
                             DỪNG CỨNG 400 → vượt = STOP = CHANGE_BUDGET_EXCEEDED
                             template ≤220 · CSS ≤25 · test ≥30 (0 skip mới) ·
                             dependency 0 · schema 0 · migration 0 · index 0 · config 0
                             Mục tiêu 255 (thấp hơn ước tính 275 của S094) nhờ headroom
                             từ Minimum-Value Filter; headroom đó KHÔNG được tiêu việc khác.

REVIEW_BUDGET              = effective_risk MEDIUM → 1 blocking repair cycle · 0 đã dùng
                             Independent Review E2 BẮT BUỘC (CHECK-PRA003-12)
                             Lineage ĐÃ MỞ: PROJECT/REVIEW_BUDGET_LEDGER.md →
                             "Root Task: TASK-PRA-003", BASE_SHA = facf090

COMPLETION_GATE            = FROZEN tại S095 — 14 check: 12 REQUIRED + 2 RECOMMENDED
                             01 no-double-count current-state · 02 oracle golden độc lập ·
                             03 NULL≠0 hiện "—" · 04 LN KPI chỉ AUTO + 2 coverage ·
                             05 nhân viên đối soát tổng kỳ (Đơn KHÔNG cộng được) ·
                             06 tách nguồn + legacy không hồi quy · 07 real vertical
                             production 09/2026 · 08 kỳ trước vắng ⟹ blank không 0% ·
                             09 dòng thiếu sale_date được phơi ra · 10 không PII
                             (gồm imei, note_raw) · 11 không hồi quy Golden/suite/validators ·
                             12 Independent Review E2 · [R] 13 CHANGE_BUDGET đo được ·
                             [R] 14 thời gian tải ≥12k dòng (ứng viên hardening DUY NHẤT)
                             Tất cả Status = NOT_TESTED (chưa implement — không bịa PASS)

ACCEPTANCE_ORACLE          = O-B golden 01/2026: orders 254 · lines 351 · quantity 407 ·
                               doanh thu 3.562.310.000 (ĐỌC từ tests/fixtures/golden/
                               expected/period_2026_01.json, KHÔNG hard-code)
                             O-C LN KPI và LN kế toán cùng kỳ = "—" (0/351), KHÔNG 0
                             O-G production Tháng 09/2026: 40 đơn · 61 dòng · AUTO 15 ·
                               Review 25 (ĐÃ QUAN SÁT S093) · so tháng trước TRỐNG
                             O-K Golden 58 passed / 2 skipped, full suite không giảm
GIỚI HẠN ORACLE GOLDEN     = fixture ẩn danh về ĐÚNG 1 nhân viên và 351/351 dòng
                             price_source = Pending ⟹ KHÔNG làm oracle được cho phân rã
                             nhiều nhân viên hay cho giá trị lợi nhuận dương. Hai vùng đó
                             do test đơn vị phủ. KHÔNG dựng fixture "giống production"
                             rồi gọi là bằng chứng thật.
NOT_CLAIMED                = tiền/số lượng/lợi nhuận của ca production 01→03/09 (chưa quan
                             sát). Bộ số qty 71 / gross 593.750.000 / net 593.550.000 là
                             provenance RDA S090/S091 — KHÔNG phải số production của ca này
                             và KHÔNG được dùng làm kỳ vọng.

VALIDATORS (S095, E1)      = structure PASS · project_state PASS · evidence PASS (116 record) ·
                             task_completion PASS (10 DONE task) ·
                             reference_integrity FAIL đúng 3 issue REM-T06 đã biết
                             (không phát sinh mới; KHÔNG sửa — hard exclusion)
SCOPE_DRIFT                = NO — 0 dòng production, không schema/migration/tracking/
                             hạ tầng, không mở PRA-004/PRA-005, không repair REM-T06,
                             không repair finding DEFER của PRA-002
IMPLEMENTATION_READY       = YES
EVIDENCE                   = docs/sessions/S095-pra-003-roadmap-finalization.md ·
                             docs/tasks/TASK-PRA-003-tong-quan-nhan-vien.md ·
                             PROJECT/REVIEW_BUDGET_LEDGER.md → Root Task: TASK-PRA-003
NEXT_VERTICAL_ACTION       = MỘT phiên MAJOR implement theo thứ tự bắt buộc
                             analytics_queries → analytics_presentation → route →
                             template → CSS; test đơn vị viết TRƯỚC test route/integration.
                             Sau đó: Independent Review E2 (≤1 repair cycle) → Owner
                             nghiệm thu trên production kỳ Tháng 09/2026 (CHECK-PRA003-07).
                             KHÔNG mở PRA-004/PRA-005.
```

## CANONICAL CURRENT STATE — TASK-PRA-003 (lịch sử, 2026-09-03, S094 — DISCOVERY)

Phiên discovery/plan của `TASK-PRA-003` (Tổng quan + Nhân viên). Đây là trạng
thái hiện hành có thẩm quyền của PRA-003. Khối PRA-002 ngay bên dưới vẫn đúng
và không bị khối này thay thế — hai task khác nhau.

```text
SESSION                    = S094 — PRA-003 Vertical Slice Discovery (docs-only)
TASK-PRA-003               = PLANNED (discovery xong; task file + gate CHƯA tạo)
RESULT                     = DISCOVERY_COMPLETE
CANONICAL_SHA              = facf090c782b022730ecc5f1cf0d0b02e29ca8d7
                             (khớp EXPECTED — canonical KHÔNG moved; branch authority
                              check: DEFAULT_TIP == HEAD_SHA, WORKTREE CLEAN)
TIỀN ĐỀ                    = TASK-PRA-002 = DONE và ĐÃ tích hợp vào canonical
                             (facf090/189516e/432ad4e nằm trên default branch)

PRODUCTION_CODE_ADDED      = 0 dòng      SCHEMA_CHANGED = NO      MIGRATION = NO
TRACKING_CHANGED           = NO          INFRASTRUCTURE_CHANGED = NO
PRA-001 / PRA-002 CHANGED  = NO

SLICE ĐÃ CHỌN              = Tổng quan (12 ô) + Nhân viên bản pipeline (10 cột),
                             kỳ theo THÁNG dẫn xuất từ order_line_current.sale_date,
                             so kỳ trước = tháng liền trước (TRỐNG khi không có dữ liệu)
TOUCH_AREA                 = MỚI: app/web/analytics_queries.py,
                             app/web/analytics_presentation.py,
                             templates/tong_quan.html, templates/_pipeline_bits.html
                             SỬA: app/web/server.py (+1 route, +1 tham số nguon),
                             templates/layout.html (+1 tab), templates/nhan_vien.html,
                             static/css/tinphat-ui.css
                             KHÔNG CHẠM: tools/db, app/history, history_store,
                             history_writer, app/modules/**, config/**, hạ tầng
CHANGE_BUDGET (riêng PRA-003, KHÔNG kế thừa 40 LOC còn lại của PRA-002)
                           = Python production mục tiêu ~275, DỪNG CỨNG 400
                             template ≤220 · CSS ≤25 · test ≥30 · dependency 0
REVIEW_BUDGET              = effective_risk MEDIUM → 1 blocking repair cycle (V4.1 §2)
                             Chấm theo failure path: tầng CHỈ-ĐỌC, không INSERT/UPDATE/
                             DELETE; hỏng = hiện sai một số quản lý, KHÔNG ghi đè dữ
                             liệu và KHÔNG đụng bất biến no-double-count của PRA-002.
                             Lineage CHƯA mở trong REVIEW_BUDGET_LEDGER.md.

FACT NỀN (đọc từ mã nguồn, dùng cho mọi phiên PRA-003 sau)
  1. status AUTO ⟹ chắc chắn có đủ accounting_purchase_price + accounting_profit
     + eligible_kpi_profit (excel_exporter.py:71-73 + 141-149). Chiều ngược lại
     KHÔNG đúng. Nên "LN KPI chỉ cộng dòng AUTO" là quy tắc trình bày có định
     nghĩa chặt, luôn cộng được.
  2. "Accounting coverage 100%" = accounted_orders/input_orders (đơn dựng được),
     KHÔNG phải coverage giá nhập. KHÔNG suy ra 61 dòng đều có lợi nhuận.
  3. order_line_current.sale_date NULLABLE; _period() lọc bằng >=/<= nên dòng
     không có ngày bán rơi khỏi mọi kỳ TRONG IM LẶNG → bắt buộc đếm và hiện riêng.
  4. source_snapshot.summary_json là số của MỘT lần chạy; cộng nó theo kỳ là
     double-count. AUTO/Review theo kỳ PHẢI dẫn xuất từ order_line_current →
     order_line_result_version.status.
  5. Fixture golden KHÔNG làm oracle được cho nhân viên (chỉ 1 nhân viên sau ẩn
     danh) và cho lợi nhuận (351/351 dòng price_source = Pending).

DATA_GAPS                  = Số lượng SP loại dòng phí = MISSING_BUSINESS_RULE (N.7);
                             target/so target = MISSING_DATA (N.8, config/targets
                             không tồn tại); margin = MISSING_BUSINESS_RULE (§L LATER);
                             doanh số quy đổi = §L LATER, cấm tính ở tầng UI.
OWNER_DECISIONS_REQUIRED   = 3, TẤT CẢ NON-BLOCKING (có default an toàn):
                             D1 lợi nhuận nào là số chính → mặc định KPI(AUTO)+coverage
                                là số chính, LN kế toán là cột phụ, source_profit KHÔNG lên
                             D2 target → mặc định DEFER khỏi slice 1 (không có dữ liệu;
                                dùng target legacy bị loại vì vi phạm DEC-166 E)
                             D3 ô số lượng → mặc định "Tổng số lượng (mọi dòng)",
                                DEFER chỉ tiêu "Số lượng SP"
ACCEPTANCE_ORACLE          = golden 01/2026 (orders 254 · lines 351 · qty 407 ·
                             doanh thu 3.562.310.000 từ expected/period_2026_01.json)
                             + LN KPI/kế toán phải là "—" chứ KHÔNG phải 0
                             + production 2026-09/2026: 40 đơn · 61 dòng · AUTO 15 ·
                               Review 25 (ĐÃ QUAN SÁT) · so tháng trước TRỐNG
NOT_CLAIMED                = tiền/số lượng của ca production 01→03/09 (chưa quan sát);
                             bộ số qty 71 / gross 593.750.000 / net 593.550.000 là
                             provenance RDA S090/S091, KHÔNG phải số production của ca này
SCOPE_DRIFT                = NO. Kế hoạch HẸP HƠN TASK-PRA-000 §M SLICE 3 ở 3 chỗ có
                             bằng chứng: bỏ drill-down nhân viên→ngày→đơn (PRA-004),
                             bỏ bảng lệch legacy/pipeline (chưa có kỳ chồng nhau),
                             bỏ target (không có dữ liệu).
IMPLEMENTATION_READY       = YES (với default D1/D2/D3)
EVIDENCE                   = docs/sessions/S094-pra-003-vertical-slice-discovery.md
NEXT_VERTICAL_ACTION       = (1) Owner xác nhận/ghi đè D1-D3 → (2) phiên Roadmap
                             Finalization viết docs/tasks/TASK-PRA-003-*.md + FREEZE
                             gate + mở lineage trong REVIEW_BUDGET_LEDGER.md →
                             (3) 1 phiên MAJOR implement → (4) Independent Review →
                             (5) Owner nghiệm thu trên production kỳ Tháng 09/2026.
                             KHÔNG mở PRA-004/PRA-005; KHÔNG freeze gate trong phiên
                             discovery.
```

## CANONICAL CURRENT STATE — TASK-PRA-002 (AUTHORITATIVE, 2026-09-03, S093 FINAL — TASK DONE)

Production Acceptance đã đóng. Đây là trạng thái hiện hành có thẩm quyền của
`TASK-PRA-002`. Các khối bên dưới là bản ghi lịch sử đúng của thời điểm chúng;
khi mâu thuẫn về trạng thái *hiện tại*, khối này đúng.

```text
SESSION                    = S093 (giai đoạn 3) — PRA-002 Production Acceptance closeout (docs-only)
PRODUCTION_ACCEPTANCE_RESULT = PASS
EVIDENCE_PROVENANCE        = OWNER_PROVIDED_PRODUCTION_EVIDENCE (Owner thao tác + đọc UI production thật)

TASK-PRA-002               = DONE
CHECK-PRA002-14            = PASS  (E1 real data — S090/S091)
CHECK-PRA002-15            = PASS  (E1 production — phiên này)
CHECK-PRA002-17            = PASS  (E2 toàn task — S092)
COMPLETION_GATE            = ĐỦ — 16/16 check REQUIRED PASS; 16 RECOMMENDED có số đo; Exit Criteria 6/6
MISSING_REQUIRED_EVIDENCE  = NONE
BLOCKING_FINDINGS          = 0

DEPLOYED_SHA               = c2142dd (== REQUIRED canonical c2142ddee795d1e4d829cabfd01b1774d3441651)
                             Render Manual Deploy · Live · 2026-09-03 10:36:11 GMT+7 · 24.0s
ALEMBIC_VERSION            = 0002_snapshots (suy dẫn loại trừ từ fail-closed assert_schema_current +
                             REPORTS_REQUIRE_HISTORY_DB=1; service Live + ghi snapshot ⟹ guard PASS.
                             KHÔNG có ảnh chụp truy vấn SQL — không tuyên bố có)
LEGACY_NON_REGRESSION      = /nhan-vien 200 — "NHÂN VIÊN — SỐ CŨ THEO THÁNG", legacy source
                             LEG-20260902-4ffe5198 (Báo cáo Kinh doanh 2026.xlsx, Tháng 08/2026),
                             bảng đầy đủ; cùng ID hiện ở /du-lieu (LEGACY_REFERENCE, ĐANG XEM)
                             ⟹ bản nhập legacy trước deploy KHÔNG đổi. PRA-001 không hồi quy.
FIRST_UPLOAD               = So_chi_tiet_ban_hang (8).xlsx · SNAP-20260903034024-7b421983 ·
                             HEADER_CONSISTENT · 2026-09-01 → 2026-09-03 · 61 dòng / 40 đơn ·
                             INSERT 61 · SAME 0 · SOURCE_CHANGED 0 · COLLISION 0 · NOT_SEEN 0 ·
                             REMOVED_CANDIDATE 0 · run COMPLETE (03:40:28) · CÓ SNAPSHOT
SECOND_UPLOAD              = đúng file đó · SNAP-20260903034120-7b421983 · "FILE TRÙNG" ·
                             SAME 61 = line_count · INSERT 0 · SOURCE_CHANGED 0 · COLLISION 0 ·
                             0 source version mới · không cờ SOURCE · run COMPLETE (03:41:23)
NO_DOUBLE_COUNT            = OBSERVED_ON_PRODUCTION — sau hai upload vẫn 61 dòng / 40 đơn; F5 giữ nguyên
TRACKING_AUTO              = REAL — "Sẵn sàng — dữ liệu Tracking lấy trực tiếp (live) mỗi lần chạy" ·
                             AUTO 15 · Review 25 · priority review 3 · 0 dòng không nhận ra ·
                             Accounting coverage 100% · không fake, không mutate, không ép tỉ lệ AUTO
MEMORY / OOM               = PASS_PRODUCTION_BEHAVIOR. Render Metrics KHÔNG có data point Memory/CPU
                             cho khung 10:40–11:03 GMT+7 (chỉ hiện "Limit 512 MB") → numeric peak
                             NOT_OBSERVED, KHÔNG bịa số, KHÔNG đọc đường trống thành 0 MB.
                             Cận trên < 512 MB xác lập bằng cơ chế fail-stop: limit CỨNG 512 MB,
                             vượt ⟹ OOM-kill ⟹ Instance failed + request đứt; hai upload COMPLETE,
                             service Live liên tục, state sống sau F5 ⟹ đỉnh chưa từng chạm 512 MB.
                             Dòng Evidence của chính CHECK-15 quy mục này về "không OOM".
                             Bối cảnh độ lớn (không gánh kết luận): CHECK-16 đo 75,6 MB / 78,7 MB
                             trên workbook golden 351 dòng vs production 61 dòng.
OBSERVABILITY_LIMITATION   = Render Metrics không trả telemetry Memory/CPU trên cấu hình hiện tại.
                             Ghi nhận, KHÔNG chặn, KHÔNG mở finding/task, KHÔNG đổi plan.
NOT_CLAIMED_AS_PRODUCTION  = qty 71 · gross 593.750.000 · discount 200.000 · net 593.550.000
                             (provenance RDA S090/S091 = CHECK-14) · COUNT(*) source version thô ·
                             kết quả truy vấn alembic_version · numeric RAM peak

CODE_REQUIRED              = NO       PRODUCTION_CODE_ADDED = 0 dòng
CHANGE_BUDGET_STATE        = 1.460 / 1.500   REMAINING = 40 LOC (KHÔNG chạm)
REVIEW_BUDGET_STATE        = 1 / 2 USED · 1 REMAINING (không tiêu repair cycle)
TRACKING_CHANGED           = NO       INFRASTRUCTURE_CHANGED = NO
INTEGRATION_READY          = YES — Controlled Integration KHÔNG thực hiện trong phiên này
EVIDENCE                   = docs/sessions/S093-pra-002-production-acceptance.md (mục 14–17;
                             ma trận REQUIRED cuối ở mục 15.1) ·
                             docs/tasks/TASK-PRA-002-...md CHECK-PRA002-15 ·
                             docs/deployment/S071_DEPLOYMENT.md
NEXT_VERTICAL_ACTION       = Controlled Integration docs/state cuối của PRA-002 vào canonical
                             claude/extract-upload-repo-gq2ws4, SAU ĐÓ mới mở PRA-003
                             (Tổng quan + Nhân viên). KHÔNG mở PRA-003 ở phiên này.
```

## CANONICAL CURRENT STATE — TASK-PRA-002 (lịch sử, 2026-09-03, S093 giai đoạn 2)

Cập nhật sau khi **Owner trả về bằng chứng production thật**. Đây là bước 6
của mục 16 (ghi kết quả vào file này). Các khối bên dưới giữ nguyên như bản
ghi lịch sử đúng của thời điểm đó; khi mâu thuẫn về trạng thái *hiện tại*,
khối này đúng.

```text
SESSION                    = S093 (giai đoạn 2) — PRA-002 Production Acceptance từ bằng chứng Owner (docs-only)
PRODUCTION_ACCEPTANCE_RESULT = PARTIAL_PENDING_OWNER_EVIDENCE
EVIDENCE_PROVENANCE        = OWNER_PROVIDED_PRODUCTION_EVIDENCE (Owner thao tác + đọc UI production thật)

DEPLOYED_SHA               = c2142dd  — Render hiển thị, service Live
                             Manual deployment 2026-09-03 10:36:11 GMT+7 · 24.0s
                             branch claude/extract-upload-repo-gq2ws4 → KHỚP REQUIRED canonical
                             c2142ddee795d1e4d829cabfd01b1774d3441651
ALEMBIC_VERSION            = 0002_snapshots (suy dẫn LOẠI TRỪ từ fail-closed:
                             create_app → _build_history → assert_schema_current raise nếu
                             version != ALEMBIC_HEAD, và REPORTS_REQUIRE_HISTORY_DB=1 nên app
                             KHÔNG khởi động; service Live + ghi snapshot thành công ⟹ PASS.
                             KHÔNG có ảnh chụp truy vấn SQL — không tuyên bố có)

FIRST_UPLOAD               = So_chi_tiet_ban_hang (8).xlsx · 40 đơn · 61 dòng ·
                             SNAP-20260903034024-7b421983 · HEADER_CONSISTENT ·
                             range 2026-09-01 → 2026-09-03 ·
                             INSERT 61 · SAME 0 · SOURCE_CHANGED 0 · COLLISION 0 ·
                             NOT_SEEN 0 · REMOVED_CANDIDATE 0 · run COMPLETE · CÓ SNAPSHOT
SECOND_UPLOAD              = đúng file đó · SNAP-20260903034120-7b421983 · "FILE TRÙNG" ·
                             SAME 61 (= line_count) · INSERT 0 · SOURCE_CHANGED 0 · COLLISION 0 ·
                             NOT_SEEN 0 · REMOVED_CANDIDATE 0 · run #2 COMPLETE · CÓ SNAPSHOT
NEW_SOURCE_VERSION         = 0 (suy dẫn từ semantics freeze: SAME là nhánh DUY NHẤT không ghi
                             source version mới — reconciler._decide; COUNT(*) thô không hiển thị)
NO_DOUBLE_COUNT            = OBSERVED_ON_PRODUCTION — sau hai lần upload vẫn 61 dòng / 40 đơn
TRACKING_AUTO              = REAL — "Sẵn sàng — dữ liệu Tracking lấy trực tiếp (live) mỗi lần chạy" ·
                             AUTO 15 · Review 25 · priority review 3 · dòng không nhận ra 0 ·
                             Accounting coverage 100% · không tỉ lệ AUTO định trước, không fake Tracking
PERSISTENCE                = F5 trên /du-lieu: cả hai snapshot và cả hai run (03:40:28, 03:41:23)
                             vẫn hiện, số liệu không đổi

CHECK-PRA002-14            = PASS   (E1 real data, S091 — không đổi)
CHECK-PRA002-15            = NOT_TESTED — 3 assertion REQUIRED chưa quan sát (xem MISSING bên dưới)
CHECK-PRA002-17            = PASS   (E2 toàn task, S092 — không đổi)
MISSING_REQUIRED_EVIDENCE  = (1) mục 16 bước 2: `/nhan-vien` trả 200 (PRA-001 không hồi quy)
                             (2) mục 16 bước 2: legacy import hiện có KHÔNG đổi trên /du-lieu
                             (3) mục 16 bước 5: Render Metrics RAM đỉnh lúc upload < 512 MB
                             — cả ba là thao tác ĐỌC; không cần upload lại, không cần deploy lại
NOT_REQUIRED (không chặn)  = COUNT(*) source version thô · truy vấn alembic_version tận mắt ·
                             qty/gross/net trên UI production · restart Render · người xem thứ hai ·
                             tỉ lệ AUTO định trước · CONFIRMED_COMPLETE
COMPLETION_GATE            = CHƯA THOẢ — còn đúng một gate REQUIRED: CHECK-PRA002-15
TASK-PRA-002               = IN_PROGRESS
BLOCKING_FINDINGS          = 0  (không defect nào trên production path; thiếu là ảnh bằng chứng)
CODE_REQUIRED              = NO       PRODUCTION_CODE_ADDED = 0 dòng
CHANGE_BUDGET_STATE        = 1.460 / 1.500   REMAINING = 40 LOC (KHÔNG chạm)
REVIEW_BUDGET_STATE        = 1 / 2 USED · 1 REMAINING
TRACKING_CHANGED           = NO       INFRASTRUCTURE_CHANGED = NO
INTEGRATION_READY          = NO — chờ CHECK-15 PASS rồi mới Controlled Integration
EVIDENCE                   = docs/sessions/S093-pra-002-production-acceptance.md (mục 8–13,
                             ma trận REQUIRED đầy đủ ở mục 10)
NEXT_VERTICAL_ACTION       = Owner gửi 3 mục MISSING → CHECK-PRA002-15 = PASS →
                             TASK-PRA-002 = DONE → Controlled Integration docs/state cuối →
                             sau đó mới PRA-003 (Tổng quan + Nhân viên)
```

## CANONICAL CURRENT STATE — TASK-PRA-002 (lịch sử, 2026-09-03, S093 giai đoạn 1)

Cập nhật sau phiên **Production Acceptance (CHECK-PRA002-15)**. Các khối bên dưới
giữ nguyên như bản ghi lịch sử đúng của phiên đó; khi mâu thuẫn về trạng thái
*hiện tại*, khối này đúng.

```text
SESSION                    = S093 — PRA-002 Production Acceptance (docs-only)
PRODUCTION_ACCEPTANCE_RESULT = BLOCKED_ON_OWNER_ACTION (KHÔNG PASS, KHÔNG FAIL — chưa thực thi)
CANONICAL_SHA              = c2142ddee795d1e4d829cabfd01b1774d3441651 (khớp REQUIRED — canonical KHÔNG moved)
DEPLOYED_SHA               = UNKNOWN — không deploy được từ session; chờ bằng chứng Render của Owner
CANONICAL_DELTA_VERIFIED   = d7a1154..c2142dd = 4 commit docs-only; git diff app/ tools/ alembic.ini
                             render.yaml Dockerfile = RỖNG → cây mã deploy == cây mã đã E2 ACCEPT (S092)
ALEMBIC_HEAD_IN_SHA        = 0002_snapshots (tools/db/__init__.py); Dockerfile CMD chạy
                             `alembic upgrade head` trước gunicorn (fail-closed)
STOP_REASON                = NO_PRODUCTION_EGRESS + WORKBOOK_NOT_IN_SESSION
EGRESS_EVIDENCE            = reports.tinphatcrm.com:443 và api.render.com:443 → CONNECT 403
                             (agent proxy `connect_rejected` — policy denial, không phải lỗi tạm thời)
WORKBOOK_EVIDENCE          = So_chi_tiet_ban_hang_8.xlsx KHÔNG có trong environment (find toàn hệ
                             thống = 0 kết quả; data/samples/ rỗng). KHÔNG sinh file thay thế.
CHECK-PRA002-14            = PASS   (E1 real data, S091 closeout — không đổi)
CHECK-PRA002-15            = NOT_TESTED (KHÔNG đổi — không có bằng chứng production; Owner thực hiện)
CHECK-PRA002-17            = PASS   (E2 toàn task, S092 — không đổi)
COMPLETION_GATE            = CHƯA THOẢ — còn đúng một gate REQUIRED: CHECK-PRA002-15
TASK-PRA-002               = IN_PROGRESS
BLOCKING_FINDINGS          = 0  (không phát hiện defect; chặn là ACCESS, không phải defect production path)
CODE_REQUIRED              = NO       PRODUCTION_CODE_ADDED = 0 dòng
CHANGE_BUDGET_STATE        = 1.460 / 1.500   REMAINING = 40 LOC (KHÔNG chạm)
REVIEW_BUDGET_STATE        = 1 / 2 USED · 1 REMAINING (phiên này không tiêu repair cycle)
TRACKING_CHANGED           = NO
OWNER_RUNBOOK              = docs/sessions/S093-pra-002-production-acceptance.md mục 5 (6 bước UI tối thiểu)
                             + mục 6 (oracle nghiệm thu để đối chiếu)
EVIDENCE                   = docs/sessions/S093-pra-002-production-acceptance.md
NEXT_VERTICAL_ACTION       = Owner chạy runbook mục 5 trên Render + reports.tinphatcrm.com, trả bằng
                             chứng về → đóng CHECK-PRA002-15 → TASK-PRA-002 DONE.
                             PRA-003 (Tổng quan + Nhân viên) CHỈ mở sau khi PRA-002 DONE.
```

## CANONICAL CURRENT STATE — TASK-PRA-002 (lịch sử, 2026-09-03, S092 WHOLE-TASK E2)

Cập nhật sau **Independent Review E2 cấp TOÀN TASK**. Các khối bên dưới giữ nguyên
như bản ghi lịch sử đúng của phiên đó; khi mâu thuẫn về trạng thái *hiện tại*,
khối này đúng.

```text
SESSION                    = S092 — PRA-002 Whole-Task Independent Review E2 (INDEPENDENT REVIEW, docs-only)
REVIEW_RESULT              = PASS
FINAL_ACCEPTANCE           = ACCEPT
TASK-PRA-002               = IN_PROGRESS   (KHÔNG DONE — CHECK-PRA002-15 Production Acceptance chưa PASS)
CANONICAL_SHA              = d7a1154a2892e5869e286e10da49f750aa0611df (khớp EXPECTED — canonical KHÔNG moved)
RDA_EVIDENCE_SHA           = 14499dd6e8f193c5656b85c47b7181a169e32709 (= canonical + 3 commit docs-only; 0 production code)
IMPLEMENTATION_LINEAGE     = A 80c6fe1→b0ecab7→27b9d1c · B 7658c5e→d2c7691→bfe7008 · C1 3cd92ea→579b497→d7a1154;
                             diff app/+tools/ sau accepted C1 (579b497..d7a1154) = RỖNG
E2_REPRODUCED_ON_PG        = PostgreSQL 16.13 thật cô lập: alembic 0002_snapshots (up/down) · CHECK-03/04/05/07/08/09 ·
                             FIND-PRA002-A1 invariant [1,2,3,4] · route web xac-nhan-du 400/400/302/409 ·
                             persist sau restart · reappearance is_active dẫn xuất
TESTS (reviewer tự chạy)   = full 1805 passed / 11 skipped + 1 test môi trường (clone shallow thiếu commit base
                             740f396a…; PASS sau git fetch --unshallow) · Golden 58 passed / 2 skipped ·
                             PRA-002 focused 211 · PRA-001 101 · test_demo 13 · git diff --check sạch ·
                             validators PASS (reference_integrity 3 pre-existing REM-T06 → DEFER)
LOC_BUDGET (đo lại độc lập) = A 1.104 · B 289 · C1 67 · RDA +0 → 1.460 / 1.500, REMAINING = 40 (KHỚP)
REVIEW_BUDGET              = 1 / 2 USED · 1 REMAINING (review toàn task KHÔNG tiêu cycle — 0 BLOCKING)
BLOCKING_FINDINGS          = 0
NON_BLOCKING               = A2/A3/B2/B3/B4/FIND-RDA-01/FIND-RDA-02 giữ DEFER; không finding mới
CHECK-PRA002-14            = PASS   (E1 real data — provenance review E2, không rerun)
CHECK-PRA002-15            = NOT_TESTED (Production Acceptance — Owner deploy Render; KHÔNG deploy trong review)
CHECK-PRA002-17            = PASS   (E2 toàn task)
INTEGRATE_RDA_DOCS_READY   = YES    (RDA docs 14499dd + E2 record — Controlled Integration là bước kế tiếp, KHÔNG làm trong review)
PRODUCTION_ACCEPTANCE_READY= YES    (sau Controlled Integration docs)
TRACKING_CHANGED           = NO      PRODUCTION_CODE_ADDED = 0
EVIDENCE                   = docs/reviews/TASK-PRA-002-INDEPENDENT-REVIEW-RECORD.md
NEXT_VERTICAL_ACTION       = Controlled Integration RDA/E2 docs vào canonical, rồi PRA-002 Production Acceptance (CHECK-15)
```

## CANONICAL CURRENT STATE — TASK-PRA-002 (lịch sử, 2026-09-03, S091 CLOSEOUT)

Cập nhật sau **RDA closeout tiếp nối Owner confirmation tường minh**. Các khối
bên dưới giữ nguyên như bản ghi lịch sử đúng của phiên đó; khi mâu thuẫn về
trạng thái *hiện tại*, khối này đúng.

```text
SESSION                    = S091 (phần 2) — PRA-002 RDA Closeout (EVIDENCE ONLY)
RDA_CLOSEOUT_RESULT        = PASS
TASK-PRA-002               = IN_PROGRESS   (KHÔNG DONE — CHECK-15 Production Acceptance chưa PASS)
CANONICAL_SHA              = d7a1154a2892e5869e286e10da49f750aa0611df (khớp EXPECTED)
OWNER_CONFIRMATION         = "Đúng, đây là file đầy đủ 01/09–03/09." — OWNER_DECISION, không phải AI inference
COVERAGE_CONFIRMATION      = POST /du-lieu/snapshot/SNAP-20260903021014-7b421983/xac-nhan-du
                             (tu_ngay 2026-09-01 · den_ngay 2026-09-03 · xac_nhan=1) → HTTP 302
                             HEADER_CONSISTENT → CONFIRMED_COMPLETE ·
                             confirmed_range 2026-09-01..2026-09-03 ·
                             confirmed_at 2026-09-03T02:27:08+00:00 · n_removed_candidate 0
REAL_RDA_EVIDENCE          = GIỮ NGUYÊN từ S090/S091 phần 1, không rerun/không diễn giải lại:
                             A ⊂ B PROVEN · state(A,B) == state(B) PROVEN ·
                             SAME 35 · INSERT 13 · SOURCE_CHANGED 13 (thật) · COLLISION 0 ·
                             RESULT_REVISED 0 · exact reupload B SAME 61, source version không tăng
RDA4                       = PASS — PASS_REAL (cơ chế, 13 thay đổi kế toán thật) +
                             PASS_CONTROLLED_COPY (assertion lớp trường tiền):
                             đúng 1 SOURCE_CHANGED · changed_fields = sell_price + total_sales_raw
                             ("7800000" → "8000000") · version cũ đọc được · current = version mới ·
                             SUM(total_sales) +200.000 đúng delta · 0 cờ khác
RDA5                       = PASS (CONTROLLED_COPY_EVIDENCE) — trước xác nhận n_not_seen 1;
                             sau POST xac-nhan-du n_removed_candidate 1, flag
                             REMOVED_IN_SOURCE_CANDIDATE (from_version_id 72, scope CONFIRMED);
                             dòng bị xoá VẪN current VẪN trong SUM (BH73923, 13.350.000);
                             current 61 dòng / 40 đơn / net 593.750.000 KHÔNG đổi;
                             COUNT(*) mọi bảng fact không giảm qua 4 mốc
RDA5_REAL_RESULT           = REMOVED_CANDIDATE = 0 trên dữ liệu thật (đúng: A ⊂ B) — không phải failure
RDA6                       = PASS — Golden 58 passed / 2 skipped; mệnh đề cohort S068 trong bảng
                             mục 15 là CÓ ĐIỀU KIỆN ("nếu có trong máy") nên không kích hoạt;
                             KHÔNG reconstruct, KHÔNG giả PASS
CONTROLLED_COPY_PROVENANCE = dẫn xuất từ REAL snapshot B (SHA256 7b421983...ce901) bằng openpyxl
                             có sẵn (tiền lệ tests/test_pipeline_history_vertical.py::cut_workbook);
                             chỉ trong scratchpad · KHÔNG commit · B gốc KHÔNG sửa (SHA trước == sau) ·
                             PostgreSQL 16.13 cô lập rda_ab · không production · không Tracking mutation ·
                             KHÔNG tạo make_snapshot_variants/CLI/parser/dependency mới
                             B'  SHA256 73b0ba45f46bc6ae26a98dfc4276aa3070916ba4e52888ac5132331fbfd91ade
                             B'' SHA256 b366c54570f0ef9d14238e76032d8d80404e8268a2b8fa59ee666f333e683f79
REQUIRED_GATE_MATRIX       = RDA-1 PASS_REAL · RDA-2 PASS_REAL · RDA-3 PASS_REAL ·
                             RDA-4 PASS_REAL + PASS_CONTROLLED_COPY · RDA-5 PASS_CONTROLLED_COPY ·
                             RDA-6 PASS_REAL
CHECK-PRA002-14            = PASS   (toàn bộ REQUIRED acceptance oracle bảng mục 15 đã đạt)
CHECK-PRA002-15            = NOT_TESTED — Production Acceptance trên Render (Owner; phiên KHÔNG deploy)
CHECK-PRA002-17            = NOT_TESTED ở cấp TOÀN TASK (PASS cho slice A + B + C1) — ngoài phạm vi RDA
FIND-RDA-01                = OWNER_SEMANTIC_CONFIRMED · CODE_REQUIRED = NO ·
                             parser repair DEFERRED · không mở rộng Tháng/Quý/Năm
CODE_REQUIRED              = NO       PRODUCTION_CODE_ADDED = 0 dòng
CHANGE_BUDGET_STATE        = 1.460 / 1.500   REMAINING = 40 LOC   (KHÔNG đổi, KHÔNG dùng)
REVIEW_BUDGET_STATE        = 1 / 2 USED · 1 REMAINING (RDA evidence không tiêu repair cycle)
TRACKING_CHANGED           = NO
EVIDENCE                   = docs/sessions/S091-pra-002-real-overlap-snapshot-b.md (phần 2)
NEXT_VERTICAL_ACTION       = PRA-002 Production Acceptance (CHECK-PRA002-15, Owner deploy Render)
                             + Independent Review E2 cấp toàn task (CHECK-PRA002-17).
                             KHÔNG deploy trong phạm vi RDA
```


## CANONICAL CURRENT STATE — TASK-PRA-002 (lịch sử, 2026-09-03, S091 phần 1)

Cập nhật sau **Real Data Acceptance overlap A → B trên HAI workbook kế toán
THẬT** do Owner cung cấp (continuation của S090). Khối S090 và các khối cũ hơn
bên dưới giữ nguyên như bản ghi lịch sử đúng của phiên đó; khi mâu thuẫn về
trạng thái *hiện tại*, khối này đúng.

```text
SESSION                    = S091 — PRA-002 Real Data Acceptance: real overlap A → B (EVIDENCE ONLY)
RESULT                     = PARTIAL — RDA-1/2/3 PASS · RDA-4 PARTIAL · RDA-5 BLOCKED · RDA-6 PARTIAL
TASK-PRA-002               = IN_PROGRESS   (KHÔNG DONE)
CANONICAL_SHA              = d7a1154a2892e5869e286e10da49f750aa0611df  (khớp EXPECTED — KHÔNG moved)
BRANCH_AUTHORITY           = AUTHORITY_OK (0 behind default)
SNAPSHOT_A                 = So_chi_tiet_ban_hang_7.xlsx — REAL_OWNER_PROVIDED, exact bytes CÒN
                             trong environment; SHA256 e1c6cec2...0bfa56 verify lại KHỚP S090
SNAPSHOT_B                 = So_chi_tiet_ban_hang_8.xlsx — REAL_OWNER_PROVIDED
                             SHA256 7b421983a73210637d618806446e4a4e3a2d03e3b367694e7ee6ecb3207ce901
                             18.209 bytes · header "Từ ngày 01/09/2026 đến ngày 03/09/2026"
                             61 dòng · 40 đơn · detected 2026-09-01..2026-09-03
                             (54 dòng 01/09 · 7 dòng 03/09 · 0 dòng 02/09)
                             KHÔNG commit · KHÔNG sửa · SHA256 trước == sau
A_B_RELATIONSHIP           = A ⊂ B XÁC NHẬN — 0 khoá chỉ có ở A; 13 khoá mới ở B
POSTGRESQL_CONTEXT         = PostgreSQL 16.13 THẬT, hai DB cô lập non-production:
                             rda_ab (A→B→B) và rda_bonly (chỉ B); cả hai alembic_version = 0002_snapshots
PRODUCTION_PATH            = route production POST /run — không patch production code
B_FIRST_IMPORT             = HTTP 302 · SNAP-20260903021014-7b421983 ·
                             INSERT 13 · SAME 35 · SOURCE_CHANGED 13 · COLLISION 0 ·
                             NOT_SEEN 0 · REMOVED_CANDIDATE 0 · RESULT_REVISED 0
                             (35+13 = 48 = toàn bộ khoá A vẫn còn)
SOURCE_CHANGED_EVIDENCE    = OBSERVED_IN_REAL_DATA — 13 dòng 01/09 được kế toán bổ sung
                             delivery_cost (60.000–130.000) và 8 dòng thêm imei;
                             MỌI trường tiền giữ nguyên. version cũ IMMUTABLE (v1 vẫn thuộc
                             snapshot A, delivery_cost vẫn NULL), version mới APPENDED (v2 × 13),
                             current → version mới (0 khoá trỏ sai), 13 flag SOURCE_CHANGED với
                             13 from/to version id phân biệt, 0 cờ loại khác
STATE_AB_EQUALS_STATE_B    = PROVEN — state(A,B) == state(B) khớp tuyệt đối:
                             current tuple identical · key_set identical (61) ·
                             tập (khoá, line_fingerprint) identical · per_order identical (40 đơn)
NO_DOUBLE_COUNT            = PROVEN — net A=468.300.000 · A→B=593.550.000 · B=593.550.000 ·
                             naive(A+B)=1.061.850.000 → A→B == B ≠ naive.
                             dòng 48/61/61 (naive 109) · đơn 34/40/40 (naive 74)
B_EXACT_REUPLOAD           = PASS — duplicate_of đúng · SAME 61 = line_count · INSERT 0 ·
                             SOURCE_CHANGED 0 · source version 74 → 74 (không tăng) ·
                             result version 109 → 170 (history observation) · current state identical
RESULT_REVISED             = NOT_OBSERVED_IN_REAL_DATA (0 khoá có result_fingerprint khác nhau) — ĐÚNG
ACCOUNTING_SAFETY          = PASS — khớp tuyệt đối oracle app.pipeline.run_import (GB-4) và footer
                             workbook: 40 đơn / 61 dòng / SL 71 / chiết khấu 200.000 /
                             doanh số 593.750.000 / net 593.550.000 · unmapped_lines 0
AUTO_PENDING_SAFETY        = 61/61 PENDING · price_source "Pending" · 0 giá nhập bịa · 0 lợi nhuận bịa.
                             REAL ACCOUNTING/PERSISTENCE PATH = tested;
                             REAL AUTO PATH = not tested (Cloud không có secret Tracking; KHÔNG fake)
COVERAGE_STATE             = B: HEADER_CONSISTENT (header ⊇ detected) · A: DETECTED_ONLY (giữ nguyên)
GOLDEN                     = 58 passed, 2 skipped
LEGACY_NON_REGRESSION      = /du-lieu 200 (cả 3 snapshot) · 3 trang snapshot 200 · /nhan-vien 200
                             (cờ SOURCE chỉ hiện trên trang snapshot B đầu tiên — đúng)
FIND-RDA-01                = OWNER_SEMANTIC_CONFIRMED (cũ: DATA_SHAPE_UNKNOWN).
                             Rule Owner: "Ngày D tháng M năm YYYY" = coverage đúng ngày đó.
                             Parser repair KHÔNG cần: confirm_coverage chỉ gọi confirmation_error,
                             không nhánh nào đòi HEADER_CONSISTENT → snapshot DETECTED_ONLY vẫn
                             xác nhận được → DEFER. Không mở rộng parser Tháng/Quý/Năm
CHECK-PRA002-14            = BLOCKED (không còn NOT_TESTED). RDA-1 PASS · RDA-2 PASS ·
                             RDA-3 PASS (sai lệch ghi rõ: n_same 35 ≠ 48 vì 13 khoá A thực sự bị
                             kế toán sửa) · RDA-4 PARTIAL (cơ chế chứng minh bằng dữ liệu thật;
                             assertion tiền của kịch bản --edit-line NOT_OBSERVED_IN_REAL_DATA) ·
                             RDA-5 BLOCKED (cần export thật có chứng từ biến mất + Owner
                             POST xac-nhan-du) · RDA-6 PARTIAL (Golden PASS; cohort S068 vắng)
CHECK-PRA002-15            = NOT_TESTED — Production Acceptance pending (Owner; phiên KHÔNG deploy)
CODE_REQUIRED              = NO       PRODUCTION_CODE_ADDED = 0 dòng
CHANGE_BUDGET_STATE        = 1.460 / 1.500      REMAINING = 40 LOC   (KHÔNG đổi)
TRACKING_CHANGED           = NO (READ-ONLY)
OWNER_CONFIRMATION_REQUIRED= YES — SNAPSHOT_ID = SNAP-20260903021014-7b421983,
                             RANGE = 2026-09-01..2026-09-03. Phiên KHÔNG POST xac-nhan-du
EVIDENCE                   = docs/sessions/S091-pra-002-real-overlap-snapshot-b.md
NEXT_VERTICAL_ACTION       = Owner xác nhận coverage snapshot B; sau đó quyết đường đóng RDA-4/5
                             (export thật có chứng từ sửa giá / bị xoá, hoặc cho phép controlled
                             copy ASSUMPTION D14). Không deploy trong phạm vi RDA
```


## CANONICAL CURRENT STATE — TASK-PRA-002 (lịch sử, 2026-09-02, S090)

Cập nhật sau **Real Data Acceptance trên workbook kế toán THẬT do Owner cung
cấp trong phiên** (continuation của S089). Khối S088 và các khối cũ hơn bên
dưới giữ nguyên như bản ghi lịch sử đúng của phiên đó; khi mâu thuẫn về trạng
thái *hiện tại*, khối này đúng.

```text
SESSION                    = S090 — PRA-002 Real Data Acceptance (EVIDENCE ONLY)
RESULT                     = PARTIAL — RDA-1 PASS · RDA-2 PASS · RDA-6 PASS (Golden) ·
                             RDA-3/4/5 BLOCKED_OWNER_INPUT
TASK-PRA-002               = IN_PROGRESS   (KHÔNG DONE — RDA chưa đủ bảng mục 15;
                             Production Acceptance chưa xong)
CANONICAL_SHA              = d7a1154a2892e5869e286e10da49f750aa0611df  (khớp EXPECTED — canonical KHÔNG dịch chuyển)
BRANCH_AUTHORITY           = AUTHORITY_OK (0 ahead / 0 behind default)
REAL_WORKBOOK              = So_chi_tiet_ban_hang_7.xlsx — REAL_OWNER_PROVIDED
                             (KHÔNG commit, KHÔNG sửa; SHA256 trước == sau)
REAL_WORKBOOK_SHA256       = e1c6cec2e27e5fd831a818cda5fd538fee53e4b5a3e7cb7d9af3e729c40bfa56
REAL_DATA_PROFILE          = 48 dòng · 34 đơn · 2026-09-01..2026-09-01 · 16.196 bytes ·
                             BH 48/48 khớp `BH\d+` · 0 đơn nhiều ngày
POSTGRESQL_CONTEXT         = PostgreSQL 16.13 THẬT, database cô lập `rda_pra002` (non-production);
                             `alembic upgrade head` → alembic_version = 0002_snapshots
PRODUCTION_PATH            = route production `POST /run` (app/web/server.py) trên
                             SnapshotRepository PostgreSQL — không patch production code
RDA1_FIRST_IMPORT          = PASS — HTTP 302 · SNAP-20260902154531-e1c6cec2 ·
                             line_count 48 · order_count 34 · INSERT 48 · SAME 0 ·
                             SOURCE_CHANGED 0 · COLLISION 0 · NOT_SEEN 0 ·
                             REMOVED_CANDIDATE 0 · RESULT_REVISED 0
RDA2_EXACT_REUPLOAD        = PASS — HTTP 302 · SNAP-...-01 ·
                             duplicate_of_snapshot_id = snapshot #1 · SAME 48 = line_count ·
                             INSERT 0 · SOURCE_CHANGED 0 · mọi cờ 0 · không cờ SOURCE trên trang
SOURCE_VERSION_EVIDENCE    = 48 version, version_no>1 = 0, MAX(version_no) = 1
                             → exact reupload KHÔNG tạo source version mới
RESULT_VERSION_EVIDENCE    = 48 → 96 (history observation theo frozen Slice A contract);
                             0 khoá có result_fingerprint khác nhau giữa hai run
NO_DOUBLE_COUNT            = PROVEN — current state T1 (sau RDA-1) == T2 (sau RDA-2):
                             lines 48 · orders 34 · total_sales 468.300.000 ·
                             raw_sales 468.500.000 · qty 55 · discount 200.000 ·
                             keyset identical · per-order identical · 0 flag
ACCOUNTING_SAFETY          = PASS — khớp tuyệt đối oracle `app.pipeline.run_import` (GB-4)
                             VÀ footer "Tổng cộng" của chính workbook:
                             34 đơn / 48 dòng / SL 55 / chiết khấu 200.000 /
                             doanh số 468.500.000 / net 468.300.000 · unmapped_lines 0.
                             AUTO/PENDING safety: input_orders == accounted_orders = 34;
                             48/48 PENDING, 0 giá nhập bịa, 0 lợi nhuận bịa
RDA_TRACKING_LIMITATION    = Cloud không có secret Tracking → capture giá RỖNG (đúng tiền lệ
                             tests/test_pipeline_history_vertical.py) → auto_orders = 0.
                             Chiều an toàn ĐƯỢC chứng minh; đường AUTO CHƯA thực thi trên dữ liệu thật
COVERAGE_STATE             = DETECTED_ONLY (detected 2026-09-01..2026-09-01;
                             header_date_min/max NULL) — KHÔNG tự nâng CONFIRMED_COMPLETE
SOURCE_CHANGED             = NOT_OBSERVED_IN_REAL_DATA (một workbook không đổi không thể tự sinh)
RESULT_REVISED             = 0 — kết quả ĐÚNG, không phải thiếu sót (C1 đã có E2 evidence riêng)
RDA6_GOLDEN                = PASS — tests/test_golden_baseline.py → 58 passed, 2 skipped;
                             cohort S068 NOT_TESTED (không có trong môi trường)
LEGACY_NON_REGRESSION      = GET /du-lieu 200 · /du-lieu/snapshot/<id> 200 (cả hai) ·
                             /nhan-vien 200
CHECK-PRA002-14            = NOT_TESTED (giữ nguyên — hợp đồng frozen đòi ĐỦ bảng mục 15).
                             RDA-1 PASS · RDA-2 PASS · RDA-6 PARTIAL ·
                             RDA-3/4/5 BLOCKED_OWNER_INPUT
CHECK-PRA002-15            = NOT_TESTED — Production Acceptance pending (Owner; phiên KHÔNG deploy)
FINDINGS                   = FIND-RDA-01 header dạng thứ ba `Ngày 01 tháng 9 năm 2026` →
                             DATA_SHAPE_UNKNOWN + OWNER_DECISION_REQUIRED, NON_BLOCKING
                             (hệ thống fail-safe đúng: DETECTED_ONLY, không đoán, không nới regex).
                             FIND-RDA-02 một dòng `Suspicious` → NON_BLOCKING, có ở cả oracle.
                             KHÔNG có BLOCKING_PRODUCTION_DEFECT
CODE_REQUIRED              = NO
PRODUCTION_CODE_ADDED      = 0 dòng
CHANGE_BUDGET_STATE        = 1.460 / 1.500      REMAINING = 40 LOC   (KHÔNG đổi)
TRACKING_CHANGED           = NO (READ-ONLY — không gọi, không sửa)
OWNER_CONFIRMATION_REQUIRED= YES (chỉ để đóng RDA-5) — SNAPSHOT_ID = SNAP-20260902154531-e1c6cec2,
                             RANGE = 2026-09-01..2026-09-01. Phiên KHÔNG POST xac-nhan-du
OWNER_SECOND_FILE_REQUIRED = YES (cho RDA-3) — export THẬT chứa trọn 2026-09-01 và rộng hơn (A ⊂ B)
EVIDENCE                   = docs/sessions/S090-pra-002-real-data-acceptance.md
NEXT_VERTICAL_ACTION       = Owner cung cấp export thật thứ hai (A ⊂ B) HOẶC cho phép đường
                             controlled copy ASSUMPTION D14 → chạy RDA-3/4/5 → đóng CHECK-PRA002-14
```


## CANONICAL CURRENT STATE — TASK-PRA-002 (lịch sử, 2026-09-02, S088)

Cập nhật sau **Controlled Integration slice C1** vào canonical. Khối S087 và các
khối cũ hơn bên dưới giữ nguyên như bản ghi lịch sử đúng của phiên đó; khi mâu
thuẫn về trạng thái *hiện tại*, khối này đúng.

```text
SESSION                    = S088 — PRA-002 Slice C1 Controlled Integration (INTEGRATION ONLY)
RESULT                     = PASS
C1_FINAL_STATUS            = ACCEPTED + INTEGRATED
TASK-PRA-002               = IN_PROGRESS   (KHÔNG DONE — RDA + Production Acceptance chưa xong)
SLICE A                    = IMPLEMENTED · REVIEWED · ACCEPTED · INTEGRATED
SLICE B                    = IMPLEMENTED · REVIEWED · ACCEPTED · INTEGRATED
SLICE C1                   = IMPLEMENTED · REVIEWED · ACCEPTED · INTEGRATED
CANONICAL_BEFORE_SHA       = bfe7008f7dfd42c90465f6d32ca38b4c2dfeaf82  (khớp EXPECTED — canonical KHÔNG dịch chuyển)
ACCEPTED_C1_SHA            = 579b497ba7427d66838d9b2769863ccca20a104e  (== origin/claude/pra-002-slice-c-plan-jg798m)
REVIEW_LINEAGE             = bfe7008 → 3cd92ea (implementation) → 579b497 (Independent Review E2, docs-only).
                              Cả 3cd92ea lẫn 579b497 đều là tổ tiên của ACCEPTED_C1_SHA; BASE là tổ tiên của HEAD
INTEGRATION_METHOD         = git merge --ff-only  → fast-forward THUẦN.
                              KHÔNG squash · KHÔNG rebase · KHÔNG cherry-pick · KHÔNG force · KHÔNG merge commit
CANONICAL_AFTER_FF_SHA     = 579b497ba7427d66838d9b2769863ccca20a104e
TREE_EQUIVALENCE           = IDENTICAL — tree SHA canonical == tree SHA accepted (ba9220ccd3d964331aab3762600d44237ea6bc0a);
                              git diff HEAD..579b497 rỗng
REMOTE_CANONICAL_SHA       = 579b497ba7427d66838d9b2769863ccca20a104e  (fetch lại sau push, khớp local)
BRANCH_AUTHORITY           = AUTHORITY_OK (0 ahead / 0 behind default; DIVERGENCE WITHIN_LIMITS)
TESTS                      = tree IDENTICAL với accepted tree đã E2 verify → KHÔNG rerun full suite (đúng policy).
                              Smoke: C1 focused 83 passed · Slice A/B persistence 97 passed ·
                              git diff --check sạch. Bằng chứng đầy đủ (full 1806/11, Golden 81/2,
                              PRA-001 101, PostgreSQL 16.13 PASS) giữ nguyên từ S087
VALIDATORS                 = structure PASS · project_state PASS · task_completion PASS · evidence PASS ·
                              reference_integrity FAIL với ĐÚNG 3 pre-existing REM-T06 (/README.md,
                              CODE_OF_CONDUCT.md, CONTRIBUTING.md) → DEFER, KHÔNG phải integration blocker
CHECK-PRA002-08            = PASS (E2 — reviewer tái lập độc lập trên PostgreSQL 16.13 thật, S087)
CHECK-PRA002-14            = NOT_TESTED — RDA pending (Owner; cần workbook thật)
CHECK-PRA002-15            = NOT_TESTED — Production Acceptance pending (Owner)
CHECK-PRA002-17            = PASS cho slice A + B + C1; CHƯA PASS ở cấp toàn task
REVIEW_BUDGET_USED         = 1 / 2        REVIEW_BUDGET_REMAINING = 1
                              (đối chiếu đã chốt ở review commit 579b497 — KHÔNG sửa lại,
                              KHÔNG tiêu repair cycle trong integration)
CHANGE_BUDGET_STATE        = 1.460 / 1.500      REMAINING = 40 LOC
                              (A 1.104 + B 289 + C1 67. KHÔNG dùng lại 1.393/107 làm ngân sách hiện hành)
TRACKING_CHANGED           = NO
PRODUCTION_CODE_ADDED      = 0 dòng trong phiên integration
EVIDENCE                   = docs/reviews/TASK-PRA-002-SLICE-C1-INDEPENDENT-REVIEW-RECORD.md
NEXT_VERTICAL_ACTION       = PRA-002 Real Data Acceptance Preparation / Execution
                              (KHÔNG mặc định là "Slice C2 implementation" — xem phân loại bên dưới)
```

**Phân loại phần việc PRA-002 còn lại — KHÔNG mặc định là code.**

| Nhóm | Nội dung | CODE_REQUIRED? |
|---|---|---|
| A. RDA / evidence | `CHECK-PRA002-14` RDA-1..6 trên workbook thật (mục 15) | **KHÔNG** trên đường ưu tiên — mục 15 chỉ định "hai export thật" do Owner cung cấp. `tools/analysis/make_snapshot_variants` chỉ thuộc đường dự phòng controlled copy (ASSUMPTION D14), và mục 792–793 cho phép `NOT_TESTED` + gate Owner |
| B. PostgreSQL verification | PRA-002.C3 — kịch bản A→B→B'→B'' trên PostgreSQL 16 local, đo `ru_maxrss` | Là **thực thi kịch bản + ghi bằng chứng**, không phải production feature |
| C. Production deployment | deployment doc + deploy | Owner / vận hành |
| D. Owner production acceptance | `CHECK-PRA002-15` (mục 16) | Owner |

Không nhóm nào chứng minh được `CODE_REQUIRED` trên production path ngay lúc
này. Vì vậy bước kế tiếp là **chuẩn bị/thực thi RDA**, không phải mở thêm mã.

**Luật 40 LOC (bắt buộc đọc trước khi viết bất kỳ dòng mã nào).** 40 LOC còn
lại **KHÔNG** phải ngân sách để tiện tay sửa incidental finding. KHÔNG dùng cho:
`FIND-PRA002-A2`, `A3`, `B2`, `B3`, `B4`, same-second sequencing, `REM-T06`,
CSRF, pagination, acknowledgement, hay refactor. Nếu RDA phát hiện thiếu
capability production cần **> 40 LOC** → **DỪNG TRƯỚC KHI VIẾT MÃ** và lập
`CHANGE_BUDGET` proposal cho Owner. Nếu RDA phát hiện hình dạng dữ liệu thật mà
contract không nhận ra → ghi `UNKNOWN / OWNER_DECISION_REQUIRED`, KHÔNG mở rộng
parser/thuật toán (mục 794–796).

## CANONICAL CURRENT STATE — TASK-PRA-002 (lịch sử, 2026-09-02, S087)

Cập nhật sau **Independent Review E2 slice C1**. Khối S086 và các khối cũ hơn
bên dưới giữ nguyên như bản ghi lịch sử đúng của phiên đó; khi mâu thuẫn về
trạng thái *hiện tại*, khối này đúng.

```text
SESSION                    = S087 — PRA-002 Slice C1 Independent Review E2 (INDEPENDENT REVIEW)
REVIEW_RESULT              = PASS
FINAL_ACCEPTANCE           = ACCEPT
INTEGRATION_READY          = YES
TASK-PRA-002               = IN_PROGRESS  (slice A INTEGRATED; slice B INTEGRATED;
                              slice C1 REVIEWED · ACCEPTED — chờ Controlled Integration)
SLICE C1                   = IMPLEMENTED · REVIEWED · ACCEPTED  (CHƯA integrate, CHƯA DONE)
REVIEW_BASE_SHA            = bfe7008f7dfd42c90465f6d32ca38b4c2dfeaf82  (== origin/claude/extract-upload-repo-gq2ws4;
                              canonical KHÔNG dịch chuyển — fetch và so khớp trước khi đọc dòng mã nào)
REVIEW_HEAD_SHA            = 3cd92eae3035dd40aaf3f64bd3ba96a1d1b49cd0  (== origin/claude/pra-002-slice-c-plan-jg798m)
BRANCH_AUTHORITY           = AUTHORITY_OK (BRANCH_WITH_UPSTREAM; DIVERGENCE WITHIN_LIMITS)
VERSION_ID_SEMANTICS       = GIẢI QUYẾT BẰNG THẨM QUYỀN, không bằng "DB cho phép". Frozen contract mục 12 ghi
                              tường minh: from_version_id = "source hoặc result version cũ (THEO KIND)" →
                              generic version reference. RESULT_REVISED dùng result-version id là ĐÚNG hợp đồng.
                              Kiểm chứng máy: mọi đầu version của cờ đều thuộc id space của
                              order_line_result_version. KHÔNG redesign schema, KHÔNG thêm FK/cột
BLOCKING findings          = 0
NON_BLOCKING findings      = FIND-PRA002-C1-N1 (bookkeeping ledger) — ĐÃ SỬA trong phiên, docs-only
REPAIR_CYCLES_THIS_SESSION = 0
REVIEW_BUDGET_USED         = 1 / 2       (PRA-002-RC-1 — FIND-PRA002-A1, Independent Review slice A)
REVIEW_BUDGET_REMAINING    = 1
REVIEW_BUDGET_RECONCILIATION = GIẢI QUYẾT. Khối máy đọc của ledger ghi sai `repair_cycles_used: 0`;
                              thẩm quyền rõ ba chiều: V4.1 §3 tính cycle theo LẦN SỬA + danh sách `cycles:`
                              có đúng 1 mục có base_sha/head_sha + prose S084 ghi "lineage vẫn 1/2"; cùng quy
                              ước với TASK-GOLDEN-BASELINE-001. Đã sửa thành 1/1. KHÔNG tiêu cycle cho bookkeeping
TESTS (reviewer tự chạy)   = full suite 1806 passed, 11 skipped · Golden 81 passed, 2 skipped
                              C1 focused 83 passed · Slice A/B persistence 97 passed · PRA-001 101 passed
                              PostgreSQL 16.13 THẬT: vertical A+B+C1 do reviewer tự viết → PASS
MUTATION (độc lập)         = 4 đột biến ngữ nghĩa đều bị bắt: bỏ điều kiện SAME (4 fail) · sai tập trường diff
                              (8 fail) · tính revisions sau khi dịch con trỏ (6 fail) · cờ trỏ source version (1 fail)
CHANGE_BUDGET slice C1     = +67 — ĐO LẠI ĐỘC LẬP, khớp S086 TỪNG FILE (keys +2 · models +12 ·
                              reconciler +21 · history_store +32). Không refactor/minify để đạt số
CHANGE_BUDGET lineage      = 1.460 / 1.500        REMAINING_TO_HARD_STOP = 40 LOC
DATABASE                   = KHÔNG migration, KHÔNG schema change; 0002_snapshots vẫn head, không có 0003.
                              n_result_revised và FLAG_KINDS.RESULT_REVISED đã có SẴN ở BASE (git show bfe7008)
SLICE_B_REGRESSION         = coverage.py / extraction.py / history_writer.py / server.py UNCHANGED;
                              cờ khoá-có-mặt và cờ khoá-vắng-mặt rời nhau theo cấu trúc
CHECK-PRA002-08            = PASS (E2 — reviewer tái lập độc lập trên PostgreSQL 16.13 thật)
CHECK-PRA002-14            = NOT_TESTED (RDA — Owner)
CHECK-PRA002-15            = NOT_TESTED (Production Acceptance — Owner)
TASK-PRA-002 STATUS        = IN_PROGRESS (KHÔNG đánh DONE — RDA + Production Acceptance chưa xong)
TRACKING_CHANGED           = NO
EVIDENCE                   = docs/reviews/TASK-PRA-002-SLICE-C1-INDEPENDENT-REVIEW-RECORD.md
NEXT_VERTICAL_ACTION       = Controlled integration Slice C1 (KHÔNG bắt đầu RDA/C2)
```

## CANONICAL CURRENT STATE — TASK-PRA-002 (lịch sử, 2026-09-02, S086)

Cập nhật sau phiên implement **slice C1 (`RESULT_REVISED`)**. Khối S085 và các
khối cũ hơn bên dưới giữ nguyên như bản ghi lịch sử đúng của phiên đó; khi mâu
thuẫn về trạng thái *hiện tại*, khối này đúng.

```text
SESSION                    = S086 — PRA-002 Slice C1 Implementation (MAJOR)
TASK-PRA-002               = IN_PROGRESS  (slice A INTEGRATED; slice B INTEGRATED;
                              slice C1 IMPLEMENTED, chờ Independent Review E2)
SLICE_C1_RESULT            = PASS
SLICE A                    = IMPLEMENTED · REVIEWED · ACCEPTED · INTEGRATED
SLICE B                    = IMPLEMENTED · REVIEWED · ACCEPTED · INTEGRATED
SLICE C1                   = IMPLEMENTED — chờ Independent Review E2 (CHƯA integrate, CHƯA DONE)
BASE_SHA                   = bfe7008f7dfd42c90465f6d32ca38b4c2dfeaf82  (== origin/claude/extract-upload-repo-gq2ws4;
                              canonical KHÔNG dịch chuyển — đã fetch và so khớp trước khi mở việc)
BRANCH                     = claude/pra-002-slice-c-plan-jg798m  (đứng đúng tại canonical SHA lúc mở phiên:
                              0 ahead / 0 behind → phát triển trên nó LÀ phát triển từ exact canonical)
MIGRATION                  = KHÔNG có migration mới; KHÔNG schema change (tools/db/** không sửa một dòng).
                              Schema 0002_snapshots đã đủ: cột n_result_revised đã có, CHECK kind đã chứa
                              RESULT_REVISED, và from/to_version_id KHÔNG có FK nên tham chiếu result version hợp lệ
CONTRACT                   = RESULT_REVISED ⟺ (đã có current result) ∧ (nguồn SAME) ∧ (không COLLISION)
                              ∧ (result_fingerprint khác). SOURCE_CHANGED thắng; COLLISION → 0 cờ
FINGERPRINT                = sha256(status, accounting_purchase_price, eligible_kpi_profit) — đúng 3 trường F3
DETAIL_JSON                = chỉ diff 3 trường F3, dạng canon, json sort_keys → deterministic. KHÔNG PII
VERSION_REFS               = from_version_id/to_version_id trỏ order_line_result_version (cấp KẾT QUẢ),
                              KHÔNG dùng source version id
CURRENT_POINTER            = current_source_version_id GIỮ NGUYÊN; current_result_version_id ĐỔI;
                              result version cũ còn nguyên vẹn; KHÔNG tạo source version n+1
                              (đo trên PostgreSQL 16.13 thật: source COUNT 2→2, result COUNT 2→4)
TEMPLATE_CHANGED           = KHÔNG — snapshot.html render kind/cặp version/detail_json tổng quát;
                              chứng minh bằng test web thật, không bằng đọc code
SLICE_B_SAFETY             = NOT_SEEN/REMOVED/coverage/confirmation/is_active KHÔNG đổi một dòng;
                              khoá vắng mặt không thể sinh RESULT_REVISED (test khoá lại)
TRANSACTION                = phát hiện + result version + cờ + con trỏ + counter trong đúng engine.begin() đã có;
                              test ép lỗi giữa chừng → không có partial RESULT_REVISED state
TEST                       = full suite 1806 passed, 11 skipped (BASE bfe7008 = 1784/11 → +22 test, 0 skip thêm)
                              Golden 58 passed, 2 skipped (KHÔNG đổi); PRA-001 focused 81 passed
                              PostgreSQL 16.13 THẬT: alembic upgrade head + 113 passed
                              Mutation check: hoàn nguyên riêng app/ → 6 test mới FAIL đúng như phải thế
CHANGE_BUDGET slice C1     = 67 dòng logic production (LOW 55 / EXPECTED 73 / HIGH 95 của planning)
CHANGE_BUDGET lineage      = 1.393 (A+B) + 67 (C1) = 1.460 / dừng cứng 1.500
REMAINING_TO_HARD_STOP     = 40 LOC   ← siết lại đáng kể, phiên sau phải biết trước khi mở việc
LOC_METHOD                 = hiệu chuẩn lại từ đầu trong phiên này và tái lập ĐÚNG cả ba số đã chấp nhận:
                              slice A +1104, slice B +289 (khớp cả 5 dòng per-file), lineage +1393
CHECK-PRA002-08            = PASS (E1; bằng chứng persistence + PostgreSQL 16.13 thật đạt mức E2)
CHECK-PRA002-14            = NOT_TESTED (RDA — Owner)
CHECK-PRA002-15            = NOT_TESTED (Production Acceptance — Owner)
CHECK-PRA002-17            = PASS cho phần slice A + B + C1 hiện có; KHÔNG PASS ở cấp toàn task
TASK-PRA-002 STATUS        = IN_PROGRESS (KHÔNG đánh DONE — RDA + Production Acceptance chưa xong)
REVIEW_BUDGET_STATUS       = UNKNOWN_CONFLICT — ledger tự mâu thuẫn (khối máy đọc repair_cycles_used: 0
                              vs prose S085 "1/2" vs danh sách cycles có PRA-002-RC-1). C1 KHÔNG tự sửa;
                              Independent Review C1 phải xác minh TRƯỚC khi tiêu repair cycle mới
                              [ĐÃ GIẢI QUYẾT ở S087: đúng là 1/2, còn 1 — xem khối AUTHORITATIVE ở trên]
BLOCKING findings          = 0
NON_BLOCKING findings      = FIND-PRA002-C1-N1 (mâu thuẫn ledger review budget — governance, không phải production)
TRACKING_CHANGED           = NO
VALIDATORS                 = structure/project_state/task_completion/evidence PASS;
                              reference_integrity FAIL với ĐÚNG 3 pre-existing REM-T06 → DEFER, không phải blocker
EVIDENCE                   = docs/sessions/S086-pra-002-slice-c1-result-revised.md
NEXT_VERTICAL_ACTION       = Independent Review E2 Slice C1 (KHÔNG bắt đầu RDA/C2)
```

**Điều phiên sau phải biết.** Headroom CHANGE_BUDGET còn **40 dòng logic
production** trước dừng cứng 1.500. Slice C2/C3 (RDA thật, production
acceptance) phần lớn là việc Owner thực hiện thủ công và KHÔNG cần code; nếu
phần nào cần code vượt 40 dòng, mở đề xuất CHANGE_BUDGET cho Owner **TRƯỚC**
khi viết mã.

## CANONICAL CURRENT STATE — TASK-PRA-002 (AUTHORITATIVE, 2026-09-02, S085)

Cập nhật sau **Controlled Integration của slice B vào canonical**. Khối S084 bên
dưới (Independent Review E2) giữ nguyên như bản ghi lịch sử đúng của phiên đó;
khối này chỉ thêm sự kiện tích hợp — kết luận review không đổi.

```text
SESSION                    = S085 — PRA-002 Slice B Controlled Integration
TASK-PRA-002               = IN_PROGRESS  (slice A INTEGRATED; slice B INTEGRATED; slice C NEXT)
SLICE A                    = IMPLEMENTED · REVIEWED · ACCEPTED · INTEGRATED
SLICE B                    = IMPLEMENTED · REVIEWED · ACCEPTED · INTEGRATED
SLICE C                    = NEXT — bắt buộc BUDGET-AWARE PLAN trước implementation (xem dưới)
INTEGRATION_METHOD         = git merge --ff-only (KHÔNG squash/rebase/force/cherry-pick)
CANONICAL_BEFORE_SHA       = 27b9d1c5a578742450099c53f2f82411f07aa9dc
ACCEPTED_SLICE_B_SHA       = d2c7691210313ef82016a6c28106885e5f58c19a
                              (== origin/claude/pra-002-slice-b-snapshot-8rbwip; chứa 7658c5e + d2c7691)
CANONICAL_AFTER_SHA        = d2c7691210313ef82016a6c28106885e5f58c19a  (fast-forward, tree == accepted tree)
REMOTE_CANONICAL_SHA       = d2c7691210313ef82016a6c28106885e5f58c19a  (khớp local sau push + fetch lại)
TREE_EQUIVALENCE           = ĐÚNG (git rev-parse HEAD^{tree} == ACCEPTED_SLICE_B_SHA^{tree})
POST-INTEGRATION SMOKE     = slice B focused 79 passed; slice A reconciliation focused 96 passed;
                              git diff --check sạch trên toàn khoảng 27b9d1c..HEAD
                              (tree fast-forward y hệt accepted tree — không chạy lại full suite,
                              đúng thứ chỉ thị integration cho phép khi tree identical)
VALIDATORS                 = structure/project_state/task_completion/evidence PASS;
                              reference_integrity FAIL với ĐÚNG 3 pre-existing REM-T06
                              (/README.md, CODE_OF_CONDUCT.md, CONTRIBUTING.md) → DEFER, không phải integration blocker
CHECK-PRA002-06            = PASS
CHECK-PRA002-07            = PASS
CHECK-PRA002-08            = NOT_TESTED (slice C, NEXT)
CHECK-PRA002-14            = NOT_TESTED (Owner/RDA pending)
CHECK-PRA002-15            = NOT_TESTED (Owner/production pending)
CHECK-PRA002-17            = PASS cho phần slice A + slice B (evidence hiện có); KHÔNG PASS ở cấp toàn task —
                              frozen gate còn đòi CHECK-08/14/15 thuộc slice C
TASK-PRA-002 STATUS        = IN_PROGRESS (KHÔNG đánh DONE — slice C + RDA + Production Acceptance chưa xong)
CHANGE_BUDGET_STATE        = 1.393 / 1.500 (dừng cứng)   REMAINING_TO_HARD_STOP = 107 LOC
                              (giá trị authoritative từ Independent Review S084; số 1.346/154 của S083 đã bị supersede)
TRACKING_CHANGED           = NO
EVIDENCE                   = docs/reviews/TASK-PRA-002-SLICE-B-INDEPENDENT-REVIEW-RECORD.md (review),
                              lệnh git/test/validator của chính phiên S085 (integration)
NEXT_VERTICAL_ACTION       = PRA-002 Slice C — Budget-Aware Implementation Plan (KHÔNG code-first)
```

**Slice C handoff — chỉ kế hoạch, không code.** Cumulative production logic của
PRA-002 hiện là **1.393 LOC** trên dừng cứng **1.500** → còn đúng **107 LOC**.
Session Slice C KHÔNG được bắt đầu bằng code-first; trước implementation phải có
một **BUDGET-AWARE SLICE C PLAN** xác định: (a) minimum code path cho
`RESULT_REVISED`; (b) phần RDA/production acceptance nào không cần code (checklist
Owner thực hiện thủ công); (c) ước tính LOC production; (d) tận dụng primitives/
repository/schema hiện có, không tạo mới nếu tránh được; (e) không refactor
slice A/B chỉ để lấy budget. Nếu ước tính > 107 LOC, lập đề xuất CHANGE_BUDGET cho
Owner **TRƯỚC** khi viết mã — không viết trước rồi xin sau.

## CANONICAL CURRENT STATE — TASK-PRA-002 (AUTHORITATIVE, 2026-09-02, S084)

Cập nhật sau **Independent Review E2 của slice B**. Khối S083/S082/S081/S080 bên
dưới giữ nguyên như bản ghi lịch sử đúng tại thời điểm của chúng; khi mâu thuẫn về
trạng thái *hiện tại*, khối này đúng.

```text
SESSION                 = S084 — PRA-002 Slice B Independent Review E2
TASK-PRA-002            = IN_PROGRESS  (slice A INTEGRATED; slice B REVIEWED + ACCEPTED, chờ Controlled Integration; slice C PENDING)
REVIEW_RESULT           = PASS
FINAL_ACCEPTANCE        = ACCEPT
INTEGRATION_READY       = YES
REVIEW_BASE_SHA         = 27b9d1c5a578742450099c53f2f82411f07aa9dc  (== origin/claude/extract-upload-repo-gq2ws4 — canonical KHÔNG dịch chuyển)
REVIEW_HEAD_SHA         = 7658c5e5341935c7e3ff4edf31505b8a1d205e85  (== origin/claude/pra-002-slice-b-snapshot-8rbwip)
EXACT_DIFF              = 16 file, +2.254 / −44  (1 commit)
BLOCKING findings       = 0  → repair cycle tiêu thụ trong phiên này = 0 (lineage vẫn 1/2, còn 1)
NON_BLOCKING findings   = FIND-PRA002-B1 (số liệu CHANGE_BUDGET — đã sửa), B2/B3/B4 (DEFER, có re-trigger)
RANGE_SEMANTICS         = ĐÚNG frozen contract (mục 8 bước 4 dùng DETECTED, bước R dùng khoảng ĐÃ XÁC NHẬN).
                          Chỉ thị phiên trước KHÔNG override frozen contract — không sửa để khớp wording.
CONFIRMATION_AUTHORITY  = đúng MỘT cửa ghi CONFIRMED_COMPLETE (SnapshotRepository.confirm_coverage),
                          checkbox mặc định chưa tick, mọi nhánh từ chối fail-closed và không ghi gì
ABSENCE_SET             = bước R dùng snapshot_line membership của CHÍNH snapshot đang xác nhận, KHÔNG dùng last_seen
CURRENT/TOTALS          = current_totals() không đổi một dòng nào trong diff và không tham chiếu bảng cờ;
                          đo trên PostgreSQL 16.13 thật: 262 cờ REMOVED → current + tổng tiền KHÔNG đổi
TRANSACTION             = nâng coverage + bước R trong MỘT engine.begin(); review bổ sung 3 test rollback
                          (ép hỏng từng nửa) — đã mutation-check, chỉ sửa file test
TEST                    = full suite 1784 passed, 11 skipped (sau khi thêm 3 test)
                          Golden 74 passed, 2 skipped (2 skip môi trường, có sẵn ở BASE)
                          PostgreSQL 16.13 THẬT: alembic upgrade head → 0002_snapshots; vertical 113 passed
CHANGE_BUDGET slice B   = 289 dòng logic production (đo lại độc lập; S083 báo 242) / mục tiêu slice ≤ 500 → ĐẠT
CHANGE_BUDGET lineage   = 1.104 (A) + 289 (B) = 1.393 / mục tiêu 1.200 / dừng cứng 1.500
REMAINING_TO_HARD_STOP  = 107 dòng  (KHÔNG phải 154 — xem FIND-PRA002-B1)
CHECK PASS (E1)         = 01, 02, 03, 04, 05, 06, 07, 09, 10, 11, 12, 13, 16  (reviewer tái lập độc lập 06 và 07 ở mức E2)
CHECK NOT_TESTED        = 08 (slice C), 14 (RDA — Owner), 15 (Production — Owner)
CHECK-PRA002-17         = PASS cho phần slice B (còn slice C trước khi đóng toàn task)
TRACKING_CHANGED        = NO
EVIDENCE                = docs/reviews/TASK-PRA-002-SLICE-B-INDEPENDENT-REVIEW-RECORD.md
NEXT_VERTICAL_ACTION    = Controlled Integration slice B vào canonical (KHÔNG bắt đầu slice C)
```

**Điều phiên slice C phải biết trước khi mở việc.** Headroom thật trước dừng cứng
CHANGE_BUDGET là **107 dòng logic production**, không phải 154: con số 242 của S083
bị đo thiếu 47 dòng, và phương pháp đo lại đã được hiệu chuẩn bằng cách đo lại
slice A ra đúng 1.104 như đã chấp nhận. Nếu slice C không nằm gọn trong 107 dòng,
mở đề xuất CHANGE_BUDGET cho Owner **TRƯỚC** khi viết mã.

## CANONICAL CURRENT STATE — TASK-PRA-002 (AUTHORITATIVE, 2026-09-02, S083)

Cập nhật sau phiên implement **slice B**. Các khối S082/S081/S080 bên dưới giữ
nguyên như bản ghi lịch sử đúng tại thời điểm của chúng; khi mâu thuẫn về trạng
thái *hiện tại*, khối này đúng.

```text
SESSION                 = S083 — PRA-002 Slice B Implementation (MAJOR)
TASK-PRA-002            = IN_PROGRESS  (slice A INTEGRATED; slice B IMPLEMENTED, chờ Independent Review E2; slice C PENDING)
SLICE_B_RESULT          = PASS
IMPLEMENTATION_BASE_SHA = 27b9d1c5a578742450099c53f2f82411f07aa9dc  (== origin/claude/extract-upload-repo-gq2ws4 lúc mở phiên — canonical KHÔNG dịch chuyển)
BRANCH                  = claude/pra-002-slice-b-snapshot-8rbwip     (cắt từ đúng SHA trên; chưa integrate)
MIGRATION               = KHÔNG có migration mới — schema 0002_snapshots đã đủ (ALEMBIC_HEAD không đổi; tools/db/** không sửa)
COVERAGE                = DETECTED_ONLY / HEADER_CONSISTENT / CONFIRMED_COMPLETE; CHỈ POST /du-lieu/snapshot/<id>/xac-nhan-du
                          (có tick ô) nâng được mức thứ ba — 2 test tĩnh AST khoá "đúng một cửa"
FAIL-SAFE               = "không thấy" KHÔNG BAO GIỜ thành "đã xoá": NOT_SEEN và REMOVED_CANDIDATE đều
                          giữ nguyên current + tổng + mọi bảng fact (đo trên PostgreSQL 16.13 thật)
RANH GIỚI PHẠM VI       = absence chỉ có nghĩa trong phạm vi snapshot đại diện: xác nhận 01–10 → 0 REMOVED cho đơn 11–31;
                          xác nhận cả tháng → 262 REMOVED, hiện hành vẫn 351 dòng / 3.562.310.000 VND
FIND-PRA002-A4          = ĐÃ SỬA — nhãn trang snapshot theo coverage_state thật, ba nhãn khác nhau đôi một
TEST                    = full suite 1781 passed, 11 skipped (baseline 1711/11 → +70 test, 0 skip thêm)
                          Golden 58 passed, 2 skipped (KHÔNG đổi); PRA-001 focused 81 passed
                          PostgreSQL 16.13 thật: migration + 5 kịch bản slice B PASS
CHANGE_BUDGET slice B   = 242 dòng logic production / mục tiêu ≤ 500 (cảnh báo 600, dừng cứng 800 KHÔNG chạm)
CHANGE_BUDGET lineage   = 1.104 (A) + 242 (B) = 1.346 / mục tiêu 1.200 / dừng cứng 1.500 — VƯỢT mục tiêu mềm,
                          còn 154 dòng trước dừng cứng; slice C phải biết trước khi mở việc
CHECK PASS (E1)         = 01, 02, 03, 04, 05, **06**, **07**, 09, 10, 11, 12, 13, 16
CHECK NOT_TESTED        = 08 (slice C), 14 (RDA — Owner), 15 (Production — Owner), 17 (Independent Review E2 slice B)
REVIEW BUDGET           = 2 cycle, ĐÃ DÙNG 1 (còn 1)
TRACKING_CHANGED        = NO
EVIDENCE                = docs/sessions/S083-pra-002-slice-b-coverage-semantics.md
NEXT_VERTICAL_ACTION    = Independent Review E2 slice B (KHÔNG bắt đầu slice C)
```

**Điểm Reviewer cần soi trước tiên.** (1) Chỉ thị phiên (mục 12) và frozen
contract (mục 8 bước 4) nói khác nhau về việc có dựng `NOT_SEEN` cho các khoá
NGOÀI khoảng đo được của snapshot mới hay không; implementation theo **frozen
contract** (không dựng), đúng thứ tự thẩm quyền mà chính chỉ thị đặt ra và đúng
nguyên tắc "absence chỉ có nghĩa trong phạm vi coverage". (2) Trạng thái "cờ
vắng mặt còn hiệu lực" được DẪN XUẤT bằng so sánh NGẶT trên `created_at`; hai
snapshot cùng một giây → giữ cờ còn hiệu lực (fail-safe). Không con số nghiệp vụ
nào phụ thuộc nhãn này.

## CANONICAL CURRENT STATE — TASK-PRA-002 (AUTHORITATIVE, 2026-09-02, S082)

Cập nhật sau **Controlled Integration của slice A vào canonical**. Khối S081
ngay dưới giữ nguyên như bản ghi lịch sử đúng tại thời điểm Independent
Review; khi hai khối mâu thuẫn về trạng thái *hiện tại*, khối này đúng.

```text
SESSION                 = S082 — PRA-002 Slice A Controlled Integration (MAJOR)
TASK-PRA-002            = IN_PROGRESS  (slice A IMPLEMENTED + REVIEWED + ACCEPTED + INTEGRATED; slice B NEXT; slice C PENDING)
CANONICAL_BEFORE_SHA    = 7fad3f76908d6d56114a5e2e947d83e15f8eda02
ACCEPTED_SLICE_A_SHA    = 86f26a0e15b9655d3b0384b59c221f68bc3a1665  (== exact remote HEAD của claude/pra-002-slice-a-umygjq lúc integrate)
CANONICAL_AFTER_SHA     = 86f26a0e15b9655d3b0384b59c221f68bc3a1665
INTEGRATION_METHOD      = fast-forward (không merge commit, không squash, không rebase, không cherry-pick)
LINEAGE                 = 7fad3f7 (canonical before) → 80c6fe1 (slice A implementation) → b0ecab7 (review repair cycle 1) → 86f26a0 (ledger head_sha) — cả ba đều là ancestor của canonical sau integrate
REMOTE_CANONICAL_SHA    = 86f26a0e15b9655d3b0384b59c221f68bc3a1665  (khớp local — xác minh sau push)
TREE_EQUIVALENCE        = ĐÚNG (fast-forward: tree canonical sau integrate == tree accepted head, không có thay đổi nào phát sinh trong integration)
TESTS_AFTER_INTEGRATION = focused Slice A (test_history_keys/reconciler/db, test_snapshot_repository, test_web_history, test_pipeline_history_vertical): 116 passed
                          (full suite/Golden/PostgreSQL không chạy lại vì tree không đổi so với accepted head đã E2-verify)
VALIDATORS              = validate_structure PASS; validate_project_state PASS; validate_evidence PASS;
                          validate_reference_integrity FAIL — 3 lỗi pre-existing trong TASK-REM-T06, ngoài scope integration, DEFER
BRANCH_AUTHORITY        = AUTHORITY_OK (branch_authority_check.sh)
CHECK-PRA002-17         = NOT_TESTED ở cấp toàn task (frozen gate đòi CHECK-07 slice B); phần slice A đã PASS E2, xem
                          docs/reviews/TASK-PRA-002-SLICE-A-INDEPENDENT-REVIEW-RECORD.md
EVIDENCE                = commit fast-forward trên claude/extract-upload-repo-gq2ws4 (86f26a0), branch_authority_check log, test log phiên này
NEXT_VERTICAL_ACTION    = PRA-002 Slice B — Coverage Semantics
```

## CANONICAL CURRENT STATE — TASK-PRA-002 (AUTHORITATIVE, 2026-09-02, S081)

Cập nhật sau **Independent Review E2 của slice A**. Khối S080 ngay dưới giữ
nguyên như bản ghi lịch sử đúng tại thời điểm implement; khi hai khối mâu
thuẫn về trạng thái *hiện tại*, khối này đúng.

```text
SESSION                 = S081 — PRA-002 Slice A Independent Review (MAJOR)
TASK-PRA-002            = IN_PROGRESS  (slice A REVIEWED + REPAIRED; slice B, C chưa bắt đầu)
REVIEW_BASE_SHA         = 7fad3f76908d6d56114a5e2e947d83e15f8eda02  (canonical, chưa dịch chuyển)
REVIEW_HEAD_SHA         = 80c6fe1d1c98497d821a8802fdbc9a1ca6a48b60
BRANCH                  = claude/pra-002-slice-a-umygjq  (chưa integrate)
REVIEW_RESULT           = E2 PASS sau 1 repair cycle
FINAL_ACCEPTANCE        = ACCEPT
INTEGRATION_READY       = YES
BLOCKING FINDING        = FIND-PRA002-A1 — ĐÃ SỬA trong chính phiên review
NON_BLOCKING FINDING    = FIND-PRA002-A2 (present_lines tính hai lần, DEFER slice C),
                          FIND-PRA002-A3 (detected_date_* nullable, DEFER),
                          FIND-PRA002-A4 (câu "CHƯA XÁC NHẬN ĐỦ" cố định, slice B)
TEST                    = full suite 1711 passed, 11 skipped; Golden 58 passed, 2 skipped
                          PostgreSQL 16.13 thật: migration up/down + vertical PASS
CHANGE_BUDGET DÙNG      = 1.104 / 1.200 dòng logic production (dừng cứng 1.500 không chạm)
CHECK PASS (E2)         = 01, 02, 03, 04, 05, 09, 10, 11, 12, 13; 16 (E1, RECOMMENDED)
CHECK PARTIAL           = 06 (xác nhận tường minh = slice B)
CHECK NOT_TESTED        = 07 (slice B), 08 (slice C), 14 (RDA — Owner), 15 (Production — Owner)
CHECK-PRA002-17         = PARTIAL — phần slice A đã review E2 và PASS; CHECK-07
                          (slice B) chưa chạy được nên check toàn task chưa đóng
REVIEW BUDGET           = 2 cycle, ĐÃ DÙNG 1
TRACKING_CHANGED        = NO
EVIDENCE                = docs/reviews/TASK-PRA-002-SLICE-A-INDEPENDENT-REVIEW-RECORD.md
NEXT_VERTICAL_ACTION    = Controlled Integration slice A vào canonical claude/extract-upload-repo-gq2ws4
```

**Điều review chứng minh thêm mà implement chưa bắt được:** sau một
`ORDER_KEY_COLLISION`, lần upload TIẾP THEO trên cùng Số BH vi phạm UNIQUE
`(khoá, version_no)` và làm `/run` trả HTTP 500 vĩnh viễn — vì version mới
được đánh số theo version hiện hành thay vì theo max đã ghi (trái mục 5.3).
Tái hiện trên cả SQLite và PostgreSQL 16.13; đã sửa và đã có test chặn
(`test_uploading_again_after_a_collision_still_works`).

## CANONICAL CURRENT STATE — TASK-PRA-002 (AUTHORITATIVE, 2026-09-02, S080)

Cập nhật sau phiên implement **slice A**. Khối S079 ngay dưới giữ nguyên như
bản ghi lịch sử đúng tại thời điểm freeze contract; khi hai khối mâu thuẫn về
trạng thái *hiện tại*, khối này đúng.

```text
SESSION                 = S080 — PRA-002 Slice A Implementation (MAJOR)
TASK-PRA-002            = IN_PROGRESS  (slice A IMPLEMENTED; slice B, C chưa bắt đầu)
PRA002_IMPLEMENTATION_STARTED = YES
SLICE_A_RESULT          = PASS  (vertical chạy end-to-end, chờ Independent Review E2)
IMPLEMENTATION_BASE_SHA = 7fad3f76908d6d56114a5e2e947d83e15f8eda02
BRANCH                  = claude/pra-002-slice-a-umygjq  (cắt từ đúng SHA trên, chưa integrate)
MIGRATION               = 0002_snapshots (head mới; additive, 4 bảng legacy KHÔNG đổi)
TEST                    = full suite 1710 passed, 11 skipped  (baseline 1608/11 — +102 test, 0 skip mới)
                          Golden 58 passed, 2 skipped — KHÔNG đổi
CHANGE_BUDGET DÙNG      = 1.080 / 1.200 dòng logic production (dừng cứng 1.500 không chạm)
CHECK PASS              = 01, 02, 03, 04, 05, 09, 10, 11, 12, 13, 16(RECOMMENDED)
CHECK PARTIAL           = 06 (DETECTED/HEADER xong; xác nhận tường minh = slice B)
CHECK NOT_TESTED        = 07 (slice B), 08 (slice C), 14 (RDA — thiếu workbook thật),
                          15 (Production Acceptance — Owner), 17 (Independent Review E2)
REVIEW BUDGET           = 2 cycle, ĐÃ DÙNG 0
PROTECTED_CORE_IMPACT   = alias exporter (3 dòng) + 2 trường DemoRun — không đổi hành vi, XLSX không đổi
TRACKING_CHANGED        = NO
EVIDENCE                = docs/sessions/S080-pra-002-slice-a-implementation.md
```

**Đã chứng minh trong slice A (E1, bằng chứng nguyên văn ở handoff S080):**

- Một upload golden `period_2026_01.xlsx` → snapshot 351 dòng / 254 đơn,
  `SUM(current total_sales) = 3.562.310.000` = `sales_normalized` của Golden.
- Upload lại đúng file → 351 `SAME`, **0 version nguồn mới**, tổng hiện hành
  không đổi tới từng đồng (no-double-count).
- A (≤10/01: 89 dòng/61 đơn) rồi B (351/254) → **đẳng thức**
  `state(A,B) == state(B trên DB sạch)` trên cả tập khoá lẫn tập
  `(khoá, line_fingerprint)`; đảo thứ tự không đổi tổng.
- Sửa đúng một dòng → 1 `SOURCE_CHANGED`, version cũ đọc lại nguyên văn,
  `changed_fields` nêu đúng `sell_price` + `total_sales_raw`, tổng đổi đúng
  delta.
- Cùng BH lệch > 90 ngày → `ORDER_KEY_COLLISION`: ghi đủ, dựng cờ, **không**
  ghi đè hiện trạng, **không** merge, **không** mất bản ghi.
- Kịch bản A→A→B→B' chạy lại trên **PostgreSQL 16 thật**; migration
  `0001_legacy → 0002_snapshots` giữ nguyên dòng legacy đã có.
- `ru_maxrss` end-to-end `/run` = **75,6 MB** (mục tiêu < 300 MB).

**NEXT_VERTICAL_ACTION:** Independent Review E2 cho slice A trước Controlled
Integration (`docs/reviews/TASK-PRA-002-INDEPENDENT-REVIEW-RECORD` theo
`governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`). KHÔNG bắt đầu
slice B trước khi review xong.


## CANONICAL CURRENT STATE — TASK-PRA-002 (bản ghi lịch sử, 2026-09-02, S079)

Đây là chỉ dẫn trạng thái hiện hành có thẩm quyền cho `TASK-PRA-002`. Các
khối bên dưới (S078R, S078, PRA-001, S073…) giữ nguyên như **bản ghi lịch
sử đúng tại thời điểm của chúng**; khi một khối lịch sử mâu thuẫn với mục
này về trạng thái *hiện tại*, mục này đúng.

```text
SESSION                 = S079 — Roadmap Finalization / Freeze Contract (SPIKE, không code)
TASK-PRA-002            = READY   (Completion Gate FROZEN — 17 check, 16 REQUIRED, Risk 4 → E1, E2 review)
PRA002_READY_FOR_IMPLEMENTATION = YES
OWNER_DECISION_REQUIRED = NONE (blocking)  — mọi UNKNOWN có fail-safe + re-trigger (task file mục 18)
BASE_SHA                = 553d8a36f578b082128a6e45d2748da2bc371e70  (HEAD canonical lúc freeze)
Baseline                = Golden 58 passed, 2 skipped · full suite 1608 passed, 11 skipped
TASK FILE               = docs/tasks/TASK-PRA-002-pipeline-persistence-reconciliation.md
DEC                     = DEC-171 (quyết định chiến thuật S079; Owner Decision nền = DEC-166/167/170)
REVIEW BUDGET           = HIGH = 2 blocking repair cycles (ledger "Root Task: TASK-PRA-002", 0 dùng)
CHANGE BUDGET           = ≤ 1.200 dòng logic (dừng cứng 1.500)
IMPLEMENTATION SLICES   = A (persistence + INSERT/SAME/SOURCE_CHANGED/COLLISION + result + current)
                          → B (coverage xác nhận + NOT_SEEN/REMOVED_CANDIDATE)
                          → C (RESULT_REVISED + Real Data Acceptance + PostgreSQL thật)
PRA002_IMPLEMENTATION_STARTED = NO
PROTECTED_CORE_IMPACT   = NONE (phiên này); implementation chỉ alias exporter + 2 trường DemoRun
TRACKING_CHANGED        = NO
```

**Contract đã freeze (tóm tắt — chi tiết ở task file):**

- Vertical: upload sổ kế toán chồng kỳ → pipeline hiện có (không đổi) →
  `PIPELINE_GENERATED` vào PostgreSQL (6 bảng, migration `0002_snapshots`)
  → reconcile theo `ORDER_LINE_KEY = (order_id engine, product_key,
  occurrence_index)` + `line_fingerprint` → current một khoá một dòng →
  tổng theo kỳ không đếm trùng (oracle đẳng thức `state(A,B) == state(B)`).
- INSERT / SAME / SOURCE_CHANGED (version n+1, `changed_fields`, giữ cũ,
  mới = current) / NOT_SEEN (chưa xác nhận) / REMOVED_CANDIDATE (chỉ khi
  `CONFIRMED_COMPLETE`, vẫn current, vẫn tính, không xoá) / RESULT_REVISED
  (trục kết quả riêng, 3 trường). `ORDER_KEY_COLLISION` (cùng BH lệch > 90
  ngày) là fail-safe cho UNKNOWN BH reset.
- Coverage: `DETECTED_ONLY` / `HEADER_CONSISTENT` / `CONFIRMED_COMPLETE` —
  chỉ `POST /du-lieu/snapshot/<id>/xac-nhan-du` (khai báo khoảng + checkbox,
  validate `DETECTED ⊆ khoảng`) nâng lên CONFIRMED. Không UI PRA-004.
- Không PII trong bảng PRA-002. Không `DELETE`/`UPDATE` fact. Một
  transaction bao cả ghi R2; lỗi → 500, không run COMPLETE.

**FACT mới đo được ở S079:** ô A2 của fixture golden là
`"Nhân viên: Tín Phát 0869931931, Tháng 1 năm 2026"`, khác dạng
`"Từ ngày … đến ngày …"` của file production (`docs/analysis/01_DATA_MAPPING.md`)
→ header parser chỉ nhận đúng hai dạng này, còn lại `DETECTED_ONLY`.
Fixture golden 01: 351 dòng/254 đơn, 0 cặp `(đơn, sản phẩm)` lặp, dòng ≤
10/01 = 89 (61 đơn) → fixture hai snapshot cắt từ golden có sẵn số kỳ vọng.

**Việc còn treo bên ngoài PRA-002 (cập nhật S079 close-out):** Owner ĐÃ
deploy canonical và ĐÃ import workbook legacy thật thành công trên
production — xem khối "PRODUCTION STATE RECONCILIATION" ngay dưới. Còn treo
duy nhất: Phase D bảo mật (`0.0.0.0/0` trong allowed IP list của
`tinphat-reports-db`) — không chặn PRA-002. Production Acceptance của
PRA-002 (`CHECK-PRA002-15`) vẫn cần một lần deploy RIÊNG cho SHA mang
migration `0002_snapshots`, sau khi implement xong.

**NEXT_VERTICAL_ACTION (tại thời điểm S079):** mở session implement
`TASK-PRA-002` slice A theo handoff
`docs/sessions/S079-pra-002-roadmap-finalization.md` → "IMPLEMENTATION
HANDOFF". *(Đã thực hiện ở S080 — xem khối CANONICAL CURRENT STATE S080 ở
đầu file.)*


## PRODUCTION STATE RECONCILIATION — S079 CLOSE-OUT (2026-09-02, HIỆN HÀNH)

Khối này là **trạng thái production hiện hành có thẩm quyền**. Nó thay thế
mọi mô tả cũ nói rằng "production chờ Owner deploy" (khối
"PRODUCTION POSTGRESQL ACTIVATION — S078" và ghi chú `EXACT_DEPLOY_SHA`
trong khối S078R bên dưới giữ nguyên như **bản ghi lịch sử đúng tại thời
điểm của chúng**, không bị viết lại).

Đây là **state reconciliation**, KHÔNG phải một repair mới của S078/S078R
và KHÔNG mở task mới.

```text
PRODUCTION_DEPLOYED_SHA     = canonical (S078R) — Owner đã deploy
LEGACY_IMPORT_PRODUCTION    = PASS   — workbook legacy THẬT import thành công
OOM_ON_IMPORT               = KHÔNG CÒN (repair S078R có hiệu lực trên production)
LEGACY_PERSIST_AND_READ     = PASS   — dữ liệu LEGACY đã persist và đọc lại được trên web
LEGACY_MULTI_PERIOD_QUERY   = PASS   — tab Nhân viên query được nhiều kỳ legacy
PHASE_C_PRODUCTION          = ĐÃ ĐÓNG bằng quan sát production của Owner
                              (thay thế "CHỜ OWNER DEPLOY" của khối S078)
COMPUTE_TARGET              = Render 512 MB — Owner quyết định KHÔNG nâng 2 GB
PAID_COMPUTE_UPGRADE        = KHÔNG MỞ TASK
PHASE_D_SECURITY            = OPEN / PENDING — nếu `0.0.0.0/0` còn trong allowed
                              IP list của `tinphat-reports-db` thì database vẫn
                              phơi inbound public (chỉ mật khẩu chắn).
                              Thao tác: `docs/deployment/S071_DEPLOYMENT.md` bước 13.
                              KHÔNG được ghi Phase D = DONE khi chưa có bằng chứng.
```

**Nguồn và giới hạn của bằng chứng (không được đọc rộng hơn).** Các dòng
`PASS` ở trên là **quan sát trực tiếp của Owner trên production**, do Owner
báo lại tại phiên close-out S079. Session KHÔNG tự đo được: egress tới
`api.render.com` và `reports.tinphatcrm.com` bị chặn `403` (đã ghi ở S078).
Vì vậy:

- `Evidence Level = E1`, `Executed By = Owner (production)` — một lần chạy
  thật, không phải tường thuật của agent;
- repo KHÔNG lưu output nguyên văn (số dòng import, log Render, ảnh chụp);
  không con số nào ở đây được suy ra hay bịa thêm;
- `CHECK-PRA001-09` trong `docs/tasks/TASK-PRA-001-legacy-reference-vertical.md`
  GIỮ NGUYÊN evidence đã freeze (PostgreSQL 16.13 local). Quan sát production
  này **củng cố** nó chứ không thay evidence đã ghi, và không sửa gate frozen.

**Hệ quả cho PRA-002:** dependency hạ tầng của `TASK-PRA-002` đã thoả trên
thực tế (production chạy đúng canonical, history store PostgreSQL hoạt động
đầu-cuối với dữ liệu thật). `CHECK-PRA002-15` (Production Acceptance) vẫn
là gate riêng, cần một lần deploy SHA có migration `0002_snapshots` SAU khi
implement — không phải lần deploy này.

## S078R — LEGACY IMPORT OOM REPAIR (2026-09-02, HIỆN HÀNH)

```text
RESULT                  = PASS
SỰ CỐ                   = Render kill container ("used over 512MB") khi
                          Owner import workbook Legacy ~3 MB trên c0fc2f7
ROOT CAUSE              = app/legacy/parser.py mở workbook 2 lần ở chế độ
                          read_only=False → openpyxl dựng cây Cell cho MỌI
                          sheet, kể cả hàng chục sheet sổ bán hàng thô mà
                          import legacy không đọc dòng nào
PEAK RSS BEFORE         = 379.6 MB (parse đơn lẻ) / 474.2 MB (end-to-end,
                          một gunicorn worker; Dockerfile chạy 2 worker)
PEAK RSS AFTER          =  32.0 MB (parse đơn lẻ) /  81.9 MB (end-to-end)
BUSINESS_FIDELITY       = KHÔNG ĐỔI — output parser cũ/mới IDENTICAL
                          (diff JSON 767 dòng, 0 khác biệt, 2 workbook)
NEW_INFRASTRUCTURE      = NONE (không worker/queue/Redis/service/DB mới)
PAID_COMPUTE            = NONE (giữ 512 MB, không nâng plan)
CHANGED FILES           = app/legacy/parser.py (1 file code)
PRA002_STARTED          = NO
TRACKING_CHANGED        = NO
PROTECTED_CORE_IMPACT   = NONE
```

Điểm cốt lõi: sau repair, peak RAM **không còn phụ thuộc kích thước sổ bán
hàng trong workbook**. Workbook 7.79 MB tốn đúng bằng workbook 3.15 MB
(31.8 vs 32.0 MB) vì sheet không được đọc thì XML của nó không bao giờ được
phân tích. Đây là sửa cấu trúc, không phải chỉnh tham số — nên không cần
theo dõi lại mỗi khi workbook của Owner lớn thêm.

Bằng chứng đầy đủ, giới hạn của bằng chứng, và finding DEFER:
`docs/sessions/S078R-legacy-import-memory-repair.md`.

**SHA cần deploy đã đổi.** `c0fc2f7` là bản BỊ OOM — không deploy lại nó.
`EXACT_DEPLOY_SHA` mới = HEAD hiện tại của
`claude/extract-upload-repo-gq2ws4` (`git rev-parse
origin/claude/extract-upload-repo-gq2ws4`). Biến `HISTORY_DATABASE_URL` +
scheme `postgresql+psycopg://` Owner đã cấu hình xong từ trước, không phải
làm lại.

> **Cập nhật S079 close-out (2026-09-02):** thao tác deploy này **đã được
> Owner thực hiện**. Production chạy bản có repair S078R; import workbook
> legacy thật không còn OOM ở 512 MB. Xem khối "PRODUCTION STATE
> RECONCILIATION — S079 CLOSE-OUT" phía trên.


## PRODUCTION POSTGRESQL ACTIVATION — BẢN GHI S078 (2026-09-02)

> **BỊ THAY THẾ MỘT PHẦN (S079 close-out, 2026-09-02).** Dòng
> `PHASE_C_PRODUCTION = CHỜ OWNER DEPLOY` và `production after SHA = CHƯA
> ĐỔI` trong khối này đúng tại thời điểm S078 và được giữ nguyên làm bản
> ghi lịch sử. Trạng thái production HIỆN HÀNH nằm ở khối
> "PRODUCTION STATE RECONCILIATION — S079 CLOSE-OUT" phía trên: Owner đã
> deploy, legacy import thật đã chạy thành công, Phase C đóng; chỉ Phase D
> (`0.0.0.0/0`) còn OPEN/PENDING.

Cập nhật 2026-09-02 sau Independent Review (`ACCEPT`, 0 blocking finding)
và Owner Decision: `DEC-170 = OWNER_ACCEPTED`, S078 đã Controlled
Integration vào nhánh canonical. Khối này là trạng thái HIỆN HÀNH có thẩm
quyền; `docs/sessions/S078-postgres-production-activation.md` giữ nguyên
làm bản ghi lịch sử đúng tại thời điểm của nó.

```text
RESULT                  = PASS  (đã tích hợp; chờ đúng một thao tác deploy)
PHASE_A_LINEAGE         = PASS  (production stale, KHÔNG divergent)
PHASE_B_COMPATIBILITY   = PASS  (code) / RESOLVED (cấu hình Render — Owner
                          đã đặt HISTORY_DATABASE_URL + postgresql+psycopg://)
PHASE_C_PRODUCTION      = CHỜ OWNER DEPLOY — session không có egress (403)
PHASE_D_SECURITY        = ĐÃ VIẾT THÀNH BƯỚC, chờ Phase C
CHECK-PRA001-09         = PASS trên PostgreSQL 16.13 thật (KHÔNG phải
                          Render PostgreSQL 18 production)
DEC-170                 = OWNER_ACCEPTED
INDEPENDENT_REVIEW      = ACCEPT (BLOCKING_FINDINGS = 0)
PRA002_STARTED          = NO
TRACKING_CHANGED        = NO
PROTECTED_CORE_IMPACT   = NONE

canonical branch        = claude/extract-upload-repo-gq2ws4
CANONICAL_BEFORE_SHA    = 90f85a7edfd6acc497db1d18304baef87ab62d99
ACCEPTED_SHA (S078)     = c5e19949df81a5ee456bc1b7735b8eb5a814735e
CANONICAL_AFTER_SHA     = HEAD hiện tại của claude/extract-upload-repo-gq2ws4
                          sau Controlled Integration S078. Kiểm chứng:
                          `git rev-parse origin/claude/extract-upload-repo-gq2ws4`
production before SHA   = 596564b  (ancestor THẲNG của canonical — kiểm
                          chứng khoảng cách: `git rev-list --count
                          596564b..origin/claude/extract-upload-repo-gq2ws4`)
production after SHA    = CHƯA ĐỔI — cần Owner deploy CANONICAL_AFTER_SHA
```

**Canonical contract (Owner accepted, không được nới lỏng):** biến môi
trường là `HISTORY_DATABASE_URL`, scheme `postgresql+psycopg://`. **Không
có fallback sang `DATABASE_URL`** — xem `DEC-170`.

Vì sao production hiện tại chưa chứng minh gì về PostgreSQL: service đang
chạy `596564b`, commit đó có TRƯỚC toàn bộ history store nên không đọc
`HISTORY_DATABASE_URL` và cũng không có `REPORTS_REQUIRE_HISTORY_DB=1`.
Chỉ sau khi deploy `CANONICAL_AFTER_SHA` thì fail-closed mới có hiệu lực
và `alembic upgrade head` mới chạy trên PostgreSQL 18 production.

Thao tác còn lại của Owner (chi tiết + cách đọc log lỗi ở
`docs/sessions/S078-postgres-production-activation.md`; quy trình đầy đủ ở
`docs/deployment/S071_DEPLOYMENT.md` bước 8–13):

1. ✅ ĐÃ XONG — biến Render `HISTORY_DATABASE_URL` với scheme
   `postgresql+psycopg://` (Owner xác nhận; session KHÔNG nhận giá trị).
2. ▶️ Manual Deploy **`CANONICAL_AFTER_SHA`** trên nhánh
   `claude/extract-upload-repo-gq2ws4` (fast-forward từ `596564b` — không
   force push, không sửa lịch sử, không dùng `main`). Đây là SHA DUY NHẤT
   được deploy.
3. ⏳ Kiểm tra `/du-lieu` → tab **Nhân viên** hiện số cũ kèm nhãn `LEGACY`.
   Xanh rồi mới xoá `0.0.0.0/0` khỏi allowed IP list của database
   (Phase D, bước 13).


## CANONICAL CURRENT STATE — TASK-PRA-001 (AUTHORITATIVE, 2026-09-02, S077)

Đây là chỉ dẫn trạng thái hiện hành có thẩm quyền cho `TASK-PRA-001`. Mọi
khối session bên dưới (S073, S074, S075, S076) được giữ nguyên như **bản ghi
lịch sử đúng tại thời điểm của chúng** — đặc biệt S076 ghi
`CHECK-PRA001-01 = NOT_TESTED` và `TASK-PRA-001 = IMPLEMENTED`, đó là trạng
thái đúng của S076 và KHÔNG bị viết lại. Khi một khối lịch sử mâu thuẫn với
mục này về trạng thái *hiện tại*, mục này đúng.

```text
TASK-PRA-001            = DONE
CODE_ACCEPTANCE         = PASS
REAL_DATA_ACCEPTANCE    = PASS
CHECK-PRA001-01         = PASS   (file Excel THẬT, không còn NOT_TESTED)
CHECK-PRA001-09         = PASS   (S078 — PostgreSQL 16.13 THẬT; xem
                                   "PRODUCTION POSTGRESQL ACTIVATION" bên dưới)
FINAL_DELTA_REVIEW      = PASS
DEC169_REVIEW           = FAITHFUL
REQUIRED_GATES          = 9/9 PASS  (CHECK-PRA001-01…08 + -10)
BLOCKING_FINDINGS       = NONE
REPAIR_CYCLES_REMAINING = 0
EXACT_ACCEPTED_SHA      = 3faedfdebc1f14d8a27e89955d9cfa64d6a462cd
SOURCE_BRANCH           = claude/reports-pipeline-architecture-gj8bji
```

### Phạm vi import production đã chốt (DEC-169)

```text
Summary 2025    = REFERENCE_ONLY   (không import / persist / query / display)
Summary 2026    = REQUIRED_IMPORT
DataChart 2026  = REQUIRED_IMPORT
```

`Summary 2025` là sheet đã dán cứng (0 ô công thức, 99 dòng value-only trên
workbook thật). Importer raise `LegacyImportError` thay vì đoán `row_kind` —
đúng theo guard DEC-168 / FIND-PRA001-R01. Owner bác bỏ giả định "phải
production-import Summary 2025"; đây là `OWNER_SCOPE_CLARIFICATION`, KHÔNG
phải repair cycle 2, và repair budget PRA-001 vẫn `0 used sau cycle 1 /
0 remaining` (xem `PROJECT/PROJECT_DECISIONS.md` DEC-169).

**Không được đọc mục này thành "toàn bộ workbook lịch sử đã được import".**
Chỉ dữ liệu 2026 cần thiết được đưa vào production store.

### Real Data Acceptance — bằng chứng (E1, workbook thật)

Workbook Owner cung cấp trong Claude Cloud (KHÔNG commit vào repo, KHÔNG bị
sửa — SHA256 trước/sau giống hệt): `Báo cáo Kinh doanh 2026.xlsx`, SHA256
`4ffe51983306a16f507d3fe5fad6b0f2acf9bfe8b0486f30c83cb64398d11f72`.

```text
sheets_imported = ['Summary 2026', 'DataChart 2026']
summary_rows    = 71     daily_sales = 174     monthly_reference = 12
import_id       = LEG-20260902-4ffe5198

SUMMARY_SOURCE_ROWS_WITH_VALUES  = 71
SUMMARY_IMPORTED_ROWS            = 71
SUMMARY_UNACCOUNTED_ROWS         = 0
SUMMARY_REFERENCE_ONLY_PERSISTED = 0
matched=1508 mismatched=0
exit=0
```

Fidelity ở đây gồm **HAI** phần và phải được đọc như vậy: `VALUE MATCH`
(`mismatched=0`) **và** `SOURCE COVERAGE`
(`SUMMARY_SOURCE_ROWS_WITH_VALUES == SUMMARY_IMPORTED_ROWS`). Con số
`matched=N mismatched=0` đứng MỘT MÌNH không còn được chấp nhận làm bằng
chứng completeness kể từ FIND-PRA001-R01.

### Vòng review — bản ghi durable

| Vòng | SHA được review | Kết quả |
|---|---|---|
| Independent Review #1 | `7d84072765288b7a9dc28679a09325fce7860b48` | `CHANGES_REQUIRED` — 2 blocking (`FIND-PRA001-R01`, `FIND-PRA001-R02`) |
| Repair Re-review (cycle 1/1) | `5bea87ad` (repair của S076) | `PASS` — cả hai finding đã đóng |
| Final Independent Delta Review | `3faedfdebc1f14d8a27e89955d9cfa64d6a462cd` | `PASS` — `DEC169_REVIEW = FAITHFUL`, 0 blocking |

Bản ghi đầy đủ: `docs/reviews/TASK-PRA-001-INDEPENDENT-REVIEW-RECORD.md`.

### Controlled Integration — ĐÃ THỰC HIỆN (2026-09-02, S077)

```text
CANONICAL_BRANCH         = claude/extract-upload-repo-gq2ws4
CANONICAL_BEFORE_SHA     = 596564bf5e7c3f088f60fe173cc83f5faa7f1ace
CANONICAL_AFTER_SHA      = a4f5fd68195b9097811a23ac8767bc9af3952d71
phương pháp              = git merge --no-ff x2 qua nhánh trung gian
                           integration/pra-001-legacy-reference-vertical;
                           KHÔNG squash / rebase / cherry-pick / force push
conflict                 = 0
ACCEPTED_SHA_IS_ANCESTOR = YES (3faedfde)
CLOSEOUT_SHA_IS_ANCESTOR = YES (741be69)
REMOTE_CANONICAL_VERIFIED = YES
```

Post-integration trên canonical: 4/5 validator PASS,
`validate_reference_integrity` FAIL với ĐÚNG 3 issue pre-existing của
REM-T06 (0 finding mới); full suite `1608 passed, 11 skipped`; Golden
`58 passed, 2 skipped`; PRA-001 focused `114 passed`; `git diff --check`
sạch. `branch_authority_check.sh` = `AUTHORITY_OK`, `DIVERGENCE =
WITHIN_LIMITS` — điều kiện `INTEGRATION_DECISION_REQUIRED [loc>5000]`
(V4.1 §8) đã ĐÓNG bằng chính integration này.

### Ranh giới đã giữ

```text
PROTECTED_CORE_IMPACT = NONE
TRACKING_CHANGED      = NO
PRA002_STARTED        = NO   (PRA-002 chỉ là NEXT, chưa mở)
PRA002_PREBUILD       = NONE (không prebuild schema snapshot/version)
POSTGRESQL_PROVISIONED = NO  — gate infra riêng, SAU integration
```

PostgreSQL production provisioning là **NEXT INFRA GATE** tách biệt
(`docs/deployment/S071_DEPLOYMENT.md` bước 8–12), không thuộc PRA-001 DONE.

## CANONICAL CURRENT DELIVERY STATUS — AUTHORITATIVE (2026-09-01)

Đây là chỉ dẫn trạng thái hiện hành có thẩm quyền cho bản giao canonical sau
phiên đối chiếu/tích hợp. Các khối tiến độ, trạng thái task, và evidence theo
từng session ở bên dưới được giữ nguyên như lịch sử; một trạng thái cũ chỉ là
trạng thái lịch sử trừ khi chỉ dẫn hiện hành này tham chiếu lại nó.

### DONE

- Core production pipeline của Reports.
- Đường authority Public Purchase của Tracking.
- Contract Tracking → Reports.
- Reports History Reader.
- Production price composition.
- Pending / Review Queue an toàn.
- Golden validations.
- Real batch validation.
- Demo V1: thin CLI, XLSX Summary / Order Lines / Review Queue.
- Owner Usability V1: native macOS picker và luồng double-click
  `Open Reports.command` đi vào production path của Demo V1.
- S068 identity authority vertical (nhánh `s068/inv-map-vertical`, checkpoint
  `f8d3ffc3c2071a33f2818664713c62da9cfe176f`): `inv.map` của Tracking được
  consume làm authority THỨ HAI, cùng cấp `alias.map`/`board` — xem chi tiết
  dưới CURRENT.
- S069 Beta Operator UI + Feedback (nhánh `s069/beta-operator-ui`, baseline
  `3f92c953b4c6d12834d4d3a0c611a7b27e7e0061`, implementation SHA
  `938a2a8e8b07632eacd2f633d7880e8b13e2bcb3`): Owner launcher nối thêm
  `tracking_inv_map` (gap chưa từng nối trước S069 — launcher V1 ra
  `AUTO=0` thay vì `22` đã accepted), Review summary + severity hiển thị
  đúng authoritative, feedback + telemetry local (`data/beta_feedback/`,
  git-ignored). **Independent Review (phiên #2, 2026-09-01) PASS** sau 3
  repair truthfulness nhỏ, cục bộ, presentation-only (nhãn "Lỗi" →
  "Ưu tiên xem ngay", nhãn readiness "Sẵn sàng" → "Có capture hợp lệ trên
  máy", header Review reasons ghi rõ đếm theo dòng) — real cohort rerun độc
  lập khớp tuyệt đối `58/83/22/36/100%/0 dropped/3 ERRORS`, regression độc
  lập `1373 passed, 11 skipped`, GUI chạy thật xác nhận trên đúng SHA qua
  telemetry + `lsof` (Excel mở đúng file report vừa tạo). Xem chi tiết đầy
  đủ và finding mới `inv.map` staleness (DEFERRED, không phải regression)
  tại `docs/sessions/S069-beta-operator-ui-feedback.md` →
  "Independent Review".
- S070 — Web Beta V1 / Thin Web Delivery Layer (nhánh `s070/web-beta-v1`,
  Independent Review PASS sau 1 repair, **ĐÃ merge canonical qua
  `8d1f87902fea840b034227ae460bb0fa3a42d52b`** — xác nhận bằng
  `git merge-base --is-ancestor`): Owner có thêm một cửa vào web
  (`127.0.0.1:8765`, double-click `Open Reports Web.command`) chạy đúng
  engine đã accepted, không tính lại business rule. Cửa sổ Tkinter
  (`Open Reports.command`) giữ nguyên, không đổi — dùng như tham chiếu/
  fallback. Chi tiết đầy đủ dưới CURRENT.

### CURRENT

- **S071B — Render deployment thật đầu tiên + 2 packaging repair (nhánh
  `s071b/stateless-r2`, cùng ngày 2026-09-01, SAU khi Owner deploy blueprint
  S071B lên Render).** Render build/deploy thật lần đầu (SHA `9fed597`)
  phát hiện HAI blocker packaging pre-existing (không phải bug S071B tự
  sinh ra, nhưng chỉ bị lộ ra khi build Docker thật lần đầu):
  1. `pip install ".[web-prod]"` FAIL — setuptools "Multiple top-level
     packages discovered: ['app', 'config']" (chưa từng khai báo packages
     tường minh trong `pyproject.toml`). Sửa: `tools/__init__.py` (mới) +
     `[tool.setuptools.packages.find] include = ["app*", "tools*"]`. SHA
     `9fed597dc5f6307bd3102c4683f62dbeccb675f2`.
  2. Sau khi build PASS, chạy workbook thật đã accepted ở S068 qua
     production cho **0 AUTO order** thay vì **22 AUTO order** baseline —
     điều tra xác nhận KHÔNG PHẢI business rule/identity/PP thay đổi
     (identity unresolved 31, PP pending 13, accounting coverage 100% đều
     khớp tuyệt đối baseline) mà do `Dockerfile` không `COPY data ./data`:
     `app/composition.py::run_import_production()` nạp KHÔNG ĐIỀU KIỆN
     `data/confirmed_adjustments/confirmed_adjustments.jsonl` (một nguồn
     "canonical committed"), file này vắng mặt trong container (khác "tồn
     tại nhưng rỗng" ở checkout local) → `ConfirmedAdjustmentSource`
     UNAVAILABLE (fail-closed đúng thiết kế DEC-144 §3) cho **mọi dòng**
     (không chỉ dòng vốn đã Pending vì thiếu giá) → mọi order mất
     `eligible_kpi_profit` → 0 AUTO. Sửa: `Dockerfile` thêm `COPY data
     ./data` (đúng 3 file nhỏ đã commit) + `.dockerignore` (mới, chặn mọi
     thư mục con `data/` chứa dữ liệu thật/PII). Test mới `tests/
     test_deployment_canonical_data_packaging.py` (5 test, tái hiện đúng
     production failure trước khi sửa). SHA
     `122f170150a3fb681c8ee7fcd448574b69a074c1`.

  Cả hai đều là gap đóng gói Docker (file/package cần thiết không nằm
  trong build context), KHÔNG phải thay đổi kiến trúc/business logic —
  không đụng AUTO rule, Product Identity Authority, R2/Render/Cloudflare
  architecture. Full regression sau cả hai: **1494 passed, 11 skipped**
  (từ `1489 passed, 11 skipped` baseline S071B implementation — +5 test
  mới, không regression). Chi tiết đầy đủ, evidence từng bước, RETURN
  block: `docs/sessions/S071-shared-online-beta.md` §13–§14.
  `RENDER_NEXT_ACTION` (chưa xác nhận trong session): Owner chờ Render
  auto-deploy build trên `122f170`, chạy lại đúng workbook cohort, xác
  nhận số liệu khớp lại 22 AUTO/36 Review/100%/0 lỗi im lặng.

- **S071B — Stateless Persistence Adapter (nhánh `s071b/stateless-r2`,
  baseline `5f12516cde2c51b4307413ac960eb6a1c97da2ec` = HEAD của nhánh S071
  tại thời điểm mở phiên). CODE COMPLETE + VERIFYING, CHƯA DEPLOYED
  (deployment thật + 2 packaging repair — xem entry ngay trên), CHƯA
  merge canonical.** Follow-up trực tiếp của "S071 DEPLOYMENT GATE" bên
  dưới: thay SQLite + persistent Disk (Render, 1 disk/service) bằng
  **Cloudflare R2** để Reports Python web runtime trở thành STATELESS —
  chạy được trên bất kỳ host Python nào, không cần volume.

  **SUPERSEDES** kiến trúc "S071 DEPLOYMENT GATE" bên dưới (Render + MỘT
  persistent Disk `/app/persistent`, `REPORTS_DATA_ROOT` gộp SQLite +
  artifact). Lý do: persistent disk là implementation convenience của
  S071 (giải quyết ràng buộc "1 disk/service" của Render), KHÔNG phải một
  yêu cầu của Reports Core — bản thân registry run + artifact chưa từng
  cần đọc/ghi ngẫu nhiên trên đĩa, chỉ cần put/get theo `run_id`, đúng hình
  dạng một object store. `REPORTS_DATA_ROOT`/SQLite/`render.yaml` disk cũ
  của S071 KHÔNG bị xoá khỏi lịch sử — chỉ không còn là đường production
  hiện hành.

  Implementation (đổi tối thiểu, không đổi Reports Core/business logic,
  không đổi call site nào ngoài đúng chỗ cần chọn backend):
  - `tools/storage/r2_store.py` (mới, NGOÀI `app/` — `boto3` bị cấm import
    trực tiếp dưới `app/`, xem `ADR-101`/
    `test_no_module_under_app_reaches_the_network`): put/get JSON + bytes
    trên R2 qua client S3-compatible, key `runs/<run_id>.json` (run_id đã
    sortable theo thời gian — `get_run` O(1), liệt kê mới→cũ bằng sort tên
    khoá, không cần index JSON dùng chung) và `artifacts/<run_id>.xlsx`.
    `tools/storage/errors.py` (mới): `StorageUnavailableError`/
    `RunAlreadyExistsError`/`CorruptRunRecordError` dùng chung.
  - `app/web/storage_backend.py` (mới): `LocalRunStore` (SQLite + file cục
    bộ — hành vi S070/S071 giữ nguyên tuyệt đối) và `R2RunStore` cùng một
    interface (`create_run`/`get_run`/`list_runs`/`save_artifact`/
    `artifact_response`); `build()` chọn R2 khi đã cấu hình đủ 4 biến
    `R2_ACCOUNT_ID`/`R2_BUCKET`/`R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY`,
    ngược lại fallback `LocalRunStore` — TRỪ khi `REPORTS_REQUIRE_R2=1`
    (production), khi đó fail `StorageConfigurationError` ngay lúc khởi
    động thay vì âm thầm chạy bằng đĩa ephemeral trong container.
  - `app/web/server.py`: thay `registry = run_registry.RunRegistry(...)`
    bằng `store = storage_backend.build(...)` (tham số `store=` cho phép
    test tiêm trực tiếp); mọi route đổi `registry.` → `store.`, bọc qua
    `_guarded()` (lỗi storage → HTTP 503 rõ ràng, KHÔNG hiểu nhầm thành
    "không tìm thấy"/"lịch sử rỗng"); artifact upload (R2: temp local →
    upload → verify `head_object` → xoá temp) PHẢI thành công trước khi ghi
    run — fail closed, không để lộ run "thành công" mà artifact không tồn
    tại. Raw workbook upload vẫn temp-only, không đổi (không upload lên R2
    ở S071B).
  - `render.yaml`: xoá `disk:` (không còn Disk nào); thêm
    `REPORTS_REQUIRE_R2=1` + 4 biến `R2_*` (secret `sync: false`).
    `Dockerfile`: cập nhật comment, `mkdir` giữ nguyên nhưng chỉ còn ý nghĩa
    scratch space tạm, không phải mount point persistent.
    `pyproject.toml`: thêm optional-dependency `storage = ["boto3>=1.34"]`,
    gộp vào `web-prod`.

  Test mới: `tests/test_r2_store.py` (20 test — put/get JSON round-trip,
  duplicate run_id → `RunAlreadyExistsError`, JSON corrupt →
  `CorruptRunRecordError` (không phải `None`), R2 unavailable/timeout/auth
  → `StorageUnavailableError`, list newest-first + list rỗng an toàn + list
  lỗi không biến thành lịch sử rỗng, artifact put/get round-trip, verify
  upload sai kích thước → fail closed), `tests/test_storage_backend.py`
  (18 test — chọn backend theo env, fail closed khi `REPORTS_REQUIRE_R2`
  thiếu credential, `R2RunStore` round-trip/multi-viewer/list bỏ qua đúng
  1 record hỏng mà không sập cả trang/artifact upload-verify-xoá temp/
  artifact-run mismatch bị từ chối), cùng 9 test tích hợp Flask mới trong
  `tests/test_web_server.py` (run→download round-trip qua R2 thật (fake
  client), 2 viewer độc lập đọc chung 1 run qua R2, 2 run tạo gần đồng thời
  đều lưu độc lập, artifact upload fail → run không xuất hiện, get/list
  fail → 503 không phải 404/lịch sử rỗng, artifact-run mismatch → 404,
  `REPORTS_REQUIRE_R2` fail app startup khi thiếu credential). `tests/
  fixtures/fake_r2_client.py` (mới): fake S3-compatible client in-memory,
  tiêm lỗi theo method — không cần credential/mạng R2 thật (Claude Cloud
  không có credential R2, đúng dự liệu của task S071B). Full regression:
  **1489 passed, 11 skipped** (từ baseline `1442 passed, 11 skipped` —
  +47 test mới, không skip nào đổi, không giảm coverage nào có sẵn). Bất
  biến kiến trúc `test_no_module_under_app_reaches_the_network` verify lại
  PASS sau khi thêm `tools/storage/r2_store.py` (nằm ngoài `app/`, đúng vị
  trí — `app/web/storage_backend.py` chỉ import `tools.storage.r2_store`,
  không tự `import boto3`).

  **Production LOC**: 429 dòng Python net mới (`app/web/storage_backend.py`
  176 + `tools/storage/r2_store.py` 198 + `tools/storage/errors.py` 25 +
  `app/web/server.py` net +30) — vượt ước tính audit ban đầu (~250–350)
  nhưng dưới ngưỡng dừng cứng 500 (không trigger `CHANGE_BUDGET_EXCEEDED`).
  Vượt ước tính chủ yếu do failure model tường minh (phân biệt rõ
  storage-unavailable/corrupt/not-found/already-exists thay vì gộp chung
  một exception) và test injection (`client=`/`env=` xuyên suốt) — không
  phải do một generic storage framework hay abstraction nhiều provider
  (đúng constraint "một R2 adapter, không abstract 5 provider").

  **`R2_LIVE_VERIFICATION = BLOCKED_BY_MISSING_CREDENTIAL`** — môi trường
  Claude Cloud chạy session này không có credential R2 thật
  (`R2_ACCOUNT_ID`/`R2_BUCKET`/`R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY`);
  `boto3` cũng không cài sẵn (không cần cho test — toàn bộ test tiêm
  `client=` fake, không import `boto3` thật). Verify được bằng test có
  fake client (47/47 PASS), KHÔNG verify được bằng R2 thật — đúng dự liệu
  trước của task ("Nếu credential không tồn tại trong Claude Cloud: tests
  dùng fake/mock. Không STOP implementation"), không coi là architecture
  blocker.

  **`DEPLOYMENT_STATUS = DEPLOYMENT_READY`, KHÔNG DEPLOYED** — session
  không có tài khoản Cloudflare/Render nào để tạo R2 bucket/API token thật
  hay deploy blueprint mới. `docs/deployment/S071_DEPLOYMENT.md` đã cập
  nhật SUPERSEDES + bước Owner cần làm (tạo R2 bucket, API token, cập nhật
  biến môi trường Render). Chi tiết đầy đủ, DECISION log, RETURN block tại
  `docs/sessions/S071-shared-online-beta.md` §12.

- **S071 — Shared Online Beta / Cloud-First** — kiến trúc SQLite +
  `REPORTS_DATA_ROOT` + Render Disk. **SUPERSEDED BY S071B** (bên trên) kể
  từ implementation SHA của nhánh `s071b/stateless-r2`. Giữ nguyên như bản
  ghi lịch sử bên dưới — không sửa lại các đoạn cũ để giả như S071 từng
  chọn kiến trúc stateless ngay từ đầu.

- **S071 — Shared Online Beta / Cloud-First (nhánh
  `claude/s071-shared-online-beta-inydpg`, baseline
  `d64d208775c96a02791c957df25c11d6bf9835f8` = HEAD canonical tại thời điểm
  mở phiên, không drift). CODE COMPLETE + VERIFYING, CHƯA DEPLOYED, CHƯA
  merge canonical.** Xây trên S070 (Web Beta V1, chạy cục bộ trên máy
  Owner) để biến Reports Web thành một shared online beta thật: (1) run
  registry đổi từ `dict` process-local sang SQLite persistent
  (`app/web/run_registry.py`) — sống qua restart, nhiều viewer/nhiều worker
  process cùng đọc một trạng thái; (2) Tracking Sync Model đổi từ "đọc
  capture chụp tay trên máy Owner" sang **PULL ON REPORT RUN**
  (`tools/tracking/live_pull.py`) khi
  `TRACKING_REPORT_SOURCE_URL`/`TRACKING_REPORT_API_KEY` được cấu hình ở
  environment (deployment cloud) — máy Owner không còn nằm trên critical
  path; khi CHƯA cấu hình (máy Owner local, đúng trạng thái S068–S070),
  hành vi cũ giữ nguyên tuyệt đối, không đổi gì; (3) thêm trang `/history`
  (lịch sử run, mới nhất trước); (4) `app/web/wsgi.py` + `Dockerfile` cho
  triển khai production qua gunicorn (khác `app/web/launcher.py` cục bộ,
  không đổi).

  Test mới: `tests/test_web_run_registry.py` (12 test — round-trip field,
  PERSIST qua "restart" mô phỏng bằng việc mở `RunRegistry` MỚI trỏ cùng
  file DB sau khi xoá reference Python cũ, MULTI-VIEWER bằng 2 instance
  registry độc lập, concurrent reads/writes 8–10 thread), cùng
  `tests/test_tracking_live_pull.py` (20 test — thành công, REQUIRED
  `purchase_price_history`/`catalog` fail → raise rõ node, mô phỏng
  timeout/403/502/404/malformed-schema, TUỲ CHỌN `inv_map` fail không chặn
  run). `tests/test_web_server.py` viết lại cho registry mới (43 test, từ
  34 — restart persistence, multi-viewer qua 2 Flask app + 2 test client
  cùng `db_path`, storage-failure trả 500 rõ ràng không traceback, live-pull
  integration không âm thầm fallback khi Tracking unavailable). Full
  regression: **1440 passed, 11 skipped** (từ `1404 passed, 11 skipped`
  baseline S070). Bất biến kiến trúc `test_no_module_under_app_reaches_the_network`
  (ranh giới network `ADR-101`/`DEC-152` §6) verify lại PASS sau khi thêm
  `tools/tracking/live_pull.py` (nằm ngoài `app/modules/**`, đúng vị trí).

  **`TRACKING_LIVE_VERIFICATION = BLOCKED_BY_REMOTE_SECRET`** — môi trường
  Claude Cloud chạy session S071 không có
  `TRACKING_REPORT_SOURCE_URL`/`TRACKING_REPORT_API_KEY`; adapter live pull
  chỉ verify được bằng test có mock (30/30 PASS, không mạng thật), đúng như
  S071 §7 dự liệu trước — KHÔNG coi là architecture blocker.

  **`DEPLOYMENT_STATUS = DEPLOYMENT_READY`, KHÔNG DEPLOYED** — session
  không có credential hosting/DNS/Cloudflare nào. `docs/deployment/
  S071_DEPLOYMENT.md` ghi đủ "exact minimal deployment action" cho Owner:
  chọn nhà cung cấp compute+volume (Dockerfile provider-agnostic), mount
  volume vào `/app/data` + `/app/outputs`, đặt hai biến môi trường
  Tracking, trỏ DNS `reports.tinphatcrm.com`, bật Cloudflare Access. Chi
  tiết đầy đủ, bảng so sánh kiến trúc, DECISION log, và RETURN block đầy đủ
  tại `docs/sessions/S071-shared-online-beta.md`.

  **Cập nhật cùng ngày — S071 DEPLOYMENT GATE.** Tiếp tục trực tiếp (không
  mở task/kiến trúc mới): thực hiện đúng "deployment architecture
  selection" thay vì đẩy việc chọn nhà cung cấp cho Owner. Verify trực tiếp
  bằng lệnh (không giả định): session KHÔNG có CLI provider nào cài sẵn
  (`flyctl`/`render`/`railway`/`aws`/`gcloud`/... đều "not found") và
  egress mạng session bị chính sách tổ chức chặn tới host hosting/DNS
  ngoài allowlist nội bộ (`curl https://api.fly.io` → proxy `403`,
  `recentRelayFailures` của agent proxy xác nhận `connect_rejected`) — hai
  giới hạn độc lập, mỗi cái đã đủ chặn tự provisioning từ trong session.
  Trong phạm vi làm được: so sánh 3 lựa chọn hosting thực tế (Render/
  Fly.io/VPS thô), **CHỌN Render** (Web Service, Docker + 1 Disk) — lý do:
  duy nhất vừa có persistent disk vừa deploy-từ-GitHub hoàn toàn qua
  dashboard, không đòi Owner học CLI, đúng trọng số "operational
  simplicity" cho một Owner không chuyên kỹ thuật. Phát hiện: Render chỉ
  cho gắn ĐÚNG MỘT persistent Disk mỗi service, trong khi SQLite registry
  (`data/web_runs/`) và artifact (`outputs/reports/`) trước đó là hai gốc
  khác nhau — thêm biến môi trường `REPORTS_DATA_ROOT` (mới,
  `app/web/server.py` + `app/web/run_registry.py`) để cả hai cùng trỏ vào
  một gốc mount khi biến này được đặt; vắng mặt (mọi test/local dev) giữ
  nguyên đường cũ tuyệt đối — đây là thay đổi tối thiểu trực tiếp cần cho
  blocker deployment thật, không phải refactor lại kiến trúc đã accept.
  Viết `render.yaml` (blueprint đầy đủ, Owner chỉ cần bấm theo, không tự
  cấu hình) và viết lại `docs/deployment/S071_DEPLOYMENT.md` thành đúng 6
  bước Owner cần làm (tạo tài khoản Render có thanh toán, Deploy Blueprint,
  dán secret Tracking thật, Cloudflare CNAME, Custom Domain, Cloudflare
  Access). `OWNER_PAYMENT_REQUIRED = YES` (~US$7–10/tháng, Render Starter +
  1GB Disk — không provider managed nào trong 3 lựa chọn có persistent disk
  miễn phí vĩnh viễn, không riêng Render) — dừng đúng tại đây, không tự tạo
  tài khoản/subscription thay Owner. Test mới `tests/test_web_data_root.py`
  (2 test — có/không `REPORTS_DATA_ROOT`), full regression sau thay đổi:
  **1442 passed, 11 skipped** (từ 1440). Không gate nào cần production thật
  (HTTPS/Access/multi-viewer trên mạng thật/Tracking live/real cohort) được
  fabricate PASS — tất cả ghi `NOT_EXECUTABLE_IN_THIS_SESSION` đúng thực
  tế. Chi tiết đầy đủ + RETURN block: `docs/sessions/S071-shared-online-beta.md`
  §11.

- **S070 — Web Beta V1 / Thin Web Delivery Layer (nhánh `s070/web-beta-v1`,
  baseline `fad7647a5f07e5eeaa3587a03f0688cb6f7bb904`), Independent Review
  PASS sau 1 repair, ĐÃ merge canonical qua
  `8d1f87902fea840b034227ae460bb0fa3a42d52b` — xác nhận bằng
  `git merge-base --is-ancestor`.** Web Beta V1 giờ là cửa vào có sẵn cho
  Owner (Tkinter `Open Reports.command` giữ vai trò tham chiếu/fallback,
  không đổi hành vi). Thêm `app/web/`
  (Flask, opt-in dependency dưới `[project.optional-dependencies].web` —
  core CLI/Tkinter footprint không đổi): Owner mở browser tại
  `127.0.0.1:8765` qua double-click `Open Reports Web.command`, chọn/upload
  workbook `.xlsx`, chạy báo cáo, xem Tổng đơn/AUTO/Cần xem lại/Ưu tiên xem
  ngay/Accounting coverage + Review reasons theo dòng, tải Excel, gửi phản
  hồi — không cần terminal sau khi server đã chạy. Tầng web KHÔNG tính lại
  business rule: gọi nguyên `app.owner_usability.run_owner_report()` (đúng
  adapter `owner_launcher.py` Tkinter đã dùng), reuse nguyên
  `app/beta_feedback.py` + `app/beta_telemetry.py` (S069, không tạo taxonomy
  hay schema thứ hai), reuse nhãn Review reason qua
  `app/beta_presentation.py`. Download artifact chỉ resolve qua `run_id` từ
  registry server tự tạo (không nhận path tuỳ ý từ browser); upload luôn lưu
  bằng tên server sinh (không tin filename client, không path traversal).
  Real cohort rerun qua server thật (`127.0.0.1:8765`, upload qua `curl -F`,
  cùng workbook + capture evidence với LOCAL): `58/83/22/36/100%/0
  dropped/3` business severity, Review reason counts khớp tuyệt đối LOCAL,
  artifact tải về SHA256 khớp byte-for-byte file trên đĩa, feedback +
  telemetry ghi đúng 1 dòng mỗi loại (không duplicate), response không rò rỉ
  secret/absolute path/authority payload (grep xác nhận). Trong lúc
  implement, `app/web/launcher.py` bản đầu dùng `import socket` để pre-check
  cổng đã làm FAIL 3 test bất biến kiến trúc có sẵn
  (`test_no_module_under_app_reaches_the_network` — không module nào dưới
  `app/` được import network primitive trực tiếp, Tracking phải qua
  `tools/tracking/`); sửa cục bộ ngay trong phiên bằng
  `werkzeug.serving.make_server` + bắt `OSError` (không cần `socket`, không
  còn race check-rồi-bind) — regression PASS lại đủ, bất biến gốc không bị
  hạ thấp. Regression toàn repo (implementation SHA `026c7db`): `1403 passed,
  11 skipped` (từ `1373 passed, 11 skipped` trước S070; +30 test mới cho
  `app/web/*`, không skip nào đổi).
  **Independent Review** (cùng ngày, SHA implementation `026c7db` →
  repair `s070/web-beta-v1` HEAD mới) verify lại độc lập toàn bộ bằng git,
  code, test thật (python3.11, không mock `test_client` cho phần runtime) và
  tìm ra 1 finding LOCAL + CLEAR + DIRECT BLOCKER: `app/web/launcher.py` gọi
  `werkzeug.serving.make_server(HOST, PORT, app)` KHÔNG truyền
  `threaded=True` → server single-threaded; verify trực tiếp bằng repro (giữ
  một kết nối HTTP/1.1 keep-alive mở, request độc lập thứ hai timeout 100%
  cho tới khi connection đầu đóng) — vì launcher tự mở browser
  (`webbrowser.open`) ngay sau khi bind, tab đó giữ đúng loại kết nối này,
  nghĩa là flow bình thường (double-click → browser tự mở) có thể tự khoá
  toàn bộ server cho chính Owner (upload lần 2, refresh, tải file, gửi phản
  hồi đều treo vô thời hạn). Repair: thêm `threaded=True` vào lệnh
  `make_server` (không đổi bind host, không bật debugger/reloader) + 1 test
  regression mới xác nhận cấu hình. Sau repair: `1404 passed, 11 skipped`;
  repro xác nhận hết treo; rerun toàn bộ battery upload adversarial (path
  traversal, `.xlsx.exe`, empty/zero-byte/malformed workbook, >25MB thật,
  Unicode filename, artifact bị xoá khỏi đĩa sau khi đăng ký) đều fail-safe;
  2 run liên tiếp qua server thật → đúng 2 artifact riêng biệt (SHA256 khớp
  byte-for-byte đĩa), đúng 2 dòng telemetry, đúng 2 dòng feedback liên kết
  đúng run; LOCAL (`run_owner_report()` gọi trực tiếp) và WEB (server thật)
  trên cùng workbook thật khớp tuyệt đối: `58/83/22/36 (AUTO/Review), 100%
  accounting, business severity 3, dropped 0`; render thật qua Browser pane
  (không chỉ Flask test client) xác nhận trang usable, nhãn đúng, không lộ
  thông tin kỹ thuật. Chi tiết đầy đủ, evidence từng bước, và giới hạn đã
  biết tại `docs/sessions/S070-web-beta-v1.md` → "Independent Review".

- **S068 — Internal Beta review (checkpoint `f8d3ffc3c2071a33f2818664713c62da9cfe176f`,
  nhánh `s068/inv-map-vertical`, ĐÃ merge canonical qua
  `3f92c953b4c6d12834d4d3a0c611a7b27e7e0061` — xác nhận lúc mở phiên S069
  bằng `git merge-base --is-ancestor`).** Owner xác nhận
  `inv.map` (bảng do người của Tracking duyệt, khoá bằng câu tên hàng kế toán
  đầy đủ đã `normCode()`) là authority cùng cấp `alias.map` — không còn
  candidate-tier, không cần `confirmation_action` thứ hai từ Reports.
  `ProductIdentityResolver` mở rộng: thử `alias.map`/`board` (khoá mã) trước,
  MISS thì thử `inv.map` (khoá câu tên hàng); `"-"` = Ignore đã người xác
  nhận (`PendingReason.TRACKING_INV_MAP_EXPLICIT_IGNORE`); target hết hợp lệ
  trong `board` = Pending (`MAPPING_STALE_TARGET_ABSENT`, tái dùng lý do có
  sẵn); khoá vắng mặt = Pending như MISS gốc. Không fuzzy, không substring,
  không `board.name`/`board.alt`, không `extractCode()`.
  Acquisition: `tools/tracking/capture_inv_map.py` (mới), đọc
  `GET /api/xuat/inv_map`, cùng credential/fail-safe/`INV-12` với
  board/alias/PPH; production đã capture thật COMPLETE, 468 entries, 18
  explicit Ignore.
  Rerun cohort thật 2026-08-31 (58 đơn / 83 dòng), độc lập tái xác nhận hai
  lần (implementation + Internal Beta review), cùng một kết quả: **AUTO
  22 đơn / 23 dòng** (từ `0/0`), Review Queue 36 đơn / 60 dòng, Error `0`,
  Dropped `0`, accounting coverage `100%`, silent error candidates `0`.
  52 dòng resolve identity qua `inv.map` (39 có giá đầy đủ qua
  `TrackingHistoryPriceProvider` hiện có — không current-PP backfill, không
  suy đoán temporal; 13 dòng identity đã có nhưng PP evidence chưa phủ ngày
  bán, giữ Pending trung thực). 31 dòng còn `IDENTITY_UNRESOLVED` — 19 unique
  mô tả chưa có khoá `inv.map`: 13 là sản phẩm thật (đã chuẩn bị candidate
  gợi ý không-authority cho Owner), 6 là dòng chi phí/dịch vụ (KHÔNG đưa vào
  hành động classify sản phẩm — xem finding riêng dưới).
  Focused/affected/full regression tái xác nhận độc lập tại review: `1349
  passed, 11 skipped` (11 skip là ngoại lệ môi trường đã biết, không đổi từ
  trước vertical này).
  Backend/security review (Internal Beta gate, phiên này): Reports không có
  frontend/server network split của riêng nó (CLI + cửa sổ Tkinter cục bộ,
  cùng tiến trình tin cậy với logic nghiệp vụ) — ranh giới tin cậy THẬT DUY
  NHẤT là Reports (client) ↔ Tracking `/api/xuat/*` (server), và ranh giới đó
  giữ nguyên: chỉ `GET`, danh sách node đóng, credential chỉ qua biến môi
  trường/header (không log/không persist/không hardcode — có test xác nhận),
  fail-closed trên mọi hình dạng lạ. Không có write path Reports→Tracking
  (`grep` xác nhận 0 lệnh `PUT/POST/PATCH/.push/.set/.update` trong toàn bộ
  `tools/tracking/`). `PriceResolutionRecord.__post_init__` là bất biến cứng
  chặn RESOLVED-thiếu-giá và PENDING-mang-giá ở tầng dữ liệu, không chỉ tầng
  hiển thị. `data/captures/`, `data/tracking_catalog/`, `data/tracking_inv_map/`,
  `data/tracking_price_history/` là runtime evidence thật, cố ý KHÔNG commit
  (kỷ luật thao tác, không phải `.gitignore` pattern — xem DEFERRED).

### PLANNED — PHASE-PRA: Persistent Reporting & Analytics (S072, 2026-09-02)

- **TASK-PRA-000 — Kế hoạch kiến trúc (SPIKE, DONE trong S072, nhánh
  `claude/reports-pipeline-architecture-gj8bji`).** Chỉ lập kế hoạch: không
  code feature, không refactor, không migration, không deploy, không sửa
  Tracking (READ-ONLY REFERENCE). Tài liệu chốt tại
  `docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md` (18 mục
  A–R) và bàn giao
  `docs/sessions/S072-persistent-reporting-analytics-planning.md`.
  Kết luận chính: (1) Reports hiện chỉ persist 7 số tổng hợp/run + XLSX —
  chưa có dữ liệu đơn/dòng để query lịch sử; AUTO/Review chỉ được suy ra
  trong exporter. (2) Hai origin lịch sử tách biệt tuyệt đối:
  `LEGACY_REFERENCE` (Excel cũ nhập nguyên trạng, kèm cờ lỗi công thức
  A1–A6, không tính lại) và `PIPELINE_GENERATED` (kết quả pipeline, có
  provenance snapshot + evidence Tracking). (3) `ORDER_KEY = Số BH chuẩn hoá`
  (guard 90 ngày chống trùng số khi reset); `ORDER_LINE_KEY = (ORDER_KEY,
  product_key, occurrence_index)` + `line_fingerprint` — nguồn ERP không có
  khoá dòng tự nhiên. (4) Snapshot model với coverage tường minh và HAI trục
  phiên bản (nguồn kế toán đổi ≠ pipeline chạy lại với evidence mới) → 4
  CASE INSERT / SAME / CHANGED / REMOVED_CANDIDATE + RESULT_REVISED; không
  DELETE/UPDATE-in-place fact. (5) UI giữ 6 khu vực, chỉnh: "Cần kiểm tra"
  gộp Review Queue + Thay đổi nguồn + Đối chiếu cũ/mới; "Lịch sử dữ liệu" →
  "Dữ liệu" (coverage calendar); "Sản phẩm" lùi slice cuối; điều hướng tab
  ngang + thanh ngữ cảnh sticky theo token `--tp-*` của Tracking (chỉ chép
  CSS, không runtime dependency).
  Roadmap 5 slice dọc (đều `TRACKING_CHANGE_REQUIRED = NO`,
  `PROTECTED_CORE_IMPACT = NONE`): PRA-001 Legacy reference + nền DB →
  PRA-002 Persistence + overlapping-upload reconciliation (slice nặng nhất,
  Tier C, E2 review) → PRA-003 Tổng quan + Nhân viên → PRA-004 Bán hàng
  drill-down + Review Operations → PRA-005 Sản phẩm + analytics LATER.
  **Chưa task nào READY.** Chặn bởi 4 quyết định Owner (DB production,
  nguồn coverage, chính sách CHANGED, chính sách REMOVED) + ratify
  amendment ADR-101 (web layer = Flask/Jinja) — danh sách đủ 13 quyết định
  tại mục N của kế hoạch. `SCOPE_DRIFT = NO`. Mục "DEFERRED → Dashboard"
  bên dưới nay có kế hoạch nhưng vẫn chưa READY.

### S076 (2026-09-02) — TASK-PRA-001 repair cycle 1/1: hai blocking finding đã sửa; DEC-168 mở ngân sách ~1.050 LOC

Independent Review trên `7d84072765288b7a9dc28679a09325fce7860b48` =
`CHANGES_REQUIRED`. Repair base giữ nguyên, KHÔNG rewrite.

Hai finding cùng một bản chất — **một sự cố được trình bày như trạng thái
bình thường**, đúng loại sai mà cả PRA-001 tồn tại để ngăn:

- **FIND-PRA001-R01** — verifier duyệt từ DB → Excel nên chỉ trả lời được
  "cái đã nhập có đúng không", không bao giờ thấy "cái chưa từng được nhập".
  Tái tạo trước repair: mất trọn `Summary 2025` (0 dòng nhập, nguồn có số ở
  dòng 4/5/6) mà vẫn in `matched=372 mismatched=0`. Sửa: parser raise
  `LegacyImportError` nêu đích danh sheet + dòng khi một dòng có giá trị
  nghiệp vụ không khớp contract phân loại; verifier đổi vòng lặp Summary
  sang EXCEL → DB, in `SUMMARY_SOURCE_ROWS_WITH_VALUES` /
  `SUMMARY_IMPORTED_ROWS` / `SUMMARY_UNACCOUNTED_ROWS`, thiếu dòng nguồn =
  exit khác 0. Sau repair, đúng case reviewer: `SUMMARY_UNACCOUNTED_ROWS=3`,
  `matched=580 mismatched=0`, **exit=1**.
- **FIND-PRA001-R02** — `abort(503)` của `_guarded` ném `HTTPException`, bị
  `except Exception` trong route import nuốt thành redirect 302 "Không đọc
  được workbook legacy": một sự cố DATABASE hiển thị thành LỖI FILE của
  Owner, phá `CHECK-PRA001-06` trong im lặng. Sửa tối thiểu:
  `except HTTPException: raise` trong đúng route đó.

Cả hai test repair đã chứng minh FAIL trên code trước repair (`assert 302 ==
503`; `DID NOT RAISE LegacyImportError`).

**DEC-168 (Owner):** (1) `PRA-001_CHANGE_BUDGET_EXCEPTION = APPROVED`, ngân
sách production logic ~1.050 dòng — review xác minh `ESSENTIAL ≈ 950`,
`OUT_OF_SCOPE = 0 material`, nên chỉnh ngân sách theo thực tế thay vì cắt
capability; đo sau repair = **1.045**, trong ngân sách. (2) Hợp đồng nghiệp
vụ: dòng Summary có giá trị nghiệp vụ mà contract không nhận ra thì **FAIL
TO**, KHÔNG auto-guess `row_kind` từ việc dòng có số.

Regression: `1586 passed, 11 skipped` → `1600 passed, 11 skipped` (+14 test
repair, 0 test mất). PRA-001 focused suite `106 passed`. Validator 4/5 PASS;
reference integrity chỉ còn 3 finding PRE_EXISTING của REM-T06.
Repair budget: **1/1 đã dùng, còn 0**.

`CHECK-PRA001-01` vẫn NOT_TESTED (cần file Excel thật) nhưng evidence đã
viết lại: fidelity kể từ đây gồm `VALUE MATCH` **+** `SOURCE COVERAGE`;
`628/0` không còn được dùng một mình. `CHECK-PRA001-06` mở rộng sang cả
đường GHI. `CHECK-PRA001-09` vẫn BLOCKED (cần PostgreSQL thật).

PROTECTED_CORE_IMPACT = NONE. TRACKING_CHANGED = NO. Không implement PRA-002.
Chi tiết: `docs/sessions/S076-pra-001-repair-cycle-1.md`.

### S075 (2026-09-02) — TASK-PRA-001 = IMPLEMENTED; Legacy Reference Vertical chạy đầu-cuối; CHANGE_BUDGET_EXCEEDED chờ Owner

Nhánh `claude/reports-pipeline-architecture-gj8bji`, base authority
`b50e8bc29b92e8f5199675cfc8574332970fe1b9` (close-out S074, đã xác minh).

**Owner giờ xem được số báo cáo cũ ngay trong Reports.** Nhập workbook
"Báo cáo Kinh doanh" ở tab **Dữ liệu** → mở tab **Nhân viên** (ma trận
tháng × người bán, nghìn đồng) hoặc **Doanh số ngày** (từ DataChart, VND
nguyên) → chọn kỳ lịch sử. Mọi con số đeo nhãn `LEGACY` kèm đơn vị; ô có
lỗi công thức đã biết mang dấu nhắc A1/A2/A4/A6 — không cần mở Excel để
xem summary cơ bản nữa.

Đã dựng: `tools/db/` (engine builder + fail-closed + `assert_schema_current`),
Alembic chain với ĐÚNG một migration `0001_legacy` (4 bảng `legacy_*`),
`app/legacy/` (importer thuần openpyxl), `app/web/history_store.py`
(`LegacyRepository`, SQLAlchemy Core, engine tiêm được), 5 route web,
layout + tab bar + CSS token `--tp-*` chép tĩnh từ đặc tả design của
TASK-PRA-000 mục E (không hot-link, không JS Tracking).

Ba bất biến được khoá bằng test, không phải bằng lời:
1. **Không tính lại số cũ** — fixture có ô giá trị `999` với công thức
   `=G9/5.5%` (đúng công thức ~547.272); hệ thống lưu và hiện `999`. Quét
   AST: không phép chia/nhân nào trong `app/legacy/`; quét mã sau khi xoá
   chuỗi/chú thích: `/2`, `/ 2`, `5.5%` không có trong logic.
2. **Không số cũ nào hiển thị thiếu nhãn** — test trích MỌI ô số từ HTML
   và khẳng định ô nào cũng mang `LEGACY` + đơn vị.
3. **Không biến sự cố thành "chưa có dữ liệu"** — thiếu cấu hình hoặc
   schema cũ → app không khởi động; DB lỗi lúc request → HTTP 503.

Trạng thái check: 8 REQUIRED PASS (E1); CHECK-01 (fidelity trên FILE THẬT)
= NOT_TESTED vì workbook thật không có trong Claude Cloud và không được
commit (PII) — script đối chiếu `tools/analysis/verify_legacy_import.py`
đã viết và chạy PASS trên fixture (`matched=628 mismatched=0`); CHECK-09
(DDL trên PostgreSQL thật) = BLOCKED vì session không có Postgres và không
được tự tạo dịch vụ trả phí. Cả hai thành gate của Owner, quy trình đã
viết ở `docs/deployment/S071_DEPLOYMENT.md` bước 8–12.

Regression: baseline đầu phiên `1494 passed, 11 skipped` → cuối phiên
`1586 passed, 11 skipped` (+92 test mới, 0 test mất, 0 skip mới).
Validator 4/5 PASS; reference integrity chỉ còn 3 finding PRE_EXISTING của
REM-T06 (S075 thêm 0). Protected core, R2, Tracking KHÔNG bị chạm.

**BLOCKER CẦN OWNER: `CHANGE_BUDGET_EXCEEDED`.** 1.024 dòng logic
production Python so với ngưỡng dừng cứng 600 (930 nếu chỉ tính đúng tập
file mà CHANGE_BUDGET liệt kê). Ngân sách khác vẫn trong hạn (template
284/300, CSS 200/450, test 92 ≥ 25, đúng 3 dependency được phép). Ba
phương án A/B/C đã viết ở mục "ESCALATION — CHANGE_BUDGET_EXCEEDED" trong
`docs/tasks/TASK-PRA-001-legacy-reference-vertical.md`; session KHÔNG tự
chọn. Vì vậy TASK-PRA-001 = **IMPLEMENTED**, KHÔNG phải DONE, và KHÔNG
merge canonical trước khi Owner phân xử + Independent Review.

Chi tiết đầy đủ: `docs/sessions/S075-pra-001-legacy-reference-vertical.md`.

### CLOSE-OUT S074 (2026-09-02) — ADR-108 APPROVED; TASK-PRA-000 = DONE / architecture finalized; TASK-PRA-001 = READY

- Owner approve ADR-108 (DEC-167): Production structured history = Managed
  PostgreSQL; Artifacts / run JSON / XLSX = R2; Local/test = SQLite;
  PRA-001 database scope = minimum legacy schema only; không prebuild schema
  PRA-002; Tracking READ-ONLY, không đổi.
- `docs/adr/ADR-108-persistent-history-store.md` → Accepted.
- `docs/tasks/TASK-PRA-001-legacy-reference-vertical.md` → READY (gate
  FROZEN từ S073 không đổi; Ready Gate còn 2 điều kiện vận hành: file Excel
  legacy trên máy chạy acceptance, đồng bộ nhánh đầu session).
- Session close-out docs-only: không code, không migration, không provision,
  không deploy. Implementation base = HEAD nhánh
  `claude/reports-pipeline-architecture-gj8bji` sau commit S074.
- Session tiếp theo: implement TASK-PRA-001 theo handoff
  `docs/sessions/S073-pra-finalization.md` (10 bước; bước 2 đã làm ở S074).

### PLANNED — PHASE-PRA finalization (S073, 2026-09-02) — TASK-PRA-001 gate FROZEN

- Owner review kế hoạch S072: `PLANNING_REVIEW = PASS`, `SCOPE_DRIFT = NO`.
  Owner chốt 5 quyết định nền (DEC-166): A giữ Flask + Jinja (amendment
  `docs/adr/ADR-109-web-layer-flask-jinja.md`, ADR-101 thêm Superseded By);
  B coverage auto-detect, phân biệt `DETECTED_DATE_RANGE` với
  `CONFIRMED_COMPLETE_COVERAGE`; C SOURCE_CHANGED giữ version + changed_fields;
  D REMOVED_CANDIDATE không silent delete, không tự loại khỏi analytics;
  E legacy nguyên trạng. Policy reconciliation chốt tại
  `docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md` phụ lục F3.
- Persistence: decision audit R2 vs D1 vs PostgreSQL tại
  `docs/adr/ADR-108-persistent-history-store.md` — đề xuất HYBRID
  (PostgreSQL managed cho structured records + R2 artifact không đổi +
  SQLite local/test). **Status Proposed — Owner CHƯA approve.** Đây là
  quyết định blocking duy nhất còn lại, và chỉ chặn deploy production của
  PRA-001, không chặn implement/test local.
- **TASK-PRA-001 — Legacy Reference Vertical**: task file
  `docs/tasks/TASK-PRA-001-legacy-reference-vertical.md`, Status PLANNED,
  Completion Gate FROZEN (10 check, 9 REQUIRED, Risk 3 → E1), Change Budget
  ≤450 LOC Python (dừng cứng 600). Ready Gate còn 3 ô chưa tick: approve
  ADR-108, file Excel legacy có trên máy chạy acceptance, đồng bộ nhánh
  đầu session. `READY_FOR_PRA_001 = YES` có điều kiện (approve ADR-108
  trước deploy). Implementation handoff:
  `docs/sessions/S073-pra-finalization.md`.
- PRA-002…005: PLANNED, không mở implementation (preview PRA-002 tại phụ
  lục F6 chứng minh PRA-001 không dead-end).

### DEFERRED FINDING — Product Identity Discovery Gap (S068 follow-up audit)

- **Case:** một sản phẩm nhập → bán hết trong ngày → tồn cuối kỳ = 0. Nguồn
  discovery DUY NHẤT đã audit cho `inv.map` (khoá bằng câu tên hàng đầy đủ)
  là file "tồn kho" Owner tải lên (`invNameKey()`/`invRowKey()` khoá theo
  đúng dòng trong file đó — xác nhận trên `origin/main` Tracking thật,
  commit `9ede079413065ae0beef2c3ae005d332d8d92eca`). Một SKU không xuất
  hiện dòng dương trong lần tải "tồn" gần nhất sẽ không bao giờ sinh khoá
  `inv.map`, dù `board` có thể đã biết SKU đó qua một đường khác. `dnhap`
  (nhánh RTDB khác) ĐÃ audit và loại trừ hoàn toàn — đó là nhật ký đăng nhập
  thiết bị lạ, không mang trường sản phẩm nào (`{t, email, may}`), không
  liên quan Product Identity.
- **Bằng chứng thật, cohort 2026-08-31:** 13/13 mô tả kế toán "chưa
  classify" đều có mã ứng viên ĐÃ tồn tại trong `board` (present_in_board
  =true) nhưng KHÔNG có key `inv.map` và 0 hoạt động giá
  (`purchase_price_baseline`/`history` trống cho cả 13 mã) — khớp hồ sơ
  "sản phẩm hiếm, không nhập lại", đúng kịch bản Owner mô tả.
- **STATUS = DEFERRED_KNOWN_LIMITATION.**
- **BETA_BLOCKER = NO** — hệ thống fail-safe đúng: các dòng này ở Pending
  trung thực (Review Queue), không AUTO sai, không mất dòng, không giả giá.
- **REOPEN CONDITION:** chỉ mở lại sau Beta nếu dữ liệu sử dụng thực tế
  chứng minh việc phân loại các mã kiểu này xảy ra đủ thường xuyên và tạo
  workload tay đáng kể.
- **KHÔNG implement trước Beta:** Persistent Identity Inbox, Tracking
  discovery pipeline mới, workaround sales-quantity→inventory, fuzzy
  identity authority, generic MDM, event architecture. Phương án khả dĩ đã
  audit (Reports export mô tả chưa-classify + SL đã bán → Owner tự tải vào
  đúng nút "Tải file tồn" có sẵn của Tracking) vẫn CHƯA implement vì cần
  Owner chấp nhận rủi ro ý nghĩa dữ liệu (số hiển thị tạm thời trên màn Tồn
  kho là "đã bán" chứ không phải "đang tồn") — một quyết định nghiệp vụ,
  không phải một sửa code trung lập.

### DEFERRED FINDING — `inv.map`/`alias.map`/`board` Không Có Temporal Safety Net (S069 Independent Review)

- **Case:** `PP history` (Purchase Price) có temporal validation thật —
  `TrackingPriceHistoryReader` so `captured_at`/khoảng thời gian capture với
  `sale_date` từng dòng, fail-safe về Pending nếu capture không phủ đúng
  ngày bán (`app/modules/pricing/tracking_history/reader.py`). `inv.map`,
  `alias.map`, `board` KHÔNG có cơ chế tương đương: đây là bảng
  khoá→giá trị tại MỘT THỜI ĐIỂM, không có timestamp theo từng entry để so
  sánh. Nếu Tracking SỬA một mapping đã có (không phải thêm mới) giữa hai
  lần Reports capture, Reports dùng capture cũ sẽ resolve theo giá trị CŨ
  và coi là AUTO — khác hẳn PP history (luôn fail-safe về Pending khi
  stale). Đây LÀ rủi ro "wrong AUTO", không chỉ "missed AUTO".
- **Không phải regression của S069 hay S068.** Đặc tính này tồn tại từ
  kiến trúc `alias.map`/`board` gốc (Owner Usability V1, trước cả S068).
  S068 chỉ mở rộng CÙNG mô hình cho `inv.map` như authority thứ hai; S069
  không chạm resolver, chỉ là session ĐẦU TIÊN launcher thật sự dùng đường
  `inv.map` (launcher V1 chưa từng nối trước đó), nên đây là session đầu
  tiên rủi ro này trở thành "sống" trên đường Owner double-click thật thay
  vì chỉ tồn tại trong test/CLI.
- **STATUS = DEFERRED_KNOWN_LIMITATION.**
- **BETA_BLOCKER = NO** — xác suất Tracking SỬA (không phải thêm) một
  mapping đã duyệt, đúng trong khoảng thời gian giữa hai lần Owner capture,
  đúng trên một dòng đang bán, là rủi ro biên rất hiếm; hệ thống vẫn
  fail-safe cho toàn bộ các trường hợp phổ biến hơn (thêm mới, xoá, target
  hết hợp lệ → Pending trung thực).
- **REOPEN CONDITION:** mở lại nếu (a) Owner ghi nhận một trường hợp AUTO
  sai thực tế do mapping bị sửa sau capture, hoặc (b) trước khi thêm một
  authority point-in-time thứ ba tương tự `inv.map`, nên đánh giá lại liệu
  có cần temporal/versioning chung cho cả nhóm nguồn này.
- **KHÔNG implement trước Beta:** thêm timestamp/versioning cho từng entry
  `inv.map`/`alias.map`/`board`, hay đổi Tracking API/schema để hỗ trợ — đây
  là thay đổi kiến trúc/schema Tracking, ngoài phạm vi S069 và cần quyết
  định nghiệp vụ riêng.

### WAITING_EXTERNAL

- Không có blocker authority/cutover hay acquisition còn mở cho S068. Muốn
  tăng coverage cho 13 sản phẩm thật còn Pending, cần Owner classify qua
  Tracking workflow hiện có (đã chuẩn bị candidate gợi ý — không phải
  authority) hoặc Owner quyết định về DEFERRED FINDING ở trên.

### DO_WHEN_IDLE

- TASK-REM-T06 repository-root hygiene: hoàn tất phạm vi README/LICENSE đã có
  khi Owner chọn điều khoản license. Việc này độc lập với capture, không đổi
  business rules, và là hạng mục maintenance/governance còn lại đã được tài
  liệu hóa có đủ giá trị.
- (Low-severity, không chặn Beta) `data/captures/`, `data/tracking_catalog/`,
  `data/tracking_inv_map/`, `data/tracking_price_history/` hiện chỉ tránh
  commit bằng kỷ luật thao tác ("không `git add .`"), không bằng
  `.gitignore` pattern tường minh — có thể thêm pattern phòng vệ khi rảnh.

### DEFERRED

- Dashboard.
- Batch 200.
- Tối ưu AUTO lịch sử tháng 1.
- Signed macOS installer.
- Styling/polish.
- Low-value hardening không chặn kết quả thật.
- Product Identity Discovery Gap (A1/zero-stock) — xem khối riêng ở trên,
  KHÔNG được coi là đã đóng.

## Reports Demo V1 — đã triển khai (2026-08-31)

Theo yêu cầu Owner, CLI + xuất Excel + Review Queue được triển khai trong
cùng phiên trên `codex/demo-v1`, từ đúng SHA
`1ab5dbdfdd70deff1f0636ec1bb5f734ba6a0592`. Worktree đầu phiên detached,
nhánh kỳ vọng `claude/bh73804-confirmed-identity` trỏ cùng SHA; không đồng bộ
sang baseline khác với chỉ định Owner. Không merge.

`app/demo.py` gọi production composition hiện có, giữ PriceResolutionRecord
từng dòng và xuất đúng Summary / Order Lines / Review Queue. Không đổi engine,
business rule, Tracking hay coverage; không đọc PP YAML cũ. Workbook tháng 1
thật đã ẩn danh: 254/254 đơn, 351/351 dòng; AUTO=1, REVIEW_QUEUE=253,
ORDER_ACCOUNTING_RATE=100%, SILENT_DROPPED=0. BH73804 preflight có sẵn:
1/1 đơn Pending do snapshot không phủ ngày bán, không sửa ngày để ép AUTO.

13 focused tests PASS. Full regression trong checkout Git sạch, có quyền
localhost cho test HTTP: 1305 passed, 11 skipped. 15 artifact runtime đầu
phiên còn nguyên và không đưa vào commit. Hướng dẫn: `docs/demo-v1.md`;
bằng chứng: `docs/sessions/DEMO-V1-20260831.md`.

Trạng thái: IMPLEMENTED trong phạm vi Demo V1; Owner có thể mở workbook để
xem AUTO và hàng chờ. Không tuyên bố đóng toàn bộ task xuất báo cáo/CLI lịch
sử hoặc thay trạng thái gate TASK-105/110. Bước tiếp theo: Owner đọc báo cáo
và xử lý bằng chứng còn thiếu của các đơn Pending; không cần dashboard.

## Đồng Bộ Nhánh

Nhánh mặc định (canonical) trên GitHub remote hiện tại:
`claude/extract-upload-repo-gq2ws4` — xác nhận bằng `git remote show origin`
→ "HEAD branch". Tên này là do lịch sử tạo nhánh, không phải "main" theo
nghĩa đen — coi nó là "main" của dự án cho tới khi owner đổi tên chính thức.

Trước khi đọc phần còn lại của file này, xác nhận bạn đang đứng trên nhánh
đó và đã `git fetch` mới nhất. Xem `CLAUDE.md` → "Đồng Bộ Nhánh" và
`governance/core/00_SESSION_ORCHESTRATION.md` → "Giao thức Mở Phiên" bước 0.
File này từng bị đọc từ một nhánh lỗi thời 14 commit, dẫn tới báo cáo tiến độ
sai — xem DEC-118.

## Trạng thái sau GOLDEN #3 — QUANTITY + DISCOUNT (S057, 2026-08-29)

```text
GOLDEN #3 = GOLDEN_PASS (Session 1/2 — không cần Session 2)

Case thật   : BH62439 — Điều hòa Daikin FTHF25XVMV (source_row=52, 1 trong
              4 dòng của đơn), Quantity=2, Discount=100.000 VND
Purchase price : 10.250.000 VND, OWNER_MANUAL_LEGACY_CONFIRMATION
              (Owner-confirmed qua AskUserQuestion, DEC-164) — cùng cơ chế
              BH62063 (DEC-163)
AccountingProfit    (thật) = 500.000 VND   khớp oracle
EligibleKpiProfit   (thật) = 400.000 VND   khớp oracle
              (lệch AccountingProfit đúng bằng Discount — Discount không
              double-count, hai capability tách biệt như DEC-126 điểm 1)

Blocker duy nhất tìm được : thiếu registry entry Owner-confirmed thứ hai
              (data class blocker, KHÔNG phải code bug) — cùng lớp blocker
              khiến Golden #2 (implementation/golden-2-historical-vendor)
              WAITING_REAL_DATA. KHÔNG bịa giá vốn để né; hỏi Owner trực
              tiếp và nhận giá thật.

Production diff : +1 dòng data/historical_confirmed/registry.jsonl,
              +1 file test mới (7 test). 0 dòng app/**/config/** sửa.
Golden Baseline (58 passed, 2 skipped) : KHÔNG đổi (test đó không đọc
              registry.jsonl).
Golden #1 (BH62063)      : regression-safe, không đổi.
Golden #2                : KHÔNG đọc, KHÔNG sửa, KHÔNG reopen TASK-105C/105E.
Full pytest : 1035 passed, 11 skipped, 0 failed (trước: 1028 passed).
Validators  : structure/project_state/evidence/task_completion PASS;
              reference_integrity FAIL đúng 3 issue baseline TASK-REM-T06
              (không đổi). branch_authority_check → AUTHORITY_OK.
```

Bằng chứng đầy đủ: `docs/sessions/S057-golden-3-quantity-discount.md`,
`DEC-164` trong `PROJECT/PROJECT_DECISIONS.md`.

## Trạng thái sau GOLDEN #4 — SAFE PENDING (S058, 2026-08-29)

```text
GOLDEN #4 = GOLDEN_PASS (Session 1/2 — không cần Session 2)

Case thật   : BH62439 — Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV
              (source_row=53, 1 trong 4 dòng của đơn — CÙNG đơn Golden #3,
              dòng 52 đã resolve), Quantity=1, SellPrice=16.300.000,
              Discount=50.000, SaleDate=2026-01-08
Phân loại   : PURCHASE_PRICE_UNRESOLVED (KHÔNG PHẢI IDENTITY_UNRESOLVED —
              product_raw rõ ràng, giữ nguyên; TASK-105D identity resolver
              KHÔNG wiring vào app.pipeline nên "Identity" hiện tại = product_raw)
Mục tiêu    : chứng minh đường SAFE FAILURE — Real input → production thật
              → insufficient evidence → Pending → không bịa giá/lợi
              nhuận/identity → dòng vẫn accounted for → reason trung thực →
              Review Queue hiện có (TASK-110) đã nhận đúng dòng này.

Kết quả (run_import_production() thật, KHÔNG DI/mock/stub):
    price_source = Pending, accounting_purchase_price = None,
    accounting_profit = None, kpi_purchase_price = None
    (provenance = "Pending"), eligible_kpi_profit = None — khớp oracle
    ghi TRƯỚC khi test. Dòng 52 (cùng đơn, đã resolve = 10.250.000) KHÔNG
    rò rỉ sang dòng 53 (cross-line leakage = KHÔNG). Dòng có mặt trong
    result.orders (4/4 dòng, không rơi rớt) VÀ trong Review Queue —
    detect_missing_purchase_price (aggregate: true, DEC-128 §1) nén thành
    ĐÚNG MỘT ReviewItem cấp batch, source_rows chứa 53, message trung thực
    ("... chưa có giá nhập kế toán ... không phải lỗi dữ liệu").

Blocker    : KHÔNG có. Production đã đúng theo thiết kế từ trước (Golden #3
             xác nhận arithmetic; Golden #4 xác nhận thêm safe-failure/Review
             Queue). 0 dòng app/**, config/**, data/** sửa.

Production diff : +1 file test mới (6 test), +1 session log,
              +ghi trạng thái này. 0 dòng app/**/config/**/data/** sửa.
Golden Baseline (58 passed, 2 skipped) : KHÔNG đổi.
Golden #1 (BH62063) / Golden #3 (BH62439 dòng 52) : regression-safe, không đổi.
Golden #2 : KHÔNG đọc, KHÔNG sửa, KHÔNG reopen TASK-105C/105E.
Full pytest : 1041 passed, 11 skipped, 0 failed (trước: 1035 passed).
Validators  : structure/project_state/evidence/task_completion PASS;
              reference_integrity FAIL đúng 3 issue baseline TASK-REM-T06
              (không đổi). branch_authority_check → AUTHORITY_OK.

QUAN TRỌNG: Golden #4 PASS KHÔNG tuyên bố TASK-110 DONE. TASK-110 (toàn bộ
lineage R1-A2→R8) vẫn NOT DONE, budget EXHAUSTED_PRE_V4.1, CHECK-110-16 vẫn
BLOCKED (POST_MERGE_PRODUCTION_ACCEPTANCE) — không đổi bởi phiên này. Golden
#4 chỉ verify riêng detector missing_purchase_price đã hoạt động đúng trên
MỘT case thật, không phải toàn bộ Completion Gate của TASK-110.
```

Bằng chứng đầy đủ: `docs/sessions/S058-golden-4-safe-pending.md`.

## Trạng thái sau BATCH 50 REAL ORDERS (S059, 2026-08-29)

```text
BATCH 50 = BATCH_50_PASS (Session 1/2 — không cần Session 2)

Cohort   : 50 OrderID DUY NHẤT đầu tiên theo thứ tự xuất hiện trong
           tests/fixtures/golden/period_2026_01.xlsx (BH62063 .. BH62519,
           75 dòng thô, 2026-01-02..2026-01-10). Đông lạnh, tái lập được:
           tools/analysis/batch_50_real_orders.py (mới).

TRƯỚC/SAU (giống hệt nhau — KHÔNG repair):
  AUTO_SUCCESS = 1, REVIEW_QUEUE = 49, PENDING_NOT_QUEUED = 0, ERROR = 0,
  SILENTLY_DROPPED = 0
  AUTOMATION_RATE = 2,0%   ORDER_ACCOUNTING_RATE = 100,0%

Root cause chiếm ưu thế (49/50 đơn REVIEW_QUEUE): Missing.PurchasePrice —
thiếu giá vốn kế toán, CÙNG LỚP blocker khiến Golden #2 WAITING_REAL_DATA,
KHÔNG PHẢI code defect. Không đơn nào chạm EmployeeMapping/OrderInconsistency/
Duplicate/SourceClassification trong toàn file. 8 dòng có tín hiệu
Suspicious/Suspicious.ERP — xác minh tay: TẤT CẢ đúng dữ liệu thật (phụ kiện
tặng kèm giá 0, dòng SL=0, lợi nhuận ERP âm), không phải nhiễu do thiếu
non-product keyword.

Manual validation sample (6 đơn, 9 dòng cụ thể, gồm AUTO_SUCCESS/Qty>1+
Discount!=0/multi-line/Suspicious/Suspicious.ERP): CORRECT_AUTO=2,
CORRECT_PENDING=7, SILENT_ERROR=0, UNVERIFIABLE=0.
SILENT_ERROR_RATE = 0/9 = 0%.

Complete Blocking Set: RỖNG. Không silent wrong monetary result, không
silently dropped order, không crash, không sai order/line association,
không sai Review Queue accounting. Một quan sát đã kiểm tra và loại trừ:
KpiPurchasePrice/EligibleKpiProfit không có detector Review Queue riêng,
nhưng trên dữ liệu thật hiện có (confirmed_adjustments.jsonl LOADED rỗng),
mọi dòng KPI-Pending đều là tập con của dòng đã có trong
Missing.PurchasePrice — không phát sinh PENDING_NOT_QUEUED mới. Không mở
lại TASK-108B.

Production diff : +1 file mới (tools/analysis/batch_50_real_orders.py, công
              cụ đo lường, không phải business logic), +1 session log,
              +ghi trạng thái này. 0 dòng app/**, config/**, data/** sửa —
              hợp lệ theo mục 12 chỉ thị batch-50 ("zero legitimate code
              blockers -> zero production changes").
MANUAL_WORK_REDUCTION: NOT_YET_MEASURABLE — không có baseline thời gian xử
              lý tay cũ nào trong repo để so sánh; không bịa số.
Golden Baseline (58 passed, 2 skipped) : KHÔNG đổi.
Golden #1 (BH62063) / Golden #3+#4 (BH62439 dòng 52/53) : PASS, regression-safe.
Golden #2 : KHÔNG đọc, KHÔNG sửa, KHÔNG reopen TASK-105C/105E.
Full pytest : 1041 passed, 11 skipped, 0 failed (không đổi so với S058).
Validators  : structure/project_state/evidence/task_completion PASS;
              reference_integrity FAIL đúng 3 issue baseline TASK-REM-T06
              (REG-01, không đổi). branch_authority_check → AUTHORITY_OK.

QUAN TRỌNG: BATCH_50_PASS KHÔNG tuyên bố TASK-110 DONE và KHÔNG tuyên bố
90% tự động hoá đã đạt (2,0% hiện tại — trung thực, vì Phase 1 chưa có Price
Master, đúng dự kiến). Batch 50 chỉ đo hệ thống trên dữ liệu thật và xác
nhận: 0 silent error, 100% order accounting, 0 blocker hợp lệ cần sửa.
```

Bằng chứng đầy đủ: `docs/sessions/S059-batch-50-real-orders.md`,
`tools/analysis/batch_50_real_orders.py`.

## TASK-105E — Production Price Composition, Session 1 (S061, 2026-08-29)

Current-state pointer cho nhánh giá POST-cutover. Không supersede `DEC-154`;
nó **thực thi** `DEC-154` §7/§11 lần đầu tiên trên biên production, và không
đụng `CUTOVER_DATE`.

**Điều đã đổi thật.** Trước S061, `run_import_production()` chỉ nạp ba nguồn
của nhánh pre-cutover; mọi dòng `sale_date >= 2026-09-01` rơi thẳng vào
`PendingPriceProvider`, nên Reports History Reader V1 — dù đã review độc lập
và tích hợp (S060) — **chưa từng được production gọi một lần nào**. Từ S061,
seam production nạp thêm bằng chứng giá post-cutover và truyền một
`PostCutoverPriceComposition` vào `run_import()`.

```text
run_import_production()
  ├─ sale_date < 2026-09-01 → HistoricalConfirmedRegistry (P00)   — KHÔNG ĐỔI
  └─ sale_date >= 2026-09-01 → PostCutoverPriceComposition (TASK-105E)
        ├─ TASK-105D resolve identity (catalog + PP version + store view)
        ├─ TRACKING:<mã>        → Reports History Reader V1 (S060)
        ├─ PUBLIC_PURCHASE:<mã> → bảng giá Public Purchase (TASK-105B)
        └─ mọi kết cục khác     → Pending → Missing.PurchasePrice (TASK-110)
```

**Mặc định KHÔNG đổi.** `app/pipeline.py` nhận một tham số DI optional mới
`price_composition`, mặc định `None` = `PendingPriceProvider` như cũ
(`CHECK-105-04`). `price_provider` và `price_composition` loại trừ lẫn nhau —
truyền cả hai là `ValueError`, không phải một lựa chọn thầm lặng.

**`P01`/`P03` bị chặn có chủ đích.** `P03` đòi một absence ĐÃ XÁC ĐỊNH từ
nguồn vendor (`TASK-105C`), mà nguồn ấy vẫn `BLOCKED / NOT AUTHORIZED` — câu
hỏi chưa từng được đặt ra. "Chưa hỏi" không phải "đã hỏi và không có". Hệ
quả: identity `TRACKING` **không bao giờ** mượn giá Public Purchase trong
kiến trúc hiện tại, kể cả khi có `CrossSystemProductMapping` CONFIRMED — có
test khẳng định. `PUBLIC_PURCHASE_NO_VENDOR_PRICE` (`P09`) đã được định nghĩa
đầy đủ và tách khỏi `PUBLIC_PURCHASE_NO_TRACKING` (`P08`) theo `DEC-154` §10,
nhưng chưa có đường tới.

**`OWNER_DECISION_REQUIRED` (mở, không chặn).** Không artifact frozen nào đặt
Reports History Reader V1 vào một ô của bảng `P00–P11`; `DEC-154` §7 viết
trước khi reader tồn tại. S061 đặt nó làm nguồn `TRACKING` duy nhất được nối
theo luồng của chỉ thị mở phiên. Hôm nay lựa chọn ấy không quan sát được
(`P01` không có nguồn, `P03` bị chặn); nó trở nên quan sát được ngay khi
`TASK-105C` có nguồn thật — **retrigger trước khi `TASK-105C` được cấp phép**.

**Hai cutover, không gộp.** `CUTOVER_DATE = 2026-09-01` không đổi một byte.
Mốc dữ liệu Tracking `2026-08-29 19:35:37` (Firebase server time) là một
`datetime` có múi giờ; hai giá trị khác KIỂU và test khẳng định Python từ chối
so sánh trực tiếp chúng. Một đơn ngày `30/08/2026` vẫn đi nhánh lịch sử.

**Nguồn: ba trạng thái không gộp.**

```text
file không tồn tại    → nguồn CHƯA ĐƯỢC NỐI  → Pending có lý do riêng
file hỏng             → LỖI NẠP (raise)      → không sinh report giả
capture_status FAILED → LỖI CỨNG (INV-12)    → không bao giờ thành Pending
```

Hôm nay cả ba nguồn post-cutover đều VẮNG MẶT trên đĩa, nên hành vi production
là: post-cutover → `IDENTITY_SOURCES_UNAVAILABLE` → Pending → Review Queue.
Không crash, không đơn mất, không giá bịa.

**Kết quả đo.**

```text
Golden Baseline      : 58 passed, 2 skipped   — KHÔNG ĐỔI
Golden #1 BH62063    : 7.000.000 / EligibleKpiProfit 500.000 — KHÔNG ĐỔI
Golden #3 BH62439/52 : AccountingProfit 500.000 / EligibleKpiProfit 400.000 — KHÔNG ĐỔI
Golden #4 BH62439/53 : SAFE PENDING, Missing.PurchasePrice — KHÔNG ĐỔI
Batch 50 (01/2026)   : INPUT 50, AUTO 1, REVIEW_QUEUE 49,
                       PENDING_NOT_QUEUED 0, ERROR 0, SILENTLY_DROPPED 0,
                       AUTOMATION_RATE 2,0%, ORDER_ACCOUNTING_RATE 100,0%
                       — GIỐNG HỆT baseline S059
FULL pytest          : 1155 passed, 11 skipped, 0 failed (đo SAU commit)
                       (base 740f396: 1112 passed, 11 skipped — +43, 0 hồi quy)
Validators           : structure/project_state/evidence/task_completion PASS;
                       reference_integrity FAIL đúng 3 issue tiền tồn
                       TASK-REM-T06 (REG-01), không đổi
```

Batch 50 nằm trong tháng 01/2026, tức TRƯỚC mốc dữ liệu Tracking 29/08/2026;
`TASK-105E` không được phép và không hề làm nó tự động hơn. 49 đơn vẫn Pending
vì thiếu historical authority — đó KHÔNG phải regression.

**`WAITING_REAL_POST_CUTOVER_DATA`.** Repo không có đơn thật nào
`sale_date >= 2026-09-01` và không có file capture production nào. Wiring được
chứng minh bằng focused integration fixture chạy qua `run_import()` thật (43
test) cộng một lần chạy chính `run_import_production()` trên dữ liệu
post-cutover với nguồn giá đúng như trên đĩa hôm nay.

Trạng thái: `TASK-105E = IMPLEMENTED`, **NOT DONE** — Completion Gate chưa
soạn/chưa freeze, cần Independent Review (Session 2). Bằng chứng đầy đủ:
`docs/sessions/S061-task-105e-production-price-composition.md`,
`docs/tasks/TASK-105E-price-resolution-composition.md`.

## POST-CUTOVER PRODUCTION VALIDATION V1 (S062, 2026-08-30)

Bộ kiểm định production hậu-cutover. Không phải task kiến trúc mới, không
supersede `TASK-105E`/`DEC-154`; nó là công cụ ĐO composition đã tích hợp ở
S061, chạy trên chính seam production.

```text
VALIDATOR_IMPLEMENTATION_PASS    = YES
PRODUCTION_POST_CUTOVER_ACCEPTED = NO
Trạng thái vận hành              = WAITING_REAL_POST_CUTOVER_DATA
```

**Vì sao `WAITING_REAL_POST_CUTOVER_DATA`.** Repo không có đơn bán thật nào
`sale_date >= 2026-09-01`; hai kỳ nghiệp vụ thật hiện có là 01/2026 (254 đơn)
và 06/2026 (146 đơn), đều PRE-cutover — hôm nay là 2026-08-30, mốc Product
Identity còn chưa tới. Bốn nguồn giá post-cutover trên đĩa đều
`SOURCE_NOT_CAPTURED`. Đây là trạng thái vận hành mong đợi, KHÔNG phải một
thất bại quy trình, và KHÔNG được nhảy sang `PRODUCTION_POST_CUTOVER_ACCEPTED`
bằng fixture.

**Công cụ.** `tools/analysis/validate_post_cutover.py` (mới) — một lệnh:

```text
python3 tools/analysis/validate_post_cutover.py \
    --sales <so_chi_tiet_ban_hang.xlsx> --output <dir>
```

Nó đông lạnh cohort (N `OrderID` DUY NHẤT đầu tiên theo thứ tự xuất hiện, chỉ
đơn hoàn toàn hậu-cutover; `MIXED`/`UNDATED` loại ra nhưng ĐẾM RIÊNG), đông
lạnh mọi nguồn giá ĐÚNG MỘT LẦN qua loader production kèm `sha256`, chạy
`app.composition.run_import_production()` THẬT, rồi ĐỌC kết quả. 0 dòng
business logic mới: không tính giá, không resolve identity, không dựng lại
engine KPI.

**Kết quả trên dữ liệu THẬT hiện có.** Cohort hậu-cutover rỗng ở cả hai file,
nhưng bộ phát hiện silent error vẫn chạy trên toàn bộ dòng — đó chính là phép
kiểm §14 (Batch 50 không được tự động hoá bằng dữ liệu Tracking 08/2026):

```text
period_2026_01.xlsx : 254 đơn, LINES_CHECKED_FOR_SILENT_ERRORS = 351,
                      SILENT_ERROR_FINDINGS = 0
period_2026_06.xlsx : 146 đơn, LINES_CHECKED_FOR_SILENT_ERRORS = 180,
                      SILENT_ERROR_FINDINGS = 0
```

531 dòng thật: không rò thẩm quyền qua mốc cutover theo cả hai chiều, không
sai số học `AccountingProfit`/`EligibleKpiProfit`, không dòng nào mang giá khi
input còn Pending, không nhãn nguồn lạ.

**Hai lớp silent error, không gộp.** (A) 26 code mâu thuẫn cấu trúc máy chấm
được — mỗi code có một test làm nó đỏ, cộng một kiểm soát âm, cộng một meta-test
quét mã nguồn công cụ để chính bất biến "không code nào thiếu test" được kiểm
bằng máy. (B) Kiểm
tay: `manual_sample.csv` với cột `outcome` để trống; chừng nào chưa ai điền,
`SILENT_ERROR_RATE = NOT_YET_MEASURED`, **không phải `0%`**. Verdict đã điền
không bao giờ bị một lần chạy lại ghi đè.

**Giới hạn thẩm quyền.** Công cụ không phân biệt được sổ bán hàng THẬT với một
fixture cùng hình dạng, nên trạng thái cao nhất nó in ra là
`ELIGIBLE_FOR_PRODUCTION_ACCEPTANCE_REVIEW`. `PRODUCTION_POST_CUTOVER_ACCEPTED`
là quyết định governance, ghi ở chính file này, và đòi bằng chứng về tính thật
của dữ liệu mà chỉ con người mới cấp được.

**Kết quả đo.**

```text
Golden Baseline      : 58 passed, 2 skipped   — KHÔNG ĐỔI
Golden #1 / #3 / #4  : 16 passed              — KHÔNG ĐỔI
TASK-110 / TASK-105E / Tracking Reader / KPI engine : 146 passed — KHÔNG ĐỔI
Batch 50 (01/2026)   : INPUT 50, AUTO 1, REVIEW_QUEUE 49,
                       PENDING_NOT_QUEUED 0, ERROR 0, SILENTLY_DROPPED 0,
                       AUTOMATION_RATE 2,0%, ORDER_ACCOUNTING_RATE 100,0%
                       — GIỐNG HỆT baseline S059/S061
Focused              : tests/test_post_cutover_validation.py — 58 passed
FULL pytest          : 1213 passed, 11 skipped, 0 failed
                       (base b1eeadc: 1155 passed, 11 skipped — +58, 0 hồi quy)
Validators           : structure/project_state/evidence/task_completion PASS;
                       reference_integrity FAIL đúng 3 issue tiền tồn
                       TASK-REM-T06 (REG-01), không đổi

Production diff : +1 công cụ đo lường (tools/analysis/validate_post_cutover.py),
              +1 file test mới (58 test), +1 session log, +ghi trạng thái này.
              0 dòng app/**, config/**, data/** sửa. Repo Tracking KHÔNG bị sửa.
MANUAL_WORK_REDUCTION: NOT_YET_MEASURABLE — không có baseline thời gian xử lý
              tay cũ nào trong repo để so sánh; không bịa số.
```

**QUAN TRỌNG.** Phiên này KHÔNG tuyên `TASK-105E = DONE` (vẫn `IMPLEMENTED`,
Completion Gate chưa soạn/chưa freeze, cần Independent Review), KHÔNG tuyên
`TASK-110 = DONE`, KHÔNG đóng `OWNER_DECISION_REQUIRED` mở từ S061 (vị trí của
Reports History Reader V1 trong bảng `P00–P11`), và KHÔNG mở `TASK-105C`.
`P01`/`P03` vẫn bị chặn có chủ đích; validator có detector
`VENDOR_FALLBACK_REACHED_WHILE_BLOCKED` cho ngày nhánh ấy vô tình mở ra.

Bằng chứng đầy đủ: `docs/sessions/S062-post-cutover-production-validation.md`,
`tools/analysis/validate_post_cutover.py`,
`tests/test_post_cutover_validation.py`.

## IDENTITY SOURCE ACQUISITION REPAIR — Tracking catalog (S063, 2026-08-30)

Sửa một nửa ranh giới bị bỏ dở, không phải một task kiến trúc mới. `TASK-105D`
§4.1 vẽ hai phía (`tools/tracking/` ghi file capture bất biến, `app/modules/`
chỉ đọc); `TASK-105E` xây phía ĐỌC; phía GHI cho `TrackingCatalogSnapshot`
chưa bao giờ được xây.

```text
ACQUISITION_REPAIR_IMPLEMENTED  = YES
ROOT_CAUSE_CONFIRMED            = YES
REAL_TRACKING_CAPTURE_EXECUTED  = NO
Trạng thái vận hành             = WAITING_REAL_TRACKING_CATALOG_CAPTURE
```

**Root cause của `BH73804`.** `PostCutoverPriceComposition._resolve_eligible()`
(`app/modules/pricing/resolution/composition.py:345-374`) chặn ở một cổng
**AND** trên ba nguồn; `tracking_catalog` là `None` vì
`data/tracking_catalog/capture.json` không tồn tại và **không công cụ nào
trong repo ghi được file đó**. `tools/tracking/capture_purchase_price_history.py`
chỉ chụp `purchase_price_baseline` + `purchase_price_history`.

**Repair.** `tools/tracking/capture_tracking_catalog.py` — READ-ONLY, đọc đúng
hai nhánh `board` và `alias` theo bằng chứng đã audit (`DEC-147` §4, `S024`
C-01), dùng lại nguyên `_http_fetcher`/`write_capture`/`TOKEN_ENV_VAR` của
công cụ chị em nên cả repo có đúng một đường mạng và một đường credential.
Công cụ cũ **0 dòng thay đổi**. `inv`/`phist`/`backup` KHÔNG BAO GIỜ được hỏi
tới; `board` trả cả cây nhưng chỉ danh sách trắng `("name", "alt")` được ghi
ra, nên `p/<NCC>`, `tp/ton`, `tp/chot`, `_c` không vào artifact.

**Fail closed.** `CaptureStatus` giữ nguyên enum ĐÓNG `{COMPLETE, FAILED}`
(`INV-12` treo lên đúng nó); bốn kết cục của chỉ thị được phân biệt bằng tiền
tố máy đọc được trong `failure_reason`: `SOURCE_UNAVAILABLE:` /
`MALFORMED_SOURCE:` / `EMPTY_SOURCE_NOT_ASSERTABLE:`. Một `board` rỗng KHÔNG
được ghi thành danh mục rỗng — RTDB trả cùng một `null` cho "nhánh không tồn
tại" và "nhánh rỗng", nên emptiness không khẳng định được từ dây.

**Public Purchase — không phải implementation gap.**
`PublicPurchaseSourceVersion` là một nguồn **file được publish**
(`data/public_purchase/source_version.yaml` → `PublicPurchaseSourceLoader.load()`,
`D-01`/`OR-01`), không phải một lần chụp mạng. Cơ chế đã tồn tại; absence hôm
nay nghĩa là chưa ai publish version đầu tiên. Không dựng capture tool, không
fabricate dữ liệu PP.

**Đính chính tiền đề.** Tracking catalog là blocker đã được trace, nhưng cổng
ở `composition.py:349` là AND — `BH73804` chỉ thoát
`IDENTITY_SOURCES_UNAVAILABLE` khi **cả** catalog **và** Public Purchase có
mặt.

**Điều gì xảy ra khi có capture thật.** Phép dò trên chính resolver production:
`product_raw = "Máy Giặt LG T2109NT1G"` với catalog có dòng `T2109NT1G` cho
`PendingProduct(ONLY_SIMILARITY_EVIDENCE)`, không phải `Resolved`; chỉ
`product_raw = "T2109NT1G"` mới cho `TRACKING:T2109NT1G`. Đây là hành vi ĐÚNG
theo `INV-01`/`D-04` (exact-match-only; `extractCode()` là tiền lệ đã bỏ).
Nghĩa là `BH73804` vẫn vào Review Queue, nhưng đổi chất: từ "chưa nối được
nguồn" thành "đã hỏi cả bốn nguồn, chỉ có bằng chứng similarity" — đường đi
tiếp là **một `confirmation_action` của người dùng Reports**, không phải một
thay đổi mã. Finding kế tiếp; S063 KHÔNG sửa trước, KHÔNG thêm fuzzy mapping,
KHÔNG special-case `T2109NT1G`.

```text
Focused        tests/test_tracking_catalog_capture.py   34 passed
Product Identity / TASK-105D                          218 passed
TASK-105E                                              43 passed
Post-Cutover Validator                                 62 passed
Golden Baseline                            58 passed, 2 skipped
Golden #1/#3/#4                                        16 passed
Batch 50                                                5 passed
Toàn bộ suite                          1251 passed, 11 skipped
Sửa: +1 file tools/, +1 file tests/, +1 doc session, +1 mục progress.
     0 dòng app/**, config/**, data/** sửa. Repo Tracking KHÔNG bị sửa.
```

**QUAN TRỌNG.** Phiên này KHÔNG tuyên `TASK-105E = DONE`, KHÔNG đóng bất kỳ
`OWNER_DECISION_REQUIRED` nào, KHÔNG chạy capture thật (không có credential),
KHÔNG merge, KHÔNG deploy. Bốn nguồn giá post-cutover trên đĩa vẫn
`SOURCE_NOT_CAPTURED`.

Bằng chứng đầy đủ: `docs/sessions/S063-tracking-catalog-acquisition-repair.md`,
`tools/tracking/capture_tracking_catalog.py`,
`tests/test_tracking_catalog_capture.py`.

## REPORTS → TRACKING DATA CONTRACT V1 INTEGRATION (S064, 2026-08-30)

Sửa transport của chính hai công cụ capture ở trên, không phải một task mới.
Reports KHÔNG còn đọc Firebase RTDB trực tiếp.

```text
CONTRACT_CLIENT_IMPLEMENTED      = YES
FIREBASE_DIRECT_PATH_RETIRED     = YES
REAL_TRACKING_CAPTURE_EXECUTED   = NO   (thiếu secret + egress bị chặn)
BH73804_REAL_TRACE_EXECUTED      = NO
Verdict                          = IMPLEMENTATION_PASS_RUNTIME_PENDING
```

**Vì sao.** Đường cũ `<database_url>/<node>.json?auth=<TRACKING_RTDB_TOKEN>`
đòi Firebase Auth/App Check — thứ Reports không có và không nên có; nó đã hỏng
trên production. Tracking đã phát hành Data Contract V1 và merge vào main của
họ; Reports chuyển sang đúng hợp đồng đó.

**Điểm sửa.** Đúng MỘT hàm: `_http_fetcher()` trong
`tools/tracking/capture_purchase_price_history.py` — vốn đã là đường mạng duy
nhất của cả repo (`capture_tracking_catalog.py` import lại chính nó), nên cả
hai công cụ đổi nguồn cùng lúc, không có client thứ hai.

```text
GET <source_url>/api/xuat/<node>      Header: X-Report-Key: <TRACKING_REPORT_API_KEY>
ALLOWED_NODES = {board, alias, purchase_price_baseline, purchase_price_history}
```

`--database-url` → `--source-url` (không giữ alias: tên cũ nói sai sự thật cho
người vận hành; không caller nào ngoài test dùng nó). `TRACKING_RTDB_TOKEN`
XOÁ khỏi mã. `--source-system-ref` mặc định → `tracking/api/xuat`. Thêm kiểm
`Content-Type: application/json` (HTML 200 là cách im lặng nhất để rác thành
"capture thành công"). **Không có fallback Firebase** — hợp đồng lỗi thì
capture `FAILED`, vì hai đường nguồn song song đúng là thứ `INV-12` chặn.

**Không đổi:** `_rows_from_board()`, `_alias_map_from()`,
`canonical_content_hash()`, `write_capture()` (`INV-11`), toàn bộ
`app/modules/**`. Hợp đồng trả `board` đã chiếu sẵn `{name, alt[]}` với `alt`
là mảng — đúng hình dạng tầng envelope đã đọc từ S063. Ranh giới `ADR-101`
nguyên vẹn: mạng chỉ ở `tools/tracking/**`.

**Artifact bất biến.** Lần thử Firebase/App Check hỏng KHÔNG bị viết đè thành
COMPLETE; `write_capture()` vẫn từ chối ghi đè và có test khoá điều đó. Lần
capture mới = file mới, `capture_id` mới. (Artifact FAILED của phiên trước
không nằm trong repo — không xoá gì, cũng không bịa một cái để "có bằng chứng".)

**BH73804 — preflight, KHÔNG phải real trace.** Không capture thật, không file
doanh số thật trong container, nên `validate_post_cutover.py` không chạy được.
Chạy được là câu hỏi offline, qua `ProductIdentityResolver` thật:
`"Máy Giặt LG T2109NT1G"` → `PendingProduct(ONLY_SIMILARITY_EVIDENCE)`, 1
candidate; `"T2109NT1G"` → `Resolved TRACKING:T2109NT1G`. XÁC NHẬN dự đoán của
S063, và nói thêm: kết cục phụ thuộc `board/<mã>/name` THẬT — chỉ biết sau một
capture thật. Đây là TRUTHFUL PENDING; KHÔNG thêm regex/fuzzy/AI matching để
`BH73804` AUTO.

**Đính chính.** Cơ chế confirmation của `TASK-105D` tồn tại ở mức hàm
(`cli.confirm`, `cli.callable_surfaces()`) và `build_parser()` có đủ tham số,
nhưng **không có `main()` nối hai thứ đó** — `python3 -m
app.modules.product.identity.cli` không chạy được. Ghi ra làm finding, KHÔNG
lấp trong phiên này (ngoài Scope Lock của một repair transport).

**Public Purchase.** `PUBLIC_PURCHASE_VERSION_REQUIRED`, chặn ở
`composition.py:349` (cổng AND). `data/public_purchase/source_version.yaml`
không tồn tại. Kể cả khi capture Tracking thật thành công, `BH73804` vẫn dừng
ở `IDENTITY_SOURCES_UNAVAILABLE` chừng nào PP còn vắng. KHÔNG nhầm blocker này
với Tracking transport — transport là PASS.

```text
Focused  tests/test_tracking_contract_client.py (mới)        21 passed
Tracking capture + 105E + History Reader + Batch 50
  + Post-Cutover Validator                                  211 passed
Toàn bộ suite                                 1273 passed, 11 skipped
Production LOC chạm tới: 72 (+50/−22, bỏ docstring/comment) trên trần 100
Sửa: 2 file tools/, +1 file tests/, 1 file tests/ cập nhật, +1 doc session,
     +1 mục progress. 0 dòng app/**, config/**, data/**.
```

**QUAN TRỌNG.** Phiên này KHÔNG chạy capture thật, KHÔNG tuyên Production
Acceptance, KHÔNG merge, KHÔNG deploy. Bốn nguồn giá post-cutover trên đĩa vẫn
`SOURCE_NOT_CAPTURED`. Egress tới `price.tinphatcrm.com` bị network policy của
môi trường phiên chặn ở tầng CONNECT (`http=000`, **không phải** `403` của hợp
đồng) — phiên này chưa từng chạm tới endpoint production.

Bằng chứng đầy đủ: `docs/sessions/S064-reports-tracking-contract-integration.md`,
`tools/tracking/capture_purchase_price_history.py`,
`tests/test_tracking_contract_client.py`.

## RUNTIME REPAIR — 403 Forbidden trên client contract thật (S065, 2026-08-30)

Tiếp tục `S064`, cùng task lineage, không mở task mới. Operator chạy thật
trên Mac (`TRACKING_REPORT_API_KEY` đã nạp) cung cấp evidence bác bỏ ba giả
thuyết: `curl -H "X-Report-Key: $KEY" .../api/xuat/board` → `HTTP 200`
(secret đúng, network đúng); `capture_tracking_catalog.py` cùng secret/cùng
máy → `HTTP 403 Forbidden`.

```text
ROOT_CAUSE          = User-Agent mặc định + thiếu Accept (WAF/Cloudflare)
RULED_OUT           = MISSING_API_KEY, WRONG_SECRET, EGRESS_BLOCKED (curl 200 bác cả ba)
INVESTIGATED_AND_RULED_OUT = header case (X-Report-Key → X-report-key)
Verdict              = RUNTIME_REPAIR_READY
```

**Root cause.** `urllib` mặc định tự xưng `User-Agent: Python-urllib/
<version>` và không gửi `Accept` — đúng chữ ký thư viện HTTP mà một
WAF/Cloudflare phía trước hợp đồng chặn; `curl` (UA riêng + `Accept: */*`)
qua lọt với cùng secret. Sửa: đặt tường minh `CLIENT_USER_AGENT =
"TinPhat-Reports-TrackingClient/1.0"` + `Accept: */*` trong `_http_fetcher()`
— đúng MỘT hàm, dùng chung bởi cả hai công cụ capture.

**Một giả thuyết đã điều tra và loại trừ bằng thực nghiệm, ghi lại để không
lặp lại.** Nghi vấn đầu (đúng hướng checklist "case normalization"):
`Request(url, headers={...})` chạy `add_header()` → `key.capitalize()` →
`X-Report-Key` thành `X-report-key`. Trace sâu hơn một tầng lộ ra
`do_open()`: `headers = {name.title(): val for name, val in headers.items()}`
— MỌI header bị `.title()`-hoá lại ngay trước khi gửi, bất kể case đặt lúc
dựng `Request`; `"X-report-key".title() == "X-Report-Key"`. Case luôn tự
đúng trên dây — xác nhận bằng một `http.server` cục bộ đọc lại chuỗi header
thô thật nhận được, cho cả hai đường dựng `Request`.

**Repair xác nhận bằng CLI thật (subprocess), không mock.** Không có egress
thật tới `price.tinphatcrm.com` trong môi trường phiên (như `S064`); repair
được exercise qua `python3 -m tools.tracking.capture_tracking_catalog` thật
nhắm vào một server local đúng hình dạng hợp đồng — mọi lớp (argparse, env
var, `_http_fetcher`, `urlopen`) đều chạy thật. Kết quả: `COMPLETE`, header
nhận được đúng `User-Agent: TinPhat-Reports-TrackingClient/1.0` + `Accept:
*/*` + `X-Report-Key`. Đây KHÔNG phải bằng chứng production.

```text
Focused  tests/test_tracking_contract_client.py                23 passed (21 cũ + 2 mới)
Tracking capture + 105E + History Reader + Batch 50
  + Post-Cutover Validator                                    211 passed
Toàn bộ suite                                   1275 passed, 11 skipped
Additional production LOC: +8/−1 = 9 dòng (cộng dồn 81/100 với S064)
```

Test mới `test_the_client_sends_a_non_default_user_agent_and_an_accept_header`
đã XÁC NHẬN bắt được lỗi: revert tạm phần header về bản không có `User-Agent`/
`Accept` tường minh → FAIL đúng thông điệp trỏ vào `Python-urllib`; áp lại
repair → PASS.

**Failed artifacts.** `data/tracking_catalog/capture*.json` không nằm trong
checkout của phiên (sống trên đĩa operator, không commit) — không có gì bị
overwrite/delete. `write_capture()` (`INV-11`, không đổi) vẫn từ chối ghi đè.

**QUAN TRỌNG.** Local repair hoàn tất, có test thật. KHÔNG tuyên production
PASS — operator phải chạy lại lệnh capture thật trên máy có secret + egress,
ghi ra tên artifact mới (`capture_contract_v1_prod_2.json`, không ghi đè lần
`_prod.json` đã `FAILED` với `403`).

Bằng chứng đầy đủ: `docs/sessions/S065-runtime-repair-403-user-agent.md`,
`tools/tracking/capture_purchase_price_history.py`,
`tests/test_tracking_contract_client.py`.

## PUBLIC PURCHASE TRACE — REAL_SOURCE_MISSING (S066, 2026-08-30)

Tiếp tục cùng task lineage (`S064`→`S065`→`S066`), không mở task mới. Phiên
TRACE + OPERATION thuần — **0 dòng production code sửa**.

```text
CLASSIFICATION   = CASE B — REAL_SOURCE_MISSING
IMPLEMENTATION   = ĐẦY ĐỦ, FROZEN, INTEGRATED (TASK-105B/105D/105E)
BH73804          = BLOCKED_AT_GATE (IDENTITY_SOURCES_UNAVAILABLE)
```

**Trace xác nhận bằng code, không suy đoán.** Public Purchase là một nguồn
giá công khai **độc lập với Tracking** (`DEC-156` §1, `D-01`/`OR-01`
APPROVED), dữ liệu do **chủ dự án cung cấp trực tiếp** (`TASK-108B` §38.4:
`prices.yaml` "bảng giá chủ dự án cấp"; `DATA-CONTRACT` §3.3: publish là
quyền `PUBLIC_PURCHASE_SOURCE_PUBLISH`, role `ADMIN`) — không phải một hệ
thống Reports tự capture được. Toàn bộ implementation (loader strict
`INV-02`/`04`/`05`/`06`/`09`, schema `E-A/E-B/E-C`, composition wiring) đã
FROZEN và INTEGRATED. Blocker DUY NHẤT là dữ liệu thật chưa từng được cấp —
xác nhận lại bằng chính lịch sử `PROJECT_PROGRESS.md`/`PROJECT_DECISIONS.md`
("NEXT AUTHORIZED ACTION = chờ Owner cấp bảng giá production thật", `DEC-156`
§12), không phải phát hiện mới của phiên này.

**Phát hiện đáng ghi lại (phản trực giác).**
`ProductIdentityResolver.__init__` nhận `pp_version` **không** `Optional` —
Public Purchase là input bắt buộc để RESOLVE IDENTITY (không riêng định giá),
vì candidate-discovery phải loại trừ khả năng một raw string là mã Public
Purchase trước khi khẳng định nó là `TRACKING:<mã>`. Vì vậy dù giá cuối cùng
của một identity `TRACKING:<mã>` (như `T2109NT1G`) sẽ đến TỪ
`TrackingHistoryPriceProvider` — KHÔNG BAO GIỜ từ Public Purchase (P03
fallback bị chặn có chủ đích, `VENDOR_SOURCE_NOT_AUTHORIZED` — `TASK-105C`
chưa cấp phép) — thiếu Public Purchase vẫn chặn TOÀN BỘ composition ở cổng
AND của `_resolve_eligible()`. Và `INV-02` cấm `products`/`prices` rỗng, nên
KHÔNG có "version tối giản vô hại" nào khả dĩ để mở gate mà không mang dữ
liệu thật — không có đường lách nào trong kiến trúc hiện tại.

**BH73804 không real/preflight thêm được.** Public Purchase gate chặn trước
khi chạm dòng nào — dù real Tracking capture (`capture_contract_v1_prod_2.json`
×2 trên Mac, `S065`) đã có. Cũng không có sales file thật
(`So_chi_tiet_ban_hang (4).xlsx`) trong checkout của phiên này — không
fabricate fixture thay thế rồi gọi đó là real validation.

**Owner action cần:** (1) cung cấp ≥1 dòng Public Purchase thật (product +
price, schema tại session doc §1.D); (2) thực hiện/uỷ quyền publish
(`ADMIN`, `DEC-124`) vào `data/public_purchase/source_version.yaml`,
`version_id = PP-<YYYYMMDD>-<NN>`. Không phải implementation failure.

Final SHA không đổi: `b0f83d6680629823915cb44050f701b76e2d1d06` + commit tài
liệu của phiên này.

Bằng chứng đầy đủ: `docs/sessions/S066-public-purchase-trace-real-source-missing.md`.

## PUBLIC PURCHASE AUTHORITY CORRECTION (S067, 2026-08-30)

Tiếp tục cùng task lineage (`S064`→`S065`→`S066`→`S067`), không mở task mới.
Phiên TRACE → DESIGN → IMPLEMENT → TEST. Quyết định: `DEC-165` /
`docs/adr/ADR-107-public-purchase-authority-in-tracking.md`.

```text
CLASSIFICATION   = CASE A — REUSE (purchase_price_history ĐÃ là lịch sử PP)
AUTHORITY        = TRACKING (single source of truth cho Public Purchase)
S066 CASE B      = SUPERSEDED (đúng với giả định cũ, sai với nghiệp vụ thật)
```

**Owner đã chốt nghiệp vụ thật, và nó khác giả định trong `DEC-156`.** Public
Purchase KHÔNG phải một nguồn giá độc lập do chủ dự án cấp bằng YAML cho
Reports. Nó là **giá Owner tự quản trong Tracking**, có quyền đặt cao hơn giá
vốn thật để nhân viên không tự hạ giá bán, và là giá chuẩn tính KPI.

**Trace Tracking (bằng chứng, không suy đoán).** Chỉ thị cấm mặc định
`inv.cong`/`tp.ton` là Public Purchase chỉ vì tên nghe hợp; đã trace đủ chuỗi
Owner UI → handler → state → Firebase → board → giá nhân viên nhìn thấy:

```text
inv.gia   = giá vốn tồn THỰC TẾ (Y)  — invRecalcAvg(), bình quân gia quyền
                                        Ở LẠI tab Tồn kho, không rời Tracking
inv.cong  = PUBLIC PURCHASE           — invSetGia(kind="cong") Owner sửa tay
inv.congTay                           — cờ khoá: từ đó Y KHÔNG ghi đè PP nữa
   -> invSyncPart()  u[k+"/tp/ton"] = cong[...]     (CHỈ giá công khai)
   -> savePpHist()   purchase_price_history/<mã>/<pushId>
                     { prev, next, t=ServerValue.TIMESTAMP, ta:"SERVER", by, src }
```

Chú thích nguyên văn trong `public/index.html` (Tracking): *"Chỉ GIÁ CÔNG KHAI
đi sang cột Tồn/Min. Giá thực nhập trung bình ở lại tab Tồn kho và tab Giá trị
tồn kho."*

**Hệ quả: `purchase_price_baseline` + `purchase_price_history` — hai nhánh
Reports ĐÃ đọc qua Data Contract — chính là lịch sử effective-dated của Public
Purchase**, không phải của `Y`. `TrackingPriceHistoryReader` (History Reader
V1, `S060`) đã dựng lại đúng đại lượng cần dựng từ trước. Không cần nhánh
history mới, không cần baseline thứ hai, không cần migration, không cần sửa
Rules, không cần mở rộng allowlist.

**Sửa kiến trúc phía Reports (`ADR-107` / `DEC-165`).** Finding của `S066` —
`ProductIdentityResolver` nhận `pp_version` không `Optional` — nay được xử lý
đúng bản chất: nó ghép hai trách nhiệm rời nhau vào một cổng AND.

```text
TRƯỚC: catalog Tracking AND catalog PP YAML AND store  -> mới resolve identity
SAU  : catalog Tracking AND store                      -> đủ cho TRACKING:<mã>
```

`data/public_purchase/source_version.yaml` chuyển sang tư cách **LEGACY
SUPPORTED FORMAT** — loader, schema `E-A/E-B/E-C`, invariant `INV-02`/`04`…`09`
và namespace identity `PUBLIC_PURCHASE` giữ nguyên, KHÔNG xoá; chỉ mất tư cách
*production source authority*. `pp_version=None` ghi vào provenance là
`pp_version_id=None` — "chưa nối", không phải "rỗng".

**Không có fallback sang `Y`.** Public Purchase không xác định được tại ngày
bán → `Pending` → Review Queue canonical (`TASK-110`). `Y` cũng không có đường
nào tới Reports: hợp đồng chiếu `board` xuống đúng `{name, alt}`, allowlist
không có nhánh `inv`.

**Production LOC:** Tracking `0`; Reports `78+/8-` trong `app/` (trong đó ~57
dòng là docstring/chú thích; phần thực thi ~21+/8-); Rules `0`;
migration/cutover `0`. Dưới ngưỡng `400` — không `CHANGE_BUDGET_EXCEEDED`.

**Tests.** Reports `1286 passed, 11 skipped, 0 failed` (trước `1275` — delta
đúng 11 test mới, `tests/test_public_purchase_authority.py`). Tracking
`57 bộ · 2461 đạt · 0 hỏng · 2 bỏ qua` (trước `56 bộ · 2434 đạt` — delta đúng
27 bài mới, `kiem/gia-cong-khai-tham-quyen.js`), `npm run build` PASS.

**BH73804 vẫn chưa AUTO được, và đó là câu trả lời đúng.** Cổng Public
Purchase YAML đã gỡ, nhưng checkout này không có capture production nào
(`data/tracking_catalog/`, `data/purchase_price_history/` đều vắng) và không
có file bán hàng thật. Không fabricate fixture rồi gọi đó là real validation.
Điều kiện còn lại là **vận hành**, không phải implementation — xem "Session
tiếp theo".

**Nợ kỹ thuật ghi nhận (không sửa trong phiên này).** Hai đường phụ ghi
`board/<mã>/tp/ton` mà KHÔNG sinh mốc lịch sử: `mergePaths()` (gộp mã — chỉ
lấp ô đang trống) và nhập bảng giá từ Excel. Khoá chuỗi `prev` của reader bắt
đúng loại lỗ hổng này và trả `Pending`, nên nó **không** sinh số sai — chỉ
giảm độ phủ.

## BETA OPERATOR UI + FEEDBACK (S069, 2026-09-01)

Nhánh `s069/beta-operator-ui`, baseline
`3f92c953b4c6d12834d4d3a0c611a7b27e7e0061`. Chi tiết đầy đủ:
`docs/sessions/S069-beta-operator-ui-feedback.md`.

**Phát hiện trước khi sửa.** Audit `app/owner_usability.py` (Owner launcher
V1) cho thấy nó chưa từng chọn/nối capture `data/tracking_inv_map/` —
nghĩa là double-click `Open Reports.command` trước S069 vẫn ra baseline CŨ
(`AUTO=0/58`) thay vì baseline `22 AUTO/36 Review` mà S068 đã accept. Đây là
gap chặn Exit Criteria "AUTO/Review hiển thị đúng", được sửa trong S069
bằng cách nối đúng tham số `tracking_inv_map` (đã tồn tại từ S068,
`demo.run_demo` đã hỗ trợ tuỳ chọn) vào launcher — không phải business rule
mới, không tăng AUTO ngoài baseline đã accepted.

**Thay đổi chính.** `ReportSummary` thêm `error_count` +
`review_reason_counts` (đếm lại đúng dữ liệu authoritative đã tính cho
Excel, không phân loại lại). Owner launcher thêm data readiness, Result
summary đầy đủ, Review summary (nhãn hiển thị qua `app/beta_presentation.py`,
reason gốc giữ nguyên), nút "Mở báo cáo Excel" thường trực
(`owner_usability.open_report_file`, tách để test được), nút "Gửi phản
hồi". `app/beta_feedback.py` + `app/beta_telemetry.py` (mới): JSONL
append-only local tại `data/beta_feedback/` (đã thêm `.gitignore`), schema
cố định, không PII, không secret, không payload Tracking.

**Real Beta Smoke — evidence đã refresh, không phải regression.** Lần chạy
đầu qua launcher đã nối cho `AUTO=0/58` thay vì `22/36`: trace ra
`data/captures/PPH-20260831T080038Z.json` cục bộ đã STALE so với capture
lúc S068 accept (không còn trên máy này). Dùng lại đúng
`tools/tracking/capture_purchase_price_history.py` +
`tools/tracking/capture_inv_map.py` (cơ chế đã accepted, không code mới) để
refresh cả hai capture → rerun ra đúng `58 đơn/83 dòng/22 AUTO/36
Review/100% accounting/0 dropped` — khớp tuyệt đối baseline S068 đã accept.

**Regression.** `1373 passed, 11 skipped` (từ `1349 passed, 11 skipped`;
+24 test mới, không skip nào đổi).

**Giới hạn đã biết, không che giấu.** `owner_launcher.py` dùng Tkinter
thật; môi trường session này không có interpreter nào vừa có Tkinter vừa có
dependency dự án cùng lúc, nên phần widget-wiring chỉ được xác nhận bằng
`py_compile` + review thủ công (đúng giới hạn đã tồn tại từ bản gốc trước
S069, bản đó cũng chưa từng có test). Toàn bộ logic thuần (feedback,
telemetry, presentation, capture wiring, open-file adapter) đã unit test
đầy đủ, độc lập Tkinter.

**Known deferred findings không đổi**: A1 Product Identity Discovery Gap,
13 sản phẩm Pending thật, 6 dòng service/cost, PP coverage, AUTO rate
target, fuzzy/substring mapping, generic MDM, web frontend/backend.

**S069_GATE_RESULT = PASS.** Chưa merge canonical trong phiên này; đã push
`s069/beta-operator-ui` lên origin, chờ independent review trước
integration.

## Governance V4.1 — Trạng Thái Adoption

```
V4.1 = POLICY_ADOPTED   (2026-08-27, TASK-V4-ADOPTION, session V4.1-0)
V4.1 = FULLY_ENFORCED   (2026-08-27, sau Freeze Finalization + Controlled
                        Integration của TASK-GOLDEN-BASELINE-001, session
                        "FREEZE FINALIZATION + CONTROLLED INTEGRATION")
```

**`TASK-GOLDEN-BASELINE-001` đã FROZEN, MERGED, DONE (2026-08-27).** Golden
Baseline chạy trên hai kỳ nghiệp vụ thật của Tín Phát (01.2026 = 254 đơn,
06.2026 = 146 đơn), fixture đã ẩn danh theo Owner Decision `OD-GB-1 = A + A1`,
một lệnh chạy: `python3 -m pytest tests/test_golden_baseline.py -q`. Sau
Repair Cycle #1 (`GB-IR-01`, đóng bằng `54a575d`), Independent Review #2 đã
**PASS — ELIGIBLE_FOR_FREEZE** tại reviewed SHA
`85210691702550d83c0fd42fe816be8ca9dde889` (review verdict record
`94b2513d1894dbd58f3b08656e3c7412be191df5`), 0 blocking finding — ghi tại
`docs/reviews/TASK-GOLDEN-BASELINE-001-INDEPENDENT-REVIEW-2.md`. Freeze
Finalization ghi tại `DEC-142` (`PROJECT/PROJECT_DECISIONS.md`), freeze SHA
`41813535c9d32a7f72782011a5f30ad2c38924f9`. Controlled Integration qua nhánh
trung gian `integration/v4-1-golden-baseline`, merge `--no-ff` (không squash,
không rebase) vào nhánh mặc định `claude/extract-upload-repo-gq2ws4` tại SHA
`f332a4cb4410b3ca9c71d659d36a3e8f26aa1fa5`. Trên default: Golden test
`58 passed, 2 skipped`; toàn bộ `pytest -q` `697 passed, 11 skipped, 0
failed`, 0 regression; business anchors 01/2026 và 06/2026 khớp tuyệt đối.
Chi tiết đầy đủ: `docs/tasks/TASK-GOLDEN-BASELINE-001-PLAN.md` Phần E/F/G.

Điều kiện `FULLY_ENFORCED` (`governance/core/V4_1_POLICY_FREEZE.md` §1) đã đủ
trên chính nhánh mặc định: Golden fixture tồn tại, deterministic expected
output tồn tại, one-command Golden diff tồn tại
(`python3 -m pytest tests/test_golden_baseline.py -q`), test suite đó PASS.
Ba executable enforcement asset đã kiểm chứng chạy được trên default:
`scripts/branch_authority_check.sh` → `AUTHORITY_OK`;
`PROJECT/REVIEW_BUDGET_LEDGER.md` có transition state đúng cho cả `TASK-110`
(`EXHAUSTED_PRE_V4.1`) và `TASK-GOLDEN-BASELINE-001` (`FROZEN`); Golden test
chạy PASS trên default.

Policy overlay: `governance/core/V4_1_POLICY_FREEZE.md`. Ngân sách sống
theo root task: `PROJECT/REVIEW_BUDGET_LEDGER.md`. Chi tiết Owner Decision:
DEC-140 trong `PROJECT/PROJECT_DECISIONS.md` (cấp phát lại từ `DEC-128` tại
phiên integration — `DEC-128` đã thuộc về TASK-110 Gate/Readiness Review từ
2026-08-23; xem `DEC-141`).

`TASK-110` (mọi nhánh review, lineage R1-A1…R8): **KHÔNG đổi bởi phiên này.**
Repair budget vẫn `EXHAUSTED_PRE_V4.1`, `remaining = 0`. `R1-A2 → R8` vẫn
`OWNER_EXTENSION REQUIRED` để mở tiếp. `CHECK-110-16` tiếp tục `BLOCKED`
(merge gate — thiếu production workbook thật). `TASK-110` vẫn `NOT DONE`.
Golden Baseline **không** tự đóng `TASK-110` (khác dataset, khác câu hỏi —
xem `docs/tasks/TASK-GOLDEN-BASELINE-001-PLAN.md` §A.20).

**Controlled Integration — `TASK-105B`/`TASK-105C` discovery + Owner
Decisions (2026-08-27, phiên "CONTROLLED INTEGRATION — TASK-105B/TASK-105C
GOVERNANCE CHECKPOINT").** `branch_authority_check.sh` báo
`INTEGRATION_DECISION_REQUIRED` (V4.1 §8: ahead=10-11 commit, cumulative LOC
6.936–8.131, cả hai vượt ngưỡng) trên nhánh
`claude/reports-price-rtdb-audit-bg5y4t` (toàn bộ chuỗi discovery
`DEC-147`→`DEC-152`, `S024`→`S029`). Owner chọn **Option A — integrate
soon**.

Cùng khuôn với `TASK-GOLDEN-BASELINE-001`: qua nhánh trung gian
`integration/v4-1-price-history-foundation` (cắt từ chính default tip
`7e60978`), merge `--no-ff` candidate `aaceb883` vào nhánh trung gian —
**0 conflict** (`merge-base` = default tip cũ, tức candidate vốn đã là
fast-forward-able descendant của default). Validator chạy đủ trước VÀ sau
integration (`validate_structure`/`validate_project_state`/
`validate_evidence`/`validate_task_completion` — cả bốn PASS;
`validate_reference_integrity` — đúng 3 lỗi tiền tồn `TASK-REM-T06`,
xác nhận bằng cách chạy lại validator trên chính default tip cũ, không
regression mới), `git diff --check` sạch ở mọi bước. Merge nhánh trung gian
vào nhánh mặc định bằng `--ff-only` (fast-forward thuần, không tạo merge
commit — giữ lineage tuyến tính, không rewrite, không squash, không force
push) tại SHA **`abddbe0c8f02330617917516957a26596b8d2dd9`**. Xác nhận:
candidate `aaceb883` là ancestor của default HEAD mới; `local == remote`
sau push. `branch_authority_check.sh` sau push: `DIVERGENCE = WITHIN_LIMITS`.

Toàn bộ nội dung integrate là **tài liệu governance/discovery/spec** — 0
byte `app/**`/`config/**`/`tests/**`/Golden fixture thay đổi; repo giá
(`Tracking`) không bị sửa; `TASK-105B`/`TASK-105C`/`TASK-108B`
**implementation vẫn CHƯA bắt đầu** — chỉ discovery, Owner Decisions
(`DEC-143`→`DEC-152`), và Scope Lock/Completion Gate của `TASK-105C` được
đưa vào nhánh mặc định. **Không được đọc "đã integrate" thành "đã
implement".**

## Reports History Reader V1 — S060 (2026-08-29)

Current-state pointer cho nhánh giá TRACKING theo thời gian. Không supersede
`DEC-154`; nó bổ sung một NGUỒN cho nhánh `TRACKING` và không đụng
`CUTOVER_DATE`.

**HAI cutover, tuyệt đối không gộp:**

```text
Tracking price-history data cutover = 2026-08-29 19:35:37 (Firebase server time)
    một THỜI ĐIỂM có múi giờ; là gốc trục thời gian của reader
    production: 3441 mã kiểm, 341 giá hợp lệ, 3100 absent, 0 invalid

Product Identity architecture cutover = 2026-09-01   (CUTOVER_DATE, DEC-154 §1)
    một NGÀY; KHÔNG đổi trong S060
```

Khoảng 29/08 → trước 01/09 KHÔNG phải lý do dời `01/09`.

**Thẩm quyền thời gian (đã đóng trong S060).** Trước S060, mốc cutover dùng
`ServerValue.TIMESTAMP` còn `purchase_price_history.t` dùng `Date.now()` của
máy trạm, và rules không có `.validate` nào cho `t` — không tồn tại bằng
chứng nào chứng minh thẩm quyền của nó. Repair phía Tracking (branch riêng
`claude/pph-server-timestamp-authority-v1`, base `91e57a00…`, final
`1821af06…`, **chưa deploy, chưa merge**) làm sự kiện MỚI mang
`t = ServerValue.TIMESTAMP` + `ta = "SERVER"`, và rules `.validate` bắt buộc
`t === now && ta === 'SERVER'` nên client không giả được nhãn. Sự kiện CŨ
không bị viết lại và KHÔNG được nâng thẩm quyền — chúng là
`UNVERIFIED_CLIENT` và reader fail-safe sang Pending.

**Reader.** `app/modules/pricing/tracking_history/` — nhận một `SaleInterval`
(không phải một thời điểm, vì Reports chỉ có độ phân giải NGÀY) và chỉ trả
giá khi trạng thái hằng trên toàn khoảng. Quy đổi nghìn VND → VND đúng một
chỗ. Unresolved → `price_source = "Pending"` → `Missing.PurchasePrice` của
`TASK-110`; không tạo hàng chờ mới.

**Điểm tích hợp.** `TrackingHistoryPriceProvider` là `PriceProvider` truyền
TƯỜNG MINH vào `run_import(price_provider=...)`. Mặc định pipeline vẫn
`PendingPriceProvider` (`CHECK-105-04`) và `run_import_production` KHÔNG nối
reader — composition P00–P11 vẫn thuộc `TASK-105E` (`PLANNED`).

Trạng thái: implementation PASS, **NOT DONE**. Evidence đầy đủ ở
`docs/sessions/S060-reports-history-reader-v1.md`.

## Current Price Architecture — DEC-154 (2026-08-28)

Khối này là current-state pointer mới nhất. Nó supersede các đoạn current
state cũ nếu còn nói mọi product phải map vào Tracking `<MÃ>`,
`TASK-105B → TASK-105C` là dependency tuyến tính, hoặc `TASK-105C = READY`.
Các đoạn cũ giữ nguyên làm lịch sử.

```text
CUTOVER_DATE = 2026-09-01

sale_date < cutover + Owner-confirmed historical report
  → identity + price authority = HISTORICAL_CONFIRMED_REPORT
  → bypass catalog/resolver/provider

sale_date >= cutover
  → TASK-105D resolves (namespace, source_product_code)
       ├─ TRACKING        → TASK-105C HistoricalVendorMin
       │                     absence → cross-map → TASK-105B
       └─ PUBLIC_PURCHASE → TASK-105B PublicPurchasePrice
  → PRICE RESOLUTION P00–P11  (chủ sở hữu: TASK-105E, DEC-156 §5)
  → KpiPurchasePrice / TASK-108B
```

Canonical namespaces: `TRACKING`, `PUBLIC_PURCHASE`. Tracking MISS không tự
động thành Pending nếu Public Purchase resolve deterministic; Public Purchase
product không cần Tracking product giả. Product identity và price source là
hai khái niệm tách biệt.

### Exact task states

```text
TASK-105B
  = FROZEN + INTEGRATED + RC-1 INTEGRATED + NOT DONE
  current role = Public Purchase effective-dated provider foundation
  DONE blocker = Owner/source-confirmed Public Purchase production dataset
                 load/replay được + remaining HB triggers resolved trước use
  PendingPriceProvider vẫn default; FilePriceProvider NOT ACTIVATED
  budget = 2 allowed / 1 used / 1 remaining

TASK-105E
  = IMPLEMENTED (Session 1, S061 2026-08-29) + NOT DONE
  Scope Lock Session 1 = SOẠN (chưa freeze); Completion Gate = CHƯA SOẠN
  production composition P00-P11 đã nối vào run_import_production()
  P00/P04/P05/P06/P07/P08/P09/P10/P11 = PASS (E1)
  P01/P02 = NOT_APPLICABLE (nguồn TASK-105C chưa được cấp phép)
  P03 = BLOCKED (điều kiện "no valid vendor candidate" không xác định được)
  OWNER_DECISION_REQUIRED = vị trí Reports History Reader V1 trong bảng P00-P11
  WAITING_REAL_POST_CUTOVER_DATA = chưa có đơn thật >= 2026-09-01,
      chưa có file capture production cho cả ba nguồn post-cutover
  budget = 2 allowed / 0 used / 2 remaining (không cycle nào mở bởi S061)
  Independent Review (Session 2) = CHƯA

TASK-105C
  = BLOCKED / NOT AUTHORIZED   (KHÔNG đổi bởi DEC-156, KHÔNG đổi bởi S061)
  semantic branch = TRACKING HistoricalVendorMin, DEC-151/152 preserved
  input = resolved TRACKING identity + sale_date
  output = HistoricalVendorMin hoặc absence cho fallback
  Scope Lock = REOPENED_BY_DEC-154
  Completion Gate = CHANGE_PROPOSAL_OPEN, NOT FROZEN
  không còn compose/depend cứng TASK-105B
  budget lineage = TASK-105C (ROOT RIÊNG, 2 allowed / 0 used / 2 remaining)
      cấp bởi Owner tại DEC-156 §4 (HB-154-04 Option B).
      TASK-105B giữ nguyên 2/1/1 — TASK-105B-RC-1 vẫn CONSUMED, không
      chuyển, không xoá. Đây là tách lineage theo kiến trúc, KHÔNG phải
      reset ngân sách đã tiêu.

TASK-105D
  = READY / SPECIFICATION COMPLETE + DATA CONTRACT COMPLETE
    + OWNER RATIFIED + COMPLETION GATE FROZEN
    (READY ≠ IMPLEMENTED ≠ DONE — implementation cần phiên cấp phép riêng,
     và DEC-157 §2 chặn implementation trước divergence decision)
  canonical spec = docs/tasks/TASK-105D-product-identity-resolver.md
  canonical data contract = docs/spec/TASK-105D-DATA-CONTRACT.md (S034/DEC-155,
      Owner-ratified DEC-156)
  Completion Gate 32 check = FROZEN (S038, 2026-08-28, V4.1 §12),
      32/32 NOT_TESTED (freeze đóng băng NGỮ NGHĨA, không tuyên bố đã test),
      gate count vẫn ĐÚNG 32, 32/32 REQUIRED, E2 = 19 / E1 = 13
      GATE_SET_SHA256 = 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
      frozen source SHA = be835b1b1b03d4e8d21656c3624b6e4bc964b7a1
  Freeze Finalization attempt #1 = FAIL (S036, 2026-08-28)
      5 BLOCKING / 5 HARDENING; testable 30/32; deterministic 29/32;
      G06 ↔ G23 mâu thuẫn; 5/20 case đối kháng bắt buộc không được phủ
      evidence: docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW.md
  Gate Revision #1 = ÁP DỤNG (S037, 2026-08-28, DEC-157)
      F-01…F-05 xử lý 5/5; G04/G05/G22 nay deterministic + testable;
      H-01/H-03 ĐÓNG; H-02 (một phần) + H-04 nạp thêm; H-05 CÒN MỞ
      (đổi data contract — ngoài thẩm quyền phiên gate revision);
      32/32 gate có assertion + fixture + PASS + FAIL + nguồn quy phạm;
      20/20 case đối kháng bắt buộc được phủ (trước: 14 ĐẠT / 1 MỘT PHẦN /
      5 KHÔNG ĐẠT); gate thêm = 0, gate xoá = 0, Evidence Level hạ = 0
      (hai lần NÂNG E1 → E2: CHECK-105D-10, CHECK-105D-21)
      evidence: docs/reviews/TASK-105D-COMPLETION-GATE-CHANGE-PROPOSAL.md
  Freeze Finalization retry (attempt #2) = PASS WITH HARDENING
      (S038, 2026-08-28, reviewed base SHA be835b1)
      review độc lập TOÀN BỘ 32 gate, KHÔNG kế thừa kết luận S037;
      BLOCKING 0 / HARDENING 4 / OUT_OF_SCOPE 3;
      testable 32/32; deterministic 32/32; contradiction 0;
      adversarial A–T 20/20 PASS; Owner Ratification OR-01/02/03 đều có gate
      → Completion Gate FROZEN; TASK-105D → READY
      HARDENING mới: HB-105D-F2-01 (§3.3 câu 8 "bộ ba" vs INV-55 "CẢ BỐN" —
                     V4.1 §11 giải; G21 C đã assert đúng bốn)
                     HB-105D-F2-02 (§16.1 stale: "CHƯA CÓ CHỦ" vs §16.3
                     GRANTED; thiếu E-A/E-B/E-C/E-D trong bảng ownership)
                     HB-105D-F2-03 (13 invariant không có gate riêng —
                     INV-51/52/53, 65, 79…82, 84/85/86, 26; INV-08 cố ý)
      HARDENING kế thừa: H-05 (ranking_method_id OPTIONAL vs hashed) —
                     phân loại lại độc lập = HARDENING, KHÔNG BLOCKING
      evidence: docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW-2.md
  implementation = IMPLEMENTATION CANDIDATE (S040, 2026-08-28)
      nhánh task/task-105d-implementation, base 222844d; KHÔNG merge default
      app/modules/product/identity/ — 19 module, ánh xạ 1:1 E-A…E-L
      174 test mới; 32/32 frozen check thực thi = PASS (E2 = 19 / E1 = 13)
      A–T đối kháng 20/20 PASS
      Golden 58 passed 2 skipped (KHÔNG ĐỔI); full 756 → 930 passed,
          11 skipped, 0 regression (delta = đúng 174 test mới)
      validator = baseline tham chiếu (chỉ 3 issue TASK-REM-T06), 0 regression
      GATE_SET_SHA256 tái lập KHỚP; khối gate frozen KHÔNG sửa một byte
      → 32 trường Status: trong khối gate vẫn đọc NOT_TESTED do giữ nguyên
        artifact freeze; kết quả thực thi thật ở
        docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md (lý do tại §1)
      H-05 / HB-105D-F2-01 / HB-105D-F2-02 = VẪN OPEN (không sửa data contract)
      HB-105D-F2-03 = đã phủ bằng test, phân loại HARDENING không đổi
      BLOCKING mới 0 / HARDENING mới 0 / OUT_OF_SCOPE mới 0
      CHƯA qua Independent Review ⇒ KHÔNG phải IMPLEMENTED-đã-verify,
          KHÔNG phải DONE
      evidence: docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md,
                docs/sessions/S040-task-105d-implementation.md
  independent review #1 = FAIL — REPAIR REQUIRED (S041, 2026-08-28)
      nhánh review/task-105d-implementation-1; target e6252c0, base 222844d
      reviewer KHÔNG phải tác giả implementation; KHÔNG kế thừa PASS của S040
      GATE_SET_SHA256 tái lập KHỚP; 32/32 frozen check PASS (thực thi độc lập)
      A–T 20/20 PASS bằng bộ đối kháng RIÊNG của reviewer
      Golden 58/2 KHÔNG ĐỔI; full 756 → 930; regression 0
      1 BLOCKING (B-01) / 7 HARDENING / 3 OUT_OF_SCOPE
      B-01 = thiếu khoá file; check-then-append race ở đúng biên "một máy"
             mà data contract §11.1 tuyên bố phủ; INV-59 không thi hành được
             qua biên tiến trình ⇒ hai bản ghi CONFIRMED độc lập ⇒
             MappingIntegrityError VĨNH VIỄN
      evidence: docs/reviews/TASK-105D-INDEPENDENT-IMPLEMENTATION-REVIEW-1.md,
                docs/sessions/S041-task-105d-independent-implementation-review-1.md
  repair cycle #1 = REPAIR CANDIDATE (S042, 2026-08-28)
      nhánh task/task-105d-rc1, base e6252c0; KHÔNG merge default
      Owner Decision B-01 = option (a) — GIỮ hợp đồng concurrency "một máy",
          sửa implementation bằng khoá file THẬT; KHÔNG thu hẹp §11.1 xuống
          một tiến trình; KHÔNG sửa Completion Gate đã freeze
      cơ chế: fcntl.flock(LOCK_EX) trên sidecar <log>.lock (O_NOFOLLOW, 0o600);
          nạp lại log quyền uy TRONG khoá TRƯỚC khi kiểm expected_version;
          append/import_bundle/rebuild_index dùng CHUNG một biên giao dịch;
          đường ghi thứ hai _persist_raw() bị XOÁ
      B-01 tái lập TRƯỚC sửa: 2 APPLIED + integrity error vĩnh viễn
      B-01 sau sửa: 60/60 vòng tranh chấp = đúng 1 APPLIED + đúng 1
          MappingVersionConflict; phân bố người thắng 26/34 (tranh chấp thật);
          kẻ ghi cũ KHÔNG append; reopen từ đĩa hợp lệ
      25 test mới (multiprocessing.Barrier, KHÔNG sleep/monkeypatch/1-instance)
          — chạy ở base e6252c0 → 18 failed ⇒ test THẬT SỰ bắt được defect
      targeted 174 → 199; Golden 58/2 KHÔNG ĐỔI; full 930 → 955; skipped 11 → 11
      GATE_SET_SHA256 tái lập KHỚP; khối gate 0 byte thay đổi;
          NOT_TESTED → PASS KHÔNG thực hiện (phiên này không có gate authority)
      validator = baseline tham chiếu (chỉ 3 issue TASK-REM-T06), 0 regression
      hiệu năng append +4…9 % ⇒ H-04 giữ nguyên HARDENING
      H-01…H-07, HB-105D-F2-01/02/03 = VẪN OPEN, KHÔNG sửa cơ hội
      B-01 = CODE-LEVEL RESOLVED / READY FOR INDEPENDENT RE-REVIEW
          (KHÔNG phải governance closure — Independent Review #2 sở hữu)
      evidence: docs/reviews/TASK-105D-RC-1-REPAIR-RECORD.md,
                docs/sessions/S042-task-105d-repair-cycle-1.md
  independent review #2 = PASS WITH HARDENING (S043, 2026-08-28)
      nhánh review/task-105d-implementation-2; target a098235 (RC-1 final)
      reviewer KHÔNG phải tác giả S040 và KHÔNG phải tác giả S042;
          KHÔNG kế thừa tuyên bố "CODE-LEVEL RESOLVED" của S042
      B-01 tái lập ĐỘC LẬP trên mã trước repair (e6252c0): 10/10 vòng cho
          hai APPLIED + MappingIntegrityError vĩnh viễn khi mở lại
      B-01 trên RC-1: 135 vòng / 7 kịch bản tranh chấp tiến trình HĐH thật
          (n=2/4/8; request-id giống và khác; append vs rebuild_index) —
          đúng 1 APPLIED, đúng n-1 MappingVersionConflict, log vật lý đúng
          1 dòng, reopen OK ở MỌI vòng; 0 bất thường, 0 flake
      khoá đo được ở mức HĐH: store.append() production bị chặn > 2 s sau một
          holder; SIGKILL → nhân trả khoá → append hoàn tất; không stale lock
      mọi đường ghi bền vững liệt kê ĐỘC LẬP bằng quét tĩnh toàn app/:
          store.py là module DUY NHẤT ghi xuống đĩa; append/import_bundle/
          rebuild_index dùng chung một biên giao dịch; _persist_raw đã XOÁ;
          HistoricalConfirmedRegistry = thuần bộ nhớ, ngoài phạm vi B-01
      anti-tautology: 25 test mới chạy trên e6252c0 → 19 failed
      B-01 CLOSURE MATRIX = 10/10 PASS  ⇒  B-01 = CLOSED
      32/32 frozen check PASS (thực thi độc lập); A–T 20/20 PASS
      GATE_SET_SHA256 tái lập KHỚP TUYỆT ĐỐI (57.614 byte); khối gate KHÔNG sửa
      targeted 199 / Golden 58+2 KHÔNG ĐỔI / full 955+11 / delta +25 / regression 0
      hiệu năng: chi phí khoá KHÔNG đo được trên nhiễu (RC-1 6,795 s vs
          pre-repair 6,969 s ở n=800) ⇒ H-04 giữ nguyên HARDENING, KHÔNG mở lại
      findings: 0 BLOCKING / 5 HARDENING mới / 4 OUT_OF_SCOPE
          H2-01 _consume() mutate state trước khi đẩy _log_offset ⇒ thử lại
                sau lỗi nạp trùng bản ghi (fail closed, 0 byte xuống đĩa;
                nằm TRONG cumulative repair diff RC-1 — V4.1 §3)
          H2-02 RC-1 tạo thêm ĐÚNG MỘT lỗi reference_integrity (3 → 4)
          H2-03 event đã commit nhưng caller nhận exception khi ghi index lỗi
                (hình dạng CÓ SẴN trước repair — không phải hồi quy RC-1)
          H2-04 test_both_orderings_… không khẳng định điều tên nó nói
          H2-05 log truncate về rỗng: store mở mới không phát hiện
      H-01…H-07 + HB-105D-F2-01/02/03 = 10/10 VẪN OPEN (đo lại, không trích dẫn);
          0 CLOSED, 0 SUPERSEDED, 0 RECLASSIFIED, 0 promote lên BLOCKING
      H-07: NOT_TESTED trong khối gate chặn DONE, KHÔNG chặn integration;
          reconciliation bắt buộc TRƯỚC DONE (§23 của artifact)
      Repair Cycle #2 = KHÔNG mở; budget KHÔNG đổi
      evidence: docs/reviews/TASK-105D-INDEPENDENT-IMPLEMENTATION-REVIEW-2.md,
                docs/sessions/S043-task-105d-independent-implementation-review-2.md
  controlled integration = HOÀN TẤT (S044, 2026-08-28)
      Owner Decision V4.1 §8 Option A — INTEGRATE EARLY
      nhánh integration/v4-1-task-105d-implementation, base 222844df
      git merge --no-ff × 3, ancestry-preserving; KHÔNG squash / rebase /
          cherry-pick; KHÔNG dựng lại diff implementation bằng tay
      hợp nhất: lineage RC-1 (e6252c0 → 1cc96a9 → a098235) + evidence
          Review #1 (58323e2e) + evidence Review #2 (4d44ec4a)
      xung đột = 2 file / 4 hunk, TOÀN BỘ là governance state; 0 xung đột
          chạm app/**, tests/**, khối frozen gate, hay data contract
      verdict lịch sử S041 giữ NGUYÊN VĂN (52/52 dòng, diff = rỗng);
          bản ghi repair-budget KHÔNG bị loại bỏ
      GATE_SET_SHA256 TRƯỚC == SAU = 0444e58c…4408a5c877 (KHÔNG ĐỔI)
      production ≡ RC-1 đã review: diff app/tests/config/tools/scripts/
          pyproject/docs/spec/docs/tasks vs a098235 = RỖNG;
          store.py sha256 = c3d3b09d… KHỚP
      targeted 199 / Golden 58+2 / full 955+11 / regression 0
      validator: structure/project_state/evidence/task_completion = PASS;
          reference_integrity = 3 issue = ĐÚNG BẰNG baseline canonical
          (H2-02 = RESOLVED_BY_INTEGRATION — hợp nhất artifact Review #1
           làm tham chiếu tự phân giải; validator KHÔNG bị sửa)
      HARDENING: 14 OPEN + 1 RESOLVED_BY_INTEGRATION (H2-02); 0 repair
      H-07 = VẪN OPEN — reconciliation bắt buộc TRƯỚC DONE, KHÔNG chặn
          integration (§23 của Review #2)
      Repair Cycle #2 = KHÔNG mở; budget KHÔNG ĐỔI
      INTEGRATION KHÔNG ngụ ý DONE
      evidence: docs/sessions/S044-task-105d-controlled-integration.md
  budget lineage = 2 allowed / 1 used / 1 remaining (S042 MỞ VÀ TIÊU THỤ
      Repair Cycle #1 — lần đầu của lineage; S036/S037/S038/S041 đều 0 dòng
      code/test nên không tiêu cycle, S042 có sửa app/** + tests/**)
  Ready Gate blocker = 0  (4 → 2 sau S034 → 1 sau DEC-156 → 0 sau S038):
    ĐÃ ĐÓNG: Owner ratification OR-01 / OR-02 / OR-03 (DEC-156)
    ĐÃ ĐÓNG: Completion Gate freeze (S038, 2026-08-28) — S036 TỪ CHỐI,
             S037 sửa gate theo đúng findings, S038 re-review độc lập
             TOÀN BỘ gate set rồi ghi FROZEN (V4.1 §12)

TASK-105E  (MỚI — Owner cấp task ID tại DEC-156 §5)
  = PLANNED / SPEC OUTLINE / READY GATE BLOCKED
  canonical owner của P00–P11 price-resolution composition
  canonical spec = docs/tasks/TASK-105E-price-resolution-composition.md
  Scope Lock = CHƯA SOẠN; Completion Gate = CHƯA SOẠN, NOT FROZEN
  implementation = NOT STARTED / NOT AUTHORIZED
  budget lineage mới = 2 allowed / 0 used / 2 remaining
  KHÔNG resolve identity, KHÔNG thay 105B/105C/105D, KHÔNG invent
  mapping/price, KHÔNG mutate Tracking

TASK-108B
  = BLOCKED_BY_DEPENDENCY  (KHÔNG unblocked bởi S038)
  chờ TASK-105D (blocker chuyển từ "gate chưa freeze được" sang "chờ
  implementation" — gate nay FROZEN nhưng implementation chưa mở),
  TASK-105C refreeze+implementation, TASK-105B DONE,
  TASK-105E (ownership ĐÃ CÓ tại DEC-156; Scope Lock/Gate/implementation
  CHƯA CÓ) và TASK-105B-Q3
```

### Remaining HB-105B audit

| Finding | Current trigger | Triggered now? | Required action |
|---|---|---|---|
| HB-105B-03 | Lần đầu đọc Public Purchase file thật/non-test | NO | Canonicalize invalid shape/root/row error trước usage |
| HB-105B-05 | Public Purchase dataset production xuất hiện | NO | Strict required-column check; typo không thành open record |
| HB-105B-06 | TASK-105C thêm tools/tests | NO | Mở rộng assertion đúng boundary; network chỉ ở intended tool |
| HB-105B-10 | Machine-generated file được nạp qua FilePriceProvider | NO | Strict schema trước Public Purchase export/snapshot usage |

`HB-105B-07/08` vẫn RESOLVED + independently verified; `09/11` vẫn
SUPERSEDED; `04` vẫn OUT_OF_SCOPE. Phiên docs này không mở Repair Cycle #2,
không tiêu budget.

### Next authorized action

*(Cập nhật 2026-08-28, S035/`DEC-156` — Owner Ratification. Toàn bộ quyết
định Owner đang chờ ở khối S034 bên dưới đã được đóng. Đoạn cũ giữ lại làm
lịch sử.)*

*(Cập nhật 2026-08-28, S038 — FREEZE FINALIZATION RETRY = **PASS WITH
HARDENING**; Completion Gate `TASK-105D` = **FROZEN**; `TASK-105D` = **READY**.
Đoạn ngay dưới đây là hành động kế tiếp hiện hành; các đoạn S037/S036/S035
phía sau giữ nguyên làm lịch sử.)*

*(Cập nhật 2026-08-28, S039 — CONTROLLED READINESS INTEGRATION. Owner đã
quyết định `V4.1` §8 **Option A — INTEGRATE EARLY** (`DEC-158`); toàn bộ
lineage readiness/freeze của `TASK-105D` đã được hợp nhất vào nhánh mặc định
giữ nguyên ancestry. Đoạn ngay dưới đây là trạng thái + hành động kế tiếp
hiện hành; khối "1. OWNER DECISION — BRANCH DIVERGENCE" của S038 phía sau nay
đã **ĐƯỢC ĐÓNG** và giữ nguyên làm lịch sử.)*

*(Cập nhật 2026-08-28, S040 — IMPLEMENTATION `TASK-105D`. Owner đã cấp phép
một phiên implementation RIÊNG; implementation candidate nằm trên nhánh
`task/task-105d-implementation`, **chưa** qua Independent Review và **chưa**
merge default. Khối S040 phía sau giữ nguyên làm lịch sử.)*

*(Cập nhật 2026-08-28, S041 — INDEPENDENT IMPLEMENTATION REVIEW #1 =
**FAIL — REPAIR REQUIRED**, 1 BLOCKING `B-01`. Hành động kế tiếp của S040
(mục 1) đã được thực hiện và trả kết quả FAIL.)*

*(Cập nhật 2026-08-28, S043 — **INDEPENDENT IMPLEMENTATION REVIEW #2**.
Phiên review độc lập (read-only) đã xác minh repair candidate `RC-1` tại
`a098235`. Khối S043 phía sau giữ nguyên làm lịch sử.)*

*(Cập nhật 2026-08-28, S044 — **CONTROLLED INTEGRATION**. Owner Decision
`V4.1` §8 Option A (INTEGRATE EARLY): lineage `TASK-105D` (implementation +
`RC-1`) cùng CẢ HAI artifact Independent Review đã được hợp nhất vào nhánh
mặc định bằng `git merge --no-ff`, giữ nguyên ancestry. Đoạn ngay dưới đây là
trạng thái + hành động kế tiếp hiện hành; các khối S043/S042/S040/S039 phía
sau giữ nguyên làm lịch sử.)*

### Trạng thái sau H-07 RECONCILIATION (S045, 2026-08-28)

```text
TASK-105D  = IMPLEMENTED + RC-1 INTEGRATED
             + INDEPENDENT REVIEW #2 PASS WITH HARDENING
             + CONTROLLED INTEGRATION COMPLETE
             H-07 = PARTIALLY RECONCILED
                 lớp diễn giải/thẩm quyền  : RESOLVED — Owner Decision
                     DEC-159 (Option (b)); GATE_SET_SHA256 KHÔNG đổi
                     (0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877,
                     tái lập TRƯỚC == SAU phiên S045)
                 lớp validator (điều kiện #7) : VẪN OPEN — MỚI, phạm vi hẹp
                     (validate_task_completion.py grep literal Status: PASS
                     trong khối gate, không biết tới Gate Execution Record
                     tách rời; sẽ FAIL nếu TASK-105D.Status=DONE được ghi
                     trong khi 32 khối vẫn NOT_TESTED)
             H-07 CLOSED?  KHÔNG.
             TASK-105D = STILL_BLOCKED_BEFORE_DONE (không phải
                 ELIGIBLE_FOR_DONE_REVIEW — điều kiện #7 chưa thoả)
             B-01 = CLOSED (không đổi, kế thừa S043/S044)
             32 trường Status: trong ĐỊNH NGHĨA gate vẫn NOT_TESTED — thiết
                 kế, KHÔNG mutate — "Frozen Gate Status" (freeze-time
                 metadata) và "Effective Completion Status" (bản ghi thực
                 thi tách rời, 32/32 PASS) nay là hai khái niệm canonical
                 tách biệt theo DEC-159
             HARDENING = 14 OPEN + 1 RESOLVED_BY_INTEGRATION (H2-02)
                 (không đổi bởi S045 — không finding nào bị sửa cơ hội)
             budget = 2 allowed / 1 used / 1 remaining (KHÔNG ĐỔI)
             Repair Cycle #2 = KHÔNG mở
             frozen gate = KHÔNG SỬA; app/**, tests/**, config/** = 0 dòng

TASK-105B  = FROZEN + INTEGRATED + RC-1 INTEGRATED / NOT DONE / NOT ACTIVATED (không đổi)
TASK-105C  = BLOCKED / NOT AUTHORIZED                                        (không đổi)
TASK-105E  = PLANNED / OUTLINE / READY GATE BLOCKED / NOT AUTHORIZED         (không đổi)
TASK-108B  = BLOCKED_BY_DEPENDENCY                                           (không đổi)
```

**HÀNH ĐỘNG KẾ TIẾP ĐƯỢC PHÉP (S045 → …)**

```text
1. Một phiên có thẩm quyền tooling/governance-scripts, được Owner cấp phép
   riêng, đối chiếu governance/scripts/governance/validate_task_completion.py
   với mô hình hai lớp vừa được DEC-159 công nhận — HOẶC Owner chấp nhận
   rằng DONE thật sự của TASK-105D sẽ cần một Completion Gate Change
   Proposal riêng (mutate 32 trường Status:, đổi GATE_SET_SHA256) tại thời
   điểm đó.
2. Xem CAP-PRICE-RESOLUTION (bên dưới) cho hành động kế tiếp của Objective B.
3. KHÔNG mở Repair Cycle #2. KHÔNG đánh dấu TASK-105D = DONE.
4. TASK-105E vẫn NOT IMPLEMENTED / NOT AUTHORIZED; FilePriceProvider vẫn
   KHÔNG activate; Tracking vẫn KHÔNG chạm.
```

Bằng chứng đầy đủ:
`docs/sessions/S045-task-105d-h07-reconciliation-and-capability-governance.md`,
`DEC-159` trong `PROJECT/PROJECT_DECISIONS.md`.

*(Cập nhật 2026-08-28, S044 — khối trạng thái controlled integration, nay là
LỊCH SỬ: H-07 reconciliation S045 phía trên đã thay thế phần "hành động kế
tiếp" và bổ sung disposition H-07. Verdict của S044 giữ nguyên từng chữ.)*

### Trạng thái sau H-07 VALIDATOR ALIGNMENT (S046, 2026-08-28)

```text
TASK-105D  = IMPLEMENTED + RC-1 INTEGRATED
             + INDEPENDENT REVIEW #2 PASS WITH HARDENING
             + CONTROLLED INTEGRATION COMPLETE
             H-07 = RECONCILED (CẢ HAI LỚP)
                 lớp diễn giải/thẩm quyền  : RESOLVED — DEC-159 (không đổi)
                 lớp validator (điều kiện #7) : RESOLVED — DEC-161.
                     governance/scripts/governance/validate_task_completion.py
                     nay công nhận Layer 2 (Gate Execution Record) theo đúng
                     8 điều kiện binding DEC-159 §1; fail-closed trên thiếu
                     record/sai hash/thiếu check ID/FAIL/thiếu lineage/
                     duplicate-ambiguous. Layer 1 (Status: PASS literal)
                     không đổi hành vi. Xác nhận bằng 10 test tập trung +
                     mô phỏng trên chính dữ liệu thật TASK-105D (32/32 PASS,
                     0 lỗi, không mutate file task).
             H-07 mechanical blocker CLOSED?  CÓ.
             TASK-105D = ELIGIBLE_FOR_DONE_REVIEW (không phải DONE — 4 điều
                 kiện completion khác chưa được S046 đánh giá: 0 BLOCKING
                 finding re-verify, Independent Review cho chính hành động
                 DONE, INV-01…INV-87, progress/handoff cho DONE)
             GATE_SET_SHA256 = 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
                 — KHÔNG đổi (đo lại trước/sau S046, khớp tuyệt đối)
             32 trường Status: trong ĐỊNH NGHĨA gate vẫn NOT_TESTED — thiết
                 kế, KHÔNG mutate
             HARDENING = 14 OPEN + 1 RESOLVED_BY_INTEGRATION (H2-02, không
                 đổi bởi S046)
             budget = 2 allowed / 1 used / 1 remaining (KHÔNG ĐỔI — S046
                 không phải repair cycle, 0 byte app/**/tests/**/config/**)
             Repair Cycle #2 = KHÔNG mở
             frozen gate = KHÔNG SỬA; app/**, config/**, docs/tasks/TASK-105D-*.md = 0 dòng
```

**HÀNH ĐỘNG KẾ TIẾP ĐƯỢC PHÉP (S046 → …)**

```text
1. Một phiên DONE-review có thẩm quyền completion (KHÔNG phải S046) đánh
   giá 4 điều kiện completion còn lại (0 BLOCKING finding re-verify,
   Independent Review cho chính hành động "đặt Status: DONE", INV-01…
   INV-87, progress/roadmap/handoff cập nhật), rồi mới được đặt TASK-105D
   top-level Status: DONE.
2. KHÔNG mở Repair Cycle #2. KHÔNG tạo task mới. KHÔNG chạm
   TASK-105B/C/E/108B. KHÔNG thực hiện V4.2 migration.
3. Nhánh governance/task-105d-gate-execution-reconciliation KHÔNG merge
   vào nhánh mặc định trong phiên S046.
```

Bằng chứng đầy đủ:
`docs/sessions/S046-task-105d-h07-validator-alignment.md`,
`DEC-161` trong `PROJECT/PROJECT_DECISIONS.md`.

### Trạng thái sau GOLDEN ORDER #1 CANONICAL ACCEPTANCE (S049, 2026-08-29)

```text
TASK-105D  = DONE                                    (không đổi, không reopen)

END_TO_END_ACCEPTANCE : PENDING_OWNER_DATA → DEFINED

             Owner cung cấp đầy đủ dữ liệu còn thiếu cho Golden Order #1
             (BH62063) — xem mục "END_TO_END_ACCEPTANCE" phía trên (đã cập
             nhật tại chỗ, KHÔNG tạo framework acceptance song song) và
             DEC-163.

             Toạ độ Owner-confirmed: OrderID, sale date, raw product name,
             Tracking code, Public Purchase code, canonical identity kỳ
             vọng (TRACKING:FV1410S4W1), price source kỳ vọng ("Tồn"),
             ApplicablePriceDate, ExpectedPurchasePrice (7.000.000 VND),
             currency/unit, quantity, sell price, discount, Public
             Purchase fallback authorization, công thức thủ công, số học
             cụ thể, ExpectedEligibleKpiProfit (500.000 VND), provenance
             human-readable — đầy đủ, không chỉ con số cuối.

             "Tồn" semantic guard: giữ nguyên đúng nhãn Owner dùng.
             TECHNICAL_SOURCE_MAPPING của "Tồn" = UNRESOLVED (không tự
             suy diễn sang phist NCC / Public Purchase / inv.cong). Public
             Purchase CHỈ là fallback được Owner cho phép khi preferred
             price path không có giá phù hợp — KHÔNG phải preferred
             source.

             Production diff = 0 (app/**, config/**, Tracking không đổi).
             Test implementation diff = 0.
             Registration guard: SET A 13→13, SET B 22→22,
                 new_registered_task_ids = 0.
             V4.2 KHÔNG adoption. TASK-105C/E/108B KHÔNG mở.
             Owner Decision đóng dấu: DEC-163.

Golden Baseline hiện có (58 passed, 2 skipped) = KHÔNG đổi trong S049.
BH62063 = business seed cho Golden Baseline, KHÔNG phải Golden framework
             thứ hai.
```

Bằng chứng đầy đủ: `DEC-163` trong `PROJECT/PROJECT_DECISIONS.md`,
`docs/sessions/S049-golden-order-1-canonical-acceptance.md`.

**HÀNH ĐỘNG KẾ TIẾP ĐƯỢC PHÉP (S049 → …)**

```text
1. END_TO_END_ACCEPTANCE = DEFINED. Critical path kế tiếp: RUN BH62063
   THROUGH CURRENT SYSTEM AS-IS để xác định FIRST_FAILING_BOUNDARY thật
   (session đề xuất: S050 — GOLDEN ORDER #1 AS-IS VERTICAL TRACE). Đây là
   trace, KHÔNG phải implementation.
2. KHÔNG tự gán TASK-105C / TASK-105E / TASK-108B là bước kế tiếp trước
   khi AS-IS execution chứng minh boundary đó. KHÔNG tạo task mới. KHÔNG
   thực hiện V4.2 migration.
3. Nhánh governance/golden-order-1-canonicalize KHÔNG merge vào nhánh mặc
   định trong phiên S049.
```

### Trạng thái sau INV-81/INV-82 EVIDENCE CLOSURE (S048, 2026-08-29)

```text
TASK-105D  = DONE

             S048 đóng đúng NEAREST_REMAINING_BLOCKING_CONDITION mà S047 để
             lại: evidence INV-81/INV-82 yếu (H-06).

             INV-81  : Classification A — production behavior đã tồn tại
                 (PublicPurchaseSourceLoader.load() đọc rollback_of trực
                 tiếp từ data, public_purchase.py:219; không có API
                 "rollback" riêng). Test viết lại để đi qua đúng loader thật
                 thay vì object.__setattr__ (tests/test_105d_boundaries.py,
                 tests/support/identity_fixtures.py). INV-81 = PASS.
             INV-82  : Classification B — G21
                 (tests/test_105d_audit_replay.py::TestG21ProvenanceActorAndReplay::
                 test_part_c_replay_is_identical_after_store_catalog_and_price_change)
                 đã chứng minh đầy đủ qua đường replay thật; xác minh độc lập
                 tại S048 rằng rollback_of không rẽ nhánh ở đâu khác trong
                 app/. Evidence binding ghi tại
                 docs/reviews/TASK-105D-INV81-INV82-EVIDENCE-CLOSURE.md, KHÔNG
                 tạo test trùng lặp. INV-82 = PASS.
             H-06    = RESOLVED (mapping đầy đủ: xem review doc §6)
             INV-01…INV-87 = PASS

             GATE_SET_SHA256 = 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
                 — KHÔNG đổi (đo lại trước/sau S048, khớp tuyệt đối; thay đổi
                 Status field + Exit Criteria đều NGOÀI vùng frozen 631-2359)
             HARDENING = 13 OPEN + 1 RESOLVED_BY_INTEGRATION (H2-02) — H-06
                 chuyển RESOLVED (không đổi cách phân loại các mục còn lại)
             validator = structure/project_state/evidence PASS;
                 task_completion PASS (Checked 7 DONE task(s), 0 lỗi — Layer 2
                 kích hoạt thật lần đầu trên TASK-105D thật); reference_integrity
                 FAIL 3 issue (baseline TASK-REM-T06, không đổi, không liên
                 quan TASK-105D)
             targeted 199 / Golden 58+2 / full 965+11+0 — khớp tuyệt đối S047
             production diff = 0 (app/**, config/**, Tracking)
             registration guard: SET A 13→13, SET B 22→22,
                 new_registered_task_ids = 0
             budget = 2 allowed / 1 used / 1 remaining (KHÔNG ĐỔI — S048
                 không phải repair cycle)
             Repair Cycle #2 = KHÔNG mở
             Owner Decision đóng dấu: DEC-162

TASK-105B  = FROZEN + INTEGRATED + RC-1 INTEGRATED / NOT DONE / NOT ACTIVATED (không đổi)
TASK-105C  = BLOCKED / NOT AUTHORIZED                                        (không đổi)
TASK-105E  = PLANNED / OUTLINE / READY GATE BLOCKED / NOT AUTHORIZED         (không đổi)
TASK-108B  = BLOCKED_BY_DEPENDENCY                                           (không đổi)
```

**HÀNH ĐỘNG KẾ TIẾP ĐƯỢC PHÉP (S048 → …)**

```text
1. TASK-105D = DONE. Vertical critical path kế tiếp: Golden Order BH62063
   (Owner-confirmed, §17 của brief S048) — persist END_TO_END_ACCEPTANCE =
   DEFINED, sau đó chạy hệ thống hiện tại AS-IS để tìm FIRST_FAILING_BOUNDARY.
   Đây là bước implementation kế tiếp của CAP-PRICE-RESOLUTION — KHÔNG mở
   trong S048.
2. KHÔNG mở Repair Cycle #2 mặc định. KHÔNG tạo task mới. KHÔNG chạm
   TASK-105B/C/E/108B. KHÔNG thực hiện V4.2 migration.
3. Nhánh review/task-105d-inv81-inv82-closure KHÔNG merge vào nhánh mặc định
   trong phiên S048.
```

Bằng chứng đầy đủ:
`docs/sessions/S048-task-105d-inv81-inv82-evidence-closure.md`,
`docs/reviews/TASK-105D-INV81-INV82-EVIDENCE-CLOSURE.md`, `DEC-162`.

### Trạng thái sau FINAL COMPLETION REVIEW (S047, 2026-08-28)

```text
TASK-105D  = IMPLEMENTED + RC-1 INTEGRATED
             + INDEPENDENT REVIEW #2 PASS WITH HARDENING
             + CONTROLLED INTEGRATION COMPLETE
             + H-07 RECONCILED (không đổi, kế thừa DEC-159/DEC-161)
             TASK-105D = NOT_DONE  (không đổi top-level Status: vẫn READY)

             S047 là phiên Independent Review cho chính hành động "đặt
             Status: DONE" (điều kiện còn thiếu mà DEC-161 §6 nêu) — đã
             thực hiện, verdict = NOT_DONE, không phải "chưa đánh giá".

             4 điều kiện completion còn lại theo DEC-161 §6, đánh giá lại
             tại S047:
               0 BLOCKING finding re-verify        : PASS (B-01 CLOSED,
                   H2-02 RESOLVED_BY_INTEGRATION, unresolved BLOCKING = 0)
               Independent Review cho hành động DONE : THỰC HIỆN tại S047
                   (evidence level E2) — xem
                   docs/reviews/TASK-105D-FINAL-COMPLETION-REVIEW.md
               INV-01…INV-87                        : PARTIAL — INV-81,
                   INV-82 chỉ có test "yếu" (H-06, OPEN từ S041, không đổi
                   qua RC-1/S043/S044/S045/S046; xác minh lại trực tiếp mã
                   test tại S047, đúng nhận định cũ: test_inv81 dùng
                   object.__setattr__ bơm thẳng field cần chứng minh thay vì
                   qua API rollback thật; test_inv82 tự ghi nhận chứng minh
                   đầy đủ nằm ở G21 chứ không phải chính nó)
               progress/roadmap/handoff cập nhật     : khối này (đang viết)

             NEAREST_REMAINING_BLOCKING_CONDITION = Exit Criteria
                 "INV-01…INV-87 có assertion tương ứng" chưa thoả cho
                 INV-81/INV-82 (docs/tasks/TASK-105D-product-identity-resolver.md
                 dòng 2385-2386). Mọi điều kiện REQUIRED khác đã PASS.

             GATE_SET_SHA256 = 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
                 — KHÔNG đổi (đo lại trước/sau S047, khớp tuyệt đối)
             HARDENING = 14 OPEN + 1 RESOLVED_BY_INTEGRATION (H2-02,
                 không đổi bởi S047)
             validator = structure/project_state/evidence/task_completion
                 PASS; reference_integrity FAIL 3 issue (baseline
                 TASK-REM-T06, không đổi, không liên quan TASK-105D)
             targeted 199 / Golden 58+2 / full 965+11 / regression 0
             production diff = 0 (app/**, config/**, Tracking)
             registration guard: SET A 13→13, SET B 22→22,
                 new_registered_task_ids = 0
             budget = 2 allowed / 1 used / 1 remaining (KHÔNG ĐỔI — S047
                 không phải repair cycle)
             Repair Cycle #2 = KHÔNG mở

TASK-105B  = FROZEN + INTEGRATED + RC-1 INTEGRATED / NOT DONE / NOT ACTIVATED (không đổi)
TASK-105C  = BLOCKED / NOT AUTHORIZED                                        (không đổi)
TASK-105E  = PLANNED / OUTLINE / READY GATE BLOCKED / NOT AUTHORIZED         (không đổi)
TASK-108B  = BLOCKED_BY_DEPENDENCY                                           (không đổi)
```

**HÀNH ĐỘNG KẾ TIẾP ĐƯỢC PHÉP (S047 → …)**

```text
1. MỘT trong hai, do một phiên có thẩm quyền phù hợp thực hiện:
   (a) một phiên Repair Cycle (tiêu 1 cycle còn lại của budget 2/1/1) viết
       lại test_inv81_…/test_inv82_… (tests/test_105d_boundaries.py) để
       diễn tập một đường rollback/migration sản xuất thật thay vì
       object.__setattr__ trên fixture, rồi một phiên DONE-review kế tiếp
       xác nhận lại; HOẶC
   (b) một Owner Decision tường minh chấp nhận evidence hiện có (H-06) là
       đủ cho Exit Criteria INV-01…INV-87, theo tiền lệ Option (b) của
       DEC-159 cho H-07.
2. KHÔNG mở Repair Cycle #2 mặc định — đó là quyết định của phiên (a) ở
   trên nếu được Owner cấp phép, KHÔNG tự động.
3. KHÔNG tạo task mới. KHÔNG chạm TASK-105B/C/E/108B. KHÔNG thực hiện V4.2
   migration.
4. Nhánh review/task-105d-done-final KHÔNG merge vào nhánh mặc định trong
   phiên S047.
5. Vertical Slice: Golden Order BH62063 (KpiPurchasePrice kỳ vọng
   7.000.000 VND, EligibleKpiProfit kỳ vọng 500.000 VND) là business oracle
   đã sẵn sàng cho bước implementation kế tiếp của CAP-PRICE-RESOLUTION —
   nhưng bước đó vẫn CHƯA mở vì TASK-105D chưa DONE.
```

Bằng chứng đầy đủ:
`docs/sessions/S047-task-105d-final-completion-review.md`,
`docs/reviews/TASK-105D-FINAL-COMPLETION-REVIEW.md`.

### Trạng thái sau CONTROLLED INTEGRATION (S044, 2026-08-28)

```text
TASK-105D  = IMPLEMENTED + RC-1 INTEGRATED
             + INDEPENDENT REVIEW #2 PASS WITH HARDENING
             + CONTROLLED INTEGRATION COMPLETE
             NOT DONE
             implementation ĐÃ nằm trên nhánh mặc định
             B-01 = CLOSED (ma trận đóng 10/10, xác minh độc lập bởi S043)
             BLOCKING = 0
             Completion Gate 32 check = FROZEN, KHÔNG sửa một byte
             GATE_SET_SHA256 = 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
                               (TRƯỚC == SAU integration)
             32 trường Status: trong ĐỊNH NGHĨA gate vẫn NOT_TESTED —
                 bằng chứng thực thi 32/32 PASS nằm TÁCH RỜI tại
                 docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md và
                 §17.2 của Independent Review #2
             H-07 = VẪN OPEN — gate-authority reconciliation BẮT BUỘC
                 TRƯỚC DONE; KHÔNG chặn controlled integration
             HARDENING = 14 OPEN + 1 RESOLVED_BY_INTEGRATION (H2-02)
             targeted 199 / Golden 58+2 KHÔNG ĐỔI / full 955+11 / regression 0
             budget = 2 allowed / 1 used / 1 remaining (KHÔNG ĐỔI)
             Repair Cycle #2 = KHÔNG mở

TASK-105B  = FROZEN + INTEGRATED + RC-1 INTEGRATED
             NOT DONE / NOT ACTIVATED                       (không đổi; không chạm)
             FilePriceProvider KHÔNG activate; diff file = RỖNG
TASK-105C  = BLOCKED / NOT AUTHORIZED                       (không đổi; không chạm)
TASK-105E  = PLANNED / OUTLINE / READY GATE BLOCKED         (không đổi; không mở)
             NOT IMPLEMENTED / NOT AUTHORIZED
TASK-108B  = BLOCKED_BY_DEPENDENCY                          (không đổi)

default branch   = ĐÃ CẬP NHẬT (đây là mục đích được cấp phép của S044)
merge            = git merge --no-ff × 3 + merge --no-ff vào default
                   KHÔNG squash / KHÔNG rebase / KHÔNG cherry-pick
app/** , tests/** = 0 dòng thay đổi bởi S044 (chỉ mang qua từ RC-1 đã review)
production ≡ a098235 đã review: diff production = RỖNG
app/pipeline.py  = KHÔNG ĐỔI (PendingPriceProvider vẫn là default)
Tracking         = KHÔNG CHẠM, 0 lệnh ghi
production data  = KHÔNG CHẠM, KHÔNG TẠO
data contract    = KHÔNG SỬA
frozen gate      = KHÔNG SỬA
```

**HÀNH ĐỘNG KẾ TIẾP ĐƯỢC PHÉP (S044 → …)**

```text
1. Owner / gate authority reconcile H-07 theo §23 của Independent Review #2
   — BẮT BUỘC TRƯỚC khi bất kỳ phiên nào đề xuất TASK-105D = DONE.
   Khuyến nghị của reviewer: đường (b) — Owner Decision công nhận bản ghi
   thực thi tách rời, giữ nguyên GATE_SET_SHA256 = 0444e58c….
2. KHÔNG mở Repair Cycle #2 (B-01 đã CLOSED). Nếu Owner muốn đóng
   H2-01 / H-05 / H-01 / H-03: đó là Owner Decision; H2-01 + H-05 cùng vùng
   mã (_consume) nên sửa MỘT lượt, thuộc CÙNG cycle #1 theo V4.1 §3 —
   không tiêu thêm ngân sách.
3. Song song, không chặn: phiên có thẩm quyền data contract đóng H-02
   (ranking_method_id §6.7), HB-105D-F2-01, HB-105D-F2-02.
4. TASK-105E vẫn NOT IMPLEMENTED / NOT AUTHORIZED; FilePriceProvider vẫn
   KHÔNG activate; Tracking vẫn KHÔNG chạm.
```

*(Cập nhật 2026-08-28, S043 — khối trạng thái review độc lập, nay là LỊCH SỬ:
controlled integration S044 phía trên đã thay thế phần "hành động kế tiếp".
Verdict của S043 giữ nguyên từng chữ.)*

### Trạng thái sau INDEPENDENT REVIEW #2 (S043, 2026-08-28)

```text
TASK-105D  = RC-1 VERIFIED — ELIGIBLE FOR CONTROLLED INTEGRATION
             NOT DONE / NOT MERGED / NOT INTEGRATED
             nhánh task/task-105d-rc1, final SHA a098235
             B-01 = CLOSED  (10/10 tiêu chí đóng, xác minh ĐỘC LẬP bởi S043)
             verdict Review #2 = PASS WITH HARDENING
             findings Review #2 = 0 BLOCKING / 5 HARDENING mới / 4 OUT_OF_SCOPE
             Completion Gate 32 check = FROZEN, KHÔNG sửa một byte
             GATE_SET_SHA256 = 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
                               (tái lập khớp tuyệt đối bởi S043, 57.614 byte)
             NOT_TESTED → PASS = KHÔNG thực hiện (S043 không có gate authority)
             32/32 frozen check PASS + A–T 20/20 PASS (thực thi độc lập S043)
             targeted 199 / Golden 58+2 KHÔNG ĐỔI / full 955+11 / regression 0
             HARDENING đang mở = H-01…H-07 + HB-105D-F2-01/02/03 (10, kế thừa)
                                 + H2-01…H2-05 (5, mới từ S043)
             budget = 2 allowed / 1 used / 1 remaining  (Review #2 KHÔNG tiêu cycle)
             Repair Cycle #2 = KHÔNG mở

TASK-105B  = FROZEN + INTEGRATED + RC-1 INTEGRATED
             NOT DONE / NOT ACTIVATED                       (không đổi; không chạm)
             FilePriceProvider KHÔNG activate; diff file = RỖNG
TASK-105C  = BLOCKED / NOT AUTHORIZED                       (không đổi; không chạm)
TASK-105E  = PLANNED / OUTLINE / READY GATE BLOCKED         (không đổi; không mở)
TASK-108B  = BLOCKED_BY_DEPENDENCY                          (không đổi)

default branch   = KHÔNG ĐỔI
merge            = KHÔNG thực hiện
task/task-105d-rc1            = KHÔNG CHẠM (review branch chỉ mang evidence)
task/task-105d-implementation = KHÔNG CHẠM
app/** , tests/** , config/** = 0 dòng thay đổi bởi S043
app/pipeline.py  = KHÔNG ĐỔI (PendingPriceProvider vẫn là default)
Tracking         = KHÔNG CHẠM, 0 lệnh ghi
production data  = KHÔNG CHẠM, KHÔNG TẠO; toàn bộ fixture là dữ liệu tổng hợp
data contract    = KHÔNG SỬA
```

**HÀNH ĐỘNG KẾ TIẾP ĐƯỢC PHÉP (S043 → …)**

```text
1. OWNER INTEGRATION DECISION theo V4.1 §8 — divergence hiện ở
   INTEGRATION_DECISION_REQUIRED [loc > 5.000]. Owner chọn (A) integrate sớm,
   (B) cắt scope, hay (C) tiếp tục divergence có lý do + review date.
   Khuyến nghị của reviewer: (A).
2. NẾU (A): một phiên CONTROLLED INTEGRATION hợp nhất lineage TASK-105D
   (e6252c0 → 1cc96a9 → a098235) vào default bằng git merge --no-ff
   (ancestry-preserving; KHÔNG squash, KHÔNG cherry-pick), hợp nhất KÈM cả
   artifact Review #1 (58323e2e) và Review #2 — việc này tự phân giải H2-02.
3. TRƯỚC KHI bất kỳ phiên nào đề xuất TASK-105D = DONE: Owner reconcile H-07
   (NOT_TESTED trong khối gate chặn DONE, không chặn integration) — xem §23
   của docs/reviews/TASK-105D-INDEPENDENT-IMPLEMENTATION-REVIEW-2.md.
4. KHÔNG mở Repair Cycle #2 (B-01 đã CLOSED; 5 finding mới đều HARDENING).
   Nếu Owner muốn đóng H2-01 / H-05 / H-01 / H-03: đó là Owner Decision;
   H2-01 + H-05 cùng vùng mã (_consume) nên sửa MỘT lượt, và thuộc CÙNG
   cycle #1 theo V4.1 §3 — không tiêu thêm ngân sách.
5. Song song, không chặn: phiên có thẩm quyền data contract đóng H-02
   (ranking_method_id §6.7), HB-105D-F2-01, HB-105D-F2-02.
```

*(Cập nhật 2026-08-28, S042 — **REPAIR CYCLE #1**. Owner cấp phép mở Repair
Cycle #1 và quyết định `B-01` = option (a). Repair candidate nằm trên nhánh
`task/task-105d-rc1`, **chưa** qua Independent Review #2 và **chưa** merge
default. Đoạn ngay dưới đây là trạng thái + hành động kế tiếp hiện hành; các
khối S040/S039 phía sau giữ nguyên làm lịch sử.)*

### Trạng thái sau REPAIR CYCLE #1 (S042, 2026-08-28)

```text
TASK-105D  = REPAIR CANDIDATE — READY FOR INDEPENDENT REVIEW #2
             NOT INDEPENDENT-REVIEWED-2 / NOT DONE / NOT MERGED
             nhánh task/task-105d-rc1, base e6252c0
             B-01 = CODE-LEVEL RESOLVED / READY FOR INDEPENDENT RE-REVIEW
             Completion Gate 32 check = FROZEN, KHÔNG sửa một byte
             GATE_SET_SHA256 = 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
                               (tái lập khớp SAU repair)
             NOT_TESTED → PASS = KHÔNG thực hiện (không có gate authority)
             targeted 199 / Golden 58+2 KHÔNG ĐỔI / full 955+11 / regression 0
             HARDENING H-01…H-07 + HB-105D-F2-01/02/03 = VẪN OPEN
             budget = 2 allowed / 1 used / 1 remaining

TASK-105B  = FROZEN + INTEGRATED + RC-1 INTEGRATED
             NOT DONE / NOT ACTIVATED                       (không đổi; không chạm)
             FilePriceProvider KHÔNG activate; diff file = RỖNG
TASK-105C  = BLOCKED / NOT AUTHORIZED                       (không đổi; không chạm)
TASK-105E  = PLANNED / OUTLINE / READY GATE BLOCKED         (không đổi; không mở)
TASK-108B  = BLOCKED_BY_DEPENDENCY                          (không đổi)

default branch   = KHÔNG ĐỔI
merge            = KHÔNG thực hiện
task/task-105d-implementation = KHÔNG CHẠM
app/pipeline.py  = KHÔNG ĐỔI (PendingPriceProvider vẫn là default)
Tracking         = KHÔNG CHẠM, 0 lệnh ghi
production data  = KHÔNG CHẠM, KHÔNG TẠO; toàn bộ fixture là dữ liệu tổng hợp
data contract    = KHÔNG SỬA (§11.1 giữ nguyên phạm vi "một máy")
```

**HÀNH ĐỘNG KẾ TIẾP ĐƯỢC PHÉP (S042 → …)**

```text
1. INDEPENDENT IMPLEMENTATION REVIEW #2 của repair candidate, do một phiên
   KHÁC thực hiện, trên nhánh task/task-105d-rc1 (V4.1 §12 — reviewer không
   được là người viết repair). Phiên S042 cố ý KHÔNG tự review chính mình và
   KHÔNG tuyên bố B-01 đã đóng về mặt governance.
2. Trọng tâm review #2: B-01 (10 tiêu chí đóng ở §20 của bản ghi repair),
   cộng toàn bộ HARDENING H-01…H-07 và HB-105D-F2-01/02/03 vẫn mở.
3. Owner quyết định H-05 / H-02 (data contract §6.7 ranking_method_id) — vẫn
   cần một phiên có thẩm quyền sửa data contract; S042 KHÔNG sửa.
4. CHỈ SAU (1) PASS: quyết định integration vào default theo V4.1 §8.
5. Còn 1 repair cycle trong ngân sách lineage. Vượt → OWNER_EXTENSION REQUIRED.
```

### Trạng thái sau IMPLEMENTATION (S040, 2026-08-28)

```text
TASK-105D  = IMPLEMENTATION CANDIDATE
             READY → implementation viết xong, 32/32 frozen check PASS
             NOT INDEPENDENT-REVIEWED / NOT DONE / NOT MERGED
             Completion Gate 32 check = FROZEN, KHÔNG sửa một byte
             GATE_SET_SHA256 = 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
                               (tái lập khớp SAU implementation)
             32/32 PASS      — bản ghi: docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md
                               (khối gate giữ NOT_TESTED để không đổi SHA — §1
                                của bản ghi giải thích đầy đủ)
             budget = 2 allowed / 0 used / 2 remaining   (KHÔNG ĐỔI)
             Repair Cycle = KHÔNG mở

TASK-105B  = FROZEN + INTEGRATED + RC-1 INTEGRATED
             NOT DONE / NOT ACTIVATED                       (không đổi; không chạm)
             FilePriceProvider KHÔNG activate; diff file = RỖNG
TASK-105C  = BLOCKED / NOT AUTHORIZED                       (không đổi; không chạm)
TASK-105E  = PLANNED / OUTLINE / READY GATE BLOCKED         (không đổi; không mở)
TASK-108B  = BLOCKED_BY_DEPENDENCY                          (không đổi)

default branch   = KHÔNG ĐỔI
app/pipeline.py  = KHÔNG ĐỔI (PendingPriceProvider vẫn là default)
Tracking         = KHÔNG CHẠM, 0 lệnh ghi
production data  = KHÔNG TẠO; toàn bộ fixture là dữ liệu tổng hợp
```

**HÀNH ĐỘNG KẾ TIẾP ĐƯỢC PHÉP (S040 → …)**

```text
1. INDEPENDENT REVIEW E2 của TASK-105D implementation, do một phiên KHÁC
   thực hiện (V4.1 §12 — reviewer không được là người viết code).
   Phiên S040 cố ý KHÔNG tự review chính mình.
2. Owner quyết định H-05: data contract §6.7 ranking_method_id
   OPTIONAL → REQUIRED, hoặc quy định sentinel. Vẫn cần một phiên có thẩm
   quyền sửa data contract; S040 KHÔNG sửa.
3. CHỈ SAU (1) PASS: quyết định integration vào default theo V4.1 §8.
```

*(Cập nhật 2026-08-28, S041 — INDEPENDENT IMPLEMENTATION REVIEW #1 của
`TASK-105D`. Reviewer độc lập, KHÔNG phải tác giả implementation, KHÔNG kế thừa
PASS của `S040`. **Khối S041 dưới đây đã được SIÊU VIỆT (superseded) bởi S042
(Repair Cycle #1) và S043 (Independent Review #2); nó giữ nguyên làm LỊCH SỬ,
KHÔNG còn là trạng thái hiện hành.** Trạng thái hiện hành: khối S043 phía trên.
Verdict lịch sử của S041 giữ nguyên từng chữ, không viết lại.)*

### Trạng thái sau INDEPENDENT REVIEW #1 (S041, 2026-08-28)

```text
TASK-105D  = IMPLEMENTATION CANDIDATE — INDEPENDENT REVIEW #1 = FAIL
             REPAIR REQUIRED (1 BLOCKING)
             NOT ELIGIBLE FOR INTEGRATION / NOT DONE / NOT MERGED
             Completion Gate 32 check = FROZEN, KHÔNG sửa một byte
             GATE_SET_SHA256 = 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
                               (reviewer tái lập ĐỘC LẬP — KHỚP)
             32/32 frozen check thực thi độc lập = PASS
             A–T 20/20 PASS (bộ đối kháng riêng của reviewer)
             regression = 0 (Golden 58/2 không đổi; full 756 → 930, delta +174)
             BLOCKING = 1 (B-01)  HARDENING = 7  OUT_OF_SCOPE = 3
             budget = 2 allowed / 0 used / 2 remaining   (KHÔNG ĐỔI —
                      independent review không tiêu thụ Repair Cycle)
             Repair Cycle = CHƯA mở; khuyến nghị mở #1

TASK-105B  = FROZEN + INTEGRATED + RC-1 INTEGRATED                (không chạm)
             FilePriceProvider KHÔNG activate; diff file = RỖNG
TASK-105C  = BLOCKED / NOT AUTHORIZED                             (không chạm)
TASK-105E  = PLANNED / OUTLINE / READY GATE BLOCKED               (không mở)
TASK-108B  = BLOCKED_BY_DEPENDENCY                                (không đổi)

default branch   = KHÔNG ĐỔI
implementation   = KHÔNG bị reviewer sửa một dòng nào
app/pipeline.py  = KHÔNG ĐỔI (PendingPriceProvider vẫn là default)
Tracking         = KHÔNG CHẠM
production data  = KHÔNG TẠO
merge            = KHÔNG thực hiện
```

**HÀNH ĐỘNG KẾ TIẾP ĐƯỢC PHÉP (S041 → …)**

```text
1. Owner quyết định hướng đóng B-01:
     (a) thêm khoá file quanh chu trình đọc-lại → kiểm version → append,
         giữ nguyên data contract §11.1; HOẶC
     (b) thu hẹp phạm vi đã claim ở §11.1 + store.py docstring xuống MỘT
         TIẾN TRÌNH, kèm gate/test khẳng định biên mới (thay đổi data
         contract — cần authority riêng).
2. Repair Cycle #1 cho TASK-105D thực hiện quyết định đó + H-01.
   Sau repair: 2 allowed / 1 used / 1 remaining.
3. Independent Implementation Review #2 do một phiên KHÁC thực hiện,
   trên SHA sau repair.
4. CHỈ SAU (3) PASS: quyết định integration vào default theo V4.1 §8.
5. Song song, không chặn: phiên có thẩm quyền data contract đóng H-02 (H-05),
   HB-105D-F2-01, HB-105D-F2-02; phiên có gate authority xử lý H-07
   (32 trường Status: còn NOT_TESTED chặn DONE) TRƯỚC khi bất kỳ phiên nào
   đề xuất TASK-105D = DONE.
```

### Trạng thái sau CONTROLLED INTEGRATION (S039, 2026-08-28, `DEC-158`)

```text
TASK-105D  = READY
             NOT IMPLEMENTED / NOT DONE
             Completion Gate 32 check = FROZEN
             GATE_SET_SHA256 = 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
             32/32 NOT_TESTED  (freeze SEMANTICS, chưa test)
             implementation = NOT STARTED; NOT AUTHORIZED
                              (ràng buộc DEC-157 §2 đã thoả bằng DEC-158,
                               nhưng vẫn cần phiên cấp phép RIÊNG của Owner)
             budget = 2 allowed / 0 used / 2 remaining

TASK-105B  = FROZEN + INTEGRATED + RC-1 INTEGRATED
             NOT DONE / NOT ACTIVATED                       (không đổi; không chạm)
TASK-105C  = BLOCKED / NOT AUTHORIZED                       (không đổi)
TASK-105E  = PLANNED / OUTLINE / READY GATE BLOCKED /
             NOT IMPLEMENTED / NOT AUTHORIZED               (không đổi)
TASK-108B  = BLOCKED_BY_DEPENDENCY                          (không đổi; KHÔNG unblock)
             blocker: TASK-105C implementation, TASK-105D implementation,
                      TASK-105E, TASK-105B-Q3
```

Hợp nhất đã thực hiện:

```text
integration branch : integration/v4-1-task-105d-readiness
freeze SHA         : a53af1d193d4023fcf90bcc8e55bb874eaae19fe
phương pháp        : git merge --no-ff (ancestry-preserving); KHÔNG squash,
                     KHÔNG cherry-pick rời
conflict           : 0
merge commit       : e271c26770bb6b4cecd9d4a54aea4e12a183012c
tree == a53af1d    : YES (byte-exact)
ancestry giữ đủ    : 442404d → d3b73e5 → 9cd8714 → 7b89d4c → 1676e1d
                     → 4c9c072 → be835b1 → a53af1d
                     (gồm CẢ bằng chứng THẤT BẠI của Freeze Attempt #1
                      `7b89d4c`, verdict FAIL — không rewrite, không xoá)
production diff    : 0 dòng
```

`HARDENING` giữ nguyên, **KHÔNG repair** trong phiên này: `H-05`,
`HB-105D-F2-01`, `HB-105D-F2-02`, `HB-105D-F2-03` — vẫn `HARDENING`, vẫn mở,
re-trigger còn nguyên. `docs/spec/TASK-105D-DATA-CONTRACT.md` không bị sửa.

#### Đối chiếu trạng thái `TASK-105B` — ghi nhận khác biệt văn bản

`docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW-2.md` §16 ghi
`TASK-105B = FROZEN (DEC-153) / DONE`, kèm chú "(không đổi; không chạm)".
Bản ghi trạng thái canonical của repo (file này) ghi `TASK-105B = FROZEN +
INTEGRATED + RC-1 INTEGRATED`, **vẫn `NOT DONE`** và chưa activate — xem các
khối "Cập nhật sau CONTROLLED INTEGRATION" và "Cập nhật sau RECONCILIATION"
phía dưới, cùng `NEXT AUTHORIZED ACTION` của lineage `TASK-105B`
("…chuyển `TASK-105B` sang `DONE`" — tức `DONE` CHƯA đạt).

Phân giải, theo `CLAUDE.md` ("Trạng thái hiện tại → `PROJECT/PROJECT_PROGRESS.md`")
và `governance/core/V4_1_POLICY_FREEZE.md` §12 (`DONE` = thẩm quyền Owner /
completion authority — một phiên Freeze Finalization của `TASK-105D` **không**
có thẩm quyền ghi `DONE` cho `TASK-105B`):

```text
TRẠNG THÁI CANONICAL CỦA TASK-105B = FROZEN + INTEGRATED + RC-1 INTEGRATED
                                     NOT DONE / NOT ACTIVATED
Chữ "/ DONE" trong REVIEW-2 §16 = ghi chú phụ trợ SAI của một artifact review,
KHÔNG phải state transition, và KHÔNG có hiệu lực.
```

Artifact review **không bị sửa** — `V4.1` §10 cấm retro-fit tài liệu
governance lịch sử, và sửa nó sẽ làm đổi bằng chứng freeze. Khác biệt được
ghi tại đây làm bản ghi đối chiếu. Điều này **không** ảnh hưởng freeze verdict
của `TASK-105D`: `TASK-105B` không nằm trong gate set 32 check, và
`GATE_SET_SHA256` không đổi.

#### NEXT AUTHORIZED ACTION (sau S039)

**Controlled integration KHÔNG tự động cấp quyền implementation.**

```text
1. Một phiên IMPLEMENTATION TASK-105D được Owner cấp phép RIÊNG, chạy trên
   Completion Gate đã FROZEN (32 check, GATE_SET_SHA256 0444e58c…).
   Phiên đó phải xử lý HB-105D-F2-03 và H-05 khi chạm đúng vùng re-trigger.
   S039 KHÔNG tạo implementation branch.

Song song, không bị chặn:
   - phiên sửa data contract có thẩm quyền : H-05 + HB-105D-F2-01
   - phiên soạn Scope Lock + Completion Gate cho TASK-105E : HB-105D-F2-02
   - refreeze TASK-105C (lineage riêng 2/0/2)
   - Owner cung cấp dữ liệu thật: PublicPurchaseSourceVersion đầu tiên,
     TrackingCatalogSnapshot đầu tiên, báo cáo lịch sử Owner-confirmed
```

*(Đoạn S038 dưới đây — "1. OWNER DECISION — BRANCH DIVERGENCE" — ĐÃ ĐÓNG bởi
`DEC-158` (Option A). Giữ nguyên văn làm lịch sử:)*


**1. OWNER DECISION — BRANCH DIVERGENCE (`V4.1` §8). Đây là việc PHẢI làm
trước bất kỳ việc nào khác trên lineage `TASK-105D`**, theo `DEC-157` §2
(review point bắt buộc = ngay sau freeze verdict; verdict đã có).

```text
ahead default   : 7 commit        (ngưỡng > 10)     OK
divergence days : 0               (ngưỡng > 3)      OK
cumulative LOC  : 8.703           (ngưỡng > 5.000)  VƯỢT
  production LOC    : 0
  documentation LOC : 8.639   (18 file, +8.639 / −64)
DIVERGENCE      : INTEGRATION_DECISION_REQUIRED [ loc>5000 ]
AUTHORITY       : AUTHORITY_OK

Scope mà Option C cho phép đã DÙNG HẾT:
  (1) Gate Revision S037            ✔
  (2) MỘT Freeze Finalization retry ✔  (S038)

Owner chọn một trong ba:
  (A) integrate/merge sớm   ← RECOMMENDATION của reviewer S038
  (B) cắt scope
  (C) tiếp tục divergence có lý do + review date  (= GIA HẠN; S038 KHÔNG có
      thẩm quyền tự cấp, và lý do gốc của Option C đã hết hiệu lực)
```

Lý do recommendation (A): lý do Owner nêu khi chọn Option C ("phần việc còn
lại chỉ là gate correction + freeze") nay đã hoàn tất; production diff = 0 và
`behind = 0` nên merge là thao tác rủi ro thấp nhất, không phải giải conflict
nào; việc tiếp theo của lineage sẽ chạm production code, lúc đó rủi ro merge
chuyển từ "văn bản" sang "hành vi". Chi tiết: §14 của
`docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW-2.md`.

**2. Chỉ SAU quyết định đó**: một phiên **implementation `TASK-105D`** được
cấp phép riêng, chạy trên Completion Gate đã `FROZEN` (32 check,
`GATE_SET_SHA256 = 0444e58c…`). Phiên đó phải xử lý `HB-105D-F2-03` và `H-05`
khi chạm đúng vùng re-trigger.

**3. Song song, không bị chặn bởi hai việc trên:**

```text
- phiên sửa data contract có thẩm quyền : H-05 + HB-105D-F2-01
- phiên soạn Scope Lock + Completion Gate cho TASK-105E : HB-105D-F2-02
- refreeze TASK-105C (lineage riêng 2/0/2)
- Owner cung cấp dữ liệu thật: PublicPurchaseSourceVersion đầu tiên,
  TrackingCatalogSnapshot đầu tiên, báo cáo lịch sử Owner-confirmed
```

*(Đoạn S037, SUPERSEDED bởi S038 — giữ nguyên văn:)*

**Một phiên FREEZE FINALIZATION RETRY có thẩm quyền cho `TASK-105D`**
(`V4.1` §12). Gate revision đã xong; việc còn lại là review độc lập rồi ghi
verdict:

```text
1. Re-review TOÀN BỘ 32 gate đã sửa — KHÔNG chỉ phần diff.
2. Xác minh F-01…F-05 đã đóng thật; G04/G05/G22 nay deterministic + testable.
3. PASS  → ghi FROZEN ⇒ TASK-105D mới chuyển được READY.
   FAIL  → ghi finding; gate vẫn NOT FROZEN.
4. NGAY SAU verdict: review lại branch divergence theo DEC-157 §2
   (V4.1 §8 Option C — review point bắt buộc, không phải tuỳ chọn).
```

Đầu vào bắt buộc của phiên đó:
`docs/tasks/TASK-105D-product-identity-resolver.md` (32 khối gate),
`docs/reviews/TASK-105D-COMPLETION-GATE-CHANGE-PROPOSAL.md` (before/after),
`docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW.md` (findings gốc),
`DEC-157`.

**KHÔNG mở `TASK-105D` implementation trước divergence review point ở bước 4**,
kể cả khi freeze verdict là PASS.

*(Đoạn S036, SUPERSEDED bởi S037 — giữ nguyên văn:)*

**Một phiên GATE REVISION có thẩm quyền cho `TASK-105D`**, dùng khuôn
`COMPLETION GATE CHANGE PROPOSAL` (`governance/core/TASK_COMPLETION_GATE_STANDARD.md`), xử lý
5 BLOCKING mà S036 tìm được:

```text
F-01  DEC-156/OR-02 chưa truyền hết vào khối "Định nghĩa vận hành bắt buộc"
      của task file — khối đó vẫn liệt kê ALIAS_AID_UNIQUE TRONG tập
      auto-resolve và vẫn nói "Ba nguồn". Hệ quả: G06 và G23 mâu thuẫn.
F-02  CHECK-105D-05 là phát biểu cho phép ("có thể auto-resolve"), không phải
      assertion — không có PASS/FAIL condition.
F-03  OR-03 (actor REQUIRED, cấm gọi là authenticated) không có gate bảo vệ.
F-04  OR-01 (unified Public Purchase source) + ResolutionBinding/replay không
      có gate bảo vệ.
F-05  Catalog drift (INV-13/INV-14/INV-16) không có gate bảo vệ.
```

`F-01` và `F-02` không cần quyết định nghiệp vụ mới (hoàn tất propagation một
Owner Decision đã có; chép ngữ nghĩa quy phạm đã tồn tại vào gate).
`F-03`/`F-04`/`F-05` cần Owner chọn **hình thức**: nạp assertion vào gate hiện
có để giữ đúng 32, hay mở rộng gate set vượt 32 (thay đổi phạm vi artifact
Owner đã được thông báo — `V4.1` §10 + §12).

Sau khi áp dụng: một phiên **Freeze Finalization MỚI** re-review **toàn bộ**
gate set đã sửa (không chỉ phần diff) rồi mới ghi `FROZEN`. Chỉ sau đó
`TASK-105D` mới chuyển được `READY`, rồi mới mở một phiên implementation
riêng.

*(Đoạn S035, SUPERSEDED bởi S036 — giữ nguyên văn:)*

**Một phiên FREEZE FINALIZATION có thẩm quyền riêng** — review và freeze
Completion Gate 32 check của `TASK-105D` (`V4.1` §12: `FROZEN` chỉ được ghi
bởi một phiên Freeze Finalization; reviewer/readiness/ratification session
đều KHÔNG được ghi). Đây là blocker **duy nhất** còn lại của Ready Gate
`TASK-105D`. Chỉ sau đó `TASK-105D` mới chuyển được `READY`, rồi mới mở một
phiên implementation riêng.

Không chặn việc trên, có thể chạy song song khi Owner muốn:
- Phiên refreeze Scope/Completion Gate của `TASK-105C` — nay chạy trên
  lineage/budget của **chính nó** (`TASK-105C`, `2/0/2`, `DEC-156` §4).
- Phiên soạn Scope Lock + Completion Gate cho `TASK-105E`, biến `P00–P11`
  thành executable gate (`DEC-156` §5).
- Cung cấp dữ liệu thật: `PublicPurchaseSourceVersion` đầu tiên,
  `TrackingCatalogSnapshot` đầu tiên, bảng mapping Owner-confirmed (nếu có),
  báo cáo lịch sử Owner-confirmed cho registry.

*(Khối S034, SUPERSEDED bởi `DEC-156` ở phần Owner decisions — giữ nguyên
văn:)*

Hai việc song song, không việc nào thuộc thẩm quyền một phiên agent:

1. **Owner ratification** `OR-01`/`OR-02`/`OR-03` (`DEC-155` §4). Không có
   ba câu trả lời này thì Ready Gate của `TASK-105D` vẫn `BLOCKED`.
2. **Một phiên Freeze Finalization có thẩm quyền riêng** review và freeze
   Completion Gate 32 check của `TASK-105D` (`V4.1` §12 — reviewer/readiness
   session KHÔNG được ghi `FROZEN`).

Sau đó, và chỉ sau đó: `TASK-105D` mới có thể chuyển `READY`, rồi mở một
phiên implementation riêng.

Ba quyết định Owner khác đang chờ, không chặn hai việc trên:
- `HB-154-04` — review-budget lineage của `TASK-105C` (`DEC-155` §6), nên
  đặt ra tại phiên refreeze Scope/Completion Gate của `TASK-105C`.
- Cấp task ID cho lớp composition `P00–P11` (`DEC-155` §5, ID đề xuất
  `TASK-105E`).
- Cung cấp dữ liệu thật: bảng mapping Owner-confirmed (nếu có), báo cáo lịch
  sử Owner-confirmed cho registry, `PublicPurchaseSourceVersion` đầu tiên.

*(Đoạn cũ, SUPERSEDED — giữ nguyên văn:)* Một phiên **TASK-105D
readiness/data-contract + persistence/audit design** có authority riêng:
cung cấp catalog/version contract, pre-cutover confirmed report registry
contract, persistence/concurrency/migration plan, review và freeze Completion
Gate. Không thực hiện action đó trong phiên này.

## CAP-PRICE-RESOLUTION (Capability Registration — S045, 2026-08-28)

Đây là **đăng ký CAPABILITY**, không phải đăng ký TASK (`CAP-*`, không dùng
tiền tố `TASK-*`, không có Task Spec dưới `docs/tasks/`). Ghi theo `DEC-160`,
khung Capability-First Delivery Governance (`governance/core/
V4_1_POLICY_FREEZE.md` §16 — hiện ở dạng PROPOSED, xem
`docs/reviews/CAP-PRICE-RESOLUTION-CORE-GOVERNANCE-CHANGE-PROPOSAL.md`).

```text
CAPABILITY ID     : CAP-PRICE-RESOLUTION
BUSINESS PURPOSE  : từ một dòng bán hàng, xác định tất yếu định danh sản
                     phẩm đúng và cơ sở giá mua áp dụng, để logic nghiệp vụ
                     downstream tiêu thụ một KpiPurchasePrice đã resolve
                     kèm đầy đủ provenance.
MEMBER TASKS      : TASK-105B, TASK-105C, TASK-105D, TASK-105E
OUTSIDE CAPABILITY: TASK-108B (downstream consumer, KHÔNG phải member)
```

### END_TO_END_ACCEPTANCE

```text
END_TO_END_ACCEPTANCE = DEFINED
```

**Chuyển từ `PENDING_OWNER_DATA` → `DEFINED` tại S049 (2026-08-29).** Owner
đã cung cấp đầy đủ dữ liệu còn thiếu cho Golden Order #1 (`BH62063`) — xem
`DEC-163`. Đây là **business oracle canonicalization**, KHÔNG phải một lần
chạy production pipeline: `BH62063` CHƯA được chạy qua hệ thống hiện tại
trong S049 (đó là việc của S050, xem "CRITICAL PATH KẾ TIẾP" bên dưới).

Vertical acceptance slice (`Sales record → identity → price source →
resolved purchase price → provenance`), Owner-confirmed toàn bộ tại S049,
KHÔNG bịa:

```text
SALES_RECORD
  Order         : BH62063
  Sale date     : 2026-01-02
  Quantity      : 1
  Sell price    : 7.500.000 VND
  Discount      : 0
  Nguồn         : tests/fixtures/golden/period_2026_01.xlsx (dòng dữ liệu
                  thật, cột VERBATIM theo tests/fixtures/golden/anonymize.py
                  — chỉ customer/customer_code bị thay surrogate)

PRODUCT
  Raw label (chứng từ)         : "Máy giặt LG 10kg FV1410S4W1"
  Tracking code                : FV1410S4W1
  Public Purchase code         : FV1410S4W1
  Cross-system identity        : OWNER_CONFIRMED — YES (Tracking code và
                  Public Purchase code cùng trỏ một sản phẩm cho đúng đơn
                  BH62063; đây KHÔNG phải một quy tắc suy diễn tự động
                  "code trùng ⇒ cùng sản phẩm" cho mọi trường hợp khác —
                  chỉ là mapping Owner-confirmed riêng cho Golden Order
                  này, xem DEC-163 §"IDENTITY GUARD")
  Expected canonical identity  : TRACKING:FV1410S4W1 (Owner-confirmed,
                  KHÔNG phải kết luận kỹ thuật của TASK-105D)

PRICE_SOURCE
  ExpectedPriceSource (Owner)  : "Tồn"
  ApplicablePriceDate          : 2026-01-02
  TECHNICAL_SOURCE_MAPPING     : UNRESOLVED — "Tồn" là nhãn nghiệp vụ Owner
                  dùng để mô tả nguồn giá áp dụng; repo hiện KHÔNG có mapping
                  kỹ thuật đã xác nhận từ "Tồn" sang một price provider cụ
                  thể (không phải phist NCC, không phải Public Purchase,
                  không phải inv.cong mặc định — KHÔNG suy diễn). Việc xác
                  định technical path cho "Tồn" thuộc phạm vi S050 (AS-IS
                  trace), KHÔNG phải S049.
  Public Purchase fallback     : AUTHORIZED bởi Owner — CHỈ khi preferred
                  price path (nguồn "Tồn") không có giá phù hợp áp dụng.
                  Public Purchase KHÔNG phải preferred/default source cho
                  Golden Order #1.
  ExpectedPurchasePrice        : 7.000.000 VND
                  (SOURCE_DISPLAY_VALUE Owner cung cấp = 7.000,
                  SOURCE_UNIT = THOUSAND_VND → normalize một lần duy nhất
                  thành 7.000.000 VND — KHÔNG nhân ×1000 lần thứ hai)

EXPECTED_RESOLUTION
  ExpectedKpiPurchasePrice     : 7.000.000 VND

MANUAL_ORACLE
  Công thức canonical (docs/tasks/TASK-108B-eligible-costs-owner-definition.md:1040,
  xác nhận cuối cùng của Owner, không đổi sau đó trong toàn file):

    EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity − Discount
                       = (7.500.000 − 7.000.000) × 1 − 0
                       = 500.000 VND

  ExpectedEligibleKpiProfit    : 500.000 VND

PROVENANCE (kỳ vọng, human-readable)
  BH62063
  → "Máy giặt LG 10kg FV1410S4W1"
  → TRACKING:FV1410S4W1
  → NCC/nguồn: "Tồn" (technical mapping UNRESOLVED — xem trên)
  → applicable price tại 2026-01-02
  → KpiPurchasePrice = 7.000.000 VND
  → EligibleKpiProfit = 500.000 VND
```

```text
OWNER_DATA_COMPLETE      = YES
BUSINESS_ORACLE_DEFINED  = YES
```

`END_TO_END_ACCEPTANCE` là **hạt giống nghiệp vụ** cho cơ chế Golden
Baseline hiện có, KHÔNG phải một framework acceptance song song — khi
authority triển khai cho phép, case này NÊN trở thành một Golden case thực
thi được qua đúng `GOLDEN_BASELINE_STRATEGY`.

**CURRENT VERTICAL GOLDEN = `BH62063`.** Business oracle =
`EligibleKpiProfit` 500.000 VND. Mọi implementation session tiếp theo trên
critical path production hiện tại (bao gồm bất kỳ session nào chạm
`CAP-PRICE-RESOLUTION`) phải khai báo `VERTICAL_SLICE_IMPACT` (trạng thái
Golden trước/sau, và session đó có đưa `BH62063` tiến gần oracle hay
không) trong bàn giao session của mình.

**CRITICAL PATH KẾ TIẾP (sau S049):** `RUN BH62063 THROUGH CURRENT SYSTEM
AS-IS → determine FIRST_FAILING_BOUNDARY` (session đề xuất: `S050 —
GOLDEN ORDER #1 AS-IS VERTICAL TRACE`). Đây là trace, KHÔNG phải
implementation — session đó CHƯA được phép tự gán tiếp theo là
`TASK-105C`, `TASK-105E`, hay `TASK-108B`; lựa chọn đó chỉ được xác nhận
sau khi AS-IS execution đã chứng minh boundary thật.

### Task Registry — bằng chứng BEFORE/AFTER (S045)

```text
SET A — REGISTERED_TASK_SET (task ID có "= STATUS"/"Status:" tường minh
trong các khối trạng thái của file này — KHÔNG phải grep tự do mọi chuỗi
khớp pattern TASK-*, brief §B8 cấm cách đo đó):
  TASK-101, TASK-105, TASK-105B, TASK-105C, TASK-105D, TASK-105E, TASK-106,
  TASK-107, TASK-108A-1, TASK-108B, TASK-110, TASK-GOLDEN-BASELINE-001,
  TASK-V4-ADOPTION
  BEFORE = 13   AFTER = 13 (không đổi — S045 chỉ cập nhật narrative của
  TASK-105D đã có sẵn, không thêm task ID nào)

SET B — TASK_SPEC_SET (docs/tasks/*.md) BEFORE = 22   AFTER = 22 (không đổi)

new_registered_task_ids                = 0
proposals_created                      = 0
proposal_names                         = []
owner_assignment_required_entries_added = 0
```

Ghi chú phương pháp: một phép đo sơ bộ bằng `grep -oE "TASK-[A-Z0-9]+(-
[A-Z0-9]+)*"` (đúng kiểu grep tự do brief §B8 cấm) từng cho BEFORE=58/
AFTER=59 — chênh lệch là `TASK-105D-RC-1`, một **repair-cycle identifier**
(đã tồn tại từ `S042` trong `PROJECT/REVIEW_BUDGET_LEDGER.md`), không phải
một task ID mới. Đây chính là false positive mà §B8 cảnh báo; SET A ở trên
dùng định nghĩa đúng (task ID có khai báo trạng thái), không phải regex tự
do.

### OWNER_ASSIGNMENT_REQUIRED

Không có mục nào được ghi trong phiên này — không hạng mục công việc mới
nào với ownership mơ hồ được phát hiện (mọi finding rà lại ở `TASK-105D` đã
có owner tường minh theo re-trigger gốc của chúng).

### Absorption

```text
absorption_items_identified = 0
ABSORPTION_LIMIT_REACHED    = KHÔNG kích hoạt (không có gì để hấp thụ trong
                               phiên này)
```

### Capability-Level Repair Budget (PROPOSED, CHƯA ADOPTED)

Xem `PROJECT/REVIEW_BUDGET_LEDGER.md` → "Capability-Level Repair Budget —
CAP-PRICE-RESOLUTION" cho reconstruction đầy đủ. Tóm tắt:

```text
capability_repair_cycles_allowed (Owner PROPOSAL)  : 4
capability_repair_cycles_used                       : 2
                      (TASK-105B-RC-1 + TASK-105D-RC-1)
capability_repair_cycles_remaining (nếu ADOPTED)     : 2
migration_status                                     : PROPOSED
```

Ngân sách per-task hiện hành (`TASK-105B` 2/1/1, `TASK-105C` 2/0/2,
`TASK-105D` 2/1/1, `TASK-105E` 2/0/2) **giữ nguyên authoritative** cho tới
khi `migration_status = ADOPTED` bằng một Owner Decision riêng.

### Capability Governance Verdict

```text
CAPABILITY_GOVERNANCE_VERDICT = PROPOSED_PENDING_CORE_AUTHORITY
```

CORE-eligible rule (capability-first sibling-proliferation control,
absorption limit, capability repair-budget semantics) ở dạng canonical
governance change proposal tại
`docs/reviews/CAP-PRICE-RESOLUTION-CORE-GOVERNANCE-CHANGE-PROPOSAL.md`,
CHƯA merge vào `governance/core/V4_1_POLICY_FREEZE.md` (0 byte thay đổi).

Bằng chứng đầy đủ: `DEC-160` trong `PROJECT/PROJECT_DECISIONS.md`,
`docs/sessions/S045-task-105d-h07-reconciliation-and-capability-governance.md`
phần B.

## Hai Track Song Song

Repo này chứa **hai track công việc độc lập**, cả hai đều canonical, cả hai
đều track trong chính file này:

- **Track A — Sản phẩm Tín Phát** (phần "Tóm tắt dự án" → "Session tiếp
  theo" ngay bên dưới) — xây dựng công cụ báo cáo kinh doanh. Đây là track
  đang hoạt động chính (GATE-00 đang chờ owner duyệt).
- **Track B — Governance Remediation** (mục "Track Governance — Bảo Trì Nền
  Tảng (PHASE-GOV)" phía dưới) — sửa chữa chính khung governance của repo.
  Chạy song song, không chặn Track A trừ khi ghi rõ dependency.

**Bản dễ hiểu cho người ngoài dự án:** `PROJECT/LO_TRINH_DE_HIEU.md` — cùng
một lộ trình Track A, viết lại không dùng thuật ngữ kỹ thuật, dành cho chủ
dự án/quản lý không rành code. File đó KHÔNG tự động đồng bộ — **bất kỳ
session nào sửa roadmap Track A trong file này cũng phải cập nhật file đó
theo, cùng một lần sửa** (xem `governance/core/00_SESSION_ORCHESTRATION.md`
→ "Giao thức Đóng Phiên").

## Tóm tắt dự án

Project:
Tín Phát — Công cụ tự động tạo Báo cáo Kinh doanh

Objective:
Thay thế việc lắp ráp thủ công hằng tháng file `Báo cáo Kinh doanh 2026.xlsx`
bằng một công cụ nạp sổ bán hàng thô từ ERP, phân loại nguồn đơn của từng đơn
hàng, tính lợi nhuận kế toán và lợi nhuận KPI tách riêng, quy đổi doanh thu qua
hai bucket độc lập PERSONAL/ADS, tạo Summary tháng và năm, và cho nhiều người
xem/sửa dữ liệu hằng ngày trước khi xuất `.xlsx`.

Project Type:
NEW (ứng dụng xây mới, thay thế một quy trình dựa trên bảng tính)

Profile:
PRODUCT

Last Updated:
2026-08-28 (`DEC-156`, S035 — Owner Ratification: OR-01/OR-02/OR-03,
HB-154-04 Option B, cấp `TASK-105E`; production code không đổi. Trước đó
cùng ngày: `DEC-155`/S034 — TASK-105D readiness data contract; `DEC-154`/S032
— Product Identity & Purchase Price Resolution reconciliation).

Historical prior update:
2026-08-23 (S021 — **Independent Review #5 FAIL, 4 finding, đã sửa toàn bộ
bằng ARCHITECTURE REPAIR**, không phải một vòng patch cục bộ. Audit trước khi
code chỉ ra cả bốn finding là bốn biểu hiện của **một** root cause: validation
tái tạo lại các sự thật production đã biết thay vì nhận lại chúng — và audit
tìm thêm một drift thứ năm reviewer chưa nêu (F3 khớp prefix trên chuỗi đã
normalize trong khi production khớp trên chuỗi thô). Đã **xóa** nguồn sự thật
thứ hai (`select_effective_record`, `_record_key`, vòng khớp prefix riêng);
`EmployeeMapper` nay là nguồn duy nhất và trả `RecordRef` — danh tính của bản
ghi đã load, nên collision là **bất khả**. `MappingFinding` mất hẳn trường
`details`; `ReviewItem` mất hẳn field `affected_count`/`source_row` — tất cả
dẫn xuất từ `RowProvenance`. Ba Human Decision (**HD-110-06/07/08**) ghi thành
**DEC-132**. **330/330 test**, 179 mới so với baseline `c7a1b24`, 0 regression;
L1/L2/L3 chứng minh 0 dịch chuyển nghiệp vụ.

*(Đoạn trên là bản ghi lịch sử của vòng repair #5 — **SUPERSEDED**. Trạng
thái hiện tại nằm ngay dưới đây và ở "Trạng thái Task hiện tại".)*

**TRẠNG THÁI HIỆN TẠI (sau integration V4.1-1):**

```
R1-A1    = FROZEN        (DEC-139; Independent Review PASS — ELIGIBLE_FOR_FREEZE
                          tại reviewed SHA a85397106b81799d149d98e71a7fcfd5bc8963ad;
                          Freeze Finalization 01a03b08ab6fc21b6b9ef3eeab5dfa1d692a8713)
R1-A     = NOT FROZEN    (không suy diễn tăng theo)
R1       = NOT FROZEN
TASK-110 = NOT DONE      (đã MERGED vào nhánh mặc định tại V4.1-1, nhưng
                          MERGE KHÔNG ĐỒNG NGHĨA DONE)
CHECK-110-16 = REQUIRED · BLOCKED · Gate Class = POST_MERGE_PRODUCTION_ACCEPTANCE
               (DEC-141; thiếu file thô production, không synthetic PASS)
TASK-110 repair budget = EXHAUSTED_PRE_V4.1, remaining = 0
R1-A2 → R8 = OWNER_EXTENSION REQUIRED — không unit nào tự mở
```

**TASK-108B (sau DEC-143 + DEC-144 / `OD-108B-01` + `OD-108B-02`, 2026-08-27):**

```
SEMANTIC_DEFINITION   = APPROVED   (đầy đủ — formula đã được Owner xác nhận, DEC-144 §1)
IMPLEMENTATION        = BLOCKED_BY_DEPENDENCY
BLOCKED_BY_DEPENDENCY = [ 1. TASK-105C implementation thật (Scope Lock +
                             Completion Gate đã FROZEN, DEC-152 — kèm
                             TASK-105B làm dependency cứng, chưa DONE),
                          2. product identity mapping (product_raw Reports
                             ↔ <MÃ> Tracking — dependency mới đặt tên tại
                             DEC-152 §5, chưa mở task, cấm fuzzy matching),
                          3. TASK-105B-Q3 (dòng phụ) ]
                          — BỎ (ĐÃ ĐÓNG bởi DEC-151/DEC-152): "chủ dự án
                            chốt trường nào là AccountingPurchasePrice"
                            (đã chốt = HistoricalVendorPrice từ phist);
                            "tầng capture/export bất biến chưa tồn tại"
                            (KHÔNG còn bắt buộc trong Phase 1); "chưa xác
                            định kiến trúc RTDB" (đã audit xong); hai câu
                            hỏi filtering Q1/Q2 (NCC retired/MIN_LOAI hồi
                            tố, outlier threshold hồi tố — CLOSED, DEC-152
                            §1/§2). KHÔNG còn câu hỏi nghiệp vụ nào chờ
                            Owner cho nguồn giá lịch sử.
IN-SCOPE MECHANISM    = [ confirmed-adjustment source khai báo rỗng ] ← nội bộ TASK-108B,
                          KHÔNG phải blocker chờ Owner (DEC-144 §5)
EligibleCosts         = {} (CLOSED EMPTY SET — không phải fallback = 0)
DeliveryCost          = NOT ELIGIBLE FOR NOW
OtherKpiAdjustment    = 0 BY DEFINITION
EligibleKpiProfit     = (SellPrice − KpiPurchasePrice) × Quantity − Discount  ✅ XÁC NHẬN
KpiPurchasePrice      = AccountingPurchasePrice + ConfirmedKpiPurchaseAdjustment (có record)
                      = AccountingPurchasePrice (absence ĐÃ XÁC ĐỊNH; provenance
                        Config:NoConfirmedAdjustment) — DEC-144 §2
                      = None/Pending khi UNKNOWN / SOURCE_UNAVAILABLE / LOOKUP_FAILURE
                        (tuyệt đối không thành 0 — DEC-144 §3)
effective_risk        = HIGH   (Golden KHÔNG hạ bậc — V4.1 §4.1)
repair budget         = 2 allowed / 0 used / 2 remaining (lineage TASK-108B)
```

`SEMANTIC_DEFINITION = APPROVED` **không** đồng nghĩa `IMPLEMENTATION = READY`.
Không hardcode dữ liệu để vượt blocker, không synthetic PASS.

**TASK-105B / TASK-105C — sau audit chéo repo (DEC-147, 2026-08-27).**
Đã audit repository vận hành hệ thống giá (`hoangvinhkta-creator/Tracking` @
`d177363a`) và đối chiếu với contract `PriceProvider`. Bốn trong năm câu hỏi
của `DEC-146` nay **trả lời được bằng code**.

```
RTDB có lưu lịch sử?      CÓ — nhánh `phist/<mã>/<NCC>/<YYYY-MM-DD>`,
                          append theo ngày, chỉ ghi khi giá ĐỔI.
                          Chế độ thật = HYBRID (ảnh chụp `board` + lịch sử `phist`).
⇒ BLOCKING ARCHITECTURE GAP có điều kiện của DEC-146 §3: KHÔNG KÍCH HOẠT.

NHƯNG — SOURCE MISMATCH:
  loại giá CÓ lịch sử  = giá NCC BÁO (báo giá nhà cung cấp trong ngày)
  loại giá Reports CẦN = giá thực nhập (`inv.<slot>.gia`/`.lo`) — KHÔNG có
                         lịch sử (hai ô cuốn chiếu `cu`/`moi`, ghi bằng `set()`
                         đè cả nhánh)
```

```
SEMANTIC_READINESS (Q1/Q2/Q3, DEC-145)  = READY — KHÔNG đổi, vẫn đúng
IMPLEMENTATION (FilePriceProvider)      = READY về kỹ thuật (gỡ "TẠM DỪNG"),
                                           BLOCKED_BY [ chủ dự án chốt trường
                                           nào là AccountingPurchasePrice ]
effective_risk  = HIGH   (data path: Price → KpiPurchasePrice → CR → KPI/lương)
repair budget   = 2 allowed / 0 used / 2 remaining (lineage TASK-105B, không đổi)
```

Kiến trúc khuyến nghị (`DEC-147` §8): **OPTION C giao hàng bằng định dạng
OPTION D** — một tầng capture ghi price history **bất biến**, xuất ra file 4
cột đúng `DEC-145` §4, Reports đọc bằng `FilePriceProvider`. Không đọc thẳng
RTDB từ `app/modules/`: sẽ kéo mạng vào Phase 1 (va `ADR-101`) và đặt phép
nhân 1.000 sai tầng (va `ADR-103` §2 — RTDB lưu theo **nghìn đồng**).
`FilePriceProvider` vì vậy **được đề cử trở lại làm production path** — đảo lại
nghi vấn của `DEC-146` §6, không huỷ gì của `DEC-145`.

Năm điều kiện bắt buộc kèm theo lịch sử `phist` (`DEC-147` §3): độ mịn chỉ tới
**ngày**; `0` là sentinel **hết hàng** → phải map thành gap → `Pending`, tuyệt
đối không thành `purchase_price = 0`; không có mốc trước ngày bật tính năng;
**lịch sử SỬA ĐƯỢC** (bốn đường xoá/dời/mồ côi/lệch đang chạy) nên phải đóng
băng mới thoả `DEC-121`; không API nào đưa `phist` ra ngoài.

**Cập nhật sau `DEC-148` (2026-08-27, cùng ngày, phiên tiếp theo): chủ dự án
đã chỉ định trường.** `AccountingPurchasePrice = inv.cong` (giá nhập
**công khai**) — không phải `inv.gia` (private) hay `phist` (giá NCC báo).
Đã audit đầy đủ write/read/lifecycle của `inv.cong` bằng bằng chứng code, xác
nhận cả bốn semantics chủ dự án nêu đều khớp. Kết luận mới, **quan trọng hơn
bản thân việc chọn field**:

```
inv.cong KHÔNG có lịch sử, và KHÔNG có bất kỳ đảm bảo giữ dữ liệu nào theo
thời gian — NO GUARANTEED DELAY WINDOW.
```

Trong ngày: overwrite **tức thời** (sửa tay `invSetGia()`, hoặc tải lại file
`invApply()`) — không version, không khoá "đã dùng ở báo cáo". Qua ngày
(`invNextDay()`): giữ đúng **một bước**, và bước đó do **nút bấm thủ công**,
không nằm trong lịch cron của Worker — có thể 0 lần/tuần hoặc nhiều lần/ngày.
`backup` không chứa nhánh `inv` và tự xoá sau 10 bản; `hist` không mang giá
trị số. ⇒ Cửa sổ tối thiểu đạt được trên thực tế = **0**.

Hệ quả: capture layer **không còn là việc làm sau** — mỗi ngày trì hoãn là
dữ liệu ngày đó có nguy cơ mất vĩnh viễn. Chi tiết đầy đủ: `DEC-148`,
`docs/sessions/S025-task-105c-public-purchase-price-cong-audit.md`,
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần VII.

*(5 câu hỏi ở trên — DEC-147/DEC-148 — SUPERSEDED bởi `DEC-151`, xem ngay
dưới. Giữ lại nguyên văn làm bản ghi lịch sử, không xoá.)*

**TASK-105C — `RTDBPriceProvider` / capture layer:**

```
DISCOVERY      = COMPLETE (S024/DEC-147, S025/DEC-148, S026/DEC-149,
                            S027/DEC-150, S028/DEC-151, S029/DEC-152)
SEMANTIC_DEFINITION = COMPLETE, SCOPE_LOCK = COMPLETE,
IMPLEMENTATION = READY  →  xem "Cập nhật sau DEC-152" ngay dưới

^^^ SUPERSEDED BY DEC-154 (2026-08-28) — KHÔNG còn đúng.
    Trạng thái hiện hành: TASK-105C = BLOCKED / NOT AUTHORIZED;
    SCOPE_LOCK = REOPENED_BY_DEC-154;
    COMPLETION_GATE = CHANGE_PROPOSAL_OPEN, NOT FROZEN.
    Khối trên giữ nguyên làm bản ghi lịch sử (V4.1 §10).
    Current state: "Current Price Architecture — DEC-154" ở đầu file.
```

*(Khối `CONFLICT DETECTED`/`RTDBPriceProvider readiness` ở trên — SUPERSEDED
bởi `DEC-151`, xem ngay dưới. Giữ lại nguyên văn làm bản ghi lịch sử.)*

**Xác minh popup "Lịch sử giá" (S027/DEC-150, audit fact).** Owner cung cấp
bằng chứng UI: popup biểu đồ giá theo ngày mở từ ô Min trên tab Bảng giá.
Đã audit trực tiếp `openPhist()`/`loadPhist()`/`renderPhist()`
(`public/index.html:6218-6314`). Kết luận: popup là **vendor-price history
thuần** (đọc `phist/<mã>`, một đường mỗi NCC) — KHÔNG có bất kỳ tính toán
Min nào, KHÔNG đọc `inv.cong`/`tp.ton`, KHÔNG có persistent Min history
record nào tồn tại ở bất kỳ đâu trong repo B. Kết luận này **vẫn đúng và
càng có ý nghĩa hơn** sau `DEC-151`: nó xác nhận `phist` (không phải
`_c.min`) đúng là nguồn duy nhất có bằng chứng lịch sử — đúng nguồn mà
`DEC-151` chọn làm nền cho `HistoricalKpiPurchasePrice`.

---

**Cập nhật sau `DEC-151` (2026-08-27, cùng ngày, phiên tiếp theo) — OWNER
DECISION, đóng `CONFLICT DETECTED` bằng THU HẸP PHẠM VI, không phải bằng
chọn (A)/(B).** *(Nguồn giá/scope reduction ở khối này vẫn ĐÚNG và CURRENT.
Riêng trạng thái Q1/Q2 "BLOCKED_BY" bên dưới — SUPERSEDED bởi `DEC-152`:
cả hai đã CLOSED. Xem "Cập nhật sau `DEC-152`" phía dưới khối này để có
trạng thái hiện hành.)*

Chủ dự án xác nhận: Reports **KHÔNG** cố tái dựng `_c.min` lịch sử. Nguồn
giá lịch sử **DUY NHẤT** cho `AccountingPurchasePrice`/`KpiPurchasePrice`
là `phist/<mã>/<NCC>/<YYYY-MM-DD>`:

```
Price(NCC, D)                = record gần nhất ngày <= D
HistoricalVendorPrice(mã, D) = MIN qua mọi NCC có Price(NCC,D) xác định,
                                loại 0-sentinel (hết hàng)
KpiPurchasePrice(mã, D)      = HistoricalVendorPrice nếu xác định được,
                                else Pending — KHÔNG suy đoán, KHÔNG lấy
                                giá hiện tại, KHÔNG nearest/latest khác
```

`inv.cong`: **KHÔNG** áp ngược cho quá khứ, **KHÔNG bắt buộc** xây lịch sử
trong Phase 1. `MarketMinHistory` (capture `_c.min`): **KHÔNG bắt buộc**
trong Phase 1. `DEC-149` OPTION B (capture cả hai) **không còn là khuyến
nghị hiện hành** — nó phục vụ một mục tiêu (tái dựng đúng `_c.min`) mà
quyết định này vừa loại bỏ; số đo ở `DEC-149` vẫn đúng, chỉ mục tiêu cần nó
đã đổi.

Pending khi không đủ căn cứ lịch sử là **hành vi chủ đích** (tần suất thấp,
chi phí xử lý tay thấp hơn xây capture layer đầy đủ) — đúng nguyên tắc
`DEC-103`. Manual resolution phải explicit, có provenance, gắn đúng
dòng/đơn/mã, không rewrite `phist`, không backdating.

```
TASK-105B  = KHÔNG ĐỔI — contract §38 (DEC-145) vẫn đúng
TASK-105C  IMPLEMENTATION = OWNER_DECISION_REQUIRED (hẹp lại, chỉ 2 câu hỏi)
           BLOCKED_BY = [ Q1: NCC retired/MIN_LOAI có giá tại D (trước khi
                             trạng thái đó có hiệu lực) có tính vào
                             HistoricalVendorPrice(mã,D) không?
                          Q2: bộ lọc giá bất thường (NGUONG_BAT_THUONG,
                             thêm 24/08/2026) có áp dụng hồi tố cho mốc
                             TRƯỚC ngày đó không? ]
           Q1/Q2 CHỈ ảnh hưởng độ chính xác, KHÔNG chặn mở implementation
           — mặc định an toàn (không lọc, đúng y semantics đã chốt) dùng
           được trong lúc chờ, miễn ghi rõ provenance là giả định tạm.
           RTDBPriceProvider readiness = NEEDS_SCHEMA_CHANGE, KHÔNG đề cử
           — thay bằng đề xuất tên HistoricalVendorPriceProvider (đọc
           TRỰC TIẾP phist, không qua _c.min) — audit fact, đặt tên chính
           thức là việc của implementation session
TASK-108B  BLOCKED_BY = [ Q1/Q2 (không chặn mở), TASK-105B-Q3 ]
           KHÔNG còn BLOCKED_BY: kiến trúc nguồn giá; field nào là
           AccountingPurchasePrice (đã chốt); capture layer; MarketMinHistory
```

Audit hẹp bắt buộc trong phiên (`DEC-151` §7,
`docs/sessions/S028-task-105c-historical-kpi-price-scope-reduction.md`):
`phist` **đủ** cho `HistoricalVendorPrice` deterministic theo đúng semantics
trên, **không cần** giả định `NCC_RETIRED`/`NCC_MIN_LOAI`/
`NGUONG_BAT_THUONG` hiện tại áp cho lịch sử — vì semantics đó **cố ý không
đi qua** các input không-versioned đó (`buildSync()` ghi `phist` bất kể
trạng thái loại trừ, `public/index.html:5100-5203`). Q1/Q2 là câu hỏi
NGHIỆP VỤ về việc có nên LỌC BỚT theo các danh sách đó hay không — không
suy ra được từ code, để ngỏ đúng yêu cầu "không tự suy ra".

Rủi ro mang theo vào implementation: `phist` vẫn sửa/xoá được (`DEC-147`
§54 R4) — `HistoricalVendorPriceProvider` phải đóng băng/snapshot dữ liệu
đã dùng cho một báo cáo cụ thể, không đọc `phist` sống mỗi lần chạy lại;
`NCC_ALIAS` không hồi tố (nợ kỹ thuật nhỏ, xem `S028` V-03/V-04).

Chi tiết đầy đủ: `DEC-151`,
`docs/sessions/S028-task-105c-historical-kpi-price-scope-reduction.md`,
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần X.

*(Khối "CONFLICT DETECTED (DEC-149 §71)" → "Khoá sản phẩm..." ngay dưới
đây — bản ghi TỪ DEC-149, TRƯỚC `DEC-151`/`DEC-152` — SUPERSEDED. Giữ
nguyên văn làm lịch sử; trạng thái CURRENT nằm ở "Cập nhật sau `DEC-152`"
phía dưới cùng của khối này.)*

**`CONFLICT DETECTED` (DEC-149 §71) — chưa giải quyết, không tự chọn.**
`_c.min` (Min hiển thị trên board) tính bằng `min(giá NCC rẻ nhất còn hàng
đã lọc outlier, tp.ton)` — `tp.ton` chính là `inv.cong` (`DEC-148`). Nghĩa là
`cong` **luôn** được xét và **thắng** bất cứ khi nào rẻ hơn giá NCC, kể cả
khi NCC hoàn toàn còn hàng và "có căn cứ" theo đúng nghĩa Owner dùng. Đây
KHÔNG phải quy tắc ưu tiên tuần tự (Min trước, cong chỉ khi Min bất khả) mà
Owner mô tả — `cong` là một input hoà tan bên trong cùng công thức, không
phải một candidate dự phòng độc lập. Cần Owner xác nhận: (A) dùng đúng
`_c.min` như đang hiển thị (chấp nhận cong lai bên trong), hay (B) cần một
field MỚI tách riêng vendor-only Min — hai lựa chọn cho ra hai kết quả khác
nhau ở chính những mã mà `cong` tình cờ rẻ hơn giá NCC.

**`inv.cong` là ứng viên đã chốt (DEC-148) — nhưng chưa có một byte lịch sử
nào, và `_c.min` cũng vậy.** `_c.min` tái tính/ghi đè trên đúng cùng trigger
mà `inv.cong` đã xác nhận NO GUARANTEED DELAY WINDOW (`DEC-148` §8) — không
có gì trong cơ chế `_c` làm window này khá hơn. Formula sống **không bao
giờ** đọc `phist` (0 hit khi grep toàn bộ `price-engine/`/`src/index.js`) —
Historical Replay = **C, chỉ current snapshot, không replay được**, thiếu
bốn lớp cùng lúc: `_c` không có history riêng; `tp.ton`/`inv.cong` không có
lịch sử; danh sách loại trừ NCC (`NCC_RETIRED`/`NCC_MIN_LOAI`) và ngưỡng lọc
outlier (`NGUONG_BAT_THUONG=0.3`) là hằng số mã nguồn, không versioned.

Đề xuất kiến trúc: **OPTION B** — capture `MarketMinPrice` (`_c.min`) VÀ
`PublicPurchasePrice` (`inv.cong`) độc lập, để quyết định "dùng số nào"
chuyển sang tầng đọc (Reports `PriceProvider`) thay vì khoá cứng ở tầng
capture — không cần capture lại nếu Owner đổi ý giữa (A)/(B) ở trên. Mỗi
lượt capture bắt buộc ghi kèm `_ANC` + `NGUONG_BAT_THUONG` làm provenance.
Chi tiết đầy đủ: `DEC-149`,
`docs/sessions/S026-task-105c-market-min-price-path-audit.md`,
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần VIII.

Khoá sản phẩm (đóng câu hỏi cũ số 3): RTDB **đã có mã ổn định** —
`normCode(mã)` = `toUpperCase()` + bỏ mọi ký tự ngoài `[A-Z0-9]`, rồi qua
`aliasOf()`. Nhưng Reports dùng `product_raw` = **câu tên hàng trên chứng từ**
⇒ **cần mapping**, không khớp trực tiếp. Đáng chú ý: repo B đã **thử** rút mã
từ tên hàng bằng máy (`extractCode()`) và **bỏ hẳn** vì đoán sai trên tài sản
thật, thay bằng bảng `inv.map` do người duyệt — tiền lệ production ủng hộ đúng
lệnh cấm fuzzy matching của `OD-105B-01` §B. `DEC-145` §2 **không đổi**.

*(Hết khối SUPERSEDED. Trạng thái CURRENT — cập nhật sau `DEC-152` — nằm
ngay dưới đây.)*

---

**Cập nhật sau `DEC-152` (2026-08-27, cùng ngày, phiên tiếp theo) — OWNER
DECISION cuối: đóng Q1/Q2 + Scope Lock/Completion Gate cho `TASK-105C`.**

```
Q1 — NCC retired/MIN_LOAI hồi tố  = CLOSED. Trạng thái NCC HIỆN TẠI KHÔNG
     áp ngược. Giá lịch sử hợp lệ tại D vẫn là candidate.
Q2 — Outlier threshold hồi tố     = CLOSED. NGUONG_BAT_THUONG hiện tại
     KHÔNG áp ngược. Phase 1 = MIN qua mọi candidate hợp lệ (loại sentinel
     0), không lọc gì thêm.
```

```
TASK-105C
    SEMANTIC_DEFINITION = COMPLETE
    SCOPE_LOCK           = COMPLETE
    IMPLEMENTATION        = READY
    Canonical spec: docs/tasks/TASK-105C-historical-vendor-price-provider.md
    (Scope Lock + Completion Gate 20 check, CHECK-105C-01…20, FROZEN)
    Dependency CỨNG: TASK-105B (FilePriceProvider) — CHƯA DONE, phải
    implement trước/cùng lúc (HistoricalVendorPriceProvider compose nó).
    Dependency riêng, CHƯA MỞ TASK: product identity mapping
    (product_raw ↔ <MÃ> Tracking) — không chặn implement/test provider
    (dùng <MÃ> tổng hợp), CHẶN kết quả không-Pending ở quy mô trên dữ liệu
    thật. KHÔNG được tự vá bằng fuzzy matching (OD-105B-01 §B, tiền lệ
    extractCode() thất bại).
```

Kiến trúc thực thi (quyết định kỹ thuật của phiên, không phải Owner
Decision): `HistoricalVendorPriceProvider` **compose** `FilePriceProvider`
(đọc file snapshot 4-cột do một script export sinh ra), thay vì viết lại
validation. Script fetch mạng (`tools/pricing/`) tách hẳn khỏi
`app/modules/pricing/`, giữ đúng ranh giới `ADR-101`. Snapshot **bất
biến**, không ghi đè — một report ghim vào đúng một `capture_id`, miễn
nhiễm với việc `phist` bị sửa sau đó (`DEC-147` §54 R4).

`DEC-149` OPTION B (capture cả `_c.min` lẫn `inv.cong`) **chính thức
không còn áp dụng** — thay bằng kiến trúc compose `FilePriceProvider` ở
trên, ít thay đổi hơn và không cần capture `_c.min` dưới bất kỳ hình thức
nào.

```
TASK-108B  BLOCKED_BY = [ 1. TASK-105C implementation (bao gồm TASK-105B
                          làm dependency cứng); 2. product identity mapping
                          (dependency mới, chưa mở task); 3. TASK-105B-Q3 ]
           KHÔNG còn BLOCKED_BY: bất kỳ câu hỏi filtering/kiến trúc/field-
           selection nào — toàn bộ đã đóng qua DEC-147 → DEC-152.
```

Chi tiết đầy đủ: `DEC-152`,
`docs/tasks/TASK-105C-historical-vendor-price-provider.md`,
`docs/sessions/S029-task-105c-final-decision-scope-lock.md`.

`TASK-105B-Q3` (chính sách zero-price dòng phụ) **không đổi, vẫn BLOCKED** bởi
`TASK-103`/enumeration — độc lập hoàn toàn với nguồn giá. Audit evidence đang
làm dở (30 raw label từ `evidence.json`) **không mất**, tạm dừng theo yêu cầu
chủ dự án, tiếp tục được ở phiên sau.

Q1 = khoảng ĐÓNG `[from, to]`, overlap/>1 record mở = `INVALID PRICE MASTER`,
gap → `Pending`, cấm latest/nearest/current. Q2 = chuẩn hoá NFC → strip →
collapse → casefold; đã có sẵn `fold()` tại `app/modules/validation/text.py`,
kiểm chứng đúng trên 3 ví dụ Owner và trên 528 dòng production.

**Cập nhật sau IMPLEMENTATION (2026-08-28, phiên "TASK-105B —
IMPLEMENTATION").** `FilePriceProvider` (`app/modules/pricing/file_price_provider.py`,
**MỚI**) đã viết xong đúng contract §38/`DEC-145`, tự kiểm tra (self-verify)
đầy đủ:

```
TASK-105B  IMPLEMENTATION       = COMPLETE (code-level)
           SELF_VERIFICATION    = PASS — 17/17 REQUIRED Completion Gate
                                  check PASS (CHECK-105B-01..17, gate
                                  frozen tại phiên này —
                                  docs/tasks/TASK-105B-file-price-provider.md)
           INDEPENDENT_REVIEW   = PASS — hai artifact E2 độc lập, song song
                                  (Review A tại
                                  docs/reviews/TASK-105B-INDEPENDENT-REVIEW-1.md,
                                  Review B archived tại
                                  docs/reviews/archive/TASK-105B-INDEPENDENT-REVIEW-1-B-file-price-provider-review-negpxw.md),
                                  cùng target c22cef8, cùng verdict
                                  PASS — ELIGIBLE_FOR_FREEZE, đã reconcile
                                  (2026-08-28) —
                                  docs/reviews/TASK-105B-INDEPENDENT-REVIEW-RECONCILIATION.md
           REVIEW_EVIDENCE       = RECONCILED
           ELIGIBLE_FOR_FREEZE   = YES
           FROZEN                = YES  (DEC-153, 2026-08-28 — xem "Cập
                                  nhật sau FREEZE" ngay dưới)
           DONE                 = NO
```

**Cập nhật sau FREEZE (2026-08-28, phiên "TASK-105B — FREEZE + CONTROLLED
INTEGRATION").** `DEC-153` niêm phong đúng implementation SHA `c22cef8`,
tham chiếu reconciliation SHA `95a7ae6`. Freeze không review lại technical
correctness — chỉ ghi nhận verdict `PASS — ELIGIBLE_FOR_FREEZE` đã có thành
`FROZEN`, đúng State Authority Matrix (`governance/core/V4_1_POLICY_FREEZE.md`
§12). Review Budget lineage `TASK-105B` giữ nguyên `2 allowed / 0 used / 2
remaining` — freeze không tiêu cycle. `app/**`/`tests/**`/`config/**` = 0
trong diff của phiên Freeze. `HB-105B-07`/`HB-105B-08` re-trigger giữ
nguyên, chưa resolve. Chi tiết đầy đủ: `DEC-153`
(`PROJECT/PROJECT_DECISIONS.md`).

**Cập nhật sau CONTROLLED INTEGRATION (2026-08-28, cùng phiên "TASK-105B —
FREEZE + CONTROLLED INTEGRATION").** Divergence trước integration đo bằng
`branch_authority_check.sh`: ahead=7 commit, LOC=3294, 0 ngày —
`WITHIN_LIMITS` (dưới ngưỡng V4.1 §8, không bắt buộc
`INTEGRATION_DECISION_REQUIRED`, integrate vẫn thực hiện theo đúng khuôn
Rollout Order `V4.1` §13). `merge-base(review branch, default) == default
tip cũ` — review branch là fast-forward-able descendant thuần, 0 conflict
kỳ vọng và xác nhận đúng khi merge.

Qua nhánh trung gian `integration/v4-1-task-105b-price-provider` (cắt từ
default tip `c49cb67`), merge `--no-ff` `review/task-105b-independent-review-1`
(chứa implementation, Review A, Review B preserved-archived, reconciliation,
Freeze) — **0 conflict**, merge commit `2301bf6`. Merge nhánh trung gian vào
nhánh mặc định bằng `--ff-only` (fast-forward thuần — không tạo merge commit
thứ hai, không squash, không rebase, không force push, giữ nguyên toàn bộ
Git ancestry).

Post-integration validation (chạy trên chính nhánh trung gian, trước khi
ff-only vào default):

```
Production content check : git diff c22cef8 HEAD -- app/modules/pricing/file_price_provider.py = 0 (byte-identical với reviewed SHA)
4 file production lõi    : diff c22cef8 HEAD -- app/pipeline.py price_engine.py provider.py models.py = 0
Default provider          : app/pipeline.py vẫn PendingPriceProvider — không đổi
FilePriceProvider caller  : grep -rn "FilePriceProvider" app/ tools/ config/ ngoài chính module = 0 hit
TASK-105C code            : 0 file (chưa tồn tại)
Targeted (test_file_price_provider.py) : 33 passed
Golden (test_golden_baseline.py)       : 58 passed, 2 skipped (không đổi)
Full pytest -q                         : 730 passed, 11 skipped (0 regression so baseline 697+11)
4 validator (structure/project_state/evidence/task_completion) : PASS
validate_reference_integrity                                    : đúng 3 lỗi tiền tồn TASK-REM-T06, 0 lỗi mới
git diff --check                                                 : sạch
worktree                                                          : CLEAN
```

Implementation SHA `c22cef8`, reconciliation SHA `95a7ae6`, Freeze SHA
`b627109`, và cả hai artifact review gốc — toàn bộ **reachable** từ default
sau integration (ancestor thật, không phải copy nội dung).

`TASK-105B = FROZEN + INTEGRATED`. **VẪN CHƯA `DONE`** — Exit Criteria của
chính `docs/tasks/TASK-105B-file-price-provider.md` còn đúng một mục chưa
đạt: *"Bảng giá production thật nạp được"* (data dependency đang mở, không
phải code blocker — chưa được chủ dự án cấp file trong phiên này). `DONE`
chỉ được ghi khi mục đó đạt, đúng nguyên tắc CODE COMPLETE ≠ TASK COMPLETE
(`governance/core/TASK_COMPLETION_GATE_STANDARD.md`).

**Cập nhật sau TASK-105B PRICE-PARSER MICRO-HARDENING (2026-08-28, phiên
"TASK-105B PRICE-PARSER MICRO-HARDENING", nhánh
`task/task-105b-price-parser-hardening`, cắt từ default tip
`89948df42b510e27b80a9a7902e3c07d4a7066e7`).** Sửa đúng và chỉ đúng
`HB-105B-07`/`HB-105B-08` — đúng RE-TRIGGER CONDITION đã ghi tại `DEC-153`
(bắt buộc trước `TASK-105C` implementation hoặc trước `FilePriceProvider`
activation thật, tuỳ điều kiện nào tới trước — chưa điều kiện nào xảy ra,
phiên này chủ động chạy trước).

Root cause cả hai finding: `_parse_price()` gọi `to_decimal()` rồi so
sánh `price < 0` ngay mà không kiểm tra hữu hạn trước. `to_decimal()`
trả `Decimal("NaN")` thành công (không raise) cho input NaN — so sánh
`price < 0` sau đó raise `decimal.InvalidOperation` thô, thoát ra ngoài
`InvalidPriceMasterError` (`HB-105B-07`). `Decimal("Infinity") < 0` =
`False` nên `+Infinity` lọt qua thành giá hợp lệ; `-Infinity` bị chặn
tình cờ bởi đúng check đó nhưng sai `.reason` (`negative_price` thay vì
một lỗi hữu hạn) (`HB-105B-08`).

Sửa: một check `price.is_finite()` (canonical finite check của
`Decimal`) chèn giữa check `missing_price` và `negative_price` trong
`_parse_price()`, raise `InvalidPriceMasterError(reason=
"non_finite_price")` — không viết lại parser, không đổi
normalization/effective-dating, không đổi 17 REQUIRED Completion Gate
check nào.

```
Root cause          : _parse_price() thiếu kiểm tra hữu hạn trước khi
                       so sánh/chấp nhận giá
Fix                 : price.is_finite() check, reason="non_finite_price"
Production files    : app/modules/pricing/file_price_provider.py (+7 dòng)
Test files          : tests/test_file_price_provider.py (+120 dòng, 26
                       test mới)
Targeted            : 33 → 59 passed (+26)
Golden              : 58 passed, 2 skipped (không đổi)
Full pytest -q      : 730 → 756 passed, 11 skipped (chênh lệch = đúng 26
                       test mới, 0 regression, 0 skip mới)
Adversarial         : NaN/+Infinity/-Infinity qua string/float/Decimal
                       (9 case) → InvalidPriceMasterError(reason=
                       "non_finite_price"), 0 raw decimal.InvalidOperation
                       thoát ra, lookup() không bao giờ trả Decimal phi
                       hữu hạn
4 file production lõi diff (pipeline.py, price_engine.py, provider.py,
models.py)           : 0
PendingPriceProvider vẫn default pipeline; 0 caller FilePriceProvider
ngoài chính module; 0 code TASK-105C được thêm
Validator            : 4/4 validator PASS; validate_reference_integrity
                       đúng 3 lỗi tiền tồn TASK-REM-T06, 0 lỗi mới;
                       git diff --check sạch
```

Đường thẩm quyền sửa mã đã đóng băng (`DEC-153`): **repair cycle mới có
thẩm quyền riêng** — phiên này chính là phiên đó (được `DEC-153` đặt tên
tường minh làm NEXT AUTHORIZED ACTION, không tự phát sinh). Ghi tại
`PROJECT/REVIEW_BUDGET_LEDGER.md` §"Root Task: TASK-105B" thành
`TASK-105B-RC-1` (`base_sha = c22cef8`, `head_sha =
7f7048d65619c2c2198c99ccbfb073d6cb97ebe2`). Review Budget lineage
`TASK-105B`: `2 allowed / 1 used / 1 remaining` (trước phiên: `2/0/2`).

`HB-105B-07`: **RESOLVED** (code-level). `HB-105B-08`: **RESOLVED**
(code-level). `HB-105B-03`/`HB-105B-05`/`HB-105B-06`/`HB-105B-10`: **không
đổi**, không sửa trong phiên này (ngoài phạm vi khoá của brief).

Independent Review độc lập tại
`9241ccfca9a8b0159b347f4d1171c0caa37eecad` đã **PASS — REPAIR VERIFIED**.
Repair cycle nay `CLOSED_BY_REPAIR, INDEPENDENTLY_VERIFIED`; review không
tiêu thêm cycle. Controlled Integration qua
`integration/v4-1-task-105b-rc1` đã merge reviewed lineage bảo toàn ancestry,
0 conflict, rồi state reconciliation được ghi tại
`docs/sessions/S031-task-105b-rc1-controlled-integration.md`.

`TASK-105B = FROZEN + INTEGRATED + RC-1 INTEGRATED`, vẫn `NOT DONE` — Exit
Criteria vẫn thiếu đúng một mục: bảng giá production thật nạp được (data
dependency, không đổi bởi phiên này). `HB-105B-07`/`HB-105B-08` prerequisite
cho `TASK-105C` = **CLEARED**, nhưng `TASK-105C` **CHƯA được cấp phép bắt
đầu**: bảng giá production thật và product identity mapping (`product_raw` ↔
`<MÃ>` Tracking, dependency riêng chưa mở task) vẫn OPEN. "Nền tảng code
105B an toàn" **không đồng nghĩa** "105C được phép bắt đầu".

**NEXT AUTHORIZED ACTION = chờ Owner cấp bảng giá production thật cho
`TASK-105B` và authority riêng cho product identity mapping.** Không tự mở
hay implement `TASK-105C`; sau khi hai dependency được cập nhật canonical,
đánh giá lại authorization của task đó một cách riêng.

**Cập nhật sau RECONCILIATION (2026-08-28, phiên "TASK-105B — INDEPENDENT
REVIEW RECONCILIATION").** Hai session Independent Review #1 độc lập chạy
song song trên hai nhánh khác nhau (`review/task-105b-independent-review-1`
và `claude/file-price-provider-review-negpxw`), không biết về nhau, cùng
review đúng `c22cef8` và cùng ghi artifact tại đúng
`docs/reviews/TASK-105B-INDEPENDENT-REVIEW-1.md` — cùng loại sự cố đã ghi ở
`DEC-118`. Một phiên reconciliation riêng đã: xác minh cả hai target đúng
`c22cef8` (`merge-base` = implementation SHA); dedupe namespace `HB-105B-*`
(phát hiện Review B tái dùng nhầm hai ID `HB-105B-01`/`02` vốn thuộc
`TASK-108B` §34 — sửa về canonical ID `HB-105B-07`/`HB-105B-08`, không
collision); giải quyết một classification disagreement (`HB-105B-04`: HARDENING
theo Review B vs OUT_OF_SCOPE theo Review A — reconciled = OUT_OF_SCOPE theo
đúng normative Scope Lock table của `TASK-105B`, không ảnh hưởng Freeze
eligibility); bảo toàn cả hai artifact gốc nguyên vẹn (Review A giữ canonical
path, Review B archived byte-identical). Cả hai review đồng thuận **0
BLOCKING** — verdict reconciled = `PASS — ELIGIBLE_FOR_FREEZE`.
`app/**`/`tests/**`/`config/**` = 0 trong toàn bộ diff reconciliation.
Chi tiết đầy đủ:
`docs/reviews/TASK-105B-INDEPENDENT-REVIEW-RECONCILIATION.md`.

Bằng chứng chính: `pytest tests/test_file_price_provider.py -q` → `33
passed`; `pytest tests/test_golden_baseline.py -q` → `58 passed, 2
skipped` (y hệt trước phiên, không đổi); `pytest -q` toàn bộ → `730
passed, 11 skipped` (trước phiên: `697 passed, 11 skipped` — chênh lệch
đúng bằng 33 test mới, **0 regression**, 0 skip mới); diff `app/pipeline.py`,
`price_engine.py`, `provider.py`, `models.py` = **0** (`git diff --quiet`
exit 0); 4 validator (`validate_structure`/`validate_project_state`/
`validate_evidence`/`validate_task_completion`) PASS,
`validate_reference_integrity` giữ đúng 3 lỗi tiền tồn `TASK-REM-T06`,
không lỗi mới. Provider mặc định **không đổi** — `app/pipeline.py` vẫn
`PendingPriceProvider`, Golden vẫn chạy provider đó (đúng yêu cầu
"Preserve Pending Default", không tự kích hoạt provider mới vào production
path).

**Còn mở, không phải code blocker:** bảng giá production thật của chủ dự
án **chưa được cấp** trong phiên này — `FilePriceProvider` mới kiểm chứng
bằng fixture tổng hợp (synthetic). Khi có file thật, chỉ cần
`FilePriceProvider.from_yaml(<path>)`, không cần sửa code. Chi tiết đầy
đủ, gate 17 check với evidence từng dòng, provenance/error semantics,
composition seam cho `TASK-105C`: `docs/tasks/TASK-105B-file-price-provider.md`
(canonical, mới tạo, frozen tại phiên này — Scope Lock + Completion Gate
kế thừa nguyên vẹn `DEC-145`/`OD-105B-01`, không phát minh business rule
mới).

**TASK-105B-Q3 — chính sách zero-price dòng phụ (tách riêng):**

```
IMPLEMENTATION = BLOCKED_BY [ TASK-103 Product/Transaction Classification,
                              hoặc danh sách enumerated do Owner cấp ]
```

`OD-105B-01` §C **cấm** matcher mới trong provider và yêu cầu reuse
classification production — nhưng `TASK-103` **chưa làm**,
`config/classification.yaml` **không tồn tại**, và cơ chế duy nhất
(`is_non_product_line`) tự khai là *noise-reduction only*, **tạm thời**
(HD-110-02), **cấm tune**. Đo trên production: keyword set hiện hành khớp **36**
dòng trong khi đúng 3 nhóm Owner nêu chỉ **34** (dôi `Phụ Phí`, `Phụ Phí Đổi
mới`). Chi tiết + hai đường đi:
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần IV §40.

Contract + Completion Gate 16 check: cùng file, Phần IV. Chuỗi mở khoá (cập
nhật sau `DEC-151` — nguồn giá lịch sử nay là `phist`, không còn "file giá 4
cột" làm điểm vào chính; `FilePriceProvider`/`TASK-105B` giữ vai trò
bootstrap/fixture độc lập, không còn nằm TRÊN chuỗi này):
**`phist` (`HistoricalVendorPriceProvider`, `TASK-105C`)** →
(`TASK-103` hoặc danh sách enumerated) → `TASK-105B-Q3` → `TASK-108B` →
`TASK-109`.

Lịch sử: S020 sửa Review #4 (2 provenance defect, DEC-131), S019 sửa Review #3
(3 finding, DEC-130), S018 sửa Review #2 (4 finding), S017 sửa Review #1
(6 finding, DEC-129), S016 triển khai, S015 Gate Review (DEC-128).
**Chưa vòng review nào PASS.**)

Overall Status:
IN_PROGRESS

Current Phase:
PHASE-01 — Engine tính toán

Current Task:
**GOVERNANCE/SPEC RECONCILIATION — COMPLETE tại working tree, chưa merge.**
`DEC-154` recorded; `TASK-105D` canonical spec created ở trạng thái
`PLANNED/BLOCKED`; `TASK-105C` chuyển current authorization từ `READY` sang
`BLOCKED`; `TASK-105B` vẫn `NOT DONE` và chưa activate. Đây không phải
implementation task.

Previous canonical milestone (giữ làm lịch sử):
**TASK-GOLDEN-BASELINE-001 — DONE (2026-08-27).** Golden Business Baseline.
`DISCOVERY = COMPLETE` (`b738fa4`), `IMPLEMENTATION = COMPLETE`,
`INDEPENDENT_REVIEW_2 = PASS — ELIGIBLE_FOR_FREEZE` tại reviewed SHA
`85210691702550d83c0fd42fe816be8ca9dde889` (ghi tại
`docs/reviews/TASK-GOLDEN-BASELINE-001-INDEPENDENT-REVIEW-2.md`),
**`FROZEN = YES`** (`DEC-142`, freeze SHA `41813535c9d32a7f72782011a5f30ad2c38924f9`),
**`MERGED = YES`** (qua `integration/v4-1-golden-baseline`, default SHA
`f332a4cb4410b3ca9c71d659d36a3e8f26aa1fa5`), **`DONE = YES`** — toàn bộ 11
Exit Criteria của GB-12 (`docs/tasks/TASK-GOLDEN-BASELINE-001-PLAN.md`) đạt:
Golden test PASS trên default, full suite 0 regression, business anchors
khớp, provenance/invariant có authority, ledger cập nhật, `TASK-110`/
`CHECK-110-16`/`R1-A1`/`app/`/`config/` không đổi.
`effective_risk = HIGH`, 2 repair cycle khả dụng, **1 đã dùng** (`GB-IR-01`,
`CLOSED_BY_REPAIR, INDEPENDENTLY_VERIFIED`), **1 còn lại — UNUSED, task đóng
không bắt buộc dùng hết ngân sách** — xem `PROJECT/REVIEW_BUDGET_LEDGER.md`.
Task này **không** thuộc lineage `TASK-110` và **không** mở `R1-A2` → `R8`.
Golden Baseline nay **ACTIVE**, chạy trên nhánh mặc định bằng một lệnh:
`python3 -m pytest tests/test_golden_baseline.py -q`.

Task liền trước (vẫn NOT DONE):
TASK-110 — validation + Review Queue — **REPAIR MODE — R1-A1 FROZEN, lineage
tạm dừng vì hết review budget**. `R1-A1` đã đạt `FROZEN` theo **DEC-139**
(Independent Review `PASS — ELIGIBLE_FOR_FREEZE`, 0 blocking finding, 1
hardening backlog HB-A1-05). `R1-A` và `R1` tổng **vẫn NOT FROZEN** — không
suy diễn tăng theo. `R1-A2` → `R8` **KHÔNG tự mở**: lineage `TASK-110` có
`repair_cycles_remaining = 0` (`EXHAUSTED_PRE_V4.1`), mỗi unit cần một
`OWNER_EXTENSION` riêng — xem `PROJECT/REVIEW_BUDGET_LEDGER.md`.

Canonical cho giai đoạn này:
`docs/tasks/TASK-110_REPAIR_PROGRESS.md` (bảng tiến độ từng unit — đọc TRƯỚC
`PROJECT_PROGRESS.md` cho câu hỏi "unit nào đang làm") và
`docs/tasks/TASK-110-REPAIR-MODE.md` (bối cảnh Review #8 + 8 finding, artifact
lịch sử).

**ĐÃ MERGED vào nhánh mặc định (V4.1-1). VẪN NOT DONE.**
`CHECK-110-16` = **REQUIRED · BLOCKED · POST_MERGE_PRODUCTION_ACCEPTANCE**
(DEC-141). `TASK-110` chỉ chuyển `DONE` khi check này thực sự `PASS` trên dữ
liệu production thật.

Current Task Mode:
MAJOR

Next Recommended Task:
**TASK-105D readiness/data-contract + persistence/audit design** — phiên có
authority riêng để chốt catalog/version contracts, pre-cutover confirmed
report registry, migration/rollback/concurrency mechanism và review/freeze
Completion Gate. Không implement resolver trước khi Ready Gate đạt.

Historical prior pointer (SUPERSEDED bởi `DEC-154` ở trên):
**`TASK-GOLDEN-BASELINE-001` đã DONE — không còn việc governance nào treo ở
đây.** `V4.1` đã chuyển `FULLY_ENFORCED` (xem "Governance V4.1 — Trạng Thái
Adoption" đầu file).

Track A (sản phẩm) hiện bị chặn ở hai điểm cần **Owner quyết định**, không
phải việc agent tự làm tiếp được:

1. **`TASK-108B` (Converted Revenue)** — **semantics ĐÃ ĐÓNG HOÀN TOÀN
   (DEC-143 + DEC-144; `OD-108B-01` + `OD-108B-02`, 2026-08-27); C15 ĐÃ ĐÓNG.**
   Chuỗi audit nguồn giá `DEC-146` → `DEC-150` (RTDB discovery → source
   mismatch → `_c.min` path audit → popup verification) khép lại bằng
   **`DEC-151` + `DEC-152` (Owner Decision, 2026-08-27): thu hẹp phạm vi +
   chốt cuối.** Reports KHÔNG dùng `_c.min`/`inv.cong` làm nguồn giá lịch
   sử — nguồn DUY NHẤT là `phist/<mã>/<NCC>/<ngày>`, với semantics
   `Price(NCC,D) = record gần nhất ≤ D` rồi lấy MIN qua các NCC có căn cứ
   (không lọc gì thêm ngoài sentinel `0` — Q1/Q2 CLOSED, `DEC-152`); không
   đủ căn cứ → `Pending` có chủ đích, xử lý tay sau. `TASK-105B-Q3` (dòng
   phụ) không đổi, vẫn chờ `TASK-103`. Xem
   `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần III–XI,
   `docs/tasks/TASK-105C-historical-vendor-price-provider.md`.
   *(Chi tiết `OD-108B-01` giữ nguyên bên dưới.)* `EligibleCosts = {}` (closed empty
   set), `DeliveryCost = NOT ELIGIBLE FOR NOW`, `OtherKpiAdjustment = 0 by
   definition`, canonical formula đã chốt.
   `IMPLEMENTATION = BLOCKED_BY_DEPENDENCY` — còn **3 blocker**, KHÔNG còn
   câu hỏi nghiệp vụ nào chờ Owner: (a) `TASK-105C` implementation thật
   (kèm `TASK-105B` làm dependency cứng — chưa DONE); (b) product identity
   mapping (`product_raw` ↔ `<MÃ>` Tracking — dependency mới, chưa mở
   task, cấm fuzzy matching); (c) confirmed `KpiPurchaseAdjustment`
   persistence. Xem
   `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` §19–21, Phần XI.
   `TASK-109` (summary_engine) vẫn theo sau `TASK-108B`.
   **Next Product Task — cập nhật sau IMPLEMENTATION `TASK-105B`
   (2026-08-28):**

   ```
   1. TASK-105B implementation   IMPLEMENTED + SELF-VERIFIED (2026-08-28),
                                  INDEPENDENT_REVIEW = PASS, REVIEW_EVIDENCE
                                  = RECONCILED (2026-08-28),
                                  ELIGIBLE_FOR_FREEZE = YES,
                                  FROZEN = YES (DEC-153, 2026-08-28) — xem
                                  docs/reviews/TASK-105B-INDEPENDENT-REVIEW-RECONCILIATION.md
   1b. TASK-105B PRICE-PARSER    BẮT BUỘC trước bước 2 — resolve
       MICRO-HARDENING           HB-105B-07 (NaN)/HB-105B-08 (Infinity),
                                  re-trigger canonical đã ghi kèm DEC-153.
                                  CHƯA làm trong phiên Freeze này.
   2. TASK-105C implementation   CHỜ (1) TASK-105B FROZEN (đã đạt) VÀ (1b)
                                  micro-hardening NaN/Infinity xong VÀ
                                  Controlled Integration/state DONE thật —
                                  KHÔNG được làm trước dù (1) đã FROZEN
   3. Product Identity Mapping   (dependency riêng, chưa mở task — product_raw
                                  Reports ↔ <MÃ> Tracking, cấm fuzzy matching)
   4. TASK-105B-Q3                (dòng phụ, độc lập, chờ TASK-103/enumeration)
   5. TASK-108B                   (Converted Revenue — chờ 1+1b+2+3)
   6. TASK-109                    (summary_engine — chờ TASK-108B)
   ```

   **NEXT AUTHORIZED ACTION: `TASK-105B` FREEZE** — Independent Review #1 đã
   `PASS — ELIGIBLE_FOR_FREEZE` trên hai artifact E2 độc lập, đã reconcile
   (2026-08-28,
   `docs/reviews/TASK-105B-INDEPENDENT-REVIEW-RECONCILIATION.md`), 0
   BLOCKING. Một phiên Freeze Finalization có thẩm quyền riêng
   (`governance/core/V4_1_POLICY_FREEZE.md` §12) mới được ghi `FROZEN` và
   chuyển `TASK-105B` sang `DONE`. `TASK-105C` vẫn KHÔNG được bắt đầu code
   cho tới khi `TASK-105B` chuyển `DONE` thật. Product Identity Mapping
   (bước 3) vẫn mở song song được — không phụ thuộc `TASK-105B`/`TASK-105C`.
2. **`CHECK-110-16`** — vẫn `BLOCKED`, `Gate Class = POST_MERGE_PRODUCTION_ACCEPTANCE`
   (DEC-141). Chờ Owner cấp file thô toàn công ty 6 tháng (11.765 dòng) để
   đối chiếu; đây là nhánh **độc lập** với Golden Baseline (khác dataset —
   xem `docs/tasks/TASK-GOLDEN-BASELINE-001-PLAN.md` §A.20). `TASK-110` chỉ
   `DONE` khi check này thực sự `PASS` trên dữ liệu production thật.

Không có Owner Extension nào cho `R1-A2` → `R8` của lineage `TASK-110` —
**KHÔNG** tự mở bất kỳ unit nào trong nhóm đó.

**KHÔNG** bắt đầu `R1-A2`, `R2` hay bất kỳ unit nào từ `R1-B` → `R8`: lineage
`TASK-110` có `repair_cycles_remaining = 0`; mỗi unit cần `OWNER_EXTENSION`
riêng kèm production path cụ thể, kịch bản nghiệp vụ sai cụ thể, phạm vi và
budget được Owner cấp. Không có Owner Extension ⇒ `STOP`.

Lịch sử review của lineage (tham chiếu, không phải việc còn lại): tám vòng
Independent Review, bảy vòng đầu FAIL và đều đã sửa xong (6 + 4 + 3 + 2 + 4 +
6 + Closure finding); mỗi finding có regression hoặc falsification test riêng.
Vòng #5 và #6 là **Architecture Repair**, không phải vá cục bộ. Vòng cuối trên
`R1-A1` **PASS** tại `a853971` (DEC-139).

Sau đó: **TASK-111 (excel_exporter)** dùng được đầu ra Review Queue cho sheet
Audit/Overrides.

**TASK-109 (summary_engine) bị chặn một phần** — cột "DS quy đổi" và "LN KPI"
cần TASK-108B. Không nên bắt đầu trước khi C15 đóng, nếu không sẽ phải làm
lại một nửa.

TASK-108 gốc đã tách làm ba (DEC-127, Gate v3):
- **108A-1** ConversionScheme Resolution — **DONE** (Review #4 PASS)
- **108A-2** ProductGroup Auto Classification — NOT REQUIRED FOR PHASE 1
- **108B** Converted Revenue — BLOCKED (C15 `EligibleCosts`)

## Roadmap tổng thể

- [x] PHASE-00 — Bootstrap governance và phân tích nguồn
  - [x] TASK-000 — Đưa gói governance lên gốc repository (MICRO). **Trùng
        việc với REM-T02 của Track Governance** — cả hai làm trên hai nhánh
        khác nhau, không biết về nhau, cùng hội tụ đúng một kết quả. Xem
        "Track Governance" bên dưới và DEC-118.
  - [x] TASK-001 — S000: chọn profile và khởi tạo trạng thái dự án (MAJOR)
  - [x] TASK-002 — Phân tích workbook nguồn, 6 tài liệu theo mục 27 đặc tả (MAJOR)
  - [x] TASK-003 — ADR-101/102/103 (MICRO)
  - [x] GATE-00 — Chủ dự án duyệt `docs/analysis/` trước khi có dòng code ứng
        dụng nào. **PASS (DEC-122, 2026-08-23).** Duyệt trực tiếp trong hội
        thoại sau đợt rà soát nghiệp vụ DEC-119/120/121; C4b/C9/C10 đóng cùng
        lúc, C11 còn mở không chặn.

- [ ] PHASE-01 — Engine tính toán (Python thuần, không UI, không database)
  - [x] TASK-101 — importer + normalizer. **DONE** (2026-08-23). Thực hiện 7
        bước đầu của import workflow mục §22 đặc tả: đọc `.xlsx` (header
        dòng 4, data dòng 6), báo cáo metadata trước khi chuẩn hóa, chuẩn
        hóa cột (trừ `Chiết khấu` — DEC-114), áp employee mapping, nhóm theo
        OrderID, áp rule ADS ở cấp đơn, propagate nguồn đơn xuống line item.
        49/49 test PASS trên fixture tổng hợp ẩn danh (DEC-108); **13/13
        REQUIRED check PASS**, bao gồm đối chiếu trên dữ liệu thật Tín Phát
        01.2026 (254 đơn) và 06.2026 (146 đơn) — khớp tuyệt đối, không sai
        lệch nghiệp vụ đáng kể, không sửa business rule để ép khớp. Chi
        tiết đầy đủ + mục "Đối Chiếu Dữ Liệu Thật":
        `docs/tasks/TASK-101-importer-normalizer.md`.
  - [x] TASK-102 — employee_mapper. **Năng lực lõi đã xây trong TASK-101**
        (`app/modules/mapping/employee_mapper.py`, config-driven, effective-
        dated, 7/7 test PASS). Không tạo task riêng trùng lặp — nếu phát sinh
        yêu cầu mở rộng (vd. UI quản lý mapping) sẽ mở lại dưới TASK-304.
  - [x] TASK-103 — order_builder. **Năng lực lõi đã xây trong TASK-101**
        (`app/modules/orders/order_builder.py`, nhóm theo OrderID, 3/3 test
        PASS). Product/transaction classification (dòng phụ có giá trị tiền)
        **chưa làm** — đúng phạm vi gốc của TASK-103, dời sang khi cần
        (DEC-110/113 áp dụng lúc đó).
  - [x] TASK-104 — lead_source_engine (rule ADS). **Đã xây trong TASK-101**
        (`app/modules/lead_source/classifier.py`). Phân giải `LeadSource` ở
        cấp OrderID, đúng hai giá trị `PERSONAL`/`ADS`, chuỗi 4 bậc: override
        tay → rule từ khóa → mặc định cấp nhân viên → mặc định hệ thống
        (DEC-119, ADR-104). 19/19 test PASS, khớp hành vi bản tham chiếu
        `tools/analysis/verify_ads_rule.py` (31/31 PASS) trên 18 case
        LeadSource dùng chung. **Không** quyết định tỉ lệ — đó là việc của
        TASK-108 (ConversionScheme, bước phân giải độc lập).
  - [x] TASK-105 — price_engine + interface PriceProvider. **DONE**
        (2026-08-23). Bước 8 của §22 đặc tả: tra giá nhập nếu có Price
        Master, chưa có thì Pending (DEC-103). `PriceProvider` là Protocol
        ổn định (`lookup(product_code, sale_date) -> Optional[Decimal]`);
        `PendingPriceProvider` là implementation mặc định — đúng cho 100%
        dòng ở Phase 1 vì chưa có Price Master nào tồn tại, không phải giới
        hạn tạm thời. Không bao giờ coi giá thiếu là 0 (kiểm chứng bằng
        test kể cả với provider "thật" nhưng miss một sản phẩm). 9/9
        REQUIRED check PASS, 57/57 test tổng (8 mới, không regression trên
        49 test TASK-101). Chi tiết: `docs/tasks/TASK-105-price-engine.md`.
  - [x] TASK-106 — adjustment_engine. **DONE** (2026-08-23). DEC-125 làm rõ:
        `KpiAdjustment` không có nguồn raw (không có gì để "parse" tự động,
        khác giả định ban đầu) — loại điều chỉnh (`Qua kho`, `NCC giao`,
        `KHBH`, `Thợ lắp`) và phương tiện giao hàng là thứ người dùng chọn
        tay sau khi import. Task giao đúng phần Phase 1 làm được:
        `AirConditionerClassifier` (dò từ khóa điều hòa trên `ProductRaw`) +
        `AdjustmentResolver` (số tiền đề xuất theo `delivery_method_tiers`
        cho Qua kho/NCC giao, `air_conditioner_only_defaults` cho KHBH/Thợ
        lắp — không có mặc định cho non-AC, không bao giờ suy đoán). **Không**
        nối vào `run_import()`, **không** thêm field domain model — cả hai
        thuộc phạm vi override thật (Phase 2/3, TASK-202/302/305). 5/5
        REQUIRED check PASS, 74/74 test tổng (17 mới, không regression).
        Chi tiết: `docs/tasks/TASK-106-adjustment-engine.md`.
  - [x] TASK-107 — profit_engine. **DONE** (2026-08-23). Trước khi code, chủ
        dự án chốt DEC-126 — 6 nguyên tắc ranh giới AccountingProfit/Adjustment.
        Task chỉ triển khai `AccountingProfit = (SellPrice −
        AccountingPurchasePrice) × Quantity` (Universal formula), **không**
        mở rộng sang `EligibleKpiProfit` vì persistence + xác nhận Adjustment
        chưa tồn tại (DEC-126 điểm 3–6). `profit_engine` không phụ thuộc
        `app.modules.adjustment` theo bất kỳ cách nào (kiểm chứng bằng grep).
        Nối vào `run_import()` làm bước 9 — tự động Pending khi giá nhập
        chưa có, không cần logic điều kiện riêng. 6/6 REQUIRED check PASS,
        83/83 test tổng (9 mới, không regression). Chi tiết:
        `docs/tasks/TASK-107-profit-engine.md`.
  - [x] TASK-108A-1 — ConversionScheme Resolution. **DONE**
        (2026-08-23, Independent Review #1→#4, #4 PASS, đã merge). Ba vòng pre-implementation
        review (Gate v1→v3) trước khi code; DEC-127 + ADR-106 chốt: tách
        `Nội thành` thành ba Employee thật (Vinh/Quý/Hiệp) cùng
        `employee_group = NOI_THANH`; thêm dimension `ProductGroup`
        (`DIEN_MAY`/`GIA_DUNG`) ở **cấp product line**; `ConversionScheme`
        hạ từ cấp Order xuống cấp line. Resolver 4 chiều, lọc cứng theo
        `lead_source`, chọn dòng cụ thể nhất theo specificity, hòa điểm là
        lỗi cấu hình, không khớp là `Unresolved`. 16/16 REQUIRED check PASS,
        119/119 test, reconciliation 55 ô cột F Summary 2026 **0 ô lệch** và
        employee mapping đúng trên 14.389 dòng thô thật. Chi tiết:
        `docs/tasks/TASK-108A-1-conversion-scheme-resolver.md`.
  - [ ] TASK-105B — `FilePriceProvider` (Phase 1). Implementation thứ hai của
        `PriceProvider` Protocol. **FROZEN + INTEGRATED + RC-1 INTEGRATED,
        NOT DONE**. `DEC-154` chốt current role = provider foundation cho
        **Public Purchase effective-dated price**, không còn là dependency
        cứng/composition seam của `TASK-105C`. DONE còn chờ dataset Public
        Purchase production thật load/replay được và remaining HB triggers
        resolve trước usage. `PendingPriceProvider` vẫn default;
        `FilePriceProvider` chưa activate. Budget `2/1/1`.
  - [ ] TASK-105C — `HistoricalVendorPriceProvider` (tên chính thức, thay
        `RTDBPriceProvider`, chốt tại `DEC-152`). Đọc TRỰC TIẾP `phist`,
        KHÔNG qua `_c.min`/`inv.cong`. **BLOCKED / NOT AUTHORIZED** sau
        `DEC-154`: semantics `DEC-151/152` giữ nguyên, nhưng Scope Lock đã
        reopen và Completion Gate change proposal chưa refreeze.
        Canonical spec:
        `docs/tasks/TASK-105C-historical-vendor-price-provider.md`.
        **Owner Decision cuối (`DEC-152`) đóng Q1/Q2:**
        Q1 (NCC retired/MIN_LOAI hồi tố) = **CLOSED** — trạng thái NCC
        HIỆN TẠI không áp ngược, giá lịch sử hợp lệ vẫn là candidate.
        Q2 (outlier threshold hồi tố) = **CLOSED** — không áp ngược,
        Phase 1 = MIN qua mọi candidate hợp lệ, loại sentinel `0`, không
        lọc gì thêm.
        **Nguồn HistoricalVendorMin: `phist/<mã>/<NCC>/<ngày>`.**
        `Price(NCC,D)` = record gần nhất ≤ D; `HistoricalVendorPrice(mã,D)`
        = MIN qua mọi NCC có giá xác định > 0. Không candidate → explicit
        absence để price-resolution thử Public Purchase fallback; không tự
        thành giá 0.
        `inv.cong`/`_c.min`/`MarketMinHistory`: **không bắt buộc** Phase 1.
        Input là resolved `TRACKING` identity + sale_date từ `TASK-105D`;
        PUBLIC_PURCHASE identity bypass. Không cần pre-map toàn catalog.
        Không compose `FilePriceProvider` sau `DEC-154`.
        Rủi ro mang theo: `phist` sửa/xoá được (`DEC-147` §54 R4) —
        provider phải đóng băng/snapshot bất biến theo `capture_id`, không
        đọc `phist` sống mỗi lần chạy lại; `NCC_ALIAS` không hồi tố (nợ kỹ
        thuật nhỏ). Chi tiết:
        `docs/tasks/TASK-105C-historical-vendor-price-provider.md`,
        `DEC-152`, `DEC-154`.
  - [ ] TASK-105D — `Product Identity Resolver`. **PLANNED; specification
        complete; Ready Gate BLOCKED; Completion Gate 32 check DRAFT,
        NOT_TESTED, chưa frozen; implementation chưa được cấp phép.** Hai
        namespace `TRACKING`/`PUBLIC_PURCHASE`, persistent alias/rejection/
        cross-system mapping, DISTINCT-before-mapping, batch/keyboard-first,
        audit/idempotency/concurrency. Canonical spec:
        `docs/tasks/TASK-105D-product-identity-resolver.md`.
  - [ ] TASK-105B-Q3 — chính sách `AccountingPurchasePrice = 0` cho dòng phụ
        (`Policy:SupplementaryExpenseZeroPurchasePrice`). **BLOCKED** — cần
        `TASK-103` (Product/Transaction Classification, chưa làm) hoặc một danh
        sách enumerated do chủ dự án cấp. `OD-105B-01` §C cấm phát minh matcher
        mới trong provider; `is_non_product_line` hiện có tự khai là tạm thời
        (HD-110-02) và cấm tune.
        Hợp lệ ở Phase 1 theo đặc tả §10 (*"Version đầu cho phép nhập tay"*);
        không sửa `price_engine`/`pipeline`, không thêm field, **không phá
        Golden**. `effective_risk = HIGH`. Discovery đầy đủ + bảng cột file giá:
        `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần III.
  - [ ] TASK-108B — Converted Revenue (2 bucket PERSONAL/ADS).
        **SEMANTIC_DEFINITION = APPROVED (DEC-143, `OD-108B-01`, 2026-08-27) ·
        IMPLEMENTATION = BLOCKED_BY_DEPENDENCY.** `EligibleCosts = {}`,
        `DeliveryCost = NOT ELIGIBLE`, `OtherKpiAdjustment = 0`, formula chốt
        `(SellPrice − KpiPurchasePrice) × Quantity − Discount`. C15 **ĐÃ ĐÓNG**.
        Sau **DEC-144 → DEC-154**: `CONFLICT DETECTED` ở `DEC-149` §71
        **ĐÃ ĐÓNG** bởi `DEC-151`; Q1/Q2 filtering **ĐÃ ĐÓNG** bởi
        `DEC-152` — Owner Decision thu hẹp phạm vi `AccountingPurchasePrice`
        lịch sử về `HistoricalVendorPrice` tính từ `phist`, loại
        `_c.min`/`inv.cong` khỏi vai trò nguồn, và chốt "không lọc gì
        ngoài sentinel `0`" là quy tắc CUỐI cho Phase 1 (xem `TASK-105C` ở
        trên). `DEC-154` thêm two-namespace identity + Public Purchase
        direct/fallback branch. Blocker còn lại: (1) `TASK-105D`; (2)
        `TASK-105C` refreeze + implementation; (3) `TASK-105B` DONE với
        Public Purchase dataset; (4) ownership/executable gate P01–P10;
        (5) `TASK-105B-Q3`.
        **KHÔNG còn** bất kỳ câu hỏi filtering/kiến trúc/field-selection
        nào chờ Owner — toàn bộ đã đóng.
        `PendingPriceProvider` trả `None` vô điều kiện; Golden xác nhận
        100 % Pending trên dữ liệu production — chưa đổi, chờ implementation
        thật của `HistoricalVendorPriceProvider`.
        `TASK-105B` **là dependency cứng**, chưa DONE — xem `TASK-105C` ở
        trên. Confirmed
        `KpiPurchaseAdjustment` **hết là blocker semantic** (`OD-108B-02`);
        còn lại một yêu cầu cơ chế nội bộ (source khai báo rỗng để phân biệt
        absence với source-unavailable), thuộc phạm vi chính TASK-108B.
        Bước 11 của §22 đặc tả. Phân giải `ConversionScheme` đã
        xong ở 108A-1; phần còn lại là quy đổi hai bucket
        (DEC-119, DEC-121, ADR-104), sau đó quy đổi từng bucket độc lập rồi
        cộng lại. Engine tự tổng hợp `PersonalProfit`/`AdsProfit` từ phân loại
        cấp đơn — `X` không còn là đầu vào (DEC-120).
  - [ ] TASK-109 — summary_engine. Mục §15 đặc tả: Summary tháng có 3 cột
        Personal / ADS / Total cho Tổng đơn, Số SP, Doanh số, LN KPI, DS quy
        đổi, DSQĐ/đơn, Lợi nhuận thực, % Target — **và tương tự theo từng
        nhân viên dạng YTD**, để tách bạch năng lực tự bán với năng lực xử lý
        lead do công ty tạo ra.
  - [ ] TASK-110 — validation + Review Queue. **MERGED vào nhánh mặc định
        (V4.1-1), NOT DONE.** `R1-A1` = **FROZEN** (DEC-139, Independent
        Review PASS tại `a853971`); `R1-A` = NOT FROZEN; `R1` = NOT FROZEN.
        `R1-A2` → `R8` = `OWNER_EXTENSION REQUIRED` (repair budget
        `remaining = 0`). Tám vòng review, vòng cuối trên `R1-A1` PASS.
        21/22 REQUIRED check PASS; CHECK-110-16 (đối chiếu dữ liệu thật)
        **BLOCKED**, Gate Class `POST_MERGE_PRODUCTION_ACCEPTANCE` (DEC-141)
        — thiếu file thô production; **chặn DONE, không chặn merge**.
        **20/20 falsification CLOSED** (trước Closure: 7/20); RC-1→RC-5 đóng bằng cấu trúc; oracle đã mutation-test. Phạm vi
        thật **7 loại** sau DEC-128 (V7 mở thành **F1–F6** theo DEC-129),
        không phải 5 — xem `docs/tasks/TASK-110-validation-review-queue.md`.
        Mục §18 đặc tả, 5 loại gốc:
        `Missing` (thiếu ngày, OrderID, nhân viên, số lượng, doanh số, giá
        nhập), `Suspicious` (SL ≤ 0, giá bán = 0, giá nhập > giá bán, lợi
        nhuận âm — 1.912 dòng như vậy trong mẫu), `Order inconsistency` (cùng
        OrderID, khác nhân viên), `Source classification` (override tay
        không khớp rule ADS), `Duplicate` (cùng `source_file` +
        `source_row`). Không bao giờ chặn toàn bộ import.
  - [ ] TASK-111 — excel_exporter. Mục §23 đặc tả, 5 loại sheet: Summary;
        Processed Data; sheet `MM.YYYY Employee` theo từng nhân viên khi bật
        tùy chọn; Config Snapshot (employee mapping, source rules, conversion
        rules, adjustment rules, target); Audit/Overrides. Personal / ADS /
        Total luôn hiển thị ở cả sheet chi tiết lẫn Summary. Dòng tổng phụ
        mang nhãn `RowType` và nằm ngoài mọi vùng SUM (DEC-115).
  - [ ] TASK-112 — CLI
  - [ ] GATE-01 — Đối chiếu với file thô thật; xác nhận chênh lệch +6,0% của
        Hoàng/Kiên do không di trú (DEC-120) là chấp nhận được với số liệu
        thật; đóng C11 (88 dòng chưa map)

- [ ] PHASE-02 — Lưu trữ và API
  - [ ] TASK-201 — schema database + migration
  - [ ] TASK-202 — audit_service
  - [ ] TASK-203 — HTTP API. Triển khai bản đồ route backend trong **ADR-105**
        §2: 24 endpoint dưới tiền tố `/api/v1`, nhóm theo 9 module của
        ADR-101. **Không viết endpoint ghi vào RAW** — `raw_rows` không có
        UPDATE/DELETE theo ADR-102, ở đây điều đó nghĩa là code không được
        phép tồn tại (kiểm chứng bằng `grep`). Mỗi endpoint phải điền đủ
        `API Contract Template` (`governance/core/06_DATABASE_API_RULES.md`),
        mục Authorization không được để trống.
  - [ ] TASK-204 — authentication và phân quyền. **Đơn giản hóa 2026-08-23
        (DEC-124):** chủ dự án xác nhận trực tiếp — công cụ quản trị nội bộ,
        chỉ một vai trò `ADMIN` trong MVP, không `viewer`/`editor`/
        `employee_scope` (**ADR-105** §4, Accepted). Danh tính không phải
        `ADMIN` nhận `403` ở mọi endpoint trừ
        `auth/login`/`auth/logout`/`auth/me`, và không mở được frontend.
        Ranh giới bảo mật đặt ở backend dù chỉ một vai trò: một `curl`
        không mang token `ADMIN` hợp lệ phải bị chặn, không chỉ ẩn nút trên
        UI. Thiết kế `users.role` dạng enum cho phép thêm vai trò sau này,
        không xây trước hạ tầng nhiều vai trò (ADR-105 §5). C12/C13/C14 đã
        đóng — không còn phụ thuộc nghiệp vụ nào chặn Roadmap Finalization
        của task này khi PHASE-02 mở.
  - [ ] TASK-205 — recalculate tăng dần (incremental)

- [ ] PHASE-03 — Giao diện Web
  - [ ] TASK-301 — upload và xem trước khi import. Route: `/imports`,
        `/imports/new`, `/imports/{batchId}` (ADR-105 §3)
  - [ ] TASK-302 — lưới chi tiết nhân viên theo tháng, sửa inline. Route:
        `/employees/{employeeId}/{period}` (ADR-105 §3)
  - [ ] TASK-303 — Summary tháng và dashboard năm. Mục §16 đặc tả: chuyển đổi
        metric giữa Orders / Sales / Converted Revenue / Accounting Profit /
        KPI Profit / % Target; lọc theo nguồn đơn All / Personal / ADS; so
        sánh nhân viên theo doanh thu quy đổi Personal và Ads riêng biệt;
        trend theo tháng cho từng nguồn đơn; tỉ trọng ADS trên tổng doanh thu
        quy đổi của mỗi người. Route: `/dashboard`, `/summary/{period}`
        (ADR-105 §3)
  - [ ] TASK-304 — màn hình cấu hình. Route: `/settings/employees`,
        `/settings/conversion`, `/settings/adjustments`, `/settings/targets`
        (ADR-105 §3)
  - [ ] TASK-305 — màn hình review queue và audit. Route: `/review`, `/audit`
        (ADR-105 §3)
  - [ ] TASK-306 — xuất Excel. Route: `/exports` (ADR-105 §3)
  - [ ] GATE-03 — Nghiệm thu MVP, mục 28 đặc tả, đủ 14 tiêu chí. Bổ sung:
        mọi route ở ADR-105 §3 phải mở trực tiếp được, refresh được,
        back/forward đúng, và chặn đúng khi truy cập trái quyền
        (`governance/core/02_ROUTING_RULES.md` → "Checklist Routing")

- [ ] PHASE-04 — Hoàn thiện
  - [ ] TASK-401 — tích hợp PriceMasterProvider. Schema mục §20 đặc tả:
        ProductCode, ProductName, Supplier, EffectiveFrom, EffectiveTo,
        PurchasePrice, Source, UpdatedAt. Tra theo ProductCode + SaleDate;
        giá tra được chỉ là giá trị *đề xuất*, luôn override được.
  - [ ] TASK-402 — product_mapper
  - [ ] TASK-403 — công thức hóa target và hoa hồng
  - [ ] TASK-404 — sheet kênh và Split Conversion. Mục §12 đặc tả: Split
        Conversion chỉ hỗ trợ như một ngoại lệ — workflow thông thường vẫn là
        một OrderID → một LeadSource → một ConversionScheme.

## Độ phủ đặc tả

Toàn bộ 31 mục của `docs/spec/Dac_ta_cong_cu_bao_cao_kinh_doanh.docx` đã được
truy vết tới một artifact và một task trong `docs/analysis/07_SPEC_COVERAGE.md`.
Không mục nào chưa được giao. Mục 27, 29 và 31 đã hoàn thành; các mục còn lại
đã phân tích hoặc ghi nhận, chờ Phase 1.

## Track Governance — Bảo Trì Nền Tảng (PHASE-GOV)

Track thứ hai, độc lập với roadmap sản phẩm Tín Phát ở trên. Track này audit
và sửa chính khung governance của repo (không phải tính năng Tín Phát). Chạy
song song, KHÔNG chặn PHASE-00..04 của Tín Phát trừ khi ghi rõ dependency.

Lịch sử: chạy trên nhánh `claude/s001-discovery-pka3fu` qua 7 session
(S001–S007, 2026-08-22 → 2026-08-23), merge vào nhánh mặc định qua PR#4/#5
(2026-08-23). Trong lúc merge, nội dung phần này từng bị nhánh Tín Phát ghi
đè hoàn toàn khỏi `PROJECT_PROGRESS.md` — không mất dữ liệu thật (mọi file
vẫn còn dưới `docs/audit/`, `docs/tasks/TASK-REM-*.md`), nhưng mất khả năng
nhìn thấy trong checklist canonical, khiến REM-T05 (đã READY, gate frozen)
trông như không tồn tại. Khôi phục lại ở đây theo DEC-118.

Chi tiết đầy đủ (không lặp lại ở đây — chỉ tóm tắt trạng thái):
`docs/audit/REMEDIATION_ROADMAP.md`, `docs/audit/S001_AUDIT_FINDINGS.md`,
`docs/audit/DECISIONS.md` (DEC-001..016 của riêng track này — đánh số trùng
với DEC-101..117 của Tín Phát chỉ là trùng dải số cũ trước khi tách theo
DEC-117, không phải cùng một quyết định).

### Trạng thái

- [x] **PHASE-01 — Governance Foundation Repair — DONE.** Phase Gate 01 PASS
      (10/10 check, S006). REM-T02, REM-T03, REM-T04, REM-T07 đều DONE.
      **Lưu ý:** REM-T02 (dời governance package lên root) trùng việc với
      TASK-000 của Track Tín Phát — xem ghi chú ở PHASE-00 phía trên. Cả hai
      hội tụ đúng cùng một kết quả, xác nhận bằng `validate_structure.py`
      PASS trên state hiện tại. Không cần làm lại; ghi nhận như bài học về
      chi phí của việc thiếu bước "đồng bộ nhánh" (DEC-118).
- [ ] PHASE-02 — Documentation & Evidence Truth-Up
  - [x] **REM-T05** — Sửa tài liệu và artifact kiểm chứng — MAJOR — Tier B —
        **DONE** (S008, 2026-08-23) — 4/4 check REQUIRED PASS (E1);
        CHECK-T05-05 (RECOMMENDED, E2) NOT_TESTED — không có reviewer độc
        lập khả dụng trong session solo, ghi giới hạn tường minh, không
        chặn DONE. Đóng FIND-005, FIND-006, FIND-011, FIND-012. File:
        `docs/tasks/TASK-REM-T05-documentation-truth-up.md`, handoff:
        `docs/sessions/S008-rem-t05-documentation-truth-up.md`.
  - [ ] Phase Gate 02 — chờ REM-T06
- [ ] PHASE-03 — Repository Hygiene
  - [ ] REM-T06 — Vệ sinh repository root — MICRO — Tier A — **READY, gate
        FROZEN** (S009 sẽ implement). Đóng FIND-009 (một phần đã xử lý —
        `.gitignore` đã có từ S003). File:
        `docs/tasks/TASK-REM-T06-repository-root-hygiene.md`.
  - [ ] Phase Gate 03 — đánh giá lại GAP-01 (Backup/DR)

### Finding còn OPEN

Không tự đóng chỉ vì bị mồ côi khỏi checklist ở lần merge trước:

| ID | Severity | Tóm tắt | Đóng bởi |
|---|---|---|---|
| FIND-009 | LOW | Thiếu root README/LICENSE (một phần đã xử lý) | REM-T06 |

### Finding đã RESOLVED (S008, 2026-08-23)

| ID | Severity | Tóm tắt | Đóng bởi | Bằng chứng |
|---|---|---|---|---|
| FIND-005 | MEDIUM | Báo cáo validation đã ship khẳng định một PASS sai sự thật | REM-T05 | `governance/reference/COMPACT_STRUCTURE_VALIDATION.md` nay trích dẫn lệnh + output thật của cả 5 validator (CHECK-T05-01) |
| FIND-006 | MEDIUM | START_HERE guide tự mâu thuẫn về layout | REM-T05 | 5 vị trí trong `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` đã sửa về layout compact (CHECK-T05-02) |
| FIND-011 | LOW | Bare reference không resolve trong changelog lịch sử | REM-T05 | Ghi rõ tường minh 2 loại trừ (`governance/reference/history/`, `docs/audit/`) trong báo cáo validation, không sửa file lịch sử |
| FIND-012 | LOW | README validator từng thiếu tài liệu hóa | REM-T05 | Re-verify CHECK-T05-03 PASS — đã DONE tiện thể ở REM-T03/S005, xác nhận chính thức ở đây |

### Việc phụ tồn đọng (không thuộc task nào)

- Owner xóa thủ công nhánh `scratch/ci-failure-test` trên GitHub (DEC-014,
  proxy chặn agent xóa).
- Owner cân nhắc bật branch protection cho check `governance`.

### Nợ Kỹ Thuật / Cảnh Báo Vận Hành

Ghi theo yêu cầu của Independent Review #4 khi duyệt TASK-108A-1.

### TD-001 — F2/F4 là WARNING, phải hiển thị trong Review Queue/UI

`tools/analysis/reconcile_conversion.py` phân loại kết quả thành HARD FAILURE
(F1/F3/F5 — quyết định exit code) và **WARNING / REVIEW SIGNAL** (F2/F4 —
không làm exit non-zero):

- **F2** — nhân viên đang `active` và hiệu lực trong kỳ nhưng không khớp dòng
  nào. Có thể sai `raw_prefix` (lỗi thật), cũng có thể chỉ là không có doanh
  số kỳ đó (bình thường).
- **F4** — tên chưa map có số dòng ≥ nhân viên đã map nhỏ nhất. Dấu hiệu
  master data đang thiếu người đáng kể.

**Yêu cầu bắt buộc:** hai cảnh báo này **phải được hiển thị rõ ràng** trong
Review Queue / UI khi xây (TASK-110 trở đi). **Không được âm thầm bỏ qua.**

**Vì sao:** một F4 bị nuốt nghĩa là một nhân viên thật đang bán hàng mà hệ
thống không biết — và theo DEC-127 §8, mọi dòng của người đó trả `Unresolved`,
tức **không nhận tỉ lệ nào**, tức không vào KPI của ai. Im lặng ở đây là mất
doanh số của một người thật khỏi bảng lương.

Owner: TASK-110. **ĐÃ XỬ LÝ (S016). Bảy vòng review siết dần provenance:
#1 yêu cầu mỗi mục phải truy vết được (S017); #2 yêu cầu F4 bỏ qua
`employee_raw` rỗng và F6 chấm theo effective dating từng dòng (S018); #3 yêu
cầu F3 chỉ đánh dấu dòng thật sự ambiguous, F4 giữ mọi biến thể raw, và F6
không phát khi thiếu ngày — HD-110-04/DEC-130 (S019); #4 yêu cầu **mọi**
provenance dựng từ chính tập row của finding, và F3 cũng cần ngày —
HD-110-05/DEC-131 (S020); #5 là một **Architecture Repair** — xóa nguồn sự
thật thứ hai cho việc chọn employee record, xóa kênh provenance song song
(`details`), và fail-fast cho master data hỏng — HD-110-06/07/08 → **DEC-132**
(S021). *(Câu "Chưa vòng nào PASS; chờ Review #6" ở đây là bản ghi tại thời
điểm S021 — **SUPERSEDED**. Trạng thái hiện tại: vòng review trên `R1-A1` đã
**PASS — ELIGIBLE_FOR_FREEZE** tại `a853971`, `R1-A1 = FROZEN` theo **DEC-139**;
`R1-A`/`R1` tổng vẫn NOT FROZEN, `TASK-110` vẫn NOT DONE.)* F2/F4 nay do `app/modules/validation/validator.py` sinh ra trên chính
luồng `run_import()`, không còn chỉ nằm trong script phân tích chạy tay. Bằng
chứng: **CHECK-110-12** (F2 có mặt trong `ImportResult.review_queue`),
**CHECK-110-13** (F4, và F2/F4 không làm `run_import()` raise),
**CHECK-110-14** (`reconcile_conversion.py` giữ nguyên hành vi, 24/24 test
không sửa). Cả ba PASS. Tiêu chí F1–F5 đã dời sang
`app/modules/validation/employee_mapping.py`; script phân tích import ngược
lại đúng các tên đó, nên hai đường dùng chung một bộ tiêu chí thay vì hai bản
cài đặt. Xem `docs/tasks/TASK-110-validation-review-queue.md`.

**Chưa đóng hoàn toàn:** màn hình duyệt thật vẫn là TASK-305 — hiện F2/F4 nằm
trong `ImportResult`, chưa có UI hiển thị. Đóng hẳn TD-001 khi TASK-305 xong.

## Session tiếp theo cho track này

S009 — REM-T06 (vệ sinh repository root, MICRO, Tier A, **gate FROZEN**) →
sau đó Phase Gate 02 → Phase Gate 03. Không chặn Track Tín Phát — có thể xen
kẽ vào bất kỳ lúc nào một session rảnh, hoặc sau khi GATE-00 duyệt, tùy chủ
dự án quyết định thứ tự ưu tiên.

## Sơ đồ phụ thuộc sơ bộ

```
TASK-000 → TASK-001 → TASK-002 → TASK-003 → GATE-00
GATE-00  → TASK-101 → TASK-102 → TASK-103 → TASK-104
                                   ↓          ↓
                        TASK-105 → TASK-106 → TASK-107 → TASK-108 → TASK-109
                                                                       ↓
                                              TASK-110 ─────────────→ TASK-111 → TASK-112 → GATE-01
GATE-01  → TASK-201 → TASK-202 → TASK-203 → TASK-204 → TASK-205
TASK-205 → TASK-301 … TASK-306 → GATE-03 → PHASE-04
```

Làm song song được: TASK-105 có thể chạy cùng lúc với TASK-103/TASK-104;
TASK-110 có thể chạy cùng lúc với TASK-108/TASK-109.

## Chấm điểm sơ bộ

| Task | Difficulty | Risk | Blast Radius | Mode | Primary Tier | Escalation |
|---|---|---|---|---|---|---|
| TASK-000 | 1 | 1 | 2 | MICRO | A | B |
| TASK-001 | 2 | 2 | 1 | MAJOR | C | — |
| TASK-002 | 3 | 2 | 1 | MAJOR | C | — |
| TASK-003 | 2 | 2 | 2 | MICRO | C | — |
| TASK-101 | 3 | 3 | 3 | MAJOR | B | C |
| TASK-102 | 2 | 3 | 3 | MAJOR | B | C |
| TASK-103 | 2 | 4 | 4 | MAJOR | B | C |
| TASK-104 | 3 | 4 | 5 | MAJOR | C | — |
| TASK-105 | 3 | 3 | 3 | MAJOR | B | C |
| TASK-106 | 4 | 4 | 4 | MAJOR | C | — |
| TASK-107 | 2 | 4 | 4 | MAJOR | B | C |
| TASK-108 | 3 | 5 | 5 | MAJOR | C | — |
| TASK-109 | 3 | 4 | 4 | MAJOR | B | C |
| TASK-110 | 3 | 3 | 2 | MAJOR | B | C |
| TASK-111 | 3 | 2 | 2 | MAJOR | B | C |
| TASK-112 | 1 | 2 | 2 | MICRO | A | B |
| TASK-201 | 3 | 4 | 5 | MAJOR | C | — |
| TASK-202 | 3 | 4 | 4 | MAJOR | C | — |
| TASK-203 | 3 | 3 | 4 | MAJOR | B | C |
| TASK-204 | 3 | 5 | 5 | MAJOR | C | — |
| TASK-205 | 4 | 4 | 4 | MAJOR | C | — |
| TASK-301…306 | 3 | 2 | 3 | MAJOR | B | C |

Risk 4–5 tập trung ở TASK-104, TASK-106, TASK-108, TASK-201, TASK-204 và
TASK-205 — những task mà một lỗi âm thầm trở thành một con số sai trên lương
của ai đó, hoặc rò rỉ dữ liệu cá nhân khách hàng. Các task này bắt buộc E1 và
khuyến nghị E2 theo quy tắc bằng chứng của profile.

## Completion Gate sơ bộ

Được chốt và đóng băng cho từng task trước khi task đó READY. Các REQUIRED
check sơ bộ ghi nhận ngay bây giờ:

- Toàn bộ PHASE-01: số đơn duy nhất của Tín Phát phải bằng 254 cho 01.2026 và
  146 cho 06.2026 đối chiếu với file thô thật (E1). Mọi chênh lệch còn lại so
  với báo cáo mẫu phải được giải thích bằng văn bản, không được làm tròn cho
  khớp. **✅ VERIFIED 2026-08-23 (TASK-101, CHECK-101-08)** — khớp tuyệt đối
  cả hai kỳ, xem `docs/tasks/TASK-101-importer-normalizer.md`.
- TASK-104: `LeadSource` chỉ nhận đúng hai giá trị `PERSONAL` và `ADS`. Không
  literal `TINPHAT_ADS` nào còn tồn tại trong mã nguồn hay tài liệu (E1, kiểm
  chứng bằng grep) — DEC-119.
- TASK-104: phân loại quyết định ở cấp OrderID và áp cho mọi dòng của đơn; hai
  dòng cùng `OrderID` không bao giờ mang hai `LeadSource` khác nhau (E1).
- TASK-108: `ConversionScheme` tra từ config theo `(employee, lead_source,
  ngày của đơn)`. Không đường code nào suy tỉ lệ trực tiếp từ `LeadSource`
  (E1). Case E/F của DEC-119 là phép kiểm: cùng `PERSONAL` như Kiên nhưng Nội
  thành phải ra 2 %, không phải 5,5 %.
- TASK-108: tra tỉ lệ dùng **ngày của đơn**, không dùng thời điểm chạy. Thêm
  một dòng chính sách có `effective_from` trong tương lai rồi chạy lại một kỳ
  lịch sử phải cho kết quả **không đổi** (E1) — DEC-121.
- TASK-108: nạp lợi nhuận KPI theo nhân viên-tháng **và** 14 giá trị `X` của
  workbook vào `conversion_engine` phải tái hiện đúng cột `F` của
  `Summary 2026` ở cả 14 kỳ (E1). Đây là phép kiểm engine cài đúng phép toán,
  thay cho mốc 13.883.242 đã gỡ theo DEC-120.
- TASK-108: một tổ hợp `(employee, lead_source, ngày)` không khớp dòng config
  nào phải trả về `Unresolved` và vào Review Queue — không bao giờ mượn tỉ lệ
  của nhân viên khác, không bao giờ mặc định về một tỉ lệ nào (E1).
- TASK-109/111: không có phép chia bù nào trong logic tổng hợp. Mọi con số
  cộng đúng một lần; dòng tổng phụ mang nhãn `RowType` và nằm ngoài mọi vùng
  SUM (DEC-115). Một phép `/2` trong logic tổng hợp là một lỗi
  (E1, kiểm chứng được bằng grep).
- TASK-101: `Chiết khấu` bị trừ khỏi doanh số ở toàn bộ 408 dòng bị ảnh hưởng;
  tổng 6 tháng là 36.750 nghìn đồng, trong đó 26.300 là của Ly (E1).
- TASK-104: cả 8 test case ADS ở mục 29 đặc tả đều PASS (E1).
- TASK-108: `TotalConvertedRevenue == PersonalConvertedRevenue + AdsConvertedRevenue`
  đúng cho mọi nhân viên-tháng, và không có đường code nào chia một lợi nhuận
  gộp cho một tỉ lệ duy nhất (E1).
- TASK-201/204: không có dữ liệu cá nhân khách hàng trong log ứng dụng; kiểm
  tra vai trò thực hiện ở phía server (E1, hướng tới E2).
- TASK-203: không tồn tại endpoint nào ghi vào `raw_rows` — không UPDATE,
  không DELETE, không PATCH. Kiểm chứng bằng `grep` trên toàn bộ định nghĩa
  router (E1). Đây là hệ quả trực tiếp của ADR-102, xem ADR-105 §2.
- TASK-203: mọi endpoint có mục Authorization được điền trong `API Contract
  Template`, không endpoint nào để trống (E1).
- TASK-204: với **mọi endpoint** ở ADR-105 §2 (trừ ba endpoint auth), một
  test gọi thẳng API bằng danh tính không phải `ADMIN` (chưa đăng nhập, hoặc
  đăng nhập với role khác) và khẳng định `403` — không phải khẳng định nút
  bị ẩn trên UI (E1, hướng tới E2 vì đây là bề mặt bảo mật).
- TASK-204: với danh tính `ADMIN`, test khẳng định từng endpoint trả đúng dữ
  liệu, không bị chặn nhầm — kiểm chứng bằng cách gọi API thật (E1).
- TASK-301…306 / GATE-03: mọi route ở ADR-105 §3 mở trực tiếp được, refresh
  được, back/forward đúng, có trạng thái not-found; không có màn hình chính
  nào chỉ tới được bằng tab state (E1, theo "Checklist Routing" của
  `governance/core/02_ROUTING_RULES.md`). Riêng frontend: danh tính không
  phải `ADMIN` phải nhận màn hình "không có quyền truy cập" ở mọi route
  nghiệp vụ, kể cả khi gõ thẳng URL (E1).
- Mọi phase: không tên nhân viên, tỉ lệ quy đổi, target, số tiền adjustment
  hay từ khóa ADS nào xuất hiện dưới dạng literal trong mã nguồn ứng dụng
  (E1, kiểm chứng được bằng grep).

**Lưu ý cho session sau — các check PHASE-02/03 ở trên là PRELIMINARY.**
`ADR-105` §4/§5 (phân quyền) đã chuyển **Accepted** (DEC-124, C12/C13/C14 đã
đóng); §2/§3 (route) vẫn Accepted như từ đầu. **Nhưng Completion Gate của
TASK-203/204 vẫn chưa freeze** — chấp nhận ADR khác với freeze gate. Quy
trình đúng khi PHASE-02 mở: chạy Roadmap Finalization đầy đủ cho TASK-203/204
(`governance/core/00_SESSION_ORCHESTRATION.md` → "Hoàn thiện Roadmap") rồi
mới freeze — bước này giờ nhanh hơn nhiều vì không còn câu hỏi nghiệp vụ nào
mở. Xem DEC-123, DEC-124.

## Trạng thái Task hiện tại

Task:
TASK-110 — Validation + Review Queue

Task Mode:
MAJOR

Status:
**MERGED vào nhánh mặc định (V4.1-1). NOT DONE.**

```
R1-A1    = FROZEN        (DEC-139 — Independent Review PASS — ELIGIBLE_FOR_FREEZE,
                          0 blocking finding, 1 hardening backlog HB-A1-05;
                          reviewed SHA  a85397106b81799d149d98e71a7fcfd5bc8963ad;
                          freeze  SHA   01a03b08ab6fc21b6b9ef3eeab5dfa1d692a8713)
R1-A     = NOT FROZEN
R1       = NOT FROZEN
TASK-110 = NOT DONE
CHECK-110-16 = REQUIRED · BLOCKED · POST_MERGE_PRODUCTION_ACCEPTANCE (DEC-141)
repair_cycles_used = EXHAUSTED_PRE_V4.1 · repair_cycles_remaining = 0
R1-A2 → R8 = OWNER_EXTENSION REQUIRED
```

**MERGE KHÔNG ĐỒNG NGHĨA DONE.** `TASK-110` chỉ chuyển `DONE` khi
`CHECK-110-16` thực sự `PASS` trên dữ liệu production thật. Không synthetic
PASS, không workbook giả, không bypass.

Bảng tiến độ từng unit (canonical, đọc trước file này cho câu hỏi "unit nào
đang làm"): `docs/tasks/TASK-110_REPAIR_PROGRESS.md`.

Completion Gate đã **FROZEN** (chủ dự án, 2026-08-23) — Gate không còn ở trạng
thái chờ duyệt, và code đã viết xong.

*Phần dưới đây là **bản ghi lịch sử** các vòng Independent Review — giữ nguyên
làm history, không phải trạng thái hiện tại:*

- **Independent Review #1 — FAIL, 6 finding** → đã sửa toàn bộ (S017), ba
  Human Decision ghi thành **DEC-129**.
- **Independent Review #2 — FAIL, 4 finding** → đã sửa toàn bộ (S018).
- **Independent Review #3 — FAIL, 3 finding** → đã sửa toàn bộ (S019); một
  Human Decision (**HD-110-04**) ghi thành **DEC-130**.
- **Independent Review #4 — FAIL, 2 provenance defect** → đã sửa toàn bộ
  (S020); một Human Decision (**HD-110-05**) ghi thành **DEC-131**.
- **Independent Review #5 — FAIL, 4 finding** → đã sửa toàn bộ bằng
  **Architecture Repair** (S021); ba Human Decision (**HD-110-06/07/08**) ghi
  thành **DEC-132**. Hai finding provenance đã tái xuất ở representation khác
  nhau qua các vòng trước, nên vòng này sửa **cơ chế sinh ra chúng** thay vì
  sửa representation: trạng thái sai không còn **biểu diễn được**.

- **Independent Review #6, #7, #8** — FAIL; #8 falsify các tuyên bố
  `ARCHITECTURE CLOSED` / `RC-1→RC-5 CLOSED` của #7, mở giai đoạn REPAIR MODE
  theo từng unit `R1` → `R8` (xem `docs/tasks/TASK-110-REPAIR-MODE.md`).
- **Vòng cuối trên `R1-A1` — PASS — ELIGIBLE_FOR_FREEZE** tại `a853971`
  (**DEC-139**). Đây là vòng review PASS đầu tiên của lineage; nó freeze
  **`R1-A1` và chỉ `R1-A1`**.

*(Bản ghi lịch sử kết thúc ở đây.)*

21/22 REQUIRED check PASS. **CHECK-110-16 (đối chiếu dữ liệu thật) vẫn
BLOCKED** — file thô production không có trong repo (đúng
`governance/product/17_DATA_GOVERNANCE_PRIVACY.md`) và không có trong
container. Theo **DEC-141** check này nay có Gate Class
`POST_MERGE_PRODUCTION_ACCEPTANCE`: **chặn DONE, không chặn merge**.

Phạm vi: **7 loại cảnh báo** (không phải 5), V7 mở thành **F1–F6** theo
DEC-129. Chấm điểm: Difficulty 3, **Risk 3** (kéo theo E1 bắt buộc cho mọi
check REQUIRED). Bốn khoảng trống nghiệp vụ của §18 đã đóng bằng **DEC-128**.

File: `docs/tasks/TASK-110-validation-review-queue.md`.
Trạng thái từng unit: `docs/tasks/TASK-110_REPAIR_PROGRESS.md`.
Handoff: `docs/sessions/S021-*.md` (Architecture Repair, mới nhất),
`S015-*.md` (Gate), `S016-*.md` (triển khai),
`S017-*.md` (sửa Review #1), `S018-*.md` (sửa Review #2),
`S019-*.md` (sửa Review #3), `S020-*.md` (sửa Review #4).

### TASK-108A-1 (task liền trước)

Task Mode:
MAJOR

Status:
**DONE** — 16/16 REQUIRED check PASS, 151/151 test, Independent Review #4
PASS, đã merge tại `c7a1b24`.

Required Gate Progress:
GATE-00 PASS (DEC-122). TASK-101, TASK-105, TASK-106, TASK-107, TASK-108A-1
đều **DONE**. Bộ test hiện tại: **346/346 PASS** (`pytest tests/ -q`) —
xem "Trạng thái Task hiện tại" cho TASK-110. Chi tiết từng task:
`docs/tasks/TASK-101-importer-normalizer.md`,
`docs/tasks/TASK-105-price-engine.md`,
`docs/tasks/TASK-106-adjustment-engine.md`,
`docs/tasks/TASK-107-profit-engine.md`.

Primary Agent Tier:
C

Escalation Tier:
—

### TASK-108A-1 — DONE (2026-08-23), Independent Review #4 PASS

Ba vòng pre-implementation review trước khi có dòng code nào. Kết quả chốt
thành **DEC-127** (8 quyết định nghiệp vụ) và **ADR-106** (ProductGroup +
hạ granularity xuống cấp line).

Thay đổi mô hình: `Nội thành` không còn là Employee — Vinh, Quý, Hiệp là ba
Employee thật, cùng `employee_group = NOI_THANH`. Thêm dimension
`ProductGroup` (`DIEN_MAY`/`GIA_DUNG`) ở **cấp product line**, vì đo được
118/10.609 OrderID chứa đồng thời cả hai loại. `ConversionScheme` do đó hạ
từ cấp Order xuống cấp line; `LeadSource` giữ nguyên cấp Order (DEC-119).

Resolver tra 4 chiều `(employee, employee_group, lead_source, product_group,
ngày của đơn)`: `lead_source` là lọc cứng, dòng cụ thể nhất thắng theo
specificity `4×employee + 2×group + 1×product_group`, **hòa điểm là lỗi cấu
hình** (engine từ chối chọn), không khớp là `Unresolved` (không fallback).

Bằng chứng trên dữ liệu thật: reconciliation 55 ô cột F của `Summary 2026`
— **52 khớp chính xác, 3 legacy, 0 lệch**; employee mapping đúng trên
**14.389 dòng** file thô toàn công ty với 107 dòng `unmapped` đúng C11.
16/16 REQUIRED check PASS, 119/119 test (36 mới), không regression.

**Bốn vòng independent review.** Bản đầu (`98142af`) có 119/119 test nội bộ
PASS và reconciliation tự báo "52 khớp, 0 lệch", nhưng reviewer độc lập vẫn
tìm ra bốn lớp lỗi qua ba vòng: nhân viên chưa map vẫn nhận tỉ lệ 5,5 %
(CRITICAL, ảnh hưởng trực tiếp tiền lương); manual override bỏ qua
effective date; reconciliation hard-code dimension tạo "khớp giả" ở 16/52 ô;
verification có oracle song song; sau đó là thiếu failure criterion cho raw
mapping, bỏ qua effective window, và dùng heuristic làm hard failure. Tất cả
đã sửa; **Review #4 PASS**. Chi tiết từng vòng:
`docs/tasks/TASK-108A-1-conversion-scheme-resolver.md` mục "Lịch Sử
Independent Review".

**Kết quả đối chiếu cuối:** 36 ô khớp độc lập / 0 lệch / 19 ô ghi nhận
LIMITED (nhãn báo cáo gộp + legacy, không có artifact production để nối) —
**không đưa về 52 bằng bất kỳ assumption nào**.

Chi tiết: `docs/tasks/TASK-108A-1-conversion-scheme-resolver.md`.

### TASK-107 — DONE (2026-08-23)

`profit_engine.compute_accounting_profit()` + `apply_accounting_profit()` —
`AccountingProfit = (SellPrice − AccountingPurchasePrice) × Quantity`,
Universal formula, `None` khi bất kỳ input nào thiếu (không bao giờ 0).
Trước khi code, chủ dự án chốt **DEC-126**: 6 nguyên tắc ranh giới, quan
trọng nhất là AccountingProfit độc lập hoàn toàn với KPI Adjustment, và
`EligibleKpiProfit` **không** thuộc scope task này (cần Adjustment record đã
xác nhận, persistence đó chưa tồn tại). Nối vào `run_import()` làm bước 9,
tự động — không cần lựa chọn thủ công như TASK-106, vì đây là hàm thuần túy
của các field đã sẵn có. 6/6 REQUIRED check PASS, 83/83 test tổng (9 mới,
không regression). Chi tiết: `docs/tasks/TASK-107-profit-engine.md`.

### TASK-106 — DONE (2026-08-23)

`AirConditionerClassifier` (dò từ khóa điều hòa trên `ProductRaw`, NFC-
normalize, không phân biệt hoa/thường) + `AdjustmentResolver`
(`resolve_suggested_amount()` — Qua kho/NCC giao tra `delivery_method_tiers`
theo phương tiện giao; KHBH/Thợ lắp chỉ có mặc định khi `is_air_conditioner=True`).
DEC-125 làm rõ: không có nguồn raw cho từ vựng adjustment — module này
**không** nối vào `run_import()`, khác hẳn `PendingPriceProvider` (TASK-105).
Trả giá trị **đề xuất**, không tự áp; `None` khi không có căn cứ (không bao
giờ suy đoán, không coi 0 — DEC-103). 5/5 REQUIRED check PASS, 74/74 test
tổng (17 mới, không regression trên 57 test TASK-101+105). Chi tiết:
`docs/tasks/TASK-106-adjustment-engine.md`.

### TASK-105 — DONE (2026-08-23)

`PriceProvider` (Protocol) + `PendingPriceProvider` + `price_engine.apply_prices()`,
nối vào `run_import()` làm bước 8. Vì chưa có Price Master nào tồn tại ở
Phase 1, mọi dòng đều `Pending` — đúng hành vi kỳ vọng, không phải giới hạn
tạm thời. Không bao giờ coi giá thiếu là 0 (DEC-103), kiểm chứng cả khi
provider có dữ liệu cho sản phẩm khác trong cùng lần chạy. Provider tùy
chỉnh cắm được qua dependency injection (`run_import(price_provider=...)`)
mà không sửa `price_engine`/`provider.py` — chuẩn bị sẵn cho TASK-401
(Phase 4) tích hợp Price Master thật. 9/9 REQUIRED check PASS, 57/57 test
tổng (8 mới, không regression). Chi tiết:
`docs/tasks/TASK-105-price-engine.md`.

### TASK-101 — DONE (2026-08-23)

Implement xong ngày 2026-08-23 với 12/13 REQUIRED check PASS trên fixture
tổng hợp ẩn danh; CHECK-101-08 (đối chiếu 254 đơn 01.2026 / 146 đơn 06.2026)
BLOCKED vì thiếu `data/samples/` thật trong môi trường phiên đó.

**Cùng ngày, phiên kế tiếp:** chủ dự án cung cấp trực tiếp 2 file thật của
Tín Phát (xuất riêng theo tháng, 01.2026 và 06.2026). Chạy
`tools/analysis/reconcile_real_data.py` gọi thẳng `app.pipeline.run_import()`
— kết quả:

- 01.2026: 254 đơn — khớp tuyệt đối với kỳ vọng.
- 06.2026: 146 đơn — khớp tuyệt đối với kỳ vọng.
- Đối chiếu chéo độc lập với dòng "Tổng cộng" tự có trong chính file thô
  (không do engine tính): khớp tuyệt đối cả doanh số lẫn chiết khấu ở cả hai
  tháng — xác nhận không sót, không đếm trùng dòng nào.
- 100% đơn Tín Phát phân loại ADS qua mặc định nhân viên (DEC-109), 0 đơn qua
  từ khóa "ADS" — khớp phát hiện gốc (chuỗi "ADS" không xuất hiện trong dữ
  liệu công ty).
- So sánh `Doanh số bán` (raw) với `SellPrice × Quantity − Discount`: mọi
  chênh lệch quan sát được (22/351 dòng ở 01.2026, 1/180 dòng ở 06.2026) đều
  giải thích được bằng đúng một pattern đã biết trước — DEC-114 (raw là số
  gross, chưa trừ chiết khấu). Không có pattern lệch nào khác, không cần và
  không sửa business rule.

**CHECK-101-08 chuyển PASS. TASK-101 chuyển DONE.** Không sai lệch nghiệp vụ
đáng kể. Chi tiết đầy đủ (kèm bảng số liệu hai kỳ):
`docs/tasks/TASK-101-importer-normalizer.md` → mục "Đối Chiếu Dữ Liệu Thật".
File thật đã xóa khỏi môi trường làm việc sau khi dùng, đúng DEC-108 — chưa
từng commit vào git.

Sửa thêm theo góp ý review: CHECK-101-05 từng ghi heading "8 case A–G" gây
hiểu nhầm task đã kiểm chúng — đã sửa lại chỉ claim phạm vi `LeadSource`
thật sự thuộc TASK-101; 8 case A–G (ConversionScheme) vẫn thuộc TASK-108,
không mở rộng phạm vi TASK-101 sang đó.

### GATE-00 — PASS (2026-08-23)

**Đã duyệt.** Chủ dự án đọc `docs/analysis/` cùng đợt rà soát nghiệp vụ
DEC-119/120/121, sau đó xác nhận trực tiếp trong hội thoại — nguyên văn và
đầy đủ hệ quả ghi ở **DEC-122**. Lượt duyệt: 1/1.

Ba điểm chủ dự án đã xác nhận biết trước khi duyệt (không phải giả định ngầm):

1. **Lịch sử 2026 không khớp workbook cũ** — Hoàng và Kiên cao hơn 6,0 %
   (+837.503 nghìn, ~3,0 triệu tiền thưởng) do bỏ di trú (DEC-120). Chủ dự án:
   *"chấp nhận"*.
2. **C9** — đơn của Nội thành/Gia dụng có chữ "ADS" quy đổi ở 7,5 % (không có
   dòng scheme riêng). Chủ dự án: *"luôn không xuất hiện ADS, không cần quan
   tâm"* — đóng, không đổi cấu hình.
3. **C10** — chính sách 2027 chưa có gì khác 2026 để cấu hình. Chủ dự án:
   *"không đổi"* — đóng cho hiện tại, mở lại nếu có tin mới.

PHASE-01 mở khóa ngay khi duyệt. Không cần vòng duyệt bổ sung nào cho GATE-00.

### Đã trả lời

| # | Câu hỏi | Trả lời |
|---|---|---|
| C1 | Tín Phát có nên mặc định ADS không? | **Có** — mọi đơn của Tín Phát quy đổi 7,5% bất kể ghi chú. DEC-109, sửa đổi bởi DEC-119. Số liệu lịch sử của Tín Phát không cần di trú gì cả. |
| C5 | Loại dòng nào tính vào số SP, doanh số, lợi nhuận, số đơn? | Dòng phụ có giá trị tiền **có** tính vào doanh số và lợi nhuận, không tính vào số SP, và mỗi dòng đều vào hàng đợi duyệt tay để giữ lại hoặc loại trừ. DEC-110. |
| C6 | Nhân viên có sửa được `Diễn giải` không? | **Có.** Mặc định ERP giữ nguyên; nhân viên chỉ sửa khi là đơn ADS. DEC-111. |
| C7 | Lợi nhuận ADS lịch sử của Hoàng và Kiên xử lý thế nào? | **Không di trú** — lịch sử mặc định PERSONAL. DEC-120 (thay thế DEC-112). |
| C8 | Số SP có loại trừ dòng phụ có giá trị tiền không? | **Có**, và bản thân chỉ số này giá trị thấp — vẫn giữ làm cột nhưng bỏ khỏi tiêu chí gate. DEC-113. |
| C4 | `Chiết khấu` trừ vào đâu? | **Trừ vào doanh số.** DEC-114. Đã xác minh số của ERP là gross, nên đây là một phép sửa thật, không phải trừ hai lần. |
| C4b | Chiết khấu có trừ vào lợi nhuận không? | **Có.** DEC-122, xác nhận trực tiếp 2026-08-23. |
| C2 | Vì sao sheet kênh chia đôi? | **Có dòng tổng phụ theo ngày nằm trong vùng dữ liệu**, nên một phép SUM đơn thuần bị đếm hai lần. Đã giải thích, không tái tạo — dòng tổng phụ chuyển ra ngoài vùng SUM, đánh dấu bằng nhãn `RowType`. DEC-115. |
| C3 | Rule hoa hồng? | **Dựa trên mức đạt target**; công thức hóa ở TASK-403 như kế hoạch. Phase 1 nạp bảng tỉ lệ quan sát được làm dữ liệu. DEC-116. |
| C9 | Tỉ lệ ADS cho Nội thành/Gia dụng? | **Không quan tâm** — tổ hợp này không xảy ra trong thực tế, giữ mặc định 7,5%. DEC-122. |
| C10 | Chính sách 2027 khác 2026 ở đâu? | **Không đổi**, tính đến 2026-08-23. DEC-122. |

### Còn mở

Danh sách đầy đủ: `docs/analysis/10_OPEN_QUESTIONS.md`.

| # | Câu hỏi | Mặc định đang áp dụng | Cần trước |
|---|---|---|---|
| C11 | 88 dòng nhân viên chưa map xử lý thế nào khi lên production? | Review Queue loại `Missing`, không tính vào KPI của ai. Chủ dự án: *"tôi chưa rõ"* (2026-08-23). | GATE-01 |

Không chặn GATE-00 (đã PASS) hay Phase 1 — mặc định Review Queue đã an toàn:
không âm thầm bỏ, không âm thầm gán nhân viên.

Cũng đã ghi nhận, không chặn: tổng tháng trong Summary mẫu bỏ sót 60,0% doanh
thu quy đổi (`05 §A2`), và Kiên mang cùng một số ADS gõ tay `7565` suốt ba
tháng liên tiếp (`05 §B2`). Cả hai không phải câu hỏi cần chủ dự án trả lời
ngay — cả hai được ghi lại để giải thích được khi con số của công cụ khác với
bảng tính.

## Micro Task (Inline)

Checklist chuẩn:
`governance/templates/MICRO_TASK_CHECKLIST.md`

### MICRO-003 — Architecture Decision Records
Status:
DONE

Checklist Reference:
`governance/templates/MICRO_TASK_CHECKLIST.md`

Evidence Summary:
E1 — `docs/adr/ADR-101-architecture-and-stack.md`,
`docs/adr/ADR-102-three-layer-data-model-and-audit.md`,
`docs/adr/ADR-103-currency-unit-standard.md` tồn tại và theo đúng cấu trúc
đặt tên/section của `docs/adr/README.md`.

### MICRO-000 — Đưa gói governance lên gốc repository
Status:
DONE

Checklist Reference:
`governance/templates/MICRO_TASK_CHECKLIST.md`

Evidence Summary:
E1 — đã chạy `git mv`, `ls` xác nhận `CLAUDE.md`, `PROJECT/`, `docs/`,
`governance/` ở gốc repository; `git status` cho thấy 74 pure rename, không
đổi nội dung. Commit `8f77e20`.

## Blocker đang hoạt động
- **B-01 (S060)** — sự kiện `purchase_price_history` ghi TRƯỚC repair thẩm
  quyền không có nhãn `ta` và không được viết lại, nên vĩnh viễn không đủ
  thẩm quyền. Mọi mã có ít nhất một sự kiện như vậy sẽ Pending. Đây là kết
  quả ĐÚNG theo `SILENT_ERROR_RATE = 0`; gỡ nó cần một artifact thẩm quyền do
  Owner xác nhận, cùng hạng `HistoricalConfirmedRegistry`.
- **B-02 (S060)** — repair Tracking chưa deploy (branch riêng, chưa merge),
  nên trước deploy độ phủ thực tế của reader chỉ gồm các mã KHÔNG có sự kiện
  lịch sử nào.
- **B-03 (S060)** — Reports không lưu GIỜ bán, chỉ ngày. Một ngày có thay đổi
  giá ở giữa là Pending theo thiết kế. Nâng độ phân giải `sale_date` là thay
  đổi data contract → thuộc quyết định của Owner.

## Rủi ro đang hoạt động

- **RISK-01 — Từ khóa ADS chưa có dữ liệu nào để đứng vững.** Chuỗi "ADS"
  xuất hiện 0 lần trong sổ bán hàng thô và 0 lần trong workbook báo cáo. Rule
  từ khóa được xây đúng đặc tả, nhưng chỉ bắt đầu khớp khi cách nhập liệu thay
  đổi. DEC-109 xử lý phần lớn nhất — 1.108 đơn của Tín Phát (12,7%) được phân
  loại ADS từ mặc định cấp nhân viên chứ không phải từ khóa — nên phần chưa
  đánh dấu còn lại là công việc ADS của các nhân viên khác.
  Giảm thiểu: override tay ở cấp OrderID có audit trail; công cụ báo cáo số
  đơn khớp rule mỗi lần import, để một tháng toàn số 0 hiện ra rõ ràng thay vì
  bị mặc nhiên coi là đúng.

- **RISK-02 — ĐÃ XỬ LÝ 2026-08-22.** Tín Phát mặc định `ADS` (DEC-109, sửa đổi
  bởi DEC-119), nên tỉ lệ 7,5% được giữ nguyên, không con số nào thay đổi. Còn
  lại: đánh dấu một đơn là ADS *làm giảm* doanh thu quy đổi (5,5% chia ra số
  lớn hơn 7,5%), nên đánh dấu ADS quá tay sẽ khiến nhân viên mất tiền. Review
  queue phải hiện cả đơn mới chuyển sang ADS, không chỉ đơn mới chuyển về
  PERSONAL.

- **RISK-05 — Chênh lệch 6,0% của Hoàng và Kiên trên dữ liệu lịch sử.** Hệ quả
  trực tiếp của DEC-120 (không di trú): doanh thu quy đổi 01–08.2026 của hai
  người sẽ là 14.720.745 thay vì 13.883.242 nghìn đồng đang báo cáo — cao hơn
  837.503 nghìn, kéo theo khoảng 3,0 triệu đồng tiền thưởng. Chiều lệch *có
  lợi* cho nhân viên.
  Giảm thiểu: chênh lệch đã được định lượng chính xác và ghi tại
  `docs/analysis/06_ADS_RULE_VERIFICATION.md` §6.1 và §8, nên giải thích được
  bất cứ lúc nào. DEC-112 vẫn còn nguyên vẹn để kích hoạt lại nếu GATE-01 kết
  luận chênh lệch này không chấp nhận được.

- **RISK-03 — Giá nhập vắng mặt ở nguồn.** File thô không mang giá nhập, chỉ
  có lợi nhuận do ERP tính sẵn. Theo quyết định của chủ dự án, trường này giữ
  Pending thay vì suy đoán. Hệ quả: lợi nhuận KPI và doanh thu quy đổi chưa
  đầy đủ cho tới khi công cụ bảng giá được kết nối hoặc giá được nhập tay.
  Công cụ phải hiển thị Pending rõ ràng và không bao giờ được âm thầm coi giá
  thiếu là bằng 0.

- **RISK-04 — Dữ liệu cá nhân khách hàng.** Tên, số điện thoại, địa chỉ trên
  mọi dòng. Dữ liệu mẫu bị `.gitignore` loại trừ; test cần fixture đã ẩn danh;
  trường dữ liệu cá nhân không được lọt vào log ứng dụng.

## Regression còn tồn đọng

- **REG-01 (mới, 2026-08-23) — `validate_reference_integrity.py` đang FAIL
  trên nhánh mặc định.** Ba reference không phân giải được, tất cả trong
  `docs/tasks/TASK-REM-T06-repository-root-hygiene.md`: README, CONTRIBUTING
  và CODE_OF_CONDUCT ở gốc repo (cố ý viết không có backtick ở đây — xem đoạn
  cuối mục này).

  Đây là **forward-reference tới chính các file mà REM-T06 sẽ tạo** — task
  file mô tả sản phẩm bàn giao của nó bằng backtick, và validator coi mọi
  chuỗi backtick kết thúc bằng `.md` là một reference cần phân giải.

  Xuất hiện từ commit `2d5cf9b` ("Hoàn thiện Ready Gate REM-T06"), **không
  phải** do session soạn ADR-105 gây ra — đã kiểm chứng bằng cách stash toàn
  bộ thay đổi của session này rồi chạy lại validator: vẫn đúng 3 lỗi đó.
  Nghĩa là CI trên nhánh mặc định đang đỏ kể từ `2d5cf9b`.

  **Chưa sửa, có chủ đích.** Sửa nội dung task file của REM-T06 khi gate của
  nó đã FROZEN là đụng vào Scope Lock của một task khác — đúng thứ DEC-012 đã
  rút kinh nghiệm ("khi phát hiện một sửa đổi thuộc task khác trong lúc làm
  việc, ghi nhận nó thay vì tự sửa"). Tiền lệ ngược lại cũng có: S005 từng sửa
  ngay reference do chính task đó tạo ra (commit `1da459d`) — nhưng khi ấy là
  task đang implement, không phải task đã frozen chờ session khác.

  **Đóng ở S009 (REM-T06)** — session đó vừa tạo ba file thật, vừa làm ba
  reference này phân giải được, nên lỗi tự biến mất mà không cần sửa văn bản.
  Nếu S009 bị hoãn lâu, cân nhắc một MICRO riêng để bỏ backtick khỏi ba tên
  file đó trong task file.

  **Bẫy cần biết cho mọi session:** viết tên một file *chưa tồn tại* trong
  backtick sẽ làm validator FAIL — kể cả khi đang mô tả nó như một sản phẩm
  sắp tạo, và kể cả trong chính ghi chú về lỗi đó. Session này vấp đúng bẫy
  ấy khi soạn mục REG-01 và phải viết lại không dùng backtick. Khi cần nhắc
  tên một file sắp tạo, viết trần (README.md) thay vì trong backtick.

## Quyết định gần đây
- Xem `PROJECT/PROJECT_DECISIONS.md` — DEC-101 đến DEC-124 (track Tín Phát).
  Các quyết định mới nhất:
  - **DEC-119** — tách `LeadSource` khỏi `ConversionScheme`; `TINPHAT_ADS` bị
    loại bỏ. Xem ADR-104.
  - **DEC-120** — không di trú dữ liệu ADS lịch sử; thay thế DEC-112. Gỡ mốc
    13.883.242 khỏi REQUIRED check của TASK-108.
  - **DEC-121** — 2026 là giai đoạn chuyển đổi; mốc chuẩn chính thức
    01/01/2027; mọi business rule mang `effective_from`/`effective_to` và tra
    theo ngày của đơn.
  - **DEC-122** — GATE-00 PASS; PHASE-01 mở khóa.
  - **DEC-123** — Roadmap Finalization **sơ bộ** cho TASK-203/204; ADR-105
    (route map + mô hình phân quyền) dựng lần đầu, ba mặc định tạm cho
    C12/C13/C14.
  - **DEC-124** — chủ dự án quyết định trực tiếp: MVP chỉ một vai trò
    `ADMIN`, không `viewer`/`editor`/`employee_scope`. Đóng C12/C13/C14.
    ADR-105 §4/§5 viết lại, chuyển `Accepted`. Completion Gate TASK-203/204
    vẫn chưa freeze.
- Xem `docs/audit/DECISIONS.md` — DEC-001 đến DEC-016 (track Governance,
  dải số riêng, xem DEC-117 về lý do tách).

## Lịch sử Session
- S093 (giai đoạn 3) — PRA-002 PRODUCTION ACCEPTANCE CLOSEOUT — 2026-09-03 — Owner hoàn tất
  ba thao tác đọc còn lại. `/nhan-vien` 200 với legacy source LEG-20260902-4ffe5198
  (Báo cáo Kinh doanh 2026.xlsx, Tháng 08/2026) → PRA-001 không hồi quy và bản nhập legacy
  trước deploy không đổi. Render Metrics KHÔNG có telemetry Memory/CPU → numeric peak
  NOT_OBSERVED, không bịa số; cận trên < 512 MB xác lập bằng cơ chế fail-stop (limit cứng
  512 MB, vượt ⟹ OOM-kill ⟹ instance failed; hai upload COMPLETE + service Live liên tục +
  state sống sau F5 ⟹ chưa từng chạm ngưỡng), đúng như dòng Evidence của CHECK-15 quy về
  "không OOM". MISSING_REQUIRED_EVIDENCE = NONE. `CHECK-PRA002-15 = PASS`; 16/16 check
  REQUIRED PASS; Exit Criteria 6/6 → **TASK-PRA-002 = DONE**. 0 dòng production code;
  budget 1.460/1.500 không đổi; review budget 1/2. INTEGRATION_READY = YES (chưa integrate).
- S093 (giai đoạn 2) — PRA-002 PRODUCTION ACCEPTANCE TỪ BẰNG CHỨNG OWNER — 2026-09-03 —
  Owner deploy `c2142dd` lên Render (Live, manual, 10:36:11 GMT+7, 24.0s) và chạy hai
  lần upload workbook thật trên `reports.tinphatcrm.com`. Production chứng minh trực tiếp:
  40 đơn · 61 dòng · HEADER_CONSISTENT 2026-09-01→03 · lần 1 INSERT 61 · lần 2 SAME 61 /
  INSERT 0 / SOURCE_CHANGED 0 / COLLISION 0 · Accounting coverage 100% · Tracking live thật
  (AUTO 15 / Review 25 / 0 dòng không nhận ra) · hai run COMPLETE có snapshot · state sống
  sau F5 · KHÔNG double count. Ma trận REQUIRED của CHECK-15 dựng theo hợp đồng freeze:
  14/17 assertion PASS_PRODUCTION_UI, 3 assertion NOT_OBSERVED (`/nhan-vien` 200; legacy
  import không đổi; Render Metrics RAM đỉnh < 512 MB). Không suy PASS cho phần chưa quan sát,
  không tạo yêu cầu mới. `CHECK-PRA002-15` giữ `NOT_TESTED`; TASK-PRA-002 vẫn IN_PROGRESS;
  BLOCKING_FINDINGS 0; 0 dòng production code; budget 1.460/1.500 không đổi.
- S093 — PRA-002 PRODUCTION ACCEPTANCE — 2026-09-03 — Xác minh canonical đứng đúng
  `c2142dd` (khớp REQUIRED, không moved) và chứng minh delta `d7a1154..c2142dd` là
  4 commit docs-only (diff `app/`+`tools/`+hạ tầng = RỖNG) → cây mã deploy bằng
  đúng cây mã đã E2 ACCEPT. Deploy KHÔNG thực hiện được: agent proxy trả CONNECT
  403 cho cả `reports.tinphatcrm.com` và `api.render.com` (policy denial), và
  workbook thật không có trong environment. KHÔNG chế access, KHÔNG bịa bằng chứng
  production. `CHECK-PRA002-15` giữ `NOT_TESTED`; TASK-PRA-002 vẫn IN_PROGRESS.
  0 dòng production code; budget 1.460/1.500 không đổi. Runbook UI tối thiểu cho
  Owner + oracle nghiệm thu: `docs/sessions/S093-pra-002-production-acceptance.md`.
- S092 — PRA-002 WHOLE-TASK INDEPENDENT REVIEW E2 — 2026-09-03 — Review độc lập
  toàn task (slice A + B + C1 + RDA) đối chiếu Completion Gate frozen S079.
  Canonical `d7a1154a…` khớp EXPECTED; RDA branch `14499dd` docs-only; 0
  production code sau accepted C1. Reviewer tái lập trên PostgreSQL 16.13 thật:
  migration 0002_snapshots, đẳng thức state(A,B) == state(B), SOURCE_CHANGED,
  NOT_SEEN → REMOVED_CANDIDATE vẫn current vẫn tính, FIND-PRA002-A1 invariant,
  RESULT_REVISED, route xac-nhan-du, persist sau restart. LOC đo lại 1.460/1.500
  khớp. RDA evidence S090/S091 review theo provenance. BLOCKING = 0, 0 repair
  cycle. CHECK-PRA002-17 → PASS (E2); CHECK-15 NOT_TESTED. TASK-PRA-002 vẫn
  IN_PROGRESS. Evidence: `docs/reviews/TASK-PRA-002-INDEPENDENT-REVIEW-RECORD.md`.
- S091 (phần 2) — PRA-002 RDA CLOSEOUT — 2026-09-03 — Owner xác nhận tường
  minh "Đúng, đây là file đầy đủ 01/09–03/09" và cho phép đường controlled-copy
  ASSUMPTION D14. Thực hiện coverage confirmation thật qua `POST xac-nhan-du`
  (HEADER_CONSISTENT → CONFIRMED_COMPLETE, 2026-09-01..2026-09-03,
  `n_removed_candidate` 0 — đúng vì A ⊂ B). Đóng hai assertion mà dữ liệu thật
  không tự tạo ra, bằng controlled copy dẫn xuất từ REAL snapshot B (dán nhãn
  CONTROLLED_COPY_EVIDENCE, không commit, B gốc không sửa): RDA-4 — đúng 1
  SOURCE_CHANGED với `changed_fields` = sell_price + total_sales_raw và
  `SUM(total_sales)` đổi đúng +200.000; RDA-5 — trước xác nhận NOT_SEEN 1, sau
  xác nhận REMOVED_IN_SOURCE_CANDIDATE 1, dòng bị xoá VẪN current VẪN trong SUM,
  COUNT(*) mọi bảng fact không giảm. RDA-6 PASS (Golden 58/2; mệnh đề cohort
  S068 là có điều kiện). CHECK-PRA002-14 chuyển BLOCKED → PASS. 0 dòng
  production code; CHANGE_BUDGET không đổi (1.460/1.500); review budget không
  tiêu. TASK-PRA-002 vẫn IN_PROGRESS — CHECK-PRA002-15 Production Acceptance
  chưa PASS. Evidence: `docs/sessions/S091-pra-002-real-overlap-snapshot-b.md`.
- S091 — PRA-002 REAL DATA ACCEPTANCE: REAL OVERLAP A → B (EVIDENCE ONLY) —
  2026-09-03 — Owner upload snapshot B thật (`So_chi_tiet_ban_hang_8.xlsx`,
  header `Từ ngày 01/09/2026 đến ngày 03/09/2026`, 61 dòng / 40 đơn); exact
  bytes của snapshot A (S090) còn nguyên nên chạy được **đường ưu tiên hai
  export thật** của mục 15, trên hai PostgreSQL 16.13 cô lập. A ⊂ B xác nhận
  (0 khoá chỉ có ở A). B first import: INSERT 13 / SAME 35 / SOURCE_CHANGED 13.
  **SOURCE_CHANGED lần đầu quan sát được trên dữ liệu thật** — kế toán bổ sung
  `delivery_cost` cho 13 dòng 01/09 và `imei` cho 8 dòng, mọi trường tiền giữ
  nguyên; version cũ immutable, version mới appended, current trỏ version mới,
  `changed_fields` đúng nguyên văn. Đẳng thức frozen `state(A,B) == state(B)`
  khớp tuyệt đối kể cả tập (khoá, `line_fingerprint`); no double count (A→B
  593.550.000 == B, khác naive A+B 1.061.850.000). Exact reupload B: SAME 61,
  0 source version mới. Accounting oracle B khớp `run_import` (GB-4) và footer
  workbook; Golden 58 passed/2 skipped. Coverage B = HEADER_CONSISTENT; không
  POST `xac-nhan-du`. FIND-RDA-01 → OWNER_SEMANTIC_CONFIRMED, parser repair
  KHÔNG cần (DEFER). RDA-5 BLOCKED (cần export thật có chứng từ biến mất +
  Owner xác nhận). CHECK-PRA002-14 chuyển NOT_TESTED → BLOCKED. 0 dòng
  production code; CHANGE_BUDGET không đổi (1.460/1.500).
  Evidence: `docs/sessions/S091-pra-002-real-overlap-snapshot-b.md`.
- S090 — PRA-002 REAL DATA ACCEPTANCE (EVIDENCE ONLY) — 2026-09-02 — Owner
  upload MỘT workbook kế toán THẬT trong phiên (`So_chi_tiet_ban_hang_7.xlsx`,
  48 dòng / 34 đơn / 2026-09-01; không commit, không sửa, SHA256 trước == sau).
  Chạy qua route production `POST /run` trên PostgreSQL 16.13 thật, database cô
  lập, `alembic_version = 0002_snapshots`. RDA-1 PASS (INSERT 48 / SAME 0 /
  SOURCE_CHANGED 0); RDA-2 exact reupload PASS (SAME 48 = line_count, 0 source
  version mới, `duplicate_of` đúng); no-double-count chứng minh bằng current
  state chụp xen giữa hai lần import — 48 dòng / 34 đơn / 468.300.000 không
  đổi, keyset và per-order identical; accounting oracle khớp tuyệt đối
  `run_import` (GB-4) và footer workbook; Golden 58 passed/2 skipped.
  RDA-3/4/5 `BLOCKED_OWNER_INPUT` (cần export thật thứ hai A ⊂ B);
  `SOURCE_CHANGED = NOT_OBSERVED_IN_REAL_DATA`; `RESULT_REVISED = 0` là kết quả
  đúng. FIND-RDA-01 header dạng thứ ba → `OWNER_DECISION_REQUIRED`,
  NON_BLOCKING, không nới parser. 0 dòng production code; CHANGE_BUDGET không
  đổi (1.460/1.500). CHECK-PRA002-14 giữ `NOT_TESTED` (hợp đồng đòi đủ bảng
  mục 15). Evidence: `docs/sessions/S090-pra-002-real-data-acceptance.md`.
- S060 — REPORTS HISTORY READER V1 (Session 1/2) — 2026-08-29 — Trace mã
  production hai repo; xác nhận bằng bằng chứng rằng `purchase_price_history.t`
  không có thẩm quyền nào (client `Date.now()`, rules không `.validate`);
  repair Tracking trên branch riêng (server timestamp + nhãn `ta` được rules
  kiểm, không rewrite sự kiện cũ); dựng
  `app/modules/pricing/tracking_history/` (snapshot/reader/provider) với hợp
  đồng khoảng-bán vì Reports chỉ có độ phân giải NGÀY; unresolved đi vào
  `Missing.PurchasePrice` của TASK-110; `CUTOVER_DATE 2026-09-01` không đổi.
  Reports 1107 passed/11 skipped; Tracking 2286 đạt/0 hỏng + build.
  Implementation PASS, NOT DONE — chờ independent review (Session 2).
  Evidence: `docs/sessions/S060-reports-history-reader-v1.md`.
- S000 — MỞ DỰ ÁN — 2026-08-22 — Đọc đặc tả và cả hai workbook mẫu; xác minh
  business rule với dữ liệu thật; chọn profile PRODUCT; tạo roadmap, sơ đồ phụ
  thuộc, chấm điểm và completion gate sơ bộ; ghi nhận 8 quyết định chiến thuật
  và 4 rủi ro đang hoạt động. Sau đó hoàn thành TASK-002 (sáu tài liệu phân
  tích, có script trích xuất bằng chứng chạy lại được) và TASK-003 (ba ADR).
  Dừng ở GATE-00.
- 2026-08-23 — Merge PR#4 vào nhánh mặc định `claude/extract-upload-repo-gq2ws4`,
  hợp nhất với nhánh audit bộ khung quản trị (S001–S007). Phát hiện và sửa va
  chạm mã số: cả hai track cùng dùng DEC-001..016 và cả hai đều có một
  `ADR-001`. Renumber toàn bộ quyết định và ADR của dự án Tín Phát sang
  DEC-101..117 / ADR-101..103 (DEC-117 ghi nhận chính việc renumber này);
  khôi phục nguyên văn 16 quyết định gốc của track audit vào
  `docs/audit/DECISIONS.md` để không mất tính toàn vẹn của các tham chiếu
  DEC-XXX mà `docs/audit/`, `docs/sessions/`, `docs/tasks/TASK-REM-*.md` và
  `governance/scripts/governance/README.md` đang trích dẫn. Đã chạy lại cả 5
  validator của governance và bộ test rule ADS sau khi sửa — toàn bộ PASS.
  Nội dung roadmap của dự án Tín Phát không đổi qua lần merge này.
- 2026-08-23 — **Hợp nhất hai track (DEC-118).** Một session được yêu cầu rà
  soát tiến độ phát hiện nhánh local đang lỗi thời 14 commit so với nhánh mặc
  định thật trên origin, dẫn tới một câu trả lời sai trước đó ("3 file đặc tả
  Report chưa được intake"). Sau khi fast-forward về đúng state, phát hiện
  track Governance (S001–S007) đã bị merge PR#4/#5 ghi đè khỏi
  `PROJECT_PROGRESS.md` — REM-T05 (READY, gate frozen) và REM-T06 không còn
  xuất hiện trong checklist canonical nào. Khôi phục lại dưới mục "Track
  Governance — Bảo Trì Nền Tảng (PHASE-GOV)" phía trên. Xác nhận TASK-000 và
  REM-T02 đã làm trùng một việc (dời governance lên root) trên hai nhánh
  khác nhau — cả hai hội tụ đúng kết quả, không cần làm lại. Thêm cơ chế bắt
  buộc đồng bộ nhánh cho mọi session tương lai: SessionStart hook
  (`.claude/hooks/session-start.sh` + `.claude/settings.json`, nới
  `.gitignore` để commit được hai file này), bước 0 mới trong
  `governance/core/00_SESSION_ORCHESTRATION.md` → "Giao thức Mở Phiên", và
  mục "Đồng Bộ Nhánh" mới trong `CLAUDE.md`. Đã chạy lại cả 5 validator sau
  toàn bộ thay đổi — PASS. Push thẳng lên nhánh mặc định theo yêu cầu trực
  tiếp của chủ dự án.
- 2026-08-23 — **S008 — REM-T05 DONE (Track Governance).** Đồng bộ nhánh
  trước tiên (bước 0), xác nhận HEAD khớp origin default branch. Chạy lại
  toàn bộ 5 validator tại thời điểm thực thi (không copy baseline S007) và
  dán output thật vào `governance/reference/COMPACT_STRUCTURE_VALIDATION.md`,
  kèm nêu rõ 2 loại trừ của `validate_reference_integrity.py`. Sửa 5 vị trí
  layout pre-compact trong `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` (4 dòng đã biết
  trước — 83, 85, 144, 146 — cộng 1 dòng phát hiện thêm khi thực thi, dòng
  179 PHẦN 3, cùng loại lỗi, đã sửa và ghi nhận minh bạch thay vì âm thầm mở
  rộng); rút gọn khối liệt kê tay 21 required path ở PHẦN 2 thành hướng dẫn
  chạy validator để tránh tái diễn chính vấn đề FIND-005/006 mô tả (hai
  nguồn sự thật dễ lệch nhau). Re-verify README validator vẫn liệt kê đủ mọi
  script (kể cả `regression_nested_layout.py` mới từ S007) — không cần sửa.
  Xác nhận `governance/reference/history/` không bị đụng bằng `git diff`.
  4/4 REQUIRED check PASS (E1); CHECK-T05-05 (RECOMMENDED, E2) NOT_TESTED —
  không có reviewer độc lập trong session solo, ghi giới hạn rõ ràng, không
  chặn DONE theo đúng điều kiện task đã ghi. Đóng FIND-005, FIND-006,
  FIND-011, FIND-012.

- 2026-08-23 — **Rà soát xác nhận nghiệp vụ trước khi chuyển Phase.** Chủ dự
  án gửi 10 xác nhận nghiệp vụ kèm chỉ thị không tự chuyển Phase. Rà soát lại
  toàn bộ tài liệu phân tích, ADR, data mapping, formula mapping và acceptance
  criteria theo các xác nhận đó. Phát hiện và xử lý ba mâu thuẫn thật: (1)
  `TINPHAT_ADS` là một giá trị enum nguồn đơn có chứa tên nhân viên, khiến
  `PERSONAL` bị hiểu là đồng nghĩa 5,5% và khiến Nội thành/Gia dụng chỉ tồn
  tại được dưới dạng ngoại lệ ngoài mô hình → tách thành `LeadSource` và
  `ConversionScheme` (DEC-119, ADR-104 mới); (2) xác nhận số 6 phủ định
  DEC-112 và làm mất hiệu lực một REQUIRED check đã ghi trong completion gate
  (mốc 13.883.242) → DEC-120 thay thế DEC-112, thay bằng một check tái lập
  được, ghi rõ chênh lệch +6,0% mà quyết định này tạo ra (RISK-05 mới); (3)
  yêu cầu mốc 2027 chưa có chỗ nào trong thiết kế → DEC-121, kèm ràng buộc tra
  cứu theo ngày của đơn. Bổ sung 8 test case A–G do chủ dự án chỉ định, 2
  check hai bucket end-to-end và 3 check tra theo thời điểm vào
  `tools/analysis/verify_ads_rule.py` — **31/31 PASS**. Sửa một tham chiếu
  DEC-009 lỗi thời còn sót trong script sau đợt renumber DEC-117. Ghi 4 câu
  hỏi nghiệp vụ còn mở vào `docs/analysis/10_OPEN_QUESTIONS.md` (C4b, và C9,
  C10, C11 mới). GATE-00 giữ nguyên trạng thái VERIFYING — đợt xác nhận này là
  đầu vào cho việc duyệt, không phải bản thân lượt duyệt.
- 2026-08-23 — **GATE-00 PASS (DEC-122).** Chủ dự án duyệt trực tiếp trong
  hội thoại: (a) chấp nhận chênh lệch +6,0% của Hoàng/Kiên; (b) C4b — chiết
  khấu trừ cả lợi nhuận; (c) C9 — tổ hợp Nội thành/Gia dụng + ADS không xảy
  ra trong thực tế, không cần đổi cấu hình; (d) C10 — chính sách 2027 chưa có
  gì khác 2026; (e) C11 — chưa rõ, giữ mở, không chặn. Cập nhật
  `docs/analysis/10_OPEN_QUESTIONS.md` đóng C4b/C9/C10, giữ C11 mở. Chuyển
  Current Task từ GATE-00 sang TASK-101, đánh dấu PHASE-00 DONE trong roadmap.
  Đồng bộ `PROJECT/LO_TRINH_DE_HIEU.md` theo "Giao thức Đóng Phiên". Merge
  `origin/claude/extract-upload-repo-gq2ws4` (REM-T05 DONE, Track Governance,
  không chồng lấn nội dung với thay đổi Track A) trước khi push. Chạy lại cả
  5 validator governance — PASS.
- 2026-08-23 — **Roadmap Finalization sơ bộ cho TASK-203/204 (DEC-123).** Chủ
  dự án hỏi roadmap đã tính tới bảo mật qua backend và phân chia router chưa.
  Rà soát cho kết quả: nguyên tắc có đủ (`ADR-101` phân lớp, `04_SECURITY_RULES`
  và `02_ROUTING_RULES` đều Mandatory và cấm thẳng những thứ được hỏi), nhưng
  TASK-203/204 mỗi cái chỉ là một dòng một câu, ba vai trò được đặt tên mà
  chưa định nghĩa, và không có danh sách route nào trong repo. Soạn `ADR-105`
  (24 endpoint backend, 14 route frontend gán cho TASK-301…306, ma trận 3 vai
  trò × 13 năng lực, ba phát biểu ràng buộc ranh giới backend/frontend). Mở
  rộng TASK-203/204, gán route cho TASK-301…306 và GATE-03, thêm 6 check
  PRELIMINARY. **Cố ý không freeze** — ADR-105 ở trạng thái `Proposed`, vì
  PHASE-02 còn xa và vì ma trận phân quyền chứa ba câu hỏi nghiệp vụ chủ dự án
  chưa được hỏi (C12/C13/C14 mới trong `docs/analysis/10_OPEN_QUESTIONS.md`).
  Không đổi thứ tự task, không đổi Current Task — TASK-101 vẫn là việc tiếp
  theo. Chạy lại cả 5 validator governance — PASS.
- 2026-08-23 — **TASK-101 implement (Python thuần, ADR-101).** Tạo
  `docs/tasks/TASK-101-importer-normalizer.md`, freeze Completion Gate trước
  khi code. Xây 7 module: `domain` (dataclass `RawRow`/`WorkingLine`/`Order`,
  `Decimal` VND nguyên theo ADR-103), `config/loader` (YAML + effective-dating
  theo DEC-121), `importing` (raw_reader đọc đúng layout header dòng 4/data
  dòng 6, preview metadata, normalizer trừ `Chiết khấu` theo DEC-114),
  `mapping/employee_mapper` (DEC-104, config-driven, dòng chưa map được flag
  không bị bỏ), `orders/order_builder` (nhóm theo OrderID),
  `lead_source/classifier` (DEC-119/ADR-104, chuỗi 4 bậc, tách khỏi
  ConversionScheme). Đây cũng là năng lực lõi mà TASK-102/103/104 định xây
  riêng — không tạo 3 task trùng lặp, đánh dấu chúng hoàn thành phần lõi
  trong roadmap.

  Vì `data/samples/` không tồn tại trong môi trường này (DEC-108 — dữ liệu cá
  nhân khách hàng không commit), dựng fixture tổng hợp đã ẩn danh
  (`tests/fixtures/synthetic_workbook.py`, 8 dòng/7 đơn synthetic, không liên
  quan dữ liệu thật) làm cơ sở test. 49/49 test PASS
  (`pytest tests/ -q`), gồm: 18 case LeadSource port nguyên văn từ
  `tools/analysis/verify_ads_rule.py` để đối chiếu hành vi. Static check xác
  nhận: không import `fastapi`/`sqlalchemy` trong `app/modules/`, không
  hard-code business value (chỉ có hằng số cấu trúc `ADS = "ADS"` của enum
  `LeadSource`), không `float` cho tiền, không log dữ liệu cá nhân.

  12/13 REQUIRED check PASS (E1 trên fixture). **CHECK-101-08 BLOCKED** —
  đối chiếu 254 đơn (01.2026) / 146 đơn (06.2026) với file thô thật đòi hỏi
  `data/samples/So_chi_tiet_ban_hang.xlsx`, không có trong session này. Ghi
  rõ BLOCKED, không bịa PASS, không đoán số. TASK-101 dừng ở **VERIFYING**,
  không DONE. Cập nhật roadmap: TASK-101 đánh dấu VERIFYING; TASK-102,
  TASK-103, TASK-104 đánh dấu phần lõi đã có, ghi rõ phạm vi còn thiếu (kênh
  UI, product classification) dời sang lúc cần.
- 2026-08-23 — **TASK-101 → DONE: đóng CHECK-101-08 bằng dữ liệu thật.**
  Review trước đó yêu cầu 5 việc: (1) sửa wording CHECK-101-05 vì heading cũ
  nói đã kiểm 8 case A–G trong khi Evidence nói chưa — sửa lại chỉ claim
  đúng phạm vi `LeadSource` của TASK-101, không đụng ConversionScheme;
  (2)(3) chủ dự án cung cấp trực tiếp 2 file thật Tín Phát (01.2026,
  06.2026, xuất riêng theo tháng) — chạy `tools/analysis/reconcile_real_data.py`
  (script mới, gọi thẳng `run_import()`) tính đủ các chỉ số reviewer yêu
  cầu: raw rows, OrderID duy nhất, employee mapped/unmapped, tổng doanh số
  raw, chiết khấu, doanh số normalized, PERSONAL/ADS breakdown theo nguồn
  (mặc định nhân viên vs từ khóa), OrderID thiếu, OrderID nhiều employee.
  Kết quả: 254/146 đơn khớp tuyệt đối cả hai kỳ; đối chiếu chéo độc lập với
  dòng "Tổng cộng" tự có trong file thô (không do engine tính) cũng khớp
  tuyệt đối; (4) so sánh `Doanh số bán` raw vs `SellPrice×Qty−Discount` —
  mọi lệch (22/351 và 1/180 dòng) đều đúng bằng số ở cột Chiết khấu, khớp
  100% với DEC-114 đã biết trước, không phải phát hiện mới, không sửa rule;
  (5) không mở rộng sang ConversionScheme — xác nhận giữ nguyên ranh giới.
  CHECK-101-08 chuyển PASS, TASK-101 chuyển DONE (13/13 REQUIRED check
  PASS). File thật xóa khỏi môi trường sau khi dùng, chưa từng commit
  (DEC-108). Current Task chuyển sang TASK-105.
- 2026-08-23 — **Đơn giản hóa phân quyền — ADMIN-only (DEC-124).** Chủ dự án
  trả lời trực tiếp, đóng cùng lúc C12/C13/C14 mà DEC-123 để mở: công cụ quản
  trị nội bộ, MVP chỉ một vai trò `ADMIN`, không `viewer`/`editor`/
  `employee_scope`. Non-ADMIN nhận `403` ở mọi API trừ `auth/login`,
  `auth/logout`, `auth/me`, và không mở được frontend; phân quyền vẫn kiểm ở
  backend, không chỉ ẩn UI. Database thiết kế cho phép thêm vai trò sau này
  (cột `role` enum), không xây trước hạ tầng nhiều vai trò.

  Viết lại `ADR-105` §4 (ma trận 3 vai trò → nhị phân ADMIN/không-ADMIN) và
  §5 (`employee_scope` hạn chế → mở rộng vai trò trong tương lai, không xây
  trước); §2/§3 (route) không đổi. Chuyển §4/§5 sang `Accepted` — thêm annotation
  "Sửa đổi 2026-08-23" vào DEC-123 thay vì viết lại lịch sử. Đóng C12/C13/C14
  trong `docs/analysis/10_OPEN_QUESTIONS.md`, chuyển vào bảng "Đã đóng". Cập
  nhật `PROJECT/PROJECT_PROFILE.md` (Authentication), 2 check PRELIMINARY của
  TASK-204 (ma trận → nhị phân). **Completion Gate TASK-203/204 vẫn KHÔNG
  freeze** — chấp nhận ADR khác với freeze gate của task còn hai phase nữa
  mới tới. Đồng bộ `PROJECT/LO_TRINH_DE_HIEU.md`. Chạy lại 5 validator
  governance — PASS.
- 2026-08-23 — **TASK-105 DONE (price_engine + PriceProvider).** Tạo
  `docs/tasks/TASK-105-price-engine.md`, freeze Completion Gate trước khi
  code. Mở rộng `WorkingLine` thêm `accounting_purchase_price` và
  `price_source` (default `Pending`, không bao giờ suy ra 0 — DEC-103, khớp
  nguyên tắc 03_DATA_MODEL_RULES §5 đã dùng cho quantity/sell_price ở
  TASK-101). Định nghĩa `PriceProvider` (Protocol) ổn định cho TASK-401 sau
  này, và `PendingPriceProvider` — implementation đúng cho 100% dòng ở
  Phase 1 vì thật sự chưa có Price Master nào, không phải giới hạn của môi
  trường test (khác TASK-101, không cần dữ liệu thật để đối chiếu). Nối
  `apply_prices()` vào `run_import()` làm bước 8, thêm tham số
  `price_provider` tùy chọn cho dependency injection. 8 test mới (provider,
  price_engine, 2 test tích hợp pipeline dùng provider giả lập) — xác nhận
  cả trường hợp provider "thật" miss một sản phẩm vẫn giữ Pending, không
  âm thầm dùng giá của sản phẩm khác. 9/9 REQUIRED check PASS, 57/57 test
  tổng, không regression trên 49 test TASK-101. Current Task chuyển sang
  TASK-106.
- 2026-08-23 — **TASK-106 DONE (adjustment_engine).** Trước khi code: chủ
  dự án làm rõ 4 điểm nghiệp vụ qua AskUserQuestion, ghi lại thành **DEC-125**
  — kết luận đúng phương án (b) mà S011 đã nêu: `KpiAdjustment` không có
  nguồn raw, là dữ liệu chọn tay sau khi import, không phải thứ để "parse".
  Bốn quy tắc cụ thể: Qua kho/NCC giao tính theo phương tiện giao (xe máy
  nhẹ/cồng kềnh/ô tô = -50k/-100k/-200k, không theo model); KHBH/Thợ lắp chỉ
  có mặc định khi sản phẩm là điều hòa (-50k/-200k), ngoài điều hòa luôn
  nhập tay; nhận diện điều hòa bằng khớp từ khóa trên `ProductRaw` (đã xác
  nhận khả thi trên dữ liệu thật); kích hoạt là người dùng chọn tay, không
  có quét tự động. Tạo `docs/tasks/TASK-106-adjustment-engine.md`, freeze
  Completion Gate trước khi code. Xây `AirConditionerClassifier` +
  `AdjustmentResolver` (`app/modules/adjustment/`) + `config/adjustments.yaml`
  — **module tính toán độc lập, không nối `run_import()`, không thêm field
  domain model** (khác TASK-105 — không có "mọi dòng đều Pending" nào đúng
  ở đây, vì không có nguồn dữ liệu thật nào để tự động áp). 17 test mới, tất
  cả nhánh (3 tier × 2 loại, AC/non-AC × 2 loại, không khớp, loại lạ) đều
  trả `None` đúng lúc, không suy đoán. 5/5 REQUIRED check PASS, 74/74 test
  tổng, không regression. Current Task chuyển sang TASK-107.
- 2026-08-23 — **TASK-107 DONE (profit_engine).** Ngay sau khi chấp nhận
  TASK-106 DONE, chủ dự án chốt luôn 6 nguyên tắc ranh giới cho profit/
  adjustment trước khi cho phép code TASK-107 — ghi lại thành **DEC-126**:
  (1) AccountingProfit độc lập hoàn toàn với KPI Adjustment; (2) Adjustment
  không ghi đè dữ liệu kế toán; (3) một Order phải hỗ trợ nhiều Adjustment
  records khi có persistence thật; (4) phân biệt `suggested_amount` (từ
  `AdjustmentResolver`, TASK-106) và `final_amount` (người dùng xác nhận);
  (5) chỉ Adjustment đã xác nhận mới dùng cho `EligibleKpiProfit`; (6) không
  mặc định adjustment chưa xác định = 0. Hệ quả: TASK-107 **chỉ** triển khai
  `AccountingProfit`, không tự mở rộng sang `EligibleKpiProfit` vì
  persistence/xác nhận Adjustment chưa sẵn sàng. Xây
  `profit_engine.compute_accounting_profit()` (hàm thuần túy, `None` khi
  thiếu bất kỳ input nào) + `apply_accounting_profit()`, nối vào
  `run_import()` làm bước 9 — tự động, không cần chọn tay (khác TASK-106) vì
  chỉ dùng field đã sẵn có trên `WorkingLine`. Xác nhận bằng grep:
  `profit_engine` không có bất kỳ import/dependency nào vào
  `app.modules.adjustment`. 9 test mới, gồm case cố ý đặt discount cực lớn
  để xác nhận công thức không bị discount ảnh hưởng (đúng §U, khác
  `TotalSales`). 6/6 REQUIRED check PASS, 83/83 test tổng, không regression.
  Current Task chuyển sang TASK-108.

## Nợ Kỹ Thuật / Cảnh Báo Vận Hành

Ghi theo yêu cầu của Independent Review #4 khi duyệt TASK-108A-1.

### TD-001 — F2/F4 là WARNING, phải hiển thị trong Review Queue/UI

`tools/analysis/reconcile_conversion.py` phân loại kết quả thành HARD FAILURE
(F1/F3/F5 — quyết định exit code) và **WARNING / REVIEW SIGNAL** (F2/F4 —
không làm exit non-zero):

- **F2** — nhân viên đang `active` và hiệu lực trong kỳ nhưng không khớp dòng
  nào. Có thể sai `raw_prefix` (lỗi thật), cũng có thể chỉ là không có doanh
  số kỳ đó (bình thường).
- **F4** — tên chưa map có số dòng ≥ nhân viên đã map nhỏ nhất. Dấu hiệu
  master data đang thiếu người đáng kể.

**Yêu cầu bắt buộc:** hai cảnh báo này **phải được hiển thị rõ ràng** trong
Review Queue / UI khi xây (TASK-110 trở đi). **Không được âm thầm bỏ qua.**

**Vì sao:** một F4 bị nuốt nghĩa là một nhân viên thật đang bán hàng mà hệ
thống không biết — và theo DEC-127 §8, mọi dòng của người đó trả `Unresolved`,
tức **không nhận tỉ lệ nào**, tức không vào KPI của ai. Im lặng ở đây là mất
doanh số của một người thật khỏi bảng lương.

Owner: TASK-110. **ĐÃ XỬ LÝ (S016). Bảy vòng review siết dần provenance:
#1 yêu cầu mỗi mục phải truy vết được (S017); #2 yêu cầu F4 bỏ qua
`employee_raw` rỗng và F6 chấm theo effective dating từng dòng (S018); #3 yêu
cầu F3 chỉ đánh dấu dòng thật sự ambiguous, F4 giữ mọi biến thể raw, và F6
không phát khi thiếu ngày — HD-110-04/DEC-130 (S019); #4 yêu cầu **mọi**
provenance dựng từ chính tập row của finding, và F3 cũng cần ngày —
HD-110-05/DEC-131 (S020); #5 là một **Architecture Repair** — xóa nguồn sự
thật thứ hai cho việc chọn employee record, xóa kênh provenance song song
(`details`), và fail-fast cho master data hỏng — HD-110-06/07/08 → **DEC-132**
(S021). *(Câu "Chưa vòng nào PASS; chờ Review #6" ở đây là bản ghi tại thời
điểm S021 — **SUPERSEDED**. Trạng thái hiện tại: vòng review trên `R1-A1` đã
**PASS — ELIGIBLE_FOR_FREEZE** tại `a853971`, `R1-A1 = FROZEN` theo **DEC-139**;
`R1-A`/`R1` tổng vẫn NOT FROZEN, `TASK-110` vẫn NOT DONE.)* F2/F4 nay do `app/modules/validation/validator.py` sinh ra trên chính
luồng `run_import()`, không còn chỉ nằm trong script phân tích chạy tay. Bằng
chứng: **CHECK-110-12** (F2 có mặt trong `ImportResult.review_queue`),
**CHECK-110-13** (F4, và F2/F4 không làm `run_import()` raise),
**CHECK-110-14** (`reconcile_conversion.py` giữ nguyên hành vi, 24/24 test
không sửa). Cả ba PASS. Tiêu chí F1–F5 đã dời sang
`app/modules/validation/employee_mapping.py`; script phân tích import ngược
lại đúng các tên đó, nên hai đường dùng chung một bộ tiêu chí thay vì hai bản
cài đặt. Xem `docs/tasks/TASK-110-validation-review-queue.md`.

**Chưa đóng hoàn toàn:** màn hình duyệt thật vẫn là TASK-305 — hiện F2/F4 nằm
trong `ImportResult`, chưa có UI hiển thị. Đóng hẳn TD-001 khi TASK-305 xong.

## Session tiếp theo

> **Cập nhật 2026-09-02 (S076):** repair cycle 1/1 của TASK-PRA-001 đã
> xong — hai blocking finding của Independent Review đã sửa, DEC-168 đóng
> `CHANGE_BUDGET_EXCEEDED`. `1600 passed, 11 skipped`. Session tiếp theo:
> re-review độc lập; rồi Owner deploy PostgreSQL (CHECK-09) và chạy
> `verify_legacy_import` trên file Excel thật (CHECK-01). Repair budget đã
> hết (0 còn lại) — finding blocking tiếp theo phải leo thang.
>
> **Cập nhật 2026-09-02 (S075):** TASK-PRA-001 = IMPLEMENTED. Legacy
> Reference Vertical chạy đầu-cuối; `1586 passed, 11 skipped`. Session tiếp
> theo: (1) Owner phân xử `CHANGE_BUDGET_EXCEEDED`, (2) Independent Review,
> (3) Owner tạo Render PostgreSQL để đóng CHECK-09, (4) Owner chạy
> `verify_legacy_import` trên file Excel thật để đóng CHECK-01. Xem khối
> "S075 (2026-09-02)" ở đầu file và
> `docs/sessions/S075-pra-001-legacy-reference-vertical.md`.
>
> **Cập nhật 2026-09-02 (S074, close-out):** ADR-108 Accepted (DEC-167);
> TASK-PRA-000 DONE; TASK-PRA-001 READY — session tiếp theo implement PRA-001.
>
> **Cập nhật 2026-09-02 (S073):** kế hoạch đã được Owner review PASS;
> TASK-PRA-001 gate FROZEN, còn chờ Owner approve ADR-108 (persistence).
> Xem khối "PLANNED — PHASE-PRA finalization (S073)" ở đầu file.
>
> **Cập nhật 2026-09-02 (S072):** track mới PHASE-PRA (Persistent Reporting
> & Analytics) đã có kế hoạch tại
> `docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md`. Session
> đề xuất tiếp theo cho track này: Owner trả lời quyết định N.1–N.4 + N.12,
> rồi mở TASK-PRA-001 (Slice 1 — Legacy reference + nền DB) theo Roadmap
> Finalization. Xem khối "PLANNED — PHASE-PRA" trong CANONICAL CURRENT
> DELIVERY STATUS ở đầu file. Nội dung bên dưới là lịch sử của các track
> trước, giữ nguyên.


Có hai session được đề xuất, thuộc hai track độc lập — chủ dự án chọn thứ tự,
không có ràng buộc kỹ thuật bắt buộc cái nào trước:

### Track A (Tín Phát) — Recommended Session: TASK-108 (conversion_engine)

Purpose:
**TASK-107 đã DONE** (2026-08-23) — `AccountingProfit` tồn tại trên mỗi
`WorkingLine`, tự động tính ở bước 9, `None` khi giá nhập còn Pending.
`EligibleKpiProfit` cố ý chưa làm (DEC-126) — không chặn TASK-108, vì
`ConversionScheme`/quy đổi doanh thu không phụ thuộc `EligibleKpiProfit`.

TASK-108 là **task rủi ro cao nhất trong toàn bộ roadmap** (Risk 5/5, Blast
Radius 5/5 — xem bảng "Chấm điểm sơ bộ"). Bước 10–11 của §22 đặc tả: phân
giải `ConversionScheme` **độc lập** với `LeadSource` — tra config theo
`(employee, lead_source, ngày của đơn)` (DEC-119, DEC-121, ADR-104), sau đó
quy đổi doanh thu qua 2 bucket **độc lập** PERSONAL/ADS. Sai ở đây nghĩa là
sai lương/thưởng của ai đó.

Các REQUIRED check đã ghi sẵn ở mục "Completion Gate sơ bộ" phía trên (đọc
kỹ trước khi code) — trong đó quan trọng nhất:
- Không đường code nào suy tỉ lệ trực tiếp từ `LeadSource` — case E/F của
  DEC-119 là phép kiểm bắt buộc (cùng `PERSONAL` nhưng nhân viên Nội thành
  phải ra tỉ lệ khác nhân viên thường).
- Tra tỉ lệ dùng **ngày của đơn**, không dùng thời điểm chạy (effective-dating
  đúng, DEC-121) — thêm một dòng chính sách tương lai rồi chạy lại kỳ lịch sử
  phải cho kết quả không đổi.
- Tổ hợp `(employee, lead_source, ngày)` không khớp dòng config nào phải trả
  `Unresolved` + Review Queue — không mượn tỉ lệ của nhân viên khác, không
  mặc định về bất kỳ tỉ lệ nào.
- Nạp lại 14 kỳ của workbook mẫu phải tái hiện đúng cột `F` của `Summary
  2026` — đây là phép kiểm engine cài đúng phép toán.

Files to read first:
- `PROJECT/PROJECT_PROGRESS.md` mục "Completion Gate sơ bộ" — toàn bộ check
  TASK-108 đã ghi sẵn, đọc trước khi viết Ready Gate cho task
- `docs/adr/ADR-104-lead-source-vs-conversion-scheme.md` — kiến trúc tách
  LeadSource/ConversionScheme
- `PROJECT/PROJECT_DECISIONS.md` (DEC-119, DEC-120, DEC-121)
- `tools/analysis/verify_ads_rule.py` — bản tham chiếu đã verify 31/31 case,
  bao gồm case E/F dùng làm phép kiểm
- `app/modules/lead_source/classifier.py` — pattern config-driven +
  effective-dating đã dùng ở TASK-101, nên theo cùng phong cách
- `app/pipeline.py`, `app/modules/domain/models.py` — code đã có

### Track B (Governance) — Recommended Session: S009 — REM-T06

Purpose:
REM-T05 đã DONE (S008). REM-T06 (vệ sinh repository root, MICRO, Tier A) 
nay READY — gate FROZEN, sẵn sàng implement. Không còn cần hoàn thiện 
Ready Gate; S009 sẽ triển khai luôn. Xem "Track Governance — Bảo Trì Nền 
Tảng" phía trên để có chi tiết đầy đủ.

Files to read first:
- `PROJECT/PROJECT_PROGRESS.md` (mục "Track Governance")
- `docs/sessions/S008-rem-t05-documentation-truth-up.md`
- `docs/audit/S001_AUDIT_FINDINGS.md` (FIND-009)

### Ghi chú cho session nào mở PHASE-02 (chưa phải bây giờ)

`ADR-105` đã dựng sẵn bản đồ route (§2/§3) và mô hình phân quyền (§4/§5) cho
TASK-203/204. **Cả bốn mục đều `Accepted`** (DEC-123 cho §2/§3; DEC-124
2026-08-23 cho §4/§5, sau khi chủ dự án xác nhận trực tiếp: công cụ quản trị
nội bộ, chỉ một vai trò `ADMIN`, không `viewer`/`editor`/`employee_scope`
trong MVP). **Completion Gate của TASK-203/204 vẫn CHƯA freeze** — ADR được
chấp nhận không tự động freeze gate của task tương ứng.

Quy trình đúng khi PHASE-02 mở:
1. Chạy Roadmap Finalization đầy đủ cho TASK-203 và TASK-204
   (`governance/core/00_SESSION_ORCHESTRATION.md` → "Hoàn thiện Roadmap",
   9 bước), dùng ADR-105 làm bản thiết kế đã chốt chứ không phải bản nháp —
   không còn câu hỏi nghiệp vụ nào mở nên bước này nên nhanh.
2. Freeze Completion Gate dựa trên 6 check PRELIMINARY đã có sẵn trong mục
   "Completion Gate sơ bộ" phía trên, điều chỉnh nếu thực tế lúc đó khác.

Không còn phụ thuộc nghiệp vụ nào (C12/C13/C14 đã đóng) — bước 1 giờ chỉ còn
là thủ tục hoàn thiện gate, không cần hỏi lại chủ dự án gì thêm cho phần này.

### Bắt buộc cho cả hai track

Trước khi mở bất kỳ session nào ở trên: thực hiện "Đồng Bộ Nhánh" (đầu file
này) trước tiên. Đây chính là bước từng bị bỏ qua dẫn tới sự cố cần hợp nhất
hôm nay (DEC-118).
