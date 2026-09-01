"""Chọn backend lưu trữ Run/Artifact cho Reports Web (S071B).

Hai backend cùng thoả một interface tối thiểu (``create_run``/``get_run``/
``list_runs``/``save_artifact``/``artifact_response``) — ``app/web/
server.py`` không cần biết đang chạy trên backend nào:

- ``LocalRunStore`` — hành vi S070/S071 giữ nguyên: SQLite
  (``app.web.run_registry.RunRegistry``) + file .xlsx cục bộ dưới
  ``artifact_dir``. Dùng khi R2 chưa cấu hình (dev/test).
- ``R2RunStore`` — Cloudflare R2 (``tools.storage.r2_store``): không
  SQLite, không đĩa persistent. Production stateless (S071B).

``build()`` chọn backend một lần khi tạo Flask app, không phải mỗi
request — nhưng cả hai backend vẫn stateless-per-call.

Fail closed: khi ``REPORTS_REQUIRE_R2`` bật nhưng R2 chưa cấu hình đủ,
``build()`` raise ``StorageConfigurationError`` ngay lúc khởi động — không
âm thầm rơi về SQLite/đĩa ephemeral trong production.
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any, Optional, Protocol

from flask import Response, send_file

from app.web import run_registry
from tools.storage import r2_store
from tools.storage.errors import CorruptRunRecordError

REQUIRE_R2_ENV_VAR = "REPORTS_REQUIRE_R2"

XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class StorageConfigurationError(RuntimeError):
    """``REQUIRE_R2_ENV_VAR`` bật nhưng thiếu credential R2."""


class RunStore(Protocol):
    def create_run(self, **kwargs: Any) -> None: ...
    def get_run(self, run_id: str) -> Optional[run_registry.RunRecord]: ...
    def list_runs(self, *, limit: int = 50) -> list[run_registry.RunRecord]: ...
    def save_artifact(self, temp_path: Path, run_id: str) -> str: ...
    def artifact_response(self, record: run_registry.RunRecord) -> Optional[Response]: ...


class LocalRunStore:
    """SQLite + file cục bộ — hành vi S070/S071 không đổi."""

    def __init__(self, *, db_path: Path, artifact_dir: Path) -> None:
        self._registry = run_registry.RunRegistry(db_path=db_path)
        self._artifact_dir = artifact_dir

    def create_run(self, **kwargs: Any) -> None:
        self._registry.create_run(**kwargs)

    def get_run(self, run_id: str) -> Optional[run_registry.RunRecord]:
        return self._registry.get_run(run_id)

    def list_runs(self, *, limit: int = 50) -> list[run_registry.RunRecord]:
        return self._registry.list_runs(limit=limit)

    def save_artifact(self, temp_path: Path, run_id: str) -> str:
        # Exporter đã ghi thẳng dưới artifact_dir — chỉ cần path tương đối.
        return str(temp_path.relative_to(self._artifact_dir))

    def artifact_response(self, record: run_registry.RunRecord) -> Optional[Response]:
        candidate = (self._artifact_dir / record.artifact_path).resolve()
        try:
            candidate.relative_to(self._artifact_dir)
        except ValueError:
            return None
        if not candidate.is_file():
            return None
        return send_file(candidate, as_attachment=True, download_name=candidate.name)


class R2RunStore:
    """Cloudflare R2 — stateless. ``client``/``env`` cho phép test tiêm một
    fake S3-compatible client thay vì cần credential R2 thật."""

    def __init__(self, *, client=None, env: Optional[dict[str, str]] = None) -> None:
        self._client = client
        self._env = env

    def create_run(self, **kwargs: Any) -> None:
        run_id = kwargs["run_id"]
        if not r2_store.is_valid_run_id(run_id):
            raise ValueError(f"run_id không hợp lệ: {run_id!r}")
        payload = {
            "run_id": run_id,
            "created_at": kwargs["created_at"],
            "status": kwargs["status"],
            "workbook_display_name": kwargs.get("workbook_display_name"),
            "artifact_path": kwargs.get("artifact_path"),
            "view": kwargs.get("view"),
            "tracking_evidence": kwargs.get("tracking_evidence"),
            "error_message": kwargs.get("error_message"),
        }
        r2_store.put_json_if_absent(
            r2_store.run_key(run_id), payload, client=self._client, env=self._env,
        )

    def get_run(self, run_id: str) -> Optional[run_registry.RunRecord]:
        if not r2_store.is_valid_run_id(run_id):
            return None
        payload = r2_store.get_json(r2_store.run_key(run_id), client=self._client, env=self._env)
        return _payload_to_record(payload) if payload is not None else None

    def list_runs(self, *, limit: int = 50) -> list[run_registry.RunRecord]:
        keys = r2_store.list_run_keys_desc(limit=limit, client=self._client, env=self._env)
        records: list[run_registry.RunRecord] = []
        for key in keys:
            try:
                payload = r2_store.get_json(key, client=self._client, env=self._env)
            except CorruptRunRecordError:
                continue  # một record hỏng không được kéo sập cả trang lịch sử
            if payload is not None:
                records.append(_payload_to_record(payload))
        records.sort(key=lambda record: (record.created_at, record.run_id), reverse=True)
        return records[:limit]

    def save_artifact(self, temp_path: Path, run_id: str) -> str:
        if not r2_store.is_valid_run_id(run_id):
            raise ValueError(f"run_id không hợp lệ: {run_id!r}")
        key = r2_store.artifact_key(run_id)
        data = temp_path.read_bytes()
        r2_store.put_bytes(
            key, data, content_type=XLSX_CONTENT_TYPE, client=self._client, env=self._env,
        )
        temp_path.unlink(missing_ok=True)
        return key

    def artifact_response(self, record: run_registry.RunRecord) -> Optional[Response]:
        # Key luôn tự suy từ run_id authoritative — không tin artifact_path
        # đọc từ registry/browser làm key R2 trực tiếp.
        expected_key = r2_store.artifact_key(record.run_id)
        if record.artifact_path != expected_key:
            return None
        data = r2_store.get_bytes(expected_key, client=self._client, env=self._env)
        if data is None:
            return None
        return send_file(
            io.BytesIO(data), as_attachment=True,
            download_name=f"{record.run_id}.xlsx", mimetype=XLSX_CONTENT_TYPE,
        )


def _payload_to_record(payload: dict) -> run_registry.RunRecord:
    return run_registry.RunRecord(
        run_id=payload["run_id"],
        created_at=payload["created_at"],
        status=payload["status"],
        workbook_display_name=payload.get("workbook_display_name"),
        artifact_path=payload.get("artifact_path"),
        view=payload.get("view"),
        tracking_evidence=payload.get("tracking_evidence"),
        error_message=payload.get("error_message"),
    )


def build(*, db_path: Path, artifact_dir: Path) -> RunStore:
    require_r2 = os.environ.get(REQUIRE_R2_ENV_VAR, "").strip().lower() in {"1", "true", "yes"}
    if r2_store.is_configured():
        return R2RunStore()
    if require_r2:
        raise StorageConfigurationError(
            f"{REQUIRE_R2_ENV_VAR} yêu cầu R2 nhưng thiếu credential — cần đủ "
            f"{r2_store.ACCOUNT_ID_ENV_VAR}, {r2_store.BUCKET_ENV_VAR}, "
            f"{r2_store.ACCESS_KEY_ID_ENV_VAR}, {r2_store.SECRET_ACCESS_KEY_ENV_VAR}."
        )
    return LocalRunStore(db_path=db_path, artifact_dir=artifact_dir)
