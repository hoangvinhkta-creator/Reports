# S125 — TASK-UIUX-001: Tinh chỉnh UI/UX toàn bộ Reports cho người đọc quản trị

## 0. Exact Gate

```text
BRANCH        = claude/reports-ui-ux-refinement-3n5v8l
BASE_HEAD     = f1f9aa8a394ccbbff64af561bcb2a5319c6c99dd
                (= origin/claude/extract-upload-repo-gq2ws4, nhánh mặc định,
                 đã fetch và xác nhận HEAD cục bộ trùng trước khi đọc governance)
IMPL_HEAD     = 9d8bda85ce9fa4dfb8b310881758a9a79a0f9e65
                (commit mã nguồn + test)
FINAL_HEAD    = commit đóng phiên (docs/governance) ngay sau IMPL_HEAD
                trên cùng nhánh — xem `git log -2`
WORKING_TREE  = clean sau commit
TASK          = docs/tasks/TASK-UIUX-001-reports-ui-ux-refinement.md
DECISION      = DEC-190
```

## 1. Phạm vi phiên này

Lượt TINH CHỈNH TRÌNH BÀY toàn bộ web Reports theo chỉ thị bàn giao sau
khi Phase B đóng (`DEC-189`). Không phải vertical tính năng. Người dùng
chính được tối ưu: chủ doanh nghiệp / quản lý cấp cao. Finance
(`/home/user/Finance`) là THAM CHIẾU CHỈ ĐỌC — không file nào của Finance
bị đổi, không commit nào vào Finance.

Điều KHÔNG làm, đúng mục 7 của chỉ thị: không đổi business logic, công
thức, ngữ nghĩa doanh thu / lợi nhuận / DS quy đổi / Target, Product
Identity, thẩm quyền thương hiệu, gán nhân viên, Nội thành / Gia dụng,
loại dòng, Legacy, schema, migration, thẩm quyền ghi, route, thanh điều
hướng (`DEC-185` giữ đúng ba mục). Không tính năng mới, không trang mới,
không JavaScript, không thư viện.

## 2. Cách audit

1. Dựng Flask thật với dữ liệu giả lập đủ hình dạng thực tế (6 nhân viên ở
   hai nhóm, 20 dòng tháng 09 + 6 dòng tháng 08, dòng thiếu giá, dòng chưa
   phân loại, dòng lỗ, chiết khấu, Target nhóm + Target cá nhân, 19 tháng
   số cũ 2025–07/2026 với một import mỗi năm theo `DEC-181`).
2. Chụp 19 màn hình × 2 khổ (1366×900, 390×844) bằng Playwright + Chromium
   cài sẵn, đo `scrollWidth` từng trang.
3. Đọc `Finance/index.html` (CSS + hàm render `renderOverview`,
   `monthStatsHtml`, `fmtBig`/`signed`) để rút ngôn ngữ thiết kế.
4. Phân loại HIGH / MEDIUM / LOW theo mẫu USER PROBLEM · WHY IT MATTERS ·
   EXPECTED BEHAVIOR · UI FIX · RISK · BUSINESS_LOGIC_IMPACT (đầy đủ trong
   file task, mục "Kết Quả Audit").
5. Sửa các mục giá trị cao / rủi ro thấp; chụp lại 23 màn hình × 2 khổ
   (thêm trạng thái trống, kỳ chỉ có số cũ, trang Chạy báo cáo); chạy
   test.

## 3. Điều đã sửa (tóm tắt — chi tiết ở file task)

```text
H-01  Thẻ "Tổng số SP" trên Báo cáo không có nhãn (biến template chưa
      đăng ký)                                               → SỬA
H-02  Không ô nào trả lời "tháng này ra sao" trước; so tháng trước ở
      module thứ tư                                          → Ô CHỦ ĐẠO
H-03  Cột Nhóm lộ mã enum STANDARD_SALES / NOI_THANH         → tên từ master
H-04  Trang sổ thô kéo cả trang sang ngang ở 390px           → .tp-scroll
M-01  Số âm không phân biệt; mọi số đều đậm                  → .neg, 400/700
M-02  Cảnh báo dang dở và khoảng trống thương hiệu đều đỏ    → .warn / .notice
M-03  Bảng kê Nhân viên: pill kéo dài 7 cột, khách hàng bẻ
      dòng, thẻ đơn lẻ kéo hết chiều ngang                   → SỬA
M-04  Thương hiệu / Cơ cấu: 4–6 đoạn chú giải trước bảng     → <details>
M-05  Bảng kê chi tiết viết ngày ISO                         → DD/MM/YYYY
M-06  Cảnh báo sổ nạp đứng thứ sáu trên trang                → ngay dưới KPI
M-07  Tab Dữ liệu: cột Coverage hiện DETECTED_ONLY           → nhãn ngắn
M-08  Thẻ "Dòng chưa có ngày bán" to khi không có gì để nói  → footnote
L-01…L-04                                                    → SỬA
L-05  Nhãn "Shared Online Beta"                              → DEFERRED
L-06  Ô nhập Target VND thô                → DEFERRED_REQUIRES_BUSINESS_CHANGE
L-07  Timestamp ISO + tag LEGACY_REFERENCE ở tab Dữ liệu     → DEFERRED
L-08…L-10                                                    → GIỮ theo DEC
```

## 4. Điều đã rút từ Finance và điều cố ý KHÔNG chép

Thích nghi: một con số chủ đạo với dòng so sánh ngay cạnh (`.hero .big` +
`.vs`); số bảng viết thường, tổng đậm, âm có màu; chú giải ngắn và lùi
sau; bảng luôn cuộn trong thẻ; thẻ chỉ tiêu nhãn-mờ / giá-trị-đậm /
dòng-phụ-mờ.

Không chép: sidebar trái và tabbar đáy (Reports giữ ba tab ngang của
`DEC-185`); bảng màu đơn sắc (Reports cần xanh "đã chốt" / vàng "cần
xem" / đỏ "lỗi" đã có nghĩa trong hệ thống — `R-S7`); đơn vị `k` / `tr`
(Reports giữ "nghìn đồng" + tooltip VND đầy đủ theo R1 §9); JavaScript
render phía client (Reports không có JS, cố ý — `DEC-184`).

## 5. Bằng chứng thực thi (E1)

```text
FULL_SUITE    = 1 failed, 2694 passed, 12 skipped in 111.67s
                (baseline Phase B: 2684 passed, 11 skipped → +12 test mới
                 = 2696 kỳ vọng; 2694 pass + 1 fail môi trường + 1 skip
                 môi trường — xem dưới)
GOLDEN        = 58 passed, 2 skipped (đúng baseline CLAUDE.md)
UI_SUBSET     = 488 passed (11 file test UI/nghiệp vụ hướng đích)
NEW_TESTS     = tests/test_uiux_refinement.py → 12 passed
OVERFLOW_390  = 0 trang (lượt 1: /ban-hang 982px, /san-pham 613px → đã sửa)
VALIDATORS    = xem CHECK-UIUX-07 trong file task
```

Test FAIL duy nhất —
`test_105d_boundaries.py::TestG25GoldenBaselineUnchanged::test_protected_golden_artifacts_match_the_task_105e_review_base`
— fail Y HỆT trên HEAD chưa sửa (kiểm bằng `git worktree add … HEAD`):
`git diff --stat 740f396a…` trả `fatal: bad object` vì clone của môi
trường này là clone nông (`git rev-parse --is-shallow-repository` = true,
50 commit) không mang commit đó. Không do phiên này; không sửa test.

## 6. Ranh giới đã giữ (kiểm lại, không suy diễn)

```text
BUSINESS_LOGIC_CHANGED     = NO   (không file nào dưới app/modules/)
BUSINESS_FORMULA_CHANGED   = NO
DATABASE_CHANGED           = NO   (ALEMBIC_HEAD = 0007_employee_workspace)
NEW_FEATURE_CREATED        = NO
PRIMARY_NAV_CHANGED        = NO   (layout.html không đổi; NAV-01 PASS)
FINANCE_CODE_CHANGED       = NO
EXISTING_TESTS_MODIFIED    = 0
DEC-184 §14                = GIỮ (không <details> trên không gian làm việc
                              — có test canh)
DEC-185                    = GIỮ (một biểu đồ, ba tab, nhận diện tại chỗ)
R-S7 / DEC-PHB02-02        = GIỮ (CHÍNH THỨC / CHƯA HOÀN CHỈNH y nguyên)
R1 §9                      = GIỮ (nghìn đồng + tooltip VND đầy đủ)
```

## 7. Bàn giao

```text
UI_UX_RESULT                 = PASS_WITH_FINDINGS
FINANCE_USED_AS_REFERENCE    = YES
FINANCE_CODE_CHANGED         = NO
PRIMARY_USER_OPTIMIZED_FOR   = COMPANY_OWNER / SENIOR_MANAGER
HIGH_FINDINGS                = [H-01, H-02, H-03, H-04]
MEDIUM_FINDINGS              = [M-01, M-02, M-03, M-04, M-05, M-06, M-07, M-08]
LOW_FINDINGS                 = [L-01 … L-10]
FIXED                        = [H-01…H-04, M-01…M-08, L-01…L-04]
DEFERRED                     = [L-05, L-06 (DEFERRED_REQUIRES_BUSINESS_CHANGE),
                                L-07]; giữ theo quyết định: [L-08, L-09, L-10]
MAJOR_UX_IMPROVEMENTS        = [ô chủ đạo doanh thu + so tháng trước,
                                tên nhóm người đọc được, ba giọng
                                lỗi/cảnh báo/thông báo, bảng kê Nhân viên
                                đọc được theo khối BH, chú giải lùi sau
                                một lần bấm, không tràn ngang ở 390px,
                                một quy ước ngày trên mọi màn hình nghiệp vụ]
BUSINESS_LOGIC_CHANGED       = NO
BUSINESS_FORMULA_CHANGED     = NO
DATABASE_CHANGED             = NO
NEW_FEATURE_CREATED          = NO
PRIMARY_NAV_CHANGED          = NO
REGRESSION_RESULT            = xem mục 5
SCOPE_DRIFT                  = NO
IMPL_HEAD                    = 9d8bda85ce9fa4dfb8b310881758a9a79a0f9e65
FINAL_HEAD                   = commit đóng phiên (docs) ngay sau IMPL_HEAD
SAFE_FOR_REVIEW              = YES
NEXT_RECOMMENDED             = Owner mở Báo cáo / Nhân viên trên production
                                sau khi tích hợp để nghiệm thu bằng mắt;
                                ba mục DEFERRED chờ quyết định sản phẩm.
```
