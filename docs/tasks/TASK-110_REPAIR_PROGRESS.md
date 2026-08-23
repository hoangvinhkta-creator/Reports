# TASK-110 REPAIR PROGRESS

> File theo dõi riêng cho giai đoạn cô lập repair sau Independent Review #8.
> Không thay thế `PROJECT/PROJECT_PROGRESS.md`. Chỉ dùng để điều phối R1→R8.
> Mỗi unit chỉ được chuyển `FROZEN` sau Independent Review PASS.

## Baseline

| Trường | Giá trị |
|---|---|
| Review source | Independent Review #8 |
| Reviewed SHA | `c8c18229e3ef5a9d600b8d99a1cc21bcbbb2d8dd` |
| TASK-110 | NOT MERGED · NOT DONE |
| CHECK-110-16 | BLOCKED |
| Repair mode | ACTIVE |

## Tiến độ

| Unit | Chủ đề | Severity | Trạng thái | Repair SHA | Review verdict | Ghi chú |
|---|---|---:|---|---|---|---|
| R1 | Canonical Object Safety | HIGH | READY | — | — | Bắt đầu tại đây |
| R2 | MappingStats Single Source of Truth | HIGH | BLOCKED BY R1 | — | — | Không sửa trước R1 PASS |
| R3 | WorkingData Ownership | HIGH | BLOCKED BY R2 | — | — | — |
| R4 | Diagnostics ↔ Provenance | HIGH | BLOCKED BY R3 | — | — | — |
| R5 | ReviewQueue Integrity | HIGH | BLOCKED BY R4 | — | — | — |
| R6 | Master Identity / snapshot_id | MEDIUM | BLOCKED BY R5 | — | — | — |
| R7 | Oracle L2 Coverage | MEDIUM | BLOCKED BY R6 | — | — | — |
| R8 | Governance Canonical State | MEDIUM | BLOCKED BY R7 | — | — | — |
| FINAL | Final Integration Review | — | BLOCKED BY R1–R8 | — | — | Không chạy sớm |

## State machine

`READY → IMPLEMENTING → AWAITING_REVIEW → FROZEN`

Nếu review FAIL:

`AWAITING_REVIEW → REPAIRING → AWAITING_REVIEW`

Không được chuyển sang unit tiếp theo khi unit hiện tại chưa `FROZEN`.

## Nhật ký repair

### R1 — Canonical Object Safety
- Status: READY
- Exact starting SHA: TBD tại session repair.
- Finding reproduction before change: TODO.
- Frozen touch-area: TODO.
- Invariant: canonical object invalid không thể được tạo qua public/reasonable API.
- Focused tests: TODO.
- Independent falsification: TODO.
- Repair SHA: TODO.
- Independent Review: TODO.
- Freeze evidence: TODO.

### R2 — MappingStats Single Source of Truth
- Status: BLOCKED BY R1.
- Không thực hiện trước khi R1 FROZEN.

### R3 — WorkingData Ownership
- Status: BLOCKED BY R2.

### R4 — Diagnostics ↔ Provenance
- Status: BLOCKED BY R3.

### R5 — ReviewQueue Integrity
- Status: BLOCKED BY R4.

### R6 — Master Identity / snapshot_id
- Status: BLOCKED BY R5.

### R7 — Oracle L2 Coverage
- Status: BLOCKED BY R6.

### R8 — Governance Canonical State
- Status: BLOCKED BY R7.

## Quy tắc cập nhật file này

Mỗi session repair chỉ được cập nhật:
- trạng thái unit hiện tại;
- exact starting SHA;
- falsification evidence;
- touch-area;
- tests/evidence;
- repair SHA;
- verdict review.

Không được đánh dấu unit PASS/FROZEN dựa trên self-review của Claude. `FROZEN` cần Independent Review PASS.
