"""Chụp giá MIN theo NGÀY BÁN của Tracking ra file — hợp đồng `daily-min-v1`.

## Vì sao công cụ này nằm ở `tools/`, không phải `app/modules/`

`ADR-101` + `DEC-152` §6: phần chạm mạng nằm NGOÀI `app/modules/`. Ranh giới
ấy được thi hành bằng một assertion import-graph (`CHECK-105D-17`) quét toàn bộ
`app/modules/**` tìm import mạng. Công cụ này là phía bên kia của ranh giới:
nó gọi hợp đồng READ-ONLY rồi ghi ra một file bất biến;
`app/modules/pricing/daily_min/capture_file.py` đọc file đó.

## Nguồn: `POST /api/min-ngay` — MỘT yêu cầu, nhiều mã, nhiều ngày

```text
POST <source_url>/api/min-ngay
Header: X-Report-Key: <secret>
Body:   {"product_codes": [...], "date_from": "...", "date_to": "...", "cursor": ...}
```

Cố ý KHÔNG gọi một lượt mạng cho mỗi dòng bán: một kỳ báo cáo có hàng nghìn
dòng, và một lượt gọi cho mỗi dòng vừa chậm vừa biến một sự cố mạng giữa chừng
thành một báo cáo thiếu vài dòng giá mà không ai để ý.

## Đọc HẾT các trang, hoặc FAILED

Hợp đồng có trần mã mỗi lượt và trả `next_cursor`. Công cụ này đi hết chuỗi
trang; dừng giữa chừng là đưa về một ảnh chụp thiếu mã, và một ảnh chụp thiếu
mã trông y hệt một ảnh chụp đầy đủ của những mã chưa từng có giá. Có trần số
trang (`TRAN_TRANG`) để một `next_cursor` lặp vô hạn phía máy chủ không biến
thành một vòng lặp không kết thúc ở đây.

Phong bì của mọi trang phải khớp nhau (`schema_version`, `currency_unit`,
`business_timezone`, `date_from`, `date_to`, `query_revision`). Lệch một trường
là hai trang đến từ hai trạng thái khác nhau, và nối chúng lại là dựng một ảnh
chụp chưa từng tồn tại ở bất kỳ thời điểm nào.

Năm trường đầu chỉ lặp lại yêu cầu vừa gửi đi, nên chúng khớp nhau kể cả khi dữ
liệu bên dưới đã đổi. `query_revision` là trường DUY NHẤT nói về trạng thái
database: Tracking đổi nó sau mọi lượt ghi vào nhánh MIN theo ngày, và đọc nó
TRƯỚC khi đọc dữ liệu, nên một lượt ghi xen giữa hai trang luôn làm hai trang
lệch. Con trỏ phân trang chỉ là vị trí trong danh sách mã; nó không đóng băng
gì cả.

## Chỉ ĐỌC

Không `PUT`, không `PATCH`, không `DELETE`. `POST` ở đây là một TRUY VẤN có
tham số (danh sách mã quá dài cho query string), không phải một lệnh ghi —
Tracking là read-only đối với Reports (`DEC-154` Preserves).

## Credential

Không hardcode, không nhúng, không đoán, không đặt trong query string.
`--source-url` là tham số bắt buộc; secret đọc từ biến môi trường
`TRACKING_REPORT_API_KEY` và đi ra ngoài DUY NHẤT ở header `X-Report-Key`. Nó
KHÔNG BAO GIỜ được ghi vào file capture, vào thông điệp lỗi hay ra log — file
capture đi vào repo, còn secret thì không.

## Capture hỏng ghi ra `capture_status = FAILED`, không ghi file rỗng

`INV-12`: một lần capture hỏng và một khoảng thời gian thật sự không có giá là
hai sự kiện khác nhau. Gộp lại thì một lần mất mạng trông y hệt một kết luận
về dữ liệu.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

from tools.tracking.capture_purchase_price_history import (
    API_KEY_ENV_VAR,
    API_KEY_HEADER,
    CLIENT_USER_AGENT,
    JSON_CONTENT_TYPE,
    MISSING_API_KEY,
    CaptureError,
    mo_ta_loi_http,
    write_capture,
)

CONTRACT_PATH = "/api/min-ngay"
SCHEMA_VERSION = "daily-min-v1"

TRAN_TRANG = 200
"""Trần số trang mỗi lần capture.

Không phải một con số tuỳ tiện: trần mã mỗi trang phía Tracking là 100, nên
200 trang = 20.000 mã, rộng hơn nhiều lần danh mục thật (~3.400). Nó tồn tại
để một `next_cursor` lặp phía máy chủ dừng thành một lỗi có tên, thay vì một
vòng lặp chạy tới khi hết bộ nhớ."""

#: Những trường của phong bì phải GIỐNG NHAU ở mọi trang — xem docstring.
#:
#: `query_revision` là trường quan trọng nhất trong danh sách này, và cũng là
#: trường duy nhất KHÔNG suy ra được từ yêu cầu. Năm trường kia chỉ lặp lại
#: những gì công cụ này vừa gửi đi, nên chúng khớp nhau kể cả khi dữ liệu phía
#: dưới đã đổi giữa hai trang. `query_revision` đổi sau MỌI lượt ghi vào các
#: nhánh MIN theo ngày — một lượt cron chụp thêm, một ngày chuyển sang FINAL,
#: một lệnh sửa bản ghi cũ. Không có nó thì hai trang của hai trạng thái khác
#: nhau ghép lại thành một ảnh chụp chưa từng tồn tại, và mọi trường phong bì
#: khác vẫn khớp nên không có gì đỏ lên.
TRUONG_PHONG_BI = (
    "schema_version",
    "currency_unit",
    "business_timezone",
    "date_from",
    "date_to",
    "query_revision",
)

Poster = Callable[[dict[str, Any]], Any]
"""`body -> JSON đã decode`. Được tiêm vào để test không cần mạng."""


def _http_poster(source_url: str, api_key: Optional[str]) -> Poster:
    """Client DUY NHẤT của hợp đồng `daily-min-v1` trong cả repo Reports."""
    base = source_url.rstrip("/")

    def post(body: dict[str, Any]) -> Any:
        # Kiểm tra ở TRONG hàm chứ không lúc dựng: `build_capture` bắt
        # `CaptureError` và ghi ra một artifact `FAILED` đọc lại được, thay vì
        # để CLI chết bằng traceback và không để lại bằng chứng nào.
        if not api_key:
            raise CaptureError(
                f"{MISSING_API_KEY}: thiếu biến môi trường {API_KEY_ENV_VAR} — "
                f"hợp đồng Tracking đòi header {API_KEY_HEADER}; không phát "
                "request không key."
            )
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        # `User-Agent`/`Accept` tường minh — cùng lý do `S065` đã ghi ở
        # `capture_purchase_price_history.py`: mặc định của `urllib` khớp chữ
        # ký bot mà WAF phía trước hợp đồng chặn.
        request = urllib.request.Request(
            base + CONTRACT_PATH,
            method="POST",
            data=payload,
            headers={
                API_KEY_HEADER: api_key,
                "User-Agent": CLIENT_USER_AGENT,
                "Accept": "*/*",
                "Content-Type": JSON_CONTENT_TYPE,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                content_type = (
                    (response.headers.get("Content-Type") or "").split(";")[0].strip()
                )
                if content_type != JSON_CONTENT_TYPE:
                    # Một trang HTML (login/redirect/error page) trả 200 là
                    # cách im lặng nhất để một "capture thành công" thành rác.
                    raise CaptureError(
                        f"hợp đồng phải trả {JSON_CONTENT_TYPE}, nhận "
                        f"{content_type!r}"
                    )
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            # Mang mã + `ly` của Tracking (409 `nguon-dang-ghi` khi cron đang
            # ghi, 409 `trang-doc-khong-nhat-quan`, 413 `khoang-ngay-qua-dai`
            # …), KHÔNG mang header — secret không đi ra log.
            raise CaptureError(
                f"không gọi được {CONTRACT_PATH}: {type(exc).__name__}: "
                f"{mo_ta_loi_http(exc)}"
            ) from exc
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
            # Thông điệp KHÔNG mang header — secret không đi ra log.
            raise CaptureError(
                f"không gọi được {CONTRACT_PATH}: {type(exc).__name__}: {exc}"
            ) from exc

    return post


def _ngay(value: str, name: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise CaptureError(f"{name}={value!r} không phải ngày `YYYY-MM-DD`.") from exc


def gop_trang(pages: list[dict[str, Any]]) -> dict[str, Any]:
    """Nối các trang thành MỘT phong bì hợp đồng.

    Kiểm phong bì khớp nhau TRƯỚC khi nối: hai trang khác `date_from` hay khác
    `currency_unit` là hai trạng thái khác nhau, và nối chúng lại là dựng một
    ảnh chụp chưa từng tồn tại ở bất kỳ thời điểm nào.
    """
    if not pages:
        raise CaptureError("không có trang nào để gộp")
    dau = pages[0]
    for field in TRUONG_PHONG_BI:
        if field not in dau:
            raise CaptureError(f"phong bì trang 1 thiếu trường {field!r}")
    for so, trang in enumerate(pages[1:], start=2):
        for field in TRUONG_PHONG_BI:
            if trang.get(field) != dau.get(field):
                raise CaptureError(
                    f"trang {so} lệch phong bì ở {field!r}: "
                    f"{trang.get(field)!r} ≠ {dau.get(field)!r}"
                )
    revision = dau.get("query_revision")
    if not isinstance(revision, str) or not revision.strip():
        raise CaptureError(
            "trang 1 thiếu `query_revision` — không chứng minh được các trang "
            "cùng một trạng thái database; từ chối gộp."
        )
    if dau.get("schema_version") != SCHEMA_VERSION:
        raise CaptureError(
            f"schema_version={dau.get('schema_version')!r} không phải "
            f"{SCHEMA_VERSION!r} — công cụ này không chụp một hợp đồng nó "
            "không hiểu."
        )

    records: list[Any] = []
    errors: list[Any] = []
    for so, trang in enumerate(pages, start=1):
        r = trang.get("records")
        e = trang.get("errors", [])
        if not isinstance(r, list) or not isinstance(e, list):
            raise CaptureError(f"trang {so}: `records`/`errors` phải là danh sách")
        records.extend(r)
        errors.extend(e)

    return {
        **{field: dau.get(field) for field in TRUONG_PHONG_BI},
        "generated_at": dau.get("generated_at"),
        "pages": len(pages),
        "records": records,
        "errors": errors,
    }


#: Những trường phải giống nhau khi gộp nhiều ĐOẠN NGÀY của cùng một lần chụp.
#: Khác `TRUONG_PHONG_BI` ở đúng hai chỗ: `date_from`/`date_to` cố ý KHÁC nhau
#: giữa các đoạn (đó là lý do có nhiều đoạn), và khoảng kết quả là hợp của
#: chúng.
TRUONG_CHUNG_KHOANG = (
    "schema_version",
    "currency_unit",
    "business_timezone",
    "query_revision",
)


def gop_khoang(parts: list[dict[str, Any]]) -> dict[str, Any]:
    """Nối nhiều ĐOẠN NGÀY thành MỘT phong bì cho cả kỳ.

    Hợp đồng có trần 62 ngày mỗi lượt, nên một kỳ rộng hơn phải hỏi làm nhiều
    lượt. Nối chúng lại CHỈ hợp lệ khi mọi đoạn mang cùng `query_revision`:
    khi ấy database không đổi giữa các lượt, và hợp của chúng đúng là một ảnh
    chụp đã từng tồn tại. Lệch một token là hai đoạn của hai trạng thái, và
    ghép lại thì kỳ báo cáo mang giá của hai thời điểm khác nhau mà không có
    gì đỏ lên.

    Không tự thử lại ở đây: bên gọi biết nó đang ở trong một lần chạy nào và
    quyết định được nên báo lỗi hay hỏi lại, còn một vòng lặp thử lại giấu bên
    trong sẽ biến một database đang bận thành một lần chạy treo.
    """
    if not parts:
        raise CaptureError("không có đoạn nào để gộp")
    dau = parts[0]
    for field in TRUONG_CHUNG_KHOANG:
        gia_tri = dau.get(field)
        # `.strip()`: một chuỗi toàn khoảng trắng là "thiếu" chứ không phải
        # một giá trị. Nó vẫn `==` chính nó ở các đoạn sau, nên phép so khớp
        # bên dưới sẽ cho qua và cả kỳ được gộp trên một token rỗng.
        if not isinstance(gia_tri, str) or not gia_tri.strip():
            raise CaptureError(f"đoạn 1 thiếu trường {field!r}")
    for so, phan in enumerate(parts[1:], start=2):
        for field in TRUONG_CHUNG_KHOANG:
            if phan.get(field) != dau.get(field):
                raise CaptureError(
                    f"đoạn {so} lệch {field!r}: {phan.get(field)!r} ≠ "
                    f"{dau.get(field)!r} — hai đoạn đến từ hai trạng thái khác "
                    "nhau của database; không gộp."
                )

    records: list[Any] = []
    errors: list[Any] = []
    for so, phan in enumerate(parts, start=1):
        r, e = phan.get("records"), phan.get("errors", [])
        if not isinstance(r, list) or not isinstance(e, list):
            raise CaptureError(f"đoạn {so}: `records`/`errors` phải là danh sách")
        records.extend(r)
        errors.extend(e)

    return {
        **{field: dau.get(field) for field in TRUONG_CHUNG_KHOANG},
        "date_from": min(str(p.get("date_from")) for p in parts),
        "date_to": max(str(p.get("date_to")) for p in parts),
        "generated_at": dau.get("generated_at"),
        "pages": sum(int(p.get("pages") or 1) for p in parts),
        "windows": len(parts),
        "records": records,
        "errors": errors,
    }


def build_capture(
    post: Poster,
    *,
    product_codes: Iterable[str],
    date_from: str,
    date_to: str,
    capture_id: str,
    captured_by: str,
    source_system_ref: str,
    captured_at: Optional[datetime] = None,
) -> dict[str, Any]:
    """Đọc HẾT các trang và dựng envelope. Lỗi → envelope `FAILED`, không raise."""
    moment = captured_at or datetime.now(timezone.utc)
    envelope: dict[str, Any] = {
        "capture_id": capture_id,
        "captured_at": moment.isoformat(),
        "captured_by": captured_by,
        "source_system_ref": source_system_ref,
    }
    codes = sorted({c for c in product_codes if isinstance(c, str) and c.strip()})
    try:
        if not codes:
            raise CaptureError(
                "danh sách mã rỗng — một lần capture không mã nào là một ảnh "
                "chụp rỗng giả, không phải một kết luận về giá."
            )
        tu = _ngay(date_from, "date_from")
        den = _ngay(date_to, "date_to")
        if tu > den:
            raise CaptureError(f"khoảng ngày ngược: {date_from} > {date_to}")

        pages: list[dict[str, Any]] = []
        cursor: Optional[str] = None
        while True:
            body: dict[str, Any] = {
                "product_codes": codes,
                "date_from": date_from,
                "date_to": date_to,
            }
            if cursor is not None:
                body["cursor"] = cursor
            page = post(body)
            if not isinstance(page, dict):
                raise CaptureError("hợp đồng trả về thứ không phải một ánh xạ")
            if page.get("ok") is False:
                raise CaptureError(f"hợp đồng từ chối: {page.get('ly')!r}")
            pages.append(page)
            cursor = page.get("next_cursor")
            if not cursor:
                break
            if len(pages) >= TRAN_TRANG:
                raise CaptureError(
                    f"vượt {TRAN_TRANG} trang mà `next_cursor` vẫn còn — dừng "
                    "để không chạy vô hạn; kiểm tra phân trang phía Tracking."
                )
        data = gop_trang(pages)
    except CaptureError as exc:
        envelope["capture_status"] = "FAILED"
        envelope["failure_reason"] = str(exc)
        return envelope

    envelope["capture_status"] = "COMPLETE"
    envelope["data"] = data
    return envelope


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Chụp giá MIN theo ngày bán của Tracking (daily-min-v1) ra một file "
            "bất biến cho Reports (READ-ONLY)."
        )
    )
    parser.add_argument(
        "--source-url",
        required=True,
        help=(
            "URL gốc của hợp đồng Tracking (vd https://price.tinphatcrm.com). "
            "KHÔNG có mặc định và không nhúng sẵn."
        ),
    )
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--date-from", required=True)
    parser.add_argument("--date-to", required=True)
    parser.add_argument(
        "--codes-file",
        required=True,
        type=Path,
        help=(
            "File văn bản, mỗi dòng một mã Tracking. Truyền qua FILE chứ không "
            "qua tham số dòng lệnh: danh sách hàng nghìn mã vượt trần độ dài "
            "lệnh, và nó sẽ nằm nguyên trong lịch sử shell."
        ),
    )
    parser.add_argument("--captured-by", required=True, help="Ai/cái gì chạy lần capture này.")
    parser.add_argument("--source-system-ref", default="tracking/api/min-ngay")
    parser.add_argument("--capture-id", default=None)
    args = parser.parse_args(argv)

    try:
        codes = [
            dong.strip()
            for dong in args.codes_file.read_text(encoding="utf-8").splitlines()
            if dong.strip()
        ]
    except OSError as exc:
        print(f"FAILED -> không đọc được {args.codes_file}: {exc}", file=sys.stderr)
        return 1

    capture_id = args.capture_id or (
        "DMIN-"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:8]
    )
    envelope = build_capture(
        _http_poster(args.source_url, os.environ.get(API_KEY_ENV_VAR)),
        product_codes=codes,
        date_from=args.date_from,
        date_to=args.date_to,
        capture_id=capture_id,
        captured_by=args.captured_by,
        source_system_ref=args.source_system_ref,
    )
    path = write_capture(envelope, args.out)
    print(f"{envelope['capture_status']} -> {path}")
    return 0 if envelope["capture_status"] == "COMPLETE" else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
