"""Employee-mapping diagnostics F1–F6 — TD-001, HD-110-01, HD-110-03.

**Why this file exists.** These criteria were written for
`tools/analysis/reconcile_conversion.py`, an analysis script somebody runs by
hand. TD-001 (`PROJECT/PROJECT_PROGRESS.md` → "Nợ Kỹ Thuật / Cảnh Báo Vận
Hành") requires F2 and F4 to appear in the Review Queue, and the Review Queue
lives on the import path. So the criteria live here — in production — and the
script imports them back. The direction matters: production owns the rule, the
analysis tool consumes it, never the reverse.

`reconcile_conversion.py` must keep behaving exactly as it did when
CHECK-108A1-15 was signed off — that output is shipped evidence for a task
already reviewed and merged, and quietly shifting it would invalidate a
record, not improve it (CHECK-110-14). That is why `RawMappingVerdict` still
exposes `hard_failures` / `warnings` / `info` as the very same lists of
strings, in the very same order: the script and its tests see no change at
all. Production reads `findings` instead, which carries the same verdicts as
structured objects so each one can be traced back to real rows (Independent
Review #1, Finding 1).

    Hard failures (invariants — cannot be true of correct master data):
        F1  every employee's `group` must be declared in `employee_groups`
        F3  no raw `NVBH` may match two employees whose effective windows
            overlap on that row's own date (DEC-121)
        F5  at least one employee must map at all

    Warnings (heuristics — worth a human's attention, never block):
        F2  a configured employee, active and effective in this dataset's
            range, that matched no row
        F4  an unmapped name carrying at least as many rows as the smallest
            mapped employee. A blank `NVBH` never counts: there is no identity
            for master data to be missing, and that row is already reported as
            `Missing.employee` (Review #2, Finding 1).

    F6 is a warning too, but it does not live in `evaluate_raw_mapping`:
        F6  a config RECORD flagged `active: false` that still owns rows inside
            its own effective window (HD-110-03). It needs each row's date and
            the production mapper's record-selection semantics, which the
            analysis script never collects — see `evaluate_inactive_records`.
            Keeping it out also means `evaluate_raw_mapping` still produces
            exactly the F1–F5 output signed off in CHECK-108A1-15.

    Info: employees legitimately absent (not yet effective, no longer
    effective, or `active: false` with no rows). Reporting these silently as
    "missing" would train readers to ignore F2.

**F6 exists because of a gap Independent Review #1 exposed.** Removing
`inactive` from the `Missing.employee` rule (Finding 3) would have left a
salesperson marked as having left, yet still selling, with no signal anywhere
— while their revenue kept flowing into their KPI. `active: false` covering
rows that actually happened is contradictory master data. F6 reports it and
changes nothing else: no calculation moves, no KPI ownership moves. The
project owner approved exactly this shape (HD-110-03) rather than letting the
tool invent a rule of its own.

Independent Review #2 then found F6 was aggregating by employee NAME. A closed
historical record and a current active record share a name by design — that is
how DEC-121 expresses a handover — so the closed one raised a false F6 on the
active one's transactions. F6 now resolves each row to a specific record by
that row's own date (`evaluate_inactive_records`).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from app.modules.config.loader import as_date
from app.modules.domain.models import WorkingLine
from app.modules.mapping.employee_mapper import EmployeeMapper, RecordRef
from app.modules.validation.models import (
    AffectedRow,
    AmbiguousRow,
    Diagnostics,
    RowProvenance,
)
from app.modules.validation.text import normalize_text

BUCKET_HARD = "HARD"
BUCKET_WARNING = "WARNING"
BUCKET_INFO = "INFO"


# Re-exported under its original name: `tools/analysis/reconcile_conversion.py`
# imports `norm` from this module and must keep working untouched
# (CHECK-110-14). The implementation now lives in `text.py` so the validation
# rules and these criteria normalize identically (Review #1, Finding 4).
norm = normalize_text


@dataclass(frozen=True)
class MappingFinding:
    """Một verdict F1–F6, kèm mọi thứ cần để lần ngược về dòng thô.

    `message` đúng là chuỗi mà script phân tích vẫn luôn in ra — nó là bản
    render, không phải bản ghi. `criterion`, `employee`, `raw_value` và
    `provenance` mới là bản ghi.

    **Không còn trường `details: dict`** (DEC-132, điểm 8). Trước Independent
    Review #5, đó là một kênh khóa tùy ý chạy song song với `affected_rows`:
    một finding có thể mang `affected_rows = (dòng 6,)` mà `details` lại nói
    về dòng 7, và validator sao chép nguyên trạng sang `ReviewItem`. Không có
    quy ước nào đóng được cửa đó — chỉ có việc gỡ bỏ cánh cửa. Metadata chẩn
    đoán giờ là các TRƯỜNG CÓ TÊN, CÓ KIỂU: thêm một trường là sửa dataclass
    và lọt vào code review; thêm một khóa dict thì không ai thấy.
    """

    criterion: str
    bucket: str
    message: str
    employee: Optional[str] = None
    raw_value: Optional[str] = None
    raw_prefix: Optional[str] = None
    declared_group: Optional[str] = None
    # TẬP DÒNG canonical — nguồn duy nhất của mọi provenance mà finding này
    # phơi ra. Không có accessor nào tra dòng theo canonical identity, vì
    # không còn chỗ nào để tra.
    provenance: RowProvenance = field(default_factory=RowProvenance)

    @property
    def affected_rows(self) -> tuple[AffectedRow, ...]:
        return self.provenance.rows

    @property
    def affected_count(self) -> int:
        return self.provenance.affected_count

    @property
    def source_rows(self) -> tuple[int, ...]:
        return self.provenance.source_rows

    @property
    def source_file(self) -> Optional[str]:
        return self.provenance.source_file

    @property
    def batch_scoped(self) -> bool:
        return self.provenance.batch_scoped

    def raw_variants(self) -> dict[str, list[int]]:
        return self.provenance.raw_variants()

    def render_variants(self) -> str:
        return self.provenance.render_variants()

    def diagnostics(self) -> Diagnostics:
        """Metadata chẩn đoán CÓ KIỂU — không thể nhắc tới dòng nào.

        Trả một `Diagnostics`, không phải dict: không còn khoá tuỳ ý để một
        tham chiếu dòng lẻn vào. Một dòng muốn tới `ReviewItem` chỉ còn đúng
        một đường là `provenance` (INVARIANT P).
        """
        return Diagnostics(
            criterion=self.criterion,
            employee=self.employee,
            raw_value=self.raw_value,
            raw_prefix=str(self.raw_prefix) if self.raw_prefix else None,
            declared_group=self.declared_group,
        )


@dataclass(frozen=True)
class RawMappingVerdict:
    """Outcome of the raw employee-mapping reconciliation.

    `hard_failures` alone decide the exit code. Warnings and info are printed
    but never fail the run — a diagnostic that can be wrong must not be able
    to block a merge on its own.
    """

    findings: list[MappingFinding] = field(default_factory=list)

    def _messages(self, bucket: str) -> list[str]:
        return [f.message for f in self.findings if f.bucket == bucket]

    @property
    def hard_failures(self) -> list[str]:
        return self._messages(BUCKET_HARD)

    @property
    def warnings(self) -> list[str]:
        return self._messages(BUCKET_WARNING)

    @property
    def info(self) -> list[str]:
        return self._messages(BUCKET_INFO)


def _effective_window(row: dict) -> tuple[date, date]:
    starts = as_date(row.get("effective_from")) or date.min
    ends = as_date(row.get("effective_to")) or date.max
    return starts, ends


def _overlaps(row: dict, start: Optional[date], end: Optional[date]) -> bool:
    if start is None or end is None:
        return True  # unknown dataset range: assume the employee is in scope
    starts, ends = _effective_window(row)
    return starts <= end and start <= ends


def evaluate_raw_mapping(
    mapped: Counter,
    groups: dict[str, str],
    unmapped: Counter,
    ambiguities: dict[str, set],
    employees: list[dict],
    declared_groups: set[str],
    dataset_start: Optional[date] = None,
    dataset_end: Optional[date] = None,
    row_index: Optional["MappingStats"] = None,
) -> RawMappingVerdict:
    """Criteria for the raw employee-mapping reconciliation.

    Counting rows and printing them proves nothing on its own: a badly broken
    `employees.yaml` still produces a tidy table, just a wrong one. But the
    opposite failure is just as bad — a criterion that fires on healthy data
    is noise, and noise gets ignored. So the criteria are split by how certain
    they are. See the module docstring for F1–F6.

    None of these criteria names an expected employee or group. An
    expected-values table written here would only assert that the config still
    says what it said when this file was authored.
    """
    findings: list[MappingFinding] = []

    for position, row in enumerate(employees):
        group = row.get("group")
        if group not in declared_groups:
            name = norm(row.get("normalized"))
            findings.append(
                MappingFinding(
                    criterion="F1",
                    bucket=BUCKET_HARD,
                    message=(
                        f"F1 — nhân viên {row.get('normalized')!r} khai group "
                        f"{group!r} không có trong `employee_groups`"
                    ),
                    employee=name or None,
                    declared_group=str(group),
                    provenance=RowProvenance(
                        row_index.rows_for_record_at(position) if row_index else ()
                    ),
                )
            )

    for raw_value, matches in ambiguities.items():
        # `row_index` is optional so `reconcile_conversion.py` — which calls
        # this positionally and only prints strings — keeps working
        # byte-for-byte (CHECK-110-14). Production passes it, and only then
        # does the finding carry rows at all: `ambiguous_rows()` returns ONLY
        # the rows where more than one record was really in force on that
        # row's own date (Review #3 Finding 1, Review #4 Finding 1).
        rows = row_index.ambiguous_rows(raw_value) if row_index else ()
        findings.append(
            MappingFinding(
                criterion="F3",
                bucket=BUCKET_HARD,
                message=(
                    f"F3 — {raw_value!r} khớp nhiều nhân viên cùng hiệu lực tại "
                    f"ngày của dòng đó: {sorted(matches)}"
                ),
                raw_value=raw_value,
                provenance=RowProvenance(rows),
            )
        )

    if not mapped:
        findings.append(
            MappingFinding(
                criterion="F5",
                bucket=BUCKET_HARD,
                message=(
                    "F5 — KHÔNG nhân viên nào map được dòng nào. Mapping "
                    "production hỏng hoàn toàn."
                ),
                provenance=RowProvenance(
                    row_index.all_unmapped_rows() if row_index else (),
                    batch_scoped=True,
                ),
            )
        )
        return RawMappingVerdict(findings)

    for row in employees:
        name = norm(row["normalized"])
        active = row.get("active", True)

        if name in mapped:
            continue

        starts, ends = _effective_window(row)
        if not active:
            findings.append(
                MappingFinding(
                    criterion="F2",
                    bucket=BUCKET_INFO,
                    message=(
                        f"F2 — {name!r} `active: false`, không có dòng nào: "
                        "đúng kỳ vọng"
                    ),
                    employee=name,
                    raw_prefix=row.get("raw_prefix"),
                )
            )
        elif not _overlaps(row, dataset_start, dataset_end):
            findings.append(
                MappingFinding(
                    criterion="F2",
                    bucket=BUCKET_INFO,
                    message=(
                        f"F2 — {name!r} hiệu lực {starts}..{ends}, ngoài phạm "
                        "vi dữ liệu: đúng kỳ vọng, không phải lỗi"
                    ),
                    employee=name,
                    raw_prefix=row.get("raw_prefix"),
                )
            )
        else:
            findings.append(
                MappingFinding(
                    criterion="F2",
                    bucket=BUCKET_WARNING,
                    message=(
                        f"F2 — {name!r} (raw_prefix {row.get('raw_prefix')!r}) "
                        "đang hiệu lực trong kỳ nhưng không khớp dòng nào. Có "
                        "thể là sai prefix, cũng có thể chỉ là không có doanh "
                        "số — cần người xem."
                    ),
                    employee=name,
                    raw_prefix=row.get("raw_prefix"),
                )
            )

    smallest_name, smallest = min(mapped.items(), key=lambda kv: kv[1])
    for raw_value, count in unmapped.items():
        # A blank/absent `NVBH` is not an unmapped IDENTITY — there is no name
        # for master data to be missing. That row is already reported as
        # `Missing.employee`, and letting it reach F4 produced a finding with
        # no raw identity and no rows to point at (Review #2, Finding 1).
        # `reconcile_conversion.py` never sees blanks either: it skips rows
        # with no `NVBH` before counting, so this changes nothing there.
        if not raw_value:
            continue
        if count >= smallest:
            findings.append(
                MappingFinding(
                    criterion="F4",
                    bucket=BUCKET_WARNING,
                    message=(
                        f"F4 — {raw_value!r} chưa map nhưng có {count} dòng, "
                        f"≥ nhân viên nhỏ nhất đã map ({smallest_name}: "
                        f"{smallest}). Dấu hiệu master data thiếu người đáng "
                        "kể — chẩn đoán, không phải kết luận."
                    ),
                    raw_value=raw_value,
                    # ONLY the rows that failed to map. A row of the same
                    # canonical identity that mapped fine is not evidence of
                    # missing master data, and naming it would put a row
                    # outside the finding into the finding's provenance
                    # (Review #4, Finding 2).
                    provenance=RowProvenance(
                        row_index.unmapped_rows(raw_value) if row_index else ()
                    ),
                )
            )

    return RawMappingVerdict(findings)


def evaluate_inactive_records(
    mapper: EmployeeMapper, row_index: "MappingStats"
) -> list[MappingFinding]:
    """F6 — a record flagged `active: false` that still owns rows (HD-110-03).

    Attributed **per config record**, from the row index's own record
    attribution. Independent Review #2, Finding 2: the first version
    aggregated by normalized name and then applied one boolean `active` to
    every record sharing that name, so a closed historical record borrowed the
    current record's transactions and raised a false F6.

    The index attributes a row to a record only when the row has a date
    (HD-110-04): with no date there is no evidence for which record was in
    force, and picking one would manufacture a verdict out of an unknown. Such
    a row is already reported as `Missing.date`.

    Diagnostic only — no rate, no KPI ownership, and no
    `employee_mapping_status` changes because of it.
    """
    findings: list[MappingFinding] = []
    for position, record in enumerate(mapper.records):
        if record.get("active", True):
            continue
        owned = row_index.rows_for_record_at(position)
        if not owned:
            continue
        name = norm(record.get("normalized"))
        prefix = record.get("raw_prefix")
        starts, ends = _effective_window(record)
        findings.append(
            MappingFinding(
                criterion="F6",
                bucket=BUCKET_WARNING,
                message=(
                    f"F6 — bản ghi {name!r} (raw_prefix {prefix!r}, hiệu lực "
                    f"{starts}..{ends}) khai `active: false` nhưng có "
                    f"{len(owned)} dòng rơi đúng vào cửa sổ hiệu lực của nó. "
                    "Master data mâu thuẫn: nếu người này đã nghỉ thì "
                    "`effective_to` phải đóng trước các dòng đó. Doanh số vẫn "
                    "đang tính cho họ — cần người xem."
                ),
                employee=name,
                raw_prefix=prefix,
                provenance=RowProvenance(owned),
            )
        )
    return findings


def _record_label(record: dict) -> str:
    """A record identity a human can act on — name alone is not enough when
    two records deliberately share it (DEC-121)."""
    starts, ends = _effective_window(record)
    return (
        f"{norm(record.get('normalized'))}"
        f"[{record.get('raw_prefix')}|{starts.isoformat()}..{ends.isoformat()}]"
    )


@dataclass(frozen=True)
class MappingStats:
    """Các counter mà `evaluate_raw_mapping` cần, cộng một CHỈ MỤC DÒNG HẸP.

    Script phân tích dựng counter bằng cách đọc thẳng `.xlsx`. Production dựng
    chúng từ các `WorkingLine` mà chính `EmployeeMapper` đã resolve, nên hai
    đường đồng ý **theo cấu trúc** chứ không nhờ một bản cài đặt thứ hai của
    quy tắc khớp.

    **Chỉ mục dòng hẹp có chủ đích (Independent Review #4).** Một bản trước
    phơi ra `rows_by_raw_value` / `rows_by_employee` — "mọi dòng cùng canonical
    identity" — và hàng chờ dựng provenance từ đó. Tập ấy rộng hơn mọi finding.
    Các accessor rộng đó đã bị gỡ; những gì còn lại chỉ trả lời đúng câu hỏi mà
    một tiêu chí được phép hỏi.

    **Chỉ mục khóa bằng `RecordRef` (Independent Review #5).** Trước đây khóa
    là `_record_key` — một tuple giá trị gồm tên + prefix + cửa sổ hiệu lực.
    Hai record có thể trùng khít cả ba mà vẫn khác `active`/`group`, nên F6
    nhặt đúng các dòng mà production đã gán cho record KIA. `RecordRef` là
    danh tính của bản ghi đã load, nên va chạm là bất khả.
    """

    mapped: Counter
    groups: dict[str, str]
    unmapped: Counter
    ambiguities: dict[str, set]
    dataset_start: Optional[date]
    dataset_end: Optional[date]
    source_file: Optional[str]
    total_rows: int
    _mapper: EmployeeMapper
    _unmapped_rows: dict[str, tuple[AffectedRow, ...]]
    _rows_by_record: dict[RecordRef, tuple[AffectedRow, ...]]
    _ambiguous_rows: dict[str, tuple[AmbiguousRow, ...]]

    # -- accessor hẹp: mỗi câu hỏi một tiêu chí được phép hỏi ---------------

    def unmapped_rows(self, raw_value: str) -> tuple[AffectedRow, ...]:
        """F4: các dòng của identity này KHÔNG map được. Một dòng cùng identity
        mà map bình thường không phải bằng chứng thiếu master data."""
        return self._unmapped_rows.get(raw_value, ())

    def all_unmapped_rows(self) -> tuple[AffectedRow, ...]:
        """F5: không map được gì cả, nên mọi dòng unmapped đều bị ảnh hưởng."""
        return tuple(
            row for rows in self._unmapped_rows.values() for row in rows
        )

    def ambiguous_rows(self, raw_value: str) -> tuple[AmbiguousRow, ...]:
        """F3: chỉ các dòng mà thật sự có nhiều hơn một record cùng hiệu lực
        tại ngày của chính dòng đó."""
        return self._ambiguous_rows.get(raw_value, ())

    def rows_for_record_at(self, index: int) -> tuple[AffectedRow, ...]:
        """F1 và F6: các dòng mà production đã resolve về ĐÚNG record ở vị trí
        này TRONG MASTER SNAPSHOT.

        Tra bằng `RecordRef` của chính snapshot, không bằng so sánh đối tượng:
        master giữ bản **đã đóng băng** của record, nên so `is` với dict gốc
        của caller sẽ trượt trong im lặng — đúng lớp lỗi mà INVARIANT M tồn
        tại để loại bỏ. Hai record cố ý dùng chung tên trong một lượt bàn giao
        (DEC-121), và Review #5 chứng minh chúng còn có thể dùng chung cả
        prefix lẫn cửa sổ hiệu lực — chỉ số trong snapshot phân biệt được cả
        hai trường hợp đó.
        """
        if index < 0 or index >= len(self._mapper.records):
            return ()
        return self._rows_by_record.get(self._mapper.ref_for_index(index), ())

    def dataset_range(self) -> str:
        if self.dataset_start and self.dataset_end:
            return f"{self.dataset_start.isoformat()}..{self.dataset_end.isoformat()}"
        return "không xác định"


def collect_mapping_stats(
    lines: list[WorkingLine], mapper: EmployeeMapper
) -> MappingStats:
    """Dựng counter và chỉ mục dòng hẹp từ các dòng đã resolve.

    Nhận thẳng `EmployeeMapper` production — không nhận một list record rời để
    rồi tự đoán lại. Đây là thay đổi kiến trúc trung tâm của Independent Review
    #5: mọi câu hỏi về "record nào" đều được HỎI mapper, nên trong hệ thống chỉ
    còn đúng một phép chọn record và không còn chỗ cho bản thứ hai drift.
    """
    mapped: Counter = Counter()
    groups: dict[str, str] = {}
    unmapped: Counter = Counter()
    ambiguities: dict[str, set] = {}
    unmapped_rows: dict[str, list[AffectedRow]] = defaultdict(list)
    rows_by_record: dict[RecordRef, list[AffectedRow]] = defaultdict(list)
    ambiguous_rows: dict[str, list[AmbiguousRow]] = defaultdict(list)
    dataset_start: Optional[date] = None
    dataset_end: Optional[date] = None
    source_file: Optional[str] = None

    for line in lines:
        raw_value = norm(line.employee_raw)
        when = line.date
        source_file = source_file or line.raw.source_file
        affected = AffectedRow(
            source_file=line.raw.source_file,
            source_row=line.raw.source_row,
            raw_original=line.employee_raw or "",
            when=when,
        )

        if when:
            dataset_start = when if dataset_start is None else min(dataset_start, when)
            dataset_end = when if dataset_end is None else max(dataset_end, when)

        if line.employee_normalized:
            name = norm(line.employee_normalized)
            mapped[name] += 1
            groups[name] = line.employee_group or "—"
        else:
            unmapped[raw_value] += 1
            unmapped_rows[raw_value].append(affected)

        # Chỉ các dòng CÓ NGÀY mới được quy về record (HD-110-04). Không có
        # ngày thì bộ lọc cửa sổ hiệu lực không áp dụng, nên mọi record chọn ở
        # đây đều là phỏng đoán; một tiêu chí dựng trên đó là kết tội master
        # data bằng bằng chứng không tồn tại.
        if when is None:
            continue

        ref = mapper.resolve_record(line.employee_raw, when)
        if ref is not None:
            rows_by_record[ref].append(affected)

        # Ambiguity chấm theo ngày của CHÍNH dòng này, và bằng ĐÚNG ngữ nghĩa
        # chuỗi mà production dùng để map (DEC-132, điểm D3). Bản trước khớp
        # prefix trên chuỗi đã normalize trong khi production khớp trên chuỗi
        # thô, nên một dòng mà production để `unmapped` vẫn bị F3 — mức ERROR —
        # kết tội là ambiguous.
        #
        # HD-110-05 (DEC-131): dòng KHÔNG có ngày không được tham gia — đã
        # `continue` ở trên. Chốt chặn nằm ở ĐÂY, trong collector của
        # production, chứ không nằm trong `evaluate_raw_mapping`: script phân
        # tích tự dựng `ambiguities` của nó và phải giữ nguyên hành vi đã ký
        # duyệt ở CHECK-108A1-15.
        candidates = mapper.candidate_records(line.employee_raw, when)
        hits = {
            norm(mapper.record(candidate).get("normalized"))
            for candidate in candidates
        }
        if len(hits) > 1:
            # Verdict vẫn khóa theo identity — đó là thứ script phân tích tiêu
            # thụ. Các DÒNG được ghi riêng để hàng chờ chỉ nêu đúng những dòng
            # thật sự va chạm.
            ambiguities[raw_value] = hits
            ambiguous_rows[raw_value].append(
                AmbiguousRow(
                    source_file=line.raw.source_file,
                    source_row=line.raw.source_row,
                    raw_original=line.employee_raw or "",
                    when=when,
                    raw_value=raw_value,
                    records=tuple(
                        sorted(
                            _record_label(mapper.record(candidate))
                            for candidate in candidates
                        )
                    ),
                )
            )

    return MappingStats(
        mapped=mapped,
        groups=groups,
        unmapped=unmapped,
        ambiguities=ambiguities,
        dataset_start=dataset_start,
        dataset_end=dataset_end,
        source_file=source_file,
        total_rows=len(lines),
        _mapper=mapper,
        _unmapped_rows={k: tuple(v) for k, v in unmapped_rows.items()},
        _rows_by_record={k: tuple(v) for k, v in rows_by_record.items()},
        _ambiguous_rows={k: tuple(v) for k, v in ambiguous_rows.items()},
    )
