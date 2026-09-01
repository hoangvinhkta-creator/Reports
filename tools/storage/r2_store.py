"""Cloudflare R2 storage adapter cho Reports (S071B) — thay SQLite + đĩa
persistent để runtime STATELESS. Xem docs/deployment/S071_DEPLOYMENT.md.

Nằm NGOÀI ``app/`` như ``tools/tracking/live_pull.py``: ``app/`` không được
import trực tiếp một network primitive (``boto3`` nằm trong danh sách cấm
của ``test_no_module_under_app_reaches_the_network``, ADR-101).
``app/web/storage_backend.py`` chỉ gọi hàm public ở đây, không tự
``import boto3``.

Object model:
- ``runs/<run_id>.json`` — key = chính run_id. run_id hiện có dạng
  ``report-<UTC timestamp compact>[-NN]`` (xem
  ``app.owner_usability.default_output_path``), đã sortable theo thời gian
  — cho phép ``get_run`` resolve O(1) chính xác VÀ liệt kê mới→cũ bằng sort
  tên khoá giảm dần, không cần một index JSON dùng chung (tránh race khi
  nhiều run được tạo gần đồng thời).
- ``artifacts/<run_id>.xlsx`` — key luôn tự suy từ run_id của run metadata
  authoritative đã fetch, không bao giờ nhận key thô từ browser.

Mỗi hàm public tự tạo (hoặc nhận qua ``client=``/``env=`` để test tiêm
fake) một client ngắn hạn — không connection sống giữa các lời gọi, cùng
triết lý ``RunRegistry._connect`` (SQLite) đã dùng.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

from tools.storage.errors import (
    CorruptRunRecordError, RunAlreadyExistsError, StorageUnavailableError,
)

ACCOUNT_ID_ENV_VAR = "R2_ACCOUNT_ID"
BUCKET_ENV_VAR = "R2_BUCKET"
ACCESS_KEY_ID_ENV_VAR = "R2_ACCESS_KEY_ID"
SECRET_ACCESS_KEY_ENV_VAR = "R2_SECRET_ACCESS_KEY"

_REQUIRED_ENV_VARS = (
    ACCOUNT_ID_ENV_VAR, BUCKET_ENV_VAR, ACCESS_KEY_ID_ENV_VAR, SECRET_ACCESS_KEY_ENV_VAR,
)

RUN_KEY_PREFIX = "runs/"
ARTIFACT_KEY_PREFIX = "artifacts/"

# run_id do server tự sinh — chỉ alnum/dash/underscore, chặn path traversal
# trước khi ghép thành key R2.
_SAFE_RUN_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def is_configured(env: Optional[dict[str, str]] = None) -> bool:
    """Cùng semantics ``live_pull.is_configured``: absent = chọn nhánh
    fallback SQLite/local, KHÔNG phải lỗi kiến trúc."""
    source = env if env is not None else os.environ
    return all(source.get(name) for name in _REQUIRED_ENV_VARS)


def is_valid_run_id(run_id: str) -> bool:
    return bool(_SAFE_RUN_ID.match(run_id))


def run_key(run_id: str) -> str:
    return f"{RUN_KEY_PREFIX}{run_id}.json"


def artifact_key(run_id: str) -> str:
    return f"{ARTIFACT_KEY_PREFIX}{run_id}.xlsx"


def _client(env: Optional[dict[str, str]] = None):
    import boto3  # cục bộ — module này là ranh giới network duy nhất.

    source = env if env is not None else os.environ
    account_id = source[ACCOUNT_ID_ENV_VAR]
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=source[ACCESS_KEY_ID_ENV_VAR],
        aws_secret_access_key=source[SECRET_ACCESS_KEY_ENV_VAR],
        region_name="auto",
    )


def _bucket(env: Optional[dict[str, str]] = None) -> str:
    source = env if env is not None else os.environ
    return source[BUCKET_ENV_VAR]


def put_json_if_absent(
    key: str, payload: dict[str, Any], *, client=None, env: Optional[dict[str, str]] = None,
) -> None:
    """Ghi mới; raise ``RunAlreadyExistsError`` nếu key đã tồn tại.

    HEAD-rồi-PUT, không ``IfNoneMatch`` điều kiện — một khe race lý thuyết
    giữa hai lời gọi đồng thời CÙNG run_id, nhưng run_id luôn do server sinh
    mới (trùng là lỗi lập trình, không phải kịch bản concurrency thật).
    """
    client = client or _client(env)
    bucket = _bucket(env)
    try:
        client.head_object(Bucket=bucket, Key=key)
    except Exception as exc:
        if not _is_not_found(exc):
            raise StorageUnavailableError(str(exc)) from exc
    else:
        raise RunAlreadyExistsError(key)
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    try:
        client.put_object(Bucket=bucket, Key=key, Body=body, ContentType="application/json")
    except Exception as exc:
        raise StorageUnavailableError(str(exc)) from exc


def get_json(
    key: str, *, client=None, env: Optional[dict[str, str]] = None,
) -> Optional[dict[str, Any]]:
    """``None`` nếu key không tồn tại; raise ``CorruptRunRecordError`` nếu
    object có nhưng JSON hỏng — không bao giờ trả ``None`` cho trường hợp
    này (tránh giả làm "không tồn tại")."""
    client = client or _client(env)
    try:
        response = client.get_object(Bucket=_bucket(env), Key=key)
    except Exception as exc:
        if _is_not_found(exc):
            return None
        raise StorageUnavailableError(str(exc)) from exc
    raw = response["Body"].read()
    try:
        return json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise CorruptRunRecordError(key) from exc


def list_run_keys_desc(
    *, limit: int, client=None, env: Optional[dict[str, str]] = None,
) -> list[str]:
    """Key dưới ``runs/`` mới nhất trước (sort tên khoá giảm dần, không
    fetch body), quét tối đa 5000 key mỗi lần gọi — đủ cho Internal Beta."""
    client = client or _client(env)
    bucket = _bucket(env)
    keys: list[str] = []
    token = None
    try:
        while True:
            kwargs: dict[str, Any] = {"Bucket": bucket, "Prefix": RUN_KEY_PREFIX, "MaxKeys": 1000}
            if token:
                kwargs["ContinuationToken"] = token
            response = client.list_objects_v2(**kwargs)
            keys.extend(item["Key"] for item in response.get("Contents", []))
            token = response.get("NextContinuationToken")
            if not token or len(keys) >= 5000:
                break
    except Exception as exc:
        raise StorageUnavailableError(str(exc)) from exc
    return sorted(keys, reverse=True)[:limit]


def put_bytes(
    key: str, data: bytes, *, content_type: str, client=None, env: Optional[dict[str, str]] = None,
) -> None:
    """Upload rồi verify bằng ``head_object`` — fail closed nếu kích thước
    không khớp, thay vì để lộ một run "thành công" mà artifact không thật
    sự tồn tại trên R2."""
    client = client or _client(env)
    bucket = _bucket(env)
    try:
        client.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
        head = client.head_object(Bucket=bucket, Key=key)
    except Exception as exc:
        raise StorageUnavailableError(str(exc)) from exc
    if head.get("ContentLength") != len(data):
        raise StorageUnavailableError(f"Verify upload thất bại cho key {key!r}.")


def get_bytes(
    key: str, *, client=None, env: Optional[dict[str, str]] = None,
) -> Optional[bytes]:
    client = client or _client(env)
    try:
        response = client.get_object(Bucket=_bucket(env), Key=key)
    except Exception as exc:
        if _is_not_found(exc):
            return None
        raise StorageUnavailableError(str(exc)) from exc
    return response["Body"].read()


def _error_code(exc: Exception) -> str:
    response = getattr(exc, "response", None)
    if not isinstance(response, dict):
        return ""
    return str(response.get("Error", {}).get("Code", ""))


def _is_not_found(exc: Exception) -> bool:
    return _error_code(exc) in {"NoSuchKey", "404", "NotFound"}
