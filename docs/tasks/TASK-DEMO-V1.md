# TASK-DEMO-V1 — Báo cáo Excel cho Owner

Status: IMPLEMENTED
Current Task Mode: MAJOR
Risk: 3
Evidence Level: E1

## Mục tiêu và phạm vi đã chốt trước triển khai

Theo yêu cầu Owner ngày 2026-08-31: thực hiện CLI, xuất Excel và Review Queue
trong cùng một phiên. Gọi production composition hiện có, giữ bản ghi giá từng
dòng, xuất đúng ba sheet Summary, Order Lines, Review Queue. Không thay đổi
engine, business rule, Tracking, Firebase, coverage hay nguồn lịch sử.

Dependency: các capability production được Owner xác nhận trong yêu cầu phiên.
Không mở lại các gate lịch sử của TASK-105/110. Đây là lớp trình bày Demo V1,
không tuyên bố hoàn thành toàn bộ phạm vi cũ của TASK-111/112.

Vùng tác động: `app/demo.py`, `app/modules/exporting/`, test và tài liệu Demo.
Difficulty: 2. Blast Radius: 3 (hiển thị nhầm giá/trạng thái có thể khiến Owner
đọc sai kết quả). Agent chính: Codex hiện tại. Escalation: chỉ khi cần thay đổi
engine hoặc authority ngoài yêu cầu; không tự mở rộng phạm vi.

## Ready Gate

- [x] Đã đọc composition, PriceResolutionRecord, pipeline và Review Queue.
- [x] Đã xác minh SHA đầu phiên đúng `1ab5dbdfdd70deff1f0636ec1bb5f734ba6a0592`.
- [x] Worktree bắt đầu detached, nhánh kỳ vọng trỏ cùng SHA; dùng nhánh
  `codex/demo-v1` riêng, không đồng bộ sang SHA khác với yêu cầu Owner.
- [x] Đã báo 15 file runtime chưa theo dõi; không xóa, sửa hay commit chúng.
- [x] Không network/Firebase, không migration, không thêm dependency.

## Completion Gate đã chốt

Tất cả check dưới đây REQUIRED, E1:

1. CLI nhận bốn đường dẫn tường minh, gọi production, không nạp PP YAML.
2. Excel có đúng ba sheet và các trường Owner yêu cầu; tiền chưa resolve để
   trống, giữ nguyên giá/lợi nhuận và lý do từ engine theo từng dòng.
3. Đối chiếu đủ OrderID và từng dòng nguồn; mất dòng/đơn phải báo lỗi rõ ràng,
   không in DEMO_COMPLETE. AUTO và REVIEW_QUEUE được đếm theo đơn duy nhất.
4. Focused tests, regression tests và `git diff --check` đạt.
5. Chạy workbook thật đã có tại máy với capture bất biến tương thích;
   ORDER_ACCOUNTING_RATE = 100%, không bịa dữ liệu để tạo AUTO.
6. Kiểm tra nội dung và hình thức cả ba sheet. Ghi kết quả vào session handoff.

Exit Criteria: các check đạt, chỉ commit source/tests/docs có chủ đích, báo SHA
cuối phiên và đường dẫn XLSX. Không merge, deploy hay mở task dashboard.

## Kết quả kiểm chứng

Sáu check REQUIRED đạt E1; xem `docs/sessions/DEMO-V1-20260831.md`.
13 focused tests đạt; full suite trên checkout sạch: 1305 passed, 11 skipped.
Workbook thật: 254/254 đơn, 351/351 dòng, 1 AUTO, 253 Review Queue.
Không thay engine/authority, không mở lại gate lịch sử, không merge.
