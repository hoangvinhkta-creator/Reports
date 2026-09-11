"""`STAB-01` — đo thời gian và truy vết MỘT request, từ browser tới log.

Vì sao module này tồn tại: hiện tượng người dùng báo ("mở lần đầu gần một
phút", "mở/sửa đơn khoảng 5 giây") KHÔNG chỉ ra thành phần nào chậm. Không
có phép đo tách theo thành phần, mọi lần tối ưu là một lần đoán — và một
lần đoán sai vẫn tốn đúng số ngày làm việc như một lần đoán đúng.

Bốn thứ module này cung cấp, và không thứ nào trong đó tính lại một con số
nghiệp vụ nào:

1. `trace_id` — MỘT mã cho mỗi request, DO SERVER SINH, có mặt cả trong
   header trả về (`X-Request-Id`) và trong dòng log. Đây là sợi dây duy
   nhất nối một lần bấm trên browser với một dòng trong log máy chủ.
   `P1-2` — mã client gửi KHÔNG được dùng làm mã này; nó được lọc và giữ
   riêng ở `client_ref`. Xem `REQUEST_ID_HEADER`.
2. Các `span` theo tên (`sql`, `r2`, `tracking`, `presentation`,
   `template`) — cộng dồn theo request, không phải theo tiến trình.
3. `Server-Timing` — cùng những con số đó, ở dạng browser DevTools đọc
   được trực tiếp trong tab Network, không cần vào log máy chủ.
4. `process_age_seconds` — tuổi của TIẾN TRÌNH đang phục vụ. Đây là cách
   phân biệt COLD OPEN với WARM REQUEST mà không cần quyền vào dashboard:
   một request đến với `process_age_seconds` gần 0 là request đầu tiên sau
   một lần khởi động (spin-down của gói Free, restart, hoặc deploy), và
   thời gian của nó không so sánh được với một request lúc máy đã nóng.

## Ranh giới

Module này chỉ ĐO. Nó không cache, không đổi thứ tự thực thi, không bỏ bớt
một lượt gọi nào. Nếu tắt hẳn nó đi, mọi con số nghiệp vụ ra y nguyên —
đó là điều kiện để nó được phép nằm trên đường đi của mọi request.

`SQL` được đếm bằng event listener của SQLAlchemy trên đúng `Engine` mà
`create_app` đã dựng, nên nó đếm câu THẬT đã gửi tới database, không đếm
số lần một hàm Python được gọi.
"""

from __future__ import annotations

import os
import re
import time
import uuid
from contextlib import contextmanager
from typing import Optional

from flask import g, request

#: Thời điểm module được nạp — xấp xỉ thời điểm tiến trình bắt đầu phục vụ.
#: Đọc ở đây chứ không ở `create_app()`: gunicorn fork worker sau khi import,
#: và cái ta muốn biết là "tiến trình này đã sống bao lâu".
PROCESS_STARTED_AT = time.monotonic()

#: Tên các span được nhận. Danh sách ĐÓNG, để một lần gõ sai tên không âm
#: thầm tạo ra một cột mới mà không ai đọc.
SPANS = ("sql", "r2", "tracking", "presentation", "template")

#: Header mang mã truy vết.
#:
#: `P1-2 REPAIR` — bản trước TIN TRỰC TIẾP giá trị client gửi, và review
#: chứng minh hai hậu quả bằng probe:
#:
#:     gửi  `X-Request-Id: aaa status=200 total_ms=0.0 slow=0 attacker=1`
#:     log  `reports.timing rid=aaa status=200 … attacker=1 method=GET …`
#:
#: Client bơm được `key=value` giả vào đúng định dạng grep, ĐỨNG TRƯỚC
#: trường thật cùng tên — mọi parser lấy match đầu tiên đọc số của kẻ gửi.
#: Và hai request khác nhau gửi cùng một chuỗi thì log không phân biệt
#: được chúng.
#:
#: Nay `trace_id` LUÔN do server sinh và luôn có một thành phần server ở
#: cuối, nên hai request không bao giờ dùng chung mã. Phần client gửi được
#: giữ lại như một GỢI Ý đã lọc (`client_ref`), ở một trường riêng, để hai
#: đầu vẫn nối được với nhau khi cần.
REQUEST_ID_HEADER = "X-Request-Id"

#: Ký tự được phép trong `client_ref`. Cố tình HẸP: không khoảng trắng,
#: không `=`, không xuống dòng — tức không ký tự nào của định dạng log.
_CLIENT_REF_ALLOWED = re.compile(r"[^A-Za-z0-9._-]")

#: `client_ref` bị cắt ở đây. Một gợi ý dài hơn không nói thêm gì, và một
#: gợi ý rất dài là cách làm phình mọi dòng log.
MAX_CLIENT_REF = 64

#: Ký tự KHÔNG được đi nguyên vào dòng log — xem `_log_value`. Tập an
#: toàn hẹp có chủ đích: `/`, `.`, `-`, `_`, `:`, `@` đủ cho đường dẫn và
#: mã, và không ký tự nào trong đó phá được cặp `key=value`. `=`, khoảng
#: trắng, xuống dòng và dấu nháy đều KHÔNG an toàn.
_LOG_UNSAFE = re.compile(r"[^A-Za-z0-9._:/@-]")

#: Một request chậm hơn ngưỡng này (giây) được log ở mức đáng chú ý. Không
#: phải một SLA — chỉ là ngưỡng để dòng log không trôi mất giữa các dòng
#: bình thường.
SLOW_REQUEST_SECONDS = 1.0


def _state() -> dict:
    """Ô đo của request đang chạy, tạo khi cần.

    Nằm trên `flask.g` nên nó CHẾT cùng request: hai request đồng thời
    (hai worker thread) không cộng số của nhau, và không có trạng thái nào
    sống sót sang request sau.
    """
    state = getattr(g, "_timing", None)
    if state is None:
        state = {
            # `trace_id` do SERVER sinh, luôn luôn. Xem
            # `REQUEST_ID_HEADER` về việc vì sao không nhận từ client.
            "trace_id": uuid.uuid4().hex,
            "client_ref": _clean_client_ref(
                request.headers.get(REQUEST_ID_HEADER)),
            "started": time.monotonic(),
            "spans": {name: 0.0 for name in SPANS},
            "counts": {name: 0 for name in SPANS},
        }
        g._timing = state
    return state


def _clean_client_ref(raw: Optional[str]) -> Optional[str]:
    """Gợi ý truy vết của client, đã LỌC. `None` khi không có gì dùng được.

    Ký tự lạ bị THAY bằng `.` chứ không bị xoá: xoá sẽ làm hai chuỗi khác
    nhau (`a b` và `ab`) thành một, và khi đó việc lọc lại tạo ra đúng cái
    va chạm mà nó định ngăn.
    """
    text = (raw or "").strip()
    if not text:
        return None
    return _CLIENT_REF_ALLOWED.sub(".", text)[:MAX_CLIENT_REF]


def trace_id() -> str:
    """Mã truy vết của request đang chạy, do SERVER sinh.

    `P1-4` — đây là một trong BA loại mã, và chúng không được lẫn nhau:

        `trace_id`         một REQUEST. Đổi ở mỗi lần thử lại.
        `idempotency_key`  một LẦN GỬI của client (`mutation_guard`). Giữ
                           nguyên qua các lần thử lại — đó là điểm của nó.
        `audit_id`         một LẦN GHI nghiệp vụ, do server sinh.

    Bản trước gọi cả `trace_id` và `idempotency_key` là `request_id` ở hai
    nhánh khác nhau của cùng một response, nên client không đọc được trường
    đó mà không biết nhánh nào đã chạy.
    """
    try:
        return _state()["trace_id"]
    except RuntimeError:  # ngoài request context (CLI, test đơn vị)
        return "-"


def client_ref() -> Optional[str]:
    """Gợi ý truy vết client gửi, đã lọc. `None` khi không có."""
    try:
        return _state()["client_ref"]
    except RuntimeError:
        return None


def add(name: str, seconds: float, *, count: int = 1) -> None:
    """Cộng `seconds` vào span `name`. Tên lạ bị BỎ QUA, không ném lỗi.

    Bỏ qua thay vì ném: một lần gõ sai tên span trong code đo lường không
    được phép làm sập một request nghiệp vụ.
    """
    if name not in SPANS:
        return
    try:
        state = _state()
    except RuntimeError:
        return
    state["spans"][name] += float(seconds)
    state["counts"][name] += int(count)


@contextmanager
def span(name: str):
    """Đo một đoạn code và cộng vào span `name`.

        with request_timing.span("tracking"):
            catalog = live_pull.pull(...)

    Ngoại lệ trong thân `with` VẪN được cộng thời gian rồi ném tiếp: một
    lượt gọi thất bại sau 30 giây là đúng thứ ta cần thấy trong log, và bỏ
    nó đi sẽ làm một request chậm trông như một request nhanh.
    """
    started = time.monotonic()
    try:
        yield
    finally:
        add(name, time.monotonic() - started)


def snapshot(*, response_bytes: Optional[int] = None) -> dict:
    """Bản đọc số của request đang chạy, đơn vị GIÂY (float).

    `process_age_seconds` là tuổi tiến trình, không phải tuổi request — xem
    docstring của module về việc phân biệt cold/warm.
    """
    try:
        state = _state()
    except RuntimeError:
        return {}
    now = time.monotonic()
    return {
        "trace_id": state["trace_id"],
        "client_ref": state["client_ref"],
        "total": now - state["started"],
        "process_age_seconds": now - PROCESS_STARTED_AT,
        "pid": os.getpid(),
        "spans": dict(state["spans"]),
        "counts": dict(state["counts"]),
        "response_bytes": response_bytes,
    }


def server_timing_header(data: dict) -> str:
    """`Server-Timing` từ một `snapshot()`.

    Đơn vị của đặc tả là MILLIGIÂY. Các span có giá trị 0 vẫn được ghi ra:
    một cột trống nói "đã đo, không mất thời gian", còn một cột VẮNG MẶT
    không phân biệt được với "chưa đo bao giờ".
    """
    parts = [f'total;dur={data.get("total", 0.0) * 1000:.1f}']
    for name in SPANS:
        seconds = data.get("spans", {}).get(name, 0.0)
        count = data.get("counts", {}).get(name, 0)
        parts.append(f"{name};desc=\"n={count}\";dur={seconds * 1000:.1f}")
    age = data.get("process_age_seconds")
    if age is not None:
        parts.append(f"procage;dur={age * 1000:.1f}")
    return ", ".join(parts)


def _log_value(value) -> str:
    """Một giá trị an toàn cho dòng log `key=value`.

    `P1-2 REPAIR` — mọi giá trị đi vào dòng log qua đây, không có ngoại lệ.
    Ba nguồn có thể mang ký tự của kẻ gửi: `client_ref` (header), `path`
    (URL, đã được Flask giải mã nên `%20` thành khoảng trắng THẬT) và
    `method`. Trước bản sửa, `path` đi thẳng vào dòng log.

    ## Vì sao LỌC chứ không BỌC NHÁY

    Bọc nháy (logfmt) là cách thường dùng và nó ĐÚNG — với điều kiện mọi
    thứ đọc log đều hiểu nháy. Nhưng dòng log này được thiết kế để `grep`
    và `awk` đọc, và một câu `awk` tách theo khoảng trắng vẫn thấy
    `status=500` bên trong `path="/api/x y status=500"`. Một cửa an toàn
    phụ thuộc vào việc người đọc dùng đúng parser thì không phải một cửa.

    Nên giá trị được LỌC: ký tự an toàn đi nguyên, mọi ký tự khác thành
    `.`. Sau bước này KHÔNG dòng log nào có thể chứa một cặp `key=value`
    do kẻ gửi đặt, với BẤT KỲ parser nào.

    Cái mất đi: một `path` chứa ký tự lạ đọc ra không chính xác từng ký
    tự. Đánh đổi đó là đúng — `path` trong log để nhận ra ROUTE, còn
    `trace_id` mới là thứ nối một dòng log với một request cụ thể.

    Hậu tố `~` được thêm khi có ký tự bị thay, để người đọc log biết chuỗi
    đã bị lọc thay vì tưởng đó là giá trị gốc.
    """
    text = "-" if value is None else str(value)
    if not text:
        return "-"
    cleaned = _LOG_UNSAFE.sub(".", text)
    return cleaned if cleaned == text else cleaned + "~"


def log_line(data: dict, *, method: str, path: str, status: int) -> str:
    """Một dòng log, một request. Định dạng `key=value` để grep được.

    `trace_id` do server sinh nên nó luôn an toàn; `client_ref` và `path`
    đi qua `_log_value` vì chúng mang ký tự của kẻ gửi. Xem `_log_value`.
    """
    spans = data.get("spans", {})
    counts = data.get("counts", {})
    fields = [
        f'trace={_log_value(data.get("trace_id", "-"))}',
        f'client_ref={_log_value(data.get("client_ref"))}',
        f"method={_log_value(method)}",
        f"path={_log_value(path)}",
        f"status={status}",
        f'total_ms={data.get("total", 0.0) * 1000:.1f}',
        f'bytes={data.get("response_bytes") if data.get("response_bytes") is not None else "-"}',
        f'procage_s={data.get("process_age_seconds", 0.0):.1f}',
        f'pid={data.get("pid", "-")}',
    ]
    for name in SPANS:
        fields.append(f"{name}_ms={spans.get(name, 0.0) * 1000:.1f}")
        fields.append(f"{name}_n={counts.get(name, 0)}")
    return "reports.timing " + " ".join(fields)


def install_sql_counter(engine) -> None:
    """Đếm + đo MỌI câu SQL của `engine` vào span `sql`.

    Gắn ở tầng `Engine` chứ không ở từng hàm truy vấn: đó là cách duy nhất
    để con số này không phụ thuộc việc ai nhớ bọc câu truy vấn của mình.
    Gọi hai lần trên cùng engine là vô hại (cờ trên chính engine).
    """
    if engine is None or getattr(engine, "_reports_timing_installed", False):
        return
    try:
        from sqlalchemy import event
    except Exception:  # noqa: BLE001 — không có SQLAlchemy ⟹ không đo SQL
        return

    @event.listens_for(engine, "before_cursor_execute")
    def _before(conn, cursor, statement, parameters, context, executemany):
        conn.info["_reports_sql_started"] = time.monotonic()

    @event.listens_for(engine, "after_cursor_execute")
    def _after(conn, cursor, statement, parameters, context, executemany):
        started = conn.info.pop("_reports_sql_started", None)
        if started is not None:
            add("sql", time.monotonic() - started)

    try:
        engine._reports_timing_installed = True
    except Exception:  # noqa: BLE001 — engine không cho gắn thuộc tính
        pass
