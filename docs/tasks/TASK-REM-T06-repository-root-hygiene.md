# TASK-REM-T06 — Vệ sinh Repository Root

## Metadata

Status:
READY

Phase:
PHASE-03 — Repository Hygiene

Task Mode:
MICRO

Primary Agent Tier:
A (nhanh, rủi ro thấp, phạm vi rõ ràng)

Escalation Tier:
N/A — task MICRO, không có escalation formal

Difficulty:
1/5 (tạo 2 file text tĩnh)

Risk:
1/5 (chỉ thêm file, không modify logic/data)

Blast Radius:
1/5 (chỉ ảnh hưởng repository root, không ảnh hưởng code chạy hay validator)

Project Profile:
PRODUCT

## Mục Tiêu (Objective)

Hoàn thiện repository root hygiene bằng cách tạo README.md và LICENSE tại root, 
đáp ứng FIND-009 (LOW). Giúp người dùng/contributor từ ngoài hiểu rõ repo này là 
gì và điều kiện sử dụng.

Ghi chú: `.gitignore` đã tồn tại từ S003 (chứng minh: REM-T03 checklist).

## Phạm Vi (Scope)

**Tạo hoặc cập nhật:**
- `/README.md` — giải thích về governance framework, cách clone/run validator, 
  thông tin liên lạc chủ dự án
- `/LICENSE` — điều khoản sử dụng (nội dung cụ thể do chủ dự án quyết định)

**Xác minh:**
- 2 file đã tồn tại ở root
- Không có lỗi reference integ rity trỏ vào chúng
- Validator `validate_structure.py` vẫn PASS

## Ngoài Phạm Vi (Out of Scope)

- Thay đổi `.gitignore` (đã xử lý ở REM-T03)
- Tạo `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (không yêu cầu ở đây)
- Cập nhật gitattributes, .gitmodules (không cần)
- Thay đổi logic của bất kỳ validator nào
- Tạo/sửa schema hoặc dữ liệu persistent

## Phụ Thuộc (Dependencies)

- Không có (task độc lập với Track A)

## Chặn (Blocks)

- Không chặn bất kỳ task nào (FIND-009 là LOW)

## An Toàn Để Chạy Song Song Với (Parallel-Safe With)

- Toàn bộ Track A (GATE-00 đã PASS, Phase 1 đang triển khai)
- REM-T07 (CI enforcement — không xung đột file)
- Bất kỳ task khác trên Track B (không xung đột)

## Phạm Vi Tác Động Dự Kiến (Expected Touch Area)

Allowed:
- `/README.md` (tạo mới nếu chưa tồn tại; cập nhật nếu đã có nhưng cũ)
- `/LICENSE` (tạo mới)
- `PROJECT/PROJECT_PROGRESS.md` — cập nhật REM-T06 từ PLANNED → DONE, 
  đóng FIND-009

Không được đụng vào nếu chưa có Scope Expansion:
- `governance/` — ngoại trừ việc thêm reference đến nó ở README
- `docs/` — ngoại trừ việc tạo session handoff (S009)
- Bất kỳ validator `.py` nào
- `.gitignore` (đã DONE)

## Subtask (Subtasks)

- [ ] 06.1 Viết README.md tại root — giải thích repo và cách sử dụng
- [ ] 06.2 Viết LICENSE tại root — xác định điều khoản sử dụng
- [ ] 06.3 Xác minh 2 file không gây lỗi reference integrity
- [ ] 06.4 Chạy lại `validate_structure.py` — xác nhận PASS
- [ ] 06.5 Cập nhật PROJECT_PROGRESS.md, ghi Completion Gate evidence
- [ ] 06.6 Viết session handoff (S009)

## Ready Gate

Dùng `governance/core/TASK_READY_GATE_STANDARD.md`.

- [x] Yêu cầu/lỗi đã rõ ràng đủ để bắt tay vào làm.
  - FIND-009 đã ghi rõ: repository root thiếu README + LICENSE
  - Scope Lock: chỉ tạo 2 file này, không expand

- [x] Risk <= 2.
  - Risk = 1: chỉ tạo file text tĩnh, không ảnh hưởng code logic hay data

- [x] Blast Radius <= 2.
  - Blast Radius = 1: chỉ ảnh hưởng repository root, không ảnh hưởng 
    validator, governance, hay Track A

- [x] Không có thay đổi về architecture/auth/schema/dữ liệu mang tính phá hủy.
  - Không có thay đổi nào kiểu này; chỉ tạo file

- [x] Phạm vi tác động dự kiến hẹp và đã biết rõ.
  - 2 file cụ thể ở root, xác nhận trong Scope Lock

- [x] Phương pháp xác minh liên quan đã được xác định.
  - Subtask 06.3 (reference integrity): `grep` tìm reference vào 
    `README.md`/`LICENSE` trong toàn codebase
  - Subtask 06.4: `python3 governance/scripts/governance/validate_structure.py`
  - Subtask 06.5: ghi evidence vào Completion Gate

**Ready Gate Status: FROZEN** — sẵn sàng triển khai ngay.

## Completion Gate

Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và `governance/core/EVIDENCE_STANDARD.md`.

### Functional

#### CHECK-T06-01 — README tồn tại và có nội dung

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

#### CHECK-T06-02 — LICENSE tồn tại và có nội dung

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

#### CHECK-T06-03 — Không có lỗi reference integrity

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
```bash
$ python3 governance/scripts/governance/validate_reference_integrity.py
REFERENCE INTEGRITY: PASS
```

#### CHECK-T06-04 — validate_structure.py PASS

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
```bash
$ python3 governance/scripts/governance/validate_structure.py
GOVERNANCE STRUCTURE: PASS
Deployment root: PASS — /home/user/Reports
Checked 21 required paths.
```

### Exit Criteria

- Toàn bộ 4 CHECK REQUIRED đều PASS (E1 evidence)
- Không xảy ra Scope Expansion
- Không có regression trong validator
- Không có issue mới phát sinh liên quan safe deployment

**Exit Criteria Status: NOT_MET** — chưa triển khai

## Ghi Chú

- Task này độc lập; có thể chạy ngay sau khi Ready Gate frozen
- Không chặn Phase Gate 02 (đó là Gate 02 mà phần trước REM-T05 mở, cần kết hợp 
  tương lai sau REM-T06)
- Nội dung README và LICENSE do chủ dự án quyết định cuối cùng; agent viết bản 
  draft rõ ràng, rồi chủ dự án review/approve trước khi merge
