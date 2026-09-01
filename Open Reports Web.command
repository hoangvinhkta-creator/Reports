#!/bin/zsh
set -euo pipefail
cd "$(dirname "$0")"
if ! python3 -c "import flask" >/dev/null 2>&1; then
  echo "Reports Web cần cài đặt thêm gói 'flask' một lần."
  echo "Chạy lệnh sau rồi mở lại file này:"
  echo "  python3 -m pip install flask"
  exit 1
fi
exec python3 -m app.web.launcher
