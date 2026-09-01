"""S071 Deployment Gate — ``REPORTS_DATA_ROOT`` gộp registry + artifact dưới
MỘT persistent disk gốc.

Một số hosting managed (vd Render Web Service) chỉ cho gắn ĐÚNG MỘT
persistent disk mỗi service. Registry SQLite (``app.web.run_registry``) và
artifact/upload/tracking-tạm (``app.web.server``) phải trỏ vào cùng gốc mount
đó khi biến ``REPORTS_DATA_ROOT`` được đặt, và giữ NGUYÊN đường cũ (tương đối
``REPO_ROOT``) khi biến vắng mặt — không đổi hành vi local/test đã có.

Cả hai module đọc biến môi trường Ở THỜI ĐIỂM IMPORT (module-level
constant), nên test phải ``importlib.reload`` sau khi set biến, và luôn phục
hồi lại trạng thái module gốc ở cuối — các test khác trong bộ suite import
``app.web.server``/``app.web.run_registry`` dựa trên hằng số REPO_ROOT mặc
định.
"""

from __future__ import annotations

import importlib

from app.web import run_registry as run_registry_module
from app.web import server as server_module


def _reload_with_env(monkeypatch, data_root):
    monkeypatch.setenv("REPORTS_DATA_ROOT", str(data_root))
    importlib.reload(run_registry_module)
    importlib.reload(server_module)


def _reload_defaults(monkeypatch):
    monkeypatch.delenv("REPORTS_DATA_ROOT", raising=False)
    importlib.reload(run_registry_module)
    importlib.reload(server_module)


def test_data_root_env_var_relocates_registry_and_artifact_paths_together(
    monkeypatch, tmp_path
):
    data_root = tmp_path / "persistent-disk"
    try:
        _reload_with_env(monkeypatch, data_root)

        assert run_registry_module.DEFAULT_DB_PATH == data_root / "data" / "web_runs" / "runs.db"
        assert server_module.UPLOAD_DIR == data_root / "data" / "uploads"
        assert server_module.ARTIFACT_DIR == (data_root / "outputs" / "reports").resolve()
        assert server_module.TRACKING_TEMP_DIR == data_root / "data" / "tracking_live_tmp"

        # Registry và artifact nằm CÙNG một gốc disk — không phải hai
        # persistent volume tách biệt (đúng ràng buộc "một disk mỗi service").
        assert run_registry_module.DEFAULT_DB_PATH.is_relative_to(data_root)
        assert server_module.ARTIFACT_DIR.is_relative_to(data_root)
    finally:
        _reload_defaults(monkeypatch)


def test_missing_data_root_env_var_keeps_the_original_repo_relative_paths(monkeypatch):
    """Mặc định (biến vắng mặt, đúng mọi môi trường local/test đã có từ
    trước S071 deployment gate) không đổi — regression bảo vệ hành vi cũ."""
    try:
        _reload_defaults(monkeypatch)

        repo_root = server_module.REPO_ROOT
        assert server_module.UPLOAD_DIR == repo_root / "data" / "uploads"
        assert server_module.ARTIFACT_DIR == (repo_root / "outputs" / "reports").resolve()
        assert run_registry_module.DEFAULT_DB_PATH == repo_root / "data" / "web_runs" / "runs.db"
    finally:
        _reload_defaults(monkeypatch)
