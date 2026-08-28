# TASK-105D — INDEPENDENT IMPLEMENTATION REVIEW #2 (RC-1 VERIFICATION)

## Metadata

```text
review_id        : TASK-105D-IMPL-REVIEW-2
root_task        : TASK-105D
session          : S043 (2026-08-28)
review_branch    : review/task-105d-implementation-2
reviewed_target  : origin/task/task-105d-rc1
rc1_final_sha    : a09823506fc17b7903e44be848672a18f92bc6ee
original_impl_sha: e6252c06347ed5305fc32a77706a3a63f5a950cf
repair_impl_sha  : 1cc96a99638326513b26280b72bbeb3bce9d454d
review1_evidence : 58323e2e59382e2ce4816453cfaaa5d31deba3db
base_sha         : 222844dfb5cf576238fda4cc913ef2095789b4eb
Selected Profile : PRODUCT
Current Task Mode: MAJOR
Risk             : Effective Risk HIGH — max(Local Risk 4, Blast Radius 5)
Evidence Level   : E2
Executed By      : phiên Independent Implementation Review #2 (S043)
Timestamp        : 2026-08-28
```

Reviewer **không** phải tác giả implementation (`S040`) và **không** phải tác
giả repair (`S042`). Tuyên bố của phiên repair — `B-01 = CODE-LEVEL RESOLVED /
READY FOR INDEPENDENT RE-REVIEW` — được đối xử như một **giả thuyết cần chứng
minh hoặc bác bỏ**, không phải một kết luận được kế thừa. Toàn bộ số đo dưới
đây do phiên này tự thực thi; không có dòng nào sao chép từ `S040`, `S041` hay
`S042`.

Phiên này **KHÔNG repair**. `app/**`, `tests/**`, `config/**` = 0 dòng thay
đổi.

---

## 1. Pre-flight

```text
$ git rev-parse --abbrev-ref HEAD
review/task-105d-implementation-2

$ git rev-parse HEAD
a09823506fc17b7903e44be848672a18f92bc6ee

$ git rev-parse origin/task/task-105d-rc1
a09823506fc17b7903e44be848672a18f92bc6ee        <-- KHỚP

$ git status --porcelain
(rỗng — worktree sạch)
```

Ba object tham chiếu đều truy xuất được:

```text
e6252c06347ed5305fc32a77706a3a63f5a950cf : commit   (implementation gốc)
1cc96a99638326513b26280b72bbeb3bce9d454d : commit   (repair)
58323e2e59382e2ce4816453cfaaa5d31deba3db : commit   (Review #1 evidence)
```

Artifact Review #1 được đọc **nguyên văn** bằng
`git show 58323e2e:docs/reviews/TASK-105D-INDEPENDENT-IMPLEMENTATION-REVIEW-1.md`
— **không** merge nhánh review-1 vào RC-1 để đọc. Đọc toàn bộ `§13` (findings),
`§9`, `§10`, `§11`, `§16`, `§17`; không chỉ Final Report.

`branch_authority_check.sh` → `AUTHORITY_OK`; `DIVERGENCE =
INTEGRATION_DECISION_REQUIRED [loc>5000]` (`V4.1` §8 — quyết định thuộc Owner,
xem `§17` dưới đây).

**Lineage RC-1 đúng ba commit trên default `222844d`:**

```text
a098235  docs(TASK-105D): ghi head_sha của TASK-105D-RC-1 vào ledger
1cc96a9  fix(TASK-105D): RC-1 — khoá file liên-tiến-trình đóng B-01
e6252c0  TASK-105D — implementation candidate (32/32 frozen gate PASS)
```

---

## 2. Phạm vi diff repair — phân loại từng file

```text
$ git diff --stat e6252c06 1cc96a99
 PROJECT/PROJECT_PROGRESS.md                    | 102 ++-
 PROJECT/REVIEW_BUDGET_LEDGER.md                |  70 ++-
 app/modules/product/identity/store.py          | 367 +++++++++---
 docs/reviews/TASK-105D-RC-1-REPAIR-RECORD.md   | 550 ++++++++++++++++++
 docs/sessions/S042-task-105d-repair-cycle-1.md |  82 ++++
 tests/test_105d_interprocess_concurrency.py    | 567 ++++++++++++++++++
 6 files changed, 1664 insertions(+), 74 deletions(-)

$ git diff --stat 1cc96a99 a0982350
 PROJECT/REVIEW_BUDGET_LEDGER.md | 10 +++++---   (chỉ ghi head_sha)
```

| Loại | Nội dung |
|---|---|
| **A. Mã sửa chữa thật** | `app/modules/product/identity/store.py` — DUY NHẤT một file production |
| **B. Test mới** | `tests/test_105d_interprocess_concurrency.py` — 25 test, file mới |
| **C. Governance/evidence** | `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/REVIEW_BUDGET_LEDGER.md`, repair record, `S042` |

**Scope creep: KHÔNG.** Xác minh bằng liệt kê đường dẫn, không bằng lời:

```text
$ git diff --name-only e6252c06 a0982350 -- docs/tasks/ docs/spec/ config/ tools/ scripts/ pyproject.toml
(rỗng)
```

Khối gate đã freeze, data contract, config production, pipeline: **0 byte**.

Đúng trọng tâm mà brief dự kiến: production = `store.py`, test mới =
`tests/test_105d_interprocess_concurrency.py`.

### 2.1 Mọi dòng production đã đọc

Diff `store.py` gồm đúng bảy thay đổi hành vi:

1. `import fcntl` bọc `try/except ImportError`; `StoreLockUnavailableError` mới.
2. `self.lock_path = <log_path> + ".lock"`; `_log_offset` / `_log_lines` /
   `_thread_lock` (`RLock`) / `_lock_depth` mới.
3. `_transaction()` — contextmanager: `os.open(O_RDWR|O_CREAT|O_NOFOLLOW, 0o600)`
   → `flock(LOCK_EX)` → `_refresh_from_disk()` → thân → `LOCK_UN` → `close`,
   với `finally` lồng hai lớp; đếm `_lock_depth` để tái nhập thành no-op.
4. `_refresh_from_disk()` + `_consume()` thay `_load_log()`; đọc **tăng dần** từ
   `_log_offset` (log append-only ⇒ phần đã nạp là tiền tố).
5. `append()` bọc TOÀN BỘ bốn bước (idempotency 1 → authority → version →
   idempotency 2) trong `_transaction()`.
6. `_persist()` tách thành `_append_line()` (ghi vật lý duy nhất, đẩy
   `_log_offset` đúng số byte) + `rebuild_index()`; `rebuild_index()` công khai
   tự lấy khoá, `_write_index()` là phần thân.
7. `import_bundle()` dùng `_transaction()` cho CẢ bundle; đường ghi thứ hai
   `_persist_raw()` bị **xoá**.

Không có thay đổi nào ngoài bảy mục trên. Không có nới lỏng invariant, không có
`try/except` nuốt lỗi, không có đường tắt mới.

---

## 3. Tái lập `B-01` trên mã TRƯỚC repair — ĐỘC LẬP

Bộ đối kháng **riêng** của reviewer (`spawn`, không `fork`; store dựng SAU khi
tiến trình con khởi động ⇒ không kế thừa một mẩu state nào; đồng bộ bằng
`multiprocessing.Barrier`, **không** `sleep`). Worktree tách riêng tại
`e6252c06`.

**2 tiến trình HĐH, cùng file log, cùng khoá, `expected_version = 0`, 10 vòng:**

```text
REPO=<worktree @ e6252c0> n=2 rounds=10
     9 x applied=2 conflict=0 already=0 events=2 reopen=EXC
     1 x applied=1 conflict=0 already=0 events=2 reopen=EXC
       (+1 vòng có FileNotFoundError trên identity.index.json.tmp —
        race thứ hai trên đường os.replace của index)
  anomalous_rounds=10  /  10

Ví dụ nguyên văn:
  [('TRK-1','APPLIED',1), ('TRK-0','APPLIED',1)]  events=2
  reopen -> MappingIntegrityError: INV-33: bản ghi 426ff36c… cho khoá
  'REPORTS_SALES\x1fNồi chiên không dầu tranh chấp R2' khai supersedes=None
  nhưng bản ghi trước đó là '64eacaad…'
```

**4 tiến trình, 10 vòng (pre-repair):**

```text
     4 x applied=1 events=4 reopen=EXC
     4 x applied=2 events=4 reopen=EXC
     2 x applied=3 events=4 reopen=EXC
  anomalous_rounds=10 / 10   (0 vòng nào raise MappingVersionConflict)
```

**Cùng `client_request_id`, 2 tiến trình, 10 vòng (pre-repair):**

```text
     9 x applied=2 events=2 reopen=EXC     <-- INV-68 cũng bị phá qua biên tiến trình
```

**Kết luận `§4`:** `B-01` **ĐƯỢC TÁI LẬP ĐỘC LẬP**. Trên mã trước repair:
writer A = `APPLIED` **và** writer B = `APPLIED`; log kết thúc với hai (hoặc
tới bốn) bản ghi `CONFIRMED` độc lập cho cùng một khoá; mở lại store từ đĩa
raise `MappingIntegrityError` — **10/10 vòng ở mọi cấu hình**. Không có vòng
nào phục hồi được. Mô tả của Review #1 khớp chính xác.

Ghi nhận thêm — một hệ quả Review #1 không nêu tường minh: pre-repair còn có
race thứ hai trên `os.replace(temp, index_path)` (`FileNotFoundError` khi hai
tiến trình cùng ghi `identity.index.json.tmp`). Khoá của RC-1 đóng luôn cả nó
(xem `§10`).

---

## 4. Cùng một race trên RC-1

Cùng bộ đối kháng, cùng tham số, chạy tại `a0982350`:

```text
REPO=RC-1  n=2  rounds=30  request_id khác nhau
    30 x applied=1 conflict=1 already=0 events=1 reopen=OK
  anomalous_rounds=0

REPO=RC-1  n=4  rounds=25
    25 x applied=1 conflict=3 already=0 events=1 reopen=OK
  anomalous_rounds=0

REPO=RC-1  n=8  rounds=15
    15 x applied=1 conflict=7 already=0 events=1 reopen=OK
  anomalous_rounds=0
```

Trong **70 vòng / 190 tiến trình HĐH**: đúng **1** writer thắng, mọi writer cũ
còn lại raise `MappingVersionConflict`, **log vật lý luôn đúng 1 dòng**, và mở
lại store bằng một tiến trình `spawn` MỚI luôn đọc được (`reopen=OK`).

Kiểm nội dung log vật lý sau tranh chấp (không chỉ giá trị trả về):

```text
persisted_event_count = 1 ở cả 70 vòng
reopen: revision = 1, active mapping = (<mã của người thắng>, version 1, CONFIRMED)
```

Ngữ nghĩa khớp canonical: `1 × APPLIED` + `n−1 × MappingVersionConflict` cho
cùng `expected_version` với `client_request_id` khác nhau.

---

## 5. Cơ chế khoá — có thật ở mức HĐH không?

Đọc mã, rồi **đo**, không chỉ đọc.

```text
app/modules/product/identity/store.py:364   os.open(lock_path, O_RDWR|O_CREAT|O_NOFOLLOW, 0o600)
app/modules/product/identity/store.py:367   fcntl.flock(fd, fcntl.LOCK_EX)
app/modules/product/identity/store.py:370   self._refresh_from_disk()     <-- TRONG khoá
app/modules/product/identity/store.py:371   yield                          <-- thân giao dịch
app/modules/product/identity/store.py:374   fcntl.flock(fd, fcntl.LOCK_UN) <-- finally
app/modules/product/identity/store.py:376   os.close(fd)                   <-- finally ngoài
```

`grep -rn "fcntl\|flock" app/` chỉ trả kết quả trong `store.py` — trước repair
trả **0 kết quả**.

| Tiêu chí `§6` | Kết quả | Bằng chứng |
|---|---|---|
| Khoá liên-tiến-trình HĐH thật | PASS | `flock` của nhân, đo bằng blocking thật (dưới) |
| `LOCK_EX` (độc quyền) | PASS | dòng 367, không có `LOCK_SH` ở đâu |
| Khoá lấy TRƯỚC khi nạp lại quyền uy | PASS | 367 trước 370 |
| Khoá giữ suốt kiểm version | PASS | `_require_version` gọi từ `_append_mapping_command`, nằm trong `yield` |
| Khoá giữ suốt append + `fsync` | PASS | `_append_line` (`write`+`flush`+`fsync`) nằm trong `yield` |
| Giải phóng an toàn với exception | PASS | `finally` lồng hai lớp; đo ở `§12` |
| Khoá process-local là đủ? | KHÔNG — và RC-1 không dựa vào nó | `RLock` chỉ tuần tự hoá luồng của cùng instance |
| Khoá quanh riêng `write()`? | KHÔNG — biên là giao dịch | `append()` bọc CẢ bốn bước |
| Kiểm version từ bộ nhớ cũ trước khoá? | KHÔNG | không còn đường nào kiểm version ngoài `_transaction` |

**Đo mutual exclusion thật** — một tiến trình giữ `_transaction()`, một tiến
trình khác gọi `store.append()` thật:

```text
holder  : "HOLDING"           (đang trong _transaction)
probe   : "BUILT"             (đã import xong, sắp dựng store)
probe còn bị chặn sau 2,0 s : True        <-- khoá là THẬT, không phải trang trí
holder SIGKILL rc=-9
probe   : "DONE APPLIED"                   <-- nhân trả khoá ⇒ probe đi tiếp
```

Đây là điểm phân biệt quan trọng: probe bị chặn ở **đường ghi production**, không
phải ở một `flock` thủ công trong test.

---

## 6. Sidecar `<log_path>.lock` — TOCTOU và vòng đời

Lý do dùng sidecar được kiểm chứng, không chỉ chấp nhận: `rebuild_index()` thay
index bằng `os.replace` ⇒ **đổi inode**; khoá trên một inode bị thay giữa chừng
mất tác dụng loại trừ. Log thì không bị replace, nhưng đặt khoá trên log lại
trộn lẫn hai vai trò. Sidecar tạo một lần và không bao giờ bị xoá/thay.

| Kiểm | Kết quả | Bằng chứng |
|---|---|---|
| inode khoá ổn định | PASS | inode không đổi qua nhiều `append` + `rebuild_index` (test của tác giả + đo lại ở `§10`) |
| lock file bị thay giữa giao dịch | KHÔNG — không có `unlink`/`os.replace`/`rename` nào chạm `lock_path` | `grep` toàn `store.py` |
| race unlink/recreate | KHÔNG TỒN TẠI | không có đường xoá |
| `O_NOFOLLOW` | PASS | symlink → `OSError(ELOOP=40)`, **0 dòng log được ghi** |
| Quyền | PASS | `0o600` (đo trên file thật) |
| Dẫn xuất đường dẫn | PASS | `log_path.with_name(name + ".lock")` — cùng thư mục, cùng filesystem |
| Lock file đã tồn tại | PASS | `O_CREAT` không `O_EXCL` ⇒ dùng lại, đúng ý đồ |
| Sau khi tiến trình chết | PASS | `§12` — nhân trả khoá, `LOCK_NB` lấy được ngay |

Đo symlink (đây là cửa hậu đưa `B-01` quay lại: hai tiến trình khoá hai inode
khác nhau):

```text
$ ln -s attacker.lock identity.log.jsonl.lock  &&  store.append(...)
refused: OSError 40 [Errno 40] Too many levels of symbolic links
log written? False
```

**TOCTOU:** không tìm thấy. Đường `mkdir → os.open(O_CREAT|O_NOFOLLOW) → flock`
không có cửa sổ nào mà quyết định ghi được đưa ra ngoài khoá; `lock_path` được
tính một lần trong `__init__` và là thuộc tính chỉ-đọc trên thực tế.

Hạn chế **được ghi rõ, không phải mới**: `flock` không loại trừ qua NFS ở nhiều
cấu hình. Nằm đúng trong phạm vi "nhiều máy = Phase 2" mà data contract `§11.1`
đã tuyên bố; không phải hạn chế do RC-1 tạo ra.

---

## 7. Nạp lại trong khoá (`_refresh_from_disk`)

`_refresh_from_disk()` được gọi **sau** `flock(LOCK_EX)` và **trước** `yield`,
tức trước mọi quyết định phụ thuộc version. Không tồn tại đường nào gọi nó
ngoài khoá (`grep`: 1 lời gọi duy nhất, dòng 370).

`_log_offset` — log append-only ⇒ phần đã nạp là **tiền tố** của file, nên đọc
từ `_log_offset` là hợp lệ; `_append_line()` đẩy offset đúng số byte vừa ghi,
nên tiến trình không đọc lại chính dòng mình vừa ghi thành event thứ hai.

Các case đối kháng, đo trên RC-1:

| Case | Kết quả |
|---|---|
| Tiến trình khác append 1 event hợp lệ | Nạp lại, thấy version thật, `MappingVersionConflict` — `§9` |
| Tiến trình khác append NHIỀU event | `b.current_revision()` 0 → 2 sau khi vào khoá; không rewind |
| Log co lại | `MappingIntegrityError: log co lại từ 1662 xuống 0 byte — vi phạm append-only (INV-67)` |
| Dòng mới sai khuôn (không phải JSON) | `MappingIntegrityError: dòng 2 không phải JSON hợp lệ` |
| Bản ghi cuối ghi dở (`{"event_id": "par`) | `MappingIntegrityError` — fail closed, **không** đọc thành nửa state |
| State cũ trong bộ nhớ | Không còn đường nào quyết định từ bộ nhớ cũ (`§9`) |

Store **không** ra quyết định mutation từ bộ nhớ cũ. Xác nhận.

Một khiếm khuyết mới tìm thấy ở đúng đường này — xem `H2-01` (`§15`): khi
`_consume()` gặp lỗi giữa chunk, nó đã mutate `_events`/`_raw_records` nhưng
`_log_offset` chưa tiến, nên mỗi lần thử lại sẽ nạp trùng phần đã nạp. Fail
closed trên đĩa ở mọi lần, nên phân loại `HARDENING`, không `BLOCKING`.

---

## 8. Mọi đường ghi — liệt kê ĐỘC LẬP, không tin con số "ba"

Quét tĩnh toàn `app/`, không đọc lời tác giả:

```text
$ grep -rn "open(\|write_text\|write_bytes\|os.replace\|os.remove\|unlink\|shutil\." \
        app/ --include=*.py | grep -v "identity/store.py"
app/modules/config/loader.py:23:    with open(path, "r", encoding="utf-8") as handle:
```

Đúng **một** kết quả ngoài `store.py`, và nó là `"r"` — chỉ đọc. Nghĩa là
`store.py` là module DUY NHẤT trong `app/` ghi bất cứ thứ gì xuống đĩa.

Trong `store.py`, mọi đường đổi state bền vững:

| Đường ghi | Vào khoá? | Bằng chứng |
|---|---|---|
| `append()` (create / confirm / correct / bootstrap / mark-stale / reject / cross-system) | CÓ | `with self._transaction():` bọc toàn thân |
| `import_bundle()` | CÓ | `with store._transaction():` bọc CẢ bundle |
| `rebuild_index()` (công khai) | CÓ | `with self._transaction(): self._write_index()` |
| `_append_line()` (private) | Chỉ gọi từ trong khoá | 2 lời gọi: `_persist()`, `import_bundle()` — cả hai trong khoá |
| `_write_index()` (private) | Chỉ gọi từ trong khoá | 1 lời gọi: `rebuild_index()` |
| `_persist_raw()` | **ĐÃ XOÁ** — đây từng là đường ghi thứ hai bỏ ngoài khoá |
| Ghi thẳng file từ nơi khác | KHÔNG TỒN TẠI | quét tĩnh ở trên |

Các đường ghi mà brief yêu cầu tìm riêng:

```text
append                        -> append()                       KHOÁ
import                        -> import_bundle()                KHOÁ
rebuild                       -> rebuild_index()                KHOÁ
correction (CORRECT_MAPPING)  -> append()                       KHOÁ
confirmation                  -> append()                       KHOÁ
rejection (RejectCandidate)   -> append() -> _apply_rejection    KHOÁ
cross-system mutation         -> append() -> _append_cross_...   KHOÁ
helper/private bypass         -> KHÔNG CÒN (_persist_raw đã xoá)
direct file write             -> KHÔNG TỒN TẠI
```

**Historical registry mutation** (`HistoricalConfirmedRegistry.append`,
`registry.py:200`) là ngoại lệ duy nhất và cần nói chính xác: registry
**hoàn toàn trong bộ nhớ** — `grep` cho `log_path`/`open(`/`write` trong
`registry.py` trả 0 kết quả. Nó không có state bền vững để tranh chấp, nên nó
không phải một "đường ghi bỏ ngoài khoá"; nó nằm ngoài phạm vi `B-01`. Ghi lại
tường minh làm re-trigger cho phiên đầu tiên cấp persistence cho registry.

**Kết luận `§9`: 0 đường ghi bền vững nào bypass được biên giao dịch.**

---

## 9. Hai instance độc lập (`§10`)

Không tái tạo `B`; `B` giữ nguyên ảnh chụp cũ.

```text
both observe version N:              0   0
A append expected_version=0    ->  APPLIED  new_version 1
B (KHÔNG tái tạo) vẫn tin revision =  0
B append expected_version=0    ->  MappingVersionConflict     <-- từ chối
B sau khi nạp lại TRONG khoá, revision = 1
log lines sau lần từ chối     :  1                            <-- không ghi gì
B retry expected_version=1     ->  APPLIED  new_version 2
log lines                      :  2   | bản ghi cuối supersedes != None : True
reopen mới: revision 2 | active = TRK-B CONFIRMED v2
```

Canonical: từ chối trước khi ghi, không ghi gì, không tăng version (`INV-59`);
reload + reconcile rồi mới ghi (`INV-60`); bản ghi mới khai `supersedes`
(`INV-33`).

---

## 10. Stress đa tiến trình + >2 contender

Tổng hợp toàn bộ vòng đã chạy trên RC-1 (mỗi vòng = thư mục log sạch, tiến
trình `spawn` mới, barrier thật, không `sleep`):

| Kịch bản | Vòng | Winner | Conflict | ALREADY_APPLIED | Event trên đĩa | Reopen | Bất thường |
|---|---|---|---|---|---|---|---|
| 2 tiến trình, request_id khác | 30 | 1 | 1 | 0 | 1 | OK | 0 |
| 4 tiến trình, request_id khác | 25 | 1 | 3 | 0 | 1 | OK | 0 |
| 8 tiến trình, request_id khác | 15 | 1 | 7 | 0 | 1 | OK | 0 |
| 2 tiến trình, CÙNG request_id | 25 | 1 | 0 | 1 | 1 | OK | 0 |
| 4 tiến trình, CÙNG request_id | 15 | 1 | 0 | 3 | 1 | OK | 0 |
| append×2 vs `rebuild_index`×2 | 15 | 1 | 1 | 0 | 2 | OK | 0 |
| `rebuild_index`×4 | 10 | — | — | — | 1 | OK | 0 |
| **Tổng** | **135** | | | | | | **0** |

```text
Phân bố người thắng      : cả hai/mọi tiến trình đều thắng ở các vòng khác nhau
                           (tranh chấp thật, không phải thứ tự cố định)
Conflict count           : đúng n-1 ở MỌI vòng request_id khác nhau
Kết cục bất ngờ          : 0
Flake / timeout          : 0   (không vòng nào chạm timeout 180 s)
Đồng bộ                  : multiprocessing.Barrier — KHÔNG sleep
```

`>2 contender` (4 và 8 tiến trình, cùng version, cùng khoá): đúng **một**
mutation hợp lệ; mọi writer cũ còn lại thất bại theo đúng ngữ nghĩa conflict
canonical; mở lại sau đó luôn toàn vẹn. Đây là **bằng chứng review**, không
commit thành test production.

---

## 11. Idempotency và request-id khác nhau dưới tranh chấp

**Cùng `client_request_id`, đồng thời** (`§13` của brief):

```text
n=2, 25 vòng : 25 x  applied=1  already=1  conflict=0  events=1  reopen=OK
n=4, 15 vòng : 15 x  applied=1  already=3  conflict=0  events=1  reopen=OK
```

Phân biệt canonical được giữ đúng, không bị bịa: kẻ đến sau nạp lại log **trong
khoá**, thấy `client_request_id` đã dùng, và thoát qua **lớp idempotency 1**
(`INV-68` → `ALREADY_APPLIED`), **không** qua version conflict. Đó đúng là thứ
tự kiểm mà `§11.3` của data contract quy định (idempotency lớp 1 **trước**
version), nên khoá không đổi ngữ nghĩa sẵn có — nó chỉ làm cho ngữ nghĩa ấy
thi hành được qua biên tiến trình. Số event bền vững kiểm trực tiếp trên file:
**1**.

**`client_request_id` khác nhau, cùng `expected_version`, cùng identity**
(`§14`): 70 vòng ở `§10` — đúng **một** lần ghi quyền uy; writer thứ hai
**không** append (log vật lý = 1 dòng ở mọi vòng).

---

## 12. Tiến trình chết khi đang giữ khoá + đường lỗi

**SIGKILL khi đang giữ `_transaction()`** (không phải một `flock` thủ công):

```text
holder giữ _transaction()                      -> "HOLDING"
store.append() thật ở tiến trình khác          -> bị chặn, còn chặn sau 2,0 s
SIGKILL holder (rc = -9; không finally nào chạy trong tiến trình con)
append bị chặn                                 -> DONE APPLIED
log lines 1 -> 2
LOCK_NB trên lock file sau đó                  -> lấy được ngay (không stale lock)
reopen store                                   -> revision = 2
thao tác hợp lệ kế tiếp                        -> APPLIED, version 3
```

Tách bạch đúng hai bảo đảm như brief yêu cầu:

```text
BẢO ĐẢM TRẢ KHOÁ        : ĐẠT — nhân trả flock khi tiến trình chết/fd đóng,
                          kể cả SIGKILL. Không có stale lock, không deadlock.
BẢO ĐẢM GHI DỞ (durability) : KHÁC — xem §13. flock không làm cho một lần
                          append JSONL bị ngắt trở nên phục hồi được.
```

Trong lần đo này không có ghi dở (holder chết trước khi vào thân giao dịch), nên
store còn dùng được — đúng như phát biểu của brief `§15`.

**Đường lỗi — giải phóng khoá** (mỗi case: gây lỗi, rồi thực hiện một thao tác
hợp lệ để chứng minh không deadlock):

| Đường lỗi | Exception | Khoá trả? | Thao tác hợp lệ sau đó |
|---|---|---|---|
| Version conflict | `MappingVersionConflict` | CÓ | APPLIED |
| Authority rejection (`INV-01`) | `SimilarityAuthorityError` | CÓ | APPLIED, log vẫn rỗng trước đó |
| Log sai khuôn | `MappingIntegrityError` | CÓ | nổ cùng lỗi miền, không treo |
| Log co lại | `MappingIntegrityError` | CÓ | không treo |
| Lỗi ghi index (`os.replace` → `ENOSPC`) | `OSError` | **CÓ** (đo bằng `LOCK_NB`) | APPLIED, version 3 |
| Lỗi rebuild/index trong `_persist` | như trên | CÓ | reopen revision đúng |

Đo trực tiếp trên case khó nhất (lỗi giữa `_persist`):

```text
append raised: OSError [Errno 28] No space left on device
log lines on disk: 2                 <-- event ĐÃ commit
lock free after failure: YES         <-- không deadlock
subsequent valid op: APPLIED 3
fresh reopen revision: 3
```

Ghi lại tường minh: event **đã** bền vững nhưng caller nhận exception. Đây là
hình dạng có SẴN từ trước repair (`_persist` cũ cũng ghi rồi mới
`rebuild_index`), không phải hồi quy của RC-1 — xem `H2-03`.

---

## 13. Ghi dở / durability — biên còn lại, đánh giá theo contract

Câu hỏi đúng không phải "RC-1 có phục hồi được log hỏng không?" mà "**canonical
contract yêu cầu gì?**". Contract nói:

> `INV-62` Atomic write. Append một event = một lần ghi + fsync. […] Một lần
> ghi bị ngắt **KHÔNG được để lại state đọc được nhưng sai**.

Contract yêu cầu **fail closed**, KHÔNG yêu cầu recovery. Đo trên RC-1:

| Tình huống | Instance đang sống | Store mở mới |
|---|---|---|
| Dòng JSON cuối bị cắt (`{"event_id": "par`) | `MappingIntegrityError` | `MappingIntegrityError` |
| Dòng rác cuối (`not json`) | `MappingIntegrityError` | `MappingIntegrityError` |
| Log bị truncate về rỗng | `MappingIntegrityError` (`INV-67`) | mở được, revision 0 |
| `fsync` | có, mỗi event, trước khi `_append_line` trả về | — |

Đánh giá:

- **`INV-62` được thoả.** Không có đường nào cho ra "đọc được nhưng sai": bản
  ghi cuối hỏng làm mọi phép đọc nổ, không cho ra nửa state.
- **Thất bại là VĨNH VIỄN** với một bản ghi cuối hỏng, và `INV-67` (không
  DELETE) không để lại đường phục hồi trong contract. Đây là một khoảng trống
  contract **có sẵn**, không do RC-1 tạo, và contract hiện hành **không** đòi
  recovery ⇒ theo đúng chỉ dẫn `§17` của brief, **KHÔNG** phân loại `BLOCKING`.
- **Truncate về rỗng**: instance đang sống phát hiện (`INV-67`), nhưng một store
  mở mới thấy một log rỗng hợp lệ và trả revision 0 — mất dữ liệu im lặng trước
  một tác nhân ngoài store. Ngoài mô hình đe doạ của `B-01` (không tiến trình
  nào của hệ thống truncate log), ghi lại làm `H2-05`.

**Tách bạch dứt khoát:** `B-01` là **concurrency**, và nó đã đóng (`§16`).
Durability hardening là **việc khác**, vẫn mở, không chặn RC-1.

---

## 14. `rebuild_index` — tương tác với `os.replace`

Đây là lý do RC-1 chọn sidecar, nên phải kiểm chính nó.

```text
[append x2 vs rebuild_index x2] — 15 vòng, tiến trình HĐH thật:
    15 x  appends_applied=1  conflicts=1  rebuild_ok=2  log=2
          idx_rev=2  idx_consistent=True  reopen=OK

[rebuild_index x4, không append] — 10 vòng:
    10 x  rebuild_ok=4  log=1  idx_rev=1  idx_consistent=True  reopen=OK
```

`idx_consistent` = `index["revision"] == số dòng log`. **25/25 vòng nhất quán**,
0 vòng mất state, 0 vòng index lệch log, 0 `FileNotFoundError` trên
`.tmp` (pre-repair có race này — `§3`). Khoá sidecar thật sự bảo vệ được qua
biên thay-inode của index, đúng như lý do đưa ra.

Ghi nhận: `rebuild_index()` công khai lấy khoá; gọi từ `_persist()` thì
`_lock_depth` biến nó thành no-op — không tự khoá chính mình trên fd thứ hai.
Đã kiểm bằng 135 vòng ở `§10` (mọi `append` đều đi qua đường tái nhập này) —
0 deadlock.

---

## 15. Nền tảng / khả dụng của khoá

```text
$ (fcntl := None) ; store(log_path=...).append(cmd)
StoreLockUnavailableError: …/identity.log.jsonl.lock: nền tảng không cung cấp
fcntl.flock; store có persistence KHÔNG được chạy không khoá (INV-59 sẽ không
thi hành được qua biên tiến trình)
log written? False                      <-- fail closed, KHÔNG hạ cấp âm thầm

$ store thuần bộ nhớ (log_path=None) không có fcntl
APPLIED                                 <-- không cần khoá, không bị ảnh hưởng
```

Đường import: `try: import fcntl / except ImportError: fcntl = None`, rồi
`if fcntl is None: raise StoreLockUnavailableError` **chỉ khi** `lock_path is
not None`. Không có nhánh nào chạy persistence mà không khoá. Xác nhận.

Tính khả chuyển: POSIX-only. `ADR-101`/`§11.1` tuyên bố runtime Phase 1 là một
máy; repo không tuyên bố hỗ trợ Windows ở đâu, và test
`test_the_repository_runtime_provides_a_real_file_lock` khẳng định
`os.name == "posix"` như một điều kiện runtime. Vì contract **không** đặc tả
portability, phân loại tương xứng: **không phải finding**, chỉ là một giả định
runtime nay được khẳng định bằng test — chặt hơn trước repair, không lỏng hơn.

---

## 16. Hiệu năng

Đo trên cùng máy, cùng phiên, cùng fixture; ba cấu hình để tách chi phí khoá
khỏi chi phí index có sẵn:

| n append | RC-1 log+index | pre-repair log+index | RC-1 log only | RC-1 in-memory |
|---|---|---|---|---|
| 100 | 0,210 s | 0,217 s | 0,129 s | 0,057 s |
| 200 | 0,590 s | 0,626 s | 0,335 s | 0,174 s |
| 400 | 1,995 s | 1,946 s | 1,080 s | 0,766 s |
| 800 | **6,795 s** | **6,969 s** | 3,931 s | 2,785 s |

```text
Chi phí khoá mới        : KHÔNG ĐO ĐƯỢC trên nhiễu (RC-1 nhanh hơn 2,5 % ở
                          n=800; chậm hơn 2,5 % ở n=400 — hai chiều ⇒ nhiễu)
Chi phí index/rebuild   : có sẵn, ~ 42 % thời gian ở n=800 (so cột 1 vs 3)
Siêu tuyến tính còn lại : có sẵn ở CẢ cột in-memory (2,785 s) ⇒ nguồn gốc là
                          phép chiếu lại toàn bộ event ở mỗi append, KHÔNG
                          phải khoá và KHÔNG chỉ là rebuild_index
```

`H-04` **không** được mở lại chỉ vì JSONL vẫn siêu tuyến tính — đúng chỉ dẫn
`§20` của brief. `H-04` giữ nguyên `HARDENING`, và RC-1 **không** làm nó xấu đi.

Ghi chú đối chiếu: bản ghi repair báo "+4…9 %". Phép đo độc lập của phiên này
không tái lập được mức đó — chênh lệch nằm trong nhiễu hai chiều. Không phải
mâu thuẫn thực chất (cả hai đều kết luận "không hồi quy vật chất"), nên không
mở finding; ghi lại để số liệu của hai artifact không bị đọc là xung đột.

---

## 17. 32 frozen check + A–T + regression + validator

### 17.1 Frozen hash

```text
$ sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md | wc -c
57614
$ sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md | sha256sum
0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877  -

$ diff <(git show be835b1:docs/tasks/…-resolver.md | sed -n '567,2295p') \
       <(sed -n '631,2359p' docs/tasks/…-resolver.md)
(không có khác biệt)

$ git diff --name-only e6252c06 a0982350 -- docs/tasks/ docs/spec/
(rỗng)
```

**KHỚP TUYỆT ĐỐI với giá trị kỳ vọng.** Khối gate 0 byte thay đổi bởi RC-1.
Phiên này KHÔNG sửa khối gate.

### 17.2 32 frozen check — thực thi ĐỘC LẬP tại `a0982350`

Không sao chép `S040`/`S041`/`S042`; mỗi dòng chạy lại bằng
`python3 -m pytest <ref> -q`.

```text
CHECK-105D-01 PASS  7 passed      CHECK-105D-17 PASS  4 passed
CHECK-105D-02 PASS  5 passed      CHECK-105D-18 PASS  5 passed
CHECK-105D-03 PASS  3 passed      CHECK-105D-19 PASS  4 passed
CHECK-105D-04 PASS  1 passed      CHECK-105D-20 PASS  7 passed
CHECK-105D-05 PASS  3 passed      CHECK-105D-21 PASS  8 passed
CHECK-105D-06 PASS  5 passed      CHECK-105D-22 PASS  3 passed
CHECK-105D-07 PASS  3 passed      CHECK-105D-23 PASS  4 passed
CHECK-105D-08 PASS  3 passed      CHECK-105D-24 PASS  1 passed
CHECK-105D-09 PASS  6 passed      CHECK-105D-25 PASS  3 passed
CHECK-105D-10 PASS  9 passed      CHECK-105D-26 PASS  1 passed
CHECK-105D-11 PASS  1 passed      CHECK-105D-27 PASS  1 passed
CHECK-105D-12 PASS  6 passed      CHECK-105D-28 PASS 11 passed
CHECK-105D-13 PASS  4 passed      CHECK-105D-29 PASS  5 passed
CHECK-105D-14 PASS  3 passed      CHECK-105D-30 PASS  5 passed
CHECK-105D-15 PASS  2 passed      CHECK-105D-31 PASS  8 passed
CHECK-105D-16 PASS  3 passed      CHECK-105D-32 PASS  8 passed
-----------------------------------------------------------------
REQUIRED 32 / 32    PASS 32    FAIL 0    NOT_TESTED 0
```

Số test mỗi dòng **giống hệt** bản ghi `S040` ⇒ RC-1 không hồi quy kết quả
32/32 trước đó, và cũng không thay đổi phạm vi bất kỳ gate nào.

Lưu ý E2 tái lập: `CHECK-105D-26`/`-27` phải chạy với
`tests/test_105d_resolution.py::…`, không phải `test_105d_boundaries.py` như
bảng trong Gate Execution Record gợi ý — `H-03` của Review #1 **VẪN OPEN**
(`§18`).

### 17.3 A–T — truy vết ĐỘC LẬP

```text
A PASS  1   F PASS  1   K PASS  6   P PASS  9
B PASS  2   G PASS  5   L PASS  5   Q PASS  7
C PASS  3   H PASS 12   M PASS  1   R PASS  1
D PASS  2   I PASS  1   N PASS  1   S PASS 13
E PASS  4   J PASS  8   O PASS  1   T PASS 19
------------------------------------------------
A–T : 20 / 20 PASS
```

`N` (concurrency) được phiên này **không** chấp nhận chỉ bằng
`TestG20…::test_part_a_…` (fixture một instance): nó được kiểm bổ sung bằng
135 vòng tranh chấp đa tiến trình ở `§10`. `N` PASS ở cả hai mức.

### 17.4 Regression

```text
                       base 222844d   e6252c0   RC-1 a098235   kỳ vọng
TASK-105D targeted        —            174        199          199   OK
Golden                    —          58 p/2 s   58 p/2 s   58 p/2 s  OK
Full suite              756/11       930/11     955/11       955/11  OK
delta test mới             —            —          +25          +25  OK
skipped                   11           11          11           11   OK
regression                 —             0           0            0  OK
```

Delta xác minh **hai chiều** trên worktree tách riêng tại `e6252c0`:
930 → 955 = +25; targeted 174 → 199 = +25; và file test mới đếm đúng
`25 passed`. Không có test nào biến mất, không có test nào chuyển thành skip.

### 17.5 Validator

```text
validate_structure           : PASS  (21 required path)
validate_project_state       : PASS
validate_evidence            : PASS  (88 REQUIRED PASS record)
validate_task_completion     : PASS  (6 DONE task)
validate_reference_integrity : FAIL  — 4 reference
```

So với baseline canonical (đo lại trên worktree riêng, không tin trí nhớ):

```text
base 222844d  : 3 unresolved  (TASK-REM-T06: /README.md, CODE_OF_CONDUCT.md,
                               CONTRIBUTING.md)
e6252c0       : 3 unresolved  (giống hệt)
RC-1 a098235  : 4 unresolved  (3 như trên + 1 MỚI)
                MỚI: docs/reviews/TASK-105D-RC-1-REPAIR-RECORD.md
                     -> docs/reviews/TASK-105D-INDEPENDENT-IMPLEMENTATION-REVIEW-1.md
```

**Có ĐÚNG MỘT lỗi reference mới do RC-1 tạo ra.** Xem `H2-02`.

Nhánh review này giữ nguyên con số đó: sau khi ghi artifact `S043`,
`validate_reference_integrity` vẫn báo **4** (không phải 5+). Reviewer cố ý
không lặp lại chính khiếm khuyết mình vừa ghi nhận — mọi tham chiếu trong hai
artifact của phiên đều là đường dẫn đầy đủ tính từ repository root, và artifact
Review #1 được dẫn bằng SHA (`git show 58323e2e:…`) trong khối `text`, không
bằng một đường dẫn inline không phân giải được.

---

## 18. Anti-tautology — test mới có thật sự bắt được `B-01` không?

Copy nguyên văn `tests/test_105d_interprocess_concurrency.py` sang worktree
tại `e6252c06` (mã TRƯỚC repair) rồi chạy:

```text
19 failed, 6 passed
```

Tác giả báo `18 failed`. Chênh 1 và điều đó được brief `§21` cho phép (môi
trường khác — phiên này chạy `pytest 9.1.1`). Quan trọng hơn con số: **những
test nào** fail. 19 test fail bao gồm TOÀN BỘ các test chạm đúng khiếm khuyết:

```text
FAILED TestInterProcessVersionRace::test_exactly_one_writer_wins_and_the_stale_one_is_refused
FAILED TestInterProcessVersionRace::test_the_stale_writer_appends_nothing
FAILED TestInterProcessVersionRace::test_repeated_contention_never_produces_two_winners
FAILED TestStoreStaysValidAfterContention::…reopened_from_disk_reads_one_confirmed_mapping
FAILED TestStoreStaysValidAfterContention::test_no_permanent_integrity_error_…
FAILED TestStoreStaysValidAfterContention::test_the_store_still_accepts_the_next_valid_write
FAILED TestTwoInstancesInOneProcess::…refreshes_under_lock_and_sees_the_stale_version
FAILED TestTwoInstancesInOneProcess::test_the_refused_instance_can_reconcile_and_then_succeed
FAILED TestTwoInstancesInOneProcess::test_a_stale_instance_never_rewinds_the_log
FAILED TestIdempotencyUnderContention::…same_client_request_id_from_two_processes_writes_one_event
FAILED TestAuditUnderContention::test_the_refused_writer_leaves_no_audit_evidence
FAILED TestLockReleaseOnFailurePaths::…malformed_log_line_releases_the_lock_…
FAILED TestLockReleaseOnFailurePaths::test_a_shrinking_log_is_refused_…
FAILED TestEveryWritePathIsLocked::  (5 test)
FAILED test_the_repository_runtime_provides_a_real_file_lock
```

**Không phải tautology.** Bộ test bắt đúng defect gốc, không chỉ bắt sự vắng
mặt của thuộc tính `lock_path`.

6 test PASS trên mã hỏng, phân tích từng cái:

| Test PASS trên mã hỏng | Có chính đáng không |
|---|---|
| `test_a_cross_process_retry_returns_the_earlier_result` | CÓ — tuần tự, không tranh chấp; không phải bộ dò `B-01` |
| `test_a_version_conflict_releases_the_lock` | CÓ — pre-repair không có khoá nên trivially pass |
| `test_an_authority_rejection_releases_the_lock` | CÓ — như trên |
| `test_a_hundred_sequential_appends_stay_within_a_sane_budget` | CÓ — benchmark chống thoái hoá |
| `test_a_killed_holder_leaves_no_stale_lock` | MỘT PHẦN — nó dùng một `flock` **thủ công** trong test, nên nó chứng minh hành vi của **nhân**, không chứng minh **store** có chờ khoá đó. Phiên này bù bằng phép đo `§12` (probe là `store.append()` thật) |
| `test_both_orderings_actually_occur_across_rounds` | **KHÔNG** — xem `H2-04` |

---

## 19. Chất lượng 25 test mới — rà từng tiêu chí

| Tiêu chí `§22` | Kết quả |
|---|---|
| Tranh chấp giả | KHÔNG — `multiprocessing.Barrier`, tiến trình HĐH thật |
| `fork` kế thừa store đã khởi tạo | KHÔNG — store dựng **trong** `_worker`, sau `fork`; `_race()` không dựng store ở tiến trình cha |
| Tuần tự trá hình tranh chấp | KHÔNG — 135 vòng độc lập của reviewer cho phân bố người thắng hai chiều |
| Barrier đặt sau chỗ race | KHÔNG — `barrier.wait()` đứng ngay trước `store.append()`, sau khi command đã dựng xong |
| Chấp nhận exception quá rộng | MỘT CHỖ — `pytest.raises(OSError)` cho case symlink (`H2-04`) |
| Test pass nếu CẢ HAI writer fail | KHÔNG — `assert len(applied) == 1` |
| Test pass nếu CẢ HAI writer thành công | KHÔNG ở test race chính — nhưng CÓ ở `test_both_orderings_…` (`H2-04`) |
| Skip do nền tảng | Chỉ `pytest.skip` khi thiếu `fork`; trên POSIX không skip. `0 skipped` trong 25 test |
| Timeout mong manh | KHÔNG — `queue.get(timeout=30)`, `join(timeout=30)`; 0 timeout trong toàn bộ lần chạy |
| Assert chỉ trên bộ nhớ | KHÔNG — `_log_lines()` đọc file thật; index đọc từ đĩa; reopen bằng instance mới |

**Test race trọng yếu** — bốn assertion mà brief yêu cầu:

```text
success_count == 1        : test_exactly_one_writer_wins…  +  test_repeated_contention…
conflict_count == 1       : test_exactly_one_writer_wins…  +  test_repeated_contention…
persisted_event_count == 1: test_the_stale_writer_appends_nothing  +  test_repeated_contention…
reopen sạch               : test_a_fresh_store_reopened_from_disk_reads_one_confirmed_mapping
```

Cả bốn **đều có mặt**, và ba trong bốn nằm chung trong `test_repeated_contention_
never_produces_two_winners` (25 vòng). Không có một test đơn lẻ nào gộp cả bốn;
bộ đối kháng của reviewer thì có (`§10` — 135 vòng, cả bốn cùng lúc, 0 bất
thường). Không nâng thành finding: yêu cầu là bốn assertion tồn tại, và chúng
tồn tại.

`test_only_one_helper_writes_to_the_log_file` là một kiểm **tĩnh** thông minh —
nó khoá con số đường ghi vật lý xuống đúng hai dòng `open(self.log_path, …)`,
nên một đường ghi thứ ba lọt vào tương lai sẽ làm đỏ CI. Ghi nhận tích cực.

---

## 20. Ma trận đóng `B-01` — quyết định độc lập 10/10

| # | Tiêu chí | Kết quả | Bằng chứng của phiên này |
|---|---|---|---|
| 1 | Khoá liên-tiến-trình THẬT tồn tại | **PASS** | `fcntl.flock(LOCK_EX)` trên sidecar; `store.append()` thật bị chặn > 2,0 s sau một holder (`§12`) |
| 2 | Kiểm version nằm TRONG khoá | **PASS** | `append()` bọc cả bốn bước; `_require_version` chỉ tới được từ trong `yield` (`§5`) |
| 3 | State bền vững được nạp lại TRONG khoá | **PASS** | `_refresh_from_disk()` sau `flock`, trước `yield`; lời gọi duy nhất (`§7`) |
| 4 | Race hai tiến trình → đúng một người thắng | **PASS** | 30/30 (n=2), 25/25 (n=4), 15/15 (n=8) — 0 bất thường (`§4`, `§10`) |
| 5 | Writer cũ KHÔNG append được | **PASS** | `persisted_event_count == 1` ở toàn bộ 70 vòng; kiểm trên file, không trên giá trị trả về |
| 6 | Store mở lại hợp lệ | **PASS** | `reopen=OK` ở 135/135 vòng, bằng tiến trình `spawn` mới |
| 7 | Không mutation trùng đã confirm | **PASS** | cùng `client_request_id`: 40 vòng → 1 APPLIED + n−1 ALREADY_APPLIED, 1 event (`§11`) |
| 8 | Không có integrity failure vĩnh viễn | **PASS** | 0/135 vòng cho `MappingIntegrityError`; pre-repair là 10/10 vòng CÓ (`§3` vs `§4`) |
| 9 | Idempotency vẫn đúng | **PASS** | phân biệt canonical `APPLIED`/`ALREADY_APPLIED`/`MappingVersionConflict` giữ nguyên (`§11`); `CHECK-105D-19` PASS |
| 10 | Không hồi quy | **PASS** | 32/32, A–T 20/20, Golden 58/2 không đổi, full 955/11, delta +25, regression 0, hiệu năng không đổi (`§16`, `§17`) |

```text
B-01 CLOSURE CRITERIA : 10 / 10 PASS
B-01                  : CLOSED
```

Đây là kết luận **độc lập**, dựng từ số đo của phiên này, không kế thừa tuyên bố
`CODE-LEVEL RESOLVED` của `S042`.

---

## 21. Findings của phiên này

### BLOCKING

```text
KHÔNG CÓ.  (0)
```

`B-01` = `CLOSED`. Không phát hiện `BLOCKING` mới, kể cả không liên quan.

### HARDENING (mới)

#### `H2-01` — `_consume()` mutate state trước khi đẩy `_log_offset`; thử lại sau lỗi nạp trùng bản ghi

```text
Phân loại : HARDENING
Cơ sở     : không có production path tới dữ liệu sai — fail closed ở MỌI lần;
            0 byte ghi xuống đĩa
Vị trí    : app/modules/product/identity/store.py::_consume / _refresh_from_disk
Nguồn     : mã MỚI của RC-1 (nằm TRONG cumulative repair diff — V4.1 §3)
```

`_consume()` append vào `_events`/`_raw_records`/`_results_by_request` **theo
từng dòng**, nhưng chỉ đẩy `self._log_offset += len(chunk)` ở **cuối**. Nếu một
dòng giữa chunk hỏng, exception thoát ra khi state trong bộ nhớ đã bị mutate
một phần còn offset thì chưa tiến. Mỗi lần thử lại đọc lại đúng phần đó.

Tái lập (log = 2 event hợp lệ + 1 dòng hỏng do một tiến trình khác ghi):

```text
start: revision = 1  offset = 1534
  attempt 1: MappingIntegrityError | in-memory revision = 2 | offset = 1534
  attempt 2: MappingIntegrityError | in-memory revision = 3 | offset = 1534
  attempt 3: MappingIntegrityError | in-memory revision = 4 | offset = 1534
  attempt 4: MappingIntegrityError | in-memory revision = 5 | offset = 1534
disk log lines (unchanged): 3
```

`current_revision()` — vốn KHÔNG raise — trả về một số sai và tăng đơn điệu theo
số lần thử.

Vì sao **không** `BLOCKING`: điều kiện tiên quyết là log đã hỏng sẵn (store đã
fail closed theo `INV-63`); mọi đường ghi vẫn nổ; **0 dòng** được ghi xuống đĩa
ở cả bốn lần thử; `read_at_revision()` cũng nổ. Không tồn tại đường nào dẫn tới
một quyết định nghiệp vụ sai hay một byte sai được bền vững hoá.

**Re-trigger chính xác:** phiên đầu tiên chạm `store.py::_consume` /
`_refresh_from_disk`; **hoặc** phiên đầu tiên có caller đọc `current_revision()`
sau khi bắt `MappingIntegrityError` (ví dụ vòng retry ở tầng UI/CLI). Hình dạng
sửa gợi ý (KHÔNG áp dụng ở đây): nạp vào biến tạm rồi commit
`_events`/`_raw_records`/`_results_by_request`/`_log_offset` nguyên tử, hoặc đẩy
offset theo từng dòng.

Ghi chú ngân sách: `H2-01` nằm trong cumulative repair diff của `TASK-105D-RC-1`.
Theo `V4.1` §3, nếu Owner cho sửa thì việc sửa thuộc **CÙNG** cycle #1, **không**
mở cycle mới.

#### `H2-02` — RC-1 tạo thêm đúng một lỗi `reference_integrity`

```text
Phân loại : HARDENING (governance artifact hygiene)
Vị trí    : docs/reviews/TASK-105D-RC-1-REPAIR-RECORD.md
```

Baseline canonical là **3** unresolved (đo lại tại `222844d` và `e6252c0`).
RC-1 nâng lên **4**: repair record trỏ tới
artifact Review #1 (đường dẫn ghi trong repair record), vốn chỉ
tồn tại trên `review/task-105d-implementation-1` (`58323e2e`), chưa có trên
lineage này. Bản thân repair record đã ghi rõ điều đó ở `§1` — nên đây là một
tham chiếu **cố ý**, không phải nhầm lẫn — nhưng validator không phân biệt được
ý định.

Kỳ vọng `§30` của brief ("không có lỗi governance/reference mới") **bị vi phạm
đúng một lần**. Không có tác động production.

**Re-trigger chính xác:** phiên controlled integration hợp nhất lineage
`TASK-105D` vào default — hợp nhất cả artifact Review #1 (và Review #2 này) sẽ
tự phân giải tham chiếu; nếu integration chỉ mang RC-1 mà không mang artifact
review, phải đổi tham chiếu thành dạng chỉ-SHA
(`git show 58323e2e:docs/reviews/…`) để validator trở lại baseline 3.

#### `H2-03` — event đã commit nhưng caller nhận exception khi ghi index lỗi

```text
Phân loại : HARDENING
Nguồn     : hình dạng CÓ SẴN từ trước repair — KHÔNG phải hồi quy của RC-1
Vị trí    : store.py::_persist  (_append_line rồi mới rebuild_index)
```

```text
os.replace -> OSError(ENOSPC) trong rebuild_index
append raised: OSError [Errno 28]      <-- caller nghĩ là thất bại
log lines on disk: 2                   <-- nhưng event ĐÃ bền vững
lock free: YES ; subsequent op: APPLIED 3 ; reopen revision 3
```

Khoá vẫn được trả, không deadlock, index tự dựng lại được ở lần sau (`INV-63` —
index là DERIVED). Rủi ro thực chất là một caller retry sẽ nhận
`ALREADY_APPLIED` chứ không ghi trùng — nên fail closed về dữ liệu.
**Re-trigger:** phiên đầu tiên thêm xử lý lỗi ghi ở tầng gọi `append()`, hoặc
phiên chuyển store sang cơ chế Phase 2.

#### `H2-04` — `test_both_orderings_actually_occur_across_rounds` không khẳng định điều tên nó nói

```text
Phân loại : HARDENING (test quality)
Vị trí    : tests/test_105d_interprocess_concurrency.py
```

Test chạy 25 vòng rồi chỉ assert `set(winners) <= {"TRK-A", "TRK-B"}` — một
điều kiện luôn đúng. Bằng chứng nó rỗng: **test này PASS trên mã TRƯỚC repair**,
nơi cả hai writer cùng thắng ở mọi vòng (`§18`). Docstring có tự thú nhận là nó
không khẳng định tỉ lệ, nhưng cái tên `both_orderings_actually_occur` khiến một
người đọc bảng kết quả tin rằng tính hai chiều của tranh chấp đã được khẳng
định. Phiên này khẳng định điều đó bằng bộ đối kháng riêng (`§10`), nên không
có khoảng trống bằng chứng — chỉ có một cái tên hứa quá.

Cùng mục: `test_a_symlinked_lock_path_is_refused_instead_of_followed` dùng
`pytest.raises(OSError)`; `OSError` phủ cả `FileNotFoundError`,
`PermissionError` — hẹp lại `errno in (ELOOP, EMLINK)` sẽ chặt hơn.

**Re-trigger:** phiên đầu tiên chạm `tests/test_105d_interprocess_concurrency.py`.

#### `H2-05` — log bị truncate về rỗng: instance sống phát hiện, store mở mới thì không

```text
Phân loại : HARDENING (durability, ngoài mô hình đe doạ B-01)
```

```text
truncate về rỗng -> instance đang sống : MappingIntegrityError (INV-67)  ✔
                 -> store mở mới       : reopen OK, revision 0           ✘ (mất dữ liệu im lặng)
```

Không tiến trình nào của hệ thống truncate log (`INV-67`: không có thao tác
xoá), nên đường này chỉ mở ra trước một tác nhân ngoài store. Ghi lại vì
`§17`/`§18` của brief yêu cầu tách bạch bảo đảm durability khỏi bảo đảm khoá.
**Re-trigger:** phiên đầu tiên soạn backup/restore hoặc integrity-check khi khởi
động cho store (`INV-65` đã có `export_bundle` + manifest + hash — chưa có ai
kiểm hash lúc mở).

### OUT_OF_SCOPE

```text
O2-01  validate_reference_integrity — 3 reference của TASK-REM-T06
       (/README.md, CODE_OF_CONDUCT.md, CONTRIBUTING.md). GIỐNG HỆT tại base
       222844d và tại e6252c0. Có trước, không liên quan TASK-105D.
       (= O-01 của Review #1, xác nhận lại độc lập.)
O2-02  HB-105D-F2-01 — data contract §3.3 câu 8 "bộ ba" vs E-L/INV-55 "CẢ BỐN".
       VẪN OPEN. Cần phiên có thẩm quyền sửa data contract.
O2-03  HB-105D-F2-02 — data contract §16.1 stale. VẪN OPEN, documentation-only.
O2-04  DIVERGENCE = INTEGRATION_DECISION_REQUIRED [loc > 5.000] theo V4.1 §8.
       Không phải defect của RC-1; là một quyết định Owner (A/B/C) phải ghi lại,
       không được tiếp tục im lặng.
```

```text
BLOCKING     : 0
HARDENING    : 5 mới (H2-01 … H2-05)  +  10 kế thừa vẫn mở (§22)
OUT_OF_SCOPE : 4
```

---

## 22. Đối chiếu HARDENING đã có — KHÔNG repair

Mỗi mục được **đo lại**, không đọc từ bản ghi của phiên trước.

| ID | Nội dung | Trạng thái sau RC-1 | Bằng chứng / re-trigger |
|---|---|---|---|
| `H-01` | Tập ĐẾM `confirmation_action` dùng làm tập THẨM QUYỀN | **OPEN** | Đo: `CORRECT_MAPPING in CONFIRMATION_ACTION_TYPES = False`; correct với `SIMILARITY_RANKED` → BLOCKED, `ALIAS_AID_UNIQUE` → BLOCKED, `CATALOG_EXACT_UNIQUE`/`ALIAS_EXACT` → APPLIED. Giống hệt Review #1. **Re-trigger:** phiên nối permission model `DEC-124` vào correction, hoặc phiên tiếp theo chạm `_guard_authority` |
| `H-02` (kế thừa `H-05` của Freeze Review #2) | `ranking_method_id` OPTIONAL nhưng được hash | **OPEN ở mức contract** | `docs/spec/TASK-105D-DATA-CONTRACT.md` 0 byte thay đổi bởi RC-1; `evidence.py` vẫn tự khai "trạng thái contract-level VẪN OPEN". **Re-trigger:** phiên có thẩm quyền sửa `§6.7` — (a) `OPTIONAL → REQUIRED`, hoặc (b) quy phạm hoá sentinel trong `§7.3` |
| `H-03` | Test reference sai cho `CHECK-105D-26/-27` | **OPEN** | Đo: `pytest tests/test_105d_boundaries.py::TestG26G27… ` → `ERROR: not found`; lớp thật ở `test_105d_resolution.py`. `TASK-105D-GATE-EXECUTION-RECORD.md` không bị RC-1 chạm. **Re-trigger:** phiên kế tiếp chạm Gate Execution Record |
| `H-04` | `rebuild_index()` O(n) mỗi append ⇒ O(n²) bulk | **OPEN — KHÔNG hồi quy** | Đo `§16`: RC-1 6,795 s vs pre-repair 6,969 s ở n=800. Thêm dữ liệu mới: siêu tuyến tính còn hiện diện cả ở store thuần bộ nhớ (2,785 s) ⇒ nguyên nhân rộng hơn `rebuild_index`. KHÔNG promote. **Re-trigger:** bootstrap/migration > 1.000 mapping, hoặc chuyển sang cơ chế Phase 2 |
| `H-05` (của Review #1) | Dòng log sai khuôn raise lỗi ngoài miền | **OPEN** | Đo: dòng JSON **hợp lệ** nhưng sai khuôn (`{"khong_phai_event": true}`) → `KeyError: 'event_id'`, không phải `MappingIntegrityError`. RC-1 chỉ chuyển `_load_log` → `_consume` giữ nguyên nguyên văn xử lý lỗi. **Re-trigger:** cùng lượt với bất kỳ sửa đổi nào trên `_consume` (trùng vùng với `H2-01` — nên sửa một lượt) |
| `H-06` | Hai test migration/rollback mỏng | **OPEN** | RC-1 không chạm `test_105d_audit_replay.py`/`boundaries`. **Re-trigger:** phiên đầu tiên implement migration/rollback thật |
| `H-07` | 32 trường `Status:` còn `NOT_TESTED` | **OPEN** | 32 khối `#### CHECK-105D-NN` trong khối gate, `Status: NOT_TESTED` nguyên vẹn; `GATE_SET_SHA256` khớp. Xem `§23` |
| `HB-105D-F2-01` | `§3.3` "bộ ba" vs `INV-55` "CẢ BỐN" | **OPEN** | data contract 0 byte thay đổi |
| `HB-105D-F2-02` | `§16.1` stale | **OPEN** | data contract 0 byte thay đổi |
| `HB-105D-F2-03` | 13 invariant chưa có gate riêng | **OPEN** (đã phủ bằng test, phân loại không đổi) | Không có gate nào được thêm/xoá; gate count vẫn 32 |

```text
CLOSED      : 0
SUPERSEDED  : 0
RECLASSIFIED: 0
OPEN        : 10 / 10
```

Không mục nào được promote lên `BLOCKING`: không mục nào có production path
hiện tại kèm tác động correctness/data/business/safety (`V4.1` §7). `H-01` gần
nhất — nó khoá một workflow bắt buộc của contract — nhưng nó **fail closed**
(không ghi gì) nên không phải data-integrity, đúng như phân loại của Review #1.

Ghi nhận: Review #1 khuyến nghị Repair Cycle #1 sửa `B-01` **cộng `H-01`**.
`S042` chỉ sửa `B-01` và **khai báo tường minh** rằng `H-01` giữ OPEN. Đó là
thu hẹp phạm vi có ghi chép, **không** phải scope creep và **không** phải khai
man; không tạo finding. Nhưng cần nói rõ để phiên sau không đọc nhầm rằng
khuyến nghị của Review #1 đã được thực hiện đầy đủ.

---

## 23. `H-07` — câu hỏi thẩm quyền gate, kết luận chính xác

Sự kiện đã xác minh: trong `docs/tasks/TASK-105D-product-identity-resolver.md`,
32 trường `Status:` của khối gate đã freeze vẫn là `NOT_TESTED`, trong khi
`docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md` §3 ghi 32/32 `PASS`, và phiên
này **tự thực thi lại** cho ra 32/32 `PASS` (`§17.2`).

Ba văn bản canonical quyết định:

1. `governance/core/TASK_COMPLETION_GATE_STANDARD.md`: *"Bất kỳ REQUIRED check nào là FAIL,
   BLOCKED, hoặc `NOT_TESTED` đều ngăn task đạt **DONE**"*. Câu này nói về
   `DONE`. Nó **không** nói gì về integration.
2. Khối freeze của chính task: *"bất kỳ sửa đổi nào làm đổi `GATE_SET_SHA256`
   cần một `COMPLETION GATE CHANGE PROPOSAL` mới + authority"*. Ghi `PASS` vào
   trong khối sẽ đổi hash ⇒ cần authority riêng.
3. `V4.1` §12 State Authority Matrix: `DONE → Owner / completion authority`;
   integration là trục riêng, do `V4.1` §8 (`INTEGRATION_DECISION_REQUIRED` →
   Owner chọn A/B/C).

**Kết luận:**

```text
Integration ĐƯỢC PHÉP tiến hành với execution evidence tách rời.
  - NOT_TESTED trong khối gate KHÔNG phải một gate chặn integration;
  - nó là hệ quả cơ học của việc giữ artifact freeze byte-identical;
  - bằng chứng thực thi thật tồn tại, tái lập được, và đã được MỘT phiên độc
    lập (phiên này) chạy lại cho ra cùng kết quả 32/32.

Gate-authority reconciliation BẮT BUỘC TRƯỚC `DONE`, KHÔNG trước integration.
```

Hai đường hợp lệ để reconcile, cả hai đều **ngoài** thẩm quyền phiên này:

```text
(a) Một phiên có GATE AUTHORITY mở COMPLETION GATE CHANGE PROPOSAL, ghi
    NOT_TESTED -> PASS trong khối gate, và chấp nhận GATE_SET_SHA256 MỚI
    (giá trị 0444e58c… sẽ không còn hiệu lực — phải ghi lại giá trị mới ở
    mọi artifact tham chiếu nó).
(b) Một OWNER DECISION tường minh rằng bản ghi thực thi tách rời
    (TASK-105D-GATE-EXECUTION-RECORD.md + review artifact này) THOẢ MÃN yêu cầu
    "REQUIRED check PASS" của TASK_COMPLETION_GATE_STANDARD, giữ nguyên
    GATE_SET_SHA256 = 0444e58c….

Khuyến nghị của reviewer: (b). Nó giữ nguyên bất biến "artifact freeze không bị
sửa" — chính bất biến làm cho việc tái lập hash trở thành bằng chứng có giá trị
— và chi phí của (a) là làm mất giá trị tham chiếu 0444e58c… trong SÁU artifact
lịch sử. Nhưng đây là quyết định của Owner, không phải của reviewer.
```

Phiên này **KHÔNG** sửa khối gate (`§17.1` — hash khớp tuyệt đối sau khi phiên
này ghi artifact).

---

## 24. Ngân sách repair

```text
TASK-105D trước Review #2 : 2 allowed / 1 used / 1 remaining
Independent Review #2     : KHÔNG tiêu thụ Repair Cycle
                            (V4.1 §3 — cycle tính theo cumulative repair diff
                             của implementation; phiên này sửa 0 dòng
                             app/**, tests/**, config/**, tools/**, scripts/**,
                             pyproject.toml)
TASK-105D sau Review #2   : 2 allowed / 1 used / 1 remaining   (KHÔNG ĐỔI)
```

`B-01` = `CLOSED` ⇒ **KHÔNG** mở Repair Cycle #2. Phiên này cũng không mở RC-2
cho bất kỳ `HARDENING` nào: `V4.1` §3/§7 không cho phép reviewer tự mở cycle, và
5 finding mới đều là `HARDENING`. Nếu Owner muốn đóng `H2-01`/`H-01`/`H-03`, đó
là **Owner Decision**, và vì `H2-01` nằm trong cumulative repair diff của RC-1,
việc sửa nó thuộc **CÙNG** cycle #1 (`V4.1` §3), không tiêu thêm ngân sách.

---

## 25. Ranh giới — đã xác minh KHÔNG bị vượt

```text
nhánh RC-1 (task/task-105d-rc1) bị mutate      : KHÔNG
nhánh task/task-105d-implementation bị mutate  : KHÔNG
app/** bị reviewer sửa                          : KHÔNG (0 dòng)
tests/** bị reviewer sửa                        : KHÔNG (0 dòng)
config/** bị reviewer sửa                       : KHÔNG (0 dòng)
khối Completion Gate đã freeze                  : KHÔNG SỬA (hash khớp)
data contract                                   : KHÔNG SỬA
production data                                 : KHÔNG CHẠM, KHÔNG TẠO
                                                  (toàn bộ fixture là dữ liệu
                                                   tổng hợp trong tmpdir)
Tracking                                        : KHÔNG CHẠM — 0 đường ghi tồn tại
FilePriceProvider activate                      : KHÔNG (diff base→RC-1 trên
                                                  app/modules/pricing/ + config/
                                                  = rỗng)
TASK-105E implement                             : KHÔNG (chỉ có spec outline
                                                  có sẵn; 0 dòng P00–P11)
default branch đổi                              : KHÔNG
merge                                           : KHÔNG thực hiện
DONE được đánh dấu                              : KHÔNG
```

Script đối kháng của reviewer nằm ở scratchpad ngoài repo và **không** được
commit — governance không yêu cầu chúng làm artifact.

---

## 26. Verdict

```text
PASS WITH HARDENING — RC-1 VERIFIED / ELIGIBLE FOR CONTROLLED INTEGRATION

B-01                     : CLOSED  (10/10 tiêu chí đóng, xác minh độc lập)
BLOCKING                 : 0
HARDENING                : 5 mới (H2-01…H2-05) + 10 kế thừa vẫn OPEN
OUT_OF_SCOPE             : 4

32 frozen check          : 32 / 32 PASS  (thực thi độc lập tại a098235)
A–T                      : 20 / 20 PASS  (truy vết độc lập; N kiểm bổ sung
                                          bằng 135 vòng đa tiến trình)
GATE_SET_SHA256          : 0444e58c…  tái lập KHỚP TUYỆT ĐỐI (57.614 byte)
TASK-105D targeted       : 199 passed
Golden                   : 58 passed, 2 skipped — KHÔNG ĐỔI
Full suite               : 955 passed, 11 skipped
Test delta               : 930 → 955 = +25  (xác minh hai chiều)
Regression               : 0
Validator                : 4/5 PASS; reference_integrity 3 (baseline) → 4 (H2-02)
Repair budget            : 2 allowed / 1 used / 1 remaining  (KHÔNG ĐỔI)
```

Nói cho công bằng và chính xác: bản sửa này đúng chỗ. Nó không khoá quanh
`write()` — chỗ chưa bao giờ hỏng — mà khoá quanh **quyết định "được phép ghi"**,
và nó nạp lại state quyền uy **bên trong** khoá trước khi kiểm version. Đó chính
xác là hai nửa mà `B-01` đòi hỏi, và cả hai đều được xác minh bằng tranh chấp
tiến trình HĐH thật chứ không bằng lập luận. Việc `_persist_raw()` — đường ghi
thứ hai — bị **xoá** thay vì được vá thêm khoá, cho thấy phiên repair tìm đúng
tập đường ghi chứ không chỉ vá chỗ được chỉ.

5 `HARDENING` mới không mục nào chạm được tới một byte sai được bền vững hoá.

`TASK-105D` **KHÔNG** phải `DONE`: `H-07` (gate authority) và 15 `HARDENING`
đang mở đều nằm ngoài thẩm quyền của phiên này.

---

## 27. Next authorized action

```text
1. OWNER INTEGRATION DECISION theo V4.1 §8 (DIVERGENCE =
   INTEGRATION_DECISION_REQUIRED, loc > 5.000): chọn (A) integrate sớm,
   (B) cắt scope, hay (C) tiếp tục divergence có lý do + review date.
   Khuyến nghị của reviewer: (A) — RC-1 đã PASS review độc lập, và mỗi ngày
   divergence tiếp theo chỉ làm tăng chi phí hợp nhất.

2. NẾU (A): một phiên CONTROLLED INTEGRATION hợp nhất lineage TASK-105D
   (e6252c0 → 1cc96a9 → a098235) vào default bằng git merge --no-ff
   (ancestry-preserving; KHÔNG squash, KHÔNG cherry-pick), và hợp nhất cả
   artifact Review #1 (58323e2e) + Review #2 này — việc hợp nhất cả hai
   artifact tự phân giải H2-02.

3. TRƯỚC KHI bất kỳ phiên nào đề xuất TASK-105D = DONE: Owner reconcile
   H-07 theo §23 — khuyến nghị đường (b) (Owner Decision công nhận bản ghi
   thực thi tách rời), giữ nguyên GATE_SET_SHA256.

4. KHÔNG mở Repair Cycle #2. Nếu Owner muốn đóng H2-01 / H-01 / H-03 / H-05:
   đó là Owner Decision; H2-01 và H-05 nằm cùng vùng mã (_consume) nên nên
   sửa MỘT lượt, và cả hai thuộc CÙNG cycle #1 theo V4.1 §3 — không tiêu
   thêm ngân sách.

5. Song song, không chặn: phiên có thẩm quyền data contract đóng H-02 (H-05
   của Freeze Review #2), O2-02 (HB-105D-F2-01), O2-03 (HB-105D-F2-02).
```

**STOP.** Phiên này dừng ở review state. Không repair, không merge, không đánh
dấu `DONE`, không mở Repair Cycle #2.
