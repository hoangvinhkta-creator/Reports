"""Exception dùng chung cho lớp lưu trữ R2 (S071B).

Tách riêng khỏi ``tools.storage.r2_store`` (nơi import ``boto3``) để các
module dưới ``app/`` — nơi ``boto3``/``requests``/``socket``... bị cấm import
trực tiếp (xem ``tests/test_tracking_contract_client.py::
test_no_module_under_app_reaches_the_network``, ``ADR-101``) — vẫn bắt được
đúng các type lỗi này mà không phải kéo theo ``boto3``.
"""

from __future__ import annotations


class StorageUnavailableError(Exception):
    """R2 không truy cập được (network/timeout/auth/...) — KHÔNG được hiểu
    nhầm thành "lịch sử rỗng" hay "run không tồn tại"."""


class RunAlreadyExistsError(Exception):
    """``run_id`` đã tồn tại trong lưu trữ — lỗi lập trình (server luôn sinh
    run_id mới), không phải một tình huống vận hành bình thường."""


class CorruptRunRecordError(Exception):
    """Object run tồn tại nhưng JSON không parse được — khác với "không tồn
    tại" (``None``); caller không được coi đây là run vắng mặt."""
