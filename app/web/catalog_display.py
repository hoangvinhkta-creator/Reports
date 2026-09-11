"""R5 §5 + R5.1 — bản chiếu HIỂN THỊ của danh mục Tracking.

    mã Tracking → model canonical + hãng + nhóm hàng

Module này tồn tại để trả lời đúng một câu trên màn hình nhân viên: *dòng
này, sau khi đã được phân loại, là model gì, của hãng nào, thuộc loại hàng
nào?* Và nó tồn tại theo cách nhỏ nhất có thể trả lời được câu đó.

Ba trường trả lời ba câu KHÁC NHAU, và R5.1 giữ chúng tách bạch có chủ đích:

```text
brand            ai làm ra          "Samsung"
model_label      đúng dòng máy nào  "55Q6FA"
category_label   LOẠI hàng gì       "Tivi"
```

`category_label` vì thế không bao giờ chứa tên hãng, model, nhà cung cấp hay
giá — Tracking CHỌN nó từ một taxonomy đóng (`R5.1 REPAIR-1`, `DEC-205`),
không cắt/lọc từ chuỗi `cat` thô. `None` nghĩa là CHƯA ĐỦ CĂN CỨ, và Reports
không lấp chỗ trống ấy từ tên trên sổ kế toán.

## Vì sao KHÔNG đọc thẳng danh mục ở mỗi lần tải trang

`server._tracking_snapshot()` nói rõ vì sao nó chỉ được gọi khi Owner thật sự
mở bảng chọn của MỘT dòng: một lần pull live giữ authority thô của Tracking
trên đĩa máy chủ, và `S071` §10 bắt dọn nó ngay sau khi dùng. Gọi nó cho mọi
lần render bảng kê là biến một ngoại lệ có kiểm soát thành thói quen — và
thành một lần gọi mạng cho mỗi lần bấm.

Vì vậy R5 ghi lại ĐÚNG hai trường hiển thị mỗi khi một lần pull đã được cho
phép xảy ra vì một lý do khác, rồi đọc lại từ file đó. Không lần gọi mạng
nào được thêm vào.

## Đây KHÔNG phải một bảng danh mục của Reports

Ba ranh giới, và cả ba là ranh giới của `PHB-06 §3`/`BR-02`/`BR-10`:

1. Nó chỉ chứa những gì Tracking ĐÃ NÓI. Không dòng nào được suy ra, và
   không có đường ghi tay nào vào file này.
2. Nó KHÔNG tham gia nhận diện. `TrackingCatalogSnapshot._match_field` không
   đọc `model_label`/`brand`/`category_label`, và module này không được gọi
   từ bất kỳ đường resolve nào — nó chỉ đi vào tầng trình bày. Ghép thêm
   bằng nhóm hàng còn tệ hơn ghép bằng hãng: mọi cái Tivi trên đời sẽ khớp
   với nhau.
3. Nó KHÔNG phải nguồn sự thật. Mất file (deploy mới, đĩa ephemeral) ⟹ màn
   hình hiện TÊN THÔ và "chưa xác định" — đúng trạng thái mà một hệ thống
   chưa biết hãng phải hiện. Không nhánh nào đoán bù.
4. Nó KHÔNG phải một bảng taxonomy. R5.1 không thêm đường sửa nhóm hàng
   trong Reports: sửa ngành hàng xảy ra bên Tracking, và lần capture kế tiếp
   chở giá trị mới sang mà không ai phải phân loại lại mã sản phẩm.

Điểm 3 là lý do file này được phép sống trên đĩa ephemeral: cái giá của việc
mất nó là một màn hình nói ít đi, không phải một màn hình nói sai.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

#: Cùng thư mục với log quyết định Product Identity — cùng vòng đời, và cùng
#: một chỗ để tìm khi cần dọn.
DEFAULT_DISPLAY_PATH = Path("data/product_identity/tracking_display.json")


#: Ba trường hiển thị của một dòng danh mục. Viết MỘT LẦN ở đây để `rows_of`
#: và `read` không thể trôi khỏi nhau — một trường có mặt lúc ghi mà vắng lúc
#: đọc sẽ mất im lặng, và mất im lặng trên một nhãn thì không ai báo lỗi.
FIELDS: tuple[str, ...] = ("model_label", "brand", "category_label")


def rows_of(snapshot) -> dict:
    """`{tracking_code: {"model_label", "brand", "category_label"}}` cho các
    dòng CÓ ít nhất một trong ba trường. Dòng không có gì để nói thì không
    chiếm chỗ."""
    if snapshot is None:
        return {}
    out = {}
    for row in getattr(snapshot, "rows", ()):
        values = {field: getattr(row, field, None) for field in FIELDS}
        if all(value is None for value in values.values()):
            continue
        out[row.tracking_code] = values
    return out


#: Mã lý do một lần ghi bản chiếu KHÔNG thành công. Tập ĐÓNG, và mỗi mã là một
#: câu người đọc hành động được — không phải một mã lỗi kỹ thuật.
REASON_NO_SNAPSHOT = "NO_SNAPSHOT"
REASON_NO_METADATA = "NO_METADATA"
REASON_WRITE_FAILED = "WRITE_FAILED"
#: `R5.3` — CHỈ dùng cho nhánh ghi BỀN (`tracking_display_snapshot`). Nó nói
#: "không có nơi lưu bền nào được cấu hình cho môi trường này", tức máy dev
#: chưa `alembic upgrade head`. Trên production nhánh này KHÔNG xảy ra:
#: `REPORTS_REQUIRE_HISTORY_DB=1` làm container không lên nếu thiếu database.
REASON_NO_STORE = "NO_STORE"

WRITE_REASONS = {
    REASON_NO_SNAPSHOT: (
        "Lần chạy này không có capture danh mục Tracking, nên không có gì để "
        "ghi. Cột Hãng và Nhóm hàng sẽ hiện dấu gạch cho tới lần chạy có "
        "capture danh mục."
    ),
    REASON_NO_METADATA: (
        "Capture danh mục của lần chạy này KHÔNG mang trường hiển thị nào "
        "(model/hãng/nhóm hàng) — thường là một artifact đời cũ. Bảng kê giữ "
        "mã Tracking và dấu gạch; đây là trạng thái ĐÚNG, không phải lỗi."
    ),
    REASON_NO_STORE: (
        "Môi trường này chưa cấu hình nơi lưu bền cho lịch sử, nên nhãn của "
        "lần chạy chỉ nằm trên đĩa máy chủ. Mọi con số vẫn ĐÚNG; nhưng nếu "
        "máy chủ khởi động lại, cột Hãng/Nhóm hàng sẽ hiện dấu gạch cho tới "
        "lần chạy báo cáo kế tiếp."
    ),
    REASON_WRITE_FAILED: (
        "KHÔNG ghi được bản chiếu hiển thị xuống đĩa (đĩa chỉ đọc hoặc hết "
        "chỗ). Báo cáo và mọi con số vẫn đúng, nhưng cột Hãng/Nhóm hàng sẽ "
        "hiện dấu gạch cho tới khi ghi được."
    ),
}


MISSING_PROJECTION_NOTE = (
    "Bản chiếu hiển thị của danh mục Tracking hiện KHÔNG đọc được, nên cột "
    "Mặt hàng giữ tên trên sổ kế toán và cột Hãng/Nhóm hàng hiện dấu gạch — "
    "kể cả với những dòng đã xác nhận mã. Mọi con số của báo cáo vẫn ĐÚNG: "
    "bản chiếu chỉ mang NHÃN, không mang tiền. Chạy lại báo cáo là cách dựng "
    "lại nó; nếu vẫn không có, xem trạng thái ghi bản chiếu trong bằng chứng "
    "của lần chạy."
)


#: Câu mở đầu của cảnh báo STALENESS — khác `MISSING_PROJECTION_NOTE` ở đúng
#: một điểm cốt lõi: bản chiếu KHÔNG rỗng, nó chỉ đang là một bản CŨ. `stale_
#: metadata_note()` ghép câu này với lý do cụ thể của lần ghi gần nhất
#: (`WRITE_REASONS`), để người đọc biết VÌ SAO nó cũ mà không phải tự đoán.
STALE_METADATA_NOTE_PREFIX = (
    "Lần chạy báo cáo GẦN NHẤT không làm mới được bản chiếu hiển thị của "
    "Tracking, nên một số dòng ĐÃ xác nhận mã đang hiện tên trên sổ kế toán "
    "và dấu gạch — KHÔNG phải vì Tracking chưa phân loại, mà vì nhãn của "
    "chúng CHƯA được nạp ở lần chạy này. Mọi con số của báo cáo vẫn ĐÚNG: bản "
    "chiếu chỉ mang NHÃN, không mang tiền. Chạy lại báo cáo để làm mới."
)


def stale_metadata_note(reason: Optional[str]) -> str:
    """Câu cảnh báo STALENESS đầy đủ, kèm LÝ DO cụ thể của lần ghi gần nhất.

    Tách khỏi `MISSING_PROJECTION_NOTE` một cách có chủ đích: "có dữ liệu CŨ,
    một phần chưa được làm mới" là một câu chuyện khác "không có gì cả", và
    dùng chung một câu cho cả hai sẽ nói sai với người đọc ở một trong hai
    trường hợp.
    """
    detail = WRITE_REASONS.get(reason, "") if reason else ""
    return f"{STALE_METADATA_NOTE_PREFIX} {detail}".strip()


@dataclass(frozen=True)
class WriteResult:
    """Kết quả MỘT lần ghi bản chiếu — để tầng gọi NÓI RA thay vì đoán.

    Trước `R5.1 REPAIR-2`, `write()` trả `None` và nuốt mọi thất bại. Với
    luồng "mở bảng chọn" điều đó chấp nhận được (Owner đang đứng ngay đó và
    thấy ngay), nhưng với luồng CHẠY BÁO CÁO thì không: bản chiếu là thứ duy
    nhất làm cột Hãng/Nhóm hàng có nội dung, và một lần ghi thất bại im lặng
    cho ra đúng triệu chứng production đã gặp — cả bảng chỉ có dấu gạch, không
    một dòng nào giải thích vì sao.

    `written=False` KHÔNG phải một lỗi cần dừng lần chạy: bản chiếu là NHÃN.
    Nó là một sự thật cần ghi vào bằng chứng của run và cần nói trên màn hình.
    """

    written: bool
    rows: int = 0
    reason: Optional[str] = None

    @property
    def note(self) -> Optional[str]:
        """Câu giải thích cho người đọc, hoặc `None` khi ghi thành công."""
        return None if self.reason is None else WRITE_REASONS.get(self.reason)

    def as_evidence(self) -> dict:
        """Hình dạng đi vào `tracking_evidence` của một run.

        Chỉ ba trường nguyên thuỷ, JSON được, không mirror một dòng danh mục
        nào — thẩm quyền vẫn ở Tracking (`ADR-107`).
        """
        return {"written": self.written, "rows": self.rows,
                "reason": self.reason}


def _status_path(target: Path) -> Path:
    """Đường dẫn TRẠNG THÁI của lần ghi gần nhất — cạnh chính bản chiếu.

    File RIÊNG, KHÔNG một khoá đặc biệt nhồi vào bản chiếu: `read()` đọc MỌI
    khoá top-level của bản chiếu như một `tracking_code`, nên một khoá trạng
    thái ở đó sẽ va với một mã Tracking thật có tên trùng nó (khó nhưng không
    phải không thể) và làm bản chiếu tự bịa ra một "mã sản phẩm" không do
    Tracking nói.
    """
    return target.with_name(target.stem + ".status.json")


def _record_status(target: Path, result: WriteResult) -> None:
    """Ghi lại KẾT QUẢ của lần gọi `write()` này, best-effort như chính nó.

    Đây là điều kiện để phân biệt hai trạng thái mà chỉ đọc `read()` không
    tách được, khi một mã CONFIRMED vẫn thiếu nhãn:

        Tracking đơn giản CHƯA phân loại mã này    → hợp lệ (`AR-R5.1-01`)
        lần chạy GẦN NHẤT không làm mới được bản
        chiếu, nên nó đang hiện một bản CŨ có thể
        thiếu mã mới xác nhận SAU lần ghi cuối cùng → lỗi luồng chính, cần
                                                      cảnh báo (`R5.1 REPAIR-2`
                                                      lần 2)

    `read()` một mình không phân biệt được hai câu trên: cả hai cho ra cùng
    một `display.get(code)` là falsy. Chỉ có LỊCH SỬ ghi — "lần gần nhất có
    thành công không, và vì sao không" — mới tách được chúng, và đó là toàn bộ
    lý do file trạng thái này tồn tại.

    Lỗi ghi trạng thái KHÔNG được làm hỏng lần gọi đang chạy và KHÔNG được đổi
    giá trị `write()` trả về — cùng kỷ luật fail-safe mà chính `write()` áp
    dụng cho bản chiếu.
    """
    try:
        status_path = _status_path(target)
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(
            json.dumps({"written": result.written, "rows": result.rows,
                       "reason": result.reason}, ensure_ascii=False),
            encoding="utf-8")
    except OSError:
        return


def _finish(target: Path, result: WriteResult) -> WriteResult:
    """Ghi trạng thái rồi trả `result` ra NGUYÊN VẸN — một chỗ DUY NHẤT gọi
    `_record_status`, để không lần sửa `write()` nào trong tương lai quên ghi
    trạng thái ở MỘT nhánh mà quên ở nhánh khác."""
    _record_status(target, result)
    return result


def last_write_status(path: Optional[Path] = None) -> Optional[WriteResult]:
    """`WriteResult` của lần ghi GẦN NHẤT, hoặc `None` khi chưa có bằng chứng.

    `None` KHÔNG có nghĩa "lỗi" — nó có nghĩa "chưa từng gọi `write()` cho
    đường dẫn này, hoặc trạng thái không đọc được", và tầng gọi coi đó là
    TRUNG TÍNH: không đủ căn cứ để cảnh báo bản chiếu đang STALE, vì không có
    gì để so với hiện tại.
    """
    target = Path(path or DEFAULT_DISPLAY_PATH)
    try:
        payload = json.loads(
            _status_path(target).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    written = payload.get("written")
    if not isinstance(written, bool):
        return None
    reason = payload.get("reason")
    if reason is not None and reason not in WRITE_REASONS:
        return None
    rows = payload.get("rows")
    if not isinstance(rows, int):
        rows = 0
    return WriteResult(written=written, rows=rows, reason=reason)


def write(snapshot, path: Optional[Path] = None) -> WriteResult:
    """Ghi bản chiếu hiển thị. Lỗi ghi KHÔNG được làm hỏng lần gọi đang chạy.

    Đây là một tác dụng phụ tiện ích của một thao tác khác (mở bảng chọn, chạy
    báo cáo). Nếu nó thất bại, thứ duy nhất mất đi là vài cái nhãn — biến điều
    đó thành một trang lỗi sẽ đánh đổi một tính năng chính lấy một tính năng
    phụ.

    Nhưng nó KHÔNG còn thất bại im lặng: hàm trả về `WriteResult` để tầng gọi
    ghi vào bằng chứng của run và hiện lên màn hình (`R5.1 REPAIR-2`). Những
    nơi gọi cũ bỏ qua giá trị trả về vẫn chạy y như trước.

    Mỗi lần gọi CŨNG ghi lại kết quả của chính nó vào một file trạng thái cạnh
    bản chiếu (`_record_status`), để một REQUEST SAU (ví dụ render tab Nhân
    viên ở một lần tải trang khác) biết được lần ghi gần nhất có thành công
    hay không — không chỉ nội dung bản chiếu đang có trên đĩa. Đây là điều
    kiện để `_catalog_projection_warning` phân biệt được "chưa Tracking phân
    loại" khỏi "bản chiếu đang STALE vì lần chạy gần nhất hỏng".
    """
    target = Path(path or DEFAULT_DISPLAY_PATH)
    if snapshot is None:
        return _finish(target, WriteResult(
            written=False, reason=REASON_NO_SNAPSHOT))
    rows = rows_of(snapshot)
    if not rows:
        # Danh mục đọc được nhưng KHÔNG dòng nào có một trong ba trường hiển
        # thị — artifact đời cũ. Giữ nguyên bản chiếu đang có (nếu có): ghi một
        # file rỗng lên nó sẽ XOÁ nhãn của những mã mà một lần chạy trước đã
        # đọc được, tức làm màn hình nói ÍT hơn vì một capture cũ.
        return _finish(target, WriteResult(
            written=False, reason=REASON_NO_METADATA))
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(rows, ensure_ascii=False, sort_keys=True),
            encoding="utf-8")
    except OSError:
        return _finish(target, WriteResult(
            written=False, rows=len(rows), reason=REASON_WRITE_FAILED))
    return _finish(target, WriteResult(written=True, rows=len(rows)))


def normalise(payload) -> dict:
    """Một payload BẤT KỲ → đúng hình dạng bản chiếu, hoặc `{}`.

    `R5.3` tách phép vệ sinh này ra khỏi `read()` vì bản chiếu nay có HAI
    nguồn đọc — file cache trên đĩa và bản lưu BỀN theo lần chạy — và cả hai
    phải qua CÙNG một phép vệ sinh. Hai bản sao của cùng một luật là hai bản
    sẽ trôi khỏi nhau, và chỗ chúng trôi khỏi nhau là chỗ một giá trị không
    phải chuỗi lọt lên màn hình như một cái tên hãng.

    Mọi hư hỏng đều cho ra `{}` hoặc `None` cho trường ấy — không nhánh nào
    ép kiểu và không nhánh nào đoán bù.
    """
    if not isinstance(payload, dict):
        return {}
    out = {}
    for code, value in payload.items():
        if not isinstance(code, str) or not isinstance(value, dict):
            continue
        out[code] = {}
        for field in FIELDS:
            text = value.get(field)
            out[code][field] = text if isinstance(text, str) and text else None
    return out


def read(path: Optional[Path] = None) -> dict:
    """Bản chiếu đã ghi trên đĩa, hoặc `{}`.

    Mọi hư hỏng đều cho ra `{}` — file chưa có, JSON hỏng, kiểu sai. Cả ba
    dẫn tới cùng một màn hình: tên thô và "chưa xác định". Phân biệt chúng ở
    đây sẽ tạo ra ba nhánh mà không nhánh nào đổi được điều người dùng thấy.

    `R5.3` — từ bản này, `{}` KHÔNG còn là câu trả lời cuối cùng của hệ
    thống: tầng gọi dựng lại bản chiếu từ bản lưu BỀN của lần chạy
    (`restore()` ngay dưới). File này là một CACHE, không phải nguồn sự thật
    duy nhất — xem `server._tracking_display()`.
    """
    target = Path(path or DEFAULT_DISPLAY_PATH)
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return normalise(payload)


def restore(rows: dict, path: Optional[Path] = None) -> bool:
    """Ghi LẠI cache đĩa từ một bản chiếu đã dựng lại. `True` khi ghi được.

    Khác `write()` ở ba điểm, và cả ba là có chủ ý:

    1. Nó nhận `rows` đã dựng sẵn, không nhận một snapshot — nguồn của nó là
       bản lưu BỀN của chính lần chạy, không phải một capture mới.
    2. Nó KHÔNG đụng file trạng thái (`_record_status`). Trạng thái ấy trả
       lời "lần ghi từ CAPTURE gần nhất có thành công không", và đó là câu
       mà `_catalog_projection_warning` hình dạng 2 dựa vào. Một lần khôi
       phục cache không phải một lần ghi từ capture, nên nó không được phép
       viết lại lịch sử ấy — làm thế sẽ xoá mất bằng chứng của một lần ghi
       hỏng và làm cảnh báo STALE im lặng sai.
    3. Thất bại là chuyện thường và KHÔNG được nói ra ở đâu: đĩa chỉ đọc thì
       lần tải trang sau lại dựng lại từ bản bền, chậm hơn vài mili giây và
       không sai một chữ nào.
    """
    if not rows:
        return False
    target = Path(path or DEFAULT_DISPLAY_PATH)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(rows, ensure_ascii=False, sort_keys=True),
            encoding="utf-8")
    except OSError:
        return False
    return True


def brand_source(display: dict):
    """`BrandSource` của PHB-06 đọc từ bản chiếu này — mở lại `PHB-06` CÓ CHỦ ĐÍCH.

    `brand_identity.canonical_brand` đọc trường `brand` TRÊN chính danh tính,
    và hợp đồng danh tính hôm nay vẫn không có trường đó (`INV-18`: so sánh
    LUÔN bằng đủ tuple — thêm một trường hiển thị vào value object sẽ làm hai
    danh tính cùng mã khác hãng thành hai danh tính KHÁC NHAU). Nên R5 đi
    đường thứ hai mà `PHB-06 §4` đã để ngỏ: một read model canonical tương
    đương, cắm vào đúng tham số `brand_source` đã có sẵn.

    Không có bảng brand nào của riêng Reports được tạo ra: bảng chiếu này chỉ
    chứa những gì Tracking đã nói, và hàm này chỉ tra `source_product_code`.
    """
    def source(identity) -> Optional[str]:
        if identity is None:
            return None
        code = getattr(identity, "source_product_code", None)
        if not code:
            return None
        return (display.get(code) or {}).get("brand")
    return source


def category_of(display: dict, code: Optional[str]) -> Optional[str]:
    """Nhóm hàng canonical của một mã, hoặc `None`.

    `None` KHÔNG có nghĩa "đoán lấy một nhóm": tầng gọi hiện một ô trống hoặc
    chữ "chưa phân loại", và đó là câu trả lời đúng cho một mã mà Tracking
    chưa xếp ngành hàng. Khác `label_of`, ở đây KHÔNG có fallback nào — mã
    Tracking là một cái mã, không phải một loại hàng hoá.
    """
    if not code:
        return None
    return (display.get(code) or {}).get("category_label")


def label_of(display: dict, code: Optional[str]) -> Optional[str]:
    """Model canonical của một mã, hoặc `None`.

    `None` KHÔNG có nghĩa "dùng mã": tầng gọi tự quyết định fallback, và câu
    trả lời của R5 §5 cho dòng ĐÃ phân loại là fallback về chính mã Tracking
    — một mã đối chiếu được vẫn hơn một ô trống.
    """
    if not code:
        return None
    return (display.get(code) or {}).get("model_label")


__all__ = ["DEFAULT_DISPLAY_PATH", "FIELDS", "MISSING_PROJECTION_NOTE",
           "REASON_NO_METADATA",
           "REASON_NO_SNAPSHOT", "REASON_NO_STORE", "REASON_WRITE_FAILED",
           "STALE_METADATA_NOTE_PREFIX", "WRITE_REASONS",
           "WriteResult", "brand_source", "category_of",
           "label_of", "last_write_status", "normalise", "read", "restore",
           "rows_of", "stale_metadata_note", "write"]
