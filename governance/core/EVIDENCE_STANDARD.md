# Evidence Standard

## Mục đích
Ngăn một AI agent đánh dấu gate là PASS chỉ dựa trên các tuyên bố tường thuật không có căn cứ.

## Evidence Levels

### E0 — Claim
Chỉ là mô tả do agent tự viết.

Ví dụ:
"Permission test passed."

Sử dụng cho:
- ghi chú mang tính thông tin,
- các check rủi ro thấp, không quan trọng.

E0 KHÔNG được chấp nhận là evidence duy nhất cho các required gate có rủi ro cao.

### E1 — Execution Evidence
Output từ một check đã thực sự được thực thi.

Ví dụ:
- output của lệnh test,
- output build/lint/typecheck,
- mã phản hồi HTTP,
- output từ database rule emulator,
- checksum của artifact được tạo ra,
- ảnh chụp màn hình kết quả thực tế,
- kết quả xác minh bằng browser/devtool khi phù hợp.

### E2 — Independent Evidence
Xác minh độc lập với bên đưa ra tuyên bố triển khai.

Ví dụ:
- kết quả CI,
- công cụ quét bảo mật độc lập bên ngoài,
- kiểm tra trên staging,
- review bởi agent thứ hai,
- người review (human reviewer),
- lần chạy test độc lập.

## Evidence tối thiểu theo Risk

### Risk 1–2
Required checks:
- E0 hoặc E1 tùy theo loại check.
- Với functional correctness nên ưu tiên E1 khi có thể thực thi được.

### Risk 3
Required checks:
- E1 bắt buộc cho các xác minh có thể thực thi được.

### Risk 4–5
Required checks:
- E1 bắt buộc.
- Các check liên quan bảo mật/dữ liệu quan trọng NÊN có E2.
- Nếu E2 không khả dụng, phải ghi lại hạn chế này và ngăn việc release lên production ở những nơi mà profile yêu cầu phải có xác minh độc lập.

## Tính toàn vẹn của Evidence

Không được bịa ra:
- output lệnh,
- kết quả test,
- mã trạng thái HTTP,
- ảnh chụp màn hình,
- kết quả CI,
- sự phê duyệt của con người.

Nếu chưa được thực thi:
Status = NOT_TESTED.

## Evidence Record

Check ID:
...

Status:
PASS / FAIL / BLOCKED / NOT_TESTED

Evidence Level:
E0 / E1 / E2

Evidence:
...

Executed By:
...

Timestamp:
...

## Quy trình Review độc lập cho Solo Developer

Đối với một solo developer không có CI/staging/người review khác, E2 có thể được tạo ra bởi một reviewer-agent session riêng biệt.

Reviewer session phải:
1. Bắt đầu từ trạng thái thực tế của repository, không phải từ các tuyên bố của người triển khai (implementer).
2. Đọc frozen task gate.
3. Kiểm tra diff/code thực tế.
4. Chạy lại các required check một cách độc lập khi có thể.
5. Ghi lại evidence của chính mình.
6. Xem các tuyên bố PASS do người triển khai viết là tường thuật không đáng tin cậy.

Reviewer phải nhìn thấy code/diff đang được review; tính độc lập nghĩa là xác minh độc lập, không phải là không biết gì về phần triển khai.

Nếu không có con đường E2 nào đáng tin cậy:
- ghi lại hạn chế này;
- không giả vờ rằng E2 tồn tại;
- tuân theo quy tắc release của project profile.


## Lưu trữ Artifact của E2

Output của independent review phải được lưu trữ lâu dài tại:

`docs/reviews/`

Sử dụng:

`governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`

Không được để kết quả E2 chỉ tồn tại trong lịch sử chat.
