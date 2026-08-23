# Thư Mục Governance

Thư mục này chứa governance TĨNH (STATIC).

## Cấu Trúc

```text
governance/
├── core/       # session control, engineering rules, gates, evidence
├── product/    # product/production/operations rules
├── audit/      # discovery and audit templates
├── templates/  # runtime artifact templates
├── scripts/    # machine validators
└── reference/  # guide, changelog, history, acceptance material
```

## Lưu Ý Quan Trọng

Không di chuyển các file này trở lại thư mục gốc repository.

Điểm bắt đầu (entry point) ở thư mục gốc là:
`CLAUDE.md`

Mỗi session nên bắt đầu từ `CLAUDE.md`, sau đó chỉ tải các file cần thiết cho project profile đã chọn và task hiện tại.


## Quy Tắc Bảo Toàn Nội Dung

Việc tái cấu trúc thư mục KHÔNG ĐƯỢC viết lại, tóm tắt, rút gọn, hoặc xóa bỏ ngữ nghĩa governance.

Được phép trong một lần tái cấu trúc thuần cấu trúc:
- di chuyển file,
- cập nhật đường dẫn canonical,
- cập nhật cách validator resolve đường dẫn.

Bất kỳ thay đổi mang tính ngữ nghĩa nào cũng phải được xác định riêng, có lý do rõ ràng, và được kiểm thử.
