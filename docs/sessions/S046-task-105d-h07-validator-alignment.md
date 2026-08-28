# S046 — TASK-105D H-07 Validator Alignment (Tooling)

Session Type:
TOOLING / VALIDATOR ALIGNMENT — sửa `governance/scripts/governance/validate_task_completion.py`
để nó công nhận mô hình hai lớp của `DEC-159`. **Không** phải phiên
implementation `TASK-105D`, **không** phải phiên repair, **không** phải
phiên review độc lập, **không** phải phiên completion.

Date:
2026-08-28

Current Task Mode:
MICRO (tooling alignment, phạm vi hẹp, xác định trước — không mở file task
mới, không đổi frozen gate, không đổi production/business logic).

Selected Profile:
PRODUCT

Risk:
Effective Risk của thay đổi này = LOW/MEDIUM cục bộ (script governance nội
bộ, không phải `app/**`) nhưng **hệ quả gián tiếp HIGH**: nó là điều kiện #7
chặn `TASK-105D DONE` (Effective Risk HIGH kế thừa, Local Risk 4 / Blast
Radius 5). Vì vậy toàn bộ thay đổi được verify bằng E2 (chạy thật, không suy
diễn) trước khi coi là closed.

Evidence Level:
E2 — mọi lệnh dưới đây được chạy thật trong phiên này.

Executed By:
phiên H-07 Validator Alignment (S046)

Timestamp:
2026-08-28

Branch:
`governance/task-105d-gate-execution-reconciliation`

Base SHA:
`048a276337bcb7db1478c80592eb192e8e4a2037` (đầu phiên `S046`,
= head của `S045` trên nhánh này)

Authority:
Owner Decision — chỉ thị mở phiên này ("TASK-105D H-07 — VALIDATOR
ALIGNMENT") tường minh cấp thẩm quyền tooling/governance-scripts mà
`DEC-159` Impact/"Can Revisit After" đã nêu là điều kiện đóng H-07 lớp
validator. Phiên **không** có completion authority (không đánh dấu `DONE`),
**không** có thẩm quyền sửa `governance/core/TASK_COMPLETION_GATE_STANDARD.md`,
frozen gate, hay `app/**`/`config/**`.

## 1. Xác minh lại DEC-159 và bằng chứng canonical S045 (bắt buộc trước khi sửa code)

Đọc lại toàn văn `DEC-159` (`PROJECT/PROJECT_DECISIONS.md`) và
`docs/sessions/S045-task-105d-h07-reconciliation-and-capability-governance.md`
§A6/A7/A8 (đã xác nhận trong phiên trước khi sửa bất kỳ dòng code nào):

```text
Layer 1 (frozen)           : Completion Gate definition tại
                              docs/tasks/TASK-105D-product-identity-resolver.md,
                              GATE_SET_SHA256 = 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
                              — 32/32 Status: NOT_TESTED, VĨNH VIỄN theo thiết kế.
Layer 2 (execution record) : docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md
                              — 32/32 PASS, bind đúng GATE_SET_SHA256, lineage
                              S040 (thực thi) + Independent Review #1 (S041) +
                              Independent Review #2 (S043), 3 lần đo độc lập
                              cho cùng một kết quả.
8 điều kiện binding (DEC-159 §1) : đã liệt kê tường minh trong Owner Decision;
                              validator mới implement đúng 8 điều kiện đó,
                              không thêm/bớt.
Xung đột cần đóng (DEC-159 §5) : validate_task_completion.py grep literal
                              `Status:` trong khối `#### CHECK-*`; không có
                              khái niệm Gate Execution Record tách rời; sẽ
                              FAIL cả 32 REQUIRED check nếu một phiên tương
                              lai đặt TASK-105D top-level Status: DONE trong
                              khi 32 khối vẫn NOT_TESTED.
```

Không phát hiện sai lệch giữa văn bản `DEC-159`/`S045` và trạng thái thật đo
lại trong phiên này (hash, số check, lineage — xem §3 dưới).

## 2. Thiết kế thay đổi

`governance/scripts/governance/validate_task_completion.py` giữ nguyên
đường đi Layer 1 (literal `Status: PASS` trong khối `#### CHECK-*`) không
đổi một dòng hành vi. Thêm một đường đi Layer 2, **chỉ** kích hoạt khi khối
literal đọc đúng `Status: NOT_TESTED` (placeholder freeze theo DEC-159 —
không áp dụng cho `FAIL`/`BLOCKED`/`NOT_APPLICABLE` literal, vì đó không
phải tình huống DEC-159 mô tả):

```text
1. Tìm GATE_SET_SHA256 đã khai báo trong chính file task (khối freeze),
   qua regex tìm nhãn + hash 64-hex, không phụ thuộc định dạng chính xác
   từng byte (chấp nhận backtick hoặc không, cùng dòng hoặc dòng kế tiếp).
2. Tìm (các) file docs/reviews/TASK-<ID>-GATE-EXECUTION-RECORD*.md, suy ra
   <ID> từ chính tên file task (TASK-<ID>-...). Không hardcode "105D" —
   cơ chế áp dụng cho MỌI task tương lai dùng đúng quy ước đặt tên này.
3. Parse bảng kết quả (CHECK | Status | Evidence Level | ... | ...) trong
   mỗi record, và nhãn GATE_SET_SHA256 + Executed By ở phần metadata.
4. Một REQUIRED check NOT_TESTED được coi là "effectively PASS" CHỈ KHI:
   - tồn tại record ràng buộc đúng GATE_SET_SHA256 (khớp tuyệt đối với
     hash khai báo trong file task);
   - record đó có dòng cho đúng CHECK ID;
   - không có record nào khác (cùng bind đúng hash + đúng check ID) cho
     kết quả KHÁC — nếu có, FAIL CLOSED (ambiguous), không đoán mò;
   - kết quả = PASS (khác PASS ⇒ FAIL CLOSED, báo đúng kết quả);
   - Executed By non-empty (lineage);
   - Evidence Level ∈ {E0,E1,E2};
   - Evidence (kết quả chạy + test reference) non-empty.
5. Bất kỳ điều kiện nào không thoả ⇒ lỗi cụ thể, KHÔNG effective PASS.
```

Đường đi Layer 1 (`Status: PASS` literal) và trường hợp literal
`FAIL`/`BLOCKED`/`NOT_APPLICABLE` giữ nguyên 100% hành vi cũ, byte-for-byte
cùng thông điệp lỗi.

Để test được cô lập (không phải chạy trên toàn bộ `docs/tasks/` thật), logic
được bọc trong một hàm `run_validation(task_dir=TASK_DIR,
gate_exec_dir=GATE_EXEC_DIR)` thay vì chạy ở top-level module; khối
`if __name__ == "__main__":` gọi hàm này với default = đường dẫn thật, giữ
nguyên contract CLI (stdout, exit code) — xem §4 xác nhận không đổi output
trên baseline thật.

## 3. Production diff

```text
$ git diff --stat
 governance/scripts/governance/validate_task_completion.py | 287 ++++++++++++++++-----
 1 file changed, 217 insertions(+), 70 deletions(-)

$ git diff --stat -- app/ config/ docs/tasks/ docs/spec/ governance/core/ Tracking
(không có output — 0 file)
```

`docs/tasks/TASK-105D-product-identity-resolver.md` **không** bị chạm.

## 4. Frozen gate hash — trước/sau (bắt buộc, brief §)

```text
$ sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md | sha256sum
0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877  -
```

Đo TRƯỚC khi sửa validator (đầu phiên, trên `048a276`) và SAU khi sửa xong
(cuối phiên) — cùng một giá trị, khớp tuyệt đối với `GATE_SET_SHA256` đã
freeze tại `S038`/ghi trong `DEC-159`. 0 byte đổi trong khối gate.

## 5. Validator tests — 10 test tập trung

File mới: `tests/test_governance_validate_task_completion.py`. Import trực
tiếp module qua `importlib.util.spec_from_file_location` (script không nằm
trong package). Sáu test bắt buộc theo brief + bốn test bổ sung: hai cho các
điều kiện fail-closed brief liệt kê riêng (duplicate/ambiguous, malformed
binding), và một regression test cho một bug thật phát hiện ở §5.1.

```text
test_a_legacy_embedded_pass_still_works               PASS
test_b_valid_two_layer_pass_works                      PASS
test_c_wrong_hash_fails                                PASS
test_d_missing_check_fails                             PASS
test_e_fail_result_fails                                PASS
test_f_not_tested_without_execution_record_fails       PASS
test_duplicate_ambiguous_records_fail_closed           PASS
test_malformed_binding_missing_lineage_fails           PASS
test_check_heading_with_trailing_description_resolves  PASS
test_real_repo_cli_output_is_unchanged                 PASS

$ python3 -m pytest tests/test_governance_validate_task_completion.py -q
..........
10 passed in 0.05s
```

### 5.1 Bug thật phát hiện bởi mô phỏng trên dữ liệu thật (§8), không phải bởi fixture đơn giản

Bản draft đầu tiên của `_resolve_via_gate_execution_record` tra cứu check ID
bằng chính `check_name` — dòng đầu tiên của khối `#### CHECK-*`. Toàn bộ 9
test fixture ban đầu (dùng heading trần, ví dụ `#### CHECK-TEST-01`) PASS
với draft đó, **che giấu** một lỗi thật: heading thật trong
`docs/tasks/TASK-105D-product-identity-resolver.md` có dạng
`CHECK-105D-01 (G01) — mô tả tiếng Việt dài`, không phải ID trần. Mô phỏng
§8 (chạy `run_validation()` trên bản sao trong bộ nhớ của chính file task
thật, patch top-level `Status: DONE`) phát hiện **cả 32/32 check FAIL** với
lý do `check ID not present in any Gate Execution Record` — vì
`check_name` (cả câu heading) không bao giờ khớp bảng `CHECK-105D-01` trần
trong `docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md`.

Sửa: tách riêng `check_id` (chỉ token `CHECK-<...>` dẫn đầu, qua regex) khỏi
`check_name` (giữ nguyên cho thông điệp lỗi, không đổi hành vi cũ). Thêm
test `test_check_heading_with_trailing_description_resolves` tái lập đúng
hình dạng heading thật để khoá lại bug này. Đây là bằng chứng trực tiếp cho
lý do §8 (mô phỏng trên dữ liệu thật) là bước bắt buộc, không phải chỉ chạy
unit test cô lập trên fixture tối giản.

## 6. Canonical validators — chạy lại toàn bộ

```text
$ python3 governance/scripts/governance/validate_structure.py
GOVERNANCE STRUCTURE: PASS
Deployment root: PASS — /home/user/Reports
Checked 21 required paths.

$ python3 governance/scripts/governance/validate_project_state.py
PROJECT STATE: PASS

$ python3 governance/scripts/governance/validate_reference_integrity.py
REFERENCE INTEGRITY: FAIL
Quét 163 file .md (loại trừ 10 file trong governance/reference/history/, docs/audit/).
3 reference không phân giải được:
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md

$ python3 governance/scripts/governance/validate_evidence.py
EVIDENCE VALIDATION: PASS
Checked 88 REQUIRED PASS evidence record(s).

$ python3 governance/scripts/governance/validate_task_completion.py
TASK COMPLETION: PASS
Checked 6 DONE task(s).
```

Đúng baseline tham chiếu đã biết (3 issue `TASK-REM-T06` tiền tồn, không
liên quan phiên này) — **0 regression mới**. `validate_task_completion.py`
cho **cùng output hệ trọng** với baseline trước sửa
(`TASK COMPLETION: PASS`, `Checked 6 DONE task(s).`) vì `TASK-105D` hiện
`Status: READY` (chưa `DONE`) nên đường đi Layer 2 chưa được kích hoạt trên
dữ liệu thật — thay đổi chỉ **có sẵn**, chưa **được dùng** cho `TASK-105D`.

## 7. Full test suite — regression check

```text
$ python3 -m pytest -q
965 passed, 11 skipped in 14.30s
```

0 failed, 0 test cũ đổi kết quả.

## 8. TASK-105D validation result — mô phỏng trên dữ liệu thật (không mutate)

Không mutate `docs/tasks/TASK-105D-product-identity-resolver.md`
(`Status: READY`, không phải `DONE` — validator không kích hoạt kiểm tra
REQUIRED check cho task này ở trạng thái hiện tại, đúng thiết kế). Để chứng
minh Layer 2 hoạt động đúng trên chính bộ dữ liệu thật của `TASK-105D` mà
KHÔNG sửa file task, phiên này chạy một kiểm tra tạm thời (không commit)
trỏ `run_validation()` vào bản sao **trong bộ nhớ/thư mục tạm** với
top-level `Status:` được đổi thành `DONE` (chỉ trong buffer/tmpdir, không
ghi lại vào `docs/tasks/`), giữ nguyên toàn bộ 32 khối gate + đọc thẳng
`docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md` thật trên đĩa:

```text
$ python3 - <<'EOF'
import importlib.util, tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "validate_task_completion",
    "governance/scripts/governance/validate_task_completion.py",
)
vtc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vtc)

real_task_path = Path("docs/tasks/TASK-105D-product-identity-resolver.md")
text = real_task_path.read_text(encoding="utf-8")
old = "Status:\nREADY"
assert text.count(old) == 1
patched = text.replace(old, "Status:\nDONE", 1)

with tempfile.TemporaryDirectory() as td:
    tmp_task_dir = Path(td) / "tasks"
    tmp_task_dir.mkdir()
    (tmp_task_dir / real_task_path.name).write_text(patched, encoding="utf-8")
    errors, checked = vtc.run_validation(
        task_dir=tmp_task_dir,
        gate_exec_dir=Path("docs/reviews"),
    )

print("checked_done:", checked)
print("error_count:", len(errors))
for e in errors:
    print("-", e)
EOF
checked_done: 1
error_count: 0
```

Kết quả (SAU khi sửa bug §5.1): `TASK COMPLETION` mô phỏng = PASS trên toàn
bộ 32/32 `CHECK-105D-01..32` — mọi check literal `NOT_TESTED` được Layer 2
giải quyết effectively PASS qua `docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md`
thật, đúng `GATE_SET_SHA256`, đúng 32 check ID, PASS, Evidence Level +
Evidence + lineage đầy đủ. **Trước khi sửa bug §5.1, cùng script này cho
32/32 lỗi** (`check ID not present in any Gate Execution Record`) — bằng
chứng nguyên văn giữ lại tại §5.1 để không xoá lịch sử phát hiện.

Kết luận cơ học: **nếu** một phiên có thẩm quyền completion trong tương lai
đặt `TASK-105D` top-level `Status: DONE`, `validate_task_completion.py` bản
mới **sẽ không** FAIL 32 REQUIRED check chỉ vì chúng đọc `NOT_TESTED` —
điều kiện #7 của `DEC-159` (§A7) nay được thoả về mặt cơ học.

## 9. H-07 disposition sau phiên này

```text
H-07 trước phiên này (S045)  : PARTIALLY RECONCILED
    lớp diễn giải/thẩm quyền  : RESOLVED (DEC-159)
    lớp validator (điều kiện #7) : OPEN

H-07 sau phiên này (S046)    : RECONCILED — CẢ HAI LỚP
    lớp diễn giải/thẩm quyền  : RESOLVED (DEC-159, không đổi)
    lớp validator (điều kiện #7) : RESOLVED — validate_task_completion.py
                                    công nhận Layer 2 (Gate Execution Record)
                                    đúng 8 điều kiện binding của DEC-159,
                                    xác nhận bằng 10 test tập trung + mô phỏng
                                    §8 trên dữ liệu thật.

H-07 mechanical blocker CLOSED? CÓ.
```

`H-07` (toàn bộ, cả hai lớp) nay **RECONCILED**. Đây là **mechanical
blocker** cuối cùng theo brief mở phiên — không phải toàn bộ điều kiện
`DONE` của `TASK-105D`.

## 10. TASK-105D vẫn KHÔNG DONE — lý do không đổi

Đóng H-07 (điều kiện #7 của `DEC-159`) chỉ giải quyết ĐÚNG MỘT trong nhiều
điều kiện `Tiêu Chí Hoàn Thành` của `TASK-105D`
(`governance/core/TASK_COMPLETION_GATE_STANDARD.md`). Các điều kiện khác
KHÔNG được phiên này đánh giá lại và KHÔNG tự động thoả chỉ vì H-07 đóng:

```text
- 0 BLOCKING finding                         : cần một phiên đọc lại toàn bộ
                                                14 HARDENING còn OPEN (bảng
                                                S045 §A8-A9) và xác nhận
                                                không phát sinh mới.
- Independent Review E2 PASS cho chính
  quyết định "DONE"                          : Independent Review #2 (S043)
                                                đã PASS WITH HARDENING cho
                                                IMPLEMENTATION, nhưng KHÔNG
                                                phải review cho hành động
                                                "đặt Status: DONE" — đó là
                                                một quyết định completion
                                                riêng, ngoài thẩm quyền
                                                phiên này.
- INV-01…INV-87 có assertion/lý do đầy đủ    : chưa re-verify trong phiên này.
- Progress/roadmap/handoff cập nhật cho DONE : chưa thực hiện — phiên này
                                                CHỦ ĐỘNG không mark DONE
                                                (ngoài thẩm quyền, brief cấm).
```

Phiên này **không** có completion authority và **không** đánh giá các điều
kiện trên — đúng ranh giới brief đặt ra ("Do not mark TASK-105D DONE").

```text
TASK-105D eligible for DONE review?  CÓ — điều kiện #7 (blocker cơ học cuối
    cùng theo S045 §A9) nay đã đóng, nên một phiên DONE-review CÓ THỂ mở mà
    không còn vấp lỗi validator cơ học. "Eligible for review" ≠ "DONE" —
    phiên DONE-review đó vẫn phải tự đánh giá 4 điều kiện còn lại ở trên,
    độc lập, không kế thừa mù kết luận này.
```

## 11. Ranh giới đã xác nhận KHÔNG vượt

```text
- Frozen gate TASK-105D (docs/tasks/TASK-105D-product-identity-resolver.md) : 0 byte đổi
- 32 trường Status: trong khối gate                                          : không đổi
- GATE_SET_SHA256                                                            : không đổi (§4)
- app/**, config/**, business logic                                         : 0 byte đổi
- Repair Cycle #2                                                            : KHÔNG mở
- TASK-105D top-level Status                                                : không đổi (vẫn READY)
- Task file mới                                                             : KHÔNG tạo
- Tracking                                                                  : không chạm
- TASK-105B/C/E/108B                                                        : không chạm
- V4.2 migration                                                            : không thực hiện
- governance/core/TASK_COMPLETION_GATE_STANDARD.md                          : không chạm — không cần,
    thay đổi nằm gọn trong validator, không đòi tái diễn giải standard.
```

## 12. FINAL REPORT

```text
Base SHA   : 048a276337bcb7db1478c80592eb192e8e4a2037
Head SHA   : (SHA của commit phiên này — xem git log sau khi commit)

Production diff : 0 byte (app/**, config/**, docs/tasks/**, governance/core/**, Tracking)

Validator diff   : governance/scripts/governance/validate_task_completion.py
                    (217 insertions, 70 deletions — thêm Layer 2 Gate
                    Execution Record resolution, giữ nguyên Layer 1;
                    refactor logic vào run_validation() để test cô lập được,
                    CLI contract (__main__) không đổi)

Tests added      : tests/test_governance_validate_task_completion.py
                    (10 test: A-F theo brief + 2 fail-closed bổ sung +
                    1 regression test cho bug §5.1 + 1 smoke test trên
                    repo thật) — 10/10 PASS

Frozen hash TRƯỚC : 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
Frozen hash SAU   : 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
                    (KHỚP TUYỆT ĐỐI — không đổi)

TASK-105D validation result (mô phỏng, không mutate) : PASS 32/32 qua Layer 2
    (xem §8) — không có lỗi phát sinh; trên dữ liệu thật hiện tại
    (Status: READY) validator vẫn PASS như baseline cũ (6 DONE task, không
    đổi) vì Layer 2 chưa kích hoạt (TASK-105D chưa DONE).

H-07 mechanical blocker closed?  CÓ.
Eligible for DONE review?        CÓ (điều kiện #7 đóng) — nhưng KHÔNG đồng
    nghĩa DONE; 4 điều kiện completion còn lại (§10) chưa được phiên này
    đánh giá và cần một phiên DONE-review riêng, có thẩm quyền.
```

## Next authorized action

```text
1. Một phiên DONE-review có thẩm quyền completion (KHÔNG phải phiên này)
   đánh giá 4 điều kiện còn lại ở §10, rồi mới được đặt TASK-105D
   top-level Status: DONE.
2. KHÔNG mở Repair Cycle #2. KHÔNG tạo task mới. KHÔNG chạm TASK-105B/C/E/108B.
3. Nhánh này KHÔNG merge vào nhánh mặc định trong phiên này — theo đúng
   chỉ thị brief ("Do not merge default").
```
