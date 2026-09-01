"""WSGI entrypoint cho triển khai shared/production (S071).

Khác ``app/web/launcher.py`` (double-click cục bộ, ``werkzeug.serving.
make_server``, foreground, một tiến trình): file này chỉ export một
callable WSGI chuẩn để một process manager thật (gunicorn) chạy multi-worker,
bind ``0.0.0.0``, và sống lâu dài trên server dùng chung.

Dùng:

    gunicorn --workers 2 --threads 4 --bind 0.0.0.0:$PORT app.web.wsgi:application

Không đổi ``create_app()`` — cùng một Flask app cho cả local launcher và
production WSGI, chỉ khác cách tiến trình được khởi động và bind.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
    sys.path.insert(0, str(REPO_ROOT))

from app.web.server import create_app  # noqa: E402

application = create_app()
