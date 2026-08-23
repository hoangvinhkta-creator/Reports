#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]

required = [
    "CLAUDE.md",
    "governance/core/00_SESSION_ORCHESTRATION.md",
    "governance/core/PROJECT_PROFILE_STANDARD.md",
    "governance/core/RULE_PRECEDENCE.md",
    "governance/core/EVIDENCE_STANDARD.md",
    "governance/core/TASK_MODE_STANDARD.md",
    "governance/core/TASK_READY_GATE_STANDARD.md",
    "governance/core/TASK_COMPLETION_GATE_STANDARD.md",
    "governance/core/04_SECURITY_RULES.md",
    "governance/core/11_FORBIDDEN_ACTIONS.md",
    "PROJECT/PROJECT_PROFILE.md",
    "PROJECT/PROJECT_PROGRESS.md",
    "PROJECT/PROJECT_DECISIONS.md",
    "docs/tasks/README.md",
    "docs/sessions/README.md",
    "docs/reviews/README.md",
    "governance/templates/TASK_DEFINITION_TEMPLATE.md",
    "governance/templates/SESSION_HANDOFF_TEMPLATE.md",
    "governance/templates/PROJECT_PROGRESS_TEMPLATE.md",
    "governance/templates/MICRO_TASK_CHECKLIST.md",
    "governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md",
]


def find_git_root(start: Path):
    """Đi ngược lên từ `start` tìm một thư mục chứa `.git` (dir hoặc file —
    file trong trường hợp git worktree). Trả về Path hoặc None nếu không tìm
    thấy trước khi chạm filesystem root."""
    current = start
    while True:
        if (current / ".git").exists():
            return current
        if current.parent == current:
            return None
        current = current.parent


def check_deployment_root(script_path: Path):
    """Assert rằng ROOT đã resolve từ vị trí file script (parents[3]) chính
    là git root thật. Trả về (status, message) với status thuộc
    {"PASS", "FAIL", "NOT_APPLICABLE"}.

    Tách thành hàm riêng, nhận script_path tường minh, để có thể unit-test
    bằng một fixture path giả lập mà không cần chạy lại toàn bộ script."""
    resolved_root = script_path.resolve().parents[3]
    git_root = find_git_root(script_path.resolve().parent)

    if git_root is None:
        return (
            "NOT_APPLICABLE",
            "Deployment root: NOT_APPLICABLE — không tìm thấy .git khi đi "
            "ngược lên từ vị trí script; không chạy trong một git repository "
            "(ví dụ: package được copy ra ngoài git để dùng độc lập).",
        )

    if git_root != resolved_root:
        return (
            "FAIL",
            "Deployment root: FAIL — governance package không nằm ở gốc git "
            f"repository.\n"
            f"  Gốc git repository (git root):        {git_root}\n"
            f"  Gốc mà validator resolve được (ROOT):  {resolved_root}\n"
            "  Kỳ vọng: hai đường dẫn trên phải trùng nhau. CLAUDE.md, "
            "PROJECT/, docs/, governance/ phải nằm trực tiếp tại git root, "
            "không lồng trong một thư mục con.",
        )

    return ("PASS", f"Deployment root: PASS — {resolved_root}")


deployment_status, deployment_message = check_deployment_root(Path(__file__))

missing = [p for p in required if not (ROOT / p).exists()]

if deployment_status == "FAIL" or missing:
    print("GOVERNANCE STRUCTURE: FAIL")
    print(deployment_message)
    for p in missing:
        print(f"- missing: {p}")
    sys.exit(1)

print("GOVERNANCE STRUCTURE: PASS")
print(deployment_message)
print(f"Checked {len(required)} required paths.")
