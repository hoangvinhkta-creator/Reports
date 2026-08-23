# ADR-001 — Gói governance đặt tại thư mục gốc repository

## Status
Accepted

## Date
2026-08-22

## Context

Gói AI Engineering Constitution V3.2 FINAL COMPACT đã được commit vào
repository này dưới dạng một thư mục archive đã giải nén,
`AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/`. Do đó, thư mục gốc
của repository chỉ chứa `.git` và duy nhất thư mục đó, còn `CLAUDE.md` — điểm
vào governance duy nhất — nằm thấp hơn root một cấp.

S001 đã ghi nhận việc này dưới mã FIND-001 (HIGH). Ba đặc điểm của cấu trúc
hiện tại dẫn đến quyết định này:

1. Một agent hoặc con người mở repository sẽ không thấy ngay `CLAUDE.md` và
   không nhận được tín hiệu nào cho biết governance tồn tại. Thứ tự đọc bắt
   buộc trước khi làm việc trong
   `governance/core/00_SESSION_ORCHESTRATION.md` bị bỏ qua một cách âm thầm
   thay vì báo lỗi rõ ràng.
2. Chính hướng dẫn của gói,
   `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 1, đánh dấu
   chính xác cấu trúc lồng nhau này dưới tiêu đề "Không nên", với lý do nêu rõ
   rằng framework phải nằm cùng cấp với code của dự án để một agent xem nó là
   governance của repository đó.
3. Mọi validator đều xác định root của nó từ
   `Path(__file__).resolve().parents[3]`, chính là thư mục của gói. Do đó
   chúng validate gói chứ không phải repository, và `validate_structure.py`
   trả về PASS trên cây thư mục bị triển khai sai (FIND-007, evidence
   CHK-S001-05). Lỗi này vô hình đối với chính công cụ được thiết kế để phát
   hiện nó.

Cần một quyết định ngay bây giờ thay vì để sau, vì mọi task khắc phục tiếp
theo đều sửa các file có đường dẫn mà quyết định này sẽ thay đổi.

## Decision

Bốn thành phần của gói — `CLAUDE.md`, `PROJECT/`, `docs/`, `governance/` —
được chuyển lên thư mục gốc repository, và thư mục bọc ngoài bị loại bỏ.

Việc di chuyển được thực hiện dưới dạng REM-T02 và **chỉ thay đổi đường dẫn**:
dùng `git mv` mà không thay đổi nội dung, theo quy tắc bảo toàn nội dung
(content-preservation) trong `governance/README.md`. Việc sửa các tham chiếu
canonical bị hỏng mà bước di chuyển này không khắc phục là một task riêng
(REM-T04), để diff của bước di chuyển có thể được xác minh chỉ gồm các thao
tác rename.

## Alternatives Considered

**A — Giữ nguyên cấu trúc lồng nhau và ghi lại tài liệu về nó.**
Bị từ chối. Nó mâu thuẫn với chính hướng dẫn cài đặt của gói, và không có
lượng tài liệu nào khiến một agent đọc được một `CLAUDE.md` mà nó không bao
giờ thấy. Nó cũng sẽ buộc mọi bên sử dụng repository này trong tương lai phải
học một ngoại lệ cục bộ.

**B — Giữ nguyên cấu trúc lồng nhau và sửa các validator để chấp nhận nó.**
Bị từ chối. Điều này đảo ngược vấn đề: nó sẽ khiến công cụ xác nhận một cấu
trúc mà chính framework định nghĩa là sai, làm sâu thêm FIND-007 thay vì
đóng nó lại.

**C — Di chuyển các file và sửa tham chiếu trong cùng một task.**
Bị từ chối. Nó sẽ khiến diff của REM-T02 là hỗn hợp giữa rename và chỉnh sửa
nội dung, khiến `git diff -M` không còn có thể chứng minh rằng không có ngữ
nghĩa governance nào bị thay đổi. Với một thay đổi có Blast Radius 5/5 ảnh
hưởng đến đường đọc của agent, đó là cơ chế an toàn chính. Tách các task ra
tốn thêm một phiên làm việc nhưng đổi lại một diff có thể xác minh được.

**D — Tái cấu trúc thành thư mục ẩn `.governance/` hoặc tương tự.**
Bị từ chối. Đây là một cấu trúc mới lạ mà framework không định nghĩa, và nó
sẽ khiến repository này khác biệt so với mọi bên sử dụng khác của cùng gói.

## Rationale

Phương án C là phương án gần nhất và lý do từ chối nó đáng được nêu rõ: giá
trị của bước di chuyển này không chỉ nằm ở trạng thái cuối cùng mà còn ở khả
năng chứng minh không có gì khác bị thay đổi trong quá trình đạt đến đó. Một
diff rename thuần túy có thể được xác minh một cách máy móc; một diff hỗn hợp
đòi hỏi con người phải đánh giá thủ công trên 73 file.

Việc khớp với cấu trúc đã được tài liệu hóa của framework cũng có nghĩa là
các bản nâng cấp gói trong tương lai sẽ áp dụng suôn sẻ, và cách xác định root
`parents[3]` hiện tại vẫn đúng — độ sâu của các script so với root của gói
không đổi qua bước di chuyển này.

## Consequences

### Positive
- `CLAUDE.md` trở thành thứ đầu tiên nhìn thấy tại thư mục gốc repository.
- Cấu trúc khớp với bản cài đặt đã được tài liệu hóa của framework, nên các
  bản nâng cấp gói và bất kỳ code ứng dụng nào trong tương lai đều nằm đúng
  vị trí mà hướng dẫn mong đợi.
- Các validator bắt đầu validate repository thay vì một thư mục con.
- Đóng FIND-001 và loại bỏ điều kiện tiên quyết đứng sau RSK-001.

### Negative / Tradeoffs
- Toàn bộ 73 đường dẫn file được theo dõi thay đổi cùng lúc. Bất kỳ bookmark
  hoặc liên kết bên ngoài nào trỏ vào đường dẫn cũ đều bị hỏng. Không có gì
  bên trong repository bị hỏng, vì các đường dẫn tương đối so với `CLAUDE.md`
  không đổi.
- Bước di chuyển này phải được sắp xếp trước REM-T03, REM-T04, REM-T05 và
  REM-T06, điều này làm tuần tự hóa công việc mà lẽ ra có thể tiến hành song
  song.
- `git log` không có `--follow` sẽ cho thấy một đoạn gián đoạn tại commit di
  chuyển.

## Migration / Implementation Notes

Được thực hiện dưới dạng REM-T02. Xem
`docs/tasks/TASK-REM-T02-root-promotion.md` để biết Completion Gate đã được
frozen. Các check mang tính chịu tải (load-bearing):

- CHECK-T02-03 — `git diff --stat HEAD~1 -M` phải chỉ cho thấy rename, với
  không dòng nội dung nào được thêm hoặc xóa.
- CHECK-T02-04 — `git log --follow` phải trả về lịch sử trước khi di chuyển
  cho ít nhất ba file được lấy mẫu, bao gồm `CLAUDE.md`.
- CHECK-T02-05 — xác nhận độc lập (E2) rằng không có chỉnh sửa ngữ nghĩa nào
  xảy ra.

Điều kiện tiên quyết: một backup ref đã được push, và xác nhận rõ ràng của
chủ sở hữu do Blast Radius.

REM-T07 (CI) được sắp xếp trước task này để CHECK-T02-05 có một nguồn E2, và
workflow của nó phải phát hiện các validator tại runtime thay vì hard-code
đường dẫn — nếu không, bước di chuyển này sẽ làm hỏng CI và buộc phải chỉnh
sửa nội dung mà CHECK-T02-03 cấm.

## Supersedes
None

## Superseded By
None
