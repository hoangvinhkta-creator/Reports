#!/usr/bin/env bash
#
# branch_authority_check.sh — Machine Control #1 của Governance V4.1.
#
# Mục đích: xác lập BRANCH AUTHORITY của phiên làm việc TRƯỚC KHI đọc bất kỳ
# tài liệu nào dùng để suy luận trạng thái dự án (PROJECT_PROGRESS.md,
# roadmap, task status, governance state).
#
# Ràng buộc theo V4.1 §0 và §17:
#   - fetch origin;
#   - resolve origin/HEAD ĐỘNG, KHÔNG hard-code "main";
#   - xử lý branch mode (kiểm upstream, báo ahead/behind);
#   - xử lý detached mode với exact TARGET_SHA;
#   - exit non-zero khi authority bất định.
#
# Script này KHÔNG sửa nội dung repository. Nó chỉ đọc trạng thái git và
# (khi cần) cập nhật ref cục bộ refs/remotes/origin/HEAD — đây là metadata
# remote-tracking của bản clone, không phải nội dung được version.
#
# Exit codes:
#   0  AUTHORITY_OK              — trạng thái authority xác định.
#   2  BRANCH_AUTHORITY_UNRESOLVED
#   3  WRONG_REVIEW_TARGET
#   4  NOT_A_GIT_REPOSITORY
#
# Biến môi trường:
#   TARGET_SHA   — bắt buộc khi HEAD detached; SHA phải khớp EXACT.
#   SKIP_FETCH   — đặt "1" để bỏ qua network fetch (dùng cho smoke test
#                  offline). Không dùng trong phiên làm việc thật.

set -u

STATUS_OK=0
STATUS_UNRESOLVED=2
STATUS_WRONG_TARGET=3
STATUS_NOT_REPO=4

emit() { printf '%s\n' "$*"; }

fail_unresolved() {
    emit ""
    emit "STOP — BRANCH AUTHORITY UNRESOLVED"
    emit "Lý do: $*"
    exit "$STATUS_UNRESOLVED"
}

fail_wrong_target() {
    emit ""
    emit "STOP — WRONG REVIEW TARGET"
    emit "Lý do: $*"
    exit "$STATUS_WRONG_TARGET"
}

emit "=== BRANCH AUTHORITY CHECK (Governance V4.1 Machine Control #1) ==="

# ---------------------------------------------------------------- repo check
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    emit ""
    emit "STOP — NOT A GIT REPOSITORY"
    exit "$STATUS_NOT_REPO"
fi

# ---------------------------------------------------------------- fetch
if [ "${SKIP_FETCH:-0}" = "1" ]; then
    emit "fetch                : SKIPPED (SKIP_FETCH=1)"
else
    if git fetch origin --prune >/dev/null 2>&1; then
        emit "fetch                : OK (origin --prune)"
    else
        fail_unresolved "git fetch origin --prune thất bại; không thể xác nhận trạng thái remote."
    fi
fi

# ---------------------------------------------------------------- default ref
# Resolve origin/HEAD một cách ĐỘNG. Không hard-code refs/remotes/origin/main.
DEFAULT_REMOTE_REF="$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null || true)"

if [ -z "$DEFAULT_REMOTE_REF" ] && [ "${SKIP_FETCH:-0}" != "1" ]; then
    # origin/HEAD chưa được ghi trong bản clone này — hỏi lại remote.
    git remote set-head origin -a >/dev/null 2>&1 || true
    DEFAULT_REMOTE_REF="$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null || true)"
fi

if [ -z "$DEFAULT_REMOTE_REF" ]; then
    fail_unresolved "không resolve được origin/HEAD (nhánh mặc định của remote)."
fi

if ! DEFAULT_TIP="$(git rev-parse --verify --quiet "$DEFAULT_REMOTE_REF")"; then
    fail_unresolved "origin/HEAD trỏ tới '$DEFAULT_REMOTE_REF' nhưng ref này không tồn tại cục bộ."
fi

DEFAULT_BRANCH="${DEFAULT_REMOTE_REF#refs/remotes/origin/}"
HEAD_SHA="$(git rev-parse HEAD)"

emit "DEFAULT_REMOTE_REF   : $DEFAULT_REMOTE_REF"
emit "DEFAULT_BRANCH       : $DEFAULT_BRANCH"
emit "DEFAULT_TIP          : $DEFAULT_TIP"
emit "HEAD_SHA             : $HEAD_SHA"

# ---------------------------------------------------------------- worktree
if [ -n "$(git status --porcelain)" ]; then
    WORKTREE_STATE="DIRTY"
else
    WORKTREE_STATE="CLEAN"
fi
emit "WORKTREE             : $WORKTREE_STATE"

# ---------------------------------------------------------------- mode split
if git symbolic-ref -q HEAD >/dev/null 2>&1; then
    # ------------------------------------------------------------ BRANCH MODE
    MODE="BRANCH"
    CURRENT_BRANCH="$(git branch --show-current)"
    emit "MODE                 : BRANCH"
    emit "CURRENT_BRANCH       : $CURRENT_BRANCH"

    UPSTREAM="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
    if [ -z "$UPSTREAM" ]; then
        fail_unresolved "nhánh '$CURRENT_BRANCH' không có upstream; vị trí authority so với remote không xác định. Khắc phục: git push -u origin $CURRENT_BRANCH (hoặc git branch --set-upstream-to=origin/$CURRENT_BRANCH)."
    fi
    emit "UPSTREAM             : $UPSTREAM"

    BEHIND_UPSTREAM="$(git rev-list --count "HEAD..@{u}" 2>/dev/null || true)"
    AHEAD_UPSTREAM="$(git rev-list --count "@{u}..HEAD" 2>/dev/null || true)"
    if [ -z "$BEHIND_UPSTREAM" ] || [ -z "$AHEAD_UPSTREAM" ]; then
        fail_unresolved "không tính được ahead/behind so với upstream '$UPSTREAM'."
    fi
    emit "behind upstream      : $BEHIND_UPSTREAM commit"
    emit "ahead  upstream      : $AHEAD_UPSTREAM commit"

    AHEAD_DEFAULT="$(git rev-list --count "$DEFAULT_REMOTE_REF..HEAD" 2>/dev/null || true)"
    BEHIND_DEFAULT="$(git rev-list --count "HEAD..$DEFAULT_REMOTE_REF" 2>/dev/null || true)"
    if [ -z "$AHEAD_DEFAULT" ] || [ -z "$BEHIND_DEFAULT" ]; then
        fail_unresolved "không tính được ahead/behind so với '$DEFAULT_REMOTE_REF'."
    fi
    emit "ahead  default       : $AHEAD_DEFAULT commit"
    emit "behind default       : $BEHIND_DEFAULT commit"

    AUTHORITY="BRANCH_WITH_UPSTREAM"

    # V4.1 §12 — BRANCH DIVERGENCE LIMIT (chỉ cảnh báo; quyết định thuộc Owner).
    MERGE_BASE="$(git merge-base HEAD "$DEFAULT_REMOTE_REF" 2>/dev/null || true)"
    DIVERGENCE_FLAGS=""
    if [ "$AHEAD_DEFAULT" -gt 10 ]; then
        DIVERGENCE_FLAGS="${DIVERGENCE_FLAGS}ahead>10 "
    fi
    if [ -n "$MERGE_BASE" ]; then
        BASE_EPOCH="$(git log -1 --format=%ct "$MERGE_BASE")"
        HEAD_EPOCH="$(git log -1 --format=%ct HEAD)"
        DIVERGENCE_DAYS=$(( (HEAD_EPOCH - BASE_EPOCH) / 86400 ))
        emit "divergence days      : $DIVERGENCE_DAYS"
        if [ "$DIVERGENCE_DAYS" -gt 3 ] && [ "$AHEAD_DEFAULT" -gt 0 ]; then
            DIVERGENCE_FLAGS="${DIVERGENCE_FLAGS}days>3 "
        fi
        CHANGED_LOC="$(git diff --numstat "$MERGE_BASE..HEAD" 2>/dev/null \
            | awk '{ a = ($1 == "-" ? 0 : $1); d = ($2 == "-" ? 0 : $2); s += a + d } END { print s + 0 }')"
        emit "cumulative LOC       : $CHANGED_LOC"
        if [ "$CHANGED_LOC" -gt 5000 ]; then
            DIVERGENCE_FLAGS="${DIVERGENCE_FLAGS}loc>5000 "
        fi
    fi
    if [ -n "$DIVERGENCE_FLAGS" ]; then
        emit "DIVERGENCE           : INTEGRATION_DECISION_REQUIRED [ ${DIVERGENCE_FLAGS}]"
    else
        emit "DIVERGENCE           : WITHIN_LIMITS"
    fi
else
    # ---------------------------------------------------------- DETACHED MODE
    MODE="DETACHED"
    emit "MODE                 : DETACHED"
    # KHÔNG gọi HEAD..@{u} ở chế độ detached (V4.1 §0.B).

    if [ -z "${TARGET_SHA:-}" ]; then
        fail_unresolved "HEAD detached nhưng phiên không được giao TARGET_SHA; không xác định được review target."
    fi

    if ! RESOLVED_TARGET="$(git rev-parse --verify --quiet "${TARGET_SHA}^{commit}")"; then
        fail_unresolved "TARGET_SHA='${TARGET_SHA}' không resolve được thành commit trong repository này."
    fi

    emit "TARGET_SHA           : $TARGET_SHA"
    emit "TARGET_RESOLVED      : $RESOLVED_TARGET"

    if [ "$HEAD_SHA" = "$RESOLVED_TARGET" ]; then
        AUTHORITY="DETACHED_EXACT_TARGET"
        emit "AUTHORITY            : DETACHED_EXACT_TARGET"
        emit "note                 : detached checkout tới exact target SHA KHÔNG tính là repository modification."
    else
        fail_wrong_target "HEAD=$HEAD_SHA khác TARGET=$RESOLVED_TARGET (yêu cầu khớp exact SHA)."
    fi
fi

emit ""
emit "AUTHORITY            : $AUTHORITY"
emit "RESULT               : AUTHORITY_OK"
exit "$STATUS_OK"
