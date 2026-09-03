#!/usr/bin/env python3
"""
Quét mọi file `.md` được track (hoặc mọi file `.md` dưới ROOT nếu không chạy
trong git) tìm các reference `.md`/`.py`/`.svg` được trích trong dấu backtick,
và xác nhận từng reference đó phân giải (resolve) được thành một file thật.

Quy tắc phân giải (chốt tại S002, tái tạo lại cách scan thủ công của S001 —
xem CHK-S001-06 và DEC-012/T04-C2b): thử phân giải từ ROOT trước, nếu không
được thì thử từ thư mục chứa file đang tham chiếu. Một reference chỉ bị coi
là BROKEN khi cả hai cách đều không phân giải được.

Loại trừ theo subtask 03.4 của TASK-REM-T03:
- `governance/reference/history/` — kho lưu trữ đã đóng băng (frozen archive),
  không quét NỘI DUNG của các file trong thư mục này (FIND-011). Các file khác
  tham chiếu VÀO thư mục này vẫn được kiểm tra bình thường.
- `docs/audit/` — bản ghi audit bất biến, trích dẫn nguyên văn các token lỗi
  (ví dụ `OPTIONAL_ENFORCEMENT_LAYER.md` trần trụi) làm bằng chứng lịch sử.
  Không quét nội dung file trong thư mục này.
- Reference chứa `*` (glob pattern, ví dụ `docs/tasks/TASK-REM-*.md`) — không
  phải một đường dẫn cụ thể, bỏ qua.

Usage:
    python3 validate_reference_integrity.py [ROOT_DIR]

Nếu ROOT_DIR được cung cấp, quét thư mục đó thay vì git root tự phát hiện —
dùng để test lại trên một cây thư mục khác (ví dụ một git worktree checkout
tại một commit lịch sử), theo CHECK-T03-03/CHECK-T03-04.
"""
from pathlib import Path
import re
import sys

# Chỉ bắt reference kết thúc bằng .md/.py/.svg — đúng phạm vi khai báo trong
# Objective/Scope của TASK-REM-T03. Đã thử mở rộng sang cả reference thư mục
# (kết thúc bằng "/", ví dụ `templates/`) để tái hiện đủ 3 finding gốc của
# S001 cho CHECK-T03-03, nhưng cách đó gây ra 20 false positive khi quét HEAD
# hiện tại (đa số là ví dụ minh họa trong văn xuôi như `src/`, `shared/`,
# hoặc tên thư mục cũ trong tường thuật lịch sử — không phải reference sống
# thật cần resolve). Một validator kêu sai nhiều sẽ bị phớt lờ, đúng bài học
# của chính FIND-005. Xem COMPLETION GATE CHANGE PROPOSAL trong DEC-013 —
# CHECK-T03-03 được sửa để chỉ yêu cầu tái hiện 2/3 finding gốc (loại .md),
# case directory `templates/` bị loại khỏi phạm vi validator một cách tường
# minh, không phải bị bỏ sót ngầm.
REF_PATTERN = re.compile(r"`([A-Za-z0-9_./-]+\.(?:md|py|svg))`")

EXCLUDED_DIR_PREFIXES = (
    "governance/reference/history/",
    "docs/audit/",
)

# Cặp (file nguồn, reference) được biết là trích dẫn token lỗi làm bằng
# chứng lịch sử, hoặc forward-reference tới file mà một task PLANNED/READY
# sẽ tạo ra — không phải link thực sự bị hỏng. Đây là allowlist theo TỪNG
# CẶP CHÍNH XÁC (không phải theo token), để một reference thực sự hỏng tới
# cùng tên file ở một nơi khác trong repo vẫn bị báo cáo bình thường.
#
# Thêm một dòng mới vào đây chỉ khi đã xác nhận thủ công đó là trích dẫn/
# forward-reference hợp lệ, không phải regression thực sự — xem DEC-012 và
# TASK-REM-T03 subtask 03.4.
KNOWN_EXEMPT_PAIRS = {
    # DEC-011 trong PROJECT_DECISIONS.md: trích dẫn nguyên văn token lỗi đã
    # từng tồn tại (FIND-003), mô tả những gì đã được sửa.
    ("PROJECT/PROJECT_DECISIONS.md", "OPTIONAL_ENFORCEMENT_LAYER.md"),
    # Findings Register trong PROJECT_PROGRESS.md: trích dẫn tên finding
    # FIND-003, mô tả lỗi đã biết (nay đã RESOLVED).
    ("PROJECT/PROJECT_PROGRESS.md", "OPTIONAL_ENFORCEMENT_LAYER.md"),
    # MICRO-002/REM-T06 trong PROJECT_PROGRESS.md: forward-reference tới
    # README.md mà REM-T06 (PLANNED) sẽ tạo ở gốc repository.
    ("PROJECT/PROJECT_PROGRESS.md", "README.md"),
    # Subtask 03.4 của chính task file này: trích dẫn token lỗi làm ví dụ
    # minh họa cho loại reference cần loại trừ.
    ("docs/tasks/TASK-REM-T03-validator-hardening.md", "OPTIONAL_ENFORCEMENT_LAYER.md"),
    # TASK-105C (DEC-152) Scope Lock: forward-reference tới các file mà
    # TASK-105C implementation (READY, chưa IN_PROGRESS) sẽ tạo — đúng module
    # code (app/modules/pricing/), export tool (tools/pricing/), và test suite
    # (tests/) được mô tả trong Scope Lock/Completion Gate, chưa tồn tại vì
    # chưa implementation.
    ("docs/tasks/TASK-105C-historical-vendor-price-provider.md",
     "app/modules/pricing/historical_vendor_price.py"),
    ("docs/tasks/TASK-105C-historical-vendor-price-provider.md",
     "app/modules/pricing/historical_vendor_price_provider.py"),
    ("docs/tasks/TASK-105C-historical-vendor-price-provider.md",
     "tools/pricing/export_historical_vendor_prices.py"),
    ("docs/tasks/TASK-105C-historical-vendor-price-provider.md",
     "tests/test_historical_vendor_price.py"),
    ("docs/tasks/TASK-105C-historical-vendor-price-provider.md",
     "tests/test_historical_vendor_price_provider.py"),
    # DEC-152 trong PROJECT_DECISIONS.md: cùng forward-reference tới export
    # tool mà TASK-105C sẽ tạo, trích dẫn trong phần mô tả kiến trúc.
    ("PROJECT/PROJECT_DECISIONS.md",
     "tools/pricing/export_historical_vendor_prices.py"),
    # S029 (bàn giao session DEC-152): cùng forward-reference, trong phần
    # "File Đã Thay Đổi" liệt kê những gì TASK-105C sẽ tạo ở phiên sau.
    ("docs/sessions/S029-task-105c-final-decision-scope-lock.md",
     "tools/pricing/export_historical_vendor_prices.py"),
    # TASK-PRA-005 Contract Freeze (S107): forward-reference tới bản ghi
    # Independent Review E2 mà CHECK-PRA005-14 sẽ tạo ở phiên implementation
    # sau — cùng khuôn tiền lệ TASK-PRA-001..004
    # (docs/reviews/TASK-PRA-0XX-INDEPENDENT-REVIEW-RECORD.md), file chưa
    # tồn tại vì PRA-005 mới ở trạng thái Contract FROZEN, chưa
    # implementation.
    ("docs/tasks/TASK-PRA-005-san-pham.md",
     "docs/reviews/TASK-PRA-005-INDEPENDENT-REVIEW-RECORD.md"),
}


def find_git_root(start: Path):
    current = start
    while True:
        if (current / ".git").exists():
            return current
        if current.parent == current:
            return None
        current = current.parent


def resolve_root(argv):
    if len(argv) > 1:
        root = Path(argv[1]).resolve()
        if not root.is_dir():
            print(f"REFERENCE INTEGRITY: FAIL")
            print(f"- ROOT_DIR không tồn tại hoặc không phải thư mục: {root}")
            sys.exit(1)
        return root

    script_dir = Path(__file__).resolve().parent
    git_root = find_git_root(script_dir)
    if git_root is None:
        # Không có ROOT_DIR truyền vào và không tìm được git root — dùng
        # cách resolve cố định như các validator khác (parents[3]) để vẫn
        # chạy được khi package bị copy ra ngoài git.
        return Path(__file__).resolve().parents[3]
    return git_root


def is_excluded(rel_path: str) -> bool:
    return any(rel_path.startswith(prefix) for prefix in EXCLUDED_DIR_PREFIXES)


def resolves(ref: str, root: Path, referencing_file_dir: Path) -> bool:
    if (root / ref).exists():
        return True
    if (referencing_file_dir / ref).exists():
        return True
    return False


def scan(root: Path):
    broken = []
    scanned_files = 0
    excluded_files = 0

    for md_file in sorted(root.rglob("*.md")):
        rel = md_file.relative_to(root).as_posix()

        if is_excluded(rel):
            excluded_files += 1
            continue

        scanned_files += 1
        text = md_file.read_text(encoding="utf-8", errors="replace")
        refs = sorted(set(REF_PATTERN.findall(text)))

        for ref in refs:
            if "*" in ref:
                continue
            if "/" not in ref and not ref.endswith(".md"):
                # Tên file trần trụi không kèm đường dẫn và không phải .md
                # (ví dụ một dòng code python nhắc tới "foo.py" không mang ý
                # nghĩa tham chiếu file) — bỏ qua để tránh false positive.
                continue
            if resolves(ref, root, md_file.parent):
                continue
            if (rel, ref) in KNOWN_EXEMPT_PAIRS:
                continue
            broken.append((rel, ref))

    return broken, scanned_files, excluded_files


def main():
    root = resolve_root(sys.argv)
    broken, scanned_files, excluded_files = scan(root)

    if broken:
        print("REFERENCE INTEGRITY: FAIL")
        print(f"Quét {scanned_files} file .md (loại trừ {excluded_files} file "
              f"trong {', '.join(EXCLUDED_DIR_PREFIXES)}).")
        print(f"{len(broken)} reference không phân giải được:")
        for source, ref in broken:
            print(f"- {source} -> {ref}")
        sys.exit(1)

    print("REFERENCE INTEGRITY: PASS")
    print(f"Quét {scanned_files} file .md (loại trừ {excluded_files} file "
          f"trong {', '.join(EXCLUDED_DIR_PREFIXES)}).")
    print("0 reference bị hỏng.")


if __name__ == "__main__":
    main()
