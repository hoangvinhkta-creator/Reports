"""F-R1 — sàn phụ thuộc ``boto3``/``botocore`` cho PUT có điều kiện.

``tools.storage.r2_store.put_json_if_absent`` gọi
``client.put_object(..., IfNoneMatch="*")`` (N-01) để việc kiểm-tra-rồi-ghi
xảy ra nguyên tử trong một request phía R2/S3. Một số bản ``botocore`` cũ
hơn sàn phụ thuộc cũ (``boto3>=1.34``) — cụ thể 1.34.x và cả 1.35.0/1.35.1 —
KHÔNG có tham số ``IfNoneMatch`` trong shape ``PutObject``: gọi với tham số
đó sẽ nhận ``ParamValidationError: Unknown parameter in input:
"IfNoneMatch"`` ngay ở lớp SDK, trước khi có request nào rời máy — nghĩa là
MỌI ghi có điều kiện fail closed. Test này verify trực tiếp qua service
model của botocore đang cài (không cần mạng/credential thật) rằng bản đang
cài THỰC SỰ hỗ trợ tham số này — nó phải fail dưới một botocore không có
tham số, để bắt sớm một môi trường cài đặt lỡ hạ sàn phụ thuộc.
"""

from __future__ import annotations

import pytest

botocore = pytest.importorskip("botocore")
import botocore.session  # noqa: E402


def test_installed_botocore_put_object_shape_supports_if_none_match():
    session = botocore.session.get_session()
    operation = session.get_service_model("s3").operation_model("PutObject")
    assert "IfNoneMatch" in operation.input_shape.members, (
        f"botocore {botocore.__version__} thiếu PutObject.IfNoneMatch — "
        "put_json_if_absent (PUT có điều kiện, N-01) sẽ fail với "
        "ParamValidationError trên mọi lần ghi. Nâng botocore/boto3 lên "
        ">=1.35.2 (sàn phụ thuộc tối thiểu đã verify có tham số này)."
    )
