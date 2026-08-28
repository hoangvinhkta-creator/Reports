# TASK-105D — REPAIR CYCLE #1 — BẢN GHI SỬA CHỮA

## Metadata

```text
repair_cycle_id : TASK-105D-RC-1
root_task       : TASK-105D
branch          : task/task-105d-rc1
base_sha        : e6252c06347ed5305fc32a77706a3a63f5a950cf
trigger         : B-01 — Independent Implementation Review #1
review_evidence : 58323e2e59382e2ce4816453cfaaa5d31deba3db
                  docs/reviews/TASK-105D-INDEPENDENT-IMPLEMENTATION-REVIEW-1.md
repair_scope    : concurrency persistence liên-tiến-trình / khoá file
authority       : Owner APPROVES Repair Cycle #1; Owner Decision cho B-01 =
                  option (a) — GIỮ hợp đồng concurrency "một máy, nhiều tiến
                  trình", sửa IMPLEMENTATION bằng một khoá file thật
budget_before   : 2 allowed / 0 used / 2 remaining
budget_after    : 2 allowed / 1 used / 1 remaining
Selected Profile: PRODUCT
Current Task Mode: MAJOR
Risk            : Effective Risk HIGH — max(Local Risk 4, Blast Radius 5)
Evidence Level  : E2
Executed By     : phiên Repair Cycle #1 (S042)
Timestamp       : 2026-08-28
```

Trạng thái được phép của phiên này:
**REPAIR CANDIDATE — READY FOR INDEPENDENT REVIEW #2.**
Phiên này KHÔNG tự tuyên bố Independent Review #2 PASS và KHÔNG đóng
governance closure cho `TASK-105D`.

---

## 1. Pre-flight

```text
branch          : task/task-105d-rc1                              OK
HEAD            : e6252c06347ed5305fc32a77706a3a63f5a950cf        OK
worktree        : clean (git status --porcelain rỗng)             OK
review evidence : 58323e2e… truy xuất được sau `git fetch origin` OK
                  (chứa trên origin/review/task-105d-implementation-1)
```

Artifact review được đọc NGUYÊN VĂN (`§13` `B-01`, `§9` case `N`, `§10`,
`§11`), không chỉ đọc Final Report.

Lưu ý cho phiên review kế tiếp: artifact
`docs/reviews/TASK-105D-INDEPENDENT-IMPLEMENTATION-REVIEW-1.md` và session
`docs/sessions/S041-…` nằm trên nhánh `review/task-105d-implementation-1`
(commit `58323e2e`), CHƯA được hợp nhất vào nhánh này. `S042` cố ý không kéo
chúng sang: nhánh repair chỉ mang diff repair + bằng chứng của chính nó. Đọc
bằng `git show 58323e2e:docs/reviews/TASK-105D-INDEPENDENT-IMPLEMENTATION-REVIEW-1.md`.

---

## 2. Tái lập `B-01` TRƯỚC khi sửa

Hai tiến trình HĐH độc lập, cùng file log, cùng `expected_version = 0`, thả
đồng thời bằng một barrier trên file.

```text
$ python3 drive.py        # tại e6252c0, TRƯỚC repair
A: APPLIED version=1
B: APPLIED version=1                       <-- KHÔNG raise MappingVersionConflict

--- log trên đĩa ---
1 CONFIRM_MAPPING B version=1 supersedes=None
2 CONFIRM_MAPPING A version=1 supersedes=None

--- tiến trình thứ ba đọc mapping ---
MappingIntegrityError: INV-33: bản ghi 1ebdbfa5… cho khoá
'REPORTS_SALES\x1fSP CHUNG' khai supersedes=None nhưng bản ghi trước đó là
'2c5bd28f…' — hai bản ghi CONFIRMED độc lập cho cùng một khoá; TUYỆT ĐỐI
không tự chọn một cái
```

Khớp chính xác mô tả của `B-01`: hai APPLIED, hai bản ghi `CONFIRMED` độc
lập, và store hỏng VĨNH VIỄN cho mọi phép đọc sau đó.

---

## 3. Nguyên nhân gốc

Không phải một lỗi ghi file. `append()` có đúng ba khiếm khuyết xếp chồng:

1. **Không tồn tại khoá liên-tiến-trình nào.** `grep -rn "fcntl\|flock"` trên
   `app/` trả 0 kết quả tại base.
2. **`_require_version()` so `expected_version` với ẢNH CHỤP TRONG BỘ NHỚ**,
   được nạp một lần duy nhất lúc khởi tạo instance. Một tiến trình khác ghi
   xong rồi thì instance này vẫn tin version cũ.
3. Vì (1) và (2), chu trình `đọc version → quyết định → append` KHÔNG nguyên
   tử. Cả hai tiến trình cùng thấy `version = 0`, cả hai cùng qua kiểm, cả
   hai cùng ghi.

Điểm cần nói rõ: `write()` chưa bao giờ là chỗ hỏng — mỗi event vẫn được ghi
bằng MỘT lời gọi `write()` + `fsync`, nên log không bị trộn ký tự. Chỗ hỏng
là **quyết định "được phép ghi"**. Vì vậy một khoá quanh riêng `write()`, hay
một `threading.Lock` trong tiến trình, đều KHÔNG sửa được `B-01`.

---

## 4. Cơ chế khoá

| Hạng mục | Quyết định |
|---|---|
| File/inode bị khoá | `<log_path>.lock` — file *sidecar* riêng, tạo một lần, **không bao giờ** bị xoá hay `os.replace` |
| Cơ chế | `fcntl.flock(fd, LOCK_EX)` — stdlib POSIX, **không** thêm dependency (giữ nguyên `D-11`) |
| Ngữ nghĩa | Độc quyền, không có chế độ shared: mọi đường ghi đều phải nạp lại state nên đều là writer |
| Chặn hay không | Chặn (không `LOCK_NB`) — hai người dùng trên một máy xếp hàng, không nhận lỗi giả |
| Vòng đời | Đúng một giao dịch: `os.open` → `LOCK_EX` → nạp lại → thân → `LOCK_UN` → `os.close` |
| Giải phóng khi lỗi | `finally` lồng hai lớp; mọi exception (`MappingVersionConflict`, `SimilarityAuthorityError`, `MappingIntegrityError`, `TypeError`) đều rời khối qua đó |
| Tiến trình chết | Nhân giải phóng `flock` khi tiến trình chết/fd đóng, kể cả `SIGKILL` ⇒ **không có stale lock** |
| Tái nhập | `_persist()` → `rebuild_index()` cũng là giao dịch; `_lock_depth` (dưới `RLock`) biến lần vào trong thành no-op, tránh tự khoá chính mình trên fd thứ hai |
| Symlink | `O_NOFOLLOW` — một symlink đặt sẵn ở đường dẫn khoá sẽ khiến hai tiến trình khoá hai inode khác nhau, tức `B-01` quay lại qua cửa sau. Gặp symlink thì nổ |
| Nền tảng | POSIX. Không có `fcntl` (Windows) + có `log_path` ⇒ `StoreLockUnavailableError` (fail closed), KHÔNG âm thầm chạy không khoá |
| NFS | `flock` không loại trừ lẫn nhau qua NFS ở nhiều cấu hình — nằm đúng trong phạm vi "nhiều máy = Phase 2" mà `§11.1` đã tuyên bố, không phải hạn chế mới |

### Vì sao là file sidecar, không phải chính log hay index

`rebuild_index()` thay index bằng `os.replace`, tức **đổi inode**. Khoá đặt
trên một inode bị thay giữa chừng sẽ mất tác dụng loại trừ: hai tiến trình
khoá hai inode khác nhau và cùng tưởng mình độc quyền. Log thì append-only
nên inode ổn định, nhưng file khoá riêng cho phép giữ một bất biến mạnh hơn
và dễ kiểm chứng hơn: **file `.lock` không bao giờ bị tạo lại**. Đó là lý do
nó cũng không được xoá khi giải phóng — xoá file khoá là cách kinh điển tạo
ra đúng cái race mà nó đang chống. `CHECK` tương ứng:
`test_the_lock_file_sits_beside_the_log_and_is_never_replaced` so sánh
`st_ino` trước/sau nhiều lần append + `rebuild_index()`.

---

## 5. Biên nguyên tử

```text
ACQUIRE flock(LOCK_EX) trên <log_path>.lock
    _refresh_from_disk()          ← nạp lại phần đuôi log do tiến trình khác ghi
    read_at_revision() → _project ← chiếu lại + kiểm toàn vẹn (INV-33/INV-63)
    idempotency lớp 1 (INV-68)    ← client_request_id, SAU khi đã nạp lại
    _guard_authority   (INV-01)
    _require_version   (INV-59)   ← so với version vừa đọc lại từ đĩa
    _next_mapping / conflict check
    _append_line + fsync (INV-62)
    rebuild_index (lồng, no-op khoá)
RELEASE flock(LOCK_UN) → close(fd)
```

Ba điều `§4` của brief đòi hỏi, và cách chúng được thoả:

- **Kiểm version SAU khi khoá** — `_require_version()` chỉ được gọi từ
  `_append_mapping_command()` / `_append_cross_system_command()`, cả hai chỉ
  được gọi bên trong `with self._transaction():` của `append()`.
- **Kiểm version SAU khi làm mới state quyền uy** — `_refresh_from_disk()`
  chạy bên trong `_transaction()`, TRƯỚC khi `yield`.
- **Không phải khoá quanh riêng append, không phải `threading.Lock` đơn
  thuần, không phải check-then-lock-then-append** — xem sơ đồ trên;
  `threading.RLock` chỉ bảo vệ bộ đếm độ sâu và tuần tự hoá các luồng của
  CÙNG instance, nó **không** được dùng làm cơ chế loại trừ liên tiến trình.

### Làm mới trong khoá (`_refresh_from_disk`)

Log là append-only (`INV-67`), nên phần đã nạp luôn là một **tiền tố** của
file. Vì vậy chỉ cần đọc từ `_log_offset` trở đi thay vì parse lại toàn bộ —
đúng đắn tương đương mà không thêm một vòng O(n) parse vào mỗi append.

- `size == _log_offset` → không có gì mới, thoát ngay.
- `size > _log_offset` → đọc phần đuôi, parse, chiếu vào `_events` /
  `_raw_records` / `_results_by_request`.
- `size < _log_offset` → log co lại ⇒ vi phạm append-only ⇒
  `MappingIntegrityError`, KHÔNG đọc tiếp thành nửa state.

Một dòng hỏng (kể cả dòng ghi dở do tiến trình chết) bị TỪ CHỐI chứ không bị
bỏ qua — giữ nguyên hành vi và thông điệp lỗi của `_load_log()` cũ.

---

## 6. Test đa tiến trình

File mới: `tests/test_105d_interprocess_concurrency.py` (25 test).

Thiết kế — đúng những gì `§6` của brief CẤM, đã tránh:

```text
KHÔNG hai lời gọi trên một instance
KHÔNG hai object chạy tuần tự
KHÔNG monkeypatch giả lập tranh chấp
KHÔNG chỉ dùng thread (hợp đồng nói process-level)
KHÔNG sleep làm cơ chế đồng bộ chính
```

Đồng bộ dùng `multiprocessing.Barrier(2)` — nhân thả cả hai tiến trình ra
cùng lúc. Store được dựng **sau** fork, trong tiến trình con, nên hai tiến
trình không chia sẻ một mẩu state nào trong bộ nhớ; chúng chỉ gặp nhau ở
file log.

### Kết quả

```text
1 vòng, đo trực tiếp:
  APPLIED                 : đúng 1
  MappingVersionConflict  : đúng 1
  dòng trên đĩa           : đúng 1   (kẻ cũ KHÔNG append gì)

60 vòng lặp (đo ngoài pytest, cùng hàm _race):
  mọi vòng               : đúng 1 APPLIED + đúng 1 MappingVersionConflict
  mọi vòng               : đúng 1 dòng log
  phân bố người thắng    : {'TRK-B': 34, 'TRK-A': 26}
  tổng thời gian         : 0,66 s
```

Phân bố 26/34 là bằng chứng barrier tạo tranh chấp THẬT: người thắng do lịch
biểu của nhân quyết định chứ không cố định, vậy mà số người thắng luôn là
đúng một. Trong bộ test CI, `CONTENTION_ROUNDS = 25`.

### Chứng minh test thật sự bắt được `B-01`

Chạy CHÍNH file test này trên một worktree tách riêng tại base
`e6252c06` (chưa sửa):

```text
18 failed, 5 passed
```

18 case gãy gồm toàn bộ nhóm đa tiến trình, reopen/restart, hai-instance,
idempotency dưới tranh chấp và audit. Test không phải là thứ chỉ pass sau khi
sửa — nó FAIL trước khi sửa.

---

## 7. Reopen / restart

Sau tranh chấp, huỷ mọi instance, dựng store MỚI từ file:

```text
mapping đọc được          : có, source_product_code = đúng người thắng
status                    : CONFIRMED
version                   : 1
current_revision()        : 1
alias_index()             : 1 phần tử (dựng lại từ log)
index trên đĩa            : revision 1, 1 active mapping
MappingIntegrityError     : KHÔNG
lệnh ghi hợp lệ kế tiếp   : APPLIED, version 2   (không deadlock, không kẹt khoá)
```

Đây là tính đúng đắn của trạng thái **TRÊN ĐĨA**, không phải trong bộ nhớ.

---

## 8. Hai instance trong một tiến trình (`§8` — bổ sung, không thay thế)

```text
A và B cùng bắt đầu từ version N = 0
A.append(expected_version=0)                    -> APPLIED,  version 1
B.append(expected_version=0)                    -> MappingVersionConflict
dòng log                                        -> 1  (B không append)
B nạp lại trong khoá  -> B.current_revision()   -> 2 khi A đã ghi 2 event
B.append(expected_version=1) sau reconcile      -> APPLIED,  version 2
                                                   supersedes != None (INV-60)
```

---

## 9. Idempotency (`§11`)

Không có ngữ nghĩa mới nào được phát minh.

```text
hai tiến trình, CÙNG client_request_id, cùng expected_version=0:
    outcomes ⊆ {APPLIED, ALREADY_APPLIED}
    APPLIED  : đúng 1
    event    : đúng 1

retry liên tiến trình (instance khác, cùng client_request_id):
    outcome     : ALREADY_APPLIED
    new_version : 1
    event       : vẫn đúng 1
```

Kẻ đến sau nạp lại log TRONG khoá, thấy `client_request_id` đã dùng, nên đi
ra bằng lớp idempotency 1 (`INV-68`) chứ không phải bằng version conflict —
đúng thứ tự kiểm mà docstring `append()` đã công bố từ trước.

---

## 10. Audit (`§12`)

```text
đúng một mutation được chấp nhận  -> len(events) == 1
                                     confirmation_action_count() == 1
                                     actor_id = actor của người thắng
kẻ ghi bị từ chối                 -> 0 event, 0 dấu vết audit
```

Hợp đồng hiện hành KHÔNG yêu cầu audit cho conflict, nên không thêm.

---

## 11. Đường lỗi và giải phóng khoá (`§10`)

| Đường lỗi | Hành vi đo được |
|---|---|
| Version conflict | raise, 0 ghi, khoá trả, lệnh hợp lệ kế tiếp APPLIED |
| Authority rejection (sau khoá, trước append) | `SimilarityAuthorityError`, log rỗng, lệnh hợp lệ kế tiếp APPLIED |
| Dòng log hỏng (crash giữa `write()`) | `MappingIntegrityError`; khoá đã trả — tiến trình khác vẫn lấy được khoá và vẫn nổ bằng CÙNG lỗi miền, không treo |
| Log co lại | `MappingIntegrityError` (vi phạm append-only `INV-67`) |
| Tiến trình giữ khoá bị `SIGKILL` | Đo bằng `LOCK_NB` probe: trong khi con giữ, cha KHÔNG lấy được (`BlockingIOError`) ⇒ khoá là thật. Sau `kill`, cha append thành công ⇒ **không stale lock**, không deadlock |

Không có đường nào rời `_transaction()` mà còn giữ khoá: `LOCK_UN` nằm trong
`finally` trong, `os.close` nằm trong `finally` ngoài.

---

## 12. Hiệu năng (`§13`)

Đo trên cùng máy, cùng kịch bản, base vs RC-1:

```text
              base e6252c0      RC-1        chênh
100 append      0,20 s         0,21 s       +5 %
400 append      2,11 s         2,31 s       +9 %
800 append      8,04 s         8,37 s       +4 %
```

Khoá KHÔNG phải là thành phần chi phối. Đường cong siêu tuyến tính đã có sẵn
ở base và do `H-04` (`rebuild_index()` O(n) mỗi append) gây ra — `H-04` giữ
nguyên phân loại HARDENING và KHÔNG được sửa trong RC-1. Không có dự án tối
ưu hoá nào trong phiên này; `_refresh_from_disk()` cố ý đọc tăng dần thay vì
parse lại toàn bộ chính là để không tạo thêm một vòng O(n) mới.

---

## 13. Rà soát bảo mật / toàn vẹn dữ liệu (`§19`)

| Hạng mục | Kết luận |
|---|---|
| Xử lý đường dẫn khoá | Dẫn xuất thuần từ `log_path` (`+ ".lock"`), không nhận input riêng |
| Symlink | `O_NOFOLLOW`; test dựng symlink thật và khẳng định `OSError` + 0 dòng log |
| Quyền file | `0o600` |
| Stale lock | Không tồn tại — nhân trả khoá khi tiến trình chết; file `.lock` cố ý không bị xoá |
| Crash release | Đo bằng `SIGKILL` + `LOCK_NB` probe (§11) |
| JSONL hỏng dưới khoá | `MappingIntegrityError`, không đọc thành nửa state |
| Ghi dở / partial write | Một event = một `write()` + `fsync`; dòng dở bị từ chối |
| Bypass qua entry point khác | `append()`, `import_bundle()`, `rebuild_index()` — cả ba đều vào `_transaction()` |
| Mọi mutation method dùng cùng giao dịch | CÓ. `_persist_raw()` (đường ghi thứ hai, không khoá) đã bị **xoá**; `import_bundle` nay dùng chung `_append_line()` trong MỘT giao dịch |
| Không còn đường ghi nào ngoài khoá | Kiểm TĨNH: `test_only_one_helper_writes_to_the_log_file` khẳng định trong toàn file chỉ tồn tại đúng hai lời gọi `open(self.log_path, …)` — một `"rb"` (đọc, trong khoá) và một `"ab"` (ghi, trong khoá) |

Bản sửa này KHÔNG phải vá nửa vời một entry point: cả ba đường ghi đều nằm
trong cùng một biên giao dịch, và có một test tĩnh giữ cho điều đó không âm
thầm hồi quy.

---

## 14. Hợp đồng — KHÔNG bị nới lỏng

```text
data contract §11.1   : KHÔNG SỬA MỘT BYTE
docstring store.py    : giữ nguyên câu "JSONL + khoá file … một máy";
                        phần thêm vào GIẢI THÍCH cách thi hành, không thu hẹp
INV-59 / INV-60       : nay thi hành được qua biên tiến trình (trước: không)
INV-61 aggregate      : không đổi — khoá bảo vệ giao dịch, biên version vẫn
                        là (source_system, raw_identity_key)
INV-62 / INV-63       : không đổi
INV-66 / INV-67       : mạnh lên — `_persist_raw()` (đường ghi thứ hai) bị xoá
INV-68 / INV-69       : không đổi về ngữ nghĩa, nay đúng cả liên tiến trình
business semantics    : KHÔNG ĐỔI
Completion Gate       : KHÔNG SỬA
```

Không có phương án (b) nào được dùng: hợp đồng KHÔNG bị thu hẹp xuống
"một tiến trình".

---

## 15. Gate đã freeze

```text
$ sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md | sha256sum
0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877  -

$ sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md | wc -c
57614

$ git diff --stat -- docs/tasks/TASK-105D-product-identity-resolver.md
(rỗng)
```

KHỚP TUYỆT ĐỐI với `GATE_SET_SHA256` của bản freeze `S038`. Khối gate KHÔNG
bị sửa một byte. 34 dòng `NOT_TESTED` trong khối vẫn nguyên trạng —
phiên này KHÔNG chuyển `NOT_TESTED → PASS` (không có gate authority; và làm
vậy sẽ đổi SHA). Bằng chứng thực thi vẫn nằm tách riêng.

---

## 16. Test

```text
TASK-105D targeted   : 174 → 199 passed      (+25)
Golden               : 58 passed, 2 skipped  (KHÔNG ĐỔI)
Full suite           : 930 → 955 passed      (+25)
skipped              : 11 → 11               (KHÔNG ĐỔI)
regression           : 0
```

Delta được giải thích CHÍNH XÁC: 25 test mới, toàn bộ trong một file mới
`tests/test_105d_interprocess_concurrency.py`. Không test nào bị sửa, đổi
tên, bỏ qua hay xoá.

Phân bổ 25 test mới:

```text
TestInterProcessVersionRace           4   race hai tiến trình + lặp 25 vòng
TestStoreStaysValidAfterContention    3   reopen/restart từ đĩa
TestTwoInstancesInOneProcess          3   §8
TestIdempotencyUnderContention        2   §11
TestAuditUnderContention              1   §12
TestLockReleaseOnFailurePaths         4   §10
TestEveryWritePathIsLocked            5   §19 (gồm 1 kiểm tĩnh, 1 symlink)
TestCrashReleasesTheLock              1   §10 SIGKILL + LOCK_NB probe
TestLockDoesNotStarveOrdinaryAppends  1   §13
runtime cung cấp fcntl                1
```

Ổn định: file test chạy lại 3 lần liên tiếp + full suite 2 lần, không flake.

---

## 17. Validator

```text
validate_structure            PASS   (21 required path)
validate_project_state        PASS
validate_evidence             PASS   (88 REQUIRED PASS evidence record)
validate_task_completion      PASS   (6 DONE task)
validate_reference_integrity  FAIL   — ĐÚNG 3 issue đã biết của TASK-REM-T06
                                       (/README.md, CODE_OF_CONDUCT.md,
                                        CONTRIBUTING.md) = O-01, giống hệt base
```

Không có regression governance/reference mới.

---

## 18. Phạm vi — những gì KHÔNG bị chạm

```text
production data          : KHÔNG chạm, KHÔNG tạo (toàn bộ fixture là tổng hợp)
Tracking                 : KHÔNG chạm, 0 lệnh ghi
FilePriceProvider        : KHÔNG activate
app/pipeline.py          : KHÔNG đổi (PendingPriceProvider vẫn là default)
TASK-105E                : KHÔNG triển khai
default branch           : KHÔNG đổi
merge                    : KHÔNG thực hiện
task/task-105d-implementation : KHÔNG chạm
Completion Gate frozen   : KHÔNG sửa
data contract            : KHÔNG sửa
TASK-105D                : KHÔNG đánh dấu DONE
```

File thay đổi — **đúng 2**:

```text
M  app/modules/product/identity/store.py           (+301 / −66)
A  tests/test_105d_interprocess_concurrency.py     (mới)
```

cộng các artifact governance của chính phiên repair (bản ghi này, session
log, ledger, progress).

---

## 19. Xử lý HARDENING khác — KHÔNG sửa

`§14` của brief: không sửa cơ hội. Giữ nguyên trạng thái OPEN, không đóng,
không đụng tới:

```text
H-01  tập ĐẾM confirmation_action bị dùng làm tập THẨM QUYỀN   OPEN — KHÔNG SỬA
H-02  (kế thừa H-05) ranking_method_id OPTIONAL nhưng được hash OPEN — KHÔNG SỬA
H-03  test reference sai cho CHECK-105D-26/-27                  OPEN — KHÔNG SỬA
H-04  rebuild_index() O(n) mỗi append ⇒ O(n²) bulk              OPEN — KHÔNG SỬA
H-05  dòng log sai khuôn raise lỗi ngoài miền                   OPEN — KHÔNG SỬA
H-06  hai test migration/rollback mỏng                          OPEN — KHÔNG SỬA
H-07  32 trường Status: còn NOT_TESTED chặn DONE                OPEN — KHÔNG SỬA
HB-105D-F2-01 / -02 / -03                                       OPEN — KHÔNG SỬA
O-01 / O-02 / O-03                                              OUT_OF_SCOPE
```

Ghi chú về `H-05` (dòng log sai khuôn): `_load_log()` bị thay bằng
`_consume()` vì cơ chế nạp lại tăng dần **bắt buộc** phải như vậy — nhưng
thông điệp lỗi và loại exception được giữ NGUYÊN VĂN, nên `H-05` không được
đóng cũng không bị làm nặng thêm. Đây là trường hợp `§14` gọi là "repair
mechanically requires touching one": lý do được nêu ở đây trước khi sửa.

Ghi chú về `H-04`: `§12` cho thấy khoá không tạo hồi quy vật chất (+4…9 %),
nên `H-04` giữ nguyên phân loại HARDENING theo đúng `§13` của brief.

---

## 20. Tiêu chí đóng `B-01` (`§16`)

| # | Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|---|
| 1 | Khoá liên-tiến-trình THẬT tồn tại | ĐẠT | `fcntl.flock(LOCK_EX)` trên `<log>.lock`; §4 |
| 2 | Kiểm version nằm TRONG khoá | ĐẠT | `_require_version` chỉ gọi được từ trong `_transaction()`; §5 |
| 3 | State quyền uy được nạp lại TRONG khoá, TRƯỚC kiểm version | ĐẠT | `_refresh_from_disk()` chạy trước `yield`; §5 |
| 4 | Race hai tiến trình cùng version → đúng một người thắng | ĐẠT | 60/60 vòng: 1 APPLIED + 1 conflict; §6 |
| 5 | Kẻ ghi cũ KHÔNG append được | ĐẠT | đúng 1 dòng log ở mọi vòng; §6 |
| 6 | Store reopen vẫn hợp lệ | ĐẠT | §7 |
| 7 | Không có mutation CONFIRMED trùng lặp | ĐẠT | §7, §10 |
| 8 | Không còn lỗi toàn vẹn vĩnh viễn | ĐẠT | §7 |
| 9 | Idempotency sẵn có vẫn đúng | ĐẠT | §9 + 174 test cũ vẫn PASS |
| 10 | Không regression | ĐẠT | Golden không đổi; full +25 = đúng số test mới; §16 |

**Disposition `B-01`: CODE-LEVEL RESOLVED / READY FOR INDEPENDENT RE-REVIEW.**

Đây KHÔNG phải governance closure. Independent Review #2 sở hữu việc xác
minh; phiên này không tự tuyên bố PASS.

---

## 21. Ngân sách repair

```text
trước RC-1 : 2 allowed / 0 used / 2 remaining
sau  RC-1  : 2 allowed / 1 used / 1 remaining
```

Đúng MỘT cycle được tiêu thụ cho toàn bộ diff repair này, kể cả các lần lặp
bên trong (thêm `O_NOFOLLOW`, thêm test crash-release, bỏ state thừa) —
`V4.1` §3: mọi defect do chính cycle hiện tại tạo/sửa thuộc CÙNG cycle.

```text
cycles:
    - id: TASK-105D-RC-1
      base_sha: e6252c06347ed5305fc32a77706a3a63f5a950cf
      head_sha: <SHA commit của phiên này>
```

---

## 22. Trạng thái cuối

```text
TASK-105D = REPAIR CANDIDATE — READY FOR INDEPENDENT REVIEW #2

NOT DONE / NOT MERGED / NOT INDEPENDENT-REVIEWED-2
```

**Hành động kế tiếp được phép:** Independent Implementation Review #2, do một
phiên KHÁC thực hiện, trên nhánh `task/task-105d-rc1`, với `B-01` là trọng
tâm và toàn bộ HARDENING ở §19 vẫn mở.
