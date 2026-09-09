# S137 — Owner ghi đè hai điều kiện chặn của `S136`, merge R5 thật

Phiên MERGE THẬT (tiếp `S136` trong cùng phiên hội thoại). `S136` đã hoàn tất
mọi kiểm tra kỹ thuật và kết luận `INTEGRATION_READY_WAITING_FOR_OWNER_GATE`
— chặn bởi hai điều kiện: (1) Independent Review vòng 2 chưa có artifact
trong repo, (2) `CHECK-R3-20`/`CHECK-R4-24` (Owner nghiệm thu R3/R4 production)
`NOT_TESTED`. File này ghi lại việc Owner trực tiếp ghi đè cả hai điều kiện
và chỉ thị merge, cùng những gì phiên đã thực hiện sau đó.

---

## 1. Chỉ thị Owner (nguyên văn)

```text
Owner: "tôi đã Independent Review vòng 2 ở codex. hãy bỏ qua và merge luôn
        vào công cụ để tôi sử dụng trực tiếp"
```

Phiên **không** merge ngay — hỏi lại hai điểm chưa rõ trong chỉ thị, vì đây
là quyết định ảnh hưởng production và mâu thuẫn trực tiếp với giới hạn
"không deploy production trong session này, trừ khi tôi gửi chỉ thị deploy
riêng" đã có ở đầu phiên `S136`:

1. "Bỏ qua" có gồm luôn điều kiện `CHECK-R3-20`/`CHECK-R4-24` không (chỉ thị
   gốc chỉ nhắc tới Independent Review, không nhắc R3/R4)?
2. Cả hai repo dùng Render Blueprint — push lên nhánh mặc định thường tự
   động kích hoạt deploy production. Owner có chấp nhận điều đó không?

Owner trả lời:

```text
Owner: "tôi đã tự kiểm R3 R4 xong rồi nên hãy bỏ qua"
Owner: "Merge và chấp nhận Render tự deploy luôn"
```

Quyết định được ghi lại đầy đủ ở **`PROJECT/PROJECT_DECISIONS.md` → `DEC-203`**
trước khi merge — không merge nào chạy trước khi quyết định được ghi thành
văn bản.

---

## 2. Điều gì THAY ĐỔI và điều gì KHÔNG

**Không có bằng chứng thực thi được (E1/E2) nào được thêm vào repo cho
Independent Review vòng 2 hay cho việc đối chiếu R3/R4 trên production.**
Cả hai xác nhận đều bằng lời của Owner. Phiên này **không tự chạy** một vòng
review độc lập nào, **không tự đối chiếu** dữ liệu production nào để giả
làm bằng chứng thay Owner — làm vậy sẽ là bịa bằng chứng, đúng thứ CLAUDE.md
cấm tuyệt đối.

Những gì thực sự đổi:

- `CHECK-R5-27`, `CHECK-R5R1-09`: `FAIL`/`NOT_TESTED` → `ACCEPT_WITH_RECORDED_RISK
  (Owner override, DEC-203)`.
- `CHECK-R3-20`, `CHECK-R4-24`: `NOT_TESTED` → `ACCEPTED_BY_OWNER_VERBAL
  (DEC-203)`.
- `CHECK-R5-28` (Owner nghiệm thu R5 trên production): **KHÔNG đổi**, vẫn
  `NOT_TESTED` — override không bao gồm nghiệm thu R5 (chưa từng lên
  production trước phiên này).
- Ngân sách repair `R5`: **KHÔNG đổi**, giữ `2 allowed / 1 used / 1
  remaining` — override không phải một repair cycle.

Chi tiết đầy đủ, rủi ro, và điều kiện xem lại: `DEC-203`.

---

## 3. Merge

### 3.1 Tracking — PR #26

```text
$ merge_pull_request(owner=hoangvinhkta-creator, repo=tracking, pullNumber=26)
```

(Kết quả merge — SHA thật, xem §4 sau khi thực thi.)

### 3.2 Reports — PR #12

```text
$ merge_pull_request(owner=hoangvinhkta-creator, repo=reports, pullNumber=12,
                     expectedHeadSha=<HEAD của claude/r5-integration-vinh SAU
                     khi đẩy commit cập nhật CHECK-R5-27/28, DEC-203, S137>)
```

(Kết quả merge — SHA thật, xem §4.)

---

## 4. Trạng thái sau merge

(Điền bằng SHA thật ngay sau khi hai lệnh merge ở §3 thực thi — xem commit
theo sau file này trong cùng phiên nếu bảng dưới chưa được cập nhật.)

```text
Tracking merge commit    <điền sau merge>
Tracking default (main)  <tip sau merge>
Reports merge commit     <điền sau merge>
Reports default          <tip sau merge>
```

---

## 5. Deploy — KHÔNG XÁC NHẬN ĐƯỢC từ phiên này

Đúng giới hạn đã ghi nhận xuyên suốt `S127`/`S130`/`S133`: phiên này không có
egress/credential tới Render Dashboard hay domain production. Owner đã xác
nhận chấp nhận Render tự động build+deploy sau merge (Blueprint tự kích
hoạt theo `render.yaml` của mỗi repo khi có commit mới trên nhánh liên kết
đã cấu hình) — nhưng **"sẽ tự chạy" không phải bằng chứng "đã chạy xong và
healthy."** Owner cần tự xác nhận qua Render Dashboard (các bước xem
`S133` §4, cùng khuôn cho Tracking và Reports):

1. Mở Render Dashboard → service tương ứng → tab **Events**, tìm sự kiện
   deploy gắn với commit merge ở §4.
2. Xác nhận **Live** (không phải *Deploy failed*/đang *Building*).
3. Xem **Logs**: với Reports, `alembic upgrade head` chạy xong không lỗi
   TRƯỚC khi `gunicorn` khởi động (Dockerfile fail-closed).
4. Nếu FAIL: đọc log tới nguyên nhân gốc, đưa cho phiên sau — không tự sửa
   bằng cách bỏ qua migration hay khởi động app trước `alembic upgrade head`.

`CHECK-R5-28` (Owner nghiệm thu R5 trên production) vẫn `NOT_TESTED` cho tới
khi Owner tự làm §7 của `S136` (mục 7–8) trên production thật, SAU khi deploy
được xác nhận Live.

---

## 6. Điều kiện mở R5.1

Vẫn CHƯA `READY` — `CHECK-R5-28` cần `PASS`/`ACCEPT_WITH_RECORDED_RISK` từ
một nghiệm thu THẬT trên production trước khi bất kỳ nội dung R5.1 nào được
mở. Việc merge ở phiên này không tự động mở R5.1.
