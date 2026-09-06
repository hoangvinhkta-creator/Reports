# TASK-UIUX-001 — Tinh chỉnh UI/UX toàn bộ Reports cho người đọc quản trị

## Metadata
Status:
DONE

Phase:
Reports — sau Phase B (Phase B = DONE, production accepted, `DEC-189`).
Đây là một lượt TINH CHỈNH TRÌNH BÀY, KHÔNG phải một vertical tính năng.

Task Mode:
MAJOR

Primary Agent Tier:
B

Escalation Tier:
C

Difficulty:
2/5

Risk:
2/5

Blast Radius:
3/5

Project Profile:
PRODUCT

## Mục Tiêu (Objective)
Audit toàn bộ giao diện web Reports từ góc nhìn NGƯỜI DÙNG CHÍNH — chủ
doanh nghiệp / quản lý cấp cao, mở Reports vài lần một ngày hoặc một tuần,
dành 10–30 giây đầu để hiểu tình hình — rồi sửa những điểm làm họ hiểu sai
hoặc phải cố gắng không cần thiết. Dùng dự án Finance làm THAM CHIẾU ngôn
ngữ thiết kế (chỉ đọc), chọn lọc và thích nghi, không chép.

Thứ tự ưu tiên UX của chỉ thị: hiểu ngay khi liếc → thông tin quan trọng
nhất đứng trước → điều bất thường dễ nhận ra → chi tiết nằm sau một lần
bấm → ít thao tác → ít thuật ngữ kỹ thuật → nhất quán → giữ cảm giác công
cụ quản trị, không phải bảng dữ liệu kế toán.

## Phạm Vi (Scope)
- Toàn bộ template dưới `app/web/templates/` và file CSS duy nhất
  `app/web/static/css/tinphat-ui.css`.
- Tầng TRÌNH BÀY (`app/web/*_presentation.py`) ở mức nhãn/định dạng chuỗi.
- Đăng ký biến template trong `app/web/server.py` (không đổi route, không
  đổi hợp đồng dữ liệu).
- Nhãn ngắn của trạng thái coverage snapshot (`app/history/coverage.py`,
  thuần nhãn).
- Test trình bày mới `tests/test_uiux_refinement.py`.

## Ngoài Phạm Vi (Out of Scope)
Theo đúng mục 7 của chỉ thị — KHÔNG đụng: business logic, công thức, ngữ
nghĩa doanh thu / lợi nhuận / DS quy đổi / Target, Product Identity, thẩm
quyền thương hiệu, gán nhân viên, ngữ nghĩa Nội thành / Gia dụng, loại
dòng, thẩm quyền Legacy, schema, migration, thẩm quyền ghi, ngữ nghĩa
route, thanh điều hướng chính (`DEC-185` giữ đúng ba mục), mã Finance
(`FINANCE_REPO_MODE = READ_ONLY_REFERENCE`).

## Phụ Thuộc (Dependencies)
- Reports Phase B = DONE (`DEC-189`) — nền tảng đã nghiệm thu production.
- `DEC-184` (không gian làm việc Nhân viên) và `DEC-185` (điều hướng ba
  mục, một biểu đồ, nhận diện tại chỗ) — các ranh giới UX phải GIỮ NGUYÊN.

## Chặn (Blocks)
- Không chặn task nào.

## An Toàn Để Chạy Song Song Với (Parallel-Safe With)
- Mọi task không chạm `app/web/templates/`, `tinphat-ui.css`,
  `*_presentation.py`.

## Phạm Vi Tác Động Dự Kiến (Expected Touch Area)

Allowed:
- `app/web/templates/*.html`
- `app/web/static/css/tinphat-ui.css`
- `app/web/analytics_presentation.py`, `app/web/business_presentation.py`,
  `app/web/workspace_presentation.py` (nhãn, định dạng)
- `app/web/server.py` (đăng ký biến template)
- `app/history/coverage.py` (nhãn ngắn)
- `tests/test_uiux_refinement.py`

Không được đụng vào nếu chưa có Scope Expansion (Do not touch without Scope Expansion):
- `app/modules/**` (engine nghiệp vụ), `app/web/business_metrics`,
  `app/web/business_queries.py`, `app/web/business_service.py`,
  `app/web/business_store.py`, `tools/db/**`, `config/**`, mọi route
  trong `server.py`, `layout.html` (thanh điều hướng), repo Finance.

## Subtask (Subtasks)
- [x] UIUX.1 Dựng harness dữ liệu giả lập thực tế (6 nhân viên, 20 dòng,
      thiếu giá, chưa phân loại, lỗ, chiết khấu, Target, 19 tháng lịch sử)
      và chụp 19 màn hình × 2 khổ (1366 / 390) TRƯỚC khi sửa.
- [x] UIUX.2 Đọc ngôn ngữ thiết kế Finance (`index.html` — token, `.stat`,
      `.hero`, `.tbl`, định dạng số) — chỉ đọc.
- [x] UIUX.3 Phân loại phát hiện HIGH / MEDIUM / LOW theo mẫu của chỉ thị.
- [x] UIUX.4 Sửa các phát hiện giá trị cao / rủi ro thấp.
- [x] UIUX.5 Chụp lại, kiểm tràn ngang, chạy test UI + hồi quy + golden.
- [x] UIUX.6 Ghi task / session / DEC / PROGRESS / LO_TRINH.

## Kết Quả Audit (TRƯỚC khi sửa)

Chụp bằng Playwright (Chromium cài sẵn) trên Flask thật với dữ liệu giả
lập: `/kinh-doanh`, `/kinh-doanh/nhan-vien` (bốn sheet, một BH đang sửa),
`/kinh-doanh/thuong-hieu`, `/kinh-doanh/co-cau`, `/kinh-doanh/target`,
`/kinh-doanh/gia-nhap`, `/du-lieu`, `/giai-thich`, `/du-lieu/chay-bao-cao`,
`/lich-su`, `/tong-quan`, `/ban-hang`, `/san-pham`, `/nhan-vien`,
`/doanh-so-ngay` — mỗi trang ở 1366×900 và 390×844.

### Ngôn ngữ thiết kế Finance — điều đã rút ra (tham chiếu, không chép)
- MỘT con số chủ đạo (`.hero .big`, 34px) kèm dòng so sánh ngay cạnh
  (`.vs`), rồi mới tới hàng thẻ `.stat` (nhãn 12px mờ · giá trị 24px đậm ·
  dòng phụ 12px mờ).
- Bảng: chữ 13px, số căn phải, KHÔNG đậm; chỉ dòng tổng đậm; số âm/mờ có
  lớp riêng; mọi bảng nằm trong `.scroll`.
- Chú giải ngắn, mờ (`.hint`), không đoạn văn dài trước dữ liệu.
- Bo góc 8px, viền 1px, nền giấy nhẹ — Reports đã dùng cùng hệ token.

### HIGH

#### H-01 — Thẻ "Tổng số SP" trên Báo cáo không có nhãn
USER PROBLEM: Ô thứ hai trên trang Báo cáo hiện một con số trần (`13`)
không tên.
WHY IT MATTERS: Người đọc quản trị không biết `13` là gì; nhãn là thứ duy
nhất cho con số nghĩa.
EXPECTED BEHAVIOR: Thẻ hiện "TỔNG SỐ SP" như bảng phía dưới.
UI FIX: Biến `QUALIFYING_QUANTITY_LABEL` chưa từng được đăng ký với Jinja
(Jinja render biến chưa định nghĩa thành rỗng) — đăng ký trong
`server.py`.
RISK: NONE. BUSINESS_LOGIC_IMPACT: NONE.

#### H-02 — Không ô nào trả lời "tháng này ra sao" trước; so tháng trước ở module thứ tư
USER PROBLEM: Bốn thẻ KPI ngang hàng, hai thẻ vàng "CHƯA HOÀN CHỈNH" hút
mắt hơn doanh thu; chênh lệch so tháng trước nằm trong một module riêng
dưới biểu đồ và khối coverage.
WHY IT MATTERS: Câu hỏi đầu tiên (doanh thu + hơn/kém tháng trước) cần
hai lần cuộn mới ghép được.
EXPECTED BEHAVIOR: Một ô chủ đạo: doanh thu to, chênh lệch có dấu và màu
ngay cạnh, nguồn mốc so (`SỐ CŨ`) vẫn hiện khi có.
UI FIX: Macro `kpi_hero` + `mom_inline` (`_business_bits.html`); module
"So với tháng trước" gỡ; mọi `data-metric` (`mom`, `mom-origin`,
`mom-source`, `mom-note`) và mọi nhánh "không so được" giữ nguyên.
RISK: LOW. BUSINESS_LOGIC_IMPACT: NONE.

#### H-03 — Cột "Nhóm" lộ mã enum nội bộ
USER PROBLEM: Bảng Theo nhân viên (Báo cáo) và bảng Target hiện
`STANDARD_SALES`, `NOI_THANH`.
WHY IT MATTERS: Thuật ngữ kỹ thuật trên màn hình quản trị; trang Cơ cấu
đã có test cấm rò rỉ enum (`PHB-07` §22) — hai trang nói hai thứ tiếng.
EXPECTED BEHAVIOR: Tên nhóm người đọc được: "Kênh Nội thành", "Kinh doanh
tiêu chuẩn".
UI FIX: `analytics_presentation.group_label` đọc `employee_groups[].name`
từ chính master `config/employees.yaml` (nguồn duy nhất, không bịa tên);
mã lạ ⟹ trả nguyên mã; mã vẫn đi cùng ô ở `data-group`.
RISK: LOW. BUSINESS_LOGIC_IMPACT: NONE.

#### H-04 — Trang sổ thô kéo cả trang sang ngang ở màn hình hẹp
USER PROBLEM: `/ban-hang` (scrollWidth 982 / viewport 390) và `/san-pham`
(613 / 390) làm thân trang cuộn ngang; header và tab trôi khỏi màn hình.
WHY IT MATTERS: Vi phạm quy tắc 21 §9 (responsive) và checklist audit
"horizontal overflow".
EXPECTED BEHAVIOR: Bảng cuộn TRONG thẻ; thân trang không cuộn ngang.
UI FIX: Bọc bảng bằng `.tp-scroll` sẵn có (`ban_hang`, `san_pham`,
`ban_hang_chi_tiet`, `tong_quan`).
RISK: NONE. BUSINESS_LOGIC_IMPACT: NONE.

### MEDIUM

#### M-01 — Số âm không phân biệt được; mọi số đều in đậm
USER PROBLEM: `-300` / `-15.000` của một nhân viên đang lỗ trông y hệt số
dương; mọi ô số đậm 600 nên dòng TỔNG không nổi.
UI FIX: `td.num` về 400, `row-total` giữ 700, lớp `.neg` (đỏ, dấu trừ vẫn
có mặt — màu chỉ bổ sung, quy tắc 21 §5) trên Báo cáo / Thương hiệu / Cơ
cấu. RISK: NONE. BUSINESS_LOGIC_IMPACT: NONE.

#### M-02 — Cảnh báo dang dở dùng giọng LỖI; khoảng trống thương hiệu đọc như lỗi hệ thống
USER PROBLEM: `INCOMPLETE_NOTE` in đỏ đậm 16px; `BRAND_UNAVAILABLE_NOTE`
(trạng thái ĐÃ BIẾT của nguồn danh tính) cũng đỏ.
UI FIX: Lớp `.warn` (vàng — có việc phải làm) và `.notice` (khung vàng
nhạt — trạng thái đã biết); `.error` (đỏ) chỉ còn cho điều sai/hỏng (đối
soát FAIL, dòng chưa có ngày bán, cảnh báo sổ nạp). Câu chữ không đổi.
RISK: NONE. BUSINESS_LOGIC_IMPACT: NONE.

#### M-03 — Bảng kê Nhân viên: viên pill kéo dài, khách hàng bẻ dòng, thẻ đơn lẻ kéo hết chiều ngang
USER PROBLEM: Ô "N dòng" là `<td class="cnt" colspan=7>` ⟹ một viên pill
xám phủ bảy cột; Tên KH · SĐT · Địa chỉ nối liền một dòng rồi bẻ giữa
chừng; thẻ Lợi nhuận KPI đơn lẻ trong lưới auto-fit kéo ra hết chiều
ngang như một dải cảnh báo.
UI FIX: `td.bh-count` (chữ nhạt), `.bh-customer-meta` (SĐT · địa chỉ
xuống dòng dưới, mờ), `.kpi-grid-one` (tối đa 320px). `DEC-184` §14 giữ
nguyên (không `<details>` trên trang này — có test canh).
RISK: NONE. BUSINESS_LOGIC_IMPACT: NONE.

#### M-04 — Thương hiệu / Cơ cấu: 4–6 đoạn chú giải trước bảng
USER PROBLEM: Trang đọc như tài liệu; kết quả đối soát chìm giữa các
đoạn.
UI FIX: Chú giải cách đọc bảng vào `<details class="how-to-read">` "Cách
đọc bảng này" (phần tử gốc trình duyệt, không script); kết quả đối soát,
mẫu số tỉ trọng, ghi chú đơn vị báo cáo, các dòng "sửa ở đâu" vẫn hiển
thị không cần bấm. Mọi `data-metric` còn trong HTML.
RISK: LOW. BUSINESS_LOGIC_IMPACT: NONE.

#### M-05 — Hai màn hình viết ngày theo hai quy ước
USER PROBLEM: Bảng kê chi tiết viết `2026-09-01`, không gian làm việc
viết `01/09/2026` (`DEC-184` §24).
UI FIX: `business_date` dời về `business_presentation`, dùng cho
`detail_rows` và dòng "Chiết khấu"; `workspace_presentation` import lại.
RISK: LOW. BUSINESS_LOGIC_IMPACT: NONE.

#### M-06 — Cảnh báo "sổ nạp gần nhất không thấy lại dòng" đứng thứ sáu trên trang
UI FIX: Dời khối lên NGAY dưới khối chỉ tiêu (điều bất thường là thứ nhìn
thấy thứ hai). RISK: NONE. BUSINESS_LOGIC_IMPACT: NONE.

#### M-07 — Tab Dữ liệu: cột Coverage hiện `DETECTED_ONLY`
UI FIX: `coverage_short_label` ("Chưa xác nhận đủ" / "Đã xác nhận đủ"),
câu đầy đủ và mã ở tooltip; cùng ba trạng thái với trang snapshot.
RISK: NONE. BUSINESS_LOGIC_IMPACT: NONE.

#### M-08 — Thẻ "Dòng chưa có ngày bán" chiếm một module khi không có gì để nói
UI FIX: Không có dòng thiếu ngày ⟹ một dòng `footnote`; có ⟹ vẫn thẻ
cảnh báo đỏ. `data-metric="undated-lines"` giữ nguyên.
RISK: NONE. BUSINESS_LOGIC_IMPACT: NONE.

### LOW

- L-01 Nhãn cột cuối biểu đồ bị cắt ở 1366px; cột lịch sử gạch chéo đậm hơn
  cột hiện hành. FIXED (cột 50px, gạch nhạt hơn — vẫn phân biệt khi in).
- L-02 Sheet trống hiện bullet "0 dòng chưa có giá nhập". FIXED (chỉ liệt
  kê khi > 0).
- L-03 Tiêu đề module không xuống dòng ở màn hình hẹp. FIXED (`flex-wrap`).
- L-04 Hai câu dẫn dài trước hai đường dẫn Thương hiệu / Cơ cấu. FIXED
  (một hàng `view-links`, chữ trên nút giữ nguyên).
- L-05 Nhãn "Shared Online Beta" ở header là thuật ngữ vận hành (S071).
  DEFERRED — nhãn trạng thái triển khai, quyết định sản phẩm.
- L-06 Ô nhập Target trên `/kinh-doanh/target` hiện VND thô không dấu phân
  cách. DEFERRED_REQUIRES_BUSINESS_CHANGE — đổi định dạng ô nhập chạm hợp
  đồng khứ hồi PHB-05 §7 / `DEC-184` §7.
- L-07 Tab Dữ liệu: timestamp ISO và tag `LEGACY_REFERENCE`. DEFERRED —
  `DEC-166 E` yêu cầu tên origin phân biệt được; đổi nhãn cần quyết định.
- L-08 Nút thao tác dòng chỉ có biểu tượng (✎ ⇥ 🗑), đã có `title` /
  `aria-label`. GIỮ (`DEC-184` §27 một nút sửa); chỉ thêm `min-width`.
- L-09 Thẻ "CHƯA HOÀN CHỈNH" mã hoá ba lần (nền · viền · tag). GIỮ theo
  `R-S7` / `DEC-PHB02-02`.
- L-10 Thẻ "Tiến độ" (chỉ báo lịch) ngang hàng chỉ tiêu tiền. GIỮ theo
  `DEC-184` §16.

## Ready Gate
Dùng `governance/core/TASK_READY_GATE_STANDARD.md`.

- [x] Objective, Scope, Out-of-scope rõ (mục 1–7 của chỉ thị bàn giao).
- [x] Dependency DONE (Phase B, `DEC-189`).
- [x] Touch area xác định; không data / security / routing / migration.
- [x] Difficulty 2 · Risk 2 · Blast Radius 3 đã chấm (3 vì chạm nhiều
      template — lý do MAJOR thay vì MICRO).
- [x] Completion Gate hoàn thiện và đóng băng trước khi sửa (các check
      dưới đây được viết trước khi chạm code; chỉ phần Evidence điền sau).

## Completion Gate
Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và `governance/core/EVIDENCE_STANDARD.md`.

### UI/UX

#### CHECK-UIUX-01 — Audit đầy đủ TRƯỚC khi sửa, có ảnh chụp thật
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Harness `serve_fixture.py` + `shoot.py` (Playwright, Chromium
`/opt/pw-browsers/chromium-1194`) dựng Flask thật với dữ liệu giả lập, chụp
19 trang × 2 khổ. Output lượt 1 (trước sửa) — trích:
`200 ban-hang-mob scrollWidth=982 viewport=390` ·
`200 san-pham-mob scrollWidth=613 viewport=390` · 36 dòng còn lại
`scrollWidth == viewport`. Các phát hiện H-01…L-10 ở trên đọc từ chính
các ảnh đó (thẻ `13` không nhãn, `STANDARD_SALES` trong cột Nhóm, pill
`colspan=7`, ngày ISO ở bảng kê chi tiết).

Executed By:
Phiên S125 (Claude Code, nhánh `claude/reports-ui-ux-refinement-3n5v8l`)

Timestamp:
2026-09-06T05:00:00Z

#### CHECK-UIUX-02 — Bộ test UI/template + hồi quy nghiệp vụ PASS sau khi sửa
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`python3 -m pytest -q tests/` → `1 failed, 2694 passed, 12 skipped in 111.67s (0:01:51)`.
Bộ UI/nghiệp vụ hướng đích (`test_uiux_refinement` · `test_r1_navigation`
· `test_dec185_nav_chart_identity` · `test_employee_workspace_ux` ·
`test_phb05_employee_target` · `test_phb06_brand_reporting` ·
`test_phb07_advanced_analytics` · `test_web_server` ·
`test_phb03_followup_repairs` · `test_business_vertical` ·
`test_dec180_discount_parity`) → `488 passed in 25.51s`.
Một test FAIL duy nhất trong suite đầy đủ —
`test_105d_boundaries.py::TestG25GoldenBaselineUnchanged::test_protected_golden_artifacts_match_the_task_105e_review_base`
— FAIL Y HỆT trên HEAD chưa sửa (kiểm bằng `git worktree add … HEAD` rồi
chạy đúng test đó: `1 failed in 0.14s`); nguyên nhân là môi trường:
`git cat-file -e 740f396acb11cf279f303f09ea22dffd0ca95462` → exit 1,
`git rev-parse --is-shallow-repository` → `true` (clone nông 50 commit
không mang commit mà test diff tới). KHÔNG do task này.

Executed By:
Phiên S125 (Claude Code)

Timestamp:
2026-09-06T05:23:47Z

#### CHECK-UIUX-03 — Golden Baseline không đổi
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`python3 -m pytest -q tests/test_golden_baseline.py` → `58 passed, 2 skipped in 5.63s`
(2 skipped là hai workbook thô `GOLDEN_RAW_01/06` không có trong môi
trường — cùng hình dạng với baseline `58 passed, 2 skipped` đã ghi ở
`CLAUDE.md`).

Executed By:
Phiên S125 (Claude Code)

Timestamp:
2026-09-06T05:23:47Z

#### CHECK-UIUX-04 — Không trang nào tràn ngang ở 390px sau khi sửa
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Lượt chụp 2 (23 trang × 2 khổ, gồm trạng thái trống `ky=2026-08` sheet
Gia dụng, kỳ chỉ có số cũ, trang Chạy báo cáo): 46 ảnh, mọi dòng `200`,
bộ lọc `awk` in `OVERFLOW` khi `scrollWidth > viewport` → không in dòng
nào (`overflow check done`). Ảnh xem lại trực tiếp: Báo cáo (desk/mob),
Nhân viên bốn sheet (desk/mob, có BH đang sửa, sheet trống), Thương hiệu,
Cơ cấu, Target, Bảng kê chi tiết, Dữ liệu.

Executed By:
Phiên S125 (Claude Code)

Timestamp:
2026-09-06T05:23:47Z

#### CHECK-UIUX-05 — Không thay đổi nghiệp vụ / schema / route / điều hướng
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`git diff --name-only` chỉ chạm: `app/history/coverage.py` (thêm nhãn
ngắn), `app/web/analytics_presentation.py`, `app/web/business_presentation.py`,
`app/web/workspace_presentation.py` (nhãn/định dạng), `app/web/server.py`
(đăng ký 3 biến template), `app/web/static/css/tinphat-ui.css`, 10 template,
`tests/test_uiux_refinement.py`. Không file nào dưới `app/modules/`,
`tools/db/`, `config/`; `grep -i "migration|alembic|schema"` trên danh
sách file đổi → `no migration/schema files touched`. Thanh điều hướng:
`test_nav_01_the_primary_nav_is_exactly_bao_cao_nhan_vien_du_lieu` PASS;
`layout.html` không đổi. Số liệu: mọi test nghiệp vụ hiện có PASS không
sửa (xem CHECK-UIUX-02).

Executed By:
Phiên S125 (Claude Code)

Timestamp:
2026-09-06T05:23:47Z

#### CHECK-UIUX-06 — Test mới canh các sửa chữa trình bày
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`python3 -m pytest -q tests/test_uiux_refinement.py` → `12 passed in 1.38s`.
12 test: nhãn thẻ Tổng số SP · cột Nhóm không mã enum (Báo cáo + Target) ·
`group_label` đọc master và không bịa tên · MoM nằm trong ô chủ đạo,
trước biểu đồ, không còn `<h2>So với` · số âm mang `.neg` · footnote
dòng chưa có ngày · mọi `<table>` trong `.tp-scroll` trên 6 trang ·
ô đếm BH không phải pill · khoảng trống thương hiệu là `.notice` và đối
soát đứng ngoài `<details>` · không gian làm việc KHÔNG có `<details>`
(`DEC-184` §14) · bảng kê chi tiết viết `DD/MM/YYYY` · Dữ liệu viết
coverage bằng chữ.

Executed By:
Phiên S125 (Claude Code)

Timestamp:
2026-09-06T05:23:47Z

### Documentation

#### CHECK-UIUX-07 — Validator governance
Priority:
RECOMMENDED

Status:
PASS

Evidence Level:
E1

Evidence:
`validate_structure` → `GOVERNANCE STRUCTURE: PASS` · `validate_project_state`
→ `PROJECT STATE: PASS` · `validate_task_completion` → `TASK COMPLETION:
PASS` (Checked 14 DONE task(s)) · `validate_evidence` → `EVIDENCE
VALIDATION: PASS` (161 REQUIRED PASS evidence record(s)) ·
`validate_reference_integrity` → `FAIL` với ĐÚNG 3 reference hỏng CÓ SẴN
của `docs/tasks/TASK-REM-T06-repository-root-hygiene.md` (`F-05` /
`FIND-PHB06-03` / `FIND-PHB07-03`, đã ghi ở `DEC-189`) — cùng 3 dòng đó
trên HEAD chưa sửa; không reference nào của task này hỏng.

Executed By:
Phiên S125 (Claude Code)

Timestamp:
2026-09-06T05:23:47Z

## Tiêu Chí Hoàn Thành (Exit Criteria)
- [x] 100% REQUIRED checks PASS
- [x] Không có lỗi nghiêm trọng (critical) chưa xử lý
- [x] Đạt mức evidence yêu cầu (Risk 2 → E1 cho mọi check thực thi được)
- [x] Tài liệu bắt buộc đã được cập nhật (task · session · `DEC-190`)
- [x] Tiến độ dự án đã được cập nhật (`PROJECT/PROJECT_PROGRESS.md`,
      `PROJECT/LO_TRINH_DE_HIEU.md`)
- [x] Đã viết Session Handoff (`docs/sessions/S125-reports-ui-ux-refinement.md`)

## Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)
- Bất kỳ sửa chữa nào cần đổi một chuỗi trong tầng nghiệp vụ, một cột DB,
  một route, hay thanh điều hướng ⟹ DỪNG, đánh dấu
  `DEFERRED_REQUIRES_BUSINESS_CHANGE` (đã áp cho L-06).
- Một test nghiệp vụ hiện có đỏ vì thay đổi trình bày ⟹ sửa trình bày,
  KHÔNG sửa test (không xảy ra: 0 test hiện có bị sửa).

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- `tests/test_uiux_refinement.py`
- `docs/tasks/TASK-UIUX-001-reports-ui-ux-refinement.md`
- `docs/sessions/S125-reports-ui-ux-refinement.md`

Modified:
- `app/web/static/css/tinphat-ui.css`
- `app/web/templates/_business_bits.html`, `kinh_doanh.html`,
  `kinh_doanh_nhan_vien.html`, `kinh_doanh_thuong_hieu.html`,
  `kinh_doanh_co_cau.html`, `ban_hang.html`, `ban_hang_chi_tiet.html`,
  `san_pham.html`, `tong_quan.html`, `du_lieu.html`
- `app/web/analytics_presentation.py`, `app/web/business_presentation.py`,
  `app/web/workspace_presentation.py`, `app/web/server.py`
- `app/history/coverage.py`
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/PROJECT_DECISIONS.md` (`DEC-190`),
  `PROJECT/LO_TRINH_DE_HIEU.md`

Deleted:
- Không.

Migration Impact:
- Không. `ALEMBIC_HEAD` giữ `0007_employee_workspace`.

## Ghi Chú (Notes)
- Finance chỉ được ĐỌC (`/home/user/Finance`, không một file nào đổi,
  không commit). Điều được thích nghi: ô chủ đạo + so sánh cạnh số; số
  bảng không đậm, tổng đậm, âm có màu; chú giải lùi sau; bảng luôn cuộn
  trong thẻ. Điều KHÔNG chép: sidebar, tabbar dưới đáy, bảng màu đơn sắc,
  đơn vị `k`/`tr` (Reports giữ "nghìn đồng" và tooltip VND đầy đủ theo
  R1 §9).
- Không JavaScript mới; không thư viện; không token màu mới.
