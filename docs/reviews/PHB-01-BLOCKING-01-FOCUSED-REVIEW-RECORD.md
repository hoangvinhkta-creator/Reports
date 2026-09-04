# RÀ SOÁT ĐỘC LẬP (INDEPENDENT REVIEW) — PHB-01 BLOCKING-01 FOCUSED RE-REVIEW

Review ID:
PHB-01-BLOCKING-01-REVIEW-2

Task / Release:
PHB-01 (Product Identity Manual Resolution V1, contract `PHB-PI-001`) —
focused re-review of the narrow `BLOCKING-01` repair only. Không phải một
lượt review toàn vertical lần hai; D1/D2 và mục A–G không mở lại.

Reviewer Session:
Độc lập, phiên riêng, read-only (không cùng phiên với implementation S112
hay với round 1 review đã tìm ra `BLOCKING-01`).

Executed By:
Claude Code — độc lập, read-only. Model được cấu hình cho phiên review:
`claude-opus-5` (configured; serving model may differ — ghi nguyên văn như
artifact gốc, không tự xác minh được model thực sự phục vụ từ phiên này).
Effort: High.

Timestamp:
2026-09-04

Evidence Level:
E1/E2 hỗn hợp — verification bằng mutation testing trực tiếp trên
`public/index.html` thật (không chỉ đọc báo cáo sửa lỗi), cộng đối chiếu
diff/grep tĩnh cho phần D8 containment và Reports doc delta.

## Scope

Chỉ đúng phạm vi hẹp của bản sửa `BLOCKING-01` (Tracking
`f0873942a419bc2b18431e6a94668a81eb02235f` → `53993f18f67e76927a2b7e115fdc61301cdfb4ec`).
KHÔNG re-review toàn bộ D1/D2/D8/A–G của PHB-01 (đã PASS ở round 1, không
mở lại). KHÔNG Production E2E. KHÔNG deploy. KHÔNG PHB-02.

Lineage đã xác minh TRƯỚC khi đọc bất kỳ dòng mã nào:

```text
TRACKING_HEAD  = 53993f18f67e76927a2b7e115fdc61301cdfb4ec  (== expected)
REPORTS_HEAD   = 8ba7e4612ae744e245010f13e94e78d36f0e9d92  (== expected)
```

## Chuỗi bàn giao (chain of custody)

Nội dung artifact bên dưới nhận được ở dạng file đính kèm từ Owner (upload
ngoài repository, không phải một đường dẫn trong cây mã nguồn) trong phiên
governance-sync này — KHÔNG phải sản phẩm trực tiếp của chính phiên
governance-sync này (phiên này KHÔNG thực hiện review, đúng như S112 và
governance yêu cầu). Trước khi đưa vào canonical record, phiên
governance-sync này đã **độc lập tái xác minh** (không chỉ tin nội dung
artifact) các điểm sau, trực tiếp trên hai repository:

```text
git diff f0873942..53993f18 --stat  → ĐÚNG 2 file: kiem/phan-loai-ten-hang.js,
                                        public/index.html — khớp DELTA_BOUNDARY
public/index.html dòng ~7065        → khớp NGUYÊN VĂN snippet artifact trích
APP_BUILD "b124" → "b125"           → khớp
db.ref("inv").set(                  → 0 lời gọi thật (chỉ còn trong comment)
                                        → khớp WHOLE_INV_WRITE_REINTRODUCED = NO
saveInvPaths(...) call sites        → 9 chỗ (khớp "chín chỗ gọi" đã đính chính)
npm test (chạy thật trên 53993f18)  → phan-loai-ten-hang.js: 72 đạt, 0 hỏng
                                        59 bộ · 2572 đạt · 0 hỏng · 2 bỏ qua
                                        → KHỚP CHÍNH XÁC FOCUSED_TEST_RESULTS
                                        và TRACKING_FULL_SUITE mà artifact nêu
```

Mutation-testing narrative (mục "Test quality" bên dưới) là claim của
artifact, KHÔNG được phiên governance-sync này lặp lại độc lập (lặp lại sẽ
là "thực hiện thêm một lượt review", việc bị cấm rõ trong chỉ thị của
phiên này). Phần được xác minh độc lập là phần có thể kiểm bằng diff/grep/
chạy thật — đã liệt kê ở trên và đều khớp.

---

## Nội dung artifact gốc (giữ nguyên, không viết lại)

```
PHB-01 BLOCKING-01 FOCUSED RE-REVIEW
```

`REVIEW_SESSION  = independent re-review, read-only`

`AGENT           = Claude Code`

`MODEL           = claude-opus-5 (configured; serving model may differ)`

`EFFORT          = High`

`──────────────────────────────────────────────`

`TARGET_VERIFICATION`

`──────────────────────────────────────────────`

`TRACKING_BRANCH         = claude/phb-01-product-identity-manual-o28bsn`

`TRACKING_HEAD           = 53993f18f67e76927a2b7e115fdc61301cdfb4ec  ✓ expected`

`TRACKING_ANCESTOR_f0873942 = YES`

`TRACKING_WORKTREE_CLEAN = YES (verified before and after mutation testing)`

`REPORTS_BRANCH          = claude/phb-01-product-identity-manual-o28bsn`

`REPORTS_HEAD            = 8ba7e4612ae744e245010f13e94e78d36f0e9d92  ✓ expected`

`REPORTS_ANCESTOR_e7a5595 = YES`

`REPORTS_WORKTREE_CLEAN  = YES`

`TARGET_GATE = PASS`

**Two target-gate notes, neither a mismatch of reviewed content:**

- The session's local Reports checkout was one commit stale (`e7a5595`). I fetched and reviewed `8ba7e46` from the fetched ref **without switching or modifying branches**, as instructed.
- Tracking was not on disk. I attached and cloned it fresh; its default branch `main` sits at `9ede079` (pre-PHB-01), consistent with "Tracking builds from `main`; this branch does not reach production."

```
DELTA_BOUNDARY = PASS
```

Tracking `f087394..53993f1` = exactly 2 files, and [public/index.html](https://github.com/hoangvinhkta-creator/Reports/blob/claude/phb-01-product-identity-manual-o28bsn/public/index.html) contains exactly 2 hunks:

| **#ChangeIn claimed scope** |                                                                                                                                                                                                         |                                            |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| 1                           | `loadInv()` cloud migration persistence repair (1 line + comment)                                                                                                                                       | yes                                        |
| 2                           | `APP_BUILD "b124" → "b125"`                                                                                                                                                                             | yes (repo convention, stated at line 2662) |
| 3                           | [kiem/phan-loai-ten-hang.js](https://github.com/hoangvinhkta-creator/Reports/blob/claude/phb-01-product-identity-manual-o28bsn/kiem/phan-loai-ten-hang.js) section H + real-source `grab()` extractions | yes                                        |
| 4                           | fake datastore `once()` deep-copy                                                                                                                                                                       | yes                                        |

No unrelated functional change. Reports delta = 2 `.md` files, zero non-markdown.

---

### Primary verification

```
BLOCKING_01                     = CLOSED
```

`MIGRATION_PERSISTENCE_SEMANTICS = PASS`

`MIGRATION_TERMINATION           = PASS`

`ECONOMIC_STATE_PRESERVATION     = PASS`

`MAP_PRESERVATION                = PASS`

The real path ([public/index.html:7065](https://github.com/hoangvinhkta-creator/Reports/blob/claude/phb-01-product-identity-manual-o28bsn/public/index.html#L7065)) is now:

```
try{ await saveInvPaths({cu: INV.cu || null, moi: INV.moi || null}); }
```

`saveInvPaths` → `db.ref("inv").update(duong)`. Checked against actual source semantics:

- **Writes to ****`/inv/cu`**** and ****`/inv/moi`** as named children of an `update()` — **not** a whole `/inv` write. `map` is a sibling and is absent from the path list, so it survives untouched.
- **All eight fields persist.** `invMigrateGia()` (line 6992) mutates `gia`, `tay`, `giaV2` in the `!giaV2` branch, and `lo`, `cong`, `congTay`, `lotRequired`, `giaV3` in the `!giaV3` branch, plus orphan cleanup. Whole-card replacement covers every one; the old four-table form covered `gia`/`lo`/`cong`/`congTay` only, dropping all four migration-critical fields.
- **Deletion semantics are correct.** Firebase `update()` replaces a named child node wholesale, so the rebuilt `tay` cannot leave stale keys behind — the exact case the four-table write missed. `INV.cu || null` correctly deletes an absent card; migration cannot trigger on a null slot anyway (`invMigrateGia` returns false on `!s`).
- **The RAM snapshot is fresh, not stale.** `INV` is read from the server microseconds earlier in the same function. This is what distinguishes it from the removed `saveInv()`, whose snapshot could be hours old — the D8 hazard is not reintroduced.
- **Shape matches precedent.** `invUndoDay()` (line 7319) already writes `{cu, moi}` identically, and matches the shape S112 declared ("qua ngày / hoàn tác / di trú giá → cu, moi").

---

### Test quality — verified by mutation, not by report

```
TEST_QUALITY     = PASS
```

`NEGATIVE_CONTROL = PASS`

I did not accept the repair report as evidence. Three independent checks:

**1. The test runs real production logic.** `NEN` extracts `loadInv`, `invMigrateGia`, `invMigrate`, `invRowKey`, `invOldKey`, `invCode`, `extractCode` from [public/index.html](https://github.com/hoangvinhkta-creator/Reports/blob/claude/phb-01-product-identity-manual-o28bsn/public/index.html) via `cat()`, which **throws** when a regex misses ([kiem/khung.js:33](https://github.com/hoangvinhkta-creator/Reports/blob/claude/phb-01-product-identity-manual-o28bsn/kiem/khung.js#L33)) — extraction cannot silently degrade into a vacuous test.

**2. Mutation test — I reverted the real production line to the pre-repair shape.** Section H went red with 8 failures, reproducing the reported regression precisely:

```
LỖI giaV2 đã xuống máy chủ                  được undefined  mong true
```

`LỖI giaV3 đã xuống máy chủ                  được undefined  mong true`

`LỖI lotRequired ... đã xuống máy chủ        được true       mong false`

`LỖI tay ... đã xuống máy chủ                được "undefined" mong "object"`

`LỖI lần nạp trang sau không ghi gì nữa      được 2          mong 1`

`LỖI giá lô người dùng gõ còn nguyên         được {}         mong {…:6800}`

`LỖI giá công khai và cờ gõ-tay cũng còn nguyên`

`                                            được [{…:7000},{}]`

`                                            mong [{…:9500},{…:true}]`

That is the original regression exactly: `lo` wiped to `{}`, `cong` reverted from the operator's 9500 back to the migrated 7000, `congTay` cleared.

**3. The ****`once()`**** deep-copy is a false-negative removal, not a manufactured PASS.** With the buggy production code **and** `once()` reverted to a live reference, 7 of those 8 assertions falsely turn green (only the call-shape assertion, which inspects `db.goi` rather than server state, still catches it). A live reference makes every RAM mutation auto-"saved," masking precisely this bug class. Real Firebase decodes fresh objects off the wire, so the deep copy is the faithful semantics. The fake store also deep-copies on write (`datDuong`), and `update()` correctly replaces named children — the harness observes server state, not shared mutable RAM.

The in-file negative control (`H-đối chứng`) independently rebuilds the pre-repair `loadInv()` body from the same real functions and asserts the old shape fails.

---

### D8 containment

```
D8_OTHER_CALLSITES_CHANGED   = NO
```

`WHOLE_INV_WRITE_REINTRODUCED = NO`

`D8_FINAL                     = PASS`

The `index.html` diff is 2 hunks; the other eight `saveInvPaths` call sites are byte-identical to `f087394`. Grep at `53993f1` finds **no** `db.ref("inv").set(` — only `.once("value")` (read) and `.update(duong)`; the residual `saveInv()` mentions are inside explanatory comments. Nine call sites total, confirming the documentation correction. Mapping persistence remains granular via `saveInvMapKey → saveInvPaths({["map/"+k]: v})`.

---

### Reports doc delta

```
REPORTS_FUNCTIONAL_CHANGE = NO
```

`DOCUMENTATION_8_TO_9      = PASS`

"8 chỗ gọi" → "CHÍN chỗ gọi" corrected in both files, with the nine line numbers cited. Status correctly held: `PHB01_STATUS = IMPLEMENTED (COMPLETE_FOR_REVIEW) — CHƯA DONE`, `CODE_REVIEW_GATE = PENDING_RE_REVIEW`. Not marked DONE. Section H honestly records that the first PASS was overturned.

---

### Test execution

```
FOCUSED_TEST_RESULTS = kiem/phan-loai-ten-hang.js — 72 đạt, 0 hỏng (exit 0)
```

`TRACKING_FULL_SUITE  = 59 bộ · 2572 đạt · 0 hỏng · 2 bỏ qua  (exit 0)`

Matches the implementation report exactly (59 / 2572 / 0 / 2). Reports full suite not run — its delta contains no functional code, per §10.

---

### Findings

```
NEW_BLOCKING_FINDINGS = NONE
```

**NON\_BLOCKING\_FINDINGS** (informational; no task created, per §11):

1. **Migration write widens the concurrent-overwrite window** for `/inv/cu` and `/inv/moi` from four price tables to the whole card, including `rows`. Bounded and accepted: it fires only for a never-migrated card (effectively once, at first load after deploy), immediately after a fresh read, and matches the existing `invUndoDay()` precedent. `map` is unaffected either way.
2. The `!CLOUD` branch (line 7041) still passes `invGiaDuong(...)` while the cloud branch passes whole cards. Harmless — `saveInvPaths` ignores `upd` entirely when `!CLOUD` and serializes all of `INV` to localStorage, so flags do persist locally. This is the previously-recorded informational finding; the repair did not change its production consequence, so per §11 it is not reopened.

---

### Gate

```
H_REGRESSION     = PASS
```

`CODE_REVIEW_GATE = PASS`

`PRODUCTION_E2E   = NOT_RUN`

`SCOPE_DRIFT      = NO`

BLOCKING-01 is closed on the real production path, proven by mutation testing rather than by the repair report. No new blocking regression. D1/D2 and areas A–G are not reopened — nothing contradictory surfaced.

**NEXT\_VERTICAL\_ACTION:** PHB-01 may move from `IMPLEMENTED (COMPLETE_FOR_REVIEW)` to code-review-cleared. Remaining before `DONE` is the separate, still-outstanding gate: `PRODUCTION_E2E` (this session had no production egress; Tracking builds from `main`, which is at `9ede079` and does not carry this branch). PHB-02 not opened.
