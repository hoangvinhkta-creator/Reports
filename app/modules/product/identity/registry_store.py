"""Loader read-only cho `HistoricalConfirmedRegistry` (E-J) từ JSONL.

## Phạm vi cố ý hẹp hơn `store.py` (E-F)

`JsonlProductIdentityStore` (E-F, `store.py`) là một store ghi được, nhiều
tiến trình, với khoá file thật (`B-01`, Independent Review #1/#2). Module
này KHÔNG làm lại việc đó cho E-J: `HistoricalConfirmedRegistry` production
vẫn thuần bộ nhớ (S051 §9), và loader ở đây chỉ có một việc — đọc một file
JSONL các entry đã Owner-confirmed thật (`INV-54`: "nhập từ báo cáo
Owner-confirmed thật, hoặc để trống") và replay chúng vào một registry mới,
MỘT LẦN, lúc khởi động một lần gọi `run_import()`. Không có correction
workflow, không có concurrent writer nào cần khoá ở đây — khi entry cần
persist/correct thật (ghi, không chỉ đọc), đó là phạm vi của một
DATA/PERSISTENCE SESSION khác (S051 §9, S052 §5), không phải module này.

## Vì sao không hard-code path

`run_import()`/`build_working_data()` (S051) nhận `identity_registry` qua
dependency injection, mặc định registry rỗng — không đổi. Loader này là một
tiện ích CHO CALLER dùng khi muốn nạp entry thật (`app/pipeline.py` không tự
gọi nó) — tránh side-effect âm thầm đổi hành vi mặc định của mọi lời gọi
`run_import()` hiện có (bao gồm Golden Baseline `tests/test_golden_baseline.py`,
vốn không truyền `identity_registry` và phải giữ nguyên hành vi rỗng).
"""

from __future__ import annotations

import json
from pathlib import Path

from app.modules.product.identity.commands import ConfirmHistoricalEntry
from app.modules.product.identity.registry import (
    HistoricalConfirmedRegistry,
    entry_from_record,
)


class InvalidRegistrySeedRecordError(ValueError):
    """Một dòng JSONL không parse được thành entry hợp lệ (§9.2 data contract)."""


def load_registry_from_jsonl(path: Path) -> HistoricalConfirmedRegistry:
    """Đọc một file JSONL các `HistoricalConfirmedRegistryEntry` (record §9.2,
    một entry mỗi dòng, JSON) và replay chúng vào một registry mới bằng
    ĐÚNG đường ghi production duy nhất (`registry.append`, `INV-66`).

    File không tồn tại → registry rỗng (giống hành vi mặc định hiện có,
    không phải lỗi — một Golden/tenant chưa có entry nào là trạng thái hợp
    lệ, `INV-54`).
    """
    registry = HistoricalConfirmedRegistry()
    if not path.exists():
        return registry

    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise InvalidRegistrySeedRecordError(
                    f"{path}:{line_no} không phải JSON hợp lệ: {exc}"
                ) from exc
            entry = entry_from_record(record)
            if entry is None:
                raise InvalidRegistrySeedRecordError(
                    f"{path}:{line_no} thiếu entry_id hoặc record rỗng"
                )
            registry.append(
                ConfirmHistoricalEntry(
                    actor_id=entry.confirmed_by,
                    client_request_id=f"bootstrap:{path.name}:{line_no}",
                    expected_version=0,
                    entry_id=entry.entry_id,
                    entry=entry,
                    reason="bootstrap load từ registry seed JSONL",
                )
            )
    return registry
