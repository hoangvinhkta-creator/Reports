# S110 — TASK-PRA-005 Production Acceptance (CHECK-PRA005-15) — Attempt / Owner Runbook

Mode: PRODUCTION ACCEPTANCE / OWNER-OPERATED REAL SYSTEM.
Docs-only · 0 dòng production code · không migration · không sửa Tracking ·
không đổi Render/PostgreSQL/R2/Cloudflare · không mở PRA-006.

## 1. Authority — canonical KHÔNG moved

```text
CANONICAL_BRANCH      = claude/extract-upload-repo-gq2ws4 (HEAD branch thật
                        của origin, xác minh bằng `git remote show origin`)
REQUIRED_SHA           = 1a011ee66f9e2b2ffee4d04f6864bfb0eeb45948
REMOTE_CANONICAL_SHA   = 1a011ee66f9e2b2ffee4d04f6864bfb0eeb45948 → KHỚP CHÍNH XÁC
CANONICAL_MOVED        = KHÔNG
SESSION_BRANCH         = claude/pra-005-production-acceptance-auv2vl (docs-only,
                        0 ahead / 0 behind canonical lúc mở phiên)
TRACKING               = READ-ONLY (không gọi, không sửa)
```

`1a011ee` là chính commit S109 (Independent Review E2 record) — commit này
đã là con TRỰC TIẾP của `18ab5d3` (S108 implementation) và ĐÃ nằm trên
canonical (không cần một bước "Controlled Integration" tách biệt: nhánh
review S109 chính là nhánh được fast-forward). `PRA-005` implementation +
review record ĐÃ tích hợp canonical. Điều còn thiếu DUY NHẤT là
`CHECK-PRA005-15` (Owner Production Acceptance).

## 2. Deploy — KHÔNG thực hiện được từ session (bằng chứng, không suy đoán)

Đúng tiền lệ đã ghi nhận ở `docs/sessions/S093-pra-002-production-acceptance.md`
mục 2: network policy của environment chặn cả hai host cần thiết.

```text
curl https://reports.tinphatcrm.com/    → curl (56) CONNECT tunnel failed, response 403
curl https://api.render.com/v1/services → curl (56) CONNECT tunnel failed, response 403

$HTTPS_PROXY/__agentproxy/status → recentRelayFailures:
  { kind: "connect_rejected",
    detail: "gateway answered 403 to CONNECT (policy denial or upstream failure)",
    host: "reports.tinphatcrm.com:443" }
  { kind: "connect_rejected",
    detail: "gateway answered 403 to CONNECT (policy denial or upstream failure)",
    host: "api.render.com:443" }
```

Đây là **policy denial cố định**, không phải lỗi mạng tạm thời — giống hệt
kết quả đo được ở S093 cho một host khác (candidate SHA khác), cùng cơ chế
chặn. Không có đường vòng hợp lệ; KHÔNG tự chế access, KHÔNG tắt TLS
verification, KHÔNG tạo service/queue/worker mới, KHÔNG dùng bất kỳ token
Render/Cloudflare nào (session không có, và cũng sẽ không dùng nếu có, theo
đúng phân quyền Owner-operated real system).

`render.yaml` (dòng đầu file) ghi rõ tiền đề tương tự: *"Áp dụng blueprint
này (Owner thực hiện — cần tài khoản Render + phương thức thanh toán ...)"* —
deploy production luôn là hành động Owner, không phải hành động session,
độc lập với egress.

## 3. CHECK-PRA005-15 — nguyên văn Completion Gate yêu cầu Owner

`docs/tasks/TASK-PRA-005-san-pham.md` → CHECK-PRA005-15, Yêu cầu (nguyên
văn, đã frozen tại S107):

> Bảy bước mục 27 (A–G tối thiểu; H–L khi áp dụng) thực hiện trực tiếp trên
> `reports.tinphatcrm.com` bởi Owner, KHÔNG phải ảnh chụp/fixture.

Đây KHÔNG phải một giới hạn kỹ thuật tạm thời của session này — đây là
Completion Gate đã FROZEN, chỉ định rõ tác nhân là Owner. Kết hợp với mục 2
(session không có egress dưới bất kỳ hình thức nào), kết luận: **session
này không có thẩm quyền lẫn khả năng kỹ thuật để tự đóng CHECK-PRA005-15.**

## 4. Kết luận gate — GIAI ĐOẠN 1 (trước khi có bằng chứng Owner)

```text
PRODUCTION_ACCEPTANCE_EXECUTED = NO (giai đoạn 1)
STOP_REASON                    = NO_PRODUCTION_EGRESS + GATE_REQUIRES_OWNER_ACTION
CHECK-PRA005-15                = NOT_TESTED (không đổi)
TASK-PRA-005                   = CHƯA DONE (không đổi)
```

Không phân loại `PRODUCTION_DEPLOY_FAILURE` — chưa có lần deploy nào được
thực hiện để mà thất bại. Không phân loại `DATA_INTEGRITY_RISK` — chưa có số
production để đối chiếu. Không mở repair cycle — đây không phải một finding
về đúng/sai của candidate, mà là giới hạn về ai/ở đâu có thể thực thi bước
nghiệm thu.

## 5. Runbook Owner — ánh xạ 1-1 vào mục 27 (A–L) của Contract

Owner làm đúng ngần này, không hơn: **không đổi plan, không đổi region,
không tạo service/database/bucket mới, không sửa Cloudflare, không sửa biến
môi trường, không upload dữ liệu giả để "cho đủ" một tiêu chí.**

### Bước 0 — Deploy đúng candidate

Render Dashboard → service Reports (`reports-web`, Virginia) → **Manual
Deploy** → chọn commit `1a011ee66f9e2b2ffee4d04f6864bfb0eeb45948` (nhánh
`claude/extract-upload-repo-gq2ws4`) → Deploy.

Ghi lại: **Deploy ID**, **thời điểm**, và **commit SHA mà Render hiển thị**
(bằng chứng SHA deploy — không suy ra từ việc canonical trỏ ở đó).

### Bước 1 — Mở `/san-pham`

Qua `https://reports.tinphatcrm.com/san-pham` (đường Cloudflare Access bình
thường, không bypass). Ghi lại:

- HTTP 200, trang render được.
- Đúng năm cột bảng: `Mặt hàng · Số lượng · Số đơn · Doanh thu · LN KPI`.
- Đúng bốn ô tóm tắt: Số mặt hàng trên chứng từ · Tổng số lượng ·
  Doanh thu (NET) · LN KPI + coverage.
- Câu disclosure bắt buộc xuất hiện nguyên văn: *"Mặt hàng được gộp theo tên
  ghi trên chứng từ. Các tên khác nhau của cùng một sản phẩm có thể được
  hiển thị thành các dòng riêng."*
- KHÔNG có cột/ô: Giá mua tham chiếu, PP trung bình/mới nhất/hiện hành, LN
  kế toán.

### Bước 2 — Đối chiếu A/B (doanh thu, số lượng) với `/tong-quan`

Mở `/tong-quan` với **CÙNG kỳ/lọc** đang xem ở `/san-pham` (Owner ghi lại kỳ
cụ thể, ví dụ "Tháng 09/2026" hoặc khoảng ngày tuỳ UI hiển thị). Ghi lại từ
cả hai trang:

```
/san-pham  → Tổng số lượng = ?      Doanh thu (NET) = ?
/tong-quan → Tổng số lượng = ?      Doanh thu (NET) = ?
```

PASS nếu hai cặp số bằng nhau tuyệt đối (không sai số làm tròn).

### Bước 3 — Đối chiếu C/D (tổng nhóm = tổng kỳ)

Trang `/san-pham` tự cộng dồn 226+ dòng mặt hàng ra đúng bốn ô tóm tắt phía
trên nó (kiến trúc `product_summary()` tái dụng `period_totals()` — xem
Independent Review E2 mục 5/11), nên Bước 2 ĐÃ chứng minh C/D nếu A/B PASS:
tổng đã lọc = tổng qua bốn ô tóm tắt = tổng nếu cộng tay từng dòng bảng
(cùng nguồn số). Owner KHÔNG cần cộng tay 226+ dòng; chỉ cần xác nhận số
dòng bảng khớp ô "Số mặt hàng trên chứng từ" ở đầu trang.

### Bước 4 — Đối chiếu E/F (LN KPI + coverage)

So `LN KPI` hiển thị trên `/san-pham` (tổng) với `LN KPI` trên `/tong-quan`
cùng kỳ — phải bằng nhau. Ghi lại tử số/mẫu số coverage hiển thị (`N / M
dòng`) ở CẢ hai trang nếu `/tong-quan` cũng hiện coverage; nếu không, ghi
coverage riêng của `/san-pham`.

### Bước 5 — G (split) / H (dịch vụ phí) trên dữ liệu kỳ đang xem

Quan sát bảng thật của kỳ đang xem:

- Nếu tồn tại hai mô tả khác nhau của CÙNG một máy thật (ví dụ cặp
  `FTKB50ZVMV` nếu kỳ này còn dữ liệu đó, hoặc một cặp tương đương khác) —
  xác nhận chúng vẫn là HAI dòng riêng, không bị gộp.
- Nếu KHÔNG có cặp như vậy trong kỳ đang xem: ghi
  `NOT_PRESENT_IN_CURRENT_REAL_DATA` — không tự tạo dữ liệu giả, không chặn
  vì lý do này (hành vi generic đã có E2 CHECK-PRA005-02/07 làm bằng chứng).
- Tương tự cho dòng dịch vụ/phí (`Chi phí vận chuyển`, `Chênh VAT`, `Phụ
  Phí`, `Giá treo Tivi`, hoặc mô tả tương đương thật của kỳ): nếu có, xác
  nhận còn trong bảng; nếu không có trong kỳ đang xem, ghi
  `NOT_PRESENT_IN_CURRENT_REAL_DATA`.

### Bước 6 — I (sắp xếp) / J (vắng PP) / K (`NULL != 0`)

- Xác nhận dòng đầu bảng có doanh thu cao nhất, dãy doanh thu không tăng dần
  xuống dưới (không cần xếp hạng nhãn).
- Xác nhận KHÔNG một ô/cột nào ghi giá mua tham chiếu cấp mặt hàng.
- Tìm ít nhất một mặt hàng có LN KPI hiển thị `—` hoặc một số kèm `N / M
  dòng` với `N < M` — xác nhận KHÔNG BAO GIỜ hiện `0`/`0đ` cho trường hợp
  chưa biết. Nếu kỳ đang xem tình cờ mọi mặt hàng đều `N = M` (coverage đầy
  đủ 100% mọi dòng): ghi `NO_UNKNOWN_KPI_IN_CURRENT_REAL_DATA` — không chặn
  (hành vi generic đã có E2 CHECK-PRA005-06 làm bằng chứng).

### Bước 7 — Ghi kết quả

Dán nguyên văn các số/quan sát trên vào phản hồi tiếp theo trong phiên này
(hoặc phiên kế tiếp cùng lineage) để Session tiếp tục đóng
`CHECK-PRA005-15` — KHÔNG tự đánh PASS thay Owner.

## 6. Sức khoẻ production — KHÔNG kiểm được từ session

`Reports front door`, `Cloudflare Access`, `PostgreSQL-backed history`, `R2
artifact` đều nằm sau cùng policy denial ở mục 2. Owner xác nhận trực tiếp
qua các bước 1–7 ở trên (mở trang = front door + Cloudflare Access sống;
trang có dữ liệu thật = PostgreSQL sống; nếu kỳ đang xem yêu cầu upload mới
thì R2 cũng được exercised tự nhiên qua luồng `/run` hiện có — KHÔNG tự tạo
upload giả trong phiên này).

## 7. Ngân sách / phạm vi

```text
CODE_REQUIRED         = NO       PRODUCTION_CODE_ADDED = 0 dòng
REVIEW_BUDGET_STATE   = 1 / 1 dùng (Independent Review E2, S109) ·
                        repair_cycles_used = 0 / 1 (không đổi)
TRACKING_CHANGED      = NO       INFRASTRUCTURE_CHANGED = NO
SCOPE_CHECK           = OK — docs-only; không deploy, không implement, không
                        migration/schema, không refactor/hardening, không
                        PRA-006, không sửa REM-T06
```

## 8. Governance (phiên này)

```text
branch_authority_check.sh    : AUTHORITY_OK sau khi push (nhánh có upstream);
                                DIVERGENCE trong giới hạn; WORKTREE CLEAN
validate_structure            : PASS (21 required paths)
validate_project_state        : PASS
validate_evidence              : PASS (154 REQUIRED PASS evidence record)
validate_task_completion       : PASS (12 DONE task — không đổi, PRA-005
                                CHƯA DONE nên không nằm trong tập này)
validate_reference_integrity   : FAIL — ĐÚNG 3 reference REM-T06 đã biết
                                (baseline không đổi, không issue mới)
git diff --check                : sạch
```

## 9. Kết luận phiên

```text
PRODUCTION_ACCEPTANCE_RESULT = STOP — NO_PRODUCTION_EGRESS + GATE_REQUIRES_OWNER_ACTION
DEPLOY_CANDIDATE_SHA          = 1a011ee66f9e2b2ffee4d04f6864bfb0eeb45948
DEPLOY_RESULT                 = NOT_EXECUTED_BY_SESSION (Owner runbook mục 5 phát hành)
CHECK-PRA005-15                = NOT_TESTED (không đổi)
PRA-005_FINAL_STATUS           = PRODUCTION_ACCEPTANCE_PENDING (không đổi)
BLOCKING_FINDINGS              = 0
SCOPE_DRIFT                    = NO
NEXT_ACTION                    = Owner thực hiện mục 5 (Bước 0–7) trên hệ
                                thống thật, dán kết quả vào phiên; session sẽ
                                đối chiếu với mục 27 (A–L) và đóng
                                CHECK-PRA005-15 chỉ từ số Owner cung cấp.
```

Không có phiên nào khác cần mở để làm việc này — đây KHÔNG phải một defect
cần sửa, KHÔNG cần Session 3, KHÔNG cần OWNER_OR_SCOPE_DECISION cho scope
(chỉ là một hành động đọc trên hệ thống thật mà chỉ Owner truy cập được).
