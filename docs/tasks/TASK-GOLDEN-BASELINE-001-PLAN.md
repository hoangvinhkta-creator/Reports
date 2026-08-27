# TASK-GOLDEN-BASELINE-001 — DISCOVERY REPORT + IMPLEMENTATION PLAN

```
Task            : TASK-GOLDEN-BASELINE-001
Task Mode       : MAJOR
Phase           : V4.1-2 (governance/core/V4_1_POLICY_FREEZE.md §13)
Session         : Discovery only — KHÔNG implementation
Baseline SHA    : 716ae2e1bcb719c1c8adadbf5506c45c090c2efe
Branch          : claude/golden-baseline-discovery-plan-daxbwh
Status          : DISCOVERY = BLOCKED · OWNER_DECISION_REQUIRED (OD-GB-1)
```

> Đây là artifact **duy nhất** của task này tính đến thời điểm hiện tại
> (artifact #1/4 theo `governance/core/V4_1_POLICY_FREEZE.md` §10). Phiên
> Discovery **không** sửa production code, **không** tạo fixture, **không**
> tạo test, **không** sửa `TASK-110`, **không** sửa governance, **không** ghi
> vào `PROJECT/REVIEW_BUDGET_LEDGER.md`.

---

## PHẦN A — DISCOVERY REPORT

### A.1 Branch Authority (mục 0 của chỉ thị)

```
DEFAULT_REMOTE_REF   : refs/remotes/origin/claude/extract-upload-repo-gq2ws4
DEFAULT_BRANCH       : claude/extract-upload-repo-gq2ws4
DEFAULT_TIP          : 716ae2e1bcb719c1c8adadbf5506c45c090c2efe
HEAD_SHA             : 716ae2e1bcb719c1c8adadbf5506c45c090c2efe
CURRENT_BRANCH       : claude/golden-baseline-discovery-plan-daxbwh
UPSTREAM             : origin/claude/golden-baseline-discovery-plan-daxbwh
behind/ahead upstream: 0 / 0
behind/ahead default : 0 / 0
divergence days      : 0
cumulative LOC       : 0
DIVERGENCE           : WITHIN_LIMITS
AUTHORITY            : BRANCH_WITH_UPSTREAM
RESULT               : AUTHORITY_OK
```

`git symbolic-ref refs/remotes/origin/HEAD` ban đầu **không tồn tại** trong
clone này (`fatal: ref refs/remotes/origin/HEAD is not a symbolic ref`).
Default branch được xác định bằng hai nguồn độc lập, không hardcode:
`git remote show origin` → `HEAD branch: claude/extract-upload-repo-gq2ws4`,
và `git ls-remote --symref origin HEAD` →
`ref: refs/heads/claude/extract-upload-repo-gq2ws4  HEAD` @ `716ae2e1…`.

**Xác minh baseline Owner cung cấp:**
`git merge-base --is-ancestor 716ae2e1bcb719c1c8adadbf5506c45c090c2efe HEAD`
→ exit 0. HEAD **bằng đúng** SHA đó, đồng thời bằng đúng tip của default
branch. Không có BRANCH AUTHORITY MISMATCH.

**Một hành động đã thực hiện trước khi machine check PASS được:**
`scripts/branch_authority_check.sh` lần chạy đầu trả
`STOP — BRANCH AUTHORITY UNRESOLVED` vì nhánh session chưa có upstream (bản
copy remote của nhánh này đã bị xoá, `git fetch --prune` báo `[deleted]`).
Đã `git push -u origin claude/golden-baseline-discovery-plan-daxbwh` tại
đúng SHA `716ae2e1…` (0 commit nội dung) để lập upstream; chạy lại →
`AUTHORITY_OK` / `DIVERGENCE: WITHIN_LIMITS`. Đây là thao tác trên nhánh
session được chỉ định, không đụng default branch.

**Ghi chú không chặn:** ref cục bộ `claude/extract-upload-repo-gq2ws4` đang
lỗi thời 31 commit so với `origin/claude/extract-upload-repo-gq2ws4`. Ref này
không được checkout và không được dùng làm nguồn trạng thái ở phiên này —
mọi phép so đều dùng `origin/…`. Không tự sửa (ngoài scope).

### A.2 Governance files đã đọc

| File | Vai trò trong phiên này |
|---|---|
| `CLAUDE.md` | canonical governance entry point |
| `governance/core/V4_1_POLICY_FREEZE.md` | policy overlay V4.1 (đọc **đầy đủ**, 251 dòng) |
| `PROJECT/REVIEW_BUDGET_LEDGER.md` | ngân sách sống theo root task (Machine Control #2) |
| `scripts/branch_authority_check.sh` | Machine Control #1 — đã **chạy**, không chỉ đọc |
| `governance/core/00_SESSION_ORCHESTRATION.md` | Giao thức Mở/Đóng Phiên |
| `governance/core/TASK_COMPLETION_GATE_STANDARD.md` (tham chiếu qua gate hiện có) | ranh giới CODE COMPLETE ≠ TASK COMPLETE |
| `PROJECT/PROJECT_PROGRESS.md` | trạng thái dự án (Track A + Track B) |
| `PROJECT/PROJECT_DECISIONS.md` | DEC-108, DEC-109, DEC-114, DEC-119, DEC-121, DEC-127, DEC-140, DEC-141 |
| `PROJECT/PROJECT_PROFILE.md` (liệt kê), `PROJECT/LO_TRINH_DE_HIEU.md` | profile PRODUCT; bản roadmap dễ hiểu |
| `docs/tasks/TASK-110-validation-review-queue.md` | CHECK-110-16 nguyên văn |
| `docs/tasks/TASK-110_REPAIR_PROGRESS.md` | bảng unit R1→R8 |
| `docs/tasks/TASK-101-importer-normalizer.md` | CHECK-101-08 + mục "Đối Chiếu Dữ Liệu Thật" |
| `docs/tasks/TASK-108A-1-conversion-scheme-resolver.md` | CHECK-108A1-14 / -15 |
| `docs/analysis/05_EXCEPTIONS.md`, `docs/analysis/07_SPEC_COVERAGE.md` | bảng đối chiếu thô ↔ báo cáo |
| `docs/analysis/_evidence/evidence.json` | evidence tổng hợp đã commit |
| `.gitignore`, `config/*.yaml`, `app/pipeline.py`, `tests/**` | ràng buộc dữ liệu + pipeline + oracle hiện có |

**Golden Baseline rules** nằm tại `governance/core/V4_1_POLICY_FREEZE.md` §1 (điều kiện
`FULLY_ENFORCED`), §4.1 (Golden không tự động hạ risk), §6 (phạm vi đúng của
Golden Baseline). **Production Path Decision Rule** = §5. **Blast Radius
rules** = §4. **HARDENING/BLOCKING semantics** = §7. **Artifact limits** = §10.
**State transition authority** = §12. **Stop conditions** = §8, §9, §14.
Không có file governance đứng riêng nào mang tên GOLDEN_BASELINE_STANDARD
(đuôi `.md`) — đã kiểm tra bằng
`grep -rn "Golden" governance/`.

### A.3 Project state — có nhất quán không?

**CÓ. Không có STATE_CONFLICT.** Trạng thái Owner cung cấp khớp từng dòng với
repository tại `716ae2e1…`:

| Owner cung cấp | Nguồn trong repo | Khớp |
|---|---|---|
| V4.1-1 = COMPLETE | `PROJECT/REVIEW_BUDGET_LEDGER.md` → "Cập nhật gần nhất" 2026-08-27 V4.1-1 | ✔ |
| V4.1 = POLICY_ADOPTED, NOT FULLY_ENFORCED | `governance/core/V4_1_POLICY_FREEZE.md` §1; `PROJECT/PROJECT_PROGRESS.md` L17-21 | ✔ |
| KNOWN PRE-V4.1 DIVERGENCE = CLOSED | `PROJECT/REVIEW_BUDGET_LEDGER.md` → "Branch divergence đã biết" (DEC-141 §4) | ✔ |
| R1-A1 FROZEN; R1-A / R1 NOT FROZEN | `TASK-110_REPAIR_PROGRESS.md` bảng Tiến độ | ✔ |
| TASK-110 NOT DONE | `PROJECT/PROJECT_PROGRESS.md` L100-110; `docs/tasks/TASK-110-validation-review-queue.md` L19-20 | ✔ |
| CHECK-110-16 BLOCKED · POST_MERGE_PRODUCTION_ACCEPTANCE | `docs/tasks/TASK-110-validation-review-queue.md` L611-651 | ✔ |
| repair budget EXHAUSTED_PRE_V4.1, remaining 0 | `PROJECT/REVIEW_BUDGET_LEDGER.md` → Root Task: TASK-110 | ✔ |
| R1-A2 → R8 = OWNER_EXTENSION REQUIRED | `PROJECT/REVIEW_BUDGET_LEDGER.md` → "Owner Extension log" **trống** | ✔ |
| Golden Baseline NOT YET IMPLEMENTED | `TASK-110_REPAIR_PROGRESS.md` L1724; không có `tests/test_golden_baseline.py` | ✔ |
| Next authorized task = TASK-GOLDEN-BASELINE-001 | `PROJECT/PROJECT_PROGRESS.md` → "Next Recommended Task" | ✔ |

**Test suite tại baseline (E1):** `python3 -m pytest -q` →
`639 passed, 9 skipped in 8.55s`. 9 skip là parametrize rỗng trong
`tests/test_r1a_canonical_type_coverage.py` (`… không có field khai str/int`),
không phải skip vì thiếu dữ liệu.

### A.4 Golden data source nào THỰC SỰ tồn tại

**Kết luận thẳng: dữ liệu thô nghiệp vụ thật KHÔNG tồn tại ở bất kỳ đâu trong
repository, git history, hay môi trường thực thi này.**

Bằng chứng E1:

```
$ git ls-files | grep -i "xlsx\|\.csv\|data/"          -> (rỗng)
$ git log --all --diff-filter=A --name-only --pretty=format: | grep -i "\.xlsx$" | sort -u
                                                        -> (rỗng)
$ ls -la data                                           -> No such file or directory
```

Không một file `.xlsx` nào từng được thêm vào git ở bất kỳ commit nào, trên
bất kỳ nhánh nào. Đúng `DEC-108` và `.gitignore` (`*.xlsx`, `data/samples/`).

| Nguồn ứng viên | Tồn tại? | Nội dung | Dùng được cho gì |
|---|---|---|---|
| `data/samples/So_chi_tiet_ban_hang_TinPhat_01.2026.xlsx` | **NOT FOUND** — đã xoá sau CHECK-101-08 | 352 dòng sheet / 351 RawRow / 254 đơn | (chỉ khi Owner cấp lại) |
| `data/samples/So_chi_tiet_ban_hang_TinPhat_06.2026.xlsx` | **NOT FOUND** — đã xoá | 181 / 180 / 146 | (chỉ khi Owner cấp lại) |
| File thô toàn công ty 6 tháng (11.765 dòng) | **NOT FOUND** | nguồn của `evidence.json` | dependency của CHECK-110-16 |
| File thô toàn công ty tới 2026-09-10 (14.389 mapped + 107 unmapped) | **NOT FOUND** | nguồn của CHECK-108A1-15 | — |
| `Báo cáo Kinh doanh 2026.xlsx` | **NOT FOUND** | 59 sheet, nguồn của 55 ô cột F | — |
| **`docs/analysis/_evidence/evidence.json`** | **CÓ — đã commit, 47.575 byte** | tổng hợp đã ẩn danh | **nguồn invariant chính** |
| `tests/fixtures/synthetic_workbook.py` | **CÓ** | 8 dòng / 7 đơn, hoàn toàn bịa | fixture cấu trúc, **không** phải dữ liệu nghiệp vụ |
| `tests/fixtures/baseline/*.json` (L1, L1v1, L2) | **CÓ** | oracle non-regression của TASK-110 | **không** phải Golden Baseline (xem A.4.1) |
| `config/*.yaml` | **CÓ** | master data nhân viên/tỉ lệ/từ khoá | production path §5 nguồn (2) |

#### A.4.1 `tests/fixtures/baseline/` KHÔNG phải Golden Baseline

Repo đã có một bộ oracle tên "baseline". Phải phân biệt dứt khoát, nếu không
sẽ có người tuyên bố Golden đã tồn tại:

| | `tests/fixtures/baseline/` (đã có) | Golden Baseline (task này) |
|---|---|---|
| Mục đích | chứng minh **repair của TASK-110** không dịch chuyển nghiệp vụ | lưới an toàn regression nghiệp vụ **lâu dài** |
| Dữ liệu | fixture tổng hợp 8 dòng | dữ liệu nghiệp vụ đại diện (xem OD-GB-1) |
| Mốc so | hành vi tại `8386d34` (trước dòng sửa đầu tiên) | output nghiệp vụ đã được Owner/evidence xác minh |
| Hình dạng | dump **mọi trường** của mọi dòng (structural) | aggregate nghiệp vụ + invariant + diff đọc được |
| Phạm vi | `EmployeeMapper.resolve()` + `run_import()` scalar/graph | end-to-end + business invariant map tới authority |
| Review Queue | **cố ý loại trừ** | phải nằm trong (ở mức đếm/phân loại, xem GB-5) |
| Hạ Blast Radius? | **KHÔNG** (V4.1 §4.1: trước khi task này xong, không Golden test nào được dùng để hạ risk) | có, theo từng path đã phủ |

### A.5 Hai kỳ 01/2026 và 06/2026 — có truy được evidence không?

**CÓ — truy được tới hai nguồn độc lập đã commit.** Đây là phần mạnh nhất của
Discovery.

**Nguồn 1 — `docs/analysis/_evidence/evidence.json` (đã commit):**

```
raw_by_month_employee["01.2026|Tín Phát 0869931931"]
    = {orders: 254, qty: 407.0, sales_thousands: 3564610.0, profit_thousands: 240033.0}
raw_by_month_employee["06.2026|Tín Phát 0869931931"]
    = {orders: 146, qty: 210.0, sales_thousands: 1925272.0, profit_thousands: 95957.0}
```

Sinh bởi `tools/analysis/extract_evidence.py` tại TASK-002 từ file thô 6
tháng (`raw.line_count = 11765`, `raw.distinct_order_count = 8714`,
`date_min = 2026-01-01`, `date_max = 2026-06-30`).

**Nguồn 2 — `docs/tasks/TASK-101-importer-normalizer.md` → CHECK-101-08
(REQUIRED · PASS · E1, 2026-08-23):** chạy
`tools/analysis/reconcile_real_data.py` gọi thẳng `app.pipeline.run_import()`
trên hai file thật do Owner cấp trực tiếp:

```
01.2026: Số OrderID duy nhất: 254  ->  Kỳ vọng: 254 đơn -> PASS
06.2026: Số OrderID duy nhất: 146  ->  Kỳ vọng: 146 đơn -> PASS
```

Kèm **đối chiếu chéo độc lập không phụ thuộc engine**: dòng "Tổng cộng" do
chính file thô tự viết khớp tuyệt đối với tổng do `run_import()` tính
(01.2026: `3.564.610.000` và chiết khấu `2.300.000`; 06.2026: `1.925.272.000`
và `400.000`).

**Hai nguồn khớp nhau đến từng đồng** dù được sinh ở hai task khác nhau, từ
hai lần export khác nhau (một bản toàn công ty 6 tháng, một bản xuất riêng
theo tháng). Đây là mức xác minh cao nhất có thể đạt được mà không có file.

**Bảng số liệu kỳ đã xác minh — dùng làm expected output nghiệp vụ:**

| Chỉ số | 01.2026 (Tín Phát) | 06.2026 (Tín Phát) | Nguồn |
|---|---:|---:|---|
| Dòng trong sheet (kể cả "Tổng cộng") | 352 | 181 | CHECK-101-08 |
| Dòng thiếu OrderID (dòng "Tổng cộng", loại đúng ý) | 1 | 1 | CHECK-101-08 |
| RawRow đọc vào | 351 | 180 | CHECK-101-08 |
| **Số OrderID duy nhất** | **254** | **146** | CHECK-101-08 + evidence.json |
| Dòng mapped / unmapped | 351 / 0 | 180 / 0 | CHECK-101-08 |
| OrderID có >1 employee_raw | 0 | 0 | CHECK-101-08 |
| Tổng "Doanh số bán" raw (VND) | 3.564.610.000 | 1.925.272.000 | CHECK-101-08 + evidence.json |
| Tổng Chiết khấu (VND) | 2.300.000 | 400.000 | CHECK-101-08 |
| Tổng doanh số normalized | 3.562.310.000 | 1.924.872.000 | CHECK-101-08 |
| PERSONAL / ADS (đơn) | 0 / 254 | 0 / 146 | CHECK-101-08 |
| ADS qua `Auto:Employee Default` | 254 | 146 | CHECK-101-08, DEC-109 |
| ADS qua từ khoá "ADS" | 0 | 0 | CHECK-101-08 + `evidence.json.ads_keyword_cell_hits = {raw:0, report:0}` |
| Số dòng lệch raw vs normalized | 22 / 351 | 1 / 180 | CHECK-101-08 |
| Tổng chênh lệch (= tổng chiết khấu) | 2.300.000 | 400.000 | CHECK-101-08, DEC-114 |
| Số lượng (qty) | 407 | 210 | evidence.json |
| Lợi nhuận ERP (nghìn đồng) | 240.033 | 95.957 | evidence.json |

### A.6 Raw dataset thực tế nằm ở đâu

**Không nằm ở đâu cả trong phạm vi máy này.** Nó nằm ở phía Owner, ngoài
version control, theo đúng `DEC-108` và
`governance/product/17_DATA_GOVERNANCE_PRIVACY.md`.
`docs/tasks/TASK-101-importer-normalizer.md` ghi rõ trong mục "Deleted":
hai file `data/samples/So_chi_tiet_ban_hang_TinPhat_01.2026.xlsx` và
`..._06.2026.xlsx` **đã bị xoá khỏi môi trường sau khi dùng**, không commit
tại bất kỳ thời điểm nào.

Bố cục file (đã ghi lại, dùng được để dựng fixture):
`docs/analysis/01_DATA_MAPPING.md` §1 — header ở dòng 4, dòng 5 là header
phụ bị bỏ qua, dữ liệu từ dòng 6; 17 cột, thứ tự cố định trong
`tests/fixtures/synthetic_workbook.py::HEADER` và
`app/modules/importing/raw_reader.py::COLUMNS`.

### A.7 PII / business-sensitive data

**Trường PII khách hàng** — `app/modules/validation/models.py`:

```python
PII_FIELD_NAMES = ("customer", "customer_code", "phone", "address")
```

`WorkingLine`/`RawRow` mang thêm `imei` (số serial thiết bị — định danh vật
lý, DEC-108 liệt kê rõ) và `note_raw`/`Diễn giải` (**có thể chứa tên/địa chỉ
khách nhúng trong văn xuôi** — đây là rủi ro rò rỉ ẩn, không nằm trong
`PII_FIELD_NAMES`).

**Business-sensitive (không phải PII cá nhân khách hàng):**
`sell_price`, `accounting_purchase_price` (giá nhập — bí mật kinh doanh),
`source_profit`, `delivery_cost`, `trip_pay`/lương chuyến, và toàn bộ chuỗi
suy ra KPI/lương.

**Dữ liệu nhân viên đã được chấp nhận trong repo:** `config/employees.yaml`
chứa tên và `tests/fixtures/baseline/employee_resolve_matrix*.json` chứa số
điện thoại nhân viên (qua `_SUFFIXES`). Đây là master data vận hành, đã tồn
tại từ trước, **không** mở rộng thêm ở task này.

**Ràng buộc bất khả nghịch:** một khi commit, dữ liệu tồn tại vĩnh viễn trong
git history (DEC-108 → "Can Revisit After: Không bao giờ"). Đây là lý do
Blast Radius của chính task này là HIGH (A.15).

### A.8 Fixture tối thiểu đề xuất

Xem GB-2/GB-3. Tóm tắt: **hai fixture `.xlsx` ẩn danh, một cho mỗi kỳ**, đặt
tại `tests/fixtures/golden/` với **tên file cố định** (bắt buộc — xem A.12
HB-GB-01), giữ nguyên 351 và 180 dòng, giữ nguyên `Số BH`, `Ngày`, `SL`,
`Đơn giá`, `Doanh số bán`, `Chiết khấu`, `NVBH`, `Lợi nhuận`; thay thế toàn
bộ `Tên KH`, `Mã khách hàng`, `Địa chỉ`, `ĐT di động`, `Trường mở rộng chi
tiết 1` (IMEI); `Diễn giải` **rút gọn về nhãn cấu trúc** thay vì văn xuôi
thật. `.gitignore` đã có ngoại lệ `!tests/fixtures/**/*.xlsx`, nên đường này
mở sẵn về mặt kỹ thuật.

### A.9 Expected output tối thiểu đề xuất

Xem GB-7. Tóm tắt: **một file JSON cho mỗi kỳ**, chứa aggregate nghiệp vụ ở
mức kỳ + phân rã theo chiều, **không** dump từng dòng. Hình dạng đã được
chứng minh tính được ngay hôm nay bằng `run_import()`, không cần sửa một
dòng production code nào (E1 — xem A.11).

### A.10 Business invariants — reuse từ đâu

**Không tạo bộ invariant governance mới.** Mọi invariant map ngược về một
authority đã tồn tại:

| # | Invariant | Authority hiện có |
|---|---|---|
| I-01 | Số OrderID duy nhất 01.2026 = 254; 06.2026 = 146 | `PROJECT/PROJECT_PROGRESS.md` → "Completion Gate sơ bộ" dòng 1; CHECK-101-08 |
| I-02 | Tổng "Doanh số bán" raw khớp dòng "Tổng cộng" của chính file | CHECK-101-08 (đối chiếu chéo độc lập) |
| I-03 | `TotalSales = SellPrice × Quantity − Discount`; mọi dòng lệch raw↔normalized lệch **đúng** bằng Chiết khấu của chính dòng đó | DEC-114; CHECK-101-08 mục Item 4 |
| I-04 | `LeadSource` chỉ nhận `PERSONAL`/`ADS`; không literal `TINPHAT_ADS` | Completion Gate sơ bộ (TASK-104); DEC-119; ADR-104 |
| I-05 | LeadSource quyết định ở cấp OrderID, áp cho mọi dòng; hai dòng cùng OrderID không bao giờ khác LeadSource | Completion Gate sơ bộ (TASK-104) |
| I-06 | 100% đơn Tín Phát = ADS **qua `Auto:Employee Default`**, 0 đơn qua từ khoá | DEC-109/DEC-119; CHECK-101-08; `evidence.json.ads_keyword_cell_hits` |
| I-07 | `ConversionScheme` tra theo `(employee, employee_group, lead_source, product_group, NGÀY CỦA ĐƠN)`; không đường code nào suy tỉ lệ trực tiếp từ `LeadSource` | Completion Gate sơ bộ (TASK-108); ADR-106 §3/§4; DEC-127 §3 |
| I-08 | Tra tỉ lệ dùng **ngày của đơn**, không dùng "hôm nay"; thêm dòng chính sách `effective_from` tương lai không đổi kết quả kỳ lịch sử | Completion Gate sơ bộ (TASK-108); DEC-121 |
| I-09 | Tổ hợp không khớp dòng config nào → `Unresolved` + Review Queue; **không bao giờ mượn tỉ lệ** của người khác, không fallback | Completion Gate sơ bộ (TASK-108); `conversion_rates.yaml` header |
| I-10 | Dòng `unmapped` không bao giờ nhận tỉ lệ | DEC-104, DEC-127 §8, C11; `tests/test_conversion_engine.py::test_unmapped_employee_line_never_receives_a_rate` |
| I-11 | Employee ownership: mỗi dòng thuộc đúng một `RecordRef` trong một `snapshot_id` duy nhất | DEC-132; `EmployeeMapper.snapshot_id`; R1-A1 FROZEN contract |
| I-12 | Không có phép chia bù (`/2`) trong logic tổng hợp; mọi con số cộng đúng một lần | Completion Gate sơ bộ (TASK-109/111); DEC-115 |
| I-13 | Không hardcode tên nhân viên / tỉ lệ / target / từ khoá ADS trong `app/` | Completion Gate sơ bộ ("Mọi phase"); CHECK-101-10 |
| I-14 | `TotalConvertedRevenue == PersonalConvertedRevenue + AdsConvertedRevenue` cho mọi nhân viên-tháng | Completion Gate sơ bộ (TASK-108) |
| I-15 | RAW bất biến, giữ `source_file`/`source_sheet`/`source_row` | ADR-102; CHECK-101-11 |
| I-16 | Validation **không bao giờ chặn** import; Review Queue là báo cáo đi kèm, không phải stage sửa dữ liệu | đặc tả §18; DEC-128; `app/pipeline.py` docstring |

**I-12, I-14 hiện chưa kiểm được end-to-end** vì `summary_engine` (TASK-109)
và `excel_exporter` (TASK-111) chưa tồn tại, và TASK-108B (Converted Revenue)
đang BLOCKED bởi C15 `EligibleCosts`. Xem OUT-GB-02.

### A.11 Pipeline entry point cụ thể

```
app/pipeline.py
    run_import(raw_path: Path,
               config_dir: Path = Path("config"),
               price_provider: PriceProvider | None = None,
               product_group_provider: ProductGroupProvider | None = None) -> ImportResult

    build_working_data(...) -> WorkingData      # bước 1–10, TRƯỚC validation
```

`ImportResult = (preview, orders, unmapped_lines, review_queue)`.
Chuỗi 11 bước (docstring `app/pipeline.py`): `read_raw_rows` → `build_preview`
→ `normalize_lines` → `EmployeeMapper.apply` → `build_orders` →
`LeadSourceClassifier.apply` → (lan LeadSourceFinal) → `apply_prices` →
`apply_accounting_profit` → `apply_conversion_schemes` → `Validator.build_queue_for`.

**Golden test phải gọi `run_import()`**, không gọi lại từng module — đó là
đúng ranh giới mà `tools/analysis/reconcile_real_data.py` đã dùng khi đóng
CHECK-101-08, nên expected output so được với evidence lịch sử.

**E1 — hình dạng aggregate tính được ngay hôm nay**, chạy trên fixture tổng
hợp hiện có, không sửa production code:

```json
{ "order_count": 7, "line_count": 8, "unmapped_line_count": 1,
  "total_sales_normalized": ["11550000", 1],
  "discount_total": ["50000", 0],
  "lead_source_split": {"ADS": 2, "PERSONAL": 5},
  "scheme_distribution": {"ADS_7_5@0.075": 3, "NOI_THANH_2@0.020": 1,
                          "PERSONAL_5_5@0.055": 3, "Unresolved@None": 1},
  "employee_order_count": {"<unmapped>": 1, "Hoàng": 1, "Ly": 2,
                           "Thắng": 1, "Tín Phát": 1, "Vinh": 1},
  "review_item_count": 8 }
```

(`[tổng, số_ô_Pending]` tách tiền khỏi số ô chưa có giá — `None` không bị
gộp thành 0, giữ đúng `03_DATA_MODEL_RULES` §5.)

### A.12 Determinism risks (mục 12 của chỉ thị)

Đã audit bằng grep trên `app/` + đo thực nghiệm. **Kết quả tổng thể rất
thuận lợi**, nhưng có đúng một hố thật.

**Đo thực nghiệm (E1)** — L2 snapshot của `run_import()` trên cùng fixture,
chạy lại nhiều lần với `PYTHONHASHSEED ∈ {0, 1, 12345}`, thư mục tạm khác
nhau, `TZ=Pacific/Kiritimati` và `TZ=UTC`, `LC_ALL=C` và `LC_ALL=vi_VN.UTF-8`:
**sha256 giống hệt ở mọi tổ hợp** (`2896e87bc5242b2a`).

| # | SOURCE | IMPACT | NORMALIZATION STRATEGY | RISK OF HIDING REAL REGRESSION |
|---|---|---|---|---|
| D-01 | **Tên file đầu vào** — `raw_reader.py:94` `source_file=path.name` | **THẬT.** Đổi tên file fixture ⇒ mọi `RawRow.source_file` đổi ⇒ golden FAIL. Đo được: đây là **trường duy nhất** nhạy với tên file | Fixture có **tên file cố định, commit cùng expected output**. **KHÔNG** xoá `source_file` khỏi golden | Cao nếu xoá trường: `source_file` là provenance bắt buộc của ADR-102/I-15; xoá đi thì mất luôn khả năng phát hiện đọc nhầm sheet/file |
| D-02 | `datetime.now()` / `date.today()` | **KHÔNG CÓ.** `grep -rnE "datetime\.now\|\.today\(" app/` → 0 kết quả | không cần | — |
| D-03 | UUID / `random` | **KHÔNG CÓ.** grep → 0 kết quả | không cần | — |
| D-04 | `os.environ` / `getenv` | **KHÔNG CÓ** trong `app/` | không cần | — |
| D-05 | `hash()` ngẫu nhiên theo tiến trình | Đã tránh sẵn: `snapshot_id` dùng `hashlib.sha256`, không dùng `hash()` (docstring `baseline_snapshot._digest` ghi rõ lý do) | giữ nguyên | — |
| D-06 | Thứ tự `dict`/`set` | Python 3.7+ giữ thứ tự chèn; các chỗ xuất ra ngoài đều `sorted()` (`employee_mapper.py:464`, `rules.py:311/402`, `models.py:307/327/630`) | Golden serialize bằng `json.dumps(..., sort_keys=True)` | Trung bình: `sort_keys` che mất **thay đổi thứ tự** có ý nghĩa nghiệp vụ ⇒ vì thế phải giữ riêng `order_graph` (thứ tự line trong order) như oracle L2 đã làm |
| D-07 | Thứ tự filesystem | Không đọc thư mục; chỉ đọc đúng đường dẫn được truyền | không cần | — |
| D-08 | Locale | Đo: không ảnh hưởng. `app/modules/validation/text.py` chuẩn hoá NFC + gộp khoảng trắng, không phụ thuộc locale | ghim `ensure_ascii=False`, encoding `utf-8` tường minh | — |
| D-09 | Timezone | Đo: không ảnh hưởng. `RawRow.date` là `date` thuần, serialize `.isoformat()` | giữ nguyên | — |
| D-10 | Float formatting | **Đã loại trừ tận gốc.** Tiền là `Decimal` (ADR-103); `grep -rnE "\bfloat\(" app/` → 0 kết quả; `to_decimal` đi qua `str(value)` cho ô float | Serialize `Decimal` thành **chuỗi**, không bao giờ thành `float` | Cao nếu vi phạm: `float` biến so sánh chính xác thành xấp xỉ và làm trôi chữ số cuối vào bảng lương |
| D-11 | Excel serialization / openpyxl | Đọc `read_only=True, data_only=True`; ô ngày trả `datetime` | Fixture tạo bằng chính `openpyxl` đang pin; ghi version vào metadata golden | Trung bình |
| D-12 | Version interpreter/thư viện | `pyproject.toml` chỉ ràng `>=`: `openpyxl>=3.1`, `PyYAML>=6.0`, `requires-python >=3.11`. Môi trường hiện tại: CPython **3.11.15**, openpyxl **3.1.5**, PyYAML **6.0.1**. R1-A1 FROZEN contract **đã ghim CPython 3.11.15** cho corpus annotation | Ghi 3 version vào block `_environment` của expected output; **so sánh nhưng chỉ WARN**, không FAIL | Cao nếu FAIL cứng: mọi nâng cấp thư viện sẽ đỏ golden và bị "sửa" bằng cách sinh lại expected output — tức là xoá bằng chứng |
| D-13 | `EmployeeMapper.snapshot_id` | **Là tài sản, không phải rủi ro.** Đo được: sửa comment trong `employees.yaml` ⇒ `snapshot_id` **không đổi** (`17fffad7c6d499cc`); sửa `normalized: "Ly"` → `"Ly2"` ⇒ **đổi** (`7d55239d11639603`) | **Nhúng `snapshot_id` vào expected output** làm chốt danh tính config | Thấp — ngược lại, nó bắt được config drift mà aggregate có thể không thấy |
| D-14 | Generated metadata (timestamp trong file `.xlsx` fixture) | openpyxl ghi `created`/`modified` vào `docProps`. Fixture được **commit như blob nhị phân cố định**, không sinh lại lúc chạy test ⇒ không ảnh hưởng | Không sinh lại fixture trong test; sinh một lần, commit, khoá | Cao nếu sinh lúc chạy: mất tính tái lập giữa các máy |

**Nguyên tắc chặn (V4.1 §6):** normalization **không được** xoá dữ liệu
nghiệp vụ để test xanh. Cụ thể ba điều cấm ở GB-6.

### A.13 Normalization strategy

Xem GB-6 (đầy đủ). Nguyên tắc: chuẩn hoá **biểu diễn**, không chuẩn hoá
**giá trị nghiệp vụ**.

### A.14 Production-path coverage (V4.1 §5)

Áp rule bốn nguồn ngay trong thiết kế:

| Thành phần Golden | Dựng từ nguồn nào (§5) | Phân loại |
|---|---|---|
| Bố cục sheet, 17 cột, header dòng 4 / data dòng 6 | (1) annotation/schema inventory — `raw_reader.COLUMNS`, `docs/analysis/01_DATA_MAPPING.md` §1 | production-realistic |
| Chuỗi `NVBH` thật (`Tín Phát 0869931931`, `Đức Kiên - Tân Á 0867666533`, …) | (2) config hiện hành `config/employees.yaml` + (4) raw đã xác minh qua `evidence.json.raw.employees` | production-realistic |
| Ngày, số lượng, đơn giá, chiết khấu, `Số BH` | (4) raw production đã xác minh — **chỉ khi Owner cấp lại file** | production-realistic **nếu** OD-GB-1 = A |
| Cùng bộ số nhưng do agent bịa ra để khớp tổng | không thuộc 1–4 | **HARDENING BY DEFAULT** — không được gọi là production baseline |
| Tổng kỳ 254/146, 3.564.610.000/1.925.272.000 | (4) qua evidence đã commit (`evidence.json` + CHECK-101-08) | production-realistic |
| Tỉ lệ 5,5% / 7,5% / 2,0% / 8,0% | (2) `config/conversion_rates.yaml` | production-realistic |

**Hệ quả trực tiếp:** nếu Owner **không** cấp lại file thô, một fixture dựng
bằng cách bịa từng dòng sao cho tổng bằng 3.564.610.000 **không** đạt tiêu
chuẩn nguồn (4) và **không được** gọi là Golden Baseline nghiệp vụ. Nó chỉ là
fixture cấu trúc mở rộng. Đây chính là nội dung OD-GB-1.

### A.15 Blast Radius theo từng data path (V4.1 §4)

Chấm theo **đường dữ liệu**, không theo tên file. `canonical.py` xuất hiện ở
nhiều path với mức khác nhau — đúng như §4 yêu cầu.

| Path | Mô tả failure | Có chặn trước output không? | Blast Radius | Golden test nào phủ (GB-8) | Hạ 1 bậc? |
|---|---|---|---|---|---|
| P1 — Raw ingestion (`raw_reader`) | sót/nhân đôi dòng ⇒ sai số đơn, sai tổng | Có — I-02 đối chiếu dòng "Tổng cộng" của chính file | **HIGH** | `test_golden_period_row_and_order_counts` + `test_golden_raw_total_matches_source_total_row` | **CÓ** → MEDIUM |
| P2 — Normalization / chiết khấu (`normalizer`, DEC-114) | trừ sai/không trừ chiết khấu ⇒ doanh số sai | Không có gate độc lập | **HIGH** | `test_golden_discount_delta_equals_discount_column` (I-03) | **CÓ** → MEDIUM |
| P3 — Employee identity (`employee_mapper`, `RecordRef`, `snapshot_id`) | sai chủ sở hữu dòng ⇒ sai KPI ⇒ **sai lương** | Không | **HIGH** | `test_golden_employee_ownership_matrix` + chốt `snapshot_id` (I-11) | **CÓ** → MEDIUM |
| P4 — Sealing / immutability (`canonical.py` `@canonical`, `FrozenMapping`) | object nghiệp vụ bị sửa **sau khi** seal ⇒ giá trị sai không ai thấy | Không | **HIGH** | Golden **không** phủ trực tiếp (nó so output cuối, không quan sát mutation giữa chừng) | **KHÔNG** |
| P5 — Annotation validation (R1-A1 FROZEN contract) | `@canonical` im lặng chấp nhận kiểu lẽ ra phải từ chối ⇒ vô hiệu hoá P4 | Không | **HIGH** (blast của P4) | `tests/test_r1a1_annotation_contract.py` — **không phải** Golden | **KHÔNG** |
| P6 — LeadSource classification | PERSONAL↔ADS sai ⇒ tỉ lệ sai ⇒ doanh số quy đổi sai | Không | **HIGH** | `test_golden_lead_source_split_and_provenance` (I-04/05/06) | **CÓ** → MEDIUM |
| P7 — Conversion scheme resolution | sai tỉ lệ hoặc mượn tỉ lệ người khác ⇒ **sai lương** | Một phần — `Unresolved` vào Review Queue | **HIGH** | `test_golden_scheme_distribution` + `test_golden_unmapped_never_gets_a_rate` (I-07/09/10) | **CÓ** → MEDIUM |
| P8 — Effective dating (DEC-121) | tra tỉ lệ bằng "hôm nay" ⇒ viết lại báo cáo đã phát hành | Không | **HIGH** | `test_golden_is_stable_when_a_future_policy_row_is_added` (I-08) | **CÓ** → MEDIUM |
| P9 — Accounting profit (`profit_engine`) | lợi nhuận kế toán sai | Không | **HIGH** | phủ **một phần**: hôm nay giá nhập toàn `Pending` ⇒ profit `Pending` | **KHÔNG** (xem OUT-GB-03) |
| P10 — KPI / Adjustment / EligibleKpiProfit | sai thưởng/lương | — | **HIGH** | **chưa tồn tại** (TASK-202/302/305) | **KHÔNG** |
| P11 — Converted Revenue totals (TASK-108B) | I-14 sai ⇒ tổng quy đổi sai | — | **HIGH** | **chưa tồn tại** — BLOCKED bởi C15 | **KHÔNG** |
| P12 — Summary aggregation (TASK-109) | `/2` bù trừ, cộng hai lần (I-12) | — | **HIGH** | **chưa tồn tại** | **KHÔNG** |
| P13 — Export `.xlsx` (TASK-111) | số đúng trong bộ nhớ, sai trên file phát hành | — | **HIGH** | **chưa tồn tại** | **KHÔNG** |
| P14 — Validation / Review Queue | báo sai finding, chỉ sai dòng | Không sửa dữ liệu (bước 11 chỉ đọc, I-16) | **MEDIUM** | `test_golden_review_queue_shape` (đếm + phân loại, **không** so nguyên văn message) | **CÓ** → LOW |
| P15 — Pricing (`PendingPriceProvider`) | sai giá nhập | Hôm nay mọi giá = `Pending` | **LOW hôm nay / HIGH khi có Price Master** | `test_golden_all_prices_pending` (chốt trạng thái hiện tại) | n/a |

**Ghi rõ theo §4.1:** việc hạ một bậc ở P1/P2/P3/P6/P7/P8/P14 **chỉ có hiệu
lực sau khi** `TASK-GOLDEN-BASELINE-001` hoàn tất và test tương ứng thật sự
tồn tại và PASS. Cho tới lúc đó, **không** Golden test nào được dùng để hạ
Blast Radius (V4.1 §4.1, câu cuối). Mọi lần viện dẫn phải nêu tên test +
fixture + path + expected output như bảng trên, không được nói "Golden tồn
tại nên an toàn".

**P4/P5 không bao giờ được Golden hạ risk** — Golden so output cuối, nên nó
mù với mutation xảy ra giữa chừng rồi lại bị ghi đè, và mù với việc lớp
enforcement bị vô hiệu hoá. Đây chính là ranh giới V4.1 §6: Golden bắt "hôm
nay khác hôm qua", không bắt "cả hai cùng sai".

### A.16 Effective Risk của task

```
Local Risk   : LOW–MEDIUM  (task chỉ thêm test + fixture + 1 artifact;
                            Scope Lock cấm sửa app/)
Blast Radius : HIGH
Effective Risk = max(Local, Blast) = HIGH
```

Hai failure path HIGH có nguồn production cụ thể (đạt §5), không phải giả định:

- **BR-1 — Rò rỉ PII vào git history.** Nếu anonymization sót một trường (đặc
  biệt `Diễn giải` và `Trường mở rộng chi tiết 1`/IMEI, hai trường **không**
  nằm trong `PII_FIELD_NAMES`), dữ liệu cá nhân khách hàng tồn tại **vĩnh
  viễn**. Vi phạm `governance/product/17_DATA_GOVERNANCE_PRIVACY.md` và
  DEC-108 ("Can Revisit After: Không bao giờ"). Không có gate nào chặn sau
  khi push. Production path: nguồn (4) + chính sách dữ liệu hiện hành.
- **BR-2 — Đóng băng một hành vi sai thành "chuẩn".** Expected output được
  sinh từ code hiện tại. Nếu code hiện tại đã sai ở một path, Golden biến cái
  sai đó thành mốc, và mọi lần sửa đúng sau này sẽ **đỏ** rồi bị "sửa" bằng
  cách sinh lại expected output. Không có gate nào đứng giữa. Production
  path: nguồn (3) — chính Golden fixture trở thành nguồn production-realistic
  cho các review sau, theo §5(3).

BR-2 được giảm nhẹ (không loại bỏ) bằng GB-1: mọi con số aggregate phải khớp
**evidence đã commit trước khi có code này** (`evidence.json` sinh tại
TASK-002, trước TASK-101), nên Golden không chỉ chép lại chính mình.

### A.17 Review Budget đề xuất

Theo bảng đã freeze (V4.1 §2), `HIGH → 2 blocking repair cycles`. **Không tồn
tại HIGH = 3.** Owner được phép đặt thấp hơn.

Block đề xuất cho `PROJECT/REVIEW_BUDGET_LEDGER.md` — **phiên này KHÔNG ghi
vào ledger**, chỉ đề xuất (V4.1 §16 cấm sửa governance ở phiên Discovery):

```
root_task: TASK-GOLDEN-BASELINE-001
effective_risk: HIGH
repair_cycles_allowed: 2
repair_cycles_used: 0
repair_cycles_remaining: 2

scope_lock:
    - app/**              : FORBIDDEN (không sửa production code)
    - config/**           : FORBIDDEN
    - docs/tasks/TASK-110*: FORBIDDEN
    - governance/**       : FORBIDDEN
    - tests/fixtures/baseline/**, tests/test_task110_non_regression.py : FORBIDDEN

cycles:
- id: (chưa mở — chưa có repair)
  base_sha: N/A
  head_sha: N/A
```

Quy tắc áp dụng (V4.1 §2, §3):
- Ngân sách gắn với **root task lineage** `TASK-GOLDEN-BASELINE-001`. Mọi
  sub-unit (GB-1…GB-12 hay bất kỳ cách chia nào khác) **tiêu chung** ngân sách
  này, không có budget riêng, không reset.
- **Chưa tiêu cycle nào ở phiên Discovery** — chưa có repair.
- Khi một blocking repair cycle mở: ghi `base_sha` = SHA **trước** repair,
  `head_sha` tiến lên theo từng lần sửa trong **cùng** cycle; `base_sha`
  **không** reset. Phạm vi xác định bằng
  `git diff <base_sha>..<head_sha> --name-only`.
- Không dùng session mới / branch mới / tên task mới để reset `base_sha`.
- Vượt 2 cycle → `OWNER_EXTENSION REQUIRED`, dừng.

### A.18 File dự kiến tạo/sửa ở implementation

| File | Hành động | Thuộc GB |
|---|---|---|
| `tests/fixtures/golden/__init__.py` | tạo | GB-8 |
| `tests/fixtures/golden/period_2026_01.xlsx` | tạo (blob nhị phân, tên **cố định**) | GB-2, GB-3 |
| `tests/fixtures/golden/period_2026_06.xlsx` | tạo (blob nhị phân, tên **cố định**) | GB-2, GB-3 |
| `tests/fixtures/golden/expected/period_2026_01.json` | tạo | GB-7 |
| `tests/fixtures/golden/expected/period_2026_06.json` | tạo | GB-7 |
| `tests/fixtures/golden/build_expected.py` | tạo — sinh expected output, **chạy tay**, không chạy trong test | GB-7, GB-9 |
| `tests/fixtures/golden/anonymize.py` | tạo — biến raw thật thành fixture ẩn danh, **chạy tay một lần**, ghi rõ không bao giờ nhận file thật trong CI | GB-3 |
| `tests/test_golden_baseline.py` | tạo — **file test bắt buộc theo V4.1 §1** | GB-8, GB-9, GB-10 |
| `docs/tasks/TASK-GOLDEN-BASELINE-001-PLAN.md` | **sửa** (file này) — thêm Completion Gate + Evidence | GB-11, GB-12 |
| `PROJECT/REVIEW_BUDGET_LEDGER.md` | sửa — thêm root task entry (A.17) | GB-11 |
| `PROJECT/PROJECT_PROGRESS.md` | sửa — trạng thái task + `V4.1 = FULLY_ENFORCED` khi đạt | GB-11 |
| `PROJECT/LO_TRINH_DE_HIEU.md` | sửa — đồng bộ bắt buộc nếu roadmap Track A đổi trạng thái (Giao thức Đóng Phiên bước 5) | GB-11 |
| `governance/core/V4_1_POLICY_FREEZE.md` | **KHÔNG SỬA** — §1 đã mô tả sẵn điều kiện; trạng thái adoption ghi ở `PROJECT/PROJECT_PROGRESS.md` | — |
| `app/**`, `config/**` | **KHÔNG SỬA** — Scope Lock | — |

**Artifact governance đếm được: 1** (`TASK-GOLDEN-BASELINE-001-PLAN.md`).
Fixture/test/expected là artifact **kỹ thuật**, không phải artifact
governance. Ngưỡng `OWNER APPROVAL REQUIRED` (artifact governance thứ 5+,
V4.1 §10) **chưa chạm**. Không tạo thêm CONTRACT / MODE / RECONCILIATION /
FINALIZATION artifact.

### A.19 Lệnh test Golden dự kiến

```bash
python3 -m pytest tests/test_golden_baseline.py -q
```

Sinh lại expected output (**chỉ chạy tay, chỉ khi Owner phê duyệt một thay
đổi nghiệp vụ có chủ đích**):

```bash
python3 -m tests.fixtures.golden.build_expected
```

`pyproject.toml` đã có `pythonpath = ["."]` và `testpaths = ["tests"]`, nên
lệnh trên chạy được từ repo root không cần cấu hình thêm.

### A.20 Quan hệ với CHECK-110-16

**Golden Baseline KHÔNG thay thế và KHÔNG PASS được CHECK-110-16.** Ba lý do
cụ thể, không phải lý do thủ tục:

1. **Khác dataset.** CHECK-110-16 đo trên file thô **toàn công ty 6 tháng,
   11.765 dòng**. Golden đề xuất dùng hai kỳ **chỉ của Tín Phát**, 351 + 180
   dòng. Mốc tham chiếu của CHECK-110-16 (`Missing` thiếu nhân viên = 2,
   `Missing` thiếu SL = 52, V3 lợi nhuận âm = 1.912, dòng phụ = 1.261 / 30
   loại, V1-P = 11.765) **không** tái tạo được từ hai kỳ Tín Phát.
2. **Khác câu hỏi.** CHECK-110-16 hỏi "Review Queue trên dữ liệu thật có ra
   đúng số phát hiện đã đo không". Golden hỏi "output hôm nay có khác output
   đã xác minh không". V4.1 §6 tách rõ hai loại.
3. **Gate Class.** `POST_MERGE_PRODUCTION_ACCEPTANCE` (DEC-141) — chỉ đóng
   được bằng dữ liệu production thật. `TASK-GOLDEN-BASELINE-001` **không**
   được đổi gate, PASS gate, xoá gate, sửa `TASK-110`, hay tuyên bố
   `TASK-110 DONE`.

**Dependency map (đề xuất, Owner quyết định riêng):**

```
Owner cấp file thô 2 kỳ Tín Phát (01.2026 + 06.2026)
    └─> TASK-GOLDEN-BASELINE-001  ──> V4.1 = FULLY_ENFORCED

Owner cấp file thô toàn công ty 6 tháng (11.765 dòng)
    └─> CHECK-110-16 đánh giá được ──> TASK-110 có thể DONE

Hai nhánh ĐỘC LẬP. Nhánh trên không mở nhánh dưới.
```

**Hạ tầng dùng chung (đây là lợi ích thật, và là tất cả những gì có):** nếu
GB-3 tạo ra `anonymize.py` + quy trình nhận file có kiểm soát, thì khi Owner
cấp file 6 tháng, phiên đánh giá CHECK-110-16 dùng lại được đúng hạ tầng đó
thay vì dựng lại. Đó là **đề xuất**, không phải thay thế.

### A.21 Những gì Golden Baseline KHÔNG chứng minh

Ghi rõ để không ai viện dẫn quá tầm (V4.1 §6):

1. **Không** chứng minh logic mới đúng — chỉ chứng minh nó **giống** mốc đã
   xác minh.
2. **Không** chứng minh baseline vốn đúng. Nếu baseline sai, Golden khoá cái
   sai lại (BR-2).
3. **Không** thay thế exploratory review / adversarial review. Không có claim
   định lượng kiểu "Golden thay 70% adversarial review".
4. **Không** cấm reviewer tìm attack mới (V4.1 §7: discovery budget không bị
   hạn chế bởi repair budget).
5. **Không** bắt được "baseline và implementation mới cùng sai".
6. **Không** phủ P4 (sealing) và P5 (annotation validation) — Golden so output
   cuối, mù với mutation giữa chừng và với lớp enforcement bị vô hiệu hoá.
7. **Không** phủ P9–P13 (KPI/Adjustment, Converted Revenue, Summary, Export) —
   những module đó chưa tồn tại.
8. **Không** đóng CHECK-110-16 (A.20).
9. **Không** chứng minh dữ liệu ẩn danh đại diện cho mọi hình dạng dữ liệu
   production tương lai — nó đại diện cho **hai kỳ đã đo**.

### A.22 BLOCKING findings

**KHÔNG CÓ.**

Đã kiểm tra `app/` cho các nguồn nondeterminism và không tìm thấy defect
production nào có production path hiện tại theo §5. Không có finding nào đạt
đồng thời hai điều kiện của V4.1 §7 (production path hiện tại + tác động
correctness/data/business/safety).

Cụ thể, ba thứ dễ bị nhầm là BLOCKING nhưng **không phải**:
- `source_file` nhạy với tên file (D-01) — đây là provenance **đúng ý** theo
  ADR-102/I-15, không phải defect. Nó là ràng buộc thiết kế của Golden.
- `pyproject.toml` không pin version (D-12) — chưa gây sai giá trị nghiệp vụ
  nào ở hiện tại; là robustness tương lai ⇒ HARDENING.
- `snapshot_id` phụ thuộc nội dung `employees.yaml` (D-13) — hành vi đúng, đã
  đo (comment-insensitive, content-sensitive).

### A.23 HARDENING findings

Mỗi finding có RE-TRIGGER CONDITION cụ thể, gắn với cơ chế/test, không phải
lời hứa trong prose (V4.1 §7).

**HB-GB-01 — Golden snapshot bị khoá cứng vào tên file fixture.**
`app/modules/importing/raw_reader.py:94` gán `source_file=path.name`. Đo được
(E1): đổi tên file đầu vào ⇒ `RawRow.source_file` là **trường duy nhất** đổi
trong toàn bộ L2 snapshot. Không có production path sai giá trị nào — nhưng
bất kỳ artifact golden nào serialize `source_file` sẽ vỡ khi đổi tên fixture.
*RE-TRIGGER:* khi một golden/oracle artifact serialize `source_file`, **và**
khi có đề xuất đổi tên/di chuyển file trong `tests/fixtures/golden/`.
*Cơ chế:* GB-8 thêm `test_golden_fixture_filenames_are_pinned` khẳng định
đúng tên file mà expected output ghi trong `_environment.fixture_filename`.

**HB-GB-02 — Không pin version openpyxl / PyYAML / CPython.**
`pyproject.toml`: `openpyxl>=3.1`, `PyYAML>=6.0`, `requires-python >=3.11`.
Môi trường đo: CPython 3.11.15, openpyxl 3.1.5, PyYAML 6.0.1. Một thay đổi
trong cách openpyxl parse ô có thể dịch chuyển golden output mà không có
commit nào trong `app/`.
*RE-TRIGGER:* golden diff FAIL khi `git diff` trên `app/` và `config/` **rỗng**.
*Cơ chế:* GB-7 ghi block `_environment` vào expected output; GB-9 khi FAIL
phải in so sánh version **trước** khi in diff nghiệp vụ, để phân biệt ngay
"đổi thư viện" với "đổi nghiệp vụ".

**HB-GB-03 — `Diễn giải` và IMEI nằm ngoài `PII_FIELD_NAMES`.**
`PII_FIELD_NAMES = ("customer", "customer_code", "phone", "address")` không
bao gồm `note_raw` (`Diễn giải`) và `imei` (`Trường mở rộng chi tiết 1`).
`Diễn giải` là văn xuôi tự do do người nhập viết, có thể chứa tên/địa chỉ
khách nhúng trong câu; `imei` là định danh thiết bị vật lý mà DEC-108 liệt kê
là lý do không commit. Với `tests/fixtures/baseline/` hiện tại điều này không
gây hại (fixture tổng hợp, không có dữ liệu thật). Với Golden dựng từ dữ liệu
thật, đây là đường rò rỉ chính.
*RE-TRIGGER:* bất kỳ fixture nào dựng từ dữ liệu production thật đi vào git.
*Cơ chế:* GB-3 xử lý hai trường này tường minh; GB-8 thêm
`test_golden_fixture_contains_no_free_text_and_no_imei` quét chính blob
fixture đã commit.

**HB-GB-04 — `sort_keys=True` che thay đổi thứ tự có nghĩa nghiệp vụ.**
Serialize ổn định đòi `sort_keys`, nhưng thứ tự line trong một Order **là**
business state (`Order.total_sales`, `line_count` đọc từ nó). Oracle L2 hiện
có đã giải bài này bằng `order_graph` (Audit O2 của TASK-110).
*RE-TRIGGER:* khi expected output thêm bất kỳ collection nào bị `sorted()`
trước khi ghi.
*Cơ chế:* GB-7 giữ `order_graph` (`order_id -> [source_row, …]`, **giữ thứ
tự**) song song với các aggregate đã sort.

### A.24 OUT_OF_SCOPE findings

**OUT-GB-01 — CHECK-110-16 vẫn BLOCKED.** Cần file thô toàn công ty 6 tháng /
11.765 dòng. Không thuộc contract của task này (A.20). Không sửa, không đổi
gate, không PASS.

**OUT-GB-02 — I-12 và I-14 chưa kiểm được end-to-end.**
`TotalConvertedRevenue == Personal + Ads` (I-14) và "không có `/2` trong logic
tổng hợp" (I-12) cần `summary_engine` (TASK-109) và Converted Revenue
(TASK-108B, BLOCKED bởi C15 `EligibleCosts`). Golden hiện tại chỉ khoá được
**tỉ lệ per-line** (P7) và `scheme_distribution`, không khoá được tổng quy
đổi. Ghi lại làm hạng mục mở rộng Golden khi TASK-108B/109 mở.

**OUT-GB-03 — P9 (accounting profit) chỉ phủ được một phần.** Mặc định
`PendingPriceProvider` ⇒ mọi `accounting_purchase_price` và
`accounting_profit` là `Pending`. Golden khoá được **trạng thái Pending đó**
(giá trị thật hôm nay), nhưng không khoá được phép tính lợi nhuận trên giá
nhập thật cho tới khi có Price Master.

**OUT-GB-04 — Ref cục bộ `claude/extract-upload-repo-gq2ws4` lỗi thời 31
commit.** Không được checkout, không dùng làm nguồn trạng thái ở phiên này.
Vệ sinh môi trường, không thuộc contract.

**OUT-GB-05 — Ba con số Owner nêu không hoàn toàn khớp evidence, cần đính
chính.** Xem A.25.

### A.25 Đính chính số liệu (chỉ thị mục 5 — không coi prompt là ground truth)

Đã truy nguồn từng con số Owner nêu. Ba nhận xét:

1. **"khoảng 254 đơn kỳ 01/2026" và "khoảng 146 đơn kỳ 06/2026"** —
   **XÁC NHẬN, chính xác tuyệt đối** (không phải "khoảng"). Hai nguồn độc lập,
   khớp từng đồng (A.5).

2. **"khoảng 14.389 dòng dữ liệu thô"** — **CÓ TỒN TẠI nhưng thuộc một dataset
   KHÁC.** 14.389 là *số dòng map được* trong CHECK-108A1-15, trên file thô
   toàn công ty phạm vi `2026-01-01 .. 2026-09-10` (tổng 14.389 mapped + 107
   unmapped = 14.496 dòng). Nó **không phải** dataset của `evidence.json`
   (11.765 dòng, `2026-01-01 .. 2026-06-30`), cũng **không phải** dataset của
   CHECK-110-16 (11.765 dòng), cũng **không phải** hai kỳ Tín Phát (351 + 180
   dòng). Trong repo tồn tại bằng chứng của **ba** dataset thô khác nhau.
   Không được trộn ba mốc này.

3. **"55 ô Summary cột F từng được đối chiếu với 0 lệch"** — **CẦN ĐÍNH
   CHÍNH.** CHECK-108A1-14 (E1) ghi rõ:

   ```
   Ô đối chiếu ĐỘC LẬP được  : 36
       khớp                  : 36
       LỆCH                  :  0
   Ô KHÔNG đối chiếu được    : 19
       Nội thành 8 · Gia dụng 8 · Fanpage 2 · Linh 1
   ```

   Tức là **55 ô được xem xét, 36 ô đối chiếu độc lập được với 0 lệch, 19 ô
   ghi nhận là GIỚI HẠN — không tính là đối chiếu thành công.** Chính
   CHECK-108A1-14 ghi rằng con số 52 báo trước đó là sai vì 16 ô chỉ "khớp"
   nhờ mapping tự gán, và Independent Review #1 Finding 3 (HIGH) đã bác bỏ.
   Nếu Golden dùng "55 ô, 0 lệch" làm invariant, nó sẽ tái lập chính cái
   PASS giả đã bị bác. Golden **chỉ được** dùng 36 ô đối chiếu độc lập được.

   Ngoài ra nguồn của các ô này là `Báo cáo Kinh doanh 2026.xlsx` — **không
   commit, NOT FOUND**. Phần đã commit là `evidence.json.report.conversion_rows`
   (56 mục: công thức, target, nhãn kỳ/nhân viên) và
   `evidence.json.report.sheet_totals` (56 sheet). Đây là thứ Golden dùng
   được, không phải workbook.

---

## PHẦN B — OWNER DECISION REQUIRED

### OD-GB-1 — Nguồn dữ liệu cho Golden Dataset

Đây là **ambiguity ảnh hưởng contract** duy nhất còn lại. Không tự quyết
(V4.1 §5, §12; chỉ thị mục 19).

**Vấn đề:** chỉ thị mục 4 yêu cầu Golden trả lời *"với cùng dữ liệu nghiệp vụ
**đã được xác minh**…"* và mục 6 yêu cầu *"ưu tiên hai kỳ nghiệp vụ thật đã
được xác minh nếu evidence hỗ trợ"*. Evidence **có** hỗ trợ (A.5), nhưng
**dữ liệu thô thì không còn tồn tại** (A.4/A.6) — và chỉ thị mục 5 cấm dựng
synthetic replacement rồi gọi nó là production baseline.

**Ba lựa chọn:**

**A — REAL-DERIVED (đề xuất).** Owner cấp lại một lần
`So_chi_tiet_ban_hang_TinPhat_01.2026.xlsx` và `..._06.2026.xlsx` theo đúng
quy trình đã dùng ở CHECK-101-08 (đặt tạm `data/samples/`, xoá sau khi dùng).
Phiên implementation chạy `anonymize.py` **một lần**, commit **chỉ** fixture
đã ẩn danh, xoá bản gốc.
- Golden đạt nguồn (4) của §5 ⇒ **production-realistic**.
- Giữ nguyên 254/146 và mọi invariant I-01…I-11 trên dữ liệu thật.
- Rủi ro: BR-1 (rò rỉ PII) — GB-3 xử lý.

**B — EVIDENCE-CONSTRAINED SYNTHETIC.** Không cấp file. Dựng fixture bằng
cách sinh dòng sao cho mọi aggregate khớp bảng A.5.
- **KHÔNG** đạt nguồn (4). Theo §5 ⇒ **HARDENING BY DEFAULT**.
- Nó **không được** gọi là Golden Baseline nghiệp vụ; nó là fixture cấu trúc
  mở rộng. Vẫn hữu ích (khoá được P1/P2/P6/P7/P8/P14 ở mức regression), nhưng
  không trả lời được câu hỏi ở chỉ thị mục 4.
- Cần Owner chấp nhận tường minh việc hạ cấp này.

**C — HOÃN.** Giữ `V4.1 = POLICY_ADOPTED` cho tới khi có dữ liệu.

**Câu hỏi cần Owner trả lời (chính xác trường/phạm vi cần, theo chỉ thị mục
13):**

| Cần gì | Chi tiết |
|---|---|
| File | `So_chi_tiet_ban_hang_TinPhat_01.2026.xlsx`, `So_chi_tiet_ban_hang_TinPhat_06.2026.xlsx` — đúng hai file đã dùng ở CHECK-101-08 |
| Phạm vi ngày | `2026-01-01 .. 2026-01-31` và `2026-06-01 .. 2026-06-30` |
| Cột **bắt buộc giữ nguyên giá trị** | `Ngày`, `Số BH`, `SL`, `Đơn giá`, `Doanh số bán`, `Chiết khấu`, `NVBH`, `Lợi nhuận` |
| Cột **sẽ bị thay thế/ẩn danh** | `Tên KH`, `Mã khách hàng`, `Địa chỉ`, `ĐT di động (Người liên hệ)`, `Trường mở rộng chi tiết 1` (IMEI), `Diễn giải`, `Giao vận`, `Lương chuyến` |
| Cột không cần | không có — giữ đủ 17 cột để bố cục khớp `raw_reader.COLUMNS` |
| Cam kết | bản gốc **không** commit, xoá khỏi môi trường ngay sau khi sinh fixture (đúng DEC-108, như CHECK-101-08 đã làm) |

**Quyết định phụ (nếu OD-GB-1 = A):** `Diễn giải` xử lý thế nào? Nó là đầu
vào của rule từ khoá ADS (I-06), nên không thể xoá trắng.
- **A1 (đề xuất)** thay bằng nhãn cấu trúc giữ nguyên **sự có/không có** từ
  khoá ADS: `"Bán hàng"` hoặc `"Bán hàng ADS"`. Trên hai kỳ này, evidence đã
  chứng minh **0 dòng** chứa "ADS" (`ads_keyword_cell_hits.raw_workbook = 0`)
  ⇒ mọi ô thành `"Bán hàng"`, và I-06 vẫn kiểm được đúng (0 qua từ khoá, 100%
  qua employee default).
- **A2** giữ nguyên `Diễn giải` — **không khuyến nghị**, đây là đường rò rỉ
  chính (HB-GB-03).

---

## PHẦN C — IMPLEMENTATION PLAN (GB-1 → GB-12)

Chỉ được bắt đầu sau khi Owner phê duyệt (Phần D). Không phân rã thành
subtask mới; GB-x là các bước tuần tự trong **cùng một** lineage
`TASK-GOLDEN-BASELINE-001`, tiêu **chung** review budget ở A.17.

### GB-1 — Source provenance

- **Mục tiêu:** mỗi con số trong expected output truy được về một authority đã
  tồn tại trước code, không phải về chính code.
- **Input:** `docs/analysis/_evidence/evidence.json`;
  `docs/tasks/TASK-101-importer-normalizer.md` (CHECK-101-08);
  `docs/analysis/05_EXCEPTIONS.md` Nhóm C; `docs/analysis/01_DATA_MAPPING.md` §1.
- **Output:** bảng provenance nhúng vào expected output (`_provenance`), mỗi
  aggregate ghi `{value, source_file, source_anchor}`.
- **Touch area:** `tests/fixtures/golden/expected/*.json`; mục mới trong file
  PLAN này.
- **Acceptance:** 100% aggregate ở mức kỳ có `source_anchor` trỏ tới một
  artifact đã commit **trước** `716ae2e1…`. Bảng A.5 tái tạo được từ
  `_provenance` mà không đọc code.
- **Failure condition:** bất kỳ aggregate nào chỉ có nguồn là "output của
  `run_import()` hôm nay" ⇒ **DỪNG**, không đưa vào Golden (đó chính là BR-2).

### GB-2 — Dataset minimization

- **Mục tiêu:** fixture nhỏ nhất vẫn bảo toàn mọi đường nghiệp vụ ở A.15.
- **Input:** hai file thô Owner cấp (OD-GB-1 = A).
- **Output:** quyết định giữ **toàn bộ** 351 + 180 dòng, **không** lấy mẫu.
- **Lý do không lấy mẫu:** I-01 (254/146 đơn) và I-02 (khớp dòng "Tổng cộng")
  là invariant **ở mức toàn kỳ**; lấy mẫu phá cả hai và biến Golden thành một
  fixture khác không so được với evidence. 531 dòng × 17 cột là kích thước
  rất nhỏ với `.xlsx` — không có lý do kỹ thuật để cắt.
- **Touch area:** `tests/fixtures/golden/*.xlsx`.
- **Acceptance:** mỗi fixture đọc ra đúng 351 / 180 `RawRow` và 254 / 146
  `OrderID` duy nhất; kích thước mỗi file `< 1 MB`.
- **Failure condition:** số dòng hoặc số đơn lệch bảng A.5 ⇒ anonymization đã
  làm mất dòng ⇒ dừng, không "điều chỉnh kỳ vọng cho khớp".

### GB-3 — Privacy / anonymization

- **Mục tiêu:** không một byte dữ liệu cá nhân khách hàng nào vào git.
- **Input:** file thô; `PII_FIELD_NAMES`; `governance/product/17_DATA_GOVERNANCE_PRIVACY.md`; DEC-108.
- **Output:** `tests/fixtures/golden/anonymize.py` + hai fixture đã ẩn danh.
- **Quy tắc thay thế** (giữ nguyên quan hệ cần cho mapping/KPI):

  | Cột | Xử lý | Vì sao |
  |---|---|---|
  | `Tên KH` | `"Khách hàng {n}"`, `n` theo **thứ tự xuất hiện đầu tiên** | giữ quan hệ 1-1 khách↔đơn, mất danh tính |
  | `Mã khách hàng` | `"KH{n:05d}"` cùng `n` như trên | giữ tính nhất quán mã↔tên |
  | `Địa chỉ` | `"Địa chỉ {n}"` | — |
  | `ĐT di động` | `"09{n:08d}"` | giữ định dạng, không phải số thật |
  | `Trường mở rộng chi tiết 1` (IMEI) | `None` | không có invariant nào đọc IMEI |
  | `Diễn giải` | `"Bán hàng"` / `"Bán hàng ADS"` theo OD-GB-1/A1 | giữ **sự có/không có** từ khoá ADS cho I-06 |
  | `Giao vận`, `Lương chuyến` | `"Giao vận {k}"`, giữ nguyên số tiền | tên shipper là cá nhân; số tiền chưa đi vào invariant nào nhưng giữ để không đổi cấu trúc |
  | `NVBH` | **GIỮ NGUYÊN** | I-11 phụ thuộc chuỗi raw thật (`"Đức Kiên - Tân Á 0867666533"` phải khớp prefix `"Đức Kiên"`); đây là dữ liệu nhân viên đã có trong `config/employees.yaml` |
  | `Ngày`, `Số BH`, `SL`, `Đơn giá`, `Doanh số bán`, `Chiết khấu`, `Lợi nhuận`, `Tên hàng trên chứng từ` | **GIỮ NGUYÊN** | là chính dữ liệu nghiệp vụ được kiểm |

  `Tên hàng trên chứng từ` giữ nguyên vì `non_product_line_types` (dòng phụ:
  "Chi phí vận chuyển", "Chênh VAT"…) là một đường nghiệp vụ thật đã đo trong
  `evidence.json`; nhưng phải kiểm bằng GB-3 acceptance rằng cột này không
  chứa tên/số điện thoại khách (một số giá trị trong `evidence.json` có dạng
  `"Chi phí giao hộ 65C6K x1"` — mã hàng, không phải PII).
- **Touch area:** `tests/fixtures/golden/anonymize.py`, `*.xlsx`.
- **Acceptance:** quét blob `.xlsx` đã commit — không khớp regex số điện thoại
  Việt Nam ngoài dải `09xxxxxxxx` sinh ra, không xuất hiện chuỗi nào trong
  danh sách tên khách của file gốc, `Trường mở rộng chi tiết 1` rỗng toàn bộ.
  Bản gốc bị xoá và ghi vào mục "Deleted" của PLAN, đúng cách CHECK-101-08 đã
  làm.
- **Failure condition:** bất kỳ giá trị PII nào còn sót ⇒ **KHÔNG COMMIT**,
  không "sửa sau" — git history không revert được (DEC-108).

### GB-4 — Pipeline entry-point lock

- **Mục tiêu:** khoá đúng một ranh giới gọi, để Golden không âm thầm đo một
  đường khác đường production.
- **Input:** `app/pipeline.py`.
- **Output:** Golden gọi **chỉ**
  `run_import(fixture_path, Path("config"))` với provider mặc định
  (`PendingPriceProvider`, `DefaultProductGroupProvider`) — đúng cách
  `tools/analysis/reconcile_real_data.py` đã gọi khi đóng CHECK-101-08.
- **Touch area:** `tests/test_golden_baseline.py`.
- **Acceptance:** test khẳng định chữ ký `run_import` không đổi
  (`inspect.signature`), theo đúng khuôn mẫu CHECK-110-20 đã dùng cho
  `reconcile_conversion` — nếu ai đó đổi chữ ký, Golden báo ngay thay vì
  lặng lẽ đo sai đường.
- **Failure condition:** Golden gọi lại từng module thay vì `run_import()`;
  Golden truyền provider không mặc định mà không ghi lý do vào expected output.

### GB-5 — Business invariant lock

- **Mục tiêu:** mỗi invariant map tới authority đã có (A.10), không tạo bộ
  invariant governance song song.
- **Input:** bảng A.10 (I-01 … I-16).
- **Output:** trong `tests/test_golden_baseline.py`, mỗi invariant là một test
  riêng, docstring ghi authority (`Completion Gate sơ bộ`, `DEC-xxx`,
  `CHECK-xxx`), **không** phát biểu lại luật.
- **Phạm vi phiên này:** I-01 … I-11, I-15, I-16 (kiểm được).
  I-12/I-13/I-14 giữ ở dạng đã có (`grep`-based / unit test hiện hữu), ghi
  OUT-GB-02.
- **Touch area:** `tests/test_golden_baseline.py`.
- **Acceptance:** mỗi test có đúng một authority reference; không invariant nào
  chỉ tồn tại trong Golden mà không có nguồn.
- **Failure condition:** một invariant mới xuất hiện trong Golden mà không map
  được về authority ⇒ đó là scope expansion ⇒ `SCOPE EXPANSION REQUIRED`.

### GB-6 — Deterministic normalization

- **Mục tiêu:** loại nhiễu biểu diễn, **không** loại dữ liệu nghiệp vụ.
- **Input:** bảng D-01 … D-14 (A.12).
- **Output:** hàm serialize dùng chung: `Decimal` → chuỗi; `date` →
  `isoformat()`; `None` giữ nguyên là `None` (**không** thành `0`, giữ
  `03_DATA_MODEL_RULES` §5); `json.dumps(ensure_ascii=False, sort_keys=True,
  indent=2)`; encoding `utf-8` tường minh; `order_graph` **giữ thứ tự**.
- **Ba điều CẤM tuyệt đối** (V4.1 §6 — normalization không được xoá dữ liệu
  nghiệp vụ để test xanh):
  1. **Không** làm tròn / cắt chữ số tiền.
  2. **Không** bỏ trường khỏi expected output vì nó "hay đổi" (đó là cách
     oracle whitelist của TASK-110 đã bị Review #6 falsify).
  3. **Không** thay `None` bằng `0`, không gộp `Pending` vào tổng.
- **Touch area:** `tests/fixtures/golden/build_expected.py`.
- **Acceptance:** chạy `build_expected` **hai lần** trên hai máy/tmpdir/
  `PYTHONHASHSEED` khác nhau ⇒ file bytes **giống hệt** (đã chứng minh khả thi:
  L2 hiện tại cho sha256 `2896e87bc5242b2a` bất biến qua
  `PYTHONHASHSEED ∈ {0,1,12345}`, `TZ`, `LC_ALL`).
- **Failure condition:** hai lần chạy khác nhau ⇒ còn nguồn nondeterminism
  chưa xử lý ⇒ **không** khoá expected output.

### GB-7 — Golden expected-output format

- **Mục tiêu:** machine-diffable, người đọc được, không snapshot khổng lồ.
- **Input:** GB-1, GB-6.
- **Output:** một JSON cho mỗi kỳ, cấu trúc:

```
{
  "_environment": { "python": "3.11.15", "openpyxl": "3.1.5",
                    "pyyaml": "6.0.1",
                    "fixture_filename": "period_2026_01.xlsx",
                    "config_snapshot_id": "17fffad7c6d499cc" },
  "_provenance":  { "<metric>": { "source_file": "...", "source_anchor": "..." } },
  "period": { "label": "01.2026", "date_min": "...", "date_max": "..." },
  "counts": { "sheet_rows": 352, "rows_missing_order_id": 1,
              "raw_rows": 351, "orders": 254,
              "lines_mapped": 351, "lines_unmapped": 0,
              "orders_with_multiple_employee_raw": 0 },
  "money":  { "sales_raw_gross": "...", "discount_total": "...",
              "sales_normalized": "...", "pending_cells": 0 },
  "lead_source": { "split": {"ADS": 254, "PERSONAL": 0},
                   "by_provenance": {"Auto:Employee Default": 254,
                                     "Auto:ADS Rule": 0} },
  "conversion":  { "scheme_distribution": {"ADS_7_5@0.075": 351, ...},
                   "unresolved_lines": 0 },
  "employees":   { "<normalized>": {"orders": n, "lines": n,
                                    "sales_normalized": "..."} },
  "discount_delta": { "lines_differing": 22, "total_delta": "2300000" },
  "review_queue": { "total_items": n, "by_rule": {...}, "by_severity": {...} },
  "order_graph":  { "<order_id>": [source_row, ...] }
}
```

- **Touch area:** `tests/fixtures/golden/expected/*.json`,
  `build_expected.py`.
- **Acceptance:** mỗi file `< 200 KB`; mở bằng mắt đọc được; `counts`,
  `money`, `lead_source` khớp **đúng** bảng A.5; `review_queue` chỉ chứa
  **đếm và phân loại**, **không** chứa nguyên văn `message` (message là
  projection từ provenance — DEC-133 — và thay đổi diễn đạt không phải
  regression nghiệp vụ).
- **Failure condition:** file phình thành dump từng dòng ⇒ diff không đọc được
  ⇒ vi phạm chỉ thị mục 11.

### GB-8 — Golden test design

- **Mục tiêu:** `tests/test_golden_baseline.py` chạy được bằng một lệnh.
- **Input:** GB-4 … GB-7.
- **Output:** bộ test, mỗi test một câu hỏi:

  | Test | Path phủ (A.15) | Invariant |
  |---|---|---|
  | `test_golden_period_row_and_order_counts` | P1 | I-01 |
  | `test_golden_raw_total_matches_source_total_row` | P1 | I-02 |
  | `test_golden_discount_delta_equals_discount_column` | P2 | I-03 |
  | `test_golden_employee_ownership_matrix` | P3 | I-11 |
  | `test_golden_config_snapshot_id_is_pinned` | P3 | I-11 |
  | `test_golden_lead_source_split_and_provenance` | P6 | I-04, I-05, I-06 |
  | `test_golden_scheme_distribution` | P7 | I-07 |
  | `test_golden_unmapped_never_gets_a_rate` | P7 | I-09, I-10 |
  | `test_golden_is_stable_when_a_future_policy_row_is_added` | P8 | I-08 |
  | `test_golden_all_prices_pending` | P15 | (trạng thái hiện tại) |
  | `test_golden_review_queue_shape` | P14 | I-16 |
  | `test_golden_raw_rows_are_immutable_with_provenance` | P1 | I-15 |
  | `test_golden_fixture_filenames_are_pinned` | — | HB-GB-01 |
  | `test_golden_fixture_contains_no_free_text_and_no_imei` | — | HB-GB-03 |
  | `test_golden_expected_output_is_regenerable_byte_identical` | — | GB-6 |

- **Touch area:** `tests/test_golden_baseline.py`, `tests/conftest.py` (fixture
  path).
- **Acceptance:** `python3 -m pytest tests/test_golden_baseline.py -q` PASS;
  `python3 -m pytest -q` vẫn PASS ở mức ≥ 639 + số test mới, **0 regression**.
- **Failure condition:** bất kỳ test nào cần biến môi trường, đường dẫn tuyệt
  đối, hoặc mạng ⇒ không đạt "chạy bằng một lệnh".

### GB-9 — Failure diff / reporting

- **Mục tiêu:** khi FAIL, người đọc biết **con số nghiệp vụ nào** đổi, trong
  vòng vài giây.
- **Input:** GB-7.
- **Output:** helper so sánh đệ quy trả về danh sách
  `"<đường dẫn>: expected=<x> actual=<y>"`, sắp xếp tất định, **cắt ở 20 mục
  đầu** kèm dòng `"… và N khác biệt khác"`.
- **Thứ tự báo cáo bắt buộc:** (1) `_environment` lệch → in cảnh báo
  "có thể do đổi thư viện, không phải đổi nghiệp vụ" **trước**; (2) `counts`;
  (3) `money`; (4) phần còn lại.
- **Touch area:** `tests/test_golden_baseline.py`.
- **Acceptance:** cố tình đổi một giá trị trong expected output ⇒ thông báo
  FAIL nêu **đúng** đường dẫn và cặp giá trị, không phải một dump JSON.
- **Failure condition:** thông báo FAIL là `assert a == b` trên hai dict lớn.

### GB-10 — Regression verification (falsification)

- **Mục tiêu:** chứng minh Golden **có thể FAIL** — nếu không, nó là tautology.
- **Input:** GB-8.
- **Output:** ma trận đột biến, mỗi đột biến áp tạm rồi khôi phục sạch (đúng
  cách CHECK-108A1-14/15 đã làm):

  | Đột biến | Test phải FAIL |
  |---|---|
  | `conversion_rates.yaml`: `PERSONAL_5_5` 0.055 → 0.060 | `test_golden_scheme_distribution` |
  | `conversion_rates.yaml`: `ADS_7_5` 0.075 → 0.080 | `test_golden_scheme_distribution` |
  | `employees.yaml`: `Tín Phát` `default_lead_source: ADS` → `null` | `test_golden_lead_source_split_and_provenance` |
  | `employees.yaml`: đổi `group` của một nhân viên | `test_golden_scheme_distribution` + `test_golden_config_snapshot_id_is_pinned` |
  | `employees.yaml`: xoá một nhân viên | `test_golden_employee_ownership_matrix` |
  | `lead_source.yaml`: thêm từ khoá khớp `Diễn giải` fixture | `test_golden_lead_source_split_and_provenance` |
  | bỏ một dòng khỏi fixture | `test_golden_period_row_and_order_counts` |
  | cộng 1 VND vào một `Đơn giá` trong fixture | `test_golden_raw_total_matches_source_total_row` |
  | không trừ chiết khấu (mô phỏng đảo DEC-114) | `test_golden_discount_delta_equals_discount_column` |
  | thêm dòng chính sách `effective_from: 2027-01-01` | **KHÔNG** test nào FAIL (I-08/DEC-121) |

- **Touch area:** `tests/test_golden_baseline.py` (mục falsification) hoặc mục
  Evidence của PLAN.
- **Acceptance:** mọi đột biến "phải FAIL" đều FAIL; đột biến effective-dating
  **không** FAIL; config khôi phục sạch (`git status --porcelain` rỗng).
- **Failure condition:** một đột biến không làm Golden đỏ ⇒ path đó **chưa**
  được phủ ⇒ **không** được viện dẫn để hạ Blast Radius cho path đó (V4.1 §4.1).

### GB-11 — Governance / ledger update

- **Mục tiêu:** ghi trạng thái, không viết lại luật.
- **Input:** A.17; V4.1 §1.
- **Output:**
  - `PROJECT/REVIEW_BUDGET_LEDGER.md`: thêm root task entry (nguyên văn A.17).
  - `PROJECT/PROJECT_PROGRESS.md`: trạng thái task; **chỉ khi GB-12 đạt đủ**
    mới đổi `V4.1 = POLICY_ADOPTED` → `FULLY_ENFORCED`.
  - `PROJECT/LO_TRINH_DE_HIEU.md`: đồng bộ **cùng một lần sửa** nếu roadmap
    Track A đổi trạng thái (Giao thức Đóng Phiên bước 5).
  - File PLAN này: thêm Completion Gate + Evidence + mục "Deleted" cho file
    thô đã xoá.
- **Touch area:** như trên. **Không** sửa `governance/core/V4_1_POLICY_FREEZE.md`
  (§1 đã mô tả sẵn điều kiện; trạng thái adoption sống ở `PROJECT/PROJECT_PROGRESS.md`).
- **Acceptance:** artifact governance của task = **1**; ledger có `base_sha`/
  `head_sha` nếu (và chỉ nếu) một repair cycle thật sự mở; `PROJECT/PROJECT_PROGRESS.md`
  và `PROJECT/LO_TRINH_DE_HIEU.md` không lệch nhau.
- **Failure condition:** tạo artifact governance thứ 2+ mà không có lý do
  production cụ thể; hoặc đổi `FULLY_ENFORCED` khi GB-12 chưa đủ.

### GB-12 — Exit criteria

`TASK-GOLDEN-BASELINE-001 = DONE` khi **tất cả** đúng:

1. `tests/fixtures/golden/` có fixture cho cả hai kỳ, đã ẩn danh, GB-3
   acceptance PASS.
2. `tests/fixtures/golden/expected/` có expected output cho cả hai kỳ, sinh
   lại byte-identical (GB-6).
3. `python3 -m pytest tests/test_golden_baseline.py -q` **PASS**.
4. `python3 -m pytest -q` **PASS**, 0 regression so với `639 passed, 9 skipped`.
5. Ma trận falsification GB-10 đầy đủ, mọi đột biến "phải FAIL" đều FAIL, config
   khôi phục sạch.
6. Mỗi aggregate có `_provenance` trỏ artifact commit trước `716ae2e1…` (GB-1).
7. Mỗi invariant map tới authority đã tồn tại (GB-5); không có invariant mới
   không nguồn.
8. Ledger cập nhật (GB-11); artifact governance của task ≤ 4 (hiện 1).
9. `CHECK-110-16` vẫn `BLOCKED`, `Gate Class` vẫn
   `POST_MERGE_PRODUCTION_ACCEPTANCE`, `TASK-110` vẫn `NOT DONE` — **không**
   đụng tới.
10. `R1-A1` vẫn `FROZEN`; `R1-A2` → `R8` vẫn `OWNER_EXTENSION REQUIRED`;
    `tests/fixtures/baseline/**` và `tests/test_task110_non_regression.py`
    **không đổi một byte**.
11. `git diff <baseline>..<head> --name-only` **không** chứa `app/**` hay
    `config/**`.

Chỉ khi 1–11 đạt, `V4.1` mới được chuyển `POLICY_ADOPTED` → `FULLY_ENFORCED`
(V4.1 §1 — task này là task **duy nhất** được phép làm việc đó).

---

## PHẦN D — ĐIỀU KIỆN CHÍNH XÁC ĐỂ IMPLEMENTATION ĐƯỢC PHÉP BẮT ĐẦU

Cả bốn điều kiện phải đúng:

1. **Owner trả lời OD-GB-1** (A + quyết định phụ A1/A2, hoặc B kèm chấp nhận
   tường minh việc hạ cấp xuống HARDENING, hoặc C).
2. **Nếu OD-GB-1 = A:** hai file thô có mặt trong môi trường phiên
   implementation tại `data/samples/`.
3. **Owner phê duyệt Review Budget** ở A.17 (`HIGH`, 2 cycle — hoặc đặt thấp
   hơn).
4. **Branch authority PASS** tại thời điểm mở phiên implementation:
   `scripts/branch_authority_check.sh` → `AUTHORITY_OK` +
   `DIVERGENCE: WITHIN_LIMITS`, HEAD có `716ae2e1…` là ancestor.

**Không** cần Owner Extension: `TASK-GOLDEN-BASELINE-001` là root task lineage
**mới**, không thuộc lineage `TASK-110`, nên ngân sách `EXHAUSTED_PRE_V4.1`
của `TASK-110` không áp vào đây. Nó cũng **không** mở `R1-A2` → `R8`.

---

## PHẦN E — IMPLEMENTATION RECORD (2026-08-27)

```
Owner Decision   : OD-GB-1 = A + A1
Plan commit      : b738fa4
Implementation   : GB-1 … GB-12 thực hiện đủ, một lượt, không mở subtask
Trạng thái       : IMPLEMENTATION = READY_FOR_INDEPENDENT_REVIEW
                   (chưa Independent Review, chưa FROZEN, chưa DONE)
```

### E.1 First Gate — xác minh workbook gốc (GB-1)

Hai workbook production do Owner đính kèm session, **không** nằm trong repo.

| | 01.2026 | 06.2026 |
|---|---|---|
| SHA256 đo được | `4e29747e…b78308` | `ef9a85e0…a0fdaa` |
| SHA256 Owner khai | `4e29747e…b78308` | `ef9a85e0…a0fdaa` |
| Kết quả | **KHỚP** | **KHỚP** |
| Dòng tiêu đề sheet | `Nhân viên: Tín Phát 0869931931, Tháng 1` | `… Tháng 6` |

Chạy `app.pipeline.run_import()` — production thật, không mô phỏng — trên
**bản gốc**, trước khi ẩn danh:

| Chỉ số | 01.2026 | Tài liệu | 06.2026 | Tài liệu |
|---|---:|---:|---:|---:|
| Dòng sheet (kể cả `Tổng cộng`) | 352 | 352 | 181 | 181 |
| Dòng thiếu OrderID | 1 | 1 | 1 | 1 |
| RawRow | 351 | 351 | 180 | 180 |
| **OrderID duy nhất** | **254** | **254** | **146** | **146** |
| SL (footer ERP) | 407 | 407 | 210 | 210 |
| Doanh số bán raw | 3.564.610.000 | 3.564.610.000 | 1.925.272.000 | 1.925.272.000 |
| Chiết khấu | 2.300.000 | 2.300.000 | 400.000 | 400.000 |
| Doanh số normalized | 3.562.310.000 | 3.562.310.000 | 1.924.872.000 | 1.924.872.000 |
| Lợi nhuận ERP | 240.032.781 | 240.033k | 95.956.942 | 95.957k |
| mapped / unmapped | 351 / 0 | 351 / 0 | 180 / 0 | 180 / 0 |
| Đơn có >1 employee_raw | 0 | 0 | 0 | 0 |
| ADS / PERSONAL | 254 / 0 | 254 / 0 | 146 / 0 | 146 / 0 |
| ADS qua `Auto:Employee Default` | 254 | 254 | 146 | 146 |
| ADS qua từ khoá | 0 | 0 | 0 | 0 |
| Dòng raw ≠ normalized | 22 | 22 | 1 | 1 |
| Tổng lệch (= tổng chiết khấu) | 2.300.000 | 2.300.000 | 400.000 | 400.000 |

**Không có SOURCE BASELINE MISMATCH.** `254`/`146` được chứng minh bằng
pipeline chạy trên file thật + evidence đã commit, **không** lấy từ prompt.
`407`/`210` được xử lý đúng là **tổng số lượng hàng**, không phải số đơn.

Ba con số đo lần đầu trên dataset này, chưa từng có mốc lịch sử: `41`/`30`
review item, `26`/`17` dòng có lợi nhuận ERP âm, `22`/`14` dòng phụ.

### E.2 Minimize → Anonymize (GB-2, GB-3)

**MINIMIZE trước.** Một trường chỉ được giữ nếu có đường code đọc nó:

| Trường | Đường code đọc | Quyết định |
|---|---|---|
| `note_raw` | `LeadSourceClassifier._note_matches_ads()` | **A1 label** |
| `product_raw` | `rules.is_non_product_line()` → `matches_any()`; `ProductGroupProvider` | giữ nguyên văn |
| `employee_raw` | `EmployeeMapper.resolve()` khớp prefix trên chuỗi **thô** | giữ nguyên văn |
| `Ngày`/`Số BH`/`SL`/`Đơn giá`/`Doanh số`/`Chiết khấu`/`Lương chuyến`/`Lợi nhuận` | pipeline tính tiền | giữ nguyên văn |
| `customer`, `customer_code` | **không rule nào đọc** | surrogate |
| `address`, `phone`, `shipper_raw`, `imei` | **không rule nào đọc** | **XOÁ HẲN** |

`address`/`phone`/`shipper_raw`/`imei` bị xoá chứ không thay surrogate: giữ
surrogate cho trường không ai đọc chỉ làm phình fixture.
`customer`/`customer_code` giữ surrogate vì hai lý do đo được — bảo toàn lực
lượng, và bảo toàn quan hệ **không** 1-1 giữa mã và tên (01.2026: 227/227;
06.2026: **135 tên / 133 mã**).

`Diễn giải` theo **A1**: nhãn tính bằng **chính** `LeadSourceClassifier`
production, không bằng một bản viết lại.

```
normalize rỗng      -> ""          (giữ nguyên trạng thái "trống")
có chứa từ khoá ADS -> "ADS"
còn lại             -> "BAN_HANG"
```

Số dòng chứa "ADS": **0/351** và **0/180** — khớp `ads_keyword_cell_hits` = 0
trong `docs/analysis/_evidence/evidence.json` và DEC-109. Hệ quả trung thực:
Golden **không** phủ nhánh ADS-qua-từ-khoá vì dữ liệu thật không có dòng nào
đi qua nhánh đó. **Không** bịa thêm một dòng ADS vào fixture.

**Vì sao giữ cả 351 + 180 dòng thay vì lấy mẫu.** Ba invariant mạnh nhất đều
là aggregate **toàn kỳ**, và lấy mẫu phá cả ba:

1. `I-01` là một phép đếm trên toàn kỳ — lấy mẫu ⇒ không còn 254/146 ⇒ mất
   luôn khả năng đối chiếu với CHECK-101-08 và `evidence.json`.
2. `I-02` đòi dòng `Tổng cộng` của ERP bằng tổng mọi dòng dữ liệu — đây là
   **oracle độc lập với engine duy nhất** tồn tại; lấy mẫu là phá nó.
3. `I-03` ở kỳ 06.2026 chỉ có **1/180** dòng lệch — gần như chắc chắn biến
   mất trong bất kỳ phép lấy mẫu nào.

Chi phí giữ toàn bộ: 31 KB + 19 KB.

**Đo được — ẩn danh KHÔNG dịch chuyển nghiệp vụ.** Chạy pipeline trên bản gốc
và trên fixture rồi so structural (`dataclasses.fields()`, không phải danh
sách trắng):

```
01.2026 / 06.2026
  orders              254 vs 254 · 146 vs 146      SAME
  lines               351 vs 351 · 180 vs 180      SAME
  order_graph                                       IDENTICAL
  Order  — mọi trường trừ `lines`                   IDENTICAL
  WorkingLine — 27/34 trường (trừ trường đã tuyên bố) IDENTICAL
  RawRow      — 12/21 trường (trừ trường đã tuyên bố) IDENTICAL
  Review Queue — category/severity/scope/order/tập dòng IDENTICAL (41·30)
  preview                                           IDENTICAL
```

Đây là `test_golden_anonymization_preserves_business_output`, chạy được khi
Owner cấp lại file thô qua `GOLDEN_RAW_01`/`GOLDEN_RAW_06`, tự SKIP khi
không có. Nó là bằng chứng **E1** của phiên tạo fixture, không phải cổng CI.

### E.3 Golden Coverage Map (GB-8) — theo data path P1…P15

**Bản đồ này là ỨNG VIÊN, chưa có hiệu lực.**
`governance/core/V4_1_POLICY_FREEZE.md` §4.1 cấm dùng Golden test để hạ Blast
Radius cho tới khi `TASK-GOLDEN-BASELINE-001` **hoàn tất**. Task đang ở
`READY_FOR_INDEPENDENT_REVIEW`, chưa `DONE`. Vì vậy **hiện tại không path nào
được hạ một bậc** — cột cuối ghi mức sẽ áp dụng *sau khi* Independent Review
PASS và Owner freeze.

| Path | Golden test có tên | Trạng thái | BR hiện tại | BR sau freeze |
|---|---|---|---|---|
| P1 Raw ingestion | `test_golden_period_row_and_order_counts`, `test_golden_raw_total_matches_source_total_row`, `test_golden_order_graph_preserves_membership_and_order` | **COVERED** | HIGH | MEDIUM |
| P2 Normalization / chiết khấu | `test_golden_discount_delta_equals_discount_column` | **COVERED** | HIGH | MEDIUM |
| P3 Employee identity | `test_golden_employee_ownership_matrix`, `test_golden_config_snapshot_id_is_pinned` | **COVERED** | HIGH | MEDIUM |
| P4 Sealing / immutability | — | **NOT COVERED** | HIGH | **HIGH** |
| P5 Annotation validation | — | **NOT COVERED** | HIGH | **HIGH** |
| P6 LeadSource | `test_golden_lead_source_split_and_provenance`, `test_golden_lead_source_is_decided_at_order_level`, `test_golden_note_label_is_functional_not_decorative` | **COVERED** | HIGH | MEDIUM |
| P7 Conversion — nhánh resolved | `test_golden_scheme_distribution` | **COVERED** | HIGH | MEDIUM |
| P7′ Conversion — nhánh unmapped | `test_golden_unmapped_never_borrows_a_rate` | **PARTIAL — VACUOUS** (0 dòng unmapped ở cả hai kỳ) | HIGH | **HIGH** |
| P8 Effective dating | `test_golden_is_stable_when_a_future_policy_row_is_added` | **COVERED** | HIGH | MEDIUM |
| P9 Accounting profit | `test_golden_all_prices_pending` | **PARTIAL** — chỉ chốt trạng thái `Pending`, chưa phủ phép tính trên giá nhập thật | HIGH | **HIGH** |
| P10 KPI / Adjustment | — | **NOT COVERED** — module chưa tồn tại | HIGH | **HIGH** |
| P11 Converted Revenue totals | — | **NOT COVERED** — TASK-108B BLOCKED bởi C15 | HIGH | **HIGH** |
| P12 Summary aggregation | — | **NOT COVERED** — TASK-109 chưa tồn tại | HIGH | **HIGH** |
| P13 Export `.xlsx` | — | **NOT COVERED** — TASK-111 chưa tồn tại | HIGH | **HIGH** |
| P14 Validation / Review Queue | `test_golden_review_queue_shape`, `test_golden_validation_never_blocks_the_import` | **COVERED** | MEDIUM | LOW |
| P15 Pricing | `test_golden_all_prices_pending` | state-locked | LOW hôm nay | LOW |

**P4 và P5 không bao giờ được Golden hạ risk.** Golden so output cuối, nên nó
mù với mutation xảy ra giữa chừng rồi bị ghi đè, và mù với việc lớp
enforcement bị vô hiệu hoá. Ranh giới này đã ghi ở §A.15 và không đổi vì
Golden đã PASS.

`lines_digest` bù đúng chỗ aggregate mù: hoán đổi giá của hai dòng trong cùng
một đơn không đổi bất kỳ tổng nào, kể cả tổng của chính đơn đó.

### E.4 Falsification (GB-10) — chứng minh Golden CÓ THỂ đỏ

| Đột biến (áp trên bản copy config trong `tmp_path`, repo không đổi) | Kết quả |
|---|---|
| `ADS_7_5` 7,5 % → 8,0 % | Golden **đỏ** ở cả hai kỳ |
| Tín Phát mất `default_lead_source: ADS` | Golden **đỏ** ở cả hai kỳ |
| Xoá Tín Phát khỏi master data | Golden **đỏ** ở cả hai kỳ |
| Thêm `"BAN_HANG"` vào `ads_keywords` | provenance chuyển `Auto:Employee Default` → `Auto:ADS Rule` cho **đúng** những đơn có `Diễn giải` không rỗng ⇒ chứng minh nhãn A1 **thật sự được đọc**, không phải trang trí |
| Thêm dòng chính sách `effective_from: 2027-01-01` | **KHÔNG** test nào đỏ — đúng DEC-121 |
| Đổi một giá trị trong expected output | `format_diff` nêu đúng `counts.orders: expected=254 actual=253` |

### E.5 Determinism (GB-6)

Chạy trong **tiến trình con thật** (`PYTHONHASHSEED` chỉ có hiệu lực lúc
interpreter khởi động, nên `monkeypatch` trong cùng tiến trình không chứng
minh được gì):

```
PYTHONHASHSEED = 0 · 1 · 12345 · 7
TZ             = (mặc định) · Pacific/Kiritimati · UTC
LC_ALL         = (mặc định) · C · C.UTF-8
cwd            = repo root · thư mục tạm khác
=> 1 digest duy nhất qua 5 môi trường + 1 cwd khác
=> sinh lại expected output cho ra ĐÚNG TỪNG BYTE file đã commit
```

`RawRow.source_file` (HB-GB-01) được xử lý ở **biên fixture/test**, không sửa
production: tên file được chốt cứng ở `_environment.fixture_filename` và
`test_golden_fixture_filenames_are_pinned`, đồng thời bị loại khỏi
`lines_digest` để một lần đổi tên không làm vỡ Golden ở chỗ khó hiểu.

Version `python`/`openpyxl`/`pyyaml` được ghi vào `_environment` nhưng **chỉ
cảnh báo**, không so cứng (HB-GB-02): bắt cứng chúng khiến mọi lần nâng cấp
thư viện làm Golden đỏ, và cách "sửa" hiển nhiên nhất khi đó là sinh lại
expected output — tức là xoá chính bằng chứng.

### E.6 Privacy verification (§21)

Quét **chính blob đã commit** (giải nén toàn bộ XML trong `.xlsx`, kể cả
sharedStrings; đọc toàn văn `.json`), đối chiếu với **tập giá trị thật** lấy
từ workbook gốc:

```
4 artifact × 7 lớp giá trị thật + pattern số điện thoại
  period_2026_01.xlsx (31.417 B) · period_2026_01.json (122.653 B)
  period_2026_06.xlsx (19.230 B) · period_2026_06.json  (73.727 B)
=> 0 hit trên: customer · customer_code · address · phone · imei · shipper · Diễn giải
=> 0 chuỗi giống số điện thoại
```

Ngoại lệ **có tên** duy nhất: `0869931931` — số của chính Tín Phát trong dòng
tiêu đề sheet và cột `NVBH`. Đây là master data nhân viên đã có sẵn trong
`config/employees.yaml` và `tests/fixtures/baseline/` từ trước, không phải PII
khách hàng. Ngoại lệ được khai báo tường minh trong
`test_golden_fixture_contains_no_customer_pii`, không phải một lỗ hổng của
phép quét.

Bảng ánh xạ ngược (surrogate → giá trị thật) chỉ tồn tại trong bộ nhớ của lần
chạy `anonymize.py` và **không bao giờ** được ghi ra đĩa.

`git ls-files | grep -i xlsx` chỉ trả về hai fixture đã ẩn danh. Hai workbook
gốc nằm ở thư mục attachment của session, ngoài repository, và không bao giờ
được `git add`.

### E.7 36 verified / 19 limitation (§8)

**OUT OF GOLDEN SCOPE.** 55 ô cột F của `Summary 2026` thuộc
`Báo cáo Kinh doanh 2026.xlsx` — một workbook **khác**, không nằm trong repo,
và không phải dataset của Golden này. Golden không đưa ra bất kỳ claim nào về
55 ô đó.

Phân biệt lịch sử được bảo toàn nguyên trạng và **không** bị bóp méo:
CHECK-108A1-14 ghi **36 ô đối chiếu độc lập được, 0 lệch**, và **19 ô
LIMITATION** không đủ độc lập để xác minh (Nội thành 8 · Gia dụng 8 ·
Fanpage 2 · Linh 1). Không ở đâu trong artifact của task này xuất hiện claim
"55/55 đúng". 19 ô limitation **không** được chuyển thành PASS.

### E.8 Dataset separation (§6)

`_provenance.dataset_scope` của mỗi expected output ghi thẳng vào file, và
`test_golden_provenance_records_the_real_source_workbook` khẳng định nó:

```
Tín Phát, một kỳ, xuất riêng theo tháng.
KHÔNG phải dataset 11.765 dòng của evidence.json.
KHÔNG phải dataset 14.389 dòng của CHECK-108A1-15.
KHÔNG phải dataset của CHECK-110-16.
```

Không invariant nào trong `tests/test_golden_baseline.py` mượn con số của ba
dataset kia. Các con số `review_queue` (41/30) được khai báo tường minh là
**đo lần đầu trên dataset này**, có anchor provenance nói đúng như vậy thay vì
giả vờ có mốc lịch sử.

### E.9 CHECK-110-16 — KHÔNG ĐỔI

```
CHECK-110-16
Priority   : REQUIRED
Status     : BLOCKED
Gate Class : POST_MERGE_PRODUCTION_ACCEPTANCE   (DEC-141)
TASK-110   : NOT DONE
```

Golden của hai kỳ Tín Phát **không** thay thế dataset của `CHECK-110-16`
(toàn công ty, 6 tháng, 11.765 dòng). Không synthetic PASS, không bypass,
không đổi gate. Lý do đầy đủ ở §A.20.

### E.10 Regression (GB-10, §20)

| Bộ | Baseline `716ae2e1…` | Sau implementation |
|---|---|---|
| `pytest -q` toàn bộ | 639 passed, 9 skipped | **691 passed, 11 skipped** |
| `tests/test_golden_baseline.py` | (chưa tồn tại) | **52 passed, 2 skipped** |
| … cùng `GOLDEN_RAW_01`/`GOLDEN_RAW_06` | — | **54 passed, 0 skipped** |
| TASK-110 non-regression L1/L2/L3 | 10 passed | **10 passed** |
| TASK-108A conversion + resolver + reconcile | 65 passed | **65 passed** |
| R1 / R1-A / R1-A1 + oracle mutation | 301 passed, 9 skipped | **301 passed, 9 skipped** |
| `validate_evidence.py` | PASS (88 record) | **PASS (88 record)** |
| `validate_project_state.py` | PASS | **PASS** |
| `validate_structure.py` | PASS (21 path) | **PASS (21 path)** |
| `validate_task_completion.py` | PASS (6 DONE task) | **PASS (6 DONE task)** |
| `validate_reference_integrity.py` | **FAIL — 3 reference** (TASK-REM-T06) | **FAIL — 3 reference** (cùng 3) |
| `scripts/branch_authority_check.sh` | AUTHORITY_OK | **AUTHORITY_OK** |

**0 regression.** `+52` test mới, `+2` skip mới (đúng hai test tương đương
ẩn danh, tự SKIP khi không có file thô).

`validate_reference_integrity.py` đỏ **từ trước** ở baseline với đúng 3
reference của `docs/tasks/TASK-REM-T06-repository-root-hygiene.md`
(README, CODE_OF_CONDUCT, CONTRIBUTING ở gốc repo) — artifact lịch sử,
ngoài scope, không sửa. Phiên Discovery `b738fa4` đã **thêm 8 reference trần**
trong chính file PLAN này; 8 cái đó đã được sửa thành đường dẫn đầy đủ trong
phiên này, đưa validator về đúng trạng thái baseline.

### E.11 Files changed

```
A  tests/fixtures/golden/__init__.py
A  tests/fixtures/golden/anonymize.py
A  tests/fixtures/golden/build_expected.py
A  tests/fixtures/golden/period_2026_01.xlsx          (fixture đã ẩn danh)
A  tests/fixtures/golden/period_2026_06.xlsx          (fixture đã ẩn danh)
A  tests/fixtures/golden/expected/period_2026_01.json
A  tests/fixtures/golden/expected/period_2026_06.json
A  tests/test_golden_baseline.py
M  PROJECT/REVIEW_BUDGET_LEDGER.md                    (root task entry)
M  PROJECT/PROJECT_PROGRESS.md                        (trạng thái)
M  PROJECT/LO_TRINH_DE_HIEU.md                        (đồng bộ bắt buộc)
M  docs/tasks/TASK-GOLDEN-BASELINE-001-PLAN.md        (Phần E + sửa 8 reference trần)
```

**`app/**` và `config/**` không đổi một byte.** Không sửa business logic.
Artifact governance của task vẫn là **1** (chính file này) — không tạo
REPAIR-MODE / FROZEN-CONTRACT / RECONCILIATION-PLAN / FINALIZATION-PLAN.

### E.12 Findings

**BLOCKING: KHÔNG CÓ.** Không phát hiện defect production nào trong phiên
này. Pipeline tái hiện đúng mọi con số nghiệp vụ đã được xác minh trên dữ
liệu thật.

**HARDENING:**

- **HB-GB-01** (từ Discovery) — `RawRow.source_file = path.name`. **ĐÃ XỬ LÝ
  ở biên fixture/test**, không sửa production: tên file chốt ở
  `_environment.fixture_filename` + `test_golden_fixture_filenames_are_pinned`,
  và bị loại khỏi `lines_digest`.
  *RE-TRIGGER:* có đề xuất đổi tên/di chuyển file trong `tests/fixtures/golden/`.
- **HB-GB-02** (từ Discovery) — `pyproject.toml` không pin version
  (`openpyxl>=3.1`, `PyYAML>=6.0`, `requires-python >=3.11`). **ĐÃ GIẢM NHẸ**:
  version ghi vào `_environment`, và `format_diff` in cảnh báo môi trường
  **trước** diff nghiệp vụ. Chưa pin — pin là thay đổi `pyproject.toml`, nằm
  ngoài touch-area của task này.
  *RE-TRIGGER:* Golden đỏ trong khi `git diff` trên `app/` và `config/` rỗng.
- **HB-GB-03** (từ Discovery) — `PII_FIELD_NAMES` không bao gồm `note_raw`
  và `imei`. **ĐÃ XỬ LÝ cho fixture**: cả hai bị xoá/thay nhãn, và
  `test_golden_fixture_contains_no_customer_pii` quét chính blob `.xlsx` đã
  commit chứ không dựa vào `PII_FIELD_NAMES`. Bản thân hằng số trong
  `app/modules/validation/models.py` **không đổi** (Scope Lock).
  *RE-TRIGGER:* bất kỳ fixture nào khác dựng từ dữ liệu production thật.
- **HB-GB-04** (từ Discovery) — `sort_keys=True` che thứ tự có nghĩa. **ĐÃ XỬ
  LÝ**: `order_graph` và `orders_detail` là **list**, giữ thứ tự, và
  `test_golden_order_graph_preserves_membership_and_order` khẳng định nó.
- **HB-GB-05** (mới) — `test_golden_unmapped_never_borrows_a_rate` là
  **vacuous** trên dataset này (0 dòng unmapped ở cả hai kỳ). Nhánh unmapped
  của P7 vì vậy **không** được Golden phủ thật; nó do
  `tests/test_conversion_engine.py::test_unmapped_employee_line_never_receives_a_rate`
  phủ trên fixture tổng hợp.
  *RE-TRIGGER:* khi Golden mở rộng sang một kỳ có nhân viên ngoài master data
  (ví dụ dataset toàn công ty, nơi đã đo 107 dòng unmapped).
- **HB-GB-06** (mới) — Golden **không** phủ nhánh ADS-qua-từ-khoá, vì dữ liệu
  thật của hai kỳ có 0 dòng chứa "ADS". Đây là sự thật nghiệp vụ, không phải
  thiếu sót của fixture, và **không** được sửa bằng cách bịa một dòng ADS.
  *RE-TRIGGER:* khi một kỳ tương lai xuất hiện dòng chứa từ khoá ADS —
  `test_golden_lead_source_split_and_provenance` sẽ đỏ và đó là tín hiệu đúng.

**OUT_OF_SCOPE:**

- **OUT-GB-01** — `CHECK-110-16` vẫn BLOCKED; cần dataset 11.765 dòng. Không
  thuộc contract task này.
- **OUT-GB-02** — `I-12` (không `/2` trong tổng hợp) và `I-14`
  (`Total == Personal + Ads`) chưa kiểm được end-to-end: `summary_engine`
  (TASK-109) và Converted Revenue (TASK-108B, BLOCKED bởi C15) chưa tồn tại.
- **OUT-GB-03** — `P9` chỉ phủ được trạng thái `Pending`; chưa có Price Master.
- **OUT-GB-04** — 3 reference trần (tới README, CODE_OF_CONDUCT và
  CONTRIBUTING ở gốc repo, cả ba không tồn tại) của
  `docs/tasks/TASK-REM-T06-repository-root-hygiene.md` làm `validate_reference_integrity.py` đỏ **từ trước** baseline. Artifact
  lịch sử, không retrofit (V4.1 §10).
- **OUT-GB-05** — 55 ô cột F của `Summary 2026`: OUT OF GOLDEN SCOPE (§E.7).

### E.13 Trạng thái sau phiên này

```
TASK-GOLDEN-BASELINE-001
    IMPLEMENTATION = READY_FOR_INDEPENDENT_REVIEW
    repair_cycles_used = 0 · remaining = 2

Governance V4.1
    = POLICY_ADOPTED
    = Golden implementation candidate EXISTS
    = NOT YET FULLY_ENFORCED  (chờ Independent Review + freeze)

TASK-110      = NOT DONE
CHECK-110-16  = REQUIRED · BLOCKED · POST_MERGE_PRODUCTION_ACCEPTANCE
R1-A1         = FROZEN     (không đụng)
R1-A2 → R8    = OWNER_EXTENSION REQUIRED (không mở)
```

`V4.1` **chưa** chuyển `FULLY_ENFORCED`: §1 của overlay đòi Golden test PASS,
điều đó đã đạt, nhưng chuyển trạng thái là hành động của một phiên có thẩm
quyền sau Independent Review (`governance/core/V4_1_POLICY_FREEZE.md` §12 — `FROZEN` thuộc
authorized Freeze Finalization session, `DONE` thuộc Owner/completion
authority). Implementation agent **không** tự chuyển.

### F. Cập nhật hiện trạng (append, 2026-08-27) — Phần E.13 ở trên SUPERSEDED

Phần E.13 phía trên là **bản ghi lịch sử** tại thời điểm implementation vừa
xong (`repair_cycles_used = 0`). Từ đó tới nay đã xảy ra thêm hai việc, không
sửa lại nội dung E.13:

1. **Repair Cycle #1** (`GB-IR-01`, commit `54a575d`, ghi tại
   `PROJECT/REVIEW_BUDGET_LEDGER.md`): `repair_cycles_used = 1`,
   `remaining = 1`.
2. **Independent Review #2 — PASS** (2026-08-27, phiên "VERDICT RECORDING
   ONLY", verdict do Owner cung cấp từ review chạy ngoài canonical repo):
   reviewed SHA `85210691702550d83c0fd42fe816be8ca9dde889`, `BLOCKING = 0`,
   `GB-IR-01 = CLOSED_BY_REPAIR, INDEPENDENTLY_VERIFIED`. Ghi đầy đủ tại
   `docs/reviews/TASK-GOLDEN-BASELINE-001-INDEPENDENT-REVIEW-2.md`.

Trạng thái hiện tại (current-state pointer, thay cho phần tương ứng của
E.13):

```
TASK-GOLDEN-BASELINE-001
    IMPLEMENTATION       = COMPLETE
    INDEPENDENT_REVIEW_2 = PASS — ELIGIBLE_FOR_FREEZE
    reviewed_sha          : 85210691702550d83c0fd42fe816be8ca9dde889
    repair_cycles_used = 1 · remaining = 1 (UNUSED)
    FROZEN = NO · DONE = NO · MERGED = NO

Governance V4.1
    = POLICY_ADOPTED
    = NOT YET FULLY_ENFORCED  (chờ Freeze Finalization + Integration)

TASK-110      = NOT DONE            (không đổi)
CHECK-110-16  = REQUIRED · BLOCKED · POST_MERGE_PRODUCTION_ACCEPTANCE (không đổi)
R1-A1         = FROZEN     (không đụng)
R1-A2 → R8    = OWNER_EXTENSION REQUIRED (không mở)
```

Next authorized action: **FREEZE FINALIZATION + INTEGRATION** (phiên riêng,
có thẩm quyền riêng). Phiên recording này không tự mở phiên đó.
