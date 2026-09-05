"""Nơi lưu BỀN của log quyết định Product Identity — sửa `F-B` (và nửa còn
lại của `F-A`).

## Vấn đề đúng như nó xảy ra trên production

Bản Web chạy `gunicorn --workers 2` trong một container KHÔNG có persistent
disk (`Dockerfile:75`, `render.yaml` § "KHÔNG có `disk:`"). Log quyết định
Product Identity của Phase 1 lại nằm ở `data/product_identity/mappings.jsonl`
— tức trên chính filesystem ephemeral đó. Hệ quả:

    một lần redeploy  ⟹ mọi mặt hàng Owner đã phân loại quay lại
                        "Chưa phân loại"
    hai worker        ⟹ khoá `flock` chỉ loại trừ trong CÙNG container, và
                        mỗi worker vẫn giữ ảnh chụp riêng của mình

## Vì sao là R2 chứ không phải một bảng mới

Thứ tự ưu tiên đã đi hết, theo đúng thứ tự:

1. **Một đường GHI của Tracking.** Không tồn tại trong repo này. Data
   Contract V1 mà Reports nói chuyện là READ-ONLY theo thiết kế —
   `tools/tracking/capture_purchase_price_history.py` nói thẳng: "Không
   `PUT`, không `PATCH`, không `POST`, không `DELETE`". `inv.map` là bảng do
   người của Tracking duyệt (`tracking_inv_map.py` § Owner decision), và
   Reports không có, và KHÔNG ĐƯỢC có, một đường ghi vào đó.

2. **Một nơi lưu bền DÙNG CHUNG đã được chấp nhận.** Có: Cloudflare R2
   (`S071B`) — đúng nơi mà bản Web đã lưu run/artifact, đã fail-closed bằng
   `REPORTS_REQUIRE_R2`, đã có adapter ngoài `app/` theo `ADR-101`. Không
   migration, không schema mới, không bảng identity thứ hai.

Đây là bước 2 và nó dừng ở bước 2. Không có gì được phát minh thêm.

## Vì sao ĐỔI CHỖ LƯU không tạo ra một thẩm quyền thứ hai

`PHB-01` chốt Tracking là thẩm quyền Product Identity. Cái được lưu ở đây
KHÔNG phải `inv.map` và không phải một bảng ánh xạ song song: nó là log
append-only của những `confirmation_action` mà một NGƯỜI phía Reports đã ra
(`mapping_source = HUMAN_CONFIRMATION`, `source_system = REPORTS_SALES`) —
đúng log mà CLI `app/modules/product/identity/cli.py` và màn hình cùng ghi
qua đúng một `store.append()`, và nó đã tồn tại trước bản sửa này. Bản sửa
này chỉ trả lời câu hỏi "các byte đó nằm ở đâu". Một bản ghi không đổi bản
chất vì đổi chỗ nằm.

## Object model

    product-identity/events/000000000001.json
    product-identity/events/000000000002.json
    ...

Số thứ tự đệm 0 tới 12 chữ số ⟹ sắp theo TÊN khoá trùng với sắp theo thời
gian, nên `pull()` chỉ cần MỘT lần liệt kê (không fetch body) để biết có gì
mới, và không cần một index dùng chung nào — một index như thế sẽ là đúng
điểm tranh chấp mà `r2_store` đã tránh cho `runs/`.

## Loại trừ giữa nhiều người viết, khi không có khoá file chung

Nhiều container ⟹ `flock` vô nghĩa. Chỗ hai người viết gặp nhau là phép
GHI-NẾU-VẮNG tại đúng một khoá: cả hai cùng tính vị trí kế tiếp là `N+1`,
một người ghi được, người kia nhận `RunAlreadyExistsError` và bị dịch thành
`JournalWriteConflict`. Store hoàn lại state trong bộ nhớ rồi ném tiếp — tức
đúng `INV-59`/`INV-60` (nạp lại và reconcile), chỉ phát hiện ở tầng lưu trữ.

`put_json_if_absent` dùng HEAD-rồi-PUT, nên vẫn còn một khe race lý thuyết
hẹp giữa hai lần ghi ĐỒNG THỜI tuyệt đối vào cùng một khoá. Đây là hạn chế
đã biết và được nói ra, không phải một điều được giả vờ là đã giải quyết: nó
hẹp hơn hẳn khe race hiện tại (hai worker ghi hai file khác nhau và mất trắng
một bên sau redeploy), và thu hẹp nốt nó cần một phép ghi có điều kiện
(`If-None-Match`) — một thay đổi ở tầng adapter R2, ngoài phạm vi bản sửa
chặn này.
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from typing import Any, Iterator, Optional

from app.modules.product.identity.journal import JournalWriteConflict
from app.modules.product.identity.mapping import MappingIntegrityError
from tools.storage import r2_store
from tools.storage.errors import RunAlreadyExistsError

#: Prefix của log quyết định trong bucket. Tách hẳn khỏi `runs/`/`artifacts/`
#: — ba object model khác nhau, ba vòng đời khác nhau.
EVENT_KEY_PREFIX = "product-identity/events/"

#: Số chữ số của số thứ tự trong tên khoá. Đủ cho mọi quy mô mà bản Web này
#: sẽ gặp, và cố định — đổi nó sẽ làm thứ tự sắp xếp của log cũ và log mới
#: khác nhau, tức làm hỏng chính bất biến mà tên khoá tồn tại để giữ.
_SEQUENCE_DIGITS = 12


def event_key(sequence: int) -> str:
    return f"{EVENT_KEY_PREFIX}{sequence:0{_SEQUENCE_DIGITS}d}.json"


class ObjectStoreIdentityJournal:
    """`IdentityJournal` trên object store dùng chung (`§ Object model`).

    `client`/`env` cho phép test tiêm một fake S3-compatible client — cùng
    khuôn mà `app/web/storage_backend.py` đã dùng.
    """

    def __init__(self, *, client=None, env: Optional[dict[str, str]] = None) -> None:
        self._client = client
        self._env = env
        #: Số bản ghi đã đưa cho người gọi. Cũng chính là số thứ tự của bản
        #: ghi cuối cùng đã biết — hai con số đó bằng nhau vì log không có lỗ
        #: hổng (xem `pull()`).
        self._count = 0

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Không có khoá giữ suốt giao dịch — xem `§ Loại trừ` ở đầu file.

        Cố ý KHÔNG dựng một khoá giả (một object `.lock` tự đặt/tự xoá): một
        khoá không có thời hạn sống trên object store sẽ kẹt vĩnh viễn khi
        một container chết giữa chừng, và đó là một chế độ hỏng tệ hơn hẳn
        chế độ hỏng mà nó định chặn.
        """
        yield

    def pull(self) -> list[dict[str, Any]]:
        """Các bản ghi có thêm kể từ lần `pull()` trước, đúng thứ tự.

        Một lần liệt kê (không body) cho trường hợp thường gặp nhất — không
        có gì mới — rồi chỉ fetch đúng phần đuôi chưa biết.

        Log phải LIỀN MẠCH. Một lỗ hổng số thứ tự nghĩa là một event đã từng
        tồn tại rồi biến mất, và `INV-63` (log thắng) không cho phép đọc phần
        còn lại thành một state một nửa — nó là lỗi, không phải một dữ liệu
        thiếu có thể bỏ qua.
        """
        keys = r2_store.list_keys(
            EVENT_KEY_PREFIX, client=self._client, env=self._env)
        if len(keys) <= self._count:
            return []
        expected = [event_key(index) for index in range(1, len(keys) + 1)]
        if keys != expected:
            raise MappingIntegrityError(
                f"{EVENT_KEY_PREFIX}: chuỗi event có lỗ hổng số thứ tự — log "
                "KHÔNG liền mạch, không được đọc tiếp thành một state một nửa "
                "(INV-63/INV-67)"
            )
        records = []
        for key in keys[self._count:]:
            payload = r2_store.get_json(key, client=self._client, env=self._env)
            if payload is None:
                raise MappingIntegrityError(
                    f"{key}: vừa liệt kê được nhưng đọc lại không thấy — log "
                    "không ổn định, KHÔNG được đọc tiếp"
                )
            records.append(payload)
        self._count = len(keys)
        return records

    def append(self, record: dict[str, Any]) -> None:
        """Ghi bản ghi vào ĐÚNG vị trí kế tiếp, chỉ khi vị trí đó còn trống."""
        sequence = self._count + 1
        # Qua `json.loads(json.dumps(...))` cho đúng một lý do: bản ghi được
        # ghi ra JSON rồi đọc lại ở mọi worker khác, nên nếu nó chứa thứ
        # không round-trip được thì phải nổ NGAY tại đường ghi, chứ không
        # phải ở một worker khác vào một lúc khác.
        payload = json.loads(json.dumps(record, ensure_ascii=False, sort_keys=True))
        try:
            r2_store.put_json_if_absent(
                event_key(sequence), payload, client=self._client, env=self._env)
        except RunAlreadyExistsError as exc:
            raise JournalWriteConflict(
                f"vị trí {sequence} của log quyết định đã bị một người viết "
                "khác chiếm; nạp lại và thử lại (INV-59/INV-60)"
            ) from exc
        self._count = sequence


def build(env: Optional[dict[str, str]] = None):
    """Journal bền nếu R2 đã cấu hình, ngược lại `None`.

    `None` KHÔNG có nghĩa "không lưu": nó có nghĩa "người gọi dùng nhánh file
    cục bộ". Trên máy Owner nhánh đó đúng — đĩa thật, một tiến trình, bền qua
    khởi động lại. Chỉ trong container nó mới sai, và chính vì thế
    `identity_gateway.build_store()` từ chối nhánh đó khi
    `REPORTS_REQUIRE_R2` bật.
    """
    if not r2_store.is_configured(env):
        return None
    return ObjectStoreIdentityJournal(env=env)


def requires_durable_store(env: Optional[dict[str, str]] = None) -> bool:
    """Môi trường có tuyên bố "không được lưu trên đĩa ephemeral" không.

    Đọc ĐÚNG biến mà `storage_backend` đã đọc cho run/artifact: hai loại dữ
    liệu khác nhau nhưng cùng một câu hỏi vận hành — "container này có
    persistent disk không" — và hai biến riêng cho cùng một câu hỏi là hai
    cơ hội để chúng lệch nhau.
    """
    values = os.environ if env is None else env
    return (values.get("REPORTS_REQUIRE_R2") or "").strip().lower() in {
        "1", "true", "yes"}


__all__ = [
    "EVENT_KEY_PREFIX", "ObjectStoreIdentityJournal", "build", "event_key",
    "requires_durable_store",
]
