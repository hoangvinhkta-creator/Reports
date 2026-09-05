# S116 — Repair N-01/F-N02/F-N03: Journal Safety + Timeline Wording

Mode: SMALL CONTAINED FOLLOW-UP REPAIR — bounded trên đúng một `BASE_HEAD`.

Không merge canonical · không deploy · không mở UX mới · không mở F-04/F-05 ·
không chạm Brand/Advanced Analytics · không migration mới · không đổi thẩm
quyền Product Identity · không đổi công thức nghiệp vụ timeline.

## 0. Exact Gate

```text
SOURCE_BRANCH        = claude/reports-identity-timeline-repair-duxfzt
EXPECTED_SOURCE_HEAD = b5b41f1239f6bfd259eba17b6ac119e448cc0b83
OBSERVED HEAD        = b5b41f1239f6bfd259eba17b6ac119e448cc0b83  → KHỚP
WORKTREE             = sạch
GATE                 = PASS
```

## 1. N-01 — Ghi có điều kiện thay HEAD-rồi-PUT

`tools/storage/r2_store.put_json_if_absent` trước đây làm `head_object` rồi
`put_object` — hai request rời nhau, có khe hở lý thuyết cho hai lời viết
đồng thời tuyệt đối cùng khoá. Đã đóng bằng PUT có điều kiện đúng một request
(`put_object(..., IfNoneMatch="*")`); precondition thất bại (`PreconditionFailed`
/`412`/`ConditionalRequestConflict`) dịch thành `RunAlreadyExistsError`, và
`app/web/identity_journal.py` dịch tiếp thành `JournalWriteConflict` như cũ
(không đổi hợp đồng phía trên).

`tests/fixtures/fake_r2_client.py` mở rộng: `put_object` nhận `IfNoneMatch`,
kiểm-tra-rồi-ghi nguyên tử dưới một `threading.Lock`; thêm hook
`before_check[method]` để test gắn một `threading.Barrier` ép hai luồng cùng
đứng lại đúng ở điểm quyết định trước khi ghi — mô phỏng đúng hình dạng một
cuộc đua thật, không phó mặc lịch chạy luồng hệ điều hành.

Test mới: `tests/test_r2_store.py::test_two_threads_racing_the_same_key_exactly_one_wins`,
`tests/test_journal_conditional_write_and_pagination.py::test_two_writers_at_the_same_next_sequence_exactly_one_wins_one_conflicts`
(+ retry-sau-conflict, restart-giữ-cả-hai) và
`test_conditional_write_contention_never_reports_two_successes_for_one_slot`
(lặp 5 lần).

## 2. F-N02 — Phân trang liệt kê log

`identity_journal.pull()` từng gọi `r2_store.list_keys` — dừng ở `_SCAN_LIMIT`
(5000), khiến log vượt ngưỡng đó đọc thiếu event và `append()` kế tiếp ghi đè
lên một vị trí đã có (deadlock ghi vĩnh viễn tại N+1 = 5001). Thêm
`r2_store.list_all_keys` — phân trang triệt để qua `ContinuationToken`, không
giới hạn số lượng; `list_keys`/`list_run_keys_desc` (dùng cho lịch sử `runs/`)
giữ nguyên hành vi cũ, không bị ảnh hưởng. `FakeR2Client.list_objects_v2` sửa
để tôn trọng `MaxKeys`/`ContinuationToken` thật (trước đây trả hết trong một
lần gọi, không mô phỏng được phân trang).

Test mới: `test_pull_sees_all_events_beyond_the_old_5000_cap_and_append_continues`
(5003 event), `test_list_all_keys_returns_every_key_beyond_a_single_page`
(2500 key), và hai test lỗ hổng số thứ tự —
`test_a_gap_straddling_a_page_boundary_raises_mapping_integrity_error` (lỗ
hổng ngay sau ranh giới trang đầu ở 1000) và
`test_a_gap_well_inside_a_single_page_still_raises`.

## 3. F-N03 — Câu chữ chú thích biểu đồ

`revenue_timeline.CHART_NOTE` từng nói "Mỗi mốc chỉ lấy từ MỘT nguồn" — sai
với chính hành vi gộp quý/năm đã có từ trước (`§ Thẩm quyền được giải ở mức
THÁNG`, mẫu Quý 3 = 111tr gồm hai tháng sổ cũ + một tháng sổ nạp). Sửa thành:

> "Mỗi tháng chỉ lấy từ một nguồn có thẩm quyền; quý và năm có thể tổng hợp
> các tháng từ nhiều nguồn lịch sử/hiện tại."

Không thêm bộ chọn nguồn hay UI provenance mới — chỉ đổi câu chữ.
`MIXED_POINT_NOTE` (câu cho một mốc thô cụ thể gồm nhiều origin) đã đúng từ
trước, không đổi.

Test mới: `tests/test_identity_durability_and_timeline_aggregation.py::
test_f_n03_chart_note_resolves_authority_by_month_not_by_bar`.

## 4. Mutation Probes (đã chạy thật, không suy diễn)

| Probe | Mutation | Kết quả |
|---|---|---|
| M1 | Khôi phục HEAD-rồi-PUT | Race test FAIL — `['success', 'success']` (BOTH_SUCCESS) |
| M2 | (cùng mutation M1 — cả hai PUT "thành công") | 3 test race FAIL đồng loạt |
| M3 | Bỏ qua trang sau trang đầu trong `list_all_keys` | Test 5003-event và 2500-key FAIL (`1000 == 5003` / `1000 == 2500`) |
| M4 | Tắt kiểm lỗ hổng số thứ tự trong `pull()` | Cả hai test gap FAIL (`DID NOT RAISE`) |
| M5 | Khôi phục "Mỗi mốc chỉ lấy từ MỘT nguồn" | Test wording FAIL (`'mốc' in note`) |

Sau mỗi probe, mã nguồn được khôi phục lại đúng bản sửa (đối chiếu `diff` với
bản sao lưu = identical) trước khi chạy probe kế tiếp.

## 5. Test Evidence

```text
FULL_SUITE            = 2581 passed, 11 skipped
                        (trước sửa: 2569 passed, 11 skipped — +12 test mới,
                        -1 test tham số hoá không còn hợp lệ [head_object
                        qua put_json_if_absent], +1 test thay thế đúng chỗ
                        [head_object qua put_bytes])
GOLDEN                = 58 passed, 2 skipped (không đổi)
GOVERNANCE_VALIDATORS = validate_evidence PASS · validate_project_state PASS
                        · validate_structure PASS · validate_task_completion
                        PASS · validate_reference_integrity FAIL (3 tham
                        chiếu hỏng có sẵn từ trước trong
                        docs/tasks/TASK-REM-T06-repository-root-hygiene.md,
                        không do phiên này) · validate_refactor_preservation
                        cần tham số, không áp dụng
PRE_EXISTING_ENV_ISSUE = test_105d_boundaries.py::TestG25GoldenBaselineUnchanged::
                        test_protected_golden_artifacts_match_the_task_105e_review_base
                        FAIL cả trước và sau sửa — môi trường clone nông
                        thiếu object git `740f396a...`, không liên quan
                        N-01/F-N02/F-N03
NEW_MIGRATION          = NONE
ALEMBIC_HEAD           = 0007_employee_workspace (không đổi)
```

## 6. Files Changed

```text
tools/storage/r2_store.py                                — N-01 + F-N02
app/web/identity_journal.py                               — F-N02 (dùng list_all_keys)
                                                            + docstring
app/web/revenue_timeline.py                                — F-N03
tests/fixtures/fake_r2_client.py                           — conditional PUT
                                                            + pagination thật
                                                            + before_check hook
tests/test_r2_store.py                                     — test race + list_all_keys
                                                            + điều chỉnh test
                                                            head_object cũ
tests/test_journal_conditional_write_and_pagination.py     — MỚI: race + retry
                                                            + restart + pagination
                                                            + gap
tests/test_identity_durability_and_timeline_aggregation.py — test wording F-N03
```

## 7. Next Action

Mở Independent Review MỚI, độc lập, trên đúng FINAL_HEAD của nhánh này.
