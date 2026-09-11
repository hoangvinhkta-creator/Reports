# R7 — Làm mới liên hệ dòng SAME · Biểu đồ theo container lịch + dự phóng · Số đơn lấp lỗ hổng

## Metadata

Status:
DONE

Current Status Reason:
Ba việc Owner giao trong một phiên (2026-09-11), kèm ba file sổ thô và ảnh
chụp tab Nhân viên. §A và §C/§D là code; §B (giá nhập từ MIN) là kết luận
điều tra, không sửa code Reports. `CHECK-R7-01` … `CHECK-R7-12` PASS (E1).
Merge theo chỉ thị Owner (`DEC-222`). `CHECK-R7-13` (nghiệm thu production)
chỉ Owner đóng.

Phase:
PHASE-01 — Engine tính toán

Task Mode:
MAJOR

Primary Agent Tier:
Claude Code (S153)

Escalation Tier:
Owner

Difficulty:
3/5

Risk:
2/5

Blast Radius:
2/5 (`V4.1` §4 — chấm theo FAILURE PATH, cho từng phần):

```text
§A  sổ nạp → reconcile SAME → UPDATE 3 cột liên hệ của version hiện hành
    → ô Khách hàng/Liên hệ tab Nhân viên. Không fingerprint, không tiền,
    không quyết định Owner nào đọc ba cột này (CHECK-R7-02/03).
§C  paired_series (chọn & xếp điểm ĐÃ tính) → hai đường + dòng dự phóng.
    Không một phép cộng doanh thu/số đơn nào được viết lại; dự phóng là
    trình bày, không đi vào KPI/bảng kê/chốt kỳ (CHECK-R7-05..08).
§D  daily_orders.jsonl → count_series → biểu đồ Số đơn. Chỉ ngày + số
    đếm; không chạm tổng số đơn của kỳ ở ô chỉ tiêu (CHECK-R7-09..11).
```

Project Profile:
PRODUCT

## 1. Yêu cầu của Owner và kết luận điều tra

### §A — Khách hàng/SĐT hiện `—` dù sổ có

Đối chiếu trực tiếp trên sổ tháng 9 Owner gửi: BH73884, BH73914, BH73700,
BH73922, BH73923 đều CÓ tên KH và SĐT (0 dòng trống tên trong 609 dòng).
Reports vẫn hiện `—` ⟹ lỗi phía Reports. Cơ chế: ba trường liên hệ không
thuộc `FINGERPRINT_FIELDS`; dòng đã có version từ lần nạp trước được
reconcile `SAME` và giữ nguyên version cũ mãi — kể cả khi version ấy ghi lúc
liên hệ còn trống. Sửa: `SnapshotRepository._refresh_contact_fields` — làm
mới tại chỗ ba cột liên hệ của version hiện hành cho dòng `SAME` khi sổ nạp
mang giá trị khác và không trống. Không version mới, không đổi fingerprint.

### §B — Giá nhập "các mã cũ" không đọc được từ MIN (KHÔNG sửa code)

Nguyên nhân là DỮ LIỆU, không phải phép tra mã: hợp đồng `daily-min-v1`
chỉ trả giá cho ngày `d` khi Tracking CÓ BẢN NGÀY của `d` (`min_ngay_ngay/
<d>` ở PROVISIONAL/FINAL). Tracking bắt đầu chụp MIN ngày từ R1
(2026-09-07, `src/min-ngay.js`, cron `*/20`). Mọi ngày bán TRƯỚC đó
⟹ `SOURCE_UNAVAILABLE` ⟹ `TRACKING_DAILY_MIN_SOURCE_UNAVAILABLE` ⟹ `—`.
Khớp ảnh chụp: 01–05/09 toàn `—`, 07/08/10-09 có giá. R1 cố ý KHÔNG có nhánh
dự phòng (không rơi về `tp/ton`, không lấy giá ngày khác — `composition.py`
`_tracking_branch`). Hai ngày 06/09 và 09/09 `—` cần đọc nhật ký cron bên
Tracking. Lựa chọn thuộc Owner (ghi ở `DEC-222` §4): (1) chấp nhận — nhập
tay giá cho đơn trước 07/09; (2) Tracking backfill bản ngày cho các ngày
trước 07/09 nếu có dữ liệu Engine lịch sử; (3) mở lại nhánh dự phòng `tp/
ton` cho ngày không có bản ngày — đổi thẩm quyền giá, cần quyết định riêng.

### §C — Biểu đồ: container lịch + "đến hiện tại" + dự phóng

`container_slots`: Ngày = 01 → cuối tháng chứa mốc neo; Tuần = mọi tuần ISO
chạm quý; Tháng = 12 tháng; Quý = 4 quý; Năm = 5 năm. So sánh = container ấy
của NĂM TRƯỚC (giữ `DEC-211`). Đường hiện tại DỪNG ở mốc neo; đường so sánh
chạy trọn container. Container lệch một mốc (tháng 2 nhuận, quý 13/14 tuần)
⟹ đệm mốc trống, không mang số. `project()`: dự phóng = đã có tới mốc neo ÷
phần lịch đã trôi (đo bằng NGÀY ở mọi mức); % so với trọn cùng kỳ năm trước
và % "đến cùng thời điểm". Hiện thành một dòng dưới legend ở CẢ hai biểu đồ,
cả trang Báo cáo lẫn trang Phân tích (`_r6_bits.paired_chart`).

### §D — Số đơn lấp lỗ hổng

`tools/chart_gapfill/extract_daily_orders.py` → `data/chart_gapfill/
daily_orders.jsonl` (579 ngày, 2025-01-01 → 2026-08-31, 29.883 đơn) từ hai sổ
2025 và 2026 (01–08). Sổ tháng 9 KHÔNG đưa vào (đang nạp). `revenue_timeline.
count_series` gộp sổ nạp + nguồn lấp theo NGÀY, ở mọi mức. Chi tiết:
`data/chart_gapfill/PROVENANCE.md` → "Nguồn số đơn".

## 2. Scope Lock

TRONG phạm vi:

```text
app/history/models.py                 CurrentState +contact_values
app/web/history_store.py              _load_current +3 cột; +_refresh_contact_fields;
                                      SnapshotWriteResult +contact_refreshed
app/web/revenue_timeline.py           container_bounds/container_slots; paired_series
                                      theo container + cutoff mốc neo + đệm; Projection/
                                      project(); count_series(); _day_points(value_field)
app/web/chart_gapfill.py              nguồn số đơn (load/daily_order_rows)
app/web/business_presentation.py      _projection_view; x_ticks bỏ mốc đệm; count chart
                                      gapfill_note
app/web/server.py                     hai biểu đồ Số đơn dùng count_series
app/web/templates/kinh_doanh.html     dòng dự phóng
app/web/templates/_r6_bits.html       dòng dự phóng
app/web/static/css/tinphat-ui.css     .chart-projection
tools/chart_gapfill/extract_daily_orders.py   MỚI
data/chart_gapfill/daily_orders.jsonl         MỚI
data/chart_gapfill/PROVENANCE.md      +mục số đơn
tests/**                              3 file mới; cập nhật test cửa sổ cũ
docs/**, PROJECT/**                   governance
```

NGOÀI phạm vi:

```text
Tracking (mọi thứ)                    READ-ONLY — kể cả backfill bản ngày MIN (§B)
thẩm quyền giá / composition          FORBIDDEN — §B chỉ kết luận, Owner quyết
công thức doanh thu / số đơn của kỳ   FORBIDDEN — dự phóng không đi vào KPI
fingerprint / reconcile / version     FORBIDDEN — chỉ 3 cột liên hệ, tại chỗ
```

## Completion Gate

Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và `governance/core/EVIDENCE_STANDARD.md`.

### Functional — §A

#### CHECK-R7-01
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Dòng SAME + sổ mới có liên hệ ⟹ màn hình theo sổ mới; `contact_refreshed=1`,
`n_same=1`, KHÔNG version mới, tiền không đổi —
`test_a_same_line_takes_the_contact_the_new_book_carries`.

Executed By:
Claude Code (S153)

Timestamp:
2026-09-11

#### CHECK-R7-02
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Sổ mới để trống KHÔNG xoá liên hệ đã có; liên hệ giống hệt ⟹ 0 lần ghi;
đường SOURCE_CHANGED không đi qua làm mới —
`test_an_empty_contact_in_a_later_book_never_erases_what_is_known`,
`test_an_identical_contact_writes_nothing`,
`test_a_changed_line_still_gets_a_new_version_with_its_own_contact`.

Executed By:
Claude Code (S153)

Timestamp:
2026-09-11

#### CHECK-R7-03
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Canh tĩnh AST: `update(order_line_source_version)` CHỈ trong
`_refresh_contact_fields`, CHỈ ba cột liên hệ; không `delete` —
`test_only_the_contact_refresh_updates_a_source_version`,
`test_the_write_path_contains_no_delete_and_updates_only_the_pointer_table`.

Executed By:
Claude Code (S153)

Timestamp:
2026-09-11

### Functional — §C

#### CHECK-R7-04
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Container đúng ở 5 mức (30/14/12/4/5 mốc với neo 30/09/2026); Ngày 01 →
cuối tháng, tháng 2 28/29; so sánh = container năm trước —
`test_every_granularity_draws_two_windows_on_the_calendar_container`,
`test_the_day_window_runs_from_the_first_to_the_last_day_of_the_month`,
`test_the_comparison_window_is_the_same_container_one_year_earlier`.

Executed By:
Claude Code (S153)

Timestamp:
2026-09-11

#### CHECK-R7-05
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Đường hiện tại dừng ở mốc neo, đường so sánh trọn container; mốc đệm không
mang số/khoá —
`test_the_current_line_stops_at_the_anchor_and_the_comparison_runs_the_whole_container`,
`test_a_leap_february_pads_the_shorter_window_with_a_blank_slot`,
`test_a_custom_range_anchors_the_window_on_its_own_end_date` (R6, HTTP thật).

Executed By:
Claude Code (S153)

Timestamp:
2026-09-11

#### CHECK-R7-06
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Dự phóng = đã có ÷ phần lịch đã trôi, đo bằng ngày ở mọi mức; % trọn kỳ và
% đến cùng thời điểm; Năm chỉ so năm trước; không % khi năm trước không có
số; bỏ qua số sau mốc neo —
`test_the_day_projection_divides_by_the_elapsed_share_of_the_month`,
`test_the_week_projection_measures_days_inside_the_quarter`,
`test_the_year_level_projects_this_year_against_last_year_only`,
`test_a_missing_last_year_gives_no_percent_but_still_a_projection`,
`test_projection_ignores_data_after_the_anchor_and_pad_slots`.

Executed By:
Claude Code (S153)

Timestamp:
2026-09-11

#### CHECK-R7-07
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Dòng dự phóng hiện trên CẢ hai biểu đồ trang Báo cáo, đúng số (48.000.000
sau 5/30 ngày; 6 đơn), % xuất hiện khi năm trước có số (200 %) —
`test_both_charts_on_the_report_page_show_the_projection_line`,
`test_the_percent_appears_when_last_year_has_a_number`.

Executed By:
Claude Code (S153)

Timestamp:
2026-09-11

#### CHECK-R7-08
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Một engine doanh thu, không bịa số 0, KPI phía trên không đổi theo cửa sổ,
R5/R6 cùng số ở cửa sổ so sánh — toàn bộ `tests/test_r5_two_window_chart.py`
và `tests/test_r6_repair1_chart_windows.py` (HTTP thật) xanh trên container mới.

Executed By:
Claude Code (S153)

Timestamp:
2026-09-11

### Functional — §D

#### CHECK-R7-09
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`count_series`: ngày sổ nạp thắng (2 đơn, không phải 7 của nguồn lấp); ngày
sổ nạp im lặng nhận nguồn lấp; mức Tháng gộp theo ngày và tự khai MIXED —
`test_count_series_fills_only_the_days_the_book_is_silent_about`,
`test_count_series_reaches_month_level_and_says_it_is_mixed`.

Executed By:
Claude Code (S153)

Timestamp:
2026-09-11

#### CHECK-R7-10
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
File đã commit chỉ có ngày + số đếm nguyên không âm; file hỏng NỔ —
`test_the_committed_orders_source_is_dates_and_counts_only`. Biểu đồ Số đơn
trên trang thật vẽ đường năm trước từ nguồn lấp, tự khai nguồn, ngày sổ nạp
không bị lấp — `test_the_orders_chart_reads_its_own_gapfill_source`.

Executed By:
Claude Code (S153)

Timestamp:
2026-09-11

#### CHECK-R7-11
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Nguồn lấp bị cắt khỏi mọi workspace test tổng hợp (`conftest`), nên các bài
đếm đơn chính xác (`test_chart_12_order_counts_equal_the_real_number_of_orders_per_day`,
`test_every_granularity_charts_the_real_order_count`) vẫn xanh nguyên.

Executed By:
Claude Code (S153)

Timestamp:
2026-09-11

### Regression

#### CHECK-R7-12
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Full `pytest` (trừ hai suite trình duyệt): 3658 passed / 23 skipped / 0 failed (nền S152: 3640 / 23 / 0; +18 bài mới, không bài nào bị xoá). Validators
governance PASS; reference_integrity đúng 4 baseline cũ; `git diff --check`
sạch. Nguyên văn: `docs/sessions/S153-r7-lien-he-bieu-do-so-don.md` §5.

Executed By:
Claude Code (S153)

Timestamp:
2026-09-11

#### CHECK-R7-13
Priority:
RECOMMENDED

Status:
NOT_TESTED

Evidence Level:
E0

Evidence:
Owner nghiệm thu production: (a) 5 đơn đầu tháng 9 hiện tên KH/SĐT sau lần
nạp sổ kế tiếp; (b) biểu đồ Ngày chạy 01 → 30/09 với dòng dự phóng; (c) biểu
đồ Số đơn có đường năm trước. Chỉ Owner đóng được.

Executed By:
—

Timestamp:
—

## Tiêu Chí Hoàn Thành (Exit Criteria)
- [x] 100% REQUIRED checks PASS
- [x] Không có lỗi nghiêm trọng (critical) chưa xử lý
- [x] Đạt mức evidence yêu cầu (Risk 2/5 → E1 cho REQUIRED)
- [x] Tài liệu bắt buộc đã được cập nhật
- [x] Tiến độ dự án đã được cập nhật
- [x] Đã viết Session Handoff

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- `tools/chart_gapfill/__init__.py`, `tools/chart_gapfill/extract_daily_orders.py`
- `data/chart_gapfill/daily_orders.jsonl`
- `tests/test_r7_lam_moi_lien_he_dong_same.py`
- `tests/test_r7_bieu_do_container_du_phong.py`
- `docs/tasks/R7-lien-he-bieu-do-container-so-don.md`
- `docs/sessions/S153-r7-lien-he-bieu-do-so-don.md`

Modified:
- `app/history/models.py`, `app/web/history_store.py`
- `app/web/revenue_timeline.py`, `app/web/chart_gapfill.py`,
  `app/web/business_presentation.py`, `app/web/server.py`
- `app/web/templates/kinh_doanh.html`, `app/web/templates/_r6_bits.html`,
  `app/web/static/css/tinphat-ui.css`
- `data/chart_gapfill/PROVENANCE.md`
- `tests/conftest.py`, `tests/test_snapshot_repository.py`,
  `tests/test_r5_two_window_chart.py`, `tests/test_r6_repair1_chart_windows.py`,
  `tests/test_dec216_chart_gapfill.py`,
  `tests/test_identity_durability_and_timeline_aggregation.py`
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/PROJECT_DECISIONS.md`,
  `PROJECT/REVIEW_BUDGET_LEDGER.md`

Deleted:
- không

Migration Impact:
- không (không cột/bảng mới; §A UPDATE ba cột đã có)
