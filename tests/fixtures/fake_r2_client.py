"""Fake S3-compatible client cho test R2 adapter (S071B) — không cần
credential/mạng R2 thật (``tools/storage/r2_store.py``,
``app/web/storage_backend.py``). Tiêm qua tham số ``client=`` mà cả hai
module đó đã hỗ trợ cho mục đích test.
"""

from __future__ import annotations

from typing import Any, Callable, Optional, Union


class FakeClientError(Exception):
    """Mô phỏng hình dạng ``botocore.exceptions.ClientError`` mà
    ``tools.storage.r2_store`` đọc qua ``exc.response["Error"]["Code"]``."""

    def __init__(self, code: str, message: str = "fake-error") -> None:
        super().__init__(message)
        self.response = {"Error": {"Code": code, "Message": message}}


class _FakeBody:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data


class FakeR2Client:
    """Lưu trữ in-memory. ``fail`` cho phép tiêm lỗi cho một method cụ thể
    (timeout/auth/unavailable/...) — key = tên method boto3, value = một
    exception instance hoặc callable trả về exception."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.fail: dict[str, Union[Exception, Callable[[], Exception]]] = {}
        self.calls: list[tuple[str, str]] = []

    def put_raw(self, key: str, data: bytes) -> None:
        """Ghi thẳng, bỏ qua mọi logic của r2_store — dùng để dựng sẵn dữ
        liệu hỏng/không hợp lệ cho test (vd JSON corrupt)."""
        self.objects[key] = data

    def _maybe_fail(self, method: str) -> None:
        trigger = self.fail.get(method)
        if trigger is None:
            return
        raise trigger() if callable(trigger) else trigger

    def head_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        self.calls.append(("head_object", Key))
        self._maybe_fail("head_object")
        if Key not in self.objects:
            raise FakeClientError("404")
        return {"ContentLength": len(self.objects[Key])}

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        self.calls.append(("get_object", Key))
        self._maybe_fail("get_object")
        if Key not in self.objects:
            raise FakeClientError("NoSuchKey")
        return {"Body": _FakeBody(self.objects[Key])}

    def put_object(
        self, *, Bucket: str, Key: str, Body: bytes, ContentType: str = "",
    ) -> dict[str, Any]:
        self.calls.append(("put_object", Key))
        self._maybe_fail("put_object")
        self.objects[Key] = bytes(Body)
        return {}

    def list_objects_v2(
        self, *, Bucket: str, Prefix: str = "", MaxKeys: int = 1000,
        ContinuationToken: Optional[str] = None,
    ) -> dict[str, Any]:
        self.calls.append(("list_objects_v2", Prefix))
        self._maybe_fail("list_objects_v2")
        matching = sorted(key for key in self.objects if key.startswith(Prefix))
        return {"Contents": [{"Key": key} for key in matching]}
