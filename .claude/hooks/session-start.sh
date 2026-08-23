#!/bin/bash
# SessionStart hook — kiểm tra đồng bộ nhánh trước khi session bắt đầu đọc
# governance hay làm việc. Xem DEC-118 (PROJECT/PROJECT_DECISIONS.md) và
# governance/core/00_SESSION_ORCHESTRATION.md → "Giao thức Mở Phiên", bước 0.
#
# Sự cố mà hook này ngăn chặn: nhiều session song song từng làm việc trên các
# nhánh phân tán mà không kiểm tra lại nhánh mặc định trên origin, dẫn tới hai
# track roadmap tách rời và một lần trùng lặp công việc thật (TASK-000 và
# REM-T02 cùng dời gói governance lên repository root, trên hai nhánh khác
# nhau, không biết về nhau).
set -uo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

REPO_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO_DIR" 2>/dev/null || exit 0

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

SYMREF=$(git ls-remote --symref origin HEAD 2>/dev/null | head -1)
DEFAULT_BRANCH="${SYMREF#ref: refs/heads/}"
DEFAULT_BRANCH="${DEFAULT_BRANCH%%$'\t'*}"

if [ -z "$DEFAULT_BRANCH" ] || [ "$DEFAULT_BRANCH" = "$SYMREF" ]; then
  echo "Không xác định được nhánh mặc định trên origin — bỏ qua kiểm tra đồng bộ nhánh."
  exit 0
fi

if ! git fetch origin "$DEFAULT_BRANCH" --quiet 2>/dev/null; then
  echo "=== ĐỒNG BỘ NHÁNH ==="
  echo "CẢNH BÁO: không fetch được origin/$DEFAULT_BRANCH (mạng/proxy)."
  echo "Không thể xác nhận đồng bộ tự động — coi như CHƯA đồng bộ cho tới khi"
  echo "verify thủ công bằng: git fetch origin $DEFAULT_BRANCH"
  echo "======================"
  exit 0
fi

CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
BEHIND=$(git rev-list --count HEAD.."origin/$DEFAULT_BRANCH" 2>/dev/null)
AHEAD=$(git rev-list --count "origin/$DEFAULT_BRANCH"..HEAD 2>/dev/null)

echo "=== ĐỒNG BỘ NHÁNH (governance/core/00_SESSION_ORCHESTRATION.md → Giao thức Mở Phiên, bước 0) ==="
echo "Nhánh mặc định trên origin (canonical, đóng vai trò 'main'): $DEFAULT_BRANCH"
echo "Nhánh của session này: ${CURRENT_BRANCH:-<detached HEAD>}"

if [ "$CURRENT_BRANCH" = "$DEFAULT_BRANCH" ] && [ "${BEHIND:-0}" = "0" ]; then
  echo "OK — đồng bộ đầy đủ với origin/$DEFAULT_BRANCH."
else
  echo "CẢNH BÁO — session này CHƯA đồng bộ với nhánh mặc định."
  echo "  Lỗi thời (behind) so với origin/$DEFAULT_BRANCH: ${BEHIND:-?} commit."
  echo "  Vượt trước (ahead): ${AHEAD:-?} commit."
  echo "TRƯỚC KHI đọc PROJECT/PROJECT_PROGRESS.md hay bắt đầu bất kỳ task nào:"
  echo "  1. git fetch origin $DEFAULT_BRANCH"
  echo "  2. Đọc trạng thái thật từ origin: git show origin/$DEFAULT_BRANCH:PROJECT/PROJECT_PROGRESS.md"
  echo "  3. Nếu phát hiện một task đã làm trên origin/$DEFAULT_BRANCH mà nhánh"
  echo "     này định làm lại — DỪNG LẠI, hỏi chủ dự án trước khi tiếp tục."
fi
echo "======================================================================"
