"""Máy trạng thái reconcile — hàm THUẦN, không DB, không thời gian, không I/O.

Vào: các dòng nguồn của snapshot mới + hiện trạng theo khoá đã lưu.
Ra:  một quyết định cho MỖI khoá của snapshot mới.

Tách thuần như vậy vì đây là nơi một lỗi sẽ gây hậu quả kế toán thật (đếm hai
lần một dòng bán → doanh thu/KPI/lương sai), nên nó phải kiểm được bằng bảng
đầu vào/đầu ra chứ không phải bằng cách dựng database rồi đoán.

Slice A (TASK-PRA-002 mục 20) hiện thực bước 0–3 và 5 của mục 8:
INSERT / SAME / SOURCE_CHANGED / ORDER_KEY_COLLISION.

Slice B thêm ``absent_keys`` — hàm dùng chung cho bước 4
(``NOT_SEEN_IN_LATEST_SNAPSHOT``) và bước R (``REMOVED_IN_SOURCE_CANDIDATE``).
Hai bước đó là CÙNG một phép toán tập hợp ("khoá hiện hành nào không có trong
snapshot này, trong phạm vi nào"); thứ DUY NHẤT khác nhau là phạm vi ngày và
thẩm quyền của phạm vi đó:

    bước 4  phạm vi = khoảng ĐO ĐƯỢC của snapshot   → chỉ thông tin
    bước R  phạm vi = khoảng ĐƯỢC XÁC NHẬN tường minh → ứng viên Review

Viết một hàm cho cả hai là cố ý: nếu tách đôi, hai bản sao có thể trôi khỏi
nhau và bước R — bước duy nhất có hệ quả nghiệp vụ — sẽ là bản không được
kiểm kỹ. Hàm này KHÔNG BAO GIỜ tự quyết phạm vi: phạm vi là tham số, và
thẩm quyền của nó do caller mang tới.
"""

from __future__ import annotations

from datetime import date
from typing import Iterable, Mapping, Optional, Sequence

from app.history.keys import changed_fields
from app.history.models import (
    COLLISION_DAY_THRESHOLD, CurrentKey, CurrentState, Decision, LineKey,
    OUTCOME_COLLISION, OUTCOME_INSERT, OUTCOME_SAME, OUTCOME_SOURCE_CHANGED,
    ReconcileResult, SourceLine,
)


def reconcile(
    lines: Sequence[SourceLine],
    current: Mapping[LineKey, CurrentState],
) -> ReconcileResult:
    """Quyết định cho từng khoá của snapshot mới, theo đúng bảng contract 3.2."""
    return ReconcileResult(tuple(_decide(line, current.get(line.key)) for line in lines))


def _decide(line: SourceLine, state: CurrentState | None) -> Decision:
    if state is None:
        # Khoá chưa từng thấy: source version 1, current trỏ tới nó.
        return Decision(line=line, outcome=OUTCOME_INSERT, version_no=1,
                        creates_version=True, becomes_current=True)

    gap = _day_gap(line, state)
    if gap is not None and gap > COLLISION_DAY_THRESHOLD:
        # Cùng Số BH nhưng ngày bán cách nhau quá xa: hệ thống KHÔNG có thẩm
        # quyền khẳng định đây là cùng một đơn (BH có reset theo năm hay không
        # vẫn là UNKNOWN — D2). Ghi lại đầy đủ, dựng cờ, và KHÔNG đụng vào
        # hiện trạng: không SAME, không CHANGED, không merge, không mất bản ghi.
        return Decision(
            line=line, outcome=OUTCOME_COLLISION, version_no=state.next_version_no,
            creates_version=True, becomes_current=False,
            previous_version_id=state.source_version_id,
            collision_detail={
                "current_sale_date": _iso(state.sale_date),
                "incoming_sale_date": _iso(line.sale_date),
                "day_gap": gap,
                "threshold_days": COLLISION_DAY_THRESHOLD,
            },
        )

    if line.fingerprint == state.fingerprint:
        # Cùng nội dung nghiệp vụ → KHÔNG version mới, KHÔNG double-count.
        # Việc dòng này xuất hiện lại vẫn được ghi (membership snapshot_line),
        # vì "snapshot nào có chứa dòng này" là một sự thật riêng.
        return Decision(line=line, outcome=OUTCOME_SAME, version_no=state.version_no,
                        creates_version=False, becomes_current=True,
                        previous_version_id=state.source_version_id)

    return Decision(
        line=line, outcome=OUTCOME_SOURCE_CHANGED, version_no=state.next_version_no,
        creates_version=True, becomes_current=True,
        previous_version_id=state.source_version_id,
        changed_fields=changed_fields(state.fingerprint_values, line.fingerprint_values),
    )


def _day_gap(line: SourceLine, state: CurrentState) -> int | None:
    if line.sale_date is None or state.sale_date is None:
        return None
    return abs((line.sale_date - state.sale_date).days)


def _iso(value) -> str | None:
    return None if value is None else value.isoformat()


def absent_keys(
    *,
    present: Iterable[LineKey],
    candidates: Iterable[CurrentKey],
    start: Optional[date],
    end: Optional[date],
) -> tuple[LineKey, ...]:
    """Khoá hiện hành nằm TRONG ``[start, end]`` mà snapshot mới KHÔNG chứa.

    Bốn điều kiện loại trừ, mỗi điều kiện là một cách hệ thống có thể tạo ra
    một sự vắng mặt GIẢ nếu quên:

    1. Khoá có trong snapshot mới → không vắng mặt (kể cả khi nội dung đổi).
    2. ``sale_date`` là ``None`` → không biết dòng đó thuộc kỳ nào, nên KHÔNG
       có snapshot nào có thẩm quyền nói nó biến mất.
    3. Ngày nằm NGOÀI ``[start, end]`` → snapshot không đại diện cho kỳ đó.
       Đây là ranh giới quan trọng nhất của slice B: một sổ 01–10/09 không
       nói được gì về đơn ngày 20/09, dù người dùng có xác nhận nó đầy đủ
       cho 01–10/09 hay không.
    4. Khoá đang có tranh chấp danh tính (``ORDER_KEY_COLLISION``) → hệ thống
       chưa biết nó là đơn nào, nên càng không được kết luận nó vắng mặt.

    Phạm vi mở (``start``/``end`` là ``None``) trả về rỗng: không có phạm vi
    thì không có thẩm quyền, không phải "vắng mặt tất cả".
    """
    if start is None or end is None:
        return ()
    seen = set(present)
    return tuple(
        candidate.key
        for candidate in candidates
        if candidate.key not in seen
        and candidate.sale_date is not None
        and start <= candidate.sale_date <= end
        and not candidate.order_key_collision
    )
