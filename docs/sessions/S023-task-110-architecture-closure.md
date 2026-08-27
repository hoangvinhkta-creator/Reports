# S023 — TASK-110, Architecture Closure

## Metadata

Task:
TASK-110 — Validation + Review Queue

Current Task Mode:
MAJOR

Selected Profile:
PRODUCT

Ngày:
2026-08-23

Base SHA (trước repair):
`2d1da986d2ff99ca352d912ecc5898b765cb98ee`

Baseline commit:
`e22192401e0f5bb5917b3fcbb1802678f1a60be0`

Trạng thái ra khỏi phiên:
**IMPLEMENTED. NOT MERGED. NOT DONE.** CHECK-110-16 tiếp tục **BLOCKED**.

## Root Cause — một câu

> Mọi invariant của TASK-110 được cưỡng chế tại một **CHỖ** (một hàm, một
> check, một test) thay vì được **MANG** bởi một **KIỂU**. Một chỗ thì đi vòng
> được; một kiểu thì không.

Đó là lý do sáu vòng review không hội tụ: mỗi vòng thêm một chỗ, vòng sau tìm
đúng con đường không đi qua chỗ đó.

## Năm root cause, đóng bằng cấu trúc

| RC | Đóng bằng |
|---|---|
| RC-1 | **Sealed construction.** `EmployeeMaster`, `EmployeeRecord`, `AffectedRow`, `RowProvenance` chỉ dựng được qua factory đã parse. Giữ được object = bằng chứng nó hợp lệ. |
| RC-2 | **`message`/`details` là property dẫn xuất.** `renderer.py` là hàm thuần chỉ nhận `(Diagnostics, RowProvenance)`; không có đầu vào nào khác để nêu một dòng lạ. |
| RC-3 | **`evaluate_raw_mapping(stats)`** — một `MappingStats` sở hữu đồng thời bộ đếm, chỉ mục dòng, mapper. Mọi con số dòng trong message đọc từ `provenance`. |
| RC-4 | **Parse, đừng validate.** `EmployeeRecord` + `DateWindow`; ngày méo mó, sai kiểu, cửa sổ bất khả, group ma, prefix trùng khít chồng cửa sổ đều là parse thất bại tại biên master. |
| RC-5 | **Oracle structural.** L1 phủ `MappingResult` qua `dataclasses.fields()`; L2 giữ `order_graph`. Không regex-over-message. |

## HD-110-16 — chứng minh

`tests/test_reconcile_raw_criteria.py`: **13 test trước → 13 test sau**, không
test nào bị xoá. 15 lời gọi 8-tham-số chuyển sang `MappingStats` canonical qua
helper `_synth()` dựng đúng số dòng thô mà mỗi Counter mô tả — nên stats mang
provenance thật thay vì một con số trần. Hai test F1 migrate sang
`pytest.raises(InvalidEmployeeConfig)`, giữ nguyên ý định "master hỏng KHÔNG
được đi lọt", nay bị bắt sớm hơn.

Không shim 8-tham-số; chữ ký cũ đã biến mất và có test canh
(`inspect.signature(evaluate_raw_mapping).parameters == ["stats"]`).

## HD-110-17 — chứng minh

`test_hd_110_17_no_public_entry_point_admits_a_bad_group` cố ý dựng master có
group không khai / thiếu group / group rỗng qua **mọi** điểm vào production —
`build_employee_master()`, `load_employee_master()`, `EmployeeMapper.from_yaml()`
— và tất cả đều raise `InvalidEmployeeConfig` **trước khi** một giao dịch nào
được xử lý. `'criterion="F1"'` không còn tồn tại trong mã nguồn.

## Ghi chú thực thi HD-110-15

Luật cấm `raw_prefix` trùng khít áp **chỉ khi hai cửa sổ hiệu lực chồng nhau** —
đó đúng là tình huống gây hại mà HD-110-15 mô tả. Cùng prefix với cửa sổ **rời
nhau** là cách DEC-121 diễn đạt một lượt **bàn giao**; cấm nó sẽ phá một quy
tắc nghiệp vụ canonical, và không dòng nào bị mất. Có test canh cả hai chiều.

## Bằng chứng ra khỏi phiên

- **20/20** case falsification của Architecture Closure Audit = **CLOSED**
  (trước repair: 7/20).
- **7/7** mutation class chứng minh oracle **CÓ THỂ FAIL**.
- L1 semantic IDENTICAL · L1 v1 IDENTICAL · L2 scalar IDENTICAL · L2 graph IDENTICAL.
- TASK-108A-1: **24/24** PASS.
- 22 module nghiệp vụ được bảo vệ: không file nào đổi.

## Rủi ro còn lại

- **CHECK-110-16 vẫn BLOCKED** — chưa có workbook production.
- L2 chạy trên dữ liệu synthetic; không phủ hình dạng dữ liệu chưa từng thấy.
- Seal dùng sentinel `_SEAL` cấp module — chống nhầm lẫn vô ý, không chống một
  người cố tình import ký hiệu private.
- `EmployeeRecord.__getitem__`/`get` giữ cú pháp đọc kiểu dict cho artifact đã
  freeze; đó là một object với hai cú pháp đọc, không phải hai nguồn dữ liệu.
- `renderer.py` giữ bảng văn bản theo `rule`/`criterion`; thêm một rule mới mà
  quên renderer sẽ **raise** chứ không im lặng — có test canh.

## Bàn giao

**Independent Review #8.** Không merge, không tự chuyển DONE.
