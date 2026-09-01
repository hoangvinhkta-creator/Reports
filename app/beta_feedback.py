"""Feedback Owner cục bộ — S069.

Feedback là PRIVATE LOCAL DATA: không gửi Internet, không cloud analytics.
Comment là free text Owner tự nhập; module này không tự động gắn thêm bất kỳ
dữ liệu nghiệp vụ nào (khách hàng, workbook, giá, payload Tracking).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
FEEDBACK_LOG_PATH = REPO_ROOT / "data" / "beta_feedback" / "feedback.jsonl"

FEEDBACK_CATEGORIES = (
    "Kết quả có vẻ không đúng",
    "Không hiểu lý do cần xem lại",
    "Thao tác bất tiện",
    "Thiếu mã / giá / dữ liệu",
    "Khác",
)


class InvalidFeedbackError(ValueError):
    """Category ngoài danh sách cố định — fail-safe, không âm thầm nhận."""


@dataclass(frozen=True)
class FeedbackRecord:
    feedback_id: str
    timestamp: str
    run_id: Optional[str]
    category: str
    comment: str


def build_feedback_record(
    *,
    category: str,
    comment: str = "",
    run_id: Optional[str] = None,
    now: Optional[datetime] = None,
) -> FeedbackRecord:
    if category not in FEEDBACK_CATEGORIES:
        raise InvalidFeedbackError(
            f"Category phản hồi không hợp lệ: {category!r}. "
            f"Chỉ chấp nhận: {', '.join(FEEDBACK_CATEGORIES)}."
        )
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return FeedbackRecord(
        feedback_id=uuid.uuid4().hex,
        timestamp=moment.isoformat(timespec="seconds"),
        run_id=run_id,
        category=category,
        comment=comment.strip(),
    )


def save_feedback(
    record: FeedbackRecord, *, log_path: Path = FEEDBACK_LOG_PATH,
) -> Path:
    """Append một dòng JSON; không đọc, không viết lại các dòng cũ."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(record), ensure_ascii=False))
        handle.write("\n")
    return log_path
