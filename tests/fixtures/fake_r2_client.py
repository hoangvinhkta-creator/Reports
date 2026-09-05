"""Fake S3-compatible client cho test R2 adapter (S071B) — không cần
credential/mạng R2 thật (``tools/storage/r2_store.py``,
``app/web/storage_backend.py``). Tiêm qua tham số ``client=`` mà cả hai
module đó đã hỗ trợ cho mục đích test.
"""

from __future__ import annotations

import threading
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
        #: Khoá bảo vệ đúng đoạn kiểm-tra-rồi-ghi của PUT có điều kiện
        #: (``IfNoneMatch="*"``) — mô phỏng một request PUT có điều kiện thật
        #: là MỘT thao tác nguyên tử phía server, không phải hai bước rời
        #: nhau mà caller tự ghép.
        self._conditional_write_lock = threading.Lock()
        #: Tên method -> callable() gọi ĐÚNG trước bước method đó đọc trạng
        #: thái để quyết định absent/present. Test tiêm một
        #: ``threading.Barrier`` vào đây để ép hai luồng cùng đứng lại ở
        #: đúng điểm quyết định trước khi cho cả hai đi tiếp — mô phỏng đúng
        #: hình dạng một cuộc đua thật giữa hai request đồng thời, thay vì
        #: trông chờ vào may rủi lịch chạy luồng của hệ điều hành.
        self.before_check: dict[str, Callable[[], None]] = {}

    def put_raw(self, key: str, data: bytes) -> None:
        """Ghi thẳng, bỏ qua mọi logic của r2_store — dùng để dựng sẵn dữ
        liệu hỏng/không hợp lệ cho test (vd JSON corrupt)."""
        self.objects[key] = data

    def _maybe_fail(self, method: str) -> None:
        trigger = self.fail.get(method)
        if trigger is None:
            return
        raise trigger() if callable(trigger) else trigger

    def _checkpoint(self, method: str) -> None:
        hook = self.before_check.get(method)
        if hook is not None:
            hook()

    def head_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        self.calls.append(("head_object", Key))
        self._maybe_fail("head_object")
        self._checkpoint("head_object")
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
        IfNoneMatch: Optional[str] = None,
    ) -> dict[str, Any]:
        self.calls.append(("put_object", Key))
        self._maybe_fail("put_object")
        self._checkpoint("put_object")
        if IfNoneMatch == "*":
            # Nguyên tử thật: kiểm tra rồi ghi trong CÙNG một khoá, đúng
            # ngữ nghĩa một request PUT có điều kiện phía R2/S3 — hai luồng
            # cùng lọt qua `_checkpoint` rồi mới tới đây vẫn chỉ có một
            # luồng thắng.
            with self._conditional_write_lock:
                if Key in self.objects:
                    raise FakeClientError(
                        "PreconditionFailed", "conditional PUT: key đã tồn tại")
                self.objects[Key] = bytes(Body)
            return {}
        self.objects[Key] = bytes(Body)
        return {}

    def list_objects_v2(
        self, *, Bucket: str, Prefix: str = "", MaxKeys: int = 1000,
        ContinuationToken: Optional[str] = None,
    ) -> dict[str, Any]:
        self.calls.append(("list_objects_v2", Prefix))
        self._maybe_fail("list_objects_v2")
        matching = sorted(key for key in self.objects if key.startswith(Prefix))
        start = int(ContinuationToken) if ContinuationToken else 0
        page = matching[start:start + MaxKeys]
        result: dict[str, Any] = {"Contents": [{"Key": key} for key in page]}
        next_start = start + len(page)
        if next_start < len(matching):
            result["NextContinuationToken"] = str(next_start)
        return result
