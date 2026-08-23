# 00 — Điều Phối Phiên Làm Việc (Session Orchestration)

## Mục đích
Xác định cách một dự án được lập kế hoạch và thực thi xuyên suốt nhiều phiên làm việc của AI coding, đồng thời bảo toàn ngữ cảnh chung, ranh giới phạm vi, tiến độ và việc xác minh.

## Mô hình Cốt lõi
Một Major Task = Một Primary Session.

Micro Task có thể được xử lý ngay trong phiên nếu đủ điều kiện.
Spike/Exploratory Task có thể dùng một phiên khám phá (discovery session) riêng.

## Các Chế độ Bắt đầu Dự án

### Dự án Nhỏ / Mới
S000 có thể gộp chung:
- chọn profile,
- mở dự án,
- discovery (khám phá),
- roadmap,
- phân rã task,
- các gate sơ bộ.

### Dự án Lớn / Legacy
Nên ưu tiên:
- S000 — Mở Dự án + Chọn Profile
- S001 — Discovery & Baseline
- S002 — Hoàn thiện Roadmap
- S003+ — Các Session cho Major Task

## S000 — MỞ DỰ ÁN

S000 phải thực thi theo đúng thứ tự sau:

0. Chọn profile dự án theo `governance/core/PROJECT_PROFILE_STANDARD.md`.
1. Ghi/cập nhật `PROJECT/PROJECT_PROFILE.md`.
2. Hiểu mục tiêu dự án và loại dự án.
3. Xác định quy mô dự án và độ sâu governance.
4. Khảo sát đủ ngữ cảnh repository để tạo kế hoạch ban đầu.
5. Quyết định liệu công việc có nên bắt đầu ở chế độ AUDIT hay không.
6. Tạo các phase chính.
7. Tạo các Major Task và xác định các task Micro/Spike đủ điều kiện.
8. Tạo các subtask sơ bộ.
9. Tạo dependency graph sơ bộ.
10. Ước lượng Difficulty, Risk, và Blast Radius.
11. Đề xuất capability tier.
12. Tạo các Completion Gate sơ bộ.
13. Khởi tạo/cập nhật `PROJECT/PROJECT_PROGRESS.md`.
14. Ghi lại các quyết định chiến thuật ban đầu nếu cần.

Đối với công việc legacy/AUDIT:
- dùng `governance/audit/DISCOVERY_BASELINE_TEMPLATE.md`;
- dùng `governance/audit/AUDIT_FINDINGS_TEMPLATE.md`;
- không được sửa production feature code.

S000 không được sửa production feature code trừ khi thực sự cần thiết cho bootstrap/governance.

## Hoàn thiện Roadmap

Trước khi một task tương lai trở thành READY:

1. Kiểm tra lại yêu cầu dựa trên hiểu biết hiện tại về dự án.
2. Xác nhận Task Mode.
3. Xác nhận các dependency.
4. Xác nhận Scope Lock.
5. Hoàn thiện Ready Gate.
6. Hoàn thiện Completion Gate.
7. Gắn các evidence level bắt buộc.
8. Đóng băng (freeze) Completion Gate.
9. Gán capability tier chính và capability tier dự phòng (escalation).

Không đóng băng chi tiết của các task còn xa trước khi việc discovery đã đủ.

## Yêu cầu đối với Major Task

Mỗi Major Task phải định nghĩa:
- Task ID
- Tên
- Task Mode
- Mục tiêu (Objective)
- Phạm vi (Scope)
- Ngoài phạm vi (Out of Scope)
- Dependency
- Blocks
- Các task có thể chạy song song an toàn (Parallel-safe tasks)
- Vùng dự kiến bị tác động (Expected touch area)
- Difficulty
- Risk
- Blast Radius
- Primary Agent Tier
- Escalation Agent Tier
- Subtask
- Ready Gate
- Completion Gate
- Yêu cầu Evidence
- Exit Criteria

## Quy tắc Micro Task

Dùng `governance/templates/MICRO_TASK_CHECKLIST.md`.

Một Micro Task không cần task file riêng hoặc session handoff riêng, trừ khi:
- phạm vi mở rộng,
- rủi ro tăng lên,
- task được nâng cấp (promote) thành MAJOR.

## Quy tắc Spike / Exploratory

Mục tiêu là giảm sự không chắc chắn.

Việc hoàn thành dựa trên:
- giả thuyết đã được kiểm chứng,
- các phương án thay thế đã được so sánh,
- các ràng buộc đã được phát hiện,
- bằng chứng đã được thu thập,
- khuyến nghị đã được ghi lại.

Không ép buộc áp dụng tiêu chí nghiệm thu production quá sớm.

## Giao thức Mở Phiên (Session Open Protocol)

Vào đầu mỗi phiên Major Task:

0. Đồng bộ nhánh: xác định nhánh mặc định thật trên origin (`git remote show
   origin` → "HEAD branch" — không giả định tên nhánh, kể cả "main"),
   `git fetch origin <nhánh mặc định>`, và xác nhận HEAD cục bộ khớp/không
   lỗi thời so với nhánh đó trước khi đọc bất kỳ file nào bên dưới. Nếu đang
   đứng trên một nhánh khác hoặc lỗi thời, đồng bộ trước — không đọc trạng
   thái từ một nhánh cô lập rồi hành động như thể đó là trạng thái chính
   thức. Môi trường Claude Code on the web tự động in cảnh báo này qua
   `.claude/hooks/session-start.sh`; các môi trường khác phải tự kiểm tra
   bằng tay. Xem DEC-118 (`PROJECT/PROJECT_DECISIONS.md`) — sự cố đã xảy ra
   thật: `TASK-000` và `REM-T02` cùng làm một việc trên hai nhánh khác nhau
   vì thiếu bước này.
1. Đọc `CLAUDE.md`.
2. Đọc `PROJECT/PROJECT_PROFILE.md`.
3. Đọc `PROJECT/PROJECT_PROGRESS.md`.
4. Đọc task file hiện tại.
5. Đọc các file governance liên quan.
6. Xác minh các dependency đã DONE.
7. Xác minh Ready Gate đạt (pass).
8. Nạp Scope Lock.
9. Nạp Completion Gate đã đóng băng.
10. Nạp các yêu cầu evidence.
11. Chỉ bắt đầu triển khai sau khi đã xác nhận sẵn sàng.

## Scope Lock

Nếu công việc yêu cầu chạm vào phần ngoài phạm vi đã được phê duyệt:

SCOPE EXPANSION REQUIRED

Không được âm thầm tiếp tục.

Cập nhật phân tích tác động trước khi mở rộng phạm vi.

## Giao thức Đóng Phiên (Session Close Protocol)

Trước khi đóng một phiên Major Task:

1. Chạy các bước xác minh bắt buộc.
2. Thực thi Completion Gate.
3. Ghi lại evidence kèm Evidence Level.
4. Cập nhật trạng thái task.
5. Cập nhật `PROJECT/PROJECT_PROGRESS.md`. Nếu thay đổi động tới roadmap
   sản phẩm (thêm/bớt bước, đổi thứ tự, đổi trạng thái), cập nhật đồng thời
   `PROJECT/LO_TRINH_DE_HIEU.md` — bản dễ hiểu song song, không thuật ngữ
   kỹ thuật, dành cho người ngoài dự án. Không để hai file lệch nhau.
6. Ghi lại các file đã thay đổi.
7. Ghi lại các quyết định mới.
8. Ghi lại các blocker/rủi ro.
9. Viết session handoff.
10. Xác định task được khuyến nghị tiếp theo.

## Quy tắc Thay đổi Roadmap

Dùng:

ROADMAP CHANGE PROPOSAL

Lý do:
...

Task bị ảnh hưởng:
...

Tác động đến dependency:
...

Risk:
...

Đề xuất thay đổi:
...

Không được âm thầm tái cấu trúc roadmap.

## Câu hỏi về Tiến độ

Nếu người dùng hỏi:
- "đến đâu rồi?"
- "tiến độ thế nào?"
- "còn gì?"
- "bước tiếp theo?"
- "show checklist"

agent phải đọc `PROJECT/PROJECT_PROGRESS.md` trước.

## Vô hiệu hóa do Hồi quy (Regression Invalidation)

Nếu một thay đổi sau này làm mất hiệu lực một cam kết (guarantee) của một task đã hoàn thành:
- giữ nguyên trạng thái DONE lịch sử của task đó;
- tạo một regression item;
- liên kết đến gate bị ảnh hưởng;
- chặn release nếu regression vi phạm một yêu cầu release.

## Evidence

Tuân theo `governance/core/EVIDENCE_STANDARD.md`.

Không được bịa đặt command output, test, kết quả HTTP, screenshot, kết quả CI, hoặc phê duyệt.
