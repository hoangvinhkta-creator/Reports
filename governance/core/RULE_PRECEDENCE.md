# Rule Precedence

## Mục đích
Giải quyết các xung đột thực sự giữa các quy tắc governance mà không tự ý dàn xếp một cách âm thầm.

## Thứ tự ưu tiên

1. Safety / Security
2. Data Integrity
3. Legal / Privacy / Compliance
4. Explicit Business Requirements
5. Backward Compatibility
6. Architecture Contracts
7. Reliability / Operations
8. Accessibility / UX Correctness
9. Performance
10. Code Style / Developer Convenience

## Quy tắc quan trọng

Thứ tự ưu tiên CHỈ được áp dụng khi hai yêu cầu thực sự không thể cùng được thỏa mãn.

Một quy tắc có mức ưu tiên cao hơn không cấp phép để bỏ qua một quy tắc có mức ưu tiên thấp hơn khi cả hai có thể cùng tồn tại.

## Quy trình xử lý xung đột

Khi có một xung đột thực sự, hãy ghi lại:

RULE CONFLICT

Higher-priority rule:
...

Lower-priority rule:
...

Why both cannot be satisfied:
...

Risk:
...

Proposed resolution:
...

Required decision:
...

Không được tự ý giải quyết các xung đột quan trọng một cách âm thầm.
