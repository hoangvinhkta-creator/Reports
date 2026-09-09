# S146 — Independent Review `R6`, VÒNG 2 (trên HEAD sau `REPAIR-1`)

Ngày: 2026-09-09
Task Mode: MAJOR (independent review)
Quyết định nền: `DEC-207`
Kết quả phiên: **`CHECK-R6-31` = `PASS` (vòng 2, E1).** Cả bốn mục của vòng 1
được xác nhận ĐÃ SỬA bằng bằng chứng ĐỘC LẬP. KHÔNG có finding
`REPAIR_REQUIRED` mới, nên lineage `R6` KHÔNG phải escalate.

Phiên KHÔNG sửa mã, KHÔNG merge, KHÔNG mở PR, KHÔNG deploy, KHÔNG làm `R7`,
KHÔNG tự đánh dấu Owner Acceptance.

Bằng chứng nguyên văn: `docs/reviews/R6-INDEPENDENT-REVIEW-RECORD-ROUND-2.md`.

---

## 1. Đối tượng review

```text
Reports   nhánh mặc định THẬT   claude/extract-upload-repo-gq2ws4  (05f2b44)
          HEAD review (detached) 40807efd50e675b71ccd1a14b5801394da4cafc1
          worktree               CLEAN
Tracking  nhánh mặc định         main = 66787c0, HEAD = origin/main, CLEAN
          diff so với origin/main  RỖNG — dependency, không có thay đổi R6

lineage (đo bằng git, không tin bàn giao)
  05f2b44 nền → 0adb6d1 → 56aca4c R6 IMPLEMENTED (vòng 1 review cái này)
          → b3fa809 bản ghi review vòng 1 → 419391c REPAIR-1 (mã)
          → 40807ef ghi nhận INTEGRATION_DECISION_REQUIRED
  cả bốn SHA đề bài nêu đều là ancestor của HEAD: XÁC NHẬN

branch authority   TARGET_SHA=40807ef… → DETACHED_EXACT_TARGET / AUTHORITY_OK
```

## 2. Kết luận từng mục của vòng 1

| Mục vòng 1 | Kết luận vòng 2 | Bằng chứng độc lập |
|---|---|---|
| `FIND-R6-IR-01` — cửa sổ so sánh vẽ `0` cho khoảng có tiền thật | **ĐÃ SỬA** | 93 phép đo qua HTTP thật, 4 probe / 4 sổ khác nhau |
| `FIND-R6-IR-02` — "Chưa xác định" đứng làm một nhóm hàng hoá | **ĐÃ SỬA** | 51 phép đo, có 1 probe toàn trang xuyên hai repo và 1 diff trực tiếp với `56aca4c` |
| `AR-R6-IR-03` — hai vế phép chia giá BQ đọc hai tập dòng | **ĐÃ SỬA** | 34 phép đo, phần lớn là diff trực tiếp với `56aca4c` |
| `COR-R6-IR-01` — docstring dẫn một file test không tồn tại | **ĐÃ SỬA** | bài canh thật tồn tại và đo đúng HTML đã render |

Phiên này KHÔNG dùng lại một fixture nào của `REPAIR-1` và KHÔNG lấy một con
số nào từ `S145` làm bằng chứng — mọi thứ được dựng và đo lại.

### 2.1 `FIND-R6-IR-01` — điểm cốt lõi

Oracle là trang Báo cáo `R5` trên **cùng server, cùng sổ, cùng kỳ, cùng mức
gộp**. Hình dạng lỗi mà vòng 1 ghi (`{'0': 60}`) không tái hiện được ở bất kỳ
đâu:

```text
R6 == R5 TỪNG MỐC, cả hai cửa sổ, ở ngay / tuan / thang / quy
cửa sổ so sánh có tiền thật ở CẢ BỐN mức (thang 2025-03 = 10.000.000;
  quy 2023-Q4 = 8.000.000 và 2024-Q2 = 6.000.000 — đo trên một sổ trải từ 2023)
số 0 CHỈ ở mốc rỗng THẬT nằm trọn trong coverage đã xác nhận; ngoài coverage
  vẫn là KHOẢNG TRỐNG
custom range neo vào `Đến ngày` người dùng gõ, KHÔNG trôi theo dữ liệu mới
  nhất, KHÔNG mượn chốt kỳ
ô chỉ tiêu / bảng gộp / giỏ hàng / bảng kê VẪN chỉ đọc phạm vi đang xem —
  giữ nguyên 25.000.000 đồng ở cả bốn mức gộp
lát MỞ RỘNG vẫn là effective data: một dòng Owner loại ở cửa sổ so sánh
  KHÔNG quay lại (R5 và R6 cùng giảm 8.000.000 → 5.000.000)
neo `scope.date_to` == `anchor_date()` với phạm vi PERIOD ở cả ba ca biên
  (kỳ hiện tại giữa tháng, kỳ quá khứ, kỳ vừa xong)
```

### 2.2 `FIND-R6-IR-02` — điểm cốt lõi

```text
đơn `Tivi + chưa khớp mã` KHÔNG còn là "đơn nhiều nhóm hàng hoá"  (ô = 2, chỉ
  hai đơn có hai nhóm CHÍNH DANH)
CẢ NĂM lý do chưa xác định đều ngoài chiều nhóm hàng; 10/10 tổ hợp hai lý do
  KHÔNG sinh cặp — đo ở min_support=1, khắt khe hơn mặc định
diff trực tiếp 56aca4c vs HEAD trên CÙNG đầu vào:
  TRƯỚC 5/5 đơn bị đếm multi + cặp ('Tivi','__UNRESOLVED__') và
        ('__CONFLICT__','__UNRESOLVED__')
  SAU   2 đơn, đúng một cặp THẬT ('Tivi','Tủ lạnh')
  KHÔNG ĐỔI: orders, multi_line, multi_product, service_attachment, ngữ nghĩa
        CẶP SẢN PHẨM, products/lines/merchandise_lines/revenue từng đơn, tổng
dòng PHÍ / CHIẾT KHẤU không bị đếm là "chưa xác định nhóm hàng", tiền vẫn đủ
UI nói ra 2 đơn / 3 dòng bị để ngoài; KHÔNG rò một trường khách hàng nào
tổng tiền/SL/đơn TRƯỚC và SAU phân loại: y hệt; đối soát bảng nhóm hàng: khớp
```

### 2.3 `AR-R6-IR-03` — điểm cốt lõi

```text
thiếu total_sales   5.000.000  → 10.000.000   (giá duy nhất quan sát được)
quantity == 0       6.500.000  → 5.000.000    (chiều ngược lại, cũng sửa)
thiếu quantity      giá BQ 8.000.000, nhưng dòng ấy VẪN góp vào min/max
hàng tặng giá 0     KHÔNG đổi một số nào so với trước repair (0 là giá THẬT)
ca bình thường      495.049,50 — KHÔNG đổi
mẫu số 0            None KÈM LÝ DO (hai câu khác nhau cho hai trạng thái),
                    không bao giờ 0
total_quantity nghiệp vụ = 6 (đếm MỌI dòng có SL) — KHÔNG bị thu hẹp
tổng doanh thu, đối soát bảng nhóm: khớp tuyệt đối
trang thật: 7.333.333,33 (gia quyền, đúng); mọi ô trống đều có `title` giải thích
```

## 3. Regression và bằng chứng vận hành

```text
R6 repair-focused (2 file)        48 passed
toàn bộ R6 (9 file)              186 passed
full pytest — lần 1         1 failed / 3444 passed / 12 skipped
full pytest — lần 2         0 failed / 3445 passed / 12 skipped
smoke R6 xuyên hai repo           29 PASS / 0 FAIL
smoke R5.1 xuyên hai repo         63 PASS / 0 FAIL   (khớp S142 §4.5)
Tracking node kiem/chay.js        62 bộ · 2892 đạt · 0 hỏng · 2 bỏ qua
git diff --check                  sạch (cả 56aca4c..HEAD và 05f2b44..HEAD)
branch_authority_check.sh         AUTHORITY_OK
validator                         STRUCTURE / STATE / EVIDENCE / COMPLETION PASS
                                  REFERENCE INTEGRITY 4 đỏ — BASELINE (S136,
                                  TASK-REM-T06), không file R6 nào góp thêm
đối soát sổ Golden                KHỚP TOÀN BỘ, 3.562.310.000 (số freeze TRƯỚC R6)
```

**Bài đỏ ở lần 1 là BASELINE của môi trường, không phải của `R6`** —
`test_105d_boundaries.py::TestG25GoldenBaselineUnchanged` báo
`fatal: bad object 740f396…` vì clone NÔNG
(`git rev-parse --is-shallow-repository` → `true`). `R6` không chạm bài kiểm
ấy hay artifact nó canh (`git diff` rỗng); chạy riêng file ấy: `41 passed`; và
sau khi `branch_authority_check.sh` thực hiện một `git fetch origin --prune`
đầy đủ, chạy LẠI toàn bộ bộ kiểm cho `0 failed` mà không ai sửa gì. Cùng hình
dạng và cùng cách xác minh mà vòng 1 (`S144` §6.2) đã ghi.

## 4. Read-only — đo lại từ đầu, không tin bàn giao

```text
alembic heads       0009_line_binding_period_close — đúng MỘT head, của R3
migration mới       KHÔNG (git diff rỗng trên tools/db/, alembic.ini, migrations)
bảng mới            KHÔNG
route POST          18 ở cả 05f2b44, 56aca4c và 40807ef — KHÔNG đổi
5 route R6          đều @app.get; POST → 405 (đo bằng HTTP thật)
bất biến tiền       git diff RỖNG trên pricing/profit/kpi/period_lock/
                    business_store/business_queries/business_service/
                    business_metrics/migrations/config/tools-db — cả từ 56aca4c
                    LẪN từ nền 05f2b44
Tracking            không lệch một byte so với origin/main
Scope Lock          37 file lineage R6 chạm, không file nào nằm ngoài
độ bền URL          40 tổ hợp tham số hỏng/lạ trên 4 route → 200/200, không 500
```

## 5. Ghi nhận — 4 mục, KHÔNG mục nào tiêu ngân sách

Không mục nào thuộc lớp bắt buộc repair của brief `R6` §7, không mục nào đổi
một con số trên màn hình. Ghi để lần chạm mã kế tiếp dọn cùng.

```text
OBS-R6-IR2-01  chuỗi "(repair AR-R6-IR-03)" — một mã finding NỘI BỘ — lọt vào
               câu chữ Owner đọc trên trang phân tích. Sửa = một chuỗi.
OBS-R6-IR2-02  docstring `drilldown_rows` thiếu "không phải": "…đo trên chính
               HTML đã render CHỨ TRÊN kết quả của hàm này". Câu đọc ra ngược
               nghĩa. Tham chiếu bài canh thì ĐÚNG, nên COR-R6-IR-01 vẫn ĐÃ SỬA.
OBS-R6-IR2-03  Scope Lock ghi `tests/test_r6_*.py MỚI (7 file)`; thực tế 9 file.
               Mẫu vẫn phủ đủ — chỉ con số trong ngoặc là cũ.
OBS-R6-IR2-04  `_chart_details` chạy HAI LẦN mỗi lần nạp trang (mỗi biểu đồ một
               lần) với CÙNG một khoảng; ở muc=quy đó là 4 năm dữ liệu đọc hai
               lần. Đo được: 2 lát mở rộng / lần nạp. Hiệu năng, không đúng/sai.
```

## 6. `INTEGRATION_DECISION_REQUIRED` — vẫn MỞ, cần Owner quyết

Đo lại trong phiên này: `cumulative LOC` từ nhánh mặc định tới HEAD =
`10.155`, ngưỡng V4.1 §8 = `5.000`. (`S145` ghi `10.100` vì đo tại `419391c`;
chênh đúng 57 dòng của commit tài liệu `40807ef` — không mâu thuẫn.)

Owner phải chọn (A) integrate/merge sớm, (B) cắt scope, hay (C) tiếp tục
divergence có lý do + ngày review. Phiên review KHÔNG chọn thay.

## 7. Trạng thái sau phiên

```text
CHECK-R6-31   NOT_TESTED → PASS (vòng 2, E1)
CHECK-R6-30   VẪN NOT_TESTED  — sổ Owner không có trong môi trường container
CHECK-R6-32   VẪN NOT_TESTED  — Owner Acceptance, không phải việc của phiên này
CHECK-R51-26  VẪN NOT_TESTED  — vẫn CHẶN merge/deploy R6 (DEC-207 §10)

repair cycle tiêu bởi phiên này   0
số dư R6                          1 allowed / 1 used / 0 remaining  (KHÔNG đổi)
ESCALATION                        KHÔNG cần — vòng 2 không có REPAIR_REQUIRED
```

`R6` vẫn **KHÔNG được merge hay deploy**. Ba việc còn lại đều thuộc Owner:
`CHECK-R51-26`, `CHECK-R6-30` (chạy đối soát trên sổ thật, trên HEAD
`40807ef`), và `CHECK-R6-32` — trong đó `CHECK-R6-32` còn phải chờ quyết định
V4.1 §8 cho cờ `INTEGRATION_DECISION_REQUIRED`.

## 8. Việc kế tiếp (theo thứ tự)

1. **Owner quyết cờ V4.1 §8** (`INTEGRATION_DECISION_REQUIRED`, LOC 10.155).
2. **Owner chạy đối soát sổ thật** trên HEAD `40807ef` → `CHECK-R6-30`:
   `.venv/bin/python scripts/r6_book_reconciliation.py --so <sổ> --so-cua-owner`
3. **Owner nghiệm thu `R5.1` trên production** → `CHECK-R51-26` (đang chặn).
4. **Owner Acceptance `R6`** → `CHECK-R6-32`.
5. Bốn `OBS-R6-IR2-*` dọn kèm ở lần chạm mã kế tiếp — KHÔNG mở repair cycle
   riêng cho chúng.
