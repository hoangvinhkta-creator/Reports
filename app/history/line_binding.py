"""Gắn dòng nguồn của một snapshot mới vào ĐÚNG khoá dòng đã có (R3 §1).

Hàm THUẦN: không DB, không thời gian, không I/O. Vào là các dòng của snapshot
mới cộng hiện trạng của từng nhóm khoá; ra là một `occurrence_index` cho mỗi
dòng, cộng danh sách những chỗ hệ thống KHÔNG dám tự ghép.

## Vấn đề mà module này đóng lại

Trước R3, `occurrence_index` được đánh bằng ĐÚNG một quy tắc: sắp theo
``source_row`` tăng dần rồi đếm 1..n trong phạm vi ``(order_key, product_key)``
(`app/history/extraction.build_source_lines`). Quy tắc đó ổn định khi và chỉ
khi THỨ TỰ DÒNG trong file không đổi — một điều kiện mà không gì trong hệ
thống bảo đảm, vì file là một workbook do kế toán sửa tay.

Hệ quả cụ thể, và nó tốn tiền: một đơn có hai dòng cùng tên hàng (dữ liệu thật
có — "Chi phí vận chuyển" xuất hiện hai lần trong một đơn). Owner gõ giá nhập
cho dòng thứ nhất; khoá của quyết định đó là ``(BH…, sha256(tên), 1)``. Lần
nạp sau, kế toán đảo hai dòng đó cho nhau trong file. Dòng VẬT LÝ thứ hai bây
giờ nhận ``occurrence_index = 1`` — và giá nhập Owner đã gõ cho dòng kia lặng
lẽ chuyển sang nó. Không cờ nào bật, không màn hình nào đổi, con số thì sai.

Đó là "gắn nhầm override", và nó là một lỗi của PHÉP GẮN chứ không phải của
dữ liệu: sổ nguồn không cấp một ID dòng ổn định nào, nên vị trí đã bị dùng
làm danh tính.

## Ba mỏ neo, theo đúng thứ tự sức mạnh

    1. ``IMEI``          — mã máy, DUY NHẤT cho một chiếc hàng có thật.
    2. ``FINGERPRINT``   — toàn bộ nội dung nghiệp vụ của dòng không đổi.
    3. ``POSITION``      — thứ tự dòng, mỏ neo YẾU NHẤT và có điều kiện.

Mỏ neo 1 là thứ gần nhất với một ID dòng ổn định mà sổ này có. Nó thắng cả
fingerprint: một chiếc máy có IMEI mà kế toán sửa lại giá bán VẪN là chiếc máy
đó, còn hai chiếc cùng model cùng giá thì fingerprint không phân biệt nổi.

Mỏ neo 3 chỉ được dùng khi việc dùng sai nó KHÔNG THỂ làm hỏng gì — xem dưới.

## Vì sao vị trí chỉ được dùng có điều kiện

Ghép sai vị trí gây hại ĐÚNG khi một quyết định của người đang treo trên khoá
bị ghép sai. Nếu không khoá nào trong nhóm mang quyết định nào, thì hai cách
ghép cho ra hai lịch sử version khác nhau nhưng KHÔNG khác nhau một đồng nào,
và bắt Owner đi xử lý một "ngoại lệ" như thế là tạo ra nhiễu để rồi chính họ
học cách bấm bỏ qua.

Vì vậy quy tắc là:

    còn ĐÚNG một dòng vào và ĐÚNG một khoá trống   → ghép (không có lựa chọn nào khác)
    không khoá trống nào mang quyết định của người → ghép theo thứ tự (vô hại)
    còn lại                                        → KHÔNG ghép, dựng NGOẠI LỆ

Nhánh thứ ba KHÔNG bao giờ đoán. Các dòng vào nhận khoá MỚI (chỉ số nối tiếp
sau chỉ số lớn nhất đã dùng), nên không quyết định nào bị gắn nhầm; các khoá
cũ KHÔNG bị xoá và KHÔNG bị hủy — chúng chỉ vắng mặt ở snapshot này, đúng cơ
chế `absent_keys` đã nghiệm thu ở PRA-002 slice B. Owner nhận một ngoại lệ nói
rõ đơn nào, mặt hàng nào, và quyết định nào đang treo.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, replace
from typing import Iterable, Mapping, Optional, Sequence

from app.history.models import LineKey, SourceLine

#: Mỏ neo đã dùng để gắn một dòng vào khoá của nó. Ghi lại để bằng chứng nói
#: được "vì sao dòng này là dòng kia", chứ không chỉ "nó là dòng kia".
ANCHOR_IMEI = "IMEI"
ANCHOR_FINGERPRINT = "FINGERPRINT"
ANCHOR_POSITION = "POSITION"
ANCHOR_NEW = "NEW"

ANCHORS = (ANCHOR_IMEI, ANCHOR_FINGERPRINT, ANCHOR_POSITION, ANCHOR_NEW)

#: Loại ngoại lệ duy nhất mà module này dựng. Một chuỗi, không một enum, vì nó
#: đi thẳng xuống một cột ``TEXT`` và phải đọc được nguyên văn trong database.
EXCEPTION_AMBIGUOUS_BINDING = "AMBIGUOUS_LINE_BINDING"


@dataclass(frozen=True)
class ExistingOccurrence:
    """Một khoá dòng ĐANG hiện hành trong nhóm ``(order_key, product_key)``.

    ``owner_decisions`` là các quyết định của người đang treo trên khoá này
    (giá nhập tay, gán nhân viên, phân loại dòng, loại khỏi báo cáo). Rỗng
    nghĩa là ghép sai khoá này không làm sai một đồng nào — và đó chính là
    điều kiện cho phép dùng mỏ neo vị trí.
    """

    occurrence_index: int
    fingerprint: str
    imei: Optional[str] = None
    owner_decisions: tuple[str, ...] = ()

    @property
    def protected(self) -> bool:
        return bool(self.owner_decisions)


@dataclass(frozen=True)
class AmbiguousBinding:
    """Một nhóm mà hệ thống từ chối đoán — kèm đủ dữ kiện để người quyết."""

    order_key: str
    product_key: str
    #: Chỉ số MỚI đã cấp cho dòng vào (không đụng vào khoá cũ nào).
    assigned_occurrence_index: int
    source_row: int
    #: Các khoá cũ còn trống mà dòng vào CÓ THỂ là một trong số đó.
    candidate_occurrence_indexes: tuple[int, ...]
    #: Tập con của trên: những khoá đang mang quyết định của người.
    protected_occurrence_indexes: tuple[int, ...]
    #: Nhãn quyết định đang treo, gộp và sắp xếp — để màn hình nói được
    #: "đang treo giá nhập tay" chứ không chỉ "có gì đó".
    protected_decisions: tuple[str, ...]

    def detail(self) -> dict:
        return {
            "candidate_occurrence_indexes": list(self.candidate_occurrence_indexes),
            "protected_occurrence_indexes": list(self.protected_occurrence_indexes),
            "protected_decisions": list(self.protected_decisions),
            "source_row": self.source_row,
        }


@dataclass(frozen=True)
class BindingResult:
    lines: tuple[SourceLine, ...]
    #: ``khoá tạm (theo vị trí) → khoá đã gắn``. Chỉ chứa các khoá THỰC SỰ đổi.
    remap: dict
    #: ``khoá đã gắn → mỏ neo``. Bằng chứng, không tham gia phép tính nào.
    anchors: dict
    ambiguities: tuple[AmbiguousBinding, ...]

    def rebound_results(self, results: Sequence) -> tuple:
        """Chiếu cùng phép đổi khoá sang các dòng KẾT QUẢ đi kèm.

        Dòng nguồn và dòng kết quả là hai trục của CÙNG một dòng bán, ghép với
        nhau bằng khoá. Đổi khoá ở một trục mà quên trục kia sẽ làm
        ``_insert_result_versions`` ghi kết quả vào một khoá không tồn tại —
        nên phép đổi được viết ĐÚNG MỘT LẦN, ở đây.
        """
        if not self.remap:
            return tuple(results)
        return tuple(
            replace(result, key=self.remap[result.key])
            if result.key in self.remap else result
            for result in results
        )


def normalized_imei(value: Optional[str]) -> Optional[str]:
    """IMEI dùng được làm mỏ neo, hoặc ``None``.

    Chuẩn hoá tối thiểu và KHÔNG khoan dung: NFC, bỏ khoảng trắng hai đầu và
    khoảng trắng bên trong, casefold. Một ô trống, hay một ô chỉ có khoảng
    trắng, KHÔNG phải một mỏ neo — coi chuỗi rỗng là một IMEI sẽ gộp mọi dòng
    không có IMEI vào cùng một danh tính, tức đúng lỗi mà module này đóng lại.
    """
    if value is None:
        return None
    text = unicodedata.normalize("NFC", str(value))
    text = "".join(text.split()).casefold()
    return text or None


def bind_occurrences(
    lines: Sequence[SourceLine],
    existing: Mapping[tuple, Sequence[ExistingOccurrence]],
) -> BindingResult:
    """Gắn mỗi dòng nguồn vào một ``occurrence_index``, theo ba mỏ neo.

    ``lines`` mang khoá TẠM do `build_source_lines` đánh theo vị trí; hàm này
    thay nó bằng khoá đã gắn. ``existing`` là hiện trạng theo nhóm
    ``(order_key, product_key)``; nhóm vắng mặt ⟹ mọi dòng của nhóm là dòng
    mới, và kết quả trùng khớp HÀNH VI TRƯỚC R3 (1..n theo ``source_row``).
    """
    bound: list[SourceLine] = []
    remap: dict = {}
    anchors: dict = {}
    ambiguities: list[AmbiguousBinding] = []

    for group, incoming in _grouped(lines).items():
        available = sorted(
            existing.get(group, ()), key=lambda item: item.occurrence_index)
        used = {item.occurrence_index for item in available}
        assignments, unresolved = _assign_group(incoming, available, used)
        for line, occurrence, anchor in assignments:
            key = LineKey(group[0], group[1], occurrence)
            if key != line.key:
                remap[line.key] = key
                line = replace(line, key=key)
            anchors[key] = anchor
            bound.append(line)
        ambiguities.extend(unresolved)

    # Thứ tự trả về theo ``source_row``: mọi tầng gọi (reconcile, membership,
    # ghép dòng kết quả) đọc hai danh sách song song theo thứ tự này, và đổi
    # thứ tự ở đây sẽ ghép kết quả sang nhầm dòng.
    bound.sort(key=lambda line: line.source_row)
    return BindingResult(
        lines=tuple(bound), remap=remap, anchors=anchors,
        ambiguities=tuple(ambiguities),
    )


def _grouped(lines: Iterable[SourceLine]) -> dict:
    grouped: dict = {}
    for line in sorted(lines, key=lambda item: item.source_row):
        grouped.setdefault((line.key.order_key, line.key.product_key), []).append(line)
    return grouped


def _assign_group(incoming, available, used):
    """Ghép các dòng vào của MỘT nhóm với các khoá đang có của nhóm đó."""
    assignments: list[tuple] = []
    ambiguities: list[AmbiguousBinding] = []
    free = list(available)
    pending = list(incoming)

    pending, free = _match_by_imei(pending, free, assignments)
    pending, free = _match_by_fingerprint(pending, free, assignments)

    if pending and free:
        if len(pending) == 1 and len(free) == 1:
            # Không có lựa chọn nào khác để nhầm: một dòng vào, một khoá trống.
            # Đây là ca "kế toán sửa một giá trị trên dòng" — ghép đúng ở đây
            # là toàn bộ lý do `SOURCE_CHANGED` tồn tại.
            assignments.append((pending[0], free[0].occurrence_index, ANCHOR_POSITION))
            pending, free = [], []
        elif not any(item.protected for item in free):
            paired = min(len(pending), len(free))
            for line, slot in zip(pending[:paired], free[:paired]):
                assignments.append((line, slot.occurrence_index, ANCHOR_POSITION))
            pending, free = pending[paired:], free[paired:]
        else:
            candidates = tuple(item.occurrence_index for item in free)
            protected = tuple(
                item.occurrence_index for item in free if item.protected)
            decisions = tuple(sorted({
                name for item in free for name in item.owner_decisions}))
            next_index = (max(used) if used else 0) + 1
            for line in pending:
                assignments.append((line, next_index, ANCHOR_NEW))
                ambiguities.append(AmbiguousBinding(
                    order_key=line.key.order_key,
                    product_key=line.key.product_key,
                    assigned_occurrence_index=next_index,
                    source_row=line.source_row,
                    candidate_occurrence_indexes=candidates,
                    protected_occurrence_indexes=protected,
                    protected_decisions=decisions,
                ))
                used.add(next_index)
                next_index += 1
            pending, free = [], free

    for line in pending:
        next_index = (max(used) if used else 0) + 1
        used.add(next_index)
        assignments.append((line, next_index, ANCHOR_NEW))

    return assignments, ambiguities


def _match_by_imei(pending, free, assignments):
    by_imei: dict = {}
    for item in free:
        anchor = normalized_imei(item.imei)
        if anchor is not None:
            by_imei.setdefault(anchor, []).append(item)
    if not by_imei:
        return pending, free

    taken = set()
    rest = []
    for line in pending:
        anchor = normalized_imei(line.imei)
        bucket = by_imei.get(anchor) if anchor is not None else None
        match = next(
            (item for item in bucket or ()
             if item.occurrence_index not in taken), None)
        if match is None:
            rest.append(line)
            continue
        taken.add(match.occurrence_index)
        assignments.append((line, match.occurrence_index, ANCHOR_IMEI))
    return rest, [item for item in free if item.occurrence_index not in taken]


def _match_by_fingerprint(pending, free, assignments):
    by_fingerprint: dict = {}
    for item in free:
        by_fingerprint.setdefault(item.fingerprint, []).append(item)

    taken = set()
    rest = []
    for line in pending:
        bucket = by_fingerprint.get(line.fingerprint)
        match = next(
            (item for item in bucket or ()
             if item.occurrence_index not in taken), None)
        if match is None:
            rest.append(line)
            continue
        taken.add(match.occurrence_index)
        assignments.append((line, match.occurrence_index, ANCHOR_FINGERPRINT))
    return rest, [item for item in free if item.occurrence_index not in taken]


__all__ = [
    "ANCHORS", "ANCHOR_FINGERPRINT", "ANCHOR_IMEI", "ANCHOR_NEW",
    "ANCHOR_POSITION", "AmbiguousBinding", "BindingResult",
    "EXCEPTION_AMBIGUOUS_BINDING", "ExistingOccurrence", "bind_occurrences",
    "normalized_imei",
]
