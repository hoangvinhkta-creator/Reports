# S117 — PHB-06: Báo Cáo Theo Thương Hiệu

Mode: BOUNDED VERTICAL — một nhánh, một `BASE_HEAD`, không merge canonical,
không deploy.

Không mở lại vertical đã đóng · không migration mới · không thẩm quyền
Product Identity mới · không thẩm quyền giá nhập mới · không Target thương
hiệu · không đổi điều hướng chính · không mở F-04/F-05 · không Advanced
Analytics.

## 0. Exact Gate

```text
CANONICAL_BRANCH      = claude/extract-upload-repo-gq2ws4
EXPECTED_HEAD         = 0d9d93111c7955fa407e5b43ebee682e5c728c56
OBSERVED origin HEAD  = 0d9d93111c7955fa407e5b43ebee682e5c728c56  → KHỚP
WORKTREE              = sạch
FEATURE_BRANCH        = claude/phb-06-brand-reporting-0i2oun (tách từ đúng head trên)
GATE                  = PASS
```

Ghi chú vận hành: bản sao cục bộ của nhánh canonical trong container này lệch
khỏi origin (131 commit cục bộ của một phiên trước, chưa từng được đẩy lên).
`origin/claude/extract-upload-repo-gq2ws4` mới là bản ghi chính thống
(`CLAUDE.md` § Đồng Bộ Nhánh), nên nhánh cục bộ được `reset --hard` về đúng
origin trước khi tách nhánh tính năng. Không commit nào của origin bị mất.

## 1. Audit thẩm quyền thương hiệu — kết quả ĐO ĐƯỢC

| Nguồn | Trường/ngữ nghĩa | Thẩm quyền | Hiện hành/Legacy | Tái dụng được? |
|---|---|---|---|---|
| `CanonicalProductIdentity` | `namespace`, `source_product_code` | Product Identity (canonical) | Hiện hành | Có — nhưng KHÔNG mang thương hiệu |
| `TrackingCatalogRow` (`board`) | `tracking_code`, `present_in_board`, `name`, `alt[]` | Tracking (chỉ đọc) | Hiện hành | Không có thương hiệu |
| `TrackingInvMapSnapshot` (`inv.map`) | khoá câu tên hàng → mã \| `"-"` | Tracking (người duyệt) | Hiện hành | Không có thương hiệu |
| `PublicPurchaseIdentityRow` | `product_code`, `product_name`, `aliases`, `active_from/to` | Public Purchase | Hiện hành | Không có thương hiệu |
| `order_line_result_version` | 38 cột kết quả pipeline | Engine | Hiện hành | Không có cột thương hiệu |
| `legacy_summary_row` / `legacy_daily_sales` / `legacy_monthly_reference` | tổng theo người bán/ngày/tháng | LEGACY_HISTORY | Legacy | Không có thương hiệu |
| Route/trang thương hiệu có sẵn | — | — | — | KHÔNG TỒN TẠI (`/thuong-hieu`, `/brand`, `/hang` đều không có) |

Kết luận đo được: **không nguồn nào trong hệ thống mang thương hiệu.**

Kết luận này TRÙNG với một freeze đã có, không phải một phát hiện mới:
`docs/tasks/TASK-PRA-005-san-pham.md` §19 ghi
`BRAND = NOT_AVAILABLE (không cột nào ở bất kỳ bảng nào)`, freeze `DEFERRED`,
kèm câu *"KHÔNG suy luận từ tên sản phẩm. KHÔNG mở một dự án phân loại."*
`tests/test_web_product_view.py` còn canh chủ động rằng chữ `Brand` không
xuất hiện như một cột trên `/san-pham`.

## 2. Điều đã ship

| Tệp | Vai trò |
|---|---|
| `app/modules/reporting/brand_metrics.py` | Tầng gộp THUẦN: `BrandBucket`, `group_by_brand` (phân hoạch), `reconciliation` |
| `app/web/brand_identity.py` | Cửa DUY NHẤT đọc thương hiệu từ hợp đồng Product Identity + `BrandCoverage` |
| `app/web/identity_gateway.py` | `+ confirmed_identities()` — chỉ đọc, cùng đường/cùng bộ lọc với `confirmed_keys()` |
| `app/web/business_presentation.py` | `+ BRAND_COLUMNS`, `brand_rows`, `brand_summary`, các chú thích |
| `app/web/server.py` | `+ GET /kinh-doanh/thuong-hieu` (`business_brand`) |
| `app/web/templates/kinh_doanh_thuong_hieu.html` | Trang, CHỈ ĐỌC |
| `app/web/templates/kinh_doanh.html` | Một đường dẫn từ Báo cáo sang khung nhìn con |
| `tests/test_phb06_brand_reporting.py` | 42 test: thẩm quyền · phân hoạch · vertical · trang · 8 mutation probe |

Trên dữ liệu hôm nay trang hiện ĐÚNG hai dòng — cả hai là "chưa xác định
thương hiệu", tách theo hai nguyên nhân — và nói ra bằng chữ rằng danh tính
sản phẩm hiện hành không mang thương hiệu. Tổng vẫn đối soát tuyệt đối về
tổng kỳ: tiền không mất đi đâu, nó chỉ chưa tách được theo thương hiệu.

## 3. Vì sao KHÔNG dựng một bảng thương hiệu trông như thật

Bốn đường duy nhất có thể cho ra một bảng có dòng, và cả bốn đều bị cấm:

1. suy từ `product_raw` / mã máy / so chuỗi con — `PHB-06 §2`/`BR-02` và
   `PRA-005` §19 cấm tường minh;
2. một bảng ánh xạ thương hiệu của riêng Reports — `§3`/`BR-10` cấm;
3. một cột `brand` mới trên schema — `§18`/`BR-13` yêu cầu DỪNG trước
   migration; và một cột rỗng không sinh ra dữ liệu;
4. một trường thương hiệu mới ở Tracking — nằm ngoài thẩm quyền của Reports
   (Tracking = READ-ONLY REFERENCE).

Một bảng dựng bằng (1) sẽ cộng tiền THẬT vào sai thương hiệu và không màn
hình nào lộ ra — nó chỉ trông như một báo cáo bình thường. Nói ra khoảng
trống là kết quả kém vui hơn nhưng đúng, và nó đo được: Owner biết chính xác
bao nhiêu tiền và bao nhiêu dòng đang nằm trong khoảng trống đó.

## 4. OWNER_DECISION_REQUIRED — nguồn thương hiệu

**Điểm mơ hồ (đúng một):** trường thương hiệu chính danh phải đến TỪ ĐÂU.
Mọi phần còn lại của PHB-06 không mơ hồ và đã ship.

**Bằng chứng:** bảng ở mục 1; `PRA-005` §19; và
`tests/test_phb06_brand_reporting.py::test_the_canonical_identity_contract_still_carries_no_brand`
(khẳng định hợp đồng danh tính có ĐÚNG hai trường).

**Ba lựa chọn nhỏ nhất:**

| | Lựa chọn | Hệ quả nghiệp vụ |
|---|---|---|
| A | Tracking thêm thương hiệu vào `board` (`brand` cạnh `name`/`alt`) | Thẩm quyền đúng chỗ, không thêm thẩm quyền nào ở Reports. Bảng thương hiệu tự lên số cho MỌI dòng đã nhận diện, không phải sửa mã Reports. Cần một thay đổi ở hệ thống Tracking và một lần capture lại. |
| B | Public Purchase thêm `brand` vào projection identity | Cùng hình dạng như A nhưng chỉ phủ các mặt hàng đi qua danh mục công khai; hàng chỉ có ở Tracking vẫn trống. |
| C | Giữ nguyên — không có thương hiệu | Bảng thương hiệu tiếp tục là một bề mặt đo khoảng trống. Không tốn gì, và không trả lời được câu hỏi nghiệp vụ. |

**Khuyến nghị:** A. Nó đặt thương hiệu vào đúng thẩm quyền đã sở hữu danh
tính sản phẩm, và không mở một thẩm quyền thứ hai nào ở Reports.

**KHÔNG được coi là lựa chọn:** một bảng thương hiệu do Reports tự giữ, hay
bất kỳ phép suy từ tên hàng nào.

## 5. Findings

```text
BLOCKING_FINDINGS = 0
```

- `FIND-PHB06-01` · `NON_BLOCKING` — **Thương hiệu không có nguồn.** Đã xử lý
  bằng mục 4 (`OWNER_DECISION_REQUIRED`) + hai bucket "chưa xác định" tách
  bạch. RE-TRIGGER: hợp đồng danh tính có thêm trường thương hiệu — test nêu
  ở mục 4 sẽ đỏ đúng lúc đó.
- `FIND-PHB06-02` · `NON_BLOCKING` — **Không có MoM/lịch sử thương hiệu.**
  `§12` chỉ cho tái dùng một hợp đồng MoM ĐÃ có cho thương hiệu; không có.
  Không phát minh một hợp đồng mới. RE-TRIGGER: sau khi `FIND-PHB06-01` được
  giải quyết và có ít nhất hai kỳ liền nhau có thương hiệu.
- `FIND-PHB06-03` · `NON_BLOCKING` · **CÓ SẴN, không do PHB-06 gây ra** —
  `validate_reference_integrity.py` FAIL với 3 reference hỏng trong
  `docs/tasks/TASK-REM-T06-repository-root-hygiene.md` — ba tệp chuẩn của gốc
  repository mà tài liệu đó nhắc tới nhưng repo không có (README ở gốc, quy
  tắc ứng xử, hướng dẫn đóng góp). Ba tên tệp cố ý KHÔNG viết trong dấu nháy
  ngược ở đây: chính `validate_reference_integrity.py` coi mọi tên tệp trong
  nháy ngược là một reference phải phân giải được, nên trích dẫn nguyên văn
  sẽ nhân bản đúng lỗi đang mô tả. Đã xác nhận cùng 3 lỗi đó trên
  đúng `BASE_HEAD` khi stash toàn bộ thay đổi của phiên này. Đây chính là
  `F-05` mà `DEC-185` §7 đã quyết GIỮ NGUYÊN làm phát hiện; PHB-06 không mở
  lại nó.

## 6. Bằng chứng test

```text
BASE_HEAD (trước thay đổi)   : 2588 passed, 11 skipped
SAU PHB-06 (toàn bộ)         : 2630 passed, 11 skipped   (+42 = đúng test mới)
PHB-06 focused               : 42 passed
Bộ hồi quy đã nêu (§21)      : 622 passed, 2 skipped
  (105D · BH73804 · PHB-03 · PHB-05 · Employee Workspace · F-01 ·
   DEC-180 · DEC-185 · business metrics · business boundaries · golden ·
   identity durability + timeline)
Mutation probe M1…M8         : 8/8 BITE (mỗi probe làm phép kiểm tương ứng đỏ)

validate_structure           : PASS
validate_project_state       : PASS
validate_evidence            : PASS (155 bản ghi)
validate_reference_integrity : FAIL — 3 lỗi CÓ SẴN trên BASE_HEAD (FIND-PHB06-03)
```

## 7. Bàn giao

`NEXT_VERTICAL_ACTION` = đưa mục 4 tới Chủ dự án. Không lát cắt PHB-06 nào
tiếp theo có ý nghĩa cho tới khi nguồn thương hiệu được quyết: tầng gộp, phép
đối soát, trang và test đã sẵn sàng và sẽ tự lên số mà không phải sửa mã.
