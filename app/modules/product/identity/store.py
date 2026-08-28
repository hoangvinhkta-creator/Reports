"""`ProductIdentityStore` — Protocol + cơ chế Phase 1, data contract §10/§11.

## Interface trước, cơ chế sau

`D-10`. Domain chỉ phụ thuộc `ProductIdentityStore` (Protocol) — đúng tiền lệ
`PriceProvider`/`DEC-103` và đúng lời hứa của `ADR-101` rằng Phase 2 chuyển
vào DB mà **giữ nguyên interface**. Cùng một bộ test chạy được trên cả hai cơ
chế; đó là lý do tách Protocol chứ không phải để cho đẹp sơ đồ.

## Cơ chế Phase 1: JSONL append-only + index dẫn xuất

`D-11`. Không thêm dependency (stdlib `json`), nên `app/modules/` giữ nguyên
tính chất "thư viện Python thuần" mà `ADR-101` bắt kiểm chứng bằng test tĩnh.
Append-only là yêu cầu gốc của `ADR-102`, không phải thứ phải mô phỏng. Và
point-in-time read (`§10.2`) là *miễn phí*: "trạng thái tại revision R" =
chiếu lại log tới event R. Đó chính là thứ làm cho replay của `INV-56` khả thi
mà không cần một bảng lịch sử riêng.

Hạn chế ghi rõ, không giấu: JSONL + khoá file là concurrency **một máy**.
Nhiều người dùng đồng thời trên nhiều máy là bài toán Phase 2 và cần DB.

## Khoá liên-tiến-trình: biên giao dịch, không phải biên `write()`

`B-01` (Independent Implementation Review #1) chỉ ra rằng lời hứa "một máy" ở
trên trước đây KHÔNG có gì thi hành: hai tiến trình cùng đọc `version = N`,
cả hai cùng qua `_require_version`, cả hai cùng append — `INV-59` bị phá và
log kết thúc với hai bản ghi `CONFIRMED` độc lập cho cùng một khoá, làm mọi
phép đọc sau đó raise `MappingIntegrityError` VĨNH VIỄN.

Sửa đúng chỗ có nghĩa là khoá bao trọn **giao dịch**, không bao mỗi lệnh ghi:

```text
ACQUIRE khoá độc quyền trên <log_path>.lock
    nạp lại phần đuôi log do tiến trình khác ghi   ← trạng thái quyền uy
    chiếu lại + kiểm toàn vẹn (INV-33/INV-63)
    idempotency lớp 1 (INV-68)
    authority (INV-01)
    version hiện tại → so expected_version (INV-59)
    dựng mutation + append + fsync + rebuild index
RELEASE
```

Kiểm version SAU khi đã khoá và SAU khi đã nạp lại — `check → lock → append`
vẫn là cùng một race, chỉ hẹp hơn. Khoá quanh riêng `write()` cũng vậy:
`write()` chưa bao giờ là chỗ hỏng; hỏng nằm ở quyết định "được phép ghi".

Chi tiết cơ chế — xem `_transaction()`.

## Ba luật mà file này thi hành, không chỉ mô tả

- `INV-63` LOG THẮNG. Index là DERIVED. Mọi phép đọc dưới đây chiếu lại từ
  log; `rebuild_index()` chỉ ghi lại một bản cache. Mất index không mất dữ
  liệu, và log bất đồng với index thì log đúng.
- `INV-67` KHÔNG DELETE. Không có phương thức xoá ở bất kỳ đâu trong interface.
  Correction là supersede.
- `INV-01`/`INV-28b` similarity không bao giờ tự thành `CONFIRMED`. Luật này
  đặt ở tầng append — nghĩa là nó áp cho MỌI đường ghi (bootstrap, migration,
  script vận hành), không riêng đường resolve. Đó là điều `CHECK-105D-07` đi
  tìm: một phủ định toàn cục, không phải hành vi của một case.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional, Protocol

try:  # POSIX — Linux/macOS, đúng môi trường runtime đã tuyên bố của Phase 1.
    import fcntl
except ImportError:  # pragma: no cover — nền tảng không phải POSIX
    fcntl = None  # type: ignore[assignment]

from app.modules.product.identity.audit import (
    AffectedScope,
    AggregateType,
    CONFIRMATION_ACTION_TYPES,
    EventType,
    MappingAuditEvent,
)
from app.modules.product.identity.commands import (
    BootstrapMapping,
    ConfirmCrossSystem,
    ConfirmMapping,
    CorrectCrossSystem,
    CorrectMapping,
    Command,
    CrossSystemCommand,
    MappingCommand,
    MarkStale,
    RejectCandidate,
    SetPending,
)
from app.modules.product.identity.cross_system import (
    CrossSystemConflictError,
    CrossSystemProductMapping,
    CrossSystemStatus,
)
from app.modules.product.identity.evidence import (
    ResolutionMethod,
    is_auto_resolvable,
)
from app.modules.product.identity.identity import Namespace
from app.modules.product.identity.mapping import (
    MappingIntegrityError,
    MappingSource,
    MappingStatus,
    ProductIdentityMapping,
)
from app.modules.product.identity.rejection import RejectedCandidate


class AppendOutcome(str, Enum):
    """Bốn kết cục của một lần append — §11.3 phân biệt retry/no-op/correction."""

    APPLIED = "APPLIED"
    ALREADY_APPLIED = "ALREADY_APPLIED"
    NO_CHANGE = "NO_CHANGE"


class MappingVersionConflict(RuntimeError):
    """`INV-59` — `expected_version` không khớp version hiện tại.

    Mang theo `current_state` để client reload và reconcile (`INV-60`). Không
    có auto-merge, không có "force write" ở Phase 1: hai người cùng khẳng định
    hai identity khác nhau cho một sản phẩm là một bất đồng nghiệp vụ, và một
    cái máy chọn hộ là cách sai để giải nó.
    """

    def __init__(self, message: str, *, current_state: Any = None) -> None:
        super().__init__(message)
        self.current_state = current_state


class StoreLockUnavailableError(RuntimeError):
    """Không có cơ chế khoá liên-tiến-trình trên nền tảng đang chạy.

    Fail closed. Một store có `log_path` mà KHÔNG khoá được chính là khiếm
    khuyết `B-01`; chạy tiếp trong im lặng sẽ tái lập đúng nó, nên đường này
    nổ thay vì hạ cấp âm thầm xuống "một tiến trình".
    """


class SimilarityAuthorityError(RuntimeError):
    """`INV-01`/`INV-28b` — một đường ghi cố tạo `CONFIRMED` từ evidence không
    thuộc tập auto-resolve mà không có `confirmation_action`."""


class StoreView:
    """Trạng thái đã chiếu tại một revision. Chỉ đọc."""

    def __init__(
        self,
        revision: int,
        mappings: dict[str, ProductIdentityMapping],
        all_mappings: tuple[ProductIdentityMapping, ...],
        rejections: tuple[RejectedCandidate, ...],
        cross_system: dict[str, CrossSystemProductMapping],
        all_cross_system: tuple[CrossSystemProductMapping, ...],
    ) -> None:
        self.revision = revision
        self._mappings = mappings
        self.all_mappings = all_mappings
        self.rejections = rejections
        self._cross_system = cross_system
        self.all_cross_system = all_cross_system

    def active_mapping(
        self, source_system: str, raw_identity_key: str
    ) -> Optional[ProductIdentityMapping]:
        return self._mappings.get(_mapping_key(source_system, raw_identity_key))

    def alias_index(self) -> dict[str, ProductIdentityMapping]:
        """E-G `AliasMemory` — một *view*, không phải một store thứ hai (`D-06`).

        Dựng lại từ chính các bản ghi ACTIVE mỗi lần gọi. Không có trạng thái
        riêng nào để lệch khỏi log.
        """
        return dict(self._mappings)

    def confirmed_cross_system(
        self, tracking_code: str
    ) -> Optional[CrossSystemProductMapping]:
        return self._cross_system.get(tracking_code)


class ProductIdentityStore(Protocol):
    """Protocol `D-10`. `app/modules/` chỉ phụ thuộc bốn phương thức này.

    Cố ý KHÔNG có `delete`, `truncate` hay `update` (`INV-67`): một interface
    mà không ai gọi được để xoá là một bảo đảm mạnh hơn một quy ước rằng không
    ai nên xoá.
    """

    def read_active_mapping(
        self, source_system: str, raw_identity_key: str
    ) -> Optional[ProductIdentityMapping]:
        ...

    def read_at_revision(self, revision: int) -> StoreView:
        ...

    def append(self, command: Command) -> "AppendResult":
        ...

    def current_revision(self) -> int:
        ...


@dataclass(frozen=True)
class AppendResult:
    outcome: AppendOutcome
    new_version: int
    revision: int
    event: Optional[MappingAuditEvent] = None
    mapping: Optional[ProductIdentityMapping] = None
    cross_system: Optional[CrossSystemProductMapping] = None
    rejection: Optional[RejectedCandidate] = None


_LOCK_SUFFIX = ".lock"


def _mapping_key(source_system: str, raw_identity_key: str) -> str:
    return f"{source_system}\x1f{raw_identity_key}"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JsonlProductIdentityStore:
    """Cơ chế Phase 1 (`D-11`). Thi hành `ProductIdentityStore`.

    `log_path` là nguồn sự thật duy nhất. `index_path` chỉ là cache và có thể
    xoá bất cứ lúc nào mà không mất dữ liệu — `CHECK-105D-09` fixture (2) đi
    đúng đường đó.
    """

    def __init__(
        self, log_path: Optional[Path] = None, index_path: Optional[Path] = None
    ) -> None:
        self.log_path = Path(log_path) if log_path else None
        self.index_path = Path(index_path) if index_path else None
        self.lock_path = (
            self.log_path.with_name(self.log_path.name + _LOCK_SUFFIX)
            if self.log_path is not None
            else None
        )
        self._events: list[MappingAuditEvent] = []
        self._raw_records: list[dict[str, Any]] = []
        self._results_by_request: dict[str, AppendResult] = {}
        # Số byte và số dòng vật lý của log đã được nạp vào bộ nhớ. Log là
        # append-only (`INV-67`), nên phần đã nạp luôn là một TIỀN TỐ của file
        # — đó là điều làm cho việc nạp lại phần đuôi trở nên hợp lệ.
        self._log_offset = 0
        self._log_lines = 0
        # Khoá trong-tiến-trình: bảo vệ chính bộ đếm độ sâu bên dưới và tuần
        # tự hoá các luồng của CÙNG instance. KHÔNG thay thế khoá file.
        self._thread_lock = threading.RLock()
        self._lock_depth = 0
        if self.log_path is not None and self.log_path.exists():
            # Nạp lần đầu cũng phải nằm trong khoá: một tiến trình khác có thể
            # đang ghi dở một dòng, và đọc trúng dòng dở đó sẽ raise
            # `MappingIntegrityError` cho một log hoàn toàn lành.
            with self._transaction():
                pass

    # ---- khoá liên-tiến-trình --------------------------------------------

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        """Biên nguyên tử của MỌI đường ghi (`INV-59`/`INV-62`/`INV-66`).

        Đối tượng bị khoá
        -----------------
        `<log_path>.lock` — một file *sidecar* riêng, KHÔNG phải chính log và
        KHÔNG phải index. Lý do phải là sidecar chứ không phải log:
        `rebuild_index()` thay index bằng `os.replace`, tức đổi inode. Khoá
        trên một inode bị thay giữa chừng sẽ mất tác dụng loại trừ lẫn nhau —
        hai tiến trình sẽ khoá hai inode khác nhau và cùng tưởng mình độc
        quyền. File lock ở đây được tạo một lần và KHÔNG BAO GIỜ bị xoá hay
        thay thế, nên inode của nó ổn định suốt vòng đời store.

        Ngữ nghĩa
        ---------
        `fcntl.flock(LOCK_EX)` — độc quyền, không có chế độ chia sẻ: mọi
        đường ghi đều phải nạp lại state nên đều là writer. Khoá chặn (không
        `LOCK_NB`): hai người dùng trên một máy phải xếp hàng, không phải
        nhận lỗi giả.

        Vòng đời
        --------
        Giữ đúng một giao dịch: mở fd → `LOCK_EX` → nạp lại đuôi log → thân
        giao dịch → `LOCK_UN` → đóng fd. `finally` chạy trên mọi đường thoát,
        kể cả `MappingVersionConflict`, `SimilarityAuthorityError` hay
        `MappingIntegrityError` — không có đường nào rời khối này mà còn giữ
        khoá.

        Tiến trình chết
        ---------------
        `flock` gắn với *open file description*; nhân giải phóng khoá khi
        tiến trình chết hoặc fd đóng, kể cả khi bị `SIGKILL`. Vì vậy KHÔNG có
        stale lock, và cũng vì vậy file `.lock` không được xoá: xoá nó là
        cách kinh điển tạo ra hai tiến trình khoá hai inode khác nhau.

        Tái nhập (reentrancy)
        ---------------------
        `_persist()` gọi `rebuild_index()`, mà `rebuild_index()` cũng là một
        giao dịch. `flock` trên một fd THỨ HAI của cùng tiến trình vẫn xung
        đột, nên mở fd lần nữa sẽ tự khoá chính mình. Bộ đếm `_lock_depth`
        (đặt dưới `RLock` nên an toàn giữa các luồng) làm lần vào bên trong
        thành no-op.

        Giới hạn nền tảng
        -----------------
        POSIX. Trên nền tảng không có `fcntl` (Windows), một store CÓ
        `log_path` sẽ raise `StoreLockUnavailableError` thay vì chạy không
        khoá. Store thuần bộ nhớ (`log_path is None`) không cần khoá và
        không bị ảnh hưởng.

        `flock` cũng không loại trừ lẫn nhau qua NFS ở nhiều cấu hình; điều đó
        nằm trong đúng phạm vi mà `§11.1` đã tuyên bố là Phase 2 ("nhiều máy"),
        không phải một hạn chế mới do bản sửa này tạo ra.
        """
        with self._thread_lock:
            if self._lock_depth > 0:
                self._lock_depth += 1
                try:
                    yield
                finally:
                    self._lock_depth -= 1
                return

            if self.lock_path is None:
                # Store thuần bộ nhớ: không có file dùng chung nào để tranh
                # chấp. `RLock` ở trên đã đủ cho biên luồng.
                self._lock_depth += 1
                try:
                    yield
                finally:
                    self._lock_depth -= 1
                return

            if fcntl is None:  # pragma: no cover — nền tảng không phải POSIX
                raise StoreLockUnavailableError(
                    f"{self.lock_path}: nền tảng không cung cấp fcntl.flock; "
                    "store có persistence KHÔNG được chạy không khoá "
                    "(INV-59 sẽ không thi hành được qua biên tiến trình)"
                )

            self.lock_path.parent.mkdir(parents=True, exist_ok=True)
            # `O_NOFOLLOW`: một symlink đặt sẵn ở đúng đường dẫn khoá sẽ khiến
            # hai tiến trình khoá hai inode KHÁC nhau và cùng tưởng mình độc
            # quyền — tức đúng `B-01` quay lại qua cửa sau. Gặp symlink thì nổ,
            # không đi theo.
            fd = os.open(
                self.lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600
            )
            try:
                fcntl.flock(fd, fcntl.LOCK_EX)
                self._lock_depth = 1
                try:
                    self._refresh_from_disk()
                    yield
                finally:
                    self._lock_depth = 0
                    fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def _refresh_from_disk(self) -> None:
        """Nạp lại phần log do tiến trình khác ghi. CHỈ gọi khi đang giữ khoá.

        Đây là nửa còn lại của bản sửa `B-01`: khoá mà không nạp lại thì
        `expected_version` vẫn được so với một ảnh chụp cũ trong bộ nhớ, và
        writer cũ vẫn thắng. Vì log là append-only, phần đã nạp luôn là tiền
        tố của file, nên chỉ cần đọc từ `_log_offset` trở đi.
        """
        if self.log_path is None or not self.log_path.exists():
            return
        size = self.log_path.stat().st_size
        if size == self._log_offset:
            return
        if size < self._log_offset:
            raise MappingIntegrityError(
                f"{self.log_path}: log co lại từ {self._log_offset} xuống "
                f"{size} byte — vi phạm append-only (INV-67); KHÔNG được đọc "
                "tiếp thành một state một nửa"
            )
        with open(self.log_path, "rb") as handle:
            handle.seek(self._log_offset)
            chunk = handle.read()
        self._consume(chunk)

    def _consume(self, chunk: bytes) -> None:
        """Chiếu `chunk` (một hoặc nhiều dòng JSONL) vào state trong bộ nhớ.

        Một dòng hỏng — kể cả một dòng ghi dở do tiến trình chết giữa
        `write()` — bị TỪ CHỐI, không bị bỏ qua: `INV-63` nói log thắng, nên
        một log không đọc được phải nổ chứ không được đọc thành nửa state.
        """
        for line in chunk.decode("utf-8").splitlines():
            self._log_lines += 1
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise MappingIntegrityError(
                    f"{self.log_path}: dòng {self._log_lines} không phải JSON "
                    "hợp lệ — log hỏng, KHÔNG được đọc tiếp thành một state "
                    "một nửa"
                ) from exc
            self._raw_records.append(record)
            event = _event_from_record(record)
            self._events.append(event)
            if event.client_request_id and event.client_request_id not in (
                self._results_by_request
            ):
                self._results_by_request[event.client_request_id] = AppendResult(
                    outcome=AppendOutcome.APPLIED,
                    new_version=event.resulting_version,
                    revision=event.revision,
                    event=event,
                )
        self._log_offset += len(chunk)

    # ---- đọc -------------------------------------------------------------

    def current_revision(self) -> int:
        """§10.2 — số thứ tự của event cuối cùng. Đơn điệu, không tái sử dụng.

        Đường ĐỌC cố ý KHÔNG nạp lại từ đĩa. Đó chính là mô hình optimistic
        concurrency của `§10.3`: client đọc version `N`, gửi
        `expected_version = N`, và nếu trong lúc đó có người khác ghi thì
        `append()` — nơi DUY NHẤT có quyền quyết định — phát hiện và trả
        `MappingVersionConflict` (`INV-59`), rồi client reload và reconcile
        (`INV-60`). Nạp lại ở đây sẽ biến một phép đọc thành một lần lấy khoá
        và vẫn không loại bỏ được cửa sổ giữa đọc và ghi.
        """
        return len(self._events)

    def read_at_revision(self, revision: int) -> StoreView:
        """Chiếu lại log tới `revision`. Cùng revision → cùng kết quả (`INV-64`)."""
        if revision < 0 or revision > len(self._events):
            raise ValueError(
                f"revision {revision} ngoài khoảng [0, {len(self._events)}]"
            )
        return _project(self._events[:revision], revision)

    def read_active_mapping(
        self, source_system: str, raw_identity_key: str
    ) -> Optional[ProductIdentityMapping]:
        return self.read_at_revision(self.current_revision()).active_mapping(
            source_system, raw_identity_key
        )

    def events(self) -> tuple[MappingAuditEvent, ...]:
        """Toàn bộ audit log. Append-only, không có phương thức nào sửa nó."""
        return tuple(self._events)

    def confirmation_action_count(
        self, *, since_revision: int = 0, aggregate_id: Optional[str] = None
    ) -> int:
        """Đếm `confirmation_action` theo định nghĩa quy phạm §17.1.

        Đúng bốn loại command, đếm ở tầng domain. Đây là hàm mà `G03`, `G04`,
        `G11`, `G23`, `G24`, `G32` đọc — nên nó cố ý không biết gì về phím,
        chuột, hay bề mặt điều khiển.
        """
        return sum(
            1
            for event in self._events[since_revision:]
            if event.is_confirmation_action
            and (aggregate_id is None or event.aggregate_id == aggregate_id)
        )

    # ---- ghi -------------------------------------------------------------

    def append(self, command: Command) -> AppendResult:
        """Đường ghi DUY NHẤT (`INV-66`).

        Thứ tự kiểm là một phần của hợp đồng, không phải chi tiết cài đặt:

        0. khoá liên-tiến-trình + nạp lại log (`_transaction`) — TOÀN BỘ bốn
           bước dưới đây nằm trong đó. Không bước nào được phép nhìn thấy một
           ảnh chụp cũ hơn state trên đĩa;
        1. idempotency lớp 1 (`INV-68`) — retry phải trả kết quả cũ **trước
           khi** chạm tới version, nếu không một retry hợp lệ sẽ bị báo
           conflict;
        2. authority (`INV-01`) — chặn similarity → `CONFIRMED` trên MỌI đường;
        3. concurrency (`INV-59`) — `expected_version`;
        4. idempotency lớp 2 (`INV-69`) — state không đổi thì không ghi gì.

        Bước 1 nằm TRONG khoá là có chủ ý, không phải tiện tay: một retry của
        cùng `client_request_id` có thể đã được một tiến trình khác áp dụng, và
        chỉ sau khi nạp lại log thì bộ nhớ retry mới biết điều đó.
        """
        with self._transaction():
            cached = self._results_by_request.get(command.client_request_id)
            if cached is not None:
                return AppendResult(
                    outcome=AppendOutcome.ALREADY_APPLIED,
                    new_version=cached.new_version,
                    revision=cached.revision,
                    event=cached.event,
                    mapping=cached.mapping,
                    cross_system=cached.cross_system,
                    rejection=cached.rejection,
                )

            self._guard_authority(command)

            view = self.read_at_revision(self.current_revision())
            if isinstance(command, MappingCommand):
                return self._append_mapping_command(command, view)
            if isinstance(command, CrossSystemCommand):
                return self._append_cross_system_command(command, view)
            raise TypeError(f"command không được hỗ trợ: {type(command).__name__}")

    def _guard_authority(self, command: Command) -> None:
        """`INV-01`/`INV-28b`/`G07` — phủ định TOÀN CỤC, không theo case.

        Một mapping `CONFIRMED` mang `resolution_method` ngoài tập auto-resolve
        chỉ hợp lệ khi chính event tạo ra nó là một `confirmation_action`. Đặt
        luật ở đây nghĩa là bootstrap, migration và mọi script vận hành đều bị
        chặn bằng cùng một dòng code — không có "đường sau".
        """
        method = getattr(command, "resolution_method", None)
        if method is None:
            return
        if is_auto_resolvable(method):
            return
        if command.event_type in CONFIRMATION_ACTION_TYPES:
            return
        raise SimilarityAuthorityError(
            f"INV-01/INV-28b: {command.event_type.value} không được tạo mapping "
            f"CONFIRMED với resolution_method={method.value} — "
            "cần một confirmation_action của người"
        )

    def _append_mapping_command(
        self, command: MappingCommand, view: StoreView
    ) -> AppendResult:
        current = view.active_mapping(command.source_system, command.raw_identity_key)
        current_version = current.version if current is not None else 0
        self._require_version(command, current_version, current)

        if isinstance(command, RejectCandidate):
            return self._apply_rejection(command, view, current_version)

        new_mapping, old_record = self._next_mapping(command, current, view)
        if new_mapping is None:
            return AppendResult(
                outcome=AppendOutcome.NO_CHANGE,
                new_version=current_version,
                revision=self.current_revision(),
                mapping=current,
            )

        event = self._write_event(
            command=command,
            aggregate_type=AggregateType.PRODUCT_IDENTITY_MAPPING,
            aggregate_id=command.aggregate_id,
            old_value=old_record,
            new_value=new_mapping.to_record(),
            resulting_version=new_mapping.version,
        )
        result = AppendResult(
            outcome=AppendOutcome.APPLIED,
            new_version=new_mapping.version,
            revision=self.current_revision(),
            event=event,
            mapping=new_mapping,
        )
        self._results_by_request[command.client_request_id] = result
        return result

    def _next_mapping(
        self,
        command: MappingCommand,
        current: Optional[ProductIdentityMapping],
        view: StoreView,
    ) -> tuple[Optional[ProductIdentityMapping], Optional[dict[str, Any]]]:
        """Bản ghi mới, hoặc `None` khi state kết quả bằng state hiện tại.

        Correction KHÔNG sửa `current` tại chỗ: bản cũ được ghi lại dưới dạng
        `old_value` trong event và ở lại log vĩnh viễn với `status =
        SUPERSEDED` khi chiếu (`INV-32`, `INV-74`).
        """
        now = _utcnow()
        old_record = current.to_record() if current is not None else None

        if isinstance(command, (ConfirmMapping, BootstrapMapping)):
            target = command.target
            if (
                current is not None
                and current.status is MappingStatus.CONFIRMED
                and current.identity_tuple
                == (target.namespace, target.source_product_code)
            ):
                return None, old_record
            return (
                ProductIdentityMapping(
                    mapping_id=str(uuid.uuid4()),
                    source_system=command.source_system,
                    raw_product_identity=command.raw_product_identity,
                    raw_identity_key=command.raw_identity_key,
                    normalized_matching_aid=_aid_of(command),
                    status=MappingStatus.CONFIRMED,
                    mapping_source=command.mapping_source,
                    resolution_method=command.resolution_method,
                    evidence=command.evidence,
                    version=(current.version + 1) if current is not None else 1,
                    created_at=now,
                    created_by=command.actor_id,
                    namespace=target.namespace,
                    source_product_code=target.source_product_code,
                    supersedes=current.mapping_id if current is not None else None,
                    pp_version_id=command.pp_version_id,
                    tracking_capture_id=command.tracking_capture_id,
                    confirmed_at=now,
                    confirmed_by=command.actor_id,
                ),
                old_record,
            )

        if isinstance(command, SetPending):
            status = (
                MappingStatus.STALE
                if command.pending_status_stale
                else MappingStatus.PENDING
            )
            if current is not None and current.status is status:
                return None, old_record
            return (
                ProductIdentityMapping(
                    mapping_id=str(uuid.uuid4()),
                    source_system=command.source_system,
                    raw_product_identity=command.raw_product_identity,
                    raw_identity_key=command.raw_identity_key,
                    normalized_matching_aid=_aid_of(command),
                    status=status,
                    mapping_source=MappingSource.HUMAN_CONFIRMATION,
                    resolution_method=ResolutionMethod.SIMILARITY_RANKED,
                    evidence=command.evidence or _pending_evidence(command),
                    version=(current.version + 1) if current is not None else 1,
                    created_at=now,
                    created_by=command.actor_id,
                    supersedes=current.mapping_id if current is not None else None,
                    pp_version_id=command.pp_version_id,
                    tracking_capture_id=command.tracking_capture_id,
                ),
                old_record,
            )

        if isinstance(command, MarkStale):
            if current is None:
                raise ValueError("MARK_STALE cần một mapping đang tồn tại")
            if current.status is MappingStatus.STALE:
                return None, old_record
            return (
                ProductIdentityMapping(
                    mapping_id=str(uuid.uuid4()),
                    source_system=current.source_system,
                    raw_product_identity=current.raw_product_identity,
                    raw_identity_key=current.raw_identity_key,
                    normalized_matching_aid=current.normalized_matching_aid,
                    status=MappingStatus.STALE,
                    mapping_source=current.mapping_source,
                    resolution_method=current.resolution_method,
                    evidence=current.evidence,
                    version=current.version + 1,
                    created_at=now,
                    created_by=command.actor_id,
                    namespace=current.namespace,
                    source_product_code=current.source_product_code,
                    supersedes=current.mapping_id,
                    pp_version_id=command.pp_version_id,
                    tracking_capture_id=command.tracking_capture_id,
                ),
                old_record,
            )

        raise TypeError(f"command không được hỗ trợ: {type(command).__name__}")

    def _apply_rejection(
        self, command: RejectCandidate, view: StoreView, current_version: int
    ) -> AppendResult:
        duplicate = any(
            r.suppression_key
            == (
                command.raw_identity_key,
                command.candidate_namespace,
                command.candidate_code,
                command.evidence_fingerprint,
            )
            for r in view.rejections
        )
        if duplicate:
            return AppendResult(
                outcome=AppendOutcome.NO_CHANGE,
                new_version=current_version,
                revision=self.current_revision(),
            )

        rejection_id = str(uuid.uuid4())
        record = {
            "rejection_id": rejection_id,
            "source_system": command.source_system,
            "raw_identity_key": command.raw_identity_key,
            "candidate_namespace": command.candidate_namespace.value,
            "candidate_code": command.candidate_code,
            "evidence_fingerprint": command.evidence_fingerprint,
            "rejected_by": command.actor_id,
            "rejected_at": _utcnow().isoformat(),
            "pp_version_id": command.pp_version_id,
            "tracking_capture_id": command.tracking_capture_id,
            "reason": command.reason,
        }
        event = self._write_event(
            command=command,
            aggregate_type=AggregateType.REJECTED_CANDIDATE,
            aggregate_id=command.aggregate_id,
            old_value=None,
            new_value=record,
            resulting_version=current_version,
        )
        result = AppendResult(
            outcome=AppendOutcome.APPLIED,
            new_version=current_version,
            revision=self.current_revision(),
            event=event,
        )
        self._results_by_request[command.client_request_id] = result
        return result

    def _append_cross_system_command(
        self, command: CrossSystemCommand, view: StoreView
    ) -> AppendResult:
        current = view.confirmed_cross_system(command.tracking_code)
        current_version = current.version if current is not None else 0
        self._require_version(command, current_version, current)

        if (
            current is not None
            and current.public_purchase_code == command.public_purchase_code
            and isinstance(command, ConfirmCrossSystem)
        ):
            return AppendResult(
                outcome=AppendOutcome.NO_CHANGE,
                new_version=current_version,
                revision=self.current_revision(),
                cross_system=current,
            )

        holder = next(
            (
                m
                for m in view.all_cross_system
                if m.status is CrossSystemStatus.CONFIRMED
                and m.public_purchase_code == command.public_purchase_code
                and m.tracking_code != command.tracking_code
            ),
            None,
        )
        if holder is not None:
            raise CrossSystemConflictError(
                f"INV-39/INV-40: public_purchase_code {command.public_purchase_code!r} "
                f"đã thuộc mapping CONFIRMED của tracking_code "
                f"{holder.tracking_code!r}; status = CONFLICT, không "
                "last-write-wins"
            )

        now = _utcnow()
        mapping = CrossSystemProductMapping(
            mapping_id=str(uuid.uuid4()),
            tracking_code=command.tracking_code,
            public_purchase_code=command.public_purchase_code,
            status=CrossSystemStatus.CONFIRMED,
            confirmed_by=command.actor_id,
            confirmed_at=now,
            evidence=command.evidence,
            version=current_version + 1,
            pp_version_id=command.pp_version_id or "",
            tracking_capture_id=command.tracking_capture_id or "",
            reason=command.reason,
            supersedes=current.mapping_id if current is not None else None,
        )
        event = self._write_event(
            command=command,
            aggregate_type=AggregateType.CROSS_SYSTEM_MAPPING,
            aggregate_id=command.aggregate_id,
            old_value=current.to_record() if current is not None else None,
            new_value=mapping.to_record(),
            resulting_version=mapping.version,
        )
        result = AppendResult(
            outcome=AppendOutcome.APPLIED,
            new_version=mapping.version,
            revision=self.current_revision(),
            event=event,
            cross_system=mapping,
        )
        self._results_by_request[command.client_request_id] = result
        return result

    def _require_version(
        self, command: Command, current_version: int, current_state: Any
    ) -> None:
        """`INV-59` — mismatch thì từ chối và KHÔNG ghi gì, KHÔNG tăng version."""
        if command.expected_version != current_version:
            raise MappingVersionConflict(
                f"expected_version={command.expected_version} nhưng version hiện "
                f"tại={current_version}; reload và reconcile (INV-59/INV-60)",
                current_state=current_state,
            )

    def _write_event(
        self,
        *,
        command: Command,
        aggregate_type: AggregateType,
        aggregate_id: str,
        old_value: Optional[dict[str, Any]],
        new_value: Optional[dict[str, Any]],
        resulting_version: int,
    ) -> MappingAuditEvent:
        revision = self.current_revision() + 1
        scope = command.affected_scope
        event = MappingAuditEvent(
            event_id=str(uuid.uuid4()),
            revision=revision,
            event_type=command.event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            actor_id=command.actor_id,
            occurred_at=_utcnow(),
            old_value=old_value,
            new_value=new_value,
            affected_scope=AffectedScope(
                distinct_identity_count=scope.distinct_identity_count,
                affected_order_ids=scope.affected_order_ids,
                affected_line_count=scope.affected_line_count,
                computed_at_revision=revision - 1,
            ),
            client_request_id=command.client_request_id,
            resulting_version=resulting_version,
            pp_version_id=command.pp_version_id,
            tracking_capture_id=command.tracking_capture_id,
            reason=command.reason,
        )
        self._events.append(event)
        record = event.to_record()
        self._raw_records.append(record)
        self._persist(record)
        return event

    # ---- I/O -------------------------------------------------------------

    def _persist(self, record: dict[str, Any]) -> None:
        """`INV-62` — một event = một lần ghi + `fsync`.

        Ghi cả dòng trong một lần `write()` rồi `fsync` trước khi trả về: một
        lần ghi bị ngắt để lại một dòng JSON dở, và dòng dở đó bị `_consume()`
        từ chối thay vì được đọc thành một state "đọc được nhưng sai".
        """
        if self.log_path is None:
            return
        self._append_line(record)
        self.rebuild_index()

    def _append_line(self, record: dict[str, Any]) -> None:
        """Ghi MỘT dòng + `fsync` và đẩy `_log_offset` theo đúng số byte đó.

        Đường ghi vật lý DUY NHẤT xuống log. Việc `_log_offset` tiến lên ngay
        tại đây là điều giữ cho `_refresh_from_disk()` không đọc lại chính
        dòng mình vừa ghi thành một event thứ hai.
        """
        if self.log_path is None:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        payload = (
            json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
        ).encode("utf-8")
        with open(self.log_path, "ab") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        self._log_offset += len(payload)
        self._log_lines += 1

    def rebuild_index(self) -> None:
        """Ghi lại index dẫn xuất theo khuôn write-temp + `os.replace` (`INV-62`).

        `os.replace` là đổi tên nguyên tử trên cùng filesystem: người đọc thấy
        index cũ hoặc index mới, không bao giờ thấy một index viết dở.

        Gọi công khai thì tự lấy khoá — nếu không, hai tiến trình có thể ghi
        đè index của nhau bằng hai ảnh chụp khác nhau. Gọi từ `_persist()` thì
        đã ở trong khoá và `_transaction()` biến nó thành no-op.
        """
        if self.index_path is None:
            return
        with self._transaction():
            self._write_index()

    def _write_index(self) -> None:
        if self.index_path is None:
            return
        view = self.read_at_revision(self.current_revision())
        payload = {
            "revision": view.revision,
            "active_mappings": {
                key: mapping.mapping_id for key, mapping in view.alias_index().items()
            },
        }
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.index_path.with_suffix(self.index_path.suffix + ".tmp")
        temp.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8"
        )
        os.replace(temp, self.index_path)

    def export_bundle(self) -> dict[str, Any]:
        """`INV-65` — artifact tự mô tả: log + manifest + hash.

        `import_bundle()` trên một store rỗng cho lại một store tương đương
        bit: cùng chuỗi event, cùng revision, cùng hash.
        """
        import hashlib

        payload = json.dumps(
            self._raw_records, ensure_ascii=False, sort_keys=True
        ).encode("utf-8")
        return {
            "manifest": {
                "schema": "TASK-105D/product-identity-store",
                "event_count": len(self._raw_records),
                "revision": self.current_revision(),
                "content_hash": hashlib.sha256(payload).hexdigest(),
            },
            "events": list(self._raw_records),
        }

    @classmethod
    def import_bundle(
        cls, bundle: dict[str, Any], *, log_path: Optional[Path] = None
    ) -> "JsonlProductIdentityStore":
        store = cls(log_path=log_path)
        # Import là một đường GHI, nên nó chịu đúng biên nguyên tử như
        # `append()` (`§19` — không đường ghi nào được để ngoài khoá). Cả
        # bundle nằm trong MỘT giao dịch: một tiến trình khác thấy log trước
        # import hoặc sau import, không bao giờ thấy nửa bundle.
        with store._transaction():
            for record in bundle["events"]:
                store._raw_records.append(record)
                store._events.append(_event_from_record(record))
                store._append_line(record)
        return store


def _aid_of(command: MappingCommand) -> str:
    from app.modules.product.identity.keys import normalized_matching_aid

    source = command.raw_product_identity or command.raw_identity_key
    return normalized_matching_aid(source)


def _pending_evidence(command: MappingCommand):
    from app.modules.product.identity.evidence import Evidence, MatchedOn

    return Evidence(
        matched_on=MatchedOn.MANUAL_SEARCH,
        matched_value=command.raw_identity_key,
        candidate_set_ids=(),
    )


def _project(events: Iterable[MappingAuditEvent], revision: int) -> StoreView:
    """Chiếu log thành trạng thái. Đây là toàn bộ "cơ sở dữ liệu" của Phase 1.

    `INV-33` được thi hành ngay tại đây, và phép kiểm là **chuỗi supersede**
    chứ không phải phép đếm. Một correction hợp lệ để lại NHIỀU bản ghi
    `CONFIRMED` cho cùng một khoá trong log — đó là `INV-32`, bản cũ ở lại vĩnh
    viễn — nên "đếm được hai bản ghi CONFIRMED" không phải lỗi. Cái LÀ lỗi là
    hai bản ghi **độc lập**: mỗi bản ghi mới phải khai `supersedes` đúng bằng
    bản ghi liền trước của khoá đó. Một log bị chèn tay một bản ghi `CONFIRMED`
    thứ hai với `supersedes = None` vi phạm đúng luật đó, và phép đọc NỔ chứ
    không chọn một cái — đọc bừa một trong hai là cách biến một lỗi toàn vẹn
    thành một con số sai im lặng.
    """
    active: dict[str, ProductIdentityMapping] = {}
    last_record_id: dict[str, str] = {}
    all_mappings: list[ProductIdentityMapping] = []
    rejections: list[RejectedCandidate] = []
    cross_active: dict[str, CrossSystemProductMapping] = {}
    all_cross: list[CrossSystemProductMapping] = []

    for event in events:
        if event.aggregate_type is AggregateType.PRODUCT_IDENTITY_MAPPING:
            mapping = _mapping_from_record(event.new_value)
            if mapping is None:
                continue
            all_mappings.append(mapping)
            key = _mapping_key(mapping.source_system, mapping.raw_identity_key)
            expected_predecessor = last_record_id.get(key)
            if mapping.supersedes != expected_predecessor:
                raise MappingIntegrityError(
                    f"INV-33: bản ghi {mapping.mapping_id} cho khoá {key!r} khai "
                    f"supersedes={mapping.supersedes!r} nhưng bản ghi trước đó là "
                    f"{expected_predecessor!r} — hai bản ghi CONFIRMED độc lập cho "
                    "cùng một khoá; TUYỆT ĐỐI không tự chọn một cái"
                )
            last_record_id[key] = mapping.mapping_id
            if mapping.status is MappingStatus.CONFIRMED:
                active[key] = mapping
            else:
                active.pop(key, None)
        elif event.aggregate_type is AggregateType.REJECTED_CANDIDATE:
            rejection = _rejection_from_record(event.new_value, event.event_id)
            if rejection is not None:
                rejections.append(rejection)
        elif event.aggregate_type is AggregateType.CROSS_SYSTEM_MAPPING:
            mapping = _cross_from_record(event.new_value)
            if mapping is None:
                continue
            all_cross.append(mapping)
            if mapping.status is CrossSystemStatus.CONFIRMED:
                cross_active[mapping.tracking_code] = mapping

    return StoreView(
        revision=revision,
        mappings=active,
        all_mappings=tuple(all_mappings),
        rejections=tuple(rejections),
        cross_system=cross_active,
        all_cross_system=tuple(all_cross),
    )


def _mapping_from_record(record: Optional[dict[str, Any]]):
    if not record or "mapping_id" not in record:
        return None
    from app.modules.product.identity.evidence import Evidence, MatchedOn

    evidence_record = record.get("evidence") or {}
    evidence = Evidence(
        matched_on=MatchedOn(evidence_record.get("matched_on", "MANUAL_SEARCH")),
        matched_value=evidence_record.get("matched_value", ""),
        candidate_set_ids=tuple(evidence_record.get("candidate_set_ids") or ()),
        ranking_method_id=evidence_record.get("ranking_method_id"),
        parent_mapping_id=evidence_record.get("parent_mapping_id"),
    )
    namespace = record.get("namespace")
    return ProductIdentityMapping(
        mapping_id=record["mapping_id"],
        source_system=record["source_system"],
        raw_product_identity=record.get("raw_product_identity", ""),
        raw_identity_key=record["raw_identity_key"],
        normalized_matching_aid=record.get("normalized_matching_aid", ""),
        status=MappingStatus(record["status"]),
        mapping_source=MappingSource(record["mapping_source"]),
        resolution_method=ResolutionMethod(record["resolution_method"]),
        evidence=evidence,
        version=record["version"],
        created_at=_parse_dt(record["created_at"]),
        created_by=record["created_by"],
        namespace=Namespace(namespace) if namespace else None,
        source_product_code=record.get("source_product_code"),
        supersedes=record.get("supersedes"),
        superseded_by=record.get("superseded_by"),
        pp_version_id=record.get("pp_version_id"),
        tracking_capture_id=record.get("tracking_capture_id"),
        confirmed_at=_parse_dt(record.get("confirmed_at")),
        confirmed_by=record.get("confirmed_by"),
        audit_event_ids=tuple(record.get("audit_event_ids") or ()),
    )


def _rejection_from_record(record: Optional[dict[str, Any]], event_id: str):
    if not record or "rejection_id" not in record:
        return None
    return RejectedCandidate(
        rejection_id=record["rejection_id"],
        source_system=record["source_system"],
        raw_identity_key=record["raw_identity_key"],
        candidate_namespace=Namespace(record["candidate_namespace"]),
        candidate_code=record["candidate_code"],
        evidence_fingerprint=record["evidence_fingerprint"],
        rejected_by=record["rejected_by"],
        rejected_at=_parse_dt(record["rejected_at"]),
        pp_version_id=record.get("pp_version_id"),
        tracking_capture_id=record.get("tracking_capture_id"),
        audit_event_id=record.get("audit_event_id") or event_id,
        reason=record.get("reason"),
    )


def _cross_from_record(record: Optional[dict[str, Any]]):
    if not record or "tracking_code" not in record:
        return None
    from app.modules.product.identity.evidence import Evidence, MatchedOn

    evidence_record = record.get("evidence") or {}
    return CrossSystemProductMapping(
        mapping_id=record["mapping_id"],
        tracking_code=record["tracking_code"],
        public_purchase_code=record["public_purchase_code"],
        status=CrossSystemStatus(record["status"]),
        confirmed_by=record["confirmed_by"],
        confirmed_at=_parse_dt(record["confirmed_at"]),
        evidence=Evidence(
            matched_on=MatchedOn(evidence_record.get("matched_on", "MANUAL_SEARCH")),
            matched_value=evidence_record.get("matched_value", ""),
            candidate_set_ids=tuple(evidence_record.get("candidate_set_ids") or ()),
            ranking_method_id=evidence_record.get("ranking_method_id"),
            parent_mapping_id=evidence_record.get("parent_mapping_id"),
        ),
        version=record["version"],
        pp_version_id=record.get("pp_version_id") or "",
        tracking_capture_id=record.get("tracking_capture_id") or "",
        audit_event_ids=tuple(record.get("audit_event_ids") or ()),
        reason=record.get("reason"),
        supersedes=record.get("supersedes"),
        superseded_by=record.get("superseded_by"),
    )


def _event_from_record(record: dict[str, Any]) -> MappingAuditEvent:
    scope = record.get("affected_scope") or {}
    return MappingAuditEvent(
        event_id=record["event_id"],
        revision=record["revision"],
        event_type=EventType(record["event_type"]),
        aggregate_type=AggregateType(record["aggregate_type"]),
        aggregate_id=record["aggregate_id"],
        actor_id=record["actor_id"],
        occurred_at=_parse_dt(record["occurred_at"]),
        old_value=record.get("old_value"),
        new_value=record.get("new_value"),
        affected_scope=AffectedScope(
            distinct_identity_count=scope.get("distinct_identity_count", 0),
            affected_order_ids=tuple(scope.get("affected_order_ids") or ()),
            affected_line_count=scope.get("affected_line_count", 0),
            computed_at_revision=scope.get("computed_at_revision", 0),
        ),
        client_request_id=record["client_request_id"],
        resulting_version=record["resulting_version"],
        pp_version_id=record.get("pp_version_id"),
        tracking_capture_id=record.get("tracking_capture_id"),
        reason=record.get("reason"),
    )


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    return datetime.fromisoformat(value)
